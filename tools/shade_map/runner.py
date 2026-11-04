"""Durable engine orchestration, manifest transactions, and explicit prune."""
from __future__ import annotations

import importlib.metadata
from contextlib import nullcontext
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import time

from src import v1, v2
from tools import region_request as adapter
from .common import (CODE_ROOT, CONTRACT, ENGINE_FILES, FORMAT, atomic_json, digest, identity, name_lock,
                     read_json, seal, verify_files, verify_seal)
from .config import InvalidInput, check_document, machine_config, region_config, validate_output_root
from .planning import ROOT_MARKER, ownership, prepare
from .publication import publish_frame, verify_frame, write_summaries
from .sources import provider


def progress(message):
    print(message, file=sys.stderr, flush=True)


def _machine_record(machine):
    libraries = {}
    for name in ('numpy','rasterio','pyproj','psutil','numba'):
        libraries[name] = importlib.metadata.version(name)
    return dict(platform=platform.platform(),python=sys.version, libraries=libraries, **machine)


def _tool_record():
    return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=CODE_ROOT,text=True).strip(),
                dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=CODE_ROOT,text=True).strip()))


def _save(folder, manifest):
    seal(manifest)
    check_document(manifest, 'run')
    atomic_json(folder/'run_manifest.json', manifest)


def verify_run(folder, manifest=None):
    folder = Path(folder)
    manifest = manifest or read_json(folder/'run_manifest.json')
    check_document(manifest, 'run')
    verify_seal(manifest)
    if manifest['status'] != 'complete' or any(f['status'] != 'published' for f in manifest['frames']):
        raise InvalidInput('prune: every frame must be published and verified')
    if list(folder.rglob('*.partial')):
        raise RuntimeError('Partial publication remains; run must resume before completion')
    verify_files(folder, manifest['files'])
    for frame in manifest['frames']:
        verify_frame(folder/frame['date']/frame['time'], frame)
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'run_manifest.json'}:
        raise RuntimeError('Unexpected or missing published files')
    return manifest


def _recover_partials(folder, manifest):
    """Discard interrupted publication, retaining only independently verified finals."""
    redo = False
    frames = {(f['date'], f['time']): f for f in manifest['frames']}
    for partial in sorted(folder.glob('*/*.partial')):
        if partial.parent.is_symlink() or partial.is_symlink() or not partial.is_dir():
            raise RuntimeError('Partial publication must be a directory, not a symlink')
        frame = frames.get((partial.parent.name, partial.name.removesuffix('.partial')))
        if frame is not None:
            final = partial.with_name(frame['time'])
            if final.is_symlink():
                raise RuntimeError('Published frame cannot be a symlink')
            try:
                verify_frame(final, frame)
            except (OSError, ValueError, KeyError, RuntimeError):
                prefix = frame['date']+'/'+frame['time']+'/'
                manifest['files'] = {k:v for k,v in manifest['files'].items() if not k.startswith(prefix)}
                frame.update(status='pending', files={})
                manifest['status'] = 'incomplete'
                redo = True
                # Persist the redo obligation before removing its recovery cue.
                _save(folder, manifest)
                if final.exists():
                    shutil.rmtree(final)
        shutil.rmtree(partial)
    if redo:
        _save(folder, manifest)
    return redo


def _guard(prepared):
    estimates = prepared.document['estimates']
    required = estimates['published_bytes']['value'] + estimates['working_bytes']['value']
    maximum = prepared.machine['max_output_bytes']
    if maximum is not None and required > maximum:
        raise InvalidInput(f'max_output_bytes: estimated published plus working bytes {required} exceed {maximum}')
    # Account for publication and engine/cache volumes separately, as well as a shared volume.
    targets = [(prepared.folder, estimates['published_bytes']['value']),
               (v1.ROOT, estimates['working_bytes']['value'])]
    devices = {}
    for path, amount in targets:
        while not path.exists():
            path = path.parent
        device = path.stat().st_dev
        devices.setdefault(device, [path,0])[1] += amount
    for path, amount in devices.values():
        if amount > shutil.disk_usage(path).free:
            raise InvalidInput('output_root: insufficient free space for estimated published plus working bytes')


def _new_manifest(prepared, sidecar_hash):
    plan = prepared.document
    return dict(schema='shade-map-run-1.0',contract=CONTRACT,run_id=plan['run_id'],name=plan['name'],
                region_config=prepared.region,region_config_sha256=identity(prepared.region),
                identity_document=prepared.identity_document,tool=_tool_record(),
                engine_hashes=prepared.identity_document['engine_hashes'],policies=prepared.source.policies(),
                source_identity=prepared.identity_document['source_identity'],adapter_sidecar_sha256=sidecar_hash,
                batch_ids=[b.id for b in prepared.batch_plans],resolved_bounds=plan['resolved_bounds'],grid=plan['grid'],
                cells=plan['cells'],frames=[dict(f,status='pending',files={}) for f in plan['frames']],
                dropped_times=plan['dropped_times'],files={},machine=_machine_record(prepared.machine),
                timings=dict(invocations=[],engine_seconds=0.,publication_seconds=0.),
                prune=dict(pruned=False),status='incomplete',engine_events=[],publication_events=[])


def _owner(prepared):
    return dict(schema='shade-map-work-1.0',name=prepared.region['name'],run_id=prepared.document['run_id'])


def _engine(prepared, manifest):
    work = prepared.work
    state = work/'state'
    path = work/'batch_plans.json'
    if path.exists():
        plans = [v2.BatchPlan(**p) for p in read_json(path)]
        if [p.id for p in plans] != manifest['batch_ids']:
            raise RuntimeError('Saved batch definitions differ from manifest')
    else:
        raise RuntimeError('Missing durable batch definitions')
    for batch in plans:
        previous = None
        if (state/'state.sqlite').exists():
            # Query without submitting: a completed batch must never be resubmitted.
            import sqlite3
            with sqlite3.connect('file:'+str(state/'state.sqlite')+'?mode=ro',uri=True) as db:
                previous = db.execute('SELECT state FROM batches WHERE id=?',(batch.id,)).fetchone()
        action = 'verify'
        started=time.perf_counter()
        if previous is None:
            action='submit_run'
            v2.submit_batch(batch,state_dir=state)
            progress('Computing V2 batch '+batch.id[:12])
            result=v2.run_batch(batch.id,state_dir=state)
        else:
            result=v2.status_batch(batch.id,state_dir=state)
            if result['state'] != 'SUCCEEDED':
                action='resume'
                progress('Resuming V2 batch '+batch.id[:12])
                result=v2.resume_batch(batch.id,state_dir=state)
        seconds=time.perf_counter()-started
        manifest['timings']['engine_seconds'] += seconds
        manifest['engine_events'].append(dict(batch_id=batch.id,action=action,state=result['state'],
                                               attempts=len(result['attempts']),tasks=result['tasks'],
                                               metrics=result['metrics']))
        _save(prepared.folder,manifest)
        if result['state'] != 'SUCCEEDED':
            raise RuntimeError(f"V2 batch {batch.id} is {result['state']}: {result['failures']}")
    return [state/(p.id+'.logical_mosaic.json') for p in plans]


def run_region(region, machine='config/machine.local.json'):
    started=time.perf_counter()
    region,machine=region_config(region),machine_config(machine)
    validate_output_root(machine, (provider(region['dsm_source']).catalogue(machine),))
    ownership(machine,region)
    work_root=v1.ROOT/'outputs/shade_map_work'
    if (work_root/'.locks'/(region['name']+'.lock')).exists():
        # Refuse a concurrent controller before catalogue reads or source views.
        with name_lock(work_root,region['name'],create=False):
            return _run_region(region,machine,started,lock_held=True)
    return _run_region(region,machine,started,lock_held=False)


def _run_region(region,machine,started,*,lock_held):
    # Reject known config/foreign-folder conflicts before even creating a source view.
    prior=ownership(machine,region)
    if prior:
        source=provider(region['dsm_source'])
        if (prior['source_identity'] != source.preview_identity(region,machine)
                or prior['policies'] != source.policies()
                or prior['engine_hashes'] != {p:digest(CODE_ROOT/p) for p in ENGINE_FILES}
                or prior['identity_document']['publication_format'] != FORMAT):
            raise InvalidInput('name: existing run has a different source, engine or publication identity')
        if prior['status']=='complete':
            with (nullcontext() if lock_held else name_lock(v1.ROOT/'outputs/shade_map_work',region['name'],create=False)):
                folder = Path(machine['output_root'])/region['name']
                if not _recover_partials(folder, prior):
                    verify_run(folder,prior)
                    progress('Complete run verified')
                    return dict(schema='shade-map-result-1.0',run_id=prior['run_id'],name=region['name'],
                                status='complete',published_frames=len(prior['frames']),reused_frames=len(prior['frames']),
                                computed_batches=0,verified_only=True)
    prepared=prepare(region,machine)
    if prepared.document['existing_run']['status']=='conflict':
        raise InvalidInput(prepared.document['existing_run']['reason'])
    work_root=v1.ROOT/'outputs/shade_map_work'
    complete=prepared.document['existing_run']['status']=='complete'
    if not complete:
        _guard(prepared)
    with (nullcontext() if lock_held else name_lock(work_root,region['name'],create=not complete)):
        existing=ownership(machine,region)
        if existing and existing['run_id'] != prepared.document['run_id']:
            raise InvalidInput('name: existing run has a different run_id')
        if existing and existing['status']=='complete' and not _recover_partials(prepared.folder, existing):
            verify_run(prepared.folder,existing)
            progress('Complete run verified')
            return dict(schema='shade-map-result-1.0',run_id=existing['run_id'],name=region['name'],
                        status='complete',published_frames=len(existing['frames']),reused_frames=len(existing['frames']),
                        computed_batches=0,verified_only=True)
        root=Path(machine['output_root'])
        if not root.exists():
            root.mkdir(parents=True)
            atomic_json(root/ROOT_MARKER,dict(schema='shade-map-root-1.0'))
        if prepared.work.exists():
            if read_json(prepared.work/'owner.json') != _owner(prepared):
                raise InvalidInput('name: work folder ownership differs')
        else:
            prepared.work.mkdir(parents=True)
            atomic_json(prepared.work/'owner.json',_owner(prepared))
        # The lock file itself is in the common name-lock directory; this record is inspectable.
        atomic_json(prepared.work/'lock.json',dict(schema='shade-map-lock-1.0',name=region['name'],
                                                   run_id=prepared.document['run_id'],mechanism='POSIX flock'))
        sidecar_dir=prepared.work/'adapter'
        if not sidecar_dir.exists():
            adapter.write_region(prepared.adapter_plan,sidecar_dir)
        if not (prepared.work/'batch_plans.json').exists():
            atomic_json(prepared.work/'batch_plans.json',[b.to_dict() for b in prepared.batch_plans])
        sidecar_path=sidecar_dir/'region_request.json'
        if existing:
            manifest=existing
            if digest(sidecar_path) != manifest['adapter_sidecar_sha256']:
                raise RuntimeError('Adapter sidecar hash differs')
        else:
            prepared.folder.mkdir()
            atomic_json(prepared.folder/'region_config.json',prepared.region)
            manifest=_new_manifest(prepared,digest(sidecar_path))
            manifest['files']['region_config.json']=digest(prepared.folder/'region_config.json')
            _save(prepared.folder,manifest)
        _recover_partials(prepared.folder, manifest)
        sidecar=read_json(sidecar_path)
        mosaics=_engine(prepared,manifest)
        records=[]
        reused=0
        publication_start=time.perf_counter()
        for frame in manifest['frames']:
            expected={k:frame[k] for k in ('local_time','utc_time','date','time')}
            if frame['status']=='published':
                record=verify_frame(prepared.folder/frame['date']/frame['time'],expected)
                reused+=1
                # Also discard a stale partial alongside a completed frame.
                partial=prepared.folder/frame['date']/(frame['time']+'.partial')
                if partial.exists():
                    if partial.is_symlink(): raise RuntimeError('Partial publication cannot be a symlink')
                    shutil.rmtree(partial)
            else:
                progress('Publishing '+frame['date']+'/'+frame['time'])
                record,written=publish_frame(prepared,expected,sidecar,mosaics)
                reused+=int(not written)
                frame['status']='published'
                prefix=frame['date']+'/'+frame['time']+'/'
                frame['files']={prefix+k:v for k,v in record['files'].items()}
                frame['files'][prefix+'frame.json']=digest(prepared.folder/prefix/'frame.json')
                manifest['files'].update(frame['files'])
                manifest['publication_events'].append(dict(date=frame['date'],time=frame['time'],
                                                            action='published' if written else 'recovered'))
                _save(prepared.folder,manifest)
            records.append(record)
        write_summaries(prepared.folder,records)
        manifest['files'].update({name:digest(prepared.folder/name) for name in ('summary.json','summary.csv')})
        manifest['timings']['publication_seconds']+=time.perf_counter()-publication_start
        manifest['timings']['invocations'].append(dict(wall_seconds=time.perf_counter()-started,reused_frames=reused))
        manifest['status']='complete'
        _save(prepared.folder,manifest)
        verify_run(prepared.folder,manifest)
        return dict(schema='shade-map-result-1.0',run_id=manifest['run_id'],name=region['name'],status='complete',
                    published_frames=len(records),reused_frames=reused,
                    computed_batches=sum(e['action']!='verify' for e in manifest['engine_events']),verified_only=False)


def _size(path):
    return sum(p.lstat().st_size for p in path.rglob('*') if p.is_file() or p.is_symlink())


def prune_region(region, machine='config/machine.local.json', *, yes=False):
    region,machine=region_config(region),machine_config(machine)
    validate_output_root(machine, (provider(region['dsm_source']).catalogue(machine),))
    manifest=ownership(machine,region)
    if manifest is None:
        raise InvalidInput('prune: no run with this name')
    folder=Path(machine['output_root'])/region['name']
    verify_run(folder,manifest)
    work_root=v1.ROOT/'outputs/shade_map_work'
    work=work_root/(region['name']+'-'+manifest['run_id'][:12])
    with name_lock(work_root,region['name'],create=False):
        # Re-read inside the lock before deletion.
        manifest=verify_run(folder)
        owner=dict(schema='shade-map-work-1.0',name=region['name'],run_id=manifest['run_id'])
        if work.exists() and (work.is_symlink() or read_json(work/'owner.json') != owner):
            raise InvalidInput('prune: work folder ownership differs')
        listing=[dict(path=p.relative_to(work).as_posix(),bytes=p.lstat().st_size)
                 for p in sorted(work.rglob('*')) if p.is_file() or p.is_symlink()] if work.exists() else []
        result=dict(schema='shade-map-prune-1.0',run_id=manifest['run_id'],name=region['name'],
                    work_folder='outputs/shade_map_work/'+work.name,files=listing,
                    bytes=sum(p['bytes'] for p in listing),deleted=False)
        if yes and work.exists():
            shutil.rmtree(work)
            result['deleted']=True
            manifest['prune']=dict(pruned=True,deleted_bytes=result['bytes'],work_folder=result['work_folder'])
            _save(folder,manifest)
        return result
