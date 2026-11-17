// Aviac 6B as a page you drive. The camera flies over a made-up field: the ground slides under it, the four
// shutters fire together at the interval the overlap needs, frames run down the flat cables, air goes through the
// heatsink duct. Left alone the page tours itself with a cursor; any click, drag, wheel or key hands control to the
// visitor and 25 s of quiet hands it back. Structure after the teardown kit (elvarofficial/teardown, MIT).
import * as THREE from 'three';
import {warmComposer} from '../kit/warm.js';
import {CAMS, createConsole, H_RANGE, MODULES, OPENS, SHOWS, V_RANGE} from './console.js';
import {buildMachine} from './machine.js';
import data from './parts.json';
import {flight, OVERLAP, thermal} from './sim.js';
import {createStage} from './stage.js';

const W = 1600, H = 900, IDLE = 25;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smoother = (x) => { const u = clamp(x, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10); };
const lerp = (a, b, k) => a + (b - a) * k;

const VIEWS = {
  hero: {tx: 0.13, ty: -0.105, tz: 0, az: -0.62, el: 0.13, d: 1.12},
  optics: {tx: 0.155, ty: -0.062, tz: 0, az: -0.5, el: -0.62, d: 0.86},
  board: {tx: 0.06, ty: -0.008, tz: 0, az: -0.22, el: 1.08, d: 0.64},
  shell: {tx: 0.115, ty: -0.045, tz: 0, az: -0.78, el: 0.46, d: 0.92},
  duct: {tx: 0.05, ty: -0.03, tz: 0, az: -1.22, el: 0.05, d: 0.62},
  open: {tx: 0.12, ty: -0.03, tz: 0, az: -0.72, el: 0.2, d: 1.38},
};
const CALLS = {
  hero: [['rgb_bezel', 'C-mount lens, 16 mm', 'Sony IMX565 · 12.4 MP · RGB', [520, 560]], ['mira1_bezel', 'CS-mount lens, 6 mm', 'Mira220 · 2.2 MP · one of three', [1110, 520]],
    ['enclosure_lower', 'Ram-air intake', 'cools the computer, no fan', [520, 330], [0.004, -0.028, 0.02]], ['brd_J1', 'Battery in, 3S to 6S', 'reverse-polarity protected', [700, 170]]],
  optics: [['rgb_lens_glass', 'RGB: blue, green, red', '16 mm C-mount · 39° wide', [525, 250]], ['mira0_filter', 'Red edge', '717 – 730 nm filter', [525, 600]],
    ['mira1_filter', 'Near infrared', '830 – 850 nm filter', [1180, 300]], ['mira2_filter', 'Extended NIR', '860 – 920 nm filter', [1180, 620]]],
  board: [['brd_U6', 'Sync microcontroller', 'one timer fires all four shutters', [525, 330]], ['brd_U9', 'GNSS receiver', 'time pulse stamps every frame', [600, 150]],
    ['m2_ssd', 'NVMe SSD', '16-bit TIFF, every band', [1180, 640]], ['brd_J3', 'Four camera ports', '2 lanes each · 100 Ω pairs', [1180, 300]], ['brd_L1', 'Power stage', '7.5 V 4 A + 3.3 V 3 A', [525, 640]]],
  duct: [['heatsink', 'Heatsink in the airstream', 'fins along the flow', [1120, 250]], ['jetson_pcb', 'Jetson Orin Nano', '25 W at full load', [1120, 640]]],
  shell: [['lens_plate', 'One machined lens plate', 'keeps four lenses aligned', [1150, 640]], ['fpc_J5', 'Flat cables', 'image data, 2 lanes each', [1150, 250]],
    ['heatsink', 'Heatsink', 'hangs into the air duct', [525, 640]], ['jetson_pcb', 'Jetson Orin Nano 8GB', 'maps the field in flight', [525, 250]]],
  open: [['enclosure_upper', 'Upper shell', 'printed PA12', [1130, 150]], ['carrier_pcb', 'Carrier board', '171 parts · 6 layers', [525, 250]], ['jetson_pcb', 'Jetson Orin Nano 8GB', '67 TOPS', [525, 400]],
    ['heatsink', 'Heatsink', 'black anodised', [525, 540]], ['rgb_sensor_pcb', 'IMX565 sensor board', 'global shutter', [1150, 330]], ['lens_plate', 'Lens plate', 'machined aluminium', [1150, 470]],
    ['rgb_lens_barrel', 'Lenses', '1 × C-mount · 3 × CS-mount', [1150, 600]]],
};
const ISO_TEXT = Object.fromEntries(MODULES.map(([n, g]) => [g, n]));
const MOD_NOTE = {
  'RGB camera (IMX565)': 'SONY IMX565 · 4128 × 3008 · GLOBAL SHUTTER · THE REFERENCE THE OTHER BANDS ARE REGISTERED TO',
  'Red edge camera (Mira220)': 'MIRA220 · 1600 × 1400 · RED EDGE REACTS FIRST WHEN A CROP IS STRESSED',
  'NIR camera (Mira220)': 'MIRA220 · NEAR INFRARED · HEALTHY LEAVES REFLECT STRONGLY HERE',
  'Extended NIR camera (Mira220)': 'MIRA220 · 860 – 920 NM · STOPS SHORT OF THE WATER-VAPOUR DIP IN SUNLIGHT',
  'Optics bench': 'ONE ALUMINIUM PLATE CARRIES ALL FOUR LENS THREADS AND ALL FOUR SENSOR BOARDS',
  'Carrier board': 'POWER, SYNC, GNSS, STORAGE AND FOUR CAMERA PORTS · FIRST ROUTING PASS',
  'Jetson Orin Nano': 'RECEIVES ALL EIGHT CAMERA LANES · REGISTERS, STITCHES AND MAPS DURING THE FLIGHT',
  'Thermal': 'FINNED HEATSINK IN A RAM-AIR DUCT · THE ELECTRONICS BAY STAYS SEALED',
  'DLS + GNSS top unit': 'ON TOP OF THE AIRFRAME · MEASURES SUNLIGHT IN THE SAME BANDS · CARRIES THE GNSS ANTENNA',
};

const CSS = `
html,body{background:#ebebe8;overflow:hidden;margin:0;height:100%;padding:0!important}
#app{position:absolute!important;inset:auto!important;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0}
#gl{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none;cursor:grab}
#gl.drag{cursor:grabbing}
.tb{pointer-events:auto;cursor:pointer;user-select:none}
.tb:hover{filter:brightness(.94)}
.hit{position:absolute;pointer-events:auto;cursor:ew-resize}
.tourchip{position:absolute;left:800px;top:62px;transform:translateX(-50%);display:flex;align-items:center;gap:7px;height:21px;padding:0 11px;border:1px solid #e1e3e6;background:rgba(255,255,255,.95);color:#16181b;font:600 8.8px Inter,sans-serif;letter-spacing:1.3px;white-space:nowrap;cursor:pointer;pointer-events:auto}
.tourchip i{display:block;width:6px;height:6px;border-radius:50%;background:#e2531a}
.tourchip.on i{animation:blink 1.2s steps(2) infinite}
@keyframes blink{50%{opacity:.15}}
.note{position:absolute;left:0;right:0;top:420px;text-align:center;font:600 13px Inter,sans-serif;letter-spacing:1.4px;color:#8b8f95;text-transform:uppercase}
.turn{position:fixed;left:0;right:0;bottom:18px;text-align:center;font:600 12px/1.4 'JetBrains Mono',monospace;letter-spacing:1px;color:#8b8f95;text-transform:uppercase;display:none}
@media (orientation:portrait) and (max-width:820px){.turn{display:block}}
`;

async function run() {
  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);
  const app = document.getElementById('app');
  const canvas = document.createElement('canvas');
  canvas.id = 'gl';
  app.appendChild(canvas);
  const note = document.createElement('div');
  note.className = 'note';
  note.textContent = 'Loading the camera…';
  app.appendChild(note);

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
      fetch(base + 'model.txt').then((r) => { if (!r.ok) throw new Error('model ' + r.status); return r.text(); }).then((s) => {
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
  note.remove();
  const tourChip = document.createElement('div');
  tourChip.className = 'tourchip';
  ui.root.appendChild(tourChip);
  const turn = document.createElement('div');
  turn.className = 'turn';
  turn.textContent = 'Turn your phone sideways for the full console';
  document.body.appendChild(turn);

  // ------------------------------------------------------------ state
  let T = 0, paused = false, hidden = false;
  let h = 120, v = 18, hT = 120, vT = 18;
  let dist = 0, frames = 0, lastTrigDist = 0, mapped = 0;
  const trig = [];                      // times (T) of recent triggers, newest first
  let view = 'hero', open = 'closed', iso = null;
  const show = {labels: 1, footprints: 1, signals: 1, airflow: 0};
  const an = {k: 0, shell: 1, xray: 0, foot: 1, sig: 1, air: 0, top: 0, call: 1};
  const cam = {...VIEWS.hero};
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
  const setOpen = (o) => {
    open = o;
    if (o === 'exploded') { view = 'hero'; iso = null; }
  };
  const act = (k) => {
    if (CAMS.includes(k)) {
      setView(k);
      if (k === 'board' && open === 'closed') open = 'shell off';
      if (k === 'duct') { show.airflow = 1; }
      if (k === 'optics' && open === 'exploded') open = 'closed';
    } else if (OPENS.includes(k)) setOpen(k);
    else if (SHOWS.includes(k)) show[k] = show[k] ? 0 : 1;
    else if (k.startsWith('m:')) {
      const g = k.slice(2);
      iso = iso === g ? null : g;
      if (iso && open === 'closed') open = 'shell off';
    } else if (k === 'pause') paused = !paused;
    else if (k === 'fire') fire();
    if (ui.spots[k]) pulse(...ui.spots[k]);
  };

  // ------------------------------------------------------------ the tour: operator moves on a 46 s loop
  const SCRIPT = [
    [0.0, () => { open = 'closed'; iso = null; setView('hero'); Object.assign(show, {labels: 1, footprints: 1, signals: 1, airflow: 0}); hT = 120; vT = 18; }, null],
    [5.5, () => act('optics'), 'optics'],
    [11.0, () => act('hero'), 'hero'],
    [12.6, () => act('shell off'), 'shell off'],
    [18.0, () => act('board'), 'board'],
    [23.5, () => act('duct'), 'duct'],
    [29.0, () => { act('airflow'); show.airflow = 0; }, 'airflow'],
    [30.0, () => act('exploded'), 'exploded'],
    [37.0, () => act('closed'), 'closed'],
    [39.0, () => { hT = 60; }, 'h', 0.25],
    [43.0, () => { hT = 120; }, 'h', 0.75],
  ];
  const DUR = 46;
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
    const th = thermal(v);
    if (!paused) {
      dist += v * dt;
      if (dist - lastTrigDist >= fl.along * (1 - OVERLAP)) fire();
    }
    mapped = lastTrigDist + fl.along / 2;

    // eased state
    const ease = (key, to, rate = 4) => (an[key] = lerp(an[key], to, 1 - Math.exp(-dt * rate)));
    ease('k', open === 'exploded' ? 1 : 0, 3.2);
    ease('shell', open === 'closed' || open === 'exploded' ? 1 : 0, 5);
    ease('xray', show.airflow && open !== 'shell off' ? 1 : 0, 5);
    ease('foot', show.footprints && view !== 'board' && view !== 'duct' && !(open === 'shell off' && view === 'hero') ? 1 : 0, 5);
    ease('sig', show.signals ? 1 : 0, 6);
    ease('air', show.airflow ? 1 : 0, 5);
    ease('top', iso === 'DLS + GNSS top unit' ? 1 : 0, 5);
    const inside = open === 'shell off' && view === 'hero';
    const vt = open === 'exploded' ? VIEWS.open : iso === 'DLS + GNSS top unit' ? {...VIEWS.hero, ty: 0.0, d: 1.3} : inside ? VIEWS.shell : VIEWS[view];
    const kc = 1 - Math.exp(-dt * 2.6);
    for (const key of ['tx', 'ty', 'tz', 'az', 'el', 'd']) cam[key] = lerp(cam[key], vt[key], kc);
    if (AP.on && view === 'hero' && open !== 'exploded') off.az = Math.sin(T * 0.25) * 0.2;
    else if (AP.on) off.az = lerp(off.az, 0, kc);

    mc.update({k: an.k, shell: an.shell, xray: an.xray, iso, foot: an.foot, sigOn: an.sig, airOn: an.air, top: an.top, fl, th, dist,
      trig: trig.map((t) => T - t), T});
    st.frame({tx: cam.tx, ty: cam.ty, tz: cam.tz, az: cam.az + off.az, el: clamp(cam.el + off.el, -1.45, 1.45), d: cam.d * off.k});

    // overlay
    const since = trig.length ? T - trig[0] : 9;
    ui.update({fl, th, frames, paused, view, open, show, iso, since, mapped, isoText: iso ? MOD_NOTE[iso] : 'FOUR GLOBAL SHUTTERS · ONE HARDWARE TRIGGER · ONE MAP, BUILT IN FLIGHT'});
    const set = open === 'exploded' ? CALLS.open : open === 'shell off' && view === 'hero' ? CALLS.shell : CALLS[view];
    const steady = Math.abs(cam.d - vt.d) < 0.05 && Math.abs(cam.az - vt.az) < 0.06 && Math.abs(off.az) < 0.35 && Math.abs(off.el) < 0.2 && Math.abs(an.k - (open === 'exploded' ? 1 : 0)) < 0.04;
    an.call = lerp(an.call, show.labels && steady && !iso ? 1 : 0, 1 - Math.exp(-dt * (steady ? 5 : 14)));
    ui.callouts((set || []).map(([name, title, sub, to, at]) => {
      const p = at || mc.anchor(name, an.k);
      return {at: st.project(p[0], p[1], p[2]), to, title, sub, a: an.call, hot: /bezel|lens_glass/.test(name) && since < 0.25};
    }));
    const rk = clamp((T - ring.t) / 0.5, 0, 1);
    ui.pointer({...cur, rx: ring.x, ry: ring.y, ring: T - ring.t < 0.5 ? 1 - rk : 0});
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}
run();
