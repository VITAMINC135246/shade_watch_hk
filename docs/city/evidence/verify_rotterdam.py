"""Audit the authorized Rotterdam results, manifests, grids and tags."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/shade_map_g1_dev_20261111"
PROCESSED = ROOT / "data/processed"
LAYERS = {"shade": {0, 1, 255}, "quality": set(range(5)), "surface": {0, 1, 2, 3, 4, 255}}
FORBIDDEN = ("CEDD 2020 LiDAR DSM", "Government of the Hong Kong Special Administrative Region",
             "HKT", "Asia/Hong_Kong")


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def folder(run, frame):
    return run / frame["date"] / frame["time"]


def inspect_grid(path, bounds):
    with rasterio.open(path) as ds:
        assert ds.crs.to_epsg() == 28992, path
        assert ds.res == (.5, .5) and ds.transform.b == ds.transform.d == 0, path
        assert tuple(ds.bounds) == tuple(bounds), path
        assert all(x * 2 == round(x * 2) for x in ds.bounds), path
        assert (ds.width, ds.height) == (round((bounds[2]-bounds[0])/.5), round((bounds[3]-bounds[1])/.5)), path
        assert ds.count == 1 and ds.dtypes == ("uint8",), path
        return ds.tags()


def counts(path):
    with rasterio.open(path) as ds:
        return {str(k): int(v) for k, v in enumerate(np.bincount(ds.read(1).ravel())) if v}


def inspect_run(number, registration, source_line):
    name = f"g1_dev_nl{number}"
    path = OUT / name
    run = read(path / "run_manifest.json")
    plan = read(EVIDENCE / f"nl{number}-plan.json")
    assert run["status"] == "complete" and run["run_id"] == plan["run_id"]
    assert run["city"] == run["identity_document"]["city"] == plan["city"]
    assert run["identity_document"]["publication_format"] == "shade-map-publication-1.1"
    assert run["city"]["ingest_id"] == registration["ingest_id"]
    assert run["city"]["crs"] == "EPSG:28992" and run["city"]["timezone"] == "Europe/Amsterdam"
    assert run["policies"] == {"engine": "SW-V1-POLICY-1.0",
                               "sea": "none" if number == 3 else "SW-SEA-POLICY-2.2"}
    if number != 3:
        assert run["region_config"]["dsm_source"] == "sea-2.2"
        assert run["source_identity"]["view_id"] == registration["view_id"]
    assert len(run["frames"]) == (50 if number == 1 else 3)
    assert all(frame["status"] == "published" for frame in run["frames"])
    assert all((path / filename).is_file() for filename in ("summary.json", "summary.csv", "region_config.json"))
    frame_data = []
    raster_total = 0
    for frame in run["frames"]:
        directory = folder(path, frame)
        record = read(directory / "frame.json")
        assert all(record[k] == frame[k] for k in ("date", "time", "local_time", "utc_time"))
        for layer, codes in LAYERS.items():
            for suffix in (".vrt", ".tif"):
                inspect_grid(directory / (layer + suffix), run["resolved_bounds"])
                raster_total += 1
            for cell in run["cells"]:
                inspect_grid(directory / layer / (cell["id"] + ".tif"), cell["bounds"])
                raster_total += 1
            found = counts(directory / (layer + ".vrt"))
            assert found == record["value_counts"][layer] and set(map(int, found)) <= codes
        if number != 3:
            assert all(not record["value_counts"]["quality"].get(str(code)) for code in (1, 2))
        frame_data.append(dict(local_time=frame["local_time"], utc_time=frame["utc_time"],
                               value_counts=record["value_counts"]))
    work = ROOT / "outputs/shade_map_work" / (name + "-" + run["run_id"][:12])
    engine_total = 0
    for path in work.glob("engine/**/result_index.json"):
        engine = read(path)
        assert engine["grid"]["crs"] == "EPSG:28992"
        assert engine["request"]["local_timezone"] == "Europe/Amsterdam"
        for frame in engine["frames"]:
            for key in ("raster", "quality_raster"):
                tags = inspect_grid(Path(frame[key]), engine["resolved_bounds"])
                assert tags["source_and_owner"] == source_line and tags["timezone"] == "Europe/Amsterdam"
                engine_total += 1
    assert engine_total == len(run["frames"]) * 2
    for path in work.glob("state/*.logical_mosaic.json"):
        assert read(path)["crs"] == "EPSG:28992"
    return run, dict(run_id=run["run_id"], bounds=run["resolved_bounds"],
                     raster_headers=raster_total, engine_tags=engine_total, frames=frame_data)


def inspect_attribution(roots):
    checked = Counter()
    visited = set()
    for root in roots:
        paths = root.rglob("*") if root.is_dir() else (root,)
        for path in paths:
            if path in visited or not path.is_file() or path.is_symlink():
                continue
            visited.add(path)
            if path.suffix == ".tif":
                with rasterio.open(path) as ds:
                    content = json.dumps([ds.tags(), ds.descriptions])
                checked["raster_tags"] += 1
            elif path.suffix in (".json", ".jsonl", ".csv", ".vrt", ".sqlite", ".xml"):
                content = path.read_bytes().decode(errors="replace")
                checked["text_and_state"] += 1
            else:
                continue
            assert all(token not in content for token in FORBIDDEN), path
    return dict(checked)


def inspect_diagnostic(run, result):
    report = read(Path(result["report"]))
    assert report["diagnostic"] and report["policy_run_id"] == run["run_id"]
    assert len(report["frames"]) == result["frames"] == 5
    integrity = read(Path(result["work"]) / "publication-integrity.json")
    assert integrity["before_sha256"] == integrity["after_sha256"]
    rows = []
    for frame in report["frames"]:
        parent = folder(Path(result["report"]).parent, frame)
        path = parent / "dependency.vrt"
        inspect_grid(path, run["resolved_bounds"])
        for cell in run["cells"]:
            inspect_grid(parent / "dependency" / (cell["id"] + ".tif"), cell["bounds"])
        by_code = Counter()
        for group in frame["groups"].values():
            by_code.update({code: n for code, n in group["counts"].items() if n})
        assert counts(path) == dict(by_code)
        rows.append(dict(date=frame["date"], time=frame["time"], dependence_counts=dict(by_code)))
    return dict(frames=rows, protected_publication=integrity, counterfactual_id=report["counterfactual_id"])


def inspect_registration(registration, city):
    catalogue = PROCESSED / "dsm_catalogues/rotterdam" / registration["ingest_id"]
    view = PROCESSED / "dsm_views/sea_fill_v2_2" / registration["view_id"]
    ingest = read(catalogue / "manifest.json")
    filled = read(view / "manifest.json")
    report = read(catalogue / "registration_report.json")
    assert ingest["profile"] == city and ingest["ingest_id"] == registration["ingest_id"]
    assert len(ingest["cells"]) == registration["cells"] == 160
    assert sum(cell["valid_pixels"] for cell in ingest["cells"]) == report["valid_pixels"] == 214_048_125
    assert sum(cell["nodata_pixels"] for cell in ingest["cells"]) == report["nodata_pixels"] == 35_951_875
    assert round(report["minimum_m"], 4) == -10.9959 and round(report["maximum_m"], 4) == 204.6538
    assert report["valid_pixels_below_fill"] == 106_321_205
    assert report["warnings"] == ["fill_above_ground"] and report["h_fill_m"] == 0
    for item in ingest["cells"]:
        assert item["valid_pixels"] + item["nodata_pixels"] == 1250 * 1250
        assert all(x % 625 == 0 for x in item["bounds"])
        with rasterio.open(catalogue / "tiles" / item["name"]) as ds:
            assert ds.shape == (1250, 1250) and ds.res == (.5, .5)
            assert ds.crs.to_epsg() == 28992 and list(ds.bounds) == item["bounds"]
            assert ds.dtypes == ("float32",) and ds.nodata == -9999.0
    rings = Counter()
    inside = Counter()
    for cell in filled["cells"]:
        (inside if cell["supplied"] else rings).update(cell["counts"])
    assert inside["0"] == 214_048_125 and sum(inside[str(x)] for x in (1, 3, 4)) == 35_951_875
    assert rings["4"] == sum(rings.values()) == 156_000_000
    assert filled["totals"]["2"] == 0 and sum(filled["totals"].values()) == 406_000_000
    files = (catalogue / "manifest.json", catalogue / "registration_report.json", view / "manifest.json")
    return catalogue, view, dict(registration_report=report, view_totals=filled["totals"],
                                 supplied=dict(inside), ring=dict(rings),
                                 manifest_file_hashes={p.relative_to(ROOT).as_posix(): digest(p) for p in files},
                                 versions={"ingestion": ingest["versions"], "view": filled["versions"]})


def main():
    city = read(ROOT / "config/cities/rotterdam.json")
    registration = read(EVIDENCE / "nl0-registration.json")
    catalogue, view, registration_report = inspect_registration(registration, city)
    runs, results = zip(*(inspect_run(i, registration, city["dsm_source_line"]) for i in (1, 2, 3)))
    summer, winter = (list(f["local_time"] for f in results[0]["frames"] if f["local_time"].startswith(day))
                      for day in ("2026-06-21", "2026-12-22"))
    assert len(summer) == 34 and summer[0][11:16] == "05:30" and summer[-1][11:16] == "22:00"
    assert len(winter) == 16 and winter[0][11:16] == "09:00" and winter[-1][11:16] == "16:30"
    assert all(t.endswith("+02:00") for t in summer) and all(t.endswith("+01:00") for t in winter)
    assert [datetime.fromisoformat(f["utc_time"]).strftime("%H:%M") for f in runs[1]["frames"]] == [
        "07:00", "11:40", "16:00"]
    noon = read(OUT / "g1_dev_nl2/20260621/1340/frame.json")["solar_by_tile"]
    assert noon and all(175 <= s["azimuth_deg"] <= 185 and 61 <= s["apparent_elevation_deg"] <= 62 for s in noon)
    projection = read(EVIDENCE / "nl2-plan.json")["projection"]
    assert projection["operation"] and projection["pyproj_version"] and projection["proj_version"]
    edge = read(EVIDENCE / "nl5-edge-plan.json")
    inner = read(EVIDENCE / "nl1-plan.json")
    assert edge["fill_context"]["no_dsm_cells_within_1km"] > 0
    assert "no_dsm_cells_within_1km" in edge["warnings"]
    assert inner["fill_context"]["no_dsm_cells_within_1km"] == 0
    dst = read(EVIDENCE / "nl5-dst-plan.json")["frames"]
    offsets = {}
    for day, offset in [("2026-03-28", "+01:00"), ("2026-03-29", "+02:00"),
                        ("2026-10-24", "+02:00"), ("2026-10-25", "+01:00")]:
        local = [f["local_time"] for f in dst if f["local_time"].startswith(day)]
        assert local and all(t.endswith(offset) for t in local)
        offsets[day] = dict(offset=offset, frames=len(local), first=local[0], last=local[-1])
    diag_result = read(EVIDENCE / "nl4-result.json")
    diagnostic = inspect_diagnostic(runs[0], diag_result)
    cache = PROCESSED / "shade_v1"
    roots = [catalogue, catalogue.parent / "current.json", view,
             view.parent / "current-nl_rotterdam_dsm05.json", Path(diag_result["work"]),
             Path(diag_result["report"]).parent, cache / ("sea_fill_v2_2_" + registration["view_id"][:12]),
             cache / ("sea2_2_fill_impact_" + diagnostic["counterfactual_id"][:12])]
    roots.extend(cache.glob("g1_dev_raw_*_rotterdam"))
    for run in runs:
        work = ROOT / "outputs/shade_map_work" / (run["name"] + "-" + run["run_id"][:12])
        source_view = Path(read(work / "adapter/region_request.json")["source_directory"])
        roots.extend([OUT / run["name"], work, source_view])
    checked = inspect_attribution(roots)
    print(json.dumps(dict(registration=registration_report, runs=results, diagnostic=diagnostic,
                          projection=projection, noon=noon, dst=offsets,
                          edge_fill_context=edge["fill_context"], attribution_files_checked=checked), indent=2))


if __name__ == "__main__":
    main()
