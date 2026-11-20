import esbuild from 'esbuild';
import fs from 'node:fs';
fs.rmSync('../src/chunks', {recursive: true, force: true});
await esbuild.build({entryPoints: ['src/viewer.js', 'src/flight.js', 'src/story.js'], bundle: true, minify: true, format: 'esm', target: 'es2022', outdir: '../src',
  splitting: true, chunkNames: 'chunks/[name]-[hash]', legalComments: 'none'});
