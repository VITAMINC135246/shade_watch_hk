"""Hand-computed policy fixtures, written before the tiled implementation."""
import numpy as np
import pytest

from shade_watch.fill.profile import validate_profile
from shade_watch.publish.config import InvalidInput, load_json


def profile(**changes):
    p = load_json('config/sea_profiles/hk_cedd_2020.json')
    p.update(max_shore_distance_m=3, shore_preference_m=1)
    p.update(changes)
    return p


@pytest.mark.parametrize('changes', [
    {'connectivity': 8}, {'max_shore_distance_m': -1}, {'h_sea_m': float('nan')},
    {'shore_preference_m': True}, {'unknown': 1}, {'profile_id': '../raw'},
    {'exclusions': [{'id': 'x', 'bounds': [1, 0, 0, 1], 'reason': 'test'}]},
])
def test_invalid_profiles(changes):
    p = load_json('config/sea_profiles/hk_cedd_2020.json'); p.update(changes)
    with pytest.raises(InvalidInput): validate_profile(p)


def test_frozen_profile():
    p = validate_profile(load_json('config/sea_profiles/hk_cedd_2020.json'))
    assert [p[k] for k in ('h_sea_m','low_shore_margin_m','max_shore_distance_m','shore_preference_m','connectivity','exclusions')] == [0,5,1000,50,4,[]]


def classify(a, p=None, supplied=None, tiled=False, shape=(3, 4)):
    from shade_watch.fill.rule import classify_array
    return classify_array(np.array(a, dtype=np.float32), p or profile(),
                          resolution=1, supplied=supplied, cell_shape=shape if tiled else None)


def test_low_shore_and_exact_range():
    a = np.full((3, 7), np.nan); a[:, 0] = 2
    expected = np.tile([0, 1, 1, 1, 4, 4, 4], (3, 1)).astype(np.uint8)
    assert np.array_equal(classify(a), expected)


def test_frozen_one_kilometre_limit_inclusive():
    from shade_watch.fill.rule import classify_array
    a=np.full((1,2003),np.nan,np.float32); a[0,0]=2
    p=load_json('config/sea_profiles/hk_cedd_2020.json')
    result=classify_array(a,p,resolution=.5,cell_shape=(1,200))
    assert np.all(result[0,1:2001]==1)
    assert np.all(result[0,2001:]==4)


def test_distance_retains_actual_subpixel_native_centres():
    from shade_watch.fill.rule import classify_points
    p=load_json('config/sea_profiles/hk_cedd_2020.json')
    bad=np.ones((1,1),bool);empty=np.empty((0,2));delta=1.9e-7
    beyond=classify_points(bad,bad,np.array([[0,-2000-delta]]),empty,p,x0=0,y0=0,resolution=.5)
    at_limit=classify_points(bad,bad,np.array([[0,-2000]]),empty,p,x0=0,y0=0,resolution=.5)
    shifted_target=classify_points(bad,bad,np.array([[0,-2000]]),empty,p,x0=0,y0=0,resolution=.5,pixel_offset=(0,delta))
    assert beyond[0,0]==4 and at_limit[0,0]==1 and shifted_target[0,0]==4


def test_high_shore_and_preference():
    a = np.full((3, 8), np.nan); a[:, 0] = 2; a[:, 7] = 20
    # Distances to the two vertical shores: low=x, high=7-x.
    expected = np.tile([0, 1, 1, 1, 1, 4, 4, 0], (3, 1)).astype(np.uint8)
    p = profile(); p['max_shore_distance_m'] = 10
    assert np.array_equal(classify(a, p), expected)
    p['shore_preference_m'] = 0
    expected[:, 4] = 4
    assert np.array_equal(classify(a, p), expected)


def test_enclosed_void_and_empty_cell():
    a = np.ones((9, 12), np.float32); a[3:6, 4:8] = np.nan
    supplied = np.ones(a.shape, bool); supplied[3:6, 4:8] = False
    expected = np.zeros(a.shape, np.uint8); expected[3:6, 4:8] = 3
    assert np.array_equal(classify(a, supplied=supplied), expected)
    assert np.array_equal(classify(a, supplied=supplied, tiled=True), expected)


def test_diagonal_only_is_enclosed_under_four_connectivity():
    a = np.ones((5, 5), np.float32); a[0, 0] = a[1, 1] = a[2, 2] = np.nan
    expected = np.zeros(a.shape, np.uint8); expected[0, 0] = 1
    expected[1, 1] = expected[2, 2] = 3
    assert np.array_equal(classify(a), expected)


def test_cross_cell_component_and_empty_water():
    a = np.ones((9, 12), np.float32); a[:, 5:7] = np.nan
    supplied = np.ones(a.shape, bool); supplied[3:6, 5:7] = False
    expected = np.zeros(a.shape, np.uint8); expected[:, 5:7] = 1
    expected[3:6, 5:7] = 2
    assert np.array_equal(classify(a, supplied=supplied, tiled=True), expected)


def test_whole_empty_native_cell_open_water_hand_computed():
    a=np.ones((9,12),np.float32);a[:,4]=np.nan;a[3:6,4:8]=np.nan
    supplied=np.ones(a.shape,bool);supplied[3:6,4:8]=False
    expected=np.zeros(a.shape,np.uint8);expected[:,4]=1;expected[3:6,4:8]=2
    assert np.array_equal(classify(a,supplied=supplied,tiled=True),expected)


def test_exclusion_pixel_centres():
    a = np.full((3, 5), np.nan); a[:, 0] = 0
    p = profile(); p['exclusions'] = [dict(id='x',bounds=[1, 0, 2, 3],reason='fixture')]
    expected = np.tile([0,4,1,1,4], (3,1)).astype(np.uint8)
    assert np.array_equal(classify(a,p), expected)


@pytest.mark.parametrize('shape', [(1,1),(2,3),(3,4),(7,5),(13,19)])
def test_one_pass_equals_tiled(shape):
    rng=np.random.default_rng(42)
    a=rng.uniform(-1,20,(13,19)).astype(np.float32); a[rng.random(a.shape)<.65]=np.nan
    a[4:6,7:9]=-9999; a[0,2]=np.inf
    supplied=np.ones(a.shape,bool); supplied[3:6,4:8]=False; a[~supplied]=np.nan
    p=profile(); p['exclusions']=[dict(id='test',bounds=[3,4,8,8],reason='fixture')]
    assert np.array_equal(classify(a,p,supplied),classify(a,p,supplied,True,shape))


@pytest.mark.parametrize('preference',[0,50,100])
def test_certified_distance_blocks_equal_independent_EDT(preference):
    from shade_watch.fill.rule import classify_array
    rng=np.random.default_rng(4)
    a=np.full((300,600),np.nan,np.float32); a[:,0]=2; a[0,200:]=20
    a[120:140,200:230]=3; a[125:135,205:225]=np.nan
    p=load_json('config/sea_profiles/hk_cedd_2020.json'); p.update(max_shore_distance_m=120,shore_preference_m=preference)
    supplied=np.ones(a.shape,bool);supplied[200:,:]=False
    expected=classify_array(a,p,resolution=.5,supplied=supplied)
    tiled=classify_array(a,p,resolution=.5,supplied=supplied,cell_shape=(300,600))
    assert np.array_equal(expected,tiled)
