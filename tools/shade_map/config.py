"""Strict configuration and a hand-written validator for the documented schemas."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from src import v1
from tools import region_request as adapter

SCHEMAS = Path(__file__).resolve().parents[2] / 'config/schema'
HKT = timezone(timedelta(hours=8))
ROOT_MARKER = '.shade_map_root.json'


def city_clock(city):
    # F clock labels for Hong Kong have always used fixed UTC+8.
    return HKT if city['city_id'] == 'hong_kong' else ZoneInfo(city['timezone'])


class InvalidInput(ValueError):
    """A user input or publication ownership conflict (CLI exit 2)."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('utf-8')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput(f'{key}: duplicate JSON key')
        result[key] = value
    return result


def load_json(path):
    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=_pairs,
                          parse_constant=lambda x: float(x))
    except (OSError, ValueError) as exc:
        raise InvalidInput(f'{path}: {exc}') from exc


def validate_schema(value, schema, path='$', *, root=None):
    """Implement only the JSON Schema keywords used by this package, without deps.

    Tests walk each schema and reject every unsupported validation keyword.
    Numeric values must additionally be finite (strict JSON).
    """
    root = schema if root is None else root
    if '$ref' in schema:
        target = root
        for key in schema['$ref'].removeprefix('#/').split('/'):
            target = target[key]
        validate_schema(value, target, path, root=root)
    if 'oneOf' in schema:
        successes, reasons = 0, []
        for alternative in schema['oneOf']:
            try:
                validate_schema(value, alternative, path, root=root)
                successes += 1
            except InvalidInput as exc:
                reasons.append(str(exc))
        if successes != 1:
            raise InvalidInput(f'{path}: must match exactly one form; ' + '; '.join(reasons))
    types = {'object': lambda x: type(x) is dict, 'array': lambda x: type(x) is list,
             'string': lambda x: type(x) is str, 'integer': lambda x: type(x) is int,
             'number': lambda x: type(x) in (int, float) and math.isfinite(x),
             'boolean': lambda x: type(x) is bool, 'null': lambda x: x is None}
    if 'type' in schema:
        allowed = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(types[t](value) for t in allowed):
            raise InvalidInput(f'{path}: expected {schema["type"]} (numbers must be finite)')
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        raise InvalidInput(f'{path}: must equal {schema["const"]!r}')
    if 'enum' in schema and not any(type(value) is type(v) and value == v for v in schema['enum']):
        raise InvalidInput(f'{path}: must be one of {schema["enum"]}')
    if type(value) is dict:
        for key in schema.get('required', []):
            if key not in value:
                raise InvalidInput(f'{path}.{key}: required key missing')
        properties = schema.get('properties', {})
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f'{path}.{key}', root=root)
            elif schema.get('additionalProperties') is False:
                raise InvalidInput(f'{path}.{key}: unknown key')
            elif isinstance(schema.get('additionalProperties'), dict):
                validate_schema(item, schema['additionalProperties'], f'{path}.{key}', root=root)
    if type(value) is list:
        for keyword, compare in [('minItems', lambda n: len(value) >= n),
                                 ('maxItems', lambda n: len(value) <= n)]:
            if keyword in schema and not compare(schema[keyword]):
                raise InvalidInput(f'{path}: violates {keyword}={schema[keyword]}')
        if schema.get('uniqueItems') and len({canonical(v) for v in value}) != len(value):
            raise InvalidInput(f'{path}: duplicate entries')
        if 'items' in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema['items'], f'{path}[{index}]', root=root)
    if type(value) is str:
        if 'minLength' in schema and len(value) < schema['minLength']:
            raise InvalidInput(f'{path}: string is too short')
        if 'maxLength' in schema and len(value) > schema['maxLength']:
            raise InvalidInput(f'{path}: string is too long')
        if 'pattern' in schema and re.fullmatch(schema['pattern'], value) is None:
            raise InvalidInput(f'{path}: must match {schema["pattern"]}')
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise InvalidInput(f'{path}: must be finite')
        for keyword, compare in [('minimum', lambda n: value >= n), ('maximum', lambda n: value <= n)]:
            if keyword in schema and not compare(schema[keyword]):
                raise InvalidInput(f'{path}: violates {keyword}={schema[keyword]}')


def check_document(value, name):
    validate_schema(value, load_json(SCHEMAS / f'shade_map_{name}.schema.json'))
    return value


def _defaults(value, schema_name):
    schema = load_json(SCHEMAS / f'shade_map_{schema_name}.schema.json')
    value = deepcopy(value)
    validate_schema(value, schema)
    for key, rule in schema['properties'].items():
        if key not in value and 'default' in rule:
            value[key] = deepcopy(rule['default'])
    return value


def machine_config(value='config/machine.local.json', *, require_dsm=True):
    value = _defaults(load_json(value) if isinstance(value, (str, Path)) else value, 'machine')
    for key in ('dsm_dir', 'output_root'):
        value[key] = str((v1.ROOT / value[key]).resolve())
    if require_dsm:
        if not Path(value['dsm_dir']).is_dir():
            raise InvalidInput('dsm_dir: catalogue directory does not exist')
        validate_output_root(value)
    for name in value.get('cities', {}):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', name):
            raise InvalidInput(f'cities: invalid city identifier {name!r}')
    namespace = value['cache_namespace']
    try:
        v1._owned_path(v1.ROOT/'data/processed/shade_v1'/namespace,
                       'data/processed/shade_v1', 'data/processed/shade_v1/shade_map_raw')
    except ValueError as exc:
        raise InvalidInput(f'cache_namespace: {exc}') from exc
    return value


def validate_output_root(machine, source_directories=()):
    """Check resolved write boundaries before the adapter can create a view."""
    root = Path(machine['output_root']).resolve()
    if root.is_relative_to((v1.ROOT / 'data').resolve()):
        raise InvalidInput('output_root: must not lie inside data/')
    catalogues = {Path(machine['dsm_dir']).resolve(),
                  *(Path(p).resolve() for p in source_directories)}
    sources = {*catalogues, (v1.ROOT/'outputs/region_views').resolve()}
    for catalogue in catalogues:
        # A provider catalogue can be a view of files in other source directories.
        sources.update(p.resolve().parent for p in catalogue.iterdir() if p.is_file())
    if any(root.is_relative_to(source) for source in sources):
        raise InvalidInput('output_root: must not equal or lie inside a DSM/source directory')
    containers = {v1.ROOT.resolve(), (v1.ROOT/'outputs').resolve()}
    ancestor = root.parent
    while ancestor not in containers:
        if ancestor.exists():
            marker = ancestor/ROOT_MARKER
            try:
                owned = (not marker.is_symlink() and marker.is_file()
                         and load_json(marker) == {'schema': 'shade-map-root-1.0'})
            except InvalidInput:
                owned = False
            if owned:
                break
            raise InvalidInput('output_root: lies inside an existing folder F did not create')
        ancestor = ancestor.parent


def corners(value, *, project=True):
    ll, ur = value['lower_left'], value['upper_right']
    if value['crs'] == 'wgs84':
        for key in ('lower_left', 'upper_right'):
            lat, lon = value[key]
            if not -90 <= lat <= 90:
                raise InvalidInput(f'{key}: latitude must be in [-90, 90]')
            if not -180 <= lon <= 180:
                raise InvalidInput(f'{key}: longitude must be in [-180, 180]')
        labels = ('latitude', 'longitude')
    else:
        labels = ('easting', 'northing')
    for index, label in enumerate(labels):
        if not ll[index] < ur[index]:
            raise InvalidInput(f'lower_left.{label} must be less than upper_right.{label}')
    if not project:
        return
    try:
        a, b = adapter.project_corner(ll, value['crs']), adapter.project_corner(ur, value['crs'])
    except ValueError as exc:
        raise InvalidInput(f'corners: {exc}') from exc
    if not a[0] < b[0] or not a[1] < b[1]:
        raise InvalidInput('corners: projected EPSG:2326 easting and northing must keep lower-left order')


def _day(value, key):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidInput(f'{key}: invalid calendar date {value}') from exc


def dates(value):
    if isinstance(value, dict):
        first, last = _day(value['from'], 'time.dates.from'), _day(value['to'], 'time.dates.to')
        count = (last-first).days + 1
        if not 1 <= count <= 366:
            raise InvalidInput('time.dates: range must be ordered and contain 1..366 dates')
        value = [(first + timedelta(days=i)).isoformat() for i in range(count)]
    for index, day in enumerate(value):
        _day(day, f'time.dates[{index}]')
    return value


def region_config(value, *, project_legacy=True):
    value = _defaults(load_json(value) if isinstance(value, (str, Path)) else value, 'region')
    legacy = value['schema'] == 'shade-map-region-1.0'
    if legacy and ('city' in value or value['crs'] == 'projected'):
        raise InvalidInput('city and projected corners require shade-map-region-1.1')
    value.setdefault('dsm_source', 'raw' if legacy else 'sea-2.2')
    corners(value, project=legacy and project_legacy)
    value['lower_left'] = [float(v) for v in value['lower_left']]
    value['upper_right'] = [float(v) for v in value['upper_right']]
    time = value['time']
    if time['mode'] in ('daylight', 'window'):
        time['dates'] = dates(time['dates'])
        time.setdefault('interval_minutes', 10)
        if time['mode'] == 'window' and time['end'] < time['start']:
            raise InvalidInput('time.end: must not be earlier than time.start')
    elif legacy:
        if any(len(text) != 16 and not text.endswith('+08:00') for text in time['instants']):
            raise InvalidInput('time.instants: shade-map-region-1.0 accepts only the +08:00 offset')
        time['instants'] = normalize_instants(time['instants'], HKT)
    return value


def _local_instant(text, clock):
    value = datetime.fromisoformat(text)
    if clock is HKT:
        local = value.astimezone(clock) if value.tzinfo else value.replace(tzinfo=clock)
    else:
        local = datetime.fromisoformat(v1.normalize_instant(value, clock.key).local)
    if value.tzinfo is not None and value.utcoffset() != local.utcoffset():
        raise ValueError('explicit UTC offset disagrees with the city time zone')
    return local


def normalize_instants(instants, clock):
    normalized = []
    for index, text in enumerate(instants):
        label = f'time.instants[{index}]'
        _day(text[:10], label)
        try:
            normalized.append(_local_instant(text, clock).isoformat(timespec='minutes'))
        except ValueError as exc:
            raise InvalidInput(f'{label}: {exc}') from exc
    if len({text[:16] for text in normalized}) != len(normalized):
        raise InvalidInput('time.instants: duplicate physical instant or local frame folder')
    return normalized


def expanded_time(time, *, clock=HKT, daylight_reference=v1.DAYLIGHT_REFERENCE):
    """Daylight stays dates; the engine alone expands its daylight samples."""
    if time['mode'] == 'daylight':
        return dict(dates=time['dates'], interval_minutes=time['interval_minutes']), []
    if time['mode'] == 'instants':
        requested = time['instants']
    else:
        requested = []
        for day in time['dates']:
            start = datetime.fromisoformat(f'{day}T{time["start"]}')
            end = datetime.fromisoformat(f'{day}T{time["end"]}')
            while start <= end:
                requested.append(start.isoformat())
                start += timedelta(minutes=time['interval_minutes'])
    bounds, kept, dropped = {}, [], []
    for text in requested:
        try:
            local = _local_instant(text, clock)
        except ValueError as exc:
            raise InvalidInput(f'time: {text}: {exc}') from exc
        utc = local.astimezone(v1.UTC)
        day = local.date()
        if day not in bounds:
            bounds[day] = v1.daylight_bounds(day, *daylight_reference, v1.HKT if clock is HKT else clock)
        rise, setting = bounds[day]
        if rise.astimezone(v1.UTC) <= utc <= setting.astimezone(v1.UTC):
            kept.append(local.isoformat())
        else:
            dropped.append(dict(local_time=local.isoformat(), utc_time=utc.isoformat(), reason='outside daylight'))
    return dict(instants=kept, interval_minutes=time.get('interval_minutes', 10)), dropped
