"""Compare every development frame with the frozen Hong Kong references."""
from argparse import ArgumentParser
from datetime import datetime
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "outputs/shade_map_g1_dev_20261111"
REF = {
    1: ROOT / "outputs/v2_daylight_cheungchau_20261009/combined",
    2: ROOT / "outputs/shade_map/measure_lo_wu",
    3: ROOT / "outputs/shade_map/measure_tai_mo_shan",
    4: ROOT / "outputs/shade_map/measure_central",
}


def read(path):
    return json.loads(path.read_text())


def nonzero(counts):
    return {k: v for k, v in counts.items() if v}


def folder_label(frame):
    return datetime.fromisoformat(frame["local_time"]).strftime("%Y%m%d/%H%M")


def compare(candidate, reference, *, crop=False):
    with rasterio.open(candidate) as ds, rasterio.open(reference) as ref:
        assert (ds.count, ds.dtypes, ds.crs, ds.nodata) == (ref.count, ref.dtypes, ref.crs, ref.nodata)
        window = from_bounds(*ds.bounds, ref.transform).round_offsets().round_lengths() if crop else None
        transform = ref.window_transform(window) if crop else ref.transform
        assert ds.transform == transform
        actual, expected = ds.read(1), ref.read(1, window=window)
        assert actual.shape == expected.shape
        return int(np.count_nonzero(actual != expected))


def run(number):
    candidate = OUTPUT / f"g1_dev_hk{number}"
    reference = REF[number]
    v2_reference = number == 1
    actual = read(candidate / "run_manifest.json")
    expected = read(reference / ("result_index.json" if v2_reference else "run_manifest.json"))
    assert actual["status"] == "complete"
    assert actual["resolved_bounds"] == expected["resolved_bounds"]
    assert len(actual["frames"]) == len(expected["frames"]) == (65 if v2_reference else 146)
    frames = []
    for made, original in zip(actual["frames"], expected["frames"]):
        for key in ("utc_time", "local_time"):
            assert made[key] == original[key], (key, made[key], original[key])
        label = f"{made['date']}/{made['time']}"
        assert label == folder_label(original)
        a = candidate / label
        b = reference / label
        counts = read(a / "frame.json")["value_counts"]
        differences = []
        if v2_reference:
            for layer, key in (("shade", "counts"), ("quality", "quality_counts")):
                assert nonzero(counts[layer]) == nonzero(original[key]), (label, layer)
                ref = Path(original["raster" if layer == "shade" else "quality_raster"])
                for path in sorted((a / layer).glob("*.tif")):
                    differences.append(compare(path, ref, crop=True))
                for path in (a / (layer + ".tif"), a / (layer + ".vrt")):
                    differences.append(compare(path, ref))
        else:
            assert (made["date"], made["time"]) == (original["date"], original["time"])
            assert counts == read(b / "frame.json")["value_counts"], label
            assert read(a / "frame.json")["combinations"] == read(b / "frame.json")["combinations"], label
            names = {p.relative_to(a) for p in a.rglob("*") if p.suffix in (".tif", ".vrt")}
            assert names == {p.relative_to(b) for p in b.rglob("*") if p.suffix in (".tif", ".vrt")}
            differences = [compare(a / name, b / name) for name in sorted(names)]
        frames.append(dict(folder=label, utc_time=made["utc_time"], counts=counts,
                           compared_rasters=len(differences), differing_pixels=sum(differences)))
    jobs = {k: sum(e["metrics"].get(k, 0) for e in actual["engine_events"])
            for k in ("computed", "reused", "horizon_calls")}
    return dict(run_id=actual["run_id"], reference=reference.relative_to(ROOT).as_posix(),
                frames=frames, jobs=jobs, differing_pixels=sum(f["differing_pixels"] for f in frames))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("number", type=int, choices=REF)
    args = parser.parse_args()
    result = run(args.number)
    print(json.dumps(result, indent=2))
    return int(result["differing_pixels"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
