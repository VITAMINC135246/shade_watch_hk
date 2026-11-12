"""Pixel-centre map comparisons and class-3 components for the report-only reader."""
from __future__ import annotations

import argparse
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from scipy import ndimage

from shade_watch.engine.spatial import intersects
from shade_watch.publish.common import atomic_json, digest, read_json
from .catalogue import Catalogue, DOMAIN_MARGIN_M
from .rule import Components, CODES, classify_points, counts, label, missing
from .view import read_manifest


class MapCells:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.manifest = read_json(self.directory/'manifest.json')

    @lru_cache(maxsize=128)
    def masks(self, name, bounds, shape):
        path = self.directory/(name+'.json')
        if digest(path) != self.manifest['cell_files'][path.name]:
            raise RuntimeError('Validation vector hash mismatch')
        features = read_json(path)
        transform = from_bounds(*bounds, shape[1], shape[0])

        def burn(code):
            shapes = [(f['geometry'],1) for f in features if f['code']==code]
            if not shapes:
                return np.broadcast_to(False, shape)
            return rasterize(shapes, out_shape=shape, transform=transform,
                             all_touched=False, dtype='uint8').view(bool)
        return burn('SEF'), burn('LAF')


def metrics(surface, sef, laf, bounds, coverage_bbox, res):
    water = (surface == 1) | (surface == 2)
    missed = (surface == 3) | (surface == 4)
    mapped_sea = sef & ~laf
    unknown = water & ~(sef | laf)
    h, w = surface.shape
    l, b, r, t = coverage_bbox
    xs = bounds[0]+(np.arange(w)+.5)*res
    ys = bounds[3]-(np.arange(h)+.5)*res
    inside = ((xs>=l)&(xs<=r))[None,:] & ((ys>=b)&(ys<=t))[:,None]
    return dict(water_pixels=int(water.sum()),
                water_inside_SEF_minus_LAF=int(np.count_nonzero(water & mapped_sea)),
                mapped_sea_nodata=int(np.count_nonzero((water | missed) & mapped_sea)),
                false_water=int(np.count_nonzero(water & laf)),
                missed_sea_3=int(np.count_nonzero((surface == 3) & mapped_sea)),
                missed_sea_4=int(np.count_nonzero((surface == 4) & mapped_sea)),
                class_3_inside_SEF=int(np.count_nonzero((surface == 3) & sef)),
                water_outside_coverage_bbox=int(np.count_nonzero(unknown & ~inside)),
                water_neither_class_within_bbox=int(np.count_nonzero(unknown & inside)),
                water_neither_class=int(unknown.sum()))


def component_stats(labels, offset, cell, res):
    l, _, _, t = cell['bounds']
    bincount = np.bincount(labels.ravel())
    result = {}
    for local, slices in enumerate(ndimage.find_objects(labels), 1):
        rs, cs = slices
        result[offset+local] = dict(pixels=int(bincount[local]), cell=cell['id'],
                                    bounds=[l+cs.start*res,t-rs.stop*res,l+cs.stop*res,t-rs.start*res])
    return result


def final_components(components, stats, minimum):
    groups = {}
    for key, value in stats.items():
        root = components.find(key)
        if root not in groups:
            groups[root] = dict(pixels=0, bounds=list(value['bounds']), cells=set())
        row = groups[root]
        row['pixels'] += value['pixels']
        row['cells'].add(value['cell'])
        a, b = row['bounds'], value['bounds']
        row['bounds'] = [min(a[0],b[0]), min(a[1],b[1]), max(a[2],b[2]), max(a[3],b[3])]
    return [dict(component_id=k, pixels=v['pixels'], bounds=v['bounds'], cells=sorted(v['cells']))
            for k, v in sorted(groups.items()) if v['pixels'] >= minimum]


def report_scope(cells, get_surface, maps, grid, *, bounds=None, progress=False, built=False):
    totals = defaultdict(int)
    classes = {str(c):0 for c in CODES}
    unclassified = []
    components = Components()
    comp_stats = {}
    res = grid['resolution']
    north_cutoff = grid['domain_bounds'][3]-DOMAIN_MARGIN_M-10000
    chosen = [c for c in cells if bounds is None or intersects(c['bounds'], bounds)]
    for i, cell in enumerate(chosen):
        if progress and i % 250 == 0:
            print(f'iB5000 raster report: {i+1}/{len(chosen)}', file=sys.stderr, flush=True)
        if built and bounds is None and not any(cell['counts'][str(code)] for code in (1,2,3,4)):
            classes['0'] += cell['counts']['0']
            continue
        surface = get_surface(cell)
        sef, laf = maps.masks(cell['id'], tuple(cell['bounds']), surface.shape)
        cl, cb, cr, ct = cell['bounds']
        actual = cell['bounds'] if bounds is None else [
            max(cl,bounds[0]), max(cb,bounds[1]), min(cr,bounds[2]), min(ct,bounds[3])]
        l, b, r, t = actual
        rs = slice(round((ct-t)/res),round((ct-b)/res))
        cs = slice(round((l-cl)/res),round((r-cl)/res))
        a, sm, lm = surface[rs,cs], sef[rs,cs], laf[rs,cs]
        for k, n in (cell['counts'] if built and bounds is None else counts(a)).items():
            classes[k] += n
        value = metrics(a, sm, lm, actual, maps.manifest['coverage_bbox'], res)
        for k, n in value.items():
            totals[k] += n
        if value['water_neither_class']:
            unclassified.append(dict(cell=cell['id'], bounds=actual,
                    water_neither_class=value['water_neither_class'],
                    outside_coverage_bbox=value['water_outside_coverage_bbox'],
                    within_bbox_neither_class=value['water_neither_class_within_bbox'],
                    northern_boundary=t>=north_cutoff))
        if value['false_water']:
            false = np.zeros(surface.shape, bool)
            false[rs,cs] = ((a==1)|(a==2)) & lm
            key = tuple(cell['key'])
            labels = components.add(key, false)
            offset, _ = components.cells[key]
            comp_stats.update(component_stats(labels, offset, cell, res))
    water = classes['1']+classes['2']
    nodata = water+classes['3']+classes['4']
    mapped = totals['mapped_sea_nodata']
    return dict(class_counts=classes, **totals,
                false_water_fraction=totals['false_water']/water if water else None,
                mapped_sea_nodata_water_fraction=totals['water_inside_SEF_minus_LAF']/mapped if mapped else None,
                dsm_nodata_pixels=nodata, dsm_nodata_water_fraction=water/nodata if nodata else None,
                unclassified_water_cells=unclassified,
                northern_boundary_definition=dict(lower_northing=north_cutoff,
                    description='northernmost 10 km of the raw catalogue plus its northern domain margin'),
                northern_boundary_cells=[r for r in unclassified if r['northern_boundary']],
                false_water_components_over_2500=final_components(components, comp_stats, 2501))


def enclosed_components(cells, read_surface, catalogue):
    components = Components()
    stats = {}
    by_key = {tuple(cell['key']):cell for cell in cells}
    res = catalogue.res
    for key, cell in by_key.items():
        if cell['counts']['3']:
            labels = components.add(key, read_surface(cell) == 3)
            stats.update(component_stats(labels, components.cells[key][0], cell, res))
    selected = final_components(components, stats, 10000)
    selected_ids = {row['component_id'] for row in selected}
    touched = {name for row in selected for name in row['cells']}

    @lru_cache(maxsize=16)
    def root_labels(key):
        if key not in components.cells:
            return None
        offset, n = components.cells[key]
        roots = [components.find(offset+i) for i in range(1,n+1)]
        table = np.array([0, *(i if i in selected_ids else 0 for i in roots)], np.int32)
        if not table.any():
            return None
        labels, _ = label(read_surface(by_key[key]) == 3)
        return table[labels]

    heights = defaultdict(list)
    neighbors = ((0,0), (-1,0), (1,0), (0,-1), (0,1))
    for key, cell in by_key.items():
        if not cell['counts']['0']:
            continue
        x, y = key
        keys = [(x+dx,y+dy) for dx,dy in neighbors]
        if not any(k in by_key and by_key[k]['id'] in touched for k in keys):
            continue
        # Observed pixels occur only in full supplied cells. A class-3
        # component cannot reach a partial cell on the domain boundary.
        h, w = catalogue.height, catalogue.width
        padded = np.zeros((h+2,w+2), np.int32)
        center, west, east, south, north = map(root_labels, keys)
        if center is not None: padded[1:-1,1:-1] = center
        if west is not None: padded[1:-1,0] = west[:,-1]
        if east is not None: padded[1:-1,-1] = east[:,0]
        if south is not None: padded[-1,1:-1] = south[0,:]
        if north is not None: padded[0,1:-1] = north[-1,:]
        rows, cols = np.nonzero((padded[:-2,1:-1] > 0) | (padded[2:,1:-1] > 0) |
                               (padded[1:-1,:-2] > 0) | (padded[1:-1,2:] > 0))
        if not len(rows):
            continue
        raw = catalogue.read(catalogue.window(key))[rows,cols]
        adjacent = np.stack([padded[rows,cols+1], padded[rows+2,cols+1],
                             padded[rows+1,cols], padded[rows+1,cols+2]])
        for component in np.unique(adjacent[adjacent > 0]):
            # An observed pixel contributes once to each component it borders.
            values = raw[(adjacent == component).any(axis=0) & ~missing(raw)]
            if values.size:
                heights[int(component)].append(values)
    for row in selected:
        values = heights[row['component_id']]
        samples = np.concatenate(values) if values else np.empty(0)
        p10, median, p90 = map(float, np.percentile(samples,[10,50,90])) if samples.size else (None,None,None)
        row['observed_shore_heights_m'] = dict(pixels=int(samples.size), p10=p10, median=median, p90=p90)
    return selected


def sensitivity(doc, catalogue, maps, halos, read_surface):
    cells = doc['cells']
    outputs = []
    maximum = doc['profile']['max_shore_distance_m']
    for margin in (4,5,6):
        profile = dict(doc['profile'], low_shore_margin_m=margin)
        shore_keys = set()
        padding = maximum+100+catalogue.res
        for halo in halos.values():
            expanded = [halo[0]-padding,halo[1]-padding,halo[2]+padding,halo[3]+padding]
            shore_keys.update(tuple(c['key']) for c in cells if c['supplied'] and intersects(c['bounds'],expanded))
        shores = {key:catalogue.shores(key,profile) for key in sorted(shore_keys)}
        for preference in (0,50,100):
            profile['shore_preference_m'] = preference
            for name, halo in halos.items():
                def classified(cell):
                    key = tuple(cell['key'])
                    old = read_surface(cell)
                    bad = (old>=1) & (old<=4)
                    opened = bad & (old!=3)
                    low, high = catalogue.points_near(key,shores,maximum+preference)
                    x, y, _, _ = catalogue.window(key)
                    return classify_points(bad,opened,low,high,profile,x0=x,y0=y,resolution=catalogue.res,
                                           supplied=cell['supplied'],origin=(catalogue.e0,catalogue.n0),
                                           pixel_offset=catalogue.pixel_offset(key))
                result = report_scope(cells,classified,maps,doc['grid'],bounds=halo)
                outputs.append(dict(scope=name,bounds=halo,low_shore_margin_m=margin,
                                    shore_preference_m=preference,report=result))
                print(f'sensitivity {name}: margin={margin}, preference={preference}',file=sys.stderr,flush=True)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('view','maps','scopes','machine','work'):
        parser.add_argument('--'+name,required=True)
    args = parser.parse_args(argv)
    view = Path(args.view)
    doc = read_manifest(view)
    maps = MapCells(args.maps)
    scopes = read_json(args.scopes)
    root = Path(__file__).resolve().parents[2]
    work = Path(args.work).absolute()
    if work.resolve()!=work or work.parent!=root/'work' or not work.name.startswith('validation_'):
        raise ValueError('Validation work must be a validation_* namespace under work/')
    if maps.manifest['view_id'] != doc['view_id'] or rasterio.crs.CRS.from_user_input(maps.manifest['crs']) != rasterio.crs.CRS.from_string(doc['grid']['crs']):
        raise RuntimeError('iB5000 map inputs differ from the view ID or CRS')

    @lru_cache(maxsize=128)
    def surface_by_name(name, sha256):
        path = view/'surface'/name
        if digest(path)!=sha256:
            raise RuntimeError('Surface changed during validation')
        with rasterio.open(path) as ds:
            return ds.read(1)

    def read(cell):
        return surface_by_name(cell['surface_name'], cell['surface_sha256'])

    halos = {name+'_halo':[b[0]-DOMAIN_MARGIN_M,b[1]-DOMAIN_MARGIN_M,b[2]+DOMAIN_MARGIN_M,b[3]+DOMAIN_MARGIN_M]
             for name,b in scopes.items()}
    reports = {'territory':report_scope(doc['cells'],read,maps,doc['grid'],progress=True,built=True)}
    for name, bounds in halos.items():
        reports[name] = report_scope(doc['cells'],read,maps,doc['grid'],bounds=bounds)
    central = reports['central_halo']
    harbour = dict(numerator=central['water_inside_SEF_minus_LAF'], denominator=central['mapped_sea_nodata'],
                   share=central['mapped_sea_nodata_water_fraction'],
                   dsm_only_numerator=central['water_pixels'], dsm_only_denominator=central['dsm_nodata_pixels'],
                   dsm_only_share=central['dsm_nodata_water_fraction'])
    header = dict(report_only=True,view_id=doc['view_id'],profile_sha256=doc['profile_sha256'],
                  observational_accuracy='NOT VERIFIED')
    output = work/'reports'
    atomic_json(output/'ib5000-report.json',dict(schema='sea2-ib5000-report-2.2',**header,reports=reports,
        victoria_harbour=harbour, map_coverage_definition='Joint LAF/SEF bounding box is a coverage proxy. Both inside and outside that box, pixels in neither class are listed.'))
    catalogue = Catalogue(root/read_json(args.machine)['dsm_dir'])
    enclosed = enclosed_components(doc['cells'],read,catalogue)
    atomic_json(output/'class-3-components.json',dict(schema='sea2-class-3-components-2.2',**header,
                minimum_pixels=10000, connectivity=4, components=enclosed))
    variants = sensitivity(doc,catalogue,maps,halos,read)
    atomic_json(output/'sensitivity-report.json',dict(schema='sea2-label-sensitivity-2.2',**header,
                classification_only=True,variants=variants))
    print('iB5000, class-3 components and all 27 sensitivity records complete',flush=True)


if __name__=='__main__':
    main()
