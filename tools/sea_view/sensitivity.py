"""Four explicitly diagnostic variants on one authorized Cheung Chau tile."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

from src import v2
from tools.sea_view.build import build_view,SCOPES
from tools.sea_view.checks import ROOT,EVIDENCE
from tools.sea_view.helpers import read_manifest


def run():
    base=ROOT/'outputs/sea_dev_cheung_chau/combined/result_index.json'
    raw=ROOT/'outputs/v2_daylight_cheungchau_20261009/combined/result_index.json'
    baseline=json.loads(base.read_text());original=json.loads(raw.read_text())
    view=Path(json.loads((EVIDENCE/'views.json').read_text())['cheung_chau']['path'])
    name=SCOPES['cheung_chau'][0]
    with rasterio.open(view/'surface'/name) as ds: surface=ds.read(1);bounds=ds.bounds
    t=baseline['grid']['transform'];c=round((bounds.left-t[2])/.5);r=round((t[5]-bounds.top)/.5)
    window=Window(c,r,surface.shape[1],surface.shape[0])
    times=['2026-01-07T08:30:00+08:00','2026-01-07T12:30:00+08:00','2026-01-07T15:10:00+08:00']
    report={}
    for height,tolerance,label in [(0.,0.,'h0'),(3.,0.,'h3'),(1.6,2.5,'band2_5'),(1.6,5.,'band5')]:
        variant=build_view('cheung_chau',height=height,tolerance=tolerance,diagnostic=True)
        manifest=read_manifest(variant);assert manifest['diagnostic']
        output=ROOT/f'outputs/sea_dev_diagnostic_{label}'
        request=dict(id=label,tile=name,instants=times,direction_method='nearest5',dsm_dir=str(variant/'tiles'),
                     cache_dir=str(ROOT/'data/processed/shade_v1'/('sea_fill_v1_diagnostic_'+variant.name)),
                     output_dir=str(output/'result'))
        plan=v2.plan_batch([request],workers=1)
        batch=v2.submit_batch(plan,state_dir=output/'state')
        result=v2.run_batch(batch,state_dir=output/'state')
        assert result['state']=='SUCCEEDED',result['failures']
        index=json.loads((output/'result/result_index.json').read_text());rows=[]
        for frame in index['frames']:
            prior=next(f for f in baseline['frames'] if f['utc_time']==frame['utc_time'])
            rawframe=next(f for f in original['frames'] if f['utc_time']==frame['utc_time'])
            with rasterio.open(prior['raster']) as ds:old=ds.read(1,window=window)
            with rasterio.open(rawframe['quality_raster']) as ds:q=ds.read(1,window=window)
            with rasterio.open(frame['raster']) as ds:new=ds.read(1)
            rows.append(dict(utc=frame['utc_time'],land_label_changes=int(((surface==0)&(old!=new)).sum()),
                        sea_label_changes=int(((surface==1)&(old!=new)).sum()),
                        former_quality2_strict={str(k):int(((surface==0)&(q==2)&(old==k)).sum()) for k in (0,1,255)},
                        former_quality2_variant={str(k):int(((surface==0)&(q==2)&(new==k)).sum()) for k in (0,1,255)}))
        report[label]=dict(diagnostic=True,height=height,tolerance=tolerance,view=str(variant),view_id=variant.name,
                           target=name,frames=rows,result_metrics=result['metrics'])
        (EVIDENCE/'sensitivity.json').write_text(json.dumps(report,indent=2)+'\n')
        print('diagnostic',label,'complete',flush=True)
    return report


if __name__=='__main__': run()
