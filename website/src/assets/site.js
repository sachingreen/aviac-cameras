// Aviac website: nav, reveals, the spectral chart, the sample field (RGB / NDVI), colourway swatches, and the teardown
// side-scroll on product pages. No library: the teardown reads scroll position and drives the 3D viewer directly.
document.documentElement.classList.add('js');
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

// nav
const nav = $('.nav');
addEventListener('scroll', () => nav?.classList.toggle('scrolled', scrollY > 10), {passive: true});
$('.burger')?.addEventListener('click', () => nav.classList.toggle('open'));
$$('.nav ul a').forEach((l) => l.addEventListener('click', () => nav.classList.remove('open')));   // close after choosing

// reveals (content stays visible without JS)
const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), {threshold: 0.12});
$$('.reveal').forEach((el) => io.observe(el));

// ---------- why beyond visible light: reflectance of healthy vs stressed leaves, with the Aviac MS bands
function spectrum(cv) {
  const d = Math.min(2, devicePixelRatio || 1), r = cv.getBoundingClientRect();
  cv.width = r.width * d; cv.height = r.height * d;
  const g = cv.getContext('2d'), W = cv.width, H = cv.height, P = 30 * d;
  const X = (nm) => P + ((nm - 400) / 550) * (W - 2 * P), Y = (v) => H - P - v * (H - 2 * P);
  const leaf = (nm, s) => {             // a textbook-shaped curve: green bump, red trough, red-edge rise, NIR plateau
    const green = 0.11 * Math.exp(-(((nm - 550) / 35) ** 2));
    const edge = 1 / (1 + Math.exp(-(nm - (705 - 12 * s)) / 14));
    return 0.04 + green * (1 + s) + edge * (0.52 - 0.26 * s);
  };
  const bands = [[475, '#3a6fd8', 'B'], [560, '#2fa14b', 'G'], [668, '#d8382c', 'R'], [723, '#a3151f', 'RE'], [840, '#6b1036', 'NIR'], [890, '#43103f', 'NIR+']];
  g.font = `${11 * d}px JetBrains Mono, monospace`;
  for (const [nm, c, n] of bands) {
    g.fillStyle = c + '22'; g.fillRect(X(nm - 12), P, X(nm + 12) - X(nm - 12), H - 2 * P);
    g.fillStyle = c; g.fillText(n, X(nm) - g.measureText(n).width / 2, P - 8 * d);
  }
  for (const [s, c, w] of [[0, '#16683a', 2.6], [1, '#c4862f', 2.2]]) {
    g.strokeStyle = c; g.lineWidth = w * d; g.beginPath();
    for (let nm = 400; nm <= 950; nm += 4) { const x = X(nm), y = Y(leaf(nm, s)); nm === 400 ? g.moveTo(x, y) : g.lineTo(x, y); }
    g.stroke();
  }
  g.fillStyle = '#7c8a82';
  for (const nm of [400, 500, 600, 700, 800, 900]) g.fillText(nm, X(nm) - 10 * d, H - 8 * d);
}
$$('canvas[data-spectrum]').forEach(spectrum);

// ---------- RGB / NDVI compare: drag the divider, or use the toggle
$$('.cmpimg').forEach((box) => {
  const card = box.closest('.sample'), h = $('.handle', box);
  let cur = 0.5;
  const set = (k, anim) => {
    cur = clamp(k, 0, 1);
    box.classList.toggle('dragging', !anim);
    box.style.setProperty('--x', `${cur * 100}%`);
    h.setAttribute('aria-valuenow', Math.round(cur * 100));
    box.classList.toggle('show-flag', cur < 0.6);
    $$('.pin', box).forEach((p) => p.classList.toggle('on', parseFloat(p.style.left) > cur * 100 + 1));
    $$('.tog button', card).forEach((b) => b.classList.toggle('on', (+b.dataset.at === 1) === (cur < 0.5)));
  };
  const at = (e) => { const r = box.getBoundingClientRect(); return (e.clientX - r.left) / r.width; };
  let down = false;
  box.addEventListener('pointerdown', (e) => { down = true; box.setPointerCapture(e.pointerId); set(at(e)); });
  box.addEventListener('pointermove', (e) => down && set(at(e)));
  box.addEventListener('pointerup', () => (down = false));
  h.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') set(cur - 0.05, true); if (e.key === 'ArrowRight') set(cur + 0.05, true); });
  $$('.tog button', card).forEach((b) => b.addEventListener('click', () => set(+b.dataset.at === 1 ? 0 : 1, true)));
  set(0.5, true);
});

// ---------- colourway swatches on product pages
$$('.swatches').forEach((sw) => {
  const target = $(sw.dataset.for);
  $$('button', sw).forEach((b) => b.addEventListener('click', () => {
    $$('button', sw).forEach((x) => x.classList.toggle('on', x === b));
    $('span', sw).textContent = b.title;
    const v = window.Aviac?.viewers?.[target.id];
    v ? v.setFinish(b.dataset.finish) : (target.dataset.finish = b.dataset.finish);
    $$(`.viewer[data-follow="${target.id}"]`).forEach((f) => window.Aviac?.viewers?.[f.id]?.setFinish(b.dataset.finish));
  }));
});

// ---------- teardown: vertical scroll -> horizontal track; each stage separates the parts and isolates one group
const td = $('.td');
if (td) {
  const track = $('.track', td), cards = $$('.card', td), bars = $$('.prog i', td), label = $('.prog span', td), vid = $('.viewer', td).id;
  const stages = cards.map((c) => c.dataset.group || null);
  const views = cards.map((c) => (c.dataset.view || '0.6,0.2,3.2').split(',').map(Number));
  const mobile = () => false;                           // one behaviour everywhere: scrolling drives the stages
  let last = -1;
  const apply = (i) => {
    const v = window.Aviac?.viewers?.[vid];
    if (!v) return;
    v.driven = true;
    const end = i === cards.length - 1;
    v.explode(i === 0 || end ? 0 : 1);
    const [az, el, d] = views[i];
    v.view(az, el, d);
    v.focus(i === 0 || end ? null : stages[i]);
  };
  const tick = () => {
    if (mobile()) return;
    const r = td.getBoundingClientRect(), span = td.offsetHeight - innerHeight;
    const p = clamp(-r.top / span, 0, 1);
    const maxShift = track.scrollWidth - innerWidth + 80;
    track.style.transform = `translateX(${-p * Math.max(0, maxShift)}px)`;
    const i = clamp(Math.round(p * (cards.length - 1)), 0, cards.length - 1);
    if (i !== last) {
      last = i;
      cards.forEach((c, j) => c.classList.toggle('on', j === i));
      bars.forEach((b, j) => b.classList.toggle('on', j <= i));
      label.textContent = `${String(i + 1)} / ${cards.length}`;
    }
    apply(i);
  };
  addEventListener('scroll', tick, {passive: true});
  addEventListener('resize', tick);
  setInterval(tick, 400);                               // also picks up the viewer once it has loaded
  // mobile: swipe the cards, the visible one drives the model
  const tio = new IntersectionObserver((es) => es.forEach((e) => {
    if (!mobile() || !e.isIntersecting) return;
    const i = cards.indexOf(e.target);
    cards.forEach((c, j) => c.classList.toggle('on', j === i));
    bars.forEach((b, j) => b.classList.toggle('on', j <= i));
    label.textContent = `${i + 1} / ${cards.length}`;
    apply(i);
  }), {root: track, threshold: 0.6});
  cards.forEach((c) => tio.observe(c));
  // keyboard: arrows step through the stages when the teardown is in view
  addEventListener('keydown', (e) => {
    if (mobile() || !['ArrowRight', 'ArrowLeft'].includes(e.key)) return;
    const r = td.getBoundingClientRect();
    if (r.top > 0 || r.bottom < innerHeight) return;
    const span = td.offsetHeight - innerHeight, step = span / (cards.length - 1);
    scrollTo({top: scrollY + (e.key === 'ArrowRight' ? step : -step), behavior: 'smooth'});
    e.preventDefault();
  });
}

// ---------- pilot request: sent to info@aviac.in through FormSubmit (a static site has no server of its own);
// if that service cannot be reached, the visitor's mail app opens with everything filled in instead
$$('form[data-mailto]').forEach((f) => f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const v = (n) => f.elements[n]?.value?.trim() || '';
  if (v('_honey')) return;                                  // bots fill the hidden field
  const msg = $('.sent', f), btn = $('button[type=submit]', f);
  const subject = 'Pilot request: ' + (v('org') || v('name'));
  btn.disabled = true; btn.style.opacity = 0.6;
  try {
    const r = await fetch(`https://formsubmit.co/ajax/${f.dataset.mailto}`, {method: 'POST', headers: {'Content-Type': 'application/json', Accept: 'application/json'},
      body: JSON.stringify({_subject: subject, _template: 'table', name: v('name'), email: v('email'), company: v('org'), size: v('acres'), interested_in: v('interest'), message: v('message')})});
    const j = await r.json().catch(() => ({}));
    if (!r.ok || String(j.success) !== 'true') throw new Error('send failed');
    msg.textContent = `Thank you, ${v('name').split(' ')[0] || 'we have it'}. Your request is with us at ${f.dataset.mailto}; we will reply within two working days.`;
    f.reset();
  } catch (err) {
    const body = `${v('message')}\n\n${v('name')} · ${v('org')}\n${v('email')}\nSize: ${v('acres')}\nInterested in: ${v('interest')}`;
    location.href = `mailto:${f.dataset.mailto}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    msg.textContent = `Your mail app should open with the request ready. If it does not, write to ${f.dataset.mailto}.`;
  }
  msg.hidden = false; btn.disabled = false; btn.style.opacity = '';
}));

// ---------- home: solutions explorer, auto-advancing until someone picks a market
$$('.explorer').forEach((ex) => {
  const tabs = $$('.xt', ex), panes = $$('.xp', ex), bar = $('.xbar i', ex);
  let i = 0, t0 = performance.now(), auto = true, seen = false;
  const go = (k) => { i = k; tabs.forEach((t, j) => { t.classList.toggle('on', j === k); t.setAttribute('aria-selected', j === k); }); panes.forEach((p, j) => p.classList.toggle('on', j === k)); t0 = performance.now(); };
  tabs.forEach((t, k) => { t.addEventListener('click', () => { auto = false; go(k); bar.style.width = '0'; }); t.addEventListener('mouseenter', () => { if (matchMedia('(hover:hover)').matches) { auto = false; go(k); bar.style.width = '0'; } }); });
  new IntersectionObserver((es) => { seen = es[0].isIntersecting; t0 = performance.now(); }).observe(ex);
  const tick = (now) => { if (auto && seen) { const k = (now - t0) / 6000; bar.style.width = `${Math.min(1, k) * 100}%`; if (k >= 1) go((i + 1) % panes.length); } requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
});

// ---------- films: the small file on phones, loaded when near the screen, paused when off it
$$('video[data-src]').forEach((v) => {
  let loaded = false;
  new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) {
      if (!loaded) { v.src = innerWidth < 760 && v.dataset.sm ? v.dataset.sm : v.dataset.src; loaded = true; }
      v.play().catch(() => {});
    } else if (loaded) v.pause();
  }), {rootMargin: '200px'}).observe(v);
});

// ---------- scroll: progress line, staggered reveals inside groups, a gentle parallax on the big photos
(() => {
  const bar = $('.sprog');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  $$('.systems,.minis,.segs,.steps,.people,.partners,.stats,.facts,.bstats,.dgrid').forEach((g) => [...g.children].forEach((c, i) => {
    c.style.setProperty('--d', `${Math.min(i, 6) * 0.08}s`);
    if (!c.classList.contains('reveal') && !g.classList.contains('reveal')) { c.classList.add('reveal'); io.observe(c); }
  }));
  const par = reduce ? [] : $$('.band>img,.hero .pic img,.phero .pic img');
  let ticking = false;
  const onScroll = () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      const h = document.documentElement.scrollHeight - innerHeight;
      bar?.style.setProperty('--p', h > 0 ? (scrollY / h).toFixed(4) : 0);
      for (const im of par) {
        const r = im.parentElement.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) continue;
        const k = (r.top + r.height / 2 - innerHeight / 2) / innerHeight;
        im.style.transform = `translateY(${(k * -28).toFixed(1)}px) scale(1.06)`;
      }
      ticking = false;
    });
  };
  addEventListener('scroll', onScroll, {passive: true}); onScroll();
})();

// ---------- shared spectrum chart: 0 to 2500 nm, the same reference spectra on every page; each page overlays where its
// camera works. MS adds a zoom on its six filters, Duos and TH plot the Mira220 QE on a right axis, TH extends to LWIR.
(() => {
  const g2 = (nm, c, fw) => Math.exp(-4 * Math.LN2 * ((nm - c) / fw) ** 2);
  const veg = (nm, s = 0) => {                           // vegetation reflectance; s = stress
    const vis = 0.04 + (0.07 + 0.05 * s) * g2(nm, 550, 75) + 0.05 * s * g2(nm, 650, 60);
    let r = vis + (0.43 - 0.17 * s) / (1 + Math.exp(-(nm - (712 - 12 * s)) / 13));
    if (nm > 1000) r -= (nm - 1000) * 0.00004 + 0.03 * g2(nm, 1200, 70) + 0.22 * g2(nm, 1450, 120) + 0.33 * g2(nm, 1940, 140) - 0.06 * g2(nm, 1660, 160) - 0.05 * g2(nm, 2220, 160);
    return Math.max(0.02, r);
  };
  const soil = (nm) => 0.11 + 0.1 * Math.min(1, (nm - 350) / 1100) + 0.06 * Math.max(0, (nm - 1450) / 1050) - 0.035 * g2(nm, 1420, 80) - 0.07 * g2(nm, 1920, 110) - 0.03 * g2(nm, 2200, 60);
  const water = (nm) => Math.max(0.005, 0.07 * Math.exp(-(nm - 400) / 140));
  const mica = (nm) => 0.45 - 0.08 * g2(nm, 1410, 40) - 0.05 * g2(nm, 1910, 50) - 0.2 * g2(nm, 2200, 28) - 0.07 * g2(nm, 2350, 40);
  const QE = [[300, .57], [320, .63], [350, .63], [380, .70], [400, .85], [420, .89], [450, .90], [500, .94], [550, .94], [600, .90], [650, .86],
              [700, .78], [750, .70], [800, .62], [850, .55], [900, .44], [940, .36], [960, .31], [1000, .20], [1050, .08], [1100, .01]];   // Mira220, typical
  const qe = (nm) => { if (nm < 300 || nm >= 1100) return 0; let i = 1; while (QE[i][0] < nm) i++; const [a, va] = QE[i - 1], [b, vb] = QE[i]; return va + (vb - va) * (nm - a) / (b - a); };
  const MSB = [[475, 32, '#3a6fd8', 'Blue'], [560, 27, '#2fa14b', 'Green'], [668, 16, '#d8382c', 'Red'], [723, 12, '#a3151f', 'Red edge'], [840, 40, '#7a2f6b', 'NIR'], [890, 30, '#43103f', 'NIR+']];
  const COL = {veg: '#2a7f8f', vegS: '#c4862f', soil: '#d99a2b', water: '#7fb3d5', mica: '#17324d', qe: '#2f6f4e'};
  const CFG = {
    ms: {win: [[455, 910, 'MS · six bands']], filters: MSB, zoom: [430, 940], stress: true},
    duos: {win: [[400, 1000, 'Duos · Mira220']], qe: true},
    th: {win: [[400, 940, 'NIR module · 400–940 nm']], qe: true, lwir: [8000, 14000]},
    sw: {win: [[900, 1700, 'SW · InGaAs 900–1700 nm']], mica: true},
    construction: {win: [[400, 700, 'Colour map'], [700, 1000, 'Duos NIR']], qe: true},
  };
  const WIN = '#2f6f4e';
  function draw(cv) {
    const key = cv.dataset.band, C = CFG[key];
    const d = Math.min(2, devicePixelRatio || 1), cssW = cv.getBoundingClientRect().width, small = cssW < 560;
    const cssH = (C.zoom ? (small ? 470 : 470) : (small ? 300 : 330));
    cv.style.height = cssH + 'px'; cv.width = cssW * d; cv.height = cssH * d;
    const g = cv.getContext('2d'), Wd = cv.width;
    const fs = (small ? 9.5 : 11) * d, font = (w = 500) => `${w} ${fs}px Inter, system-ui, sans-serif`;
    g.clearRect(0, 0, Wd, cv.height);
    const L = (small ? 34 : 50) * d, Rr = (C.qe ? (small ? 34 : 46) : (small ? 10 : 18)) * d;
    const text = (t, x, y, col = '#6b7a72', align = 'left', w = 500) => { g.font = font(w); g.fillStyle = col; g.textAlign = align; g.fillText(t, x, y); g.textAlign = 'left'; };
    // a plot box: x range [a, b], y reflectance 0..ymax
    const plot = (x0, x1, top, bot, a, b, ymax, opt = {}) => {
      const X = (nm) => x0 + ((nm - a) / (b - a)) * (x1 - x0), Y = (v) => bot - (v / ymax) * (bot - top);
      // spectral regions as soft blocks with labels on top, shown only when they fit
      if (!opt.lwir) for (const [ra, rb, n] of [[0, 400, 'UV'], [400, 1000, 'VNIR'], [1000, 2500, 'SWIR']]) {
        const l = X(Math.max(ra, a)), r = X(Math.min(rb, b)); if (r <= l) continue;
        if (n === 'VNIR') { g.fillStyle = '#eef2f4'; g.fillRect(l, top, r - l, bot - top); }
        g.font = font(); if (g.measureText(n).width + 10 * d < r - l && !opt.zoom) text(n, (l + r) / 2, top + 14 * d, '#8a979e', 'center');
      } else { g.fillStyle = '#fbf1ea'; g.fillRect(x0, top, x1 - x0, bot - top); text('LWIR', (x0 + x1) / 2, top + 14 * d, '#a4704e', 'center'); }
      // gridlines and axes
      g.strokeStyle = '#e3e8e5'; g.lineWidth = d;
      const yt = ymax > 0.5 ? [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6] : [0, 0.25, 0.5, 0.75, 1];
      if (!opt.lwir) for (const v of yt) { if (v > ymax) continue; g.beginPath(); g.moveTo(x0, Y(v)); g.lineTo(x1, Y(v)); g.stroke(); if (opt.yaxis) text(v.toFixed(1), x0 - 6 * d, Y(v) + 3.5 * d, '#6b7a72', 'right'); }
      g.strokeStyle = '#2b3a33'; g.beginPath(); g.moveTo(x0, top); g.lineTo(x0, bot); g.lineTo(x1, bot); g.stroke();
      const step = opt.lwir ? 2000 : (b - a > 1500 ? (small ? 500 : 250) : 100);
      for (let nm = Math.ceil(a / step) * step; nm <= b; nm += step) { const x = X(nm); g.fillStyle = '#2b3a33'; g.fillRect(x, bot, d, 4 * d);
        text(opt.lwir ? String(nm / 1000) : String(nm), x, bot + 15 * d, '#3b4a43', 'center'); }
      // the camera's window(s)
      let lastEnd = -1e9, row = 0;
      if (!opt.lwir) for (const [wa, wb, n] of C.win) {
        const l = X(Math.max(wa, a)), r = X(Math.min(wb, b)); if (r <= l) continue;
        g.fillStyle = 'rgba(47,111,78,.13)'; g.fillRect(l, top, r - l, bot - top); g.fillStyle = WIN; g.fillRect(l, top, r - l, 3 * d);
        g.font = font(600); const tw = g.measureText(n).width, tx = Math.min(Math.max(l + 3 * d, x0 + 4 * d), x1 - tw - 4 * d);
        row = tx < lastEnd + 6 * d ? row + 1 : 0; lastEnd = tx + tw;
        if (!opt.zoom) text(n, tx, top + (30 + row * 13) * d, WIN, 'left', 600);
      } else { const l = X(C.lwir[0]), r = X(C.lwir[1]); g.fillStyle = 'rgba(194,65,12,.18)'; g.fillRect(l, top, r - l, bot - top); g.fillStyle = '#c2410c'; g.fillRect(l, top, r - l, 3 * d);
        text(small ? '8–14 µm' : 'Thermal · 8–14 µm', (l + r) / 2, top + 30 * d, '#c2410c', 'center', 600); }
      // MS filters
      if (C.filters && !opt.lwir) for (const [c0, fw, col, n] of C.filters) {
        if (c0 < a || c0 > b) continue;
        g.beginPath(); g.moveTo(X(c0 - 2 * fw), bot);
        for (let nm = c0 - 2 * fw; nm <= c0 + 2 * fw; nm += 1) g.lineTo(X(nm), Y(ymax * 0.86 * Math.pow(g2(nm, c0, fw), 0.55)));
        g.lineTo(X(c0 + 2 * fw), bot); g.closePath(); g.fillStyle = col + (opt.zoom ? '3a' : '60'); g.fill();
        if (opt.zoom) { g.strokeStyle = col; g.lineWidth = 1.4 * d; g.stroke(); }
      }
      if (opt.zoom && C.filters) {                       // peak labels, staggered so neighbours never collide
        C.filters.forEach(([c0, , col, n], i) => { const yy = top + (i % 2 ? 28 : 14) * d; text(`${c0}`, X(c0), yy, col, 'center', 600); });
      }
      // feature markers
      let lastLab = -1e9;
      if (!opt.lwir && !opt.zoom) for (const [nm, n] of [[700, 'red edge'], [1450, 'water'], [1940, 'water'], [2200, 'Al-OH']]) {
        if (nm < a || nm > b) continue; const x = X(nm); g.strokeStyle = '#b9c3bd'; g.setLineDash([2 * d, 3 * d]); g.beginPath(); g.moveTo(x, top + 36 * d); g.lineTo(x, bot); g.stroke(); g.setLineDash([]);
        g.font = font(); const tw = g.measureText(n).width; if (x + 3 * d > lastLab + 6 * d && x + 3 * d + tw < x1) { text(n, x + 3 * d, top + (46 + (C.win.length > 1 ? 10 : 0)) * d, '#8a979e', 'left', 500); lastLab = x + 3 * d + tw; }
      }
      // reference spectra
      if (!opt.lwir) {
        const curves = [[veg, COL.veg, 2.2], [soil, COL.soil, 1.8], [water, COL.water, 1.8]];
        if (C.mica) curves.push([mica, COL.mica, 1.8]);
        if (opt.zoom && C.stress) curves.splice(1, 2, [(nm) => veg(nm, 1), COL.vegS, 2.2]);
        for (const [f, col, w] of curves) { g.strokeStyle = col; g.lineWidth = w * d; g.beginPath(); let first = true;
          for (let nm = Math.max(350, a); nm <= b; nm += 2) { const x = X(nm), y = Y(Math.min(ymax, f(nm))); first ? g.moveTo(x, y) : g.lineTo(x, y); first = false; } g.stroke(); }
      }
      // Mira220 QE on a right axis
      if (C.qe && !opt.lwir) {
        const Yq = (v) => bot - v * (bot - top - 40 * d);
        g.beginPath(); g.moveTo(X(300), bot); for (let nm = 300; nm <= 1100; nm += 4) g.lineTo(X(nm), Yq(qe(nm))); g.lineTo(X(1100), bot); g.closePath();
        g.fillStyle = 'rgba(47,111,78,.10)'; g.fill();
        g.strokeStyle = COL.qe; g.lineWidth = 2 * d; g.setLineDash([6 * d, 3 * d]); g.beginPath();
        for (let nm = 300; nm <= 1100; nm += 4) { const x = X(nm), y = Yq(qe(nm)); nm === 300 ? g.moveTo(x, y) : g.lineTo(x, y); } g.stroke(); g.setLineDash([]);
        for (const v of [0, 0.5, 1]) text(`${v * 100}%`, x1 + 5 * d, Yq(v) + 3.5 * d, COL.qe);
        g.strokeStyle = COL.qe; g.lineWidth = d; g.beginPath(); g.moveTo(x1, top + 40 * d); g.lineTo(x1, bot); g.stroke();
        if (!small) for (const [nm, v] of [[550, .94], [850, .55], [940, .36]]) { const x = X(nm), y = Yq(v); g.fillStyle = COL.qe; g.beginPath(); g.arc(x, y, 3 * d, 0, 7); g.fill();
          text(`${Math.round(v * 100)}%`, x + 5 * d, y - 5 * d, COL.qe, 'left', 600); }
      }
      return X;
    };
    const top = 6 * d, H = cv.height;
    if (C.zoom) {
      const split = H * 0.46;
      const X = plot(L, Wd - Rr, top, split - 34 * d, 0, 2500, 0.7, {yaxis: true});
      text('Wavelength (nm)', (L + Wd - Rr) / 2, split - 6 * d, '#3b4a43', 'center');
      const [za, zb] = C.zoom; g.strokeStyle = 'rgba(47,111,78,.5)'; g.setLineDash([3 * d, 3 * d]); g.lineWidth = d;
      g.strokeRect(X(za), top, X(zb) - X(za), split - 34 * d - top); g.setLineDash([]);
      g.beginPath(); g.moveTo(X(za), split - 34 * d); g.lineTo(L, split + 8 * d); g.moveTo(X(zb), split - 34 * d); g.lineTo(Wd - Rr, split + 8 * d); g.stroke();
      plot(L, Wd - Rr, split + 10 * d, H - 34 * d, za, zb, 0.7, {zoom: true, yaxis: true});
      text('Zoom: the six MS filters over a healthy and a stressed leaf', (L + Wd - Rr) / 2, H - 6 * d, '#3b4a43', 'center');
    } else if (C.lwir) {
      const lw = Math.min(small ? 80 * d : 200 * d, Wd * 0.24), gap = (C.qe ? (small ? 40 : 52) : (small ? 16 : 26)) * d, x1 = Wd - (small ? 8 : 14) * d - lw - gap;
      plot(L, x1, top, H - 34 * d, 0, 2500, 0.7, {yaxis: true});
      plot(x1 + gap, Wd - (small ? 8 : 14) * d, top, H - 34 * d, 7000, 15000, 0.7, {lwir: true});
      g.strokeStyle = '#2b3a33'; g.lineWidth = 1.4 * d; for (const dx of [-3, 3]) { g.beginPath(); g.moveTo(x1 + gap / 2 + dx * d - 4 * d, H - 28 * d); g.lineTo(x1 + gap / 2 + dx * d + 4 * d, H - 40 * d); g.stroke(); }
      text('Wavelength (nm · µm)', (L + Wd) / 2, H - 6 * d, '#3b4a43', 'center');
    } else {
      plot(L, Wd - Rr, top, H - 34 * d, 0, 2500, 0.7, {yaxis: true});
      text('Wavelength (nm)', (L + Wd - Rr) / 2, H - 6 * d, '#3b4a43', 'center');
    }
    g.save(); g.translate(11 * d, H * (C.zoom ? 0.24 : 0.45)); g.rotate(-Math.PI / 2); text('Reflectance', 0, 0, '#3b4a43', 'center'); g.restore();
    const lg = document.querySelector(`[data-legend="${key}"]`);
    if (lg) {
      const items = [[COL.veg, 'Vegetation'], ...(C.stress ? [[COL.vegS, 'Stressed vegetation']] : []), [COL.soil, 'Soil'], [COL.water, 'Water']];
      if (C.mica) items.push([COL.mica, 'White mica (Al-OH)']);
      if (C.qe) items.push([COL.qe, 'Mira220 QE (right axis)', true]);
      items.push(['rgba(47,111,78,.35)', 'Where the camera works', false, true]);
      if (C.lwir) items.push(['rgba(194,65,12,.45)', 'Thermal band', false, true]);
      lg.innerHTML = items.map(([c, n, dash, block]) => `<span><i class="${block ? 'blk' : dash ? 'dsh' : ''}" style="--c:${c}"></i>${n}</span>`).join('');
    }
  }
  const all = $$('canvas[data-band]');
  const run = () => all.forEach(draw);
  (document.fonts?.ready || Promise.resolve()).then(run); run();
  let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
})();
