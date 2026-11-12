# Package G1.0 independent acceptance prompt

Independently assess the G1.0 implementation of `shade_watch_hk` against `docs/prompts/G1/ACCEPTANCE_CONTRACT.md` (`SW-G1.0`). This is a review, not a second development pass. Re-running the developer's tests is not enough.

## Pin the candidate

- **Project:** `/Volumes/My Passport for Mac/Projects/shade_watch_hk`, with the repository's `.venv`.
- **Identities to record.** Resolve the supplied `TARGET_COMMIT` to a full SHA, then record:
  - the candidate SHA and its parent. The parent is expected to be the G1.0 planning commit, whose own parent is `839e200b3bc8b53012bd3fc67627717b1ac44a4c`;
  - the contract's SHA-256, compared with the value given in the handoff message;
  - the accepted V2 SHA `356f611d7b775ce31006904b80ca31d3c1c484b2`, the accepted F1.0 commit `35225fd9547a00e4df202e7ab30204c633b2c845` and the accepted B2.2 commit `7707c511a44233d05914604c4741aefb86701d7a`;
  - the environment and its lock;
  - the identity of every input: the two Rotterdam sheets, the Hong Kong view pointer, and the four regression references.
- **Two places to work.**
  - **Main checkout,** for the Hong Kong regression only. The Hong Kong view and its horizon caches exist only there. Confirm that its HEAD is `TARGET_COMMIT` and that no tracked file is modified apart from `.gitignore`. If not, stop and report.
  - **Review worktree,** for everything about Rotterdam. Create a Git-managed detached worktree at `outputs/shade_map_g1_review_<candidate12>_<YYYYMMDD>/worktree` at exactly `TARGET_COMMIT`. The tools derive their fixed paths from the repository root, so a registration and runs started from this worktree put the catalogue, the view, the caches and the work folders under the review root. Point `cities.rotterdam.raw_dir` and `dsm_dir` at the main checkout's absolute raw paths.
  - Never reset or alter the user's files, and do not prune existing worktrees.
- **Do not change:** production code, the developer's tests, the profiles, `docs/OUTPUT_CODES.md`, or the developer's catalogue, view, outputs and evidence.
- **Write only:**
  - under the review root `outputs/shade_map_g1_review_<candidate12>_<YYYYMMDD>/`;
  - for the Hong Kong regression in the main checkout: new entries for your run names in the fixed containers named in the contract, and one new raw cache namespace `data/processed/shade_v1/g1_review_raw_<candidate12>`;
  - the report file named below.
- **Read-only:** raw data, the Hong Kong view, every existing cache namespace, every existing output, the developer's Rotterdam catalogue, view and outputs, `presentations/` and the sibling projects.
- **Not authorized:** changing a fill height or a profile, rebuilding the Hong Kong view, a resolution other than 0.5 m, territory runs, V3, downloads, push and merge.

## Scope measurement

Use exactly these bases. Do not substitute a narrower allowed list than the contract's.

1. **Candidate's own changes.** `git diff --name-status <parent> <TARGET_COMMIT>`. Every path must be in the contract's allowed-file list (section "Write scope and allowed files"), applied as written.
2. **Untouched files.** The four engine files and the eight `tools/sea2/` files have the SHA-256 values listed in the contract. `git diff <parent> <TARGET_COMMIT>` is empty for them, for `docs/prompts/`, for `docs/planning/`, for `config/sea_profiles/hk_cedd_2020.json`, for `config/schema/sea_profile.schema.json` and for `config/regions/cheung_chau.json`.
3. **Limited files.** Read the full diff of `tools/region_request.py` and `tools/sea2/fill_impact.py` and judge it against design item 6. Read the full diff of the six engine files and judge it against design item 2: inputs instead of constants, defaults kept, no change of rule.
4. **Existing tests.** No test that exists at the parent is removed or weakened.
5. **Writes on disk.** Compare the developer's before and after listings, and the planner's baseline given in the handoff message, with the present state. Every new entry must lie in a location the contract allows. No existing unit may have changed.

## Budget and independent cases

- **Ceilings:**
  - 75 minutes of real-DSM shade jobs;
  - 30 minutes for one fresh Rotterdam registration and one repeat;
  - 12 GiB job memory;
  - 20 GiB of new artifacts.

  Measure wall time with a clock that includes system sleep, and run jobs under `caffeinate -dims`. Measure every process that touches real DSM data.
- **Freeze an independent manifest before observing any outcome.** Reading the developer's manifests to choose cells is allowed; they are inputs. The manifest contains:
  - your own Rotterdam rectangle of at most four cells, different from NL-1 and NL-2, that contains water and land below 0 m according to the registration report or the view's per-cell counts, with at most twelve instants on a date of your choice that is not 2026-06-21 or 2026-12-22;
  - the random pixel samples for the ray check, with their seeds;
  - the cells and frames you will inspect.

## Required independent work

1. **Audit.** Check G1-01 to G1-16 against the code and the evidence, looking for:
   - scope deviations (section above);
   - a Hong Kong constant that still applies to another city: CRS, time zone, daylight reference, `+08:00`, the source line;
   - a default that changed under `src/`;
   - any path by which a Rotterdam run could read or write Hong Kong data, or the reverse;
   - any fill value other than float32 0.0;
   - network access.
2. **Hong Kong regression** (G1-02, G1-03, G1-04), in the main checkout.
   - Take a listing of every existing cache namespace before the runs.
   - Run HK-1 to HK-4 under your own names. Before each of HK-2 to HK-4, confirm that the plan shows zero missing directions.
   - Compare every raster with its reference with your own script. Compare frame lists, folder names and per-frame counts.
   - Confirm after the runs that no existing cache namespace gained or changed a file.
   - Plan `config/regions/cheung_chau.json`, a copy of a `shade-map-region-1.0` file without `dsm_source`, and a region with the user's `config/machine.local.json`. Run `pytest tests`.
3. **Ingestion** (G1-07, G1-09). Register Rotterdam afresh in the review worktree.
   - Write your own reader for the comparison. It must not import `tools/city`. Compare all 250,000,000 pixels of the raw sheets with the ingested cells.
   - Recompute the registration report's numbers from the raw sheets.
   - With copies of small synthetic sheets, confirm that registration refuses a changed sheet, a missing sheet, an extra sheet, and a profile whose extent or daylight reference is wrong.
   - Confirm that the raw sheets' hashes are unchanged.
4. **Reproducibility** (G1-08). The `ingest_id`, the `view_id` and every file hash of your fresh registration equal the developer's in the main checkout. Then register once more in the worktree and confirm that no existing file changed.
5. **Fill view** (G1-10). With your own script, over the whole domain: fill values, unchanged bits, the class totals of the contract, and the class of the ring. Confirm that the Hong Kong pointer and view in the main checkout are unchanged.
6. **Rotterdam runs** (G1-11, G1-12, G1-13, G1-15), in the review worktree.
   - Run NL-1 to NL-5 and your own rectangle. Start NL-2 through the Python function, with `city="rotterdam"` and no `dsm_source`.
   - Check raster headers, VRTs, manifests, the `city` block, code histograms and the quality 1 and 2 counts.
   - Project the NL-2 corners yourself and compare the snapped rectangle.
   - Compute sunrise and sunset for 51.92° N, 4.48° E with a method of your own, not `src/solar.py`, and derive the expected frame lists for 2026-06-21 and 2026-12-22. Check the offsets on the four clock-change dates.
   - Search every file written for Rotterdam for the Hong Kong source line, `HKT` and `Asia/Hong_Kong`.
   - Try the rejections: an unknown city, a rectangle outside the extent, `projected` without a city, `hk1980` with `rotterdam`, corners in the wrong order, an offset that disagrees with the city, 2026-03-29 02:30 local.
7. **Independent rays** (G1-14). Write your own direct-ray implementation from `docs/v1/POLICY.md` and the contract. Apply it to the filled view for the frozen sample of NL-1 and for your own rectangle. Report every disagreement with its cause.
8. **Fill impact** (G1-15). Recompute the dependence counts of NL-4 yourself from the filled run and a raw run. Confirm that the tool writes nothing inside the NL-1 run folder.
9. **Documentation** (G1-16). Follow the guide from a clean worktree. Check every limitation statement of design item 8. The documents must not claim observational accuracy, verified labels, a correct fill height for Rotterdam, or a cooling effect.

## Report and release gate

Write a concise report to `docs/city/INDEPENDENT_ACCEPTANCE_G1_0_<candidate12>.md` in the main checkout. Do not commit it unless the user asks. The report contains:

- the candidate SHA, its parent and the contract hash;
- environment and input identities;
- the frozen independent manifest;
- a budget ledger;
- one row per criterion, G1-01 to G1-16, marked PASS, FAIL or NOT VERIFIED, each with reproducible evidence paths and commands;
- defects, each with severity, expected versus actual behaviour, a minimal reproduction and the affected paths.

Do not fix any defect.

G1.0 is ACCEPTED only if all of G1-01 to G1-16 pass. Report engineering acceptance and numerical consistency separately. Observational accuracy remains NOT VERIFIED for both cities, and Rotterdam's surface labels remain not verified.

Any repair needs a new candidate SHA and targeted re-acceptance, and the original failure evidence must be preserved. Do not proceed to another city, another fill height, Windows support, push or merge.
