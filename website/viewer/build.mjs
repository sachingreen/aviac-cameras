// Bundles the product viewer into website/src/viewer.js (copied into public/ by website/build.py).
import esbuild from 'esbuild';
await esbuild.build({entryPoints: ['src/viewer.js'], bundle: true, minify: true, format: 'esm', target: 'es2022', outfile: '../src/viewer.js', legalComments: 'none'});
console.log('viewer built');
