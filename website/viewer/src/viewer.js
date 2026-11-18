// Aviac product viewer. <div class="viewer" data-src="models/ms/" data-finish="titanium"> gets a lens-forward 3D model
// with studio light. window.Aviac.viewers[el.id] exposes setFinish(name), explode(k), focus(group|null), so the product
// page can drive the teardown from the scroll position. Drag to turn, scroll the page (not the canvas) to move on.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';

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
    case 'lens': return Ph({color: new THREE.Color('#06100f'), roughness: 0.04, metalness: 0.5, clearcoat: 1, clearcoatRoughness: 0.0, iridescence: 0.5, iridescenceIOR: 1.6});
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
  renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
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

  const [data, txt] = await Promise.all([fetch(base + 'parts.json').then((r) => r.json()), fetch(base + 'model.txt').then((r) => r.text())]);
  const raw = atob(txt), u8 = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) u8[i] = raw.charCodeAt(i);
  const i16 = new Int16Array(u8.buffer);
  const root = new THREE.Group();
  scene.add(root);
  const parts = [];
  for (const p of data.parts) {
    const pos = new Float32Array(p.k * 3);
    for (let i = 0; i < p.k * 3; i++) pos[i] = i16[p.o * 3 + i] * 1e-5;              // 0.01 mm -> metres
    let geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo = toCreasedNormals(geo, 0.6);
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

  let k = 0, kT = 0, focus = null;
  const look = new THREE.Vector3(), lookT = new THREE.Vector3(), camT = home.clone();
  const api = {
    setFinish,
    explode(v) { kT = v; },
    focus(g, at) {
      focus = g;
      if (g) {
        const b = new THREE.Box3();
        for (const r of parts) if (r.p.g === g) b.expandByObject(r.mesh);
        b.getCenter(lookT);
      } else lookT.set(0, 0, 0);
      if (at) camT.copy(at).multiplyScalar(R);
    },
    view(az, el2, d) { camT.set(Math.sin(az) * Math.cos(el2), Math.sin(el2), Math.cos(az) * Math.cos(el2)).multiplyScalar(R * d); },
    driven: false,
  };
  (window.Aviac ??= {viewers: {}}).viewers[el.id || base] = api;

  const resize = () => {
    const w = el.clientWidth, h = el.clientHeight;
    renderer.setSize(w, h); camera.aspect = w / Math.max(1, h); camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe(el);
  resize();
  el.classList.add('ready');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const loop = () => {
    const a = reduce ? 1 : 0.08;
    k += (kT - k) * a;
    for (const r of parts) {
      r.mesh.position.copy(r.e).multiplyScalar(ease(Math.min(1, k)));
      const want = !focus || r.p.g === focus ? 1 : 0.12;
      r.dim += (want - r.dim) * a;
      r.mesh.material.opacity = r.dim * (r.base ?? 1);
      r.mesh.material.depthWrite = r.dim > 0.5;
      r.mesh.visible = r.dim > 0.02;
    }
    if (api.driven) {
      look.lerp(lookT, a); controls.target.copy(look);
      camera.position.lerp(camT.clone().add(look), a);
    }
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  };
  loop();
}

const io = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting && !e.target.dataset.started) { e.target.dataset.started = '1'; mount(e.target).catch((err) => { e.target.classList.add('failed'); console.error(err); }); }
}), {rootMargin: '300px'});
document.querySelectorAll('.viewer[data-src]').forEach((v) => io.observe(v));
