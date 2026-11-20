// Aviac home scroll hero. A fixed-wing VTOL (models/vtol.glb, built in Blender) crosses a field at golden hour; as the page
// scrolls, the belly camera switches on, the field turns into NDVI behind its footprint, the world becomes a wireframe twin
// and the stress zones light up. Three lines type themselves with the scroll. Lenis eases the scrolling on this page.
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

if (hero) start();

function start() {
  // eased scrolling, as on the reference site (off for reduced motion and frame capture)
  if (!CAPTURE && !REDUCE) {
    const lenis = new Lenis({lerp: 0.09, smoothWheel: true, anchors: true});
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf);
  }

  // typing lines: one span per character; the frontier glows
  const typer = (el) => {
    const text = el.textContent; el.textContent = '';
    const spans = [...text].map((ch) => { const s = document.createElement('span'); s.textContent = ch; el.appendChild(s); return s; });
    el.setAttribute('aria-label', text);
    let last = -2;
    return (q) => {
      const n = Math.round(clamp(q) * spans.length); if (n === last) return; last = n;
      spans.forEach((s, i) => { s.className = i < n ? 'on' : i === n && n < spans.length ? 'cur' : ''; });
    };
  };

  const stage = $('.sh-stage'), cv = $('.sh-gl');
  let renderer;
  try { renderer = new THREE.WebGLRenderer({canvas: cv, antialias: true, alpha: true, powerPreference: 'high-performance'}); }
  catch { hero.classList.add('sh-static'); return; }                    // no WebGL: the CSS sunset and the text still play
  renderer.setPixelRatio(Math.min(1.75, devicePixelRatio || 1));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.35;
  const camera = new THREE.PerspectiveCamera(34, 1, 0.3, 9000);
  const FOG_DAY = new THREE.Color('#e7b588'), FOG_TWIN = new THREE.Color('#06120d');
  scene.fog = new THREE.Fog(FOG_DAY.clone(), 260, 2100);
  const sun = new THREE.DirectionalLight('#ffbf86', 3.4); scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight('#ffe2c2', '#4a5631', 1.1));
  const rim = new THREE.DirectionalLight('#9fc4ff', 0.6); scene.add(rim, rim.target);

  // ground: colour, NDVI revealed through a painted mask, and a twin mode with a glowing grid
  const W = 735, tl = new THREE.TextureLoader();
  const tex = (n) => { const t = tl.load(IMG + n + '.jpg'); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const maskCv = document.createElement('canvas'); maskCv.width = maskCv.height = 512;
  const mctx = maskCv.getContext('2d'), tMask = new THREE.CanvasTexture(maskCv);
  const gMat = new THREE.ShaderMaterial({
    uniforms: {tA: {value: tex('field_rgb')}, tB: {value: tex('field_ndvi')}, tM: {value: tMask}, uTwin: {value: 0}, uFog: {value: scene.fog.color}, uNear: {value: 260}, uFar: {value: 2100}},
    vertexShader: 'varying vec2 vUv; varying float vD; void main(){ vUv=uv; vec4 mv=modelViewMatrix*vec4(position,1.); vD=-mv.z; gl_Position=projectionMatrix*mv; }',
    fragmentShader: `uniform sampler2D tA,tB,tM; uniform float uTwin,uNear,uFar; uniform vec3 uFog; varying vec2 vUv; varying float vD;
      void main(){
        vec3 a=texture2D(tA,vUv).rgb, b=texture2D(tB,vUv).rgb; float m=texture2D(tM,vUv).r;
        vec3 bb=mix(vec3(dot(b,vec3(.3,.59,.11))),b,.82);
        vec3 day=mix(a*vec3(1.06,.97,.86), bb, m);
        vec2 g=abs(fract(vUv*48.)-.5); float l1=1.-smoothstep(.0,.035,min(g.x,g.y));
        vec2 g2=abs(fract(vUv*12.)-.5); float l2=1.-smoothstep(.0,.012,min(g2.x,g2.y));
        vec3 col=mix(day, b*.42+vec3(.25,.95,.62)*(l1*.22+l2*.45), uTwin);
        col=mix(col,uFog,smoothstep(uNear,uFar,vD));
        gl_FragColor=vec4(col,1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(W, W), gMat); ground.rotation.x = -Math.PI / 2; scene.add(ground);
  const sTex = tex('field_rgb'); sTex.wrapS = sTex.wrapT = THREE.MirroredRepeatWrapping; sTex.repeat.set(10, 10);
  const around = new THREE.Mesh(new THREE.PlaneGeometry(W * 10, W * 10), new THREE.MeshStandardMaterial({map: sTex, color: '#c9b79a', roughness: 1}));
  around.rotation.x = -Math.PI / 2; around.position.y = -0.4; scene.add(around);
  const AROUND = new THREE.Color('#c9b79a');

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
  const foot = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), footMat); foot.rotation.x = -Math.PI / 2; foot.position.y = 0.3; scene.add(foot);

  // twin particles
  const PN = 1400, pPos = new Float32Array(PN * 3);
  for (let i = 0; i < PN; i++) { pPos[i * 3] = (Math.random() - 0.5) * W * 1.2; pPos[i * 3 + 1] = Math.random() * 160; pPos[i * 3 + 2] = (Math.random() - 0.5) * W * 1.2; }
  const pGeo = new THREE.BufferGeometry(); pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const pMat = new THREE.PointsMaterial({color: '#a6f5c6', size: 1.6, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending});
  scene.add(new THREE.Points(pGeo, pMat));

  // the demo field's stress zones (image %), as pulsing rings with labels
  const FINDS = [[81.3, 33.0, 'Stress · 0.21 ac'], [33.7, 85.9, 'Stress · 0.08 ac']];
  const rings = FINDS.map(([x, y]) => {
    const r = new THREE.Mesh(new THREE.RingGeometry(9, 11, 48), new THREE.MeshBasicMaterial({color: '#ff8a5c', transparent: true, opacity: 0, depthWrite: false}));
    r.rotation.x = -Math.PI / 2; r.position.set((x / 100 - 0.5) * W, 0.6, (y / 100 - 0.5) * W); scene.add(r); return r;
  });
  const tags = FINDS.map(([, , t]) => { const d = document.createElement('div'); d.className = 'sh-tag'; d.textContent = t; stage.appendChild(d); return d; });

  // flight path and camera keys (drone-relative): low against the sunset, a side chase that shows the scan, then high oblique
  const ALT = 58, PZ = -125, X0 = -330, X1 = 330;
  const KEYS = [
    [0.00, [-7.5, -1.6, 6.6], [1.5, 0.9, 0]],
    [0.12, [-5.2, 1.0, 4.6], [0.8, 0.0, 0]],
    [0.27, [12, 7, 24], [-16, -7, 0]],
    [0.42, [34, 24, 54], [-30, -20, 0]],
    [0.58, [-120, 150, 120], [50, -50, 0]],
    [0.74, [-170, 300, 230], [70, -58, 30]],
    [0.88, [-170, 340, 270], [75, -58, 45]],
    [1.00, [-130, 430, 330], [60, -58, 60]],
  ];
  const lerp3 = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  const key = (p) => {
    for (let i = 0; i < KEYS.length - 1; i++) {
      const [p0, c0, l0] = KEYS[i], [p1, c1, l1] = KEYS[i + 1];
      if (p <= p1) { const t = ss(p0, p1, p); return [lerp3(c0, c1, t), lerp3(l0, l1, t)]; }
    }
    return [KEYS.at(-1)[1], KEYS.at(-1)[2]];
  };

  const lines = $$('.sh-line', hero).map((el) => ({el, t: typer($('.sh-t', el)), a: +el.dataset.a, b: +el.dataset.b}));
  const night = $('.sh-night'), hud = $('.sh-hud'), hudP = $('.sh-hud b');
  const prog = () => { const r = hero.getBoundingClientRect(); return clamp(-r.top / (hero.offsetHeight - innerHeight)); };
  const resize = () => {
    const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.fov = camera.aspect < 1 ? 56 : 34; camera.updateProjectionMatrix();
  };
  addEventListener('resize', resize); resize();

  const v = new THREE.Vector3(), clock = new THREE.Clock(), cTwin = new THREE.Color('#06120d');
  let pS = 0, lastPaint = -1, onScreen = true;
  new IntersectionObserver(([e]) => { const was = onScreen; onScreen = e.isIntersecting; if (onScreen && !was) requestAnimationFrame(frame); }).observe(hero);

  function frame() {
    if (!onScreen) return;                                             // stops drawing once the hero has scrolled away
    const dt = Math.min(0.05, clock.getDelta()), t = clock.elapsedTime;
    pS += (prog() - pS) * (CAPTURE ? 1 : 0.12);
    const twin = ss(0.56, 0.7, pS), scan = ss(0.2, 0.3, pS);
    const x = X0 + (X1 - X0) * pS;
    drone.position.set(x, ALT + Math.sin(t * 0.9) * 0.25, PZ);
    drone.rotation.set(Math.sin(t * 0.7) * 0.025, 0, Math.sin(t * 0.5) * 0.012);
    spin.forEach((o) => { o.rotation.x += dt * 60; });
    const [co, lo] = key(pS);
    camera.position.copy(drone.position).add(v.set(...co));
    camera.lookAt(drone.position.x + lo[0], drone.position.y + lo[1], drone.position.z + lo[2]);
    sun.position.copy(drone.position).add(v.set(260, 70, 140)); sun.target.position.copy(drone.position);
    rim.position.copy(drone.position).add(v.set(-200, 60, -160)); rim.target.position.copy(drone.position);
    // footprint (MS at 58 m: about 42 × 31 m) and the NDVI it leaves behind
    const sw = 42, sl = 31;
    footMat.opacity = scan * (0.16 - twin * 0.1); foot.scale.set(sl, sw, 1); foot.position.set(x, 0.3, PZ);
    const pa = fpGeo.attributes.position.array, apex = [x + 0.25, ALT - 0.4, PZ];
    const cs = [[x - sl / 2, PZ - sw / 2], [x + sl / 2, PZ - sw / 2], [x + sl / 2, PZ + sw / 2], [x - sl / 2, PZ + sw / 2]];
    let k = 0;
    for (let i = 0; i < 4; i++) { pa.set([...apex, cs[i][0], 0.4, cs[i][1]], k); k += 6; }
    for (let i = 0; i < 4; i++) { const a = cs[i], b = cs[(i + 1) % 4]; pa.set([a[0], 0.4, a[1], b[0], 0.4, b[1]], k); k += 6; }
    fpGeo.attributes.position.needsUpdate = true; fpMat.opacity = scan * 0.75;
    const pk = Math.round(pS * 400);
    if (pk !== lastPaint) {
      lastPaint = pk;
      const px = (wx) => (wx / W + 0.5) * 512;
      mctx.fillStyle = '#000'; mctx.fillRect(0, 0, 512, 512); mctx.fillStyle = '#fff';
      if (pS > 0.22) { const xs = X0 + (X1 - X0) * 0.22; mctx.fillRect(px(xs), px(PZ - sw / 2), px(x) - px(xs), (sw / W) * 512); }
      const grow = ss(0.5, 0.74, pS);
      if (grow > 0) { mctx.beginPath(); mctx.arc(px(x), px(PZ), grow * 760, 0, Math.PI * 2); mctx.fill(); }
      tMask.needsUpdate = true;
    }
    gMat.uniforms.uTwin.value = twin;
    scene.fog.color.copy(FOG_DAY).lerp(FOG_TWIN, twin); around.material.color.copy(AROUND).lerp(cTwin, twin);
    solids.forEach((m) => { m.opacity = 1 - twin * 0.82; });
    edges.forEach((m) => { m.opacity = twin * 0.95; });
    pMat.opacity = twin * 0.75;
    if (twin > 0) { for (let i = 0; i < PN; i++) pPos[i * 3 + 1] = (pPos[i * 3 + 1] + dt * 3) % 160; pGeo.attributes.position.needsUpdate = true; }
    night.style.opacity = twin.toFixed(3);
    const act = ss(0.66, 0.78, pS);
    rings.forEach((r, i) => {
      r.material.opacity = act * (0.6 + 0.4 * Math.sin(t * 3 + i)); r.scale.setScalar(1 + 0.25 * ((t * 0.8 + i * 0.5) % 1));
      v.copy(r.position).project(camera);
      tags[i].style.opacity = act > 0.02 && v.z < 1 ? act : 0;
      tags[i].style.transform = `translate(${(v.x * 0.5 + 0.5) * stage.clientWidth}px, ${(-v.y * 0.5 + 0.5) * stage.clientHeight}px)`;
    });
    lines.forEach((L) => {
      const q = clamp((pS - L.a) / (L.b - L.a));
      L.t(q / 0.8);
      L.el.style.opacity = pS < L.a - 0.005 ? 0 : pS > L.b + 0.03 ? clamp(1 - (pS - L.b - 0.03) / 0.03) : 1;
    });
    hud.style.opacity = scan.toFixed(3);
    hudP.textContent = `${Math.round(clamp((pS - 0.22) / 0.62) * 100)} %`;
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  ready.then(() => { hero.classList.add('sh-ready'); requestAnimationFrame(frame); });
}
