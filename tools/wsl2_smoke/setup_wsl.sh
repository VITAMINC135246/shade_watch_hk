#!/usr/bin/env bash
# Set up shade_watch_hk inside WSL2 (Ubuntu 24.04) from an unpacked smoke pack.
# Usage, inside WSL:  bash ~/wsl2_smoke_pack_YYYYMMDD/setup_wsl.sh
# Optional: REPO=~/some/other/path bash .../setup_wsl.sh
set -euo pipefail

PACK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$HOME/shade_watch_hk}"

case "$PACK" in
  /mnt/*) echo "ERROR: the pack is on a Windows drive ($PACK). Copy it into the Linux home first, e.g. cp -r \"$PACK\" ~/" >&2; exit 1 ;;
esac
grep -qi microsoft /proc/version || echo "WARNING: this does not look like WSL; continuing as plain Linux."
FS="$(stat -f -c %T "$HOME")"
echo "Home filesystem type: $FS"

if ! command -v python3.12 >/dev/null 2>&1 || ! python3.12 -c "import venv, ensurepip" >/dev/null 2>&1; then
  echo "Installing python3.12, venv and git (needs sudo and network)..."
  sudo apt-get update
  sudo apt-get install -y python3.12 python3.12-venv git
fi

BASE="$(python3.12 -c "import json,sys; print(json.load(open(sys.argv[1]))['base_commit'])" "$PACK/reference_manifest.json")"
if [ -e "$REPO" ]; then
  echo "ERROR: $REPO already exists. Remove it or set REPO=... to a new path." >&2; exit 1
fi

git clone --no-checkout "$PACK/repo.bundle" "$REPO"
cd "$REPO"
git checkout --detach "$BASE"
mkdir -p tools/wsl2_smoke
cp "$PACK/run_smoke.py" tools/wsl2_smoke/run_smoke.py

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock.txt

echo
echo "Setup complete. Next, run the smoke test (about 10-30 minutes):"
echo "  cd $REPO && .venv/bin/python tools/wsl2_smoke/run_smoke.py --pack $PACK"
