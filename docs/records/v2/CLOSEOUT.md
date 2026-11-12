# V2 closeout and V3 preparation

**V2 ACCEPTED — B01–B14 PASS; 73 tests pass.** Closed 2026-10-09, Asia/Hong_Kong.

User scope: finish V2, push `feature`, and prepare future V3 execution without
running V3 on the Mac. This report supplements the immutable independent review;
it does not replace independent acceptance.

## V2 repair and acceptance lineage

- Accepted V1: `796ac8abf05b92f1fbbac23a4aa0f18c9d944101`, report
  `docs/v1/INDEPENDENT_ACCEPTANCE_796ac8a.md`.
- Original V2: `e2fa0cde8e104439eb0c05e9bf9f549edffd6797`. Development passed its
  own B01–B14 checks; independent acceptance was interrupted after finding two
  P1 defects. It must not be represented as independently accepted.
- Repair candidate: `f3dac3175706988591387b22a56ee9857afad276`. All four validated
  V2 engine files now participate in batch identity. Shared scientific indexes
  are independent of request/batch/state context; separate verified execution
  receipts preserve each controller's provenance.
- Final repair candidate: `356f611d7b775ce31006904b80ca31d3c1c484b2`. A subsequent
  independent cross-version check found that schema-1.0 indexes could be rewritten
  in place. The new publisher now rejects legacy V1/V2 result directories before
  changing outputs; fresh namespaces can reuse compatible direction caches.
- Final independent decision: **ACCEPTED**, [independent report](INDEPENDENT_ACCEPTANCE_356f611.md).
  All B01–B14 pass; three original P1 defects are closed. Report SHA-256:
  `441e6befd492f0c1c0ac02c3c10ad14fa72329bc2c26294224478b10b4406487`.
  Final tests: **73 passed**. Frozen estimator hold-outs measured on f3dac31 have
  median/max APE **15.63% / 19.38%**, inherited with explicit attribution after
  the targeted final repair checks. Earlier FAIL reports remain preserved.
  Scientific V1 policy, horizon/classifier/solar code and frozen estimator
  coefficients have not changed.

The original two failure records remain in
`outputs/v2_independent_acceptance_e2fa0cd/evidence/identity_change_defect.json`
and `competing_writer_defect.json`. Reacceptance uses a fresh namespace and the
original 19-file calibration inputs with their content hashes checked. Full
territory input is not substituted for the frozen estimator domain.

## Newly supplied DSM

Header inventory: **3,310 GeoTIFFs; 26,043,475,302 bytes; EPSG:2326; 0.5 m;
1500 × 1200 cells each**. All original 19 TIFFs have matching content hashes in
the new full download and the preserved HKUST directory. Raw TIFFs/metadata were
only read and are excluded from Git.

Four source headers contain approximately 9.4e-8 m origin offsets, producing
seven strict sliver-overlap pairs. These are a documented V3 ingestion issue;
strict V1/V2 inventory rejects overlapping footprints. No original geotransform
was edited or silently normalized. File counts do not establish gap-free
administrative coverage, full raster validity or confirmed vertical datum.

## Supplementary V2 test on the new data

The new-data case was declared before execution in
`outputs/v2_closeout_20261008/evidence/new_data_manifest.json`:

- Targets: `11NE10B` and adjacent `11NE10D`; **29 supplied support tiles** within
  the native 1 km halos, selected from the new 3,310-file dataset.
- Instants: 2026-12-17 09:43:29 and 2027-03-23 15:21:41, Asia/Hong_Kong.
- One worker, four new directional entries, no final-result hits. Independent
  native outputs, combined output and a logical seam window agree exactly in
  shade/quality pixels and georeferencing. A separate V1 API run also agrees.
- Batch API wall time **43.969 s**, including V1 warm reference **47.440 s**.
  Sampled V2 controller/worker peak **807,960,576 bytes**; generated artifacts
  including reference approximately **37.03 MiB**. No media was generated.
- Both instants have 3,600,000 quality-0 pixels in this selected two-tile output.
  That observation applies only to these targets/instants and the adopted 1 km
  model; it is not a territory-wide quality or physical-accuracy claim.

[Compact evidence and file hashes](CLOSEOUT_EVIDENCE.json) are committed; raw
state, rasters, predictions and detailed logs remain local. This is developer
supplementary numerical consistency evidence, separate from independent samples.
`tools/v2_closeout.py --campaign <fresh-name>` prepares the same bounded case
in a fresh namespace. Reusing an existing result record is rejected.

## V3 scope handoff

Representative contrasting regional trials belong to **V3 C15**, not a missing
V2 territory gate. The prepared [seven-scene plan](../v3/SCENE_PLAN.md) expands
that requirement into seven 2×2-native-tile regions: Central/Mid-Levels, Mong Kok,
Tai Mo Shan, Yuen Long, south Lantau, Cheung Chau and HKUST/Clear Water Bay.

The [future-machine runbook](../v3/RUNBOOK.md), profile and pilot launcher are
prepared. Only static syntax/JSON checks were performed. **V3 was not run.**
The package is a bounded V2-backed pilot launcher; complete V3 ingestion,
boundary/scale engineering, machine validation and independent acceptance remain
open as enumerated in [V3 status](../v3/STATUS.md). It must not be presented as
ENGINEERING READY, DEPLOYMENT VALIDATED or a completed territory campaign.

Research host/access/allocation, confirmed vertical datum, authoritative boundary
and a separately authorized campaign profile are still needed. No transfer,
remote execution or full-year/territory job occurred. Observational shade
accuracy remains **NOT VERIFIED**. Unrelated `presentations/` stay untracked.
