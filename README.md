# Shade Watch HK

Shade maps from a digital surface model (DSM): for each 0.5 m pixel and each instant, whether the sun is blocked within a 1 km sunward search. Results are GeoTIFFs organised by date and time. Hong Kong (CEDD 2020 DSM) and Rotterdam (AHN DSM 0.5 m, two sheets) are registered.

This is the first clean version on macOS, tag `mac-v1.0`. The repository layout and names follow [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## What a result is, and is not

- Codes: 0 sunlit, 1 shaded, 255 invalid or uncertain. 255 is never shade and never sunlight. See [docs/OUTPUT_CODES.md](docs/OUTPUT_CODES.md).
- With the default source `sea-2.2`, every missing DSM value is filled at 0 m in the city's vertical datum. Labels that depend on filled data are model results under that assumption; measure the dependence with `fill-impact`.
- Not a cooling effect, temperature or ΔT.
- **Observational accuracy is NOT VERIFIED** for Hong Kong and for Rotterdam. The 1 km search and the 5° direction bins are model boundaries, not proven accuracy.
- A regional result is not a territory-wide or city-wide result.

## Quick start (macOS)

From the repository root, with the repository's `.venv` (Python 3.12, packages in `requirements.lock.txt`):

```sh
cp config/machine.example.json config/machine.local.json     # once; git ignores it
.venv/bin/python -m shade_watch.fill build                   # once per DSM catalogue (Hong Kong: about 35–40 min)
.venv/bin/python -m shade_watch plan config/regions/<name>.json
caffeinate -dims .venv/bin/python -m shade_watch run config/regions/<name>.json
```

Or from Python:

```python
from shade_watch import shade_map
shade_map([820250, 807200], [821750, 808400], "2026-06-21", name="my_region", crs="hk1980")
```

Results appear under `runs/main/<name>/<YYYYMMDD>/<HHMM>/`. The step-by-step guide is [docs/GUIDE.md](docs/GUIDE.md) (繁體中文：[docs/GUIDE.zh-TW.md](docs/GUIDE.zh-TW.md)).

Supported: macOS. Linux is the next package (C2.0). Native Windows is not supported.

## Where things are

| Path | Content |
| --- | --- |
| `shade_watch/` | The package: `engine/`, `region.py`, `publish/`, `fill/`, `city/` |
| `config/` | Cities, fill profiles, region examples, schemas, machine example |
| `tests/` | Test suite, including the layout check `tests/test_layout.py` |
| `web/viewer/` | Result viewer and request generator (local, read-only) |
| `docs/` | Index, conventions, architecture, guide, output codes; package records |
| `data/`, `runs/`, `work/`, `baselines/`, `archive/` | Not in Git: raw and derived data, results, work files, regression baselines, history |

The full map of documents is [docs/INDEX.md](docs/INDEX.md); the design is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Status

| Package | Content | Status |
| --- | --- | --- |
| E1.0, E2.0 | Engine: arbitrary instants; reliable local batches | Accepted (`796ac8a`, `356f611`) |
| F1.0 | `shade_map` function, configs and publication | Accepted (`35225fd`) |
| B2.2 | DSM-only fill policy `SW-SEA-POLICY-2.2` | Accepted (`7707c51`) |
| G1.0 | Cities; Rotterdam | Accepted (`af6fca9`) |
| H1.0 | One layout and one naming scheme | Accepted (`2edd8bc`) |
| C2.0 | Running on a Linux machine | Not started |

Each package has a frozen contract and an independent acceptance report; [docs/INDEX.md](docs/INDEX.md) lists them.
