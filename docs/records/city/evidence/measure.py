"""Supervise one authorized Mac job and record its resource use."""
from argparse import ArgumentParser
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

import psutil

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[2]
LEDGER = EVIDENCE / "resources.jsonl"
GIB = 1024**3
LIMITS = {"registration": 1200, "shade": 5400}
CONTAINERS = (
    "data/processed/dsm_catalogues",
    "data/processed/dsm_views/sea_fill_v2_2",
    "data/processed/shade_v1",
    "outputs",
    "outputs/shade_map_work",
    "outputs/shade_map_work/.locks",
    "outputs/region_views",
    "outputs/sea2_2_diagnostic_work",
    "outputs/sea2_2_diagnostic_work/.locks",
)


def file_bytes(path):
    try:
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            return sum(file_bytes(p) for p in path.iterdir())
        return info.st_size
    except FileNotFoundError:
        return 0


def artifacts(baseline):
    # Inspect only new roots and names. Avoid walking the pre-existing outputs
    # and caches on every sample. The after-audit checks those independently.
    paths = set()
    for name in CONTAINERS:
        directory = ROOT / name
        if directory.exists():
            paths.update(p for p in directory.iterdir()
                         if p.relative_to(ROOT).as_posix() not in baseline
                         and p.relative_to(ROOT).as_posix() not in CONTAINERS)
    return sum(file_bytes(p) for p in paths)


def mac_children():
    proc = ctypes.CDLL("/usr/lib/libproc.dylib")
    children = proc.proc_listchildpids
    children.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_int)

    def list_children(pid):
        pids = (ctypes.c_int * 256)()
        count = children(pid, pids, ctypes.sizeof(pids))
        return pids[:count] if count > 0 else []

    return list_children


def tree_rss(root, children):
    by_pid = {}
    pending = [root]
    while pending:
        pid = pending.pop()
        try:
            by_pid[pid] = psutil.Process(pid).memory_info().rss
        except psutil.NoSuchProcess:
            continue
        pending.extend(p for p in children(pid) if p not in by_pid)
    return by_pid


def timestamp(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--job", required=True)
    parser.add_argument("--category", choices=["audit", *LIMITS], required=True)
    parser.add_argument("command", nargs="+")
    args = parser.parse_args()
    baseline = {}
    if args.baseline:
        baseline = json.loads(args.baseline.read_text())["data"]
    elif args.category != "audit":
        parser.error("a protected baseline is required for timed jobs")
    prior = LEDGER.read_text().splitlines() if LEDGER.exists() else []
    spent = sum(row["wall_seconds"] for row in map(json.loads, prior)
                if row["category"] == args.category)
    budget = LIMITS.get(args.category, float("inf")) - spent
    if budget <= 0:
        parser.exit(2, "Campaign wall budget already exhausted\n")
    children = mac_children()
    disk_before = artifacts(baseline) if baseline else 0
    disk_peak = disk_before
    rss_peak = 0
    process_peaks = {}
    stopped = None
    started = time.time()
    deadline = started + budget
    command = ["/usr/bin/caffeinate", "-dims", *args.command]
    job = subprocess.Popen(command, cwd=ROOT, start_new_session=True)
    last_disk = started
    try:
        while job.poll() is None:
            now = time.time()
            rss = tree_rss(job.pid, children)
            rss_peak = max(rss_peak, sum(rss.values()))
            for pid, size in rss.items():
                process_peaks[pid] = max(process_peaks.get(pid, 0), size)
            if baseline and now - last_disk >= 3:
                disk_peak = max(disk_peak, artifacts(baseline))
                last_disk = now
            if time.time() >= deadline:
                stopped = "wall budget"
            elif rss_peak > 12 * GIB:
                stopped = "memory budget"
            elif disk_peak > 20 * GIB:
                stopped = "artifact budget"
            if stopped:
                break
            time.sleep(.10)
    finally:
        if job.poll() is None:
            # The session is private to this job, including its spawn workers.
            os.killpg(job.pid, signal.SIGKILL)
        status = job.wait()
        ended = time.time()
        disk_after = artifacts(baseline) if baseline else 0
        disk_peak = max(disk_peak, disk_after)
        if not stopped and ended > deadline:
            stopped = "wall budget"
        if not stopped and disk_peak > 20 * GIB:
            stopped = "artifact budget"
        row = dict(job=args.job, category=args.category, command=args.command,
                   started_utc=timestamp(started), ended_utc=timestamp(ended),
                   wall_seconds=round(ended - started, 6), peak_tree_rss_bytes=rss_peak,
                   sampled_process_peaks_bytes=process_peaks, exit_code=status, stopped=stopped,
                   new_artifact_bytes=disk_after - disk_before,
                   campaign_artifact_bytes=disk_after,
                   campaign_peak_artifact_bytes=disk_peak)
        with LEDGER.open("a") as ledger:
            ledger.write(json.dumps(row, sort_keys=True) + "\n")
        print(json.dumps(row), file=sys.stderr)
    return 124 if stopped else status


if __name__ == "__main__":
    raise SystemExit(main())
