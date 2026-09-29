"""NOAA fractional-year approximation for solar geometry (not author code)."""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")


@dataclass(frozen=True)
class Sun:
    azimuth_deg: float  # Clockwise from true north, toward the Sun.
    geometric_elevation_deg: float  # Degrees above astronomical horizon.
    apparent_elevation_deg: float  # Geometric elevation plus NOAA refraction.

    @property
    def zenith_deg(self) -> float:
        return 90.0 - self.apparent_elevation_deg


def position(instant: datetime, latitude: float, longitude: float) -> Sun:
    """Solar centre at an aware instant; longitude is positive eastward."""
    if instant.tzinfo is None:
        raise ValueError("Solar time must have a time zone")
    utc = instant.astimezone(timezone.utc)
    days = 366 if calendar.isleap(utc.year) else 365
    hour = utc.hour + utc.minute / 60 + utc.second / 3600 + utc.microsecond / 3.6e9
    gamma = 2 * math.pi / days * (utc.timetuple().tm_yday - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (
        0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
    )
    true_minutes = (hour * 60 + eqtime + 4 * longitude) % 1440
    hour_angle = math.radians(true_minutes / 4 - 180)
    lat = math.radians(latitude)
    sin_elevation = (
        math.sin(lat) * math.sin(decl)
        + math.cos(lat) * math.cos(decl) * math.cos(hour_angle)
    )
    geometric = math.degrees(math.asin(max(-1.0, min(1.0, sin_elevation))))
    azimuth = (
        math.degrees(math.atan2(
            math.sin(hour_angle),
            math.cos(hour_angle) * math.sin(lat) - math.tan(decl) * math.cos(lat),
        )) + 180
    ) % 360
    if geometric > 85:
        correction = 0.0
    elif geometric > 5:
        tangent = math.tan(math.radians(geometric))
        correction = (58.1 / tangent - 0.07 / tangent**3 + 0.000086 / tangent**5) / 3600
    elif geometric > -0.575:
        e = geometric
        correction = (1735 - 518.2 * e + 103.4 * e**2 - 12.79 * e**3 + 0.711 * e**4) / 3600
    else:
        correction = -20.774 / math.tan(math.radians(geometric)) / 3600
    return Sun(azimuth, geometric, geometric + correction)


def daylight_bounds(day: date, latitude: float, longitude: float) -> tuple[datetime, datetime]:
    """Sunrise/sunset when geometric solar-centre elevation crosses -0.833°.

    NOAA's -0.833° includes typical refraction and the solar disk radius.
    The model does not account for the local DSM horizon or weather.
    """
    start = datetime(day.year, day.month, day.day, tzinfo=HKT)
    times = [start + timedelta(minutes=2 * i) for i in range(721)]
    values = [position(t, latitude, longitude).geometric_elevation_deg + 0.833 for t in times]
    crossings = []
    for i in range(len(values) - 1):
        if values[i] * values[i + 1] < 0:
            lo, hi = times[i], times[i + 1]
            sign = values[i] > 0
            for _ in range(28):
                mid = lo + (hi - lo) / 2
                if (position(mid, latitude, longitude).geometric_elevation_deg + 0.833 > 0) == sign:
                    lo = mid
                else:
                    hi = mid
            crossings.append(lo + (hi - lo) / 2)
    if len(crossings) != 2:
        raise ValueError(f"Expected one sunrise and sunset on {day}; got {len(crossings)}")
    return crossings[0], crossings[1]


def daylight_samples(sunrise: datetime, sunset: datetime, minutes: int = 10) -> list[datetime]:
    """Clock-aligned samples inside actual daylight; no nighttime frames."""
    midnight = sunrise.replace(hour=0, minute=0, second=0, microsecond=0)
    step = timedelta(minutes=minutes)
    index = math.ceil((sunrise - midnight) / step)
    output = []
    t = midnight + index * step
    while t <= sunset:
        output.append(t)
        t += step
    return output
