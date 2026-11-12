"""Check the candidate's staged files and the cumulative F diff."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
START = '5b1da9be4246acac53b0488c3587df7884941108'
ENGINE = '356f611d7b775ce31006904b80ca31d3c1c484b2'
ADAPTER = 'f5f24acc4163aa1353534d5db5a5dbe30faf0dae'
F1 = '35225fd9547a00e4df202e7ab30204c633b2c845'
B20 = '5744e2301eea34f8bae05b9df3e14508425b8282'
F_PATHS = ('tools/shade_map/', 'config/schema/shade_map_*.json', 'config/machine.example.json',
           'config/regions/', 'tests/test_shade_map.py', 'tests/shade_map_campaign.py',
           'tests/shade_map_repair_campaign.py', 'docs/shade_map/GUIDE.md','docs/shade_map/DESIGN.md')
F_ALLOWED = {'tools/shade_map/sources.py','tools/shade_map/publication.py',
             'config/schema/shade_map_region.schema.json','config/schema/shade_map_machine.schema.json',
             'config/machine.example.json','docs/shade_map/GUIDE.md','docs/shade_map/DESIGN.md'}
SEA_FILES = {'config/schema/fill_impact.schema.json','config/schema/void_impact.schema.json',
             'docs/sea2/POLICY.md','docs/sea2/GUIDE.md','docs/sea2/DESIGN.md','docs/sea2/DEVELOPMENT_REPORT_B2_2.md'}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scope(candidate=None):
    assert git('branch','--show-current').decode().strip()=='feature'
    compare = ('--cached',) if candidate is None else (candidate,)
    if candidate is None:
        assert git('rev-parse','HEAD').decode().strip()==START
    else:
        assert git('rev-parse',candidate+'^').decode().strip()==START
    staged = git('diff','--name-only','-z',START,*compare).decode().strip('\0').split('\0')
    for path in staged:
        assert (path in F_ALLOWED or path in SEA_FILES or
                path.startswith(('tools/sea2/','docs/sea2/evidence/b2_2/')) or
                (path.startswith('tests/test_sea2_') and path.endswith('.py'))), path
    assert not git('diff',START,*compare,'--','src/','tools/region_request.py')
    protected = ('tools/sea_view/','docs/sea/','tests/test_sea_masks.py',
                 'docs/sea2/DEVELOPMENT_REPORT.md','docs/sea2/evidence/',
                 ':(exclude)docs/sea2/evidence/b2_2/', 'docs/prompts/','docs/planning/',
                 'docs/OUTPUT_CODES.md','config/sea_profiles/','config/schema/sea_profile.schema.json')
    assert not git('diff',START,*compare,'--',*protected)
    prior = json.loads((EVIDENCE/'start.json').read_text())
    pinned = {p:sha(git('show',ENGINE+':'+p)) for p in prior['pinned_engine_hashes']}
    assert pinned == prior['pinned_engine_hashes'] == {p:sha((ROOT/p).read_bytes()) for p in pinned}
    assert sha(git('show',ADAPTER+':tools/region_request.py')) == sha((ROOT/'tools/region_request.py').read_bytes())
    subprocess.run(['git','merge-base','--is-ancestor',B20,START],cwd=ROOT,check=True)
    contract = ROOT/'docs/prompts/B2/CONTRACT_B2_2.md'
    assert sha(contract.read_bytes())==prior['expected_contract_sha256']
    assert git('show',START+':docs/prompts/B2/CONTRACT_B2_2.md')==contract.read_bytes()
    changed_f = set(git('diff','--name-only',F1,*compare,'--',*F_PATHS).decode().splitlines())
    assert changed_f==F_ALLOWED, changed_f
    expected = git('show',F1+':tools/shade_map/publication.py').replace(
        b'([0,1,255], list(map(int,v1.QUALITY)), [0,1,255])',
        b'([0,1,255], list(map(int,v1.QUALITY)), [0,1,2,3,4,255])')
    assert expected==(ROOT/'tools/shade_map/publication.py').read_bytes()
    assert git('show',B20+':tools/shade_map/sources.py').replace(b"'sea-2.0'",b"'sea-2.2'") == (ROOT/'tools/shade_map/sources.py').read_bytes()
    return dict(start=START,cumulative_f_base=F1,staged_paths=len(staged),allowed_paths=True,
                pinned_engine=pinned, adapter_sha256=prior['adapter_sha256'],
                cumulative_f_files=sorted(changed_f), publication_only_surface_allowlist=True,
                protected_tracked_diff_empty=True,contract_sha256=sha(contract.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate')
    args = parser.parse_args()
    result = scope(args.candidate)
    if args.candidate is None:
        (EVIDENCE/'scope.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    else:
        print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
