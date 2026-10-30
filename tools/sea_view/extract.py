"""Extract frozen iB5000 sea/land polygons using standard OpenFileGDB only.

Run with the external tools environment, never the engine .venv.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def polygonal(geometry):
    """Deterministically retain polygon members after make_valid."""
    from shapely.geometry import MultiPolygon
    if geometry.geom_type in ('Polygon','MultiPolygon'):
        return geometry
    parts=[]
    for child in getattr(geometry,'geoms',[]):
        value=polygonal(child)
        if value.geom_type=='Polygon': parts.append(value)
        elif value.geom_type=='MultiPolygon': parts.extend(value.geoms)
    return MultiPolygon(parts)


def extract(source,dictionary,destination):
    import numpy as np
    import pyogrio
    from pyogrio.raw import read
    import shapely
    from shapely.geometry import mapping
    source,dictionary,destination=map(Path,(source,dictionary,destination))
    if destination.exists(): raise ValueError('Extraction destination already exists; no overwrite')
    info=pyogrio.read_info(source,layer='HydrographyPoly',force_feature_count=True)
    meta,fids,wkb,attributes=read(source,layer='HydrographyPoly',
                                where="FEATURESUBTYPE = 3 AND DATASTATUS = 'E'",
                                columns=['FEATURESUBTYPE','FEATURECODE','DATASTATUS'],return_fids=True)
    fields=dict(zip(meta['fields'],attributes))
    counts=Counter(map(str,fields['FEATURECODE']))
    if info['features']!=7116 or counts!={'LAF':1111,'SEF':345}:
        raise ValueError(f'S02 count gate failed: total={info["features"]}; filtered={dict(counts)}')
    # Pyogrio resolves the authoritative layer CRS; engine CRS equivalence is
    # independently checked by rasterio before any rasterization.
    if not meta.get('crs'): raise ValueError('Map has no CRS')
    features,invalid=[],[]
    for fid,code,blob in sorted(zip(fids,fields['FEATURECODE'],wkb),key=lambda r:int(r[0])):
        geom=shapely.from_wkb(blob)
        if geom is None or geom.is_empty: raise ValueError(f'Empty geometry at FID {fid}')
        if not shapely.is_valid(geom):
            reason=shapely.is_valid_reason(geom)
            geom=polygonal(shapely.make_valid(geom))
            invalid.append(dict(fid=int(fid),reason=reason,method='GEOS make_valid; retain polygon members',
                                repaired_wkb_sha256=hashlib.sha256(shapely.to_wkb(geom)).hexdigest()))
        if geom.is_empty or not shapely.is_valid(geom) or geom.geom_type not in ('Polygon','MultiPolygon'):
            raise ValueError(f'Geometry remains invalid/nonpolygonal at FID {fid}')
        features.append(dict(type='Feature',id=int(fid),properties=dict(code=str(code)),
                             bbox=list(geom.bounds),geometry=mapping(geom)))
    vector=dict(type='FeatureCollection',crs=dict(type='name',properties=dict(name=meta['crs'])),features=features)
    manifest=dict(schema='shade-watch-sea-map-1.0',policy='SW-SEA-POLICY-1.0',
                  source_directory=str(source.resolve()),source_hash_scope='all FGDB files, conservative superset of reader dependencies',
                  source_hashes={p.name:digest(p) for p in sorted(source.iterdir()) if p.is_file()},
                  dictionary_sha256=digest(dictionary),reader='pyogrio/OpenFileGDB',
                  versions=dict(python=sys.version,pyogrio=pyogrio.__version__,gdal=pyogrio.__gdal_version_string__,
                                shapely=shapely.__version__,geos=shapely.geos_version_string,numpy=np.__version__),
                  crs=meta['crs'],total_features=info['features'],counts=dict(counts),invalid_geometries=invalid,
                  filter="FEATURESUBTYPE = 3 AND DATASTATUS = 'E'",vector_file='coastline.geojson')
    destination.mkdir(parents=True,exist_ok=False)
    path=destination/'coastline.geojson'
    path.write_text(json.dumps(vector,separators=(',',':'),allow_nan=False)+'\n')
    manifest['vector_sha256']=digest(path)
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    return manifest


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True)
    p.add_argument('--dictionary',required=True)
    p.add_argument('--destination',required=True)
    a=p.parse_args()
    print(json.dumps(extract(a.source,a.dictionary,a.destination),indent=2))
