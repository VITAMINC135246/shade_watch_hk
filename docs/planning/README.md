# Planning records (snapshot)

This folder holds dated snapshots of the planning records kept in the Claude project `SHADE_WATCH_HK`. The copies let developers (Codex) and independent-acceptance conversations read the decisions and reviews that the contracts refer to. Contracts up to G1.0 are in `docs/prompts/`; from H1.0 on they are in `docs/packages/<version>/`.

- **Master copy:** the Claude project (`claude/DECISIONS.zh-TW.md`, `claude/reviews/`). If a snapshot here disagrees with the master, the master wins.
- **When it is refreshed:** each time a contract is frozen.
- **Language:** the decision log is in Traditional Chinese, an exception to the English-only rule for repository documents. The reviews are in English.
- **These are records, not evidence.** Acceptance verdicts come only from the acceptance reports named in the reviews and contracts.

| File | Content |
| --- | --- |
| `DECISIONS.zh-TW.md` | Decision log D-001 to D-027 |
| `reviews/REGION_REVIEW_precommit_20261029.md` | Static pre-commit review of package A1.0 (working tree, 2026-10-29) |
| `reviews/REGION_REVIEW_374a70d.md` | Review of A1.0 at `374a70d` |
| `reviews/SEA_PRECHECK_86dbee6.md` | Static pre-check of B1.0 at `86dbee6` (not an acceptance) |
| `reviews/REGION_REVIEW_f5f24ac.md` | Review of A1.0 + A1.1 at `f5f24ac` |
| `reviews/F1_PRECHECK_eb605f5.md` | Static pre-check of the first F1.0 candidate `eb605f5` (later NOT ACCEPTED) |
| `reviews/F1_PRECHECK_35225fd.md` | Static pre-check of the repaired F1.0 candidate `35225fd` (later ACCEPTED) |
| `reviews/B2_PRECHECK_5744e23.md` | Static pre-check of the B2.0 candidate `5744e23` (not sent to acceptance; superseded by B2.2) |
| `reviews/B2_2_BASELINE_20261105.md` | Planner baseline of protected files before B2.2 development (2026-11-05) |
| `reviews/B2_PRECHECK_7707c51.md` | Static pre-check of the B2.2 candidate `7707c51` (later ACCEPTED) |
| `reviews/G1_BASELINE_20261111.md` | Planner baseline of protected files before G1.0 development (2026-11-11) |
| `reviews/G1_PRECHECK_af6fca9.md` | Static pre-check of the G1.0 candidate `af6fca9` (later ACCEPTED) |
| `reviews/H1_BASELINE_20261112.md` | Planner baseline of the data folders before H1.0 development (2026-11-12) |
| `reviews/H1_PRECHECK_84dc81f.md` | Static pre-check of the H1.0 candidate `84dc81f` (not an acceptance) |

Snapshot taken 2026-11-13 (HKT).
