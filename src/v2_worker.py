"""Bounded metadata-only IPC workers and independently recoverable output tasks."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict
import json
import os
from pathlib import Path
import threading
import time

import numpy as np
import psutil
import rasterio
from rasterio.windows import Window

from . import v1
from .pipeline import EXTERNAL_PIDS, memory_monitor
from .spatial import digest_file, intersects
from .v1_cache import atomic_json, ensure_directions, entry_paths, exclusive_lock, source_identity, valid_entry


class Cancelled(RuntimeError):
    pass


def artifact(path, role):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest_file(path), role=role)


def artifacts_valid(items):
    try:
        return all(Path(i["path"]).stat().st_size == i["bytes"] and
                   digest_file(i["path"]) == i["sha256"] for i in items)
    except (OSError, KeyError, TypeError):
        return False


def _prepare(plan):
    from .v2 import json_metadata
    out = Path(plan.output_directory)
    items = [p.name for p in out.iterdir() if p.name != ".writer.lock"] if out.exists() else []
    definition = out / "run_definition.json"
    if items:
        try:
            if json.loads(definition.read_text())["key"] != plan.key:
                raise ValueError("Output directory belongs to another request")
        except (OSError, KeyError, ValueError) as exc:
            raise ValueError("Unmanaged or conflicting existing output is protected") from exc
        return
    atomic_json(definition, dict(schema=plan.schema, key=plan.key, plan=json_metadata(plan.to_dict())))


def _frames(plan):
    frames = [v1._valid_frame(plan, i) for i in range(len(plan.request.instants))]
    if any(f is None for f in frames):
        raise ValueError("Required scientific frames are not valid")
    return frames


def _metadata(cache, key, direction, source, memo):
    from .v2 import signature
    paths = entry_paths(cache, key, direction)
    token = (cache, key, direction)
    sig = tuple(tuple(signature(p)) for p in paths)
    cached = memo.get(token)
    if cached is not None and cached[0] == sig:
        memo.move_to_end(token)
        return cached[1]
    meta = valid_entry(cache, key, direction, source)
    if meta is None:
        raise ValueError("Required directional entry is incomplete/corrupt")
    memo[token] = (sig, meta)
    while len(memo) > 32:
        memo.popitem(last=False)
    return meta


def execute_task(kind, payload, plans, batch, store_directory, cancel, send, memo):
    from .v2 import plan_from_dict
    if cancel.is_set():
        raise Cancelled("Batch cancellation requested")
    if kind == "horizon":
        # A valid final-result hit does not force an evicted horizon to be rebuilt.
        required = set()
        for name in payload["consumers"]:
            plan = plan_from_dict(plans[name])
            for i in range(len(plan.request.instants)):
                if v1._valid_frame(plan, i) is None:
                    for tile in plan.tiles:
                        if tile.spatial_key == payload["key"] and tile.solar[i]["apparent_elevation_deg"] > 0:
                            required.add(tile.solar[i]["direction_deg"])
        def complete(event):
            send(dict(type="direction", value={k: v for k, v in event.items() if k != "meta"}))
            if cancel.is_set():
                raise Cancelled("Cancelled after committed directional checkpoint")
        events = ensure_directions(payload["records"], payload["source"], sorted(required),
                                   payload["cache"], payload["key"], on_direction=complete)
        items = []
        for direction in required:
            path, status = entry_paths(payload["cache"], payload["key"], direction)
            items.extend([artifact(path, "horizon"), artifact(status, "horizon_manifest")])
        return dict(artifacts=items, metrics=dict(computed=sum(e["computed"] for e in events),
                    reused=sum(e["reused"] for e in events), horizon_calls=sum(e["horizon_calls"] for e in events),
                    source_records=len(payload["records"]), skipped_final_hit=not required))
    if kind == "mosaic":
        layers = []
        for name, value in plans.items():
            plan = plan_from_dict(value)
            for frame in _frames(plan):
                layers.append(dict(request=name, utc_time=frame["utc_time"], raster=frame["raster"],
                                   quality_raster=frame["quality_raster"], grid=asdict(plan.grid),
                                   bounds=plan.grid.bounds(), policy=v1.POLICY))
        path = Path(store_directory) / f"{batch}.logical_mosaic.json"
        atomic_json(path, dict(schema="shade-watch-v2-logical-mosaic-1.0", batch=batch,
                    crs="EPSG:2326", resolution_m=.5, layers=layers,
                    note="logical source view; no physical whole-region copy"))
        return dict(artifacts=[artifact(path, "logical_mosaic")], metrics={})
    plan = plan_from_dict(plans[payload["request"]])
    out = Path(plan.output_directory)
    with exclusive_lock(out / ".writer.lock"):
        _prepare(plan)
        if kind == "frame":
            i = payload["index"]
            frame = v1._valid_frame(plan, i)
            hit = frame is not None
            if frame is None:
                thresholds = {}
                for tile in plan.tiles:
                    solar = tile.solar[i]
                    if solar["apparent_elevation_deg"] > 0:
                        thresholds[tile.spatial_key] = _metadata(plan.cache_directory, tile.spatial_key,
                            solar["direction_deg"], tile.source, memo)["threshold_deg"]
                frame = v1._compose_frame(plan, i, thresholds)
            items = [artifact(p, role) for p, role in zip(v1._frame_paths(out, plan.request.instants[i]),
                       ("shade", "quality", "frame_manifest"))]
            return dict(artifacts=items, metrics=dict(final_result_hits=int(hit),
                        new_frames=int(not hit), equality_neighborhood=frame["equality_neighborhood"],
                        frame_timing=frame["timing"] if not hit else {}))
        frames = _frames(plan)
        if kind == "media":
            class CheckedFrames:
                def __len__(self):
                    return len(frames)
                def __iter__(self):
                    for f in frames:
                        if cancel.is_set():
                            raise Cancelled("Cancelled between media frames")
                        yield f
            media = v1._media(plan, CheckedFrames())
            items = [artifact(out / "media/index.json", "media_manifest")]
            items.extend(artifact(f["path"], "jpg") for f in media["jpg"])
            if media["mp4"]:
                items.append(artifact(media["mp4"], "mp4"))
            return dict(artifacts=items, metrics=dict(media_tracking=media.get("process_tracking", {})))
        if kind == "statistics":
            path = out / "statistics.json"
            atomic_json(path, dict(frames=[dict(utc_time=f["utc_time"], counts=f["counts"],
                       quality_counts=f["quality_counts"]) for f in frames],
                       note="Derived counts; pixel rasters are authoritative"))
            return dict(artifacts=[artifact(path, "statistics")], metrics={})
        if kind != "index":
            raise ValueError("Unknown batch task kind")
        media = dict(jpg=[], mp4=None, frames=0)
        if plan.request.jpg or plan.request.mp4:
            media = json.loads((out / "media/index.json").read_text())
            if media["frame_times"] != [f["utc_time"] for f in frames]:
                raise ValueError("Media timestamps do not match the scientific request")
        # Shared scientific output must not depend on its scheduling context.
        # The first publisher's immutable definition supplies relocation-sensitive provenance.
        canonical = json.loads((out / "run_definition.json").read_text())["plan"]
        index = dict(schema="shade-watch-v2-result-1.1", policy=v1.POLICY, plan_key=plan.key,
                     grid=asdict(plan.grid), request=asdict(plan.request),
                     requested_bounds=plan.request.requested_bounds, resolved_bounds=plan.grid.bounds(),
                     coverage=plan.coverage, tile_dependencies=[dict(key=t.spatial_key,
                     sources=t.dependency_identities) for t in plan.tiles],
                     frames=frames, media=media, cache_directory=canonical["cache_directory"],
                     quality_reasons=v1.QUALITY,
                     observational_validation="NOT VERIFIED; no registered observations")
        atomic_json(out / "result_index.json", index)
        from .pipeline import fingerprint
        receipt = Path(store_directory) / "receipts" / batch / (fingerprint(payload["request"]) + ".json")
        atomic_json(receipt, dict(batch_id=batch, request_id=payload["request"],
                    state_directory=str(store_directory), cache_directory=plan.cache_directory,
                    plan_key=plan.key, result_index=str(out / "result_index.json")))
        return dict(artifacts=[artifact(out / "result_index.json", "result_index"),
                               artifact(receipt, "execution_receipt")], metrics={})


def classify_failure(exc):
    import errno
    if isinstance(exc, Cancelled):
        return dict(category="cancelled", retryable=False, error=repr(exc))
    if isinstance(exc, RuntimeError) and "writer owns" in str(exc):
        return dict(category="ownership_contention", retryable=True, error=repr(exc))
    if isinstance(exc, OSError):
        retryable = exc.errno in {errno.EIO, errno.EINTR, errno.EAGAIN, errno.ETIMEDOUT}
        return dict(category="transient_io" if retryable else "input_or_storage", retryable=retryable, error=repr(exc))
    return dict(category="validation_or_execution", retryable=False, error=repr(exc))


def worker_entry(connection, cancel, root, token, owner_file):
    v1.ROOT = Path(root)
    owner = dict(pid=os.getpid(), create_time=psutil.Process().create_time(), token=token)
    atomic_json(owner_file, owner)
    send_lock = threading.Lock()
    def send(value):
        with send_lock:
            connection.send(value)
    send(dict(type="ready", owner=owner))
    memo = OrderedDict()
    while True:
        try:
            message = connection.recv()
        except EOFError:
            return
        if message is None:
            return
        done = threading.Event()
        with memory_monitor() as memory:
            def watch():
                while not done.wait(.1):
                    media = []
                    for pid in set(EXTERNAL_PIDS):
                        try:
                            proc = psutil.Process(pid)
                            media.append(dict(pid=pid, create_time=proc.create_time(), parent=os.getpid()))
                        except psutil.Error:
                            pass
                    try:
                        send(dict(type="memory", memory=dict(memory), media=media))
                    except (BrokenPipeError, EOFError, OSError):
                        cancel.set()
                        return
            thread = threading.Thread(target=watch, daemon=True)
            thread.start()
            started = time.perf_counter()
            try:
                while True:
                    try:
                        result = execute_task(message["kind"], message["payload"], message["plans"],
                                   message["batch"], message["store_directory"], cancel, send, memo)
                        break
                    except RuntimeError as exc:
                        if ("writer owns" not in str(exc) or time.perf_counter() - started > 15
                                or cancel.wait(.1)):
                            raise
                result["metrics"].update(wall_seconds=time.perf_counter() - started, **memory)
                send(dict(type="result", result=result))
            except BaseException as exc:
                send(dict(type="failure", error=classify_failure(exc)))
            finally:
                done.set()
                thread.join()


def read_logical_window(path, *, utc_time, bounds):
    """Return a bounded scientific window from logical sources; preserve gaps/flags."""
    from .v2 import Grid
    from rasterio.transform import from_origin
    manifest = json.loads(Path(path).read_text())
    if manifest.get("schema") != "shade-watch-v2-logical-mosaic-1.0":
        raise ValueError("Unsupported logical view")
    left, bottom, right, top = bounds
    if any(not np.isfinite(v) or abs(v / .5 - round(v / .5)) > 1e-7 for v in bounds):
        raise ValueError("Logical window must align to canonical 0.5 m edges")
    w, h = round((right - left) / .5), round((top - bottom) / .5)
    if min(w, h) <= 0 or w * h > v1.MAX_OUTPUT_PIXELS:
        raise ValueError("Logical window exceeds bounded area profile")
    labels = np.full((h, w), 255, np.uint8)
    quality = np.ones((h, w), np.uint8)
    seen = np.zeros((h, w), bool)
    for layer in manifest["layers"]:
        if layer["utc_time"] != utc_time or not intersects(bounds, layer["bounds"]):
            continue
        l, b, r, t = layer["bounds"]
        a, z, c, d = max(left, l), max(bottom, b), min(right, r), min(top, t)
        iw, ih = round((c-a)/.5), round((d-z)/.5)
        source = Window(round((a-l)/.5), round((t-d)/.5), iw, ih)
        dest = (slice(round((top-d)/.5), round((top-d)/.5)+ih),
                slice(round((a-left)/.5), round((a-left)/.5)+iw))
        with rasterio.open(layer["raster"]) as ds, rasterio.open(layer["quality_raster"]) as qs:
            expected = Grid(**{**layer["grid"], "transform": tuple(layer["grid"]["transform"])})
            if ds.transform != expected.affine or qs.transform != expected.affine or ds.crs.to_string() != "EPSG:2326":
                raise ValueError("Logical source georeferencing changed")
            avalues, qvalues = ds.read(1, window=source), qs.read(1, window=source)
        overlap = seen[dest]
        if np.any(overlap & ((labels[dest] != avalues) | (quality[dest] != qvalues))):
            raise ValueError("Conflicting scientific pixels in overlapping logical layers")
        labels[dest], quality[dest], seen[dest] = avalues, qvalues, True
    return labels, quality, from_origin(left, top, .5, .5)
