#!/bin/sh
# Run from the project root after HK-1 and the synthetic tests.
set -eu
export PYTHONDONTWRITEBYTECODE=1 PROJ_NETWORK=OFF
scratch=/private/tmp/sw-g1-3531437
export NUMBA_CACHE_DIR="$scratch/numba"
evidence=docs/city/evidence
configs="$evidence/configs"
python=.venv/bin/python
machine="$configs/machine.json"

measure() {
    job=$1
    category=$2
    shift 2
    "$python" "$evidence/measure.py" --baseline "$scratch/before.json" --job "$job" --category "$category" -- "$@"
}

for n in 2 3 4; do
    measure "HK-$n" shade "$python" -m docs.city.evidence.campaign "hk$n" > "$evidence/hk$n-result.json"
    measure "HK-$n-compare" shade "$python" "$evidence/compare_hk.py" "$n" > "$evidence/hk$n-comparison.json"
done

measure "HK-compatibility-plans" shade "$python" -m docs.city.evidence.campaign compatibility > "$evidence/legacy-plans.json"
measure "NL-0" registration "$python" -m tools.city register rotterdam --machine "$machine" > "$evidence/nl0-registration.json"
measure "NL-1-plan" shade "$python" -m tools.shade_map plan --machine "$machine" "$configs/nl1.json" > "$evidence/nl1-plan.json"
measure "NL-1" shade "$python" -m tools.shade_map run --machine "$machine" "$configs/nl1.json" > "$evidence/nl1-result.json"
measure "NL-2" shade "$python" -m docs.city.evidence.campaign nl2 > "$evidence/nl2-result.json"
measure "NL-3-plan" shade "$python" -m tools.shade_map plan --machine "$machine" "$configs/nl3.json" > "$evidence/nl3-plan.json"
measure "NL-3" shade "$python" -m tools.shade_map run --machine "$machine" "$configs/nl3.json" > "$evidence/nl3-result.json"
measure "NL-4" shade "$python" -m tools.sea2 fill-impact --machine "$machine" "$configs/nl1.json" --times 0900,1330,1800 > "$evidence/nl4-result.json"
for case in edge dst; do
    measure "NL-5-$case" shade "$python" -m tools.shade_map plan --machine "$machine" "$configs/nl5-$case.json" > "$evidence/nl5-$case-plan.json"
done
