# V2 measured estimator

Model: `shade-watch-v2-estimator-1.0`, [estimator.json](estimator.json).
Frozen SHA-256: `ad6939e4455d9e80495d27e382438d635f5cb9f0920601959e09bbbe2e721469`.
Coefficients were frozen before held-out runs. A preliminary component model was
retained in evidence; phase/concurrency separation was finalized using calibration
alone. No coefficient was changed after any held-out outcome.

## Meaning and domain

Predict wall time from invocation of a submitted batch's `run_batch` to its return,
including input validation, spawned processes, calculation, compression/readback,
journal/controller checks and returned status verification. Planning/submission
time is separately recorded. Cold denotes missing directional cache entries;
OS filesystem/JIT code caches were not flushed.

Initial catalogue, process startup, missing directional work, classification,
output/compression/validation, provisional media and final-result hits have
separate terms. Native workload units are 1.8 million pixels. Direction unions
count missing scientific entries, not duplicate requests. A valid final-frame
hit can bypass a missing directional entry. Memory uses inherited conservative
native allocation bounds plus controller/request metadata; disk distinguishes
uncompressed retained data and temporary files/database allowance. Those are
engineering ceilings, not statistical intervals.

Calibration used mostly-valid native 11NE10B and 11NE10D, 1500×1200, nearest5,
one/two workers, scientific-only output, <=2 tiles, <=320 native-frame units and
<=12 union entries. Other tiles/terrain/NoData distributions, custom crops,
media/statistics/logical views, alternate direction policies or four workers are
explicitly outside the calibrated domain. They can run within admission limits,
but predictions are labeled extrapolated. The JSON reports hardware and storage
assumptions; local gates cannot establish territory accuracy.

## Calibration

Mac arm64/macOS 15.7.4, 10 logical CPUs, 24 GiB RAM, local HFS external volume,
project Python 3.12.5 and locked existing packages. One-worker cold 2-direction
native batch: 23.912 s; two-worker 4-direction/two-tile batch: 23.252 s.
Warm directional queries into new outputs: 32 frames/one worker 9.789 s,
64 frames/two workers 15.137 s. These include complete API-return verification.

Measured native-direction union-task cost: 10.842383 s/entry. Warm complete frame
cost: 0.274613 s/native-frame unit, with 0.018902 s classification and the
remainder assigned to output/controller validation. Initial catalogue/startup
allowances are 0.25/0.75 s. Measured directional two-worker efficiency is capped
at 1.0; output-stage efficiency is 0.621660. They are separate because output
I/O/journaling does not share directional CPU scaling. Media/final-hit/four-worker
terms are provisional and are not validated by B10.

Development hold-outs were predeclared in `outputs/v2_development/evidence/samples.json`,
with predictions saved before each run. Warm setup populated only directions
using separate cropped outputs; every warm measured native frame was newly
classified/exported, with zero final-result hits.

| Directional cache | Prediction | Observation | Absolute percentage error |
| --- | ---: | ---: | ---: |
| Cold | 23.568 s | 20.848 s | 13.05% |
| Warm | 57.543 s | 63.868 s | 9.90% |
| Mixed | 23.568 s | 19.627 s | 20.08% |

Median APE **13.05%**, maximum **20.08%**: within frozen 30%/60% gates.
All three exceed 10 seconds. Peak sampled job memory and generated disk fit the
pre-run plan ceilings. All outcomes/residuals are retained; none were dropped.
See `holdouts.json`, per-case prediction/result files and `ledger.json`.

Final strict-JSON/journal/monitoring changes were revalidated with the same cases
and unchanged coefficients; the original outcomes remain above. Candidate-code
observations were 21.091/67.037/19.750 s, errors 11.74/14.16/19.33% (cold/warm/mixed),
median **14.16%**, maximum **19.33%**. All duration/resource gates pass. The code
hashes and pre-run revalidation manifest are in `candidate_revalidation_manifest.json`;
all predictions are saved in `candidate_*_prediction.json`. These repetitions
are development regressions, not the independent review's untouched cases.

## Extrapolation

`src.v2.project_territory` requires explicit tile count, effective-pixel fraction,
direction union, queries per tile, cache fraction, worker count, output selection
and named hardware. It produces a qualified range and uncompressed storage terms.
It does not schedule a territory job. A 1000-tile illustrative profile is saved
in `outputs/v2_development/evidence/projection.json`; that tile count is an
assumption, not a Hong Kong inventory. Download/ingest, territory source validation,
storage topology, cold JIT, remote queues, different hardware, failures and media
are excluded and named. The broad 0.5–2× projection range is an engineering
variation allowance, not a calibrated confidence interval or territory guarantee.
