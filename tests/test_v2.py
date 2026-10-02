"""V2 public scheduling, durable recovery, isolation and scientific regressions."""
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src import v1, v2
from src.v1_cache import entry_paths
from src.v2_state import Store
from src.v2_worker import artifacts_valid, classify_failure, read_logical_window


@pytest.fixture
def batch_scene(tmp_path, monkeypatch):
    monkeypatch.setattr(v1, "ROOT", tmp_path)
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    rng = np.random.default_rng(20261003)
    values = rng.uniform(0, 4, (32, 70)).astype(np.float32)
    values[9:20, 15:24] = 40
    values[0, 0] = -9999
    for c in (0, 35):
        with rasterio.open(raw / f"tile_{c}.tif", "w", driver="GTiff", width=35, height=32,
                           count=1, dtype="float32", crs="EPSG:2326", nodata=-9999,
                           transform=from_origin(800000 + c * .5, 820000, .5, .5)) as ds:
            ds.write(values[:, c:c+35], 1)
    return raw


def requests(raw, name="a", **kwargs):
    return dict(id=name, dsm_dir=str(raw), tile="tile_0.tif",
                instants=["2026-01-07T14:31:27+08:00"], output_dir=f"outputs/{name}", **kwargs)


def frame_arrays(directory, index=0):
    frame = json.loads((directory / "result_index.json").read_text())["frames"][index]
    with rasterio.open(frame["raster"]) as ds, rasterio.open(frame["quality_raster"]) as qs:
        return ds.read(1), qs.read(1), ds.transform


def child_controller(root, batch, action="run"):
    script = root / f"{action}_{batch[:10]}.py"
    script.write_text("from pathlib import Path\nfrom src import v1,v2\n"
        f"v1.ROOT=Path({str(root)!r})\n"
        "if __name__=='__main__':\n"
        f" print(v2.{action}_batch({batch!r},state_dir={str(root/'outputs/state')!r}))\n")
    env = dict(os.environ, PYTHONPATH=str(Path(v2.__file__).resolve().parents[1]))
    return subprocess.Popen([sys.executable, str(script)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def wait_for(predicate, timeout=25):
    start = time.monotonic()
    while time.monotonic()-start < timeout:
        result = predicate()
        if result:
            return result
        time.sleep(.01)
    raise AssertionError("Owned test process did not reach injection point")


def test_plan_inventory_union_no_writes_and_immutable(batch_scene):
    before = set(v1.ROOT.rglob("*"))
    with patch.object(v1, "index_sources", wraps=v1.index_sources) as inv, \
            patch("src.v1_cache.pixel_centred_horizon", side_effect=AssertionError("planning computed")):
        plan = v2.plan_batch([requests(batch_scene), requests(batch_scene, "b")])
    assert inv.call_count == 1
    assert set(v1.ROOT.rglob("*")) == before
    assert sum(t["kind"] == "horizon" for t in plan.definition["tasks"]) == 1
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    assert v2.submit_batch(plan, state_dir="outputs/state") == batch
    assert v2.status_batch(batch, state_dir="outputs/state")["state"] == "QUEUED"
    import sqlite3
    store=Store(v1.ROOT/"outputs/state")
    with pytest.raises(sqlite3.IntegrityError,match="immutable"):
        store.db.execute("UPDATE tasks SET payload='{}' WHERE batch=?",(batch,))
    store.close()
    plan.definition["settings"]["workers"] = 4
    with pytest.raises(ValueError, match="modified"):
        v2.submit_batch(plan, state_dir="outputs/state")


def test_overlap_two_workers_quality_logical_and_v1(batch_scene):
    a = requests(batch_scene)
    b = requests(batch_scene, "b", crop=(3, 5, 17, 13), jpg=True)
    b["instants"] = ["2026-01-08T14:31:27+08:00", "2026-01-07T14:31:27+08:00"]
    c = requests(batch_scene, "c")
    c.pop("tile"); c["tiles"] = ["tile_0.tif", "tile_35.tif"]
    plan = v2.plan_batch([a,b,c], workers=2, statistics=True, logical_mosaic=True)
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    result = v2.run_batch(batch, state_dir="outputs/state", reverse_order=True)
    assert result["state"] == "SUCCEEDED", result["failures"]
    assert result["metrics"]["horizon_calls"] == 2
    assert result["metrics"]["max_in_flight"] <= 2
    solo, flags, trans = frame_arrays(v1.ROOT / "outputs/a")
    combined = frame_arrays(v1.ROOT / "outputs/c")
    odd = frame_arrays(v1.ROOT / "outputs/b", 1)
    assert np.array_equal(solo, combined[0][:,:35])
    assert np.array_equal(flags, combined[1][:,:35])
    assert np.array_equal(solo[5:18,3:20], odd[0])
    assert np.array_equal(flags[5:18,3:20], odd[1])
    legacy = v1.run_shade(v1.plan_shade(dsm_dir=batch_scene, tile="tile_0.tif",
                         instants=a["instants"], output_dir="outputs/v1_baseline"))
    for target, path in zip((solo,flags), (legacy.frames[0]["raster"], legacy.frames[0]["quality_raster"])):
        with rasterio.open(path) as ds:
            assert np.array_equal(target, ds.read(1))
    mosaic = v1.ROOT / "outputs/state" / f"{batch}.logical_mosaic.json"
    view = read_logical_window(mosaic, utc_time=plan.definition["requests"]["a"]["request"]["instants"][0]["utc"],
                               bounds=(800001.5,819991,800010,819997.5))
    assert np.array_equal(view[0],solo[5:18,3:20])
    assert np.array_equal(view[1],flags[5:18,3:20])
    assert (v1.ROOT/"outputs/a/statistics.json").exists()


def test_transitions_cancel_pending_and_fresh_process(batch_scene):
    plan = v2.plan_batch([requests(batch_scene)])
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    store = Store(v1.ROOT / "outputs/state")
    task = store.db.execute("SELECT id FROM tasks WHERE batch=? LIMIT 1", (batch,)).fetchone()[0]
    with pytest.raises(ValueError, match="Illegal"):
        with store.tx(): store.transition(task, "SUCCEEDED")
    store.close()
    assert v2.cancel_batch(batch, state_dir="outputs/state") == "CANCELLED"
    proc = child_controller(v1.ROOT, batch, "resume")
    out,err = proc.communicate(timeout=30)
    assert proc.returncode == 0,err.decode()
    assert v2.status_batch(batch, state_dir="outputs/state")["state"] == "SUCCEEDED"


def test_corrupt_output_and_cache_recover_and_attempts_preserved(batch_scene):
    plan = v2.plan_batch([requests(batch_scene)])
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    first = v2.run_batch(batch, state_dir="outputs/state")
    assert first["state"] == "SUCCEEDED"
    source = v2.plan_from_dict(plan.definition["requests"]["a"]).tiles[0]
    cache = plan.definition["requests"]["a"]["cache_directory"]
    path,_ = entry_paths(cache,source.spatial_key,source.directions[0])
    path.write_bytes(b"corrupt")
    shade = next((v1.ROOT/"outputs/a/shade").glob("*.tif"))
    shade.write_bytes(b"partial")
    assert v2.status_batch(batch, state_dir="outputs/state")["state"] == "INCOMPLETE"
    recovered = v2.resume_batch(batch, state_dir="outputs/state")
    assert recovered["state"] == "SUCCEEDED"
    assert recovered["metrics"]["horizon_calls"] == 1
    assert max(a["number"] for a in recovered["attempts"]) == 2


def test_unavailable_input_truthful_no_infinite_retry(batch_scene):
    plan = v2.plan_batch([requests(batch_scene)])
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    (batch_scene/"tile_0.tif").unlink()
    result = v2.run_batch(batch, state_dir="outputs/state")
    assert result["state"] == "FAILED"
    assert result["metrics"]["horizon_calls"] == 0
    assert all(json.loads(f["error"])["category"] == "preflight" for f in result["failures"])


def test_media_only_retry_no_horizons(batch_scene, monkeypatch):
    plan = v2.plan_batch([requests(batch_scene, mp4=True)])
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    monkeypatch.setenv("IMAGEIO_FFMPEG_EXE", "/not/a/real/encoder")
    failed = v2.run_batch(batch, state_dir="outputs/state")
    assert failed["state"] == "FAILED" and failed["metrics"]["computed"] == 1
    assert all(f["kind"] == "media" for f in failed["failures"])
    from src.spatial import digest_file
    scientific={str(p):digest_file(p) for base in ("shade","quality") for p in (v1.ROOT/"outputs/a"/base).glob("*.tif")}
    monkeypatch.delenv("IMAGEIO_FFMPEG_EXE")
    passed = v2.resume_batch(batch, state_dir="outputs/state")
    assert passed["state"] == "SUCCEEDED"
    assert passed["metrics"]["horizon_calls"] == 0
    assert all(digest_file(p)==sha for p,sha in scientific.items())


def test_owned_controller_and_worker_kills_resume(batch_scene):
    req = requests(batch_scene)
    req["instants"] = [f"2026-01-07T14:31:{i:02d}+08:00" for i in range(40)]
    plan = v2.plan_batch([req])
    batch = v2.submit_batch(plan, state_dir="outputs/state")
    proc = child_controller(v1.ROOT, batch)
    store = Store(v1.ROOT / "outputs/state")
    def running_worker():
        row=store.db.execute("SELECT owner FROM attempts WHERE state='RUNNING' LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None
    owned=wait_for(running_worker)
    os.kill(owned["pid"],signal.SIGTERM)
    wait_for(lambda: store.db.execute("SELECT COUNT(*) FROM events WHERE event LIKE '%worker_termination%'").fetchone()[0])
    wait_for(lambda: store.db.execute("SELECT COUNT(*) FROM tasks WHERE state='SUCCEEDED'").fetchone()[0])
    wait_for(lambda: store.db.execute("SELECT COUNT(*) FROM tasks WHERE state='RUNNING'").fetchone()[0])
    proc.terminate(); proc.communicate(timeout=10)
    store.close()
    recovery=child_controller(v1.ROOT,batch,"resume")
    out,err=recovery.communicate(timeout=40)
    assert recovery.returncode == 0,err.decode()
    result=v2.status_batch(batch,state_dir="outputs/state")
    assert result["state"] == "SUCCEEDED"
    assert any("worker_lost" in (a["error"] or "") for a in result["attempts"])
    assert any("stale_controller" in (a["error"] or "") for a in result["attempts"])
    assert result["metrics"]["horizon_calls"] == 0


def test_resource_rejection_and_failure_classification(batch_scene):
    with pytest.raises(ValueError,match="memory"):
        v2.plan_batch([requests(batch_scene)],workers=2,memory_budget_mb=512)
    with pytest.raises(ValueError,match="workers"):
        v2.plan_batch([requests(batch_scene)],workers=5)
    with pytest.raises(ValueError,match="artifact"):
        v2.plan_batch([requests(batch_scene)],artifact_budget_bytes=1)
    import errno
    assert classify_failure(OSError(errno.ENOSPC,"quota"))["retryable"] is False
    assert classify_failure(OSError(errno.EIO,"temporary I/O"))["retryable"] is True
    assert not artifacts_valid([dict(path="/unavailable",bytes=5,sha256="bad")])


def test_cooperative_active_cancel_and_unrelated_sentinel(batch_scene):
    req = requests(batch_scene)
    req["instants"] = [f"2026-01-07T14:31:{i:02d}+08:00" for i in range(50)]
    plan = v2.plan_batch([req])
    batch = v2.submit_batch(plan,state_dir="outputs/state")
    sentinel = subprocess.Popen([sys.executable,"-c","import time; time.sleep(20)"])
    proc = child_controller(v1.ROOT,batch)
    store = Store(v1.ROOT/"outputs/state")
    try:
        wait_for(lambda: store.db.execute("SELECT COUNT(*) FROM tasks WHERE state='RUNNING'").fetchone()[0])
        assert v2.cancel_batch(batch,state_dir="outputs/state") == "CANCELLING"
        proc.communicate(timeout=30)
        assert v2.status_batch(batch,state_dir="outputs/state")["state"] == "CANCELLED"
        assert sentinel.poll() is None
        assert v2.resume_batch(batch,state_dir="outputs/state")["state"] == "SUCCEEDED"
    finally:
        store.close()
        sentinel.terminate(); sentinel.wait(timeout=5)
        if proc.poll() is None:
            proc.terminate(); proc.wait(timeout=5)


def test_partial_publication_process_exit_reconciles(batch_scene):
    plan=v2.plan_batch([requests(batch_scene)])
    batch=v2.submit_batch(plan,state_dir="outputs/state")
    assert v2.run_batch(batch,state_dir="outputs/state")["state"] == "SUCCEEDED"
    store=Store(v1.ROOT/"outputs/state")
    task=store.db.execute("SELECT id FROM tasks WHERE kind='frame' LIMIT 1").fetchone()[0]
    with store.tx():
        store.transition(task,"PENDING",reason="invalid_artifacts")
        store.transition(task,"RUNNING",owner={"test":"publication child"})
    value=plan.definition["requests"]["a"]
    script=v1.ROOT/"interrupt_publication.py"
    script.write_text("import os,json\nfrom src import v1,v2\nfrom pathlib import Path\n"
        f"v1.ROOT=Path({str(v1.ROOT)!r})\n"
        f"p=v2.plan_from_dict(json.loads({json.dumps(value)!r}))\n"
        "orig=os.replace\ndef stop(a,b):\n"
        " if '/shade/' in str(b) and str(b).endswith('.tif'): orig(a,b); os._exit(41)\n"
        " return orig(a,b)\nos.replace=stop\n"
        "v1._compose_frame(p,0,{t.spatial_key:0. for t in p.tiles})\n")
    env=dict(os.environ,PYTHONPATH=str(Path(v2.__file__).resolve().parents[1]))
    child=subprocess.run([sys.executable,str(script)],env=env,capture_output=True,timeout=20)
    assert child.returncode == 41,child.stderr.decode()
    assert v1._valid_frame(v2.plan_from_dict(value),0) is None
    store.close()
    result=v2.resume_batch(batch,state_dir="outputs/state")
    assert result["state"] == "SUCCEEDED"
    assert result["metrics"]["horizon_calls"] == 0


def test_queue_fourfold_fixed_concurrency_no_array_payloads(batch_scene):
    peaks=[]
    for n in (8,32):
        plan=v2.plan_batch([requests(batch_scene,f"queue{n}_{i}",crop=(3,5,4,4)) for i in range(n)])
        assert not any(isinstance(v,np.ndarray) for t in plan.definition["tasks"] for v in t["payload"].values())
        batch=v2.submit_batch(plan,state_dir="outputs/state")
        result=v2.run_batch(batch,state_dir="outputs/state")
        assert result["state"] == "SUCCEEDED"
        assert result["metrics"]["max_in_flight"] == 1
        peaks.append(result["metrics"]["parent_peak_rss_bytes"])
    # Metadata can grow; no native scientific array is retained per queued task.
    assert peaks[1]-peaks[0] < 64*1024**2


def test_quota_and_write_failure_no_false_science_success(batch_scene):
    import errno
    from collections import OrderedDict
    from threading import Event
    from src.v2_worker import execute_task
    plan=v2.plan_batch([requests(batch_scene)])
    batch=v2.submit_batch(plan,state_dir="outputs/state")
    assert v2.run_batch(batch,state_dir="outputs/state")["state"] == "SUCCEEDED"
    value=plan.definition["requests"]["a"]
    p=v2.plan_from_dict(value)
    shade,quality,status=v1._frame_paths(Path(p.output_directory),p.request.instants[0])
    status.unlink()
    with patch.object(v1.os,"replace",side_effect=OSError(errno.ENOSPC,"simulated quota")):
        with pytest.raises(OSError):
            execute_task("frame",dict(request="a",index=0),{"a":value},batch,
                         str(v1.ROOT/"outputs/state"),Event(),lambda v: None,OrderedDict())
    assert v1._valid_frame(p,0) is None
    assert v2.status_batch(batch,state_dir="outputs/state")["state"] == "INCOMPLETE"
    assert v2.resume_batch(batch,state_dir="outputs/state")["state"] == "SUCCEEDED"


def test_competing_writer_waits_and_reuses_committed_entry(batch_scene):
    req=requests(batch_scene)
    req["cache_dir"]="data/processed/shade_v1/v2_default"
    p=v1.plan_shade(**{k:v for k,v in req.items() if k!='id'})
    v1.run_shade(p)
    req["output_dir"]="outputs/contending"
    plan=v2.plan_batch([req])
    batch=v2.submit_batch(plan,state_dir="outputs/state")
    tile=v2.plan_from_dict(plan.definition["requests"]["a"]).tiles[0]
    lock=Path(plan.definition["requests"]["a"]["cache_directory"])/tile.spatial_key/".writer.lock"
    script=v1.ROOT/"cache_owner.py"
    script.write_text("import time\nfrom src.v1_cache import exclusive_lock\n"
         f"with exclusive_lock({str(lock)!r}):\n print('owned',flush=True)\n time.sleep(2)\n")
    env=dict(os.environ,PYTHONPATH=str(Path(v2.__file__).resolve().parents[1]))
    proc=subprocess.Popen([sys.executable,str(script)],env=env,stdout=subprocess.PIPE)
    assert proc.stdout.readline().strip()==b"owned"
    try:
        result=v2.run_batch(batch,state_dir="outputs/state")
        assert result["state"] == "SUCCEEDED"
        assert result["metrics"]["reused"] == 1 and result["metrics"]["horizon_calls"] == 0
    finally:
        proc.wait(timeout=10)


def test_nan_nodata_strict_metadata_and_valid_missing_target(batch_scene):
    path=batch_scene/"tile_0.tif"
    with rasterio.open(path,"r+") as ds:
        values=ds.read(1); values[values==-9999]=np.nan
        ds.nodata=float("nan"); ds.write(values,1)
    plan=v2.plan_batch([requests(batch_scene)])
    json.dumps(plan.to_dict(),allow_nan=False)
    batch=v2.submit_batch(plan,state_dir="outputs/state")
    result=v2.run_batch(batch,state_dir="outputs/state")
    assert result["state"] == "SUCCEEDED",result["failures"]
    labels,quality,_=frame_arrays(v1.ROOT/"outputs/a")
    assert labels[0,0]==255 and quality[0,0]==1


def test_worker_losses_exhaust_fixed_attempt_ceiling(batch_scene):
    plan=v2.plan_batch([requests(batch_scene)],max_attempts=2)
    batch=v2.submit_batch(plan,state_dir="outputs/state")
    proc=child_controller(v1.ROOT,batch)
    store=Store(v1.ROOT/"outputs/state")
    seen=set()
    try:
        for _ in range(2):
            def next_owner():
                row=store.db.execute("SELECT owner FROM attempts WHERE state='RUNNING' ORDER BY started DESC LIMIT 1").fetchone()
                if row:
                    owner=json.loads(row[0])
                    if owner['pid'] not in seen: return owner
            owner=wait_for(next_owner); seen.add(owner['pid']); os.kill(owner['pid'],signal.SIGTERM)
        proc.communicate(timeout=30)
        result=v2.status_batch(batch,state_dir="outputs/state")
        assert result["state"] == "FAILED"
        assert len(result["attempts"])==2
        assert v2.resume_batch(batch,state_dir="outputs/state")["state"] == "FAILED"
    finally:
        store.close()
        if proc.poll() is None: proc.terminate();proc.wait(timeout=5)
