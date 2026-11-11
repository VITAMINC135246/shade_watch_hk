# Shade Watch HK Console — UI and runner design (D-1)

Status: approved 2026-10-29. Written by the planning conversation (Claude).
Decision record: D-005, which covers roles and schedule.
Prototype: the Claude design canvas "Shade Watch HK Console", four clickable screens, private to the user. The Results screen uses a 25 m downsample of the accepted Cheung Chau V2 run; every other screen uses mock data.

## Purpose

Shade Watch is currently driven by Python APIs, CLIs and JSON configuration. The Console makes the common work self-service:

- choose an area and times;
- see what a run will cost before starting it;
- start the run, watch it, and inspect the results.

It must work for runs that last days on a WSL2 research machine.

The Console is a front end and contains no scientific logic. The accepted engine (V1/V2), the region adapter (`SW-RGN-AC-1.0` + `1.1`) and the sea-view tools (`SW-SEA-AC-1.0`) resolve every request.

### Non-goals

- Public deployment, multiple users, or authentication. The server binds to 127.0.0.1 only.
- Editing scientific parameters beyond the accepted options.
- A physical mosaic of the whole territory.
- Any claim about accuracy, cooling or ΔT.

## Users and settings

**Users**

- **Operator** (the student): plans runs, starts them, resumes them after interruptions, and checks the evidence.
- **Reviewer** (the professor): browses results, compares times, and reads provenance and limitations.

**Machines**

- **Mac:** development and small runs.
- **WSL2 research machine:** long runs. The server runs inside WSL; the user opens `http://localhost:<port>` in a Windows browser.

## Architecture

```
Browser (static HTML/JS, served locally)
   │  JSON over HTTP, 127.0.0.1 only
   ▼
Local API server  ──────────────►  Runner (detached processes)
(tools/runner, Python stdlib)         │  python -m src.v2 run/resume …
   │ reads                            ▼
   ├─ result_index.json, Shade/Quality/Surface GeoTIFFs   V2 state DB per batch
   ├─ DSM catalogues + sea-view manifests                  (outputs/…/state)
   └─ region adapter (tools/region_request) for planning
```

- **Jobs survive the server.** Jobs run in their own process session. Closing the browser or stopping the server never stops a computation, and the API is a thin, restartable view over V2 state.
- **GeoTIFFs are the only scientific source.** The server renders previews from the Shade, Quality and Surface rasters with a fixed palette, and never decodes JPG or MP4.
- **No new dependencies in the engine environment.** The server uses the Python standard library plus packages already locked (rasterio, numpy, pyproj, Pillow).
- **Front-end assets.** Leaflet is vendored as static files. Background map tiles are optional and can be turned off when there is no network.

## Screens

### 1. New run (request builder)

The map sits on the left, the form on the right. The map shows the DSM tile lattice and the target tiles. When a sea view is selected, it also shows sea-fill coverage.

**Region** has four modes; the first is the default:

1. **Rectangle (two corners).** Draw the rectangle on the map, or type two corners in WGS84 or HK1980. The screen then shows:
   - the resolved rectangle in both coordinate systems;
   - the intersecting native tiles (cost scales with these, not with the rectangle's area);
   - any no-DSM areas, with the note that they will read as 255 unless the chosen DSM input covers them.
2. **Tiles:** click native tiles; the selection must be rectangular.
3. **Point:** a latitude/longitude selects the containing tile.
4. **Bounds:** HK1980 left, bottom, right, top.

**Time** has three modes:

- exact instants, each with an explicit time zone;
- a daylight sequence for one or more dates, at a chosen interval;
- a date range plus interval, which is expanded into dates. A preview shows the frame count.

**DSM input:** the raw 2020 catalogue, or an accepted sea-fill view. A sea-fill view is shown with its `view_id` and policy pair.

**Direction method:** fixed to `nearest5`. Other methods appear under "advanced", labelled as not validated.

**Outputs:**

- Scientific Shade + Quality: always on, cannot be switched off.
- Statistics.
- Logical mosaic.
- JPG/MP4 previews: off by default, labelled "presentation only".

**Plan preview.** Pressing "Plan" computes nothing. It shows:

- tiles, plus sub-requests and batches when the rectangle must be split;
- direction jobs, split into cached and missing;
- estimated time, memory and disk as ranges, labelled "estimate" and with the machine named;
- warnings: splitting, budget limits, NoData share, edge-of-data areas.

**Start** asks for confirmation, then opens the job page.

### 2. Runs

A table of jobs with these columns: label, region, times, DSM input, state, progress (tasks done / total), elapsed time, estimated remaining time (labelled as an estimate), and machine.

- Row actions: open, cancel, resume, copy the command line.
- A "Resume all incomplete" button handles recovery after a reboot.
- A health strip shows CPU, RAM, free disk, cache and output sizes, and the engine commit.

### 3. Job detail

- State timeline and per-task counts.
- Failures, with their error text.
- A tail of the log.
- Provenance: request JSON, plan key, batch id, DSM catalogue or view manifest, policy pair, engine commit.

### 4. Results viewer

- **Map overlay** of one frame, with a time slider, play button and frame list.
- **Layers:** Shade (default), Quality reasons, Surface class.
- **Legend:**
  - shaded is black and sunlit is white;
  - uncertain is grey, labelled "not shade — insufficient data";
  - water pixels are tinted blue-black / blue-white, labelled "water: lower confidence".
- **Pixel inspector** (click a pixel): coordinates in both systems, label, quality reason, surface class, tile, solar azimuth and elevation, and the tile's distant-obstruction threshold.
- **Frame statistics:** land and water are always kept separate, reported as land-sunlit, land-shaded and land-uncertain shares.
- **Downloads:** the GeoTIFFs and a CSV of statistics. JPG/MP4 are listed under "presentation previews".
- **Footer:** "Engineering results; observational accuracy NOT VERIFIED. Shade ≠ cooling or ΔT."

### 5. System

- Machine information and the WSL2 smoke-test result.
- Available catalogues and views.
- Disk usage per cache namespace.
- Versions and documentation links.

There is no "delete" button; pruning stays manual.

## Language and wording

The UI is in English, matching the repository; a Traditional Chinese toggle can come later. Wording follows the project red lines:

- "uncertain", never "shade";
- "estimate", never "will take";
- "engineering acceptance", never "accurate".

## Delivery plan

| Step | Owner | Depends on | Output |
| --- | --- | --- | --- |
| D-1 | Claude | — | This design, the clickable prototype, and the D-2 API contract (`docs/prompts/runner/`) |
| D-2 | Codex | Region adapter 1.0 + 1.1 reviewed; WSL2 smoke test run or explicitly waived for development | `tools/runner/`: server, job runner, API, tests |
| D-3 | Claude | D-2 API frozen | `web/console/`: request builder, runs, job pages |
| D-4 | Claude | B accepted (surface layer frozen) | Results viewer in `web/console/`. The legacy `web/index.html` is kept unchanged. |

The front end is developed against a mock server that implements the same JSON shapes as the contract. It is then integration-tested on the Mac and on WSL.
