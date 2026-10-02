# V2 acceptance contract — reliable batch execution and measured scaling

Contract ID: `SW-V2-AC-1.0`  
Status: proposed execution contract; freeze and hash before development.  
Predecessor: an independently accepted V1 implementation, identified by full commit SHA and acceptance-report identity. The historical planning baseline `7c56760c854cb1e5138c8381a7b68d543b68cdef` is not a V1 implementation.

This contract is shared by the adjacent development and independent-acceptance prompts. Do not start V2 implementation without verifying the accepted V1 baseline. Read the V1 contract and freeze the inherited scientific policy, cache schema, API behavior and approximation limitations. Do not retroactively weaken criteria after seeing results. User-approved scope changes require a new contract version and an explanation of affected evidence.

## Objective and scope

Turn the V1 arbitrary-date/time query engine into a reliable local batch system with persistent job state, bounded concurrency, cache-aware scheduling, recoverable outputs, measured optimizations and useful resource estimates. A batch may contain many tiles, dates and timestamps, but the science remains the accepted V1 science. Native tiles remain spatial work units; direction entries remain cache/checkpoint units. Never infer arbitrary instants by interpolating binary daily maps.

V2 does not require a GUI, public API service, GPU backend, cluster deployment, new DSM downloads or actual whole-Hong-Kong execution. Territory-wide numbers are projections unless measured on territory-wide data. Use the existing 19 DSM files, available V1 fixtures and outputs, plus explicitly labeled synthetic scheduling workloads.

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Protect original DSM and metadata, all historical results/caches, unrelated `presentations/`, and `heat_index_urop`. New outputs belong in an isolated V2 directory; do not overwrite accepted V1 evidence. Use existing dependencies where practical.

## Required design

- Keep the V1 request/plan/run interface and add stable batch IDs, inspection, status, cancellation and resume operations. Planning is non-computational: no horizon calculation, classification or media rendering.
- Persist request parameters, scientific identities, dependencies, task transitions, attempts, failures and artifact states across process exits. Define legal transitions and stale-worker recovery. Preserve failed-attempt evidence.
- Plan the union of required tile/direction work across requests. Scientific work may be shared, while separate user requests retain their own timestamps, outputs and provenance. Do not confuse deduplication of scientific work with deletion of distinct user requests.
- Enforce bounded memory, concurrency and in-flight work. Do not retain all tiles or timestamps in memory. Do not start nested worker pools that exceed the declared budget.
- Provide safe ownership of cache/output publication. Exactly-once committed artifacts are required; exactly-once CPU execution after a crash is not promised. Interrupted unfinished work may repeat; verified completed scientific work must not repeat unnecessarily.
- Separate scientific classification, optional statistics, visualization and logical mosaics. Turning media off must not change shade/quality values. Avoid a compulsory physical whole-region mosaic or compulsory daily videos.
- Preserve read-only or isolated legacy/V1 result access. Cache migration must be explicit, identity-checked and nondestructive. No automatic pruning of user data or historical caches.
- The estimator separates initial DSM/catalog validation, missing directional work, warm classification/query work, output/compression/media work and available final-result hits. Record hardware, concurrency, uncertainty, calibration domain and storage assumptions. Estimate peak temporary as well as retained disk use.
- Optimize in order: repeated inventory/hash work; irrelevant source searches; duplicate directional work; repeated cache I/O; optional output overhead; concurrency/storage settings. Only then consider numerical-kernel changes. Changes to direction spacing, precision or scientific rules are not performance-only changes and are outside this version unless separately approved and versioned.

## Shared acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| B01 | Accepted predecessor and traceability | Exact accepted V1 SHA/report, actual V2 starting SHA, both contract hashes, environment and input identities recorded; unrelated and historical work preserved. |
| B02 | Stable API and planning | Single-request compatibility plus batch plan/run/status/cancel/resume examples work. Planning reports dependencies, counts, cache states and estimates without starting scientific/media computation. |
| B03 | Durable state | A controller exit and fresh-process restart preserve requests, completed work, failures and pending dependencies. Terminal success is impossible while required artifacts are incomplete. |
| B04 | Deduplication and ownership | Overlapping requests share tile/direction computations; date/range changes reuse compatible cache entries. Concurrent writers cannot publish conflicting artifacts. Independent requests keep correct metadata and outputs. |
| B05 | Crash and cancellation recovery | Controller/worker termination, cooperative cancellation and partial publication are exercised. Restart skips verified completed scientific entries; incomplete/corrupt entries recover; stale ownership cannot cause indefinite blocking. Unrelated processes are untouched. |
| B06 | Failure isolation and retries | Controlled unreadable input, write failure/disk-quota simulation, corrupt cache and failed media task yield truthful states. Retries are bounded and classified; unrecoverable errors are not retried forever. A media-only retry does not recompute completed horizons. |
| B07 | Resource bounds | Enforce configured worker/memory limits with preflight and monitored behavior. Test one and two workers; four is optional if safe. A 4x increase in queued fixture tasks at fixed concurrency does not introduce retained scientific arrays per task. A long queue completes without deadlock or unbounded retained memory. |
| B08 | Scientific regression | Against accepted V1, shade/quality arrays are identical on unchanged inputs/settings; horizon differences <=1e-4 degrees and support flags identical. Retain V1 equality-neighborhood reporting for direct numerical reference comparisons. Test different task order, worker count, crops and output combinations. |
| B09 | Separated outputs | Scientific-only, media-enabled and resumed-media modes yield the same scientific arrays. A logical combined view agrees with source tile pixels and georeferencing without forcing a full-region copy. Optional derived statistics do not replace pixel-level outputs. |
| B10 | Calibrated estimator | Freeze coefficients before at least three held-out real workload configurations with measured duration >=10 seconds each, covering cold, warm and mixed cache states. Median absolute percentage error for total wall time <=30%, maximum <=60%; provisional resource-plan ceilings cover observed peak job memory and peak generated disk. Record predictions before execution and publish all residuals. |
| B11 | Honest extrapolation | Full-territory projections use explicit tile/effective-pixel assumptions, direction-union size, query counts, cache state, output selection, hardware and measured concurrency efficiency. Include ranges and excluded costs. Do not claim local estimator thresholds validate full-territory accuracy. |
| B12 | Demonstrated optimization | At least one targeted optimization reduces its claimed measured cost or instrumented redundant work versus accepted V1 on matched requests. Report end-to-end effects and regressions, not only the fastest kernel. No mandatory arbitrary speedup factor; no improvement demonstrated means this criterion is not passed. |
| B13 | Tests and independent samples | Automated scheduler/failure tests, V1 regressions and bounded real batches exist; sample provenance distinguishes development tuning from independent acceptance. Scientific approximation and observational accuracy remain separate. |
| B14 | Handoff | Working code, tests, commands, state/recovery documentation, benchmark/estimate report, evidence manifest and immutable implementation SHA are delivered; large data remain untracked. |

For B10, the numerical targets are proposed engineering gates for the calibrated local workload domain. Freeze them before implementation. Estimates outside that domain must be labeled extrapolated or unavailable. Do not satisfy the gate by dropping slow trials, padding intervals without explanation, or treating a final-result hit as a warm directional query. If the user changes the targets before development, version this contract first. Retesting after estimator tuning requires a fresh held-out set.

## Test budgets

Default ceilings for each campaign: one worker by default, maximum four if preflight permits; 12 GiB total job-memory budget; 20 GiB new artifacts. The one/two-worker tests are required; do not launch four if unsafe. Preserve headroom for the host and preflight available disk.

- Development: <=120 minutes cumulative real-DSM job wall time.
- Independent acceptance: <=60 minutes cumulative real-DSM job wall time.
- Failure-injection and large-queue tests should primarily use inexpensive synthetic fixtures. Real tests must include multiple native tiles, multiple dates and one mixed-cache batch; a few selected timestamps suffice, rather than repeated full-day media runs.
- Do not generate a full year or run all Hong Kong. Maintain a runtime/memory/disk ledger. Budget exhaustion makes affected criteria NOT VERIFIED; it does not authorize silently expanding the run.

## Decisions and evidence

Use PASS, FAIL or NOT VERIFIED for every B01–B14 criterion, with exact evidence and reason. A demonstrated violation is FAIL; missing data, unavailable environment or insufficient budget is NOT VERIFIED. V2 is accepted only when all B01–B14 pass and inherited V1 scientific regressions are satisfied. Real-world accuracy remains NOT VERIFIED without independent observations; this is separate from the engineering gate.

Acceptance checks the exact candidate commit, adds independent workload/failure cases and does not fix production code. Fixes require a new candidate SHA and targeted reacceptance. No V3 execution, download, remote deployment, push or merge is authorized merely by V2 acceptance.
