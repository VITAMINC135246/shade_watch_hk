// Minimal GeoTIFF reader for shade_map publications only: classic TIFF, one 8-bit unsigned band,
// tiles or strips, no compression or DEFLATE (zlib), predictor 1 or 2. Anything else is refused,
// so a format change can never be displayed silently. Uses the browser's DecompressionStream.

const TAG = {
  ImageWidth: 256, ImageLength: 257, BitsPerSample: 258, Compression: 259, StripOffsets: 273,
  SamplesPerPixel: 277, RowsPerStrip: 278, StripByteCounts: 279, PlanarConfiguration: 284,
  Predictor: 317, TileWidth: 322, TileLength: 323, TileOffsets: 324, TileByteCounts: 325,
  SampleFormat: 339, ModelPixelScale: 33550, ModelTiepoint: 33922, GDALNoData: 42113,
};
const TYPE_SIZE = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 16: 8 };

function readIfd(view, offset, le) {
  const n = view.getUint16(offset, le);
  const tags = {};
  for (let i = 0; i < n; i++) {
    const p = offset + 2 + i * 12;
    const tag = view.getUint16(p, le), type = view.getUint16(p + 2, le), count = view.getUint32(p + 4, le);
    const size = (TYPE_SIZE[type] || 1) * count;
    const at = size <= 4 ? p + 8 : view.getUint32(p + 8, le);
    const values = [];
    for (let k = 0; k < count; k++) {
      switch (type) {
        case 1: case 2: case 7: values.push(view.getUint8(at + k)); break;
        case 3: values.push(view.getUint16(at + 2 * k, le)); break;
        case 4: values.push(view.getUint32(at + 4 * k, le)); break;
        case 12: values.push(view.getFloat64(at + 8 * k, le)); break;
        case 11: values.push(view.getFloat32(at + 4 * k, le)); break;
        default: values.push(null);
      }
    }
    tags[tag] = type === 2 ? String.fromCharCode(...values).replace(/\0+$/, '') : values;
  }
  return tags;
}

async function inflate(bytes) {
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/** Decode an ArrayBuffer holding a shade_map GeoTIFF layer. */
export async function decodeTiff(buffer) {
  const view = new DataView(buffer);
  const order = view.getUint16(0, false);
  if (order !== 0x4949 && order !== 0x4D4D) throw new Error('Not a TIFF file');
  const le = order === 0x4949;
  const magic = view.getUint16(2, le);
  if (magic !== 42) throw new Error(magic === 43 ? 'BigTIFF is not supported' : 'Not a classic TIFF');
  const t = readIfd(view, view.getUint32(4, le), le);
  const first = (k, d) => (t[k] ? t[k][0] : d);
  const width = first(TAG.ImageWidth), height = first(TAG.ImageLength);
  const bits = first(TAG.BitsPerSample, 1), spp = first(TAG.SamplesPerPixel, 1);
  const fmt = first(TAG.SampleFormat, 1), compression = first(TAG.Compression, 1);
  const predictor = first(TAG.Predictor, 1);
  if (bits !== 8 || spp !== 1 || fmt !== 1) throw new Error('Only single-band 8-bit unsigned layers are supported');
  if (![1, 8, 32946].includes(compression)) throw new Error(`Unsupported compression ${compression}`);
  if (![1, 2].includes(predictor)) throw new Error(`Unsupported predictor ${predictor}`);
  const tiled = !!t[TAG.TileWidth];
  const bw = tiled ? first(TAG.TileWidth) : width;
  const bh = tiled ? first(TAG.TileLength) : first(TAG.RowsPerStrip, height);
  const offsets = t[tiled ? TAG.TileOffsets : TAG.StripOffsets];
  const counts = t[tiled ? TAG.TileByteCounts : TAG.StripByteCounts];
  const across = tiled ? Math.ceil(width / bw) : 1;
  const out = new Uint8Array(width * height);
  await Promise.all(offsets.map(async (off, i) => {
    let block = new Uint8Array(buffer, off, counts[i]);
    if (compression !== 1) block = await inflate(block);
    const bx = (i % across) * bw, by = Math.floor(i / across) * bh;
    const rows = Math.min(bh, height - by), cols = Math.min(bw, width - bx);
    if (block.length < (rows - 1) * bw + cols) throw new Error('Truncated TIFF block');
    for (let r = 0; r < rows; r++) {
      const row = block.subarray(r * bw, r * bw + bw);
      if (predictor === 2) for (let c = 1; c < bw && c < row.length; c++) row[c] = (row[c] + row[c - 1]) & 0xFF;
      out.set(row.subarray(0, cols), (by + r) * width + bx);
    }
  }));
  const scale = t[TAG.ModelPixelScale], tie = t[TAG.ModelTiepoint];
  const transform = scale && tie ? [scale[0], 0, tie[3] - tie[0] * scale[0], 0, -scale[1], tie[4] + tie[1] * scale[1]] : null;
  const nd = t[TAG.GDALNoData];
  return { width, height, data: out, transform, nodata: nd === undefined || nd === '' ? null : Number(nd) };
}

/** Fetch and decode a layer; throws with the URL on HTTP errors. */
export async function fetchTiff(url, fetchImpl = fetch) {
  const res = await fetchImpl(url);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return decodeTiff(await res.arrayBuffer());
}
