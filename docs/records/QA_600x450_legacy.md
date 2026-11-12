# QA report — 600 m × 450 m HKUST study, 7 January 2026

**Status: Not yet validated against real-world observations.** This is an internal consistency and visual report for an independent reconstruction. The [previous 100 m report](QA_100x100.md) is retained for comparison.

## Geometry and inputs

The configured centre remains 22.340113333° N, 114.263323333° E (E 845173.471 m, N 822340.233 m in EPSG:2326). The north-up output bounds are E **844873.471–845473.471 m** and N **822115.233–822565.233 m**: exactly **600 m × 450 m = 0.27 km²**, or **1,200 × 900 native 0.5 m pixels**. A 1,000 m buffer on every side makes the input grid 2.6 km × 2.45 km (5,200 × 4,900 pixels). The output has 98.57% source-DSM coverage; the larger input grid has 64.99% coverage.

The same 19 original CEDD GeoTIFF tiles were used. They report EPSG:2326, 0.5 m pixels, and NoData −9999; their supplied metadata records HKPD and acquisition from 20 December 2019 to 2 February 2020. SHA-256 hashes of all 23 source paper/raw files in the new inventory match the preceding run, showing that those inputs were not changed. The new configuration hash reflects the requested scope change. The DSM predates the simulated date, so scene changes remain possible.

## Why the old presentation looked blocky

The preceding result had only 200 × 200 scientific cells for its 100 m square. Its presentation code enlarged those cells to 600 × 600 with nearest-neighbour rendering, showing each cell as a visible 3 × 3 square. The new 1,200 × 900 map is drawn at **one output cell per presentation pixel**, with no enlargement or smoothing of binary labels. At 14:30, the JPG and decoded MP4 frame visibly retain building, road, and canopy outlines without the enlarged-cell grid. The central location is wooded, so its fine canopy texture naturally differs from the supplied dense-urban reference image; widening the study area adds campus buildings but does not change the site or its 0.5 m source data.

## Results and checks

The calculated daylight lasts from **07:03:33 to 17:53:13 HKT**. The MP4 contains **65 independently computed frames** at 10-minute clock times from 07:10 to 17:50 HKT, encoded as H.264 at 4 fps and 1,536 × 1,088 pixels. Its decoded frame count is 65. The 14:30 JPG has the same presentation dimensions. All 65 GeoTIFFs and PNGs passed the run's cross-format checks: EPSG:2326, 900 rows × 1,200 columns, valid labels 0 or 1, explicit NoData 255, and matching PNG label and alpha channels. The quality GeoTIFFs distinguish DSM NoData, incomplete 1 km ray support, and the conservative distant-obstruction flag.

At **14:30 HKT**, 733,501 cells are shaded (black), 330,795 are sunlit (white), and 15,704 are invalid/uncertain (gray), leaving **98.55%** classified. Of the gray cells, 15,479 lack source DSM elevation and 225 lack complete sunward support. Some morning frames have more gray because source coverage is incomplete or the low-sun distant-obstruction sensitivity check applies; gray is never silently relabelled black or white. The threshold for that conservative check is **23.57°**, calculated from the highest buffered DSM cell, lowest output cell, and 1 km distance. It is a warning about unseen distant blockers, not measured evidence of them.

At 14:30, 400 spatially distributed points were sampled for an independent 0.5 m direct-ray numerical comparison; 390 had complete data. The main pixel-centred scan's median absolute horizon difference was **0.00°**, its 95th percentile was **2.95°**, and its maximum was **27.04°**. The rotated-grid baseline's corresponding median and 95th percentile were **0.18°** and **19.34°**. Its binary result differed from the main result for 64,818 of 1,064,269 jointly valid cells (**6.09%**). Large discrepancies are possible at sharp roofs and canopy edges. These comparisons test numerical implementation, not real-world accuracy.

The decoded MP4 map at 14:30 was compared with its lossless presentation frame: mean absolute RGB difference **0.67** on an 8-bit scale, 95th percentile **3**, and only **0.0034%** of channel values differed by more than 20. The MP4 and JPG were visually inspected for fixed extent, north orientation, legend, scale, and time. The local timeline viewer was opened and checked at 07:10 and 14:30, including the 600 m × 450 m map, changing frame counts, pixel totals, and playback control. All nine synthetic tests pass, including a rectangular-grid rotation and a one-pixel-to-one-pixel black/white presentation check.

## Independent photo and limits

The supplied DJI image's XMP exposure is **2026-01-07 06:33:02.040750 UTC**, or **14:33:02.040750 HKT**. A separate simulated raster at that actual time is in `outputs/600x450/validation_capture/`. The photo's ground footprint/control points, independent pixel labels, and weather/cloud record are unavailable, so it does not support a defensible positional match or accuracy percentage. Tree pixels represent canopy tops, not sun beneath them. This remains a clear-sky DSM-surface result and excludes clouds, overhangs, and thermal comfort.

## Local performance

The complete local CPU run took **333.14 s** on this Mac, sampled peak process memory was **903 MB**, and generated files excluding the inventory used **43.78 MB**. These numbers describe this one 0.27 km² run only.
