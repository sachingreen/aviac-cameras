// Aviac Duo as a page you drive. The box flies over a field being sprayed: the crop slides under it, both shutters
// fire together at the interval the overlap needs, the frames run down the flat cables to the Jetson, and the heat
// leaves through the finned lid with no fan. A coverage map fills in as it goes and flags the pass where the pump
// dropped out. Left alone the page tours itself with a cursor; any click, drag, wheel or key hands control to the
// visitor and 25 s of quiet hands it back. Structure after the teardown kit (elvarofficial/teardown, MIT).
import * as THREE from 'three';
import {warmComposer} from '../kit/warm.js';
import {MARK, WORDMARK} from './logo.js';
import {CAMS, createConsole, H_RANGE, MODULES, OPENS, SHOWS, V_RANGE} from './console.js';
import {buildMachine} from './machine.js';
import data from './parts.json';
import {flight, OVERLAP, thermal} from './sim.js';
import {createStage} from './stage.js';

const W = 1600, H = 900, IDLE = 25;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;

const VIEWS = {
  hero: {tx: 0.1, ty: -0.25, tz: 0, az: 1.05, el: 0.24, d: 5.4},
  underside: {tx: 0.051, ty: 0.01, tz: 0, az: -0.95, el: -0.78, d: 0.52},
  inside: {tx: 0.051, ty: 0.04, tz: 0, az: -0.85, el: 0.78, d: 0.5},
  lid: {tx: 0.051, ty: 0.06, tz: 0, az: -1.15, el: 0.3, d: 0.58},
  open: {tx: 0.051, ty: 0.01, tz: 0, az: -1.0, el: 0.16, d: 1.42},
};
const CALLS = {
  hero: [['body', 'Aviac Duo, 108 mm box', 'two Mira220 · 60 mm stereo', [1075, 330]],
    ['mira1_bezel', 'Looks at the crop just sprayed', 'coverage, gaps and drift, live', [1075, 520]],
    ['lid', 'Spray drone, 6 rotors', 'Duo clamps to the skid crossbar', [540, 230], 'drone']],
  underside: [['mira0_bezel', 'Camera A', 'blue · green · red · NIR', [1130, 600]], ['mira1_bezel', 'Camera B', 'any band, twist-lock filter', [480, 300]],
    ['lens_plate', '60 mm stereo baseline', 'one machined plate holds both', [1130, 280], [0.051, -0.001, 0]], ['body', 'Sealed body + windows', 'gasketed against spray drift', [480, 640], [0.0, 0.0, -0.045]]],
  inside: [['brd_U6', 'Sync microcontroller', 'one edge fires both shutters', [470, 330]], ['brd_J1', 'Power in', '3S – 6S, reverse protected', [470, 200]],
    ['fpc_J3', 'Two flat cables', '2 MIPI lanes per camera', [1130, 240]], ['m2_ssd', 'NVMe SSD', 'every pair, 16-bit', [1130, 620]], ['jetson_soc', 'Jetson Orin Nano', 'flipped: the chip faces the lid', [470, 640]]],
  lid: [['lid', 'Finned aluminium lid', 'the only heatsink', [1130, 230]], ['body', 'Body', 'machined 6061, gasketed', [470, 640]], ['yoke', 'Tilt yoke', 'two knobs, no tools', [470, 220]]],
  open: [['lid', 'Finned lid + thermal pad', 'Jetson presses straight into it', [1130, 150]], ['jetson_pcb', 'Jetson Orin Nano 8GB', 'stereo + coverage in flight', [470, 250]],
    ['carrier_pcb', 'Carrier board', 'Duo variant · 2 camera ports', [470, 400]], ['lens_plate', 'Lens plate', 'both lenses, one part', [1130, 470]],
    ['body', 'Body', '108 × 98 × 77 mm', [470, 560]], ['mira1_bezel', 'Windows, filters, bezel', 'sealed from below', [1130, 640]], ['clamp_base', 'Tube clamp', 'fits most spray drones', [1130, 300]]],
};
const MOD_NOTE = {
  'Camera A (Mira220)': 'MIRA220 RGB-IR · 1600 × 1400 GLOBAL SHUTTER · COLOUR AND NEAR INFRARED IN ONE FRAME',
  'Camera B (Mira220)': 'MIRA220 MONO · SAME LENS · DROP IN ANY FILTER FOR THE BAND YOU ARE CHECKING',
  'Optics bench': 'ONE ALUMINIUM PLATE · BOTH LENS THREADS 60 MM APART · THE STEREO BASELINE CANNOT DRIFT',
  'Carrier board': 'SHARED ORIN CARRIER, DUO VARIANT · POWER, SYNC, GNSS TIME, SSD, TWO CAMERA PORTS',
  'Jetson Orin Nano': 'MOUNTED UPSIDE DOWN SO THE MODULE PRESSES INTO THE LID · 15 W IN FLIGHT',
  'Thermal': 'NO FAN, NO DUCT · FINNED LID PLUS THERMAL PAD · ROTOR DOWNWASH DOES THE WORK',
  'Mount': 'YOKE AND TUBE CLAMP · TILTS THE CAMERA TO LOOK STRAIGHT DOWN ON ANY FRAME',
};

const CSS = `
html,body{background:radial-gradient(120% 90% at 50% 40%,#0b1726 0%,#05090f 55%,#020306 100%);overflow:hidden;margin:0;height:100%;padding:0!important}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:2;
  background:repeating-linear-gradient(0deg,rgba(120,200,255,.025) 0 1px,transparent 1px 3px),radial-gradient(120% 100% at 50% 45%,transparent 55%,rgba(0,0,0,.55) 100%)}
body::after{content:'';position:fixed;left:0;right:0;height:140px;top:-140px;pointer-events:none;z-index:3;
  background:linear-gradient(180deg,transparent,rgba(56,225,255,.05),transparent);animation:sweep 7s linear infinite}
@keyframes sweep{to{transform:translateY(calc(100vh + 140px))}}
#app{position:absolute!important;inset:auto!important;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0}
#gl{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none;cursor:grab}
#gl.drag{cursor:grabbing}
.tb{pointer-events:auto;cursor:pointer;user-select:none}
.tb:hover{border-color:rgba(56,225,255,.7);box-shadow:0 0 10px rgba(56,225,255,.35);color:#fff}
.hit{position:absolute;pointer-events:auto;cursor:ew-resize}
.tourchip{position:absolute;left:800px;top:64px;transform:translateX(-50%);display:flex;align-items:center;gap:8px;height:24px;padding:0 14px;border:1px solid rgba(56,225,255,.35);border-radius:12px;
  background:rgba(6,14,24,.6);backdrop-filter:blur(10px);color:#cfe9f7;font:600 8.8px 'Space Grotesk',Inter,sans-serif;letter-spacing:1.6px;white-space:nowrap;cursor:pointer;pointer-events:auto;box-shadow:0 0 18px rgba(56,225,255,.18)}
.tourchip i{display:block;width:6px;height:6px;border-radius:50%;background:#38e1ff;box-shadow:0 0 8px #38e1ff}
.tourchip.on i{animation:blink 1.2s steps(2) infinite}
@keyframes blink{50%{opacity:.15}}
.turn{position:fixed;left:0;right:0;bottom:18px;text-align:center;font:600 12px/1.4 'JetBrains Mono',monospace;letter-spacing:1px;color:#7f95aa;text-transform:uppercase;display:none;z-index:5}
@media (orientation:portrait) and (max-width:820px){.turn{display:block}}
.intro{position:absolute;inset:0;z-index:60;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(80% 70% at 50% 45%,#22342b,#18241e 55%,#0d1612 100%);transition:opacity 1.1s ease,filter 1.1s ease}
.intro.out{opacity:0;filter:blur(8px);pointer-events:none}
.intro .logo{width:170px;margin-bottom:26px;filter:drop-shadow(0 0 22px rgba(242,241,235,.25));animation:rise 1.6s ease both}
.intro .word{width:420px;animation:rise 1.6s .25s ease both}
.intro .word svg{width:100%;height:auto;display:block}
.intro .logo svg{width:100%;height:auto;display:block}
@keyframes rise{from{opacity:0;transform:translateY(14px) scale(.94)}}
.intro .mark{font:700 64px 'Space Grotesk',Inter,sans-serif;letter-spacing:22px;margin-right:-22px;color:transparent;background:linear-gradient(180deg,#fff,#38e1ff);-webkit-background-clip:text;background-clip:text;filter:drop-shadow(0 0 22px rgba(56,225,255,.45))}
.intro .sub{margin-top:14px;font:500 12px 'Space Grotesk',Inter,sans-serif;letter-spacing:6px;color:#7f95aa;text-transform:uppercase}
.intro .bar{margin-top:46px;width:340px;height:2px;background:rgba(120,200,255,.15);position:relative;overflow:hidden}
.intro .bar b{position:absolute;left:0;top:0;bottom:0;width:0;background:linear-gradient(90deg,#38e1ff,#ff6b2c);box-shadow:0 0 12px #38e1ff;transition:width .2s}
.intro .msg{margin-top:14px;font:500 10px 'JetBrains Mono',monospace;letter-spacing:2px;color:#38e1ff;text-transform:uppercase;min-height:14px}
.intro .bands{display:flex;gap:6px;margin-top:30px}
.intro .bands i{width:26px;height:3px;opacity:.25;transition:opacity .4s,box-shadow .4s}
.intro .bands i.on{opacity:1;box-shadow:0 0 10px currentColor}
`;

async function run() {
  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);
  const app = document.getElementById('app');
  const canvas = document.createElement('canvas');
  canvas.id = 'gl';
  app.appendChild(canvas);
  const intro = document.createElement('div');
  intro.className = 'intro';
  const BANDC = ['#38c8ff', '#2f8fd8', '#7a8cff', '#ff6b2c', '#ff4a3a'];
  intro.innerHTML = `<div class="logo">${MARK('#f2f1eb')}</div><div class="word">${WORDMARK('#f2f1eb')}</div><div class="sub">DUO &nbsp;·&nbsp; Stereo spray-check camera</div>
    <div class="bands">${BANDC.map((c) => `<i style="background:${c};color:${c}"></i>`).join('')}</div>
    <div class="bar"><b></b></div><div class="msg">Initialising sensor array</div>`;
  app.appendChild(intro);
  const bar = intro.querySelector('.bar b'), msg = intro.querySelector('.msg'), bandEls = [...intro.querySelectorAll('.bands i')];
  const MSGS = ['Initialising stereo pair', 'Checking the 60 mm baseline', 'Arming the spray trigger', 'Syncing both shutters', 'Ready'];
  const progress = (k) => {
    bar.style.width = `${Math.round(k * 100)}%`;
    msg.textContent = MSGS[Math.min(MSGS.length - 1, Math.floor(k * (MSGS.length - 1)))];
    bandEls.forEach((e, i) => e.classList.toggle('on', k >= (i + 1) / (bandEls.length + 1)));
  };
  const note = {set textContent(t) { msg.textContent = t; msg.style.color = '#ff6b2c'; }, remove() {}};

  let scale = 1;
  const st = createStage(canvas);
  const lite = new URLSearchParams(location.search).has('lite');          // software renderers and slow machines
  const light = lite || matchMedia('(pointer: coarse)').matches || Math.min(innerWidth, innerHeight) < 700;
  const maxPr = lite ? 1 : light ? 1.25 : 2;
  st.setQuality({samples: lite ? 0 : light ? 2 : 4, ao: !light, shadow: lite ? 512 : light ? 1024 : 2048});
  const fit = () => {
    scale = Math.min(innerWidth / W, innerHeight / H);
    app.style.transform = `translate(${(innerWidth - W * scale) / 2}px, ${(innerHeight - H * scale) / 2}px) scale(${scale})`;
    st.resize(W, H, clamp((devicePixelRatio || 1) * scale, 0.75, maxPr));
  };
  fit();
  addEventListener('resize', fit);

  let bin, tex;
  try {
    const base = window.__ASSETS || '';
    [bin, tex] = await Promise.all([
      fetch(base + 'model.txt').then(async (r) => {
        if (!r.ok) throw new Error('model ' + r.status);
        const total = +r.headers.get('content-length') || 3.2e6;
        if (!r.body) return r.text();
        const rd = r.body.getReader(), parts = [];
        let got = 0;
        for (;;) {
          const {done, value} = await rd.read();
          if (done) break;
          parts.push(value); got += value.length;
          progress(Math.min(0.96, got / total));
        }
        return new TextDecoder().decode(await new Blob(parts).arrayBuffer());
      }).then((s) => {
        const raw = atob(s), n = raw.length, u8 = new Uint8Array(n);
        for (let i = 0; i < n; i++) u8[i] = raw.charCodeAt(i);
        return u8.buffer;
      }),
      new THREE.TextureLoader().loadAsync(base + 'board.png'),
    ]);
  } catch (e) {
    note.textContent = 'The 3D model did not load. Reload the page to try again.';
    return;
  }
  const mc = buildMachine(data, bin, tex);
  st.scene.add(mc.root);
  const ui = createConsole(app);
  progress(1);
  setTimeout(() => intro.classList.add('out'), 450);
  setTimeout(() => intro.remove(), 1700);
  const tourChip = document.createElement('div');
  tourChip.className = 'tourchip';
  ui.root.appendChild(tourChip);
  const turn = document.createElement('div');
  turn.className = 'turn';
  turn.textContent = 'Turn your phone sideways for the full console';
  document.body.appendChild(turn);

  // ------------------------------------------------------------ state
  let T = 0, paused = false, hidden = false;
  let h = 3, v = 5, hT = 3, vT = 5;
  let dist = 0, frames = 0, lastTrigDist = 0;
  const trig = [];
  let view = 'hero', open = 'closed', iso = null;
  const show = {labels: 1, footprints: 1, signals: 1, heat: 1};
  const an = {plane: 1, k: 0, lid: 1, body: 1, mount: 1, foot: 1, sig: 1, heat: 1, call: 1};
  const cam = {...VIEWS.hero, d: VIEWS.hero.d * 2.4, az: VIEWS.hero.az + 1.2, el: 0.7};      // flies in on reveal
  const off = {az: 0, el: 0, k: 1};
  let ring = {t: -9, x: 0, y: 0};
  const pulse = (x, y) => (ring = {t: T, x, y});

  const fire = () => {
    trig.unshift(T);
    if (trig.length > 7) trig.pop();
    frames++;
    lastTrigDist = dist;
  };
  const setView = (name) => { view = name; Object.assign(off, {az: 0, el: 0, k: 1}); };
  const act = (k) => {
    if (CAMS.includes(k)) {
      setView(k);
      if (k === 'inside' && open === 'closed') open = 'lid off';
      if (k !== 'inside' && open === 'lid off' && k !== 'hero') open = 'closed';
      if (open === 'exploded') open = 'closed';
    } else if (OPENS.includes(k)) { open = k; if (k === 'exploded') { view = 'hero'; iso = null; } }
    else if (SHOWS.includes(k)) show[k] = show[k] ? 0 : 1;
    else if (k.startsWith('m:')) {
      const g = k.slice(2);
      iso = iso === g ? null : g;
      if (iso && open === 'closed' && !/Camera|Thermal|Mount/.test(iso)) open = 'lid off';
    } else if (k === 'pause') paused = !paused;
    else if (k === 'fire') fire();
    if (ui.spots[k]) pulse(...ui.spots[k]);
  };

  // ------------------------------------------------------------ the tour: operator moves on a 48 s loop
  const SCRIPT = [
    [0.0, () => { open = 'closed'; iso = null; setView('hero'); Object.assign(show, {labels: 1, footprints: 1, signals: 1, heat: 1}); hT = 3; vT = 5; }, null],
    [6.0, () => act('underside'), 'underside'],
    [12.0, () => act('m:Camera B (Mira220)'), 'm:Camera B (Mira220)'],
    [15.5, () => act('m:Camera B (Mira220)'), 'm:Camera B (Mira220)'],
    [17.0, () => act('inside'), 'inside'],
    [23.0, () => act('lid'), 'lid'],
    [28.5, () => act('exploded'), 'exploded'],
    [35.5, () => act('closed'), 'closed'],
    [36.5, () => act('hero'), 'hero'],
    [39.0, () => { hT = 5.5; }, 'h', (5.5 - H_RANGE[0]) / (H_RANGE[1] - H_RANGE[0])],
    [43.5, () => { hT = 3; }, 'h', (3 - H_RANGE[0]) / (H_RANGE[1] - H_RANGE[0])],
  ];
  const DUR = 48;
  const AP = {on: true, t0: 0, i: 0};
  let lastInput = -99;
  const spotOf = (e) => (e[2] === 'h' ? ui.hKnobAt(e[3]) : e[2] ? ui.spots[e[2]] : [800, 470]);
  const startTour = () => { AP.on = true; AP.t0 = T; AP.i = 0; paused = false; };
  const takeOver = () => { lastInput = T; AP.on = false; };
  tourChip.addEventListener('pointerdown', (e) => { e.stopPropagation(); lastInput = T; if (AP.on) takeOver(); else startTour(); });
  addEventListener('pointerdown', (e) => { if (e.target !== tourChip) takeOver(); });

  // ------------------------------------------------------------ controls
  for (const [k, n] of Object.entries(ui.btn)) n.addEventListener('click', () => act(k));
  const slider = (y, range, set) => {
    const hit = document.createElement('div');
    hit.className = 'hit';
    hit.style.cssText = `left:${ui.SL.x - 6}px;top:${y - 9}px;width:${ui.SL.w + 12}px;height:20px`;
    ui.root.appendChild(hit);
    const move = (e) => {
      const r = app.getBoundingClientRect();
      const x = (e.clientX - r.left) / scale;
      set(lerp(range[0], range[1], clamp((x - ui.SL.x) / ui.SL.w, 0, 1)));
    };
    hit.addEventListener('pointerdown', (e) => { hit.setPointerCapture(e.pointerId); move(e); });
    hit.addEventListener('pointermove', (e) => { if (e.buttons) move(e); });
  };
  slider(836, H_RANGE, (x) => (hT = x));
  slider(869, V_RANGE, (x) => (vT = x));
  let drag = null;
  canvas.addEventListener('pointerdown', (e) => { drag = {x: e.clientX, y: e.clientY}; canvas.setPointerCapture(e.pointerId); canvas.classList.add('drag'); });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    off.az -= ((e.clientX - drag.x) / scale) * 0.006;
    off.el = clamp(off.el + ((e.clientY - drag.y) / scale) * 0.005, -1.3, 1.3);
    drag = {x: e.clientX, y: e.clientY};
  });
  const end = () => { drag = null; canvas.classList.remove('drag'); };
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('wheel', (e) => { e.preventDefault(); takeOver(); off.k = clamp(off.k * Math.exp(e.deltaY * 0.0011), 0.35, 1.8); }, {passive: false});
  addEventListener('keydown', (e) => {
    takeOver();
    if (e.key === ' ') { act('pause'); e.preventDefault(); }
    else if (e.key === 'h') { hidden = !hidden; ui.root.style.display = hidden ? 'none' : ''; }
    else if (/^[1-4]$/.test(e.key)) act(CAMS[+e.key - 1]);
  });

  try { await warmComposer?.(st.renderer, st.composer, st.scene, st.camera); } catch (e) { /* warm-up is optional */ }

  // ------------------------------------------------------------ the loop
  let last = performance.now();
  const cursor = {x: 800, y: 470};
  const loop = (now) => {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    T += dt;
    // the tour
    if (!AP.on && T - lastInput > IDLE) startTour();
    let cur = {x: -1, y: -1, press: false};
    if (AP.on) {
      let tt = T - AP.t0;
      if (tt >= DUR) { AP.t0 = T; AP.i = 0; tt = 0; }
      while (AP.i < SCRIPT.length && SCRIPT[AP.i][0] <= tt) { SCRIPT[AP.i][1](); AP.i++; }
      const next = SCRIPT[Math.min(AP.i, SCRIPT.length - 1)];
      const target = AP.i < SCRIPT.length ? spotOf(next) : [800, 470];
      const eta = AP.i < SCRIPT.length ? next[0] - tt : 9;
      const kx = eta < 1.4 ? 1 - Math.exp(-dt * 7) : 1 - Math.exp(-dt * 0.6);
      cursor.x = lerp(cursor.x, target[0], kx);
      cursor.y = lerp(cursor.y, target[1], kx);
      cur = {x: cursor.x, y: cursor.y, press: T - ring.t < 0.14};
    }
    tourChip.className = 'tourchip' + (AP.on ? ' on' : '');
    tourChip.innerHTML = AP.on ? '<i></i>AUTO TOUR &nbsp;·&nbsp; CLICK ANYWHERE TO TAKE OVER' : '<i></i>YOU HAVE CONTROL &nbsp;·&nbsp; RESUME TOUR';

    // flight
    h = lerp(h, hT, 1 - Math.exp(-dt * 3));
    v = lerp(v, vT, 1 - Math.exp(-dt * 3));
    const fl = flight(h, v);
    const th = thermal(v, !paused);
    if (!paused) {
      dist += v * dt;
      if (dist - lastTrigDist >= fl.along * (1 - OVERLAP)) fire();
    }

    // eased state
    const ease = (key, to, rate = 4) => (an[key] = lerp(an[key], to, 1 - Math.exp(-dt * rate)));
    ease('k', open === 'exploded' ? 1 : 0, 3.2);
    ease('plane', view === 'hero' && open === 'closed' && !iso ? 1 : 0, 4);
    ease('lid', open === 'closed' || open === 'exploded' ? 1 : 0, 5);
    ease('body', 1, 5);
    ease('mount', open === 'lid off' || view === 'inside' || view === 'underside' ? 0 : 1, 5);
    ease('foot', show.footprints && view !== 'inside' && view !== 'lid' ? 1 : 0, 5);
    ease('sig', show.signals ? 1 : 0, 6);
    ease('heat', show.heat && open === 'closed' ? 1 : 0, 5);
    const vt = open === 'exploded' ? VIEWS.open : VIEWS[view];
    const kc = 1 - Math.exp(-dt * (T < 4 ? 1.0 : 2.6));
    for (const key of ['tx', 'ty', 'tz', 'az', 'el', 'd']) cam[key] = lerp(cam[key], vt[key], kc);
    if (AP.on && view === 'hero' && open !== 'exploded') off.az = Math.sin(T * 0.25) * 0.2;
    else if (AP.on) off.az = lerp(off.az, 0, kc);

    mc.update({plane: an.plane, k: an.k, lid: an.lid, body: an.body, mount: an.mount, iso, foot: an.foot, sigOn: an.sig, heatOn: an.heat, fl, th, dist,
      trig: trig.map((t) => T - t), T});
    st.frame({tx: cam.tx, ty: cam.ty, tz: cam.tz, az: cam.az + off.az, el: clamp(cam.el + off.el, -1.45, 1.45), d: cam.d * off.k});

    // overlay
    const since = trig.length ? T - trig[0] : 9;
    ui.update({fl, th, frames, paused, flying: !paused, view, open, show, iso, since, dist,
      isoText: iso ? MOD_NOTE[iso] : 'TWO GLOBAL SHUTTERS · ONE TRIGGER · DEPTH, COLOUR AND COVERAGE FROM EVERY PASS'});
    const set = open === 'exploded' ? CALLS.open : CALLS[view];
    const steady = Math.abs(cam.d - vt.d) < 0.04 && Math.abs(cam.az - vt.az) < 0.06 && Math.abs(off.az) < 0.35 && Math.abs(off.el) < 0.2 && Math.abs(an.k - (open === 'exploded' ? 1 : 0)) < 0.04;
    an.call = lerp(an.call, show.labels && steady && !iso ? 1 : 0, 1 - Math.exp(-dt * (steady ? 5 : 14)));
    ui.callouts((set || []).map(([name, title, sub, to, at]) => {
      const p = at === 'drone' ? mc.sprayer.label : at || mc.anchor(name, an.k);
      return {at: st.project(p[0], p[1], p[2]), to, title, sub, a: an.call, hot: /bezel|lens_glass/.test(name) && since < 0.25};
    }));
    const rk = clamp((T - ring.t) / 0.5, 0, 1);
    ui.pointer({...cur, rx: ring.x, ry: ring.y, ring: T - ring.t < 0.5 ? 1 - rk : 0});
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}
run();
