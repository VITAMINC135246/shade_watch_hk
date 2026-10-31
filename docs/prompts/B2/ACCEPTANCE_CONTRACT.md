# Package B2.0 acceptance contract — DSM-only sea surface (`SW-SEA-POLICY-2.0`)

Contract ID: `SW-B2.0`
Status: frozen 2026-10-31 by user approval. Record this file's SHA-256 before development. Development starts only after F1.0 is independently accepted.
Policy introduced: `SW-SEA-POLICY-2.0`, a data layer on top of the unchanged engine policy `SW-V1-POLICY-1.0`. It replaces `SW-SEA-POLICY-1.0` (B1.0, never accepted) for all new work.
Item codes: `B2-01` to `B2-15` (numbering rule: decision D-011).
Decision records (Claude project `claude/DECISIONS.zh-TW.md`, snapshot in `docs/planning/`): D-010 (direction), D-012 (F1.0), D-014 (B2.0 decisions).

The development prompt and the independent-acceptance prompt both use this contract. Do not weaken any criterion after seeing results. Any change to scope, policy values or budgets needs a new contract version, agreed before work starts.

## Problem and objective

In the CEDD 2020 DSM, water has no elevation (NoData). The accepted engine treats NoData within 1 km in the sunward direction as incomplete support (Quality 2). As a result, coastal land is mostly uncertain: in the reference Cheung Chau run, 53.0% of land pixels were Quality 2 at 12:30 HKT.

The objective is a versioned sea surface that is derived from the DSM alone, so that the same rule can later be applied to other cities' DSMs:

- DSM NoData that the rule identifies as water becomes a flat surface at sea level, h_sea = 0.00 m in the DSM's vertical datum (HKPD for Hong Kong).
- Water then supports land and is itself a target that the engine classifies (0, 1 or 255).
- NoData holes inside land stay NoData. The engine keeps reporting them as invalid (255), and a diagnostic measures how much land they leave uncertain.
- The iB5000 map is used only to report how well the rule did. It is never an input.

The engine is unchanged. Water reaches it as a derived DSM view that package F1.0 selects with `dsm_source: "sea-2.0"`.

## Non-goals

- No edit to any file under `src/` or to `tools/region_request.py`. The ten pinned engine files stay byte-identical to `356f611d7b775ce31006904b80ca31d3c1c484b2`.
- No change to `SW-V1-POLICY-1.0`, the 1 km search, `nearest5`, the V1/V2 limits, cache keys or the estimator.
- Changes to package F code are limited to the list in design item 7.
- Not part of this package:
  - filling land voids (that would be a later version, triggered by the 10% rule in D-010);
  - territory-wide shade computation;
  - the four-region winter/summer measurement (the user runs it later with the tools delivered here);
  - an ingestion policy for the four `14NE15*` tiles;
  - other cities and engine portability (phase 2);
  - web work, V3, downloads, push.
- B1.0 (`86dbee6`, `tools/sea_view/`) may be reused by import, but its existing functions and outputs must keep their behaviour. Nothing from B1.0 counts as accepted.

## Frozen decisions (user, 2026-10-31; D-010 and D-014)

1. **Sea level.** h_sea = 0.00 m HKPD, stored as float32. Water is filled at exactly h_sea.
2. **DSM-only.** Building the sea view and running with it read only the DSM catalogue and the sea profile (design item 1). The iB5000 data under `data/raw/coastline/` is never opened by build or run code.
3. **Automatic rule plus optional exceptions** (design item 2). Its parameters live in a per-dataset sea profile, so another city needs only its own profile. Exception zones are supported; the Hong Kong 2.0 profile has none. Whether Hong Kong needs any, for example at the Shenzhen border, is decided after this package's measurements.
4. **Land voids stay NoData** (shade 255). They are measured, not filled.
5. **Void-impact diagnostic** (design item 8). A counterfactual run in which land voids are also filled at h_sea. The uncertainty attributed to voids is counted as the voids themselves plus the land pixels that are Quality 2 only because of voids.
6. **iB5000 is report-only.** It produces numbers and lists, and has no pass/fail threshold (design item 9).
7. **One sea view per DSM catalogue.** Classification is computed once over the whole catalogue, so a pixel's class never depends on which region was requested.

## Required design

### 1. Sea profile

The sea profile is a JSON file per DSM dataset: `config/sea_profiles/<profile_id>.json`, with schema `config/schema/sea_profile.schema.json`. Its fields:

| Key | Hong Kong value (`hk_cedd_2020`) | Meaning |
| --- | --- | --- |
| `schema` | `"sea-profile-1.0"` | Format identifier |
| `profile_id` | `"hk_cedd_2020"` | Identifier |
| `vertical_datum` | `"HKPD"` | Documentation of the datum |
| `h_sea_m` | `0.00` | Sea level in the DSM's datum; also the fill value |
| `low_shore_margin_m` | `5.00` | A shore pixel is *low* if its height ≤ h_sea + this margin |
| `max_shore_distance_m` | `1000` | Water extends at most this far from a low shore (equal to the model's 1 km search) |
| `shore_preference_m` | `50` | How much farther the nearest low shore may be than the nearest high shore |
| `connectivity` | `4` | Pixel connectivity used for NoData regions |
| `exclusions` | `[]` | Optional exception zones: axis-aligned rectangles `{"id", "bounds": [left, bottom, right, top], "reason"}` in the DSM's CRS. Nothing is filled inside them |

Basis for the Hong Kong values:

- **Low-shore margin.** In B1.0's territory scan (a development result, never accepted), the DSM pixels next to map-defined sea had p50 = 1.37 m and p95 = 3.90 m. The margin of 5.00 m is set above that p95.
- **Maximum shore distance.** 1 km is the model's search distance: water farther than 1 km from every shore cannot complete any land pixel's support.
- **Shore preference.** 50 m is 100 pixels.

These values are frozen. They are not tuned after seeing results.

### 2. Classification rule (`SW-SEA-POLICY-2.0`)

**Definitions**

- **Domain.** The catalogue's native lattice (cells of 750 × 600 m in Hong Kong, derived from the catalogue), extended by `max_shore_distance_m` on every side.
- **Cells.**
  - A *supplied* cell has a DSM tile.
  - An *empty* cell has no tile. Every pixel of an empty cell counts as NoData.
- **NoData pixel.** A non-finite value or −9999 in a supplied tile, or any pixel of an empty cell.
- **Shore pixel.** A valid DSM pixel that is 4-adjacent to a NoData pixel.
  - *Low shore:* height ≤ h_sea + `low_shore_margin_m`.
  - *High shore:* any other shore pixel.
- **Open and enclosed NoData.**
  - A NoData pixel is *open* if it is connected, through NoData pixels with the profile's connectivity and across cell borders, to the outer edge of the domain.
  - Every other NoData pixel is *enclosed*.

**Water.** A NoData pixel p is water if and only if all of the following hold:

- p is open;
- d_low(p) ≤ `max_shore_distance_m`;
- d_low(p) ≤ d_high(p) + `shore_preference_m`;
- p lies outside every exclusion zone.

d_low and d_high are the Euclidean distances, between pixel centres in metres, from p to the nearest low-shore and nearest high-shore pixel. If no high shore exists, d_high is infinite.

**Surface classes.** Every pixel of the domain gets exactly one class:

| Class | Meaning | Counted as land in diagnostics |
| --- | --- | --- |
| 0 | DSM-observed surface (valid pixel) | yes |
| 1 | Water, filled, inside a supplied tile | no |
| 2 | Water, filled, inside an empty cell (synthetic tile) | no |
| 254 | Open NoData that is not water: beyond the distance limit, nearer a high shore, inside an exclusion zone, or an empty cell that is not water | no |
| 255 | Enclosed NoData: land voids and enclosed empty cells | yes |

**Other rules.**

- Valid DSM pixels are never changed.
- Pixels of classes 254 and 255 stay NoData.
- The four shifted-origin `14NE15*` tiles are not corrected. For connectivity only, they are treated as lying on the lattice; the offset is about 1.9e-7 pixel. This treatment is documented and changes no data.

### 3. Sea view

- **Built once per catalogue and profile,** by an explicit command:

  ```
  python -m tools.sea2 build --machine <machine.json>
  ```

  The profile is read from the machine config (design item 7). The command is read-only on raw data.
- **Output,** written only to `data/processed/dsm_views/sea_fill_v2/<view_id>/`:
  - `tiles/`: the catalogue given to the engine;
  - `surface/`: the uint8 surface classes per cell;
  - `manifest.json`.
- **Supplied tiles.**
  - A tile with no water pixel is a symlink to, or a byte-identical copy of, the raw tile.
  - A tile with water pixels is a lossless DEFLATE copy: water pixels hold exactly float32 h_sea, and every other pixel is bit-identical to raw. Georeferencing, size, data type and NoData value are identical.
- **Synthetic tiles.**
  - One synthetic tile `SEA_e<left>n<bottom>.tif` is written for each empty cell that contains water.
  - It has the native grid, size, CRS, data type and NoData value. It holds h_sea at water pixels and NoData elsewhere, and never overlaps a supplied tile.
- **Surface classes** must be readable for any aligned window of the domain, including empty cells that have no tile.
- **Identity.**
  - `view_id` is the hash of the manifest content, excluding timestamps. The manifest records:
    - the policy ID and the full profile, with its hash;
    - the catalogue identity: SHA-256 of every raw tile and auxiliary file;
    - the rule and library versions;
    - per-tile and per-cell records: source hash, output hash, counts of each class, synthetic flag;
    - territory class totals.
  - A pointer file `data/processed/dsm_views/sea_fill_v2/current-<profile_id>.json` names the latest view built for that profile, together with a cheap header inventory of the catalogue: names, sizes and modification times.
- **Reproducibility.** Rebuilding with identical inputs gives the same `view_id` and file hashes.

### 4. Hong Kong profile and exception zones

- Ship `config/sea_profiles/hk_cedd_2020.json` with the values in design item 1 and `exclusions: []`.
- Adding or changing an exclusion changes the profile hash, so it produces a new `view_id`. It needs a new contract version.

### 5. Engine use

- **Cache namespace.** Runs on the sea view use `data/processed/shade_v1/sea_fill_v2_<view_id12>/`.
- **Policy pair.** Engine results keep the `SW-V1-POLICY-1.0` tag. The policy pair (`SW-V1-POLICY-1.0`, `SW-SEA-POLICY-2.0`) and the `view_id` are recorded in F's run manifest.

### 6. `sea-2.0` source provider

A provider registered in F's registry (`tools/shade_map/sources.py`):

- **`catalogue(machine)`** returns the current view's `tiles/` for the machine's profile.
  - It fails with `invalid input: sea view missing or built from a different catalogue; run python -m tools.sea2 build` when the pointer is missing, or when the header inventory differs from `dsm_dir`.
- **`cache_namespace`** as in design item 5.
- **`policies`** returns the policy pair.
- **`source_identity`** includes the `view_id`, the profile hash, and the hashes of the selected view tiles.
- **`read_surface`** returns the classes 0, 1, 2, 254 and 255 from the view for any aligned window, including windows over empty cells.

### 7. Changes allowed in package F code

Only these:

- **Register** `sea-2.0` in `PROVIDERS`.
- **Region config:** `dsm_source` accepts `"raw"` and `"sea-2.0"` (schema, validator, tests).
- **Machine config:** a new optional `sea_profile`, default `"hk_cedd_2020"` (schema, validator, tests, `config/machine.example.json`). Like every machine setting, it is excluded from `run_id`; the profile reaches the identity through `source_identity`.
- **GUIDE:** a section on `sea-2.0`.

No change to planning, publication, runner, identity or resume logic. All existing F tests pass unchanged. A raw-mode `plan` of `config/regions/cheung_chau.json` still gives `run_id` `e608af7ffe4181f3d097ce3f776f464b5b79fc67f1c1e5dc12bc6806a421b1ca`.

### 8. Void-impact diagnostic

```
python -m tools.sea2 void-impact --machine <machine.json> <region.json>
```

- **Precondition.** It requires a complete F run of that region config with `dsm_source: "sea-2.0"`. Otherwise it exits 2 with a clear message.
- **Counterfactual view.** It builds a scope-limited view with the same tiles as the sea view, except that enclosed NoData (class 255) is also filled at h_sea.
  - Written to `data/processed/dsm_views/sea_voidfill_v2_diagnostic/<id>/`, labelled `diagnostic`.
  - It differs from the sea view only at class-255 pixels.
- **Counterfactual run.** It plans through the adapter and runs V2 for exactly the same frames.
  - Work folder: `outputs/sea2_diagnostic_work/<name>-<id12>/`.
  - Cache namespace: `data/processed/shade_v1/sea_voidfill_v2_diagnostic_<id12>/`.
  - It never writes inside the F run folder, and its rasters are not published as results.
- **Metrics,** per frame, with the land domain L = surface class 0 ∪ 255:
  - `void_pixels`: class 255;
  - `void_caused`: class-0 pixels that are Quality 2 in the policy run and not Quality 2 in the counterfactual, split by their counterfactual outcome (0, 1, Quality 3);
  - `other_quality2`: class-0 pixels that are Quality 2 in both runs;
  - `quality3`, `sunlit` and `shaded`: class-0 pixels in the policy run;
  - all of the above as fractions of |L|, the whole land domain (D-009).
- **Trigger value.** For each date, the mean over its frames of (`void_pixels` + `void_caused`) / |L|, with a flag `exceeds_10_percent`.
- **Output:** `<output_root>/_diagnostics/void_impact/<name>/void_impact.csv` and `void_impact.json` (schema `config/schema/void_impact.schema.json`).
- **Resume.** Re-running resumes the counterfactual run.

### 9. iB5000 validation (report only)

- **Separate environment.** `tools/sea2/validate_ib5000.py` runs in the separate tools environment (pyogrio, pinned in `requirements.tools.lock.txt`), reading `HydrographyPoly`, `FEATURESUBTYPE = 3`, `DATASTATUS = 'E'`, with `SEF` as sea and `LAF` as land, exactly as in B1.0.
- **What it reports,** territory-wide and for the Cheung Chau and Central scopes:
  - false water: water pixels inside `LAF`, as a count and as a fraction of water in supplied tiles;
  - missed sea: NoData pixels inside `SEF` − `LAF` that are not water, split by class (254 or 255);
  - water outside the map's coverage, or in neither class, listed per cell with bounds. The northern boundary is reported separately.
  - every false-water component larger than 2,500 pixels, listed with location;
  - the land voids (class 255) that lie inside `SEF` (sea read as land).
- These are reports, not gates. No parameter is changed because of them.
- **Sensitivity report.** This is classification only, with no shade runs, over the Cheung Chau and Central halos. It gives the water, 254 and 255 pixel counts, and the same iB5000 figures, for `low_shore_margin_m` ∈ {4, 5, 6} and `shore_preference_m` ∈ {0, 50, 100}. It informs a possible later profile version; the frozen profile does not change.

### 10. Documentation

- `docs/sea2/POLICY.md`: the frozen rule, profile, classes, identity and limitations.
- `docs/sea2/GUIDE.md`:
  - building the view;
  - running F with `sea-2.0`;
  - running `void-impact`, and reading its numbers against the 10% trigger;
  - adapting the profile for another DSM (sea level in that DSM's datum; exception zones).
- `docs/sea2/DESIGN.md` and `docs/sea2/DEVELOPMENT_REPORT.md`.
- **Limitations must state:**
  - h_sea = 0 m lies about 1.4 m below the DSM waterline median, so shade on near-shore water is slightly overstated.
  - Low land at the edge of DSM coverage can be read as water. The Shenzhen side near low river banks or fish ponds is the known risk.
  - Sea next to long high shores (cliffs, high seawalls), and water more than 1 km from a low shore, stay unfilled.
  - Piers, pontoons, boats and tide are not modelled.
  - Land voids remain 255 and are not shade.
  - Sea-target labels are less certain than land labels.
  - Regions needing the `14NE15*` tiles are rejected.
  - The phase-1 engine is Hong Kong only.
  - Observational accuracy is NOT VERIFIED.
  - Shade is not cooling and not ΔT.

## Authorized computation scope

- **(v) View build.** One territory sea view for `hk_cedd_2020`, plus one full rebuild for reproducibility.
- **(a) Cheung Chau.** F runs of `config/regions/cheung_chau.json` (2026-01-07 daylight, 65 frames) with `sea-2.0`, on a cold cache, compared with the F1.0 raw results of the same config. Reuse the F1.0 development run read-only, or rerun raw under a new name.
- **(b) Central.** The Central/Mid-Levels 2×2 (`11SW8D`, `11SW9C`, `11SW13B`, `11SW14A`) at 3 daylight instants on 2026-01-07, with both `raw` and `sea-2.0`.
- **(c) Void impact.** `void-impact` for the Cheung Chau run (a).
- **(d) Sea-target checks.** Direct-ray references for B2-11.
- **(e) iB5000 validation.** In the tools environment.
- **Not authorized:** other regions; the four-region solstice measurement; territory shade runs; exception zones; V3; edits to `config/v3/`; downloads; web work; push.

## Budgets

| Phase | Real-DSM job wall time | View build | Job memory | New artifacts |
| --- | --- | --- | --- | --- |
| Development | ≤ 60 min | ≤ 60 min per build | ≤ 12 GiB | ≤ 30 GiB, covering views, caches, outputs and diagnostics |
| Independent acceptance | ≤ 45 min | one rebuild ≤ 60 min | same | same |

When a budget runs out, the criteria it affects become NOT VERIFIED. Budgets may not be extended.

## Acceptance matrix

| ID | Requirement | Pass evidence |
| --- | --- | --- |
| B2-01 | Traceability; engine and adapter untouched; F changes limited | Starting SHA (must contain the independently accepted F1.0 commit), contract hash, both environments with their locks. `git diff <start>..<candidate> -- src/ tools/region_request.py` is empty, and the ten pinned files equal `356f611`. The F diff touches only the items in design item 7. B1.0 functions are unchanged. |
| B2-02 | DSM-only | `build`, `plan`, `run` and `void-impact` succeed with `data/raw/coastline/` made unreadable, giving the same `view_id` and the same outputs. A code audit shows no build or run path that opens coastline data. |
| B2-03 | Rule on synthetic fixtures | Tests cover: open NoData next to a low shore (water); next to a high shore beyond the preference margin (254); within the margin (water); beyond 1 km (254); an enclosed low-shore void (255); an enclosed empty cell (255); an empty cell with water (class 2, synthetic tile); a diagonal-only link (not connected under 4-connectivity); a component crossing cells; an exclusion zone (254). Each fixture's classes equal hand-computed expectations. |
| B2-04 | Scope independence | Surface classes read through two different requests over an overlapping area are identical. Classifying a fixture in one pass equals classifying it cell by cell with halos. |
| B2-05 | Fill correctness | For every derived tile in the view: water pixels are exactly float32 h_sea; every other pixel is bit-identical to raw; transform, CRS, size, data type and NoData are identical; water-free tiles are links or byte-identical copies. The four `14NE15*` tiles are not corrected. Territory class totals reconcile with the per-cell counts. |
| B2-06 | Synthetic tiles | A synthetic tile exists exactly for each empty cell containing water. All are lattice-aligned, native-sized and non-overlapping, and named `SEA_e<left>n<bottom>.tif`. Request-local views built from the sea view are accepted by `v1.index_sources`. |
| B2-07 | Identity and reproducibility | The rebuild reproduces the `view_id` and every file hash. The cache namespace is as specified. Plan keys differ from raw plan keys wherever a dependency changed. F manifests record the policy pair and `view_id`. |
| B2-08 | F integration and regression | `sea-2.0` works through the registry. The F diff is limited as in B2-01. All F tests pass unchanged. The raw-mode Cheung Chau `run_id` is unchanged (`e608af7f…b1ca`). Published surface layers equal the view's classes. |
| B2-09 | Land regression, Cheung Chau | Over the 65 frames of (a), on land (class 0), `sea-2.0` against raw: (i) zero shaded → sunlit; (ii) class 254/255 pixels stay shade 255; (iii) every sunlit → not-sunlit change is explained by a demonstrated blocker or by a rise in the tile's distant-obstruction threshold (old and new `threshold_deg` reported per tile). The transitions of former Quality 2 land pixels to 0, 1 and 255 are reported per frame. |
| B2-10 | Urban guard, Central | For (b), gates (i) and (ii) of B2-09 hold on land. Class counts are reported, including the share of Victoria Harbour NoData within the Central halo that became water. That share is reported, not gated. |
| B2-11 | Sea-target consistency | At 3 instants, at least 200 sampled water pixels per instant, including water next to tall structures, get the same label from the engine as from an independent direct-ray reference on the view, within the engine's documented equality tolerance. This is numerical consistency only. |
| B2-12 | Void-impact diagnostic | (c) completes. The counterfactual view differs from the sea view only at class-255 pixels, which hold h_sea. For every frame, the metric counts reconcile with the rasters and sum to \|L\|. The output validates against its schema. The tool refuses when the sea-2.0 run is missing or does not match. It writes nothing inside the F run folder. |
| B2-13 | iB5000 and sensitivity reports | Every report item in design item 9, including the sensitivity report, is computed with the separate reader environment, for the territory, Cheung Chau and Central, including the northern-boundary listing. No parameter changed. |
| B2-14 | Scope, resources, write scope | Listings before and after show no writes to `data/raw/`, to existing namespaces under `data/processed/`, or to existing `outputs/` folders. Only authorized computations ran. The ledger of job time, view-build time, peak memory and disk use is within budget. |
| B2-15 | Tests, docs, handoff | Automated tests on synthetic fixtures; the full existing suite passes unchanged. POLICY, GUIDE, DESIGN and DEVELOPMENT_REPORT are present, and every required limitation is stated. The Hong Kong profile and schemas are committed. An evidence manifest is present. One local commit, full SHA reported, no push. |

## Decisions and release

- **Marking.** Each of B2-01 to B2-15 is marked PASS, FAIL or NOT VERIFIED, with evidence paths and commands.
- **Acceptance.** `SW-SEA-POLICY-2.0` is accepted only if every criterion passes in a separate independent-acceptance conversation.
- **What acceptance means.** Engineering acceptance and numerical consistency. The iB5000 figures describe agreement with a map, not observational accuracy. Shade on water and on land remains NOT VERIFIED against observations.
- **What acceptance does not authorize:**
  - adding exception zones;
  - filling voids;
  - territory runs;
  - V3;
  - a push.

  Each needs its own decision. The four-region solstice measurement is run by the user with the delivered tools, and its result decides whether a void-filling version is drafted (D-010, Q2).
- **Fixes.** Each fix needs a new commit SHA and targeted re-acceptance. Failure evidence is preserved.
