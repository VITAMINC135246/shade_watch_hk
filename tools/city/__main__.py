"""Register a city's native DSM catalogue and build its 0 m fill view."""
import argparse
import json
import sys

from tools.shade_map.config import InvalidInput
from .ingest import register


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["register"])
    parser.add_argument("city")
    parser.add_argument("--machine", default="config/machine.local.json")
    args = parser.parse_args(argv)
    try:
        result = register(args.city, args.machine)
    except InvalidInput as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"city registration failed: {exc}", file=sys.stderr)
        return 1
    for warning in result["registration_report"]["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
