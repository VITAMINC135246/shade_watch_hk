# Independent acceptance of SW-G1.0, amended by SW-G1.1

**Engineering acceptance — NOT ACCEPTED.** The gate requires sixteen passes. 12 PASS, 1 FAIL, 3 NOT VERIFIED. G1-08 failed the cross-worktree pointer hash comparison. G1-16 lacks complete peak-memory evidence, and the shade budget curtailed the remaining Hong Kong regression.

## Candidate and environment

| Input | Verified identity |
| --- | --- |
| Candidate and detached worktree | `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d` |
| Parent and planning base | `35314377986fcb9551db288a62b74d3b743121ef`, based on `839e200b3bc8b53012bd3fc67627717b1ac44a4c` |
| Main checkout | `9646279d85325b97bd2f23a37b87f1a60d4b527f`. The two descendant planning commits satisfy A4. Tracked files were clean. |
| Accepted V2 | `356f611d7b775ce31006904b80ca31d3c1c484b2` |
| Accepted F1.0 | `35225fd9547a00e4df202e7ab30204c633b2c845` |
| Accepted B2.2 | `7707c511a44233d05914604c4741aefb86701d7a` |
| Contract SHA-256 at candidate | `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef` |
| Amendment SHA-256 at main HEAD | `8a96095a29c8c32cc639d8464446a146e982312ddde082233f61726bfee3cb93` |
| Independent prompt SHA-256 at candidate | `2be96aabd269a754bea7cace8684cedd60724797443c54dda345bcca11371fab` |
| Environment | macOS 15.7.4 arm64, repository `.venv`, Python 3.12.5, NumPy 2.5.3, Rasterio 1.5.1 / GDAL 3.12.4, pyproj 3.8.0 / PROJ 9.8.1, Numba 0.67.0 |
| Environment lock | `requirements.lock.txt` SHA-256 `ffcc5e7fb9bc57c599c1b76778f10d7edb23f4cf6d301530dccc2126526451e0`. All locked package versions match. `requirements.tools.lock.txt` SHA-256 `98c673a8f17f24ffd629dd8febe223f80687a5ce24c2a578355c34784621cf0e`. |

Commands and outputs are under [review evidence](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/). Re-run Git comparisons with `git diff --name-status 3531437 af6fca9` and `git diff --name-status af6fca9 9646279`. [Scope audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/scope-audit.stdout) · [Environment and test definitions](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/environment-tests-check.stdout)

I inspected the full engine and limited-tool diffs. Hong Kong's CRS, default clock, reference, and source attribution remain the defaults. The daylight change iterates the local day across clock transitions. I compared 6,136 lists on 1,534 Hong Kong dates with the parent and found no differences. The adapter passes the city's inputs to the engine, and the Rotterdam diagnostic resolves the local catalogue and view before using the raw counterfactual. [Engine and adapter diff](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/engine-and-limited-tools.diff) · [Daylight comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk-daylight-equivalence.stdout)

## Input identities

| Input | Path or identifier |
| --- | --- |
| North Rotterdam sheet | `data/raw/dsm/rotterdam_ahn4_dsm05/R_37FZ1.tif`, 457,826,580 bytes, SHA-256 `7a679cf84482cf4397e41992e20a42351a9e266a59e9edf2225b1452e13b3431` |
| South Rotterdam sheet | `data/raw/dsm/rotterdam_ahn4_dsm05/R_37HN1.tif`, 422,003,345 bytes, SHA-256 `15d2cf2027567128dab7727c2f96ef04d300983752f75be9dff6ad0090269ff5` |
| Hong Kong pointer | `data/processed/dsm_views/sea_fill_v2_2/current-hk_cedd_2020.json`, SHA-256 `57bae245ece93063cbff1d97dfab227cbd8bb7a0199f0f0b4d85515164377a5e`, view `8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1` |
| HK-1 accepted V2 | `outputs/v2_daylight_cheungchau_20261009/combined`, plan key `9828649a7b664f6126e5c39321a2814de553c560d29687644d607ffdbd7f31ec` |
| HK-2 reference | `outputs/shade_map/measure_lo_wu`, run `81366c74f1866f1f70ffbf3dc9b557655ec67910155f2044c4513305c22252b8` |
| HK-3 reference | `outputs/shade_map/measure_tai_mo_shan`, run `cb575746ad22b2b78875c6fd471e20ca06bfca159c0ff147a9b0ba8c617a9122` |
| HK-4 reference | `outputs/shade_map/measure_central`, run `43696b580c186299996971b7cdde2abc07b8bc96d5e4d63e2091d92bce5174e2` |
| Rotterdam registration | Developer and fresh review ingestion `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634` and view `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843` |

The input inventory includes SHA-256 for every regular file in the four regression trees and the Hong Kong view, with symlink targets in the filesystem listing. [Input inventory](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/inventory-before.json.gz) · [Input summary](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/inventory-before.stdout)

## Frozen independent manifest

I selected the extra rectangle and drew the sample from the supplied Rotterdam height and surface inputs before starting the reviewer runs or opening the developer’s Rotterdam shade results. The original frozen manifest SHA-256 is `597823c45447a353a624a9a779703e0e74710d26c404e7b20ea02b7f0fdca87d`. A supplement drawn and sealed before the fresh registration adds one distinct NL-1 location, using seed `6111405`. Its SHA-256 is `85c398c22f9ec53af12a8c91241d6c288823d8dc797cbecf8a243f9791db6f86`. [Frozen manifest](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/frozen_manifest.json) · [Supplement](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/frozen_supplement.json) · [Selection script](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/freeze_samples.py)

| Rectangle, EPSG:28992 | Inspected native cells | Local frames and PCG64 seeds |
| --- | --- | --- |
| NL-1, `[91875, 436875] → [93125, 438125]` | `e91875n436875`, `e92500n436875`, `e91875n437500`, `e92500n437500` | 2026-06-21 09:00, 13:30, 18:00 and 2026-12-22 12:30, seeds `6110901`, `6111331`, `6111801`, `1221231` |
| Reviewer rectangle, `[91250, 435000] → [92500, 435625]` | `e91250n435000`, `e91875n435000` | 2026-05-14 09:00, 13:20, 17:30, seeds `5140901`, `5141321`, `5141731` |

The independent input selection found 1,537,730 observed NL-1 pixels below 0 m within 50 m of fill. The ray check covered 300 distinct such targets, 300 distinct observed pixels 4-adjacent to fill and 491 rays crossing the seam. The extra rectangle contains 1,869,691 class 1 pixels and 11,235 observed pixels below 0 m. Its 8,308 observed candidates 4-adjacent to class 1 yielded 295 distinct sampled locations in that stratum. [Sample and ray results](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-rays.stdout)

## Acceptance matrix

| Criterion | Status | Reproducible evidence |
| --- | --- | --- |
| G1-01 | PASS | The candidate is one commit with 84 allowed paths under A1 and A2. All 12 pinned file hashes match the accepted bases and the protected diff is empty. I reconciled the 154,709-entry developer baseline with the current inventory and its exact after digest for 16,405 allowed additions. The planner's fallback totals, all 16 published unit fingerprints, and all 17 file-group digests match. The full session-scoped planner inventory was unavailable. The final main-checkout inventory has only authorized additions and preserved protected data. [Git audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/scope-audit.stdout) · [Final inventory](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/inventory-after.stdout) |
| G1-02 | NOT VERIFIED | 357 complete frames and 6,036 raster comparisons matched with zero differing pixels. The 75-minute budget stopped the remaining case. `compare_regression.py` reads raster pixels and checks transforms, frame order, local and UTC labels, folder names, and counts. For HK-1, F's folder labels map to the V2 reference's local timestamps and each cell is compared to the corresponding V2 pixel window. [Run and comparison commands](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk_campaign.sh) · [Comparator](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/compare_regression.py) |
| G1-03 | NOT VERIFIED | HK-2 had 0 planned misses, 0 computed, 156 reused. HK-3 had 0 planned misses, 0 computed, 156 reused. HK-4 had no complete plan recorded. Every existing namespace retained its listing digest. The preflight records the actual plan before horizon execution. [Preflight code](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk_gate.py) · [Namespace inventory](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/inventory-after.stdout) |
| G1-04 | PASS | The original Cheung Chau config and the 1.0 copy without `dsm_source` each plan 65 Hong Kong frames using the user's unchanged machine file. Both use the legacy raw semantics. `python -m pytest -p no:cacheprovider --basetemp <review>/evidence/pytest-tmp tests` gave 309 passed. Only the A1 test changed. It still covers API, CLI verification, conflict and prune, and the unchanged tests cover raw 1.0 publication. [Original plan](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/compat-cheung_chau.stdout) · [No-source plan](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/compat-legacy-no-source.stdout) · [Pytest](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/pytest.stdout) · [Diff](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/candidate-tests.diff) |
| G1-05 | PASS | The profiles and fill settings equal the frozen JSON and validate. Synthetic CLI cases for unknown city, missing time zone and 1 m resolution return `invalid input`, exit 2, with no new files. [Independent guards](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/guards.stdout) |
| G1-06 | PASS | WGS84 auto-selection chose the same city and bounds as the explicit NL-2 request. Synthetic zero-match and two-match cases and actual CLI cases for outside bounds, missing city, incompatible CRS and corner order returned exit 2 without output writes. [Actual CLI](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-real-cli.stdout) · [Synthetic cases](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/guards.stdout) |
| G1-07 | PASS | All 250,000,000 raw pixels were read independently. 35,951,875 map to float32 −9999.0 and 214,048,125 keep identical bits. All 160 cells are 1250 × 1250 on the RD New lattice. Changed, missing and extra synthetic sheets and bad extent or daylight references were rejected. Both raw sheet hashes match the before snapshot. [Independent reader](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/check_ingestion.py) · [Pixel evidence](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ingest-pixel-check.stdout) · [Guards](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/guards.stdout) |
| G1-08 | FAIL | Both IDs match and 741 of 742 registration file hashes match across the checkouts. The Rotterdam view pointer differs. The repeat returned the same result and left its full registration listing and hashes intact. [Cross-checkout comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/registration-fresh-compare.stdout) · [Repeat](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/registration-repeat-compare.stdout) |
| G1-09 | PASS | Raw extrema are −10.995900 and 204.653793 m NAP, and the 1st/50th/99th percentiles are −6.159500 / 0.042300 / 26.549101 m. The report's centre and counts match. 106,321,205 valid pixels are below 0 m, or 49.6716%. Only `fill_above_ground` fires. Constant 2 m and 10.25 m synthetic sheets give the expected no-warning and `fill_far_below_ground` outcomes. [Raw statistics](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ingest-pixel-check.stdout) · [Synthetic thresholds](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/guards.stdout) |
| G1-10 | PASS | All 406,000,000 domain pixels checked. Every filled bit pattern is float32 +0.0 and every observed pixel retains its bits. Inside-sheet classes 0/1/2/3/4 total 214,048,125 / 18,211,404 / 0 / 17,691,564 / 48,907. All 156,000,000 ring pixels are class 4. The Hong Kong pointer and view hashes match the before snapshot. [Fill-domain evidence](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ingest-pixel-check.stdout) · [Protected inventory](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/inventory-after.stdout) |
| G1-11 | PASS | All 1,008 NL-1–NL-3 rasters and VRTs are EPSG:28992 on the 0.5 m native lattice. An independent PROJ call snaps NL-2 to `[92246.5, 437228.5, 92595.0, 437558.5]`. The plan records the Amersfoort to WGS 84 (4) inverse and RD New operation, stated 1 m accuracy and both versions. [Grid and projection](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-publications.stdout) |
| G1-12 | PASS | An independent J2000 solar calculation gives summer rise/set 05:22:19/22:05:27 and winter 08:47:53/16:33:22. Its 34 and 16 wall-clock frames equal the publication lists, 05:30–22:00 and 09:00–16:30. The four DST offsets and the three NL-2 UTC instants agree. All 13:40 cells meet the solar bounds. Bad offsets and naive gap/fold instants were rejected. [Daylight calculation](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-daylight.stdout) · [CLI rejections](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-real-cli.stdout) |
| G1-13 | PASS | NL-1, NL-2 and NL-3 finished complete with 50, 3 and 3 frames. NL-2 used the documented Python call with no source argument and published `sea-2.2`. F format, city and policy records, raster codes, sealed manifests, VRTs and summaries reconcile. NL-1 and NL-2 have zero quality 1 and 2 pixels. Checked 2,278 raster/VRT metadata sets and 645 text/state files for Hong Kong attribution. All 128 engine shade/quality rasters carry Rotterdam attribution and time zone, with no Hong Kong attribution found. [Publication audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-publications.stdout) · [Invocation](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl_resume.sh) |
| G1-14 | PASS | 1,201 NL-1 target-frame comparisons at 1,200 distinct pixels across four frames, and 420 on the reviewer rectangle. Zero shade or quality disagreements. The samples satisfy A3. [Independent ray code](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/check_rays.py) · [Per-target results](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-rays.stdout) |
| G1-15 | PASS | Independent comparison of the filled output with the raw counterfactual reconciles all five EPSG:28992 dependency mosaics and counts. The three shared raw frames equal NL-3. NL-1's content hashes and listing are identical around the diagnostic. NL-5 finds and warns about 10 missing cells, and NL-1 has zero. [Recomputation](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl-impact-check.stdout) · [Diagnostic output](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl4-impact.stdout) |
| G1-16 | NOT VERIFIED | The guide's registration, CLI plan and run, Python API, and fill-impact commands worked from the detached worktree with the repository environment and the two sheets. The literal guide replay used the example machine’s one-worker setting. All required limitations are present. PROJ networking was disabled and the audited paths operate on local files. Full-job memory is unavailable for NL-1. The development report also records a checksum preflight without RSS metering. The supervisor stopped hk4 before further shade work could exceed the 75-minute cap. No further real-DSM shade jobs were started. [Guide](GUIDE.md) · [Network code search](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/network-code-search.txt) · [Budget ledger](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ledger.jsonl) |

## Hong Kong regression detail

| Run | Published frames | Rasters compared | Planned misses | Computed / reused directions | Evidence |
| --- | ---: | ---: | --- | --- | --- |
| HK-1 Cheung Chau | 65/65 | 780 | new raw cache | 108 / 0 | [Comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk1-compare.stdout) |
| HK-2 Lo Wu | 146/146 | 2628 | 0 | 0 / 156 | [Comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk2-compare.stdout) |
| HK-3 Tai Mo Shan | 146/146 | 2628 | 0 | 0 / 156 | [Comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk3-compare.stdout) |
| HK-4 Central | 0/146 | — | — | — | [Wall stop](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ledger.jsonl) |

## Defect and verification gap

**Major · G1-08 · Cross-worktree registration pointer SHA-256 differs.** The criterion calls for equality of every file hash after a fresh registration in another worktree. Both content IDs and all immutable registration files agree. The frozen view builder writes each catalogue file's mtime into the view pointer. All 160 pointer inventory mtimes differ across checkouts, while their names and sizes match. The amendment provides no exception for this mutable pointer. Its SHA-256 is `3ed2d79bd568431af1da7c75bd571858096924adffff5505867393755e5036ca` in the developer checkout and `b15b2722c040a0c112c75650eb12dda0443ff3e6fdef8393e9207a78efab1767` in review. Affected paths are `data/processed/dsm_views/sea_fill_v2_2/current-nl_rotterdam_dsm05.json`, `tools/sea2/build.py` and `tools/sea2/catalogue.py`. With `W` set to the detached worktree, run the following from the main checkout. [Full file comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/registration-fresh-compare.stdout)

```sh
p=data/processed/dsm_views/sea_fill_v2_2/current-nl_rotterdam_dsm05.json
shasum -a 256 "$p" "$W/$p"
```

**G1-16 · Review resource evidence is incomplete.** The NL-1 outer supervisor was interrupted after starting the candidate. NL-1 published all 50 frames. I reconstructed a conservative 1,588 s wall charge using the output log's birth and modification times, including a 2 s granularity allowance. V2 reported 0.75 GiB peak RSS during engine execution. The full command's peak RSS and transient artifact peak cannot be recovered. In HK-1, the first reviewer wrapper was re-entered by macOS worker spawning. I guarded the reviewer entry point, replacement workers recovered in the same invocation, and I charged its entire 871.6 s to the shade budget. [NL-1 stdout](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/nl1-run.stdout) · [HK-1 stderr](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/hk1.stderr) · [Ledger](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ledger.jsonl)

## Budget ledger

The supervisor used `caffeinate -dims`, sleep-inclusive `mach_continuous_time`, sampled process-tree RSS, and Darwin `wait4` for the command's peak RSS. Start, end, command and per-process samples are in the ledger. It tracks both the detached worktree and the new allowed Hong Kong artifacts. The shade charge includes the direct-ray computation. Other audit jobs were metered separately. For HK-2 to HK-4 the reviewer observed the normal F plan's return before execution, avoiding a duplicate preparation of the same plan. [Supervisor](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/meter.py) · [Full ledger](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/ledger.jsonl)

| Budget | Limit | Review record |
| --- | ---: | --- |
| Shade jobs and plans | 75 min | 74.97 min charged (guard stopped hk4) |
| Fresh registration and repeat | 30 min | 6.67 min |
| Total job memory | 12 GiB | 4.67 GiB highest fully observed concurrent RSS. NL-1 full-job peak unavailable. |
| New artifacts | 20 GiB | 4.29 GiB highest supervised sample. NL-1 transient peak unavailable. |

Times below are local UTC+08:00 on 2026-11-12. The full ledger includes commands and per-process readings.

| Job | Category | Start | End | Wall s | Peak job RSS GiB | Outcome |
| --- | --- | --- | --- | ---: | ---: | --- |
| freeze-samples | audit | 00:01:38 | 00:01:42 | 3.7 | 0.59 | exit 0 |
| nl0-fresh | registration | 00:02:18 | 00:04:48 | 150.0 | 2.09 | exit 0 |
| inventory-before | audit | 00:04:02 | 00:09:04 | 302.7 | 0.27 | exit 0 |
| nl1-plan | shade | 00:05:55 | 00:06:20 | 25.0 | 0.15 | exit 0 |
| nl1-run | shade | 00:06:20 | 00:32:46 | 1588.0 | 0.75 engine only | incomplete metering |
| hk1 | shade | 10:56:05 | 11:10:36 | 871.6 | 2.44 | exit 0 |
| nl2-run | shade | 10:56:27 | 10:56:59 | 32.6 | 0.42 | exit 0 |
| nl2-plan | shade | 10:57:00 | 10:57:07 | 7.9 | 0.22 | exit 0 |
| nl3-run | shade | 10:57:08 | 10:59:33 | 145.3 | 0.71 | exit 0 |
| registration-fresh-compare | audit | 10:57:14 | 10:58:30 | 76.1 | 0.02 | exit 0 |
| ingest-pixel-check | audit | 10:58:30 | 11:02:04 | 213.7 | 3.19 | exit 0 |
| nl0-repeat | registration | 10:58:30 | 11:02:40 | 250.1 | 2.11 | exit 0 |
| nl1-before-nl4 | shade | 10:59:33 | 11:00:09 | 36.0 | 0.02 | exit 0 |
| scope-audit | audit | 10:59:57 | 11:00:43 | 46.2 | 0.33 | exit 0 |
| nl4-impact | shade | 11:00:09 | 11:06:18 | 368.5 | 0.77 | exit 0 |
| guards | synthetic | 11:01:21 | 11:01:58 | 36.6 | 0.15 | exit 0 |
| pytest | synthetic | 11:01:58 | 11:04:14 | 136.2 | 1.03 | exit 0 |
| registration-repeat-compare | audit | 11:02:40 | 11:02:41 | 0.8 | 0.02 | exit 0 |
| nl1-after-nl4 | shade | 11:06:18 | 11:06:23 | 4.3 | 0.02 | exit 0 |
| nl5-edge | shade | 11:06:23 | 11:06:25 | 2.3 | 0.15 | exit 0 |
| nl5-dst | shade | 11:06:26 | 11:07:08 | 42.4 | 0.24 | exit 0 |
| own-run | shade | 11:07:08 | 11:08:07 | 59.1 | 0.68 | exit 0 |
| nl-rays | audit | 11:09:15 | 11:09:17 | 2.6 | 0.45 | exit 0 |
| nl-real-cli | shade | 11:09:15 | 11:09:24 | 9.1 | 0.24 | exit 0 |
| nl-daylight | audit | 11:09:24 | 11:09:25 | 1.1 | 0.02 | exit 0 |
| hk2 | shade | 11:10:37 | 11:20:06 | 569.7 | 1.55 | exit 0 |
| hk1-compare | audit | 11:10:44 | 11:11:07 | 23.1 | 0.27 | exit 0 |
| nl-publications | audit | 11:11:08 | 11:11:47 | 38.9 | 0.47 | exit 0 |
| nl-impact-check | audit | 11:12:10 | 11:12:11 | 1.4 | 0.59 | exit 0 |
| environment-tests | audit | 11:13:33 | 11:13:42 | 9.5 | 0.17 | exit 0 |
| environment-tests-check | audit | 11:15:52 | 11:15:55 | 3.3 | 0.18 | exit 0 |
| hk-daylight-equivalence | synthetic | 11:15:55 | 11:16:03 | 8.2 | 0.02 | exit 0 |
| compat-cheung_chau | shade | 11:18:09 | 11:18:48 | 39.0 | 0.16 | exit 0 |
| compat-legacy-no-source | shade | 11:18:49 | 11:19:14 | 25.8 | 0.16 | exit 0 |
| hk3 | shade | 11:20:07 | 11:30:32 | 625.3 | 1.59 | exit 0 |
| hk2-compare | audit | 11:20:08 | 11:21:27 | 79.7 | 0.28 | exit 0 |
| hk4 | shade | 11:30:33 | 11:31:16 | 43.6 | 0.23 | wall limit |
| hk3-compare | audit | 11:30:39 | 11:31:54 | 75.8 | 0.32 | exit 0 |
| inventory-after | audit | 11:31:24 | 11:35:55 | 271.0 | 0.30 | exit 0 |

## Other conclusions and limits

- **Numerical consistency.** 357 complete frames and 6,036 raster comparisons matched with zero differing pixels. The 75-minute budget stopped the remaining case. Rotterdam ingestion and fill have zero bit mismatches over the required domains. All 1,621 independent ray comparisons agree with published shade and quality.
- **Approximation error.** Physical error from the 1 km cutoff, nearest-5° directions, tile-centre solar references, filled heights and the unchanged NOAA approximation remains unquantified. The approximation's solar accuracy at 52° N remains unverified.
- **Performance.** Registration took 6.67 min. The shade ledger charges 74.97 min. The NL-1 monitoring gap prevents full memory and artifact certification.
- **Observational accuracy.** NOT VERIFIED for Hong Kong and Rotterdam. Rotterdam's surface labels and the AHN release of the two sheets remain unverified.
- **Production completion.** Rotterdam's two-sheet publications and diagnostics completed. 357 of 503 Hong Kong frames were published. The release gate remains closed.

Only 0.5 m DSMs and 0.00 m fill in each city's vertical datum are supported. Rotterdam's water and voids are filled at 0.00 m NAP. About 49.7% of valid pixels and 44.8% of shore pixels lie below that level, by up to about 11 m. The fill can cast false shade on low observed ground, which the model labels shaded. Where shore is above 0 m, fill can leave land falsely sunlit, as in Hong Kong. The diagnostic measures dependence on fill and cannot separate false shade from true shade.

The two sheets bound real coverage. Results within 1 km of their edge depend on fill. The remote-obstruction threshold is `atan((highest point in the native tile and its 1 km buffer − lowest point in that tile) / 1,000 m)`. It reaches about 12° in central Rotterdam. Winter-solstice noon is about 14.7°. Near tall buildings, most winter frames retain quality 3 wherever the 1 km search cannot prove shade.

WGS84 input depends on the PROJ operation available on the computer. Projected corners guarantee exact rectangle reproduction across computers. The unchanged horizon cache identity retains fixed text naming EPSG:2326 for every city.
