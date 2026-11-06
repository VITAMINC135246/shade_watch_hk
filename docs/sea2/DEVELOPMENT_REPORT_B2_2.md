# SW-B2.2 development report

Development started on `feature` at
`5b1da9be4246acac53b0488c3587df7884941108`. The starting tree contains
B2.0 candidate `5744e2301eea34f8bae05b9df3e14508425b8282`.
Before editing, the contract hash matched
`12d79865dda53ce1539560f4d79c047d3c80fd3fd974e4b9f643bf409580f2a9`.
The engine and adapter matched their pinned baselines. The F paths matched
the accepted F1.0 tree with the documented B2.0 additions. See
[start.json](evidence/b2_2/start.json).

The candidate fills every literal NoData pixel inside the fixed domain at
float32 0.00 m HKPD and stores the B2.0 labelling rule as surface classes
0 through 4. F reads the view via `sea-2.2` and publishes the expanded
surface allowlist. See [output codes](../OUTPUT_CODES.md), [policy](POLICY.md),
[guide](GUIDE.md) and [design](DESIGN.md).

## Single territory view

Final view ID
`8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1`.

| Surface class | Territory pixels |
| --- | ---: |
| 0 | 4,384,416,867 |
| 1 | 1,453,438,606 |
| 2 | 1,315,054,618 |
| 3 | 93,109,991 |
| 4 | 5,285,979,918 |
| 255 inside the domain | 0 |

The build initially omitted `provider.py` from the manifest's code hashes.
F's package initialization imports that module indirectly. Before any regional
plan, the campaign added it to the build's hash list and finalized the manifest
and pointer under the new ID. The single raster build supplied all tile and
surface hashes unchanged. The original and final identities and code hashes
are recorded in [metadata-finalization.json](evidence/b2_2/metadata-finalization.json).
The separate rebuild is **NOT VERIFIED**.

Coastline access was denied before the build and remained denied through
all regional plans, runs and fill-impact commands. The probe returned
`EACCES` and the campaign restored mode `0755` before map validation.
The synthetic comparison verified the same view ID, run ID, frame file
hashes and fill-impact metrics with both permissions. F's Git provenance
check may attempt an untracked directory listing. The scientific paths
read the DSM and profile. See [coastline-access.json](evidence/b2_2/coastline-access.json)
and [dsm-only-code-audit.json](evidence/b2_2/dsm-only-code-audit.json).

## Runs

The three configs and both read-only reference configs are in
[evidence/b2_2/configs](evidence/b2_2/configs/). All runs used 2026-01-07 HKT
and four V2 workers. Cheung Chau published 65 daylight frames. Central
published 08:30, 12:30 and 15:10. The five-class region published 08:00,
12:30 and 16:00. Before any shade run, the five-class target counts were
306,318 observed, 1,479,578 class 1, 1,114,582 class 2, 14,104 class 3
and 685,418 class 4. See [view-preflight.json](evidence/b2_2/view-preflight.json).

Both raw Cheung Chau plan IDs matched `35225fd`. The candidate's raw Central
plan matched the existing completed Central reference, which was reused
read-only. See [raw-plan-identity.json](evidence/b2_2/raw-plan-identity.json).

## Commands

Run from the repository root with the committed machine and region configs.
The evidence ledger records the exact commands, scopes and exit codes used
during development. The independent rebuild has its own scope and budget.

```sh
evidence=docs/sea2/evidence/b2_2
machine="$evidence/configs/machine.json"
.venv/bin/python -m tools.sea2 build --machine "$machine"
.venv/bin/python -m tools.shade_map plan --machine "$machine" "$evidence/configs/cheung_chau.json"
.venv/bin/python -m tools.shade_map run --machine "$machine" "$evidence/configs/cheung_chau.json"
.venv/bin/python -m tools.sea2 fill-impact --machine "$machine" "$evidence/configs/cheung_chau.json" --times 0720,1230,1740
.venv/bin/python -m tools.sea2 fill-impact --machine "$machine" "$evidence/configs/five_class.json"
~/venvs/shade_watch_tools/bin/python -m tools.sea2.validate_ib5000 --machine "$machine" --scopes "$evidence/configs/validation_scopes.json"
.venv/bin/python -m pytest tests
```

The [campaign launcher](evidence/b2_2/campaign.py), [readback](evidence/b2_2/audit_real.py),
[postcheck launcher](evidence/b2_2/postcheck.py) and
[listing audit](evidence/b2_2/inventory.py) document the measurements.

## Readback and report-only validation

The exhaustive readback checked all 7,128 cells. It verified 1,656 rewritten
supplied tiles, 1,654 raw links, and 3,818 synthetic tiles. Every partial
synthetic edge retained -9999 outside the domain. The exact tile inventory
and overlap scan found no synthetic overlaps with supplied tiles. All
four `14NE15*` files remain raw links with class 0 throughout.
See [view-readback.json](evidence/b2_2/view-readback.json).

The map reader ran in the five-wheel tools environment. Its pinned
engine-environment child rasterized the polygons at DSM pixel centres.
For cells outside or in neither map class, the report uses the joint
LAF/SEF bounding box as a coverage proxy. The northern listing uses the
northernmost 10 km of the raw catalogue plus the northern domain margin.

| Scope | Water pixels | Water inside LAF | False water / Water | Missed sea, class 3 | Missed sea, class 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Territory | 2,768,493,224 | 30,016,979 | 1.0842% | 100,829 | 3,629,051,495 |
| Cheung Chau halo | 34,494,878 | 27,683 | 0.0803% | 0 | 152,489 |
| Central halo | 11,010,914 | 155,351 | 1.4109% | 0 | 0 |
| Five-class halo | 15,248,801 | 0 | 0.0000% | 6 | 10,902,699 |

Central's Victoria Harbour share was 10,855,563 / 10,855,563 (100%)
within mapped sea NoData. Its DSM-only share was 11,010,914 / 11,010,914.
The territory report lists 73 northern cells with water-labelled pixels
in neither map class, and 184 false-water components above 2,500 pixels.
The DSM-only component report lists 90 enclosed components of at least
10,000 pixels with their observed shore height quantiles. All 27
sensitivity records are present, and the frozen setting reproduces the
baseline report for each halo. See [map report](evidence/b2_2/ib5000-report.json),
[class-3 components](evidence/b2_2/class-3-components.json) and
[label sensitivity](evidence/b2_2/sensitivity-report.json).

The validation figures describe agreement with iB5000 and have no pass
threshold. Observational accuracy is **NOT VERIFIED**. The filled height
and model limits are documented in the [policy](POLICY.md#limitations).

## Regional outcomes

Each published surface raster matched its view window. Across all 71 frames,
every quality-1 and quality-2 count was zero. All remaining shade-255 pixels
had quality 3. The quality-3 counts below sum pixels over frames.

| Region | Frames | Quality 1 | Quality 2 | Quality 3 | Quality 4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cheung Chau | 65 | 0 | 0 | 11,883,324 | 0 |
| Central | 3 | 0 | 0 | 1,023,106 | 0 |
| Five-class | 3 | 0 | 0 | 0 | 0 |

On observed land, all three comparisons had zero shaded-to-sunlit changes and
zero sunlit-to-non-sunlit changes. The filled-blocker and raised-threshold
attribution paths therefore had no losses to explain in these runs. The
regression records retain both thresholds per tile and every raw-255
transition by quality. The publication records give per-frame shade bounds,
sunlit bounds and counts over all Land and Water pixels.

At 12:30 Cheung Chau Land had 1,845,223 sunlit, 1,477,090 shaded and zero
uncertain pixels. Water had 3,861,088 sunlit, 16,599 shaded and zero
uncertain pixels. Water labels carry higher uncertainty under the 0 m fill.

| Five-class time HKT | Class-3 sunlit | Class-3 shaded | Class-3 uncertain | Fill-dependent Land |
| --- | ---: | ---: | ---: | ---: |
| 08:00 | 6,189 | 7,915 | 0 | 22.16% |
| 12:30 | 12,977 | 1,127 | 0 | 23.22% |
| 16:00 | 8,284 | 5,820 | 0 | 63.31% |

Cheung Chau's fill-dependent Land shares were 0.00%, 53.04% and 0.00% at
07:20, 12:30 and 17:40. Both diagnostics reconciled every dependency
pixel and all transition counts. The five-class repeat verified the saved
raw batch. The synthetic suite also verified recovery of a missing raw
mosaic. The first five-class and Cheung Chau readbacks looked up the V2
batch IDs in the wrong field. The corrected readbacks used the batch IDs
in the adapter sidecars and passed against the same outputs. The failed
readback attempts remain in the ledger and the `*-attempt1.txt` logs.

At each of 08:00, 12:30 and 16:00, the independent reference matched all
1,080 Cheung Chau water samples, including 120 within 8 m of observed
DSM heights of at least 10 m. In the five-class region it matched all
440 class-3 or class-4 targets and all 240 observed targets within 50 m
of a filled pixel per instant. The comparison used the documented
0.0001-degree equality tolerance. This checks numerical consistency.

## Resources and write scope

| Measurement | Observed | Cap |
| --- | ---: | ---: |
| One territory view build | 34.14 min | 60 min |
| Real-DSM jobs including plans, metadata finalization and readbacks | 41.54 min | 60 min |
| Report-only validation | 15.11 min | 30 min |
| Peak job RSS | 2.36 GiB | 12 GiB |
| Peak new artifacts | 5.17 GiB | 30 GiB |

The sleep-inclusive clock was `mach_continuous_time`. The jobs ran under
`caffeinate -dims`. The metadata finalization and preflight took 3.95 s,
charged in the real-DSM ledger. The protected listings show zero missing
or changed files and 23,506 additions within the new output namespaces
and permitted F and adapter entries. See the [ledger](evidence/b2_2/resources.jsonl),
[resource summary](evidence/b2_2/resource-summary.json),
[before listing](evidence/b2_2/protected-before.json) and
[after listing](evidence/b2_2/protected-after.json).

## Development matrix

| ID | Status | Evidence |
| --- | --- | --- |
| B2-16 | PASS | Starting SHA and verified contract hash, both locked environments, exact engine and adapter comparisons, cumulative F audit, and protected file listings. [Start](evidence/b2_2/start.json), [scope](evidence/b2_2/scope.json), [engine environment](evidence/b2_2/engine-environment.json), [tools environment](evidence/b2_2/tools-environment.json). |
| B2-17 | PASS | Build, plans, runs and fill-impact completed under the permission denial. The restored-mode readback verified the view and publications. The synthetic comparison checked exact identity and raster hash equality across permissions. [Access](evidence/b2_2/coastline-access.json), [code audit](evidence/b2_2/dsm-only-code-audit.json), [suite](evidence/b2_2/pytest-resume.txt). |
| B2-18 | PASS | Hand-computed synthetic low/high shore, preference, distance, connectivity, exclusion, empty-cell, literal-sentinel and domain-edge cases. The fixtures verify class and height behavior. [Suite](evidence/b2_2/pytest-resume.txt). |
| B2-19 | PASS | One-pass EDT agrees with tiled classification. Two F plans read identical surface classes over their overlap. [Suite](evidence/b2_2/pytest-resume.txt). |
| B2-20 | PASS | Every derived tile, raw link, class count, fill bit, observed bit, metadata field and literal exception checked. [View readback](evidence/b2_2/view-readback.json). |
| B2-21 | PASS | Exact empty-cell synthetic inventory, native lattice and NoData edge masks. Strict bounding boxes have zero overlaps. F accepted all three request-local views. [View readback](evidence/b2_2/view-readback.json), [five-class publication](evidence/b2_2/five_class-publication.json). |
| B2-22 | NOT VERIFIED | Manifest identity and build-code hashes, view-scoped cache, policy pair and distinct raw/sea request keys checked. A separate full rebuild is required. [Manifest finalization](evidence/b2_2/metadata-finalization.json), [view readback](evidence/b2_2/view-readback.json), [request keys](evidence/b2_2/request-plan-keys.json). |
| B2-23 | PASS | Registry and schema use `sea-2.2`. The cumulative publication diff is one allowlist change. Both raw plan IDs match F1.0. The unchanged F tests and six-code publication fixture pass. All five real surface codes matched. [Scope](evidence/b2_2/scope.json), [raw IDs](evidence/b2_2/raw-plan-identity.json), [suite](evidence/b2_2/pytest-resume.txt), [publication](evidence/b2_2/five_class-publication.json). |
| B2-24 | PASS | Quality 1 and 2 are zero in every frame. Shade 255 occurs only with quality 3 in these frames. [Cheung Chau](evidence/b2_2/cheung_chau-publication.json), [Central](evidence/b2_2/central-publication.json), [five-class](evidence/b2_2/five_class-publication.json). |
| B2-25 | PASS | All 65 Cheung Chau frames pass both observed-land gates. Per-tile thresholds and raw-255 transitions are present. [Regression](evidence/b2_2/cheung_chau-regression.json). |
| B2-26 | PASS | Central and the five-class region pass both observed-land gates. Class-3 shade distributions are recorded by frame. [Central](evidence/b2_2/central-regression.json), [five-class regression](evidence/b2_2/five_class-regression.json), [five-class classes](evidence/b2_2/five_class-publication.json). |
| B2-27 | PASS | Water, other filled, and adjacent observed samples exceeded 200 per group and instant, with zero mismatches. [Water rays](evidence/b2_2/cheung_chau-rays.json), [five-class rays](evidence/b2_2/five_class-rays.json). |
| B2-28 | PASS | Raw V2, independent dependency raster and VRT checks, group and transition reconciliation, schema, F folder hashes, precondition rejection and resume. [Cheung Chau](evidence/b2_2/cheung_chau-fill-impact-audit.json), [five-class](evidence/b2_2/five_class-fill-impact-audit.json), [resume](evidence/b2_2/five_class-fill-impact-resume.txt), [suite](evidence/b2_2/pytest-resume.txt). |
| B2-29 | PASS | Exact tools packages, wheel URLs/hashes, map reports, Victoria Harbour numerator/denominator, component list, north listing and all 27 sensitivity reports. [Environment](evidence/b2_2/tools-environment.json), [reader](evidence/b2_2/ib5000-reader.json), [map](evidence/b2_2/ib5000-report.json), [components](evidence/b2_2/class-3-components.json), [sensitivity](evidence/b2_2/sensitivity-report.json). |
| B2-30 | PASS | Both protected inventories agree for pre-existing files. All new files were inside authorized namespaces, and all measured categories stayed within budget. [Resources](evidence/b2_2/resource-summary.json), [write audit](evidence/b2_2/protected-after.json). |
| B2-31 | PASS | Full suite passed with 275 tests. The evidence index hashes each retained file. The scoped candidate is handed off in one local commit. [Suite](evidence/b2_2/pytest-resume.txt), [scope](evidence/b2_2/scope.json), [evidence index](evidence/b2_2/manifest.json). |

Independent acceptance remains separate. Observational accuracy is
**NOT VERIFIED**.
