# Package H1.0 amendment 5 — operating-system metadata in `docs/`

Amendment ID: `SW-H1.5`
Amends: `SW-H1.0` (`CONTRACT.md`, SHA-256 `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c`), design item 9, rule 2, as amended by `SW-H1.1` to `SW-H1.4`. No earlier file is edited.
Status: frozen by the commit that adds this file, by user decision of 2026-11-16 12:41 HKT (D-035). Record this file's SHA-256 before the repair.

Where this amendment and an earlier document differ, this amendment applies. The commit that adds this file also updates `docs/CONVENTIONS.md` (section 6 states the same exception; section 2 names C2.0 as the Linux package). If two requirements conflict, or a requirement cannot be met, stop and report. Do not choose.

## Why

The second independent acceptance of `6afbb444ddd77d4a4e46ea57ffa810633882b52c` (`docs/packages/H1.0/ACCEPTANCE_REPORT_6afbb444ddd7.md`, SHA-256 `ce4bbe9252cf64a28d1f8a0b02a72e107444c418d621b058c42aa9a7c6607654`) passed 13 of 14 items. H1-03 failed because the main checkout holds `docs/.DS_Store`, a file that macOS Finder writes into every folder it opens. Git ignores it.

Rule 1 of design item 9 (the top level) admits tool caches, and `tests/test_layout.py` admits `.DS_Store` there. Rule 2 (`docs/`) had no such allowance. The two rules should use the same exceptions. Without this change, the test fails whenever someone opens `docs/` in Finder.

## G1. Rule 2

Rule 2 reads: `docs/` holds only `CONVENTIONS.md`, `OUTPUT_CODES.md`, `packages/`, `planning/`, `records/`, and the documents that closeout adds (`INDEX.md`, `ARCHITECTURE.md`, `GUIDE.md`, `GUIDE.zh-TW.md`, `design/`). Entries with these names are not counted, as for rule 1: `.DS_Store`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.ipynb_checkpoints`, `node_modules`.

## G2. Repair (developer)

- **Starting commit:** the commit that adds this amendment; its full SHA is in the handoff message. Its parent is `7499dbf` (second acceptance report), whose parent is the candidate `6afbb44`.
- **Before changing anything:** record HEAD, the branch, a clean tracked tree, the SHA-256 of this file, and that `docs/.DS_Store` exists. Stop and report if any differs.
- **The only product or test change:** in `tests/test_layout.py`, `test_docs_top_level` also accepts the names of G1. No test is added, removed or renamed. The other five layout tests do not change.
- **Do not delete `docs/.DS_Store`.** It stays in place as the case that the test must now accept.
- **New files:** `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_2.md`, with evidence under `docs/packages/H1.0/evidence/repair_2/` (text and JSON only). Larger logs go to `archive/reviews/h1_0_dev3_<YYYYMMDD>/`.
- **Checks:**
  - in the main checkout, with `docs/.DS_Store` present, the full test suite passes;
  - the collected test IDs equal those of `6afbb44` (308);
  - `git diff 6afbb44 <candidate>` touches only `tests/test_layout.py`, apart from the planner's files (this amendment, `docs/CONVENTIONS.md`, `docs/planning/`, the second acceptance report) and the new repair documents.
  - Run pytest with `-B -p no:cacheprovider` so that it writes no cache into the tree.
- **No real-DSM job is authorized.** No regression run, no view build, no registration.
- **Writes:** the one test file, the new repair documents, and `archive/reviews/h1_0_dev3_<YYYYMMDD>/`. Nothing else under `runs/`, `work/`, `data/`, `baselines/` or `archive/`.
- **Deliverable:** one local commit on the starting commit. The report lists the change, the test output and the test-ID comparison, and gives H1-03, H1-06 and H1-14 a verdict. Report the full commit SHA. Do not push. Do not declare acceptance.

## G3. Targeted re-acceptance (reviewer)

- **`TARGET_COMMIT`** is the repair commit. The main checkout's HEAD is `TARGET_COMMIT`, or a descendant that differs from it only in files under `docs/planning/`. `docs/.DS_Store` must exist in the main checkout; do not delete it.
- **Items checked again:**

  | Item | Work |
  | --- | --- |
  | H1-01 | `git diff 6afbb44 TARGET_COMMIT`: apart from the planner's files (this amendment, `docs/CONVENTIONS.md`, `docs/planning/`, the second acceptance report) and the repair-2 documents, the only change is in `tests/test_layout.py`, and it adds exactly the names of G1 to `test_docs_top_level` |
  | H1-03 | In the main checkout: `tests/test_layout.py` passes, and the reviewer's own audit of rules 1 to 6 (rule 2 as in G1, rule 4 as amended by A2 and A7) passes |
  | H1-06 | Collected test IDs at `TARGET_COMMIT` equal those at `6afbb44`. The full suite passes in the main checkout and in a detached checkout |
  | H1-14 | `DEVELOPMENT_REPORT_REPAIR_2.md` lists the change, the test output and the test-ID comparison |

- **Items carried over** from the second acceptance report: H1-02, H1-04, H1-05 and H1-07 to H1-13. Condition: `git diff 6afbb44 TARGET_COMMIT` is empty for `shade_watch/`, `config/`, `web/`, `legacy/`, `docs/records/` and every test file other than `tests/test_layout.py`, and the three cache-key hashes match the contract. If the condition does not hold, those items are NOT VERIFIED.
- **No real-DSM job.**
- **Writes:** evidence and a detached worktree under `archive/reviews/h1_0_<candidate12>_<YYYYMMDD>/`, and the report `docs/packages/H1.0/ACCEPTANCE_REPORT_<candidate12>.md` (not committed).
- **Verdict:** give each of H1-01 to H1-14 PASS, FAIL or NOT VERIFIED. H1.0 is ACCEPTED only if all fourteen pass. Report engineering acceptance and numerical consistency separately; numerical consistency rests on the second acceptance report. Observational accuracy remains NOT VERIFIED for both cities.
