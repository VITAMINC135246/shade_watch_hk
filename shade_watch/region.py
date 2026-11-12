"""Two-corner region adapter (SW-RGN-AC-1.1); never starts shade computation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import time

import numpy as np
import pyproj
from pyproj import Transformer
import rasterio

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shade_watch.engine import v1, v2
from shade_watch.engine.spatial import intersects
from shade_watch.engine.v1_cache import BUFFER_M

_HEADER_CACHE = {}


def project_corner(corner, crs, *, dsm_crs=v1.DEFAULT_CRS):
    """WGS84 pairs are (latitude, longitude); HK1980 pairs are (east, north)."""
    if crs not in ("wgs84", "hk1980", "projected"):
        raise ValueError("CRS must explicitly be wgs84, hk1980 or projected")
    if crs == "hk1980" and dsm_crs != v1.DEFAULT_CRS:
        raise ValueError("hk1980 requires an EPSG:2326 DSM")
    if len(corner) != 2:
        raise ValueError("Each corner needs exactly two coordinates")
    try:
        a, b = map(float, corner)
    except (TypeError, ValueError) as exc:
        raise ValueError("Corner coordinates must be numeric and finite") from exc
    if not all(math.isfinite(x) for x in (a, b)):
        raise ValueError("Corner coordinates must be finite")
    if crs == "wgs84":
        if not -90 <= a <= 90 or not -180 <= b <= 180:
            raise ValueError("WGS84 latitude must be -90..90 and longitude -180..180")
        x, y = Transformer.from_crs("EPSG:4326", dsm_crs, always_xy=True).transform(b, a)
    else:
        x, y = a, b
    if not all(math.isfinite(x) for x in (x, y)):
        raise ValueError("Projection produced non-finite coordinates")
    return x, y


def _stat(path):
    info = Path(path).stat()
    return dict(path=str(Path(path).resolve()), bytes=info.st_size, mtime_ns=info.st_mtime_ns)


def header_catalogue(directory):
    """Header-only index; no raster data/hash reads. Cache lives only in-process."""
    headers = []
    for path in sorted(Path(directory).glob("*.tif")):
        signature = _stat(path)
        auxiliary_candidates = [Path(str(path)+suffix) for suffix in ('.msk', '.aux.xml')]
        auxiliary_candidates += [path.with_suffix(suffix) for suffix in ('.tfw', '.wld')]
        auxiliary_stamps = [_stat(p) for p in auxiliary_candidates if p.is_file()]
        key = tuple(signature.values()) + tuple(tuple(v.values()) for v in auxiliary_stamps)
        header = _HEADER_CACHE.get(key)
        if header is None:
            with rasterio.open(path) as ds:
                header = dict(signature, width=ds.width, height=ds.height, crs=ds.crs.to_string() if ds.crs else None,
                              transform=list(ds.transform)[:6], bounds=list(ds.bounds),
                              auxiliary_paths=sorted(str(Path(f).resolve()) for f in ds.files
                                                     if Path(f).resolve() != path.resolve()))
            _HEADER_CACHE[key] = header
        # Auxiliary identities must be refreshed even when the TIFF is unchanged.
        headers.append(dict(header, auxiliary_files=[_stat(f) for f in header['auxiliary_paths']]))
    if not headers:
        raise ValueError("No DSM GeoTIFF files found in the catalogue")
    return headers


def source_view(directory, bounds):
    """Publish/reuse an immutable symlink view of all owning tiles' halo sources."""
    started = time.perf_counter()
    headers = header_catalogue(directory)
    grid = v1._custom_grid(headers, bounds)
    targets = [r for r in headers if intersects(grid.bounds(), r['bounds'])]
    if not targets:
        raise ValueError("Requested rectangle intersects no DSM tile in the catalogue")
    halos = [(r['bounds'][0]-BUFFER_M, r['bounds'][1]-BUFFER_M,
              r['bounds'][2]+BUFFER_M, r['bounds'][3]+BUFFER_M) for r in targets]
    selected = [r for r in headers if any(intersects(r['bounds'], halo) for halo in halos)]
    shifted = [Path(r['path']).name for r in selected
               if Path(r['path']).stem.split('(')[0] in {'14NE15A', '14NE15B', '14NE15C', '14NE15D'}]
    if shifted:
        raise ValueError("Source view needs shifted-origin tiles " + ', '.join(shifted) +
                         "; blocked by the pending shifted-origin DSM ingestion policy. Raw data is unchanged.")
    definition = dict(schema='shade-watch-region-source-view-1.0', catalogue=str(Path(directory).resolve()),
                      halo_m=BUFFER_M, sources=selected)
    token = hashlib.sha256(json.dumps(definition, sort_keys=True, allow_nan=False).encode()).hexdigest()
    parent = v1.ROOT / 'work/source_views'
    path = parent / token
    links = {}
    for record in selected:
        for filename in [record['path']] + record['auxiliary_paths']:
            name = Path(filename).name
            if name in links and links[name] != filename:
                raise ValueError(f"Source view has an auxiliary filename collision: {name}")
            links[name] = filename
    if path.exists():
        if json.loads((path/'source_view.json').read_text()) != definition:
            raise ValueError("Existing source view manifest changed")
        if set(p.name for p in path.iterdir()) != set(links) | {'source_view.json'}:
            raise ValueError("Existing source view contains unexpected/missing files")
        if any(not (path/name).is_symlink() or (path/name).resolve() != Path(target)
               for name, target in links.items()):
            raise ValueError("Existing source view symlinks changed")
    else:
        parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='.region_', dir=parent))
        try:
            for name, target in links.items():
                (stage/name).symlink_to(target)
            (stage/'source_view.json').write_text(json.dumps(definition, indent=2, allow_nan=False)+'\n')
            try:
                stage.rename(path)
            except FileExistsError:
                # A concurrent identical publisher is safe only after validation.
                return source_view(directory, bounds)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return path, dict(path=str(path), identity=token, catalogue_tiles=len(headers), source_tiles=len(selected),
                      target_tiles=[r['path'] for r in targets], header_and_view_seconds=time.perf_counter()-started)


def _budget_error(exc):
    return any(s in str(exc) for s in ('memory budget', 'artifact budget', '1..4096', 'metadata exceeds'))


def _partition(records, bounds, limit, forbidden):
    """Rectangular native-edge partition, minimizing residual pixels then parts.

    Exact memoized guillotine search on small domains; bounded candidate search
    on large domains. Never allocates an array proportional to output pixels.
    """
    rect = tuple(round(v/.5) for v in bounds)
    sources = [tuple(round(v/.5) for v in r['bounds']) for r in records if intersects(bounds, r['bounds'])]
    origin = tuple(round(v/.5) for v in records[0]['bounds'][:2])
    steps = []
    for axis in (0, 1):
        sizes = [r['width' if axis == 0 else 'height'] for r in records]
        offsets = [round(r['bounds'][axis]/.5)-origin[axis] for r in records]
        steps.append(math.gcd(*sizes, *offsets))
    calls = 0

    def area(r):
        return (r[2]-r[0])*(r[3]-r[1])

    @lru_cache(None)
    def owners(r):
        return tuple(s for s in sources if intersects(r, s))

    def cuts(r, axis):
        lo, hi, pitch, phase = r[axis], r[axis+2], steps[axis], origin[axis]
        first, last = (lo-phase)//pitch+1, (hi-phase-1)//pitch
        if last-first <= 24:
            return [phase+i*pitch for i in range(first, last+1)]
        values = {s[i] for s in owners(r) for i in (axis, axis+2)}
        other = r[3-axis]-r[1-axis]
        count = max(1, limit//(other*pitch))
        for edge in (lo, hi, (lo+hi)//2):
            for offset in (-count, -1, 0, 1, count):
                values.add(phase+((edge-phase)//pitch+offset)*pitch)
        return sorted(v for v in values if lo < v < hi and (v-phase) % pitch == 0)

    def split(r, axis, cut):
        a, b = list(r), list(r)
        a[axis+2], b[axis] = cut, cut
        return tuple(a), tuple(b)

    def score(solution):
        parts, gaps = solution
        return sum(area(g) for g in gaps), len(parts), sum((r[2]-r[0])+(r[3]-r[1]) for r in parts)

    @lru_cache(None)
    def solve(r):
        nonlocal calls
        calls += 1
        if not owners(r):
            return (), (r,)
        if area(r) <= limit and r not in forbidden:
            return (r,), ()
        candidates = [split(r, axis, cut) for axis in (0, 1) for cut in cuts(r, axis)]
        if not candidates:
            raise ValueError(f"Native lattice part {tuple(v*.5 for v in r)} exceeds a limit; no native boundary remains")
        def order(pair):
            return (sum(area(c) for c in pair if not owners(c)),
                    sum(math.ceil(area(c)/limit) for c in pair), abs(area(pair[0])-area(pair[1])))
        candidates.sort(key=order)
        if calls > 4096:
            candidates = candidates[:1]
        elif len(candidates) > 32:
            candidates = candidates[:8]
        best = None
        for a, b in candidates:
            try:
                ap, ag = solve(a)
                bp, bg = solve(b)
            except ValueError:
                continue
            candidate = ap+bp, ag+bg
            if best is None or score(candidate) < score(best):
                best = candidate
            if score(best)[:2] == (0, math.ceil(area(r)/limit)):
                break
        if best is None:
            raise ValueError("An indivisible native lattice part cannot fit the engine/test limit; no native boundary remains")
        return best

    parts, gaps = solve(rect)
    return ([tuple(v*.5 for v in r) for r in sorted(parts)],
            [dict(bounds=tuple(v*.5 for v in r), reason='No lattice-aligned merge into an owning part fits the current area/artifact limits',
                  shade=255, quality=1) for r in sorted(gaps)],
            dict(origin_pixels=origin, step_pixels=steps, searched_rectangles=calls,
                 method='guillotine search; minimize residual area, then part count'))


def _time_groups(instants, dates, interval_minutes, probe):
    if (instants is None) == (dates is None):
        raise ValueError('Supply exactly one of instants or dates')
    def strings(values):
        if isinstance(values, str) or hasattr(values, 'isoformat'):
            values = [values]
        return [v.isoformat() if hasattr(v, 'isoformat') else v for v in values]
    time_input = dict(instants=strings(instants)) if instants is not None else dict(dates=strings(dates))
    time_input['interval_minutes'] = interval_minutes
    if dates is not None and not time_input['dates']:
        raise ValueError('Daylight dates must contain at least one date')
    try:
        planned = probe(time_input)
        return [dict(input=time_input, utc_times=[i.utc for i in planned.request.instants])]
    except ValueError as exc:
        if dates is None or not any(s in str(exc) for s in ('512-frame', 'Daylight dates exceed')):
            raise
    groups, pending, utc = [], [], []
    # A complete date is the atomic temporal unit; the engine expands each one.
    for day in time_input['dates']:
        try:
            planned = probe(dict(dates=[day], interval_minutes=interval_minutes))
        except ValueError as exc:
            raise ValueError(f'Daylight date {day} cannot fit V1: {exc}; use a larger interval') from exc
        times = [i.utc for i in planned.request.instants]
        if pending and len(utc)+len(times) > v1.MAX_FRAMES:
            groups.append(dict(input=dict(dates=pending, interval_minutes=interval_minutes), utc_times=utc))
            pending, utc = [], []
        pending.append(day)
        utc.extend(times)
    if pending:
        groups.append(dict(input=dict(dates=pending, interval_minutes=interval_minutes), utc_times=utc))
    return groups


def plan_region(corner1, corner2, *, crs, instants=None, dates=None, interval_minutes=10,
                dsm_dir=None, auto_source_view=False, output_dir='work/engine/region_request',
                cache_dir='data/cache/horizon/region_dev', max_pixels_per_request=None,
                memory_budget_mb=8192, artifact_budget_bytes=v2.ARTIFACT_CEILING,
                dsm_crs=v1.DEFAULT_CRS, local_timezone=v1.HKT.key,
                daylight_reference=v1.DAYLIGHT_REFERENCE, dsm_source_line=v1.SOURCE_LINE):
    """Resolve inputs and validate engine plans. Only the opt-in source view writes."""
    started = time.perf_counter()
    first = project_corner(corner1, crs, dsm_crs=dsm_crs)
    second = project_corner(corner2, crs, dsm_crs=dsm_crs)
    bounds = (min(first[0], second[0]), min(first[1], second[1]),
              max(first[0], second[0]), max(first[1], second[1]))
    if bounds[0] == bounds[2] or bounds[1] == bounds[3]:
        raise ValueError('Rectangle has zero width or height')
    limit = v1.MAX_OUTPUT_PIXELS if max_pixels_per_request is None else max_pixels_per_request
    if type(limit) is not int or not 0 < limit <= v1.MAX_OUTPUT_PIXELS:
        raise ValueError('Test-only max_pixels_per_request must be positive and at most the V1 limit')
    if type(auto_source_view) is not bool:
        raise ValueError('auto_source_view must be a boolean')
    if (instants is None) == (dates is None):
        raise ValueError('Supply exactly one of instants or dates')
    source_directory = Path(dsm_dir or v1.RAW).resolve()
    view = None
    if auto_source_view:
        source_directory, view = source_view(source_directory, bounds)
    indexed = time.perf_counter()
    records = v1.index_sources(source_directory, dsm_crs)
    indexing_seconds = time.perf_counter()-indexed
    if not any(intersects(bounds, r['bounds']) for r in records):
        raise ValueError('Requested rectangle intersects no DSM tile in the catalogue')
    grid = v1._custom_grid(records, bounds)
    out = v1._owned_path(output_dir, 'work', 'work/engine/region_request')
    cache = v1._owned_path(cache_dir, 'data/cache/horizon', 'data/cache/horizon/region_dev')
    base = dict(mode='custom', dsm_dir=str(source_directory), cache_dir=str(cache), memory_budget_mb=memory_budget_mb)
    if dsm_crs != v1.DEFAULT_CRS:
        base['crs'] = dsm_crs
    if local_timezone != v1.HKT.key:
        base['local_timezone'] = local_timezone
    if tuple(daylight_reference) != v1.DAYLIGHT_REFERENCE:
        base['daylight_reference'] = tuple(daylight_reference)
    if dsm_source_line != v1.SOURCE_LINE:
        base['dsm_source_line'] = dsm_source_line
    target = next(r for r in records if intersects(grid.bounds(), r['bounds']))
    def probe(time_input):
        return v1.plan_shade(**base, **time_input, bounds=target['bounds'], output_dir=out/'temporal_probe', _records=records)
    groups = _time_groups(instants, dates, interval_minutes, probe)
    forbidden = set()
    while True:
        if grid.width*grid.height <= limit and tuple(round(v/.5) for v in grid.bounds()) not in forbidden:
            parts, gaps = [bounds], []
            lattice = dict(method='single unchanged V1 request')
        else:
            parts, gaps, lattice = _partition(records, grid.bounds(), limit, forbidden)
        planned, requests, request_parts, failed = [], [], [], False
        for g, group in enumerate(groups):
            for i, part in enumerate(parts):
                output = out / (f'dates_{g:04d}' if len(groups)>1 else '') / f'part_{i:04d}'
                req = dict(base, **group['input'], bounds=list(part), output_dir=str(output))
                try:
                    plan = v1.plan_shade(**req, _records=records)
                except ValueError as exc:
                    if 'artifact profile' not in str(exc):
                        raise
                    forbidden.add(tuple(round(v/.5) for v in v1._custom_grid(records, part).bounds()))
                    failed = True
                    break
                planned.append(plan)
                requests.append(req)
                request_parts.append(dict(partition_id=f'part_{i:04d}', time_group=g, key=plan.key, grid=asdict(plan.grid),
                                          utc_times=group['utc_times'], output_directory=plan.output_directory,
                                          tiles=[t.source['path'] for t in plan.tiles], resources=plan.resources))
            if failed:
                break
        if not failed:
            break
    settings = dict(workers=1, logical_mosaic=True, memory_budget_mb=memory_budget_mb,
                    artifact_budget_bytes=artifact_budget_bytes)
    admitted = []
    def pack(indices):
        if len(indices)>4096:
            pack(indices[:4096]); pack(indices[4096:]); return
        try:
            batch = v2.plan_batch([planned[i] for i in indices], **settings)
        except ValueError as exc:
            if not _budget_error(exc):
                raise
            if len(indices)==1:
                raise ValueError(f'One native partition cannot fit a batch budget: {exc}') from exc
            mid = len(indices)//2
            pack(indices[:mid]); pack(indices[mid:]); return
        admitted.append((indices, batch))
    pack(list(range(len(planned))))
    batches, summaries, generated = [], [], []
    for b, (indices, batch) in enumerate(admitted):
        name = f'batch_{b:04d}.json'
        payload = []
        for j, idx in enumerate(indices):
            local_id = f'request_{j:04d}'
            qualified = name+'#'+local_id
            payload.append(dict(requests[idx], id=local_id))
            request_parts[idx].update(id=qualified, batch=b, engine_request_id=local_id)
            generated.append(qualified)
        batches.append(dict(settings, requests=payload))
        summaries.append(dict(id=batch.id, request_file=name, estimate=batch.estimate,
                              resources=batch.definition['resources'], request_ids=[request_parts[i]['id'] for i in indices],
                              utc_times=sorted({t for i in indices for t in request_parts[i]['utc_times']}),
                              horizon_tasks=sum(t['kind']=='horizon' for t in batch.definition['tasks'])))
    transformer = Transformer.from_crs('EPSG:4326', dsm_crs, always_xy=True)
    transformer.transform(daylight_reference[1], daylight_reference[0])
    sidecar = dict(schema='shade-watch-region-request-1.1', contract='SW-RGN-AC-1.1',
                   original_corners=[list(map(float, corner1)), list(map(float, corner2))], crs=crs,
                   coordinate_order='latitude,longitude' if crs=='wgs84' else 'easting,northing',
                   projected_corners=[first, second], transformer_description=transformer.description,
                   transformation_applied=crs=='wgs84', pyproj_version=pyproj.__version__, proj_version=pyproj.proj_version_str,
                   requested_bounds=bounds, resolved_bounds=grid.bounds(), resolved_grid=asdict(grid), native_lattice=lattice,
                   partition=[dict(id=f'part_{i:04d}', requested_bounds=part,
                                   resolved_bounds=v1._custom_grid(records, part).bounds(),
                                   key=planned[i].key, grid=asdict(planned[i].grid),
                                   tiles=[t.source['path'] for t in planned[i].tiles], resources=planned[i].resources)
                              for i, part in enumerate(parts)],
                   no_dsm_areas=gaps, no_dsm_encoding=dict(shade=255, quality=1), time_groups=groups,
                   requests=request_parts, generated_request_ids=generated, batches=summaries,
                   request_files=[b['request_file'] for b in summaries], source_directory=str(source_directory),
                   source_view=view, indexing_seconds=indexing_seconds, planning_seconds=time.perf_counter()-started)
    if len(requests)==1:
        req = requests[0]
        args = [sys.executable, '-m', 'shade_watch.engine.v1', 'query', '--mode', 'custom', '--bounds', *map(str, req['bounds']),
                '--dsm-dir', req['dsm_dir'], '--cache', req['cache_dir'], '--output', req['output_dir'],
                '--memory-budget-mb', str(memory_budget_mb), '--interval-minutes', str(interval_minutes)]
        for key, flag in [('crs', '--crs'), ('local_timezone', '--timezone'), ('dsm_source_line', '--dsm-source-line')]:
            if key in req:
                args.extend([flag, req[key]])
        if 'daylight_reference' in req:
            args.extend(['--daylight-reference', *map(str, req['daylight_reference'])])
        for kind, flag in [('instants', '--at'), ('dates', '--date')]:
            for value in req.get(kind, []):
                args.extend([flag, str(value)])
        sidecar['v1_command'] = shlex.join(args)
    return dict(sidecar=sidecar, batches=batches)


def write_region(plan, directory):
    """Write a fresh sidecar/request directory separate from all engine directories."""
    directory = Path(directory).resolve()
    for batch in plan['batches']:
        for req in batch['requests']:
            for key in ('output_dir', 'cache_dir', 'dsm_dir'):
                engine = (v1.ROOT / req[key]).resolve()
                if directory.is_relative_to(engine) or engine.is_relative_to(directory):
                    raise ValueError('Sidecar directory must be separate from engine output/cache/source directories')
    directory.mkdir(parents=True, exist_ok=False)
    for name, batch in zip(plan['sidecar']['request_files'], plan['batches']):
        (directory/name).write_text(json.dumps(batch, indent=2, allow_nan=False)+'\n')
    (directory/'region_request.json').write_text(json.dumps(plan['sidecar'], indent=2, allow_nan=False)+'\n')
    return directory


def read_region_window(region, *, utc_time, bounds, logical_mosaics):
    """Read completed engine mosaics, retaining explicitly recorded 255/1 residuals.

    A missing required batch is an error, never mistaken for an uncovered area.
    """
    from shade_watch.engine.v2_worker import read_logical_window
    sidecar = json.loads(Path(region).read_text()) if isinstance(region, (str, Path)) else region
    instant = v1.normalize_instant(utc_time).utc
    if instant not in {t for g in sidecar['time_groups'] for t in g['utc_times']}:
        raise ValueError('Instant is not part of this region request')
    grid = v1._custom_grid([dict(crs=sidecar['resolved_grid']['crs'])], bounds)
    if tuple(bounds) != grid.bounds() or grid.width*grid.height > v1.MAX_OUTPUT_PIXELS:
        raise ValueError('Region window must be aligned and within the V1 area limit')
    l, b, r, t = sidecar['resolved_bounds']
    if bounds[0]<l or bounds[1]<b or bounds[2]>r or bounds[3]>t:
        raise ValueError('Region window lies outside the resolved rectangle')
    needed = {q['batch'] for q in sidecar['requests'] if instant in q['utc_times'] and
              intersects(bounds, sidecar['partition'][int(q['partition_id'].split('_')[-1])]['resolved_bounds'])}
    manifests = {}
    for path in logical_mosaics:
        value = json.loads(Path(path).read_text())
        if value['batch'] in manifests:
            raise ValueError('Duplicate logical mosaic for a batch')
        manifests[value['batch']] = (path, value)
    labels = np.full((grid.height, grid.width), 255, np.uint8)
    quality = np.ones_like(labels)
    seen = np.zeros_like(labels, dtype=bool)
    for idx in sorted(needed):
        batch = sidecar['batches'][idx]
        if batch['id'] not in manifests:
            raise ValueError(f"Missing completed logical mosaic for {batch['request_file']}")
        path, value = manifests[batch['id']]
        if value['crs'] != grid.crs:
            raise ValueError('Logical mosaic CRS differs from the region')
        present = {layer['request'] for layer in value['layers'] if layer['utc_time']==instant}
        expected = {q['engine_request_id'] for q in sidecar['requests'] if q['batch']==idx and instant in q['utc_times']}
        if not expected <= present:
            raise ValueError('Logical mosaic is missing expected region requests')
        shade, flags, transform = read_logical_window(path, utc_time=instant, bounds=bounds)
        if transform != grid.affine:
            raise ValueError('Logical window transform differs')
        coverage = np.zeros_like(seen)
        for layer in value['layers']:
            if layer['utc_time']!=instant or not intersects(bounds, layer['bounds']):
                continue
            ll, bb, rr, tt = layer['bounds']
            coverage[round((bounds[3]-min(bounds[3], tt))/.5):round((bounds[3]-max(bounds[1], bb))/.5),
                     round((max(bounds[0], ll)-bounds[0])/.5):round((min(bounds[2], rr)-bounds[0])/.5)] = True
        if np.any(seen & coverage & ((labels!=shade) | (quality!=flags))):
            raise ValueError('Conflicting region logical mosaics')
        labels[coverage], quality[coverage], seen[coverage] = shade[coverage], flags[coverage], True
    return labels, quality, grid.affine


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'write'])
    parser.add_argument('--crs', required=True, choices=['wgs84', 'hk1980'])
    parser.add_argument('--corner1', nargs=2, type=float, required=True)
    parser.add_argument('--corner2', nargs=2, type=float, required=True)
    times = parser.add_mutually_exclusive_group(required=True)
    times.add_argument('--at', action='append')
    times.add_argument('--date', action='append')
    parser.add_argument('--interval-minutes', type=int, default=10)
    parser.add_argument('--dsm-dir')
    parser.add_argument('--auto-source-view', action='store_true')
    parser.add_argument('--output', required=True)
    parser.add_argument('--cache', default='data/cache/horizon/region_dev')
    parser.add_argument('--directory', help='Fresh request directory')
    args = parser.parse_args(argv)
    try:
        if args.action=='write' and not args.directory:
            raise ValueError('write requires --directory')
        plan = plan_region(args.corner1, args.corner2, crs=args.crs, instants=args.at, dates=args.date,
                           interval_minutes=args.interval_minutes, dsm_dir=args.dsm_dir, auto_source_view=args.auto_source_view,
                           output_dir=args.output, cache_dir=args.cache)
        if args.action=='write':
            write_region(plan, args.directory)
        print(json.dumps(plan['sidecar'], indent=2, allow_nan=False))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Region request rejected: {exc}\n')


if __name__=='__main__':
    main()
