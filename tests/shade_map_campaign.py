"""Explicit, bounded SW-F1.0 development campaign. Not collected by pytest.

Run from the repo root: PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py ACTION
Real jobs share a persisted 3600 s / 12 GiB / 20 GiB watchdog ledger.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

import numpy as np
import psutil
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer

from src import v1
from tools.shade_map.common import atomic_json, digest, identity, read_json, safe_relative, verify_files
from tools.shade_map.config import check_document
from tools.shade_map.planning import prepare
from tools.shade_map.runner import verify_run
from tools.shade_map.publication import NODATA
from tools.shade_map.sources import RawSource
from tools import region_request as adapter

ROOT=Path(__file__).resolve().parents[1]
DIAG=ROOT/'outputs/shade_map_f1_diagnostics_20261031'
EVIDENCE=ROOT/'docs/shade_map/evidence'
LEDGER=EVIDENCE/'resource_ledger.json'
PYTHON=str(ROOT/'.venv/bin/python')
NAMESPACE='f1_dev_20261031_'


def config(kind):
    return DIAG/(kind+'_machine.json'),DIAG/(kind+'_region.json')


def artifacts():
    roots=[ROOT/'outputs/shade_map_f1_20261031',DIAG,ROOT/'outputs/shade_map_work']
    roots+=list((ROOT/'data/processed/shade_v1').glob(NAMESPACE+'*'))
    before=read_json(EVIDENCE/'protected_before.json')
    views=ROOT/'outputs/region_views'
    roots += [p for p in views.iterdir() if p.is_dir() and
              not any(k.startswith(p.relative_to(ROOT).as_posix()+'/') for k in before)] if views.exists() else []
    return sum(p.lstat().st_size for root in roots if root.exists()
               for p in root.rglob('*') if p.is_file() or p.is_symlink())


def monitored(label,args,*,kill_at=None):
    ledger=read_json(LEDGER) if LEDGER.exists() else dict(schema='shade-map-resource-ledger-1.0',
        limits=dict(real_job_seconds=3600,peak_tree_rss_bytes=12*1024**3,new_artifact_bytes=20*1024**3),jobs=[])
    charged=sum(j['wall_seconds'] for j in ledger['jobs'])+ledger.get('preflight_overhead',{}).get('charged_seconds',0)
    remaining=3600-charged
    if remaining<=0: raise RuntimeError('Real-DSM wall budget exhausted')
    original=label
    sequence=1
    while (DIAG/(label+'.stdout.json')).exists():
        label=f'{original}_{sequence:02d}'
        sequence+=1
    stdout,stderr=DIAG/(label+'.stdout.json'),DIAG/(label+'.stderr.txt')
    started=time.perf_counter(); peak=0; disk=artifacts(); killed=False; reason=None; kill_evidence=None
    with stdout.open('w') as out,stderr.open('w') as err:
        process=subprocess.Popen(args,cwd=ROOT,stdout=out,stderr=err,start_new_session=True,
                                 env={**os.environ,'PYTHONPATH':str(ROOT)})
        owner=psutil.Process(process.pid)
        next_disk=0
        while process.poll() is None:
            elapsed=time.perf_counter()-started
            try:
                tree=[owner]+owner.children(recursive=True)
                peak=max(peak,sum(p.memory_info().rss for p in tree if p.is_running()))
            except (psutil.NoSuchProcess,psutil.AccessDenied): pass
            if elapsed>=next_disk:
                disk=max(disk,artifacts()); next_disk=elapsed+10
            if elapsed>remaining or peak>12*1024**3 or disk>20*1024**3:
                reason='budget exceeded'; os.killpg(process.pid,signal.SIGKILL); break
            if kill_at:
                phase,kind=kill_at
                machine,region=config(kind)
                region=read_json(region)
                work=list((ROOT/'outputs/shade_map_work').glob(region['name']+'-*'))
                if work:
                    work=work[0]
                    if phase=='compute' and (work/'state/state.sqlite').exists():
                        try:
                            with sqlite3.connect('file:'+str(work/'state/state.sqlite')+'?mode=ro',uri=True) as db:
                                succeeded=db.execute("SELECT COUNT(*) FROM tasks WHERE state='SUCCEEDED'").fetchone()[0]
                                running=db.execute("SELECT COUNT(*) FROM tasks WHERE state='RUNNING'").fetchone()[0]
                                attempts=db.execute("SELECT task,state FROM attempts").fetchall()
                            if succeeded and running:
                                kill_evidence=dict(succeeded=succeeded,running=running,attempts=attempts)
                                # A real second CLI must refuse the live name lock promptly.
                                concurrent_start=time.perf_counter()
                                refusal=subprocess.run([PYTHON,'-m','tools.shade_map','run','--machine',str(machine),str(config(kind)[1])],
                                    cwd=ROOT,capture_output=True,text=True,timeout=20)
                                assert refusal.returncode==2 and refusal.stderr.startswith('invalid input:')
                                assert 'another run owns the lock' in refusal.stderr and not refusal.stdout
                                kill_evidence['concurrent_refusal']=dict(returncode=refusal.returncode,stderr=refusal.stderr,
                                    seconds=time.perf_counter()-concurrent_start)
                        except sqlite3.Error: pass
                    elif phase=='publication':
                        folder=ROOT/'outputs/shade_map_f1_20261031'/region['name']
                        published=list(folder.glob('*/*/frame.json'))
                        partials=list(folder.glob('*/*.partial'))
                        if published and partials:
                            kill_evidence=dict(published=[p.relative_to(folder).as_posix() for p in published],
                                               partials=[p.relative_to(folder).as_posix() for p in partials])
                    if kill_evidence:
                        # Kill the F controller only. V2's resume owns/reclaims its recorded worker.
                        os.kill(process.pid,signal.SIGKILL); killed=True; break
            time.sleep(.02 if kill_at else .2)
        process.wait()
    seconds=time.perf_counter()-started
    if killed and kill_at[0]=='publication':
        kill_evidence['retained_files']={}
        for name in kill_evidence['published']:
            for p in (folder/Path(name).parent).rglob('*'):
                if p.is_file():
                    kill_evidence['retained_files'][p.relative_to(folder).as_posix()]=[digest(p),p.stat().st_mtime_ns]
    disk=max(disk,artifacts())
    record=dict(label=label,argv=args,wall_seconds=seconds,peak_tree_rss_bytes=peak,
                cumulative_artifact_bytes=disk,returncode=process.returncode,
                intentional_sigkill=killed,kill_evidence=kill_evidence,budget_failure=reason,
                stdout=str(stdout.relative_to(ROOT)),stderr=str(stderr.relative_to(ROOT)))
    ledger['jobs'].append(record)
    ledger['total_real_job_seconds']=sum(j['wall_seconds'] for j in ledger['jobs'])+ledger.get('preflight_overhead',{}).get('charged_seconds',0)
    ledger['peak_tree_rss_bytes']=max(j['peak_tree_rss_bytes'] for j in ledger['jobs'])
    ledger['peak_new_artifact_bytes']=max(j['cumulative_artifact_bytes'] for j in ledger['jobs'])
    ledger['within_budget']=ledger['total_real_job_seconds']<=3600 and ledger['peak_tree_rss_bytes']<=12*1024**3 and ledger['peak_new_artifact_bytes']<=20*1024**3
    atomic_json(LEDGER,ledger)
    print(json.dumps(record),flush=True)
    if reason: raise RuntimeError(reason)
    if kill_at and not killed: raise RuntimeError('Requested interruption phase was not observed')
    if not kill_at and process.returncode: raise RuntimeError(f'{label} failed; see {stderr}')
    return stdout


def cli(action,kind,**kwargs):
    mp,rp=config(kind)
    return monitored(kind+'_'+action,[PYTHON,'-m','tools.shade_map',action,'--machine',str(mp),str(rp)],**kwargs)


def setup():
    DIAG.mkdir(exist_ok=True)
    inverse=Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True)
    corners=[list(inverse.transform(x,y)[::-1]) for x,y in [(820240.13,808390.17),(820260.32,808410.39)]]
    a=dict(schema='shade-map-region-1.0',name='f1_cheung_chau',crs='hk1980',
           lower_left=[820250,807200],upper_right=[821750,808400],
           time=dict(mode='daylight',dates=['2026-01-07'],interval_minutes=10))
    b=dict(schema='shade-map-region-1.0',name='f1_sparse_window',crs='wgs84',
           lower_left=corners[0],upper_right=corners[1],
           time=dict(mode='window',dates=['2026-01-07'],start='12:30',end='12:50',interval_minutes=10))
    configs={'a':a,'b':b,'instant':dict(deepcopy(b),name='f1_sparse_instants',
        time=dict(mode='instants',instants=['2026-01-07T12:30','2026-01-07T00:00'])),
        'kill_compute':dict(deepcopy(b),name='f1_kill_compute'),
        'kill_publish':dict(deepcopy(b),name='f1_kill_publish')}
    for kind,region in configs.items():
        mp,rp=config(kind)
        if mp.exists() or rp.exists(): raise RuntimeError('Campaign config already frozen')
        machine=dict(schema='shade-map-machine-1.0',dsm_dir='data/raw/dsm/2020/D12.DSM.TIFF',
                     output_root='outputs/shade_map_f1_20261031',cache_namespace=NAMESPACE+kind,
                     workers=1,memory_budget_mb=8192,max_output_bytes=12*1024**3)
        if (ROOT/'data/processed/shade_v1'/machine['cache_namespace']).exists():
            raise RuntimeError('Cache namespace is not fresh')
        atomic_json(mp,machine); atomic_json(rp,region)
    atomic_json(EVIDENCE/'frozen_sparse_rectangle.json',dict(frozen_before_execution=True,
        projected_input_corners=[[820240.13,808390.17],[820260.32,808410.39]],
        wgs84_corners=corners,region=b,configs=configs,cache_namespaces={k:NAMESPACE+k for k in configs}))


def gate():
    path=cli('plan','a'); plan=read_json(path)
    prepared=prepare(read_json(config('a')[1]),read_json(config('a')[0]))
    actual=sorted(p.name for p in Path(prepared.adapter_plan['sidecar']['source_directory']).glob('*.tif'))
    expected=sorted(p.name for p in (ROOT/'outputs/v2_daylight_cheungchau_20261009/source_view').glob('*.tif'))
    record=dict(actual=actual,reference=expected,equal=actual==expected,frame_count=len(plan['frames']),
                first=plan['frames'][0],last=plan['frames'][-1],run_id=plan['run_id'],cache_was_absent=not (ROOT/'data/processed/shade_v1'/(NAMESPACE+'a')).exists())
    atomic_json(EVIDENCE/'cheung_chau_source_gate.json',record)
    if actual!=expected: raise RuntimeError('STOP: source lists differ; decision required')
    assert len(plan['frames'])==65 and plan['frames'][0]['time']=='0710' and plan['frames'][-1]['time']=='1750'


def reference():
    mp,rp=config('b'); p=prepare(read_json(rp),read_json(mp))
    plan=v1.plan_shade(mode='custom',bounds=p.document['resolved_bounds'],
        instants=[f['local_time'] for f in p.document['frames']],
        dsm_dir=p.adapter_plan['sidecar']['source_directory'],
        output_dir=ROOT/'outputs/shade_map_work'/('f1_sparse_reference-'+p.document['run_id'][:12])/'v1',
        cache_dir=ROOT/'data/processed/shade_v1'/(NAMESPACE+'reference'))
    result=v1.run_shade(plan)
    atomic_json(EVIDENCE/'independent_v1_reference.json',dict(index=str(Path(result.index_path).relative_to(ROOT)),jobs=result.jobs,
        bounds=p.document['resolved_bounds'],frames=[f['utc_time'] for f in result.frames]))


def verify(kind):
    mp,rp=config(kind); p=prepare(read_json(rp),read_json(mp)); folder=p.folder
    manifest=verify_run(folder)
    assert identity(manifest['identity_document'])==manifest['run_id']
    assert identity(manifest['region_config'])==manifest['region_config_sha256']
    sidecar=read_json(p.work/'adapter/region_request.json')
    mosaics=[p.work/'state'/(b+'.logical_mosaic.json') for b in manifest['batch_ids']]
    reference_index=None
    if kind=='a': reference_index=read_json(ROOT/'outputs/v2_daylight_cheungchau_20261009/combined/result_index.json')
    elif kind in ('b','instant'):
        reference_index=read_json(ROOT/read_json(EVIDENCE/'independent_v1_reference.json')['index'])
    ref_frames={f['utc_time']:f for f in reference_index['frames']} if reference_index else {}
    checked=[]; csv_expected=[]
    summary=read_json(folder/'summary.json'); check_document(summary,'summary')
    source=RawSource()
    for record in manifest['frames']:
        frame_dir=folder/record['date']/record['time']
        frame=read_json(frame_dir/'frame.json'); check_document(frame,'frame')
        for layer in ('shade','quality','surface'):
            for suffix in ('.vrt','.tif'):
                if suffix=='.tif' and not p.document['full_images']: continue
                with rasterio.open(frame_dir/(layer+suffix)) as ds:
                    assert list(ds.bounds)==p.document['resolved_bounds']
                    assert ds.width==p.document['grid']['width'] and ds.height==p.document['grid']['height']
                    assert ds.crs.to_epsg()==2326 and ds.dtypes==('uint8',) and ds.nodata==NODATA[layer]
        expected_counts={layer:Counter() for layer in ('shade','quality','surface')}
        triples=Counter()
        for cell in manifest['cells']:
            shade,quality,transform=adapter.read_region_window(sidecar,utc_time=record['utc_time'],bounds=cell['bounds'],logical_mosaics=mosaics)
            surface=source.read_surface(cell['bounds'],p.records)
            for layer,array in zip(('shade','quality','surface'),(shade,quality,surface)):
                with rasterio.open(frame_dir/layer/(cell['id']+'.tif')) as ds:
                    assert ds.transform==transform and ds.crs.to_epsg()==2326 and ds.nodata==NODATA[layer]
                    assert ds.dtypes==('uint8',) and ds.is_tiled and ds.compression.value=='DEFLATE'
                    assert np.array_equal(ds.read(1),array)
                for suffix in ('.vrt','.tif'):
                    if suffix=='.tif' and not p.document['full_images']: continue
                    with rasterio.open(frame_dir/(layer+suffix)) as ds:
                        assert np.array_equal(ds.read(1,window=from_bounds(*cell['bounds'],ds.transform)),array)
                values,counts=np.unique(array,return_counts=True)
                expected_counts[layer].update({str(int(v)):int(n) for v,n in zip(values,counts)})
                if layer!='surface' and reference_index:
                    ref=ref_frames[record['utc_time']]['raster' if layer=='shade' else 'quality_raster']
                    with rasterio.open(ref) as ds:
                        win=from_bounds(*cell['bounds'],ds.transform)
                        assert ds.window_transform(win)==transform
                        assert np.array_equal(ds.read(1,window=win),array)
            if cell['source_tile'] is None:
                assert np.all(shade==255) and np.all(quality==1) and np.all(surface==255)
            encoded=(surface.astype(np.uint32)<<16)|(shade.astype(np.uint32)<<8)|quality
            values,counts=np.unique(encoded,return_counts=True)
            triples.update({int(v):int(n) for v,n in zip(values,counts)})
        assert {k:dict(v) for k,v in expected_counts.items()}==frame['value_counts']
        for counts in expected_counts.values(): assert sum(counts.values())==p.document['pixel_count']
        assert [dict(surface=k>>16,shade=(k>>8)&255,quality=k&255,pixels=n) for k,n in sorted(triples.items())]==frame['combinations']
        csv_expected.extend([[record['date'],record['time'],record['utc_time'],str(k>>16),str((k>>8)&255),str(k&255),str(n)]
                             for k,n in sorted(triples.items())])
        summarized=next(f for f in summary['frames'] if f['utc_time']==record['utc_time'])
        for item in summarized['surfaces']:
            actual={0:0,1:0,255:0}; qualities=Counter()
            for code,count in triples.items():
                if code>>16==item['surface']:
                    actual[(code>>8)&255]+=count; qualities[str(code&255)]+=count
            assert sum(actual.values())==item['pixels']
            assert [item['counts'][k] for k in ('sunlit','shaded','uncertain')]==[actual[c] for c in (0,1,255)]
            for label,count in item['counts'].items(): assert item['fractions'][label]==count/item['pixels']
            assert all(item['quality_counts'][q]==qualities[q] for q in v1.QUALITY)
        checked.append(dict(date=record['date'],time=record['time'],cells=len(manifest['cells']),pixels=p.document['pixel_count'],all_equal=True))
        print('Verified '+kind+' '+record['date']+'/'+record['time'],file=sys.stderr,flush=True)
    import csv
    with (folder/'summary.csv').open(newline='') as src:
        rows=list(csv.reader(src))
    assert rows[0]==['date','time','utc','surface','shade','quality','pixels'] and rows[1:]==csv_expected
    # Portable VRTs: all layers in all frames, after copying the complete folder.
    import shutil
    copied=DIAG/('portable_'+kind)
    shutil.copytree(folder,copied)
    for record in manifest['frames']:
        for layer in ('shade','quality','surface'):
            rel=Path(record['date'])/record['time']/(layer+'.vrt')
            with rasterio.open(folder/rel) as a,rasterio.open(copied/rel) as b:
                assert a.transform==b.transform and np.array_equal(a.read(1),b.read(1))
    shutil.rmtree(copied)
    paths=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assert len(paths)==len({x.casefold() for x in paths})
    for path in paths: safe_relative(path)
    def no_absolute(value,inside_machine=False):
        if isinstance(value,dict):
            for k,v in value.items(): no_absolute(v,inside_machine or k=='machine')
        elif isinstance(value,list):
            for v in value: no_absolute(v,inside_machine)
        elif isinstance(value,str) and not inside_machine: assert not value.startswith('/')
    for path in paths:
        if path.endswith('.json'): no_absolute(read_json(folder/path))
    atomic_json(EVIDENCE/(kind+'_pixel_verification.json'),dict(frames=checked,all_cells_engine_equal=True,
        reference_equal=bool(reference_index),surface_direct_dsm_equal=True,all_vrts_portable=True,
        path_count=len(paths),absolute_paths_only_in_machine=True,summary_counts_equal=True,
        sha256_manifest=digest(folder/'run_manifest.json')))


def reuse_comparison(kind):
    base=ROOT/'outputs/shade_map_f1_20261031/f1_sparse_window'
    folder=ROOT/'outputs/shade_map_f1_20261031'/read_json(config(kind)[1])['name']
    a,b=read_json(base/'run_manifest.json'),verify_run(folder)
    table={k:v for k,v in a['files'].items() if k.startswith('20260107/')}
    other={k:v for k,v in b['files'].items() if k.startswith('20260107/')}
    assert table==other
    assert not list(folder.rglob('*.partial'))
    work=ROOT/'outputs/shade_map_work'/(b['name']+'-'+b['run_id'][:12])
    with sqlite3.connect(work/'state/state.sqlite') as db:
        attempts=[dict(task=r[0],state=r[1],attempts=r[2]) for r in db.execute('SELECT task,MAX(state),COUNT(*) FROM attempts GROUP BY task')]
    killed=next(j for j in read_json(LEDGER)['jobs'] if j['intentional_sigkill'] and j['label'].startswith(kind+'_run'))
    if kind=='kill_compute':
        completed={task for task,state in killed['kill_evidence']['attempts'] if state=='SUCCEEDED'}
        assert completed and all(a['attempts']==1 for a in attempts if a['task'] in completed)
    else:
        assert all(a['attempts']==1 for a in attempts)
        for name,(sha,mtime) in killed['kill_evidence']['retained_files'].items():
            assert digest(folder/name)==sha and (folder/name).stat().st_mtime_ns==mtime
    atomic_json(EVIDENCE/(kind+'_resume_verification.json'),dict(all_published_hashes_equal=True,
        published_file_count=len(table),no_partial_survives=True,engine_events=b['engine_events'],
        publication_events=b['publication_events'],attempts=attempts,completed_tasks_not_redone=True,
        retained_frame_timestamps_unchanged=kind=='kill_publish'))


def finish():
    """Real conflict and prune verification; never compute another geometry."""
    import shutil
    from tools.shade_map.runner import prune_region,run_region
    mp,rp=config('b'); machine,region=read_json(mp),read_json(rp)
    folder=ROOT/'outputs/shade_map_f1_20261031'/region['name']
    manifest=verify_run(folder)
    work=ROOT/'outputs/shade_map_work'/(region['name']+'-'+manifest['run_id'][:12])
    before_manifest_sha256=digest(folder/'run_manifest.json')
    def snapshot():
        result={}
        for root in [ROOT/'outputs',ROOT/'data/processed']:
            for p in root.rglob('*'):
                if (p.is_file() or p.is_symlink()) and not p.is_relative_to(DIAG):
                    s=p.lstat(); result[p.relative_to(ROOT).as_posix()]=[s.st_size,s.st_mtime_ns]
        return result
    changed=deepcopy(region); changed['time']['end']='12:40'
    conflict=DIAG/'conflict_region.json'; atomic_json(conflict,changed)
    before=snapshot()
    rejected=subprocess.run([PYTHON,'-m','tools.shade_map','run','--machine',str(mp),str(conflict)],
                            cwd=ROOT,capture_output=True,text=True)
    assert rejected.returncode==2 and rejected.stderr.startswith('invalid input:') and not rejected.stdout
    assert before==snapshot()
    dry=prune_region(region,machine)
    assert before==snapshot() and work.exists() and not dry['deleted']
    result=prune_region(region,machine,yes=True)
    assert result['deleted'] and not work.exists()
    after=snapshot()
    removed=sorted(set(before)-set(after))
    modified=sorted(k for k in set(before)&set(after) if before[k]!=after[k])
    assert removed and all(k.startswith(work.relative_to(ROOT).as_posix()+'/') for k in removed)
    assert modified==[(folder/'run_manifest.json').relative_to(ROOT).as_posix()]
    assert not set(after)-set(before)
    rerun=run_region(region,machine)
    assert rerun['verified_only'] and not work.exists() and after==snapshot()
    atomic_json(EVIDENCE/'conflict_and_prune.json',dict(conflict_exit=2,conflict_stderr=rejected.stderr,
        conflict_wrote_nothing=True,dry_run=dry,pruned_work_files=removed,only_modified_file=modified,
        caches_source_views_other_runs_untouched=True,complete_rerun=rerun,
        before_manifest_sha256=before_manifest_sha256,after_manifest_sha256=digest(folder/'run_manifest.json')))


def audit():
    """Reproduce the final metadata listing and frozen source/contract checks."""
    before=read_json(EVIDENCE/'protected_before.json')
    changed=[]; missing=[]; unexpected=[]
    for name,stamp in before.items():
        p=ROOT/name
        if not p.exists() and not p.is_symlink():
            missing.append(name); continue
        st=p.lstat()
        now=[st.st_size,st.st_mtime_ns,os.readlink(p) if p.is_symlink() else None]
        if now!=stamp: changed.append(dict(path=name,before=stamp,after=now))
    roots=['data/raw','data/processed','outputs','presentations','docs/prompts','docs/planning',
           'docs/ui','tools/wsl2_smoke','web/console']
    allowed=('outputs/shade_map_work/','outputs/shade_map_f1_20261031/',
             'outputs/shade_map_f1_diagnostics_20261031/','data/processed/shade_v1/'+NAMESPACE)
    additions=[]
    for dirname in roots:
        for p in (ROOT/dirname).rglob('*'):
            if not (p.is_file() or p.is_symlink()): continue
            name=p.relative_to(ROOT).as_posix()
            if name in before: continue
            additions.append(name)
            permitted=name.startswith(allowed)
            if name.startswith('outputs/region_views/'):
                prefix='/'.join(name.split('/')[:3])+'/'
                permitted=not any(old.startswith(prefix) for old in before)
            if not permitted: unexpected.append(name)
    scope=dict(protected_files=len(before),changed=changed,missing=missing,unexpected_additions=unexpected,
               authorized_additions=sorted(additions),listings_equal_for_every_preexisting_file=not(changed or missing),
               method='path, size, nanosecond mtime, symlink target; existing files read-only')
    atomic_json(EVIDENCE/'protected_after.json',scope)
    assert not changed and not missing and not unexpected
    from tools.shade_map.common import ENGINE_FILES,CODE_ROOT
    start=read_json(EVIDENCE/'start.json')
    pinned={}
    for name in ENGINE_FILES:
        original=subprocess.check_output(['git','show','356f611d7b775ce31006904b80ca31d3c1c484b2:'+name],cwd=ROOT)
        pinned[name]=digest(ROOT/name)
        assert (ROOT/name).read_bytes()==original
    assert (ROOT/'tools/region_request.py').read_bytes()==subprocess.check_output(
        ['git','show','f5f24acc4163aa1353534d5db5a5dbe30faf0dae:tools/region_request.py'],cwd=ROOT)
    assert digest(ROOT/'docs/prompts/F1/ACCEPTANCE_CONTRACT.md')=='dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690'
    diff=subprocess.check_output(['git','diff',start['head'],'--','src/','tools/region_request.py'],cwd=ROOT,text=True)
    assert not diff
    atomic_json(EVIDENCE/'final_traceability.json',dict(start=start['head'],branch=subprocess.check_output(
        ['git','branch','--show-current'],cwd=ROOT,text=True).strip(),contract_sha256=digest(ROOT/'docs/prompts/F1/ACCEPTANCE_CONTRACT.md'),
        engine_hashes=pinned,engine_and_adapter_diff_empty=True,adapter_sha256=digest(ROOT/'tools/region_request.py'),
        tool_source_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'tools/shade_map').glob('*.py'))},
        requirements_lock_sha256=digest(ROOT/'requirements.lock.txt')))
    print(json.dumps(dict(protected_files=len(before),changed=0,unexpected=0,new_artifact_bytes=artifacts())))


def main():
    action=sys.argv[1]
    if action=='setup': setup()
    elif action=='gate': gate()
    elif action=='run-a':
        assert read_json(EVIDENCE/'cheung_chau_source_gate.json')['equal']; cli('run','a')
    elif action=='run-b':
        path=cli('plan','b'); plan=read_json(path)
        assert len(plan['cells'])==4 and any(c['source_tile'] is None for c in plan['cells'])
        atomic_json(EVIDENCE/'sparse_plan_before_execution.json',plan)
        cli('run','b'); cli('run','instant')
        monitored('independent_v1_reference',[PYTHON,__file__,'reference-internal'])
    elif action=='reference-internal': reference()
    elif action=='interrupt-compute':
        cli('run','kill_compute',kill_at=('compute','kill_compute')); cli('run','kill_compute'); reuse_comparison('kill_compute')
    elif action=='interrupt-publication':
        cli('run','kill_publish',kill_at=('publication','kill_publish')); cli('run','kill_publish'); reuse_comparison('kill_publish')
    elif action=='verify-internal': verify(sys.argv[2])
    elif action.startswith('verify-'):
        kind=action.removeprefix('verify-')
        monitored(kind+'_verify',[PYTHON,__file__,'verify-internal',kind])
    elif action=='finish': monitored('conflict_and_prune',[PYTHON,__file__,'finish-internal'])
    elif action=='finish-internal': finish()
    elif action=='audit': audit()
    else: raise ValueError(action)


if __name__=='__main__': main()
