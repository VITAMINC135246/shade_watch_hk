# WSL2 smoke test — running the accepted engine on a Windows research machine

Status: prepared 2026-10-29; not yet executed.
Decision record: D-004 in the Claude project.

This is a platform smoke test, not V3 acceptance. It answers one question: does the
accepted engine (V2, `356f611`; repository commit `38303b1`) run under WSL2 on the
professor's Windows machine, and does it reproduce the Mac's scientific results within
the accepted tolerance?

It does not authorize V3 pilots or territory runs. It does not change `execution_authorized`.

## Why WSL2

Native Windows Python cannot run the engine:

- `src/v1_cache.py` imports `fcntl`;
- `src/v2_state.py` accepts only macOS and Linux filesystems;
- `tools/v3_campaign.py` requires Linux, symlinks and POSIX process groups.

Under WSL2, the code sees a real Linux kernel and an ext4 filesystem, so no code changes
are needed.

## What the test compares

The reference case is the accepted Cheung Chau 2×2 run
(`outputs/v2_daylight_cheungchau_20261009`) at 08:30, 12:30 and 15:10 HKT on 2026-01-07.
That is three sun directions (125°, 180°, 225°) over four target tiles, supported by 21
DSM tiles.

| Check | PASS when |
| --- | --- |
| P1 environment | Linux, under WSL2 (plain Linux is allowed but recorded); Python 3.12; every package equals `requirements.lock.txt`; HEAD equals `38303b1`; the ten engine files equal `356f611`; V2 accepts the filesystem. |
| P2 tests | The existing `pytest` suite passes. |
| P3 inputs | Every pack file matches its SHA-256; the four spatial keys equal the Mac keys. |
| P4 run | The V2 plan, submit and run reach `SUCCEEDED`; `resume` adds no new attempts. |
| P5 horizons | For all 12 cache entries: identical NaN mask, \|Δ horizon\| ≤ 1e-4°, identical support flags, identical distant-obstruction thresholds. |
| P6 labels | Shade and Quality equal the Mac frames, or every differing pixel lies within the 1e-4° equality neighbourhood. |

Apple arm64 and x86_64 may differ in the last bits of floating-point results, so
bit-identical rasters are not required. The tolerance is the rule the V2 regression
(B08) already accepted.

## Step 0 — build the pack on the Mac (Codex or the user)

From the repository root:

```sh
python3 tools/wsl2_smoke/make_pack.py --dry-run
python3 tools/wsl2_smoke/make_pack.py --out outputs/wsl2_smoke_pack_YYYYMMDD
```

The dry run verifies the 51 source files (about 218 MB) without copying anything. The
second command writes a new folder containing:

- `dsm/`: the 21 DSM tiles;
- `reference/`: Mac cache entries and frames;
- `repo.bundle`: the Git history, so no GitHub access is needed;
- `reference_manifest.json`;
- `setup_wsl.sh` and `run_smoke.py`.

Source files are only read. Copy the folder to a USB drive, or send it any other way.

## Step 1 — prepare Windows (once; needs an administrator)

1. In an administrator PowerShell, run `wsl --install -d Ubuntu-24.04`, then reboot if
   asked. Ubuntu 24.04 ships Python 3.12, which the project pins.
2. Optionally, create `%UserProfile%\.wslconfig` to give WSL enough resources. WSL's
   defaults are half of Windows RAM and all logical processors. For example:

   ```ini
   [wsl2]
   memory=16GB
   processors=8
   swap=8GB
   ```

   Then run `wsl --shutdown` so the change takes effect.
3. For long runs later, but not needed for this test: turn off sleep, and schedule
   Windows Update restarts outside run windows.

## Step 2 — copy the pack into the Linux home

Inside the Ubuntu terminal (USB drives appear under `/mnt/<letter>`):

```sh
cp -r /mnt/d/wsl2_smoke_pack_YYYYMMDD ~/
```

Keep the pack, the repository and all outputs in the Linux home (ext4), never under
`/mnt/c` or `/mnt/d`. V2 refuses Windows-mounted filesystems for state and caches.

## Step 3 — set up the repository and environment

```sh
bash ~/wsl2_smoke_pack_YYYYMMDD/setup_wsl.sh
```

The script:

- installs Python 3.12 and git if missing (needs `sudo` and network);
- clones the bundle to `~/shade_watch_hk` and checks out `38303b1`;
- creates `.venv`;
- installs the pinned packages.

## Step 4 — run the smoke test

```sh
cd ~/shade_watch_hk
.venv/bin/python tools/wsl2_smoke/run_smoke.py --pack ~/wsl2_smoke_pack_YYYYMMDD
```

It writes only to `outputs/wsl2_smoke_<stamp>/` and
`data/processed/shade_v1/wsl2_smoke_<stamp>/`.

Expected cost on a recent PC: a few minutes for the tests, plus a few minutes for 12
horizon entries and 3 frames. This is an estimate; the actual time is recorded.

## Step 5 — return the results

Send back `outputs/wsl2_smoke_<stamp>/SMOKE_REPORT.md` and `SMOKE_REPORT.json`. The report
also records information needed to plan longer runs:

- CPU, RAM and free disk;
- timings;
- the median ratio of this machine's horizon calculation time to the Mac's.

## Interpreting the result

- **All of P1–P6 PASS.** The platform is suitable for the bounded V3 pilots, once those
  pilots are separately authorized. A PASS does not make Mac-based estimates valid for
  this machine; that requires calibration.
- **P5 or P6 FAIL.** Do not run science on this machine. Report the JSON details. The
  cause could be a package mismatch, a different PROJ or GDAL build, or numerical
  differences beyond tolerance.
- **P1 issues.**
  - "package versions differ": usually a wheel was not available; record which one.
  - "filesystem rejected": the repo or outputs are on `/mnt/...`.
- **Network or permission failures in Step 3** are setup problems, not engine failures.

Observational accuracy, territory coverage and performance at scale are not tested here.

## Planning information to collect at the same time

- Machine model, CPU, RAM and free disk on the Linux side (`df -h ~`).
- Whether the machine may run unattended for several days, and its power and update policy.
- Who can restart it, and how results will be copied back (USB, network share, cloud).
