"""One bounded local controller per batch, with durable attempts and recovery."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import time
import uuid

import psutil

from . import v1
from .spatial import digest_file
from .v1_cache import exclusive_lock, spatial_identity
from .v2 import _store, plan_from_dict, signature, status_batch
from .v2_worker import artifacts_valid, worker_entry


def _owned_kill(owner):
    """Only known batch-created children; PID reuse never grants ownership."""
    try:
        proc = psutil.Process(owner["pid"])
        if abs(proc.create_time() - owner["create_time"]) > .001:
            return False
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except psutil.TimeoutExpired:
            proc.kill()
        return True
    except psutil.Error:
        return False


def _reclaim(store, batch):
    previous = store.batch(batch)
    if previous["owner"]:
        owner = json.loads(previous["owner"])
        for child in owner.get("workers", []):
            path = Path(child["owner_file"])
            try:
                recorded = json.loads(path.read_text())
                if recorded["token"] == child["token"] and recorded["pid"] == child["pid"]:
                    _owned_kill(child)
            except (OSError, ValueError, KeyError):
                pass
        for child in owner.get("media", []):
            _owned_kill(child)
    with store.tx():
        for task in store.db.execute("SELECT * FROM tasks WHERE batch=? AND state='RUNNING'", (batch,)).fetchall():
            error = dict(category="stale_controller_or_worker", retryable=True,
                         error="Controller lock reclaimed; prior RUNNING attempt interrupted")
            target = "PENDING" if task["attempts"] < task["max_attempts"] else "FAILED"
            store.transition(task["id"], target, error=error, reason="stale_owner_recovery")


def _reconcile(store, batch, resume):
    invalid = set()
    changed_dependencies = set()
    for task in store.db.execute("SELECT * FROM tasks WHERE batch=?", (batch,)).fetchall():
        if task["state"] != "SUCCEEDED":
            changed_dependencies.add(task["id"])
        if task["artifacts"] is not None and not artifacts_valid(json.loads(task["artifacts"])):
            invalid.add(task["id"])
            # A corrupted final hit may now require directions previously skipped.
            if task["kind"] == "frame":
                invalid.update(r["dependency"] for r in store.db.execute("SELECT dependency FROM edges WHERE task=?", (task["id"],)))
    frontier = list(invalid | changed_dependencies)
    while frontier:
        task = frontier.pop()
        for row in store.db.execute("SELECT task FROM edges WHERE dependency=?", (task,)):
            if row["task"] not in invalid:
                invalid.add(row["task"])
                frontier.append(row["task"])
    with store.tx():
        for task_id in invalid:
            task = store.task(task_id)
            if task["state"] == "SUCCEEDED":
                if task["attempts"] >= task["max_attempts"]:
                    store.event(batch, task_id, dict(invalid_artifacts=True, attempt_ceiling_exhausted=True))
                    raise ValueError("Artifact repair exceeds fixed task attempt ceiling; submit a new batch")
                store.transition(task_id, "PENDING", reason="invalid_artifacts")
        if resume:
            store.db.execute("UPDATE batches SET cancelled=0 WHERE id=?", (batch,))
            for task in store.db.execute("SELECT * FROM tasks WHERE batch=? AND state IN ('FAILED','CANCELLED')", (batch,)).fetchall():
                if task["attempts"] < task["max_attempts"]:
                    store.transition(task["id"], "PENDING", reason="explicit_resume")


def _current_inputs(definition):
    for name, expected in definition["engine_code"].items():
        if digest_file(Path(__file__).with_name(name)) != expected:
            raise ValueError("V2 execution code changed; replan for a new immutable batch")
    catalogues = {directory: v1.index_sources(directory) for directory in definition["catalogues"]}
    signatures = {}
    for value in definition["requests"].values():
        plan = plan_from_dict(value)
        if v1._plan_key(plan.request, plan.grid, plan.tiles) != plan.key:
            raise ValueError("V1 scientific/execution identity changed; replan")
        for tile in plan.tiles:
            key, _, deps = spatial_identity(catalogues[plan.source_directory], tile.source)
            if key != tile.spatial_key:
                raise ValueError("DSM dependencies changed; immutable batch cannot silently change science")
            for rec in deps:
                signatures[rec["path"]] = signature(rec["path"])
                for aux in rec.get("auxiliary_files", []):
                    signatures[aux["path"]] = signature(aux["path"])
    return signatures


def _generated_bytes(roots, existing):
    total = 0
    for base in roots:
        if base.exists():
            for path in base.rglob("*"):
                if path.is_file():
                    try:
                        total += max(0, path.stat().st_size - existing.get(str(path), 0))
                    except OSError:
                        pass
    return total


def execute_batch(batch, *, state_dir, reverse_order=False, resume=False):
    store = _store(state_dir)
    started = time.perf_counter()
    slots = []
    ctx = mp.get_context("spawn")
    cancel = ctx.Event()
    owner = dict(pid=os.getpid(), create_time=psutil.Process().create_time(), token=uuid.uuid4().hex,
                 workers=[], media=[])
    metrics = dict(parent_peak_rss_bytes=0, workers_peak_rss_bytes=0, media_peak_rss_bytes=0,
                   peak_tree_rss_bytes=0, peak_new_disk_bytes=0, max_in_flight=0,
                   computed=0, reused=0, horizon_calls=0, final_result_hits=0,
                   input_inventory_calls=0, memory_sample_seconds=.02,
                   media_tracking="known worker-reported PIDs; sub-sample spikes may be missed",
                   monitoring_gaps="input admission sampled at start/end; continuous 20 ms loop starts after spawn")
    initial_rss=psutil.Process().memory_info().rss
    metrics["parent_peak_rss_bytes"]=metrics["peak_tree_rss_bytes"]=initial_rss
    try:
        with exclusive_lock(store.directory / f"{batch}.controller.lock"):
            row = store.batch(batch)
            definition = json.loads(row["definition"])["definition"]
            from .pipeline import fingerprint
            if definition.get("integrity") != fingerprint({k:v for k,v in definition.items() if k!="integrity"}):
                raise ValueError("Persistent immutable batch definition failed integrity validation")
            if row["cancelled"] and not resume:
                return status_batch(batch, state_dir=state_dir)
            _reclaim(store, batch)
            _reconcile(store, batch, resume)
            try:
                signatures = _current_inputs(definition)
                metrics["input_inventory_calls"] = len(definition["catalogues"])
                peak = definition["resources"]["estimated_peak_bytes"]
                if peak > psutil.virtual_memory().available - 512 * 1024**2:
                    raise MemoryError("Insufficient current host memory/headroom for requested workers")
                if definition["resources"]["estimated_peak_new_bytes"] > shutil.disk_usage(store.directory).free:
                    raise OSError("Insufficient disk for peak temporary and retained artifacts")
            except (ValueError, OSError, MemoryError) as exc:
                with store.tx():
                    for task in store.db.execute("SELECT id FROM tasks WHERE batch=? AND state='PENDING'", (batch,)).fetchall():
                        store.transition(task["id"], "FAILED", error=dict(category="preflight", retryable=False, error=repr(exc)))
                    store.set_batch(batch, "FAILED", metrics=metrics)
                    store.event(batch, None, dict(preflight_failure=repr(exc)))
                return status_batch(batch, state_dir=state_dir)
            roots = {store.directory}
            for plan in definition["requests"].values():
                roots.update([Path(plan["output_directory"]), Path(plan["cache_directory"])])
            roots = {p for p in roots if not any(p != q and p.is_relative_to(q) for q in roots)}
            existing = {str(p): p.stat().st_size for r in roots if r.exists() for p in r.rglob("*") if p.is_file()}
            with store.tx():
                store.set_batch(batch, "RUNNING", owner=owner, metrics=metrics)
            pending_count = store.db.execute("SELECT COUNT(*) FROM tasks WHERE batch=? AND state='PENDING'", (batch,)).fetchone()[0]
            if pending_count:
                def spawn_slot():
                    parent, child = ctx.Pipe()
                    token = uuid.uuid4().hex
                    owner_file = store.directory / "workers" / f"{token}.json"
                    proc = ctx.Process(target=worker_entry, args=(child, cancel, str(v1.ROOT), token, str(owner_file)))
                    proc.start()
                    child.close()
                    record = dict(pid=proc.pid, create_time=psutil.Process(proc.pid).create_time(),
                                  token=token, owner_file=str(owner_file))
                    owner["workers"].append(record)
                    slot = dict(process=proc, pipe=parent, ready=False, task=None, memory={}, record=record)
                    slots.append(slot)
                    with store.tx():
                        store.set_batch(batch, "RUNNING", owner=owner, metrics=metrics)
                    return slot
                for _ in range(min(definition["settings"]["workers"], pending_count)):
                    spawn_slot()
            last_disk = last_record = 0.
            fatal = None
            while slots:
                if store.batch(batch)["cancelled"]:
                    cancel.set()
                for slot in list(slots):
                    pipe, proc = slot["pipe"], slot["process"]
                    while pipe.poll():
                        try:
                            message = pipe.recv()
                        except (EOFError, OSError):
                            break
                        kind = message["type"]
                        if kind == "ready":
                            slot["ready"] = True
                        elif kind == "memory":
                            slot["memory"] = message["memory"]
                            known = {(c["pid"], c["create_time"]) for c in owner["media"]}
                            owner["media"].extend(c for c in message["media"] if (c["pid"], c["create_time"]) not in known)
                        elif kind == "direction":
                            event = message["value"]
                            for key in ("computed", "reused", "horizon_calls"):
                                metrics[key] += event[key]
                            with store.tx():
                                store.event(batch, slot["task"], dict(direction=event))
                        elif kind in {"result", "failure"}:
                            task = store.task(slot["task"])
                            with store.tx():
                                if kind == "result":
                                    result = message["result"]
                                    if not artifacts_valid(result["artifacts"]):
                                        error = dict(category="publication_validation", retryable=False, error="Artifacts failed controller verification")
                                        store.transition(task["id"], "FAILED", error=error)
                                    else:
                                        store.transition(task["id"], "SUCCEEDED", artifacts=result["artifacts"])
                                        store.event(batch, task["id"], dict(result_metrics=result["metrics"]))
                                        metrics["final_result_hits"] += result["metrics"].get("final_result_hits", 0)
                                        slot["memory"] = result["metrics"]
                                else:
                                    error = message["error"]
                                    target = ("CANCELLED" if error["category"] == "cancelled" else
                                              "PENDING" if error["retryable"] and task["attempts"] < task["max_attempts"] else "FAILED")
                                    store.transition(task["id"], target, error=error, reason="bounded_retry" if target == "PENDING" else None)
                            slot["task"] = None
                    if not proc.is_alive():
                        if slot["task"] is not None:
                            task = store.task(slot["task"])
                            with store.tx():
                                store.transition(task["id"], "PENDING" if task["attempts"] < task["max_attempts"] and not cancel.is_set() else
                                                 "CANCELLED" if cancel.is_set() else "FAILED",
                                                 error=dict(category="worker_lost", retryable=True, exitcode=proc.exitcode), reason="worker_termination")
                        pipe.close()
                        proc.join(timeout=.1)
                        slots.remove(slot)
                        if not cancel.is_set() and store.ready(batch, reverse=reverse_order) is not None:
                            spawn_slot()
                        continue
                    if slot["ready"] and slot["task"] is None and not cancel.is_set() and fatal is None:
                        task = store.ready(batch, reverse=reverse_order)
                        if task is not None:
                            try:
                                changed = any(signature(path) != sig for path, sig in signatures.items())
                            except OSError:
                                changed = True
                            if changed:
                                fatal = "Inputs changed during execution"
                                cancel.set()
                                break
                            payload = json.loads(task["payload"])
                            names = payload.get("consumers", [payload["request"]] if "request" in payload else list(definition["requests"]))
                            plans = {n: definition["requests"][n] for n in names}
                            with store.tx():
                                store.transition(task["id"], "RUNNING", owner=slot["record"])
                            slot["task"] = task["id"]
                            pipe.send(dict(kind=task["kind"], payload=payload, plans=plans,
                                           batch=batch, store_directory=str(store.directory)))
                parent_rss = psutil.Process().memory_info().rss
                worker_rss = media_rss = 0
                for slot in slots:
                    try:
                        worker_rss += psutil.Process(slot["process"].pid).memory_info().rss
                    except psutil.Error:
                        pass
                for child in owner["media"]:
                    try:
                        proc = psutil.Process(child["pid"])
                        if abs(proc.create_time() - child["create_time"]) <= .001:
                            media_rss += proc.memory_info().rss
                    except psutil.Error:
                        pass
                tree = parent_rss + worker_rss + media_rss
                for key, value in (("parent_peak_rss_bytes", parent_rss), ("workers_peak_rss_bytes", worker_rss),
                                  ("media_peak_rss_bytes", media_rss), ("peak_tree_rss_bytes", tree)):
                    metrics[key] = max(metrics[key], value)
                active = sum(s["task"] is not None for s in slots)
                metrics["max_in_flight"] = max(metrics["max_in_flight"], active)
                now = time.perf_counter()
                if now - last_disk >= 1:
                    metrics["peak_new_disk_bytes"] = max(metrics["peak_new_disk_bytes"], _generated_bytes(roots, existing))
                    last_disk = now
                if tree > definition["resources"]["memory_budget_bytes"] or metrics["peak_new_disk_bytes"] > definition["settings"]["artifact_budget_bytes"]:
                    fatal = "Measured resource budget exceeded"
                    cancel.set()
                    for slot in slots:
                        slot["process"].terminate()
                        slot["process"].join(timeout=2)
                        if slot["process"].is_alive():
                            slot["process"].kill()
                if now - last_record >= 1:
                    with store.tx():
                        store.set_batch(batch, "CANCELLING" if cancel.is_set() else "RUNNING", owner=owner, metrics=metrics)
                    last_record = now
                if active == 0 and (cancel.is_set() or store.ready(batch, reverse=reverse_order) is None):
                    break
                time.sleep(.02)
            # Shutdown owns these processes only, never a process-name/global kill.
            for slot in slots:
                if slot["process"].is_alive():
                    slot["pipe"].send(None)
            for slot in slots:
                slot["process"].join(timeout=2)
                if slot["process"].is_alive():
                    _owned_kill(slot["record"])
            with store.tx():
                if cancel.is_set():
                    for task in store.db.execute("SELECT * FROM tasks WHERE batch=? AND state IN ('PENDING','RUNNING')", (batch,)).fetchall():
                        store.transition(task["id"], "FAILED" if fatal else "CANCELLED",
                                         error=dict(category="resource_or_input" if fatal else "cancelled", retryable=False, error=fatal))
                counts = {r["state"]: r["n"] for r in store.db.execute("SELECT state,COUNT(*) n FROM tasks WHERE batch=? GROUP BY state", (batch,))}
                all_valid = all(artifacts_valid(json.loads(r["artifacts"] or "[]")) for r in store.db.execute(
                    "SELECT artifacts FROM tasks WHERE batch=? AND state='SUCCEEDED'", (batch,)))
                state = "FAILED" if fatal or counts.get("FAILED") or not all_valid else "CANCELLED" if cancel.is_set() else \
                        "SUCCEEDED" if set(counts) == {"SUCCEEDED"} else "FAILED"
                metrics["run_wall_seconds"] = time.perf_counter() - started
                end_rss=psutil.Process().memory_info().rss
                metrics["parent_peak_rss_bytes"]=max(metrics["parent_peak_rss_bytes"],end_rss)
                metrics["peak_tree_rss_bytes"]=max(metrics["peak_tree_rss_bytes"],end_rss)
                metrics["peak_new_disk_bytes"] = max(metrics["peak_new_disk_bytes"], _generated_bytes(roots, existing))
                store.set_batch(batch, state, metrics=metrics)
                store.event(batch, None, dict(finished=state, metrics=metrics, fatal=fatal))
    finally:
        for slot in slots:
            if slot["process"].is_alive():
                slot["process"].terminate()
                slot["process"].join(timeout=2)
                if slot["process"].is_alive():
                    slot["process"].kill()
            slot["pipe"].close()
        store.close()
    return status_batch(batch, state_dir=state_dir)
