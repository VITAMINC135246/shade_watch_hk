"""Build the WSL2 smoke-test pack on the Mac (standard library only).

Run from the repository root:

    python3 tools/wsl2_smoke/make_pack.py --out outputs/wsl2_smoke_pack_YYYYMMDD
    python3 tools/wsl2_smoke/make_pack.py --dry-run      # verify only, copy nothing

The pack contains:
  dsm/          the 21 DSM tiles the accepted Cheung Chau run depended on
  reference/    Mac horizon-cache entries (3 directions x 4 tiles) and Mac Shade/Quality
                frames for 08:30, 12:30 and 15:10 HKT on 2026-01-07
  repo.bundle   a git bundle of the current branch (the WSL side checks out BASE_COMMIT)
  reference_manifest.json

Everything is derived from the accepted run's result index and verified by SHA-256;
nothing is typed by hand. Source files are only read. The output directory must not exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(os.environ.get("SHADE_WATCH_ROOT", Path(__file__).resolve().parents[2])).resolve()
RUN = ROOT / "outputs/v2_daylight_cheungchau_20261009"
INDEX = RUN / "combined/result_index.json"
CACHE = ROOT / "data/processed/shade_v1/v2_daylight_cheungchau_20261009"
DSM = ROOT / "data/raw/dsm/2020/D12.DSM.TIFF"
BASE_COMMIT = "38303b164d107b81c02f50f14da61951f09e9b49"
ACCEPTED_ENGINE = "356f611d7b775ce31006904b80ca31d3c1c484b2"
LOCAL_TIMES = ("08:30", "12:30", "15:10")
DIRECTIONS = (125.0, 180.0, 225.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tile_names_by_origin() -> dict:
    """Map (left, top) -> .tif name using the .tfw world files (pixel-centre origins)."""
    names = {}
    for tfw in DSM.glob("*.tfw"):
        values = tfw.read_text().split()
        left, top = round(float(values[4]) - 0.25, 3), round(float(values[5]) + 0.25, 3)
        names[(left, top)] = tfw.with_suffix(".tif").name
    return names


def build_manifest() -> dict:
    index = json.loads(INDEX.read_text())
    by_origin = tile_names_by_origin()
    dsm_files = {}
    for dependency in index["tile_dependencies"]:
        for source in dependency["sources"]:
            left, _, _, top = source["bounds"]
            name = by_origin[(round(left, 3), round(top, 3))]
            dsm_files[name] = dict(sha256=source["sha256"], bytes=(DSM / name).stat().st_size)
    targets = [Path(p).name for p in index["grid"]["selected_sources"]]
    frames = [f for f in index["frames"] if f["local_time"][11:16] in LOCAL_TIMES]
    if len(frames) != len(LOCAL_TIMES):
        raise SystemExit("Reference frames not found in the accepted result index")
    tiles = []
    for name in targets:
        solar = next(t for t in frames[0]["solar_by_tile"] if t["source_name"] == name)
        key, entries = solar["spatial_key"], {}
        for status in sorted((CACHE / key).glob("direction_*.json")):
            meta = json.loads(status.read_text())
            if meta["direction_deg"] in DIRECTIONS:
                entries[str(meta["direction_deg"])] = dict(
                    entry=status.stem, tif_sha256=meta["sha256"],
                    threshold_deg=meta["threshold_deg"],
                    mac_calculation_seconds=meta.get("calculation_seconds"),
                    mac_preprocessing_seconds=meta.get("preprocessing_seconds"))
        if len(entries) != len(DIRECTIONS):
            raise SystemExit(f"Missing reference cache entries for {name}")
        tiles.append(dict(name=name, spatial_key=key, entries=entries))
    return dict(
        schema="shade-watch-wsl2-smoke-reference-1.0",
        base_commit=BASE_COMMIT, accepted_engine_commit=ACCEPTED_ENGINE,
        reference_run=str(RUN.relative_to(ROOT)), reference_cache=str(CACHE.relative_to(ROOT)),
        request=dict(tiles=targets, direction_method=index["request"]["direction_method"],
                     local_timezone=index["request"]["local_timezone"],
                     instants=[f["local_time"] for f in frames]),
        grid=dict(width=index["grid"]["width"], height=index["grid"]["height"],
                  transform=index["grid"]["transform"], crs=index["grid"]["crs"]),
        dsm_files=dict(sorted(dsm_files.items())),
        tiles=tiles,
        frames=[dict(local_time=f["local_time"], utc_time=f["utc_time"], files=f["hashes"],
                     counts=f["counts"], quality_counts=f["quality_counts"],
                     solar_by_tile=[dict(source_name=t["source_name"], direction_deg=t["direction_deg"],
                                         apparent_elevation_deg=t["apparent_elevation_deg"],
                                         threshold_deg=t["threshold_deg"]) for t in f["solar_by_tile"]])
                for f in frames],
        tolerances=dict(horizon_abs_deg=1e-4, equality_neighbourhood_deg=1e-4,
                        note="V2 B08: horizon <= 1e-4 deg, identical support; label differences only "
                             "inside the equality neighbourhood"),
    )


def planned_copies(manifest: dict) -> list:
    copies = [(DSM / name, Path("dsm") / name, meta["sha256"]) for name, meta in manifest["dsm_files"].items()]
    for tile in manifest["tiles"]:
        for entry in tile["entries"].values():
            base = CACHE / tile["spatial_key"] / entry["entry"]
            rel = Path("reference/cache") / tile["spatial_key"] / entry["entry"]
            copies.append((base.with_suffix(".tif"), rel.with_suffix(".tif"), entry["tif_sha256"]))
            copies.append((base.with_suffix(".json"), rel.with_suffix(".json"), None))
    for frame in manifest["frames"]:
        for name, digest in frame["files"].items():
            folder = "shade" if name.startswith("shade_") else "quality"
            copies.append((RUN / "combined" / folder / name, Path("reference/frames") / name, digest))
    return copies


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", help="new directory under outputs/ (must not exist)")
    parser.add_argument("--dry-run", action="store_true", help="verify sources and hashes, copy nothing")
    args = parser.parse_args(argv)
    manifest = build_manifest()
    copies = planned_copies(manifest)
    for source, _, digest in copies:
        if not source.is_file():
            raise SystemExit(f"Missing source: {source}")
        if digest is not None and sha256(source) != digest:
            raise SystemExit(f"Hash mismatch: {source}")
    total = sum(s.stat().st_size for s, _, _ in copies)
    print(f"Verified {len(copies)} files, {total / 1e6:.1f} MB")
    if args.dry_run:
        print(json.dumps(dict(dsm_files=len(manifest["dsm_files"]), tiles=[t["name"] for t in manifest["tiles"]],
                              instants=manifest["request"]["instants"]), indent=2))
        return
    if not args.out:
        raise SystemExit("--out is required unless --dry-run")
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to((ROOT / "outputs").resolve()) or out.exists():
        raise SystemExit("--out must be a new directory under outputs/")
    for source, rel, digest in copies:
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest is not None and sha256(target) != digest:
            raise SystemExit(f"Copy verification failed: {target}")
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.check_call(["git", "bundle", "create", str(out / "repo.bundle"), branch], cwd=ROOT)
    subprocess.check_call(["git", "bundle", "verify", str(out / "repo.bundle")], cwd=ROOT)
    manifest["bundle"] = dict(file="repo.bundle", branch=branch, sha256=sha256(out / "repo.bundle"))
    (out / "reference_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    shutil.copy2(Path(__file__).with_name("run_smoke.py"), out / "run_smoke.py")
    shutil.copy2(Path(__file__).with_name("setup_wsl.sh"), out / "setup_wsl.sh")
    print(f"Pack written to {out}")


if __name__ == "__main__":
    sys.exit(main())
