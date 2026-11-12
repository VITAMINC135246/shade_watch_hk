# Package H1.0 contract — one clean layout and one naming scheme, with unchanged results

Contract ID: `SW-H1.0`
Status: frozen by the commit that adds this file. The user approved the scope and the names on 2026-11-12 (D-024, D-025). Record this file's SHA-256 before development.
Item codes: `H1-01` to `H1-14` (`H` is a new package letter: housekeeping).
Starting point: the commit that adds this contract, whose parent is `cfb6e3c52001103a206c256c1af46bcdce30f01c` (tag `pre-h1.0`, pushed to `origin/feature`).
Accepted base: G1.0 at `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d` (accepted under `SW-G1.0` with `SW-G1.1` and `SW-G1.2`).
Conventions: `docs/CONVENTIONS.md`. Where this contract is more specific, this contract applies.
Decision records (snapshot in `docs/planning/DECISIONS.zh-TW.md`): D-022 to D-025.

The development prompt and the independent-acceptance prompt for H1.0 both use this contract. Do not weaken any criterion after seeing results. Any change to scope or budgets needs a new contract version, agreed before work starts.

If two requirements of this contract conflict, or a requirement cannot be met, stop and report. Do not choose between them.

## Problem and objective

The repository grew through many stages. Names follow several schemes, runtime outputs of all kinds share `outputs/`, derived data and caches share `data/processed/`, and living documents sit next to historical ones.

The objective is one layout and one naming scheme before cross-platform work starts:

- one Python package, `shade_watch`, with sub-packages by responsibility;
- separate places for published runs, work files, baselines and archives;
- raw data by city; derived data separate from caches;
- records of earlier stages moved as a block to `docs/records/`, unchanged;
- retired code moved to `legacy/`.

**H1.0 changes names and locations only. It changes no rule, no policy value and no pixel.**

## Non-goals

- No change to any numerical rule, policy ID, policy value, schema name, profile or region config.
- No change to the content of `horizon.py`, `spatial.py` and `v1_cache.py`.
- No split of `pipeline.py` or `shade_watch.py` (the engine module). They move as they are; only hard-coded paths in them change. Splitting them is part of C2.0.
- No Windows support, no change to file locking, no new city, no other resolution or fill height.
- No new living documentation. The planning conversation writes the index, the README, the architecture document and the guide after acceptance.
- No deletion of data. The planning conversation removed recomputable and unaccepted data before this contract (list below). H1.0 moves what remains.
- No push.

## Verified starting facts (planning pre-check, 2026-11-12 14:30–15:00 and 18:15–18:50 HKT, linked Mac)

**Repository**

- Branch `feature`, HEAD `cfb6e3c`, equal to `origin/feature`. Tag `pre-h1.0` exists locally and on the remote. The only untracked entry is `archive/` (see below). `presentations/` is ignored.
- SHA-256 of the three files that define the horizon cache key:

  ```
  afb46c37742767e7480220d82527873ed389bb184623fef78b4a3a1d19e8144e  src/horizon.py
  5ecc0495dd102596ab41903b5e174c142888ffc14664b81009164fbf176d3aa7  src/spatial.py
  96a576d12ada9186319e4c8c5f1e626b06ab0aac5f7345a9c6083b9f1b6fe479  src/v1_cache.py
  ```

- `src/horizon.py` and `src/spatial.py` import no project module. `src/v1_cache.py` imports only `.horizon`, `.pipeline` (`fingerprint`, `profile`) and `.spatial`. The cache key hashes these three files by base name and does not contain a path.
- The view identity hashes eight files of `tools/sea2/` (`__init__.py`, `__main__.py`, `build.py`, `catalogue.py`, `profile.py`, `provider.py`, `rule.py`, `view.py`). They import `src` and `tools.shade_map` and hold the view's storage location. Their content must change in H1.0, so the view ID changes. The ingestion identity hashes the files of `tools/city/` in the same way.
- Runtime paths are hard-coded in `src/v1.py`, `src/v2.py`, `src/pipeline.py`, `src/shade_watch.py`, `tools/region_request.py`, `tools/shade_map/`, `tools/sea2/` and `tools/city/`. None is in the three cache-key files. The engine reads `docs/v2/estimator.json` and `config/study_area.md` at run time. `tests/test_chunking.py` reads `config/processing.json`.
- The view manifests, the view pointers, the ingestion manifest and the horizon cache entries contain no file-system path. A cache namespace holds only key folders. The view ID is not part of the cache key: the key uses the content hash and the geometry of each source tile.
- The user's `config/machine.local.json` holds `dsm_dir` `data/raw/dsm/2020/D12.DSM.TIFF`, `output_root` `outputs/shade_map`, `cache_namespace` `shade_map_raw`, four workers, and no `cities` key.
- Six Git worktrees are registered under `outputs/` (five from earlier reviews and the G1.0 review worktree).
- The G1.0 acceptance ran 309 tests, all passing.

**Data on disk after the planner's clean-up** (2026-11-12 14:31–14:33 HKT; user decisions D-023 and D-024)

- Removed: 160 units, 21.28 GB, 27,581 files and links: the fill-impact counterfactual caches, the pre-V1 caches, the caches of earlier development and acceptance work, the engine and diagnostic work folders, the request-local source views, and the views and caches of candidates that were never accepted (B1.0, B2.0). Their manifests are kept in `archive/removed/`. No unit outside the confirmed list was removed, and no kept unit changed.
- **Planner baseline** (2026-11-12 18:20 HKT): `archive/baseline_h1_0_20261112/listing.tsv` lists every entry of `data/raw`, `data/processed`, `outputs` and `archive` with its kind, size, modification time and link target. Its SHA-256 is `c82d5ed7644927d8384177254ccba4960117d5d482ebd1a2e27f13571b6b5afb`. The same folder holds a copy of the user's `config/machine.local.json`. Summary: `docs/planning/reviews/H1_BASELINE_20261112.md`.

  | Tree | Files | Directories | Symlinks | Bytes |
  | --- | --- | --- | --- | --- |
  | `data/raw` | 7,173 | 14 | 0 | 27,811,128,531 |
  | `data/processed` | 15,523 | 51 | 1,654 | 13,877,377,518 |
  | `outputs` | 111,540 | 27,865 | 4,235 | 14,194,288,133 |
  | `archive` (without the baseline folder) | 13 | 20 | 0 | 9,644,599 |

- `data/processed/` now holds only:
  - the accepted Hong Kong view `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1` with its pointer and lock;
  - the Rotterdam view `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843` with its pointer and lock, and the Rotterdam catalogue `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634`;
  - four cache namespaces under `shade_v1/`: `sea_fill_v2_2_8ee51b017411`, `sea_fill_v2_2_4b2c2e76ca8b`, `g1_dev_raw_20261111`, `g1_dev_raw_20261111_rotterdam`;
  - the tracked `README.md`.

## Required design

### 1. Python package

| Now | After H1.0 |
| --- | --- |
| `src/` ten engine files and `pipeline.py` | `shade_watch/engine/` (same file names) |
| `tools/region_request.py` | `shade_watch/region.py` |
| `tools/shade_map/` | `shade_watch/publish/` |
| `tools/sea2/` except `checks.py` and `resources.py` | `shade_watch/fill/` |
| `tools/city/` | `shade_watch/city/` |

- User-facing names:
  - `from shade_watch import shade_map, plan_shade_map`;
  - `python -m shade_watch plan|run|prune --machine <machine.json> <region.json>`;
  - `python -m shade_watch.fill build|fill-impact ...`;
  - `python -m shade_watch.city register <city_id> --machine <machine.json>`;
  - `python -m shade_watch.region ...` and `python -m shade_watch.engine.v1 ...`, `python -m shade_watch.engine.v2 ...` for the lower-level tools that exist today.
- New files without logic: `shade_watch/__init__.py` (exposes `shade_map` and `plan_shade_map` from `shade_watch.publish`) and `shade_watch/__main__.py` (hands over to the command line of `shade_watch.publish`). `src/__init__.py` becomes `shade_watch/engine/__init__.py`.
- Importing the package `shade_watch` must not import its sub-packages. No `python -m shade_watch...` command, and no worker process that the tools start, may load a module twice or print a double-import warning.
- Arguments, options, defaults other than paths, exit codes and messages are unchanged. A message may change only where it prints a path or a command.
- `src/` and `tools/` no longer exist.

### 2. Identity

- **Cache key: unchanged.** `shade_watch/engine/horizon.py`, `spatial.py` and `v1_cache.py` are byte-identical to the three files at the starting commit. The functions `fingerprint` and `profile` in `pipeline.py` keep their source text. If the work seems to need a change in any of these, stop and report.
- **Policy constants: unchanged.** `SW-V1-POLICY-1.0`, `SW-SEA-POLICY-2.2`, `SW-INGEST-POLICY-1.0`, the source names `raw` and `sea-2.2`, the rule version, every schema name and the publication format `shade-map-publication-1.1`.
- **Config content: unchanged.** Every file under `config/cities/`, `config/sea_profiles/` and `config/regions/` is byte-identical. Schemas change only in default path values and their descriptions.
- **View ID and ingestion ID: change once.** The Hong Kong view is rebuilt and Rotterdam is registered again with the moved code. The new files must have the content of the accepted ones (H1-08, H1-09).
- **Run IDs change.** Pixels do not.

### 3. Runtime locations

| Purpose | Now | After H1.0 |
| --- | --- | --- |
| Default `output_root` | `outputs/shade_map` | `runs` |
| Engine work folder of a run | `outputs/shade_map_work/<name>-<id12>` | `work/runs/<name>-<id12>` |
| Run-name locks | `outputs/shade_map_work/.locks` | `work/locks` |
| Request-local source views | `outputs/region_views/<key>` | `work/source_views/<key>` |
| Fill-impact work | `outputs/sea2_2_diagnostic_work` | `work/fill_impact` |
| Lower-level engine and adapter defaults | `outputs/v1_query`, `v2_batch`, `v2_state`, `region_request` | under `work/engine/` |
| iB5000 validation work | `outputs/sea2_2_*` | `work/validation_*` |
| Horizon caches | `data/processed/shade_v1/<namespace>` | `data/cache/horizon/<namespace>` |
| Views, pointers, build locks | `data/processed/dsm_views/sea_fill_v2_2/` | `data/derived/views/` |
| Ingested catalogues | `data/processed/dsm_catalogues/<city>/` | `data/derived/catalogues/<city>/` |
| Fill-impact results | `<output_root>/_diagnostics/fill_impact/` | unchanged |

- **Cache namespaces:** `view_<view_id12>` for a view; `<cache_namespace>_<city_id>` for `raw`, for every city including `hong_kong`, with default `cache_namespace` `raw`; `fill_impact_<id12>` for the fill-impact counterfactual.
- **Ownership rules** keep their present logic with the new names: engine outputs must lie under `work/`, caches under `data/cache/horizon/`, and an `output_root` inside the repository must lie under `runs/` or directly under the repository root. It may not lie inside `data/`, `work/`, `baselines/`, `archive/` or a DSM directory.
- The run folder structure `<name>/<YYYYMMDD>/<HHMM>/` and every published file name are unchanged.
- No code creates `outputs/` or `data/processed/`.

### 4. Data moves

Moves are renames on the same volume. Sizes and modification times of files must not change.

| Now | After H1.0 |
| --- | --- |
| `data/raw/dsm/2020/` | `data/raw/hong_kong/dsm_cedd_2020/` |
| `data/raw/dsm/2020_HKUST_Around/` | `data/raw/hong_kong/dsm_cedd_2020_hkust/` |
| `data/raw/dsm/` loose files (metadata page, two terms PDFs, `README.md`) | `data/raw/hong_kong/dsm_cedd_2020_docs/` |
| `data/raw/coastline/`, `validation/`, `basemap/` | `data/raw/hong_kong/coastline/`, `validation/`, `basemap/` |
| `data/raw/dsm/rotterdam_ahn4_dsm05/` | `data/raw/rotterdam/dsm_ahn_05m/` |
| `data/processed/shade_v1/sea_fill_v2_2_8ee51b017411` | `data/cache/horizon/view_<new Hong Kong view_id12>` |
| `data/processed/shade_v1/sea_fill_v2_2_4b2c2e76ca8b` | `data/cache/horizon/view_<new Rotterdam view_id12>` |
| `data/processed/shade_v1/g1_dev_raw_20261111` | `data/cache/horizon/raw_hong_kong` |
| `data/processed/shade_v1/g1_dev_raw_20261111_rotterdam` | `data/cache/horizon/raw_rotterdam` |
| `data/processed/dsm_views/sea_fill_v2_2/` (present content) | `archive/data_processed/dsm_views/sea_fill_v2_2/` |
| `data/processed/dsm_catalogues/` (present content) | `archive/data_processed/dsm_catalogues/` |
| `outputs/v2_daylight_cheungchau_20261009` | `baselines/e2_cheung_chau_20260107` |
| `outputs/shade_map` (whole folder) | `baselines/measure_5regions_20261110` |
| `outputs/shade_map_g1_dev_20261111` | `baselines/g1_dev_20261111` |
| every other entry of `outputs/` | `archive/outputs/<same name>` |
| `archive/removed/`, `archive/baseline_h1_0_20261112/` | stay |

- Tracked `README.md` files move with their folders (`git mv`). `outputs/README.md` moves to `docs/records/outputs_README.md` and `data/processed/README.md` to `docs/records/data_processed_README.md`.
- The contents of moved folders are not edited. Links inside archived folders may dangle after the move; that is accepted.
- After the archive move, run `git worktree prune`. The six old worktree folders stay as plain folders in the archive.
- `.gitignore` ignores `runs/`, `work/`, `baselines/`, `archive/`, `data/derived/`, `data/cache/` and everything under `data/raw/` except the tracked `README.md` files. `presentations/` stays ignored.
- `data/processed/` and `outputs/` no longer exist.

### 5. Views and catalogues

- Rebuild the Hong Kong view once with the moved code and the moved raw catalogue. Register Rotterdam once.
- Every tile and surface file of each new view has the SHA-256 that the archived accepted manifest records for the file of the same name. Each new view manifest equals the archived one in every field except `view_id` and `build_code_sha256`.
- Each new view pointer equals the archived one in every field except `view_id`; for Rotterdam also except `header_inventory[*].mtime_ns`.
- Every tile of the new Rotterdam ingestion has the same SHA-256 as in the archived one. Its `manifest.json` equals the archived one in every field except `ingest_id` and `ingestion_code_sha256`. Its `registration_report.json` and `current.json` equal the archived ones in every field except `ingest_id`.
- After the rebuild, move the two view cache namespaces to their new names (design item 4). Do not copy or recompute cache entries.

### 6. Records

- Move to `docs/records/`, keeping each relative path below `docs/`: the folders `v1`, `v2`, `v3`, `region`, `sea`, `sea2`, `shade_map`, `city`, `ui`, `prompts`, and the top-level files `ARCHITECTURE.md`, `GUIDE.md`, `GUIDE.zh-TW.md`, `METHOD.md`, `METHOD_legacy.md`, `NATIVE_MOSAIC_2026-09-29.md`, `NATIVE_TILE_UNITS_2026-09-28.md`, `PROJECT_STATUS_2026-10-29.zh-TW.md`, `QA.md`, `QA_100x100.md`, `QA_600x450_legacy.md`, `RUN_INDIVIDUAL_TILES.md`, `TILING_RESEARCH_2026-09-28.md`.
- Two exceptions: `docs/v2/estimator.json` moves to `config/engine/estimator.json`, byte-identical; the present `README.md` moves to `docs/records/README_pre_h1.md`.
- Every moved record is byte-identical to the file before the move. Records are never edited, including their links.
- Stay in place: `docs/planning/` (not edited by the developer), `docs/packages/H1.0/`, `docs/CONVENTIONS.md`, and `docs/OUTPUT_CODES.md`. In `docs/OUTPUT_CODES.md` only the two path mentions (`src/shade_watch.py`, `docs/v1/POLICY.md`) may be updated.
- A new `README.md` holds only: the project name, one paragraph that says the layout follows `docs/CONVENTIONS.md`, the three commands of design item 1, and a note that the full README follows at closeout.

### 7. Legacy

Moved unchanged, not maintained and not expected to run:

| Now | After H1.0 |
| --- | --- |
| `src/batch_tiles.py`, `src/verify_chunking.py`, `src/verify_mosaic.py` | `legacy/pipeline/` |
| `tools/sea_view/`, `tests/test_sea_masks.py` | `legacy/b1_sea_view/` |
| `tools/v1_development.py`, `v2_development.py`, `v2_closeout.py`, `v3_campaign.py` | `legacy/campaigns/` |
| `tools/sea2/checks.py`, `tools/sea2/resources.py`, `tests/test_sea2_checks.py` | `legacy/campaigns/b2_2/` |
| `tests/shade_map_campaign.py`, `tests/shade_map_repair_campaign.py` | `legacy/campaigns/f1/` |
| `tools/wsl2_smoke/` | `legacy/wsl2_smoke/` |
| `web/index.html`, `web/console/` | `legacy/web/` |
| `config/mosaic_6tiles.json`, `config/v3/` | `legacy/config/` |

- `config/study_area.md` and `config/processing.json` move to `config/engine/`.
- `web/shade_map/` moves to `web/viewer/`. Its default folders become `runs` and `baselines`, and it contains no `outputs/` path. Its `README.md` changes only in paths, commands and the view ID it names. `data/cells.json` is regenerated from the new Hong Kong view and must have the same cell list as before.
- **Retired tests** (they test retired code): every test of `tests/test_sea_masks.py` and `tests/test_sea2_checks.py`, and `test_campaign_internal_dispatch_is_not_recursive` in `tests/test_shade_map.py`. No other test is removed.
- All other tests stay in `tests/`. They change only in imports, module names and paths.

### 8. User's machine config

`config/machine.local.json` is the user's ignored file. Update only these values in it and report the difference:

| Key | New value |
| --- | --- |
| `dsm_dir` | `data/raw/hong_kong/dsm_cedd_2020/D12.DSM.TIFF` |
| `output_root` | `runs` |
| `cache_namespace` | `raw` |
| `cities.rotterdam.raw_dir` (added) | `data/raw/rotterdam/dsm_ahn_05m` |

`config/machine.example.json` shows the same values.

### 9. Layout check

`tests/test_layout.py` checks, as part of the test suite:

1. The repository's top level holds only: `README.md`, `.gitignore`, `requirements.lock.txt`, `requirements.tools.lock.txt`, `shade_watch/`, `config/`, `tests/`, `web/`, `docs/`, `legacy/`, `references/`, `data/`, and the ignored `runs/`, `work/`, `baselines/`, `archive/`, `presentations/`, `.venv/` and tool caches.
2. `docs/` holds only: `CONVENTIONS.md`, `OUTPUT_CODES.md`, `packages/`, `planning/`, `records/`, and the documents that closeout adds (`INDEX.md`, `ARCHITECTURE.md`, `GUIDE.md`, `GUIDE.zh-TW.md`, `design/`).
3. `src/`, `tools/`, `outputs/` and `data/processed/` do not exist.
4. No tracked file refers to an old location or import: `from src`, `import src`, `from tools`, `import tools`, and the paths `src/`, `tools/`, `outputs/`, `data/processed`, `data/raw/dsm`, `shade_map_work`, `region_views`, `sea2_2_diagnostic_work`, `dsm_views`, `shade_v1`. Excluded from this rule: `docs/records/`, `docs/planning/`, `docs/packages/`, `docs/CONVENTIONS.md`, `legacy/` and `tests/test_layout.py` itself. The patterns must not match unrelated words; the report lists them.
5. The three cache-key files have the SHA-256 values of this contract.
6. `docs/records/` matches a manifest of paths and SHA-256 values written at the move (`docs/packages/H1.0/evidence/records_manifest.json`).

### 10. Developer documents

- `docs/packages/H1.0/DEVELOPMENT_REPORT.md` with evidence under `docs/packages/H1.0/evidence/` (text and JSON only).
- The evidence includes the complete move table: every old path and its new path, for tracked files and for data folders.
- A listing or log larger than 1 MB is kept under `archive/reviews/h1_0_dev_<YYYYMMDD>/`, and the report records its path and SHA-256.

## Authorized computation

| Run | What | Reference |
| --- | --- | --- |
| V-1 | Rebuild the Hong Kong view once | archived view `8ee51b01…` |
| V-2 | Register Rotterdam once | archived catalogue `7272bb1a…` and view `4b2c2e76…` |
| R-1 | Hong Kong, `raw`, Cheung Chau `[820250, 807200]`→`[821750, 808400]`, 2026-01-07, daylight, 10 min (65 frames) | the shade and quality rasters under `baselines/e2_cheung_chau_20260107/combined/`, matched by UTC time |
| R-2 | The `measure_lo_wu` region, `sea-2.2`, 2026-06-21 and 2026-12-22 (146 frames) | `baselines/measure_5regions_20261110/measure_lo_wu` |
| R-3 | The `measure_tai_mo_shan` region (146 frames) | same root, `measure_tai_mo_shan` |
| R-4 | The `measure_central` region (146 frames) | same root, `measure_central` |
| R-5 | Rotterdam, `projected` `[91875, 436875]`→`[93125, 438125]`, 2026-06-21 and 2026-12-22, daylight, 30 min (50 frames) | `baselines/g1_dev_20261111/g1_dev_nl1` |
| R-6 | `from shade_watch import shade_map` with `city="rotterdam"`, WGS84 `[51.9200, 4.4750]`→`[51.9230, 4.4800]`, no `dsm_source`, instants 2026-06-21 09:00, 13:40, 18:00 | `baselines/g1_dev_20261111/g1_dev_nl2` |
| R-7 | Fill-impact on R-5 with `--times 0900,1330,1800` (five frames) | the `frames` list and `raw_catalogue_sha256` of `baselines/g1_dev_20261111/_diagnostics/fill_impact/g1_dev_nl1/fill_impact.json` |
| R-8 | Plan only: `config/regions/cheung_chau.json` and a `shade-map-region-1.0` file without `dsm_source`, with the user's updated machine config | both plan as Hong Kong with `raw` |

R-1 to R-4 repeat HK-1 to HK-4 of the accepted G1.0 work, and R-5 to R-7 repeat NL-1, NL-2 and NL-4. R-1 and R-5 use the region configs of that work (`docs/records/city/evidence/configs/hk1.json` and `nl1.json`) and R-6 uses the arguments of NL-2 (`campaign.py` in the same folder); only `name` changes. R-2 to R-4 use the files in `config/regions/` as they are. R-7 computes the directions of its counterfactual again, in a `fill_impact_<id12>` namespace; this is the only authorized direction computation.

Direct comparison scripts and hashing are not limited. Nothing else that computes shade is authorized.

Development publishes under `runs/h1_0_dev_<YYYYMMDD>/`. Independent acceptance publishes under `runs/h1_0_review_<sha12>_<YYYYMMDD>/`, keeps its evidence and its worktree under `archive/reviews/h1_0_<sha12>_<YYYYMMDD>/`, repeats R-1 to R-8 in the main checkout, and registers Rotterdam afresh in its worktree. It does not rebuild the Hong Kong view.

## Budgets

| Budget | Development | Independent acceptance |
| --- | --- | --- |
| Hong Kong view rebuild (wall clock, sleep included) | ≤ 60 min, once | none |
| Rotterdam registration | ≤ 10 min, once | ≤ 10 min, once, in the worktree |
| Shade jobs and plans (R-1 to R-8) | ≤ 90 min | ≤ 90 min |
| Total job memory | ≤ 12 GiB | ≤ 12 GiB |
| New artifacts | ≤ 15 GiB | ≤ 10 GiB |

Keep the computer awake during timed jobs. Start the metering before a job reads data. Guard every wrapper against re-entry by worker processes. Record start, end and peak memory of every job that reads real DSM. When a budget runs out, the criteria it affects become NOT VERIFIED. Budgets may not be extended.

## Write scope

- The developer may move, add and edit tracked files as this contract requires, in one local commit. `docs/planning/`, `docs/packages/H1.0/CONTRACT.md`, the two prompts and `docs/CONVENTIONS.md` are not edited.
- On disk, the developer performs the moves of design item 4, creates the new view, catalogue, runs and work files, and updates the user's machine config as in design item 8.
- **Nothing is deleted,** except: directories left empty by a move, the three one-byte `.gitkeep` files (`src/`, `tests/`, `web/`), `__pycache__`, `.pytest_cache`, `.DS_Store`, and the worktree registrations removed by `git worktree prune`.
- Every file and symlink that the planner baseline lists under `data/raw`, `data/processed`, `outputs` and `archive` exists after H1.0 at its mapped path with the same size and modification time. `.DS_Store` files and entries inside `__pycache__` or `.pytest_cache` are outside this rule.

## Acceptance matrix

Each item is PASS, FAIL or NOT VERIFIED, with evidence. The package is accepted only if every item is PASS.

| Item | Requirement | Evidence |
| --- | --- | --- |
| H1-01 | Traceability and scope. One local commit on the starting commit; contract hash recorded; nothing pushed. With rename detection, every changed product file differs from its origin only in imports, module names, paths and the items this contract names. `docs/planning/`, the contract, the prompts and the conventions are unchanged. | `git diff -M --stat`, reviewed diffs, hashes. |
| H1-02 | Cache-key files. `shade_watch/engine/horizon.py`, `spatial.py` and `v1_cache.py` have the SHA-256 values of this contract. `fingerprint` and `profile` have unchanged source text. | Hashes; diff of `pipeline.py`. |
| H1-03 | Layout. `tests/test_layout.py` passes. The reviewer checks rules 1 to 6 of design item 9 with a script of their own. | Test output; reviewer's script. |
| H1-04 | Records. Every record under `docs/records/` is byte-identical to its file at the starting commit, at the mapped path; none is missing; `config/engine/estimator.json` equals the former `docs/v2/estimator.json`. | Blob comparison against the starting commit. |
| H1-05 | Data moves. Every file and symlink of the planner baseline exists at its mapped path with the same size and modification time (exceptions as in the write scope). The two Rotterdam sheets and at least 300 Hong Kong tiles chosen by the reviewer have unchanged SHA-256. Nothing is missing, and nothing outside the allowed deletions was removed. | Listing comparison under the move table; hashes. |
| H1-06 | Tests. The collected test IDs equal those at the starting commit, minus the retired tests of design item 7, plus the layout tests, with module paths and path-valued parameters mapped. All pass. No remaining test changed in more than imports, module names and paths. | `pytest --collect-only` at both commits; `pytest tests`; test diffs. |
| H1-07 | Behaviour. Every file under `config/cities/`, `config/sea_profiles/` and `config/regions/` is byte-identical. Schemas differ only in default paths and their descriptions. Policy IDs, source names, schema names and the publication format are unchanged. R-8 plans as Hong Kong with `raw`. The rejections tested in G1-06 still return `invalid input` and exit 2. | File hashes; schema diffs; plans; CLI transcripts. |
| H1-08 | Hong Kong view. Every tile and surface file of the new view has the SHA-256 recorded for the same name in the archived accepted manifest; class totals are equal; the new manifest equals the archived one except `view_id` and `build_code_sha256`; the new pointer equals the archived one except `view_id`. The reviewer hashes every file of the new view. | Reviewer's script and its output. |
| H1-09 | Rotterdam. The same for the Rotterdam view. The new ingestion has the tile hashes of the archived catalogue, and its three JSON files equal the archived ones except the fields named in design item 5. A fresh registration in the review worktree gives the developer's IDs and file hashes; its view pointer equals the developer's except `header_inventory[*].mtime_ns`. | Reviewer's script; both registrations. |
| H1-10 | Cache keys. R-1 to R-6 plan zero missing directions and compute zero directions. In the four moved cache namespaces, every entry of the planner baseline is present with the same size and modification time, and none was added or changed by R-1 to R-6. | Plans; run logs; namespace listings before and after. |
| H1-11 | Pixels. R-1: the 65 frames match the 65 reference frames by UTC time, and every shade and quality raster is pixel-identical. R-2 to R-6: every shade, quality and surface raster is pixel-identical to its reference; frame lists, folder names and per-frame counts are identical. R-7: the `frames` list and `raw_catalogue_sha256` equal the reference. | Per-frame comparison tables; zero differing pixels. |
| H1-12 | Runtime locations. R-1 to R-7 write only under `runs/`, `work/`, `data/derived/` and `data/cache/`. `outputs/` and `data/processed/` are not created. The published runs follow the F format, and their manifests record the new paths. | Listings before and after; manifests. |
| H1-13 | Names. The imports and commands of design item 1 work as written, without a double-import warning. R-6 is started through `from shade_watch import shade_map`. The viewer's files contain no old path, and its regenerated cell index has the same cells. `config/machine.example.json` and the user's machine config hold the new values and only the allowed keys changed. | Transcripts; text search; cell index comparison; config diff. |
| H1-14 | Documents and budgets. The development report holds the matrix, the complete move table and the job ledger. Every job has start, end and peak memory, and every budget is met. No network access by the tools. | Report; ledger. |

## Decisions and release

- A PASS on all fourteen items means: the layout and the names follow the conventions, and results are unchanged — numerical consistency on four Hong Kong regions and two Rotterdam runs, with unchanged cache keys and views of identical content.
- It does not mean: observational accuracy for any city; verified Rotterdam surface labels; Windows support; that `pipeline.py` and `shade_watch.py` are clean.
- After acceptance the planning conversation writes the living documents and tags the result `mac-v1.0`. The user pushes.
- Fixes need a new commit SHA and targeted re-acceptance. Failure evidence is preserved.
