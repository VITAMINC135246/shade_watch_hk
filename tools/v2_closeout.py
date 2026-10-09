"""Bounded V2 regression against the newly supplied DSM; never a territory run."""
from pathlib import Path
import argparse, sys, json, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import rasterio
from src import v1, v2
from src.spatial import intersects
from src.v1_cache import atomic_json
from src.v2_worker import read_logical_window

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/v2_closeout_20261008'
NAMES = ['11NE10B(e844n822,e845n822).tif', '11NE10D(e844n821,e845n822).tif']

def main():
    evidence = OUT/'evidence'
    evidence.mkdir(parents=True,exist_ok=True)
    if (evidence/'new_data_result.json').exists():
        raise SystemExit('Evidence already exists; preserve it and use a new campaign namespace.')
    if not (evidence/'data_headers.json').exists():
        rows=[]
        for file in sorted((ROOT/'data/raw/dsm/2020/D12.DSM.TIFF').glob('*.tif')):
            with rasterio.open(file) as ds:
                rows.append(dict(path=str(file.relative_to(ROOT)),name=file.name,bytes=file.stat().st_size,width=ds.width,height=ds.height,crs=str(ds.crs),transform=list(ds.transform)[:6],bounds=list(ds.bounds),nodata=ds.nodata))
        atomic_json(evidence/'data_headers.json',dict(rows=rows,count=len(rows),scope='Header inventory only'))
    headers = json.loads((evidence/'data_headers.json').read_text())['rows']
    targets = [r for r in headers if r['name'] in NAMES]
    assert len(targets) == 2
    supports = [r for r in headers if any(intersects(r['bounds'], [t['bounds'][0]-1000,t['bounds'][1]-1000,t['bounds'][2]+1000,t['bounds'][3]+1000]) for t in targets)]
    raw = OUT/'source_view'; raw.mkdir(exist_ok=True)
    for rec in supports:
        p = ROOT/rec['path']
        for source in [p, p.with_suffix('.tfw'), Path(str(p)+'.aux.xml')]:
            if source.exists():
                link=raw/source.name
                if not link.exists(): link.symlink_to(source)
    times = ['2026-12-17T09:43:29+08:00','2027-03-23T15:21:41+08:00']
    atomic_json(evidence/'new_data_manifest.json',dict(targets=NAMES,source_files=[r['path'] for r in supports],instants=times,
        expected='Both native tiles equal the combined raster and logical view in shade, quality, transform; unchanged V1 science',
        budgets=dict(real_wall_seconds=1200,memory_bytes=12*1024**3,new_bytes=2*1024**3)))
    base=dict(dsm_dir=str(raw),instants=times,cache_dir='data/processed/shade_v1/'+OUT.name)
    requests=[dict(base,id=f'tile{i}',tile=n,output_dir=str(OUT/f'tile{i}')) for i,n in enumerate(NAMES)]
    requests.append(dict(base,id='combined',tiles=NAMES,output_dir=str(OUT/'combined')))
    plan=v2.plan_batch(requests,workers=1,logical_mosaic=True,statistics=True,artifact_budget_bytes=2*1024**3)
    atomic_json(evidence/'new_data_prediction.json',plan.to_dict())
    bid=v2.submit_batch(plan,state_dir=OUT/'state'); start=time.perf_counter()
    result=v2.run_batch(bid,state_dir=OUT/'state'); elapsed=time.perf_counter()-start
    assert result['state']=='SUCCEEDED',result
    assert elapsed<=1200
    checks=[]
    combined=json.loads((OUT/'combined/result_index.json').read_text())
    for i,frame in enumerate(combined['frames']):
        for role in ('raster','quality_raster'):
            with rasterio.open(frame[role]) as ds: full=ds.read(1); transform=ds.transform
            pieces=[]
            for j in range(2):
                index=json.loads((OUT/f'tile{j}/result_index.json').read_text())
                with rasterio.open(index['frames'][i][role]) as ds:
                    pieces.append(ds.read(1))
                    assert ds.transform == transform * rasterio.Affine.translation(0,j*1200)
            assert np.array_equal(full,np.vstack(pieces))
        grid=plan.definition['requests']['combined']['grid']; x,y=grid['transform'][2],grid['transform'][5]
        bounds=(x+15,y-602,x+25,y-598)
        shade,quality,tr=read_logical_window(OUT/'state'/f'{bid}.logical_mosaic.json',utc_time=frame['utc_time'],bounds=bounds)
        for arr,role in [(shade,'raster'),(quality,'quality_raster')]:
            with rasterio.open(frame[role]) as ds: assert np.array_equal(arr,ds.read(1,window=rasterio.windows.from_bounds(*bounds,ds.transform)))
        checks.append(dict(utc=frame['utc_time'],native_combined_logical_identical=True,counts=frame['counts'],quality_counts=frame['quality_counts']))
    # Separate inherited V1 API, same supplied sources and directions; warm cache.
    reference=v1.run_shade(v1.plan_shade(**base,tiles=NAMES,output_dir=str(OUT/'v1_reference')))
    for a,b in zip(combined['frames'],reference.frames):
        for role in ('raster','quality_raster'):
            with rasterio.open(a[role]) as x,rasterio.open(b[role]) as y:
                assert np.array_equal(x.read(1),y.read(1)) and x.transform==y.transform
    total=sum(p.stat().st_size for root in (OUT/'state',OUT/'tile0',OUT/'tile1',OUT/'combined',OUT/'v1_reference',ROOT/base['cache_dir']) for p in root.rglob('*') if p.is_file())
    atomic_json(evidence/'new_data_result.json',dict(result=result,wall_seconds=elapsed,total_with_reference_seconds=time.perf_counter()-start,generated_bytes=total,support_count=len(supports),checks=checks,v1_equal=True,scope='V2 supplementary consistency only; no V3 or full-territory computation'))
    print(json.dumps(dict(batch=bid,wall_seconds=elapsed,supports=len(supports),checks=checks)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',default='v2_closeout_20261008')
    args=parser.parse_args()
    if not args.campaign or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in args.campaign):
        parser.error('Campaign must be a safe directory name')
    OUT=ROOT/'outputs'/args.campaign
    main()
