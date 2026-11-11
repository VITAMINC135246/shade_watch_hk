# Package G1.0 — static pre-check of candidate `af6fca9` (2026-11-11)

Written by the planning conversation (Claude), through the linked computer. This is a static pre-check before independent acceptance. It is not an acceptance. No test was run, no real-DSM job was run, and no raster was compared. Numbers quoted from the developer are marked as such.

## Candidate

- `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d`, branch `feature`, committed 2026-11-11 23:02:34 +0800, one local commit, not pushed.
- Parent `35314377986fcb9551db288a62b74d3b743121ef` (the G1.0 freeze commit). Contract SHA-256 `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef`, as recorded in the development report.
- 84 files changed, 20,940 insertions and 194 deletions. Code, tests and config: 29 files, 1,528 insertions and 194 deletions. The rest is `docs/city/` (3 documents and 49 evidence files) and three documentation additions.
- Developer's identifiers: `ingest_id` `7272bb1ae35aa4f04e78b50d0f72548caae1bee8b7d36bbb1760565aab4bd634`; Rotterdam `view_id` `4b2c2e76ca8b7d5ee56932deb3c8197471b5d16f6164e8c50024e1ed805be843`.
- Developer's self-assessment: PASS for G1-01 to G1-06, G1-13 and G1-15; NOT VERIFIED for G1-07 to G1-12, G1-14 and G1-16 (the reviewer-only parts, the water stratum of G1-14, and one unmetered job).

## What was checked, and the result

| Check | Result |
| --- | --- |
| Changed paths against the allowed-file list | All inside the list, with two exceptions that are contract errors: findings 1 and 2. |
| Twelve files that must stay byte-identical | All twelve SHA-256 values equal the contract. |
| `docs/prompts/`, `docs/planning/`, `config/sea_profiles/hk_cedd_2020.json`, `config/schema/sea_profile.schema.json`, `config/regions/cheung_chau.json` | No change. `src/v2_state.py` is also unchanged. |
| City profiles and Rotterdam fill profile | Parsed JSON equals the three JSON blocks of the contract. |
| `docs/OUTPUT_CODES.md` | Nine added lines, none removed. |
| Protected trees against the planner baseline (`G1_BASELINE_20261111.md`) | All 222 baseline units present with the same digest. No unit missing. 28 new units, all in allowed locations (list below). |
| User's files (261 hashed at baseline) | All identical at the time of the pre-check. |
| Hong Kong view and its cache namespace | Units `dsm_views/sea_fill_v2_2/8ee51b01…`, its pointer, its lock and `shade_v1/sea_fill_v2_2_8ee51b017411` have unchanged digests. |
| Engine diff (`src/v1.py`, `solar.py`, `v2.py`, `v2_runner.py`, `v2_worker.py`) | New optional inputs with Hong Kong defaults; no changed default; JPG and MP4 rejected for other cities; the time-zone tag is added only for other cities. One point for the reviewer: finding 5. |
| `tools/region_request.py`, `tools/sea2/fill_impact.py` | Changes are the city's CRS, time zone, daylight reference, source line and catalogue. Within design item 6. |
| Package F time labels | `tools/shade_map/config.py` keeps the fixed UTC+8 clock for `hong_kong` and uses the IANA zone for other cities. Config 1.0 defaults to `raw`, 1.1 to `sea-2.2`. |

New units since the baseline (14,018 files and links, 4.68 GB):

- `data/processed/dsm_catalogues` (163 files);
- in `data/processed/dsm_views/sea_fill_v2_2/`: the view `4b2c2e76…` (577 files), `current-nl_rotterdam_dsm05.json`, `build-nl_rotterdam_dsm05.lock`;
- cache namespaces `shade_v1/g1_dev_raw_20261111`, `g1_dev_raw_20261111_rotterdam`, `sea2_2_fill_impact_4e4d45dfd153`, `sea_fill_v2_2_4b2c2e76ca8b`;
- `outputs/shade_map_g1_dev_20261111` (10,677 files);
- seven work folders and seven locks `g1_dev_{hk1..hk4,nl1..nl3}` in `outputs/shade_map_work/`; three new entries in `outputs/region_views/`; one work folder and one lock `g1_dev_nl1` in `outputs/sea2_2_diagnostic_work/`.

## Extra check: the rewritten daylight functions

`src/solar.py` changed more than a parameter: `daylight_bounds` now scans in UTC, and `daylight_samples` was rewritten to walk the local wall clock with fold handling. The pre-check compared the old and the new file directly, without the engine:

- Hong Kong reference (22.3° N, 114.2° E), every day from 1940-01-01 to 2040-12-31 (36,891 days), sunrise, sunset and the sample lists at 7, 10, 30 and 60 minutes (147,564 lists): no difference, including the years in which Hong Kong had summer time.
- Rotterdam (51.92° N, 4.48° E, Europe/Amsterdam), every day of 2026, sample lists at 10 and 30 minutes: equal to the lists that the planning pre-check derived from the old functions.

## Findings

1. **Contract conflict, resolved by user decision; needs `SW-G1.1` (A1).** One existing test function, `test_full_publication_api_cli_resume_prune`, was changed to use `sea-2.2` and config 1.1. The contract forbade changing existing tests, but its own design item 5 (new function default) makes that test fail unchanged. The developer stopped and asked; the user decided. No other existing test function changed. Other unchanged tests still publish with `raw` and the 1.0 fixture. Without an amendment, G1-01 and G1-04 would fail on the frozen wording.
2. **Contract error; needs `SW-G1.1` (A2).** The allowed-file list says `tests/test_city_*.py`; the candidate adds `tests/test_city.py`.
3. **Contract wording; needs `SW-G1.1` (A3).** NL-1 contains only surface classes 0 and 3 (developer's counts), so it has no pixel next to water-labelled fill. The developer's 1,200 ray targets include 300 seam crossings and 200 observed pixels below 0 m within 50 m of fill, with zero disagreements (developer's numbers), and report zero water neighbours available.
4. **Procedure; needs `SW-G1.1` (A4).** By user decision, planning commits follow the candidate on `feature`. The acceptance prompt requires the main checkout to be at the candidate.
5. **For the reviewer's judgement.** The rewrite of the two daylight functions goes beyond "an input instead of a constant" in form. In effect it is equivalent for Hong Kong on every day tested (extra check above).
6. **For the reviewer's judgement.** The developer reports that the first checksum of the two raw sheets ran without memory metering and was repeated inside the measured baseline audit. The contract asks for start, end and peak memory of every job that reads real DSM. The developer marked G1-16 NOT VERIFIED.

## Developer's numbers (not independently verified)

- Hong Kong: 503 frames and 8,664 raster comparisons identical; HK-2 to HK-4 computed zero directions and reused 156, 156 and 148.
- Rotterdam registration: 160 cells; 214,048,125 valid and 35,951,875 NoData pixels; 106,321,205 valid pixels below 0 m (49.67%); warning `fill_above_ground`.
- Rotterdam view classes: 214,048,125 class 0; 18,211,404 class 1; zero class 2; 17,691,564 class 3; 156,048,907 class 4, of which 156,000,000 in the ring.
- NL-2: PROJ 9.8.1, pyproj 3.8.0, operation "Inverse of Amersfoort to WGS 84 (4) + RD New", stated accuracy 1 m; snapped bounds `[92246.5, 437228.5, 92595.0, 437558.5]`.
- NL-4 (fill-impact on NL-1): of 6,250,000 pixels, 321,678 are filled targets; the observed pixels whose label depends on fill number 2,646,084 at 09:00, 4,544,196 at 13:30 and 2,893,375 at 18:00 on 2026-06-21. This is dependence, not error.
- Resources: shade jobs, plans and checks 57.53 of 90 minutes; registration 2.14 of 20 minutes; peak memory 2.51 GiB; new artifacts 4.36 GiB; 309 tests passed.

## Conclusion

The candidate can go to independent acceptance together with amendment `SW-G1.1`. The amendment is needed for findings 1 to 4; without it the frozen wording would fail items for reasons that are errors of the contract, not of the candidate. Findings 5 and 6 are left to the reviewer.

Engineering acceptance, numerical consistency and observational accuracy remain to be stated by the independent acceptance. Observational accuracy is NOT VERIFIED.
