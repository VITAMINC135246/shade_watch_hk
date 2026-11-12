"""Build the DSM-only sea view or measure dependence on its fill."""
import argparse
import json
import sys


def main(argv=None):
    from shade_watch.publish.config import InvalidInput

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    build_command = commands.add_parser('build')
    build_command.add_argument('--machine', default='config/machine.local.json')
    diagnostic = commands.add_parser('fill-impact')
    diagnostic.add_argument('--machine', default='config/machine.local.json')
    diagnostic.add_argument('region')
    diagnostic.add_argument('--times', metavar='HHMM[,HHMM...]')
    args = parser.parse_args(argv)
    try:
        if args.action == 'build':
            from .build import build
            result = build(args.machine)
        else:
            from .fill_impact import fill_impact
            result = fill_impact(args.machine, args.region, times=args.times)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except InvalidInput as exc:
        print(f'invalid input: {exc}', file=sys.stderr)
        return 2
    except Exception as exc:
        print(f'sea2 failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
