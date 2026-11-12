# Package H1.0 amendment 2 — repair after the first independent acceptance

Amendment ID: `SW-H1.2`
Amends: `SW-H1.0` (`CONTRACT.md`, SHA-256 `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c`) as amended by `SW-H1.1` (`AMENDMENT_1.md`, SHA-256 `b07551ce74958863e709625a980e0d727f05e3382902d566771f0830b22976ea`). Neither file is edited.
Status: frozen by the commit that adds this file, by user decision of 2026-11-13 03:05 HKT (D-029). Record this file's SHA-256 before the repair.
Decision records (snapshot in `docs/planning/DECISIONS.zh-TW.md`): D-027 to D-029.

The contract and amendment 1 apply as written, except for the items below. Where they differ, this amendment applies. If two requirements conflict, or a requirement cannot be met, stop and report. Do not choose.

This file has three parts: changes to the contract (A), the repair (B, for the developer), and the targeted re-acceptance (C, for the reviewer). It is the only instruction document of the repair round. `DEVELOPMENT_PROMPT.md` and `ACCEPTANCE_PROMPT.md` stay as records of the first round; their general rules on metering, evidence and independence still apply where this file does not say otherwise.

## Why

The first independent acceptance of candidate `84dc81fddb3b297881d921fe0125f6783780bbae` ended NOT ACCEPTED: `docs/packages/H1.0/ACCEPTANCE_REPORT_84dc81fddb3b.md` (SHA-256 `8df2c93139687835ec21a0eaa98a4c89ae21cbe5949e6adb8c17138ed9bd13e7`). Eight items passed. H1-01, H1-03 and H1-13 failed. H1-10, H1-11 and H1-12 were not verified.

| Report defect | Cause | Item below |
| --- | --- | --- |
| 1. Module aliases in two engine files exceed the scope | Design item 1 of the contract required that no module is loaded twice. That could only be met by changing code. | A6 |
| 2. The older pipeline entry opens `src/horizon.py` | A path built with `ROOT/'src'/p` was not migrated. Layout rule 4 searched for the string `src/` only. | A7 |
| 3. Publishing to a folder under `runs/` first makes the default root `runs` unusable | The contract made `runs` the default output root and also put the development and review roots below it. | A8 |
| 4. The reviewer could not run R-2 to R-4 | The contract made R-2 to R-4 use the region files as they are, so their work folders were those of the developer. | A9 |
| 5. Two stale references | Not required by the contract. | A10 |

## A. Changes to the contract

### A6. Loading of modules (replaces one sentence of design item 1)

- The sentence "No `python -m shade_watch...` command, and no worker process that the tools start, may load a module twice or print a double-import warning" is replaced by:
  - Importing the package `shade_watch` does not import its sub-packages.
  - No `python -m shade_watch...` command prints a double-import warning of the Python runtime (`RuntimeWarning` from `runpy`).
  - How often a module file is executed by a command is the same as at the parent commit `dc7ad08` for the corresponding command. In particular, `python -m shade_watch.engine.v2` and `python -m shade_watch.engine.shade_watch` behave as `python -m src.v2` and `python -m src.shade_watch` did. Changing this is left to C2.0.
- The two blocks

  ```python
  if __name__ in ("__main__", "__mp_main__") and __spec__ is not None:
      sys.modules[__spec__.name] = sys.modules[__name__]
  ```

  in `shade_watch/engine/shade_watch.py` and `shade_watch/engine/v2.py` are removed, with the `import sys` that the candidate added to `v2.py`.
- After the repair, these two files differ from `src/shade_watch.py` and `src/v2.py` at `dc7ad08` only in module names and paths.
- H1-13 reads "without a double-import warning" in the sense of this item.

### A7. The older pipeline entry and layout rule 4

- `shade_watch/engine/pipeline.py` reads the two code files of its identity (`horizon.py`, `spatial.py`) from `shade_watch/engine/`. No other change is made to that statement.
- Layout rule 4 (design item 9) also forbids, in every tracked file to which the rule applies, a quoted string that is exactly `src`, `tools` or `outputs` (single or double quotes). This catches paths that are built from parts. The exclusions of rule 4, including the one of A2, are unchanged.
- `tests/test_layout.py` checks this inside its existing test of rule 4. No test is added or removed.
- New evidence for H1-03 and H1-13: on a small synthetic DSM, the command `python -m shade_watch.engine.shade_watch --config <config> --tile <tile>` completes, and every raster it writes is pixel-identical to the raster that `python -m src.shade_watch` writes with the same inputs at `dc7ad08`. The first acceptance holds such a case (`archive/reviews/h1_0_84dc81fddb3b_20261113/evidence/synthetic/`). No real DSM is used for this.

### A8. Default output root `runs/main`

- The default `output_root` is `runs/main` (design item 3; it was `runs`). Every output root that the project uses is a folder directly under `runs/`, next to the others. `runs/` itself is a container and holds no ownership marker.
- This changes values only:

  | Where | Change |
  | --- | --- |
  | `config/schema/shade_map_machine.schema.json` | default of `output_root`: `runs/main` |
  | `config/machine.example.json` | `output_root`: `runs/main` |
  | User's `config/machine.local.json` | `output_root`: `runs/main`; no other key changes |
  | `web/viewer/request.js`, `web/viewer/results.js` | the default folder shown and used when none is given: `runs/main`. The search of `runs/` and `baselines/` is unchanged |
  | `web/viewer/README.md` | where it names the default folder |

- The rules of `validate_output_root` are not changed.
- The file `runs/.shade_map_root.json`, which the developer's preparation script wrote by hand, is deleted. This is added to the allowed deletions of the write scope. No other file under `runs/` is changed.
- Design item 8 and H1-13: compared with the planner's copy in `archive/baseline_h1_0_20261112/`, the user's machine config differs in the same four keys, with `output_root` equal to `runs/main`.
- New evidence for H1-13: in an empty synthetic runtime, a run with `output_root` `runs/<any name>` followed by a run with the default root both succeed, and no marker is written by hand. The first acceptance holds the failing case (`evidence/synthetic-corrected/`, `evidence/jobs/synthetic-root-reuse.stdout`).

### A9. Region configs of R-2 to R-4

- R-2 to R-4 use copies of `config/regions/measure_lo_wu.json`, `measure_tai_mo_shan.json` and `measure_central.json` in which only `name` is changed. The files in `config/regions/` stay byte-identical.
- In every repair and review run of R-1 to R-6, `name` is new: it has not been used by any earlier run in this checkout. The developer uses the prefix `h1_0_dev2_`, the reviewer `h1_0_rev2_`.
- H1-11 compares, for R-2 to R-6, the frame lists, the date and time folder names, the per-frame counts and every raster. The name of the run folder is not compared.
- R-8 uses the user's machine config as updated by A8.

### A10. Two references

- `web/viewer/README.md` names the view from which `data/cells.json` was generated: view `412eae7951535ccf4f747be461ebcfe64f4e812d67a4d93f558150a718277d5e`, manifest SHA-256 `c915c1061d58f46b1f798585ed7ae88ed1530564ee4935e8548cf7b407178af8`. `data/cells.json` is not regenerated.
- `config/engine/study_area.md` names `config/engine/processing.json` and `legacy/config/mosaic_6tiles.json` where it named `config/processing.json` and `config/mosaic_6tiles.json`. The fields that the engine reads from this file (centre latitude, centre longitude, simulation date) are not touched.

### A11. Names of repair documents

- The repair report is `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md`, with evidence under `docs/packages/H1.0/evidence/repair_1/`. Listings and logs larger than 1 MB go to `archive/reviews/h1_0_dev2_<YYYYMMDD>/`.
- `DEVELOPMENT_REPORT.md`, the existing files under `evidence/`, the first acceptance report and this amendment are records. They are not edited.
- The second acceptance report is `docs/packages/H1.0/ACCEPTANCE_REPORT_<candidate12>.md` for the new candidate.

## B. Repair (developer)

### Starting point

- Branch `feature`. The starting commit is the commit that adds this amendment; its full SHA is in the handoff message. Its first parent chain is: `2442f2e` (first acceptance report), `25c018d` (planner pre-check), `84dc81f` (first candidate), `dc7ad08`, `fda9985`, `cfb6e3c`.
- Before changing anything, record HEAD, the branch, the dirty files and the SHA-256 of this file. Stop and report if the tree is not clean, if the three cache-key hashes differ from the contract, or if the two view pointers in `data/derived/views/` do not name `412eae79…` (Hong Kong) and `11004a24…` (Rotterdam).

### Allowed changes — nothing else

| File | Change |
| --- | --- |
| `shade_watch/engine/shade_watch.py` | Remove the alias block (A6) |
| `shade_watch/engine/v2.py` | Remove the alias block and the added `import sys` (A6) |
| `shade_watch/engine/pipeline.py` | The path of A7, in that one statement |
| `config/schema/shade_map_machine.schema.json`, `config/machine.example.json` | The default of A8 |
| `web/viewer/request.js`, `web/viewer/results.js`, `web/viewer/README.md` | The default folder (A8) and the view named in the README (A10) |
| `config/engine/study_area.md` | The path mentions of A10 |
| `tests/test_layout.py` | The added pattern of A7 |
| A test file | Only if it holds the default output root as a value, and only that value |
| `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md`, `docs/packages/H1.0/evidence/repair_1/**` | New |
| User's `config/machine.local.json` (not tracked) | `output_root` (A8) |
| `runs/.shade_map_root.json` (not tracked) | Deleted (A8) |

- Not changed: the eight view-identity files and the other files of `shade_watch/fill/`, `shade_watch/city/`, the three cache-key files, `fingerprint` and `profile`, every other file of `shade_watch/`, `config/cities/`, `config/sea_profiles/`, `config/regions/`, `config/engine/estimator.json`, `config/engine/processing.json`, `docs/records/`, `legacy/`, `docs/planning/`, `docs/CONVENTIONS.md`, the contract, both amendments, both prompts, the first reports and their evidence.
- The view IDs and the ingestion ID do not change. **The Hong Kong view is not rebuilt and Rotterdam is not registered again.**
- Nothing under `data/`, `baselines/` and `archive/` is changed, apart from new files in `archive/reviews/h1_0_dev2_<YYYYMMDD>/`. The earlier runs and work folders (`runs/h1_0_dev_20261112/`, `runs/h1_0_review_84dc81fddb3b_20261113/`, their folders under `work/`, and `data/cache/horizon/fill_impact_*`) are read-only.

### Checks and runs

- The full test suite. The collected test IDs equal those of `84dc81f` (308).
- The two synthetic cases of A7 and A8, on synthetic fixtures outside the real data. Temporary detached worktrees for them may be created under `archive/reviews/h1_0_dev2_<YYYYMMDD>/`.
- R-1 to R-8 as in the contract, with A9, published under `runs/h1_0_dev2_<YYYYMMDD>/`. Before each of R-1 to R-6, the plan shows zero missing directions; if not, stop and report.
- Budgets: R-1 to R-8 jobs and plans ≤ 90 min in total; memory ≤ 12 GiB; new artifacts ≤ 10 GiB. Metering as in the contract. Budgets may not be extended; if one runs out, the items it affects are NOT VERIFIED.

### Deliverables

- One local commit on the starting commit. Not pushed.
- `DEVELOPMENT_REPORT_REPAIR_1.md`: the list of changed files with the reason for each, the H1-01 to H1-14 matrix for the repaired tree (PASS, FAIL or NOT VERIFIED with evidence; items that the repair cannot affect say so and why), the job ledger and the limits.
- Report the full commit SHA. Do not declare acceptance.

## C. Targeted re-acceptance (reviewer)

### Candidate and places

- `TARGET_COMMIT` is the repair commit; its parent is the commit that adds this amendment. The main checkout's HEAD is `TARGET_COMMIT`, or a descendant that differs from it only in added files and in files under `docs/planning/`.
- Evidence under `archive/reviews/h1_0_<candidate12>_<YYYYMMDD>/`; publications under `runs/h1_0_review_<candidate12>_<YYYYMMDD>/`; the report as in A11, not committed. A detached worktree at `TARGET_COMMIT` under the evidence folder may be used for tests and synthetic cases.
- Read-only: raw data, views, catalogues, every existing cache namespace, baselines, the archive, and every run, work folder and evidence folder of the first round and of the developer.
- No Hong Kong rebuild. No Rotterdam registration. Do not fix a defect. Do not push.
- Budgets: R-1 to R-8 jobs and plans ≤ 90 min in total; memory ≤ 12 GiB; new artifacts ≤ 10 GiB.

### Every item gets a verdict

The second report gives PASS, FAIL or NOT VERIFIED for each of H1-01 to H1-14 for the repaired tree. H1.0 is accepted only if all fourteen pass.

| Item | Work in the re-acceptance |
| --- | --- |
| H1-01 | Two diffs. (1) `git diff 84dc81f TARGET_COMMIT`: apart from the planner's files (`docs/planning/`, the first acceptance report, this amendment, `docs/CONVENTIONS.md`), every change is in the table of part B and is the change named there. (2) `git diff -M dc7ad08 TARGET_COMMIT` for `shade_watch/engine/shade_watch.py`, `v2.py` and `pipeline.py`: only module names and paths differ from the origin. The classification of the first report stands for files that the repair did not touch. |
| H1-02 | The three hashes; the source text of `fingerprint` and `profile`. |
| H1-03 | `tests/test_layout.py`, and the reviewer's own audit of rules 1 to 6 with the added pattern of A7. The synthetic pipeline case of A7. |
| H1-04 | Carried over if `git diff 84dc81f TARGET_COMMIT` is empty for `docs/records/`, `config/engine/estimator.json` and `legacy/`, and the record-manifest test passes. |
| H1-05 | The inventory comparison against the planner baseline is repeated (sizes, modification times, link targets). Content hashes of raw tiles are carried over from the first report. |
| H1-06 | Collected test IDs at `TARGET_COMMIT` equal those at `84dc81f`. The full suite passes. The diff of every test file between `84dc81f` and `TARGET_COMMIT` is read. |
| H1-07 | The three config trees are byte-identical to `dc7ad08`. The schema differs from `dc7ad08` only in the two defaults, with `output_root` now `runs/main`. R-8. The rejection cases are repeated. |
| H1-08, H1-09 | The pointers name the view IDs and the ingestion ID of the first acceptance. The hash comparison of every tile, surface and ingested file against the archived manifests, and the comparison of manifests and pointers, are repeated. The fresh Rotterdam registration of the first acceptance is carried over if `git diff 84dc81f TARGET_COMMIT` is empty for `shade_watch/fill/` and `shade_watch/city/`. |
| H1-10 | Fresh R-1 to R-6 under the reviewer's names: each plans zero missing directions and computes none; R-2 to R-4 use the spatial keys recorded for G1.0. Every cache namespace that exists before the runs is unchanged after them. |
| H1-11 | Fresh R-1 to R-6 compared with the baselines as in the contract and A9; R-7 as in the contract. |
| H1-12 | Listings before and after: the runs write only under `runs/`, `work/`, `data/cache/` (the new fill-impact namespace) and the evidence folder. `outputs/` and `data/processed/` do not exist. `runs/.shade_map_root.json` does not exist. |
| H1-13 | The imports and commands of design item 1, with warnings shown (A6). The two alias blocks are absent. The synthetic pipeline case (A7). The synthetic nested-then-default case (A8). The user's machine config against the planner's copy (A8). The viewer names `runs/main` as its default, holds no old path, and its README names the view of A10. |
| H1-14 | `DEVELOPMENT_REPORT_REPAIR_1.md`: matrix, list of changes, ledger, budgets. The first development report is not edited. |

Report engineering acceptance and numerical consistency separately. Observational accuracy remains NOT VERIFIED for both cities. Any further repair needs a new candidate SHA; the evidence of both rounds is preserved.
