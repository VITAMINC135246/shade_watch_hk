# City profiles and native DSM grids

SW-G1.0 adds city selection to the shade map interface. City profiles supply the projected CRS, local time zone, daylight reference and source attribution. The engine keeps the 0.5 m lattice, 1 km search and SW-V1-POLICY-1.0 classification. Registration cuts sheets into lossless native cells before the existing SW-SEA-POLICY-2.2 builder fills them.

## Verification plan

| Item | Development check and evidence |
| --- | --- |
| G1-01 | Record the starting tree, protected hashes and file metadata. Audit the final tree and staged paths. |
| G1-02 | Compare all HK-1 to HK-4 frame timestamps, counts and pixels against the named references. |
| G1-03 | Require zero misses before HK-2 to HK-4. Compare cache listings and record reused and computed directions. |
| G1-04 | Plan the legacy Cheung Chau region and its no-source variant with the existing machine config. Run the full test suite. |
| G1-05 | Validate the frozen profiles and exercise rejection of bad profiles and resolutions on synthetic data. |
| G1-06 | Test city selection, projection, corner order and extent with synthetic catalogues and CLI rejections. |
| G1-07 | Test sentinel conversion, bit preservation, source guards and extent validation. Compare registered cell totals with the pre-check. The independent reader runs in review. |
| G1-08 | Test repeat registration with synthetic data. Record identities and file hashes for the reviewer’s fresh registration. |
| G1-09 | Check Rotterdam registration statistics and both warning thresholds with synthetic and real inputs. |
| G1-10 | Compare the built view’s class totals and preserve the Hong Kong view. Review independently checks the full domain. |
| G1-11 | Inspect all Rotterdam raster and VRT headers and the WGS84 projection record. Review repeats the projection independently. |
| G1-12 | Compare local frames and offsets with the frozen expectations and test invalid clock times. Review independently computes daylight. |
| G1-13 | Run the CLI and Python entry points and check manifests, tags, encodings and quality counts. |
| G1-14 | Compare direct-ray spot checks with NL-1 rasters. Review freezes and checks its own sample. |
| G1-15 | Verify the diagnostic’s five frames and the edge and interior dependency reports. |
| G1-16 | Verify copyable commands and record each real-data job’s time, memory and artifact bytes. |

## Registration and identity

`tools.city` validates the portable profile and pins each non-hidden sheet by
size and SHA-256 before opening its native pixel grid. The extent must match the
union’s bounding rectangle. The reference point must be within 0.01° of its
centre. The work stays on the projected-origin lattice. Registration reads
integer windows and writes lossless DEFLATE float32 cells, carrying finite
observed values bit for bit. Declared NoData, non-finite pixels and uncovered
padding use -9999.0. The collision guard rejects a valid raw -9999.0 value.
The report distinguishes raw NoData from cell padding.

The staging directory holds the cells and an on-disk float32 array used to
calculate the exact linear-interpolated percentiles. Statistics use raw
coverage. The manifest identifies the profile by canonical JSON hash and
records library versions, code hashes and each cell’s SHA-256. Canonical
manifest content determines `ingest_id` before the ID field is added. No
absolute path enters the ingestion identity. The final catalogue is published
by directory rename. A repeat compares fresh and existing files while holding
the city directory lock. It verifies the current fill view and preserves the
files and pointers when the identity is unchanged.

Registration supplies the unchanged sea builder with the published catalogue
and the city’s 0 m fill profile. The Rotterdam exclusions cover the 1 km ring
outside the sheets. The ring is surface 4. The view and its horizon cache use
the existing view-ID naming convention. Raw horizons use the machine cache
namespace suffixed with the city ID for ingested cities.

## Planning and publication

The 1.1 region config selects a city before source-view creation. WGS84 corners
are transformed once per candidate, with XY axis order and local PROJ
resources. The selected operation description, stated accuracy and library
versions are recorded in the plan. The adapter receives projected corners and
passes the CRS, time zone, daylight reference and source line to V1/V2.
The engine continues to evaluate solar position at each owning tile’s
geometric centre. The fixed city reference governs the daylight frame list.

The city’s wall clock supplies the local calendar and folder labels. The
Hong Kong publication clock keeps fixed UTC+8. Explicit offsets must agree
with the chosen clock. Spring gaps and ambiguous naive fall times are
invalid. Daylight bounds are searched over the local calendar day in physical
time and sampled at wall-clock intervals. A repeated frame folder is rejected.

The publication format identity is `shade-map-publication-1.1`. It includes
the city record and the snapped bounds. Native pixels, cell GeoTIFFs, VRTs and
the raw fill-impact counterfactual retain the city’s CRS and 0.5 m transform.
The plan counts cells absent from the unfilled catalogue in the union of the
owning cells’ 1 km halos. The count reports coverage and does not change
admission. Region 1.0 retains Hong Kong, the raw default and its legacy
extent behavior.

The numerical and cache files retain their hashes. Hong Kong run IDs change
with the publication identity and engine code hashes. Horizon keys depend on
the unchanged kernel/cache files and the same native DSM sources.

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
