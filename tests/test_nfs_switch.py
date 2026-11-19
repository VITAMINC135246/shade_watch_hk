"""Exploration switch SHADE_WATCH_ALLOW_NFS (C2.0 discovery, not accepted).

The mount table is faked so the tests run on any Linux machine; the folders themselves are local.
"""
import json
import sys
from pathlib import Path

import pytest

from shade_watch.engine import v2_state

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads the Linux mount table")


@pytest.fixture
def mount_as(monkeypatch, tmp_path):
    """Make tmp_path look like a mount point of the given file-system type."""
    real = Path.read_text

    def install(kind):
        table = f"rootfs / ext4 rw 0 0\nserver:/export {tmp_path} {kind} rw 0 0\n"

        def read_text(self, *args, **kwargs):
            if str(self) == "/proc/mounts":
                return table
            return real(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)
        monkeypatch.setattr(v2_state, "_nfs_warned", False)
        return tmp_path / "state"

    return install


@pytest.mark.parametrize("kind", ["nfs", "nfs4"])
def test_nfs_refused_without_switch(mount_as, monkeypatch, kind):
    monkeypatch.delenv(v2_state.NFS_SWITCH, raising=False)
    with pytest.raises(ValueError, match=f"Unsupported filesystem for V2 local state: {kind}; set SHADE_WATCH_ALLOW_NFS=1"):
        v2_state.local_filesystem(mount_as(kind))


@pytest.mark.parametrize("value", ["0", "true", "yes", ""])
def test_switch_needs_exact_value(mount_as, monkeypatch, value):
    monkeypatch.setenv(v2_state.NFS_SWITCH, value)
    with pytest.raises(ValueError, match="Unsupported filesystem"):
        v2_state.local_filesystem(mount_as("nfs4"))


@pytest.mark.parametrize("kind", ["nfs", "nfs4"])
def test_switch_allows_nfs_and_warns_once(mount_as, monkeypatch, capsys, kind):
    monkeypatch.setenv(v2_state.NFS_SWITCH, "1")
    path = mount_as(kind)
    assert v2_state.local_filesystem(path) == kind
    assert v2_state.local_filesystem(path) == kind
    err = capsys.readouterr().err
    assert err.count("SHADE_WATCH_ALLOW_NFS=1") == 1
    assert "at most one V2 job (shade_watch run or fill-impact) at a time" in err


@pytest.mark.parametrize("kind", ["cifs", "smb3", "lustre", "gpfs", "fuse.sshfs", "zfs"])
def test_switch_does_not_allow_other_file_systems(mount_as, monkeypatch, kind):
    monkeypatch.setenv(v2_state.NFS_SWITCH, "1")
    with pytest.raises(ValueError) as error:
        v2_state.local_filesystem(mount_as(kind))
    assert str(error.value) == f"Unsupported filesystem for V2 local state: {kind}"


@pytest.mark.parametrize("switch", [None, "1"])
def test_local_file_systems_unchanged(mount_as, monkeypatch, capsys, switch):
    if switch is None:
        monkeypatch.delenv(v2_state.NFS_SWITCH, raising=False)
    else:
        monkeypatch.setenv(v2_state.NFS_SWITCH, switch)
    assert v2_state.local_filesystem(mount_as("ext4")) == "ext4"
    assert capsys.readouterr().err == ""


def test_store_records_nfs_when_switched(mount_as, monkeypatch):
    monkeypatch.setenv(v2_state.NFS_SWITCH, "1")
    store = v2_state.Store(mount_as("nfs4"), create=True)
    assert store.filesystem == "nfs4"
    assert json.loads((store.directory / "store.json").read_text())["filesystem"] == "nfs4"
