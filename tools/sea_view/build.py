"""Build only the two authorized scoped DSM views (and Cheung Chau diagnostics)."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import time

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy.ndimage import distance_transform_edt

from src import v1
from src.spatial import intersects,inventory
from tools.sea_view.checks import ROOT,RAW,VECTOR,metadata
from tools.sea_view.extract import digest
from tools.sea_view.masks import Coastline,fill_mask

SCOPES={
 'cheung_chau':['14NW19B(e820n807,e821n808).tif','14NW20A(e821n807,e821n808).tif',
               '14NW19D(e820n807,e821n807).tif','14NW20C(e821n807,e821n807).tif'],
 'central':['11SW8D(e833n815,e834n816).tif','11SW9C(e834n815,e835n816).tif',
            '11SW13B(e833n815,e834n815).tif','11SW14A(e834n815,e835n815).tif']}


def identity(manifest):
    body={k:v for k,v in manifest.items() if k not in ('view_id','created_at')}
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def classify_surface(values,sea,height=1.6):
    fill=fill_mask(values,sea)
    result=values.copy();result[fill]=np.float32(height)
    surface=np.where(np.isfinite(values) & (values!=-9999),0,255).astype(np.uint8)
    surface[fill]=1
    return result,surface,fill


def synthetic_cells(targets,records):
    first=targets[0];dx=first['width']*.5;dy=first['height']*.5
    x0,y0=first['bounds'][:2]
    halos=[(r['bounds'][0]-1000,r['bounds'][1]-1000,r['bounds'][2]+1000,r['bounds'][3]+1000) for r in targets]
    selected=[r for r in records if any(intersects(r['bounds'],h) for h in halos)]
    if any((r['width'],r['height'],r['crs'])!=(first['width'],first['height'],first['crs']) for r in selected):
        raise ValueError('Scoped native dimensions/CRS are inconsistent')
    cells=set()
    for l,b,r,t in halos:
        cells.update((ix,iy) for ix in range(math.floor((l-x0)/dx),math.ceil((r-x0)/dx))
                     for iy in range(math.floor((b-y0)/dy),math.ceil((t-y0)/dy)))
    missing=[]
    for ix,iy in sorted(cells):
        l=x0+ix*dx;b=y0+iy*dy;bounds=(l,b,l+dx,b+dy)
        if any(intersects(bounds,r['bounds']) for r in selected): continue
        name=f'SEA_E{round(l)}_N{round(b+dy)}.tif'
        if any(Path(r['path']).name==name for r in records): raise ValueError('Synthetic name collision')
        missing.append(dict(path=name,width=first['width'],height=first['height'],bounds=bounds,
                            transform=(.5,0,l,0,-.5,b+dy),crs=first['crs'],nodata=first['nodata']))
    return selected,missing


def sea_for_tile(coast,rec,tolerance):
    shape=(rec['height'],rec['width']);transform=Affine(*rec['transform'])
    if tolerance==0: return coast.masks(shape,transform)
    pad=math.ceil(tolerance/.5)+1
    sea,land=coast.masks((shape[0]+2*pad,shape[1]+2*pad),transform*Affine.translation(-pad,-pad))
    if sea.any(): sea|=land & (distance_transform_edt(~sea,sampling=.5)<=tolerance)
    return sea[pad:-pad,pad:-pad],land[pad:-pad,pad:-pad]


def write_raster(path,array,rec,surface=False):
    with rasterio.open(path,'w',driver='GTiff',width=rec['width'],height=rec['height'],count=1,
                       dtype='uint8' if surface else 'float32',crs=rec['crs'],transform=Affine(*rec['transform']),
                       nodata=255 if surface else rec['nodata'],compress='deflate',predictor=1 if surface else 3,
                       zlevel=6,tiled=True,blockxsize=256,blockysize=256,num_threads=1) as ds:
        ds.write(array,1)


def build_records(scope,targets,records,coast,output_root,staging_root,*,height=1.6,tolerance=0,diagnostic=False):
    selected,missing=synthetic_cells(targets,records)
    staging_root=Path(staging_root);staging_root.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='view_',dir=staging_root))
    (stage/'tiles').mkdir();(stage/'surface').mkdir()
    rows=[]
    try:
        for synthetic,rec in [(False,r) for r in selected]+[(True,r) for r in missing]:
            name=Path(rec['path']).name
            if rec['nodata']!=-9999: raise ValueError('Expected native -9999 NoData for this frozen view')
            sea,land=sea_for_tile(coast,rec,tolerance)
            if synthetic:
                values=np.full((rec['height'],rec['width']),-9999,np.float32)
                source_sha=None
            else:
                with rasterio.open(rec['path']) as ds:
                    if ds.dtypes!=('float32',): raise ValueError('Expected native float32 DSM')
                    values=ds.read(1)
                source_sha=digest(rec['path'])
            filled,surface,mask=classify_surface(values,sea,height)
            if synthetic and not mask.any(): continue
            destination=stage/'tiles'/name
            if not synthetic and not mask.any(): shutil.copyfile(rec['path'],destination)
            else: write_raster(destination,filled,rec)
            write_raster(stage/'surface'/name,surface,rec,surface=True)
            with rasterio.open(destination) as ds:
                check=ds.read(1)
                assert np.array_equal(check.view(np.uint32)[~mask],values.view(np.uint32)[~mask])
                assert np.all(check[mask]==np.float32(height))
                assert ds.transform==Affine(*rec['transform']) and ds.crs==rasterio.crs.CRS.from_string(rec['crs'])
                assert ds.nodata==rec['nodata'] and ds.shape==values.shape and ds.dtypes==('float32',)
            assert not np.any(mask & np.isfinite(values) & (values!=-9999))
            if tolerance==0: assert not np.any(mask & land)
            rows.append(dict(name=name,source_sha256=source_sha,output_sha256=digest(destination),
                             surface_sha256=digest(stage/'surface'/name),sea_fill_pixels=int(mask.sum()),
                             land_nodata_pixels=int(((~np.isfinite(values)|(values==-9999)) & land).sum()),
                             synthetic=synthetic,transform=rec['transform'],width=rec['width'],height=rec['height'],
                             nodata=rec['nodata'],crs=rec['crs'],nonfill_bit_identical=True))
        # Admission uses the real accepted engine and full new view catalogue.
        v1.index_sources(stage/'tiles')
        manifest=dict(schema='shade-watch-sea-view-1.0',policy='SW-SEA-DIAGNOSTIC-1.0' if diagnostic else 'SW-SEA-POLICY-1.0',height_m_hkpd=height,
                      stored_float32_height=float(np.float32(height)),tolerance_m=tolerance,diagnostic=diagnostic,
                      scope=scope,targets=[Path(t['path']).name for t in targets],
                      map_identity=coast.manifest,source_catalogue=[dict(name=Path(r['path']).name,sha256=digest(r['path'])) for r in selected],
                      rasterization='rasterio.features.rasterize all_touched=False; SEF minus LAF; polygon holes honored',
                      diagnostic_tolerance_rule='Euclidean native-centre distance from strict sea, extending into LAF only' if tolerance else None,
                      versions=dict(rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__,numpy=np.__version__),
                      compression='DEFLATE level 6; tiled 256; float predictor 3 / uint8 predictor 1; one thread',tiles=rows)
        manifest['view_id']=identity(manifest)
        output=Path(output_root)/manifest['view_id']
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists():
            prior=json.loads((output/'manifest.json').read_text())
            if prior!=json.loads(json.dumps(manifest)): raise ValueError('Rebuilt manifest differs')
            for row in rows:
                for folder,key in [('tiles','output_sha256'),('surface','surface_sha256')]:
                    if digest(output/folder/row['name'])!=row[key]: raise ValueError('Rebuilt file hash differs')
            shutil.rmtree(stage)
        else: stage.rename(output)
        return output
    except BaseException:
        shutil.rmtree(stage)
        raise


def build_view(scope,*,height=1.6,tolerance=0,diagnostic=False):
    scan=json.loads((ROOT/'docs/sea/evidence/territory-scan.json').read_text())
    if scan.get('status')!='PASS' or not scan.get('elevation_gate_pass'): raise ValueError('S06 gate has not passed')
    if scope not in SCOPES: raise ValueError('Only Cheung Chau and Central scopes are authorized')
    if diagnostic:
        if scope!='cheung_chau' or (height,tolerance) not in ((0,0),(3,0),(1.6,2.5),(1.6,5)):
            raise ValueError('Unauthorized sensitivity variant')
    elif height!=1.6 or tolerance!=0: raise ValueError('Frozen height/tolerance cannot be changed')
    records=metadata();names=SCOPES[scope][:1] if diagnostic else SCOPES[scope]
    targets=[next(r for r in records if Path(r['path']).name==name) for name in names]
    out=ROOT/'data/processed/dsm_views/sea_fill_v1'
    if diagnostic: out=out/'diagnostic'
    return build_records(scope,targets,records,Coastline(VECTOR),out,ROOT/'outputs/sea_dev_build',
                         height=height,tolerance=tolerance,diagnostic=diagnostic)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scope',choices=SCOPES)
    p.add_argument('--height',type=float,default=1.6);p.add_argument('--tolerance',type=float,default=0)
    p.add_argument('--diagnostic',action='store_true');a=p.parse_args()
    print(build_view(a.scope,height=a.height,tolerance=a.tolerance,diagnostic=a.diagnostic))
