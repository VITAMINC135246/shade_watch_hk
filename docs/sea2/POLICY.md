# SW-SEA-POLICY-2.2

This DSM-only layer implements the frozen [SW-B2.2 contract](../prompts/B2/CONTRACT_B2_2.md).
It fills literal NoData on the native catalogue lattice and its fixed 1,000 m
domain margin. The Hong Kong profile uses float32 0.00 m HKPD for every fill.
The engine consumes this view under `SW-V1-POLICY-1.0`.

## Domain and labels

A supplied pixel is NoData if it is non-finite or equals −9999. Every pixel in
an empty cell inside the domain is also NoData. Every such pixel gets
`h_sea_m` as its height. The builder preserves observed float32 bits.

An open component is 4-connected to the outside edge of the domain. A shore
pixel is a valid DSM pixel with a 4-adjacent NoData pixel. Low shore is at most
`h_sea_m + low_shore_margin_m`. For Hong Kong these heights are 0 m and 5 m.
Water requires an open component, a nearest low shore within 1,000 m, and
a low-shore distance at most 50 m greater than the high-shore distance.
Distances are Euclidean between pixel centres. The high-shore distance is
infinite where no high shore exists. The Hong Kong profile has no exclusion
zones.

| Surface | Meaning | Height |
| --- | --- | --- |
| 0 | Observed DSM | Raw value |
| 1 | Water label in a supplied tile | Fill height |
| 2 | Water label in an empty cell | Fill height |
| 3 | Enclosed NoData | Fill height |
| 4 | Open NoData outside the water rule | Fill height |
| 255 | Outside the domain | NoData |

The [output codes](../OUTPUT_CODES.md) define shade, quality, statistics groups
and dependency codes. Land combines surface 0 and 3, and Water combines
surface 1 and 2. Quality 3 and 4 remain shade 255. Fill-impact measures how
labels change against the raw DSM at the selected instants.

## Limitations

- At 0 m HKPD, the fill is about 1.4 m below the median DSM waterline. This
  slightly overstates near-shore water shade. Filled targets carry more
  uncertainty than observed land.
- Enclosed NoData includes land voids and inland water such as reservoirs.
  Where the real surface lies higher, the fill forms a pit. This can bias the
  filled target toward shade and nearby land toward sunlight when the fill
  removes a real obstruction. Fill-dependent labels are model results
  conditional on the assumed height.
- Filling can raise the distant-obstruction threshold and increase quality 3
  at low sun. Quality 3 marks sensitivity beyond the 1 km model boundary.
  Quality 4 marks nonpositive apparent solar elevation.
- The label parameters affect surface classes. Shade depends on the filled
  height. Low land near the DSM edge can receive a water label, especially
  river banks and fish ponds on the Shenzhen side.
- The four shifted `14NE15*` tiles declare the float32-minimum sentinel.
  Under the literal rule they remain observed. Regions needing those tiles
  are rejected.
- Piers, pontoons, boats and tide fall outside the model. The phase-1 engine
  covers Hong Kong. Observational accuracy is **NOT VERIFIED**. The result
  describes shade geometry. Cooling and ΔT require separate evidence.
