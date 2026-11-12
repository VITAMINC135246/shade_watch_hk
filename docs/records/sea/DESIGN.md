# Sea view design — SW-SEA-AC-1.0

This describes the development candidate. It is not an acceptance declaration.

Separate tools environment: standard pyogrio/OpenFileGDB reader, pinned lock.
`tools/sea_view/extract.py` filters HydrographyPoly subtype 3, status E,
LAF/SEF; raw FGDB is read-only. Deterministic geometry repair, if necessary:
Shapely make_valid, retain polygonal components, record original validity and
output geometry hashes per feature; never silently drop geometries.
Engine environment: rasterio pixel-centre rasterization (all_touched=False),
LAF subtraction, float32 1.60 only at non-finite/-9999 DSM pixels, uint8 surface
classes. `scan.py` reads all coastal tile grids with a one-pixel halo for exact
8-neighbour shoreline samples. Distribution and coverage precede any view build;
median outside [1.30,1.90] stops work. Shifted grids are preserved.

`build.py` derives scoped targets plus 1 km source dependencies and missing
native cells. Synthetic names: SEA_E<integer_easting>_N<integer_northing>.tif;
collision checks are mandatory. Lossless DEFLATE compression, fixed settings,
no creation timestamps. Per-tile hashes cover values, georeferencing and surface
files. Manifest identity hashes canonical sorted strict JSON excluding timestamps
and view_id itself; includes all source hashes, dictionary hash, policy/h,
rasterizer/library versions, scope, file hashes, counts and synthetic flags.
Publish atomically under data/processed/dsm_views/sea_fill_v1/<view_id> only after
hashing and validation. `helpers.py` resolves policy and bounded surface windows.

S01: start/locks/source hashes and protected-file inventory. S02: exact standard
reader counts/CRS/geometry audit. S03: synthetic hole/sliver/edge/overlap cases and
halo counts. S04: bitwise non-fill preservation and exact float32 fill. S05:
missing-cell coverage/alignment/index acceptance. S06: one timed territory scan
with quantiles/coverage. S07: byte-identical engine, separated caches, reproducible
manifest/file identity. S08: 65-frame land transitions with threshold/blocker
explanations. S09: 200 water samples at each of three instants with ray-reference
comparison. S10: four explicitly diagnostic sensitivity variants. S11: Central
three-instant guard. S12: full/odd surface windows and effective-policy resolver.
S13: bounded scope and cumulative ledger. S14: synthetic and unchanged full suite,
POLICY/GUIDE/manifest/report; separate independent review remains pending.

Stop at reader acquisition failure, map-count mismatch, failed elevation gate,
or any other blocker. Do not implement later phases after a blocking gate.
Deliverable tools/tests/docs and the root tools lock are authorized by the prompt;
the new-directory-only list applies to runtime data and outputs.

Implementation refinements and assumptions:

- Synthetic coverage uses the fixed scoped targets' 1 km halos, not recursive
  halos of newly included support tiles. This follows S05 and prevents unbounded
  expansion. Native dimensions and lattice origin come from scoped metadata.
- Source catalogues for raw comparisons are read-only symlink subsets containing
  every relevant supplied halo tile. This preserves raw dependencies while
  avoiding unrelated shifted-origin tiles rejected by whole-catalogue indexing.
- S06 preserves each native grid. One-cell halo reads use the unchanged engine's
  nearest native addressing; the four shifted-origin sources are listed and are
  neither corrected nor included in the two output scopes.
- View staging is under outputs/sea_dev_build; complete immutable views are
  published under their hashes only after pixel/hash/index checks. Rebuilds
  compare every output/surface hash. Unchanged source copies retain original
  compression; rewritten outputs use deterministic DEFLATE.
- Diagnostics are limited to the first Cheung Chau target and its halo, use
  SW-SEA-DIAGNOSTIC-1.0, and remain under an explicitly diagnostic namespace.
  Band variants use native-centre Euclidean distance from strict sea into LAF;
  neither-class pixels are never added.
- S09 uses diagnostic_horizon at exact owning-tile nearest5 directions, 12x12
  canonical windows and independent cache-free reference classification. Water
  samples prioritize proximity within 8 m to observed surfaces at least 10 m
  high. This is numerical consistency only.
- V2 runs use two workers (diagnostics one), scientific rasters only. Dates,
  solar references, native target grids and nearest5 match the accepted baseline;
  optional media is deliberately disabled per the authorized scientific-only
  instruction.
