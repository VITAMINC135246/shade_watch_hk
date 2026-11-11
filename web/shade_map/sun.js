// Port of src/solar.py (NOAA fractional-year approximation) for planning estimates only.
// shade_map plan and the engine remain authoritative. Times are Hong Kong (UTC+08:00, no DST).

const HKT_OFFSET_MS = 8 * 3600 * 1000;
const RAD = Math.PI / 180;
export const DAYLIGHT_REFERENCE = [22.3, 114.2];  // src/v1.py DAYLIGHT_REFERENCE

function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
function dayOfYear(d) { return Math.floor((d - Date.UTC(d.getUTCFullYear(), 0, 1)) / 86400000) + 1; }

/** Solar centre at a UTC epoch (ms); longitude positive eastward. */
export function position(epochMs, latitude, longitude) {
  const utc = new Date(epochMs);
  const days = isLeap(utc.getUTCFullYear()) ? 365 + 1 : 365;
  const hour = utc.getUTCHours() + utc.getUTCMinutes() / 60 + utc.getUTCSeconds() / 3600 + utc.getUTCMilliseconds() / 3.6e6;
  const gamma = 2 * Math.PI / days * (dayOfYear(utc) - 1 + (hour - 12) / 24);
  const eqtime = 229.18 * (0.000075 + 0.001868 * Math.cos(gamma) - 0.032077 * Math.sin(gamma)
    - 0.014615 * Math.cos(2 * gamma) - 0.040849 * Math.sin(2 * gamma));
  const decl = 0.006918 - 0.399912 * Math.cos(gamma) + 0.070257 * Math.sin(gamma)
    - 0.006758 * Math.cos(2 * gamma) + 0.000907 * Math.sin(2 * gamma)
    - 0.002697 * Math.cos(3 * gamma) + 0.00148 * Math.sin(3 * gamma);
  const trueMinutes = (((hour * 60 + eqtime + 4 * longitude) % 1440) + 1440) % 1440;
  const ha = (trueMinutes / 4 - 180) * RAD;
  const lat = latitude * RAD;
  const sinEl = Math.sin(lat) * Math.sin(decl) + Math.cos(lat) * Math.cos(decl) * Math.cos(ha);
  const geometric = Math.asin(Math.max(-1, Math.min(1, sinEl))) / RAD;
  const azimuth = ((Math.atan2(Math.sin(ha), Math.cos(ha) * Math.sin(lat) - Math.tan(decl) * Math.cos(lat)) / RAD + 180) % 360 + 360) % 360;
  let correction;
  if (geometric > 85) correction = 0;
  else if (geometric > 5) {
    const t = Math.tan(geometric * RAD);
    correction = (58.1 / t - 0.07 / t ** 3 + 0.000086 / t ** 5) / 3600;
  } else if (geometric > -0.575) {
    const e = geometric;
    correction = (1735 - 518.2 * e + 103.4 * e ** 2 - 12.79 * e ** 3 + 0.711 * e ** 4) / 3600;
  } else correction = -20.774 / Math.tan(geometric * RAD) / 3600;
  return { azimuth, geometric, apparent: geometric + correction };
}

/** Local midnight (HKT) of an ISO date 'YYYY-MM-DD' as a UTC epoch in ms. */
export function hktMidnight(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);
  return Date.UTC(y, m - 1, d) - HKT_OFFSET_MS;
}

/** Sunrise and sunset (epoch ms) when the geometric centre crosses -0.833 deg (src/solar.py). */
export function daylightBounds(isoDate, latitude = DAYLIGHT_REFERENCE[0], longitude = DAYLIGHT_REFERENCE[1]) {
  const start = hktMidnight(isoDate);
  const f = (t) => position(t, latitude, longitude).geometric + 0.833;
  const times = Array.from({ length: 721 }, (_, i) => start + i * 120000);
  const values = times.map(f);
  const crossings = [];
  for (let i = 0; i < values.length - 1; i++) {
    if (values[i] * values[i + 1] < 0) {
      let lo = times[i], hi = times[i + 1];
      const sign = values[i] > 0;
      for (let k = 0; k < 28; k++) {
        const mid = lo + (hi - lo) / 2;
        if ((f(mid) > 0) === sign) lo = mid; else hi = mid;
      }
      crossings.push(lo + (hi - lo) / 2);
    }
  }
  if (crossings.length !== 2) throw new Error(`Expected one sunrise and sunset on ${isoDate}; got ${crossings.length}`);
  return crossings;
}

/** Clock-aligned samples inside daylight (src/solar.py daylight_samples). */
export function daylightSamples(isoDate, minutes = 10) {
  const [rise, set] = daylightBounds(isoDate);
  const midnight = hktMidnight(isoDate);
  const step = minutes * 60000;
  const out = [];
  for (let t = midnight + Math.ceil((rise - midnight) / step) * step; t <= set; t += step) out.push(t);
  return out;
}

/** HKT clock text 'HH:MM' for an epoch. */
export function hktClock(epochMs) {
  const d = new Date(epochMs + HKT_OFFSET_MS);
  return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
}

/** Epoch for 'YYYY-MM-DD' and 'HH:MM' in HKT. */
export function hktEpoch(isoDate, clock) {
  const [h, m] = clock.split(':').map(Number);
  return hktMidnight(isoDate) + (h * 60 + m) * 60000;
}

/** Expand {from,to} or a list of dates like tools/shade_map/config.py dates(). */
export function expandDates(value) {
  if (Array.isArray(value)) return value;
  const out = [];
  const [a, b] = [hktMidnight(value.from), hktMidnight(value.to)];
  for (let t = a; t <= b; t += 86400000) out.push(new Date(t + HKT_OFFSET_MS).toISOString().slice(0, 10));
  return out;
}

/**
 * Estimated frames for a region time block, mirroring tools/shade_map/config.py expanded_time():
 * daylight dates use daylight samples; window and instant times outside daylight are dropped.
 */
export function estimateFrames(time) {
  const kept = [], dropped = [];
  const inDaylight = (date, t) => { const [r, s] = daylightBounds(date); return r <= t && t <= s; };
  if (time.mode === 'daylight') {
    for (const day of expandDates(time.dates)) for (const t of daylightSamples(day, time.interval_minutes || 10)) kept.push({ date: day, t });
  } else if (time.mode === 'window') {
    const step = (time.interval_minutes || 10) * 60000;
    for (const day of expandDates(time.dates)) {
      for (let t = hktEpoch(day, time.start); t <= hktEpoch(day, time.end); t += step) {
        (inDaylight(day, t) ? kept : dropped).push({ date: day, t });
      }
    }
  } else {
    for (const text of time.instants) {
      const day = text.slice(0, 10), t = hktEpoch(day, text.slice(11, 16));
      (inDaylight(day, t) ? kept : dropped).push({ date: day, t });
    }
  }
  return { kept, dropped };
}
