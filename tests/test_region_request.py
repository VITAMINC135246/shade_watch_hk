"""Development checks for frozen region contract; no independent acceptance."""
import json
from dataclasses import asdict
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from shade_watch.engine import v1, v2
from shade_watch.region import main, plan_region, project_corner, write_region

AT=['2026-01-07T14:31:27+08:00']


@pytest.fixture
def catalogue(tmp_path, monkeypatch):
    monkeypatch.setattr(v1,'ROOT',tmp_path)
    raw=tmp_path/'data/raw'
    raw.mkdir(parents=True)
    for x in (800000,800010):
        for y in (820000,820010):
            with rasterio.open(raw/f'{x}_{y}.tif','w',driver='GTiff',width=20,height=20,
                               count=1,dtype='float32',crs='EPSG:2326',nodata=-9999,
                               transform=from_origin(x,y,.5,.5)) as dst:
                dst.write(np.zeros((20,20),np.float32),1)
    return raw


def region(raw,a=(800002,819992),b=(800018,820008),**kwargs):
    return plan_region(a,b,crs='hk1980',instants=AT,dsm_dir=raw,**kwargs)


@pytest.mark.parametrize('a,b',[
    ((800001,819991),(800004,819994)),
    ((800008,819998),(800012,820002)),
    ((800001.13,819991.04),(800004.43,819994.19)),
])
def test_equivalence_order_and_read_only(catalogue,a,b):
    before=set(v1.ROOT.rglob('*'))
    with patch('shade_watch.engine.v1_cache.pixel_centred_horizon',side_effect=AssertionError('computed')):
        result=region(catalogue,a,b)
    assert before==set(v1.ROOT.rglob('*'))
    req=result['batches'][0]['requests'][0]
    manual=v1.plan_shade(**{k:v for k,v in req.items() if k!='id'})
    part=result['sidecar']['partition'][0]
    assert part['key']==manual.key
    assert part['grid']==asdict(manual.grid)
    assert region(catalogue,b,a)['sidecar']['partition']==result['sidecar']['partition']


@pytest.mark.parametrize('point',[(22.20,114.03),(22.28,114.16),(22.34,114.27),(22.50,114.10),(22.55,114.30)])
def test_bit_exact_engine_transform(point):
    expected=v1.Transformer.from_crs('EPSG:4326','EPSG:2326',always_xy=True).transform(point[1],point[0])
    assert project_corner(point,'wgs84')==expected


@pytest.mark.parametrize('a,b,crs,message',[
    ((114.2,22.3),(114.3,22.4),'wgs84','latitude'),
    ((22.3,181),(22.4,114.3),'wgs84','longitude'),
    ((float('nan'),1),(2,3),'hk1980','finite'),
    ((float('inf'),1),(2,3),'wgs84','finite'),
    ((1,1),(1,2),'hk1980','zero width'),
    ((1,1),(2,1),'hk1980','zero width'),
    ((1,1),(2,2),'hk1980','no DSM'),
    ((1,1),(2,2),'guessed','explicitly'),
])
def test_rejections(catalogue,a,b,crs,message):
    with pytest.raises(ValueError,match=message):
        plan_region(a,b,crs=crs,instants=AT,dsm_dir=catalogue)


def test_wgs84_full_path(catalogue):
    inv=v1.Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True)
    points=[inv.transform(x,y)[::-1] for x,y in [(800002,819992),(800008,819998)]]
    plan=plan_region(*points,crs='wgs84',instants=AT,dsm_dir=catalogue)
    assert plan['sidecar']['transformation_applied']
    assert len(plan['sidecar']['partition'])==1


def test_partition_union_horizon_inventory_and_sidecar(catalogue,tmp_path):
    result=region(catalogue,max_pixels_per_request=300)
    sc=result['sidecar']
    parts=sc['partition']
    assert len(parts)==4
    # Exact pixel-address occupancy checks both coverage and pairwise disjointness.
    occupied=set()
    for part in parts:
        l,b,r,t=part['resolved_bounds']
        pixels={(x,y) for x in range(round(l*2),round(r*2)) for y in range(round(b*2),round(t*2))}
        assert occupied.isdisjoint(pixels)
        occupied.update(pixels)
    l,b,r,t=sc['resolved_bounds']
    assert occupied=={(x,y) for x in range(round(l*2),round(r*2)) for y in range(round(b*2),round(t*2))}
    batch=result['batches'][0]
    checked=v2.plan_batch(**batch)
    assert sum(t['kind']=='horizon' for t in checked.definition['tasks'])==4
    assert len({p for part in parts for p in part['tiles']})==4
    dest=write_region(result,tmp_path/'requests')
    saved=json.loads((dest/'region_request.json').read_text())
    for key in ['original_corners','crs','transformer_description','pyproj_version','proj_version',
                'requested_bounds','resolved_bounds','partition','generated_request_ids']:
        assert key in saved
    assert json.loads((dest/'batch_0000.json').read_text())==batch
    with pytest.raises(FileExistsError): write_region(result,dest)
    with pytest.raises(ValueError,match='separate'): write_region(result,batch['requests'][0]['output_dir'])


def test_multiple_budget_checked_batches(catalogue):
    # One frame per part and a native direction entry fit; four do not.
    result=region(catalogue,max_pixels_per_request=300,artifact_budget_bytes=17_000_000)
    assert len(result['batches'])>1
    for batch in result['batches']:
        assert v2.plan_batch(**batch).definition['resources']['estimated_peak_new_bytes']<=17_000_000
    with pytest.raises(ValueError,match='cannot fit'):
        region(catalogue,max_pixels_per_request=300,artifact_budget_bytes=1)
    with pytest.raises(ValueError,match='no native boundary'):
        region(catalogue,max_pixels_per_request=1)


def test_cli(catalogue,tmp_path,capsys):
    args=['--crs','hk1980','--corner1','800001','819991','--corner2','800003','819993',
          '--at',AT[0],'--dsm-dir',str(catalogue),'--output','work/engine/cli']
    main(['plan',*args])
    assert json.loads(capsys.readouterr().out)['requested_bounds']==[800001,819991,800003,819993]
    main(['write',*args,'--directory',str(tmp_path/'cli_requests')])
    assert (tmp_path/'cli_requests/region_request.json').is_file()
