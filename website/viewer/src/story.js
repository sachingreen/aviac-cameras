// Aviac home hero: a rendered film (Blender Cycles, 200 frames, one orbit locked on the aircraft) scrubbed by the scroll, as
// the best product pages do it. The page only draws pictures, so it stays smooth on any device: the opening frames load first,
// in order, then the rest coarse to fine, cross-fading between neighbours so motion never steps. Over it: lines that type
// themselves, MS's six bands lighting up, the share of the field surveyed, labels on the four findings (positions exported from
// Blender per frame) and the finding card.
// After the hero, "Light carries the answer": spectrum waves and a lens over the farm.
import Lenis from 'lenis';

const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const hero = $('.sh');
const R = hero?.dataset.root ?? '';
const IMG = R + 'assets/img/demo/';
const CAPTURE = location.search.includes('capture');
const REDUCE = matchMedia('(prefers-reduced-motion: reduce)').matches;

// light easing: the film follows the hand closely (0.1 is Lenis's own default; heavier felt rubbery)
if (!CAPTURE && !REDUCE) { const lenis = new Lenis({lerp: 0.1, smoothWheel: true, anchors: true}); const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf); }
if (hero) film();
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

function film() {
  const stage = $('.sh-stage'), cv = $('.sh-gl'), ctx = cv.getContext('2d', {alpha: false});
  const N = +hero.dataset.frames, ext = hero.dataset.ext || 'webp';
  const portrait = innerWidth / innerHeight <= 0.8;                      // phones: their own portrait film, the drone framed for it
  const conn = navigator.connection, STEP = conn && (conn.saveData || /2g$/.test(conn.effectiveType || '')) ? 2 : 1;   // data saver: every other frame
  const base = portrait && hero.dataset.filmM ? hero.dataset.filmM : hero.dataset.film;
  const frames = new Array(N).fill(null);
  const src = (i) => `${base}f${String(i + 1).padStart(3, '0')}.${ext}`;
  const load = (i) => new Promise((res) => {
    if (frames[i]) return res();
    const im = new Image(); im.decoding = 'async';
    im.onload = () => { (im.decode ? im.decode() : Promise.resolve()).catch(() => {}).then(() => { frames[i] = im; res(); }); };
    im.onerror = () => res(); im.src = src(i);
  });
  // the opening first, in order (that is where the scroll starts), then every 8th, 4th, 2nd frame across the film
  const order = [], seen = new Uint8Array(N);
  const push = (i) => { if (i >= 0 && i < N && !seen[i]) { seen[i] = 1; order.push(i); } };
  for (let i = 0; i < Math.min(N, 40); i += STEP) push(i);
  for (const step of [8, 4, 2, 1]) if (step >= STEP) for (let i = 0; i < N; i += step) push(i);
  let next = 0;
  const worker = async () => {
    while (next < order.length) { const i = order[next++]; await load(i); if (i === 0) { hero.classList.add('sh-ready'); draw(true); } }
  };
  for (let k = 0; k < 6; k++) worker();

  const lines = $$('.sh-line', hero).map((el) => ({el, t: typer($('.sh-t', el)), a: +el.dataset.a, b: +el.dataset.b}));
  const hud = $('.sh-hud'), hudB = $('.sh-hud b'), card = $('.sh-card'), bandEls = $$('.sh-bands i'), hint = $('.sh-hint');
  const LABEL = {nitrogen: ['Nitrogen deficit · 110 m²', '#ffa431'], water: ['Water stress · 200 m²', '#5aa7ff'], pest: ['Pest damage · 40 m²', '#ff5a4a'], yield: ['High-yield zone · 150 m²', '#5fe08a']};
  // each label hangs above its zone (from the zone's far edge) or below it (from the near edge), both exported from Blender for
  // every frame. It takes whichever spot is clear of the aircraft, the card, the HUD, the words and the other labels, and glides
  // across when that changes, so nothing ever sits on top of anything else.
  let pins = null, near = null, tags = [];
  fetch(base + 'pins.json').then((r) => r.json()).then((j) => {
    pins = j.pins; near = j.near || null;
    tags = j.order.map((k) => {
      const d = document.createElement('div'); d.className = 'sh-tag'; d.textContent = LABEL[k][0];
      d.style.background = LABEL[k][1]; stage.appendChild(d); return {el: d, side: 0, w: 0, h: 0, css: 'off', op: ''};
    });
    measure();
  }).catch(() => {});

  let W = 0, H = 0, dpr = 1;
  // what the labels must keep clear of, measured once per layout (positions relative to the stage)
  const nav = $('.nav');
  const walls = {top: 8, card: null, hud: null, words: []};
  function measure() {
    const sr = stage.getBoundingClientRect(), rel = (r) => ({l: r.left - sr.left, t: r.top - sr.top, r: r.right - sr.left, b: r.bottom - sr.top});
    walls.top = nav ? nav.offsetHeight + 8 : 8;
    walls.card = rel(card.getBoundingClientRect()); walls.hud = rel(hud.getBoundingClientRect());
    walls.words = lines.map((L) => {                                     // one box per rendered line of each sentence
      const rows = new Map();
      $$('.sh-t span, .sh-s', L.el).forEach((g) => {
        const r = g.getBoundingClientRect(); if (!r.width) return;
        const k = Math.round(r.top), o = rows.get(k);
        rows.set(k, o ? {l: Math.min(o.l, r.left), t: Math.min(o.t, r.top), r: Math.max(o.r, r.right), b: Math.max(o.b, r.bottom)} : {l: r.left, t: r.top, r: r.right, b: r.bottom});
      });
      return [...rows.values()].map((r) => rel({left: r.l - 6, top: r.t - 4, right: r.r + 6, bottom: r.b + 4}));
    });
    tags.forEach((t) => { t.w = t.el.offsetWidth; t.h = t.el.offsetHeight; });
  }
  const resize = () => { dpr = Math.min(1.5, devicePixelRatio || 1); W = stage.clientWidth; H = stage.clientHeight; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); draw(true); measure(); };
  addEventListener('resize', resize);
  if (document.fonts) document.fonts.ready.then(measure);
  const cover = (im) => { const s = Math.max(W / im.width, H / im.height), w = im.width * s, h = im.height * s; return {x: (W - w) / 2, y: (H - h) / 2, w, h}; };
  const nearest = (i) => { for (let d = 0; d < N; d++) { if (frames[i - d]) return i - d; if (frames[i + d]) return i + d; } return -1; };
  const prog = () => { const r = hero.getBoundingClientRect(); return clamp(-r.top / (hero.offsetHeight - innerHeight)); };
  let pS = 0, lastDrawn = -1, cov = null;

  function draw(force) {
    const f = pS * (N - 1), i0 = Math.floor(f / STEP) * STEP, i1 = Math.min(N - 1, i0 + STEP), fr = (f - i0) / STEP;
    const a = frames[i0] ? i0 : nearest(Math.round(f));
    if (a < 0 || !W) return;
    const blend = a === i0 && i1 > i0 && frames[i1] && fr > 0.03 && fr < 0.97;   // cross-fade only between two loaded neighbours
    const key = a * 100 + (blend ? Math.round(fr * 24) : 0);
    if (!force && key === lastDrawn) return; lastDrawn = key;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const c = cov = cover(frames[a]);
    ctx.globalAlpha = 1; ctx.drawImage(frames[a], c.x, c.y, c.w, c.h);
    if (blend) { ctx.globalAlpha = fr; ctx.drawImage(frames[i1], c.x, c.y, c.w, c.h); ctx.globalAlpha = 1; }
  }

  const ov = (a, b) => (b ? Math.max(0, Math.min(a.r, b.r) - Math.max(a.l, b.l)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.t, b.t)) : 0);
  // the six spots a label can take around its zone: above or below it, centred, to the right or to the left of the anchor
  const SPOTS = [[0, 0], [1, 0], [0, 1], [1, 1], [0, -1], [1, -1]], PREF = [0, 30, 60, 90, 60, 90];
  function placeTags(dt, cA, hA) {
    const c = cov; if (!c || !pins || !tags.length) return;
    const f = pS * (N - 1), fk = String(Math.round(f) + 1), P = pins[fk], Q = near ? near[fk] : P;
    if (!P || !Q) return;
    const D = P[4], dx = c.x + D[0] * c.w, dy = c.y + (1 - D[1]) * c.h;              // the aircraft: its pin and wingspan on screen
    const plane = portrait ? {l: dx - 0.23 * c.w, r: dx + 0.28 * c.w, t: dy - 0.085 * c.h, b: dy + 0.06 * c.h} : {l: dx - 0.15 * c.w, r: dx + 0.18 * c.w, t: dy - 0.15 * c.h, b: dy + 0.11 * c.h};
    const words = walls.words.flatMap((rows, i) => (+lines[i].el.style.opacity > 0.05 ? rows : []));
    const placed = [], ease = 1 - Math.exp(-dt / 0.14), fade = 1 - Math.exp(-dt / 0.2), cardW = 1.5 * ss(0.8, 0.85, pS);  // the card's spot is kept free just before it lands
    tags.forEach((t, k) => {
      const show = ss(0.75 + 0.025 * k, 0.79 + 0.025 * k, pS), A = P[k], B = Q[k];
      if (!A || !B || A[2] < 0 || show < 0.01) { if (t.css !== 'off') { t.el.style.opacity = 0; t.css = 'off'; t.op = ''; } return; }
      const boxes = SPOTS.map(([below, h]) => {
        const p = below ? B : A, ax = c.x + p[0] * c.w, ay = c.y + (1 - p[1]) * c.h;
        const l = clamp(h === 0 ? ax - t.w / 2 : h > 0 ? ax + 18 : ax - 18 - t.w, 8, W - t.w - 8);
        const tp = clamp(below ? ay + 14 : ay - 18 - t.h, walls.top, H - t.h - 8);
        return {l, t: tp, r: l + t.w, b: tp + t.h};
      });
      const cost = boxes.map((b, i) => PREF[i] + ov(b, plane) + cardW * ov(b, walls.card) + hA * ov(b, walls.hud)
        + words.reduce((s, w) => s + 1.2 * ov(b, w), 0) + placed.reduce((s, o) => s + 0.8 * ov(b, o), 0));
      let best = 0; cost.forEach((v, i) => { if (v < cost[best]) best = i; });
      const first = t.css === 'off' || !t.wt;
      if (first) { t.side = best; t.wt = SPOTS.map((_, i) => +(i === best)); }                // first sight: straight to its spot
      else {
        if (cost[best] + 120 < cost[t.side]) t.side = best;                                   // a little hysteresis, so it never flickers
        t.wt = t.wt.map((v, i) => v + (+(i === t.side) - v) * ease);
      }
      // when even the best spot is crowded (a short screen, the zone passing under the aircraft), the label waits until it is clear
      const crowd = (cost[t.side] - PREF[t.side]) / (t.w * t.h);
      if (first) t.clear = +(crowd < 0.03); else if (crowd > 0.12) t.clear = 0; else if (crowd < 0.03) t.clear = 1;
      t.vis = first ? t.clear : t.vis + (t.clear - t.vis) * fade;
      const sum = t.wt.reduce((s, v) => s + v, 0) || 1;
      let x = 0, y = 0; boxes.forEach((b, i) => { x += b.l * t.wt[i] / sum; y += b.t * t.wt[i] / sum; });
      if (t.vis > 0.3) placed.push({l: x, t: y, r: x + t.w, b: y + t.h});
      const css = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px)`, op = (show * t.vis).toFixed(3);
      if (css !== t.css) { t.el.style.transform = css; t.css = css; }
      if (op !== t.op) { t.el.style.opacity = op; t.op = op; }
    });
  }

  let onScreen = true, last = 0;
  new IntersectionObserver(([e]) => { const was = onScreen; onScreen = e.isIntersecting; if (onScreen && !was) { last = 0; requestAnimationFrame(tick); } }).observe(hero);
  function tick(now) {
    if (!onScreen) return;
    const dt = last ? Math.min(0.1, (now - last) / 1000) : 1; last = now;
    pS = prog();
    draw(false);
    lines.forEach((L) => {
      L.t(clamp((pS - L.a) / ((L.b - L.a) * 0.72)));
      L.el.style.opacity = (ss(L.a - 0.015, L.a, pS) * (1 - ss(L.b, L.b + 0.03, pS))).toFixed(3);
    });
    const cA = ss(0.84, 0.92, pS), hA = ss(0.22, 0.28, pS) * (1 - ss(0.775, 0.8, pS));
    // the survey completes, the HUD bows out, then the findings are labelled and summed up in the card
    hud.style.opacity = hA.toFixed(3);
    hudB.textContent = `${Math.round(ss(0.26, 0.76, pS) * 100)} %`;
    bandEls.forEach((el, i) => el.classList.toggle('on', pS > 0.26 + i * 0.035));
    card.style.opacity = cA.toFixed(3); card.style.transform = `translateY(${((1 - cA) * 18).toFixed(1)}px)`;
    if (hint) hint.style.opacity = (1 - ss(0.015, 0.06, pS)).toFixed(3);              // the hint has done its job once scrolling starts
    placeTags(dt, cA, hA);
    requestAnimationFrame(tick);
  }
  resize(); requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- after the hero: light carries the answer
function lightSection() {
  const sec = $('.lc'); if (!sec) return;
  const g = $('.lc-waves g', sec);
  if (g) {
    const NW = 14, paths = [];
    for (let k = 0; k < NW; k++) { const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('opacity', (1 - k / (NW + 1)).toFixed(2)); g.appendChild(p); paths.push(p); }
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
  const LAY = [{a: 'field_rgb', b: 'field_ndvi', row: 0}, {a: 'field_rgb', b: 'field_ndvi', row: 1}, {a: 'field_rgb', b: 'spray_coverage', row: 2}, {a: 'field_rgb', b: 'spray_coverage', row: 3}];
  const box = $('.lc-lens', sec), rows = $$('.lc-tele > div', sec);
  if (!box) return;
  let li = 0;
  const show = (i) => {
    li = i; const L = LAY[i];
    $('.lc-a', box).style.backgroundImage = `url(${IMG}${L.a}.webp)`; $('.lc-b', box).style.backgroundImage = `url(${IMG}${L.b}.webp)`;
    rows.forEach((r, j) => r.classList.toggle('on', j === L.row));
  };
  show(0);
  let tx = 0.5, ty = 0.5, x = 0.5, y = 0.5, user = -1e9, vis = false;
  const t0 = performance.now(); let lastCycle = performance.now();
  rows.forEach((r, j) => r.addEventListener('click', () => { show(j); user = performance.now() + 6000; }));
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
