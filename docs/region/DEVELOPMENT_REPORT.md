# Region development report — SW-RGN-AC-1.1

Development candidate for planning review, not an acceptance declaration. This
amendment starts from **86dbee663ccec8edcca7f123542a345fa13ca18b**, branch `feature`, after Package B.
Candidate SHA: the one local commit containing this report, obtained with
`git log -1 --format=%H -- docs/region/DEVELOPMENT_REPORT.md`.

Frozen SHA-256 values verified before editing (and at handoff):

- AMENDMENT_1_1.md: `e80e5da083a5750c61f42cffc7b8414ff142aeab6c8aa2c1dd2c10716f009ea0`.
- ACCEPTANCE_CONTRACT.md: `3bc918a993a3f5f7baebc26db5c698173e35b0d9c81f31c6a6bee1c76980a579`.

Evidence paths below are relative to `docs/region/evidence/v1_1/` unless stated
otherwise. The original 1.0 R01–R08 matrix and report are preserved verbatim at
the end as historical evidence; the current matrix supersedes its open R06 and
its rejected-gap behavior. Work is limited to A 1.1. The new project direction
(function-style output / sea at 0 m) was not implemented here.

| ID | Current status | Evidence and commands |
|---|---|---|
| R01 | PASS | `start.json`, `final-integrity.json`; starting HEAD/branch/status and both hashes recorded; every src/*.py unchanged, all ten pinned files byte-identical to 356f611. `git diff <start>..<candidate> -- src/` empty. |
| R02 | PASS | Existing validation tests pass unchanged in `tests/test_region_request.py`; explicit CRS, corner order, non-finite/out-of-range/zero area and whole-rectangle-no-tile errors. Added empty/duplicate dates and single-date frame-limit errors. |
| R03 | PASS | Existing five spread-out Hong Kong points remain bit-identical to V1 transformer construction. `real-plan.json` records transformer, pyproj and PROJ versions. |
| R04 | PASS | Existing single-tile, four-tile-corner and fractional-corner tests compare the complete V1 key/grid with hand-written custom bounds. Dates-mode equivalence additionally verified in R10. |
| R05 | PASS | Exact pixel occupancy, pairwise disjointness, per-part V1 admission, batch V2 admission, unique native horizon inventory. Sparse fixture uses two larger parts covering eight lattice cells and four supplied tiles; the original forced-split test still has four distinct horizon tasks. |
| R06 | PASS | `real-equality.json`, `real-plan.json`, `v2-result.json`, `v1-result.json`: real two-tile V2 split, both frames pixel-identical in Shade/Quality/transform to one independently computed V1 custom rectangle. New complete monitor ledger replaces the old unverified exercise as the qualifying run. |
| R07 | PASS | `GUIDE.md`, `guide-checks.json`, `guide_0_stdout.json`, `guide_1_stdout.json`; both exact WGS84/HK1980 commands exit 0 using auto views. Sidecar contains original/projected corners, versions, requested/resolved grid, partitions, residuals, temporal groups, source identity and qualified request IDs. |
| R08 | PASS | `.venv/bin/python -m pytest tests/ -q -o junit_family=legacy --junitxml=docs/region/evidence/v1_1/full-tests.xml`: **106 passed** (99 previous + 7 amendment tests), existing test files unchanged. `full-tests.txt`, `full-tests.xml`; evidence manifest and one inspected local commit. No push. |
| R09 | PASS | `tests/test_region_request_v1_1.py`: interior/edge no-DSM cells retained in two tile-owning parts; exact union/disjointness; engine execution and read-back give 255/1 on gaps. Adding a tile computes that cell (non-1 Quality and finite Shade labels). Far residual remains recorded/readable; a whole no-tile rectangle still rejects. Multi-batch read-back equals a V1 reference and missing batches reject. |
| R10 | PASS | Same tests: date request key equals hand-written plan_shade(dates=...) key; nine dates exceed 512 frames and split only at complete-date boundaries; ordered UTC frames exactly equal concatenated per-date engine frames, no duplicates/interpolation. CLI --date/--interval-minutes round-trips. |
| R11 | NOT VERIFIED | `r11-real-identity.json` provides passing coastal, inland and four-tile-corner comparisons against a **75-source compatible control catalogue** with auto 21/24/30-source views. Native spatial keys and V1 plan keys match, and also match auto selection from all 3,310 raw headers. Full/view times are below. `source-view-timings.json` separately verifies a complete compatible synthetic catalogue with distant data and external-mask coverage. The invalid 3,310-file engine catalogue is not falsely claimed to be admissible; reference scope is explained below. |
| R12 | PASS | `real-equality.json`: each real native tile has distinct cache directions **130° and 215°** at 09:17:23/14:31:27 HKT. V2 computed 4 directions; independent fresh V1 cache computed **4**, reused **0**. All arrays/transforms and the region helper agree. `ledger.json` includes both cold runs. |

## R11 reference scope and measured planning

The pinned engine cannot produce a full-raw reference key for the 3,310-file
catalogue: its four shifted-origin 14NE15* tiles fail admission (original
`docs/region/evidence/blocker.json`). Correcting or globally discarding those
files would require the pending ingestion policy and is outside this task.

For an actual valid full-catalogue comparison, the control contains the UNION
of every source in the three real target-halo views selected from all 3,310 raw
headers: **75 unmodified native files**, linked under `outputs/region_views/`.
It includes irrelevant distant sources for each individual ROI, so auto selection
must preserve scientific identities while reducing the catalogue. The engine
independently indexes/hashes both paths. No terrain is reprojected, filled or
corrected. Keys also match the previous direct auto selection from the entire
raw header catalogue, establishing that every relevant raw dependency is present.

| Real region | Full catalogue tiles | Auto-view tiles | Full planning seconds | Auto-view seconds | V1/spatial keys |
|---|---:|---:|---:|---:|---|
| coastal | 75 | 21 | 10.662153 | 1.101407 | equal |
| inland | 75 | 24 | 2.256289 | 0.842023 | equal |
| tile_corner | 75 | 30 | 3.210694 | 1.277136 | equal |

These are local warm-file-system timings, not calibrated territory forecasts.
The compatible-control results are supporting evidence, not a replacement for
a successful plan against the unchanged 3,310-file raw catalogue. R11 is
conservatively **NOT VERIFIED** for that literal full-catalogue comparison until
the ingestion policy is decided. No criterion is weakened to claim a pass. The implementation's
required-source guard is tested: a needed 14NE15* target/halo dependency raises
a clear pending shifted-origin DSM ingestion policy error, never a silent skip.

## Resource ledger and immutable runtime locations

The authoritative cumulative ledger is `evidence/v1_1/ledger.json`; the original
`evidence/ledger.json` remains historical and unmodified.

- Original conservative charge: **391.000 seconds**.
- Amendment work including guide planning, two cold computations, three real
  source-view timings and full-compatible R11 comparisons: **338.014 seconds**.
- Cumulative conservative charge: **739.014 / 1200 seconds**, including an additional 10-second conservative charge for final integrity audits.
- Amendment peak sampled process-tree RSS: **689,487,872 bytes / 8 GiB**; R11 process high-water RSS also included.
- Final retained-file byte totals are reconciled in the ledger, including prior
  region artifacts, new views/cache/output, code, tests and documentation; below
  **5 GiB**. Raw symlink targets are not counted as newly created raster bytes.
- R11 full-reference indexing is timed separately and conservatively charged to
  the same 20-minute total; the indexing exception was not needed.

Runtime roots: `outputs/region_dev_v1_1_validation`, the two documented
`outputs/region_dev_v1_1_example_*` requests, immutable `outputs/region_views/<hash>`
views, and `data/processed/shade_v1/region_dev_v1_1_v2` /
`data/processed/shade_v1/region_dev_v1_1_v1`. No derived TIFF, state DB, cache or
runtime source catalogue is committed. The supervisor checks monitoring access
before launch and terminates with margins before time/memory/artifact ceilings.
Old monitoring uncertainty is preserved in the historical report, not rewritten.

## Assumptions, choices and remaining limits

1. No-DSM cells are processed by the engine inside tile-owning rectangles. The
   adapter never rasterizes/fills/relabels scientific outputs. Residuals carry
   their bounds, reason and 255/1 encoding; parts plus residuals cover the full
   resolved rectangle exactly. A later catalogue with a tile there computes it.
2. Partitioning uses catalogue-derived native edge periods and engine snapping.
   Small domains use memoized guillotine search; large domains bound candidate
   exploration. Objective: minimize residual pixels, then prefer fewer/larger
   admitted parts. No global optimum is claimed. A native cell indivisible under
   an artificially smaller test cap still gives a clear limit error.
3. Dates remain original Hong Kong dates and interval values in written requests.
   Complete dates are the atomic temporal unit. A single date over 512 frames
   requires a larger interval; no interpolation or intra-date truncation occurs.
4. Batch admission passes pre-built ShadePlans. Whole-batch admission is attempted
   first; only budget failures cause bisection. The unchanged V2 still indexes
   the chosen catalogue once per attempted batch; no runtime monkeypatch hides
   this validation. Tests assert one admission and two inventory calls total
   for a normal multi-part request (adapter + V2), not one trial per part.
5. V2 names pre-built plans request_NNNN. Emitted files use those same names,
   preserving the exact batch ID. Sidecar identifiers are globally qualified by
   batch filename; geometry and temporal requests are represented separately.
6. Auto-source-view is opt-in. It may write only its immutable symlink catalogue
   during `plan`, an explicit 1.1 exception to ordinary read-only planning.
   Header cache is process-local and invalidated by source/known-auxiliary
   path/size/mtime signatures; engine hashing remains authoritative.
7. Source views link recognized auxiliary files too; an external-mask fixture
   verifies identity equivalence and cache invalidation. Required known shifted
   inputs fail with the named pending ingestion policy. Raw data is unchanged.
8. The read-back helper delegates raster reading to read_logical_window, checks
   requested instants and completed batch IDs, rejects missing science and
   conflicting overlaps, and returns explicit residuals as 255/1. Read windows
   must obey the unchanged aligned V1 area ceiling.
9. R11's passing compatible-control checks and unavailable literal full-raw
   comparison are stated separately above. R11 remains NOT VERIFIED. No new territory ingestion
   or scientific policy is inferred from those local measurements.
10. Bare pytest initially discovered another conversation's review-worktree test
    copies under outputs and failed collection on duplicate names. No tests
    executed in that failed attempt. The complete intended suite was then run
    explicitly as `pytest tests/` and passed; the collection log is retained.
11. Planner/user directories listed in the latest instruction, including
    web/console and the WSL smoke material, were not intentionally edited or
    staged. External hash drift since start is recorded in final-integrity.json
    and not restored. Nothing under src/*.py changed.
12. The previous sea implementation and the new function-style / sea-at-zero
    direction are outside this commit. No independent acceptance, V3, UI,
    download, push or PR was run for this amendment.

The historical 1.0 matrix follows intact. Its sparse-cell rejection, guide
admission issue and same-direction/warm-reference evidence are superseded by the
current R09, R07 and R06/R12 evidence respectively.

<!-- ORIGINAL_1_0_REPORT -->
# Region development report — SW-RGN-AC-1.0

Candidate: local commit containing this report (`git log -1 --format=%H -- docs/region/DEVELOPMENT_REPORT.md`). Development handoff only; no acceptance claim.
Starting HEAD: `38303b164d107b81c02f50f14da61951f09e9b49`, branch `feature`.
Contract SHA-256: `3bc918a993a3f5f7baebc26db5c698173e35b0d9c81f31c6a6bee1c76980a579`.

The coherent completed unit is the read-only input adapter, request writer,
synthetic tests and documentation. Further real work stopped when the whole
permitted DSM catalogue was rejected by the unchanged engine for incompatible
alignment at `14NE15A(e828n809,e829n809).tif`. No source was corrected. The
already-started bounded child completed on a local halo catalogue before the
stop inspection. No additional runs followed that finding.

| ID | Status | Evidence / command |
|---|---|---|
| R01 | PASS | `evidence/start.json`, `evidence/final-integrity.json`; starting SHA/hash/status recorded; all ten files byte-compared with `git show 356f611:src/<file>`; `git diff 38303b1 -- src/` empty. |
| R02 | PASS | `tests/test_region_request.py`, `evidence/unit-tests.txt`; both CRSs, reversed corners, invalid lat/lon, NaN/Inf, zero dimensions, no DSM and explicit CRS validation. |
| R03 | PASS | Five Hong Kong points compare exact float tuples to V1's transformer construction. Versions/description in `evidence/real-plan.json`. |
| R04 | PASS | Three parameterized rectangles: single-tile, four-tile intersection and fractional corners. Plan keys and complete grids equal hand-written V1 custom requests. |
| R05 | PASS | Exact pixel-set union/disjointness; four synthetic owners/four horizon tasks; every part passes V1, every batch V2. Budget tests exercise multiple files and indivisible rejection. Real plan has two owners/two horizon tasks. |
| R06 | NOT VERIFIED | `evidence/real-equality.json` proves exact Shade/Quality/transform equality at both daylight instants across two tiles (240 pixels each). V2 computed two directions; V1 reused both. However the outer watchdog ledger never advanced from launch, so complete campaign peak monitoring is unverified. Full raw catalogue also rejected; see `evidence/blocker.json`. No acceptance claim from partial evidence. |
| R07 | PASS | `GUIDE.md`, `DESIGN.md`; sidecar round-trip tests; real sidecar at `outputs/region_dev_validation/requests/region_request.json`. Both CRS examples, rectangle definition and native-tile cost limitation documented. |
| R08 | PASS | `.venv/bin/python -m pytest -q`: 93 passed (73 existing + 20 new), `evidence/full-tests.txt`. Existing tests unchanged. Only new task files staged; one local commit; no push. |

## Resource ledger

`evidence/ledger.json` preserves the accounting and limitations. Engine run APIs:
23.218 seconds cumulative; complete bounded exercise: 64 seconds from retained
file timestamps. Conservative charge including the initial full-catalogue
inspection and intervening authoring: **391 seconds / 1200 seconds**. Engine
measured peak process-tree RSS: **651,313,152 bytes / 8 GiB**. This is an engine
measurement, not a verified whole-exercise peak. Retained generated artifacts
were **18,254,111 bytes** at reconciliation, plus the final small report/evidence
updates (final exact total in ledger). Ceiling: 5 GiB. No downloads.

Only `outputs/region_dev_validation` and
`data/processed/shade_v1/region_dev` contain new runtime artifacts. The catalogue
contains 29 read-only symlinks to original DSM files, not copied data. Derived
rasters/cache/state are not committed. Synthetic tests use temporary fixtures.
The original incomplete ledger is retained as `evidence/ledger-incomplete-original.json`.

## Assumptions and open issues

1. WGS84 pairs mean (latitude, longitude), following the contract; HK1980 means
   (easting, northing). No automatic CRS or coordinate-order inference.
2. Private `v1._custom_grid` is used solely to reuse exact engine snapping for
   oversized bounds; it is not reimplemented. Engine limit constants are read.
3. Native tile-edge coordinates define cuts. Sparse partitions without DSM,
   test caps below an indivisible part, and over 4096 parts are explicit errors.
   These limitations require review; they are not silently filled or dropped.
4. Budget overflow emits feasible sequential batches; no minimum packing claim.
   Single requests use the existing V2 request JSON schema and also supply a V1
   command. Request sidecars remain outside engine output/cache directories.
5. The real exercise selected all sources intersecting the two owning tiles'
   union 1 km halo. It uses only authorized DSM data and preserves all relevant
   halo dependencies. The 29-source choice is recorded in `evidence/catalogue.json`.
6. Two consecutive daylight seconds are two distinct instants and share a
   nearest5 direction. They contain both sunlit and shaded labels; they are not
   night-only or all-invalid shortcuts.
7. Raw catalogue incompatibility is a blocker for the whole-directory examples.
   The known shifted-origin tile is left unchanged. The guide examples show the
   interface, not a claim that this raw catalogue passes admission.
8. Outer monitoring failed to produce a final ledger. A process inspection was
   initially denied; a permitted elevated read-only inspection then found no
   remaining development processes. Engine metrics and timestamps reconstruct
   accounting, but the missing outer measurement is not invented. The original
   one-off script is archived as `evidence/run-script.py` for audit only; it is
   not a supported executable (its original location was tools/).
9. Planner/user files were never edited or staged. A background presentation
   preview independently removed `live_preview/lock.json` and changed
   `live_preview/server.log`; both are listed in `final-integrity.json`. They
   were not restored or included. All other captured protected hashes match.
10. A stopped package may commit the coherent, tested adapter. R06 stays open
    for review; no independent acceptance, V3, config change, UI, push or PR ran.

Evidence files are enumerated and hashed in `evidence/manifest.json`; source
and test paths above are repository-relative. Runtime evidence paths are also
repository-relative and remain local/read-only for the reviewer.
