# Package H1.0 independent acceptance prompt

Independently assess the H1.0 implementation of `shade_watch_hk` against `docs/packages/H1.0/CONTRACT.md` (`SW-H1.0`). This is a review, not a second development pass. Re-running the developer's checks is not enough.

H1.0 claims that only names and locations changed. Your task is to try to show the opposite: a changed rule, a changed pixel, a lost file, an edited record, a changed cache key.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`, with the repository's `.venv`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA and its parent (the H1.0 planning commit, whose own parent is `cfb6e3c52001103a206c256c1af46bcdce30f01c`);
  - the SHA-256 of the contract and of any amendment, compared with the values given in the handoff message;
  - the accepted G1.0 commit `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d`;
  - the environment and its lock;
  - the archived accepted Hong Kong view `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1`, the archived Rotterdam catalogue `7272bb1a…` and view `4b2c2e76…`, and the three baselines.
- **Two places to work.**
  - **Main checkout,** for everything that needs the Hong Kong view and the caches. Its HEAD must be `TARGET_COMMIT` or a descendant whose difference from `TARGET_COMMIT` holds only added files and modifications under `docs/planning/`; no tracked file may be modified in the working tree. If not, stop and report.
  - **Review worktree,** a Git-managed detached worktree at `archive/reviews/h1_0_<candidate12>_<YYYYMMDD>/worktree` at exactly `TARGET_COMMIT`, for the fresh Rotterdam registration. Point its machine config at the main checkout's absolute raw paths.
- **Write only:**
  - evidence and the worktree under `archive/reviews/h1_0_<candidate12>_<YYYYMMDD>/`;
  - publications under `runs/h1_0_review_<candidate12>_<YYYYMMDD>/`, and the work files that the tools create for those run names under `work/`;
  - the report file named below.
- **Read-only:** raw data, the views, the catalogues, every cache namespace, the baselines, the archive, the developer's runs.
- **Do not:** change production code, tests, config or records; rebuild the Hong Kong view; fix a defect; push.

## Budget

- Shade jobs and plans (R-1 to R-8): 90 minutes. Rotterdam registration in the worktree: 10 minutes, once. Job memory: 12 GiB. New artifacts: 10 GiB.
- For planning the order: the G1.0 development ledger (`docs/records/city/evidence/resources.jsonl`, four workers) records HK-1 6.8 min with directions computed, HK-2 12.3, HK-3 11.8, HK-4 9.1, NL-1 11.6 with directions computed, NL-2 0.3, NL-4 1.1, and 2.1 min for the Rotterdam registration. These are measurements of that day, not guarantees. If the budget runs out, the criteria it affects are NOT VERIFIED.
- Measure wall time with a clock that includes system sleep, run jobs under `caffeinate -dims`, start the metering before a job reads data, and guard every wrapper against re-entry by worker processes. Use four workers for the regression runs.
- Hashing and listing do not count as shade jobs, but record them.

## Required independent work

1. **Scope and diff** (H1-01, H1-02).
   - `git diff -M --name-status <parent> <TARGET_COMMIT>`. Classify every entry: pure rename, rename with edits, new file, deleted file. No file may be deleted unless the contract names it or it reappears at a mapped path.
   - Read every rename with edits. Each edit must be an import, a module name, a path, or an item the contract names. Report anything else, however small.
   - Confirm the three cache-key hashes, and that `fingerprint` and `profile` are textually unchanged.
   - Confirm that `docs/planning/`, the contract, the prompts and `docs/CONVENTIONS.md` are unchanged.
2. **Records** (H1-04). With your own script, compare every blob under `docs/records/` and `config/engine/estimator.json` with its origin at the parent commit. Confirm that no file that the contract lists as a record is missing.
3. **Data moves** (H1-05). Check the SHA-256 of the planner baseline `archive/baseline_h1_0_20261112/listing.tsv` against the contract. Compare it, and the developer's inventory, with the present state under the move table: every file and symlink present, same size, same modification time. Hash the two Rotterdam sheets and at least 300 Hong Kong tiles of your own random choice (record the seed) and compare with the hashes in the archived Hong Kong view manifest's catalogue record.
4. **Layout** (H1-03). Check rules 1 to 6 of contract design item 9 with a script of your own, written from the contract text. Then run `tests/test_layout.py`.
5. **Tests** (H1-06). Run `pytest --collect-only -q` at the parent (in a second detached worktree under the same review folder, used for collection only) and at the candidate. Map module paths and compare the sets of test IDs. Run the full suite. Read the diff of every remaining test file.
6. **Behaviour** (H1-07). Compare `config/cities/`, `config/sea_profiles/` and `config/regions/` byte for byte. Read the schema diffs. Search for the policy IDs, source names, schema names and the publication format. Run R-8. Repeat the rejections of G1-06 with the new commands.
7. **Views and catalogue** (H1-08, H1-09).
   - Hash every file of the new Hong Kong view and compare with the hashes recorded in the archived accepted manifest; compare the two manifests field by field.
   - Do the same for the Rotterdam view. For the Rotterdam ingestion, compare the tile hashes and the three JSON files with the archived ones, as in contract design item 5. Compare both view pointers with the archived ones.
   - Register Rotterdam afresh in the review worktree and compare IDs, file hashes and the pointer (equal except `header_inventory[*].mtime_ns`).
8. **Cache keys and pixels** (H1-10, H1-11, H1-12), in the main checkout.
   - Take a listing of every cache namespace and of `data/derived/` before the runs.
   - Run R-1 to R-7 under your own names. Before each of R-1 to R-6, observe the plan: zero missing directions. For R-2 to R-4, confirm that the spatial keys are those recorded as `cache_gates` in `docs/records/city/evidence/hk2-plan.json` to `hk4-plan.json`.
   - Compare every raster with its baseline with your own comparison script; compare frame lists, folder names and per-frame counts. R-1's baseline has the older E2.0 layout: match its `combined/` rasters by UTC time. For R-7, compare the `frames` list and `raw_catalogue_sha256` with the reference report.
   - After the runs: no cache namespace gained or changed an entry, apart from the fill-impact namespace of R-7; `outputs/` and `data/processed/` do not exist; everything written lies under `runs/`, `work/`, `data/derived/` or `data/cache/`.
9. **Names** (H1-13). Run the imports and commands of contract design item 1 as written, with warnings shown, and confirm that none loads a module twice. Start R-6 through `from shade_watch import shade_map`. Search the viewer for old paths and compare the regenerated cell index with the previous one. Compare the user's machine config with the copy in `archive/baseline_h1_0_20261112/`: only the four keys of contract design item 8 changed.
10. **Documents and ledger** (H1-14). Check the development report: matrix, move table, ledger, budgets.

## Report and release gate

Write the report to `docs/packages/H1.0/ACCEPTANCE_REPORT_<candidate12>.md` in the main checkout. Do not commit it. The report contains:

- the candidate SHA, its parent and the contract hash;
- environment and input identities;
- a budget ledger;
- one row per criterion, H1-01 to H1-14, marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

H1.0 is ACCEPTED only if all of H1-01 to H1-14 pass. Report engineering acceptance and numerical consistency separately. Observational accuracy remains NOT VERIFIED for both cities.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved.
