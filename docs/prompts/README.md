# Development and independent acceptance prompts

These are English execution prompts and predeclared acceptance contracts, not evidence that any version has been implemented.

| Version | Development prompt | Independent acceptance prompt | Shared contract |
| --- | --- | --- | --- |
| V1 — arbitrary-date/time pixel queries | [Develop](v1/DEVELOPMENT_PROMPT.md) | [Review](v1/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [A01–A14](v1/ACCEPTANCE_CONTRACT.md) |
| V2 — reliable batches and measured scaling | [Develop](v2/DEVELOPMENT_PROMPT.md) | [Review](v2/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [B01–B14](v2/ACCEPTANCE_CONTRACT.md) |
| V3 — territory readiness and deployment | [Develop](v3/DEVELOPMENT_PROMPT.md) | [Review](v3/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [C01–C16](v3/ACCEPTANCE_CONTRACT.md) |
| Region request — two-corner rectangle input (no science change) | [Develop](region/DEVELOPMENT_PROMPT.md) | Planning-conversation review | [R01–R08](region/ACCEPTANCE_CONTRACT.md) |
| Sea-surface support — `SW-SEA-POLICY-1.0` sea-filled DSM view | [Develop](sea/DEVELOPMENT_PROMPT.md) | [Review](sea/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [S01–S14](sea/ACCEPTANCE_CONTRACT.md) |
| F1.0 — `shade_map` function and CLI (no science change) | [Develop](F1/DEVELOPMENT_PROMPT.md) | [Review](F1/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [F1-01–F1-14](F1/ACCEPTANCE_CONTRACT.md) |
| B2.0 — DSM-only sea surface `SW-SEA-POLICY-2.0` (starts after F1.0 acceptance) | [Develop](B2/DEVELOPMENT_PROMPT.md) | [Review](B2/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [B2-01–B2-15](B2/ACCEPTANCE_CONTRACT.md) |
| B2.2 — fill every NoData pixel at 0 m `SW-SEA-POLICY-2.2` (supersedes B2.0; codes in [OUTPUT_CODES](../OUTPUT_CODES.md)) | [Develop](B2/DEVELOPMENT_PROMPT_B2_2.md) | [Review](B2/INDEPENDENT_ACCEPTANCE_PROMPT_B2_2.md) | [B2-16–B2-31](B2/CONTRACT_B2_2.md) |
| G1.0 — cities other than Hong Kong; first city Rotterdam (engine inputs instead of Hong Kong constants; Hong Kong pixels unchanged) | [Develop](G1/DEVELOPMENT_PROMPT.md) | [Review](G1/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [G1-01–G1-16](G1/ACCEPTANCE_CONTRACT.md), amended by [SW-G1.1](G1/AMENDMENT_G1_1.md) and [SW-G1.2](G1/AMENDMENT_G1_2.md) |

## Numbering rule (from 2026-10-31, decision D-011)

- **Work packages:**
  - A: two-corner region input;
  - B: sea surface;
  - C: the professor's computer (WSL2);
  - D: web viewer and request generator;
  - F: the `shade_map` function;
  - G: cities other than Hong Kong (geography).

  V1, V2 and V3 are engine versions, not packages.
- **Versions:** package letter plus version number, for example A1.1, B2.0, F1.0.
- **Contract IDs:** `SW-<version>`, for example `SW-F1.0`. An amendment gets the next minor version, for example `SW-F1.1`.
- **Acceptance items:** `<letter><major version>-<two digits>`, for example `F1-01`. Amendments continue the numbering.
- **Folders:** `docs/prompts/<letter><major version>/`, for example `docs/prompts/F1/`.
- **Policy IDs keep their names.** Scientific policy IDs written into data and manifests (`SW-V1-POLICY-1.0`, `SW-SEA-POLICY-*`) are not renamed.
- **Frozen files keep their original IDs**, because renaming would change their hashes. Mapping:

| Original name | What it is | Reference from now on |
| --- | --- | --- |
| V1 contract, items A01–A14 | Engine version V1 (accepted) | V1 |
| V2 contract, items B01–B14 | Engine version V2 (accepted) | V2 |
| V3 contract, items C01–C16 | Territory readiness (not executed) | V3 |
| `SW-RGN-AC-1.0` / `-1.1`, items R01–R12 | Package A, two-corner input (committed and reviewed at `f5f24ac`) | A1.0 / A1.1 |
| `SW-SEA-AC-1.0`, items S01–S14 | Package B, `SW-SEA-POLICY-1.0` (independent acceptance stopped) | B1.0 |
| `SW-RUN-AC-1.0` | Package D-2, background runner and API (cancelled) | D (cancelled) |

Use the development prompt in the project, then supply the developer's full implementation commit SHA with the corresponding independent acceptance prompt in a separate review conversation. Both roles must read the same shared contract. Freeze the contract hash before implementation; change proposed scope/tolerances/budgets only before work or through an explicitly approved versioned amendment.

Order: define/freeze criteria -> develop and test -> independent acceptance -> repair on a new commit -> reaccept -> start the next version when requested. V2 requires an accepted V1 commit, and V3 requires an accepted V2 commit. The historical commit `7c56760c854cb1e5138c8381a7b68d543b68cdef` is the planning baseline only; future implementation commit SHAs must not be invented.

Budget defaults are ceilings, not promises or instructions to consume the allocation:

| Version | Development real-DSM jobs | Independent real-DSM jobs | Total job memory | New artifacts |
| --- | --- | --- | --- | --- |
| V1 | 60 min | 45 min | 8 GiB | 10 GiB |
| V2 | 120 min | 60 min | 12 GiB | 20 GiB |
| V3 local engineering | 120 min | 90 min | 12 GiB | 20 GiB |

V3 external benchmarks, regional pilots and territory campaigns require explicit data/machine/campaign profiles and their own authorized budgets. They are not included in the local-engineering ceilings. Report engineering readiness, actual deployment validation and production completion separately. Missing territory data or research-machine access cannot be replaced by synthetic evidence.

PASS / FAIL / NOT VERIFIED must map to concrete evidence. Numerical consistency, approximation error, performance and observational accuracy are separate conclusions. None of these prompts authorizes automatic progression into the next version, unbounded computation, public deployment or a GitHub push.

## Current handoff (2026-10-09)

See [`docs/v2/CLOSEOUT.md`](../v2/CLOSEOUT.md) for the V2 repair/acceptance
lineage and new DSM data status. Preserve failed-candidate reports as evidence;
use the final independently accepted candidate recorded there as V3's baseline.
The [V3 regional execution package](../v3/RUNBOOK.md) is prepared but unexecuted.
The user has explicitly excluded V3 execution on the current Mac. Its templates
and static checks do not satisfy the V3 engineering/deployment acceptance gates.
