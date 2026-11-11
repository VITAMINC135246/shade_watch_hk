# F1.0 design (SW-F1.0)

The frozen contract SHA-256 is recorded in `evidence/start.json` before edits.
Only the new F package, tests, configs, schemas and these documents are changed.
The engine and A1.1 adapter are dependencies, not implementation targets.

## Modules and configuration

`config.py` implements a small, hand-written JSON Schema validator and semantic
corner/date/time checks. Machine and region schemas reject unknown keys at every
level. Defaults are materialised in the normalised region copy; date ranges and
optional HKT offsets are canonicalised. Machine paths resolve from the repository
root and never enter the scientific/publication identity.

`sources.py` defines a provider protocol and registry: catalogue, surface reader,
cache namespace, policy pair and content identity. A read-only identity preview
rejects source changes before the adapter can create a new view for a conflicting
run. It reads catalogue headers and uses engine snapping and the engine's halo
constant; the adapter still owns all actual planning and view publication.
Raw surface codes are 0 for observed DSM and 255 for missing DSM.
With `sea-2.2`, codes 0 through 4 describe the surface within the view,
and 255 describes the area outside the view. See [output codes](../OUTPUT_CODES.md). Publication uses the protocol
without testing the provider name. Tests substitute a fixture provider.

`planning.py` passes daylight dates directly to the adapter; explicit times are
filtered using the engine's fixed daylight reference. The adapter owns snapping,
spatial partitioning, temporal admission and source views. V2 owns batch resource
admission and estimates. F enumerates publication cells from the catalogue lattice,
clips them to the adapter's resolved grid and labels all estimates explicitly.

`publication.py` writes/reads lossless cells and relative VRTs and computes counts.
`runner.py` owns locks, atomic manifests, durable V2 submission/resume and prune.
`__init__.py` and `__main__.py` expose the same config-driven code path to Python
and the three CLI actions. No additional packages are needed.

## Canonical identity

Canonical JSON uses sorted keys, compact separators, finite numbers and UTF-8.
Its SHA-256 is `run_id`. The document contains the normalised region, expanded
HKT/UTC frame list, source names/content hashes including auxiliary inputs, ten
engine hashes, provider policy pair and publication format version. Paths,
machine settings, estimates, cache availability, timings and the F commit are
excluded. The full identity document is retained in the manifest for inspection.

## State and publication

Planning is read-only except for the adapter's immutable request-local views.
Before writes, reject invalid corners, foreign/conflicting run folders and disk
guards. New publication roots have an F ownership marker; an existing unmarked
root is refused. A common name lock under `outputs/shade_map_work/.locks/`
serialises competing runs, including differing identities. The run work folder is
`outputs/shade_map_work/<name>-<run_id12>/`; its owner record permits safe prune.
Resolved publication paths are checked against `data/`, the configured and
provider catalogues, and their resolved backing-file directories before the
adapter can write a source view. Ancestor ownership is checked outside the
repository too; only repository/output containers and verified F roots are trusted.

Persist adapter sidecars and immutable batch plans before submission. On resume,
use saved batch IDs and V2 state: completed batches are verified, never resubmitted;
incomplete batches use `resume_batch`. F does not regenerate V2 definitions from
warm-cache estimates. Publication writes `<HHMM>.partial`, verifies every cell
against `read_region_window` (including transforms), verifies VRT/full views, then
renames and atomically updates the manifest. A killed partial is removed and
rebuilt. A renamed frame not yet recorded is recovered from its verified record.
Published frames are immutable and reused after hash verification.
Complete-run paths also discard stale partial directories under the name lock.
If an associated final cannot be verified, the manifest records its pending redo
before removing the recovery cue, then the ordinary durable engine/publication
path restores it. Final verification refuses any remaining `.partial` entry.

Frame records hash every layer file. The run manifest hashes those records,
region config and summaries. A JSON record cannot hash its own bytes: the run
manifest therefore carries a canonical self-integrity digest excluding that one
digest field, while its file table covers every other published file. A complete
rerun verifies these hashes without modifying the run. Prune requires complete,
verified publication and removes only the ownership-checked run work folder.

## Planned checks and evidence

| Contract | Planned check / evidence |
| --- | --- |
| F1-01 | preflight SHA, ancestry, engine/adapter byte hashes, final scope diff |
| F1-02 | schema-rule walker; malformed configs; machine-independent identity |
| F1-03 | both CRSs, order/range/finite errors, projected order, no-write listings |
| F1-04 | engine date equivalence including solstices; stepping/filter/duplicates |
| F1-05 | three direct adapter equivalences; plan schema/status/read-only checks |
| F1-06 | raw and injected fixture provider through identical publication |
| F1-07 | clipped/missing cells; portable VRT copy; path checks in real runs |
| F1-08 | every real frame/cell/VRT/full image vs engine; surface vs DSM |
| F1-09 | source-view list gate, cold Cheung Chau run vs all 65 reference frames |
| F1-10 | frozen fractional WGS84 sparse rectangle; independent cold V1 references |
| F1-11 | actual SIGKILL during compute/publication; task/frame reuse; conflicts/lock |
| F1-12 | record schemas/hash/count/fraction checks; dry-run/prune/rerun checks |
| F1-13 | protected listings; monitored real-job wall/RSS/disk ledger |
| F1-14 | synthetic/full test logs, guide/report, evidence manifest, one local commit |

Real computations are restricted to contract runs (a), (b), (c). The campaign
watchdog charges all real-DSM jobs against 3600 seconds, 12 GiB sampled process
tree RSS and 20 GiB new artifacts. Exhausted checks are NOT VERIFIED; no budget
extension or additional region is implied. Independent acceptance remains separate.

## G1 native city grids

G1 adds `shade-map-region-1.1` and `shade-map-publication-1.1`. City
resolution and clock validation precede adapter calls. The selected city
supplies the projected CRS, time zone, daylight reference and source line to
the adapter and engine. WGS84 plans record the local PROJ operation and
versions. The run identity includes the city record and snapped bounds.

The source provider receives a machine dictionary scoped to the city’s
catalogue and fill profile. Raster and VRT georeferencing comes from the
resolved grid. The plan reports missing native cells in the 1 km dependency
area and exposes the number of missing directional jobs. The legacy 1.0
region schema keeps its Hong Kong interpretation and raw default. The
[city design](../city/DESIGN.md) describes registration, identity and limits.
