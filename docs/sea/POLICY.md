# SW-SEA-POLICY-1.0 — frozen, pending development and independent acceptance

This document records the frozen contract, not an acceptance declaration.
The engine remains SW-V1-POLICY-1.0. Sea support is a separate derived-data
policy, identified with its manifest and view_id.

Sources are the read-only CEDD 2020 DSM (HKPD heights, acquired 2019–20) and
2026-10-12 Lands Department iB5000 HydrographyPoly, FEATURESUBTYPE=3,
DATASTATUS='E'. LAF identifies land and SEF sea. Rasterize polygons with holes
on each native 0.5 m grid using rasterio's pixel-centre rule, all_touched=False.
Fill only DSM non-finite/-9999 pixels in SEF and outside LAF. Store exactly
float32 +1.60 m HKPD, with zero coastline tolerance. Every other supplied pixel
and its georeferencing, size, type and NoData value remain unchanged. Do not
correct the four known shifted-origin source tiles.

Missing native cells intersecting the scoped targets' 1 km halos receive a
SEA_ synthetic tile only if they contain sea pixel centres; no overlap with
supplied tiles is allowed. Synthetic unknown pixels stay NoData. Surface rasters
are uint8: 0 observed DSM, 1 policy-filled water, 255 no surface. Sea pixels are
targets and participate in obstruction/support using the unchanged classifier.

A canonical manifest records policy and height, source and dictionary hashes,
DSM identity, rasterization and library versions, scope, source/output hashes,
fill counts and synthetic flags. view_id hashes that manifest excluding
timestamps and the view_id field. Cache namespace is sea_fill_v1_<view_id>.
Engine result tags remain SW-V1-POLICY-1.0; manifest resolution reports the pair.
Identical inputs must reproduce the ID and output hashes. Compression is
lossless DEFLATE with fixed settings. Historical caches are never reused by
assuming policy compatibility.

The territory-wide median of DSM-valid pixels 8-adjacent to fill must lie in
[1.30,1.90] m before building views. Failure stops development; h is not retuned.
Only the frozen Cheung Chau and Central scopes may be built. Height/tolerance
variants are Cheung Chau diagnostics in separate labelled namespaces.

Limitations: boats and pontoons are absent; tide is not modelled. The 2026 map
and 2019–20 DSM may disagree after reclamation. Piers and coastal slivers inside
LAF remain unknown; reservoirs are unchanged. No map coverage, or neither class,
means unknown. Sea-target labels are less certain than land labels. Shade is not
cooling and is not a temperature change. Numerical agreement cannot establish
observational accuracy. Neither land nor water labels are observationally
validated by this work. No territory view, V3 use or release is authorized.
