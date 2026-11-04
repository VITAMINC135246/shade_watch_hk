"""Read-only F plans backed by the reviewed adapter and accepted V2 planner."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path

from src import v1, v2
from src.spatial import intersects
from tools import region_request as adapter
from .common import (CODE_ROOT, ENGINE_FILES, FORMAT, digest, identity, read_json,
                     verify_seal)
from .config import (ROOT_MARKER, InvalidInput, check_document, expanded_time, hkt_time,
                     machine_config, region_config, validate_output_root)
from .sources import SourceProvider, provider



def output_location(machine, region):
    return Path(machine['output_root']) / region['name']


def ownership(machine, region):
    root = Path(machine['output_root'])
    if root.exists():
        marker = root / ROOT_MARKER
        if not marker.is_file() or marker.is_symlink() or read_json(marker) != {'schema': 'shade-map-root-1.0'}:
            raise InvalidInput('output_root: existing folder was not created by F')
    folder = output_location(machine, region)
    if folder.is_symlink():
        raise InvalidInput('name: publication folder cannot be a symlink')
    if not folder.exists():
        return None
    # A valid sealed manifest is the ownership record, not the directory name.
    path = folder / 'run_manifest.json'
    if not path.is_file() or path.is_symlink():
        raise InvalidInput('name: existing folder was not created by F')
    try:
        manifest = read_json(path)
        check_document(manifest, 'run')
        verify_seal(manifest)
    except (ValueError, KeyError, RuntimeError) as exc:
        raise InvalidInput(f'name: existing manifest is not verifiable: {exc}') from exc
    if manifest['region_config'] != region:
        raise InvalidInput('name: existing run has a different region config')
    return manifest


def _cells(records, bounds):
    """Publication cells, not engine request partitions; derive the native phase."""
    origin = [round(v / .5) for v in records[0]['bounds'][:2]]
    steps = [math.gcd(*[r['width' if axis == 0 else 'height'] for r in records],
                      *[round(r['bounds'][axis]/.5)-origin[axis] for r in records])
             for axis in (0, 1)]
    l, b, r, t = [round(v/.5) for v in bounds]
    cells = []
    for iy in range((b-origin[1])//steps[1], (t-1-origin[1])//steps[1]+1):
        for ix in range((l-origin[0])//steps[0], (r-1-origin[0])//steps[0]+1):
            x, y = origin[0]+ix*steps[0], origin[1]+iy*steps[1]
            native = [x*.5, y*.5, (x+steps[0])*.5, (y+steps[1])*.5]
            if not native[0].is_integer() or not native[1].is_integer():
                raise InvalidInput('dsm_dir: native cell origins must be whole metres')
            clipped = [max(bounds[0], native[0]), max(bounds[1], native[1]),
                       min(bounds[2], native[2]), min(bounds[3], native[3])]
            sources = [Path(q['path']).name for q in records if intersects(native, q['bounds'])]
            if len(sources) > 1:
                raise InvalidInput('dsm_dir: more than one DSM source owns a native cell')
            cells.append(dict(id=f'e{int(native[0])}n{int(native[1])}', native_bounds=native,
                              bounds=clipped, width=round((clipped[2]-clipped[0])/.5),
                              height=round((clipped[3]-clipped[1])/.5),
                              source_tile=sources[0] if sources else None))
    return cells


def _adapter_plans(region, machine, source, temporal, provisional):
    options = dict(crs=region['crs'], dsm_dir=source.catalogue(machine), auto_source_view=True,
                   cache_dir=v1.ROOT/'data/processed/shade_v1'/source.cache_namespace(machine),
                   memory_budget_mb=min(machine['memory_budget_mb'], 8192))
    groups = [temporal]
    empty = 'instants' in temporal and not temporal['instants']
    if empty:
        # Geometry-only probe; discarded before producing any execution requests.
        time = region['time']
        day = (time['instants'][0][:10] if time['mode'] == 'instants' else time['dates'][0])
        groups = [dict(dates=[day], interval_minutes=60)]
    elif 'instants' in temporal and len(temporal['instants']) > v1.MAX_FRAMES:
        groups = [dict(temporal, instants=temporal['instants'][i:i+v1.MAX_FRAMES])
                  for i in range(0, len(temporal['instants']), v1.MAX_FRAMES)]
    plans = []
    for index, group in enumerate(groups):
        out = provisional / (f'group_{index:04d}' if len(groups) > 1 else '') / 'engine'
        plans.append(adapter.plan_region(region['lower_left'], region['upper_right'],
                                         output_dir=out, **group, **options))
    result = deepcopy(plans[0])
    sc = result['sidecar']
    if empty:
        for key in ('time_groups', 'requests', 'batches', 'request_files', 'generated_request_ids'):
            sc[key] = []
        result['batches'] = []
    else:
        for extra in plans[1:]:
            offset, batch_offset = len(sc['time_groups']), len(result['batches'])
            sc['time_groups'].extend(extra['sidecar']['time_groups'])
            for request in extra['sidecar']['requests']:
                request['time_group'] += offset
                request['batch'] += batch_offset
                sc['requests'].append(request)
            result['batches'].extend(extra['batches'])
    return result


@dataclass
class Prepared:
    region: dict
    machine: dict
    source: SourceProvider
    records: list
    adapter_plan: dict
    batch_plans: list
    identity_document: dict
    document: dict
    work: Path
    folder: Path


def prepare(region, machine='config/machine.local.json'):
    region, machine = region_config(region), machine_config(machine)
    source = provider(region['dsm_source'])
    validate_output_root(machine, (source.catalogue(machine),))
    conflict = None
    try:
        existing = ownership(machine, region)
    except InvalidInput as exc:
        existing, conflict = None, str(exc)
    temporal, dropped = expanded_time(region['time'])
    provisional = v1.ROOT/'outputs/shade_map_work'/(region['name']+'-plan')
    try:
        adapted = _adapter_plans(region, machine, source, temporal, provisional)
        records = v1.index_sources(adapted['sidecar']['source_directory'])
    except ValueError as exc:
        raise InvalidInput(str(exc)) from exc
    sc = adapted['sidecar']
    frames = []
    for group in sc['time_groups']:
        for utc in group['utc_times']:
            instant = v1.normalize_instant(utc)
            local = hkt_time(instant.utc)
            frames.append(dict(local_time=local.isoformat(), utc_time=instant.utc,
                               date=f'{local.year:04d}{local.month:02d}{local.day:02d}',
                               time=f'{local.hour:02d}{local.minute:02d}'))
    if len({f['date']+'/'+f['time'] for f in frames}) != len(frames):
        raise InvalidInput('time: duplicate Hong Kong frame folder')
    hashes = {p: digest(CODE_ROOT/p) for p in ENGINE_FILES}
    identity_document = dict(region_config=region, frames=frames,
                             source_identity=source.source_identity(records), engine_hashes=hashes,
                             policies=source.policies(), publication_format=FORMAT)
    run_id = identity(identity_document)
    work = v1.ROOT/'outputs/shade_map_work'/(region['name']+'-'+run_id[:12])
    for request in sc['requests']:
        request['output_directory'] = str(work/Path(request['output_directory']).relative_to(provisional))
    for batch in adapted['batches']:
        batch.update(workers=machine['workers'], memory_budget_mb=machine['memory_budget_mb'],
                     logical_mosaic=True, statistics=False)
        for req in batch['requests']:
            req['output_dir'] = str(work/Path(req['output_dir']).relative_to(provisional))
    batch_plans = []
    try:
        for payload in adapted['batches']:
            batch_plans.append(v2.plan_batch(**payload))
    except ValueError as exc:
        raise InvalidInput(str(exc)) from exc
    sc['batches'], sc['request_files'], sc['generated_request_ids'] = [], [], []
    for index, batch in enumerate(batch_plans):
        name = f'batch_{index:04d}.json'
        sc['request_files'].append(name)
        request_ids = []
        for request in sc['requests']:
            if request['batch'] == index:
                request['id'] = name+'#'+request['engine_request_id']
                request_ids.append(request['id'])
        sc['generated_request_ids'].extend(request_ids)
        sc['batches'].append(dict(id=batch.id, request_file=name, request_ids=request_ids,
                                  estimate=batch.estimate, resources=batch.definition['resources']))
    bounds, grid = sc['resolved_bounds'], json.loads(json.dumps(sc['resolved_grid']))
    cells = _cells(records, bounds)
    pixels = grid['width']*grid['height']
    full = region['full_image'] == 'auto' and pixels <= v1.MAX_OUTPUT_PIXELS
    n = len(frames)
    file_count = n*(3*len(cells)+4+3*int(full))+4
    published = n*pixels*3*(1+int(full)) + file_count*16384 + 1024*len(cells)*n
    working = sum(p.definition['resources']['estimated_peak_new_bytes'] for p in batch_plans)
    directions = {float(d) for p in batch_plans
                  for t in p.definition['tasks'] if t['kind'] == 'horizon'
                  for d in t['payload']['directions']}
    warnings = []
    if any(c['source_tile'] is None for c in cells):
        warnings.append('No-DSM cells remain shade 255, quality 1, surface 255')
    if dropped:
        warnings.append(f'{len(dropped)} requested times dropped outside daylight')
    if not frames:
        warnings.append('No frames remain inside daylight; no engine computation will run')
    if conflict or (existing and existing['run_id'] != run_id):
        status = dict(status='conflict', published_frames=0, total_frames=n,
                      reason=conflict or 'name: existing run has a different run_id')
    elif existing:
        k = sum(f['status'] == 'published' for f in existing['frames'])
        status = dict(status='complete' if existing['status']=='complete' else 'resumable',
                      published_frames=k, total_frames=n)
    else:
        status = dict(status='new', published_frames=0, total_frames=n)
    estimate = dict(label='estimate', compute_wall_seconds=sum(p.estimate['total_wall_seconds'] for p in batch_plans),
                    estimator_models=[dict(schema=p.estimate['model']['schema'],
                                           sha256=p.estimate['model'].get('model_sha256'),
                                           extrapolated=p.estimate['extrapolated']) for p in batch_plans],
                    published_bytes=dict(label='estimate', value=published),
                    working_bytes=dict(label='estimate', value=working),
                    file_count=dict(label='estimate', value=file_count))
    document = dict(schema='shade-map-plan-1.0', run_id=run_id, name=region['name'],
                    resolved_bounds=list(bounds), grid=grid, pixel_count=pixels, cells=cells,
                    frames=frames, dropped_times=dropped, sub_requests=len(sc['requests']),
                    batches=len(batch_plans), distinct_horizon_directions=len(directions),
                    estimates=estimate, full_images=full, warnings=warnings, existing_run=status)
    check_document(document, 'plan')
    return Prepared(region, machine, source, records, adapted, batch_plans,
                    identity_document, document, work, output_location(machine, region))
