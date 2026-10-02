"""Reliable local V2 batches: plan, submit, run, status, cancel and resume."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import shutil
import time

import psutil

from . import v1
from .pipeline import fingerprint
from .spatial import Grid, digest_file
from .v1_cache import entry_paths, source_identity
from .v2_state import Store, local_filesystem

SCHEMA = "shade-watch-v2-batch-1.0"
MEMORY_CEILING = 12 * 1024**3
ARTIFACT_CEILING = 20 * 1024**3


def json_metadata(value):
    """GeoTIFF NaN NoData is represented explicitly in strict JSON metadata."""
    if isinstance(value, dict):
        return {k: json_metadata(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [json_metadata(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        raise ValueError("Infinite metadata is invalid")
    return value


def signature(path):
    st = Path(path).stat()
    return [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino]


def plan_from_dict(value):
    req = dict(value["request"])
    req["instants"] = tuple(v1.Instant(**t) for t in req["instants"])
    for name in ("dates", "selector", "requested_bounds", "crop"):
        if req[name] is not None:
            req[name] = tuple(req[name])
    grid = dict(value["grid"])
    grid["transform"] = tuple(grid["transform"])
    grid["selected_sources"] = tuple(grid["selected_sources"])
    tiles = []
    for tile in value["tiles"]:
        tile = dict(tile)
        tile["source"] = dict(tile["source"])
        if tile["source"].get("nodata") == "NaN":
            tile["source"]["nodata"] = float("nan")
        for name in ("dependency_identities", "solar", "directions", "missing_directions"):
            tile[name] = tuple(tile[name])
        tiles.append(v1.TilePlan(**tile))
    value = dict(value)
    value.update(request=v1.ShadeRequest(**req), grid=Grid(**grid), tiles=tuple(tiles))
    return v1.ShadePlan(**value)


@dataclass(frozen=True)
class BatchPlan:
    definition: dict
    estimate: dict
    planning_seconds: float

    @property
    def id(self):
        return self.definition["id"]

    def to_dict(self):
        return asdict(self)


def load_model(path=None):
    path = Path(path or Path(__file__).resolve().parents[1] / "docs/v2/estimator.json")
    if path.exists():
        model = json.loads(path.read_text())
        if model.get("schema") != "shade-watch-v2-estimator-1.0":
            raise ValueError("Unsupported estimator model")
        coefficients=model.get("coefficients",{})
        if not isinstance(coefficients,dict) or any(
            type(coefficients.get(k)) not in (int,float) or not math.isfinite(coefficients[k]) or coefficients[k]<0
            for k in ("catalog_seconds","startup_seconds","direction_seconds","frame_seconds","hit_seconds","media_frame_seconds")):
            raise ValueError("Estimator coefficients must be finite nonnegative numbers")
        if coefficients["direction_seconds"] <= 0 or coefficients["frame_seconds"] <= 0:
            raise ValueError("Estimator work coefficients must be positive")
        if not 0 <= coefficients.get("classification_seconds",0) <= coefficients["frame_seconds"]:
            raise ValueError("Invalid classification/output coefficient split")
        for efficiencies in (model.get("efficiency"),model.get("direction_efficiency",model.get("efficiency"))):
            if not isinstance(efficiencies,dict) or any(type(v) not in (int,float) or not 0<v<=1 for v in efficiencies.values()):
                raise ValueError("Estimator efficiency must be in (0,1]")
        return model | {"model_sha256": digest_file(path)}
    return dict(schema="shade-watch-v2-estimator-1.0", calibrated=False,
                coefficients=dict(catalog_seconds=0.3, startup_seconds=1.2,
                                  direction_seconds=10., frame_seconds=.3, hit_seconds=.03,
                                  media_frame_seconds=.1, controller_task_seconds=.025),
                efficiency={"1": 1., "2": .8}, domain={})


def estimate_batch(definition, model=None):
    model = model or load_model()
    c = model["coefficients"]
    horizon = [t for t in definition["tasks"] if t["kind"] == "horizon"]
    plans = [plan_from_dict(p) for p in definition["requests"].values()]
    misses = sum(t["payload"]["missing_units"] for t in horizon)
    all_directions = sum(len(t["payload"]["directions"]) for t in horizon)
    frame_units = sum(p.grid.width * p.grid.height / 1_800_000 *
                      (len(p.request.instants) - definition["final_hits"][name])
                      for name, p in zip(definition["requests"], plans))
    hit_count = sum(definition["final_hits"].values())
    media_units = sum(len(p.request.instants) * (int(p.request.jpg) + int(p.request.mp4))
                      for p in plans)
    workers = definition["settings"]["workers"]
    # Effective concurrency is limited by runnable native work, never N cores by fiat.
    horizon_parallel = min(workers, max(1, sum(bool(t["payload"]["missing_units"]) for t in horizon)))
    efficiency = model["efficiency"].get(str(workers))
    measured = efficiency is not None
    efficiency = efficiency or .65
    direction_efficiency = model.get("direction_efficiency", model["efficiency"]).get(str(horizon_parallel), .65)
    class_cost = c.get("classification_seconds", min(.02, c["frame_seconds"]))
    phases = dict(catalog_validation_seconds=c["catalog_seconds"] * len(definition["catalogues"]),
                  startup_seconds=c["startup_seconds"],
                  missing_direction_seconds=c["direction_seconds"] * misses /
                    (horizon_parallel * direction_efficiency),
                  warm_classification_seconds=class_cost * frame_units / (workers * efficiency),
                  output_compression_validation_seconds=(c["frame_seconds"]-class_cost) * frame_units / (workers * efficiency),
                  final_hit_seconds=c["hit_seconds"] * hit_count / (workers * efficiency),
                  media_seconds=c["media_frame_seconds"] * media_units,
                  controller_validation_seconds=c.get("controller_task_seconds", .025) * len(definition["tasks"]))
    total = sum(phases.values())
    domain = model.get("domain", {})
    in_domain = (model.get("calibrated", False) and measured and not media_units
                 and all(t.source["width"] == 1500 and t.source["height"] == 1200
                         for p in plans for t in p.tiles)
                 and all(Path(t.source["path"]).name in domain.get("source_tiles", [])
                         for p in plans for t in p.tiles)
                 and all(p.request.direction_method == "nearest5" for p in plans)
                 and all(p.request.mode == "native" and p.request.crop is None and len(p.tiles)==1 for p in plans)
                 and not hit_count
                 and not definition["settings"]["logical_mosaic"] and not definition["settings"]["statistics"]
                 and len(horizon) <= domain.get("max_tiles", 0)
                 and frame_units <= domain.get("max_native_frames", 0)
                 and all_directions <= domain.get("max_union_directions", 0))
    return dict(model=model, phases=phases, total_wall_seconds=total,
                indicative_range_seconds=[total * .65, total * 1.6],
                range_note="engineering variation allowance, not a fitted confidence interval",
                calibrated_domain=in_domain, extrapolated=not in_domain,
                missing_direction_units=misses, union_direction_entries=all_directions,
                warm_native_frame_units=frame_units, final_result_hits=hit_count,
                resources=definition["resources"],
                assumptions=["local same-machine filesystem; warm OS/JIT code cache",
                             "cold means empty directional cache, not flushed OS cache",
                             "effective-pixel/terrain changes affect directional cost",
                             "outputs include lossless compression/readback; media separate",
                             "whole-territory estimates require explicit profile and are extrapolations"])


def plan_batch(requests, *, workers=1, memory_budget_mb=12288, artifact_budget_bytes=ARTIFACT_CEILING,
               max_attempts=3, logical_mosaic=False, statistics=False, model_path=None):
    """Read-only plan. Requests are named kwargs dictionaries or V1 ShadePlans."""
    started = time.perf_counter()
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError("V2 workers must be 1..4")
    if type(memory_budget_mb) is not int or not 512 <= memory_budget_mb <= 12288:
        raise ValueError("V2 memory budget must be 512..12288 MiB")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 5:
        raise ValueError("max_attempts must be 1..5")
    if type(artifact_budget_bytes) is not int or not 1 <= artifact_budget_bytes <= ARTIFACT_CEILING:
        raise ValueError("Artifact budget must be <=20 GiB")
    if type(logical_mosaic) is not bool or type(statistics) is not bool:
        raise ValueError("Output selections must be booleans")
    requests = list(requests)
    if not requests or len(requests) > 4096:
        raise ValueError("A local batch needs 1..4096 bounded requests")
    plans, catalogues, snapshots, hits = {}, {}, {}, {}
    metadata_bytes = 0
    union = {}
    for i, item in enumerate(requests):
        if isinstance(item, v1.ShadePlan):
            name, plan = f"request_{i:04d}", item
            directory = plan.source_directory
            if directory not in catalogues:
                catalogues[directory] = v1.index_sources(directory)
        else:
            kwargs = dict(item)
            name = kwargs.pop("id", f"request_{i:04d}")
            directory = str(Path(kwargs.get("dsm_dir") or v1.RAW).resolve())
            if directory not in catalogues:
                catalogues[directory] = v1.index_sources(directory)
            kwargs.setdefault("cache_dir", "data/processed/shade_v1/v2_default")
            kwargs.setdefault("output_dir", f"outputs/v2_batch/{name}")
            plan = v1.plan_shade(**kwargs, _records=catalogues[directory])
        if not isinstance(name, str) or not name or name in plans:
            raise ValueError("Request IDs must be distinct nonempty strings")
        if any(p["output_directory"] == plan.output_directory for p in plans.values()):
            raise ValueError("Distinct requests require distinct output directories")
        if v1._plan_key(plan.request, plan.grid, plan.tiles) != plan.key:
            raise ValueError("Changed V1 plan; make a fresh plan")
        for path in (plan.output_directory, plan.cache_directory):
            local_filesystem(path)
        # Strong identity check even for supplied V1 plans; only metadata is shared.
        from .v1_cache import spatial_identity, valid_entry
        frame_hits = [v1._valid_frame(plan, f) is not None for f in range(len(plan.request.instants))]
        for tile in plan.tiles:
            key, _, deps = spatial_identity(catalogues[directory], tile.source)
            if key != tile.spatial_key:
                raise ValueError("Stale V1 input plan")
            union_key = fingerprint([plan.cache_directory, key])
            group = union.setdefault(union_key, dict(source=tile.source, key=key,
                 cache=plan.cache_directory, records=deps, directions=set(), needed=set(), consumers=[]))
            group["directions"].update(tile.directions)
            group["needed"].update(s["direction_deg"] for f,s in enumerate(tile.solar)
                                    if not frame_hits[f] and s["apparent_elevation_deg"] > 0)
            group["consumers"].append(name)
        plans[name] = json_metadata(plan.to_dict())
        metadata_bytes += len(json.dumps(plans[name]).encode())
        if metadata_bytes > 128 * 1024**2:
            raise ValueError("Batch request metadata exceeds the bounded 128 MiB local profile")
        hits[name] = sum(frame_hits)
    for directory, records in catalogues.items():
        snapshots[directory] = {r["path"]: signature(r["path"]) for r in records}
        for r in records:
            snapshots[directory].update({f["path"]: signature(f["path"]) for f in r.get("auxiliary_files", [])})
    tasks, dependencies = [], {}
    for key, group in union.items():
        directions = sorted(group["directions"])
        missing = [d for d in sorted(group["needed"]) if valid_entry(group["cache"], group["key"], d, group["source"]) is None]
        task_id = "horizon_" + key
        dependencies[key] = task_id
        payload = {k: v for k, v in group.items() if k not in {"directions", "needed"}} | dict(
            directions=directions, missing_directions=missing,
            missing_units=len(missing) * group["source"]["width"] * group["source"]["height"] / 1_800_000)
        tasks.append(dict(id=task_id, kind="horizon", payload=payload, dependencies=[]))
    finals = []
    for name, value in plans.items():
        plan = plan_from_dict(value)
        deps = [dependencies[fingerprint([plan.cache_directory, t.spatial_key])] for t in plan.tiles]
        frames = []
        for i in range(len(plan.request.instants)):
            task_id = f"frame_{fingerprint(name)}_{i}"
            tasks.append(dict(id=task_id, kind="frame", payload=dict(request=name, index=i), dependencies=deps))
            frames.append(task_id)
        outputs = list(frames)
        for kind, enabled in (("media", plan.request.jpg or plan.request.mp4), ("statistics", statistics)):
            if enabled:
                task_id = kind + "_" + fingerprint(name)
                tasks.append(dict(id=task_id, kind=kind, payload=dict(request=name), dependencies=frames))
                outputs.append(task_id)
        task_id = "index_" + fingerprint(name)
        tasks.append(dict(id=task_id, kind="index", payload=dict(request=name), dependencies=outputs))
        finals.append(task_id)
    if logical_mosaic:
        tasks.append(dict(id="mosaic", kind="mosaic", payload={}, dependencies=finals))
    worker_peak = max(plan_from_dict(p).resources["estimated_peak_bytes"] for p in plans.values())
    peak_memory = 400 * 1024**2 + 2 * metadata_bytes + workers * max(worker_peak, 768 * 1024**2)
    retained = sum(plan_from_dict(p).grid.width * plan_from_dict(p).grid.height * 2 *
                   (len(plan_from_dict(p).request.instants) - hits[name]) for name, p in plans.items())
    retained += sum(t["payload"]["source"]["width"] * t["payload"]["source"]["height"] * 12 *
                    len(t["payload"]["missing_directions"]) for t in tasks if t["kind"] == "horizon")
    retained += sum(4 * 1024**2 * len(plan_from_dict(p).request.instants) *
                    (int(p["request"]["jpg"]) + int(p["request"]["mp4"])) for p in plans.values())
    temporary = workers * max(t["source"]["width"] * t["source"]["height"] * 12 for t in union.values())
    temporary += 16 * 1024**2 + len(tasks) * 32768
    if peak_memory > memory_budget_mb * 1024**2:
        raise ValueError("Requested concurrency exceeds the configured total memory budget")
    if retained + temporary > artifact_budget_bytes:
        raise ValueError("Batch exceeds configured retained/temporary artifact budget")
    definition = dict(schema=SCHEMA, requests=plans, catalogues=catalogues, signatures=snapshots,
                      settings=dict(workers=workers, memory_budget_mb=memory_budget_mb,
                                    artifact_budget_bytes=artifact_budget_bytes, max_attempts=max_attempts,
                                    logical_mosaic=logical_mosaic, statistics=statistics),
                      resources=dict(estimated_peak_bytes=peak_memory, memory_budget_bytes=memory_budget_mb * 1024**2,
                                     retained_new_bytes=retained, temporary_new_bytes=temporary,
                                     estimated_peak_new_bytes=retained + temporary, request_metadata_bytes=metadata_bytes),
                      tasks=tasks, final_hits=hits)
    # Runtime measurements/cache availability are not request identity.
    identity = dict(requests={n: p["key"] for n, p in plans.items()},
                    directories={n: [p["output_directory"], p["cache_directory"]] for n, p in plans.items()},
                    settings=definition["settings"], engine=digest_file(Path(__file__)),
                    worker=digest_file(Path(__file__).with_name("v2_worker.py")))
    definition=json_metadata(definition)
    definition["engine_code"] = {name: digest_file(Path(__file__).with_name(name))
                                 for name in ("v2.py", "v2_worker.py", "v2_runner.py", "v2_state.py")}
    definition["id"] = fingerprint(identity)
    definition["integrity"] = fingerprint(definition)
    return BatchPlan(definition, estimate_batch(definition, load_model(model_path)), time.perf_counter() - started)


def _store(directory, *, create=False):
    path = v1._owned_path(directory, "outputs", "outputs/v2_state")
    return Store(path, create=create)


def submit_batch(plan, *, state_dir="outputs/v2_state"):
    if not isinstance(plan, BatchPlan) or plan.definition.get("schema") != SCHEMA:
        raise ValueError("submit_batch requires a V2 BatchPlan")
    definition = plan.definition
    if definition.get("integrity") != fingerprint({k: v for k, v in definition.items() if k != "integrity"}):
        raise ValueError("Batch plan was modified")
    state_path = v1._owned_path(state_dir, "outputs", "outputs/v2_state")
    if any(Path(p["output_directory"]) == state_path for p in definition["requests"].values()):
        raise ValueError("State and request output directories must be distinct")
    store = _store(state_dir, create=True)
    try:
        with store.tx():
            prior = store.db.execute("SELECT id FROM batches WHERE id=?", (plan.id,)).fetchone()
            if prior:
                return plan.id
            for name, value in definition["requests"].items():
                existing = store.db.execute("SELECT plan_key FROM outputs WHERE directory=?", (value["output_directory"],)).fetchone()
                if existing and existing["plan_key"] != value["key"]:
                    raise ValueError("Output is already reserved by another scientific request")
                store.db.execute("INSERT OR IGNORE INTO outputs VALUES(?,?)", (value["output_directory"], value["key"]))
            store.db.execute("INSERT INTO batches(id,definition,state,created,updated) VALUES(?,?,?,?,?)",
                             (plan.id, json.dumps(plan.to_dict()), "QUEUED", time.time(), time.time()))
            for name, value in definition["requests"].items():
                store.db.execute("INSERT INTO requests VALUES(?,?,?)", (plan.id, name, json.dumps(value)))
            for task in definition["tasks"]:
                task_id = plan.id + ":" + task["id"]
                store.db.execute("INSERT INTO tasks(id,batch,kind,payload,state,max_attempts) VALUES(?,?,?,?,?,?)",
                                 (task_id, plan.id, task["kind"], json.dumps(task["payload"]), "PENDING", definition["settings"]["max_attempts"]))
                for dep in task["dependencies"]:
                    store.db.execute("INSERT INTO edges VALUES(?,?)", (task_id, plan.id + ":" + dep))
            store.event(plan.id, None, dict(submitted=True, plan_integrity=definition["integrity"], estimate=plan.estimate))
        return plan.id
    finally:
        store.close()


def cancel_batch(batch_id, *, state_dir="outputs/v2_state"):
    store = _store(state_dir)
    try:
        with store.tx():
            row = store.batch(batch_id)
            if row["state"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                return row["state"]
            store.db.execute("UPDATE batches SET cancelled=1,state=?,updated=? WHERE id=?",
                             ("CANCELLING" if row["state"] == "RUNNING" else "CANCELLED", time.time(), batch_id))
            for task in store.db.execute("SELECT id FROM tasks WHERE batch=? AND state='PENDING'", (batch_id,)).fetchall():
                store.transition(task["id"], "CANCELLED", reason="user_cancel")
            store.event(batch_id, None, dict(cancel_requested=True))
        return store.batch(batch_id)["state"]
    finally:
        store.close()


def status_batch(batch_id, *, state_dir="outputs/v2_state", verify=True):
    from .v2_worker import artifacts_valid
    store = _store(state_dir)
    try:
        row = store.batch(batch_id)
        counts = {r["state"]: r["n"] for r in store.db.execute(
            "SELECT state,COUNT(*) n FROM tasks WHERE batch=? GROUP BY state", (batch_id,))}
        invalid = []
        if verify:
            for task in store.db.execute("SELECT id,artifacts FROM tasks WHERE batch=? AND state='SUCCEEDED'", (batch_id,)):
                if not artifacts_valid(json.loads(task["artifacts"] or "[]")):
                    invalid.append(task["id"])
        return dict(id=batch_id, state="INCOMPLETE" if invalid and row["state"] == "SUCCEEDED" else row["state"],
                    persisted_state=row["state"], cancelled=bool(row["cancelled"]), tasks=counts,
                    invalid_artifacts=invalid, metrics=json.loads(row["metrics"]),
                    attempts=[dict(r) for r in store.db.execute("SELECT a.* FROM attempts a JOIN tasks t ON t.id=a.task WHERE t.batch=? ORDER BY a.started", (batch_id,))],
                    failures=[dict(r) for r in store.db.execute("SELECT id,kind,state,error FROM tasks WHERE batch=? AND state='FAILED'", (batch_id,))])
    finally:
        store.close()


def run_batch(batch_id, *, state_dir="outputs/v2_state", reverse_order=False):
    from .v2_runner import execute_batch
    return execute_batch(batch_id, state_dir=state_dir, reverse_order=reverse_order, resume=False)


def resume_batch(batch_id, *, state_dir="outputs/v2_state", reverse_order=False):
    from .v2_runner import execute_batch
    return execute_batch(batch_id, state_dir=state_dir, reverse_order=reverse_order, resume=True)


def project_territory(*, tile_count, effective_pixel_fraction, union_directions, queries_per_tile,
                      directional_cache_fraction, workers, output_selection, hardware, model_path=None):
    """Explicit extrapolation only. Does not launch or certify a territory campaign."""
    if (type(tile_count) is not int or tile_count < 1 or type(union_directions) is not int
            or not 0 <= union_directions <= 144 or type(queries_per_tile) is not int or queries_per_tile < 1
            or type(workers) is not int or not 1 <= workers <= 4
            or not 0 <= effective_pixel_fraction <= 1 or not 0 <= directional_cache_fraction <= 1):
        raise ValueError("Invalid explicit territory profile")
    if output_selection != "scientific_only" or not isinstance(hardware, str) or not hardware:
        raise ValueError("Projection needs a named hardware profile and scientific_only output selection")
    model = load_model(model_path)
    c = model["coefficients"]
    efficiency = model["efficiency"].get(str(workers), .65)
    missing = tile_count * union_directions * (1-directional_cache_fraction)
    direction_efficiency=model.get("direction_efficiency",model["efficiency"]).get(str(workers),.65)
    work = c["direction_seconds"] * missing * effective_pixel_fraction / (workers*direction_efficiency)
    work += c["frame_seconds"] * tile_count * queries_per_tile / (workers*efficiency)
    retained = 1_800_000 * (12*missing + 2*tile_count*queries_per_tile)
    return dict(extrapolated=True, local_gate_does_not_validate_territory=True,
                profile=dict(tile_count=tile_count, native_pixels_per_tile=1_800_000,
                  effective_pixel_fraction=effective_pixel_fraction, union_directions=union_directions,
                  queries_per_tile=queries_per_tile, directional_cache_fraction=directional_cache_fraction,
                  final_result_hits_assumed=0, workers=workers, output_selection=output_selection, hardware=hardware),
                model_sha256=model.get("model_sha256"), measured_efficiency=efficiency if str(workers) in model["efficiency"] else None,
                indicative_compute_and_output_seconds=work, range_seconds=[work*.5,work*2],
                uncompressed_retained_bytes=retained, temporary_native_direction_bytes=workers*21_600_000,
                excluded_costs=["territory ingest/download/source validation and storage topology",
                                "cold JIT, remote queues, failure campaigns, media, statistics",
                                "different hardware; measured efficiency applies only to named calibration host"],
                caveat="Local coefficients extrapolated; compression/terrain/I/O contention are not validated at territory scale")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "submit", "run", "status", "cancel", "resume"))
    parser.add_argument("--requests", help="JSON object with requests plus optional batch settings")
    parser.add_argument("--batch")
    parser.add_argument("--state", default="outputs/v2_state")
    parser.add_argument("--reverse-order", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action in {"plan", "submit"}:
            if not args.requests:
                raise ValueError("--requests is required")
            value = json.loads(Path(args.requests).read_text())
            plan = plan_batch(value.pop("requests"), **value)
            result = plan.to_dict() if args.action == "plan" else dict(id=submit_batch(plan, state_dir=args.state))
        else:
            if not args.batch:
                raise ValueError("--batch is required")
            if args.action in {"run", "resume"}:
                result = (run_batch if args.action == "run" else resume_batch)(
                    args.batch, state_dir=args.state, reverse_order=args.reverse_order)
            elif args.action == "status":
                result = status_batch(args.batch, state_dir=args.state)
            else:
                result = dict(state=cancel_batch(args.batch, state_dir=args.state))
        print(json.dumps(result, indent=2))
        if isinstance(result, dict) and result.get("state") in {"FAILED", "INCOMPLETE"}:
            parser.exit(1)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f"V2 batch rejected: {exc}\n")


if __name__ == "__main__":
    main()
