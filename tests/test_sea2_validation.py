import json
from pathlib import Path

import numpy as np

from tools.sea2.validation_worker import metrics, report_scope
from tools.sea2.rule import Components
from tools.shade_map.common import atomic_json,digest
import pytest
from tools.sea2.validate_ib5000 import require_reader_versions


def test_map_counts_denominators_and_voids():
    surface=np.array([[0,1,2,254,255,1]],np.uint8)
    sea=np.array([[1,1,0,1,1,0]],bool); land=np.array([[0,0,1,0,0,0]],bool)
    result=metrics(surface,sea,land,[0,0,6,1],[0,0,5,1],1)
    assert result['water_in_supplied_tiles']==2
    assert result['false_water']==1 and result['false_water_synthetic']==1
    assert result['missed_sea_254']==1 and result['missed_sea_255']==1
    assert result['land_voids_inside_SEF']==1
    assert result['water_outside_coverage_bbox']==1 and result['water_neither_class']==1


def test_large_false_water_components_join_across_cells():
    class Maps:
        manifest=dict(coverage_bbox=[0,0,120,40])
        def masks(self,name,bounds,shape):return np.zeros(shape,bool),np.ones(shape,bool)
    cells=[dict(id='a',key=[0,0],bounds=[0,0,60,40]),dict(id='b',key=[1,0],bounds=[60,0,120,40])]
    result=report_scope(cells,lambda cell:np.ones((40,60),np.uint8),Maps(),dict(resolution=1,domain_bounds=[0,0,120,40]))
    assert result['false_water']==4800
    assert len(result['false_water_components_over_2500'])==1
    assert result['false_water_components_over_2500'][0]['pixels']==4800
    assert result['false_water_fraction_of_water_in_supplied_tiles']==1


def test_reader_refuses_missing_or_wrong_pinned_environment():
    expected={'certifi':'2025.8.3','numpy':'2.2.6','packaging':'25.0','pyogrio':'0.11.1','shapely':'2.1.1'}
    assert require_reader_versions(expected.get)==expected
    with pytest.raises(RuntimeError,match='unavailable or not pinned'):require_reader_versions(lambda name:None)
    expected['numpy']='2.5.3'
    with pytest.raises(RuntimeError,match='unavailable or not pinned'):require_reader_versions(expected.get)
