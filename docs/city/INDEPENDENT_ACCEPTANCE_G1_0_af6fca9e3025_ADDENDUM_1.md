# Supplementary independent acceptance of SW-G1.0

**Engineering acceptance — ACCEPTED under SW-G1.2.** 16 PASS, 0 FAIL, 0 NOT VERIFIED.

## Pinned inputs

| Input | Verified identity |
| --- | --- |
| Candidate and existing detached worktree | `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d` |
| Main checkout HEAD | `322431f0d0df2c3940057bc0a4cc54ed41dd25db` |
| SW-G1.0 contract SHA-256 | `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef` |
| SW-G1.1 SHA-256 | `8a96095a29c8c32cc639d8464446a146e982312ddde082233f61726bfee3cb93` |
| SW-G1.2 SHA-256 | `4324da9234c4a9141a13b6755fd0c5b09a018d91589ae97217f4a9adca26ab65` |
| First report SHA-256 | `11d605dc18a2d54b071714e7c6abd8ad329f75089beb60f77f6beb5873f38875` |
| Environment | `macOS-15.7.4-arm64-arm-64bit`, repository `.venv`, Python 3.12.5, matching `requirements.lock.txt` SHA-256 `ffcc5e7fb9bc57c599c1b76778f10d7edb23f4cf6d301530dccc2126526451e0` |

A4 passed at both boundaries. The main checkout is a permitted descendant of the candidate and both checkouts have clean tracked files. The publication manifests' Git status flags also reflect untracked entries (`presentations/` in main and the `.venv` symlink in the worktree). The first report retains its original verdict and checksum. [First report](INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025.md) · [Before pins](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/pins-before.json) · [After pins](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/pins-after.json)

## G1-08 under B1

**PASS.** The prior FAIL applied the hash criterion before B1. The candidate SHA is unchanged. The first review's saved inventories give 163 equal ingestion file hashes and 577 equal view-folder file hashes. The fresh and repeat snapshots are identical over all 747 entries. Both checkouts resolve ingestion `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634` and view `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843`. [B1 evidence](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/g1-08-b1.json) · [First hash comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/registration-fresh-compare.stdout) · [Original repeat](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence/registration-repeat-compare.stdout)

| Rotterdam view pointer | SHA-256 |
| --- | --- |
| Developer | `3ed2d79bd568431af1da7c75bd571858096924adffff5505867393755e5036ca` |
| Review | `b15b2722c040a0c112c75650eb12dda0443ff3e6fdef8393e9207a78efab1767` |

The pointer bytes still differ. Comparing the JSON after removing only each `header_inventory[*].mtime_ns` gives exact equality. All 160 names, sizes and row positions match and 160 modification times differ. [Reproduction script](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/recheck_b1.py)

## Supplementary runs

| Case | Publication | Frames compared | Rasters and VRTs | Differing pixels | Planned misses | Computed / reused |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| S-1 · HK-4 Central | `g1_add1_af6fca9e3025_s1_central` | 146 | 2628 | 0 | 0 | 0 / 148 |
| S-2 · NL-1 Rotterdam | `g1_add1_af6fca9e3025_s2_rotterdam` | 50 | 900 | 0 | 0 | 0 / 180 |

S-1 uses the Central reference configuration and the first review's four-worker machine configuration. S-2 uses the first NL-1 rectangle, dates, time step and one-worker machine configuration. Both invocations use new run names. The guarded wrapper observes the real candidate plan before horizon execution. Both plans are required to find every requested direction and its existing writer lock in the expected cache. [Guarded runner](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/run_case.py) · [S-1 configuration](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s1-region.json) · [S-2 configuration](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s2-region.json)

S1 frame order, local and UTC labels, frame folder names, per-frame counts, grid metadata and decoded raster pixels are checked against the reference. [Plan](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s1-plan.json) · [Per-frame comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s1-compare.stdout) · [Comparator](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/compare_publications.py)

S2 frame order, local and UTC labels, frame folder names, per-frame counts, grid metadata and decoded raster pixels are checked against the reference. [Plan](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s2-plan.json) · [Per-frame comparison](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s2-compare.stdout) · [Comparator](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/compare_publications.py)

## Acceptance criteria

| Criterion | Verdict | Evidence |
| --- | --- | --- |
| G1-02 | PASS | HK-1 through HK-3 are carried forward with 357 frames and 6,036 comparisons. S-1 covers the Central reference as listed above. [First-review checks](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/first-review-continuity.json) |
| G1-03 | PASS | HK-2 and HK-3 each reused 156 directions and computed zero. The supplement checked 47 main and 3 worktree cache namespaces immediately after S-1. Inventory equality after S-1: True. After S-2: True. [S-1 cache audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/cache-after-s1.json) · [Final cache audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/cache-after-all.json) |
| G1-08 | PASS | The amended reproducibility check is documented above. |
| G1-16 | PASS | B2 combines the original NL-1 engine record with S-2's full-command metering. B3 accepts the development ledger's metered repeat of the checksum check. [Original engine record](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/environment-and-first-nl1.json) · [Supplement ledger](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/ledger.jsonl) |

The other twelve items retain PASS from the first report (G1-01, G1-04, G1-05, G1-06, G1-07, G1-09, G1-10, G1-11, G1-12, G1-13, G1-14, G1-15). The write audit found only the two runs' allowed additions and preserved the protected entries. [Write-scope audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/scope-strict.json) · [Comparison read audit](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/comparison-read-audit.json)

## Supplement ledger

Times are local UTC+08:00. Jobs used `caffeinate -dims` and sleep-inclusive `mach_continuous_time`. For each shade job the supervisor recorded and synced a live RSS sample before releasing the guarded process to read data. It sampled the whole command tree and used Darwin `wait4` for the root process's high-water RSS. Artifact accounting tracks cumulative new logical bytes. [Supervisor](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/meter.py) · [Complete ledger](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/ledger.jsonl) · [S-1 samples](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s1-meter.jsonl) · [S-2 samples](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/s2-meter.jsonl)

| Job | Budget category | Start | End | Wall s | Peak RSS GiB | Peak new GiB | Result |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| s1 | shade | 2026-11-12T12:34:56+08:00 | 2026-11-12T12:46:22+08:00 | 685.88 | 1.623 | 0.239 | exit 0 |
| s2 | shade | 2026-11-12T12:46:23+08:00 | 2026-11-12T12:49:01+08:00 | 157.40 | 0.560 | 0.314 | exit 0 |
| s1-compare | audit | 2026-11-12T12:49:30+08:00 | 2026-11-12T12:50:30+08:00 | 60.23 | 0.279 | 0.317 | exit 0 |
| s2-compare | audit | 2026-11-12T12:50:30+08:00 | 2026-11-12T12:50:49+08:00 | 19.06 | 0.236 | 0.318 | exit 0 |

Shade jobs and their plans used **14.05 / 45 min**. The highest measured whole-command RSS was **1.623 / 12 GiB** and the highest recorded new-artifact total was **0.318 / 10 GiB**. The published-raster comparisons are listed as audits. They read published rasters and local VRT sources. The supplement's candidate computation consists of S-1 and S-2.

The original NL-1 engine computed 180 directions, reported 0.746 GiB peak tree RSS and recorded 1.335 GiB peak new engine artifacts. S-2 measures planning, composition and publication with a warm cache. The original report's resource gap stays documented. [Cold engine evidence](../../outputs/shade_map_g1_review_af6fca9e3025_20261111/evidence_addendum_1/environment-and-first-nl1.json)

## Numerical consistency and limits

Hong Kong has 503 pixel-identical frames and 8,664 matching raster and VRT comparisons across all four regressions.
Rotterdam S-2 reproduces the first NL-1 publication over 50 frames and 900 raster and VRT comparisons with zero differing pixels.

Observational accuracy remains **NOT VERIFIED** for Hong Kong and Rotterdam. Rotterdam surface labels remain **NOT VERIFIED**. The model and input limitations in the first report apply.
