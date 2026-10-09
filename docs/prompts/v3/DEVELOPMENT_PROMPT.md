# V3 development prompt

Implement V3 of `shade_watch_hk`: territory-wide catalog/readiness, reproducible research-machine deployment and staged operation, preserving accepted V1/V2 arbitrary-date/time per-pixel shadow behavior.

## Establish the actual prerequisites

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Inspect repository instructions, HEAD/branch and local changes. Read the full `docs/prompts/v3/ACCEPTANCE_CONTRACT.md` (`SW-V3-AC-1.0`) and inherited V1/V2 contracts. Record contract hashes before editing, the independently accepted V2 SHA/report, inherited scientific policy versions and actual starting SHA. Do not implement against an unaccepted/missing V2; report missing prerequisite evidence rather than inventing it.

Preserve user work, the existing 19 DSM files/metadata, historical outputs/caches, unrelated `presentations/` and `heat_index_urop`. Keep `feature` unless instructed otherwise. New outputs and migration trials must be isolated. The historical planning commit `7c56760c854cb1e5138c8381a7b68d543b68cdef` identifies the early project, not completed V1/V2.

Inventory which additional territory DSM, authoritative boundary and research-machine access the user has actually supplied. Do not download, pay for, upload or transfer data merely because V3 needs more coverage. Existing explicit authorizations remain valid. Continue engineering work using local data and clearly labeled fixtures when external prerequisites are absent.

## Objective and release distinction

Build the ability to ingest, plan and query territory data without loading all of Hong Kong into memory or changing local science according to the requested region. Preserve native-tile work units and tiled scientific outputs. Queries remain date/time driven using the directional obstruction model; 24 solar terms are optional evaluation dates, not binary-map interpolation anchors.

Report three separate milestones from the shared contract: ENGINEERING READY (C01–C12), DEPLOYMENT VALIDATED (also C13–C15), and PRODUCTION CAMPAIGN COMPLETE (C16). Do not claim a full Hong Kong rollout based on 19 local files or metadata simulations. Missing data/host access does not prevent useful readiness work, but affected deployment gates remain NOT VERIFIED.

## Implementation sequence

1. **Freeze profiles and traceability.** Map C01–C16 to modules/tests/evidence. Define data, machine and production-profile schemas. Record actual supplied roots, dataset years/versions, units/datums, boundary provenance, expected targets/support and known gaps. Produce a missing-input list without assuming absent values.
2. **Build robust ingestion and indexing.** Support validated, idempotent catalog ingestion and updates. Detect incompatible grids, corrupt files, overlaps and duplicates. Use spatial indexes for local dependency discovery and adjacency QA. Avoid per-request full-catalog rehashing and all-pairs seam scans while retaining trustworthy version/change detection.
3. **Handle real territory geometry.** Resolve targets from supplied boundaries including islands and holes, with support DSM outside targets/administrative borders when available. Preserve quality uncertainty where support is absent. Do not fill unknown water or cross-border areas with invented elevations. Keep canonical solar/quality policies independent of output size.
4. **Provide bounded access and storage.** Expose tiled results through a logical spatial/temporal index, regional exports and bounded previews. Keep science and media separable. Include temporary disk peaks and cache growth in plans; do not force one gigantic physical mosaic or materialize a year of frames.
5. **Package reproducible execution.** Supply environment specifications, preflight, a small benchmark bundle and install/query/resume/export instructions. Test an available clean environment. Support the actual user-designated research machine; build a scheduler adapter only if an actual scheduler is specified. Never treat remote credentials as repository content.
6. **Measure and stage deployment.** Validate local regressions first; then ingest supplied real territory data, run explicitly authorized target-machine benchmarks and regional pilots, and compare predicted versus actual resource use. Use matched workloads so hardware comparisons do not confuse changed settings with acceleration.
7. **Prepare the production campaign.** Produce a concrete profile with exact scope, source versions, direction policy, cache/on-demand strategy, outputs, budgets and completion/stop conditions. Execute only the scope explicitly authorized by the user. Ask only for genuinely missing authorization/resources after the plan is reviewable. Do not silently start a territory-wide or full-year workload.

## Development tests and budgets

Testing is part of implementation. Use inherited numerical/regression tests plus ingestion, boundary, neighbor-index, disk-failure, update/rollback and restart tests. Add labeled synthetic metadata catalogs of 1000/5000/10000 tiles for indexing/scheduler-scale checks. These test metadata behavior, not real DSM throughput or actual geographic coverage.

Use existing real data for actual raster checks, held-out dates/times and boundary cases. Verify identical shade/quality under unchanged science, <=1e-4-degree finite horizon differences, and no output-extent dependence. Inspect visual exports as well as array/metadata integrity. Preserve missing-data distinctions.

Observe the shared local engineering budget: <=120 minutes cumulative real-DSM jobs, <=12 GiB job memory, at most four safe workers and <=20 GiB new artifacts. Target-machine pilots and production need their own supplied budgets and permissions; absent profiles authorize no external run. Keep a resource ledger and do not use synthetic data to claim a real-data criterion passed.

## Deliverables and completion

Deliver catalog/ingestion/query/deployment code and tests; reproducible environment/preflight and benchmark bundle; data/machine/campaign profile templates; commands and operational runbooks for updates, failures, resume and export; coverage/quality reports for data actually inspected; calibrated performance reports and qualified projections; and a C01–C16 evidence matrix with separate gate decisions.

Commit necessary code/tests/concise documentation locally and report an immutable implementation SHA. Exclude DSM, caches, runtime state, large media and secrets. Preserve unrelated changes. Do not push, publish, merge or create a PR unless separately authorized.

If territory data, boundary, target host or production authorization are missing, finish the unaffected readiness work and identify exactly which gates remain NOT VERIFIED and what would resolve them. Do not label partial deployment complete, invent measurements or weaken the contract. Hand off to independent acceptance rather than self-certifying V3.
