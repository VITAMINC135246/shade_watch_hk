"""Confirm the frozen five-class targets before any shade runs."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from src import v1
from tools.sea2 import VIEW_NAMESPACE
from tools.sea2.rule import counts
from tools.sea2.view import read_manifest, read_surface_window
from tools.shade_map.common import atomic_json, digest, read_json
from finalize_manifest import finalize


def main():
    evidence = Path(__file__).resolve().parent
    directory = v1.ROOT/'data/processed/dsm_views'/VIEW_NAMESPACE
    pointer = read_json(directory/'current-hk_cedd_2020.json')
    view = finalize(directory,pointer,evidence)
    doc = read_manifest(view)
    region = read_json(evidence/'configs/five_class.json')
    bounds = region['lower_left']+region['upper_right']
    classes = counts(read_surface_window(view,bounds,manifest=doc))
    cache = v1.ROOT/'data/processed/shade_v1'/(VIEW_NAMESPACE+'_'+doc['view_id'][:12])
    result = dict(view_id=doc['view_id'],manifest_sha256=digest(view/'manifest.json'),view=str(view),
                  bounds=bounds,classes=classes,cold_cache=not cache.exists(),
                  five_classes=all(classes[str(k)]>0 for k in range(5)) and classes['255']==0)
    atomic_json(evidence/'view-preflight.json',result)
    print(result)
    if not result['five_classes'] or not result['cold_cache']:
        raise SystemExit('Stop before shade runs. The five-class or cold-cache precondition failed.')


if __name__=='__main__':
    main()
