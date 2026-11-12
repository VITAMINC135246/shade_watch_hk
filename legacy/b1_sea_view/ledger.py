"""Cumulative development accounting with bounded, supervised child jobs."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import psutil

from tools.sea_view.checks import ROOT,EVIDENCE


def disk_bytes():
    roots=[ROOT/'data/processed/coastline/ib5000_20261012',ROOT/'data/processed/dsm_views/sea_fill_v1',ROOT/'docs/sea']
    roots+=list((ROOT/'outputs').glob('sea_dev_*'))
    roots+=list((ROOT/'data/processed/shade_v1').glob('sea_fill_v1_*'))
    return sum(p.stat().st_size for root in roots if root.exists() for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def supervise(action):
    path=EVIDENCE/'ledger.json'
    if path.exists(): ledger=json.loads(path.read_text())
    else:
        previous=[json.loads((EVIDENCE/f).read_text()) for f in ['halo-counts.json','edge-diagnostic.json']]
        scan=json.loads((EVIDENCE/'territory-scan.json').read_text())
        ledger=dict(real_job_wall_seconds=sum(p['wall_seconds'] for p in previous),scan_seconds=scan['wall_seconds'],
                    peak_tree_rss_bytes=max(p['peak_rss_bytes'] for p in previous+[scan]),entries=[],
                    ceilings=dict(real_job_wall_seconds=3600,scan_seconds=1800,memory_bytes=12*1024**3,artifact_bytes=20*1024**3))
    remaining=3600-ledger['real_job_wall_seconds']-20
    if remaining<30: raise RuntimeError('Remaining real job budget cannot admit another stage')
    # Fail before starting if process metrics are unavailable.
    psutil.Process(os.getpid()).memory_info()
    psutil.Process(os.getpid()).children(recursive=True)
    started=time.monotonic()
    entry=dict(action=action,status='RUNNING',wall_seconds=0,peak_tree_rss_bytes=0)
    ledger['entries'].append(entry)
    with (EVIDENCE/f'{action}-run.txt').open('x') as log:
        proc=subprocess.Popen([sys.executable,'-m','tools.sea_view.development',action],
                              cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            process=psutil.Process(proc.pid)
            while proc.poll() is None:
                elapsed=time.monotonic()-started
                rss=0
                for p in [process]+process.children(recursive=True):
                    try: rss+=p.memory_info().rss
                    except psutil.NoSuchProcess: pass
                entry['peak_tree_rss_bytes']=max(entry['peak_tree_rss_bytes'],rss)
                entry['wall_seconds']=elapsed
                ledger['generated_bytes']=disk_bytes()
                path.write_text(json.dumps(ledger,indent=2)+'\n')
                if elapsed>=remaining or rss>=11.5*1024**3 or ledger['generated_bytes']>=19.5*1024**3:
                    raise RuntimeError('Resource watchdog stopped job before frozen ceiling')
                time.sleep(.5)
            if proc.returncode!=0: raise RuntimeError(f'Development stage {action} failed with exit {proc.returncode}')
            entry['status']='SUCCEEDED'
        except BaseException as exc:
            entry['status']='BLOCKED';entry['error']=repr(exc)
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            raise
        finally:
            entry['wall_seconds']=time.monotonic()-started
            ledger['real_job_wall_seconds']+=entry['wall_seconds']
            ledger['peak_tree_rss_bytes']=max(ledger['peak_tree_rss_bytes'],entry['peak_tree_rss_bytes'])
            ledger['generated_bytes']=disk_bytes()
            path.write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps(entry,indent=2))


if __name__=='__main__': supervise(sys.argv[1])
