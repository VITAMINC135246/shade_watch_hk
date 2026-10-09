# Development and independent acceptance prompts

These are English execution prompts and predeclared acceptance contracts, not evidence that any version has been implemented.

| Version | Development prompt | Independent acceptance prompt | Shared contract |
| --- | --- | --- | --- |
| V1 — arbitrary-date/time pixel queries | [Develop](v1/DEVELOPMENT_PROMPT.md) | [Review](v1/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [A01–A14](v1/ACCEPTANCE_CONTRACT.md) |
| V2 — reliable batches and measured scaling | [Develop](v2/DEVELOPMENT_PROMPT.md) | [Review](v2/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [B01–B14](v2/ACCEPTANCE_CONTRACT.md) |
| V3 — territory readiness and deployment | [Develop](v3/DEVELOPMENT_PROMPT.md) | [Review](v3/INDEPENDENT_ACCEPTANCE_PROMPT.md) | [C01–C16](v3/ACCEPTANCE_CONTRACT.md) |

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
