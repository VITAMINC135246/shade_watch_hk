"""WSL2 smoke test for shade_watch_hk (run inside WSL2, from the repository root, with the repo .venv).

    .venv/bin/python tools/wsl2_smoke/run_smoke.py --pack ~/wsl2_smoke_pack

What it checks (see docs/v3/WSL2_SMOKE_TEST.md):
  P1 environment   Linux/WSL2, Python 3.12, packages equal requirements.lock.txt, repo at the pinned
                   commit, engine files identical to accepted V2, state/cache on a supported local filesystem
  P2 tests         the existing pytest suite passes
  P3 inputs        pack hashes verify; spatial keys equal the Mac keys
  P4 run           V2 plan/submit/run reaches SUCCEEDED; resume adds no attempts
  P5 horizons      12 cache entries: same NaN mask, |delta horizon| <= 1e-4 deg, identical support,
                   identical distant-obstruction thresholds
  P6 labels        Shade/Quality equal the Mac frames, or every differing pixel lies in the
                   1e-4 deg equality neighbourhood

It writes only to outputs/wsl2_smoke_<stamp>/ and data/processed/shade_v1/wsl2_smoke_<stamp>/.
Cross-architecture bit-identity is not required; the tolerance is the accepted V2 B08 rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ENGINE_FILES = ("v1.py", "v1_cache.py", "horizon.py", "solar.py", "spatial.py", "shade_watch.py",
                "v2.py", "v2_worker.py", "v2_runner.py", "v2_state.py")


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------- pure comparison functions (unit-testable without rasterio) ----------

def compare_horizon(h_ref, h_new, s_ref, s_new, tol):
    nan_ref, nan_new = ~np.isfinite(h_ref), ~np.isfinite(h_new)
    both = ~nan_ref & ~nan_new
    diff = np.abs(h_ref[both].astype(np.float64) - h_new[both].astype(np.float64))
    result = dict(nan_mask_equal=bool(np.array_equal(nan_ref, nan_new)),
                  max_abs_diff_deg=float(diff.max()) if diff.size else 0.0,
                  pixels_over_tol=int((diff > tol).sum()),
                  support_equal=bool(np.array_equal(s_ref, s_new)),
                  support_differences=int((s_ref != s_new).sum()))
    result["pass"] = (result["nan_mask_equal"] and result["pixels_over_tol"] == 0 and result["support_equal"])
    return result


def compare_labels(ref, new, h_ref, h_new, elevation, tol):
    """Label differences are acceptable only where a horizon sits within tol of the solar elevation."""
    differ = ref != new
    near = np.zeros_like(differ)
    finite = np.isfinite(h_ref) | np.isfinite(h_new)
    with np.errstate(invalid="ignore"):
        near = finite & ((np.abs(h_ref - elevation) <= tol) | (np.abs(h_new - elevation) <= tol))
    unexplained = differ & ~near
    return dict(differing=int(differ.sum()), explained_by_equality_neighbourhood=int((differ & near).sum()),
                unexplained=int(unexplained.sum()), pass_=bool(unexplained.sum() == 0))


def place_tiles(grid_shape, grid_transform, tiles, fill=np.nan):
    """tiles: list of (array, transform) on the same 0.5 m lattice -> mosaic on the combined grid."""
    out = np.full(grid_shape, fill, dtype=np.float64)
    gx, gy = grid_transform[2], grid_transform[5]
    for array, transform in tiles:
        col = int(round((transform[2] - gx) / 0.5))
        row = int(round((gy - transform[5]) / 0.5))
        h, w = array.shape
        out[row:row + h, col:col + w] = array
    return out


# ---------- checks ----------

def check_environment(manifest):
    from importlib import metadata
    info = dict(system=platform.system(), release=platform.release(), machine=platform.machine(),
                python=platform.python_version(), cpu_count=os.cpu_count())
    try:
        info["proc_version"] = Path("/proc/version").read_text().strip()
    except OSError:
        info["proc_version"] = None
    try:
        info["cpu_model"] = next(l.split(":", 1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines()
                                 if l.startswith("model name"))
    except (OSError, StopIteration):
        info["cpu_model"] = None
    import psutil
    info["memory_total_gib"] = round(psutil.virtual_memory().total / 1024**3, 1)
    info["disk_free_gib"] = round(shutil.disk_usage(ROOT).free / 1024**3, 1)
    issues = []
    if info["system"] != "Linux":
        issues.append("not Linux")
    if not (info["proc_version"] and "microsoft" in info["proc_version"].lower()):
        issues.append("not running under WSL (allowed for plain Linux; recorded)")
    if not info["python"].startswith("3.12."):
        issues.append(f"Python {info['python']} is not 3.12")
    mismatched = {}
    for line in (ROOT / "requirements.lock.txt").read_text().splitlines():
        if "==" in line:
            name, version = line.strip().split("==")
            try:
                installed = metadata.version(name)
            except metadata.PackageNotFoundError:
                installed = None
            if installed != version:
                mismatched[name] = dict(locked=version, installed=installed)
    if mismatched:
        issues.append("package versions differ from requirements.lock.txt")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != manifest["base_commit"]:
        issues.append(f"HEAD {head} is not the pinned base commit")
    engine_diff = subprocess.run(["git", "diff", "--quiet", manifest["accepted_engine_commit"], "--"]
                                 + [f"src/{n}" for n in ENGINE_FILES], cwd=ROOT).returncode
    if engine_diff != 0:
        issues.append("engine files differ from the accepted V2 commit")
    sys.path.insert(0, str(ROOT))
    from src.v2_state import local_filesystem
    try:
        info["filesystem"] = local_filesystem(ROOT / "outputs")
    except (ValueError, OSError) as exc:
        info["filesystem"] = None
        issues.append(f"filesystem rejected by V2: {exc}")
    info.update(head=head, package_mismatches=mismatched)
    hard = [i for i in issues if not i.startswith("not running under WSL")]
    return dict(info=info, issues=issues, status="PASS" if not hard else "FAIL")


def check_pack(pack, manifest):
    bad = []
    for name, meta in manifest["dsm_files"].items():
        if sha256(pack / "dsm" / name) != meta["sha256"]:
            bad.append(f"dsm/{name}")
    for tile in manifest["tiles"]:
        for entry in tile["entries"].values():
            path = pack / "reference/cache" / tile["spatial_key"] / f"{entry['entry']}.tif"
            if sha256(path) != entry["tif_sha256"]:
                bad.append(str(path.relative_to(pack)))
    for frame in manifest["frames"]:
        for name, digest in frame["files"].items():
            if sha256(pack / "reference/frames" / name) != digest:
                bad.append(f"reference/frames/{name}")
    return dict(bad_files=bad, status="PASS" if not bad else "FAIL")


def run_tests():
    started = time.perf_counter()
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-15:]
    return dict(returncode=proc.returncode, seconds=round(time.perf_counter() - started, 1), tail=tail,
                status="PASS" if proc.returncode == 0 else "FAIL")


def run_batch(pack, manifest, stamp):
    from src.v2 import plan_batch, submit_batch, run_batch as run, status_batch, resume_batch
    out = f"outputs/wsl2_smoke_{stamp}"
    request = dict(id="cheungchau", tiles=manifest["request"]["tiles"], instants=manifest["request"]["instants"],
                   direction_method=manifest["request"]["direction_method"], dsm_dir=str(pack / "dsm"),
                   output_dir=f"{out}/cheungchau", cache_dir=f"data/processed/shade_v1/wsl2_smoke_{stamp}")
    timings = {}
    t = time.perf_counter(); plan = plan_batch([request], workers=1); timings["plan_seconds"] = time.perf_counter() - t
    batch = submit_batch(plan, state_dir=f"{out}/state")
    t = time.perf_counter(); status = run(batch, state_dir=f"{out}/state"); timings["run_seconds"] = time.perf_counter() - t
    attempts_before = len(status.get("attempts", []))
    t = time.perf_counter(); resumed = resume_batch(batch, state_dir=f"{out}/state"); timings["resume_seconds"] = time.perf_counter() - t
    attempts_after = len(resumed.get("attempts", []))
    ok = status["state"] == "SUCCEEDED" and resumed["state"] == "SUCCEEDED" and attempts_after == attempts_before
    return dict(batch=batch, state=status["state"], resumed_state=resumed["state"], tasks=status.get("tasks"),
                attempts_before_resume=attempts_before, attempts_after_resume=attempts_after,
                failures=status.get("failures"), timings={k: round(v, 1) for k, v in timings.items()},
                output_dir=f"{out}/cheungchau", cache_dir=request["cache_dir"], status="PASS" if ok else "FAIL")


def compare_science(pack, manifest, run_info):
    import rasterio
    tol = manifest["tolerances"]["horizon_abs_deg"]
    index = json.loads((ROOT / run_info["output_dir"] / "result_index.json").read_text())
    keys = {t["source_name"]: t["spatial_key"] for t in index["frames"][0]["solar_by_tile"]}
    key_check = {t["name"]: keys.get(t["name"]) == t["spatial_key"] for t in manifest["tiles"]}
    horizons, entry_results, speed = {}, [], []
    for tile in manifest["tiles"]:
        for direction, entry in tile["entries"].items():
            new_path = ROOT / run_info["cache_dir"] / tile["spatial_key"] / f"{entry['entry']}.tif"
            ref_path = pack / "reference/cache" / tile["spatial_key"] / f"{entry['entry']}.tif"
            with rasterio.open(ref_path) as r, rasterio.open(new_path) as n:
                h_ref, s_ref, _ = r.read(); h_new, s_new, _ = n.read()
                transform = tuple(n.transform)[:6]
            result = compare_horizon(h_ref, h_new, s_ref, s_new, tol)
            meta = json.loads(new_path.with_suffix(".json").read_text())
            result.update(tile=tile["name"], direction=float(direction),
                          threshold_equal=meta["threshold_deg"] == entry["threshold_deg"])
            result["pass"] = result["pass"] and result["threshold_equal"]
            entry_results.append(result)
            horizons[(tile["name"], float(direction))] = (h_ref, h_new, transform)
            if entry.get("mac_calculation_seconds") and meta.get("calculation_seconds"):
                speed.append(meta["calculation_seconds"] / entry["mac_calculation_seconds"])
    shape = (manifest["grid"]["height"], manifest["grid"]["width"])
    gt = manifest["grid"]["transform"]
    frame_results = []
    new_frames = {f["utc_time"]: f for f in index["frames"]}
    for frame in manifest["frames"]:
        new = new_frames[frame["utc_time"]]
        ref_names = sorted(frame["files"])
        q_ref, s_ref = [pack / "reference/frames" / n for n in ref_names]  # quality_*, shade_*
        with rasterio.open(s_ref) as a, rasterio.open(new["raster"]) as b:
            shade_ref, shade_new = a.read(1), b.read(1)
            transform_equal = tuple(a.transform) == tuple(b.transform)
        with rasterio.open(q_ref) as a, rasterio.open(new["quality_raster"]) as b:
            qual_ref, qual_new = a.read(1), b.read(1)
        tiles_ref, tiles_new, elev = [], [], []
        for t in frame["solar_by_tile"]:
            h_ref, h_new, transform = horizons[(t["source_name"], float(t["direction_deg"]))]
            tiles_ref.append((h_ref, transform)); tiles_new.append((h_new, transform))
            elev.append((np.full(h_ref.shape, t["apparent_elevation_deg"]), transform))
        H_ref, H_new, E = (place_tiles(shape, gt, x) for x in (tiles_ref, tiles_new, elev))
        shade = compare_labels(shade_ref, shade_new, H_ref, H_new, E, tol)
        quality = compare_labels(qual_ref, qual_new, H_ref, H_new, E, tol)
        frame_results.append(dict(local_time=frame["local_time"], transform_equal=transform_equal,
                                  shade=shade, quality=quality,
                                  passed=transform_equal and shade["pass_"] and quality["pass_"]))
    return dict(
        keys=dict(per_tile=key_check, status="PASS" if all(key_check.values()) else "FAIL"),
        horizons=dict(entries=entry_results, status="PASS" if all(e["pass"] for e in entry_results) else "FAIL"),
        labels=dict(frames=frame_results, status="PASS" if all(f["passed"] for f in frame_results) else "FAIL"),
        speed_vs_mac=dict(median_ratio=float(np.median(speed)) if speed else None,
                          note="WSL calculation_seconds / Mac calculation_seconds per cache entry; >1 means slower"))


def write_report(out, report):
    out.mkdir(parents=True, exist_ok=True)
    (out / "SMOKE_REPORT.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    rows = [("P1 environment", report["P1"]["status"]), ("P2 tests", report["P2"]["status"]),
            ("P3 inputs (pack hashes)", report["P3"]["status"]), ("P3 inputs (spatial keys)", report.get("P3_keys", "NOT VERIFIED")),
            ("P4 V2 run and resume", report["P4"]["status"]), ("P5 horizons", report.get("P5", "NOT VERIFIED")),
            ("P6 labels", report.get("P6", "NOT VERIFIED"))]
    lines = ["# WSL2 smoke test report", "", f"Generated: {report['generated']}", "",
             "| Check | Result |", "| --- | --- |"] + [f"| {a} | {b} |" for a, b in rows]
    lines += ["", "Environment:", "```", json.dumps(report["P1"]["info"], indent=2, default=str), "```",
              "", "Issues: " + (", ".join(report["P1"]["issues"]) or "none"),
              "", f"Timings: {report['P4'].get('timings')}",
              f"Speed vs Mac (median calculation-time ratio): {report.get('speed_vs_mac')}",
              "", "Details: SMOKE_REPORT.json. This is a platform smoke test, not V3 acceptance."]
    (out / "SMOKE_REPORT.md").write_text("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", required=True, help="unpacked smoke pack directory on the WSL ext4 filesystem")
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%S"))
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    pack = Path(args.pack).expanduser().resolve()
    manifest = json.loads((pack / "reference_manifest.json").read_text())
    out = ROOT / f"outputs/wsl2_smoke_{args.stamp}"
    if out.exists():
        raise SystemExit(f"{out} exists; choose a new --stamp")
    report = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S %z"), pack=str(pack))
    report["P1"] = check_environment(manifest)
    report["P3"] = check_pack(pack, manifest)
    report["P2"] = dict(status="NOT VERIFIED", reason="skipped") if args.skip_tests else run_tests()
    if report["P1"]["status"] == "FAIL" or report["P3"]["status"] == "FAIL":
        report["P4"] = dict(status="NOT VERIFIED", reason="environment or pack failed")
        write_report(out, report)
        print(f"Stopped early; see {out / 'SMOKE_REPORT.md'}")
        return 1
    report["P4"] = run_batch(pack, manifest, args.stamp)
    if report["P4"]["status"] == "PASS":
        science = compare_science(pack, manifest, report["P4"])
        report["science"] = science
        report["P3_keys"] = science["keys"]["status"]
        report["P5"] = science["horizons"]["status"]
        report["P6"] = science["labels"]["status"]
        report["speed_vs_mac"] = science["speed_vs_mac"]
    write_report(out, report)
    print((out / "SMOKE_REPORT.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
