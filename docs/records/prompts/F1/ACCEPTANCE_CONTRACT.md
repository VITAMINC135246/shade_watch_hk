# Package F1.0 acceptance contract — `shade_map` function and CLI

Contract ID: `SW-F1.0`
Status: frozen 2026-10-31 by user approval. Record this file's SHA-256 before development.
Item codes: `F1-01` to `F1-14` (numbering rule: decision D-011).
Decision records (Claude project, `claude/DECISIONS.zh-TW.md`): D-010 (direction), D-011 (numbering), D-012 (F1.0 details).
Planning-layer review: `claude/reviews/REGION_REVIEW_f5f24ac.md`.

The development prompt and the independent-acceptance prompt both use this contract. Do not weaken any criterion after seeing results. Any change to scope, behaviour or budgets needs a new contract version (`SW-F1.1`, …), agreed before work starts.

## Objective

Deliver the function the project is now organised around:

```
shade_map([lat1, lon1], [lat2, lon2], when)  ->  a folder of GeoTIFFs organised by date and time
```

A user copies one region config, edits the corners and the time, and runs the same command.

F1.0 is an engineering package. It combines accepted and reviewed parts and changes no scientific rule:

- **Planning:** the reviewed two-corner adapter `tools/region_request.py` at `f5f24ac` (packages A1.0 and A1.1).
- **Computation:** the accepted V1/V2 engine pinned at `356f611` (V2 durable batches, resume, logical mosaic).
- **New in F:** configuration, time expansion, the corner rule, publication into the folder layout, manifests, summaries, resumable publication and clean-up.

## Non-goals

- No edit to any file under `src/`, and no edit to `tools/region_request.py`. The ten pinned engine files stay byte-identical to `356f611d7b775ce31006904b80ca31d3c1c484b2`: `src/v1.py`, `src/v1_cache.py`, `src/horizon.py`, `src/solar.py`, `src/spatial.py`, `src/shade_watch.py`, `src/v2.py`, `src/v2_worker.py`, `src/v2_runner.py`, `src/v2_state.py`.
- No change to `SW-V1-POLICY-1.0`, the 1 km search, `nearest5`, the V1/V2 limits, cache keys or the estimator.
- No sea-surface policy. F1.0 uses the DSM as supplied, so sea and other DSM NoData stay invalid (255). Package B2.0 will add a sea source through the interface in design item 6.
- Not part of this package: web pages, territory-wide runs, V3 work, native Windows support, an ingestion policy for the four shifted-origin `14NE15*` tiles, downloads, push.

## Frozen decisions (user, 2026-10-31; D-010 and D-012)

1. **Inputs.** Two corners and a time specification. `lower_left` must be the lower-left corner and `upper_right` the upper-right corner; anything else is rejected as invalid input. Corners are never swapped automatically.
2. **Configuration-driven, two layers.** A machine config, set once per computer, and a region config that is portable and is copied and edited per region. Commands: `plan` and `run`; `run` resumes when re-run. A third command, `prune`, removes engine working files when the user asks.
3. **Time.** Three forms: `daylight`, `window`, `instants`. Default interval 10 minutes. Following the Shade Watch paper, only times from sunrise to sunset are computed. Window and instant times outside daylight are dropped and listed, never computed. Instants must be whole minutes.
4. **Output.** `<output_root>/<name>/<YYYYMMDD>/<HHMM>/` in Hong Kong time.
   - Each frame folder holds three layers: shade, quality and surface. Each layer is one GeoTIFF per native cell plus one VRT.
   - Cells at the rectangle edge are clipped to the rectangle.
   - When the rectangle has at most `v1.MAX_OUTPUT_PIXELS` (20,000,000) pixels, about 5 km², each frame folder also holds one full-rectangle GeoTIFF per layer.
   - A run manifest and a summary are written.
5. **Engine working files** are kept after publication until the user runs `prune`.
6. **DSM source.** F1.0 runs on the raw DSM only (sea not filled). B2.0 will add sea filling as a separate, selectable source.
7. **Acceptance** is independent, in a separate conversation.

## Required design

### 1. Location, dependencies and engine use

- **Where the code lives.**
  - New package `tools/shade_map/`, run as `python -m tools.shade_map`.
  - Tests under `tests/`; documents under `docs/shade_map/`; schemas and example configs under `config/`.
- **Environment.** Runs from the repository root in the existing engine `.venv`. No new packages.
  - The JSON Schema files are normative documentation.
  - The validator is hand-written, and a test proves it enforces every rule in the schemas.
- **Engine APIs only.** F calls:
  - `tools.region_request.plan_region`, `write_region` and `read_region_window`;
  - `src.v2.plan_batch`, `submit_batch`, `status_batch`, `run_batch` and `resume_batch`;
  - `src.v1` constants and helpers, plus `src.solar.daylight_bounds`.

  It never re-implements lattice snapping, partitioning, solar geometry or classification. Engine constants such as `v1.MAX_OUTPUT_PIXELS` and `v1.QUALITY` are read from the module, not copied.
- **Engine directories** follow the engine's own rules:
  - engine outputs and V2 state under `outputs/shade_map_work/<name>-<run_id12>/`, where `run_id12` is the first 12 hex characters of `run_id`;
  - the horizon cache under `data/processed/shade_v1/<cache_namespace>/`;
  - request-local source views wherever the adapter puts them (`outputs/region_views/`).
- **Batch options:** `logical_mosaic=True`, `statistics=False`, and no JPG or MP4.

### 2. Configuration

Both files are JSON. Unknown keys, wrong types and missing required keys are rejected, and the message names the key. The schemas are `config/schema/shade_map_machine.schema.json` and `config/schema/shade_map_region.schema.json`.

**Machine config.** The default path is `config/machine.local.json`; the existing `.gitignore` pattern `config/*local*` keeps it out of git. A committed example lives at `config/machine.example.json`.

| Key | Type and default | Meaning |
| --- | --- | --- |
| `schema` | `"shade-map-machine-1.0"`, required | Format identifier |
| `dsm_dir` | path, required | Raw DSM catalogue; read-only |
| `output_root` | path, default `outputs/shade_map` | Where `<name>/` folders are published. Must not lie inside `data/` or inside an existing folder that F did not create |
| `cache_namespace` | string, default `shade_map_raw` | Engine horizon cache, under `data/processed/shade_v1/` |
| `workers` | int 1–4, default 1 | V2 workers |
| `memory_budget_mb` | int 512–12288, default 8192 | V2 memory budget |
| `max_output_bytes` | int or null, default null | Optional guard on estimated published plus working bytes |

Machine settings never enter the run identity.

**Region config.** One file per region at `config/regions/<name>.json`. A committed example lives at `config/regions/cheung_chau.json`.

| Key | Type and default | Meaning |
| --- | --- | --- |
| `schema` | `"shade-map-region-1.0"`, required | Format identifier |
| `name` | string matching `^[a-z0-9][a-z0-9_-]{0,47}$`, required | Output folder name |
| `crs` | `"wgs84"` (default) or `"hk1980"` | Coordinate system of the corners |
| `lower_left`, `upper_right` | `[lat, lon]` for wgs84; `[easting, northing]` for hk1980; required | Corners |
| `time` | object, required | See design item 4 |
| `dsm_source` | `"raw"`, default and only value in F1.0 | See design item 6 |
| `full_image` | `"auto"` (default) or `"never"` | See design item 7 |

### 3. Corner rule

- **WGS84.** Values must be finite, with latitude in [−90, 90] and longitude in [−180, 180]. Require `lower_left` latitude < `upper_right` latitude, and `lower_left` longitude < `upper_right` longitude.
- **HK1980.** Values must be finite, with x_ll < x_ur and y_ll < y_ur.
- **After projection.** Once projected to EPSG:2326 with the adapter's transformer, the corners must keep the same order; otherwise the input is invalid.
- **On any violation:** exit code 2, print `invalid input: <rule that failed>`, and write nothing.
- The adapter's own checks (zero area, no intersecting DSM tile, shifted-origin dependency) still apply and are reported the same way.

### 4. Time

All clock times are Hong Kong time (UTC+8, no daylight saving). `interval_minutes` is an integer from 1 to 60, default 10, and applies to `daylight` and `window`.

- **`{"mode": "daylight", "dates": D}`**
  - Every frame of the engine's dates mode, for each date: clock-aligned samples from sunrise to sunset at the engine's reference point (−0.833°).
  - F passes `dates` and `interval_minutes` to the adapter unchanged, so the frames equal those of `plan_shade(dates=...)` exactly.
- **`{"mode": "window", "dates": D, "start": "HH:MM", "end": "HH:MM"}`**
  - For each date, the times `start`, `start + interval`, … up to and including `end` when it falls on a step.
  - `end` earlier than `start` is invalid; `start` equal to `end` gives one time.
- **`{"mode": "instants", "instants": ["YYYY-MM-DDTHH:MM", …]}`**
  - An optional `+08:00` suffix is allowed.
  - Any other offset, any seconds, or a duplicate time is invalid.
- **Dates `D`.** Either a list of `YYYY-MM-DD` dates, or `{"from": …, "to": …}` with both ends included. Duplicates are invalid; at most 366 dates are allowed.
- **Daylight rule for `window` and `instants`.**
  - A time is kept only if sunrise ≤ t ≤ sunset on its date, using the engine's `daylight_bounds` at the engine's reference point.
  - Dropped times are listed in the plan output and the manifest with the reason `outside daylight`. They are never computed.
- **Folder names** are `YYYYMMDD/HHMM`, taken from the Hong Kong time, and are unique within a run.

### 5. `plan`

`python -m tools.shade_map plan --machine <machine.json> <region.json>`

- **What it does.** Validates both configs, expands the times, applies the corner rule, and plans through the adapter with `auto_source_view=True`.
- **What it writes.** Nothing, except the adapter's request-local source view (symlinks only).
- **Output.** One JSON document on stdout, with schema `config/schema/shade_map_plan.schema.json` and identifier `shade-map-plan-1.0`. It contains at least:
  - `run_id` and `name`;
  - the resolved bounds, grid size and pixel count;
  - the cell list and the frame list;
  - the dropped times;
  - the numbers of sub-requests, batches and distinct horizon directions;
  - the V2 estimated compute time, with the estimator model's identity;
  - estimated published bytes, working bytes and file count, each labelled `estimate`;
  - whether full images will be written;
  - warnings, such as no-DSM cells inside the rectangle and dropped times;
  - the status of any existing run with this name: `new`, `resumable` (with k of n frames published), `complete` or `conflict`.
- This JSON is the interface for the web request generator, and its schema is versioned.

### 6. DSM-source interface

- **Registry.** A small registry maps each `dsm_source` value to a source provider. A provider supplies:
  - the catalogue directory given to the adapter;
  - a surface-class reader for any aligned window;
  - the cache namespace;
  - the policy pair recorded in manifests (the engine policy, plus a sea policy or `none`);
  - a source identity, used in the run identity.
- **The `raw` provider (F1.0).**
  - Catalogue: the adapter's request-local view of `dsm_dir`.
  - Surface classes: 0 = DSM-observed surface (finite and not −9999); 255 = no surface (DSM NoData, or no tile).
  - Policy pair: (`SW-V1-POLICY-1.0`, `none`).
  - Class 1 is reserved for policy-filled water, which B2.0 will add.
- **No special cases.** Publication code must not branch on the source name. B2.0 must be able to add a source without editing publication code.

### 7. Published layout

```
<output_root>/<name>/
  region_config.json        normalised copy of the region config used
  run_manifest.json
  summary.csv               long format: date, time, utc, surface, shade, quality, pixels
  summary.json
  <YYYYMMDD>/
    <HHMM>/
      frame.json
      shade.vrt   quality.vrt   surface.vrt
      shade/<cell>.tif   quality/<cell>.tif   surface/<cell>.tif
      shade.tif   quality.tif   surface.tif        (full image, only when allowed)
```

- **Cells.**
  - A native cell is 750 × 600 m; the cell lattice is derived from the catalogue.
  - Every native cell that intersects the resolved rectangle gets one file per layer, including cells with no DSM tile.
  - Each file covers the cell clipped to the resolved rectangle.
  - `<cell>` is `e<left>n<bottom>` of the full native cell, in whole metres (EPSG:2326), for example `e820250n807800`.
  - The manifest records each cell's source tile name, or `null`.
- **GeoTIFF format.**
  - Single-band uint8, EPSG:2326, with the window's transform; lossless DEFLATE, tiled.
  - Shade and quality keep the data type and NoData setting of the corresponding engine outputs.
  - Values are unchanged: shade is 0 sunlit, 1 shaded, 255 invalid or uncertain; quality is 0–4 as in `v1.QUALITY`.
- **VRT.** One GDAL VRT per layer per frame. It covers exactly the resolved rectangle and references the cell files by relative path, so a whole `<name>/` folder copied elsewhere still opens.
- **Full image.** Written when `full_image` is `auto` and the resolved rectangle has at most `v1.MAX_OUTPUT_PIXELS` pixels.
- **Surface** is written in every frame folder; its content is the same in every frame.
- **`frame.json`** (`shade-map-frame-1.0`) records:
  - the Hong Kong and UTC times and the folder names;
  - per tile, the solar azimuth, apparent elevation and cache direction as recorded by the engine;
  - every file with its SHA-256;
  - value counts for each layer.
- **`run_manifest.json`** (`shade-map-run-1.0`) records:
  - `run_id` and the contract ID;
  - the normalised region config and its hash;
  - the F tool commit and a dirty flag;
  - the pinned engine file hashes;
  - the policy pair;
  - the source identity (tile names and hashes of the request-local view);
  - the adapter sidecar hash and the V2 batch IDs;
  - the resolved bounds, the grid and the cell table;
  - the frame list with each frame's status, and the dropped times;
  - every published file with its SHA-256;
  - a machine record outside the identity (platform, Python and library versions, workers, memory budget);
  - timings and prune status.

  Published JSON contains no absolute paths, except inside the machine record.
- **`summary.json`.** For each frame and each surface class: counts and fractions of sunlit, shaded and uncertain pixels, with the whole surface class as the denominator (D-009), plus quality counts. Fractions over valid pixels only are not reported.
- **Names and paths.**
  - Only `[A-Za-z0-9._-]` and `/` are used; no colons or spaces.
  - Names are unique when case is ignored.
  - Every published relative path is at most 100 characters.

### 8. `run`, identity and resume

`python -m tools.shade_map run --machine <machine.json> <region.json>`

- **Identity.** `run_id` is the SHA-256 of a canonical document containing:
  - the normalised region config;
  - the expanded frame list;
  - the source identity;
  - the pinned engine file hashes;
  - the policy pair;
  - the publication format version.

  Machine settings, paths and timestamps are excluded.
- **Folder rules.**
  - A new name creates `<name>/`.
  - An existing `<name>/` with the same `run_id` is resumed.
  - An existing `<name>/` with a different `run_id`, or a folder F did not create, is a conflict: exit with code 2 and write nothing.
  - A lock file in the work area prevents two concurrent runs of the same name.
- **Guards.** Before computing, refuse if the estimated published plus working bytes exceed `max_output_bytes` (when set) or the free space on the target volume.
- **Computation.**
  - Submit the adapter's batches to V2 with an isolated state directory inside the work folder.
  - Resume incomplete batches with `resume_batch`, and never resubmit a completed batch.
- **Publication, one frame at a time.**
  1. Write the frame into `<HHMM>.partial/`.
  2. Verify every cell file against `read_region_window`: pixels and transform.
  3. Rename the folder to `<HHMM>/` and record the hashes in the manifest.
- **Atomicity.** Manifest writes are atomic. A `.partial` folder is never treated as complete; on resume it is removed and redone.
- **Re-running a complete run** only verifies hashes.
- **Output and exit codes.** Progress goes to stderr; a final JSON summary goes to stdout. Exit code 0 on success, 2 on invalid input or conflict, 1 on any other failure.

### 9. `prune`

`python -m tools.shade_map prune --machine <machine.json> <region.json> [--yes]`

- `prune` is allowed only when every frame is published and verified.
- **Without `--yes`:** lists what would be deleted, with sizes.
- **With `--yes`:** deletes only this run's work folder, `outputs/shade_map_work/<name>-<run_id12>/`. It never deletes published files, the horizon cache, source views, or anything outside that folder.
- The prune is recorded in the manifest. A later `run` with the same config verifies and does nothing.

### 10. Python API

- **Running and planning.** `shade_map(lower_left, upper_right, when, *, name, crs="wgs84", machine="config/machine.local.json", dsm_source="raw", full_image="auto")` runs. `plan_shade_map(...)`, with the same arguments, plans.
- **`when`** is the region config's `time` object. A bare `"YYYY-MM-DD"` string means daylight on that date.
- **Same code path as the CLI.** The API builds a region config, validates it with the same validator, and follows the same code path as the CLI. Results are identical to running the CLI on the `region_config.json` it writes.

### 11. Documentation

- **`docs/shade_map/GUIDE.md`** covers:
  - setting up the machine config;
  - the Cheung Chau example, and copying it to make a Central config;
  - the three time forms;
  - reading the outputs: layers, codes, VRT, full image, summary;
  - resume and prune;
  - limitations.
- **Also required:** `docs/shade_map/DESIGN.md` and `docs/shade_map/DEVELOPMENT_REPORT.md`.
- **The limitations must state:**
  - In F1.0, sea and other DSM NoData remain 255, so coastal land is often Quality 2. In the reference Cheung Chau run, 53.0% of land was Quality 2 at 12:30.
  - 255 is not shade.
  - Regions that need the four `14NE15*` tiles are rejected until an ingestion policy exists.
  - Time and size estimates are not guarantees.
  - Engineering acceptance is not observational accuracy.
  - Shade is not cooling and not ΔT.

## Authorized computation scope

All runs use new output folders and new cache namespaces. Historical outputs and caches are read-only.

- **(a) Cheung Chau regression.**
  - Region config: `crs` `hk1980`; `lower_left` [820250, 807200]; `upper_right` [821750, 808400]. This is the union of `14NW19B`, `14NW20A`, `14NW19D` and `14NW20C`.
  - Time: `daylight` on `2026-01-07`, interval 10. Source: `raw`. Cold cache.
- **(b) Non-aligned rectangle.**
  - One WGS84 rectangle with fractional corners that crosses a four-cell corner and contains at least one no-DSM cell, at most 4 cells in total. Freeze it in the evidence before running.
  - Times: one `window` that gives 2–3 frames; and one `instants` request with one daylight instant and one night instant (the night instant must be dropped).
  - Also independent V1 custom-bounds references for the same frames, in a separate cache namespace.
- **(c) Interruption tests** on configs the size of (b), with fresh names and fresh cache namespaces.
- **Not authorized:** other regions, territory-scale runs, sea views, V3, edits to `config/v3/`, downloads, web work, push.

## Budgets

| Phase | Real-DSM job wall time | Job memory | New artifacts |
| --- | --- | --- | --- |
| Development | ≤ 60 min | ≤ 12 GiB | ≤ 20 GiB, covering work folders, caches, published outputs and diagnostics |
| Independent acceptance | ≤ 45 min | same | same |

When a budget runs out, the criteria it affects become NOT VERIFIED. Budgets may not be extended.

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| F1-01 | Traceability; engine and adapter untouched | Starting SHA (must contain `f5f24ac`), contract hash, environment and lock file recorded. `git diff <start>..<candidate> -- src/ tools/region_request.py` is empty, and the ten pinned files equal `356f611`. Only task files are committed. |
| F1-02 | Configuration | Schemas present. Tests show the validator rejects unknown keys, wrong types, missing keys, bad names and out-of-range values, covering every schema rule. Two machine configs that differ in paths and workers give the same `run_id`; changing only the corners, or only the time, gives a different one. |
| F1-03 | Corner rule | For both CRSs, tests show that the correct order is accepted. Swapped latitude, swapped longitude, both swapped, equal values, non-finite values and out-of-range values each give exit code 2 and `invalid input` with the specific reason, and write nothing (listings before and after). The projected-order check is tested. |
| F1-04 | Time | `daylight` frames equal `plan_shade(dates=...)` frames exactly, for at least 3 dates including both solstices. `window` stepping, the inclusive end, and rejection of `end < start` are tested. Times outside daylight are dropped and listed. Seconds, other offsets and duplicates are rejected. Date ranges include both ends. Folder names are unique. |
| F1-05 | `plan` and planning equivalence | `plan` writes nothing except the source view (listings before and after). Its output validates against the plan schema and contains every required field; estimates are labelled. For 3 configs (single cell, four-cell corner, rectangle with no-DSM cells), the adapter requests and plan keys F produces equal those from calling the adapter directly with equivalent arguments. A config that needs `14NE15*` is rejected with the documented message. Existing-run status is correct for the new, resumable, complete and conflict cases. |
| F1-06 | DSM-source interface | `raw` is implemented through the registry. A test-only provider over a fixture catalogue, with its own surface classes, produces correct published outputs without any change to publication code. |
| F1-07 | Layout and portability | In (a) and (b), the published tree matches design item 7: every intersecting cell has all three layers in every frame, including no-DSM cells, and edge cells are clipped. Every published path meets the name and path rules. A copy of a run folder at another path opens every VRT and reads identical arrays. |
| F1-08 | Pixel equality | For every published frame of (a) and (b): each cell file equals `read_region_window` over its window (shade, quality and transform); each VRT, read over the resolved rectangle, equals the logical window; each full image equals it too; surface equals the classes derived directly from the DSM. Data type, CRS and NoData are as specified. |
| F1-09 | Cheung Chau regression | Run (a) produces exactly the 65 frames (07:10–17:50 HKT) of the reference run `outputs/v2_daylight_cheungchau_20261009` (read-only; produced by the accepted V2 engine). Every published shade and quality pixel equals the reference. Before running, compare the request-local source view's tile list with the reference run's `source_view/`; if they differ, report both lists and stop for a decision. Any differing pixel is a FAIL. |
| F1-10 | Non-aligned rectangle | In run (b), the per-cell outputs equal the independent V1 custom-bounds references pixel for pixel. No-DSM cells read shade 255, quality 1 and surface 255. The night instant is dropped. |
| F1-11 | Resume and conflicts | Kill `run` with SIGKILL once during computation and once during publication, then re-run. The published files are hash-identical to those of an uninterrupted run, and completed V2 tasks and published frames are not redone (V2 reuse counts, manifest). No `.partial` folder survives. The same name with a different config exits with code 2 and writes nothing. A concurrent second `run` is refused. |
| F1-12 | Manifest, frame records, summary, prune | Records validate against their schemas, and every manifest hash matches its file. For every frame and layer, value counts sum to the pixel count, and summary counts match the rasters. Fractions use whole-class denominators. `prune` refuses on an incomplete run; on a complete run it deletes only the work folder, and a following `run` verifies and does nothing. |
| F1-13 | Scope, resources, write scope | Listings before and after show no writes to `data/raw/`, to existing namespaces under `data/processed/`, or to existing `outputs/` folders. Only authorized runs were executed. The ledger of real-DSM job time, peak memory and disk use is within budget. |
| F1-14 | Tests, docs, handoff | Automated tests on synthetic fixtures; the full existing suite passes unchanged. GUIDE, DESIGN and DEVELOPMENT_REPORT are present, and the GUIDE states every required limitation. Example configs are committed. An evidence manifest is present. One local commit, full SHA reported, no push. |

## Decisions and release

- **Marking.** Each of F1-01 to F1-14 is marked PASS, FAIL or NOT VERIFIED, with evidence paths and commands.
- **Acceptance.** F1.0 is accepted only if every criterion passes in a separate independent-acceptance conversation.
- **What acceptance means.** Engineering acceptance and numerical consistency with the accepted engine. It does not establish observational accuracy, which stays NOT VERIFIED, and it changes no scientific conclusion of V1 or V2.
- **What acceptance does not authorize:** territory runs, V3 execution, sea filling, web work or a push. Adding a new source (B2.0) needs its own contract.
- **Fixes.** Each fix needs a new commit SHA and targeted re-acceptance. Failure evidence is preserved.
