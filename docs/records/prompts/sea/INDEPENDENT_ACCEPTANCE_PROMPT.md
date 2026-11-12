# Sea-surface support independent acceptance prompt

Independently assess the `SW-SEA-POLICY-1.0` implementation of `shade_watch_hk` against `docs/prompts/sea/ACCEPTANCE_CONTRACT.md` (`SW-SEA-AC-1.0`). This is a review, not a second development pass. Re-running the developer's tests is not enough.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA;
  - the contract hash, compared against the frozen hash in the decision record;
  - the accepted V2 SHA `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - the engine and tools environments, with their lock files;
  - the identity of every input.
- **Isolation.** Evaluate exactly `TARGET_COMMIT`. If the working tree is dirty, use a managed worktree. Never reset or alter the user's files.
- **Do not change:** production code, the developer's tests, policy values or existing views.
- **Write only to:** `outputs/sea_review_*` and `data/processed/dsm_views/sea_fill_v1_review/`. This covers your harnesses, reports and any independently rebuilt views.
- **Read-only:** raw data, historical caches and outputs, `presentations/`, sibling projects.
- **Not authorized:** a territory view, V3 execution, downloads, push, merge.

## Budget and independent cases

- **Ceilings:** 45 minutes real-DSM job wall time, 12 GiB job memory, 20 GiB new artifacts.
- **Freeze an independent manifest before observing any outcome.** It contains:
  - a different date, `2026-06-21`, with 4 instants: shortly after sunrise, about 10:00, about 13:00 and about 16:30 HKT;
  - random pixel samples with their seeds;
  - the tiles to inspect.
- **Developer views.** Use the developer's Cheung Chau and Central views only after your own rebuild has reproduced them.

## Required independent work

1. **Audit.** Check S01–S14 against the code and evidence, looking for:
   - mutable or unrecorded inputs;
   - writes to protected paths;
   - any change under `src/`, checked by diff and by byte comparison of the ten pinned files against `356f611`;
   - places where a pixel could be filled without meeting all three conditions of policy item 2.
2. **Map extraction cross-check.** Re-read the FGDB with a method different from the developer's — another library or reader, or GDAL `ogrinfo` output. Confirm the S02 counts, the CRS, and that the derived vector hash matches the manifest.
3. **Rasterization and fill.**
   - Classify at least 20,000 random pixel centres in views (a) and (b) yourself, stratified to include coastline pixels. Use point-in-polygon against `SEF` and `LAF`, plus the raw DSM value. Compare your result with the view tiles and surface rasters. Any wrongly filled or wrongly unfilled pixel is a FAIL, unless it is a documented exact-boundary tie.
   - Verify S04 bit-identity of non-sea pixels on full tiles.
   - Rebuild one view from scratch; `view_id` and hashes must reproduce.
4. **Synthetic tiles.** Check lattice alignment, sizes, absence of overlap and halo coverage (S05). `v1.index_sources` must accept the view without ambiguous-overlap errors.
5. **Fill-elevation check.** Recompute the S06 statistic on a random 20% sample of coastal tiles. Its p50 must agree with the developer's within 0.05 m. Report the full distribution.
6. **Land regression on your own instants.**
   - Run V2 on both the raw catalogue and view (a) at your 4 instants, using isolated cache namespaces.
   - Apply S08 gates (i)–(iii) to land pixels (surface class 0).
   - Explain every sunlit → non-sunlit change, using per-tile `threshold_deg` evidence or a demonstrated blocker.
   - Report how former Quality 2 pixels transitioned.
7. **Sea-target consistency (S09).** At 2 of your instants, sample at least 200 sea-fill pixels per instant independently. Compare the engine's labels with the direct-ray reference.
8. **Urban guard.**
   - On view (b), DSM NoData inside `LAF` must be unchanged, and Victoria Harbour pixels must equal h exactly.
   - Run 2 of your independent instants and apply S08 gates (i)–(ii).
9. **Helpers and provenance.**
   - Test `read_surface_window` on an odd-offset crop that crosses tiles.
   - Test `effective_policy` on a result index from a view run and on one from a raw run. The raw case must report that no sea policy applies.
10. **Documentation.** `docs/sea/POLICY.md` and `docs/sea/GUIDE.md` must state every limitation listed in the contract and must not claim accuracy, a cooling effect or territory completion.

## Report and release gate

Write a concise report containing:

- candidate SHA and contract hash;
- environment and input identities;
- the frozen independent manifest;
- a budget ledger;
- one row per criterion S01–S14 marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

`SW-SEA-POLICY-1.0` is ACCEPTED only if all of S01–S14 pass. Report engineering acceptance, numerical consistency and observational accuracy separately; observational accuracy remains NOT VERIFIED.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved. Do not proceed to V3, territory builds, push or merge.
