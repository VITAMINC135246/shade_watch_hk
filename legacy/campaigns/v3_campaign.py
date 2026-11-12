"""Prepared, opt-in regional pilot launcher. No full-territory execution command.

All computational execution requires the named Linux host, a completed profile,
and --execute. Preparation is metadata/planning only. Not yet deployment tested.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def owned(relative, parent):
    path = (ROOT / relative).resolve()
    base = (ROOT / parent).resolve()
    if not path.is_relative_to(base) or path == base:
        raise ValueError(f'Path must be isolated below {base}')
    return path


def load_profile(path):
    p = read(path)
    if p['schema'] != 'shade-watch-v3-pilot-preparation-1.0' or p['scope'] != 'regional_pilots_only':
        raise ValueError('Only bounded regional pilot profiles are supported')
    name = p['campaign_id']
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in name):
        raise ValueError('Invalid campaign ID')
    b = p['budgets']
    if (type(b['workers']) is not int or not 1 <= b['workers'] <= 4
        or not 512 <= b['memory_mb'] <= 12288 or not 0 < b['artifact_bytes'] <= 20*1024**3
        or not 0 < b['wall_seconds'] <= 7200 or not 1 <= b['max_attempts'] <= 5):
        raise ValueError('Invalid bounded pilot budget')
    if p['science'] != dict(policy='SW-V1-POLICY-1.0', direction_method='nearest5', pixel_m=.5, search_m=1000):
        raise ValueError('Scientific policy changes need separate versioning')
    if not p['instants'] or len(p['instants']) > 16 or not 2 <= len(p['regions']) <= 8:
        raise ValueError('Pilot profile must contain 2..8 regions and 1..16 instants')
    ids = [r['id'] for r in p['regions']]
    if len(set(ids)) != len(ids) or any(not n or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in n) for n in ids):
        raise ValueError('Region IDs must be distinct safe names')
    for region in p['regions']:
        if len(region['tiles']) != 4 or len(set(region['tiles'])) != 4:
            raise ValueError('Each regional pilot requires exactly four distinct native tiles')
    if p['outputs'] != dict(scientific=True,logical_mosaic=True,statistics=True,jpg=False,mp4=False):
        raise ValueError('Prepared pilots require scientific, statistics and logical outputs only')
    return p


def locations(p):
    return owned('outputs/v3_'+p['campaign_id'], 'outputs'), owned('data/processed/shade_v1/v3_'+p['campaign_id'], 'data/processed/shade_v1')


def source_snapshot(raw):
    return {p.name: [p.stat().st_size, p.stat().st_mtime_ns] for p in sorted(raw.iterdir())
            if p.is_file() and (p.suffix.lower() in ('.tif','.tfw') or p.name.endswith('.aux.xml'))}


def engine_snapshot():
    files = list((ROOT/'src').glob('*.py')) + [Path(__file__),ROOT/'docs/v2/estimator.json']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def preflight(p, execution=False):
    import psutil
    import shutil
    from src.v2_state import local_filesystem
    out,cache = locations(p)
    if execution:
        if p.get('execution_authorized') is not True:
            raise ValueError('Execution is not authorized in this profile')
        if platform.system() != 'Linux' or p['machine']['system'] != 'Linux':
            raise ValueError('Scientific V3 pilots are disabled on this Mac; use the designated Linux host')
        if not p['machine']['hostname'] or socket.gethostname() != p['machine']['hostname']:
            raise ValueError('Complete and match the designated research-machine hostname')
        if not p['data'].get('vertical_datum'):
            raise ValueError('Confirm source vertical datum in the data profile')
        if not p.get('accepted_v2_commit') or not p.get('accepted_v2_report_sha256'):
            raise ValueError('Pin the independently accepted V2 commit and report hash')
        accepted=p['accepted_v2_commit']
        if len(accepted)!=40 or any(c not in '0123456789abcdef' for c in accepted):
            raise ValueError('Accepted V2 commit must be a full immutable SHA')
        for name in ('v2.py','v2_worker.py','v2_runner.py','v2_state.py','v1.py','v1_cache.py','horizon.py','solar.py','spatial.py','shade_watch.py'):
            expected=subprocess.check_output(['git','show',f'{accepted}:src/{name}'],cwd=ROOT)
            if (ROOT/'src'/name).read_bytes()!=expected:
                raise ValueError('Engine differs from accepted V2; reaccept changes before pilots')
        report=ROOT/p['accepted_v2_report']
        if hashlib.sha256(report.read_bytes()).hexdigest()!=p['accepted_v2_report_sha256']:
            raise ValueError('Accepted report identity mismatch')
        if not platform.python_version().startswith(p['machine']['python']+'.'):
            raise ValueError('Python runtime differs from the pinned profile')
    for path in (out,cache): local_filesystem(path)
    free=shutil.disk_usage(ROOT).free
    available=psutil.virtual_memory().available
    if free < max(p['budgets']['artifact_bytes'],p['machine']['minimum_free_disk_gib']*1024**3):
        raise ValueError('Insufficient local disk headroom')
    if available < max(p['budgets']['memory_mb']*1024**2,p['machine']['min_available_memory_gib']*1024**3):
        raise ValueError('Insufficient available memory headroom')
    return dict(host=socket.gethostname(),system=platform.system(),python=platform.python_version(),
                cpu_count=os.cpu_count(),available_memory_bytes=available,free_disk_bytes=free,
                execution_requested=execution)


def prepare(p):
    import rasterio
    from src import v2
    from src.spatial import intersects
    from src.v1_cache import atomic_json
    out,cache=locations(p)
    environment=preflight(p)
    manifest=out/'prepared.json'
    if manifest.exists():
        raise ValueError('Prepared campaign exists; preserve it, use status/resume or a new campaign ID')
    raw=(ROOT/p['data']['root']).resolve()
    snapshot=source_snapshot(raw)
    headers=[]
    for file in sorted(raw.glob('*.tif')):
        with rasterio.open(file) as ds:
            a=ds.transform
            if (str(ds.crs)!='EPSG:2326' or ds.count!=1 or a.a!=.5 or a.e!=-.5 or a.b!=0 or a.d!=0
                or ds.width*ds.height>2_000_000):
                raise ValueError(f'Unsupported native grid: {file.name}')
            headers.append(dict(path=file,bounds=tuple(ds.bounds)))
    if not headers: raise ValueError('No DSM sources')
    by_name={r['path'].name:r for r in headers}
    plans=[]
    for region in p['regions']:
        selected=[by_name[n] for n in region['tiles']]
        supports=[r for r in headers if any(intersects(r['bounds'],(t['bounds'][0]-1000,t['bounds'][1]-1000,t['bounds'][2]+1000,t['bounds'][3]+1000)) for t in selected)]
        view=out/'sources'/region['id'];view.mkdir(parents=True,exist_ok=True)
        for rec in supports:
            file=rec['path']
            for source in (file,file.with_suffix('.tfw'),Path(str(file)+'.aux.xml')):
                if source.exists():
                    link=view/source.name
                    if link.is_symlink() and link.resolve()!=source.resolve():raise ValueError('Source view changed')
                    if not link.exists():link.symlink_to(source)
        base=dict(dsm_dir=str(view),instants=p['instants'],cache_dir=str(cache),direction_method=p['science']['direction_method'])
        requests=[dict(base,id='tile_'+str(i),tile=name,output_dir=str(out/region['id']/('tile_'+str(i)))) for i,name in enumerate(region['tiles'])]
        requests.append(dict(base,id='combined',tiles=region['tiles'],output_dir=str(out/region['id']/'combined')))
        b=p['budgets']
        plan=v2.plan_batch(requests,workers=b['workers'],memory_budget_mb=b['memory_mb'],artifact_budget_bytes=b['artifact_bytes'],max_attempts=b['max_attempts'],logical_mosaic=True,statistics=True)
        plan_path=out/'plans'/(region['id']+'.json');atomic_json(plan_path,plan.to_dict())
        plans.append(dict(region=region['id'],path=str(plan_path),sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),batch=plan.id,support_files=len(supports),estimate=plan.estimate))
    peak = sum(r['estimate']['resources']['retained_new_bytes'] for r in plans) + max(r['estimate']['resources']['temporary_new_bytes'] for r in plans)
    if peak > p['budgets']['artifact_bytes']:
        raise ValueError('Aggregate regional storage estimate exceeds campaign budget')
    # Frozen before any submission or calculation. This is not a V3 acceptance report.
    result=dict(profile=p,profile_sha256=digest(p),engine=engine_snapshot(),source_snapshot=snapshot,
                environment=environment,plans=plans,created_utc=time.time(),status='PREPARED_NOT_EXECUTED',
                caveat='Regional V2-backed launcher; indexed territory ingestion and administrative coverage remain separate V3 work')
    atomic_json(manifest,result)
    atomic_json(out/'ledger.json',dict(elapsed_seconds=0,attempts=[]))
    return result


def generated_bytes(out,cache):
    return sum(x.stat().st_size for root in (out,cache) if root.exists() for x in root.rglob('*') if x.is_file() and not x.is_symlink())


def verify_region(out,region,batch):
    import numpy as np
    import rasterio
    from rasterio.windows import from_bounds
    from src.v2_worker import read_logical_window
    combined=read(out/region/'combined/result_index.json')
    natives=[read(out/region/('tile_'+str(i))/'result_index.json') for i in range(4)]
    for f,frame in enumerate(combined['frames']):
        for index in natives:
            for role in ('raster','quality_raster'):
                with rasterio.open(frame[role]) as full,rasterio.open(index['frames'][f][role]) as tile:
                    for _,window in tile.block_windows(1):
                        bounds=rasterio.windows.bounds(window,tile.transform)
                        if not np.array_equal(tile.read(1,window=window),full.read(1,window=from_bounds(*bounds,full.transform))):
                            raise ValueError('Native/combined scientific pixels differ')
        with rasterio.open(frame['raster']) as ds:
            x,y=ds.bounds.left+750,ds.bounds.top-600
            bounds=(x-2,y-2,x+2,y+2)
            view=read_logical_window(out/'state'/region/(batch+'.logical_mosaic.json'),utc_time=frame['utc_time'],bounds=bounds)
            for arr,role in zip(view[:2],('raster','quality_raster')):
                with rasterio.open(frame[role]) as source:
                    if not np.array_equal(arr,source.read(1,window=from_bounds(*bounds,source.transform))):
                        raise ValueError('Logical seam differs from combined output')
    return dict(native_combined_equal=True,logical_seam_equal=True,frames=len(combined['frames']),observational_accuracy='NOT VERIFIED')


def execute(p,resume,confirmed):
    from src import v2
    from src.v1_cache import atomic_json,exclusive_lock
    if not confirmed:raise ValueError('Scientific execution requires explicit --execute')
    preflight(p,execution=True)
    out,cache=locations(p);prepared=read(out/'prepared.json')
    if prepared['profile_sha256']!=digest(p) or prepared['engine']!=engine_snapshot():
        raise ValueError('Profile/code changed; prepare a new campaign ID')
    if prepared['source_snapshot']!=source_snapshot((ROOT/p['data']['root']).resolve()):
        raise ValueError('Source catalog changed; prepare a new campaign ID')
    with exclusive_lock(out/'.campaign.lock'):
        ledger=read(out/'ledger.json')
        if any(a['state']=='RUNNING' for a in ledger['attempts']):
            raise ValueError('Interrupted outer launcher has unreconciled budget; inspect ledger and account elapsed time before resuming')
        for row in prepared['plans']:
            path=Path(row['path'])
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Prepared plan changed')
            state=out/'state'/row['region']
            plan=v2.BatchPlan(**read(path));bid=v2.submit_batch(plan,state_dir=state)
            if v2.status_batch(bid,state_dir=state)['state']=='SUCCEEDED':
                began=time.monotonic()
                ledger.setdefault('verified_regions',{})[row['region']]=verify_region(out,row['region'],bid)
                ledger['elapsed_seconds']+=time.monotonic()-began
                atomic_json(out/'ledger.json',ledger)
                if ledger['elapsed_seconds']>p['budgets']['wall_seconds']:
                    raise ValueError('Campaign budget exhausted during verification')
                continue
            remaining=p['budgets']['wall_seconds']-ledger['elapsed_seconds']
            if remaining<=0 or generated_bytes(out,cache)>=p['budgets']['artifact_bytes']:
                raise ValueError('Cumulative campaign budget exhausted')
            attempt=dict(region=row['region'],batch=bid,state='RUNNING',started_utc=time.time(),reserved_seconds=remaining)
            ledger['attempts'].append(attempt);atomic_json(out/'ledger.json',ledger)
            start=time.monotonic();proc=None
            try:
                log=out/(row['region']+f'.attempt{len(ledger["attempts"])}.log')
                with log.open('w') as handle:
                    proc=subprocess.Popen([sys.executable,'-m','src.v2','resume' if resume else 'run','--batch',bid,'--state',str(state)],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
                    while proc.poll() is None:
                        if time.monotonic()-start>=remaining or generated_bytes(out,cache)>p['budgets']['artifact_bytes']:
                            v2.cancel_batch(bid,state_dir=state)
                            raise RuntimeError('Campaign time/storage limit reached')
                        time.sleep(.5)
                result=v2.status_batch(bid,state_dir=state)
                attempt.update(result=result,state=result['state'],returncode=proc.returncode)
                if proc.returncode or result['state']!='SUCCEEDED':raise RuntimeError('Pilot failed; inspect recorded attempts before resume')
                attempt['verification']=verify_region(out,row['region'],bid)
                ledger.setdefault('verified_regions',{})[row['region']]=attempt['verification']
            except BaseException as exc:
                attempt.update(state='FAILED',error=repr(exc));raise
            finally:
                if proc is not None and proc.poll() is None:
                    # This group was created by this launcher and contains only its owned V2 job.
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                attempt['elapsed_seconds']=time.monotonic()-start
                ledger['elapsed_seconds']+=attempt['elapsed_seconds']
                ledger['generated_bytes']=generated_bytes(out,cache)
                atomic_json(out/'ledger.json',ledger)
        if any(a['state']=='FAILED' for a in ledger['attempts']):
            # Historical failures remain evidence; current status determines completion.
            ledger['note']='Historical failed attempts retained; inspect latest verified batch statuses'
        if len(ledger.get('verified_regions',{}))!=len(prepared['plans']) or ledger['elapsed_seconds']>p['budgets']['wall_seconds'] or generated_bytes(out,cache)>p['budgets']['artifact_bytes']:
            raise ValueError('Campaign verification or final resource reconciliation incomplete')
        ledger['status']='REGIONAL_PILOTS_FINISHED_NOT_TERRITORY_ACCEPTANCE'
        atomic_json(out/'ledger.json',ledger)
        return ledger


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['preflight','prepare','run','resume','status','cancel'])
    parser.add_argument('--profile',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();p=load_profile(args.profile)
    if args.action=='preflight':result=preflight(p,execution=args.execute)
    elif args.action=='prepare':result=prepare(p)
    elif args.action in ('run','resume'):result=execute(p,args.action=='resume',args.execute)
    else:
        from src import v2
        out,_=locations(p);prepared=read(out/'prepared.json');result={}
        for row in prepared['plans']:
            state=out/'state'/row['region']
            if not (state/'state.sqlite').exists():result[row['region']]='NOT_SUBMITTED';continue
            result[row['region']]=(v2.cancel_batch(row['batch'],state_dir=state) if args.action=='cancel' else v2.status_batch(row['batch'],state_dir=state))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError) as exc:raise SystemExit(f'V3 pilot request rejected: {exc}')
