# Package F1.0 independent acceptance prompt

Independently assess the `shade_map` implementation of `shade_watch_hk` against `docs/prompts/F1/ACCEPTANCE_CONTRACT.md` (`SW-F1.0`). This is a review, not a second development pass. Re-running the developer's tests is not enough.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA;
  - the contract hash, compared against the frozen value `dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690`;
  - the accepted V2 SHA `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - the adapter commit `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`;
  - the engine environment and its lock file;
  - the identity of every input.
- **Isolation.**
  - Evaluate exactly `TARGET_COMMIT`. If the working tree is dirty, use a managed worktree.
  - Never reset or alter the user's files.
- **Do not change:** production code, the developer's tests, or the developer's outputs.
- **Write only to:**
  - `outputs/shade_map_review_*` (harnesses, reports, review runs and their work folders);
  - cache namespaces `data/processed/shade_v1/shade_map_review_*`;
  - any request-local source views the adapter creates under `outputs/region_views/`.
- **Read-only:** raw data, historical caches and outputs, `presentations/`, the sibling projects.
- **Not authorized:** sea views, territory runs, V3 execution, downloads, push, merge.

## Budget and independent cases

- **Ceilings:** 45 minutes of real-DSM job wall time, 12 GiB job memory, 20 GiB of new artifacts.
- **Freeze an independent manifest before observing any outcome.** It contains:
  - your own non-aligned WGS84 rectangle, of at most 4 cells, in a different area from the developer's (for example Central/Mid-Levels), crossing a cell corner. Confirm with `plan` that it does not need the `14NE15*` tiles.
  - times on `2026-06-21`: an `instants` request with 4 times (shortly after sunrise, about 10:00, about 13:00 and about 16:30 HKT) plus one night time; and a `window` of 3 frames;
  - your own invalid-input cases for corners, time and configuration;
  - random seeds for any sampling.

## Required independent work

1. **Audit.** Check F1-01 to F1-14 against the code and the evidence, looking for:
   - any change under `src/` or to `tools/region_request.py` (diff, plus byte comparison of the ten pinned files against `356f611`);
   - re-implemented engine logic (lattice, partition, solar, classification);
   - writes to protected paths;
   - machine settings leaking into `run_id`;
   - absolute paths in published JSON outside the machine record.
2. **Input rules.** Run your own invalid cases.
   - Each must exit with code 2, print `invalid input` with the right reason, and write nothing (listings before and after).
   - Confirm that valid configs with different machine files give the same `run_id`.
3. **Time.**
   - Confirm that `daylight` frames for 2 dates of your choice equal `plan_shade(dates=...)`.
   - Confirm that your night time is dropped and listed, and that window stepping and the inclusive end behave as specified.
4. **`plan`.** Check its write scope (listings before and after), its schema, its labelled estimates, and the existing-run status in the new, resumable, complete and conflict cases.
5. **Cheung Chau regression (F1-09).**
   - Re-run case (a) yourself under a review name and a cold review cache namespace.
   - Compare all 65 frames, pixel for pixel, with the reference run `outputs/v2_daylight_cheungchau_20261009`, reading the reference through its own result index or logical mosaic.
   - Check the source-view tile list against the reference `source_view/`.
6. **Your rectangle.**
   - Run your manifest.
   - Compute independent V1 custom-bounds references, one per cell window and frame, in a separate review cache namespace.
   - Compare every cell file, every VRT and the full image with the references and with `read_region_window`: full arrays, not samples.
   - Check edge clipping, no-DSM cells (shade 255, quality 1, surface 255) and surface classes derived directly from the DSM.
7. **Layout and portability.** Walk the published trees and check the name and path rules. Copy one run folder to another path and confirm that every VRT opens and reads identical arrays.
8. **Resume and conflicts.**
   - On a fresh name and a fresh cache namespace, kill `run` (SIGKILL) during computation, and again during publication.
   - Re-run, and compare the hashes with an uninterrupted run of the same config.
   - Confirm that completed V2 tasks and published frames are not redone and that no `.partial` folder survives.
   - Confirm that a same-name conflict and a concurrent run are both refused.
9. **Records and summary.**
   - Validate `run_manifest.json`, `frame.json` and the plan JSON against their schemas, and recompute every hash.
   - Recompute the value counts from the rasters and reconcile them with `summary.csv` and `summary.json`; check the whole-class denominators.
10. **`prune`.** Confirm that it refuses on an incomplete run, deletes only the work folder on a complete run, and that a following `run` only verifies.
11. **DSM-source interface.** Confirm that publication code does not branch on the source name, and run the developer's test-only provider test.
12. **Documentation.** `docs/shade_map/GUIDE.md` must state every limitation listed in the contract. It must not claim sea correction, observational accuracy, a cooling effect or territory completion.

## Report and release gate

Write a concise report to `docs/shade_map/INDEPENDENT_ACCEPTANCE_<candidate12>.md`, where `<candidate12>` is the first 12 hex characters of the candidate SHA. Do not commit it unless the user asks. The report contains:

- the candidate SHA and the contract hash;
- environment and input identities;
- the frozen independent manifest;
- a budget ledger;
- one row per criterion, F1-01 to F1-14, marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

F1.0 is ACCEPTED only if all of F1-01 to F1-14 pass. Report engineering acceptance and numerical consistency with the accepted engine separately; observational accuracy remains NOT VERIFIED.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved. Do not proceed to B2.0, sea views, territory runs, push or merge.
