"""F1.0: config-driven shade maps using the unchanged V1/V2 engine."""
from .planning import prepare
from .runner import prune_region, run_region

__all__ = ['shade_map','plan_shade_map','run_region','prune_region']


def _region(lower_left, upper_right, when, *, name, crs, dsm_source, full_image):
    return dict(schema='shade-map-region-1.0',name=name,crs=crs,
                lower_left=list(lower_left) if isinstance(lower_left,(tuple,list)) else lower_left,
                upper_right=list(upper_right) if isinstance(upper_right,(tuple,list)) else upper_right,
                time=dict(mode='daylight',dates=[when]) if isinstance(when,str) else when,
                dsm_source=dsm_source,full_image=full_image)


def plan_shade_map(lower_left, upper_right, when, *, name, crs='wgs84',
                   machine='config/machine.local.json', dsm_source='raw', full_image='auto'):
    return prepare(_region(lower_left,upper_right,when,name=name,crs=crs,
                           dsm_source=dsm_source,full_image=full_image),machine).document


def shade_map(lower_left, upper_right, when, *, name, crs='wgs84',
              machine='config/machine.local.json', dsm_source='raw', full_image='auto'):
    return run_region(_region(lower_left,upper_right,when,name=name,crs=crs,
                              dsm_source=dsm_source,full_image=full_image),machine)
