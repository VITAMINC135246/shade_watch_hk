# V1 acceptance contract — arbitrary-date/time shadow queries

Contract ID: `SW-V1-AC-1.0`  
Planning baseline: `7c56760c854cb1e5138c8381a7b68d543b68cdef`  
Status: proposed execution contract, fixed before implementation starts.

This contract is shared by `DEVELOPMENT_PROMPT.md` and `INDEPENDENT_ACCEPTANCE_PROMPT.md`. It defines V1, not the whole Hong Kong rollout. Before implementation, record its SHA-256 in the development evidence. Acceptance must use that same contract. Do not weaken requirements or select new tolerances after observing results. A necessary contract change must be proposed explicitly, approved by the user, versioned, and assessed as a change of scope.

## 1. Objective and boundaries

Provide a reusable Python API and command-line entry point for a location/area and arbitrary timezone-aware date/time, producing per-pixel shade labels, quality flags, and optional visualizations. Support a single instant, explicit instant lists, and daylight sequences for one or multiple dates. Do not restrict instant queries to existing 10-minute frames.

Separate a fixed DSM-dependent directional obstruction model from date-dependent solar position and classification. Twenty-four solar terms are potential evaluation dates, not a required training set or an annual interpolation mechanism. Do not linearly interpolate binary shadow images to infer uncomputed instants.

Use the existing 19 local DSM GeoTIFFs. V1 establishes a working local prototype, spatially stable scientific rules, reusable directional caches, and measured evidence. V2 will add durable large-job orchestration, richer estimation and performance optimization. V3 will handle territory-wide ingestion and deployment. A GUI, network service, GPU backend, cluster deployment, full-Hong-Kong run, and full-year raster export are outside V1.

## 2. Available inputs and protected material

- Project: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.
- Python: project `.venv/bin/python`; use existing dependencies where possible.
- DSM: `data/raw/dsm/2020/D12.DSM.TIFF/*.tif`, currently 19 files.
- Existing six-tile mosaic: `outputs/native_mosaic_6tiles_1km_20260929/`.
- Existing six independent runs: `outputs/individual_6tiles_20261001/`.
- Context: `docs/ARCHITECTURE.md`, `docs/METHOD.md`, `docs/NATIVE_MOSAIC_2026-09-29.md`, and `docs/RUN_INDIVIDUAL_TILES.md`.

Original DSM, accompanying metadata, historical results, and old caches are read-only. Preserve unrelated work, including `presentations/`, and do not modify `heat_index_urop`. Synthetic fixtures, masked input views, or isolated copies may be used for controlled missing-data and invalidation tests; never edit the originals. Do not download replacement DSM or add new datasets in V1.

## 3. Scientific and interface contract

1. Preserve native 0.5 m resolution, EPSG:2326 alignment and source-tile geometry. A normal spatial work unit remains one native tile, currently 1500 columns by 1200 rows, with a 1000 m buffer on every side and a radial maximum obstruction-search distance of 1000 m. Small cropped diagnostic windows are allowed in tests.
2. Preserve the adopted pixel-centred ray semantics: 0.25 m nominal sampling, documented nearest-cell rounding, radial cutoff, and missing-data handling. Define a canonical coordinate/parity anchor independent of the requested output extent. Any intentional scientific change requires its own version and explicit comparison with the old method.
3. Retain scientific labels `1=shaded`, `0=sunlit`, `255=invalid/uncertain`, and machine-readable reasons. Missing DSM is not zero elevation or proof of sunlight. A known blocker can establish shade despite incomplete support; incomplete support cannot establish sunlight. Define and test horizon equality, below-horizon solar conditions, and refraction conventions.
4. Freeze a documented, output-independent solar-reference policy and uncertainty policy before changing those calculations. Resolve the current dependence on the union output centre and whole-output elevation range. Fixed canonical tile references may be evaluated as an approximation; per-pixel coordinates provide a comparison reference. Do not claim that tile-centre solar positions equal per-pixel solar positions. Test reference-boundary effects separately from computational seams.
5. Preserve coordinates supplied by the user. In native mode they select a source tile; native output retains its geometric centre/bounds. Explicit custom mode may change the requested centre and extent. Numerical spatial references must follow the frozen policy, rather than changing merely because a query combines more tiles.
6. Use `Asia/Hong_Kong` as the documented local default and normalize explicit aware timestamps. Preserve seconds. Reject ambiguous/invalid inputs clearly or apply a documented explicit convention; do not silently discard time zones or snap arbitrary times to saved frames. Support equivalent UTC/HKT inputs and leap dates.
7. Implement `plan_shade(...)` and `run_shade(plan)` or equivalent clearly documented APIs. Planning may inspect metadata and cache availability, but must not start horizon computation, render media, or modify scientific outputs. No interactive confirmation is required between planning and running an already authorized request.
8. A plan records requested and resolved spatial bounds, timestamps, data dependencies, expected/missing direction jobs, coverage limitations, outputs and resource settings. V1 may report honest task counts instead of a calibrated whole-Hong-Kong time estimate.
9. Outputs include native-resolution shade and quality GeoTIFFs, a machine-readable result index and optional JPG/MP4. Media must be independently switchable. A single instant does not require a video. Scientific data, classification and visualization are separate concerns.
10. Use a new versioned cache namespace. A directional cache identity depends on canonical spatial geometry, relevant buffered DSM content/metadata, direction, algorithm and numerical settings. It must not depend on the query date, requested mosaic membership, unrelated distant source files, or output-directory name. If a dependency is added, removed or changed within the buffered domain, relevant caches must invalidate. A previously missing neighboring tile becoming available is also a dependency change.
11. Cache validation and publication must be atomic and corruption-aware. A second process must not publish a conflicting cache entry. Reuse must be demonstrated at the horizon-computation level, not merely by returning an old final image.
12. Preserve legacy commands and historical result readability. Document intentional differences in V1 outputs caused by corrected scientific policies; do not silently overwrite old results or describe all such differences as regressions. Do not reuse old caches unless their scientific identity is proven compatible.

## 4. Shared acceptance matrix

For every ID below, both reports must give a result and concrete evidence paths. The independent review must add cases rather than just repeat the developer suite.

| ID | Requirement | Required pass evidence |
| --- | --- | --- |
| A01 | Provenance and isolation | Exact source commit, contract hash, input identities, environment and commands recorded; original DSM and historical artifacts preserved. |
| A02 | Unified API and planning | Executable Python and CLI examples for an instant, instant list and multi-date daylight sequence; planning performs zero horizon calls and no scientific/media output writes. |
| A03 | Arbitrary time and solar provenance | Off-grid timestamps, seconds, UTC/HKT equivalence and a leap date tested; result metadata preserves the requested instant and calculated solar parameters; no nearest-frame substitution. |
| A04 | Spatial semantics | Native bounds/centre retained; explicit custom request resolved and aligned as documented; clipped and nonrectangular tile selections handled or rejected explicitly without silently inventing coverage. |
| A05 | Output-extent invariance | Same pixels and instant produce identical shade/quality arrays when queried alone, as a crop and in a larger combination under the same V1 policy; continuous horizon values differ by no more than 1e-4 degrees where both are finite. Include an odd-pixel crop offset. |
| A06 | Correct missing-data semantics | Synthetic flat/blocked scenes, target NoData and missing sunward buffer cases preserve correct labels and reasons; missing data never becomes zero-height ground; known-blocker and unknown-sunlight cases are distinguished. |
| A07 | Cross-date and cross-range reuse | Instrumented tests show zero new horizon evaluations for already-cached tile/direction dependencies after changing date or output combination. A query requiring a missing direction computes only the missing entries. |
| A08 | Dependency invalidation | Isolated tests cover changed, removed and newly added relevant sources, distant unrelated sources, algorithm settings and corrupted cache artifacts. Relevant entries invalidate; unrelated entries remain reusable. |
| A09 | Scientific numerical verification | Analytic fixtures and an independently implemented small-window reference test the actual documented ray/quality semantics. For the same exact direction, finite horizon differences are <=1e-4 degrees; support flags match exactly. Binary classifications match outside a declared 1e-4-degree equality neighborhood, whose counts and treatment must also be reported. |
| A10 | Direction approximation assessed honestly | Compare the existing 5-degree nearest-direction baseline with at least one candidate improvement, using direct unbinned directions on small real windows. Report horizon error, label disagreement, coverage/quality changes, runtime and storage. Default choice and limitations are documented. No physical per-pixel accuracy claim follows from these tests. |
| A11 | Output integrity and resource control | GeoTIFF dimensions, CRS, transforms, nodata, labels and metadata validated; optional media matches requested timestamps and frame count. No allocation proportional to full-year frame count or entire combined DSM is introduced. Measure parent/worker/media peak memory, or explicitly state measurement gaps. |
| A12 | Basic recovery and regression | Isolated interruption/corruption test skips completed valid direction jobs and recomputes incomplete/invalid jobs; existing automated tests pass or intentional versioned changes are explained and tested. Legacy commands receive an actual bounded smoke run, not only `--help`. Durable V2 batch-queue recovery is not a V1 requirement. |
| A13 | Performance evidence | Separate truly empty scientific-cache runs, warm directional-cache queries and final-result cache hits. Report preprocessing, horizon work, classification, output/validation time, cache job counts, hardware and bytes. Compare equivalent requests with identical output settings. For a representative native-tile query needing horizon work, warm-direction-cache scientific-query median must be lower than cold-scientific-cache median; no fixed speedup is promised. |
| A14 | Reproducible handoff | Code, tests, API/CLI examples, policy decisions, migration notes, limitations, development report and evidence manifest are present; delivery identifies an immutable implementation commit. Large DSM/cache/output artifacts remain untracked. |

The 1e-4-degree tolerance is an engineering numerical-consistency tolerance, not a tolerance for directional approximation, solar-model physical error, or agreement with observations. Do not hide invalid pixels or boundary cases when calculating metrics: report denominators, valid-mask differences and excluded equality cases explicitly. Report spatially concentrated errors, not only a whole-image average.

No real-world accuracy percentage or maximum acceptable approximation-error percentage has been agreed. A10 passes when the comparison and limitations are complete and honest; it does not certify that the default direction spacing meets an unstated scientific accuracy target. Any later accuracy threshold must be agreed before selecting/tuning a method against the final validation set.

## 5. Budgets and staging

Defaults are ceilings, not workload targets. Use one worker by default, at most two concurrently, an 8 GiB total job-memory budget, and at most 10 GiB of new generated artifacts per development or independent-acceptance campaign. Preflight available disk space. Stop only the campaign's own processes if its limits are exceeded.

- Development: at most 60 minutes of cumulative wall time for real-DSM calculation/benchmark jobs. Use small windows for extensive numerical comparisons, and include at least one complete native-tile production query. Avoid repeated all-day video renders during debugging.
- Independent acceptance: at most 45 minutes of cumulative wall time for real-DSM jobs. Include a full native-tile instant query and a bounded real multi-date sequence; use cropped windows for the larger held-out matrix. Up to three cold and three warm trials of a one-direction-dominated query may be used for medians. Declare process/JIT/filesystem-cache conditions.
- Test computation must use new output/cache locations and may not overwrite the historical six-tile runs. Keep cumulative runtime, peak memory and generated bytes in a ledger.
- Do not simulate all 365 days or download/run all Hong Kong. Do not exhaust the budget simply because time remains.

If a required test cannot be completed within budget, record it as NOT VERIFIED with the reason and the bounded additional work needed. Do not mark it PASS, silently relax the test, or keep launching large jobs. Continue documentation and unaffected checks.

## 6. Evidence and release decisions

Use exactly `PASS`, `FAIL`, and `NOT VERIFIED` per criterion, with the reason for NOT VERIFIED distinguished as missing data, unavailable environment/hardware, or exhausted execution budget. `FAIL` is a demonstrated requirement violation. An untested claim is not a pass.

Reports must distinguish: software behavior; scientific numerical consistency; directional/solar approximation error; observed performance; and real-world validation. Real-world validation remains NOT VERIFIED unless suitable independent observations actually exist. Missing observations do not prevent an engineering V1 release, but must not be converted into an accuracy claim.

V1 is accepted only when A01–A14 pass. Otherwise the gate is FAIL or NOT VERIFIED as appropriate. Passing V1 authorizes no V2/V3 implementation by itself. Retain raw local evidence, a compact shareable report, test IDs, commands, source/input hashes and a mapping from each conclusion to evidence.
