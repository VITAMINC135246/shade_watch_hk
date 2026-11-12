# Package H1.0 amendment 3 — runtime write scope of the repair and the re-acceptance

Amendment ID: `SW-H1.3`
Amends: `SW-H1.2` (`AMENDMENT_2.md`, SHA-256 `5d1728681b126d44cedc9b4cd9b3556ea154bfce7eb5ce44744491d9de9a5077`). No earlier file is edited. `SW-H1.0`, `SW-H1.1` and `SW-H1.2` apply as written, except for the items below.
Status: frozen by the commit that adds this file (D-030). Record this file's SHA-256 before the repair.

## Why

The developer stopped at the preflight of the repair on 2026-11-13 and reported a conflict in part B of `SW-H1.2`: it forbids every change under `data/` apart from new files under `archive/reviews/`, and it requires R-7, which writes a new fill-impact cache namespace under `data/cache/horizon/`. Part C allows that namespace for the reviewer; part B did not. The developer was right. No file was changed and no job ran.

Part B and part C also did not list the work folders that the tools create for new run names. This amendment states the runtime write scope of both in full.

## D1. Runtime writes allowed in the repair (part B)

In addition to the files in the table of part B, the repair may create, and only create:

- publications under `runs/h1_0_dev2_<YYYYMMDD>/`;
- the folders under `work/` that the tools create for run names with the prefix `h1_0_dev2_` (engine work folders, locks, request-local source views, fill-impact work);
- **one** new namespace `data/cache/horizon/fill_impact_<id12>/`, written by R-7. If the namespace that R-7 plans already exists, stop and report;
- evidence and temporary detached worktrees under `archive/reviews/h1_0_dev2_<YYYYMMDD>/`.

Every other path under `data/`, `runs/`, `work/`, `baselines/` and `archive/` stays as it is. This includes the four protected cache namespaces, the two earlier `fill_impact_*` namespaces, and the runs and work folders of the first round. The one deletion that part B allows (`runs/.shade_map_root.json`) is unchanged.

## D2. Runtime writes allowed in the re-acceptance (part C)

The reviewer may create, and only create:

- publications under `runs/h1_0_review_<candidate12>_<YYYYMMDD>/`;
- the folders under `work/` that the tools create for run names with the prefix `h1_0_rev2_`;
- one new namespace `data/cache/horizon/fill_impact_<id12>/`, written by R-7. If it already exists, stop and report;
- evidence and detached worktrees under `archive/reviews/h1_0_<candidate12>_<YYYYMMDD>/`;
- the report named in A11.

Everything else is read-only, including the namespace and the folders that the repair created.

## Unchanged

Everything else in `SW-H1.2`: the allowed file changes, the checks, R-1 to R-8, the budgets, the deliverables, and the re-acceptance items H1-01 to H1-14. In H1-12, "the new fill-impact namespace" means the one of D1 or D2.
