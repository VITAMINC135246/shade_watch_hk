# Pre-implementation traceability

Contract hash is recorded in [POLICY.md](POLICY.md). The initial inventory is
`outputs/v1_development_20261002/evidence/baseline.json` (ignored local evidence).
The baseline regression suite is 30 passing tests (11.91 s). Baseline CLI,
fixed-date and scientific limitations are documented in the existing method
and individual-tile guides. Historical six-tile timings are context, not a
matched V1 performance comparison.

| ID | Planned implementation | Planned evidence |
| --- | --- | --- |
| A01 | isolated paths; source identities | baseline and final protected-input audits |
| A02 | `src/v1.py` models, planner, runner, CLI | real public API/CLI and zero-call planning trap |
| A03 | normalized exact instants; solar metadata | seconds, UTC/HKT, leap dates, near-horizon tests |
| A04 | native selection; aligned custom; crop | metadata, selector, hole and alignment cases |
| A05 | absolute parity; per-tile science | odd crop and combined-output comparisons |
| A06 | unchanged labels and conservative reasons | analytic flat/blocker/gap/NoData/night fixtures |
| A07 | `src/v1_cache.py` directional entries | instrumented cross-date/range and missing direction |
| A08 | content-based buffered dependencies | fixture change/remove/add/distant/mask/corruption |
| A09 | independent ray oracle in tests/tools | analytic oracle validation and exact-direction metrics |
| A10 | named 5-degree/2.5-degree/direct choices | frozen development windows, errors and denominators |
| A11 | windowed rasters and switchable media | output readback; memory monitor and artifact ledger |
| A12 | lock/atomic/checksum recovery | stopped isolated process; legacy real smoke |
| A13 | instrumented phases and cache tiers | three native cold/warm pairs and result hits |
| A14 | guide, policy, reports, immutable commit | reviewed staged diff and independent handoff |

Development real-data allocation: full-native one-direction queries (cold/warm
trials), a bounded multi-date request, small-window approximation/reference
calculations and a small legacy daylight smoke, one worker. Ceiling 3600 s real
job wall time, 8 GiB combined RSS and 10 GiB newly generated artifacts. Raw
evidence records actual use, not these ceilings as consumed allocations.

Development samples are frozen before numerical outcomes in the local manifest:
source tile 11NE10B and adjacent 12NW6A, seed 20261002; window offsets
(901,701,24,20), (301,201,24,20), (1191,1001,24,20) on 11NE10B and
(301,301,24,20) on 12NW6A. Dates: 2026-01-07, 2026-03-20, 2026-06-21,
2026-09-22, 2024-02-29. Times include 08:17:23, 12:03:41, 15:29:17 and
02:11:09 HKT. Reviewer must choose additional seasonal dates/windows.
