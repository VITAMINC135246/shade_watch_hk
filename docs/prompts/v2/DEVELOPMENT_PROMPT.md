# V2 development prompt

Implement V2 of `shade_watch_hk`: reliable batch execution, persistent recovery, bounded resource use, cache-aware planning and measured performance/resource estimates. Keep accepted V1 arbitrary-date/time per-pixel science unchanged.

## Preconditions

Work in `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Read applicable repository instructions and inspect HEAD, branch and dirty files. Read the full `docs/prompts/v2/ACCEPTANCE_CONTRACT.md` (`SW-V2-AC-1.0`) and the inherited V1 contract. Locate the full accepted V1 implementation SHA and its independent acceptance report. Record these, the actual starting SHA and both contract hashes before editing.

Do not mistake the historical planning commit `7c56760c854cb1e5138c8381a7b68d543b68cdef` for implemented V1. If no accepted V1 exists, do not implement V2 against missing/unaccepted APIs: report the missing prerequisite and limit work to non-mutating assessment. Do not invent acceptance evidence.

Preserve existing DSM, metadata, prior outputs/caches, unrelated `presentations/` and `heat_index_urop`. Keep `feature` unless instructed otherwise; never reset user changes. Use the current project environment and the existing 19 DSM files. No new data download, GUI, GPU rewrite, public service, cluster deployment or territory-wide computation is requested.

## Implementation sequence

1. **Baseline and traceability.** Map B01–B14 to components/tests. Capture accepted V1 behavior and matched cold/warm/optional-media measurements. Freeze scheduler/state/estimator designs before implementation and predictions before validation runs.
2. **Persistent batch model.** Extend the V1 plan/run interface with stable job IDs, status, cancellation and resume. Persist immutable scientific requests, dependency graphs, attempts, states and output identities. Define recovery from stale owners and a controller crash. Choose a simple local persistence mechanism with tested transaction boundaries; do not assume a local database/lock is safe on arbitrary network storage.
3. **Cache-aware scheduling.** Form the union of needed tile/direction work across dates and requests. Schedule bounded native-tile tasks, reuse completed direction entries, minimize repeated DSM/cache reads, and retain distinct request outputs. Enforce task/cache/output ownership so concurrent requests cannot corrupt results. Never promise exactly-once computation when only atomic committed output can be guaranteed.
4. **Failure and resource controls.** Enforce the configured memory/concurrency budget, bounded in-flight work, clear cancellation semantics and bounded retries. Make progress/state survive process exits. A failed video export must not force horizon recomputation. Handle partial outputs and write failures without publishing false success. Do not remove user caches automatically.
5. **Output separation and composition.** Keep scientific classification, optional statistics, presentation and logical mosaics independent. Combined/cropped views must retain accepted V1 pixel/quality semantics. Avoid compulsory full-region physical mosaics and daily media exports.
6. **Measurement-led optimization.** Remove repeated inventory/hash work, irrelevant source searches, duplicate calculations and unnecessary I/O before touching numerical kernels. Benchmark one and two workers; test four only within budget. Preserve scientific policies and precision. Any scientific change requires explicit scope/version approval rather than being hidden as an optimization.
7. **Estimator and handoff.** Estimate missing directional work, warm queries, output work, peak memory and temporary/retained disk separately. Calibrate on development workloads, freeze the model, then validate on held-out cases under B10. Publish assumptions and prediction errors. Territory-wide numbers must be qualified projections, not a claim of measured performance.

## Testing is mandatory during development

Run meaningful automated tests while implementing and fix discovered defects. In addition to inherited V1 regressions, test legal/illegal state transitions, duplicate submissions, overlapping requests, competing cache writers, worker/controller termination, cancellation, stale ownership, corrupt entries, failed media, write failures and bounded retries. Keep injection restricted to owned test processes and isolated filesystems/fixtures.

Compare numerical outputs against the accepted V1 implementation, not only the new code's own expectations. Vary task order, worker count and output grouping. Validate a logical mosaic by sampling actual scientific pixels and transforms. Prove reuse with instrumentation and task manifests, not just filenames.

Use inexpensive synthetic workloads for large queues and failures; also run a bounded real batch with multiple native tiles, multiple dates and mixed cache availability. All science must still use exact requested instants rather than interpolating daily labels. Observe the shared 120-minute real-job, 12 GiB memory and 20 GiB artifact ceilings. Do not perform full-year/full-territory runs. Record all budget use; missing mandatory evidence is NOT VERIFIED, not PASS.

The estimator must meet the frozen local gates in B10 on untouched hold-outs. Do not tune after inspecting validation outcomes and then claim the same cases remained independent. Do not claim a fixed multi-core speedup or territory-wide accuracy based on a few local timings.

## Deliverables

Deliver code/tests; API/CLI examples for plan, submit/run, status, cancel and resume; persistence/ownership/recovery documentation; cache compatibility notes; output-selection and logical-mosaic examples; the estimator methodology; reproducible cold/warm/mixed benchmark records; a B01–B14 verification matrix; evidence/sample manifests; limitations and the resource ledger.

Commit only necessary V2 code, tests and concise documents locally and report the immutable full SHA. Do not commit DSM, databases, caches, large test artifacts or unrelated work. Do not push or open a PR unless separately authorized. Inspect the staged diff before committing. Report PASS/FAIL/NOT VERIFIED per requirement, distinguish engineering readiness from observational accuracy, and hand off to independent acceptance. Do not declare self-acceptance or begin V3 automatically.
