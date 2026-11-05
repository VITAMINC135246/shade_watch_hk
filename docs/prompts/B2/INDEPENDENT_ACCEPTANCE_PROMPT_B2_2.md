# Package B2.2 independent acceptance prompt

Independently assess the `SW-SEA-POLICY-2.2` implementation of `shade_watch_hk` against `docs/prompts/B2/CONTRACT_B2_2.md` (`SW-B2.2`). This is a review, not a second development pass. Re-running the developer's tests is not enough.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA and its parent. The parent is expected to be the B2.2 planning commit, which contains `5744e23` and the contract;
  - the contract's SHA-256, compared with the value given in the handoff message;
  - the accepted V2 SHA `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - the adapter commit `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`;
  - the accepted F1.0 commit `35225fd9547a00e4df202e7ab30204c633b2c845`;
  - the unaccepted B2.0 candidate `5744e2301eea34f8bae05b9df3e14508425b8282`;
  - both environments with their locks: the engine `.venv`, and the tools environment `~/venvs/shade_watch_tools` as the developer recorded it;
  - the identity of every input.
- **Isolation.**
  - Create a Git-managed detached worktree at `outputs/sea2_2_review_<candidate12>_<YYYYMMDD>/worktree` at exactly `TARGET_COMMIT`. `<candidate12>` is the first 12 hex characters of the candidate SHA.
  - The engine and the B2/F tools derive their fixed paths from the repository root. Running from this worktree therefore puts the view, caches, diagnostic folders, F work folders and request-local source views under the review root. Point `dsm_dir` at the main checkout's absolute raw catalogue path.
  - For the raw `run_id` check at `35225fd`, create a second detached worktree under the same review root.
  - Never reset or alter the user's files, and do not prune existing worktrees.
- **Do not change:** production code, the developer's tests, the profile, `docs/OUTPUT_CODES.md`, or the developer's views, outputs and evidence.
- **Write only** under the review root `outputs/sea2_2_review_*`, plus the report file named below. The contract's reading of "writes to existing folders" (section "Write scope and allowed files") applies when you judge the developer's write scope.
- **Read-only:** raw data, historical caches and outputs (including B2.0's), the developer's B2.2 view and outputs, `presentations/` and the sibling projects.
- **Not authorized:** exception zones, profile changes, reclassifying quality 3 or 4, territory shade runs, V3, downloads, push and merge.

## Scope measurement

Use exactly these bases. Do not substitute a narrower allowed list than the contract's.

1. **Candidate's own changes.** `git diff --name-status <parent> <TARGET_COMMIT>`. Every path must be in the contract's allowed-file list (section "Write scope and allowed files"), applied as written.
2. **Engine and adapter.** `git diff <parent> <TARGET_COMMIT> -- src/ tools/region_request.py` is empty. The ten pinned files are byte-identical to `356f611`, and `tools/region_request.py` equals `f5f24ac`.
3. **Package F.** `git diff 35225fd <TARGET_COMMIT> --` over the F paths listed in contract design item 8 contains only the changes listed there.
   - `docs/shade_map/INDEPENDENT_ACCEPTANCE_*.md` are excluded: they come from the user's closeout commit `05c66ab`.
   - Commits between `35225fd` and the parent are user-authorized baseline history: `05c66ab` (closeout), `5744e23` (B2.0 candidate) and the B2.2 planning commit. Their F-path content is judged cumulatively by this rule. Their non-F files are not candidate changes.
4. **Records unchanged.** The following are unchanged between the parent and `TARGET_COMMIT`:
   - `tools/sea_view/`, `docs/sea/` and `tests/test_sea_masks.py`;
   - `docs/sea2/DEVELOPMENT_REPORT.md` and `docs/sea2/evidence/` outside `b2_2/`;
   - `docs/prompts/`, `docs/planning/` and `docs/OUTPUT_CODES.md`.

## Budget and independent cases

- **Ceilings:**
  - 45 minutes of real-DSM job wall time;
  - one view rebuild of at most 60 minutes;
  - 20 minutes for the report-only cross-check;
  - 12 GiB job memory;
  - 30 GiB of new artifacts.

  Measure wall time with a clock that includes system sleep, and run jobs under `caffeinate -dims`. Measure every process that touches real DSM data.
- **Freeze an independent manifest before observing any outcome.** Reading the view's manifest to choose cells is allowed; it is an input. The manifest contains:
  - date `2026-06-21`, with 4 instants: shortly after sunrise, about 10:00, about 13:00 and about 16:30 HKT;
  - your own five-class region: at most 2 cells, different from the developer's region (c), whose targets contain classes 0 to 4 according to the view's per-cell counts, with no `14NE15*` tile within 1 km;
  - random pixel samples, with their seeds;
  - the cells to inspect: at least one on the northern boundary, at least one with a long high shore (seawall or cliff), and `e829250n807800` (`14NE20B`) next to the `14NE15*` block.

## Required independent work

1. **Audit.** Check B2-16 to B2-31 against the code and the evidence, looking for:
   - scope deviations (section above);
   - any build, run or diagnostic path that can read `data/raw/coastline/`;
   - parameters not taken from the profile, or any fill value other than h_fill;
   - manifest build-code hashes that differ from the candidate's files;
   - writes to protected paths. Use the developer's before/after listings and your own.
2. **DSM-only and rebuild** (B2-17, B2-22).
   - The worktree has no copy of `data/raw/coastline/`. Make the main checkout's `data/raw/coastline/` unreadable, confirm with a failing read probe, and record the original modes.
   - Keep it unreadable through the rebuild and all your plans, runs and fill-impact runs. Restore it before step 9, and record the restored modes.
   - Rebuild the view in the worktree. Its `view_id` and every file hash must equal the developer's view in the main checkout (`data/processed/dsm_views/sea_fill_v2_2/<view_id>/`, read-only).
3. **Independent label rule** (B2-18 to B2-20).
   - Write your own implementation of the label rule from the contract text only, with the literal NoData definition.
   - Recompute the classes for the full halo windows of Cheung Chau, Central and your five-class region.
   - For open versus enclosed, either recompute connectivity over the whole domain within the rebuild budget, or flood-fill every sampled component to the domain edge.
   - Compare all pixels with the view's classes. Any difference is a FAIL unless it is an exact distance tie, which the contract leaves undefined; report every tie.
   - For `14NE20B`, report whether its class-3 pixels are enclosed only because of the literal treatment of the `14NE15*` tiles, and whether any such component reaches more than 1 km from those tiles. This follows the contract and is not by itself a defect.
4. **Fill and synthetic tiles.**
   - Check B2-20 on full tiles for every derived tile in the three halos.
   - Check B2-21 for every empty cell in the three halos.
   - `v1.index_sources` must accept request-local views built from the view.
5. **F integration** (B2-23).
   - The full suite passes, run as `pytest tests`.
   - Both raw `run_id` checks pass at `TARGET_COMMIT` and at `35225fd`. Copy the `f1_cheung_chau` config into the review worktree's `config/regions/`, which is outside `outputs/` relative to the worktree root; the original stays untouched.
   - The `publication.py` change is only the surface allowlist.
   - The six-code fixture passes.
   - Published surface layers equal the view's classes on your region.
6. **Runs on your instants** (B2-24 to B2-26).
   - Run F with `raw` and with `sea-2.2` for the Cheung Chau config and the Central 2×2 at your 4 instants. Use fresh names; raw runs use cache namespaces `sea2_2_review_raw_*`.
   - Run `sea-2.2` for your five-class region at your 4 instants. Its raw comparison may come from the fill-impact counterfactual of step 8 instead of a separate raw F run.
   - Apply B2-24 (zero quality 1 and 2) to every `sea-2.2` frame.
   - Apply gates (i) and (ii) of B2-25 to observed land, and explain every sunlit → not-sunlit change.
   - Report the transitions of raw-255 observed land, and the shade distribution on class-3 targets.
7. **Filled-target consistency** (B2-27). At 2 of your instants, independently sample and compare with a direct-ray reference on the view:
   - at least 200 water targets per instant;
   - at least 200 class-3 or class-4 targets per instant;
   - at least 200 observed targets within 50 m of a filled pixel per instant.
8. **Fill-impact** (B2-28).
   - Run `fill-impact` for your five-class region (all 4 frames) and for Cheung Chau (at least 3 frames).
   - Recompute every metric and every dependency raster yourself from the two runs.
   - Confirm that the tool refuses a missing run, a mismatched run, and a time that is not a frame of the run.
   - Confirm that it writes nothing inside the F run folder, and that it resumes.
9. **Tools environment and iB5000 cross-check** (B2-29).
   - Confirm that the tools environment matches the lock: versions, and the wheel hashes as recorded.
   - Use a different method from the developer's (for example, your own rasterization of the same layer). Recompute false water, missed sea by class, and the Victoria Harbour share, for the Cheung Chau and Central halos. Confirm the developer's numbers within 0.5%, or explain the difference.
   - Recompute two components of the class-3 component report.
10. **Documentation** (B2-31). POLICY, GUIDE and DESIGN must:
    - refer to `docs/OUTPUT_CODES.md` without contradicting it;
    - state every required limitation;
    - not claim observational accuracy, a cooling effect, or territory completion.

## Report and release gate

Write a concise report to `docs/sea2/INDEPENDENT_ACCEPTANCE_B2_2_<candidate12>.md`. Do not commit it unless the user asks. The report contains:

- the candidate SHA, its parent and the contract hash;
- environment and input identities;
- the frozen independent manifest;
- a budget ledger;
- one row per criterion, B2-16 to B2-31, marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

`SW-SEA-POLICY-2.2` is ACCEPTED only if all of B2-16 to B2-31 pass. Report engineering acceptance, numerical consistency and agreement with the iB5000 map separately. Observational accuracy remains NOT VERIFIED.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved. Do not proceed to exception zones, territory runs, reclassification of quality 3 or 4, push or merge.
