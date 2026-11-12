"""Read-only checks of the completed B2.2 view, publications and diagnostics."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
import numpy as np
import rasterio

from tools.sea2 import VIEW_NAMESPACE, POLICY
from tools.sea2.build import assert_fill, build_code_hashes
from tools.sea2.catalogue import Catalogue, DOMAIN_MARGIN_M
from tools.sea2.checks import EvidenceRun, RawCounterfactual, compare, layer, publication_counts, rays
from tools.sea2.rule import CODES, counts, missing
from tools.sea2.view import read_manifest
from tools.shade_map.common import atomic_json, digest, identity, read_json
from tools.shade_map.config import validate_schema


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[3]
MACHINE = read_json(EVIDENCE/'configs/machine.json')
OUTPUT = ROOT/MACHINE['output_root']
RAW = ROOT/MACHINE['dsm_dir']


def audit_view(view, doc):
    catalogue = Catalogue(RAW)
    expected = {key:catalogue.name(key) for key in catalogue.keys()}
    actual = {tuple(c['key']):c['id'] for c in doc['cells']}
    assert len(expected)==len(doc['cells'])==len(doc['tiles']) and actual==expected
    assert doc['grid']['domain_bounds']==catalogue.bounds((
        catalogue.domain[0], catalogue.domain[1],
        catalogue.domain[2]-catalogue.domain[0],catalogue.domain[3]-catalogue.domain[1]))
    records = {t['cell']:t for t in doc['tiles']}
    territory = Counter()
    derived = synthetic = linked = partial = 0
    overlaps = []
    exception_tiles = []
    fill_bits = np.float32(doc['profile']['h_sea_m']).view(np.uint32)
    for i, cell in enumerate(doc['cells']):
        key = tuple(cell['key'])
        name = cell['id']
        record = records[name]
        surface_file = view/'surface'/cell['surface_name']
        tile_file = view/'tiles'/record['name']
        assert digest(surface_file)==cell['surface_sha256']
        with rasterio.open(surface_file) as ds:
            assert ds.nodata==255 and ds.dtypes==('uint8',) and list(ds.bounds)==cell['bounds']
            surface = ds.read(1)
        actual_counts = counts(surface)
        assert actual_counts==cell['counts']==record['counts']
        assert actual_counts['255']==0 and sum(actual_counts.values())==surface.size
        territory.update(actual_counts)
        raw = catalogue.tiles.get(key)
        assert cell['tile_name']==record['name'] and record['output_sha256']==cell['output_sha256']
        assert record['synthetic']==cell['synthetic']==(raw is None)
        assert cell['supplied']==(raw is not None)
        if raw is not None:
            source = RAW/raw['name']
            assert record['name']==raw['name'] and record['source_sha256']==doc['catalogue']['files'][raw['name']]
            if tile_file.is_symlink():
                assert tile_file.resolve()==source.resolve()
                assert record['source_sha256']==record['output_sha256']
                with rasterio.open(source) as ds:
                    assert not missing(ds.read(1)).any()
                assert actual_counts['0']==surface.size
                linked += 1
            else:
                assert digest(tile_file)==record['output_sha256']
                assert_fill(source,tile_file,surface,doc['profile']['h_sea_m'])
                derived += 1
            if raw['name'].split('(')[0] in ('14NE15A','14NE15B','14NE15C','14NE15D'):
                assert tile_file.is_symlink() and actual_counts['0']==surface.size
                exception_tiles.append(raw['name'])
        else:
            assert record['name']=='FILL_'+name+'.tif' and record['source_sha256'] is None
            assert not tile_file.is_symlink() and digest(tile_file)==record['output_sha256']
            full = catalogue.window(key,clip=False)
            x,y,w,h = catalogue.window(key)
            with rasterio.open(tile_file) as ds:
                assert ds.transform==catalogue.transform(full) and list(ds.bounds)==cell['native_bounds']
                assert ds.crs.to_string()==catalogue.crs and ds.nodata==-9999 and ds.dtypes==('float32',)
                assert ds.shape==(catalogue.height,catalogue.width)
                data = ds.read(1)
            row, col = full[1]+full[3]-y-h, x-full[0]
            inside = np.zeros(data.shape,bool)
            inside[row:row+h,col:col+w] = True
            assert not actual_counts['0'] and not actual_counts['1']
            assert np.all(data.view(np.uint32)[inside]==fill_bits) and np.all(data[~inside]==-9999)
            synthetic += 1
            partial += int(not inside.all())
            # A strict continuous footprint check also records subpixel drift
            # beside literal-definition exceptions, separately from lattice overlap.
            l,b,r,t = cell['native_bounds']
            for j in range(key[1]-1,key[1]+2):
                for k in range(key[0]-1,key[0]+2):
                    neighbor = catalogue.tiles.get((k,j))
                    if neighbor is None:
                        continue
                    nl,nb,nr,nt = neighbor['bounds']
                    dw,dh = min(r,nr)-max(l,nl),min(t,nt)-max(b,nb)
                    if dw>0 and dh>0:
                        overlaps.append(dict(synthetic=name,supplied=neighbor['name'],width_m=dw,height_m=dh))
        if i%500==0:
            print(f'View readback {i+1}/{len(expected)}',flush=True)
    for name, sha in doc['auxiliary_outputs'].items():
        assert digest(view/'tiles'/name)==sha
    assert dict(territory)==doc['totals']
    assert sorted(exception_tiles)==sorted(t['name'] for t in doc['literal_definition_exceptions'])
    assert doc['build_code_sha256']==build_code_hashes()
    assert doc['catalogue']['identity']==identity(doc['catalogue']['files'])
    assert doc['profile_sha256']==identity(doc['profile'])
    return dict(view_id=doc['view_id'],manifest_sha256=digest(view/'manifest.json'),
                verified_derived=derived,verified_synthetic=synthetic,verified_links=linked,partial_synthetic=partial,
                totals=dict(territory),literal_definition_exceptions=doc['literal_definition_exceptions'],
                exact_native_cell_inventory=True,strict_bbox_overlaps=overlaps,
                domain_margin_m=DOMAIN_MARGIN_M,grid=doc['grid'],build_code_sha256=doc['build_code_sha256'],
                catalogue_identity=doc['catalogue']['identity'],catalogue_files=len(doc['catalogue']['files']),
                versions=doc['versions'],view_pointer_inventory_count=len(read_json(view.parent/'current-hk_cedd_2020.json')['header_inventory']))


def diagnostic_work(run):
    report_path = OUTPUT/'_diagnostics/fill_impact'/run.manifest['name']/'fill_impact.json'
    report = read_json(report_path)
    work = ROOT/'outputs/sea2_2_diagnostic_work'/(run.manifest['name']+'-'+report['counterfactual_id'][:12])
    return report_path, report, work


def audit_diagnostic(run, doc):
    report_path, report, work = diagnostic_work(run)
    validate_schema(report,read_json(ROOT/'config/schema/fill_impact.schema.json'))
    cf = RawCounterfactual(work)
    raw_view = read_json(Path(cf.sidecar['source_directory'])/'source_view.json')
    assert Path(raw_view['catalogue'])==RAW.resolve()
    assert report['counterfactual_id']==cf.run_id
    assert report['raw_catalogue_sha256']==doc['catalogue']['identity']
    assert report['policy_run_id']==run.run_id
    checked = []
    for frame in report['frames']:
        prefix = report_path.parent/frame['date']/frame['time']
        metrics = {name:Counter() for name in ('land','water','other')}
        transitions = Counter()
        raster_hashes = {}
        with rasterio.open(prefix/'dependency.vrt') as vrt:
            assert vrt.nodata==255 and list(vrt.bounds)==run.bounds
            for cell in run.manifest['cells']:
                surface = layer(run.folder,frame,cell,'surface')
                filled, fq = run.layers(frame,cell)
                raw, rq = cf.layers(frame,cell)
                # Evaluate the documented precedence independently of fill_impact.
                reference = np.select(
                    [surface==255,filled==255,surface!=0,raw==filled,raw==255],
                    [255,4,3,0,1],default=2).astype(np.uint8)
                path = prefix/'dependency'/(cell['id']+'.tif')
                with rasterio.open(path) as ds:
                    pixels = ds.read(1)
                    assert ds.nodata==255 and list(ds.bounds)==cell['bounds']
                    assert np.array_equal(pixels,reference)
                    assert np.array_equal(vrt.read(1,window=vrt.window(*cell['bounds'])),reference)
                raster_hashes[cell['id']] = digest(path)
                for name, classes in [('land',(0,3)),('water',(1,2)),('other',(4,))]:
                    mask = np.isin(surface,classes)
                    metrics[name].update({str(code):int(np.count_nonzero(mask & (pixels==code))) for code in range(5)})
                observed = surface==0
                for a, aq in [(0,0),(1,0),(255,1),(255,2),(255,3),(255,4)]:
                    selected = observed & (raw==a) & (rq==aq)
                    if not selected.any():
                        continue
                    for b, bq in [(0,0),(1,0),(255,1),(255,2),(255,3),(255,4)]:
                        n = int(np.count_nonzero(selected & (filled==b) & (fq==bq)))
                        if n:
                            transitions[(a,aq,b,bq)] += n
        for name, group in frame['groups'].items():
            assert group['counts']==metrics[name] and group['pixels']==sum(metrics[name].values())
            if 'fractions' in group:
                assert group['fractions']=={k:n/group['pixels'] if group['pixels'] else 0. for k,n in metrics[name].items()}
        land = frame['groups']['land']
        assert frame['fill_dependent_land']==(sum(metrics['land'][str(k)] for k in (1,2,3))/land['pixels'] if land['pixels'] else 0.)
        actual = {(r['raw_shade'],r['raw_quality'],r['filled_shade'],r['filled_quality']):r['pixels']
                  for r in frame['observed_transitions']}
        assert actual==transitions
        checked.append(dict(time=frame['time'],raster_hashes=raster_hashes,group_counts=metrics,
                            fill_dependent_land=frame['fill_dependent_land']))
    publication = read_json(work/'publication-integrity.json')
    assert publication['before_sha256']==publication['after_sha256']
    assert publication['sealed_manifest_sha256']==digest(run.folder/'run_manifest.json')
    return dict(counterfactual_source=raw_view['catalogue'],counterfactual_id=cf.run_id,
                report_sha256=digest(report_path), report_path=str(report_path),
                schema_valid=True, checked_frames=checked, publication_integrity=publication,
                v2_events=read_json(work/'execution.json'))


def audit_run(name, view, doc):
    region = read_json(EVIDENCE/'configs'/(name+'.json'))
    run = EvidenceRun(OUTPUT/region['name'])
    manifest = run.manifest
    assert manifest['policies']==dict(engine='SW-V1-POLICY-1.0',sea=POLICY)
    assert manifest['source_identity']['view_id']==doc['view_id']
    root = ROOT/'outputs/shade_map_work'/(manifest['name']+'-'+run.run_id[:12])
    adapter_path = root/'adapter/region_request.json'
    assert digest(adapter_path)==manifest['adapter_sidecar_sha256']
    sidecar = read_json(adapter_path)
    plan = read_json(EVIDENCE/(name+'-plan.txt'))
    assert run.run_id==plan['run_id']
    reference_folder = {
        'cheung_chau': ROOT/'outputs/shade_map_f1_20261031/f1_cheung_chau',
        'central': ROOT/'outputs/sea2_f_20261104/sea2_central_raw',
    }
    if name in reference_folder:
        raw = EvidenceRun(reference_folder[name])
    else:
        _, _, work = diagnostic_work(run)
        raw = RawCounterfactual(work)
    actual = publication_counts(run,view)
    result = compare(raw,run,view)
    first_old = {s['source_name']:s['spatial_key'] for s in raw.solar(raw.frames[0])}
    first_new = {s['source_name']:s['spatial_key'] for s in run.solar(run.frames[0])}
    provenance = dict(policies=manifest['policies'], source=manifest['source_identity']['provider'],
                      adapter_sidecar_sha256=manifest['adapter_sidecar_sha256'],
                      raw_spatial_keys=first_old,sea_spatial_keys=first_new,
                      v1_request_keys=[r['key'] for r in sidecar['requests']],
                      request_local_source_directory=sidecar['source_directory'],
                      cache_namespace=VIEW_NAMESPACE+'_'+doc['view_id'][:12],
                      files=len(manifest['files']),manifest_sha256=digest(run.folder/'run_manifest.json'))
    atomic_json(EVIDENCE/(name+'-publication.json'),dict(**actual,provenance=provenance))
    atomic_json(EVIDENCE/(name+'-regression.json'),result)
    if name!='central':
        atomic_json(EVIDENCE/(name+'-rays.json'),rays(run,view,water=name=='cheung_chau'))
        atomic_json(EVIDENCE/(name+'-fill-impact-audit.json'),audit_diagnostic(run,doc))
    print(name, len(run.frames), 'frames', 'quality gate',actual['missing_data_check'],
          'observed guard',result['passed'],flush=True)


def audit_request_keys(doc):
    def f_requests(folder):
        run = read_json(folder/'run_manifest.json')
        path = ROOT/'outputs/shade_map_work'/(run['name']+'-'+run['run_id'][:12])/'adapter/region_request.json'
        assert digest(path)==run['adapter_sidecar_sha256']
        return read_json(path)['requests']

    def keys(requests):
        return [row['key'] for row in requests]

    result = {}
    for name, reference in [('cheung_chau','shade_map_f1_20261031/f1_cheung_chau'),
                            ('central','sea2_f_20261104/sea2_central_raw'),
                            ('five_class',None)]:
        target = OUTPUT/('sea2_2_'+name)
        sea = keys(f_requests(target))
        if reference is None:
            run = read_json(target/'run_manifest.json')
            impact = read_json(OUTPUT/'_diagnostics/fill_impact'/run['name']/'fill_impact.json')
            work = ROOT/'outputs/sea2_2_diagnostic_work'/(run['name']+'-'+impact['counterfactual_id'][:12])
            raw = keys(read_json(work/'counterfactual.json')['sidecar']['requests'])
        else:
            raw = keys(f_requests(ROOT/'outputs'/reference))
        result[name] = dict(raw=raw,sea=sea,disjoint=set(raw).isdisjoint(sea))
    return dict(view_id=doc['view_id'],checks=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check',choices=['view','keys','cheung_chau','central','five_class'])
    args = parser.parse_args()
    preflight = read_json(EVIDENCE/'view-preflight.json')
    view = Path(preflight['view'])
    doc = read_manifest(view)
    if args.check=='view':
        result = audit_view(view,doc)
        atomic_json(EVIDENCE/'view-readback.json',result)
        print(json_summary(result),flush=True)
    elif args.check=='keys':
        atomic_json(EVIDENCE/'request-plan-keys.json',audit_request_keys(doc))
    else:
        audit_run(args.check,view,doc)


def json_summary(result):
    return {k:result[k] for k in ('verified_derived','verified_synthetic','verified_links',
                                 'strict_bbox_overlaps','totals')}


if __name__=='__main__':
    main()
