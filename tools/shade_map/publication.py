"""Bounded frame publication, relative VRTs and whole-surface summaries."""
from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import from_bounds

from src import v1
from tools import region_request as adapter
from .common import (atomic_json, digest, read_json, safe_relative, seal,
                     verify_files, verify_seal)
from .config import check_document

LAYERS = ('shade', 'quality', 'surface')
NODATA = dict(shade=255, quality=None, surface=255)


def raster_profile(bounds, crs=v1.DEFAULT_CRS):
    l, b, r, t = bounds
    return dict(driver='GTiff', width=round((r-l)/.5), height=round((t-b)/.5), count=1,
                dtype='uint8', crs=crs, transform=from_origin(l,t,.5,.5),
                compress='DEFLATE', tiled=True, blockxsize=256, blockysize=256,
                predictor=2)


def write_raster(path, values, bounds, layer, crs=v1.DEFAULT_CRS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, 'w', **raster_profile(bounds, crs), nodata=NODATA[layer]) as dst:
        dst.write(values, 1)
        dst.update_tags(layer=layer, policy=v1.POLICY)
        if layer == 'quality':
            import json
            dst.update_tags(quality_reasons=json.dumps(v1.QUALITY, sort_keys=True))


def write_vrt(path, bounds, cells, layer, crs=v1.DEFAULT_CRS):
    profile = raster_profile(bounds, crs)
    root = ET.Element('VRTDataset', rasterXSize=str(profile['width']), rasterYSize=str(profile['height']))
    ET.SubElement(root, 'SRS').text = rasterio.crs.CRS.from_string(crs).to_wkt()
    a = profile['transform']
    ET.SubElement(root, 'GeoTransform').text = ','.join(map(str, (a.c,a.a,a.b,a.f,a.d,a.e)))
    band = ET.SubElement(root, 'VRTRasterBand', dataType='Byte', band='1')
    if NODATA[layer] is not None:
        ET.SubElement(band, 'NoDataValue').text = str(NODATA[layer])
    for cell in cells:
        source = ET.SubElement(band, 'SimpleSource')
        ET.SubElement(source, 'SourceFilename', relativeToVRT='1').text = f'{layer}/{cell["id"]}.tif'
        ET.SubElement(source, 'SourceBand').text = '1'
        ET.SubElement(source, 'SrcRect', xOff='0', yOff='0', xSize=str(cell['width']), ySize=str(cell['height']))
        ET.SubElement(source, 'DstRect', xOff=str(round((cell['bounds'][0]-bounds[0])/.5)),
                      yOff=str(round((bounds[3]-cell['bounds'][3])/.5)),
                      xSize=str(cell['width']), ySize=str(cell['height']))
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def _solar(sidecar, utc):
    tiles = {}
    for request in sidecar['requests']:
        if utc not in request['utc_times']:
            continue
        index = read_json(Path(request['output_directory'])/'result_index.json')
        frame = next(f for f in index['frames'] if f['utc_time'] == utc)
        for tile in frame['solar_by_tile']:
            name = tile['source_name']
            if name in tiles and tiles[name] != tile:
                raise RuntimeError('Conflicting engine solar metadata')
            tiles[name] = tile
    return [tiles[name] for name in sorted(tiles)]


def verify_frame(folder, expected_frame=None):
    record = read_json(Path(folder)/'frame.json')
    check_document(record, 'frame')
    verify_seal(record)
    if expected_frame and any(record[k] != expected_frame[k] for k in ('local_time','utc_time','date','time')):
        raise RuntimeError('Published frame time differs')
    verify_files(folder, record['files'])
    actual = {p.relative_to(folder).as_posix() for p in Path(folder).rglob('*') if p.is_file()}
    if actual != set(record['files']) | {'frame.json'}:
        raise RuntimeError('Unexpected or missing published frame files')
    return record


def _check_raster(path, expected, bounds, layer, crs):
    with rasterio.open(path) as ds:
        profile = raster_profile(bounds, crs)
        if (ds.count != 1 or ds.dtypes != ('uint8',) or ds.crs.to_string() != crs
                or ds.transform != profile['transform'] or ds.nodata != NODATA[layer]
                or ds.compression.value != 'DEFLATE' or not ds.is_tiled
                or not np.array_equal(ds.read(1), expected)):
            raise RuntimeError(f'Published cell differs from engine/source: {path.name}')


def _verify_views(directory, bounds, cells, sidecar, mosaics, utc, source, records, full, crs):
    profile = raster_profile(bounds, crs)
    for cell in cells:
        shade, quality, transform = adapter.read_region_window(sidecar, utc_time=utc,
                                                              bounds=cell['bounds'], logical_mosaics=mosaics)
        surface = source.read_surface(cell['bounds'], records)
        if transform != raster_profile(cell['bounds'], crs)['transform']:
            raise RuntimeError('Engine logical transform differs')
        for layer, expected in zip(LAYERS, (shade,quality,surface)):
            _check_raster(directory/layer/(cell['id']+'.tif'), expected, cell['bounds'], layer, crs)
            for name in [layer+'.vrt'] + ([layer+'.tif'] if full else []):
                with rasterio.open(directory/name) as ds:
                    if (ds.transform != profile['transform'] or ds.crs.to_string() != crs
                            or ds.width != profile['width'] or ds.height != profile['height']
                            or ds.dtypes != ('uint8',) or ds.nodata != NODATA[layer]
                            or not np.array_equal(ds.read(1, window=from_bounds(*cell['bounds'], ds.transform)), expected)):
                        raise RuntimeError(f'Published view differs: {name}')


def publish_frame(prepared, frame, sidecar, mosaics):
    """Write -> independently read back -> rename. No source-name branches."""
    parent = prepared.folder/frame['date']
    parent.mkdir(parents=True, exist_ok=True)
    final, partial = parent/frame['time'], parent/(frame['time']+'.partial')
    if partial.exists():
        if partial.is_symlink():
            raise RuntimeError('Partial publication cannot be a symlink')
        shutil.rmtree(partial)
    if final.exists():
        return verify_frame(final, frame), False
    partial.mkdir()
    counts = {layer: Counter() for layer in LAYERS}
    combinations = Counter()
    plan = prepared.document
    crs = plan['grid']['crs']
    for cell in plan['cells']:
        shade, quality, transform = adapter.read_region_window(sidecar, utc_time=frame['utc_time'],
                                                               bounds=cell['bounds'], logical_mosaics=mosaics)
        if transform != raster_profile(cell['bounds'], crs)['transform']:
            raise RuntimeError('Logical cell transform differs')
        surface = prepared.source.read_surface(cell['bounds'], prepared.records)
        for layer, array, allowed in zip(LAYERS, (shade,quality,surface),
                                         ([0,1,255], list(map(int,v1.QUALITY)), [0,1,2,3,4,255])):
            if array.dtype != np.uint8 or array.shape != shade.shape or not np.all(np.isin(array, allowed)):
                raise RuntimeError(f'Invalid {layer} provider/engine encoding')
            write_raster(partial/layer/(cell['id']+'.tif'), array, cell['bounds'], layer, crs)
            values, amounts = np.unique(array, return_counts=True)
            counts[layer].update({str(int(v)):int(n) for v,n in zip(values,amounts)})
        encoded = (surface.astype(np.uint32)<<16) | (shade.astype(np.uint32)<<8) | quality
        values, amounts = np.unique(encoded, return_counts=True)
        combinations.update({int(v):int(n) for v,n in zip(values,amounts)})
    for layer in LAYERS:
        write_vrt(partial/(layer+'.vrt'), plan['resolved_bounds'], plan['cells'], layer, crs)
        if plan['full_images']:
            with rasterio.open(partial/(layer+'.vrt')) as src, rasterio.open(
                    partial/(layer+'.tif'), 'w', **raster_profile(plan['resolved_bounds'], crs), nodata=NODATA[layer]) as dst:
                for _, window in dst.block_windows(1):
                    dst.write(src.read(1, window=window), 1, window=window)
                dst.update_tags(layer=layer, policy=v1.POLICY)
    _verify_views(partial, plan['resolved_bounds'], plan['cells'], sidecar, mosaics,
                  frame['utc_time'], prepared.source, prepared.records, plan['full_images'], crs)
    files = {safe_relative(p.relative_to(partial).as_posix()):digest(p)
             for p in sorted(partial.rglob('*')) if p.is_file()}
    record = dict(schema='shade-map-frame-1.0', **frame, solar_by_tile=_solar(sidecar, frame['utc_time']),
                  pixel_count=plan['pixel_count'], value_counts={k:dict(v) for k,v in counts.items()},
                  combinations=[dict(surface=k>>16, shade=(k>>8)&255, quality=k&255, pixels=n)
                                for k,n in sorted(combinations.items())], files=files)
    seal(record)
    check_document(record, 'frame')
    atomic_json(partial/'frame.json', record)
    verify_frame(partial, frame)
    partial.rename(final)
    return record, True


def write_summaries(folder, records):
    frames, rows = [], []
    for record in records:
        classes = {}
        for entry in record['combinations']:
            surface = entry['surface']
            classes.setdefault(surface, dict(pixels=0, counts=dict(sunlit=0,shaded=0,uncertain=0),
                                             quality_counts={k:0 for k in v1.QUALITY}))
            item = classes[surface]
            n = entry['pixels']
            item['pixels'] += n
            item['counts'][{0:'sunlit',1:'shaded',255:'uncertain'}[entry['shade']]] += n
            item['quality_counts'][str(entry['quality'])] += n
            rows.append([record['date'],record['time'],record['utc_time'],surface,
                         entry['shade'],entry['quality'],n])
        surfaces = []
        for surface, item in sorted(classes.items()):
            item['fractions'] = {k:v/item['pixels'] for k,v in item['counts'].items()}
            surfaces.append(dict(surface=surface, **item))
        frames.append(dict(local_time=record['local_time'],utc_time=record['utc_time'],
                           date=record['date'],time=record['time'],surfaces=surfaces))
    summary = dict(schema='shade-map-summary-1.0', denominator='whole surface class',frames=frames)
    check_document(summary, 'summary')
    atomic_json(folder/'summary.json', summary)
    # Only complete-run summaries are published; rename makes replacement atomic.
    temp = folder/'.summary.csv.tmp'
    with temp.open('w',newline='') as dst:
        writer=csv.writer(dst,lineterminator='\n')
        writer.writerow(['date','time','utc','surface','shade','quality','pixels'])
        writer.writerows(rows)
    temp.replace(folder/'summary.csv')
