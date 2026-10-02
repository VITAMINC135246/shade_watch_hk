"""V1 contract tests; fixtures and NumPy oracle are independent of production."""
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src import v1
from src.horizon import pixel_centred_horizon
from src.shade_watch import classify
from src.spatial import digest_file, read_window
from src.v1_cache import (canonical_origin, diagnostic_horizon, entry_paths, exclusive_lock,
                          spatial_identity, tile_grid, valid_entry)
from v1_oracle import ray_oracle, classification_oracle, meeus_solar


@pytest.fixture
def scene(tmp_path, monkeypatch):
    monkeypatch.setattr(v1, "ROOT", tmp_path)
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    rng = np.random.default_rng(20261002)
    heights = rng.uniform(0, 2, (32, 70)).astype(np.float32)
    heights[12:18, 30:39] = 28
    heights[4:6, 5:8] = -9999
    for c in (0, 35):
        with rasterio.open(raw / f"tile_{c}.tif", "w", driver="GTiff", width=35, height=32,
                           count=1, dtype="float32", crs="EPSG:2326", nodata=-9999,
                           transform=from_origin(800000 + c * .5, 820000, .5, .5)) as ds:
            ds.write(heights[:, c:c + 35], 1)
    return raw


def request(scene, name="query", **kwargs):
    return v1.plan_shade(dsm_dir=scene, output_dir=f"outputs/{name}", **kwargs)


def arrays(result, index=0):
    frame = result.frames[index]
    with rasterio.open(frame["raster"]) as ds, rasterio.open(frame["quality_raster"]) as qs:
        return ds.read(1), qs.read(1)


def test_planner_zero_horizons_and_writes_and_model_validation(scene):
    before = set(scene.parent.parent.rglob("*"))
    with patch("src.v1_cache.pixel_centred_horizon", side_effect=AssertionError("planning computed")):
        plan = request(scene, tile="tile_0.tif", instants=["2026-01-07T14:31:27+08:00"])
    assert plan.resources["missing_direction_jobs"] == 1
    assert set(scene.parent.parent.rglob("*")) == before
    assert plan.grid.bounds() == (800000, 819984, 800017.5, 820000)
    assert plan.tiles[0].reference["easting_m"] == 800008.75
    for kwargs in ({}, {"instants": [], "dates": []}, {"instants": []},
                   {"instants": ["2026-01-07"]}, {"instants": ["2026-02-29T12:00"]},
                   {"instants": ["2026-01-07T12:00"], "workers": 2}):
        with pytest.raises(ValueError):
            request(scene, tile="tile_0.tif", **kwargs)


def test_exact_seconds_timezone_leap_and_daylight(scene):
    kwargs = dict(tile="tile_0.tif")
    first = request(scene, "hkt", instants=["2024-02-29T14:31:27.123456+08:00"], **kwargs)
    second = request(scene, "utc", instants=["2024-02-29T06:31:27.123456Z"], **kwargs)
    assert first.request.instants[0].utc == second.request.instants[0].utc
    assert first.tiles[0].solar == second.tiles[0].solar
    third = request(scene, "seconds", instants=["2024-02-29T14:31:28.123456+08:00"], **kwargs)
    assert first.tiles[0].solar != third.tiles[0].solar
    result = v1.run_shade(first)
    result2 = v1.run_shade(second)
    assert result2.jobs["horizon_calls"] == 0
    assert all(np.array_equal(a, b) for a, b in zip(arrays(result), arrays(result2)))
    assert result.frames[0]["requested_time"] == first.request.instants[0].requested
    days = request(scene, "dates", dates=["2026-03-20", "2026-06-21"], interval_minutes=240, **kwargs)
    assert len({t.local[:10] for t in days.request.instants}) == 2
    assert all(datetime.fromisoformat(t.local).minute == 0 for t in days.request.instants)
    with pytest.raises(ValueError, match="Duplicate physical"):
        request(scene, instants=["2024-02-29T14:31:27+08:00", "2024-02-29T06:31:27Z"], **kwargs)


@pytest.mark.parametrize("stamp", ["2026-11-01T01:30:00", "2026-03-08T02:30:00"])
def test_dst_ambiguity_and_nonexistent_are_rejected(stamp):
    with pytest.raises(ValueError, match="Ambiguous or nonexistent"):
        v1.normalize_instant(stamp, "America/New_York")
    assert v1.normalize_instant(stamp + "-04:00").utc


def test_spatial_odd_crop_composition_invariance_and_custom(scene):
    at = ["2026-01-07T14:31:27+08:00"]
    solo = request(scene, "alone", tile="tile_0.tif", instants=at)
    full = v1.run_shade(solo)
    combined = v1.run_shade(request(scene, "combined", tiles=["tile_0.tif", "tile_35.tif"], instants=at))
    assert combined.jobs["computed"] == 1 and combined.jobs["reused"] == 1
    odd = v1.run_shade(request(scene, "odd", tile="tile_0.tif", instants=at, crop=(3, 5, 17, 13)))
    custom = v1.run_shade(request(scene, "custom", instants=at, mode="custom",
                                 bounds=(800001.51, 819990.04, 800010., 819997.49)))
    for a, b, c, d in zip(arrays(full), arrays(combined), arrays(odd), arrays(custom)):
        assert np.array_equal(a, b[:, :35])
        assert np.array_equal(a[5:18, 3:20], c)
        assert np.array_equal(a[5:20, 3:20], d)
    assert odd.jobs["horizon_calls"] == custom.jobs["horizon_calls"] == 0
    records = v1.index_sources(scene)
    whole = diagnostic_horizon(records, records[0], (0, 0, 35, 32), 90)
    part = diagnostic_horizon(records, records[0], (3, 5, 17, 13), 90)
    for a, b in zip(whole, part):
        assert np.array_equal(a[5:18, 3:20], b, equal_nan=True)
    unknown = v1.run_shade(request(scene, "outside", instants=at, mode="custom",
                                  bounds=(799999., 819997., 800002., 820001.)))
    assert np.all(arrays(unknown)[0][:2] == 255) and np.all(arrays(unknown)[1][:2] == 1)
    with pytest.raises(ValueError, match="missing"):
        request(scene, tile="absent.tif", instants=at)
    with pytest.raises(ValueError, match="distinct"):
        request(scene, tiles=["tile_0.tif", "tile_0.tif"], instants=at)


def test_coordinate_selector_preserved_and_native_center(scene):
    with patch("src.spatial.Transformer.from_crs") as transform:
        transform.return_value.transform.return_value = (800002., 819999.)
        plan = request(scene, latitude=22.3, longitude=114.2, instants="2026-01-07T12:00")
    assert plan.request.selector == (22.3, 114.2)
    assert plan.grid.bounds() == (800000., 819984., 800017.5, 820000.)
    assert plan.tiles[0].reference["easting_m"] == 800008.75


def test_analytic_oracle_and_missing_equality_night():
    dsm = np.zeros((40, 40), np.float32)
    rows, cols = np.array([20]), np.array([20])
    assert ray_oracle(dsm, rows, cols, 90, radius=5)[0][0] == 0
    dsm[20, 24] = 20
    ref = ray_oracle(dsm, rows, cols, 90, radius=5)
    assert ref[0][0] == pytest.approx(np.degrees(np.arctan(20 / 1.75)))
    dsm[20, 26] = np.nan
    assert ray_oracle(dsm, rows, cols, 90, radius=5)[1][0] == 0
    horizons = np.array([[45., 0., np.nan, 10., 10.]])
    support = np.array([[0, 0, 0, 1, 1]], np.uint8)
    for elevation in (-1., 0., 10., 10.0002, 44.9998, 45., 45.0002):
        got = classify(horizons, support.astype(bool), np.isfinite(horizons), elevation, 10.)
        ref = classification_oracle(horizons, support, elevation, 10.)
        assert all(np.array_equal(a, b) for a, b in zip(got, ref))
    assert classify(horizons, support.astype(bool), np.isfinite(horizons), 20, 10)[0][0, 0] == 1
    assert classify(horizons, support.astype(bool), np.isfinite(horizons), 20, 10)[1][0, 1] == 2


@pytest.mark.parametrize("azimuth", [0., 45., 90., 92.37, 135., 215., 267.51, 315.])
def test_independent_ray_exact_direction_support_and_binary(azimuth):
    rng = np.random.default_rng(27)
    dsm = rng.uniform(0, 30, (71, 73)).astype(np.float32)
    dsm[20:23, 41:43] = np.nan
    rows = np.array([35, 36, 21, 1, 69])
    cols = np.array([35, 36, 41, 1, 71])
    got = pixel_centred_horizon(dsm, rows, cols, azimuth, 12., 12., .5, -13, 17)
    ref = ray_oracle(dsm, rows, cols, azimuth, radius=12., origin_row=-13, origin_col=17)
    assert np.array_equal(np.isfinite(got[0]), np.isfinite(ref[0]))
    assert np.max(np.abs(got[0][np.isfinite(got[0])] - ref[0][np.isfinite(ref[0])])) <= 1e-4
    assert np.array_equal(got[1], ref[1])
    assert np.array_equal(got[2], ref[2])
    for elevation in (0., 5., 20., 45., 89.):
        prod = classify(got[0], got[1].astype(bool), np.isfinite(got[0]), elevation, 15.)
        independent = classification_oracle(ref[0], ref[1], elevation, 15.)
        equality = np.isfinite(ref[0]) & (np.abs(ref[0] - elevation) <= 1e-4)
        assert all(np.array_equal(a[~equality], b[~equality]) for a, b in zip(prod, independent))


def test_dependency_add_remove_change_distant_mask_corruption_relocation(scene):
    at = "2026-01-07T14:31:27+08:00"
    base = request(scene, "base", tile="tile_0.tif", instants=at)
    result = v1.run_shade(base)
    original = base.tiles[0].spatial_key
    with rasterio.open(scene / "distant.tif", "w", driver="GTiff", width=4, height=4,
                       count=1, dtype="float32", crs="EPSG:2326", transform=from_origin(900000, 920000, .5, .5)) as ds:
        ds.write(np.zeros((4, 4), np.float32), 1)
    unrelated = request(scene, "unrelated", tile="tile_0.tif", instants=at)
    assert unrelated.tiles[0].spatial_key == original
    assert v1.run_shade(unrelated).jobs["computed"] == 0
    changed = scene / "tile_35.tif"
    original_bytes = changed.read_bytes()
    with rasterio.open(changed, "r+") as ds:
        ds.write(np.full((32, 35), 90, np.float32), 1)
    assert request(scene, tile="tile_0.tif", instants=at).tiles[0].spatial_key != original
    assert v1.run_shade(request(scene, "changed", tile="tile_0.tif", instants=at)).jobs["computed"] == 1
    with pytest.raises(ValueError, match="dependencies changed"):
        v1.run_shade(base)
    changed.unlink()
    removed = request(scene, tile="tile_0.tif", instants=at).tiles[0].spatial_key
    assert removed != original
    assert v1.run_shade(request(scene, "removed", tile="tile_0.tif", instants=at)).jobs["computed"] == 1
    changed.write_bytes(original_bytes)
    assert request(scene, tile="tile_0.tif", instants=at).tiles[0].spatial_key == original
    assert v1.run_shade(request(scene, "restored", tile="tile_0.tif", instants=at)).jobs["computed"] == 0
    moved = scene.parent / "relocated"
    shutil.copytree(scene, moved)
    assert v1.plan_shade(dsm_dir=moved, tile="tile_0.tif", instants=at).tiles[0].spatial_key == original
    path, status = entry_paths(base.cache_directory, original, base.tiles[0].directions[0])
    path.write_bytes(b"corrupted")
    repair = v1.run_shade(request(scene, "repair", tile="tile_0.tif", instants=at))
    assert repair.jobs["computed"] == 1
    assert valid_entry(base.cache_directory, original, base.tiles[0].directions[0], base.tiles[0].source)
    status.write_text("null")
    assert valid_entry(base.cache_directory, original, base.tiles[0].directions[0], base.tiles[0].source) is None
    assert v1.run_shade(request(scene, "invalidmanifest", tile="tile_0.tif", instants=at)).jobs["computed"] == 1
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(changed, "r+") as ds:
            mask = np.full((32, 35), 255, np.uint8)
            mask[0, 0] = 0
            ds.write_mask(mask)
    assert request(scene, tile="tile_0.tif", instants=at).tiles[0].spatial_key != original
    records = v1.index_sources(scene)
    with patch("src.v1_cache.ALGORITHM", "new-numerical-settings"):
        assert spatial_identity(records, records[0])[0] != original


def test_cross_date_reuse_new_direction_and_final_hit(scene):
    first = request(scene, "first", tile="tile_0.tif", instants="2026-01-07T14:31:27+08:00")
    result = v1.run_shade(first)
    same = request(scene, "otherdate", tile="tile_0.tif", instants="2026-01-08T14:31:27+08:00")
    assert first.tiles[0].directions == same.tiles[0].directions
    with patch("src.v1_cache.pixel_centred_horizon", side_effect=AssertionError("did not reuse")):
        assert v1.run_shade(same).jobs["computed"] == 0
        hit = v1.run_shade(first)
    assert hit.jobs["final_result_hits"] == 1 and hit.jobs["horizon_calls"] == 0
    missing = request(scene, "newdir", tile="tile_0.tif", instants=["2026-01-07T14:31:27+08:00", "2026-01-07T08:17:23+08:00"])
    new = v1.run_shade(missing)
    assert new.jobs["computed"] == 1 and new.jobs["reused"] == 1
    result_path = Path(result.frames[0]["raster"])
    old_hash = digest_file(result_path)
    result_path.write_bytes(b"bad result")
    repaired = v1.run_shade(first)
    assert repaired.jobs["final_result_hits"] == 0 and repaired.jobs["computed"] == 0
    assert digest_file(result_path) == old_hash


def test_cache_conflicting_writers_and_interruption_resume(scene):
    plan = request(scene, "interrupted", tile="tile_0.tif",
                   instants=["2026-01-07T08:17:23+08:00", "2026-01-07T14:31:27+08:00"])
    with exclusive_lock(Path(plan.cache_directory) / plan.tiles[0].spatial_key / ".writer.lock"):
        with pytest.raises(RuntimeError, match="Another V1 writer"):
            v1.run_shade(plan)
    # A real child exits immediately after the first atomic completed entry.
    code = ("from pathlib import Path; import os; from src import v1; "
            f"v1.ROOT=Path({str(scene.parent.parent)!r}); "
            f"p=v1.plan_shade(dsm_dir={str(scene)!r},tile='tile_0.tif',output_dir='outputs/interrupted',"
            "instants=['2026-01-07T08:17:23+08:00','2026-01-07T14:31:27+08:00']); "
            "v1.run_shade(p,on_direction=lambda e: os._exit(19))")
    process = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert process.returncode == 19, process.stderr
    completed = [d for d in plan.tiles[0].directions if valid_entry(plan.cache_directory, plan.tiles[0].spatial_key, d, plan.tiles[0].source)]
    assert len(completed) == 1
    # Leave a partial artifact for the other direction, then restart.
    missing = next(d for d in plan.tiles[0].directions if d not in completed)
    p, status = entry_paths(plan.cache_directory, plan.tiles[0].spatial_key, missing)
    p.write_bytes(b"incomplete"); status.write_text('{"status":"running"}')
    restarted = v1.run_shade(plan)
    assert restarted.jobs["computed"] == 1 and restarted.jobs["reused"] == 1


def test_outputs_media_and_night(scene):
    plan = request(scene, "media", tile="tile_0.tif", jpg=True, mp4=True,
                   instants=["2026-01-07T14:31:27+08:00", "2026-01-07T02:11:09+08:00"])
    result = v1.run_shade(plan)
    data = json.loads(Path(result.index_path).read_text())
    assert data["media"]["frames"] == 2 and len(data["media"]["jpg"]) == 2
    assert data["media"]["frame_times"] == [i.utc for i in plan.request.instants]
    with rasterio.open(result.frames[0]["raster"]) as ds:
        assert ds.crs.to_string() == "EPSG:2326" and ds.nodata == 255 and ds.transform == plan.grid.affine
        assert ds.tags()["requested_time"].endswith("14:31:27+08:00")
    labels, quality = arrays(result, 1)
    assert np.all(labels == 255) and set(np.unique(quality)) == {1, 4}


def test_public_api_flat_known_blocker_missing_support_and_target(scene):
    from src.solar import Sun
    (scene / "tile_35.tif").unlink()  # sunward footprint is deliberately unavailable
    flat = np.zeros((32, 35), np.float32)
    flat[0, 0] = -9999
    with rasterio.open(scene / "tile_0.tif", "r+") as ds:
        ds.write(flat, 1)
    with patch("src.v1.position", return_value=Sun(90., 20., 20.)):
        result = v1.run_shade(request(scene, "flat_missing", tile="tile_0.tif", instants="2026-01-07T12:00"))
    labels, quality = arrays(result)
    assert labels[15, 10] == 255 and quality[15, 10] == 2
    assert labels[0, 0] == 255 and quality[0, 0] == 1
    flat[15, 14] = 30
    with rasterio.open(scene / "tile_0.tif", "r+") as ds:
        ds.write(flat, 1)
    with patch("src.v1.position", return_value=Sun(90., 20., 20.)):
        result = v1.run_shade(request(scene, "blocked_missing", tile="tile_0.tif", instants="2026-01-07T12:00"))
    labels, quality = arrays(result)
    assert labels[15, 10] == 1 and quality[15, 10] == 0
    assert labels[16, 10] == 255 and quality[16, 10] == 2


def test_actual_model_apparent_horizon_crossing(scene):
    from datetime import timedelta, date
    plan = request(scene, tile="tile_0.tif", instants="2026-01-07T12:00")
    ref = plan.tiles[0].reference
    sunrise, _ = v1.daylight_bounds(date(2026, 1, 7), ref["latitude"], ref["longitude"])
    lo, hi = sunrise - timedelta(minutes=10), sunrise + timedelta(minutes=10)
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        if v1.position(mid, ref["latitude"], ref["longitude"]).apparent_elevation_deg <= 0:
            lo = mid
        else:
            hi = mid
    stamps = [lo - timedelta(seconds=1), hi + timedelta(seconds=1)]
    boundary = request(scene, "solar_horizon", tile="tile_0.tif", instants=stamps)
    assert boundary.tiles[0].solar[0]["apparent_elevation_deg"] < 0
    assert boundary.tiles[0].solar[1]["apparent_elevation_deg"] > 0
    result = v1.run_shade(boundary)
    assert set(np.unique(arrays(result, 0)[1])) == {1, 4}
    assert 4 not in np.unique(arrays(result, 1)[1])


def test_legacy_outputs_protected_and_changed_plan(scene):
    plan = request(scene, tile="tile_0.tif", instants="2026-01-07T12:00")
    out = Path(plan.output_directory)
    out.mkdir(parents=True)
    (out / "historical.txt").write_text("preserve")
    with pytest.raises(ValueError, match="Unmanaged"):
        v1.run_shade(plan)
    (out / "historical.txt").unlink()
    with pytest.raises(ValueError, match="Plan/code was changed"):
        v1.run_shade(replace(plan, key="tampered"))


def test_direction_narrow_blocker_and_solar_reference_is_distinct():
    # One-cell blocker on an azimuth between finite bins: both can miss it.
    dsm = np.zeros((601, 601), np.float32)
    dsm[110, 319] = 60
    azimuth = np.degrees(np.arctan2(19, 190))
    rows = np.array([300]); cols = np.array([300])
    exact = ray_oracle(dsm, rows, cols, azimuth, radius=200)[0][0]
    baseline = ray_oracle(dsm, rows, cols, v1.direction_for(azimuth, "nearest5"), radius=200)[0][0]
    candidate = ray_oracle(dsm, rows, cols, v1.direction_for(azimuth, "nearest2_5"), radius=200)[0][0]
    assert exact > 20 and baseline == candidate == 0
    instant = datetime.fromisoformat("2026-01-07T14:31:27+08:00")
    centre = v1.position(instant, 22.3, 114.2)
    independent = meeus_solar(instant, 22.3, 114.2)
    assert abs(centre.geometric_elevation_deg - independent[1]) > .001
