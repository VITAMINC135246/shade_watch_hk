"""F1 provider integration, implemented outside F's frozen orchestration."""
from contextvars import ContextVar
from pathlib import Path

MISSING = 'sea view missing or built from a different catalogue; run python -m tools.sea2 build'


class SeaSource:
    def __init__(self):
        self._active=ContextVar('sea2_active_view',default=None)

    def catalogue(self,machine):
        from src import v1
        from tools.shade_map.common import identity, read_json
        from tools.shade_map.config import InvalidInput
        from .catalogue import header_inventory
        from .profile import load_profile
        from .view import read_manifest
        profile=load_profile(machine)
        root=v1.ROOT/'data/processed/dsm_views/sea_fill_v2'
        pointer=root/f'current-{profile["profile_id"]}.json'
        try:
            if pointer.is_symlink(): raise ValueError('pointer symlink')
            doc=read_json(pointer)
            import re
            if not re.fullmatch('[0-9a-f]{64}',doc['view_id']): raise ValueError('invalid view ID')
            view=root/doc['view_id']; manifest=read_manifest(view)
            from . import POLICY
            if (doc['schema']!='sea-view-pointer-2.0' or manifest['diagnostic']
                    or manifest['schema']!='sea-view-2.0' or manifest['policy']!=POLICY
                    or manifest['view_id']!=doc['view_id'] or manifest['profile']!=profile
                    or doc['profile_id']!=profile['profile_id']
                    or doc['header_inventory']!=header_inventory(machine['dsm_dir'])
                    or doc['profile_sha256']!=identity(profile)
                    or manifest['profile_sha256']!=identity(profile)):
                raise ValueError('stale view')
            expected={t['name'] for t in manifest['tiles']}|set(manifest.get('auxiliary_outputs',{}))
            if {p.name for p in (view/'tiles').iterdir()}!=expected:
                raise ValueError('view tile inventory differs')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            raise InvalidInput(MISSING) from exc
        self._active.set((view,manifest))
        return view/'tiles'

    def cache_namespace(self,machine):
        self.catalogue(machine)
        return 'sea_fill_v2_'+self._active.get()[1]['view_id'][:12]

    def policies(self):
        from src import v1
        from . import POLICY
        return dict(engine=v1.POLICY,sea=POLICY)

    def source_identity(self,records):
        from tools.shade_map.sources import RawSource
        from tools.shade_map.config import InvalidInput
        active=self._active.get()
        if active is None: raise InvalidInput(MISSING)
        view,manifest=active
        raw=RawSource.source_identity(self,records)
        expected={r['name']:r['output_sha256'] for r in manifest['tiles']}
        if any(expected.get(s['name'])!=s['sha256'] for s in raw['sources']):
            raise InvalidInput('sea view: selected tile hashes differ from manifest')
        # Bind publication records to their immutable view, independent of later plans.
        for record in records: record['_sea2_view']=str(view)
        return dict(provider='sea-2.0',view_id=manifest['view_id'],
                    profile_sha256=manifest['profile_sha256'],sources=raw['sources'])

    def preview_identity(self,region,machine):
        from tools.shade_map.sources import RawSource
        return RawSource.preview_identity(self,region,machine)

    def read_surface(self,bounds,records):
        from .view import read_surface_window
        bound={r['_sea2_view'] for r in records if '_sea2_view' in r}
        if len(bound)!=1:
            raise RuntimeError('sea view: publication records must bind exactly one view')
        return read_surface_window(bound.pop(),bounds)
