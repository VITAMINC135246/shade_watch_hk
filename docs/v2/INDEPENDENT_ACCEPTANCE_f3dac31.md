# Independent V2 reacceptance — f3dac31

**Gate: FAIL — B04 and B14 fail on cross-version output preservation.** The two P1 defects from e2fa0cd are repaired; a further compatibility defect was independently reproduced. Real-world observational accuracy remains **NOT VERIFIED**. Completed 2026-10-09, Asia/Hong_Kong.

Candidate: `f3dac3175706988591387b22a56ee9857afad276`. Failed predecessor: `e2fa0cde8e104439eb0c05e9bf9f549edffd6797`. V2 starting commit: `f0598140c735786fba7d0b193c57b2aaa8564825`. Accepted V1: `796ac8abf05b92f1fbbac23a4aa0f18c9d944101`.

- V1 contract `SW-V1-AC-1.0`: `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
- V2 contract `SW-V2-AC-1.0`: `236198cdc0cc202d5e4278b6db7baa7c79c3ef710d123faa51b1683e5537b0ac`.
- Accepted V1 report: `cc7a9f2fd0d1db5c3ae6339742f703cbf68a3ed2dd3188072110e6d46c005510`.
- Frozen estimator: `ad6939e4455d9e80495d27e382438d635f5cb9f0920601959e09bbbe2e721469`.


Evidence root: `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_f3dac31`. Independent manifest SHA-256: `cacf2533db2639f236a0d9a23ec23aa5fb0346c8b6608cf85da1c0ad703e3097`. Initial tracked files matched the candidate. Every measured batch persists the four engine hashes used during execution; source changes for the next repair occurred only after these measurements. Main-task README/example/V3 preparation is a separate documentation overlay.

## Input and provenance

Original 19 DSM TIFFs now reside in `data/raw/dsm/2020_HKUST_Around/D12.DSM.TIFF`. All 19 content hashes match the first campaign; all 120 original scientific/alternate-format/metadata files match after correctly mapping the entire old folder. Two Finder files and the input README changed between campaigns. Buffered spatial identities for B/D remain identical. All requests use explicit `dsm_dir`; new 3310-file territory data were excluded. Evidence: `initial_provenance.json`, `input_relocation_resolved.json`, `spatial_identity_relocation.json`.

## Full matrix

| ID | Result | Independent evidence / command stage |
| --- | --- | --- |
| B01 | PASS | Candidate/contracts/model/input checks; original review evidence kept read-only. |
| B02 | PASS | `planning.json`, `cli.json`, `reaccept_identity.json`: plan/run/status/cancel/resume; runner/state changes yield new IDs and runnable new definitions. |
| B03 | PASS | `controller_loss.json`, `worker_loss.json`, `corruption.json`, `reaccept_contexts.json`: fresh-process durable recovery and receipt-integrity validation. |
| B04 | FAIL | Same-version concurrency passes with different request/batch/cache/state contexts, but a compatible older output's index is overwritten. See cross-version defect below. |
| B05 | PASS | Owned SIGKILL during kernels, completed direction hash preserved, partial publication, cooperative cancellation, stale owner and unrelated sentinel survival; `acceptance.py fixtures`. |
| B06 | PASS | Permanent unavailable/write/quota errors, corrupt cache/frame, bounded two-attempt worker loss and media-only zero-horizon retry; respective case JSON/journals. |
| B07 | PASS | `queue.json`: 10/40 requests, one in-flight task, parent growth 3,047,424 bytes; admission rejects over-budget settings. Real one/two-worker runs and independent RSS crosscheck. |
| B08 | PASS | `scientific_regression.json`, `numerical_regression.json`; accepted V1 comparison, separate cold caches, odd/boundary/custom crops, exact shade/quality/support and solar-time provenance. |
| B09 | PASS | Media/scientific/logical/statistics and resumed-media consistency; `reaccept_overlap_verify.json` resolves the retained reviewer window-shape assertion. |
| B10 | PASS | Three fresh >=10 s cold/fully-warm/mixed native configurations; saved predictions, zero final hits, all resource ceilings cover observations. `estimator_all_residuals.json`. |
| B11 | PASS | `reaccept_projection.json`: explicit illustrative tile/pixel/cache/direction/query/hardware assumptions and ranges; outside-domain planning explicitly extrapolated. |
| B12 | PASS | `optimization.json`: matched catalogue calls 6 → 2 and source hashing reduced by 598,012,232 bytes; complete matched time 2.926 → 2.706 s. |
| B13 | PASS | 71 existing tests, frozen independent manifest, actual faults/queues and bounded real batches; original/retest provenance kept distinct. |
| B14 | FAIL | Code/commands/state documents exist, but new schema rewrites compatible old results without explicit migration, invalidating their stores. |

## Estimator and scientific checks

| Case | Prediction s | Observation s | APE |
| --- | ---: | ---: | ---: |
| new_cold | 23.568 | 20.382 | 15.63% |
| new_warm | 53.726 | 51.845 | 3.63% |
| new_mixed | 23.568 | 19.743 | 19.38% |

Median APE **15.63%**, maximum **19.38%**; limits 30%/60%. The complete warm trial implements the previously frozen warm supplement: 192 native frames, four already populated directions, zero new horizon calls, zero final hits. The original e2fa0cd warm-labeled result is correctly relabeled mixed; all six old/new residuals are retained. Model hash and coefficients are unchanged. Domain is B/D native, nearest5, <=2 tiles, <=320 frames, <=12 union entries, workers1/2, scientific-only, no final hits.

Native comparisons cover two 1,800,000-pixel tiles at day/night with workers1/2: all shade/quality arrays and transforms agree, finite horizon maximum difference **0 degrees**, support/blocker-distance arrays exact. New independent ray/oracle checks cover 567/567 finite targets at three windows/directions; maximum error **3.777704e-6 degrees**, support and finite masks exact. Equality-neighborhood counts and nighttime/missing/known-blocker controls are retained. Nighttime V2 records unused sensitivity threshold 0; V1 records the preceding directional threshold; solar parameters and scientific values agree. These checks do not validate physical shade accuracy or remove inherited finite-direction/tile-centre approximations.

## Remaining P1 defect: implicit legacy index migration

Expected: preserve compatible prior committed output or reject it before mutation pending explicit migration. Actual: genuine e2fa0cd output has the same V1 plan key, yet the new batch succeeds and changes `shade-watch-v2-result-1.0` to `1.1`; the original store becomes **INCOMPLETE** from index checksum mismatch. No historical production file was touched: exact old/new code ran in the owned `upgrade_copy/`.

Evidence: [minimal reproduction](/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_f3dac31/evidence/cross_version_output.json), `upgrade_manifest.json`, `upgrade_copy/old.json`, `new.json`, and both saved index versions. Reproduce the recorded two commands after generating the same owned fixture and replacing only the isolated src snapshot with f3dac31. Affected code: `src/v2_worker.py::_prepare` and unconditional index publication, lines 172–187; compatibility guide did not specify legacy output rejection.

The original engine-ID and same-version context defects are **closed on this SHA** (`reaccept_identity.json`, `reaccept_contexts.json`); their original failure evidence remains untouched. The remaining defect requires a new immutable candidate and targeted reacceptance. No model recalibration or repeat of unaffected real hold-outs is needed.

Real-job wall on this candidate: **202.290424 s**; original+reacceptance total **405.844784 s / 3600 s**. Conservative sampled job-memory upper bound **2.287 GiB / 12 GiB**. Temporary/retained disk and outer/controller RSS are crosschecked in `independent_resource_crosscheck.json`; combined artifacts remain below 20 GiB. Sampling is 20 ms for known PIDs; input admission/startup, short media lifetime and sub-sample spikes are disclosed gaps, not hard OS enforcement.

Commands: `acceptance.py fixtures`; `reaccept.py identity contexts projection`; `reaccept.py overlap_verify estimator`; `science.py regression numerical optimization`, all with isolated cache/output locations, `PYTHONDONTWRITEBYTECODE=1` and owned `NUMBA_CACHE_DIR`. Logs and per-batch predictions/journals persist exact definitions and commands. All e2fa0cd measurements and failures remain preserved. No production edits, estimator tuning, data download, territory run, V3 execution, commit or push by this reviewer.
