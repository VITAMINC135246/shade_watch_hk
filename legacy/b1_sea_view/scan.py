"""One bounded read-only territory scan for S06; never writes DSM tiles."""
import hashlib
import json
import math
from pathlib import Path
import resource
import time

import numpy as np
from rasterio.transform import Affine
from scipy.ndimage import binary_dilation

from src.spatial import Grid,intersects,read_window
from tools.sea_view.checks import EVIDENCE,VECTOR,metadata
from tools.sea_view.masks import Coastline,fill_mask


def adjacent_values(values,sea):
    """Return interior valid target heights 8-adjacent to a sea-fill neighbour."""
    fill=fill_mask(values,sea)
    adjacent=binary_dilation(fill,structure=np.ones((3,3),bool))
    valid=np.isfinite(values) & (values!=-9999)
    return values[1:-1,1:-1][(valid & adjacent)[1:-1,1:-1]]


def run():
    path=EVIDENCE/'territory-scan.json'
    if path.exists(): raise RuntimeError('The authorized territory scan has already been attempted')
    started=time.monotonic()
    result=dict(status='RUNNING',tiles_completed=0,synthetic_cells_checked=0,
                wall_seconds=0,peak_rss_bytes=0,ceiling_seconds=1800,
                quantile_method='exact numpy percentile, linear interpolation of float32 samples',
                adjacency='8-neighbour centres on each target native grid, including 1 pixel halo and no-source sea support',
                footprint_accounting='sum of supplied tile footprints; per-tile grids retained')
    def checkpoint():
        result['wall_seconds']=time.monotonic()-started
        result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        if result['wall_seconds']>1740: raise RuntimeError('Scan stopped before 30 minute ceiling')
        if result['peak_rss_bytes']>11*1024**3: raise RuntimeError('Scan stopped before 12 GiB ceiling')
    checkpoint()
    try:
        coast=Coastline(VECTOR)
        records=metadata()
        result['catalogue_metadata_sha256']=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()
        result['catalogue_tiles']=len(records)
        result['map_vector_sha256']=coast.manifest['vector_sha256']
        samples=[]
        neither=coastal=0
        shifted=[]
        for rec in records:
            checkpoint()
            grid=Grid(rec['width'],rec['height'],rec['transform'],rec['crs'])
            bounds=grid.bounds((-1,-1,grid.width+2,grid.height+2))
            deps=[r for r in records if intersects(bounds,r['bounds'])]
            if any(abs(v/.5-round(v/.5))>1e-7 for v in (grid.affine.c,grid.affine.f)):
                shifted.append(rec['path'])
            sea,land=coast.masks((grid.height+2,grid.width+2),grid.local_transform((-1,-1,grid.width+2,grid.height+2)))
            neither+=int((~sea[1:-1,1:-1] & ~land[1:-1,1:-1]).sum())
            if sea.any():
                coastal+=1
                values=read_window(deps,grid,(-1,-1,grid.width+2,grid.height+2))
                selected=adjacent_values(values,sea)
                if selected.size: samples.append(selected.copy())
            result['tiles_completed']+=1
            if result['tiles_completed']%100==0:
                print('scanned',result['tiles_completed'],flush=True)
        joined=np.concatenate(samples) if samples else np.array([],np.float32)
        result.update(coastal_tiles=coastal,n=int(joined.size),
                      neither_class_pixels=neither,neither_class_area_m2=neither*.25,
                      shifted_origins_preserved=shifted)
        if not joined.size: raise ValueError('No shoreline-adjacent valid DSM samples')
        result['quantiles_m']=dict(zip(['p5','p25','p50','p75','p95'],map(float,np.percentile(joined,[5,25,50,75,95]))))
        result['elevation_gate_pass']=1.3<=result['quantiles_m']['p50']<=1.9
        # The frozen gate stops immediately: do not spend further scan resources
        # on synthetic coverage or build any view if the height check fails.
        if not result['elevation_gate_pass']:
            result['status']='FAIL: S06 median outside [1.30,1.90]; policy h remains 1.60'
            return result
        first=records[0]
        dx=first['width']*.5;dy=first['height']*.5
        x0=first['bounds'][0];y0=first['bounds'][1]
        if any(r['width']!=first['width'] or r['height']!=first['height'] for r in records):
            raise ValueError('Cannot derive a single native tile lattice from catalogue dimensions')
        candidates=set()
        for rec in records:
            l,b,r,t=rec['bounds']
            for ix in range(math.floor((l-1000-x0)/dx),math.ceil((r+1000-x0)/dx)):
                for iy in range(math.floor((b-1000-y0)/dy),math.ceil((t+1000-y0)/dy)):
                    candidates.add((ix,iy))
        synthetic=sea_pixels=0
        for ix,iy in sorted(candidates):
            checkpoint()
            l=x0+ix*dx;b=y0+iy*dy
            bounds=(l,b,l+dx,b+dy)
            if any(intersects(bounds,r['bounds']) for r in records): continue
            sea,_=coast.masks((first['height'],first['width']),Affine(.5,0,l,0,-.5,b+dy))
            count=int(sea.sum())
            synthetic+=count>0;sea_pixels+=count
            result['synthetic_cells_checked']+=1
        result.update(synthetic_cells_required=synthetic,synthetic_sea_pixels=sea_pixels,status='PASS')
        return result
    except BaseException as exc:
        result['status']='BLOCKED: '+repr(exc)
        raise
    finally:
        result['wall_seconds']=time.monotonic()-started
        result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__': print(json.dumps(run(),indent=2))
