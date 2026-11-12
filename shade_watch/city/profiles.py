"""Portable profile checks and resolution of the current ingested catalogue."""
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pyproj
from pyproj.exceptions import CRSError

from shade_watch.engine import v1
from shade_watch.publish.common import identity
from shade_watch.publish.config import InvalidInput, check_document, load_json
from shade_watch.fill.profile import load_profile

CITY_DIR = Path(__file__).resolve().parents[2] / "config/cities"
HK = "hong_kong"
POINTER_SCHEMA = "shade-map-city-current-1.0"
MANIFEST_SCHEMA = "shade-map-ingestion-1.0"


def city_ids():
    return sorted(p.stem for p in CITY_DIR.glob("*.json") if not p.name.startswith("."))


def load_city(city_id):
    if not isinstance(city_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", city_id):
        raise InvalidInput(f"city: invalid identifier {city_id!r}")
    path = CITY_DIR / (city_id + ".json")
    if not path.is_file():
        raise InvalidInput(f"city: unknown city {city_id!r}")
    value = check_document(load_json(path), "city")
    if value["city_id"] != city_id:
        raise InvalidInput("city: profile city_id must match its filename")
    pyproj.network.set_network_enabled(False)
    try:
        crs = pyproj.CRS(value["crs"])
        ZoneInfo(value["timezone"])
    except (CRSError, ZoneInfoNotFoundError, ValueError) as exc:
        raise InvalidInput(f"city: {city_id} has an invalid CRS or time zone") from exc
    if not crs.is_projected or any(axis.unit_conversion_factor != 1 for axis in crs.axis_info):
        raise InvalidInput("city.crs: a projected metre CRS is required")
    left, bottom, right, top = value["extent"]
    if not left < right or not bottom < top:
        raise InvalidInput("city.extent: expected an ordered rectangle")
    lat, lon = value["daylight_reference"]
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise InvalidInput("city.daylight_reference: expected WGS84 latitude and longitude")
    ingest = value["ingest"]
    if (ingest is None) != (city_id == HK):
        raise InvalidInput("city.ingest: a sheet specification is required for each ingested city")
    if ingest is not None:
        if value["sea_profile"] == "hk_cedd_2020":
            raise InvalidInput("city.sea_profile: Hong Kong's view is reserved for Hong Kong")
        if math.prod(ingest["cell_pixels"]) > v1.MAX_TILE_PIXELS:
            raise InvalidInput("city.ingest.cell_pixels: cell exceeds V1 native tile limit")
        names = [s["name"].casefold() for s in ingest["sheets"]]
        if len(names) != len(set(names)):
            raise InvalidInput("city.ingest.sheets: duplicate sheet name")
    return value


def city_record(city, ingest_id=None):
    result = {key: city[key] for key in ("city_id", "crs", "timezone", "daylight_reference", "vertical_datum")}
    result["profile_sha256"] = identity(city)
    if ingest_id is not None:
        result["ingest_id"] = ingest_id
    return result


def fill_profile(city, machine):
    profile = load_profile(machine)
    if profile["h_sea_m"] != 0 or math.copysign(1, profile["h_sea_m"]) < 0:
        raise InvalidInput("h_sea_m: registered cities require 0.00 m fill")
    if profile["vertical_datum"] != city["vertical_datum"]:
        raise InvalidInput("sea_profile: vertical datum differs from the city")
    return profile


def catalogue_root(city):
    root = v1.ROOT / "data/derived/catalogues" / city["city_id"]
    if root.resolve() != root:
        raise InvalidInput("city catalogue: output namespace cannot use symlinks")
    return root


def machine_for_city(machine, city, dsm_source):
    """Return a provider-compatible machine dictionary and its ingestion ID."""
    machine = dict(machine, cache_namespace=machine["cache_namespace"] + "_" + city["city_id"])
    if city["city_id"] == HK:
        return machine, None
    root = catalogue_root(city)
    pointer = root / "current.json"
    if not pointer.exists() and dsm_source == "sea-2.2":
        from shade_watch.fill.provider import MISSING
        raise InvalidInput(MISSING)
    doc = load_json(pointer)
    ingest_id = doc.get("ingest_id", "") if isinstance(doc, dict) else ""
    if (pointer.is_symlink() or not isinstance(ingest_id, str)
            or not re.fullmatch(r"[0-9a-f]{64}", ingest_id)
            or doc.get("schema") != POINTER_SCHEMA or doc.get("city_id") != city["city_id"]):
        raise InvalidInput("city catalogue: invalid current ingestion pointer")
    folder = root / ingest_id
    path, tiles = folder / "manifest.json", folder / "tiles"
    if folder.is_symlink() or tiles.is_symlink() or path.is_symlink() or not tiles.is_dir():
        raise InvalidInput("city catalogue: invalid ingestion directory")
    manifest = load_json(path)
    if (not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA
            or manifest.get("ingest_id") != ingest_id
            or identity({k: v for k, v in manifest.items() if k != "ingest_id"}) != ingest_id
            or manifest.get("profile") != city or manifest.get("profile_sha256") != identity(city)):
        raise InvalidInput("city catalogue: ingestion manifest differs from the city profile")
    expected = {item["name"] for item in manifest["cells"]}
    actual = {p.name for p in tiles.iterdir() if p.is_file() and not p.is_symlink()}
    if actual != expected or len(list(tiles.iterdir())) != len(expected):
        raise InvalidInput("city catalogue: tile inventory differs from the ingestion manifest")
    return dict(machine, dsm_dir=str(tiles), sea_profile=city["sea_profile"]), ingest_id
