"""Authorized development stages only; never independent acceptance."""
import json
from pathlib import Path
import sys

from tools.sea_view.build import build_view,SCOPES
from tools.sea_view.checks import ROOT,EVIDENCE
from tools.sea_view.helpers import read_manifest


def build():
    evidence={}
    for scope in SCOPES:
        first=build_view(scope)
        again=build_view(scope)
        assert first==again
        manifest=read_manifest(first)
        evidence[scope]=dict(path=str(first),view_id=first.name,rebuild_equal=True,
                            supplied_tiles=sum(not r['synthetic'] for r in manifest['tiles']),
                            synthetic_tiles=sum(r['synthetic'] for r in manifest['tiles']),
                            sea_fill_pixels=sum(r['sea_fill_pixels'] for r in manifest['tiles']),
                            manifest=manifest)
        (EVIDENCE/'views.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(scope,first,flush=True)


def requests_for(scope,view,output,*,raw=False):
    from src import v1
    baseline=json.loads((ROOT/'outputs/v2_daylight_cheungchau_20261009/combined/result_index.json').read_text())
    cache=ROOT/'data/processed/shade_v1'/('sea_fill_v1_raw_central' if raw else 'sea_fill_v1_'+view.name)
    common=dict(id=scope,tiles=SCOPES[scope],dsm_dir=str(view/'tiles'),cache_dir=str(cache),
                output_dir=str(output),direction_method='nearest5',jpg=False,mp4=False)
    if scope=='cheung_chau': common.update(dates=['2026-01-07'],interval_minutes=10)
    else: common.update(instants=['2026-01-07T08:30:00+08:00','2026-01-07T12:30:00+08:00','2026-01-07T15:10:00+08:00'])
    return common


def run_scope(scope):
    from src import v1,v2
    from tools.sea_view.checks import RAW
    from tools.sea_view.helpers import effective_policy,read_surface_window
    import numpy as np
    views=json.loads((EVIDENCE/'views.json').read_text())
    view=Path(views[scope]['path']);manifest=read_manifest(view)
    rawview=ROOT/f'outputs/sea_dev_raw_{scope}'
    (rawview/'tiles').mkdir(parents=True,exist_ok=False)
    for row in manifest['tiles']:
        if not row['synthetic']: (rawview/'tiles'/row['name']).symlink_to(RAW/row['name'])
    rawreq=requests_for(scope,rawview,ROOT/f'outputs/sea_dev_raw_{scope}/combined',raw=True)
    request=requests_for(scope,view,ROOT/f'outputs/sea_dev_{scope}/combined')
    rawplan=v1.plan_shade(**{k:v for k,v in rawreq.items() if k!='id'})
    plan=v1.plan_shade(**{k:v for k,v in request.items() if k!='id'})
    assert plan.key!=rawplan.key
    assert all(a.spatial_key!=b.spatial_key for a,b in zip(plan.tiles,rawplan.tiles))
    if scope=='cheung_chau':
        baseline=json.loads((ROOT/'outputs/v2_daylight_cheungchau_20261009/combined/result_index.json').read_text())
        assert [i.utc for i in plan.request.instants]==[f['utc_time'] for f in baseline['frames']]
        oldkeys={t['spatial_key'] for t in baseline['frames'][0]['solar_by_tile']}
        assert {t.spatial_key for t in rawplan.tiles}==oldkeys, 'Raw baseline dependencies changed'
    batch=v2.plan_batch([request],workers=2,memory_budget_mb=12288,artifact_budget_bytes=10*1024**3)
    (EVIDENCE/f'{scope}-plan.json').write_text(json.dumps(dict(estimate=batch.estimate,resources=batch.definition['resources'],
              view_key=plan.key,raw_key=rawplan.key,view_spatial_keys=[t.spatial_key for t in plan.tiles],
              raw_spatial_keys=[t.spatial_key for t in rawplan.tiles],frames=len(plan.request.instants)),indent=2)+'\n')
    state=ROOT/f'outputs/sea_dev_{scope}/state'
    identifier=v2.submit_batch(batch,state_dir=state)
    result=v2.run_batch(identifier,state_dir=state)
    (EVIDENCE/f'{scope}-result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['state']=='SUCCEEDED',result['failures']
    index=Path(request['output_dir'])/'result_index.json'
    policy=effective_policy(index)
    surface,trans=read_surface_window(view,plan.grid.bounds())
    bounds=plan.grid.bounds()
    oddbounds=(bounds[0]+1.5,bounds[1]+2.5,bounds[0]+12.5,bounds[3]-3.5)
    odd,ot=read_surface_window(view,oddbounds)
    assert np.array_equal(odd,surface[7:surface.shape[0]-5,3:25])
    (EVIDENCE/f'{scope}-helpers.json').write_text(json.dumps(dict(policy=policy,shape=surface.shape,
            transform_equal=trans==plan.grid.affine,odd_crop_equal=True,surface_counts={str(k):int(v) for k,v in zip(*np.unique(surface,return_counts=True))}),indent=2)+'\n')
    if scope=='central':
        batch=v2.plan_batch([rawreq],workers=2)
        state=ROOT/'outputs/sea_dev_raw_central/state'
        identifier=v2.submit_batch(batch,state_dir=state)
        result=v2.run_batch(identifier,state_dir=state)
        (EVIDENCE/'central-raw-result.json').write_text(json.dumps(result,indent=2)+'\n')
        assert result['state']=='SUCCEEDED',result['failures']


if __name__=='__main__':
    action=sys.argv[1]
    if action=='build': build()
    elif action in SCOPES: run_scope(action)
    elif action=='compare_cheung_chau':
        from tools.sea_view.compare import compare
        compare('cheung_chau')
    elif action=='compare_central':
        from tools.sea_view.compare import compare
        compare('central')
    elif action=='rays':
        from tools.sea_view.rays import run
        run()
    elif action=='sensitivity':
        from tools.sea_view.sensitivity import run
        run()
    else: raise ValueError('Unknown development stage')
