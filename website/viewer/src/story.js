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
  const portrait = innerWidth / innerHeight < 0.8;                       // phones: their own portrait film, the drone framed for it
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
  for (let i = 0; i < Math.min(N, 40); i++) push(i);
  for (const step of [8, 4, 2, 1]) for (let i = 0; i < N; i += step) push(i);
  let next = 0;
  const worker = async () => {
    while (next < order.length) { const i = order[next++]; await load(i); if (i === 0) { hero.classList.add('sh-ready'); draw(true); } }
  };
  for (let k = 0; k < 6; k++) worker();

  const lines = $$('.sh-line', hero).map((el) => ({el, t: typer($('.sh-t', el)), a: +el.dataset.a, b: +el.dataset.b}));
  const hud = $('.sh-hud'), hudB = $('.sh-hud b'), card = $('.sh-card'), bandEls = $$('.sh-bands i');
  const LABEL = {nitrogen: ['Nitrogen deficit · 0.21 ac', '#ffa431'], water: ['Water stress · 0.6 ac', '#5aa7ff'], pest: ['Pest damage · 0.08 ac', '#ff5a4a'], yield: ['High-yield zone · 3.4 ac', '#5fe08a']};
  let pins = null, tags = [];
  fetch(base + 'pins.json').then((r) => r.json()).then((j) => {
    pins = j.pins;
    tags = j.order.map((k) => { const d = document.createElement('div'); d.className = 'sh-tag'; d.textContent = LABEL[k][0]; d.style.background = LABEL[k][1]; stage.appendChild(d); return d; });
  }).catch(() => {});

  let W = 0, H = 0, dpr = 1;
  const resize = () => { dpr = Math.min(1.5, devicePixelRatio || 1); W = stage.clientWidth; H = stage.clientHeight; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); draw(true); };
  addEventListener('resize', resize);
  const cover = (im) => { const s = Math.max(W / im.width, H / im.height), w = im.width * s, h = im.height * s; return {x: (W - w) / 2, y: (H - h) / 2, w, h}; };
  const nearest = (i) => { for (let d = 0; d < N; d++) { if (frames[i - d]) return i - d; if (frames[i + d]) return i + d; } return -1; };
  const prog = () => { const r = hero.getBoundingClientRect(); return clamp(-r.top / (hero.offsetHeight - innerHeight)); };
  let pS = 0, lastDrawn = -1;

  function draw(force) {
    const f = pS * (N - 1), i0 = Math.floor(f), fr = f - i0;
    const a = nearest(i0);
    if (a < 0 || !W) return;
    const blend = a === i0 && frames[i0 + 1] && fr > 0.03 && fr < 0.97;        // cross-fade only between two real neighbours
    const key = a * 100 + (blend ? Math.round(fr * 24) : 0);
    if (!force && key === lastDrawn) return; lastDrawn = key;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const c = cover(frames[a]);
    ctx.globalAlpha = 1; ctx.drawImage(frames[a], c.x, c.y, c.w, c.h);
    if (blend) { ctx.globalAlpha = fr; ctx.drawImage(frames[i0 + 1], c.x, c.y, c.w, c.h); ctx.globalAlpha = 1; }
    // finding labels sit on the rendered rings (positions exported from Blender for every frame)
    const P = pins && pins[String(Math.round(f) + 1)], show = ss(0.76, 0.84, pS);
    tags.forEach((t, k) => {
      if (!P || !P[k] || P[k][2] < 0 || show < 0.01) { t.style.opacity = 0; return; }
      t.style.opacity = show.toFixed(3);
      t.style.transform = `translate(${clamp(c.x + P[k][0] * c.w, 4, W - t.offsetWidth - 26).toFixed(1)}px, ${(c.y + (1 - P[k][1]) * c.h).toFixed(1)}px)`;
    });
  }

  let onScreen = true;
  new IntersectionObserver(([e]) => { const was = onScreen; onScreen = e.isIntersecting; if (onScreen && !was) requestAnimationFrame(tick); }).observe(hero);
  function tick() {
    if (!onScreen) return;
    pS = prog();
    draw(false);
    lines.forEach((L) => {
      L.t(clamp((pS - L.a) / ((L.b - L.a) * 0.72)));
      L.el.style.opacity = (ss(L.a - 0.015, L.a, pS) * (1 - ss(L.b, L.b + 0.03, pS))).toFixed(3);
    });
    const cA = ss(0.84, 0.92, pS);
    hud.style.opacity = (ss(0.22, 0.28, pS) * (portrait ? 1 - cA : 1)).toFixed(3);   // phones: the finding card takes the HUD's place
    hudB.textContent = `${Math.round(ss(0.26, 0.8, pS) * 100)} %`;
    bandEls.forEach((el, i) => el.classList.toggle('on', pS > 0.26 + i * 0.035));
    card.style.opacity = cA.toFixed(3); card.style.transform = `translateY(${((1 - cA) * 18).toFixed(1)}px)`;
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
    $('.lc-a', box).style.backgroundImage = `url(${IMG}${L.a}.jpg)`; $('.lc-b', box).style.backgroundImage = `url(${IMG}${L.b}.jpg)`;
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
