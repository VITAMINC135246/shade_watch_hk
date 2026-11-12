# Package G1.0 development prompt

Implement package G1.0 for `shade_watch_hk`, as defined in `docs/prompts/G1/ACCEPTANCE_CONTRACT.md` (`SW-G1.0`). After this package the `shade_map` function works for a registered city other than Hong Kong. The first city is Rotterdam, from two map sheets that are already on disk.

Three things must hold at the end:

- Hong Kong results are pixel-identical to the accepted results, and Hong Kong horizon cache keys are unchanged.
- The numerical kernel and the fill builder are untouched: four files under `src/` and eight files under `tools/sea2/` stay byte-identical (contract design items 2 and 4).
- Rotterdam runs stay on the EPSG:28992 lattice of its DSM, in Europe/Amsterdam local time, with every NoData pixel filled at 0.00 m NAP.

## Preconditions

- **Branch and baseline.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`, with the repository's `.venv`.
  - The starting commit's full SHA is given in the handoff message. It must contain `docs/prompts/G1/ACCEPTANCE_CONTRACT.md`, and its parent must be `839e200b3bc8b53012bd3fc67627717b1ac44a4c`.
  - Before editing, record:
    - the actual HEAD;
    - the branch;
    - the dirty files;
    - the SHA-256 of `docs/prompts/G1/ACCEPTANCE_CONTRACT.md`, compared with the value given in the handoff message.
- **Stop and report** if any of the following differ:
  - any of the ten engine files, compared with `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - tracked files under `src/`, `tools/`, `config/` or `tests/`, compared with `7707c511a44233d05914604c4741aefb86701d7a`;
  - the twelve file hashes listed in the contract;
  - the size or SHA-256 of either Rotterdam sheet in `data/raw/dsm/rotterdam_ahn4_dsm05/`;
  - the Hong Kong view named by `data/processed/dsm_views/sea_fill_v2_2/current-hk_cedd_2020.json` (expected `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1`).
- **Read first (do not edit):**
  - the whole contract;
  - `docs/OUTPUT_CODES.md`;
  - `docs/planning/DECISIONS.zh-TW.md` (D-016, D-018, D-019);
  - `src/v1.py`, `src/solar.py`, `src/v2.py`, `src/v2_worker.py`, and how `src/v1_cache.py` and `src/spatial.py` build the cache identity and read windows;
  - `tools/shade_map/` (all files), `tools/region_request.py`;
  - `tools/sea2/build.py`, `catalogue.py`, `profile.py`, `provider.py`, `view.py` and `fill_impact.py`;
  - `docs/shade_map/{GUIDE,DESIGN}.md`, `docs/sea2/{POLICY,GUIDE,DESIGN}.md`.
- **Leave untouched:**
  - everything under `data/raw/`;
  - every existing folder under `data/processed/` and `outputs/`, including the Hong Kong view, every existing cache namespace and every published run;
  - `docs/prompts/`, `docs/planning/`, every acceptance report, `presentations/` and `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - the user's uncommitted files: the `.gitignore` change, `web/`, `docs/GUIDE.md`, `docs/GUIDE.zh-TW.md`, `config/regions/measure_*.json`, `config/machine.local.json`, `docs/prompts/{region,runner,sea}/`, `docs/ui/`, `docs/v3/WSL2_SMOKE_TEST.md`, `tools/wsl2_smoke/` and `data/raw/coastline/`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Never stage or commit** a file outside the contract's allowed-file list.
- **Not authorized:**
  - edits to `src/horizon.py`, `src/spatial.py`, `src/v1_cache.py`, `src/shade_watch.py`, or to the eight `tools/sea2/` build files;
  - a resolution other than 0.5 m, a fill height other than 0.00 m, or any change to the kernel, the classification, the search distance or the label rule;
  - rebuilding or changing the Hong Kong view, or adding files to an existing cache namespace;
  - real-DSM computation outside the contract's list (HK-1 to HK-4, NL-0 to NL-5, direct-ray checks);
  - downloads, V3, `config/v3/`, web work, WK4 material, push or PR.

## Facts that shape the implementation

These come from the planning pre-check. Verify them as you go.

- `tools/sea2/provider.py` and `tools/sea2/build.py` take the catalogue from the machine's `dsm_dir` and the profile from the machine's `sea_profile`. They may not change. For a city other than Hong Kong, give them a machine dictionary whose `dsm_dir` is the ingested catalogue and whose `sea_profile` is the city's profile.
- The view pointer stores the size and modification time of every catalogue file. If ingested tiles are rewritten, the view becomes stale. A repeat registration must therefore leave existing files untouched.
- The builder writes the Rotterdam view into `data/processed/dsm_views/sea_fill_v2_2/`, next to the Hong Kong view. That is allowed. Nothing belonging to the Hong Kong view may change.
- The horizon cache key depends on `src/horizon.py`, `src/spatial.py`, `src/v1_cache.py` and the source tiles only. Changing `src/v1.py` or `src/solar.py` changes run IDs and plan keys, not cache keys.
- `tools/region_request.py` calls `v1.plan_shade` without a time zone or a daylight reference. It must pass the city's values. `tools/sea2/fill_impact.py` plans its raw counterfactual through the same adapter from the machine's `dsm_dir`.
- Package F labels Hong Kong frames with a fixed UTC+8 offset. That behaviour must be reproduced exactly for `hong_kong`.
- `solar.daylight_samples` aligns frames to the wall clock of the time zone it is given. With Europe/Amsterdam it gives the frame counts stated in the contract.
- `.DS_Store` files exist in the raw folders. Hidden files are not sheets.

## Implementation sequence

1. **Plan.** Map G1-01 to G1-16 to tests and evidence. Start `docs/city/DESIGN.md`.
2. **Protected listings.** Before any run, take a listing of `data/raw/`, `data/processed/` and `outputs/` (path, type, size, modification time) and the hashes of the user's untracked files. Keep it as evidence.
3. **Engine inputs.** Make the CRS, the time zone, the daylight reference and the DSM source line inputs of the six engine files that may change. Keep every default. Run the existing tests.
4. **Hong Kong regression first.** Run HK-1 before building anything else on top, and compare it with its reference. A single differing pixel means stop and find the cause.
5. **City profiles and machine config.** Add the schema, the two profiles and the optional `cities` key.
6. **Ingestion** (`python -m tools.city register`): source check, profile check, lossless cells, guard, manifest, pointer, registration report with warnings, repeat behaviour. Test with small synthetic sheets, including a sheet with a NoData value that is not −9999, a sheet with a non-finite pixel, and a valid pixel equal to −9999.
7. **Fill view.** Add `config/sea_profiles/nl_rotterdam_dsm05.json` exactly as in the contract and call the unchanged builder from registration.
8. **Package F.** Region config 1.1, city selection, the `projected` corner type, projection record, time in the city's zone, the `city` block and publication format 1.1, `fill_context` in the plan, sources per city, the raw cache namespace rule.
9. **Adapter and fill-impact,** within design item 6.
10. **Real work,** within the contract's scope and budgets, with new names and namespaces:
    - keep a development machine config and every region config under `docs/city/evidence/configs/`. The machine config uses `output_root` `outputs/shade_map_g1_dev_<YYYYMMDD>`, a raw `cache_namespace` that starts with `g1_dev_raw_`, and `cities.rotterdam.raw_dir` `data/raw/dsm/rotterdam_ahn4_dsm05`. Do not edit `config/machine.local.json`;
    - HK-2, HK-3 and HK-4. Confirm before each run that the plan shows zero missing directions. If it does not, stop and report;
    - NL-0 once;
    - NL-1, NL-2, NL-3, NL-4 and NL-5;
    - direct-ray checks on NL-1.
11. **Documentation:** `docs/city/GUIDE.md`, `DESIGN.md` and `DEVELOPMENT_REPORT.md`, the additions to `docs/shade_map/GUIDE.md` and `DESIGN.md`, and additions to `docs/OUTPUT_CODES.md` only if a new field needs a definition. Include every limitation statement of design item 8.

## Resources and monitoring

- **Measure every process** that touches real DSM data, including read-only plans and tests on real data. Record wall time, peak RSS and new-artifact bytes. Keep the ledger in `docs/city/evidence/resources.jsonl`.
- **Use a wall clock that includes system sleep.** Keep the Mac awake during jobs, for example by running them under `caffeinate -dims`. Stop a job when its budget runs out.
- **Budgets:**
  - real-DSM shade jobs ≤ 90 min;
  - Rotterdam registration ≤ 20 min, including stopped attempts;
  - job memory ≤ 12 GiB;
  - new artifacts ≤ 20 GiB.

  When a budget runs out, mark the affected criteria NOT VERIFIED; do not extend it.
- **Harness hygiene.** Any temporary launcher must be safe under multiprocessing spawn (guard its entry point). If a helper is part of the evidence, include its source under `docs/city/evidence/`.

## Testing

- Unit tests use tiny synthetic catalogues and sheets.
- Run the full suite with `.venv/bin/python -m pytest tests` before committing. Every test that exists at the starting commit must pass, and none may be removed or weakened.

## Deliverables

- Code, tests, schemas, profiles and documents within the contract's allowed-file list.
- The G1-01 to G1-16 matrix in `docs/city/DEVELOPMENT_REPORT.md`: PASS, FAIL or NOT VERIFIED for each, with evidence paths under `docs/city/evidence/`.
  - Evidence is text and JSON only: no rasters, catalogues, views or caches. Keep listings compact: hashes and counts, not full dumps.
  - Mark the reviewer-only parts NOT VERIFIED: the fresh registration in another worktree (G1-08) and the independent recomputations.
- The resource ledger and the protected listings before and after.
- One local commit containing only allowed files. Inspect the staged diff before committing.

Report the full commit SHA, the `ingest_id` and the Rotterdam `view_id`. Do not push, and do not declare acceptance; hand off for independent acceptance.
