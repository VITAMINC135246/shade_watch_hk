// Group statistics from published counts, following docs/OUTPUT_CODES.md reporting rules:
// the denominator is the whole group; sunlit, shaded and uncertain are reported side by side;
// uncertain is split by quality; prose fractions use lower/upper bounds. No ratio over valid
// labels only (shaded / (shaded + sunlit)) is computed anywhere.

import { policyOf } from './codes.js';

function emptyGroup(def) {
  return { ...def, pixels: 0, sunlit: 0, shaded: 0, uncertain: 0, byQuality: { 1: 0, 2: 0, 3: 0, 4: 0 } };
}

function finish(g) {
  const n = g.pixels;
  const f = (x) => (n ? x / n : null);
  g.fraction = { sunlit: f(g.sunlit), shaded: f(g.shaded), uncertain: f(g.uncertain) };
  g.bounds = {
    shaded: [f(g.shaded), f(g.shaded + g.uncertain)],
    sunlit: [f(g.sunlit), f(g.sunlit + g.uncertain)],
  };
  return g;
}

/**
 * From frame.json `combinations` ({surface, shade, quality, pixels}).
 * Returns {policy, report: [group], count: [group], total, unknownSurface}.
 */
export function frameStats(combinations, seaPolicy) {
  const policy = policyOf(seaPolicy);
  if (!policy) return { policy: null, total: combinations.reduce((s, c) => s + c.pixels, 0) };
  const report = policy.report.map(emptyGroup), count = policy.count.map((d) => ({ ...d, pixels: 0 }));
  let total = 0, unknownSurface = 0;
  for (const c of combinations) {
    total += c.pixels;
    const g = report.find((r) => r.classes.includes(c.surface));
    const k = count.find((r) => r.classes.includes(c.surface));
    if (g) {
      g.pixels += c.pixels;
      if (c.shade === 0) g.sunlit += c.pixels;
      else if (c.shade === 1) g.shaded += c.pixels;
      else { g.uncertain += c.pixels; g.byQuality[c.quality] = (g.byQuality[c.quality] || 0) + c.pixels; }
    } else if (k) k.pixels += c.pixels;
    else unknownSurface += c.pixels;
  }
  return { policy, report: report.map(finish), count, total, unknownSurface };
}

/**
 * From one summary.json frame ({surfaces: [{surface, pixels, counts:{shaded,sunlit,uncertain}, quality_counts}]}).
 */
export function summaryFrameStats(frame, seaPolicy) {
  const combos = [];
  for (const s of frame.surfaces) {
    combos.push({ surface: s.surface, shade: 0, quality: 0, pixels: s.counts.sunlit });
    combos.push({ surface: s.surface, shade: 1, quality: 0, pixels: s.counts.shaded });
    for (const q of [1, 2, 3, 4]) {
      const n = Number(s.quality_counts?.[q] ?? s.quality_counts?.[String(q)] ?? 0);
      if (n) combos.push({ surface: s.surface, shade: 255, quality: q, pixels: n });
    }
  }
  return frameStats(combos, seaPolicy);
}

/** Checks that frame.json combinations agree with its value_counts and pixel_count. */
export function reconcile(frame) {
  const sum = (key) => {
    const m = {};
    for (const c of frame.combinations) m[c[key]] = (m[c[key]] || 0) + c.pixels;
    return m;
  };
  const issues = [];
  const total = frame.combinations.reduce((s, c) => s + c.pixels, 0);
  if (total !== frame.pixel_count) issues.push(`combinations sum ${total} != pixel_count ${frame.pixel_count}`);
  for (const layer of ['shade', 'quality', 'surface']) {
    const got = sum(layer), want = frame.value_counts?.[layer] || {};
    const keys = new Set([...Object.keys(got), ...Object.keys(want)]);
    for (const k of keys) if ((got[k] || 0) !== (want[k] || 0)) issues.push(`${layer} ${k}: ${got[k] || 0} vs ${want[k] || 0}`);
  }
  for (const c of frame.combinations) {
    if ((c.quality === 0) !== (c.shade === 0 || c.shade === 1)) issues.push(`shade ${c.shade} with quality ${c.quality}`);
  }
  return issues;
}

export function pct(x, digits = 1) {
  return x === null || x === undefined ? '—' : `${(100 * x).toFixed(digits)}%`;
}

export function fmtInt(n) {
  return Number(n).toLocaleString('en-US');
}
