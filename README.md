# Shade Watch HK

Local CPU reconstruction of clear-sky direct-sun obstruction on the supplied CEDD 2020 DSM. **Not yet validated against real-world observations.** The configured tile-selector location, 7 January 2026 simulation date, Asia/Hong_Kong time zone, 10-minute daylight sampling, 5° nearest-direction LUT, and conservative uncertainty rules are preserved.

The default output and spatial work unit are the original DSM tile containing the configured centre: for the current files, **750 × 600 m, 1,500 columns × 1,200 rows, 0.5 m, EPSG:2326**. These properties come from GeoTIFF metadata. This tile is processed as one spatial task, with one buffered DSM read and the required azimuths calculated within that task. The saved location selects the tile; the effective output and shared solar reference use that tile’s geometric centre. The saved location is preserved. Only explicitly requested custom mode changes the placement. The existing exactly centred **600 × 450 m** extent remains available as custom mode.

## Run

Use the existing project environment; no downloads or new dependencies are required:

```sh
.venv/bin/python -m src.shade_watch
.venv/bin/python -m src.shade_watch --config config/mosaic_6tiles.json
.venv/bin/python -m src.shade_watch --output-mode custom --width-m 600 --height-m 450 --output outputs/custom_600x450_1km
.venv/bin/python -m src.shade_watch --output-mode custom --width-m 900 --height-m 700 --workers 1 --output outputs/custom_900x700_1km
.venv/bin/python -m src.shade_watch --output-mode custom --center-lat 22.34011333333333 --center-lon 114.26332333333333 --width-m 600 --height-m 450 --output outputs/explicit_center_1km
.venv/bin/python -m pytest -q --disable-warnings
```

Settings are in `config/processing.json`; location/date remain in `config/study_area.md`. A different grid, date, DSM, or scientific configuration requires a new output directory. Repeating the same command resumes the run, verifies completed caches and scientific outputs, and regenerates presentation files. Do not run two writers against the same output or horizon cache; exclusive locks reject that situation. Old outputs are preserved in `outputs/` and `outputs/600x450/`.

## Three independent spatial concepts

- **Source tiles** are read-only original GeoTIFFs in `data/raw/dsm/2020/D12.DSM.TIFF/`. Only metadata and streamed hashes enter the inventory; at most one source file is open for reading windows (two in the seam audit).
- **Output extent** is the selected native tile, an explicit rectangular collection of native tiles (`native_mosaic`), or a user-sized, exactly centred rectangle. Mosaic filenames are listed in `native_tile_names`; tiles must share dimensions and fill an aligned rectangle without gaps. Native selection includes west/north edges and excludes east/south edges. A shared corner therefore selects the southeast tile. Missing selections, overlapping sources, mixed CRS/resolution, shifted source grids, rotated pixels, and non-metric grids fail explicitly. Different source file dimensions are allowed when their grids are compatible.
- **Computational cores** default to the selected source tile's rectangular dimensions (`core_mode: native_tile`): 1,500 columns × 1,200 rows for this DSM. One native output tile therefore means one spatial task. Native mosaics use one exact source footprint per task. Larger custom outputs use repeated tile-sized cores, clipped at the requested boundary. Each output pixel belongs to exactly one core. The optional `fixed` mode retains independently configured square/rectangular work units for memory tuning.

Custom dimensions must be positive integer multiples of native resolution. Exact-centre custom grids can have a fractional source-grid offset; nearest-neighbour source-cell sampling is applied once by a globally defined mapping. No chunk independently snaps or reprojects. Custom output cores are anchored to that exact-centre output grid; their dimensions match a native tile, but their boundaries need not coincide with original source-file edges.

## Search, buffer, memory, and concurrency

The adopted model uses **1,000 m maximum horizontal search** and **1,000 m of input buffer on every side of every core**. At 0.5 m this is **2,000 pixels per side**. The default 1,500 × 1,200 core therefore reads a 5,500 × 5,200 buffered array (2,750 × 2,600 m). Rectangular corner data never extend the radial search limit. Both nominal sample distance and sampled cell-centre horizontal distance must be within 1 km.

The buffer supplies actual neighboring DSM elevations. Adjacent tasks can read overlapping DSM neighborhoods, but save only their own disjoint cores. No output pixel has two owners, and no binary labels are averaged or blended. Missing coverage remains unknown. A known obstruction can prove shade even across missing data; missing support cannot prove sunlight. The 1 km limit is an adopted model boundary, **not evidence that farther terrain cannot cast shadows**.

The default is one worker and one native-tile-sized rectangular core, as requested after the initial memory benchmarks. The earlier 1,024-pixel choice was an implementation decision, not a requirement of the original brief. `--core-size 2048` explicitly switches to a fixed 2,048 × 2,048 **per-axis** limit; 1,500 and 1,200 both fit, but this is not the same as using 1,500 × 1,200 units throughout larger outputs. `--core-mode native_tile` selects metadata-derived tile dimensions. In fixed-mode JSON, `core_size_px` may be a side length or `[columns, rows]`. See `docs/QA.md` for the earlier square-core trials and the native-unit follow-up. Smaller cores duplicate buffer reads; larger cores use more RAM. Choose worker count only within the configured memory budget; the six-tile example uses 3 workers. Parallel execution first measures one real task and applies 25% headroom, bounds submitted tasks to the worker count, and propagates failures. Memory budget checks are admission estimates, not an OS-enforced hard limit. Each worker has a 32 MiB GDAL cache; no daily LUT or whole-study DSM is held in memory. Thread count in the scientific kernel remains one per worker.

## Results and cache

The six-tile merged example is in `outputs/native_mosaic_6tiles_1km_20260929/` (1500 × 1800 m; 3000 × 3600 pixels). The default single-tile command now targets `outputs/native_tile_geometric_1km_20260929/`. Earlier native-unit and four-core runs remain in `outputs/native_tile_unit_1km_20260928/` and `outputs/native_tile_1km_20260928/`. Each completed run directory contains:

- `shade_20260107_1430_HKT.jpg` and `shade_daylight_2026-01-07_HKT.mp4` (65 daylight frames, 4 fps).
- `rasters/`: native-resolution lossless GeoTIFFs, **1 shaded, 0 sunlit, 255 invalid/uncertain**.
- `quality/`: 0 valid, 1 missing DSM surface, 2 incomplete 1 km support, 3 distant-obstruction sensitivity, 4 solar centre below horizon.
- `png/`: lossless grayscale + alpha labels, with explicit grid sidecars. For outputs over four million pixels these are per-core pieces. GeoTIFF assembly writes disjoint windows and does not require a whole-output array. Sidecars provide each piece's global core address, affine transform and CRS; place pieces at those addresses without blending.
- `result_inventory.json`, `run_definition.json`, `status/`, and `task_events.jsonl`: source identities, target grid, geometric centre / shared solar reference, statistics, quality counts, task status, parameters, timing, measured memory, and output checksums.

Horizon caches live in `data/processed/horizon_cache_1km/`. Keys include source SHA-256 identities (including associated external masks/auxiliary files when present), whole target grid, azimuth spacing, search, buffer, NoData policy, algorithm version and calculation/I/O code hashes; per-direction filenames record the actual bin. Dates and timestamps do not invalidate unchanged horizons. Each core/direction contains known horizon, support, and blocker distance. Completion requires metadata, shape/grid, band content and checksum validation, not mere file existence. Interrupted/failed or corrupt tasks are recomputed; files publish through atomic rename.

Presentations use black shade, white sunlight, and gray invalid/uncertain pixels. Native-tile output is shown at one scientific pixel per display pixel. Larger previews are capped at the configured longest side (default 1,500 pixels) using nearest labels, and explicitly report display resolution. Authoritative scientific rasters keep native resolution. The old `web/` viewer remains a viewer of the preserved historical 600 × 450 m run.

See [six-tile example and centre policy](docs/NATIVE_MOSAIC_2026-09-29.md), [method](docs/METHOD.md), [QA and measured results](docs/QA.md), and the preserved [tiling research](docs/TILING_RESEARCH_2026-09-28.md). The project Git repository tracks code, configuration, tests, and documentation on its `feature` branch. Raster data, caches, environments, and deliverables are excluded by `.gitignore`. Whole-Hong-Kong processing is an architectural capability, not a completed or performance-validated production run.
