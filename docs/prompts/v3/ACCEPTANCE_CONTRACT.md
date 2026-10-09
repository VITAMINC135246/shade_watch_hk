# V3 acceptance contract — territory-wide readiness and staged deployment

Contract ID: `SW-V3-AC-1.0`  
Status: proposed execution contract; freeze and hash before development.  
Predecessor: an independently accepted V2 commit and report, with inherited V1 scientific definitions and acceptance evidence.

This contract is shared by the adjacent development and independent-acceptance prompts. Record the accepted predecessor, actual starting commit and contract hashes. Do not weaken gates after seeing data or performance. V3 extends coverage and deployment; it does not silently change the accepted obstruction model or certify observational accuracy.

## Objective and release levels

Support territory-wide DSM catalogs, actual research boundaries, reproducible execution on a specified research machine and staged production operation. Users must retain arbitrary-date/time per-pixel queries, quality flags, cache reuse and bounded execution. Hong Kong is selected by an explicit boundary/dataset definition, not an invented oversized rectangle around a point.

Distinguish three claims:

1. **ENGINEERING READY:** C01–C12 pass. The software can ingest/plan large catalogs and operate reproducibly; synthetic scale tests and local real data are identified as such.
2. **DEPLOYMENT VALIDATED:** ENGINEERING READY plus C13–C15 pass on the actual territory catalog, specified machine and authorized regional pilots.
3. **PRODUCTION CAMPAIGN COMPLETE:** C16 passes for a specific authorized full-territory campaign. This says exactly what that campaign covered, not that every possible date/time raster has been materialized.

Do not use an unqualified “V3 fully accepted/deployed” when only the first level passes. With only the existing 19 DSM files or no research-machine access, report the later gates NOT VERIFIED. Continue useful engineering work; do not fabricate territory coverage or hardware measurements.

## Data, machine and campaign profiles

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Existing local files remain read-only and provide bounded real regression data. Protect accepted evidence, unrelated presentations and other projects.

Record a data profile: supplied DSM roots, acquisition/version information, file identities, CRS/resolution/vertical units, authoritative boundary source/version, target tiles/pixels, supporting buffer tiles, expected coverage and known gaps. Validate new files against accepted scientific requirements. Do not silently resample incompatible data or mix datums/years as though homogeneous. Duplicates and overlaps need deterministic explicit resolution or rejection. Distinguish source coverage, queryable targets and directional support.

No new data downloads, paid resources, uploads or external transfers are implied by this prompt. Read-only inspection/indexing of user-supplied local datasets is in scope. Use provided boundary files or prepare an input contract when missing; do not invent an authoritative boundary. Authorization already explicitly supplied by the user remains valid and need not be requested again.

Before remote execution, record the user-designated host, allowed access, operating system/runtime, CPU/RAM/storage, destination paths, job allocation and permitted data transfer. Use the accepted environment and reproducible dependency specification. A container is optional, not a prerequisite. An optional cluster adapter may be built only for an actually specified scheduler; do not introduce a distributed system merely because one is possible.

A separate production execution profile must specify the exact boundary/data revision, task scope, direction policy, query dates/times if any, cache-precompute versus on-demand behavior, outputs, concurrency, memory/disk ceilings, time/allocation budget, restart policy and stop conditions. A passed dry run is not authorization for an unbounded run. Obtain only the missing user authorization after presenting the concrete plan; do not ask again for actions already explicitly authorized.

## Scientific and architecture requirements

- Inherit accepted V1/V2 ray, solar, quality, timestamp and approximation rules. Maintain 0.5 m scientific pixels, 1000 m support/search and canonical native-tile addressing.
- Target boundary clipping controls requested outputs, not the availability of obstacles. Read supporting DSM beyond target/administrative boundaries when supplied. Missing water or cross-border data must remain missing/uncertain unless a separately approved scientific treatment exists.
- Index relevant spatial neighbors; avoid per-query full-catalog rehashing, all-pairs seam checks and whole-region array allocation. Preserve reliable detection of changed dependencies through versioned ingestion, rather than assuming files never change.
- Never use a single whole-Hong-Kong elevation extreme to redefine all local quality thresholds or a new union-centre solar reference. Maintain output-extent invariance.
- Keep scientific outputs tiled, with a logical mosaic/spatial-temporal index and bounded previews/exports. An enormous physical raster or full-year movie is not required.
- Validate geographic coverage of the chosen directional approximation over the supported solar trajectories. “Any timestamp accepted” does not mean the chosen angular approximation has zero error. Record out-of-cache/on-demand behavior.
- Provide idempotent catalog ingestion, dependency-aware updates and a rollback/recovery procedure that preserves completed results and version provenance.

## Shared acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| C01 | Accepted baseline and frozen profiles | Accepted V2 SHA/report, V1 policy versions, actual start/candidate commits, contract hashes and supplied data/environment profiles recorded. Missing external inputs are explicitly listed. |
| C02 | Catalog validation | Real local and synthetic fixtures exercise CRS/resolution/datum metadata, corrupt files, duplicates, overlaps, irregular coverage and input updates; incompatible inputs are rejected or explicitly handled, never silently normalized. |
| C03 | Boundary and buffer semantics | Native targets, boundary clipping, islands/holes and external support are handled correctly; use clearly labeled boundary fixtures if actual boundary data are absent. Missing support retains quality uncertainty. Target extent is not mistaken for the DSM-read extent. Actual authoritative territory coverage is assessed separately in C13. |
| C04 | Large-catalog planning | Labeled synthetic catalogs of 1000, 5000 and 10000 tile records are planned/indexed without horizon calls or whole-region arrays. Instrumented neighbor queries and adjacency checks avoid exhaustive pair scans. Report time/memory scaling; do not call metadata-fixture timing real DSM throughput. |
| C05 | Local real regression | On existing 19-file data, inherited V1/V2 numerical, time, extent-invariance, cache, media and recovery checks pass. Same scientific inputs/settings give identical shade/quality and <=1e-4-degree finite horizon differences from accepted V2. |
| C06 | Reproducible deployment package | Environment/runtime specification, install/preflight commands, a small reproducible benchmark bundle and runbook work on an available clean test environment. A mock host is labeled, not substituted for actual-machine validation. |
| C07 | Storage and composition | Tiled outputs, logical combined access, regional/instant export and bounded previews agree with source pixels/quality. Plan reports retained and peak temporary disk use; low-space behavior does not corrupt committed work. |
| C08 | Update and recovery | New/changed/removed catalog sources invalidate only dependent scientific work; interrupted ingestion is recoverable; corrupted/missing outputs are visible; restart/rollback preserves identities and completed unaffected work. |
| C09 | Operational observability | Reports expose task progress, failures, retry/recovery state, actual cache coverage, timing, memory/disk and budget use. Missing data are not counted as successfully modeled sunlight. |
| C10 | Scale projections | Predictions separately cover first directional-model build, warm instant/day query, optional media, sample seasonal queries and an explicitly defined annual request workload. Publish actual versus assumed tile counts, coverage, hardware, measured efficiency, uncertainty and estimator calibration limits. |
| C11 | Tests and bounded engineering evidence | Automated tests, independent-oracle regressions, held-out local scenes/times and failure tests exist with budget/evidence ledgers; observational accuracy remains a separate unverified claim unless measured. |
| C12 | Handoff | Code/tests, machine/data/campaign profile templates, ingestion/query/resume/export commands, deployment/update/recovery runbook, reports and immutable candidate SHA are supplied; large datasets and credentials are excluded from Git. |
| C13 | Actual territory catalog | User-supplied territory data and authoritative boundary are inventoried and validated; actual target/support counts, missing/overlap regions and provenance are reported. A gap-free coverage claim requires supporting evidence; known gaps cannot be hidden in a blanket complete-coverage claim. |
| C14 | Actual research machine | The specified accessible machine passes environment/preflight and matched cold/warm benchmarks; hardware and allocation are recorded; numerical differences versus accepted local results are assessed and satisfy inherited tolerances. Local or simulated measurements cannot pass this gate. |
| C15 | Staged regional deployment | At least two authorized real regional pilot batches with differing available scene characteristics complete on the target machine. Exercise resume and storage/export behavior; compare predictions with observations. Apply inherited V2 estimator gates within its calibrated domain; label extrapolations and recalibrate only using new held-outs. |
| C16 | Authorized territory campaign | A user-authorized full-territory profile runs to its stated completion conditions, with every planned job accounted for, valid published artifacts, coverage/quality maps and resource reconciliation. Unresolved failed/canceled required jobs preclude completion; explicitly planned data gaps remain documented. On-demand catalog readiness alone is not a completed full-territory computation. |

## Budgets and staging

Engineering development default: <=120 minutes cumulative real-DSM job wall time. Independent engineering acceptance: <=90 minutes. Each campaign is limited to 12 GiB total job memory, maximum four workers if safe, and 20 GiB new artifacts; default to one worker. Synthetic catalog tests may exceed 19 records, but must not masquerade as additional real data.

These defaults authorize bounded local engineering checks, not an entire Hong Kong run. External benchmarks, regional pilots and production campaigns require the supplied machine/campaign budgets; no external runtime is authorized by a missing profile. Planning and a concrete deployment proposal can proceed while these inputs are absent. Reuse prior accepted evidence where unaffected rather than unnecessarily rerunning expensive jobs.

Use isolated outputs/cache namespaces, preflight disk, track actual resource use and stop only owned jobs at budget limits. Missing inputs/access or exhausted budget is NOT VERIFIED, not an instruction to pretend completion or continue unbounded execution.

## Evidence and gate decisions

Every C01–C16 receives PASS, FAIL or NOT VERIFIED and evidence. Distinguish untested/missing-resource cases from demonstrated violations. Report all three release levels separately. Production completion certifies the specified campaign, not perfect per-pixel real-world accuracy or precomputation of every day of a year.

Independent acceptance pins an immutable candidate, uses extra scenes/timestamps/failures and does not patch production code. Repairs require a new SHA and affected rechecks. No automatic push, merge, public publication, unrelated-host operation or expansion of approved run scope follows from passing a gate.
