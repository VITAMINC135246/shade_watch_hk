"""Tools-environment geometric check of sampled mask disagreements."""
import json
from pathlib import Path
from shapely.geometry import shape,Point


def run(root):
    root=Path(root)
    vector=json.loads((root/'data/processed/coastline/ib5000_20261012/coastline.geojson').read_text())
    evidence=root/'docs/sea/evidence/edge-diagnostic.json'
    report=json.loads(evidence.read_text())
    features=[(f['properties']['code'],f['bbox'],shape(f['geometry'])) for f in vector['features']]
    for sample in report['samples']:
        x,y=sample['x'],sample['y'];point=Point(x,y)
        states={};distances=[]
        for code in ('LAF','SEF'):
            relevant=[geom for c,b,geom in features if c==code and b[0]-.5<=x<=b[2]+.5 and b[1]-.5<=y<=b[3]+.5]
            states[code]=any(g.contains(point) for g in relevant)
            if code=='LAF': distances=[g.boundary.distance(point) for g in relevant]
        sample['geometric_land']=states['LAF']
        sample['geometric_sea']=states['SEF'] and not states['LAF']
        sample['nearest_land_boundary_m']=min(distances) if distances else None
        sample['rasterio_matches_geometry']=(sample['rasterio_land']==sample['geometric_land'] and sample['rasterio_sea']==sample['geometric_sea'])
    result=dict(samples=report['samples'],all_sample_centres_agree=all(s['rasterio_matches_geometry'] for s in report['samples']),
                note='Independent Shapely point containment on standard-reader polygons; PIL edge burn is diagnostic and is not the policy. Exact original planning renderer is unavailable; the PIL comparison explains edge inclusion mechanism rather than claiming exact reproduction.')
    (root/'docs/sea/evidence/edge-point-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('samples',len(result['samples']),'all centre checks agree',result['all_sample_centres_agree'])
    assert result['all_sample_centres_agree']


if __name__=='__main__': run(Path(__file__).resolve().parents[2])
