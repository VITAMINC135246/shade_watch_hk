"""Artificial geometries are automated fixtures, never observational evidence."""
import json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from src.spatial import Grid, inventory, cores, read_window, target_grid, region_stats, seam_audit, digest_file
from src.pipeline import calculate_core, process_core, valid_cache, cache_paths, execute
from src.shade_watch import classify
from src.horizon import pixel_centred_horizon


def fixture_tiles(tmp_path):
    rng = np.random.default_rng(29)
    z = rng.uniform(0, 2, (64, 70)).astype(np.float32)
    z[18:23, 32:38] = 25  # crosses an edge and corner of several layouts
    z[44:48, 60:65] = 50
    z[34:37, 27:31] = -9999
    paths = []
    for c in (0,35):
        p = tmp_path/f'source_{c}.tif'; paths.append(p)
        with rasterio.open(p,'w',driver='GTiff',width=35,height=64,count=1,dtype='float32',
                           crs='EPSG:2326',transform=from_origin(800000+c*.5,820000,.5,.5),nodata=-9999) as ds:
            ds.write(z[:,c:c+35],1)
    return inventory(paths), Grid(70,64,tuple(from_origin(800000,820000,.5,.5))[:6],'EPSG:2326')


@pytest.mark.parametrize('az', [0,45,90,135,225,315])
def test_exact_chunk_equivalence_edges_corners_gaps_low_sun(tmp_path, az):
    records, grid = fixture_tiles(tmp_path)
    ref = calculate_core(records,grid,(0,0,70,64),az,10,10)
    for size in (17,32,71,(35,64),(35,31)):
        got = [np.empty((64,70),a.dtype) for a in ref]
        owners = np.zeros((64,70),np.uint8)
        for c,r,w,h in cores(grid,size):
            pieces = calculate_core(records,grid,(c,r,w,h),az,10,10)
            for target, piece in zip(got,pieces):
                target[r:r+h,c:c+w] = piece
            owners[r:r+h,c:c+w] += 1
        assert np.all(owners == 1)
        for a,b in zip(ref,got):
            assert np.array_equal(a,b,equal_nan=True)
        for elevation in (.1, 5, 30, 65):
            a = classify(ref[0],ref[1].astype(bool),np.isfinite(ref[0]),elevation,20)
            b = classify(got[0],got[1].astype(bool),np.isfinite(got[0]),elevation,20)
            for x,y in zip(a,b):
                assert np.array_equal(x,y)
            assert np.array_equal(a[0] != 255,b[0] != 255)


def test_global_parity_with_odd_array_origins_and_distance_boundary():
    dsm = np.zeros((30,30),np.float32)
    dsm[10,14] = 30  # 2 m from target, exactly at cutoff
    dsm[10,15] = 300 # outside cutoff, never permitted
    rows,cols = np.array([10]), np.array([10])
    a = pixel_centred_horizon(dsm,rows,cols,90.,2.,2.)
    b = pixel_centred_horizon(dsm[3:,3:],rows-3,cols-3,90.,2.,2.,.5,3,3)
    for x,y in zip(a,b):
        assert np.array_equal(x,y,equal_nan=True)
    assert a[2][0] <= 2
    dsm[10,14] = 0
    assert pixel_centred_horizon(dsm,rows,cols,90.,2.,2.)[0][0] == 0
    # Cell-centre cutoff also excludes diagonal nearest cells beyond radius.
    dsm[:] = 0; dsm[7,13] = 100
    assert pixel_centred_horizon(dsm,rows,cols,45.,2.,2.)[0][0] == 0


def test_native_boundary_and_exact_custom_alignment(tmp_path):
    records,grid = fixture_tiles(tmp_path)
    from pyproj import Transformer
    lon,lat = Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True).transform(800017.5,819990)
    study = dict(longitude=lon,latitude=lat)
    # Roundtrip can differ by nanometres; use exact projected test via patch.
    from unittest.mock import patch
    with patch('src.spatial.Transformer.from_crs') as trans:
        trans.return_value.transform.return_value = (800017.5,819990.)
        native = target_grid(records,study)
        assert native.selected_source == records[1]['path']
        custom = target_grid(records,study,'custom',20,15)
    assert custom.bounds() == (800007.5,819982.5,800027.5,819997.5)
    all_data = read_window(records,custom,(0,0,40,30))
    out = np.empty_like(all_data)
    for c,r,w,h in cores(custom,13):
        out[r:r+h,c:c+w] = read_window(records,custom,(c,r,w,h))
    assert np.array_equal(all_data,out,equal_nan=True)
    # Fractional shift preserves whole-grid sampling.
    custom = replace(custom,transform=tuple(from_origin(800007.73,819997.73,.5,.5))[:6])
    ref = read_window(records,custom,(0,0,40,30))
    for c,r,w,h in cores(custom,13):
        assert np.array_equal(ref[r:r+h,c:c+w], read_window(records,custom,(c,r,w,h)),equal_nan=True)


def test_incompatible_and_overlapping_grids_are_rejected(tmp_path):
    records,grid = fixture_tiles(tmp_path)
    with pytest.raises(ValueError,match='Ambiguous'):
        inventory([records[0]['path'],records[0]['path']])
    with rasterio.open(records[1]['path'],'r+') as ds:
        ds.transform = from_origin(800017.6,820000,.5,.5)
    with pytest.raises(ValueError,match='Incompatible'):
        inventory([r['path'] for r in records])


def test_restart_validates_corruption_and_failed_status(tmp_path):
    records,grid = fixture_tiles(tmp_path)
    cache = tmp_path/'cache';cache.mkdir()
    core=(0,0,17,17)
    a=process_core(records,grid,core,[45,90],cache,'key',10,10)
    assert a['computed']==2
    p,status=cache_paths(cache,core,45)
    assert valid_cache(cache,grid,core,45,'key')
    assert not valid_cache(cache,grid,core,45,'changed-grid-or-source')
    # Simulate interruption before publication and a truncated existing output.
    status.write_text(json.dumps({'status':'running','key':'key'}));p.write_bytes(b'truncated')
    b=process_core(records,grid,core,[45,90],cache,'key',10,10)
    assert b['computed']==1 and b['reused']==1
    assert valid_cache(cache,grid,core,45,'key')
    with rasterio.open(p) as ds:
        result=ds.read()
    ref=calculate_core(records,grid,core,45,10,10)
    assert np.array_equal(result,np.stack(ref),equal_nan=True)


def test_window_stats_seams_and_missing_outer_coverage(tmp_path):
    records,grid=fixture_tiles(tmp_path)
    stats=region_stats(records,grid,(0,0,70,64))
    a=read_window(records,grid,(0,0,70,64))
    assert stats['valid_pixels']==np.isfinite(a).sum()
    seam=seam_audit(records)
    diff=np.abs(a[:,34]-a[:,35]);diff=diff[np.isfinite(diff)]
    assert seam['pairs_of_adjacent_valid_pixels']==len(diff)
    assert seam['max_abs_difference_m']==diff.max()
    h,s,_=calculate_core(records,grid,(0,0,3,3),315,10,10)
    assert not np.any(s)
    labels,q=classify(h,s.astype(bool),np.isfinite(h),89,0)
    assert np.all(labels==255) and np.all(q==2)


@pytest.mark.parametrize("workers", [2,3])
def test_parallel_equal_to_single_and_failure_propagation(tmp_path, workers):
    records,grid=fixture_tiles(tmp_path)
    grid=replace(grid,width=20,height=17)
    single=tmp_path/'single'; parallel=tmp_path/'parallel'
    list(execute(records,grid,13,1,[45],single,'key',10,10))
    list(execute(records,grid,13,workers,[45],parallel,'key',10,10))
    for core in cores(grid,13):
        a,_=cache_paths(single,core,45);b,_=cache_paths(parallel,core,45)
        with rasterio.open(a) as aa,rasterio.open(b) as bb:
            assert np.array_equal(aa.read(),bb.read(),equal_nan=True)
    broken=[{**records[0],'path':str(tmp_path/'missing.tif')}]
    with pytest.raises(Exception):
        list(execute(broken,grid,13,workers,[45],tmp_path/'broken','key',10,10))


def test_large_png_pieces_and_window_assembly(tmp_path):
    from datetime import datetime
    from src.pipeline import profile,assemble_frame,export_pngs,render_frame
    from src.solar import HKT,position,daylight_bounds
    from src.shade_watch import nearest_bin
    from PIL import Image
    # Deliberately synthetic labels/horizons test publication only, not real inputs.
    grid=Grid(2051,2001,tuple(from_origin(800000,820000,.5,.5))[:6],'EPSG:2326')
    instant=datetime(2026,1,7,14,30,tzinfo=HKT)
    sun=position(instant,22.340113333,114.263323333)
    cache=tmp_path/'cache';cache.mkdir()
    for core in cores(grid,1024):
        p,_=cache_paths(cache,core,nearest_bin(sun.azimuth_deg))
        with rasterio.open(p,'w',**profile(grid,core,3,'float32',None)) as ds:
            a=np.zeros((core[3],core[2]),np.float32)
            a[::2,::2]=80
            if core[0]==0 and core[1]==0: a[0,0]=np.nan
            ds.write(a,1);ds.write(np.ones(a.shape,np.float32),2);ds.write(np.zeros(a.shape,np.float32),3)
    out=tmp_path/'out'
    result=assemble_frame(grid,1024,cache,instant,sun,0,out,'key')
    assert sum(result['counts'].values())==grid.width*grid.height
    assert result['counts']['invalid_or_uncertain']==1
    path=Path(result['raster'])
    export_pngs(path,out,grid,1024)
    count=0
    with rasterio.open(path) as ds:
        for p in (out/'png').glob('*.png'):
            meta=json.loads(p.with_suffix('.json').read_text());core=meta['core']
            with Image.open(p) as im: a=np.asarray(im)
            assert np.array_equal(a[:,:,0],ds.read(1,window=rasterio.windows.Window(*core)))
            count+=a.shape[0]*a.shape[1]
    assert count==grid.width*grid.height
    sunrise,sunset=daylight_bounds(instant.date(),22.340113333,114.263323333)
    frame,display=render_frame(path,instant,sun,grid,.99,sunrise,sunset,1000)
    assert display['width']==1000 and frame.width<1500
    # Resume verifies final hashes. A corruption must trigger deterministic rebuild.
    original=digest_file(path)
    path.write_bytes(b'bad')
    assemble_frame(grid,1024,cache,instant,sun,0,out,'key')
    assert digest_file(path)==original


def test_external_mask_is_part_of_cache_source_identity(tmp_path):
    from src.pipeline import include_auxiliary_source_identities, fingerprint
    records,grid=fixture_tiles(tmp_path)
    before=fingerprint(include_auxiliary_source_identities(records))
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(records[0]['path'],'r+') as ds:
            mask=np.full((64,35),255,np.uint8);mask[5,5]=0;ds.write_mask(mask)
    after=include_auxiliary_source_identities(inventory([r['path'] for r in records]))
    assert after[0]['auxiliary_files']
    assert fingerprint(after)!=before
    assert np.isnan(read_window(after,grid,(5,5,1,1))[0,0])


def test_unmanaged_existing_results_are_protected(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    config=json.loads((pipeline.ROOT/'config/processing.json').read_text())
    monkeypatch.setattr(pipeline,'ROOT',tmp_path)
    old=tmp_path/'outputs/old_results';old.mkdir(parents=True)
    original=old/'previous.jpg';original.write_bytes(b'user-owned previous output')
    config['output_directory']='outputs/old_results'
    with pytest.raises(ValueError,match='unmanaged existing results'):
        pipeline.run(config)
    assert original.read_bytes()==b'user-owned previous output'


def test_native_tile_is_one_spatial_unit_and_neighbor_output_has_one_owner(tmp_path):
    from src.pipeline import resolve_core_layout
    from src.spatial import expand, intersects
    from pyproj import Transformer
    records, larger = fixture_tiles(tmp_path)
    lon, lat = Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True).transform(800005,819995)
    study = dict(longitude=lon, latitude=lat)
    native = target_grid(records, study, 'native_tile')
    size, layout = resolve_core_layout({'core_mode':'native_tile'}, records, study, native)
    assert size == (35,64)  # metadata-derived rectangular tile, no hardcoded dimensions
    assert layout['dimension_source'] == records[0]['path']
    assert list(cores(native,size)) == [(0,0,35,64)]
    size, _ = resolve_core_layout({'core_mode':'native_tile'}, records, study, larger)
    jobs = list(cores(larger,size))
    assert jobs == [(0,0,35,64), (35,0,35,64)]
    assert not intersects(larger.bounds(jobs[0]), larger.bounds(jobs[1]))
    assert intersects(larger.bounds(expand(jobs[0],20)), larger.bounds(expand(jobs[1],20)))
    owners = np.zeros((64,70),np.uint8)
    for c,r,w,h in jobs:
        owners[r:r+h,c:c+w] += 1
    assert np.all(owners == 1)
    # The custom target origin is preserved even when it has a fractional offset.
    shifted = replace(larger, transform=tuple(from_origin(800000.13,820000.13,.5,.5))[:6])
    shifted_size, _ = resolve_core_layout({'core_mode':'native_tile'}, records, study, shifted)
    assert shifted_size == size and shifted.affine.c == 800000.13


def test_2048_is_a_per_axis_limit_not_a_total_pixel_limit():
    from src.pipeline import resolve_core_layout
    from src.spatial import core_dimensions
    grid = Grid(1500,1200,tuple(from_origin(845000,822800,.5,.5))[:6],'EPSG:2326')
    size, _ = resolve_core_layout({'core_mode':'fixed','core_size_px':2048}, [], {}, grid)
    assert size == (2048,2048)
    assert list(cores(grid,size)) == [(0,0,1500,1200)]
    for invalid in (0,True,[-1,1200],[1500], '2048'):
        with pytest.raises(ValueError):
            core_dimensions(invalid)


def test_geometric_default_center_and_explicit_custom_override(tmp_path):
    from src.pipeline import resolve_output
    from pyproj import Transformer
    records, _ = fixture_tiles(tmp_path)
    lon, lat = Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True).transform(800002,819998)
    study = dict(longitude=lon,latitude=lat)
    config = dict(output_mode='native_tile',custom_width_m=10,custom_height_m=10)
    grid, center, _ = resolve_output(config,records,study)
    assert grid.bounds() == records[0]['bounds']
    assert (center['easting_m'],center['northing_m']) == (800008.75,819984)
    assert center['selector_latitude'] == lat
    assert center['latitude'] != lat
    lon2, lat2 = Transformer.from_crs('EPSG:2326','EPSG:4326',always_xy=True).transform(800021,819995)
    custom = {**config,'output_mode':'custom','custom_center_wgs84':dict(latitude=lat2,longitude=lon2)}
    shifted, center, _ = resolve_output(custom,records,study)
    assert center['placement'] == 'explicit_custom_center'
    assert center['easting_m'] == pytest.approx(800021,abs=.001)
    assert center['northing_m'] == pytest.approx(819995,abs=.001)
    assert shifted.width == shifted.height == 20
    with pytest.raises(ValueError,match='explicit center requires'):
        resolve_output({**config,'custom_center_wgs84':study},records,study)


def test_native_mosaic_preserves_source_bounds_and_shared_center(tmp_path):
    from src.pipeline import resolve_output, resolve_core_layout
    from src.spatial import native_mosaic_grid, output_reference
    records, whole = fixture_tiles(tmp_path)
    names = [Path(r['path']).name for r in reversed(records)]
    config = dict(output_mode='native_mosaic',native_tile_names=names,core_mode='native_tile')
    grid, center, _ = resolve_output(config,records,dict(latitude=22,longitude=114))
    assert grid.bounds() == whole.bounds()
    size, _ = resolve_core_layout(config,records,{},grid)
    assert size == (35,64)
    assert [grid.bounds(core) for core in cores(grid,size)] == [r['bounds'] for r in records]
    assert (center['easting_m'],center['northing_m']) == (800017.5,819984)
    assert output_reference(grid) == output_reference(whole)
    with pytest.raises(ValueError,match='distinct'):
        native_mosaic_grid(records,names+names)
    with pytest.raises(ValueError,match='missing'):
        native_mosaic_grid(records,['missing.tif'])
    distant = {**records[1], 'bounds':(800035,819968,800052.5,820000)}
    with pytest.raises(ValueError,match='without gaps'):
        native_mosaic_grid([records[0],distant],names)
    with pytest.raises(ValueError,match='uniform'):
        native_mosaic_grid([records[0],{**records[1],'width':34}],names)
