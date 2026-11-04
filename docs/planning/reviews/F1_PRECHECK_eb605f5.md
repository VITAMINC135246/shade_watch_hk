# Package F1.0 — static pre-check of `eb605f5`

Written by the planning conversation (Claude) on 2026-10-31, about 21:30 HKT. **This is not the independent acceptance.** It only confirms the candidate is fit to hand to an independent reviewer.

## Candidate

- **Commit:** `eb605f52d119a00fa30b8c5d0f44a725f9d88043` on `feature`, parent `d1a89c8`, committed 2026-10-31 21:11 +08:00. Message: "Implement F1.0 shade_map function and CLI".
- **Contract:** `docs/prompts/F1/ACCEPTANCE_CONTRACT.md` (`SW-F1.0`). SHA-256 on disk `dd19ec24…d690`, equal to the frozen value; the file is unchanged since `d1a89c8`.

## Static checks (verified by Claude)

| Check | Result |
| --- | --- |
| `git diff d1a89c8 eb605f5 -- src/ tools/region_request.py` empty | PASS |
| Ten pinned engine files have the same blob ids as `356f611` | PASS |
| `tools/region_request.py` identical to `f5f24ac` | PASS |
| No rasters, VRTs, databases or images committed | PASS |
| Existing test files unchanged; only `tests/test_shade_map.py` and `tests/shade_map_campaign.py` added | PASS |
| Planner and user files (`docs/planning/`, `docs/prompts/{region,runner,sea}/`, `docs/ui/`, `tools/wsl2_smoke/`, `web/console/`, `presentations/`, `.gitignore`, `data/raw/coastline/`) outside the commit | PASS |
| GUIDE names the required limitations (53.0% Quality 2, `14NE15*`, 255 not shade, no cooling, estimates, observational accuracy) | PASS (by text search) |

The commit has 45 files: `tools/shade_map/` (7 modules), six schemas under `config/schema/`, `config/machine.example.json`, `config/regions/cheung_chau.json`, `docs/shade_map/{DESIGN,GUIDE,DEVELOPMENT_REPORT}.md`, evidence (4.8 MB of text/JSON; `protected_before.json` alone is 4.65 MB) and two test files.

## Developer self-assessment (claims, not verified here)

- F1-01 to F1-12 and F1-14: PASS. **F1-13: NOT VERIFIED**: the peak memory of the first read-only planning process was not captured (process enumeration was denied); the plan was repeated with monitoring before any horizon computation. The write-scope audit passed.
- F1-09: 21-tile source view equal to the reference run; 65 frames 07:10–17:50; zero differing shade/quality pixels. Cold cache.
- Tests: `pytest tests` 189 passed; synthetic suite 83 passed.
- Resources: 2,096.7 s of 3,600 s charged; sampled peak tree RSS 5.609 GiB (during a failed validation-harness recursion, preserved in `verification_harness_recursion.json`); sampled artifact peak 0.635 GiB.

## Items for the independent reviewer

1. **F1-13.** Decide on the evidence whether the repeated, monitored plan closes the memory gap. The criterion must not be lowered. If it stays NOT VERIFIED, F1.0 cannot be ACCEPTED under the frozen contract, and the user must decide how to proceed.
2. **Test collection.** Run `pytest tests`; a bare `pytest` also collects historical review checkouts under `outputs/`.
3. **Harness bug.** The recursion bug was in `tests/shade_map_campaign.py`, not in `tools/shade_map/`. Confirm the production code has no similar dispatch path.
4. **Developer outputs** under `outputs/shade_map_f1_20261031/`, `outputs/shade_map_f1_diagnostics_20261031/` and `outputs/shade_map_work/` are read-only for the reviewer.
