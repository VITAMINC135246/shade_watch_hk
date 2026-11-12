# Shade Watch HK — operating guide

Status: 2026-11-09, written under decision D-017. A Traditional Chinese copy is in [`GUIDE.zh-TW.md`](GUIDE.zh-TW.md); if the two differ, this English file wins.

This guide takes you from a computer with the repository to reported numbers. It uses only accepted tools:

- the engine `SW-V1-POLICY-1.0` (V2, `356f611`);
- `shade_map` F1.0 (`35225fd`);
- the sea policy `SW-SEA-POLICY-2.2` (B2.2, `7707c51`).

You run every computation yourself. The web page only views results and writes configs.

Details live in:

- [`docs/shade_map/GUIDE.md`](shade_map/GUIDE.md) for F;
- [`docs/sea2/GUIDE.md`](sea2/GUIDE.md) and [`docs/sea2/POLICY.md`](sea2/POLICY.md) for B2.2;
- [`docs/OUTPUT_CODES.md`](OUTPUT_CODES.md) for codes and reporting rules;
- [`web/shade_map/README.md`](../web/shade_map/README.md) for the page.

## 0. What the result is, and is not

- **What it is:** a map of shade (0 sunlit, 1 shaded, 255 invalid or uncertain) per 0.5 m pixel and instant, from the CEDD 2020 DSM, using a 1 km sunward search.
- **What it is not:**
  - not a cooling effect, ΔT or temperature;
  - not observed truth (observational accuracy is NOT VERIFIED);
  - not territory-wide coverage.
- **Fill-dependent labels.** With `sea-2.2`, every missing DSM value is filled at 0 m HKPD. Labels that depend on filled data are model results under that assumption.
- **What 255 means.** 255 is never shade and never sunlight. After filling, it remains only for quality 3 (possible obstruction beyond 1 km at low sun) and quality 4 (sun at or below the horizon).

## 1. Set up a computer once

1. Use the repository's `.venv` from the repository root, on macOS or Linux (WSL2 on Windows). Native Windows Python is not supported, because the engine uses `fcntl`.
2. Check that the raw DSM catalogue is at `data/raw/dsm/2020/D12.DSM.TIFF` (3,310 tiles, about 26 GB). It is read-only; never edit it.
3. Copy `config/machine.example.json` to `config/machine.local.json`, which git ignores. The fields:
   - `dsm_dir`: the raw catalogue path.
   - `sea_profile`: `hk_cedd_2020`.
   - `output_root`: where results are published. The default is `outputs/shade_map`. It must be a new or F-owned folder inside the repository or `outputs/`; F refuses foreign folders.
   - `cache_namespace`: the horizon-cache folder for raw runs (`sea-2.2` runs use a cache tied to the view).
   - `workers`: 1–4. Development used 4.
   - `memory_budget_mb`: 512–12288. The default is 8192.
4. **Build the B2.2 sea view once** (about 35–40 minutes on the Mac; read-only on raw data):

   ```sh
   caffeinate -dims .venv/bin/python -m tools.sea2 build --machine config/machine.local.json
   ```

   - It writes `data/processed/dsm_views/sea_fill_v2_2/<view_id>/` and a pointer. The accepted view is `8ee51b01…`, and rebuilding with the same code and data reproduces it exactly.
   - `sea-2.2` runs refuse a missing or stale view. Rebuild only if the DSM catalogue changes.
   - `caffeinate -dims` keeps a Mac awake. Omit it on Linux.

## 2. Open the web page

From the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8765/web/shade_map/>. Keep the terminal open while you use the page, and stop it with Ctrl-C.

## 3. Make a region config

1. Open **New request**.
2. Draw a rectangle on the map, or type the lower-left and upper-right corners:
   - HK1980 in metres as [easting, northing];
   - or WGS84 as [latitude, longitude].
   - The lower-left corner must be south-west of the upper-right corner. Planning never swaps them.
3. Choose a name: lower case, digits, `_` or `-`. The name is also the output folder. A name used before with different settings is refused, so use a new name.
4. Choose times:
   - **Daylight**: dates (a list, or a range `from..to`) at an interval in minutes. Only sunrise to sunset is computed.
   - **Window**: dates with a start and end clock time. Times outside daylight are dropped.
   - **Instants**: explicit `YYYY-MM-DDTHH:MM` values in Hong Kong time.
5. Choose the DSM source:
   - `sea-2.2`: the accepted fill policy. Use this unless you need the raw comparison.
   - `raw`: the DSM as published.
6. Read the checks:
   - **Red messages** are errors: the config is not offered, and planning would refuse it.
   - **Amber messages** are warnings to record:
     - the northern DSM edge (Shenzhen side, filled at 0 m);
     - enclosed fills such as reservoirs;
     - times outside daylight.
7. Download the JSON and save it as `config/regions/<name>.json`. The page shows the commands for this config.

Keep regions small while you learn: a 2×2 block of native cells (1.5 × 1.2 km) is about 7.2 million pixels. Reference timings (development, Mac, 4 workers, cold cache):

- Cheung Chau, 4 cells × 65 frames: about 11 minutes.
- 2 cells × 3 frames: about 1 minute.

These are not predictions.

## 4. Plan (always first)

```sh
.venv/bin/python -m tools.shade_map plan --machine config/machine.local.json config/regions/<name>.json
```

`plan` runs no horizon computation. It prints JSON with:

- the snapped bounds, cells and pixels;
- the frames, and the dropped times with their reasons;
- request, batch and direction counts, and estimates;
- whether a full image will be written;
- warnings and conflicts.

**Errors** (exit 2, `invalid input:`):

- swapped corners or a bad name;
- a region needing the four `14NE15*` tiles within 1 km (D-008);
- a missing or stale sea view (run step 1.4);
- a name already used with different settings.

Compare the plan with the page's estimate. If they differ, the plan is right.

## 5. Run

```sh
caffeinate -dims .venv/bin/python -m tools.shade_map run --machine config/machine.local.json config/regions/<name>.json
```

- **Resume:** if the run stops (sleep, power, Ctrl-C), run the same command again; it resumes.
- **Where results go:** `<output_root>/<name>/<YYYYMMDD>/<HHMM>/`, with `shade`, `quality` and `surface` (one GeoTIFF per cell, plus a VRT, plus a full image for small regions) and `frame.json`. The run folder also holds `run_manifest.json`, `summary.json` and `summary.csv`.
- **Work files and caches:** they remain until you prune:

  ```sh
  .venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/<name>.json        # list
  .venv/bin/python -m tools.shade_map prune --machine config/machine.local.json config/regions/<name>.json --yes  # delete this run's work folder
  ```

## 6. Measure fill dependence (sea-2.2 runs)

```sh
caffeinate -dims .venv/bin/python -m tools.sea2 fill-impact --machine config/machine.local.json config/regions/<name>.json [--times 0720,1230,1740]
```

**What it does.** It reruns the same frames on the raw DSM (a counterfactual) and compares each pixel. Use `--times` to diagnose a subset; the times must be frames of the run.

**Requirements and cost.** It needs a complete `sea-2.2` run of the same config. It costs about as much as a raw run of those frames. It resumes and never writes inside the run folder.

**Output:** `<output_root>/_diagnostics/fill_impact/<name>/` (`fill_impact.json`, `fill_impact.csv` and dependency rasters).

**Dependency codes** for observed and filled targets:

| Code | Meaning |
| --- | --- |
| 0 | Same label without filling |
| 1 | Resolved by the fill (uncertain in the raw run) |
| 2 | Label changed by the fill |
| 3 | Filled target with a label |
| 4 | Still uncertain |

**Fill-dependent Land** = (codes 1, 2 and 3 within Land) / all Land. It is a dependency share, **not** a shade share.

## 7. View the results

On **Results**, set the output folder (the `output_root`), press **List runs** and choose a run.

- **Map:** use the slider or the list to step through frames, and the buttons to switch layers.
- **Pixel:** click a pixel to read its shade, quality and surface codes and its tile's sun position.
- **Frame statistics:** groups as defined below, with counts that reconcile with the published files.
- **Whole run:** mean shaded and sunlit bounds per date, and a chart over the day.
- **Fill dependence:** the fill-impact table, if you ran step 6.

## 8. Report numbers

Follow [`docs/OUTPUT_CODES.md`](OUTPUT_CODES.md). In short:

1. **Groups.** For `sea-2.2`, Land L = surface 0 + 3 and Water W = surface 1 + 2. Class 4 and 255 are counted only. For raw runs, Land = surface 0.
2. **Denominator.** It is the whole group. Never use shaded ÷ (shaded + sunlit); it is biased toward shade.
3. **Three items side by side.** Report sunlit, shaded and uncertain together, and split uncertain by quality.
4. **Bounds in prose.** For example: "Land shaded 44.5 %–44.5 %, sunlit 55.5 %–55.5 %, uncertain 0 % (Cheung Chau, 2026-01-07 12:30, sea-2.2)". Lower = label ÷ L; upper = (label + uncertain) ÷ L.
5. **Water separately.** Report water apart from land, and say that water labels are less certain (the 0 m fill is about 1.4 m below the median DSM waterline).
6. **Fill dependence alongside.** Give the fill-dependent Land share next to the main numbers.
7. **Separate statements.** State engineering acceptance, numerical consistency, approximation error, performance, observational accuracy (NOT VERIFIED) and production completeness separately. A regional result is not a territory result.

## 9. The four-region measurement (your next step)

**Purpose.** Measure how much the results depend on filled data, in typical settings, before deciding on portability work. This replaces the "voids stay 255; 10 % trigger" plan of D-010 Q2: under D-016 voids are filled, so the question is now fill dependence. Whether the numbers are acceptable is your decision.

**Regions** (2×2 native cells each, to keep each run short):

| Region | Corners |
| --- | --- |
| Cheung Chau | `config/regions/cheung_chau.json`: HK1980 [820250, 807200] → [821750, 808400] |
| Central / Mid-Levels | HK1980 [833750, 815000] → [835250, 816200] |
| Dense urban area | Your choice, for example Mong Kok; check the page's warnings |
| Vegetated hillside | Your choice, for example a country-park slope |
| Northern border (recommended) | Your choice, along the Shenzhen River; quantifies the Shenzhen-side fill |

**Times.** Daylight at 10 minutes on the two solstices: 2026-06-21 (81 frames) and 2026-12-22 (65 frames). Put both dates in one config, or make one config per date.

**Source.** `sea-2.2`, then `fill-impact` on all frames.

**For each region and date, record:**

- the mean Land shaded bounds, mean sunlit bounds and mean uncertain share (all quality 3 under `sea-2.2`);
- the same for Water;
- the mean fill-dependent Land share, and its largest frame.

**Budget (rough, unverified).** Each region and date takes about 10–15 minutes for the run, plus a similar time for fill-impact. Five regions on two dates take about 3–5 hours and several GB of caches and outputs. Plan for it, check free disk space first, and keep the Mac awake.

## 10. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Page says to open through the local server | Start `python3 -m http.server 8765 --bind 127.0.0.1` from the repository root. |
| Results page lists no runs | Set the output folder to the machine's `output_root`, or use **Find output folders under outputs/**. |
| `sea view missing or built from a different catalogue` | Run step 1.4 (`tools.sea2 build`). |
| `invalid input` naming `14NE15*` | The region needs the four offset tiles (D-008); move the rectangle. |
| Name conflict | Use a new region name; F never overwrites a run with different settings. |
| Run stopped | Rerun the same `run` command; it resumes. |

## 11. Limitations (summary)

The full lists are in `docs/sea2/POLICY.md` and `docs/shade_map/GUIDE.md`.

- **Hong Kong only.** The phase-1 engine assumes EPSG:2326, a 0.5 m grid and Hong Kong time.
- **Model boundaries.** The 1 km search and the 5° direction bins are model boundaries, not proven accuracy.
- **The 0 m fill:**
  - Shade on near-shore water is slightly overstated.
  - Enclosed fills (reservoirs, voids) form pits.
  - Terrain beyond the DSM edge, including the Shenzhen side, cannot shade Hong Kong targets.
- **Quality 3 and 4 stay 255.**
- **Not modelled:** piers, pontoons, boats and tide.
- **Observational accuracy is NOT VERIFIED.**
