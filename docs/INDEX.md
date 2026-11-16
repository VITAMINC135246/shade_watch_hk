# Documentation index

Start here. Living documents describe the current version and are kept up to date. Records describe a past stage and are never edited (see [CONVENTIONS.md](CONVENTIONS.md), section 1).

## Living documents

| Document | Content |
| --- | --- |
| [../README.md](../README.md) | What the project is, quick start, status |
| [GUIDE.md](GUIDE.md), [GUIDE.zh-TW.md](GUIDE.zh-TW.md) | Step by step: set up, plan, run, view, report numbers; cities |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Packages, data flow, identities, runtime folders |
| [OUTPUT_CODES.md](OUTPUT_CODES.md) | Codes of the shade, quality and surface layers; reporting rules |
| [CONVENTIONS.md](CONVENTIONS.md) | Names, layout, identity rules, what may be deleted, what "clean" means |
| [../web/viewer/README.md](../web/viewer/README.md) | The result viewer and request generator |

## Packages

Each package has a frozen contract, a developer report and an independent acceptance report. Earlier names are mapped to the current scheme in [CONVENTIONS.md](CONVENTIONS.md), section 2.

| Package | Earlier name | Content | Status | Contract | Acceptance report |
| --- | --- | --- | --- | --- | --- |
| E1.0 | V1 | Engine: one instant or a day, any rectangle | Accepted at `796ac8a` | [records/prompts/v1/](records/prompts/v1/) | [records/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md](records/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md) |
| E2.0 | V2 | Engine: reliable local batches | Accepted at `356f611` | [records/prompts/v2/](records/prompts/v2/) | [records/v2/INDEPENDENT_ACCEPTANCE_356f611.md](records/v2/INDEPENDENT_ACCEPTANCE_356f611.md) |
| E3.0 | V3 | Seven-region campaign | Prepared only, never run | [records/prompts/v3/](records/prompts/v3/) | — |
| A1.0, A1.1 | `SW-RGN-AC-1.0`, `1.1` | Two-corner region input | Reviewed | [records/prompts/region/](records/prompts/region/) | [planning/reviews/](planning/reviews/) |
| B1.0 | `SW-SEA-AC-1.0` | First sea view | Acceptance stopped | [records/prompts/sea/](records/prompts/sea/) | — |
| B2.2 | `SW-B2.2` | DSM-only fill policy `SW-SEA-POLICY-2.2` | Accepted at `7707c51` | [records/prompts/B2/](records/prompts/B2/) | [records/sea2/INDEPENDENT_ACCEPTANCE_B2_2_7707c511a442.md](records/sea2/INDEPENDENT_ACCEPTANCE_B2_2_7707c511a442.md) |
| F1.0 | `SW-F1.0` | `shade_map` function, configs, publication | Accepted at `35225fd` | [records/prompts/F1/](records/prompts/F1/) | [records/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md](records/shade_map/INDEPENDENT_ACCEPTANCE_35225fd9547a.md) with addendum |
| G1.0 | `SW-G1.0` to `SW-G1.2` | Cities; Rotterdam | Accepted at `af6fca9` | [records/prompts/G1/](records/prompts/G1/) | [records/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025_ADDENDUM_1.md](records/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025_ADDENDUM_1.md) |
| D2.0 | `SW-RUN-AC-1.0` | Background runner and web API | Cancelled | [records/prompts/runner/](records/prompts/runner/) | — |
| D3.0 | — | Result viewer and request generator | Planner's own checks only | — | [../web/viewer/README.md](../web/viewer/README.md) |
| H1.0 | `SW-H1.0` to `SW-H1.5` | One layout and one naming scheme | Accepted at `2edd8bc` | [packages/H1.0/](packages/H1.0/) | [packages/H1.0/ACCEPTANCE_REPORT_2edd8bcfda81.md](packages/H1.0/ACCEPTANCE_REPORT_2edd8bcfda81.md) |
| C2.0 | — | Running on a Linux machine | Not started | — | — |

Failed candidates and their reports are kept next to the accepted ones.

## Records

- [records/](records/): every document of the stages before H1.0, byte-identical to its state before the move. Links inside a record point to the layout of its own time; use the commit the record names, or the move table [packages/H1.0/evidence/move_table.tsv](packages/H1.0/evidence/move_table.tsv).
- [planning/](planning/): snapshot of the planner's decision log (Traditional Chinese) and planner reviews.
- [packages/](packages/): one folder per package from H1.0 on.

## Data and results (not in Git)

| Folder | Content |
| --- | --- |
| `data/raw/hong_kong/`, `data/raw/rotterdam/` | Raw data, read-only |
| `data/derived/` | City catalogues and fill views |
| `data/cache/horizon/` | Horizon caches; recomputable |
| `runs/` | Published results; default output root `runs/main` |
| `baselines/` | Accepted results used by regression checks |
| `work/` | Engine work folders, locks, source views, diagnostics |
| `archive/` | Earlier outputs, earlier views and catalogues, review evidence |
