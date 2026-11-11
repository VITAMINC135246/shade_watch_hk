# Shade maps web page (`web/shade_map/`)

A local, read-only web page with two pages (decisions D-010 Q7 and D-017):

- **Results**: open a `shade_map` run folder, step through frames, view the Shade, Quality and Surface layers, click a pixel to read its three codes, and read the statistics required by [`docs/OUTPUT_CODES.md`](../../docs/OUTPUT_CODES.md). It also shows whole-run summaries and the fill-impact diagnostic when present.
- **New request**: draw a rectangle or type two corners, choose times, and download a region config (`shade-map-region-1.0`) with the commands to plan and run it.

The page starts no computation and writes no file. Run commands yourself. `shade_map plan` is the authoritative check of every estimate shown here.

## Start and stop

From the repository root, with any Python 3:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open <http://127.0.0.1:8765/web/shade_map/>. Stop the server with Ctrl-C.

- The server shares the repository read-only with this computer only (127.0.0.1). It must start from the repository root, because the page reads `outputs/...`, `docs/...` and `web/shade_map/data/...` by path.
- Opening `index.html` as a file does not work; the page then says how to start the server.
- The same command works on macOS, Linux, WSL2 and Windows.
- If port 8765 is busy, use another port in both the command and the address.

## Results page

Address form: `#/results?root=<output_root>&run=<name>&frame=<YYYYMMDD>/<HHMM>&layer=shade|quality|surface`.

**Files read:** `run_manifest.json`, `summary.json`, `<date>/<time>/frame.json`, `<date>/<time>/<layer>/<cell>.tif`, and `<output_root>/_diagnostics/fill_impact/<name>/fill_impact.json`. It never reads JPG or MP4 files.

**Statistics:**

- The groups follow the run's sea policy (`policies.sea` in the run manifest).
  - Raw runs: Land = surface 0; surface 255 is counted only.
  - `SW-SEA-POLICY-2.2`: Land = 0 + 3 and Water = 1 + 2; classes 4 and 255 are counted only.
- Sunlit, shaded and uncertain are shown side by side over the whole group, and uncertain is split by quality.
- Bounds: lower = label / group; upper = (label + uncertain) / group.
- No ratio over valid labels only is computed. An unknown sea policy withholds group statistics.
- Every frame's cross-counts are reconciled with its `value_counts` and `pixel_count`.

**Display:**

- Runs above 16 million pixels are drawn with every Nth pixel (nearest) to stay responsive, and the page says so.
- Statistics and pixel inspection always use every pixel.
- Grey (shade 255) is invalid or uncertain, never shade or sunlight.

## New request page

- **Cell index:** the map shows the native cell lattice from `data/cells.json`. Tan cells have a DSM tile, light cells have none, and red outlines mark the four `14NE15*` tiles that planning rejects within 1 km (D-008).
- **Frame estimates:** these mirror `tools/shade_map/config.py` and `src/solar.py`: daylight from the −0.833° crossing at 22.3°N, 114.2°E, with clock-aligned samples.
- **WGS84 conversion:** WGS84 corners are converted with an approximation (within about 1 m of pyproj); planning uses pyproj.
- **Warnings:** swapped corners, invalid names or times, cells without DSM in raw mode, the northern DSM edge (fill-dependent), enclosed fills (pits), times outside daylight, and dates with more than 512 frames.

## Files

| File | Role |
| --- | --- |
| `index.html`, `style.css`, `app.js` | Shell, styles (adapted from the `web/console/` prototype), hash router |
| `results.js`, `request.js` | The two pages |
| `map.js` | Canvas map in HK1980 metres (adapted from `web/console/map.js`) |
| `tiff.js` | Minimal GeoTIFF reader for the publication format only: classic TIFF, one uint8 band, DEFLATE or none, predictor 1 or 2. Other formats are refused. |
| `codes.js`, `stats.js` | Codes, colours and groups from `docs/OUTPUT_CODES.md`; group statistics and bounds |
| `sun.js`, `hk1980.js` | Port of `src/solar.py` daylight logic; WGS84 ↔ HK1980 approximation |
| `util.js` | Fetch, directory listing of `http.server`, hash state, download |
| `data/cells.json` | Native cell index derived from B2.2 view `8ee51b01…` (manifest SHA-256 `1a7a43bd…1c52`) |
| `make_cells_index.py` | Rebuilds `data/cells.json` from the current view: `python3 web/shade_map/make_cells_index.py` |

There are no external libraries, fonts or network requests. `window.shadeMapResults` is a test hook used by the automated checks.

## Verification (2026-11-09, Claude, on workspace copies of accepted outputs)

This records engineering checks of the page. It is not an acceptance of any scientific result.

- **GeoTIFF reader:** 66 published rasters (118.8 million pixels) from the B2.2 development runs and the F1.0 Cheung Chau run decode identically to rasterio, including transforms and NoData values.
- **Pixel inspection:** 170 points (cell corners and random points) in three runs equal the rasterio values for all three layers.
- **Statistics:** for 7 frames, `frame.json` cross-counts and `summary.json` give identical groups, and the counts reconcile. Two examples:
  - Raw Cheung Chau, 2026-01-07 12:30, Land: 83,092 sunlit, 1,477,090 shaded, 1,762,131 uncertain (quality 2), as in D-009.
  - `sea-2.2` Cheung Chau, 12:30, Land: 1,845,223 sunlit, 1,477,090 shaded, 0 uncertain.
- **Daylight:** sunrise and sunset agree with `src/solar.py` within 1 ms on six dates (including 2028-02-29), and the frame counts at 1- and 10-minute intervals are identical.
- **WGS84 conversion:** six pyproj reference points from `frame.json` are reproduced within 0.85 m.
- **Request configs:** generated configs (daylight, window with a date range, WGS84 instants) validate against `config/schema/shade_map_region.schema.json`.
- **Warnings:** the `14NE15*` rejection and the outside-domain error appear where expected.
- **Browsers:** the page made no request outside 127.0.0.1. It was checked in Chromium at 1440 px and 390 px wide, with no horizontal overflow.
- **Not verified here:**
  - Safari and Firefox;
  - a `plan` run on a generated config (to be run by the user);
  - performance on runs larger than four cells.

## Limitations

- The user interface is in English.
- There is no basemap: cells are drawn from the DSM catalogue only.
- The page shows what was published; it cannot check observational accuracy (NOT VERIFIED).
- Shade is not cooling and not ΔT.
- The 2026-10-30 runner console in `web/console/` is a cancelled prototype (D-010 Q7) and is not used by this page.
