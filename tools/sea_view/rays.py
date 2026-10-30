"""S09 sampled direct-window reference, separate from cache/output composition."""
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from src import v1
from src.v1_cache import diagnostic_horizon
from tools.sea_view.checks import ROOT,EVIDENCE
from tools.sea_view.compare import arrays,bounds_for_grid
from tools.sea_view.helpers import read_manifest


def run():
    view=Path(json.loads((EVIDENCE/'views.json').read_text())['cheung_chau']['path'])
    manifest=read_manifest(view);records=v1.index_sources(view/'tiles')
    index=json.loads((ROOT/'outputs/sea_dev_cheung_chau/combined/result_index.json').read_text())
    selected=[f for f in index['frames'] if f['local_time'][11:16] in ('08:30','12:30','15:10')]
    assert len(selected)==3
    bounds=bounds_for_grid(index['grid']);results=[];rng=np.random.default_rng(20261030)
    for frame in selected:
        shade,quality=arrays(frame);samples=[]
        for solar in frame['solar_by_tile']:
            rec=next(r for r in records if Path(r['path']).name==solar['source_name'])
            with rasterio.open(view/'surface'/solar['source_name']) as ds: surface=ds.read(1)
            with rasterio.open(view/'tiles'/solar['source_name']) as ds: heights=ds.read(1)
            water=surface==1
            near=water & binary_dilation((surface==0)&(heights>=10),iterations=16)
            pool=np.argwhere(near if near.any() else water)
            if not len(pool): continue
            rowoff=round((bounds[3]-rec['bounds'][3])/.5);coloff=round((rec['bounds'][0]-bounds[0])/.5)
            seen=set()
            # Clustered 12x12 diagnostic windows limit reads, while preserving
            # canonical reference rays and selecting >=50 distinct water targets per tile.
            for choice in rng.permutation(len(pool)):
                rr,cc=map(int,pool[choice]);r=max(0,min(rec['height']-12,rr-6));c=max(0,min(rec['width']-12,cc-6))
                horizon,support,_=diagnostic_horizon(records,rec,(c,r,12,12),solar['direction_deg'])
                expected,flags=v1.classify(horizon,support.astype(bool),np.isfinite(horizon),
                                          solar['apparent_elevation_deg'],solar['threshold_deg'])
                candidates=np.argwhere(water[r:r+12,c:c+12])
                # Prioritize the near-structure pixels inside each checked window.
                candidates=sorted(candidates.tolist(),key=lambda p:not near[r+p[0],c+p[1]])
                for pr,pc in candidates:
                    y,x=r+pr,c+pc
                    if (y,x) in seen: continue
                    seen.add((y,x))
                    eq=abs(float(horizon[pr,pc])-solar['apparent_elevation_deg'])<=1e-4
                    actual=int(shade[rowoff+y,coloff+x]);reference=int(expected[pr,pc])
                    samples.append(dict(tile=solar['source_name'],row=y,col=x,near_structure=bool(near[y,x]),
                                label=actual,reference_label=reference,quality=int(quality[rowoff+y,coloff+x]),
                                reference_quality=int(flags[pr,pc]),equality_neighbourhood=eq,
                                matches=actual==reference))
                    if len(seen)>=50: break
                if len(seen)>=50: break
        result=dict(utc=frame['utc_time'],n=len(samples),near_structure_samples=sum(s['near_structure'] for s in samples),
                    mismatches_outside_equality=sum(not s['matches'] and not s['equality_neighbourhood'] for s in samples),samples=samples)
        results.append(result)
    passed=all(r['n']>=200 and r['near_structure_samples']>0 and r['mismatches_outside_equality']==0 for r in results)
    report=dict(method='diagnostic_horizon on independent canonical 12x12 windows, unchanged classifier, exact owning-tile nearest5 direction and threshold; no cache values used as reference',
                numerical_consistency_only=True,frames=results,passed=passed)
    (EVIDENCE/'sea-ray-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    assert passed,'S09 direct-window consistency failed'
    print('S09 passed',[(r['n'],r['near_structure_samples']) for r in results],flush=True)


if __name__=='__main__': run()
