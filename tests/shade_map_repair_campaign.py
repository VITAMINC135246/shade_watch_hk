"""Bounded F1 repair campaign; exact actions, fresh outputs, monitored planning."""
from __future__ import annotations
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time

import psutil
from src import v1
from tools.shade_map.common import atomic_json, digest, read_json
from tools.shade_map.config import InvalidInput
from tools.shade_map.planning import prepare
from tools.shade_map.runner import run_region, prune_region, verify_run

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT/'outputs/shade_map_f1_repair_1_diagnostics_20261104'
PUB = ROOT/'outputs/shade_map_f1_repair_1_20261104'
EVIDENCE = ROOT/'docs/shade_map/evidence/repair_1'
LEDGER = EVIDENCE/'resource_ledger.json'
NS = 'f1_repair_1_20261104_'
PYTHON = str(ROOT/'.venv/bin/python')
ENV = {**os.environ, 'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1',
       'NUMBA_CACHE_DIR': str(DIAG/'numba_cache')}

spec = importlib.util.spec_from_file_location('original_f1_campaign', Path(__file__).with_name('shade_map_campaign.py'))
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
original.DIAG, original.EVIDENCE, original.LEDGER, original.NAMESPACE = DIAG, EVIDENCE, LEDGER, NS


def config(kind):
    return DIAG/(kind+'_machine.json'), DIAG/(kind+'_region.json')


def artifacts():
    before = read_json(DIAG/'protected_before.json')
    roots = [PUB, DIAG, EVIDENCE]
    roots += list((ROOT/'data/processed/shade_v1').glob(NS+'*'))
    roots += list((ROOT/'outputs/shade_map_work').glob('f1r1_*'))
    views = ROOT/'outputs/region_views'
    roots += [p for p in views.iterdir() if p.is_dir() and not any(
        name.startswith(p.relative_to(ROOT).as_posix()+'/') for name in before)] if views.exists() else []
    return sum(p.lstat().st_size for root in roots if root.exists()
               for p in root.rglob('*') if p.is_file() or p.is_symlink())


def monitored(label, argv, kill_kind=None):
    ledger = read_json(LEDGER) if LEDGER.exists() else dict(
        schema='shade-map-repair-ledger-1.0', previous_development_seconds=2096.71,
        limits=dict(repair_seconds=1500, memory_bytes=12*1024**3, artifacts_bytes=20*1024**3), jobs=[])
    remaining = 1500-sum(j['wall_seconds'] for j in ledger['jobs'])
    if remaining < 15: raise RuntimeError('STOP before remaining development allowance is exhausted')
    out, err = DIAG/(label+'.stdout.json'), DIAG/(label+'.stderr.txt')
    assert not out.exists(), 'Preserve previous evidence; action already recorded'
    # Enumeration permission is mandatory; never silently continue with an RSS gap.
    psutil.Process().memory_info()
    started = time.perf_counter(); peak = 0; disk = artifacts(); next_disk = 0
    peaks = {}; samples = 0; failure = None; killed = None; concurrent = None
    with ThreadPoolExecutor(max_workers=1) as sampler, out.open('w') as stdout, err.open('w') as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, env=ENV, stdout=stdout, stderr=stderr, start_new_session=True)
        owner = psutil.Process(process.pid)
        disk_sample = None
        try:
            while process.poll() is None:
                elapsed = time.perf_counter()-started
                try:
                    tree = [owner]+owner.children(recursive=True)
                except psutil.NoSuchProcess:
                    if process.poll() is not None: break
                    raise
                if concurrent is not None:
                    try: tree += [psutil.Process(concurrent.pid)]
                    except psutil.NoSuchProcess: pass
                rss = 0
                for child in tree:
                    try:
                        memory = child.memory_info().rss
                        key = str(child.pid)+':'+str(child.create_time())
                        peaks[key] = max(peaks.get(key, 0), memory); rss += memory
                    except psutil.NoSuchProcess: pass
                peak = max(peak, rss); samples += 1
                if disk_sample is not None and disk_sample.done():
                    disk = max(disk, disk_sample.result()); disk_sample = None
                if elapsed >= next_disk and disk_sample is None:
                    disk_sample = sampler.submit(artifacts); next_disk = elapsed+10
                if elapsed >= remaining-15 or peak >= 11.5*1024**3 or disk >= 19*1024**3:
                    raise RuntimeError('STOP before a frozen resource ceiling')
                if kill_kind:
                    work = list((ROOT/'outputs/shade_map_work').glob('f1r1_'+kill_kind+'-*'))
                    if work and (work[0]/'state/state.sqlite').exists():
                        try:
                            with sqlite3.connect('file:'+str(work[0]/'state/state.sqlite')+'?mode=ro', uri=True) as db:
                                tasks = [dict(id=a, state=b, attempts=c) for a,b,c in db.execute('SELECT id,state,attempts FROM tasks')]
                        except sqlite3.Error:
                            tasks = []  # Schema initialization can precede its first commit.
                        folder = PUB/('f1r1_'+kill_kind)
                        compute = kill_kind == 'kill_compute' and any(t['state']=='SUCCEEDED' for t in tasks) and any(t['state']=='RUNNING' for t in tasks)
                        publication = kill_kind == 'kill_publish' and list(folder.glob('*/*/frame.json')) and list(folder.glob('*/*.partial'))
                        if compute and concurrent is None:
                            mp,rp=config(kill_kind)
                            concurrent = subprocess.Popen([PYTHON,'-m','tools.shade_map','run','--machine',str(mp),str(rp)],
                                cwd=ROOT,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                        refused = None
                        if concurrent is not None and concurrent.poll() is not None:
                            a,b = concurrent.communicate()
                            assert concurrent.returncode == 2 and b.startswith('invalid input:') and 'another run owns the lock' in b and not a
                            refused = dict(exit=2, stderr=b)
                        if publication or (compute and refused):
                            # Freeze only our captured processes so the observed
                            # publication/computation phase cannot finish while
                            # its evidence is read, then deliver real SIGKILL.
                            for child in tree:
                                try: child.send_signal(signal.SIGSTOP)
                                except psutil.NoSuchProcess: pass
                            retained = {p.relative_to(folder).as_posix():[digest(p),p.stat().st_mtime_ns]
                                        for f in folder.glob('*/*/frame.json') for p in f.parent.rglob('*') if p.is_file()}
                            killed = dict(tasks=tasks, retained=retained, concurrent_refusal=refused,
                                          partials=[p.relative_to(folder).as_posix() for p in folder.glob('*/*.partial')])
                            for child in reversed(tree):
                                try: child.kill()
                                except psutil.NoSuchProcess: pass
                            break
                time.sleep(.005)
        except Exception as exc:
            failure = repr(exc)
            try: owned_tree=[owner]+owner.children(recursive=True)
            except psutil.NoSuchProcess: owned_tree=[owner]
            for child in reversed(owned_tree):
                try: child.kill()
                except psutil.NoSuchProcess: pass
        process.wait()
        if killed and process.returncode != -signal.SIGKILL:
            failure='Observed controller did not terminate from SIGKILL'
        if disk_sample is not None: disk = max(disk, disk_sample.result())
    seconds = time.perf_counter()-started; disk = max(disk, artifacts())
    row = dict(label=label,argv=list(map(str,argv)),wall_seconds=seconds,peak_tree_rss_bytes=peak,
               per_process_peak_rss_bytes=peaks,samples=samples,new_artifact_bytes=disk,returncode=process.returncode,
               intentional_sigkill=killed,monitoring_failure=failure,stdout=str(out.relative_to(ROOT)),stderr=str(err.relative_to(ROOT)))
    ledger['jobs'].append(row)
    ledger['previous_development_seconds']=read_json(EVIDENCE.parent/'resource_ledger.json')['total_real_job_seconds']
    ledger.update(total_repair_seconds=sum(j['wall_seconds'] for j in ledger['jobs']),
                  peak_tree_rss_bytes=max(j['peak_tree_rss_bytes'] for j in ledger['jobs']),
                  peak_new_artifact_bytes=max(j['new_artifact_bytes'] for j in ledger['jobs']))
    ledger['within_budget'] = (ledger['total_repair_seconds'] <= 1500 and ledger['peak_tree_rss_bytes'] <= 12*1024**3
                               and ledger['peak_new_artifact_bytes'] <= 20*1024**3)
    ledger['total_development_seconds']=ledger['previous_development_seconds']+ledger['total_repair_seconds']
    ledger['complete_monitoring'] = all(j['peak_tree_rss_bytes'] > 0 and not j['monitoring_failure'] for j in ledger['jobs'])
    atomic_json(LEDGER,ledger)
    print(json.dumps({k:v for k,v in row.items() if k not in ('per_process_peak_rss_bytes','intentional_sigkill')}),flush=True)
    if failure: raise RuntimeError(failure)
    if kill_kind and not killed: raise RuntimeError('Interruption phase was not observed')
    if not kill_kind and process.returncode: raise RuntimeError('Job failed; see preserved stderr')


def cli(action, kind, label=None, **kwargs):
    mp,rp=config(kind)
    monitored(label or kind+'_'+action,[PYTHON,'-m','tools.shade_map',action,'--machine',str(mp),str(rp)],**kwargs)


def setup():
    frozen = {}
    for kind in ['a','b','instant','kill_compute','kill_publish']:
        old = ROOT/'outputs/shade_map_f1_diagnostics_20261031'
        region = read_json(old/(kind+'_region.json'))
        region['name'] = 'f1r1_'+kind
        machine = dict(schema='shade-map-machine-1.0',dsm_dir='data/raw/dsm/2020/D12.DSM.TIFF',
                       output_root=str(PUB.relative_to(ROOT)),cache_namespace=NS+kind,
                       workers=1,memory_budget_mb=8192,max_output_bytes=12*1024**3)
        mp,rp=config(kind)
        assert not mp.exists() and not (ROOT/'data/processed/shade_v1'/(NS+kind)).exists()
        atomic_json(mp,machine); atomic_json(rp,region)
        frozen[kind]=dict(region=region,machine=machine)
    assert not PUB.exists()
    atomic_json(EVIDENCE/'frozen_campaign.json',dict(frozen_before_real_planning=True,configs=frozen,
        unchanged_original_geometry_and_times=True,remaining_wall_seconds=1500))


def gate():
    p = prepare(read_json(config('a')[1]),read_json(config('a')[0]))
    actual = sorted(x.name for x in Path(p.adapter_plan['sidecar']['source_directory']).glob('*.tif'))
    reference = sorted(x.name for x in (ROOT/'outputs/v2_daylight_cheungchau_20261009/source_view').glob('*.tif'))
    assert actual == reference, 'STOP: source list changed'
    assert len(p.document['frames'])==65 and p.document['frames'][0]['time']=='0710' and p.document['frames'][-1]['time']=='1750'
    assert not (ROOT/'data/processed/shade_v1'/(NS+'a')).exists()
    atomic_json(EVIDENCE/'cheung_chau_source_gate.json',dict(actual=actual,reference=reference,equal=True,
        cold_cache=True,plan=p.document,source_identity=p.identity_document['source_identity']))


def reference():
    p = prepare(read_json(config('b')[1]),read_json(config('b')[0]))
    assert len(p.document['cells'])==4 and any(c['source_tile'] is None for c in p.document['cells'])
    cache=ROOT/'data/processed/shade_v1'/(NS+'reference')
    assert not cache.exists(), 'V1 reference cache must be cold'
    plan = v1.plan_shade(mode='custom',bounds=p.document['resolved_bounds'],
        instants=[f['local_time'] for f in p.document['frames']],dsm_dir=p.adapter_plan['sidecar']['source_directory'],
        output_dir=ROOT/'outputs/shade_map_work/f1r1_reference/v1',
        cache_dir=cache)
    result = v1.run_shade(plan)
    atomic_json(EVIDENCE/'independent_v1_reference.json',dict(index=str(Path(result.index_path).relative_to(ROOT)),
        jobs=result.jobs,cache_cold_before=True,bounds=p.document['resolved_bounds'],frames=[f['utc_time'] for f in result.frames]))


def compare_original(kind):
    original.verify(kind)
    region=read_json(config(kind)[1]); folder=PUB/region['name']
    oldname={'a':'f1_cheung_chau','b':'f1_sparse_window','instant':'f1_sparse_instants'}[kind]
    old=ROOT/'outputs/shade_map_f1_20261031'/oldname
    paths=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*.tif'))
    assert paths==sorted(p.relative_to(old).as_posix() for p in old.rglob('*.tif'))
    hashes={name:digest(folder/name) for name in paths}
    assert all(sha==digest(old/name) for name,sha in hashes.items())
    atomic_json(EVIDENCE/(kind+'_original_raster_hashes.json'),dict(original=str(old.relative_to(ROOT)),
        repaired=str(folder.relative_to(ROOT)),all_rasters_sha256_equal=True,files=hashes))


def resume_check(kind):
    region=read_json(config(kind)[1]);folder=PUB/region['name'];manifest=verify_run(folder)
    base=verify_run(PUB/'f1r1_b')
    files={k:v for k,v in manifest['files'].items() if k.startswith('20260107/')}
    assert files=={k:v for k,v in base['files'].items() if k.startswith('20260107/')}
    killed=next(j['intentional_sigkill'] for j in read_json(LEDGER)['jobs'] if j['label']==kind+'_kill')
    work=ROOT/'outputs/shade_map_work'/(region['name']+'-'+manifest['run_id'][:12])
    with sqlite3.connect(work/'state/state.sqlite') as db:
        now={a:(b,c) for a,b,c in db.execute('SELECT id,state,attempts FROM tasks')}
    completed=[t for t in killed['tasks'] if t['state']=='SUCCEEDED']
    assert completed and all(now[t['id']]==('SUCCEEDED',t['attempts']) for t in completed)
    for name,(sha,mtime) in killed['retained'].items(): assert digest(folder/name)==sha and (folder/name).stat().st_mtime_ns==mtime
    atomic_json(EVIDENCE/(kind+'_resume.json'),dict(all_frame_hashes_equal=True,files=len(files),
        completed_tasks_retained=len(completed),published_files_retained=len(killed['retained']),no_partials=not list(folder.rglob('*.partial')),
        tasks=now,engine_events=manifest['engine_events'],concurrent_refusal=killed['concurrent_refusal']))


def finish():
    region,machine=read_json(config('b')[1]),read_json(config('b')[0]);folder=PUB/region['name']
    manifest=verify_run(folder)
    work=ROOT/'outputs/shade_map_work'/(region['name']+'-'+manifest['run_id'][:12])
    # Verification can use the very same raw inputs through the existing view.
    # Paths are machine settings, and the source-identity check remains active.
    machine['dsm_dir']=read_json(work/'adapter/region_request.json')['source_directory']
    conflict=deepcopy(region);conflict['time']['end']='12:40'
    conflict_path=DIAG/'conflict_region.json';atomic_json(conflict_path,conflict)
    conflict_machine=DIAG/'conflict_machine.json';atomic_json(conflict_machine,machine)
    def snapshot():
        return {str(p.relative_to(ROOT)):(p.lstat().st_size,p.lstat().st_mtime_ns)
                for root in [ROOT/'outputs',ROOT/'data/processed'] for p in root.rglob('*')
                if (p.is_file() or p.is_symlink()) and not p.is_relative_to(DIAG)}
    before=snapshot()
    refused=subprocess.run([PYTHON,'-m','tools.shade_map','run','--machine',str(conflict_machine),str(conflict_path)],
                           cwd=ROOT,env=ENV,capture_output=True,text=True)
    assert refused.returncode==2 and refused.stderr.startswith('invalid input:') and snapshot()==before
    partial=folder/'20260107/1230.partial';partial.mkdir()
    result=run_region(region,machine)
    assert result['verified_only'] and not list(folder.rglob('*.partial'))
    dry=prune_region(region,machine);pruned=prune_region(region,machine,yes=True)
    after=run_region(region,machine)
    assert not dry['deleted'] and pruned['deleted'] and after['verified_only'] and after['computed_batches']==0
    atomic_json(EVIDENCE/'partial_and_prune.json',dict(empty_orphan_removed=True,complete_result=result,prune=pruned,after_prune=after,
        real_same_name_conflict=dict(exit=2,stderr=refused.stderr,no_writes=True)))


def incomplete(kind):
    machine,region=read_json(config(kind)[0]),read_json(config(kind)[1])
    folder=PUB/region['name'];before=digest(folder/'run_manifest.json')
    try:prune_region(region,machine,yes=True)
    except InvalidInput as exc:
        assert 'every frame must be published' in str(exc)
        assert digest(folder/'run_manifest.json')==before
        atomic_json(EVIDENCE/(kind+'_incomplete.json'),dict(prune_refused=True,reason=str(exc),manifest_unchanged=True))
    else:raise AssertionError('Incomplete prune was accepted')


def audit():
    before=read_json(DIAG/'protected_before.json');changed=[];missing=[];unexpected=[]
    for name,stamp in before.items():
        path=ROOT/name
        if not path.exists() and not path.is_symlink(): missing.append(name);continue
        st=path.lstat();now=[st.st_size,st.st_mtime_ns,os.readlink(path) if path.is_symlink() else None]
        if now!=stamp:changed.append(name)
    allowed=(str(PUB.relative_to(ROOT))+'/',str(DIAG.relative_to(ROOT))+'/',
             'outputs/shade_map_work/f1r1_','outputs/shade_map_work/.locks/f1r1_',
             'data/processed/shade_v1/'+NS)
    for prefix in ['data/raw','data/processed','outputs','presentations','docs/prompts','docs/planning','docs/ui','tools/wsl2_smoke','web/console']:
        for path in (ROOT/prefix).rglob('*'):
            if not(path.is_file() or path.is_symlink()):continue
            name=path.relative_to(ROOT).as_posix()
            if name in before or name.startswith(allowed):continue
            if name.startswith('outputs/region_views/'):
                view='/'.join(name.split('/')[:3])+'/'
                if not any(old.startswith(view) for old in before):continue
            unexpected.append(name)
    atomic_json(EVIDENCE/'protected_after.json',dict(protected_files=len(before),changed=changed,missing=missing,
        unexpected_additions=unexpected,review_and_original_outputs_untouched=not(changed or missing or unexpected)))
    assert not(changed or missing or unexpected),(changed,missing,unexpected)
    start=read_json(EVIDENCE/'start.json')
    for name,sha in start['engine_hashes'].items():assert digest(ROOT/name)==sha
    assert digest(ROOT/'tools/region_request.py')==start['adapter_sha256']
    assert digest(ROOT/'docs/prompts/F1/ACCEPTANCE_CONTRACT.md')==start['contract_sha256']
    assert not subprocess.check_output(['git','diff',start['start'],'--','src/','tools/region_request.py','docs/prompts/','config/v3/',
        'docs/shade_map/evidence',':(exclude)docs/shade_map/evidence/repair_1/**'],cwd=ROOT)
    assert digest(ROOT/'docs/shade_map/INDEPENDENT_ACCEPTANCE_eb605f52d119.md')==start['review_report_sha256']
    original_partial=ROOT/'outputs/shade_map_review_eb605f52d119_20261031/worktree/outputs/shade_map_review_published/shade_map_review_central_i/20260621/1000.partial'
    assert original_partial.is_dir(), 'Preserve the reviewer failure folder'
    sources={}
    for kind in ['a','b','instant']:
        manifest=read_json(PUB/read_json(config(kind)[1])['name']/'run_manifest.json')
        for source in manifest['source_identity']['sources']:
            path=ROOT/'data/raw/dsm/2020/D12.DSM.TIFF'/source['name']
            assert digest(path)==source['sha256'];sources[str(path.relative_to(ROOT))]=source['sha256']
    inputs={str(path.relative_to(ROOT)):digest(path) for path in DIAG.glob('*_*.json') if 'stdout' not in path.name}
    inputs.update(sources)
    atomic_json(EVIDENCE/'traceability.json',dict(start=start['start'],contract_sha256=start['contract_sha256'],
        engine_hashes=start['engine_hashes'],adapter_sha256=start['adapter_sha256'],
        tool_source_hashes={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'tools/shade_map').glob('*.py')},
        input_hashes=inputs,python=sys.version,platform=sys.platform,
        libraries={name:importlib.metadata.version(name) for name in ['numpy','rasterio','pyproj','numba','psutil','pytest']},
        requirements_lock_sha256=digest(ROOT/'requirements.lock.txt'),tools_lock_sha256=digest(ROOT/'requirements.tools.lock.txt')))


def main():
    action=sys.argv[1]
    if action=='setup': setup()
    elif action in ('tests', 'tests-final'):
        label = 'full_tests' if action == 'tests' else 'full_tests_final'
        monitored(label,[PYTHON,'-m','pytest','tests','-q','--disable-warnings','--basetemp',str(DIAG/(label+'_tmp')),'-o','cache_dir='+str(DIAG/'pytest_cache')])
    elif action=='plans':
        cli('plan','a');monitored('source_gate',[PYTHON,__file__,'_gate']);cli('plan','b');cli('plan','instant')
    elif action=='a':
        assert read_json(EVIDENCE/'cheung_chau_source_gate.json')['equal'];cli('run','a')
    elif action=='b':
        cli('run','b');cli('run','instant');monitored('v1_reference',[PYTHON,__file__,'_reference'])
    elif action=='verify':monitored('all_verify',[PYTHON,__file__,'_verify_all'])
    elif action in ('kill_compute','kill_publish'):
        cli('run',action,label=action+'_kill',kill_kind=action)
        monitored(action+'_incomplete',[PYTHON,__file__,'_incomplete',action])
        cli('run',action,label=action+'_resume')
        monitored(action+'_check',[PYTHON,__file__,'_resume_check',action])
    elif action=='finish':monitored('partial_prune',[PYTHON,__file__,'_finish'])
    elif action=='audit':monitored('protected_audit',[PYTHON,__file__,'_audit'])
    elif action=='_gate':gate()
    elif action=='_reference':reference()
    elif action=='_verify':compare_original(sys.argv[2])
    elif action=='_verify_all':
        for kind in ['a','b','instant']:compare_original(kind)
    elif action=='_resume_check':resume_check(sys.argv[2])
    elif action=='_finish':finish()
    elif action=='_incomplete':incomplete(sys.argv[2])
    elif action=='_audit':audit()
    else:raise ValueError('Unknown exact campaign action: '+action)


if __name__=='__main__': main()
