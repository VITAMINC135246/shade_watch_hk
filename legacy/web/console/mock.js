// Mock runner API for front-end development (?mock in the URL). Not connected to the engine.
// Tile lattice: the real 3,310-tile CEDD 2020 footprint (names here are synthetic).
// Results: a 25 m majority downsample of the accepted Cheung Chau V2 run (2026-01-07),
// so the viewer shows real classes; everything else (jobs, estimates, machine) is invented.

const TILE_ROWS = '3:13;4:10-13,58-60;5:10-12,58-61;6:11-12,58-61;7:9-13,56,58-61;8:10-13,39-44,57-61,63,65;9:11-13,39-44,57-59,62-63,65-66;10:11,21-23,39-44,57-59,62-66;11:2-4,21-23,26-27,40-43,53-54;12:2-5,21-22,26-29,40-44,53-54;13:2-6,11-13,26-29,40-46,53-54,57-59;14:2-7,10-14,22,26-29,37-46,49,51-54,57-59;15:1-14,16,21-25,27-28,37-42,49,51-54,56-59;16:1-14,21-28,38-42,50-53,56-59;17:1-15,20-26,38-42,46-47,51-59;18:2-19,21-26,38-40,45-59;19:2-24,28-30,39-40,43-58,63-64;20:3-24,27-30,40,42-58,62-64;21:4-25,27-30,42-59,62-65;22:3-25,27-31,41-59,62-64,71-72;23:3-25,27-31,41-59,61-62,64-65,71-72;24:5-27,30-31,40-59,61-66,71-72,74-75;25:6-27,40-58,60-66,71-72;26:4-27,40-57,60-67,73;27:3-4,7-27,29-30,34-35,39-57,60-65;28:8-32,34-35,39-57,60-65;29:9-30,42-44,46-48,50-53,56-58,60-66;30:9-27,45-50,55-68;31:9-26,28-30,45-50,53-68;32:8-18,21-31,45-67,74-75;33:9-18,22-31,42-43,45-64,67,71-75;34:7-18,23-31,40-65,68-69,71-74;35:7-18,21,24-31,36-61,64-65,67-69,71-76;36:9-13,19,25-32,36-61,64-65,67-69,71,73-76;37:11-13,19,21,26-32,36-61,67-70,72-75;38:8-9,21,29-32,35-60,64,66-68,71-75;39:8-9,30-33,35-61,65-68,70-74;40:8,27,31-62,64-75;41:6,15-17,26-62,64-76;42:13-17,22-77;43:7-8,12-17,19-20,22-61,63-72,74-77;44:7-8,12-61,63-77;45:7-8,12-63,65-77;46:7,13-62,64-77;47:12-77;48:12-76;49:11-77;50:10-77;51:10-76,78-79;52:11-79;53:12-79;54:14-53,55-61,63-78;55:16-52,56-79;56:16-51,54,56-58,62-79;57:17-49,53,59,62-70,72-74;58:17-55,57-59,62-70,72-74,78;59:18-59,63-70,73-74;60:19-60,63-71,73-74;61:18-57,59-61,63-71,73-74,82;62:18-19,21-56,59-63,66-71,73-74;63:17-18,22-57,60-65,67-74;64:23-57,60,62-66,68-69,72-75;65:23-67,73-74;66:25-68,73;67:25-69,72-73;68:26-70,73-74;69:31-70;70:32-62,64-68;71:33-64,66-68;72:34-63,66-68;73:34-52,54-68;74:36-38,40-53,56-61,63-68,83-84;75:41-60,63-66,69,82-84;76:44-55,57-61,63-67,82-83;77:44-54,57,59-61,63-67,82-83;78:45-54;79:46-47';
const CC_FRAMES = {
  "08:30": "4s1k7s10k1u7k2u32s1k1u1k4s11k2u7k1u31s3u1k1u1k1s14k1u6k32s3u17k2u5k1u32s1u19k1u6k1u34s25k1u35s17k1u6k1u36s24k36s16k2u6k36s6k1u7k2u8k1u36s5k5u2s11k1u32s1k4s1u2k1u8s10k1u32s1u18s1k1u7k1u51s8k1u30s1k21s7k2u52s5k1u1k1u28s1k24s6k2u27s1u25s6k2u52s7k1u25s1u26s7k2u52s7k2u51s8k2u50s9k2u49s10k1u49s10k1w2u47s9k1w2k2u46s14k46s12k1u7k1u39s20k1u38s4k1u5k1u10k1u37s1k1w3k1u20k6s1k26s29k3s2k1u25s2k1w17k1u13k26s2k1u16k2u13k26s3k2u15k2u12k25s22k1u12k25s23k1u11k24s36k18s42k8s1u2k1u1k1u4k1u8k2u31k6s5k4u11k2u2k1u29k5s22k1u19k2u11k4s42k2u12k4s56k4s56k3s1k1u55k3s57k2s58k",
  "12:30": "4s1u7s9k3u1k3u2k1w2u31s3u5s3k1u5k5u3k2w1u31s6u1s1u4k1u1k1u1k1u1k1u1k3u1k2u2w32s6u5k2u1k1u5k7u1w31s8u2k2u2k2u1k1u3k6u2w33s6u2k2u1k3u3k1u1k3u1k2u1k1w35s3u4k1u4k1u2k1u1k6u2w36s1u3k7u1k10u1k1w36s4k1u1k9u1k7u1w36s2u2k14u1k3u1k2w37s2k8u1s3u1k5u1k2w32s1u4s4u8s4u1k3u1k2w32s1u4s1u13s2u1k3u4w51s5u1k3w30s1u21s4u1k4w52s3u4w1u28s1u24s2u4w2u27s1u25s1u3w1k3u52s1u3w1k2u1k25s1u27s1u1w1k5u52s9u51s8u1k1u50s11u49s11u49s5u5k3u47s1u1k12u46s12u1k2u45s6u2k2u1k4u4k2u39s15u4k2u38s8u1k4u8k1u37s10u1k1u1k1u2k1u8k1u6s1k26s11u2k4u11k1u3s2k1u25s10u1k1u3k2u1k7u4k1u4k26s1k8u1k2u4k3u1k3u1k1u9k26s12u9k3u1k1u5k3u25s1k6u1k5u1k1u7k7u2k1u3k25s1k3u1k1u2k1u1k3u2k1u2k2u2k3u1k4u5k24s1k5u1k8u1k4u4k6u1k1u3k1u18s5k7u1k3u1k3u3k5u2k4u7k1u8s9u1k12u1k9u1k3u3k1u2k2u8k6s1k9u1k22u1k3u7k1u9k5s1u4k8u3k2u1k7u2k2u2k6u3k5u9k4s1u1k2u2k5u1k5u2k1u2k2u4k1u6k2u5k2u1k2u9k4s1u1k3u1k2u1k2u3k4u6k1u7k1u2k1u5k6u3k2u1k1u2k4s6u3k1u4k1u4k2u2k2u1k4u1k1u3k1u2k9u3k1u2k1u2k3s6u3k3u1k1u12k3u1k2u3k1u1k1u2k4u1k3u5k1u3k3s5u3k2u2k1u9k3u2k1u1k3u3k2u3k1u1k1u3k3u1k4u2k1u3s3k1u1k2u2k2u2k1u6k1u7k1u1k6u3k3u1k5u1k2u5k1u",
  "15:10": "4s1u7s1u8k2u2k1u6k32s3u4s1u3k1u6k2u1k1u3k1u1k1u31s6u2s4k1u7k3u3k1u1k32s6u8k1u5k3u1k1u3k31s8u2k1u4k2u4k3u5k33s3u10k1u7k1u5k35s3u4k1u9k5u3k36s1u6k3u5k1u1k4u3k36s1u3k1u2k8u1k4u1k2u1k36s2u4k3u1k1u1k8u2k1u2k36s1u3k6u2s7u5k32s1u4s4u8s4u1k2u2k1u1k32s1u18s2u1k2u1k1u3k51s2u1k2u2k1u1k30s1u21s2u1k1u5k52s2u1k1u1k3u28s1u24s2u1k1u1k1u1k1u27s1u25s4u3k1u25s1u26s4u4k25s1u27s7u1k52s3u3k1u2k51s1u1k1u1k4u2k50s2k1u2k1u4k50s3u2k1u2k1u1k1w49s2u9k1w48s1u2k1u2k1u2k1w2k2w47s1u2k2u1k2w1k1w3k1w46s1u1k2u1w2k2w1k2w1k1w5k1w39s2u1k1u4k2w11k38s1u1k2u2w4k2w10k37s3u2k2w9k1w9k6s1u26s2u4k2w1k2w4k3w11k3s2k1u25s3u1k1w1k4w5k2w3k4w5k2u3k26s3u2w1k3w2k1w4k1w3k3w7k1u3k26s1u1k6w1k3w10k2w9k1u25s2k2w1k1w3k1w1k1w11k2w1k1u8k25s1k1w3k1w2k1w3k1w5k2w3k1w1u10k24s2k3w3k1w4k1w2k1w8k3u8k19s4k1w3k1w1k1w6k2w6k1w15k8s12u1k1w1k1w1k4w2k2w3k1w2k1w11k1u8k6s1u1k3u1k4u1k2u1k1w3k4w1k2w1k2w2k1w4k1w9k1u8k5s1u6k4u9k4w1k1w2k1w4k1w1k1w6k1u12k4s1u1k2u9k1w2k2w5k1w18k2u2k1u9k4s1u1k1u7k1u4k1w1k1w22k1u5k1u9k4s4u19k1w2k1w2k1w8k2u6k1u6k1u2k3s1u1k4u5k1u22k1w5k1u6k2u8k3s2u1k2u4k1u12k1u1k2u4k2w15k2u1k1u1k1u3k1u2s1u5k1u4k1u19k3w7k1u2k2u1k2u1k2u6k"
};

const ORIGIN = { e: 836694.05, n: 819069.8, lat: 22.31213333, lon: 114.17855556 };
const M_PER_DEG_LAT = 110766, M_PER_DEG_LON = 102988;
const toHK = (lat, lon) => [ORIGIN.e + (lon - ORIGIN.lon) * M_PER_DEG_LON, ORIGIN.n + (lat - ORIGIN.lat) * M_PER_DEG_LAT];
const toWGS = (e, n) => [ORIGIN.lat + (n - ORIGIN.n) / M_PER_DEG_LAT, ORIGIN.lon + (e - ORIGIN.e) / M_PER_DEG_LON];

const TILES = [];
for (const row of TILE_ROWS.split(';')) {
  const [j, ranges] = row.split(':');
  for (const r of ranges.split(',')) {
    const [a, b] = r.split('-').map(Number);
    for (let i = a; i <= (Number.isNaN(b) || b === undefined ? a : b); i++) {
      const left = 800000 + 750 * i, top = 800000 + 600 * Number(j);
      TILES.push({ name: `T${i}_${j}.tif`, i, j: Number(j), b: [left, top - 600, left + 750, top] });
    }
  }
}
const tileAt = new Map(TILES.map((t) => [`${t.i},${t.j}`, t]));
const CC_TILES = ['14NW19B(e820n807,e821n808).tif', '14NW20A(e821n807,e821n808).tif', '14NW19D(e820n807,e821n807).tif', '14NW20C(e821n807,e821n807).tif'];
const CC_GRID = { width: 3000, height: 2400, transform: [0.5, 0, 820250, 0, -0.5, 808400], crs: 'EPSG:2326' };
const DISCLAIMER = 'Engineering result; observational accuracy NOT VERIFIED. Shade is not cooling or ΔT. 255 = uncertain, not shade.';
const PROVENANCE = { engine_commit: '356f611 (mock)', engine_matches_accepted: true, policy_pair: ['SW-V1-POLICY-1.0', null], catalogue_id: 'raw-2020', view_id: null };

function decodeRle(s) {
  let out = '';
  s.replace(/(\d+)([wkus])/g, (_, n, ch) => { out += ch.repeat(Number(n)); return ''; });
  return out;
}
const CC = [
  { local: '2026-01-07T08:30:00+08:00', utc: '2026-01-07T00:30:00+00:00', az: 123.59, el: 16.63, dir: 125, grid: decodeRle(CC_FRAMES['08:30']),
    counts: { 0: 76184, 1: 2505182, 255: 4618634 }, q: { 0: 2581366, 1: 3877687, 2: 740947, 3: 0, 4: 0 } },
  { local: '2026-01-07T12:30:00+08:00', utc: '2026-01-07T04:30:00+00:00', az: 180.24, el: 45.30, dir: 180, grid: decodeRle(CC_FRAMES['12:30']),
    counts: { 0: 83092, 1: 1477090, 255: 5639818 }, q: { 0: 1560182, 1: 3877687, 2: 1762131, 3: 0, 4: 0 } },
  { local: '2026-01-07T15:10:00+08:00', utc: '2026-01-07T07:10:00+00:00', az: 223.82, el: 30.62, dir: 225, grid: decodeRle(CC_FRAMES['15:10']),
    counts: { 0: 482469, 1: 1869329, 255: 4848202 }, q: { 0: 2351798, 1: 3877687, 2: 970515, 3: 0, 4: 0 } },
];

const state = {
  started: new Date(Date.now() - 3600e3).toISOString(),
  plans: new Map(),
  jobs: [{ job_id: 'job_cc_20261009', label: 'Cheung Chau 2×2 · accepted V2 run (sample)', created: '2026-10-09T16:20:00+08:00',
    state: 'SUCCEEDED', progress: { done: 1, total: 1 }, elapsed_seconds: 523, plan_id: 'pln_cc', fixed: true }],
};

const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
const fail = (status, code, message) => json({ error: { code, message } }, status);
const intersects = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];

function resolveRegion(region) {
  if (!region || !region.type) throw ['bad_region', 'region.type is required'];
  if (region.type === 'corners') {
    const p = [region.corner1, region.corner2];
    if (!p.every((c) => Array.isArray(c) && c.length === 2 && c.every(Number.isFinite))) throw ['bad_region', 'Two numeric corners are required'];
    const xy = region.crs === 'wgs84' ? p.map(([lat, lon]) => {
      if (Math.abs(lat) > 90 || Math.abs(lon) > 180) throw ['bad_region', 'WGS84 corners are (latitude, longitude)'];
      return toHK(lat, lon);
    }) : p;
    const b = [Math.min(xy[0][0], xy[1][0]), Math.min(xy[0][1], xy[1][1]), Math.max(xy[0][0], xy[1][0]), Math.max(xy[0][1], xy[1][1])];
    if (b[0] === b[2] || b[1] === b[3]) throw ['bad_region', 'The rectangle has zero width or height'];
    return b;
  }
  if (region.type === 'bounds') return region.bounds;
  if (region.type === 'tiles') {
    const t = TILES.filter((x) => region.tiles.includes(x.name));
    if (!t.length) throw ['bad_region', 'No known tiles selected'];
    return [Math.min(...t.map((x) => x.b[0])), Math.min(...t.map((x) => x.b[1])), Math.max(...t.map((x) => x.b[2])), Math.max(...t.map((x) => x.b[3]))];
  }
  if (region.type === 'point') {
    const [x, y] = toHK(region.lat, region.lon);
    const t = TILES.find((k) => x >= k.b[0] && x < k.b[2] && y >= k.b[1] && y < k.b[3]);
    if (!t) throw ['no_dsm', 'The point is not inside any DSM tile'];
    return t.b;
  }
  throw ['bad_region', `Unknown region type ${region.type}`];
}

function framesFor(time) {
  if (time.type === 'instants') return { frames: time.instants.length, dates: 0 };
  if (time.type === 'daylight') return { frames: time.dates.length * Math.round(650 / (time.interval_minutes || 10)), dates: time.dates.length };
  if (time.type === 'date_range') {
    const days = Math.max(1, Math.round((Date.parse(time.end) - Date.parse(time.start)) / 864e5) + 1);
    return { frames: days * Math.round(650 / (time.interval_minutes || 10)), dates: days };
  }
  throw ['bad_time', 'Unknown time type'];
}

function plan(body) {
  const b = resolveRegion(body.region);
  const tiles = TILES.filter((t) => intersects(t.b, b));
  if (!tiles.length) throw ['no_dsm', 'The rectangle intersects no DSM tile in this catalogue.'];
  const i0 = Math.floor((b[0] - 800000) / 750), i1 = Math.ceil((b[2] - 800000) / 750) - 1;
  const j0 = Math.floor((b[1] - 800000) / 600) + 1, j1 = Math.ceil((b[3] - 800000) / 600);
  let noDsm = 0;
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) if (!tileAt.has(`${i},${j}`)) noDsm++;
  const { frames, dates } = framesFor(body.time);
  if (!frames) throw ['bad_time', 'At least one instant or date is required'];
  const dirs = body.time.type === 'instants' ? Math.min(frames, 47) : Math.min(47, 27 + 3 * (dates - 1));
  const w = Math.round((b[2] - b[0]) / 0.5), h = Math.round((b[3] - b[1]) / 0.5);
  const parts = Math.max(1, Math.ceil((w * h) / 20e6)) * Math.max(1, Math.ceil(frames / 512));
  const missing = tiles.length * dirs;
  const base = missing * 4.2 + frames * tiles.length * 0.19;
  const sea = body.catalogue_id !== 'raw-2020';
  const warnings = ['Cost scales with whole native tiles (750 × 600 m), not with the rectangle area.'];
  if (noDsm) warnings.push(`${noDsm} lattice cell(s) inside the rectangle have no DSM tile. They stay in the output: with this catalogue they read as 255 / Quality 1 (uncertain, not shade).`);
  if (parts > 1) warnings.push(`The request is split into ${parts} parts (V1 limits: 20 M pixels and 512 frames per request); read back through the logical mosaic.`);
  if (sea) warnings.push('Sea-fill view: water pixels are classified too, with lower confidence (no boats, no tide). Shade on water is not cooling.');
  const plan_id = `pln_${Math.random().toString(36).slice(2, 10)}`;
  const corners = [[b[0], b[3]], [b[2], b[3]], [b[2], b[1]], [b[0], b[1]]].map(([x, y]) => toWGS(x, y));
  const result = {
    plan_id,
    resolved: { bounds_hk1980: b, corners_wgs84: corners, width_px: w, height_px: h },
    tiles: tiles.map((t) => t.name),
    requests: Array.from({ length: parts }, (_, k) => ({ id: `region_${String(k).padStart(4, '0')}`, bounds_hk1980: b, tiles: tiles.map((t) => t.name), frames })),
    batches: Math.max(1, Math.ceil(parts / 8)),
    no_dsm_areas: [], no_dsm_cells: noDsm,
    direction_jobs: { total: missing, cached: 0, missing },
    frames,
    estimate: { wall_seconds_range: [base * 0.8, base * 2.0], peak_memory_bytes: 1.1e9 * (body.workers || 1),
      new_disk_bytes: missing * 4.1e6 + frames * tiles.length * 1.8e6 * 0.256, machine: 'Mac calibration (mock)', label: 'estimate' },
    warnings,
  };
  state.plans.set(plan_id, { body, result });
  return result;
}

function tick(job) {
  if (job.fixed || ['CANCELLED', 'FAILED', 'SUCCEEDED'].includes(job.state)) return;
  const elapsed = (Date.now() - job.t0) / 1000;
  job.elapsed_seconds = Math.round(elapsed);
  job.progress.done = Math.min(job.progress.total, Math.floor(elapsed / 0.6));
  job.state = job.progress.done >= job.progress.total ? 'SUCCEEDED' : (elapsed < 2 ? 'PENDING' : 'RUNNING');
}

function jobDetail(job) {
  tick(job);
  const p = state.plans.get(job.plan_id);
  const horizon = p ? p.result.direction_jobs.missing : 108;
  const doneH = Math.min(horizon, job.progress.done);
  return { ...job, fixed: undefined, t0: undefined,
    batches: [{ batch_id: `${job.job_id}_b0`, state: job.state, tasks: { SUCCEEDED: job.progress.done, PENDING: job.progress.total - job.progress.done }, failures: [] }],
    log_tail: [
      `[mock] plan ${job.plan_id}: ${p ? p.result.tiles.length : 4} target tiles via a request-local source view`,
      `[mock] horizon ${doneH} / ${horizon} complete`,
      job.state === 'SUCCEEDED' ? '[mock] frames, statistics and index written' : '[mock] working…',
    ],
    provenance: { ...PROVENANCE, catalogue_id: p ? p.body.catalogue_id : 'raw-2020', plan_id: job.plan_id, request: p ? p.body : { note: 'accepted Cheung Chau run' } },
    result_available: job.state === 'SUCCEEDED',
  };
}

function pixel(frameIndex, x, y) {
  const f = CC[frameIndex];
  if (!f) throw ['bad_frame', 'Unknown frame'];
  const col = Math.floor((x - 820250) / 0.5), row = Math.floor((808400 - y) / 0.5);
  if (col < 0 || row < 0 || col >= 3000 || row >= 2400) throw ['outside', 'The point is outside the result grid'];
  const ch = f.grid[Math.floor(row / 50) * 60 + Math.floor(col / 50)];
  const label = { w: 0, k: 1, u: 255, s: 255 }[ch];
  const quality = { w: 0, k: 0, u: 2, s: 1 }[ch];
  const reasons = { 0: 'valid', 1: 'missing target DSM', 2: 'incomplete 1 km sunward support' };
  const tile = CC_TILES[(row < 1200 ? 0 : 2) + (col < 1500 ? 0 : 1)];
  const [lat, lon] = toWGS(x, y);
  return { x, y, lat, lon, row, col, label, quality_code: quality, quality_reason: reasons[quality],
    surface_class: ch === 's' ? 255 : 0, tile, solar: { azimuth_deg: f.az, apparent_elevation_deg: f.el, direction_deg: f.dir },
    threshold_deg: 6.14, note: 'mock: value of the 25 m block majority, not the 0.5 m pixel' };
}

const SAMPLE_RESULT = () => ({
  frames: CC.map((f, index) => ({ index, local_time: f.local, utc_time: f.utc, counts: f.counts, quality_counts: f.q })),
  grid: CC_GRID,
  bounds_wgs84: { corners: [[820250, 808400], [821750, 808400], [821750, 807200], [820250, 807200]].map(([x, y]) => toWGS(x, y)) },
  surface_source: 'raw_dsm_finite', ...PROVENANCE, disclaimer: DISCLAIMER,
  note: 'Mock: every job shows the accepted Cheung Chau sample (3 of 65 frames).',
});

export async function mockFetch(method, path, body) {
  await new Promise((r) => setTimeout(r, 120));
  const url = new URL(path, location.origin);
  const p = url.pathname;
  try {
    if (method === 'GET' && p === '/api/health') {
      return json({ api_version: 'runner-api-1.0', server: { started: state.started, pid: 4242 },
        repo: { root: '~/shade_watch_hk', head: '[HEAD]', engine_matches_accepted: true, accepted_engine_commit: '356f611d7b775ce31006904b80ca31d3c1c484b2' },
        machine: { system: 'Linux', release: '[WSL2 kernel]', wsl: true, cpu_model: '[CPU model]', cpu_count: 16, memory_total_gib: 24, memory_available_gib: 19.5 },
        disk: { free_gib: 1210 }, smoke_test: { report_path: null, status: 'NOT RUN' }, mock: true });
    }
    if (method === 'GET' && p === '/api/catalogues') {
      return json({ catalogues: [
        { id: 'raw-2020', kind: 'raw', path: 'data/raw/dsm/2020/D12.DSM.TIFF', tiles: 3310, policy_pair: ['SW-V1-POLICY-1.0', null] },
        { id: 'sea_fill_v1/a3c26a13', kind: 'sea_view', path: 'data/processed/dsm_views/sea_fill_v1/a3c26a13…/tiles', tiles: 41,
          policy_pair: ['SW-V1-POLICY-1.0', 'SW-SEA-POLICY-1.0'], view_id: 'a3c26a13…', accepted: false },
      ] });
    }
    if (method === 'GET' && p === '/api/tiles') {
      const bbox = (url.searchParams.get('bbox') || '').split(',').map(Number);
      const [x0, y0] = toHK(bbox[1], bbox[0]), [x1, y1] = toHK(bbox[3], bbox[2]);
      const box = [x0, y0, x1, y1];
      return json({ type: 'FeatureCollection', features: TILES.filter((t) => !bbox.every(Number.isFinite) || intersects(t.b, box)).map((t) => ({
        type: 'Feature', properties: { name: t.name, bounds_hk1980: t.b },
        geometry: { type: 'Polygon', coordinates: [[[t.b[0], t.b[1]], [t.b[2], t.b[1]], [t.b[2], t.b[3]], [t.b[0], t.b[3]], [t.b[0], t.b[1]]].map(([x, y]) => toWGS(x, y).reverse())] },
      })) });
    }
    if (method === 'POST' && p === '/api/transform') {
      const pts = body.points.map(([a, b]) => (body.from === 'wgs84' ? toHK(a, b) : toWGS(a, b)));
      return json({ points: pts, transformer: 'mock linear approximation (the real server uses the engine transformer)' });
    }
    if (method === 'POST' && p === '/api/plan') return json(plan(body));
    if (method === 'POST' && p === '/api/jobs') {
      const pl = state.plans.get(body.plan_id);
      if (!pl) throw ['unknown_plan', 'Plan not found; plan again'];
      if (state.jobs.some((j) => { tick(j); return ['PENDING', 'RUNNING'].includes(j.state); })) return fail(409, 'busy', 'Another job is running. Only one job may run at a time.');
      const total = pl.result.direction_jobs.missing + pl.result.frames + 2;
      const job = { job_id: `job_${Math.random().toString(36).slice(2, 10)}`, label: body.label || pl.body.label || 'Untitled run',
        created: new Date().toISOString(), state: 'PENDING', progress: { done: 0, total: Math.min(total, 60) }, elapsed_seconds: 0, plan_id: body.plan_id, t0: Date.now() };
      state.jobs.unshift(job);
      return json({ job_id: job.job_id, state: job.state });
    }
    if (method === 'GET' && p === '/api/jobs') {
      state.jobs.forEach(tick);
      return json({ jobs: state.jobs.map(({ job_id, label, created, state: s, progress, elapsed_seconds, plan_id }) => ({ job_id, label, created, state: s, progress, elapsed_seconds, plan_id })) });
    }
    if (method === 'POST' && p === '/api/jobs/resume-incomplete') return json({ resumed: [] });
    let m = p.match(/^\/api\/jobs\/([^/]+)(\/cancel)?$/);
    if (m) {
      const job = state.jobs.find((j) => j.job_id === decodeURIComponent(m[1]));
      if (!job) return fail(404, 'not_found', 'Job not found');
      if (m[2] && method === 'POST') {
        tick(job);
        if (['PENDING', 'RUNNING'].includes(job.state)) { job.state = 'CANCELLED'; job.fixed = true; }
        return json({ state: job.state });
      }
      return json(jobDetail(job));
    }
    m = p.match(/^\/api\/results\/([^/]+)(\/stats|\/files|\/pixel)?$/);
    if (m) {
      const job = state.jobs.find((j) => j.job_id === decodeURIComponent(m[1]));
      if (!job) return fail(404, 'not_found', 'Job not found');
      tick(job);
      if (job.state !== 'SUCCEEDED') return fail(409, 'not_ready', 'Results are available when the job has succeeded.');
      if (!m[2]) return json(SAMPLE_RESULT());
      if (m[2] === '/stats') {
        return json({ frames: CC.map((f, index) => ({ index, land: { sunlit: f.counts[0], shaded: f.counts[1], uncertain: f.counts[255] - f.q[1] }, water: null, nodata: f.q[1] })), ...PROVENANCE, disclaimer: DISCLAIMER });
      }
      if (m[2] === '/files') {
        return json({ files: CC.flatMap((f, i) => {
          const stamp = f.utc.replace(/[-:]/g, '').replace('+0000', '').replace('T', 'T') + '000000Z';
          return [{ kind: 'shade', frame: i, path: `outputs/…/shade/shade_${stamp}.tif`, bytes: 420000, sha256: '[sha256]', url: '#' },
                  { kind: 'quality', frame: i, path: `outputs/…/quality/quality_${stamp}.tif`, bytes: 300000, sha256: '[sha256]', url: '#' }];
        }), ...PROVENANCE, disclaimer: DISCLAIMER });
      }
      if (m[2] === '/pixel') {
        return json({ ...pixel(Number(url.searchParams.get('frame')), Number(url.searchParams.get('x')), Number(url.searchParams.get('y'))), ...PROVENANCE, disclaimer: DISCLAIMER });
      }
    }
    return fail(404, 'not_found', `No mock for ${method} ${p}`);
  } catch (err) {
    if (Array.isArray(err)) return fail(400, err[0], err[1]);
    return fail(500, 'mock_error', String(err));
  }
}

const PALETTE = {
  shade: { w: [255, 255, 255, 255], k: [0, 0, 0, 255], u: [158, 158, 158, 255], s: [158, 158, 158, 255] },
  quality: { w: [0, 0, 0, 0], k: [0, 0, 0, 0], u: [255, 179, 0, 255], s: [126, 87, 194, 255] },
  surface: { w: [189, 183, 168, 255], k: [189, 183, 168, 255], u: [189, 183, 168, 255], s: [0, 0, 0, 0] },
};
const previewCache = new Map();
export function mockPreviewUrl(id, frame, layer) {
  const key = `${frame}:${layer}`;
  if (previewCache.has(key)) return previewCache.get(key);
  const grid = CC[frame].grid, pal = PALETTE[layer] || PALETTE.shade;
  const canvas = document.createElement('canvas');
  canvas.width = 60; canvas.height = 48;
  const ctx = canvas.getContext('2d');
  const img = ctx.createImageData(60, 48);
  for (let k = 0; k < 2880; k++) img.data.set(pal[grid[k]], k * 4);
  ctx.putImageData(img, 0, 0);
  const urlStr = canvas.toDataURL('image/png');
  previewCache.set(key, urlStr);
  return urlStr;
}
