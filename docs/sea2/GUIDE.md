# Run B2.2 sea-filled shade maps

The [policy](POLICY.md) and [output codes](../OUTPUT_CODES.md) define how
B2.2 fills the DSM and how to interpret the three published layers.

## Build the view

Use the repository's engine environment and a machine config that points
to the raw DSM catalogue. The optional `sea_profile` defaults to
`hk_cedd_2020`.

```sh
.venv/bin/python -m tools.sea2 build --machine config/machine.local.json
```

The command writes a versioned view under
`data/processed/dsm_views/sea_fill_v2_2/<view_id>/` and updates
`current-hk_cedd_2020.json` after publication. It records the catalogue,
profile, build code, raster hashes and class counts. A missing view or a
changed catalogue inventory requires an explicit build.

## Plan and run

Copy the region config to a new name and set `"dsm_source": "sea-2.2"`.
Use a fresh output location when starting a development campaign. F handles
native grid alignment, daylight filtering and resume as described in its
[guide](../shade_map/GUIDE.md).

```sh
.venv/bin/python -m tools.shade_map plan --machine config/machine.local.json region.json
.venv/bin/python -m tools.shade_map run --machine config/machine.local.json region.json
```

Use `policies.sea` in the run manifest to interpret the surface layer.
`SW-SEA-POLICY-2.2` has Land (0 and 3), Water (1 and 2), and count-only
classes 4 and 255. For each group, report sunlit, shaded and uncertain
together, splitting the uncertain count by quality. Divide by the whole
group, including uncertain pixels. Report shade as a range from
`shaded / group` to `(shaded + uncertain) / group`. The sunlit range uses
the same formulas with the sunlit count. Report Land and Water separately.

## Measure fill dependence

After the matching F run completes, select its frames with four-digit Hong
Kong clock times. Omit `--times` for all published frames.

```sh
.venv/bin/python -m tools.sea2 fill-impact --machine config/machine.local.json region.json --times 0720,1230,1740
```

The command plans the selected frames on raw DSM, runs or resumes V2, and
writes diagnostic GeoTIFFs and a VRT at
`<output_root>/_diagnostics/fill_impact/<name>/<YYYYMMDD>/<HHMM>/`.
Read `fill_impact.json` or `fill_impact.csv` for dependency counts,
fractions over all Land and Water pixels, and observed-target transitions
from raw shade and quality to filled shade and quality. For Land,
`fill_dependent_land` is codes 1, 2 and 3 divided by the full Land count.
Present it separately from the main shade bounds.

## Validate the labels

The separate Python 3.12 tools environment uses the five packages from
`requirements.tools.lock.txt`. The map reader takes the frozen
`HydrographyPoly` coastline selection. The raster worker reports map
agreement, enclosed components and label sensitivity. These reports are
descriptive and have no pass threshold.

```sh
~/venvs/shade_watch_tools/bin/python -m tools.sea2.validate_ib5000 \
  --machine docs/sea2/evidence/b2_2/configs/machine.json \
  --scopes docs/sea2/evidence/b2_2/configs/validation_scopes.json \
  --work outputs/sea2_2_validation
```

For a different DSM profile, choose `h_sea_m` in that DSM's vertical datum.
It sets the fill height for water, enclosed NoData and other open NoData.
Low-shore margin, distance and preference change labels only. The fixed
1 km domain margin follows the model search. Phase 1 engine support is Hong
Kong only.

## Limitations

The 0 m fill lies about 1.4 m below the median DSM waterline, so near-shore
water shade is slightly overstated. Enclosed NoData includes voids and
reservoirs. A 0 m pit can overstate shade on the filled surface and can
overstate sunlight nearby if the true surface would block light. Filled
labels carry more uncertainty than observed land. Filling can increase
the quality-3 count at low sun. Quality 3 and 4 remain 255 at the model
boundary and at nonpositive apparent elevation respectively.

Water labels may include low land on the Shenzhen side, such as river
banks and fish ponds. The `14NE15*` tiles retain their literal
float32-minimum values and regions needing them are rejected. Piers,
pontoons, boats and tide fall outside the model. Observational accuracy is
**NOT VERIFIED**. The outputs describe shade. Cooling and ΔT require
separate evidence.
