"""Compare a verified sea publication with the same frames on raw DSM."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import csv
import fcntl
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
import rasterio

from src import v1, v2
from tools import region_request as adapter
from tools.shade_map.common import CODE_ROOT, ENGINE_FILES, atomic_json, digest, identity, read_json
from tools.shade_map.config import ROOT_MARKER, InvalidInput, validate_schema
from tools.shade_map.planning import resolve_request
from tools.shade_map.publication import raster_profile
from tools.shade_map.runner import verify_run
from tools.shade_map.sources import RawSource
from . import SOURCE_NAME
from .build import write_raster
from .provider import SeaSource
from .view import read_manifest

GROUPS = dict(land=(0, 3), water=(1, 2), other=(4,))
DEPENDENCY_CODES = (0, 1, 2, 3, 4)
SCHEMA = 'fill-impact-1.0'


def dependency_codes(surface, filled, raw):
    if not (surface.shape == filled.shape == raw.shape):
        raise RuntimeError('Fill-impact raster shapes differ')
    observed = surface == 0
    computed = surface <= 4
    valid = computed & (filled != 255)
    result = np.full(surface.shape, 255, np.uint8)
    result[computed & ~valid] = 4
    result[valid & ~observed] = 3
    result[valid & observed & (raw == filled)] = 0
    result[valid & observed & (raw == 255)] = 1
    result[valid & observed & (raw != 255) & (raw != filled)] = 2
    return result


def frame_metrics(surface, filled, filled_quality, raw, raw_quality):
    dependency = dependency_codes(surface, filled, raw)
    for shade, quality in ((filled, filled_quality), (raw, raw_quality)):
        if shade.shape != quality.shape or not np.array_equal(shade == 255, quality != 0):
            raise RuntimeError('Fill-impact shade and quality do not partition valid labels')
    group_counts = {name: np.bincount(dependency[np.isin(surface, classes)], minlength=5)
                    for name, classes in GROUPS.items()}
    observed = surface == 0
    # Shade/quality states are compact pairs. Keep every observed transition,
    # including cases where the filled result remains uncertain.
    a, aq, b, bq = (array[observed].astype(np.uint32)
                    for array in (raw, raw_quality, filled, filled_quality))
    values, counts = np.unique((a << 24) | (aq << 16) | (b << 8) | bq, return_counts=True)
    transitions = Counter({(int(v >> 24), int(v >> 16 & 255), int(v >> 8 & 255), int(v & 255)): int(n)
                           for v, n in zip(values, counts)})
    return dependency, group_counts, transitions


def select_frames(frames, times):
    if times is None:
        return frames
    requested = times.split(',')
    if any(not re.fullmatch(r'(?:[01][0-9]|2[0-3])[0-5][0-9]', t) for t in requested):
        raise InvalidInput('fill-impact: --times must be a comma-separated list of HHMM values')
    if len(set(requested)) != len(requested):
        raise InvalidInput('fill-impact: --times contains a duplicate value')
    missing = set(requested) - {frame['time'] for frame in frames}
    if missing:
        raise InvalidInput('fill-impact: times absent from the completed F run: '+', '.join(sorted(missing)))
    return [frame for frame in frames if frame['time'] in requested]


def require_run(machine, region, times=None):
    return _require_run(resolve_request(region, machine), times)


def _require_run(request, times):
    machine, region = request.machine, request.region
    if region['dsm_source'] != SOURCE_NAME:
        raise InvalidInput(f'fill-impact requires a complete matching {SOURCE_NAME} F run')
    root = Path(machine['output_root'])
    folder = root/region['name']
    marker = root/ROOT_MARKER
    try:
        if folder.is_symlink() or marker.is_symlink() or read_json(marker) != {'schema':'shade-map-root-1.0'}:
            raise ValueError('output is not owned by F')
        manifest = read_json(folder/'run_manifest.json')
    except (OSError, ValueError) as exc:
        raise InvalidInput(f'fill-impact requires a complete matching {SOURCE_NAME} F run; run F first') from exc
    source = SeaSource()
    if (manifest.get('status') != 'complete' or manifest.get('region_config') != region
            or manifest.get('city') != request.city
            or manifest.get('policies') != source.policies()
            or manifest.get('engine_hashes') != {p:digest(CODE_ROOT/p) for p in ENGINE_FILES}):
        raise InvalidInput('fill-impact: F run is incomplete or does not match the region/current sea view')
    frames = select_frames(manifest['frames'], times)
    try:
        verify_run(folder, manifest)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        raise InvalidInput(f'fill-impact: F run failed publication verification: {exc}') from exc
    if manifest.get('source_identity') != source.preview_identity(request.projected, machine):
        raise InvalidInput('fill-impact: F run does not match the current sea view')
    view = source.catalogue(machine).parent
    return machine, region, folder, manifest, frames, read_manifest(view)


def owned_directory(path):
    if path.resolve() != path or (path.exists() and not path.is_dir()):
        raise InvalidInput(f'fill-impact: directory must be inside its namespace without symlinks: {path}')
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def diagnostic_lock(root, name):
    locks = owned_directory(root/'.locks')
    lock = locks/(name+'.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InvalidInput('fill-impact: another diagnostic owns the lock') from exc
        yield


def plan_raw(request, frames, view, work, token):
    if not frames:
        return dict(source_identity=dict(provider='raw', sources=[]), plans=[], sidecar=None)
    cache = v1.ROOT/'data/processed/shade_v1'/('sea2_2_fill_impact_'+token[:12])
    if cache.resolve() != cache:
        raise InvalidInput('fill-impact: cache namespace cannot use symlinks')
    machine, region = request.machine, request.projected
    adapted = adapter.plan_region(
        region['lower_left'], region['upper_right'], **request.adapter_options(),
        instants=[f['local_time'] for f in frames], dsm_dir=machine['dsm_dir'],
        auto_source_view=True, output_dir=work/'engine', cache_dir=cache,
        memory_budget_mb=min(machine['memory_budget_mb'], 8192))
    sidecar = adapted['sidecar']
    if [t for group in sidecar['time_groups'] for t in group['utc_times']] != [f['utc_time'] for f in frames]:
        raise RuntimeError('Raw counterfactual frames differ from the selected F frames')
    sources = RawSource().source_identity(v1.index_sources(sidecar['source_directory'], request.city['crs']))
    expected = view['catalogue']['files']
    if any(expected.get(s['name']) != s['sha256'] or
           any(expected.get(a['name']) != a['sha256'] for a in s['auxiliary'])
           for s in sources['sources']):
        raise InvalidInput('fill-impact: raw dependencies differ from the built catalogue')
    plans = []
    for index, payload in enumerate(adapted['batches']):
        payload.update(workers=machine['workers'], memory_budget_mb=machine['memory_budget_mb'],
                       logical_mosaic=True, statistics=False)
        plan = v2.plan_batch(**payload)
        sidecar['batches'][index].update(id=plan.id, estimate=plan.estimate,
                                         resources=plan.definition['resources'])
        plans.append(plan.to_dict())
    return dict(source_identity=sources, plans=plans, sidecar=sidecar)


def run_raw(work, definition):
    state = work/'state'
    events, mosaics = [], []
    for saved in definition['plans']:
        plan = v2.BatchPlan(**saved)
        previous = None
        if (state/'state.sqlite').exists():
            with sqlite3.connect((state/'state.sqlite').as_uri()+'?mode=ro', uri=True) as db:
                previous = db.execute('SELECT state FROM batches WHERE id=?', (plan.id,)).fetchone()
        if previous is None:
            v2.submit_batch(plan, state_dir=state)
            result = v2.run_batch(plan.id, state_dir=state)
            action = 'submit_run'
        else:
            result = v2.status_batch(plan.id, state_dir=state)
            action = 'verify'
            if result['state'] != 'SUCCEEDED':
                result = v2.resume_batch(plan.id, state_dir=state)
                action = 'resume'
        events.append(dict(id=plan.id, action=action, state=result['state']))
        atomic_json(work/'execution.json', events)
        if result['state'] != 'SUCCEEDED':
            raise RuntimeError('Raw counterfactual V2 batch failed: '+str(result.get('failures')))
        mosaics.append(state/(plan.id+'.logical_mosaic.json'))
    return mosaics, events


def write_dependency_vrt(path, bounds, cells, crs):
    profile = raster_profile(bounds, crs)
    affine = profile['transform']
    root = ET.Element('VRTDataset', rasterXSize=str(profile['width']), rasterYSize=str(profile['height']))
    ET.SubElement(root, 'SRS').text = rasterio.crs.CRS.from_string(crs).to_wkt()
    ET.SubElement(root, 'GeoTransform').text = ','.join(map(str, affine.to_gdal()))
    band = ET.SubElement(root, 'VRTRasterBand', dataType='Byte', band='1')
    ET.SubElement(band, 'NoDataValue').text = '255'
    for cell in cells:
        source = ET.SubElement(band, 'SimpleSource')
        ET.SubElement(source, 'SourceFilename', relativeToVRT='1').text = f'dependency/{cell["id"]}.tif'
        ET.SubElement(source, 'SourceBand').text = '1'
        width, height = str(cell['width']), str(cell['height'])
        ET.SubElement(source, 'SrcRect', xOff='0', yOff='0', xSize=width, ySize=height)
        ET.SubElement(source, 'DstRect', xOff=str(round((cell['bounds'][0]-bounds[0])/.5)),
                      yOff=str(round((bounds[3]-cell['bounds'][3])/.5)), xSize=width, ySize=height)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def atomic_write(path, writer):
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', suffix=path.suffix, dir=path.parent)
    os.close(fd)
    try:
        writer(Path(temporary))
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def frame_report(folder, destination, run, frame, raw_sidecar, mosaics):
    prefix = folder/frame['date']/frame['time']
    target = owned_directory(destination/frame['date']/frame['time']/'dependency')
    totals = {name: np.zeros(5, np.int64) for name in GROUPS}
    transitions = Counter()
    crs = run['grid']['crs']
    for cell in run['cells']:
        rasters = []
        for layer in ('surface', 'shade', 'quality'):
            with rasterio.open(prefix/layer/(cell['id']+'.tif')) as ds:
                rasters.append(ds.read(1))
        raw, quality, transform = adapter.read_region_window(
            raw_sidecar, utc_time=frame['utc_time'], bounds=cell['bounds'], logical_mosaics=mosaics)
        dependency, groups, changes = frame_metrics(*rasters, raw, quality)
        path = target/(cell['id']+'.tif')
        atomic_write(path, lambda temporary: write_raster(temporary, dependency, transform, crs, 255))
        for name, counts in groups.items():
            totals[name] += counts
        transitions.update(changes)
    atomic_write(target.parent/'dependency.vrt',
                 lambda path: write_dependency_vrt(path, run['resolved_bounds'], run['cells'], crs))
    groups = {}
    for name, counts in totals.items():
        size = int(counts.sum())
        values = {str(code): int(counts[code]) for code in DEPENDENCY_CODES}
        groups[name] = dict(pixels=size, counts=values)
        if name != 'other':
            groups[name]['fractions'] = {code: n/size if size else 0.0 for code, n in values.items()}
    land = groups['land']['pixels']
    return dict(date=frame['date'], time=frame['time'], utc_time=frame['utc_time'], groups=groups,
                fill_dependent_land=int(totals['land'][1:4].sum())/land if land else 0.0,
                observed_transitions=[
                    dict(raw_shade=a, raw_quality=aq, filled_shade=b, filled_quality=bq, pixels=n)
                    for (a, aq, b, bq), n in sorted(transitions.items())])


def write_csv(path, frames):
    columns = ('date','time','utc_time','group','dependency_code','pixels','fraction','fill_dependent_land',
               'raw_shade','raw_quality','filled_shade','filled_quality')
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for frame in frames:
            context = {k:frame[k] for k in ('date','time','utc_time','fill_dependent_land')}
            for name, group in frame['groups'].items():
                for code, pixels in group['counts'].items():
                    writer.writerow(dict(**context, group=name, dependency_code=code, pixels=pixels,
                                         fraction=group.get('fractions', {}).get(code)))
            for row in frame['observed_transitions']:
                writer.writerow(dict(**context, group='observed', **row))


def publication_listing(folder):
    entries = {}
    for path in folder.rglob('*'):
        if path.is_file():
            info = path.stat()
            entries[path.relative_to(folder).as_posix()] = [info.st_size, info.st_mtime_ns]
    return entries


def fill_impact(machine, region, *, times=None):
    request = resolve_request(region, machine)
    machine, region, folder, run, frames, view = _require_run(request, times)
    name = region['name']
    before = publication_listing(folder)
    owner = dict(schema='sea2-fill-impact-work-1.0', name=name, policy_run_id=run['run_id'],
                 view_id=view['view_id'], raw_catalogue_sha256=view['catalogue']['identity'],
                 utc_times=[f['utc_time'] for f in frames])
    token = identity(owner)
    work_root = v1.ROOT/'outputs/sea2_2_diagnostic_work'
    with diagnostic_lock(work_root, name):
        destination = Path(machine['output_root'])/'_diagnostics/fill_impact'/name
        report_path = destination/'fill_impact.json'
        if destination.resolve() != destination or report_path.is_symlink():
            raise InvalidInput('fill-impact: report directory cannot use symlinks')
        if report_path.exists() and read_json(report_path).get('policy_run_id') != run['run_id']:
            raise InvalidInput('fill-impact: existing report belongs to another F run')
        work = owned_directory(work_root/(name+'-'+token[:12]))
        owner_path = work/'owner.json'
        if owner_path.exists() and read_json(owner_path) != owner:
            raise InvalidInput('fill-impact: work belongs to another counterfactual')
        if not owner_path.exists():
            if any(work.iterdir()):
                raise InvalidInput('fill-impact: existing work has no ownership record')
            atomic_json(owner_path, owner)
        planned = work/'counterfactual.json'
        if planned.exists():
            definition = read_json(planned)
        else:
            definition = plan_raw(request, frames, view, work, token)
            atomic_json(planned, definition)
        mosaics, events = run_raw(work, definition)
        owned_directory(destination)
        metrics = [frame_report(folder, destination, run, f, definition['sidecar'], mosaics) for f in frames]
        report = dict(schema=SCHEMA, diagnostic=True, name=name, policy_run_id=run['run_id'],
                      sea_view_id=view['view_id'], counterfactual_id=token,
                      raw_catalogue_sha256=owner['raw_catalogue_sha256'], frames=metrics)
        validate_schema(report, read_json(CODE_ROOT/'config/schema/fill_impact.schema.json'))
        atomic_write(destination/'fill_impact.csv', lambda path: write_csv(path, metrics))
        atomic_json(report_path, report)
        after = publication_listing(folder)
        if before != after:
            raise RuntimeError('F publication listing changed during fill-impact')
        atomic_json(work/'publication-integrity.json',
                    dict(files=len(before), before_sha256=identity(before), after_sha256=identity(after),
                         sealed_manifest_sha256=digest(folder/'run_manifest.json')))
        return dict(report=str(report_path), work=str(work), frames=len(metrics), events=events)
