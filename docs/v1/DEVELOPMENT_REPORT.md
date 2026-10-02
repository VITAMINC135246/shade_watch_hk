# V1 development verification — 2026-10-02

This is developer verification, **not independent acceptance**. The shared
contract is `SW-V1-AC-1.0`, SHA-256
`04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
Planning baseline and actual starting commit are both
`7c56760c854cb1e5138c8381a7b68d543b68cdef`, on `feature`. The delivered immutable
implementation SHA is supplied in the handoff and local
`outputs/v1_development_20261002/evidence/HANDOFF.json`; the report does not
attempt to embed its own Git commit hash.

Evidence root: [local evidence](../../outputs/v1_development_20261002/evidence/).
The pre-outcome sample manifest is `development_samples.json`; policy SHA-256 is
`62966bbbfe0e74f86a291f2a1ae844d08c4fbc841f6702f47c6c7214ba602077`.
The manifest fixes seven numerical cases on two tiles, four 24 × 20 windows,
seasonal development dates and the leap date. No hold-out acceptance cases were
used to select the default. See [policy/migration](POLICY.md), [API/CLI guide](GUIDE.md)
and [pre-implementation traceability](TRACEABILITY.md).

## Criterion decisions

| ID | Result | Observed behavior and concrete evidence |
| --- | --- | --- |
| A01 | PASS | Baseline commit/contract/source identities and installed environment recorded. All 19 DSM hashes unchanged; 4,610 protected file size/mtime signatures and 1,343 historical JSON hashes unchanged. `baseline.json`, `environment.json`, `protected_audit.json`. |
| A02 | PASS | Public plan/run models and actual CLI instant/list/two-date requests execute. Planning trap raises on any ray call, observes zero writes; real CLI planning with both media flags leaves no output directory. `tests.txt`, `cli.json`, `cli_planning.stdout.json`. |
| A03 | PASS | Off-grid seconds/microseconds, equivalent UTC/HKT, leap day, duplicate instants, DST rejection and an apparent-horizon crossing tested. Exact instants and per-tile solar parameters are in outputs. `test_exact_seconds_timezone_leap_and_daylight`, `test_actual_model_apparent_horizon_crossing`, frame metadata. |
| A04 | PASS | Exact native geometry and preserved selectors; explicit aligned custom bounds, clipped crops, uncovered custom pixels and invalid tile selection tested. Nonrectangular selections use the existing explicitly rejecting rectangle validator. `test_spatial_odd_crop_composition_invariance_and_custom`, existing geometry tests, `real_operations.json`. |
| A05 | PASS | Real shade and quality arrays are identical alone, in a two-tile composition, and in odd-offset native/custom crops. Canonical continuous horizons match exactly across synthetic odd windows; all output modes read the same native directional entries. `real_operations.json`, `test_spatial_odd_crop_composition_invariance_and_custom`. |
| A06 | PASS | Flat missing support remains 255/2, a known blocker gives 1/0 through missing coverage, target NoData stays 255/1, nighttime is 255/4. Equality and fixed-threshold priority match an independent classification oracle. `test_public_api_flat_known_blocker_missing_support_and_target`, analytic oracle tests. |
| A07 | PASS | Real cross-date and odd/custom crops make zero horizon calls. Composition reuses one tile/direction and computes only its new neighbor; synthetic additional-direction query computes one and reuses one. `real_operations.json`, direction event logs, cross-date test. |
| A08 | PASS | Relevant content change/removal/addition produce different domains; relevant changed/removed views compute one entry each; original restored domain can reuse its prior valid entry. Distant additions retain reuse, external masks/settings change identities, relocation preserves them, TIFF/JSON corruption recomputes. Dependency test and `tests.txt`. |
| A09 | PASS | Separately implemented NumPy oracle agrees on 3,360 real pixel/direction pairs: max finite angle difference 3.814e-6 degrees, zero support/valid-mask/classification disagreements. Random/analytic fixtures include missing targets/support, parity and cutoff. Real equality neighborhood: 0/3,360; synthetic explicit equality cases: 4/28 finite comparisons (35 total including missing targets), strict comparison retained. `numerical.json`, `arrays_case_*.npz`, `tests/v1_oracle.py`. |
| A10 | PASS | Nearest 5°, nearest 2.5° and direct unbinned rays compared on frozen real windows, with errors, denominators, masks, examples, time/storage. Narrow one-cell synthetic blocker is missed by both finite tables. Default and limitations below. `numerical.json`, narrow-blocker test. |
| A11 | PASS | Native 1200 × 1500 rasters, 0.5 m/EPSG:2326, transforms, nodata and encodings read back; all quality validity masks agree. Optional JPG-only and MP4-only real cases plus combined synthetic media run; frame count/times checked. Bounded allocation and peak RSS recorded, measurement gaps disclosed below. `benchmarks.json`, `real_operations.json`, output/media indexes. |
| A12 | PASS | Actual isolated child exits after one complete entry; restart skips it and computes the partial second entry. Competing lock rejects another writer; corrupt final raster rebuilds. All 53 tests pass; unchanged legacy command runs 65 real small-window frames and decoded video, into new paths. `tests.txt`, `legacy_smoke.json`, legacy log. |
| A13 | PASS | Three genuinely empty native scientific-cache trials versus three new-output warm directional queries: cold median 10.435 s, warm median 0.570 s. Each cold computes one; each warm reuses one and has zero final hits. Final-result hits separately measured. Phase/job/byte/memory evidence and confounds recorded. `benchmarks.json`, `ledger.json`. |
| A14 | PASS | Necessary code/tests, this report, guide, frozen policy, migration, evidence manifest and immutable local implementation handoff delivered; large data/cache/output remain ignored. `manifest.json`, `HANDOFF.json`, local implementation commit. |

## Software and scientific numerical consistency

The existing regression suite had 30 passing tests. The final suite has **53
passing tests**, 6.87 s, with existing dependency deprecation warnings recorded
in `tests.txt`. Production V1 shares only the established kernel/classifier with
legacy; the independent oracle calls neither. Its remaining shared assumptions
are DSM input I/O, adopted ray model, rounding/cutoff conventions and float32
height subtraction. Analytic blocker first-hit distance, flat scenes and cutoff
fixtures validate the oracle before random/real comparisons.

The real two-date sequence has four clock-aligned frames across 2026-01-07 and
2026-06-21 at 360-minute intervals. The complete native query and two-tile query
retain full scientific resolution. Actual CLI planning/instant/list/date commands
are preserved verbatim in `cli.json`; no shared configuration was mutated.

## Directional and solar approximations

Seven windows total **3,360 pixel/direction pairs**, all with finite targets in
these chosen windows; invalid-mask differences are zero and no equality pixels
are excluded. Nighttime remains in the denominator. This sample is development
evidence, not a representative territory accuracy estimate.

| Method | Maximum horizon error | Shade disagreement / 3360 | Quality disagreement / 3360 | Window work incl. input I/O |
| --- | ---: | ---: | ---: | ---: |
| direct vs independent oracle | 0.000003814° | 0 | 0 | 1.046 s |
| nearest5 | 76.4613° | 106 (3.155%) | 41 (1.220%) | 0.741 s |
| nearest2_5 | 32.3163° | 79 (2.351%) | 4 (0.119%) | 0.745 s |

The arrays and per-case coordinates identify concentrated building-edge errors;
the maxima are not hidden as numerical noise. Both finite tables miss the
synthetic narrow blocker between directions. Nearest2_5 improves these cases but
does not guarantee improvement for every pixel. **V1 retains the named nearest5
default**, preserving the documented baseline and bounded directional storage;
nearest2_5 and direct are explicit alternatives. No accuracy threshold was
agreed and these measurements do not establish physical accuracy.

A native three-band direction uses 21,600,000 uncompressed data bytes: full 5°
and 2.5° tables would have 72 and 144 entries respectively. On-demand queries
compute only needed directions; direct has no finite fixed-table size.

For these development windows, tile-centre apparent elevations differ from
per-pixel use of the same solar model by up to **0.002411°**. At the studied native
reference boundary the centre-model elevation jump is up to **0.006611°**, versus
about **0.0000044°** between adjacent per-pixel references; fixed tile thresholds
differ by **3.232701°**. These are policy boundaries, separate from computational
seams. Composition tests demonstrate invariant ownership, not absence of
reference discontinuities.

The preserved fractional-year solar model differs from independently transcribed
NOAA Julian-century/Meeus equations by up to **0.451893° geometric elevation** and
**0.451474° azimuth** in this set. This is algorithm comparison, not observed sky
accuracy. Primary source [NOAA equations/calculator details](https://gml.noaa.gov/grad/solcalc/calcdetails.html)
and [calculator source](https://gml.noaa.gov/grad/solcalc/main.js) are identified in
the raw evidence; downloaded source SHA-256 is
`3832956f24724eafacf9e18173b9299b1554d6252bed0784d9c9aca6d9f54856`.

## Performance and resource ledger

Mac arm64/macOS 15.7.4, Python 3.12.5; exact installed package versions and
machine memory/CPU inventory are in environment/baseline evidence. One real
worker/process, synthetic JIT preload, existing Numba disk code cache and no
filesystem-cache flushing. Native signature loading/JIT, hashing, cache
validation, output compression/readback are included in run timing; planning is
separate. Classification and output/validation are individually instrumented.
The third cold trial overlapped roughly five seconds of synthetic regression
tests; the first two pairs were otherwise isolated. No real DSM jobs overlapped.

Final-result hits are measured separately (approximately 0.28–0.31 s wall) and
do not count as warm-direction trials. The warm median remains below the cold
median under identical native scientific/output settings. This is a local
measurement, not a territory scaling estimate or promised speedup.

Actual cumulative real-job wall time: **105.678 s / 3600 s ceiling**. New artifacts:
about **77.1 MiB / 10 GiB ceiling**. Sampled campaign parent/tree peak:
**613.7 MiB / 8 GiB ceiling**, sampled every 20 ms. Legacy subprocess measurements
are separately available in its result inventory; the outer ledger does not
include that subprocess in its own process tree. V1 has no separate worker;
allocations are in the parent. Known media PIDs enter tree RSS when tracking
succeeds; a separate media-only maximum is not measured. These sampling gaps are
explicit, and conservative admission estimates bound native allocations.

## Reproduce and hand off

```sh
.venv/bin/python -m pytest -q --disable-warnings
.venv/bin/python tools/v1_development.py all
git rev-parse HEAD
```

The measurement tool does not silently reuse a populated cache as a cold trial.
Completed stages are retained rather than rerun; a new campaign needs its own
frozen baseline/sample manifest. Each stage writes phase measurements, hashes,
arrays or logs and updates the cumulative ledger. Independent acceptance must
freeze new seasonal times/windows, use its own namespace and target the supplied
immutable SHA. Developer outcomes do not grant an acceptance gate.

Real-world observational validation: **NOT VERIFIED — no suitable registered
independent observations were used**. No V2/V3 work or public deployment is
authorized by this developer handoff.
