# V1 scientific policy and migration — SW-V1-POLICY-1.0

Frozen before numerical implementation on 2026-10-02. Contract `SW-V1-AC-1.0`,
SHA-256 `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
Planning baseline and actual starting commit:
`7c56760c854cb1e5138c8381a7b68d543b68cdef`; branch `feature`.

## Canonical pixels and spatial requests

The source EPSG:2326, north-up 0.5 m lattice is authoritative. The parity anchor
is the projected origin (E0,N0): column = Ewest / 0.5, row = -Nnorth / 0.5.
Origins must be integer addresses. Pixel centres are half a cell from edges.
The existing pixel-centred kernel receives these absolute addresses, including
negative halo addresses. Rays retain 0.25 m nominal steps, ties-to-even cell
rounding, the nominal slope denominator, cardinal-component snapping below
1e-14, and both nominal and cell-centre 1000 m radial cutoffs. The buffer remains
1000 m on every side. DSM gaps remain NaN. This changes the legacy *output*
parity anchor, not the ray model; odd output origins no longer redefine ties.

Native location requests preserve the user's coordinates as a selector and
return the containing source's exact bounds and geometric centre. Exact tile
names are also supported. Multiple selected tiles must form a complete aligned
rectangle; holes are rejected, rather than filled with unselected coverage.
Custom bounds or a custom centre/size are explicitly selected. Requested bounds
are preserved in the plan; resolved bounds expand outward to the source lattice
(up to one pixel per edge). Custom pixels outside source footprints retain
shade 255 / quality 1. A crop is an integer [column,row,width,height] window of
the resolved output and does not move scientific references. This intentional
change from legacy exactly-centred, fractionally shifted custom grids makes
the same native pixels available in every composition.

## Solar and uncertainty references

Every source tile has a fixed geometric-centre WGS84 solar reference. A composed
output uses each pixel's owning source tile, never the union centre. The solar
model remains `src/solar.py`'s NOAA fractional-year approximation, including its
refraction. This is a tile-centre approximation, not per-pixel astronomy.
Per-pixel comparisons and reference-boundary discontinuities are measured
separately. Correct invocation of this model does not establish its astronomical
accuracy. Primary descriptions: [fractional-year equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF)
and [NOAA calculator/refraction details](https://gml.noaa.gov/grad/solcalc/calcdetails.html).

The fixed low-sun threshold for each tile is
atan(max(0, max_valid_buffer_height - min_valid_native_tile_height) / 1000).
The native tile and its fixed rectangular buffer define these statistics,
including in custom/cropped requests. This is observed-height sensitivity, not
a bound on unseen terrain. No available support means no certified sunlight.
This change versions legacy whole-output statistics; it is not numerical noise.

Labels remain 1 shaded, 0 sunlit, 255 invalid/uncertain. Quality reasons:
0 valid; 1 missing target DSM (including uncovered custom pixels); 2 incomplete
sunward support; 3 distant-obstruction sensitivity; 4 nonpositive apparent
solar-centre elevation. A finite known horizon strictly greater than positive
apparent solar elevation proves shade despite missing support. Equality is not
shade; sunlight additionally requires complete support and elevation strictly
above the tile threshold. Apparent elevation <= 0 takes priority over blockers;
missing targets remain quality 1. Equality-neighbourhood counts use 1e-4 degrees
for reporting only, without altering classification. Sunrise sequences use the
existing -0.833-degree geometric-centre crossing at the fixed Hong Kong reference
22.3 N, 114.2 E (independent of requested area), so first/last daylight samples
can still have quality 4. There is no local-horizon or weather sunrise model.

## Time, directions, and execution

ISO timestamps preserve seconds and microseconds. Aware inputs normalize to UTC
and Asia/Hong_Kong. Naive inputs use the explicit timezone, default
Asia/Hong_Kong; ambiguous/nonexistent local times are rejected. An instant list
is explicit and ordered. Daylight dates use Hong Kong calendar days and a
positive integer clock-aligned minute interval. Duplicate physical instants are
rejected. V1 is bounded to 512 frames per request and one worker, preventing
full-year export and unbounded jobs.

The V1 default remains named `nearest5`: nearest 5-degree direction, half-bin
ties toward increasing azimuth, wrapping at 360. Development will assess the
candidate `nearest2_5` and direct unbinned directions. No interpolation of binary
frames or obstruction angles is used. Finite directions can miss narrow blockers;
neither denser sampling nor a direct DSM ray is physical/subpixel ground truth.

Planning reads metadata, streamed hashes and cache integrity only. It writes no
scientific or media files and invokes no horizon computation. Execution
rechecks dependencies to reject a stale plan, processes one native tile at a
time, and streams each frame into output rasters. JPG and MP4 are separate
switches, disabled by default; a single instant needs no video.

## Cache migration and recovery

Use only `data/processed/shade_v1/`, never the legacy namespace. Canonical native
tile geometry, intersecting buffered source content/metadata and external-mask
identities, algorithm/code versions and numerical settings define a spatial
identity. Paths, query dates, output membership, output directories and distant
files do not. Add/remove/change of intersecting sources changes this identity,
including newly available neighbors. Direction completes an entry identity.
Canonical tile statistics are stored with validated completed direction entries.
Each entry is checksum/structure/value checked. Exclusive per-tile writer locks,
temporary files and atomic rename plus a last-published complete manifest reject
conflicts and incomplete publication. Termination releases locks; completed
entries survive and partial entries are recomputed. Final-result hits are
validated and counted separately from directional reuse.

Old commands, source data, old caches and historical results retain their old
policies and remain readable. No old cache is scientifically compatible by
assumption. V1 may differ through canonical parity, tile references, fixed tile
thresholds and aligned custom bounds; these are explicit versioned changes.
No GUI/service, V2 orchestration, new downloads or deployment is included.
