"""Sun-aligned DSM rotation, profile horizon scan, and inverse mapping."""

from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy.ndimage import map_coordinates


@njit(cache=True)
def _scan_columns(strip_by_column: np.ndarray, support_cells: int,
                  max_cells: int = 2000, resolution: float = 0.5):
    """Bounded rotated diagnostic (production uses pixel-centred profiles)."""
    ncols, nrows = strip_by_column.shape
    slopes = np.full((ncols, nrows), np.nan, np.float32)
    supported = np.zeros((ncols, nrows), np.uint8)
    blocker = np.zeros((ncols, nrows), np.float32)
    for c in range(ncols):
        for r in range(nrows):
            z = strip_by_column[c, r]
            if not np.isfinite(z):
                continue
            best = 0.0
            complete = r >= support_cells
            for j in range(max(0, r-max_cells), r):
                v = strip_by_column[c, j]
                if not np.isfinite(v):
                    if r-j <= support_cells:
                        complete = False
                else:
                    slope = (v-z)/((r-j)*resolution)
                    if slope > best:
                        best = slope
                        blocker[c, r] = (r-j)*resolution
            slopes[c, r] = best
            supported[c, r] = complete
    return slopes, supported, blocker


def rotated_strip(
    buffered_dsm: np.ndarray, azimuth_deg: float, *,
    resolution: float = 0.5, t_min: float = -1000.0,
    t_max: float = 100.0, s_min: float = -100.0, s_max: float = 100.0,
) -> tuple[np.ndarray, dict]:
    """Rotate only the sunward strip needed by the central output area.

    t grows away from the Sun; s grows to the right in the rotated view.
    Nearest-neighbour sampling preserves original DSM height values and gaps.
    """
    if buffered_dsm.ndim != 2:
        raise ValueError("Expected a north-up two-dimensional DSM grid")
    nrows = round((t_max - t_min) / resolution)
    ncols = round((s_max - s_min) / resolution)
    t = t_min + (np.arange(nrows, dtype=np.float32) + 0.5) * resolution
    s = s_min + (np.arange(ncols, dtype=np.float32) + 0.5) * resolution
    rad = math.radians(azimuth_deg)
    sina, cosa = math.sin(rad), math.cos(rad)
    centre_row = (buffered_dsm.shape[0] - 1) / 2
    centre_col = (buffered_dsm.shape[1] - 1) / 2
    rr = centre_row + (t[:, None] * cosa + s[None, :] * sina) / resolution
    cc = centre_col + (-t[:, None] * sina + s[None, :] * cosa) / resolution
    strip = map_coordinates(
        buffered_dsm, [rr, cc], order=0, mode="constant", cval=np.nan,
        prefilter=False,
    ).astype(np.float32, copy=False)
    return strip, {"t_min": t_min, "s_min": s_min, "resolution": resolution, "azimuth_deg": azimuth_deg}


def horizon_at_output(
    buffered_dsm: np.ndarray, azimuth_deg: float, output_east: np.ndarray,
    output_north: np.ndarray, *, support_m: float = 1000.0,
    max_distance_m: float = 1000.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rotate, scan, and map horizons back to the north-up output grid.

    Returns known horizon elevation (degrees), complete 1 km support, and
    distance to the known maximum blocker. The first may be useful even when
    support is incomplete: a known blocker can still prove shade.
    """
    radius = math.hypot(float(np.max(np.abs(output_east))),
                        float(np.max(np.abs(output_north)))) + 1.0
    strip, meta = rotated_strip(
        buffered_dsm, azimuth_deg,
        t_min=-max_distance_m - radius, t_max=radius,
        s_min=-radius, s_max=radius,
    )
    slopes, supported, blocker = _scan_columns(np.ascontiguousarray(strip.T), round(support_m / 0.5), int(max_distance_m / 0.5))
    a = math.radians(azimuth_deg)
    t = -(output_east * math.sin(a) + output_north * math.cos(a))
    s = output_east * math.cos(a) - output_north * math.sin(a)
    ri = np.rint((t - meta["t_min"]) / 0.5 - 0.5).astype(np.int32)
    ci = np.rint((s - meta["s_min"]) / 0.5 - 0.5).astype(np.int32)
    if ri.min() < 0 or ri.max() >= strip.shape[0] or ci.min() < 0 or ci.max() >= strip.shape[1]:
        raise ValueError("Rotated strip does not cover the output area")
    known_elevation = np.rad2deg(np.arctan(slopes[ci, ri]))
    return known_elevation, supported[ci, ri].astype(bool), blocker[ci, ri]


@njit(cache=True)
def direct_ray_reference(dsm: np.ndarray, rows: np.ndarray, cols: np.ndarray,
                         azimuth_deg: float, max_distance_m: float = 1000.0):
    """Independent original-grid nearest-cell ray sample for QA only."""
    angle = math.radians(azimuth_deg)
    dr = -math.cos(angle)
    dc = math.sin(angle)
    max_steps = int(max_distance_m / 0.5)
    out = np.empty(len(rows), dtype=np.float32)
    complete = np.ones(len(rows), dtype=np.uint8)
    for k in range(len(rows)):
        r0, c0 = rows[k], cols[k]
        z0 = dsm[r0, c0]
        if not np.isfinite(z0):
            out[k] = np.nan
            complete[k] = 0
            continue
        slope = 0.0
        for step in range(1, max_steps + 1):
            r = int(round(r0 + dr * step))
            c = int(round(c0 + dc * step))
            if r < 0 or c < 0 or r >= dsm.shape[0] or c >= dsm.shape[1]:
                complete[k] = 0
                continue
            if ((r-r0)**2 + (c-c0)**2)*0.25 > max_distance_m**2 + 1e-9:
                continue
            z = dsm[r, c]
            if not np.isfinite(z):
                complete[k] = 0
            else:
                candidate = (z - z0) / (step * 0.5)
                if candidate > slope:
                    slope = candidate
        out[k] = math.degrees(math.atan(slope))
    return out, complete


@njit(cache=True, nogil=True)
def pixel_centred_horizon(dsm: np.ndarray, rows: np.ndarray, cols: np.ndarray,
                          azimuth_deg: float, max_distance_m: float = 1000.0,
                          support_m: float = 1000.0, resolution: float = 0.5,
                          origin_row: int = 0, origin_col: int = 0):
    """Existing 0.25 m pixel-centred profiles with globally consistent sampling.

    origin is the buffered array's address in the whole output grid. Banker's
    rounding uses global index parity, so odd chunk offsets cannot change ties.
    Both nominal ray range and sampled cell-centre horizontal range are bounded.
    Farther cells in a rectangular halo never extend the model boundary.
    """
    angle = math.radians(azimuth_deg)
    dr, dc = -math.cos(angle), math.sin(angle)
    if abs(dr) < 1e-14:
        dr = 0.0
    if abs(dc) < 1e-14:
        dc = 0.0
    step_m = 0.25
    max_steps = int(math.floor(max_distance_m / step_m + 1e-10))
    ro = np.empty((2, max_steps), np.int32)
    co = np.empty((2, max_steps), np.int32)
    for parity in range(2):
        for i in range(max_steps):
            ro[parity, i] = int(round(parity + dr*(i+1)*step_m/resolution))-parity
            co[parity, i] = int(round(parity + dc*(i+1)*step_m/resolution))-parity
    out = np.empty(len(rows), dtype=np.float32)
    supported = np.ones(len(rows), dtype=np.uint8)
    blocker = np.zeros(len(rows), dtype=np.float32)
    for k in range(len(rows)):
        r0, c0 = rows[k], cols[k]
        z0 = dsm[r0, c0]
        if not np.isfinite(z0):
            out[k] = np.nan
            supported[k] = 0
            continue
        rp, cp = (r0+origin_row) % 2, (c0+origin_col) % 2
        max_slope = 0.0
        for i in range(max_steps):
            rd, cd = ro[rp, i], co[cp, i]
            if (rd*rd+cd*cd)*resolution*resolution > max_distance_m*max_distance_m + 1e-9:
                continue
            r, c = r0+rd, c0+cd
            distance = (i+1)*step_m
            if r < 0 or c < 0 or r >= dsm.shape[0] or c >= dsm.shape[1]:
                if distance <= support_m:
                    supported[k] = 0
                continue
            z = dsm[r, c]
            if not np.isfinite(z):
                if distance <= support_m:
                    supported[k] = 0
            else:
                candidate = (z-z0)/distance
                if candidate > max_slope:
                    max_slope = candidate
                    blocker[k] = distance
        out[k] = math.degrees(math.atan(max_slope))
    return out, supported, blocker
