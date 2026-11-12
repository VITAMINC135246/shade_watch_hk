"""Development land-transition evidence with per-pixel blocker attribution."""
import json
import math
from pathlib import Path

import numpy as np
import rasterio

from src.v1_cache import entry_paths
from tools.sea_view.checks import ROOT,EVIDENCE
from tools.sea_view.helpers import read_manifest,read_surface_window


def arrays(frame):
    with rasterio.open(frame['raster']) as ds,rasterio.open(frame['quality_raster']) as qs:
        return ds.read(1),qs.read(1)


def bounds_for_grid(grid):
    a=grid['transform'];return (a[2],a[5]-grid['height']*.5,a[2]+grid['width']*.5,a[5])


def compare(scope):
    views=json.loads((EVIDENCE/'views.json').read_text());view=Path(views[scope]['path'])
    manifest=read_manifest(view)
    oldpath=ROOT/('outputs/v2_daylight_cheungchau_20261009/combined/result_index.json' if scope=='cheung_chau'
                 else 'outputs/sea_dev_raw_central/combined/result_index.json')
    newpath=ROOT/f'outputs/sea_dev_{scope}/combined/result_index.json'
    old=json.loads(oldpath.read_text());new=json.loads(newpath.read_text())
    bounds=bounds_for_grid(new['grid']);surface,_=read_surface_window(view,bounds)
    assert old['grid']['transform']==new['grid']['transform']
    assert [f['utc_time'] for f in old['frames']]==[f['utc_time'] for f in new['frames']]
    land=surface==0;water=surface==1
    tilemap={t['name']:t for t in manifest['tiles']}
    frames=[];thresholds={};examples=[]
    for before,after in zip(old['frames'],new['frames']):
        oldshade,oldq=arrays(before);shade,q=arrays(after)
        shaded_to_sunlit=int((land & (oldshade==1) & (shade==0)).sum())
        missing_changed=int((land & (oldq==1) & (shade!=255)).sum())
        losses=land & (oldshade==0) & (shade!=0)
        explained=np.zeros(losses.shape,bool)
        reasons=dict(raised_threshold=0,filled_blocker=0)
        for ot,nt in zip(before['solar_by_tile'],after['solar_by_tile']):
            assert ot['source_name']==nt['source_name'] and ot['reference']==nt['reference']
            assert ot['direction_deg']==nt['direction_deg'] and ot['apparent_elevation_deg']==nt['apparent_elevation_deg']
            name=nt['source_name'];rec=tilemap[name]
            col=round((rec['transform'][2]-bounds[0])/.5);row=round((bounds[3]-rec['transform'][5])/.5)
            sl=(slice(row,row+rec['height']),slice(col,col+rec['width']))
            local=losses[sl];elevation=nt['apparent_elevation_deg']
            thresholds[name]=dict(old=ot['threshold_deg'],new=nt['threshold_deg'])
            distant=local & (q[sl]==3) & (nt['threshold_deg']>ot['threshold_deg']) & (elevation<=nt['threshold_deg'])
            explained[sl]|=distant;reasons['raised_threshold']+=int(distant.sum())
            needed=local & ~distant
            if not needed.any(): continue
            cache,_=entry_paths(new['cache_directory'],nt['spatial_key'],nt['direction_deg'])
            with rasterio.open(cache) as ds: horizon,support,distance=ds.read()
            rr,cc=np.nonzero(needed)
            angle=math.radians(nt['direction_deg']);dr=-math.cos(angle);dc=math.sin(angle)
            if abs(dr)<1e-14:dr=0.
            if abs(dc)<1e-14:dc=0.
            absr=round(-rec['transform'][5]/.5)+rr;absc=round(rec['transform'][2]/.5)+cc
            # Reconstruct the exact maximum-blocker sample from cached nominal
            # distances with the engine's canonical parity and ties-to-even rule.
            br=absr+np.rint(absr%2+dr*distance[rr,cc]/.5).astype(np.int64)-absr%2
            bc=absc+np.rint(absc%2+dc*distance[rr,cc]/.5).astype(np.int64)-absc%2
            proven=np.zeros(len(rr),bool)
            for tile in manifest['tiles']:
                r0=round(-tile['transform'][5]/.5);c0=round(tile['transform'][2]/.5)
                hit=(br>=r0)&(br<r0+tile['height'])&(bc>=c0)&(bc<c0+tile['width'])
                if not hit.any():continue
                with rasterio.open(view/'surface'/tile['name']) as ds: classes=ds.read(1)
                proven[hit]=classes[br[hit]-r0,bc[hit]-c0]==1
            proven&=(horizon[rr,cc]>elevation)&(shade[sl][rr,cc]==1)
            explained[sl][rr[proven],cc[proven]]=True
            reasons['filled_blocker']+=int(proven.sum())
            for i in np.flatnonzero(proven)[:3]:
                if len(examples)<60:examples.append(dict(utc=after['utc_time'],tile=name,row=int(rr[i]),col=int(cc[i]),
                    blocker_absolute_row=int(br[i]),blocker_absolute_col=int(bc[i]),distance_m=float(distance[rr[i],cc[i]]),
                    horizon_deg=float(horizon[rr[i],cc[i]]),elevation_deg=elevation))
        unaccounted=int((losses & ~explained).sum())
        frames.append(dict(utc=after['utc_time'],shaded_to_sunlit=shaded_to_sunlit,quality1_land_changed=missing_changed,
                old_quality1_land_pixels=int((land & (oldq==1)).sum()),sunlit_to_non_sunlit=int(losses.sum()),
                explained=reasons,unexplained=unaccounted,
                former_quality2={str(k):int((land & (oldq==2) & (shade==k)).sum()) for k in (0,1,255)},
                water_counts={str(k):int((water & (shade==k)).sum()) for k in (0,1,255)},
                water_fractions={str(k):float((water & (shade==k)).sum()/water.sum()) for k in (0,1,255)}))
    result=dict(scope=scope,frames=frames,thresholds=thresholds,blocker_examples=examples,
                gates_pass=all(r['shaded_to_sunlit']==r['quality1_land_changed']==r['unexplained']==0 for r in frames),
                attribution='Every sunlit loss checked: raised threshold and Quality 3, or exact cached maximum-blocker address resolves to surface class 1 with horizon above Sun.')
    (EVIDENCE/f'{scope}-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['gates_pass'],'Land regression gate failed; stop subsequent stages'
    print(scope,'comparison passed',len(frames),'frames',flush=True)
    return result


if __name__=='__main__':
    import sys
    compare(sys.argv[1])
