# V2 development verification

Development verification: **B01–B14 PASS**. This is an implementation handoff,
not independent acceptance. The independent reviewer must pin the full local
implementation SHA supplied in `outputs/v2_development/evidence/HANDOFF.json`
and choose additional cases. No V3, push, merge or deployment is included.

## Baseline and frozen contract

Starting commit: `f0598140c735786fba7d0b193c57b2aaa8564825`, branch `feature`.
Accepted V1: `796ac8abf05b92f1fbbac23a4aa0f18c9d944101`.
Accepted report: `docs/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md`, SHA-256
`cc7a9f2fd0d1db5c3ae6339742f703cbf68a3ed2dd3188072110e6d46c005510`.
Planning baseline `7c56760c854cb1e5138c8381a7b68d543b68cdef` was not treated
as an implementation. V1 contract hash
`04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`;
V2 SW-V2-AC-1.0 hash
`236198cdc0cc202d5e4278b6db7baa7c79c3ef710d123faa51b1683e5537b0ac`.
Contracts were not amended. [DESIGN.md](DESIGN.md) was written before code.

Existing macOS 15.7.4 arm64/Python 3.12.5 environment, 10 logical CPUs, 24 GiB,
local HFS volume and the existing 19 DSM files were used. No dependency or raw
data download. Initial source/auxiliary identities, dirty files, protected file
signatures and budgets are recorded in `outputs/v2_development/evidence/baseline.json`.
The final protection audit matches all 19 raw TIFF hashes and 7,955 protected
file signatures. Unrelated `presentations/`, V3 prompts and other projects remain
outside this commit/work. All generated data/databases are ignored.

## Verification matrix

Evidence root: `outputs/v2_development/evidence/`. The checked-in test suite
contains **68 passing tests**, 366 existing dependency warnings, 28.88 s at the
final full-suite run. A final estimator-domain restriction does not change
execution; exact final engine hashes and real executions are retained below.

| ID | Development result | Concrete evidence and behavior |
| --- | --- | --- |
| B01 | PASS | Accepted predecessor/report and both contract hashes frozen; `baseline.json`, `protection_audit.json`, design and unchanged numerical-source audit. |
| B02 | PASS | V1-compatible planning plus durable named batch APIs. Actual six CLI actions in `cli.json`; planning trap/inventory tests prove zero scientific/media writes and one catalogue per source directory. |
| B03 | PASS | Transactional immutable definitions/graph, legal transitions and attempt history. Fresh child process reopens cancelled/crashed state; success requires controller-validated artifacts. State/fresh-process/partial-publication tests. |
| B04 | PASS | Overlapping dates/crops/tile selections share native direction unions while retaining distinct metadata/results. Two-worker overlap and actual contending writer tests; synthetic calls=2 for two source tiles, warm real optimization reuses one union. |
| B05 | PASS | Actual owned worker and controller termination, cooperative active cancellation and publisher exit after first raster rename. Restart preserves completed directions, repairs missing output/cache and leaves an unrelated sentinel process alive. Original failure attempts remain. |
| B06 | PASS | Removed input, corrupt cache/output, simulated ENOSPC publication and unavailable media encoder tested. Permanent/transient categories and fixed attempt ceiling; two worker losses exhaust exactly two attempts. Media repair runs zero horizons and preserves scientific hashes. |
| B07 | PASS | One/two-worker real and synthetic jobs; preflight rejects over-budget concurrency. 8/32-request queues complete at one in-flight task with <64 MiB parent metadata growth and no raster payloads. Known-PID memory sampling and temporary/retained disk bounds enforced; gaps below. |
| B08 | PASS | Immutable accepted-V1 source snapshot versus V2 on real native tiles, UTC/HKT-equivalent leap instant, night, odd-offset crops, output combinations/order and one/two workers. Separate new cold cache matches all 3.6 million finite native horizon pixels exactly; support/finite masks and shade/quality exact. `regression.json`, `cold_regression.json`. |
| B09 | PASS | Scientific-only versus JPG-enabled crop/combined/logical views match accepted pixels/transforms. Native-boundary logical sample matches adjoining rasters. Separate media/statistics/index tasks; failed MP4 repair leaves scientific hashes unchanged. |
| B10 | PASS | Frozen model `ad6939e...1469`; cold/warm/mixed >=10 s, no final-result-only hits. Original median/max APE=13.05/20.08%; final-code revalidation=14.16/19.33%. Every predicted resource ceiling covers the corresponding observation. `holdouts.json`, `candidate_holdouts.json`, pre-run predictions/manifests. |
| B11 | PASS | Projection requires tile/effective-pixel/direction/query/cache/output/hardware/worker assumptions; ranges/exclusions and extrapolation flag explicit. `projection.json`, estimator guide and public `project_territory`. No territory run or territory accuracy claim. |
| B12 | PASS | Three matched accepted-V1/V2 warm native queries: full catalogue calls 6 -> 2, same science, no final hits. Recorded end-to-end 3.929 -> 2.755 s; instrumented redundant work reduction is the supported claim. `optimization.json`; confounds/regressions below. |
| B13 | PASS | Scheduler/failure/inherited tests, predeclared calibration/hold-out manifests, bounded multi-tile/multi-date/mixed real batches and exact accepted-code comparisons. Independent review must use new case provenance. |
| B14 | PASS | Code/tests, API/CLI examples, state/recovery/compatibility guide, frozen model, measurements, evidence/sample inventory and local immutable commit handoff. No datasets/databases/cache/output in Git. |

## Numerical consistency and limitations

`horizon.py`, `spatial.py`, `v1_cache.py`, `solar.py` and `shade_watch.py` are
byte-identical to accepted V1. The only V1 API change is a private request-local
catalogue argument used by V2 planning. V1 execution still validates its inputs.
The V2 scheduler supplies relevant buffered sources and groups all required
directions once per tile; it never changes precision, ray spacing, direction
spacing, solar policy, uncertainty policy or timestamp selection.

Real separate-cache comparisons used 11NE10B/11NE10D at 200°: each 1,800,000
finite targets, maximum angle difference 0°, support/finite-mask differences 0.
Scientific arrays match at native resolution, including an odd 903/703 crop and
the shared native boundary. Equality-neighbourhood counts (1e-4° reporting only,
strict comparison retained) are saved in every frame and `regression.json`.
Native/cropped output and logical sampling agree on transforms and quality masks.

Inherited finite-direction, fixed tile-centre solar and 1 km search limitations
remain those in V1 policy/acceptance. V2 numerical consistency does not reduce
directional/astronomical approximation error or establish observational accuracy.
Real-world shade validation: **NOT VERIFIED — no registered independent
observations**. Whole-Hong-Kong production readiness is outside V2.

## Measurement and resource ledger

Actual real-job wall time: **386.295 s / 7200 s ceiling** (6 min 26 s), including
calibration, accepted-V1 references, new-cache regression, matched optimization,
warm-cache setup, hold-outs/revalidation and CLI run/resume. Initial inventory,
output-only comparisons and synthetic tests are separately scoped. Generated
artifacts, including example CLI state/cache/output: approximately **420.0 MiB /
20 GiB**. Conservative observed parent-plus-reported-job peak: approximately
**1.49 GiB / 12 GiB**. `ledger.json` records every real job and failures/reservations.

Twenty-millisecond controller/worker sampling uses known PIDs, without system-wide
enumeration. Parent/worker/media peaks are separately reported where observable;
worker task metrics include known ImageIO encoder/decoder RSS. Input admission
and process spawn precede the continuous loop and use start/end samples plus
allocation ceilings. Sub-sample spikes and a separate very-short-media peak can
be missed. The outer CLI harness does not enumerate grandchildren, so its parent
peak plus the CLI controller's reported job peak provides a conservative bound.
This is sampled local control, not a cgroup or power-loss guarantee.

The estimator separates CPU-direction and output concurrency. Calibration and
the first three hold-outs used a scheduler prior to final strict-JSON/journal
invariant/monitoring improvements; final engine hashes and identical-case
revalidation are retained in `candidate_revalidation_manifest.json`. Coefficients
were unchanged and all first/repeated outcomes retained. None of those cases may
be presented as the independent review's untouched samples.

The matched warm optimization overlapped some synthetic regression work; its
timings are descriptive. The six-to-two catalogue count reduction is direct
instrumentation. Process startup, transactions, extra integrity checks and
verification can regress very small warm requests versus single-process V1;
no fixed speedup is promised. Four workers were not benchmarked; other media,
terrain, source tiles and territory estimates remain extrapolated/provisional.

## Reproduction and handoff

```sh
.venv/bin/python -m pytest -q --disable-warnings
.venv/bin/python tools/v2_development.py all
.venv/bin/python -m src.v2 plan --requests docs/v2/example_batch.json
git rev-parse HEAD
```

The retained campaign refuses to overwrite measured case records. A fresh replay
needs new campaign output/cache namespaces and a fresh ledger/manifest; the
harness constants may be routed to those owned directories before invocation.
Do not rerun destructive fixture stages against original evidence. Exact CLI
commands, plans, source identities, predictions, outcomes, code hashes and raw
event/attempt journals are preserved. `manifest.json` inventories evidence;
`HANDOFF.json` supplies the actual local implementation SHA after commit.

Observed implementation fixes include dependent-output invalidation on recovery,
accurate final-hit missing-work planning, quota/media isolation, strict NaN NoData
metadata, immutable definition triggers and no-op memory reporting. Development
harness injection timing was corrected when the controller was initially stopped
between tasks; the process-loss assertions then explicitly reached RUNNING work.
No contract threshold or scientific policy was weakened. Independent acceptance
is the next release gate; defects require a new candidate commit and reacceptance.
