"""Bounded R06 development exercise, never an independent acceptance harness."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import psutil
import rasterio

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src import v1,v2
from src.spatial import intersects
from src.v2_worker import read_logical_window
from tools.region_request import plan_region,write_region

OUT=ROOT/'outputs/region_dev_validation'
CACHE=ROOT/'data/processed/shade_v1/region_dev'
DOC=ROOT/'docs/region/evidence'


def save(name,value):
    (DOC/name).write_text(json.dumps(value,indent=2,default=str)+'\n')


def work():
    raw=ROOT/'data/raw/dsm/2020/D12.DSM.TIFF'
    view=OUT/'catalogue'
    view.mkdir(parents=True,exist_ok=False)
    # A read-only symlink catalogue includes EVERY source intersecting the fixed
    # native owners' 1 km halos. No DSM values are copied or modified.
    halo=(843250.,820600.,846000.,823800.)
    selected=[]
    for p in sorted(raw.glob('*.tif')):
        with rasterio.open(p) as ds:
            if intersects(halo,ds.bounds):
                selected.append(dict(path=str(p),bounds=list(ds.bounds)))
                (view/p.name).symlink_to(p)
    save('catalogue.json',dict(halo=halo,selection='all source footprints intersecting union of two owners plus 1000 m buffer',sources=selected))
    print(f'selected {len(selected)} native source tiles',flush=True)
    times=['2026-01-07T14:31:27+08:00','2026-01-07T14:31:28+08:00']
    plan=plan_region((844701.5,822197.5),(844713.5,822202.5),crs='hk1980',
                     instants=times,dsm_dir=view,output_dir=str(OUT/'parts'),cache_dir=str(CACHE),
                     max_pixels_per_request=120,artifact_budget_bytes=5*1024**3)
    write_region(plan,OUT/'requests')
    assert len(plan['sidecar']['partition'])==2
    batch=v2.plan_batch(**plan['batches'][0])
    assert sum(t['kind']=='horizon' for t in batch.definition['tasks'])==2
    save('real-plan.json',plan['sidecar'])
    state=OUT/'state'
    batch_id=v2.submit_batch(batch,state_dir=state)
    start=time.monotonic()
    result=v2.run_batch(batch_id,state_dir=state)
    save('v2-result.json',dict(result=result,elapsed_seconds=time.monotonic()-start))
    assert result['state']=='SUCCEEDED',result
    single=v1.plan_shade(mode='custom',bounds=plan['sidecar']['requested_bounds'],instants=times,
                         dsm_dir=view,output_dir=OUT/'single',cache_dir=CACHE)
    start=time.monotonic()
    baseline=v1.run_shade(single)
    evidence=[]
    for i,instant in enumerate(single.request.instants):
        shade,quality,transform=read_logical_window(state/f'{batch_id}.logical_mosaic.json',
                            utc_time=instant.utc,bounds=single.grid.bounds())
        for field,actual in [('raster',shade),('quality_raster',quality)]:
            with rasterio.open(baseline.frames[i][field]) as ds:
                assert np.array_equal(actual,ds.read(1))
                assert transform==ds.transform
        evidence.append(dict(instant=instant.utc,shade_equal=True,quality_equal=True,transform_equal=True,
                             shape=shade.shape,shade_counts=dict(zip(*np.unique(shade,return_counts=True))),
                             quality_counts=dict(zip(*np.unique(quality,return_counts=True)))))
    # Convert NumPy histogram keys for strict JSON.
    for row in evidence:
        for key in ('shade_counts','quality_counts'):
            row[key]={str(k):int(v) for k,v in row[key].items()}
    save('real-equality.json',dict(frames=evidence,baseline_jobs=baseline.jobs,
                                 v1_elapsed_seconds=time.monotonic()-start,batch_id=batch_id))


def generated_bytes():
    roots=[OUT,CACHE,ROOT/'docs/region']
    return sum(p.stat().st_size for root in roots if root.exists() for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def supervise():
    if OUT.exists(): raise RuntimeError('Use a fresh validation directory; evidence is immutable')
    started=time.monotonic()
    ledger=dict(ceiling_seconds=1200,ceiling_memory_bytes=8*1024**3,ceiling_artifact_bytes=5*1024**3,
                status='RUNNING',wall_seconds=0,peak_tree_rss_bytes=0,generated_bytes=0,
                scope='entire real exercise including catalogue selection, planning, V2 run, V1 run and equality checks; read-only initial full-catalogue inspection excluded')
    save('ledger.json',ledger)
    with (DOC/'real-run.txt').open('w') as log:
        proc=subprocess.Popen([sys.executable,__file__,'--child'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        tracked=psutil.Process(proc.pid)
        while proc.poll() is None:
            ledger['wall_seconds']=time.monotonic()-started
            try:
                rss=sum(p.memory_info().rss for p in [tracked]+tracked.children(recursive=True) if p.is_running())
                ledger['peak_tree_rss_bytes']=max(ledger['peak_tree_rss_bytes'],rss)
            except psutil.Error: pass
            ledger['generated_bytes']=generated_bytes()
            if (ledger['wall_seconds']>1180 or ledger['peak_tree_rss_bytes']>7.5*1024**3
                    or ledger['generated_bytes']>4.8*1024**3):
                ledger['status']='BLOCKED: resource watchdog stopped before contract ceiling'
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL); proc.wait()
                break
            save('ledger.json',ledger)
            time.sleep(.5)
    ledger['wall_seconds']=time.monotonic()-started
    ledger['generated_bytes']=generated_bytes()
    ledger['exit_code']=proc.returncode
    if ledger['status']=='RUNNING': ledger['status']='SUCCEEDED' if proc.returncode==0 else 'BLOCKED: real exercise failed'
    save('ledger.json',ledger)
    print(json.dumps(ledger,indent=2))
    return proc.returncode


if __name__=='__main__':
    if '--child' in sys.argv: work()
    else: sys.exit(supervise())
