"""Local transactional batch journal. Scientific arrays never enter this store."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from .v1_cache import atomic_json, exclusive_lock

TASK_STATES = {"PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"}
TRANSITIONS = {
    "PENDING": {"RUNNING", "CANCELLED", "FAILED"},
    "RUNNING": {"SUCCEEDED", "FAILED", "CANCELLED", "PENDING"},
    "FAILED": {"PENDING"}, "CANCELLED": {"PENDING"},
    "SUCCEEDED": {"PENDING"},  # only reconciliation of invalid committed artifacts
}


def local_filesystem(path):
    """Do not infer that SQLite/flock on NFS/SMB is a local coordination primitive."""
    path = Path(path).resolve()
    while not path.exists():
        path = path.parent
    if sys.platform == "darwin":
        class StatFS(ctypes.Structure):
            _fields_ = [("bsize", ctypes.c_uint32), ("iosize", ctypes.c_int32),
                        *[(n, ctypes.c_uint64) for n in ("blocks", "bfree", "bavail", "files", "ffree")],
                        ("fsid", ctypes.c_int32 * 2), ("owner", ctypes.c_uint32),
                        ("type", ctypes.c_uint32), ("flags", ctypes.c_uint32),
                        ("subtype", ctypes.c_uint32), ("fstype", ctypes.c_char * 16),
                        ("mount", ctypes.c_char * 1024), ("source", ctypes.c_char * 1024),
                        ("reserved", ctypes.c_uint32 * 8)]
        stat = StatFS()
        if ctypes.CDLL(None, use_errno=True).statfs(os.fsencode(path), ctypes.byref(stat)) != 0:
            raise OSError(ctypes.get_errno(), "Cannot verify local filesystem")
        if not stat.flags & 0x1000:  # Darwin MNT_LOCAL
            raise ValueError("V2 state/cache/output require a local filesystem")
        return stat.fstype.decode()
    if sys.platform.startswith("linux"):
        mounts = []
        for line in Path("/proc/mounts").read_text().splitlines():
            _, mount, kind, *_ = line.split()
            mount = mount.replace("\\040", " ")
            if path.is_relative_to(mount):
                mounts.append((len(mount), kind))
        kind = max(mounts)[1]
        if kind not in {"ext4", "ext3", "ext2", "xfs", "btrfs", "overlay", "tmpfs", "exfat", "vfat"}:
            raise ValueError(f"Unsupported filesystem for V2 local state: {kind}")
        return kind
    raise ValueError("V2 local coordination supports POSIX macOS/Linux only")


class Store:
    def __init__(self, directory, *, create=False):
        self.directory = Path(directory).resolve()
        self.path = self.directory / "state.sqlite"
        self.filesystem = local_filesystem(self.directory)
        if create:
            if self.path.exists():
                try:
                    if json.loads((self.directory / "store.json").read_text())["schema"] != "shade-watch-v2-state-1.0":
                        raise ValueError("Unsupported existing state schema")
                except (OSError, KeyError, ValueError) as exc:
                    raise ValueError("Unmanaged existing database is protected") from exc
            if self.directory.exists() and not self.path.exists() and any(self.directory.iterdir()):
                raise ValueError("Unmanaged existing state directory is protected")
            self.directory.mkdir(parents=True, exist_ok=True)
            with exclusive_lock(self.directory / ".schema.lock"):
                self._connect()
                self.db.executescript("""
                CREATE TABLE IF NOT EXISTS batches (
                  id TEXT PRIMARY KEY, definition TEXT NOT NULL, state TEXT NOT NULL,
                  cancelled INTEGER NOT NULL DEFAULT 0, owner TEXT, created REAL NOT NULL,
                  updated REAL NOT NULL, metrics TEXT NOT NULL DEFAULT '{}');
                CREATE TABLE IF NOT EXISTS requests (
                  batch TEXT NOT NULL, id TEXT NOT NULL, plan TEXT NOT NULL,
                  PRIMARY KEY(batch,id));
                CREATE TABLE IF NOT EXISTS outputs (directory TEXT PRIMARY KEY, plan_key TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY, batch TEXT NOT NULL, kind TEXT NOT NULL,
                  payload TEXT NOT NULL, state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                  max_attempts INTEGER NOT NULL, artifacts TEXT, error TEXT);
                CREATE INDEX IF NOT EXISTS task_queue ON tasks(batch,state,kind);
                CREATE TABLE IF NOT EXISTS edges (task TEXT NOT NULL, dependency TEXT NOT NULL,
                  PRIMARY KEY(task,dependency));
                CREATE INDEX IF NOT EXISTS reverse_edges ON edges(dependency);
                CREATE TABLE IF NOT EXISTS attempts (
                  task TEXT NOT NULL, number INTEGER NOT NULL, started REAL NOT NULL,
                  ended REAL, state TEXT NOT NULL, owner TEXT, error TEXT,
                  PRIMARY KEY(task,number));
                CREATE TABLE IF NOT EXISTS events (
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT, batch TEXT NOT NULL,
                  task TEXT, time REAL NOT NULL, event TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS batch_events ON events(batch,sequence);
                CREATE TRIGGER IF NOT EXISTS immutable_batch BEFORE UPDATE OF id,definition,created ON batches
                  BEGIN SELECT RAISE(ABORT,'immutable batch definition'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_request BEFORE UPDATE ON requests
                  BEGIN SELECT RAISE(ABORT,'immutable scientific request'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_task BEFORE UPDATE OF id,batch,kind,payload,max_attempts ON tasks
                  BEGIN SELECT RAISE(ABORT,'immutable task definition'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_edge BEFORE UPDATE ON edges
                  BEGIN SELECT RAISE(ABORT,'immutable dependency'); END;
                """)
                atomic_json(self.directory / "store.json", dict(schema="shade-watch-v2-state-1.0",
                            filesystem=self.filesystem, journal="DELETE", synchronous="FULL"))
        else:
            if not self.path.exists():
                raise ValueError("No V2 persistent store exists here")
            self._connect()
        if json.loads((self.directory / "store.json").read_text())["schema"] != "shade-watch-v2-state-1.0":
            raise ValueError("Unsupported V2 store schema")

    def _connect(self):
        self.db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self.db.close()

    @contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def event(self, batch, task, value):
        self.db.execute("INSERT INTO events(batch,task,time,event) VALUES(?,?,?,?)",
                        (batch, task, time.time(), json.dumps(value, allow_nan=False)))

    def batch(self, batch):
        row = self.db.execute("SELECT * FROM batches WHERE id=?", (batch,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown batch: {batch}")
        return dict(row)

    def task(self, task):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown task: {task}")
        return dict(row)

    def transition(self, task, state, *, owner=None, error=None, artifacts=None, reason=None):
        if state not in TASK_STATES:
            raise ValueError("Unknown task state")
        row = self.task(task)
        old, number = row["state"], row["attempts"]
        if state not in TRANSITIONS[old]:
            raise ValueError(f"Illegal task transition {old} -> {state}")
        if old == "SUCCEEDED" and (state != "PENDING" or reason != "invalid_artifacts"):
            raise ValueError("Succeeded tasks can only be invalidated after artifact validation")
        if state == "RUNNING":
            if number >= row["max_attempts"]:
                raise ValueError("Task attempt ceiling exhausted")
            number += 1
            self.db.execute("INSERT INTO attempts(task,number,started,state,owner) VALUES(?,?,?,?,?)",
                            (task, number, time.time(), state, json.dumps(owner)))
        elif old == "RUNNING":
            self.db.execute("UPDATE attempts SET ended=?,state=?,error=? WHERE task=? AND number=?",
                            (time.time(), state, json.dumps(error), task, number))
        self.db.execute("UPDATE tasks SET state=?,attempts=?,error=?,artifacts=? WHERE id=?",
                        (state, number, json.dumps(error) if error else None,
                         json.dumps(artifacts) if artifacts is not None else row["artifacts"], task))
        self.event(row["batch"], task, dict(transition=[old, state], reason=reason, error=error))

    def set_batch(self, batch, state, *, owner=None, metrics=None):
        self.db.execute("UPDATE batches SET state=?,updated=?,owner=?,metrics=COALESCE(?,metrics) WHERE id=?",
                        (state, time.time(), json.dumps(owner) if owner else None,
                         json.dumps(metrics) if metrics is not None else None, batch))

    def ready(self, batch, *, reverse=False):
        # No eager list of all queued tasks or raster buffers.
        return self.db.execute("""SELECT t.* FROM tasks t WHERE t.batch=? AND t.state='PENDING'
          AND NOT EXISTS(SELECT 1 FROM edges e JOIN tasks d ON d.id=e.dependency
                         WHERE e.task=t.id AND d.state!='SUCCEEDED')
          ORDER BY t.rowid """ + ("DESC" if reverse else "ASC") + " LIMIT 1", (batch,)).fetchone()
