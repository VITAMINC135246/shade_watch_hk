# Region-request acceptance contract — two-corner rectangle input

Contract ID: `SW-RGN-AC-1.0`
Status: frozen 2026-10-29 by user approval. Record this file's SHA-256 before development.
Decision record: Claude project `claude/DECISIONS.zh-TW.md`, D-002.

This contract is shared by the development prompt and the reviewer. Do not weaken criteria after seeing results. Scope changes require a new contract version.

## Objective

Let a user define the spatial extent of a shade request with two corner points, (x1, y1) and (x2, y2). The rectangle they span must resolve to the existing, independently accepted custom-bounds path (`src/v1.py` `plan_shade(mode="custom", bounds=...)`). A rectangle too large for one V1 request is split automatically into a V2 batch, and its output is read back through the existing logical mosaic.

This is an input adapter. It must not change any scientific rule, cached quantity, engine file or accepted behavior.

## Non-goals

- No edits to the ten engine files that `tools/v3_campaign.py` pins against accepted V2 `356f611d7b775ce31006904b80ca31d3c1c484b2`:
  - `src/v1.py`, `src/v1_cache.py`, `src/horizon.py`, `src/solar.py`, `src/spatial.py`, `src/shade_watch.py`
  - `src/v2.py`, `src/v2_worker.py`, `src/v2_runner.py`, `src/v2_state.py`

  No other file under `src/` may change either, because V3 provenance snapshots hash every `src/*.py`.
- No change to `SW-V1-POLICY-1.0`, the V1/V2 limits, budgets, cache keys or the estimator.
- Not part of this contract: the sea-surface policy (`SW-SEA-AC-1.0`), any UI, V3 profile changes, new data downloads, Windows or WSL work.

## Required design

1. **Location.** New code lives outside `src/`, for example `tools/region_request.py`, with tests in `tests/`. It runs from the repository root with the existing `.venv` and only imports engine APIs; it never modifies them.
2. **Inputs.** Two corners plus an explicit caller-chosen CRS:
   - `wgs84`: latitude and longitude in degrees;
   - `hk1980`: EPSG:2326 easting and northing in metres.

   Never guess the CRS. Corner order does not matter. Reject non-finite values, out-of-range latitude or longitude, zero width or height, and rectangles that intersect no DSM tile in the chosen catalogue. Every error message states its cause.
3. **Transformation.** Convert WGS84 → EPSG:2326 with exactly the construction `src/v1.py` uses for centre selectors: pyproj `Transformer.from_crs("EPSG:4326", "EPSG:2326", always_xy=True)`. Both paths must produce bit-identical coordinates. Record the pyproj and PROJ versions and the transformer description. This contract does not validate the transformation's absolute geodetic accuracy.
4. **Rectangle definition.** After projection, take left = min(x), bottom = min(y), right = max(x), top = max(y) in EPSG:2326. Document that a rectangle drawn in latitude/longitude is not exactly this rectangle. Pass the unsnapped bounds to the engine and report the engine's resolved bounds. Do not reimplement lattice snapping.
5. **Single request.** If the rectangle fits the V1 limits, emit one request equivalent to a hand-written `mode="custom", bounds=[left, bottom, right, top]` request. Read the V1 limits from the engine module; do not copy the constants.
6. **Splitting.** Otherwise:
   - Derive the native-tile lattice from the DSM catalogue (do not hard-code it).
   - Split the resolved rectangle along that lattice so the sub-rectangles partition it exactly: no gaps, no overlaps. Each sub-rectangle must pass `v1.plan_shade`.
   - Emit a V2 batch request file in the schema of `docs/v2/example_batch.json`, with distinct ids, distinct output directories, and `logical_mosaic: true`.
   - If one batch would exceed the V2 artifact or memory budget, either emit several batch files that each pass `plan_batch`, or reject with a clear message stating the minimum number of batches needed. Never raise a budget.
   - Tests only: an optional `max_pixels_per_request` below the V1 limit may force splitting.
7. **Provenance.** Write a sidecar `region_request.json` next to the generated request files, never inside engine output directories. It records the original corners, CRS, transformer description, library versions, requested and resolved bounds, the partition, and the generated request ids.
8. **Interface.** A Python API plus a CLI with two actions:
   - `plan`: validate, resolve, and report tiles, sub-requests and estimates, without computation;
   - `write`: emit the request or batch files and the sidecar.

   Running stays with the existing `python -m src.v1` / `python -m src.v2` commands. The adapter never starts a computation.

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| R01 | Traceability; engine untouched | Starting SHA and contract hash recorded. `git diff <start>..<candidate> -- src/` is empty. A script shows the ten pinned files are byte-identical to `356f611`. |
| R02 | Input validation | Tests cover both CRSs, swapped corner order, swapped lat/lon (out of range), zero-area, non-finite and no-DSM rectangles; each gives a clear rejection or the correct result. |
| R03 | Transformation consistency | For at least 5 points spread across Hong Kong, the adapter's coordinates exactly equal those from the `src/v1.py` selector transformer. Transformer description and library versions recorded. |
| R04 | Equivalence with hand-written bounds | For at least 3 rectangles (inside one tile; across a four-tile corner; fractional-metre corners), the V1 plan key and resolved grid equal those of the equivalent hand-written custom-bounds request. |
| R05 | Exact partition, no duplicate science | For a rectangle that must split: the union of the parts equals the resolved rectangle and the parts are pairwise disjoint; every part passes `plan_shade`; the batch passes `plan_batch`; the number of horizon tasks equals the number of distinct intersecting native tiles. |
| R06 | Real bounded run, logical-mosaic equality | One real V2 run: a rectangle across at least 2 native tiles, split by the test-only limit, at 2 instants. `read_logical_window` over the full rectangle equals a single V1 custom-bounds result pixel for pixel (Shade and Quality), with identical transforms. |
| R07 | Provenance and documentation | The sidecar contains every field listed in design item 7. A guide section gives a WGS84 and an HK1980 example, and states both the rectangle definition and that cost scales with intersecting native tiles, not rectangle area. |
| R08 | Tests and handoff | New automated tests pass; the existing suite passes unchanged; an evidence list is written; an immutable local commit SHA is reported. No push. |

## Budgets

- Ceilings: 20 minutes cumulative real-DSM job wall time, 8 GiB job memory, 5 GiB new artifacts.
- DSM input: `data/raw/dsm/2020/D12.DSM.TIFF`, read-only.
- New outputs go under `outputs/region_dev_*`; the new cache namespace is `data/processed/shade_v1/region_dev`.
- Exhausting a budget makes the affected criteria NOT VERIFIED.

## Decisions and review

- Every criterion is marked PASS, FAIL or NOT VERIFIED, with evidence paths and commands.
- The planning conversation reviews the candidate against this matrix. No separate independent-acceptance conversation is required, because R01 shows that no engine or scientific behavior changed.
- If R01 fails, the change needs independent acceptance before use.
- Each fix requires a new commit SHA.
- Nothing in this contract authorizes a push, merge, V3 execution or UI work.
