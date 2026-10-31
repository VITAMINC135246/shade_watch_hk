# Package B2.0 independent acceptance prompt

Independently assess the `SW-SEA-POLICY-2.0` implementation of `shade_watch_hk` against `docs/prompts/B2/ACCEPTANCE_CONTRACT.md` (`SW-B2.0`). This is a review, not a second development pass. Re-running the developer's tests is not enough.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA;
  - the contract hash, compared against the frozen value `b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`;
  - the accepted V2 SHA `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - the adapter commit `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`;
  - the accepted F1.0 commit (decision D-012);
  - both environments with their locks;
  - the identity of every input.
- **Isolation.** Evaluate exactly `TARGET_COMMIT`. If the working tree is dirty, use a managed worktree. Never reset or alter the user's files.
- **Do not change:** production code, the developer's tests, the profile, or the developer's views and outputs.
- **Write only to:**
  - `outputs/sea2_review_*`;
  - `data/processed/dsm_views/sea_fill_v2_review/`;
  - cache namespaces `data/processed/shade_v1/sea2_review_*`;
  - any request-local source views the adapter creates under `outputs/region_views/`.
- **Read-only:** raw data, historical caches and outputs, `presentations/`, the sibling projects.
- **Not authorized:** exception zones, void filling as a result, territory shade runs, V3, downloads, push, merge.

## Budget and independent cases

- **Ceilings:**
  - 45 minutes of real-DSM job wall time, plus one view rebuild of at most 60 minutes;
  - 12 GiB job memory;
  - 30 GiB of new artifacts.
- **Freeze an independent manifest before observing any outcome.** It contains:
  - date `2026-06-21`, with 4 instants: shortly after sunrise, about 10:00, about 13:00 and about 16:30 HKT;
  - random pixel samples, with their seeds;
  - the cells to inspect, including at least one cell on the northern boundary and one with a long high shore (seawall or cliff).

## Required independent work

1. **Audit.** Check B2-01 to B2-15 against the code and the evidence, looking for:
   - any change under `src/` or to `tools/region_request.py` (diff, plus byte comparison of the ten pinned files);
   - F changes beyond the contract's design item 7;
   - any build or run path that can read `data/raw/coastline/`;
   - parameters not taken from the profile;
   - writes to protected paths.
2. **DSM-only.** With `data/raw/coastline/` unreadable, rebuild the view into the review namespace. Its `view_id` and file hashes must equal the developer's. Restore the permissions afterwards.
3. **Independent rule implementation.**
   - Write your own implementation of the classification rule, from the contract text only.
   - Recompute the classes for the full Cheung Chau and Central halo windows.
   - For the open/enclosed test, either recompute connectivity over the whole domain within the rebuild budget, or flood-fill every sampled component to the domain edge.
   - Compare all pixels with the view's surface classes. Any difference is a FAIL unless it is an exact distance tie that the contract leaves undefined; report every tie.
4. **Fill and synthetic tiles.**
   - Check B2-05 on full tiles for every derived tile in both halos.
   - Check B2-06 for every empty cell in both halos.
   - `v1.index_sources` must accept request-local views built from the sea view.
5. **F integration.**
   - The F test suite passes, run as `pytest tests`.
   - The raw Cheung Chau `run_id` is unchanged.
   - Published surface layers equal the view's classes.
6. **Land regression on your instants.**
   - Run F with `raw` and with `sea-2.0` for the Cheung Chau config and the Central 2×2 at your 4 instants, using fresh names and review cache namespaces.
   - Apply gates (i) to (iii) of B2-09 to land. Explain every sunlit → not-sunlit change.
   - Report the transitions of former Quality 2 land pixels.
7. **Sea-target consistency.** At 2 of your instants, sample at least 200 water pixels per instant independently, and compare them with a direct-ray reference.
8. **Void-impact.**
   - Run `void-impact` for one of your Cheung Chau runs, covering at least 3 frames.
   - Recompute every metric from the rasters yourself.
   - Confirm that the counterfactual view differs from the sea view only at class-255 pixels, and that the tool refuses a missing or mismatched sea-2.0 run.
9. **iB5000 cross-check.** With a different reader or method from the developer's, recompute the false-water and missed-sea figures for the Cheung Chau halo. Confirm the developer's numbers within 0.5%, or explain the difference.
10. **Documentation.** POLICY and GUIDE must state every required limitation and must not claim observational accuracy, a cooling effect, or territory completion.

## Report and release gate

Write a concise report to `docs/sea2/INDEPENDENT_ACCEPTANCE_<candidate12>.md`, where `<candidate12>` is the first 12 hex characters of the candidate SHA. Do not commit it unless the user asks. The report contains:

- the candidate SHA and the contract hash;
- environment and input identities;
- the frozen independent manifest;
- a budget ledger;
- one row per criterion, B2-01 to B2-15, marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

`SW-SEA-POLICY-2.0` is ACCEPTED only if all of B2-01 to B2-15 pass. Report engineering acceptance, numerical consistency and agreement with the iB5000 map separately; observational accuracy remains NOT VERIFIED.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved. Do not proceed to exception zones, void filling, territory runs, push or merge.
