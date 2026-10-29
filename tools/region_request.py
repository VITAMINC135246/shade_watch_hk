"""Read-only two-corner planning and request-file writer (SW-RGN-AC-1.0)."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import shlex
import sys

import pyproj
from pyproj import Transformer

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import v1, v2
from src.spatial import intersects


def project_corner(corner, crs):
    """WGS84 means (latitude, longitude); HK1980 means (easting, northing)."""
    if crs not in ("wgs84", "hk1980"):
        raise ValueError("CRS must explicitly be wgs84 or hk1980")
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
        x, y = Transformer.from_crs("EPSG:4326", "EPSG:2326", always_xy=True).transform(b, a)
    else:
        x, y = a, b
    if not all(math.isfinite(x) for x in (x, y)):
        raise ValueError("Projection produced non-finite coordinates")
    return x, y


def _budget_error(exc):
    return any(s in str(exc) for s in ("memory budget", "artifact budget", "1..4096"))


def plan_region(corner1, corner2, *, crs, instants, dsm_dir=None,
                output_dir="outputs/region_request", cache_dir="data/processed/shade_v1/region_dev",
                max_pixels_per_request=None, memory_budget_mb=8192,
                artifact_budget_bytes=v2.ARTIFACT_CEILING):
    """Return strict-JSON provenance and validated V2 request-file payloads; no writes."""
    first, second = project_corner(corner1, crs), project_corner(corner2, crs)
    bounds = (min(first[0], second[0]), min(first[1], second[1]),
              max(first[0], second[0]), max(first[1], second[1]))
    if bounds[0] == bounds[2] or bounds[1] == bounds[3]:
        raise ValueError("Rectangle has zero width or height")
    limit = v1.MAX_OUTPUT_PIXELS if max_pixels_per_request is None else max_pixels_per_request
    if type(limit) is not int or not 0 < limit <= v1.MAX_OUTPUT_PIXELS:
        raise ValueError("Test-only max_pixels_per_request must be positive and at most the V1 limit")
    records = v1.index_sources(dsm_dir or v1.RAW)
    if not records or not any(intersects(bounds, r['bounds']) for r in records):
        raise ValueError("Requested rectangle intersects no DSM tile in the catalogue")
    grid = v1._custom_grid(records, bounds)
    resolved = grid.bounds()
    out = v1._owned_path(output_dir, 'outputs', 'outputs/region_request')
    base = dict(mode="custom", instants=[instants] if isinstance(instants, str) else list(instants),
                dsm_dir=str(Path(dsm_dir or v1.RAW).resolve()), cache_dir=str(cache_dir),
                memory_budget_mb=memory_budget_mb)
    def request(part, i):
        return dict(base, bounds=list(part), id=f"region_{i:04d}", output_dir=str(out / f"part_{i:04d}"))
    def validate(req):
        return v1.plan_shade(**{k: v for k, v in req.items() if k != "id"}, _records=records)
    parts = [bounds]
    single = None
    if grid.width * grid.height <= limit:
        try:
            single = validate(request(bounds, 0))
        except ValueError as exc:
            if "artifact profile" not in str(exc):
                raise
    lattice = dict(x=sorted({r['bounds'][i] for r in records for i in (0, 2)}),
                   y=sorted({r['bounds'][i] for r in records for i in (1, 3)}))
    if single is None:
        xs = [resolved[0]] + [x for x in lattice['x'] if resolved[0] < x < resolved[2]] + [resolved[2]]
        ys = [resolved[1]] + [y for y in lattice['y'] if resolved[1] < y < resolved[3]] + [resolved[3]]
        if (len(xs)-1)*(len(ys)-1) > 4096:
            raise ValueError("Native lattice partition exceeds adapter's 4096-part planning bound")
        parts = [(l,b,r,t) for b,t in zip(ys,ys[1:]) for l,r in zip(xs,xs[1:])]
    requests, partition = [], []
    for i, part in enumerate(parts):
        req = request(part, i)
        try:
            plan = single if single is not None else validate(req)
        except ValueError as exc:
            raise ValueError(f"Native lattice part {part} cannot be planned: {exc}") from exc
        if plan.grid.width * plan.grid.height > limit:
            raise ValueError(f"Native lattice part {part} exceeds max_pixels_per_request; no native boundary remains")
        requests.append(req)
        partition.append(dict(id=req['id'], requested_bounds=list(part), resolved_bounds=list(plan.grid.bounds()),
                              grid=asdict(plan.grid), key=plan.key, tiles=[t.source['path'] for t in plan.tiles],
                              resources=plan.resources))
    settings = dict(workers=1, logical_mosaic=True, memory_budget_mb=memory_budget_mb,
                    artifact_budget_bytes=artifact_budget_bytes)
    batches, summaries, pending, admitted = [], [], [], None
    def finish():
        batches.append(dict(settings, requests=list(pending)))
        summaries.append(dict(id=admitted.id, estimate=admitted.estimate,
                              resources=admitted.definition['resources'],
                              horizon_tasks=sum(t['kind']=='horizon' for t in admitted.definition['tasks']),
                              request_ids=[r['id'] for r in pending]))
    for req in requests:
        try:
            trial = v2.plan_batch(pending+[req], **settings)
        except ValueError as exc:
            if not _budget_error(exc):
                raise
            if not pending:
                raise ValueError(f"One native partition cannot fit a batch budget: {exc}") from exc
            finish()
            pending = []
            try:
                trial = v2.plan_batch([req], **settings)
            except ValueError as single_exc:
                raise ValueError(f"One native partition cannot fit a batch: {single_exc}") from single_exc
        pending.append(req)
        admitted = trial
    finish()
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2326", always_xy=True)
    transformer.transform(114.2, 22.3)
    sidecar = dict(schema="shade-watch-region-request-1.0", contract="SW-RGN-AC-1.0",
                   original_corners=[list(map(float, corner1)), list(map(float, corner2))], crs=crs,
                   coordinate_order="latitude,longitude" if crs=='wgs84' else "easting,northing",
                   projected_corners=[first,second], transformer_description=transformer.description,
                   transformation_applied=crs=='wgs84', pyproj_version=pyproj.__version__, proj_version=pyproj.proj_version_str,
                   requested_bounds=bounds, resolved_bounds=resolved, resolved_grid=asdict(grid),
                   native_lattice=lattice, partition=partition, generated_request_ids=[r['id'] for r in requests],
                   batches=summaries, request_files=[f"batch_{i:04d}.json" for i in range(len(batches))])
    if len(requests)==1:
        req=requests[0]
        args=[sys.executable,'-m','src.v1','query','--mode','custom','--bounds',*map(str,req['bounds']),
              '--dsm-dir',req['dsm_dir'],'--cache',req['cache_dir'],'--output',req['output_dir'],
              '--memory-budget-mb',str(memory_budget_mb)]
        for at in req['instants']:
            args.extend(['--at',str(at)])
        sidecar['v1_command']=shlex.join(args)
    return dict(sidecar=sidecar, batches=batches)


def write_region(plan, directory):
    """Create a fresh request directory outside every engine output/cache directory."""
    directory=Path(directory).resolve()
    for batch in plan['batches']:
        for req in batch['requests']:
            for key in ('output_dir','cache_dir'):
                engine=(v1.ROOT / req[key]).resolve()
                if directory.is_relative_to(engine) or engine.is_relative_to(directory):
                    raise ValueError("Sidecar directory must be separate from engine output/cache directories")
    directory.mkdir(parents=True, exist_ok=False)
    for name, batch in zip(plan['sidecar']['request_files'],plan['batches']):
        (directory/name).write_text(json.dumps(batch,indent=2,allow_nan=False)+'\n')
    (directory/'region_request.json').write_text(json.dumps(plan['sidecar'],indent=2,allow_nan=False)+'\n')
    return directory


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','write'])
    parser.add_argument('--crs',required=True,choices=['wgs84','hk1980'])
    parser.add_argument('--corner1',nargs=2,type=float,required=True)
    parser.add_argument('--corner2',nargs=2,type=float,required=True)
    parser.add_argument('--at',action='append',required=True)
    parser.add_argument('--dsm-dir')
    parser.add_argument('--output',required=True)
    parser.add_argument('--cache',default='data/processed/shade_v1/region_dev')
    parser.add_argument('--directory',help='Fresh directory for request files and sidecar')
    args=parser.parse_args(argv)
    try:
        if args.action=='write' and not args.directory:
            raise ValueError('write requires --directory')
        plan=plan_region(args.corner1,args.corner2,crs=args.crs,instants=args.at,dsm_dir=args.dsm_dir,
                         output_dir=args.output,cache_dir=args.cache)
        if args.action=='write':
            write_region(plan,args.directory)
        print(json.dumps(plan['sidecar'],indent=2,allow_nan=False))
    except (ValueError,OSError) as exc:
        parser.exit(2,f'Region request rejected: {exc}\n')


if __name__=='__main__':
    main()
