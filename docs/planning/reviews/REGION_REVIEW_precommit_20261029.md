# Region adapter review (pre-commit, static): SW-RGN-AC-1.0

Reviewer: planning conversation (Claude).
Time: 2026-10-29 14:04 UTC (22:04 HKT).
Candidate: uncommitted working tree on `feature`. HEAD is still `38303b1`; no Codex commit exists yet.
Files reviewed: `tools/region_request.py`, `tools/region_development.py`, `tests/test_region_request.py`, `docs/region/DESIGN.md`, `docs/region/GUIDE.md`, `docs/region/evidence/*`.

Method: static reading plus the evidence files Codex wrote. Claude cannot run the project environment, so every run-dependent verdict below relies on Codex's evidence. This is not an independent acceptance.

## Status of the work

- **No commit, and `docs/region/DEVELOPMENT_REPORT.md` is missing.**
  - The newest file times are about 12:35 UTC.
  - `docs/region/evidence/ledger.json` still says `"status": "RUNNING"` with zero totals.
  - The development session appears to have stopped or paused after the R06 run, possibly waiting for an approval in the Codex UI. **Not verified.**
- **Engine untouched.** `git status` / `git diff -- src` show no changes under `src/`. `start.json` records the pinned hashes and the contract SHA-256.

## Criteria

| ID | Verdict | Evidence / reason |
| --- | --- | --- |
| R01 | PASS (working tree; recheck at commit) | No `src/` changes. `start.json` has the pinned and protected checks. Needs re-confirmation against the final commit. |
| R02 | PASS (relies on Codex evidence) | `test_rejections` is parametrized over both CRSs and the invalid inputs. `unit-tests.txt`: 20 passed. |
| R03 | PASS | `project_corner` builds `Transformer.from_crs("EPSG:4326","EPSG:2326", always_xy=True)` and calls `.transform(lon, lat)`, the same as `src/v1.py`. `test_bit_exact_engine_transform` covers the points. |
| R04 | PASS (relies on Codex evidence) | `test_equivalence_order_and_read_only` compares against hand-written custom plans, using the engine's own `_custom_grid` for snapping. |
| R05 | PASS against the letter of the contract; see finding F1 | Partition union, disjointness and the horizon-task inventory are tested on a fixture. Lattice cells with no DSM file make the whole request fail. |
| R06 | NOT VERIFIED (evidence incomplete) | Logical window = single V1 custom result (Shade, Quality, transform equal; 10 × 24 px, 2 tiles). Weaknesses: the two instants are 1 s apart (14:31:27 and 14:31:28 HKT), so only one sun direction is exercised; the V1 reference reused the V2 cache (`computed: 0`); the budget ledger was not finalized. |
| R07 | PARTIAL | The sidecar has every required field. The guide has WGS84 and HK1980 examples and the cost-scaling statement. Both examples use the full raw catalogue, which makes planning very slow (F2), and the guide does not warn about this. |
| R08 | NOT VERIFIED | Full suite: 93 passed (`full-tests.txt`). The development report, the R01–R08 matrix and the commit SHA are all missing. |

## Findings

- **F1 (medium, contract gap).**
  - **What happens:** when a split is needed, every native-lattice cell must pass `plan_shade`. A cell with no DSM file (open sea) raises "no available native DSM tiles", so the whole request is rejected.
  - **Why it matters:** in Hong Kong, most large coastal rectangles contain such cells.
  - **Proposal:** amend to `SW-RGN-AC-1.1`. Record those cells in the sidecar as `uncovered` (output would be all 255) and skip them. The union of planned parts plus uncovered cells must equal the resolved rectangle.
- **F2 (major usability, not correctness).**
  - **What happens:** `plan_region` calls `v1.index_sources(dsm_dir)`, which SHA-256-hashes every file. The packing loop then calls `v2.plan_batch` once per request, and each call re-indexes the catalogue.
  - **Why it matters:** with the full 3,310-tile raw catalogue (about 26 GB), every plan costs minutes, multiplied by the number of parts. The R06 exercise avoided this with a 29-tile symlink view.
  - **Proposal:** the D-2 runner contract already requires request-local source views. Until then, document that callers should pass a subset view. Optionally, in 1.1, build the source view inside the adapter (symlinks to tiles intersecting the targets' 1 km halos), with spatial-key equality tests.
- **F3 (medium, scope).**
  - **What happens:** only exact instants are accepted (`--at`). There is no `dates` + `interval_minutes` daylight mode.
  - **Why it matters:** the Console (D-2/D-3) needs daylight sequences.
  - **Proposal:** add this in 1.1.
- **F4 (low).** Splitting cuts at every lattice line, so each part is at most one tile. Large rectangles become many small requests. This is correct and cheap thanks to horizon deduplication, but it produces many output folders.
- **F5 (low).** `_budget_error` classifies errors by matching substrings of the V2 messages. It is brittle if those messages ever change. The current messages match.
- **F6 (low).** The R06 evidence should use instants with different sun directions, and an independent V1 cache namespace, so the comparison is not purely a composition check.

## Recommended next steps

1. When the user returns, check whether the Codex session is waiting for input. Codex should then:
   - finalize the ledger;
   - write `docs/region/DEVELOPMENT_REPORT.md`;
   - re-run R06 with two different-direction instants and a separate V1 cache namespace;
   - commit.
2. Draft `SW-RGN-AC-1.1` covering F1, F3 and optionally F2. This is a versioned amendment and does not weaken 1.0.
3. Do not start B until A is committed, as the run sheet requires.
