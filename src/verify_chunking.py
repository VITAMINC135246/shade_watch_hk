"""Reproducible real-input numerical QA; no observational accuracy claims."""
import argparse
from dataclasses import asdict, replace
from datetime import datetime
import json
import math
from pathlib import Path
import time
import numpy as np
import rasterio
from rasterio.windows import Window
from .spatial import inventory,target_grid,cores,region_stats,expand,read_window,Grid,digest_file
from .pipeline import (calculate_core,memory_monitor,atomic_json,profile,cache_paths,
                       process_core, fingerprint)
from .shade_watch import ROOT,RAW,load_study_area,classify,nearest_bin
from .solar import HKT,position,daylight_bounds,daylight_samples

QA=ROOT/'outputs/chunking_qa_20260928'


def benchmark(size, repeats):
    records=inventory(RAW.glob('*.tif')); study=load_study_area()
    base=target_grid(records,study)
    grid=replace(base,width=size*repeats,height=size,mode='benchmark')
    t=time.perf_counter()
    with memory_monitor() as memory:
        # Full core, real available DSM, one direction; missing outer area stays NaN.
        for core in cores(grid,size):
            arrays=calculate_core(records,grid,core,225)
            del arrays
    result=dict(core_size=size,chunks=repeats,total_pixels=grid.width*grid.height,
                direction=225,seconds=time.perf_counter()-t,**memory,
                note='One azimuth over available real DSM; missing cells cost less than covered cells. Independent fresh process.')
    atomic_json(QA/f'benchmark_{size}_{repeats}.json',result)
    print(json.dumps(result),flush=True)


def reference(mode):
    records=inventory(RAW.glob('*.tif'));study=load_study_area()
    grid=target_grid(records,study,'custom' if mode=='multi' else mode,
                     900 if mode=='multi' else 600,700 if mode=='multi' else 450)
    whole=(0,0,grid.width,grid.height)
    stats=region_stats(records,grid,whole);buff=region_stats(records,grid,expand(whole,2000))
    threshold=math.degrees(math.atan(max(0,buff['max_m']-stats['min_m'])/1000))
    sunrise,sunset=daylight_bounds(study['date'],study['latitude'],study['longitude'])
    times=daylight_samples(sunrise,sunset,10)
    azimuths=sorted({nearest_bin(position(t,study['latitude'],study['longitude']).azimuth_deg) for t in times}) if mode=='native_tile' else [115,180,225]
    folder=QA/mode;folder.mkdir(parents=True,exist_ok=True)
    identity=fingerprint(dict(grid=asdict(grid),sources=records,algorithm=digest_file(ROOT/'src/horizon.py')))
    for az in azimuths:
        path=folder/f'reference_{az}.tif'
        if path.exists():
            with rasterio.open(path) as ds:
                if ds.tags().get('identity')==identity:
                    continue
        t=time.perf_counter()
        with memory_monitor() as memory:
            ref=calculate_core(records,grid,whole,az)
            tmp=path.with_suffix('.tmp.tif')
            with rasterio.open(tmp,'w',**profile(grid,whole,3,'float32',None)) as ds:
                for band,array in enumerate(ref,1): ds.write(array.astype(np.float32),band)
                ds.update_tags(identity=identity)
            tmp.replace(path);del ref
        print(f'{mode}: single-region reference {az}° {time.perf_counter()-t:.1f}s, RSS {memory["peak_rss_bytes"]/1e6:.1f} MB',flush=True)
    atomic_json(folder/'definition.json',dict(grid=asdict(grid),threshold=threshold,azimuths=azimuths,identity=identity,
                                             surface=stats,buffered=buff))


def compare(mode,size,production=None,azimuths=None):
    folder=QA/mode;definition=json.loads((folder/'definition.json').read_text())
    if azimuths is not None:
        if not set(azimuths).issubset(definition['azimuths']): raise ValueError('Missing reference directions')
        definition['azimuths']=azimuths
    grid=Grid(**definition['grid']);records=inventory(RAW.glob('*.tif'))
    errors=dict(horizon=0,support=0,blocker=0,labels=0,quality=0,validity=0)
    max_delta=0.;pixels=0;t=time.perf_counter()
    if production:
        run=json.loads((ROOT/production/'result_inventory.json').read_text())
        cache=Path(run['cache_directory'])
        layout=run.get('core_layout')
        size=(layout['width_px'],layout['height_px']) if layout else run['config']['core_size_px']
    with memory_monitor() as memory:
        for az in definition['azimuths']:
            with rasterio.open(folder/f'reference_{az}.tif') as ds:
                for core in cores(grid,size):
                    ref=ds.read(window=Window(*core))
                    if production:
                        hp,_=cache_paths(cache,core,az)
                        with rasterio.open(hp) as hd: got=hd.read()
                    else:
                        got=np.stack(calculate_core(records,grid,core,az))
                    for i,name in enumerate(('horizon','support','blocker')):
                        equal=(ref[i]==got[i]) | (np.isnan(ref[i])&np.isnan(got[i]))
                        errors[name]+=int(np.count_nonzero(~equal))
                    finite=np.isfinite(ref[0])&np.isfinite(got[0])
                    if np.any(finite): max_delta=max(max_delta,float(np.max(np.abs(ref[0][finite]-got[0][finite]))))
                    for elev in (.1,5.,20.,45.,65.):
                        a=classify(ref[0],ref[1].astype(bool),np.isfinite(ref[0]),elev,definition['threshold'])
                        b=classify(got[0],got[1].astype(bool),np.isfinite(got[0]),elev,definition['threshold'])
                        errors['labels']+=int(np.count_nonzero(a[0]!=b[0]))
                        errors['quality']+=int(np.count_nonzero(a[1]!=b[1]))
                        errors['validity']+=int(np.count_nonzero((a[0]!=255)!=(b[0]!=255)))
                    if production:
                        for frame in run['frames']:
                            if nearest_bin(frame['azimuth_deg']) != az:
                                continue
                            expected=classify(ref[0],ref[1].astype(bool),np.isfinite(ref[0]),
                                              frame['apparent_elevation_deg'],definition['threshold'])
                            with rasterio.open(frame['raster']) as labels_ds, rasterio.open(frame['quality_raster']) as quality_ds:
                                labels=labels_ds.read(1,window=Window(*core));quality=quality_ds.read(1,window=Window(*core))
                            errors['labels']+=int(np.count_nonzero(expected[0]!=labels))
                            errors['quality']+=int(np.count_nonzero(expected[1]!=quality))
                            errors['validity']+=int(np.count_nonzero((expected[0]!=255)!=(labels!=255)))
                    pixels+=core[2]*core[3]
            print(f'{mode} size {size}: {az}° compared, cumulative differences {sum(errors.values())}',flush=True)
    result=dict(mode=mode,core_size=size,grid=asdict(grid),azimuths=definition['azimuths'],
                pixel_direction_pairs=pixels,elevations=[.1,5,20,45,65],differences=errors,
                production_daylight_frames_checked=len(run['frames']) if production else 0,
                max_horizon_difference_deg=max_delta,tolerance_deg=0,seconds=time.perf_counter()-t,**memory)
    size_label=f'{size[0]}x{size[1]}' if isinstance(size, (tuple,list)) else str(size)
    atomic_json(folder/f'comparison_{size_label}.json',result)
    if any(errors.values()): raise AssertionError(result)


def distance_change():
    """Same grid/input/rounding; only ray distance changes, separate from chunk QA."""
    study=load_study_area();records=inventory(RAW.glob('*.tif'))
    grid=target_grid(records,study,'custom');core=(0,0,grid.width,grid.height)
    definition=json.loads((QA/'custom/definition.json').read_text())
    halo=2000;region=expand(core,halo);dsm=read_window(records,grid,region)
    rr,cc=np.indices((grid.height,grid.width),np.int32);rr+=halo;cc+=halo
    from .horizon import pixel_centred_horizon
    results=[]
    for hour,minute in ((7,10),(14,30),(17,50)):
        instant=datetime(2026,1,7,hour,minute,tzinfo=HKT)
        sun=position(instant,study['latitude'],study['longitude']);az=nearest_bin(sun.azimuth_deg)
        values=[]
        for distance in (1000,1500):
            h,s,_=pixel_centred_horizon(dsm,rr.ravel(),cc.ravel(),az,distance,1000,.5,-halo,-halo)
            values.append((h.reshape(grid.height,grid.width),s.reshape(grid.height,grid.width)))
        a,b=[classify(h,s.astype(bool),np.isfinite(h),sun.apparent_elevation_deg,definition['threshold']) for h,s in values]
        finite=np.isfinite(values[0][0])&np.isfinite(values[1][0])
        result=dict(azimuth=az,time=instant.isoformat(),elevation_deg=sun.apparent_elevation_deg,
                    horizon_changed_pixels=int(np.count_nonzero(values[0][0][finite]!=values[1][0][finite])),
                    max_horizon_difference_deg=float(np.max(np.abs(values[0][0][finite]-values[1][0][finite]))),
                    labels_changed=int(np.count_nonzero(a[0]!=b[0])),quality_changed=int(np.count_nonzero(a[1]!=b[1])))
        old=ROOT/'outputs/600x450/rasters'/f'shade_{instant:%Y%m%d_%H%M}_HKT.tif'
        with rasterio.open(old) as ds: legacy=ds.read(1)
        result['new_vs_preserved_legacy_labels_changed']=int(np.count_nonzero(a[0]!=legacy))
        results.append(result);print(json.dumps(result),flush=True)
    atomic_json(QA/'distance_change.json',dict(grid=asdict(grid),frames=results,
                note='Controlled 1000 vs 1500 m search on same 1000 m buffered input; same global sampling and 1000 m support.',
                legacy_note='Historical outputs also used legacy rounding and raster merge; not the chunk equality reference. Three representative times only.'))


def restart_probe():
    import multiprocessing
    records=inventory(RAW.glob('*.tif'));grid=target_grid(records,load_study_area())
    core=(0,0,512,512);azimuths=[115,180,225]
    cache=QA/'interruption_cache';cache.mkdir(parents=True,exist_ok=True)
    for p in cache.glob('*'): p.unlink()
    key='explicit-real-input-interruption-test'
    context=multiprocessing.get_context('spawn')
    worker=context.Process(target=process_core,args=(records,grid,core,azimuths,cache,key,1000,1000))
    worker.start();deadline=time.monotonic()+60
    first,status=cache_paths(cache,core,115)
    while time.monotonic()<deadline:
        if status.exists():
            try:
                if json.loads(status.read_text()).get('status')=='complete': break
            except ValueError: pass
        if not worker.is_alive(): raise RuntimeError('Worker exited before interruption checkpoint')
        time.sleep(.01)
    else: raise RuntimeError('Interruption checkpoint timed out')
    worker.terminate();worker.join(10)
    retained_hash=digest_file(first)
    result=process_core(records,grid,core,azimuths,cache,key,1000,1000)
    assert result['reused']>=1 and digest_file(first)==retained_hash
    differences=0
    for az in azimuths:
        path,_=cache_paths(cache,core,az)
        with rasterio.open(path) as ds: actual=ds.read()
        expected=np.stack(calculate_core(records,grid,core,az))
        differences+=int(np.count_nonzero(~((actual==expected)|(np.isnan(actual)&np.isnan(expected)))))
    assert differences==0
    atomic_json(QA/'actual_interruption.json',dict(exitcode=worker.exitcode,resumed=result,
                                                differences=differences,retained_complete_task_hash=retained_hash))
    print('Actual terminated-process restart: exact agreement; completed task reused',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['benchmark','reference','compare','distance','restart'])
    p.add_argument('--mode',default='native_tile',choices=['native_tile','custom','multi']);p.add_argument('--size',type=int,default=1024)
    p.add_argument('--chunks',type=int,default=1);p.add_argument('--production');p.add_argument('--azimuths',type=int,nargs='+')
    a=p.parse_args();QA.mkdir(parents=True,exist_ok=True)
    if a.action=='benchmark': benchmark(a.size,a.chunks)
    elif a.action=='reference': reference(a.mode)
    elif a.action=='compare': compare(a.mode,a.size,a.production,a.azimuths)
    elif a.action=='restart': restart_probe()
    else: distance_change()

if __name__=='__main__': main()
