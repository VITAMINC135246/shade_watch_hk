"""Warm-cache gates and the NL-2 and compatibility entry points."""
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from tools.shade_map import plan_shade_map, shade_map
from tools.shade_map.common import atomic_json, read_json
from tools.shade_map.planning import prepare
from tools.shade_map.runner import run_region

EVIDENCE = Path(__file__).resolve().parent
CONFIGS = EVIDENCE / "configs"
MACHINE = CONFIGS / "machine.json"


def warm_hk(number):
    config = CONFIGS / f"hk{number}.json"
    prepared = prepare(config, MACHINE)
    plan = prepared.document
    cache_tasks = [task["payload"] for batch in prepared.batch_plans
                   for task in batch.definition["tasks"] if task["kind"] == "horizon"]
    gates = [dict(cache=t["cache"], spatial_key=t["key"], missing=t["missing_directions"],
                  lock_exists=(Path(t["cache"]) / t["key"] / ".writer.lock").is_file())
             for t in cache_tasks]
    atomic_json(EVIDENCE / f"hk{number}-plan.json", dict(plan, cache_gates=gates))
    if (not gates or plan["missing_direction_jobs"]
            or any(gate["missing"] or not gate["lock_exists"] for gate in gates)):
        raise SystemExit(f"HK-{number} stopped before execution: incomplete protected horizon cache")
    return run_region(config, MACHINE)


def nl2():
    region = read_json(CONFIGS / "nl2.json")
    args = region["lower_left"], region["upper_right"], region["time"]
    kwargs = dict(name=region["name"], city="rotterdam", machine=MACHINE)
    atomic_json(EVIDENCE / "nl2-plan.json", plan_shade_map(*args, **kwargs))
    return shade_map(*args, **kwargs)


def compatibility():
    result = {}
    for name, config in [
        ("cheung_chau", "config/regions/cheung_chau.json"),
        ("legacy_without_source", CONFIGS / "legacy-no-source.json"),
    ]:
        prepared = prepare(config, "config/machine.local.json")
        assert prepared.region["dsm_source"] == "raw"
        assert prepared.document["city"]["city_id"] == "hong_kong"
        result[name] = dict(provider=prepared.identity_document["source_identity"]["provider"],
                            plan=prepared.document)
    return result


def rejections():
    base = read_json(CONFIGS / "nl1.json")
    wrong_order = dict(base, lower_left=base["upper_right"], upper_right=base["lower_left"])
    no_city = {k: v for k, v in base.items() if k != "city"}
    cases = dict(unknown_city=dict(base, city="absent_city"),
                 outside=dict(base, lower_left=[89000, 431000]), no_city=no_city,
                 wrong_crs=dict(base, crs="hk1980"), wrong_order=wrong_order)
    for key, instant in (("offset", "2026-06-21T13:30+01:00"), ("spring_gap", "2026-03-29T02:30"),
                         ("fall_fold", "2026-10-25T02:30")):
        cases[key] = dict(base, time=dict(mode="instants", instants=[instant]))
    result = {}
    with TemporaryDirectory() as temp:
        for key, case in cases.items():
            path = Path(temp) / (key + ".json")
            atomic_json(path, dict(case, name="g1_dev_invalid_" + key))
            command = [sys.executable, "-m", "tools.shade_map", "run", "--machine", str(MACHINE), str(path)]
            run = subprocess.run(command, text=True, capture_output=True)
            assert run.returncode == 2 and run.stderr.startswith("invalid input:") and not run.stdout
            result[key] = dict(region=case, exit_code=run.returncode, stderr=run.stderr.strip())
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=["hk2", "hk3", "hk4", "nl2", "compatibility", "rejections"])
    case = parser.parse_args().case
    if case.startswith("hk"):
        result = warm_hk(int(case[-1]))
    else:
        result = {"nl2": nl2, "compatibility": compatibility, "rejections": rejections}[case]()
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
