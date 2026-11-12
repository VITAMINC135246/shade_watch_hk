# Region-request contract amendment `SW-RGN-AC-1.1`

Status: frozen 2026-10-29 by user approval. Record this file's SHA-256 before development.

This amendment changes the frozen `SW-RGN-AC-1.0` (`docs/prompts/region/ACCEPTANCE_CONTRACT.md`, SHA-256 `3bc918a993a3f5f7baebc26db5c698173e35b0d9c81f31c6a6bee1c76980a579`). It responds to the pre-commit review findings F1–F4 and F6.

- It only adds scope; no 1.0 criterion is weakened.
- Every 1.0 rule still applies unless a section below replaces it.
- Decision record: D-002 (user decision of 2026-10-29: cells without DSM must neither be rejected nor dropped; they are processed normally).

## A1. Cells without DSM files are never rejected or dropped

This section replaces the 1.0 behaviour in which a partition cell without DSM rejects the whole request.

### Definition

A *no-DSM cell* is a native-lattice cell of the resolved rectangle that intersects no tile in the chosen catalogue. Typically it is open sea in the raw catalogue.

### How no-DSM cells are processed

No-DSM cells stay inside the requested output, and the unchanged engine processes them by its normal rules:

- **The catalogue supplies a tile there** (for example a synthetic sea tile in a sea-fill view): the pixels are computed like any other surface.
- **The catalogue supplies no tile there**: the engine writes Shade 255 / Quality 1 (missing target DSM). This is the same thing it already does for any uncovered pixel of a custom grid.

The adapter never fills, interpolates or relabels these pixels itself.

### Partition rules

- Parts are lattice-aligned rectangles.
- Each part contains at least one tile, as `plan_shade` requires, and stays within every V1/V2 limit.
- No part consists only of no-DSM cells. Merge such cells into an adjacent part instead.
- Prefer fewer, larger parts, subject to the limits. This addresses finding F4.

### Residual case

Rarely, a contiguous no-DSM area cannot be merged into any part without exceeding a limit; this can happen only far from every tile. Even then the adapter does not reject the request. Instead:

- It records each such area in the sidecar under `no_dsm_areas`, with its bounds and the reason.
- The plan output states that, with this catalogue, these areas will read as Shade 255 / Quality 1.
- The read-back helper returns exactly that encoding for these areas.

The parts and the `no_dsm_areas` together partition the resolved rectangle exactly: no gaps and no overlaps.

### Unchanged rule

A request is still rejected only when the whole rectangle intersects no tile.

## A2. Daylight sequences

- Besides `instants`, the adapter accepts `dates` (Hong Kong calendar dates) plus `interval_minutes`. These are passed unchanged to `plan_shade(dates=..., interval_minutes=...)`.
- If a request would exceed the V1 frame limit (512 per request), split it by date into several requests.
- Never interpolate between dates.
- The CLI gains `--date` (repeatable) and `--interval-minutes`.

## A3. Request-local source views (performance only)

- **The option.** `auto_source_view` (CLI: `--auto-source-view`) builds a fresh `outputs/region_views/<hash>/` containing symlinks to every catalogue tile that intersects the 1 km halo of any target tile.
- **Building the view.** May use a header-only catalogue index, cached by path, size and mtime.
- **Planning.** Still uses the engine's own indexing of the view.
- **Batch packing.** Passes pre-built V1 `ShadePlan` objects to `plan_batch` wherever possible, so the catalogue is not re-indexed on every trial.
- **Guide.** The guide must warn that planning directly against the full 3,310-tile raw catalogue hashes about 26 GB per plan.

## Added acceptance criteria

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| R09 | No-DSM cells | Fixture catalogue with no-DSM cells both inside and at the edge of the rectangle. The request plans successfully, and no part lacks tiles. Parts plus any `no_dsm_areas` partition the resolved rectangle exactly. Read-back gives Shade 255 / Quality 1 on no-DSM cells and engine values elsewhere. With a second fixture catalogue that adds a tile on one of those cells, that cell is computed rather than returned as 255. A rectangle with no tile at all is still rejected. |
| R10 | Daylight dates | A dates-mode plan has the same plan key as a hand-written `plan_shade(dates=...)` plan. A request over 512 frames splits by date, and the frames of the parts equal the union of the per-date frames. |
| R11 | Source-view identity | For 3 regions (coastal, inland, across a tile corner), the spatial keys and V1 plan keys from the auto source view equal those from the full catalogue. Planning wall time is reported for both. |
| R12 | Stronger real evidence | Re-run R06 using two instants with different cache directions and a separate V1 cache namespace, so the V1 reference itself computes (`computed > 0`). Equality still holds. |

## Budgets and review

- **Budgets:** the same as 1.0.
- **Exception for R11:** it may time one full-catalogue planning per region. This is read-only indexing; record its time in the ledger.
- **Review:** done by the planning conversation; no science is changed.
- **Delivery:** one commit may satisfy both 1.0 and 1.1. The development report must then list R01–R12.
