"""Build DSM-only sea views or measure land-void impact."""
import argparse
import json
import sys


def main(argv=None):
    from tools.shade_map.config import InvalidInput
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    build=sub.add_parser('build'); build.add_argument('--machine',default='config/machine.local.json')
    diagnostic=sub.add_parser('void-impact'); diagnostic.add_argument('--machine',default='config/machine.local.json'); diagnostic.add_argument('region')
    args=parser.parse_args(argv)
    try:
        if args.action=='build':
            from .build import build
            result=build(args.machine)
        else:
            from .void_impact import void_impact
            result=void_impact(args.machine,args.region)
        print(json.dumps(result,indent=2,allow_nan=False))
        return 0
    except InvalidInput as exc:
        print(f'invalid input: {exc}',file=sys.stderr); return 2
    except Exception as exc:
        print(f'sea2 failed: {exc}',file=sys.stderr); return 1


if __name__=='__main__': sys.exit(main())
