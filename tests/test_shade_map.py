"""F1.0 development checks: synthetic inputs only; independent acceptance is separate."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from shade_watch.engine import v1, v2
from shade_watch import region as adapter
from shade_watch.publish import plan_shade_map, shade_map
from shade_watch.publish.__main__ import main
from shade_watch.publish.common import identity, read_json, seal
from shade_watch.publish.config import (InvalidInput, SCHEMAS, check_document, expanded_time,
                                    machine_config, region_config, validate_schema)
from shade_watch.publish.planning import prepare
from shade_watch.publish.runner import prune_region, run_region, verify_run
from shade_watch.publish.sources import PROVIDERS, RawSource


@pytest.fixture
def fixture_map(tmp_path,monkeypatch):
    monkeypatch.setattr(v1,'ROOT',tmp_path)
    raw=tmp_path/'data/raw/fixture'
    raw.mkdir(parents=True)
    for x,y in [(800000,820000),(800006,820000),(800000,820004)]:
        data=np.full((8,12),7,np.float32)
        data[0,0]=-9999
        data[0,1]=np.nan
        with rasterio.open(raw/f'tile_{x}_{y}.tif','w',driver='GTiff',width=12,height=8,count=1,
                           dtype='float32',crs='EPSG:2326',nodata=-9999,
                           transform=from_origin(x,y+4,.5,.5)) as dst:
            dst.write(data,1)
    machine=dict(schema='shade-map-machine-1.0',dsm_dir=str(raw),output_root='runs/published',
                 cache_namespace='fixture_f1',workers=1)
    region=dict(schema='shade-map-region-1.0',name='fixture',crs='hk1980',
                lower_left=[800004.13,820002.17],upper_right=[800008.32,820006.39],
                time=dict(mode='instants',instants=['2026-01-07T12:30']))
    return raw,machine,region


def listing(root):
    return {p.relative_to(root).as_posix():(p.lstat().st_size,p.lstat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file() or p.is_symlink()}


def _sample(schema):
    if 'oneOf' in schema: return _sample(schema['oneOf'][0])
    if 'const' in schema: return deepcopy(schema['const'])
    if 'enum' in schema: return schema['enum'][0]
    kind=schema.get('type')
    if isinstance(kind,list): kind=kind[0]
    if kind=='object': return {k:_sample(v) for k,v in schema.get('properties',{}).items() if k in schema.get('required',[])}
    if kind=='array': return [_sample(schema['items']) for _ in range(schema.get('minItems',0))]
    if kind in ('number','integer'): return schema.get('minimum',0)
    if kind=='string':
        pattern=schema.get('pattern','')
        if r'\d{4}-' in pattern: return '2026-01-07T12:30' if 'T' in pattern else '2026-01-07'
        if '[01]' in pattern: return '12:30'
        return 'a'*schema.get('minLength',1)
    if kind=='boolean': return False
    return None


def schema_rule_checks():
    """Walk every config validation keyword, with valid and invalid witnesses."""
    checked=[]
    annotations={'$schema','$id','default','description','title'}
    constraints={'type','const','enum','required','additionalProperties','minItems','maxItems',
                 'uniqueItems','minLength','maxLength','pattern','minimum','maximum','oneOf'}
    structural={'properties','items'}
    def walk(node,path):
        assert not set(node)-annotations-constraints-structural,(path,set(node))
        for key in constraints & node.keys():
            rule=node[key]
            good=_sample(node)
            local={key:rule}
            if key=='type':
                kinds=rule if isinstance(rule,list) else [rule]
                bad=next(x for x in [None,{},[],True,'text',1.5] if not any(
                    {'null':x is None,'object':type(x) is dict,'array':type(x) is list,'boolean':type(x) is bool,
                     'string':type(x) is str,'integer':type(x) is int,'number':type(x) in (int,float)}[t] for t in kinds))
            elif key=='const': bad='__wrong__'
            elif key=='enum': bad='__wrong__'
            elif key=='required': good={k:None for k in rule}; bad={k:None for k in rule[1:]}
            elif key=='additionalProperties':
                if rule is not False: continue
                local['properties']=node.get('properties',{})
                good={}; bad={'__unknown__':1}
            elif key=='minItems': good=[None]*rule; bad=[None]*(rule-1)
            elif key=='maxItems': good=[]; bad=[None]*(rule+1)
            elif key=='uniqueItems': good=[1,2]; bad=[1,1]
            elif key=='minLength': good='x'*rule; bad='x'*(rule-1)
            elif key=='maxLength': good=''; bad='x'*(rule+1)
            elif key=='pattern': bad='!'
            elif key=='minimum': good=rule; bad=rule-1
            elif key=='maximum': good=rule; bad=rule+1
            elif key=='oneOf': bad={'mode':'bad'}
            validate_schema(good,local)
            with pytest.raises(InvalidInput): validate_schema(bad,local)
            checked.append(path+'/'+key)
        for k,v in node.get('properties',{}).items(): walk(v,path+'/properties/'+k)
        if 'items' in node: walk(node['items'],path+'/items')
        for i,v in enumerate(node.get('oneOf',[])): walk(v,path+f'/oneOf/{i}')
    for name in ('machine','region'):
        walk(read_json(SCHEMAS/f'shade_map_{name}.schema.json'),name)
    return checked


def test_every_config_schema_rule():
    checked=schema_rule_checks()
    assert checked and len(checked)==len(set(checked))
    print('Schema constraints covered:',len(checked))


@pytest.mark.parametrize('key,value',[
    ('workers',True),('workers',0),('workers',5),('memory_budget_mb',511),
    ('memory_budget_mb',12289),('max_output_bytes',-1),('max_output_bytes','5'),
    ('cache_namespace','../old'),('schema','bad'),('unknown',1),('dsm_dir',[]),
])
def test_machine_validation(fixture_map,key,value):
    _,machine,_=fixture_map
    machine[key]=value
    with pytest.raises(InvalidInput,match=key): machine_config(machine)


@pytest.mark.parametrize('key,value',[
    ('name','UPPER'),('name','x'*49),('name','../escape'),('name',''),('name','foo\n'),('crs','EPSG:2326'),
    ('full_image',False),('dsm_source','sea'),('unknown',1),('lower_left',[1,2,3]),('schema','bad'),
])
def test_region_validation(fixture_map,key,value):
    _,_,region=fixture_map
    region[key]=value
    with pytest.raises(InvalidInput,match=key): region_config(region)


@pytest.mark.parametrize('key',['schema','name','lower_left','upper_right','time'])
def test_missing_region(fixture_map,key):
    _,_,region=fixture_map
    del region[key]
    with pytest.raises(InvalidInput,match=key): region_config(region)


@pytest.mark.parametrize('crs,case',
    [(crs,case) for crs in ('wgs84','hk1980')
     for case in ('first','second','both','equal_first','equal_second','nan','inf')]
    + [('wgs84','range_latitude'),('wgs84','range_longitude')])
def test_corner_cli_no_writes(fixture_map,tmp_path,capsys,crs,case):
    _,machine,region=fixture_map
    region.update(crs=crs,lower_left=[22.2,114.0] if crs=='wgs84' else [800001,820001],
                  upper_right=[22.3,114.1] if crs=='wgs84' else [800002,820002])
    if case in ('first','both'): region['lower_left'][0],region['upper_right'][0]=region['upper_right'][0],region['lower_left'][0]
    if case in ('second','both'): region['lower_left'][1],region['upper_right'][1]=region['upper_right'][1],region['lower_left'][1]
    if case.startswith('equal'): region['lower_left'][0 if case=='equal_first' else 1]=region['upper_right'][0 if case=='equal_first' else 1]
    if case in ('nan','inf'): region['lower_left'][0]=float(case)
    if case.startswith('range_'):
        # HK1980 has finite/order checks, with no artificial geographic range.
        region['upper_right'][0 if case=='range_latitude' else 1]=91 if case=='range_latitude' else 181
    mp,rp=tmp_path/'machine.json',tmp_path/'region.json'
    mp.write_text(json.dumps(machine)); rp.write_text(json.dumps(region))
    before=listing(tmp_path)
    assert main(['run','--machine',str(mp),str(rp)])==2
    error=capsys.readouterr()
    assert not error.out and error.err.startswith('invalid input:')
    assert listing(tmp_path)==before


def test_correct_corners_and_projected_order(fixture_map):
    _,_,region=fixture_map
    assert region_config(region)
    region.update(crs='wgs84',lower_left=[22.2,114.0],upper_right=[22.3,114.1])
    assert region_config(region)
    with patch.object(adapter,'project_corner',side_effect=[(2,2),(1,3)]):
        with pytest.raises(InvalidInput,match='projected'): region_config(region)


@pytest.mark.parametrize('time',[
    dict(mode='window',dates=['2026-01-07'],start='13:00',end='12:00'),
    dict(mode='window',dates=['2026-01-07'],start='12:00',end='12:30',unknown=1),
    dict(mode='daylight',dates=['2026-01-07'],interval_minutes=0),
    dict(mode='daylight',dates=['2026-01-07'],interval_minutes=61),
    dict(mode='daylight',dates=['2026-01-07'],interval_minutes=True),
    dict(mode='daylight',dates=['2026-01-07','2026-01-07']),
    dict(mode='daylight',dates=['2026-02-30']),
    dict(mode='daylight',dates={'from':'2026-01-02','to':'2026-01-01'}),
    dict(mode='daylight',dates={'from':'2025-01-01','to':'2026-01-02'}),
    *[dict(mode='instants',instants=[s]) for s in ['2026-01-07T12:30:00','2026-01-07T12:30Z','2026-01-07T12:30+00:00','2026-01-07T25:00']],
    dict(mode='instants',instants=['2026-01-07T12:30','2026-01-07T12:30+08:00']),
])
def test_invalid_time(fixture_map,time):
    _,_,region=fixture_map; region['time']=time
    with pytest.raises(InvalidInput,match='time'): region_config(region)


def test_time_expansion(fixture_map):
    _,_,region=fixture_map
    region['time']=dict(mode='window',dates={'from':'2026-01-07','to':'2026-01-08'},start='12:00',end='12:20')
    normal=region_config(region)
    kept,dropped=expanded_time(normal['time'])
    assert len(kept['instants'])==6 and not dropped
    assert kept['instants'][2].startswith('2026-01-07T12:20')
    region['time'].update(start='12:00',end='12:00')
    assert len(expanded_time(region_config(region)['time'])[0]['instants'])==2
    region['time']=dict(mode='instants',instants=['2026-01-07T00:00','2026-01-07T12:30'])
    kept,dropped=expanded_time(region_config(region)['time'])
    assert len(kept['instants'])==1 and dropped[0]['reason']=='outside daylight'


@pytest.mark.parametrize('day',['2026-01-07','2026-06-21','2026-12-21'])
def test_daylight_equal_engine(fixture_map,day):
    raw,machine,region=fixture_map
    region['time']=dict(mode='daylight',dates=[day])
    result=prepare(region,machine)
    manual=v1.plan_shade(mode='custom',bounds=result.document['resolved_bounds'],dsm_dir=result.adapter_plan['sidecar']['source_directory'],
                         dates=[day],output_dir=v1.ROOT/'work/engine/manual')
    assert [f['utc_time'] for f in result.document['frames']]==[i.utc for i in manual.request.instants]
    assert len({f['date']+'/'+f['time'] for f in result.document['frames']})==len(result.document['frames'])


@pytest.mark.parametrize('corners',[
    ([800001.1,820001.1],[800003.2,820002.8]),
    ([800005.1,820003.1],[800007.1,820005.1]),
    ([800004.13,820002.17],[800008.32,820006.39]),
])
def test_plan_equivalence_read_only(fixture_map,tmp_path,corners):
    raw,machine,region=fixture_map
    region['lower_left'],region['upper_right']=corners
    before=listing(tmp_path)
    planned=prepare(region,machine)
    additions=set(listing(tmp_path))-set(before)
    assert all(p.startswith('work/source_views/') for p in additions)
    assert all(listing(tmp_path)[p]==value for p,value in before.items())
    batch=planned.adapter_plan['batches'][0]
    request=batch['requests'][0]
    direct=adapter.plan_region(*corners,crs='hk1980',instants=['2026-01-07T12:30:00+08:00'],
                              dsm_dir=raw,auto_source_view=True,
                              output_dir=Path(request['output_dir']).parent,
                              cache_dir=v1.ROOT/'data/cache/horizon/fixture_f1_hong_kong')
    assert direct['batches'][0]['requests']==batch['requests']
    assert [p['key'] for p in direct['sidecar']['partition']]==[p['key'] for p in planned.adapter_plan['sidecar']['partition']]
    check_document(planned.document,'plan')


def test_identity_machine_independent(fixture_map,tmp_path):
    raw,machine,region=fixture_map
    first=prepare(region,machine).document['run_id']
    copied=tmp_path/'catalogue_copy'; shutil.copytree(raw,copied)
    changed=dict(machine,dsm_dir=str(copied),workers=2,output_root='runs/other',cache_namespace='another')
    assert prepare(region,changed).document['run_id']==first
    altered=deepcopy(region); altered['lower_left'][0]+=.1
    assert prepare(altered,machine).document['run_id']!=first
    altered=deepcopy(region); altered['time']['instants']=['2026-01-07T12:31']
    assert prepare(altered,machine).document['run_id']!=first


def test_shifted_origin_rejected(fixture_map):
    raw,machine,region=fixture_map
    old=next(raw.glob('*.tif')); old.rename(raw/'14NE15A(shifted).tif')
    with pytest.raises(InvalidInput,match='pending shifted-origin DSM ingestion policy'): prepare(region,machine)


def test_guards_and_foreign_roots(fixture_map,tmp_path):
    _,machine,region=fixture_map
    before=listing(tmp_path)
    with pytest.raises(InvalidInput,match='max_output_bytes'): run_region(region,dict(machine,max_output_bytes=1))
    assert all(listing(tmp_path)[p]==v for p,v in before.items())
    assert not (tmp_path/'runs/published').exists()
    foreign=tmp_path/'foreign'; foreign.mkdir()
    assert prepare(region,dict(machine,output_root=str(foreign))).document['existing_run']['status']=='conflict'
    before=listing(tmp_path)
    with pytest.raises(InvalidInput,match='not created by F'): run_region(region,dict(machine,output_root=str(foreign)))
    assert before==listing(tmp_path)
    with pytest.raises(InvalidInput,match='data/'): machine_config(dict(machine,output_root='data/published'))


@pytest.mark.parametrize('action', ['plan', 'run', 'prune'])
@pytest.mark.parametrize('location', ['dsm', 'dsm_child', 'foreign', 'dsm_symlink',
                                      'foreign_symlink', 'data_symlink', 'provider', 'source_file',
                                      'malformed_marker'])
def test_repair_output_locations_rejected_before_writes(fixture_map, tmp_path, monkeypatch, capsys,
                                                       action, location):
    raw, machine, region = fixture_map
    repo = tmp_path/'repo'; repo.mkdir()
    monkeypatch.setattr(v1, 'ROOT', repo)
    foreign = tmp_path/'foreign'; foreign.mkdir()
    if location == 'malformed_marker': (foreign/'.shade_map_root.json').write_text('invalid JSON')
    data = repo/'data'; data.mkdir()
    alias = repo/'alias'
    if location in ('dsm_symlink', 'foreign_symlink', 'data_symlink'):
        alias.symlink_to({'dsm_symlink': raw, 'foreign_symlink': foreign,
                         'data_symlink': data}[location], target_is_directory=True)
        output = alias/'published'
    elif location in ('provider', 'source_file'):
        catalogue = tmp_path/'provider'; catalogue.mkdir()
        # Owned-parent markers cannot override the source-directory prohibition.
        (catalogue/'.shade_map_root.json').write_text('{"schema":"shade-map-root-1.0"}')
        if location == 'provider':
            monkeypatch.setattr(RawSource, 'catalogue', lambda self, machine: catalogue)
        else:
            (raw/'.shade_map_root.json').write_text('{"schema":"shade-map-root-1.0"}')
            for path in raw.glob('*.tif'): (catalogue/path.name).symlink_to(path)
            machine['dsm_dir'] = str(catalogue)
        output = (catalogue if location == 'provider' else raw)/'published'
    else:
        output = {'dsm': raw, 'dsm_child': raw/'published', 'foreign': foreign/'published',
                  'malformed_marker': foreign/'published'}[location]
    machine['output_root'] = str(output)
    mp, rp = tmp_path/'machine.json', tmp_path/'region.json'
    mp.write_text(json.dumps(machine)); rp.write_text(json.dumps(region))
    before = listing(tmp_path)
    paths_before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*'))
    with patch.object(adapter, 'plan_region', side_effect=AssertionError('adapter wrote before guard')):
        assert main([action, '--machine', str(mp), str(rp)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith('invalid input: output_root:') and not captured.out
    assert listing(tmp_path) == before
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*')) == paths_before


@pytest.mark.parametrize('contents', ['', 'unfinished'])
@pytest.mark.parametrize('final_state', ['verified', 'missing', 'corrupt'])
def test_repair_complete_run_discards_orphan_partial(fixture_map, tmp_path, contents, final_state):
    _, machine, region = fixture_map
    run_region(region, machine)
    folder = tmp_path/'runs/published/fixture'
    final = folder/'20260107/1230'
    before = listing(final)
    expected_files = read_json(final/'frame.json')['files']
    partial = final.with_name('1230.partial'); partial.mkdir()
    if contents: (partial/'interrupted.txt').write_text(contents)
    if final_state == 'missing': shutil.rmtree(final)
    elif final_state == 'corrupt': (final/'shade.tif').write_bytes(b'interrupted publication')
    with pytest.raises(RuntimeError, match='Partial publication remains'): verify_run(folder)
    result = run_region(region, machine)
    assert result['status'] == 'complete' and not list(folder.rglob('*.partial'))
    verify_run(folder)
    assert read_json(final/'frame.json')['files'] == expected_files
    if final_state == 'verified':
        assert result['verified_only'] and before == listing(final)


def test_full_publication_api_cli_resume_prune(fixture_map,tmp_path,capsys,monkeypatch):
    from shade_watch.city import profiles
    from shade_watch.fill.build import build

    _,machine,region=fixture_map
    city = dict(profiles.load_city('hong_kong'), extent=[800000,820000,800012,820008])
    profile_dir = tmp_path/'city_profiles'
    profile_dir.mkdir()
    (profile_dir/'hong_kong.json').write_text(json.dumps(city))
    monkeypatch.setattr(profiles, 'CITY_DIR', profile_dir)
    monkeypatch.setattr('shade_watch.fill.catalogue.DOMAIN_MARGIN_M', 2)
    view = build(machine)
    region.update(schema='shade-map-region-1.1', dsm_source='sea-2.2')
    mp=tmp_path/'machine.json'; mp.write_text(json.dumps(machine))
    assert prepare(region,machine).document['existing_run']['status']=='new'
    result=shade_map(region['lower_left'],region['upper_right'],region['time'],name=region['name'],crs='hk1980',machine=mp)
    assert result['published_frames']==1
    folder=tmp_path/'runs/published/fixture'
    manifest=verify_run(folder)
    assert prepare(region,machine).document['existing_run']['status']=='complete'
    assert manifest['region_config']['schema'] == 'shade-map-region-1.1'
    assert manifest['region_config']['dsm_source'] == 'sea-2.2'
    assert manifest['source_identity']['view_id'] == view['view_id']
    synthetic = [c for c in manifest['cells'] if c['source_tile'].startswith('FILL_')]
    assert len(manifest['cells']) == 4 and len(synthetic) == 1
    with rasterio.open(folder/'20260107/1230/surface'/(synthetic[0]['id']+'.tif')) as ds:
        assert np.all(np.isin(ds.read(1), [2, 3, 4]))
    for layer in ('shade','quality','surface'):
        with rasterio.open(folder/'20260107/1230'/f'{layer}.vrt') as ds:
            expected=ds.read(1)
        copied=tmp_path/'portable'/region['name']
        if not copied.exists(): shutil.copytree(folder,copied)
        with rasterio.open(copied/'20260107/1230'/f'{layer}.vrt') as ds:
            assert np.array_equal(expected,ds.read(1))
    summary=read_json(folder/'summary.json')
    for item in summary['frames'][0]['surfaces']:
        assert sum(item['counts'].values())==item['pixels']
        assert sum(item['quality_counts'].values())==item['pixels']
        for k,count in item['counts'].items(): assert item['fractions'][k]==count/item['pixels']
    before=listing(tmp_path)
    assert main(['run','--machine',str(mp),str(folder/'region_config.json')])==0
    assert json.loads(capsys.readouterr().out)['verified_only']
    assert before==listing(tmp_path)
    conflict=deepcopy(region); conflict['upper_right'][0]+=.1
    assert prepare(conflict,machine).document['existing_run']['status']=='conflict'
    before=listing(tmp_path)
    with pytest.raises(InvalidInput,match='different region'): run_region(conflict,machine)
    assert before==listing(tmp_path)
    work=tmp_path/'work/runs'/('fixture-'+manifest['run_id'][:12])
    dry=prune_region(region,machine)
    assert dry['bytes']>0 and work.exists()
    assert prune_region(region,machine,yes=True)['deleted'] and not work.exists()
    after=listing(tmp_path)
    assert run_region(region,machine)['verified_only'] and not work.exists()
    assert after==listing(tmp_path)


def test_source_interface_surface_one(fixture_map,monkeypatch):
    _,machine,region=fixture_map
    class FixtureSource(RawSource):
        def source_identity(self,records): return dict(super().source_identity(records),provider='fixture-source')
        def read_surface(self,bounds,records):
            values=super().read_surface(bounds,records); values[values==0]=1; return values
    monkeypatch.setitem(PROVIDERS,'raw',FixtureSource())
    region['name']='provider'; region['full_image']='never'
    run_region(region,machine)
    folder=v1.ROOT/'runs/published/provider'
    frame=read_json(folder/'20260107/1230/frame.json')
    assert frame['value_counts']['surface'].get('1',0)>0
    assert frame['value_counts']['surface'].get('0',0)==0
    assert not (folder/'20260107/1230/surface.tif').exists()


def test_lock_and_incomplete_prune(fixture_map):
    from shade_watch.publish.common import name_lock
    _,machine,region=fixture_map
    planned=prepare(region,machine)
    with name_lock(v1.ROOT/'work/locks',region['name']):
        with pytest.raises(InvalidInput,match='another run'): run_region(region,machine)
    run_region(region,machine)
    path=planned.folder/'run_manifest.json'
    manifest=read_json(path); manifest['status']='incomplete'
    path.write_text(json.dumps(seal(manifest)))
    assert prepare(region,machine).document['existing_run']['status']=='resumable'
    with pytest.raises(InvalidInput,match='every frame'): prune_region(region,machine,yes=True)


def test_all_night_empty_run_and_missing_machine_keys(fixture_map):
    _,machine,region=fixture_map
    for key in ('schema','dsm_dir'):
        broken=dict(machine); del broken[key]
        with pytest.raises(InvalidInput,match=key): machine_config(broken)
    region['time']=dict(mode='instants',instants=['2026-01-07T00:00'])
    plan=prepare(region,machine).document
    assert not plan['frames'] and plan['dropped_times'][0]['reason']=='outside daylight'
    with patch.object(v2,'submit_batch',side_effect=AssertionError('night was computed')):
        result=run_region(region,machine)
    assert result['published_frames']==0
    assert read_json(v1.ROOT/'runs/published/fixture/summary.json')['frames']==[]


def test_more_than_one_explicit_engine_request(fixture_map):
    _,machine,region=fixture_map
    # Daylight window exceeds MAX_FRAMES but each emitted engine request does not.
    region['time']=dict(mode='window',dates=['2026-01-07'],start='07:10',end='17:50',interval_minutes=1)
    prepared=prepare(region,machine)
    assert len(prepared.document['frames'])==641
    assert len(prepared.adapter_plan['sidecar']['time_groups'])==2
    assert all(len(group['utc_times'])<=v1.MAX_FRAMES for group in prepared.adapter_plan['sidecar']['time_groups'])
    assert all(request['id'] in prepared.adapter_plan['sidecar']['generated_request_ids']
               for request in prepared.adapter_plan['sidecar']['requests'])


def test_bad_calendar_and_nested_date_rules(fixture_map):
    _,_,region=fixture_map
    for dates in [[],['2026-01-07']*367,{'from':'2026-01-07'},
                  {'from':'2026-01-07','to':'2026-01-08','extra':1},'2026-01-07']:
        region['time']=dict(mode='daylight',dates=dates)
        with pytest.raises(InvalidInput,match='dates'): region_config(region)
    region['time']=dict(mode='instants',instants=['2026-02-30T12:30'])
    with pytest.raises(InvalidInput,match='instants'): region_config(region)


def test_native_dsm_observed_classes(fixture_map):
    raw,_,_=fixture_map
    records=v1.index_sources(raw)
    surface=RawSource().read_surface([800000,820000,800006,820004],records)
    assert surface[0,0]==255 and surface[0,1]==255
    assert np.all(surface[1:]==0)
    missing=RawSource().read_surface([800006,820004,800012,820008],records)
    assert np.all(missing==255)


def test_changed_source_conflict_does_not_create_view(fixture_map,tmp_path):
    raw,machine,region=fixture_map
    run_region(region,machine)
    source=next(raw.glob('*.tif'))
    with rasterio.open(source,'r+') as ds:
        data=ds.read(1); data[-1,-1]+=1; ds.write(data,1)
    before=listing(tmp_path)
    with pytest.raises(InvalidInput,match='different source'): run_region(region,machine)
    assert before==listing(tmp_path)


def test_existing_name_lock_precedes_catalogue_reads(fixture_map):
    from shade_watch.publish.common import name_lock
    _,machine,region=fixture_map
    run_region(region,machine)
    with name_lock(v1.ROOT/'work/locks',region['name']):
        with patch.object(RawSource,'preview_identity',side_effect=AssertionError('catalogue read before lock')):
            with pytest.raises(InvalidInput,match='another run'): run_region(region,machine)


def test_historical_explicit_clocks_are_fixed_utc8(fixture_map):
    _,machine,region=fixture_map
    region['time']=dict(mode='instants',instants=['1973-06-21T12:30'])
    frame=prepare(region,machine).document['frames'][0]
    assert frame['local_time']=='1973-06-21T12:30:00+08:00'
    assert frame['utc_time']=='1973-06-21T04:30:00+00:00'


def test_recover_renamed_frame_and_discard_partial(fixture_map,tmp_path):
    _,machine,region=fixture_map
    run_region(region,machine)
    folder=tmp_path/'runs/published/fixture'
    frame=folder/'20260107/1230'
    before=listing(frame)
    manifest=read_json(folder/'run_manifest.json')
    # Simulate death after rename, before the manifest transaction.
    manifest['status']='incomplete'
    manifest['frames'][0]['status']='pending'
    manifest['frames'][0]['files']={}
    (folder/'run_manifest.json').write_text(json.dumps(seal(manifest)))
    partial=folder/'20260107/1230.partial'; partial.mkdir()
    (partial/'unfinished.txt').write_text('interrupted')
    result=run_region(region,machine)
    assert result['reused_frames']==1 and not partial.exists()
    assert before==listing(frame)
    final=verify_run(folder)
    assert final['publication_events'][-1]['action']=='recovered'
    assert final['engine_events'][-1]['action']=='verify'


@pytest.mark.parametrize('bad',[None,42])
def test_api_invalid_corner_uses_config_validator(fixture_map,bad):
    _,machine,region=fixture_map
    with pytest.raises(InvalidInput,match='lower_left'):
        plan_shade_map(bad,region['upper_right'],region['time'],name='bad_api',crs='hk1980',machine=machine)
