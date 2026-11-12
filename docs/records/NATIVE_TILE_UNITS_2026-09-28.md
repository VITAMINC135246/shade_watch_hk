# Native-tile-sized spatial work units

The user clarified that one native DSM tile's dimensions should be the basic spatial work unit. This supersedes the initial default of square 1024-pixel cores. The original brief required evaluating 1024, 2048 and 4096-pixel options; it did not mandate 1024. The earlier square-core results and QA records are preserved.

## Current default

`config/processing.json` now selects `core_mode: native_tile`. Dimensions are read from the metadata of the tile containing the configured study centre. For the supplied dataset, this is:

- Core/output: **1500 columns × 1200 rows**, or **750 × 600 m** at 0.5 m.
- Buffered input: **5500 columns × 5200 rows**, or **2750 × 2600 m**.
- Buffer: 2000 pixels = 1000 m on **each** side.
- Workers: 1.

A native-tile output is one spatial task. That task reads its buffered DSM once and computes the required azimuth horizons within the task. There are still 27 date-independent direction cache entries for this daylight run; this is not a reduction to one shade value per tile.

Larger custom outputs are divided into rectangles with the same native-tile dimensions, with partial cores at the requested boundary. Their existing exact-centre target grid is preserved. Therefore a custom core has the native tile's dimensions, but its boundary need not coincide with the edges of original source files. Original files remain a separate read-only data inventory.

`--core-size 2048` is still an explicit alternative: it selects a **2048 × 2048** maximum square core. Both 1500 and 1200 fit under their respective 2048 limits. It does not mean a maximum of 2048 total pixels. A 1500 × 1200 image has 1,800,000 pixels; a 2048 × 2048 square can hold 4,194,304. Square-2048 mode would process the current native output in one task, but would use different work-unit dimensions for larger outputs, so it is not the requested default.

## Overlap and ownership

1. Core rectangles have non-overlapping, half-open row/column ranges. Every requested output pixel has one owner.
2. Each core is expanded by 1 km on every side to read actual neighboring DSM data. Adjacent tasks can read the same source elevations. For equal-height east/west adjacent cores, their buffered input windows overlap by 2 km horizontally, because both extend 1 km across the shared boundary.
3. The horizon calculation evaluates only targets in the owning core, using surrounding input elevations for obstructions. Horizontal search remains capped at 1 km, including diagonal and distance-limit sampling rules.
4. Each task saves only its core. No halo labels are written into another task's output, and no binary labels are averaged or blended.
5. The whole requested output shares one grid, solar parameters and uncertainty threshold. Global-address sampling and bounded source-window reads are unchanged. Missing DSM remains unknown, including inside an overlap.

## Verification

**26 tests pass.** Added checks establish metadata-derived rectangular units, exactly one task for a native tile, unique output ownership across neighboring native-sized tasks, overlapping input windows, preservation of fractional custom-grid origins, and the per-axis interpretation of a 2048-pixel limit. Existing edge/corner/NoData/low-sun equality tests now also exercise rectangular cores, including odd offsets.

A real 900 × 700 m custom region was tested with 1500 × 1200 cores at 115°, 180° and 225°: **zero horizon, support, blocker-distance, binary-label, quality or validity differences** against its single-region 1 km reference. This compares 7,560,000 pixel/direction pairs, with additional classifications at elevations 0.1°, 5°, 20°, 45° and 65°. Evidence: `outputs/chunking_qa_20260928/multi/comparison_1500x1200.json`.

The current full daylight output directory is `outputs/native_tile_unit_1km_20260928/`. The previous four-core output remains at `outputs/native_tile_1km_20260928/`. Source DSM, location, date, resolution, 1 km search, 1 km buffer, shade encoding and NoData policy are unchanged.

## Completed daylight run

The native-unit production run completed **one spatial core** (`0,0,1500,1200`), computing all 27 direction caches and all **65 daylight frames**. Total runtime was **186.17 s**; sampled parent-process peak RSS was **582.62 MB**, task peak **486.69 MB**, and combined parent/video-process peak **1124.19 MB**. These are local measurements, with some QA work running concurrently.

Every native-resolution label, quality flag and validity mask matches the preserved four-core daylight output **pixel for pixel**. The representative JPG is byte-identical. Against the established single-region 1 km references, all 27 directions have **0.0° maximum horizon difference**, and all 65 actual daylight frames have zero label/quality/validity differences. Source identity records also match the preceding run exactly.

Evidence: `outputs/chunking_qa_20260928/native_tile_unit_comparison.json`, `outputs/chunking_qa_20260928/native_tile/comparison_1500x1200.json`, and `outputs/native_tile_unit_1km_20260928/result_inventory.json`. The cache and output arrays use disjoint core ownership; no seam blending was introduced.

Reproduce the selected policy:

```sh
.venv/bin/python -m src.shade_watch --core-mode native_tile
.venv/bin/python -m src.verify_chunking compare --mode native_tile --production outputs/native_tile_unit_1km_20260928
```

The 1 km boundary and missing-data limitations in the main method/QA notes still apply. Changing the spatial work unit does not fill missing DSM or change scientific classification.

## 29 September follow-up

The geometry/solar-centre policy is superseded by [the native mosaic update](NATIVE_MOSAIC_2026-09-29.md). Metrics and comparisons above describe the preserved 28 September runs. New default runs use the selected native tile’s geometric centre, and mosaics use the union’s geometric centre for all tasks.
