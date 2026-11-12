# Project conventions

Adopted 2026-11-12 (decisions D-023 to D-025); the output-root rule of section 3 was changed on 2026-11-13 (D-029). They apply from package H1.0 on. Package H1.0 brings the repository to this layout; until it is accepted, the tree still has the old layout.

These conventions answer four questions: what things are called, where they live, what may be changed or deleted, and how "clean" is checked.

## 1. Three kinds of files

Every file or folder belongs to exactly one kind.

| Kind | What it is | May it change? | May it be deleted? |
| --- | --- | --- | --- |
| Living | Code, config, tests, current documents, these conventions, the index | Yes. A change to code needs a contract and an independent acceptance. | Yes, with the code, under a contract |
| Record | Frozen contracts and prompts, acceptance reports, development reports, evidence, decision log, failed candidates and their reports | No. Content and file names stay. A record may only move as part of a block. | No |
| Recomputable | Caches, work folders, diagnostic counterfactuals | Not applicable | Yes, from an itemised list that the user confirmed |

Two special cases:

- **Raw data** (`data/raw/`) is read-only.
- **Baselines** are accepted results that regression tests compare against. They are records, kept at a fixed place.

## 2. Names

### 2.1 Packages of work

One scheme: a letter and a version, for example `F1.0`, `B2.2`.

| Letter | Subject |
| --- | --- |
| A | Region input (two corners) |
| B | Fill (sea and NoData) |
| C | Other computers and operating systems |
| D | Web |
| E | Engine |
| F | Function and publication |
| G | Cities |
| H | Housekeeping |

- Contract ID: `SW-<version>`, for example `SW-H1.0`. An amendment takes the next minor version.
- Acceptance items: `<letter><major>-<two digits>`, for example `H1-01`.
- Policy IDs that are written into data keep their names: `SW-V1-POLICY-1.0`, `SW-SEA-POLICY-2.2`, `SW-INGEST-POLICY-1.0`.

### 2.2 Earlier names

Old files keep their names. This table is the mapping.

| Earlier name | Name under this scheme | Status on 2026-11-12 |
| --- | --- | --- |
| V1 (items A01–A14) | E1.0 | Accepted |
| V2 (items B01–B14) | E2.0 | Accepted |
| V3 (items C01–C16) | E3.0 | Prepared, not executed |
| `SW-RGN-AC-1.0` / `1.1` (R01–R12) | A1.0 / A1.1 | Reviewed |
| `SW-SEA-AC-1.0` (S01–S14) | B1.0 | Acceptance stopped |
| `SW-B2.0`, `SW-B2.1` | B2.0, B2.1 | Superseded by B2.2 |
| `SW-B2.2` | B2.2 | Accepted |
| `SW-RUN-AC-1.0` | D2.0 | Cancelled |
| Result viewer and request generator | D3.0 | Self-checked by the planner only |
| WSL2 smoke test | C1.0 | Not executed |
| `SW-F1.0` | F1.0 | Accepted |
| `SW-G1.0`, `SW-G1.1`, `SW-G1.2` | G1.0 to G1.2 | Accepted |

Next packages: H1.0 (this clean-up) and C2.0 (other operating systems).

### 2.3 Files

- Code, config and folders: lower case with underscores.
- Documents: upper case with underscores (`GUIDE.md`, `DESIGN.md`).
- From H1.0 on, each package version has one folder `docs/packages/<version>/` with fixed names: `CONTRACT.md`, `AMENDMENT_<n>.md`, `DEVELOPMENT_PROMPT.md`, `ACCEPTANCE_PROMPT.md`, `DEVELOPMENT_REPORT.md`, `DEVELOPMENT_REPORT_REPAIR_<n>.md`, `ACCEPTANCE_REPORT_<sha12>.md`, `ACCEPTANCE_REPORT_<sha12>_ADDENDUM_<n>.md`, `evidence/`.
- A published run keeps the accepted structure `<name>/<YYYYMMDD>/<HHMM>/`.
- Language: repository documents, contracts, prompts and comments are in English. The user guide also has a Traditional Chinese version. The decision log is in Traditional Chinese.

## 3. Layout

```
shade_watch_hk/
├── README.md
├── shade_watch/             the Python package
│   ├── engine/              horizon, solar, spatial, V1 query, V2 batch
│   ├── region.py            two corners to engine requests
│   ├── publish/             the shade_map function, CLI and publication
│   ├── fill/                fill policy: view builder, source, fill-impact
│   └── city/                city profiles and ingestion
├── config/                  cities/ regions/ sea_profiles/ schema/ engine/
├── tests/
├── web/viewer/              result viewer and request generator
├── docs/
│   ├── INDEX.md  CONVENTIONS.md  ARCHITECTURE.md  OUTPUT_CODES.md
│   ├── GUIDE.md  GUIDE.zh-TW.md
│   ├── design/              current design and policy descriptions
│   ├── packages/            one folder per package version, from H1.0
│   ├── planning/            decision log snapshot and planner reviews
│   └── records/             documents of every stage before H1.0, unchanged
├── legacy/                  retired code, config and web prototypes
├── data/
│   ├── raw/<city>/          raw data, read-only
│   ├── derived/             catalogues/<city>/<ingest_id>/, views/<view_id>/
│   └── cache/horizon/       horizon caches, recomputable
├── runs/                    published results, one folder per output root (default: runs/main)
├── baselines/               accepted results used by regression tests
├── work/                    engine work folders, locks, source views, diagnostics
└── archive/                 earlier outputs and review folders, as they were
```

- `data/`, `runs/`, `work/`, `baselines/` and `archive/` are not in Git, apart from `README.md` files under `data/raw/`.
- Every output root is a folder directly under `runs/`. `runs/` itself is a container and is never used as an output root.
- Records keep their content. A link inside a record refers to the tree at the commit the record was written for; after a move it may not resolve. `docs/INDEX.md` gives the present locations.

## 4. Identity

Results are identified by content hashes. A clean-up must know which names take part in them.

| Identity | Defined by | Consequence of a change |
| --- | --- | --- |
| Horizon cache key | The content of `engine/horizon.py`, `engine/spatial.py`, `engine/v1_cache.py`, and the hashes and geometry of the input tiles. No path. | Every horizon cache must be recomputed |
| View ID | The content of the eight view-builder files of `fill/`, the fill profile, the hash of every catalogue file, library versions | The view must be rebuilt and compared |
| Ingestion ID | The ingestion code, the city profile, the raw sheet hashes | The catalogue must be ingested again |
| Run ID | Region config, frames, source identity, engine file hashes, policies, publication format, city | A new run number; pixels do not change |

A change that touches one of these is planned, stated in the contract, and verified: equal file hashes for views and catalogues, zero recomputed directions where the cache key must not change, and pixel-identical regression runs.

## 5. Deleting and archiving

- Recomputable data may be deleted from an itemised list that the user confirmed. The list and the result go into the decision log.
- Records are archived, not deleted.
- Data of a candidate that was never accepted may be deleted; its manifest and reports are kept.
- Apart from the `README.md` files under `data/raw/`, nothing under `data/`, `runs/`, `baselines/` and `archive/` is in Git. A deletion there cannot be undone.

## 6. What "clean" means

`tests/test_layout.py` checks the layout as part of the test suite: the top level and `docs/` hold only the entries of section 3; the old top-level names do not exist; no living file refers to an old location or import; records match their manifest; the cache-key files have their recorded hashes.

## 7. Commits and versions

- The planning conversation commits its own work (contracts, records, living documents). A developer commits a finished candidate. Nothing is pushed without the user.
- A contract is frozen by the commit that adds it. Its SHA-256 is recorded before development.
- Version tags: `pre-h1.0` marks the tree before the clean-up; `mac-v1.0` marks the first clean version on macOS.
