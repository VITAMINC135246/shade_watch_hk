"""Record and audit protected paths. Keep the full snapshot outside the repo."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
import stat
import subprocess

from measure import CONTAINERS, ROOT

HK_VIEW = "8ee51b017411bd60e833e97fef10577546ba97f61e601df0fb21ecbfc0a4cbd1"
VIEW_ROOT = "data/processed/dsm_views/sea_fill_v2_2"
RAW_SHEETS = "data/raw/dsm/rotterdam_ahn4_dsm05"
ENGINE = ("horizon", "spatial", "v1_cache", "shade_watch")
BUILDER = ("__init__", "__main__", "build", "catalogue", "profile", "provider", "rule", "view")
PROTECTED = (
    ".gitignore", "config/machine.local.json", "docs/prompts/G1/ACCEPTANCE_CONTRACT.md",
    *(f"src/{name}.py" for name in ENGINE),
    *(f"tools/sea2/{name}.py" for name in BUILDER),
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identity(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def listing():
    items = {}
    for name in ("data/raw", "data/processed", "outputs"):
        start = ROOT / name
        pending = [start]
        while pending:
            path = pending.pop()
            info = path.lstat()
            kind = stat.S_IFMT(info.st_mode)
            items[path.relative_to(ROOT).as_posix()] = [
                kind, info.st_size, info.st_mtime_ns,
                str(path.readlink()) if stat.S_ISLNK(kind) else None,
            ]
            if stat.S_ISDIR(kind):
                pending.extend(path.iterdir())
    return items


def snapshot(paths):
    return dict(
        data=listing(),
        user={name: digest(ROOT/name) for name in paths},
        pinned={name: digest(ROOT/name) for name in (
            *PROTECTED,
            f"{VIEW_ROOT}/current-hk_cedd_2020.json",
            f"{VIEW_ROOT}/{HK_VIEW}/manifest.json",
            f"{RAW_SHEETS}/R_37FZ1.tif",
            f"{RAW_SHEETS}/R_37HN1.tif",
        )},
    )


def compact(items):
    return dict(entries=len(items), sha256=identity(items))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["before", "after"])
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--rotterdam-view")
    args = parser.parse_args()
    if args.action == "before":
        paths = git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")
        # The evidence directory was created by this task.
        paths = sorted(p for p in paths if p and not p.startswith("docs/city/"))
        current = snapshot(paths)
        args.snapshot.write_text(json.dumps(current))
        print(json.dumps(dict(
            head=git("rev-parse", "HEAD").decode().strip(),
            parent=git("rev-parse", "HEAD^").decode().strip(),
            branch=git("branch", "--show-current").decode().strip(),
            origin_feature=git("rev-parse", "origin/feature").decode().strip(),
            status=git("status", "--porcelain", "--untracked-files=normal").decode().splitlines(),
            data={name: compact({p: m for p, m in current["data"].items()
                                 if p == name or p.startswith(name+"/")})
                  for name in ("data/raw", "data/processed", "outputs",
                               "data/processed/shade_v1", f"{VIEW_ROOT}/{HK_VIEW}")},
            user=compact(current["user"]), pinned=current["pinned"],
        ), indent=2, sort_keys=True))
        return 0

    before = json.loads(args.snapshot.read_text())
    current = snapshot(before["user"])
    old, new = before["data"], current["data"]
    additions = new.keys() - old.keys()
    view = args.rotterdam_view
    allowed = (
        "data/processed/dsm_catalogues/rotterdam/",
        "data/processed/shade_v1/g1_dev_raw_",
        "data/processed/shade_v1/sea2_2_fill_impact_",
        f"data/processed/shade_v1/sea_fill_v2_2_{view[:12]}/",
        f"{VIEW_ROOT}/{view}/",
        f"{VIEW_ROOT}/current-nl_rotterdam_dsm05.json",
        f"{VIEW_ROOT}/build-nl_rotterdam_dsm05.lock",
        "outputs/shade_map_g1_dev_20261111/",
        "outputs/shade_map_work/g1_dev_",
        "outputs/shade_map_work/.locks/g1_dev_",
        "outputs/sea2_2_diagnostic_work/g1_dev_",
        "outputs/sea2_2_diagnostic_work/.locks/g1_dev_",
        "outputs/region_views/",
    )
    unexpected = sorted(p for p in additions if p not in CONTAINERS and
                        not any(p == a.rstrip("/") or p.startswith(a) for a in allowed))
    parents = {str(Path(p).parent) for p in additions}
    containers = set(CONTAINERS) | {"data/processed"}
    changed = sorted(p for p, m in old.items() if p not in new or
                     (new[p] != m and not (p in parents and p in containers and
                                           stat.S_ISDIR(m[0]) and stat.S_ISDIR(new[p][0]))))
    pinned_changed = current["pinned"] != before["pinned"]
    user_changed = current["user"] != before["user"]
    print(json.dumps(dict(
        original_entries=len(old), after_entries=len(new), additions=compact({p: new[p] for p in additions}),
        changed=changed, unexpected=unexpected, pinned_changed=pinned_changed, user_changed=user_changed,
        original_cache=compact({p: m for p, m in old.items() if p.startswith("data/processed/shade_v1/")}),
        after_original_cache=compact({p: new[p] for p in old if p in new and p.startswith("data/processed/shade_v1/")}),
        original_hk_view=compact({p: m for p, m in old.items() if p.startswith(f"{VIEW_ROOT}/{HK_VIEW}")}),
        after_hk_view=compact({p: m for p, m in new.items() if p.startswith(f"{VIEW_ROOT}/{HK_VIEW}")}),
        user=compact(current["user"]), pinned=current["pinned"],
    ), indent=2, sort_keys=True))
    return int(bool(unexpected or changed or pinned_changed or user_changed))


if __name__ == "__main__":
    raise SystemExit(main())
