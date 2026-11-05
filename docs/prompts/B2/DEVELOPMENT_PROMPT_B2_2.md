# Package B2.2 development prompt

Implement `SW-SEA-POLICY-2.2` for `shade_watch_hk`, as defined in `docs/prompts/B2/CONTRACT_B2_2.md` (`SW-B2.2`). Every NoData pixel inside the sea view's domain is filled at h_fill = 0.00 m HKPD. The B2.0 label rule decides only the surface class. The engine and the region adapter stay unchanged. Package F changes only as listed in the contract's design item 8.

This is a second development round of package B. It reuses and changes the code of the unaccepted B2.0 candidate `5744e2301eea34f8bae05b9df3e14508425b8282`.

## Preconditions

- **Branch and baseline.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`.
  - The starting commit's full SHA is given in the handoff message. It must contain `5744e23` and `docs/prompts/B2/CONTRACT_B2_2.md`.
  - Before editing, record:
    - the actual HEAD;
    - the branch;
    - the dirty files;
    - the SHA-256 of `docs/prompts/B2/CONTRACT_B2_2.md`, compared with the value given in the handoff message.
- **Stop and report** if any of the following differ:
  - any of the ten pinned engine files, compared with `356f611d7b775ce31006904b80ca31d3c1c484b2`;
  - `tools/region_request.py`, compared with `f5f24ac`;
  - F1.0 code, compared with `35225fd` plus the B2.0 design-item-7 changes in `5744e23`.
- **Read first (do not edit):**
  - the whole contract;
  - `docs/OUTPUT_CODES.md`;
  - `docs/planning/DECISIONS.zh-TW.md` (D-014 to D-016) and `docs/planning/reviews/B2_PRECHECK_5744e23.md`;
  - the B2.0 development report `docs/sea2/DEVELOPMENT_REPORT.md` and its evidence;
  - `tools/sea2/`, `docs/sea2/`;
  - `docs/shade_map/{GUIDE,DESIGN}.md` and `tools/shade_map/` (especially `sources.py` and `publication.py`);
  - `docs/v1/POLICY.md`, `src/shade_watch.py::classify`, the support and threshold code in `src/v1.py`, and `src/horizon.py` (`direct_ray_reference`, `diagnostic_horizon`);
  - `data/raw/coastline/README.md` (for validation only).
- **Leave untouched:**
  - everything under `data/raw/` (`data/raw/coastline/` is read only by the validation script, in the tools environment);
  - every existing namespace under `data/processed/`, including B2.0's `dsm_views/sea_fill_v2/` and `shade_v1/sea_fill_v2_*`, `sea_voidfill_v2_diagnostic*` and `sea2_raw_20261104`;
  - all existing `outputs/` folders, including B2.0's `outputs/sea2_f_20261104/` and `outputs/sea2_diagnostic_work/`, and the F1.0 development and review outputs;
  - `docs/sea2/DEVELOPMENT_REPORT.md` and B2.0 evidence under `docs/sea2/evidence/` outside `b2_2/`;
  - `docs/prompts/`, `docs/planning/`, `docs/OUTPUT_CODES.md`, `presentations/` and `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - the uncommitted planner files: the `.gitignore` change, `docs/prompts/{region,runner,sea}/`, `docs/ui/`, `docs/v3/WSL2_SMOKE_TEST.md`, `tools/wsl2_smoke/` and `web/console/`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Never stage or commit** a file outside the contract's allowed-file list.
- **Not authorized:**
  - edits under `src/` or to `tools/region_request.py`;
  - F changes beyond the contract's design item 8;
  - reclassifying quality 3 or 4, or extending the search distance;
  - exception zones or profile changes;
  - territory shade runs, the four-region measurement, or regions other than (a), (b) and (c);
  - downloads other than the tools environment in design item 10;
  - V3, `config/v3/`, web work, push or PR.

## Implementation sequence

1. **Plan.** Map B2-16 to B2-31 to tests and evidence. Update `docs/sea2/DESIGN.md` for:
   - filling every NoData pixel;
   - the new classes and the domain;
   - synthetic tiles for every empty cell;
   - the new namespaces;
   - build-code hashes in the manifest;
   - the provider rename;
   - the fill-impact diagnostic.
2. **Rule and classes.** Change the classifier so that classes are 0 to 4 and 255 outside the domain, and every NoData pixel gets h_fill.
   - Update the synthetic fixtures for B2-18 first, including the new cases: exclusion still filled; a tile whose declared NoData is not −9999; a partial domain-edge cell.
   - Keep the one-pass versus tiled equality test (B2-19).
3. **View builder** (`python -m tools.sea2 build`):
   - output under `data/processed/dsm_views/sea_fill_v2_2/` with its own pointer;
   - synthetic `FILL_e<left>n<bottom>.tif` tiles for every empty lattice cell in the domain;
   - manifest with build-code hashes;
   - reproducible.
4. **Provider and F integration.** Only the items in contract design item 8:
   - register `sea-2.2` and remove `sea-2.0`;
   - change the one surface allowlist in `publication.py`;
   - update the schemas, the example machine config and the F docs.

   Run the full F test suite unchanged, and both raw `run_id` checks against a plan at `35225fd`. Replace the strict expected-failure test with a passing six-code publication test.
5. **Fill-impact diagnostic** (`python -m tools.sea2 fill-impact`), with dependency rasters, metrics and `config/schema/fill_impact.schema.json`. Withdraw `void-impact`.
6. **Tools environment** (contract design item 10). Create it at `~/venvs/shade_watch_tools` with Python 3.12:

   ```
   <python3.12> -m venv ~/venvs/shade_watch_tools
   ~/venvs/shade_watch_tools/bin/pip install --no-deps -r requirements.tools.lock.txt
   ```

   Record the interpreter path and version, the pip download URLs, and the SHA-256 of every wheel. Install nothing else. If the download fails, record the failure and mark the affected criteria NOT VERIFIED; do not use other packages or versions.
7. **Validation script:** the iB5000 label report (including the Victoria Harbour share), the class-3 component report and the sensitivity report.
8. **Real work,** within the contract's scope and budgets, using new names and namespaces:
   - keep the machine and region configs for these runs under `docs/sea2/evidence/b2_2/configs/` (`config/regions/` stays unchanged). Use an `output_root` under a new `outputs/sea2_2_*` folder and a new raw cache namespace `sea2_2_raw_*`;
   - snapshot the protected listings first;
   - build (v) once;
   - confirm that region (c)'s targets contain classes 0 to 4; if they do not, stop and report;
   - F runs (a), (b) and (c);
   - fill-impact (d);
   - direct-ray checks (e);
   - validation (f).

   Before any shade run, run `build` and `plan` with `data/raw/coastline/` made unreadable. Keep it unreadable through the F runs and fill-impact as well. Record a failing read probe during the blackout, and the original and restored modes. Restore before the validation step.
9. **Documentation:**
   - `docs/sea2/POLICY.md`, `GUIDE.md` and `DESIGN.md` for B2.2, referring to `docs/OUTPUT_CODES.md`, with every required limitation;
   - the F GUIDE section on `sea-2.2` and the F DESIGN surface-code description;
   - `docs/sea2/DEVELOPMENT_REPORT_B2_2.md`.

## Resources and monitoring

- **Measure every process** that touches real DSM data, including read-only plans and test runs on real data. Record wall time, peak RSS and new-artifact bytes. Keep the ledger in `docs/sea2/evidence/b2_2/resources.jsonl`.
- **Use a wall clock that includes system sleep** for every budget (not uptime or a monotonic clock that stops during sleep). Keep the Mac awake during jobs, for example by running them under `caffeinate -dims`. Stop a job when its budget runs out.
- **Budgets** (new ledger; B2.0 time is not carried over):
  - real-DSM jobs ≤ 60 min;
  - one view build ≤ 60 min, including stopped attempts;
  - report-only validation ≤ 30 min;
  - job memory ≤ 12 GiB;
  - new artifacts ≤ 30 GiB.

  When a budget runs out, mark the affected criteria NOT VERIFIED; do not extend it.
- **Harness hygiene.** Any temporary launcher or permission helper must be safe under multiprocessing spawn (guard its entry point). If a helper is part of the evidence, include its source under `docs/sea2/evidence/b2_2/`.

## Testing

- Unit tests use tiny synthetic catalogues.
- Run the full suite with `pytest tests` before committing. Existing F test functions must pass unchanged.

## Deliverables

- Code, tests, schemas and documents within the contract's allowed-file list.
- The B2-16 to B2-31 matrix in `docs/sea2/DEVELOPMENT_REPORT_B2_2.md`: PASS, FAIL or NOT VERIFIED for each, with evidence paths under `docs/sea2/evidence/b2_2/`.
  - Evidence is text and JSON only: no rasters, views or caches. Keep listings compact: hashes and counts, not full dumps.
  - B2-22's rebuild part is NOT VERIFIED by design.
- The resource ledger and the protected listings before and after.
- One local commit containing only allowed files. Inspect the staged diff before committing.

Report the full commit SHA. Do not push, and do not declare acceptance; hand off for independent acceptance.
