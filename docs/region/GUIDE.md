# Two-corner region requests

Run from the repository root using `.venv`. Coordinates require an explicit
CRS. WGS84 pairs are **latitude longitude**, while HK1980 pairs are **easting
northing**. Corner order is immaterial.

```sh
.venv/bin/python -m tools.region_request plan --crs wgs84 \
  --corner1 22.339 114.262 --corner2 22.341 114.264 \
  --at 2026-01-07T14:31:27+08:00 \
  --dsm-dir data/raw/dsm/2020/D12.DSM.TIFF --output outputs/region_dev_example_wgs84

.venv/bin/python -m tools.region_request write --crs hk1980 \
  --corner1 844701.5 822197.5 --corner2 844713.5 822202.5 \
  --at 2026-01-07T14:31:27+08:00 \
  --dsm-dir data/raw/dsm/2020/D12.DSM.TIFF --output outputs/region_dev_example_hk1980 \
  --directory outputs/region_dev_example_requests
```

`plan` performs no computation or writes. `write` creates a fresh request
folder containing `region_request.json` and one or more `batch_NNNN.json` files.
Each batch can be planned/submitted/run with the existing `python -m src.v2`
commands in [the V2 guide](../v2/GUIDE.md). A single request also has a copyable
`v1_command` in the sidecar. The adapter never starts shade computation.

Python: `tools.region_request.plan_region(corner1, corner2, crs="hk1980",
instants=[...], dsm_dir=..., output_dir=...)`; pass the returned object to
`write_region(result, fresh_directory)` to save it.

The rectangle uses min/max **projected** corner coordinates in EPSG:2326. A
rectangle drawn in latitude/longitude is not exactly this rectangle. The engine
expands unsnapped bounds to its canonical pixel lattice; both requested and
resolved bounds are preserved. Transformation consistency does not establish
absolute geodetic accuracy.

Cost scales with intersecting native tiles and their required directions, not
rectangle area. A tiny new crop can still require complete native-tile horizons.
Large requests split only on tile boundaries derived from the current catalogue.
Sparse catalogues may leave a partition with no DSM; this is rejected explicitly.
The test-only Python cap cannot split inside a native tile. More than 4096 parts
is rejected. Multiple budget-admitted batches use a deterministic feasible
packing, not a claim of minimum batch count. Read a separate logical mosaic per
batch; a full-window read remains subject to the V1 area cap. Estimates are the
unchanged engines' estimates. No science, budgets, or cache identities change.
