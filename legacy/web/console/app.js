// Shade Watch HK Console (D-3/D-4 front end). Vanilla ES modules, no build step.
// Science lives in the engine; this page only plans, starts, monitors and displays runs.
import { api, MOCK, ApiError } from './api.js';
import { HKMap } from './map.js';

const HK_BBOX_WGS84 = [113.80, 22.13, 114.45, 22.58];
const HK_EXTENT = [800750, 801800, 863250, 848000];
const DISCLAIMER = 'Engineering result; observational accuracy NOT VERIFIED. Shade is not cooling or ΔT. 255 = uncertain, not shade.';

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmtInt = (n) => (Number.isFinite(n) ? Math.round(n).toLocaleString('en-US') : '—');
const fmtPct = (a, b) => (b > 0 ? `${((100 * a) / b).toFixed(1)}%` : '—');
const fmtBytes = (n) => (!Number.isFinite(n) ? '—' : n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : n >= 1e6 ? `${Math.round(n / 1e6)} MB` : `${Math.round(n / 1e3)} kB`);
const fmtDur = (s) => (!Number.isFinite(s) ? '—' : s < 90 ? `${Math.round(s)} s` : s < 5400 ? `${Math.round(s / 60)} min` : `${(s / 3600).toFixed(1)} h`);
const fmtNum = (n, d = 1) => (Number.isFinite(n) ? n.toFixed(d) : '—');
const STATE_TONE = { SUCCEEDED: 'ok', RUNNING: 'info', PENDING: 'info', CANCELLING: 'muted', CANCELLED: 'muted', FAILED: 'bad', INCOMPLETE: 'warn' };

let cleanup = [];
const onLeave = (fn) => cleanup.push(fn);
const every = (ms, fn) => { const id = setInterval(fn, ms); onLeave(() => clearInterval(id)); };

const cache = { tiles: new Map(), health: null, catalogues: null };
async function loadTiles(catalogue) {
  if (!cache.tiles.has(catalogue)) {
    const fc = await api.tiles(catalogue, HK_BBOX_WGS84);
    cache.tiles.set(catalogue, fc.features.map((f) => ({ name: f.properties.name, b: f.properties.bounds_hk1980 })));
  }
  return cache.tiles.get(catalogue);
}

function errorBox(err) {
  const msg = err instanceof ApiError ? `${err.message} (${err.code})` : String(err?.message || err);
  return `<div class="alert" role="alert">${esc(msg)}</div>`;
}

function shell(active, body) {
  const nav = [['#/new', 'New run', 'new'], ['#/runs', 'Runs', 'runs']]
    .map(([href, label, key]) => `<a href="${href}" ${active === key ? 'aria-current="page"' : ''}>${label}</a>`).join('');
  return `
  <header class="topbar"><div class="wrap topbar-row">
    <div class="brand">Shade Watch HK <span>Console</span></div>
    <nav aria-label="Main">${nav}</nav>
    <div class="badges">
      <span class="badge" id="engine-badge">engine …</span>
      ${MOCK ? '<span class="badge warn">mock data · not connected</span>' : ''}
    </div>
  </div></header>
  <main class="wrap">${body}</main>`;
}

async function fillEngineBadge() {
  try {
    cache.health = cache.health || await api.health();
    const h = cache.health, el = $('#engine-badge');
    if (el) {
      el.textContent = `engine ${String(h.repo.accepted_engine_commit).slice(0, 7)} · ${h.repo.engine_matches_accepted ? 'matches accepted' : 'DIFFERS from accepted'}`;
      el.classList.toggle('bad', !h.repo.engine_matches_accepted);
    }
  } catch { /* badge stays neutral; pages show their own errors */ }
}

// ---------------------------------------------------------------- New run
function newRunPage() {
  return shell('new', `
  <div class="page-head"><h1>New run</h1><p class="muted">Planning computes nothing. Shade is calculated only after you press Start.</p></div>
  <div class="cols">
    <section class="panel map-panel" aria-label="Map">
      <div class="toolbar" role="toolbar" aria-label="Map tools">
        <div class="seg" id="map-mode">
          <button type="button" data-mode="draw" aria-pressed="true">Draw rectangle</button>
          <button type="button" data-mode="pan" aria-pressed="false">Pan</button>
          <button type="button" data-mode="tiles" aria-pressed="false">Pick tiles</button>
          <button type="button" data-mode="point" aria-pressed="false">Point</button>
        </div>
        <div class="seg">
          <button type="button" id="zoom-in" aria-label="Zoom in">+</button>
          <button type="button" id="zoom-out" aria-label="Zoom out">−</button>
          <button type="button" id="fit-hk">Hong Kong</button>
          <button type="button" id="fit-sel">Selection</button>
        </div>
      </div>
      <canvas id="map" class="map" aria-label="DSM tile lattice in HK1980 grid; drag to draw a rectangle"></canvas>
      <p class="hint">Grey squares are native DSM tiles (750 × 600 m); blue-grey is sea or no data. Scroll to zoom; Shift-drag or right-drag to pan.</p>
    </section>

    <section class="panel form-panel" aria-label="Request">
      <form id="req" novalidate>
        <label class="field">Label <input name="label" maxlength="120" placeholder="e.g. Cheung Chau winter day"></label>

        <fieldset><legend>Region</legend>
          <div class="seg" id="region-mode">
            <button type="button" data-region="corners" aria-pressed="true">Two corners</button>
            <button type="button" data-region="tiles" aria-pressed="false">Tiles</button>
            <button type="button" data-region="point" aria-pressed="false">Point</button>
            <button type="button" data-region="bounds" aria-pressed="false">HK1980 bounds</button>
          </div>
          <div data-pane="corners">
            <label class="field">Coordinates
              <select name="crs"><option value="wgs84">WGS84 · latitude, longitude</option><option value="hk1980">HK1980 Grid · easting, northing (m)</option></select>
            </label>
            <div class="grid2">
              <label class="field"><span>Corner 1 · <span class="crs-a">latitude</span></span><input name="c1a" inputmode="decimal"></label>
              <label class="field"><span>Corner 1 · <span class="crs-b">longitude</span></span><input name="c1b" inputmode="decimal"></label>
              <label class="field"><span>Corner 2 · <span class="crs-a">latitude</span></span><input name="c2a" inputmode="decimal"></label>
              <label class="field"><span>Corner 2 · <span class="crs-b">longitude</span></span><input name="c2b" inputmode="decimal"></label>
            </div>
            <button type="button" class="link" id="show-corners">Show typed corners on the map</button>
          </div>
          <div data-pane="tiles" hidden><p class="muted" id="tile-count">No tiles picked. Use “Pick tiles” on the map; the selection must form a full rectangle.</p></div>
          <div data-pane="point" hidden>
            <div class="grid2">
              <label class="field">Latitude <input name="plat" inputmode="decimal"></label>
              <label class="field">Longitude <input name="plon" inputmode="decimal"></label>
            </div>
            <p class="muted">Selects the native tile that contains the point.</p>
          </div>
          <div data-pane="bounds" hidden>
            <div class="grid2">
              <label class="field">Left (E) <input name="bl" inputmode="decimal"></label>
              <label class="field">Bottom (N) <input name="bb" inputmode="decimal"></label>
              <label class="field">Right (E) <input name="br" inputmode="decimal"></label>
              <label class="field">Top (N) <input name="bt" inputmode="decimal"></label>
            </div>
          </div>
        </fieldset>

        <fieldset><legend>Time (Asia/Hong_Kong)</legend>
          <label class="field">Mode
            <select name="tmode">
              <option value="daylight">Daylight sequence for dates</option>
              <option value="instants">Exact instants</option>
              <option value="date_range">Date range</option>
            </select>
          </label>
          <div data-time="daylight" class="grid2">
            <label class="field">Dates (one per line) <textarea name="dates" rows="2">2026-01-07</textarea></label>
            <label class="field">Interval (minutes) <input name="interval" type="number" min="1" value="10"></label>
          </div>
          <div data-time="instants" hidden>
            <label class="field">Instants with offset (one per line)
              <textarea name="instants" rows="3">2026-01-07T08:30:00+08:00&#10;2026-01-07T12:30:00+08:00&#10;2026-01-07T15:10:00+08:00</textarea></label>
          </div>
          <div data-time="date_range" class="grid3" hidden>
            <label class="field">Start <input name="rstart" type="date" value="2026-01-01"></label>
            <label class="field">End <input name="rend" type="date" value="2026-01-07"></label>
            <label class="field">Interval (min) <input name="rinterval" type="number" min="1" value="10"></label>
          </div>
        </fieldset>

        <fieldset><legend>DSM input</legend>
          <label class="field"><span class="sr-only">Catalogue</span><select name="catalogue" id="catalogue"><option>Loading…</option></select></label>
          <p class="muted" id="catalogue-note"></p>
        </fieldset>

        <fieldset><legend>Outputs</legend>
          <label class="check"><input type="checkbox" checked disabled> Shade + Quality GeoTIFF (always)</label>
          <label class="check"><input type="checkbox" name="statistics" checked> Statistics (land and water separated)</label>
          <label class="check"><input type="checkbox" name="logical_mosaic" checked> Logical mosaic index</label>
          <label class="check"><input type="checkbox" name="jpg"> JPG previews (presentation only)</label>
          <label class="check"><input type="checkbox" name="mp4"> MP4 preview (presentation only)</label>
          <label class="field narrow">Workers <select name="workers"><option>1</option><option>2</option><option>3</option><option>4</option></select></label>
        </fieldset>

        <div class="actions"><button type="submit" class="primary">Plan (no computation)</button></div>
      </form>
      <div id="plan-out" aria-live="polite"></div>
    </section>
  </div>`);
}

async function mountNewRun() {
  const form = $('#req');
  // fromMap: the corners came from the map (HK1980 is then sent as-is, avoiding WGS84 round-off
  // that can push a tile-aligned rectangle a few centimetres into neighbouring tiles).
  const s = { region: 'corners', picked: [], selection: null, catalogues: [], fromMap: false };
  const map = new HKMap($('#map'), {
    onRect: async (b) => {
      s.selection = b;
      s.fromMap = true;
      form.crs.value === 'hk1980' ? setCorners([b[0], b[3]], [b[2], b[1]]) : await setCornersFromHK(b);
      if (s.region !== 'corners') setRegion('corners');
      $('#plan-out').innerHTML = '';
    },
    onTiles: (names) => {
      s.picked = names;
      $('#tile-count').textContent = names.length ? `${names.length} tile(s) picked.` : 'No tiles picked.';
      if (s.region !== 'tiles') setRegion('tiles');
    },
    onPoint: async (x, y) => {
      const { points } = await api.transform('hk1980', [[x, y]]);
      form.plat.value = points[0][0].toFixed(6);
      form.plon.value = points[0][1].toFixed(6);
      if (s.region !== 'point') setRegion('point');
    },
  });
  onLeave(() => map.destroy());

  function setCorners(c1, c2) {
    form.c1a.value = c1[0]; form.c1b.value = c1[1];
    form.c2a.value = c2[0]; form.c2b.value = c2[1];
  }
  async function setCornersFromHK(b) {
    const { points } = await api.transform('hk1980', [[b[0], b[3]], [b[2], b[1]]]);
    setCorners(points[0].map((v) => v.toFixed(6)), points[1].map((v) => v.toFixed(6)));
  }
  function setRegion(mode) {
    s.region = mode;
    document.querySelectorAll('#region-mode button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.region === mode)));
    document.querySelectorAll('[data-pane]').forEach((p) => { p.hidden = p.dataset.pane !== mode; });
  }
  function setMapMode(mode) {
    map.setMode(mode);
    document.querySelectorAll('#map-mode button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)));
  }
  $('#region-mode').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setRegion(b.dataset.region); });
  $('#map-mode').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) setMapMode(b.dataset.mode); });
  $('#zoom-in').onclick = () => map.zoom(1.5);
  $('#zoom-out').onclick = () => map.zoom(1 / 1.5);
  $('#fit-hk').onclick = () => map.fit(HK_EXTENT);
  $('#fit-sel').onclick = () => s.selection && map.fit(s.selection, 0.6);
  form.crs.addEventListener('change', async () => {
    const wgs = form.crs.value === 'wgs84';
    document.querySelectorAll('.crs-a').forEach((x) => { x.textContent = wgs ? 'latitude' : 'easting'; });
    document.querySelectorAll('.crs-b').forEach((x) => { x.textContent = wgs ? 'longitude' : 'northing'; });
    if (s.selection) wgs ? await setCornersFromHK(s.selection) : setCorners([s.selection[0], s.selection[3]], [s.selection[2], s.selection[1]]);
  });
  ['c1a', 'c1b', 'c2a', 'c2b'].forEach((n) => form[n].addEventListener('input', () => { s.fromMap = false; }));
  $('#show-corners').onclick = async () => {
    try {
      let p = [[+form.c1a.value, +form.c1b.value], [+form.c2a.value, +form.c2b.value]];
      if (!p.flat().every(Number.isFinite)) throw new Error('Enter four numbers first.');
      if (form.crs.value === 'wgs84') p = (await api.transform('wgs84', p)).points;
      s.selection = [Math.min(p[0][0], p[1][0]), Math.min(p[0][1], p[1][1]), Math.max(p[0][0], p[1][0]), Math.max(p[0][1], p[1][1])];
      s.fromMap = false;
      map.setSelection(s.selection);
      map.fit(s.selection, 0.6);
    } catch (err) { $('#plan-out').innerHTML = errorBox(err); }
  };
  form.tmode.addEventListener('change', () => {
    document.querySelectorAll('[data-time]').forEach((p) => { p.hidden = p.dataset.time !== form.tmode.value; });
  });

  try {
    const { catalogues } = await api.catalogues();
    s.catalogues = catalogues;
    form.catalogue.innerHTML = catalogues.map((c) => `<option value="${esc(c.id)}">${esc(c.kind === 'raw' ? 'Raw CEDD 2020 DSM' : 'Sea-fill view')} · ${esc(c.id)}${c.kind === 'sea_view' && !c.accepted ? ' (not yet accepted)' : ''}</option>`).join('');
    const note = () => {
      const c = s.catalogues.find((k) => k.id === form.catalogue.value);
      $('#catalogue-note').textContent = c ? `${c.tiles} tiles · policy ${c.policy_pair.filter(Boolean).join(' + ')}` : '';
    };
    form.catalogue.addEventListener('change', note);
    note();
    map.setTiles(await loadTiles(catalogues[0].id));
  } catch (err) { $('#plan-out').innerHTML = errorBox(err); }
  map.fit([818500, 805400, 824500, 810200]);
  s.selection = [820250, 807200, 821750, 808400];
  s.fromMap = true;
  map.setSelection(s.selection);
  await setCornersFromHK(s.selection).catch(() => {});

  function buildRequest() {
    const lines = (v) => v.split(/[\n,]+/).map((x) => x.trim()).filter(Boolean);
    let region;
    if (s.region === 'corners' && s.fromMap && s.selection) {
      const b = s.selection;
      region = { type: 'corners', crs: 'hk1980', corner1: [b[0], b[3]], corner2: [b[2], b[1]] };
    } else if (s.region === 'corners') {
      region = { type: 'corners', crs: form.crs.value, corner1: [+form.c1a.value, +form.c1b.value], corner2: [+form.c2a.value, +form.c2b.value] };
      if (![...region.corner1, ...region.corner2].every(Number.isFinite)) throw new Error('Enter both corners, or draw a rectangle on the map.');
    } else if (s.region === 'tiles') {
      if (!s.picked.length) throw new Error('Pick at least one tile on the map.');
      region = { type: 'tiles', tiles: s.picked };
    } else if (s.region === 'point') {
      region = { type: 'point', lat: +form.plat.value, lon: +form.plon.value };
      if (![region.lat, region.lon].every(Number.isFinite)) throw new Error('Enter latitude and longitude, or click the map in Point mode.');
    } else {
      region = { type: 'bounds', bounds: [+form.bl.value, +form.bb.value, +form.br.value, +form.bt.value] };
      if (!region.bounds.every(Number.isFinite)) throw new Error('Enter four HK1980 bounds.');
    }
    let time;
    if (form.tmode.value === 'daylight') time = { type: 'daylight', dates: lines(form.dates.value), interval_minutes: +form.interval.value };
    else if (form.tmode.value === 'instants') time = { type: 'instants', instants: lines(form.instants.value) };
    else time = { type: 'date_range', start: form.rstart.value, end: form.rend.value, interval_minutes: +form.rinterval.value };
    return {
      region, time, catalogue_id: form.catalogue.value,
      outputs: { statistics: form.statistics.checked, logical_mosaic: form.logical_mosaic.checked, jpg: form.jpg.checked, mp4: form.mp4.checked },
      workers: +form.workers.value, label: form.label.value.trim() || undefined,
    };
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const out = $('#plan-out');
    out.innerHTML = '<p class="muted">Planning…</p>';
    let req;
    try {
      req = buildRequest();
      const p = await api.plan(req);
      const rb = p.resolved.bounds_hk1980;
      s.selection = rb;
      map.setSelection(rb);
      map.setNoData((p.no_dsm_areas || []).map((a) => a.bounds_hk1980));
      const cat = s.catalogues.find((c) => c.id === req.catalogue_id);
      const blocked = cat && cat.kind === 'sea_view' && !cat.accepted;
      const facts = [
        ['Native tiles computed', fmtInt(p.tiles.length)],
        ['Rectangle', `${fmtInt(rb[2] - rb[0])} × ${fmtInt(rb[3] - rb[1])} m`],
        ['Output grid', `${fmtInt(p.resolved.width_px)} × ${fmtInt(p.resolved.height_px)} px`],
        ['Frames', fmtInt(p.frames)],
        ['Requests / batches', `${p.requests.length} / ${p.batches}`],
        ['Direction jobs (missing / total)', `${fmtInt(p.direction_jobs.missing)} / ${fmtInt(p.direction_jobs.total)}`],
        ['Wall time (estimate)', `${fmtDur(p.estimate.wall_seconds_range[0])} – ${fmtDur(p.estimate.wall_seconds_range[1])}`],
        ['New disk (estimate)', fmtBytes(p.estimate.new_disk_bytes)],
        ['Peak memory (estimate)', fmtBytes(p.estimate.peak_memory_bytes)],
        ['Cells without DSM', fmtInt(p.no_dsm_cells ?? 0)],
      ];
      out.innerHTML = `
        <div class="plan">
          <h2>Plan preview</h2>
          <dl class="facts">${facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>
          <p class="muted small">Estimates: ${esc(p.estimate.machine)} · ${esc(p.estimate.label)}. Not a measurement on this machine.</p>
          <ul class="warnings">${p.warnings.map((w) => `<li>${esc(w)}</li>`).join('')}</ul>
          ${blocked ? '<div class="alert warn">Start is blocked: this sea-fill view has not passed independent acceptance.</div>' : ''}
          <div class="actions">
            <button type="button" class="dark" id="start" ${blocked ? 'disabled' : ''}>Start run</button>
            <span class="muted small">plan ${esc(p.plan_id)}</span>
          </div>
        </div>`;
      $('#start')?.addEventListener('click', async () => {
        if (!confirm(`Start this run now?\n${p.tiles.length} tiles · ${p.frames} frames · estimate ${fmtDur(p.estimate.wall_seconds_range[0])}–${fmtDur(p.estimate.wall_seconds_range[1])}`)) return;
        try {
          const job = await api.start(p.plan_id, req.label);
          location.hash = `#/jobs/${encodeURIComponent(job.job_id)}`;
        } catch (err) { out.insertAdjacentHTML('beforeend', errorBox(err)); }
      });
    } catch (err) {
      out.innerHTML = errorBox(err);
    }
  });
}

// ---------------------------------------------------------------- Runs
function runsPage() {
  return shell('runs', `
  <div class="page-head"><h1>Runs</h1>
    <div class="actions"><span id="resume-note" class="muted"></span>
      <button type="button" id="resume-all">Resume all incomplete</button>
      <a class="button primary" href="#/new">New run</a></div></div>
  <section class="health" id="health" aria-label="Machine health"></section>
  <section class="panel table-wrap" aria-label="Jobs"><table class="jobs">
    <thead><tr><th scope="col">Job</th><th scope="col">State</th><th scope="col">Progress</th><th scope="col">Elapsed</th><th scope="col">Created</th><th scope="col">Actions</th></tr></thead>
    <tbody id="jobs-body"><tr><td colspan="6" class="muted">Loading…</td></tr></tbody></table></section>
  <p class="muted small">Jobs run as detached processes. Closing this page or restarting the server never stops a computation. After a reboot, use “Resume all incomplete”: finished horizon work is reused.</p>
  <div id="runs-err"></div>`);
}

async function mountRuns() {
  async function health() {
    try {
      const h = await api.health();
      cache.health = h;
      $('#health').innerHTML = [
        ['Machine', `${esc(h.machine.system)}${h.machine.wsl ? ' · WSL2' : ''}`, `${esc(h.machine.cpu_model)} · ${esc(h.machine.cpu_count)} threads`],
        ['Memory available', `${fmtNum(h.machine.memory_available_gib)} of ${fmtNum(h.machine.memory_total_gib)} GiB`, ''],
        ['Free disk', `${fmtNum(h.disk.free_gib, 0)} GiB`, ''],
        ['WSL2 smoke test', esc(h.smoke_test.status || 'unknown'), esc(h.smoke_test.report_path || '')],
      ].map(([k, v, sub]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="sub">${sub}</div></div>`).join('');
    } catch (err) { $('#health').innerHTML = errorBox(err); }
  }
  async function jobs() {
    try {
      const { jobs: list } = await api.jobs();
      $('#jobs-body').innerHTML = list.length ? list.map((j) => {
        const pct = j.progress.total ? Math.round((100 * j.progress.done) / j.progress.total) : 0;
        const live = ['PENDING', 'RUNNING'].includes(j.state);
        return `<tr>
          <td><a href="#/jobs/${encodeURIComponent(j.job_id)}">${esc(j.label)}</a><div class="mono small muted">${esc(j.job_id)}</div></td>
          <td><span class="pill ${STATE_TONE[j.state] || 'muted'}">${esc(j.state)}</span></td>
          <td><div class="bar" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><span style="width:${pct}%"></span></div>
              <div class="mono small muted">${fmtInt(j.progress.done)} / ${fmtInt(j.progress.total)} tasks</div></td>
          <td class="mono">${fmtDur(j.elapsed_seconds)}</td>
          <td class="small">${esc(new Date(j.created).toLocaleString())}</td>
          <td class="row-actions"><a class="button small" href="#/jobs/${encodeURIComponent(j.job_id)}">Details</a>
            ${j.state === 'SUCCEEDED' ? `<a class="button small" href="#/results/${encodeURIComponent(j.job_id)}">Results</a>` : ''}
            ${live ? `<button type="button" class="small danger" data-cancel="${esc(j.job_id)}">Cancel</button>` : ''}</td></tr>`;
      }).join('') : '<tr><td colspan="6" class="muted">No jobs yet.</td></tr>';
    } catch (err) { $('#runs-err').innerHTML = errorBox(err); }
  }
  $('#jobs-body').addEventListener('click', async (e) => {
    const id = e.target.closest('[data-cancel]')?.dataset.cancel;
    if (!id || !confirm('Cancel this job? Finished horizon work is kept.')) return;
    try { await api.cancel(id); jobs(); } catch (err) { $('#runs-err').innerHTML = errorBox(err); }
  });
  $('#resume-all').onclick = async () => {
    try { const r = await api.resumeIncomplete(); $('#resume-note').textContent = `${r.resumed.length} job(s) resumed`; jobs(); } catch (err) { $('#runs-err').innerHTML = errorBox(err); }
  };
  await Promise.all([health(), jobs()]);
  every(4000, jobs);
  every(30000, health);
}

// ---------------------------------------------------------------- Job detail
function jobPage(id) {
  return shell('runs', `<a href="#/runs" class="back">← All runs</a><div id="job">Loading…</div>`);
}
async function mountJob(id) {
  let last = '';
  async function load() {
    try {
      const j = await api.job(id);
      const snap = JSON.stringify(j);
      if (snap === last) return; // unchanged: keep the DOM (and any open <details>) as it is
      last = snap;
      const wasOpen = $('#job details')?.open;
      const pct = j.progress.total ? Math.round((100 * j.progress.done) / j.progress.total) : 0;
      const live = ['PENDING', 'RUNNING'].includes(j.state);
      $('#job').innerHTML = `
        <div class="page-head"><div><h1>${esc(j.label)}</h1><div class="mono small muted">${esc(j.job_id)} · plan ${esc(j.plan_id)} · created ${esc(new Date(j.created).toLocaleString())}</div></div>
          <div class="actions"><span class="pill ${STATE_TONE[j.state] || 'muted'}">${esc(j.state)}</span>
            ${live ? '<button type="button" class="danger" id="cancel">Cancel job</button>' : ''}
            ${j.result_available ? `<a class="button primary" href="#/results/${encodeURIComponent(j.job_id)}">Open results</a>` : '<span class="muted small">Results open when the job succeeds.</span>'}</div></div>
        <div class="cols">
          <section class="panel grow">
            <h2>Progress</h2>
            <div class="bar big" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><span style="width:${pct}%"></span></div>
            <p class="mono small">${fmtInt(j.progress.done)} / ${fmtInt(j.progress.total)} tasks · elapsed ${fmtDur(j.elapsed_seconds)}</p>
            <table class="compact"><thead><tr><th scope="col">Batch</th><th scope="col">State</th><th scope="col">Tasks</th><th scope="col">Failures</th></tr></thead><tbody>
              ${j.batches.map((b) => `<tr><td class="mono small">${esc(b.batch_id)}</td><td>${esc(b.state)}</td>
                <td class="mono small">${Object.entries(b.tasks || {}).map(([k, v]) => `${esc(k)} ${fmtInt(v)}`).join(' · ')}</td>
                <td>${b.failures.length ? b.failures.map((f) => `<div class="small">${esc(f.kind)}: ${esc(f.error)}</div>`).join('') : '—'}</td></tr>`).join('')}
            </tbody></table>
            <h2>Log</h2><pre class="log">${esc(j.log_tail.join('\n'))}</pre>
          </section>
          <section class="panel side">
            <h2>Provenance</h2>
            <dl class="kv">
              <dt>Engine</dt><dd class="mono">${esc(j.provenance.engine_commit)} · ${j.provenance.engine_matches_accepted ? 'matches accepted' : 'DIFFERS'}</dd>
              <dt>Policy</dt><dd class="mono">${esc((j.provenance.policy_pair || []).filter(Boolean).join(' + '))}</dd>
              <dt>DSM input</dt><dd class="mono">${esc(j.provenance.catalogue_id)}${j.provenance.view_id ? ` / ${esc(j.provenance.view_id)}` : ''}</dd>
            </dl>
            <details><summary>Request JSON</summary><pre class="log light">${esc(JSON.stringify(j.provenance.request, null, 2))}</pre></details>
            <p class="disclaimer">${esc(DISCLAIMER)}</p>
          </section>
        </div>`;
      if (wasOpen) $('#job details').open = true;
      $('#cancel')?.addEventListener('click', async () => {
        if (!confirm('Cancel this job? Finished horizon work is kept.')) return;
        try { await api.cancel(id); load(); } catch (err) { $('#job').insertAdjacentHTML('afterbegin', errorBox(err)); }
      });
    } catch (err) { $('#job').innerHTML = errorBox(err); }
  }
  await load();
  every(3000, load);
}

// ---------------------------------------------------------------- Results
function resultsPage() {
  return shell('runs', `<a href="#/runs" class="back">← All runs</a><div id="res">Loading…</div>`);
}
async function mountResults(id) {
  const root = $('#res');
  let r, stats;
  try { [r, stats] = await Promise.all([api.results(id), api.stats(id)]); }
  catch (err) { root.innerHTML = errorBox(err); return; }
  const t = r.grid.transform;
  const bounds = [t[2], t[5] + t[4] * r.grid.height, t[2] + t[0] * r.grid.width, t[5]];
  const st = { frame: 0, layer: 'shade' };
  root.innerHTML = `
    <div class="page-head"><div><h1>Results</h1>
      <div class="chips"><span class="chip mono">${esc(r.catalogue_id)}${r.view_id ? ` / ${esc(r.view_id)}` : ''}</span>
        <span class="chip mono">${esc((r.policy_pair || []).filter(Boolean).join(' + '))}</span>
        <span class="chip mono">engine ${esc(r.engine_commit)}</span>
        <span class="chip mono">surface: ${esc(r.surface_source)}</span></div>
      ${r.note ? `<p class="muted small">${esc(r.note)}</p>` : ''}</div>
      <div class="seg" id="layer" role="group" aria-label="Layer">
        <button type="button" data-layer="shade" aria-pressed="true">Shade</button>
        <button type="button" data-layer="quality" aria-pressed="false">Quality reasons</button>
        <button type="button" data-layer="surface" aria-pressed="false">Surface class</button></div></div>
    <div class="cols">
      <section class="panel map-panel">
        <div class="toolbar"><label class="field inline">Frame
          <input type="range" id="frame" min="0" max="${r.frames.length - 1}" value="0" aria-describedby="frame-label"></label>
          <span id="frame-label" class="mono"></span></div>
        <canvas id="rmap" class="map" aria-label="Result preview; click a pixel to inspect"></canvas>
        <p class="hint">Preview rendered by the server from the Shade/Quality/Surface GeoTIFFs. Click to inspect the exact pixel.</p>
      </section>
      <aside class="side">
        <section class="panel"><h2>Legend</h2><div id="legend"></div></section>
        <section class="panel"><h2>Statistics · <span id="stats-time"></span></h2><div id="stats"></div></section>
        <section class="panel"><h2>Inspector</h2><div id="inspect" class="muted">Click the map.</div></section>
        <section class="panel"><h2>Files</h2><div id="files" class="small">Loading…</div></section>
      </aside>
    </div>
    <p class="disclaimer">${esc(r.disclaimer || DISCLAIMER)} Formal analysis reads the GeoTIFFs, never JPG/MP4.</p>`;

  const map = new HKMap($('#rmap'), {
    mode: 'inspect',
    onPoint: async (x, y) => {
      try {
        const p = await api.pixel(id, st.frame, x, y);
        $('#inspect').innerHTML = `<dl class="kv">
          <dt>HK1980</dt><dd class="mono">E ${fmtNum(p.x, 1)} · N ${fmtNum(p.y, 1)}</dd>
          <dt>WGS84</dt><dd class="mono">${fmtNum(p.lat, 6)}, ${fmtNum(p.lon, 6)}</dd>
          <dt>Pixel</dt><dd class="mono">row ${fmtInt(p.row)} · col ${fmtInt(p.col)}</dd>
          <dt>Label</dt><dd>${p.label === 0 ? 'sunlit (0)' : p.label === 1 ? 'shaded (1)' : 'uncertain (255), not shade'}</dd>
          <dt>Quality</dt><dd>${esc(p.quality_code)} · ${esc(p.quality_reason)}</dd>
          <dt>Surface</dt><dd>${p.surface_class === 1 ? '1 · policy-filled water (lower confidence)' : p.surface_class === 0 ? '0 · DSM-observed' : '255 · no surface'}</dd>
          <dt>Tile</dt><dd class="mono small">${esc(p.tile)}</dd>
          <dt>Sun</dt><dd class="mono">az ${fmtNum(p.solar.azimuth_deg)}° · el ${fmtNum(p.solar.apparent_elevation_deg)}° · dir ${fmtNum(p.solar.direction_deg, 0)}°</dd>
          <dt>Threshold</dt><dd class="mono">${fmtNum(p.threshold_deg, 2)}°</dd></dl>${p.note ? `<p class="muted small">${esc(p.note)}</p>` : ''}`;
      } catch (err) { $('#inspect').innerHTML = errorBox(err); }
    },
  });
  onLeave(() => map.destroy());
  map.setMode('inspect');
  try { map.setTiles(await loadTiles(r.catalogue_id)); } catch { /* preview still works without tiles */ }
  map.fit(bounds, 0.85);

  const LEGEND = {
    shade: [['#FFFFFF', 'Sunlit (0)'], ['#000000', 'Shaded (1)'], ['#9E9E9E', 'Uncertain or no DSM surface (255): not shade'], ['#CFE3F7', 'Water, sunlit (sea-fill view)'], ['#0B2A4A', 'Water, shaded (sea-fill view)']],
    quality: [['transparent', '0 valid'], ['#7E57C2', '1 missing target DSM'], ['#FFB300', '2 incomplete 1 km sunward support'], ['#26A69A', '3 distant-obstruction sensitivity'], ['#455A64', '4 sun below horizon']],
    surface: [['#BDB7A8', '0 DSM-observed surface'], ['#8FB8DE', '1 policy-filled water'], ['transparent', '255 no surface']],
  };
  function render() {
    const f = r.frames[st.frame];
    $('#frame-label').textContent = `${f.local_time} (${st.frame + 1}/${r.frames.length})`;
    $('#stats-time').textContent = f.local_time.slice(11, 16);
    map.setOverlay(api.previewUrl(id, st.frame, st.layer), bounds);
    $('#legend').innerHTML = LEGEND[st.layer].map(([c, l]) => `<div class="legend-row"><span class="swatch" style="background-color:${c}"></span>${esc(l)}</div>`).join('');
    const s = stats.frames.find((x) => x.index === st.frame);
    if (s) {
      const land = s.land, lt = land.sunlit + land.shaded + land.uncertain;
      const water = s.water, wt = water ? water.sunlit + water.shaded + water.uncertain : 0;
      $('#stats').innerHTML = `
        <div class="stat-grid"><div><div class="k">Land sunlit</div><div class="v">${fmtPct(land.sunlit, lt)}</div></div>
          <div><div class="k">Land shaded</div><div class="v">${fmtPct(land.shaded, lt)}</div></div>
          <div><div class="k">Land uncertain</div><div class="v">${fmtPct(land.uncertain, lt)}</div></div></div>
        <p class="small">${water ? `Water (lower confidence): sunlit ${fmtPct(water.sunlit, wt)} · shaded ${fmtPct(water.shaded, wt)} · uncertain ${fmtPct(water.uncertain, wt)}.` : 'Water: not classified with this DSM input.'}
          No surface (NoData): ${fmtInt(s.nodata)} px.</p>
        <p class="muted small">Shares are of all land pixels. Shade is confirmed by any obstruction found; sunlit also needs complete 1 km sunward support. Do not divide by valid pixels only: that ratio leans towards shade.</p>`;
    }
  }
  $('#frame').addEventListener('input', (e) => { st.frame = Number(e.target.value); render(); });
  $('#layer').addEventListener('click', (e) => {
    const b = e.target.closest('button');
    if (!b) return;
    st.layer = b.dataset.layer;
    document.querySelectorAll('#layer button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    render();
  });
  render();
  try {
    const { files } = await api.files(id);
    const sci = files.filter((f) => ['shade', 'quality', 'surface', 'statistics', 'index'].includes(f.kind));
    const media = files.filter((f) => ['jpg', 'mp4'].includes(f.kind));
    $('#files').innerHTML = `<ul class="files">${sci.map((f) => `<li><a href="${esc(f.url)}" class="mono">${esc(f.path)}</a> <span class="muted">${esc(f.kind)} · ${fmtBytes(f.bytes)}</span></li>`).join('')}</ul>
      ${media.length ? `<p class="muted">Presentation previews only:</p><ul class="files">${media.map((f) => `<li><a href="${esc(f.url)}" class="mono">${esc(f.path)}</a></li>`).join('')}</ul>` : ''}`;
  } catch (err) { $('#files').innerHTML = errorBox(err); }
}

// ---------------------------------------------------------------- Router
const routes = [
  [/^#\/new$/, () => [newRunPage(), mountNewRun]],
  [/^#\/runs$/, () => [runsPage(), mountRuns]],
  [/^#\/jobs\/([^/]+)$/, (m) => [jobPage(), () => mountJob(decodeURIComponent(m[1]))]],
  [/^#\/results\/([^/]+)$/, (m) => [resultsPage(), () => mountResults(decodeURIComponent(m[1]))]],
];

async function route() {
  cleanup.forEach((fn) => fn());
  cleanup = [];
  const hash = location.hash || '#/new';
  for (const [re, make] of routes) {
    const m = hash.match(re);
    if (m) {
      const [html, mount] = make(m);
      document.getElementById('app').innerHTML = html;
      fillEngineBadge();
      try { await mount(); } catch (err) { document.querySelector('main').insertAdjacentHTML('afterbegin', errorBox(err)); }
      return;
    }
  }
  location.hash = '#/new';
}
window.addEventListener('hashchange', route);
route();
