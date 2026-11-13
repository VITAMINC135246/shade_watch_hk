# H1.0 static pre-check of the repair candidate `555c4fc` (2026-11-13)

Done by the planning conversation on the linked Mac, read-only, on 2026-11-13 between 11:06 and 11:20 HKT, against `SW-H1.0` with `SW-H1.1`, `SW-H1.2` and `SW-H1.3`.

**This is not an acceptance.** No test was run and no shade was computed. Every item of H1-01 to H1-14 remains for the independent reviewer.

## Candidate

- `555c4fcb138f83ccd2d2fdb83bf98c911ebf613b`, one commit on `bf30c1820df00d565f1815e05ebdef6c68b0698a` (the commit that adds `AMENDMENT_3.md`). Working tree clean. Not pushed.
- Repair report: `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md` (SHA-256 `e1f575751e3e6053318746d79d81654280873d4d31c9e8591079adabe71cf8c7`). It marks H1-01 to H1-13 PASS and H1-14 NOT VERIFIED.

## Checked, with result

| Subject | Result |
| --- | --- |
| Changed tracked files since `bf30c18` | Exactly the allowed files of `SW-H1.2` part B: `shade_watch/engine/{shade_watch,v2,pipeline}.py`, the schema, `config/machine.example.json`, `config/engine/study_area.md`, `tests/test_layout.py`, three viewer files, the repair report and `evidence/repair_1/` |
| A6 | Both alias blocks and the added `import sys` are gone. Against `dc7ad08`, the three engine files differ only in module names and paths |
| A7 | `pipeline.py` reads `shade_watch/engine/<file>`. `tests/test_layout.py` adds the quoted-name pattern |
| A8 | Schema default, example config and the user's config hold `runs/main`. `runs/.shade_map_root.json` is absent. Viewer defaults are `runs/main` |
| A10 | Viewer README names view `412eae79…` and manifest `c915c106…`. `study_area.md` names the new config paths |
| Protected trees since `84dc81f` | No change in `docs/records/`, `legacy/`, `shade_watch/fill/`, `shade_watch/city/`, the three config trees, `estimator.json`, `processing.json`, the three cache-key files. The only test change is one line of `tests/test_layout.py` |
| Data moves | The planner's mapping check repeated: 133,197 files and 5,889 symlinks unchanged |
| Runtime writes (`SW-H1.3` D1) | New items: `runs/h1_0_dev2_20261113/`, `work/runs/h1_0_dev2_*`, `work/locks/h1_0_dev2_*.lock`, `work/fill_impact/h1_0_dev2_nl1-8af8c5a39aa7`, one cache namespace `fill_impact_8af8c5a39aa7`, `archive/reviews/h1_0_dev2_20261113/`. The six existing namespaces are present |

## Finding for the user and the reviewer

**H1-14 cannot pass as the evidence stands.** The contract requires that every job that reads real DSM has start, end and peak memory. For R-4 the final meter row was lost when the tool connection reset. The record `evidence/repair_1/R-4-meter-recovery.json` holds the start, a conservative end (530.77 s debited), and the peak of the engine phase only (1.61 GB); the peak of the whole command is `null`. Comparable whole-command peaks in the same ledger: R-2 1.55 GiB, R-3 1.49 GiB. The 12 GiB budget is not in question, but the requirement is not met.

The planning conversation does not decide this; see D-031.
