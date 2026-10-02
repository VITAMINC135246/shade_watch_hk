"""Independent NumPy ray/classification oracle; no production scientific calls.

Shared assumptions: native DSM, 0.25 m nominal steps, ties-to-even projected
addresses, 1 km radial boundary. This is numerical evidence, not observations.
"""
import math
import numpy as np


def ray_oracle(dsm, rows, cols, azimuth, *, radius=1000., resolution=.5,
               origin_row=0, origin_col=0):
    dr, dc = -math.cos(math.radians(azimuth)), math.sin(math.radians(azimuth))
    if abs(dr) < 1e-14:
        dr = 0.
    if abs(dc) < 1e-14:
        dc = 0.
    count = math.floor(radius / .25 + 1e-10)
    step = np.arange(1, count + 1, dtype=np.float64)
    nominal = step * .25
    answers, complete, blockers = [], [], []
    for row, col in zip(rows, cols):
        height = dsm[row, col]
        if not np.isfinite(height):
            answers.append(np.nan)
            complete.append(0)
            blockers.append(0.)
            continue
        rp, cp = (row + origin_row) % 2, (col + origin_col) % 2
        rd = np.rint(rp + dr * step * .25 / resolution).astype(np.int64) - rp
        cd = np.rint(cp + dc * step * .25 / resolution).astype(np.int64) - cp
        radial = (rd * rd + cd * cd) * resolution**2 <= radius**2 + 1e-9
        rr, cc = row + rd, col + cd
        inside = (rr >= 0) & (cc >= 0) & (rr < dsm.shape[0]) & (cc < dsm.shape[1])
        eligible = radial & inside
        sampled = np.full(count, np.nan, np.float32)
        sampled[eligible] = dsm[rr[eligible], cc[eligible]]
        known = eligible & np.isfinite(sampled)
        complete.append(int(np.all(~radial | known)))
        slopes = np.zeros(count, np.float64)
        # The adopted DSM operator subtracts native float32 heights first.
        slopes[known] = (sampled[known] - height) / nominal[known]
        best = int(np.argmax(slopes))
        maximum = max(0., slopes[best])
        answers.append(math.degrees(math.atan(maximum)))
        blockers.append(float(nominal[best]) if maximum > 0 else 0.)
    return np.array(answers), np.array(complete, np.uint8), np.array(blockers)


def classification_oracle(horizon, support, elevation, threshold):
    labels, flags = [], []
    for angle, complete in zip(np.ravel(horizon), np.ravel(support)):
        if not math.isfinite(angle):
            labels.append(255); flags.append(1)
        elif elevation <= 0:
            labels.append(255); flags.append(4)
        elif angle > elevation:
            labels.append(1); flags.append(0)
        elif not complete:
            labels.append(255); flags.append(2)
        elif elevation <= threshold:
            labels.append(255); flags.append(3)
        else:
            labels.append(0); flags.append(0)
    return np.array(labels, np.uint8).reshape(horizon.shape), np.array(flags, np.uint8).reshape(horizon.shape)


def meeus_solar(instant, latitude, longitude):
    """Independent Julian-century NOAA/Meeus reference, geometric elevation.

    Equations sourced from NOAA calculator main.js and calculation details;
    separately transcribed, no calls into src.solar. Shared spherical geometry
    and NOAA provenance remain limitations. Not an observational reference.
    """
    from datetime import timezone
    utc = instant.astimezone(timezone.utc)
    jd = utc.timestamp() / 86400 + 2440587.5
    t = (jd - 2451545.) / 36525.
    radians = math.radians
    mean_lon = (280.46646 + t * (36000.76983 + t * .0003032)) % 360
    mean_anomaly = 357.52911 + t * (35999.05029 - .0001537 * t)
    eccentricity = .016708634 - t * (.000042037 + .0000001267 * t)
    centre = (math.sin(radians(mean_anomaly)) * (1.914602 - t * (.004817 + .000014 * t))
              + math.sin(radians(2 * mean_anomaly)) * (.019993 - .000101 * t)
              + math.sin(radians(3 * mean_anomaly)) * .000289)
    omega = 125.04 - 1934.136 * t
    apparent_lon = mean_lon + centre - .00569 - .00478 * math.sin(radians(omega))
    obliquity = 23 + (26 + (21.448 - t * (46.815 + t * (.00059 - t * .001813))) / 60) / 60
    corrected = obliquity + .00256 * math.cos(radians(omega))
    declination = math.asin(math.sin(radians(corrected)) * math.sin(radians(apparent_lon)))
    y = math.tan(radians(corrected) / 2)**2
    equation = 4 * math.degrees(y * math.sin(2 * radians(mean_lon)) - 2 * eccentricity * math.sin(radians(mean_anomaly))
                               + 4 * eccentricity * y * math.sin(radians(mean_anomaly)) * math.cos(2 * radians(mean_lon))
                               - .5 * y * y * math.sin(4 * radians(mean_lon))
                               - 1.25 * eccentricity**2 * math.sin(2 * radians(mean_anomaly)))
    minute = utc.hour * 60 + utc.minute + utc.second / 60 + utc.microsecond / 6e7
    hour_angle = radians(((minute + equation + 4 * longitude) % 1440) / 4 - 180)
    lat = radians(latitude)
    elevation = math.degrees(math.asin(math.sin(lat) * math.sin(declination)
                                       + math.cos(lat) * math.cos(declination) * math.cos(hour_angle)))
    azimuth = (math.degrees(math.atan2(math.sin(hour_angle), math.cos(hour_angle) * math.sin(lat)
                                      - math.tan(declination) * math.cos(lat))) + 180) % 360
    return azimuth, elevation
