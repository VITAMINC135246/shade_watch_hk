# Independent acceptance of F1.0 — SW-F1.0

Date: 2026-10-31. Candidate: **`eb605f52d119a00fa30b8c5d0f44a725f9d88043`**.

**Engineering acceptance: NOT ACCEPTED** (11 PASS, 2 FAIL, 1 NOT VERIFIED).
F1-02 fails the output-location guard; F1-11 fails the stale `.partial` rule in a
separately frozen state-injection case. F1-13 retains an unresolved development
memory-measurement gap. The two required SIGKILL recovery cases themselves pass.

**Numerical consistency with the accepted engine: PASS for the tested arrays.**
All 65 Cheung Chau frames equal the historical accepted-engine reference, and all
7 independent rectangle frames equal separate V1 references. These are complete
array comparisons, not samples. **Observational accuracy: NOT VERIFIED.**

## Candidate, environment and input identities

- Development start: `d1a89c80306e8a3a2f2a5f1edf45149b419919d2`.
- Reviewed adapter: `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`.
- Accepted engine: `356f611d7b775ce31006904b80ca31d3c1c484b2`.
- Frozen contract SHA-256, checked before review runs and unchanged:
  `dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690`.
- Exact candidate in a detached Git-managed worktree at
  `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/shade_map_review_eb605f52d119_20261031/worktree`.
  The desktop worktree helper rejected the nested repository before creating
  anything; Git's managed worktree was used without changing the main checkout.
- Existing project `.venv`: Python 3.12.5, macOS 15.7.4 arm64; NumPy 2.5.3,
  Rasterio 1.5.1, PyProj 3.8.0, Numba 0.67.0, psutil 7.2.2, pytest 9.1.1.
  No packages were installed.
- `requirements.lock.txt` SHA-256:
  `ffcc5e7fb9bc57c599c1b76778f10d7edb23f4cf6d301530dccc2126526451e0`;
  `requirements.tools.lock.txt`:
  `98c673a8f17f24ffd629dd8febe223f80687a5ce24c2a578355c34784621cf0e`.
- Raw catalogue, read-only:
  `/Volumes/My Passport for Mac/Projects/shade_watch_hk/data/raw/dsm/2020/D12.DSM.TIFF`.
  [Input identities](../../outputs/shade_map_review_eb605f52d119_20261031/input_identities.json)
  independently rehash all 49 selected raw files and record configs, fixtures,
  source identities and manifest timing.
  [Reference identities](../../outputs/shade_map_review_eb605f52d119_20261031/reference_input_identities.json)
  hash the historical combined result index and its shade/quality inputs, plus
  the four independent V1 result indexes and their raster inputs.

[Start record](../../outputs/shade_map_review_eb605f52d119_20261031/start.json),
[code audit](../../outputs/shade_map_review_eb605f52d119_20261031/code_audit.json), and
[final scope audit](../../outputs/shade_map_review_eb605f52d119_20261031/final_scope.json)
preserve the provenance. The ten pinned engine files and adapter are byte-identical
to their accepted versions. The start-to-candidate diff under `src/`,
`tools/region_request.py` and `config/v3/` is empty. The candidate contains one
commit with 45 added F1 task files. Production dispatch uses explicit
`plan`/`run`/`prune` branches: it has no prefix redispatch, recursive monitor launch,
or invocation of the development campaign harness.

## Frozen independent cases and coverage

The [independent manifest](../../outputs/shade_map_review_eb605f52d119_20261031/frozen_manifest.json)
was frozen before outcomes; its recorded modification time precedes the first job
log's creation time. It was not changed after observing results.

- Central / Sheung Wan waterfront, WGS84 `[lat, lon]`:
  lower-left `[22.290013634059704, 114.15232503680699]`, upper-right
  `[22.29019662973763, 114.15255925827309]`.
- Projected fractional corners: `[833738.17, 816790.11]` to
  `[833762.31, 816810.37]`; resolved bounds
  `[833738, 816790, 833762.5, 816810.5]`, 49 × 41 = 2,009 pixels.
  Four clipped native cells, including `e833750n816800` with no DSM tile.
  No `14NE15*` dependency.
- `2026-06-21` instants: 05:50, 10:00, 13:00, 16:30 HKT; 00:10 is dropped as
  outside daylight. Window: 10:10–10:30 inclusive, every 10 minutes, three frames.
- Independent daylight-equivalence dates: 2026-03-20 and 2026-12-21. The unchanged
  synthetic suite also checks 2026-01-07 and both solstices.
- Own corner, time and configuration invalid cases; synthetic geometry fixtures;
  two interruption cases and additional publication states. Seeds: sampling
  451031 and fixtures 714031. All numerical comparisons used full arrays.

The frozen Central rectangle proved to be entirely DSM NoData, including the
three cells with source tiles: every frame has shade 255, quality 1 and surface
255 at all 2,009 pixels. Its result verifies clipping, gaps and invalid-data
handling; it provides no nontrivial summer land-shadow coverage. The rectangle
was not moved after seeing this outcome. Cheung Chau supplies the nontrivial
shade/quality regression.

V1 custom-bounds references were computed independently for all three owned cell
windows and seven times, in a separate cache namespace. V1 rejects an entirely
ownerless request, so the missing cell was read at its exact window from a
separately computed enclosing-rectangle V1 reference. No source tile or surface
value was invented. Bounds, jobs and indexes are in
[V1 references](../../outputs/shade_map_review_eb605f52d119_20261031/v1_references.json).

## Budget ledger and write scope

[budget.json](../../outputs/shade_map_review_eb605f52d119_20261031/budget.json)
records every monitored job's argv, elapsed time, sampled descendant RSS, artifact
size, exit status, log paths and intentional kill evidence. Monitoring was working
before the first independent job. Jobs were sequential. Synthetic tests and
verification were conservatively included in the wall-time charge.

| Independent phase measurement | Recorded | Ceiling |
| --- | ---: | ---: |
| Charged job wall time, 20 jobs | 1,398.62 s / 23.31 min | 45 min |
| Largest sampled process-tree RSS | 1,008,009,216 bytes / 0.939 GiB | 12 GiB |
| Sampled new-artifact peak | 779,000,735 bytes / 0.726 GiB | 20 GiB |

RSS and artifact peaks are sampled measurements, not OS-enforced maxima. Metadata
setup and final listing/report bookkeeping are outside the real-DSM job charge.
No ceiling was extended. Published runs, work folders, caches, source views,
portability copies and diagnostics all reside beneath the fresh review root.
Production roots were not monkeypatched.

The before/after inventory covers 34,528 original protected files. Raw data,
existing caches, historical/developer outputs and presentations have no changed,
missing or added files attributable to review. The shared main checkout acquired
three staged B2 prompt files and a staged prompt-index change concurrently;
[the discrepancy](../../outputs/shade_map_review_eb605f52d119_20261031/concurrent_main_changes.json)
is recorded explicitly. Those changes were neither made, read as B2 instructions,
staged nor altered by this review. The isolated candidate remains clean. The only
review file outside the review root is this requested, uncommitted report.

F1-13 is **NOT VERIFIED** because the candidate's own
[development report](DEVELOPMENT_REPORT.md) and
[resource ledger](evidence/resource_ledger.json) acknowledge that peak memory was
not captured for its first real-DSM read-only planning process. Repeating that
plan with monitoring establishes the repeated process's usage, not the first
process's peak. Independent measurements do not retrospectively close that gap.
There is no evidence of a limit being exceeded; the criterion has not been lowered.

## Criterion verdicts and reproducible evidence

In the commands below, run from the main project root and define:

```sh
P='/Volumes/My Passport for Mac/Projects/shade_watch_hk/.venv/bin/python'
R='/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/shade_map_review_eb605f52d119_20261031'
WT="$R/worktree"
```

`review.py` is the independent harness. Its action commands below identify the
recorded executions; exact child commands and logs are retained in `budget.json`.
Do not repeat a cold-cache or kill campaign into these retained namespaces;
a new campaign requires fresh review names. Read-only verification actions can
inspect the retained results. Schema checks use an independent implementation
of the keywords present in the normative schemas, not the candidate validator.

| ID | Verdict | Evidence and recorded command |
| --- | --- | --- |
| F1-01 | PASS | `code_audit.json`, `start.json`, `input_identities.json`; `git -C "$WT" diff d1a89c80306e8a3a2f2a5f1edf45149b419919d2..HEAD -- src/ tools/region_request.py`; `$P "$R/review.py" setup`. Pin byte comparisons, hashes, ancestor and task-only single commit checked. |
| F1-02 | **FAIL** | `invalid_results.json`, `planning_results.json`; `$P "$R/review.py" rules` and `plans`. Ordinary schema cases and machine-independent identity pass; 2 of 38 own invalid cases accept prohibited external output locations and write files (defect D1). |
| F1-03 | PASS | `invalid_results.json`, `invalid/*_machine.json`, `invalid/*_region.json`; `$P "$R/review.py" rules`. Both CRS orders, equality, nonfinite/range cases reject with specific reasons, code 2 and empty before/after deltas; projected-order gate tested with a fixture. |
| F1-04 | PASS | `planning_results.json`, `invalid_results.json`, `logs/00_full_suite.stdout`; `$P "$R/review.py" plans` and `rules`. Own two dates equal engine frames exactly; unchanged `test_daylight_equal_engine` covers three dates including both solstices. Window stepping, inclusive endpoint, unique folders and night/drop/error rules pass. |
| F1-05 | PASS | `invalid_results.json` adapter-equivalence records, `planning_results.json`, `kill_*_incomplete.json`, `states_prune.json`; `rules`, `plans`, `interrupt_compute`, `interrupt_publish`, `prune` actions. Three synthetic shapes equal direct adapter requests/keys; only source-view writes; plan schema/labelled estimates, shifted-tile rejection and all four statuses pass. |
| F1-06 | PASS | `code_audit.json`, `logs/01_test_provider.stdout`; `$P -m pytest tests/test_shade_map.py::test_source_interface_surface_one` from `$WT` (review-local test temp/cache). Correct class-1 fixture publication; no publication branch on provider name. |
| F1-07 | PASS | `cc_arrays.json`, `instants_arrays.json`, `window_arrays.json`; `$P "$R/review.py" check_cc` and `check_rect`. All cells/layers/clipped edges, path rules and all relocated VRT arrays verified. |
| F1-08 | PASS | Same array records and published manifests under `$WT/outputs/shade_map_review_published/`; `check_cc`, `check_rect`. Every cell/VRT/full raster equals logical windows; raw surface independently derived; transforms, uint8, CRS, NoData, tiled DEFLATE and per-pixel coverage checked. |
| F1-09 | PASS | `cc_source_gate.json`, `cc_arrays.json`, `logs/04_cc_run.stdout`; `plans`, `cc`, `check_cc`. Cold review cache, all 21 source tile names equal reference before computation; all 65 frames, 07:10–17:50 HKT, every shade/quality pixel identical. |
| F1-10 | PASS | `v1_references.json`, `instants_arrays.json`, `window_arrays.json`; `rect`, `refs`, `check_rect`. All seven frames equal separate V1 references, including exact missing-cell windows; no-DSM codes correct; night dropped. All-NoData coverage limitation stated above. |
| F1-11 | **FAIL** | `kill_compute_resumed.json`, `kill_publish_resumed.json`, `renamed_frame_recovery.json`, `states_prune.json`; `interrupt_compute`, `interrupt_publish`, `rename_gap`, `prune`. Both SIGKILL cases pass all 57 frame-file hashes, retain completed tasks/frames and leave no partials. Conflict and concurrency refuse. Frozen extra orphan-partial case violates the unqualified no-`.partial` rule (D2). |
| F1-12 | PASS | All three array records, `kill_*_incomplete.json`, `states_prune.json`; `check_cc`, `check_rect`, `prune`. Schemas, canonical seals, source/sidecar/file hashes and raster counts independently checked. CSV/JSON agree; fractions use whole-class denominators. Incomplete prune refuses; complete prune changes only its manifest and removes only its own work; following run only verifies. |
| F1-13 | **NOT VERIFIED** | `budget.json`, `main_before.json`, `final_scope.json`, developer `evidence/resource_ledger.json`; `$P "$R/final_audit.py"` and recorded monitored commands. Independent phase is within limits and protected paths preserved; development's first planning-process RSS remains unmeasured. |
| F1-14 | PASS | `logs/00_full_suite.stdout`: **189 passed**, unchanged `pytest tests`, plus provider test rerun; `code_audit.json`; committed GUIDE/DESIGN/DEVELOPMENT_REPORT, examples and developer evidence manifest. `$P "$R/review.py" tests`. One candidate commit, no review commit or push. |

Evidence paths without a prefix in this table are relative to `$R`. All actions
are exact dispatches; none use the failed development harness's prefix route.
The full suite was explicitly restricted to `tests`, avoiding historical review
checkouts under `outputs`.

## Preserved defects

### D1 — P1: external output locations bypass ownership and catalogue guards

Affected code: `tools/shade_map/config.py:135–142` and
`tools/shade_map/planning.py:27–39`. The data guard only considers this checkout's
`data/`; the ancestor ownership loop only runs while an ancestor is inside
`v1.ROOT`. An output root outside that checkout skips the unowned-parent guard,
including when it is nested in the declared read-only DSM catalogue.

Expected: reject these machine configs before any write, exit 2 with
`invalid input: output_root: ...`. Actual: exit 0, report `complete`, create a
root marker, normalized config, run manifest and summaries. The reproduced cases
use only review-owned synthetic fixtures and a night-only request (zero computed
frames); no user raw catalogue was written. Existing TIFF bytes remain unchanged,
but added children prove that the catalogue is not treated as read-only.

Minimal retained reproduction, from the candidate worktree:

```sh
cd "$WT"
PYTHONDONTWRITEBYTECODE=1 "$P" -m tools.shade_map run \
  --machine "$R/invalid/external_dsm_parent_wgs84_machine.json" \
  "$R/invalid/external_dsm_parent_wgs84_region.json"
```

The machine config sets `dsm_dir` to `$R/fixtures/dsm` and `output_root` to
`$R/fixtures/dsm/published_external_dsm_parent`. The region is HK1980
`[800001,820001]` to `[800003,820003]`, at `2026-06-21T00:10`.
`invalid_results.json` preserves the first-run added-path listing and stdout;
rerunning the retained case still returns success. The companion
`external_foreign_parent_wgs84` case reproduces the same bypass in an ordinary
pre-existing foreign parent. For a new first-write demonstration, use new review
fixture names rather than deleting this evidence.

### D2 — P2: complete-run verification leaves an empty stale `.partial` folder

Affected code: `tools/shade_map/runner.py:45–58`, `162–168`, `180–185`.
`verify_run` inventories files only, so an empty `.partial` directory is invisible.
The complete-run return bypasses the cleanup at lines 225–229.

Expected under design item 8 and F1-11: a stale `.partial` folder is not accepted
as part of a complete publication and does not survive resume. Actual: after
adding `20260621/1000.partial/` alongside a verified published frame, the same
request returns `status: complete`, `verified_only: true`, `computed_batches: 0`,
and leaves the partial folder. The supplementary case was frozen in advance.
This does **not** establish a failure in either mandatory SIGKILL case; those
both passed. The FAIL applies the contract's unqualified no-`.partial` rule to
this additional complete-state recovery case.

Minimal reproduction on the retained independent instants run:

```sh
mkdir -p "$WT/outputs/shade_map_review_published/shade_map_review_central_i/20260621/1000.partial"
cd "$WT"
PYTHONDONTWRITEBYTECODE=1 "$P" -m tools.shade_map run \
  --machine "$R/configs/instants_machine.json" "$R/configs/instants_region.json"
test -d "$WT/outputs/shade_map_review_published/shade_map_review_central_i/20260621/1000.partial"
```

`states_prune.json` preserves the injected path, result and `survives: true`;
the empty directory remains for inspection. No defect has been repaired.

The report and [review evidence index](../../outputs/shade_map_review_eb605f52d119_20261031/evidence_manifest.json)
are uncommitted. No push, merge, sea view, V3 or territory run was performed.
Any repair requires a new candidate SHA and targeted re-acceptance, retaining
these original failure records. This review does not proceed to B2.0.
