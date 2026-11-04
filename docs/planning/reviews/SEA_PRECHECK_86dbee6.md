# Package B (sea-surface support) — static pre-check of `86dbee6`

Written by the planning conversation (Claude) on 2026-10-30, about 14:25 HKT. **This is not the independent acceptance.** It confirms only that the candidate is in a fit state to hand to an independent reviewer.

## Candidate

- **Commit:** `86dbee663ccec8edcca7f123542a345fa13ca18b`.
- **Parent:** `374a70d`. The branch is `feature`.
- **Message:** "Add scoped sea-support DSM views and development evidence".
- **Committed:** 2026-10-30 11:06 +08:00.
- **Contract:** `docs/prompts/sea/ACCEPTANCE_CONTRACT.md`. Its SHA-256 on disk is `9742e8a34df90c6f5139c3823f53d363cb0fedee9e8905823ba3b7bfb3b66a27`, which equals the frozen value. The file is untracked, so it is **not inside the commit**.

## Static checks

| Check | Result | How |
| --- | --- | --- |
| `src/` unchanged against accepted `356f611` | PASS | `git diff --stat 356f611 86dbee6 -- src/` is empty |
| The ten pinned engine files are byte-identical to `356f611` | PASS | Blob ids compared for `v1.py`, `v1_cache.py`, `horizon.py`, `solar.py`, `spatial.py`, `shade_watch.py`, `v2.py`, `v2_worker.py`, `v2_runner.py`, `v2_state.py` |
| No derived rasters, views or caches committed | PASS | See "What the commit contains" below |
| Planner and user files not staged or committed | PASS | See "Planner and user files" below |
| Existing tests unchanged | PASS (static) | The only test file in the commit is the new `tests/test_sea_masks.py` |
| Development report present | PASS | `docs/sea/DEVELOPMENT_REPORT.md` |

**What the commit contains.** 61 files: `docs/sea/{DESIGN,DEVELOPMENT_REPORT,GUIDE,POLICY}.md`, `docs/sea/evidence/*` (JSON and TXT only), `requirements.tools.lock.txt`, `tests/test_sea_masks.py` and `tools/sea_view/*.py`.

**Planner and user files.** These are still untracked or modified in the working tree and are outside the commit:

- `docs/prompts/{region,runner,sea}/`
- `docs/ui/`
- `docs/v3/WSL2_SMOKE_TEST.md`
- `tools/wsl2_smoke/`
- `data/raw/coastline/`
- `.gitignore`
- `docs/prompts/README.md`
- `presentations/`

## Developer self-assessment

S01–S14 are all self-assessed PASS. The report lists no FAIL and no NOT VERIFIED item. It calls itself a "development candidate only" and says independent acceptance is required.

These are the developer's headline numbers. They are claims, not verified here:

- **Tests:** 99 passed (73 original, 20 from package A, 6 from package B).
- **Territory scan (S06):** n = 2,989,697 and p50 = 1.369 m, inside [1.30, 1.90]. The scan took 537 s.
- **Views:**
  - Cheung Chau `a3c26a13…74e`: 21 supplied tiles plus 15 synthetic.
  - Central `6dc631fd…cc`: 35 supplied tiles plus 1 synthetic.
- **Cheung Chau land regression (S08), all 65 instants:**
  - zero shaded → sunlit;
  - zero Quality-1-land changes;
  - zero sunlit losses;
  - thresholds identical.
- **Former Quality 2 land pixels that became sunlit, Cheung Chau:**

  | Time (HKT) | Became sunlit | Still 255 |
  | --- | --- | --- |
  | 08:30 | 659,506 / 740,947 (89.0%) | — |
  | 12:30 | 1,546,757 / 1,762,131 (87.8%) | 215,346 |
  | 16:30 | 460,255 / 618,658 (74.4%) | — |

  These figures come from `docs/sea/evidence/cheung_chau-comparison.json`.
- **Resources:**
  - real-job time: 1,370 s of 3,600;
  - peak RSS: about 1.68 GB of 12 GiB.

## Items the independent reviewer should press on

1. **S03 used the explained-difference route.** Against the planning reference:
   - NoData in LAF differs by −7.20%;
   - valid DSM in sea differs by +3.24%.

   The developer attributes this to PIL pixel-edge burning versus rasterio pixel centres. Sixty stratified samples agree with Shapely, and the maximum sampled distance to the LAF boundary is 0.412 m.
2. **S05, developer assumption 3:** target halos are not expanded recursively through newly added support tiles. Check this against the contract wording.
3. **S09** uses `diagnostic_horizon` at the nearest5 direction. This is numerical consistency only.
4. **Write-scope interpretations (assumptions 1–2).** The developer took two readings:
   - a root tools lock and task-owned new directories count as authorized;
   - "existing outputs/caches" means files that existed before the task.

   Confirm that no historical output or cache changed.
5. **Tools environment.** The FGDB reader environment lives in `/private/tmp/shade_watch_tools_20261029` and may already be gone. The reviewer must cross-check S02 with a different reader in any case.
6. **Isolation.** The working tree is dirty and the contract is untracked. The reviewer should use a worktree for the code, and read the contract from the main tree after checking its hash.

## Remaining limitations (from the developer report, unchanged)

- No boats or pontoons are modelled, and tide is not modelled.
- The map is 2026, the DSM is 2019–20, so reclamation drift is possible.
- Piers and slivers in LAF stay unknown.
- Sea-target labels are less certain than land labels.
- Observational accuracy is NOT VERIFIED.
- Shade is not cooling or ΔT.
- No territory view exists. Open sea more than 1 km from land is a question for B 1.1.
