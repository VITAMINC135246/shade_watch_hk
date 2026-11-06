# B2.2 design

SW-B2.2 starts at `5b1da9be4246acac53b0488c3587df7884941108` on
`feature` and reuses the B2.0 implementation. The contract SHA-256 is
`12d79865dda53ce1539560f4d79c047d3c80fd3fd974e4b9f643bf409580f2a9`.
The engine baseline is `356f611`, the adapter baseline is `f5f24ac`,
and the accepted F1.0 baseline is `35225fd`.

## Catalogue, connectivity and fill

The domain is the native lattice bounding rectangle extended by 1,000 m
on each edge. This margin is fixed by the engine search distance. Domain-edge
cells are clipped for classification and stored at native size for DSM access.
The four `14NE15*` tiles use their lattice addresses for connectivity and
their actual centres for distances. Their float32-minimum sentinel follows
the literal NoData definition and the adapter still rejects requests needing
those tiles.

A streaming bottom-to-top cell pass joins 4-connected NoData components
across shared pixel edges and connects boundary components to an exterior
sentinel. A one-pixel halo supplies 4-adjacent observed shore pixels.
A second pass resolves open and enclosed labels and uses bounded Euclidean
nearest-shore queries. The 64-pixel distance bounds certify whole blocks
only when both inequalities hold over the block. Other candidates retain
per-pixel queries. The one-pass EDT fixture checks this rule independently.

The class identifies the kind of fill. All literal NoData inside the domain
gets the same float32 `h_sea_m`. Each empty cell gets a native-sized
`FILL_e<left>n<bottom>.tif` with -9999 outside the domain. Supplied tiles
with NoData are rewritten in lossless DEFLATE, preserving metadata and
observed bits. Other tiles are linked. Surface rasters cover the clipped
cells and aligned reads return 255 for the portion outside the domain.
See [output codes](../OUTPUT_CODES.md).

## Immutable view and F provider

The build stages and publishes under `data/processed/dsm_views/sea_fill_v2_2/`.
The manifest hashes the raw catalogue and auxiliaries, build code, profile,
tile outputs and surface rasters. It also records versions, literal-sentinel
exceptions and reconciled counts. Canonical manifest content excluding
timestamps and the ID determines the ID. The pointer pairs that ID with a
header inventory and is replaced atomically after the view is complete.

The `sea-2.2` provider verifies the pointer and inventory, binds each plan
to its immutable view, and checks selected dependency hashes. The run
manifest records both policies and the view ID. The cache namespace is
`sea_fill_v2_2_<view_id12>`. F publishes classes 0 to 4 and 255 through
the expanded surface allowlist. The raw plan identity and publication format
retain their F1.0 definitions.

## Fill-impact

Verify the matching complete F publication and the requested times. Plan the
same frames on the raw catalogue through the adapter. V2 execution persists
batch plans and state under `outputs/sea2_2_diagnostic_work/<name>-<id12>/`
with a dedicated `sea2_2_fill_impact_<id12>` cache. The identity includes
the run, raw dependencies and the selected frames. Read counterfactual
logical windows and publish dependency rasters and metrics to the separate
diagnostics tree. The Land and Water denominators include all their pixels.
The observed-target transition table retains both runs' shade and quality.

## Reports and resources

The report-only reader runs in the pinned tools environment and exports
iB5000 polygons. The raster worker uses the engine environment to rasterize
at pixel centres and compute class and component statistics. The nine
sensitivity variants share the same domain and openness. See the
[policy limitations](POLICY.md#limitations).

The measured campaign uses a sleep-inclusive wall clock under
`caffeinate`, separate caps for real jobs, the single build and validation,
and guards for process-tree memory and new files. The pre/post protected
inventories and coastline access probe are retained in the evidence.

## Verification map

| Item | Test or campaign evidence |
| --- | --- |
| B2-16 | Ancestry, contract, locks, pinned blobs, allowed and cumulative F diffs |
| B2-17 | Coastline-denial probe, measured campaign and runtime import audit |
| B2-18 | Hand-computed label and height fixtures including partial and empty cells |
| B2-19 | One-pass versus tiled rule and overlap reads |
| B2-20 | Exhaustive fill, observed bits, metadata and manifest reconciliation |
| B2-21 | Exact synthetic inventory and request-local engine indexing |
| B2-22 | Manifest/code/cache/plan identity, independent rebuild deferred |
| B2-23 | Six-code publication, unchanged F tests and raw plan identity |
| B2-24 | Per-frame and per-class shade/quality counts in three regions |
| B2-25 | Cheung Chau observed transitions, thresholds and blocker attribution |
| B2-26 | Central and five-class transitions and class-3 shade distribution |
| B2-27 | Independent direct rays for water, other filled and nearby observed targets |
| B2-28 | Raw counterfactual, independent dependency readback and resume |
| B2-29 | Pinned reader provenance, iB5000, class-3 components and sensitivity |
| B2-30 | Protected inventories, allowlisted writes and resource ledger |
| B2-31 | Full synthetic suite, docs, evidence index and scoped local commit |

## Limitations

The 0.00 m HKPD fill sits about 1.4 m below the median DSM waterline.
It slightly overstates shade near the waterline. Class 3 includes land
voids and reservoirs. Filling them can form pits that favor shade on
filled targets and sunlight nearby if the actual surface would block
light. Filled targets carry more uncertainty than observed land.

The label parameters can change the surface class, including water
labels on low land near Shenzhen river banks and fish ponds. Only the
fill height affects the shade calculation. Filling can raise the
distant-obstruction threshold at low sun. The unchanged engine leaves
quality 3 and 4 as shade 255, recording sensitivity beyond 1 km and
nonpositive apparent elevation respectively.

The literal float32-minimum treatment leaves the four `14NE15*` tiles
in the view. Requests that need them are rejected. Piers, pontoons,
boats and tide fall outside this phase-1 Hong Kong model.
Observational accuracy is **NOT VERIFIED**. Cooling and ΔT require
evidence beyond these shade results.
