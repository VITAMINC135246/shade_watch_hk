# V2 independent acceptance prompt

Independently assess V2 of `shade_watch_hk` against `docs/prompts/v2/ACCEPTANCE_CONTRACT.md` (`SW-V2-AC-1.0`). This is a review, not another development pass. Re-running developer tests is not sufficient.

## Pin the candidate and inherited requirements

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Resolve the supplied V2 `TARGET_COMMIT` to a full immutable SHA. If absent, pin HEAD and first verify that it contains V2 deliverables. Record the accepted V1 SHA/report, actual candidate SHA, both contract identities/hashes, source/input versions and environment. Check that the V2 contract matches its pre-development hash and has not been relaxed.

If V1 acceptance or a V2 candidate is absent, report NOT VERIFIED instead of inventing prerequisites. Ensure evaluated production files match TARGET_COMMIT; isolate a dirty checkout through the available managed-worktree workflow when necessary, without resetting user files. Account for path relocation in comparisons.

Do not edit production code, modify developer tests, update golden data, change estimator coefficients or tune numerical policies. Independent harnesses and reports may be written in isolated review locations. Preserve original DSM, historical caches/results, unrelated presentations and other projects. No push, merge or deployment is requested.

## Budget and independent case selection

Read the complete shared contract and developer report first. Observe <=60 minutes cumulative real-DSM job wall time, <=12 GiB total job memory, <=20 GiB new artifacts and at most four workers if safe. One and two-worker tests are required; four is optional. Use small/synthetic jobs for most fault injection, but include multiple real native tiles, multiple dates and a mixed-cache batch.

Before outcomes are observed, freeze an independent manifest of workload mixes, cache states, timestamps, task orders and failure-injection points not used by the developer for tuning. Record seeds/methods, commands, expected properties and budgets. Use at least three real estimator hold-outs lasting >=10 seconds each, covering cold, warm and mixed directional-cache states. Save estimator predictions before starting each job. None may be a disguised final-result-only cache hit.

## Required independent work

1. Audit B01–B14 against code and evidence. Identify absent coverage, unrealistic claims, mutable dependencies, undefined states and cases where success can be reported before outputs are valid.
2. Run existing tests, then additional public-API/CLI tests. Include a fresh controller process reopening persistent state, not merely a resume method in the original process.
3. Terminate an owned worker during computation, terminate an owned controller after some work has completed, and interrupt publication. Verify restart reuses completed valid entries and safely recomputes incomplete work. Exercise cooperative cancellation separately; it must not affect unrelated users/processes.
4. Submit overlapping requests with different dates and output groupings. Inspect job/call counts, committed artifacts and request metadata. Stress competing writers and stale ownership; verify that shared scientific work does not erase distinct request outputs.
5. Inject corrupt cache, unavailable input, write failure/quota simulation and media failure. Confirm truthful job states, bounded retry policy and failure isolation. Resume a media-only failure and prove no completed horizon jobs rerun.
6. Compare accepted V1 with V2 on independently selected pixels/times, including tile boundaries and odd-offset crops, using one/two workers and changed task order. Enforce B08. Compare scientific-only/media-enabled modes and logical mosaics; inspect quality masks, transforms and labels, not just displayed images.
7. Inspect resource behavior on increasing queue length at fixed concurrency. Separate request metadata growth from retained raster arrays. Test safe rejection/throttling when requested concurrency exceeds a configured budget. Log peak parent/worker/media memory and any monitoring gaps.
8. Evaluate the frozen estimator on all hold-outs. Report each prediction, interval/assumptions, observed duration, residual, memory and disk peak. Apply B10's median <=30% and maximum <=60% absolute percentage error gates within the calibration domain. Do not recalibrate during acceptance or hide outliers. Label full-territory estimates extrapolated.
9. Independently repeat the claimed optimization on matched workloads. Distinguish reduced hash/read/job counts from actual end-to-end speedups, and distinguish cold directional calculation, warm classification and final-result hits. Report regressions and overheads as well as gains.

Retain V1 time-zone, arbitrary-time, missing-buffer and scientific-policy checks where scheduler changes could affect them. No scheduler result can establish real-world shade accuracy; keep numerical consistency, approximation error and observations separate.

## Report and release gate

Produce a concise report with the candidate/predecessor SHAs, contract hashes, input/environment identities, frozen held-out manifest, budget ledger and one PASS/FAIL/NOT VERIFIED row for every B01–B14. Each conclusion needs reproducible evidence paths and commands. Distinguish missing data, environment limitations and budget exhaustion from demonstrated failures.

List defects with severity, expected/actual behavior, minimal reproduction and affected code paths. Do not fix them during review. V2 is ACCEPTED only when all B01–B14 pass and inherited scientific regressions are satisfied; otherwise return FAIL or NOT VERIFIED as appropriate. Lack of observations must remain explicit without being confused with the engineering gate.

Repairs require a new immutable candidate SHA, reruns of affected checks/regressions and preserved original failure evidence. Estimator tuning against failed hold-outs requires new untouched cases. Do not start V3, push, merge or operate a remote machine automatically.
