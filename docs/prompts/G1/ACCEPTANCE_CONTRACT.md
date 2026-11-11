# Package G1.0 acceptance contract — cities other than Hong Kong (first city: Rotterdam)

Contract ID: `SW-G1.0`
Status: frozen on the date of the commit that adds this file, by user approval (2026-11-11). Record this file's SHA-256 before development.
Item codes: `G1-01` to `G1-16` (decision D-011; `G` is a new package letter: geography).
Starting point: the commit that adds this contract, whose parent is `839e200b3bc8b53012bd3fc67627717b1ac44a4c`.
Policies used: `SW-V1-POLICY-1.0` (engine, unchanged rules), `SW-SEA-POLICY-2.2` (fill, unchanged rules, with a new profile for Rotterdam). Policy introduced: `SW-INGEST-POLICY-1.0` (lossless ingestion of a city's raw DSM sheets).
Code definitions and reporting rules: `docs/OUTPUT_CODES.md`.
Decision records (Claude project `claude/DECISIONS.zh-TW.md`; snapshot in `docs/planning/`): D-008, D-009, D-010, D-012, D-015, D-016, D-018, D-019.

The development prompt and the independent-acceptance prompt for G1.0 both use this contract. Do not weaken any criterion after seeing results. Any change to scope, policy values or budgets needs a new contract version, agreed before work starts.

## Problem and objective

The accepted tools work only for Hong Kong. The engine rejects any DSM that is not EPSG:2326, uses a Hong Kong reference point for sunrise and sunset, and uses the Hong Kong time zone. Package F projects corners to EPSG:2326, labels frames in UTC+8 and writes EPSG:2326 rasters.

The objective is that the same function works for a registered city:

```python
from tools.shade_map import shade_map
shade_map([lat1, lon1], [lat2, lon2], when, name="...", city="rotterdam")
```

Latitude and longitude are an input convenience only. All computation and all outputs stay on the city's own projected DSM lattice (metres, square pixels). The DSM is never resampled.

Hong Kong results must stay pixel-identical to the accepted results.

## Non-goals

- No DSM resolution other than 0.5 m. A city whose DSM is not 0.5 m is rejected. The ray-step rule for other resolutions is a later package.
- No fill height other than 0.00 m. A per-city fill height is not a feature of this package.
- No change to the numerical kernel, the classification rule, the 1 km search, `nearest5`, the V1/V2 limits or the horizon cache keys.
- No change to the label rule or the fill rule of `SW-SEA-POLICY-2.2`, and no rebuild of the Hong Kong view.
- No reclassification of quality 3 or 4.
- No Windows-native support, no WSL2 work, no V3 execution, no territory-wide run.
- No download. The two Rotterdam sheets are already in `data/raw/dsm/rotterdam_ahn4_dsm05/`.
- No import policy for the Hong Kong `14NE15*` tiles (D-008 stays open).
- No JPG or MP4 output for a city other than Hong Kong.
- No web work, no WK4 material, no push, no pull request.
- No claim of observational accuracy for either city.

## Frozen decisions (user, 2026-11-10 and 2026-11-11; D-018, D-019)

1. **Fill height.** Every NoData pixel of every city is filled at 0.00 m in that city's vertical datum. Rotterdam is filled at 0.00 m NAP. The planning conversation recommended −11 m for Rotterdam; the user chose 0 m. The consequences are stated as limitations (design item 8), and registration warns about them (design item 3).
2. **Resolution and kernel.** Only 0.5 m DSMs. The four kernel files of design item 2 do not change, so Hong Kong horizon cache keys do not change.
3. **Policy IDs.** `SW-V1-POLICY-1.0` and `SW-SEA-POLICY-2.2` are kept. `SW-INGEST-POLICY-1.0` is added. The city is recorded in the run identity.
4. **Coordinates.** Latitude and longitude are input only. Computation and output stay on the city's projected lattice.
5. **Default source.** The function and new region configs use the accepted fill policy by default. `raw` stays for regression and for the fill-impact counterfactual.
6. **City settings.** One profile per city. The time zone and the daylight reference are fixed in the profile. Hong Kong keeps 22.3° N, 114.2° E.
7. **Test regions, dates and budgets** as in this contract.

## Verified starting facts (planning pre-check, 2026-11-11 16:30–17:30 HKT, linked Mac)

**Repository**

- Branch `feature`, HEAD `839e200`, 12 commits ahead of `origin/feature`; nothing has been pushed. The only tracked modification is `.gitignore`. Untracked planning files (`web/`, `docs/GUIDE*.md`, `config/regions/measure_*.json`, and older planning folders) belong to the user. Do not edit, delete, stage or commit them.
- The ten engine files (`src/v1.py`, `v1_cache.py`, `horizon.py`, `solar.py`, `spatial.py`, `shade_watch.py`, `v2.py`, `v2_worker.py`, `v2_runner.py`, `v2_state.py`) are byte-identical to `356f611`. `tools/`, `config/`, `src/` and `tests/` are identical to `7707c51`.
- SHA-256 of the twelve files that must not change (design items 2 and 4):

  ```
  afb46c37742767e7480220d82527873ed389bb184623fef78b4a3a1d19e8144e  src/horizon.py
  5ecc0495dd102596ab41903b5e174c142888ffc14664b81009164fbf176d3aa7  src/spatial.py
  96a576d12ada9186319e4c8c5f1e626b06ab0aac5f7345a9c6083b9f1b6fe479  src/v1_cache.py
  cfb5d1185af5a39521ecf4edaeddd375b76e1abc877675c63a428de21e546ea7  src/shade_watch.py
  3c47ddd3fc19d8a0c8019c3222657873d14cf64992393e0a89b3ac7425eaf3d5  tools/sea2/__init__.py
  09664e195a7c90a00a066362ccdcb1bbd6c5dbdb699b7087d51339cf225f21eb  tools/sea2/__main__.py
  a5a5cddbd85497fcd725aa9847e166f4f5925173ce3533ed86393d544803faf9  tools/sea2/build.py
  9c18ae57eeb384bb08d2af9048fcc3066b7570ee24fb48b85dfac3cc93342d0a  tools/sea2/catalogue.py
  1c48e1b8fa60f05343e78944184305aad1c9180c93e8553d8b8105d6d93ba2ea  tools/sea2/profile.py
  9fa18de494464053084cbf37ddb8aa03c544b5fdf7d36d71b4b86112ee35079f  tools/sea2/provider.py
  751dde428a1d0a3b26ada11f0b49f77edfb2b816f4a5f28e278c050905466774  tools/sea2/rule.py
  2c4e83ee87ac81f982f7aa8768535336d1e3f24c29983d4a1c264d38c0372875  tools/sea2/view.py
  ```

- Hong Kong-only settings in the engine:
  - `src/v1.py`: the CRS and resolution check in `index_sources`; `DAYLIGHT_REFERENCE = (22.3, 114.2)`; `Asia/Hong_Kong` defaults and the "Hong Kong calendar days" check; `Instant.local` in Hong Kong time; an EPSG:2326 transformer for centre-plus-size requests; the `source_and_owner` raster tag and the media text, which name the CEDD DSM and the Government of the Hong Kong SAR.
  - `src/solar.py`: `HKT` as the local midnight in `daylight_bounds`.
  - `src/v2_worker.py`: EPSG:2326 in the logical-mosaic manifest and in one check.
  - `src/spatial.py` already uses the catalogue's CRS. `src/horizon.py` takes the resolution as an argument and fixes the ray step at 0.25 m.
- Hong Kong-only settings in the tools:
  - `tools/region_request.py`: corner projection to EPSG:2326 (two places); an EPSG:2326 grid in `read_region_window`; it calls `v1.plan_shade` without a time zone or a daylight reference, so the engine's Hong Kong defaults apply.
  - `tools/shade_map/config.py`: fixed UTC+8 labels, `+08:00` in the time expansion, an EPSG:2326 message. `tools/shade_map/publication.py`: EPSG:2326 in the raster profile, the VRT and two checks. `tools/shade_map/sources.py`: literal −9999.
  - `tools/sea2/fill_impact.py`: EPSG:2326 in two places; it reads the raw catalogue from the machine's `dsm_dir` and the profile from the machine's `sea_profile`.
- `tools/sea2/build.py::build(machine, *, profile=None)` accepts a machine dictionary. `tools/sea2/catalogue.py` accepts any projected metre CRS with uniform float32 cells and derives the cell lattice from the catalogue. `tools/sea2/provider.py` finds the view from the machine's `dsm_dir` and `sea_profile`. The view pointer is per profile and the cache namespace is per view. The pointer stores the size and modification time of every catalogue file.
- The unchanged builder writes every view, pointer and build lock into the one folder `data/processed/dsm_views/sea_fill_v2_2/`, which already holds the Hong Kong view.
- The accepted Hong Kong view `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1`: 7,128 cells of 1,500 × 1,200 pixels; domain `[799750, 800200, 864750, 848400]`; catalogue box `[800750, 801200, 863750, 847400]`.
- Regression references exist: `outputs/v2_daylight_cheungchau_20261009` and `outputs/shade_map/measure_{lo_wu,tai_mo_shan,central}`.

**Rotterdam sheets** (`data/raw/dsm/rotterdam_ahn4_dsm05/`; PDOK "DSM 0,5m", CC0, as recorded in D-018). Every tile of both files was decompressed in the pre-check with a reader that is independent of rasterio and GDAL.

| File | Bytes | SHA-256 | Upper-left (E, N) | Declared NoData pixels | Valid pixels | Valid min / max (m NAP) | Valid pixels below 0 m |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `R_37FZ1.tif` | 457,826,580 | `7a679cf84482cf4397e41992e20a42351a9e266a59e9edf2225b1452e13b3431` | (90000, 443750) | 13,156,596 | 111,843,404 | −10.9959 / 154.0600 | 74,779,636 (66.86%) |
| `R_37HN1.tif` | 422,003,345 | `15d2cf2027567128dab7727c2f96ef04d300983752f75be9dff6ad0090269ff5` | (90000, 437500) | 22,795,279 | 102,204,721 | −6.2245 / 204.6538 | 31,541,569 (30.86%) |

- Both files: BigTIFF, 10,000 × 12,500 pixels, float32, DEFLATE with predictor 3, 512-pixel tiles, 0.5 m, EPSG:28992, declared NoData 3.4028234663852886e+38. No pixel is non-finite and no pixel equals −9999. Together they cover E 90000–95000, N 431250–443750. `R_37FZ1` is the northern sheet.
- Over both sheets: 35,951,875 NoData pixels and 214,048,125 valid pixels, of which 106,321,205 (49.67%) lie below 0 m.
- The files carry no tag that names the AHN release or the survey date. The release is not verified from the files. No upstream checksum was available; the hashes identify the files on this disk.
- Shore pixels (valid pixels 4-adjacent to NoData): 3,746,196 in total. Their median height is +0.88 m NAP and 44.8% of them lie below 0 m (northern sheet: median −1.31 m, 61.9% below 0 m, 10th percentile −6.03 m; southern sheet: median +3.74 m, 23.6% below 0 m).
- All 160 cells of 625 m contain NoData.
- Remote-obstruction thresholds computed from the raw sheets for the 160 cells, with a fill height of 0 m: median 5.4°, 90th percentile 11.0°, maximum 11.8°. For the four cells of run NL-1: 9.2° to 10.4°.
- With the repository's own solar functions at 51.92° N, 4.48° E and Europe/Amsterdam: on 2026-06-21 sunrise 05:21:43 and sunset 22:05:07 (+02:00); on 2026-12-22 sunrise 08:47:34 and sunset 16:33:09 (+01:00). At 30-minute steps that is 34 frames (05:30–22:00) and 16 frames (09:00–16:30). At 13:40 on 2026-06-21 (11:40 UTC) the azimuth is 178.4° and the apparent elevation 61.5°. At 12:30 on 2026-12-22 the apparent elevation is 14.7°.
- The centre of the two sheets, (92500, 437500), is 51.9225° N, 4.4786° E (pyproj 3.7.1, PROJ 9.5.1, no grid files).

## Required design

### 1. City profiles

- A city profile is a tracked JSON file `config/cities/<city_id>.json` with schema `config/schema/shade_map_city.schema.json` (`shade-map-city-1.0`). It holds only facts that are the same on every computer.
- Two profiles are delivered with exactly these values:

  ```json
  {
    "schema": "shade-map-city-1.0",
    "city_id": "hong_kong",
    "title": "Hong Kong (CEDD 2020 LiDAR DSM)",
    "crs": "EPSG:2326",
    "resolution_m": 0.5,
    "vertical_datum": "HKPD",
    "timezone": "Asia/Hong_Kong",
    "daylight_reference": [22.3, 114.2],
    "extent": [800750, 801200, 863750, 847400],
    "sea_profile": "hk_cedd_2020",
    "dsm_source_line": "CEDD 2020 LiDAR DSM; source and data owner: Government of the Hong Kong Special Administrative Region",
    "ingest": null
  }
  ```

  ```json
  {
    "schema": "shade-map-city-1.0",
    "city_id": "rotterdam",
    "title": "Rotterdam centre (AHN DSM 0.5 m, sheets 37FZ1 and 37HN1)",
    "crs": "EPSG:28992",
    "resolution_m": 0.5,
    "vertical_datum": "NAP",
    "timezone": "Europe/Amsterdam",
    "daylight_reference": [51.92, 4.48],
    "extent": [90000, 431250, 95000, 443750],
    "sea_profile": "nl_rotterdam_dsm05",
    "dsm_source_line": "AHN DSM 0.5 m, sheets R_37FZ1 and R_37HN1; source: PDOK (Actueel Hoogtebestand Nederland); licence CC0",
    "ingest": {
      "policy": "SW-INGEST-POLICY-1.0",
      "cell_pixels": [1250, 1250],
      "sheets": [
        {"name": "R_37FZ1.tif", "bytes": 457826580,
         "sha256": "7a679cf84482cf4397e41992e20a42351a9e266a59e9edf2225b1452e13b3431",
         "declared_nodata": 3.4028234663852886e+38},
        {"name": "R_37HN1.tif", "bytes": 422003345,
         "sha256": "15d2cf2027567128dab7727c2f96ef04d300983752f75be9dff6ad0090269ff5",
         "declared_nodata": 3.4028234663852886e+38}
      ]
    }
  }
  ```

- `extent` is `[left, bottom, right, top]` in the city CRS: the bounding box of the DSM coverage. The Hong Kong extent is the catalogue box of the accepted view. `daylight_reference` is `[latitude, longitude]`; the Rotterdam value is the centre of the two sheets rounded to 0.01°.
- The time zone and the daylight reference are fixed in the profile. They are not recomputed at run time.
- The machine config (`shade-map-machine-1.0`) gains one optional key, `cities`: an object that maps a city ID to `{"raw_dir": "<folder of the raw sheets>"}`. The existing top-level `dsm_dir` and `sea_profile` keep their meaning and apply to `hong_kong`. An existing machine config stays valid without change.
- An unknown city, a profile that fails its schema, or a profile whose resolution is not 0.5 fails with `invalid input` (CLI exit 2) before any file is created.

### 2. Engine changes (the only edits allowed under `src/`)

- **May change:** `src/v1.py`, `src/solar.py`, `src/v2.py`, `src/v2_worker.py`, `src/v2_runner.py`, `src/v2_state.py`. Changes are limited to accepting these as inputs instead of Hong Kong constants: the CRS, the time zone, the daylight reference and the DSM source line.
- **Must stay byte-identical to `356f611`:** `src/horizon.py`, `src/spatial.py`, `src/v1_cache.py`, `src/shade_watch.py`. If the work seems to need a change in one of these four files, stop and report. Do not change them.
- Every public function and CLI option under `src/` keeps its current default, so that a call that names no city behaves as today.
- The engine accepts a DSM catalogue only if every tile has the one CRS it was given and 0.5 m pixels on the projected-origin lattice. The checks on tile size (`MAX_TILE_PIXELS`) and lattice alignment stay.
- The daylight day is the local calendar day in the given time zone. Sunrise and sunset use the given daylight reference. Frames stay aligned to the local wall clock.
- For a city other than `hong_kong`, the engine's raster tags carry the given DSM source line and the given time zone, and a request for JPG or MP4 is rejected with a clear error. For `hong_kong`, tags and media are as today.
- The policy tag stays `SW-V1-POLICY-1.0`. The horizon cache identity keeps its text `EPSG:2326 projected origin E0,N0; ...` for every city, because `src/v1_cache.py` may not change. The cache identity already contains the real CRS of each tile, so keys of different cities cannot collide. This stale text is recorded as a known limitation in the documents.

### 3. Ingestion (`SW-INGEST-POLICY-1.0`)

Raw sheets of a new city can be far larger than the engine's tile limit and can declare any NoData value. Ingestion turns them into a catalogue that the engine and the unchanged fill builder can read.

- **Command:** `python -m tools.city register <city_id> --machine <machine.json>`. It reads `cities.<city_id>.raw_dir`, and it is read-only on raw data.
- **Source check.** Registration fails if a sheet listed in the profile is missing or differs in size or SHA-256, if an unlisted `.tif` is present, if a sheet's CRS, resolution, data type, declared NoData value or lattice alignment is not as declared, or if two sheets overlap.
- **Profile check.** Registration fails if `extent` is not the bounding box of the sheets, or if `daylight_reference` is more than 0.01° from the centre of `extent`.
- **Cells.** The catalogue is cut into cells of `ingest.cell_pixels` (Rotterdam: 1250 × 1250 pixels, 625 m). Cell edges are multiples of the cell size from the projected origin. A cell is written if and only if it intersects a raw sheet. Rotterdam gives 160 cells.
- **Values.** A pixel whose raw value equals the sheet's declared NoData value, or is non-finite, becomes −9999.0. Every other pixel keeps its exact float32 bits. A part of a cell that no sheet covers is −9999.0. Each cell is a float32 GeoTIFF with lossless compression, the city CRS, and declared NoData −9999.0.
- **Guard.** Registration fails if any raw pixel that is not NoData equals −9999.0.
- **Output,** written only to `data/processed/dsm_catalogues/<city_id>/<ingest_id>/`: `tiles/`, `manifest.json`, `registration_report.json`. A pointer `data/processed/dsm_catalogues/<city_id>/current.json` names the latest ingestion.
- **Identity.** `ingest_id` is the hash of the manifest content without timestamps. The manifest records the policy ID, the profile and its hash, each raw sheet's hash, each cell's bounds, output hash, valid count and NoData count, the library versions, and the hashes of the ingestion code. It holds no absolute path. Running registration again with the same inputs and code, in the same or in another checkout, gives the same `ingest_id` and the same file hashes.
- **Repeat.** When `<ingest_id>` already exists, registration compares every existing file with the fresh result and leaves the existing files untouched. A difference is an error.
- **Registration report.** It records, over all valid pixels: count, minimum, maximum, and the 1st, 50th and 99th percentiles; the NoData count; the centre of `extent` in latitude and longitude; the fill height `h_fill` of the city's fill profile; the number and share of valid pixels below `h_fill`; and these warnings:
  - `fill_above_ground` when any valid pixel is below `h_fill`;
  - `fill_far_below_ground` when `h_fill` is more than 10 m below the 1st percentile.

  Warnings do not stop registration. They are printed and stored.
- Hong Kong is not ingested. Its profile has `ingest: null`, and its raw catalogue and accepted view are used as they are.

### 4. Fill view for a new city

- The fill view is built by the unchanged `SW-SEA-POLICY-2.2` builder on the ingested catalogue with the city's fill profile. The build is started by `python -m tools.city register` after ingestion.
- **These files must stay byte-identical to `7707c51`:** `tools/sea2/__init__.py`, `__main__.py`, `build.py`, `catalogue.py`, `profile.py`, `provider.py`, `rule.py`, `view.py`. They are the files whose hashes are part of every view identity. If the work seems to need a change in one of them, stop and report.
- The Rotterdam view, its pointer `current-nl_rotterdam_dsm05.json` and its build lock are new entries in `data/processed/dsm_views/sea_fill_v2_2/`. The Hong Kong view `8ee51b01…cbd1`, its pointer `current-hk_cedd_2020.json`, its build lock and its cache namespace are not rebuilt, changed or added to.
- **Rotterdam fill profile** `config/sea_profiles/nl_rotterdam_dsm05.json`, with exactly these values:

  ```json
  {
    "schema": "sea-profile-1.0",
    "profile_id": "nl_rotterdam_dsm05",
    "vertical_datum": "NAP",
    "h_sea_m": 0.00,
    "low_shore_margin_m": 5.00,
    "max_shore_distance_m": 1000,
    "shore_preference_m": 50,
    "connectivity": 4,
    "exclusions": [
      {"id": "ring_south", "bounds": [89000, 430250, 96000, 431250], "reason": "outside the registered sheets: no data, not water"},
      {"id": "ring_north", "bounds": [89000, 443750, 96000, 444750], "reason": "outside the registered sheets: no data, not water"},
      {"id": "ring_west", "bounds": [89000, 431250, 90000, 443750], "reason": "outside the registered sheets: no data, not water"},
      {"id": "ring_east", "bounds": [95000, 431250, 96000, 443750], "reason": "outside the registered sheets: no data, not water"}
    ]
  }
  ```

  - `h_sea_m` 0.00 is the fill height (frozen decision 1). The label parameters equal Hong Kong's and affect labels only.
  - The four rectangles cover the 1,000 m ring outside the two sheets. The ring gets class 4, not class 2.
- No fill height other than 0.00 m is delivered, documented as supported or tested in this package.
- The surface classes of a new city are labels from the same rule. For Rotterdam there is no reference map; the labels are **not verified**.

### 5. Package F: `city`, coordinates and time

- **Signature:**

  ```python
  shade_map(lower_left, upper_right, when, *, name, city=None, crs='wgs84',
            machine='config/machine.local.json', dsm_source='sea-2.2', full_image='auto')
  ```

  `plan_shade_map` gets the same parameters. The CLI is unchanged apart from the new config fields.
- **Region config `shade-map-region-1.1`** adds:
  - `city` (optional string);
  - `crs` value `projected`: corners are `[easting, northing]` in the city CRS;
  - default `dsm_source` `sea-2.2`;
  - instants with any explicit UTC offset.

  The function builds a 1.1 config. A `shade-map-region-1.0` file keeps its exact present meaning: Hong Kong, default `dsm_source` `raw`, `crs` `wgs84` or `hk1980`, and no extent check. `hk1980` is valid only for `hong_kong`.
- **City selection** (1.1 configs and function calls).
  - If `city` is given, it is used.
  - If it is omitted: `hk1980` selects `hong_kong`; `wgs84` selects the one city whose `extent` contains both projected corners; `projected` requires `city`.
  - No city, or more than one, fails with `invalid input` and names the candidates.
  - A rectangle that is not completely inside the selected city's `extent` fails with `invalid input`.
  - All of this happens before any file is created.
- **Corners.** The lower-left and upper-right rule of D-010 is unchanged and applies in both the input CRS and the city CRS.
- **Coordinates.** WGS84 corners are projected once to the city CRS with pyproj (`always_xy`), without network access. The plan records the operation that pyproj reports, its stated accuracy (which may be unknown), and the pyproj and PROJ versions. After that step everything is in the city CRS: the snapped rectangle, the cells, the rasters, the VRTs and the manifests.
- **Outputs.** Rasters and VRTs carry the city CRS and the DSM lattice (0.5 m). No resampling and no reprojection of any raster.
- **Time.**
  - Daylight dates are local calendar days in the city's time zone.
  - Folder names `<YYYYMMDD>/<HHMM>` and `local_time` fields use the city's local wall clock with its UTC offset at that instant. `utc_time` is unchanged.
  - An instant without an offset is local time. An instant with an offset must agree with the city's offset at that instant, otherwise `invalid input`. A local time that does not exist or is ambiguous on a clock-change day is `invalid input`.
  - Two frames of one run may never share a folder.
  - For `hong_kong`, every label, folder name and manifest time value is identical to the accepted behaviour for the same input.
- **Run manifest.** It gains a `city` block: `city_id`, the profile hash, `crs`, `timezone`, `daylight_reference`, `vertical_datum`, and for an ingested city the `ingest_id`. The run identity includes this block. The publication format becomes `shade-map-publication-1.1`. Raster encoding is unchanged.
- **Plan.** The plan gains `fill_context`: the number of cells in the 1 km dependency set that have no DSM tile, and the warning `no_dsm_cells_within_1km` when that number is above zero. It is a report, not a rejection.
- **Sources.** `raw` and `sea-2.2` work for every registered city.
  - For an ingested city, both read the ingested catalogue, and `sea-2.2` reads the view of the city's fill profile. `tools/sea2/provider.py` is unchanged; package F gives it the city's catalogue and profile.
  - For a city other than `hong_kong`, the `raw` cache namespace is `<cache_namespace>_<city_id>`.
  - A city whose view is missing fails with the existing `sea view missing ...` message.

### 6. Other tools

- `tools/region_request.py` may change only to accept the city's CRS, time zone and daylight reference and to pass them to the engine. Its existing CLI and its results for `wgs84` and `hk1980` are unchanged.
- `tools/sea2/fill_impact.py` may change only to resolve the run's city: its catalogue, fill profile, CRS and time zone. The diagnostic must work for Rotterdam.
- Other files under `tools/sea2/` (`checks.py`, `validate_ib5000.py`, `validation_worker.py`, `resources.py`) are Hong Kong validation tools. They are not changed and are not required to work for other cities. Their existing tests must still pass.
- `tools/sea_view/`, `tools/wsl2_smoke/` and the `tools/v*_*.py` scripts are not changed.

### 7. Identity and history

- Hong Kong run IDs change, because the hashes of the engine files and the publication format are part of the run ID. Pixels do not change. Published runs are never overwritten: the existing rule (same name, different run ID, exit 2) stays. Regression runs use new names.
- Horizon cache keys for Hong Kong do not change, because the three files that define them do not change. A regression run on a region whose cache is complete computes no direction.
- A Rotterdam run has its own catalogue, view, pointer and cache namespaces. It shares no data with Hong Kong.

### 8. Documentation

- `docs/city/GUIDE.md`: how to run Rotterdam from a clean checkout (register, then call the function), and how to add another 0.5 m city. Every command must be copyable.
- `docs/city/DESIGN.md`: what was parameterised, the ingestion policy, and the limits below.
- `docs/city/DEVELOPMENT_REPORT.md` with evidence under `docs/city/evidence/`. The machine and region configs of every development run are stored under `docs/city/evidence/configs/`.
- Required limitation statements, in these documents and in the report:
  - Only 0.5 m DSMs are supported.
  - Every city is filled at 0.00 m in its own vertical datum. No other fill height is supported.
  - Rotterdam water and voids are filled at 0.00 m NAP. 49.7% of the valid pixels and 44.8% of the shore pixels lie below 0 m, by up to about 11 m. There the filled surface stands above the observed surface next to it and can shade it. Such pixels are labelled shaded, not uncertain. The fill-impact diagnostic measures dependence on fill, not error, and it cannot separate this false shade from true shade.
  - Where the shore is above 0 m, land that depends on fill may be wrongly sunlit, as in Hong Kong.
  - Outside the two sheets there are no data. Results within 1 km of the sheet edge depend on fill.
  - The solar model is the unchanged NOAA approximation. Its accuracy at 52° N is not verified by this package.
  - The remote-obstruction threshold is atan((highest point within the tile and its 1 km buffer − lowest point of the tile) ÷ 1,000 m). In central Rotterdam it reaches about 12°. At the winter solstice the noon sun is about 14.7° high, so most winter frames near tall buildings stay quality 3 for pixels that are not proven shaded. This is the 1 km model boundary, not a defect of this package.
  - WGS84 input depends on the PROJ operation available on the computer. Reproducing a rectangle exactly on another computer is guaranteed only with `projected` corners.
  - The horizon cache identity keeps a fixed text that names EPSG:2326 for every city.
  - The AHN release of the two sheets is not verified from the files.
  - Surface labels for Rotterdam are not verified. Observational accuracy is not verified for any city.
- Engineering acceptance, numerical consistency, approximation error, performance, observational accuracy and production completion are stated separately.

## Authorized computation scope (development)

Hong Kong regression, each as a new run name under the development output root, compared with the reference named:

| Run | Source | Region and frames | Reference (read-only) |
| --- | --- | --- | --- |
| HK-1 | `raw` | Cheung Chau `[820250, 807200]`→`[821750, 808400]`, 2026-01-07, daylight, 10 min (65 frames), new raw cache namespace | `outputs/v2_daylight_cheungchau_20261009` (accepted V2) |
| HK-2 | `sea-2.2` | the `measure_lo_wu` region, 2026-06-21 and 2026-12-22 (146 frames) | `outputs/shade_map/measure_lo_wu` |
| HK-3 | `sea-2.2` | the `measure_tai_mo_shan` region, same dates (146 frames) | `outputs/shade_map/measure_tai_mo_shan` |
| HK-4 | `sea-2.2` | the `measure_central` region, same dates (146 frames) | `outputs/shade_map/measure_central` |

The three `measure_*` references were produced by the user on 2026-11-10 with the accepted code at `839e200`. They are outputs of accepted code, not independently accepted evidence. Each reference folder holds its `region_config.json`.

Rotterdam:

| Run | Source | Region and frames |
| --- | --- | --- |
| NL-0 | — | `register rotterdam` once: ingestion and view build. Stopped or failed attempts count toward the same budget. |
| NL-1 | `sea-2.2` | `projected` `[91875, 436875]`→`[93125, 438125]` (four cells across the seam of the two sheets), 2026-06-21 and 2026-12-22, daylight, 30 min (expected 34 + 16 frames) |
| NL-2 | `sea-2.2` by default | Python function call with `city="rotterdam"`, WGS84 corners `[51.9200, 4.4750]`→`[51.9230, 4.4800]` and no `dsm_source`; instants 2026-06-21 09:00, 13:40 and 18:00 local |
| NL-3 | `raw` | The NL-1 rectangle; instants 2026-06-21 09:00, 13:30 and 18:00 local |
| NL-4 | fill-impact | On NL-1 with `--times 0900,1330,1800` (five frames) |
| NL-5 | plan only | `projected` `[90000, 436875]`→`[90625, 437500]` (a cell at the sheet edge) at one instant; and daylight plans of the NL-1 rectangle for 2026-03-28, 03-29, 10-24 and 10-25 |

Direct-ray spot checks on NL-1 frames are authorized. Nothing else that reads real DSM is authorized in development. Synthetic tests are not limited.

Independent acceptance repeats these runs under its own names. It registers Rotterdam afresh in its own worktree and once more as a repeat. It may add one Rotterdam rectangle of its own choice of at most four cells and twelve instants.

## Budgets

| Budget | Development | Independent acceptance |
| --- | --- | --- |
| Real-DSM shade jobs (wall clock, sleep included) | ≤ 90 min | ≤ 75 min |
| Rotterdam registration (ingestion and view build) | ≤ 20 min, once | ≤ 30 min: one fresh registration and one repeat |
| Total job memory | ≤ 12 GiB | ≤ 12 GiB |
| New artifacts | ≤ 20 GiB | ≤ 20 GiB |

Keep the computer awake during timed jobs, for example with `caffeinate`. Record start, end and peak memory of every job that reads real DSM, including planning. When a budget runs out, the criteria it affects become NOT VERIFIED. Budgets may not be extended.

## Write scope and allowed files

**Files the candidate may add or change.** This list is complete; reviewers use it as written.

- New: `tools/city/**`, `config/cities/hong_kong.json`, `config/cities/rotterdam.json`, `config/schema/shade_map_city.schema.json`, `config/sea_profiles/nl_rotterdam_dsm05.json`, `config/regions/rotterdam_*.json` (examples for the guide), `docs/city/**`, `tests/test_city_*.py`.
- May change:
  - the six engine files of design item 2;
  - `tools/shade_map/*.py`;
  - `tools/region_request.py` and `tools/sea2/fill_impact.py`, within design item 6;
  - `config/schema/shade_map_region.schema.json`, `shade_map_machine.schema.json`, `shade_map_plan.schema.json`, `shade_map_run.schema.json`, `shade_map_frame.schema.json` and `fill_impact.schema.json`, as far as this contract needs;
  - `config/machine.example.json`;
  - `docs/shade_map/GUIDE.md` and `DESIGN.md`; `docs/OUTPUT_CODES.md` (additions only);
  - existing test files, only to add cases.
- Must not change: the four engine files and the eight `tools/sea2/` files named above; `docs/prompts/` and `docs/planning/`; every acceptance report; `config/sea_profiles/hk_cedd_2020.json` and `config/schema/sea_profile.schema.json`; `config/regions/cheung_chau.json`; the user's untracked files, including `config/machine.local.json`.

**Data and output locations the work may write:**

- `data/processed/dsm_catalogues/` (new);
- in `data/processed/dsm_views/sea_fill_v2_2/`: the new Rotterdam view folder, `current-nl_rotterdam_dsm05.json`, `build-nl_rotterdam_dsm05.lock` and the builder's temporary folders;
- new cache namespaces under `data/processed/shade_v1/`: `sea_fill_v2_2_<Rotterdam view_id12>`, `sea2_2_fill_impact_<id12>`, and raw namespaces whose names start with `g1_`;
- the output roots `outputs/shade_map_g1_dev_<YYYYMMDD>/` (development) and `outputs/shade_map_g1_review_<sha12>_<YYYYMMDD>/` (acceptance), including their `_diagnostics/` folders;
- new entries for new run names in the fixed containers `outputs/shade_map_work/`, `outputs/shade_map_work/.locks/`, `outputs/region_views/`, `outputs/sea2_2_diagnostic_work/` and its `.locks/`.

**What counts as a write to an existing folder** (the rule of B2.2). Creating a new entry for a new run name in a fixed container, or a new namespace under `data/processed/`, does not count. Changing or deleting an existing file, or adding a file inside an existing run folder, view or cache namespace, does count. Reading an existing complete horizon cache is allowed. If a regression run would add a cache entry to an existing namespace, stop and report.

**Read-only:** `data/raw/`; every existing folder under `data/processed/` and `outputs/`, including the Hong Kong view, the existing cache namespaces and the published runs.

One local commit on `feature`. No push.

## Acceptance matrix

Each item is PASS, FAIL or NOT VERIFIED, with evidence. The package is accepted only if every item is PASS.

| Item | Requirement | Evidence |
| --- | --- | --- |
| G1-01 | Scope. Only allowed files differ from the starting commit. The four engine files equal `356f611` and the eight `tools/sea2/` files equal `7707c51`, byte for byte (hashes in this contract). Raw data, existing outputs, existing processed folders and the user's untracked files are unchanged. All writes are inside the listed locations. One local commit, nothing pushed. | `git diff --stat`, file hashes, comparison with the baseline listing taken before development. |
| G1-02 | Hong Kong pixels. HK-1 to HK-4: every shade and quality raster, and every surface raster where the reference has one, is pixel-identical to its reference. Frame lists, folder names and per-frame counts are identical. | Per-frame comparison table; zero differing pixels. |
| G1-03 | Hong Kong cache identity. HK-2 to HK-4 compute zero directions, and no file in an existing cache namespace is added or changed. | Plan and run logs (missing directions, computed and reused counts); namespace listing before and after. |
| G1-04 | Compatibility. `config/regions/cheung_chau.json`, the user's `config/machine.local.json` and a `shade-map-region-1.0` file without `dsm_source` plan successfully with their present meaning (Hong Kong; default `raw`). All tests that exist at the starting commit still pass, and none is removed or weakened. | `plan` outputs; `pytest tests` summary; diff of the test files. |
| G1-05 | City profiles. Both profiles and the Rotterdam fill profile hold exactly the values of design items 1 and 4 and pass their schemas. An unknown city, a broken profile and a resolution other than 0.5 are rejected before any file is created. | Files; tests. |
| G1-06 | City selection and corners. All rules of design item 5 hold, including automatic selection from WGS84 corners, a rectangle outside the extent, `projected` without a city, `hk1980` with a city other than `hong_kong`, and corners in the wrong order. Every rejection is `invalid input`, exit 2, with no file created. | Tests; CLI transcripts. |
| G1-07 | Ingestion is lossless. An independent reader compares both raw sheets with the ingested cells over all 250,000,000 pixels: every raw NoData pixel is −9999.0, every other pixel has identical bits, and the totals are 35,951,875 NoData and 214,048,125 valid. 160 cells exist, each 1250 × 1250, EPSG:28992, on the lattice. Registration refuses a changed, missing or extra sheet, and a profile whose extent or daylight reference fails the profile check. Nothing under `data/raw/` changes. | Reviewer's own script and its output; tests with synthetic sheets; raw file hashes before and after. |
| G1-08 | Ingestion and view are reproducible. A fresh registration by the reviewer, in a separate worktree, gives the same `ingest_id`, the same `view_id` and the same file hashes as the developer's. A repeat registration succeeds and leaves the existing files untouched. | Both manifests; hash comparison; listing before and after the repeat. |
| G1-09 | Registration report. It contains every value of design item 3. The minimum, maximum and NoData count agree with the pre-check facts of this contract. The Rotterdam registration raises `fill_above_ground` and reports 106,321,205 valid pixels below `h_fill` (49.67%); it does not raise `fill_far_below_ground`. A synthetic city that lies wholly above 0 m raises no warning; a synthetic city whose 1st percentile is more than 10 m above 0 m raises `fill_far_below_ground`. | Report file; reviewer's recomputation; tests. |
| G1-10 | Fill view. In the Rotterdam view every −9999.0 pixel of the ingested catalogue holds exactly float32 0.0, and every other pixel has identical bits. Over the domain of 406,000,000 pixels: class 0 totals 214,048,125; classes 1, 3 and 4 inside the two sheets total 35,951,875; the 156,000,000 pixels outside the sheets are all class 4; class 2 is zero. The Hong Kong pointer still names view `8ee51b01…cbd1`, and that view is unchanged. | Reviewer's own script; view manifest totals; Hong Kong pointer and view hashes before and after. |
| G1-11 | Native grid. Every NL-1, NL-2 and NL-3 raster and VRT is EPSG:28992 with 0.5 m pixels whose edges are multiples of 0.5 m, and has the size its bounds imply. NL-2's plan records the PROJ operation, its accuracy and the versions. Projecting the NL-2 corners independently on the same computer gives the same snapped rectangle. | Raster headers; plan file; reviewer's projection. |
| G1-12 | Time. Rotterdam frames use Europe/Amsterdam: `+02:00` on 2026-06-21, 2026-03-29 and 2026-10-24; `+01:00` on 2026-12-22, 2026-03-28 and 2026-10-25. NL-1 has 34 frames on 2026-06-21 (05:30 to 22:00) and 16 on 2026-12-22 (09:00 to 16:30); each list is the set of 30-minute wall-clock steps between sunrise and sunset computed independently by the reviewer for 51.92° N, 4.48° E. NL-2's frames have `utc_time` 07:00, 11:40 and 16:00; in its 13:40 frame every cell's solar azimuth is between 175° and 185° and its apparent elevation between 61.0° and 62.0°. An offset that disagrees with the city, and a local time that does not exist, are rejected. | Plans; `frame.json` files; reviewer's computation; tests. |
| G1-13 | Rotterdam runs. NL-1, NL-2 and NL-3 finish `complete`. NL-2 is started through the Python function with `city="rotterdam"` and without `dsm_source`, and its manifest shows `sea-2.2`. Layers, folders, VRTs, manifests and summaries follow the F format; each manifest has the `city` block and the policy pair. Every NL-1 and NL-2 frame has zero quality 1 and zero quality 2 pixels. Shade, quality and surface hold only defined codes. No file written for Rotterdam names the Hong Kong DSM source, `HKT` or `Asia/Hong_Kong`, except the fixed cache-identity text of design item 2; engine raster tags carry the Rotterdam source line. | Run folders; validator output; code histograms; tag listing and text search. |
| G1-14 | Independent rays. For at least 1,200 target pixels of NL-1, spread over at least four frames, an independent direct-ray implementation on the filled view agrees with the published shade and quality. The sample includes pixels next to filled water, pixels whose rays cross the sheet seam and, as far as NL-1 contains them, at least 200 observed pixels below 0 m within 50 m of a filled pixel; the available count is reported. Zero unexplained disagreements. | Reviewer's script, sample list and result table. |
| G1-15 | Fill impact and missing coverage. NL-4 produces a valid fill-impact result in EPSG:28992 for five frames, with dependence counts by code, and writes nothing inside the NL-1 run folder. The NL-5 edge plan reports cells without DSM and the warning `no_dsm_cells_within_1km`; the NL-1 plan reports zero. | Diagnostic outputs; plan files. |
| G1-16 | Documents and budgets. The guide's commands work as written. Every limitation statement of design item 8 is present. The six conclusion types are stated separately. Every job has start, end and peak memory, and every budget is met. No network access by the tools. | Documents; the report's job ledger. |

## Decisions and release

- A PASS on all sixteen items means: the city mechanism is engineering-accepted; Hong Kong numerical consistency is shown on four regions; Rotterdam results are model results on two map sheets under a 0 m fill.
- It does not mean: observational accuracy for Hong Kong or Rotterdam; that a 0 m fill is physically right for Rotterdam; verified surface labels for Rotterdam; solar accuracy at high latitude; support for other resolutions or fill heights; a city-wide or territory-wide computation; a cooling effect.
- Using another city, changing a fill height, migrating Hong Kong to an ingested catalogue, Windows support and any push each need their own decision.
- Fixes need a new commit SHA and targeted re-acceptance. Failure evidence is preserved.
