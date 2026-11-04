# F1.0 development report — SW-F1.0

Date: 2026-10-31. This is developer verification of a local candidate, not
independent acceptance. Engineering acceptance remains pending. Observational
accuracy remains NOT VERIFIED; numerical equality with the engine is a separate
claim. Shade is not cooling and not ΔT.

## Baseline and implementation

Started on `feature` at `d1a89c80306e8a3a2f2a5f1edf45149b419919d2`, which contains
A1.1 `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`. The contract hash was checked
**before editing** and is unchanged:
`dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690`.
The ten engine files remain byte-identical to
`356f611d7b775ce31006904b80ca31d3c1c484b2`; the region adapter remains byte-identical
to A1.1. See [start](evidence/start.json), [environment and lock files](evidence/environment.json),
[final traceability](evidence/final_traceability.json).

New files implement `python -m tools.shade_map plan|run|prune` and the
`shade_map` / `plan_shade_map` Python API. Configuration, strict corner/time
validation, source providers, content identity, labelled estimates, isolated V2
state, per-frame publication, relative VRTs, summaries, locks, durable resume and
ownership-checked prune live in `tools/shade_map/`. No engine, scientific policy,
sea view, historical output, existing cache namespace, download, V3, web page,
package installation, push or PR was used or changed.

The six schemas cover machine, region, plan, frame, run and summary formats.
The hand-written validator's schema walker checks **99 configuration constraint
instances** with valid and invalid witnesses. Semantic checks cover corner order,
projection, calendar validity and physical-time duplicates. Explicit clocks are
fixed UTC+8, including historical dates; daylight dates remain engine dates.

A complete rerun verifies publication/source/engine hashes without starting V2.
Saved immutable batch definitions are reused on incomplete runs. Source identity
preview and an existing name lock run before any new source view can be written
for a conflicting or concurrent request. Frame bytes are independent of the
run name, cache namespace, host and interruption history.

## Real execution and numerical evidence

- **(a) Cheung Chau:** the source-view gate matched all 21 historical DSM tile
  names before computation. Fresh namespace `f1_dev_20261031_a`; 108 computed
  directional entries, zero reused. The CLI completed in **634.37 s** including
  planning, computation, publication and verification. Exactly **65 frames**,
  07:10–17:50 HKT, 7,200,000 pixels per frame. Every shade and quality pixel
  equals the read-only historical reference. Each cell, VRT, full image, surface
  class, transform and summary was also checked. All 195 VRTs opened identically
  after copying the complete run folder. At 12:30, the DSM-observed surface's
  Quality 2 fraction rounds to **53.0%**.
- **(b) Sparse fractional WGS84 rectangle:** frozen before execution in
  [frozen rectangle](evidence/frozen_sparse_rectangle.json). Engine-resolved
  bounds are `[820240,808390,820260.5,808410.5]`, 41 × 41 pixels. Four clipped
  native cells include one no-DSM cell. Window 12:30, 12:40, 12:50; the separate
  instants request keeps 12:30 and drops 00:00 as `outside daylight`. All four
  published frames equal the independent V1 custom-bounds references. The V1
  reference cache was separate and cold: 6 computed directions, zero reused.
  No-DSM pixels are shade 255, quality 1 and surface 255.
- **(c) Interruption:** actual SIGKILL during computation and during publication,
  each with a fresh name and cache. Both resumed runs' **57 frame-file hashes**
  equal the uninterrupted window run. Previously completed V2 tasks were not
  repeated. The publication test retained the first frame's file hashes and
  modification times, verified the completed V2 batch without resubmission,
  rebuilt the partial frame and left no `.partial` folders. A real concurrent
  CLI was rejected with exit 2 in **0.42 s**.
- **Prune:** the real sparse run's dry-run changed nothing. Confirmed prune
  deleted only its 24 working files; the only other changed file was its manifest
  recording prune. Published rasters, horizon caches, source views and other runs
  were retained. A following run verified all hashes, computed zero batches,
  and did not recreate the work folder.

Published JSON was checked for absolute paths outside the machine record;
none were found. All output paths meet the character, case and length rules.
Summary CSV rows and JSON counts were independently reconstructed from raster
values. Fractions use the whole surface class, including uncertain pixels.

The run manifest cannot hash its own byte stream. Its file table hashes every
other published file, and its `integrity_sha256` hashes the canonical manifest
excluding that one field. Frame records analogously hash their layer files and
carry canonical integrity. This self-reference convention is documented in the
guide. Published rasters/sidecars/caches remain outside git; committed evidence
is text/JSON only.

## Development matrix

PASS here denotes the listed development check, not independent acceptance.

| ID | Status | Evidence and commands |
| --- | --- | --- |
| F1-01 | PASS | `start.json`, `environment.json`, `final_traceability.json`; ancestry, contract checksum, exact engine/adapter comparisons and empty `git diff <start> -- src/ tools/region_request.py config/v3/`. Only newly created task files are staged for the sole local commit; full SHA is supplied in the handoff. |
| F1-02 | PASS | `schema_rule_coverage.json`, `synthetic_tests.txt`; 99 schema constraints; missing/unknown/type/range/name cases, machine-independent identity and corner/time identity changes. |
| F1-03 | PASS | `synthetic_tests.txt`, `tests/test_shade_map.py::test_corner_cli_no_writes`; both CRSs, coordinate swaps/equalities/non-finite values, WGS84 latitude/longitude ranges, projected-order check, CLI exit/prefix and unchanged listings. HK1980 has finite/order checks without an invented geographic range. |
| F1-04 | PASS | `test_daylight_equal_engine` on 2026-01-07, 2026-06-21 and 2026-12-21; inclusive ranges/windows, equal/end-before-start, outside-daylight drops, duplicate/seconds/offset rejection, unique folders and explicit lists spanning multiple engine requests. |
| F1-05 | PASS | Three synthetic adapter request/key equivalences; source-view-only plan listings, strict plan schema, shifted-origin rejection and all four existing-run statuses in `synthetic_tests.txt`; real `sparse_plan_before_execution.json`. |
| F1-06 | PASS | Raw registry provider and fixture provider with surface class 1 through identical publication code in `test_source_interface_surface_one`. No sea policy is implemented. |
| F1-07 | PASS | `a_pixel_verification.json`, `b_pixel_verification.json`, `instant_pixel_verification.json`; all cells, clipped edges/missing cell, dtype/CRS/NoData/compression, relative portable VRTs, full images and path rules. |
| F1-08 | PASS | Same three verification records; every primary frame/cell/VRT/full image equals `read_region_window`, and surface equals direct DSM classes. |
| F1-09 | PASS | `cheung_chau_source_gate.json`, `a_pixel_verification.json`, `cheung_chau_1230_summary.json`; 21-source gate, 65 exact frames, zero differing shade/quality pixels against the historical reference. |
| F1-10 | PASS | `frozen_sparse_rectangle.json`, `sparse_plan_before_execution.json`, `independent_v1_reference.json`, `b_pixel_verification.json`, `instant_pixel_verification.json`; cold independent V1 references, 255/1/255 missing-cell values and dropped night time. |
| F1-11 | PASS | `kill_compute_resume_verification.json`, `kill_publish_resume_verification.json`, SIGKILL/lock evidence in `resource_ledger.json`, `conflict_and_prune.json`; exact hashes, task/frame reuse, no partials, real concurrent refusal and conflict with no writes. Synthetic renamed-before-manifest recovery is also covered. |
| F1-12 | PASS | Runtime schema/seal/file checks, all-frame raster/count/CSV/whole-class fraction reconstruction in pixel evidence; `conflict_and_prune.json`; synthetic incomplete-prune refusal, actual dry-run/deletion and verify-only rerun. The sparse manifest's before/after-prune hashes are recorded separately. |
| F1-13 | NOT VERIFIED | `protected_before.json`, `protected_after.json` show no protected-file changes or unexpected additions. All measured real computations and total charged wall/disk usage are within budget, but the first read-only planning process's peak memory was not captured; the complete resource criterion is therefore not claimed PASS. See resource/failure discussion below. |
| F1-14 | PASS | `full_tests.txt`: **189 passed**, including the unchanged existing suite. `synthetic_tests.txt`: **83 passed**. GUIDE, DESIGN, this report, schemas, examples and `evidence_manifest.json` are delivered. One local commit, no push; acceptance is handed off separately. |

Evidence names above are under `docs/shade_map/evidence/`. Unit tests are in
`tests/test_shade_map.py`; the bounded real campaign is reproducible from
`tests/shade_map_campaign.py`. The final candidate SHA cannot be embedded in a
file that is part of that same commit; obtain it from the handoff or
`git rev-parse HEAD` after the sole local commit.

## Resources and preserved failures

[Resource ledger](evidence/resource_ledger.json):

| Measure | Recorded amount | Frozen development ceiling |
| --- | --- | --- |
| Charged real-job wall time | **2096.71 s (34.95 min)** | 3600 s / 60 min |
| Largest recorded sampled process tree RSS | **5.609 GiB** | 12 GiB |
| Sampled campaign artifact peak | **0.635 GiB** | 20 GiB |

Task code, schemas, docs and evidence occupy only a few additional MiB. Temporary
portability copies and compression files are small relative to the remaining
artifact allowance. RSS/disk values are samples, not OS-enforced maximums.

The wall charge includes 300 conservative seconds for preliminary metadata work,
source-list readback and the final listing audit, plus the failed validation
attempt below. No budget was extended. Successful real compute jobs all used
new output names and isolated new cache namespaces. The original read-only
planning attempt finished, but restricted process enumeration prevented its
peak-memory measurement. It was repeated with working monitoring before any
horizon computation. This initial measurement gap is why **F1-13 remains
NOT VERIFIED**, despite the passing write-scope audit and the measured jobs
remaining within the frozen limits.

A validation-harness dispatch bug made `verify-internal` match a generic
`verify-` branch and recursively launch monitors. It never reached pixel
comparison. Only this task's process tree was stopped; its recorded memory was
5.609 GiB, still below 12 GiB. Its 556.03 s runtime plus 5 conservative
seconds is charged. The failure is preserved in
`verification_harness_recursion.json`; dispatch was corrected and protected by
`test_campaign_internal_dispatch_is_not_recursive`. The corrected complete
Cheung Chau verification took 106.46 s and passed. No failed evidence was erased
and no numerical criterion was weakened.

The first unqualified `pytest` collection also discovered historical review
checkouts under `outputs/` and reported duplicate test modules. That log is
preserved as `full_tests_initial_collection_error.txt`. The full current suite
was run explicitly as `pytest tests`, with **189 passing tests**. Protected
historical listings remained unchanged, including through that collection.

## Recorded commands and handoff

All commands were run from the repository root in the existing `.venv`.
These are the recorded campaign actions, not instructions to overwrite or reset
its now-existing namespaces. Independent acceptance must use fresh names and its
own frozen 45-minute budget.

```sh
.venv/bin/python -m pytest tests -q --disable-warnings
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py setup
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py gate
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py run-a
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py verify-a
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py run-b
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py interrupt-compute
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py interrupt-publication
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py verify-b
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py verify-instant
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py finish
PYTHONPATH=. .venv/bin/python tests/shade_map_campaign.py audit
```

Inspect the staged diff and verify it contains only new F1 task files before
committing. Existing user changes, including `.gitignore` and the uncommitted
planner/presentation/web/coastline files, remain outside the commit. The local
commit's full SHA is reported to the user; nothing is pushed. This development
report does not declare F1.0 accepted.

## Repair 1 — 2026-11-04

The rejected candidate was `eb605f52d119a00fa30b8c5d0f44a725f9d88043`.
This repair started on `feature` at
`439e06489efc0ee9d6f78995f1c49c3fcadd1e7a`, containing that candidate and the
frozen B2.0 documents. The contract checksum was verified before editing and
remains `dd19ec249f7b0b56d71c3720d7fbc1f266454ea4c48100a4aeaa1cc2b81ed690`.
The independent report and its output tree are preserved unchanged, including
the reviewer's empty orphan `.partial` failure folder. All preceding sections
and original evidence remain historical records. This section assesses the
repaired candidate; independent re-acceptance is still required.

### Defects and fixes

- **D1 / F1-02:** output ownership checks previously stopped at the repository
  boundary, and did not explicitly protect an external DSM catalogue. A shared
  validator now resolves symlinks and rejects publication inside `data/`, equal
  to or inside the configured/provider catalogues or their backing source-file
  directories, and beneath an existing foreign ancestor anywhere. It checks
  ownership markers rather than trusting their presence. The validation runs
  before adapter planning, source-view creation, publication or prune writes;
  the CLI returns 2 with `invalid input: output_root: ...`.
- **D2 / F1-11:** the complete-run shortcut previously skipped partial cleanup.
  All run paths now recover partial directories under the name lock. A verified
  final frame is retained while the orphan is removed. A missing or damaged
  final is marked pending durably before its recovery cue is removed, then
  restored through normal engine/publication resume. Final verification refuses
  any remaining `.partial` entry, including an empty directory.

The only production changes are in F's configuration, planning and runner
modules. There is no publication algorithm, engine, adapter, policy or source
implementation change. GUIDE and DESIGN describe the corrected boundaries and
recovery behaviour.

`tests/test_shade_map.py` adds **33 cases**: 27 combinations of nine forbidden
locations with `plan`, `run` and `prune`, plus six complete-run recovery cases.
The location cases include the reviewer's DSM-catalogue and external foreign
parent reproductions, symlinked DSM/foreign/data paths, a provider catalogue,
symlinked backing sources and a malformed ownership marker. They assert the
exit code and message, unchanged file metadata and directory listings, and no
adapter call. Recovery covers empty/nonempty orphans beside verified, missing
and damaged finals; verified final files retain their hashes and timestamps.
The final full suite, explicitly scoped as `pytest tests`, passed **222 tests**
(54.09 s pytest time; 57.67 s charged monitored job time). The earlier 217-test
run is retained too. See [full test log](evidence/repair_1/full_tests.txt).

### Fresh campaign and numerical checks

All new evidence is indexed under [repair_1](evidence/repair_1/evidence_manifest.json).
The immutable [frozen campaign](evidence/repair_1/frozen_campaign.json) records
the original geometries and times before real planning. Publication is under
`outputs/shade_map_f1_repair_1_20261104/`, diagnostics under
`outputs/shade_map_f1_repair_1_diagnostics_20261104/`, and caches use the new
prefix `f1_repair_1_20261104_`. Names are `f1r1_a`, `f1r1_b`, `f1r1_instant`,
`f1r1_kill_compute` and `f1r1_kill_publish`; the independent reference has its
own cold cache. No original development or review output was reused as writable
work space.

- **(a):** the pre-computation source gate matched all 21 historical tile names,
  with a cold cache. `f1r1_a` produced exactly 65 frames, 07:10–17:50 HKT.
  Every cell, VRT and full image was checked against the logical engine windows;
  every shade/quality pixel also equals the accepted historical Cheung Chau run.
  Surface values equal direct DSM classes, summaries match the rasters, and all
  copied VRTs open identically.
- **(b):** the original fractional WGS84 corners resolve to
  `[820240,808390,820260.5,808410.5]`, 41 × 41 pixels across four clipped cells,
  including one no-DSM cell. The window produced 12:30, 12:40 and 12:50. The
  instant request kept 12:30 and dropped 00:00 as `outside daylight`.
  Independent V1 custom-bounds references computed six directions with zero
  reuse in a separate cold cache. All four published frames match them, with
  no-DSM shade/quality/surface values 255/1/255.
- **Original raster hashes:** every published GeoTIFF has the same relative
  path and SHA-256 as its corresponding original development file: **975** for
  (a), **45** for the window and **15** for the instant run, **1,035 total**.
  See `a_original_raster_hashes.json`, `b_original_raster_hashes.json` and
  `instant_original_raster_hashes.json` in `evidence/repair_1/`.
- **(c):** real SIGKILL terminated one run during computation and one during
  publication. Each resumed run has all **57 frame-file hashes** equal to the
  uninterrupted window run. The computation case retained its completed task;
  the publication case retained all eight completed V2 tasks and the first
  frame's 19 files with unchanged hashes and modification times. Interrupted
  publication was rebuilt, and no partial folder survived. A real concurrent
  CLI was refused with exit 2; incomplete prune was refused in both cases.
- **Complete-run orphan and prune:** a new empty `1230.partial` beside a verified
  real frame was removed by a verify-only rerun. Dry-run prune, confirmed prune
  and a subsequent verify-only run passed with zero computed batches. A real
  same-name/config conflict returned 2 without writes. For these verification
  calls only, the machine DSM path used the existing raw request-local source
  view; the frozen configs and source identity were unchanged.

The campaign harness uses exact action dispatch; there is no prefix-based
recursive dispatch. It changes no engine journal or task state. Its interruption
controller captures only its own processes, freezes them to record the observed
phase, and delivers SIGKILL. The measured ledger retains both intentional
return-code -9 events and the concurrent-refusal evidence.

### Resource and write-scope ledger

[Resource ledger](evidence/repair_1/resource_ledger.json) contains **21 monitored
jobs**, including every read-only plan, source gate, both full-suite runs,
computation, independent references, verification, interruption/resume and the
protected-file audit. Every job has a process-tree RSS peak, per-process RSS
peaks, sample count, wall time, artifact sample and captured stdout/stderr;
`complete_monitoring` is true and there are no monitoring failures. Values are
sampled measurements, not OS-enforced maxima. The watchdog stops before the
remaining time, memory or disk ceiling.

| Measure | Repair result | Allowance |
| --- | --- | --- |
| Conservatively charged repair wall time | **1435.23 s (23.92 min)** | 1500 s / 25 min |
| Previous development charge, preserved | **2096.71 s (34.95 min)** | Included in total below |
| Cumulative development charge | **3531.94 s (58.87 min)** | 3600 s / 60 min |
| Largest repair process-tree RSS | **0.8944 GiB** | 12 GiB |
| Sampled repair artifact peak during jobs | **0.6645 GiB** | 20 GiB |
| Final artifact inventory including text evidence | **0.6698 GiB** | 20 GiB |

The final evidence index additionally records artifact bytes after copying text
logs/listings and writing this report; these small bookkeeping artifacts also
remain within 20 GiB. No additional real-DSM job is needed after the audit.
The original development process whose planning RSS was not captured remains
unmeasured historically; its original NOT VERIFIED statement above is preserved.
The current candidate has a fresh, fully monitored replay as requested, rather
than an inferred measurement for that old process.

The before/after audit covers **39,612 protected files**, with zero changes,
missing files or unexpected additions. It includes raw data, existing processed
namespaces, all pre-existing outputs (including review checkouts), presentations
and planner files. `protected_before.json` is the original pre-repair listing;
`protected_after.json` records its comparison. The review report checksum is
unchanged. The ten engine files still equal `356f611d7b775ce31006904b80ca31d3c1c484b2`,
and the adapter still equals `f5f24acc4163aa1353534d5db5a5dbe30faf0dae`.
Environment, dependency-lock checksums, selected DSM input hashes and F source
hashes are in [traceability](evidence/repair_1/traceability.json). No sea, V3,
downloads, web work, push or other region was used.

### Repaired candidate matrix

PASS is developer verification for this repair candidate. It does not declare
independent acceptance or observational accuracy. Evidence names below are under
`docs/shade_map/evidence/repair_1/` unless explicitly identified as original.
The original schema-rule evidence is retained and its tests rerun unchanged.

| ID | Status | Repair evidence and checks |
| --- | --- | --- |
| F1-01 | PASS | `start.json`, `traceability.json`, protected audit; exact start/branch/contract, engine and adapter checks. Empty diff from repair start for `src/`, adapter, prompts and `config/v3/`. Only F repair files enter the sole local commit; full SHA is provided in the handoff. |
| F1-02 | PASS | `full_tests.txt`; original schema walker covers all 99 constraints and identity tests remain passing. New 27 location/action cases reject both D1 reproductions, resolved symlink paths, provider/backing-source paths and foreign parents before any write, with exit 2 and the required key prefix. |
| F1-03 | PASS | `full_tests.txt`; unchanged corner CLI tests cover both CRSs, coordinate/order/equality/non-finite/range and projected-order checks with exit 2 and unchanged listings. |
| F1-04 | PASS | `full_tests.txt`; unchanged engine-equal daylight tests include both solstices and three dates; windows, inclusive dates/end, invalid offsets/seconds/duplicates and drops pass. Fresh instant plan records the night drop. |
| F1-05 | PASS | `full_tests.txt`, `jobs/a_plan.stdout.txt`, `jobs/b_plan.stdout.txt`, `jobs/instant_plan.stdout.txt`; three direct-adapter equivalences, schema/estimate checks, source-view-only writes, shifted-origin rejection and four existing-run statuses remain passing. |
| F1-06 | PASS | `full_tests.txt`; raw registry and test provider with distinct surface classes still use the identical publication path. No production provider change. |
| F1-07 | PASS | `a_pixel_verification.json`, `b_pixel_verification.json`, `instant_pixel_verification.json`; every frame/cell/layer, clipped and missing cells, raster format, path rules and copied VRT portability pass. |
| F1-08 | PASS | Same three pixel records; every cell/VRT/full-image array and transform equals the logical engine window, and surface equals direct DSM classes. The three original-raster hash records additionally prove all 1,035 files unchanged. |
| F1-09 | PASS | `cheung_chau_source_gate.json`, `a_pixel_verification.json`; 21 sources checked before compute, exactly 65 frames and every shade/quality pixel equal to the accepted historical reference. |
| F1-10 | PASS | `frozen_campaign.json`, `independent_v1_reference.json`, both sparse pixel records; fractional four-cell rectangle, six cold independent directions, missing-cell 255/1/255 and night drop. |
| F1-11 | PASS | `kill_compute_resume.json`, `kill_publish_resume.json`, ledger SIGKILL evidence; 57 hashes match in each case, completed tasks/first frame retained, concurrent refusal and no partials. `partial_and_prune.json` and six new synthetic cases cover D2 even when the manifest was complete. Real config conflict writes nothing. |
| F1-12 | PASS | All pixel records reconstruct schemas, hashes, counts/CSV and whole-class fractions; both `*_incomplete.json` records show prune refusal. `partial_and_prune.json` records dry-run/deletion and verify-only rerun; complete verification also refuses any partial. |
| F1-13 | PASS | `protected_before.json`, `protected_after.json`, `resource_ledger.json`; 39,612 protected files unchanged, only authorized fresh runs, every new planning/compute/verification process monitored, repair 23.92 min and cumulative 58.87 min within the unchanged ceilings. The historical measurement gap is preserved explicitly. |
| F1-14 | PASS | `full_tests.txt`: 222 passed; GUIDE, DESIGN, this appended report and `evidence_manifest.json`. Existing schemas/examples and original evidence retained. One local repair commit, full SHA in handoff, no push; independent re-acceptance remains required. |

### Repair commands and handoff

All actions ran from the repository root using the existing `.venv`. Each action
below was recorded once, in order, with `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`; children also used the new diagnostic Numba cache.
These names are now occupied and must not be reused for independent acceptance.

```text
.venv/bin/python tests/shade_map_repair_campaign.py setup
.venv/bin/python tests/shade_map_repair_campaign.py tests
.venv/bin/python tests/shade_map_repair_campaign.py plans
.venv/bin/python tests/shade_map_repair_campaign.py a
.venv/bin/python tests/shade_map_repair_campaign.py b
.venv/bin/python tests/shade_map_repair_campaign.py verify
.venv/bin/python tests/shade_map_repair_campaign.py kill_compute
.venv/bin/python tests/shade_map_repair_campaign.py kill_publish
.venv/bin/python tests/shade_map_repair_campaign.py finish
.venv/bin/python tests/shade_map_repair_campaign.py tests-final
.venv/bin/python tests/shade_map_repair_campaign.py audit
```

The ledger records every child command, including the actual
`.venv/bin/python -m pytest tests ...` invocations. Run manifests record the
pre-commit tool HEAD with its dirty flag; the repair evidence index binds the
tested F source bytes to this local commit. The staged diff is inspected before
the one repair commit. No review report, original evidence, output/cache,
planner or unrelated user file is staged. The full new SHA is reported to the
user for targeted independent re-acceptance; nothing is pushed.
