"""Cut verified sheets into native cells and hand them to the sea-view builder."""
from contextlib import ExitStack
import fcntl
import math
import os
from pathlib import Path
import platform
import tempfile

import numpy as np
import pyproj
from pyproj.exceptions import ProjError
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

from src import v1
from src.spatial import intersects
from tools.sea2.build import build, write_raster
from tools.sea2.provider import MISSING, SeaSource
from tools.sea2.rule import NODATA
from tools.sea2.view import verify_view
from tools.shade_map.common import atomic_json, digest, identity
from tools.shade_map.config import InvalidInput, load_json, machine_config, validate_output_root

from .profiles import MANIFEST_SCHEMA, POINTER_SCHEMA, catalogue_root, fill_profile, load_city

RESOLUTION = 0.5


def _stamp(path):
    info = path.stat()
    return info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_ino


def _open_sheets(directory, city, stack):
    sources = {p.name: p for p in directory.iterdir()
               if not p.name.startswith(".") and p.suffix.lower() == ".tif"}
    sheets = sorted(city["ingest"]["sheets"], key=lambda sheet: sheet["name"])
    expected = {sheet["name"] for sheet in sheets}
    if sources.keys() != expected:
        raise InvalidInput(f"raw sheets: missing {sorted(expected - sources.keys())}, "
                           f"extra {sorted(sources.keys() - expected)}")
    opened = []
    for sheet in sheets:
        path = sources[sheet["name"]]
        stamp = _stamp(path)
        if not path.is_file() or stamp[0] != sheet["bytes"] or digest(path) != sheet["sha256"]:
            raise InvalidInput(f"raw sheet {path.name}: size or SHA-256 differs from profile")
        ds = stack.enter_context(rasterio.open(path))
        a = ds.transform
        declared = sheet["declared_nodata"]
        if isinstance(declared, str):
            declared = float(declared)
        equal_nodata = ds.nodata == declared or (
            ds.nodata is not None and declared is not None
            and math.isnan(ds.nodata) and math.isnan(declared))
        if (ds.count != 1 or ds.dtypes != ("float32",) or not ds.crs
                or ds.crs.to_string() != city["crs"] or (a.a, a.b, a.d, a.e) != (.5, 0, 0, -.5)
                or not equal_nodata):
            raise InvalidInput(f"raw sheet {path.name}: grid, float32 type or declared NoData differs")
        addresses = tuple(v / RESOLUTION for v in ds.bounds)
        if any(not math.isfinite(v) or abs(v - round(v)) > 1e-7 for v in addresses):
            raise InvalidInput(f"raw sheet {path.name}: origin is off the 0.5 m lattice")
        bounds = tuple(round(v) for v in addresses)
        if any(intersects(bounds, item[2]) for item in opened):
            raise InvalidInput(f"raw sheet {path.name}: sheets overlap")
        opened.append((path, ds, bounds, stamp))
    return opened, sheets


def _extent_centre(opened, city):
    bounds = [m(item[2][i] for item in opened) * RESOLUTION
              for i, m in enumerate((min, min, max, max))]
    if bounds != city["extent"]:
        raise InvalidInput("city.extent: differs from the bounding box of the sheets")
    left, bottom, right, top = bounds
    transformer = pyproj.Transformer.from_crs(city["crs"], "EPSG:4326", always_xy=True)
    try:
        lon, lat = transformer.transform((left + right) / 2, (bottom + top) / 2, errcheck=True)
    except ProjError as exc:
        raise InvalidInput("city.extent: cannot project its centre to WGS84") from exc
    ref_lat, ref_lon = city["daylight_reference"]
    if math.hypot(ref_lat - lat, (ref_lon - lon + 180) % 360 - 180) > 0.01:
        raise InvalidInput("city.daylight_reference: must be within 0.01° of the extent centre")
    return [lat, lon]


def _cells(opened, width, height):
    cells = {}
    for _, ds, (l, b, r, t), _ in opened:
        for x in range(l // width, (r - 1) // width + 1):
            for y in range(b // height, (t - 1) // height + 1):
                cells.setdefault((x, y), []).append((ds, (l, b, r, t)))
    for (x, y), sources in sorted(cells.items()):
        left, bottom = x * width, y * height
        yield (left, bottom, left + width, bottom + height), sources


def _read_cell(bounds, sources):
    left, bottom, right, top = bounds
    data = np.full((top - bottom, right - left), NODATA, np.float32)
    for ds, (sl, sb, sr, st) in sources:
        l, b, r, t = max(left, sl), max(bottom, sb), min(right, sr), min(top, st)
        values = ds.read(1, window=Window(l - sl, st - t, r - l, t - b))
        bad = ~np.isfinite(values)
        if ds.nodata is not None:
            bad |= values == ds.nodata
        if np.any((values == NODATA) & ~bad):
            raise InvalidInput(f"raw sheet {Path(ds.name).name}: valid pixel equals -9999.0")
        values[bad] = NODATA
        data[top - t:top - b, l - left:r - left] = values
    return data


def _percentiles(values):
    result = {str(p): None for p in (1, 50, 99)}
    if values.size:
        ranks = {p: (values.size - 1) * int(p) / 100 for p in result}
        indices = {index for rank in ranks.values() for index in (math.floor(rank), math.ceil(rank))}
        values.partition(sorted(indices))
        for p, rank in ranks.items():
            low = math.floor(rank)
            fraction = rank - low
            result[p] = (1 - fraction) * float(values[low]) + fraction * float(values[math.ceil(rank)])
    return result


def _stage_catalogue(stage, opened, sheets, city, centre, h_fill):
    tiles = stage / "tiles"
    tiles.mkdir(parents=True)
    source_pixels = sum(ds.width * ds.height for _, ds, _, _ in opened)
    scratch = stage / "valid.f32"
    values = np.memmap(scratch, mode="w+", dtype=np.float32, shape=(source_pixels,))
    minimum, maximum = math.inf, -math.inf
    valid_count = below_count = catalogue_pixels = 0
    records = []
    width, height = city["ingest"]["cell_pixels"]
    for bounds, sources in _cells(opened, width, height):
        data = _read_cell(bounds, sources)
        valid = data[data != NODATA]
        if valid.size:
            values[valid_count:valid_count + valid.size] = valid
            minimum, maximum = min(minimum, float(valid.min())), max(maximum, float(valid.max()))
            below_count += int(np.count_nonzero(valid < h_fill))
        valid_count += int(valid.size)
        catalogue_pixels += int(data.size)
        left, bottom, right, top = [v * RESOLUTION for v in bounds]
        name = f"e{left:.1f}n{bottom:.1f}".replace(".0", "") + ".tif"
        path = tiles / name
        write_raster(path, data, from_origin(left, top, RESOLUTION, RESOLUTION), city["crs"], NODATA)
        records.append(dict(name=name, bounds=[left, bottom, right, top], sha256=digest(path),
                            valid_pixels=int(valid.size), nodata_pixels=int(data.size - valid.size)))
    percentiles = _percentiles(values[:valid_count])
    del values
    scratch.unlink()
    warnings = []
    if below_count:
        warnings.append("fill_above_ground")
    if valid_count and percentiles["1"] - h_fill > 10:
        warnings.append("fill_far_below_ground")
    manifest = dict(schema=MANIFEST_SCHEMA, policy=city["ingest"]["policy"],
                    profile=city, profile_sha256=identity(city), sheets=sheets, cells=records,
                    versions=dict(python=platform.python_version(), numpy=np.__version__,
                                  rasterio=rasterio.__version__, gdal=rasterio.__gdal_version__,
                                  pyproj=pyproj.__version__, proj=pyproj.proj_version_str),
                    ingestion_code_sha256={name: digest(Path(__file__).with_name(name)) for name in
                                           ("__init__.py", "__main__.py", "profiles.py", "ingest.py")})
    manifest["ingest_id"] = identity(manifest)
    report = dict(ingest_id=manifest["ingest_id"], valid_pixels=valid_count,
                  nodata_pixels=source_pixels - valid_count,
                  padding_nodata_pixels=catalogue_pixels - source_pixels,
                  minimum_m=minimum if valid_count else None, maximum_m=maximum if valid_count else None,
                  percentiles_m=percentiles, extent_centre=centre, h_fill_m=h_fill,
                  valid_pixels_below_fill=below_count,
                  share_valid_below_fill=below_count / valid_count if valid_count else 0.0,
                  warnings=warnings)
    atomic_json(stage / "manifest.json", manifest)
    atomic_json(stage / "registration_report.json", report)
    return manifest, report


def _file_hashes(folder):
    entries = {}
    for path in folder.rglob("*"):
        if path.is_symlink():
            raise InvalidInput("city catalogue: ingestion files cannot use symlinks")
        entries[path.relative_to(folder).as_posix()] = None if path.is_dir() else digest(path)
    return entries


def _publish(root, opened, sheets, city, centre, profile):
    with tempfile.TemporaryDirectory(prefix=".ingest-", dir=root) as pending:
        stage = Path(pending) / "catalogue"
        manifest, report = _stage_catalogue(stage, opened, sheets, city, centre, profile["h_sea_m"])
        if any(_stamp(path) != stamp for path, _, _, stamp in opened):
            raise InvalidInput("raw sheets changed during ingestion")
        ingest_id = manifest["ingest_id"]
        destination = root / ingest_id
        if destination.is_symlink():
            raise InvalidInput("city catalogue: destination cannot use symlinks")
        if destination.exists():
            if not destination.is_dir() or _file_hashes(stage) != _file_hashes(destination):
                raise InvalidInput("city catalogue: repeat registration differs at the same ingest_id")
        else:
            stage.rename(destination)
    return destination, report


def register(city_id, machine):
    city = load_city(city_id)
    if city["ingest"] is None:
        raise InvalidInput("city: Hong Kong uses its existing catalogue and view")
    machine = machine_config(machine, require_dsm=False)
    raw_dir = machine.get("cities", {}).get(city_id, {}).get("raw_dir")
    if raw_dir is None or not (raw := (v1.ROOT / raw_dir).resolve()).is_dir():
        raise InvalidInput(f"cities.{city_id}.raw_dir: sheet directory is required")
    validate_output_root(dict(machine, dsm_dir=str(raw)))
    scoped = dict(machine, sea_profile=city["sea_profile"])
    profile = fill_profile(city, scoped)
    root = catalogue_root(city)
    with ExitStack() as stack:
        stack.enter_context(rasterio.Env(GDAL_PAM_ENABLED=False, GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                                        PROJ_NETWORK="OFF"))
        opened, sheets = _open_sheets(raw, city, stack)
        centre = _extent_centre(opened, city)
        root.mkdir(parents=True, exist_ok=True)
        lock = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, lock)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InvalidInput("city catalogue: another registration owns this city") from exc
        pointer = root / "current.json"
        if pointer.is_symlink():
            raise InvalidInput("city catalogue: current pointer cannot use symlinks")
        destination, report = _publish(root, opened, sheets, city, centre, profile)
        scoped["dsm_dir"] = str(destination / "tiles")
        try:
            view = SeaSource().catalogue(scoped).parent
        except InvalidInput as exc:
            if str(exc) != MISSING:
                raise
            built = build(scoped, profile=profile)
            view_id = built["view_id"]
        else:
            view_id = verify_view(view)["view_id"]
        current = dict(schema=POINTER_SCHEMA, city_id=city_id, ingest_id=report["ingest_id"])
        if not pointer.is_file() or load_json(pointer) != current:
            atomic_json(pointer, current)
    return dict(city_id=city_id, ingest_id=report["ingest_id"], view_id=view_id,
                cells=len(list((destination / "tiles").glob("*.tif"))), registration_report=report)
