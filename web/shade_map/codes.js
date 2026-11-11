// Output codes and statistics groups, transcribed from docs/OUTPUT_CODES.md (decisions D-009, D-015, D-016).
// If that document changes, update this file; the page refuses group statistics for unknown sea policies.

export const SHADE = {
  0: { label: 'Sunlit', color: '#F2C14E' },
  1: { label: 'Shaded', color: '#2B4C7E' },
  255: { label: 'Invalid or uncertain (not shade; never read as sunlit)', color: '#9E9E9E' },
};

export const QUALITY = {
  0: { label: 'Valid: shade label is 0 or 1', color: '#E9E7E0' },
  1: { label: 'Missing target DSM', color: '#7B2D26' },
  2: { label: 'No obstruction found, 1 km sunward support incomplete', color: '#D1495B' },
  3: { label: 'Distant-obstruction sensitivity (beyond 1 km, low sun)', color: '#EDAE49' },
  4: { label: 'Sun at or below the horizon', color: '#3D348B' },
};

const SURFACE_RAW = {
  0: { label: 'DSM-observed surface', color: '#CDBE9C' },
  255: { label: 'No DSM value (sea, voids and empty cells not distinguished)', color: '#9E9E9E' },
};

const SURFACE_SEA_22 = {
  0: { label: 'DSM-observed surface', color: '#CDBE9C' },
  1: { label: 'Water, filled at h_fill, in a supplied DSM tile', color: '#4F9BD9' },
  2: { label: 'Water, filled at h_fill, in a synthetic tile', color: '#A7D0F2' },
  3: { label: 'Enclosed NoData filled at h_fill (land voids, reservoirs)', color: '#8E6C8A' },
  4: { label: 'Open NoData not labelled water, filled at h_fill', color: '#7FB7A4' },
  255: { label: 'Outside the sea view domain', color: '#FFFFFF' },
};

/**
 * Statistics groups per run sea policy (docs/OUTPUT_CODES.md, "Groups for statistics").
 * `report` groups get sunlit/shaded/uncertain over the whole group; `count` groups are counted only.
 */
export const POLICIES = {
  none: {
    name: 'Raw DSM (no sea policy)',
    surface: SURFACE_RAW,
    report: [{ key: 'land', label: 'Land L', classes: [0] }],
    count: [{ key: 'nodsm', label: 'No DSM (255)', classes: [255] }],
    notes: ['Raw runs cannot separate sea from land voids; surface 255 is counted only.'],
  },
  'SW-SEA-POLICY-2.2': {
    name: 'SW-SEA-POLICY-2.2 (every NoData filled at 0 m HKPD)',
    surface: SURFACE_SEA_22,
    report: [
      { key: 'land', label: 'Land L', classes: [0, 3] },
      { key: 'water', label: 'Water W', classes: [1, 2] },
    ],
    count: [
      { key: 'other', label: 'Other (4)', classes: [4] },
      { key: 'outside', label: 'Outside domain (255)', classes: [255] },
    ],
    notes: [
      'Water labels are less certain than land: h_fill is about 1.4 m below the median DSM waterline, so shade on near-shore water is slightly overstated.',
      'Land includes enclosed fills (class 3, e.g. reservoirs); where the true surface is higher the fill forms a pit.',
      'Labels on filled targets are model results under h_fill. Report fill dependence separately (fill-impact).',
    ],
  },
};

export function policyOf(seaPolicy) {
  return POLICIES[seaPolicy ?? 'none'] || null;
}

export function layerCodes(layer, seaPolicy) {
  if (layer === 'shade') return SHADE;
  if (layer === 'quality') return QUALITY;
  return policyOf(seaPolicy)?.surface || null;
}

/** 256-entry RGBA lookup table for a layer. Unknown codes are magenta so they cannot hide. */
export function palette(layer, seaPolicy) {
  const codes = layerCodes(layer, seaPolicy) || {};
  const lut = new Uint8ClampedArray(256 * 4);
  for (let v = 0; v < 256; v++) {
    const hex = codes[v]?.color || '#FF00FF';
    lut.set([parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16), 255], v * 4);
  }
  return lut;
}
