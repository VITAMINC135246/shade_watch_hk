import numpy as np
import pytest

from shade_watch.fill.validation_worker import enclosed_components, metrics, report_scope
from shade_watch.fill.validate_ib5000 import require_reader_versions


def test_map_counts_denominators_and_enclosed():
    surface=np.array([[0,1,2,4,3,1]],np.uint8)
    sea=np.array([[1,1,0,1,1,0]],bool)
    land=np.array([[0,0,1,0,0,0]],bool)
    result=metrics(surface,sea,land,[0,0,6,1],[0,0,5,1],1)
    assert result['water_pixels']==3
    assert result['false_water']==1
    assert result['missed_sea_4']==1 and result['missed_sea_3']==1
    assert result['class_3_inside_SEF']==1
    assert result['mapped_sea_nodata']==3
    assert result['water_inside_SEF_minus_LAF']==1
    assert result['water_outside_coverage_bbox']==1 and result['water_neither_class']==1


def test_large_false_water_components_join_only_adjacent_cells():
    class Maps:
        manifest=dict(coverage_bbox=[0,0,240,40])

        def masks(self,name,bounds,shape):
            return np.zeros(shape,bool),np.ones(shape,bool)

    cells=[dict(id='a',key=[0,0],bounds=[0,0,60,40]),dict(id='b',key=[1,0],bounds=[60,0,120,40]),
           dict(id='d',key=[3,0],bounds=[180,0,240,40])]
    result=report_scope(cells,lambda cell:np.ones((40,60),np.uint8),Maps(),dict(resolution=1,domain_bounds=[0,0,240,40]))
    assert result['false_water']==7200
    assert len(result['false_water_components_over_2500'])==1
    assert result['false_water_components_over_2500'][0]['pixels']==4800
    assert result['false_water_fraction']==1


def test_class_3_report_deduplicates_shore_pixels_and_crosses_native_border():
    surfaces = {}
    cells = []
    for i in range(2):
        pixels = np.zeros((102,60),np.uint8)
        if i==0:
            pixels[1:-1,1:] = 3
        else:
            pixels[1:-1,:-1] = 3
        surfaces[str(i)] = pixels
        cells.append(dict(id=str(i),key=[i,0],bounds=[i*60,0,(i+1)*60,102],
                          counts={'0':int((pixels==0).sum()),'3':int((pixels==3).sum())}))

    class Catalogue:
        height,width,res = 102,60,1

        def window(self,key):
            return key

        def read(self,key):
            values = surfaces[str(key[0])]
            return np.where(values==3,-9999,10+key[0]).astype(np.float32)

    result = enclosed_components(cells,lambda cell:surfaces[cell['id']],Catalogue())
    assert len(result)==1
    assert result[0]['bounds']==[1,1,119,101]
    assert result[0]['cells']==['0','1']
    assert result[0]['pixels']==11800
    assert result[0]['observed_shore_heights_m']==dict(pixels=436,p10=10,median=10.5,p90=11)


def test_reader_refuses_missing_or_wrong_pinned_environment():
    expected={'certifi':'2025.8.3','numpy':'2.2.6','packaging':'25.0','pyogrio':'0.11.1','shapely':'2.1.1'}
    assert require_reader_versions(expected.get)==expected
    with pytest.raises(RuntimeError,match='unavailable or not pinned'):
        require_reader_versions(lambda name:None)
    expected['numpy']='2.5.3'
    with pytest.raises(RuntimeError,match='unavailable or not pinned'):
        require_reader_versions(expected.get)
