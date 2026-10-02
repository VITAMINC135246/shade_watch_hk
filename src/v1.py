"""V1 arbitrary-instant API and CLI. Example: python -m src.v1 plan --at ..."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone as datetime_timezone
import json
import math
import os
from pathlib import Path
import shutil
import time
from zoneinfo import ZoneInfo

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import Window

from .pipeline import (EXTERNAL_PIDS, fingerprint, include_auxiliary_source_identities,
                       memory_monitor, profile, track_media_process)
from .shade_watch import ROOT, RAW, SOURCE_LINE, _font, classify, load_study_area
from .solar import HKT, daylight_bounds, daylight_samples, position
from .spatial import Grid, cores, digest_file, intersects, inventory, native_mosaic_grid, output_reference, target_grid
from .v1_cache import (POLICY, atomic_json, ensure_directions, entry_paths, exclusive_lock,
                       source_identity, spatial_identity, tile_grid, valid_entry)

UTC = datetime_timezone.utc
DAYLIGHT_REFERENCE = (22.3, 114.2)
MAX_FRAMES = 512
MAX_OUTPUT_PIXELS = 20_000_000
MAX_TILE_PIXELS = 2_000_000
ARTIFACT_BUDGET = 10 * 1024**3
DIRECTION_METHODS = {"nearest5": 5., "nearest2_5": 2.5, "direct": None}
QUALITY = {"0": "valid", "1": "missing target DSM", "2": "incomplete 1 km sunward support",
           "3": "distant-obstruction sensitivity", "4": "nonpositive apparent solar-centre elevation"}


@dataclass(frozen=True)
class Instant:
    requested: str
    utc: str
    local: str


@dataclass(frozen=True)
class ShadeRequest:
    instants: tuple[Instant, ...]
    dates: tuple[str, ...]
    mode: str
    selector: tuple[float, float] | None
    requested_bounds: tuple[float, ...]
    crop: tuple[int, ...] | None
    interval_minutes: int
    local_timezone: str
    direction_method: str
    jpg: bool
    mp4: bool
    workers: int
    memory_budget_mb: int


@dataclass(frozen=True)
class TilePlan:
    source: dict
    spatial_key: str
    dependency_identities: tuple[dict, ...]
    reference: dict
    solar: tuple[dict, ...]
    directions: tuple[float, ...]
    missing_directions: tuple[float, ...]
    buffered_coverage_fraction: float


@dataclass(frozen=True)
class ShadePlan:
    schema: str
    request: ShadeRequest
    grid: Grid
    tiles: tuple[TilePlan, ...]
    source_directory: str
    output_directory: str
    cache_directory: str
    coverage: dict
    resources: dict
    planning_seconds: float
    key: str

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ShadeResult:
    index_path: str
    frames: tuple[dict, ...]
    jobs: dict
    performance: dict


def normalize_instant(value, local_timezone="Asia/Hong_Kong"):
    requested = value.isoformat() if isinstance(value, datetime) else str(value)
    if not isinstance(value, datetime) and "T" not in requested and " " not in requested:
        raise ValueError("An instant requires a date and time; use dates for daylight sequences")
    instant = value if isinstance(value, datetime) else datetime.fromisoformat(requested)
    zone = ZoneInfo(local_timezone)
    if instant.tzinfo is None:
        candidates = [instant.replace(tzinfo=zone, fold=i) for i in (0, 1)]
        valid = [t for t in candidates if t.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == instant]
        if not valid or (len(valid) == 2 and valid[0].utcoffset() != valid[1].utcoffset()):
            raise ValueError("Ambiguous or nonexistent local timestamp; supply an explicit UTC offset")
        instant = valid[0]
    if instant.utcoffset() is None:
        raise ValueError("Timestamp has no usable UTC offset")
    return Instant(requested, instant.astimezone(UTC).isoformat(), instant.astimezone(HKT).isoformat())


def direction_for(azimuth, method):
    step = DIRECTION_METHODS[method]
    return float(azimuth % 360) if step is None else (math.floor((azimuth % 360 + step / 2) / step) * step) % 360


def index_sources(directory):
    records = include_auxiliary_source_identities(inventory(Path(directory).glob("*.tif")))
    for record in records:
        if record["crs"] != "EPSG:2326" or record["transform"][0] != .5:
            raise ValueError("V1 requires native 0.5 m EPSG:2326 DSM")
        if record["width"] * record["height"] > MAX_TILE_PIXELS:
            raise ValueError("Native tile exceeds V1 bounded memory profile")
        for address in (record["transform"][2] / .5, -record["transform"][5] / .5):
            if not math.isclose(address, round(address), abs_tol=1e-7):
                raise ValueError("Source grid is not on the canonical projected-origin lattice")
    return records


def _owned_path(value, parent, default):
    path = (ROOT / (value or default)).resolve()
    parent = (ROOT / parent).resolve()
    if not path.is_relative_to(parent) or path == parent:
        raise ValueError(f"Choose an isolated V1 directory under {parent}")
    return path


def _custom_grid(records, bounds):
    left, bottom, right, top = bounds
    if not all(math.isfinite(v) for v in bounds) or not left < right or not bottom < top:
        raise ValueError("Bounds must be finite [left,bottom,right,top] with positive area")
    res = .5
    # Snap values already on the lattice before floor/ceil to absorb projection roundoff.
    def cell(v):
        q = v / res
        return round(q) if abs(q - round(q)) < 1e-7 else q
    l, b, r, t = math.floor(cell(left)), math.floor(cell(bottom)), math.ceil(cell(right)), math.ceil(cell(top))
    return Grid(r - l, t - b, tuple(from_origin(l * res, t * res, res, res))[:6], records[0]["crs"], "custom")


def _plan_key(request, grid, tiles):
    return fingerprint(dict(policy=POLICY, request=asdict(request), grid=asdict(grid),
                            spatial_keys=[t.spatial_key for t in tiles], solar=[t.solar for t in tiles],
                            classification_code=digest_file(Path(__file__).with_name("shade_watch.py")),
                            solar_code=digest_file(Path(__file__).with_name("solar.py")),
                            execution_code=digest_file(Path(__file__))))


def plan_shade(*, instants=None, dates=None, interval_minutes=10,
               local_timezone="Asia/Hong_Kong", tile=None, tiles=None,
               latitude=None, longitude=None, mode="native", bounds=None,
               width_m=None, height_m=None, crop=None, direction_method="nearest5",
               jpg=False, mp4=False, workers=1, memory_budget_mb=8192,
               output_dir=None, cache_dir=None, dsm_dir=None, _records=None):
    """Inspect inputs/cache without horizon calls or scientific/media writes.

    Locations are WGS84; custom bounds are EPSG:2326. Output/cache paths are
    isolated project directories. See docs/v1/GUIDE.md for copyable examples.
    """
    started = time.perf_counter()
    if (instants is None) == (dates is None):
        raise ValueError("Supply exactly one of instants or dates")
    if type(interval_minutes) is not int or interval_minutes <= 0:
        raise ValueError("interval_minutes must be a positive integer")
    if workers != 1 or type(workers) is not int:
        raise ValueError("V1 supports one worker within the shared two-worker ceiling")
    if type(memory_budget_mb) is not int or not 512 <= memory_budget_mb <= 8192:
        raise ValueError("memory_budget_mb must be an integer from 512 to 8192")
    if direction_method not in DIRECTION_METHODS:
        raise ValueError(f"Unknown direction method: {direction_method}")
    if type(jpg) is not bool or type(mp4) is not bool:
        raise ValueError("Media switches must be booleans")
    if mode not in ("native", "custom"):
        raise ValueError("mode must be native or custom")
    if (latitude is None) != (longitude is None):
        raise ValueError("Provide latitude and longitude together")
    selector = None
    if latitude is not None:
        if not (math.isfinite(latitude) and math.isfinite(longitude)
                and -90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Selector must contain finite WGS84 coordinates")
        selector = (float(latitude), float(longitude))
    if tile is not None and tiles is not None:
        raise ValueError("Use tile or tiles, not both")
    names = [tile] if tile is not None else list(tiles) if tiles is not None else None
    if names is not None and selector is not None:
        raise ValueError("Use tile names or a coordinate selector, not both")
    if mode == "native" and any(v is not None for v in (bounds, width_m, height_m)):
        raise ValueError("Custom bounds/dimensions require mode=custom")
    if mode == "custom" and names is not None:
        raise ValueError("Tile-name selection requires native mode")
    source_directory = Path(dsm_dir or RAW).resolve()
    # V2 supplies one request-local, freshly indexed catalogue for batch planning.
    # V1 execution still independently rehashes the actual input dependencies.
    records = index_sources(source_directory) if _records is None else _records
    if mode == "native":
        if names is not None:
            grid = native_mosaic_grid(records, names)
            if len(names) == 1:
                grid = Grid(grid.width, grid.height, grid.transform, grid.crs, "native_tile",
                            grid.selected_source, grid.selected_sources)
        else:
            if selector is None:
                study = load_study_area()
                selector = (study["latitude"], study["longitude"])
            grid = target_grid(records, dict(latitude=selector[0], longitude=selector[1]))
        requested_bounds = grid.bounds()
    else:
        if bounds is not None:
            if selector is not None or width_m is not None or height_m is not None:
                raise ValueError("Use custom bounds or centre/dimensions, not both")
            if len(bounds) != 4:
                raise ValueError("Expected four custom bounds")
            requested_bounds = tuple(float(v) for v in bounds)
        else:
            if selector is None or width_m is None or height_m is None:
                raise ValueError("Custom mode needs bounds or explicit centre plus width/height")
            if not all(math.isfinite(v) and v > 0 for v in (width_m, height_m)):
                raise ValueError("Custom dimensions must be finite and positive")
            x, y = Transformer.from_crs("EPSG:4326", "EPSG:2326", always_xy=True).transform(selector[1], selector[0])
            requested_bounds = (x - width_m / 2, y - height_m / 2, x + width_m / 2, y + height_m / 2)
        grid = _custom_grid(records, requested_bounds)
    if crop is not None:
        if len(crop) != 4 or any(type(v) is not int for v in crop):
            raise ValueError("crop is an integer [column,row,width,height] window")
        c, r, w, h = crop
        if c < 0 or r < 0 or min(w, h) <= 0 or c + w > grid.width or r + h > grid.height:
            raise ValueError("crop must fit the resolved extent")
        grid = Grid(w, h, tuple(grid.local_transform(crop))[:6], grid.crs, grid.mode,
                    grid.selected_source, grid.selected_sources)
    if grid.width * grid.height > MAX_OUTPUT_PIXELS:
        raise ValueError("Output exceeds V1 local-area profile")
    owners = [r for r in records if intersects(grid.bounds(), r["bounds"])]
    if not owners:
        raise ValueError("Requested area has no available native DSM tiles")
    owners.sort(key=lambda r: (-r["bounds"][3], r["bounds"][0]))
    date_strings = ()
    if instants is not None:
        if isinstance(instants, (str, datetime)):
            instants = [instants]
        times = tuple(normalize_instant(t, local_timezone) for t in instants)
    else:
        if local_timezone != "Asia/Hong_Kong":
            raise ValueError("Daylight dates are Hong Kong calendar days; use explicit instants for other zones")
        if isinstance(dates, (str, date)):
            dates = [dates]
        days = [date.fromisoformat(str(d)) for d in dates]
        if len(set(days)) != len(days):
            raise ValueError("Duplicate daylight date")
        if not days or len(days) > MAX_FRAMES:
            raise ValueError("Daylight dates exceed V1 request limits")
        date_strings = tuple(d.isoformat() for d in days)
        samples = []
        for day in days:
            sunrise, sunset = daylight_bounds(day, *DAYLIGHT_REFERENCE)
            samples.extend(daylight_samples(sunrise, sunset, interval_minutes))
            if len(samples) > MAX_FRAMES:
                raise ValueError("Daylight sequence exceeds 512-frame V1 limit")
        times = tuple(normalize_instant(t) for t in samples)
    if not times or len(times) > MAX_FRAMES:
        raise ValueError("Request needs 1..512 instants")
    if len({t.utc for t in times}) != len(times):
        raise ValueError("Duplicate physical instant")
    out = _owned_path(output_dir, "outputs", "outputs/v1_query")
    cache = _owned_path(cache_dir, "data/processed/shade_v1", "data/processed/shade_v1/default")
    request = ShadeRequest(times, date_strings, mode, selector, tuple(requested_bounds),
                           tuple(crop) if crop is not None else None, interval_minutes,
                           local_timezone, direction_method, jpg, mp4, workers, memory_budget_mb)
    tile_plans = []
    for owner in owners:
        key, identity, dependencies = spatial_identity(records, owner)
        reference = output_reference(tile_grid(owner))
        reference.update(policy="canonical_native_tile_geometric_center", role="fixed reference for owning pixels")
        solar = []
        for instant in times:
            sun = position(datetime.fromisoformat(instant.utc), reference["latitude"], reference["longitude"])
            solar.append(asdict(sun) | dict(direction_deg=direction_for(sun.azimuth_deg, direction_method)))
        directions = tuple(sorted({s["direction_deg"] for s in solar if s["apparent_elevation_deg"] > 0}))
        missing = tuple(d for d in directions if valid_entry(cache, key, d, owner) is None)
        buffer_area = (owner["width"] * .5 + 2000) * (owner["height"] * .5 + 2000)
        halo_bounds = (owner["bounds"][0] - 1000, owner["bounds"][1] - 1000,
                       owner["bounds"][2] + 1000, owner["bounds"][3] + 1000)
        footprint_area = sum((min(halo_bounds[2], d["bounds"][2]) - max(halo_bounds[0], d["bounds"][0])) *
                             (min(halo_bounds[3], d["bounds"][3]) - max(halo_bounds[1], d["bounds"][1])) for d in dependencies)
        tile_plans.append(TilePlan(owner, key, tuple(identity["sources"]), reference,
                                   tuple(solar), directions, missing, footprint_area / buffer_area))
    tile_plans = tuple(tile_plans)
    output_area = grid.width * grid.height
    footprint_pixels = sum(round((min(grid.bounds()[2], r["bounds"][2]) - max(grid.bounds()[0], r["bounds"][0])) / .5) *
                           round((min(grid.bounds()[3], r["bounds"][3]) - max(grid.bounds()[1], r["bounds"][1])) / .5) for r in owners)
    estimate = max(400 * 1024**2 + 8 * (r["width"] + 4000) * (r["height"] + 4000)
                   + 64 * r["width"] * r["height"] for r in owners)
    # Uncompressed upper estimate plus per-entry metadata and bounded media allowance.
    disk_estimate = output_area * len(times) * 2 + sum(
        t.source["width"] * t.source["height"] * 12 * len(t.missing_directions) for t in tile_plans)
    disk_estimate += (len(times) * 4 * 1024**2 if jpg else 0) + (len(times) * 4 * 1024**2 if mp4 else 0) + 16 * 1024**2
    if estimate > memory_budget_mb * 1024**2:
        raise ValueError("Estimated V1 native-tile allocation exceeds memory budget")
    if disk_estimate > ARTIFACT_BUDGET:
        raise ValueError("Request exceeds the 10 GiB artifact profile; reduce dates/area/directions")
    resources = dict(workers=workers, estimated_peak_bytes=estimate, memory_budget_bytes=memory_budget_mb * 1024**2,
                     estimated_new_bytes=disk_estimate, artifact_budget_bytes=ARTIFACT_BUDGET,
                     expected_direction_jobs=sum(len(t.directions) for t in tile_plans),
                     missing_direction_jobs=sum(len(t.missing_directions) for t in tile_plans), frames=len(times))
    coverage = dict(output_pixels=output_area, source_footprint_pixels=footprint_pixels,
                    uncovered_pixels=output_area - footprint_pixels,
                    limitations=["Footprints do not establish valid DSM or complete sunward support",
                                 "1 km cutoff does not bound unseen farther terrain",
                                 "Solar model and tile references are approximations"],
                    daylight_reference=dict(latitude=DAYLIGHT_REFERENCE[0], longitude=DAYLIGHT_REFERENCE[1]))
    return ShadePlan("shade-watch-v1-plan-1.0", request, grid, tile_plans, str(source_directory),
                     str(out), str(cache), coverage, resources, time.perf_counter() - started,
                     _plan_key(request, grid, tile_plans))


def _frame_paths(out, instant):
    stamp = datetime.fromisoformat(instant.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return out / "shade" / f"shade_{stamp}.tif", out / "quality" / f"quality_{stamp}.tif", out / "status" / f"{stamp}.json"


def _frame_key(plan, index):
    return fingerprint(dict(plan=plan.key, instant=plan.request.instants[index].utc))


def _valid_frame(plan, index):
    paths = _frame_paths(Path(plan.output_directory), plan.request.instants[index])
    try:
        meta = json.loads(paths[2].read_text())
        if not isinstance(meta, dict) or meta.get("integrity_sha256") != fingerprint({
                k: v for k, v in meta.items() if k != "integrity_sha256"}):
            return None
        if meta["status"] != "complete" or meta["key"] != _frame_key(plan, index):
            return None
        for path, nodata in zip(paths[:2], (255, None)):
            if digest_file(path) != meta["hashes"][path.name]:
                return None
            with rasterio.open(path) as ds:
                if (ds.count != 1 or ds.dtypes != ("uint8",) or ds.nodata != nodata
                        or ds.shape != (plan.grid.height, plan.grid.width)
                        or ds.crs.to_string() != plan.grid.crs or ds.transform != plan.grid.affine
                        or ds.tags().get("policy") != POLICY):
                    return None
        return meta
    except (OSError, ValueError, KeyError, TypeError, rasterio.errors.RasterioError):
        return None


def _compose_frame(plan, index, thresholds):
    compose_start = time.perf_counter()
    classification_seconds = 0.
    instant = plan.request.instants[index]
    out = Path(plan.output_directory)
    shade_path, quality_path, status = _frame_paths(out, instant)
    for path in (shade_path, quality_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    temps = [p.with_name(p.name + f".{os.getpid()}.tmp") for p in (shade_path, quality_path)]
    atomic_json(status, dict(status="running", key=_frame_key(plan, index)))
    grid = plan.grid
    solar_by_tile = []
    equality_count = finite_count = 0
    with rasterio.open(temps[0], "w", **profile(grid, (0, 0, grid.width, grid.height))) as dst, \
            rasterio.open(temps[1], "w", **profile(grid, (0, 0, grid.width, grid.height), nodata=None)) as qdst:
        for core in cores(grid, 512):
            dst.write(np.full((core[3], core[2]), 255, np.uint8), 1, window=Window(*core))
            qdst.write(np.ones((core[3], core[2]), np.uint8), 1, window=Window(*core))
        for tile in plan.tiles:
            native = tile_grid(tile.source)
            l, b, r, t = grid.bounds()
            nl, nb, nr, nt = native.bounds()
            left, bottom, right, top = max(l, nl), max(b, nb), min(r, nr), min(t, nt)
            w, h = round((right - left) / .5), round((top - bottom) / .5)
            source_window = Window(round((left - nl) / .5), round((nt - top) / .5), w, h)
            dest_window = Window(round((left - l) / .5), round((t - top) / .5), w, h)
            solar = tile.solar[index]
            threshold = thresholds.get(tile.spatial_key, 0.)
            if solar["apparent_elevation_deg"] <= 0:
                from .spatial import read_window
                surface = read_window([tile.source], native, (int(source_window.col_off), int(source_window.row_off), w, h))
                classify_start = time.perf_counter()
                labels = np.full((h, w), 255, np.uint8)
                flags = np.where(np.isfinite(surface), 4, 1).astype(np.uint8)
                classification_seconds += time.perf_counter() - classify_start
                del surface
            else:
                path, _ = entry_paths(plan.cache_directory, tile.spatial_key, solar["direction_deg"])
                with rasterio.open(path) as ds:
                    horizon, support = ds.read([1, 2], window=source_window)
                finite = np.isfinite(horizon)
                finite_count += int(finite.sum())
                equality_count += int(np.count_nonzero(finite & (np.abs(horizon - solar["apparent_elevation_deg"]) <= 1e-4)))
                classify_start = time.perf_counter()
                labels, flags = classify(horizon, support.astype(bool), finite,
                                         solar["apparent_elevation_deg"], threshold)
                classification_seconds += time.perf_counter() - classify_start
            dst.write(labels, 1, window=dest_window)
            qdst.write(flags, 1, window=dest_window)
            solar_by_tile.append(dict(source_name=Path(tile.source["path"]).name, spatial_key=tile.spatial_key,
                                      reference=tile.reference, threshold_deg=threshold,
                                      **solar))
        tags = dict(policy=POLICY, requested_time=instant.requested, local_time=instant.local, utc_time=instant.utc,
                    encoding="1=shaded,0=sunlit,255=invalid/uncertain", source_and_owner=SOURCE_LINE,
                    solar_parameters="per canonical native tile; see frame metadata in result_index.json")
        dst.update_tags(**tags)
        qdst.update_tags(**tags, quality_reasons=json.dumps(QUALITY, sort_keys=True))
    for temp, path in zip(temps, (shade_path, quality_path)):
        os.replace(temp, path)
    counts = {str(code): 0 for code in (0, 1, 255)}
    quality_counts = {str(code): 0 for code in range(5)}
    with rasterio.open(shade_path) as ds, rasterio.open(quality_path) as qs:
        for _, win in ds.block_windows(1):
            labels, flags = ds.read(1, window=win), qs.read(1, window=win)
            if not np.all(np.isin(labels, [0, 1, 255])) or not np.all(np.isin(flags, list(range(5)))):
                raise ValueError("Output has invalid scientific encoding")
            if not np.array_equal(labels == 255, flags != 0):
                raise ValueError("Shade validity and quality reasons disagree")
            for code in counts:
                counts[code] += int(np.count_nonzero(labels == int(code)))
            for code in quality_counts:
                quality_counts[code] += int(np.count_nonzero(flags == int(code)))
    meta = dict(status="complete", key=_frame_key(plan, index), requested_time=instant.requested,
                utc_time=instant.utc, local_time=instant.local, raster=str(shade_path), quality_raster=str(quality_path),
                counts=counts, quality_counts=quality_counts, solar_by_tile=solar_by_tile,
                equality_neighborhood=dict(tolerance_deg=1e-4, count=equality_count, finite_denominator=finite_count,
                                           treatment="strict horizon > apparent elevation; no tolerance snapping"),
                hashes={p.name: digest_file(p) for p in (shade_path, quality_path)})
    meta["timing"] = dict(classification_seconds=classification_seconds,
                          output_validation_seconds=time.perf_counter() - compose_start - classification_seconds,
                          note="Output includes cache window I/O, equality accounting, raster writes/compression, readback and hashes")
    meta["integrity_sha256"] = fingerprint(meta)
    atomic_json(status, meta)
    return meta


def _render(frame, grid):
    factor = min(1., 1500 / max(grid.width, grid.height))
    shape = (max(1, round(grid.height * factor)), max(1, round(grid.width * factor)))
    with rasterio.open(frame["raster"]) as ds:
        labels = ds.read(1, out_shape=shape, resampling=Resampling.nearest)
    grey = np.full(shape, 160, np.uint8)
    grey[labels == 0], grey[labels == 1] = 255, 0
    width = math.ceil(max(1000, shape[1] + 48) / 16) * 16
    height = math.ceil(max(320, shape[0] + 160) / 16) * 16
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((24, 12), "SHADE WATCH HK / V1", font=_font(24, True), fill="black")
    draw.text((24, 48), frame["local_time"] + "  Asia/Hong_Kong", font=_font(20), fill="black")
    image.paste(Image.fromarray(grey).convert("RGB"), (24, 88))
    draw.text((24, height - 54), "Black: shaded | White: sunlit | Gray: invalid/uncertain | 0.5 m scientific pixels", font=_font(15), fill="black")
    draw.text((24, height - 28), "CEDD 2020 DSM; Government of the Hong Kong SAR", font=_font(14), fill="black")
    return image


def _media(plan, frames):
    if not plan.request.jpg and not plan.request.mp4:
        return dict(jpg=[], mp4=None, frames=0, memory_tracking="no media processes")
    out = Path(plan.output_directory) / "media"
    out.mkdir(parents=True, exist_ok=True)
    jpgs = []
    video = out / "shade_sequence.mp4"
    temp_video = out / "shade_sequence.tmp.mp4"
    writer = None
    pids = set()
    tracking = dict(encoder=False, decoder=False)
    try:
        if plan.request.mp4:
            writer = imageio.get_writer(temp_video, fps=4, codec="libx264", quality=8,
                                       pixelformat="yuv420p", macro_block_size=16,
                                       ffmpeg_log_level="error", output_params=["-threads", "1"])
        for i, frame in enumerate(frames):
            rendered = _render(frame, plan.grid)
            if plan.request.jpg:
                path = out / (Path(frame["raster"]).stem + ".jpg")
                temp = path.with_name(path.stem + ".tmp.jpg")
                rendered.save(temp, quality=94, subsampling=0)
                with Image.open(temp) as check:
                    check.verify()
                os.replace(temp, path)
                jpgs.append(dict(path=str(path), utc_time=frame["utc_time"], local_time=frame["local_time"], sha256=digest_file(path)))
            if writer is not None:
                writer.append_data(np.asarray(rendered))
                if i == 0:
                    pid = track_media_process(writer, "_write_gen", "p")
                    tracking["encoder"] = bool(pid)
                    if pid:
                        pids.add(pid)
        if writer is not None:
            writer.close()
            writer = None
            with imageio.get_reader(temp_video, "ffmpeg") as reader:
                pid = track_media_process(reader, "_read_gen", "process")
                tracking["decoder"] = bool(pid)
                if pid:
                    pids.add(pid)
                decoded = sum(1 for _ in reader)
            if decoded != len(frames):
                raise ValueError("Decoded media frame count differs from requested instants")
            os.replace(temp_video, video)
        result = dict(jpg=jpgs, mp4=str(video) if plan.request.mp4 else None,
                      frames=len(frames) if plan.request.mp4 else 0, fps=4,
                      frame_times=[f["utc_time"] for f in frames], process_tracking=tracking,
                      memory_tracking="sampled known encoder/decoder RSS; tracking booleans disclose gaps")
        atomic_json(out / "index.json", result)
        return result
    finally:
        if writer is not None:
            writer.close()
        EXTERNAL_PIDS.difference_update(pids)


def run_shade(plan, *, on_direction=None):
    """Execute an inspected plan; callback observes completed/reused directions."""
    if not isinstance(plan, ShadePlan) or plan.schema != "shade-watch-v1-plan-1.0":
        raise ValueError("run_shade needs a V1 ShadePlan")
    started = time.perf_counter()
    out, cache = Path(plan.output_directory), Path(plan.cache_directory)
    _owned_path(out, "outputs", "outputs/v1_query")
    _owned_path(cache, "data/processed/shade_v1", "data/processed/shade_v1/default")
    if _plan_key(plan.request, plan.grid, plan.tiles) != plan.key:
        raise ValueError("Plan/code was changed; call plan_shade again")
    if out.exists() and any(p.name != ".writer.lock" for p in out.iterdir()):
        try:
            prior = json.loads((out / "run_definition.json").read_text())
        except (OSError, ValueError) as exc:
            raise ValueError("Unmanaged existing output directory is protected") from exc
        if prior.get("key") != plan.key:
            raise ValueError("Output directory belongs to a different V1 request; choose a new directory")
    if shutil.disk_usage(ROOT).free < plan.resources["estimated_new_bytes"]:
        raise ValueError("Insufficient free disk for the bounded request estimate")
    with memory_monitor() as memory, exclusive_lock(out / ".writer.lock"):
        current = index_sources(plan.source_directory)
        for tile in plan.tiles:
            key, _, _ = spatial_identity(current, tile.source)
            if key != tile.spatial_key:
                raise ValueError("DSM dependencies changed after planning; call plan_shade again")
        atomic_json(out / "run_definition.json", dict(schema=plan.schema, key=plan.key, plan=plan.to_dict()))
        valid_frames = [_valid_frame(plan, i) for i in range(len(plan.request.instants))]
        preprocess_seconds = time.perf_counter() - started
        horizon_start = time.perf_counter()
        events, thresholds = [], {}
        if not all(valid_frames):
            for tile in plan.tiles:
                def record(event):
                    trimmed = {k: v for k, v in event.items() if k != "meta"}
                    with (out / "direction_events.jsonl").open("a") as handle:
                        handle.write(json.dumps(trimmed) + "\n")
                        handle.flush()
                    if memory["peak_tree_rss_bytes"] > plan.resources["memory_budget_bytes"]:
                        raise MemoryError("Measured V1 workflow RSS exceeds the declared budget")
                    if on_direction is not None:
                        on_direction(event)
                tile_events = ensure_directions(current, tile.source, tile.directions, cache,
                                                 tile.spatial_key, on_direction=record)
                events.extend(tile_events)
                if tile_events:
                    thresholds[tile.spatial_key] = tile_events[0]["meta"]["threshold_deg"]
        horizon_seconds = time.perf_counter() - horizon_start
        classification_start = time.perf_counter()
        frames = []
        for i, prior in enumerate(valid_frames):
            frames.append(prior or _compose_frame(plan, i, thresholds))
        classification_export_validation_seconds = time.perf_counter() - classification_start
        media_start = time.perf_counter()
        media = _media(plan, frames)
        jobs = dict(computed=sum(e["computed"] for e in events), reused=sum(e["reused"] for e in events),
                    horizon_calls=sum(e["horizon_calls"] for e in events), final_result_hits=sum(f is not None for f in valid_frames))
        performance = dict(preprocessing_seconds=preprocess_seconds, horizon_seconds=horizon_seconds,
                           kernel_seconds=sum(e["meta"].get("calculation_seconds", 0.) for e in events if e["computed"]),
                           classification_export_validation_seconds=classification_export_validation_seconds,
                           classification_seconds=sum(f["timing"]["classification_seconds"] for f, prior in zip(frames, valid_frames) if prior is None),
                           output_validation_seconds=sum(f["timing"]["output_validation_seconds"] for f, prior in zip(frames, valid_frames) if prior is None),
                           media_seconds=time.perf_counter() - media_start,
                           run_seconds=time.perf_counter() - started, planning_seconds=plan.planning_seconds,
                           **memory, memory_sampling_interval_seconds=.02,
                           worker_peak_rss_bytes=0, worker_note="single-process V1; worker allocations included in parent",
                           media_peak_measurement="included in tree RSS when PID tracking succeeds; no separate media-only maximum",
                           timing_note="run includes fresh input hashing, cache/output integrity, compression and media; planning separate; kernel includes first JIT if needed")
        index = dict(schema="shade-watch-v1-result-1.0", policy=POLICY, plan_key=plan.key,
                     requested_bounds=plan.request.requested_bounds, resolved_bounds=plan.grid.bounds(),
                     grid=asdict(plan.grid), request=asdict(plan.request), coverage=plan.coverage,
                     source_identities=[source_identity(r) for r in current],
                     tile_dependencies=[dict(key=t.spatial_key, sources=t.dependency_identities) for t in plan.tiles],
                     cache_directory=plan.cache_directory, frames=frames, media=media, jobs=jobs, performance=performance,
                     quality_reasons=QUALITY, observational_validation="NOT VERIFIED; no registered independent observations")
        atomic_json(out / "result_index.json", index)
    return ShadeResult(str(out / "result_index.json"), tuple(frames), jobs, performance)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "query"))
    times = parser.add_mutually_exclusive_group(required=True)
    times.add_argument("--at", action="append", help="ISO timestamp; repeat for an instant list")
    times.add_argument("--date", action="append", help="Hong Kong date; repeat for multi-date daylight")
    parser.add_argument("--interval-minutes", type=int, default=10)
    parser.add_argument("--timezone", default="Asia/Hong_Kong")
    parser.add_argument("--tile", action="append", help="Exact native DSM filename; repeat for rectangular selection")
    parser.add_argument("--center-lat", type=float)
    parser.add_argument("--center-lon", type=float)
    parser.add_argument("--mode", choices=("native", "custom"), default="native")
    parser.add_argument("--bounds", type=float, nargs=4, metavar=("LEFT", "BOTTOM", "RIGHT", "TOP"))
    parser.add_argument("--width-m", type=float)
    parser.add_argument("--height-m", type=float)
    parser.add_argument("--crop", type=int, nargs=4, metavar=("COL", "ROW", "WIDTH", "HEIGHT"))
    parser.add_argument("--direction-method", choices=tuple(DIRECTION_METHODS), default="nearest5")
    parser.add_argument("--jpg", action="store_true")
    parser.add_argument("--mp4", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--cache")
    parser.add_argument("--dsm-dir")
    parser.add_argument("--memory-budget-mb", type=int, default=8192)
    args = parser.parse_args(argv)
    try:
        plan = plan_shade(instants=args.at, dates=args.date, interval_minutes=args.interval_minutes,
                          local_timezone=args.timezone, tiles=args.tile,
                          latitude=args.center_lat, longitude=args.center_lon, mode=args.mode, bounds=args.bounds,
                          width_m=args.width_m, height_m=args.height_m, crop=tuple(args.crop) if args.crop else None,
                          direction_method=args.direction_method, jpg=args.jpg, mp4=args.mp4,
                          output_dir=args.output, cache_dir=args.cache, dsm_dir=args.dsm_dir,
                          memory_budget_mb=args.memory_budget_mb)
        if args.action == "plan":
            print(json.dumps(plan.to_dict(), indent=2))
        else:
            result = run_shade(plan)
            print(json.dumps(asdict(result), indent=2))
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f"V1 request rejected: {exc}\n")


if __name__ == "__main__":
    main()
