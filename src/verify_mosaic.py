"""Real six-tile QA against a single-region reference (bounded demonstration)."""
import argparse
from pathlib import Path
import json
import time
import numpy as np
import rasterio
from rasterio.windows import Window
from .spatial import Grid, cores, digest_file
from .pipeline import calculate_core, profile, atomic_json, cache_paths, memory_monitor
from .shade_watch import ROOT, classify, nearest_bin

DIRECTIONS = [115, 180, 215, 225]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['reference','compare'])
    parser.add_argument('--production', type=Path, required=True)
    args = parser.parse_args()
    out = (ROOT/args.production).resolve()
    definition = json.loads((out/'run_definition.json').read_text())
    grid = Grid(**definition['identity']['grid'])
    records = definition['identity']['sources']
    qa = out/'qa'; qa.mkdir(exist_ok=True)
    start = time.perf_counter()
    # Intentionally limited to this small demonstration: production remains windowed.
    if grid.width*grid.height > 12_000_000:
        raise ValueError('Single-region QA limited to 12 million output pixels')
    if args.action == 'reference':
        with memory_monitor() as memory:
            for az in DIRECTIONS:
                core = (0,0,grid.width,grid.height)
                arrays = calculate_core(records,grid,core,az)
                path = qa/f'single_region_{az}.tif'
                with rasterio.open(path.with_suffix('.tmp.tif'),'w',**profile(grid,core,3,'float32',None)) as ds:
                    for band, array in enumerate(arrays,1):
                        ds.write(array.astype(np.float32,copy=False),band)
                    ds.update_tags(production_identity=definition['key'])
                path.with_suffix('.tmp.tif').replace(path)
                del arrays
                print(f'Single-region reference {az} complete',flush=True)
        atomic_json(qa/'reference.json',dict(directions=DIRECTIONS,seconds=time.perf_counter()-start,**memory,
            note='One full-region task solely for this bounded real-data equality reference; not the production memory model'))
        return
    run = json.loads((out/'result_inventory.json').read_text())
    cache = Path(run['cache_directory'])
    size = (run['core_layout']['width_px'],run['core_layout']['height_px'])
    errors = dict(horizon=0,support=0,blocker=0,labels=0,quality=0,validity=0)
    pixels = actual_pixels = 0
    max_delta = 0.
    times = set()
    source_matches = all(digest_file(r['path']) == r['sha256'] for r in records)
    assert source_matches
    with memory_monitor() as memory:
        for az in DIRECTIONS:
            with rasterio.open(qa/f'single_region_{az}.tif') as reference:
                assert reference.tags()['production_identity'] == definition['key']
                for core in cores(grid,size):
                    ref = reference.read(window=Window(*core))
                    hp,_ = cache_paths(cache,core,az)
                    with rasterio.open(hp) as ds:
                        got = ds.read()
                    for i,name in enumerate(('horizon','support','blocker')):
                        equal = (ref[i] == got[i]) | (np.isnan(ref[i]) & np.isnan(got[i]))
                        errors[name] += int(np.count_nonzero(~equal))
                    valid = np.isfinite(ref[0]) & np.isfinite(got[0])
                    if valid.any():
                        max_delta = max(max_delta,float(np.abs(ref[0][valid]-got[0][valid]).max()))
                    for elevation in [.1,5.,20.,45.,65.]:
                        a = classify(ref[0],ref[1].astype(bool),np.isfinite(ref[0]),elevation,run['distant_threshold_deg'])
                        b = classify(got[0],got[1].astype(bool),np.isfinite(got[0]),elevation,run['distant_threshold_deg'])
                        errors['labels'] += int(np.count_nonzero(a[0] != b[0]))
                        errors['quality'] += int(np.count_nonzero(a[1] != b[1]))
                        errors['validity'] += int(np.count_nonzero((a[0] != 255) != (b[0] != 255)))
                    for frame in run['frames']:
                        if nearest_bin(frame['azimuth_deg']) != az:
                            continue
                        expected = classify(ref[0],ref[1].astype(bool),np.isfinite(ref[0]),frame['apparent_elevation_deg'],run['distant_threshold_deg'])
                        with rasterio.open(frame['raster']) as ds:
                            labels = ds.read(1,window=Window(*core))
                        with rasterio.open(frame['quality_raster']) as ds:
                            flags = ds.read(1,window=Window(*core))
                        errors['labels'] += int(np.count_nonzero(expected[0] != labels))
                        errors['quality'] += int(np.count_nonzero(expected[1] != flags))
                        errors['validity'] += int(np.count_nonzero((expected[0] != 255) != (labels != 255)))
                        actual_pixels += core[2]*core[3]
                        times.add(frame['local_time'])
                    pixels += core[2]*core[3]
            print(f'{az}: cumulative differences {errors}',flush=True)
    result = dict(directions=DIRECTIONS,spatial_tasks=len(list(cores(grid,size))),differences=errors,
        max_horizon_difference_deg=max_delta,pixel_direction_pairs=pixels,
        tested_elevations_deg=[.1,5,20,45,65],actual_frames_checked=sorted(times),actual_frame_pixel_pairs=actual_pixels,
        all_source_hashes_unchanged=source_matches,seconds=time.perf_counter()-start,**memory)
    atomic_json(qa/'comparison.json',result)
    if any(errors.values()):
        raise AssertionError(errors)


if __name__ == '__main__':
    main()
