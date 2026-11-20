// Aviac home scroll hero. One continuous flight over a mosaic landscape: a farm, a solar farm, industrial roofs and a city
// building site. The fixed-wing VTOL's belly camera reveals each tile's invisible band behind its footprint (NDVI, thermal,
// SWIR, change), a line types itself over each, and the flight ends high above all four as a wireframe twin. The camera
// follows one Catmull-Rom spline through its keys so the motion never stops and starts. Lenis eases the scroll.
// After the hero, "Light carries the answer": spectrum waves, a lens that cycles the four bands, and the readings rail.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import Lenis from 'lenis';

const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const hero = $('.sh');
const R = hero?.dataset.root ?? '';
const IMG = R + 'assets/img/demo/';
const CAPTURE = location.search.includes('capture');
const REDUCE = matchMedia('(prefers-reduced-motion: reduce)').matches;

// the four worlds, in flight order (tile 440 × 330 m each, along +x)
const ZONES = [
  {a: 'field_rgb', b: 'field_ndvi', hud: 'MS · NDVI', find: [81.3, 33.0, 'Stress · 0.21 ac']},
  {a: 'solar_rgb', b: 'solar_thermal', hud: 'TH · Thermal', find: [29.7, 25.2, 'Hot cell']},
  {a: 'swir_visible', b: 'swir_swir', hud: 'SWIRL · SWIR', find: [26.2, 38.3, 'Wet insulation']},
  {a: 'site_w3', b: 'site_w11', hud: 'MS · Change', find: [48.5, 47.5, '+9 floors of frame']},
];
const TW = 440, TD = 330, XS = -TW * 2, XE = TW * 2;               // strip from x = -880 to 880, z = -165 to 165

if (CAPTURE || !REDUCE) {
  if (!CAPTURE) { const lenis = new Lenis({lerp: 0.075, smoothWheel: true, anchors: true}); const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf); }
}
if (hero) startHero();
lightSection();

function typer(el) {
  const text = el.textContent; el.textContent = ''; el.setAttribute('aria-label', text);
  const spans = [...text].map((ch) => { const s = document.createElement('span'); s.textContent = ch; s.setAttribute('aria-hidden', 'true'); el.appendChild(s); return s; });
  let last = -2;
  return (q) => {
    const n = Math.round(clamp(q) * spans.length); if (n === last) return; last = n;
    spans.forEach((s, i) => { s.className = i < n ? 'on' : i === n && n < spans.length ? 'cur' : ''; });
  };
}

function startHero() {
  const stage = $('.sh-stage'), cv = $('.sh-gl');
  let renderer;
  try { renderer = new THREE.WebGLRenderer({canvas: cv, antialias: true, alpha: true, powerPreference: 'high-performance'}); }
  catch { hero.classList.add('sh-static'); return; }
  renderer.setPixelRatio(Math.min(1.75, devicePixelRatio || 1));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.35;
  const camera = new THREE.PerspectiveCamera(34, 1, 0.3, 12000);
  const FOG_DAY = new THREE.Color('#e7b588'), FOG_TWIN = new THREE.Color('#06120d');
  scene.fog = new THREE.Fog(FOG_DAY.clone(), 300, 2600);
  const sun = new THREE.DirectionalLight('#ffbf86', 3.4); scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight('#ffe2c2', '#4a5631', 1.1));
  const rim = new THREE.DirectionalLight('#9fc4ff', 0.6); scene.add(rim, rim.target);

  // one shared mask over the whole strip: white where the camera has looked
  const tl = new THREE.TextureLoader();
  const tex = (n) => { const t = tl.load(IMG + n + '.jpg'); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const MW = 2048, MH = 384, maskCv = document.createElement('canvas'); maskCv.width = MW; maskCv.height = MH;
  const mctx = maskCv.getContext('2d'), tMask = new THREE.CanvasTexture(maskCv); tMask.flipY = false;
  const mx = (x) => ((x - XS) / (XE - XS)) * MW, mz = (z) => ((z + TD / 2) / TD) * MH;
  const shared = {tM: {value: tMask}, uTwin: {value: 0}, uFog: {value: scene.fog.color}, uNear: {value: 300}, uFar: {value: 2600}};
  const tileMat = (z) => new THREE.ShaderMaterial({
    uniforms: {...shared, tA: {value: tex(z.a)}, tB: {value: tex(z.b)}},
    vertexShader: `varying vec2 vUv; varying vec2 vM; varying float vD;
      void main(){ vUv=uv; vec4 w=modelMatrix*vec4(position,1.); vM=vec2((w.x-(${XS.toFixed(1)}))/${(XE - XS).toFixed(1)},(w.z+${(TD / 2).toFixed(1)})/${TD.toFixed(1)});
        vec4 mv=viewMatrix*w; vD=-mv.z; gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform sampler2D tA,tB,tM; uniform float uTwin,uNear,uFar; uniform vec3 uFog; varying vec2 vUv; varying vec2 vM; varying float vD;
      void main(){
        vec3 a=texture2D(tA,vUv).rgb, b=texture2D(tB,vUv).rgb; float m=texture2D(tM,vM).r;
        vec3 bb=mix(vec3(dot(b,vec3(.3,.59,.11))),b,.85);
        vec3 day=mix(a*vec3(1.06,.97,.86), bb, m);
        vec2 g=abs(fract(vUv*vec2(48.,36.))-.5); float l1=1.-smoothstep(.0,.035,min(g.x,g.y));
        vec2 g2=abs(fract(vUv*vec2(12.,9.))-.5); float l2=1.-smoothstep(.0,.012,min(g2.x,g2.y));
        vec3 col=mix(day, b*.45+vec3(.25,.95,.62)*(l1*.2+l2*.45), uTwin);
        col=mix(col,uFog,smoothstep(uNear,uFar,vD));
        gl_FragColor=vec4(col,1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  ZONES.forEach((z, i) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(TW, TD), tileMat(z));
    m.rotation.x = -Math.PI / 2; m.position.set(XS + TW * (i + 0.5), 0, 0); scene.add(m);
  });
  const sTex = tex('field_rgb'); sTex.wrapS = sTex.wrapT = THREE.MirroredRepeatWrapping; sTex.repeat.set(16, 16);
  const AROUND = new THREE.Color('#c9b79a');
  const around = new THREE.Mesh(new THREE.PlaneGeometry(TW * 26, TW * 26), new THREE.MeshStandardMaterial({map: sTex, color: AROUND, roughness: 1}));
  around.rotation.x = -Math.PI / 2; around.position.y = -0.4; scene.add(around);

  // the aircraft: solid by day, wireframe in the twin
  const drone = new THREE.Group(); scene.add(drone);
  const edges = [], solids = [], spin = [];
  const gl = new GLTFLoader(); gl.setMeshoptDecoder(MeshoptDecoder);
  const ready = new Promise((res) => gl.load(hero.dataset.model, (g) => {
    const m = g.scene; m.scale.setScalar(1.6);
    m.traverse((o) => {
      if (!o.isMesh) return;
      o.material = o.material.clone(); o.material.transparent = true; solids.push(o.material);
      const e = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 28), new THREE.LineBasicMaterial({color: '#8ff0b4', transparent: true, opacity: 0}));
      o.add(e); edges.push(e.material);
      if (/pusher_blade/.test(o.name)) spin.push(o);
    });
    drone.add(m); res();
  }, undefined, () => res()));

  // scan frustum and footprint
  const fpMat = new THREE.LineBasicMaterial({color: '#b6ffcf', transparent: true, opacity: 0});
  const fpGeo = new THREE.BufferGeometry(); fpGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(48), 3));
  scene.add(new THREE.LineSegments(fpGeo, fpMat));
  const footMat = new THREE.MeshBasicMaterial({color: '#7cf0a8', transparent: true, opacity: 0, depthWrite: false});
  const foot = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), footMat); foot.rotation.x = -Math.PI / 2; scene.add(foot);

  // twin particles over the whole strip
  const PN = 1800, pPos = new Float32Array(PN * 3);
  for (let i = 0; i < PN; i++) { pPos[i * 3] = XS * 1.1 + Math.random() * (XE - XS) * 1.1; pPos[i * 3 + 1] = Math.random() * 200; pPos[i * 3 + 2] = (Math.random() - 0.5) * TD * 2; }
  const pGeo = new THREE.BufferGeometry(); pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const pMat = new THREE.PointsMaterial({color: '#a6f5c6', size: 1.8, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending});
  scene.add(new THREE.Points(pGeo, pMat));

  // one finding per world, as a pulsing ring with a label
  const finds = ZONES.map((z, i) => {
    const [px, pz, label] = z.find;
    const pos = new THREE.Vector3(XS + TW * i + (px / 100) * TW, 0.6, -TD / 2 + (pz / 100) * TD);
    const ring = new THREE.Mesh(new THREE.RingGeometry(8, 10, 48), new THREE.MeshBasicMaterial({color: '#ff8a5c', transparent: true, opacity: 0, depthWrite: false}));
    ring.rotation.x = -Math.PI / 2; ring.position.copy(pos); scene.add(ring);
    const tag = document.createElement('div'); tag.className = 'sh-tag'; tag.textContent = label; stage.appendChild(tag);
    return {pos, ring, tag};
  });

  // flight: x runs the strip until p = .88, then the camera climbs for the overview
  const ALT = 58, PZ = -40, PEND = 0.88;
  const xAt = (p) => XS + 40 + (XE - XS - 80) * ss(0, PEND, p) ** 0.98;
  // camera keys (drone-relative) on one Catmull-Rom spline, so it glides through them without stopping
  const K = [
    [0.00, [-7.5, -1.6, 6.6], [1.5, 0.9, 0]],
    [0.07, [-5.0, 1.2, 4.8], [0.8, 0, 0]],
    [0.15, [13, 8, 25], [-16, -7, 0]],
    [0.30, [28, 22, 50], [-26, -20, 0]],
    [0.45, [16, 11, 30], [-18, -10, 0]],
    [0.60, [30, 24, 54], [-28, -22, 0]],
    [0.74, [17, 12, 32], [-18, -11, 0]],
    [0.86, [-240, 230, 330], [-260, -55, 30]],                      // pull back and turn to the strip behind
    [1.00, [-840, 1150, 1350], [-840, -58, 0]],                     // high over the middle: all four worlds in frame
  ];
  const ps = K.map((k) => k[0]);
  const camCurve = new THREE.CatmullRomCurve3(K.map((k) => new THREE.Vector3(...k[1])), false, 'centripetal');
  const lookCurve = new THREE.CatmullRomCurve3(K.map((k) => new THREE.Vector3(...k[2])), false, 'centripetal');
  const uAt = (p) => { for (let i = 0; i < ps.length - 1; i++) if (p <= ps[i + 1]) return (i + (p - ps[i]) / (ps[i + 1] - ps[i])) / (ps.length - 1); return 1; };

  const lines = $$('.sh-line', hero).map((el) => ({el, t: typer($('.sh-t', el)), a: +el.dataset.a, b: +el.dataset.b}));
  const night = $('.sh-night'), hud = $('.sh-hud'), hudB = $('.sh-hud b'), hudK = $('.sh-hud span');
  const prog = () => { const r = hero.getBoundingClientRect(); return clamp(-r.top / (hero.offsetHeight - innerHeight)); };
  const resize = () => {
    const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.fov = camera.aspect < 1 ? 56 : 34; camera.updateProjectionMatrix();
  };
  addEventListener('resize', resize); resize();

  const v = new THREE.Vector3(), co = new THREE.Vector3(), lo = new THREE.Vector3(), clock = new THREE.Clock(), cTwin = new THREE.Color('#06120d');
  let pS = 0, lastPaint = -1, onScreen = true;
  new IntersectionObserver(([e]) => { const was = onScreen; onScreen = e.isIntersecting; if (onScreen && !was) requestAnimationFrame(frame); }).observe(hero);

  function frame() {
    if (!onScreen) return;
    const dt = Math.min(0.05, clock.getDelta()), t = clock.elapsedTime;
    pS += (prog() - pS) * (CAPTURE ? 1 : 1 - Math.pow(0.0015, dt));          // frame-rate independent smoothing
    const twin = ss(0.82, 0.93, pS), scan = ss(0.07, 0.13, pS);
    const x = xAt(pS);
    drone.position.set(x, ALT + Math.sin(t * 0.9) * 0.25, PZ);
    drone.rotation.set(Math.sin(t * 0.7) * 0.025, 0, Math.sin(t * 0.5) * 0.012);
    spin.forEach((o) => { o.rotation.x += dt * 60; });
    const u = uAt(pS); camCurve.getPoint(u, co); lookCurve.getPoint(u, lo);
    if (camera.aspect < 1) { lo.x *= 1 - 0.6 * (1 - twin); lo.z *= 0.6; co.multiplyScalar(1 + 0.8 * twin); }   // portrait: keep the aircraft centred, pull back for the overview
    camera.position.copy(drone.position).add(co);
    camera.lookAt(v.copy(drone.position).add(lo));
    sun.position.copy(drone.position).add(v.set(260, 70, 140)); sun.target.position.copy(drone.position);
    rim.position.copy(drone.position).add(v.set(-200, 60, -160)); rim.target.position.copy(drone.position);
    // footprint (about 42 × 31 m at 58 m) and the revealed band behind it
    const sw = 42, sl = 31, inStrip = x > XS && x < XE;
    footMat.opacity = scan * (0.16 - twin * 0.12) * (inStrip ? 1 : 0); foot.scale.set(sl, sw, 1); foot.position.set(x, 0.3, PZ);
    const pa = fpGeo.attributes.position.array, apex = [x + 0.25, ALT - 0.4, PZ];
    const cs = [[x - sl / 2, PZ - sw / 2], [x + sl / 2, PZ - sw / 2], [x + sl / 2, PZ + sw / 2], [x - sl / 2, PZ + sw / 2]];
    let k = 0;
    for (let i = 0; i < 4; i++) { pa.set([...apex, cs[i][0], 0.4, cs[i][1]], k); k += 6; }
    for (let i = 0; i < 4; i++) { const a = cs[i], b = cs[(i + 1) % 4]; pa.set([a[0], 0.4, a[1], b[0], 0.4, b[1]], k); k += 6; }
    fpGeo.attributes.position.needsUpdate = true; fpMat.opacity = scan * 0.75 * (1 - twin);
    const pk = Math.round(pS * 600);
    if (pk !== lastPaint) {
      lastPaint = pk;
      mctx.fillStyle = '#000'; mctx.fillRect(0, 0, MW, MH); mctx.fillStyle = '#fff';
      const x0 = xAt(0.08);
      if (pS > 0.08) { mctx.filter = 'blur(6px)'; mctx.fillRect(mx(x0), mz(PZ - sw / 2), mx(x) - mx(x0), mz(PZ + sw / 2) - mz(PZ - sw / 2)); mctx.filter = 'none'; }
      const grow = ss(0.8, 0.95, pS);                                        // the whole landscape resolves for the overview
      if (grow > 0) { mctx.globalAlpha = grow; mctx.fillRect(0, 0, MW, MH); mctx.globalAlpha = 1; }
      tMask.needsUpdate = true;
    }
    shared.uTwin.value = twin; shared.uFar.value = 2600 + twin * 3400; scene.fog.far = shared.uFar.value;
    scene.fog.color.copy(FOG_DAY).lerp(FOG_TWIN, twin); around.material.color.copy(AROUND).lerp(cTwin, twin);
    solids.forEach((m) => { m.opacity = 1 - twin * 0.82; });
    edges.forEach((m) => { m.opacity = twin * 0.95; });
    pMat.opacity = twin * 0.7;
    if (twin > 0) { for (let i = 0; i < PN; i++) pPos[i * 3 + 1] = (pPos[i * 3 + 1] + dt * 3) % 200; pGeo.attributes.position.needsUpdate = true; }
    night.style.opacity = twin.toFixed(3);
    // findings: each lights up once the camera has passed it, all of them in the overview
    finds.forEach((f, i) => {
      const seen = ss(f.pos.x - 10, f.pos.x + 40, x) * (1 - ss(f.pos.x + 260, f.pos.x + 340, x));
      const a = Math.max(seen, ss(0.86, 0.92, pS));
      f.ring.material.opacity = a * (0.6 + 0.4 * Math.sin(t * 3 + i)); f.ring.scale.setScalar(1 + 0.25 * ((t * 0.8 + i * 0.5) % 1));
      v.copy(f.pos).project(camera);
      f.tag.style.opacity = a > 0.02 && v.z < 1 ? a.toFixed(3) : 0;
      f.tag.style.transform = `translate(${(v.x * 0.5 + 0.5) * stage.clientWidth}px, ${(-v.y * 0.5 + 0.5) * stage.clientHeight}px)`;
    });
    lines.forEach((L) => {
      const q = clamp((pS - L.a) / (L.b - L.a));
      L.t(q / 0.75);
      L.el.style.opacity = (ss(L.a - 0.012, L.a, pS) * (1 - ss(L.b, L.b + 0.025, pS))).toFixed(3);
    });
    const zi = clamp(Math.floor((x - XS) / TW), 0, 3);
    hud.style.opacity = (scan * (1 - twin)).toFixed(3);
    hudK.textContent = ZONES[zi].hud;
    hudB.textContent = `${Math.round(clamp((x - xAt(0.08)) / (XE - 40 - xAt(0.08))) * 100)} %`;
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  ready.then(() => { hero.classList.add('sh-ready'); requestAnimationFrame(frame); });
}

// ---------------------------------------------------------------- after the hero: light carries the answer
function lightSection() {
  const sec = $('.lc'); if (!sec) return;
  // spectrum waves, drifting slowly
  const g = $('.lc-waves g', sec);
  if (g) {
    const N = 14, paths = [];
    for (let k = 0; k < N; k++) { const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('opacity', (1 - k / (N + 1)).toFixed(2)); g.appendChild(p); paths.push(p); }
    let vis = false; new IntersectionObserver(([e]) => { vis = e.isIntersecting; if (vis) requestAnimationFrame(draw); }).observe(sec);
    const t0 = performance.now();
    function draw(now) {
      if (!vis) return;
      const ph = REDUCE ? 0 : (now - t0) / 1000;
      paths.forEach((p, k) => {
        let d = 'M0 125';
        for (let x = 0; x <= 1440; x += 8) {
          const f = 0.004 + x * 0.000035 + k * 0.0004, a = 40 * Math.sin((x / 1440) * Math.PI) * (1 - k / 18);
          d += ` L${x} ${(125 + a * Math.sin(x * f * 3.14 + k * 0.5 - ph * 0.6)).toFixed(1)}`;
        }
        p.setAttribute('d', d);
      });
      if (!REDUCE) requestAnimationFrame(draw);
    }
  }
  // the lens: cycles the four bands, follows the pointer
  const LAY = [
    {a: 'field_rgb', b: 'field_ndvi', row: 0}, {a: 'solar_rgb', b: 'solar_thermal', row: 1},
    {a: 'swir_visible', b: 'swir_swir', row: 2}, {a: 'field_rgb', b: 'spray_coverage', row: 3},
  ];
  const box = $('.lc-lens', sec), rows = $$('.lc-tele > div', sec);
  if (!box) return;
  let li = 0;
  const show = (i) => {
    li = i; const L = LAY[i];
    $('.lc-a', box).style.backgroundImage = `url(${IMG}${L.a}.jpg)`; $('.lc-b', box).style.backgroundImage = `url(${IMG}${L.b}.jpg)`;
    rows.forEach((r, j) => r.classList.toggle('on', j === L.row));
  };
  LAY.forEach((L) => { new Image().src = IMG + L.a + '.jpg'; new Image().src = IMG + L.b + '.jpg'; });
  show(0);
  rows.forEach((r, j) => r.addEventListener('click', () => { show(j); user = performance.now() + 6000; }));
  let tx = 0.5, ty = 0.5, x = 0.5, y = 0.5, user = -1e9, vis = false, t0 = performance.now(), lastCycle = performance.now();
  box.addEventListener('pointermove', (e) => { const r = box.getBoundingClientRect(); tx = (e.clientX - r.left) / r.width; ty = (e.clientY - r.top) / r.height; user = performance.now(); });
  new IntersectionObserver(([e]) => { vis = e.isIntersecting; if (vis) requestAnimationFrame(tick); }).observe(box);
  function tick(now) {
    if (!vis) return;
    if (now - user > 2500) { const t = (now - t0) / 1000; tx = 0.5 + 0.24 * Math.sin(t * 0.45); ty = 0.5 + 0.2 * Math.sin(t * 0.7 + 1); }
    if (now - user > 2500 && now - lastCycle > 4200 && !REDUCE) { lastCycle = now; show((li + 1) % LAY.length); }
    x += (tx - x) * 0.1; y += (ty - y) * 0.1;
    box.style.setProperty('--x', (x * 100).toFixed(2) + '%'); box.style.setProperty('--y', (y * 100).toFixed(2) + '%');
    requestAnimationFrame(tick);
  }
}
