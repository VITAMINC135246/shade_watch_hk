"""Read-only F plans backed by the reviewed adapter and accepted V2 planner."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path

import pyproj
from pyproj.exceptions import ProjError

from shade_watch.engine import v1, v2
from shade_watch.engine.spatial import intersects
from shade_watch import region as adapter
from .common import (CODE_ROOT, ENGINE_FILES, FORMAT, digest, identity, read_json,
                     verify_seal)
from .config import (ROOT_MARKER, InvalidInput, check_document, city_clock, expanded_time,
                     machine_config, normalize_instants, region_config, validate_output_root)
from .sources import SourceProvider, provider
def _project(region, profile):
    corners = region['lower_left'], region['upper_right']
    if region['crs'] != 'wgs84':
        return corners, None
    (lat1, lon1), (lat2, lon2) = corners
    transformer = pyproj.Transformer.from_crs('EPSG:4326', profile['crs'], always_xy=True)
    x, y = transformer.transform([lon1, lon2], [lat1, lat2], errcheck=True)
    if not all(math.isfinite(v) for v in (*x, *y)):
        raise ProjError('Projection produced non-finite coordinates')
    try:
        operation = transformer.get_last_used_operation()
    except ProjError:
        operation = transformer
    return ([x[0], y[0]], [x[1], y[1]]), dict(
        operation=operation.description, accuracy_m=operation.accuracy,
        pyproj_version=pyproj.__version__, proj_version=pyproj.proj_version_str)


def _contains(extent, corners):
    l, b, r, t = extent
    return all(l <= x <= r and b <= y <= t for x, y in corners)


@dataclass
class RegionRequest:
    region: dict
    machine: dict
    profile: dict
    city: dict
    projected: dict
    projection: dict | None
    snapped_bounds: list

    def adapter_options(self):
        return dict(crs='projected', dsm_crs=self.city['crs'], local_timezone=self.city['timezone'],
                    daylight_reference=tuple(self.city['daylight_reference']),
                    dsm_source_line=self.profile['dsm_source_line'])


def resolve_request(region, machine):
    from shade_watch.city.profiles import HK, city_ids, city_record, fill_profile, load_city, machine_for_city

    region = region_config(region, project_legacy=False)
    legacy = region['schema'] == 'shade-map-region-1.0'
    city_id = HK if legacy else region.get('city')
    crs = region['crs']
    if crs == 'hk1980':
        if city_id not in (None, HK):
            raise InvalidInput('crs: hk1980 requires city hong_kong')
        city_id = HK
    if crs == 'projected' and city_id is None:
        raise InvalidInput('city: projected corners require an explicit city')
    if city_id is None:
        ids = city_ids()
        matches = []
        for candidate in ids:
            profile = load_city(candidate)
            try:
                points, projection = _project(region, profile)
            except ProjError:
                continue
            if _contains(profile['extent'], points):
                matches.append((profile, points, projection))
        if len(matches) != 1:
            candidates = [match[0]['city_id'] for match in matches] or ids
            raise InvalidInput(f'city: WGS84 corners match {len(matches)} cities; candidates: {", ".join(candidates)}')
        profile, points, projection = matches[0]
        city_id = profile['city_id']
    else:
        profile = load_city(city_id)
        try:
            points, projection = _project(region, profile)
        except ProjError as exc:
            raise InvalidInput(f'corners: projection to {profile["crs"]} failed') from exc
    first, second = points
    if not first[0] < second[0] or not first[1] < second[1]:
        raise InvalidInput(f'corners: projected {profile["crs"]} easting and northing must keep lower-left order')
    if not legacy and not _contains(profile['extent'], points):
        raise InvalidInput(f'corners: rectangle is outside {city_id} extent')
    if not legacy and region['time']['mode'] == 'instants':
        region['time']['instants'] = normalize_instants(region['time']['instants'], city_clock(profile))
    machine = machine_config(machine, require_dsm=city_id == HK)
    machine, ingest_id = machine_for_city(machine, profile, region['dsm_source'])
    if region['dsm_source'] == 'sea-2.2':
        fill_profile(profile, machine)
    projected = dict(region, crs='projected', lower_left=first, upper_right=second)
    snapped = list(v1._custom_grid([dict(crs=profile['crs'])], (*first, *second)).bounds())
    return RegionRequest(region, machine, profile, city_record(profile, ingest_id), projected, projection, snapped)




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


def _lattice(records):
    origin = [round(v / .5) for v in records[0]['bounds'][:2]]
    steps = [math.gcd(*[r['width' if axis == 0 else 'height'] for r in records],
                      *[round(r['bounds'][axis]/.5)-origin[axis] for r in records])
             for axis in (0, 1)]
    return origin, steps


def _cell_rectangle(bounds, lattice):
    origin, steps = lattice
    l, b, r, t = [round(v/.5) for v in bounds]
    return ((l-origin[0])//steps[0], (b-origin[1])//steps[1],
            (r-1-origin[0])//steps[0]+1, (t-1-origin[1])//steps[1]+1)


def _native_cells(bounds, lattice):
    origin, steps = lattice
    left, bottom, right, top = _cell_rectangle(bounds, lattice)
    for iy in range(bottom, top):
        for ix in range(left, right):
            x, y = origin[0]+ix*steps[0], origin[1]+iy*steps[1]
            yield x*.5, y*.5, (x+steps[0])*.5, (y+steps[1])*.5


def _cells(records, bounds, lattice):
    cells = []
    for native in _native_cells(bounds, lattice):
        clipped = [max(bounds[0], native[0]), max(bounds[1], native[1]),
                   min(bounds[2], native[2]), min(bounds[3], native[3])]
        sources = [Path(q['path']).name for q in records if intersects(native, q['bounds'])]
        if len(sources) > 1:
            raise InvalidInput('dsm_dir: more than one DSM source owns a native cell')
        label = f'e{native[0]:.1f}n{native[1]:.1f}'.replace('.0', '')
        cells.append(dict(id=label, native_bounds=list(native), bounds=clipped,
                          width=round((clipped[2]-clipped[0])/.5), height=round((clipped[3]-clipped[1])/.5),
                          source_tile=sources[0] if sources else None))
    return cells


def _fill_context(records, bounds, lattice, raw_directory):
    halos = []
    for record in records:
        l, b, r, t = record['bounds']
        if intersects(bounds, record['bounds']):
            m = adapter.BUFFER_M
            halos.append((l-m, b-m, r+m, t+m))
    rectangles = [_cell_rectangle(halo, lattice) for halo in halos]
    edges = sorted({y for _, bottom, _, top in rectangles for y in (bottom, top)})
    dependencies = 0
    # Count the union in horizontal bands without materializing missing cells.
    for low, high in zip(edges, edges[1:]):
        spans = sorted((l, r) for l, b, r, t in rectangles if b <= low < t)
        right = None
        for start, end in spans:
            begin = start if right is None else max(right, start)
            dependencies += max(0, end-begin) * (high-low)
            right = end if right is None else max(right, end)
    supplied = {cell for record in adapter.header_catalogue(raw_directory)
                for cell in _native_cells(record['bounds'], lattice)
                if any(intersects(cell, halo) for halo in halos)}
    return dict(no_dsm_cells_within_1km=dependencies - len(supplied))


def _adapter_plans(request, source, catalogue, temporal, provisional):
    region, machine = request.region, request.machine
    options = dict(request.adapter_options(), dsm_dir=catalogue, auto_source_view=True,
                   cache_dir=v1.ROOT/'data/cache/horizon'/source.cache_namespace(machine),
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
        plans.append(adapter.plan_region(request.projected['lower_left'], request.projected['upper_right'],
                                         output_dir=out, **group, **options))
    result = deepcopy(plans[0])
    sc = result['sidecar']
    sc.update(original_corners=[region['lower_left'], region['upper_right']], crs=region['crs'],
              coordinate_order='latitude,longitude' if region['crs']=='wgs84' else 'easting,northing',
              transformation_applied=request.projection is not None)
    if request.projection is not None:
        sc['transformer_description'] = request.projection['operation']
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
    return prepare_request(resolve_request(region, machine))


def prepare_request(request):
    region, machine = request.region, request.machine
    source = provider(region['dsm_source'])
    catalogue = source.catalogue(machine)
    validate_output_root(machine, (catalogue,))
    conflict = None
    try:
        existing = ownership(machine, region)
    except InvalidInput as exc:
        existing, conflict = None, str(exc)
    clock = city_clock(request.profile)
    temporal, dropped = expanded_time(region['time'], clock=clock,
                                      daylight_reference=request.city['daylight_reference'])
    provisional = v1.ROOT/'work/runs'/(region['name']+'-plan')
    try:
        adapted = _adapter_plans(request, source, catalogue, temporal, provisional)
        records = v1.index_sources(adapted['sidecar']['source_directory'], request.city['crs'])
    except ValueError as exc:
        raise InvalidInput(str(exc)) from exc
    sc = adapted['sidecar']
    frames = []
    for group in sc['time_groups']:
        for utc in group['utc_times']:
            local = datetime.fromisoformat(utc).astimezone(clock)
            frames.append(dict(local_time=local.isoformat(), utc_time=utc,
                               date=f'{local.year:04d}{local.month:02d}{local.day:02d}',
                               time=f'{local.hour:02d}{local.minute:02d}'))
    if len({f['date']+'/'+f['time'] for f in frames}) != len(frames):
        raise InvalidInput('time: duplicate local frame folder')
    hashes = {p: digest(CODE_ROOT/p) for p in ENGINE_FILES}
    identity_document = dict(region_config=region, frames=frames,
                             source_identity=source.source_identity(records), engine_hashes=hashes,
                             policies=source.policies(), publication_format=FORMAT,
                             city=request.city, resolved_bounds=request.snapped_bounds)
    run_id = identity(identity_document)
    work = v1.ROOT/'work/runs'/(region['name']+'-'+run_id[:12])
    for part in sc['requests']:
        part['output_directory'] = str(work/Path(part['output_directory']).relative_to(provisional))
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
        for part in sc['requests']:
            if part['batch'] == index:
                part['id'] = name+'#'+part['engine_request_id']
                request_ids.append(part['id'])
        sc['generated_request_ids'].extend(request_ids)
        sc['batches'].append(dict(id=batch.id, request_file=name, request_ids=request_ids,
                                  estimate=batch.estimate, resources=batch.definition['resources']))
    bounds, grid = sc['resolved_bounds'], json.loads(json.dumps(sc['resolved_grid']))
    lattice = _lattice(records)
    cells = _cells(records, bounds, lattice)
    fill_context = _fill_context(records, bounds, lattice, machine['dsm_dir'])
    pixels = grid['width']*grid['height']
    full = region['full_image'] == 'auto' and pixels <= v1.MAX_OUTPUT_PIXELS
    n = len(frames)
    file_count = n*(3*len(cells)+4+3*int(full))+4
    published = n*pixels*3*(1+int(full)) + file_count*16384 + 1024*len(cells)*n
    working = sum(p.definition['resources']['estimated_peak_new_bytes'] for p in batch_plans)
    horizons = [t['payload'] for p in batch_plans for t in p.definition['tasks'] if t['kind'] == 'horizon']
    directions = {float(d) for t in horizons for d in t['directions']}
    warnings = []
    if any(c['source_tile'] is None for c in cells):
        warnings.append('No-DSM cells remain shade 255, quality 1, surface 255')
    if fill_context['no_dsm_cells_within_1km']:
        warnings.append('no_dsm_cells_within_1km')
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
                    city=request.city, fill_context=fill_context,
                    missing_direction_jobs=sum(len(t['missing_directions']) for t in horizons),
                    estimates=estimate, full_images=full, warnings=warnings, existing_run=status)
    if request.projection is not None:
        document['projection'] = request.projection
    check_document(document, 'plan')
    return Prepared(region, machine, source, records, adapted, batch_plans,
                    identity_document, document, work, output_location(machine, region))
