// WGS84 <-> Hong Kong 1980 Grid (EPSG:2326) for display and request estimates only.
// Datum shift: the Survey and Mapping Office approximation between WGS84 and HK80
// geodetic coordinates (HK80 = WGS84 + 5.5" latitude, - 8.8" longitude; about 1-2 m).
// Projection: Transverse Mercator on the International 1924 ellipsoid with the official
// HK1980 Grid parameters. python -m shade_watch plan converts corners with pyproj and is authoritative.

const RAD = Math.PI / 180;
const A = 6378388.0;
const F = 1 / 297;
const E2 = F * (2 - F);
const LAT0 = (22 + 18 / 60 + 43.68 / 3600) * RAD;
const LON0 = (114 + 10 / 60 + 42.80 / 3600) * RAD;
const FE = 836694.05;
const FN = 819069.80;
const K0 = 1.0;
const DLAT = 5.5 / 3600;   // degrees added to WGS84 latitude
const DLON = -8.8 / 3600;  // degrees added to WGS84 longitude

function meridian(phi) {
  const e4 = E2 * E2, e6 = e4 * E2;
  return A * ((1 - E2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
    - (3 * E2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * Math.sin(2 * phi)
    + (15 * e4 / 256 + 45 * e6 / 1024) * Math.sin(4 * phi)
    - (35 * e6 / 3072) * Math.sin(6 * phi));
}
const M0 = meridian(LAT0);

function tmForward(latDeg, lonDeg) {
  const phi = latDeg * RAD, lam = lonDeg * RAD;
  const ep2 = E2 / (1 - E2);
  const s = Math.sin(phi), c = Math.cos(phi), t = Math.tan(phi);
  const N = A / Math.sqrt(1 - E2 * s * s);
  const T = t * t, C = ep2 * c * c, Aa = (lam - LON0) * c;
  const M = meridian(phi);
  const x = K0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6 + (5 - 18 * T + T * T + 72 * C - 58 * ep2) * Aa ** 5 / 120);
  const y = K0 * (M - M0 + N * t * (Aa * Aa / 2 + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24
    + (61 - 58 * T + T * T + 600 * C - 330 * ep2) * Aa ** 6 / 720));
  return [FE + x, FN + y];
}

/** WGS84 latitude/longitude (degrees) -> HK1980 Grid easting/northing (m). */
export function toHK1980(lat, lon) {
  return tmForward(lat + DLAT, lon + DLON);
}

/** HK1980 Grid easting/northing (m) -> WGS84 latitude/longitude (degrees), by Newton iteration. */
export function toWGS84(easting, northing) {
  let lat = 22.3 + (northing - FN) / 110750, lon = 114.18 + (easting - FE) / 103000;
  for (let i = 0; i < 20; i++) {
    const [e, n] = toHK1980(lat, lon);
    const h = 1e-6;
    const [e1, n1] = toHK1980(lat + h, lon), [e2, n2] = toHK1980(lat, lon + h);
    const a = (e1 - e) / h, b = (e2 - e) / h, c = (n1 - n) / h, d = (n2 - n) / h;
    const det = a * d - b * c, de = easting - e, dn = northing - n;
    const dLat = (d * de - b * dn) / det, dLon = (a * dn - c * de) / det;
    lat += dLat; lon += dLon;
    if (Math.abs(dLat) < 1e-12 && Math.abs(dLon) < 1e-12) break;
  }
  return [lat, lon];
}
