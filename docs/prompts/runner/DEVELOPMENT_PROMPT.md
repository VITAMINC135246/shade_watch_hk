# Runner and local API development prompt (D-2)

Implement the headless job runner and local JSON API for `shade_watch_hk`, as specified in `docs/prompts/runner/ACCEPTANCE_CONTRACT.md` (`SW-RUN-AC-1.0`) and `docs/ui/DESIGN.md`. You are the back-end executor; Claude builds the browser front end against this API. Science and engine code stay unchanged.

## Preconditions

- **Repository and branch.** Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`. Start from the current HEAD, which should contain the reviewed region-adapter commit (`SW-RGN-AC-1.0` + `1.1`), and the sea commit if one exists.
- **Record before editing:** HEAD, branch, dirty files, and the contract's SHA-256.
- **Stop and report** if either of these fails:
  - the ten pinned engine files equal `356f611`;
  - the adapter provides dates mode and request-local source views.
- **The smoke-test prerequisite** applies unless the user has waived it for development. Record which case applies.
- **Read fully:**
  - the contract and the design;
  - `docs/v1/GUIDE.md` and `docs/v2/GUIDE.md`;
  - the region adapter and its guide;
  - the planning, state and status APIs in `src/v1.py`, `src/v2.py` and `src/v2_state.py`.
- **Sea features** must work when no sea-view manifest exists. When one does exist, use the `SW-SEA-AC-1.0` helpers (`read_surface_window`, `effective_policy`); never reimplement them.
- **Read-only:**
  - raw data, and historical outputs and caches;
  - `presentations/`;
  - uncommitted planner files: `.gitignore`, `docs/prompts/**`, `data/raw/coastline/README.md`, `docs/ui/**`, `docs/v3/WSL2_SMOKE_TEST.md`, `tools/wsl2_smoke/**`;
  - sibling projects.
- **Write only to:** `tools/runner/`, `tests/`, `docs/runner/`, `outputs/runner*`, and `data/processed/shade_v1/runner_dev`.
- **Not authorized:** new packages in `.venv`, changes to `src/`, front-end work beyond serving static files, V3, territory runs, downloads, push, PR.

## Implementation sequence

1. **Plan.** Map U01–U12 to tests. Write a short design note covering: module layout; job and plan schemas; process supervision; how source views are reused; and the rendering approach.
2. **Fixture catalogue.** Build a few synthetic 0.5 m tiles in a temporary directory. Also set up one real bounded case for U11.
3. **Planning and source views** (U04, U05), through the adapter.
4. **Detached execution:** job registry, cancel and resume (U06, U07). Use psutil identity checks and atomic JSON writes.
5. **API server** (U02, U03, U09). Use the standard-library `http.server` with a threading server, bound to 127.0.0.1. Implement the JSON schemas exactly as in the contract table. Serve `web/console/` as static files if that directory exists.
6. **Results** (U08, U10): previews, pixel queries, statistics and file listings. Put the provenance keys and the disclaimer on every result-bearing response.
7. **Real bounded run** (U11) through the API, compared with a direct V2 run.
8. **`docs/runner/GUIDE.md`.** Cover: start-up on the Mac and in WSL; `resume-incomplete` after a reboot; optional autostart (systemd in WSL, or Windows Task Scheduler running `wsl -e`); troubleshooting.

## Testing and delivery

- Run the full existing test suite; it must pass unchanged.
- Keep a ledger of real-DSM job time, memory and disk.
- Deliver:
  - code, tests, the guide and the design note;
  - the U01–U12 matrix, with evidence paths;
  - `docs/runner/DEVELOPMENT_REPORT.md`.
- Inspect the staged diff, then make one local commit containing only this task's files. Report the full SHA.
- Do not push. Hand off for review.
- If your quota runs out mid-way, stop at a coherent point and leave a status note in the report.
