# H1.0 development repair 1

This report records the repair and development checks under SW-H1.0 through SW-H1.3. Independent re-acceptance is pending.

The repair starts at `bf30c1820df00d565f1815e05ebdef6c68b0698a` on `feature`, with parent `a70132cd7194b9a5961a18ef4b8b110b41c0b832`. The checkout was clean before edits. All six pinned document hashes, the three protected cache-key hashes, and the view and catalogue pointers matched. SW-H1.3 has SHA-256 `80151b31c9e77c71dd0872f9d08a26a2f62532971344b7454ef48d31139945b5`. [Preflight](evidence/repair_1/preflight.txt)

Fresh R-1 through R-6 matched 9,618 reference raster comparisons with zero differing pixels and zero recomputed horizon directions. R-7 matched the five reference records and the raw catalogue hash. Observational accuracy is **NOT VERIFIED** for both cities.

## Changes

| File | Reason |
| --- | --- |
| `shade_watch/engine/shade_watch.py` | A6 removes the command-module alias. |
| `shade_watch/engine/v2.py` | A6 removes the command-module alias and its added `sys` import. |
| `shade_watch/engine/pipeline.py` | A7 points the two code hashes at `shade_watch/engine/`. |
| `tests/test_layout.py` | A7 adds a pattern for a standalone quoted old directory name to the existing layout test. |
| `config/schema/shade_map_machine.schema.json` | A8 sets the machine default to `runs/main`. |
| `config/machine.example.json` | A8 sets the example root to `runs/main`. |
| `web/viewer/request.js` | A8 updates the output-root field and its fallback. |
| `web/viewer/results.js` | A8 updates the result-root field and deep-link fallback. |
| `web/viewer/README.md` | A8 records the default root. A10 records the source view ID and its full manifest SHA-256. |
| `config/engine/study_area.md` | A10 updates the two config paths used in the prose. |
| `config/machine.local.json` (ignored) | A8 changes only `output_root` to `runs/main`. |
| `runs/.shade_map_root.json` (ignored) | A8 removes the marker from the shared container. |
| `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md` and `evidence/repair_1/` | A11 adds this report, input copies, validation results and the job ledger. |

The six region copies change only `name` and use the `h1_0_dev2_` prefix. The regression machine copy sets the output root to `runs/h1_0_dev2_20261113` and uses four workers. The full change list, layout patterns and protected fingerprints are in the static checks. [Product diff](../../../archive/reviews/h1_0_dev2_20261113/product.patch) · [Static checks](evidence/repair_1/static.json) · [Inputs](evidence/repair_1/configs/) · [Local config diff](evidence/repair_1/machine-local.diff.txt)

## Criteria

These verdicts describe the repair development evidence. Carried-over evidence refers to the first independent review. The reviewer will run the targeted checks in part C of SW-H1.2.

| Item | Verdict | Evidence |
| --- | --- | --- |
| H1-01 | PASS | The ten modified tracked product and test files are exactly the A6–A10 scope. The diff of the three engine files from `dc7ad08` contains only module names and paths. The commit is on the SW-H1.3 starting commit. [Scoped diff](../../../archive/reviews/h1_0_dev2_20261113/product.patch) · [Origin diff](../../../archive/reviews/h1_0_dev2_20261113/engine-origin.patch) |
| H1-02 | PASS | All three cache-key hashes match the contract, and the source text of `fingerprint` and `profile` matches `dc7ad08`. [Static checks](evidence/repair_1/static.json) |
| H1-03 | PASS | The six layout tests pass, including the expanded quoted-name scan and the estimator exclusion. The 16 × 16 synthetic DSM pipeline completed 65 frames with 196 matching output rasters and 27 matching cache rasters. [Layout test](../../../archive/reviews/h1_0_dev2_20261113/jobs/layout.stdout) · [Synthetic results](evidence/repair_1/synthetic.json) |
| H1-04 | PASS | Carried over from the first review. Records, estimator and legacy paths are byte-identical to the first candidate. The record-manifest test passed. [Static checks](evidence/repair_1/static.json) · [First review](ACCEPTANCE_REPORT_84dc81fddb3b.md) |
| H1-05 | PASS | The planner mapping was repeated for 133,197 files and 5,889 symlinks with zero size, mtime or link discrepancies. The earlier raw hash sample remains applicable. The root-marker deletion is the A8 exception. [Planner comparison](evidence/repair_1/planner-inventory.json) |
| H1-06 | PASS | The repaired test IDs equal all 308 of `84dc81f`. All 308 passed. [Test IDs](evidence/repair_1/test-ids.json) · [Full suite](../../../archive/reviews/h1_0_dev2_20261113/jobs/tests.stdout) |
| H1-07 | PASS | The frozen city, sea-profile and region config blobs match `dc7ad08`. Only the allowed machine defaults differ in the schema. Both R-8 plans resolve to Hong Kong raw. The G1-06 rejection evidence carries over because the rejection code and city config are unchanged. [Explicit plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-explicit.stdout) · [Legacy plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-legacy.stdout) · [First review](ACCEPTANCE_REPORT_84dc81fddb3b.md) |
| H1-08 | PASS | Carried over from the first review. The Hong Kong view builder, pointer and manifest identity are preserved. The runtime inventory found zero changes under the view. [Derived identities](evidence/repair_1/derived-manifests.json) · [First review](ACCEPTANCE_REPORT_84dc81fddb3b.md) |
| H1-09 | PASS | Carried over from the first review. Rotterdam view and ingestion code, pointers, and manifests are preserved. The first review had reproduced both IDs in a fresh registration. [Derived identities](evidence/repair_1/derived-manifests.json) · [First review](ACCEPTANCE_REPORT_84dc81fddb3b.md) |
| H1-10 | PASS | R-1 to R-6 each planned and computed zero missing directions. The G1 spatial keys match for R-2 to R-4. All 6 existing cache namespaces were preserved through R-8. [Before R-7](evidence/repair_1/runtime-before-r7.json) · [After R-8](evidence/repair_1/runtime-after.json) |
| H1-11 | PASS | All 9,618 raster comparisons matched. R-1 uses the E2.0 UTC index. R-2 to R-6 match frame order, date and time folders, per-frame counts and all rasters. R-7 matches the frame records and raw catalogue hash. [Regression table](#regression-results) |
| H1-12 | PASS | The runtime inventories confirm the D1 paths. The jobs used the F publication format, kept earlier work and cache entries intact, and created one new R-7 namespace. Both old roots and the container marker are absent. [Final runtime audit](evidence/repair_1/runtime-after.json) |
| H1-13 | PASS | The package imports lazily. Synthetic CLI probes emitted no duplicate-import warning. The pipeline and V2 entry preserve the parent module-loading behavior exercised by the fixtures. Both synthetic publication roots were created by the CLI. R-6 used the public API. The local and example configs, viewer defaults and viewer provenance match A8 and A10. [Synthetic results](evidence/repair_1/synthetic.json) · [Static checks](evidence/repair_1/static.json) |
| H1-14 | NOT VERIFIED | The R-4 meter lost its final row after publication completed. The engine RSS and a conservative wall-time debit are available. The full process-tree peak for R-4 is unverified. The first development report holds the original move table and ledger. [Repair ledger](evidence/repair_1/resources.jsonl) · [R-4 recovery record](evidence/repair_1/R-4-meter-recovery.json) · [First development report](DEVELOPMENT_REPORT.md) |

## Regression results

| Run | Name | Frames | Rasters | Differing pixels | Directions computed | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| R-1 | `h1_0_dev2_hk1` | 65 | 780 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-1-plan.stdout) · [Execution](evidence/repair_1/R-1-execution.json) · [Comparison](evidence/repair_1/R-1-comparison.json) |
| R-2 | `h1_0_dev2_lo_wu` | 146 | 2,628 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-2-plan.stdout) · [Execution](evidence/repair_1/R-2-execution.json) · [Comparison](evidence/repair_1/R-2-comparison.json) |
| R-3 | `h1_0_dev2_tai_mo_shan` | 146 | 2,628 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-3-plan.stdout) · [Execution](evidence/repair_1/R-3-execution.json) · [Comparison](evidence/repair_1/R-3-comparison.json) |
| R-4 | `h1_0_dev2_central` | 146 | 2,628 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-4-plan.stdout) · [Execution](evidence/repair_1/R-4-execution.json) · [Comparison](evidence/repair_1/R-4-comparison.json) |
| R-5 | `h1_0_dev2_nl1` | 50 | 900 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-5-plan.stdout) · [Execution](evidence/repair_1/R-5-execution.json) · [Comparison](evidence/repair_1/R-5-comparison.json) |
| R-6 | `h1_0_dev2_nl2` | 3 | 54 | 0 | 0 | [Plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-6-plan.stdout) · [Execution](evidence/repair_1/R-6-execution.json) · [Comparison](evidence/repair_1/R-6-comparison.json) |
| R-7 | `h1_0_dev2_nl1` fill-impact | 5 | — | — | 20 | [Prelaunch cache gate](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-7-gate.stdout) · [Comparison](evidence/repair_1/R-7-comparison.json) |
| R-8 | Hong Kong compatibility plans | — | — | — | Plan only | [Explicit raw](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-explicit.stdout) · [Legacy without source](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-legacy.stdout) |

R-7 created `data/cache/horizon/fill_impact_8af8c5a39aa7` after the prelaunch check confirmed the path was absent. Its raw catalogue SHA-256 is `4b44b22b73f1da3809d9994d6e81f7134fb29e6d21b11f60a4b5a3e153753718`.

The run manifests record the starting Git commit with a dirty checkout because the repair was tested before its single commit. Their engine hashes match the repaired files.

## Job ledger and limits

Jobs were metered from launch with `caffeinate -dims` and `mach_continuous_time`. Memory is the maximum of sampled process-tree RSS and the command high-water mark. The artifact meter samples logical or allocated size, whichever is larger. The wrapper rejects re-entry from workers. Direct comparisons, synthetic cases and test runs are recorded separately from the R-1 to R-8 clock. The jobs used local inputs with `PROJ_NETWORK=OFF`.

A tool connection reset interrupted the R-4 meter before its final row was persisted. The completed command output, engine metrics and sealed 146-frame publication were recovered. R-4 was debited 530.76 seconds from the original launch to the first observed complete output, rounded up. Its engine-phase peak RSS was 1.500 GiB. The whole-job memory and artifact peaks for that run remain unverified. The resumed meter carried the full debit forward. [R-4 recovery record](evidence/repair_1/R-4-meter-recovery.json)

| Resource | Observed | Limit |
| --- | ---: | ---: |
| R-1 to R-8 jobs and plans, including the R-4 debit | 52.97 min | 90 min |
| Peak measured whole-job RSS (complete rows) | 2.254 GiB | 12 GiB |
| Peak recorded new artifacts | 1.399 GiB | 10 GiB |
| Hong Kong rebuilds and Rotterdam registrations | 0 | 0 |

| Job | Start (+08:00) | End (+08:00) | Wall seconds | Peak RSS GiB | Peak artifacts MiB | Exit |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| [R-1-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-1-plan.stdout) | 2026-11-13T06:10:31+08:00 | 2026-11-13T06:12:21+08:00 | 109.21 | 0.263 | 23.89 | 0 |
| [collect](../../../archive/reviews/h1_0_dev2_20261113/jobs/collect.stdout) | 2026-11-13T06:11:44+08:00 | 2026-11-13T06:11:52+08:00 | 8.23 | 0.137 | 23.23 | 0 |
| [layout](../../../archive/reviews/h1_0_dev2_20261113/jobs/layout.stdout) | 2026-11-13T06:11:53+08:00 | 2026-11-13T06:11:59+08:00 | 5.23 | 0.033 | 23.24 | 0 |
| [tests](../../../archive/reviews/h1_0_dev2_20261113/jobs/tests.stdout) | 2026-11-13T06:12:00+08:00 | 2026-11-13T06:13:54+08:00 | 114.32 | 0.965 | 52.80 | 0 |
| [R-1](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-1.stdout) | 2026-11-13T06:12:22+08:00 | 2026-11-13T06:15:54+08:00 | 212.19 | 1.502 | 195.96 | 0 |
| [synthetic](../../../archive/reviews/h1_0_dev2_20261113/jobs/synthetic.stdout) | 2026-11-13T06:13:02+08:00 | 2026-11-13T06:13:16+08:00 | 14.51 | 0.438 | 42.79 | 0 |
| [R-2-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-2-plan.stdout) | 2026-11-13T06:15:57+08:00 | 2026-11-13T06:19:41+08:00 | 224.67 | 0.312 | 233.13 | 0 |
| [R-1-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-1-compare.stdout) | 2026-11-13T06:17:00+08:00 | 2026-11-13T06:17:20+08:00 | 19.99 | 0.124 | 196.07 | 0 |
| [planner-inventory](../../../archive/reviews/h1_0_dev2_20261113/jobs/planner-inventory.stdout) | 2026-11-13T06:18:01+08:00 | 2026-11-13T06:18:09+08:00 | 7.88 | 0.311 | 233.10 | 0 |
| [R-2](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-2.stdout) | 2026-11-13T06:19:44+08:00 | 2026-11-13T06:30:54+08:00 | 670.06 | 1.549 | 493.05 | 0 |
| [R-3-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-3-plan.stdout) | 2026-11-13T06:30:56+08:00 | 2026-11-13T06:33:53+08:00 | 176.20 | 0.310 | 493.39 | 0 |
| [R-2-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-2-compare.stdout) | 2026-11-13T06:31:08+08:00 | 2026-11-13T06:31:20+08:00 | 11.58 | 0.050 | 493.36 | 0 |
| [R-3](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-3.stdout) | 2026-11-13T06:33:55+08:00 | 2026-11-13T06:44:51+08:00 | 655.50 | 1.494 | 944.19 | 0 |
| [R-4-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-4-plan.stdout) | 2026-11-13T06:44:53+08:00 | 2026-11-13T06:47:59+08:00 | 185.48 | 0.316 | 944.52 | 0 |
| [R-3-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-3-compare.stdout) | 2026-11-13T06:45:23+08:00 | 2026-11-13T06:45:52+08:00 | 28.73 | 0.054 | 944.49 | 0 |
| [R-4](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-4.stdout) | 2026-11-13T06:48:02+08:00 | Observed complete 2026-11-13T06:56:52+08:00 | 530.76 debit | Unavailable | Unavailable | Completed publication |
| [R-5-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-5-plan.stdout) | 2026-11-13T06:58:28+08:00 | 2026-11-13T06:59:44+08:00 | 76.02 | 0.235 | 1193.07 | 0 |
| [R-4-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-4-compare.stdout) | 2026-11-13T06:58:36+08:00 | 2026-11-13T06:59:01+08:00 | 25.35 | 0.049 | 1193.04 | 0 |
| [R-5](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-5.stdout) | 2026-11-13T06:59:47+08:00 | 2026-11-13T07:02:06+08:00 | 139.19 | 1.275 | 1272.54 | 0 |
| [R-6-plan](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-6-plan.stdout) | 2026-11-13T07:02:09+08:00 | 2026-11-13T07:02:21+08:00 | 12.34 | 0.204 | 1272.56 | 0 |
| [R-6](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-6.stdout) | 2026-11-13T07:02:24+08:00 | 2026-11-13T07:02:32+08:00 | 7.90 | 0.939 | 1274.18 | 0 |
| [R-5-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-5-compare.stdout) | 2026-11-13T07:02:24+08:00 | 2026-11-13T07:02:27+08:00 | 2.84 | 0.046 | 1272.67 | 0 |
| [R-6-compare](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-6-compare.stdout) | 2026-11-13T07:02:50+08:00 | 2026-11-13T07:02:50+08:00 | 0.47 | 0.042 | 1275.88 | 0 |
| [R-7-gate](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-7-gate.stdout) | 2026-11-13T07:03:19+08:00 | 2026-11-13T07:03:21+08:00 | 2.70 | 0.145 | 1277.55 | 0 |
| [R-7](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-7.stdout) | 2026-11-13T07:03:24+08:00 | 2026-11-13T07:04:31+08:00 | 67.25 | 2.254 | 1429.34 | 0 |
| [R-8-explicit](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-explicit.stdout) | 2026-11-13T07:04:34+08:00 | 2026-11-13T07:05:41+08:00 | 66.61 | 0.250 | 1429.37 | 0 |
| [R-8-legacy](../../../archive/reviews/h1_0_dev2_20261113/jobs/R-8-legacy.stdout) | 2026-11-13T07:05:44+08:00 | 2026-11-13T07:06:26+08:00 | 42.06 | 0.259 | 1429.39 | 0 |

[Commands and raw measurements](evidence/repair_1/resources.jsonl) · [Meter](../../../archive/reviews/h1_0_dev2_20261113/meter.py) · [Regression harness](../../../archive/reviews/h1_0_dev2_20261113/run_regression.sh) · [Raster comparator](../../../archive/reviews/h1_0_dev2_20261113/compare.py) · [Synthetic harness](../../../archive/reviews/h1_0_dev2_20261113/synthetic.py)

| Archived listing over 1 MB | Bytes | SHA-256 |
| --- | ---: | --- |
| [`meter-before.json`](../../../archive/reviews/h1_0_dev2_20261113/meter-before.json) | 2,842,347 | `e80c5beeb260e29e169befe92e5484d7634a94d57a964fe30d292f1ac574a28c` |
| [`planner-to-present.tsv`](../../../archive/reviews/h1_0_dev2_20261113/planner-to-present.tsv) | 38,806,649 | `3d1d480ed00d3bb178a03882ccd1e0396249fe57db8104938a2d2976c9eb3e97` |
| [`runtime_after.tsv.gz`](../../../archive/reviews/h1_0_dev2_20261113/runtime_after.tsv.gz) | 3,506,523 | `6de6df201dfcb5c80803982e45840518c3ffad46edbf64a87ca3719c3ece160d` |
| [`runtime_before.tsv.gz`](../../../archive/reviews/h1_0_dev2_20261113/runtime_before.tsv.gz) | 3,294,302 | `e2e26200f00e7462b05e7fb3434fd75470233eb472e0fbeeba1ddc4481fbe22e` |
| [`runtime_before_r7.tsv.gz`](../../../archive/reviews/h1_0_dev2_20261113/runtime_before_r7.tsv.gz) | 3,503,839 | `367ef0b9521115661806e492ce5ff92a0ca7fa673d73cdf3cd12e11ef4bd14e8` |
