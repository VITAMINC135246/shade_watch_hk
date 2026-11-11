"""Publication integrity and atomic local JSON operations."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

from .config import InvalidInput, canonical

CONTRACT = 'SW-F1.0'
FORMAT = 'shade-map-publication-1.1'
ENGINE_FILES = tuple('src/' + n + '.py' for n in (
    'v1', 'v1_cache', 'horizon', 'solar', 'spatial', 'shade_watch',
    'v2', 'v2_worker', 'v2_runner', 'v2_state'))
CODE_ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as src:
        for block in iter(lambda: src.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def identity(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n'
    fd, temp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as dst:
            dst.write(data)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def seal(document):
    document.pop('integrity_sha256', None)
    document['integrity_sha256'] = identity(document)
    return document


def verify_seal(document):
    if document.get('integrity_sha256') != identity({
            k: v for k, v in document.items() if k != 'integrity_sha256'}):
        raise RuntimeError('Published manifest integrity differs')


def safe_relative(path):
    text = str(path)
    pure = PurePosixPath(text)
    if (pure.is_absolute() or '..' in pure.parts or str(pure) != text
            or not re.fullmatch(r'[A-Za-z0-9._/-]+', text) or len(text) > 100):
        raise RuntimeError(f'Unsafe published relative path: {text}')
    return text


def verify_files(directory, files):
    directory = Path(directory)
    folded = set()
    for name, expected in files.items():
        safe_relative(name)
        if name.casefold() in folded:
            raise RuntimeError('Case-insensitive file name collision')
        folded.add(name.casefold())
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise RuntimeError(f'Published file hash differs: {name}')


@contextmanager
def name_lock(work_root, name, *, create=True):
    directory = Path(work_root) / '.locks'
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    lock = directory / (name + '.lock')
    fd = os.open(lock, os.O_RDWR | (os.O_CREAT if create else 0), 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InvalidInput(f'name: another run owns the lock for {name}') from exc
        yield lock
    finally:
        os.close(fd)
