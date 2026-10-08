# V2 batch guide

Run from the project with the existing `.venv`. V1 `plan_shade/run_shade` and
legacy commands remain available. Scientific policy is still
[SW-V1-POLICY-1.0](../v1/POLICY.md); V2 adds local durable orchestration.

## Python

```python
from src.v2 import (plan_batch, submit_batch, run_batch, status_batch,
                    cancel_batch, resume_batch)

plan = plan_batch([
    dict(id="jan", tile="11NE10B(e844n822,e845n822).tif",
         instants=["2026-01-07T14:31:27+08:00"],
         output_dir="outputs/my_v2/jan"),
    dict(id="feb", tile="11NE10B(e844n822,e845n822).tif",
         instants=["2026-02-07T14:31:29+08:00"],
         output_dir="outputs/my_v2/feb", jpg=True),
], workers=2, statistics=True, logical_mosaic=True)
print(plan.id, plan.estimate)
batch_id = submit_batch(plan, state_dir="outputs/my_v2_state")
result = run_batch(batch_id, state_dir="outputs/my_v2_state")
print(status_batch(batch_id, state_dir="outputs/my_v2_state"))
```

The read-only plan creates no state/raster/media files. Requests also accept V1
instant lists, multiple daylight dates, coordinate selectors, custom bounds,
crops and direction methods. Existing `ShadePlan` objects can be supplied.
Named requests need distinct output directories. Identical submissions return
the same stable batch ID. Concurrency/output-selection settings form part of
batch identity; scientific tile/direction keys do not depend on them.

## CLI

The checked-in example is executable, selecting two native tiles and dates:

```sh
.venv/bin/python -m src.v2 plan --requests docs/v2/example_batch.json
.venv/bin/python -m src.v2 submit --requests docs/v2/example_batch.json --state outputs/v2_example_state
```

Copy the printed full `id` into `shade_batch_id`, then:

```sh
shade_batch_id='<printed full id>'
.venv/bin/python -m src.v2 run --batch "$shade_batch_id" --state outputs/v2_example_state
.venv/bin/python -m src.v2 status --batch "$shade_batch_id" --state outputs/v2_example_state
.venv/bin/python -m src.v2 cancel --batch "$shade_batch_id" --state outputs/v2_example_state
.venv/bin/python -m src.v2 resume --batch "$shade_batch_id" --state outputs/v2_example_state --reverse-order
```

Cancellation can be requested from another process while a controller runs.
QUEUED becomes CANCELLED; RUNNING becomes CANCELLING until current work reaches
a safe boundary. A terminal completed/failed batch is not retroactively cancelled.
Run/resume exit 1 for FAILED/INCOMPLETE, and malformed/rejected commands exit 2.

## State, recovery and ownership

SQLite `state.sqlite` uses local rollback-journal transactions, synchronous
FULL and immutable definition triggers. `store.json` identifies managed state.
Inspect attempts and direction events with SQLite read-only access if needed;
do not edit the journal. Kernel controller/output/native-tile locks prevent
competing publication. There is at most one in-flight task per spawned worker,
with no nested scientific pool. The same state database may contain multiple
batches. Network filesystems are rejected. Cloud synchronization or access from
another machine is outside the local coordination guarantee.

After an owned controller/worker dies, a fresh `resume_batch` or CLI `resume`
validates input content, reclaims stale attempts, and checks committed artifact
hashes. Only recorded children with matching PID/create-time/ownership tokens
are terminated. Completed scientific entries are reused; partial or corrupt
entries required by missing output frames are rebuilt. Existing valid final
frames need not rebuild an evicted horizon. Status reports INCOMPLETE if a
previously completed artifact is damaged. Resume invalidates dependent outputs
and retains original failed attempts/events.

Transient worker loss/I/O/ownership contention receives a fixed attempt ceiling
(default 3, configurable 1–5). A writer waits at most 15 seconds per attempt.
Permission/quota/validation/input errors are permanent within the current run.
After repairing an external failure, explicit resume can use remaining attempts;
it does not erase or reset the ceiling. An exhausted attempt ceiling or changed
code/scientific input needs a new batch plan. New output names are required if
the scientific request identity changes. Never reset historical directories.

## Scientific, media, statistics and logical views

Each request has lossless native-resolution shade/quality TIFFs, per-frame
manifests, `run_definition.json` and `result_index.json`. Exact instants, canonical
solar references, quality reasons and equality-neighbourhood counts are retained.
Frame tasks use the unchanged V1 classifier/composer. JPG/MP4, derived counts
and result indexes are separate dependent tasks. A media-only failure/resume
does not requeue valid horizons or scientific frames. Counts are derived outputs,
not replacements for pixel data.

With `logical_mosaic=True`, `<batch-id>.logical_mosaic.json` in the state directory
references source rasters at every requested UTC instant. It creates no compulsory
physical mosaic. Sample an aligned, bounded EPSG:2326 window:

```python
from src.v2_worker import read_logical_window
shade, quality, transform = read_logical_window(
    "outputs/my_v2_state/<batch-id>.logical_mosaic.json",
    utc_time="2026-01-07T06:31:27+00:00",
    bounds=(844701.5, 822197.5, 844713.5, 822202.5),
)
```

Only layers at that exact instant are included; missing coverage stays 255/1.
Overlapping layers must agree. Source transforms are checked. Large windows are
rejected above the V1 20-million-pixel area profile. A full grid is allocated only
for the explicitly requested bounded sampling window.

## Cache compatibility and resource admission

Default V2 cache: `data/processed/shade_v1/v2_default`. It uses exact accepted V1
scientific keys and three-band entries; no numerical cache-format migration is
necessary. Existing V1 namespaces may be read/reused explicitly by `cache_dir`.
Old legacy caches are not assumed compatible. No cache/output is automatically
pruned. Controlled corruption tests use isolated namespaces. NaN GeoTIFF NoData
is represented as the explicit string `NaN` in strict JSON metadata.

Workers default to 1 and are limited to 4; one/two-worker measurements are recorded.
Total budget defaults to 12 GiB memory/20 GiB new artifacts. Preflight includes
native allocation bounds, controller/request metadata, retained outputs, temporary
direction files, database allowance, available disk and host-memory headroom.
Plan metadata is capped at 128 MiB; request/frame/area limits remain local profiles.
Queue length increases metadata/storage, not retained scientific arrays per task.
The controller samples known parent/worker/media RSS, cancels owned jobs on
resource excess and reports monitoring gaps. This is sampled enforcement, not
an OS cgroup or a guarantee against sub-sample peaks/power failure.

Read [ESTIMATOR.md](ESTIMATOR.md) for calibrated scope and prediction errors and
[DEVELOPMENT_REPORT.md](DEVELOPMENT_REPORT.md) for verification/evidence. Local
engineering acceptance does not establish observed physical shade accuracy.

## October 2026 closeout compatibility

Batch identity includes all four V2 engine files validated during execution.
After an engine update, make a new plan; unchanged scientific frames/directions
can still be reused. Old immutable batches continue to reject changed code.

Result schema `shade-watch-v2-result-1.1` stores shared scientific provenance.
Execution-specific `batch_id`, `request_id`, `state_directory` and the current
cache location are in `<state>/receipts/<batch>/<request-hash>.json`, retained as
verified task artifacts. Compatible publishers in different state stores may
share the output without changing its index bytes. The shared index's cache
location comes from the first publisher's immutable `run_definition.json`.

The full download is now under `data/raw/dsm/2020/D12.DSM.TIFF`; the original
19-file calibration set is under `data/raw/dsm/2020_HKUST_Around/D12.DSM.TIFF`.
Pass `dsm_dir` explicitly for historical comparisons. Adding nearby support
files can legitimately change spatial cache identities and quality flags.
Existing cached results are not evidence for the expanded support dataset.

Legacy `shade-watch-v1-result-1.0` and `shade-watch-v2-result-1.0` indexes are
read-only to the new V2 publisher. A batch pointing at such an output is rejected
before modifying any output file. Choose a fresh output directory and explicitly
reuse the compatible scientific cache. There is no automatic result-schema
migration; historical store checksums and result indexes remain valid. The
schema-1.1 sharing guarantee applies between current-version publishers.
