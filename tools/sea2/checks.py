"""Read-only real-data land regression and independent water-ray evidence."""
from __future__ import annotations

import argparse
from collections import defaultdict
from functools import lru_cache
import math
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from src import v1
from src.spatial import read_window
from src.v1_cache import tile_grid, entry_paths
from tools import region_request as adapter
from tools.shade_map.common import atomic_json, digest, identity, read_json, verify_seal
from tools.shade_map.publication import _solar
from .view import read_manifest, read_surface_window


def layer(folder,frame,cell,name):
    with rasterio.open(Path(folder)/frame['date']/frame['time']/name/(cell['id']+'.tif')) as ds:
        return ds.read(1)


class EvidenceRun:
    """Read published layers, or explicitly inspect complete V2 work read-only."""
    def __init__(self,folder,*,allow_engine_work=False):
        self.folder=Path(folder);self.manifest=read_json(self.folder/'run_manifest.json')
        run=self.manifest;verify_seal(run)
        self.engine_work=run['status']!='complete'
        self.kind='completed V2 work; F publication incomplete' if self.engine_work else 'F publication'
        if not self.engine_work:return
        if not allow_engine_work:raise RuntimeError('F publication is incomplete; --engine-work is required for intermediate evidence')
        succeeded={event['batch_id'] for event in run['engine_events'] if event['state']=='SUCCEEDED'}
        if not run['batch_ids'] or not set(run['batch_ids'])<=succeeded:
            raise RuntimeError('F engine work is incomplete')
        root=(v1.ROOT/'outputs/shade_map_work').resolve()
        work=(root/(run['name']+'-'+run['run_id'][:12])).resolve()
        if not work.is_relative_to(root) or read_json(work/'owner.json')!=dict(schema='shade-map-work-1.0',name=run['name'],run_id=run['run_id']):
            raise RuntimeError('F work ownership differs')
        path=work/'adapter/region_request.json'
        if digest(path)!=run['adapter_sidecar_sha256']:raise RuntimeError('F work sidecar hash differs')
        self.sidecar=read_json(path)
        self.mosaics=[work/'state'/(batch+'.logical_mosaic.json') for batch in run['batch_ids']]
        if not all(p.is_file() for p in self.mosaics):raise RuntimeError('Missing completed V2 logical mosaic')

    def layers(self,frame,cell):
        if self.engine_work:
            shade,quality,_=adapter.read_region_window(self.sidecar,utc_time=frame['utc_time'],bounds=cell['bounds'],logical_mosaics=self.mosaics)
            return shade,quality
        return layer(self.folder,frame,cell,'shade'),layer(self.folder,frame,cell,'quality')

    def solar(self,frame):
        if self.engine_work:return _solar(self.sidecar,frame['utc_time'])
        return read_json(self.folder/frame['date']/frame['time']/'frame.json')['solar_by_tile']


def compare(raw,sea,view,output,*,engine_work=False):
    raw,sea,view=map(Path,(raw,sea,view))
    reference=EvidenceRun(raw); candidate=EvidenceRun(sea,allow_engine_work=engine_work)
    old,new=reference.manifest,candidate.manifest;doc=read_manifest(view)
    if new['source_identity']['view_id']!=doc['view_id']:raise RuntimeError('Sea evidence uses a different view')
    if old['resolved_bounds']!=new['resolved_bounds'] or [f['utc_time'] for f in old['frames']]!=[f['utc_time'] for f in new['frames']]:
        raise RuntimeError('Regression reference geometry/frames differ')
    cache=v1.ROOT/'data/processed/shade_v1'/('sea_fill_v2_'+doc['view_id'][:12])
    surfaces={c['id']:read_surface_window(view,c['bounds']) for c in new['cells']}
    by_key={tuple(c['key']):c for c in doc['cells']}; g=doc['grid']; res=g['resolution']
    @lru_cache(maxsize=24)
    def cell_surface(key):
        rec=by_key[key]
        with rasterio.open(view/'surface'/rec['surface_name']) as ds:return ds.read(1)
    def blocker_classes(rows,cols):
        east=(cols+.5)*res; north=-(rows+.5)*res
        ix=np.floor((east-g['origin'][0])/(g['cell_width']*res)).astype(int)
        iy=np.floor((north-g['origin'][1])/(g['cell_height']*res)).astype(int)
        classes=np.full(len(rows),254,np.uint8)
        for key in set(zip(ix.tolist(),iy.tolist())):
            rec=by_key.get(key)
            if rec is None:continue
            hit=(ix==key[0])&(iy==key[1]); values=cell_surface(key)
            rr=np.floor((rec['bounds'][3]-north[hit])/res).astype(int)
            cc=np.floor((east[hit]-rec['bounds'][0])/res).astype(int)
            classes[hit]=values[rr,cc]
        return classes
    frames=[]; thresholds={}; examples=[]
    for before,after in zip(old['frames'],new['frames']):
        oldsolar={r['source_name']:r for r in reference.solar(before)};newsolar={r['source_name']:r for r in candidate.solar(after)}
        values=defaultdict(int); former={str(k):0 for k in (0,1,255)}
        for cell in new['cells']:
            s=surfaces[cell['id']];a,aq=reference.layers(before,cell);b,bq=candidate.layers(after,cell)
            if not candidate.engine_work and not np.array_equal(s,layer(sea,after,cell,'surface')):
                raise RuntimeError('Published surface differs from the sea view')
            observed=s==0; land=observed|(s==255)
            values['land_pixels']+=int(land.sum()); values['observed_land_pixels']+=int(observed.sum())
            values['shaded_to_sunlit']+=int(np.count_nonzero(observed&(a==1)&(b==0)))
            values['unfilled_pixels_with_non255_shade']+=int(np.count_nonzero(((s==254)|(s==255))&(b!=255)))
            for code in former:former[code]+=int(np.count_nonzero(observed&(aq==2)&(b==int(code))))
            losses=observed&(a==0)&(b!=0); values['sunlit_to_non_sunlit']+=int(losses.sum())
            name=cell['source_tile']
            if name is None:
                values['unexplained_sunlit_loss']+=int(losses.sum())
                continue
            ot,nt=oldsolar[name],newsolar[name]
            if any(ot[k]!=nt[k] for k in ('reference','direction_deg','apparent_elevation_deg')):
                raise RuntimeError('Owning-tile solar references changed')
            thresholds[name]=dict(old_threshold_deg=ot['threshold_deg'],new_threshold_deg=nt['threshold_deg'])
            distant=losses&(bq==3)&(nt['threshold_deg']>ot['threshold_deg'])&(nt['apparent_elevation_deg']<=nt['threshold_deg'])
            values['explained_by_raised_threshold']+=int(distant.sum())
            needed=losses&~distant
            if not needed.any():continue
            path,_=entry_paths(cache,nt['spatial_key'],nt['direction_deg'])
            with rasterio.open(path) as ds:horizon,support,distance=ds.read()
            rr,cc=np.nonzero(needed)
            # Publication cells may be cropped; convert to owning native addresses.
            rowoff=round((cell['native_bounds'][3]-cell['bounds'][3])/res)
            coloff=round((cell['bounds'][0]-cell['native_bounds'][0])/res)
            nr,nc=rr+rowoff,cc+coloff
            absolute_rows=round(-cell['native_bounds'][3]/res)+nr
            absolute_cols=round(cell['native_bounds'][0]/res)+nc
            dr,dc=-math.cos(math.radians(nt['direction_deg'])),math.sin(math.radians(nt['direction_deg']))
            if abs(dr)<1e-14:dr=0
            if abs(dc)<1e-14:dc=0
            dist=distance[nr,nc]
            br=absolute_rows+np.rint(absolute_rows%2+dr*dist/res).astype(np.int64)-absolute_rows%2
            bc=absolute_cols+np.rint(absolute_cols%2+dc*dist/res).astype(np.int64)-absolute_cols%2
            codes=blocker_classes(br,bc)
            proven=np.isin(codes,[1,2])&(horizon[nr,nc]>nt['apparent_elevation_deg'])&(b[rr,cc]==1)
            values['explained_by_water_blocker']+=int(proven.sum()); values['unexplained_sunlit_loss']+=int((~proven).sum())
            for k in np.flatnonzero(proven)[:3]:
                if len(examples)<24:examples.append(dict(utc=after['utc_time'],tile=name,row=int(nr[k]),col=int(nc[k]),
                    blocker_absolute_row=int(br[k]),blocker_absolute_col=int(bc[k]),surface_class=int(codes[k]),
                    distance_m=float(dist[k]),horizon_deg=float(horizon[nr[k],nc[k]]),apparent_elevation_deg=nt['apparent_elevation_deg']))
        frames.append(dict(utc_time=after['utc_time'],date=after['date'],time=after['time'],**values,former_quality2_to_shade=former))
    passed=all(f.get('shaded_to_sunlit',0)==f.get('unfilled_pixels_with_non255_shade',0)==f.get('unexplained_sunlit_loss',0)==0 for f in frames)
    result=dict(schema='sea2-land-regression-1.0',raw_run_id=old['run_id'],sea_run_id=new['run_id'],
                frames=frames,thresholds=thresholds,blocker_examples=examples,passed=passed,
                sea_evidence_source=candidate.kind,published_surface_verified=None if candidate.engine_work else True,
                attribution='Every sunlit loss is counted against a raised owning-tile threshold or a reconstructed maximum blocker on class 1/2 water.')
    atomic_json(output,result)
    if not passed:raise RuntimeError('Land regression gate failed; evidence retained')
    return result


def independent_rays(dsm,rows,cols,azimuth,*,origin_row,origin_col,resolution=.5,max_distance=1000):
    """Independent NumPy direct rays; no engine horizon function or cache is used.

    Implements documented 0.25 m nominal steps, global ties-to-even parity,
    radial cutoff and nominal slope denominator, separately from the Numba kernel.
    """
    rows=np.asarray(rows,int); cols=np.asarray(cols,int)
    dr=-math.cos(math.radians(azimuth)); dc=math.sin(math.radians(azimuth))
    if abs(dr)<1e-14:dr=0
    if abs(dc)<1e-14:dc=0
    distances=np.arange(1,int(max_distance/.25)+1,dtype=np.float64)*.25
    rp=(rows+origin_row)%2; cp=(cols+origin_col)%2
    rd=np.rint(rp[:,None]+dr*distances[None,:]/resolution).astype(int)-rp[:,None]
    cd=np.rint(cp[:,None]+dc*distances[None,:]/resolution).astype(int)-cp[:,None]
    radial=(rd*rd+cd*cd)*resolution**2<=max_distance**2+1e-9
    rr=rows[:,None]+rd; cc=cols[:,None]+cd
    inside=(rr>=0)&(rr<dsm.shape[0])&(cc>=0)&(cc<dsm.shape[1])
    z=dsm[np.clip(rr,0,dsm.shape[0]-1),np.clip(cc,0,dsm.shape[1]-1)].astype(np.float64)
    z[~inside]=np.nan
    target=dsm[rows,cols].astype(np.float64)
    complete=np.all(~radial|np.isfinite(z),axis=1)&np.isfinite(target)
    slopes=(z-target[:,None])/distances[None,:]
    slopes[~radial|~np.isfinite(slopes)]=0
    horizon=np.rad2deg(np.arctan(np.maximum(0,slopes.max(axis=1)))).astype(np.float32)
    horizon[~np.isfinite(target)]=np.nan
    return horizon,complete


def reference_labels(horizon,complete,elevation,threshold):
    result=np.full(horizon.shape,255,np.uint8); quality=np.ones(horizon.shape,np.uint8)
    finite=np.isfinite(horizon)
    if elevation<=0:
        quality[finite]=4; return result,quality
    shade=finite&(horizon>elevation); result[shade]=1; quality[shade]=0
    rest=finite&~shade; quality[rest&~complete]=2; quality[rest&complete]=3
    sun=rest&complete&(elevation>threshold); result[sun]=0; quality[sun]=0
    return result,quality


def rays(folder,view,records,output,*,engine_work=False):
    folder,view=Path(folder),Path(view);evidence=EvidenceRun(folder,allow_engine_work=engine_work)
    run=evidence.manifest;doc=read_manifest(view)
    if run['source_identity']['view_id']!=doc['view_id']:raise RuntimeError('Sea-ray evidence uses a different view')
    selected=[f for f in run['frames'] if f['time'] in ('0830','1230','1510')]
    if len(selected)!=3:raise RuntimeError('Sea-ray check needs the three frozen instants')
    rng=np.random.default_rng(20261104); results={f['utc_time']:dict(utc_time=f['utc_time'],samples=[]) for f in selected}
    for cell in run['cells']:
        name=cell['source_tile']
        if name is None:continue
        tile=next(r for r in records if Path(r['path']).name==name)
        surface=read_surface_window(view,cell['native_bounds'])
        with rasterio.open(view/'tiles'/name) as ds:height=ds.read(1)
        water=np.isin(surface,[1,2])
        near=water&binary_dilation((surface==0)&(height>=10),iterations=16)
        near_pool=np.argwhere(near); pool=np.argwhere(water)
        if not len(pool):continue
        chosen=[]
        if len(near_pool):chosen.extend(near_pool[rng.choice(len(near_pool),min(25,len(near_pool)),replace=False)].tolist())
        seen={tuple(p) for p in chosen}
        for k in rng.permutation(len(pool)):
            pair=tuple(map(int,pool[k]))
            if pair not in seen:chosen.append(list(pair));seen.add(pair)
            if len(chosen)>=200:break
        coords=np.array(chosen,int); grid=tile_grid(tile); halo=math.ceil(1000/grid.res)
        window=(-halo,-halo,grid.width+2*halo,grid.height+2*halo)
        dsm=read_window(records,grid,window)
        origin_row=round(-grid.affine.f/grid.res)-halo; origin_col=round(grid.affine.c/grid.res)-halo
        for frame in selected:
            solar=next(s for s in evidence.solar(frame) if s['source_name']==name)
            h,support=independent_rays(dsm,coords[:,0]+halo,coords[:,1]+halo,solar['direction_deg'],
                                       origin_row=origin_row,origin_col=origin_col)
            expected,flags=reference_labels(h,support,solar['apparent_elevation_deg'],solar['threshold_deg'])
            actual,q=evidence.layers(frame,cell)
            for k,(r,c) in enumerate(coords):
                rowoff=round((cell['native_bounds'][3]-cell['bounds'][3])/grid.res)
                coloff=round((cell['bounds'][0]-cell['native_bounds'][0])/grid.res)
                if not (0<=r-rowoff<actual.shape[0] and 0<=c-coloff<actual.shape[1]):continue
                label_value=int(actual[r-rowoff,c-coloff]); quality=int(q[r-rowoff,c-coloff])
                results[frame['utc_time']]['samples'].append(dict(tile=name,row=int(r),col=int(c),near_tall_structure=bool(near[r,c]),
                    label=label_value,quality=quality,reference_label=int(expected[k]),reference_quality=int(flags[k]),
                    horizon_deg=float(h[k]),equality_neighbourhood=bool(abs(float(h[k])-solar['apparent_elevation_deg'])<=1e-4),
                    matches=label_value==int(expected[k]) and quality==int(flags[k])))
    frames=[]
    for result in results.values():
        samples=result.pop('samples')
        mismatches=[s for s in samples if s['label']!=s['reference_label']]
        result.update(n=len(samples),near_tall_structure=sum(s['near_tall_structure'] for s in samples),
              mismatches=len(mismatches),mismatches_outside_equality=sum(not s['equality_neighbourhood'] for s in mismatches),
              quality_mismatches=sum(s['quality']!=s['reference_quality'] for s in samples),
              sample_sha256=identity(samples),sample_examples=samples[:4],mismatch_examples=mismatches[:12])
        frames.append(result)
    passed=all(f['n']>=200 and f['near_tall_structure']>0 and f['mismatches_outside_equality']==0 for f in frames)
    report=dict(schema='sea2-independent-rays-1.0',method='Independent NumPy direct 0.25 m rays with documented canonical parity and radial cutoff; independent classifier; no engine horizon/cache reference.',
                numerical_consistency_only=True,observational_accuracy='NOT VERIFIED',frames=frames,passed=passed,engine_evidence_source=evidence.kind,
                sample_seed=20261104,near_tall_structure_definition='water within 16 four-neighbour pixels of observed DSM at least 10 m high')
    atomic_json(output,report)
    if not passed:raise RuntimeError('Independent water-ray check failed; evidence retained')
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['compare','rays']);p.add_argument('--run',required=True)
    p.add_argument('--view',required=True);p.add_argument('--output',required=True);p.add_argument('--reference')
    p.add_argument('--engine-work',action='store_true',help='Read completed V2 work for numerical evidence when F publication is incomplete')
    args=p.parse_args(argv)
    if args.action=='compare':
        if not args.reference:p.error('--reference is required for compare')
        compare(args.reference,args.run,args.view,args.output,engine_work=args.engine_work)
    else:
        run=read_json(Path(args.run)/'run_manifest.json')
        work=v1.ROOT/'outputs/shade_map_work'/(run['name']+'-'+run['run_id'][:12])
        path=work/'adapter/region_request.json'
        if digest(path)!=run['adapter_sidecar_sha256']:raise RuntimeError('F work sidecar hash differs')
        sidecar=read_json(path)
        records=v1.index_sources(sidecar['source_directory'])
        rays(args.run,args.view,records,args.output,engine_work=args.engine_work)


if __name__=='__main__':main()
