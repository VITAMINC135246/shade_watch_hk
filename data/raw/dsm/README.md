Place original DSM GeoTIFF tiles and source metadata here. Treat these files as read-only inputs; they are ignored by Git.

Current user-supplied layout (2026-10-08 inventory):

- `2020/D12.DSM.TIFF/`: 3,310 native 2020 GeoTIFFs, 26,043,475,302 bytes.
- `2020_HKUST_Around/D12.DSM.TIFF/`: preserved original 19-file calibration set.

All inventoried headers report EPSG:2326, 0.5 m pixels, 1500 × 1200 cells.
Four headers have approximately 0.000000094 m origin offsets; strict footprint
intersection detects seven sliver-overlap pairs. V1/V2 deliberately reject
ambiguous overlaps. This is a pending V3 ingestion issue, not permission to edit
raw transforms or silently resample inputs. The seven predeclared regional pilot
support sets do not include those pairs. Full raster validity, authoritative land
boundary coverage and vertical datum confirmation remain separate checks.

Historical V2 calibration/reacceptance explicitly uses the 19-file root. The
new-data V2 supplement uses a read-only 29-file support view from the full root.
Adding support files changes scientific identities; never mix old-cache evidence
with new-input claims. Raw/source metadata remain ignored and were not uploaded.
