# Package H1.0 amendment 4 — metered rerun of R-4

Amendment ID: `SW-H1.4`
Amends: `SW-H1.2` (SHA-256 `5d1728681b126d44cedc9b4cd9b3556ea154bfce7eb5ce44744491d9de9a5077`) and `SW-H1.3` (SHA-256 `80151b31c9e77c71dd0872f9d08a26a2f62532971344b7454ef48d31139945b5`). No earlier file is edited.
Status: frozen by the commit that adds this file, by user decision of 2026-11-13 11:12 HKT (D-032). Record this file's SHA-256 before the rerun.

## Why

The repair candidate `555c4fcb138f83ccd2d2fdb83bf98c911ebf613b` lacks the whole-command peak memory of R-4: the final meter row was lost when the tool connection reset (`evidence/repair_1/R-4-meter-recovery.json`). H1-14 requires start, end and peak memory for every job that reads real DSM. The user chose to rerun R-4 with full metering rather than to relax H1-14.

## E1. The rerun

- Run R-4 once more, exactly as in `SW-H1.2` A9, with the run name `h1_0_dev2_central_r2`, published under `runs/h1_0_dev2_20261113/`. Its plan is part of the job.
- Before the run, the plan shows zero missing directions; if not, stop and report.
- Compare it with the baseline as in the contract and A9.
- Its plan and run count against the 90-minute budget of `SW-H1.2` together with the jobs already recorded (52.97 min including the debit for the lost R-4 row). The memory and artifact budgets are unchanged.
- Runtime writes allowed in addition to `SW-H1.3` D1: the publication folder of this name and the `work/` folders that the tools create for it. Nothing else.

## E2. The candidate

- The candidate of the repair is a new commit whose parent is the commit that adds this amendment (its parent chain: that commit, `ea8e131` planner pre-check, `555c4fc` repair). This replaces "one local commit on the starting commit" in `SW-H1.2` part B.
- The new commit changes only `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md` and adds files under `docs/packages/H1.0/evidence/repair_1/`. No product, test or config file changes. Existing evidence files are not edited; the lost-row record stays as it is.
- The report adds the complete meter row of the rerun to the ledger, states that the rerun replaces the first R-4 for H1-14, and gives H1-14 a verdict. The first R-4 and its recovery record stay in the report as history.

## E3. Re-acceptance

- `TARGET_COMMIT` in `SW-H1.2` part C is the new commit. For H1-01, the planner's files additionally include this amendment and `docs/planning/reviews/H1_PRECHECK_555c4fc.md`.
- For H1-14 the reviewer checks the ledger row of the rerun. Everything else in part C and in `SW-H1.3` D2 applies unchanged.
