# V1 independent acceptance prompt

Independently evaluate V1 of `shade_watch_hk`. Your role is an acceptance reviewer, not the implementation author. Assess whether the candidate actually satisfies the predeclared contract, using additional tests and held-out cases. Re-running the developer's suite is necessary but insufficient.

## Pin the exact candidate and contract

Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.

`TARGET_COMMIT`: use the full implementation commit SHA supplied with this request or in the developer's final handoff. If none is supplied, resolve current HEAD to a full SHA before reviewing and verify that it contains the V1 deliverables. Record that immutable SHA; never review a moving branch as the target. If the checkout contains only the planning baseline, report NOT VERIFIED because no V1 candidate exists.

The planning baseline is `7c56760c854cb1e5138c8381a7b68d543b68cdef`. Read `docs/prompts/v1/ACCEPTANCE_CONTRACT.md` in full. Check that its ID is `SW-V1-AC-1.0` and its SHA-256 matches the pre-implementation hash recorded by the developer. Investigate any differences before applying it. Do not silently accept a relaxed contract embedded in the candidate.

Inspect repository instructions and worktree state. Ensure all evaluated production files correspond to TARGET_COMMIT. If local changes would contaminate results, use an isolated checkout through the available managed-worktree workflow, or stop the affected review; never reset or discard user work. Account for path relocation when assessing cache identity, and keep tests on a consistent checkout. Leave `presentations/`, `heat_index_urop`, original DSM, old caches and historical results unchanged.

Do not patch production code, alter developer tests to make them pass, refresh golden outputs or tune the model. You may create independent test harnesses, synthetic fixtures and reports in isolated review locations. Report defects for repair on a new commit. No push, merge or PR creation is requested.

## Scope, data and budget

Use the existing 19 local DSM GeoTIFFs, the V1 artifacts and the project environment. No new DSM downloads, full-Hong-Kong execution or full-year raster run. Observe the shared contract's maximum 45 minutes cumulative real-DSM job wall time, 8 GiB job-memory budget, at most two workers and 10 GiB new generated artifacts. Prefer one worker and small diagnostic windows. Reserve enough budget for a full-native-tile instant query, a bounded real multi-date sequence and matched cold/warm measurements.

Record planned workloads and budgets before expensive execution. If a required check cannot be completed, use NOT VERIFIED and explain whether the cause is unavailable data, environment/hardware or budget. Do not replace a required real-data check entirely with synthetic tests and claim coverage.

## Independent procedure

1. **Audit requirement coverage first.** Map A01–A14 to implementation paths and the developer's claimed evidence. Identify missing tests, circular references, silent fallbacks and unsupported statements. Verify that arbitrary-time support is not nearest-frame lookup and that date/range changes do not silently change the scientific policy.
2. **Freeze a held-out case manifest before examining outcomes.** Read the developer's declared sample set, then choose additional timestamps and windows that were not used to choose direction spacing, interpolation or defaults. Record coordinates, inputs, timestamps, selection seed/method, rationale and expected properties. Do not tune against these cases. If development sample provenance is absent, report the limitation and construct new cases.
3. **Run existing tests and independent checks.** Existing tests establish regression status. Your additional harness must exercise actual public APIs/CLI and independently derived expectations. A reference that calls the production horizon/classification routine is not independent.
4. **Evaluate scientific and operational evidence separately.** Apply the shared tolerances exactly. Test numerical consistency against independent reference calculations; measure directional approximation separately; never call either real-world observational validation.
5. **Write a criterion-by-criterion decision.** Attach each conclusion to reproducible commands, hashes, arrays/metrics, logs and evidence paths. Report counterexamples, not just a summary pass rate.

## Required additional scenarios

The held-out set must contain at least 12 timestamps over at least six dates distributed across the seasons. Include times not divisible by ten minutes, nonzero seconds, an equivalent UTC/HKT pair and a leap date. Include morning/afternoon, low sun and below-horizon cases. Use small windows for most cases so this does not imply twelve full-tile cold runs. Select seasonal dates yourself; do not merely reuse the developer's solstice/equinox cases. Where the existing DSM offers no requested scene type, disclose it and use synthetic fixtures only as a separately labeled supplement.

Cover building edges/narrow blockers, vegetation or rough surfaces, hills, coastal NoData and native-tile boundaries where available. Include these concrete checks:

- **Correct instant:** trace recorded solar parameters to the exact requested timestamp and spatial reference; verify seconds and timezone conversion. Same output labels at two nearby times alone neither prove nor disprove correct time handling.
- **Output invariance:** compare identical global pixels queried alone, in a different combination and through an odd-offset crop. Compare quality as well as shade; inspect canonical reference boundaries separately from processing seams.
- **Real cache reuse:** choose different dates/times that require an already-cached direction, then inspect horizon-call/job counts and entry integrity. Test a further request that requires a new direction. Separate directional-cache reuse from returning a previously rendered frame.
- **Dependency invalidation:** in isolated fixtures/copies, alter, remove or add a buffered source; add/change a distant irrelevant source; corrupt a cache entry. Check exactly which entries are reused or invalidated, including newly available data in a previously missing buffer.
- **Uncertainty:** remove support in a controlled fixture/view. A flat target without a known blocker must not be certified sunlit through missing data. A valid known blocker may still establish shade. Validate target NoData, horizon equality and nighttime handling.
- **Direction approximation:** use unbinned real solar azimuths and directions near bin boundaries. Include a synthetic narrow obstacle between sampled directions. Report horizon-angle errors and shade/quality disagreement with explicit denominators and spatial examples. Do not demand zero approximation error under A10 or conceal it as numerical noise.
- **Independent reference:** derive a small-window ray/classification oracle separately from the production implementation, matching the contract's radial cutoff and rounding semantics. Validate the oracle first on analytic scenes. Explain its remaining shared assumptions. For solar geometry, separate correct use of the selected model from its difference from independently sourced astronomical reference values.
- **Interruption:** safely stop only an isolated review job after at least one directional entry is complete. Restart and prove valid completed work is skipped while partial/invalid work is recomputed. Do not demand V2 durable multi-job orchestration in V1.
- **Performance:** use the same native tile, scientific settings and output selection for empty-direction-cache and warm-direction-cache trials. Ensure the warm trial is not merely a final-result hit. Apply A13's median comparison and log preprocessing, calculation, classification, export/validation, job counts, memory and bytes. Disclose JIT/process/filesystem-cache conditions and measurement gaps.
- **Compatibility/output integrity:** execute a bounded legacy-command smoke run into a new directory, inspect raster alignment/labels and optional media timestamps/frame counts, and verify that native scientific resolution was retained.

## Required report and gate

Produce a compact shareable acceptance report and retain raw evidence locally. The report must contain:

1. Full TARGET_COMMIT, planning baseline, contract ID/hash, environment, dataset identities and the frozen held-out manifest.
2. One row for every A01–A14: PASS / FAIL / NOT VERIFIED, expected behavior, observed behavior, evidence links and any limitation. Cross-reference shared tests when appropriate, but identify your genuinely independent additions.
3. Reproducible defects with affected file/function, input, expected/actual behavior, severity and evidence. Do not fix production code during acceptance.
4. Separate sections for software correctness, scientific numerical consistency, approximation error, performance and real-world validation. Without suitable observations, the last remains NOT VERIFIED.
5. Actual budget use, peak resource measurements, unsupported developer claims, and a concise overall gate: ACCEPTED only if A01–A14 pass; otherwise FAIL or NOT VERIFIED as warranted. An engineering acceptance is not certification of real-world or subpixel accuracy.

After fixes, require a new immutable candidate SHA. Re-run the failed checks and affected regressions and preserve the original failure evidence. If hold-out failures were used for model tuning, choose an additional untouched set for the accuracy claim rather than rebranding the tuned cases as independent validation. Do not move into V2/V3 on your own.
