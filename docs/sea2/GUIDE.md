# Build and use the DSM-only sea surface

Run commands from the repository root with the existing `.venv`. No dependency
installation or download is required. Read POLICY.md for the frozen rule and
limitations; this development candidate still needs independent acceptance.

Copy `config/machine.example.json` to `config/machine.local.json`. Set the raw
DSM catalogue and a new repository-local F `output_root`. The optional machine
setting `sea_profile` defaults to `hk_cedd_2020`. Build explicitly before F use:

```sh
.venv/bin/python -m tools.sea2 build --machine config/machine.local.json
```

This reads the complete DSM catalogue, classifies all supplied/empty cells, and
writes only the new `data/processed/dsm_views/sea_fill_v2/` namespace. It may take
substantially longer than a regional plan. A second invocation performs a full
rebuild and compares hashes. The `current-hk_cedd_2020.json` pointer includes a
cheap source inventory; changing a source or the profile requires another build.

Copy a region config, choose a distinct name, and set `"dsm_source": "sea-2.0"`.
Use the unchanged F entry points:

```sh
.venv/bin/python -m tools.shade_map plan --machine config/machine.local.json config/regions/my_sea_region.json
.venv/bin/python -m tools.shade_map run --machine config/machine.local.json config/regions/my_sea_region.json
```

The frozen F1.0 publisher currently rejects surface classes 2 and 254. A plan
can succeed and V2 can finish the engine work, but any such frame stops during
publication. This is an observed B2-08 failure, not a supported published
result. `checks --engine-work` reads completed V2 work for numerical evidence;
it does not publish or turn an incomplete F run into a complete one. See the
development report for the exact check and the scope of a proposed amendment.

Execute only regions and dates separately authorized by the user. The B2
development scope is Cheung Chau on 2026-01-07 daylight plus Central at 08:30,
12:30 and 15:10 that day. These examples do not authorize additional computations.
Raw mode remains `"dsm_source": "raw"`. Surface classes are 0 observed, 1/2
water, 254 open unfilled and 255 enclosed. Read them together with shade/quality;
255 is not shade. The F manifest retains the policy pair and immutable view ID.

## Measure the effect of land voids

First complete the matching F sea run, then give the identical config:

```sh
.venv/bin/python -m tools.sea2 void-impact --machine config/machine.local.json config/regions/my_sea_region.json
```

The command refuses missing, incomplete, stale or mismatched policy runs with
exit 2. It verifies the original run, fills only enclosed class-255 cells in an
explicitly diagnostic scope-limited view, and runs identical frames through the
unchanged adapter/V2. It retains durable batch state and resumes on repetition.
It writes nothing inside the original F run folder and publishes no diagnostic
shade rasters as results.

Reports are `<output_root>/_diagnostics/void_impact/<name>/void_impact.{csv,json}`,
inside the repository. Work remains in `outputs/sea2_diagnostic_work/`; caches
and views contain `sea_voidfill_v2_diagnostic` in their names. The report counts
voids themselves and observed land that leaves Quality 2 in the counterfactual,
split into sunlit, shaded and Quality 3 outcomes. Other Quality 2, Quality 3,
sunlit and shaded counts are separate. Quality 4 is retained when present so the
whole-land partition still reconciles. All fractions use class 0 plus 255.

For each date, `mean_void_attributable_fraction` averages the frame fractions.
`exceeds_10_percent` means strictly above 0.10. This is evidence for a later
void-filling decision. The four-region winter/summer measurement is not part of
this package and has not been authorized here.

## Report agreement with iB5000

Only the validator uses coastline data. Use a working external tools environment
matching `requirements.tools.lock.txt`; never install the vector reader into the
engine environment. Set `TOOLS_PYTHON` to that environment's interpreter:

```sh
"$TOOLS_PYTHON" tools/sea2/validate_ib5000.py \
  --machine docs/sea2/evidence/configs/machine.json \
  --scopes docs/sea2/evidence/configs/validation_scopes.json \
  --work outputs/sea2_validation_20261104
```

Use a new work namespace for a new campaign. pyogrio/OpenFileGDB reads
HydrographyPoly subtype 3/status E, repairs invalid polygonal geometry
deterministically, and clips per-cell report polygons in the tools environment.
A measured engine-environment child performs pixel-centre rasterization and
classification-only sensitivity. The reports explicitly distinguish outside the
joint feature bounding box from neither LAF nor SEF inside it; that box is not
claimed to be an authoritative coverage polygon. The northern listing covers
the raw catalogue's northernmost 10 km, with all other uncovered cells also
listed. False-water components join across cell borders. The frozen profile is
never changed by any report.

The historical temporary reader environment had been purged before this
development run: its package directories were empty. No complete offline pinned
reader was available and downloads were forbidden. Its real-data validation is
therefore NOT VERIFIED; see the development report. The entry point checks all
locked package versions before opening any source and refuses an unavailable or
different environment with exit 2.

## Resource measurement

Use the delivered watchdog around every real-DSM command, including plans:

```sh
.venv/bin/python -m tools.sea2.resources --label my-plan --category real -- \
  .venv/bin/python -m tools.shade_map plan --machine config/machine.local.json config/regions/my_sea_region.json
```

Use `--category build` for the separately capped builds, and one shared ledger
for cumulative real-job time. `--protected-before` enables the artifact-byte
guard using a local before-inventory; `--log` retains command output without
an additional process. The OS must permit process inspection before launching.
The development contract caps real jobs at 60 minutes, each of two builds at
60 minutes, memory at 12 GiB and new artifacts at 30 GiB. Exhausted work is NOT
VERIFIED, and the watchdog does not authorize a new computation scope.

## Another DSM profile

A profile records its own vertical datum and sea level, low-shore margin,
distance limit, preference, connectivity and optional rectangle exclusions in
that DSM's CRS. Confirm the vertical datum before selecting h_sea; 0 m HKPD is
specific to this dataset. Changing a profile or exclusion changes its hash/view.
Hong Kong exceptions or frozen parameter changes require a new agreed contract.
The surface rule is parameterized, but the unchanged phase-1 shade engine is
Hong Kong only; this is not engine portability to another city.

## Limitations

h_sea = 0 m lies about 1.4 m below the DSM waterline median, so near-shore water
shade is slightly overstated. Low land at coverage edges, especially Shenzhen
river banks or fish ponds, can be read as water. Sea next to long high cliffs or
seawalls, and water more than 1 km from low shore, stay unfilled. Piers, pontoons,
boats and tide are not modelled. Land voids remain 255 and are not shade.
Sea-target labels are less certain than land labels. Regions needing `14NE15*`
are rejected. The phase-1 engine is Hong Kong only. Observational accuracy is
NOT VERIFIED. Shade is not cooling and not ΔT.
