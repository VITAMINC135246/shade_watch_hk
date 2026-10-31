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
