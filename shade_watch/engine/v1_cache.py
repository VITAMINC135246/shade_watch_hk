"""Canonical, content-addressed native-tile obstruction entries for V1."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import time
import uuid

import numpy as np
import rasterio

from .horizon import pixel_centred_horizon
from .pipeline import fingerprint, profile
from .spatial import Grid, digest_file, expand, intersects, read_window

POLICY = "SW-V1-POLICY-1.0"
ALGORITHM = "pixel-centred-1km-projected-origin-1.0"
SEARCH_M = BUFFER_M = 1000.0
RAY_STEP_M = 0.25


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("w") as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def exclusive_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Another V1 writer owns {path.parent}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def tile_grid(tile):
    return Grid(tile["width"], tile["height"], tuple(tile["transform"]), tile["crs"], "native_tile")


def source_identity(record):
    """No absolute paths: relocation and output naming do not change science."""
    nodata = record["nodata"]
    return {k: record[k] for k in ("width", "height", "transform", "crs", "bounds", "sha256")} | {
        "nodata": "NaN" if nodata is not None and math.isnan(nodata) else nodata,
        "auxiliary": sorted((dict(sha256=p["sha256"], bytes=p["bytes"])
                             for p in record.get("auxiliary_files", [])), key=lambda x: x["sha256"]),
    }


def spatial_identity(records, tile):
    grid = tile_grid(tile)
    halo = math.ceil(BUFFER_M / grid.res)
    bounds = grid.bounds(expand((0, 0, grid.width, grid.height), halo))
    dependencies = [r for r in records if intersects(bounds, r["bounds"])]
    identity = dict(
        algorithm=ALGORITHM, policy=POLICY,
        geometry=dict(width=grid.width, height=grid.height, transform=grid.transform, crs=grid.crs),
        anchor="EPSG:2326 projected origin E0,N0; row=-north/res; col=east/res",
        sources=sorted((source_identity(r) for r in dependencies), key=fingerprint),
        search_m=SEARCH_M, buffer_m=BUFFER_M, ray_step_m=RAY_STEP_M,
        numerical_code={name: digest_file(Path(__file__).with_name(name))
                        for name in ("horizon.py", "spatial.py", "v1_cache.py")},
    )
    return fingerprint(identity), identity, dependencies


def entry_paths(root, key, direction):
    token = fingerprint(dict(direction_deg=float(direction)))[:20]
    base = Path(root) / key / f"direction_{token}"
    return base.with_suffix(".tif"), base.with_suffix(".json")


def valid_entry(root, key, direction, tile):
    path, status = entry_paths(root, key, direction)
    grid = tile_grid(tile)
    try:
        meta = json.loads(status.read_text())
        if not isinstance(meta, dict):
            return None
        integrity = meta.pop("integrity_sha256")
        if (fingerprint(meta) != integrity or meta["status"] != "complete"
                or meta["key"] != key or meta["direction_deg"] != float(direction)
                or meta["sha256"] != digest_file(path)
                or not 0 <= meta["threshold_deg"] <= 90):
            return None
        with rasterio.open(path) as ds:
            if (ds.shape != (grid.height, grid.width) or ds.count != 3
                    or ds.dtypes != ("float32",) * 3 or ds.transform != grid.affine
                    or ds.crs.to_string() != grid.crs or ds.tags().get("cache_key") != key):
                return None
            for _, win in ds.block_windows(1):
                horizon, support, distance = ds.read(window=win)
                if (np.any(np.isinf(horizon)) or np.any((horizon < 0) | (horizon > 90))
                        or not np.all(np.isin(support, [0, 1]))
                        or not np.all(np.isfinite(distance))
                        or np.any((distance < 0) | (distance > SEARCH_M))
                        or np.any(~np.isfinite(horizon) & ((support != 0) | (distance != 0)))):
                    return None
        meta["integrity_sha256"] = integrity
        return meta
    except (OSError, ValueError, KeyError, TypeError, rasterio.errors.RasterioError):
        return None


def canonical_origin(grid, region):
    return (round(-grid.affine.f / grid.res) + region[1],
            round(grid.affine.c / grid.res) + region[0])


def diagnostic_horizon(records, tile, window, direction):
    """Small canonical window, same 1 km operator; does not publish a cache."""
    grid = tile_grid(tile)
    c, r, w, h = window
    if min(w, h) <= 0 or c < 0 or r < 0 or c + w > grid.width or r + h > grid.height:
        raise ValueError("Diagnostic window must be inside one native tile")
    halo = math.ceil(BUFFER_M / grid.res)
    region = expand(tuple(window), halo)
    dsm = read_window(records, grid, region)
    rr, cc = np.indices((h, w), dtype=np.int32)
    rr += halo
    cc += halo
    origin_row, origin_col = canonical_origin(grid, region)
    arrays = pixel_centred_horizon(dsm, rr.ravel(), cc.ravel(), float(direction),
                                  SEARCH_M, SEARCH_M, grid.res, origin_row, origin_col)
    return tuple(a.reshape(h, w) for a in arrays)


def ensure_directions(records, tile, directions, root, key, on_direction=None):
    """Lock before revalidation; completed entries survive process termination."""
    events = []
    with exclusive_lock(Path(root) / key / ".writer.lock"):
        valid = {d: valid_entry(root, key, d, tile) for d in directions}
        missing = [d for d in directions if valid[d] is None]
        dsm = None
        grid = tile_grid(tile)
        if missing:
            halo = math.ceil(BUFFER_M / grid.res)
            region = expand((0, 0, grid.width, grid.height), halo)
            pre_start = time.perf_counter()
            dsm = read_window(records, grid, region)
            target = dsm[halo:halo + grid.height, halo:halo + grid.width]
            surface = target[np.isfinite(target)]
            buffered = dsm[np.isfinite(dsm)]
            min_height = float(surface.min()) if surface.size else None
            max_height = float(buffered.max()) if buffered.size else None
            threshold = (math.degrees(math.atan(max(0., max_height - min_height) / SEARCH_M))
                         if min_height is not None and max_height is not None else 0.)
            stats = dict(valid_target_pixels=int(surface.size), total_target_pixels=target.size,
                         min_target_height_m=min_height, max_buffer_height_m=max_height)
            del surface, buffered
            rr, cc = np.indices((grid.height, grid.width), dtype=np.int32)
            rr += halo
            cc += halo
            origin_row, origin_col = canonical_origin(grid, region)
            preprocessing_seconds = time.perf_counter() - pre_start
        for direction in directions:
            if valid[direction] is not None:
                event = dict(key=key, direction_deg=direction, computed=0, reused=1,
                             horizon_calls=0, seconds=0., meta=valid[direction])
            else:
                path, status = entry_paths(root, key, direction)
                # Remove only this campaign's stale temporaries while exclusively locked.
                for stale in path.parent.glob(path.name + ".*.tmp"):
                    stale.unlink(missing_ok=True)
                temp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
                atomic_json(status, dict(status="running", key=key, direction_deg=direction))
                start = time.perf_counter()
                try:
                    calc_start = time.perf_counter()
                    arrays = pixel_centred_horizon(dsm, rr.ravel(), cc.ravel(), float(direction),
                                                  SEARCH_M, SEARCH_M, grid.res, origin_row, origin_col)
                    calculation_seconds = time.perf_counter() - calc_start
                    export_start = time.perf_counter()
                    with rasterio.open(temp, "w", **profile(grid, (0, 0, grid.width, grid.height), 3, "float32", None)) as ds:
                        for band, array in enumerate(arrays, 1):
                            ds.write(array.reshape(grid.height, grid.width).astype(np.float32, copy=False), band)
                        for band, text in enumerate(("known_horizon_degrees", "complete_ray_support_0_or_1",
                                                     "maximum_blocker_sample_distance_m"), 1):
                            ds.set_band_description(band, text)
                        ds.update_tags(cache_key=key, direction_deg=direction, algorithm=ALGORITHM,
                                       policy=POLICY, search_m=SEARCH_M, buffer_m=BUFFER_M)
                    del arrays
                    os.replace(temp, path)
                    meta = dict(status="complete", key=key, direction_deg=float(direction),
                                algorithm=ALGORITHM, threshold_deg=threshold, stats=stats,
                                sha256=digest_file(path), calculation_seconds=calculation_seconds,
                                export_hash_seconds=time.perf_counter() - export_start,
                                preprocessing_seconds=preprocessing_seconds)
                    meta["integrity_sha256"] = fingerprint(meta)
                    atomic_json(status, meta)
                    if valid_entry(root, key, direction, tile) is None:
                        raise ValueError(f"Published cache failed validation: {path}")
                    event = dict(key=key, direction_deg=direction, computed=1, reused=0,
                                 horizon_calls=1, seconds=time.perf_counter() - start, meta=meta)
                except BaseException as exc:
                    temp.unlink(missing_ok=True)
                    atomic_json(status, dict(status="failed", key=key, direction_deg=direction,
                                             error=repr(exc)))
                    raise
            events.append(event)
            if on_direction is not None:
                on_direction(event)
    return events
