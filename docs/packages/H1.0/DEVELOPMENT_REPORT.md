# H1.0 development report

The H1.0 layout and name migration was developed on branch `feature` under SW-H1.0 and SW-H1.1. The independent checks in the matrix remain pending.

## Preflight

The starting commit was `dc7ad088cc3739aa4d54f6415088629328f92140`. Its parent was `fda9985a259bff640237d4fb80c9c0a7e3fba0a8` and `pre-h1.0` resolved to `cfb6e3c52001103a206c256c1af46bcdce30f01c`. There were no staged or unstaged tracked changes. The only untracked entry was `archive/`.

| Preflight input | SHA-256 |
| --- | --- |
| `docs/packages/H1.0/DEVELOPMENT_PROMPT.md` | `4f03256a745df353a2d05818a1d0843b10576d67e791188a1bbfe2bf262c7c0f` |
| `docs/packages/H1.0/CONTRACT.md` | `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c` |
| `docs/packages/H1.0/AMENDMENT_1.md` | `b07551ce74958863e709625a980e0d727f05e3382902d566771f0830b22976ea` |
| `docs/CONVENTIONS.md` | `75377354fd5b5bc13ab213ef024ca679e818eda24d78f64e36f113d05224929f` |
| `archive/baseline_h1_0_20261112/listing.tsv` | `c82d5ed7644927d8384177254ccba4960117d5d482ebd1a2e27f13571b6b5afb` |

The eight tracked additions from `8d7a0d3` were the only differences from `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d` in the four checked source, tool, config and test trees. The processed-tree inventory and both existing view pointers matched the contract. All 168,088 planner entries matched before the moves. The five extra entries were the excluded planner baseline directory and its four files.

## H1-01 through H1-14

| Item | Status | Development evidence and remaining reviewer checks |
| --- | --- | --- |
| H1-01 | PASS | One candidate on the amended starting commit. The staged rename and content diff were reviewed, and the frozen planning files, prompts, contract, amendment and conventions match their starting blobs. [tracked_before.sha256](evidence/tracked_before.sha256), [protected_code_checks.json](evidence/protected_code_checks.json) |
| H1-02 | PASS | The three cache-key files are byte-identical. The source of `fingerprint` and `profile` matches the starting commit. [protected_code_checks.json](evidence/protected_code_checks.json) |
| H1-03 | NOT VERIFIED | All six developer layout tests passed. The independent layout script is a reviewer check. [tests_full.txt](evidence/tests_full.txt) |
| H1-04 | PASS | The 465 moved records and the separately moved estimator match their starting blobs. [records_manifest.json](evidence/records_manifest.json), [protected_code_checks.json](evidence/protected_code_checks.json) |
| H1-05 | NOT VERIFIED | All protected planner files and symlinks matched at their new paths. The developer hashed 300 Hong Kong raw tiles and both Rotterdam sheets. The reviewer selection and comparison are pending. [inventory_after_regression.json](evidence/inventory_after_regression.json), [hong_kong_view_comparison.json](evidence/hong_kong_view_comparison.json), [rotterdam_view_comparison.json](evidence/rotterdam_view_comparison.json) |
| H1-06 | PASS | The collected IDs match after the seven authorized retirements and six layout additions. The full retained suite passed. [test_ids.json](evidence/test_ids.json), [tests_full.txt](evidence/tests_full.txt) |
| H1-07 | PASS | Frozen configs, schema names and policy IDs were preserved. Both R-8 plans use Hong Kong raw. All eight G1-06 rejection cases matched the prior exit status and diagnostic. [protected_code_checks.json](evidence/protected_code_checks.json), [cli_rejections.json](evidence/cli_rejections.json) |
| H1-08 | NOT VERIFIED | The developer verified every Hong Kong tile and surface SHA-256, totals, manifest fields and pointer against the accepted view. The independent hash comparison is pending. [hong_kong_view_comparison.json](evidence/hong_kong_view_comparison.json) |
| H1-09 | NOT VERIFIED | The developer verified Rotterdam catalogue and view hashes and the allowed JSON differences. Fresh registration in the reviewer worktree and its independent comparison are pending. [rotterdam_view_comparison.json](evidence/rotterdam_view_comparison.json) |
| H1-10 | PASS | R-1 through R-6 planned and computed zero directions. The recorded G1.0 spatial keys match for R-2 through R-4. All four protected cache namespaces match before and after. [cache_before_regression.json](evidence/cache_before_regression.json), [cache_after_r6.json](evidence/cache_after_r6.json), [cache_after_r8.json](evidence/cache_after_r8.json) |
| H1-11 | PASS | All R-1 through R-6 raster comparisons had zero differing pixels. R-7 matched the five reference frames and raw catalogue hash. [R-1-comparison.json](evidence/R-1-comparison.json), [R-2-comparison.json](evidence/R-2-comparison.json), [R-3-comparison.json](evidence/R-3-comparison.json), [R-4-comparison.json](evidence/R-4-comparison.json), [R-5-comparison.json](evidence/R-5-comparison.json), [R-6-comparison.json](evidence/R-6-comparison.json), [R-7-comparison.json](evidence/R-7-comparison.json) |
| H1-12 | PASS | The regression used the new runtime roots and F publication layout. The final protected inventory shows zero changes. The derived inputs did not change during regression. [runtime_locations.json](evidence/runtime_locations.json), [cache_after_r8.json](evidence/cache_after_r8.json), [inventory_after_regression.json](evidence/inventory_after_regression.json) |
| H1-13 | PASS | The CLI and lazy imports used the new names without double-loading. R-6 used the public function. The regenerated cell list and permitted machine-config changes were verified. [cli_commands.txt](evidence/cli_commands.txt), [viewer_cells_comparison.json](evidence/viewer_cells_comparison.json), [machine_local.diff.txt](evidence/machine_local.diff.txt) |
| H1-14 | PASS | Each real job was metered from launch, the frozen budgets were met, and the input paths were local. Review evidence and large-file hashes are indexed below. [resources.jsonl](evidence/resources.jsonl) |

## Derived identities

| Artifact | New ID |
| --- | --- |
| Hong Kong view | `412eae7951535ccf4f747be461ebcfe64f4e812d67a4d93f558150a718277d5e` |
| Rotterdam ingestion | `ce865fa2895066d03fba441ec6a6ce80d0c8f41c387a1e21e0614136baeb36a3` |
| Rotterdam view | `11004a24a611e773a72b08cbc30e31cfda15ec462a18654105956bcdf15193eb` |

## Regression

| Case | Frames | Raster comparisons | Differing pixels | New horizon directions |
| --- | ---: | ---: | ---: | ---: |
| R-1 | 65 | 780 | 0 | 0 |
| R-2 | 146 | 2628 | 0 | 0 |
| R-3 | 146 | 2628 | 0 | 0 |
| R-4 | 146 | 2628 | 0 | 0 |
| R-5 | 50 | 900 | 0 | 0 |
| R-6 | 3 | 54 | 0 | 0 |

R-7 reproduced all 5 report frames and the raw catalogue SHA-256. The counterfactual computed 20 directions in `fill_impact_d22f3d259b66`. R-8 produced two Hong Kong raw plans. Its full output is `archive/reviews/h1_0_dev_20261112/R-8.stdout.txt`.

Two early R-1 comparison attempts stopped on an incorrect expected frame count in the verification script. The corrected check indexed expected counts by case and matched the existing 65 frames by UTC. R-1 itself ran once.

## Tests and layout scan

The test-ID comparison covers the 309 tests at the starting commit and the 308 tests at the candidate. The allowed retirements removed seven IDs. Six layout tests were added. The full comparison and final command output are linked from H1-06.

The tracked-file scan uses these patterns with word or path boundaries. Historical exclusions follow design item 9 and SW-H1.1 A2.

```text
\b(?:from|import)\s+(?:src|tools)\b
(?<![\w.-])(?:src|tools|outputs)/
(?<![\w.-])(?:data/processed|data/raw/dsm)(?![\w-])
(?<![\w-])(?:shade_map_work|region_views|sea2_2_diagnostic_work|dsm_views|shade_v1)(?![\w-])
```

The engine command modules reuse their package module name when invoked as a command or loaded by the multiprocessing bootstrap. The viewer README retains its paired historical B2.2 view and manifest reference. The regenerated index records the new view and manifest hash. The `runs/` ownership marker was initialized so the default and the nested development output root can coexist.

## Complete move table

Every move unit and tracked path is recorded in [move_table.tsv](evidence/move_table.tsv). Directory moves preserve the suffix of each descendant path. The initial table was prepared before renames, with the two view cache destinations resolved after the new IDs were known.

<details><summary>Physical move units and tracked file destinations</summary>

| Entry | Original path | Destination |
| --- | --- | --- |
| move unit | `README.md` | `docs/records/README_pre_h1.md` |
| move unit | `archive/baseline_h1_0_20261112` | `archive/baseline_h1_0_20261112` |
| move unit | `archive/removed` | `archive/removed` |
| move unit | `config/mosaic_6tiles.json` | `legacy/config/mosaic_6tiles.json` |
| move unit | `config/processing.json` | `config/engine/processing.json` |
| move unit | `config/study_area.md` | `config/engine/study_area.md` |
| move unit | `config/v3` | `legacy/config/v3` |
| move unit | `data/processed/.DS_Store` | `(remove)` |
| move unit | `data/processed/README.md` | `docs/records/data_processed_README.md` |
| move unit | `data/processed/dsm_catalogues` | `archive/data_processed/dsm_catalogues` |
| move unit | `data/processed/dsm_views/sea_fill_v2_2` | `archive/data_processed/dsm_views/sea_fill_v2_2` |
| move unit | `data/processed/shade_v1/g1_dev_raw_20261111` | `data/cache/horizon/raw_hong_kong` |
| move unit | `data/processed/shade_v1/g1_dev_raw_20261111_rotterdam` | `data/cache/horizon/raw_rotterdam` |
| move unit | `data/processed/shade_v1/sea_fill_v2_2_4b2c2e76ca8b` | `data/cache/horizon/view_11004a24a611` |
| move unit | `data/processed/shade_v1/sea_fill_v2_2_8ee51b017411` | `data/cache/horizon/view_412eae795153` |
| move unit | `data/raw/basemap` | `data/raw/hong_kong/basemap` |
| move unit | `data/raw/coastline` | `data/raw/hong_kong/coastline` |
| move unit | `data/raw/dsm/.DS_Store` | `data/raw/hong_kong/dsm_cedd_2020_docs/.DS_Store` |
| move unit | `data/raw/dsm/2020` | `data/raw/hong_kong/dsm_cedd_2020` |
| move unit | `data/raw/dsm/2020_HKUST_Around` | `data/raw/hong_kong/dsm_cedd_2020_hkust` |
| move unit | `data/raw/dsm/Metedata for LiDAR Data (2020).html` | `data/raw/hong_kong/dsm_cedd_2020_docs/Metedata for LiDAR Data (2020).html` |
| move unit | `data/raw/dsm/README.md` | `data/raw/hong_kong/dsm_cedd_2020_docs/README.md` |
| move unit | `data/raw/dsm/T&C of CEDD Spatial Data Portal.pdf` | `data/raw/hong_kong/dsm_cedd_2020_docs/T&C of CEDD Spatial Data Portal.pdf` |
| move unit | `data/raw/dsm/Terms and Conditions of Use.pdf` | `data/raw/hong_kong/dsm_cedd_2020_docs/Terms and Conditions of Use.pdf` |
| move unit | `data/raw/dsm/rotterdam_ahn4_dsm05` | `data/raw/rotterdam/dsm_ahn_05m` |
| move unit | `data/raw/validation` | `data/raw/hong_kong/validation` |
| move unit | `docs/ARCHITECTURE.md` | `docs/records/ARCHITECTURE.md` |
| move unit | `docs/GUIDE.md` | `docs/records/GUIDE.md` |
| move unit | `docs/GUIDE.zh-TW.md` | `docs/records/GUIDE.zh-TW.md` |
| move unit | `docs/METHOD.md` | `docs/records/METHOD.md` |
| move unit | `docs/METHOD_legacy.md` | `docs/records/METHOD_legacy.md` |
| move unit | `docs/NATIVE_MOSAIC_2026-09-29.md` | `docs/records/NATIVE_MOSAIC_2026-09-29.md` |
| move unit | `docs/NATIVE_TILE_UNITS_2026-09-28.md` | `docs/records/NATIVE_TILE_UNITS_2026-09-28.md` |
| move unit | `docs/PROJECT_STATUS_2026-10-29.zh-TW.md` | `docs/records/PROJECT_STATUS_2026-10-29.zh-TW.md` |
| move unit | `docs/QA.md` | `docs/records/QA.md` |
| move unit | `docs/QA_100x100.md` | `docs/records/QA_100x100.md` |
| move unit | `docs/QA_600x450_legacy.md` | `docs/records/QA_600x450_legacy.md` |
| move unit | `docs/RUN_INDIVIDUAL_TILES.md` | `docs/records/RUN_INDIVIDUAL_TILES.md` |
| move unit | `docs/TILING_RESEARCH_2026-09-28.md` | `docs/records/TILING_RESEARCH_2026-09-28.md` |
| move unit | `docs/city` | `docs/records/city` |
| move unit | `docs/prompts` | `docs/records/prompts` |
| move unit | `docs/region` | `docs/records/region` |
| move unit | `docs/sea` | `docs/records/sea` |
| move unit | `docs/sea2` | `docs/records/sea2` |
| move unit | `docs/shade_map` | `docs/records/shade_map` |
| move unit | `docs/ui` | `docs/records/ui` |
| move unit | `docs/v1` | `docs/records/v1` |
| move unit | `docs/v2` | `docs/records/v2` |
| move unit | `docs/v2/estimator.json` | `config/engine/estimator.json` |
| move unit | `docs/v3` | `docs/records/v3` |
| move unit | `outputs/.DS_Store` | `archive/outputs/.DS_Store` |
| move unit | `outputs/600x450` | `archive/outputs/600x450` |
| move unit | `outputs/README.md` | `docs/records/outputs_README.md` |
| move unit | `outputs/baseline` | `archive/outputs/baseline` |
| move unit | `outputs/chunking_qa_20260928` | `archive/outputs/chunking_qa_20260928` |
| move unit | `outputs/frames` | `archive/outputs/frames` |
| move unit | `outputs/individual_6tiles_20261001` | `archive/outputs/individual_6tiles_20261001` |
| move unit | `outputs/individual_6tiles_20261001_run.log` | `archive/outputs/individual_6tiles_20261001_run.log` |
| move unit | `outputs/mosaic_6tiles_20260929_comparison.log` | `archive/outputs/mosaic_6tiles_20260929_comparison.log` |
| move unit | `outputs/mosaic_6tiles_20260929_qa.log` | `archive/outputs/mosaic_6tiles_20260929_qa.log` |
| move unit | `outputs/mosaic_6tiles_20260929_run.log` | `archive/outputs/mosaic_6tiles_20260929_run.log` |
| move unit | `outputs/native_mosaic_6tiles_1km_20260929` | `archive/outputs/native_mosaic_6tiles_1km_20260929` |
| move unit | `outputs/native_tile_1km_20260928` | `archive/outputs/native_tile_1km_20260928` |
| move unit | `outputs/native_tile_unit_1km_20260928` | `archive/outputs/native_tile_unit_1km_20260928` |
| move unit | `outputs/pilot_time_estimate_20261009` | `archive/outputs/pilot_time_estimate_20261009` |
| move unit | `outputs/png` | `archive/outputs/png` |
| move unit | `outputs/quality` | `archive/outputs/quality` |
| move unit | `outputs/rasters` | `archive/outputs/rasters` |
| move unit | `outputs/region_dev_v1_1_example_requests` | `archive/outputs/region_dev_v1_1_example_requests` |
| move unit | `outputs/region_dev_v1_1_validation` | `archive/outputs/region_dev_v1_1_validation` |
| move unit | `outputs/region_dev_validation` | `archive/outputs/region_dev_validation` |
| move unit | `outputs/result_inventory.json` | `archive/outputs/result_inventory.json` |
| move unit | `outputs/sea2_2_development` | `archive/outputs/sea2_2_development` |
| move unit | `outputs/sea2_2_review_7707c511a442_20261109` | `archive/outputs/sea2_2_review_7707c511a442_20261109` |
| move unit | `outputs/sea2_2_validation` | `archive/outputs/sea2_2_validation` |
| move unit | `outputs/sea2_f_20261104` | `archive/outputs/sea2_f_20261104` |
| move unit | `outputs/sea_dev_build` | `archive/outputs/sea_dev_build` |
| move unit | `outputs/sea_dev_central` | `archive/outputs/sea_dev_central` |
| move unit | `outputs/sea_dev_cheung_chau` | `archive/outputs/sea_dev_cheung_chau` |
| move unit | `outputs/sea_dev_diagnostic_band2_5` | `archive/outputs/sea_dev_diagnostic_band2_5` |
| move unit | `outputs/sea_dev_diagnostic_band5` | `archive/outputs/sea_dev_diagnostic_band5` |
| move unit | `outputs/sea_dev_diagnostic_h0` | `archive/outputs/sea_dev_diagnostic_h0` |
| move unit | `outputs/sea_dev_diagnostic_h3` | `archive/outputs/sea_dev_diagnostic_h3` |
| move unit | `outputs/sea_dev_preflight` | `archive/outputs/sea_dev_preflight` |
| move unit | `outputs/sea_dev_raw_central` | `archive/outputs/sea_dev_raw_central` |
| move unit | `outputs/sea_dev_raw_cheung_chau` | `archive/outputs/sea_dev_raw_cheung_chau` |
| move unit | `outputs/sea_review_20261030` | `archive/outputs/sea_review_20261030` |
| move unit | `outputs/shade_20260107_1430_HKT.jpg` | `archive/outputs/shade_20260107_1430_HKT.jpg` |
| move unit | `outputs/shade_daylight_2026-01-07_HKT.mp4` | `archive/outputs/shade_daylight_2026-01-07_HKT.mp4` |
| move unit | `outputs/shade_map` | `baselines/measure_5regions_20261110` |
| move unit | `outputs/shade_map_f1_20261031` | `archive/outputs/shade_map_f1_20261031` |
| move unit | `outputs/shade_map_f1_diagnostics_20261031` | `archive/outputs/shade_map_f1_diagnostics_20261031` |
| move unit | `outputs/shade_map_f1_repair_1_20261104` | `archive/outputs/shade_map_f1_repair_1_20261104` |
| move unit | `outputs/shade_map_f1_repair_1_diagnostics_20261104` | `archive/outputs/shade_map_f1_repair_1_diagnostics_20261104` |
| move unit | `outputs/shade_map_g1_dev_20261111` | `baselines/g1_dev_20261111` |
| move unit | `outputs/shade_map_g1_review_af6fca9e3025_20261111` | `archive/outputs/shade_map_g1_review_af6fca9e3025_20261111` |
| move unit | `outputs/shade_map_review_35225fd9547a_20261104` | `archive/outputs/shade_map_review_35225fd9547a_20261104` |
| move unit | `outputs/shade_map_review_35225fd9547a_addendum_1_20261104` | `archive/outputs/shade_map_review_35225fd9547a_addendum_1_20261104` |
| move unit | `outputs/shade_map_review_eb605f52d119_20261031` | `archive/outputs/shade_map_review_eb605f52d119_20261031` |
| move unit | `outputs/update_backups` | `archive/outputs/update_backups` |
| move unit | `outputs/v1_development_20261002` | `archive/outputs/v1_development_20261002` |
| move unit | `outputs/v1_independent_acceptance_796ac8a` | `archive/outputs/v1_independent_acceptance_796ac8a` |
| move unit | `outputs/v2_closeout_20261008` | `archive/outputs/v2_closeout_20261008` |
| move unit | `outputs/v2_daylight_cheungchau_20261009` | `baselines/e2_cheung_chau_20260107` |
| move unit | `outputs/v2_development` | `archive/outputs/v2_development` |
| move unit | `outputs/v2_example` | `archive/outputs/v2_example` |
| move unit | `outputs/v2_example_state` | `archive/outputs/v2_example_state` |
| move unit | `outputs/v2_independent_acceptance_356f611` | `archive/outputs/v2_independent_acceptance_356f611` |
| move unit | `outputs/v2_independent_acceptance_e2fa0cd` | `archive/outputs/v2_independent_acceptance_e2fa0cd` |
| move unit | `outputs/v2_independent_acceptance_f3dac31` | `archive/outputs/v2_independent_acceptance_f3dac31` |
| move unit | `outputs/validation_capture` | `archive/outputs/validation_capture` |
| move unit | `src/.gitkeep` | `(remove)` |
| move unit | `src/__init__.py` | `shade_watch/engine/__init__.py` |
| move unit | `src/batch_tiles.py` | `legacy/pipeline/batch_tiles.py` |
| move unit | `src/horizon.py` | `shade_watch/engine/horizon.py` |
| move unit | `src/pipeline.py` | `shade_watch/engine/pipeline.py` |
| move unit | `src/shade_watch.py` | `shade_watch/engine/shade_watch.py` |
| move unit | `src/solar.py` | `shade_watch/engine/solar.py` |
| move unit | `src/spatial.py` | `shade_watch/engine/spatial.py` |
| move unit | `src/v1.py` | `shade_watch/engine/v1.py` |
| move unit | `src/v1_cache.py` | `shade_watch/engine/v1_cache.py` |
| move unit | `src/v2.py` | `shade_watch/engine/v2.py` |
| move unit | `src/v2_runner.py` | `shade_watch/engine/v2_runner.py` |
| move unit | `src/v2_state.py` | `shade_watch/engine/v2_state.py` |
| move unit | `src/v2_worker.py` | `shade_watch/engine/v2_worker.py` |
| move unit | `src/verify_chunking.py` | `legacy/pipeline/verify_chunking.py` |
| move unit | `src/verify_mosaic.py` | `legacy/pipeline/verify_mosaic.py` |
| move unit | `tests/.gitkeep` | `(remove)` |
| move unit | `tests/shade_map_campaign.py` | `legacy/campaigns/f1/shade_map_campaign.py` |
| move unit | `tests/shade_map_repair_campaign.py` | `legacy/campaigns/f1/shade_map_repair_campaign.py` |
| move unit | `tests/test_sea_masks.py` | `legacy/b1_sea_view/test_sea_masks.py` |
| move unit | `tools/city` | `shade_watch/city` |
| move unit | `tools/region_request.py` | `shade_watch/region.py` |
| move unit | `tools/sea2/__init__.py` | `shade_watch/fill/__init__.py` |
| move unit | `tools/sea2/__main__.py` | `shade_watch/fill/__main__.py` |
| move unit | `tools/sea2/build.py` | `shade_watch/fill/build.py` |
| move unit | `tools/sea2/catalogue.py` | `shade_watch/fill/catalogue.py` |
| move unit | `tools/sea2/checks.py` | `shade_watch/fill/checks.py` |
| move unit | `tools/sea2/fill_impact.py` | `shade_watch/fill/fill_impact.py` |
| move unit | `tools/sea2/profile.py` | `shade_watch/fill/profile.py` |
| move unit | `tools/sea2/provider.py` | `shade_watch/fill/provider.py` |
| move unit | `tools/sea2/resources.py` | `legacy/campaigns/b2_2/resources.py` |
| move unit | `tools/sea2/rule.py` | `shade_watch/fill/rule.py` |
| move unit | `tools/sea2/validate_ib5000.py` | `shade_watch/fill/validate_ib5000.py` |
| move unit | `tools/sea2/validation_worker.py` | `shade_watch/fill/validation_worker.py` |
| move unit | `tools/sea2/view.py` | `shade_watch/fill/view.py` |
| move unit | `tools/sea_view` | `legacy/b1_sea_view` |
| move unit | `tools/shade_map` | `shade_watch/publish` |
| move unit | `tools/v1_development.py` | `legacy/campaigns/v1_development.py` |
| move unit | `tools/v2_closeout.py` | `legacy/campaigns/v2_closeout.py` |
| move unit | `tools/v2_development.py` | `legacy/campaigns/v2_development.py` |
| move unit | `tools/v3_campaign.py` | `legacy/campaigns/v3_campaign.py` |
| move unit | `tools/wsl2_smoke` | `legacy/wsl2_smoke` |
| move unit | `web/.gitkeep` | `(remove)` |
| move unit | `web/console` | `legacy/web/console` |
| move unit | `web/index.html` | `legacy/web/index.html` |
| move unit | `web/shade_map` | `web/viewer` |
| tracked file | `README.md` | `docs/records/README_pre_h1.md` |
| tracked file | `config/mosaic_6tiles.json` | `legacy/config/mosaic_6tiles.json` |
| tracked file | `config/processing.json` | `config/engine/processing.json` |
| tracked file | `config/study_area.md` | `config/engine/study_area.md` |
| tracked file | `config/v3/pilots.template.json` | `legacy/config/v3/pilots.template.json` |
| tracked file | `data/processed/README.md` | `docs/records/data_processed_README.md` |
| tracked file | `data/raw/basemap/README.md` | `data/raw/hong_kong/basemap/README.md` |
| tracked file | `data/raw/coastline/README.md` | `data/raw/hong_kong/coastline/README.md` |
| tracked file | `data/raw/dsm/README.md` | `data/raw/hong_kong/dsm_cedd_2020_docs/README.md` |
| tracked file | `data/raw/validation/README.md` | `data/raw/hong_kong/validation/README.md` |
| tracked file | `docs/ARCHITECTURE.md` | `docs/records/ARCHITECTURE.md` |
| tracked file | `docs/GUIDE.md` | `docs/records/GUIDE.md` |
| tracked file | `docs/GUIDE.zh-TW.md` | `docs/records/GUIDE.zh-TW.md` |
| tracked file | `docs/METHOD.md` | `docs/records/METHOD.md` |
| tracked file | `docs/METHOD_legacy.md` | `docs/records/METHOD_legacy.md` |
| tracked file | `docs/NATIVE_MOSAIC_2026-09-29.md` | `docs/records/NATIVE_MOSAIC_2026-09-29.md` |
| tracked file | `docs/NATIVE_TILE_UNITS_2026-09-28.md` | `docs/records/NATIVE_TILE_UNITS_2026-09-28.md` |
| tracked file | `docs/PROJECT_STATUS_2026-10-29.zh-TW.md` | `docs/records/PROJECT_STATUS_2026-10-29.zh-TW.md` |
| tracked file | `docs/QA.md` | `docs/records/QA.md` |
| tracked file | `docs/QA_100x100.md` | `docs/records/QA_100x100.md` |
| tracked file | `docs/QA_600x450_legacy.md` | `docs/records/QA_600x450_legacy.md` |
| tracked file | `docs/RUN_INDIVIDUAL_TILES.md` | `docs/records/RUN_INDIVIDUAL_TILES.md` |
| tracked file | `docs/TILING_RESEARCH_2026-09-28.md` | `docs/records/TILING_RESEARCH_2026-09-28.md` |
| tracked file | `docs/city/DESIGN.md` | `docs/records/city/DESIGN.md` |
| tracked file | `docs/city/DEVELOPMENT_REPORT.md` | `docs/records/city/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/city/GUIDE.md` | `docs/records/city/GUIDE.md` |
| tracked file | `docs/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025.md` | `docs/records/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025.md` |
| tracked file | `docs/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025_ADDENDUM_1.md` | `docs/records/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025_ADDENDUM_1.md` |
| tracked file | `docs/city/evidence/campaign.py` | `docs/records/city/evidence/campaign.py` |
| tracked file | `docs/city/evidence/compare_hk.py` | `docs/records/city/evidence/compare_hk.py` |
| tracked file | `docs/city/evidence/configs/hk1.json` | `docs/records/city/evidence/configs/hk1.json` |
| tracked file | `docs/city/evidence/configs/hk2.json` | `docs/records/city/evidence/configs/hk2.json` |
| tracked file | `docs/city/evidence/configs/hk3.json` | `docs/records/city/evidence/configs/hk3.json` |
| tracked file | `docs/city/evidence/configs/hk4.json` | `docs/records/city/evidence/configs/hk4.json` |
| tracked file | `docs/city/evidence/configs/legacy-no-source.json` | `docs/records/city/evidence/configs/legacy-no-source.json` |
| tracked file | `docs/city/evidence/configs/machine-hk1.json` | `docs/records/city/evidence/configs/machine-hk1.json` |
| tracked file | `docs/city/evidence/configs/machine.json` | `docs/records/city/evidence/configs/machine.json` |
| tracked file | `docs/city/evidence/configs/nl1.json` | `docs/records/city/evidence/configs/nl1.json` |
| tracked file | `docs/city/evidence/configs/nl2.json` | `docs/records/city/evidence/configs/nl2.json` |
| tracked file | `docs/city/evidence/configs/nl3.json` | `docs/records/city/evidence/configs/nl3.json` |
| tracked file | `docs/city/evidence/configs/nl5-dst.json` | `docs/records/city/evidence/configs/nl5-dst.json` |
| tracked file | `docs/city/evidence/configs/nl5-edge.json` | `docs/records/city/evidence/configs/nl5-edge.json` |
| tracked file | `docs/city/evidence/development_campaign.sh` | `docs/records/city/evidence/development_campaign.sh` |
| tracked file | `docs/city/evidence/direct_rays.py` | `docs/records/city/evidence/direct_rays.py` |
| tracked file | `docs/city/evidence/engine-stage-tests.txt` | `docs/records/city/evidence/engine-stage-tests.txt` |
| tracked file | `docs/city/evidence/hk1-comparison.json` | `docs/records/city/evidence/hk1-comparison.json` |
| tracked file | `docs/city/evidence/hk1-result.json` | `docs/records/city/evidence/hk1-result.json` |
| tracked file | `docs/city/evidence/hk2-comparison.json` | `docs/records/city/evidence/hk2-comparison.json` |
| tracked file | `docs/city/evidence/hk2-plan.json` | `docs/records/city/evidence/hk2-plan.json` |
| tracked file | `docs/city/evidence/hk2-result.json` | `docs/records/city/evidence/hk2-result.json` |
| tracked file | `docs/city/evidence/hk3-comparison.json` | `docs/records/city/evidence/hk3-comparison.json` |
| tracked file | `docs/city/evidence/hk3-plan.json` | `docs/records/city/evidence/hk3-plan.json` |
| tracked file | `docs/city/evidence/hk3-result.json` | `docs/records/city/evidence/hk3-result.json` |
| tracked file | `docs/city/evidence/hk4-comparison.json` | `docs/records/city/evidence/hk4-comparison.json` |
| tracked file | `docs/city/evidence/hk4-plan.json` | `docs/records/city/evidence/hk4-plan.json` |
| tracked file | `docs/city/evidence/hk4-result.json` | `docs/records/city/evidence/hk4-result.json` |
| tracked file | `docs/city/evidence/legacy-plans.json` | `docs/records/city/evidence/legacy-plans.json` |
| tracked file | `docs/city/evidence/measure.py` | `docs/records/city/evidence/measure.py` |
| tracked file | `docs/city/evidence/nl-validation.json` | `docs/records/city/evidence/nl-validation.json` |
| tracked file | `docs/city/evidence/nl0-registration.json` | `docs/records/city/evidence/nl0-registration.json` |
| tracked file | `docs/city/evidence/nl1-plan.json` | `docs/records/city/evidence/nl1-plan.json` |
| tracked file | `docs/city/evidence/nl1-rays.json` | `docs/records/city/evidence/nl1-rays.json` |
| tracked file | `docs/city/evidence/nl1-result.json` | `docs/records/city/evidence/nl1-result.json` |
| tracked file | `docs/city/evidence/nl2-plan.json` | `docs/records/city/evidence/nl2-plan.json` |
| tracked file | `docs/city/evidence/nl2-result.json` | `docs/records/city/evidence/nl2-result.json` |
| tracked file | `docs/city/evidence/nl3-plan.json` | `docs/records/city/evidence/nl3-plan.json` |
| tracked file | `docs/city/evidence/nl3-result.json` | `docs/records/city/evidence/nl3-result.json` |
| tracked file | `docs/city/evidence/nl4-result.json` | `docs/records/city/evidence/nl4-result.json` |
| tracked file | `docs/city/evidence/nl5-dst-plan.json` | `docs/records/city/evidence/nl5-dst-plan.json` |
| tracked file | `docs/city/evidence/nl5-edge-plan.json` | `docs/records/city/evidence/nl5-edge-plan.json` |
| tracked file | `docs/city/evidence/protected-after.json` | `docs/records/city/evidence/protected-after.json` |
| tracked file | `docs/city/evidence/protected-before.json` | `docs/records/city/evidence/protected-before.json` |
| tracked file | `docs/city/evidence/protected.py` | `docs/records/city/evidence/protected.py` |
| tracked file | `docs/city/evidence/pytest.txt` | `docs/records/city/evidence/pytest.txt` |
| tracked file | `docs/city/evidence/rejections.json` | `docs/records/city/evidence/rejections.json` |
| tracked file | `docs/city/evidence/resources.jsonl` | `docs/records/city/evidence/resources.jsonl` |
| tracked file | `docs/city/evidence/verify_rotterdam.py` | `docs/records/city/evidence/verify_rotterdam.py` |
| tracked file | `docs/prompts/B2/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/B2/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/B2/AMENDMENT_B2_1.md` | `docs/records/prompts/B2/AMENDMENT_B2_1.md` |
| tracked file | `docs/prompts/B2/CONTRACT_B2_2.md` | `docs/records/prompts/B2/CONTRACT_B2_2.md` |
| tracked file | `docs/prompts/B2/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/B2/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/B2/DEVELOPMENT_PROMPT_B2_2.md` | `docs/records/prompts/B2/DEVELOPMENT_PROMPT_B2_2.md` |
| tracked file | `docs/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT_B2_2.md` | `docs/records/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT_B2_2.md` |
| tracked file | `docs/prompts/F1/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/F1/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/F1/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/F1/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/F1/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/F1/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/G1/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/G1/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/G1/AMENDMENT_G1_1.md` | `docs/records/prompts/G1/AMENDMENT_G1_1.md` |
| tracked file | `docs/prompts/G1/AMENDMENT_G1_2.md` | `docs/records/prompts/G1/AMENDMENT_G1_2.md` |
| tracked file | `docs/prompts/G1/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/G1/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/G1/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/G1/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/README.md` | `docs/records/prompts/README.md` |
| tracked file | `docs/prompts/region/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/region/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/region/AMENDMENT_1_1.md` | `docs/records/prompts/region/AMENDMENT_1_1.md` |
| tracked file | `docs/prompts/region/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/region/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/runner/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/runner/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/runner/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/runner/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/sea/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/sea/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/sea/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/sea/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/sea/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/sea/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/v1/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/v1/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/v1/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/v1/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/v1/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/v1/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/v2/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/v2/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/v2/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/v2/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/v2/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/v2/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/prompts/v3/ACCEPTANCE_CONTRACT.md` | `docs/records/prompts/v3/ACCEPTANCE_CONTRACT.md` |
| tracked file | `docs/prompts/v3/DEVELOPMENT_PROMPT.md` | `docs/records/prompts/v3/DEVELOPMENT_PROMPT.md` |
| tracked file | `docs/prompts/v3/INDEPENDENT_ACCEPTANCE_PROMPT.md` | `docs/records/prompts/v3/INDEPENDENT_ACCEPTANCE_PROMPT.md` |
| tracked file | `docs/region/DESIGN.md` | `docs/records/region/DESIGN.md` |
| tracked file | `docs/region/DEVELOPMENT_REPORT.md` | `docs/records/region/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/region/GUIDE.md` | `docs/records/region/GUIDE.md` |
| tracked file | `docs/region/evidence/blocker.json` | `docs/records/region/evidence/blocker.json` |
| tracked file | `docs/region/evidence/catalogue.json` | `docs/records/region/evidence/catalogue.json` |
| tracked file | `docs/region/evidence/final-integrity.json` | `docs/records/region/evidence/final-integrity.json` |
| tracked file | `docs/region/evidence/full-tests.txt` | `docs/records/region/evidence/full-tests.txt` |
| tracked file | `docs/region/evidence/ledger-incomplete-original.json` | `docs/records/region/evidence/ledger-incomplete-original.json` |
| tracked file | `docs/region/evidence/ledger.json` | `docs/records/region/evidence/ledger.json` |
| tracked file | `docs/region/evidence/manifest.json` | `docs/records/region/evidence/manifest.json` |
| tracked file | `docs/region/evidence/real-equality.json` | `docs/records/region/evidence/real-equality.json` |
| tracked file | `docs/region/evidence/real-plan.json` | `docs/records/region/evidence/real-plan.json` |
| tracked file | `docs/region/evidence/real-run.txt` | `docs/records/region/evidence/real-run.txt` |
| tracked file | `docs/region/evidence/run-script.py` | `docs/records/region/evidence/run-script.py` |
| tracked file | `docs/region/evidence/start.json` | `docs/records/region/evidence/start.json` |
| tracked file | `docs/region/evidence/unit-tests.txt` | `docs/records/region/evidence/unit-tests.txt` |
| tracked file | `docs/region/evidence/v1_1/development_run.py` | `docs/records/region/evidence/v1_1/development_run.py` |
| tracked file | `docs/region/evidence/v1_1/final-integrity.json` | `docs/records/region/evidence/v1_1/final-integrity.json` |
| tracked file | `docs/region/evidence/v1_1/final-unit-tests.txt` | `docs/records/region/evidence/v1_1/final-unit-tests.txt` |
| tracked file | `docs/region/evidence/v1_1/full-tests-before-empty-date-fix.txt` | `docs/records/region/evidence/v1_1/full-tests-before-empty-date-fix.txt` |
| tracked file | `docs/region/evidence/v1_1/full-tests-collection-error.txt` | `docs/records/region/evidence/v1_1/full-tests-collection-error.txt` |
| tracked file | `docs/region/evidence/v1_1/full-tests-collection-error.xml` | `docs/records/region/evidence/v1_1/full-tests-collection-error.xml` |
| tracked file | `docs/region/evidence/v1_1/full-tests.txt` | `docs/records/region/evidence/v1_1/full-tests.txt` |
| tracked file | `docs/region/evidence/v1_1/full-tests.xml` | `docs/records/region/evidence/v1_1/full-tests.xml` |
| tracked file | `docs/region/evidence/v1_1/guide-checks.json` | `docs/records/region/evidence/v1_1/guide-checks.json` |
| tracked file | `docs/region/evidence/v1_1/guide_0_stderr.txt` | `docs/records/region/evidence/v1_1/guide_0_stderr.txt` |
| tracked file | `docs/region/evidence/v1_1/guide_0_stdout.json` | `docs/records/region/evidence/v1_1/guide_0_stdout.json` |
| tracked file | `docs/region/evidence/v1_1/guide_1_stderr.txt` | `docs/records/region/evidence/v1_1/guide_1_stderr.txt` |
| tracked file | `docs/region/evidence/v1_1/guide_1_stdout.json` | `docs/records/region/evidence/v1_1/guide_1_stdout.json` |
| tracked file | `docs/region/evidence/v1_1/initial-tests.txt` | `docs/records/region/evidence/v1_1/initial-tests.txt` |
| tracked file | `docs/region/evidence/v1_1/ledger.json` | `docs/records/region/evidence/v1_1/ledger.json` |
| tracked file | `docs/region/evidence/v1_1/manifest.json` | `docs/records/region/evidence/v1_1/manifest.json` |
| tracked file | `docs/region/evidence/v1_1/r11-real-identity-run.txt` | `docs/records/region/evidence/v1_1/r11-real-identity-run.txt` |
| tracked file | `docs/region/evidence/v1_1/r11-real-identity.json` | `docs/records/region/evidence/v1_1/r11-real-identity.json` |
| tracked file | `docs/region/evidence/v1_1/r11_real_compare.py` | `docs/records/region/evidence/v1_1/r11_real_compare.py` |
| tracked file | `docs/region/evidence/v1_1/real-equality.json` | `docs/records/region/evidence/v1_1/real-equality.json` |
| tracked file | `docs/region/evidence/v1_1/real-plan.json` | `docs/records/region/evidence/v1_1/real-plan.json` |
| tracked file | `docs/region/evidence/v1_1/real-run.txt` | `docs/records/region/evidence/v1_1/real-run.txt` |
| tracked file | `docs/region/evidence/v1_1/real-source-view-timings.json` | `docs/records/region/evidence/v1_1/real-source-view-timings.json` |
| tracked file | `docs/region/evidence/v1_1/source-view-timings.json` | `docs/records/region/evidence/v1_1/source-view-timings.json` |
| tracked file | `docs/region/evidence/v1_1/start.json` | `docs/records/region/evidence/v1_1/start.json` |
| tracked file | `docs/region/evidence/v1_1/unit-tests.txt` | `docs/records/region/evidence/v1_1/unit-tests.txt` |
| tracked file | `docs/region/evidence/v1_1/unit-tests.xml` | `docs/records/region/evidence/v1_1/unit-tests.xml` |
| tracked file | `docs/region/evidence/v1_1/v1-result.json` | `docs/records/region/evidence/v1_1/v1-result.json` |
| tracked file | `docs/region/evidence/v1_1/v2-result.json` | `docs/records/region/evidence/v1_1/v2-result.json` |
| tracked file | `docs/region/evidence/v2-result.json` | `docs/records/region/evidence/v2-result.json` |
| tracked file | `docs/sea/DESIGN.md` | `docs/records/sea/DESIGN.md` |
| tracked file | `docs/sea/DEVELOPMENT_REPORT.md` | `docs/records/sea/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/sea/GUIDE.md` | `docs/records/sea/GUIDE.md` |
| tracked file | `docs/sea/POLICY.md` | `docs/records/sea/POLICY.md` |
| tracked file | `docs/sea/evidence/build-run.txt` | `docs/records/sea/evidence/build-run.txt` |
| tracked file | `docs/sea/evidence/central-comparison.json` | `docs/records/sea/evidence/central-comparison.json` |
| tracked file | `docs/sea/evidence/central-helpers.json` | `docs/records/sea/evidence/central-helpers.json` |
| tracked file | `docs/sea/evidence/central-plan.json` | `docs/records/sea/evidence/central-plan.json` |
| tracked file | `docs/sea/evidence/central-raw-result.json` | `docs/records/sea/evidence/central-raw-result.json` |
| tracked file | `docs/sea/evidence/central-result.json` | `docs/records/sea/evidence/central-result.json` |
| tracked file | `docs/sea/evidence/central-run.txt` | `docs/records/sea/evidence/central-run.txt` |
| tracked file | `docs/sea/evidence/cheung_chau-comparison.json` | `docs/records/sea/evidence/cheung_chau-comparison.json` |
| tracked file | `docs/sea/evidence/cheung_chau-helpers.json` | `docs/records/sea/evidence/cheung_chau-helpers.json` |
| tracked file | `docs/sea/evidence/cheung_chau-plan.json` | `docs/records/sea/evidence/cheung_chau-plan.json` |
| tracked file | `docs/sea/evidence/cheung_chau-result.json` | `docs/records/sea/evidence/cheung_chau-result.json` |
| tracked file | `docs/sea/evidence/cheung_chau-run.txt` | `docs/records/sea/evidence/cheung_chau-run.txt` |
| tracked file | `docs/sea/evidence/compare_central-run.txt` | `docs/records/sea/evidence/compare_central-run.txt` |
| tracked file | `docs/sea/evidence/compare_cheung_chau-run.txt` | `docs/records/sea/evidence/compare_cheung_chau-run.txt` |
| tracked file | `docs/sea/evidence/dictionary-sections.txt` | `docs/records/sea/evidence/dictionary-sections.txt` |
| tracked file | `docs/sea/evidence/dictionary.json` | `docs/records/sea/evidence/dictionary.json` |
| tracked file | `docs/sea/evidence/edge-diagnostic.json` | `docs/records/sea/evidence/edge-diagnostic.json` |
| tracked file | `docs/sea/evidence/edge-point-checks.json` | `docs/records/sea/evidence/edge-point-checks.json` |
| tracked file | `docs/sea/evidence/edge-summary.json` | `docs/records/sea/evidence/edge-summary.json` |
| tracked file | `docs/sea/evidence/extraction-stderr.txt` | `docs/records/sea/evidence/extraction-stderr.txt` |
| tracked file | `docs/sea/evidence/extraction.json` | `docs/records/sea/evidence/extraction.json` |
| tracked file | `docs/sea/evidence/final-integrity.json` | `docs/records/sea/evidence/final-integrity.json` |
| tracked file | `docs/sea/evidence/full-tests.txt` | `docs/records/sea/evidence/full-tests.txt` |
| tracked file | `docs/sea/evidence/geometry-tests.txt` | `docs/records/sea/evidence/geometry-tests.txt` |
| tracked file | `docs/sea/evidence/halo-counts.json` | `docs/records/sea/evidence/halo-counts.json` |
| tracked file | `docs/sea/evidence/historical-before.json` | `docs/records/sea/evidence/historical-before.json` |
| tracked file | `docs/sea/evidence/ledger.json` | `docs/records/sea/evidence/ledger.json` |
| tracked file | `docs/sea/evidence/manifest.json` | `docs/records/sea/evidence/manifest.json` |
| tracked file | `docs/sea/evidence/mask-tests.txt` | `docs/records/sea/evidence/mask-tests.txt` |
| tracked file | `docs/sea/evidence/rays-run.txt` | `docs/records/sea/evidence/rays-run.txt` |
| tracked file | `docs/sea/evidence/reader-discovery.json` | `docs/records/sea/evidence/reader-discovery.json` |
| tracked file | `docs/sea/evidence/reader-install-network.txt` | `docs/records/sea/evidence/reader-install-network.txt` |
| tracked file | `docs/sea/evidence/reader-install-pypi.txt` | `docs/records/sea/evidence/reader-install-pypi.txt` |
| tracked file | `docs/sea/evidence/reader-install.txt` | `docs/records/sea/evidence/reader-install.txt` |
| tracked file | `docs/sea/evidence/scan-run.txt` | `docs/records/sea/evidence/scan-run.txt` |
| tracked file | `docs/sea/evidence/sea-ray-checks.json` | `docs/records/sea/evidence/sea-ray-checks.json` |
| tracked file | `docs/sea/evidence/sensitivity-run.txt` | `docs/records/sea/evidence/sensitivity-run.txt` |
| tracked file | `docs/sea/evidence/sensitivity.json` | `docs/records/sea/evidence/sensitivity.json` |
| tracked file | `docs/sea/evidence/start.json` | `docs/records/sea/evidence/start.json` |
| tracked file | `docs/sea/evidence/territory-scan.json` | `docs/records/sea/evidence/territory-scan.json` |
| tracked file | `docs/sea/evidence/tools-environment.json` | `docs/records/sea/evidence/tools-environment.json` |
| tracked file | `docs/sea/evidence/views.json` | `docs/records/sea/evidence/views.json` |
| tracked file | `docs/sea2/DESIGN.md` | `docs/records/sea2/DESIGN.md` |
| tracked file | `docs/sea2/DEVELOPMENT_REPORT.md` | `docs/records/sea2/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/sea2/DEVELOPMENT_REPORT_B2_2.md` | `docs/records/sea2/DEVELOPMENT_REPORT_B2_2.md` |
| tracked file | `docs/sea2/GUIDE.md` | `docs/records/sea2/GUIDE.md` |
| tracked file | `docs/sea2/INDEPENDENT_ACCEPTANCE_B2_2_7707c511a442.md` | `docs/records/sea2/INDEPENDENT_ACCEPTANCE_B2_2_7707c511a442.md` |
| tracked file | `docs/sea2/POLICY.md` | `docs/records/sea2/POLICY.md` |
| tracked file | `docs/sea2/evidence/DSM-only-build-1.json` | `docs/records/sea2/evidence/DSM-only-build-1.json` |
| tracked file | `docs/sea2/evidence/DSM-only-build-2-corrected.json` | `docs/records/sea2/evidence/DSM-only-build-2-corrected.json` |
| tracked file | `docs/sea2/evidence/DSM-only-build-2.json` | `docs/records/sea2/evidence/DSM-only-build-2.json` |
| tracked file | `docs/sea2/evidence/DSM-only-central_raw.json` | `docs/records/sea2/evidence/DSM-only-central_raw.json` |
| tracked file | `docs/sea2/evidence/DSM-only-central_sea.json` | `docs/records/sea2/evidence/DSM-only-central_sea.json` |
| tracked file | `docs/sea2/evidence/DSM-only-cheung_chau_sea.json` | `docs/records/sea2/evidence/DSM-only-cheung_chau_sea.json` |
| tracked file | `docs/sea2/evidence/DSM-only-cheung_chau_void_impact.json` | `docs/records/sea2/evidence/DSM-only-cheung_chau_void_impact.json` |
| tracked file | `docs/sea2/evidence/DSM-only-equivalence.json` | `docs/records/sea2/evidence/DSM-only-equivalence.json` |
| tracked file | `docs/sea2/evidence/DSM-only-sea_plan.json` | `docs/records/sea2/evidence/DSM-only-sea_plan.json` |
| tracked file | `docs/sea2/evidence/acceptance-matrix.json` | `docs/records/sea2/evidence/acceptance-matrix.json` |
| tracked file | `docs/sea2/evidence/accepted-F1-raw-plans.json` | `docs/records/sea2/evidence/accepted-F1-raw-plans.json` |
| tracked file | `docs/sea2/evidence/b2_2/audit-central.txt` | `docs/records/sea2/evidence/b2_2/audit-central.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-cheung_chau-attempt1.txt` | `docs/records/sea2/evidence/b2_2/audit-cheung_chau-attempt1.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-cheung_chau.txt` | `docs/records/sea2/evidence/b2_2/audit-cheung_chau.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-five_class-attempt1.txt` | `docs/records/sea2/evidence/b2_2/audit-five_class-attempt1.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-five_class.txt` | `docs/records/sea2/evidence/b2_2/audit-five_class.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-keys.txt` | `docs/records/sea2/evidence/b2_2/audit-keys.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit-view.txt` | `docs/records/sea2/evidence/b2_2/audit-view.txt` |
| tracked file | `docs/sea2/evidence/b2_2/audit_real.py` | `docs/records/sea2/evidence/b2_2/audit_real.py` |
| tracked file | `docs/sea2/evidence/b2_2/caffeinate-observation.txt` | `docs/records/sea2/evidence/b2_2/caffeinate-observation.txt` |
| tracked file | `docs/sea2/evidence/b2_2/campaign.py` | `docs/records/sea2/evidence/b2_2/campaign.py` |
| tracked file | `docs/sea2/evidence/b2_2/central-plan.txt` | `docs/records/sea2/evidence/b2_2/central-plan.txt` |
| tracked file | `docs/sea2/evidence/b2_2/central-publication.json` | `docs/records/sea2/evidence/b2_2/central-publication.json` |
| tracked file | `docs/sea2/evidence/b2_2/central-regression.json` | `docs/records/sea2/evidence/b2_2/central-regression.json` |
| tracked file | `docs/sea2/evidence/b2_2/central-run.txt` | `docs/records/sea2/evidence/b2_2/central-run.txt` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-fill-impact-audit.json` | `docs/records/sea2/evidence/b2_2/cheung_chau-fill-impact-audit.json` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-fill-impact.txt` | `docs/records/sea2/evidence/b2_2/cheung_chau-fill-impact.txt` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-plan.txt` | `docs/records/sea2/evidence/b2_2/cheung_chau-plan.txt` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-publication.json` | `docs/records/sea2/evidence/b2_2/cheung_chau-publication.json` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-rays.json` | `docs/records/sea2/evidence/b2_2/cheung_chau-rays.json` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-regression.json` | `docs/records/sea2/evidence/b2_2/cheung_chau-regression.json` |
| tracked file | `docs/sea2/evidence/b2_2/cheung_chau-run.txt` | `docs/records/sea2/evidence/b2_2/cheung_chau-run.txt` |
| tracked file | `docs/sea2/evidence/b2_2/class-3-components.json` | `docs/records/sea2/evidence/b2_2/class-3-components.json` |
| tracked file | `docs/sea2/evidence/b2_2/coastline-access.json` | `docs/records/sea2/evidence/b2_2/coastline-access.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/central.json` | `docs/records/sea2/evidence/b2_2/configs/central.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/central_raw_reference.json` | `docs/records/sea2/evidence/b2_2/configs/central_raw_reference.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/cheung_chau.json` | `docs/records/sea2/evidence/b2_2/configs/cheung_chau.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/f1_cheung_chau_reference.json` | `docs/records/sea2/evidence/b2_2/configs/f1_cheung_chau_reference.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/five_class.json` | `docs/records/sea2/evidence/b2_2/configs/five_class.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/machine.json` | `docs/records/sea2/evidence/b2_2/configs/machine.json` |
| tracked file | `docs/sea2/evidence/b2_2/configs/validation_scopes.json` | `docs/records/sea2/evidence/b2_2/configs/validation_scopes.json` |
| tracked file | `docs/sea2/evidence/b2_2/copy-f1-reference.txt` | `docs/records/sea2/evidence/b2_2/copy-f1-reference.txt` |
| tracked file | `docs/sea2/evidence/b2_2/dsm-only-code-audit.json` | `docs/records/sea2/evidence/b2_2/dsm-only-code-audit.json` |
| tracked file | `docs/sea2/evidence/b2_2/engine-environment.json` | `docs/records/sea2/evidence/b2_2/engine-environment.json` |
| tracked file | `docs/sea2/evidence/b2_2/finalize_manifest.py` | `docs/records/sea2/evidence/b2_2/finalize_manifest.py` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-fill-impact-audit.json` | `docs/records/sea2/evidence/b2_2/five_class-fill-impact-audit.json` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-fill-impact-resume.txt` | `docs/records/sea2/evidence/b2_2/five_class-fill-impact-resume.txt` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-fill-impact.txt` | `docs/records/sea2/evidence/b2_2/five_class-fill-impact.txt` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-plan.txt` | `docs/records/sea2/evidence/b2_2/five_class-plan.txt` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-publication.json` | `docs/records/sea2/evidence/b2_2/five_class-publication.json` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-rays.json` | `docs/records/sea2/evidence/b2_2/five_class-rays.json` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-regression.json` | `docs/records/sea2/evidence/b2_2/five_class-regression.json` |
| tracked file | `docs/sea2/evidence/b2_2/five_class-run.txt` | `docs/records/sea2/evidence/b2_2/five_class-run.txt` |
| tracked file | `docs/sea2/evidence/b2_2/ib5000-reader.json` | `docs/records/sea2/evidence/b2_2/ib5000-reader.json` |
| tracked file | `docs/sea2/evidence/b2_2/ib5000-report.json` | `docs/records/sea2/evidence/b2_2/ib5000-report.json` |
| tracked file | `docs/sea2/evidence/b2_2/inventory-after.txt` | `docs/records/sea2/evidence/b2_2/inventory-after.txt` |
| tracked file | `docs/sea2/evidence/b2_2/inventory-before.txt` | `docs/records/sea2/evidence/b2_2/inventory-before.txt` |
| tracked file | `docs/sea2/evidence/b2_2/inventory.py` | `docs/records/sea2/evidence/b2_2/inventory.py` |
| tracked file | `docs/sea2/evidence/b2_2/manifest.json` | `docs/records/sea2/evidence/b2_2/manifest.json` |
| tracked file | `docs/sea2/evidence/b2_2/metadata-finalization.json` | `docs/records/sea2/evidence/b2_2/metadata-finalization.json` |
| tracked file | `docs/sea2/evidence/b2_2/postcheck.py` | `docs/records/sea2/evidence/b2_2/postcheck.py` |
| tracked file | `docs/sea2/evidence/b2_2/protected-after.json` | `docs/records/sea2/evidence/b2_2/protected-after.json` |
| tracked file | `docs/sea2/evidence/b2_2/protected-before.json` | `docs/records/sea2/evidence/b2_2/protected-before.json` |
| tracked file | `docs/sea2/evidence/b2_2/pytest-final.txt` | `docs/records/sea2/evidence/b2_2/pytest-final.txt` |
| tracked file | `docs/sea2/evidence/b2_2/pytest-full.txt` | `docs/records/sea2/evidence/b2_2/pytest-full.txt` |
| tracked file | `docs/sea2/evidence/b2_2/pytest-handoff.txt` | `docs/records/sea2/evidence/b2_2/pytest-handoff.txt` |
| tracked file | `docs/sea2/evidence/b2_2/pytest-resume.txt` | `docs/records/sea2/evidence/b2_2/pytest-resume.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-central-reference.txt` | `docs/records/sea2/evidence/b2_2/raw-plan-central-reference.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-default-candidate.txt` | `docs/records/sea2/evidence/b2_2/raw-plan-default-candidate.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-default-f1.txt` | `docs/records/sea2/evidence/b2_2/raw-plan-default-f1.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-f1_reference-candidate.txt` | `docs/records/sea2/evidence/b2_2/raw-plan-f1_reference-candidate.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-f1_reference-f1.txt` | `docs/records/sea2/evidence/b2_2/raw-plan-f1_reference-f1.txt` |
| tracked file | `docs/sea2/evidence/b2_2/raw-plan-identity.json` | `docs/records/sea2/evidence/b2_2/raw-plan-identity.json` |
| tracked file | `docs/sea2/evidence/b2_2/request-plan-keys.json` | `docs/records/sea2/evidence/b2_2/request-plan-keys.json` |
| tracked file | `docs/sea2/evidence/b2_2/resource-summary.json` | `docs/records/sea2/evidence/b2_2/resource-summary.json` |
| tracked file | `docs/sea2/evidence/b2_2/resources.jsonl` | `docs/records/sea2/evidence/b2_2/resources.jsonl` |
| tracked file | `docs/sea2/evidence/b2_2/scope.json` | `docs/records/sea2/evidence/b2_2/scope.json` |
| tracked file | `docs/sea2/evidence/b2_2/scope.py` | `docs/records/sea2/evidence/b2_2/scope.py` |
| tracked file | `docs/sea2/evidence/b2_2/sensitivity-report.json` | `docs/records/sea2/evidence/b2_2/sensitivity-report.json` |
| tracked file | `docs/sea2/evidence/b2_2/start.json` | `docs/records/sea2/evidence/b2_2/start.json` |
| tracked file | `docs/sea2/evidence/b2_2/territory-view-build.txt` | `docs/records/sea2/evidence/b2_2/territory-view-build.txt` |
| tracked file | `docs/sea2/evidence/b2_2/tools-environment.json` | `docs/records/sea2/evidence/b2_2/tools-environment.json` |
| tracked file | `docs/sea2/evidence/b2_2/validation.txt` | `docs/records/sea2/evidence/b2_2/validation.txt` |
| tracked file | `docs/sea2/evidence/b2_2/view-preflight.json` | `docs/records/sea2/evidence/b2_2/view-preflight.json` |
| tracked file | `docs/sea2/evidence/b2_2/view-preflight.txt` | `docs/records/sea2/evidence/b2_2/view-preflight.txt` |
| tracked file | `docs/sea2/evidence/b2_2/view-readback.json` | `docs/records/sea2/evidence/b2_2/view-readback.json` |
| tracked file | `docs/sea2/evidence/b2_2/view_preflight.py` | `docs/records/sea2/evidence/b2_2/view_preflight.py` |
| tracked file | `docs/sea2/evidence/build-1-budget-stop.json` | `docs/records/sea2/evidence/build-1-budget-stop.json` |
| tracked file | `docs/sea2/evidence/build-2-corrected.txt` | `docs/records/sea2/evidence/build-2-corrected.txt` |
| tracked file | `docs/sea2/evidence/build-2-correction-stop.json` | `docs/records/sea2/evidence/build-2-correction-stop.json` |
| tracked file | `docs/sea2/evidence/build-2.log.txt` | `docs/records/sea2/evidence/build-2.log.txt` |
| tracked file | `docs/sea2/evidence/campaign-controller.txt` | `docs/records/sea2/evidence/campaign-controller.txt` |
| tracked file | `docs/sea2/evidence/campaign.json` | `docs/records/sea2/evidence/campaign.json` |
| tracked file | `docs/sea2/evidence/catalogue-metadata-groups.json` | `docs/records/sea2/evidence/catalogue-metadata-groups.json` |
| tracked file | `docs/sea2/evidence/central-comparison.json` | `docs/records/sea2/evidence/central-comparison.json` |
| tracked file | `docs/sea2/evidence/central_land_comparison.txt` | `docs/records/sea2/evidence/central_land_comparison.txt` |
| tracked file | `docs/sea2/evidence/central_raw.txt` | `docs/records/sea2/evidence/central_raw.txt` |
| tracked file | `docs/sea2/evidence/central_sea.txt` | `docs/records/sea2/evidence/central_sea.txt` |
| tracked file | `docs/sea2/evidence/cheung-chau-noon-summary.json` | `docs/records/sea2/evidence/cheung-chau-noon-summary.json` |
| tracked file | `docs/sea2/evidence/cheung-chau-void-impact.json` | `docs/records/sea2/evidence/cheung-chau-void-impact.json` |
| tracked file | `docs/sea2/evidence/cheung_chau-comparison.json` | `docs/records/sea2/evidence/cheung_chau-comparison.json` |
| tracked file | `docs/sea2/evidence/cheung_chau-sea-rays.json` | `docs/records/sea2/evidence/cheung_chau-sea-rays.json` |
| tracked file | `docs/sea2/evidence/cheung_chau_land_comparison.txt` | `docs/records/sea2/evidence/cheung_chau_land_comparison.txt` |
| tracked file | `docs/sea2/evidence/cheung_chau_sea.txt` | `docs/records/sea2/evidence/cheung_chau_sea.txt` |
| tracked file | `docs/sea2/evidence/cheung_chau_sea_rays.txt` | `docs/records/sea2/evidence/cheung_chau_sea_rays.txt` |
| tracked file | `docs/sea2/evidence/cheung_chau_void_impact.txt` | `docs/records/sea2/evidence/cheung_chau_void_impact.txt` |
| tracked file | `docs/sea2/evidence/configs/central_raw.json` | `docs/records/sea2/evidence/configs/central_raw.json` |
| tracked file | `docs/sea2/evidence/configs/central_sea.json` | `docs/records/sea2/evidence/configs/central_sea.json` |
| tracked file | `docs/sea2/evidence/configs/cheung_chau_sea.json` | `docs/records/sea2/evidence/configs/cheung_chau_sea.json` |
| tracked file | `docs/sea2/evidence/configs/f1_cheung_chau.json` | `docs/records/sea2/evidence/configs/f1_cheung_chau.json` |
| tracked file | `docs/sea2/evidence/configs/machine.json` | `docs/records/sea2/evidence/configs/machine.json` |
| tracked file | `docs/sea2/evidence/configs/validation_scopes.json` | `docs/records/sea2/evidence/configs/validation_scopes.json` |
| tracked file | `docs/sea2/evidence/counterfactual-view-facts.json` | `docs/records/sea2/evidence/counterfactual-view-facts.json` |
| tracked file | `docs/sea2/evidence/engine-environment.json` | `docs/records/sea2/evidence/engine-environment.json` |
| tracked file | `docs/sea2/evidence/engine-plan-identity.json` | `docs/records/sea2/evidence/engine-plan-identity.json` |
| tracked file | `docs/sea2/evidence/f-publication-blocker-pytest.txt` | `docs/records/sea2/evidence/f-publication-blocker-pytest.txt` |
| tracked file | `docs/sea2/evidence/f-publication-blocker.json` | `docs/records/sea2/evidence/f-publication-blocker.json` |
| tracked file | `docs/sea2/evidence/final-scope-audit.json` | `docs/records/sea2/evidence/final-scope-audit.json` |
| tracked file | `docs/sea2/evidence/ib5000-report.json` | `docs/records/sea2/evidence/ib5000-report.json` |
| tracked file | `docs/sea2/evidence/initial-resource-notes.json` | `docs/records/sea2/evidence/initial-resource-notes.json` |
| tracked file | `docs/sea2/evidence/launcher-child-bootstrap.json` | `docs/records/sea2/evidence/launcher-child-bootstrap.json` |
| tracked file | `docs/sea2/evidence/launcher-correction.json` | `docs/records/sea2/evidence/launcher-correction.json` |
| tracked file | `docs/sea2/evidence/log-compaction.json` | `docs/records/sea2/evidence/log-compaction.json` |
| tracked file | `docs/sea2/evidence/manifest.json` | `docs/records/sea2/evidence/manifest.json` |
| tracked file | `docs/sea2/evidence/protected-after.json` | `docs/records/sea2/evidence/protected-after.json` |
| tracked file | `docs/sea2/evidence/protected-before.json` | `docs/records/sea2/evidence/protected-before.json` |
| tracked file | `docs/sea2/evidence/pytest-distance.txt` | `docs/records/sea2/evidence/pytest-distance.txt` |
| tracked file | `docs/sea2/evidence/pytest-full.txt` | `docs/records/sea2/evidence/pytest-full.txt` |
| tracked file | `docs/sea2/evidence/pytest-native-centres.txt` | `docs/records/sea2/evidence/pytest-native-centres.txt` |
| tracked file | `docs/sea2/evidence/pytest-surface-publication.txt` | `docs/records/sea2/evidence/pytest-surface-publication.txt` |
| tracked file | `docs/sea2/evidence/raw-identity-regression.json` | `docs/records/sea2/evidence/raw-identity-regression.json` |
| tracked file | `docs/sea2/evidence/readable_complete_sea_run.txt` | `docs/records/sea2/evidence/readable_complete_sea_run.txt` |
| tracked file | `docs/sea2/evidence/readable_sea_plan.txt` | `docs/records/sea2/evidence/readable_sea_plan.txt` |
| tracked file | `docs/sea2/evidence/readable_void_resume.txt` | `docs/records/sea2/evidence/readable_void_resume.txt` |
| tracked file | `docs/sea2/evidence/reader-availability.json` | `docs/records/sea2/evidence/reader-availability.json` |
| tracked file | `docs/sea2/evidence/real-run-provenance.json` | `docs/records/sea2/evidence/real-run-provenance.json` |
| tracked file | `docs/sea2/evidence/resource-summary.json` | `docs/records/sea2/evidence/resource-summary.json` |
| tracked file | `docs/sea2/evidence/resources.jsonl` | `docs/records/sea2/evidence/resources.jsonl` |
| tracked file | `docs/sea2/evidence/resume-budget.json` | `docs/records/sea2/evidence/resume-budget.json` |
| tracked file | `docs/sea2/evidence/scope-review.json` | `docs/records/sea2/evidence/scope-review.json` |
| tracked file | `docs/sea2/evidence/sea_plan.txt` | `docs/records/sea2/evidence/sea_plan.txt` |
| tracked file | `docs/sea2/evidence/sensitivity-report.json` | `docs/records/sea2/evidence/sensitivity-report.json` |
| tracked file | `docs/sea2/evidence/start.json` | `docs/records/sea2/evidence/start.json` |
| tracked file | `docs/sea2/evidence/synthetic-readback.json` | `docs/records/sea2/evidence/synthetic-readback.json` |
| tracked file | `docs/sea2/evidence/tools-environment.json` | `docs/records/sea2/evidence/tools-environment.json` |
| tracked file | `docs/sea2/evidence/tools-launcher.json` | `docs/records/sea2/evidence/tools-launcher.json` |
| tracked file | `docs/sea2/evidence/validation-attempt.txt` | `docs/records/sea2/evidence/validation-attempt.txt` |
| tracked file | `docs/sea2/evidence/view-facts.json` | `docs/records/sea2/evidence/view-facts.json` |
| tracked file | `docs/sea2/evidence/view_facts.txt` | `docs/records/sea2/evidence/view_facts.txt` |
| tracked file | `docs/sea2/evidence/void-impact-readback.json` | `docs/records/sea2/evidence/void-impact-readback.json` |
| tracked file | `docs/shade_map/DESIGN.md` | `docs/records/shade_map/DESIGN.md` |
| tracked file | `docs/shade_map/DEVELOPMENT_REPORT.md` | `docs/records/shade_map/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/shade_map/GUIDE.md` | `docs/records/shade_map/GUIDE.md` |
| tracked file | `docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md` | `docs/records/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md` |
| tracked file | `docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a_ADDENDUM_1.md` | `docs/records/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a_ADDENDUM_1.md` |
| tracked file | `docs/shade_map/INDEPENDENT_ACCEPTANCE_eb605f52d119.md` | `docs/records/shade_map/INDEPENDENT_ACCEPTANCE_eb605f52d119.md` |
| tracked file | `docs/shade_map/evidence/a_pixel_verification.json` | `docs/records/shade_map/evidence/a_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/b_pixel_verification.json` | `docs/records/shade_map/evidence/b_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/cheung_chau_1230_summary.json` | `docs/records/shade_map/evidence/cheung_chau_1230_summary.json` |
| tracked file | `docs/shade_map/evidence/cheung_chau_source_gate.json` | `docs/records/shade_map/evidence/cheung_chau_source_gate.json` |
| tracked file | `docs/shade_map/evidence/conflict_and_prune.json` | `docs/records/shade_map/evidence/conflict_and_prune.json` |
| tracked file | `docs/shade_map/evidence/environment.json` | `docs/records/shade_map/evidence/environment.json` |
| tracked file | `docs/shade_map/evidence/evidence_manifest.json` | `docs/records/shade_map/evidence/evidence_manifest.json` |
| tracked file | `docs/shade_map/evidence/final_traceability.json` | `docs/records/shade_map/evidence/final_traceability.json` |
| tracked file | `docs/shade_map/evidence/frozen_sparse_rectangle.json` | `docs/records/shade_map/evidence/frozen_sparse_rectangle.json` |
| tracked file | `docs/shade_map/evidence/full_tests.txt` | `docs/records/shade_map/evidence/full_tests.txt` |
| tracked file | `docs/shade_map/evidence/full_tests_initial_collection_error.txt` | `docs/records/shade_map/evidence/full_tests_initial_collection_error.txt` |
| tracked file | `docs/shade_map/evidence/independent_v1_reference.json` | `docs/records/shade_map/evidence/independent_v1_reference.json` |
| tracked file | `docs/shade_map/evidence/instant_pixel_verification.json` | `docs/records/shade_map/evidence/instant_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/interim_protected_audit.json` | `docs/records/shade_map/evidence/interim_protected_audit.json` |
| tracked file | `docs/shade_map/evidence/kill_compute_resume_verification.json` | `docs/records/shade_map/evidence/kill_compute_resume_verification.json` |
| tracked file | `docs/shade_map/evidence/kill_publish_resume_verification.json` | `docs/records/shade_map/evidence/kill_publish_resume_verification.json` |
| tracked file | `docs/shade_map/evidence/protected_after.json` | `docs/records/shade_map/evidence/protected_after.json` |
| tracked file | `docs/shade_map/evidence/protected_before.json` | `docs/records/shade_map/evidence/protected_before.json` |
| tracked file | `docs/shade_map/evidence/repair_1/a_original_raster_hashes.json` | `docs/records/shade_map/evidence/repair_1/a_original_raster_hashes.json` |
| tracked file | `docs/shade_map/evidence/repair_1/a_pixel_verification.json` | `docs/records/shade_map/evidence/repair_1/a_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/repair_1/b_original_raster_hashes.json` | `docs/records/shade_map/evidence/repair_1/b_original_raster_hashes.json` |
| tracked file | `docs/shade_map/evidence/repair_1/b_pixel_verification.json` | `docs/records/shade_map/evidence/repair_1/b_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/repair_1/cheung_chau_source_gate.json` | `docs/records/shade_map/evidence/repair_1/cheung_chau_source_gate.json` |
| tracked file | `docs/shade_map/evidence/repair_1/evidence_manifest.json` | `docs/records/shade_map/evidence/repair_1/evidence_manifest.json` |
| tracked file | `docs/shade_map/evidence/repair_1/frozen_campaign.json` | `docs/records/shade_map/evidence/repair_1/frozen_campaign.json` |
| tracked file | `docs/shade_map/evidence/repair_1/full_tests.txt` | `docs/records/shade_map/evidence/repair_1/full_tests.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/independent_v1_reference.json` | `docs/records/shade_map/evidence/repair_1/independent_v1_reference.json` |
| tracked file | `docs/shade_map/evidence/repair_1/instant_original_raster_hashes.json` | `docs/records/shade_map/evidence/repair_1/instant_original_raster_hashes.json` |
| tracked file | `docs/shade_map/evidence/repair_1/instant_pixel_verification.json` | `docs/records/shade_map/evidence/repair_1/instant_pixel_verification.json` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/a_plan.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/a_plan.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/a_plan.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/a_plan.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/a_run.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/a_run.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/a_run.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/a_run.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/all_verify.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/all_verify.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/all_verify.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/all_verify.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/b_plan.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/b_plan.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/b_plan.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/b_plan.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/b_run.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/b_run.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/b_run.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/b_run.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/full_tests.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/full_tests.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/full_tests.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/full_tests.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/full_tests_final.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/full_tests_final.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/full_tests_final.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/full_tests_final.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/instant_plan.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/instant_plan.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/instant_plan.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/instant_plan.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/instant_run.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/instant_run.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/instant_run.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/instant_run.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_check.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_check.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_check.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_check.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_incomplete.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_incomplete.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_incomplete.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_incomplete.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_kill.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_kill.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_kill.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_kill.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_resume.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_resume.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_compute_resume.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_compute_resume.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_check.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_check.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_check.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_check.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_incomplete.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_incomplete.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_incomplete.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_incomplete.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_kill.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_kill.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_kill.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_kill.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_resume.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_resume.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/kill_publish_resume.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/kill_publish_resume.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/partial_prune.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/partial_prune.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/partial_prune.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/partial_prune.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/protected_audit.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/protected_audit.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/protected_audit.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/protected_audit.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/source_gate.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/source_gate.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/source_gate.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/source_gate.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/v1_reference.stderr.txt` | `docs/records/shade_map/evidence/repair_1/jobs/v1_reference.stderr.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/jobs/v1_reference.stdout.txt` | `docs/records/shade_map/evidence/repair_1/jobs/v1_reference.stdout.txt` |
| tracked file | `docs/shade_map/evidence/repair_1/kill_compute_incomplete.json` | `docs/records/shade_map/evidence/repair_1/kill_compute_incomplete.json` |
| tracked file | `docs/shade_map/evidence/repair_1/kill_compute_resume.json` | `docs/records/shade_map/evidence/repair_1/kill_compute_resume.json` |
| tracked file | `docs/shade_map/evidence/repair_1/kill_publish_incomplete.json` | `docs/records/shade_map/evidence/repair_1/kill_publish_incomplete.json` |
| tracked file | `docs/shade_map/evidence/repair_1/kill_publish_resume.json` | `docs/records/shade_map/evidence/repair_1/kill_publish_resume.json` |
| tracked file | `docs/shade_map/evidence/repair_1/partial_and_prune.json` | `docs/records/shade_map/evidence/repair_1/partial_and_prune.json` |
| tracked file | `docs/shade_map/evidence/repair_1/protected_after.json` | `docs/records/shade_map/evidence/repair_1/protected_after.json` |
| tracked file | `docs/shade_map/evidence/repair_1/protected_before.json` | `docs/records/shade_map/evidence/repair_1/protected_before.json` |
| tracked file | `docs/shade_map/evidence/repair_1/resource_ledger.json` | `docs/records/shade_map/evidence/repair_1/resource_ledger.json` |
| tracked file | `docs/shade_map/evidence/repair_1/start.json` | `docs/records/shade_map/evidence/repair_1/start.json` |
| tracked file | `docs/shade_map/evidence/repair_1/traceability.json` | `docs/records/shade_map/evidence/repair_1/traceability.json` |
| tracked file | `docs/shade_map/evidence/resource_ledger.json` | `docs/records/shade_map/evidence/resource_ledger.json` |
| tracked file | `docs/shade_map/evidence/schema_rule_coverage.json` | `docs/records/shade_map/evidence/schema_rule_coverage.json` |
| tracked file | `docs/shade_map/evidence/sparse_plan_before_execution.json` | `docs/records/shade_map/evidence/sparse_plan_before_execution.json` |
| tracked file | `docs/shade_map/evidence/start.json` | `docs/records/shade_map/evidence/start.json` |
| tracked file | `docs/shade_map/evidence/synthetic_tests.txt` | `docs/records/shade_map/evidence/synthetic_tests.txt` |
| tracked file | `docs/shade_map/evidence/verification_harness_recursion.json` | `docs/records/shade_map/evidence/verification_harness_recursion.json` |
| tracked file | `docs/ui/API_REQUEST_SCHEMA.md` | `docs/records/ui/API_REQUEST_SCHEMA.md` |
| tracked file | `docs/ui/DESIGN.md` | `docs/records/ui/DESIGN.md` |
| tracked file | `docs/v1/DEVELOPMENT_REPORT.md` | `docs/records/v1/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/v1/GUIDE.md` | `docs/records/v1/GUIDE.md` |
| tracked file | `docs/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md` | `docs/records/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md` |
| tracked file | `docs/v1/POLICY.md` | `docs/records/v1/POLICY.md` |
| tracked file | `docs/v1/TRACEABILITY.md` | `docs/records/v1/TRACEABILITY.md` |
| tracked file | `docs/v2/CLOSEOUT.md` | `docs/records/v2/CLOSEOUT.md` |
| tracked file | `docs/v2/CLOSEOUT_EVIDENCE.json` | `docs/records/v2/CLOSEOUT_EVIDENCE.json` |
| tracked file | `docs/v2/DESIGN.md` | `docs/records/v2/DESIGN.md` |
| tracked file | `docs/v2/DEVELOPMENT_REPORT.md` | `docs/records/v2/DEVELOPMENT_REPORT.md` |
| tracked file | `docs/v2/ESTIMATOR.md` | `docs/records/v2/ESTIMATOR.md` |
| tracked file | `docs/v2/GUIDE.md` | `docs/records/v2/GUIDE.md` |
| tracked file | `docs/v2/INDEPENDENT_ACCEPTANCE_356f611.md` | `docs/records/v2/INDEPENDENT_ACCEPTANCE_356f611.md` |
| tracked file | `docs/v2/INDEPENDENT_ACCEPTANCE_e2fa0cd.md` | `docs/records/v2/INDEPENDENT_ACCEPTANCE_e2fa0cd.md` |
| tracked file | `docs/v2/INDEPENDENT_ACCEPTANCE_f3dac31.md` | `docs/records/v2/INDEPENDENT_ACCEPTANCE_f3dac31.md` |
| tracked file | `docs/v2/estimator.json` | `config/engine/estimator.json` |
| tracked file | `docs/v2/example_batch.json` | `docs/records/v2/example_batch.json` |
| tracked file | `docs/v3/RUNBOOK.md` | `docs/records/v3/RUNBOOK.md` |
| tracked file | `docs/v3/SCENE_PLAN.md` | `docs/records/v3/SCENE_PLAN.md` |
| tracked file | `docs/v3/STATUS.md` | `docs/records/v3/STATUS.md` |
| tracked file | `docs/v3/WSL2_SMOKE_TEST.md` | `docs/records/v3/WSL2_SMOKE_TEST.md` |
| tracked file | `outputs/README.md` | `docs/records/outputs_README.md` |
| tracked file | `src/.gitkeep` | `(remove)` |
| tracked file | `src/__init__.py` | `shade_watch/engine/__init__.py` |
| tracked file | `src/batch_tiles.py` | `legacy/pipeline/batch_tiles.py` |
| tracked file | `src/horizon.py` | `shade_watch/engine/horizon.py` |
| tracked file | `src/pipeline.py` | `shade_watch/engine/pipeline.py` |
| tracked file | `src/shade_watch.py` | `shade_watch/engine/shade_watch.py` |
| tracked file | `src/solar.py` | `shade_watch/engine/solar.py` |
| tracked file | `src/spatial.py` | `shade_watch/engine/spatial.py` |
| tracked file | `src/v1.py` | `shade_watch/engine/v1.py` |
| tracked file | `src/v1_cache.py` | `shade_watch/engine/v1_cache.py` |
| tracked file | `src/v2.py` | `shade_watch/engine/v2.py` |
| tracked file | `src/v2_runner.py` | `shade_watch/engine/v2_runner.py` |
| tracked file | `src/v2_state.py` | `shade_watch/engine/v2_state.py` |
| tracked file | `src/v2_worker.py` | `shade_watch/engine/v2_worker.py` |
| tracked file | `src/verify_chunking.py` | `legacy/pipeline/verify_chunking.py` |
| tracked file | `src/verify_mosaic.py` | `legacy/pipeline/verify_mosaic.py` |
| tracked file | `tests/.gitkeep` | `(remove)` |
| tracked file | `tests/shade_map_campaign.py` | `legacy/campaigns/f1/shade_map_campaign.py` |
| tracked file | `tests/shade_map_repair_campaign.py` | `legacy/campaigns/f1/shade_map_repair_campaign.py` |
| tracked file | `tests/test_sea_masks.py` | `legacy/b1_sea_view/test_sea_masks.py` |
| tracked file | `tools/city/__init__.py` | `shade_watch/city/__init__.py` |
| tracked file | `tools/city/__main__.py` | `shade_watch/city/__main__.py` |
| tracked file | `tools/city/ingest.py` | `shade_watch/city/ingest.py` |
| tracked file | `tools/city/profiles.py` | `shade_watch/city/profiles.py` |
| tracked file | `tools/region_request.py` | `shade_watch/region.py` |
| tracked file | `tools/sea2/__init__.py` | `shade_watch/fill/__init__.py` |
| tracked file | `tools/sea2/__main__.py` | `shade_watch/fill/__main__.py` |
| tracked file | `tools/sea2/build.py` | `shade_watch/fill/build.py` |
| tracked file | `tools/sea2/catalogue.py` | `shade_watch/fill/catalogue.py` |
| tracked file | `tools/sea2/checks.py` | `shade_watch/fill/checks.py` |
| tracked file | `tools/sea2/fill_impact.py` | `shade_watch/fill/fill_impact.py` |
| tracked file | `tools/sea2/profile.py` | `shade_watch/fill/profile.py` |
| tracked file | `tools/sea2/provider.py` | `shade_watch/fill/provider.py` |
| tracked file | `tools/sea2/resources.py` | `legacy/campaigns/b2_2/resources.py` |
| tracked file | `tools/sea2/rule.py` | `shade_watch/fill/rule.py` |
| tracked file | `tools/sea2/validate_ib5000.py` | `shade_watch/fill/validate_ib5000.py` |
| tracked file | `tools/sea2/validation_worker.py` | `shade_watch/fill/validation_worker.py` |
| tracked file | `tools/sea2/view.py` | `shade_watch/fill/view.py` |
| tracked file | `tools/sea_view/build.py` | `legacy/b1_sea_view/build.py` |
| tracked file | `tools/sea_view/checks.py` | `legacy/b1_sea_view/checks.py` |
| tracked file | `tools/sea_view/compare.py` | `legacy/b1_sea_view/compare.py` |
| tracked file | `tools/sea_view/development.py` | `legacy/b1_sea_view/development.py` |
| tracked file | `tools/sea_view/edge_diagnostic.py` | `legacy/b1_sea_view/edge_diagnostic.py` |
| tracked file | `tools/sea_view/extract.py` | `legacy/b1_sea_view/extract.py` |
| tracked file | `tools/sea_view/helpers.py` | `legacy/b1_sea_view/helpers.py` |
| tracked file | `tools/sea_view/ledger.py` | `legacy/b1_sea_view/ledger.py` |
| tracked file | `tools/sea_view/masks.py` | `legacy/b1_sea_view/masks.py` |
| tracked file | `tools/sea_view/rays.py` | `legacy/b1_sea_view/rays.py` |
| tracked file | `tools/sea_view/scan.py` | `legacy/b1_sea_view/scan.py` |
| tracked file | `tools/sea_view/sensitivity.py` | `legacy/b1_sea_view/sensitivity.py` |
| tracked file | `tools/sea_view/verify_edges.py` | `legacy/b1_sea_view/verify_edges.py` |
| tracked file | `tools/shade_map/__init__.py` | `shade_watch/publish/__init__.py` |
| tracked file | `tools/shade_map/__main__.py` | `shade_watch/publish/__main__.py` |
| tracked file | `tools/shade_map/common.py` | `shade_watch/publish/common.py` |
| tracked file | `tools/shade_map/config.py` | `shade_watch/publish/config.py` |
| tracked file | `tools/shade_map/planning.py` | `shade_watch/publish/planning.py` |
| tracked file | `tools/shade_map/publication.py` | `shade_watch/publish/publication.py` |
| tracked file | `tools/shade_map/runner.py` | `shade_watch/publish/runner.py` |
| tracked file | `tools/shade_map/sources.py` | `shade_watch/publish/sources.py` |
| tracked file | `tools/v1_development.py` | `legacy/campaigns/v1_development.py` |
| tracked file | `tools/v2_closeout.py` | `legacy/campaigns/v2_closeout.py` |
| tracked file | `tools/v2_development.py` | `legacy/campaigns/v2_development.py` |
| tracked file | `tools/v3_campaign.py` | `legacy/campaigns/v3_campaign.py` |
| tracked file | `tools/wsl2_smoke/make_pack.py` | `legacy/wsl2_smoke/make_pack.py` |
| tracked file | `tools/wsl2_smoke/run_smoke.py` | `legacy/wsl2_smoke/run_smoke.py` |
| tracked file | `tools/wsl2_smoke/setup_wsl.sh` | `legacy/wsl2_smoke/setup_wsl.sh` |
| tracked file | `web/.gitkeep` | `(remove)` |
| tracked file | `web/console/README.md` | `legacy/web/console/README.md` |
| tracked file | `web/console/api.js` | `legacy/web/console/api.js` |
| tracked file | `web/console/app.js` | `legacy/web/console/app.js` |
| tracked file | `web/console/index.html` | `legacy/web/console/index.html` |
| tracked file | `web/console/map.js` | `legacy/web/console/map.js` |
| tracked file | `web/console/mock.js` | `legacy/web/console/mock.js` |
| tracked file | `web/console/style.css` | `legacy/web/console/style.css` |
| tracked file | `web/index.html` | `legacy/web/index.html` |
| tracked file | `web/shade_map/README.md` | `web/viewer/README.md` |
| tracked file | `web/shade_map/app.js` | `web/viewer/app.js` |
| tracked file | `web/shade_map/codes.js` | `web/viewer/codes.js` |
| tracked file | `web/shade_map/data/cells.json` | `web/viewer/data/cells.json` |
| tracked file | `web/shade_map/hk1980.js` | `web/viewer/hk1980.js` |
| tracked file | `web/shade_map/index.html` | `web/viewer/index.html` |
| tracked file | `web/shade_map/make_cells_index.py` | `web/viewer/make_cells_index.py` |
| tracked file | `web/shade_map/map.js` | `web/viewer/map.js` |
| tracked file | `web/shade_map/request.js` | `web/viewer/request.js` |
| tracked file | `web/shade_map/results.js` | `web/viewer/results.js` |
| tracked file | `web/shade_map/stats.js` | `web/viewer/stats.js` |
| tracked file | `web/shade_map/style.css` | `web/viewer/style.css` |
| tracked file | `web/shade_map/sun.js` | `web/viewer/sun.js` |
| tracked file | `web/shade_map/tiff.js` | `web/viewer/tiff.js` |
| tracked file | `web/shade_map/util.js` | `web/viewer/util.js` |

</details>

The four renamed cache namespaces were moved only after both derived data comparisons passed. The six archived worktree folders were preserved and their registrations were pruned.

## Job ledger and limits

| Job | Start (+08:00) | End (+08:00) | Wall seconds | Peak GiB | New MiB | Exit |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| V-1 | 2026-11-12T22:07:36+08:00 | 2026-11-12T22:41:03+08:00 | 2007.59 | 0.615 | 3908.94 | 0 |
| V-1-compare | 2026-11-12T22:41:03+08:00 | 2026-11-12T22:46:54+08:00 | 350.35 | 0.233 | 0.06 | 0 |
| V-2 | 2026-11-12T22:46:54+08:00 | 2026-11-12T22:50:16+08:00 | 202.05 | 2.108 | 1268.48 | 0 |
| V-2-compare | 2026-11-12T22:50:17+08:00 | 2026-11-12T22:50:34+08:00 | 17.58 | 0.146 | 0.01 | 0 |
| R-1-plan | 2026-11-12T22:50:54+08:00 | 2026-11-12T22:52:21+08:00 | 86.69 | 0.291 | 0.11 | 0 |
| R-1 | 2026-11-12T22:52:23+08:00 | 2026-11-12T22:55:25+08:00 | 182.06 | 1.430 | 144.27 | 0 |
| R-1-compare | 2026-11-12T22:55:25+08:00 | 2026-11-12T22:55:25+08:00 | 0.32 | 0.041 | 0.00 | 1 |
| R-1-compare-utc | 2026-11-12T22:56:20+08:00 | 2026-11-12T22:56:20+08:00 | 0.32 | 0.041 | 0.00 | 1 |
| R-1-compare-final | 2026-11-12T22:56:52+08:00 | 2026-11-12T22:57:03+08:00 | 10.93 | 0.230 | 0.16 | 0 |
| R-2-plan | 2026-11-12T22:57:03+08:00 | 2026-11-12T22:59:30+08:00 | 146.95 | 0.325 | 0.19 | 0 |
| R-2 | 2026-11-12T22:59:31+08:00 | 2026-11-12T23:07:27+08:00 | 476.02 | 1.527 | 259.88 | 0 |
| R-2-compare | 2026-11-12T23:07:27+08:00 | 2026-11-12T23:08:04+08:00 | 36.34 | 0.226 | 0.51 | 0 |
| R-3-plan | 2026-11-12T23:08:04+08:00 | 2026-11-12T23:10:50+08:00 | 165.98 | 0.344 | 0.19 | 0 |
| R-3 | 2026-11-12T23:10:51+08:00 | 2026-11-12T23:23:12+08:00 | 741.10 | 1.441 | 450.80 | 0 |
| R-3-compare | 2026-11-12T23:23:13+08:00 | 2026-11-12T23:23:58+08:00 | 45.16 | 0.237 | 0.54 | 0 |
| R-4-plan | 2026-11-12T23:23:58+08:00 | 2026-11-12T23:27:24+08:00 | 205.84 | 0.327 | 0.19 | 0 |
| R-4 | 2026-11-12T23:27:25+08:00 | 2026-11-12T23:35:27+08:00 | 482.36 | 1.557 | 248.20 | 0 |
| R-4-compare | 2026-11-12T23:35:28+08:00 | 2026-11-12T23:36:02+08:00 | 34.27 | 0.242 | 0.52 | 0 |
| R-5-plan | 2026-11-12T23:36:03+08:00 | 2026-11-12T23:37:10+08:00 | 66.81 | 0.243 | 0.18 | 0 |
| R-5 | 2026-11-12T23:37:10+08:00 | 2026-11-12T23:39:15+08:00 | 124.86 | 1.357 | 79.48 | 0 |
| R-5-compare | 2026-11-12T23:39:16+08:00 | 2026-11-12T23:39:26+08:00 | 9.98 | 0.200 | 0.17 | 0 |
| R-6-plan | 2026-11-12T23:39:26+08:00 | 2026-11-12T23:39:35+08:00 | 8.62 | 0.230 | 0.00 | 0 |
| R-6 | 2026-11-12T23:39:36+08:00 | 2026-11-12T23:39:43+08:00 | 7.32 | 0.950 | 1.50 | 0 |
| R-6-compare | 2026-11-12T23:39:44+08:00 | 2026-11-12T23:39:44+08:00 | 0.59 | 0.082 | 0.02 | 0 |
| R-7 | 2026-11-12T23:39:45+08:00 | 2026-11-12T23:40:51+08:00 | 65.86 | 2.309 | 151.95 | 0 |
| R-7-compare | 2026-11-12T23:40:52+08:00 | 2026-11-12T23:40:52+08:00 | 0.44 | 0.039 | 0.01 | 0 |
| R-8 | 2026-11-12T23:40:53+08:00 | 2026-11-12T23:42:21+08:00 | 88.82 | 0.279 | 0.03 | 0 |

| Limit | Observed | Cap |
| --- | ---: | ---: |
| V-1 Hong Kong rebuild, one launch | 33.46 min | 60 min |
| V-2 Rotterdam registration, one launch | 3.37 min | 10 min |
| R-1 through R-8 jobs and plans | 47.49 min | 90 min |
| Peak process-tree memory | 2.309 GiB | 12 GiB |
| Cumulative new artifacts | 6.497 GiB | 15 GiB |

The meter ran under `caffeinate -dims` and used the sleep-inclusive Mac continuous clock. The first monitor setup was denied access to a system-wide process list before any scientific process was launched. The recorded jobs used job-scoped process enumeration. The memory ledger includes sampled concurrent RSS and the command high-water mark returned by `wait4`. The artifact meter sampled logical or allocated bytes, whichever was larger. Brief spikes between samples could be missed.

Hashing and raster comparison used 8.44 minutes of separately metered time. The contract excludes those direct checks from the 90-minute regression budget.

Command logs, comparison tables and the renamed-scope diff are under `archive/reviews/h1_0_dev_20261112/`. The [machine-readable ledger](evidence/resources.jsonl) names the stdout and stderr files for each job.

| Archived listing or log over 1 MB | Bytes | SHA-256 |
| --- | ---: | --- |
| `archive/reviews/h1_0_dev_20261112/derived_after_regression.json` | 2,192,764 | `0e210f0670d157cce1dc13cdaf15d49a7588391fe1f1c8a92ebe4ea7666ab778` |
| `archive/reviews/h1_0_dev_20261112/derived_before_regression.json` | 2,192,764 | `0e210f0670d157cce1dc13cdaf15d49a7588391fe1f1c8a92ebe4ea7666ab778` |
| `archive/reviews/h1_0_dev_20261112/inventory_after_all_moves.tsv` | 37,972,117 | `984db2913219a31490f580840c14cda2e411d6124a971eab16610643eed5c695` |
| `archive/reviews/h1_0_dev_20261112/inventory_after_data_moves.tsv` | 38,002,089 | `f0e2421bcef6b215e954dd1b833264bee573bb329857a928f894853f9590e446` |
| `archive/reviews/h1_0_dev_20261112/inventory_after_regression.tsv` | 37,972,117 | `984db2913219a31490f580840c14cda2e411d6124a971eab16610643eed5c695` |
| `archive/reviews/h1_0_dev_20261112/inventory_before.tsv` | 23,800,063 | `2836762dfdb5eb4d0a3f8846f37b8ebcb5ad5d8d73fea1fe8ac6cd0d49ec5436` |
