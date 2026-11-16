# H1.0 targeted independent re-acceptance of 2edd8bcfda81

Reviewed on 2026-11-16 under SW-H1.5 G3.

**Engineering acceptance — ACCEPTED.** All fourteen items pass. [Verdict evidence](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/verdicts.json)

**Numerical consistency — VERIFIED for the frozen regression cases.** The second acceptance compared 9,618 rasters across 556 frames in Hong Kong and Rotterdam in R-1 to R-6, with zero differing pixels. R-7 matched all five frame records and the raw catalogue SHA-256. G3 carries over these results. [Second acceptance regression evidence](ACCEPTANCE_REPORT_6afbb444ddd7.md#regression-evidence)

**Observational accuracy — NOT VERIFIED for Hong Kong and Rotterdam.**

## Candidate and frozen inputs

The main checkout was on `feature` at `2edd8bcfda81bfad49e04d53fc29a7030d268404` with a clean tracked tree at entry and close. Its first-parent chain runs through `991eb81c7fc8a4517d4a426967f636ef1195e382` (SW-H1.5), `7499dbfbe9a002f04b6b9127de8708e2d2aae9bd` (second acceptance report), and `6afbb444ddd77d4a4e46ea57ffa810633882b52c` (previous candidate). [Preflight](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/preflight.txt) · [Final checkout state](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-final.json)

`docs/.DS_Store` was present in the main checkout for the layout test and full suite. Its SHA-256, size, inode, device, creation time, modification time and change time matched before and after testing. [Before tests](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-before.json) · [After tests](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-after-tests.json)

| Input | Verified SHA-256 |
| --- | --- |
| `AMENDMENT_5.md` | `98523c37f8520840a38c99e07d60efe866ebdbf0dea466d7fae493f2e78a34de` |
| `ACCEPTANCE_REPORT_6afbb444ddd7.md` | `ce4bbe9252cf64a28d1f8a0b02a72e107444c418d621b058c42aa9a7c6607654` |
| `DEVELOPMENT_REPORT_REPAIR_2.md` | `9cdbb3afa8db07e487f66b09cfe712561f0bda593ad677fbdd36bd2ba00a3733` |
| `CONTRACT.md` | `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c` |
| `AMENDMENT_1.md` | `b07551ce74958863e709625a980e0d727f05e3382902d566771f0830b22976ea` |
| `AMENDMENT_2.md` | `5d1728681b126d44cedc9b4cd9b3556ea154bfce7eb5ce44744491d9de9a5077` |
| `AMENDMENT_3.md` | `80151b31c9e77c71dd0872f9d08a26a2f62532971344b7454ef48d31139945b5` |
| `AMENDMENT_4.md` | `76a258f6841cbb6f9edd55affde12a4341bba1dab63b6815aa90cf0e93fce63f` |
| `docs/CONVENTIONS.md` | `bfce6c3817f68b46b2736c5c40fe97a6878e1fed4d722fa3acdc2e131d5a8e93` |

## G3 carry-over condition

The diff from `6afbb444ddd7` to the candidate is empty for `shade_watch/`, `config/`, `web/`, `legacy/`, `docs/records/` and every test file other than `tests/test_layout.py`. The three cache-key files in the main checkout and the candidate's Git blobs match the contract. These checks authorize carrying forward H1-02, H1-04, H1-05 and H1-07 to H1-13. The second report's numbered rows provide the evidence for those verdicts. [Protected-path diff](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/protected-paths.diff) · [Scope and hash checks](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/scope-and-carry-over.json) · [Second acceptance matrix](ACCEPTANCE_REPORT_6afbb444ddd7.md#acceptance-matrix)

| Cache-key file under `shade_watch/engine/` | Verified SHA-256 |
| --- | --- |
| `horizon.py` | `afb46c37742767e7480220d82527873ed389bb184623fef78b4a3a1d19e8144e` |
| `spatial.py` | `5ecc0495dd102596ab41903b5e174c142888ffc14664b81009164fbf176d3aa7` |
| `v1_cache.py` | `96a576d12ada9186319e4c8c5f1e626b06ab0aac5f7345a9c6083b9f1b6fe479` |

## Acceptance matrix

| Item | Verdict | Basis and evidence |
| --- | --- | --- |
| H1-01 | **PASS** | Rechecked. The 19-path diff contains five planner paths, 13 repair-2 documents and `tests/test_layout.py`. Two lines add exactly the seven G1 names to the allowlist in `test_docs_top_level`. The other five layout tests and the file mode are unchanged. [Paths](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/changed-paths.tsv) · [Patch](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/layout.patch) · [Scope audit](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/scope-and-carry-over.json) |
| H1-02 | **PASS** | Carried over. The second review verified cache-key file identity and the source of `fingerprint` and `profile`. |
| H1-03 | **PASS** | Rechecked in the main checkout with `docs/.DS_Store` present. All six layout tests and all six rules passed the independent checks below. [Pytest output](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-layout.txt) · [Audit script](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/audit_layout.py) · [Audit results](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/layout-audit.json) |
| H1-04 | **PASS** | Carried over. The second review matched the 465 record blobs and relocated estimator to their origins. |
| H1-05 | **PASS** | Carried over. The second review verified the mapped data inventory and carried forward the raw-data sample hashes. |
| H1-06 | **PASS** | Rechecked. Fresh collections at the previous candidate and in both candidate checkouts yielded the same 308 unique node IDs in the same order. All 308 tests passed in each candidate checkout. [Test IDs](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/test-ids.json) · [Main suite](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-suite.txt) · [Detached suite](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/detached-suite.txt) |
| H1-07 | **PASS** | Carried over. The second review verified the configs, defaults, policy values, R-8 plans and invalid-input responses. |
| H1-08 | **PASS** | Carried over. The second review matched 14,256 Hong Kong view files and checked the manifest and pointer. |
| H1-09 | **PASS** | Carried over. The second review matched 576 Rotterdam view files and 160 ingested files, verified the metadata and carried forward the earlier independent registration. |
| H1-10 | **PASS** | Carried over. The second review measured 760 reused and zero computed horizon directions in R-1 to R-6 and verified the pre-existing cache entries. |
| H1-11 | **PASS** | Carried over. The frozen R-1 to R-6 raster comparisons and the R-7 frame and catalogue comparison matched. |
| H1-12 | **PASS** | Carried over. The second review reconciled runtime writes and checked the six sealed publications. |
| H1-13 | **PASS** | Carried over. The second review verified the imports, CLI, config, publication roots and viewer. |
| H1-14 | **PASS** | Rechecked. The repair-2 report describes the exact change and cites the successful test output and the ordered ID comparison. The developer's zero-context patch matches the candidate diff. Both archived collection logs match their recorded hashes and the fresh ordered IDs. [Repair-2 report](DEVELOPMENT_REPORT_REPAIR_2.md) · [Evidence audit](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/report-audit.json) |

## Independent layout audit

| Rule | Main-checkout observation |
| --- | --- |
| 1 | The root inventory contains the authorized project names, Git metadata and permitted OS and tool metadata. |
| 2 | The immediate entries under `docs/` comply with G1, including the existing `docs/.DS_Store`. |
| 3 | The scan found none of `src/`, `tools/`, `outputs/` or `data/processed/`, including dangling symlinks. |
| 4 | The scan found zero retired locations or imports across 101 eligible tracked paths. It applied the A2 estimator exclusion and checked A7's exact quoted components. |
| 5 | All three file hashes match the contract. |
| 6 | The filesystem and Git record path sets equal the manifest. All 465 record hashes match. |

## Reproduction and test ledger

The test environment was macOS 15.7.4 arm64 with the repository's Python 3.12.5 and pytest 9.1.1. A fresh `git archive` export supplied the reference tree for collection. The candidate's detached worktree and its Git registration are under the review evidence directory. The worktree uses the repository's existing Python environment. [Environment](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/preflight.txt) · [Dependency lock hashes](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/locks.sha256) · [Checkout setup](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/checkouts.txt) · [Final detached state](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/detached-after-tests.txt)

Run these commands from the main checkout with the retained evidence directory. The wrapper invokes Python with `-B -m pytest -p no:cacheprovider`, disables PROJ network access, and directs synthetic fixtures and tool caches into the evidence directory. Use a new label for each replay to preserve the existing transcripts and temporary directories. [Pytest wrapper](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/run_pytest.sh)

~~~sh
E="$PWD/archive/reviews/h1_0_2edd8bcfda81_20261116"
export GIT_OPTIONAL_LOCKS=0
.venv/bin/python -B "$E/audit_layout.py"
/bin/sh "$E/run_pytest.sh" replay-main-layout "$PWD" tests/test_layout.py
/bin/sh "$E/run_pytest.sh" replay-reference-collect "$E/reference" --collect-only tests
/bin/sh "$E/run_pytest.sh" replay-main-collect "$PWD" --collect-only tests
/bin/sh "$E/run_pytest.sh" replay-detached-collect "$E/detached" --collect-only tests
/bin/sh "$E/run_pytest.sh" replay-main-suite "$PWD" tests
/bin/sh "$E/run_pytest.sh" replay-detached-suite "$E/detached" tests
~~~

| Check | Result | Pytest elapsed | Exit | Command record |
| --- | --- | ---: | ---: | --- |
| Main layout | 6 passed | 0.10 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-layout.command.txt) |
| Reference collection | 308 collected | 1.79 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/reference-collect.command.txt) |
| Main collection | 308 collected | 17.82 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-collect.command.txt) |
| Detached collection | 308 collected | 0.67 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/detached-collect.command.txt) |
| Main full suite | 308 passed, 3,496 warnings | 79.96 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/main-suite.command.txt) |
| Detached full suite | 308 passed, 3,496 warnings | 71.42 s | 0 | [Command](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/detached-suite.command.txt) |

Both full suites emitted the same pending deprecation warnings for affine multiplication and Rasterio's `is_tiled` property. The targeted review ran zero real-DSM jobs, plans, view builds or registrations. The evidence footprint includes the local Git clone, source export, detached checkout and synthetic test fixtures. [Evidence footprint](../../../archive/reviews/h1_0_2edd8bcfda81_20261116/evidence-footprint-kib.txt)

The report is uncommitted.
