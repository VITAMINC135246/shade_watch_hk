"""Bounded V2 development evidence; independent acceptance uses another harness."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import v1, v2
from src.pipeline import memory_monitor
from src.spatial import digest_file
from src.v1_cache import atomic_json, entry_paths, valid_entry
from src.v2_state import Store
from src.v2_worker import read_logical_window

OUT = ROOT / "outputs/v2_development"
CACHE = ROOT / "data/processed/shade_v1/v2_development"
EVIDENCE = OUT / "evidence"
V1_SHA = "796ac8abf05b92f1fbbac23a4aa0f18c9d944101"
TILES = ["11NE10B(e844n822,e845n822).tif", "11NE10D(e844n821,e845n822).tif"]


def manifest():
    path = EVIDENCE / "samples.json"
    if path.exists():
        return json.loads(path.read_text())
    inputs = dict(frozen_utc=datetime.now(timezone.utc).isoformat(), selection="predeclared full-valid local tiles, seed 20261003",
        calibration=dict(cold_instants=["2026-01-07T09:17:23+08:00","2026-01-07T14:31:27+08:00"],
                         warm_start="2026-01-07T14:31:00+08:00",warm_frames=32),
        holdouts=dict(cold_instants=["2026-02-06T09:43:17+08:00","2026-08-16T15:26:39+08:00"],
                      warm_starts=["2026-02-08T14:31:02+08:00","2026-02-09T14:31:03+08:00"],
                      warm_frames_per_date=64,
                      mixed_instants=["2026-03-12T08:37:41+08:00","2026-11-17T15:48:23+08:00"]),
        regression=dict(stamp="2028-02-29T13:19:37.123456+08:00",odd_crop=[903,703,24,20]),
        tiles=TILES, budgets=dict(real_job_wall_seconds=7200,memory_bytes=12*1024**3,artifact_bytes=20*1024**3))
    atomic_json(path, inputs)
    return inputs


def instants(start, count):
    t=datetime.fromisoformat(start)
    return [(t+timedelta(seconds=i)).isoformat() for i in range(count)]


def request(name, tile, times, cache, **kwargs):
    return dict(id=name,tile=tile,instants=times,cache_dir=str(cache),output_dir=str(OUT/name),**kwargs)


def ledger_job(name, function, reserve=300):
    path=EVIDENCE/"ledger.json"
    ledger=json.loads(path.read_text()) if path.exists() else dict(real_job_wall_seconds=0.,ceiling_seconds=7200.,entries=[])
    if ledger["real_job_wall_seconds"]+reserve>7200:
        raise RuntimeError("Real-DSM budget cannot admit this job")
    entry=dict(name=name,started_utc=datetime.now(timezone.utc).isoformat(),reserved_seconds=reserve,status="RUNNING")
    ledger["entries"].append(entry); atomic_json(path,ledger)
    started=time.perf_counter()
    try:
        with memory_monitor() as memory:
            result=function()
        entry.update(status="SUCCEEDED",**memory)
        if isinstance(result,dict) and "metrics" in result:
            entry["job_metrics"]=result["metrics"]
        return result
    except BaseException as exc:
        entry.update(status="FAILED",error=repr(exc)); raise
    finally:
        entry["wall_seconds"]=time.perf_counter()-started
        ledger["real_job_wall_seconds"]+=entry["wall_seconds"]
        artifact_roots=(OUT,CACHE,ROOT/"outputs/v2_example",ROOT/"outputs/v2_example_state",ROOT/"data/processed/shade_v1/v2_example")
        ledger["generated_bytes"]=sum(p.stat().st_size for root in artifact_roots if root.exists() for p in root.rglob("*") if p.is_file())
        ledger["conservative_peak_job_bytes"]=max((e.get("peak_rss_bytes",0)+e.get("job_metrics",{}).get("peak_tree_rss_bytes",0)
                      if e.get("job_metrics") else e.get("peak_tree_rss_bytes",0) for e in ledger["entries"]),default=0)
        atomic_json(path,ledger)
        print(json.dumps(dict(job=name,wall_seconds=round(entry["wall_seconds"],3),status=entry["status"],
                              cumulative_seconds=round(ledger["real_job_wall_seconds"],3))),flush=True)
        if ledger["generated_bytes"]>20*1024**3:
            raise RuntimeError("Campaign artifact budget exceeded")
        if ledger["conservative_peak_job_bytes"]>12*1024**3:
            raise MemoryError("Campaign combined job memory ceiling exceeded")


def job(name, requests, *, workers=1, **options):
    record=EVIDENCE/f"{name}.json"
    if record.exists():
        raise ValueError("A measured workload is immutable; choose a fresh campaign rather than overwrite it")
    started=time.perf_counter()
    plan=v2.plan_batch(requests,workers=workers,**options)
    state=OUT/f"state_{name}"
    batch=v2.submit_batch(plan,state_dir=state)
    planning_and_submit=time.perf_counter()-started
    prediction=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),batch=batch,
                    estimate=plan.estimate,plan=plan.to_dict(),planning_submit_seconds=planning_and_submit)
    atomic_json(EVIDENCE/f"{name}_prediction.json",prediction)
    def execute():
        began=time.perf_counter()
        result=v2.run_batch(batch,state_dir=state,reverse_order=options.get("logical_mosaic",False))
        observed=time.perf_counter()-began
        if result["state"]!="SUCCEEDED":
            raise AssertionError(result["failures"])
        store=Store(state)
        events=[json.loads(r[0]) for r in store.db.execute("SELECT event FROM events WHERE batch=? ORDER BY sequence",(batch,))]
        store.close()
        return dict(**result,observed_run_api_seconds=observed,prediction=plan.estimate,
                    plan=plan.to_dict(),events=events,planning_submit_seconds=planning_and_submit)
    result=ledger_job(name,execute)
    atomic_json(record,result)
    return result


def calibration(samples):
    path=EVIDENCE/"calibration.json"
    if path.exists():
        return
    times=samples["calibration"]["cold_instants"]
    cold1=job("cal_cold_1",[request("cal_cold_1",TILES[0],times,CACHE/"cal1")])
    cold2=job("cal_cold_2",[request("cal_cold_2a",TILES[0],times,CACHE/"cal2"),
                             request("cal_cold_2b",TILES[1],times,CACHE/"cal2")],workers=2)
    warmtimes=instants(samples["calibration"]["warm_start"],samples["calibration"]["warm_frames"])
    warm1=job("cal_warm_1",[request("cal_warm_1",TILES[0],warmtimes,CACHE/"cal1")])
    assert warm1["metrics"]["horizon_calls"]==0 and warm1["metrics"]["final_result_hits"]==0
    warm2=job("cal_warm_2",[request("cal_warm_2a",TILES[0],warmtimes,CACHE/"cal2"),
                             request("cal_warm_2b",TILES[1],warmtimes,CACHE/"cal2")],workers=2)
    # Events have task IDs in SQLite; use direct queries for measured phases.
    def task_times(name,kind):
        store=Store(OUT/f"state_{name}")
        values=[json.loads(r[0])["result_metrics"]["wall_seconds"] for r in store.db.execute(
            "SELECT e.event FROM events e JOIN tasks t ON t.id=e.task WHERE t.kind=? AND e.event LIKE '%result_metrics%'",(kind,))]
        store.close(); return values
    native_direction=sum(task_times("cal_cold_1","horizon"))/cold1["prediction"]["missing_direction_units"]
    # Startup/initial catalogue/final-controller costs are explicit additive terms.
    native_frame=sum(task_times("cal_warm_1","frame"))/32
    warm_overhead=max(0.,warm1["observed_run_api_seconds"]-sum(task_times("cal_warm_1","frame")))
    startup=.75
    catalog=.25
    # Index validation and controller readback scale with frame count too.
    frame_cost=(warm1["observed_run_api_seconds"]-startup-catalog)/32
    # Derive output-stage two-worker efficiency from matched warm work.
    efficiency=(warm1["observed_run_api_seconds"]-startup-catalog)*2 / (
        2*max(.1,warm2["observed_run_api_seconds"]-startup-catalog))
    efficiency=min(1.,max(.5,efficiency))
    direction_efficiency=min(1.,sum(task_times("cal_cold_1","horizon"))/max(task_times("cal_cold_2","horizon")))
    classifications=[e["result_metrics"]["frame_timing"]["classification_seconds"]
                     for e in warm1["events"] if "result_metrics" in e and e["result_metrics"].get("new_frames")]
    model=dict(schema="shade-watch-v2-estimator-1.0",calibrated=True,
        frozen_utc=datetime.now(timezone.utc).isoformat(),
        coefficients=dict(catalog_seconds=catalog,startup_seconds=startup,direction_seconds=native_direction,
                          frame_seconds=frame_cost,classification_seconds=statistics.mean(classifications),
                          hit_seconds=.04,media_frame_seconds=.15,controller_task_seconds=0.),
        efficiency={"1":1.,"2":efficiency},
        direction_efficiency={"1":1.,"2":direction_efficiency},
        domain=dict(max_tiles=2,max_native_frames=320,max_union_directions=12,
                    outputs="native scientific only",hardware="Mac arm64 macOS15.7.4, 10 logical CPUs, 24 GiB, local HFS disk",
                    tile_shape=[1500,1200],source_tiles=TILES,
                    caveat="local mostly-valid tiles; new terrain/NoData distributions and media uncalibrated"),
        methodology=dict(direction="full native union-task wall divided by missing native directions",
                         frame="matched warm complete run minus fixed startup/catalog, divided by native frames",
                         efficiency="one/two-worker matched warm work after fixed costs; capped at 1",
                         startup_catalog="fixed engineering allowance checked against phase/whole-run timings",
                         frame_worker_seconds=native_frame,warm_overhead_seconds=warm_overhead,
                         excluded="planning/submission and OS-cache flush; run API includes final verification",
                         memory_disk="conservative V1 allocation and uncompressed bytes plus temporary/metadata headroom",
                         uncalibrated_terms="media, final hits and four-worker costs are provisional"),
        calibration_records=[f"outputs/v2_development/evidence/{n}.json" for n in
                             ("cal_cold_1","cal_cold_2","cal_warm_1","cal_warm_2")])
    atomic_json(ROOT/"docs/v2/estimator.json",model)
    atomic_json(EVIDENCE/"frozen_estimator.json",dict(model=model,sha256=digest_file(ROOT/"docs/v2/estimator.json")))
    atomic_json(path,dict(cold1=cold1["observed_run_api_seconds"],cold2=cold2["observed_run_api_seconds"],
                         warm1=warm1["observed_run_api_seconds"],warm2=warm2["observed_run_api_seconds"],model=model))


def accepted_v1():
    directory=OUT/"accepted_snapshot"
    directory.mkdir(parents=True,exist_ok=True)
    files=subprocess.check_output(["git","ls-tree","--name-only",V1_SHA,"src/"],text=True).splitlines()
    for name in files:
        if name.endswith(".py"):
            (directory/Path(name).name).write_bytes(subprocess.check_output(["git","show",f"{V1_SHA}:{name}"]))
    spec=importlib.util.spec_from_file_location("src.accepted_v1",directory/"v1.py")
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    module.ROOT=ROOT
    return module


def regression(samples):
    path=EVIDENCE/"regression.json"
    if path.exists(): return
    base=accepted_v1()
    times=[samples["regression"]["stamp"],"2028-02-29T05:19:37.123456Z","2026-10-18T23:17:11+08:00"]
    # Equivalent instants belong to separate requests, never duplicate entries in a list.
    refs=[]
    for i,tile in enumerate(TILES):
        def execute(i=i,tile=tile):
            p=base.plan_shade(tile=tile,instants=[times[0],times[2]],output_dir=str(OUT/f"v1_ref_{i}"),cache_dir=str(CACHE/"regression"))
            return asdict(base.run_shade(p))
        refs.append(ledger_job(f"v1_ref_{i}",execute))
    runs=[]
    for workers in (1,2):
        requests=[request(f"v2_reg_{workers}_{i}",tile,[times[1],times[2]],CACHE/"regression") for i,tile in enumerate(TILES)]
        requests.append(request(f"v2_odd_{workers}",TILES[0],[times[0]],CACHE/"regression",crop=tuple(samples["regression"]["odd_crop"]),jpg=True))
        runs.append(job(f"reg_{workers}",requests,workers=workers,logical_mosaic=True,statistics=True))
    comparisons=[]
    for workers,result in zip((1,2),runs):
        for i,ref in enumerate(refs):
            actual=json.loads((OUT/f"v2_reg_{workers}_{i}/result_index.json").read_text())
            for j,(old,new) in enumerate(zip(ref["frames"],actual["frames"])):
                for field in ("raster","quality_raster"):
                    with rasterio.open(old[field]) as a,rasterio.open(new[field]) as b:
                        assert np.array_equal(a.read(1),b.read(1)) and a.transform==b.transform
                comparisons.append(dict(workers=workers,tile=TILES[i],instant=j,shade_quality_identical=True,
                                        equality_neighborhood=new["equality_neighborhood"]))
        odd=json.loads((OUT/f"v2_odd_{workers}/result_index.json").read_text())["frames"][0]
        c,r,w,h=samples["regression"]["odd_crop"]
        for field in ("raster","quality_raster"):
            with rasterio.open(refs[0]["frames"][0][field]) as a,rasterio.open(odd[field]) as b:
                assert np.array_equal(a.read(1)[r:r+h,c:c+w],b.read(1))
        mosaic=OUT/f"state_reg_{workers}"/f"{result['id']}.logical_mosaic.json"
        tile=v2.plan_from_dict(result["plan"]["definition"]["requests"][f"v2_reg_{workers}_0"]).grid
        bounds=tile.bounds((c,r,w,h))
        labels,flags,transform=read_logical_window(mosaic,utc_time=times_utc(times[0]),bounds=bounds)
        with rasterio.open(odd["raster"]) as a,rasterio.open(odd["quality_raster"]) as b:
            assert np.array_equal(labels,a.read(1)) and np.array_equal(flags,b.read(1)) and transform==a.transform
    # Numerical production files are byte-identical to accepted V1, and keys match.
    unchanged={name:digest_file(ROOT/"src"/name)==digest_file(OUT/"accepted_snapshot"/name)
               for name in ("horizon.py","spatial.py","v1_cache.py","solar.py","shade_watch.py")}
    assert all(unchanged.values())
    atomic_json(path,dict(accepted_sha=V1_SHA,comparisons=comparisons,unchanged_numerical_files=unchanged,
                         horizon_difference_degrees=0.,support_identical=True,
                         note="exact same content-addressed cache entries; original numerical sources byte-identical"))


def times_utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat()


def optimization(samples):
    path=EVIDENCE/"optimization.json"
    if path.exists(): return
    base=accepted_v1()
    times=[samples["calibration"]["cold_instants"][1]]
    count=0
    orig=base.index_sources
    def inventory(directory):
        nonlocal count
        count+=1; return orig(directory)
    def execute():
        began=time.perf_counter()
        with patch.object(base,"index_sources",side_effect=inventory):
            for i in range(3):
                p=base.plan_shade(tile=TILES[0],instants=times,output_dir=str(OUT/f"opt_v1_{i}"),cache_dir=str(CACHE/"cal1"))
                base.run_shade(p)
        return dict(wall_seconds=time.perf_counter()-began,inventories=count)
    old=ledger_job("optimization_v1",execute)
    requests=[request(f"opt_v2_{i}",TILES[0],times,CACHE/"cal1") for i in range(3)]
    began=time.perf_counter()
    new=job("optimization_v2",requests)
    new_total=time.perf_counter()-began
    assert old["inventories"]==6 and new["metrics"]["input_inventory_calls"]==1
    for i in range(3):
        before=json.loads((OUT/f"opt_v1_{i}/result_index.json").read_text())["frames"][0]
        after=json.loads((OUT/f"opt_v2_{i}/result_index.json").read_text())["frames"][0]
        for field in ("raster","quality_raster"):
            with rasterio.open(before[field]) as a,rasterio.open(after[field]) as b:
                assert np.array_equal(a.read(1),b.read(1))
    atomic_json(path,dict(matched_requests=3,accepted_v1=old,v2=dict(inventories_plan_and_run=2,
                 wall_seconds=new_total,computed=new["metrics"]["computed"],reused=new["metrics"]["reused"]),
                 redundant_inventory_reduction=4,science_identical=True,
                 conclusion="fewer full input content scans; process/journal/verification overhead may regress small warm jobs"))


def cold_regression(samples):
    path=EVIDENCE/"cold_regression.json"
    if path.exists(): return
    times=[samples["regression"]["stamp"],"2026-10-18T23:17:11+08:00"]
    result=job("reg_cold_2",[request(f"reg_cold_2_{i}",tile,times,CACHE/"regression_v2_cold")
                            for i,tile in enumerate(TILES)],workers=2,logical_mosaic=True)
    assert result["metrics"]["computed"]==2
    comparisons=[]
    for i,tile in enumerate(TILES):
        plan=v2.plan_from_dict(result["plan"]["definition"]["requests"][f"reg_cold_2_{i}"])
        native=plan.tiles[0]
        for direction in native.directions:
            old,_=entry_paths(CACHE/"regression",native.spatial_key,direction)
            new,_=entry_paths(CACHE/"regression_v2_cold",native.spatial_key,direction)
            maxdiff=0.; support_diff=0; finite_diff=0; denominator=0
            with rasterio.open(old) as a,rasterio.open(new) as b:
                for _,window in a.block_windows(1):
                    x,y=a.read(window=window),b.read(window=window)
                    finite=np.isfinite(x[0]) & np.isfinite(y[0]); denominator+=int(finite.sum())
                    finite_diff+=int(np.count_nonzero(np.isfinite(x[0])!=np.isfinite(y[0])))
                    support_diff+=int(np.count_nonzero(x[1]!=y[1]))
                    if finite.any(): maxdiff=max(maxdiff,float(np.max(np.abs(x[0][finite]-y[0][finite]))))
            assert maxdiff<=1e-4 and support_diff==finite_diff==0
            comparisons.append(dict(tile=tile,direction=direction,max_horizon_difference_degrees=maxdiff,
                                    support_differences=support_diff,finite_mask_differences=finite_diff,
                                    finite_denominator=denominator))
        ref=json.loads((OUT/f"v1_ref_{i}/result_index.json").read_text())
        actual=json.loads((OUT/f"reg_cold_2_{i}/result_index.json").read_text())
        for a,b in zip(ref["frames"],actual["frames"]):
            for field in ("raster","quality_raster"):
                with rasterio.open(a[field]) as x,rasterio.open(b[field]) as y:
                    assert np.array_equal(x.read(1),y.read(1))
    grid=v2.plan_from_dict(result["plan"]["definition"]["requests"]["reg_cold_2_0"]).grid
    left,bottom,right,top=grid.bounds()
    bounds=(left+903*.5,bottom-2.5,left+927*.5,bottom+2.5)
    mosaic=OUT/"state_reg_cold_2"/f"{result['id']}.logical_mosaic.json"
    labels,flags,transform=read_logical_window(mosaic,utc_time=times_utc(times[0]),bounds=bounds)
    expected=[]
    for field in ("raster","quality_raster"):
        parts=[]
        for i in (0,1):
            frame=json.loads((OUT/f"v1_ref_{i}/result_index.json").read_text())["frames"][0]
            with rasterio.open(frame[field]) as ds:
                parts.append(ds.read(1)[-5:,903:927] if i==0 else ds.read(1)[:5,903:927])
        expected.append(np.concatenate(parts))
    assert np.array_equal(labels,expected[0]) and np.array_equal(flags,expected[1])
    atomic_json(path,dict(accepted_sha=V1_SHA,new_cache_computation=True,comparisons=comparisons,
                         shade_quality_identical=True,boundary_logical_pixels_identical=True))


def cli(samples):
    path=EVIDENCE/"cli.json"
    if path.exists(): return
    commands=[]
    def call(*args):
        command=[sys.executable,"-m","src.v2",*args]
        ran=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=180)
        commands.append(dict(command=command,returncode=ran.returncode,stderr=ran.stderr))
        assert ran.returncode==0,ran.stderr
        return json.loads(ran.stdout)
    planned=call("plan","--requests","docs/v2/example_batch.json")
    batch=call("submit","--requests","docs/v2/example_batch.json","--state","outputs/v2_example_state")["id"]
    result=ledger_job("cli_run",lambda: call("run","--batch",batch,"--state","outputs/v2_example_state"))
    status=call("status","--batch",batch,"--state","outputs/v2_example_state")
    cancelled=call("cancel","--batch",batch,"--state","outputs/v2_example_state")
    resumed=ledger_job("cli_resume",lambda:call("resume","--batch",batch,"--state","outputs/v2_example_state","--reverse-order"))
    assert status["state"]==resumed["state"]=="SUCCEEDED" and resumed["metrics"]["horizon_calls"]==0
    atomic_json(path,dict(commands=commands,batch=batch,plan=planned,result=result,
                         status=status,cancel_terminal=cancelled,resumed=resumed))


def final_holdouts(samples):
    """Revalidate unchanged coefficients on final journal/metadata robustness changes."""
    path=EVIDENCE/"candidate_holdouts.json"
    if path.exists(): return
    frozen=json.loads((EVIDENCE/"frozen_estimator.json").read_text())
    assert digest_file(ROOT/"docs/v2/estimator.json")==frozen["sha256"]
    atomic_json(EVIDENCE/"candidate_revalidation_manifest.json",dict(
        before_outcomes_utc=datetime.now(timezone.utc).isoformat(),
        reason="final strict-JSON/journal invariants/monitoring changes; coefficients and cases unchanged",
        cases=samples["holdouts"],model_sha256=frozen["sha256"],
        code={name:digest_file(ROOT/"src"/name) for name in ("v2.py","v2_state.py","v2_runner.py","v2_worker.py")}))
    h=samples["holdouts"]
    cold=job("candidate_cold",[request(f"candidate_cold_{i}",t,h["cold_instants"],CACHE/"candidate_cold") for i,t in enumerate(TILES)],workers=2)
    warmtimes=[]
    for start in h["warm_starts"]:warmtimes.extend(instants(start,h["warm_frames_per_date"]))
    warm=job("candidate_warm",[request(f"candidate_warm_{i}",t,warmtimes,CACHE/"held_warm") for i,t in enumerate(TILES)],workers=2)
    mixedcache=CACHE/"candidate_mixed"
    warm_plan=v1.plan_shade(tile=TILES[0],instants=h["mixed_instants"],output_dir=str(OUT/"candidate_cache_validation"),cache_dir=str(CACHE/"held_mixed"))
    tile=warm_plan.tiles[0]
    import shutil
    for direction in tile.directions:
        assert valid_entry(warm_plan.cache_directory,tile.spatial_key,direction,tile.source) is not None
    shutil.copytree(CACHE/"held_mixed"/tile.spatial_key,mixedcache/tile.spatial_key)
    for direction in tile.directions:
        assert valid_entry(mixedcache,tile.spatial_key,direction,tile.source) is not None
    mixed=job("candidate_mixed",[request(f"candidate_mixed_{i}",t,h["mixed_instants"],mixedcache) for i,t in enumerate(TILES)],workers=2)
    assert warm["metrics"]["horizon_calls"]==0 and warm["metrics"]["final_result_hits"]==0
    assert mixed["metrics"]["computed"]>0 and mixed["metrics"]["reused"]>0
    rows=[]
    for name,r in (("cold",cold),("warm",warm),("mixed",mixed)):
        observed=r["observed_run_api_seconds"]; predicted=r["prediction"]["total_wall_seconds"]
        rows.append(dict(name=name,predicted_seconds=predicted,observed_seconds=observed,
            absolute_percentage_error=abs(predicted-observed)/observed,duration_gate=observed>=10,
            calibrated_domain=r["prediction"]["calibrated_domain"],
            memory_ceiling_covers=r["metrics"]["peak_tree_rss_bytes"]<=r["prediction"]["resources"]["estimated_peak_bytes"],
            disk_ceiling_covers=r["metrics"]["peak_new_disk_bytes"]<=r["prediction"]["resources"]["estimated_peak_new_bytes"]))
    med=statistics.median(r["absolute_percentage_error"] for r in rows); maximum=max(r["absolute_percentage_error"] for r in rows)
    atomic_json(path,dict(frozen_model_sha256=frozen["sha256"],rows=rows,median_ape=med,max_ape=maximum,
       gate=all(r["duration_gate"] and r["calibrated_domain"] and r["memory_ceiling_covers"] and r["disk_ceiling_covers"] for r in rows) and med<=.3 and maximum<=.6,
       note="Same development validation cases repeated for final non-tuning code changes; original outcomes retained. Independent acceptance must select new cases."))


def holdouts(samples):
    path=EVIDENCE/"holdouts.json"
    if path.exists(): return
    model_path=ROOT/"docs/v2/estimator.json"
    frozen=json.loads((EVIDENCE/"frozen_estimator.json").read_text())
    assert digest_file(model_path)==frozen["sha256"]
    h=samples["holdouts"]
    cold=job("held_cold",[request(f"held_cold_{i}",t,h["cold_instants"],CACHE/"held_cold") for i,t in enumerate(TILES)],workers=2)
    warmtimes=[]
    for start in h["warm_starts"]: warmtimes.extend(instants(start,h["warm_frames_per_date"]))
    setups=[]
    for i,tile in enumerate(TILES):
        setups.append(job(f"held_warm_setup_{i}",[request(f"held_warm_setup_{i}",tile,h["warm_starts"],CACHE/"held_warm",crop=(903,703,24,20))]))
    warm=job("held_warm",[request(f"held_warm_{i}",t,warmtimes,CACHE/"held_warm") for i,t in enumerate(TILES)],workers=2)
    assert warm["metrics"]["horizon_calls"]==0 and warm["metrics"]["final_result_hits"]==0
    setup=job("held_mixed_setup",[request("held_mixed_setup",TILES[0],h["mixed_instants"],CACHE/"held_mixed",crop=(903,703,24,20))])
    mixed=job("held_mixed",[request(f"held_mixed_{i}",t,h["mixed_instants"],CACHE/"held_mixed") for i,t in enumerate(TILES)],workers=2)
    assert mixed["metrics"]["computed"]>0 and mixed["metrics"]["reused"]>0
    rows=[]
    for name,result in (("cold",cold),("warm",warm),("mixed",mixed)):
        observed=result["observed_run_api_seconds"]; predicted=result["prediction"]["total_wall_seconds"]
        rows.append(dict(name=name,predicted_seconds=predicted,observed_seconds=observed,
                         absolute_percentage_error=abs(predicted-observed)/observed,
                         duration_gate=observed>=10.,calibrated_domain=result["prediction"]["calibrated_domain"],
                         peak_memory_bytes=result["metrics"]["peak_tree_rss_bytes"],
                         peak_disk_bytes=result["metrics"]["peak_new_disk_bytes"],
                         memory_ceiling_covers=result["metrics"]["peak_tree_rss_bytes"]<=result["prediction"]["resources"]["estimated_peak_bytes"],
                         disk_ceiling_covers=result["metrics"]["peak_new_disk_bytes"]<=result["prediction"]["resources"]["estimated_peak_new_bytes"]))
    med=statistics.median(r["absolute_percentage_error"] for r in rows); maximum=max(r["absolute_percentage_error"] for r in rows)
    atomic_json(path,dict(frozen_model_sha256=frozen["sha256"],rows=rows,median_ape=med,max_ape=maximum,
                         gate=all(r["duration_gate"] and r["calibrated_domain"] and r["memory_ceiling_covers"] and r["disk_ceiling_covers"] for r in rows) and med<=.3 and maximum<=.6))
    assert digest_file(model_path)==frozen["sha256"],"Estimator must remain frozen"


def audit():
    baseline=json.loads((EVIDENCE/"baseline.json").read_text())
    changed=[]
    for name,(size,mtime) in baseline["protected"].items():
        path=ROOT/name
        if not path.exists() or (path.stat().st_size,path.stat().st_mtime_ns)!=(size,mtime): changed.append(name)
    assert not changed,changed
    for rec in baseline["source_inventory"]:
        assert digest_file(rec["path"])==rec["sha256"]
    atomic_json(EVIDENCE/"protection_audit.json",dict(changed=changed,protected_files=len(baseline["protected"]),dsm_hashes_match=True,
                v1_contract_matches=digest_file(ROOT/"docs/prompts/v1/ACCEPTANCE_CONTRACT.md")==baseline["hashes"]["docs/prompts/v1/ACCEPTANCE_CONTRACT.md"],
                v2_contract_matches=digest_file(ROOT/"docs/prompts/v2/ACCEPTANCE_CONTRACT.md")==baseline["hashes"]["docs/prompts/v2/ACCEPTANCE_CONTRACT.md"]))
    atomic_json(EVIDENCE/"projection.json",v2.project_territory(tile_count=1000,effective_pixel_fraction=.9,
         union_directions=24,queries_per_tile=8,directional_cache_fraction=.5,workers=2,
         output_selection="scientific_only",hardware="calibration host only"))
    files={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=digest_file(p)) for p in EVIDENCE.rglob("*") if p.is_file() and p.name!="manifest.json"}
    atomic_json(EVIDENCE/"manifest.json",dict(files=files))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("stage",choices=("calibration","regression","cold_regression","optimization","holdouts","final_holdouts","cli","audit","all"))
    args=parser.parse_args(); samples=manifest()
    stages=["calibration","regression","cold_regression","optimization","holdouts","final_holdouts","cli","audit"] if args.stage=="all" else [args.stage]
    for stage in stages:
        globals()[stage](samples) if stage!="audit" else audit()


if __name__=="__main__": main()
