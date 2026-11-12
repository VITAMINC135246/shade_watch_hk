"""python -m shade_watch {plan,run,prune} --machine machine.json region.json"""
import argparse
import json
import sys

from .config import InvalidInput
from .planning import prepare
from .runner import prune_region, run_region


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','run','prune'])
    parser.add_argument('--machine',default='config/machine.local.json')
    parser.add_argument('region')
    parser.add_argument('--yes',action='store_true',help='Delete this verified run\'s work folder (prune only)')
    args=parser.parse_args(argv)
    try:
        if args.yes and args.action!='prune':
            raise InvalidInput('--yes: only valid with prune')
        if args.action=='plan':
            result=prepare(args.region,args.machine).document
        elif args.action=='run':
            result=run_region(args.region,args.machine)
        else:
            result=prune_region(args.region,args.machine,yes=args.yes)
        print(json.dumps(result,indent=2,allow_nan=False))
        return 0
    except InvalidInput as exc:
        print(f'invalid input: {exc}',file=sys.stderr)
        return 2
    except Exception as exc:
        print(f'shade_map failed: {exc}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
