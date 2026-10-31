"""Bounded R06/R12 development evidence; execute from the repository root."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import psutil
import rasterio

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
from src import v1, v2
from src.v2_worker import read_logical_window
from tools.region_request import header_catalogue, plan_region, read_region_window, write_region

DOC = ROOT/'docs/region/evidence/v1_1'
OUT = ROOT/'outputs/region_dev_v1_1_validation'
RAW = ROOT/'data/raw/dsm/2020/D12.DSM.TIFF'
V2_CACHE = ROOT/'data/processed/shade_v1/region_dev_v1_1_v2'
V1_CACHE = ROOT/'data/processed/shade_v1/region_dev_v1_1_v1'
TIMES = ['2026-01-07T09:17:23+08:00', '2026-01-07T14:31:27+08:00']
BOUNDS = (844701.5, 822197.5, 844713.5, 822202.5)


def save(name, value):
    (DOC/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def guides():
    # Execute precisely the first two fenced shell examples; neither computes shade.
    text = (ROOT/'docs/region/GUIDE.md').read_text()
    block = text.split('```sh\n', 1)[1].split('```', 1)[0]
    commands = [c.strip().replace('\\\n', '') for c in block.strip().split('\n\n')]
    rows = []
    for i, command in enumerate(commands):
        import shlex
        started = time.monotonic()
        result = subprocess.run(shlex.split(command), cwd=ROOT, capture_output=True, text=True)
        (DOC/f'guide_{i}_stdout.json').write_text(result.stdout)
        (DOC/f'guide_{i}_stderr.txt').write_text(result.stderr)
        rows.append(dict(command=command, exit_code=result.returncode, wall_seconds=time.monotonic()-started))
        if result.returncode:
            save('guide-checks.json', rows)
            raise RuntimeError('Guide example failed')
    save('guide-checks.json', rows)


def work():
    if any(p.exists() for p in (OUT, V2_CACHE, V1_CACHE)):
        raise RuntimeError('Real workload requires fresh output and both fresh cache namespaces')
    OUT.mkdir(parents=True, exist_ok=False)
    guides()
    started = time.monotonic()
    region = plan_region(BOUNDS[:2], BOUNDS[2:], crs='hk1980', instants=TIMES,
                         dsm_dir=RAW, auto_source_view=True, output_dir=OUT/'parts',
                         cache_dir=V2_CACHE, max_pixels_per_request=120,
                         memory_budget_mb=8192, artifact_budget_bytes=5*1024**3)
    write_region(region, OUT/'requests')
    assert len(region['sidecar']['partition']) == 2 and not region['sidecar']['no_dsm_areas']
    source = region['sidecar']['source_directory']
    # The V1 reference has its own cold namespace and actually computes all directions.
    baseline = v1.plan_shade(mode='custom', bounds=BOUNDS, instants=TIMES,
                             dsm_dir=source, output_dir=OUT/'v1_reference', cache_dir=V1_CACHE)
    assert len(baseline.tiles) == 2 and all(len(t.directions)==2 and len(t.missing_directions)==2 for t in baseline.tiles)
    batches = [v2.plan_batch(**payload) for payload in region['batches']]
    assert len(batches)==1 and batches[0].id==region['sidecar']['batches'][0]['id']
    assert sum(t['kind']=='horizon' for t in batches[0].definition['tasks']) == len(baseline.tiles)
    save('real-plan.json', dict(sidecar=region['sidecar'], v1_reference=baseline.to_dict(),
                              admitted_batch=batches[0].to_dict(), planning_seconds=time.monotonic()-started))
    state = OUT/'state'
    batch = v2.submit_batch(batches[0], state_dir=state)
    started = time.monotonic()
    result = v2.run_batch(batch, state_dir=state)
    save('v2-result.json', dict(result=result, wall_seconds=time.monotonic()-started))
    assert result['state']=='SUCCEEDED', result['failures']
    started = time.monotonic()
    reference = v1.run_shade(baseline)
    save('v1-result.json', dict(jobs=reference.jobs, index=str(reference.index_path), wall_seconds=time.monotonic()-started))
    assert reference.jobs['computed']>0 and reference.jobs['horizon_calls']==4 and reference.jobs['reused']==0
    mosaic = state/f'{batch}.logical_mosaic.json'
    evidence = []
    for i, instant in enumerate(baseline.request.instants):
        shade, quality, transform = read_logical_window(mosaic, utc_time=instant.utc, bounds=baseline.grid.bounds())
        helper = read_region_window(region['sidecar'], utc_time=instant.utc, bounds=baseline.grid.bounds(), logical_mosaics=[mosaic])
        for key, actual in [('raster', shade), ('quality_raster', quality)]:
            with rasterio.open(reference.frames[i][key]) as ds:
                assert np.array_equal(actual, ds.read(1)) and transform == ds.transform
        assert np.array_equal(helper[0], shade) and np.array_equal(helper[1], quality) and helper[2] == transform
        evidence.append(dict(utc=instant.utc, shape=list(shade.shape), shade_equal=True, quality_equal=True,
                             transform_equal=True, region_helper_equal=True,
                             shade_counts={str(k):int(v) for k,v in zip(*np.unique(shade, return_counts=True))},
                             quality_counts={str(k):int(v) for k,v in zip(*np.unique(quality, return_counts=True))}))
    save('real-equality.json', dict(frames=evidence, v1_jobs=reference.jobs, v2_metrics=result['metrics'],
                                  directions={Path(t.source['path']).name:list(t.directions) for t in baseline.tiles},
                                  v1_cache=str(V1_CACHE), v2_cache=str(V2_CACHE), batch=batch, passed=True))
    # Additional real source-view timings for all three region types. Full raw
    # comparison is not fabricated: the original whole-catalogue rejection stands.
    regions = [dict(name='coastal', corners=((820990.,808380.),(821010.,808420.))),
               dict(name='inland', corners=((834990.,815990.),(835010.,816010.))),
               dict(name='tile_corner', corners=((844990.,822190.),(845010.,822210.)))]
    for row in regions:
        began = time.monotonic()
        plan = plan_region(*row['corners'], crs='hk1980', instants=TIMES, dsm_dir=RAW, auto_source_view=True,
                           output_dir=OUT/('timing_'+row['name']), cache_dir=V2_CACHE)
        row.update(view_seconds=time.monotonic()-began, source_view=plan['sidecar']['source_view'],
                   plan_keys=[r['key'] for r in plan['sidecar']['requests']],
                   full_raw_reference='Unavailable: v1.index_sources rejects known four shifted-origin 14NE15* sources')
    save('real-source-view-timings.json', regions)


def generated_bytes():
    roots = [ROOT/'docs/region', ROOT/'tools/region_request.py', ROOT/'tests/test_region_request_v1_1.py']
    roots += list((ROOT/'outputs').glob('region_*'))
    roots += list((ROOT/'data/processed/shade_v1').glob('region_dev*'))
    total = 0
    for root in roots:
        candidates = [root] if root.is_file() else root.rglob('*')
        for p in candidates:
            try:
                if p.is_file() and not p.is_symlink(): total += p.stat().st_size
            except FileNotFoundError:
                pass  # Task-owned atomic cache publication may remove a temporary.
    return total


def supervise():
    ledger_path = DOC/'ledger.json'
    if ledger_path.exists():
        raise RuntimeError('Do not overwrite an attempted real workload ledger')
    legacy = json.loads((ROOT/'docs/region/evidence/ledger.json').read_text())
    charged = legacy['conservative_total_elapsed_charge_seconds']
    # Fail before launch when process-tree measurement is unavailable.
    psutil.Process().memory_info(); psutil.Process().children(recursive=True)
    ledger = dict(status='RUNNING', previous_conservative_charge_seconds=charged,
                  amendment_real_job_seconds=0., cumulative_charged_seconds=charged,
                  prior_measured_engine_peak_bytes=legacy['measured_engine_peak_tree_rss_bytes'],
                  amendment_peak_tree_rss_bytes=0, ceiling_seconds=1200, ceiling_memory_bytes=8*1024**3,
                  ceiling_artifact_bytes=5*1024**3, r11_full_catalogue_index_seconds=0,
                  accounting='Includes all amendment real-DSM work, guide planning and timing. Original 391-second conservative charge retained. Symlinks are not new DSM bytes.')
    ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
    started = time.monotonic()
    with (DOC/'real-run.txt').open('x') as log:
        process = subprocess.Popen([sys.executable, __file__, '--child'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            proc = psutil.Process(process.pid)
            while process.poll() is None:
                elapsed = time.monotonic()-started
                rss = 0
                for p in [proc]+proc.children(recursive=True):
                    try: rss += p.memory_info().rss
                    except psutil.NoSuchProcess: pass
                ledger.update(amendment_real_job_seconds=elapsed, cumulative_charged_seconds=charged+elapsed,
                              amendment_peak_tree_rss_bytes=max(ledger['amendment_peak_tree_rss_bytes'], rss),
                              generated_bytes=generated_bytes())
                ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
                if charged+elapsed>1180 or rss>7.5*1024**3 or ledger['generated_bytes']>4.8*1024**3:
                    raise RuntimeError('Watchdog stopped before frozen budget ceiling')
                time.sleep(.5)
            if process.returncode:
                raise RuntimeError(f'Real check failed with exit {process.returncode}')
            ledger['status'] = 'SUCCEEDED'
        except BaseException as exc:
            ledger.update(status='BLOCKED', error=repr(exc))
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
            raise
        finally:
            ledger['amendment_real_job_seconds'] = time.monotonic()-started
            ledger['cumulative_charged_seconds'] = charged+ledger['amendment_real_job_seconds']
            ledger['generated_bytes'] = generated_bytes()
            ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
    print(json.dumps(ledger, indent=2))


if __name__=='__main__':
    if '--child' in sys.argv: work()
    else: supervise()
