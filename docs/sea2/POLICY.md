# DSM-only sea surface — SW-SEA-POLICY-2.0

This candidate implements SW-B2.0 as amended by SW-B2.1. Independent acceptance
is a separate conversation. Engine policy remains SW-V1-POLICY-1.0.

The only classification inputs are the DSM catalogue and a sea profile. The Hong
Kong profile is `hk_cedd_2020`: sea level 0.00 m HKPD (float32), low-shore margin
5.00 m, maximum shore distance 1000 m, shore preference 50 m, connectivity 4,
and no exclusions. These values are frozen and are not tuned against the map.

The domain is the native catalogue lattice's bounding rectangle extended by
1000 m on every side. Missing cells are NoData. A supplied pixel is NoData when
non-finite or -9999, as specified in the frozen contract. A valid 4-neighbour of
NoData is a shore pixel; it is low when its observed height is at most 5 m HKPD,
and high otherwise. A NoData component is open exactly when 4-connected to the
outer domain edge, across cell borders. All other NoData is enclosed.

An open NoData pixel is water exactly when its pixel-centre Euclidean distance
to the nearest low shore is at most 1000 m, that distance is at most the nearest
high-shore distance plus 50 m, and it is outside every exclusion rectangle.
Missing shore types have infinite distance. Exclusions include their boundary
pixel centres; the Hong Kong profile contains none.

| Surface | Meaning | Land denominator |
| --- | --- | --- |
| 0 | Observed, finite DSM surface under the literal rule | yes |
| 1 | Filled water in a supplied cell | no |
| 2 | Filled water in an empty native cell | no |
| 254 | Open NoData failing the water rule | no |
| 255 | Enclosed NoData, including enclosed empty cells | yes |

Only classes 1 and 2 receive exactly float32 0.00 m. All other supplied value
bits and metadata remain unchanged. Classes 254 and 255 remain NoData and shade
255. Synthetic native tiles exist exactly for empty cells containing water.

One global view is built for each catalogue/profile pair. A canonical manifest
hash determines `view_id`; it includes the complete profile/hash, raw/auxiliary
content identities, rule/library versions, every tile/surface hash and class
counts. Timestamps and paths do not determine that identity. A separate atomic
pointer carries the current view and cheap names/sizes/modification-time inventory.
F records the view, profile hash and policy pair. Its engine cache namespace is
`sea_fill_v2_<view_id12>`.

The void-impact counterfactual changes only class-255 elevations, under explicitly
diagnostic view/work/cache namespaces. It is never a published shade result or
a void-filling policy. The whole land domain is class 0 plus 255. The daily
trigger is the mean frame fraction `(void_pixels + void_caused) / land_pixels`;
strictly more than 10% flags the need for a later decision. It does not authorize
land-void filling or the four-region solstice campaign.

iB5000 is report-only, read by a separate pinned pyogrio tools environment.
False-water, missed-sea, component, northern-boundary and sensitivity numbers are
map agreement reports without acceptance thresholds. No map geometry is read
by build, F plan/run, or void-impact.

## Required limitations

- h_sea = 0 m lies about 1.4 m below the DSM waterline median, so shade on
  near-shore water is slightly overstated.
- Low land at the edge of DSM coverage can be read as water. The Shenzhen side
  near low river banks or fish ponds is the known risk.
- Sea next to long high shores (cliffs, high seawalls), and water more than 1 km
  from a low shore, stay unfilled.
- Piers, pontoons, boats and tide are not modelled.
- Land voids remain 255 and are not shade.
- Sea-target labels are less certain than land labels.
- Regions needing the `14NE15*` tiles are rejected. Their transforms and unusual
  float32-minimum NoData metadata are preserved. The literal non-finite/-9999
  classification definition does not reinterpret that other finite sentinel;
  this is disclosed, not an ingestion correction.
- The phase-1 engine is Hong Kong only.
- Observational accuracy is NOT VERIFIED.
- Shade is not cooling and not ΔT.
