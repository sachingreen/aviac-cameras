// Captures the loading screen right as the page starts, before the model arrives.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import {createRequire} from 'node:module';
const require = createRequire(import.meta.url); const {chromium} = require('playwright');
const DIST = path.resolve('dist');
const srv = http.createServer((q, r) => { const u = q.url.split('?')[0]; const f = path.join(DIST, u === '/' ? 'standalone.html' : u);
  if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  if (u.endsWith('model.txt')) return setTimeout(() => fs.createReadStream(f).pipe(r), 4000);   // hold the model back
  fs.createReadStream(f).pipe(r); }).listen(0);
const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
const p = await b.newPage({viewport: {width: 1600, height: 900}});
await p.goto(`http://127.0.0.1:${srv.address().port}/?lite`);
await p.waitForTimeout(2500);
await p.screenshot({path: process.argv[2]});
await b.close(); srv.close();
