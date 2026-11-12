// Thin client for the local runner API (runner-api-1.0). Add ?mock to the page URL to use mock.js instead.
import { mockFetch, mockPreviewUrl } from './mock.js';

export const MOCK = new URLSearchParams(location.search).has('mock');

export class ApiError extends Error {
  constructor(code, message, status) { super(message); this.code = code; this.status = status; }
}

async function call(method, path, body) {
  const opts = { method, headers: { Accept: 'application/json' } };
  if (body !== undefined) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  let res;
  try {
    res = MOCK ? await mockFetch(method, path, body) : await fetch(path, opts);
  } catch (err) {
    throw new ApiError('network', 'The local runner did not answer. Is `python -m tools.runner serve` running?', 0);
  }
  const text = await res.text();
  let data = {};
  if (text) {
    try { data = JSON.parse(text); } catch { throw new ApiError('bad_json', `Invalid JSON from ${path}`, res.status); }
  }
  if (!res.ok || data.error) {
    throw new ApiError(data.error?.code || `http_${res.status}`, data.error?.message || res.statusText || 'Request failed', res.status);
  }
  return data;
}

const q = (params) => Object.entries(params)
  .filter(([, v]) => v !== undefined && v !== null && v !== '')
  .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');

export const api = {
  health: () => call('GET', '/api/health'),
  catalogues: () => call('GET', '/api/catalogues'),
  tiles: (catalogue, bbox) => call('GET', `/api/tiles?${q({ catalogue, bbox: bbox.join(',') })}`),
  transform: (from, points) => call('POST', '/api/transform', { from, points }),
  plan: (request) => call('POST', '/api/plan', request),
  start: (plan_id, label) => call('POST', '/api/jobs', { plan_id, label }),
  jobs: () => call('GET', '/api/jobs'),
  job: (id) => call('GET', `/api/jobs/${encodeURIComponent(id)}`),
  cancel: (id) => call('POST', `/api/jobs/${encodeURIComponent(id)}/cancel`),
  resumeIncomplete: () => call('POST', '/api/jobs/resume-incomplete'),
  results: (id) => call('GET', `/api/results/${encodeURIComponent(id)}`),
  stats: (id) => call('GET', `/api/results/${encodeURIComponent(id)}/stats`),
  files: (id) => call('GET', `/api/results/${encodeURIComponent(id)}/files`),
  pixel: (id, frame, x, y) => call('GET', `/api/results/${encodeURIComponent(id)}/pixel?${q({ frame, x, y })}`),
  previewUrl: (id, frame, layer, max = 2048) => (MOCK
    ? mockPreviewUrl(id, frame, layer)
    : `/api/results/${encodeURIComponent(id)}/frames/${frame}/preview.png?${q({ layer, max })}`),
};
