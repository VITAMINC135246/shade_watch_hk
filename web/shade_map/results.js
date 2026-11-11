// Result viewer: reads one shade_map run folder (run_manifest.json, summary.json, frame.json and the
// per-cell Shade/Quality/Surface GeoTIFFs) through the local static server. Read-only.

import { HKMap, loadCells } from './map.js';
import { fetchTiff } from './tiff.js';
import { SHADE, QUALITY, layerCodes, palette, policyOf } from './codes.js';
import { frameStats, summaryFrameStats, reconcile, pct, fmtInt } from './stats.js';
import { toWGS84 } from './hk1980.js';
import { el, esc, listDir, exists, getJSON, setHash, hashParams } from './util.js';

const DISPLAY_PIXEL_BUDGET = 16e6;
const DEPENDENCY = {
  0: 'Observed target, same label without filling',
  1: 'Observed target, uncertain without filling, labelled with filling (resolved by the fill)',
  2: 'Observed target, label changed by filling',
  3: 'Filled target (surface 1-4) with a 0/1 label',
  4: 'Uncertain (255) in the sea-filled run',
};

export async function renderResults(root) {
  const params = hashParams();
  root.innerHTML = `
    <div class="page-head">
      <div>
        <h1>Results</h1>
        <p class="muted small">Reads the published GeoTIFFs and counts of a <span class="mono">shade_map</span> run. Nothing is written. Codes and reporting rules: <a href="/docs/OUTPUT_CODES.md" target="_blank" rel="noopener">docs/OUTPUT_CODES.md</a>.</p>
      </div>
    </div>
    <div class="cols">
      <section class="panel map-panel">
        <div class="toolbar">
          <div class="seg" role="group" aria-label="Layer" id="layer-seg">
            <button type="button" data-layer="shade">Shade</button>
            <button type="button" data-layer="quality">Quality</button>
            <button type="button" data-layer="surface">Surface</button>
          </div>
          <button type="button" class="small" id="prev" aria-label="Previous frame">&#9664;</button>
          <input type="range" id="frame-range" min="0" max="0" value="0" aria-label="Frame">
          <button type="button" class="small" id="next" aria-label="Next frame">&#9654;</button>
          <select id="frame-select" aria-label="Frame list"></select>
          <button type="button" class="small" id="fit">Fit run</button>
        </div>
        <canvas class="map" id="map" data-mode="inspect" tabindex="0" aria-label="Result map"></canvas>
        <p class="hint" id="map-hint">Drag to pan, wheel to zoom, click a pixel to inspect it.</p>
      </section>
      <div class="side">
        <section class="panel" id="run-panel">
          <h2>Run</h2>
          <div class="grid-run">
            <label class="field"><span>Output folder (the machine config's <code>output_root</code>)</span>
              <input id="root-input" class="mono" value="${esc(params.root || 'outputs/shade_map')}">
            </label>
            <div class="actions tight">
              <button type="button" id="list-runs">List runs</button>
              <button type="button" id="find-roots" class="link">Find output folders under outputs/</button>
            </div>
          </div>
          <div id="roots"></div>
          <div id="runs"></div>
          <div id="run-info"></div>
        </section>
        <section class="panel"><h2>Legend</h2><div id="legend"></div></section>
        <section class="panel"><h2>Frame statistics</h2><div id="frame-stats"><p class="muted small">Load a run.</p></div></section>
        <section class="panel"><h2>Pixel</h2><div id="pixel"><p class="muted small">Click the map.</p></div></section>
        <section class="panel"><h2>Whole run</h2><div id="day"><p class="muted small">Load a run.</p></div></section>
        <section class="panel"><h2>Fill dependence</h2><div id="fill"><p class="muted small">Shown when the run has a fill-impact diagnostic.</p></div></section>
      </div>
    </div>`;

  const state = { layer: params.layer || 'shade', frame: 0, run: null, cache: new Map(), images: new Map(), token: 0 };
  const map = new HKMap(root.querySelector('#map'), { mode: 'inspect', onPoint: (x, y) => inspect(x, y) });
  map.setMode('inspect');
  // Test hook for automated checks (no effect on the page).
  window.shadeMapResults = { map, inspect: (x, y) => inspect(x, y), state };
  loadCells('data/cells.json').then((idx) => map.setCells(idx.list)).catch(() => {});

  const $ = (s) => root.querySelector(s);
  const setLayer = (layer) => {
    state.layer = layer;
    root.querySelectorAll('#layer-seg button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.layer === layer)));
    if (state.run) { renderLegend(); drawFrame(); syncHash(); }
  };
  root.querySelectorAll('#layer-seg button').forEach((b) => b.addEventListener('click', () => setLayer(b.dataset.layer)));
  setLayer(state.layer);
  $('#frame-range').addEventListener('input', (e) => selectFrame(Number(e.target.value)));
  $('#frame-select').addEventListener('change', (e) => selectFrame(Number(e.target.value)));
  $('#prev').addEventListener('click', () => selectFrame(Math.max(0, state.frame - 1)));
  $('#next').addEventListener('click', () => state.run && selectFrame(Math.min(state.run.frames.length - 1, state.frame + 1)));
  $('#fit').addEventListener('click', () => state.run && map.fit(state.run.bounds));
  $('#list-runs').addEventListener('click', () => listRuns($('#root-input').value.trim()));
  $('#find-roots').addEventListener('click', findRoots);

  async function findRoots() {
    const box = $('#roots');
    box.innerHTML = '<p class="muted small">Searching outputs/ ...</p>';
    try {
      const dirs = (await listDir('outputs')).filter((d) => d.dir);
      const flags = await Promise.all(dirs.map((d) => exists(`outputs/${d.name}/.shade_map_root.json`)));
      const found = dirs.filter((_, i) => flags[i]).map((d) => `outputs/${d.name}`);
      box.innerHTML = found.length
        ? `<p class="small muted">Output folders with a shade_map marker:</p><ul class="files">${found.map((f) => `<li><button type="button" class="link" data-root="${esc(f)}">${esc(f)}</button></li>`).join('')}</ul>`
        : '<p class="small muted">No output folder with a shade_map marker was found under outputs/.</p>';
      box.querySelectorAll('[data-root]').forEach((b) => b.addEventListener('click', () => { $('#root-input').value = b.dataset.root; listRuns(b.dataset.root); }));
    } catch (err) { box.innerHTML = alertBox(err); }
  }

  async function listRuns(rootPath) {
    const box = $('#runs');
    box.innerHTML = '<p class="muted small">Listing ...</p>';
    try {
      const dirs = (await listDir(rootPath)).filter((d) => d.dir && !d.name.startsWith('.') && !d.name.startsWith('_'));
      const flags = await Promise.all(dirs.map((d) => exists(`${rootPath}/${d.name}/run_manifest.json`)));
      const runs = dirs.filter((_, i) => flags[i]).map((d) => d.name);
      box.innerHTML = runs.length
        ? `<ul class="files">${runs.map((r) => `<li><button type="button" class="link" data-run="${esc(r)}">${esc(r)}</button></li>`).join('')}</ul>`
        : `<p class="small muted">No run folders (with run_manifest.json) in <span class="mono">${esc(rootPath)}</span>.</p>`;
      box.querySelectorAll('[data-run]').forEach((b) => b.addEventListener('click', () => loadRun(rootPath, b.dataset.run)));
    } catch (err) { box.innerHTML = alertBox(err); }
  }

  async function loadRun(rootPath, name, frameKey) {
    const base = `${rootPath}/${name}`;
    $('#run-info').innerHTML = '<p class="muted small">Loading run ...</p>';
    try {
      const manifest = await getJSON(`${base}/run_manifest.json`);
      const summary = await getJSON(`${base}/summary.json`).catch(() => null);
      const fill = await getJSON(`${rootPath}/_diagnostics/fill_impact/${name}/fill_impact.json`).catch(() => null);
      const seaPolicy = manifest.policies?.sea ?? 'none';
      const frames = (manifest.frames || []).map((f) => ({ date: f.date, time: f.time ?? frameTime(f) }));
      const cells = manifest.cells || [];
      const bounds = manifest.resolved_bounds || [
        Math.min(...cells.map((c) => c.bounds[0])), Math.min(...cells.map((c) => c.bounds[1])),
        Math.max(...cells.map((c) => c.bounds[2])), Math.max(...cells.map((c) => c.bounds[3]))];
      const totalPx = cells.reduce((s, c) => s + c.width * c.height, 0);
      const factor = Math.max(1, Math.ceil(Math.sqrt(totalPx / DISPLAY_PIXEL_BUDGET)));
      state.run = { rootPath, name, base, manifest, summary, fill, seaPolicy, policy: policyOf(seaPolicy), frames, cells, bounds, factor };
      state.cache.clear(); state.images.clear();
      $('#root-input').value = rootPath;
      renderRunInfo();
      renderLegend();
      renderWholeRun();
      renderFill();
      map.setOutlines(cells.map((c) => c.bounds));
      map.fit(bounds);
      const range = $('#frame-range');
      range.max = String(Math.max(0, frames.length - 1));
      $('#frame-select').innerHTML = frames.map((f, i) => `<option value="${i}">${esc(f.date)} ${esc(f.time)}</option>`).join('');
      const start = frameKey ? Math.max(0, frames.findIndex((f) => `${f.date}/${f.time}` === frameKey)) : 0;
      selectFrame(start);
    } catch (err) {
      state.run = null;
      $('#run-info').innerHTML = alertBox(err);
    }
  }

  function renderRunInfo() {
    const r = state.run, m = r.manifest;
    const warn = [];
    if (m.status !== 'complete') warn.push(`Run status is "${esc(m.status)}", not complete. Frames may be missing.`);
    if (!r.policy) warn.push(`Unknown sea policy "${esc(r.seaPolicy)}". Group statistics are withheld; see docs/OUTPUT_CODES.md.`);
    if (m.tool?.dirty) warn.push('The run was produced from a working tree with uncommitted changes (tool.dirty = true).');
    if (r.factor > 1) warn.push(`The map shows every ${r.factor}th pixel (nearest) to stay responsive. Statistics and pixel inspection use every pixel.`);
    const rc = m.region_config || {};
    $('#run-info').innerHTML = `
      <dl class="kv">
        <dt>Name</dt><dd class="mono">${esc(r.name)}</dd>
        <dt>Status</dt><dd>${esc(m.status)}</dd>
        <dt>Run ID</dt><dd class="mono small">${esc((m.run_id || '').slice(0, 16))}…</dd>
        <dt>Policies</dt><dd class="small">engine ${esc(m.policies?.engine)} · sea ${esc(r.seaPolicy)}</dd>
        ${m.source_identity?.view_id ? `<dt>View</dt><dd class="mono small">${esc(m.source_identity.view_id.slice(0, 16))}…</dd>` : ''}
        <dt>Corners</dt><dd class="mono small">${esc(rc.crs)} ${esc(JSON.stringify(rc.lower_left))} → ${esc(JSON.stringify(rc.upper_right))}</dd>
        <dt>Cells</dt><dd>${r.cells.length} · ${fmtInt(r.cells.reduce((s, c) => s + c.width * c.height, 0))} px</dd>
        <dt>Frames</dt><dd>${r.frames.length}${m.dropped_times?.length ? ` · ${m.dropped_times.length} requested times dropped (outside daylight)` : ''}</dd>
        <dt>Code</dt><dd class="mono small">${esc((m.tool?.commit || '').slice(0, 7))}${m.tool?.dirty ? ' (dirty)' : ''}</dd>
      </dl>
      ${warn.map((w) => `<div class="alert warn">${w}</div>`).join('')}`;
  }

  function renderLegend() {
    const r = state.run;
    const codes = layerCodes(state.layer, r?.seaPolicy);
    if (!codes) { $('#legend').innerHTML = '<p class="small">No legend for this sea policy.</p>'; return; }
    const note = state.layer === 'shade'
      ? '<p class="small muted">Grey (255) is invalid or uncertain. It is not shade and must never be read as sunlit.</p>'
      : state.layer === 'surface' ? `<p class="small muted">Surface codes depend on the run's sea policy: ${esc(r?.policy?.name || r?.seaPolicy || '')}.</p>` : '';
    $('#legend').innerHTML = Object.entries(codes).map(([k, v]) =>
      `<div class="legend-row"><span class="swatch" style="background:${v.color}"></span><span class="mono">${k}</span><span>${esc(v.label)}</span></div>`).join('') + note;
  }

  function selectFrame(i) {
    if (!state.run || !state.run.frames.length) return;
    state.frame = i;
    $('#frame-range').value = String(i);
    $('#frame-select').value = String(i);
    drawFrame();
    renderFrameStats();
    if (state.lastPoint) inspect(...state.lastPoint);
    syncHash();
  }

  function syncHash() {
    const r = state.run;
    if (!r) return;
    const f = r.frames[state.frame];
    setHash('results', { root: r.rootPath, run: r.name, frame: f ? `${f.date}/${f.time}` : '', layer: state.layer });
  }

  function framePath(f) { return `${state.run.base}/${f.date}/${f.time}`; }

  async function layerArray(f, layer, cell) {
    const key = `${f.date}/${f.time}/${layer}/${cell.id}`;
    if (layer === 'surface') {
      // Surface is identical in every frame; reuse any decoded frame.
      for (const [k, v] of state.cache) if (k.endsWith(`/surface/${cell.id}`)) return v;
    }
    if (!state.cache.has(key)) {
      state.cache.set(key, fetchTiff(`/${framePath(f)}/${layer}/${cell.id}.tif`));
      if (state.cache.size > 60) state.cache.delete(state.cache.keys().next().value);
    }
    return state.cache.get(key);
  }

  async function drawFrame() {
    const r = state.run, f = r.frames[state.frame], token = ++state.token, layer = state.layer;
    const lut = palette(layer, r.seaPolicy);
    $('#map-hint').textContent = `Loading ${f.date} ${f.time} ${layer} ...`;
    try {
      const overlays = await Promise.all(r.cells.map(async (cell) => {
        const key = `${f.date}/${f.time}/${layer}/${cell.id}`;
        if (!state.images.has(key)) {
          const t = await layerArray(f, layer, cell);
          state.images.set(key, colorize(t, lut, r.factor));
          if (state.images.size > 4 * r.cells.length + 8) state.images.delete(state.images.keys().next().value);
        }
        return { image: state.images.get(key), bounds: cell.bounds };
      }));
      if (token !== state.token) return;
      map.setOverlays(overlays);
      $('#map-hint').textContent = `${f.date} ${f.time} · ${layer}. Drag to pan, wheel to zoom, click a pixel to inspect it.`;
    } catch (err) {
      if (token === state.token) $('#map-hint').textContent = `Could not draw this frame: ${err.message}`;
    }
  }

  async function renderFrameStats() {
    const r = state.run, f = r.frames[state.frame];
    const box = $('#frame-stats');
    try {
      const frame = await getJSON(`${framePath(f)}/frame.json`);
      if (r.frames[state.frame] !== f) return;
      const issues = reconcile(frame);
      const s = frameStats(frame.combinations, r.seaPolicy);
      const elev = (frame.solar_by_tile || []).map((t) => t.apparent_elevation_deg);
      const sun = elev.length ? `Sun (tile centres): apparent elevation ${Math.min(...elev).toFixed(1)}–${Math.max(...elev).toFixed(1)}°, azimuth ${(frame.solar_by_tile[0].azimuth_deg).toFixed(1)}°.` : '';
      box.innerHTML = `<p class="small"><span class="mono">${esc(frame.local_time || `${f.date} ${f.time}`)}</span> · ${fmtInt(frame.pixel_count)} px. ${sun}</p>`
        + (issues.length ? `<div class="alert">Counts do not reconcile: ${esc(issues.slice(0, 3).join('; '))}</div>` : '<p class="small ok-text">Counts reconcile with value_counts and pixel_count.</p>')
        + (s.policy ? groupTables(s) : '<div class="alert warn">Unknown sea policy: group statistics withheld.</div>');
    } catch (err) { box.innerHTML = alertBox(err); }
  }

  async function inspect(x, y) {
    state.lastPoint = [x, y];
    const r = state.run, box = $('#pixel');
    if (!r) return;
    const cell = r.cells.find((c) => x >= c.bounds[0] && x < c.bounds[2] && y >= c.bounds[1] && y < c.bounds[3]);
    const [lat, lon] = toWGS84(x, y);
    const where = `<p class="small mono">HK1980 E ${x.toFixed(1)} N ${y.toFixed(1)} · WGS84 ≈ ${lat.toFixed(6)}, ${lon.toFixed(6)}</p>`;
    if (!cell) { box.innerHTML = where + '<p class="small muted">Outside the run.</p>'; return; }
    const col = Math.floor((x - cell.bounds[0]) / 0.5), row = Math.floor((cell.bounds[3] - y) / 0.5);
    const f = r.frames[state.frame];
    try {
      const [sh, q, su] = await Promise.all(['shade', 'quality', 'surface'].map((l) => layerArray(f, l, cell)));
      const i = row * sh.width + col;
      const surfCodes = layerCodes('surface', r.seaPolicy) || {};
      const frame = await getJSON(`${framePath(f)}/frame.json`);
      const solar = (frame.solar_by_tile || []).find((t) => t.source_name === cell.source_tile);
      box.innerHTML = where + `<dl class="kv">
        <dt>Cell</dt><dd class="mono small">${esc(cell.id)} · row ${row}, col ${col}</dd>
        <dt>Shade</dt><dd><span class="mono">${sh.data[i]}</span> ${esc(SHADE[sh.data[i]]?.label || 'unknown code')}</dd>
        <dt>Quality</dt><dd><span class="mono">${q.data[i]}</span> ${esc(QUALITY[q.data[i]]?.label || 'unknown code')}</dd>
        <dt>Surface</dt><dd><span class="mono">${su.data[i]}</span> ${esc(surfCodes[su.data[i]]?.label || 'unknown code')}</dd>
        ${solar ? `<dt>Sun</dt><dd class="small">tile ${esc(solar.source_name.replace('.tif', ''))}: apparent ${solar.apparent_elevation_deg.toFixed(2)}°, azimuth ${solar.azimuth_deg.toFixed(1)}° (direction bin ${solar.direction_deg}°), distant threshold ${solar.threshold_deg.toFixed(2)}°</dd>` : ''}
      </dl>`;
    } catch (err) { box.innerHTML = where + alertBox(err); }
  }

  function renderWholeRun() {
    const r = state.run, box = $('#day');
    if (!r.summary || !r.policy) { box.innerHTML = '<p class="small muted">No summary.json, or unknown sea policy.</p>'; return; }
    const rows = r.summary.frames.map((fr) => ({ date: fr.date, time: fr.time, s: summaryFrameStats(fr, r.seaPolicy) }));
    const groups = r.policy.report.map((g) => g.key);
    const sel = `<div class="seg small-seg" role="group" aria-label="Group">${r.policy.report.map((g, i) => `<button type="button" data-g="${g.key}" aria-pressed="${i === 0}">${esc(g.label)}</button>`).join('')}</div>`;
    box.innerHTML = sel + '<div id="day-body"></div>';
    const show = (key) => {
      box.querySelectorAll('[data-g]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.g === key)));
      const series = rows.map((x) => ({ label: `${x.date} ${x.time}`, g: x.s.report.find((g) => g.key === key) }));
      const byDate = {};
      for (const x of rows) (byDate[x.date] ||= []).push(x.s.report.find((g) => g.key === key));
      const mean = (arr, f) => arr.reduce((s, g) => s + f(g), 0) / arr.length;
      const table = `<div class="table-wrap"><table class="compact"><thead><tr><th>Date</th><th>Frames</th><th>Shaded (lower–upper)</th><th>Sunlit (lower–upper)</th><th>Uncertain</th></tr></thead><tbody>${
        Object.entries(byDate).map(([d, gs]) => `<tr><td class="mono">${esc(d)}</td><td>${gs.length}</td><td>${pct(mean(gs, (g) => g.bounds.shaded[0]))}–${pct(mean(gs, (g) => g.bounds.shaded[1]))}</td><td>${pct(mean(gs, (g) => g.bounds.sunlit[0]))}–${pct(mean(gs, (g) => g.bounds.sunlit[1]))}</td><td>${pct(mean(gs, (g) => g.fraction.uncertain))}</td></tr>`).join('')
      }</tbody></table></div>`;
      box.querySelector('#day-body').innerHTML = chart(series)
        + '<p class="small muted">Means over frames of fractions of the whole group (every pixel of the group is the denominator). Bounds: lower = label / group; upper = (label + uncertain) / group.</p>'
        + table;
    };
    box.querySelectorAll('[data-g]').forEach((b) => b.addEventListener('click', () => show(b.dataset.g)));
    show(groups[0]);
  }

  function renderFill() {
    const r = state.run, box = $('#fill');
    if (!r.fill) { box.innerHTML = '<p class="small muted">No fill-impact diagnostic for this run. For sea-2.2 runs, see the guide (tools.sea2 fill-impact).</p>'; return; }
    const fr = r.fill.frames || [];
    const mean = fr.length ? fr.reduce((s, x) => s + x.fill_dependent_land, 0) / fr.length : null;
    box.innerHTML = `<p class="small">Fill-dependent Land = dependency codes 1–3 within Land / all Land. It is a dependency share, <strong>not</strong> a shade share. Mean over the ${fr.length} diagnosed frames: <strong>${pct(mean)}</strong>.</p>
      <div class="table-wrap"><table class="compact"><thead><tr><th>Frame</th><th>Fill-dependent Land</th>${[0, 1, 2, 3, 4].map((c) => `<th title="${esc(DEPENDENCY[c])}">Land code ${c}</th>`).join('')}</tr></thead><tbody>${
        fr.map((x) => `<tr><td class="mono">${esc(x.time)}<div class="muted small">${esc(x.date)}</div></td><td>${pct(x.fill_dependent_land)}</td>${[0, 1, 2, 3, 4].map((c) => `<td>${fmtInt(x.groups?.land?.counts?.[c] ?? 0)}</td>`).join('')}</tr>`).join('')
      }</tbody></table></div>
      <details><summary>Dependency codes</summary>${Object.entries(DEPENDENCY).map(([k, v]) => `<div class="small"><span class="mono">${k}</span> ${esc(v)}</div>`).join('')}</details>`;
  }

  if (params.run) loadRun(params.root || 'outputs/shade_map', params.run, params.frame);
  else listRuns($('#root-input').value.trim());
}

function frameTime(f) {
  const key = Object.keys(f.files || {}).find((k) => k.endsWith('/frame.json'));
  return key ? key.split('/')[1] : '';
}

function colorize(t, lut, factor) {
  const w = Math.ceil(t.width / factor), h = Math.ceil(t.height / factor);
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  const img = ctx.createImageData(w, h);
  const px = img.data;
  for (let r = 0, o = 0; r < h; r++) {
    const row = r * factor * t.width;
    for (let c = 0; c < w; c++, o += 4) {
      const v = t.data[row + c * factor] * 4;
      px[o] = lut[v]; px[o + 1] = lut[v + 1]; px[o + 2] = lut[v + 2]; px[o + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas;
}

function groupTables(s) {
  const out = s.report.map((g) => {
    if (!g.pixels) return `<h3>${esc(g.label)}</h3><p class="small muted">No pixels.</p>`;
    const q = [1, 2, 3, 4].filter((k) => g.byQuality[k]).map((k) => `q${k} ${fmtInt(g.byQuality[k])} (${pct(g.byQuality[k] / g.pixels)})`).join(', ');
    return `<h3>${esc(g.label)} <span class="muted small">surface ${g.classes.join('+')} · ${fmtInt(g.pixels)} px</span></h3>
      <div class="table-wrap"><table class="compact"><thead><tr><th></th><th>Pixels</th><th>Share of group</th></tr></thead><tbody>
        <tr><td><span class="swatch" style="background:${SHADE[0].color}"></span> Sunlit</td><td>${fmtInt(g.sunlit)}</td><td>${pct(g.fraction.sunlit)}</td></tr>
        <tr><td><span class="swatch" style="background:${SHADE[1].color}"></span> Shaded</td><td>${fmtInt(g.shaded)}</td><td>${pct(g.fraction.shaded)}</td></tr>
        <tr><td><span class="swatch" style="background:${SHADE[255].color}"></span> Uncertain</td><td>${fmtInt(g.uncertain)}</td><td>${pct(g.fraction.uncertain)}</td></tr>
      </tbody></table></div>
      ${q ? `<p class="small">Uncertain by quality: ${q}.</p>` : ''}
      <p class="small">Shaded ${pct(g.bounds.shaded[0])}–${pct(g.bounds.shaded[1])} · Sunlit ${pct(g.bounds.sunlit[0])}–${pct(g.bounds.sunlit[1])} <span class="muted">(lower–upper bounds)</span></p>`;
  }).join('');
  const counts = s.count.map((c) => `${esc(c.label)}: ${fmtInt(c.pixels)} px`).join(' · ');
  const notes = s.policy.notes.map((n) => `<li>${esc(n)}</li>`).join('');
  return out + `<p class="small muted">Counted only: ${counts}.${s.unknownSurface ? ` Unknown surface codes: ${fmtInt(s.unknownSurface)} px.` : ''}</p><ul class="notes small">${notes}</ul>`;
}

function chart(series) {
  const W = 360, H = 150, L = 34, B = 22, T = 8, R = 6;
  const n = series.length;
  if (!n) return '';
  const x = (i) => L + (n === 1 ? (W - L - R) / 2 : (i * (W - L - R)) / (n - 1));
  const y = (v) => T + (1 - v) * (H - T - B);
  const line = (f) => series.map((s, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(f(s.g)).toFixed(1)}`).join('');
  const band = series.map((s, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(s.g.bounds.shaded[1]).toFixed(1)}`).join('')
    + series.slice().reverse().map((s, j) => `L${x(n - 1 - j).toFixed(1)},${y(s.g.bounds.shaded[0]).toFixed(1)}`).join('') + 'Z';
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="grid"/><text x="${L - 4}" y="${y(v) + 4}" text-anchor="end">${v * 100}%</text>`).join('');
  const lab = [0, Math.floor((n - 1) / 2), n - 1].filter((v, i, a) => a.indexOf(v) === i)
    .map((i) => `<text x="${x(i)}" y="${H - 6}" text-anchor="${i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle'}">${esc(series[i].label.split(' ')[1] || series[i].label)}</text>`).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Shaded share bounds over frames">
    ${ticks}
    <path d="${band}" class="band"/>
    <path d="${line((g) => g.bounds.shaded[0])}" class="lower"/>
    <path d="${line((g) => g.fraction.uncertain)}" class="unc"/>
    ${lab}
  </svg>
  <div class="small chart-key"><span class="key band-key"></span>Shaded bounds (lower–upper) <span class="key unc-key"></span>Uncertain</div>`;
}

function alertBox(err) { return `<div class="alert">${esc(err.message || String(err))}</div>`; }
