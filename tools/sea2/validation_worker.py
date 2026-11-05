"""Report-only pixel-centre comparisons; invoked by the separate vector reader."""
from __future__ import annotations

import argparse
from collections import defaultdict
from functools import lru_cache
import math
from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from scipy import ndimage

from src.spatial import intersects
from tools.shade_map.common import atomic_json, digest, read_json
from .catalogue import Catalogue
from .rule import Components, CODES, classify_points, counts, label
from .view import read_manifest


class MapCells:
    def __init__(self,directory):
        self.directory=Path(directory); self.manifest=read_json(self.directory/'manifest.json')

    @lru_cache(maxsize=24)
    def masks(self,name,bounds,shape):
        path=self.directory/(name+'.json')
        if digest(path)!=self.manifest['cell_files'][path.name]: raise RuntimeError('Validation vector hash mismatch')
        features=read_json(path); transform=from_bounds(*bounds,shape[1],shape[0])
        def burn(code):
            shapes=[(f['geometry'],1) for f in features if f['code']==code]
            return rasterize(shapes,out_shape=shape,transform=transform,fill=0,all_touched=False,dtype='uint8').astype(bool) if shapes else np.zeros(shape,bool)
        return burn('SEF'),burn('LAF')


def metrics(surface,sef,laf,bounds,coverage_bbox,res):
    water=(surface==1)|(surface==2); absent=(surface==254)|(surface==255)
    unknown=water & ~(sef|laf)
    h,w=surface.shape
    xs=bounds[0]+(np.arange(w)+.5)*res; ys=bounds[3]-(np.arange(h)+.5)*res
    l,b,r,t=coverage_bbox
    outside=~(((xs>=l)&(xs<=r))[None,:] & ((ys>=b)&(ys<=t))[:,None])
    return dict(water_pixels=int(water.sum()),water_in_supplied_tiles=int(np.count_nonzero(surface==1)),
                water_inside_SEF_minus_LAF=int(np.count_nonzero(water&sef&~laf)),
                mapped_sea_nodata=int(np.count_nonzero((water|absent)&sef&~laf)),
                false_water=int(np.count_nonzero(water&laf)),
                false_water_supplied=int(np.count_nonzero((surface==1)&laf)),
                false_water_synthetic=int(np.count_nonzero((surface==2)&laf)),
                missed_sea_254=int(np.count_nonzero((surface==254)&sef&~laf)),
                missed_sea_255=int(np.count_nonzero((surface==255)&sef&~laf)),
                land_voids_inside_SEF=int(np.count_nonzero((surface==255)&sef)),
                land_voids_inside_SEF_minus_LAF=int(np.count_nonzero((surface==255)&sef&~laf)),
                water_outside_coverage_bbox=int(np.count_nonzero(unknown&outside)),
                water_neither_class_within_bbox=int(np.count_nonzero(unknown&~outside)),
                water_neither_class=int(unknown.sum()))


def component_stats(labels,offset,bounds,res):
    bincount=np.bincount(labels.ravel())
    result={}
    for local,slices in enumerate(ndimage.find_objects(labels),1):
        if slices is None: continue
        rs,cs=slices
        result[offset+local]=dict(pixels=int(bincount[local]),bounds=[bounds[0]+cs.start*res,bounds[3]-rs.stop*res,
                                                                     bounds[0]+cs.stop*res,bounds[3]-rs.start*res])
    return result


def final_components(components,stats):
    groups={}
    for k,value in stats.items():
        root=components.find(k)
        if root not in groups: groups[root]=dict(pixels=0,bounds=list(value['bounds']))
        row=groups[root]; row['pixels']+=value['pixels']
        a,b=row['bounds'],value['bounds']; row['bounds']=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]
    return [dict(component_id=k,**v) for k,v in sorted(groups.items()) if v['pixels']>2500]


def report_scope(cells,get_surface,maps,grid,*,bounds=None,progress=False):
    totals=defaultdict(int); classes={str(c):0 for c in CODES}; unclassified=[]; components=Components(); comp_stats={}
    res=grid['resolution']; north_cutoff=grid['domain_bounds'][3]-1000-10000
    chosen=[c for c in cells if bounds is None or intersects(c['bounds'],bounds)]
    for i,cell in enumerate(chosen):
        surface=get_surface(cell)
        sef,laf=maps.masks(cell['id'],tuple(cell['bounds']),surface.shape)
        cl,cb,cr,ct=cell['bounds']
        actual=cell['bounds'] if bounds is None else [max(cl,bounds[0]),max(cb,bounds[1]),min(cr,bounds[2]),min(ct,bounds[3])]
        l,b,r,t=actual
        rs=slice(round((ct-t)/res),round((ct-b)/res)); cs=slice(round((l-cl)/res),round((r-cl)/res))
        a=surface[rs,cs]; sm=sef[rs,cs]; lm=laf[rs,cs]
        for k,n in counts(a).items(): classes[k]+=n
        value=metrics(a,sm,lm,actual,maps.manifest['coverage_bbox'],res)
        for k,n in value.items(): totals[k]+=n
        if value['water_neither_class']:
            unclassified.append(dict(cell=cell['id'],bounds=actual,
                    water_neither_class=value['water_neither_class'],outside_coverage_bbox=value['water_outside_coverage_bbox'],
                    within_bbox_neither_class=value['water_neither_class_within_bbox'],northern_boundary=t>=north_cutoff))
        false=np.zeros(surface.shape,bool); false[rs,cs]=((a==1)|(a==2))&lm
        labels=components.add(tuple(cell['key']),false)
        offset,_=components.cells[tuple(cell['key'])]
        comp_stats.update(component_stats(labels,offset,cell['bounds'],res))
        if progress and i%250==0: print(f'iB5000 raster report: {i+1}/{len(chosen)}',file=sys.stderr,flush=True)
    denominator=totals['water_in_supplied_tiles']
    return dict(class_counts=classes,**totals,
                mapped_sea_nodata_water_fraction=totals['water_inside_SEF_minus_LAF']/totals['mapped_sea_nodata'] if totals['mapped_sea_nodata'] else None,
                false_water_fraction_of_water_in_supplied_tiles=totals['false_water']/denominator if denominator else None,
                unclassified_water_cells=unclassified,
                northern_boundary_definition=dict(lower_northing=north_cutoff,description='northernmost 10 km of the raw catalogue bounding box'),
                northern_boundary_cells=[r for r in unclassified if r['northern_boundary']],
                false_water_components_over_2500=final_components(components,comp_stats))


def sensitivity(view,doc,maps,scopes,machine):
    from copy import deepcopy
    catalogue=Catalogue(machine['dsm_dir'],doc['profile'])
    cells=doc['cells']; outputs=[]
    def read(cell):
        with rasterio.open(view/'surface'/cell['surface_name']) as ds: return ds.read(1)
    maximum=doc['profile']['max_shore_distance_m']
    needed={}
    for name,bounds in scopes.items():
        halo=[bounds[0]-1000,bounds[1]-1000,bounds[2]+1000,bounds[3]+1000]
        needed[name]=(halo,[c for c in cells if intersects(c['bounds'],halo)])
    for margin in (4,5,6):
        p=deepcopy(doc['profile']); p['low_shore_margin_m']=margin
        shore_keys=set()
        for halo,items in needed.values():
            expanded=[halo[0]-maximum-101,halo[1]-maximum-101,halo[2]+maximum+101,halo[3]+maximum+101]
            shore_keys.update(tuple(c['key']) for c in cells if c['supplied'] and intersects(c['bounds'],expanded))
        shores={key:catalogue.shores(key,p) for key in sorted(shore_keys)}
        for preference in (0,50,100):
            p['shore_preference_m']=preference
            for name,(halo,items) in needed.items():
                def classified(cell):
                    key=tuple(cell['key']); old=read(cell); bad=old!=0; opened=(old!=255)&bad
                    low,high=catalogue.points_near(key,shores,maximum+preference)
                    x,y,w,h=catalogue.window(key)
                    return classify_points(bad,opened,low,high,p,x0=x,y0=y,resolution=catalogue.res,
                                           supplied=cell['supplied'],origin=(catalogue.e0,catalogue.n0),
                                           pixel_offset=catalogue.pixel_offset(key))
                result=report_scope(items,classified,maps,doc['grid'],bounds=halo)
                outputs.append(dict(scope=name+'_halo',bounds=halo,low_shore_margin_m=margin,
                                    shore_preference_m=preference,report=result))
                print(f'sensitivity {name}: margin={margin}, preference={preference}',file=sys.stderr,flush=True)
    return outputs


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--view',required=True); p.add_argument('--maps',required=True)
    p.add_argument('--scopes',required=True); p.add_argument('--machine',required=True); p.add_argument('--work',required=True)
    args=p.parse_args(argv)
    view=Path(args.view); doc=read_manifest(view); maps=MapCells(args.maps); scopes=read_json(args.scopes)
    def read(cell):
        path=view/'surface'/cell['surface_name']
        if digest(path)!=cell['surface_sha256']: raise RuntimeError('Surface changed during validation')
        with rasterio.open(path) as ds: return ds.read(1)
    reports={'territory':report_scope(doc['cells'],read,maps,doc['grid'],progress=True)}
    for name,bounds in scopes.items():
        reports[name]=report_scope(doc['cells'],read,maps,doc['grid'],bounds=bounds)
        halo=[bounds[0]-1000,bounds[1]-1000,bounds[2]+1000,bounds[3]+1000]
        reports[name+'_halo']=report_scope(doc['cells'],read,maps,doc['grid'],bounds=halo)
    root=Path(__file__).resolve().parents[2]; evidence=root/'docs/sea2/evidence'
    header=dict(schema='sea2-ib5000-report-1.0',report_only=True,view_id=doc['view_id'],profile_sha256=doc['profile_sha256'],
                observational_accuracy='NOT VERIFIED',map_coverage_definition='outside joint LAF/SEF bounding box versus neither class within that box; no authoritative coverage polygon is inferred')
    atomic_json(evidence/'ib5000-report.json',dict(**header,reports=reports))
    variants=sensitivity(view,doc,maps,scopes,read_json(args.machine))
    atomic_json(evidence/'sensitivity-report.json',dict(**header,classification_only=True,variants=variants))
    print('iB5000 report and all 18 scope/parameter sensitivity records complete',flush=True)


if __name__=='__main__': main()
