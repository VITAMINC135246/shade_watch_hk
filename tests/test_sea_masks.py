import hashlib
import json
import numpy as np
import pytest
from rasterio.transform import from_origin
from tools.sea_view.masks import Coastline,fill_mask


def polygon(rings): return dict(type='Polygon',coordinates=rings)


def make_map(tmp_path,features):
    items=[]
    for code,geom in features:
        xy=np.array([p for ring in geom['coordinates'] for p in ring])
        items.append(dict(type='Feature',properties=dict(code=code),geometry=geom,
                          bbox=[*xy.min(axis=0).tolist(),*xy.max(axis=0).tolist()]))
    path=tmp_path/'coastline.geojson'
    path.write_text(json.dumps(dict(type='FeatureCollection',features=items)))
    (tmp_path/'manifest.json').write_text(json.dumps(dict(vector_file=path.name,
        vector_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),crs='EPSG:2326')))
    return Coastline(tmp_path)


def test_hole_overlap_and_nodata(tmp_path):
    outer=[[0,0],[4,0],[4,4],[0,4],[0,0]]
    hole=[[1,1],[1,3],[3,3],[3,1],[1,1]]
    land=[[0,0],[1,0],[1,4],[0,4],[0,0]]
    coast=make_map(tmp_path,[('SEF',polygon([outer,hole])),('LAF',polygon([land]))])
    sea,laf=coast.masks((8,8),from_origin(0,4,.5,.5))
    assert not sea[2:6,2:6].any()
    assert not sea[:,:2].any() and laf[:,:2].all()
    assert sea[:,6:].all()
    values=np.full((8,8),-9999.,np.float32)
    values[0,7]=5
    values[1,7]=np.nan
    fill=fill_mask(values,sea)
    assert not fill[0,7] and fill[1,7]
    assert not (fill & laf).any()


def test_sliver_and_exact_centre_edge(tmp_path):
    # GDAL polygon centre rule burns the right edge, excludes the left edge.
    # The boundary rule is recorded, not replaced by a custom geometric predicate.
    edge=[[.25,0],[1.25,0],[1.25,2],[.25,2],[.25,0]]
    sliver=[[1.51,0],[1.60,0],[1.60,2],[1.51,2],[1.51,0]]
    coast=make_map(tmp_path,[('SEF',polygon([edge])),('SEF',polygon([sliver]))])
    sea,land=coast.masks((4,4),from_origin(0,2,.5,.5))
    assert np.array_equal(sea,np.tile([False,True,True,False],(4,1)))
    assert not land.any()


def test_vector_integrity(tmp_path):
    coast=make_map(tmp_path,[])
    assert not coast.masks((2,2),from_origin(0,1,.5,.5))[0].any()
    (tmp_path/'coastline.geojson').write_text('{}')
    with pytest.raises(ValueError,match='hash changed'): Coastline(tmp_path)


def test_eight_neighbour_boundary_and_valid_samples():
    from tools.sea_view.scan import adjacent_values
    values=np.full((5,5),7.,np.float32)
    values[0,0]=-9999
    values[2,2]=np.nan
    sea=np.zeros((5,5),bool);sea[0,0]=True
    # A fill in the neighbouring tile's halo reaches the target corner diagonally.
    assert np.array_equal(adjacent_values(values,sea),np.array([7.],np.float32))
    sea[2,2]=True
    assert adjacent_values(values,sea).size==8


def test_fill_bit_invariants_and_synthetic_lattice():
    from tools.sea_view.build import classify_surface,synthetic_cells
    a=np.array([[1.,-9999.,np.nan],[np.inf,-9999.,-3]],np.float32)
    sea=np.array([[1,1,0],[0,0,1]],bool)
    filled,surface,mask=classify_surface(a,sea)
    assert np.array_equal(filled.view(np.uint32)[~mask],a.view(np.uint32)[~mask])
    assert filled[0,1]==np.float32(1.6)
    assert np.array_equal(surface,[[0,1,255],[255,255,0]])
    target=dict(path='native.tif',width=1500,height=1200,crs='EPSG:2326',nodata=-9999,bounds=(800000,820000,800750,820600))
    supplied,missing=synthetic_cells([target],[target])
    assert supplied==[target] and len(missing)==24
    assert len({m['path'] for m in missing})==24
    from src.spatial import intersects
    assert all(not intersects(m['bounds'],target['bounds']) for m in missing)


def test_rebuild_and_surface_helpers(tmp_path,monkeypatch):
    import rasterio
    from tools.sea_view import build
    from tools.sea_view.helpers import read_surface_window,effective_policy
    coast=make_map(tmp_path,[('SEF',polygon([[[0,0],[4,0],[4,2],[0,2],[0,0]]]))])
    raw=tmp_path/'native.tif';trans=from_origin(0,2,.5,.5)
    values=np.full((4,4),-9999,np.float32);values[0,0]=8
    with rasterio.open(raw,'w',driver='GTiff',width=4,height=4,count=1,dtype='float32',
                       crs='EPSG:2326',nodata=-9999,transform=trans) as ds: ds.write(values,1)
    rec=dict(path=str(raw),width=4,height=4,crs='EPSG:2326',nodata=-9999,bounds=(0,0,2,2),transform=tuple(trans)[:6])
    synth=dict(rec,path='SEA_E2_N2.tif',bounds=(2,0,4,2),transform=tuple(from_origin(2,2,.5,.5))[:6])
    monkeypatch.setattr(build,'synthetic_cells',lambda targets,records: ([rec],[synth]))
    args=('fixture',[rec],[rec],coast,tmp_path/'views',tmp_path/'staging')
    view=build.build_records(*args)
    assert build.build_records(*args)==view
    surface,t=read_surface_window(view,(0,0,4,2))
    assert surface.shape==(4,8) and surface[0,0]==0 and np.all(surface[1:]==1)
    odd,ot=read_surface_window(view,(.5,.5,3.5,1.5))
    assert np.array_equal(odd,surface[1:3,1:7])
    result=tmp_path/'index.json'
    result.write_text(json.dumps(dict(policy='SW-V1-POLICY-1.0',source_identities=[dict(path=str(view/'tiles/native.tif'))])))
    assert effective_policy(result)['view_id']==view.name
    with pytest.raises(ValueError,match='lattice'): read_surface_window(view,(.1,0,1,1))
    m=view/'manifest.json';m.write_text(m.read_text().replace('1.6','1.7'))
    with pytest.raises(ValueError,match='identity'): read_surface_window(view,(0,0,1,1))
