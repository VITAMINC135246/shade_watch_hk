# Shade maps (F1.0)

Use the repository's existing `.venv` from the repository root. No additional
packages are required. This package combines the reviewed A1.1 region adapter
and the accepted V1/V2 scientific engine; it does not change their policies.

## Set up this computer once

Copy `config/machine.example.json` to `config/machine.local.json`, which is already
ignored by git. Set `dsm_dir` to your read-only raw DSM catalogue. Relative paths
are relative to the repository root. The full catalogue currently lives at
`data/raw/dsm/2020/D12.DSM.TIFF`.

`output_root` defaults to `outputs/shade_map`. Choose a new publication root;
F creates an ownership marker there. F refuses existing unmarked roots, foreign
run folders, roots inside `data/`, and roots nested in historical project output
folders. Do not point it at a historical run. Subsequent F runs can share the
same F-owned root. `cache_namespace` names an isolated directory under
`data/processed/shade_v1/`; use a fresh namespace for a cold-cache experiment.

`workers` is 1–4 (default 1); `memory_budget_mb` is 512–12288 (default 8192).
V1's per-request ceiling remains 8192 MiB; a larger machine budget only applies
to V2's total resource admission. A low budget or excessive concurrency can be
rejected by the unchanged engine. `max_output_bytes` is an optional nonnegative
integer guard on estimated published plus working bytes; null disables this
optional guard. Available volume space is still checked.

Machine paths, workers, memory budgets and timestamps do not affect `run_id`.
On resume, F uses the original durable V2 definitions and scheduling settings;
editing the machine's workers does not rewrite an already submitted batch.

## Copy a region, then plan and run

The committed `config/regions/cheung_chau.json` describes the four-cell
Cheung Chau rectangle and 2026-01-07 daylight at 10-minute intervals:

```sh
.venv/bin/python -m tools.shade_map plan --machine config/machine.local.json config/regions/cheung_chau.json
.venv/bin/python -m tools.shade_map run --machine config/machine.local.json config/regions/cheung_chau.json
```

`plan` prints one versioned JSON document. It performs no horizon computation and
writes nothing except the adapter's immutable request-local source view under
`outputs/region_views/`. Its estimates are labelled, with the V2 estimator model
identity and extrapolation status. The output includes snapped bounds, grid,
pixels, cells, frames, dropped times, request/batch/direction counts, full-image
selection, warnings and existing-run status. A conflict is reported in the plan;
`run` rejects it before publication.

Copy that region file to `config/regions/central.json` for a later Central request.
Set a distinct lowercase `name`, change `crs` to `wgs84`, then set `lower_left` and
`upper_right` to your selected **[latitude, longitude]** corners and choose the
simulation date. For `hk1980`, corners are **[easting, northing]** metres. The first
corner must be strictly southwest of the second in both input coordinates and
after projection to EPSG:2326. F never swaps corners. This documentation example
does not authorise a Central computation in the F1.0 development campaign.

Names match `^[a-z0-9][a-z0-9_-]{0,47}$`. Unknown keys, missing required keys,
wrong types and invalid corners are rejected with exit 2 and `invalid input:`.
Corner errors create no source views, work folders or outputs. An adapter
rejection (no intersecting tile, zero area or shifted-origin dependency) uses the
same error convention. Other execution/integrity failures exit 1. Progress goes
to stderr; successful commands print a final JSON document to stdout.

## Three time forms

All clock times are Hong Kong time (UTC+8, no daylight saving). Instants must be
whole minutes. Only sunrise through sunset at the engine's fixed 22.3 N, 114.2 E
reference point is computed; this uses the engine's −0.833° sunrise definition.

```json
{"mode":"daylight","dates":["2026-01-07"],"interval_minutes":10}
```

Daylight is passed to the adapter as dates, so it has exactly the engine's
clock-aligned frames. Dates may instead be an inclusive range:
`{"from":"2026-01-07","to":"2026-01-08"}`. Duplicate dates and more than 366
dates are rejected. Existing V1 frame/area/artifact limits still apply; the
adapter groups whole daylight dates into admitted requests. If one daylight date
cannot fit the engine's 512-frame cap, increase the interval.

```json
{"mode":"window","dates":["2026-01-07"],"start":"12:30","end":"12:50","interval_minutes":10}
```

This requests 12:30, 12:40 and 12:50. The end is included only when it falls on a
step. Equal start and end requests one time; an earlier end is invalid.
`interval_minutes` defaults to 10 and must be an integer from 1 to 60.

```json
{"mode":"instants","instants":["2026-01-07T12:30","2026-01-07T00:00+08:00"]}
```

Only the optional `+08:00` suffix is allowed: seconds, other offsets and duplicate
physical times are invalid. For windows and instants, times outside daylight are
dropped and listed with `outside daylight` in the plan and manifest. An all-night
request produces an empty, complete run with the dropped-time record and no
engine computation. Explicit time lists beyond one engine request are chunked
using the engine's frame limit.

## Read the outputs

The tree is `<output_root>/<name>/<YYYYMMDD>/<HHMM>/`. Each frame contains:

- `shade/<cell>.tif`, `quality/<cell>.tif`, `surface/<cell>.tif`: clipped native
  cells, including cells with no DSM tile. Cell names use the full cell's origin,
  such as `e820250n807800`.
- `shade.vrt`, `quality.vrt`, `surface.vrt`: relative GDAL virtual rasters covering
  exactly the resolved rectangle. Copy the entire `<name>/` folder to move it.
- `shade.tif`, `quality.tif`, `surface.tif`: full images when `full_image` is `auto`
  and the rectangle has at most `v1.MAX_OUTPUT_PIXELS` (20,000,000) pixels. Select
  `never` to omit them. Larger requests remain cell/VRT outputs.
- `frame.json`: times, original per-tile engine solar metadata, file hashes,
  value counts and surface/shade/quality cross-counts.

GeoTIFFs are single-band uint8, EPSG:2326, tiled, lossless DEFLATE at native
0.5 m resolution. Shade uses 0 sunlit, 1 shaded, 255 invalid or uncertain and
NoData 255. Quality has no NoData sentinel: 0 valid, 1 missing target DSM,
2 incomplete 1 km sunward support, 3 distant-obstruction sensitivity,
4 nonpositive apparent solar-centre elevation. Surface is 0 DSM-observed,
255 no surface (NoData 255); 1 is reserved for future policy-filled water and is
not emitted by F1.0's raw source. Surface is repeated in every frame.

`region_config.json` is the normalised portable config. `run_manifest.json`
records the canonical identity, contract, tool commit/dirty flag, engine hashes,
source names/content hashes, policies, sidecar hash, batches, machine/library
record, files, progress, timings and prune status. Absolute paths occur only in
the machine record. The manifest's file table hashes every other published file;
its own canonical integrity digest excludes its `integrity_sha256` field to avoid
a self-referential byte hash. Frame records similarly hash their layer files.

`summary.csv` is long format: `date,time,utc,surface,shade,quality,pixels`.
`summary.json` reports sunlit/shaded/uncertain counts and fractions plus quality
counts for each surface class in every frame. Fractions use the **whole surface
class** as denominator, including its uncertain pixels. There are no fractions
conditioned only on valid pixels.

## Resume and prune

Run the identical command again to resume. A name with a different normalised
region or source identity is a conflict; choose a new name. A name lock prevents
concurrent publication. Completed V2 batches are never resubmitted. Incomplete
batches resume through V2. Published frames are hash-checked and retained. A
`.partial` frame is removed and rebuilt; a verified renamed frame interrupted
before its manifest update is recovered. Engine work stays under
`outputs/shade_map_work/<name>-<run_id12>/` until explicitly pruned.

```sh
.venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/cheung_chau.json
.venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/cheung_chau.json --yes
```

Without `--yes`, prune lists files and sizes. With it, prune deletes only this
run's ownership-checked work folder, after every published frame and hash has
been verified. It retains published files, source views and horizon caches. A
later complete `run` verifies and does nothing. Hash corruption is an integrity
failure, not a licence to overwrite a published frame.

## Python

```python
from tools.shade_map import shade_map, plan_shade_map

plan = plan_shade_map([22.2,114.0], [22.201,114.001], '2026-01-07',
                      name='my_region', machine='config/machine.local.json')
# Use only an authorised region/scope when executing:
# result = shade_map(...same arguments...)
```

A bare date means daylight; a dict is the region config's `time` object. The
keyword arguments are `name`, `crs='wgs84'`,
`machine='config/machine.local.json'`, `dsm_source='raw'`, `full_image='auto'`.
The running API writes `region_config.json`, which can be given directly to the
CLI. Planning and running share their validators and implementation with the CLI.

## Limitations

In F1.0, sea and other DSM NoData remain **255**, so coastal land is often
Quality 2. In the reference Cheung Chau run, **53.0% of land was Quality 2 at
12:30**. **255 is not shade.** The raw provider does not fill sea or infer cooling.

Regions needing any of the four `14NE15*` shifted-origin tiles are rejected until
an ingestion policy exists; F does not correct or omit a required dependency.
Time and size estimates are not guarantees. A tiny crop can require full native
tile horizons and the 1 km halo. A WGS84 two-corner rectangle resolves to the
projected rectangle, with engine snapping preserved. Current orchestration and
locks support the existing local environment; native Windows is outside F1.0.

Engineering acceptance is not observational accuracy. Observational accuracy
remains NOT VERIFIED. Shade is not cooling and not ΔT. This package authorises
neither territory-scale computation nor V3, sea filling, downloads or web work.
