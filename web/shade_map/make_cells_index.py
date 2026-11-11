"""Build web/shade_map/data/cells.json from the current B2.2 sea view manifest.

The web page uses this index to draw the native DSM lattice, to estimate how many
native cells a request touches, and to warn about the four `14NE15*` tiles that
planning rejects (decision D-008). It is display and planning help only: the
`shade_map plan` command remains authoritative.

Read-only on data. Standard library only. Run from the repository root:

    python3 web/shade_map/make_cells_index.py [--profile hk_cedd_2020] [--manifest PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEWS = ROOT / 'data' / 'processed' / 'dsm_views' / 'sea_fill_v2_2'
OUTPUT = Path(__file__).resolve().parent / 'data' / 'cells.json'


def manifest_path(profile: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    pointer = json.loads((VIEWS / f'current-{profile}.json').read_text())
    return VIEWS / pointer['view_id'] / 'manifest.json'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--profile', default='hk_cedd_2020')
    parser.add_argument('--manifest', help='explicit view manifest.json (default: current pointer)')
    args = parser.parse_args()
    path = manifest_path(args.profile, args.manifest)
    raw = path.read_bytes()
    manifest = json.loads(raw)
    grid = manifest['grid']
    exceptions = sorted(item['name'] for item in manifest.get('literal_definition_exceptions', []))
    rows = []
    for cell in manifest['cells']:
        left, bottom = cell['native_bounds'][0], cell['native_bounds'][1]
        counts = {int(k): int(v) for k, v in cell['counts'].items()}
        inside = sum(v for k, v in counts.items() if k != 255)
        land = counts.get(0, 0) + counts.get(3, 0)
        water = counts.get(1, 0) + counts.get(2, 0)
        tile = cell['tile_name'][:-4] if cell['supplied'] and cell['tile_name'].endswith('.tif') else None
        rows.append([
            int(left), int(bottom), 1 if cell['supplied'] else 0,
            round(1000 * land / inside) if inside else 0,
            round(1000 * water / inside) if inside else 0,
            counts.get(3, 0),
            tile,
        ])
    rows.sort(key=lambda r: (r[1], r[0]))
    index = {
        'schema': 'shade-map-web-cells-1.0',
        'note': 'Display and planning help only; shade_map plan is authoritative.',
        'source': {
            'view_id': manifest['view_id'],
            'policy': manifest['policy'],
            'manifest_sha256': hashlib.sha256(raw).hexdigest(),
        },
        'crs': grid['crs'],
        'cell_size_m': [grid['cell_width'] * grid['resolution'], grid['cell_height'] * grid['resolution']],
        'resolution_m': grid['resolution'],
        'domain_bounds': grid['domain_bounds'],
        'literal_exceptions': [name[:-4] if name.endswith('.tif') else name for name in exceptions],
        'columns': ['left', 'bottom', 'supplied', 'land_permille', 'water_permille', 'enclosed_pixels', 'tile'],
        'cells': rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(index, separators=(',', ':')) + '\n')
    print(f'wrote {OUTPUT.relative_to(ROOT)}: {len(rows)} cells from view {manifest["view_id"][:12]}')


if __name__ == '__main__':
    main()
