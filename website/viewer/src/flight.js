// Aviac flight demos: one light-weight three.js scene per market, mounted on <div class="fly" data-scene="...">.
// Everything is procedural: the aircraft are built from primitives here (no model files), the ground is the
// page's own demo image, and the analysed layer (NDVI, coverage, thermal, SWIR, this week's map) is painted in
// behind the camera footprint as the drone flies its lawnmower survey. The HUD numbers come from the same
// geometry the scene uses: GSD = height x pixel / focal length, swath = GSD x pixels across.
import * as THREE from 'three';

const R = (document.querySelector('script[data-root]')?.dataset.root) ?? '';
const IMG = (n) => `${R}assets/img/demo/${n}.jpg`;

const CAMS = {
  MS: {name: 'MS · IMX565 colour', px: 2.74e-6, f: 0.016, n: 4128},
  Duos: {name: 'Duos · Mira220 stereo', px: 2.79e-6, f: 0.004, n: 1600},
  TH: {name: 'TH · 640 × 512 thermal', px: 12e-6, f: 0.013, n: 640},
  SW: {name: 'SW · InGaAs SWIR', px: 5e-6, f: 0.025, n: 640},
};

const SCENES = {
  crop: {ground: 'field_rgb', layer: 'field_ndvi', layerName: 'NDVI', W: 1300, alt: 100, alts: [60, 120], speed: 18, side: 0.7, cam: 'MS', drone: 'vtol',
    bands: [['Blue', '#3b6fd8'], ['Green', '#2e9e4f'], ['Red', '#d8433b'], ['Red edge', '#b0305a'], ['NIR', '#7a2f6b'], ['Ext NIR', '#4b2a55']],
    finds: [[81.3, 33.0, 'Stress · 0.21 ac'], [33.7, 85.9, 'Stress · 0.08 ac']], findWord: 'Stress zones', title: 'Crop survey · MS on the Aviac VTOL'},
  spraying: {ground: 'field_rgb', layer: 'spray_coverage', layerName: 'Coverage', W: 260, alt: 3, alts: [2, 5], speed: 5, side: 0, swath: 6.5, cam: 'Duos', drone: 'hex', aft: true,
    bands: [['Left', '#2f6f4e'], ['Right', '#2f6f4e']], finds: [[80.4, 34.6, 'Missed strip'], [9.8, 74.5, 'Overlap']], findWord: 'Spray faults', title: 'Spray pass · Duos at the rear of the sprayer'},
  solar: {ground: 'solar_rgb', layer: 'solar_thermal', layerName: 'Thermal', W: 240, alt: 30, alts: [20, 45], speed: 6, side: 0.3, cam: 'TH', drone: 'quad', tint: 0xe9e9e6,
    bands: [['Colour', '#2f6f4e'], ['LWIR 8–14 µm', '#c2410c']],
    finds: [[29.7, 25.2, 'Hot cell'], [61.6, 52.7, 'Substring warm'], [81.2, 34.2, 'Module warm'], [47.8, 79.3, 'Half table warm'], [56.2, 14.2, 'Soiling']],
    findWord: 'Hotspot candidates', title: 'Array inspection · TH thermal'},
  industrial: {ground: 'swir_visible', layer: 'swir_swir', layerName: 'SWIR', W: 160, alt: 50, alts: [30, 80], speed: 5, side: 0.3, cam: 'SW', drone: 'quad', tint: 0x2b2d31,
    bands: [['SWIR 0.9–1.7 µm', '#3a6ea5']], finds: [[70.0, 43.3, 'Ponding'], [26.2, 38.3, 'Wet insulation'], [53.8, 89.0, 'Pipe leak']],
    findWord: 'Moisture findings', title: 'Roof inspection · SW short-wave infrared'},
  construction: {ground: 'site_w3', layer: 'site_w11', layerName: 'Week 11', W: 220, alt: 60, alts: [40, 90], speed: 10, side: 0.7, cam: 'MS', drone: 'vtol',
    bands: [['Colour map', '#2f6f4e'], ['Stereo surface', '#6b7c72']], finds: [[44.0, 36.0, 'Slab poured'], [68.0, 28.0, 'Rebar placed'], [77.0, 44.3, 'Crane installed'], [78.0, 22.0, 'Stockpile −60 %']],
    findWord: 'Changes since week 3', title: 'Weekly map · MS colour camera'},
};

// ---------------------------------------------------------------- materials and aircraft (metres)
const mat = (color, o = {}) => new THREE.MeshStandardMaterial({color, roughness: 0.45, metalness: 0.05, ...o});
const M = {
  grey: mat(0x48515a, {roughness: 0.28, metalness: 0.15}), wing: mat(0x5e646a, {roughness: 0.32}), white: mat(0xe8e8e4, {roughness: 0.5}),
  carbon: mat(0x1a1b1d, {roughness: 0.38, metalness: 0.3}), black: mat(0x0b0b0c, {roughness: 0.5}), steel: mat(0xb8bcc0, {roughness: 0.25, metalness: 0.9}),
  ti: mat(0xa7a9ab, {roughness: 0.3, metalness: 0.8}), glass: mat(0x0d1a1a, {roughness: 0.05, metalness: 0.2}), amber: new THREE.MeshBasicMaterial({color: 0xffa040}),
  blur: new THREE.MeshBasicMaterial({color: 0x222222, transparent: true, opacity: 0.18, side: THREE.DoubleSide, depthWrite: false}),
};
const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r, l, m, seg = 20) => new THREE.Mesh(new THREE.CylinderGeometry(r, r, l, seg), m);

function cameraHead(kind, finish) {
  // a small family head, lenses toward -z of the group (the group is then pointed where the camera looks)
  const g = new THREE.Group();
  const size = {MS: [0.096, 0.09, 0.08], Duos: [0.05, 0.03, 0.028], TH: [0.06, 0.042, 0.036], SW: [0.058, 0.046, 0.044]}[kind];
  const body = box(size[0], size[1], size[2], finish === 'white' ? M.white : finish === 'dark' ? M.carbon : M.ti); g.add(body);
  const hood = box(size[0] * 1.04, size[1] * 1.04, 0.008, M.black); hood.position.z = -size[2] / 2; g.add(hood);
  const lens = (x, y, r) => { const l = cyl(r, 0.012, M.glass); l.rotation.x = Math.PI / 2; l.position.set(x, y, -size[2] / 2 - 0.004); g.add(l);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, r * 0.18, 8, 24), M.black); ring.position.set(x, y, -size[2] / 2 - 0.01); g.add(ring); };
  if (kind === 'MS') { lens(0.012, -0.004, 0.02); [0.028, 0, -0.028].forEach((y) => lens(-0.032, y, 0.008)); }
  if (kind === 'Duos') { lens(-0.013, 0, 0.007); lens(0.013, 0, 0.007); }
  if (kind === 'TH') { lens(-0.009, 0, 0.012); lens(0.018, 0, 0.007); }
  if (kind === 'SW') lens(0, 0, 0.016);
  const led = box(size[0] * 0.2, 0.002, 0.002, M.amber); led.position.set(0, size[1] * 0.4, -size[2] / 2 - 0.006); g.add(led);
  g.userData.led = led;
  return g;
}

function rotorDisc(r) {
  const d = new THREE.Mesh(new THREE.CircleGeometry(r, 32), M.blur); d.rotation.x = -Math.PI / 2; return d;
}

function buildVTOL(kind) {
  // the user's grey VTOL: gloss slate pod, nose tractor prop, straight wing, carbon booms with four lift motors, white legs
  const g = new THREE.Group();
  const prof = [];
  for (let i = 0; i <= 24; i++) { const t = i / 24; prof.push(new THREE.Vector2(Math.max(0.004, 0.095 * Math.pow(Math.sin(Math.PI * Math.pow(t, 0.8)), 0.7)), (t - 0.5) * 1.1)); }
  const fus = new THREE.Mesh(new THREE.LatheGeometry(prof, 28), M.grey); fus.rotation.x = Math.PI / 2; fus.scale.set(1, 1, 0.88); g.add(fus);
  const hatch = box(0.08, 0.004, 0.14, M.black); hatch.position.set(0, 0.085, -0.25); g.add(hatch);
  const wing = box(2.1, 0.026, 0.22, M.wing); wing.position.set(0, 0.09, 0.0); g.add(wing);
  for (const s of [-1, 1]) for (let k = 0; k < 4; k++) { const st = box(0.008, 0.002, 0.06, M.white); st.position.set(s * (0.15 + k * 0.022), 0.104, 0.0); g.add(st); }
  const spin = [];
  for (const s of [-1, 1]) {
    const x = s * 0.33;
    const boom = cyl(0.011, 0.98, M.carbon, 12); boom.rotation.x = Math.PI / 2; boom.position.set(x, 0.07, -0.07); g.add(boom);
    for (const z of [-0.56, 0.42]) {
      const mt = cyl(0.02, 0.03, M.black); mt.position.set(x, 0.1, z); g.add(mt);
      const mm = box(0.018, 0.03, 0.06, M.white); mm.position.set(x, 0.078, z); g.add(mm);
      const p = box(0.36, 0.004, 0.026, M.carbon); p.position.set(x, 0.12, z); p.rotation.y = s * 0.6 + z; g.add(p);   // lift props parked in cruise
    }
    const pod = cyl(0.02, 0.15, M.black, 12); pod.rotation.x = Math.PI / 2; pod.position.set(x, 0.06, 0.48); g.add(pod);
    const leg = box(0.018, 0.32, 0.06, M.white); leg.position.set(x + s * 0.035, -0.1, -0.29); leg.rotation.z = s * 0.22; g.add(leg);
    const foot = box(0.05, 0.006, 0.08, M.white); foot.position.set(x + s * 0.07, -0.26, -0.26); g.add(foot);
  }
  const spinner = new THREE.Mesh(new THREE.ConeGeometry(0.026, 0.05, 20), M.steel); spinner.rotation.x = -Math.PI / 2; spinner.position.set(0, 0, -0.575); g.add(spinner);
  const prop = rotorDisc(0.16); prop.rotation.set(0, 0, 0); prop.position.set(0, 0, -0.565); g.add(prop); spin.push(prop);
  const cam = cameraHead(kind, 'ti');
  cam.rotation.x = -Math.PI / 2;                    // lenses straight down (nadir), back face up against the belly
  cam.position.set(0, -0.085 - 0.045, -0.15); g.add(cam);
  const hanger = box(0.1, 0.012, 0.09, M.black); hanger.position.set(0, -0.084, -0.15); g.add(hanger);
  g.userData = {spin, spinAxis: 'z', cam, camLook: new THREE.Vector3(0, -1, 0), span: 2.1};
  return g;
}

function buildHex() {
  // a six-rotor spray drone: white shell, carbon arms, tank, boom with nozzles; Duos on a yoke at the rear, facing aft-down
  const g = new THREE.Group();
  const shell = new THREE.Mesh(new THREE.SphereGeometry(0.32, 28, 16), M.white); shell.scale.set(1, 0.42, 1.25); shell.position.y = 0.12; g.add(shell);
  const tank = cyl(0.2, 0.32, M.white); tank.position.y = -0.12; g.add(tank);
  const plate = box(0.5, 0.02, 0.6, M.carbon); plate.position.y = 0.04; g.add(plate);
  const spin = [];
  for (let k = 0; k < 6; k++) {
    const a = (k / 6) * Math.PI * 2 + Math.PI / 6;
    const arm = cyl(0.022, 0.95, M.carbon, 10); arm.rotation.z = Math.PI / 2; arm.rotation.y = -a; arm.position.set(Math.cos(a) * 0.5, 0.05, Math.sin(a) * 0.5); g.add(arm);
    const mt = cyl(0.04, 0.06, M.black); mt.position.set(Math.cos(a) * 0.98, 0.09, Math.sin(a) * 0.98); g.add(mt);
    const d = rotorDisc(0.42); d.position.set(Math.cos(a) * 0.98, 0.13, Math.sin(a) * 0.98); g.add(d); spin.push(d);
  }
  for (const s of [-1, 1]) { const sk = cyl(0.015, 0.9, M.carbon, 8); sk.rotation.x = Math.PI / 2; sk.position.set(s * 0.32, -0.45, 0); g.add(sk);
    const lg = box(0.02, 0.45, 0.02, M.carbon); lg.position.set(s * 0.3, -0.24, 0); g.add(lg); }
  const boom = cyl(0.012, 1.9, M.carbon, 8); boom.rotation.z = Math.PI / 2; boom.position.set(0, -0.32, -0.05); g.add(boom);
  const nozzles = [];
  for (let i = 0; i < 6; i++) { const n = cyl(0.014, 0.04, M.black, 8); n.position.set(-0.85 + i * 0.34, -0.35, -0.05); g.add(n); nozzles.push(n.position.clone()); }
  const yoke = box(0.012, 0.06, 0.03, M.black); yoke.position.set(-0.03, -0.02, 0.62); g.add(yoke);
  const cam = cameraHead('Duos', 'white'); cam.position.set(0, -0.04, 0.64);
  cam.rotation.set(-0.85, Math.PI, 0);              // facing aft and down at the spray that just landed
  g.add(cam);
  g.userData = {spin, spinAxis: 'y', cam, camLook: new THREE.Vector3(0, -Math.sin(0.85), Math.cos(0.85)), nozzles, span: 2.8};
  return g;
}

function buildQuad(kind, tint) {
  const g = new THREE.Group();
  const bodyM = tint === 0x2b2d31 ? M.grey : M.white;
  const body = box(0.26, 0.09, 0.36, bodyM); g.add(body);
  const top = box(0.2, 0.03, 0.26, M.carbon); top.position.y = 0.06; g.add(top);
  const spin = [];
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    const arm = box(0.04, 0.03, 0.42, M.carbon); arm.position.set(sx * 0.22, 0.02, sz * 0.2); arm.rotation.y = sx * sz * 0.8; g.add(arm);
    const mt = cyl(0.03, 0.05, M.black); mt.position.set(sx * 0.36, 0.05, sz * 0.36); g.add(mt);
    const d = rotorDisc(0.22); d.position.set(sx * 0.36, 0.09, sz * 0.36); g.add(d); spin.push(d);
    const lg = box(0.015, 0.2, 0.015, M.carbon); lg.position.set(sx * 0.1, -0.13, sz * 0.12); g.add(lg);
  }
  const cam = cameraHead(kind, tint === 0x2b2d31 ? 'dark' : 'white');
  cam.rotation.x = -Math.PI / 2 + 0.0; cam.position.set(0, -0.09, -0.12); g.add(cam);
  const mount = box(0.03, 0.03, 0.03, M.black); mount.position.set(0, -0.055, -0.12); g.add(mount);
  g.userData = {spin, spinAxis: 'y', cam, camLook: new THREE.Vector3(0, -1, 0), span: 0.95};
  return g;
}

// ---------------------------------------------------------------- the demo
function mount(el) {
  const S = SCENES[el.dataset.scene]; if (!S) return;
  const C = CAMS[S.cam];
  const W = S.W, H = S.W * 0.75;
  el.innerHTML = `
  <canvas class="fly-c" aria-label="${S.title}: an animated drone survey"></canvas>
  <div class="fly-hud">
    <div class="fp fp-l"><div class="fh">Mission <b class="live">● live</b></div><div class="fbig"><b data-k="area">0</b><span data-k="areaU"></span></div>
      <div class="fbar"><i data-k="bar"></i></div><dl><dt>Pass</dt><dd data-k="pass"></dd><dt>Flight time</dt><dd data-k="time"></dd><dt>Frames</dt><dd data-k="frames"></dd><dt>Sim speed</dt><dd data-k="timex"></dd></dl>
      <canvas class="fmini" width="240" height="180"></canvas><div class="flab">${S.layerName} map, building as it flies</div></div>
    <div class="fp fp-r"><div class="fh">${C.name}</div><div class="fbig"><b data-k="gsd"></b><span data-k="gsdU"></span></div>
      <div class="fform" data-k="form"></div><dl><dt>Swath</dt><dd data-k="swath"></dd><dt>Height</dt><dd data-k="alt"></dd><dt>Ground speed</dt><dd data-k="spd"></dd><dt data-k="xk"></dt><dd data-k="xv"></dd></dl>
      <div class="fh" style="margin-top:12px">${S.findWord} <b data-k="nf">0</b></div><ul class="ffind" data-k="finds"></ul></div>
    <div class="fbands">${S.bands.map(([n, c]) => `<span><i style="background:${c}"></i>${n}</span>`).join('')}</div>
    <div class="fctl">
      <button data-a="play" aria-label="Pause">❚❚</button>
      <div class="fseg"><button data-v="drone" class="on">Drone</button><button data-v="survey">Survey</button><button data-v="map">Map</button></div>
      <label>Height <input type="range" min="${S.alts[0]}" max="${S.alts[1]}" step="${S.alts[1] > 20 ? 5 : 0.5}" value="${S.alt}"></label>
    </div>
  </div>`;
  const cv = el.querySelector('.fly-c');
  const $ = (k) => el.querySelector(`[data-k="${k}"]`);
  const renderer = new THREE.WebGLRenderer({canvas: cv, antialias: true, powerPreference: 'low-power'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  const sky = new THREE.Color(0xe9efeb); scene.background = sky; scene.fog = new THREE.Fog(sky, W * 0.9, W * 2.6);
  const cam = new THREE.PerspectiveCamera(40, 1, 0.05, W * 6);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a9a8c, 1.6));
  const sun = new THREE.DirectionalLight(0xfff4e2, 2.4); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
  scene.add(sun, sun.target);

  // ground: demo image at true size, a wide neutral surround, and the analysed layer painted in behind the footprint
  const loader = new THREE.TextureLoader();
  const gTex = loader.load(IMG(S.ground)); gTex.colorSpace = THREE.SRGBColorSpace; gTex.anisotropy = 8;
  const lTex = loader.load(IMG(S.layer)); lTex.colorSpace = THREE.SRGBColorSpace; lTex.anisotropy = 8;
  const surround = new THREE.Mesh(new THREE.PlaneGeometry(W * 8, W * 8), new THREE.MeshStandardMaterial({color: S.ground.startsWith('field') ? 0x6f7d4c : 0x8d8f8a, roughness: 1}));
  surround.rotation.x = -Math.PI / 2; surround.position.y = -Math.max(0.3, W / 800); surround.receiveShadow = true; scene.add(surround);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(W, H), new THREE.MeshStandardMaterial({map: gTex, roughness: 0.95}));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const mask = document.createElement('canvas'); mask.width = 512; mask.height = 384;
  const mctx = mask.getContext('2d');
  const mTex = new THREE.CanvasTexture(mask);
  const layer = new THREE.Mesh(new THREE.PlaneGeometry(W, H), new THREE.MeshBasicMaterial({map: lTex, alphaMap: mTex, transparent: true, depthWrite: false}));
  layer.rotation.x = -Math.PI / 2; layer.position.y = Math.max(0.02, W / 4000); scene.add(layer);

  // aircraft
  const drone = S.drone === 'vtol' ? buildVTOL(S.cam) : S.drone === 'hex' ? buildHex() : buildQuad(S.cam, S.tint);
  drone.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  scene.add(drone);
  const ud = drone.userData;

  // footprint: frustum lines and a ground rectangle
  const fpGeo = new THREE.BufferGeometry(); fpGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(16 * 3), 3));
  const fp = new THREE.LineSegments(fpGeo, new THREE.LineBasicMaterial({color: 0x1f6b47, transparent: true, opacity: 0.85})); scene.add(fp);
  const fpFill = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({color: 0x2f9e6a, transparent: true, opacity: 0.16, depthWrite: false}));
  fpFill.rotation.x = -Math.PI / 2; fpFill.position.y = 0.05; scene.add(fpFill);

  // spray mist (spraying only)
  let mist = null;
  if (S.drone === 'hex') {
    const N = 900, pos = new Float32Array(N * 3), life = new Float32Array(N);
    for (let i = 0; i < N; i++) life[i] = Math.random();
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    mist = new THREE.Points(geo, new THREE.PointsMaterial({color: 0xbfe3f5, size: 0.05, transparent: true, opacity: 0.6, depthWrite: false}));
    mist.userData.life = life; scene.add(mist);
  }

  // finds: world positions, markers appear when the footprint covers them
  const finds = S.finds.map(([px, py, label]) => {
    const p = new THREE.Vector3((px / 100 - 0.5) * W, 0, (py / 100 - 0.5) * H);
    const m = new THREE.Group();
    const s = Math.max(1.2, W / 90);
    const ring = new THREE.Mesh(new THREE.RingGeometry(s * 0.7, s, 32), new THREE.MeshBasicMaterial({color: 0xd7301f, transparent: true, opacity: 0.9, depthWrite: false}));
    ring.rotation.x = -Math.PI / 2; ring.position.y = 0.1; m.add(ring);
    const stem = cyl(s * 0.06, s * 3, new THREE.MeshBasicMaterial({color: 0xd7301f})); stem.position.y = s * 1.5; m.add(stem);
    const head = new THREE.Mesh(new THREE.SphereGeometry(s * 0.35, 16, 12), new THREE.MeshBasicMaterial({color: 0xd7301f})); head.position.y = s * 3; m.add(head);
    m.position.copy(p); m.visible = false; scene.add(m);
    return {p, label, m, found: false};
  });

  // ---- survey plan (re-planned when the height changes)
  let alt = S.alt, plan = null;
  const optics = () => {
    const gsd = alt * C.px / C.f, swathCam = gsd * C.n;
    const swath = S.swath || swathCam;                          // the sprayer's lanes are its spray swath
    const spacing = swath * (1 - S.side);
    const passes = Math.max(2, Math.ceil(H / spacing));
    return {gsd, swathCam, swath, spacing, passes};
  };
  const replan = () => {
    const o = optics();
    const pts = [];
    const sp = H / o.passes;
    for (let i = 0; i < o.passes; i++) {
      const z = -H / 2 + sp * (i + 0.5), a = i % 2 ? W / 2 + 10 : -W / 2 - 10, b = i % 2 ? -W / 2 - 10 : W / 2 + 10;
      pts.push(new THREE.Vector3(a, 0, z), new THREE.Vector3(b, 0, z));
    }
    let len = 0; const cum = [0];
    for (let i = 1; i < pts.length; i++) { len += pts[i].distanceTo(pts[i - 1]); cum.push(len); }
    const realTime = len / S.speed;
    plan = {o, pts, cum, len, timex: Math.max(1, realTime / 75), sp};
    mctx.clearRect(0, 0, 512, 384); mTex.needsUpdate = true;
    finds.forEach((f) => { f.found = false; f.m.visible = false; });
    $('finds').innerHTML = ''; $('nf').textContent = '0';
    dist = 0; frames = 0;
  };
  let dist = 0, frames = 0, playing = true, view = 'drone', auto = true, lastSwitch = 0;
  replan();

  const at = (d) => {
    const {pts, cum} = plan; d = Math.min(d, plan.len - 1e-3);
    let i = 1; while (cum[i] < d) i++;
    const t = (d - cum[i - 1]) / (cum[i] - cum[i - 1]);
    return {p: pts[i - 1].clone().lerp(pts[i], t), dir: pts[i].clone().sub(pts[i - 1]).normalize(), seg: i};
  };

  // HUD helpers
  const mini = el.querySelector('.fmini'), mx = mini.getContext('2d');
  const off = document.createElement('canvas'); off.width = 240; off.height = 180; const ox = off.getContext('2d');
  const gImg = new Image(); gImg.src = IMG(S.ground); const lImg = new Image(); lImg.src = IMG(S.layer);
  const fmt = (v, d = 0) => v.toLocaleString('en-US', {maximumFractionDigits: d, minimumFractionDigits: d});
  const unitLen = (m) => (m < 0.01 ? `${fmt(m * 1000, 1)} mm` : m < 1 ? `${fmt(m * 100, m < 0.1 ? 2 : 1)} cm` : `${fmt(m, 1)} m`);

  // controls
  el.querySelector('[data-a="play"]').addEventListener('click', (e) => { playing = !playing; e.currentTarget.textContent = playing ? '❚❚' : '▶'; e.currentTarget.setAttribute('aria-label', playing ? 'Pause' : 'Play'); });
  el.querySelectorAll('[data-v]').forEach((b) => b.addEventListener('click', () => { view = b.dataset.v; auto = false; el.querySelectorAll('[data-v]').forEach((x) => x.classList.toggle('on', x === b)); }));
  el.querySelector('input[type=range]').addEventListener('change', (e) => { alt = +e.target.value; replan(); });
  let drag = null, yaw = 0, pitch = 0;
  cv.addEventListener('pointerdown', (e) => { drag = [e.clientX, e.clientY, yaw, pitch]; auto = false; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener('pointermove', (e) => { if (!drag) return; yaw = drag[2] - (e.clientX - drag[0]) * 0.006; pitch = Math.max(-0.5, Math.min(0.6, drag[3] + (e.clientY - drag[1]) * 0.004)); });
  cv.addEventListener('pointerup', () => (drag = null));

  // ---- loop (paused when off screen)
  let visible = false, last = performance.now(), simT = 0, hudT = 1;
  new IntersectionObserver((es) => { visible = es[es.length - 1].isIntersecting; last = performance.now(); }, {threshold: 0}).observe(el);
  const camPos = new THREE.Vector3(), camTgt = new THREE.Vector3(), offP = new THREE.Vector3(), offT = new THREE.Vector3(); let lastView = '';
  const resize = () => { const w = el.clientWidth, h = el.clientHeight; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); };
  new ResizeObserver(resize).observe(el); resize();
  const tmp = new THREE.Vector3(), q = new THREE.Quaternion();

  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible) return;
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    const o = plan.o;
    const tx = view === 'drone' ? Math.min(plan.timex, 3) : view === 'survey' ? Math.max(1, plan.timex / 3) : plan.timex;
    if (playing) { simT += dt * tx / plan.timex; dist += S.speed * tx * dt; if (dist >= plan.len) { replan(); } }
    const {p, dir} = at(dist);
    const flyAlt = alt + (S.drone === 'hex' ? 0.6 : 0);
    drone.position.set(p.x, flyAlt, p.z);
    const heading = Math.atan2(-dir.x, -dir.z);
    drone.rotation.set(S.drone === 'vtol' ? 0 : -0.08, heading, Math.sin(simT * 0.7) * 0.02);
    ud.spin.forEach((s, i) => { s.rotation[ud.spinAxis === 'z' ? 'z' : 'z'] += dt * 40 * (i % 2 ? 1 : -1); });
    ud.cam.userData.led.material.color.setHex(Math.floor(simT * 2) % 2 ? 0xffa040 : 0x7a4a20);

    // footprint centre on the ground (aft for Duos), oriented with the flight
    const look = ud.camLook.clone().applyQuaternion(drone.quaternion);
    const camWorld = ud.cam.getWorldPosition(tmp.set(0, 0, 0)).clone();
    const tHit = camWorld.y / Math.max(0.2, -look.y);
    const c = camWorld.clone().add(look.clone().multiplyScalar(tHit)); c.y = 0;
    const fw = o.swathCam, fl = o.swathCam * (S.cam === 'TH' || S.cam === 'SW' ? 0.8 : S.cam === 'Duos' ? 0.875 : 0.73);
    const right = new THREE.Vector3(-dir.z, 0, dir.x);
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => c.clone().add(right.clone().multiplyScalar(a * fw / 2)).add(dir.clone().multiplyScalar(b * fl / 2)));
    const arr = fpGeo.attributes.position.array; let k = 0;
    const put = (v) => { arr[k++] = v.x; arr[k++] = v.y + 0.06; arr[k++] = v.z; };
    for (let i = 0; i < 4; i++) { put(camWorld); put(corners[i]); put(corners[i]); put(corners[(i + 1) % 4]); }
    fpGeo.attributes.position.needsUpdate = true;
    fpFill.position.set(c.x, 0.05, c.z); fpFill.scale.set(fw, fl, 1); fpFill.rotation.z = -heading;
    fp.visible = fpFill.visible = view !== 'drone' || S.alt < 10 || true;

    // paint the analysed layer: the strip under the footprint (the spray swath for the sprayer)
    if (playing) {
      const paintW = S.swath || o.swathCam;
      const px = (c.x / W + 0.5) * 512, pz = (c.z / H + 0.5) * 384;
      mctx.save(); mctx.translate(px, pz); mctx.rotate(Math.atan2(dir.z, dir.x));
      mctx.fillStyle = '#fff'; mctx.fillRect(-(fl / W) * 512 / 2, -(paintW / H) * 384 / 2, (fl / W) * 512, (paintW / H) * 384);
      mctx.restore(); mTex.needsUpdate = true;
      frames += (S.speed * tx * dt) / Math.max(0.5, fl * 0.2);
      // finds under the footprint
      for (const f of finds) {
        if (f.found) continue;
        const d = f.p.clone().sub(c);
        if (Math.abs(d.dot(right)) < paintW / 2 && Math.abs(d.dot(dir)) < fl / 2 + 1) {
          f.found = true; f.m.visible = true; f.t = simT;
          const li = document.createElement('li'); li.innerHTML = `<i></i>${f.label}<span>${fmt(plan.timex * simT / 60, 0)} min</span>`; $('finds').prepend(li);
          $('nf').textContent = finds.filter((x) => x.found).length;
        }
      }
    }
    finds.forEach((f) => { if (f.m.visible) { const s = 1 + 0.15 * Math.sin(simT * 4); f.m.children[0].scale.set(s, s, s); } });

    // spray mist under the boom
    if (mist) {
      const pos = mist.geometry.attributes.position.array, life = mist.userData.life, nz = ud.nozzles;
      for (let i = 0; i < life.length; i++) {
        life[i] += dt * 1.2;
        if (life[i] > 1) life[i] = 0;
        const n = nz[i % nz.length];
        tmp.set(n.x + (Math.random() - 0.5) * 0.1 * (1 + life[i] * 4), n.y - life[i] * flyAlt, n.z + life[i] * 0.6).applyQuaternion(drone.quaternion).add(drone.position);
        pos[i * 3] = tmp.x; pos[i * 3 + 1] = Math.max(0.05, tmp.y); pos[i * 3 + 2] = tmp.z;
      }
      mist.geometry.attributes.position.needsUpdate = true;
    }

    // camera views; the auto tour cycles them until someone takes over
    if (auto && simT - lastSwitch > 9) { lastSwitch = simT; view = view === 'drone' ? 'survey' : view === 'survey' ? 'map' : 'drone'; el.querySelectorAll('[data-v]').forEach((x) => x.classList.toggle('on', x.dataset.v === view)); }
    const span = ud.span;
    if (view === 'drone') {
      const back = dir.clone().multiplyScalar(-span * 2.6).applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.7 + yaw);
      camPos.copy(drone.position).add(back).add(new THREE.Vector3(0, span * (1.3 + pitch * 2), 0));
      camTgt.copy(drone.position).add(new THREE.Vector3(0, -span * 0.9, 0));
    } else if (view === 'survey') {
      const r = Math.max(alt * 1.7, o.swathCam * 3);
      camPos.copy(drone.position).add(new THREE.Vector3(Math.sin(0.9 + yaw) * r, alt * (0.5 + pitch), Math.cos(0.9 + yaw) * r));
      camTgt.copy(c).lerp(drone.position, 0.35);
    } else {
      camPos.set(Math.sin(yaw) * H * 0.2, H * 1.55, H * 0.45);
      camTgt.set(0, 0, 0);
    }
    const k2 = 1 - Math.pow(0.03, dt);
    const rel = view === 'map' ? camPos.clone() : camPos.clone().sub(drone.position);
    const relT = view === 'map' ? camTgt.clone() : camTgt.clone().sub(drone.position);
    if (lastView !== view) { offP.copy(rel); offT.copy(relT); lastView = view; cam.near = view === 'drone' ? 0.05 : view === 'survey' ? 0.5 : 5; cam.updateProjectionMatrix(); }
    offP.lerp(rel, k2); offT.lerp(relT, k2);
    if (view === 'map') { cam.position.copy(offP); cam.lookAt(offT); }
    else { cam.position.copy(drone.position).add(offP); cam.lookAt(tmp.copy(drone.position).add(offT)); }
    sun.position.copy(drone.position).add(new THREE.Vector3(-30, 60, 25).multiplyScalar(Math.max(1, alt / 30)));
    sun.target.position.copy(drone.position); sun.target.position.y = 0;
    const sc = sun.shadow.camera, half = Math.max(4, span * 3, alt * 0.3); sc.left = -half; sc.right = half; sc.top = half; sc.bottom = -half; sc.far = alt * 6 + 200; sc.updateProjectionMatrix();
    renderer.render(scene, cam);

    // HUD, a few times a second is enough
    if ((hudT += dt) > 0.2) {
      hudT = 0;
      const done = Math.min(1, dist / plan.len);
      const area = W * H * done;
      const acres = area / 4046.86;
      if (W * H / 4046.86 > 10) { $('area').textContent = fmt(acres, acres < 100 ? 1 : 0); $('areaU').textContent = ` of ${fmt(W * H / 4046.86, 0)} acres`; }
      else { $('area').textContent = fmt(area, 0); $('areaU').textContent = ` of ${fmt(W * H, 0)} m²`; }
      $('bar').style.width = `${done * 100}%`;
      $('pass').textContent = `${Math.min(o.passes, Math.floor(done * o.passes) + 1)} / ${o.passes}`;
      const secs = plan.timex * simT; $('time').textContent = `${Math.floor(secs / 60)}:${String(Math.floor(secs % 60)).padStart(2, '0')}`;
      $('frames').textContent = fmt(frames, 0); $('timex').textContent = `× ${fmt(tx, 0)}`;
      $('gsd').textContent = unitLen(o.gsd).split(' ')[0]; $('gsdU').textContent = ` ${unitLen(o.gsd).split(' ')[1]} / px`;
      $('form').textContent = `GSD = ${fmt(alt, alt < 10 ? 1 : 0)} m × ${fmt(C.px * 1e6, 2)} µm ÷ ${fmt(C.f * 1000, 0)} mm`;
      $('swath').textContent = S.swath ? `${fmt(S.swath, 1)} m spray · ${fmt(o.swathCam, 1)} m camera` : `${fmt(o.swathCam, 1)} m, ${fmt(S.side * 100, 0)} % sidelap`;
      $('alt').textContent = `${fmt(alt, alt < 10 ? 1 : 0)} m`; $('spd').textContent = `${fmt(S.speed, 0)} m/s`;
      const extra = {
        crop: ['Survey rate', `${fmt(S.speed * o.spacing * 3600 / 4046.86, 0)} acres / h`],
        spraying: ['Depth error', `± ${fmt(alt * alt * 0.25 * C.px / (C.f * 0.026) * 100, 1)} cm`],
        solar: ['Modules seen', fmt(done * 2520, 0)],
        industrial: ['Roof scanned', `${fmt(area, 0)} m²`],
        construction: ['Change map', 'week 3 → 11'],
      }[el.dataset.scene];
      $('xk').textContent = extra[0]; $('xv').textContent = extra[1];
      // mini map: ground, the revealed layer, the drone
      ox.globalCompositeOperation = 'source-over'; ox.clearRect(0, 0, 240, 180); ox.drawImage(mask, 0, 0, 240, 180);
      ox.globalCompositeOperation = 'source-in'; if (lImg.complete) ox.drawImage(lImg, 0, 0, 240, 180);
      if (gImg.complete) mx.drawImage(gImg, 0, 0, 240, 180);
      mx.fillStyle = 'rgba(255,255,255,.35)'; mx.fillRect(0, 0, 240, 180);
      mx.drawImage(off, 0, 0);
      mx.fillStyle = '#0b3d2a'; mx.beginPath(); mx.arc((p.x / W + 0.5) * 240, (p.z / H + 0.5) * 180, 4, 0, 7); mx.fill();
      finds.forEach((f) => { if (f.found) { mx.strokeStyle = '#d7301f'; mx.lineWidth = 2; mx.beginPath(); mx.arc((f.p.x / W + 0.5) * 240, (f.p.z / H + 0.5) * 180, 6, 0, 7); mx.stroke(); } });
    }
  }
  requestAnimationFrame(frame);
}

document.querySelectorAll('.fly[data-scene]').forEach((el) => {
  // build only when the demo is near the screen, so pages stay light
  const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); try { mount(el); } catch (e) { el.classList.add('fly-off'); console.error(e); } } }, {rootMargin: '300px'});
  io.observe(el);
});
