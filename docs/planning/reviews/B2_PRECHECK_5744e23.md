# Package B2.0 — static pre-check of `5744e23`

Written by the planning conversation (Claude) on 2026-11-05, about 16:30 HKT. **This is not independent acceptance.** No computation was run; checks are git diffs, file reads, and metadata listings compared with a baseline taken on 2026-11-04 at about 17:35 HKT, before development wrote anything.

## Candidate

- **Commit:** `5744e2301eea34f8bae05b9df3e14508425b8282`, parent `05c66ab379d87868a787ae78cdecbfb918c1730e`, committed 2026-11-05 14:18 +08:00. Message: "Implement DSM-only sea surface policy B2.0". Single local commit, not pushed.
- **Contract:** `SW-B2.0` SHA-256 `b8b5473b…0e1a`; amendment `SW-B2.1` SHA-256 `18a09995…450d`. Both unchanged at the candidate.
- **Developer self-assessment:** 9 PASS, 1 FAIL (B2-08), 5 NOT VERIFIED (B2-01, B2-07, B2-10, B2-13, B2-14). `pytest tests`: 271 passed, 1 xfailed (strict; documents the B2-08 conflict).

## Static checks (verified by Claude)

| Check | Result |
| --- | --- |
| Exactly one commit on top of `05c66ab`; working-tree status identical to the baseline | PASS |
| `docs/prompts/` and `docs/planning/` unchanged | PASS |
| `git diff 05c66ab 5744e23 -- src/ tools/region_request.py` empty; ten pinned files equal `356f611`; adapter equals `f5f24ac` | PASS |
| `git diff 35225fd 05c66ab -- tools/shade_map config tests` empty (F code at the parent equals accepted F1.0) | PASS |
| F changes limited to design item 7: `sources.py` (import + one registry entry), region schema `dsm_source` enum, machine schema `sea_profile`, `config/machine.example.json`, `docs/shade_map/GUIDE.md` (+22 lines). `config.py`, `planning.py`, `publication.py`, `runner.py`, `common.py` untouched | PASS |
| B1.0 (`tools/sea_view/`, `docs/sea/`, `tests/test_sea_masks.py`) and existing F tests (`tests/test_shade_map.py`, campaign files) unchanged | PASS |
| 104 files, 9,110 insertions, 2 deletions; all new files in `tools/sea2/`, `config/sea_profiles/`, `config/schema/` (2 new), `docs/sea2/` (74 evidence files), `tests/test_sea2_*.py`; no binary files | PASS |
| Runtime code (`tools/sea2/` except `validate_ib5000.py`, `validation_worker.py`) contains no coastline/iB5000/pyogrio reference | PASS |
| Write scope against the baseline: of 47,365 existing files under `data/raw`, `data/processed`, `outputs`, `presentations`, 0 changed and 0 missing (size + mtime). 14,061 new files, all in new leaves: `dsm_views/sea_fill_v2/`, `dsm_views/sea_voidfill_v2_diagnostic/`, cache namespaces `sea2_raw_20261104`, `sea_fill_v2_df707ce89852`, `sea_voidfill_v2_diagnostic_ea60db03d871`, four new `outputs/region_views/<key>/`, `outputs/sea2_f_20261104/`, `outputs/sea2_diagnostic_work/`, three new `outputs/shade_map_work/<name>-<id12>/`, and three new empty lock files in the existing `outputs/shade_map_work/.locks/` (F runner per-name locks) | PASS (subject to the reading of "existing outputs/ folders"; see decisions) |
| 447 uncommitted planner files and `data/raw/coastline/` files: SHA-256 identical to baseline; coastline readable again | PASS |

## Findings

1. **B2-08 FAIL is a contract conflict, not a developer defect.** `tools/shade_map/publication.py:141` allows surface codes `[0,1,255]` only. Design item 7 forbids publication changes, while B2-08 requires published surface layers to equal the view's five classes. The run identity does not include `publication.py` (it hashes the ten engine files, region, frames, source identity, policies and `FORMAT = 'shade-map-publication-1.0'`), so widening the allowlist would not change any raw `run_id`. Summary and frame schemas are already class-generic.
2. **Real-data coverage is vacuous for classes 2, 254 and 255.** Cheung Chau targets: `{0: 3,322,313, 1: 3,877,687}`; Central targets: `{0: 7,026,501, 1: 173,499}`. B2-09 gate (ii), the publication of 2/254, and the void-impact counterfactual (zero voids) are exercised only by synthetic fixtures. Territory view: 326 supplied cells contain 255, 56 contain 254, 787 synthetic cells contain both 2 and 254.
3. **Reservoirs appear as class 255.** The largest class-255 cells (e.g. `e842750n836000`, `e853250n826400`, almost entirely 255) lie where Plover Cove and High Island reservoirs are (inferred from coordinates, not verified). This follows the frozen rule (enclosed NoData = 255) but means reservoir surfaces count as land voids in D-009 denominators and in the 10% void trigger. Not stated in POLICY/GUIDE.
4. **`14NE15*` NoData sentinel.** These four tiles declare float32-minimum as NoData; the other 3,306 use -9999. Following the contract's literal NoData definition (non-finite or -9999), all 4 × 1,800,000 pixels are class 0. They sit in the sea west of Lamma (neighbours are mostly water), so their sea pixels are likely labelled observed surface. Disclosed in DESIGN/POLICY. Regions needing these tiles are already rejected (D-008); side effects on neighbouring classification (e.g. `14NE20B` has 26,564 class-255 pixels) are not verified.
5. **Build budget.** First build attempt: 4,300 s wall (CPU 958 s; the watchdog used uptime and missed system sleep), stopped, staging removed. Second phase: stopped attempt 1,294 s (native-centre correction) + completed build 2,215 s (36.9 min) + readback 49 s. No second complete build exists (B2-07). The view manifest records rule and library versions but no `tools/sea2` source hashes; build modules were last modified 2026-11-04 19:39 HKT, before the completed build (2026-11-05 13:23 HKT).
6. **B2-02** evidence covers build, plan, F run and void-impact under denied coastline access, with original and restored modes (493). The permission-test launcher is not committed, so "access denied" is the harness's own assertion.
7. **B2-10** marked NOT VERIFIED for lack of a map-defined Victoria Harbour denominator; all 11,010,914 NoData pixels in the Central halo became water, so any harbour subset is 100%. The contract does not define the denominator.
8. **Tools environment.** The B1.0 tools environment under `/private/tmp/shade_watch_tools_20261029` is empty; no downloads were made. B2-13 and the environment part of B2-01 cannot pass without a pinned reader environment.

## Resource figures (developer, not verified here)

Real-DSM jobs 47.13 / 60 min (Cheung Chau sea 65 frames 18.8 min; void-impact 65 frames 14.8 min; Central raw 2.3 min, sea 2.6 min). Peak RSS 1.623 GiB. Peak new artifacts 5.208 GiB.

## Outcome

Scope and boundaries are clean; the candidate cannot be ACCEPTED as is (one FAIL caused by the contract, five NOT VERIFIED).

**Decision (user, 2026-11-05 16:36–16:49 HKT; D-015, D-016).** `5744e23` is not sent to independent acceptance. It stays an unaccepted record; its evidence and outputs are read-only. The user directed that every NoData pixel be filled at 0 m, so the next step is a new contract, `SW-B2.2` (`docs/prompts/B2/CONTRACT_B2_2.md`, policy `SW-SEA-POLICY-2.2`), developed from `5744e23`'s code. The findings above are carried into it:

- finding 1: one publication allowlist change is allowed;
- findings 2 and 3: a real five-class region and a class-3 component report are added, and voids (including reservoirs) are filled;
- finding 4: the literal treatment is kept;
- finding 5: build-code hashes go in the manifest, and the build is timed with a sleep-inclusive clock;
- finding 7: the Victoria Harbour denominator is defined;
- finding 8: the tools environment download is authorized.
