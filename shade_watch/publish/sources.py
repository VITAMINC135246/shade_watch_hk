"""DSM providers. Adding a source requires no change to publication code."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from shade_watch.engine import v1
from shade_watch.engine.spatial import intersects
from .common import digest


class SourceProvider(Protocol):
    def catalogue(self, machine: dict) -> Path: ...
    def cache_namespace(self, machine: dict) -> str: ...
    def policies(self) -> dict: ...
    def source_identity(self, records: list[dict]) -> dict: ...
    def preview_identity(self, region: dict, machine: dict) -> dict: ...
    def read_surface(self, bounds, records: list[dict]) -> np.ndarray: ...


class RawSource:
    def catalogue(self, machine):
        return Path(machine['dsm_dir'])

    def cache_namespace(self, machine):
        return machine['cache_namespace']

    def policies(self):
        return dict(engine=v1.POLICY, sea='none')

    def source_identity(self, records):
        sources = []
        for record in sorted(records, key=lambda r: Path(r['path']).name):
            sources.append(dict(name=Path(record['path']).name, sha256=digest(record['path']),
                                auxiliary=[dict(name=Path(a['path']).name, sha256=digest(a['path']))
                                           for a in sorted(record.get('auxiliary_files', []), key=lambda a: Path(a['path']).name)]))
        return dict(provider='raw', sources=sources)

    def preview_identity(self, region, machine):
        """Read-only conflict check before the adapter can publish a new view.

        This selects catalogue dependencies only; the engine helper still owns
        snapping, and the adapter still owns every actual request and source view.
        """
        from shade_watch import region as adapter
        from .config import InvalidInput
        headers = []
        for path in sorted(self.catalogue(machine).glob('*.tif')):
            with rasterio.open(path) as ds:
                headers.append(dict(path=str(path), bounds=list(ds.bounds), width=ds.width,
                                    height=ds.height, crs=ds.crs.to_string() if ds.crs else None,
                                    auxiliary_files=[dict(path=p) for p in ds.files
                                                     if Path(p).resolve() != path.resolve()]))
        if not headers:
            raise InvalidInput('dsm_dir: no DSM GeoTIFF files found')
        a = adapter.project_corner(region['lower_left'], region['crs'])
        b = adapter.project_corner(region['upper_right'], region['crs'])
        grid = v1._custom_grid(headers, (a[0],a[1],b[0],b[1]))
        owners = [r for r in headers if intersects(grid.bounds(), r['bounds'])]
        halos = [(r['bounds'][0]-adapter.BUFFER_M, r['bounds'][1]-adapter.BUFFER_M,
                  r['bounds'][2]+adapter.BUFFER_M, r['bounds'][3]+adapter.BUFFER_M) for r in owners]
        selected = [r for r in headers if any(intersects(r['bounds'], halo) for halo in halos)]
        return self.source_identity(selected)

    def read_surface(self, bounds, records):
        grid = v1._custom_grid(records, bounds)
        result = np.full((grid.height, grid.width), 255, np.uint8)
        left, bottom, right, top = bounds
        for record in records:
            if not intersects(bounds, record['bounds']):
                continue
            l, b, r, t = record['bounds']
            a, z, c, d = max(left, l), max(bottom, b), min(right, r), min(top, t)
            with rasterio.open(record['path']) as ds:
                data = ds.read(1, window=from_bounds(a, z, c, d, ds.transform))
            rows = slice(round((top-d)/.5), round((top-z)/.5))
            cols = slice(round((a-left)/.5), round((c-left)/.5))
            result[rows, cols] = np.where(np.isfinite(data) & (data != -9999), 0, 255).astype(np.uint8)
        return result


from shade_watch.fill.provider import SeaSource

PROVIDERS: dict[str, SourceProvider] = {'raw': RawSource(), 'sea-2.2': SeaSource()}


def provider(name):
    try:
        return PROVIDERS[name]
    except KeyError as exc:
        from .config import InvalidInput
        raise InvalidInput(f'dsm_source: unknown provider {name}') from exc
