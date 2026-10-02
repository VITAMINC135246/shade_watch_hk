# V1 independent acceptance — 796ac8a

**Gate: ACCEPTED. A01–A14 are all PASS.** No reproducible violation of the frozen
contract was found. This is bounded engineering acceptance; real-world
observational accuracy remains **NOT VERIFIED**. Large local directional errors
are reported below and are not covered by the numerical-consistency tolerance.

Review completed 2026-10-03, Asia/Hong_Kong, in the independent acceptance chat.
The reviewer authored the independent harness and report, and did not implement,
patch, tune or commit production code or change developer tests.

## Immutable candidate, contract and isolation

| Item | Recorded identity |
| --- | --- |
| TARGET_COMMIT | `796ac8abf05b92f1fbbac23a4aa0f18c9d944101` |
| Planning baseline | `7c56760c854cb1e5138c8381a7b68d543b68cdef` |
| Contract | `SW-V1-AC-1.0` |
| Contract SHA-256 | `04e205a87390fe606fc1b61c25aa774413e1cdf41a91be0b9df77eb107e38d31` |
| Frozen held-out manifest SHA-256 | `53c30c787ddf37dd2da953d7c46124344527d073efac2fc4b3fb5064fcf1a450` |
| Manifest frozen UTC | `2026-10-02T14:00:14.526924+00:00`, before acceptance outcomes |
| Environment | macOS 15.7.4 arm64; project Python 3.12.5; 10 logical CPUs; 24 GiB RAM; one production process/worker |
| Evidence and harness | `outputs/v1_independent_acceptance_796ac8a/` |
| New scientific cache | `data/processed/shade_v1/acceptance_796ac8a/` |

The checkout was evaluated directly after verifying every one of the **50 tracked
files** against the bytes of TARGET_COMMIT. The final verification still matches
all 50, and HEAD still identifies that candidate. The contract hash matches the
pre-implementation hash supplied in the handoff. Initial untracked
`docs/prompts/v2/`, `docs/prompts/v3/` and `presentations/` were preserved.

All **123 original raw files** were independently SHA-256 hashed before and after
the review. All hashes match, including all 19 DSM GeoTIFFs. **6,577 existing
protected files** in raw data, prior processed data/caches, prior outputs and
presentations retain their size/mtime signatures. No original DSM, historical
output/cache or `heat_index_urop` was modified. Only isolated review artifacts
and this new report were written; large generated artifacts remain ignored.

Evidence: [initial provenance](../../outputs/v1_independent_acceptance_796ac8a/evidence/initial_provenance.json),
[complete input identities](../../outputs/v1_independent_acceptance_796ac8a/evidence/input_identities.json),
[environment and installed versions](../../outputs/v1_independent_acceptance_796ac8a/evidence/environment.json),
[final protection/source audit](../../outputs/v1_independent_acceptance_796ac8a/evidence/final_protected_audit.json).
The three numerical held-out sources are 11NE10D
(`f229f8b15f4d309b674bc3d85470079e109f84fd304ee1d4cec799105f9a2103`),
11NE5D (`1ed3fd697de4ae40aefe60ef6508777c782a39183c1fa7d6a17968aad20311c9`),
and 12NW6C (`355cf62f7642115fc7bde3b8646ba71024abf18500ef12a3c2b7b07a18dfefe3`).
Full filenames, transforms, bounds, NoData and all other source identities are in
the linked manifests and [DSM inventory](../../outputs/v1_independent_acceptance_796ac8a/evidence/dsm_inventory.json).

## Frozen independent cases

Selection seed/identifier: `79620261002`. The reviewer chose seasonal dates and
deterministic offsets on three tiles outside the developer's numerical sample
tiles. An input-only DSM overview and coastal validity mask established scene
coverage; no model output was used for selection. The windows have no overlap
with the developer's declared windows. DSM texture supports rough-surface
coverage; no registered land-cover or canopy truth is claimed.

| Window | Native source | Column, row, width, height | EPSG:2326 bounds: west, south, east, north | Coverage rationale |
| --- | --- | --- | --- | --- |
| W1 | 11NE10D | 983, 607, 24, 20 | 844741.5, 821886.5, 844753.5, 821896.5 | Urban roof/building edges; 480/480 valid |
| W2 | 11NE5D | 713, 361, 24, 20 | 844606.5, 823209.5, 844618.5, 823219.5 | Rough/vegetated ridge texture; 480/480 valid |
| W3 | 11NE10D | 151, 901, 24, 20 | 844325.5, 821739.5, 844337.5, 821749.5 | Hillslope; 480/480 valid |
| W4 | 12NW6C | 1201, 111, 24, 20 | 845600.5, 822134.5, 845612.5, 822144.5 | Coastal NoData boundary; 224/480 valid |
| W5 | 11NE10D | 1489, 613, 11, 20 | 844994.5, 821883.5, 845000, 821893.5 | West side of native/reference boundary; 220/220 valid |
| W6 | 12NW6C | 0, 613, 13, 20 | 845000, 821883.5, 845006.5, 821893.5 | East side of same boundary; 260/260 valid |

| Case | Window | Exact requested timestamp |
| --- | --- | --- |
| H01 | W1 | `2026-02-11T07:43:19+08:00` |
| H02 | W2 | `2026-02-11T15:47:53+08:00` |
| H03 | W3 | `2026-04-17T09:23:41+08:00` |
| H04 | W4 | `2026-04-17T18:11:37+08:00` |
| H05 | W5 | `2026-07-09T07:05:29+08:00` |
| H06 | W6 | `2026-07-09T13:26:11+08:00` |
| H07 | W1 | `2026-08-23T17:48:31+08:00` |
| H08 | W2 | `2026-10-13T06:13:47+08:00` |
| H09 | W3 | `2026-10-13T10:37:43+08:00` |
| H10 | W4 | `2026-12-05T16:51:17+08:00` |
| H11 | W5 | `2026-12-05T23:17:13+08:00` |
| H12 | W6 | `2028-02-29T11:52:37.123456+08:00` |
| H13 | W1 | `2028-02-29T03:52:37.123456Z` |

These are 13 input timestamps, 12 physical instants, and seven dates across all
seasons. H08 and H11 are below the apparent horizon; H04/H01/H10 include low sun.
H12/H13 are an equivalent UTC/HKT pair. Additional same-window public requests
verify that pair, and a one-second change verifies different recorded solar
parameters. The frozen manifest also declares directions 92.49°, 92.5°, 92.51°,
272.49°, 272.5°, 272.51°; cross-date reuse on 2026-02-12; and the real workload
budget. No policy, default, threshold or case was tuned after observing results.

Evidence: [frozen manifest](../../outputs/v1_independent_acceptance_796ac8a/evidence/heldout_manifest.json),
[input-only scene overview](../../outputs/v1_independent_acceptance_796ac8a/evidence/input_scene_overview.png).

## A01–A14 decisions

The [requirement audit](../../outputs/v1_independent_acceptance_796ac8a/evidence/requirement_audit.json)
maps implementation functions and developer claims to independent additions.
All PASS rows below rely on actual checks; developer results alone did not
establish any acceptance criterion.

| ID | Result | Expected and independently observed behavior | Evidence / limitation |
| --- | --- | --- | --- |
| A01 | PASS | Exact candidate/contract/input identity and isolation. All 50 tracked files and 123 raw hashes match; 6,577 protected file signatures unchanged. | [Final audit](../../outputs/v1_independent_acceptance_796ac8a/evidence/final_protected_audit.json), [initial provenance](../../outputs/v1_independent_acceptance_796ac8a/evidence/initial_provenance.json). Historical files use signature checks; raw files use content hashes. |
| A02 | PASS | Executable public instant, list and multi-date APIs/CLI. Planning traps every horizon call and creates zero paths, including when JPG/MP4 requested. | [Planning](../../outputs/v1_independent_acceptance_796ac8a/evidence/planning.json), [actual commands](../../outputs/v1_independent_acceptance_796ac8a/evidence/commands.json), [CLI readback](../../outputs/v1_independent_acceptance_796ac8a/evidence/supplement.json). |
| A03 | PASS | Arbitrary exact times/seconds, zones and leap date preserved; recorded solar geometry derives from requested instant and canonical tile reference. Independent selected-model differences <1e-9°; equivalent UTC/HKT arrays/solar parameters identical; +1 second changes parameters. | [Solar provenance](../../outputs/v1_independent_acceptance_796ac8a/evidence/solar_provenance.json), H01–H13 raw outputs. Astronomy accuracy assessed separately. |
| A04 | PASS | Native selector coordinates and source geometric bounds/centre retained; explicit custom bounds expand to lattice. Out-of-bounds crop, duplicate/nonrectangular selections reject clearly; uncovered custom pixels remain 255/1. | [Selector](../../outputs/v1_independent_acceptance_796ac8a/evidence/selector.json), [operations](../../outputs/v1_independent_acceptance_796ac8a/evidence/operations_summary.json), [invalid inputs](../../outputs/v1_independent_acceptance_796ac8a/evidence/synthetic_results.json), [uncovered custom area](../../outputs/v1_independent_acceptance_796ac8a/evidence/supplement.json). |
| A05 | PASS | Same shade/quality pixels identical alone, in full two-tile output, odd-offset crop (983,607), and aligned custom output. Canonical continuous horizon/support/blocker arrays match exactly: 0° difference. | [Operations](../../outputs/v1_independent_acceptance_796ac8a/evidence/operations_summary.json), [continuous arrays](../../outputs/v1_independent_acceptance_796ac8a/evidence/continuous_invariance.npz). Solar-reference boundary is measured separately below. |
| A06 | PASS | Missing support cannot certify sunlit; known blocker can prove shade; target NoData and night retain reasons. Controlled public flat scene gives 255/2, added known blocker 1/0, missing target 255/1. Equality, threshold and nighttime priorities agree with independent decisions. | [Synthetic controls](../../outputs/v1_independent_acceptance_796ac8a/evidence/synthetic_results.json), [coastal H04](../../outputs/v1_independent_acceptance_796ac8a/evidence/heldout_H04.json), H08/H11. No missing height is filled as zero. |
| A07 | PASS | Direction-level reuse across dates/ranges; only missing directions calculated. Instrumented cross-date query calls kernel 0 times; new direction 1; two-tile composition reuses 1 and computes 1; crops reuse 0-call entries. | [Cross-date](../../outputs/v1_independent_acceptance_796ac8a/evidence/cross_date.json), [new direction](../../outputs/v1_independent_acceptance_796ac8a/evidence/new_direction.json), [combination](../../outputs/v1_independent_acceptance_796ac8a/evidence/combined_native.json). Counts verified by a wrapper on actual kernel calls; final hits counted separately. |
| A08 | PASS | Relevant changed/removed/new neighboring sources, masks, algorithm/numerical identity changes and corruption invalidate; distant additions/changes and relocation retain reuse. Fresh removed-source domain recomputes; restored exact prior domain legitimately reuses its valid old entry. | [Synthetic actual job counts](../../outputs/v1_independent_acceptance_796ac8a/evidence/synthetic_results.json), raw `dep_*.json`, `mask_*.json`. Fixtures/copies only; no source or numerical-code edits. |
| A09 | PASS | Reviewer oracle validated analytically before real comparisons. Main 4,768 finite pairs have maximum error 3.8126881e-6°; support and finite masks exact; shade/quality agree outside declared equality neighbourhood. All actual public nearest5 arrays match independent classification of independently checked horizons. | [Independent oracle](../../outputs/v1_independent_acceptance_796ac8a/oracle.py), [numerical cases](../../outputs/v1_independent_acceptance_796ac8a/evidence/numerical.json), `arrays_H*.npz`, [analytic controls](../../outputs/v1_independent_acceptance_796ac8a/evidence/synthetic_results.json). Real equality count 0; synthetic equality counts reported below. |
| A10 | PASS | Existing nearest5, nearest2_5 candidate and unbinned directions compared on held-out real windows, plus bin-boundary rays and narrow synthetic obstacle. Errors, denominators, masks, quality, examples, runtime and storage disclosed. | [Full numerical evidence](../../outputs/v1_independent_acceptance_796ac8a/evidence/numerical.json), [summary](../../outputs/v1_independent_acceptance_796ac8a/evidence/numerical_summary.json), [frozen policy](POLICY.md). No undeclared accuracy threshold applied. |
| A11 | PASS | Native 1200×1500 scientific output and 1200×3000 combination retain 0.5 m/EPSG:2326 alignment, labels, NoData, quality and exact-time tags. JPG-only and MP4-only are independent; decoded order/frame count/seconds captions correct. Memory bounded and sampling gaps explicit. | [Native trial](../../outputs/v1_independent_acceptance_796ac8a/evidence/cold_0.json), [media/readback](../../outputs/v1_independent_acceptance_796ac8a/evidence/supplement.json), [ledger](../../outputs/v1_independent_acceptance_796ac8a/evidence/ledger.json). Media is lossy; authoritative rasters are lossless. |
| A12 | PASS | Actual isolated child terminated after one complete direction; restart reuses completed entry unchanged and recomputes partial entry. TIFF/JSON/final-raster corruption repaired; second process rejects conflicting writer. Original 53 tests pass. Legacy command actually runs 65 real frames plus decoded video in new paths. | [Recovery](../../outputs/v1_independent_acceptance_796ac8a/evidence/recovery.json), [second process/legacy readback](../../outputs/v1_independent_acceptance_796ac8a/evidence/supplement.json), [regression log](../../outputs/v1_independent_acceptance_796ac8a/evidence/regression_tests.txt), [legacy inventory](../../outputs/v1_independent_acceptance_796ac8a/evidence/legacy_smoke.json). V2 durable orchestration not required. |
| A13 | PASS | Three empty-direction-cache native queries versus three identical warm-direction/new-output queries; median 10.129435 s versus 0.502049 s. Each cold computes exactly 1, each warm reuses 1 with 0 final hits; final-result hit separately 0.290838 s. | [Benchmarks](../../outputs/v1_independent_acceptance_796ac8a/evidence/benchmarks.json), `cold_*.json`, `warm_*.json`, raw event logs. First cold overlapped synthetic recovery; other pairs isolated. JIT/filesystem conditions and phase measurements below. |
| A14 | PASS | Immutable candidate contains code/tests, usable API/CLI examples, frozen scientific policy, migration/limitations, development report/traceability and handoff. Independent commands, harness, arrays, hashes and resource ledger retained; large artifacts ignored. | [Guide](GUIDE.md), [policy](POLICY.md), [development report](DEVELOPMENT_REPORT.md), [acceptance evidence inventory](../../outputs/v1_independent_acceptance_796ac8a/evidence/manifest.json). No push/merge/PR or next-version work. |

## Software correctness and numerical consistency

Existing tests: **53 passed**, 228 dependency warnings, 8.06 seconds; no tests or
goldens were altered. Independent public Python/CLI requests exercised an instant,
explicit list and four-frame real sequence at 12:00/18:00 on 2026-04-17 and
2026-10-13. Frames are streamed; the implementation caps requests at 512 frames,
limits local output/tile sizes and processes one native tile at a time. No array
proportional to full-year frame count or entire combined DSM was introduced.

The independent [oracle](../../outputs/v1_independent_acceptance_796ac8a/oracle.py)
imports no production/test horizon or classifier. It independently places masked
DSM source windows, samples canonical pixel rays, reduces slopes/support, uses a
scalar classification decision tree and calculates solar vectors. Analytic
expectations establish parity-dependent first-hit distances of 0.25/0.5 m,
inclusive radial cutoff, exclusion of an out-of-radius diagonal cell, and
missing/known-blocker/equality/night behavior before real numerical comparisons.
Random scenes add 49 target/direction pairs, 42 finite and seven missing targets;
all support/blocker distances and finite masks match, angle errors ≤3.5568e-6°.

Remaining shared assumptions are the adopted DSM ray model, float32 height
subtraction, 0.25 m nominal slope denominator, ties-to-even canonical-address
parity, near-cardinal snapping and nominal/cell-centre 1000 m cutoff. Independent
implementation does not make these physical assumptions observational truth.

Main real comparisons contain **5,280 target/direction pairs**, **4,768 finite**
and **512 missing targets**. None is hidden: masks are compared over all 5,280;
support mismatches are zero; numerical errors use the 4,768 common finite pairs.
Classification comparisons include all pixels and nighttime. The additional six
unbinned half-bin-boundary directions contain 2,880 finite pairs and also meet
1e-4° exact-direction tolerance. The main real equality neighbourhood has 0/4,768
finite pairs. Synthetic classification controls contain 24 comparisons, 20
finite: 7 equality-neighbourhood comparisons, of which six are in the two
positive-elevation cases (6/10 finite); strict `horizon > elevation` is retained,
with nighttime priority. Equality counts are reporting categories, not snapping.

## Direction and solar approximations

The table compares with independent direct unbinned rays. Shade/quality rates use
all 5,280 pixels, including 512 invalid and 700 valid nighttime pixels. The
daylight denominator is 4,580 total / 4,068 finite; the 31 and 19 shade differences
are respectively 0.762% and 0.467% of daylight finite pixels. Errors use finite
angles only; finite-mask disagreement is zero for every method.

| Method | Mean / p95 / max absolute horizon error | Shade differences / 5280 | Quality differences / 5280 | Support differences / 5280 | Sum of 13 window calls incl. input I/O |
| --- | --- | --- | --- | --- | --- |
| direct | 0.000000993 / 0.000003057 / 0.000003813° | 0 | 0 | 0 | 1.754 s |
| nearest5 | 0.680083 / 3.731221 / 40.390782° | 31 (0.587%) | 2 (0.038%) | 39 | 1.686 s |
| nearest2_5 | 0.395419 / 2.328792 / 32.121699° | 19 (0.360%) | 2 (0.038%) | 16 | 1.681 s |

Errors concentrate spatially. On H03/W3, native pixel (column 168,row 917),
the direct horizon is 60.633465° while nearest5 gives 20.242683°: shaded becomes
sunlit. H03 has 20 nearest5 label differences versus seven nearest2_5. On
H02/W2, pixel (722,369), nearest2_5 differs by 32.121699°; both labels happen to
remain shaded. H02 has nine nearest5 disagreements and ten nearest2_5, so denser
sampling does not improve every case. Arrays and georeferenced error examples
are retained per case in `numerical.json` and `arrays_H*.npz`.

A one-cell synthetic obstacle at 91.25°, approximately 200 m away, gives a
26.565052° direct horizon but 0° at both 90° and 92.5°. Both finite tables miss it.
V1 retains the documented nearest5 default and explicit denser/direct alternatives;
no acceptance threshold for approximation error was agreed. **A10 PASS means the
comparison is complete and honest, not that 5° spacing is accurate enough for a
particular physical use.** One native three-band directional array is 21,600,000
uncompressed bytes; nominal full tables have 72 versus 144 entries. Direct is
on-demand, not a finite annual table. Actual one-direction benchmark namespaces
used 8,820,308 bytes each, including entry metadata/lock. No full table was built.

Correct selected-model invocation and astronomical model difference are separate:
all recorded fractional-year parameters match the independently transcribed
selected equations within 1e-9°. Against the separate NOAA Julian-century/Meeus
equations, maximum geometric-elevation difference is **0.359640°** and azimuth
difference **0.655681°**. Primary references:
[NOAA fractional-year equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF),
[calculator/refraction details](https://gml.noaa.gov/grad/solcalc/calcdetails.html),
[calculator source](https://gml.noaa.gov/grad/solcalc/main.js).
The primary pages were browsed; direct shell fetching was DNS-blocked and web
extraction rejects JavaScript. For coefficient inspection, the existing archived
NOAA source was copied read-only, not the developer's oracle. Its SHA-256 is
`3832956f24724eafacf9e18173b9299b1554d6252bed0784d9c9aca6d9f54856`;
[source provenance](../../outputs/v1_independent_acceptance_796ac8a/evidence/astronomy_sources.json)
records this limitation. These are model comparisons, not measured sky accuracy.

Across the studied canonical boundary, fixed tile-centre apparent-elevation jumps
reach **0.007461°**, versus **0.000004974°** between adjacent per-pixel references.
Centre/per-pixel differences reach **0.003743°** at these boundary pixels. Fixed
thresholds are 17.962283° for 11NE10D and 23.551936° for 12NW6C: a 5.589653°
policy difference. Extent invariance demonstrates stable ownership, not absence
of reference-boundary discontinuity. These are explicit, frozen approximations.

## Performance, recovery, output integrity and resources

Matched benchmark: 11NE10D, complete 1500×1200 native tile,
`2026-02-11T15:47:53+08:00`, nearest5 → 235°, shade+quality only, JPG/MP4 disabled.
Each cold namespace had no scientific direction entry. Warm trials use fresh
output directories, so all are scientific queries rather than final-image hits.

| Phase, median of three | Empty direction cache | Warm direction cache |
| --- | ---: | ---: |
| Planning, separately measured | 0.297066 s | 0.341478 s |
| Run preprocessing/input recheck | 0.287204 s | 0.289282 s |
| Horizon work / cache validation | 9.676111 s | 0.050099 s |
| Actual kernel calculation | 8.384054 s | 0 s |
| Classification | 0.013736 s | 0.013823 s |
| Output/compression/readback/hash | 0.151080 s | 0.147719 s |
| Scientific run total | **10.129435 s** | **0.502049 s** |

Individual cold run totals: 9.840212, 10.129525, 10.129435 s; warm totals:
0.494351, 0.502049, 0.508084 s. A separate final-result hit is 0.290838 s.
Synthetic JIT preload was used; the first acceptance process built its isolated
Numba cache, which later processes could load. Filesystem caches were not flushed.
Cold_0 overlapped roughly 0.9 seconds of an isolated synthetic interruption and
recovery probe; cold_1/cold_2 and subsequent real jobs had no campaign overlap.
No real DSM jobs overlapped. Process/JIT/storage effects limit extrapolation;
this proves the contracted local median comparison, not territory scaling.

Recovery terminated only the review child (return code -15) after a complete
entry was durably published, leaving an explicitly incomplete second entry.
Restart computed one and reused one; the completed raster checksum did not
change. Corrupt TIFF/JSON entries recomputed, damaged final raster recomposed
without a new horizon call, and a separate writer process exited 7 with the
cache-lock rejection. These are actual executions, not simulated success flags.

Independent readback checked dimensions, CRS, transforms, nodata, labels, tags,
quality/validity correspondence and scientific resolution. JPG-only contains one
image and no MP4; MP4-only contains no JPG and two decoded frames in exact requested
order. JPG and decoded frames visibly preserve the HKT seconds captions and
ownership attribution. The two MP4 scientific map regions have mean display-grey
errors 0.402/1.381 on a 0–255 scale, maximum 39/5, showing expected lossy media
effects; the GeoTIFF labels remain authoritative. The unmodified legacy command
ran **65 real 24×20 rasters**, quality maps, native-resolution PNGs and a video
independently decoded to 65 frames. Versioned solar/parity/threshold/custom-grid
changes are documented in [POLICY.md](POLICY.md), rather than treated as regressions.

Budget was declared before execution: planned 900 s real work with 1,800 s reserve,
ceiling 2,700 s; one production worker; 8 GiB combined memory; 10 GiB artifacts;
disk preflight approximately 1.8 TiB free. Actual [ledger](../../outputs/v1_independent_acceptance_796ac8a/evidence/ledger.json):

- **260.043 seconds (4 min 20 s)** cumulative across 53 bounded real jobs,
  including native trials, planning inside jobs, held-outs, numerical diagnostics,
  four-frame real sequence, CLI and legacy execution/validation.
- Sampled per-job maximum tree RSS **622.422 MiB**; conservative sum of overlapping
  job peaks **852.641 MiB**, below 8 GiB. At most two scientific jobs (one real plus
  synthetic recovery); at most one real DSM job and one production worker.
- Approximately **194 MiB** of new artifacts including fixtures, arrays,
  scientific caches, all outputs and logs, below 10 GiB.

Memory is sampled every 20 ms. The local sandbox blocks system-wide PID
enumeration, so the harness samples parent and its known child/media PIDs.
Legacy separately tracked both encoder and decoder; outer-parent RSS plus its
reported tree peak supplies a conservative bound. There is no separate media-only
maximum, and sub-20-ms spikes are not guaranteed captured. Metadata inventory,
input-only visualization and standalone output inspection are not DSM calculation
jobs. No budget ceiling was approached, and no missing required check was replaced
with synthetic-only evidence.

## Defects, limitations and reproduction

**Reproducible contract defects: none found.** No production repair was made or
requested. The stated developer contract-level claims were checked with new
evidence; its exact timing/error numbers describe different development samples
and are not reused as acceptance measurements. Observational/physical accuracy,
subpixel accuracy, whole-Hong-Kong readiness and annual scaling remain unsupported
by this local acceptance.

Reviewer-harness corrections are retained transparently: the initial analytic
cutoff expectation was corrected before real outcomes (the odd-address boundary
cell is first sampled at 2.0 m, not 1.75 m); PID enumeration was replaced by known
PID sampling; an inspection-only ImageIO `list(reader)` length-hint MemoryError
was corrected to iteration. Neither production implementation nor the frozen
cases/tolerances changed. `synthetic_attempt_1.log` and media inspection notes are
preserved. Original first warm_2 timings were saved in `benchmarks.json` before
the same directory was used for a separate final-hit trial; the clearly labeled
`warm_2_first_scientific_snapshot.json` reconstructs that original summary.

Harness stages actually run, from the project root with the project Python:

```sh
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python -m pytest -q --disable-warnings -o cache_dir=outputs/v1_independent_acceptance_796ac8a/pytest_cache --basetemp outputs/v1_independent_acceptance_796ac8a/regression_tmp
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py synthetic
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py benchmarks
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py interruption
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py operations
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py numerical
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/acceptance.py cli
PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR=outputs/v1_independent_acceptance_796ac8a/numba_cache .venv/bin/python outputs/v1_independent_acceptance_796ac8a/supplement.py
```

The retained campaign intentionally refuses populated cold namespaces. Do not
rerun destructive fixture/corruption stages over original evidence. A fresh
reproduction copies the harness/manifest to new review-owned locations, changes
only `OUT`, `CACHE` and the supplement import routing, starts a new ledger and
retains the candidate/cases/scientific settings. Native/API/CLI commands and
arguments are saved verbatim in `commands.json`; every plan/result includes
source dependencies, timestamp and requested/resolved geometry.

Raw evidence inventory with hashes is
[manifest.json](../../outputs/v1_independent_acceptance_796ac8a/evidence/manifest.json).
Report is shareable independently; large local arrays/rasters remain in the
isolated evidence directories. Suitable registered observations were unavailable,
so real-world validation is **NOT VERIFIED**, separately from the **ACCEPTED**
A01–A14 engineering gate. Any future repair must supply a new full candidate SHA
and preserve this evidence; any accuracy tuning must use an additional untouched
validation set. No V2/V3 progression or deployment is authorized by this report.
