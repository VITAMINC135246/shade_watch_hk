import numpy as np
import pytest
from src.horizon import pixel_centred_horizon
from tools.sea2.checks import independent_rays, reference_labels


@pytest.mark.parametrize('azimuth',[0,45,90,125,180,270,315])
def test_independent_reference_respects_documented_ray_geometry(azimuth):
    rng=np.random.default_rng(7); dsm=rng.uniform(-1,30,(40,43)).astype(np.float32)
    dsm[20:22,23:25]=np.nan
    rows=np.array([18,19,20,21,22],np.int32);cols=np.array([19,20,21,22,23],np.int32)
    expected,support,_=pixel_centred_horizon(dsm,rows,cols,float(azimuth),4,4,.5,-101,203)
    h,s=independent_rays(dsm,rows,cols,azimuth,origin_row=-101,origin_col=203,max_distance=4)
    assert np.array_equal(h,expected,equal_nan=True); assert np.array_equal(s,support)


def test_reference_classifier_strict_equality_and_uncertainty():
    h=np.array([10,11,0,np.nan],np.float32);support=np.array([True,False,False,False])
    labels,q=reference_labels(h,support,10,9)
    assert labels.tolist()==[0,1,255,255] and q.tolist()==[0,0,2,1]
