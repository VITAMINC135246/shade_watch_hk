# Package G1.0 amendment 1 — `SW-G1.1`

Amends: `SW-G1.0`, `docs/prompts/G1/ACCEPTANCE_CONTRACT.md` (SHA-256 `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef`). That file, the development prompt and the independent-acceptance prompt stay unchanged as records. Where they differ from this amendment, this amendment applies.
Status: frozen on the date of the commit that adds this file, by user decision (2026-11-11; decision D-020).
Candidate it applies to: `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d` (parent `35314377986fcb9551db288a62b74d3b743121ef`), and any later G1.0 candidate.
Item codes are unchanged: `G1-01` to `G1-16`.

This amendment records one scope decision that the user made during development (A1) and corrects three errors of wording or procedure in the frozen texts (A2 to A4). It changes no policy value, no numerical criterion, no budget and no computation scope.

## A1. One existing integration test uses `sea-2.2` and config 1.1 (user decision)

- **Conflict in the contract.** Design item 5 changes the default source of the `shade_map` function to `sea-2.2` and makes the function build a `shade-map-region-1.1` config. The existing test `test_full_publication_api_cli_resume_prune` in `tests/test_shade_map.py` calls that function without a source and compares the run with a `shade-map-region-1.0` raw fixture. It cannot pass unchanged. The contract also said that existing test files may only gain cases and that no existing test may be removed or weakened. Both cannot hold.
- **Decision.** The developer stopped and asked. The user decided on 2026-11-11 that this test uses `sea-2.2` and region config 1.1. From now on, tests and new configs use `sea-2.2` and config 1.1. `raw` stays in the code for two internal purposes only: regression against results accepted before the fill policy, and the fill-impact counterfactual.
- **Amended text.**
  - Allowed-file list, "existing test files, only to add cases": add "and the change of the one function `test_full_publication_api_cli_resume_prune` to `sea-2.2` and config 1.1".
  - G1-04, "none is removed or weakened": add "apart from that one change".
  - Independent-acceptance prompt, scope measurement 4: the same.
- **What the reviewer checks instead.**
  - `git diff <parent> <TARGET_COMMIT> -- tests/` changes no other existing test function.
  - The changed function still checks the Python function, the CLI, resume, the name conflict and prune.
  - Publication with the `raw` source and the 1.0 fixture is still covered by unchanged tests. The planning pre-check found `test_repair_complete_run_discards_orphan_partial`, `test_lock_and_incomplete_prune`, `test_recover_renamed_frame_and_discard_partial` and `test_native_dsm_observed_classes`.
  - The rest of G1-04 is unchanged: a `shade-map-region-1.0` file keeps its present meaning, with default `raw`.

## A2. Test file name

The allowed-file list names `tests/test_city_*.py`. Read it as `tests/test_city*.py`. The candidate's `tests/test_city.py` is an allowed new file.

## A3. G1-14: targets next to filled pixels

- **Fact.** Run NL-1 contains only surface classes 0 and 3. Its canals are enclosed NoData, so no NL-1 pixel carries the water label (class 1 or 2). The frozen wording "pixels next to filled water" cannot be met on NL-1 if "water" means the label.
- **Amended text.** In G1-14, "pixels next to filled water" reads "observed pixels 4-adjacent to a filled pixel (surface class 1 to 4)".
- **Added requirement, so that nothing is lost.** The reviewer's own Rotterdam rectangle must contain class 1 pixels. The reviewer's ray check on that rectangle includes at least 200 observed pixels that are 4-adjacent to a class 1 pixel. The Rotterdam view holds 18,211,404 class 1 pixels according to its manifest.

## A4. Main checkout during independent acceptance

- **Fact.** After the candidate, two kinds of planning commits were added on `feature`, by user decision D-020: the commit `8d7a0d32623d8785d08704fd474892b99338842d`, which adds planning files that had been waiting uncommitted (viewer, guides, measurement configs, earlier planning records), and the commit that adds this amendment. Neither modifies a file of the candidate.
- **Amended text.** In the independent-acceptance prompt, "Confirm that its HEAD is `TARGET_COMMIT`" reads:
  - HEAD of the main checkout is `TARGET_COMMIT` or a descendant of it;
  - `git diff --name-status <TARGET_COMMIT> HEAD` shows only added files, and modifications of `.gitignore`, `docs/prompts/README.md` and files under `docs/planning/`;
  - no tracked file is modified in the working tree.

  If any of these fails, stop and report.
- The review worktree is still created at exactly `TARGET_COMMIT`.
- **G1-01, "the user's untracked files are unchanged".** Most of those files are now tracked by `8d7a0d3`, with identical content. Compare content, not tracking state. `presentations/` and `config/machine.local.json` remain outside Git.

## What does not change

Everything else in `SW-G1.0`: the design, the profiles, the fill height, the twelve files that must stay byte-identical, the write scope on disk, the runs, the budgets, and items G1-01 to G1-16 apart from the readings above. The package is accepted only if every item is PASS.
