"""Read-only development checks of B2.2 publications and direct DSM rays."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from src import v1
from src.spatial import read_window
from src.v1_cache import canonical_origin, entry_paths, tile_grid
from tools import region_request as adapter
from tools.shade_map.common import digest, identity, read_json
from tools.shade_map.publication import _solar
from tools.shade_map.runner import verify_run
from . import VIEW_NAMESPACE
from .view import read_manifest, read_surface_window


def layer(folder, frame, cell, name):
    path = Path(folder)/frame['date']/frame['time']/name/(cell['id']+'.tif')
    with rasterio.open(path) as ds:
        return ds.read(1)


class EvidenceRun:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.manifest = verify_run(self.folder)
        self.frames = self.manifest['frames']
        self.bounds = self.manifest['resolved_bounds']
        self.run_id = self.manifest['run_id']

    def layers(self, frame, cell):
        return layer(self.folder,frame,cell,'shade'), layer(self.folder,frame,cell,'quality')

    def solar(self, frame):
        return read_json(self.folder/frame['date']/frame['time']/'frame.json')['solar_by_tile']


class RawCounterfactual:
    def __init__(self, work):
        self.work = Path(work)
        owner = read_json(self.work/'owner.json')
        self.run_id = identity(owner)
        definition = read_json(self.work/'counterfactual.json')
        if definition['source_identity']['provider'] != 'raw':
            raise RuntimeError('Counterfactual is not a raw source')
        self.sidecar = definition['sidecar']
        self.bounds = self.sidecar['resolved_bounds']
        self.frames = [dict(utc_time=t) for t in owner['utc_times']]
        self.mosaics = [self.work/'state'/(batch['id']+'.logical_mosaic.json') for batch in self.sidecar['batches']]

    def layers(self, frame, cell):
        shade, quality, _ = adapter.read_region_window(
            self.sidecar, utc_time=frame['utc_time'], bounds=cell['bounds'], logical_mosaics=self.mosaics)
        return shade, quality

    def solar(self, frame):
        return _solar(self.sidecar,frame['utc_time'])


def publication_counts(run, view):
    """Recount every published pixel, including all reasons for uncertainty."""
    doc = read_manifest(view)
    manifest = run.manifest
    if manifest['source_identity']['view_id'] != doc['view_id']:
        raise RuntimeError('F publication uses a different view')
    surfaces = {c['id']:read_surface_window(view,c['bounds'],manifest=doc) for c in manifest['cells']}
    frames = []
    for frame in run.frames:
        cross = Counter()
        for cell in manifest['cells']:
            surface = layer(run.folder,frame,cell,'surface')
            if not np.array_equal(surface,surfaces[cell['id']]):
                raise RuntimeError('Published surface differs from the view')
            shade, quality = run.layers(frame,cell)
            if not np.array_equal(shade==255,quality!=0):
                raise RuntimeError('Published shade and quality do not partition valid labels')
            # 6 possible surface classes, 3 shade codes, 5 quality codes.
            encoded = surface.astype(np.int32)*1280+shade.astype(np.int32)*5+quality
            for value in np.flatnonzero(binned := np.bincount(encoded.ravel())):
                s, rest = divmod(int(value),1280)
                sh, q = divmod(rest,5)
                cross[(s,sh,q)] += int(binned[value])
        expected = read_json(run.folder/frame['date']/frame['time']/'frame.json')['combinations']
        combinations = [dict(surface=s,shade=sh,quality=q,pixels=n) for (s,sh,q),n in sorted(cross.items())]
        if combinations != expected:
            raise RuntimeError('Published cross-counts differ from the rasters')
        groups = {}
        for name, classes in [('land',(0,3)),('water',(1,2)),('other',(4,)),('outside',(255,))]:
            count = sum(n for (s,_,_),n in cross.items() if s in classes)
            result = {'pixels':count}
            if name in ('land','water'):
                sun = sum(n for (s,sh,_),n in cross.items() if s in classes and sh==0)
                shade = sum(n for (s,sh,_),n in cross.items() if s in classes and sh==1)
                uncertain = count-sun-shade
                result.update(sunlit=sun,shaded=shade,uncertain=uncertain,
                              uncertain_by_quality={str(code):sum(n for (s,sh,q),n in cross.items()
                                  if s in classes and sh==255 and q==code) for code in range(1,5)},
                              shade_bounds=[shade/count,(shade+uncertain)/count] if count else None,
                              sunlit_bounds=[sun/count,(sun+uncertain)/count] if count else None)
            groups[name] = result
        frames.append(dict(time=frame['time'],utc_time=frame['utc_time'],cross_counts=combinations,groups=groups,
                           quality_1_or_2=sum(n for (_,_,q),n in cross.items() if q in (1,2)),
                           remaining_255_outside_quality_3_or_4=sum(n for (_,sh,q),n in cross.items() if sh==255 and q not in (3,4))))
    return dict(run_id=run.run_id,view_id=doc['view_id'],frames=frames,
                missing_data_check=all(f['quality_1_or_2']==f['remaining_255_outside_quality_3_or_4']==0 for f in frames))


def compare(reference, candidate, view):
    if (reference.bounds!=candidate.bounds or
            [f['utc_time'] for f in reference.frames]!=[f['utc_time'] for f in candidate.frames]):
        raise RuntimeError('Regression reference geometry or frames differ')
    doc = read_manifest(view)
    cache = v1.ROOT/'data/processed/shade_v1'/(VIEW_NAMESPACE+'_'+doc['view_id'][:12])
    grid = doc['grid']
    res = grid['resolution']
    cells = candidate.manifest['cells']
    surfaces = {c['id']:read_surface_window(view,c['bounds'],manifest=doc) for c in cells}
    by_key = {tuple(c['key']):c for c in doc['cells']}

    @lru_cache(maxsize=32)
    def surface_cell(key):
        record = by_key[key]
        with rasterio.open(Path(view)/'surface'/record['surface_name']) as ds:
            return ds.read(1)

    def blocker_classes(rows, cols):
        east, north = (cols+.5)*res, -(rows+.5)*res
        xs = np.floor((east-grid['origin'][0])/(grid['cell_width']*res)).astype(int)
        ys = np.floor((north-grid['origin'][1])/(grid['cell_height']*res)).astype(int)
        classes = np.full(len(rows),255,np.uint8)
        for key in set(zip(xs.tolist(),ys.tolist())) & by_key.keys():
            left, bottom, right, top = by_key[key]['bounds']
            hit = (xs==key[0]) & (ys==key[1]) & (east>=left) & (east<right) & (north>=bottom) & (north<top)
            rr = np.floor((top-north[hit])/res).astype(int)
            cc = np.floor((east[hit]-left)/res).astype(int)
            classes[hit] = surface_cell(key)[rr,cc]
        return classes

    frames, thresholds, examples = [], {}, []
    for before, after in zip(reference.frames,candidate.frames):
        old_solar = {r['source_name']:r for r in reference.solar(before)}
        new_solar = {r['source_name']:r for r in candidate.solar(after)}
        values = dict(observed_land_pixels=0,shaded_to_sunlit=0,sunlit_to_non_sunlit=0,
                      explained_by_raised_threshold=0,explained_by_filled_blocker=0,
                      unexplained_sunlit_loss=0)
        former = {str(q):{str(sh):0 for sh in (0,1,255)} for q in range(1,5)}
        for cell in cells:
            surface = surfaces[cell['id']]
            observed = surface==0
            if not observed.any():
                continue
            a, aq = reference.layers(before,cell)
            b, bq = candidate.layers(after,cell)
            values['observed_land_pixels'] += int(observed.sum())
            values['shaded_to_sunlit'] += int(np.count_nonzero(observed & (a==1) & (b==0)))
            for q, counts in former.items():
                raw_unknown = observed & (a==255) & (aq==int(q))
                for sh in counts:
                    counts[sh] += int(np.count_nonzero(raw_unknown & (b==int(sh))))
            losses = observed & (a==0) & (b!=0)
            values['sunlit_to_non_sunlit'] += int(losses.sum())
            name = cell['source_tile']
            old, new = old_solar[name],new_solar[name]
            if any(old[k]!=new[k] for k in ('reference','direction_deg','apparent_elevation_deg')):
                raise RuntimeError('Owning-tile solar reference changed')
            elevation = new['apparent_elevation_deg']
            thresholds[name] = dict(old_threshold_deg=old['threshold_deg'],new_threshold_deg=new['threshold_deg'])
            raised = old['threshold_deg'] < elevation <= new['threshold_deg']
            distant = losses & (bq==3) & raised
            values['explained_by_raised_threshold'] += int(distant.sum())
            needed = losses & ~distant
            if not needed.any():
                continue
            raster, _ = entry_paths(cache,new['spatial_key'],new['direction_deg'])
            with rasterio.open(raster) as ds:
                horizon, distance = ds.read([1,3])
            rr, cc = np.nonzero(needed)
            row = rr+round((cell['native_bounds'][3]-cell['bounds'][3])/res)
            col = cc+round((cell['bounds'][0]-cell['native_bounds'][0])/res)
            ar = round(-cell['native_bounds'][3]/res)+row
            ac = round(cell['native_bounds'][0]/res)+col
            dr = -math.cos(math.radians(new['direction_deg']))
            dc = math.sin(math.radians(new['direction_deg']))
            if abs(dr)<1e-14: dr=0
            if abs(dc)<1e-14: dc=0
            d = distance[row,col].astype(np.float64)
            br = ar+np.rint(ar%2+dr*d/res).astype(np.int64)-ar%2
            bc = ac+np.rint(ac%2+dc*d/res).astype(np.int64)-ac%2
            codes = blocker_classes(br,bc)
            with rasterio.open(Path(view)/'tiles'/name) as ds:
                z = ds.read(1)[row,col]
            angle = np.rad2deg(np.arctan((np.float32(doc['profile']['h_sea_m'])-z)/np.maximum(d,.25)))
            proven = (codes>=1) & (codes<=4) & (d>0) & (b[rr,cc]==1) & (angle>elevation)
            proven &= np.abs(angle-horizon[row,col])<=1e-4
            values['explained_by_filled_blocker'] += int(proven.sum())
            values['unexplained_sunlit_loss'] += int((~proven).sum())
            for k in np.flatnonzero(proven)[:3]:
                if len(examples)<24:
                    examples.append(dict(utc=after['utc_time'],tile=name,row=int(row[k]),col=int(col[k]),
                                         blocker_absolute_row=int(br[k]),blocker_absolute_col=int(bc[k]),
                                         surface_class=int(codes[k]),distance_m=float(d[k]),blocker_angle_deg=float(angle[k]),
                                         apparent_elevation_deg=elevation))
        frames.append(dict(time=after['time'],utc_time=after['utc_time'],**values,raw_255_observed_to_shade=former))
    passed = all(f['shaded_to_sunlit']==f['unexplained_sunlit_loss']==0 for f in frames)
    return dict(raw_identity=reference.run_id,sea_run_id=candidate.run_id,frames=frames,thresholds=thresholds,
                filled_blocker_examples=examples,passed=passed)


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



def rays(run, view, *, water):
    doc = read_manifest(view)
    work = v1.ROOT/'outputs/shade_map_work'/(run.manifest['name']+'-'+run.run_id[:12])
    sidecar_path = work/'adapter/region_request.json'
    if digest(sidecar_path)!=run.manifest['adapter_sidecar_sha256']:
        raise RuntimeError('F adapter sidecar hash differs')
    records = v1.index_sources(read_json(sidecar_path)['source_directory'])
    selected = [f for f in run.frames if f['time'] in ('0800','1230','1600')]
    if len(selected)!=3:
        raise RuntimeError('Ray check requires 08:00, 12:30 and 16:00 HKT')
    rng = np.random.default_rng(20261106)
    groups = ('water',) if water else ('filled_3_or_4','observed_within_50m')
    samples = {f['time']:{name:[] for name in groups} for f in selected}
    for cell in run.manifest['cells']:
        name = cell['source_tile']
        record = next(r for r in records if Path(r['path']).name==name)
        grid = tile_grid(record)
        halo = math.ceil(1000/grid.res)
        region = (-halo,-halo,grid.width+2*halo,grid.height+2*halo)
        dsm = read_window(records,grid,region)
        origin_row, origin_col = canonical_origin(grid,region)
        target = dsm[halo:halo+grid.height,halo:halo+grid.width]
        threshold = math.degrees(math.atan(max(0.,float(np.nanmax(dsm))-float(np.nanmin(target)))/1000))
        left,bottom,right,top = cell['bounds']
        row = round((grid.bounds()[3]-top)/grid.res)
        col = round((left-grid.bounds()[0])/grid.res)
        h, w = cell['height'],cell['width']
        pad = round(50/grid.res)
        expanded = [left-50,bottom-50,right+50,top+50]
        expanded_surface = read_surface_window(view,expanded,manifest=doc)
        core = (slice(pad,pad+h),slice(pad,pad+w))
        surface = expanded_surface[core]

        def sample(mask, count):
            flat = np.flatnonzero(mask)
            chosen = rng.choice(flat,size=min(count,len(flat)),replace=False)
            return np.column_stack(np.unravel_index(chosen,mask.shape))

        if water:
            z = dsm[halo+row-pad:halo+row+h+pad,halo+col-pad:halo+col+w+pad]
            tall = (expanded_surface==0)&(z>=10)
            near = distance_transform_edt(~tall)[core]*grid.res<=8 if tall.any() else np.zeros(surface.shape,bool)
            eligible = (surface==1)|(surface==2)
            selections = {'water':np.concatenate([sample(eligible&near,40),sample(eligible&~near,240)])}
        else:
            filled = (expanded_surface>=1)&(expanded_surface<=4)
            near = distance_transform_edt(~filled)[core]*grid.res<=50 if filled.any() else np.zeros(surface.shape,bool)
            selections = {'filled_3_or_4':np.concatenate([sample(surface==3,220),sample(surface==4,220)]),
                          'observed_within_50m':sample((surface==0)&near,240)}
        for frame in selected:
            solar = next(s for s in run.solar(frame) if s['source_name']==name)
            if not math.isclose(solar['threshold_deg'],threshold,abs_tol=1e-10):
                raise RuntimeError('Direct-ray owning-tile threshold differs')
            shade, quality = run.layers(frame,cell)
            elevation = solar['apparent_elevation_deg']
            for group, coordinates in selections.items():
                if not len(coordinates):
                    continue
                rr, cc = coordinates.T
                h_ref, support = independent_rays(dsm,rr+halo+row,cc+halo+col,solar['direction_deg'],
                        origin_row=origin_row,origin_col=origin_col,resolution=grid.res)
                labels, flags = reference_labels(h_ref,support,elevation,threshold)
                for i,(r,c) in enumerate(coordinates):
                    actual, actual_quality = int(shade[r,c]),int(quality[r,c])
                    equality = min(abs(float(h_ref[i])-elevation),abs(threshold-elevation))<=1e-4
                    samples[frame['time']][group].append(dict(
                        tile=name,row=int(r+row),col=int(c+col),surface=int(surface[r,c]),
                        near_tall_structure=bool(water and near[r,c]),horizon_deg=float(h_ref[i]),
                        actual=[actual,actual_quality],reference=[int(labels[i]),int(flags[i])],
                        equality_neighbourhood=equality))
    frames = []
    for time, by_group in samples.items():
        output = {}
        for name, rows in by_group.items():
            mismatches = [r for r in rows if r['actual']!=r['reference']]
            output[name] = dict(samples=len(rows),near_tall_structure=sum(r['near_tall_structure'] for r in rows),
                                surface_counts=dict(Counter(str(r['surface']) for r in rows)),
                                mismatches=len(mismatches),
                                mismatches_outside_equality=sum(not r['equality_neighbourhood'] for r in mismatches),
                                sample_sha256=identity(rows),examples=rows[:4],mismatch_examples=mismatches[:12])
        frames.append(dict(time=time,groups=output))
    passed = all(g['samples']>=200 and g['mismatches_outside_equality']==0 and
                 (not water or g['near_tall_structure']>0) for f in frames for g in f['groups'].values())
    return dict(run_id=run.run_id,view_id=doc['view_id'],frames=frames,passed=passed,seed=20261106,
                method='Independent NumPy rays, canonical 0.25 m steps and ties to even, 1 km radial cutoff',
                near_tall_structure='water within 8 m of observed DSM height >= 10 m',
                equality_tolerance_deg=1e-4,observational_accuracy='NOT VERIFIED')
