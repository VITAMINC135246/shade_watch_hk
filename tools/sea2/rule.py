"""Bounded Euclidean classification and cross-cell 4-connected components."""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

CROSS = ndimage.generate_binary_structure(2, 1)
CODES = (0, 1, 2, 3, 4, 255)
NODATA = -9999.0


def missing(data):
    return ~np.isfinite(data) | (data == NODATA)


def label(mask):
    if mask.all():
        return np.ones(mask.shape, np.int32), 1
    if not mask.any():
        return np.zeros(mask.shape, np.int32), 0
    return ndimage.label(mask, CROSS)


class Components:
    """Streaming bottom-to-top cell rows; exterior is component zero."""
    def __init__(self):
        self.parent = [0]
        self.cells = {}
        self.below = {}
        self.left = None
        self.previous = None

    def find(self, x):
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a, b):
        a, b = self.find(int(a)), self.find(int(b))
        if a != b:
            self.parent[max(a, b)] = min(a, b)

    def join(self, a, b):
        valid = (a > 0) & (b > 0)
        if valid.any():
            for one, two in np.unique(np.stack([a[valid], b[valid]], axis=1), axis=0):
                self.union(one, two)

    def add(self, key, mask, *, west=False, east=False, south=False, north=False):
        labels, n = label(mask)
        offset = len(self.parent)-1
        self.parent.extend(range(offset+1, offset+n+1))
        self.cells[key] = (offset, n)
        ids = lambda edge: np.where(edge > 0, edge+offset, -1)
        top, bottom = ids(labels[0]), ids(labels[-1])
        left, right = ids(labels[:, 0]), ids(labels[:, -1])
        x, y = key
        if self.previous == (x-1, y):
            self.join(self.left, left)
        if x in self.below and self.below[x][0] == y-1:
            self.join(self.below[x][1], bottom)
        for is_edge, edge in [(west,left),(east,right),(south,bottom),(north,top)]:
            if is_edge:
                for component in np.unique(edge[edge > 0]):
                    self.union(0, component)
        self.left, self.below[x], self.previous = right, (y, top), key
        return labels

    def open_mask(self, key, labels):
        offset, n = self.cells[key]
        table = np.zeros(n+1, bool)
        table[1:] = [self.find(offset+i) == 0 for i in range(1, n+1)]
        return table[labels]


def shore_masks(data, profile):
    bad = missing(data)
    shore = ~bad & ndimage.binary_dilation(bad, structure=CROSS, border_value=0)
    low = shore & (data <= profile['h_sea_m']+profile['low_shore_margin_m'])
    return low, shore & ~low


def exclusions_mask(shape, profile, *, x0, y0, resolution, origin=(0, 0)):
    result = np.zeros(shape, bool)
    if not profile['exclusions']:
        return result
    h, w = shape
    xs = origin[0]+(x0+np.arange(w)+.5)*resolution
    ys = origin[1]+(y0+h-np.arange(h)-.5)*resolution
    for zone in profile['exclusions']:
        l, b, r, t = zone['bounds']
        # Closed rectangles are explicit exclusion zones, including boundary centres.
        result |= ((ys >= b) & (ys <= t))[:, None] & ((xs >= l) & (xs <= r))[None, :]
    return result


def classify_points(bad, opened, low_points, high_points, profile, *, x0, y0,
                    resolution, supplied=True, origin=(0, 0), pixel_offset=(0, 0)):
    """Points use integer centre addresses (northing, easting), not edge coords."""
    y0+=pixel_offset[0]; x0+=pixel_offset[1]
    result = np.where(bad, np.where(opened, 4, 3), 0).astype(np.uint8)
    candidates = bad & opened & ~exclusions_mask(bad.shape, profile, x0=x0, y0=y0,
                                                resolution=resolution, origin=origin)
    if not candidates.any() or not len(low_points):
        return result
    h, w = bad.shape
    radius = (profile['max_shore_distance_m']+profile['shore_preference_m'])/resolution
    def bounded(points):
        points = np.asarray(points)
        if not len(points):
            return np.empty((0,2), np.int32)
        return points[(points[:,0] >= y0-radius) & (points[:,0] <= y0+h-1+radius)
                      & (points[:,1] >= x0-radius) & (points[:,1] <= x0+w-1+radius)]
    low_points, high_points = bounded(low_points), bounded(high_points)
    if not len(low_points):
        return result
    low_tree = cKDTree(low_points)
    high_tree = cKDTree(high_points) if len(high_points) else None
    maximum = profile['max_shore_distance_m']/resolution
    preference = profile['shore_preference_m']/resolution
    # Distance-to-a-set is 1-Lipschitz. Certify whole 64-pixel blocks only when
    # centre distance +/- the farthest pixel radius proves the exact rule for
    # every candidate. Boundary blocks retain the exact per-pixel queries below.
    # This avoids billions of redundant offshore queries without approximation.
    if np.count_nonzero(candidates)>65536:
        blocks=[]; centres=[]; radii=[]
        for row in range(0,h,64):
            for col in range(0,w,64):
                bh,bw=min(64,h-row),min(64,w-col)
                if not candidates[row:row+bh,col:col+bw].any():continue
                blocks.append((row,col,bh,bw))
                centres.append([y0+h-1-row-(bh-1)/2,x0+col+(bw-1)/2])
                radii.append(math.hypot(bh-1,bw-1)/2)
        centres=np.asarray(centres); radii=np.asarray(radii)
        dlc=low_tree.query(centres)[0]
        dhc=high_tree.query(centres)[0] if high_tree is not None else np.full(len(centres),np.inf)
        certain_water=(dlc+radii<=maximum-1e-7)&(dlc+radii<=dhc-radii+preference-1e-7)
        certain_dry=(dlc-radii>maximum+1e-7)|(dlc-radii>dhc+radii+preference+1e-7)
        for k,(row,col,bh,bw) in enumerate(blocks):
            if not (certain_water[k] or certain_dry[k]):continue
            local=candidates[row:row+bh,col:col+bw]
            if certain_water[k]:
                target=result[row:row+bh,col:col+bw]
                if np.isscalar(supplied):target[local]=1 if supplied else 2
                else:target[local]=np.where(supplied[row:row+bh,col:col+bw][local],1,2)
            local[:]=False
    # Row chunks bound coordinate allocations even for a completely empty cell.
    rows_per_chunk = max(1, 131072//w)
    for start in range(0, h, rows_per_chunk):
        rr, cc = np.nonzero(candidates[start:start+rows_per_chunk])
        rr += start
        if not len(rr):
            continue
        points = np.column_stack([y0+h-1-rr, x0+cc])
        dl = low_tree.query(points, distance_upper_bound=maximum+1e-7)[0]
        keep = np.isfinite(dl) & (dl <= maximum)
        if high_tree is not None and keep.any():
            selected = np.flatnonzero(keep)
            dh = high_tree.query(points[selected], distance_upper_bound=radius+1e-7)[0]
            keep[selected] &= dl[selected] <= dh+preference
        if np.isscalar(supplied):
            result[rr[keep], cc[keep]] = 1 if supplied else 2
        else:
            result[rr[keep], cc[keep]] = np.where(supplied[rr[keep],cc[keep]],1,2)
    return result


def counts(surface):
    values = np.bincount(surface.ravel(), minlength=256)
    return {str(code): int(values[code]) for code in CODES}


def classify_array(data, profile, *, resolution=1, supplied=None, cell_shape=None):
    """Small-fixture reference: independent one-pass EDT versus tiled queries."""
    data = np.array(data, dtype=np.float32, copy=True)
    supplied = np.ones(data.shape, bool) if supplied is None else np.asarray(supplied, bool)
    data[~supplied] = np.nan
    bad = missing(data)
    low, high = shore_masks(data, profile)
    h, w = data.shape
    if cell_shape is None:
        labels, n = label(bad)
        border = np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]))
        opened = np.isin(labels, border[border > 0]) & bad
        dl = ndimage.distance_transform_edt(~low)*resolution if low.any() else np.full(data.shape,np.inf)
        dh = ndimage.distance_transform_edt(~high)*resolution if high.any() else np.full(data.shape,np.inf)
        water = bad & opened & (dl <= profile['max_shore_distance_m']) & (dl <= dh+profile['shore_preference_m'])
        water &= ~exclusions_mask(data.shape,profile,x0=0,y0=0,resolution=resolution)
        result = np.where(bad,np.where(opened,4,3),0).astype(np.uint8)
        result[water] = np.where(supplied[water],1,2)
        return result
    ch, cw = cell_shape
    pieces = []
    for iy, y0 in enumerate(range(0,h,ch)):
        for ix, x0 in enumerate(range(0,w,cw)):
            height, width = min(ch,h-y0), min(cw,w-x0)
            pieces.append(((ix,iy),x0,y0,width,height,slice(h-y0-height,h-y0),slice(x0,x0+width)))
    components=Components()
    for key,x,y,width,height,rs,cs in pieces:
        components.add(key,bad[rs,cs],west=x==0,east=x+width==w,south=y==0,north=y+height==h)
    def points(mask):
        rr,cc=np.nonzero(mask)
        return np.column_stack([h-1-rr,cc])
    lows,highs=points(low),points(high)
    result=np.zeros(data.shape,np.uint8)
    for key,x,y,width,height,rs,cs in pieces:
        labels,_=label(bad[rs,cs])
        opened=components.open_mask(key,labels)
        result[rs,cs]=classify_points(bad[rs,cs],opened,lows,highs,profile,x0=x,y0=y,
                                     resolution=resolution,supplied=supplied[rs,cs])
    return result
