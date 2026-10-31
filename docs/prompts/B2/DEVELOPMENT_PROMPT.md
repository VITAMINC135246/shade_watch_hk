# Package B2.0 development prompt

Implement the DSM-only sea surface `SW-SEA-POLICY-2.0` for `shade_watch_hk`, as defined in `docs/prompts/B2/ACCEPTANCE_CONTRACT.md` (`SW-B2.0`). The engine and the region adapter stay unchanged. Package F1.0 gains a `sea-2.0` source only through the changes listed in the contract's design item 7.

## Preconditions

- **Branch and baseline.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`.
  - The starting commit's full SHA is given in the handoff message. It must contain both `docs/prompts/B2/` and the independently accepted F1.0 commit recorded in decision D-012.
  - Before editing, record the actual HEAD, the branch, the dirty files and the contract's SHA-256, and compare the hash with the frozen value `b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`.
- **Stop and report** if any of the following differ:
  - any of the ten pinned engine files, compared with `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - `tools/region_request.py`, compared with `f5f24ac`;
  - F1.0's code, compared with its accepted commit.
- **Read first (do not edit):**
  - the whole contract;
  - `docs/shade_map/{GUIDE,DESIGN}.md` and `tools/shade_map/` (especially `sources.py`);
  - `docs/region/GUIDE.md`;
  - `docs/sea/{POLICY,DESIGN,GUIDE}.md` and `tools/sea_view/` (B1.0: reusable, not accepted);
  - `docs/v1/POLICY.md`;
  - `src/shade_watch.py::classify`, the support and threshold code in `src/v1.py`, and `src/horizon.py` (`direct_ray_reference`, `diagnostic_horizon`);
  - `data/raw/coastline/README.md` (for validation only).
- **Leave untouched:**
  - everything under `data/raw/` (`data/raw/coastline/` is read only by the validation script, in the tools environment);
  - every existing namespace under `data/processed/`;
  - all existing `outputs/` folders, including the F1.0 development and review outputs;
  - `presentations/`, `docs/planning/` and `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - the uncommitted planner files: the `.gitignore` change, `docs/prompts/{region,runner,sea}/`, `docs/ui/`, `docs/v3/WSL2_SMOKE_TEST.md`, `tools/wsl2_smoke/` and `web/console/`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Never stage or commit** a file you did not create or were not allowed to change for this task.
- **Not authorized:**
  - edits under `src/`, to `tools/region_request.py`, or to F code beyond the contract's design item 7;
  - exception zones;
  - void filling as a result;
  - territory shade runs;
  - the four-region solstice measurement;
  - downloads, V3, `config/v3/`, web work, push or PR.

## Implementation sequence

1. **Plan.** Map B2-01 to B2-15 to tests and evidence. Write `docs/sea2/DESIGN.md`, covering:
   - the tiled computation of open/enclosed NoData (union-find across cell borders);
   - the bounded distance computation (windows with a `max_shore_distance_m` + `shore_preference_m` halo);
   - the view layout, the identity and the pointer file;
   - the provider;
   - the counterfactual view and run.
2. **Profile.** Add `config/schema/sea_profile.schema.json` and `config/sea_profiles/hk_cedd_2020.json`, with a validator and tests.
3. **Rule.** Implement the classification in `tools/sea2/`. Write the synthetic fixtures for B2-03 first, then the tiled implementation, and test that the one-pass and tiled results are equal (B2-04).
4. **View builder** (`python -m tools.sea2 build`). Derived and synthetic tiles, surface classes, manifest, `view_id`, pointer file. Make the build reproducible.
5. **Provider and F integration.** Only the items in contract design item 7. Run the full F test suite, and check that the raw Cheung Chau `run_id` is unchanged.
6. **Void-impact tool** (`python -m tools.sea2 void-impact`), with its output schema.
7. **Validation script** in the tools environment: the iB5000 report and the sensitivity report.
8. **Real work,** within the contract's scope and budgets, using new names and cache namespaces:
   - build (v), then rebuild it;
   - F runs (a) and (b);
   - `void-impact` (c);
   - the direct-ray checks (d);
   - the validation (e).

   Before any shade run, run `build` and `plan` once with `data/raw/coastline/` made unreadable (B2-02), and restore its permissions afterwards.
9. **Documentation:** `docs/sea2/POLICY.md` and `GUIDE.md` with every required limitation, the F GUIDE section, and `docs/sea2/DEVELOPMENT_REPORT.md`.

## Testing

- Unit tests use tiny synthetic catalogues.
- Run the full existing suite with `pytest tests` before committing; it must pass unchanged.
- Keep a ledger of real-DSM job time, view-build time, peak memory (measure every process, including read-only planning) and disk use.

## Deliverables

- Code, tests, schemas, the Hong Kong profile, and the documents.
- The B2-01 to B2-15 matrix in `docs/sea2/DEVELOPMENT_REPORT.md`: PASS, FAIL or NOT VERIFIED for each, with evidence paths under `docs/sea2/evidence/`. Evidence is text and JSON only; no rasters, views or caches. Keep listings compact: hashes and counts, not full file dumps.
- The resource ledger.
- One local commit containing only this task's files. Inspect the staged diff before committing.

Report the full commit SHA. Do not push, and do not declare acceptance; hand off for independent acceptance.
