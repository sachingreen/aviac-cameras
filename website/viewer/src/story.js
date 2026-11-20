// Aviac home hero: a rendered film (Blender Cycles, 120 frames) scrubbed by the scroll, the way the best product pages do it.
// The page only draws pictures, so it stays smooth on any device: frame 1 first, then every 16th, 8th, 4th, 2nd frame and the
// rest, cross-fading between neighbours so motion never steps. Over it: lines that type themselves, MS's six bands lighting up,
// the share of the field surveyed, the two stress zones (positions exported from Blender) and the finding card.
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

if (!CAPTURE && !REDUCE) { const lenis = new Lenis({lerp: 0.08, smoothWheel: true, anchors: true}); const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); }; requestAnimationFrame(raf); }
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
  const stage = $('.sh-stage'), cv = $('.sh-gl'), ctx = cv.getContext('2d');
  const N = +hero.dataset.frames, ext = hero.dataset.ext || 'webp';
  const base = innerWidth < 900 && hero.dataset.filmM ? hero.dataset.filmM : hero.dataset.film;   // phones get the 720-px set
  const frames = new Array(N).fill(null);
  const src = (i) => `${base}f${String(i + 1).padStart(3, '0')}.${ext}`;
  const load = (i) => new Promise((res) => {
    if (frames[i]) return res();
    const im = new Image(); im.decoding = 'async';
    im.onload = () => { (im.decode ? im.decode() : Promise.resolve()).catch(() => {}).then(() => { frames[i] = im; res(); }); }; im.onerror = () => res(); im.src = src(i);
  });
  // progressive: the first frame, then coarse to fine
  (async () => {
    await load(0); hero.classList.add('sh-ready'); draw(true);
    for (const step of [12, 6, 3, 1]) {
      const batch = []; for (let i = 0; i < N; i += step) if (!frames[i]) batch.push(i);
      for (let k = 0; k < batch.length; k += 6) await Promise.all(batch.slice(k, k + 6).map(load));
    }
  })();
  let pins = null; fetch(base + 'pins.json').then((r) => r.json()).then((j) => (pins = j)).catch(() => {});

  const lines = $$('.sh-line', hero).map((el) => ({el, t: typer($('.sh-t', el)), a: +el.dataset.a, b: +el.dataset.b}));
  const hud = $('.sh-hud'), hudB = $('.sh-hud b'), card = $('.sh-card'), bandEls = $$('.sh-bands i');
  const FIND = [['Nitrogen deficit · 0.21 ac', '#ffa431'], ['Water stress · 0.6 ac', '#5aa7ff'], ['Pest damage · 0.08 ac', '#ff5a4a'], ['High-yield zone · 3.4 ac', '#5fe08a']];
  const tags = FIND.map(([t, c]) => { const d = document.createElement('div'); d.className = 'sh-tag'; d.textContent = t; d.style.background = c; stage.appendChild(d); return d; });

  let W = 0, H = 0, dpr = 1;
  const resize = () => { dpr = Math.min(2, devicePixelRatio || 1); W = stage.clientWidth; H = stage.clientHeight; cv.width = W * dpr; cv.height = H * dpr; draw(true); };
  addEventListener('resize', resize);
  // object-fit: cover; on narrow screens the crop leans left in the opening shots, where the aircraft flies
  const cover = (im) => {
    const s = Math.max(W / im.width, H / im.height), w = im.width * s, h = im.height * s;
    let fx = 0.5;
    if (W < H && pins) {                                                  // portrait: centre the crop on the aircraft
      const d = pins[String(Math.round(pS * (N - 1)) + 1)]?.at(-1);
      if (d) { const cx = clamp(d[0], 0.18, 0.82); fx = clamp((cx * w - W / 2) / (w - W), 0, 1); }
    }
    return {x: (W - w) * fx, y: (H - h) * 0.5, w, h};
  };
  const nearest = (i) => { for (let d = 0; d < N; d++) { if (frames[i - d]) return i - d; if (frames[i + d]) return i + d; } return -1; };
  const prog = () => { const r = hero.getBoundingClientRect(); return clamp(-r.top / (hero.offsetHeight - innerHeight)); };
  let pS = 0, lastDrawn = -1;

  function draw(force) {
    const f = pS * (N - 1), i0 = Math.floor(f), fr = f - i0;
    const a = nearest(i0), b = frames[i0 + 1] ? i0 + 1 : a;
    if (a < 0 || !W) return;
    const key = a * 1000 + Math.round(fr * 40) + (b === a ? 0 : 500);
    if (!force && key === lastDrawn) return; lastDrawn = key;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const c = cover(frames[a]);
    ctx.globalAlpha = 1; ctx.drawImage(frames[a], c.x, c.y, c.w, c.h);
    if (b !== a && a === i0 && fr > 0.02) { ctx.globalAlpha = fr; ctx.drawImage(frames[b], c.x, c.y, c.w, c.h); ctx.globalAlpha = 1; }
    // stress labels follow the rendered rings
    const P = pins && pins[String(Math.round(f) + 1)], show = ss(0.8, 0.87, pS);
    tags.forEach((t, k) => {
      if (!P || !P[k] || P[k][2] < 0) { t.style.opacity = 0; return; }
      t.style.opacity = show.toFixed(3);
      t.style.transform = `translate(${clamp(c.x + P[k][0] * c.w, 4, W - t.offsetWidth - 26).toFixed(1)}px, ${(c.y + (1 - P[k][1]) * c.h).toFixed(1)}px)`;
    });
  }

  let onScreen = true;
  new IntersectionObserver(([e]) => { const was = onScreen; onScreen = e.isIntersecting; if (onScreen && !was) requestAnimationFrame(tick); }).observe(hero);
  function tick() {
    if (!onScreen) return;
    const p = prog();
    pS = p;
    draw(false);
    lines.forEach((L) => {
      L.t(clamp((pS - L.a) / ((L.b - L.a) * 0.72)));
      L.el.style.opacity = (ss(L.a - 0.015, L.a, pS) * (1 - ss(L.b, L.b + 0.03, pS))).toFixed(3);
    });
    const cEnd = ss(0.86, 0.94, pS);
    hud.style.opacity = (ss(0.24, 0.3, pS) * (innerWidth < 900 ? 1 - cEnd : 1)).toFixed(3);   // phones: the finding card takes the HUD's place
    hudB.textContent = `${Math.round(Math.max(clamp((pS - 0.26) / 0.3) * 0.35, ss(0.55, 0.86, pS)) * 100)} %`;
    bandEls.forEach((el, i) => el.classList.toggle('on', pS > 0.26 + i * 0.035));
    const cA = ss(0.86, 0.94, pS); card.style.opacity = cA.toFixed(3); card.style.transform = `translateY(${((1 - cA) * 18).toFixed(1)}px)`;
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
