# V1 development prompt

Implement V1 of the existing `shade_watch_hk` project: arbitrary-date/time per-pixel shadow queries backed by a reusable, fixed-DSM directional obstruction model.

## Start from the real project

Working directory: `/Volumes/My Passport for Mac/Projects/shade_watch_hk`.

The planning baseline is commit `7c56760c854cb1e5138c8381a7b68d543b68cdef`, on branch `feature`. Inspect the actual checkout, current HEAD, applicable repository instructions and local changes before editing. Record both the planning baseline and actual starting commit. Do not reset the checkout or discard subsequent work. Preserve unrelated files, especially `presentations/`, and do not touch `heat_index_urop`. Keep branch `feature` unless the user instructs otherwise.

Read `docs/prompts/v1/ACCEPTANCE_CONTRACT.md` in full. It is the shared, pre-implementation acceptance contract `SW-V1-AC-1.0`; record its SHA-256 before implementation. Read the architecture, method and individual-tile documentation identified there. Inspect the actual code rather than assuming all documented behavior is current.

The existing environment is `.venv`; there are 19 local DSM files in `data/raw/dsm/2020/D12.DSM.TIFF/`. Preserve the source data, historical six-tile mosaic/independent outputs and existing caches. No new DSM downloads are authorized. New test outputs belong in an isolated V1 directory under `outputs/`, and new scientific caches in a versioned namespace under `data/processed/`.

## Objective and scope

Provide a Python function/API and matching CLI that accept location/area plus arbitrary date/time and return native-resolution shade/quality data, a result index and optional visualizations. Support instant queries, explicit instant lists and one-/multi-date daylight sequences. Keep the original commands usable.

The scientific structure is: fixed DSM -> reusable obstruction angle by pixel and azimuth -> solar position at the requested instant -> classification. Do not estimate arbitrary instants by interpolating binary maps from 24 representative days. Solar terms may be useful test dates, but must not constrain query dates.

V1 covers local correctness, a stable API, output-independent scientific definitions and reusable caching. Do not implement a GUI, web service, GPU rewrite, territory-wide data download, cluster scheduler or full-year raster export. Durable large-batch orchestration and calibrated territory-wide estimates belong to V2/V3. Basic cache-level interruption recovery remains required in V1.

## Required implementation order

1. **Establish the baseline.** Inventory the existing tests, command behavior, known scientific limitations and available real-data outputs. Record source/input identities and baseline measurements without modifying historical artifacts. Create a traceability map from A01–A14 to planned code and tests.
2. **Freeze the V1 design before numerical changes.** Document the canonical spatial anchor, native/custom bounds behavior, solar-reference policy, uncertainty policy, timestamp conventions, equality handling and versioning. Remove dependence on the user-selected mosaic extent. If you retain tile-centre solar approximations, name them and compare them with per-pixel references. Do not silently change the 1 km or ray-sampling model. Make routine implementation decisions yourself within the contract; seek clarification only for a genuine unresolved scientific/scope decision.
3. **Separate inputs from execution.** Add validated request/plan/result models and `plan_shade(...)` / `run_shade(plan)` or equivalent. Stop mutating shared config files to change dates. Planning must inspect and describe work without launching horizon calculations or rendering outputs. Expose the same behavior through CLI commands, with runnable examples.
4. **Make spatial dependencies and caches canonical.** Index the local DSM files; identify buffered dependencies per native tile. Use tile/direction/content-based cache identities independent of date and output composition. Handle newly available support tiles, removed/changed dependencies, corruption, atomic publication and conflicting writers. Use a new namespace rather than overwriting legacy caches.
5. **Implement queries and optional outputs.** Use the requested instant, including seconds and timezone, to calculate solar parameters. Combine cached obstruction data with the frozen spatial/quality policies. Support native tile, selected tiles and documented custom extents. Compose/crop results without redefining the science for the same pixels. Separate scientific output from JPG/video rendering.
6. **Assess the directional approximation.** Keep the current 5-degree nearest-direction scheme as a named baseline. Compare it with at least one reasonable improvement on small real windows and synthetic scenes. Use a direct unbinned-direction reference. Do not claim that a finite direction table is exact, or that interpolation preserves narrow blockers. Choose and document the V1 default using development cases, leaving independent hold-outs untouched.
7. **Complete tests, evidence and handoff.** Implement the contract tests as work proceeds, fix discovered defects, run bounded real-data checks, and finish documentation and migration notes. Follow the 60-minute real-DSM computation ceiling, memory/concurrency and artifact budgets in the contract.

## Testing is part of development

Do not defer testing to the acceptance reviewer. Exercise new features and existing regressions throughout development, including actual API/CLI use and a small amount of real-data execution. Do not create tests that merely restate implementation code.

At minimum, test off-grid timestamps, UTC/HKT equivalence, leap dates, solar horizon boundaries, native/custom spatial behavior, odd-pixel crop offsets, isolated vs combined requests, missing DSM, missing sunward support with/without a known blocker, cross-date/cross-range cache reuse, relevant and irrelevant dependency changes, corrupted/partial cache entries, and cache-level interruption recovery.

Use a simple independently implemented reference and analytic fixtures for numerical tests. Do not make the supposed reference call the production horizon/classification functions. Report the scientific approximation of `src/solar.py` honestly; checking that V1 calls the existing solar function correctly is not independent proof of astronomical accuracy.

Measure cold scientific-cache work, warm directional-cache queries and final-result cache hits separately. Instrument actual horizon jobs/calls; unchanged filenames alone do not prove reuse. State which time includes compression, rendering, validation, process startup and JIT compilation. Use identical scientific/output settings in matched performance comparisons. Keep budget and evidence ledgers.

For every A01–A14 criterion, report PASS, FAIL or NOT VERIFIED with evidence. Do not claim real-world accuracy without observations, and do not turn a budget/data limitation into a pass. Tests already passing need not be rerun repeatedly without a new reason.

## Deliverables and completion behavior

Deliver:

- Working code and automated tests implementing V1 only.
- An API/CLI guide with copyable examples for a single instant, a multi-date request, a planning-only request, optional media and cache reuse.
- Versioned scientific-policy and cache-migration documentation, including known differences from legacy results.
- A compact development verification report mapping A01–A14 to commands, inputs, measurements and raw evidence paths; record the contract hash and development sample set.
- A manifest of evidence, input hashes, environment, runtime/memory/disk ledger, approximation results and unresolved limitations. Keep large artifacts in ignored local directories.
- A local implementation commit containing only necessary code, tests and concise documentation. Report the full immutable commit SHA for independent acceptance. Do not push or open a PR unless separately authorized. Do not include unrelated work or raw/generated datasets.

Before reporting completion, inspect the staged diff for accidental data, secrets or unrelated edits. State which criteria passed, failed or remain unverified and why. Do not label the result accepted: independent acceptance is a separate step. If scientific correctness or the budget blocks completion, preserve evidence and report the smallest concrete next action rather than weakening the contract. Stop at V1; do not begin V2/V3 automatically.
