# Sea-support development report — SW-SEA-AC-1.0

Development candidate only. **Independent acceptance is still required.** No
independent acceptance harness, V3, UI, push or PR was run.

Starting HEAD: `374a70df58a1e8faea09c8736b63c1739b30ed41` (Package A), branch
`feature`; A's review was not awaited. Contract SHA-256 verified before work:
`9742e8a34df90c6f5139c3823f53d363cb0fedee9e8905823ba3b7bfb3b66a27`.
Candidate SHA is the immutable local commit containing this report; retrieve it
with `git log -1 --format=%H -- docs/sea/DEVELOPMENT_REPORT.md`.

## Criteria matrix

| ID | Development status | Evidence and commands |
|---|---|---|
| S01 | PASS | `evidence/start.json`, `tools-environment.json`, `dictionary.json`, `extraction.json`, `views.json`, `final-integrity.json`. Engine lock `requirements.lock.txt` unchanged; external environment pinned in `requirements.tools.lock.txt`. All 411 FGDB files and dictionary hashed; scoped supplied DSM source hashes in view manifests. |
| S02 | PASS | Standard pyogrio 0.11.1/OpenFileGDB extraction: total 7,116, LAF 1,111, SEF 345; EPSG:2326 independently checked in engine rasterio. Six invalid geometries deterministically repaired; FIDs, reasons, method and repaired WKB hashes recorded. Export hash `ef8def691f184e58d69bc41b56668f1d3030ed8477442f0570a398b0f7e70194`. `tools/sea_view/extract.py`. |
| S03 | PASS (explained reference differences) | `mask-tests.txt`, `halo-counts.json`, `edge-diagnostic.json`, `edge-point-checks.json`, `edge-summary.json`. Hole/sliver/exact-edge/overlap tests pass. All 60 sampled disagreement centres agree with independent Shapely containment. Detailed count differences below; rasterio centre rule retained. |
| S04 | PASS | `build.py` checks every production output tile on readback: non-fill uint32 bit patterns unchanged, fill exactly float32 1.60, no valid DSM or strict LAF pixel filled, identical grid/CRS/size/type/NoData. `views.json` per-tile checks and hashes; synthetic fill invariant test. |
| S05 | PASS | `views.json`: Cheung Chau 21 supplied + 15 synthetic; Central 35 supplied + 1 synthetic. All missing native cells in scoped target halos examined; only cells with sea centres emitted. Names begin SEA_, no supplied overlap, unchanged `v1.index_sources` admits both views. Lattice/overlap fixture passes. |
| S06 | PASS | `territory-scan.json`, `scan-run.txt`; the one read-only scan completed 3,310 tiles (1,399 coastal). n=2,989,697; p50=1.3690766096 m lies in [1.30,1.90]. All quantiles and coverage below. h remains 1.60. |
| S07 | PASS | `final-integrity.json`; empty src diff and ten pinned files equal 356f611. `views.json` rebuilds reproduce both IDs and every raster hash. New cache namespaces include view_id. `cheung_chau-plan.json`, `central-plan.json`: changed plan/spatial keys; old raw Cheung Chau keys match accepted baseline exactly. Historical output/cache listing unchanged. |
| S08 | PASS | `cheung_chau-result.json`, `cheung_chau-comparison.json`: all 65 original daylight instants, nearest5, same grids/solar references. Zero land shaded→sunlit; zero Quality-1-land violations; zero sunlit losses. All four old/new thresholds identical. Former-Quality-2 transitions reported for every frame. |
| S09 | PASS | `sea-ray-checks.json`: 200 distinct sea pixels at each of 08:30, 12:30, 15:10 HKT, including 119/119/115 near high observed structures. All labels agree with cache-free diagnostic_horizon references; no discrepancy outside equality tolerance. Per-frame water label counts/fractions in `cheung_chau-comparison.json`. Numerical consistency only. |
| S10 | PASS | `sensitivity.json`: h=0/3 m and bands=2.5/5 m, each on the first Cheung Chau tile at 08:30/12:30/15:10. Land and strict-sea label changes and former-Quality-2 recovery reported separately. Production h/tolerance unchanged. |
| S11 | PASS | `central-result.json`, `central-raw-result.json`, `central-comparison.json`. Three instants; zero land shaded→sunlit and Quality-1 violations (also zero sunlit losses). The target grid contains 173,494 filled harbour pixels. Across its scoped view, 204,964 LAF NoData pixels remain unfilled. |
| S12 | PASS | `cheung_chau-helpers.json`, `central-helpers.json`; full 3000×2400 and odd-offset surface windows align exactly. Effective policy resolves SW-V1-POLICY-1.0 + SW-SEA-POLICY-1.0 and exact view_id, with source/manifest hash validation. Helper fixture checks crops, off-lattice rejection and tampering. |
| S13 | PASS | Only two authorized production scopes and four one-target diagnostics. No territory view. `ledger.json` records all measured work below 60 min real jobs, 30 min scan, 12 GiB memory and 20 GiB artifacts; final totals below. |
| S14 | PASS | `.venv/bin/python -m pytest -q`: 99 passed (73 original + 20 Package A + 6 Package B), `full-tests.txt`; existing tests unchanged. External geometry fixture checks in `geometry-tests.txt`. POLICY/GUIDE/DESIGN cover identity and limitations. `evidence/manifest.json` enumerates small evidence. One local commit, no generated rasters/caches/views committed. |

## Production view identities

- Cheung Chau: `a3c26a13169456eb99cdc7e860f29902a1ba4b80c1d6b5967a5d591b589dd74e`.
- Central: `6dc631fdb6d57927ef978019e0c704b4437e74c7d04eeb4b46b18c5e3b54d7cc`.

Both reside under `data/processed/dsm_views/sea_fill_v1/<view_id>/` with `tiles/`,
`surface/` and `manifest.json`. Run caches are
`data/processed/shade_v1/sea_fill_v1_<view_id>`. View hashes include the manifest
content excluding its own ID and timestamp fields; timestamps are not written.
Rebuilds checked both manifest equality and all tile/surface SHA-256 values.

## Rasterization difference evidence

| Frozen halo count | Planning diagnostic | Rasterio centre rule | Relative difference |
|---|---:|---:|---:|
| DSM NoData | 34,647,367 | 34,647,367 | 0% |
| NoData in sea minus land | 34,617,537 | 34,619,684 | +0.00620% |
| NoData in LAF | 29,830 | 27,683 | -7.19745% |
| Valid DSM in sea minus land | 357,470 | 369,063 | +3.24307% |

The planning check used PIL; the frozen production rule uses rasterio pixel
centres. A conventional PIL pixel-edge polygon burn on the same standard-reader
geometries produces 29,292 NoData-in-LAF and 356,648 valid-in-sea pixels and
15,320 land-mask disagreements with rasterio. This reproduces the direction and
most of the edge effect, not the exact unavailable original planning renderer.
The remaining difference is not hidden or tuned away. Sixty stratified samples
cover both disagreement directions and valid/NoData targets; all centre classes
agree with Shapely point containment. Maximum sampled distance to the LAF
boundary is 0.412 m, less than one pixel. S03's explicit explained-difference
route is used; independent review should inspect this evidence.

## Read-only territory scan

Exact linear percentiles in metres: p5=0.8679426312, p25=1.1325498819,
p50=1.3690766096, p75=1.6872034073, p95=3.9022360802. The scan preserves each
native grid and records all four shifted-origin filenames. No tile is corrected.
The one-pixel halo uses unchanged native addressing; adjacency includes
no-source sea support at catalogue boundaries. Footprint coverage is a sum over
supplied native grids: 48,642,752 pixels (12,160,688 m²) are in neither class.
A territory view would require 1,421 synthetic cells / 2,545,158,876 sea pixels;
these are counts only. No such view was built. Scan elapsed 536.990 seconds,
peak RSS 401,391,616 bytes, against 1,800 seconds and 12 GiB.

## Resources, assumptions and limitations

Final ledger totals: **1369.589 seconds / 3600** real-job time; **536.990 seconds / 1800** scan time; **1,680,687,104 bytes / 12 GiB** peak sampled process-tree RSS. Exact final artifact and external tools-environment byte totals are in `evidence/ledger.json` (both well below 20 GiB). It includes both
strict view builds and rebuilds, raw/view runs, comparisons, reference checks,
and all diagnostic builds/runs. The separate scan has its own 30-minute ceiling.
Halo/PIL checks were measured with process high-water RSS; subsequent child jobs
were monitored as process trees after confirming inspection permissions, with
termination margins before 60 minutes, 12 GiB and 20 GiB. Package installation,
FGDB/PDF inspection, authoring and synthetic tests are not real-DSM jobs. External
tools-environment disk use is reported separately. Raw data is never copied into
new download locations or changed.

Assumptions and review notes:

1. The new-directory-only restriction applies to runtime data; explicitly
   requested tools/tests/docs and the root tools lock are authorized deliverables.
2. "Existing outputs/caches" means pre-task historical files. Task-owned new
   directories may receive their own immutable artifacts and evolving ledgers.
3. Target halos are not recursively expanded through newly included support
   tiles. This follows S05's scoped-target wording and keeps the scope bounded.
4. Raw comparison catalogues are symlink views containing every relevant raw
   halo source. Four distant shifted-origin tiles remain untouched and outside
   these scoped catalogues. Raw Cheung Chau scientific keys match the accepted
   historical result, proving the comparison uses the same dependencies.
5. Optional JPG/MP4 outputs from the historical Cheung Chau run are disabled per
   the scientific-only instruction. The 65 dates/instants, nearest5, grids and
   per-tile solar references match. V2 concurrency is two; engine science remains
   single-worker per request. Diagnostic batches use one worker.
6. All six invalid polygon repairs use the pinned GEOS make_valid followed by
   deterministic polygon-component retention. No custom FGDB parser is used.
   Exact original PIL planning implementation is unavailable; reference count
   differences are documented rather than treated as exact reproduction.
7. Source metadata may be scanned for indexing without computing a territory
   statistic. Only one territory pixel scan was run; its guard prevents repeats.
8. S09's reference is diagnostic_horizon, expressly permitted by the contract,
   at the engine's nearest5 direction. It is independent of the cached output
   path, not an observational or unbinned astronomical reference. Near-structure
   means within 8 m of a DSM-observed surface at least 10 m high.
9. Diagnostic bands measure Euclidean distances between native pixel centres,
   extend strict sea into LAF only, and never extend into neither-class areas.
   Diagnostics use SW-SEA-DIAGNOSTIC-1.0 and separately labelled directories and
   caches; they do not change SW-SEA-POLICY-1.0.
10. Class 0 is observed DSM, not a legal land boundary: observed intertidal or
    other mapped-water structures remain class 0 and participate in the land
    regression exactly as specified. Quality-1/class-0 intersections are zero
    in these comparisons; that subgate is explicitly vacuous, not omitted.
11. The external tools environment lives in `/private/tmp/shade_watch_tools_20261029`
    and may be cleared by the OS. Its pinned lock and environment record permit
    recreation. Initial restricted installation found no distributions; the
    expressly allowed package-only network installation succeeded without
    modifying engine dependencies or downloading DSM/map data.
12. Protected planner/user files were neither edited nor staged. Two presentation
    preview files drifted externally (one lock removed, one log changed), as in
    Package A. They remain outside this commit. Other parallel work's new
    `docs/prompts/runner`, `docs/ui`, WSL smoke docs/tools are also left untouched.

Boats/pontoons are absent; tide is not modelled; 2026 map versus 2019–20 DSM
reclamation drift remains possible. LAF piers/slivers stay unknown; reservoirs
are unchanged. Sea-target labels are less certain than land labels. Shade is
not cooling or ΔT. Land and sea observational accuracy remain NOT VERIFIED.
No release or V3 use is authorized by this development result.
