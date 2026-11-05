"""Immutable view identity and surface windows, including cells without tiles."""
from pathlib import Path
import re

import numpy as np
import rasterio
from rasterio.windows import Window

from tools.shade_map.common import digest, identity, read_json
from tools.shade_map.config import InvalidInput


def manifest_identity(document):
    return identity({k:v for k,v in document.items() if k not in ('view_id','created_at','timestamp')})


def read_manifest(view):
    path=Path(view)/'manifest.json'
    if path.is_symlink(): raise InvalidInput('sea view: manifest must not be a symlink')
    doc=read_json(path)
    if not re.fullmatch('[0-9a-f]{64}',doc.get('view_id','')) or manifest_identity(doc)!=doc['view_id']:
        raise InvalidInput('sea view: manifest identity mismatch')
    return doc


def read_surface_window(view,bounds,*,manifest=None):
    view=Path(view); doc=manifest or read_manifest(view)
    grid=doc['grid']; res=grid['resolution']; origin=grid['origin']
    l,b,r,t=map(float,bounds)
    addresses=[(l-origin[0])/res,(b-origin[1])/res,(r-origin[0])/res,(t-origin[1])/res]
    if any(abs(x-round(x))>1e-7 for x in addresses) or not l<r or not b<t:
        raise InvalidInput('surface window: bounds must be ordered and native-grid aligned')
    dl,db,dr,dt=grid['domain_bounds']
    if l<dl or b<db or r>dr or t>dt:
        raise InvalidInput('surface window: bounds outside sea view domain')
    shape=(round((t-b)/res),round((r-l)/res))
    out=np.full(shape,254,np.uint8)
    seen=0
    for cell in doc['cells']:
        cl,cb,cr,ct=cell['bounds']
        x0,y0,x1,y1=max(l,cl),max(b,cb),min(r,cr),min(t,ct)
        if x0>=x1 or y0>=y1: continue
        path=view/'surface'/cell['surface_name']
        if digest(path)!=cell['surface_sha256']:
            raise RuntimeError('sea view: surface hash mismatch: '+cell['id'])
        width,height=round((x1-x0)/res),round((y1-y0)/res)
        with rasterio.open(path) as ds:
            if ds.crs.to_string()!=grid['crs'] or ds.dtypes!=('uint8',) or ds.count!=1 or tuple(ds.bounds)!=tuple(cell['bounds']):
                raise RuntimeError('sea view: surface metadata mismatch')
            a=ds.read(1,window=Window(round((x0-cl)/res),round((ct-y1)/res),width,height))
        row,col=round((t-y1)/res),round((x0-l)/res)
        out[row:row+height,col:col+width]=a
        seen+=height*width
    if seen!=out.size:
        raise RuntimeError('sea view: surface cells do not cover window')
    return out


def verify_view(view,manifest=None):
    view=Path(view); doc=manifest or read_manifest(view)
    expected={'manifest.json'}
    for rec in doc['tiles']:
        path=view/'tiles'/rec['name']; expected.add('tiles/'+rec['name'])
        if digest(path)!=rec['output_sha256']: raise RuntimeError('sea view: tile hash mismatch: '+rec['name'])
    for name,sha in doc.get('auxiliary_outputs',{}).items():
        expected.add('tiles/'+name)
        if digest(view/'tiles'/name)!=sha: raise RuntimeError('sea view: auxiliary hash mismatch')
    for rec in doc['cells']:
        expected.add('surface/'+rec['surface_name'])
        if digest(view/'surface'/rec['surface_name'])!=rec['surface_sha256']: raise RuntimeError('sea view: surface hash mismatch')
    actual={p.relative_to(view).as_posix() for p in view.rglob('*') if p.is_file() or p.is_symlink()}
    if actual!=expected: raise RuntimeError('sea view: unexpected or missing files')
    return doc
