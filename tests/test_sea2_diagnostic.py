from pathlib import Path

import numpy as np
import pytest

from tools.sea2.__main__ import main
from tools.sea2.void_impact import frame_metrics, require_run, counterfactual_view
from tools.shade_map.config import InvalidInput, validate_schema, load_json
from test_sea2_view import catalogue


def test_metrics_partition_and_splits():
    surface=np.array([[255,0,0,0,0,0,0,0,0,1,2,254]],np.uint8)
    shade=np.array([[255,255,255,255,255,255,0,1,255,0,1,255]],np.uint8)
    quality=np.array([[1,2,2,2,2,3,0,0,4,0,0,1]],np.uint8)
    cf=shade.copy(); cq=quality.copy(); cf[0,1:4]=[0,1,255]; cq[0,1:4]=[0,0,3]
    r=frame_metrics(surface,shade,quality,cf,cq)
    assert r['land_pixels']==9
    assert r['counts']==dict(void_pixels=1,void_caused=3,other_quality2=1,quality3=1,sunlit=1,shaded=1,quality4=1,
                             void_caused_sunlit=1,void_caused_shaded=1,void_caused_quality3=1)
    assert r['void_attributable_fraction']==4/9
    bad=cq.copy(); bad[0,1]=1
    with pytest.raises(RuntimeError,match='partition'): frame_metrics(surface,shade,quality,cf,bad)


def test_refuses_without_matching_complete_sea_run(catalogue,capsys):
    raw,p,machine,put=catalogue; put(0,0,np.ones((6,8)))
    region=dict(schema='shade-map-region-1.0',name='missing',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800004,820003],time=dict(mode='instants',instants=['2026-01-07T12:30']),dsm_source='sea-2.0')
    with pytest.raises(InvalidInput,match='run F first'): require_run(machine,region)
    region['dsm_source']='raw'
    with pytest.raises(InvalidInput,match='sea-2.0'): require_run(machine,region)
    assert not (Path(machine['output_root'])/'_diagnostics').exists()


def test_counterfactual_changes_only_enclosed_void(catalogue):
    from tools.sea2.build import build
    from tools.sea2.view import read_manifest
    import rasterio
    raw,p,machine,put=catalogue
    a=np.ones((6,8),np.float32); a[2,2]=-9999; a[:,6:]=-9999
    source=put(0,0,a); result=build(machine,profile=p); base=Path(result['path'])
    run=dict(cells=[dict(native_bounds=[800000,820000,800004,820003])])
    diagnostic,doc=counterfactual_view(base,run)
    with rasterio.open(base/'tiles'/source.name) as ds: before=ds.read(1)
    with rasterio.open(diagnostic/'tiles'/source.name) as ds: after=ds.read(1)
    assert before[2,2]==-9999 and after[2,2]==0
    mask=np.ones(a.shape,bool); mask[2,2]=False
    assert np.array_equal(before.view(np.uint32)[mask],after.view(np.uint32)[mask])
    assert doc['diagnostic'] and doc['filled_void_pixels']==1
    assert counterfactual_view(base,run)[0]==diagnostic


def test_diagnostic_end_to_end_and_resume(catalogue):
    from tools.sea2.build import build
    from tools.sea2.void_impact import void_impact
    from tools.shade_map.runner import run_region
    raw,p,machine,put=catalogue
    a=np.ones((6,8),np.float32); a[2,2]=-9999; a[:,6:]=-9999; put(0,0,a)
    build(machine,profile=p)
    region=dict(schema='shade-map-region-1.0',name='void_fixture',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800004,820003],time=dict(mode='instants',instants=['2026-01-07T12:30']),dsm_source='sea-2.0')
    run_region(region,machine)
    first=void_impact(machine,region)
    report=load_json(first['report'])
    validate_schema(report,load_json('config/schema/void_impact.schema.json'))
    assert report['frames'][0]['counts']['void_pixels']==1
    second=void_impact(machine,region)
    assert all(e['action']=='verify' for e in second['events'])
    assert load_json(second['report'])==report


def test_completed_empty_run_has_empty_diagnostic(catalogue):
    from tools.sea2.build import build
    from tools.sea2.void_impact import void_impact
    from tools.shade_map.runner import run_region
    raw,p,machine,put=catalogue;put(0,0,np.ones((6,8)))
    build(machine,profile=p)
    region=dict(schema='shade-map-region-1.0',name='night',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800004,820003],time=dict(mode='instants',instants=['2026-01-07T00:00']),dsm_source='sea-2.0')
    assert run_region(region,machine)['published_frames']==0
    result=void_impact(machine,region);report=load_json(result['report'])
    assert result['frames']==0 and result['events']==[] and report['dates']==[]
    validate_schema(report,load_json('config/schema/void_impact.schema.json'))


def test_diagnostic_refuses_different_engine_identity(catalogue):
    from src import v1
    from tools.sea2.build import build
    from tools.sea2.void_impact import void_impact
    from tools.shade_map.runner import run_region
    from tools.shade_map.common import atomic_json,seal
    raw,p,machine,put=catalogue;put(0,0,np.ones((6,8)))
    build(machine,profile=p)
    region=dict(schema='shade-map-region-1.0',name='changed_engine',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800004,820003],time=dict(mode='instants',instants=['2026-01-07T12:30']),dsm_source='sea-2.0')
    run_region(region,machine)
    path=v1.ROOT/machine['output_root']/region['name']/'run_manifest.json'
    manifest=load_json(path);manifest['engine_hashes']['src/v1.py']='0'*64;atomic_json(path,seal(manifest))
    with pytest.raises(InvalidInput,match='does not match'):void_impact(machine,region)
