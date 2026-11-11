# Sea-surface support acceptance contract — derived sea-filled DSM view

Contract ID: `SW-SEA-AC-1.0`
Status: frozen 2026-10-29 by user approval. Record this file's SHA-256 before development.
Policy introduced: `SW-SEA-POLICY-1.0`, applied as a data layer on top of the unchanged engine policy `SW-V1-POLICY-1.0`.
Decision record: Claude project `claude/DECISIONS.zh-TW.md`, D-003.

The development prompt and the independent-acceptance prompt both use this contract. Do not weaken any criterion after seeing results. Any change to scope, policy values or budgets requires a new contract version, agreed before work starts.

## Problem and objective

In the CEDD 2020 DSM, open water has no elevation (NoData). The accepted engine counts NoData within 1 km in the sunward direction as incomplete support (Quality 2), so coastal land ends up mostly invalid. In the accepted Cheung Chau run (`outputs/v2_daylight_cheungchau_20261009`, read-only), 53.0% of land pixels were Quality 2 at 12:30 HKT, and 53.9% of the frame was NoData (Quality 1).

Objective: build a versioned, provenance-tracked sea-filled DSM view.

- **How the view works.**
  - DSM NoData that an authoritative map identifies as sea becomes a horizontal water surface at a fixed elevation.
  - The accepted engine runs unchanged on the view, through `dsm_dir`.
- **What changes in the results.**
  - Sea provides support, and can act as an obstacle, for land.
  - Sea pixels inside target tiles are classified by the engine like any other surface (0, 1 or 255).
  - A static surface-class layer keeps policy-filled water distinguishable from DSM-observed surfaces in every downstream analysis.

## Frozen policy decisions (`SW-SEA-POLICY-1.0`)

1. **Sources.**
   - DSM: `data/raw/dsm/2020/D12.DSM.TIFF` (read-only). Vertical datum is HKPD, per `data/raw/dsm/Metedata for LiDAR Data (2020).html`.
   - Map: Lands Department iB5000 seamless FGDB, `data/raw/coastline/ib5000_seamless_20261012/iB5000.gdb` (read-only). Layer `HydrographyPoly`, `FEATURESUBTYPE = 3`, `DATASTATUS = 'E'`. Code `SEF` (Sea Fill) defines sea; code `LAF` (Coastline and Land Fill) defines land. See `data/raw/coastline/README.md`.
2. **Sea-fill pixel.** A pixel on the native 0.5 m lattice is a sea-fill pixel if and only if all three hold:
   - its DSM value is NoData (non-finite or −9999);
   - its centre lies inside the union of `SEF` polygons;
   - its centre lies outside the union of `LAF` polygons.
3. **Coastline tolerance band: 0 m.** DSM NoData pixels inside `LAF` stay NoData. Tolerance-band variants may appear only as labelled diagnostics.
4. **Fill elevation.** h = +1.60 m HKPD, stored as float32. This is the median DSM waterline observed in the Cheung Chau planning check. Development must check it territory-wide (S06). If that check fails, stop and report; never retune h silently.
5. **Everything else stays NoData**, including:
   - DSM NoData inside `LAF` (piers, coastal slivers, land voids);
   - reservoirs and other enclosed water;
   - pixels in neither `SEF` nor `LAF` (for example the Shenzhen side of the northern boundary);
   - areas with no map coverage.
6. **Sea pixels are targets.** The unchanged engine classifies sea-fill pixels inside requested tiles as 0, 1 or 255. These labels are less certain than land labels, because boats, pontoons and tide are not modelled. Shade on water is not cooling and not ΔT.
7. **Synthetic sea tiles.** Create one for each native-lattice cell that:
   - has no supplied DSM file;
   - intersects the 1 km halo of a supplied tile in the view's scope;
   - contains at least one sea-fill pixel centre.

   Each synthetic tile holds h at sea-fill pixels and NoData elsewhere. It has the same grid, size, CRS, data type and NoData value as native tiles, never overlaps a supplied tile, and uses a distinct, non-colliding name (prefix `SEA_`).
8. **Supplied tiles.**
   - Every non-sea-fill pixel is bit-identical to the raw tile; georeferencing and NoData value are preserved.
   - A tile with no sea-fill pixels may be a symlink to, or a byte-identical copy of, the raw file.
   - Lossless compression is allowed and must be declared.
   - The four known shifted-origin tiles are not corrected.
9. **Surface-class layer.** Each tile in the view (supplied and synthetic) has a static uint8 GeoTIFF aligned to it:
   - 0 = DSM-observed surface;
   - 1 = sea-fill water at h;
   - 255 = no surface (NoData remains).
10. **Identity.**
    - A view is identified by a `view_id`: the hash of its manifest content, excluding timestamps.
    - The manifest records:
      - policy ID and h;
      - map identity: hashes of the FGDB files read, and the data dictionary hash;
      - DSM catalogue identity;
      - rasterization rule and library versions;
      - scope;
      - per-tile records: source SHA-256, output SHA-256, sea-fill pixel count, synthetic flag.
    - Shade runs use the cache namespace `data/processed/shade_v1/sea_fill_v1_<view_id>`.
    - Engine outputs still carry `SW-V1-POLICY-1.0` tags; the effective policy pair is resolved through the view manifest.

## Required design

- **Engine untouched.**
  - The ten engine files pinned by `tools/v3_campaign.py` stay byte-identical to accepted V2 `356f611d7b775ce31006904b80ca31d3c1c484b2`: `src/v1.py`, `src/v1_cache.py`, `src/horizon.py`, `src/solar.py`, `src/spatial.py`, `src/shade_watch.py`, `src/v2.py`, `src/v2_worker.py`, `src/v2_runner.py`, `src/v2_state.py`.
  - Nothing else under `src/` changes either.
  - New code lives outside `src/`, for example under `tools/sea_view/`.
- **Map extraction.**
  - Use a standard OpenFileGDB reader (pyogrio or GDAL) in a separate tools environment outside the repository, for example `~/.venvs/shade_watch_tools`, pinned in a new `requirements.tools.lock.txt`.
  - The engine `.venv` must not change.
  - Export only the polygons the policy needs to a derived, hashed GeoJSON or GeoPackage under `data/processed/coastline/ib5000_20261012/`, with a manifest of feature counts, CRS and source hashes.
  - Report invalid geometries. Repair them only by a documented, deterministic method.
- **Rasterization** runs in the engine `.venv` using `rasterio.features.rasterize`:
  - pixel-centre rule (`all_touched=False`);
  - polygon holes honored;
  - on each tile's own native grid.
- **View builder.**
  - Input: a scope (a list of target tiles, or the authorized territory option). From it the builder derives the supplied tiles needed for the 1 km halos and the synthetic cells.
  - Output, written only to `data/processed/dsm_views/sea_fill_v1/<view_id>/`:
    - `tiles/`: the `dsm_dir` passed to the engine;
    - `surface/`;
    - `manifest.json`.
  - Re-running with identical inputs reproduces the same `view_id` and file hashes.
- **Helpers (outside the engine).**
  - `read_surface_window(view, bounds)`: returns surface classes for any EPSG:2326 grid on the 0.5 m lattice, in the same way as `read_logical_window`.
  - `effective_policy(result_index_path)`: resolves the DSM view manifest from a result index and reports the policy pair and `view_id`.
- **Documentation.**
  - `docs/sea/POLICY.md`: frozen decisions, rationale, limitations and identity rules.
  - `docs/sea/GUIDE.md`: how to build a view and run V1/V2 against it.
  - Limitations must name:
    - boats and pontoons are absent;
    - tide is not modelled;
    - the map dates from 2026 but the DSM from 2019–20, so reclamation may have drifted;
    - piers and coastal slivers inside `LAF` stay unknown;
    - reservoirs are unchanged;
    - sea-target labels are less certain than land labels;
    - shade ≠ cooling.

## Authorized computation scope

- **Views for exactly two scopes:**
  - (a) Cheung Chau 2×2 plus halos: `14NW19B(e820n807,e821n808).tif`, `14NW20A(e821n807,e821n808).tif`, `14NW19D(e820n807,e821n807).tif`, `14NW20C(e821n807,e821n807).tif`;
  - (b) Central/Mid-Levels V3 pilot 2×2 plus halos: `11SW8D(e833n815,e834n816).tif`, `11SW9C(e834n815,e835n816).tif`, `11SW13B(e833n815,e834n815).tif`, `11SW14A(e834n815,e835n815).tif`.
- **One read-only territory-wide scan,** for S06 and coverage statistics. It writes no territory view.
- **Diagnostic sensitivity views,** Cheung Chau only, in a separate namespace labelled `diagnostic`:
  - h = 0.00 m and h = 3.00 m;
  - tolerance bands of 2.5 m and 5 m.
- **Not authorized:** a territory view, territory-wide shade computation, V3 execution, edits to `config/v3/`, downloads, UI, push.

## Reference values from planning (diagnostic, not gates)

These come from an independent minimal FGDB reader and PIL rasterization.

- **Feature counts:** `HydrographyPoly` has 7,116 rows. In subtype 3, `LAF` has 1,111 and `SEF` has 345. `LAF` attribute area: 1,114.7 km².
- **Cheung Chau halo window** (EPSG:2326 bounds 819250, 806200, 822750, 809400):
  - DSM NoData: 34,647,367;
  - NoData ∩ (`SEF` − `LAF`): 34,617,537;
  - NoData ∩ `LAF`: 29,830;
  - DSM-valid ∩ (`SEF` − `LAF`): 357,470.
- **Cheung Chau Quality 2 → sunlit** (sampled 1/16, strict policy, estimates only): 08:30 87.4%, 12:30 86.6%, 15:10 75.8%.

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| S01 | Traceability | Starting SHA, contract hash, and both environments (engine and tools) with their locks recorded. FGDB files read, data dictionary and scoped DSM tiles identified by hash. Unrelated files untouched. |
| S02 | Map extraction | A standard reader was used. Counts are exactly: `LAF` 1,111, `SEF` 345, `HydrographyPoly` total 7,116. CRS equivalent to EPSG:2326. Invalid geometries listed together with how each was handled. The derived vector file is hashed and listed in the manifest. |
| S03 | Rasterization | Pixel-centre rule; holes honored. The Cheung Chau halo counts match the four reference values within 0.5% each, or any larger difference is explained with sampled pixel-level evidence. Synthetic edge-case tests cover a hole, a sliver, a pixel centre exactly on an edge, and `SEF`/`LAF` overlap. |
| S04 | Fill correctness | In every derived supplied tile: non-sea-fill pixels are bit-identical to raw; sea-fill pixels are exactly float32 1.60; no DSM-valid pixel changed; no NoData pixel in `LAF`, or in neither class, was filled; transform, CRS, size, data type and NoData value are identical. |
| S05 | Synthetic tiles | Lattice-aligned and native-sized, never overlapping a supplied tile, and covering every sea-fill cell within the 1 km halos of scoped targets. `v1.index_sources` accepts the view; no new ambiguous overlap. |
| S06 | Fill-elevation check | The read-only territory scan reports n, p5, p25, p50, p75 and p95 for DSM-valid pixels 8-adjacent to sea-fill pixels. PASS only if p50 lies in [1.30, 1.90] m. h is not changed either way. |
| S07 | Engine untouched; identity separation | `git diff <start>..<candidate> -- src/` is empty and the pinned files equal `356f611`. View runs use the new cache namespace. Plan keys differ from the raw-catalogue plan keys wherever any dependency changed. Listings before and after show no writes to historical outputs or caches. Rebuilding the view reproduces its `view_id`. |
| S08 | Land regression on Cheung Chau | Run view (a) over the full 2026-01-07 daylight sequence at 10-minute steps (65 frames), with the same settings as the accepted run. Compare only land pixels (surface class 0) against the read-only raw result. Gates: (i) zero shaded → sunlit transitions; (ii) Quality 1 land pixels stay 255; (iii) a sunlit pixel may become non-sunlit only where a filled cell is a demonstrated blocker or the tile's distant-obstruction threshold rose — old and new `threshold_deg` reported per tile, and every case explained. Transitions of former Quality 2 pixels to 0/1/255 reported per frame. |
| S09 | Sea-target consistency | Label fractions of sea-fill pixels reported per frame. At three instants, at least 200 sampled sea-fill pixels per instant — including water next to tall structures — get the same label from the engine as from an independent direct-ray reference on the view (`src/horizon.direct_ray_reference` or `diagnostic_horizon`), within the engine's documented equality tolerance. This tests numerical consistency only, not accuracy. |
| S10 | Sensitivity diagnostics | On one Cheung Chau tile at 08:30, 12:30 and 15:10: label changes for h = 0.00 m and 3.00 m against 1.60 m, reported separately for land and sea targets; and former-Quality-2 recovery with 2.5 m and 5 m tolerance bands. Reported without changing the frozen policy. |
| S11 | Urban guard (Central) | View (b) built. DSM NoData inside `LAF` remains NoData (counts reported), while Victoria Harbour is filled. One V2 run at 3 instants on view (b), with S08 gates (i) and (ii) applied to land pixels. |
| S12 | Surface layer and provenance helpers | Surface rasters align with their tiles. `read_surface_window` returns correct classes for the Cheung Chau combined grid and for an odd-offset crop. `effective_policy` resolves the policy pair and `view_id` from a result index. |
| S13 | Scope and resources | Only the authorized views were built; no territory view was written. All budgets respected, with a ledger of real job time, memory and disk use. |
| S14 | Tests, docs, handoff | Automated tests on synthetic fixtures (rasterization edges, fill invariants, synthetic-tile alignment, identity reproducibility). The full existing suite passes unchanged. POLICY and GUIDE include every required limitation. Evidence manifest present. Immutable local commit SHA reported. No push. |

## Budgets

| Phase | Real-DSM job wall time | Read-only territory scan | Job memory | New artifacts |
| --- | --- | --- | --- | --- |
| Development | ≤ 60 min | ≤ 30 min | ≤ 12 GiB | ≤ 20 GiB, covering views, vector exports, caches, outputs and diagnostics |
| Independent acceptance | ≤ 45 min | — | same | same |

When a budget is exhausted, the criteria it affects become NOT VERIFIED; the budget may not be extended.

## Decisions and release

- **Marking.** Each of S01–S14 is marked PASS, FAIL or NOT VERIFIED, with evidence paths and commands.
- **Acceptance.** `SW-SEA-POLICY-1.0` is accepted only if all criteria pass in a separate independent-acceptance conversation.
- **Scope of acceptance.** Engineering acceptance is not observational accuracy: shade on both water and land remains NOT VERIFIED against observations.
- **What acceptance does not authorize.** It does not authorize a territory view, V3 execution, V3 profile changes or a push. Using the view in V3 requires a versioned V3 profile amendment.
- **Fixes.** Each fix needs a new commit SHA and targeted re-acceptance.
