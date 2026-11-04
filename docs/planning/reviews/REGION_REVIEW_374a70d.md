# Region adapter review: commit 374a70d (SW-RGN-AC-1.0)

- **Reviewer:** planning conversation (Claude), 2026-10-30 02:40 UTC.
- **Candidate:** `374a70df58a1e8faea09c8736b63c1739b30ed41` on `feature`, parent `38303b1`.
- **Method:** static review of the commit, plus Codex's committed evidence. Claude cannot run the project environment, so run-dependent items rely on Codex evidence. This is not an independent acceptance; the contract requires none, because R01 holds.

## Scope note

The commit time is 23:49 HKT, which is before the `SW-RGN-AC-1.1` follow-up reached Codex. The commit therefore implements 1.0 only. Amendment 1.1 (R09–R12) is not implemented yet, and no uncommitted region changes exist.

## Verdicts against 1.0

| ID | Verdict | Basis |
| --- | --- | --- |
| R01 | PASS (verified by Claude) | `git diff 38303b1 374a70d -- src` is empty. All ten pinned files are byte-identical to `356f611`. No planner files are in the commit, and the contract and amendment hashes are unchanged. |
| R02 | PASS (Codex evidence) | Rejection tests cover both CRSs. |
| R03 | PASS | The transformer is built exactly as V1 builds it, and five points are compared exactly. |
| R04 | PASS (Codex evidence) | Three rectangles produce plan keys and grids equal to hand-written custom requests. |
| R05 | PASS against the letter of the contract | Union, disjointness and the horizon-task inventory are tested. Superseded by the user decision: no-DSM cells must not cause rejection (1.1 A1, pending). |
| R06 | NOT VERIFIED (self-reported) | Shade, Quality and transform are equal at two instants across two tiles. Three weaknesses: the two instants are 1 s apart and share one direction; the V1 reference reused the V2 cache; the outer resource ledger is incomplete. R12 in 1.1 covers this. |
| R07 | PARTIAL | The sidecar and the guide content are fine. However, both guide examples point at the full raw catalogue, which the engine rejects (see below), so they cannot run. Fix in 1.1 (A3 source views plus a guide correction). |
| R08 | PASS | 93 tests pass (73 existing + 20 new). One local commit, no push. |

**Overall:** the 1.0 core (R01–R05, R08) is usable. R06 and R07 stay open and are carried into the 1.1 package. The D-2 prerequisite ("adapter 1.0 + 1.1 committed and reviewed") is **not yet met**.

## New finding: the full raw catalogue cannot be indexed

`v1.index_sources('data/raw/dsm/2020/D12.DSM.TIFF')` raises "Incompatible CRS, resolution, or grid alignment" at `14NE15A(e828n809,e829n809).tif`. Evidence: `docs/region/evidence/blocker.json`.

- **Cause.** This is one of the four known shifted-origin tiles (offset ≈ 9.4e-8 m). The V1 lattice check tolerates only 1e-7 pixel, and 9.4e-8 m is about 1.9e-7 pixel at 0.5 m resolution.
- **Effect.** Any whole-directory use of the raw catalogue fails before planning starts, regardless of region.
- **Consequences:**
  - Request-local source views (1.1 A3; D-2 §3) are **mandatory**, not just a speed-up.
  - Regions whose 1 km halo touches the four `14NE15*` tiles still need the versioned V3 ingestion policy already listed in `config/v3/pilots.template.json` (`known_header_issues`).
  - Raw data must stay unchanged; no silent correction is allowed.

## Next steps

1. **After B is committed:** give Codex the A 1.1 package. It covers R09–R12, plus a corrected guide that uses source views and documents the raw-catalogue rejection.
2. **D-2 starts after the A 1.1 review.** The smoke-test prerequisite is waived for development (user decision, 2026-10-30).
3. **Before any V3 or territory work:** plan a separate, versioned ingestion policy for the shifted-origin tiles.
