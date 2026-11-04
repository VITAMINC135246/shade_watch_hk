# Package F1.0 repair 1 — static pre-check of `35225fd`

Written by the planning conversation (Claude) on 2026-11-04, about 15:45 HKT. **This is not the independent re-acceptance.**

## Candidate

- **Commit:** `35225fd9547a00e4df202e7ab30204c633b2c845`, parent `439e064`, committed 2026-11-04 15:29 +08:00. Message: "Fix shade_map output boundaries and complete-run recovery".
- **Previous candidate:** `eb605f5`, NOT ACCEPTED (`docs/shade_map/INDEPENDENT_ACCEPTANCE_eb605f52d119.md`: D1 output-root guard, D2 stale `.partial`; F1-13 memory gap).
- **Contract:** `SW-F1.0`, SHA-256 `dd19ec24…d690`, unchanged.

## Static checks (verified by Claude)

| Check | Result |
| --- | --- |
| `git diff 439e064 35225fd -- src/ tools/region_request.py docs/prompts/` empty; ten pinned files equal `356f611` | PASS |
| Production changes only in `tools/shade_map/{config,planning,runner}.py` | PASS |
| `tests/test_shade_map.py`: 66 lines added, 0 removed; new `tests/shade_map_repair_campaign.py` | PASS |
| Original evidence under `docs/shade_map/evidence/` (outside `repair_1/`) unchanged | PASS |
| Review report and `outputs/shade_map_review_eb605f52d119_20261031/` untouched (times 2026-10-31) and not committed | PASS |
| No rasters, VRTs, databases or images committed | PASS |

## What the fixes do (from reading the diff)

- **D1.** The new `validate_output_root` runs before any write in both `prepare` and `run_region`. It resolves the path and rejects an output root:
  - inside `data/`;
  - inside the catalogue, a provider source directory, the backing directories of catalogue files, or `outputs/region_views`;
  - under any existing ancestor that is neither the repository root, `outputs/`, nor an F-created root (marker `.shade_map_root.json`).

  The ancestor walk now continues outside the repository.
- **D2.**
  - `verify_run` refuses while any `*.partial` folder exists.
  - The new `_recover_partials` removes every `<date>/<HHMM>.partial`, including when the manifest is complete, and re-marks a frame pending if its final folder fails verification.

**Behaviour note (consistent with the contract, not a defect).** Because every existing ancestor must be the repository, `outputs/` or an F-created root, an `output_root` on another disk or elsewhere outside the repository is now always rejected. Publishing outside the repository would need an F1.1 amendment.

## Developer self-assessment (claims, not verified here)

- F1-01 to F1-14 all PASS. F1-13 rests on the repair phase's complete monitoring; the historical gap is kept on record.
- `pytest tests`: 222 passed.
- Campaign (a), (b), (c) re-run; all 1,035 published rasters hash-identical to the original development run.
- Repair ledger: 1,435.2 s (23.92 min), giving 3,531.9 s (58.87 min) cumulative against the 60-min development ceiling. Measured peak RSS 0.894 GiB; peak new artifacts 0.67 GiB. `complete_monitoring: true`.

## Items for the independent reviewer

1. Re-test D1 with the original reproductions and new cases (symlinks, external parents), and D2 with an orphan `.partial` folder beside a complete run.
2. F1-13: decide whether the repair candidate's complete ledger satisfies the criterion. The criterion must not be lowered.
3. Regression after the runner change: F1-07, F1-08 and F1-11 on a small run. F1-09 by hash comparison or a cold re-run, as the budget allows.
4. Budget: the first review charged 1,398.6 s of 2,700 s; about 21.7 minutes remain for targeted re-acceptance.

## Outcome (added 2026-11-04)

- The targeted re-acceptance (`docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md`) found 13 PASS and 1 FAIL. The FAIL was on F1-01 and was caused by an error in the planning conversation's review instructions: a wrong diff base, and an allowed-path list that was too narrow.
- Addendum 1 (`docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a_ADDENDUM_1.md`) re-evaluated F1-01 under corrected instructions and found it PASS. The final result is **ACCEPTED**, 14/14 PASS.
