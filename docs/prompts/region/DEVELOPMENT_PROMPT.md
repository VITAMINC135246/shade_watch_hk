# Region-request development prompt

Implement the two-corner rectangle request adapter for `shade_watch_hk`, as defined in `docs/prompts/region/ACCEPTANCE_CONTRACT.md` (`SW-RGN-AC-1.0`). This is an input layer only. Accepted V1/V2 science and engine code stay unchanged.

## Preconditions

- **Branch and baseline.** Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk` on branch `feature`. The expected starting commit is `38303b164d107b81c02f50f14da61951f09e9b49`. Before editing, record the actual HEAD, branch, dirty files and the contract's SHA-256.
- **If HEAD differs,** report it. Continue only if all ten pinned engine files still match `356f611d7b775ce31006904b80ca31d3c1c484b2`.
- **Read first (do not edit):**
  - the whole contract;
  - `docs/v1/GUIDE.md`, `docs/v1/POLICY.md` and `docs/v2/GUIDE.md`;
  - the custom-bounds, selector and limit code in `src/v1.py`;
  - the batch-planning code in `src/v2.py`.
- **Leave untouched:**
  - everything under `data/raw/` and `data/processed/`;
  - all existing `outputs/`;
  - `presentations/`;
  - `docs/PROJECT_STATUS_2026-10-29.zh-TW.md`;
  - `data/raw/coastline/README.md`;
  - the uncommitted `.gitignore` change and the uncommitted contract files under `docs/prompts/region/` and `docs/prompts/sea/`;
  - the sibling project `HEAT_INDEX_ESTIMATION_UROP_2627FALL`.
- **Never stage or commit** a file you did not create for this task.
- **Not authorized:** downloads, V3 execution, edits to `config/v3/`, UI work, push or PR.

## Implementation sequence

1. **Plan.** Map R01–R08 to planned tests and evidence. Write a short design note covering:
   - module location;
   - API and CLI actions;
   - sidecar schema;
   - partition algorithm.
2. **Validation and transformation.** Implement input validation and the WGS84 → EPSG:2326 conversion. Build the transformer exactly as `src/v1.py` builds its selector transformer, and test that the two agree bit for bit.
3. **Rectangle resolution.** Build the rectangle in EPSG:2326 and resolve it through `v1.plan_shade(mode="custom", bounds=...)`. Compare its plan keys against equivalent hand-written requests.
4. **Splitting.** Derive the native-tile lattice from the indexed catalogue and partition along it. Check exact coverage and disjointness. Validate each part with `plan_shade` and the whole with `v2.plan_batch`. Handle batches that exceed the budget as the contract requires.
5. **Provenance and CLI.** Write the sidecar and add the `plan` and `write` CLI actions. Add a guide section (`docs/region/GUIDE.md`, or a section in `docs/v2/GUIDE.md`) with:
   - one WGS84 example and one HK1980 example;
   - a short limitations list.
6. **Real bounded run (R06).** Stay within budget, use new output directories and the `region_dev` cache namespace, and compare the logical-mosaic window against a single V1 custom-bounds run pixel for pixel.

## Testing

- Unit tests use synthetic or tiny catalogues where possible.
- Run the full existing test suite before committing; it must pass unchanged.
- Keep a ledger of real-DSM job time, memory and disk use.

## Deliverables

- Code, tests, guide text and the design note.
- The R01–R08 matrix: PASS/FAIL/NOT VERIFIED for each, with evidence paths.
- The resource ledger.
- One local commit containing only this task's files. Inspect the staged diff before committing.

Report the full commit SHA. Do not push, and do not declare acceptance; hand off for review.
