# Shade maps for Rotterdam and other registered cities

Use the repository’s existing `.venv` from the repository root. Place the two
frozen Rotterdam sheets, `R_37FZ1.tif` and `R_37HN1.tif`, in
`data/raw/dsm/rotterdam_ahn4_dsm05/`. The example machine file already names
that directory. The top-level `dsm_dir` and `sea_profile` apply to Hong Kong.
Rotterdam can run from its registered catalogue on a machine with only the
two Rotterdam sheets.

## Register and run Rotterdam

```sh
.venv/bin/python -m tools.city register rotterdam --machine config/machine.example.json
.venv/bin/python -m tools.shade_map plan --machine config/machine.example.json config/regions/rotterdam_projected.json
```

Registration prints the `ingest_id`, `view_id` and registration report. For
Rotterdam, expect `fill_above_ground`. The raw catalogue and the fill view have
separate directories and pointers under `data/processed/`. Repeat registration
compares the ingestion files and verifies the current view. If a Rotterdam
request reports a missing view, use the city registration command above.

The plan resolves two projected RD New corners into a four-cell rectangle
across the sheet seam. To run the 50 summer and winter frames, use the same
machine and region files.

```sh
.venv/bin/python -m tools.shade_map run --machine config/machine.example.json config/regions/rotterdam_projected.json
```

The Python API also accepts WGS84 `[latitude, longitude]` pairs. The example
below requests three instants in Europe/Amsterdam. The default source is
`sea-2.2`.

```sh
.venv/bin/python -c '
from tools.shade_map import shade_map

result = shade_map(
    [51.9200, 4.4750], [51.9230, 4.4800],
    {"mode": "instants", "instants": [
        "2026-06-21T09:00", "2026-06-21T13:40", "2026-06-21T18:00",
    ]},
    name="rotterdam_centre", city="rotterdam", machine="config/machine.example.json",
)
print(result)
'
```

Under the example machine config, the publication appears in
`outputs/shade_map/<name>/`. Read `run_manifest.json` for city and policy
identities. Frame folders use the city’s local dates and clock times. Use
`shade.vrt`, `quality.vrt` and `surface.vrt` to open the complete rectangle.
Keep the layer subdirectories with the VRTs when moving a publication.
The [output codes](../OUTPUT_CODES.md) describe the layers and summary
denominators.

An explicit offset must agree with the city’s offset at that instant.
A nonexistent local time is invalid. An ambiguous time needs an explicit
offset. Choose distinct local frame folders. For a raw counterfactual, set
`"dsm_source": "raw"` and use a distinct run name. To measure fill dependence
on the completed projected run, use this command.

```sh
.venv/bin/python -m tools.sea2 fill-impact --machine config/machine.example.json config/regions/rotterdam_projected.json --times 0900,1330,1800
```

## Add a city

Use the Rotterdam profile and schemas as starting points. Replace the values
with the new city’s own inputs.

1. Add `config/cities/<city_id>.json`. Set the projected metre EPSG CRS, 0.5 m
   resolution, vertical datum, IANA time zone, source line and the exact
   projected bounding box of the sheets. Use the WGS84 latitude and longitude
   of the extent centre, within 0.01°, as the daylight reference.
2. Supply `ingest.cell_pixels` as `[columns, rows]`, at most 2,000,000 pixels
   per cell. List every non-hidden TIFF by filename, byte size, SHA-256 and
   declared NoData. A sheet without a declared sentinel uses JSON `null`.
   Encode a non-finite declared sentinel as `"NaN"`, `"Infinity"` or
   `"-Infinity"`.
3. Add a fill profile under `config/sea_profiles/` with a unique ID, the city’s
   vertical datum and `h_sea_m` of `0.00`. Link its ID in the city profile.
   Surface classes depend on the profile’s label settings.
4. Copy the example machine config, set `cities.<city_id>.raw_dir` and choose
   a publication root. Run the registration command with the new city ID and
   that machine file. Create a 1.1 region config or call `shade_map` with the
   same city ID. Use `projected` corners for exact rectangle reproduction.

WGS84 corners without `city` must match exactly one profile’s extent.
`projected` corners require an explicit city. `hk1980` selects Hong Kong.
The southwest corner must precede the northeast corner on both axes.

## Limits of the results

Only 0.5 m DSMs are supported. Fill is fixed at 0.00 m in each city’s vertical
datum. Rotterdam water and voids use 0.00 m NAP. About 49.7% of valid pixels
and 44.8% of shore pixels are below that level, by up to about 11 m.
The filled surface can block sunlight from reaching adjacent low ground.
The model labels such pixels shaded. Fill-impact measures dependence on the
filled heights and cannot distinguish that false shade from true shade.
Where shores stand above 0 m, fill-dependent land may be wrongly sunlit,
as in Hong Kong.

Coverage ends at the two sheet boundaries. Results within 1 km of a sheet
edge depend on fill. The distant-obstruction threshold is
`atan((highest point in the tile and its 1 km buffer − lowest point in the tile) / 1,000 m)`.
It reaches about 12° in central Rotterdam. Winter-solstice noon reaches about
14.7°. Near tall buildings, most winter frames retain quality 3 wherever the
1 km search cannot prove shade.

The unchanged NOAA approximation has unverified accuracy at 52° N. WGS84
projection depends on the local PROJ operation and grid availability. Use
`projected` corners to reproduce the exact rectangle across machines. The
horizon cache identity contains fixed text naming EPSG:2326 for every city.
The two sheets do not verify their AHN release. Rotterdam surface labels and
observational accuracy in both cities remain **NOT VERIFIED**.
