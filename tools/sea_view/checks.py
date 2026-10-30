"""Bounded development mask/count checks; no shade or view creation."""
import json
import resource
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from rasterio.transform import from_origin

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.spatial import Grid,intersects,inventory,read_window
from tools.sea_view.masks import Coastline,fill_mask

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/dsm/2020/D12.DSM.TIFF'
VECTOR=ROOT/'data/processed/coastline/ib5000_20261012'
EVIDENCE=ROOT/'docs/sea/evidence'


def metadata():
    result=[]
    for p in sorted(RAW.glob('*.tif')):
        with rasterio.open(p) as ds:
            result.append(dict(path=str(p),bounds=tuple(ds.bounds),transform=tuple(ds.transform)[:6],
                               width=ds.width,height=ds.height,crs=ds.crs.to_string(),nodata=ds.nodata))
    return result


def halo():
    start=time.monotonic()
    coast=Coastline(VECTOR)
    bounds=(819250,806200,822750,809400)
    recs=[r for r in metadata() if intersects(bounds,r['bounds'])]
    recs=inventory([r['path'] for r in recs])
    grid=Grid(7000,6400,tuple(from_origin(bounds[0],bounds[3],.5,.5))[:6],'EPSG:2326')
    values=read_window(recs,grid,(0,0,7000,6400))
    sea,land=coast.masks(values.shape,grid.affine)
    nodata=~np.isfinite(values) | (values==-9999)
    actual=dict(nodata=int(nodata.sum()),nodata_sea=int((nodata & sea).sum()),
                nodata_land=int((nodata & land).sum()),valid_sea=int((~nodata & sea).sum()))
    reference=dict(nodata=34647367,nodata_sea=34617537,nodata_land=29830,valid_sea=357470)
    relative={k:(actual[k]-reference[k])/reference[k] for k in actual}
    result=dict(actual=actual,reference=reference,relative_difference=relative,
                within_half_percent=all(abs(d)<=.005 for d in relative.values()),
                scoped_sources=[dict(path=r['path'],sha256=r['sha256']) for r in recs],
                wall_seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (EVIDENCE/'halo-counts.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='scoped_sources'},indent=2))


if __name__=='__main__': halo()
