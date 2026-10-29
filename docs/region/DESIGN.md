# Region adapter design — SW-RGN-AC-1.0

Implementation: `tools/region_request.py`; tests: `tests/test_region_request.py`.
`plan_region(corner1, corner2, crs=..., instants=..., ...)` is read-only.
WGS84 pairs are explicitly (latitude, longitude); HK1980 pairs are (easting,
northing). `project_corner` uses the exact V1 transformer construction.
CLI `plan` prints the plan; `write` emits V2-schema request files and a provenance
sidecar. A single request also includes a directly executable V1 command in the
sidecar. Neither action computes shade.

The engine's `_custom_grid` resolves bounds even above its request size cap;
this intentionally uses its existing snapping implementation. A fitting request
passes its original unsnapped bounds to `plan_shade`. If size or artifact limits
require splitting, catalogue tile-edge coordinates define the partition. Every
cell is planned independently. A test-only cap may force this same partition;
it cannot authorize a cut inside a native tile. A cell too large for that cap,
or a cell with no DSM, is rejected with its bounds and cause. Sparse catalogues
therefore need smaller caller rectangles when splitting would isolate gaps.
Admitted cells are packed in deterministic order into sequential batches, each
validated with `plan_batch`; this is feasible packing, not minimum-bin packing.
No budget is raised. Non-budget engine validation errors propagate.

Sidecar schema `shade-watch-region-request-1.0`: original corners, explicit CRS
and coordinate order, projected corners, transformer description, pyproj/PROJ
versions, requested and engine-resolved bounds/grid, native tile-edge lattice,
partition bounds/ids/tiles/plan keys/resources, batch membership/estimates and
request filenames. It is stored beside request files, outside engine output and
cache directories. Existing files are never replaced.

Planned evidence: R01 start/final byte hashes and clean src diff; R02 validation
and order tests; R03 five exact transformer comparisons; R04 three custom-plan
comparisons; R05 exact cell union/disjointness, all planners and unique horizon
inventory; R06 two daylight instants across two real tiles, logical-window vs V1
arrays/transforms; R07 sidecar tests and guide; R08 full unchanged suite log.
Real work uses only outputs/region_dev_* and cache region_dev. A watchdog bounds
real job wall time, process-tree RSS and total artifacts; the ledger includes
both the V2 run and V1 comparison.
