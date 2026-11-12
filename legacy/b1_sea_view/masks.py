"""Native-grid pixel-centre masks; runs in unchanged engine environment."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from src.spatial import intersects


class Coastline:
    def __init__(self,directory):
        directory=Path(directory)
        self.manifest=json.loads((directory/'manifest.json').read_text())
        path=directory/self.manifest['vector_file']
        with path.open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=self.manifest['vector_sha256']:
                raise ValueError('Derived vector hash changed')
        vector=json.loads(path.read_text())
        if rasterio.crs.CRS.from_user_input(self.manifest['crs'])!=rasterio.crs.CRS.from_epsg(2326):
            raise ValueError('Map CRS is not equivalent to EPSG:2326')
        self.features=vector['features']

    def masks(self,shape,transform):
        h,w=shape
        bounds=(transform.c,transform.f+h*transform.e,transform.c+w*transform.a,transform.f)
        def burn(code):
            geometries=[(f['geometry'],1) for f in self.features
                        if f['properties']['code']==code and intersects(bounds,f['bbox'])]
            if not geometries: return np.zeros(shape,bool)
            return rasterize(geometries,out_shape=shape,transform=transform,
                             fill=0,all_touched=False,dtype='uint8').astype(bool)
        land=burn('LAF')
        sea=burn('SEF') & ~land
        return sea,land


def fill_mask(values,sea):
    return (~np.isfinite(values) | (values==-9999)) & sea
