# Package B2.2 — static pre-check of `7707c51`

Written by the planning conversation (Claude) on 2026-11-06, about 17:40 HKT. **This is not independent acceptance.** No computation was run. Checks are git diffs, file and evidence reads, and metadata listings compared with the baseline `claude/reviews/B2_2_BASELINE_20261105.md` (taken 2026-11-05 17:13:40 HKT; Codex had started at 17:12:26, but nothing in the protected trees had changed since the planning commit).

## Candidate

- **Commit:** `7707c511a44233d05914604c4741aefb86701d7a`, parent `5b1da9be4246acac53b0488c3587df7884941108`, committed 2026-11-06 17:08:44 +08:00 by Zhengtao0719. Message: "Implement DSM-only fill-all sea policy B2.2". Single local commit; no remote branch contains it. HEAD equals the candidate.
- **Contract:** `SW-B2.2` SHA-256 `12d79865…f2a9`. The contract, both B2.2 prompts and `docs/OUTPUT_CODES.md` are unchanged at the candidate.
- **Developer self-assessment** (`docs/sea2/DEVELOPMENT_REPORT_B2_2.md`): 15 PASS; B2-22 NOT VERIFIED by design (rebuild left to acceptance). `pytest tests`: 275 passed (`docs/sea2/evidence/b2_2/pytest-resume.txt`). View ID `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1`.

## Static checks (verified by Claude)

| Check | Result |
| --- | --- |
| Exactly one commit on top of `5b1da9b`; HEAD = candidate; working tree dirty only with the baseline planner files | PASS |
| Candidate's own changes: 105 files, +26,825 / −1,328, no binaries. All paths in the allowed list: `tools/sea2/` (12 modified, `fill_impact.py` added, `void_impact.py` deleted); `config/schema/fill_impact.schema.json` added, `void_impact.schema.json` deleted, `shade_map_region.schema.json` modified; `docs/sea2/{POLICY,GUIDE,DESIGN}.md` modified, `DEVELOPMENT_REPORT_B2_2.md` added; 76 files added under `docs/sea2/evidence/b2_2/`; `tests/test_sea2_{diagnostic,rule,validation,view}.py` modified; `tools/shade_map/{sources,publication}.py`; `docs/shade_map/{GUIDE,DESIGN}.md` | PASS |
| `git diff 5b1da9b 7707c51 -- src/ tools/region_request.py` empty; the ten pinned files equal `356f611`; adapter equals `f5f24ac` | PASS |
| Cumulative F diff `35225fd..7707c51` over the design-item-8 paths: 7 files, exactly the allowed changes. `sources.py`: import of `SeaSource` plus one registry entry `'sea-2.2'`. `publication.py`: only the surface allowlist (line 141) `[0,1,255]` → `[0,1,2,3,4,255]`. Region schema `dsm_source` enum `raw`/`sea-2.2`. Machine schema optional `sea_profile` (default `hk_cedd_2020`). `machine.example.json` shows it. F GUIDE: one 16-line section. F DESIGN: the surface-code paragraph only, referring to `OUTPUT_CODES.md`. F tests and `config/regions/` unchanged | PASS |
| Records unchanged `5b1da9b..7707c51`: `tools/sea_view/`, `docs/sea/`, `tests/test_sea_masks.py`, `docs/sea2/DEVELOPMENT_REPORT.md`, B2.0 evidence outside `b2_2/`, `docs/prompts/`, `docs/planning/`, `docs/OUTPUT_CODES.md`, `config/regions/`, sea profile and its schema | PASS |
| No `sea-2.0`, `void_impact`, `void-impact` or `voidfill` reference left in `tools/`, `config/`, `tests/`; no `xfail` in test sources; six-code publication test present (`tests/test_sea2_view.py:170`) | PASS |
| Coastline/iB5000/pyogrio/shapely references only in `tools/sea2/validate_ib5000.py` and `validation_worker.py` | PASS |
| View manifest `build_code_sha256` (8 files) equals the candidate's blobs; the build's static `tools/sea2` imports equal `BUILD_MODULES`; policy `SW-SEA-POLICY-2.2`; manifest SHA-256 `1a7a43bd…1c52` equals the finalization record. One view folder only | PASS |
| Write scope against the baseline: 160 baseline units, 0 missing, 0 digest changes, and no entry newer than the baseline inside any pre-existing unit. 17 new units, all allowed: `dsm_views/sea_fill_v2_2/`; `shade_v1/sea_fill_v2_2_8ee51b017411`, `sea2_2_fill_impact_51d38f2c03c2`, `sea2_2_fill_impact_6f979a31d9f6`; four new `outputs/region_views/<key>/`; `outputs/sea2_2_development/`, `sea2_2_diagnostic_work/`, `sea2_2_validation/`; three new `outputs/shade_map_work/sea2_2_*-<id12>/` and their three new lock files. New: 21,735 files + 1,771 symlinks = 23,506 (equals the developer's count), 5.32 GB | PASS |
| Coastline: SHA-256 of all 423 files identical. Planner files: all 238 SHA-256 identical; `.gitignore` diff identical. `presentations/` units unchanged (no WK4 activity) | PASS |
| Raw `run_id`: `c196a09a…` and `e608af7f…` equal at the candidate and at `35225fd`; Central reference `83cfba55…` equals a candidate raw plan (`raw-plan-identity.json`) | PASS (developer evidence, not re-run) |
| Ledger (`resources.jsonl`, 31 measured invocations, `mach_continuous_time`, `caffeinate -dims`): one build 34.14 / 60 min; real-DSM 41.54 / 60 (includes two failed readbacks, 0.43 min); validation 15.11 / 30; peak RSS 2.36 / 12 GiB; peak new artifacts 5.17 / 30 GiB | PASS (developer figures) |
| POLICY, GUIDE and DESIGN refer to `docs/OUTPUT_CODES.md`; POLICY states all twelve limitations required by design item 11 | PASS |
| Tools environment record: Python 3.12.5 at `~/venvs/shade_watch_tools`, five wheels with URLs and SHA-256, versions equal the lock | PASS on record; not inspectable from the linked shell |

## Findings for the independent reviewer

1. **Post-build manifest finalization (decisive for B2-22).** The raster build ran with a `build.py` whose `BUILD_MODULES` lacked `provider.py` (view ID `2109e9d9…`, `build.py` `36b4f121…`). Before any regional plan (pointer finalized 08:20 UTC; first region view 08:25 UTC), a campaign step added `provider.py` to the list and rewrote the manifest and pointer as `8ee51b01…`, carrying the rasters forward. All other module hashes are identical before and after (`metadata-finalization.json`). The original `build.py` is not preserved, so "only the list changed" is the developer's statement. The committed `build` command never produced `8ee51b01…` from start to finish in development. The independent rebuild is therefore decisive: if it does not reproduce the `view_id` and every file hash, B2-22 fails.
2. **B2-17, cross-permission identity.** The only real build ran under the coastline blackout, and the acceptance rebuild also runs under blackout. Equality across permission states rests on the code audit, a synthetic comparison under both permissions, and a restored-mode readback of existing outputs. The reviewer judges whether that meets "the same view_id and the same outputs result".
3. **F provenance and the blackout.** `tools/shade_map/runner.py:36` runs `git status --porcelain`, which may try to list `data/raw/coastline/` (it holds an untracked README) during the blackout. This lists a directory only and opens no map data. It is existing accepted F1.0 behaviour. From the reviewer's worktree it does not touch the main checkout.
4. **iB5000 conventions not fixed by the contract.** The coverage proxy is the joint LAF/SEF bounding box. The northern listing is the northernmost 10 km of the raw catalogue plus the northern domain margin. These are report-only and do not enter the reviewer's 0.5% cross-check (false water, missed sea by class, Victoria Harbour share).
5. **Coastline modes.** The developer reports original `0o755`, blackout `0o0`, restored `0o755`. The linked shell shows masked modes (dirs 700, files 600) both before and after, so mode restoration can only be confirmed on the Mac.
6. **Tools environment.** pip was removed after installation (`bootstrap_pip_removed: true`). Check packages through dist-info or `importlib.metadata`, not `pip list`.
7. **Failed readbacks.** `audit-five_class` and `audit-cheung_chau` first exited 1 (V2 batch IDs read from the wrong field). The corrected readbacks passed on the same outputs; the attempts remain in the ledger and the `*-attempt1.txt` logs.
8. **Reported results (developer, not verified here).**
   - Cheung Chau, 65 frames, raw-255 observed land: raw quality 2 → sunlit 65,955,112 pixel-frames; quality 2 → 255 (now quality 3) 822,700; quality 3 → 255 72,041; nothing became shaded.
   - The distant-obstruction threshold rose in 3 of 4 Cheung Chau tiles (about 6.14° → 6.21°). No sunlit → not-sunlit transition occurred at the 10-minute frames.
   - Remaining 255 is all quality 3: Cheung Chau 11,883,324 pixel-frames, Central 1,023,106, five-class region 0. Quality 1 and 2 are zero in all 71 frames.
   - Five-class region targets: classes 0–4 = 306,318 / 1,479,578 / 1,114,582 / 14,104 / 685,418.
   - Ray checks: at 08:00, 12:30 and 16:00, 1,080 Cheung Chau water samples (120 near tall structures), 440 class-3/4 and 240 observed-near-fill samples, zero mismatches (tolerance 0.0001°).
9. **Territory view and statistics groups.** Classes 0–4 = 4,384,416,867 / 1,453,438,606 / 1,315,054,618 / 93,109,991 / 5,285,979,918 pixels. There are 7,128 cells: 3,310 supplied (1,656 rewritten, 1,654 links) and 3,818 synthetic. Class 4 includes open sea farther than 1 km from any low shore (iB5000 "missed sea, class 4" for the territory: 3,629,051,495). The Water group therefore covers near-shore sea only, and "Other" is large. This is a grouping effect of the frozen rule; shade is unaffected. Relevant later for the four-region measurement and for reporting.

## Developer timings for budgeting (real-DSM unless stated)

Plans 0.5–1.6 min each; Cheung Chau 65-frame run 11.34 min; Central 3-frame run 1.25 min; five-class 3-frame run 0.91 min; fill-impact 1.75 min (Cheung Chau, 3 frames) and 2.08 min (five-class); full view readback 14.68 min; build 34.14 min; validation 15.11 min.

## Outcome

Scope and boundaries are clean. The evidence is consistent with the self-assessment. **The candidate can go to independent acceptance.** The decisive item is the rebuild's reproducibility (finding 1).

## Appendix: handoff message for the independent-acceptance conversation

```
Independent acceptance of Package B2.2 (SW-SEA-POLICY-2.2) for shade_watch_hk.

Project: /Volumes/My Passport for Mac/Projects/shade_watch_hk (branch feature)
TARGET_COMMIT: 7707c511a44233d05914604c4741aefb86701d7a
Expected parent: 5b1da9be4246acac53b0488c3587df7884941108 (B2.2 planning commit; contains 5744e23 and the contract)

Follow docs/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT_B2_2.md exactly. Before starting, verify these SHA-256 values at TARGET_COMMIT:
- docs/prompts/B2/CONTRACT_B2_2.md                       12d79865dda53ce1539560f4d79c047d3c80fd3fd974e4b9f643bf409580f2a9
- docs/prompts/B2/INDEPENDENT_ACCEPTANCE_PROMPT_B2_2.md  4235112259256f5af132f649e9a423edadd28d87bcc3166e1bb576f33acf0d00
- docs/OUTPUT_CODES.md                                   f103c913d6f7f72486023ba8a27dd8c7301969537e252d0fe9369701ce443f93
Stop and report if any differs.

Developer handoff (claims, not evidence of acceptance):
- Report: docs/sea2/DEVELOPMENT_REPORT_B2_2.md; evidence index: docs/sea2/evidence/b2_2/manifest.json
- View: data/processed/dsm_views/sea_fill_v2_2/8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1/ (read-only)
- Tools environment: ~/venvs/shade_watch_tools (record: docs/sea2/evidence/b2_2/tools-environment.json)
- Self-assessment: 15 PASS; B2-22 NOT VERIFIED pending your rebuild; pytest 275 passed.

Planner pre-check notes (static only; they do not change the contract, the prompt, or any criterion):
1. Manifest finalization after the raster build. The build ran with a build.py whose BUILD_MODULES lacked provider.py (view 2109e9d9..., build.py 36b4f121...). Before any regional plan, the developer added provider.py to the list and rewrote the manifest and pointer as 8ee51b01..., carrying the rasters forward (docs/sea2/evidence/b2_2/metadata-finalization.json). The committed build command never produced 8ee51b01... end to end. Your rebuild must reproduce the view_id and every file hash; there is no tolerance.
2. B2-17: the developer's only real build ran under the coastline blackout. Cross-permission equality rests on the code audit, a synthetic two-permission comparison and a restored-mode readback. Judge whether this meets the criterion.
3. tools/shade_map/runner.py:36 runs `git status --porcelain`, which may try to list data/raw/coastline/ during a blackout of the main checkout. Directory listing only; existing accepted F1.0 behaviour.
4. The iB5000 report uses two conventions the contract does not define: the joint LAF/SEF bounding box as the coverage proxy, and "northernmost 10 km of the raw catalogue plus the northern domain margin" for the northern listing. Report-only.
5. Record coastline modes on the Mac itself. The developer reports original 0o755, blackout 0o0, restored 0o755.
6. pip was removed from the tools environment after installation; verify the five packages through dist-info or importlib.metadata.
7. Developer timings (real-DSM) to plan your 45-minute budget: plans 0.5-1.6 min each; Cheung Chau 65 frames 11.3 min; 3-frame runs about 1-1.3 min; fill-impact about 2 min; full view readback 14.7 min. Build 34.1 min (your rebuild has its own 60-minute cap).
8. docs/planning/ predates the planning commit; where it says a commit is pending, that commit is 5b1da9b.

Write the report to docs/sea2/INDEPENDENT_ACCEPTANCE_B2_2_7707c511a442.md and do not commit it. Do not fix defects, push, merge, or start exception zones, territory runs, reclassification of quality 3/4, or V3.
```
