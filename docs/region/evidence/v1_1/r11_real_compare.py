"""Three real-region identity comparisons against a full compatible catalogue.

The full 3310-file raw input is not admissible to the pinned engine. The control
catalogue is the UNION of all full-raw target-halo sources for these three ROIs,
not a corrected territory dataset. Every source remains an unmodified symlink.
"""
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
from tools.region_request import plan_region

DOC = ROOT/'docs/region/evidence/v1_1'


def run():
    rows = json.loads((DOC/'real-source-view-timings.json').read_text())
    ledger_path = DOC/'ledger.json'
    ledger = json.loads(ledger_path.read_text())
    started = time.monotonic()
    remaining = 1200-ledger['cumulative_charged_seconds']-20
    if remaining<30: raise RuntimeError('Insufficient remaining region budget')
    def expire(signum, frame): raise TimeoutError('R11 stopped before frozen time ceiling')
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    report = dict(scope='Complete compatible union of all 3310-file raw-catalogue target-halo dependencies for the three benchmark regions',
                  full_raw_admission='Rejected by pinned engine: four shifted-origin 14NE15* tiles, unchanged; this control does not claim territory ingestion',
                  regions=[], passed=False)
    try:
        sources, assets = {}, {}
        for row in rows:
            source = json.loads((Path(row['source_view']['path'])/'source_view.json').read_text())
            for record in source['sources']:
                sources[record['path']] = record
                for filename in [record['path']]+record['auxiliary_paths']:
                    name = Path(filename).name
                    if name in assets and assets[name]!=filename: raise ValueError('Benchmark source-name collision')
                    assets[name] = filename
        definition = dict(schema='shade-watch-region-r11-control-catalogue-1.0',
                          input_views=[r['source_view']['identity'] for r in rows],
                          sources=sorted(sources.values(), key=lambda s:s['path']))
        token = hashlib.sha256(json.dumps(definition, sort_keys=True).encode()).hexdigest()
        control = ROOT/'outputs/region_views'/token
        control.mkdir(parents=True, exist_ok=False)
        for name, filename in assets.items(): (control/name).symlink_to(filename)
        (control/'control_catalogue.json').write_text(json.dumps(definition, indent=2)+'\n')
        report.update(control_catalogue=str(control), control_source_tiles=len(sources))
        for row in rows:
            common = dict(crs='hk1980', instants=['2026-01-07T09:17:23+08:00','2026-01-07T14:31:27+08:00'],
                          dsm_dir=control, output_dir=ROOT/'outputs/region_dev_v1_1_validation'/('r11_'+row['name']))
            begin = time.monotonic(); full = plan_region(*row['corners'], **common)
            full_seconds = time.monotonic()-begin
            begin = time.monotonic(); view = plan_region(*row['corners'], auto_source_view=True, **common)
            view_seconds = time.monotonic()-begin
            full_keys = [r['key'] for r in full['sidecar']['requests']]
            view_keys = [r['key'] for r in view['sidecar']['requests']]
            assert full_keys==view_keys==row['plan_keys']
            # Native spatial keys are independently available in each request's
            # V2-validated definition via a directly planned bounded V1 request.
            from src import v1
            def native(plan):
                request = plan['batches'][0]['requests'][0]
                p = v1.plan_shade(**{k:v for k,v in request.items() if k!='id'})
                return [t.spatial_key for t in p.tiles]
            begin = time.monotonic(); full_native = native(full)
            full_key_seconds = time.monotonic()-begin
            begin = time.monotonic(); view_native = native(view)
            view_key_seconds = time.monotonic()-begin
            assert full_native==view_native
            report['regions'].append(dict(name=row['name'], corners=row['corners'],
                full_catalogue_seconds=full_seconds, auto_view_seconds=view_seconds,
                full_key_audit_seconds=full_key_seconds, view_key_audit_seconds=view_key_seconds,
                full_plan_keys=full_keys, auto_view_plan_keys=view_keys, raw_header_selected_plan_keys=row['plan_keys'],
                full_spatial_keys=full_native, auto_view_spatial_keys=view_native,
                full_source_tiles=len(sources), auto_view_source_tiles=view['sidecar']['source_view']['source_tiles']))
        report['passed'] = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        elapsed = time.monotonic()-started
        report.update(wall_seconds=elapsed, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        (DOC/'r11-real-identity.json').write_text(json.dumps(report, indent=2)+'\n')
        ledger['r11_compatible_control_seconds'] = elapsed
        ledger['r11_full_catalogue_index_seconds'] = sum(r['full_catalogue_seconds']+r['full_key_audit_seconds'] for r in report['regions'])
        ledger['r11_indexing_exception_used'] = False
        ledger['r11_reference_scope'] = report['scope']
        ledger['amendment_real_job_seconds'] += elapsed
        ledger['cumulative_charged_seconds'] += elapsed
        ledger['amendment_peak_tree_rss_bytes'] = max(ledger['amendment_peak_tree_rss_bytes'], report['peak_rss_bytes'])
        ledger_path.write_text(json.dumps(ledger, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__=='__main__': run()
