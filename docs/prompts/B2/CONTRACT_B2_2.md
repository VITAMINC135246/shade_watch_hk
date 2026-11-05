# Package B2.2 acceptance contract — DSM-only fill of every NoData pixel (`SW-SEA-POLICY-2.2`)

Contract ID: `SW-B2.2`
Status: frozen on the date of the commit that adds this file, by user approval (2026-11-05). Record this file's SHA-256 before development.
Supersedes for all new work: `SW-B2.0` (`docs/prompts/B2/ACCEPTANCE_CONTRACT.md`, SHA-256 `b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`) and its amendment `SW-B2.1` (`docs/prompts/B2/AMENDMENT_B2_1.md`, SHA-256 `18a09995cbbd1cca659c9a548aad9a0cb45c942668a58ce17146d371f9f8450d`). Those files stay unchanged as records.
B2.0 candidate: `5744e2301eea34f8bae05b9df3e14508425b8282` is **not accepted**. It is kept as a record; its evidence and outputs are read-only. Its code may be reused and changed.
Policy introduced: `SW-SEA-POLICY-2.2`, a data layer on top of the unchanged engine policy `SW-V1-POLICY-1.0`. It replaces `SW-SEA-POLICY-2.0`.
Item codes: `B2-16` to `B2-31`. Numbering continues from B2.0 (decision D-011).
Code definitions and reporting rules: `docs/OUTPUT_CODES.md`.
Decision records (Claude project `claude/DECISIONS.zh-TW.md`; snapshot in `docs/planning/`): D-008, D-009, D-010, D-012, D-014, D-015, D-016.

The development prompt and the independent-acceptance prompt for B2.2 both use this contract. Do not weaken any criterion after seeing results. Any change to scope, policy values or budgets needs a new contract version, agreed before work starts.

## What changed from B2.0

- Every NoData pixel inside the view domain is filled at h_fill, not only water (D-016).
- The B2.0 label rule is kept, but it only decides the surface class. It never decides a height.
- Surface classes become 0 to 4, plus 255 for outside the domain. Class 254 is withdrawn.
- Every lattice cell in the domain that has no DSM tile gets a synthetic tile.
- F publication accepts the new surface codes through one allowlist change. This resolves the B2.0 conflict recorded as B2-08 FAIL.
- The void-impact diagnostic is withdrawn and replaced by a fill-impact diagnostic.
- The source name becomes `sea-2.2`, with new view and cache namespaces.
- The view manifest records the hashes of the build code.
- A real region that contains all five surface classes is added.
- The iB5000 and sensitivity reports now evaluate labels.
- Budgets start a new ledger.

## Problem and objective

In the CEDD 2020 DSM, water and some land surfaces have no elevation (NoData). The accepted engine reports a NoData target as quality 1. It reports NoData within 1 km sunward as incomplete support (quality 2). B2.0 filled only the NoData that its rule identified as water. Land voids and the remaining open NoData stayed 255.

The user's directive (D-016) is that no pixel may stay uncertain because data are missing. The objective is a versioned DSM view derived from the DSM alone in which every NoData pixel of the domain holds h_fill. Surface classes record what was filled. Inside the domain, quality 1 and 2 therefore no longer occur.

The remaining 255 labels come from quality 3 (a possible obstruction beyond 1 km at low sun) and quality 4 (sun at or below the horizon). These are model boundaries, not missing data. They stay 255 (D-016, option A).

The engine is unchanged. The filled surface reaches it as a derived DSM view that package F selects with `dsm_source: "sea-2.2"`.

## Non-goals

- No edit to any file under `src/` or to `tools/region_request.py`. The ten pinned engine files stay byte-identical to `356f611d7b775ce31006904b80ca31d3c1c484b2`: `src/v1.py`, `src/v1_cache.py`, `src/horizon.py`, `src/solar.py`, `src/spatial.py`, `src/shade_watch.py`, `src/v2.py`, `src/v2_worker.py`, `src/v2_runner.py` and `src/v2_state.py`.
- No change to `SW-V1-POLICY-1.0`, the 1 km search, `nearest5`, the V1/V2 limits, cache keys or the estimator.
- No reclassification of quality 3 or 4, and no extended search distance (a possible phase-2 engine item).
- Changes to package F code are limited to design item 8.
- Not part of this package:
  - territory-wide shade computation;
  - the four-region measurement (the user runs it later with the tools delivered here);
  - an ingestion policy for the four `14NE15*` tiles;
  - exception zones;
  - other cities and engine portability (phase 2);
  - web work, V3, downloads other than the tools environment in design item 10, and push.
- B1.0 (`tools/sea_view/`, `docs/sea/`, `tests/test_sea_masks.py`) stays unchanged. Nothing from B1.0 or B2.0 counts as accepted.

## Frozen decisions (user, 2026-10-31 to 2026-11-05; D-010, D-014, D-015, D-016)

1. **Fill height.** h_fill = the profile's `h_sea_m` = 0.00 m HKPD, stored as float32. Every NoData pixel inside the domain is filled at exactly h_fill.
2. **DSM-only.** Building the view, running with it and the fill-impact diagnostic read only the DSM catalogue and the sea profile. The iB5000 data under `data/raw/coastline/` are never opened by build, run or diagnostic code.
3. **Labels.** The B2.0 label rule with the same frozen profile values decides the surface class only.
4. **No NoData inside the domain.** No pixel inside the domain remains NoData. The only exception is the literal-definition case of the four `14NE15*` tiles (design item 2).
5. **Quality 3 and 4 stay 255.** They are reported, not reclassified.
6. **Fill dependency.** A pixel's own fill is recorded in the surface layer. Dependence on filled data elsewhere is measured by the fill-impact diagnostic for chosen regions, not in every run (D-016, option B 甲).
7. **iB5000 is report-only.** It produces numbers and lists and has no pass/fail threshold.
8. **One view per DSM catalogue and profile.** A pixel's class and height never depend on which region was requested.

## Required design

### 1. Sea profile

- Unchanged: `config/sea_profiles/hk_cedd_2020.json` and its schema `config/schema/sea_profile.schema.json` (`sea-profile-1.0`). Values: `h_sea_m` 0.00, `low_shore_margin_m` 5.00, `max_shore_distance_m` 1000, `shore_preference_m` 50, `connectivity` 4, `exclusions` [].
- Under `SW-SEA-POLICY-2.2`, `h_sea_m` is also the fill height for every NoData pixel. All other fields affect labels only.
- Exception zones, if a later version adds any, prevent the water label inside them. Their pixels are still filled. The Hong Kong profile has none.

### 2. Domain and NoData

- **Domain.** The catalogue's native lattice (cells of 750 × 600 m in Hong Kong, derived from the catalogue), extended by 1,000 m on every side. 1,000 m is the model search distance. It is fixed, independent of the profile.
- **Cells.** A *supplied* cell has a DSM tile. An *empty* cell has none.
- **NoData pixel.** A non-finite value or −9999 in a supplied tile, or any pixel of an empty cell that lies inside the domain.
- **`14NE15*` tiles.** These four tiles declare float32-minimum as their NoData value. Under the literal definition, their pixels are observed (class 0) and are not filled. This is documented, not corrected. Regions that need these tiles stay rejected (D-008).
  - For connectivity only, they are addressed on the lattice (offset about 1.9e-7 pixel).
  - Distances use their actual pixel centres.

### 3. Label rule (`SW-SEA-POLICY-2.2`)

**Definitions** (identical to B2.0)

- **Shore pixel.** A valid DSM pixel that is 4-adjacent to a NoData pixel.
  - *Low shore:* height ≤ `h_sea_m` + `low_shore_margin_m`.
  - *High shore:* any other shore pixel.
- **Open and enclosed NoData.** A NoData pixel is *open* if it is connected to the outer edge of the domain through NoData pixels, with the profile's connectivity and across cell borders. Every other NoData pixel is *enclosed*.
- **Distances.** d_low and d_high are the Euclidean distances, in metres between pixel centres, from a NoData pixel to the nearest low-shore and the nearest high-shore pixel. If no high shore exists, d_high is infinite.

**Water label.** A NoData pixel p is labelled water if and only if all of the following hold:

- p is open;
- d_low(p) ≤ `max_shore_distance_m`;
- d_low(p) ≤ d_high(p) + `shore_preference_m`;
- p lies outside every exclusion zone.

**Surface classes.** Every pixel of the domain gets exactly one class:

| Class | Meaning | Height in the view | Statistics group |
| --- | --- | --- | --- |
| 0 | DSM-observed surface (valid pixel) | Raw value, unchanged | Land |
| 1 | Water label, inside a supplied tile | h_fill | Water |
| 2 | Water label, inside an empty cell (synthetic tile) | h_fill | Water |
| 3 | Enclosed NoData (land voids, enclosed inland water) | h_fill | Land |
| 4 | Open NoData without the water label (beyond the distance limit, nearer a high shore, inside an exclusion zone, or an empty cell without water) | h_fill | Other |
| 255 | Outside the domain | NoData | — |

- Valid DSM pixels are never changed.
- Every NoData pixel inside the domain gets class 1 to 4 and height h_fill.

### 4. Sea view

- **Build command:**

  ```
  python -m tools.sea2 build --machine <machine.json>
  ```

  The profile is read from the machine config. The command is read-only on raw data.
- **Output,** written only to `data/processed/dsm_views/sea_fill_v2_2/<view_id>/`:
  - `tiles/`: the catalogue given to the engine;
  - `surface/`: uint8 surface classes per cell;
  - `manifest.json`.

  A pointer file `data/processed/dsm_views/sea_fill_v2_2/current-<profile_id>.json` names the latest view built for that profile, with a header inventory of the catalogue (names, sizes, modification times). Nothing is written to B2.0's `data/processed/dsm_views/sea_fill_v2/`.
- **Supplied tiles.**
  - A tile without NoData pixels is a symlink to, or a byte-identical copy of, the raw tile.
  - A tile with NoData pixels is a lossless DEFLATE copy. Every NoData pixel holds exactly float32 h_fill, and every other pixel is bit-identical to raw. Georeferencing, size, data type and the declared NoData value are identical.
- **Synthetic tiles.**
  - One synthetic tile `FILL_e<left>n<bottom>.tif` is written for every lattice cell that intersects the domain and has no supplied tile.
  - It has the native grid, size, CRS and data type, with NoData value −9999.
  - It holds h_fill at every pixel inside the domain and NoData outside the domain.
  - It never overlaps a supplied tile.
- **Surface classes** must be readable for any aligned window of the domain.
- **Identity.** `view_id` is the hash of the manifest content, excluding timestamps. The manifest records:
  - the policy ID and the full profile with its hash;
  - the catalogue identity: SHA-256 of every raw tile and auxiliary file;
  - the label-rule version and the library versions;
  - the SHA-256 of every file under `tools/sea2/` that the build imports;
  - per-tile and per-cell records: source hash, output hash, counts of each class, synthetic flag;
  - territory class totals;
  - the list of literal-definition exception tiles (the four `14NE15*` tiles).
- **Reproducibility.** Rebuilding with identical inputs and code gives the same `view_id` and file hashes.

### 5. Engine use

- **Cache namespace.** Runs on the view use `data/processed/shade_v1/sea_fill_v2_2_<view_id12>/`.
- **Policy pair.** Engine results keep the `SW-V1-POLICY-1.0` tag. The policy pair (`SW-V1-POLICY-1.0`, `SW-SEA-POLICY-2.2`) and the `view_id` are recorded in F's run manifest.

### 6. `sea-2.2` source provider

The provider is implemented in `tools/sea2/` and registered in F's registry (`tools/shade_map/sources.py`) under the name `sea-2.2`. The B2.0 name `sea-2.0` is removed.

- **`catalogue(machine)`** returns the current B2.2 view's `tiles/` for the machine's `sea_profile`. It fails with `invalid input: sea view missing or built from a different catalogue; run python -m tools.sea2 build` when the pointer is missing, or when the header inventory differs from `dsm_dir`.
- **`cache_namespace`** as in design item 5.
- **`policies`** returns the policy pair.
- **`source_identity`** includes the `view_id`, the profile hash and the hashes of the selected view tiles.
- **`preview_identity`** as required by F's provider protocol.
- **`read_surface`** returns classes 0 to 4 for any aligned window inside the domain, and 255 outside it.

### 7. Expected quality outcome

- A target inside the catalogue lattice has its whole 1 km neighbourhood inside the domain. For such targets, quality 1 and 2 cannot occur, except next to the rejected `14NE15*` tiles.
- The remaining 255 labels have quality 3 or 4.
- Filling lowers a tile's minimum height to h_fill. It can therefore raise the tile's distant-obstruction threshold, so quality 3 may increase at low sun. This is reported, not hidden.

### 8. Changes allowed in package F code

Measured as the cumulative diff from the accepted F1.0 commit `35225fd9547a00e4df202e7ab30204c633b2c845`, restricted to the F paths:

- `tools/shade_map/`;
- `config/schema/shade_map_*.json`;
- `config/machine.example.json`;
- `config/regions/`;
- `tests/test_shade_map.py`, `tests/shade_map_campaign.py`, `tests/shade_map_repair_campaign.py`;
- `docs/shade_map/GUIDE.md`, `docs/shade_map/DESIGN.md`.

The F1.0 acceptance reports `docs/shade_map/INDEPENDENT_ACCEPTANCE_*.md` (added by the user-authorized closeout commit `05c66ab`) are not F code and are excluded.

Only these changes are allowed:

- **`tools/shade_map/sources.py`:** import the `sea-2.2` provider from `tools/sea2/` and register it. Nothing else.
- **`tools/shade_map/publication.py`:** only the surface allowlist used during frame publication (at `35225fd`: line 141, `[0,1,255]`) becomes `[0,1,2,3,4,255]`. The shade and quality allowlists, `FORMAT` (`shade-map-publication-1.0`), the layout, the summaries and the verification stay unchanged.
- **`config/schema/shade_map_region.schema.json`:** `dsm_source` accepts `"raw"` and `"sea-2.2"`.
- **`config/schema/shade_map_machine.schema.json`:** an optional `sea_profile`, default `"hk_cedd_2020"`. Like every machine setting, it is excluded from `run_id`.
- **`config/machine.example.json`:** shows `sea_profile`.
- **`docs/shade_map/GUIDE.md`:** a section on `sea-2.2`.
- **`docs/shade_map/DESIGN.md`:** the description of surface codes only, referring to `docs/OUTPUT_CODES.md`.
- **Tests:** new tests may be added, in `tests/test_sea2_*.py` or appended to the three F test files. Existing test functions in the three F test files stay unchanged.

Planning, runner, configuration-loading code, common helpers, identity and resume logic stay unchanged. `run_id` hashes the ten engine files, the region, the frames, the source identity, the policies and `FORMAT`. It does not hash `publication.py`.

Raw-mode identity regression (the method of `SW-B2.1` A1, kept): a raw-mode `plan` at the candidate and at `35225fd` must give the same `run_id` for both of these configs:

- `config/regions/cheung_chau.json` (B2.0 development evidence: `c196a09a3a213e0720b8dcb5ea5b4edb32ad217fcabcb70a930a9b17b458878e`);
- a copy of `outputs/shade_map_f1_20261031/f1_cheung_chau/region_config.json` made outside `outputs/` (expected `e608af7ffe4181f3d097ce3f776f464b5b79fc67f1c1e5dc12bc6806a421b1ca`).

Raw published outputs are unchanged.

### 9. Fill-impact diagnostic

```
python -m tools.sea2 fill-impact --machine <machine.json> <region.json> [--times HHMM[,HHMM...]]
```

- **Precondition.** It requires a complete F run of that region config with `dsm_source: "sea-2.2"`. The selected times must be frames of that run; the default is all of them. Otherwise it exits 2 with a clear message.
- **Counterfactual.** The same frames, planned through the adapter on the raw catalogue (the machine's `dsm_dir`) and run with V2.
  - Work folder: `outputs/sea2_2_diagnostic_work/<name>-<id12>/`.
  - Cache namespace: `data/processed/shade_v1/sea2_2_fill_impact_<id12>/`.
  - It never writes inside the F run folder. Its rasters are diagnostics, not published results.
- **Dependency raster,** per frame and per cell, with the codes in `docs/OUTPUT_CODES.md`: `<output_root>/_diagnostics/fill_impact/<name>/<YYYYMMDD>/<HHMM>/dependency/<cell>.tif`, plus a VRT.
- **Metrics per frame.** Groups: land L (surface 0 and 3), water W (1 and 2) and other (4).
  - Counts of each dependency code in each group.
  - For observed targets (surface 0): transition counts from raw (shade, quality) to sea-filled (shade, quality).
  - Fractions over |L| and over |W|.
  - `fill_dependent_land` = (codes 1, 2 and 3 within L) / |L|.
- **Output:** `<output_root>/_diagnostics/fill_impact/<name>/fill_impact.csv` and `fill_impact.json`, with schema `config/schema/fill_impact.schema.json`.
- **Resume.** Re-running resumes the counterfactual run.
- **Void-impact is withdrawn.** Its command is removed. `tools/sea2/void_impact.py` and `config/schema/void_impact.schema.json` may be deleted. No B2.2 path may call them.

### 10. Tools environment and validation (report only)

- **Environment.**
  - A separate virtual environment at `~/venvs/shade_watch_tools`: outside the repository, not under `/tmp`, Python 3.12.
  - Created with `pip install --no-deps -r requirements.tools.lock.txt`. It contains exactly the five pinned packages: certifi 2025.8.3, numpy 2.2.6, packaging 25.0, pyogrio 0.11.1 and shapely 2.1.1.
  - Record the interpreter, the download URLs and the SHA-256 of every wheel.
  - This download is authorized; no other download is.
- **Reader.** `tools/sea2/validate_ib5000.py` runs in this environment. It reads `HydrographyPoly` with `FEATURESUBTYPE = 3` and `DATASTATUS = 'E'`, taking `SEF` as sea and `LAF` as land, as in B1.0.
- **iB5000 label report.** It covers the territory and the halos of Cheung Chau, Central and the five-class region:
  - false water: water-labelled pixels inside `LAF`, as a count and as a fraction of water;
  - missed sea: pixels inside `SEF` − `LAF` that are labelled 3 or 4, by class;
  - class-3 pixels inside `SEF` (sea read as enclosed);
  - water-labelled pixels outside the map's coverage or in neither class, listed per cell with bounds, with the northern boundary listed separately;
  - every false-water component larger than 2,500 pixels, with its location;
  - for Central, the Victoria Harbour share. The denominator is raw-DSM NoData pixels inside `SEF` − `LAF` within the Central halo; the numerator is those labelled water. The DSM-only bound (the share of all halo NoData labelled water) is also reported.
- **Class-3 component report** (DSM-only, no iB5000). For every enclosed component of at least 10,000 pixels: an ID, its bounds, its pixel count, the cells it touches, and the median, p10 and p90 heights of its observed 4-adjacent shore pixels. The shore heights estimate how far the h_fill surface sits below its surroundings.
- **Sensitivity report** (labels only, no shade runs). Over the Cheung Chau, Central and five-class halos: class counts 1 to 4 and the iB5000 figures, for `low_shore_margin_m` ∈ {4, 5, 6} and `shore_preference_m` ∈ {0, 50, 100}. Shade results do not depend on these parameters, because every NoData pixel is filled at h_fill. The frozen profile does not change.
- These are reports, not gates. No parameter is changed because of them.

### 11. Documentation

- `docs/OUTPUT_CODES.md` is a planning record and is read-only for the developer. Report any inconsistency instead of editing it.
- `docs/sea2/POLICY.md`, `GUIDE.md` and `DESIGN.md` describe B2.2. They refer to `docs/OUTPUT_CODES.md` and do not contradict it.
- `docs/sea2/DEVELOPMENT_REPORT_B2_2.md` is new. Evidence goes under `docs/sea2/evidence/b2_2/`. B2.0's `docs/sea2/DEVELOPMENT_REPORT.md` and its evidence elsewhere under `docs/sea2/evidence/` stay unchanged.
- **GUIDE contents:**
  - building the view;
  - running F with `sea-2.2`;
  - running `fill-impact` and reading its numbers;
  - the reporting rules in `docs/OUTPUT_CODES.md`, including bounds;
  - adapting the profile to another DSM: h_fill in that DSM's datum, with the label parameters affecting labels only.
- **Limitations must state:**
  - h_fill = 0 m lies about 1.4 m below the median DSM waterline, so shade on near-shore water is slightly overstated.
  - Every NoData pixel is filled at h_fill, whatever it really is. Enclosed NoData (class 3) includes land voids and inland water such as reservoirs. Where the true surface is higher, the fill forms a pit. Shade on the pit itself is biased toward shade, and nearby land may lose a real obstruction and be biased toward sunlit. Labels that depend on filled data are model results under this assumption.
  - Filling can raise a tile's distant-obstruction threshold, so quality 3 can increase slightly at low sun.
  - Quality 3 and 4 stay 255. This is the 1 km model boundary, not missing data.
  - Water and other labels depend on the profile parameters; shade results depend only on h_fill.
  - Low land at the edge of DSM coverage can be labelled water. The Shenzhen side near low river banks or fish ponds is the known risk.
  - The four `14NE15*` tiles are treated literally and regions needing them are rejected.
  - Piers, pontoons, boats and tide are not modelled.
  - Labels on filled targets are less certain than labels on observed land.
  - The phase-1 engine is Hong Kong only.
  - Observational accuracy is NOT VERIFIED.
  - Shade is not cooling and not ΔT.

## Authorized computation scope (development)

- **(v) View build.** One territory build of the B2.2 view for `hk_cedd_2020`. Stopped or failed attempts count toward the same build budget. There is no second build in development: the independent rebuild provides reproducibility evidence.
- **(a) Cheung Chau.** An F run with the parameters of `config/regions/cheung_chau.json` (2026-01-07 daylight, 65 frames), with `sea-2.2`, under a new name and on a cold cache. The raw reference is the F1.0 development run `outputs/shade_map_f1_20261031/f1_cheung_chau/` (read-only; `SW-B2.1` A3).
- **(b) Central.** The Central/Mid-Levels 2×2 (`11SW8D`, `11SW9C`, `11SW13B`, `11SW14A`; HK1980 `[833750, 815000]` to `[835250, 816200]`) at 08:30, 12:30 and 15:10 HKT on 2026-01-07, with `sea-2.2`. Raw reference, either of:
  - `outputs/sea2_f_20261104/sea2_central_raw/`, read-only, after confirming that its `run_id` equals a raw `plan` at the candidate;
  - a raw rerun under a new name.
- **(c) Five-class region.** HK1980 `[811250, 833000]` to `[812750, 833600]`, covering cell `e812000n833000` (tile `5NE14A`) and the empty cell `e811250n833000`. Run at 08:00, 12:30 and 16:00 HKT on 2026-01-07, with `sea-2.2`. Before running, confirm from the view that its targets contain classes 0 to 4. If they do not, report and stop for a decision; do not pick another region.
- **(d) Fill-impact.** Cheung Chau at 07:20, 12:30 and 17:40; the five-class region at all three of its frames.
- **(e) Direct-ray checks** for B2-27.
- **(f) Validation** in the tools environment (design item 10), including creating that environment.
- **Not authorized:**
  - other regions;
  - territory shade runs;
  - the four-region measurement;
  - exception zones and profile changes;
  - engine changes;
  - V3 and edits to `config/v3/`;
  - downloads other than (f);
  - web work;
  - push.

## Budgets

| Phase | Real-DSM job wall time | View build | Report-only validation | Job memory | New artifacts |
| --- | --- | --- | --- | --- | --- |
| Development | ≤ 60 min | ≤ 60 min, one build | ≤ 30 min | ≤ 12 GiB | ≤ 30 GiB |
| Independent acceptance | ≤ 45 min | one rebuild, ≤ 60 min | ≤ 20 min | ≤ 12 GiB | ≤ 30 GiB |

- Wall time is measured with a clock that includes system sleep. Prevent sleep during jobs, for example with `caffeinate`.
- Measure every process that touches real DSM data, including read-only planning.
- This is a new ledger. The B2.0 ledger, including its first-build overrun, stays in the B2.0 report and is not carried over.
- When a budget runs out, the criteria it affects become NOT VERIFIED. Budgets may not be extended.

## Write scope and allowed files

**Files the candidate may add, change or delete.** This list is complete; reviewers use it as written.

- `tools/sea2/**`
- `config/schema/fill_impact.schema.json` (new); `config/schema/void_impact.schema.json` (may be deleted); new schemas under `config/schema/` for B2.2 view manifests or pointers
- `tests/test_sea2_*.py`
- `docs/sea2/POLICY.md`, `docs/sea2/GUIDE.md`, `docs/sea2/DESIGN.md`, `docs/sea2/DEVELOPMENT_REPORT_B2_2.md`, `docs/sea2/evidence/b2_2/**` (including the run configs, under `docs/sea2/evidence/b2_2/configs/`)
- the F files and changes listed in design item 8

`config/regions/` stays unchanged.

`config/sea_profiles/hk_cedd_2020.json` and `config/schema/sea_profile.schema.json` stay unchanged.

**Data and output locations the development may write:**

- `data/processed/dsm_views/sea_fill_v2_2/`;
- `data/processed/shade_v1/sea_fill_v2_2_*`, `data/processed/shade_v1/sea2_2_fill_impact_*` and new raw namespaces `data/processed/shade_v1/sea2_2_raw_*`;
- new top-level folders `outputs/sea2_2_*` (including `outputs/sea2_2_diagnostic_work/`);
- new entries for new run names in the fixed containers of F and the adapter (see below);
- `~/venvs/shade_watch_tools`.

**What counts as a write to an existing folder** (agreed by the user on 2026-11-05; recorded under D-014). Creating a new entry for a new run name in F's or the adapter's fixed containers does not count:

- `outputs/shade_map_work/<name>-<id12>/`;
- `outputs/shade_map_work/.locks/<name>.lock`;
- `outputs/region_views/<key>/`.

Nor does creating a new namespace under `data/processed/`. Changing or deleting an existing file, or adding files inside a pre-existing run folder or namespace, does count.

**Read-only:**

- `data/raw/` (`data/raw/coastline/` is read only by the validation script);
- every existing namespace under `data/processed/`, including B2.0's `dsm_views/sea_fill_v2/` and its caches;
- all existing `outputs/` folders, including B2.0's `outputs/sea2_f_20261104/` and `outputs/sea2_diagnostic_work/`;
- `docs/sea2/DEVELOPMENT_REPORT.md` and B2.0 evidence under `docs/sea2/evidence/` outside `b2_2/`;
- `docs/prompts/`, `docs/planning/`, `docs/OUTPUT_CODES.md`, `presentations/`;
- the uncommitted planner files.

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| B2-16 | Traceability and boundaries | The starting commit contains `5744e23` and this contract; contract hash recorded; both environments recorded with their locks. `git diff <candidate parent>..<candidate> -- src/ tools/region_request.py` is empty, and the ten pinned files equal `356f611`. The candidate's own changes, measured from its parent, stay inside the allowed-file list. The cumulative F-path diff from `35225fd` contains only the changes in design item 8. B1.0 files and all B2.0 records and outputs are unchanged. |
| B2-17 | DSM-only | `build`, `plan`, `run` and `fill-impact` succeed while `data/raw/coastline/` is unreadable. A read probe during the blackout fails, and the original and restored modes are recorded. The same `view_id` and the same outputs result. A code audit shows no build, run or diagnostic path that opens coastline data. |
| B2-18 | Label rule on synthetic fixtures | Each fixture's classes and heights equal hand-computed expectations. The fixtures cover: open NoData next to a low shore (1); next to a high shore beyond the preference margin (4); within the margin (1); beyond 1 km (4); an enclosed void (3); an enclosed empty cell (3, synthetic tile); an empty cell with water (2); a diagonal-only link (not connected); a component crossing cells; an exclusion zone (4, still filled); a tile whose declared NoData is not −9999 (literal treatment); a partial domain-edge cell (255 outside the domain). |
| B2-19 | Scope independence | Surface classes read through two different requests over an overlapping area are identical. Classifying a fixture in one pass equals classifying it cell by cell with halos. |
| B2-20 | Fill correctness | For every derived tile: every literal NoData pixel holds exactly float32 h_fill; every other pixel is bit-identical to raw; transform, CRS, size, data type and declared NoData value are identical. Tiles without NoData are links or byte-identical copies. No literal NoData pixel remains inside the domain. The four `14NE15*` tiles are unfilled and uncorrected. Territory class totals reconcile with the per-cell counts. |
| B2-21 | Synthetic tiles | A synthetic tile exists for exactly every lattice cell that intersects the domain without a supplied tile. All are lattice-aligned, native-sized, non-overlapping and named `FILL_e<left>n<bottom>.tif`. Each holds h_fill inside the domain and NoData outside it. Request-local views built from the view are accepted by `v1.index_sources`. |
| B2-22 | Identity and reproducibility | The manifest contains every record listed in design item 4, including the build-code hashes, and they equal the candidate's files. An independent full rebuild reproduces the `view_id` and every file hash. The developer marks this rebuild part NOT VERIFIED; that does not block hand-off. The cache namespace is as specified. Plan keys differ from raw plan keys wherever a dependency changed. F manifests record the policy pair and `view_id`. |
| B2-23 | F integration and regression | `sea-2.2` works through the registry, and `sea-2.0` is gone. The publication change is limited as in design item 8, and `FORMAT` is unchanged. All existing F tests pass unchanged. Both raw `run_id` checks pass. Published surface layers equal the view's classes, for all six codes on a synthetic fixture and for classes 0 to 4 on region (c). No expected-failure mark remains for surface publication. |
| B2-24 | No missing-data uncertainty | In every published `sea-2.2` frame of (a), (b) and (c), quality 1 and quality 2 counts are zero. Every remaining 255 has quality 3 or 4. Counts per frame and per surface class are reported. |
| B2-25 | Land regression, Cheung Chau | Over the 65 frames of (a), on observed land (class 0), `sea-2.2` against raw: (i) zero shaded → sunlit; (ii) every sunlit → not-sunlit change is explained by a demonstrated blocker on filled surface or by a rise in the owning tile's distant-obstruction threshold (old and new `threshold_deg` reported per tile); (iii) the transitions of raw-255 observed-land pixels to 0, 1 and 255 are reported per frame, by raw quality. |
| B2-26 | Urban and five-class guard | For (b) against its raw reference and for (c) against the raw counterfactual of (d), gates (i) and (ii) of B2-25 hold on observed land. Class counts are reported. The shade distribution on class-3 targets in (c) is reported (pit effect). |
| B2-27 | Filled-target consistency | At 3 instants, the engine label equals an independent direct-ray reference on the view, within the engine's documented equality tolerance, for: ≥ 200 water targets per instant, including water next to tall structures (Cheung Chau); ≥ 200 class-3 or class-4 targets per instant (region (c)); and ≥ 200 observed targets within 50 m of a filled pixel per instant (region (c)). Numerical consistency only. |
| B2-28 | Fill-impact diagnostic | (d) completes. The counterfactual uses the raw catalogue. For every frame, the metric counts reconcile with the rasters and sum to \|L\|, \|W\| and the other group. The dependency rasters equal an independent per-pixel recomputation from the two runs. The output validates against its schema. The tool refuses when the `sea-2.2` run is missing or does not match, writes nothing inside the F run folder, and resumes. |
| B2-29 | Tools environment and validation reports | The environment is created exactly from the lock, with the interpreter, URLs and wheel hashes recorded. Every report item in design item 10 is computed with it: the iB5000 label report for the territory and the three halos, including the northern-boundary listing and the Victoria Harbour share; the class-3 component report; and the sensitivity report. No parameter is changed. |
| B2-30 | Scope, resources, write scope | Listings before and after show writes only to the allowed locations, under the reading of existing folders given above. Only authorized computations ran. The ledger of real-DSM job time, view-build time (sleep-inclusive), validation time, peak memory and disk use is within budget, with every process measured. |
| B2-31 | Tests, docs, handoff | Automated tests use synthetic fixtures. The full suite passes, and existing F tests are unchanged. POLICY, GUIDE, DESIGN and DEVELOPMENT_REPORT_B2_2 are present, refer to `docs/OUTPUT_CODES.md` without contradicting it, and state every required limitation. An evidence manifest is present. One local commit, full SHA reported, no push. |

## Decisions and release

- **Marking.** Each of B2-16 to B2-31 is marked PASS, FAIL or NOT VERIFIED, with evidence paths and commands.
- **Acceptance.** `SW-SEA-POLICY-2.2` is accepted only if every criterion passes in a separate independent-acceptance conversation. For B2-22, the independent rebuild is the required evidence.
- **What acceptance means.** Engineering acceptance and numerical consistency.
  - The iB5000 figures describe agreement of labels with a map, not observational accuracy.
  - Labels that depend on filled data are model results under h_fill.
  - Shade on water, on filled targets and on land remains NOT VERIFIED against observations.
- **What acceptance does not authorize:**
  - exception zones;
  - territory runs;
  - reclassifying quality 3 or 4;
  - an extended search distance;
  - V3;
  - a push.

  Each needs its own decision.
- **Fixes.** Each fix needs a new commit SHA and targeted re-acceptance. Failure evidence is preserved.
