"""Metadata-only source index and bounded, globally addressed raster I/O."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import math
import numpy as np
import rasterio
from rasterio.transform import Affine, from_origin
from rasterio.windows import Window
from pyproj import Transformer

IO_SIZE = 512
GDAL_CACHE_BYTES = 32 * 1024**2


def digest_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    transform: tuple
    crs: str
    mode: str = 'custom'
    selected_source: str | None = None
    selected_sources: tuple[str, ...] = ()

    @property
    def affine(self):
        return Affine(*self.transform)

    @property
    def res(self):
        return self.transform[0]

    def bounds(self, core=None):
        c, r, w, h = core or (0, 0, self.width, self.height)
        a = self.affine
        return (a.c + c*a.a, a.f + (r+h)*a.e,
                a.c + (c+w)*a.a, a.f + r*a.e)

    def local_transform(self, core):
        return self.affine * Affine.translation(core[0], core[1])


def core_dimensions(size):
    """Return columns, rows; an integer is a per-axis limit, not a pixel count."""
    if type(size) is int:
        dimensions = (size, size)
    elif isinstance(size, (tuple, list)) and len(size) == 2:
        dimensions = tuple(size)
    else:
        raise ValueError('Core size must be a positive side length or [columns, rows]')
    if any(type(value) is not int or value <= 0 for value in dimensions):
        raise ValueError('Core columns and rows must be positive integers')
    return dimensions


def cores(grid, size):
    """Lazy, disjoint whole-output windows, with rectangular or square cores."""
    width, height = core_dimensions(size)
    for r in range(0, grid.height, height):
        for c in range(0, grid.width, width):
            yield (c, r, min(width, grid.width-c), min(height, grid.height-r))


def expand(core, halo):
    c, r, w, h = core
    return c-halo, r-halo, w+2*halo, h+2*halo


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inventory(paths):
    records = []
    for path in sorted(map(Path, paths)):
        with rasterio.open(path) as ds:
            a = ds.transform
            if (ds.count != 1 or ds.crs is None or not ds.crs.is_projected
                    or ds.crs.linear_units != 'metre' or a.b != 0 or a.d != 0
                    or a.a <= 0 or a.e != -a.a):
                raise ValueError(f'Unsupported source grid (single band, north-up square metre grid required): {path}')
            records.append(dict(path=str(path.resolve()), width=ds.width, height=ds.height,
                                transform=tuple(a)[:6], crs=ds.crs.to_string(),
                                bounds=tuple(ds.bounds), nodata=ds.nodata,
                                sha256=digest_file(path), bytes=path.stat().st_size))
    if not records:
        raise ValueError('No DSM GeoTIFF files found')
    first = records[0]
    a = Affine(*first['transform'])
    for i, rec in enumerate(records):
        b = Affine(*rec['transform'])
        if (rec['crs'] != first['crs'] or b.a != a.a
                or not math.isclose((b.c-a.c)/a.a, round((b.c-a.c)/a.a), abs_tol=1e-7)
                or not math.isclose((b.f-a.f)/a.e, round((b.f-a.f)/a.e), abs_tol=1e-7)):
            raise ValueError(f'Incompatible CRS, resolution, or grid alignment: {rec["path"]}')
        for prev in records[:i]:
            if intersects(rec['bounds'], prev['bounds']):
                raise ValueError(f'Ambiguous overlapping source grids: {rec["path"]} and {prev["path"]}')
    return records


def target_grid(records, study, mode='native_tile', width_m=600, height_m=450):
    first = records[0]
    x, y = Transformer.from_crs('EPSG:4326', first['crs'], always_xy=True).transform(
        study['longitude'], study['latitude'])
    res = first['transform'][0]
    if mode == 'native_tile':
        # Raster convention: west/north inclusive, east/south exclusive.
        matches = [r for r in records if r['bounds'][0] <= x < r['bounds'][2]
                   and r['bounds'][1] < y <= r['bounds'][3]]
        if len(matches) != 1:
            raise ValueError(f'Centre selects {len(matches)} tiles; expected exactly one under west/north-inclusive rule')
        rec = matches[0]
        return Grid(rec['width'], rec['height'], rec['transform'], rec['crs'], mode, rec['path'], (rec['path'],))
    if mode != 'custom':
        raise ValueError(f'Unknown output mode: {mode}')
    w, h = round(width_m/res), round(height_m/res)
    if min(w, h) <= 0 or not math.isclose(w*res, width_m) or not math.isclose(h*res, height_m):
        raise ValueError('Custom dimensions must be positive integer multiples of native pixel size')
    return Grid(w, h, tuple(from_origin(x-width_m/2, y+height_m/2, res, res))[:6], first['crs'])


def native_mosaic_grid(records, names):
    """Join explicitly selected native tiles, requiring a complete aligned rectangle.

    Each selected source retains its own exact core footprint. Reject holes or
    mixed tile dimensions rather than silently adding unselected output areas.
    All available sources may still supply the 1 km calculation halo.
    """
    if not names or not isinstance(names, (list, tuple)) or len(set(names)) != len(names):
        raise ValueError('native_tile_names must contain distinct source filenames')
    selected = []
    for name in names:
        matches = [r for r in records if name in (r['path'], Path(r['path']).name)]
        if len(matches) != 1:
            raise ValueError(f'Native mosaic tile is missing or ambiguous: {name}')
        selected.append(matches[0])
    if len({r['path'] for r in selected}) != len(selected):
        raise ValueError('The same source tile was selected more than once')
    selected.sort(key=lambda r: (-r['bounds'][3], r['bounds'][0]))
    first = selected[0]
    width, height = first['width'], first['height']
    res = first['transform'][0]
    if any((r['width'], r['height']) != (width, height) for r in selected):
        raise ValueError('Native mosaic requires uniform tile dimensions; use custom output for mixed formats')
    left = min(r['bounds'][0] for r in selected)
    bottom = min(r['bounds'][1] for r in selected)
    right = max(r['bounds'][2] for r in selected)
    top = max(r['bounds'][3] for r in selected)
    cols, rows = round((right-left)/res), round((top-bottom)/res)
    addresses = set()
    for r in selected:
        c, y = (r['bounds'][0]-left)/res, (top-r['bounds'][3])/res
        if not math.isclose(c/width, round(c/width), abs_tol=1e-8) or not math.isclose(y/height, round(y/height), abs_tol=1e-8):
            raise ValueError('Selected source tiles do not form an aligned native-tile lattice')
        addresses.add((round(c), round(y)))
    expected = {(c,r) for r in range(0,rows,height) for c in range(0,cols,width)}
    if cols % width or rows % height or addresses != expected:
        raise ValueError('Selected native tiles must fill a rectangle without gaps; add the missing tile(s)')
    return Grid(cols, rows, tuple(from_origin(left,top,res,res))[:6], first['crs'],
                'native_mosaic', first['path'], tuple(r['path'] for r in selected))


def output_reference(grid):
    """Geometric centre of the actual output; also the shared solar reference."""
    left, bottom, right, top = grid.bounds()
    x, y = (left+right)/2, (bottom+top)/2
    longitude, latitude = Transformer.from_crs(grid.crs, 'EPSG:4326', always_xy=True).transform(x,y)
    return dict(policy='output_geometric_center', easting_m=x, northing_m=y,
                longitude=longitude, latitude=latitude, crs=grid.crs,
                role='one shared solar reference for all spatial tasks')


def read_window(records, grid, core):
    """One destination array; one source handle and <=512² source cells at a time.

    Target centres map to source cells by floor, with ties at source cell edges
    assigned east/south. All coordinates derive from the whole-output transform.
    No per-chunk reprojection, rounding of bounds, or resampling origin exists.
    """
    c, r, w, h = core
    out = np.full((h, w), np.nan, np.float32)
    bounds = grid.bounds(core)
    a = grid.affine
    with rasterio.Env(GDAL_CACHEMAX=GDAL_CACHE_BYTES):
        for rec in records:
            if not intersects(bounds, rec['bounds']):
                continue
            s = Affine(*rec['transform'])
            # Equal resolutions and aligned source tiles permit one exact integer translation.
            dc = math.floor((a.c-s.c)/a.a + 0.5)
            dr = math.floor((s.f-a.f)/a.a + 0.5)
            x0, x1 = max(c, -dc), min(c+w, rec['width']-dc)
            y0, y1 = max(r, -dr), min(r+h, rec['height']-dr)
            if x1 <= x0 or y1 <= y0:
                continue
            with rasterio.open(rec['path']) as ds:
                for yy in range(y0, y1, IO_SIZE):
                    for xx in range(x0, x1, IO_SIZE):
                        ww, hh = min(IO_SIZE, x1-xx), min(IO_SIZE, y1-yy)
                        data = ds.read(1, window=Window(xx+dc, yy+dr, ww, hh), masked=True).astype(np.float32)
                        out[yy-r:yy-r+hh, xx-c:xx-c+ww] = data.filled(np.nan)
    return out


def region_stats(records, grid, region):
    c, r, w, h = region
    count, lo, hi = 0, math.inf, -math.inf
    for yy in range(r, r+h, IO_SIZE):
        for xx in range(c, c+w, IO_SIZE):
            a = read_window(records, grid, (xx, yy, min(IO_SIZE, c+w-xx), min(IO_SIZE, r+h-yy)))
            valid = a[np.isfinite(a)]
            count += valid.size
            if valid.size:
                lo, hi = min(lo, float(valid.min())), max(hi, float(valid.max()))
    return dict(valid_pixels=count, total_pixels=w*h, coverage=count/(w*h),
                min_m=lo if count else None, max_m=hi if count else None)


def seam_audit(records):
    """Exact count/mean/max; fixed histogram for bounded approximate quantiles."""
    hist = np.zeros(100001, np.int64)  # 0.01 m bins, final bin >=1000 m
    count, total, maximum = 0, 0., 0.
    with rasterio.Env(GDAL_CACHEMAX=GDAL_CACHE_BYTES):
        for i, one in enumerate(records):
            for two in records[i+1:]:
                for a, b in ((one, two), (two, one)):
                    al, ab, ar, at = a['bounds']; bl, bb, br, bt = b['bounds']
                    res = a['transform'][0]
                    if math.isclose(ar, bl, abs_tol=1e-7) and min(at, bt) > max(ab, bb):
                        n = round((min(at, bt)-max(ab, bb))/res)
                        wa = (a['width']-1, round((at-min(at, bt))/res), 1, n)
                        wb = (0, round((bt-min(at, bt))/res), 1, n)
                        vertical = True
                    elif math.isclose(ab, bt, abs_tol=1e-7) and min(ar, br) > max(al, bl):
                        n = round((min(ar, br)-max(al, bl))/res)
                        wa = (round((max(al, bl)-al)/res), a['height']-1, n, 1)
                        wb = (round((max(al, bl)-bl)/res), 0, n, 1)
                        vertical = False
                    else:
                        continue
                    with rasterio.open(a['path']) as da, rasterio.open(b['path']) as db:
                        for off in range(0, n, IO_SIZE):
                            size = min(IO_SIZE, n-off)
                            windows = [Window(v[0] + (0 if vertical else off),
                                              v[1] + (off if vertical else 0),
                                              1 if vertical else size, size if vertical else 1) for v in (wa, wb)]
                            aa = da.read(1, window=windows[0], masked=True)
                            ba = db.read(1, window=windows[1], masked=True)
                            diff = np.abs(aa-ba).compressed()
                            diff = diff[np.isfinite(diff)]
                            if diff.size:
                                count += diff.size; total += float(diff.astype(np.float64).sum())
                                maximum = max(maximum, float(diff.max()))
                                hist += np.bincount(np.minimum((diff/.01).astype(int), 100000), minlength=100001)
    cumulative = np.cumsum(hist)
    return dict(pairs_of_adjacent_valid_pixels=count, mean_abs_difference_m=total/count if count else None,
                max_abs_difference_m=maximum if count else None,
                median_histogram_lower_m=float(np.searchsorted(cumulative, count*.5)*.01) if count else None,
                p95_histogram_lower_m=float(np.searchsorted(cumulative, count*.95)*.01) if count else None,
                quantile_bin_m=.01, overflow_bin_m=1000,
                note='Adjacent terrain/roof differences are not measured seam errors; boundary windows only.')
