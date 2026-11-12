"""Capture protected file metadata and compare it after the B2.2 campaign."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
TREE = ('data/raw', 'data/processed', 'outputs', 'presentations', 'docs/prompts',
        'docs/planning', 'docs/sea2/evidence', 'docs/ui', 'tools/wsl2_smoke', 'web/console')
FILES = ('.gitignore', 'docs/OUTPUT_CODES.md', 'docs/PROJECT_STATUS_2026-10-29.zh-TW.md',
         'docs/v3/WSL2_SMOKE_TEST.md', 'docs/sea2/DEVELOPMENT_REPORT.md')
MUTABLE = EVIDENCE.relative_to(ROOT).as_posix()+'/'

ALLOWED = re.compile(
    r'data/processed/(?:dsm_views/sea_fill_v2_2/|shade_v1/(?:sea_fill_v2_2_|sea2_2_(?:raw|fill_impact)_)[^/]+/)'
    r'|outputs/(?:sea2_2_[^/]+/|region_views/[0-9a-f]{64}/'
    r'|shade_map_work/(?:sea2_2_[a-z_]+-[0-9a-f]{12}/|\.locks/sea2_2_[a-z_]+\.lock$))')


def record(path, content=False):
    info = path.lstat()
    value = [stat.S_IMODE(info.st_mode),info.st_size,info.st_mtime_ns]
    if path.is_symlink():
        value.append(os.readlink(path))
    elif content:
        with path.open('rb') as stream:
            value.append(hashlib.file_digest(stream,'sha256').hexdigest())
    return value


def inventory():
    result = {}
    for base in TREE:
        group = result[base] = {}
        for directory, dirs, files in os.walk(ROOT/base):
            # Directory symlinks are files for the audit and are never followed.
            links = [name for name in dirs if (Path(directory)/name).is_symlink()]
            dirs[:] = [name for name in dirs if name not in links]
            for name in files+links:
                path = Path(directory)/name
                key = path.relative_to(ROOT).as_posix()
                if not key.startswith(MUTABLE):
                    group[key] = record(path,content=base.startswith(('docs/','tools/','web/')))
    result['protected files'] = {name:record(ROOT/name,content=True) for name in FILES}
    return result


def hash_group(group):
    data = json.dumps(group,sort_keys=True,separators=(',',':')).encode()
    return dict(files=len(group), bytes=sum(v[1] for v in group.values()),
                inventory_sha256=hashlib.sha256(data).hexdigest())


def write(path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


def leaf(key):
    parts = key.split('/')
    if parts[:2] == ['data','processed']:
        return '/'.join(parts[:4])
    if parts[:2] in (['outputs','region_views'],['outputs','shade_map_work']):
        return '/'.join(parts[:3])
    return '/'.join(parts[:2])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['before','after'])
    parser.add_argument('full_inventory',type=Path)
    args = parser.parse_args()
    current = inventory()
    if args.phase=='before':
        write(args.full_inventory,current)
        write(EVIDENCE/'protected-before.json', {k:hash_group(v) for k,v in current.items()})
        return
    before = json.loads(args.full_inventory.read_text())
    old_files = {key:value for group in before.values() for key,value in group.items()}
    files = {key:value for group in current.values() for key,value in group.items()}
    changed = [key for key in old_files.keys() & files.keys() if old_files[key]!=files[key]]
    added = sorted(files.keys()-old_files.keys())
    old_leaves = {leaf(k) for k in old_files}
    disallowed = [k for k in added if not ALLOWED.match(k) or
                  (leaf(k) in old_leaves and not k.startswith('outputs/shade_map_work/.locks/'))]
    result = dict(existing_groups={k:hash_group({p:files[p] for p in group if p in files}) for k,group in before.items()},
                  missing=sorted(old_files.keys()-files.keys()), changed=sorted(changed),
                  new_files_by_namespace=dict(Counter(leaf(k) for k in added)),
                  new_files_sha256=hash_group({k:files[k] for k in added}),
                  unexpected_new_files=disallowed)
    write(EVIDENCE/'protected-after.json',result)
    if result['missing'] or changed or disallowed:
        raise SystemExit('Protected path audit differs; see protected-after.json')


if __name__=='__main__':
    main()
