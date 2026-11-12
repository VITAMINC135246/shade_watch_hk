# V2 frozen design — SW-V2-DESIGN-1.0

Frozen 2026-10-03 before implementation. Starting commit
`f0598140c735786fba7d0b193c57b2aaa8564825`; accepted V1
`796ac8abf05b92f1fbbac23a4aa0f18c9d944101`, report
`docs/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md` (SHA-256
`cc7a9f2fd0d1db5c3ae6339742f703cbf68a3ed2dd3188072110e6d46c005510`).
V1 contract SHA-256: `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31`.
V2 contract SW-V2-AC-1.0 SHA-256:
`236198cdc0cc202d5e4278b6db7baa7c79c3ef710d123faa51b1683e5537b0ac`.
Full initial inputs, environment, dirty/protected files and budgets are frozen
in `outputs/v2_development/evidence/baseline.json`.

## Science and optimization boundary

Keep SW-V1-POLICY-1.0, accepted numerical source files, canonical tile/direction
identities, nearest5 default, exact timestamp solar invocation and quality rules.
V2 uses the accepted horizon, classifier, frame composer and media exporter.
An internal planner catalogue argument avoids repeated inventories within a batch;
execution validates one fresh content catalogue per source directory, then checks
file signatures before each task. No persistent stat-only content trust is used.
Direction unions are scheduled once per native tile/cache identity. One worker
loads its DSM once for that union. Native arrays stay inside bounded workers;
queue entries and IPC contain metadata only. Cache metadata validation may be
memoized inside a worker only while file signatures remain unchanged, with fresh
validation at controller restart and final publication.

## Persistence, graph and ownership

Use local SQLite rollback-journal transactions with synchronous FULL. Reject
network filesystems; require local POSIX advisory locks and atomic rename. This
does not promise safety on arbitrary remote/cloud-synchronized storage or against
hardware power loss. A database stores immutable batch/request plans, graph edges,
task states, attempt history, direction events and artifact hashes. Identical
submissions are idempotent; different named requests retain separate outputs.
One nonblocking controller lock per batch; one lock per output and accepted V1
tile-cache locks prevent conflicting publication even across databases.

Task states: PENDING -> RUNNING -> SUCCEEDED / FAILED / CANCELLED; a failed
transient attempt can return to PENDING within the fixed attempt ceiling. Resume
can requeue interrupted/cancelled/retryable tasks after validation. Corrupt
SUCCEEDED artifacts return to PENDING with a preserved invalidation event.
Permanent input/identity errors stop without automatic retries. Lock contention,
worker loss and transient I/O receive bounded retries; quota/permission failures
and scientific validation failures are permanent until explicit repair/resume.
Batch states: QUEUED, RUNNING, CANCELLING, CANCELLED, FAILED, SUCCEEDED.
Success requires validated scientific, requested media/statistics and index
artifacts. No media error erases completed scientific work.

Worker processes are created with spawn, at most configured concurrency. A
fresh controller reclaims stale RUNNING states while preserving attempts and
terminates only its recorded orphan workers after PID/create-time/ownership
verification. Cooperative cancellation stops admission and signals owned workers;
an in-flight direction can finish atomic publication before cancellation. Locks
are released by the kernel on death. Incomplete publication may recompute; valid
completed directions survive. Exactly-once committed identities are guaranteed,
not exactly-once CPU execution.

## Resources and outputs

Maximum four workers, default one; preflight and sampled enforcement of the
configured total <=12 GiB memory ceiling, available host headroom and <=20 GiB
artifact plan. At most one task per worker is in flight; no nested pools. Reports
separate parent, workers and known media RSS and disclose sampling gaps. Cache,
temporary and retained outputs are estimated separately. Historical caches and
outputs are never pruned or implicitly migrated. New campaigns use isolated
V2 directories. Accepted V1 caches are compatible only by exact scientific key.

Classification frames, media, optional summaries and logical mosaic manifests
are separate graph tasks. Logical views reference lossless source rasters; a
bounded sampling API checks source pixel/georeferencing agreement. Physical
whole-region mosaics and daily videos are optional, never compulsory.

## Estimator and evidence plan

Before calibration: additive phases for source validation, process startup,
missing directional work (native/effective-pixel units), warm classification,
compression/readback, media and final hits. Parallel work uses measured one/two
worker efficiency; estimates outside the calibrated local domain are labeled
extrapolated. Resource estimates are conservative allocation/byte ceilings, not
statistical confidence intervals. Freeze measured coefficients and their hash
before at least three untouched >=10 s real cold/warm/mixed hold-outs; preserve
all predictions/residuals. Gates stay median APE <=30%, maximum <=60%.

Development uses synthetic public-API faults/queues, actual owned process kills,
one/two workers, accepted-V1 pixel comparisons, a multi-tile/multi-date mixed
batch and matched inventory/job-count measurements. Runtime <=7200 s real jobs,
12 GiB memory, 20 GiB new artifacts. Independent acceptance uses new cases in a
separate chat with its own 3600 s budget; no self-acceptance or automatic V3.

## Traceability

| Contract | Planned component/evidence |
| --- | --- |
| B01 | frozen baseline, unchanged-input audit, this design |
| B02 | V1 compatibility; V2 plan/submit/run/status/cancel/resume API and CLI |
| B03 | SQLite graph/attempt transactions, fresh-process recovery tests |
| B04 | native direction union, cache/output locks, overlap/concurrent tests |
| B05 | owned worker/controller kills, cancellation, partial-publication tests |
| B06 | classified bounded retries, corrupt/input/I/O/media faults |
| B07 | admission/RSS monitoring, one/two workers, fixed-concurrency 4x queue |
| B08 | accepted-V1 snapshots, exact arrays/1e-4 horizons, inherited tests |
| B09 | independent output tasks, logical source sampling, media recovery |
| B10 | frozen calibration model, three real hold-outs, phase/resource ledger |
| B11 | explicit projection assumptions, ranges, domain and excluded costs |
| B12 | matched V1/V2 inventory/read/job counters and complete wall time |
| B13 | automated suite, development manifest and independent case provenance |
| B14 | guides, report, raw evidence manifest and immutable local commit |
