"""Check the repository layout and frozen file contents required by SW-H1.0."""

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CACHE_HASHES = {
    'horizon.py': 'afb46c37742767e7480220d82527873ed389bb184623fef78b4a3a1d19e8144e',
    'spatial.py': '5ecc0495dd102596ab41903b5e174c142888ffc14664b81009164fbf176d3aa7',
    'v1_cache.py': '96a576d12ada9186319e4c8c5f1e626b06ab0aac5f7345a9c6083b9f1b6fe479',
}
OLD_REFERENCES = re.compile(
    r'\b(?:from|import)\s+(?:src|tools)\b'
    r'|(?<![\w.-])(?:src|tools|outputs)/'
    r'|(?<![\w.-])(?:data/processed|data/raw/dsm)(?![\w-])'
    r'|(?<![\w-])(?:shade_map_work|region_views|sea2_2_diagnostic_work|dsm_views|shade_v1)(?![\w-])'
    r"""|(?P<quote>['"])(?:src|tools|outputs)(?P=quote)"""
)
HISTORICAL_DIRECTORIES = (
    'docs/records/', 'docs/planning/', 'docs/packages/', 'legacy/',
)
HISTORICAL_FILES = {
    'docs/CONVENTIONS.md', 'config/engine/estimator.json', 'tests/test_layout.py',
}


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def test_repository_top_level():
    allowed = {
        'README.md', '.gitignore', 'requirements.lock.txt', 'requirements.tools.lock.txt',
        'shade_watch', 'config', 'tests', 'web', 'docs', 'legacy', 'references', 'data',
        'runs', 'work', 'baselines', 'archive', 'presentations', '.venv', '.git',
        '.DS_Store', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
        '.ipynb_checkpoints', 'node_modules',
    }
    assert {entry.name for entry in ROOT.iterdir()} <= allowed


def test_docs_top_level():
    allowed = {
        'CONVENTIONS.md', 'OUTPUT_CODES.md', 'packages', 'planning', 'records',
        'INDEX.md', 'ARCHITECTURE.md', 'GUIDE.md', 'GUIDE.zh-TW.md', 'design',
    }
    assert {entry.name for entry in (ROOT / 'docs').iterdir()} <= allowed


def test_old_locations_are_absent():
    for name in ('src', 'tools', 'outputs', 'data/processed'):
        path = ROOT / name
        assert not path.exists() and not path.is_symlink(), name


def test_tracked_files_use_current_locations():
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    matches = []
    for name in filter(None, files):
        if name in HISTORICAL_FILES or name.startswith(HISTORICAL_DIRECTORIES):
            continue
        for number, line in enumerate((ROOT / name).read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            match = OLD_REFERENCES.search(line)
            if match:
                matches.append((name, number, match.group()))
    assert not matches


def test_frozen_cache_key_files():
    for name, expected in CACHE_HASHES.items():
        assert sha256(ROOT / 'shade_watch' / 'engine' / name) == expected, name


def test_moved_records_match_manifest():
    manifest_path = ROOT / 'docs/packages/H1.0/evidence/records_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / 'docs/records').rglob('*')
        if (path.is_file() or path.is_symlink()) and path.name != '.DS_Store'
    }
    assert actual == set(manifest)
    for name, metadata in manifest.items():
        assert sha256(ROOT / name) == metadata['sha256'], name
