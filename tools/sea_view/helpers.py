"""Static surface windows and effective-policy provenance outside the engine."""
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

from src import v1
from src.spatial import intersects
from tools.sea_view.build import identity
from tools.sea_view.extract import digest


def read_manifest(view):
    view=Path(view)
    manifest=json.loads((view/'manifest.json').read_text())
    if identity(manifest)!=manifest['view_id']: raise ValueError('View manifest identity mismatch')
    return manifest


def read_surface_window(view,bounds):
    view=Path(view);manifest=read_manifest(view)
    grid=v1._custom_grid([dict(crs='EPSG:2326')],bounds)
    if tuple(bounds)!=grid.bounds(): raise ValueError('Surface bounds must be on the 0.5 m lattice')
    if grid.width*grid.height>v1.MAX_OUTPUT_PIXELS: raise ValueError('Surface window exceeds V1 area limit')
    surface=np.full((grid.height,grid.width),255,np.uint8)
    for row in manifest['tiles']:
        path=view/'surface'/row['name']
        with rasterio.open(path) as ds:
            if not intersects(bounds,ds.bounds): continue
            if digest(path)!=row['surface_sha256']: raise ValueError('Surface raster hash mismatch')
            if tuple(ds.transform)[:6]!=tuple(row['transform']) or ds.crs.to_string()!=row['crs']:
                raise ValueError('Surface georeferencing mismatch')
            c=round((ds.transform.c-grid.affine.c)/.5);r=round((grid.affine.f-ds.transform.f)/.5)
            x0=max(0,c);y0=max(0,r);x1=min(grid.width,c+ds.width);y1=min(grid.height,r+ds.height)
            surface[y0:y1,x0:x1]=ds.read(1,window=Window(x0-c,y0-r,x1-x0,y1-y0))
    return surface,grid.affine


def effective_policy(result_index_path):
    index=json.loads(Path(result_index_path).read_text())
    views=set()
    # Result indexes record source paths either directly or in dependency records.
    def visit(value):
        if isinstance(value,dict):
            for item in value.values(): visit(item)
        elif isinstance(value,list):
            for item in value: visit(item)
        elif isinstance(value,str):
            path=Path(value)
            if path.parent.name=='tiles' and (path.parent.parent/'manifest.json').exists():
                views.add(path.parent.parent)
            elif path.name=='tiles' and (path.parent/'manifest.json').exists():
                views.add(path.parent)
    visit(index)
    definition=Path(result_index_path).with_name('run_definition.json')
    if definition.exists(): visit(json.loads(definition.read_text()))
    if len(views)!=1: raise ValueError('Result must resolve to exactly one verifiable DSM view manifest')
    view=views.pop();manifest=read_manifest(view)
    hashes={t['output_sha256'] for t in manifest['tiles']}
    if any(s['sha256'] not in hashes for d in index.get('tile_dependencies',[]) for s in d['sources']):
        raise ValueError('Result dependencies disagree with view manifest')
    return dict(engine_policy=index['policy'],surface_policy=manifest['policy'],view_id=manifest['view_id'],
                diagnostic=manifest['diagnostic'],manifest=str(view/'manifest.json'))
