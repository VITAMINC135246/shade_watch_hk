# Output codes and reporting rules

Status: planning record, written 2026-11-05 under decisions D-009, D-015 and D-016 (`docs/planning/DECISIONS.zh-TW.md`). It defines the codes in `shade_map` publications and B2 sea views, and how to count them. It is not acceptance evidence.

## Where the codes appear

Every published frame folder `<output_root>/<name>/<YYYYMMDD>/<HHMM>/` holds three uint8 layers, each as one GeoTIFF per native cell plus a VRT (and a full image for small regions): `shade`, `quality` and `surface`. **The same number means different things in different layers.**

## `shade` (engine output, `SW-V1-POLICY-1.0`)

| Code | Meaning |
| --- | --- |
| 0 | Sunlit. The target has a height; no obstruction was found in the 1 km sunward search; that support is complete; and the apparent solar elevation is strictly above the tile's distant-obstruction threshold. |
| 1 | Shaded. A finite known horizon strictly greater than the positive apparent solar elevation was found in the available data. Equality is not shade. |
| 255 | Invalid or uncertain. **Not shade, and never to be read as sunlit.** This is the GeoTIFF NoData value. |

## `quality` (engine output)

| Code | Meaning |
| --- | --- |
| 0 | Valid. The shade label is 0 or 1. Quality is 0 if and only if shade is 0 or 1. |
| 1 | Missing target DSM. Rarely also a target that has a height but no finite horizon, because classification requires a finite horizon. |
| 2 | No obstruction found, but the 1 km sunward support is incomplete. |
| 3 | No obstruction found and support complete, but the apparent elevation is not above the tile's distant-obstruction threshold (sensitivity to obstructions beyond 1 km). |
| 4 | Apparent solar-centre elevation ≤ 0. The label is 255 even if a blocker exists. |

Source: `src/shade_watch.py::classify` and `docs/v1/POLICY.md`. The quality layer has no GeoTIFF NoData value.

## `surface` (source provider output)

The meaning depends on the run's sea policy. Read `policies.sea` in the run manifest (`run_manifest.json`).

### Raw runs (`policies.sea` = `none`; package F1.0)

| Code | Meaning |
| --- | --- |
| 0 | DSM-observed surface. |
| 255 | No DSM value. Sea, land voids and empty cells are **not distinguished**. GeoTIFF NoData value. |

These codes are unchanged from the accepted F1.0 (`35225fd`).

### Sea-filled runs (`policies.sea` = `SW-SEA-POLICY-2.2`; package B2.2)

| Code | Meaning | Group |
| --- | --- | --- |
| 0 | DSM-observed surface. | Land |
| 1 | Labelled water, filled at h_fill, inside a supplied DSM tile. | Water |
| 2 | Labelled water, filled at h_fill, inside a synthetic tile (a cell with no DSM tile). | Water |
| 3 | Enclosed NoData, filled at h_fill: land voids and enclosed inland water such as reservoirs (the two are not distinguished). | Land |
| 4 | Open NoData not labelled water, filled at h_fill. | Other |
| 255 | Outside the sea view's domain. GeoTIFF NoData value; not expected inside published regions. | — |

- Every filled pixel holds h_fill, which is the profile's `h_sea_m` (0.00 m HKPD for `hk_cedd_2020`). The label rule decides only the class (1 and 2 versus 3 and 4), never the height.
- NoData is defined literally as a non-finite value or −9999. The four `14NE15*` tiles declare float32-minimum as NoData instead. Their pixels are therefore treated as observed (class 0) and are not filled. Regions that need these tiles are rejected (D-008).

### Superseded: `SW-SEA-POLICY-2.0` (B2.0 candidate `5744e23`, never accepted)

Class 254 meant open NoData left unfilled, and class 255 meant enclosed NoData left unfilled. Do not mix these outputs with sea-filled 2.2 outputs.

## Groups for statistics

| Run policy | Land L | Water W | Other |
| --- | --- | --- | --- |
| Raw | surface 0 (voids cannot be separated from sea) | — | 255: count only |
| `SW-SEA-POLICY-2.2` | surface 0 and 3 | surface 1 and 2 | 4: count only; 255: count only |

## Reporting rules (D-009, D-015)

1. The denominator is the whole group (L or W), never only the pixels with a valid label.
2. Report sunlit, shaded and uncertain side by side. Split uncertain by quality code.
3. When a single shade fraction is stated in prose, give bounds: lower = shaded / |L|, upper = (shaded + uncertain) / |L|. Do the same for sunlit. Never assign uncertain pixels to either side.
4. Do not use shaded / (shaded + sunlit). It is biased toward shade (see the next section).
5. Report water separately from land, and state that labels on water targets are less certain: h_fill is about 1.4 m below the median DSM waterline in Hong Kong, so shade on near-shore water is slightly overstated.
6. For sea-filled runs, where the fill-impact diagnostic has been run, report how much of the result depends on filled data, separately from the main counts.

## Why the classification is asymmetric

- Data that the engine cannot see can only raise a horizon. A found obstruction stays valid when more data appear, so shade is proven within the model even when support is incomplete.
- Sunlight can be overturned by unseen terrain. It therefore needs complete support and an elevation above the distant-obstruction threshold.
- Consequence: pixels with quality 2 or 3 are all "no obstruction found, not confirmed", and they lean sunlit. A ratio over valid pixels only overstates shade.
- The engine is not changed (D-015). The asymmetry is handled by reporting rules 1 to 4.

## Filled-data exception to the 255 rule (D-016)

Pixels that were 255 because data were missing can become 0 or 1 under a versioned fill policy (`SW-SEA-POLICY-2.2` onwards). These labels are model results computed on a filled DSM, and they count as valid, provided that:

- the fill is marked in the surface layer;
- results that depend on filled data are reported separately wherever they have been measured (fill-impact diagnostic);
- observational accuracy is stated as NOT VERIFIED.

A 255 that remains after filling (quality 3 or 4) is still uncertain and is never reclassified.

## Diagnostic codes: fill-impact dependency raster (not a published result)

Written by `python -m tools.sea2 fill-impact` from a sea-filled run and a raw counterfactual of the same frames.

| Code | Meaning |
| --- | --- |
| 0 | Observed target (surface 0) with the same label without filling: independent of the fill. |
| 1 | Observed target that is uncertain (255) without filling and labelled 0 or 1 with filling: resolved by the fill. |
| 2 | Observed target labelled without filling that gets a different label with filling. |
| 3 | Filled target (surface 1 to 4) with a 0 or 1 label: the label exists only because the target was filled. |
| 4 | Uncertain (255) in the sea-filled run. |
| 255 | Not computed. GeoTIFF NoData value. |

## G1 city metadata

Publication format `shade-map-publication-1.1` records the city and vertical
datum in the run manifest. Rotterdam uses 0.00 m NAP. The output codes
above apply on its native EPSG:28992 grid. A plan’s
`fill_context.no_dsm_cells_within_1km` counts native cells without an
unfilled DSM tile in the 1 km dependency area. The warning of the same name
signals a positive count. It describes source coverage before filling.
