// Aviac product viewer. <div class="viewer" data-src="models/ms/" data-finish="titanium"> gets a lens-forward 3D model
// with studio light. window.Aviac.viewers[el.id] exposes setFinish(name), explode(k), focus(group|null), so the product
// page can drive the teardown from the scroll position. Drag to turn, scroll the page (not the canvas) to move on.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

function knurlTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  g.fillStyle = '#808080'; g.fillRect(0, 0, 64, 64);
  g.strokeStyle = '#ffffff'; g.lineWidth = 3;
  for (let i = -64; i < 128; i += 8) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 64, 64); g.stroke(); g.beginPath(); g.moveTo(i, 64); g.lineTo(i + 64, 0); g.stroke(); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(30, 30);
  return t;
}
let KNURL;

function material(kind, c) {
  const col = new THREE.Color(c[0], c[1], c[2]);
  const S = (o) => new THREE.MeshStandardMaterial({color: col, roughness: 0.5, metalness: 0, ...o});
  const Ph = (o) => new THREE.MeshPhysicalMaterial({color: col, roughness: 0.5, metalness: 0, ...o});
  switch (kind) {
    case 'blast': return S({metalness: 1, roughness: 0.42});
    case 'die': return Ph({color: new THREE.Color('#2a2440'), metalness: 0.9, roughness: 0.12, iridescence: 1, iridescenceIOR: 1.8, iridescenceThicknessRange: [200, 900], clearcoat: 1});
    case 'die_dark': return Ph({color: new THREE.Color('#0b0d12'), metalness: 0.8, roughness: 0.18, iridescence: 0.6, iridescenceIOR: 1.6, clearcoat: 1});
    case 'window': return Ph({color: new THREE.Color('#d8e6ee'), roughness: 0.03, metalness: 0, clearcoat: 1, transparent: true, opacity: 0.12, depthWrite: false});
    case 'glass_black': return Ph({color: new THREE.Color('#050506'), roughness: 0.06, clearcoat: 1, clearcoatRoughness: 0.03});
    case 'gloss_white': return Ph({roughness: 0.22, clearcoat: 0.7, clearcoatRoughness: 0.08});
    case 'knurl': KNURL ??= knurlTexture(); return S({roughness: 0.62, bumpMap: KNURL, bumpScale: 1.2});
    case 'powder': return S({roughness: 0.72});
    case 'satin': return S({metalness: 0.85, roughness: 0.36});
    case 'anodised': return S({color: new THREE.Color('#0d0d0f'), metalness: 0.8, roughness: 0.42});
    case 'alu': return S({color: new THREE.Color('#b9bcc0'), metalness: 1, roughness: 0.36});
    case 'steel': return S({color: new THREE.Color('#c9cacc'), metalness: 1, roughness: 0.3});
    case 'steel_black': return S({color: new THREE.Color('#141416'), metalness: 1, roughness: 0.4});
    case 'gold': return S({color: new THREE.Color('#d9a544'), metalness: 1, roughness: 0.32});
    case 'lens': return Ph({color: new THREE.Color('#0a1414'), roughness: 0.02, metalness: 0.2, clearcoat: 1, clearcoatRoughness: 0.0, iridescence: 0.8, iridescenceIOR: 1.45, transparent: true, opacity: 0.45, depthWrite: false});
    case 'lens_inner': return Ph({color: new THREE.Color('#141a18'), roughness: 0.03, metalness: 0.3, clearcoat: 1, iridescence: 0.6, iridescenceIOR: 1.7, transparent: true, opacity: 0.55, depthWrite: false});
    case 'cover_glass': return Ph({color: new THREE.Color('#1a1f22'), roughness: 0.0, metalness: 0, clearcoat: 1, transparent: true, opacity: 0.35, depthWrite: false});
    case 'germanium': return Ph({color: new THREE.Color('#2f7a3c'), roughness: 0.04, metalness: 0.3, clearcoat: 1, clearcoatRoughness: 0, emissive: new THREE.Color('#1c5a28'), emissiveIntensity: 0.45, iridescence: 0.6, iridescenceIOR: 1.6});
    case 'dichroic': return Ph({color: new THREE.Color('#e8dfe2'), roughness: 0.0, metalness: 0.1, clearcoat: 1, transparent: true, opacity: 0.35, depthWrite: false, iridescence: 1, iridescenceIOR: 1.8, iridescenceThicknessRange: [250, 700]});
    case 'iris': return Ph({color: new THREE.Color('#121214'), roughness: 0.35, metalness: 0.7});
    case 'filterglass': return Ph({color: col.clone().multiplyScalar(0.5), roughness: 0.04, metalness: 0.6, clearcoat: 1, iridescence: 0.6});
    case 'led': return S({color: new THREE.Color('#ffd9a8'), emissive: new THREE.Color('#ff9a3c'), emissiveIntensity: 1.4});
    case 'dome': return S({color: new THREE.Color('#f2f1ec'), roughness: 0.4});
    case 'etch': return S({color: new THREE.Color('#b8bcc2'), metalness: 0.5, roughness: 0.55});
    case 'pcb': { const t = pcbTextures('#' + col.getHexString()); return Ph({color: new THREE.Color('#ffffff'), map: t.map, roughnessMap: t.rough, roughness: 1, clearcoat: 0.6, clearcoatRoughness: 0.25}); }
    case 'fpc': return S({color: new THREE.Color('#d06a12'), roughness: 0.4, side: THREE.DoubleSide});
    case 'ic': return Ph({color: new THREE.Color('#141416'), roughness: 0.6, clearcoat: 0.3, clearcoatRoughness: 0.5});
    case 'ceramic': return S({color: new THREE.Color('#8a7356'), roughness: 0.55});
    case 'ceramic_dark': return S({roughness: 0.35});
    case 'ferrite': return S({color: new THREE.Color('#232325'), roughness: 0.75});
    case 'rubber': case 'rubberised': return S({roughness: 0.8});
    case 'plastic_gloss': return S({roughness: 0.38});
    case 'black': return S({color: new THREE.Color('#020203'), roughness: 0.95});
    default: return S({});
  }
}


// Procedural board artwork: solder mask with copper traces under it, vias, gold pads and white silkscreen.
// One texture per board colour; the board's own x/y position is used as UV, so traces keep a real scale (~1 px = 0.05 mm).
const PCB = {};
function pcbTextures(hex) {
  if (PCB[hex]) return PCB[hex];
  const N = 1024, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d');
  const base = new THREE.Color(hex), hsl = {}; base.getHSL(hsl);
  const css = (l, a = 1) => `hsla(${hsl.h * 360},${hsl.s * 100}%,${Math.max(0, Math.min(100, l * 100))}%,${a})`;
  g.fillStyle = css(hsl.l); g.fillRect(0, 0, N, N);
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  // copper under the mask: slightly lighter, routed in 45-degree runs
  g.strokeStyle = css(hsl.l + 0.045, 0.85); g.lineCap = 'round';
  for (let i = 0; i < 90; i++) {
    let x = rnd() * N, y = rnd() * N; g.lineWidth = rnd() < 0.8 ? 3 : 7; g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 4; k++) { const d = Math.floor(rnd() * 8) * Math.PI / 4, L = 20 + rnd() * 120; x += Math.cos(d) * L; y += Math.sin(d) * L; g.lineTo(x, y); }
    g.stroke();
  }
  // ground pours
  g.fillStyle = css(hsl.l + 0.025, 0.5);
  for (let i = 0; i < 6; i++) g.fillRect(rnd() * N, rnd() * N, 60 + rnd() * 160, 40 + rnd() * 120);
  // vias
  for (let i = 0; i < 140; i++) { const x = rnd() * N, y = rnd() * N; g.fillStyle = '#c9a24a'; g.beginPath(); g.arc(x, y, 4.5, 0, 7); g.fill(); g.fillStyle = '#1a1a1a'; g.beginPath(); g.arc(x, y, 2, 0, 7); g.fill(); }
  // pad pairs (ENIG gold) and silkscreen outlines
  for (let i = 0; i < 45; i++) {
    const x = rnd() * N, y = rnd() * N, w = 12 + rnd() * 10, h = 9 + rnd() * 6, vert = rnd() < 0.5;
    g.fillStyle = '#d8b25a';
    if (vert) { g.fillRect(x, y, h, w); g.fillRect(x, y + w + 6, h, w); } else { g.fillRect(x, y, w, h); g.fillRect(x + w + 6, y, w, h); }
    if (rnd() < 0.4) { g.strokeStyle = 'rgba(240,240,232,.85)'; g.lineWidth = 1.5; g.strokeRect(x - 4, y - 4, (vert ? h : 2 * w + 6) + 8, (vert ? 2 * w + 6 : h) + 8); }
  }
  g.fillStyle = 'rgba(240,240,232,.8)'; g.font = '600 18px monospace';
  const refs = ['C12', 'R7', 'U3', 'L1', 'J4', 'C40', 'R22', 'U9', 'FB2', 'TP1', 'C8', 'D2'];
  for (let i = 0; i < 16; i++) g.fillText(refs[i % refs.length], rnd() * N, rnd() * N);
  const map = new THREE.CanvasTexture(c); map.colorSpace = THREE.SRGBColorSpace; map.wrapS = map.wrapT = THREE.RepeatWrapping; map.anisotropy = 8;
  // roughness: mask is glossy, pads satin
  const rc = document.createElement('canvas'); rc.width = rc.height = N; const rg = rc.getContext('2d');
  rg.drawImage(c, 0, 0); const id = rg.getImageData(0, 0, N, N);
  for (let i = 0; i < id.data.length; i += 4) { const gold = id.data[i] > 180 && id.data[i + 2] < 140; const v = gold ? 120 : 70; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; }
  rg.putImageData(id, 0, 0);
  const rough = new THREE.CanvasTexture(rc); rough.wrapS = rough.wrapT = THREE.RepeatWrapping;
  return (PCB[hex] = {map, rough});
}

function boardUV(geo) {
  const pos = geo.attributes.position, uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) { uv[2 * i] = pos.getX(i) * 9; uv[2 * i + 1] = pos.getY(i) * 9; }   // metres -> 1 tile per 110 mm
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

const ease = (x) => x * x * (3 - 2 * x);

async function mount(el) {
  const base = el.dataset.src;
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'high-performance'});
  let dpr = Math.min(2, devicePixelRatio || 1);
  renderer.setPixelRatio(dpr);
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.03).texture;
  scene.environmentIntensity = 0.85;
  const key = new THREE.DirectionalLight('#ffffff', 2.4); key.position.set(-0.6, 0.9, 1.0); scene.add(key);
  const rimL = new THREE.DirectionalLight('#ffffff', 1.6); rimL.position.set(-1.2, 0.3, -1.0); scene.add(rimL);
  const warm = new THREE.DirectionalLight('#ff9a52', 1.1); warm.position.set(1.2, -0.1, 0.4); scene.add(warm);
  const camera = new THREE.PerspectiveCamera(26, 1, 0.005, 10);
  const controls = new OrbitControls(camera, renderer.domElement);
  Object.assign(controls, {enableDamping: true, enablePan: false, enableZoom: el.dataset.zoom === '1', autoRotate: el.dataset.spin === '1', autoRotateSpeed: 0.8});

  const [data, bin] = await load(base, el.dataset.v || '');
  const src = new Uint8Array(bin);
  const root = new THREE.Group();
  scene.add(root);
  const parts = [];
  for (const p of data.parts) {
    // meshopt-compressed indexed mesh: Int16 x y z + pad, 0.01 mm units
    const vb = new Int16Array(p.v * 4), big = p.v > 65535, ib = big ? new Uint32Array(p.i) : new Uint16Array(p.i);
    MeshoptDecoder.decodeVertexBuffer(new Uint8Array(vb.buffer), p.v, 8, src.subarray(p.vo, p.vo + p.vl));
    MeshoptDecoder.decodeIndexBuffer(new Uint8Array(ib.buffer), p.i, big ? 4 : 2, src.subarray(p.io, p.io + p.il));
    const pos = new Float32Array(p.v * 3);
    for (let i = 0; i < p.v; i++) { pos[i * 3] = vb[i * 4] * 1e-5; pos[i * 3 + 1] = vb[i * 4 + 1] * 1e-5; pos[i * 3 + 2] = vb[i * 4 + 2] * 1e-5; }   // -> metres
    let geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setIndex(new THREE.BufferAttribute(ib, 1));
    geo = toCreasedNormals(geo, 0.6);                                   // un-indexes and creases, same look as before
    if (p.m === 'pcb') boardUV(geo);
    const mesh = new THREE.Mesh(geo);
    root.add(mesh);
    parts.push({p, mesh, e: new THREE.Vector3(p.e[0], p.e[1], p.e[2]).multiplyScalar(0.001), dim: 1});
  }
  const cache = {};
  const setFinish = (name) => {
    const F = data.finishes[name] || {};
    for (const r of parts) {
      const role = r.p.f && F[r.p.f];
      const kind = role ? role.mat : r.p.m, col = role ? role.color : r.p.c;
      const id = kind + col.join();
      r.mesh.material = (cache[id] ??= material(kind, col)).clone();
      r.base = r.mesh.material.opacity;
      r.mesh.material.transparent = true;
    }
    el.dataset.finish = name;
  };
  setFinish(el.dataset.finish || Object.keys(data.finishes)[0]);

  const box = new THREE.Box3().setFromObject(root);
  const ctr = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
  root.position.sub(ctr);
  const R = size.length() / 2;
  const home = new THREE.Vector3(0.62, 0.22, 1).normalize().multiplyScalar(R * (+el.dataset.dist || 3.4));
  camera.position.copy(home);
  controls.target.set(0, 0, 0);

  const fit = () => Math.max(1, Math.pow(1 / Math.max(0.2, camera.aspect), 0.9)) * (innerWidth < 760 ? 1.3 : Math.min(1.3, Math.max(1, 1.45 / camera.aspect)) * (+el.dataset.dz || 1));     // narrow screens: step back
  let k = 0, kT = 0, focus = null;
  const look = new THREE.Vector3(), lookT = new THREE.Vector3(), camT = home.clone();
  // drawing on demand: the loop runs while something moves (the teardown easing, a part fading, the camera gliding or
  // settling after a drag) and sleeps once everything is still, until the page or the visitor moves it again
  let onScreen = true, running = false, need = 2, live = false;
  const wake = () => { need = Math.max(need, 2); if (live && onScreen && !running) { running = true; requestAnimationFrame(loop); } };
  const api = {
    setFinish(name) { setFinish(name); wake(); },
    explode(v) { if (v !== kT) { kT = v; wake(); } },              // calls that change nothing do not wake the loop
    focus(g, at) {
      if (g === focus && !at) return;
      focus = g;
      if (g && !(innerWidth > 760 && el.dataset.hold)) {
        const b = new THREE.Box3();
        for (const r of parts) if (r.p.g === g) b.expandByObject(r.mesh);
        b.getCenter(lookT);
      } else lookT.set(0, 0, 0);
      if (at) camT.copy(at).multiplyScalar(R);
      wake();
    },
    view(az, el2, d) {
      const was = camT.clone();
      camT.set(Math.sin(az) * Math.cos(el2), Math.sin(el2), Math.cos(az) * Math.cos(el2)).multiplyScalar(R * d * fit());
      if (camT.distanceTo(was) > R * 1e-4) wake();
    },
    driven: false,
  };
  (window.Aviac ??= {viewers: {}}).viewers[el.id || base] = api;

  const resize = () => {
    const w = el.clientWidth, h = el.clientHeight;
    renderer.setSize(w, h); camera.aspect = w / Math.max(1, h);
    // wide screens: the model can sit off-centre (data-dx, data-dy) beside the vertical teardown's text
    if (innerWidth >= 760 && +el.dataset.dx) camera.setViewOffset(w, h, -w * el.dataset.dx, h * (+el.dataset.dy || 0), w, h); else camera.clearViewOffset();
    camera.updateProjectionMatrix(); wake();
  };
  new ResizeObserver(resize).observe(el);
  resize();
  camera.position.copy(home).multiplyScalar(fit()); camT.copy(camera.position);
  controls.addEventListener('start', wake); controls.addEventListener('change', wake);
  // every shader is compiled before the first frame (in parallel where the browser allows it), so the reveal never stutters
  try { await renderer.compileAsync(scene, camera); } catch (e) { /* no parallel compile here: the first frame compiles */ }
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const camWant = new THREE.Vector3(), eps = R * 2e-4;
  let fT = 0, fSum = 0, fN = 0, lastNow = 0;
  function loop(now) {
    if (!onScreen) { running = false; lastNow = 0; return; }     // off screen: stop drawing, resume when it comes back
    running = true;
    // easing by time, not by frame, so the teardown moves at the same pace on a 60 Hz, a 120 Hz or a struggling screen
    const dt = lastNow ? Math.min(0.1, (now - lastNow) / 1000) : 1 / 60; lastNow = now;
    const a = reduce ? 1 : 1 - Math.pow(0.92, dt * 60);
    let moving = Math.abs(kT - k) > 1e-4;
    k += (kT - k) * a;
    const ek = ease(Math.min(1, k));
    for (const r of parts) {
      r.mesh.position.copy(r.e).multiplyScalar(ek);
      const want = !focus || r.p.g === focus ? 1 : 0.12;
      if (Math.abs(want - r.dim) > 1e-3) moving = true;
      r.dim += (want - r.dim) * a;
      r.mesh.material.opacity = r.dim * (r.base ?? 1);
      r.mesh.material.depthWrite = r.dim > 0.5;
      r.mesh.visible = r.dim > 0.02;
    }
    if (api.driven) {
      camWant.copy(camT).add(look);
      if (look.distanceTo(lookT) > eps || camera.position.distanceTo(camWant) > eps) moving = true;
      look.lerp(lookT, a); controls.target.copy(look);
      camera.position.lerp(camWant, a);
    }
    const changed = controls.update();
    if (!(moving || changed || need > 0 || controls.autoRotate)) { running = false; fT = 0; lastNow = 0; return; }   // all still: sleep
    if (need > 0) need--;
    renderer.render(scene, camera);
    // a GPU that cannot hold about 40 fps at this size gets fewer pixels, a quarter step at a time (never below 1.25x)
    if (fT && now - fT < 120) { fSum += now - fT; fN++; }
    fT = now;
    if (fN >= 45) { const avg = fSum / fN; fSum = fN = 0; if (avg > 25 && dpr > 1.25) { dpr = Math.max(1.25, dpr - 0.25); renderer.setPixelRatio(dpr); resize(); } }
    requestAnimationFrame(loop);
  }
  new IntersectionObserver(([e]) => { onScreen = e.isIntersecting; if (onScreen) wake(); }, {rootMargin: '100px'}).observe(el);
  el.classList.add('ready'); live = true;
  wake();
}

// model downloads: shared between viewers of the same model, low priority, cancelled when the page is left
const ctl = new AbortController(), cache = {};
addEventListener('pagehide', () => ctl.abort());
function load(base, v) {
  const opt = {signal: ctl.signal, priority: 'low'};
  return (cache[base] ??= Promise.all([fetch(base + 'parts.json?v=' + v, opt).then((r) => r.json()), fetch(base + 'model.bin?v=' + v, opt).then((r) => r.arrayBuffer()), MeshoptDecoder.ready]));
}
const afterLoad = (fn) => (document.readyState === 'complete' ? fn() : addEventListener('load', fn, {once: true}));
const io = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting && !e.target.dataset.started) { e.target.dataset.started = '1'; mount(e.target).catch((err) => { if (err.name !== 'AbortError') { e.target.classList.add('failed'); console.error(err); } }); }
}), {rootMargin: '200% 0px'});                         // the teardown is built while the visitor reads the top of the page
afterLoad(() => document.querySelectorAll('.viewer[data-src]').forEach((v) => io.observe(v)));
