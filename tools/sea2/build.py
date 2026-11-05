"""One explicit, reproducible territory surface build; never computes shade."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import sys
import tempfile
import time

import numpy as np
import rasterio
import scipy

from src import v1
from tools.shade_map.common import atomic_json, digest, identity
from tools.shade_map.config import InvalidInput, machine_config
from . import POLICY, RULE_VERSION
from .catalogue import Catalogue, header_inventory
from .profile import load_profile, validate_profile
from .rule import Components, CODES, classify_points, counts, label, missing
from .view import manifest_identity, read_manifest, verify_view


def write_raster(path,data,transform,crs,nodata,*,source_profile=None,tags=None):
    options=dict(source_profile or {})
    options.update(driver='GTiff',width=data.shape[1],height=data.shape[0],count=1,
                   dtype=str(data.dtype),transform=transform,crs=crs,nodata=nodata,
                   tiled=True,blockxsize=256,blockysize=256,compress='DEFLATE',
                   predictor=3 if data.dtype==np.float32 else 1,zlevel=6,num_threads=1)
    with rasterio.open(path,'w',**options) as dst:
        dst.write(data,1)
        if tags: dst.update_tags(**tags)


def assert_fill(raw_path,output_path,surface,h_sea):
    with rasterio.open(raw_path) as src,rasterio.open(output_path) as dst:
        if (src.transform,src.crs,src.shape,src.dtypes,src.nodata)!=(dst.transform,dst.crs,dst.shape,dst.dtypes,dst.nodata):
            raise RuntimeError('Filled tile metadata changed')
        a,b=src.read(1),dst.read(1)
        water=surface==1
        if not np.all(b[water]==np.float32(h_sea)) or not np.array_equal(a.view(np.uint32)[~water],b.view(np.uint32)[~water]):
            raise RuntimeError('Filled tile changed non-water bits or sea height')


def analyse(catalogue,profile,*,progress=None,guard=None):
    components=Components(); shores={}
    keys=list(catalogue.keys())
    for i,key in enumerate(keys):
        x,y,w,h=catalogue.window(key)
        a,shore_points=catalogue.data_and_shores(key,profile)
        components.add(key,missing(a),west=key[0]==catalogue.xs.start,
                       east=key[0]==catalogue.xs.stop-1,south=key[1]==catalogue.ys.start,
                       north=key[1]==catalogue.ys.stop-1)
        shores[key]=shore_points
        if guard: guard()
        if progress and (i%100==0 or i==len(keys)-1): progress('connectivity',i+1,len(keys))
    return components,shores


def classify_cell(catalogue,key,profile,components,shores):
    window=catalogue.window(key); x,y,w,h=window
    a=catalogue.read(window)
    bad=missing(a); labels,_=label(bad)
    opened=components.open_mask(key,labels)
    low,high=catalogue.points_near(key,shores,profile['max_shore_distance_m']+profile['shore_preference_m'])
    return classify_points(bad,opened,low,high,profile,x0=x,y0=y,resolution=catalogue.res,
                           supplied=key in catalogue.tiles,origin=(catalogue.e0,catalogue.n0),
                           pixel_offset=catalogue.pixel_offset(key))


@contextmanager
def build_lock(directory,profile_id):
    path=directory/('build-'+profile_id+'.lock')
    with path.open('a') as stream:
        try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise InvalidInput('sea view: another build owns this profile') from exc
        try: yield
        finally: fcntl.flock(stream,fcntl.LOCK_UN)


def build(machine='config/machine.local.json',*,profile=None):
    machine=machine_config(machine)
    profile=load_profile(machine) if profile is None else validate_profile(profile)
    root=v1.ROOT/'data/processed/dsm_views/sea_fill_v2'
    if root.is_symlink(): raise InvalidInput('sea view: output namespace cannot be a symlink')
    root.mkdir(parents=True,exist_ok=True)
    with build_lock(root,profile['profile_id']):
        return _build(machine,profile,root)


def _build(machine,profile,root):
    started=time.monotonic(); wall_started=time.time()
    def elapsed(): return max(time.monotonic()-started,time.time()-wall_started)
    def guard():
        if elapsed()>3600: raise RuntimeError('view-build 60-minute wall budget exhausted')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>12*1024**3: raise RuntimeError('view-build 12 GiB memory budget exhausted')
    def progress(phase,n,total):
        print(f'sea2 {phase}: {n}/{total}',file=sys.stderr,flush=True)
    inventory=header_inventory(machine['dsm_dir'])
    catalogue=Catalogue(machine['dsm_dir'],profile)
    source_hashes={item['name']:digest(catalogue.directory/item['name']) for item in inventory}
    guard()
    components,shores=analyse(catalogue,profile,progress=progress,guard=guard)
    stage=Path(tempfile.mkdtemp(prefix='.build-',dir=root))
    (stage/'tiles').mkdir(); (stage/'surface').mkdir()
    try:
        cells=[]; tiles=[]; totals={str(c):0 for c in CODES}; auxiliary={}
        keys=list(catalogue.keys())
        for i,key in enumerate(keys):
            surface=classify_cell(catalogue,key,profile,components,shores)
            window=catalogue.window(key); x,y,w,h=window
            name=catalogue.name(key); surface_name=name+'.tif'
            c=counts(surface)
            for code,n in c.items(): totals[code]+=n
            write_raster(stage/'surface'/surface_name,surface,catalogue.transform(window),catalogue.crs,None)
            raw=catalogue.tiles.get(key)
            rec=dict(id=name,key=list(key),bounds=catalogue.bounds(window),
                     native_bounds=catalogue.bounds(catalogue.window(key,clip=False)),
                     surface_name=surface_name,surface_sha256=digest(stage/'surface'/surface_name),
                     counts=c,supplied=raw is not None,source_sha256=source_hashes[raw['name']] if raw else None,
                     tile_name=None,synthetic=False)
            if raw is not None:
                output=stage/'tiles'/raw['name']
                if c['1']:
                    with rasterio.open(raw['path']) as ds:
                        data=ds.read(1); data[surface==1]=np.float32(profile['h_sea_m'])
                        write_raster(output,data,ds.transform,ds.crs,ds.nodata,source_profile=ds.profile,tags=ds.tags())
                    assert_fill(raw['path'],output,surface,profile['h_sea_m'])
                    output_hash=digest(output)
                else:
                    output.symlink_to(raw['path']); output_hash=source_hashes[raw['name']]
                for aux in raw['auxiliary']:
                    if aux not in auxiliary:
                        (stage/'tiles'/aux).symlink_to(catalogue.directory/aux)
                        auxiliary[aux]=source_hashes[aux]
                rec.update(tile_name=raw['name'],output_sha256=output_hash)
                tiles.append(dict(name=raw['name'],cell=name,source_sha256=source_hashes[raw['name']],
                                  output_sha256=output_hash,counts=c,synthetic=False,bounds=raw['bounds']))
            elif c['2']:
                filename='SEA_'+name+'.tif'
                full=catalogue.window(key,clip=False)
                data=np.full((catalogue.height,catalogue.width),catalogue.nodata,np.float32)
                row=full[1]+full[3]-(y+h); col=x-full[0]
                target=data[row:row+h,col:col+w]; target[surface==2]=np.float32(profile['h_sea_m'])
                output=stage/'tiles'/filename
                write_raster(output,data,catalogue.transform(full),catalogue.crs,catalogue.nodata)
                output_hash=digest(output)
                rec.update(tile_name=filename,output_sha256=output_hash,synthetic=True)
                tiles.append(dict(name=filename,cell=name,source_sha256=None,output_sha256=output_hash,
                                  counts=c,synthetic=True,bounds=catalogue.bounds(full)))
            cells.append(rec)
            guard()
            if i%100==0 or i==len(keys)-1: progress('surface',i+1,len(keys))
        l,b,r,t=catalogue.domain
        if sum(totals.values())!=(r-l)*(t-b): raise RuntimeError('Territory class totals do not reconcile')
        if header_inventory(machine['dsm_dir'])!=inventory: raise RuntimeError('Raw catalogue changed during build')
        document=dict(schema='sea-view-2.0',policy=POLICY,diagnostic=False,
                      profile=profile,profile_sha256=identity(profile),
                      catalogue=dict(files=source_hashes,identity=identity(source_hashes)),
                      rule_version=RULE_VERSION,
                      versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                                    rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__),
                      grid=dict(origin=[catalogue.e0,catalogue.n0],resolution=catalogue.res,
                                cell_width=catalogue.width,cell_height=catalogue.height,crs=catalogue.crs,
                                nodata=catalogue.nodata,dtype='float32',domain_bounds=catalogue.bounds((l,b,r-l,t-b))),
                      shifted_origin_connectivity_only=catalogue.shifted,
                      cells=cells,tiles=sorted(tiles,key=lambda x:x['name']),auxiliary_outputs=auxiliary,totals=totals)
        document['view_id']=manifest_identity(document)
        atomic_json(stage/'manifest.json',document)
        destination=root/document['view_id']
        reproduced=destination.exists()
        if reproduced:
            old=verify_view(destination)
            if old!=document: raise RuntimeError('Rebuild manifest differs at identical identity')
            # Both independently generated stage and existing output hashes are checked.
            verify_view(stage)
            shutil.rmtree(stage)
        else:
            stage.rename(destination)
        atomic_json(root/f'current-{profile["profile_id"]}.json',
                    dict(schema='sea-view-pointer-2.0',view_id=document['view_id'],profile_id=profile['profile_id'],
                         profile_sha256=document['profile_sha256'],header_inventory=inventory))
        return dict(view_id=document['view_id'],path=str(destination),reproduced=reproduced,
                    cells=len(cells),tiles=len(tiles),synthetic_tiles=sum(t['synthetic'] for t in tiles),
                    totals=totals,wall_seconds=elapsed())
    finally:
        if stage.exists(): shutil.rmtree(stage)
