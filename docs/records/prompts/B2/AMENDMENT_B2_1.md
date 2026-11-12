# Package B2.0 contract amendment `SW-B2.1`

Status: frozen 2026-11-04 by user approval. Record this file's SHA-256 before development.

This amendment changes the frozen `SW-B2.0` (`docs/prompts/B2/ACCEPTANCE_CONTRACT.md`, SHA-256 `b8b5473b51af318859d7a1619b616b4acfa7d9cf9ccd63ca0ffaf238fee40e1a`). It corrects factual errors found before development started, and it names the accepted F1.0 commit.

- No criterion is weakened, and no item is added or removed.
- Every rule of `SW-B2.0` still applies unless a section below replaces it.
- Decision record: D-014.

## A1. Raw-mode identity regression

This section replaces the `run_id` sentence in design item 7 and the matching clause in B2-08.

`e608af7ffe4181f3d097ce3f776f464b5b79fc67f1c1e5dc12bc6806a421b1ca` is the `run_id` of the F1.0 development region config named `f1_cheung_chau`, saved at `outputs/shade_map_f1_20261031/f1_cheung_chau/region_config.json`. It is not the `run_id` of `config/regions/cheung_chau.json`, because `run_id` includes the region name.

The requirement is now:

- Use two configs:
  - `config/regions/cheung_chau.json`;
  - a copy of `outputs/shade_map_f1_20261031/f1_cheung_chau/region_config.json`, made outside `outputs/`. The original is read-only.
- For each config, a raw-mode `plan` at the candidate must give the same `run_id` as a raw-mode `plan` at the accepted F1.0 commit (A2).
- For the `f1_cheung_chau` copy, the expected value at the accepted commit is `e608af7f…b1ca`. If the value at the accepted commit differs, report both values and stop for a decision before any shade run.

## A2. Accepted F1.0 commit

- Wherever `SW-B2.0` refers to "the independently accepted F1.0 commit", it means `35225fd9547a00e4df202e7ab30204c633b2c845`. Its acceptance is recorded in:
  - `docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md`;
  - `docs/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a_ADDENDUM_1.md`.
- Design item 7's limit on F changes is measured as the diff from that commit.

## A3. Raw reference for Cheung Chau

In the authorized scope, item (a) says "compared with the F1.0 raw results of the same config". This means the same region parameters.

The F1.0 development run `outputs/shade_map_f1_20261031/f1_cheung_chau/` (read-only) has identical parameters under a different name. It may serve as the raw reference. Alternatively, rerun raw under a new name.

## A4. Output location

F1.0 accepts an `output_root` only inside the repository (`outputs/`, or an F-created root). The void-impact output path `<output_root>/_diagnostics/void_impact/<name>/` is therefore inside the repository. The tool must not create or require any location outside it.
