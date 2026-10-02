"""Run each selected native tile separately, serially, with fresh-process timings."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from .pipeline import ROOT, atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/mosaic_6tiles.json')
    parser.add_argument('--output', required=True, help='New batch directory under outputs/')
    args = parser.parse_args()
    base = json.loads(args.config.read_text())
    names = base.get('native_tile_names', [])
    if not names or len(names) != len(set(names)):
        parser.error('Config must list distinct native_tile_names')
    ids = [Path(name).stem.split('(')[0] for name in names]
    if len(ids) != len(set(ids)) or any(name in ('', '.', '..') for name in ids):
        parser.error('Tile output names must be distinct and nonempty')
    out = (ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'outputs') or out in (ROOT/'outputs', ROOT/'outputs/600x450'):
        parser.error('Choose a new batch directory inside outputs/')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    record_dir = out/'batch_runs'/run_id
    record_dir.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    summary = dict(status='running',run_id=run_id,workers=1,execution='serial, fresh process per tile',tiles=[])
    summary_path = record_dir/'summary.json'
    try:
        for name, tile_id in zip(names, ids):
            config = {**base, 'output_mode':'native_tile', 'native_tile_name':name,
                      'core_mode':'native_tile', 'workers':1,
                      'output_directory':str((out/tile_id).relative_to(ROOT))}
            config.pop('native_tile_names', None)
            config.pop('custom_center_wgs84', None)
            config.pop('core_size_px', None)
            config_path = record_dir/f'{tile_id}.json'
            atomic_json(config_path, config)
            log = record_dir/f'{tile_id}.log'
            print(f'Starting {tile_id}', flush=True)
            t = time.perf_counter()
            with log.open('w') as handle:
                subprocess.run([sys.executable,'-m','src.shade_watch','--config',str(config_path)],
                               cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,check=True)
            elapsed = time.perf_counter()-t
            inventory_path = out/tile_id/'result_inventory.json'
            result = json.loads(inventory_path.read_text())
            tile = dict(tile=tile_id,source=name,wall_seconds=elapsed,
                        inventory=str(inventory_path),jobs=result['jobs'],
                        performance=result['performance'],frames=result['daylight']['frames'],
                        coverage=result['surface_stats']['coverage'],center=result['spatial_reference'])
            summary['tiles'].append(tile)
            summary['total_wall_seconds'] = time.perf_counter()-started
            atomic_json(summary_path,summary)
            atomic_json(out/'latest_batch.json',summary)
            print(f'Completed {tile_id}: {elapsed:.2f}s, {tile["frames"]} frames, '
                  f'{tile["jobs"]["computed"]} computed / {tile["jobs"]["reused"]} reused directions',flush=True)
    except BaseException as exc:
        summary.update(status='failed',error=repr(exc),total_wall_seconds=time.perf_counter()-started)
        atomic_json(summary_path,summary)
        atomic_json(out/'latest_batch.json',summary)
        raise
    summary.update(status='complete',total_wall_seconds=time.perf_counter()-started)
    atomic_json(summary_path,summary)
    atomic_json(out/'latest_batch.json',summary)
    print(f'Completed {len(names)} tiles in {summary["total_wall_seconds"]:.2f}s: {out}',flush=True)


if __name__ == '__main__':
    main()
