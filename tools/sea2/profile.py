"""Strict, finite sea profiles; no dataset-specific geometry inputs."""
from copy import deepcopy
from pathlib import Path

import numpy as np

from tools.shade_map.config import InvalidInput, load_json, validate_schema

CODE_ROOT = Path(__file__).resolve().parents[2]


def validate_profile(value):
    value = deepcopy(value)
    validate_schema(value, load_json(CODE_ROOT/'config/schema/sea_profile.schema.json'))
    if not np.isfinite(np.float32(value['h_sea_m'])):
        raise InvalidInput('h_sea_m: must be representable as finite float32')
    ids = set()
    for zone in value['exclusions']:
        if zone['id'] in ids:
            raise InvalidInput('exclusions: duplicate id')
        ids.add(zone['id'])
        l, b, r, t = zone['bounds']
        if not l < r or not b < t:
            raise InvalidInput('exclusions.bounds: must be ordered rectangles')
    return value


def load_profile(machine):
    name = machine.get('sea_profile', 'hk_cedd_2020')
    if not isinstance(name, str) or not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in name):
        raise InvalidInput('sea_profile: invalid profile identifier')
    path = CODE_ROOT/'config/sea_profiles'/f'{name}.json'
    value = validate_profile(load_json(path))
    if value['profile_id'] != name:
        raise InvalidInput('sea_profile: profile_id does not match filename')
    return value
