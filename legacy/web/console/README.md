# Shade Watch HK Console (`web/console/`)

A browser front end for the local runner API (`runner-api-1.0`, contract `SW-RUN-AC-1.0` in `docs/prompts/runner/`). Request and response shapes are fixed in `docs/ui/API_REQUEST_SCHEMA.md`.

The console contains no scientific logic:

- the engine, the region adapter and the sea-view tools resolve every request;
- the page only plans, starts, monitors and displays runs;
- previews come from the server, which renders them from the Shade, Quality and Surface GeoTIFFs.

The legacy viewer `web/index.html` is separate and unchanged.

## Files

| File | Role |
| --- | --- |
| `index.html` | Page shell |
| `style.css` | Styles. No external fonts or network; IBM Plex is used if installed. |
| `app.js` | Hash router and the four pages: `#/new`, `#/runs`, `#/jobs/<id>` and `#/results/<id>` |
| `api.js` | Thin client for `/api/*`. Add `?mock` to the URL to use `mock.js` instead. |
| `map.js` | Canvas map in HK1980 metres: DSM tile lattice, rectangle drawing, tile picking, point/inspect clicks, raster overlay. Needs no basemap and no network. |
| `mock.js` | In-browser mock of the API, for development and demos only |

These are ES modules with no build step and no dependencies.

## Run with the local runner

Once D-2 (`tools/runner`) exists, the server serves this folder:

```bash
python -m tools.runner serve      # binds 127.0.0.1 only
# then open http://localhost:<port>/ in a browser (from Windows when the server runs in WSL2)
```

If the runner is not running, every page shows: "The local runner did not answer".

## Run with mock data (no runner needed)

```bash
cd web/console
python3 -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/index.html?mock
```

A yellow "mock data · not connected" badge marks this mode. About the mock data:

- **Results.** Every job shows the same sample: a 25 m majority downsample of three frames (08:30, 12:30, 15:10) from the accepted Cheung Chau V2 run of 2026-01-07. The counts in it match that run's `result_index.json`.
- **Everything else is invented:** the machine, the estimates, the tile names and the job progress.

Never use mock output as evidence.

## Wording rules (project red lines)

- 255 / grey is "uncertain", never "shade".
- Estimates are labelled "estimate" and name the calibration machine.
- Every result page carries the disclaimer: engineering result, observational accuracy NOT VERIFIED, and shade is not cooling or ΔT.
- Statistics keep land and water apart and use all land pixels as the denominator. Shade is confirmed by any obstruction found (`src/shade_watch.py::classify`), but sunlit also needs complete 1 km sunward support. A share taken over valid pixels only therefore leans towards shade.
- Formal analysis reads the GeoTIFFs; JPG and MP4 are listed as presentation previews only.

## Development check

`web/console` has no automated test suite in the repository. During development, it was smoke-tested in headless Chromium in `?mock` mode, at desktop (1440 px) and phone (390 px) widths. The test covered:

- planning, the error paths, tile picking and the block on an unaccepted sea view;
- starting a run, the runs table, the job page;
- the results layers, the frame slider, the pixel inspector and the file list;
- no horizontal scrolling and no JavaScript errors.

Integration with the real runner is part of D-2/D-3 acceptance, on the Mac and on WSL2.
