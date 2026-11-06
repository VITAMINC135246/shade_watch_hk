"""One-time manifest-only correction before any B2.2 development plan."""
from pathlib import Path

from tools.sea2.build import build_code_hashes
from tools.sea2.view import manifest_identity, read_manifest
from tools.shade_map.common import atomic_json, digest


def finalize(directory, pointer, evidence):
    """Record the indirectly imported provider and change the view ID once."""
    original_id = pointer['view_id']
    view = directory/original_id
    doc = read_manifest(view)
    path = 'tools/sea2/provider.py'
    original_hashes = doc['build_code_sha256']
    if path in original_hashes:
        return view
    assert original_hashes == build_code_hashes()
    build = Path(__file__).resolve().parents[4]/'tools/sea2/build.py'
    original = build.read_bytes()
    old = b"'profile.py', 'rule.py', 'view.py')"
    new = b"'profile.py', 'provider.py', 'rule.py', 'view.py')"
    assert original.count(old) == 1
    changed = original.replace(old,new)
    from hashlib import sha256
    final_hashes = dict(original_hashes)
    final_hashes['tools/sea2/build.py'] = sha256(changed).hexdigest()
    final_hashes[path] = digest(build.with_name('provider.py'))
    original_manifest_hash = digest(view/'manifest.json')
    doc['build_code_sha256'] = final_hashes
    doc['view_id'] = manifest_identity(doc)
    final = directory/doc['view_id']
    assert not final.exists() and not final.is_symlink()
    # The territory build has exited and no plan has consumed its pointer.
    # Only the code-hash map, identity, manifest and pointer change.
    build.write_bytes(changed)
    view.rename(final)
    atomic_json(final/'manifest.json',doc)
    pointer['view_id'] = doc['view_id']
    atomic_json(directory/'current-hk_cedd_2020.json',pointer)
    assert read_manifest(final)==doc
    atomic_json(evidence/'metadata-finalization.json',dict(
        previous_view_id=original_id, final_view_id=doc['view_id'],
        previous_manifest_sha256=original_manifest_hash, final_manifest_sha256=digest(final/'manifest.json'),
        original_build_code_sha256=original_hashes, final_build_code_sha256=final_hashes,
        tile_and_surface_records_sha256=manifest_identity(dict(tiles=doc['tiles'],cells=doc['cells'])),
        note='F package initialization imports the provider. Only its inclusion in BUILD_MODULES changed after the raster build. Raster files and all raster records were carried forward unchanged.'))
    return final
