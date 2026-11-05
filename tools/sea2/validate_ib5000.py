"""Report-only iB5000 reader. Run in the separate requirements.tools.lock environment.

Vector reading/repair/clipping occurs here. Raster operations run in the pinned
engine interpreter as a measured child; no vector reader is installed there.
"""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')


def require_reader_versions(version=None):
    version=version or importlib.metadata.version
    root=Path(__file__).resolve().parents[2]
    expected={line.split('==')[0]:line.split('==')[1] for line in (root/'requirements.tools.lock.txt').read_text().splitlines() if '==' in line}
    actual={}
    for name in expected:
        try:actual[name]=version(name)
        except importlib.metadata.PackageNotFoundError:actual[name]=None
    if actual!=expected:
        raise RuntimeError('separate tools reader unavailable or not pinned; expected '+str(expected)+'; found '+str(actual))
    return actual


def export_cells(view,destination,source,dictionary):
    import numpy as np
    import pyogrio
    from pyogrio.raw import read
    import shapely
    from shapely.geometry import mapping, box
    from shapely.strtree import STRtree
    root=Path(__file__).resolve().parents[2]
    # Reuse the unchanged deterministic polygon repair from B1, not its water policy.
    sys.path.insert(0,str(root))
    from tools.sea_view.extract import polygonal
    info=pyogrio.read_info(source,layer='HydrographyPoly',force_feature_count=True)
    meta,fids,wkb,attrs=read(source,layer='HydrographyPoly',
            where="FEATURESUBTYPE = 3 AND DATASTATUS = 'E'",
            columns=['FEATURESUBTYPE','FEATURECODE','DATASTATUS'],return_fids=True)
    fields=dict(zip(meta['fields'],attrs)); counts=Counter(map(str,fields['FEATURECODE']))
    if info['features']!=7116 or counts!={'LAF':1111,'SEF':345}:
        raise ValueError('iB5000 standard-reader counts differ from the frozen reference: '+str(counts))
    geoms=[]; codes=[]; repairs=[]
    for fid,code,blob in sorted(zip(fids,fields['FEATURECODE'],wkb),key=lambda r:int(r[0])):
        geom=shapely.from_wkb(blob)
        if geom is None or geom.is_empty: raise ValueError('Empty iB5000 geometry')
        if not shapely.is_valid(geom):
            geom=polygonal(shapely.make_valid(geom))
            repairs.append(dict(fid=int(fid),method='GEOS make_valid, polygon members',wkb_sha256=hashlib.sha256(shapely.to_wkb(geom)).hexdigest()))
        if geom.is_empty or not shapely.is_valid(geom): raise ValueError('Invalid repaired iB5000 geometry')
        geoms.append(geom); codes.append(str(code))
    if '2326' not in meta['crs'] and 'Hong_Kong_1980' not in meta['crs']:
        raise ValueError('Unexpected map CRS')
    destination.mkdir(parents=True,exist_ok=False)
    tree=STRtree(geoms); cells=json.loads((view/'manifest.json').read_text())['cells']; files={}
    for i,cell in enumerate(cells):
        rectangle=box(*cell['bounds']); features=[]
        for k in sorted(tree.query(rectangle)):
            geometry=polygonal(geoms[k].intersection(rectangle))
            if not geometry.is_empty:
                features.append(dict(code=codes[k],geometry=mapping(geometry)))
        name=cell['id']+'.json'; write(destination/name,features); files[name]=sha(destination/name)
        if i%500==0: print(f'iB5000 vector clipping: {i+1}/{len(cells)}',file=sys.stderr,flush=True)
    bounds=[min(g.bounds[0] for g in geoms),min(g.bounds[1] for g in geoms),max(g.bounds[2] for g in geoms),max(g.bounds[3] for g in geoms)]
    environment=dict(python=sys.version,executable=sys.executable,
                     packages={n:importlib.metadata.version(n) for n in ['numpy','pyogrio','shapely','certifi','packaging']},
                     gdal=pyogrio.__gdal_version_string__,geos=shapely.geos_version_string,
                     lock_sha256=sha(root/'requirements.tools.lock.txt'))
    manifest=dict(schema='sea2-ib5000-vector-report-1.0',report_only=True,reader='pyogrio/OpenFileGDB',
                  filter="FEATURESUBTYPE = 3 AND DATASTATUS = 'E'",counts=dict(counts),total_features=info['features'],
                  crs=meta['crs'],coverage_bbox=bounds,repairs=repairs,environment=environment,
                  source_hashes={p.name:sha(p) for p in sorted(source.iterdir()) if p.is_file()},
                  dictionary_sha256=sha(dictionary),view_id=json.loads((view/'manifest.json').read_text())['view_id'],cell_files=files)
    write(destination/'manifest.json',manifest)
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--machine',required=True)
    p.add_argument('--work',default='outputs/sea2_validation_20261104')
    p.add_argument('--scopes',required=True,help='JSON mapping of scope names to target bounds')
    args=p.parse_args(argv)
    require_reader_versions()
    root=Path(__file__).resolve().parents[2]
    machine=json.loads((root/args.machine).read_text())
    profile=machine.get('sea_profile','hk_cedd_2020')
    pointer=json.loads((root/f'data/processed/dsm_views/sea_fill_v2/current-{profile}.json').read_text())
    view=root/'data/processed/dsm_views/sea_fill_v2'/pointer['view_id']
    work=(root/args.work).resolve()
    if not work.is_relative_to(root/'outputs') or work.is_symlink(): raise ValueError('Validation work must be a new repository outputs namespace')
    vectors=work/'map_cells'
    source=root/'data/raw/coastline/ib5000_seamless_20261012/iB5000.gdb'
    dictionary=root/'data/raw/coastline/resources_iB5000_FGDB/iB5000 Data Dictionary - FGDB v1.3.pdf'
    if vectors.exists():
        provenance=json.loads((vectors/'manifest.json').read_text())
        if provenance['view_id']!=pointer['view_id']: raise ValueError('Validation work belongs to a different sea view')
    else:
        provenance=export_cells(view,vectors,source,dictionary)
    report=root/'docs/sea2/evidence/ib5000-reader.json'; report.parent.mkdir(parents=True,exist_ok=True)
    write(report,{k:v for k,v in provenance.items() if k not in ('cell_files','source_hashes')} |
          dict(source_files=len(provenance['source_hashes']),source_identity_sha256=hashlib.sha256(json.dumps(provenance['source_hashes'],sort_keys=True).encode()).hexdigest()))
    return subprocess.call([str(root/'.venv/bin/python'),'-m','tools.sea2.validation_worker',
                            '--view',str(view),'--maps',str(vectors),'--scopes',str(root/args.scopes),
                            '--machine',str(root/args.machine),'--work',str(work)],cwd=root)


if __name__=='__main__':
    try:sys.exit(main())
    except RuntimeError as exc:
        print('validation NOT VERIFIED: '+str(exc),file=sys.stderr);sys.exit(2)
