// Canvas map in HK1980 Grid (EPSG:2326) metres. No basemap and no network: it draws the DSM tile
// lattice, a selection rectangle, tile picks, no-DSM areas and an optional raster overlay that is
// axis-aligned in HK1980 (result previews).

const COLORS = {
  sea: '#E9EFF4', tile: '#CFC6B0', tileEdge: '#B5AC96', pick: '#9CC0DE', sel: '#1D5C8C',
  selFill: 'rgba(29, 92, 140, 0.12)', nodata: 'rgba(126, 87, 194, 0.18)', marker: '#D9480F',
};

export class HKMap {
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.opts = opts;
    this.tiles = [];
    this.picked = new Set();
    this.selection = null;
    this.noData = [];
    this.overlay = null;
    this.marker = null;
    this.mode = opts.mode || 'draw';
    this.view = { cx: 832000, cy: 824000, scale: 0.01 };
    this._drag = null;
    this._bind();
    this._resizeObserver = new ResizeObserver(() => this.resize());
    this._resizeObserver.observe(canvas);
    this.resize();
  }

  destroy() { this._resizeObserver.disconnect(); }
  setMode(mode) { this.mode = mode; this.canvas.dataset.mode = mode; }
  setTiles(tiles) { this.tiles = tiles; this.draw(); }
  setSelection(b) { this.selection = b; this.draw(); }
  setPicked(names) { this.picked = new Set(names); this.draw(); }
  setNoData(areas) { this.noData = areas || []; this.draw(); }
  setMarker(xy) { this.marker = xy; this.draw(); }
  setOverlay(url, bounds) {
    if (!url) { this.overlay = null; this.draw(); return; }
    const img = new Image();
    img.onload = () => { this.overlay = { img, bounds }; this.draw(); };
    img.src = url;
  }

  fit(b, pad = 0.9) {
    const w = this.canvas.clientWidth || 600, h = this.canvas.clientHeight || 400;
    this.view.cx = (b[0] + b[2]) / 2;
    this.view.cy = (b[1] + b[3]) / 2;
    this.view.scale = Math.min(w / (b[2] - b[0]), h / (b[3] - b[1])) * pad;
    this.draw();
  }
  zoom(f, px, py) {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    const [wx, wy] = this.toWorld(px ?? w / 2, py ?? h / 2);
    this.view.scale = Math.min(20, Math.max(0.002, this.view.scale * f));
    const [sx, sy] = this.toScreen(wx, wy);
    this.view.cx += (sx - (px ?? w / 2)) / this.view.scale;
    this.view.cy -= (sy - (py ?? h / 2)) / this.view.scale;
    this.draw();
  }
  toScreen(x, y) {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    return [w / 2 + (x - this.view.cx) * this.view.scale, h / 2 - (y - this.view.cy) * this.view.scale];
  }
  toWorld(px, py) {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    return [this.view.cx + (px - w / 2) / this.view.scale, this.view.cy - (py - h / 2) / this.view.scale];
  }
  resize() {
    const dpr = window.devicePixelRatio || 1;
    const r = this.canvas.getBoundingClientRect();
    this.canvas.width = Math.max(1, Math.round(r.width * dpr));
    this.canvas.height = Math.max(1, Math.round(r.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.draw();
  }
  _rect(b) {
    const [x0, y0] = this.toScreen(b[0], b[3]);
    const [x1, y1] = this.toScreen(b[2], b[1]);
    return [x0, y0, x1 - x0, y1 - y0];
  }

  draw() {
    const ctx = this.ctx, w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    ctx.fillStyle = COLORS.sea;
    ctx.fillRect(0, 0, w, h);
    const edges = this.view.scale > 0.03;
    for (const t of this.tiles) {
      const [x, y, rw, rh] = this._rect(t.b);
      if (x > w || y > h || x + rw < 0 || y + rh < 0) continue;
      ctx.fillStyle = this.picked.has(t.name) ? COLORS.pick : COLORS.tile;
      ctx.fillRect(x, y, rw + 0.5, rh + 0.5);
      if (edges) { ctx.strokeStyle = COLORS.tileEdge; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, rw, rh); }
    }
    if (this.overlay) {
      const [x, y, rw, rh] = this._rect(this.overlay.bounds);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(this.overlay.img, x, y, rw, rh);
      ctx.strokeStyle = '#3C444D';
      ctx.strokeRect(x + 0.5, y + 0.5, rw, rh);
    }
    for (const a of this.noData) {
      const [x, y, rw, rh] = this._rect(a);
      ctx.fillStyle = COLORS.nodata;
      ctx.fillRect(x, y, rw, rh);
    }
    const sel = this._drag?.kind === 'draw' ? this._drag.rect : this.selection;
    if (sel) {
      const [x, y, rw, rh] = this._rect(sel);
      ctx.fillStyle = COLORS.selFill;
      ctx.fillRect(x, y, rw, rh);
      ctx.strokeStyle = COLORS.sel;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, rw, rh);
    }
    if (this.marker) {
      const [x, y] = this.toScreen(...this.marker);
      ctx.strokeStyle = COLORS.marker;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x - 11, y); ctx.lineTo(x + 11, y); ctx.moveTo(x, y - 11); ctx.lineTo(x, y + 11); ctx.stroke();
    }
    this._scaleBar(ctx, w, h);
  }
  _scaleBar(ctx, w, h) {
    const target = 120 / this.view.scale;
    const steps = [50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000];
    const m = steps.find((s) => s >= target) || steps[steps.length - 1];
    const px = m * this.view.scale;
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.fillRect(10, h - 34, px + 70, 24);
    ctx.fillStyle = '#15191E';
    ctx.fillRect(16, h - 20, px, 4);
    ctx.font = '12px "IBM Plex Mono", ui-monospace, monospace';
    ctx.fillText(m >= 1000 ? `${m / 1000} km` : `${m} m`, px + 22, h - 15);
  }

  _bind() {
    const c = this.canvas;
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      const r = c.getBoundingClientRect();
      this.zoom(e.deltaY < 0 ? 1.2 : 1 / 1.2, e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });
    c.addEventListener('pointerdown', (e) => {
      const r = c.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      c.setPointerCapture(e.pointerId);
      const pan = this.mode === 'pan' || e.button === 1 || e.button === 2 || e.shiftKey;
      this._drag = { kind: pan ? 'pan' : this.mode, x0: px, y0: py, moved: false, start: this.toWorld(px, py), view: { ...this.view } };
    });
    c.addEventListener('pointermove', (e) => {
      if (!this._drag) return;
      const r = c.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      if (Math.abs(px - this._drag.x0) + Math.abs(py - this._drag.y0) > 3) this._drag.moved = true;
      if (this._drag.kind === 'pan') {
        this.view.cx = this._drag.view.cx - (px - this._drag.x0) / this.view.scale;
        this.view.cy = this._drag.view.cy + (py - this._drag.y0) / this.view.scale;
        this.draw();
      } else if (this._drag.kind === 'draw' && this._drag.moved) {
        const [x1, y1] = this.toWorld(px, py), [x0, y0] = this._drag.start;
        this._drag.rect = [Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1), Math.max(y0, y1)];
        this.draw();
      }
    });
    c.addEventListener('pointerup', (e) => {
      const d = this._drag;
      this._drag = null;
      if (!d) return;
      const r = c.getBoundingClientRect();
      const [wx, wy] = this.toWorld(e.clientX - r.left, e.clientY - r.top);
      if (d.kind === 'draw' && d.moved && d.rect) {
        this.selection = d.rect.map((v) => Math.round(v * 2) / 2);
        this.draw();
        this.opts.onRect?.(this.selection);
      } else if (!d.moved && d.kind === 'tiles') {
        const t = this.tiles.find((k) => wx >= k.b[0] && wx < k.b[2] && wy >= k.b[1] && wy < k.b[3]);
        if (t) {
          if (this.picked.has(t.name)) this.picked.delete(t.name); else this.picked.add(t.name);
          this.draw();
          this.opts.onTiles?.([...this.picked]);
        }
      } else if (!d.moved && (d.kind === 'inspect' || d.kind === 'point')) {
        this.marker = [wx, wy];
        this.draw();
        this.opts.onPoint?.(wx, wy);
      } else {
        this.draw();
      }
    });
    c.addEventListener('contextmenu', (e) => e.preventDefault());
  }
}
