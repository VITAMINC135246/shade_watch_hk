# Sea-support preparation and development checks

Status and completed phases are in DEVELOPMENT_REPORT.md. No independent
acceptance is implied. The authoritative decisions are in POLICY.md and the
frozen SW-SEA-AC-1.0 contract. Commands run from the repository root.

The standard FGDB reader uses an environment **outside** the repository, with
`requirements.tools.lock.txt`. Development used
`/private/tmp/shade_watch_tools_20261029`; a fresh external environment may be
created with Python 3.12 and installed from that lock. Never install these
packages into the engine `.venv`. The temporary environment may be removed by
the operating system; the lock is the reproducibility record.

Map extraction refuses an existing destination and checks exact counts:

```sh
/private/tmp/shade_watch_tools_20261029/bin/python tools/sea_view/extract.py \
  --source data/raw/coastline/ib5000_seamless_20261012/iB5000.gdb \
  --dictionary 'data/raw/coastline/resources_iB5000_FGDB/iB5000 Data Dictionary - FGDB v1.3.pdf' \
  --destination data/processed/coastline/ib5000_20261012
```

Existing local extraction must be retained; this is a reproducibility example,
not permission to overwrite it. GeoJSON includes holes and EPSG:2326 coordinates.
`manifest.json` contains source/dictionary/vector hashes, counts, CRS, versions
and six deterministic make_valid repair records. No custom FGDB parser is used.

The unchanged engine environment consumes this export:

```sh
.venv/bin/python -m pytest tests/test_sea_masks.py -q
.venv/bin/python -m tools.sea_view.checks
```

The second command measures the exact frozen Cheung Chau halo window. Rasterio
pixel-centre masks are authoritative. `edge_diagnostic` is a PIL-only comparison
for explaining planning-reference edge effects; it must never create production
masks. `verify_edges.py`, run in the tools environment, checks sampled centres
against Shapely geometry containment.

The one authorized territory scan is `python -m tools.sea_view.scan` in the
engine environment. It refuses to run if `docs/sea/evidence/territory-scan.json`
already exists. Do not delete that guard or repeat the scan without new
authorization. It reads native grids, checks a one-pixel halo for 8-neighbour
samples, retains exact sample values for NumPy linear percentiles, and stops
before 30 minutes or 12 GiB. A median outside [1.30,1.90] stops subsequent phases.

The candidate views expose `tiles/`, `surface/`, and `manifest.json` beneath
`data/processed/dsm_views/sea_fill_v1/<view_id>/`. After the recorded S06 gate passed, each view’s `tiles/` was supplied to existing `src.v1`/`src.v2` via `dsm_dir`, with
`data/processed/shade_v1/sea_fill_v1_<view_id>` as a fresh cache. Run targets and
instants must remain within the frozen Cheung Chau/Central authorization. The report identifies completed stages and open criteria. The engine tag remains SW-V1-POLICY-1.0; the effective policy
also requires the view manifest.

Limitations: no boats or pontoons; no tide model; 2026 map versus 2019–20 DSM
reclamation drift; unknown LAF piers/coastal slivers; reservoirs unchanged;
sea-target labels less certain than land; shade is not cooling or ΔT. Neither
numerical checks nor the height gate establish observational accuracy.

## Authorized view builder and provenance helpers

The development report records the completed S06 gate. Build one of the two
fixed scopes (there is no territory build option):

```sh
.venv/bin/python -m tools.sea_view.build cheung_chau
.venv/bin/python -m tools.sea_view.build central
```

The builder stages only under `outputs/sea_dev_build`, validates every file,
and publishes beneath `data/processed/dsm_views/sea_fill_v1/<view_id>`. A repeat
build verifies identical manifests and file hashes and retains the existing
view. Unchanged tiles may be byte-identical copies; filled tiles and surfaces
use fixed DEFLATE settings. Scoped source files stay read-only.

`tools.sea_view.helpers.read_surface_window(view, bounds)` returns a uint8 array
and transform for aligned bounds, with the same 20-million-pixel read ceiling as
V1. `effective_policy(result_index_path)` checks the manifest identity and source
hashes and reports the engine/surface policy pair and view_id. A custom-bounds
result can resolve the view through its adjacent `run_definition.json`.

Development runs used V2 with scientific outputs only, two workers, a new
view-specific cache and output directories beginning `outputs/sea_dev_`.
Cheung Chau uses the unchanged 2026-01-07 10-minute daylight list (65 frames).
Central uses 08:30, 12:30 and 15:10 HKT. The raw Central comparison has a separate
`sea_fill_v1_raw_central` cache; no historical cache is written.

Sensitivity views use only the first Cheung Chau target and its halo, live under
`sea_fill_v1/diagnostic/<view_id>`, carry `SW-SEA-DIAGNOSTIC-1.0`, and use caches
`sea_fill_v1_diagnostic_<view_id>`. They are not the frozen production policy.
Permitted pairs are (h,tolerance) = (0,0), (3,0), (1.6,2.5), (1.6,5). Diagnostic
tolerance extends strict sea into LAF by Euclidean distance between native pixel
centres; neither-class areas remain unknown. No tolerance enters production.

The bounded harness `tools.sea_view.ledger` checks process inspection before
starting a child, measures the full child tree, and stops the job before frozen
limits. Its stage evidence and ledger are retained in `docs/sea/evidence`.
Do not repeat scientific stages in the same output directory or delete guards;
a follow-up run requires a fresh, explicitly budgeted workload.
