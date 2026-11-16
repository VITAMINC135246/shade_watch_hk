# H1.0 targeted independent re-acceptance of 6afbb444ddd7

Reviewed under SW-H1.2 Part C, SW-H1.3 D2 and SW-H1.4 E3. The regression campaign ran on 2026-11-13. The review closed on 2026-11-16.

**Engineering acceptance — NOT ACCEPTED.** Thirteen items pass and one fails. H1-03 fails layout rule 2 in the main checkout because `docs/.DS_Store` is present. All six layout tests and the complete 308-test suite pass in a detached checkout of the same commit.

**Numerical consistency — VERIFIED for the frozen regression cases.** All 9,618 raster comparisons across 556 frames in R-1 to R-6 matched the Hong Kong and Rotterdam baselines, with zero differing pixels. R-7 matched all five frame records and the raw catalogue SHA-256. The two city views and the Rotterdam catalogue also matched their archived references.

**Observational accuracy — NOT VERIFIED for Hong Kong and Rotterdam.**

## Candidate and frozen inputs

The main checkout on `feature` was at `6afbb444ddd77d4a4e46ea57ffa810633882b52c` with a clean tracked tree at entry and close. Its parent is `b43674c4120a5f9af77ccf574e8018e1ad0a7ff8`. The checked first-parent sequence is `6afbb44 ← b43674c ← ea8e131 ← 555c4fc ← bf30c18 ← a70132c ← 2442f2e ← 25c018d ← 84dc81f ← dc7ad08 ← fda9985 ← cfb6e3c`. The local `pre-h1.0` tag and remote-tracking `origin/feature` resolve to `cfb6e3c52001103a206c256c1af46bcdce30f01c`. The G1.0 reference commit is `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d`. The two planner pre-checks were accounted for in the diff scope only. [Preflight and full ancestry](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/preflight.txt)

Real runs used the pinned main checkout and its `.venv` on macOS 15.7.4 arm64. Python 3.12.5, NumPy 2.5.3, rasterio 1.5.1, GDAL 3.12.4, pyproj 3.8.0 and PROJ 9.8.1 were recorded. Collection and fixtures used Git-managed detached checkouts under the review archive, made from a local clone so Git worktree registrations stayed inside the evidence folder. [Environment and package versions](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/preflight.txt) · [Detached checkouts](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/review-worktrees.txt)

| Input | SHA-256 |
| --- | --- |
| `docs/packages/H1.0/CONTRACT.md` | `b45f0565d7601540e36329b843ae2eba85fe7a03ca03968d89d61f90f02edf8c` |
| `docs/packages/H1.0/AMENDMENT_1.md` | `b07551ce74958863e709625a980e0d727f05e3382902d566771f0830b22976ea` |
| `docs/packages/H1.0/AMENDMENT_2.md` | `5d1728681b126d44cedc9b4cd9b3556ea154bfce7eb5ce44744491d9de9a5077` |
| `docs/packages/H1.0/AMENDMENT_3.md` | `80151b31c9e77c71dd0872f9d08a26a2f62532971344b7454ef48d31139945b5` |
| `docs/packages/H1.0/AMENDMENT_4.md` | `76a258f6841cbb6f9edd55affde12a4341bba1dab63b6815aa90cf0e93fce63f` |
| `docs/packages/H1.0/ACCEPTANCE_PROMPT.md` | `1f6613ba4ef03f65a4dd090b710dccd765d782c097485de748ed0f815c160f0a` |
| `docs/packages/H1.0/ACCEPTANCE_REPORT_84dc81fddb3b.md` | `8df2c93139687835ec21a0eaa98a4c89ae21cbe5949e6adb8c17138ed9bd13e7` |
| `docs/packages/H1.0/DEVELOPMENT_REPORT_REPAIR_1.md` | `22f52eb251aa28a4e180acb4c154ec2df668078b779aba0bdee93a66468ad9f3` |
| `docs/CONVENTIONS.md` | `49dc90cba8738fd9907abbb6e0aadd3b0428b25c91fd4186a15d824029c21cba` |
| `archive/baseline_h1_0_20261112/listing.tsv` | `c82d5ed7644927d8384177254ccba4960117d5d482ebd1a2e27f13571b6b5afb` |
| `requirements.lock.txt` | `ffcc5e7fb9bc57c599c1b76778f10d7edb23f4cf6d301530dccc2126526451e0` |
| `requirements.tools.lock.txt` | `98c673a8f17f24ffd629dd8febe223f80687a5ce24c2a578355c34784621cf0e` |
| `config/machine.local.json` | `2ebc427f73f6411bda2c1ebd9b5e43e124a240fef72187cf5a2aef8d692507d2` |

| V1 cache-key file | SHA-256 |
| --- | --- |
| `horizon.py` | `afb46c37742767e7480220d82527873ed389bb184623fef78b4a3a1d19e8144e` |
| `spatial.py` | `5ecc0495dd102596ab41903b5e174c142888ffc14664b81009164fbf176d3aa7` |
| `v1_cache.py` | `96a576d12ada9186319e4c8c5f1e626b06ab0aac5f7345a9c6083b9f1b6fe479` |

| Derived input | Archived ID | Current ID | Files hashed |
| --- | --- | --- | ---: |
| Hong Kong view | `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1` | `412eae7951535ccf4f747be461ebcfe64f4e812d67a4d93f558150a718277d5e` | 14,256 |
| Rotterdam view | `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843` | `11004a24a611e773a72b08cbc30e31cfda15ec462a18654105956bcdf15193eb` | 576 |
| Rotterdam ingestion | `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634` | `ce865fa2895066d03fba441ec6a6ce80d0c8f41c387a1e21e0614136baeb36a3` | 160 |

[Per-file derived hashes](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/view-and-ingestion-hashes.tsv.gz) · [Manifest, pointer and class-total checks](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/views-and-ingestion.json) · [Baseline reference hashes](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/baseline-identities.sha256)

## Acceptance matrix

Use the repository root as the working directory, `P=.venv/bin/python` and `E=archive/reviews/h1_0_6afbb444ddd7_20261113`. The archived commands capture the CLI arguments, fixtures and environments. [Reproduction commands](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/commands-for-audit.txt)

| Item | Verdict | Independent result |
| --- | --- | --- |
| H1-01 | **PASS** | `git diff 84dc81f 6afbb444ddd7` yields ten A6–A10 product and test changes, 42 new repair records, and nine planner paths. The authorized planner paths include SW-H1.2 to SW-H1.4 and both pre-checks. The SW-H1.4 candidate commit updates the repair report and adds nine rerun evidence files. Rename-aware diffs from `dc7ad08` for the three engine files contain only path and module-name changes. The first review classification applies to untouched paths. [Scope classification](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/repair-file-classification.tsv) · [Engine-origin diff](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/scope-origin-engine.patch) · [E2 commit diff](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/rerun-diff.tsv) |
| H1-02 | **PASS** | `"$P" -B "$E/static_review.py"` verified the three full SHA-256 values above against both contract and original blobs. AST source extraction confirmed byte-for-byte source text for `fingerprint` and `profile`. The authorized copy of `polygonal` also matches. [Code identities](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/code-identity.json) |
| H1-03 | **FAIL** | The independent layout audit found one unexpected entry directly under `docs/`. Main-checkout `tests/test_layout.py` gave five passes and one failure at `test_docs_top_level`. The A7 quoted-component scan passed, and the synthetic pipeline completed 65 frames with all 196 publication and 27 horizon rasters matching `dc7ad08`. The candidate's six layout tests pass in the detached checkout. [Independent layout audit](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/layout-audit.json) · [Main layout test](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/main-layout-pytest.txt) · [Detached layout test](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/layout-pytest.txt) · [Synthetic pipeline](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/synthetic/engine-results.json) |
| H1-04 | **PASS** | The diff from `84dc81f` is empty for `docs/records/`, the estimator and `legacy/`. The record-manifest test passes. Independent hashing matched all 465 record blobs to their origins at `dc7ad08` and the on-disk manifest. The moved estimator is byte-identical to its origin. [Record and estimator comparison](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/records-audit.json) |
| H1-05 | **PASS** | `"$P" -B "$E/check_data.py" inventory` mapped the verified planner inventory and checked 133,197 files and 5,889 symlinks against both developer inventories and the current tree. Size, nanosecond mtime and link-target mismatches total zero. The first independent review's 320 sampled Hong Kong tiles and two Rotterdam sheets carry over under Part C. [Inventory results](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/planner-inventory.json) · [Mapped inventory](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/planner-mapped.tsv.gz) · [Earlier raw sample evidence](../../../archive/reviews/h1_0_84dc81fddb3b_20261113/evidence/raw-sample-hashes.tsv) |
| H1-06 | **PASS** | Fresh collection at `84dc81f` and `6afbb44` produced the same 308 test IDs in the same order. All 308 passed at `6afbb44` in the detached checkout. The entire test diff is the one authorized regex line in `tests/test_layout.py`. See H1-03 for the additional main-checkout layout run. [Collected IDs](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/test-ids.json) · [Full suite](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/full-pytest.txt) · [Complete test diff](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/test-diff.patch) |
| H1-07 | **PASS** | The city, sea-profile and region trees match `dc7ad08`. The schema diff changes two defaults, to `runs/main` and `raw`. The named policy IDs, sources, rule and publication format are preserved. Both R-8 plans use the user's machine file and resolve to Hong Kong raw, including the region without `dsm_source`. Eleven CLI probes returned exit 2 and `invalid input:` without changing their fixture checkout. [Config and policy checks](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/behaviour-audit.json) · [Explicit plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-8-explicit.stdout) · [Legacy plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-8-legacy.stdout) · [Rejection transcripts](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/synthetic/g1-06-rejections.json) |
| H1-08 | **PASS** | `"$P" -B "$E/check_data.py" views` hashed all 14,256 Hong Kong tiles and surfaces against the archived manifest. No file hash or class total differs. The two manifests and pointers differ only in the fields permitted by the contract. The current ID recomputes from its manifest. [Derived data audit](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/views-and-ingestion.json) |
| H1-09 | **PASS** | All 576 Rotterdam view files and all 160 ingested tiles match archived hashes. The view manifest, class totals, pointer, ingestion manifest, report and pointer agree within the authorized exceptions, including Rotterdam's view-pointer header mtimes. The diff from `84dc81f` for `shade_watch/fill/` and `shade_watch/city/` is empty. The prior independent registration reproduced both current IDs and carries over under Part C. [Derived data audit](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/views-and-ingestion.json) · [Earlier registration](../../../archive/reviews/h1_0_84dc81fddb3b_20261113/evidence/jobs/V-2.stdout) |
| H1-10 | **PASS** | Six fresh plans had zero missing directions. R-2 to R-4 reproduced their G1.0 spatial-key sets. R-1 to R-6 reused 760 horizon directions and computed zero. All 2,359 pre-existing cache entries across seven namespaces matched before and after, including inode, mode, size, timestamps and symlink targets. [Runtime and cache audit](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/run-window-audit.json) · [Regression evidence](#regression-evidence) |
| H1-11 | **PASS** | Independent raster and count comparisons matched all 9,618 R-1 to R-6 rasters. R-1 used the E2.0 UTC index. R-2 to R-6 matched frame sequence, date and time directories and per-frame counts, including summary counts. R-7 matched every frame record and the raw catalogue SHA-256. [Raster comparator](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/compare_rasters.py) · [R-7 comparison](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-7-comparison.json) · [Regression evidence](#regression-evidence) |
| H1-12 | **PASS** | The new files attributable to the timed jobs are confined to the review publication, the named work and lock paths, and one new R-7 namespace. All six sealed publications use F format and record the new paths. `outputs/`, `data/processed/` and the `runs/.shade_map_root.json` container marker are absent. The delayed inventory and post-job filesystem activity are documented below. [Raw inventory comparison](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/runtime-audit.json) · [Timestamp and path reconciliation](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/run-window-audit.json) |
| H1-13 | **PASS** | The package imports lazily and both public functions resolve. Real and synthetic CLI transcripts contain no runpy double-import warning. Both alias blocks are absent. The instrumented pipeline and V2 controller and workers match the parent module execution counts. The synthetic nested publication followed by default `runs/main` succeeded with CLI-created markers. The machine config matches exactly the four required key changes. Both viewer fallbacks use `runs/main`, all 7,128 cells match, and the README matches the verified view ID and digest. R-6 ran through the public API. [CLI and import transcripts](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/synthetic/commands.json) · [Synthetic root sequence](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/synthetic/publication-results.json) · [Viewer checks](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/viewer-audit.json) |
| H1-14 | **PASS** | The unchanged first development report has all 14 items, 157 move units and 623 tracked paths in its move table, and the original ledger. The repair report has all items, the authorized changes and the SW-H1.4 ledger. I matched the R-4 rerun's launch record, timed samples, exit and sealed publication, and verified all 23 entries of the rerun archive index. With the original R-4 debit charged, the repair budget total is 62.68 min at 2.254 GiB measured RSS and a 1.651 GiB conservative artifact ceiling. [Developer ledger audit](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/development-ledger-audit.json) · [R-4 replacement ledger](evidence/repair_1/r4_rerun/resources.jsonl) |

## H1-03 failure

**Low severity, release-gating checkout layout failure.** SW-H1.0 design item 9 rule 2 restricts the immediate entries under `docs/` to the listed documents and directories. The main checkout contains the ignored macOS file `docs/.DS_Store`. Its recorded creation time, 2026-11-13 03:21:39 +08:00, precedes the review. Neither the Git diff nor the tracked-tree status can show it. Reproduce from the main checkout with `.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_layout.py::test_docs_top_level`. The failure is at `tests/test_layout.py:52`. The main-checkout file was preserved under SW-H1.3 D2. [Failure transcript](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/main-layout-pytest.txt) · [Ignore rule and original metadata](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/main-layout-ignore.txt)

The earlier engine aliases, stale pipeline identity path, nested-to-default publication failure, shared R-2 to R-4 work paths and stale viewer and study-area references were checked in this round. All five findings from the first review are resolved. All six regression manifests identify the clean target commit. [Authorized source diff](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/scope-84dc81f-to-target.patch) · [Synthetic checks](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/synthetic/engine-results.json) · [Reviewed input provenance](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/inputs/provenance.json)

## Regression evidence

| Run | Review name | Frozen reference | Frames | Compared rasters | Different pixels | Directions reused | Evidence |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| R-1 | `h1_0_rev2_hk1` | `baselines/e2_cheung_chau_20260107/combined` | 65 | 780 | 0 | 108 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-1-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-1-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-1-rasters.tsv) |
| R-2 | `h1_0_rev2_lo_wu` | `baselines/measure_5regions_20261110/measure_lo_wu` | 146 | 2,628 | 0 | 156 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-2-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-2-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-2-rasters.tsv) |
| R-3 | `h1_0_rev2_tai_mo_shan` | `baselines/measure_5regions_20261110/measure_tai_mo_shan` | 146 | 2,628 | 0 | 156 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-3-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-3-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-3-rasters.tsv) |
| R-4 | `h1_0_rev2_central` | `baselines/measure_5regions_20261110/measure_central` | 146 | 2,628 | 0 | 148 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-4-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-4-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-4-rasters.tsv) |
| R-5 | `h1_0_rev2_nl1` | `baselines/g1_dev_20261111/g1_dev_nl1` | 50 | 900 | 0 | 180 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-5-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-5-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-5-rasters.tsv) |
| R-6 | `h1_0_rev2_nl2` | `baselines/g1_dev_20261111/g1_dev_nl2` | 3 | 54 | 0 | 12 | [Plan](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-6-plan.stdout) · [Engine](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-6-execution.json) · [Rasters](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-6-rasters.tsv) |

R-1 compared the emitted shade and quality cell rasters, mosaics and VRTs to aligned windows of the E2.0 combined rasters by UTC time. For R-2 to R-6 the comparison read the VRT pixels and used SHA-256 for byte-identical TIFFs. SHA-256 values of all files listed in each sealed F publication were read from disk and verified. R-2 to R-4 use copies whose only text change is the requested run name. R-8 uses name-only copies for its two plan-only invocations so both carry the review prefix while using the actual `config/machine.local.json`. [Comparator source](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/compare_rasters.py) · [Input copy hashes](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/inputs/provenance.json)

R-7 reused R-5's `h1_0_rev2_nl1` publication and selected `0900,1330,1800`. The prelaunch check found `fill_impact_f5aedeb04a85` absent. R-7 created that one namespace and computed 20 raw counterfactual directions. Its five frame records and `4b44b22b73f1da3809d9994d6e81f7134fb29e6d21b11f60a4b5a3e153753718` raw catalogue SHA-256 match the G1.0 reference. The diagnostic's own before-and-after integrity record agrees with the R-5 publication manifest. [R-7 prelaunch gate](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/jobs/R-7-gate.stdout) · [R-7 output check](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/R-7-comparison.json)

## Runtime audit and budgets

The jobs ran under `caffeinate -dims` with four workers, local inputs and `PROJ_NETWORK=OFF`. Metering started before command launch and used the sleep-inclusive `mach_continuous_time` clock. RSS is the greater of sampled simultaneous process-group RSS and the macOS `wait4` command high-water mark. The artifact meter samples the greater of logical and allocated bytes. Short spikes between samples are subject to sampling resolution. Each ledger row was synced before the next launch. The meter charged one additional second for an aborted R-1 plan launch while adapting the process monitor to the sandbox. The successful jobs and plans all have full meter rows. Direct hashes, listing, raster comparison and synthetic verification are outside the R-1 to R-8 time allowance. [Meter](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/meter.py) · [Meter setup record](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/meter-setup-note.txt) · [Full ledger and arguments](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/ledger.jsonl)

| Review resource | Observed | Limit |
| --- | ---: | ---: |
| R-1 to R-8 jobs and plans, including the setup debit | 3479.915 s (58.00 min) | 5,400 s |
| Peak whole-job RSS | 2,514,681,856 bytes (2.34 GiB) | 12 GiB |
| Peak new artifacts during jobs | 1,503,617,702 bytes (1.40 GiB) | 10 GiB |
| Final artifacts including comparison evidence and report | 1.40 GiB | 10 GiB |
| Hong Kong rebuilds and Rotterdam registrations | 0 and 0 | 0 and 0 |

| Command | Start on 2026-11-13 (+08:00) | End (+08:00) | Wall s | Peak RSS bytes | Net new artifact bytes | Exit |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| R-1-plan | 11:48:27.306 | 11:49:52.956 | 85.651 | 269,762,560 | 62,067,900 | 0 |
| R-1 | 11:49:53.066 | 11:52:39.152 | 166.088 | 1,618,821,120 | 181,431,208 | 0 |
| R-2-plan | 11:52:39.703 | 12:05:25.652 | 765.709 | 341,344,256 | 5,913,172 | 0 |
| R-2 | 12:05:26.203 | 12:14:19.565 | 533.361 | 1,687,240,704 | 272,784,702 | 0 |
| R-3-plan | 12:14:20.214 | 12:17:42.914 | 202.699 | 327,286,784 | 860,364 | 0 |
| R-3 | 12:17:43.534 | 12:27:44.235 | 600.549 | 1,725,186,048 | 472,861,674 | 0 |
| R-4-plan | 12:27:45.103 | 12:30:45.581 | 180.475 | 324,517,888 | 65,604 | 0 |
| R-4 | 12:30:46.343 | 12:39:03.456 | 497.106 | 1,710,260,224 | 260,447,210 | 0 |
| R-5-plan | 12:39:04.533 | 12:40:13.172 | 68.630 | 254,214,144 | 36,932 | 0 |
| R-5 | 12:40:14.080 | 12:42:27.253 | 133.170 | 1,484,980,224 | 83,413,610 | 0 |
| R-6-plan | 12:42:28.279 | 12:42:40.739 | 12.460 | 195,788,800 | 20,548 | 0 |
| R-6 | 12:42:41.562 | 12:42:48.378 | 6.816 | 926,728,192 | 1,582,536 | 0 |
| R-7-gate | 12:42:49.283 | 12:42:50.478 | 1.194 | 147,128,320 | 8,260 | 0 |
| R-7 | 12:42:51.316 | 12:44:36.377 | 105.059 | 2,514,681,856 | 159,173,094 | 0 |
| R-8-explicit | 12:44:37.407 | 12:45:56.123 | 78.715 | 269,959,168 | 41,028 | 0 |
| R-8-legacy | 12:45:57.296 | 12:46:38.531 | 41.234 | 269,008,896 | 36,932 | 0 |

For H1-14, the developer rerun `h1_0_dev2_central_r2` began at 11:26:34.276 and ended at 11:33:27.389 +08:00 on 2026-11-13. The whole-command peak was 1,676,312,576 bytes and the new artifact delta was 260,272,128 bytes. Its plan took 169.301 seconds with peak RSS 339,738,624 bytes. The completed rerun replaces the missing whole-command row under E3. The original R-4 still contributes its 530.765-second wall debit. The independently summed repair total is 3760.565 seconds and the report conservatively charges 3760.623 seconds. [Developer meter reconciliation](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/development-ledger-audit.json) · [SW-H1.4 records](evidence/repair_1/r4_rerun/resources.jsonl)

The before inventory was taken before the first launch. The after inventory was taken on 2026-11-16, after the controller had finished on 2026-11-13 at 12:46:38.531 +08:00. The raw difference records 63 added and 12 modified Finder metadata files, a later Git commit-graph replacement and Git client metadata, and two later change-time-only differences on tracked files whose frozen hashes still match. The listed metadata deltas postdate the timed review. Four publication directories reflect later Finder insertions, including three top-level run extras. The comparator verified their macOS file signatures and post-job creation times and checked every manifest-listed publication file. All observed review-generated runtime entries fall within D2. The unchanged cache entries and scoped outputs are verified from the retained listings. [Before inventory](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/before.jsonl.gz) · [After inventory](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/after.jsonl.gz) · [All filesystem differences](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/runtime-audit.json) · [Timestamp reconciliation](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/run-window-audit.json)

The evidence archive preserves the two synthetic command transcripts, the first fixture's rejected timestamp, and the comparison harness correction for the older pipeline's path-dependent identity. The numerical comparison uses matched raster data in the two fixture checkouts. [Review replay notes](../../../archive/reviews/h1_0_6afbb444ddd7_20261113/replay-notes.txt)

This report is uncommitted.
