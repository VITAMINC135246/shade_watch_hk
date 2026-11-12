# Package H1.0 amendment 1 — starting commit, two config files, two code dependencies, prompt corrections

Amendment ID: `SW-H1.1`
Amends: `SW-H1.0`, `docs/packages/H1.0/CONTRACT.md` (SHA-256 `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c`). The contract file is not edited.
Status: frozen by the commit that adds this file. Record this file's SHA-256 before development.
Decision record: D-026 (snapshot in `docs/planning/DECISIONS.zh-TW.md`).

The contract applies as written, except for the items below. Where the contract and this amendment differ, this amendment applies. No objective, non-goal, authorized computation, budget or acceptance item is removed.

## Why

The developer stopped at the read-only preflight on 2026-11-12 and reported two discrepancies in the development prompt (B1 and B2 below). No file was changed and no job ran. While checking them, the planning conversation searched the tree again for requirements of the contract that cannot hold together. It found three conflicts inside the contract (A2, A4, A5) and one open value (A3).

## A. Changes to the contract

### A1. Starting commit

- The **starting commit** is the commit that adds this amendment. Its parent is `fda9985a259bff640237d4fb80c9c0a7e3fba0a8`, the commit that added the contract; that commit's parent is `cfb6e3c52001103a206c256c1af46bcdce30f01c` (tag `pre-h1.0`).
- Every mention of "the starting commit" in the contract and in H1-01, H1-02, H1-04 and H1-06 refers to this commit. The candidate is one local commit on it.
- Between `fda9985` and the starting commit, only files under `docs/packages/H1.0/` and `docs/planning/` differ.
- This amendment is added to the files that the developer does not edit (contract write scope, H1-01).

### A2. `config/engine/estimator.json` and layout rule 4

- Conflict: the contract requires `config/engine/estimator.json` to be byte-identical to the former `docs/v2/estimator.json` (design item 6, H1-04). That file lists its four calibration records by their paths at the time (`outputs/v2_development/evidence/cal_*.json`). Layout rule 4 (design item 9) forbids `outputs/` in tracked files.
- Resolution: the file stays byte-identical. `config/engine/estimator.json` is added to the exclusions of layout rule 4. The four strings record a past calibration. Only the retired calibration tool (`tools/v2_development.py`, which moves to `legacy/`) writes them, and no code under `src/` or `tests/` reads them.

### A3. `config/engine/processing.json`

- This file holds the defaults of the older pipeline entry in `pipeline.py`. Two of its values are paths in the old layout.
- It changes in these two values only:

  | Key | Old value | New value |
  | --- | --- | --- |
  | `output_directory` | `outputs/native_tile_geometric_1km_20260929` | `work/engine/pipeline` |
  | `cache_directory` | `data/processed/horizon_cache_1km` | `data/cache/horizon/pipeline_1km` |

- Neither folder is created by H1.0, and no authorized run uses this file's defaults.

### A4. `tools/sea2/checks.py` is not retired

- Conflict: the contract moves `tools/sea2/checks.py` and `tests/test_sea2_checks.py` to `legacy/campaigns/b2_2/` (design items 1 and 7). But `tests/test_sea2_diagnostic.py`, which stays, imports `RawCounterfactual` from `checks.py`; and the contract removes no test other than the retired ones.
- Resolution:
  - `tools/sea2/checks.py` moves to `shade_watch/fill/checks.py`, with the other files of `tools/sea2/`. It changes only in imports, module names and paths.
  - `tests/test_sea2_checks.py` stays in `tests/` and is not retired.
  - `tools/sea2/resources.py` moves to `legacy/campaigns/b2_2/` as before. No other file imports it.
- The retired tests are now: every test of `tests/test_sea_masks.py`, and `test_campaign_internal_dispatch_is_not_recursive` in `tests/test_shade_map.py` (H1-06).
- `checks.py` is not one of the eight files of the view identity.

### A5. `polygonal` in the iB5000 validation tool

- Conflict: `tools/sea2/validate_ib5000.py`, which moves to `shade_watch/fill/`, imports the function `polygonal` from `tools/sea_view/extract.py`, which moves to `legacy/b1_sea_view/`. The contract moves `legacy/` unchanged and does not expect it to run, so the import would break.
- Resolution: `shade_watch/fill/validate_ib5000.py` defines `polygonal` at module level. Its source text is the function in `tools/sea_view/extract.py` at the starting commit (lines 17 to 27), unchanged. The import line is removed. `legacy/b1_sea_view/extract.py` stays as it is.
- This is the only change to existing code in H1.0 that is not an import, a module name or a path. No run of the validation tool is authorized. The change is checked by comparing the source text and by the existing tests in `tests/test_sea2_validation.py`.

## B. Corrections to the prompts

The two prompts are corrected in the commit that adds this amendment. They ask for nothing that the contract and this amendment do not require.

| File | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `DEVELOPMENT_PROMPT.md` | `0390d4ff848409c897386e53ce5eaaa04605636b5bff40311cd91e0e1ab351a4` | `4f03256a745df353a2d05818a1d0843b10576d67e791188a1bbfe2bf262c7c0f` |
| `ACCEPTANCE_PROMPT.md` | `2b86753bc9d45783a027709cbd41070741d0d15ca77caf2447e0b4d05b4ed4e3` | `1f6613ba4ef03f65a4dd090b710dccd765d782c097485de748ed0f815c160f0a` |

### B1. Count of files added by `8d7a0d3`

- The development prompt named four `config/regions/measure_*.json` files. The commit added five (`measure_central`, `measure_cheung_chau`, `measure_lo_wu`, `measure_mong_kok`, `measure_tai_mo_shan`) and three files in `tools/wsl2_smoke/`: eight files in total.
- The stop condition now names these eight files. The developer's finding was correct.

### B2. Directions computed by R-7

- The development prompt said that every regression run computes zero directions. The contract is right: R-1 to R-6 compute zero directions (H1-10); R-7 computes the directions of its counterfactual again, in a `fill_impact_<id12>` namespace, and this is authorized.
- The prompt now says the same as the contract.

### B3. Inventory comparison

- The development prompt asked the developer to report every difference between its own inventory and the planner baseline, without saying which differences are expected.
- Expected: the folder `archive/baseline_h1_0_20261112/` itself, which the baseline does not list, and `.DS_Store`, `__pycache__` and `.pytest_cache` entries. The developer reports these and continues. Any other difference is a reason to stop and report.

### B4. Summary sentence about pixels

- The development prompt said that every regression run is pixel-identical to its baseline. R-7 is a fill-impact report and R-8 is plan-only. The prompt now says: R-1 to R-6 are pixel-identical, R-7 reproduces the `frames` of its reference report, and R-8 plans as the contract says (H1-07, H1-11).

### B5. References to the starting commit and to this amendment

- Both prompts now describe the starting commit as in A1, name this amendment next to the contract, and add it to the files that are read first and not edited.
- The acceptance prompt applies the exclusion of A2 when it checks layout rule 4, accepts edits that this amendment names, and compares the source text of `polygonal` (A5).
- The development prompt names A4 and A5 in its sequence and its facts.

## Unchanged

- Scope, non-goals, required design (apart from A2 to A5), authorized computation, budgets and the acceptance matrix H1-01 to H1-14.
- The planner baseline `archive/baseline_h1_0_20261112/listing.tsv` (SHA-256 `c82d5ed7644927d8384177254ccba4960117d5d482ebd1a2e27f13571b6b5afb`).
- `docs/CONVENTIONS.md`.
