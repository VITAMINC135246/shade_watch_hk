# Package B2.0 development report — SW-B2.0 / SW-B2.1

Development candidate, 2026-11-04 to 2026-11-05 HKT. This report is not independent acceptance. Observational accuracy is NOT VERIFIED.

The DSM-only classifier, immutable sea view, `sea-2.0` provider, void-impact diagnostic, report-only validator and synthetic tests are implemented. The engine, region adapter and B1 functions are unchanged. The candidate has an observed **B2-08 failure**: F1.0’s frozen publisher rejects the required surface codes 2 and 254. No unapproved publication change or relabelling was made.

## Traceability

- Starting branch and SHA: `feature`, `05c66ab379d87868a787ae78cdecbfb918c1730e`.
- Accepted F1.0: `35225fd9547a00e4df202e7ab30204c633b2c845`. The accepted code was archived read-only for the two amended raw-plan checks.
- Contract SHA-256: `b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`. Amendment SHA-256: `18a09995cbbd1cca659c9a548aad9a0cb45c942668a58ce17146d371f9f8450d`. Both verified before edits and again on resume.
- Both raw run IDs match the accepted F1.0 snapshot. `config/regions/cheung_chau.json`: `c196a09a3a213e0720b8dcb5ea5b4edb32ad217fcabcb70a930a9b17b458878e`. Saved `f1_cheung_chau`: `e608af7ffe4181f3d097ce3f776f464b5b79fc67f1c1e5dc12bc6806a421b1ca`.
- Engine environment matches every package pin in `requirements.lock.txt`. Both lock digests are in the evidence. The historical separate tools package directories were empty; no complete offline pinned reader was found.
- The four `14NE15*` transforms and NoData metadata are preserved. Only border adjacency uses lattice addressing; distance calculations retain actual native centre offsets. The literal non-finite/-9999 rule does not reinterpret the four tiles’ other finite sentinel. The unchanged adapter still rejects dependencies on these tiles.

## Build and numerical evidence

- Completed view `df707ce89852a65121e3ba4542da99814139db20b6bfc4459bdbf7a3eadcb6e2`: 7,128 surface cells, 3,310 supplied DSM tiles, 1,101 synthetic tiles; 1,472 supplied tiles filled and read back. Territory counts: `{"0": 4384416867, "1": 1453438606, "2": 1315054618, "254": 5285979918, "255": 93109991}`.
- Read back all 1,101 synthetic tiles: content hashes, native georeferencing, exact float32 sea height and NoData outside water all matched.
- Cheung Chau target classes: `{"0": 3322313, "1": 3877687, "2": 0, "254": 0, "255": 0}`. The authorised targets contain only 0/1, so the frozen F publisher can handle these particular windows even though the general B2-08 integration fails.
- Central target classes: `{"0": 7026501, "1": 173499, "2": 0, "254": 0, "255": 0}`. The authorised targets contain only 0/1, so the frozen F publisher can handle these particular windows even though the general B2-08 integration fails.
- Cheung Chau: 65 measured frames from F publication. Shaded→sunlit: 0; unfilled targets with non-255 shade: 0; unexplained sunlit losses: 0. The per-frame former-Quality-2 transitions and per-tile thresholds are in the comparison JSON.
- At 12:30 HKT, observed-land Quality 2 went from 53.04% to 0.00% with the same 3,322,313 observed land pixels. This is model support, not observational accuracy.
- Central: 3 measured frames from F publication. The two urban label gates passed. The DSM-only halo counts do not substitute for the map-defined Victoria Harbour share.
- Independent water rays: 800 targets (69 near tall structures), 0 mismatches outside tolerance, 800 targets (69 near tall structures), 0 mismatches outside tolerance, 800 targets (69 near tall structures), 0 mismatches outside tolerance.
- Void-impact completed 65 frames. Daily trigger records: `[{"date": "20260107", "exceeds_10_percent": false, "frames": 65, "mean_void_attributable_fraction": 0.0}]`.

## Acceptance matrix

| Item | Status | Finding | Evidence |
| --- | --- | --- | --- |
| B2-01 | **NOT VERIFIED** | Engine, adapter, B1 and allowed F diff verified; the separate pinned tools environment could not be instantiated. | [start.json](evidence/start.json), [final-scope-audit.json](evidence/final-scope-audit.json), [engine-environment.json](evidence/engine-environment.json), [tools-environment.json](evidence/tools-environment.json) |
| B2-02 | **PASS** | Build, plan, F run and void-impact completed while coastline access was denied. The readable plan kept the same view and run IDs; F verification and diagnostic resume preserved the manifest and CSV/JSON hashes. The runtime code audit found no coastline reader. | [DSM-only-build-2-corrected.json](evidence/DSM-only-build-2-corrected.json), [DSM-only-sea_plan.json](evidence/DSM-only-sea_plan.json), [DSM-only-cheung_chau_sea.json](evidence/DSM-only-cheung_chau_sea.json), [DSM-only-cheung_chau_void_impact.json](evidence/DSM-only-cheung_chau_void_impact.json), [DSM-only-equivalence.json](evidence/DSM-only-equivalence.json), [final-scope-audit.json](evidence/final-scope-audit.json) |
| B2-03 | **PASS** | Hand-computed open, high/low/preference/range, enclosed and empty cells, diagonal, border and exclusion fixtures. | [pytest-native-centres.txt](evidence/pytest-native-centres.txt), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-04 | **PASS** | Overlapping aligned surface requests match; independent one-pass EDT matches tiled and certified blocks. | [pytest-distance.txt](evidence/pytest-distance.txt), [pytest-native-centres.txt](evidence/pytest-native-centres.txt), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-05 | **PASS** | All 1,472 changed supplied tiles passed bitwise preservation outside water, exact float32 sea height and metadata checks. Territory and per-cell counts reconcile; the four native transforms and NoData values were retained. | [build-2-corrected.txt](evidence/build-2-corrected.txt), [view-facts.json](evidence/view-facts.json), [catalogue-metadata-groups.json](evidence/catalogue-metadata-groups.json) |
| B2-06 | **PASS** | Exact synthetic cell inventory, complete synthetic readback and strict overlap evidence; the completed F plan invokes the unchanged request-local index. | [view-facts.json](evidence/view-facts.json), [synthetic-readback.json](evidence/synthetic-readback.json), [sea_plan.txt](evidence/sea_plan.txt), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-07 | **NOT VERIFIED** | No pair of complete territory builds. Fixture reproducibility and available engine plan/cache/policy identities are recorded. | [build-1-budget-stop.json](evidence/build-1-budget-stop.json), [resume-budget.json](evidence/resume-budget.json), [engine-plan-identity.json](evidence/engine-plan-identity.json), [real-run-provenance.json](evidence/real-run-provenance.json) |
| B2-08 | **FAIL** | Both raw identities match and existing F tests pass. The frozen F publisher rejects required surface 2/254; the positive integration test reproduces this exact failure. | [raw-identity-regression.json](evidence/raw-identity-regression.json), [f-publication-blocker.json](evidence/f-publication-blocker.json), [f-publication-blocker-pytest.txt](evidence/f-publication-blocker-pytest.txt), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-09 | **PASS** | All 65 F-published frames passed the numerical land gates, with per-frame Quality-2 transitions and per-tile thresholds recorded. The class-254/255 target set was empty; the synthetic fixture covers the unknown shade label. | [cheung_chau-comparison.json](evidence/cheung_chau-comparison.json), [real-run-provenance.json](evidence/real-run-provenance.json), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-10 | **NOT VERIFIED** | Both Central numerical gates passed. All 11,010,914 NoData pixels in the halo became water, so any nonempty Victoria Harbour NoData subset is 100% filled; its map-defined denominator was not verified. | [central-comparison.json](evidence/central-comparison.json), [view-facts.json](evidence/view-facts.json), [reader-availability.json](evidence/reader-availability.json) |
| B2-11 | **PASS** | Independent direct 0.25 m rays at three instants; label comparison uses the engine equality tolerance. | [cheung_chau-sea-rays.json](evidence/cheung_chau-sea-rays.json), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-12 | **PASS** | All 65 real diagnostic frames reconcile with independently read rasters and the schema. The scope contained zero enclosed void pixels. The synthetic fixtures exercise the fill, report, precondition and resume with enclosed void pixels. | [cheung_chau_void_impact.txt](evidence/cheung_chau_void_impact.txt), [cheung-chau-void-impact.json](evidence/cheung-chau-void-impact.json), [void-impact-readback.json](evidence/void-impact-readback.json), [counterfactual-view-facts.json](evidence/counterfactual-view-facts.json), [pytest-full.txt](evidence/pytest-full.txt) |
| B2-13 | **NOT VERIFIED** | The pinned reader packages were absent. No iB5000 or nine-variant real report numbers were invented; no downloads or changes to the profile. | [validation-attempt.txt](evidence/validation-attempt.txt), [reader-availability.json](evidence/reader-availability.json), [ib5000-report.json](evidence/ib5000-report.json), [sensitivity-report.json](evidence/sensitivity-report.json) |
| B2-14 | **NOT VERIFIED** | First build exceeded the actual wall cap before the original uptime timer problem was detected. Preserve the failure and all later resource/namespace evidence. | [protected-before.json](evidence/protected-before.json), [protected-after.json](evidence/protected-after.json), [resource-summary.json](evidence/resource-summary.json), [resources.jsonl](evidence/resources.jsonl), [build-1-budget-stop.json](evidence/build-1-budget-stop.json) |
| B2-15 | **PASS** | Existing suite passes unchanged; new strict expected failure retains the publication conflict. Code, schemas, docs and this evidence are handed off in one local commit. | [pytest-full.txt](evidence/pytest-full.txt), [manifest.json](evidence/manifest.json), [final-scope-audit.json](evidence/final-scope-audit.json) |

Criterion totals: 9 PASS, 1 FAIL, 5 NOT VERIFIED.

## Resource ledger and write scope

| Measurement | Measured | Cap |
| --- | ---: | ---: |
| Real-DSM jobs, including raw/sea plans | 47.13 min | 60 min |
| First build phase, actual elapsed lower bound including failed launches | 72.05 min | 60 min |
| Second build phase, including its stopped attempt | 59.31 min | 60 min |
| Highest measured process/tree RSS | 1.623 GiB | 12 GiB |
| Highest measured new artifacts | 5.208 GiB | 30 GiB |

The first attempt did not finish. Its initial watchdog used Mac uptime, which omitted system sleep. Once the actual elapsed overrun was detected, the job was stopped and only its own staging files were removed. The corrected watchdog includes wall elapsed; idle sleep was prevented for subsequent builds. The second attempt’s native-centre correction and restart were charged to the same remaining budget, including across the quota interruption. There was no budget reset.

The initial permission-test launcher was accidentally re-imported by worker spawning during the Cheung Chau job. Its entry guard was fixed and the same V2 batch continued; no cache, state, F or engine code was reset or edited. The entire elapsed time is charged to that real job.

Protected inventory: existing files unchanged = `true`; unexpected new paths = `0`; coastline permissions restored = `true`. New F request views and work use fresh leaves in the adapter/runner containers. No unrelated regional/territory shade computations, V3, downloads, exception zones or pushes were performed.

Full `pytest tests -q`: **271 passed, 1 xfailed, 4047 warnings in 74.75s (0:01:14)**. The strict expected failure is new and isolates the proven F publication incompatibility; it does not change the B2-08 verdict.

## Commands and handoff

Run from the repository root using `.venv`. Campaign configs are in `evidence/configs/`. Each real invocation was measured; see the command and memory records in `evidence/resources.jsonl`.

```sh
.venv/bin/python -m tools.sea2 build --machine docs/sea2/evidence/configs/machine.json
.venv/bin/python -m tools.shade_map plan --machine docs/sea2/evidence/configs/machine.json docs/sea2/evidence/configs/cheung_chau_sea.json
.venv/bin/python -m tools.shade_map run --machine docs/sea2/evidence/configs/machine.json docs/sea2/evidence/configs/cheung_chau_sea.json
.venv/bin/python -m tools.sea2 void-impact --machine docs/sea2/evidence/configs/machine.json docs/sea2/evidence/configs/cheung_chau_sea.json
.venv/bin/python -m pytest tests -q
```

The Central variants use `central_raw.json` and `central_sea.json`. The comparison and ray command logs identify whether their input is a complete F publication or completed V2 work. See GUIDE.md for the separate locked iB5000 command. These commands describe evidence/reproduction and do not grant new compute authority.

A minimal **unapproved** follow-up would allow one publication change by a new agreed contract version: replace only the surface allowlist at `tools/shade_map/publication.py:141` with `[0, 1, 2, 254, 255]`; retain the shade and quality lists. The five-class test would then be required to pass without its expected-failure mark. Any matching completed V2 work can be considered for normal F resume after that separate decision.

The candidate is delivered as one local commit. The handoff message gives its full SHA. Independent acceptance remains separate.
