# Independent V2 acceptance — 356f611

**Engineering gate: ACCEPTED — B01–B14 all PASS. No open blocking defects.** Real-world observational accuracy remains **NOT VERIFIED**. Completed 2026-10-09, Asia/Hong_Kong.

Evaluated immutable candidate: `356f611d7b775ce31006904b80ca31d3c1c484b2`. V2 starting commit: `f0598140c735786fba7d0b193c57b2aaa8564825`. Accepted V1: `796ac8abf05b92f1fbbac23a4aa0f18c9d944101`. Earlier candidates `e2fa0cde8e104439eb0c05e9bf9f549edffd6797` and `f3dac3175706988591387b22a56ee9857afad276` retain their **FAIL** gates; this acceptance applies to the repaired candidate above.

- V1 contract `SW-V1-AC-1.0`: `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
- V2 contract `SW-V2-AC-1.0`: `236198cdc0cc202d5e4278b6db7baa7c79c3ef710d123faa51b1683e5537b0ac`.
- Accepted V1 report: `cc7a9f2fd0d1db5c3ae6339742f703cbf68a3ed2dd3188072110e6d46c005510`.
- Frozen estimator: `ad6939e4455d9e80495d27e382438d635f5cb9f0920601959e09bbbe2e721469`.
- Final independent case manifest: `530c85076eb563f2150b3671ee342c196a4ebbd561fe6cf23ca2c9ee67a012fa`.

## Evidence and scope

Final evidence (**Final** below): `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_356f611/evidence`. Prior full reacceptance evidence (**f3** below): `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_f3dac31/evidence`. First-campaign evidence (**e2** below): `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_e2fa0cd/evidence`. File names in the matrix resolve under these roots.

Final checks directly execute 356f611 or exact owned source copies. Real DSM hold-outs, scientific regressions, fault/queue coverage and optimization measurements were executed on f3dac31 and are inherited with that SHA attribution; they were **not rerun on 356f611**. The production difference is solely the legacy-index guard in `src/v2_worker.py::_prepare`; the scheduler, numerical code, scientific/cache policy and estimator are unchanged. The candidate also adds two legacy tests and compatibility documentation. The final guard, current-index recovery, concurrency, receipts and engine identity were independently exercised, and the entire current test suite was rerun.

`initial_provenance.json` pins 31 source/test/contract/report/model/document files to the candidate. `final_audit.json` verifies them against Git; the 30 current files outside GUIDE match exactly. The coordinator's subsequent GUIDE overlay adds explicit historical `dsm_dir` to its example. README/input README/example and V3 preparation are separate authorized documentation/tool overlays, outside the evaluated implementation. No V3 tool was run by this reviewer.

Original input is the historical 19 TIFFs under `data/raw/dsm/2020_HKUST_Around/D12.DSM.TIFF`. Every TIFF hash still matches the original campaign. The f3 relocation audit correctly maps the entire old folder and verifies 120 original scientific/alternate-format/metadata files; its other differences are two Finder files and the input README. B/D buffered spatial cache identities agree across relocation. Every real review request uses an explicit historical `dsm_dir`. The newly downloaded 3310-file directory and developer's supplementary 29-source run are outside this independent gate.

Environment: macOS 15.7.4 arm64, Python 3.12.5, 10 logical CPUs, 24 GiB RAM, local external HFS disk, existing virtual environment/dependencies. No dependency installation or data download was needed. [Final audit](</Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_356f611/evidence/final_audit.json>) records environment, free disk, hashes, preserved file counts and budgets. [Evidence manifest](</Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_356f611/evidence/manifest.json>) inventories all three owned campaigns and all three reports with SHA-256 hashes.

## Acceptance matrix

| ID | Result | Independent evidence and reason |
| --- | --- | --- |
| B01 | PASS | Final `initial_provenance.json`, `final_audit.json`; accepted V1/report, both unchanged contracts, starting/candidate SHAs, environment and 19 input identities pinned. All 6,170 prior evidence/cache files remain byte-identical, with the same file set. |
| B02 | PASS | f3 `planning.json`, `cli.json`; planning traps establish zero computation/publication, compatible single/batch APIs and six CLI actions work. Final `reaccept_identity.json` proves runner/state changes create new IDs and runnable definitions while immutable old batches reject changed code. |
| B03 | PASS | f3 `controller_loss.json`, `worker_loss.json`, `corruption.json`; fresh controller recovery preserves committed work and failure history. Final `reaccept_contexts.json`, `final_index_corruption.json` prove missing receipts/corrupt indexes become INCOMPLETE and recover independently before success. |
| B04 | PASS | f3 overlap/date reuse checks plus Final `reaccept_contexts.json`, `final_legacy.json`; genuinely simultaneous current publishers keep one stable index and separate correct receipts. Genuine old V1/V2 results remain byte-identical and old V2 store checksums remain valid. |
| B05 | PASS | f3 `worker_loss.json`, `controller_loss.json`, `cancel.json`, `partial_publish.json`, `stale_ownership.json`; owned kernel/controller termination, separate cancellation, interrupted publication and stale ownership recover. Verified completed directions are reused; unrelated sentinel processes survive. |
| B06 | PASS | f3 `unavailable.json`, `write_failure.json`, `quota.json`, `corruption.json`, `retry_ceiling.json`, `media.json`; preflight input failure, actual worker publication faults, bounded attempts, request isolation and zero-horizon media-only recovery give truthful states. Final damaged-current-index recovery also passes. |
| B07 | PASS | f3 `queue.json`, `admission.json`, `independent_resource_crosscheck.json`; 10/40-request queues at one in-flight task complete, parent growth is 3,047,424 bytes, and unsafe worker/memory/disk requests are rejected. Safe real one/two-worker behavior is independently sampled; monitoring limitations are disclosed below. |
| B08 | PASS | f3 `scientific_regression.json`, `numerical_regression.json`; accepted V1 versus V2 exact shade/quality/georeferencing, horizon tolerance and exact support, using separate cold caches, day/night, arbitrary UTC/HKT instants, one/two workers, changed order, odd/boundary/custom crops. Numerical code is unchanged on Final. |
| B09 | PASS | f3 scientific/media/statistics/logical-view comparisons and `media.json`; pixels/transforms agree, optional statistics retain authoritative rasters, and media-only resume reuses horizons. `reaccept_overlap_verify.json` corrects the retained reviewer window-shape assertion and verifies the actual requested source subset. |
| B10 | PASS | f3 `estimator_all_residuals.json`, raw predictions/results/journals and `independent_resource_crosscheck.json`; three >=10 s in-domain cold/fully-warm/mixed trials, zero final hits, unchanged coefficients, median/max APE 15.63%/19.38%, all observed resource peaks covered by provisional ceilings. |
| B11 | PASS | f3 `reaccept_projection.json`; explicitly illustrative tile/effective-pixel/direction/query/cache/output/hardware assumptions and engineering ranges, excluded costs and extrapolation flags. No claim that the local gate validates territory-scale accuracy. |
| B12 | PASS | f3 `optimization.json`; matched inventory calls 6 → 2, 598,012,232 fewer source bytes hashed, identical science and full planning/execution timings. Initial timing regression and separate final-result reuse remain disclosed. |
| B13 | PASS | Final `existing_tests.log`: **73 passed**, 394 warnings, 45.94 s. Additional independent fixtures, real hold-outs and new samples are frozen separately from developer tuning; all original failure evidence and corrective reviewer assertions are preserved. |
| B14 | PASS | Immutable repaired source, tests, API/CLI commands, state/recovery and legacy compatibility documentation, three versioned reports, budget ledger and hashed manifest delivered. Large owned output/cache artifacts are ignored by Git. |

## Closed P1 defects

1. **Engine identity omitted runner/state hashes** (e2 FAIL). Owned copies append a behavior-neutral comment separately to each file. Final planning changes the batch ID, saves a distinct definition and executes successfully; the old immutable batch refuses the modified engine. Evidence: Final `reaccept_identity.json`; affected path `src/v2.py` engine fingerprinting. Original `e2/identity_change_defect.json` is preserved.
2. **Concurrent execution contexts invalidated a shared index** (e2 FAIL). Two real simultaneous controllers with different state/batch/request/cache contexts and workers1/2 now succeed. Shared index bytes remain stable, each execution has its own verified receipt, a third fresh-cache context reuses final frames, and deleting its receipt triggers index-only recovery. Earlier batches remain valid. Evidence: Final `reaccept_contexts.json`; affected paths `src/v2_worker.py` publication and `src/v2_state.py` artifact validation. Original `e2/competing_writer_defect.json` is preserved.
3. **Implicit legacy result-index migration invalidated an older store** (f3 FAIL). Independent owned copies first publish genuine old V2 schema 1.0 and genuine V1 schema 1.0 outputs using the historical production APIs, then install exact Final source. Publication to each old output fails once with a nonretryable read-only error. All old output/cache file hashes remain unchanged; old V2 status stays SUCCEEDED. A fresh output explicitly reuses the old scientific cache: zero horizon calls, one reused direction, zero final-result hits, exact shade/quality/transform agreement. Evidence: [genuine legacy reproduction](</Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_356f611/evidence/final_legacy.json>), owned `legacy_v1_copy/` and `legacy_v2_copy/`; repaired path `src/v2_worker.py::_prepare`, lines 40–57. Original `f3/cross_version_output.json` is preserved.

The adjacent regression damages a current schema-1.1 index. Fresh-process resume restores its original bytes without repeating horizon/frame attempts or altering scientific files. Evidence: Final `final_index_corruption.json`. The legacy guard therefore preserves current-version recoverability.

## Measured estimator and scientific results

These measurements are from **f3dac31**. Each prediction was saved before execution; all residuals, including the initial campaign, remain published.

| Configuration | Workers/order | Predicted s | Observed s | APE |
| --- | --- | ---: | ---: | ---: |
| Cold: B/D, 2027-07-11 08:23:37 and 2027-11-09 15:17:43 HKT | 2/forward | 23.568 | 20.382 | 15.63% |
| Warm: B/D, 2027-05-14/15 13:17:07/13 HKT, 48 seconds each | 1/reverse | 53.726 | 51.845 | 3.63% |
| Mixed: B cached, D cold, 2027-10-06 09:33:21 and 2027-03-03 15:29:17 HKT | 2/reverse | 23.568 | 19.743 | 19.38% |

Median APE **15.63% <=30%**; maximum **19.38% <=60%**. The fully warm trial fulfills the previously frozen supplement with the complete four-entry directional union, 192 new native frames, zero horizon calls and zero final hits. The initial e2 warm-labeled trial actually missed two directions and is retained as mixed; it does not substitute for the complete warm gate. Estimator coefficients were never tuned during review.

| Configuration | Observed sampled memory bytes | Predicted ceiling bytes | Observed peak generated disk bytes | Predicted ceiling bytes |
| --- | ---: | ---: | ---: | ---: |
| Cold | 1,149,386,752 | 2,030,075,218 | 35,430,013 | 161,039,360 |
| Warm | 532,463,616 | 1,224,869,976 | 55,721,426 | 735,999,744 |
| Mixed | 940,539,904 | 2,030,075,198 | 18,473,578 | 117,839,360 |

Observed memory uses the larger independent outer/controller sample. Local domain: B/D full native 1,800,000-pixel requests, nearest5, <=2 tiles, <=320 frames, <=12 union entries, workers1/2, scientific-only, no final hits. Media/crops/direct mode/statistics/logical views/other tiles/hardware and expanded territory inputs are extrapolated or outside this gate. Four-worker performance is unmeasured. The illustrative projection uses 1,234 tiles, 0.73 effective pixels, 72 directions, 24 queries per tile, 0.35 cache fraction and two workers on this hardware; 0.5–2 ranges are engineering allowances, not statistical confidence intervals or measurements of the 3310-file dataset.

Accepted V1 comparisons cover 14.4 million day/night pixels across B/D and both worker counts: shade, quality and transforms exact. Four native horizon comparisons have maximum finite difference **0 degrees**, exact support/blocker distance and finite masks. The independent accepted-reviewer ray operator, using new windows/directions/timestamps and no developer test oracle, checks **567/567 finite targets** with maximum error **3.777704e-6 degrees <=1e-4**. Strict equality policy and equality-neighborhood accounting, nighttime, missing-target/support and known-blocker controls are retained. The unused nighttime sensitivity metadata differs between V1 and V2; solar parameters and scientific arrays agree.

Matched optimization uses three new warm native scientific requests, no final hits and no new direction work: inventory calls **6 → 2**, source bytes hashed **897,018,348 → 299,006,116**, complete planning/execution **2.926341 → 2.705744 s**. Both read-window counts are zero because no direction is computed. The initial e2 timing regression **2.989 → 3.021 s** remains retained despite the same instrumented cost reduction. Final-result reuse is measured separately at 0.426942 s. OS/JIT caches were not flushed and host work was not exclusive, so these times establish the measured local effect without a universal speedup claim.

## Budgets, preservation and limits

Real DSM job wall: e2 **203.554360 s**, f3 **202.290424 s**, Final **0 new real seconds**; cumulative **405.844784 s / 3600 s**. The continuation did not reset the budget. Conservative sampled job-memory upper bound **2,455,699,456 bytes (2.287 GiB) / 12 GiB**. All three owned output/cache namespaces total **487,170,494 bytes (0.454 GiB)** at final audit; the manifest records the subsequent report/manifest inventory, well below **20 GiB**. See Final `ledger.json` and `final_audit.json`.

Monitoring samples known parent/worker/media PIDs every 20 ms. Admission and startup have start/end coverage; sub-sample spikes and short encoder/decoder lifetimes may be missed. The reported bound is a conservative sampled observation, not hard OS enforcement. A zero separate media-RSS field is not proof of zero media allocation.

The original reviewer assertion failures remain visible: requested-window shape, unused nighttime metadata comparison and an optimization evidence-name collision. Corrected assertions/recording retain their original traces and confirm the required properties. The original incomplete-warm trial and every old/new estimator residual remain in the evidence; no slow trial was dropped.

Finite direction discretization, tile-centre solar references, DSM completeness and observational accuracy are inherited scientific limitations. No independent physical observations were registered, so **real-world shade accuracy is NOT VERIFIED**. Territory execution, expanded-input adaptation and V3 remain outside this acceptance. There are **no open engineering blockers on 356f611**.

## Commands and handoff

From the project root, the Final campaign used `PYTHONDONTWRITEBYTECODE=1` and an owned `NUMBA_CACHE_DIR` with:

```text
.venv/bin/python -m pytest -q --disable-warnings -o cache_dir=outputs/v2_independent_acceptance_356f611/pytest_cache --basetemp=outputs/v2_independent_acceptance_356f611/test_tmp
.venv/bin/python outputs/v2_independent_acceptance_356f611/final_checks.py legacy index_corruption
.venv/bin/python outputs/v2_independent_acceptance_356f611/reaccept.py identity contexts
.venv/bin/python outputs/v2_independent_acceptance_356f611/audit.py audit
.venv/bin/python outputs/v2_independent_acceptance_356f611/audit.py manifest
```

f3 coverage used `acceptance.py fixtures`, `reaccept.py identity contexts projection`, `reaccept.py overlap_verify estimator`, and `science.py regression numerical optimization`. Per-case JSON, child logs, pre-run predictions and raw journals retain exact commands/definitions. Reproduction must use fresh owned output/cache namespaces and immutable source snapshots; the archival harness refuses to overwrite existing evidence. Review scripts, caches, isolated source copies and data artifacts stay under the three owned campaign roots. Reports are the only reviewer additions under `docs/v2/`.

Historical reports: [e2 FAIL](</Volumes/My Passport for Mac/Projects/shade_watch_hk/docs/v2/INDEPENDENT_ACCEPTANCE_e2fa0cd.md>) and [f3 FAIL](</Volumes/My Passport for Mac/Projects/shade_watch_hk/docs/v2/INDEPENDENT_ACCEPTANCE_f3dac31.md>). No production/test/golden/model edits, V3 execution, remote action, commit or push were performed by this reviewer.
