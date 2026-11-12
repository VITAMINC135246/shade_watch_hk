from pathlib import Path

import numpy as np
import pytest
import rasterio

from shade_watch.engine import v1
from shade_watch.fill.__main__ import main
from shade_watch.fill.build import build
from shade_watch.fill.checks import RawCounterfactual
from shade_watch.fill.fill_impact import fill_impact, frame_metrics, require_run
from shade_watch.publish.common import atomic_json, digest, seal
from shade_watch.publish.config import InvalidInput, validate_schema, load_json
from shade_watch.publish.runner import run_region
from test_sea2_view import catalogue


def region_config(name='fill_fixture', instant='12:30'):
    return dict(schema='shade-map-region-1.0', name=name, crs='hk1980',
                lower_left=[800000,820000], upper_right=[800004,820003],
                time=dict(mode='instants',instants=['2026-01-07T'+instant]), dsm_source='sea-2.2')


def test_dependency_codes_partition_and_observed_transitions():
    surface = np.array([[0,0,0,0,1,2,3,4,255]], np.uint8)
    sea = np.array([[0,1,1,255,0,1,255,0,255]], np.uint8)
    raw = np.array([[0,255,0,1,255,255,255,255,255]], np.uint8)
    sea_quality = np.where(sea==255,3,0).astype(np.uint8)
    raw_quality = np.where(raw==255,2,0).astype(np.uint8)
    dependency, counts, transitions = frame_metrics(surface,sea,sea_quality,raw,raw_quality)
    assert dependency.tolist() == [[0,1,2,4,3,3,4,3,255]]
    assert counts['land'].tolist() == [1,1,1,0,2]
    assert counts['water'].tolist() == [0,0,0,2,0]
    assert counts['other'].tolist() == [0,0,0,1,0]
    assert transitions == {(0,0,0,0):1,(255,2,1,0):1,(0,0,1,0):1,(1,0,255,3):1}
    with pytest.raises(RuntimeError, match='partition'):
        frame_metrics(surface,sea,raw_quality,raw,raw_quality)


def test_refuses_missing_and_wrong_provider(catalogue, capsys):
    raw,p,machine,put = catalogue
    put(0,0,np.ones((6,8)))
    region = region_config('missing')
    with pytest.raises(InvalidInput,match='run F first'):
        require_run(machine,region)
    mpath, rpath = v1.ROOT/'machine.json', v1.ROOT/'region.json'
    atomic_json(mpath,machine)
    atomic_json(rpath,region)
    assert main(['fill-impact','--machine',str(mpath),str(rpath)])==2
    assert 'run F first' in capsys.readouterr().err
    with pytest.raises(InvalidInput,match='sea-2.2'):
        require_run(machine,dict(region,dsm_source='raw'))
    assert not (v1.ROOT/machine['output_root']/'_diagnostics').exists()


def test_raw_counterfactual_report_readback_and_resume(catalogue):
    raw,p,machine,put = catalogue
    data = np.ones((6,8),np.float32)
    data[2,2] = -9999
    data[:,6:] = -9999
    source = put(0,0,data)
    build(machine,profile=p)
    region = region_config()
    run_region(region,machine)
    publication = v1.ROOT/machine['output_root']/region['name']
    before = {p:digest(p) for p in publication.rglob('*') if p.is_file()}
    with pytest.raises(InvalidInput,match='times absent'):
        fill_impact(machine,region,times='1231')
    with pytest.raises(InvalidInput,match='does not match'):
        fill_impact(machine,dict(region,upper_right=[800003,820003]))
    first = fill_impact(machine,region,times='1230')
    report = load_json(first['report'])
    validate_schema(report,load_json('config/schema/fill_impact.schema.json'))
    work = Path(first['work'])
    definition = load_json(work/'counterfactual.json')
    assert definition['source_identity']['sources'][0]['sha256'] == digest(source)
    counterfactual = RawCounterfactual(work)
    manifest = load_json(publication/'run_manifest.json')
    raw_shade, _ = counterfactual.layers(report['frames'][0],manifest['cells'][0])
    assert raw_shade[2,2]==255
    directory = Path(first['report']).parent/'20260107/1230'
    dep_path = next((directory/'dependency').glob('*.tif'))
    with rasterio.open(dep_path) as ds, rasterio.open(directory/'dependency.vrt') as vrt:
        actual = ds.read(1)
        assert ds.nodata==vrt.nodata==255
        assert np.array_equal(actual,vrt.read(1))
    assert report['frames'][0]['groups']['land']['counts']['3'] == int(actual[2,2]==3)
    second = fill_impact(machine,region)
    assert second['work']==first['work']
    assert [event['action'] for event in second['events']]==['verify']
    assert load_json(second['report'])==report
    counterfactual.mosaics[0].unlink()
    repaired = fill_impact(machine,region)
    assert [event['action'] for event in repaired['events']]==['resume']
    assert load_json(repaired['report'])==report
    assert {p:digest(p) for p in publication.rglob('*') if p.is_file()}==before


def test_completed_empty_run_has_empty_report(catalogue):
    raw,p,machine,put = catalogue
    put(0,0,np.ones((6,8)))
    build(machine,profile=p)
    region = region_config('night','00:00')
    assert run_region(region,machine)['published_frames']==0
    result = fill_impact(machine,region)
    report = load_json(result['report'])
    assert result['frames']==0 and result['events']==[] and report['frames']==[]
    validate_schema(report,load_json('config/schema/fill_impact.schema.json'))


def test_diagnostic_refuses_mismatched_engine_identity(catalogue):
    raw,p,machine,put = catalogue
    put(0,0,np.ones((6,8)))
    build(machine,profile=p)
    region = region_config()
    run_region(region,machine)
    path = v1.ROOT/machine['output_root']/region['name']/'run_manifest.json'
    manifest = load_json(path)
    manifest['engine_hashes']['shade_watch/engine/v1.py'] = '0'*64
    atomic_json(path,seal(manifest))
    with pytest.raises(InvalidInput,match='does not match'):
        fill_impact(machine,region)


def test_dsm_only_results_equal_with_coastline_denied(catalogue):
    from shade_watch.publish.planning import prepare

    raw,p,machine,put = catalogue
    data = np.ones((6,8),np.float32)
    data[2,2] = -9999
    data[:,6:] = -9999
    put(0,0,data)
    coastline = raw.parent/'coastline'
    coastline.mkdir()
    marker = coastline/'marker'
    marker.write_text('map fixture')
    region = region_config('blackout')
    readable = build(machine,profile=p)
    plan = prepare(region,machine)
    run_region(region,machine)
    report = fill_impact(machine,region)
    expected = load_json(report['report'])
    folder = v1.ROOT/machine['output_root']/region['name']
    frame_hashes = load_json(folder/'20260107/1230/frame.json')['files']
    mode = coastline.stat().st_mode & 0o777
    coastline.chmod(0)
    try:
        with pytest.raises(PermissionError):
            marker.read_bytes()
        denied = build(machine,profile=p)
        assert denied['view_id']==readable['view_id'] and denied['reproduced']
        second = dict(machine,output_root='runs/denied')
        assert prepare(region,second).document['run_id']==plan.document['run_id']
        run_region(region,second)
        folder = v1.ROOT/second['output_root']/region['name']
        assert load_json(folder/'20260107/1230/frame.json')['files']==frame_hashes
        result = fill_impact(second,region)
        assert load_json(result['report'])==expected
    finally:
        coastline.chmod(mode)
