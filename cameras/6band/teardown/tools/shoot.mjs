// Serves dist/ on a local port and captures stills of the live page at given times / after given actions.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const {chromium} = require('playwright');
const DIST = path.resolve('dist');
const out = process.argv[2] || 'shots';
fs.mkdirSync(out, {recursive: true});
const types = {'.html': 'text/html', '.txt': 'text/plain', '.png': 'image/png'};
const srv = http.createServer((q, r) => {
  const u = q.url.split('?')[0]; const f = path.join(DIST, u === '/' ? 'standalone.html' : u);
  if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, {'content-type': types[path.extname(f)] || 'text/plain'});
  fs.createReadStream(f).pipe(r);
}).listen(0);
const port = srv.address().port;
const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
const p = await b.newPage({viewport: {width: 1600, height: 900}});
const errs = [];
p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
p.on('pageerror', (e) => errs.push(String(e)));
await p.goto(`http://127.0.0.1:${port}/?lite`);
await p.waitForSelector('.tourchip', {timeout: 120000}).catch(() => errs.push('never loaded'));
const steps = (process.argv[3] || 'tour0:3').split(',');
for (const s of steps) {
  const [name, wait, click] = s.split(':');
  if (click) for (const c of click.split('+')) { await p.evaluate((t) => { const n = [...document.querySelectorAll('.tb')].find((e) => e.textContent.trim() === t); n && n.click(); }, c); await p.waitForTimeout(300); }
  await p.waitForTimeout(Number(wait) * 1000);
  await p.screenshot({path: path.join(out, name + '.png'), timeout: 180000});
  console.log('shot', name);
}
console.log('errors:', errs.slice(0, 6));
await b.close(); srv.close();
