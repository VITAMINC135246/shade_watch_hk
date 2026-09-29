# QA — 1 km search, native-tile output and spatial chunks

Current follow-up: [native-tile-sized work units](NATIVE_TILE_UNITS_2026-09-28.md). The report below records the preceding square-core implementation and its verified results.

Verification date: 2026-09-28. **Not yet validated against real-world observations.** These tests establish numerical consistency and bounded execution on the supplied DSM and explicitly artificial automated fixtures. They do not measure photographic or surveyed accuracy. The previous [600 × 450 m report](QA_600x450_legacy.md) and [100 m report](QA_100x100.md) are preserved.

## Inputs and output grid

All 23 previously recorded raw-input/paper SHA-256 hashes match the preceding run (`outputs/chunking_qa_20260928/input_preservation.json`). Original DSM files and historical results were not changed. The configured location remains 22.340113333° N, 114.263323333° E; date remains 2026-01-07, Asia/Hong_Kong.

The metadata-selected native tile is `12NW6A(e845n822,e845n822).tif`: **750 × 600 m, 1,500 × 1,200 pixels, 0.5 m, EPSG:2326**. Bounds are E 845000–845750, N 822200–822800 m. The configured centre (E 845173.471, N 822340.233 m) is inside the tile, not its geometric centre. Native output has 1,111,384 valid DSM surface cells of 1,800,000 (**61.7436% coverage**); buffered coverage is **51.3726%**. Missing cells, including the large eastern part of this tile, remain unknown.

The preserved exactly centred custom grid is 1,200 × 900 pixels, E 844873.4714897–845473.4714897, N 822115.2326670–822565.2326670 m. It intersects four source files and has **98.5668%** DSM coverage. A larger 900 × 700 m custom grid (1,800 × 1,400 pixels) also intersects four files and has **87.5262%** coverage. Both use the documented globally defined nearest-cell mapping from their fractionally shifted target grids.

## Equality to the new 1 km reference

The single-region reference was established first using the **new 1,000 m search and 1,000 m buffer**, not the historical 1,500 m result. Single-region reference GeoTIFFs and machine-readable comparisons are in `outputs/chunking_qa_20260928/{native_tile,custom,multi}/`.

| Output | Core size(s) | Compared directions | Result |
| --- | --- | --- | --- |
| Native tile, 750 × 600 m | 1024 (4 partial/full cores) | All 27 daylight bins, 115°–245° | Exact equality; 48,600,000 pixel/direction pairs |
| Native tile, 750 × 600 m | 513 (9 cores; odd offsets, partial edges) | 115°, 180°, 225° | Exact equality |
| Custom 600 × 450 m | 513 and 1024 | 115°, 180°, 225° | Exact equality for both layouts |
| Custom 900 × 700 m, four source files | 777 and 2048 | 115°, 180°, 225° | Exact equality; 777 creates 6 cores, 2048 provides the single-core control |

Across these comparisons, **horizon, support and blocker-distance differences are zero**, including matching NaN masks; maximum finite horizon difference is **0.0°**. No numerical tolerance was needed. Labels, quality flags and validity masks also have **zero differing pixels** at the additional test elevations 0.1°, 5°, 20°, 45°, and 65°.

All **65 actual native-tile daylight label and quality rasters** were compared with classifications from the single-region references at their actual solar elevations and the same global uncertainty threshold: **117,000,000 output pixels checked**, with zero label, quality or validity differences. A subsequent complete recalculation regenerated all 108 core/direction tasks and final rasters; every scientific output checksum matched the initial completed run.

## Search-distance change, reported separately

A controlled comparison keeps the custom target grid, original 1 km buffered input rectangle, global sampling and 1 km support rule fixed, changing only the search boundary between 1,000 and 1,500 m. This diagnostic does not enable 1,500 m production. The radial eligibility rule also determines whether a rounded cell just outside 1 km belongs to support.

| Local time | Apparent solar elevation | Changed horizons | Maximum horizon change | Changed binary labels | Changed quality flags |
| --- | ---: | ---: | ---: | ---: | ---: |
| 07:10 | 0.9390° | 0 | 0.0000° | 0 | 8 |
| 14:30 | 36.2896° | 724 | 0.4358° | 0 | 0 |
| 17:50 | 0.3489° | 19,412 | 3.1730° | 0 | 0 |

The eight morning quality changes distinguish two uncertainty reasons; the corresponding pixels remain invalid. New labels also match the preserved historical custom outputs at these three times. This is a **three-time sensitivity check**, not a claim that every historical frame or every region is unchanged. Evidence is `outputs/chunking_qa_20260928/distance_change.json`. The 1 km limit remains an adopted model boundary, not proof that more distant terrain cannot cast shadows.

## Automated tests, restart and parallel execution

**24 tests passed** for the original update with the existing environment. The subsequent native-unit follow-up has 26 passing tests (see the follow-up report). Remaining warnings are pending deprecations in Rasterio/Affine interfaces, not test failures. Tests cover:

- Existing solar/time-zone, cardinal-direction, slope, obstruction and NoData behavior.
- Artificial blockers across chunk edges/corners, diagonal rays, partial chunks, missing outer coverage and NoData holes.
- Global ties-to-even sampling with odd chunk offsets; exact-limit and just-beyond-limit obstruction exclusion.
- Metadata-derived tile shape, deterministic boundary ownership, fractional custom-grid sampling, rejection of overlapping/incompatible grids.
- Corrupt/truncated cache repair, incomplete-task restart, wrong identity rejection, external-mask dependency invalidation, protection of unmanaged existing results, exact one-/two-worker equality, and propagation of worker errors.
- Windowed statistics and seam checks; exact single ownership and no blending.
- A clearly synthetic 2051 × 2001 publication fixture, exceeding the full-PNG threshold, verifies native-resolution PNG pieces/sidecars, bounded GeoTIFF assembly, capped previews, and corrupted final-output regeneration.

An actual real-DSM worker was **terminated after publishing one completed direction**, then restarted. The completed file's hash was retained and all three directions matched clean computations exactly (`actual_interruption.json`). A complete production resume reused **all 108 horizon tasks**, finished all checks and presentation generation in **22.34 s**, and recomputed zero horizons (`resume_run_inventory.json`).

Parallelism is implemented with a bounded process pool and verified with two workers on automated fixtures; the production daylight deliverable uses **one worker**. A requested multi-worker production run first measures one real core before admission under the configured budget. No full multi-worker Hong Kong production benchmark is claimed.

## Measured memory and runtime

Values below are sampled process RSS at 20 ms intervals, decimal MB. These are measured allocations, not the smaller DSM-only estimates in the original research note. The three core trials ran in separate fresh processes, used one 225° direction and the actual available DSM; larger core footprints include more missing cells, so their elapsed times are not normalized throughput measurements.

| Core side | Buffered input side | Output pixels in trial | Peak process RSS | Elapsed |
| ---: | ---: | ---: | ---: | ---: |
| 1024 | 5024 | 1,048,576 | 307.25 MB | 4.67 s |
| 2048 | 6048 | 4,194,304 | 417.07 MB | 11.62 s |
| 4096 | 8096 | 16,777,216 | 754.86 MB | 30.44 s |

**1024 pixels and one worker** were the initial default chosen to minimize measured per-task memory. The subsequent user instruction changes the default to one metadata-derived native-tile-sized rectangle; the measurements in this section remain the earlier square-core trial results. Larger cores reduce repeated halo reads but increase memory. The buffer stays 2,000 pixels per side for every core size; worker count multiplies simultaneous buffered tasks. Core size never changes the search radius or pixel-level classification.

With fixed 1024-pixel cores, one direction, and one worker, increasing the output from **1 to 8 cores** raised measured peak RSS from **307.25 to 326.17 MB**, while total output pixels increased eightfold. Much of the enlarged region has missing source coverage, so its 5.47 s runtime is not evidence of fully covered regional throughput. The large arrays are nevertheless allocated at the same fixed task size. Boundary statistics use fixed windows/histograms; final assembly and the large-PNG publication test use bounded windows; preview/video dimensions are capped independently of geographic area. Only the lightweight inventory, disk usage, event records and runtime grow with total work.

The final complete native-tile recomputation, with fresh horizon tasks and regenerated scientific rasters, took **182.84 s**. Peak parent-process RSS was **521.55 MB**; peak simultaneous parent + tracked video encoder/decoder RSS was **1,075.09 MB**. Scientific task peak was **376.00 MB**. The encoder is limited to one thread. The parent-only figure must not be presented as whole-workflow memory: video encoding is a material part of the total. RSS sums include shared pages and can overcount unique physical RAM. The configured budget is admission control, not a hard OS memory ceiling.

Evidence: `benchmark_*.json`, `result_inventory.json`, `initial_run_inventory.json`, `resume_run_inventory.json`, and task events. Some verification calculations ran concurrently with production, so runtime is a measured local observation rather than a hardware-isolated speed claim.

## Deliverables and visual checks

All new required deliverables are in `outputs/native_tile_1km_20260928/`:

- `shade_20260107_1430_HKT.jpg`.
- `shade_daylight_2026-01-07_HKT.mp4`: 65 independently computed frames, 07:10–17:50 HKT, 4 fps, 1840 × 1392 presentation pixels. Calculated sunrise/sunset: 07:03:32.940807 / 17:53:12.612696 HKT.
- 65 native-resolution label GeoTIFFs in `rasters/`, 65 quality GeoTIFFs in `quality/`, and 65 lossless label/alpha PNGs plus grid sidecars in `png/`.
- `result_inventory.json`, `run_definition.json`, task events, per-frame status/checksums, and date-independent horizon cache definitions.

At 14:30: **673,490 shaded**, **437,148 sunlit**, **689,362 invalid/uncertain**. Of the invalid pixels, 688,616 lack target DSM and 746 lack complete sunward support. The global low-sun sensitivity threshold is **23.5605649°**. Labels remain 1 shade / 0 sunlit / 255 invalid; PNG alpha is 255 valid / 0 invalid. Every PNG was roundtrip-compared with its scientific raster before publication.

The JPG and decoded 14:30 video frame were visually inspected: fixed north-up extent, legible time/legend/attribution, black shade, white sun, and explicit gray uncertainty. The native map retains one 0.5 m cell per display pixel. All 65 video frames were decoded; first/last dimensions agree. The representative video's map differs from the lossless rendering by mean absolute RGB **1.264** on an 8-bit scale, 95th percentile **3**, with **0.000889%** of channel values differing by more than 20. This describes presentation compression only, not scientific accuracy. Evidence: `presentation_checks.json` and `decoded_1430.png` in the QA directory.

## Reproduce the checks

From the project root:

```sh
.venv/bin/python -m pytest -q --disable-warnings
.venv/bin/python -m src.verify_chunking reference --mode native_tile
.venv/bin/python -m src.shade_watch
.venv/bin/python -m src.verify_chunking compare --mode native_tile --production outputs/native_tile_1km_20260928
.venv/bin/python -m src.verify_chunking compare --mode native_tile --size 513 --azimuths 115 180 225
.venv/bin/python -m src.verify_chunking reference --mode custom
.venv/bin/python -m src.verify_chunking compare --mode custom --size 513
.venv/bin/python -m src.verify_chunking compare --mode custom --size 1024
.venv/bin/python -m src.verify_chunking reference --mode multi
.venv/bin/python -m src.verify_chunking compare --mode multi --size 777
.venv/bin/python -m src.verify_chunking compare --mode multi --size 2048
.venv/bin/python -m src.verify_chunking distance
.venv/bin/python -m src.verify_chunking restart
.venv/bin/python -m src.verify_chunking benchmark --size 1024
.venv/bin/python -m src.verify_chunking benchmark --size 2048
.venv/bin/python -m src.verify_chunking benchmark --size 4096
.venv/bin/python -m src.verify_chunking benchmark --size 1024 --chunks 8
```

## Remaining limits

This is not a full-Hong-Kong production run. The implementation supports larger compatible target grids through fixed-size work units and streaming assembly; demonstrated correctness covers the areas/directions above, and the larger core benchmarks cover memory behavior only. A citywide run still needs complete DSM coverage, sufficient disk space and substantial ray-scanning time. Inventory adjacency checks are currently pairwise and selection is a linear bounds scan, so a large source catalog may benefit from a spatial tree. Spatially varying solar geometry has not been added. No missing elevations are reconstructed, no farther-terrain safety guarantee is claimed, and the available photo still lacks the registration/weather evidence needed for observational accuracy scores.

## 2026-09-29 native geometric centre and six-tile mosaic

The saved location now selects the native source tile; the effective output and solar reference use its geometric centre. Explicit custom placement remains available. A rectangular six-tile example uses one shared union-centre solar reference and uncertainty threshold, with one exact original source footprint per production task. The previous runs are preserved and retain their original solar reference.

**29 automated tests pass**, including explicit centre overrides, native-centre selection, mosaic source footprints and ordering, duplicate/gap/mixed-size rejection, and both 2-worker and 3-worker equality/failure handling. Existing edge/corner, odd-origin, low-sun, NoData, cache/restart and publication checks continue to pass.

The real example covers 1500 × 1800 m / 3000 × 3600 native pixels with 6 tasks and up to 3 workers. DSM coverage is 10,044,298 / 10,800,000 pixels (**93.002759%**). First-task calibration computed 27 directions in 272.12 s, with peak RSS 472.07 MB. This includes simultaneous independent QA computation and should not be treated as a controlled throughput benchmark.

A separate single-region reference for this limited 10.8-million-pixel example completed directions 115°, 180° and 225° in 172.87 s, peak RSS 856.67 MB. Only the reference deliberately processes the whole example as one task; production remains windowed. The verifier refuses regions above 12 million pixels. See [the six-tile record](NATIVE_MOSAIC_2026-09-29.md) and `outputs/native_mosaic_6tiles_1km_20260929/qa/` for the final comparison and production measurements.


Production completed **65 frames**, confirmed by decoding all 65 MP4 frames, in **1098.90 s**. Peak RSS: parent **508.64 MB**, maximum worker **490.00 MB**, combined production parent/workers/media **1857.39 MB**. Independent QA runs are outside that process-tree measurement. Calibration computed 27 directions; the subsequent scheduler reused those and computed 135 more, totaling 162 core/direction outputs across 6 spatial tasks. The run retained 0.5 m science resolution and used a 1.2 m display preview.

At 14:30, quality counts are 9,538,373 valid; 755,702 DSM NoData; 505,925 incomplete 1 km support; zero other uncertain categories. An additional 215° whole-region reference checks the actual representative-frame LUT bin and its lower outer-coverage gray band. Gray support failures are not converted into sunlight or hidden through seam blending.


最终数值比对通过：**115°、180°、215°、225° 全范围共 43,200,000 个像素/方向对，horizon、支持标记、遮挡距离均零差异，最大 horizon 差为 0.0°**。在 0.1°、5°、20°、45°、65° 太阳高度下，标签、质量和有效性均零差异；另外比对 8 个实际全天输出时刻（包括 14:30），共 86,400,000 个像素/帧对，标签、质量和有效性同样零差异。包括灰带在内，合体输出与单一区域参考一致。

65 份完整科学 GeoTIFF、65 份质量 GeoTIFF、390 片 PNG 和相应坐标 sidecar、JPG、MP4 均已产出。所有原始 DSM 校验和与运行前及前次单 tile 记录一致；配置位置、日期和其他解析出的原始研究输入也保持一致。证据：`outputs/native_mosaic_6tiles_1km_20260929/qa/comparison.json`。这属于数值一致性验证，尚无实地观测准确率验证。
