"""Native DSM lattice with bounded window reads; no vector dependencies."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

from tools.shade_map.config import InvalidInput
from .rule import NODATA, shore_masks

DOMAIN_MARGIN_M = 1000
SHIFTED = {'14NE15A','14NE15B','14NE15C','14NE15D'}


def header_inventory(directory):
    """Include all non-hidden regular catalogue/auxiliary files, without opening."""
    records = []
    for path in sorted(Path(directory).iterdir()):
        if not path.name.startswith('.') and path.is_file():
            info = path.stat()
            records.append(dict(name=path.name, bytes=info.st_size, mtime_ns=info.st_mtime_ns))
    return records


class Catalogue:
    def __init__(self, directory):
        self.directory=Path(directory).resolve()
        self.records=[]
        for path in sorted(self.directory.glob('*.tif')):
            with rasterio.open(path) as ds:
                a=ds.transform
                if ds.count!=1 or ds.dtypes!=('float32',) or ds.crs is None or not ds.crs.is_projected or ds.crs.linear_units!='metre' or a.b or a.d or a.a<=0 or a.e!=-a.a:
                    raise InvalidInput(f'dsm_dir: unsupported native grid/type: {path.name}')
                self.records.append(dict(name=path.name,path=str(path),bounds=list(ds.bounds),
                                         transform=list(a)[:6],width=ds.width,height=ds.height,
                                         crs=ds.crs.to_string(),nodata=ds.nodata,dtype=ds.dtypes[0],
                                         auxiliary=sorted(Path(f).name for f in ds.files if Path(f).resolve()!=path)))
        if not self.records:
            raise InvalidInput('dsm_dir: no DSM GeoTIFF files found')
        first=self.records[0]
        self.res=first['transform'][0]; self.width=first['width']; self.height=first['height']
        self.crs=first['crs']
        self.e0=min(round(r['bounds'][0]/self.res)*self.res for r in self.records)
        self.n0=min(round(r['bounds'][1]/self.res)*self.res for r in self.records)
        self.tiles={}; self.shifted=[]
        for r in self.records:
            if (r['width'],r['height'],r['crs'],r['transform'][0])!=(self.width,self.height,self.crs,self.res):
                raise InvalidInput('dsm_dir: native cell dimensions, CRS and resolution must be uniform')
            # The four shifted tiles also have a different NoData metadata value.
            # Preserve it per supplied tile. The frozen rule's pixel definition
            # remains exactly non-finite or -9999; no ingestion correction occurs.
            x=(r['bounds'][0]-self.e0)/self.res; y=(r['bounds'][1]-self.n0)/self.res
            dx,dy=abs(x-round(x)),abs(y-round(y))
            shifted=r['name'].split('(')[0] in SHIFTED
            if max(dx,dy)>(1e-6 if shifted else 1e-7) or round(x)%self.width or round(y)%self.height:
                raise InvalidInput(f'dsm_dir: non-native cell origin: {r["name"]}')
            key=(round(x)//self.width,round(y)//self.height)
            if key in self.tiles:
                raise InvalidInput('dsm_dir: overlapping native cells')
            r['key']=key; self.tiles[key]=r
            if shifted: self.shifted.append(dict(name=r['name'],offset_pixels=[x-round(x),y-round(y)],declared_nodata=r['nodata']))
        self.raw_width=(max(k[0] for k in self.tiles)+1)*self.width
        self.raw_height=(max(k[1] for k in self.tiles)+1)*self.height
        distance=DOMAIN_MARGIN_M/self.res
        if abs(distance-round(distance))>1e-8:
            raise InvalidInput('domain margin must be a whole number of native pixels')
        halo=round(distance)
        self.domain=(-halo,-halo,self.raw_width+halo,self.raw_height+halo)
        l,b,r,t=self.domain
        self.xs=range(l//self.width, math.ceil(r/self.width))
        self.ys=range(b//self.height,math.ceil(t/self.height))

    def keys(self):
        for y in self.ys:
            for x in self.xs:
                yield x,y

    def window(self,key,*,clip=True):
        x,y=key[0]*self.width,key[1]*self.height
        if not clip: return x,y,self.width,self.height
        l,b,r,t=self.domain
        x1,y1=min(x+self.width,r),min(y+self.height,t)
        x,y=max(x,l),max(y,b)
        return x,y,x1-x,y1-y

    def bounds(self,window):
        x,y,w,h=window
        return [self.e0+x*self.res,self.n0+y*self.res,self.e0+(x+w)*self.res,self.n0+(y+h)*self.res]

    def transform(self,window):
        l,b,r,t=self.bounds(window)
        return from_origin(l,t,self.res,self.res)

    def name(self,key):
        e=self.e0+key[0]*self.width*self.res; n=self.n0+key[1]*self.height*self.res
        def token(v): return str(int(v)) if v==int(v) else format(v,'.12g')
        return f'e{token(e)}n{token(n)}'

    def pixel_offset(self,key):
        record=self.tiles.get(key)
        if record is None:return (0.0,0.0)
        dx=(record['transform'][2]-(self.e0+key[0]*self.width*self.res))/self.res
        dy=(record['transform'][5]-(self.n0+(key[1]+1)*self.height*self.res))/self.res
        return dy,dx

    def read(self,window):
        x,y,w,h=window
        # Every empty-cell pixel is NoData by definition, independently of a
        # supplied tile's metadata sentinel. -9999 is the rule's finite marker.
        result=np.full((h,w),NODATA,np.float32)
        for iy in range(y//self.height,math.ceil((y+h)/self.height)):
            for ix in range(x//self.width,math.ceil((x+w)/self.width)):
                r=self.tiles.get((ix,iy))
                if r is None: continue
                tx,ty=ix*self.width,iy*self.height
                l,b=max(x,tx),max(y,ty); right,top=min(x+w,tx+self.width),min(y+h,ty+self.height)
                if l>=right or b>=top: continue
                with rasterio.open(r['path']) as ds:
                    a=ds.read(1,window=Window(l-tx,ty+self.height-top,right-l,top-b))
                result[y+h-top:y+h-b,l-x:right-x]=a
        return result

    def data_and_shores(self,key,profile):
        x,y,w,h=self.window(key)
        if key not in self.tiles:
            return np.full((h,w),NODATA,np.float32),(np.empty((0,2),np.int32),)*2
        a=self.read((x-1,y-1,w+2,h+2))
        low,high=shore_masks(a,profile)
        output=[]
        offset=np.asarray(self.pixel_offset(key),np.float64)
        for mask in (low[1:-1,1:-1],high[1:-1,1:-1]):
            rr,cc=np.nonzero(mask)
            output.append(np.column_stack([y+h-1-rr,x+cc]).astype(np.float64)+offset)
        return a[1:-1,1:-1],tuple(output)

    def shores(self,key,profile):
        return self.data_and_shores(key,profile)[1]

    def points_near(self,key,shores,radius_m):
        x,y,w,h=self.window(key); radius=math.ceil(radius_m/self.res)
        pools=[[],[]]
        for iy in range((y-radius)//self.height,(y+h+radius)//self.height+1):
            for ix in range((x-radius)//self.width,(x+w+radius)//self.width+1):
                pair=shores.get((ix,iy))
                if pair:
                    for items,points in zip(pools,pair):
                        if len(points): items.append(points)
        return tuple(np.concatenate(p) if p else np.empty((0,2),np.int32) for p in pools)
