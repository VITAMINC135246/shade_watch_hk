"""Amendment checks: sparse coverage, complete dates and source-view identity."""
from datetime import date, timedelta
import json
from pathlib import Path
import time
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from shade_watch.engine import v1, v2
from shade_watch.engine.v2_worker import read_logical_window
from shade_watch.region import header_catalogue, main, plan_region, read_region_window, write_region

AT = ['2026-01-07T09:17:23+08:00']


def tile(raw, col, row, *, name=None, left=800000, top=820000):
    path = raw/(name or f'tile_{col}_{row}.tif')
    # A steep eastward fixture provides known blockers despite unknown support.
    values = np.broadcast_to(np.arange(col*4, col*4+4, dtype=np.float32)*10, (4, 4)).copy()
    with rasterio.open(path, 'w', driver='GTiff', width=4, height=4, count=1, dtype='float32',
                       crs='EPSG:2326', nodata=-9999, transform=from_origin(left+col*2, top-row*2, .5, .5)) as ds:
        ds.write(values, 1)
    return path


@pytest.fixture
def sparse(tmp_path, monkeypatch):
    monkeypatch.setattr(v1, 'ROOT', tmp_path)
    raw = tmp_path/'raw'; raw.mkdir()
    for col in (0, 2):
        for row in (0, 1):
            tile(raw, col, row)
    return raw


def request(raw, **kwargs):
    return plan_region((800000, 819996), (800008, 820000), crs='hk1980', instants=AT,
                       dsm_dir=raw, max_pixels_per_request=64, **kwargs)


def exact_partition(sidecar):
    seen = set()
    for bounds in [p['resolved_bounds'] for p in sidecar['partition']]+[g['bounds'] for g in sidecar['no_dsm_areas']]:
        l, b, r, t = [round(v*2) for v in bounds]
        cells = {(x, y) for x in range(l, r) for y in range(b, t)}
        assert not (seen & cells)
        seen |= cells
    l, b, r, t = [round(v*2) for v in sidecar['resolved_bounds']]
    assert seen == {(x, y) for x in range(l, r) for y in range(b, t)}


def execute(result, name):
    mosaics = []
    for i, payload in enumerate(result['batches']):
        batch = v2.plan_batch(**payload)
        assert batch.id == result['sidecar']['batches'][i]['id']
        state = f'work/engine/{name}_{i}'
        identifier = v2.submit_batch(batch, state_dir=state)
        run = v2.run_batch(identifier, state_dir=state)
        assert run['state'] == 'SUCCEEDED', run['failures']
        mosaics.append(v1.ROOT/state/f'{identifier}.logical_mosaic.json')
    return mosaics


def test_no_dsm_interior_edge_and_added_tile(sparse):
    result = request(sparse)
    sc = result['sidecar']; exact_partition(sc)
    assert len(sc['partition']) == 2  # four cells per rectangle, not one job per tile
    assert not sc['no_dsm_areas']
    assert all(p['tiles'] for p in sc['partition'])
    mosaics = execute(result, 'sparse')
    shade, quality, transform = read_region_window(sc, utc_time=AT[0], bounds=sc['resolved_bounds'], logical_mosaics=mosaics)
    assert np.all(shade[:, 4:8] == 255) and np.all(quality[:, 4:8] == 1)
    assert np.all(shade[:, 12:16] == 255) and np.all(quality[:, 12:16] == 1)
    assert np.any(shade[:, :4] == 1) and np.all(quality[:, :4] != 1)
    engine = read_logical_window(mosaics[0], utc_time=v1.normalize_instant(AT[0]).utc, bounds=sc['resolved_bounds'])
    assert np.array_equal(shade, engine[0]) and np.array_equal(quality, engine[1]) and transform == engine[2]
    with pytest.raises(ValueError, match='Missing completed'):
        read_region_window(sc, utc_time=AT[0], bounds=sc['resolved_bounds'], logical_mosaics=[])
    tile(sparse, 1, 0)
    changed = request(sparse, output_dir='work/engine/added', cache_dir='data/cache/horizon/region_dev_added')
    arrays = read_region_window(changed['sidecar'], utc_time=AT[0], bounds=sc['resolved_bounds'],
                                logical_mosaics=execute(changed, 'added'))
    assert np.all(arrays[1][:4, 4:8] != 1) and np.any(arrays[0][:4, 4:8] != 255)
    with pytest.raises(ValueError, match='no DSM'):
        plan_region((900000, 900000), (900002, 900002), crs='hk1980', instants=AT, dsm_dir=sparse)


def test_residual_far_gap_is_kept_and_readable(tmp_path, monkeypatch):
    monkeypatch.setattr(v1, 'ROOT', tmp_path)
    raw = tmp_path/'raw'; raw.mkdir(); tile(raw, 0, 0)
    result = plan_region((800000, 819998), (800016, 820000), crs='hk1980', instants=AT,
                         dsm_dir=raw, max_pixels_per_request=32)
    sc = result['sidecar']; exact_partition(sc)
    assert sc['no_dsm_areas'] and len(sc['partition']) == 1
    # The nearest whole missing cell in the residual cannot fit with the owner.
    for gap in sc['no_dsm_areas']:
        assert gap['bounds'][0] >= 800004 and gap['reason'] and (gap['shade'], gap['quality']) == (255, 1)
        s, q, _ = read_region_window(sc, utc_time=AT[0], bounds=gap['bounds'], logical_mosaics=[])
        assert np.all(s == 255) and np.all(q == 1)
    s, q, _ = read_region_window(sc, utc_time=AT[0], bounds=sc['resolved_bounds'], logical_mosaics=execute(result, 'far'))
    assert s.shape == (4, 32) and np.all(s[:, 8:] == 255) and np.all(q[:, 8:] == 1)


def test_dates_key_and_over_512_split_at_dates(sparse):
    dates = [(date(2026, 1, 7)+timedelta(days=i)).isoformat() for i in range(9)]
    for days in [dates[:1], dates]:
        plan = plan_region((800000, 819998), (800002, 820000), crs='hk1980', dates=days,
                           interval_minutes=10, dsm_dir=sparse)
        expected = []
        for day in days:
            p = v1.plan_shade(mode='custom', bounds=(800000, 819998, 800002, 820000), dates=[day],
                              interval_minutes=10, dsm_dir=sparse)
            expected.extend(i.utc for i in p.request.instants)
        actual = []
        for payload in plan['batches']:
            for req in payload['requests']:
                manual = v1.plan_shade(**{k: v for k, v in req.items() if k != 'id'})
                assert manual.key in [r['key'] for r in plan['sidecar']['requests']]
                assert len(manual.request.instants) <= v1.MAX_FRAMES
                assert 'dates' in req and 'instants' not in req
                actual.extend(i.utc for i in manual.request.instants)
        assert actual == expected and len(actual) == len(set(actual))
        if len(days)>1:
            assert len(expected)>v1.MAX_FRAMES and len(plan['sidecar']['time_groups'])>1
        else:
            manual = v1.plan_shade(mode='custom', bounds=(800000, 819998, 800002, 820000), dates=days,
                                   interval_minutes=10, dsm_dir=sparse)
            assert plan['sidecar']['partition'][0]['key'] == manual.key
    with pytest.raises(ValueError, match='larger interval'):
        plan_region((800000, 819998), (800002, 820000), crs='hk1980', dates=dates[:1], interval_minutes=1, dsm_dir=sparse)
    with pytest.raises(ValueError, match='at least one date'):
        plan_region((800000, 819998), (800002, 820000), crs='hk1980', dates=[], dsm_dir=sparse)
    with pytest.raises(ValueError, match='Duplicate daylight date'):
        plan_region((800000, 819998), (800002, 820000), crs='hk1980', dates=[dates[0]]*2, dsm_dir=sparse)


def test_source_view_three_regions_identity_and_prebuilt_admission(sparse, record_property):
    # Add a distant compatible source: the auto view must exclude irrelevant data.
    tile(sparse, 0, 0, name='distant.tif', left=900000, top=920000)
    regions = [((800000, 819996), (800008, 820000)),  # coastal: uncovered cells
               ((800000.5, 819998.5), (800001.5, 819999.5)),  # inside supplied tile
               ((800001, 819997), (800005, 819999))]  # tile corner and gap
    timings = []
    for a, b in regions:
        started = time.perf_counter()
        full = plan_region(a, b, crs='hk1980', instants=AT, dsm_dir=sparse)
        full_time = time.perf_counter()-started
        with patch.object(v2, 'plan_batch', wraps=v2.plan_batch) as admission, \
                patch.object(v1, 'index_sources', wraps=v1.index_sources) as index:
            started = time.perf_counter()
            view = plan_region(a, b, crs='hk1980', instants=AT, dsm_dir=sparse, auto_source_view=True)
            view_time = time.perf_counter()-started
        assert admission.call_count == 1 and all(isinstance(p, v1.ShadePlan) for p in admission.call_args.args[0])
        assert index.call_count == 2  # own engine inventory + one final V2 inventory, not one per part/trial
        assert full['sidecar']['requests'][0]['key'] == view['sidecar']['requests'][0]['key']
        f = v2.plan_batch(**full['batches'][0]); v = v2.plan_batch(**view['batches'][0])
        assert {p['key'] for p in f.definition['requests'].values()} == {p['key'] for p in v.definition['requests'].values()}
        assert {t['payload']['key'] for t in f.definition['tasks'] if t['kind']=='horizon'} == {t['payload']['key'] for t in v.definition['tasks'] if t['kind']=='horizon'}
        path = Path(view['sidecar']['source_view']['path'])
        assert all(p.is_symlink() for p in path.glob('*.tif')) and not (path/'distant.tif').exists()
        again = plan_region(a, b, crs='hk1980', instants=AT, dsm_dir=sparse, auto_source_view=True)
        assert again['sidecar']['source_view']['identity'] == view['sidecar']['source_view']['identity']
        timings.append(dict(region=['coastal', 'inland', 'tile_corner'][len(timings)], full_seconds=full_time, view_seconds=view_time,
                            v1_plan_keys=[q['key'] for q in full['sidecar']['requests']],
                            view_v1_plan_keys=[q['key'] for q in view['sidecar']['requests']],
                            full_tiles=5, view_tiles=view['sidecar']['source_view']['source_tiles'],
                            spatial_keys=sorted(t['payload']['key'] for t in f.definition['tasks'] if t['kind']=='horizon'),
                            view_spatial_keys=sorted(t['payload']['key'] for t in v.definition['tasks'] if t['kind']=='horizon')))
    record_property('r11_timings', json.dumps(timings))
    assert len(timings)==3


def test_source_view_shift_guard_header_invalidation_and_masks(sparse):
    header = header_catalogue(sparse)[0]
    path = Path(header['path'])
    # A new external mask must invalidate cached metadata/dependencies even though
    # the original TIFF's size and timestamp do not change.
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(path, 'r+') as ds:
            mask = np.full(ds.shape, 255, np.uint8); mask[0, 0] = 0; ds.write_mask(mask)
    planned = request(sparse, auto_source_view=True)
    view = Path(planned['sidecar']['source_view']['path'])
    assert (view/(path.name+'.msk')).is_symlink()
    full = request(sparse)
    assert [r['key'] for r in planned['sidecar']['requests']] == [r['key'] for r in full['sidecar']['requests']]
    # Known shifted input is rejected even as a halo dependency, never silently omitted.
    tile(sparse, 4, 0, name='14NE15A(e828n809,e829n809).tif')
    with pytest.raises(ValueError, match='pending shifted-origin DSM ingestion policy'):
        request(sparse, auto_source_view=True)


def test_date_cli_and_batch_name_provenance(sparse, tmp_path, capsys):
    args = ['write', '--crs', 'hk1980', '--corner1', '800000', '819998', '--corner2', '800002', '820000',
            '--date', '2026-01-07', '--interval-minutes', '120', '--auto-source-view',
            '--dsm-dir', str(sparse), '--output', 'work/engine/dates_cli', '--directory', str(tmp_path/'requests')]
    main(args)
    sidecar = json.loads(capsys.readouterr().out)
    assert sidecar['time_groups'][0]['input'] == dict(dates=['2026-01-07'], interval_minutes=120)
    assert '--date' in sidecar['v1_command'] and sidecar['source_view']
    result = request(sparse, artifact_budget_bytes=17_000_000)
    ids = result['sidecar']['generated_request_ids']
    assert len(ids) == len(set(ids))
    for i, payload in enumerate(result['batches']):
        assert v2.plan_batch(**payload).id == result['sidecar']['batches'][i]['id']


def test_multi_batch_engine_readback_and_one_shot_admission(sparse):
    with patch.object(v2, 'plan_batch', wraps=v2.plan_batch) as admission, \
            patch.object(v1, 'index_sources', wraps=v1.index_sources) as index:
        planned = request(sparse, auto_source_view=True)
    assert len(planned['sidecar']['partition'])==2
    assert admission.call_count==1 and index.call_count==2
    assert all(isinstance(p, v1.ShadePlan) for p in admission.call_args.args[0])
    result = request(sparse, artifact_budget_bytes=17_000_000, output_dir='work/engine/multi_parts')
    assert len(result['batches'])>1
    shade, quality, transform = read_region_window(result['sidecar'], utc_time=AT[0],
        bounds=result['sidecar']['resolved_bounds'], logical_mosaics=execute(result, 'multi'))
    reference = v1.run_shade(v1.plan_shade(mode='custom', bounds=result['sidecar']['requested_bounds'], instants=AT,
                         dsm_dir=sparse, output_dir='work/engine/multi_ref', cache_dir='data/cache/horizon/region_dev_multi_ref'))
    for key, actual in [('raster', shade), ('quality_raster', quality)]:
        with rasterio.open(reference.frames[0][key]) as ds:
            assert np.array_equal(actual, ds.read(1)) and transform==ds.transform
