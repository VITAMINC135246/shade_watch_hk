// Hash router for the two pages. Served by the local static server from the repository root.
import { renderResults } from './results.js';
import { renderRequest } from './request.js';

const app = document.getElementById('app');
const pages = { results: renderResults, request: renderRequest };

function route() {
  const page = (location.hash.match(/^#\/([a-z]+)/) || [])[1] || 'results';
  document.querySelectorAll('nav a[data-page]').forEach((a) => {
    if (a.dataset.page === page) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  app.innerHTML = '';
  (pages[page] || renderResults)(app).catch?.((err) => {
    app.innerHTML = `<div class="alert">${String(err.message || err)}</div>`;
  });
}

if (location.protocol === 'file:') {
  document.getElementById('file-warning').hidden = false;
} else {
  window.addEventListener('hashchange', route);
  route();
}
