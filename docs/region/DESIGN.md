# Region adapter design — SW-RGN-AC-1.0 / 1.1

The first section is the historical 1.0 design. The 1.1 section below supersedes
its sparse-cell rejection and ordinary read-only planning when auto views are enabled.

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

# Amendment 1.1 implementation

Start: sea commit 86dbee663ccec8edcca7f123542a345fa13ca18b. Both frozen hashes
are recorded in evidence/v1_1/start.json; engine byte checks pass.

Use the engine's bounds snapping and temporal expansion unchanged. Partition on
catalogue-derived native edges; search rectangular guillotine partitions by
uncovered area then part count, admitting larger rectangles first. Empty cells
may lie inside an admitted rectangle and receive engine 255/1. A genuinely
unmergeable empty remainder is explicitly represented, never rejected/dropped.
All final rectangles must pass the engine. A bounded search falls back to
deterministic cuts on very large grids; it does not claim globally minimum bins.

Dates remain dates in emitted requests. Group only at complete-date boundaries
when the engine reports a frame cap. Keep geometry once in the sidecar and record
each temporal request separately. Batch admission uses pre-built ShadePlans;
attempt the whole list first, bisect only after budget rejection. Engine-local
request names are qualified by batch filename in the sidecar, preserving unique
adapter IDs and exact written-file batch IDs without editing engine plans.

The opt-in source view uses cached raster headers keyed by path/size/mtime,
selects every source intersecting any target's engine-defined 1 km halo, links
recognized auxiliary files too, and lets v1.index_sources hash/validate the view.
Needed shifted-origin 14NE15A/B/C/D inputs fail with the pending-ingestion-policy
message. No global engine patch or input correction. The opt-in plan action can
write only this immutable source view; ordinary plan remains free of writes.

R09: sparse fixture with interior/edge gaps, engine execution, added-tile variant,
residual read-back, exact occupancy and no empty engine requests. R10: hand-written
date key, >512 frames grouped by date, CLI. R11: three valid catalogue regions
compare full/view keys and timings; explicitly record the real raw catalogue's
known admission failure instead of claiming that it is a valid reference.
R12: completed monitored real two-owner batch with 130°/215° directions and independent
cold V1 reference cache (4 computed, 0 reused). Carry the original 391-second conservative charge into
the 1200-second campaign ceiling; R11 full-index timing is separately recorded
under the amendment's explicit exception. Keep all old evidence immutable.
