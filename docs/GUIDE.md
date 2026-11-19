# Shade Watch HK — operating guide

Status: 2026-11-16, for tag `mac-v1.0`. A Traditional Chinese copy is in [GUIDE.zh-TW.md](GUIDE.zh-TW.md); if the two differ, this English file wins.

This guide takes you from a Mac with the repository to reported numbers. Every computation is started by you; the web page only views results and writes configs.

More detail: [ARCHITECTURE.md](ARCHITECTURE.md) for the design, [OUTPUT_CODES.md](OUTPUT_CODES.md) for codes and reporting rules, [../web/viewer/README.md](../web/viewer/README.md) for the page. The policies are described in the records: [records/v1/POLICY.md](records/v1/POLICY.md) (engine) and [records/sea2/POLICY.md](records/sea2/POLICY.md) (fill).

## 0. What the result is, and is not

- **What it is:** a map of shade (0 sunlit, 1 shaded, 255 invalid or uncertain) per 0.5 m pixel and instant, from a city's DSM, using a 1 km sunward search.
- **What it is not:**
  - not a cooling effect, ΔT or temperature;
  - not observed truth (observational accuracy is NOT VERIFIED);
  - not territory-wide or city-wide coverage.
- **Fill-dependent labels.** With `sea-2.2`, every missing DSM value is filled at 0 m in the city's vertical datum (HKPD for Hong Kong, NAP for Rotterdam). Labels that depend on filled data are model results under that assumption.
- **What 255 means.** 255 is never shade and never sunlight. After filling, it remains only for quality 3 (possible obstruction beyond 1 km at low sun) and quality 4 (sun at or below the horizon).

## 1. Set up a Mac once

1. Work from the repository root with the repository's `.venv` (Python 3.12, `requirements.lock.txt`). macOS is supported. Linux is package C2.0 and not yet verified. Native Windows is not supported.
2. Check that the Hong Kong DSM is at `data/raw/hong_kong/dsm_cedd_2020/D12.DSM.TIFF` (3,310 tiles, about 26 GB). Raw data is read-only; never edit it.
3. Copy `config/machine.example.json` to `config/machine.local.json`, which Git ignores. The fields:
   - `dsm_dir`: the Hong Kong raw catalogue.
   - `sea_profile`: `hk_cedd_2020`.
   - `output_root`: where results are published. The default is `runs/main`. Use a folder directly under `runs/`; the tools refuse folders they did not create.
   - `cache_namespace`: the prefix of the horizon cache for raw runs (default `raw`; the city is appended, for example `raw_hong_kong`). `sea-2.2` runs use a cache tied to the view.
   - `workers`: 1–4. Development used 4.
   - `memory_budget_mb`: 512–12288. The default is 8192.
   - `cities.<city_id>.raw_dir`: the raw folder of each registered city other than Hong Kong.
4. **Build the Hong Kong fill view once** (about 35–40 minutes on the Mac; reads the raw data only):

   ```sh
   caffeinate -dims .venv/bin/python -m shade_watch.fill build
   ```

   - It writes `data/derived/views/<view_id>/` and a pointer. The accepted view is `412eae79…`; rebuilding with the same code, data and libraries reproduces it.
   - `sea-2.2` runs refuse a missing or stale view. Rebuild if the DSM catalogue or its file times change.
   - `caffeinate -dims` keeps the Mac awake.

Every command takes `--machine <file>`; the default is `config/machine.local.json`.

## 2. Open the web page

From the repository root:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8765/web/viewer/>. Keep the terminal open while you use the page, and stop it with Ctrl-C.

## 3. Make a region config

The page writes Hong Kong region configs. You can also write one by hand; the examples are in `config/regions/`.

1. Open **New request**.
2. Draw a rectangle on the map, or type the lower-left and upper-right corners:
   - HK1980 in metres as [easting, northing];
   - or WGS84 as [latitude, longitude].
   - The lower-left corner must be south-west of the upper-right corner. Planning never swaps them.
3. Choose a name: lower case, digits, `_` or `-`. The name is also the output folder. A name used before with different settings is refused, so use a new name.
4. Choose times:
   - **Daylight**: dates (a list, or a range `from..to`) at an interval in minutes. Only sunrise to sunset is computed.
   - **Window**: dates with a start and end clock time. Times outside daylight are dropped.
   - **Instants**: explicit `YYYY-MM-DDTHH:MM` values in the city's local time.
5. Choose the DSM source:
   - `sea-2.2`: the accepted fill policy. Use this unless you need the raw comparison.
   - `raw`: the DSM as published.
6. Read the checks:
   - **Red messages** are errors: the config is not offered, and planning would refuse it.
   - **Amber messages** are warnings to record: the northern DSM edge (Shenzhen side, filled at 0 m), enclosed fills such as reservoirs, times outside daylight.
7. Download the JSON and save it as `config/regions/<name>.json`. The page shows the commands for this config.

Region configs come in two schemas. `shade-map-region-1.0` is for Hong Kong only and defaults to `raw`. `shade-map-region-1.1` names a `city`, accepts `projected` corners and defaults to `sea-2.2`. Use 1.1 for new work outside Hong Kong.

Keep regions small while you learn: a 2×2 block of Hong Kong cells (1.5 × 1.2 km) is about 7.2 million pixels. Measured on the Mac with 4 workers: a 2×2 block for 146 frames took 8–12 minutes when the horizon cache was already filled. These are not predictions.

## 4. Plan (always first)

```sh
.venv/bin/python -m shade_watch plan config/regions/<name>.json
```

`plan` runs no horizon computation. It prints JSON with:

- the snapped bounds, cells and pixels;
- the frames, and the dropped times with their reasons;
- request, batch and direction counts, missing directions, and estimates;
- whether a full image will be written;
- warnings and conflicts.

**Errors** (exit 2, `invalid input:`):

- swapped corners or a bad name;
- a Hong Kong region needing the four `14NE15*` tiles within 1 km (their grid is offset);
- a missing or stale fill view (run step 1.4, or register the city);
- a name already used with different settings.

If the page's estimate and the plan differ, the plan is right.

## 5. Run

```sh
caffeinate -dims .venv/bin/python -m shade_watch run config/regions/<name>.json
```

Or from Python, without a config file:

```python
from shade_watch import shade_map, plan_shade_map
plan_shade_map([820250, 807200], [821750, 808400], "2026-06-21", name="cc_test", crs="hk1980")
shade_map([820250, 807200], [821750, 808400], "2026-06-21", name="cc_test", crs="hk1980")
```

`when` is a date (daylight at 10 minutes) or a time object as in the configs. `crs` is `wgs84` (default), `hk1980` or `projected` (with `city`). `dsm_source` defaults to `sea-2.2`.

- **Resume:** if the run stops (sleep, power, Ctrl-C), run the same command again; it resumes.
- **Where results go:** `<output_root>/<name>/<YYYYMMDD>/<HHMM>/`, with `shade`, `quality` and `surface` (one GeoTIFF per cell, a VRT, and a full image for small regions) and `frame.json`. The run folder also holds `run_manifest.json`, `summary.json` and `summary.csv`. Keep the layer folders next to the VRTs when you move a publication.
- **Work files:** they remain until you prune:

  ```sh
  .venv/bin/python -m shade_watch prune config/regions/<name>.json        # list
  .venv/bin/python -m shade_watch prune config/regions/<name>.json --yes  # delete this run's work folder
  ```

## 6. Measure fill dependence (`sea-2.2` runs)

```sh
caffeinate -dims .venv/bin/python -m shade_watch.fill fill-impact config/regions/<name>.json [--times 0720,1230,1740]
```

**What it does.** It reruns the same frames on the raw DSM (a counterfactual) and compares each pixel. Use `--times` for a subset; the times must be frames of the run.

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

On **Results**, set the output folder (default `runs/main`) or press **Find output folders under runs/ and baselines/**, press **List runs** and choose a run.

The output folder can be any published root inside the repository, for example `baselines/measure_5regions_20261110`. A run can also be opened by address: `http://127.0.0.1:8765/web/viewer/#/results?root=<output folder>&run=<name>&frame=<YYYYMMDD>/<HHMM>&layer=shade`. The page was built for Hong Kong; whether it shows Rotterdam runs correctly is not verified.

- **Map:** step through frames with the slider or the list; switch layers with the buttons.
- **Pixel:** click a pixel to read its shade, quality and surface codes and its tile's sun position.
- **Frame statistics:** groups as defined below, with counts that reconcile with the published files.
- **Whole run:** mean shaded and sunlit bounds per date, and a chart over the day.
- **Fill dependence:** the fill-impact table, if you ran step 6.

The first and last frames of a day often show no sunlit pixels: the sun is still below the tile's distant-obstruction threshold, so pixels that are not shaded stay uncertain. That is the engine's rule, not a counting error.

## 8. Report numbers

Follow [OUTPUT_CODES.md](OUTPUT_CODES.md). In short:

1. **Groups.** For `sea-2.2`, Land L = surface 0 + 3 and Water W = surface 1 + 2. Class 4 and 255 are counted only. For raw runs, Land = surface 0.
2. **Denominator.** It is the whole group. Never use shaded ÷ (shaded + sunlit); it is biased toward shade.
3. **Three items side by side.** Report sunlit, shaded and uncertain together, and split uncertain by quality.
4. **Bounds in prose.** Lower = label ÷ L; upper = (label + uncertain) ÷ L.
5. **Water separately.** Report water apart from land, and say that water labels are less certain (in Hong Kong the 0 m fill is about 1.4 m below the median DSM waterline).
6. **Fill dependence alongside.** Give the fill-dependent Land share next to the main numbers.
7. **Separate statements.** State engineering acceptance, numerical consistency, approximation error, performance, observational accuracy (NOT VERIFIED) and production completeness separately. A regional result is not a territory result.

## 9. Other cities

Hong Kong and Rotterdam are registered (`config/cities/`). A city other than Hong Kong is registered once from its raw sheets.

**Rotterdam.** Put the two sheets `R_37FZ1.tif` and `R_37HN1.tif` in `data/raw/rotterdam/dsm_ahn_05m/` and set `cities.rotterdam.raw_dir` to that folder in the machine config. Then:

```sh
.venv/bin/python -m shade_watch.city register rotterdam
.venv/bin/python -m shade_watch plan config/regions/rotterdam_projected.json
caffeinate -dims .venv/bin/python -m shade_watch run config/regions/rotterdam_projected.json
```

- Registration cuts the sheets into native cells under `data/derived/catalogues/rotterdam/<ingest_id>/` and builds the 0 m NAP fill view (about 2–4 minutes). It prints the `ingest_id`, `view_id` and a report; expect the warning `fill_above_ground`.
- From Python: `shade_map([51.9200, 4.4750], [51.9230, 4.4800], when, name=..., city="rotterdam")`. Frame folders use the city's local dates and clock times (Europe/Amsterdam). A nonexistent local time is invalid; an ambiguous one needs an explicit offset.
- Use `projected` corners (RD New) to reproduce a rectangle exactly across machines.

**Add a city.** Add a city profile in `config/cities/<city_id>.json` (projected metre CRS, 0.5 m, vertical datum, IANA time zone, source line, exact extent, daylight reference within 0.01° of the extent centre, the sheets with byte sizes, SHA-256 and declared NoData), add a fill profile in `config/sea_profiles/` with `h_sea_m` 0.00, set `cities.<city_id>.raw_dir`, and register. The record [records/city/GUIDE.md](records/city/GUIDE.md) gives the full field rules.

## 10. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Page says to open through the local server | Start `python3 -m http.server 8765 --bind 127.0.0.1` from the repository root. |
| Results page lists no runs | Set the output folder to the machine's `output_root`, or use **Find output folders under runs/ and baselines/**. |
| `sea view missing or built from a different catalogue` | Hong Kong: run step 1.4. Other cities: run `shade_watch.city register <city>`. |
| `invalid input` naming `14NE15*` | The region needs the four offset tiles; move the rectangle. |
| Name conflict | Use a new region name; the tools never overwrite a run with different settings. |
| `output_root` refused | Use a folder directly under `runs/` that the tools created or that does not exist yet. |
| Run stopped | Rerun the same `run` command; it resumes. |
| `Unsupported filesystem for V2 local state: nfs4` (Linux) | The repository is on NFS. Move it to a local disk, or, on branch `c2-explore-nfs-switch` only (not accepted), prefix the command with `SHADE_WATCH_ALLOW_NFS=1` and run at most one `run` or `fill-impact` at a time. |

## 11. Limitations

- **Grids.** Only 0.5 m DSMs in a projected metre CRS.
- **Model boundaries.** The 1 km search and the 5° direction bins are model boundaries, not proven accuracy. The approximation error is not quantified.
- **The 0 m fill.**
  - Hong Kong: shade on near-shore water is slightly overstated; enclosed fills (reservoirs, voids) form pits; terrain beyond the DSM edge, including the Shenzhen side, cannot shade Hong Kong targets.
  - Rotterdam: about half of the valid pixels lie below 0 m NAP, so the filled surface can block sunlight from adjacent low ground. Fill-impact measures this dependence but cannot tell false shade from true shade.
- **Quality 3 and 4 stay 255.**
- **Not modelled:** piers, pontoons, boats and tide.
- **Solar position:** the NOAA approximation's accuracy is unverified at Rotterdam's latitude.
- **Observational accuracy is NOT VERIFIED** for Hong Kong and Rotterdam; Rotterdam surface labels are NOT VERIFIED.
