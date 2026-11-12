# Package H1.0 development prompt

Implement package H1.0 for `shade_watch_hk`, as defined in `docs/packages/H1.0/CONTRACT.md` (`SW-H1.0`). Bring the repository and its data folders to the layout and names of `docs/CONVENTIONS.md`. This package changes names and locations only. Results must not change.

Three things must hold at the end:

- The three files that define the horizon cache key are byte-identical, and every regression run computes zero directions.
- The rebuilt Hong Kong view and the re-registered Rotterdam catalogue and view have the same file content as the accepted ones.
- Every regression run is pixel-identical to its baseline.

## Preconditions

- **Branch and baseline.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`, with the repository's `.venv`.
  - The starting commit's full SHA is given in the handoff message. It must contain `docs/packages/H1.0/CONTRACT.md` and `docs/CONVENTIONS.md`, and its parent must be `cfb6e3c52001103a206c256c1af46bcdce30f01c`.
  - Before changing anything, record: the actual HEAD; the branch; the dirty files; the SHA-256 of the contract, compared with the value given in the handoff message.
- **Stop and report** if any of the following differ:
  - the three SHA-256 values of the cache-key files listed in the contract;
  - tracked files under `src/`, `tools/`, `config/` or `tests/`, compared with `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d`, apart from the files added by `8d7a0d3` (four `config/regions/measure_*.json` and `tools/wsl2_smoke/`);
  - the content of `data/processed/`, compared with the list in the contract's starting facts;
  - the view IDs named by the two pointers in `data/processed/dsm_views/sea_fill_v2_2/`.
- **Read first:**
  - the whole contract and `docs/CONVENTIONS.md`;
  - `docs/planning/DECISIONS.zh-TW.md` (D-022 to D-025);
  - every Python file under `src/` and `tools/` for its imports and its hard-coded paths, before moving anything.
- **Not authorized:**
  - any change to `horizon.py`, `spatial.py`, `v1_cache.py`, or to the source text of `fingerprint` and `profile`;
  - any change of behaviour, rule, policy value, schema name, profile or region config;
  - splitting `pipeline.py` or the engine module `shade_watch.py`;
  - deleting data, apart from the exceptions in the contract's write scope;
  - editing a record, `docs/planning/`, the contract, the prompts or `docs/CONVENTIONS.md`;
  - computation outside V-1, V-2 and R-1 to R-8;
  - Windows work, new living documentation, downloads, push or PR.

## Suggested sequence

The order matters because old paths stop working once things move.

1. **Inventory first.** Take a listing of `data/raw`, `data/processed`, `outputs` and `archive` (path, type, size, modification time) and the SHA-256 of every tracked file. Keep it as evidence, and compare it with the planner baseline `archive/baseline_h1_0_20261112/listing.tsv`; report every difference before moving anything. Write the move table (old path → new path) for tracked files and for data folders before moving anything.
2. **Code.** Create the `shade_watch` package with `git mv`, keep the three cache-key files untouched, update imports, module names, entry points and hard-coded paths. Move retired code and tests to `legacy/` unchanged. Move `estimator.json`, `study_area.md` and `processing.json` to `config/engine/`. Run the remaining tests with synthetic fixtures until they pass.
3. **Records.** `git mv` the record folders and files to `docs/records/`. Write `docs/packages/H1.0/evidence/records_manifest.json` and confirm that every record is byte-identical.
4. **Raw data, baselines and archive.** Perform the moves of contract design item 4 with renames. Confirm sizes and modification times against the inventory. Run `git worktree prune` after the archive move. Update `.gitignore`.
5. **Views.** With the moved code and the moved raw catalogue: rebuild the Hong Kong view once (V-1) and register Rotterdam once (V-2). Compare every file with the archived accepted view and catalogue (H1-08, H1-09). If a file differs, stop and report; do not continue to the cache move.
6. **Caches.** Rename the four cache namespaces to their new names. Do not copy or recompute.
7. **Machine configs.** Update `config/machine.example.json`, and the allowed keys of the user's `config/machine.local.json`; report the difference.
8. **Regression.** Run R-1 to R-8 under `runs/h1_0_dev_<YYYYMMDD>/`. Copy the G1.0 region configs that the contract names to `docs/packages/H1.0/evidence/configs/` and change only `name`. Before each of R-1 to R-6, confirm that the plan shows zero missing directions. If it does not, stop and report. Compare every raster with its baseline.
9. **Viewer and stub.** Move the viewer to `web/viewer/`, update its default folders, regenerate the cell index and compare it. Write the README stub.
10. **Layout check.** Write `tests/test_layout.py` and run the full suite.
11. **Report.** `docs/packages/H1.0/DEVELOPMENT_REPORT.md` with the H1-01 to H1-14 matrix, the complete move table, the test-ID comparison, the job ledger and the limits.

## Facts that shape the work

Verify them as you go.

- `v1_cache.py` imports `.horizon`, `.pipeline` and `.spatial` relatively, so the three cache-key files and `pipeline.py` must sit in the same package.
- The adapter starts the engine with `python -m src.v1`, and the validation tool starts a worker with `-m tools.sea2.validation_worker`. If `shade_watch/__init__.py` imported `shade_watch.publish` at import time, `python -m shade_watch.engine.v1` would load `v1` twice. Expose `shade_map` and `plan_shade_map` lazily.
- The engine computes the repository root from the location of `shade_watch.py`. One level deeper, that expression must change. This file is not a cache-key file.
- The view builder hashes its own eight files under names it builds from a hard-coded prefix. The prefix and the imports change, so `build_code_sha256` and `view_id` change. Nothing else in the manifest should.
- The view pointer stores sizes and modification times of the catalogue files. Do not rewrite catalogue files after a view is built.
- The accepted Hong Kong view holds 1,654 symlinks to raw tiles. After the raw data move they dangle in the archive. Compare against the hashes recorded in the archived manifest.
- The G1.0 evidence records the spatial keys of HK-2 to HK-4 (`cache_gates` in `docs/records/city/evidence/hk*-plan.json`). R-2 to R-4 must use the same keys.
- Durations in the G1.0 development ledger (`docs/records/city/evidence/resources.jsonl`, four workers): HK-1 6.8 min with directions computed, HK-2 12.3, HK-3 11.8, HK-4 9.1, NL-1 11.6 with directions computed, NL-2 0.3, NL-4 1.1; Rotterdam registration 2.1 min. These are measurements of that day, not guarantees.
- `tests/test_shade_map.py` holds one test that loads the F1 campaign file; it is retired with that file.
- Six worktrees are registered under `outputs/`. Move their parent folders, then prune.
- The user's `config/machine.local.json` is ignored by Git and holds old paths.

## Resources and monitoring

- **Measure every process** that reads real DSM data, including plans. Record wall time, peak memory of the whole command and new-artifact bytes in `docs/packages/H1.0/evidence/resources.jsonl`. Start the metering before the job reads data, and guard every wrapper against re-entry by worker processes.
- **Use a wall clock that includes system sleep.** Run jobs under `caffeinate -dims`.
- **Budgets:** Hong Kong view rebuild ≤ 60 min, once; Rotterdam registration ≤ 10 min, once; shade jobs and plans ≤ 90 min; job memory ≤ 12 GiB; new artifacts ≤ 15 GiB. When a budget runs out, mark the affected criteria NOT VERIFIED; do not extend it.

## Deliverables

- The repository and the data folders in the new layout.
- The H1-01 to H1-14 matrix in the development report, each item PASS, FAIL or NOT VERIFIED with evidence paths. Mark the reviewer-only parts NOT VERIFIED: the fresh Rotterdam registration in another worktree and the reviewer's own scripts.
- One local commit. Inspect the staged diff with rename detection before committing.

Report the full commit SHA, the new Hong Kong `view_id`, the new Rotterdam `ingest_id` and `view_id`. Do not push, and do not declare acceptance; hand off for independent acceptance.
