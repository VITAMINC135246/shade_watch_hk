# B2.0 design — SW-B2.0 amended by SW-B2.1

Implementation starts at `05c66ab379d87868a787ae78cdecbfb918c1730e` on
`feature`. The contract hashes were verified before repository edits:
`b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`
and `18a09995cbbd1cca659c9a548aad9a0cb45c942668a58ce17146d371f9f8450d`.
The accepted F dependency is `35225fd9547a00e4df202e7ab30204c633b2c845`.
The ten engine files and the A1.1 adapter were compared before editing.

## Catalogue and connectivity

The catalogue has one uniform native cell lattice. The exact rectangular domain
is its bounding box extended by the profile's maximum distance in each direction.
Edge cells can therefore be partial cells. Native source arrays and transforms
are never shifted. Only component addressing rounds the four documented
`14NE15*` offsets to lattice addresses; those dependencies remain rejected by
the unchanged adapter.

Distances retain the actual subpixel native centre offsets, in float64, for
both shore and target pixels. Only component addresses and shared-border
adjacency use the rounded lattice. A dedicated exact-1000-m fixture catches
accidental rounding of either the shore or target centre.

Header inspection found that those same four tiles declare float32 minimum as
NoData, while the other 3,306 declare -9999. Supplied NoData metadata is preserved
per tile; synthetic cells use the ordinary native -9999 sentinel. Classification
follows the contract's literal non-finite-or--9999 definition, including on the
four rejected tiles. Their other finite sentinel is not silently reinterpreted
or converted. This quirk is disclosed in the development evidence; regions
depending on those tiles remain unavailable.

The first pass labels NoData separately in each cell with 4-connectivity.
Component IDs are joined across shared border pixels by union-find; components
touching the domain boundary join the exterior sentinel. Only a row of borders,
the component table, and sparse shore coordinates need to remain in memory.
The second pass repeats the deterministic local labelling and resolves each
component through the global table. Empty cells participate in both passes.
This distinguishes enclosed empty cells from exterior water without a
territory-sized in-memory raster or a request-dependent flood fill.

## Bounded exact distances

Shore pixels are found with a one-pixel DSM halo and 4-neighbour adjacency.
Their centre coordinates and observed heights are retained as sparse points.
For each output cell, distance searches include shore points in the window plus
`max_shore_distance_m + shore_preference_m` on every side. Exact Euclidean
`cKDTree` queries are evaluated in bounded chunks. A farther low shore cannot
make water; a farther high shore cannot veto a qualifying low shore. Missing
shore classes have infinite distance. This implements the same rule as the
small-fixture one-pass Euclidean reference.

The first build exposed the cost of per-pixel offshore queries. The equivalent
implementation now certifies 64-pixel blocks using the 1-Lipschitz bound on
distance: centre distance plus/minus the farthest pixel radius. A block is
assigned only if those bounds prove the frozen inequalities everywhere; all
uncertified candidates retain exact per-pixel queries. Large-fixture EDT
comparisons cover this branch. The first pass also shares one halo read between
local labelling and shore extraction. Neither optimization changes the rule.

## Immutable view and provider

Build stages are inside the new `sea_fill_v2` namespace. Supplied water-free
tiles are byte-identical copies or links. Filled tiles preserve all other float32
bits, dimensions, CRS, transform and NoData, with deterministic DEFLATE encoding.
Empty water cells get native-sized `SEA_e<left>n<bottom>.tif` files. Every domain
cell has a uint8 surface raster, even when it has no engine tile.

The manifest contains the full profile/hash, all source and auxiliary hashes,
rule/library versions, tile/cell hashes and counts, and reconciled totals.
Its canonical content, excluding `view_id` and timestamps, determines `view_id`.
The atomic `current-<profile_id>.json` pointer also records a cheap catalogue
inventory of names, sizes and modification times. A full rebuild recomputes the
view before comparing all hashes; it is not a shortcut to an existing view.

`SeaSource` lives in `tools/sea2/provider.py`. F changes are restricted to its
registry entry, the two config schemas/defaults, the example machine and GUIDE.
The provider validates the pointer, profile and inventory, supplies the new cache
namespace/policy pair/identity, and reads the immutable surface independently of
which engine tiles own the output. Selected records retain their bound view for
later publication. F planning, runner, publication and identity stay unchanged.

The accepted publisher hardcodes surface 0/1/255 despite its extensible schema.
The five-class integration fixture exposed a real B2-08 failure. The frozen
scope does not permit changing that check. For numerical checks, an explicit
`--engine-work` mode reads completed V2 mosaics without publishing them. It
verifies the F manifest seal, work ownership, adapter hash and successful batch
records, and identifies that source separately from published F output.

## Counterfactual diagnostic

Require and verify a complete matching F sea run before creating diagnostic work.
Build an immutable, scope-limited copy with only class-255 pixels changed to the
profile's float32 sea level. Enclosed empty cells need diagnostic native tiles
to represent that same change. Selected sea tiles and all other pixels retain
their values. The manifest is explicitly labelled `diagnostic`.

Plan the identical frames through A1.1 and execute durable V2 batches under
`outputs/sea2_diagnostic_work/<name>-<id12>/` and the separate diagnostic cache.
Retain batch definitions/state for resume. Read counterfactual logical windows
without publishing their rasters. Metrics partition the whole land domain
(class 0 plus 255), split void-caused changes by outcome, and report daily means
against 10%. Record quality 4 separately if present to preserve reconciliation.
Reports live inside the F-owned output root's `_diagnostics` directory, never
inside the original run folder.

## Validation and resources

Only the separate validation entry point opens iB5000, using the pinned tools
environment and standard pyogrio/OpenFileGDB. It exports deterministic repaired
polygons to a new validation work folder; an engine-environment raster worker
uses pixel-centre rasterization and the sea surface. False-water components join
across cell borders. Counts include the territory, both target rectangles and
their halos, per-cell unclassified map coverage and a separately defined northern
boundary listing. Sensitivity reuses global openness but recomputes local shore
distances for all nine frozen parameter combinations on the two halos only.

All real-DSM commands, including read-only plans, run under an external watchdog
recording direct-child resource usage and sampled RSS for every descendant.
Real jobs share 3600 seconds; each of the two builds has its own 3600-second cap;
process-tree memory is capped at 12 GiB, all new artifacts at 30 GiB. Protected
file inventories are taken before/after. Coastline permissions are restored in
a `finally` path after the DSM-only experiments. Exhausted evidence is marked
NOT VERIFIED, never inferred or used to change the frozen parameters.

## Verification map (written before implementation)

| Item | Tests and retained text/JSON evidence |
| --- | --- |
| B2-01 | start/ancestry, both lock/environment records, pinned hashes, final scope diff |
| B2-02 | permission-denied proof; build/rebuild, plans, runs and diagnostic without map access; code audit |
| B2-03 | hand-computed open/low/high/preference/range/enclosed/empty/diagonal/border/exclusion fixtures |
| B2-04 | one-pass versus tiled fixture, overlapping surface windows |
| B2-05 | every derived tile bit/metadata check, unchanged-file hashes, totals |
| B2-06 | exact synthetic inventory, names/lattice/no overlap, adapter index acceptance |
| B2-07 | two full builds and all hashes, cache/policy/plan identity checks |
| B2-08 | unchanged F tests; both amendment raw-plan comparisons; published surfaces |
| B2-09 | all 65 land transitions, old/new thresholds and blocker explanations |
| B2-10 | Central raw/sea 08:30, 12:30, 15:10 guard and harbour counts |
| B2-11 | at least 200 water targets at each of those times, including tall-structure neighbours |
| B2-12 | diagnostic precondition/resume/schema, only-255 fill, per-frame land partition, no original-run writes |
| B2-13 | standard-reader provenance, territory/scopes/components/north/voids, nine sensitivity variants |
| B2-14 | protected inventories, authorised-scope ledger, wall/RSS/disk caps |
| B2-15 | synthetic and full unchanged suite, four documents/limitations, evidence manifest, one local commit |
