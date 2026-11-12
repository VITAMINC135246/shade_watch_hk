# Independent V2 acceptance — e2fa0cd

**Gate: FAIL. This candidate was never independently accepted.** Review began 2026-10-03; this retrospective closeout was written 2026-10-09 after the interrupted review resumed. Real-world observational accuracy remains **NOT VERIFIED**.

Candidate: `e2fa0cde8e104439eb0c05e9bf9f549edffd6797`. V2 starting commit: `f0598140c735786fba7d0b193c57b2aaa8564825`. Accepted V1: `796ac8abf05b92f1fbbac23a4aa0f18c9d944101`, report `docs/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md`.

- V1 contract `SW-V1-AC-1.0`: `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
- V2 contract `SW-V2-AC-1.0`: `236198cdc0cc202d5e4278b6db7baa7c79c3ef710d123faa51b1683e5537b0ac`.
- Accepted V1 report: `cc7a9f2fd0d1db5c3ae6339742f703cbf68a3ed2dd3188072110e6d46c005510`.
- Frozen estimator: `ad6939e4455d9e80495d27e382438d635f5cb9f0920601959e09bbbe2e721469`.


Independent evidence: `/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_e2fa0cd`. Cache: `data/processed/shade_v1/v2_independent_e2fa0cd/`. The initial audit verified all 66 tracked files against this commit and hashed 123 raw files; 10,337 protected signatures were recorded. The original raw inputs were the local 19-file DSM set. Input relocation and a later full-territory download occurred between campaigns, outside this review.

## Original decisions

| ID | Result | Evidence / reason |
| --- | --- | --- |
| B01 | PASS | `initial_provenance.json`, environment and input inventory; exact candidate/contracts and isolated namespaces. |
| B02 | FAIL | Planning/API/actual CLI cases work, but runner/state-only code changes produce the same batch ID. Replanning returns an old incompatible definition. |
| B03 | FAIL | Ordinary durable restart passes; omitted engine identity and conflicting committed index ownership violate valid reusable state. Original journals retained. |
| B04 | FAIL | Two concurrent state stores commit different checksums for the same result index. One batch becomes FAILED with no FAILED tasks and its SUCCEEDED index artifact is invalid. |
| B05 | PASS | Actual computing-worker/controller termination, completed checkpoint reuse, separate cooperative cancellation, partial publisher death, stale ownership and sentinel survival. |
| B06 | PASS | Unavailable input, ENOSPC/EACCES, corruption, bounded loss retries, media-only recovery with zero horizon calls. |
| B07 | PASS | One/two workers; 10/40 fixed-concurrency queue and admission rejections. Monitoring gaps recorded. |
| B08 | PASS | `scientific_regression.json`, `numerical_regression.json`; separate accepted-V1/candidate caches, new leap/UTC/night instants, crops and reference windows. |
| B09 | PASS | Scientific/media/custom/boundary/logical comparisons exact; initial 14-versus-28-row reviewer assertion corrected in `overlap_corrected_expectation.json`. |
| B10 | NOT VERIFIED | Cold and mixed timings satisfy numerical/resource gates. Declared warm setup missed a bin crossing; actual workload was mixed. Complete-warm supplement was frozen but not run before interruption. Original residuals are retained, not counted as true warm evidence. |
| B11 | PASS | Explicit extrapolation formula/profile code audit; later executed unchanged API is mapped in the reacceptance report. No territory run. |
| B12 | PASS | Matched warm inventory calls 6 → 2, hashed bytes 897,018,348 → 299,006,116. End-to-end 2.989 → 3.021 s, a small regression; instrumented redundant work reduction is the supported improvement. |
| B13 | PASS | 68 existing tests and independent cases; original seeds/manifests, raw failure histories and all residuals retained. |
| B14 | FAIL | Frozen handoff exists, but documented replan/ownership behavior is contradicted by the two defects. |

## Blocking defects

1. **P1: incomplete engine identity.** Expected: new runner/state bytes produce an executable fresh batch. Actual: both versions keep the same ID; submit returns the old definition and run rejects changed code. Reproduced separately with behavioral-neutral comments in isolated copies. Evidence: [evidence engine defect](/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_e2fa0cd/evidence/identity_change_defect.json). Affected code: `src/v2.py` identity and existing-ID return, `src/v2_runner.py::_current_inputs`.
2. **P1: conflicting shared index provenance.** Expected: compatible concurrent publishers preserve committed index bytes. Actual: state-directory/batch/request fields in the index differ across scheduling contexts and invalidate a prior store's artifact hash. Evidence: [concurrent writer defect](/Volumes/My Passport for Mac/Projects/shade_watch_hk/outputs/v2_independent_acceptance_e2fa0cd/evidence/competing_writer_defect.json), original child results/journals. Affected code: `src/v2_worker.py::_prepare` and index publication.

Original real-job wall ledger: **203.554360 s / 3600 s**. Sampled conservative campaign peak approximately **2.27 GiB / 12 GiB**, original generated artifacts about **224.4 MiB / 20 GiB**. OS/JIT caches were not flushed. No coefficients, production files, tests or goldens were changed by the reviewer; no commit/push/deployment or V3 execution.

Original exact commands and frozen selection are in `evidence/case_manifest.json`; harnesses are `acceptance.py`, `science.py`, `supplement.py`. Namespace-specific outputs refuse overwriting measured records. A fresh reproduction must use a new owned namespace. Original logs retain reviewer assertion corrections, the unused nighttime threshold metadata comparison, and an evidence-name collision after a completed optimization measurement. None is a production defect or a dropped scientific result.

Repairs were evaluated on new immutable SHAs; this FAIL gate remains unchanged. See `INDEPENDENT_ACCEPTANCE_f3dac31.md` and the final candidate report.
