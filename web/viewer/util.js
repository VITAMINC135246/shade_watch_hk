// Small helpers shared by the pages. All paths are relative to the repository root, which the
// local static server serves (python3 -m http.server --bind 127.0.0.1 from the repository root).

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function el(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

function url(path) {
  return '/' + path.replace(/^\/+/, '').split('/').map(encodeURIComponent).join('/');
}

const jsonCache = new Map();

/** GET JSON (cached per page load; run outputs are immutable once published). */
export async function getJSON(path) {
  if (!jsonCache.has(path)) {
    jsonCache.set(path, fetch(url(path)).then(async (res) => {
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${path}`);
      return res.json();
    }));
    jsonCache.get(path).catch(() => jsonCache.delete(path));
  }
  return jsonCache.get(path);
}

export async function exists(path) {
  try { return (await fetch(url(path), { method: 'HEAD' })).ok; } catch { return false; }
}

/** Parse the directory listing produced by Python's http.server. */
export async function listDir(path) {
  const res = await fetch(url(path.replace(/\/+$/, '')) + '/');
  if (!res.ok) throw new Error(`${res.status}: cannot list ${path} (is the local server running from the repository root?)`);
  const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
  return [...doc.querySelectorAll('a[href]')]
    .map((a) => decodeURIComponent(a.getAttribute('href')))
    .filter((h) => !h.startsWith('?') && !h.startsWith('/') && !h.startsWith('..') && h !== '')
    .map((h) => ({ name: h.replace(/\/$/, ''), dir: h.endsWith('/') }));
}

export function hashParams() {
  const q = location.hash.split('?')[1] || '';
  return Object.fromEntries(new URLSearchParams(q));
}

/** Update the hash without re-rendering the page. */
export function setHash(page, params) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== '')).toString();
  history.replaceState(null, '', `#/${page}${q ? `?${q}` : ''}`);
}

export function download(name, text, type = 'application/json') {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
}
