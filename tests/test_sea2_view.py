"""Small catalogue tests of view values, reproducibility and F integration."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src import v1
from tools.sea2.build import build, assert_fill
from tools.sea2.provider import SeaSource
from tools.sea2.rule import CODES
from tools.sea2.view import read_manifest, read_surface_window, verify_view
from tools.shade_map.common import digest
from tools.shade_map.config import InvalidInput, load_json, machine_config, region_config
from tools.shade_map.planning import prepare


@pytest.fixture
def catalogue(tmp_path,monkeypatch):
    monkeypatch.setattr(v1,'ROOT',tmp_path)
    raw=tmp_path/'data/raw/dsm'; raw.mkdir(parents=True)
    p=load_json('config/sea_profiles/hk_cedd_2020.json')
    p.update(profile_id='fixture',max_shore_distance_m=2,shore_preference_m=.5)
    monkeypatch.setattr('tools.sea2.profile.load_profile',lambda machine: deepcopy(p))
    machine=dict(schema='shade-map-machine-1.0',dsm_dir=str(raw),output_root='outputs/published',cache_namespace='fixture_raw')
    def put(ix,iy,data):
        path=raw/f'tile_{ix}_{iy}.tif'
        with rasterio.open(path,'w',driver='GTiff',height=6,width=8,count=1,dtype='float32',
                           transform=from_origin(800000+ix*4,820003+iy*3,.5,.5),crs='EPSG:2326',nodata=-9999) as ds:
            ds.write(np.asarray(data,np.float32),1)
        return path
    return raw,p,machine,put


def test_view_fill_synthetic_totals_and_rebuild(catalogue):
    raw,p,machine,put=catalogue
    a=np.full((6,8),-9999,np.float32); a[2:5,2:5]=2; a[3,3]=np.nan
    # Keep a distinct quiet NaN bit pattern outside water for exact preservation.
    a.view(np.uint32)[3,3]=0x7fc00123
    source=put(0,0,a); before=digest(source)
    first=build(machine,profile=p); view=Path(first['path']); doc=verify_view(view)
    surface=read_surface_window(view,[800000,820000,800004,820003])
    assert surface[3,3]==255
    assert_fill(source,view/'tiles'/source.name,surface,p['h_sea_m'])
    assert digest(source)==before
    empty_water=[c for c in doc['cells'] if not c['supplied'] and c['counts']['2']]
    assert len(empty_water)==first['synthetic_tiles']>0
    assert {c['tile_name'] for c in empty_water}=={t['name'] for t in doc['tiles'] if t['synthetic']}
    for c in empty_water:
        assert c['tile_name']=='SEA_'+c['id']+'.tif'
        with rasterio.open(view/'tiles'/c['tile_name']) as ds:
            assert ds.shape==(6,8); assert list(ds.bounds)==c['native_bounds']
    assert doc['totals']=={str(code):sum(c['counts'][str(code)] for c in doc['cells']) for code in CODES}
    second=build(machine,profile=p)
    assert second['reproduced'] and second['view_id']==first['view_id']
    assert read_manifest(view)==doc


def test_enclosed_empty_cell_no_synthetic(catalogue):
    raw,p,machine,put=catalogue
    for y in range(3):
        for x in range(3):
            if (x,y)!=(1,1): put(x,y,np.ones((6,8)))
    result=build(machine,profile=p); view=Path(result['path']); doc=read_manifest(view)
    centre=next(c for c in doc['cells'] if c['key']==[1,1])
    assert centre['counts']['255']==48 and centre['tile_name'] is None
    assert np.all(read_surface_window(view,centre['bounds'])==255)
    for path in raw.glob('*.tif'): assert (view/'tiles'/path.name).is_symlink()


def test_provider_stale_inventory_profile_and_window_overlap(catalogue):
    raw,p,machine,put=catalogue
    a=np.ones((6,8),np.float32); a[:,4:]=-9999; source=put(0,0,a)
    provider=SeaSource(); normalized=machine_config(machine)
    with pytest.raises(InvalidInput,match='run python -m tools.sea2 build'): provider.catalogue(normalized)
    result=build(machine,profile=p); view=Path(result['path'])
    assert provider.catalogue(normalized)==view/'tiles'
    assert provider.cache_namespace(normalized)=='sea_fill_v2_'+result['view_id'][:12]
    full=read_surface_window(view,[800000,820000,800004,820003])
    crop=read_surface_window(view,[800001,820001,800003,820002])
    assert np.array_equal(crop,full[2:4,2:6])
    p['low_shore_margin_m']=4
    with pytest.raises(InvalidInput,match='sea view missing'): provider.catalogue(normalized)
    p['low_shore_margin_m']=5
    source.touch()
    with pytest.raises(InvalidInput,match='different catalogue'): provider.catalogue(normalized)


def test_F_registry_identity_and_raw_machine_exclusion(catalogue):
    raw,p,machine,put=catalogue
    a=np.ones((6,8),np.float32); a[:,4:]=-9999; put(0,0,a)
    region=dict(schema='shade-map-region-1.0',name='fixture',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800004,820003],time=dict(mode='instants',instants=['2026-01-07T12:30']))
    original=prepare(region,machine)
    other=dict(machine,sea_profile='another_profile')
    assert prepare(region,other).document['run_id']==original.document['run_id']
    build(machine,profile=p)
    region['dsm_source']='sea-2.0'; sea=prepare(region,machine)
    assert sea.document['run_id']!=original.document['run_id']
    assert sea.identity_document['source_identity']['provider']=='sea-2.0'
    assert sea.identity_document['policies']['sea']=='SW-SEA-POLICY-2.0'
    assert np.array_equal(sea.source.read_surface(sea.document['resolved_bounds'],sea.records),
                          read_surface_window(sea.records[0]['_sea2_view'],sea.document['resolved_bounds']))
    assert set(q['key'] for q in sea.adapter_plan['sidecar']['requests']).isdisjoint(q['key'] for q in original.adapter_plan['sidecar']['requests'])


def test_surface_window_rejects_outside_or_fractional(catalogue):
    raw,p,machine,put=catalogue; put(0,0,np.ones((6,8)))
    result=build(machine,profile=p)
    with pytest.raises(InvalidInput,match='aligned'): read_surface_window(result['path'],[800000.1,820000,800001,820001])
    with pytest.raises(InvalidInput,match='outside'): read_surface_window(result['path'],[0,0,1,1])


def test_shifted_tile_metadata_is_preserved_without_ingestion_correction(catalogue):
    from tools.sea2.catalogue import Catalogue
    raw,p,machine,put=catalogue; put(0,0,np.ones((6,8)))
    path=raw/'14NE15A(fixture).tif'; sentinel=float(np.finfo(np.float32).min)
    a=np.full((6,8),sentinel,np.float32); a[:,0]=1; a[2,2]=-9999
    transform=from_origin(800004+9.4e-8,820003+9.4e-8,.5,.5)
    with rasterio.open(path,'w',driver='GTiff',width=8,height=6,count=1,dtype='float32',nodata=sentinel,crs='EPSG:2326',transform=transform) as ds:ds.write(a,1)
    result=build(machine,profile=p); view=Path(result['path'])
    with rasterio.open(view/'tiles'/path.name) as ds:
        assert ds.transform==transform and ds.nodata==sentinel
        assert np.array_equal(ds.read(1).view(np.uint32),a.view(np.uint32))
    assert read_manifest(view)['shifted_origin_connectivity_only']
    assert read_manifest(view)['grid']['nodata']==-9999


def test_provider_refuses_missing_or_unexpected_view_tiles(catalogue):
    raw,p,machine,put=catalogue; put(0,0,np.ones((6,8)))
    result=build(machine,profile=p); view=Path(result['path']); provider=SeaSource()
    extra=view/'tiles'/'extra.tif'; extra.write_text('unexpected')
    with pytest.raises(InvalidInput,match='sea view missing'):provider.catalogue(machine_config(machine))
    extra.unlink(); provider.catalogue(machine_config(machine))
    tile=next((view/'tiles').glob('*.tif')); tile.unlink()
    with pytest.raises(InvalidInput,match='sea view missing'):provider.catalogue(machine_config(machine))


class FrozenPublicationEncoding(RuntimeError):
    """The exact, independently reproduced F1.0 allowlist blocker."""


@pytest.mark.xfail(strict=True,raises=FrozenPublicationEncoding,
                   reason='Frozen F1.0 publication allows 0/1/255; SW-B2.0 forbids editing it')
def test_F_publication_preserves_all_five_surface_classes(catalogue):
    from tools.sea2.checks import EvidenceRun
    from tools.shade_map.runner import run_region
    raw,p,machine,put=catalogue
    a=np.ones((6,8),np.float32);a[:,7]=20;a[-1,7]=1;a[0,0]=-9999;a[2,2]=-9999
    put(0,0,a);result=build(machine,profile=p)
    region=dict(schema='shade-map-region-1.0',name='five_classes',crs='hk1980',lower_left=[800000,820000],
                upper_right=[800006,820003],time=dict(mode='instants',instants=['2026-01-07T12:30']),dsm_source='sea-2.0')
    run_folder=v1.ROOT/machine['output_root']/region['name']
    try:
        run_region(region,machine)
    except RuntimeError as exc:
        if str(exc)!='Invalid surface provider/engine encoding':raise
        # The failure is in publication, after the correct five-class provider
        # and unchanged engine have produced readable intermediate evidence.
        evidence=EvidenceRun(run_folder,allow_engine_work=True);frame=evidence.manifest['frames'][0]
        seen=set()
        for cell in evidence.manifest['cells']:
            surface=read_surface_window(result['path'],cell['bounds']);shade,_=evidence.layers(frame,cell)
            seen.update(np.unique(surface));assert np.all(shade[np.isin(surface,[254,255])]==255)
        assert seen==set(CODES) and evidence.solar(frame)
        raise FrozenPublicationEncoding(str(exc)) from exc
    folder=run_folder/'20260107/1230'
    with rasterio.open(folder/'surface.tif') as ds:surface=ds.read(1)
    with rasterio.open(folder/'shade.tif') as ds:shade=ds.read(1)
    assert set(np.unique(surface))==set(CODES)
    assert np.array_equal(surface,read_surface_window(result['path'],[800000,820000,800006,820003]))
    assert np.all(shade[np.isin(surface,[254,255])]==255)
