# Study Area: HKUST Shade Watch Pilot

Complete the fields marked **REQUIRED** before starting the real-data simulation.
The minimum entries are the centre latitude, centre longitude, and simulation
date. Place the DSM files and paper in the folders listed below. Optional fields
may remain `Unknown` or `Not available`; do not guess missing metadata.

## 1. Location — REQUIRED

- Site name: HKUST pilot_DJI_20260107143259_0005_V
- Centre latitude (WGS84, decimal degrees): [22° 20' 24.408" north]
- Centre longitude (WGS84, decimal degrees): [114° 15' 47.964" East]
- Coordinate source or map link (optional): Unknown
- Description of the selected location (optional): Unknown

Enter latitude and longitude separately. Do not enter projected easting/northing
coordinates in these fields. If you only have projected coordinates, record them
below with their CRS and ask Codex to transform them before proceeding.

- Alternative coordinates and CRS, if applicable: Not applicable

## 2. Spatial Scope — native tile default, preserved custom extent

- Default output mode: **native_tile**, controlled by `config/processing.json`; read tile bounds, dimensions, resolution and CRS from GeoTIFF metadata. The saved location selects the tile. The effective output centre and shared solar reference are the selected native tile’s geometric centre; original coordinates above are preserved. West/north edges are included; east/south edges are excluded.
- Preserved custom output area: **600 m east–west × 450 m north–south**
- Custom output area size: **270,000 m² (0.27 km²)**
- Custom placement: Explicit custom mode only; centred on the location specified above unless `custom_center_wgs84` or `--center-lat` / `--center-lon` overrides it
- Native mosaic example: `config/mosaic_6tiles.json`, six contiguous tiles in 2 columns × 3 rows; complete native bounds, one native tile per task, one shared union-centre solar reference
- Target DSM resolution: **0.5 m**, preferably the native source resolution
- Custom output dimensions at 0.5 m: **1,200 × 900 pixels**
- Maximum horizontal ray-search distance: **1,000 m**
- DSM input buffer: **1,000 m on every side of each computational core**, or 2,000 pixels at 0.5 m
- Computational work unit: **one native tile's dimensions**, read from the study-centre tile metadata (currently 1,500 columns × 1,200 rows). A native-tile output is one spatial task.
- Worker count: **1** by default; see `config/processing.json`. Fixed-size cores remain an explicit optional mode.
- Custom single-region input bounding extent: **2.6 km east–west × 2.45 km north–south**
- Scope expansion: Expanded from 100 m × 100 m to 600 m × 450 m at the user's request.

Codex must define the rectangle in a suitable metric projected CRS and document
pixel-grid alignment and the final bounds. Preserve the source's actual
resolution in the audit; do not silently upsample coarser data and describe it as
native 0.5 m data. The search limit is the adopted model boundary; the buffer supplies neighboring data.
Neither establishes that terrain beyond 1 km cannot cast shadows.

## 3. Simulation Time — REQUIRED

- Simulation date (YYYY-MM-DD): [2026-01-07]
- Time zone: **Asia/Hong_Kong (UTC+08:00 for the intended modern dates)**
- Coverage: Actual daylight period on the selected date
- Initial simulation interval: **10 minutes**
- Preferred time for the standalone JPG (HH:MM, local time; optional): Auto-select a useful daylight frame and report the choice
- Reason for selecting this date (optional): Unknown

The date is the simulated date, not necessarily the DSM acquisition date.
If validation images were captured on other dates, record their actual times
below; do not change their timestamps to match the simulation.

## 4. Input Files

All paths below are relative to the `shade_watch_hk` project root.

### Paper

- Main paper: `references/Shade Watch.pdf`
- Supplementary material filenames, if available: Not available

### DSM — files required; metadata can be inspected by Codex

- Folder: `data/raw/dsm/`
- Provider / dataset name: Unknown
- Download URL: Unknown
- Acquisition year or date range: Unknown
- Download date: Unknown
- Tile filenames or index file (optional): Codex should inventory this folder
- Does the download include the output area and its surrounding buffer? Unknown — verify from the files
- Horizontal CRS: Unknown — inspect metadata
- Vertical datum and elevation units: Unknown — inspect metadata
- Native pixel size: Unknown — inspect metadata
- NoData definition: Unknown — inspect metadata
- Metadata / licence / README filenames, if supplied: Unknown
- Known missing tiles or changed buildings / vegetation: Unknown

Keep the original tiles and accompanying metadata unchanged. Record unavailable
metadata explicitly; do not invent a CRS, vertical datum, or missing elevations.

### Optional Basemap

- Folder: `data/raw/basemap/`
- Availability: Not available
- Source, filenames, acquisition date and usage terms: Unknown

A basemap is optional and must not be treated as an input to the shadow physics.

## 5. Independent Validation — optional for initial simulation

- Folder: `data/raw/validation/`
- Availability: Not available

If images are available, add one row per image or provide a separate index.
Use actual capture times, not file modification times. Record whether each
timestamp and location is measured, documented, approximate, or unknown.

| Filename | Capture date | Local time | Time zone | Location / coordinates | Image type | Weather / cloud conditions | Time and location confidence / source |
|---|---|---|---|---|---|---|---|
| [Optional: replace this row] | Unknown | Unknown | Unknown | Unknown | Ground photo / UAV / orthophoto / satellite | Unknown | Unknown |

- Georeferencing, camera position, landmarks or control points: Unknown
- Known scene changes relative to the DSM: Unknown
- Other validation notes: None

If suitable validation evidence is absent, generate the real-DSM simulation but
label it **Not yet validated against real-world observations**. Do not invent
accuracy results or treat numerical self-consistency as real-world validation.

## 6. Agreed Outputs — already specified

- A top-down JPG for one reported simulation time.
- An MP4 showing the selected native-tile or custom area over the selected daylight period.
- Corresponding lossless GeoTIFF and PNG results: **1 = shaded, 0 = sunlit** for
  valid pixels, with invalid / NoData pixels represented separately and explicitly.
- JPG / MP4 are presentation files, not the authoritative binary labels.
- Pixel-level binary maps are required; spatially aggregated shade fractions
  must not replace them.
- If it does not materially delay the core outputs, a local web map with a
  time slider and playback using the same computed results.
- A reproducible run command, environment record, input provenance and QA report.

## 7. Scope and Remaining Notes

- Method: Independent reconstruction of Shade Watch unless verified author code becomes available.
- Baseline: 5° azimuth LUT and nearest-direction lookup, with conventions documented and tested.
- Interpretation: Clear-sky direct-sun obstruction on the DSM surface.
- Exclusions: No Slim Shady / UMEP / Deep Umbra workflow; no heat_index_urop integration or temperature analysis.
- Local hardware details: Codex should inspect the current machine.
- Additional instructions or constraints: None
