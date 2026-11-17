// Interactive product viewer for the website: the camera turned lens-first, studio-lit, slowly turning.
// Drag to rotate, scroll or pinch to zoom, the slider explodes it. <div class="viewer" data-src="ms/"> loads
// ms/parts.json, ms/model.txt and ms/board.png (the same assets as the showcase pages).
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';

const ACCENT = '#ff6b2c';
function material(kind, c) {
  const col = new THREE.Color(c[0], c[1], c[2]);
  const P = (o) => new THREE.MeshStandardMaterial({color: col, roughness: 0.5, metalness: 0, envMapIntensity: 0.6, ...o});
  switch (kind) {
    case 'shell': return P({color: new THREE.Color(c[0] * 0.8, c[1] * 0.8, c[2] * 0.85), roughness: 0.6, envMapIntensity: 0.5});
    case 'pcb': return P({roughness: 0.45, envMapIntensity: 0.5});
    case 'ic': return P({color: new THREE.Color('#141416'), roughness: 0.5});
    case 'ceramic': return P({roughness: 0.6});
    case 'ceramic_dark': return P({roughness: 0.4});
    case 'ferrite': return P({color: new THREE.Color('#232325'), roughness: 0.75});
    case 'gold': return P({color: new THREE.Color('#d9a544'), metalness: 1, roughness: 0.35});
    case 'accent': return P({color: new THREE.Color('#c8501c'), metalness: 0.9, roughness: 0.42, emissive: new THREE.Color(ACCENT), emissiveIntensity: 0});
    case 'steel': return P({color: new THREE.Color('#c9cacc'), metalness: 1, roughness: 0.4});
    case 'steel_black': return P({color: new THREE.Color('#1a1a1c'), metalness: 1, roughness: 0.45});
    case 'alu': return P({color: new THREE.Color('#b9bcc0'), metalness: 1, roughness: 0.42, envMapIntensity: 0.9});
    case 'hardcoat': return P({color: new THREE.Color('#44484e'), metalness: 0.85, roughness: 0.42, envMapIntensity: 0.9});
    case 'steel_brushed': return P({color: new THREE.Color('#b4b6b9'), metalness: 1, roughness: 0.32});
    case 'etch': return P({color: new THREE.Color('#a9adb3'), metalness: 0.5, roughness: 0.6});
    case 'paper': return P({color: new THREE.Color('#f4f4f1'), roughness: 0.9});
    case 'anodised': return P({color: new THREE.Color('#18181a'), metalness: 0.85, roughness: 0.5, envMapIntensity: 0.55});
    case 'rubberised': return P({color: new THREE.Color('#111113'), roughness: 0.8});
    case 'rubber': return P({roughness: 0.75});
    case 'plastic_gloss': return P({roughness: 0.45});
    case 'fpc': return P({color: new THREE.Color('#d06a12'), roughness: 0.45, side: THREE.DoubleSide});
    case 'lens': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.5 + 0.03, c[1] * 0.5 + 0.02, c[2] * 0.5 + 0.06), metalness: 0.85, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.1});
    case 'window': return P({color: new THREE.Color('#dfeaf0'), transparent: true, opacity: 0.16, roughness: 0.05, depthWrite: false});
    case 'bandpass': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.55 + 0.02, c[1] * 0.4 + 0.01, c[2] * 0.5 + 0.02), metalness: 0.8, roughness: 0.15, clearcoat: 1, clearcoatRoughness: 0.04});
    case 'cfrp': return P({color: new THREE.Color('#161618'), roughness: 0.38, metalness: 0.2});
    case 'emit': return P({emissive: col, emissiveIntensity: 1.0});
    case 'sensor': return P({color: new THREE.Color('#1f6f62'), metalness: 1, roughness: 0.25});
    case 'black': return P({color: new THREE.Color('#050506'), roughness: 0.9});
    default: return P({});
  }
}

const HIDE = /^(Drone|DLS \+ GNSS top unit)$/;

async function mount(el) {
  const base = el.dataset.src;
  const W = () => el.clientWidth, H = () => el.clientHeight;
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'high-performance'});
  renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1));
  renderer.setSize(W(), H());
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.75;
  const key = new THREE.DirectionalLight('#ffffff', 2.2);
  key.position.set(0.6, 1.2, 1.0);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, {left: -0.2, right: 0.2, top: 0.2, bottom: -0.2, near: 0.1, far: 4});
  key.shadow.radius = 6;
  scene.add(key);
  const rim = new THREE.DirectionalLight('#9fdcff', 1.2);
  rim.position.set(-1, 0.4, -0.8);
  scene.add(rim);
  const camera = new THREE.PerspectiveCamera(28, W() / H(), 0.01, 20);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.9;
  controls.enablePan = false;

  const [data, txt, tex] = await Promise.all([
    fetch(base + 'parts.json').then((r) => r.json()),
    fetch(base + 'model.txt').then((r) => r.text()),
    new THREE.TextureLoader().loadAsync(base + 'board.png'),
  ]);
  const raw = atob(txt), u8 = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) u8[i] = raw.charCodeAt(i);
  const f32 = new Float32Array(u8.buffer);
  // the model arrives in flight orientation (lenses down, y up); a quarter turn about x puts the lenses forward (+z)
  const turn = new THREE.Group();
  turn.rotation.x = -Math.PI / 2;
  scene.add(turn);
  const parts = [];
  for (const p of data.parts) {
    if (HIDE.test(p.g)) continue;
    let geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(f32.subarray(p.o * 3, (p.o + p.k) * 3), 3));
    geo = toCreasedNormals(geo, 0.62);
    const mesh = new THREE.Mesh(geo, material(p.m, p.c));
    mesh.castShadow = mesh.receiveShadow = !/window|lens|fpc/.test(p.m);
    turn.add(mesh);
    parts.push({mesh, e: p.e});
  }
  const b = data.board;
  tex.colorSpace = THREE.SRGBColorSpace;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(b.l, b.w), new THREE.MeshStandardMaterial({map: tex, roughness: 0.42, metalness: 0.05}));
  face.rotation.x = b.flip ? Math.PI / 2 : -Math.PI / 2;
  face.position.set(b.x0 + b.l / 2, b.y + (b.flip ? -0.00006 : 0.00006), b.z0 + b.w / 2);
  turn.add(face);
  const carrier = data.parts.find((p) => p.n === 'carrier_pcb');
  // centre it
  const box = new THREE.Box3().setFromObject(turn);
  const ctr = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
  turn.position.sub(ctr);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShadowMaterial({opacity: 0.35}));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -size.y / 2 - 0.001;
  shadow.receiveShadow = true;
  scene.add(shadow);
  const R = size.length() / 2;
  const home = new THREE.Vector3(0.55, 0.28, 1).normalize().multiplyScalar(R * 4.3);
  camera.position.copy(home);
  controls.minDistance = R * 1.6;
  controls.maxDistance = R * 6;
  controls.target.set(0, 0, 0);
  controls.update();

  // explode slider and reset button, if the page has them
  const slider = el.parentElement.querySelector('input[type=range]');
  let k = 0;
  if (slider) slider.addEventListener('input', () => { k = +slider.value; controls.autoRotate = false; });
  const reset = el.parentElement.querySelector('[data-reset]');
  if (reset) reset.addEventListener('click', () => { camera.position.copy(home); k = 0; if (slider) slider.value = 0; controls.autoRotate = true; });
  renderer.domElement.addEventListener('pointerdown', () => (controls.autoRotate = false));
  let ek = 0;
  const loop = () => {
    ek += (k - ek) * 0.12;
    for (const p of parts) p.mesh.position.set(p.e[0] * ek, p.e[1] * ek, p.e[2] * ek);
    face.position.y = b.y + (b.flip ? -0.00006 : 0.00006) + (carrier ? carrier.e[1] * ek : 0);
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  };
  new ResizeObserver(() => { renderer.setSize(W(), H()); camera.aspect = W() / H(); camera.updateProjectionMatrix(); }).observe(el);
  el.classList.add('ready');
  loop();
}

// start each viewer when it scrolls into view
const io = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting && !e.target.dataset.started) { e.target.dataset.started = '1'; mount(e.target).catch((err) => { e.target.classList.add('failed'); console.error(err); }); }
}), {rootMargin: '200px'});
document.querySelectorAll('.viewer[data-src]').forEach((v) => io.observe(v));
