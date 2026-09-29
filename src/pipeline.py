"""Bounded task scheduling, date-independent horizon cache, and streaming export."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from dataclasses import asdict
from datetime import timezone
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import platform
import threading
import time
import numpy as np
import psutil
import rasterio
from rasterio.windows import Window
from rasterio.enums import Resampling
from PIL import Image, ImageDraw
import imageio.v2 as imageio
from .spatial import (Grid, cores, core_dimensions, expand, inventory, target_grid, read_window,
                      region_stats, seam_audit, digest_file, GDAL_CACHE_BYTES, native_mosaic_grid, output_reference)
from .horizon import pixel_centred_horizon
from .shade_watch import ROOT, RAW, load_study_area, classify, nearest_bin, _font, SOURCE_LINE, write_binary_png
from .solar import daylight_bounds, daylight_samples, position

EXTERNAL_PIDS = set()
ALGORITHM = 'pixel-centred-1km-global-parity-v1'
NODATA_POLICY = 'nan-missing;known-blocker-proves-shade;complete-ray-required-for-sun;global-low-sun-threshold'


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, default=str)+'\n')
    os.replace(tmp, path)


def include_auxiliary_source_identities(records):
    """External masks/auxiliary metadata are DSM dependencies too."""
    for record in records:
        with rasterio.open(record['path']) as ds:
            files = sorted({str(Path(p).resolve()) for p in ds.files}
                           - {str(Path(record['path']).resolve())})
        if files:
            record['auxiliary_files'] = [dict(path=p, sha256=digest_file(p),
                                             bytes=Path(p).stat().st_size) for p in files]
    return records


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


@contextmanager
def memory_monitor():
    info = {'peak_rss_bytes': 0, 'peak_tree_rss_bytes': 0}
    stop = threading.Event(); proc = psutil.Process()
    def sample():
        while not stop.is_set():
            try:
                rss = proc.memory_info().rss
                info['peak_rss_bytes'] = max(info['peak_rss_bytes'], rss)
                tree = rss
                child_pids = {p.pid for p in multiprocessing.active_children()} | set(EXTERNAL_PIDS)
                for pid in child_pids:
                    try:
                        tree += psutil.Process(pid).memory_info().rss
                    except (psutil.Error, OSError):
                        pass
                info['peak_tree_rss_bytes'] = max(info['peak_tree_rss_bytes'], tree)
            except (psutil.Error, OSError):
                pass
            stop.wait(.02)
    thread = threading.Thread(target=sample, daemon=True); thread.start()
    try:
        yield info
    finally:
        stop.set(); thread.join()


def track_media_process(owner, generator_name, process_name):
    """Monitor known encoder/decoder PIDs without a system-wide process scan.

    ImageIO internals are pinned by requirements.lock.txt; unavailable tracking
    is reported explicitly instead of claiming a complete process-tree measure.
    """
    generator = getattr(owner, generator_name, None)
    frame = getattr(generator, 'gi_frame', None)
    process = frame.f_locals.get(process_name) if frame is not None else None
    pid = getattr(process, 'pid', None)
    if pid:
        EXTERNAL_PIDS.add(pid)
    return pid


def profile(grid, core, count=1, dtype='uint8', nodata=255):
    return dict(driver='GTiff', width=core[2], height=core[3], count=count,
                dtype=dtype, crs=grid.crs, transform=grid.local_transform(core),
                nodata=nodata, tiled=True, blockxsize=256, blockysize=256,
                compress='deflate', BIGTIFF='IF_SAFER')


def cache_paths(cache, core, azimuth):
    c, r, w, h = core
    stem = f'c{c}_r{r}_w{w}_h{h}_az{azimuth:03d}'
    return Path(cache)/f'{stem}.tif', Path(cache)/f'{stem}.json'


def valid_cache(cache, grid, core, azimuth, key):
    path, status = cache_paths(cache, core, azimuth)
    try:
        meta = json.loads(status.read_text())
        if (meta['status'] != 'complete' or meta['key'] != key or meta.get('core') != list(core)
                or meta.get('azimuth_deg') != azimuth or meta['sha256'] != digest_file(path)):
            return False
        with rasterio.open(path) as ds:
            if (ds.count != 3 or ds.shape != (core[3], core[2]) or ds.dtypes != ('float32',)*3
                    or ds.transform != grid.local_transform(core) or ds.crs != rasterio.crs.CRS.from_string(grid.crs)
                    or ds.tags().get('cache_key') != key):
                return False
            for _, win in ds.block_windows(1):
                h, support, distance = ds.read(window=win)
                if (np.any(~np.isin(support, [0, 1])) or np.any(~np.isfinite(distance))
                        or np.any((distance < 0) | (distance > 1000))
                        or np.any(np.isinf(h)) or np.any((h < 0) | (h > 90))):
                    return False
        return True
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError):
        return False


def calculate_core(records, grid, core, azimuth, search_m=1000, buffer_m=1000):
    halo = math.ceil(buffer_m/grid.res)
    region = expand(core, halo)
    dsm = read_window(records, grid, region)
    rr, cc = np.indices((core[3], core[2]), dtype=np.int32)
    rr += halo; cc += halo
    h, s, b = pixel_centred_horizon(dsm, rr.ravel(), cc.ravel(), float(azimuth),
                                  search_m, search_m, grid.res, region[1], region[0])
    return tuple(a.reshape(core[3], core[2]) for a in (h, s, b))


def process_core(records, grid, core, azimuths, cache, key, search_m, buffer_m):
    """Worker owns one core; no scheduling or solar decisions in calculation."""
    start = time.perf_counter(); computed = reused = 0
    with memory_monitor() as memory, rasterio.Env(GDAL_CACHEMAX=GDAL_CACHE_BYTES):
        # Validate first. Restart can skip all input allocations for finished cores.
        missing = []
        for az in azimuths:
            if valid_cache(cache, grid, core, az, key):
                reused += 1
            else:
                missing.append(az)
        if missing:
            halo = math.ceil(buffer_m/grid.res)
            region = expand(core, halo)
            dsm = read_window(records, grid, region)
            rr, cc = np.indices((core[3], core[2]), dtype=np.int32)
            rr += halo; cc += halo
            for az in missing:
                path, status = cache_paths(cache, core, az)
                meta = dict(status='running', key=key, core=core, azimuth_deg=az,
                            grid=asdict(grid), algorithm=ALGORITHM, pid=os.getpid())
                atomic_json(status, meta)
                tmp = path.with_name(path.name+f'.{os.getpid()}.tmp')
                try:
                    t = time.perf_counter()
                    arrays = pixel_centred_horizon(dsm, rr.ravel(), cc.ravel(), float(az),
                                                  search_m, search_m, grid.res, region[1], region[0])
                    with rasterio.open(tmp, 'w', **profile(grid, core, 3, 'float32', None)) as ds:
                        for band, array in enumerate(arrays, 1):
                            ds.write(array.reshape(core[3], core[2]).astype(np.float32, copy=False), band)
                        ds.set_band_description(1, 'known_horizon_degrees')
                        ds.set_band_description(2, 'complete_ray_support_0_or_1')
                        ds.set_band_description(3, 'maximum_blocker_sample_distance_m')
                        ds.update_tags(cache_key=key, algorithm=ALGORITHM, search_m=search_m, buffer_m=buffer_m)
                    del arrays
                    os.replace(tmp, path)
                    meta.update(status='complete', sha256=digest_file(path), seconds=time.perf_counter()-t)
                    atomic_json(status, meta); computed += 1
                except BaseException as exc:
                    meta.update(status='failed', error=repr(exc)); atomic_json(status, meta)
                    tmp.unlink(missing_ok=True)
                    raise
    return dict(core=core, computed=computed, reused=reused, seconds=time.perf_counter()-start, **memory)


def execute(records, grid, size, workers, azimuths, cache, key, search_m=1000, buffer_m=1000):
    """At most workers futures; failures cancel queued work and finish active work before raising."""
    Path(cache).mkdir(parents=True, exist_ok=True)
    jobs = iter(cores(grid, size))
    args = lambda core: (records, grid, core, azimuths, cache, key, search_m, buffer_m)
    if workers == 1:
        for core in jobs:
            yield process_core(*args(core))
        return
    pool = ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context('spawn'))
    pending = set()
    try:
        for _ in range(workers):
            core = next(jobs, None)
            if core is not None:
                pending.add(pool.submit(process_core, *args(core)))
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                yield future.result()
                core = next(jobs, None)
                if core is not None:
                    pending.add(pool.submit(process_core, *args(core)))
    except BaseException:
        for future in pending:
            future.cancel()
        pool.shutdown(wait=True, cancel_futures=True)
        raise
    else:
        pool.shutdown()


def output_valid(path, quality, status, key, grid):
    try:
        meta = json.loads(status.read_text())
        if meta['key'] != key or meta['status'] != 'complete':
            return None
        for p in (path, quality):
            if digest_file(p) != meta['hashes'][p.name]:
                return None
            with rasterio.open(p) as ds:
                if (ds.shape != (grid.height, grid.width) or ds.transform != grid.affine
                        or ds.crs.to_string() != grid.crs or ds.count != 1 or ds.dtypes != ('uint8',)
                        or ds.nodata != (255 if p == path else None)):
                    return None
        return meta
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError):
        return None


def assemble_frame(grid, size, cache, instant, sun, threshold, out, key):
    stamp = instant.strftime('%Y%m%d_%H%M')
    path = out/'rasters'/f'shade_{stamp}_HKT.tif'
    quality = out/'quality'/f'quality_{stamp}_HKT.tif'
    status = out/'status'/f'{stamp}.json'
    frame_key = fingerprint(dict(cache=key, instant=instant.isoformat(), sun=asdict(sun), threshold=threshold))
    prior = output_valid(path, quality, status, frame_key, grid)
    if prior:
        return prior
    for p in (path, quality):
        p.parent.mkdir(parents=True, exist_ok=True)
    temps = [p.with_name(p.name+'.tmp') for p in (path, quality)]
    counts = dict(sunlit=0, shaded=0, invalid_or_uncertain=0)
    qc = {str(i): 0 for i in range(5)}
    atomic_json(status, dict(status='running', key=frame_key))
    try:
        with rasterio.Env(GDAL_CACHEMAX=GDAL_CACHE_BYTES), rasterio.open(temps[0], 'w', **profile(grid, (0,0,grid.width,grid.height))) as dst, rasterio.open(temps[1], 'w', **profile(grid, (0,0,grid.width,grid.height), nodata=None)) as qdst:
            for core in cores(grid, size):
                hp, _ = cache_paths(cache, core, nearest_bin(sun.azimuth_deg))
                with rasterio.open(hp) as ds:
                    horizon, support = ds.read([1, 2])
                labels, flags = classify(horizon, support.astype(bool), np.isfinite(horizon),
                                         sun.apparent_elevation_deg, threshold)
                dst.write(labels, 1, window=Window(*core)); qdst.write(flags, 1, window=Window(*core))
                for name, code in [('sunlit',0), ('shaded',1), ('invalid_or_uncertain',255)]:
                    counts[name] += int(np.count_nonzero(labels == code))
                for i in range(5):
                    qc[str(i)] += int(np.count_nonzero(flags == i))
            dst.update_tags(local_time=instant.isoformat(), utc_time=instant.astimezone(timezone.utc).isoformat(),
                            search_m=1000, buffer_m=1000, lut_azimuth_deg=nearest_bin(sun.azimuth_deg),
                            source_and_owner=SOURCE_LINE, encoding='1=shade,0=sunlit,255=invalid', run_key=key)
            qdst.update_tags(code_0='valid', code_1='DSM NoData', code_2='incomplete 1km ray support',
                             code_3='distant-obstruction sensitivity', code_4='solar centre below horizon')
        for temp, dest in zip(temps, (path, quality)):
            os.replace(temp, dest)
        meta = dict(status='complete', key=frame_key, local_time=instant.isoformat(),
                    utc_time=instant.astimezone(timezone.utc).isoformat(), counts=counts, quality_counts=qc,
                    raster=str(path), quality_raster=str(quality), hashes={p.name:digest_file(p) for p in (path, quality)},
                    **asdict(sun))
        atomic_json(status, meta)
        return meta
    except BaseException as exc:
        atomic_json(status, dict(status='failed', key=frame_key, error=repr(exc)))
        raise


def export_pngs(path, out, grid, size):
    """Full lossless PNG for small regions; bounded georeferenced pieces otherwise."""
    small = grid.width*grid.height <= 4_000_000
    windows = [(0,0,grid.width,grid.height)] if small else cores(grid, size)
    with rasterio.open(path) as ds:
        for core in windows:
            labels = ds.read(1, window=Window(*core))
            suffix = '' if small else f'_c{core[0]}_r{core[1]}'
            dest = out/'png'/f'{path.stem}{suffix}.png'
            temp = dest.with_name(dest.stem+'.tmp.png')
            write_binary_png(temp, labels)
            # Verify each bounded export before publishing.
            with Image.open(temp) as im:
                png = np.asarray(im)
                if not np.array_equal(png[:,:,0], labels) or not np.array_equal(png[:,:,1] == 255, labels != 255):
                    raise ValueError(f'PNG roundtrip failure: {dest}')
            os.replace(temp, dest)
            atomic_json(dest.with_suffix('.json'), dict(crs=grid.crs, transform=tuple(grid.local_transform(core))[:6],
                                                       core=core, encoding='L:0=sunlit,1=shade,255=invalid; A:255=valid,0=invalid'))


def render_frame(path, instant, sun, grid, valid_fraction, sunrise, sunset, max_side):
    factor = min(1., max_side/max(grid.width, grid.height))
    width, height = max(1, round(grid.width*factor)), max(1, round(grid.height*factor))
    with rasterio.open(path) as ds:
        labels = ds.read(1, out_shape=(height, width), resampling=Resampling.nearest)
    grey = np.full(labels.shape, 160, np.uint8)
    grey[labels == 0] = 255; grey[labels == 1] = 0
    canvas_w = math.ceil(max(width+340, 1000)/16)*16
    canvas_h = math.ceil(max(height+180, 650)/16)*16
    image = Image.new('RGB', (canvas_w, canvas_h), 'white'); draw = ImageDraw.Draw(image)
    draw.text((24,16), 'SHADE WATCH HK / HKUST', font=_font(28, True), fill='black')
    draw.text((24,55), instant.strftime('%Y-%m-%d  %H:%M HKT'), font=_font(24, True), fill='black')
    image.paste(Image.fromarray(grey).convert('RGB'), (24,100))
    x = width+48
    lines = ['N ↑', f'{grid.width*grid.res:g} × {grid.height*grid.res:g} m',
             f'{grid.res:g} m scientific pixels', f'{grid.res/factor:.3g} m display pixels',
             'Black: shaded', 'White: sunlit', 'Gray: invalid / uncertain',
             f'Valid: {valid_fraction:.1%}', f'Azimuth: {sun.azimuth_deg:.1f}°',
             f'Elevation: {sun.apparent_elevation_deg:.1f}°', 'Clear-sky DSM surface',
             '1 km search / 1 km buffer']
    if grid.mode == 'native_mosaic':
        lines.append(f'{len(grid.selected_sources)} native tiles joined')
    for i, line in enumerate(lines):
        draw.text((x,106+i*35), line, font=_font(17), fill='black')
    y = canvas_h-65
    draw.text((24,y), f'Daylight {sunrise:%H:%M}–{sunset:%H:%M} HKT | CEDD 2020 LiDAR DSM', font=_font(15), fill='black')
    draw.text((24,y+25), 'Data owner: Government of the Hong Kong Special Administrative Region', font=_font(14), fill='black')
    return image, dict(width=width, height=height, display_pixel_m=grid.res/factor,
                       method='nearest source label; scientific GeoTIFFs and PNGs retain native resolution')


def resolve_core_layout(config, records, study, grid):
    """Native-tile dimensions are the default spatial work unit.

    All cores still reference the one whole-output grid. Exact-centre custom
    outputs keep that grid, rather than snapping to source-file boundaries.
    """
    mode = config.get('core_mode', 'fixed')  # compatibility with saved old configs
    if mode == 'native_tile':
        if grid.mode == 'native_mosaic':
            source_record = next(r for r in records if r['path'] == grid.selected_source)
            dimensions = (source_record['width'], source_record['height'])
            source = source_record['path']
        else:
            native = grid if grid.mode == 'native_tile' else target_grid(records, study, 'native_tile')
            dimensions = (native.width, native.height)
            source = native.selected_source
    elif mode == 'fixed':
        dimensions = core_dimensions(config.get('core_size_px', 1024))
        source = None
    else:
        raise ValueError('core_mode must be native_tile or fixed')
    return dimensions, dict(mode=mode, width_px=dimensions[0], height_px=dimensions[1],
                            width_m=dimensions[0]*grid.res, height_m=dimensions[1]*grid.res,
                            dimension_source=source, anchor='whole-output grid origin',
                            edge_policy='clip partial cores to requested extent')


def resolve_output(config, records, study):
    """The saved location selects a native tile; only custom mode recentres it."""
    mode = config['output_mode']
    explicit = config.get('custom_center_wgs84')
    if explicit is not None:
        if mode != 'custom':
            raise ValueError('An explicit center requires output_mode=custom; native modes retain source bounds')
        if (set(explicit) != {'latitude','longitude'}
                or not -90 <= explicit['latitude'] <= 90 or not -180 <= explicit['longitude'] <= 180):
            raise ValueError('custom_center_wgs84 must contain valid latitude and longitude')
        placement = {**study, **explicit}
    else:
        placement = study
    if mode == 'native_mosaic':
        grid = native_mosaic_grid(records, config.get('native_tile_names'))
    else:
        grid = target_grid(records, placement, mode, config['custom_width_m'], config['custom_height_m'])
    reference = output_reference(grid)
    reference['placement'] = ('explicit_custom_center' if explicit else 'configured_custom_center') if mode == 'custom' else mode
    reference['selector_latitude'] = study['latitude']
    reference['selector_longitude'] = study['longitude']
    return grid, reference, placement


def run(config):
    started = time.perf_counter()
    out = (ROOT/config['output_directory']).resolve()
    cache_root = (ROOT/config['cache_directory']).resolve()
    if not out.is_relative_to(ROOT/'outputs') or not cache_root.is_relative_to(ROOT/'data/processed'):
        raise ValueError('Results must be inside project outputs/ and caches inside data/processed/')
    if out in (ROOT/'outputs', ROOT/'outputs/600x450'):
        raise ValueError('Select a new result directory; historical outputs are protected')
    workers = config['workers']
    if type(workers) is not int or workers <= 0:
        raise ValueError('Workers must be a positive integer')
    if config.get('core_mode', 'fixed') not in ('native_tile', 'fixed'):
        raise ValueError('core_mode must be native_tile or fixed')
    if config.get('core_mode', 'fixed') == 'fixed':
        core_dimensions(config.get('core_size_px', 1024))
    if config['search_distance_m'] != 1000 or config['buffer_m'] != 1000:
        raise ValueError('This model adopts exactly 1000 m search and 1000 m buffer')
    if config['preview_max_side_px'] <= 0 or config['preview_max_side_px'] > 4096:
        raise ValueError('Preview limit must be 1..4096 pixels')
    if (out.exists() and not (out/'run_definition.json').exists()
            and any(p.name != '.run.lock' for p in out.iterdir())):
        raise ValueError('Output directory contains unmanaged existing results; choose an empty new directory')
    out.mkdir(parents=True, exist_ok=True)
    # Exclusive run lock, automatically released even after process termination.
    import fcntl
    with open(out/'.run.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'Another process owns {out}')
        return _run_locked(config, out, cache_root, workers, started)


def _run_locked(config, out, cache_root, workers, started):
    with memory_monitor() as memory, rasterio.Env(GDAL_CACHEMAX=GDAL_CACHE_BYTES):
        study = load_study_area()
        records = include_auxiliary_source_identities(inventory(RAW.glob('*.tif')))
        grid, spatial_reference, placement = resolve_output(config, records, study)
        size, core_layout = resolve_core_layout(config, records, placement, grid)
        code_files = ['horizon.py', 'spatial.py']
        identity = dict(algorithm=ALGORITHM, code={p:digest_file(ROOT/'src'/p) for p in code_files},
                        sources=records, grid=asdict(grid), search_m=1000, buffer_m=1000,
                        ray_step_m=.25, azimuth_step_deg=5, nodata_policy=NODATA_POLICY)
        key = fingerprint(identity)
        # A different date can use the same horizon key; incompatible runs cannot overwrite results.
        run_key = fingerprint(dict(horizons=key, date=str(study['date']), spatial_reference=spatial_reference, classification_code=digest_file(ROOT/'src/shade_watch.py'), solar_code=digest_file(ROOT/'src/solar.py')))
        run_meta = out/'run_definition.json'
        if run_meta.exists() and json.loads(run_meta.read_text())['key'] != run_key:
            raise ValueError('Output directory belongs to different inputs/settings; choose a new directory')
        atomic_json(run_meta, dict(key=run_key, identity=identity, config=config, core_layout=core_layout, study=study, spatial_reference=spatial_reference))
        cache = cache_root/key
        # Shared cache lock prevents concurrent writers even from different output runs.
        cache.mkdir(parents=True, exist_ok=True)
        import fcntl
        with open(cache/'.cache.lock', 'a') as cache_lock:
            try:
                fcntl.flock(cache_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Horizon cache is in use by another run')
            print(f'Grid {grid.width} × {grid.height}, {grid.res} m, {grid.mode}; core {size[0]} × {size[1]}, workers {workers}', flush=True)
            halo = math.ceil(1000/grid.res)
            # Conservative allocation planning plus measured RSS guard for requested parallel runs.
            estimated = 400*1024**2 + 8*(size[0]+2*halo)*(size[1]+2*halo) + 64*size[0]*size[1]
            if workers*estimated > config['memory_budget_mb']*1024**2:
                raise ValueError(f'Estimated worker allocation {workers*estimated/1024**2:.0f} MiB exceeds memory budget')
            whole = (0,0,grid.width,grid.height)
            surface = region_stats(records, grid, whole)
            buffered = region_stats(records, grid, expand(whole, halo))
            if not surface['valid_pixels']:
                raise ValueError('Entire requested output lacks DSM data')
            threshold = math.degrees(math.atan(max(0, buffered['max_m']-surface['min_m'])/1000))
            seams = seam_audit(records)
            sunrise, sunset = daylight_bounds(study['date'], spatial_reference['latitude'], spatial_reference['longitude'])
            times = daylight_samples(sunrise, sunset, 10)
            suns = [position(t, spatial_reference['latitude'], spatial_reference['longitude']) for t in times]
            azimuths = sorted({nearest_bin(s.azimuth_deg) for s in suns})
            atomic_json(cache/'definition.json', identity)
            jobs = dict(computed=0, reused=0, completed_cores=0, max_worker_rss_bytes=0)
            # Calibrate requested parallelism with one real task before starting the pool.
            iterator = execute(records, grid, size, 1 if workers == 1 else workers, azimuths, cache, key)
            if workers > 1:
                first = next(cores(grid, size))
                measurement = process_core(records, grid, first, azimuths, cache, key, 1000, 1000)
                if measurement['peak_rss_bytes']*workers*1.25 > config['memory_budget_mb']*1024**2:
                    raise ValueError('Measured worker RSS with 25% headroom exceeds memory budget; reduce workers')
                atomic_json(out/'parallel_calibration.json', measurement)
            with (out/'task_events.jsonl').open('a') as events:
                for result in iterator:
                    events.write(json.dumps(result)+'\n'); events.flush()
                    jobs['computed'] += result['computed']; jobs['reused'] += result['reused']
                    jobs['completed_cores'] += 1
                    jobs['max_worker_rss_bytes'] = max(jobs['max_worker_rss_bytes'], result['peak_rss_bytes'])
                    print(f"Core {result['core']}: computed {result['computed']}, reused {result['reused']}, {result['seconds']:.1f}s", flush=True)
            frames = []
            media_pids = set()
            media_monitoring = {}
            jpg_index = min(range(len(times)), key=lambda i: abs(times[i].hour*60+times[i].minute-870))
            video = out/f"shade_daylight_{study['date']}_HKT.mp4"
            temp_video = video.with_name(video.stem+'.tmp.mp4')
            with imageio.get_writer(temp_video, fps=4, codec='libx264', quality=8, pixelformat='yuv420p',
                                    macro_block_size=16, ffmpeg_log_level='error', output_params=['-threads', '1']) as writer:
                for index, (instant, sun) in enumerate(zip(times, suns)):
                    meta = assemble_frame(grid, size, cache, instant, sun, threshold, out, key)
                    path = Path(meta['raster']); export_pngs(path, out, grid, size)
                    valid_fraction = 1-meta['counts']['invalid_or_uncertain']/(grid.width*grid.height)
                    frame, display = render_frame(path, instant, sun, grid, valid_fraction, sunrise, sunset, config['preview_max_side_px'])
                    writer.append_data(np.asarray(frame))
                    if index == 0:
                        pid = track_media_process(writer, '_write_gen', 'p')
                        media_monitoring['encoder_tracked'] = bool(pid)
                        if pid: media_pids.add(pid)
                    if index == jpg_index:
                        jpg = out/f'{path.stem}.jpg'; tmp = jpg.with_name(jpg.stem+'.tmp.jpg')
                        frame.save(tmp, quality=94, subsampling=0); os.replace(tmp, jpg)
                    frames.append(meta)
            with imageio.get_reader(temp_video, 'ffmpeg') as reader:
                pid = track_media_process(reader, '_read_gen', 'process')
                media_monitoring['decoder_tracked'] = bool(pid)
                if pid: media_pids.add(pid)
                decoded_count = sum(1 for _ in reader)
            if decoded_count != len(times):
                raise ValueError('Video frame count mismatch')
            os.replace(temp_video, video)
            EXTERNAL_PIDS.difference_update(media_pids)
            result = dict(algorithm=ALGORITHM, horizon_key=key, cache_directory=str(cache), grid=asdict(grid),
                          config=config, core_layout=core_layout, study=study, spatial_reference=spatial_reference, source_inventory=records, seam_audit=seams,
                          surface_stats=surface, buffered_stats=buffered, distant_threshold_deg=threshold,
                          daylight=dict(sunrise_local=sunrise.isoformat(), sunset_local=sunset.isoformat(),
                                        interval_minutes=10, frames=len(times), decoded_video_frames=decoded_count),
                          frames=frames, jobs=jobs, display=display,
                          performance=dict(seconds=time.perf_counter()-started, **memory, **media_monitoring),
                          environment=dict(python=platform.python_version(), rasterio=rasterio.__version__, numpy=np.__version__),
                          validation_status='Not yet validated against real-world observations',
                          model_boundary='1 km limits influence; it does not prove farther terrain cannot cast shadows')
            atomic_json(out/'result_inventory.json', result)
            print(f'Completed {len(times)} daylight frames in {result["performance"]["seconds"]:.1f}s: {out}', flush=True)
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/processing.json')
    parser.add_argument('--output-mode', choices=['native_tile','native_mosaic','custom'])
    parser.add_argument('--width-m', type=float); parser.add_argument('--height-m', type=float)
    parser.add_argument('--center-lat', type=float); parser.add_argument('--center-lon', type=float)
    parser.add_argument('--core-mode', choices=['native_tile', 'fixed'])
    parser.add_argument('--core-size', type=int, help='Explicit square core side in pixels; switches to fixed mode')
    parser.add_argument('--workers', type=int)
    parser.add_argument('--output', type=str)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    for arg, field in [('output_mode','output_mode'), ('width_m','custom_width_m'), ('height_m','custom_height_m'),
                       ('core_mode','core_mode'), ('core_size','core_size_px'), ('workers','workers'), ('output','output_directory')]:
        if getattr(args, arg) is not None:
            config[field] = getattr(args, arg)
    if (args.center_lat is None) != (args.center_lon is None):
        parser.error('--center-lat and --center-lon must be supplied together')
    if args.center_lat is not None:
        if config['output_mode'] != 'custom':
            parser.error('Explicit centers require --output-mode custom')
        config['custom_center_wgs84'] = dict(latitude=args.center_lat, longitude=args.center_lon)
    if args.core_size is not None:
        if args.core_mode == 'native_tile':
            parser.error('--core-size selects fixed cores; omit it for native_tile cores')
        config['core_mode'] = 'fixed'
    run(config)


if __name__ == '__main__':
    main()
