"""One explicit, reproducible territory surface build; never computes shade."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import math
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

from shade_watch.engine import v1
from shade_watch.publish.common import atomic_json, digest, identity
from shade_watch.publish.config import InvalidInput, machine_config
from . import POINTER_SCHEMA, POLICY, RULE_VERSION, VIEW_SCHEMA
from .catalogue import Catalogue, header_inventory
from .profile import load_profile, validate_profile
from .rule import Components, CODES, NODATA, classify_points, counts, label, missing
from .view import manifest_identity, verify_view

# This entry point imports these package modules on the build path.
BUILD_MODULES = ('__init__.py', '__main__.py', 'build.py', 'catalogue.py',
                 'profile.py', 'provider.py', 'rule.py', 'view.py')


def build_code_hashes():
    directory = Path(__file__).resolve().parent
    return {'shade_watch/fill/'+name: digest(directory/name) for name in BUILD_MODULES}


def write_raster(path,data,transform,crs,nodata,*,source_profile=None,tags=None):
    options=dict(source_profile or {})
    options.update(driver='GTiff',width=data.shape[1],height=data.shape[0],count=1,
                   dtype=str(data.dtype),transform=transform,crs=crs,nodata=nodata,
                   tiled=True,blockxsize=256,blockysize=256,compress='DEFLATE',
                   predictor=3 if data.dtype==np.float32 else 1,zlevel=4,num_threads=1)
    with rasterio.open(path,'w',**options) as dst:
        dst.write(data,1)
        if tags: dst.update_tags(**tags)


def assert_fill(raw_path,output_path,surface,h_fill):
    with rasterio.open(raw_path) as src,rasterio.open(output_path) as dst:
        same_nodata = src.nodata == dst.nodata or (
            src.nodata is not None and dst.nodata is not None
            and math.isnan(src.nodata) and math.isnan(dst.nodata))
        if (src.transform,src.crs,src.shape,src.dtypes)!=(dst.transform,dst.crs,dst.shape,dst.dtypes) or not same_nodata:
            raise RuntimeError('Filled tile metadata changed')
        raw,filled=src.read(1),dst.read(1)
        bad=missing(raw)
        if not np.array_equal(bad, (surface>=1)&(surface<=4)):
            raise RuntimeError('Surface classes disagree with literal NoData')
        raw_bits,filled_bits=raw.view(np.uint32),filled.view(np.uint32)
        if (not np.all(filled_bits[bad]==np.float32(h_fill).view(np.uint32))
                or not np.array_equal(raw_bits[~bad],filled_bits[~bad])):
            raise RuntimeError('Filled tile changed observed bits or fill height')


def analyse(catalogue,profile,*,progress=None,guard=None):
    components=Components(); shores={}
    keys=list(catalogue.keys())
    for i,key in enumerate(keys):
        a,shore_points=catalogue.data_and_shores(key,profile)
        components.add(key,missing(a),west=key[0]==catalogue.xs.start,
                       east=key[0]==catalogue.xs.stop-1,south=key[1]==catalogue.ys.start,
                       north=key[1]==catalogue.ys.stop-1)
        shores[key]=shore_points
        if guard: guard()
        if progress and (i%100==0 or i==len(keys)-1): progress('connectivity',i+1,len(keys))
    return components,shores


def classify_cell(catalogue,key,profile,components,shores,*,data=None):
    window=catalogue.window(key); x,y,w,h=window
    if components.cells[key][1] == 0:
        return np.zeros((h,w),np.uint8)
    if data is None:
        data=catalogue.read(window)
    bad=missing(data); labels,_=label(bad)
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
    root=v1.ROOT/'data/derived/views'
    if root.resolve() != root:
        raise InvalidInput('sea view: output namespace cannot use symlinks')
    root.mkdir(parents=True,exist_ok=True)
    with build_lock(root,profile['profile_id']):
        return _build(machine,profile,root)


def _build(machine,profile,root):
    started=time.monotonic(); wall_started=time.time()
    def elapsed(): return max(time.monotonic()-started,time.time()-wall_started)
    def guard():
        if elapsed()>3600: raise RuntimeError('view-build 60-minute wall budget exhausted')
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if rss*(1 if sys.platform=='darwin' else 1024)>12*1024**3: raise RuntimeError('view-build 12 GiB memory budget exhausted')
    def progress(phase,n,total):
        print(f'sea2 {phase}: {n}/{total}',file=sys.stderr,flush=True)
    inventory=header_inventory(machine['dsm_dir'])
    catalogue=Catalogue(machine['dsm_dir'])
    code_hashes=build_code_hashes()
    h_fill=np.float32(profile['h_sea_m'])
    source_hashes={item['name']:digest(catalogue.directory/item['name']) for item in inventory}
    guard()
    components,shores=analyse(catalogue,profile,progress=progress,guard=guard)
    stage=Path(tempfile.mkdtemp(prefix='.build-',dir=root))
    (stage/'tiles').mkdir(); (stage/'surface').mkdir()
    try:
        cells=[]; tiles=[]; totals={str(c):0 for c in CODES}; auxiliary={}
        keys=list(catalogue.keys())
        for i,key in enumerate(keys):
            raw=catalogue.tiles.get(key)
            data=None
            if raw is not None and components.cells[key][1]:
                with rasterio.open(raw['path']) as ds:
                    data=ds.read(1)
                    if ds.nodata == h_fill:
                        raise InvalidInput(f'h_sea_m equals the declared NoData value of {ds.name}')
                    options, tags=ds.profile, ds.tags()
            surface=classify_cell(catalogue,key,profile,components,shores,data=data)
            window=catalogue.window(key); x,y,w,h=window
            name=catalogue.name(key); surface_name=name+'.tif'
            c=counts(surface)
            for code,n in c.items(): totals[code]+=n
            write_raster(stage/'surface'/surface_name,surface,catalogue.transform(window),catalogue.crs,255)
            rec=dict(id=name,key=list(key),bounds=catalogue.bounds(window),
                     native_bounds=catalogue.bounds(catalogue.window(key,clip=False)),
                     surface_name=surface_name,surface_sha256=digest(stage/'surface'/surface_name),
                     counts=c,supplied=raw is not None,source_sha256=source_hashes[raw['name']] if raw else None,
                     synthetic=raw is None)
            if raw is not None:
                output=stage/'tiles'/raw['name']
                if data is not None:
                    data[missing(data)]=h_fill
                    write_raster(output,data,options['transform'],options['crs'],options['nodata'],
                                 source_profile=options,tags=tags)
                    assert_fill(raw['path'],output,surface,h_fill)
                    output_hash=digest(output)
                else:
                    output.symlink_to(raw['path']); output_hash=source_hashes[raw['name']]
                    # Auxiliary masks/statistics from raw must not apply to filled values.
                    for aux in raw['auxiliary']:
                        if aux not in auxiliary:
                            (stage/'tiles'/aux).symlink_to(catalogue.directory/aux)
                            auxiliary[aux]=source_hashes[aux]
                rec.update(tile_name=raw['name'],output_sha256=output_hash)
                tiles.append(dict(name=raw['name'],cell=name,source_sha256=source_hashes[raw['name']],
                                  output_sha256=output_hash,counts=c,synthetic=False,bounds=raw['bounds']))
            else:
                filename='FILL_'+name+'.tif'
                full=catalogue.window(key,clip=False)
                data=np.full((catalogue.height,catalogue.width),NODATA,np.float32)
                row=full[1]+full[3]-(y+h); col=x-full[0]
                data[row:row+h,col:col+w]=h_fill
                output=stage/'tiles'/filename
                write_raster(output,data,catalogue.transform(full),catalogue.crs,NODATA)
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
        document=dict(schema=VIEW_SCHEMA,policy=POLICY,
                      profile=profile,profile_sha256=identity(profile),
                      catalogue=dict(files=source_hashes,identity=identity(source_hashes)),
                      rule_version=RULE_VERSION,build_code_sha256=code_hashes,
                      versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                                    rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__),
                      grid=dict(origin=[catalogue.e0,catalogue.n0],resolution=catalogue.res,
                                cell_width=catalogue.width,cell_height=catalogue.height,crs=catalogue.crs,
                                nodata=NODATA,dtype='float32',domain_bounds=catalogue.bounds((l,b,r-l,t-b))),
                      literal_definition_exceptions=catalogue.shifted,
                      cells=cells,tiles=sorted(tiles,key=lambda x:x['name']),auxiliary_outputs=auxiliary,totals=totals)
        if build_code_hashes()!=code_hashes:
            raise RuntimeError('Build code changed during view construction')
        document['view_id']=manifest_identity(document)
        atomic_json(stage/'manifest.json',document)
        destination=root/document['view_id']
        if destination.is_symlink():
            raise InvalidInput('sea view: destination cannot be a symlink')
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
                    dict(schema=POINTER_SCHEMA,view_id=document['view_id'],profile_id=profile['profile_id'],
                         profile_sha256=document['profile_sha256'],header_inventory=inventory))
        return dict(view_id=document['view_id'],path=str(destination),reproduced=reproduced,
                    cells=len(cells),tiles=len(tiles),synthetic_tiles=sum(t['synthetic'] for t in tiles),
                    totals=totals,wall_seconds=elapsed())
    finally:
        if stage.exists(): shutil.rmtree(stage)
