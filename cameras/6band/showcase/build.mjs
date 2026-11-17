#!/usr/bin/env node
// Bundles src/main.js with three.js and the fonts into one page.
//   dist/index.html      page body for publishing (title, style, app div, module script)
//   dist/standalone.html the same as a complete document that opens from a local web server
// model.bin and board.png are copied next to the page. Build pattern after elvarofficial/teardown (MIT).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import esbuild from 'esbuild';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(HERE, 'dist');
fs.mkdirSync(DIST, {recursive: true});
const b64 = (f) => fs.readFileSync(path.join(HERE, 'node_modules', f)).toString('base64');
const FONTS = [400, 600].map((w) => `@font-face{font-family:'JetBrains Mono';font-weight:${w};font-style:normal;font-display:block;src:url(data:font/woff2;base64,${b64(`@fontsource/jetbrains-mono/files/jetbrains-mono-latin-${w}-normal.woff2`)}) format('woff2');}`).join('\n') +
  [400, 500, 600, 700].map((w) => `\n@font-face{font-family:'Space Grotesk';font-weight:${w};font-style:normal;font-display:block;src:url(data:font/woff2;base64,${b64(`@fontsource/space-grotesk/files/space-grotesk-latin-${w}-normal.woff2`)}) format('woff2');}`).join('') +
  `\n@font-face{font-family:'Inter';font-weight:100 900;font-style:normal;font-display:block;src:url(data:font/woff2;base64,${b64('@fontsource-variable/inter/files/inter-latin-wght-normal.woff2')}) format('woff2');}`;

const res = await esbuild.build({
  entryPoints: [path.join(HERE, 'src/main.js')], bundle: true, format: 'esm', minify: !process.env.DEBUG, write: false, target: 'es2022',
  legalComments: 'none', loader: {'.json': 'json'}, logLevel: 'warning',
});
const js = res.outputFiles[0].text.replace(/<\/script/g, '<\\/script');
const body = `<title>Aviac 6B Showcase</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
${FONTS}
:root{color-scheme:dark}
</style>
<div id="app"></div>
<script type="module">
${js}
</script>
`;
fs.writeFileSync(path.join(DIST, 'index.html'), body);
fs.writeFileSync(path.join(DIST, 'standalone.html'), `<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n</head>\n<body>\n${body}</body>\n</html>\n`);
for (const f of ['model.txt', 'board.png']) fs.copyFileSync(path.join(HERE, 'assets', f), path.join(DIST, f));
console.log(`dist/index.html ${(body.length / 1024).toFixed(0)} KB`);
