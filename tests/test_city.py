"""Synthetic checks for registration, city requests and native-grid publication."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pyproj
import pytest
import rasterio
from rasterio.transform import from_origin

from src import v1
from src.solar import daylight_bounds, daylight_samples
from tools.city import profiles
from tools.city.__main__ import main as register_cli
from tools.city.ingest import register
from tools.sea2.fill_impact import fill_impact
from tools.shade_map import plan_shade_map, shade_map
from tools.shade_map.__main__ import main as shade_cli
from tools.shade_map.common import digest, read_json
from tools.shade_map.config import InvalidInput
from tools.shade_map.planning import prepare

LEFT, BOTTOM = 92500, 437500
SENTINEL = 32768.0
TIME = dict(mode='instants', instants=['2026-06-21T13:40'])


def write_json(path, value):
    path.write_text(json.dumps(value))
    return path


def file_state(root):
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, digest(p))
            for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def city_fixture(tmp_path, monkeypatch):
    hk, nl = (profiles.load_city(name) for name in ('hong_kong', 'rotterdam'))
    directory = tmp_path / 'cities'
    directory.mkdir()
    write_json(directory / 'hong_kong.json', hk)
    city_path = directory / 'rotterdam.json'
    monkeypatch.setattr(profiles, 'CITY_DIR', directory)
    monkeypatch.setattr(v1, 'ROOT', tmp_path)
    monkeypatch.setattr('tools.sea2.catalogue.DOMAIN_MARGIN_M', 2)

    raw = tmp_path / 'data/raw/nl'
    raw.mkdir(parents=True)
    (raw / '.hidden.tif').write_bytes(b'hidden')
    machine = dict(schema='shade-map-machine-1.0', dsm_dir='missing_hk',
                   output_root='outputs/maps', cache_namespace='fixture',
                   cities={'rotterdam': {'raw_dir': 'data/raw/nl'}})
    machine_path = write_json(tmp_path / 'machine.json', machine)

    def sheets(values=None, *, resolution=.5, nodata=SENTINEL):
        if values is None:
            values = np.arange(40, dtype=np.float32).reshape(5, 8) / 20 + 2
            values[0, :4] = [-2.5, SENTINEL, np.nan, np.inf]
            values[1, 3] = -0.0
        inputs = []
        for start, end, name in [(0, 3, 'west.tif'), (3, 8, 'east.tif')]:
            path = raw / name
            with rasterio.open(path, 'w', driver='GTiff', dtype='float32', count=1,
                               crs=nl['crs'], nodata=nodata, width=end-start, height=5,
                               transform=from_origin(LEFT+start*.5, BOTTOM+2.5, resolution, resolution)) as out:
                out.write(values[:, start:end], 1)
            inputs.append(dict(name=name, bytes=path.stat().st_size, sha256=digest(path),
                               declared_nodata='NaN' if np.isnan(nodata) else nodata))
        bounds = [LEFT, BOTTOM, LEFT+4, BOTTOM+2.5]
        lon, lat = pyproj.Transformer.from_crs(nl['crs'], 'EPSG:4326', always_xy=True).transform(
            LEFT+2, BOTTOM+1.25)
        nl.update(extent=bounds, daylight_reference=[lat, lon])
        nl['ingest'].update(cell_pixels=[5, 5], sheets=inputs)
        write_json(city_path, nl)
        return values

    values = sheets()
    return raw, city_path, machine_path, sheets, values


def region(**changes):
    return dict(dict(schema='shade-map-region-1.1', name='fixture', city='rotterdam',
                     crs='projected', lower_left=[LEFT, BOTTOM],
                     upper_right=[LEFT+2, BOTTOM+2], time=deepcopy(TIME)), **changes)


def test_frozen_profiles():
    contract = Path('docs/prompts/G1/ACCEPTANCE_CONTRACT.md').read_text()
    hk, nl, sea = [json.loads(block.split('```')[0]) for block in contract.split('```json')[1:]]
    assert profiles.load_city('hong_kong') == hk
    assert profiles.load_city('rotterdam') == nl
    assert profiles.fill_profile(nl, nl) == sea


def test_lossless_registration_and_repeat(city_fixture, tmp_path, capsys):
    raw, _, machine, _, original = city_fixture
    raw_before = file_state(raw)
    assert register_cli(['register', 'rotterdam', '--machine', str(machine)]) == 0
    captured = capsys.readouterr()
    first = json.loads(captured.out)
    assert 'warning: fill_above_ground' in captured.err
    root = tmp_path / 'data/processed'
    destination = root / 'dsm_catalogues/rotterdam' / first['ingest_id']
    assert first['cells'] == 2
    expected = np.full((5, 10), -9999, np.float32)
    expected[:, :8] = np.where(np.isfinite(original) & (original != SENTINEL), original, -9999)
    arrays = []
    manifest = read_json(destination / 'manifest.json')
    assert all(not Path(s['name']).is_absolute() for s in manifest['sheets'])
    for cell in manifest['cells']:
        path = destination / 'tiles' / cell['name']
        assert digest(path) == cell['sha256']
        with rasterio.open(path) as ds:
            assert (ds.shape, ds.res, ds.crs.to_epsg(), ds.nodata) == ((5, 5), (.5, .5), 28992, -9999)
            assert list(ds.bounds) == cell['bounds']
            arrays.append(ds.read(1))
    np.testing.assert_array_equal(np.concatenate(arrays, axis=1).view(np.uint32), expected.view(np.uint32))
    stats = first['registration_report']
    valid = expected[expected != -9999]
    assert stats['valid_pixels'] == valid.size == 37
    assert stats['nodata_pixels'] == 3 and stats['padding_nodata_pixels'] == 10
    assert stats['valid_pixels_below_fill'] == 1
    assert stats['warnings'] == ['fill_above_ground']
    assert stats['minimum_m'] == float(valid.min())
    assert stats['maximum_m'] == float(valid.max())
    assert list(stats['percentiles_m'].values()) == pytest.approx(np.percentile(valid, [1, 50, 99]))
    before = file_state(root)
    assert register('rotterdam', machine) == first
    assert file_state(root) == before
    assert file_state(raw) == raw_before
    changed = destination / 'registration_report.json'
    changed.write_text('{}')
    with pytest.raises(InvalidInput, match='repeat registration differs'):
        register('rotterdam', machine)
    assert changed.read_text() == '{}'


@pytest.mark.parametrize('height, expected', [(2.0, []), (10.0, []), (10.25, ['fill_far_below_ground'])])
def test_fill_warning_threshold(city_fixture, height, expected):
    _, _, machine, sheets, _ = city_fixture
    sheets(np.full((5, 8), height, dtype=np.float32))
    assert register('rotterdam', machine)['registration_report']['warnings'] == expected


def test_nan_declared_nodata(city_fixture):
    _, _, machine, sheets, _ = city_fixture
    data = np.full((5, 8), 1, np.float32)
    data[0, 0] = np.nan
    sheets(data, nodata=float('nan'))
    assert register('rotterdam', machine)['registration_report']['nodata_pixels'] == 1


@pytest.mark.parametrize('case', ['changed', 'missing', 'extra', 'extent', 'reference', 'grid', 'collision'])
def test_reject_sheets(city_fixture, tmp_path, case):
    raw, city_path, machine, sheets, values = city_fixture
    city = read_json(city_path)
    if case == 'changed':
        path = raw / 'west.tif'
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
    elif case == 'missing':
        (raw / 'west.tif').unlink()
    elif case == 'extra':
        (raw / 'extra.tif').write_bytes(b'extra')
    elif case == 'extent':
        city['extent'][2] += 1
        write_json(city_path, city)
    elif case == 'reference':
        city['daylight_reference'][0] += .02
        write_json(city_path, city)
    elif case == 'grid':
        sheets(resolution=1)
    elif case == 'collision':
        values[2, 2] = -9999
        sheets(values)
    before = file_state(raw)
    with pytest.raises(InvalidInput):
        register('rotterdam', machine)
    assert file_state(raw) == before
    assert not list((tmp_path / 'data/processed').rglob('*.json'))


@pytest.mark.parametrize('case, message', [
    ('unknown', 'unknown city'), ('bad_profile', 'required key'), ('resolution', '0.5'),
    ('outside', 'outside rotterdam extent'), ('no_city', 'explicit city'), ('wrong_crs', 'hk1980'),
    ('wrong_order', 'lower_left'), ('offset', 'offset disagrees'), ('gap', 'nonexistent'),
    ('fold', 'Ambiguous'), ('duplicate_folder', 'duplicate'),
    ('no_match', 'candidates:'), ('multiple', 'match 2 cities'),
])
def test_invalid_input_before_writes(city_fixture, tmp_path, capsys, case, message):
    _, city_path, machine, _, _ = city_fixture
    config = region()
    if case == 'unknown':
        config['city'] = 'other'
    elif case == 'bad_profile':
        city = read_json(city_path)
        del city['timezone']
        write_json(city_path, city)
    elif case == 'resolution':
        write_json(city_path, dict(read_json(city_path), resolution_m=1))
    elif case == 'outside':
        config['upper_right'][0] += 10
    elif case == 'no_city':
        del config['city']
    elif case == 'wrong_crs':
        config['crs'] = 'hk1980'
    elif case == 'wrong_order':
        config['lower_left'], config['upper_right'] = config['upper_right'], config['lower_left']
    elif case in ('no_match', 'multiple'):
        del config['city']
        config['crs'] = 'wgs84'
        config['lower_left'], config['upper_right'] = [0, 0], [1, 1]
        if case == 'multiple':
            city = read_json(city_path)
            write_json(city_path.parent / 'other.json', dict(city, city_id='other'))
            convert = pyproj.Transformer.from_crs('EPSG:28992', 'EPSG:4326', always_xy=True)
            config['lower_left'] = list(reversed(convert.transform(LEFT+.5, BOTTOM+.5)))
            config['upper_right'] = list(reversed(convert.transform(LEFT+2, BOTTOM+2)))
    else:
        times = dict(offset=['2026-06-21T13:40+01:00'], gap=['2026-03-29T02:30'],
                     fold=['2026-10-25T02:30'],
                     duplicate_folder=['2026-10-25T02:30+02:00', '2026-10-25T02:30+01:00'])
        config['time']['instants'] = times[case]
    path = write_json(tmp_path / 'region.json', config)
    before = set(tmp_path.rglob('*'))
    assert shade_cli(['run', '--machine', str(machine), str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith('invalid input:')
    assert message in captured.err
    assert set(tmp_path.rglob('*')) == before


def test_native_grid_and_fill_impact(city_fixture, tmp_path):
    _, _, machine, _, _ = city_fixture
    registration = register('rotterdam', machine)
    kwargs = dict(machine=machine, name='fixture', city='rotterdam', crs='projected')
    corners = [LEFT, BOTTOM], [LEFT+3.5, BOTTOM+2]
    plan = plan_shade_map(*corners, TIME, **kwargs)
    assert plan['fill_context']['no_dsm_cells_within_1km'] > 0
    assert 'no_dsm_cells_within_1km' in plan['warnings']
    assert plan['frames'][0]['utc_time'] == '2026-06-21T11:40:00+00:00'
    assert plan['city']['ingest_id'] == registration['ingest_id']
    convert = pyproj.Transformer.from_crs('EPSG:28992', 'EPSG:4326', always_xy=True)
    geographic = [list(reversed(convert.transform(x, y)))
                  for x, y in [(LEFT+.5, BOTTOM+.5), (LEFT+2, BOTTOM+2)]]
    auto = plan_shade_map(*geographic, TIME, name='auto', machine=machine)
    assert auto['city']['city_id'] == 'rotterdam'
    assert auto['projection']['operation']
    assert auto['projection']['accuracy_m'] >= -1
    result = shade_map(*corners, TIME, **kwargs)
    assert result['status'] == 'complete'
    folder = tmp_path / 'outputs/maps/fixture'
    run = read_json(folder / 'run_manifest.json')
    assert run['city'] == run['identity_document']['city'] == plan['city']
    assert run['identity_document']['publication_format'] == 'shade-map-publication-1.1'
    assert run['region_config']['dsm_source'] == 'sea-2.2'
    assert run['source_identity']['view_id'] == registration['view_id']
    assert shade_map(*corners, TIME, **kwargs)['verified_only']
    assert prepare(region(name='raw', dsm_source='raw'), machine).batch_plans[0].definition[
        'requests']['request_0000']['cache_directory'].endswith('/fixture_rotterdam')
    for path in (folder / '20260621/1340').rglob('*'):
        if path.suffix in ('.tif', '.vrt'):
            with rasterio.open(path) as ds:
                assert ds.crs.to_epsg() == 28992 and ds.res == (.5, .5)
    work = next((tmp_path / 'outputs/shade_map_work').glob('fixture-*'))
    engine = next(work.glob('engine/*/shade/*.tif'))
    with rasterio.open(engine) as ds:
        assert ds.tags()['source_and_owner'] == profiles.load_city('rotterdam')['dsm_source_line']
        assert ds.tags()['timezone'] == 'Europe/Amsterdam'
    before = file_state(folder)
    diagnostic = fill_impact(machine, run['region_config'], times='1340')
    assert diagnostic['frames'] == 1 and file_state(folder) == before
    with rasterio.open(Path(diagnostic['report']).parent / '20260621/1340/dependency.vrt') as ds:
        assert ds.crs.to_epsg() == 28992


@pytest.mark.parametrize('day, offset, endpoints', [
    ('2026-03-28', '+01:00', None), ('2026-03-29', '+02:00', None),
    ('2026-10-24', '+02:00', None), ('2026-10-25', '+01:00', None),
    ('2026-06-21', '+02:00', (34, '05:30', '22:00')),
    ('2026-12-22', '+01:00', (16, '09:00', '16:30')),
])
def test_amsterdam_daylight(day, offset, endpoints):
    bounds = daylight_bounds(date.fromisoformat(day), 51.92, 4.48, ZoneInfo('Europe/Amsterdam'))
    frames = [t.isoformat(timespec='minutes') for t in daylight_samples(*bounds, 30)]
    assert all(t.startswith(day) and t.endswith(offset) for t in frames)
    if endpoints:
        assert (len(frames), frames[0][11:16], frames[-1][11:16]) == endpoints


def test_media_rejected_for_other_city():
    for kind in ('jpg', 'mp4'):
        with pytest.raises(ValueError, match='JPG and MP4'):
            v1.plan_shade(instants=['2026-06-21T13:40'], crs='EPSG:28992', **{kind: True})
