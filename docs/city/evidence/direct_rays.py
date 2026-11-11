"""Stratified development spot checks using the independent NumPy V1 oracle."""
import json
import math
from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
from v1_oracle import classification_oracle, ray_oracle

FRAMES = ("20260621/0900", "20260621/1330", "20260621/1800", "20261222/1000")
SEED = 20261111
SEAM = 437500.0
RES = 0.5


def read(path):
    return json.loads(path.read_text())


def expand(bounds, metres):
    l, b, r, t = bounds
    return l-metres, b-metres, r+metres, t+metres


def offset(bounds, window):
    l, _, _, t = bounds
    left, _, _, top = window
    return round((t-top)/RES), round((left-l)/RES)


def read_view(view, bounds, cells, *, surface=False):
    left, bottom, right, top = bounds
    shape = (round((top-bottom)/RES), round((right-left)/RES))
    array = np.full(shape, 255 if surface else np.nan, np.uint8 if surface else np.float32)
    for cell in cells:
        l, b, r, t = cell["bounds"]
        a, z, c, d = max(left, l), max(bottom, b), min(right, r), min(top, t)
        if a >= c or z >= d:
            continue
        directory, filename = ("surface", cell["surface_name"]) if surface else ("tiles", cell["tile_name"])
        with rasterio.open(view / directory / filename) as ds:
            window = from_bounds(a, z, c, d, ds.transform)
            data = ds.read(1, window=window)
            if not surface:
                data[data == ds.nodata] = np.nan
        row, col = offset(bounds, (a, z, c, d))
        h, w = data.shape
        array[row:row+h, col:col+w] = data
    return array


def choose(mask, excluded, count, rng):
    indices = np.flatnonzero(mask.ravel() & ~excluded)
    selected = rng.choice(indices, min(count, len(indices)), replace=False)
    excluded[selected] = True
    return selected


def sample_categories(near_below, water_neighbor, seam, used, rng):
    categories = {}
    for name, mask, count in [("below_0_within_50m_of_fill", near_below, 50),
                               ("adjacent_to_filled_water", water_neighbor, 50),
                               ("ray_crosses_sheet_seam", seam, 100)]:
        categories[name] = choose(mask, used, count, rng)
    remaining = 300 - sum(len(values) for values in categories.values())
    categories["unrestricted"] = choose(np.ones_like(near_below), used, remaining, rng)
    return {int(idx): name for name, indices in categories.items() for idx in indices}


def inspect_frame(path, run, data, data_bounds, below, water, used, rng):
    record = read(path / "frame.json")
    with rasterio.open(path / "shade.vrt") as ds, rasterio.open(path / "quality.vrt") as qs:
        shade, quality = ds.read(1), qs.read(1)
    bounds = run["resolved_bounds"]
    seam = np.zeros(shade.shape, bool)
    solar = {row["source_name"]: row for row in record["solar_by_tile"]}
    for cell in run["cells"]:
        row, col = offset(bounds, cell["bounds"])
        direction = solar[cell["source_tile"]]["direction_deg"]
        north = bounds[3] - (row+np.arange(cell["height"])+.5)*RES
        reach = 1000 * math.cos(math.radians(direction))
        crosses = (north-SEAM)*(north+reach-SEAM) < 0
        seam[row:row+cell["height"], col:col+cell["width"]] = crosses[:, None]
    selected = sample_categories(below, water, seam, used, rng)
    indices = np.array(list(selected))
    rr, cc = np.unravel_index(indices, shade.shape)
    samples = []
    halo_row, halo_col = offset(data_bounds, bounds)
    for cell in run["cells"]:
        row, col = offset(bounds, cell["bounds"])
        h, w = cell["height"], cell["width"]
        mask = (rr >= row) & (rr < row+h) & (cc >= col) & (cc < col+w)
        r, c = rr[mask], cc[mask]
        meta = solar[cell["source_tile"]]
        native_row, native_col = offset(data_bounds, cell["native_bounds"])
        native = data[native_row:native_row+h, native_col:native_col+w]
        halo = data[native_row-2000:native_row+h+2000, native_col-2000:native_col+w+2000]
        threshold = math.degrees(math.atan((float(np.nanmax(halo)) - float(np.nanmin(native))) / 1000))
        assert math.isclose(threshold, meta["threshold_deg"], abs_tol=1e-10)
        angles, support, _ = ray_oracle(data, r+halo_row, c+halo_col, meta["direction_deg"],
                                       origin_row=round(-data_bounds[3]/RES), origin_col=round(data_bounds[0]/RES))
        labels, flags = classification_oracle(angles.astype(np.float32), support,
                                              meta["apparent_elevation_deg"], threshold)
        for i, (y, x) in enumerate(zip(r, c)):
            expected = [int(labels[i]), int(flags[i])]
            actual = [int(shade[y, x]), int(quality[y, x])]
            samples.append(dict(row=int(y), column=int(x), sample=selected[int(y*shade.shape[1]+x)],
                                expected=expected, actual=actual))
    assert len(samples) == len(selected) == 300
    return dict(local_time=record["local_time"], samples=samples,
                disagreements=sum(row["expected"] != row["actual"] for row in samples),
                seam_candidates=int(seam.sum()))


def main():
    registration = read(EVIDENCE / "nl0-registration.json")
    view = ROOT / "data/processed/dsm_views/sea_fill_v2_2" / registration["view_id"]
    manifest = read(view / "manifest.json")
    path = ROOT / "outputs/shade_map_g1_dev_20261111/g1_dev_nl1"
    run = read(path / "run_manifest.json")
    bounds = run["resolved_bounds"]
    data_bounds = expand(bounds, 1000)
    data = read_view(view, data_bounds, manifest["cells"])
    surface = read_view(view, expand(bounds, 50), manifest["cells"], surface=True)
    filled = (surface >= 1) & (surface <= 4)
    water = (surface == 1) | (surface == 2)
    core = np.s_[100:-100, 100:-100]
    observed = surface[core] == 0
    below = observed & (data[2000:-2000, 2000:-2000] < 0)
    below &= distance_transform_edt(~filled)[core] * RES <= 50
    adjacent_water = observed & binary_dilation(water)[core]
    rng = np.random.default_rng(SEED)
    used = np.zeros(observed.size, bool)
    evidence = [inspect_frame(path / frame, run, data, data_bounds, below, adjacent_water, used, rng)
                for frame in FRAMES]
    samples = [row for frame in evidence for row in frame["samples"]]
    by_category = {stratum: sum(row["sample"] == stratum for row in samples)
                   for stratum in sorted({row["sample"] for row in samples})}
    disagreements = sum(frame["disagreements"] for frame in evidence)
    print(json.dumps(dict(seed=SEED, targets=len(samples), below_0_available=int(below.sum()),
                          water_neighbors_available=int(adjacent_water.sum()), by_category=by_category,
                          disagreements=disagreements, frames=evidence), separators=(",", ":")))
    return int(bool(disagreements))


if __name__ == "__main__":
    raise SystemExit(main())
