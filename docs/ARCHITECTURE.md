# Architecture

Status: describes tag `mac-v1.0` (H1.0 accepted at `2edd8bc`). The engine rules are those of `SW-V1-POLICY-1.0`; the fill rule is `SW-SEA-POLICY-2.2`; city ingestion is `SW-INGEST-POLICY-1.0`. Earlier architecture notes are records under [records/](records/).

## 1. The package

All code is one package, `shade_watch`. Importing it loads no sub-package; `shade_map` and `plan_shade_map` are loaded on first use.

| Part | Role | Main entry |
| --- | --- | --- |
| `engine/` | Solar position, horizon scans, horizon cache, classification, single requests (V1) and local batches (V2) | `python -m shade_watch.engine.v1`, `python -m shade_watch.engine.v2` |
| `region.py` | Two-corner region input; builds the request-local source view; never computes shade | `python -m shade_watch.region` |
| `publish/` | Configs, plans, runs and publication of results (`shade_map`) | `python -m shade_watch {plan,run,prune}`, `from shade_watch import shade_map` |
| `fill/` | The DSM-only fill (`sea-2.2`): profiles, view build, fill-impact; a report-only iB5000 comparison | `python -m shade_watch.fill {build,fill-impact}` |
| `city/` | City profiles and lossless registration of a city's DSM sheets | `python -m shade_watch.city register <city>` |

Inside `engine/`:

| File | Role |
| --- | --- |
| `solar.py` | NOAA approximation of the sun's position |
| `spatial.py` | Index of source tiles and bounded raster reads |
| `horizon.py` | Horizon scan along the sun's direction (Numba) |
| `v1_cache.py` | Content-addressed horizon cache entries per native tile and direction |
| `shade_watch.py` | Classification into shade, quality and surface; the older pipeline entry |
| `pipeline.py` | Shared helpers (`fingerprint`, `profile`, memory monitor) and the older pipeline |
| `v1.py` | Plan and query one request of instants |
| `v2.py`, `v2_runner.py`, `v2_worker.py`, `v2_state.py` | Durable local batches: submit, run, resume, cancel |

`pipeline.py` and `shade_watch.py` still mix engine helpers with the older pipeline. Splitting them is planned for a later package.

## 2. Data flow

```text
data/raw/<city>/                 raw DSM, read-only
   │  city register (Rotterdam)   cut sheets into native cells
   ▼
data/derived/catalogues/<city>/<ingest_id>/
   │  fill build                  fill every missing value at 0 m (sea-2.2)
   ▼
data/derived/views/<view_id>/    filled DSM view: tiles, surface classes, manifest
   │  plan                        corners → native cells, frames, cache gates
   ▼
work/source_views/<key>/         request-local view of the tiles within 1 km
   │  run (engine V2 batches)     horizon per tile and 5° direction, reused across dates
   ▼
data/cache/horizon/<namespace>/  horizon cache
   │  classify each frame
   ▼
runs/<root>/<name>/<YYYYMMDD>/<HHMM>/   shade, quality, surface (+ VRT, full image), frame.json
```

- Hong Kong's catalogue is the raw folder itself (`data/raw/hong_kong/dsm_cedd_2020/D12.DSM.TIFF`); Rotterdam's is produced by registration.
- With `dsm_source: raw`, the plan uses the raw catalogue and no view.
- `fill-impact` recomputes the same frames on the raw DSM in its own cache namespace (`fill_impact_<id12>`) and writes a dependency report under `<root>/_diagnostics/fill_impact/<name>/`.

## 3. Identities

Results are identified by content, not by location. Moving the repository does not change them.

| Identity | Made of | Changes when |
| --- | --- | --- |
| Horizon cache key | Content of `engine/horizon.py`, `engine/spatial.py`, `engine/v1_cache.py`; hash and geometry of each source tile | One of those three files or a source tile changes |
| View ID | Raw file hashes, fill profile, the eight build files of `fill/`, library versions | Code of the fill build, the profile, the raw data or a library version changes |
| Ingest ID | Sheet hashes, city profile, the four files of `city/`, library versions | One of those changes |
| Run ID | Region, frames, source identity, engine file hashes, policies, publication format, city | Any of these changes; pixels need not change |

Cache namespaces: `view_<view_id12>` for `sea-2.2` runs, `<cache_namespace>_<city_id>` for raw runs (default `raw_hong_kong`, `raw_rotterdam`), `fill_impact_<id12>` for counterfactuals.

The view pointer `data/derived/views/current-<profile>.json` records sizes and modification times of the catalogue files. A copied or touched catalogue therefore needs the view to be rebuilt, which reproduces the same tile contents.

## 4. Runtime folders

| Folder | Written by | Content |
| --- | --- | --- |
| `runs/<root>/` | `run`, `shade_map` | Publications; every output root is a folder directly under `runs/` (default `runs/main`) |
| `work/runs/<name>-<id12>/` | `run` | Engine batch state; removed by `prune --yes` |
| `work/locks/` | `run` | One lock per run name |
| `work/source_views/<key>/` | `plan`, `run` | Request-local source views (symbolic links) |
| `work/fill_impact/` | `fill-impact` | Counterfactual work |
| `work/engine/` | engine commands | Default work folders of the engine's own commands |
| `data/derived/`, `data/cache/horizon/` | `fill build`, `city register`, `run` | Views, catalogues, caches |

The tools refuse an output root inside `data/`, `work/`, `baselines/`, `archive/` or a DSM folder, and a folder they did not create.

## 5. Platform

- macOS with the repository's `.venv` (Python 3.12, `requirements.lock.txt`).
- File locks use `fcntl`. Batch state requires a local file system: on macOS a local volume; on Linux ext2/3/4, xfs, btrfs, overlay, tmpfs, exfat or vfat. Network file systems are refused.
- Exploration switch on branch `c2-explore-nfs-switch` (C2.0 discovery, not accepted): on Linux, `SHADE_WATCH_ALLOW_NFS=1` in the environment lets batch state, cache and output live on NFS (`nfs`, `nfs4`) and prints a warning. Other network file systems stay refused. With the switch on, run at most one V2 job (`shade_watch run` or `fill-impact`) at a time in the repository; `fill build` and `city register` do not use batch state.
- Source views and the Hong Kong view use symbolic links to raw tiles.
- Linux support is package C2.0. Native Windows is not supported.

## 6. Limits

- Only 0.5 m DSMs in a projected metre CRS.
- The 1 km search and the 5° direction bins are model boundaries; their approximation error is not quantified.
- The cache identity contains a fixed text naming EPSG:2326 for every city.
- Observational accuracy is NOT VERIFIED for Hong Kong and Rotterdam; Rotterdam surface labels are NOT VERIFIED.
