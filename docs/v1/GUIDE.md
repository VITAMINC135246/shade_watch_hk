# V1 API and command guide

Run from the project directory using the existing `.venv`. Original commands
in the root README continue to use the preserved legacy pipeline. V1 uses
`src.v1` and new `data/processed/shade_v1/` entries. Read [POLICY.md](POLICY.md)
before comparing old results: solar/uncertainty references, parity anchor and
custom alignment are intentionally versioned changes.

## One arbitrary instant

```sh
.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --at '2026-01-07T14:31:27+08:00' \
  --output outputs/v1_example_instant
```

This produces native 1500 × 1200 shade/quality GeoTIFFs, frame status and
`result_index.json`, with exact requested/UTC/HKT timestamps and solar parameters
for each owning native tile. Aware timestamps preserve seconds/microseconds.
Naive ISO datetimes use `--timezone` (default Asia/Hong_Kong); ambiguous or
nonexistent local times need an explicit offset. Dates alone use `--date`.
Two equivalent physical timestamps in the same list are rejected as duplicates.

Location selection, preserving the supplied coordinates:

```sh
.venv/bin/python -m src.v1 query \
  --center-lat 22.34011333333333 --center-lon 114.26332333333333 \
  --at '2024-02-29T06:31:27Z' --output outputs/v1_example_location
```

## Planning and Python API

```sh
.venv/bin/python -m src.v1 plan \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --at '2026-01-07T14:31:27+08:00' --output outputs/v1_example_instant
```

The printed JSON records requested/resolved bounds, canonical references,
dependencies, exact solar conditions, total/missing direction jobs, footprint
limitations, output switches and bounded resource estimates. Planning hashes
input/cache files; it performs zero horizon calls and writes no outputs. It is
not a calibrated full-Hong-Kong duration forecast.

```python
from src.v1 import plan_shade, run_shade

plan = plan_shade(
    tile="11NE10B(e844n822,e845n822).tif",
    instants=["2026-01-07T14:31:27+08:00"],
    output_dir="outputs/v1_example_python",
)
print(plan.resources)
result = run_shade(plan)
print(result.index_path, result.jobs)
```

`ShadeRequest`, `ShadePlan`, `TilePlan`, `Instant` and `ShadeResult` describe the
public interface. The frozen plan validates code and source identities again
at execution; if inputs/code change, make a fresh plan. `on_direction=callback`
on `run_shade` can record completed/reused entries; events also stream into
`direction_events.jsonl`. Do not modify a plan's nested dictionaries.

## Lists, multiple dates and reusable directions

```sh
.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --at '2026-01-07T08:17:23+08:00' --at '2026-01-08T14:31:27+08:00' \
  --output outputs/v1_example_list

.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --date 2026-01-07 --date 2026-06-21 --interval-minutes 360 \
  --output outputs/v1_example_dates
```

Omit `--interval-minutes` for ten-minute daylight sequences. Dates use fixed
Hong Kong daylight reference 22.3 N, 114.2 E; classification still uses each
native tile's reference. The 512-frame cap keeps V1 requests bounded. Files
stream one frame at a time; full-year raster export is outside this version.

Use the same cache with a new date and output directory:

```sh
.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --at '2026-01-08T14:31:27+08:00' \
  --cache data/processed/shade_v1/default \
  --output outputs/v1_example_reuse
```

`computed`, `reused` and `horizon_calls` count actual directional operations;
`final_result_hits` counts validated existing scientific frames in the same
output directory. Changing output composition/date never changes a tile's
scientific cache identity. Needed new directions alone are calculated.
Same-directory reruns require the identical request; use a new directory when
changing it. A damaged/incomplete cache or output is rebuilt after validation.

## Crops, custom extents, selections and optional media

```sh
.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --at '2026-01-07T14:31:27+08:00' --crop 901 701 24 20 \
  --jpg --output outputs/v1_example_crop

.venv/bin/python -m src.v1 query --mode custom \
  --bounds 844700.51 822439.04 844712.5 822449.49 \
  --at '2026-01-07T14:31:27+08:00' --output outputs/v1_example_custom

.venv/bin/python -m src.v1 query \
  --tile '11NE10B(e844n822,e845n822).tif' \
  --tile '12NW6A(e845n822,e845n822).tif' \
  --at '2026-01-07T08:17:23+08:00' --at '2026-01-07T14:31:27+08:00' \
  --jpg --mp4 --output outputs/v1_example_media
```

Bounds are EPSG:2326 metres; resolved edges expand to the native lattice. Instead
of bounds, custom mode accepts paired coordinates with `--width-m/--height-m`.
Tile selection requires a complete rectangle; missing tiles, duplicates and
holes produce errors. A crop changes only output composition. Scientific
caches still cover complete owning native tiles, so a first tiny crop may need
full-tile work; the plan makes this cost explicit. `diagnostic_horizon` in
`src.v1_cache` computes a small canonical window without publishing a cache for
bounded numerical experiments, with the same 1 km search/buffer.

JPG and MP4 are independent, off by default; media timestamps include seconds.
The MP4 streams at 4 fps and is decoded to check frame count. `media/index.json`
records exact frame order/timestamps. Previews cap at 1500 pixels per side and
use nearest labels; authoritative rasters remain at 0.5 m.

The default `nearest5`, candidate `nearest2_5`, and optional `direct` methods
are selectable with `--direction-method`. Direct means unbinned tile-reference
azimuth, not exact physical/subpixel accuracy. Finite bins can miss thin blockers.

One worker is supported. Memory estimates, measured parent/tree RSS, compressed
output integrity and phase timings appear in the index. Requests exceeding the
8 GiB memory/10 GiB artifact profile or 20-million-pixel local-area cap fail
before calculation. A campaign still needs its cumulative budget ledger.
