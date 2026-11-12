// Request generator: builds a shade_map region config (schema shade-map-region-1.0) and the commands to
// run it. It never starts a computation and writes nothing; the config is downloaded or copied.
// The estimates mirror shade_watch/publish/config.py and shade_watch/engine/solar.py but `python -m shade_watch plan` is authoritative.

import { HKMap, loadCells } from './map.js';
import { toHK1980, toWGS84 } from './hk1980.js';
import { estimateFrames, expandDates, hktClock } from './sun.js';
import { esc, download } from './util.js';
import { fmtInt } from './stats.js';

const NAME_RE = /^[a-z0-9][a-z0-9_-]{0,47}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const CLOCK_RE = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const INSTANT_RE = /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d(?:\+08:00)?$/;
const MAX_OUTPUT_PIXELS = 20_000_000;  // v1.MAX_OUTPUT_PIXELS: full image threshold (D-012)
const MAX_FRAMES = 512;                // v1.MAX_FRAMES per engine request

export async function renderRequest(root) {
  root.innerHTML = `
    <div class="page-head">
      <div>
        <h1>New request</h1>
        <p class="muted small">Draw a rectangle or type two corners, choose times, then download the region config and run the commands yourself. This page starts nothing and writes nothing. <span class="mono">python -m shade_watch plan</span> is the authoritative check.</p>
      </div>
    </div>
    <div class="cols">
      <section class="panel map-panel">
        <div class="toolbar">
          <div class="seg" role="group" aria-label="Map mode">
            <button type="button" data-mode="draw" aria-pressed="true">Draw rectangle</button>
            <button type="button" data-mode="pan" aria-pressed="false">Pan</button>
          </div>
          <button type="button" class="small" id="fit-hk">Fit Hong Kong</button>
          <button type="button" class="small" id="fit-sel">Fit selection</button>
          <span class="small muted mono" id="cursor"></span>
        </div>
        <canvas class="map" id="map" data-mode="draw" tabindex="0" aria-label="Request map"></canvas>
        <p class="hint">Tan cells have a DSM tile (darker = more land). Light cells have none. Red outlines: the four <span class="mono">14NE15*</span> tiles that planning rejects within 1 km (D-008). Shift-drag or right-drag pans in draw mode.</p>
      </section>
      <div class="side">
        <section class="panel">
          <h2>Region</h2>
          <form id="form" autocomplete="off">
            <label class="field"><span>Name (lower case, digits, _ or -; also the output folder name)</span>
              <input name="name" class="mono" value="my_region" required>
            </label>
            <fieldset>
              <legend>Corners</legend>
              <div class="seg" role="radiogroup" aria-label="Coordinate system">
                <button type="button" data-crs="hk1980" aria-pressed="true">HK1980 Grid (m)</button>
                <button type="button" data-crs="wgs84" aria-pressed="false">WGS84 (lat, lon)</button>
              </div>
              <div class="grid2">
                <label class="field"><span id="ll-label">Lower-left easting, northing</span><input name="ll" class="mono" placeholder="820250, 807200"></label>
                <label class="field"><span id="ur-label">Upper-right easting, northing</span><input name="ur" class="mono" placeholder="821750, 808400"></label>
              </div>
              <p class="small muted">Lower-left must be south-west of upper-right; planning refuses swapped corners (D-010). A drawn rectangle is written in HK1980 metres.</p>
            </fieldset>
            <fieldset>
              <legend>Times (Hong Kong time)</legend>
              <div class="seg" role="radiogroup" aria-label="Time form">
                <button type="button" data-time="daylight" aria-pressed="true">Daylight</button>
                <button type="button" data-time="window" aria-pressed="false">Window</button>
                <button type="button" data-time="instants" aria-pressed="false">Instants</button>
              </div>
              <div data-show="daylight window">
                <label class="field"><span>Dates: a list (one per line or comma separated) or a range <code>from..to</code></span>
                  <textarea name="dates" rows="2" class="mono">2026-06-21</textarea>
                </label>
              </div>
              <div class="grid3" data-show="window">
                <label class="field">Start<input name="start" class="mono" value="10:00"></label>
                <label class="field">End<input name="end" class="mono" value="16:00"></label>
              </div>
              <div data-show="daylight window">
                <label class="field narrow">Interval (minutes)<input name="interval" type="number" min="1" max="60" value="10"></label>
              </div>
              <div data-show="instants">
                <label class="field"><span>Instants, one per line, <code>YYYY-MM-DDTHH:MM</code></span>
                  <textarea name="instants" rows="3" class="mono">2026-06-21T13:00</textarea>
                </label>
              </div>
              <p class="small muted">Only sunrise to sunset is computed (Shade Watch paper; D-010 Q3). Times outside daylight are dropped and listed by plan.</p>
            </fieldset>
            <fieldset>
              <legend>Source and output</legend>
              <label class="field">DSM source
                <select name="dsm_source">
                  <option value="sea-2.2" selected>sea-2.2: every NoData filled at 0 m (SW-SEA-POLICY-2.2, accepted 7707c51)</option>
                  <option value="raw">raw: DSM as published, missing data stay 255</option>
                </select>
              </label>
              <label class="field">Full single image per frame
                <select name="full_image"><option value="auto" selected>auto (only if ≤ 20,000,000 pixels)</option><option value="never">never</option></select>
              </label>
              <div class="grid2">
                <label class="field">Machine config<input name="machine" class="mono" value="config/machine.local.json"></label>
                <label class="field">Save the region config as<input name="path" class="mono" value=""></label>
              </div>
              <label class="field"><span>Output folder (the machine config's <code>output_root</code>)</span><input name="output_root" class="mono" value="runs"></label>
            </fieldset>
          </form>
        </section>
        <section class="panel"><h2>Checks and estimate</h2><div id="checks"></div></section>
        <section class="panel">
          <h2>Region config</h2>
          <pre class="log light" id="json"></pre>
          <div class="actions">
            <button type="button" class="primary" id="download">Download JSON</button>
            <button type="button" id="copy-json">Copy</button>
          </div>
        </section>
        <section class="panel">
          <h2>Commands</h2>
          <pre class="log" id="commands"></pre>
          <div class="actions"><button type="button" id="copy-cmd">Copy commands</button></div>
          <p class="small muted">Run from the repository root on the computer that holds the DSM. Large runs are your decision; nothing here starts them.</p>
        </section>
      </div>
    </div>`;

  const $ = (s) => root.querySelector(s);
  const form = $('#form');
  const state = { crs: 'hk1980', time: 'daylight', index: null, config: null, errors: [] };
  const map = new HKMap($('#map'), {
    mode: 'draw',
    onRect: (b) => { setCrs('hk1980', false); form.ll.value = `${b[0]}, ${b[1]}`; form.ur.value = `${b[2]}, ${b[3]}`; update(); },
    onHover: (x, y) => { $('#cursor').textContent = `E ${x.toFixed(0)} N ${y.toFixed(0)}`; },
  });
  map.setMode('draw');
  root.querySelectorAll('[data-mode]').forEach((b) => b.addEventListener('click', () => {
    root.querySelectorAll('[data-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    map.setMode(b.dataset.mode);
  }));
  try {
    state.index = await loadCells('data/cells.json');
    map.setCells(state.index.list);
    map.fit(state.index.domain_bounds);
  } catch (err) {
    $('#checks').innerHTML = `<div class="alert">Could not load data/cells.json: ${esc(err.message)}. Estimates of cells are unavailable.</div>`;
  }
  $('#fit-hk').addEventListener('click', () => state.index && map.fit(state.index.domain_bounds));
  $('#fit-sel').addEventListener('click', () => state.rect && map.fit(state.rect, 0.6));

  function setCrs(crs, convert = true) {
    if (convert && crs !== state.crs) {
      const ll = parsePair(form.ll.value), ur = parsePair(form.ur.value);
      if (ll && ur) {
        const conv = (p) => (crs === 'wgs84' ? toWGS84(p[0], p[1]).map((v) => +v.toFixed(7)) : toHK1980(p[0], p[1]).map((v) => Math.round(v * 2) / 2));
        form.ll.value = conv(ll).join(', '); form.ur.value = conv(ur).join(', ');
      }
    }
    state.crs = crs;
    root.querySelectorAll('[data-crs]').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.crs === crs)));
    $('#ll-label').textContent = crs === 'wgs84' ? 'Lower-left latitude, longitude' : 'Lower-left easting, northing';
    $('#ur-label').textContent = crs === 'wgs84' ? 'Upper-right latitude, longitude' : 'Upper-right easting, northing';
  }
  root.querySelectorAll('[data-crs]').forEach((b) => b.addEventListener('click', () => { setCrs(b.dataset.crs); update(); }));
  root.querySelectorAll('[data-time]').forEach((b) => b.addEventListener('click', () => {
    state.time = b.dataset.time;
    root.querySelectorAll('[data-time]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    root.querySelectorAll('[data-show]').forEach((d) => { d.hidden = !d.dataset.show.split(' ').includes(state.time); });
    update();
  }));
  root.querySelectorAll('[data-show]').forEach((d) => { d.hidden = !d.dataset.show.split(' ').includes(state.time); });
  form.addEventListener('input', update);
  form.addEventListener('submit', (e) => e.preventDefault());
  $('#download').addEventListener('click', () => state.config && !state.errors.length && download(`${state.config.name}.json`, configText(state.config)));
  $('#copy-json').addEventListener('click', () => navigator.clipboard?.writeText($('#json').textContent));
  $('#copy-cmd').addEventListener('click', () => navigator.clipboard?.writeText($('#commands').textContent));

  function update() {
    const errors = [], warnings = [], facts = [];
    const name = form.name.value.trim();
    if (!NAME_RE.test(name)) errors.push('Name must match ^[a-z0-9][a-z0-9_-]{0,47}$.');
    const ll = parsePair(form.ll.value), ur = parsePair(form.ur.value);
    if (!ll || !ur) errors.push('Enter both corners as two numbers each.');
    let rect = null;
    if (ll && ur) {
      if (state.crs === 'wgs84') {
        if (!(ll[0] < ur[0])) errors.push('lower_left.latitude must be less than upper_right.latitude.');
        if (!(ll[1] < ur[1])) errors.push('lower_left.longitude must be less than upper_right.longitude.');
        const a = toHK1980(ll[0], ll[1]), b = toHK1980(ur[0], ur[1]);
        rect = [a[0], a[1], b[0], b[1]];
        facts.push(['HK1980 (≈, ±1 m)', `${a.map((v) => v.toFixed(1)).join(', ')} → ${b.map((v) => v.toFixed(1)).join(', ')}`]);
      } else {
        if (!(ll[0] < ur[0])) errors.push('lower_left.easting must be less than upper_right.easting.');
        if (!(ll[1] < ur[1])) errors.push('lower_left.northing must be less than upper_right.northing.');
        rect = [ll[0], ll[1], ur[0], ur[1]];
      }
    }
    const time = buildTime(state.time, form, errors);
    const cfg = {
      schema: 'shade-map-region-1.0', name, crs: state.crs,
      lower_left: ll || [], upper_right: ur || [], time,
      dsm_source: form.dsm_source.value, full_image: form.full_image.value,
    };
    state.config = cfg;
    state.errors = errors;
    if (rect && rect[0] < rect[2] && rect[1] < rect[3]) {
      state.rect = rect;
      map.setSelection(rect);
      estimateSpace(rect, cfg, facts, warnings, errors);
    } else { map.setSelection(null); map.setHighlight([]); }
    if (time && !errors.some((e) => e.startsWith('Time'))) {
      try { estimateTime(time, facts, warnings); } catch (err) { errors.push(`Time: ${err.message}`); }
    }
    facts.push(['Runtime reference', 'Development, Mac, 4 workers, cold cache: Cheung Chau 4 cells × 65 frames ≈ 11 min; 2 cells × 3 frames ≈ 1 min. Not a prediction.']);
    const path = form.path.value.trim() || `config/regions/${name || 'NAME'}.json`;
    $('#checks').innerHTML =
      errors.map((e) => `<div class="alert">${esc(e)}</div>`).join('')
      + warnings.map((w) => `<div class="alert warn">${esc(w)}</div>`).join('')
      + `<dl class="facts">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`;
    $('#json').textContent = errors.length ? '// Fix the errors above first.' : configText(cfg);
    $('#download').disabled = errors.length > 0;
    $('#commands').textContent = commands(cfg, path, form.machine.value.trim() || 'config/machine.local.json', form.output_root.value.trim() || 'runs');
  }

  function estimateSpace(rect, cfg, facts, warnings, errors) {
    const w = rect[2] - rect[0], h = rect[3] - rect[1];
    const px = Math.ceil(w / 0.5) * Math.ceil(h / 0.5);
    facts.push(['Size', `${w.toFixed(1)} × ${h.toFixed(1)} m (${(w * h / 1e6).toFixed(3)} km²)`]);
    facts.push(['Output pixels (0.5 m)', `≈ ${fmtInt(px)}`]);
    facts.push(['Full single image', cfg.full_image === 'auto' && px <= MAX_OUTPUT_PIXELS ? 'yes (≤ 20,000,000 px)' : 'no (per-cell files and VRT only)']);
    if (!state.index) return;
    const touched = state.index.list.filter((c) => c.b[0] < rect[2] && c.b[2] > rect[0] && c.b[1] < rect[3] && c.b[3] > rect[1]);
    map.setHighlight(touched.map((c) => c.b));
    const supplied = touched.filter((c) => c.supplied).length;
    facts.push(['Native cells computed', `${touched.length} (${supplied} with a DSM tile, ${touched.length - supplied} without)`]);
    const d = state.index.domain_bounds;
    if (rect[0] < d[0] || rect[1] < d[1] || rect[2] > d[2] || rect[3] > d[3]) errors.push('Part of the rectangle lies outside the catalogue lattice and its 1 km domain.');
    if (!touched.length) errors.push('The rectangle touches no native cell.');
    const near = [rect[0] - 1000, rect[1] - 1000, rect[2] + 1000, rect[3] + 1000];
    const blocked = state.index.list.filter((c) => c.exception && c.b[0] < near[2] && c.b[2] > near[0] && c.b[1] < near[3] && c.b[3] > near[1]);
    if (blocked.length) errors.push(`Within 1 km of ${blocked.map((c) => c.tile).join(', ')}: plan rejects this region (D-008, offset tiles without an ingestion policy).`);
    if (cfg.dsm_source === 'raw' && supplied < touched.length) warnings.push(`${touched.length - supplied} cells have no DSM tile; in raw mode they are 255 / quality 1. sea-2.2 fills them at 0 m.`);
    if (cfg.dsm_source === 'raw' && supplied) warnings.push('Raw mode: missing data inside 1 km make pixels uncertain (quality 2). sea-2.2 removes quality 1 and 2.');
    if (cfg.dsm_source === 'sea-2.2') {
      const lattice = state.index.list.filter((c) => c.supplied);
      const north = Math.max(...lattice.map((c) => c.b[3]));
      if (rect[3] > north - 1500) warnings.push('Near the northern edge of DSM coverage: terrain and buildings beyond the edge (Shenzhen side) are filled at 0 m and cannot shade Hong Kong targets. Results here depend on the fill; run fill-impact and report it.');
      const enclosed = touched.reduce((s, c) => s + (c.enclosed || 0), 0);
      if (enclosed) warnings.push(`The computed cells hold ${fmtInt(enclosed)} enclosed-NoData pixels (class 3: land voids or reservoirs) filled at 0 m. Where the true surface is higher they form pits that bias shade; check fill-impact.`);
    }
  }

  function estimateTime(time, facts, warnings) {
    const { kept, dropped } = estimateFrames(time);
    const days = {};
    for (const k of kept) (days[k.date] ||= []).push(k.t);
    facts.push(['Frames (estimated)', `${kept.length} on ${Object.keys(days).length} date(s)`]);
    const first = Object.entries(days).slice(0, 3).map(([d, ts]) => `${d}: ${ts.length} (${hktClock(ts[0])}–${hktClock(ts[ts.length - 1])})`).join('; ');
    if (first) facts.push(['Per date', first + (Object.keys(days).length > 3 ? '; …' : '')]);
    if (dropped.length) warnings.push(`${dropped.length} requested time(s) fall outside sunrise–sunset and will be dropped: ${dropped.slice(0, 4).map((x) => `${x.date} ${hktClock(x.t)}`).join(', ')}${dropped.length > 4 ? ', …' : ''}.`);
    if (!kept.length) warnings.push('No frame falls inside daylight; plan will have nothing to compute.');
    if (Object.values(days).some((ts) => ts.length > MAX_FRAMES)) warnings.push(`A single date has more than ${MAX_FRAMES} frames (engine request limit). Plan will tell whether it can be split; consider a longer interval.`);
  }
}

function parsePair(text) {
  const parts = String(text).split(/[\s,;]+/).filter(Boolean).map(Number);
  return parts.length === 2 && parts.every(Number.isFinite) ? parts : null;
}

function parseDates(text, errors) {
  const t = text.trim();
  const range = t.match(/^(\d{4}-\d{2}-\d{2})\s*\.\.\s*(\d{4}-\d{2}-\d{2})$/);
  if (range) {
    const value = { from: range[1], to: range[2] };
    const n = expandDates(value).length;
    if (!(range[1] <= range[2]) || n < 1 || n > 366) errors.push('Time: a date range must be ordered and contain 1..366 dates.');
    return value;
  }
  const list = t.split(/[\s,;]+/).filter(Boolean);
  if (!list.length) errors.push('Time: enter at least one date.');
  for (const d of list) if (!DATE_RE.test(d) || Number.isNaN(Date.parse(d))) errors.push(`Time: invalid date ${d}.`);
  if (new Set(list).size !== list.length) errors.push('Time: duplicate dates.');
  if (list.length > 366) errors.push('Time: at most 366 dates.');
  return list;
}

function buildTime(mode, form, errors) {
  if (mode === 'instants') {
    const list = form.instants.value.split(/[\s,;]+/).filter(Boolean);
    if (!list.length) errors.push('Time: enter at least one instant.');
    for (const s of list) if (!INSTANT_RE.test(s)) errors.push(`Time: instant ${s} must look like 2026-06-21T13:00.`);
    if (new Set(list.map((s) => s.slice(0, 16))).size !== list.length) errors.push('Time: duplicate instants.');
    return { mode: 'instants', instants: list };
  }
  const interval = Number(form.interval.value);
  if (!Number.isInteger(interval) || interval < 1 || interval > 60) errors.push('Time: interval must be a whole number of minutes from 1 to 60.');
  const time = { mode, dates: parseDates(form.dates.value, errors), interval_minutes: interval };
  if (mode === 'window') {
    time.start = form.start.value.trim(); time.end = form.end.value.trim();
    if (!CLOCK_RE.test(time.start) || !CLOCK_RE.test(time.end)) errors.push('Time: start and end must be HH:MM.');
    else if (time.end < time.start) errors.push('Time: end must not be earlier than start.');
  }
  return time;
}

export function configText(cfg) {
  return JSON.stringify(cfg, null, 2) + '\n';
}

function commands(cfg, path, machine, outputRoot) {
  const py = '.venv/bin/python';
  const m = `--machine ${machine}`;
  const lines = [
    `# 1. Save the downloaded config as ${path}`,
  ];
  if (cfg.dsm_source === 'sea-2.2') lines.push('# 2. Once per computer: build (or verify) the B2.2 sea view (about 35-40 min on the Mac)', `${py} -m shade_watch.fill build ${m}`);
  lines.push(
    '# 3. Plan: read-only, the authoritative check of cells, frames and dropped times',
    `${py} -m shade_watch plan ${m} ${path}`,
    '# 4. Run (resumable). On macOS, caffeinate -dims keeps the computer awake.',
    `caffeinate -dims ${py} -m shade_watch run ${m} ${path}`,
  );
  if (cfg.dsm_source === 'sea-2.2') lines.push(
    '# 5. Optional: how much of the result depends on filled data (runs a raw counterfactual)',
    `${py} -m shade_watch.fill fill-impact ${m} ${path}`,
  );
  lines.push(
    '# 6. View: open this page at',
    `#   #/results?root=${outputRoot}&run=${cfg.name || 'NAME'}`,
  );
  return lines.join('\n');
}
