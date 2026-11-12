"""Measure B2.2 jobs and enforce the frozen development budgets."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'docs/sea2/evidence/b2_2'
WALL_CAPS = dict(real=3600, build=3600, validation=1800)
MEMORY_CAP = 12 * 1024**3
ARTIFACT_CAP = 30 * 1024**3


def sleep_inclusive_clock():
    if sys.platform == 'darwin':
        libc = ctypes.CDLL(None)

        class Timebase(ctypes.Structure):
            _fields_ = [('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32)]

        factor = Timebase()
        if libc.mach_timebase_info(ctypes.byref(factor)) != 0:
            raise RuntimeError('Cannot read Mac continuous clock timebase')
        libc.mach_continuous_time.restype = ctypes.c_uint64
        return lambda: libc.mach_continuous_time()*factor.numer/factor.denom/1e9
    if hasattr(time, 'CLOCK_BOOTTIME'):
        return lambda: time.clock_gettime(time.CLOCK_BOOTTIME)
    return time.time


def rss_bytes(usage):
    return usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024


def artifact_bytes(root, before, extra):
    total = 0
    for base in (root/'data/processed', root/'outputs', EVIDENCE, *extra):
        for directory, _, files in os.walk(base):
            for name in files:
                path = Path(directory)/name
                if path.is_relative_to(root) and path.relative_to(root).as_posix() in before:
                    continue
                try:
                    info = path.lstat()
                    total += max(info.st_size, info.st_blocks*512)
                except FileNotFoundError:
                    pass  # An atomic publication moved it between list and stat.
    return total


def end_group(child):
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic()+2
    while time.monotonic() < deadline:
        result = os.wait4(child.pid, os.WNOHANG)
        if result[0]:
            break
        time.sleep(.05)
    else:
        result = None
    # Workers can outlive their controller. Stop any residual group members.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return result or os.wait4(child.pid, 0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--category', choices=(*WALL_CAPS, 'setup', 'tests'), required=True)
    parser.add_argument('--ledger', type=Path, default=EVIDENCE/'resources.jsonl')
    parser.add_argument('--log', type=Path)
    parser.add_argument('--cwd', type=Path, default=ROOT)
    parser.add_argument('--protected-before', type=Path)
    parser.add_argument('--extra-artifacts', action='append', type=Path, default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('a command is required after --')
    before = set()
    if args.protected_before:
        inventory = json.loads(args.protected_before.read_text())
        before = {key for group in inventory.values() for key in group}
    previous = [json.loads(line) for line in args.ledger.read_text().splitlines()] if args.ledger.exists() else []
    charged = [row for row in previous if row['category'] == args.category]
    if args.category == 'build' and charged:
        raise SystemExit('SW-B2.2 permits one development view build')
    remaining = WALL_CAPS.get(args.category, 3600)-sum(row['wall_seconds'] for row in charged)
    if remaining <= 0:
        raise SystemExit(f'SW-B2.2 {args.category} time budget exhausted')

    # Fail before starting a scientific process if child inspection is unavailable.
    psutil.Process().children(recursive=True)
    clock = sleep_inclusive_clock()
    before_disk = artifact_bytes(ROOT, before, args.extra_artifacts) if args.protected_before else None
    output = args.log.open('w') if args.log else None
    started, wall_started = clock(), time.time()
    observed = {}
    tree_peak, disk_peak, last_disk, reason = 0, before_disk or 0, started, None
    child = subprocess.Popen(command, cwd=args.cwd, start_new_session=True, stdout=output,
                             stderr=subprocess.STDOUT if output else None)

    def interrupted(signum, _frame):
        raise InterruptedError(signal.Signals(signum).name)

    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, interrupted)
    try:
        while True:
            total = 0
            try:
                parent = psutil.Process(child.pid)
                for proc in [parent, *parent.children(recursive=True)]:
                    try:
                        rss = proc.memory_info().rss
                        total += rss
                        entry = observed.setdefault(proc.pid, dict(pid=proc.pid, name=proc.name(), peak_rss_bytes=0))
                        entry['peak_rss_bytes'] = max(rss, entry['peak_rss_bytes'])
                    except psutil.NoSuchProcess:
                        pass
            except psutil.NoSuchProcess:
                pass
            tree_peak = max(tree_peak, total)
            now = clock()
            if before_disk is not None and now-last_disk >= 10:
                disk_peak = max(disk_peak, artifact_bytes(ROOT, before, args.extra_artifacts))
                last_disk = now
            waited = os.wait4(child.pid, os.WNOHANG)
            if waited[0]:
                break
            if now-started >= remaining:
                reason = 'wall_time_budget'
            elif tree_peak >= MEMORY_CAP:
                reason = '12_GiB_memory_budget'
            elif disk_peak >= ARTIFACT_CAP:
                reason = '30_GiB_artifact_budget'
            if reason:
                waited = end_group(child)
                break
            time.sleep(min(.25, max(0, remaining-(clock()-started))))
    except (InterruptedError, PermissionError) as exc:
        reason = str(exc)
        waited = end_group(child)
    finally:
        if output:
            output.close()

    elapsed = clock()-started
    _, status, usage = waited
    child.returncode = os.waitstatus_to_exitcode(status)
    after_disk = artifact_bytes(ROOT, before, args.extra_artifacts) if before_disk is not None else None
    peak_rss = max(rss_bytes(usage), tree_peak)
    if elapsed > remaining or peak_rss > MEMORY_CAP or (after_disk or 0) > ARTIFACT_CAP:
        reason = reason or 'limit_exceeded_at_exit'
    record = dict(label=args.label, category=args.category, command=command, cwd=str(args.cwd),
                  exit_code=child.returncode, wall_seconds=elapsed, started_unix=wall_started,
                  wall_clock='mach_continuous_time' if sys.platform=='darwin' else 'sleep-inclusive',
                  limit_seconds=remaining, child_peak_rss_bytes=rss_bytes(usage),
                  sampled_process_tree_peak_rss_bytes=tree_peak, peak_rss_bytes=peak_rss,
                  processes=list(observed.values()), stopped_for=reason,
                  new_artifact_peak_bytes=max(disk_peak,after_disk or 0) if before_disk is not None else None,
                  new_artifact_delta_bytes=after_disk-before_disk if before_disk is not None else None)
    with args.ledger.open('a') as stream:
        stream.write(json.dumps(record,sort_keys=True)+'\n')
    print('B2.2 '+args.label+' '+json.dumps({k:record[k] for k in
          ('exit_code','wall_seconds','peak_rss_bytes','new_artifact_peak_bytes','stopped_for')}), flush=True)
    return child.returncode if reason is None else 124


if __name__ == '__main__':
    sys.exit(main())
