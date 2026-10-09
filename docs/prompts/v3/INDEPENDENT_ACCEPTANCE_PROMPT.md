# V3 independent acceptance prompt

Independently review V3 of `shade_watch_hk` against `docs/prompts/v3/ACCEPTANCE_CONTRACT.md` (`SW-V3-AC-1.0`). Assess software readiness, actual deployment validation and production completion separately. A claim that the entire territory is operational needs actual territory/machine/campaign evidence.

## Pin the candidate and review scope

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`. Resolve supplied `TARGET_COMMIT` to a full immutable SHA; if absent, pin HEAD and verify V3 deliverables exist. Record the accepted V2 SHA/report, inherited V1 scientific definitions, all relevant contract hashes, actual dataset profiles and available host/campaign authorizations. Confirm the shared contract matches the pre-implementation hash.

If prerequisite acceptance or the candidate is absent, report NOT VERIFIED. Ensure tested production code matches TARGET_COMMIT, using the available managed-worktree workflow for isolation if needed; never reset/discard user changes. Do not patch code, change policies, refresh golden data, retune an estimator or modify the contract to pass review. Independent harnesses and evidence may be created in isolated locations.

Protect original data, prior caches/results and unrelated work. No data downloads, external transfers, remote execution, publication, push or merge are implied by this review. Reuse explicit user authorization when present; obtain only genuinely missing authorization after showing a concrete plan for that action.

## Independent samples and budget

Read developer evidence, then freeze additional cases before observing their results. Use new seasonal timestamps, off-grid times, odd-offset crops and real available scene windows not used for tuning. Choose independent corrupt/overlapping/missing-input fixtures and catalog update/failure points. Record sample/seed/provenance, expected properties and budgets.

Local engineering acceptance is limited to 90 minutes cumulative real-DSM jobs, 12 GiB job memory, at most four safe workers and 20 GiB new artifacts. Default to one worker; use metadata fixtures for large-catalog stress. Regional/remote/full-territory jobs may run only under the existing supplied profiles and budgets. Existing logs/manifests may support audit of an authorized completed campaign; do not rerun the entire campaign merely to review it. No access or insufficient evidence means NOT VERIFIED for that gate.

## Required independent checks

1. **Requirements and provenance:** audit C01–C16, accepted predecessor evidence, scientific policy versions, input identities and profile completeness. Check that improvements did not silently change ray distance, resolution, solar references, quality handling or approximation settings.
2. **Ingestion:** exercise valid data, wrong CRS/resolution, incomplete datum information, corrupt files, duplicate/overlapping tiles, additions/removals and interrupted ingestion. Verify explicit errors/policies and dependency-aware invalidation using isolated copies/fixtures.
3. **Boundaries and support:** inspect actual supplied research-boundary provenance. Test islands, holes, clipped tiles and external support. Distinguish missing target DSM from missing sunward support; do not accept unknown water as zero elevation. No authoritative boundary means actual territory coverage is unverified.
4. **Catalog scale:** independently generate 1000/5000/10000-record metadata fixtures. Measure index/query time and memory and instrument neighbor/pair checks. Verify no horizon calls during planning and no compulsory full-region arrays. Do not convert these numbers into measured territory raster throughput.
5. **Scientific regressions:** compare accepted V2 and the candidate on held-out local pixels/times and processing arrangements. Apply inherited label/quality and 1e-4-degree horizon gates. Check time zones/seconds, reference boundaries, crops, combined views, missing data and cache behavior. Review any unchanged numerical/observational limitations explicitly.
6. **Outputs and resource behavior:** validate tiled/combined access, georeferencing, quality flags, regional exports and bounded previews. Exercise insufficient-space and interruption scenarios on owned fixtures. Inspect peak temporary disk use, memory/concurrency enforcement, state truthfulness and restart/rollback behavior.
7. **Deployment reproducibility:** test the provided environment/preflight/benchmark procedure in an available clean environment. Separately inspect/run the authorized actual research-machine benchmark. A container on the local laptop is not evidence that a different machine was validated. Check software/hardware and input hashes and numerical equivalence.
8. **Actual catalog and pilots:** if territory data/access are supplied, verify actual target/support counts, data gaps and boundary coverage; use new regional/temporal checks beyond the developer samples. Confirm at least two differing real regional pilot batches and a recovery exercise on the target machine. Verify predictions were recorded before runs and report observed residuals/calibration limits.
9. **Production audit:** if a full campaign was authorized, reconcile its frozen profile with every planned task and artifact. Distinguish completed, intentionally excluded, failed and canceled work. Sample result hashes/metadata/arrays independently. A success banner, pilot completion or a queryable catalog cannot substitute for the campaign's required completed outputs.
10. **Claim audit:** check that all-Hong-Kong/day/year estimates specify the actual workload, direction union, output choices, cache state, hardware and uncertainty. “Any timestamp can be queried” is not proof every annual frame has been calculated or that angular approximation is exact. Do not invent real-world validation from numerical agreement.

## Report and gate decisions

Publish a compact report with full candidate/predecessor SHAs, contract hashes, profiles, dataset/environment identities, frozen independent samples, commands/evidence and resource ledger. Give PASS/FAIL/NOT VERIFIED for every C01–C16, including reasons for missing data/access/budget.

Report separately:

- **ENGINEERING READY:** requires all C01–C12 PASS.
- **DEPLOYMENT VALIDATED:** also requires C13–C15 PASS on actual territory data and the specified machine.
- **PRODUCTION CAMPAIGN COMPLETE:** requires C16 PASS for its named authorized scope.

Use NOT VERIFIED rather than FAIL when the only issue is unavailable territory data, host access, authorization or evidence; use FAIL for demonstrated defects. Preserve an explicit real-world validation status, normally NOT VERIFIED without observations. Never compress these distinctions into an unqualified full V3 acceptance.

Provide prioritized defects with minimal reproductions, expected/actual behavior and evidence. Do not repair production code during review. Fixes require a new immutable SHA and affected rechecks; preserve the original failures. If a tuned estimator/model consumed hold-outs, add untouched validation cases. Do not automatically expand production scope or authorize unrelated operations after a gate passes.
