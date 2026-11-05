"""Measured B2 commands with cumulative job, memory and artifact guards.

Example: python -m tools.sea2.resources --label sea-run --category real --
         python -m tools.shade_map run --machine machine.json region.json
On macOS process inspection must be permitted before the child is launched.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import psutil


def rss_bytes(usage):
    return usage.ru_maxrss if sys.platform=='darwin' else usage.ru_maxrss*1024


def artifact_bytes(root,before):
    total=0
    for base in ('data/processed','outputs'):
        for directory,dirs,files in os.walk(root/base):
            for name in files:
                path=Path(directory)/name; relative=path.relative_to(root).as_posix()
                if relative not in before:
                    try: total+=path.lstat().st_size
                    except FileNotFoundError: pass  # an atomic task publication may move it
    return total


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True);p.add_argument('--category',choices=['setup','planning','real','build','tests'],default='planning')
    p.add_argument('--ledger',default='docs/sea2/evidence/resources.jsonl');p.add_argument('--log')
    p.add_argument('--limit',type=float,default=3600)
    p.add_argument('--protected-before',help='Local full before-inventory; compact hashes are retained as evidence')
    p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args(argv)
    command=a.command[1:] if a.command[:1]==['--'] else a.command
    if not command:p.error('a command is required after --')
    ledger=Path(a.ledger);ledger.parent.mkdir(parents=True,exist_ok=True)
    previous=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    charged=sum(r['wall_seconds'] for r in previous if r.get('category')=='real')
    limit=min(a.limit,3600-charged) if a.category=='real' else a.limit
    if limit<=0:raise SystemExit('B2 real-DSM job time budget exhausted')
    before=None
    if a.protected_before:
        groups=json.loads(Path(a.protected_before).read_text());before={k for group in groups.values() for k in group}
    root=Path(__file__).resolve().parents[2]
    # Fail before launching a scientific child if OS process inspection is denied.
    psutil.Process().children(recursive=True)
    output=Path(a.log).open('w') if a.log else None
    started=time.monotonic();wall_started=time.time()
    def elapsed():return max(time.monotonic()-started,time.time()-wall_started)
    child=subprocess.Popen(command,start_new_session=True,stdout=output,stderr=subprocess.STDOUT if output else None)
    observed={};tree_peak=0;reason=None;disk_peak=0;last_disk=started-10
    try:
        while True:
            total=0
            try:
                parent=psutil.Process(child.pid)
                for proc in [parent,*parent.children(recursive=True)]:
                    try:
                        n=proc.memory_info().rss;total+=n
                        entry=observed.setdefault(str(proc.pid),dict(pid=proc.pid,name=proc.name(),sampled_peak_rss_bytes=0))
                        entry['sampled_peak_rss_bytes']=max(n,entry['sampled_peak_rss_bytes'])
                    except psutil.NoSuchProcess:pass
            except psutil.NoSuchProcess:pass
            tree_peak=max(tree_peak,total)
            now=time.monotonic()
            if before is not None and now-last_disk>=10:
                disk_peak=max(disk_peak,artifact_bytes(root,before));last_disk=now
            pid,status,usage=os.wait4(child.pid,os.WNOHANG)
            if pid:
                child.returncode=os.waitstatus_to_exitcode(status);break
            if elapsed()>limit:reason='wall_time_budget'
            if total>12*1024**3:reason='12_GiB_memory_budget'
            if disk_peak>30*1024**3:reason='30_GiB_artifact_budget'
            if reason:
                os.killpg(child.pid,signal.SIGTERM)
                _,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status);break
            time.sleep(.1)
    finally:
        if output:output.close()
    if before is not None:disk_peak=max(disk_peak,artifact_bytes(root,before))
    record=dict(label=a.label,category=a.category,command=command,exit_code=child.returncode,
                wall_seconds=elapsed(),uptime_seconds=time.monotonic()-started,started_unix=wall_started,
                child_peak_rss_bytes=rss_bytes(usage),
                sampled_process_tree_peak_rss_bytes=tree_peak,watchdog_peak_rss_bytes=rss_bytes(resource.getrusage(resource.RUSAGE_SELF)),
                new_artifact_peak_bytes=disk_peak if before is not None else None,
                processes=list(observed.values()),stopped_for=reason)
    with ledger.open('a') as stream:stream.write(json.dumps(record,sort_keys=True)+'\n')
    print('B2_RESOURCE '+json.dumps(record,sort_keys=True),file=sys.stderr,flush=True)
    return child.returncode if reason is None else 124


if __name__=='__main__':sys.exit(main())
