"""Run the frozen B2.2 development jobs under a separate resource watchdog."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
CONFIGS = EVIDENCE/'configs'
MACHINE = CONFIGS/'machine.json'
PYTHON = ROOT/'.venv/bin/python'
TOOLS = Path.home()/'venvs/shade_watch_tools'
F1 = '35225fd9547a00e4df202e7ab30204c633b2c845'
REGIONS = ('cheung_chau','central','five_class')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


class Campaign:
    def __init__(self, scratch):
        self.scratch = scratch
        self.before = scratch/'protected.json'
        self.output = ROOT/read(MACHINE)['output_root']

    def measure(self, name, category, command, *, cwd=ROOT, expected=0):
        log = EVIDENCE/(name+'.txt')
        launcher = [str(PYTHON), '-m', 'tools.sea2.resources', '--label', name, '--category', category,
                    '--cwd', str(cwd), '--log', str(log)]
        if self.before.exists():
            launcher += ['--protected-before',str(self.before),
                         '--extra-artifacts',str(self.scratch),'--extra-artifacts',str(TOOLS)]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PROJ_NETWORK='OFF',
                   NUMBA_CACHE_DIR=str(self.scratch/'numba'), TMPDIR=str(self.scratch),
                   GDAL_DISABLE_READDIR_ON_OPEN='TRUE')
        print(f'B2.2 starting {name}',flush=True)
        process = subprocess.Popen([*launcher,'--',*map(str,command)],cwd=ROOT,env=env)
        try:
            status = process.wait()
        except InterruptedError:
            process.terminate()
            process.wait()
            raise
        if status != expected:
            print(log.read_text()[-4000:],file=sys.stderr,flush=True)
            raise RuntimeError(f'{name} exited {status}, expected {expected}')
        return log

    def python(self, name, category, module, *args, **options):
        return self.measure(name,category,[PYTHON,'-m',module,*args],**options)

    def setup(self):
        if self.before.exists() or (EVIDENCE/'resources.jsonl').exists():
            raise RuntimeError('The development ledger or before inventory already exists')
        baseline = self.scratch/'f1_baseline'
        baseline.mkdir()
        archive = self.scratch/'f1_baseline.tar'
        try:
            subprocess.run(['git','archive','--format=tar','-o',archive,F1,'src','config',
                            'tools/shade_map','tools/region_request.py','docs/v2/estimator.json'],
                           cwd=ROOT,check=True)
            subprocess.run(['/usr/bin/tar','-xf',archive,'-C',baseline],check=True)
        finally:
            archive.unlink(missing_ok=True)
        machine = read(MACHINE)
        machine.pop('sea_profile')
        machine.update(dsm_dir=str(ROOT/machine['dsm_dir']),output_root='outputs/sea2_2_f1_plan')
        write(baseline/'machine.json',machine)
        self.measure('inventory-before','setup',[PYTHON,EVIDENCE/'inventory.py','before',self.before])

    def raw_plans(self):
        baseline = self.scratch/'f1_baseline'
        reference = ROOT/'outputs/shade_map_f1_20261031/f1_cheung_chau'
        expected = {
            'default': 'c196a09a3a213e0720b8dcb5ea5b4edb32ad217fcabcb70a930a9b17b458878e',
            'f1_reference': 'e608af7ffe4181f3d097ce3f776f464b5b79fc67f1c1e5dc12bc6806a421b1ca',
        }
        # This copy is outside outputs/ and preserves the accepted run's name.
        config = CONFIGS/'f1_cheung_chau_reference.json'
        self.measure('copy-f1-reference','real',['/bin/cp',reference/'region_config.json',config])
        raw = {}
        for name, region in [('default',ROOT/'config/regions/cheung_chau.json'),('f1_reference',config)]:
            old = read(self.python(f'raw-plan-{name}-f1','real','tools.shade_map','plan',
                                   '--machine',baseline/'machine.json',region,cwd=baseline))
            new = read(self.python(f'raw-plan-{name}-candidate','real','tools.shade_map','plan',
                                   '--machine',MACHINE,region))
            raw[name] = dict(expected=expected[name], f1=old['run_id'], candidate=new['run_id'],
                             frames=len(new['frames']), matches=old['run_id']==new['run_id']==expected[name])
        central = read(self.python('raw-plan-central-reference','real','tools.shade_map','plan',
                                   '--machine',MACHINE,CONFIGS/'central_raw_reference.json'))
        prior = read(ROOT/'outputs/sea2_f_20261104/sea2_central_raw/run_manifest.json')
        raw['central_reference'] = dict(candidate=central['run_id'], historical=prior['run_id'],
                                        matches=central['run_id']==prior['run_id'] and prior['status']=='complete')
        write(EVIDENCE/'raw-plan-identity.json', raw)
        if not raw['central_reference']['matches']:
            raise RuntimeError('The stored Central raw reference differs from the candidate raw plan')

    def science(self):
        if not self.before.exists():
            raise RuntimeError('Capture the protected baseline before development jobs')
        if (ROOT/'data/processed/dsm_views/sea_fill_v2_2').exists() or self.output.exists():
            raise RuntimeError('The development view and publication namespaces must be fresh')
        with coastline_denied():
            self.python('territory-view-build','build','tools.sea2','build','--machine',MACHINE)
            self.measure('view-preflight','real',[PYTHON,EVIDENCE/'view_preflight.py'])
            self.raw_plans()
            for name, frames in zip(REGIONS, (65,3,3)):
                region = CONFIGS/(name+'.json')
                plan = read(self.python(f'{name}-plan','real','tools.shade_map','plan','--machine',MACHINE,region))
                if len(plan['frames'])!=frames or plan['existing_run']['status']!='new':
                    raise RuntimeError(f'Unexpected frame count or run identity for {name}')
                self.python(f'{name}-run','real','tools.shade_map','run','--machine',MACHINE,region)
            for name, times in [('cheung_chau',['--times','0720,1230,1740']),('five_class',[])]:
                region = CONFIGS/(name+'.json')
                self.python(f'{name}-fill-impact','real','tools.sea2','fill-impact','--machine',MACHINE,region,*times)
            self.python('five_class-fill-impact-resume','real','tools.sea2','fill-impact','--machine',MACHINE,
                        CONFIGS/'five_class.json')


@contextmanager
def coastline_denied():
    coast = ROOT/'data/raw/coastline'
    mode = stat.S_IMODE(coast.stat().st_mode)
    evidence = dict(original_mode=oct(mode))
    try:
        if coast.is_symlink() or not mode:
            raise RuntimeError('Coastline must be a readable, local directory before the test')
        coast.chmod(0)
        evidence['blackout_mode'] = oct(stat.S_IMODE(coast.stat().st_mode))
        try:
            with (coast/'README.md').open('rb') as stream:
                stream.read(1)
        except PermissionError as exc:
            evidence['read_probe'] = dict(denied=True, errno=exc.errno, path='data/raw/coastline/README.md')
        else:
            raise RuntimeError('Coastline read probe unexpectedly succeeded')
        write(EVIDENCE/'coastline-access.json', evidence)
        yield
    finally:
        if 'blackout_mode' in evidence:
            coast.chmod(mode)
        evidence['restored_mode'] = oct(stat.S_IMODE(coast.stat().st_mode))
        write(EVIDENCE/'coastline-access.json', evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['setup','science'])
    parser.add_argument('--scratch',type=Path,required=True)
    args = parser.parse_args()
    if not args.scratch.resolve().is_relative_to(Path('/private/tmp')):
        raise RuntimeError('Use a dedicated scratch directory under /private/tmp')

    def stop(signum, _frame):
        raise InterruptedError(signal.Signals(signum).name)

    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):
        signal.signal(sig,stop)
    campaign = Campaign(args.scratch)
    getattr(campaign,args.action)()


if __name__=='__main__':
    main()
