# Console ↔ runner request and response details (`runner-api-1.0`)

Status: written by the planning conversation on 2026-10-30, for use with D-2 and D-3.

This file clarifies `SW-RUN-AC-1.0` (`docs/prompts/runner/ACCEPTANCE_CONTRACT.md`). It does not change the contract. Where the contract's table names a key without fixing its inner shape, this file fixes it. The front end (`web/console/`) sends and expects exactly these shapes.

Conventions used throughout:

- Units are metres, degrees and seconds.
- Times are ISO 8601 strings with an explicit offset.
- HK1980 means EPSG:2326.

## POST `/api/plan` — request body

```json
{
  "region": {"type": "corners", "crs": "wgs84", "corner1": [22.2105, 114.0270], "corner2": [22.2010, 114.0350]},
  "time": {"type": "daylight", "dates": ["2026-01-07"], "interval_minutes": 10},
  "catalogue_id": "raw-2020",
  "outputs": {"statistics": true, "logical_mosaic": true, "jpg": false, "mp4": false},
  "workers": 1,
  "label": "Cheung Chau test"
}
```

### `region`, one of:

- `{"type": "corners", "crs": "wgs84", "corner1": [lat, lon], "corner2": [lat, lon]}`
- `{"type": "corners", "crs": "hk1980", "corner1": [easting, northing], "corner2": [easting, northing]}`
- `{"type": "tiles", "tiles": ["<native tile file name>", ...]}`. The tiles must form a full rectangle.
- `{"type": "point", "lat": 22.21, "lon": 114.03}`. Selects the native tile that contains the point.
- `{"type": "bounds", "bounds": [left, bottom, right, top]}`, in HK1980.

### `time`, one of:

- `{"type": "instants", "instants": ["2026-01-07T08:30:00+08:00", ...]}`
- `{"type": "daylight", "dates": ["YYYY-MM-DD", ...], "interval_minutes": 10}`. Dates are Hong Kong calendar days.
- `{"type": "date_range", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "interval_minutes": 10}`. Inclusive; expanded to daylight dates.

### Other fields

- `outputs`: four booleans. Scientific Shade/Quality output is always produced and cannot be switched off.
- `workers`: an integer from 1 to 4.
- `label`: optional, at most 120 characters.

## POST `/api/plan` — response

```json
{
  "plan_id": "pln_…",
  "resolved": {"bounds_hk1980": [l, b, r, t], "corners_wgs84": [[lat, lon], [lat, lon], [lat, lon], [lat, lon]], "width_px": 3000, "height_px": 2400},
  "tiles": ["14NW19B(e820n807,e821n808).tif", "..."],
  "requests": [{"id": "region_0000", "bounds_hk1980": [l, b, r, t], "tiles": ["..."], "frames": 65}],
  "batches": 1,
  "no_dsm_areas": [{"bounds_hk1980": [l, b, r, t], "reason": "no DSM tile in catalogue"}],
  "no_dsm_cells": 3,
  "direction_jobs": {"total": 108, "cached": 0, "missing": 108},
  "frames": 65,
  "estimate": {"wall_seconds_range": [420, 1050], "peak_memory_bytes": 1100000000, "new_disk_bytes": 650000000, "machine": "Mac (calibration)", "label": "estimate"},
  "warnings": ["…plain sentences…"]
}
```

- `corners_wgs84` lists the four corners of the resolved rectangle in this order: top-left, top-right, bottom-right, bottom-left.
- `no_dsm_cells` counts lattice cells inside the rectangle that have no tile in the chosen catalogue (`SW-RGN-AC-1.1` A1). They stay in the output and are computed normally, or read as Shade 255 / Quality 1.

## Jobs

- **`state`** is one of `PENDING`, `RUNNING`, `CANCELLING`, `SUCCEEDED`, `FAILED`, `CANCELLED` or `INCOMPLETE`. `INCOMPLETE` means not terminal and no live process; `resume-incomplete` picks these up.
- **`progress`** is `{"done": int, "total": int}`, counting V2 tasks.
- **`GET /api/jobs/{id}`** adds the following:
  - `batches[{batch_id, state, tasks: {STATE: count}, failures: [{id, kind, error}]}]`
  - `log_tail`: a list of strings, at most 200 lines
  - `provenance`: `{engine_commit, engine_matches_accepted, policy_pair, catalogue_id, view_id, plan_id, request}`
  - `result_available`: a boolean

## Results

- **`GET /api/results/{job_id}`**
  - `frames[{index, local_time, utc_time, counts, quality_counts}]`
  - `grid{width, height, transform: [a, b, c, d, e, f], crs: "EPSG:2326"}`
  - `bounds_wgs84{corners}`
  - `surface_source`: `"sea_view"` or `"raw_dsm_finite"`
  - the provenance keys
  - `disclaimer`
- **`.../frames/{i}/preview.png`**
  - The image covers exactly the result grid's HK1980 bounds, because the grid is axis-aligned in HK1980.
  - Surface layer palette, an addition to contract §6: 0 → #BDB7A8, 1 → #8FB8DE, 255 → transparent.
- **`.../pixel?frame=&x=&y=`** takes HK1980 metres. `lat`/`lon` are also accepted.
- **`.../stats`** returns `frames[{index, land: {sunlit, shaded, uncertain}, water: {sunlit, shaded, uncertain} | null, nodata}]`. Every value is a pixel count; the client derives percentages.
- **`.../files`** returns `files[{kind: "shade"|"quality"|"surface"|"statistics"|"index"|"jpg"|"mp4", frame, path, bytes, sha256, url}]`.
