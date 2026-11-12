# V3 prepared execution package — NOT RUN

Prepared 2026-10-08 (Hong Kong). This is an offline handoff, **not V3 acceptance**.
The user explicitly prohibited V3 execution on the current Mac. The launcher was
checked as Python syntax and the profile as JSON; it was not imported, invoked,
benchmarked or tested on a research machine. No V3 states/caches/rasters exist
from this handoff. V2 supplementary calculations are separately identified.

## What is ready

`tools/v3_campaign.py` is a concrete V2-backed regional pilot launcher, with
preflight, metadata/source-view preparation, frozen plans, run/resume/status/cancel,
serial bounded regional scheduling, cumulative time/storage accounting and
native/combined/logical seam comparison. It keeps native scientific tasks and
reuses the accepted V1/V2 science. Per-region combined rasters are deliberately
bounded to four tiles; it never creates a whole-Hong-Kong raster. See
[SCENE_PLAN.md](SCENE_PLAN.md) and `config/v3/pilots.template.json`.

The template selects seven regions × four tiles × five instants. Native outputs
and the bounded combined check share directional work. Media is disabled; the
quality rasters remain authoritative. Scene names are geographic hypotheses,
not a completed terrain classification. All Mac estimator predictions on the
research machine are extrapolations, regardless of numerical values emitted by
V2. Keep every residual; these pilots do not pass an estimator calibration gate.

## Complete these inputs on the research machine

- Preserve the accepted Git history and original DSM/sidecars. Use a local Linux
  volume supported by V2 (`ext4`, `xfs`, `btrfs`, etc.), not NFS/SMB state/cache.
- Record the actual hostname, OS, Python 3.12 runtime, CPU/RAM/storage/allocation
  and transfer authorization. No host or transfer has been designated yet.
- Confirm the DSM vertical datum from its authoritative metadata. Header checks
  alone do not establish it. The 2020 source root contains 3,310 GeoTIFFs; the
  preserved HKUST root contains 19. They must not be mixed in historical tests.
- Supply an authoritative territory boundary/version before claiming territory
  coverage. The seven explicit regional blocks can be piloted without inventing
  a territory boundary; C13/full-territory work cannot be accepted without one.
- Copy the template to a `config/*local*` filename (ignored by Git), fill the
  machine/data fields and choose a fresh campaign ID. The accepted V2 commit
  and report hash are pinned in the committed template after reacceptance.
- Only when the specific target-machine pilot campaign is authorized, set
  `execution_authorized: true` and confirm its budget. The template's one worker,
  12 GiB memory, 20 GiB new artifacts and 3,600 seconds are a proposed ceiling,
  **not permission to execute on a remote host**.

## Commands for the future target host

Run from the repository root. These commands were prepared, not executed here.
Dependency installation needs the target host's network/package access; a clean
installation and native library compatibility remain C06/C14 validation work.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pytest -q --disable-warnings
cp config/v3/pilots.template.json config/v3_pilots.local.json
# Fill the designated host, confirmed datum, campaign ID and approved budget.
.venv/bin/python tools/v3_campaign.py preflight --profile config/v3_pilots.local.json --execute
.venv/bin/python tools/v3_campaign.py prepare --profile config/v3_pilots.local.json
# Review outputs/v3_<campaign_id>/prepared.json and plans before execution.
.venv/bin/python tools/v3_campaign.py run --profile config/v3_pilots.local.json --execute
.venv/bin/python tools/v3_campaign.py status --profile config/v3_pilots.local.json
.venv/bin/python tools/v3_campaign.py cancel --profile config/v3_pilots.local.json
.venv/bin/python tools/v3_campaign.py resume --profile config/v3_pilots.local.json --execute
```

`prepare` reads native headers, gathers every supplied DSM intersecting each
1 km halo, creates symlink views without copying raw data, validates/hashes those
bounded inputs through V2 and records estimates before any scientific job. It
refuses existing prepared manifests. It does not implement a persistent spatial
index of the complete territory. Individual V2 index/receipt files retain source
content identities; `prepared.json` also freezes the directory metadata snapshot,
profile and engine bytes. Changes require a new campaign, not silent resume.

`run` requires both an authorized completed profile and `--execute`, rejects
macOS and other hostnames, validates the accepted V2 source bytes, report hash,
free memory/disk, and profile/input/code identities. Each controller runs in its
own owned process group. Time/disk exhaustion requests cancellation and terminates
only that group. Partial outputs remain available to V2's recovery checks.
Artifacts are counted cumulatively without counting symlinked raw files.
Every completed region is compared with its native outputs and a seam window.

A hard kill of the outer launcher can leave its ledger marked RUNNING; the
launcher fails closed rather than assuming unused time. Inspect the owned job's
V2 status/attempts and elapsed allocation, reconcile its ledger conservatively,
and document this administrative recovery before resuming. No automatic reset
of attempts, budgets, state or historical data is supported. Changed source/code
or exhausted V2 attempts require a new campaign ID. Preserve old evidence.

## Known source geometry issue

Four of the 3,310 GeoTIFF headers have origin offsets of about 9.4e-8 m,
producing seven strict sliver overlaps. The existing V2 inventory rejects those
overlaps. Original data are unchanged. The seven selected pilot support sets
exclude them, but full-catalog ingestion must define, version and verify an
explicit normalization/rejection policy before territory use. Header dimensions
and file count alone do not mean territory readiness.

## What remains V3 work

This launch package does **not** claim C01–C12 ENGINEERING READY. Full V3 still
needs persistent indexed ingestion/updates, authoritative boundary clipping with
islands/holes, 1k/5k/10k catalog scaling tests, clean-environment verification,
regional export/preview validation, held-out approximation checks, operational
failure tests and independent acceptance. A regional wrapper is not a substitute
for those requirements. No C13–C16 deployment/production claim is made.

The program intentionally exposes no full-territory or annual campaign command.
After target-machine cold/warm benchmarks and these contrasting regional pilots,
use the original V3 development/acceptance prompts to complete the remaining
engineering and deployment gates and propose a separately bounded territory
profile. Keep engineering readiness, deployment validation, production completion
and observational accuracy as separate conclusions.
