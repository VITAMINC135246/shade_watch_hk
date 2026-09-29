from datetime import date, datetime, timezone

import numpy as np
import pytest
import rasterio
from rasterio.merge import merge
from rasterio.transform import from_origin
from zoneinfo import ZoneInfo

from src.horizon import _scan_columns, direct_ray_reference, horizon_at_output, pixel_centred_horizon
from src.shade_watch import (OUTPUT_HEIGHT_PX, OUTPUT_WIDTH_PX, classify,
                             load_study_area, nearest_bin, parse_coordinate,
                             presentation_frame)
from src.solar import daylight_bounds, daylight_samples, position


def test_config_dms_and_required_date():
    area = load_study_area()
    assert area["latitude"] == pytest.approx(22.34011333333333)
    assert area["longitude"] == pytest.approx(114.26332333333333)
    assert area["date"] == date(2026, 1, 7)
    assert parse_coordinate("22.5") == 22.5


def test_hull_matches_brute_profiles_with_missing_cells():
    rng = np.random.default_rng(2)
    for _ in range(70):
        z = rng.normal(size=80).astype(np.float32)
        z[rng.random(len(z)) < .1] = np.nan
        got, support, _ = _scan_columns(z[None, :], 10)
        for i in range(len(z)):
            if not np.isfinite(z[i]):
                assert np.isnan(got[0, i])
                continue
            expected = max([0.0] + [float((z[j] - z[i]) / ((i - j) * .5))
                                    for j in range(i) if np.isfinite(z[j])])
            assert got[0, i] == pytest.approx(expected, abs=1e-5)
            if i >= 10:
                assert bool(support[0, i]) == bool(np.all(np.isfinite(z[i - 10:i])))


def test_flat_dsm_and_east_building_casts_west():
    flat = np.zeros((240, 240), dtype=np.float32)
    e = np.zeros((1, 1), dtype=np.float32)
    n = np.zeros((1, 1), dtype=np.float32)
    horizon, supported, _ = horizon_at_output(flat, 90, e, n, support_m=25)
    assert horizon[0, 0] == pytest.approx(0, abs=1e-6)
    assert supported[0, 0]
    labels, _ = classify(horizon, supported, np.ones((1, 1), bool), 30, 0)
    assert labels[0, 0] == 0

    flat[116:124, 136:144] = 20
    east_horizon, east_support, _ = horizon_at_output(flat, 90, e, n, support_m=25)
    west_horizon, _, _ = horizon_at_output(flat, 270, e, n, support_m=25)
    assert east_horizon[0, 0] > 45
    assert west_horizon[0, 0] == pytest.approx(0, abs=1e-6)
    assert classify(east_horizon, east_support, np.ones((1, 1), bool), 45, 0)[0][0, 0] == 1
    reference, _ = direct_ray_reference(flat, np.array([120]), np.array([120]), 90.0, 30)
    assert reference[0] > 45


def test_slope_and_nodata_support():
    dsm = np.zeros((240, 240), dtype=np.float32)
    # Eastward rise: at 10 m horizontal range the surface is 10 m higher.
    dsm += np.maximum(np.arange(240)[None, :] - 120, 0).astype(np.float32) * .5
    e = np.zeros((1, 1), dtype=np.float32)
    n = np.zeros((1, 1), dtype=np.float32)
    horizon, supported, _ = horizon_at_output(dsm, 90, e, n, support_m=25)
    assert 40 < horizon[0, 0] < 50
    assert supported[0, 0]
    dsm[120, 140] = np.nan
    horizon, supported, _ = horizon_at_output(dsm, 90, e, n, support_m=25)
    assert not supported[0, 0]
    # A known blocker proves shade despite a more distant missing cell.
    assert classify(horizon, supported, np.ones((1, 1), bool), 20, 0)[0][0, 0] == 1
    # Without the blocker, missing upstream coverage cannot prove sunlit.
    dsm[:] = 0
    dsm[120, 140] = np.nan
    horizon, supported, _ = horizon_at_output(dsm, 90, e, n, support_m=25)
    assert classify(horizon, supported, np.ones((1, 1), bool), 20, 0)[0][0, 0] == 255


def test_rectangular_grid_rotation_and_native_pixel_presentation():
    dsm = np.zeros((240, 300), dtype=np.float32)
    dsm[117:123, 169:174] = 20.0
    e = np.zeros((1, 1), dtype=np.float32)
    n = np.zeros((1, 1), dtype=np.float32)
    east_horizon, supported, _ = horizon_at_output(dsm, 90, e, n, support_m=25)
    west_horizon, _, _ = horizon_at_output(dsm, 270, e, n, support_m=25)
    assert supported[0, 0] and east_horizon[0, 0] > 45
    assert west_horizon[0, 0] == pytest.approx(0, abs=1e-6)

    labels = np.zeros((OUTPUT_HEIGHT_PX, OUTPUT_WIDTH_PX), dtype=np.uint8)
    labels[0, 0] = 1
    labels[0, 1] = 255
    instant = datetime(2026, 1, 7, 14, 30, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    sun = position(instant, 22.34011333333333, 114.26332333333333)
    sunrise, sunset = daylight_bounds(instant.date(), 22.34011333333333, 114.26332333333333)
    frame = presentation_frame(labels, instant, sun, 1.0, sunrise=sunrise, sunset=sunset)
    assert frame.size == (1536, 1088)
    assert frame.getpixel((32, 108)) == (0, 0, 0)
    assert frame.getpixel((33, 108)) == (160, 160, 160)
    assert frame.getpixel((34, 108)) == (255, 255, 255)


def test_solar_direction_time_zone_and_daylight():
    hkt = ZoneInfo("Asia/Hong_Kong")
    lat, lon = 22.34011333333333, 114.26332333333333
    morning = position(datetime(2026, 1, 7, 9, 0, tzinfo=hkt), lat, lon)
    noon = position(datetime(2026, 1, 7, 12, 30, tzinfo=hkt), lat, lon)
    afternoon = position(datetime(2026, 1, 7, 15, 0, tzinfo=hkt), lat, lon)
    assert 90 < morning.azimuth_deg < 180
    assert 170 < noon.azimuth_deg < 200
    assert 180 < afternoon.azimuth_deg < 270
    assert position(datetime(2026, 1, 7, 1, 0, tzinfo=timezone.utc), lat, lon) == morning
    sunrise, sunset = daylight_bounds(date(2026, 1, 7), lat, lon)
    assert sunrise.hour == 7 and sunset.hour == 17
    samples = daylight_samples(sunrise, sunset)
    assert all(sunrise <= t <= sunset and t.tzinfo == hkt for t in samples)
    assert all((b - a).total_seconds() == 600 for a, b in zip(samples, samples[1:]))
    with pytest.raises(ValueError):
        position(datetime(2026, 1, 7, 9, 0), lat, lon)


def test_azimuth_bins_do_not_clamp_outside_paper_range():
    assert nearest_bin(113.2) == 115
    assert nearest_bin(39.0) == 40
    assert nearest_bin(2.0) == 0
    assert nearest_bin(358.0) == 0


def test_isolated_building_shadow_length_and_slope():
    dsm = np.zeros((400, 400), dtype=np.float32)
    dsm[198:203, 200:202] = 20.0  # 20 m obstacle at/just east of centre.
    rows = np.array([200, 200, 200], dtype=np.int32)
    cols = np.array([170, 145, 225], dtype=np.int32)  # 15 m W, 27.5 m W, 12.5 m E.
    horizon, support, _ = pixel_centred_horizon(dsm, rows, cols, 90.0, 40.0, 30.0)
    assert np.all(support)
    assert horizon[0] > 45  # 20 m obstacle casts at least 15 m west at 45°.
    assert horizon[1] < 45  # Its shadow ends before 27.5 m west.
    assert horizon[2] == pytest.approx(0)  # East is sunward, not down-shadow.
    # A northward rise is visible from the north but not from the south.
    slope = np.zeros((400, 400), dtype=np.float32)
    slope[:200, :] = np.arange(200, 0, -1, dtype=np.float32)[:, None] * .5
    north, _, _ = pixel_centred_horizon(slope, np.array([205]), np.array([200]), 0.0, 60, 30)
    south, _, _ = pixel_centred_horizon(slope, np.array([205]), np.array([200]), 180.0, 60, 30)
    assert north[0] > south[0]


def test_cross_tile_blocker_and_nodata(tmp_path):
    left = np.zeros((100, 100), dtype=np.float32)
    right = np.zeros((100, 100), dtype=np.float32)
    right[48:53, 2:4] = 12.0  # Blocker in adjacent eastern tile.
    paths = [tmp_path / "west.tif", tmp_path / "east.tif"]
    for path, arr, west in zip(paths, [left, right], [0, 50]):
        with rasterio.open(path, "w", driver="GTiff", width=100, height=100,
                           count=1, dtype="float32", crs="EPSG:2326",
                           transform=from_origin(west, 50, .5, .5), nodata=-9999.0) as ds:
            ds.write(arr, 1)
    opened = [rasterio.open(path) for path in paths]
    try:
        mosaic, _ = merge(opened, nodata=-9999.0)
    finally:
        for ds in opened:
            ds.close()
    h, support, _ = pixel_centred_horizon(mosaic[0], np.array([50]), np.array([95]), 90.0, 20, 10)
    assert h[0] > 30 and support[0]
    mosaic[0, 50, 99] = np.nan
    h, support, _ = pixel_centred_horizon(mosaic[0], np.array([50]), np.array([95]), 90.0, 20, 10)
    assert h[0] > 30 and not support[0]
