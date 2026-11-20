// Turns src/models/<cam>/model.txt (base64 Int16 triangle soup from pack_models.py) into model.bin:
// per part, shared vertices are welded into an indexed mesh, reordered for the GPU cache and compressed
// with meshoptimizer, the same codec glTF uses in EXT_meshopt_compression. The viewer decodes it with
// three's MeshoptDecoder. parts.json gets each part's vertex/index counts and byte ranges.
//   node tools/encode_models.mjs [cam ...]
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(here, '../viewer/package.json'));
const {MeshoptEncoder} = require('meshoptimizer');
await MeshoptEncoder.ready;

const cams = process.argv.slice(2).length ? process.argv.slice(2) : ['ms', 'duos', 'th', 'sw'];
for (const cam of cams) {
  const dir = path.join(here, '../src/models', cam);
  const txt = path.join(dir, 'model.txt');
  if (!fs.existsSync(txt)) { console.log(cam, 'no model.txt, skipped'); continue; }
  const raw = Buffer.from(fs.readFileSync(txt, 'utf8'), 'base64');
  const soup = new Int16Array(raw.buffer, raw.byteOffset, raw.length / 2);
  const meta = JSON.parse(fs.readFileSync(path.join(dir, 'parts.json'), 'utf8'));
  const chunks = [];
  let size = 0;
  const push = (u8) => { const o = size; chunks.push(u8); size += u8.length; const pad = (4 - (size % 4)) % 4; if (pad) { chunks.push(new Uint8Array(pad)); size += pad; } return o; };
  let tv = 0, ti = 0;
  for (const p of meta.parts) {
    // weld identical positions
    const map = new Map(), verts = [], idx = new Uint32Array(p.k);
    for (let i = 0; i < p.k; i++) {
      const a = (p.o + i) * 3, x = soup[a], y = soup[a + 1], z = soup[a + 2];
      const key = x + ',' + y + ',' + z;
      let j = map.get(key);
      if (j === undefined) { j = verts.length / 3; map.set(key, j); verts.push(x, y, z); }
      idx[i] = j;
    }
    // reorder for vertex cache / fetch, then encode
    const [remap, unique] = MeshoptEncoder.reorderMesh(idx, true, false);
    const vb = new Int16Array(unique * 4);                      // x y z + pad: meshopt wants a stride that is a multiple of 4
    for (let v = 0; v < remap.length; v++) { const r = remap[v]; if (r === 0xffffffff) continue; vb.set(verts.slice(v * 3, v * 3 + 3), r * 4); }
    const big = unique > 65535, ib = big ? new Uint32Array(idx) : new Uint16Array(idx);
    const ve = MeshoptEncoder.encodeVertexBuffer(new Uint8Array(vb.buffer), unique, 8);
    const ie = MeshoptEncoder.encodeIndexBuffer(new Uint8Array(ib.buffer), ib.length, big ? 4 : 2);
    p.v = unique; p.i = ib.length; p.vo = push(ve); p.vl = ve.length; p.io = push(ie); p.il = ie.length;
    delete p.o; delete p.k;
    tv += unique; ti += ib.length;
  }
  const out = Buffer.concat(chunks);
  fs.writeFileSync(path.join(dir, 'model.bin'), out);
  fs.writeFileSync(path.join(dir, 'parts.json'), JSON.stringify(meta));
  fs.unlinkSync(txt);
  console.log(cam, meta.parts.length, 'parts', tv, 'verts', ti / 3, 'tris', (raw.length * 4 / 3 / 1e6).toFixed(2), 'MB txt ->', (out.length / 1e6).toFixed(2), 'MB bin');
}
