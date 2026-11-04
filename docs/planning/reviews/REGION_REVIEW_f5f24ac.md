# Region adapter review: commit f5f24ac (SW-RGN-AC-1.0 + 1.1)

- **Reviewer:** planning conversation (Claude), 2026-10-31 ~17:30 HKT.
- **Candidate:** `f5f24acc4163aa1353534d5db5a5dbe30faf0dae` on `feature`, parent `86dbee6`, committed 2026-10-31 16:34 +08:00. Message: "Amend region adapter for sparse coverage, daylight dates and source views".
- **Method:** static review of the commit plus Codex's committed evidence. Claude did not run the project environment; run-dependent items rely on Codex evidence. No independent acceptance is required (no science change; review by the planning conversation per the amendment).

## Static checks (verified by Claude)

- `git diff 356f611 f5f24ac -- src/` is empty. All ten pinned engine files have identical blob ids to `356f611`.
- Contract hashes on disk are unchanged: 1.0 `3bc918a9…a579`, 1.1 `e80e5da0…9ea0`.
- The commit contains 34 files: `tools/region_request.py`, `tests/test_region_request_v1_1.py`, `docs/region/{DESIGN,GUIDE,DEVELOPMENT_REPORT}.md`, `docs/region/evidence/v1_1/*` (text, JSON, XML and .py only). No rasters, views or caches. The existing `tests/test_region_request.py` is not modified.
- Planner and user files (`docs/prompts/`, `docs/ui/`, `tools/wsl2_smoke/`, `web/console/`, `data/raw/coastline/`, `presentations/`, `.gitignore`, `docs/prompts/README.md`) remain uncommitted.
- The working tree equals the commit for the adapter files.
- Ledger (committed): `COMPLETED; R11 FULL-RAW REFERENCE NOT VERIFIED`; cumulative 739.0 s of 1,200 s; peak tree RSS 689,487,872 bytes of 8 GiB.

## Verdicts

| ID | Verdict | Basis |
| --- | --- | --- |
| R01 | PASS (verified by Claude) | See static checks. |
| R02 | PASS (Codex evidence) | Existing validation tests unchanged; new empty/duplicate-date and frame-limit errors. |
| R03 | PASS (Codex evidence) | Five points bit-identical to the V1 transformer; versions in `real-plan.json`. |
| R04 | PASS (Codex evidence) | Hand-written custom-bounds key/grid equality; dates-mode equality via R10. |
| R05 | PASS (Codex evidence) | Exact occupancy and disjointness; sparse fixture uses fewer, larger parts; forced split keeps four distinct horizon tasks. |
| R06 | PASS (via R12) | Previously NOT VERIFIED; now closed by the R12 cold run with a complete ledger. |
| R07 | PASS | `GUIDE.md` examples use `--auto-source-view`; the guide warns that the full raw catalogue hashes about 26 GB per plan and is rejected because of the four `14NE15*` tiles. Both commands exit 0 (`guide-checks.json`). |
| R08 | PASS (Codex evidence) | 106 passed (73 + 20 + 6 + 7); `full-tests.txt`. One local commit, no push. |
| R09 | PASS (Codex evidence) | `test_no_dsm_interior_edge_and_added_tile`, `test_residual_far_gap_is_kept_and_readable`, `test_multi_batch_engine_readback_and_one_shot_admission`. |
| R10 | PASS (Codex evidence) | `test_dates_key_and_over_512_split_at_dates`, `test_date_cli_and_batch_name_provenance`. |
| R11 | NOT VERIFIED (blocked by D-008) | The literal criterion needs a plan against the full 3,310-file raw catalogue, which the unchanged engine rejects. Supporting evidence: against a 75-file compatible control catalogue (union of three halo views), auto views of 21/24/30 tiles give equal spatial and V1 plan keys for coastal, inland and tile-corner regions; auto selection also matches selection from all 3,310 raw headers. A needed `14NE15*` dependency raises a clear error. The criterion is not weakened. It can close only after the shifted-origin ingestion policy exists. |
| R12 | PASS (Codex evidence) | Two instants with distinct cache directions (130°, 215°); fresh V1 cache computed 4, reused 0; Shade/Quality/transform equal. |

## Overall

- The adapter at `f5f24ac` is usable as the planning layer for package F. F's starting SHA should be `f5f24ac` or a later commit that contains it.
- R11 remains open as a contract-level limitation caused by D-008, not as a code defect. The substitute evidence is sufficient for F to rely on request-local source views.
- F must keep the `14NE15*` guard: regions whose 1 km halo needs those tiles are rejected with a clear message until an ingestion policy is decided.
