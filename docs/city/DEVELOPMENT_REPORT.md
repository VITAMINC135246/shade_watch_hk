# SW-G1.0 development report

Branch `feature` started at `35314377986fcb9551db288a62b74d3b743121ef`,
parent `839e200b3bc8b53012bd3fc67627717b1ac44a4c`. The frozen contract
SHA-256 was `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef`.
Preflight matched all ten engine files to `356f611`, all tracked source, tools,
config and test files to `7707c51`, the twelve pinned code hashes, the two
Rotterdam sheet sizes and SHA-256 values, and the Hong Kong view ID. The
protected inventory and dirty paths are recorded in
[evidence/protected-before.json](evidence/protected-before.json).

The user directed the existing API/CLI publication integration case to use
`sea-2.2` and region schema 1.1. Its fixture now builds a tiny filled view.
The sparse-cell check verifies that the one synthetic cell carries fill
classes. The portability, summaries, resume, conflicts and prune checks
remain in the case. The full suite passed all 309 cases after this update.
[Test diff target](../../tests/test_shade_map.py), [Pytest](evidence/pytest.txt)

## Rotterdam registration

- `ingest_id` `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634`
- `view_id` `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843`
- 160 cells contain 214,048,125 valid pixels and 35,951,875 NoData pixels.
  The minimum and maximum are −10.9959 m and 204.6538 m NAP. The count
  below 0.00 m NAP is 106,321,205 (49.67%). Registration reported
  `fill_above_ground`.
- The view records 214,048,125 class 0, 18,211,404 class 1, zero class 2,
  17,691,564 class 3 and 156,048,907 class 4 pixels. The 156,000,000 ring
  pixels are all class 4.

The identifiers refer to data under `data/processed/dsm_catalogues/rotterdam/`
and `data/processed/dsm_views/sea_fill_v2_2/`.
[Registration output](evidence/nl0-registration.json)

## Verification matrix

| Item | Status | Evidence |
| --- | --- | --- |
| G1-01 | PASS | All 154,709 protected entries reconcile, and the audit found zero unexpected paths, pinned hash changes or user-file changes. The scope includes the user-directed integration fixture update described above. [Before](evidence/protected-before.json), [After](evidence/protected-after.json) |
| G1-02 | PASS | All 503 frames and 8,664 raster comparisons match, including frame labels, counts and all reference surface rasters. HK-1 ran at the engine gate before the city layer. [HK-1](evidence/hk1-comparison.json), [HK-2](evidence/hk2-comparison.json), [HK-3](evidence/hk3-comparison.json), [HK-4](evidence/hk4-comparison.json) |
| G1-03 | PASS | HK-2 through HK-4 planned and computed zero directions and reused 156, 156 and 148. The 5,583 existing cache entries have identical inventory hashes. [HK-2](evidence/hk2-plan.json), [HK-3](evidence/hk3-plan.json), [HK-4](evidence/hk4-plan.json), [Audit](evidence/protected-after.json) |
| G1-04 | PASS | Both legacy configs planned with the user’s machine file and retained the raw Hong Kong source. All 309 tests passed with the user-directed fixture update above. [Plans](evidence/legacy-plans.json), [Pytest](evidence/pytest.txt) |
| G1-05 | PASS | Both city profiles and the Rotterdam fill profile match the frozen JSON. Synthetic CLI tests reject broken and unsupported profiles before creating files. [Tests](../../tests/test_city.py) |
| G1-06 | PASS | CLI exit 2 and no writes for invalid inputs. Synthetic plans cover WGS84 auto-selection and ambiguous candidates. [Tests](../../tests/test_city.py), [CLI transcripts](evidence/rejections.json) |
| G1-07 | NOT VERIFIED | Synthetic sheets exercise bit preservation, sentinel replacement, padding, and the source and profile guards. All 160 real cell headers and aggregate counts match the contract. Independent comparison of all 250,000,000 raw pixels is pending. [Validation](evidence/nl-validation.json), [Tests](../../tests/test_city.py), [Raw hashes](evidence/protected-after.json) |
| G1-08 | NOT VERIFIED | Synthetic repeat preserves file hashes and mtimes and rejects altered files. The development manifests and hashes are available for comparison with a fresh registration and repeat in the review worktree. [Manifest hashes](evidence/nl-validation.json), [Tests](../../tests/test_city.py) |
| G1-09 | NOT VERIFIED | The real report matches the contract’s extrema, NoData count and 106,321,205 valid pixels below 0 m. Only `fill_above_ground` was raised. Synthetic tests exercise both warning thresholds. Independent recomputation is pending. [Registration](evidence/nl0-registration.json), [Tests](../../tests/test_city.py) |
| G1-10 | NOT VERIFIED | The builder’s supplied-tile bit checks completed and all view class totals reconcile. The Hong Kong view inventory, manifest hash and pointer hash match the baseline. The independent full-domain pixel check is pending. [Validation](evidence/nl-validation.json), [Audit](evidence/protected-after.json) |
| G1-11 | NOT VERIFIED | All 1,008 published GeoTIFF and VRT headers match the EPSG:28992 0.5 m grid. NL-2 records the local PROJ operation, 1 m stated accuracy and versions. Its bounds snap to `[92246.5, 437228.5, 92595.0, 437558.5]`. The reviewer’s projection is pending. [Validation](evidence/nl-validation.json), [NL-2 plan](evidence/nl2-plan.json) |
| G1-12 | NOT VERIFIED | NL-1 publishes 34 summer and 16 winter frames with the specified endpoints. NL-2 UTC instants and noon solar ranges match. The four clock-change offsets and invalid-clock rejections pass. Independent daylight recomputation is pending. [Validation](evidence/nl-validation.json), [DST plan](evidence/nl5-dst-plan.json), [Rejections](evidence/rejections.json) |
| G1-13 | PASS | NL-1, NL-2 and NL-3 complete with the city record, expected policy pair, defined codes and native-grid output. NL-2 used the Python default filled source. NL-1 and NL-2 have zero quality 1 or 2 pixels in every frame. Attribution checks covered 1,930 raster tag sets and 582 text or state files. [Validation](evidence/nl-validation.json), [Python invocation](evidence/campaign.py) |
| G1-14 | NOT VERIFIED | The development oracle matches 1,200 targets in four frames with zero disagreements. The sample includes 300 seam crossings and 200 below-zero observed targets within 50 m of fill out of 1,537,730 available. NL-1 contains only surface classes 0 and 3, so there were zero candidates adjacent to labelled filled water. The required water stratum and independent sample remain unverified. [Ray checks](evidence/nl1-rays.json), [Surface counts](evidence/nl-validation.json) |
| G1-15 | PASS | Five EPSG:28992 diagnostic frames reconcile by dependency code. The NL-1 publication listing and sealed manifest are preserved. The edge plan reports ten cells without DSM and NL-1 reports zero. Independent counterfactual recomputation remains NOT VERIFIED. [Diagnostic and edge checks](evidence/nl-validation.json), [Edge plan](evidence/nl5-edge-plan.json) |
| G1-16 | NOT VERIFIED | The metered campaign stayed within every budget. The first checksum-only preflight lacked RSS metering and was repeated inside the measured baseline audit. The clean-worktree guide replay remains for independent acceptance. [Ledger](evidence/resources.jsonl), [Guide](GUIDE.md) |

## Measured resources

| Resource | Observed | Ceiling |
| --- | ---: | ---: |
| Shade, read-only plans and result checks | 57.53 min | 90 min |
| Rotterdam registration and view build | 2.14 min | 20 min |
| Peak sampled process-tree RSS | 2.51 GiB | 12 GiB |
| Peak new data and output artifacts | 4.36 GiB | 20 GiB |

The two protected inventories took 1.53 minutes total. Timed jobs ran under
`caffeinate -dims`. The supervisor used sleep-inclusive wall time and sampled
each process tree. The tracked evidence and temporary audit files together
used under 30 MiB. The jobs used local inputs with PROJ network access disabled.
The full protected listings are retained in the local scratch baseline and
represented here by digests and counts.
[Resource ledger](evidence/resources.jsonl), [Supervisor](evidence/measure.py)

## Conclusions

- **Engineering acceptance** awaits independent review.
- **Numerical consistency** is established over the 503 Hong Kong regression frames
  and the 1,200 Rotterdam development ray checks.
- **Approximation error** for the 1 km cutoff, nearest-5° directions, the NOAA
  model and the filled heights has not been measured against observations.
- **Performance** met the measured development ceilings above.
- **Observational accuracy** remains NOT VERIFIED for both cities. Rotterdam’s surface labels remain unverified.
- **Production completion** covers the authorized development cases on the two
  Rotterdam sheets and the four Hong Kong regression regions.

The review worktree should use the exact local candidate commit and the two
IDs above. Review the explicitly authorized change to
`test_full_publication_api_cli_resume_prune` alongside the frozen scope.
[Independent acceptance prompt](../prompts/G1/INDEPENDENT_ACCEPTANCE_PROMPT.md)

## Limits of the results
Only 0.5 m DSMs are supported. Fill is fixed at 0.00 m in each city’s vertical
datum. Rotterdam water and voids use 0.00 m NAP. About 49.7% of valid pixels
and 44.8% of shore pixels are below that level, by up to about 11 m.
The filled surface can block sunlight from reaching adjacent low ground.
The model labels such pixels shaded. Fill-impact measures dependence on the
filled heights and cannot distinguish that false shade from true shade.
Where shores stand above 0 m, fill-dependent land may be wrongly sunlit,
as in Hong Kong.

Coverage ends at the two sheet boundaries. Results within 1 km of a sheet
edge depend on fill. The distant-obstruction threshold is
`atan((highest point in the tile and its 1 km buffer − lowest point in the tile) / 1,000 m)`.
It reaches about 12° in central Rotterdam. Winter-solstice noon reaches about
14.7°. Near tall buildings, most winter frames retain quality 3 wherever the
1 km search cannot prove shade.

The unchanged NOAA approximation has unverified accuracy at 52° N. WGS84
projection depends on the local PROJ operation and grid availability. Use
`projected` corners to reproduce the exact rectangle across machines. The
horizon cache identity contains fixed text naming EPSG:2326 for every city.
The two sheets do not verify their AHN release. Rotterdam surface labels and
observational accuracy in both cities remain **NOT VERIFIED**.
