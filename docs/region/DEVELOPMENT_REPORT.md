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
