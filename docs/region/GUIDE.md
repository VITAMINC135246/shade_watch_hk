# Two-corner region requests — SW-RGN-AC-1.1

Run from the repository root using `.venv`. WGS84 pairs are explicitly
**latitude longitude**; HK1980 pairs are **easting northing**. Corner order is
immaterial. The examples below use the opt-in source view and the existing raw
DSM files; both are exercised in the 1.1 development evidence.

```sh
.venv/bin/python -m tools.region_request plan --crs wgs84 \
  --corner1 22.339 114.262 --corner2 22.341 114.264 \
  --at 2026-01-07T14:31:27+08:00 --auto-source-view \
  --dsm-dir data/raw/dsm/2020/D12.DSM.TIFF \
  --output outputs/region_dev_v1_1_example_wgs84

.venv/bin/python -m tools.region_request write --crs hk1980 \
  --corner1 844701.5 822197.5 --corner2 844713.5 822202.5 \
  --at 2026-01-07T14:31:27+08:00 --auto-source-view \
  --dsm-dir data/raw/dsm/2020/D12.DSM.TIFF \
  --output outputs/region_dev_v1_1_example_hk1980 \
  --directory outputs/region_dev_v1_1_example_requests
```

The `write` directory must be fresh. A successful repeat `plan` may reuse the
same immutable source view. Ordinary `plan` performs no writes or shade work.
With `--auto-source-view`, planning additionally publishes/reuses symlinks under
`outputs/region_views/<hash>/`. It reads raster headers (cached in-process by
path, size, mtime and known auxiliary-file signatures), selects every source
intersecting the engine-defined 1 km halo of any target tile, and has the engine
hash and validate that view. It performs no scientific computation.

Direct planning against the full 3,310-tile raw catalogue hashes about **26 GB
per plan** and is currently rejected by `v1.index_sources` because of four
shifted-origin `14NE15A/B/C/D` tiles. The auto view excludes unrelated inputs;
if any of those four is a required target or halo dependency, planning fails
with the **pending shifted-origin DSM ingestion policy** message. They are never
corrected or silently omitted. Raw data remains read-only.

Daylight dates are Hong Kong calendar dates and remain dates in generated
requests. Use `--date` repeatedly and `--interval-minutes`, for example:

```sh
.venv/bin/python -m tools.region_request plan --crs hk1980 \
  --corner1 844701.5 822197.5 --corner2 844713.5 822202.5 \
  --date 2026-01-07 --date 2026-01-08 --interval-minutes 10 \
  --auto-source-view --dsm-dir data/raw/dsm/2020/D12.DSM.TIFF \
  --output outputs/region_dev_v1_1_dates
```

Choose exactly one of `--at` and `--date`. More than 512 daylight frames are
grouped at complete-date boundaries into several requests. Nothing is
interpolated. If one date alone exceeds 512 frames, choose a larger interval;
the unchanged V1 engine cannot accept that date at the smaller interval.

Python: `plan_region(corner1, corner2, crs="hk1980", instants=[...],
auto_source_view=True, dsm_dir=..., output_dir=...)`, or replace `instants`
with `dates=[...]` and `interval_minutes=10`. `write_region(plan, fresh_directory)`
writes `region_request.json` and budget-admitted `batch_NNNN.json` files. The
sidecar lists geometry once, time groups, per-request plan keys/UTC frames,
source-view identity, residual areas, estimates and qualified request IDs.
Within each batch the engine's request names are `request_NNNN`; the sidecar
qualifies them as `batch_NNNN.json#request_NNNN`, which are globally unique.
Pre-built ShadePlans are used for admission; V2 still performs its own fresh
catalogue validation once per attempted batch. Packing tries the whole batch
first and bisects only after a budget rejection.

Run the emitted files with the existing V2 `plan` / `submit` / `run` commands
([V2 guide](../v2/GUIDE.md)). A single request also has a copyable `v1_command`.
The adapter never starts execution. Use fresh state/output directories for each
scientific request. Keep the written sidecar beside request files, outside engine
output/cache/source directories.

Large spatial requests split only at catalogue-derived native edges, preferring
fewer, larger rectangles. A part can contain interior/edge cells without DSM;
the engine writes Shade 255 / Quality 1 there. A supplied tile, including a
synthetic sea tile in an already-built catalogue, is processed normally. The
adapter does not fill or relabel outputs. The whole rectangle still needs at
least one tile. Rare empty areas that cannot be merged within limits are
retained explicitly in `no_dsm_areas`, with bounds, reason and 255/1 encoding.
Parts plus those areas partition the resolved rectangle exactly. The optional
Python test cap cannot authorize a cut inside an indivisible native cell.
The spatial search is deterministic and prefers coverage before fewer parts;
it does not claim a globally optimal rectangle packing for large domains.

For read-back across emitted batches and residual areas:

```python
from tools.region_request import read_region_window
shade, quality, transform = read_region_window(
    "outputs/region_dev_v1_1_example_requests/region_request.json",
    utc_time="2026-01-07T06:31:27+00:00",
    bounds=(844701.5, 822197.5, 844713.5, 822202.5),
    logical_mosaics=["outputs/your_fresh_state/<batch-id>.logical_mosaic.json"],
)
```

Supply the completed logical mosaics for batches covering the requested window
and instant. A missing required batch is an error, while an explicit residual
returns 255/1. Source rasters are read through the unchanged V2 helper; overlapping
results must agree. Windows must be on the 0.5 m lattice, lie inside the region
and obey the V1 read-area ceiling.

The rectangle uses min/max **projected** corner coordinates in EPSG:2326. A
rectangle drawn in latitude/longitude is not exactly this rectangle. The engine
expands unsnapped bounds to its canonical lattice and both bounds are preserved.
Transformation consistency does not establish absolute geodetic accuracy.
Cost scales with intersecting native tiles and required directions, not rectangle
area: a tiny crop may still require complete native-tile horizons. All engine
science, limits, budgets, cache identities and estimator rules stay in force.
