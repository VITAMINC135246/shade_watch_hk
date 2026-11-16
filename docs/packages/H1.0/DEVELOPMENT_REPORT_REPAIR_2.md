# H1.0 development report for repair 2

On 2026-11-16, the preflight confirmed a clean tracked tree on `feature` at `991eb81c7fc8a4517d4a426967f636ef1195e382`. Its parent is `7499dbfbe9a002f04b6b9127de8708e2d2aae9bd` and its grandparent is `6afbb444ddd77d4a4e46ea57ffa810633882b52c`. The SHA-256 values of SW-H1.5, the second acceptance report and the updated conventions match the handoff. `docs/.DS_Store` was present. [Preflight](evidence/repair_2/preflight.txt)

SW-H1.5 G2 changes the allowlist in `test_docs_top_level` to also admit `.DS_Store`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.ipynb_checkpoints` and `node_modules`. The two added lines in `tests/test_layout.py` are the only product or test change against `991eb81`. Against `6afbb44`, the remaining differences are the planner's files and this repair's report and evidence. [Patch](evidence/repair_2/layout.diff.txt) · [Scope comparison](evidence/repair_2/scope.json)

| Item | Developer verdict | Evidence |
| --- | --- | --- |
| H1-03 | PASS | All six layout tests passed in the main checkout with `docs/.DS_Store` present. Its inode, timestamps, size and SHA-256 matched before and after the suite. [Test output](evidence/repair_2/full-pytest.txt) · [Before](evidence/repair_2/docs-metadata-before-tests.txt) · [After](evidence/repair_2/docs-metadata-after-tests.txt) |
| H1-06 | PASS | Fresh collection from the `6afbb44` source tree and collection in the repaired main checkout returned the same 308 unique test IDs in the same order. The full suite reported `308 passed, 3496 warnings in 75.86s` and exited 0. [Reference collection](evidence/repair_2/collect-6afbb44.txt) · [Repair collection](evidence/repair_2/collect-repair-2.txt) · [ID comparison](evidence/repair_2/test-ids.json) · [Suite timing and exit](evidence/repair_2/full-pytest-timing.txt) |
| H1-14 | PASS | This report records the sole test change, full pytest output, test-ID comparison and preflight. [Commands and environment](evidence/repair_2/test-commands.txt) |

The full suite ran with the project Python using `-B -p no:cacheprovider`. A temporary source export of `6afbb44` supplied the reference collection. Test fixtures and caches used a temporary directory outside the repository. Verification consisted of pytest and Git scope checks, with no real-DSM job.
