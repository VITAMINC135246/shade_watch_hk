"""Measure the remaining readbacks and report-only validation separately."""
import argparse
from pathlib import Path
import shutil

from campaign import Campaign, CONFIGS, EVIDENCE, MACHINE, PYTHON, ROOT, TOOLS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['view','keys','cheung_chau','central','five_class','validation','tests','inventory'])
    parser.add_argument('--scratch',type=Path,required=True)
    args = parser.parse_args()
    campaign = Campaign(args.scratch)
    if args.action == 'validation':
        work = ROOT/'outputs/sea2_2_validation'
        try:
            campaign.measure('validation','validation',
                [TOOLS/'bin/python','-m','tools.sea2.validate_ib5000','--machine',MACHINE,
                 '--scopes',CONFIGS/'validation_scopes.json','--work',work])
        finally:
            for path in (work/'reports').glob('*.json'):
                shutil.copyfile(path,EVIDENCE/path.name)
    elif args.action == 'inventory':
        campaign.measure('inventory-after','setup',[PYTHON,EVIDENCE/'inventory.py','after',campaign.before])
    elif args.action == 'tests':
        campaign.measure('pytest-resume','tests',[PYTHON,'-m','pytest','tests','-q',
                         '-o',f'cache_dir={args.scratch}/pytest','--basetemp',args.scratch/'final-tests'])
    else:
        campaign.measure('audit-'+args.action,'real',[PYTHON,EVIDENCE/'audit_real.py',args.action])


if __name__=='__main__':
    main()
