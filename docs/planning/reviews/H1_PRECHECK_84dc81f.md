# H1.0 static pre-check of candidate `84dc81f` (2026-11-13)

Done by the planning conversation on the linked Mac, read-only, on 2026-11-13 between 00:38 and 00:55 HKT. It checks the candidate against `docs/packages/H1.0/CONTRACT.md` (`SW-H1.0`) with `AMENDMENT_1.md` (`SW-H1.1`).

**This is not an acceptance.** No test was run and no shade was computed. Every item of H1-01 to H1-14 remains for the independent reviewer. The reviewer must not rely on this document for any verdict.

## Candidate

- Candidate: `84dc81fddb3b297881d921fe0125f6783780bbae`, one commit on `dc7ad088cc3739aa4d54f6415088629328f92140` (the commit that adds the amendment). Branch `feature`. Working tree clean. `origin/feature` is still `cfb6e3c`: nothing was pushed.
- Developer-reported identities: Hong Kong view `412eae7951535ccf4f747be461ebcfe64f4e812d67a4d93f558150a718277d5e`; Rotterdam ingestion `ce865fa2895066d03fba441ec6a6ce80d0c8f41c387a1e21e0614136baeb36a3`; Rotterdam view `11004a24a611e773a72b08cbc30e31cfda15ec462a18654105956bcdf15193eb`.
- Developer report: `docs/packages/H1.0/DEVELOPMENT_REPORT.md`. It marks H1-03, H1-05, H1-08 and H1-09 NOT VERIFIED because their reviewer-only parts are pending, and the other ten items PASS.

## What the planner checked, and the result

All checks used the planner's own scripts, written from the contract text.

| Subject | Check | Result |
| --- | --- | --- |
| Protected files | `docs/planning/`, contract, amendment, two prompts, conventions: `git diff dc7ad08 84dc81f` | No change |
| Cache-key files | SHA-256 of `shade_watch/engine/horizon.py`, `spatial.py`, `v1_cache.py` | Equal to the contract's three values |
| `fingerprint`, `profile` | Function source text at the parent and at the candidate | Identical |
| `polygonal` (A5) | Function source text in `shade_watch/fill/validate_ib5000.py` against `tools/sea_view/extract.py` at the parent | Identical |
| Diff shape | `git diff -M --name-status dc7ad08 84dc81f` | 625 entries: 522 pure renames, 38 renames with edits, 19 modified, 43 added, 3 deleted (the three `.gitkeep` files) |
| Records | Blob of every file under `docs/records/` and of `config/engine/estimator.json` against its origin at the parent | 466 of 466 identical; none missing; no extra file under `docs/records/` |
| Legacy | Blob of every file under `legacy/` against its origin | 37 of 37 identical; no extra file |
| Frozen configs | Blobs under `config/cities/`, `config/sea_profiles/`, `config/regions/` | Identical (2, 2 and 7 files) |
| Layout | Top-level and `docs/` entries; `src/`, `tools/`, `outputs/`, `data/processed/` | As design item 9; the four old folders do not exist |
| Old references | Own search of tracked files for the patterns of rule 4, with the exclusions of the contract and of A2 | No match |
| Data moves | Every file and symlink of `archive/baseline_h1_0_20261112/listing.tsv` (SHA-256 confirmed) at its mapped path: size, modification time, link target | 133,197 files and 5,889 symlinks present and unchanged; 1,052 excepted entries (`.DS_Store`, `__pycache__`, `.pytest_cache`) not compared; nothing missing |
| View manifests | New against archived, field by field | Hong Kong and Rotterdam: only `view_id` and `build_code_sha256` differ; class totals equal; file-name sets match the manifests |
| View pointers | New against archived | Hong Kong: only `view_id` differs. Rotterdam: `view_id` and `header_inventory[*].mtime_ns` |
| Ingestion | `manifest.json`, `registration_report.json`, `current.json` against the archived ones | `manifest.json`: `ingest_id` and three ingestion-code hashes differ. The other two: only `ingest_id` |
| Content samples | SHA-256 of 40 tiles and 40 surface files per view, and 30 ingested tiles, chosen with seed 20261113, against the archived manifests | All equal. The planner did not hash every file |
| Regression samples | Frame lists of R-2 to R-6 against their baselines; all rasters of four random frames per run (three for R-6) | Frame lists equal; 285 of 285 sampled rasters byte-identical. R-1 has 65 frames; the baseline has 65 shade and 65 quality rasters. The planner did not compare R-1 pixels |
| Machine config | `config/machine.local.json` against the baseline copy | Only the four keys of design item 8 changed |
| Worktrees | `git worktree list` | Only the main checkout |
| Budgets (developer ledger, not re-measured) | `evidence/resources.jsonl` | Hong Kong rebuild 33.46 min of 60; Rotterdam registration 3.37 of 10; R-1 to R-8 47.49 of 90; peak memory 2.31 GiB of 12; new artifacts 6.50 GiB of 15 |

The planner read every changed line of the 38 renamed-and-edited files and the 19 modified files (1,105 changed lines, of which 88 are the new `tests/test_layout.py`). Apart from the observations below, the changes are imports, module names, paths, and items that the contract or the amendment names.

## Not checked by the planner

- The test suite. The linked shell cannot run the Mac environment. The developer reports 309 tests at the parent and 308 at the candidate: seven retired (six in `tests/test_sea_masks.py`, one in `tests/test_shade_map.py`) and six layout tests added.
- Whether any run computed directions, and the cache listings before and after the runs.
- A full hash of the views, a full pixel comparison, the fresh Rotterdam registration, the commands and imports of design item 1.

## Observations for the reviewer

**O1. Logic added to two engine files.** `shade_watch/engine/shade_watch.py` and `shade_watch/engine/v2.py` gained:

```python
if __name__ in ("__main__", "__mp_main__") and __spec__ is not None:
    sys.modules[__spec__.name] = sys.modules[__name__]
```

and `v2.py` gained `import sys`. This is not an import, a module name or a path.

- The developer's reason (report, "Tests and layout scan"): the rule of design item 1 that no command or worker may load a module twice.
- Reading the parent tree, `python -m src.v2` and `python -m src.shade_watch` loaded those files twice, because `v2_runner.py` and `v2_worker.py` import `.v2`, and the command entry of `shade_watch.py` imports `pipeline.py`, which imports `.shade_watch`. The planner inferred this from the imports and did not run it.
- R-1 to R-7 start `python -m shade_watch` and `python -m shade_watch.engine.v1`. As far as the planner can see, they do not start `v2.py` or `shade_watch.py` as commands, so the regression does not exercise these lines.
- Neither file is a cache-key file or a view-identity file.
- For the reviewer: decide under H1-01 and H1-13 whether this addition is covered by "the items this contract names"; confirm the behaviour at the parent; exercise `python -m shade_watch.engine.v2` on synthetic fixtures only.

**O2. `name_lock` takes the lock directory.** In `shade_watch/publish/common.py` the first parameter is now the lock directory itself (`work/locks`) and no longer a work root with `.locks` below it. All callers were changed. This follows from design item 3.

**O3. Output-root rules and the marker in `runs/`.** `validate_output_root` has two new rejections that state design item 3 (not inside `work/`, `baselines/` or `archive/`; inside the repository only under `runs/` or directly under the root). The report says that the ownership marker `runs/.shade_map_root.json` "was initialized so the default and the nested development output root can coexist". For the reviewer: establish whether the tool or the developer wrote that marker, and whether the default root `runs` works when `runs/` already holds a nested root. The nesting comes from the contract (default root `runs`, development root `runs/h1_0_dev_<date>`).

**O4. Cache namespace suffix.** `machine_for_city` now appends `_<city_id>` for every city, Hong Kong included, as design item 3 requires. One test fixture name changed with it (`fixture_f1` to `fixture_f1_hong_kong`).

**O5. Viewer folder search.** `web/viewer/results.js` now searches `runs/` and `baselines/` and their sub-folders for the root marker (design item 7). This is more than a path substitution.

**O6. Viewer README names the old view.** `web/viewer/README.md` line 65 still says that `data/cells.json` comes from view `8ee51b01…`. The regenerated `cells.json` records view `412eae79…`; its cell list equals the old one. The contract allowed the README to update the view ID but did not require it.

**O7. `work/numba/`.** The developer's metering script set `NUMBA_CACHE_DIR` to `work/numba`. No product code sets it.

**O8. Two failed comparison attempts.** The ledger records two attempts of the R-1 comparison script that ended with exit 1 before the final one (script error in the expected frame count, according to the report). R-1 itself ran once.

**O9. `docs/records/README_pre_h1.md` appears as an added file** in the rename-detected diff, because `README.md` still exists as the stub. Its blob equals the `README.md` of the parent.

**O10. Plans take one to three minutes each** in the developer ledger (R-1 to R-6 plans: 11.3 minutes in total; R-8: 1.5 minutes). The reviewer's 90-minute budget includes plans.

## Planner's reading

The static evidence is consistent with the claim that names and locations changed and results did not. O1 is the only change that needs a judgement about scope. O3 and O6 are small and may need follow-up at closeout whatever the verdict.
