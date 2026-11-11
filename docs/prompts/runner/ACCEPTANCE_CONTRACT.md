# Runner and local API acceptance contract (D-2)

Contract ID: `SW-RUN-AC-1.0`
Status: frozen 2026-10-29 by user approval. Record this file's SHA-256 before development.
Design: `docs/ui/DESIGN.md` (D-1). Decision record: D-005.

Prerequisites:

- The region adapter (`SW-RGN-AC-1.0` as amended by `SW-RGN-AC-1.1`) is committed and reviewed.
- The WSL2 smoke test (`docs/v3/WSL2_SMOKE_TEST.md`) has been run, or the user has explicitly waived it for development.

The sea view (`SW-SEA-AC-1.0`) is optional at runtime. When no view manifest exists, every sea-related feature degrades gracefully.

## Objective

Provide a headless job runner and a local JSON API. With them, a browser Console (D-3/D-4, written by Claude) and the command line can do the following without hand-written configuration:

- plan shade requests;
- start them as detached, long-running jobs;
- monitor, cancel and resume them, including after a reboot;
- inspect results;
- download results.

All science stays in the accepted engine. The runner only orchestrates V1/V2 and reads their outputs.

## Non-goals

- No change to `src/`. The ten pinned engine files stay identical to `356f611`.
- No new packages in the engine `.venv`. The server uses the standard library plus packages already in `requirements.lock.txt`.
- No authentication, no binding to any address other than 127.0.0.1, no remote or multi-user service.
- No delete or prune endpoints.
- No V3 campaign execution, no territory runs, no edits to `config/v3/`.
- No front-end implementation beyond serving static files from `web/console/` when that directory exists.

## Required design

### 1. Location and commands

Put the code in a new package `tools/runner/`, with tests. Commands run from the repository root with `.venv`:

```
python -m tools.runner serve [--port 8765]
python -m tools.runner plan <request.json>
python -m tools.runner start <plan_id> [--label TEXT]
python -m tools.runner status [<job_id>]
python -m tools.runner cancel <job_id>
python -m tools.runner resume-incomplete
```

### 2. State and storage

The runner writes only:

- under `outputs/runner/`: `plans/<plan_id>.json`, `jobs/<job_id>/job.json`, `jobs/<job_id>/log.txt`, `views/<view_hash>/`;
- the V2 output, state and cache directories that its batches name.

All writes are atomic: write to a temporary file, then rename.

### 3. Source views (performance only)

V1/V2 planning hashes every file in a DSM directory, and the raw catalogue has 3,310 tiles.

- Reuse the region adapter's request-local source views (`SW-RGN-AC-1.1` A3). Do not write a second implementation. A source view is a directory of symlinks to every catalogue tile that intersects the 1 km halo of any target tile.
- A source view must produce exactly the same spatial keys and plan keys as planning against the full catalogue (U05).

### 4. Detached execution

- `start` submits the V2 batches, then launches `python -m tools.runner exec <job_id>` in a new process session (`start_new_session=True`), with output going to `log.txt`.
- Each job records the process's pid and its psutil `create_time`, so a reused pid is never mistaken for the job.
- Stopping the server never stops a job.
- Only one job may be RUNNING at a time. A second start returns HTTP 409.
- `resume-incomplete` resumes every non-terminal job that has no live process, using `src.v2.resume_batch`.

### 5. Planning

Region types:

- `corners`: calls the `SW-RGN-AC-1.1` adapter, including its handling of no-DSM cells;
- `tiles`;
- `point`;
- `bounds`.

Time types:

- `instants`: ISO strings with explicit offsets;
- `daylight`: dates plus an interval, through the adapter's dates mode;
- `date_range`: start, end and interval, expanded to dates; requests over the V1 frame limit are split by date.

Other inputs:

- a catalogue id;
- output switches: `statistics`, `logical_mosaic`, `jpg`, `mp4`;
- `workers` (1–4, default 1).

Planning never runs horizon, frame or media work.

### 6. Results

PNG previews are rendered from the Shade, Quality and Surface GeoTIFFs, never from JPG/MP4.

- **Size.** The longest side is at most `max` pixels: default 2048, hard cap 4096.
- **Fixed palette:**
  - Shade: 0 → #FFFFFF, 1 → #000000, 255 → #9E9E9E.
  - Water (surface class 1): 0 → #CFE3F7, 1 → #0B2A4A.
  - Quality: 0 → transparent, 1 → #7E57C2, 2 → #FFB300, 3 → #26A69A, 4 → #455A64.
- **Surface classes:**
  - With a sea view, they come from the view's `read_surface_window` helper.
  - With the raw catalogue, they are 0 where the DSM is finite and 255 otherwise.
  - Responses state which source was used.

### 7. Safety

- Reject path traversal.
- Serve files only from `outputs/` and `data/processed/`, and only paths that a job, plan or result index references.
- Limit request bodies to 1 MiB.
- Never expose environment variables or arbitrary directories.

### 8. Provenance and wording

Every result-bearing response includes:

- `engine_commit` and `engine_matches_accepted`;
- `policy_pair`, for example `["SW-V1-POLICY-1.0", null]` or `["SW-V1-POLICY-1.0", "SW-SEA-POLICY-1.0"]`;
- `catalogue_id`, plus `view_id` when applicable;
- `disclaimer`, with this exact text: "Engineering result; observational accuracy NOT VERIFIED. Shade is not cooling or ΔT. 255 = uncertain, not shade."

## API (version `runner-api-1.0`)

All requests and responses are JSON. Errors use the shape `{"error": {"code": str, "message": str}}`.

| Method and path | Request | Response (required keys) |
| --- | --- | --- |
| GET `/api/health` | — | `api_version`; `server{started,pid}`; `repo{root,head,engine_matches_accepted,accepted_engine_commit}`; `machine{system,release,wsl,cpu_model,cpu_count,memory_total_gib,memory_available_gib}`; `disk{free_gib}`; `smoke_test{report_path,status}` |
| GET `/api/catalogues` | — | `catalogues[{id,kind:"raw"\|"sea_view",path,tiles,policy_pair,view_id?,accepted?}]` |
| GET `/api/tiles?catalogue=&bbox=minlon,minlat,maxlon,maxlat` | — | GeoJSON FeatureCollection in WGS84; properties `name` and `bounds_hk1980` |
| POST `/api/transform` | `{from:"wgs84"\|"hk1980", points:[[a,b],…]}` (max 1000 points) | `{points:[[x,y],…], transformer}`, using the `src/v1.py` construction |
| POST `/api/plan` | `{region, time, catalogue_id, outputs, workers, label?}` | `plan_id`; `resolved{bounds_hk1980,corners_wgs84,width_px,height_px}`; `tiles[]`; `requests[]`; `batches`; `no_dsm_areas[]`; `direction_jobs{total,cached,missing}`; `frames`; `estimate{wall_seconds_range,peak_memory_bytes,new_disk_bytes,machine,label:"estimate"}`; `warnings[]` |
| POST `/api/jobs` | `{plan_id, label?}` | `job_id`, `state` |
| GET `/api/jobs` | — | `jobs[{job_id,label,created,state,progress{done,total},elapsed_seconds,plan_id}]` |
| GET `/api/jobs/{id}` | — | the job fields, plus `batches[{batch_id,state,tasks,failures}]`, `log_tail[]` and `provenance{…}` |
| POST `/api/jobs/{id}/cancel` | — | `state` |
| POST `/api/jobs/resume-incomplete` | — | `resumed[job_id…]` |
| GET `/api/results/{job_id}` | — | `frames[{index,local_time,utc_time,counts,quality_counts}]`; `grid{width,height,transform,crs}`; `bounds_wgs84{corners}`; `surface_source`; the provenance keys |
| GET `/api/results/{job_id}/frames/{i}/preview.png?layer=shade\|quality\|surface&max=` | — | PNG, with headers `X-Bounds-WGS84` and `X-Bounds-HK1980` |
| GET `/api/results/{job_id}/pixel?frame=&lat=&lon=` (or `&x=&y=` in HK1980) | — | `x`, `y`, `lat`, `lon`, `row`, `col`, `label`, `quality_code`, `quality_reason`, `surface_class`, `tile`, `solar{azimuth_deg,apparent_elevation_deg,direction_deg}`, `threshold_deg` |
| GET `/api/results/{job_id}/stats` | — | Per frame: `land{sunlit,shaded,uncertain}`; `water{…}` (null when there is no surface layer); `nodata` |
| GET `/api/results/{job_id}/files` | — | `files[{kind,path,bytes,sha256}]` and download URLs |

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| U01 | Traceability; engine untouched | Starting SHA and contract hash recorded. `git diff <start>..<candidate> -- src/` is empty. The pinned files equal `356f611`. |
| U02 | Dependencies and binding | No change to `.venv` or `requirements.lock.txt`. The server binds 127.0.0.1 only, and a test proves it is not reachable on other interfaces. |
| U03 | API conformance | Automated tests, using a small fixture catalogue, validate the required keys and types of every endpoint against this table, plus the error shapes for bad input. |
| U04 | Planning is non-computational | Instrumentation shows zero horizon, frame and media calls during `/api/plan`. The only writes are under `outputs/runner/plans` and the source views. |
| U05 | Source views preserve identity | For 3 regions (coastal, inland, across a tile corner), spatial keys and V1 plan keys from the view equal those from the full catalogue. The view contains every halo dependency. |
| U06 | Detached execution and recovery | A job survives a server restart. A job process killed mid-run is completed by `resume-incomplete`, and V2 counters show completed horizon tasks were not recomputed. |
| U07 | Concurrency and cancel | Starting a second job while one runs returns 409. Cancel reaches a truthful terminal state. Unrelated processes are untouched. |
| U08 | Results correctness | Preview size, palette and bounds headers match the spec. At least 200 random pixels, including tile seams, return the same values through `/pixel` as a direct GeoTIFF read. Stats separate land and water whenever a surface layer exists. |
| U09 | Safety | Traversal, out-of-root, oversized and malformed requests are rejected. No delete endpoint exists. |
| U10 | Provenance and wording | Every result-bearing response carries the provenance keys and the exact disclaimer. |
| U11 | Real bounded run (Mac) | Through the API, run one `corners` request across 2 tiles at 2 instants: plan → start → SUCCEEDED. Shade and Quality equal a direct V2 run of the same request. |
| U12 | Tests, docs, handoff | New tests pass, and the existing suite passes unchanged. `docs/runner/GUIDE.md` covers starting the server on the Mac and on WSL, optional autostart (WSL systemd or Windows Task Scheduler) and recovery. An evidence manifest is provided. The local commit SHA is reported. No push. |

## Budgets

- Development: ≤ 20 minutes of real-DSM job wall time, ≤ 8 GiB job memory, ≤ 5 GiB new artifacts.
- New outputs go under `outputs/runner*`.
- Cache namespace: `data/processed/shade_v1/runner_dev`.

## Release

- Every criterion gets a PASS, FAIL or NOT VERIFIED verdict, backed by evidence.
- Review is done by the planning conversation (Claude), which also builds the front end against this API.
- Science does not change, so independent scientific acceptance is not required. Exception: if U01 fails, independent acceptance becomes required.
- Every fix requires a new SHA.
- Not authorized: push, V3, territory runs.
