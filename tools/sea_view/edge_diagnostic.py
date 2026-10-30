"""Explain reference-count differences using a conventional PIL edge burn.

PIL is diagnostic only. Policy masks always come from rasterio centre rasterization.
"""
import json
import resource
import time

import numpy as np
from PIL import Image,ImageDraw
from rasterio.transform import from_origin

from src.spatial import Grid,intersects,inventory,read_window
from tools.sea_view.checks import metadata,VECTOR,EVIDENCE
from tools.sea_view.masks import Coastline


def run():
    started=time.monotonic()
    bounds=(819250,806200,822750,809400)
    w,h=7000,6400
    grid=Grid(w,h,tuple(from_origin(bounds[0],bounds[3],.5,.5))[:6],'EPSG:2326')
    coast=Coastline(VECTOR)
    recs=inventory([r['path'] for r in metadata() if intersects(bounds,r['bounds'])])
    values=read_window(recs,grid,(0,0,w,h));nodata=~np.isfinite(values)
    sea,land=coast.masks((h,w),grid.affine)
    burns={}
    for code in ('LAF','SEF'):
        union=np.zeros((h,w),bool)
        for feature in coast.features:
            if feature['properties']['code']!=code or not intersects(bounds,feature['bbox']): continue
            geom=feature['geometry']
            polygons=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
            for rings in polygons:
                image=Image.new('1',(w,h),0);draw=ImageDraw.Draw(image)
                for i,ring in enumerate(rings):
                    xy=[((p[0]-bounds[0])/.5,(bounds[3]-p[1])/.5) for p in ring]
                    draw.polygon(xy,fill=1 if i==0 else 0)
                union|=np.asarray(image)
        burns[code]=union
    psea=burns['SEF'] & ~burns['LAF'];pland=burns['LAF']
    actual=dict(nodata=int(nodata.sum()),nodata_sea=int((nodata & psea).sum()),
                nodata_land=int((nodata & pland).sum()),valid_sea=int((~nodata & psea).sum()))
    samples=[]
    for label,mask in [('nodata_PIL_land_rasterio_sea',nodata & pland & sea),
                       ('valid_PIL_land_rasterio_sea',~nodata & pland & sea),
                       ('nodata_rasterio_land_PIL_sea',nodata & land & psea)]:
        rr,cc=np.nonzero(mask)
        for k in np.linspace(0,len(rr)-1,min(20,len(rr)),dtype=int):
            r,c=int(rr[k]),int(cc[k])
            samples.append(dict(group=label,row=r,col=c,x=bounds[0]+(c+.5)*.5,y=bounds[3]-(r+.5)*.5,
                                dsm=None if nodata[r,c] else float(values[r,c]),
                                rasterio_land=bool(land[r,c]),rasterio_sea=bool(sea[r,c]),
                                pil_land=bool(pland[r,c]),pil_sea=bool(psea[r,c])))
    result=dict(method='PIL ImageDraw polygon vertices at pixel-edge coordinates, exterior fill then holes cleared, polygon masks unioned; diagnostic only',
                pil_counts=actual,land_disagreement_pixels=int((land!=pland).sum()),samples=samples,
                wall_seconds=time.monotonic()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (EVIDENCE/'edge-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))


if __name__=='__main__': run()
