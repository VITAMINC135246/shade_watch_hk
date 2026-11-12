# Package F1.0 development prompt

Implement the `shade_map` function and CLI for `shade_watch_hk`, as defined in `docs/prompts/F1/ACCEPTANCE_CONTRACT.md` (`SW-F1.0`). This is an engineering package. The accepted V1/V2 science, the engine and the reviewed region adapter all stay unchanged.

## Preconditions

- **Branch and baseline.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`.
  - The expected starting commit is the commit that added `docs/prompts/F1/`; its full SHA is given in the handoff message. It must contain `f5f24acc4163aa1353534d5db5a5dbe30faf0dae` (A1.1).
  - Before editing, record the actual HEAD, branch, dirty files and the contract's SHA-256. Compare the hash with the frozen value `dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690`.
- **Stop and report** if HEAD differs and either:
  - any of the ten pinned engine files differs from `356f611d7b775ce31006904b80ca31d3c1c484b2`; or
  - `tools/region_request.py` differs from `f5f24ac`.
- **Read first (do not edit):**
  - the whole contract;
  - `docs/region/DESIGN.md`, `docs/region/GUIDE.md` and `tools/region_request.py`;
  - `docs/v1/GUIDE.md`, `docs/v1/POLICY.md` and `docs/v2/GUIDE.md`;
  - in `src/v1.py`: `plan_shade`, the custom-grid code and the instant normalisation;
  - `daylight_bounds` and `daylight_samples` in `src/solar.py`;
  - the batch API in `src/v2.py`, and `read_logical_window` in `src/v2_worker.py`;
  - `outputs/v2_daylight_cheungchau_20261009/REPORT.md`, plus the listing of its `source_view/` (read-only).
- **Leave untouched:**
  - everything under `data/raw/`, and every existing namespace under `data/processed/`;
  - all existing `outputs/` folders;
  - `presentations/`;
  - `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - the uncommitted planner files: the `.gitignore` change, `docs/prompts/**`, `docs/ui/`, `docs/v3/WSL2_SMOKE_TEST.md`, `tools/wsl2_smoke/`, `web/console/` and `data/raw/coastline/README.md`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Never stage or commit** a file you did not create for this task. If the contract file is untracked, verify its hash but do not stage it.
- **Not authorized:** edits under `src/` or to `tools/region_request.py`; sea views or sea policy; downloads; V3 execution; edits to `config/v3/`; web work; push or PR.

## Implementation sequence

1. **Plan.** Map F1-01 to F1-14 to planned tests and evidence. Write a short design note in `docs/shade_map/DESIGN.md` covering:
   - module layout;
   - the configuration schemas;
   - the canonical identity document;
   - the publication and resume state machine (`.partial` → verified → published);
   - the DSM-source interface.
2. **Configuration.** Write the two schemas and the hand-written validator, plus a test that walks every schema rule. Add `config/machine.example.json` and `config/regions/cheung_chau.json`.
3. **Corner rule.** Reject before any planning; use the adapter's transformer for the projected-order check. Use exit code 2 and the `invalid input:` prefix.
4. **Time expansion.**
   - `daylight` is passed to the adapter as dates.
   - `window` and `instants` become explicit HKT instants.
   - The daylight filter uses the engine's `daylight_bounds` at the engine's reference point; dropped times are recorded.
5. **`plan`.**
   - Plan through `plan_region(..., auto_source_view=True)`.
   - Write the plan schema, the estimates (labelled) and the existing-run status.
   - Test planning equivalence against direct adapter calls.
6. **DSM-source interface.** Build the registry and the `raw` provider, including the surface-class reader. Add a test-only provider over a fixture catalogue.
7. **`run`.**
   - Write the adapter sidecar into the work folder, then plan, submit and resume V2 batches with an isolated state directory.
   - Publish frame by frame: cells, VRTs, the optional full image and `frame.json`, all written into `.partial`, verified against `read_region_window`, then renamed.
   - Write the manifest (atomically), the summaries and the lock file.
8. **`prune`.**
9. **Python API.** `shade_map` and `plan_shade_map` share the CLI code path, and write `region_config.json`.
10. **Real runs (a), (b), (c)** within the contract's scope and budget, with new output folders and new cache namespaces.
    - For (a), compare the source-view tile list with the reference run before computing; stop if they differ.
    - Freeze the rectangle for (b) in the evidence before running it.
11. **Documentation.** Write `docs/shade_map/GUIDE.md` with every required limitation, and `docs/shade_map/DEVELOPMENT_REPORT.md`.

## Testing

- Unit tests use tiny synthetic catalogues, including no-DSM cells, edge clipping and a fake source provider.
- Run the full existing test suite before committing; it must pass unchanged.
- Keep a ledger of real-DSM job wall time, peak memory and disk use, and stay within the contract's budgets.

## Deliverables

- Code, tests, schemas, example configs and documentation.
- The F1-01 to F1-14 matrix in `docs/shade_map/DEVELOPMENT_REPORT.md`: PASS, FAIL or NOT VERIFIED for each, with evidence paths under `docs/shade_map/evidence/`. Evidence is text and JSON only; no rasters, views or caches.
- The resource ledger.
- One local commit containing only this task's files. Inspect the staged diff before committing.

Report the full commit SHA. Do not push, and do not declare acceptance; hand off for independent acceptance.
