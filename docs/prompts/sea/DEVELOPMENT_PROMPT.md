# Sea-surface support development prompt

Implement `SW-SEA-POLICY-1.0` for `shade_watch_hk`, as specified in `docs/prompts/sea/ACCEPTANCE_CONTRACT.md` (`SW-SEA-AC-1.0`). The deliverable is a versioned, sea-filled DSM view that the accepted engine reads, unchanged, through `dsm_dir`. Accepted engine code and scientific rules stay exactly as they are.

## Preconditions

- **Branch and starting point.**
  - Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`.
  - Start from the current HEAD: the region-request (`SW-RGN-AC-1.0`) commit if it already exists — its review may still be pending — otherwise `38303b164d107b81c02f50f14da61951f09e9b49`.
  - Before editing, record HEAD, the branch, dirty files and the contract SHA-256.
- **Engine check.** Confirm that the ten pinned engine files equal `356f611d7b775ce31006904b80ca31d3c1c484b2`. If they differ, stop and report.
- **Read in full (all read-only):**
  - the contract;
  - `data/raw/coastline/README.md`;
  - the iB5000 data dictionary sections for `HydrographyPoly` and `dCoastLine`;
  - `docs/v1/POLICY.md`, `docs/v1/GUIDE.md`, `docs/v2/GUIDE.md`;
  - the source/indexing, halo, threshold and classification code in `src/v1.py`, `src/v1_cache.py`, `src/spatial.py`, `src/shade_watch.py`.
- **Never write to:**
  - `data/raw/` (DSM and coastline);
  - existing `data/processed/` caches;
  - any existing `outputs/`, including the comparison baseline `outputs/v2_daylight_cheungchau_20261009`;
  - `presentations/`;
  - `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - the uncommitted `.gitignore` change;
  - the uncommitted contract files under `docs/prompts/region/` and `docs/prompts/sea/`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Write only to new directories:**
  - `data/processed/coastline/ib5000_20261012/`
  - `data/processed/dsm_views/sea_fill_v1/`
  - `data/processed/shade_v1/sea_fill_v1_*`
  - `outputs/sea_dev_*`
- **FGDB reader environment.**
  - Install the reader (pyogrio or GDAL) in a separate environment outside the repository, for example `~/.venvs/shade_watch_tools`, and commit its pinned lock as `requirements.tools.lock.txt`. Never install into the engine `.venv`.
  - If no standard reader can be installed or found (for example, network is blocked), stop at step 2 and report BLOCKED. Do not substitute a custom FGDB parser.
- **Not authorized:** territory-wide views or shade computation, V3 execution, edits to `config/v3/`, DSM or map downloads (installing the reader package is allowed), UI work, push or PR.

## Implementation sequence

1. **Plan.** Map S01–S14 to tests and evidence. Write a short design note covering:
   - module layout under `tools/sea_view/` (or similar);
   - manifest schema and the `view_id` rule;
   - synthetic-tile naming;
   - compression choice.
2. **Map extraction (tools environment).**
   - Read `HydrographyPoly` with the standard reader, filtered to `FEATURESUBTYPE = 3` and `DATASTATUS = 'E'`.
   - Verify the exact S02 counts.
   - Report invalid geometries; repair them only by a documented, deterministic method.
   - Export `SEF` and `LAF` polygons with holes, plus a manifest that includes source file hashes.
3. **Rasterization and masks (engine `.venv`, read-only use of rasterio).**
   - Use `rasterio.features.rasterize` with the pixel-centre rule on each tile's native grid. Sea = `SEF` minus `LAF`.
   - Build synthetic fixtures for the S03 edge cases.
   - Reproduce the Cheung Chau halo reference counts, and explain any differences.
4. **Territory scan (read-only, ≤ 30 min, writes no tiles).**
   - Over all coastal tiles, compute the S06 distribution.
   - Compute coverage statistics: how many synthetic cells a territory view would need, and the tile-footprint area that is in neither class.
   - If S06 fails, stop and report.
5. **View builder.**
   - Build view (a) Cheung Chau and view (b) Central exactly as the frozen policy specifies: bit-identical non-sea pixels, h at sea-fill pixels, `SEA_` synthetic tiles, surface rasters, `manifest.json`.
   - Rebuild once to prove `view_id` and file hashes reproduce.
   - Confirm that `v1.index_sources(<view>/tiles)` accepts each view.
6. **Helpers.** Implement `read_surface_window` and `effective_policy` outside `src/`, with tests.
7. **Runs (V2 API, scientific outputs only).**
   - Cheung Chau, view (a): the full 2026-01-07 daylight sequence at 10-minute intervals with `nearest5`, using the same settings as the accepted run and cache namespace `sea_fill_v1_<view_id>`.
   - Central, view (b): 3 instants.
   - Compare against the read-only baseline using the S08 and S11 gates, and run the S09 direct-ray reference checks.
8. **Diagnostics.**
   - S10 sensitivity views and runs on one Cheung Chau tile at 3 instants, in a namespace labelled `diagnostic`.
   - Report the results without changing the policy.
9. **Documentation and handoff.**
   - `docs/sea/POLICY.md` and `docs/sea/GUIDE.md`, including every limitation the contract requires.
   - S01–S14 matrix, evidence manifest and resource ledger.

## Testing

- Use synthetic fixtures for edge cases and invariants.
- Run the full existing test suite; it must pass unchanged.
- Compare against the accepted engine's outputs on raw inputs, not only against this code's own expectations.
- Keep a ledger of real-DSM job time, scan time, memory and disk.
- Missing evidence is NOT VERIFIED, not PASS.

## Deliverables and commit

- **Deliverables:** code, tests, the tools lock file, docs and the design note. Add small evidence files only: JSON/CSV summaries and a few PNG figures.
- **Never commit:** derived rasters, views, caches or outputs.
- **Commit:** inspect the staged diff, then make one local commit containing only this task's files, and report the full SHA.

Hand off for independent acceptance. Do not self-accept, push, or start V3 or territory work.
