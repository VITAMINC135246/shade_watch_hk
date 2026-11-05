"""Scope-limited counterfactual; its rasters are diagnostics, never F results."""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
import csv
import fcntl
from pathlib import Path
import shutil
import sqlite3
import tempfile

import numpy as np
import rasterio
from rasterio.transform import from_bounds

from src import v1, v2
from src.spatial import intersects
from tools import region_request as adapter
from tools.shade_map.common import CODE_ROOT, ENGINE_FILES, atomic_json, digest, identity, read_json
from tools.shade_map.config import ROOT_MARKER, InvalidInput, machine_config, region_config, validate_schema
from tools.shade_map.runner import verify_run
from .build import write_raster
from .provider import SeaSource
from .view import manifest_identity, read_manifest, read_surface_window

COUNTS=('void_pixels','void_caused','other_quality2','quality3','sunlit','shaded','quality4')
SPLITS=('void_caused_sunlit','void_caused_shaded','void_caused_quality3')


def frame_metrics(surface,shade,quality,cf_shade,cf_quality):
    if len({a.shape for a in (surface,shade,quality,cf_shade,cf_quality)})!=1:
        raise RuntimeError('Void-impact raster shapes differ')
    for labels,flags in ((shade,quality),(cf_shade,cf_quality)):
        if not np.array_equal(labels==255,flags!=0):
            raise RuntimeError('Void-impact shade/quality do not partition valid labels')
    observed=surface==0; void=surface==255
    land=int(np.count_nonzero(observed|void))
    caused=observed & (quality==2) & (cf_quality!=2)
    masks=dict(void_pixels=void,void_caused=caused,
               other_quality2=observed & (quality==2) & (cf_quality==2),
               quality3=observed & (quality==3),sunlit=observed & (shade==0),
               shaded=observed & (shade==1),quality4=observed & (quality==4),
               void_caused_sunlit=caused & (cf_shade==0),
               void_caused_shaded=caused & (cf_shade==1),
               void_caused_quality3=caused & (cf_quality==3))
    values={k:int(np.count_nonzero(v)) for k,v in masks.items()}
    if sum(values[k] for k in COUNTS)!=land or sum(values[k] for k in SPLITS)!=values['void_caused']:
        raise RuntimeError('Void-impact categories do not partition the whole land domain')
    return dict(land_pixels=land,counts=values,
                fractions={k:v/land if land else 0.0 for k,v in values.items()},
                void_attributable_fraction=(values['void_pixels']+values['void_caused'])/land if land else 0.0)


def require_run(machine,region):
    machine=machine_config(machine); region=region_config(region)
    if region['dsm_source']!='sea-2.0':
        raise InvalidInput('void-impact requires a complete matching sea-2.0 F run')
    folder=Path(machine['output_root'])/region['name']
    try:
        manifest=read_json(folder/'run_manifest.json')
    except (OSError,ValueError) as exc:
        raise InvalidInput('void-impact requires a complete matching sea-2.0 F run; run F first') from exc
    source=SeaSource(); source.catalogue(machine)
    if (manifest.get('status')!='complete' or manifest.get('region_config')!=region
            or manifest.get('source_identity')!=source.preview_identity(region,machine)
            or manifest.get('policies')!=source.policies()
            or manifest.get('engine_hashes')!={p:digest(CODE_ROOT/p) for p in ENGINE_FILES}):
        raise InvalidInput('void-impact: F run is incomplete or does not match the region/current sea view')
    verify_run(folder,manifest)
    marker=Path(machine['output_root'])/ROOT_MARKER
    if marker.is_symlink() or not marker.is_file() or read_json(marker)!={'schema':'shade-map-root-1.0'}:
        raise InvalidInput('void-impact: output_root must be owned by F')
    return machine,region,folder,manifest,source


def counterfactual_view(view,run):
    view=Path(view); base=read_manifest(view); grid=base['grid']
    halos=[[c['native_bounds'][0]-1000,c['native_bounds'][1]-1000,
            c['native_bounds'][2]+1000,c['native_bounds'][3]+1000] for c in run['cells']]
    cells=[c for c in base['cells'] if any(intersects(c['native_bounds'],h) for h in halos)]
    root=v1.ROOT/'data/processed/dsm_views/sea_voidfill_v2_diagnostic'
    if root.is_symlink(): raise InvalidInput('diagnostic view namespace cannot be a symlink')
    root.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.diagnostic-',dir=root)); (stage/'tiles').mkdir()
    try:
        tiles=[]; changed=0
        for cell in cells:
            filename=cell['tile_name']; name=filename or 'VOID_'+cell['id']+'.tif'
            source=view/'tiles'/filename if filename else None
            if source is None and not cell['counts']['255']: continue
            with rasterio.open(view/'surface'/cell['surface_name']) as ds: surface=ds.read(1)
            shape=(grid['cell_height'],grid['cell_width'])
            if list(cell['bounds'])!=list(cell['native_bounds']):
                full=np.full(shape,254,np.uint8)
                row=round((cell['native_bounds'][3]-cell['bounds'][3])/grid['resolution'])
                col=round((cell['bounds'][0]-cell['native_bounds'][0])/grid['resolution'])
                full[row:row+surface.shape[0],col:col+surface.shape[1]]=surface
                surface=full
            if source:
                with rasterio.open(source) as ds:
                    data=ds.read(1); transform=ds.transform; crs=ds.crs; nodata=ds.nodata; options=ds.profile; tags=ds.tags()
                original_hash=digest(source)
            else:
                data=np.full(shape,grid['nodata'],np.float32)
                transform=from_bounds(*cell['native_bounds'],shape[1],shape[0]); crs=grid['crs']; nodata=grid['nodata']; options=None; tags={}
                original_hash=None
            mask=surface==255; output=stage/'tiles'/name
            if mask.any():
                before=data.view(np.uint32).copy()
                data[mask]=np.float32(base['profile']['h_sea_m'])
                write_raster(output,data,transform,crs,nodata,source_profile=options,tags=tags)
                with rasterio.open(output) as ds: actual=ds.read(1)
                if not np.array_equal(actual.view(np.uint32)[~mask],before[~mask]) or not np.all(actual[mask]==np.float32(base['profile']['h_sea_m'])):
                    raise RuntimeError('Counterfactual differs outside class 255')
                changed+=int(mask.sum())
            else:
                output.symlink_to(source.resolve())
            tiles.append(dict(name=name,cell=cell['id'],source_sha256=original_hash,
                              output_sha256=digest(output),filled_void_pixels=int(mask.sum()),
                              bounds=cell['native_bounds']))
        doc=dict(schema='sea-voidfill-diagnostic-view-2.0',diagnostic=True,
                 policy='SW-SEA-VOIDFILL-DIAGNOSTIC-2.0',parent_view_id=base['view_id'],
                 profile=base['profile'],profile_sha256=base['profile_sha256'],grid=grid,
                 scope_halos=halos,tiles=tiles,filled_void_pixels=changed)
        doc['view_id']=manifest_identity(doc); atomic_json(stage/'manifest.json',doc)
        final=root/doc['view_id']
        if final.exists():
            if read_manifest(final)!=doc: raise RuntimeError('Diagnostic view manifest changed')
            for tile in tiles:
                if digest(final/'tiles'/tile['name'])!=tile['output_sha256']: raise RuntimeError('Diagnostic view hash changed')
        else:
            stage.rename(final)
        return final,doc
    finally:
        if stage.exists(): shutil.rmtree(stage)


@contextmanager
def diagnostic_lock(root,name):
    if root.is_symlink() or not root.resolve().is_relative_to((v1.ROOT/'outputs').resolve()):
        raise InvalidInput('void-impact: diagnostic work must stay inside its repository namespace')
    locks=root/'.locks'; locks.mkdir(parents=True,exist_ok=True)
    with (locks/(name+'.lock')).open('a') as stream:
        try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise InvalidInput('void-impact: another diagnostic owns the lock') from exc
        try: yield
        finally: fcntl.flock(stream,fcntl.LOCK_UN)


def run_counterfactual(machine,region,run,view,doc,work):
    owner=dict(schema='sea2-diagnostic-work-1.0',name=region['name'],policy_run_id=run['run_id'],view_id=doc['view_id'])
    if work.exists():
        if work.is_symlink() or read_json(work/'owner.json')!=owner:
            raise InvalidInput('void-impact: diagnostic work ownership differs')
    else:
        work.mkdir(parents=True); atomic_json(work/'owner.json',owner)
    plans_path=work/'batch_plans.json'; sidecar_path=work/'region_request.json'
    if not run['frames']:
        sidecar=dict(time_groups=[],batches=[])
        atomic_json(sidecar_path,sidecar);atomic_json(plans_path,[])
        atomic_json(work/'execution.json',[])
        return sidecar,[],[]
    if plans_path.exists():
        plans=[v2.BatchPlan(**p) for p in read_json(plans_path)]
        sidecar=read_json(sidecar_path)
    else:
        adapted=adapter.plan_region(region['lower_left'],region['upper_right'],crs=region['crs'],
                    instants=[f['local_time'] for f in run['frames']],dsm_dir=view/'tiles',auto_source_view=True,
                    output_dir=work/'engine',cache_dir=v1.ROOT/'data/processed/shade_v1'/('sea_voidfill_v2_diagnostic_'+doc['view_id'][:12]),
                    memory_budget_mb=min(machine['memory_budget_mb'],8192))
        plans=[]
        for payload in adapted['batches']:
            payload.update(workers=machine['workers'],memory_budget_mb=machine['memory_budget_mb'],logical_mosaic=True,statistics=False)
            plans.append(v2.plan_batch(**payload))
        sidecar=adapted['sidecar']
        for record,plan in zip(sidecar['batches'],plans):
            record.update(id=plan.id,estimate=plan.estimate,resources=plan.definition['resources'])
        if {t for g in sidecar['time_groups'] for t in g['utc_times']}!={f['utc_time'] for f in run['frames']}:
            raise RuntimeError('Counterfactual frames differ from the policy run')
        atomic_json(sidecar_path,sidecar)
        atomic_json(plans_path,[p.to_dict() for p in plans])
    state=work/'state'; events=[]
    for plan in plans:
        previous=None
        if (state/'state.sqlite').exists():
            with sqlite3.connect('file:'+str(state/'state.sqlite')+'?mode=ro',uri=True) as db:
                previous=db.execute('SELECT state FROM batches WHERE id=?',(plan.id,)).fetchone()
        if previous is None:
            v2.submit_batch(plan,state_dir=state); result=v2.run_batch(plan.id,state_dir=state); action='submit_run'
        else:
            result=v2.status_batch(plan.id,state_dir=state); action='verify'
            if result['state']!='SUCCEEDED': result=v2.resume_batch(plan.id,state_dir=state); action='resume'
        events.append(dict(id=plan.id,action=action,state=result['state']))
        atomic_json(work/'execution.json',events)
        if result['state']!='SUCCEEDED': raise RuntimeError('Counterfactual V2 batch did not complete: '+str(result.get('failures')))
    return sidecar,[state/(p.id+'.logical_mosaic.json') for p in plans],events


def void_impact(machine,region):
    machine,region,folder,run,source=require_run(machine,region)
    before={str(p.relative_to(folder)):(p.stat().st_size,p.stat().st_mtime_ns) for p in folder.rglob('*') if p.is_file()}
    catalogue=source.catalogue(machine); view=catalogue.parent
    work_root=v1.ROOT/'outputs/sea2_diagnostic_work'
    with diagnostic_lock(work_root,region['name']):
        diagnostic,doc=counterfactual_view(view,run)
        work=work_root/(region['name']+'-'+doc['view_id'][:12])
        sidecar,mosaics,events=run_counterfactual(machine,region,run,diagnostic,doc,work)
        frames=[]; by_date=defaultdict(list)
        for frame in run['frames']:
            totals=None
            for cell in run['cells']:
                bounds=cell['bounds']; prefix=folder/frame['date']/frame['time']
                with rasterio.open(prefix/'shade'/(cell['id']+'.tif')) as ds: shade=ds.read(1)
                with rasterio.open(prefix/'quality'/(cell['id']+'.tif')) as ds: quality=ds.read(1)
                surface=read_surface_window(view,bounds)
                cf,cq,_=adapter.read_region_window(sidecar,utc_time=frame['utc_time'],bounds=bounds,logical_mosaics=mosaics)
                value=frame_metrics(surface,shade,quality,cf,cq)
                if totals is None: totals=dict(land_pixels=0,counts={k:0 for k in (*COUNTS,*SPLITS)})
                totals['land_pixels']+=value['land_pixels']
                for k,n in value['counts'].items(): totals['counts'][k]+=n
            land=totals['land_pixels']; counts=totals['counts']
            result=dict(date=frame['date'],time=frame['time'],utc_time=frame['utc_time'],**totals,
                        fractions={k:n/land if land else 0.0 for k,n in counts.items()},
                        void_attributable_fraction=(counts['void_pixels']+counts['void_caused'])/land if land else 0.0)
            frames.append(result); by_date[frame['date']].append(result['void_attributable_fraction'])
        report=dict(schema='void-impact-1.0',diagnostic=True,name=region['name'],policy_run_id=run['run_id'],
                    sea_view_id=run['source_identity']['view_id'],counterfactual_view_id=doc['view_id'],
                    counterfactual_filled_void_pixels=doc['filled_void_pixels'],frames=frames,
                    dates=[dict(date=day,frames=len(values),mean_void_attributable_fraction=float(np.mean(values)),
                                exceeds_10_percent=bool(np.mean(values)>.1)) for day,values in sorted(by_date.items())])
        schema=read_json(Path(__file__).resolve().parents[2]/'config/schema/void_impact.schema.json')
        validate_schema(report,schema)
        destination=Path(machine['output_root'])/'_diagnostics/void_impact'/region['name']
        output_root=Path(machine['output_root']).resolve()
        if not destination.resolve().is_relative_to(output_root) or any(p.is_symlink() for p in (destination,destination.parent,destination.parent.parent)):
            raise InvalidInput('void-impact: report directory must stay inside output_root without symlinks')
        if (destination/'void_impact.json').exists() and read_json(destination/'void_impact.json').get('policy_run_id')!=run['run_id']:
            raise InvalidInput('void-impact: existing report belongs to another policy run')
        destination.mkdir(parents=True,exist_ok=True)
        atomic_json(destination/'void_impact.json',report)
        fields=['date','time','utc_time','land_pixels',*COUNTS,*SPLITS,*[k+'_fraction' for k in (*COUNTS,*SPLITS)],'void_attributable_fraction']
        with (destination/'void_impact.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
            for frame in frames:
                writer.writerow({**{k:frame[k] for k in ('date','time','utc_time','land_pixels','void_attributable_fraction')},
                                 **frame['counts'],**{k+'_fraction':n for k,n in frame['fractions'].items()}})
        after={str(p.relative_to(folder)):(p.stat().st_size,p.stat().st_mtime_ns) for p in folder.rglob('*') if p.is_file()}
        if before!=after: raise RuntimeError('Void-impact wrote inside the original F run')
        verify_run(folder,run)
        return dict(schema='sea2-diagnostic-result-1.0',report=str(destination/'void_impact.json'),
                    diagnostic_view=str(diagnostic),work=str(work),frames=len(frames),events=events,dates=report['dates'])
