# Package G1.0 amendment 2 — `SW-G1.2` (supplementary acceptance)

Amends: `SW-G1.0`, `docs/prompts/G1/ACCEPTANCE_CONTRACT.md` (SHA-256 `1273541776ccfc715fad6eb6ea961b1a3f592b9214e5702db7dcb005783d80ef`), as amended by `SW-G1.1`, `docs/prompts/G1/AMENDMENT_G1_1.md` (SHA-256 `8a96095a29c8c32cc639d8464446a146e982312ddde082233f61726bfee3cb93`). Those files stay unchanged as records. Where they differ from this amendment, this amendment applies.
Status: frozen on the date of the commit that adds this file, by user decision (2026-11-12; decision D-021).
Candidate: `af6fca9e3025b9c5e8447ca06d13065e8ba86c3d`, unchanged. No development is part of this amendment.
First acceptance report: `docs/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025.md` (SHA-256 `11d605dc18a2d54b071714e7c6abd8ad329f75089beb60f77f6beb5873f38875`): NOT ACCEPTED, 12 PASS, 1 FAIL (G1-08), 3 NOT VERIFIED (G1-02, G1-03, G1-16). It stays unchanged as a record. It reports no defect in the candidate's results.

This amendment does three things. It corrects the reading of G1-08, which was written after the first result; the reason is stated in B1. It opens a new, separate budget for the two pieces of work that the first acceptance could not finish. It records a user decision on one disclosed gap in the development ledger.

## B1. G1-08: which files must have equal hashes

- **Fact.** The frozen view builder (`tools/sea2/build.py`, `catalogue.py`, which may not change) writes the size and modification time of every catalogue file into the view pointer `current-<profile_id>.json`. A fresh registration in another worktree creates new files with new modification times. The pointer's SHA-256 therefore cannot be equal across worktrees. The contract already stated this property of the pointer in its starting facts, and still asked for "the same file hashes" without excluding it. That is an error of the contract.
- **What the first acceptance found.** Both IDs are equal, and 741 of 742 registration files have equal hashes. The one different file is the Rotterdam view pointer. The planning conversation compared the two pointers on 2026-11-12: `schema`, `profile_id`, `profile_sha256` and `view_id` are equal; the 160 names and sizes in `header_inventory` are equal; only the 160 `mtime_ns` values differ.
- **Amended text.** In design item 3 ("Identity"), in G1-08 and in the acceptance prompt, "the same file hashes" reads:
  - every file of the ingestion (`tiles/`, `manifest.json`, `registration_report.json`, and the catalogue pointer `current.json`) and every file of the view folder has the same SHA-256;
  - the view pointer `current-<profile_id>.json` is equal in every field except `header_inventory[*].mtime_ns`.
- This is a change of reading after a FAIL. It is recorded as such. The rest of G1-08 is unchanged: equal `ingest_id`, equal `view_id`, and a repeat registration that leaves existing files untouched.

## B2. Supplementary computation and budget

The first acceptance used 74.97 of its 75 minutes for shade jobs. Its own harness accounted for part of that: a wrapper that was re-entered during HK-1, and NL-1 run with one worker. The contract does not allow extending a budget, so this amendment opens a new ledger for a named, limited supplement.

| Run | Where | What |
| --- | --- | --- |
| S-1 | Main checkout | HK-4: the `measure_central` region, 2026-06-21 and 2026-12-22, `sea-2.2` (146 frames), new run name, compared with `outputs/shade_map/measure_central`. Before the run, the plan must show zero missing directions. |
| S-2 | The existing review worktree at the candidate | NL-1 again under a new run name, with the same rectangle and frames, started under complete metering: start, end, peak memory of the whole command, and new-artifact bytes. Its rasters are compared with the first NL-1 publication of the review. |

- **Budget of the supplement:** shade jobs and plans ≤ 45 minutes (wall clock, sleep included); job memory ≤ 12 GiB; new artifacts ≤ 10 GiB. No registration and no other real-DSM job is authorized. If the budget runs out, the affected items stay NOT VERIFIED.
- **Metering.** Guard the entry point of any wrapper against re-entry by worker processes. Start the metering before the job and confirm that it is recording before the job reads data.
- **Evaluation.**
  - G1-02 and G1-03 are judged on HK-1 to HK-3 of the first acceptance together with S-1.
  - For G1-16, the resource evidence for NL-1 is the engine's own peak memory recorded during the first NL-1 run together with the complete metering of S-2. S-2 reuses the horizon cache of the first run, so it measures planning, composition and publication; the horizon phase is covered by the engine's record.

## B3. One unmetered job in development (user decision)

The development report discloses that the first SHA-256 check of the two raw sheets ran without memory metering and was repeated inside the measured baseline audit. The user accepts the metered repetition as the record for that job (2026-11-12). G1-16 is not failed on this point.

## Procedure

- **Reviewer.** A separate review conversation. It writes an addendum; it does not edit the first report and does not fix anything.
- **Main checkout.** Amendment `SW-G1.1` A4 applies with the present HEAD: HEAD is a descendant of the candidate; `git diff --name-status <candidate> HEAD` shows only added files and modifications of `.gitignore`, `docs/prompts/README.md` and files under `docs/planning/`; no tracked file is modified in the working tree.
- **Write only:**
  - new entries under the existing review root `outputs/shade_map_g1_review_af6fca9e3025_20261111/` (new run folders, and a new folder `evidence_addendum_1/`); existing files there are not changed or deleted;
  - new entries for the two new run names in the fixed containers named in the contract;
  - the addendum report `docs/city/INDEPENDENT_ACCEPTANCE_G1_0_af6fca9e3025_ADDENDUM_1.md`.
- **Read-only:** everything else, including the Hong Kong view, every existing cache namespace, the first review's evidence and the developer's outputs. After S-1, confirm that no existing cache namespace gained or changed a file.
- **Addendum content:** the identities (candidate, contract and both amendments with hashes, main HEAD); the ledger of the supplement; the re-evaluation of G1-08 under B1 with the pointer comparison; G1-02, G1-03 and G1-16 with evidence; a statement that the other twelve items keep the verdicts of the first report, or the reason why one does not; the final count.
- **Gate.** G1.0 is ACCEPTED only if all sixteen items are PASS after the addendum. Engineering acceptance and numerical consistency are reported separately. Observational accuracy remains NOT VERIFIED for both cities.

## What does not change

The candidate, the design, the profiles, the fill height, the files that must stay byte-identical, the write scope of the candidate, and every criterion apart from the readings in B1 to B3.
