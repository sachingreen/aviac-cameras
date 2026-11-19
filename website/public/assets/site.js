// Aviac website: nav, reveals, the spectral chart, the sample field (RGB / NDVI), colourway swatches, and the teardown
// side-scroll on product pages. No library: the teardown reads scroll position and drives the 3D viewer directly.
document.documentElement.classList.add('js');
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

// nav
const nav = $('.nav');
addEventListener('scroll', () => nav?.classList.toggle('scrolled', scrollY > 10), {passive: true});
$('.burger')?.addEventListener('click', () => nav.classList.toggle('open'));

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

// ---------- shared spectrum chart: 0 to 2500 nm, the same for every camera; each page highlights where its camera works.
// MS adds a zoomed panel of its six filters; Duos and TH plot the Mira220's quantum efficiency; TH extends to LWIR.
(() => {
  const g2 = (nm, c, fw) => Math.exp(-4 * Math.LN2 * ((nm - c) / fw) ** 2);
  const leaf = (nm, s = 0) => {                         // vegetation reflectance; s = stress
    const vis = 0.05 + (0.08 + 0.05 * s) * g2(nm, 550, 70) + 0.06 * s * g2(nm, 650, 60);
    const edge = 1 / (1 + Math.exp(-(nm - (712 - 12 * s)) / 14));
    let r = vis + edge * (0.47 - 0.2 * s);
    if (nm > 1000) r -= (nm - 1000) * 0.00011 + 0.05 * g2(nm, 1200, 70) + 0.17 * g2(nm, 1450, 120) + 0.26 * g2(nm, 1940, 150);
    return Math.max(0.02, r);
  };
  const water = (nm) => 0.04 + 0.42 * g2(nm, 1450, 100) + 0.6 * g2(nm, 1940, 120) + 0.08 * g2(nm, 1200, 70) + (nm > 2200 ? (nm - 2200) * 0.0012 : 0);
  const QE = [[300, 0.57], [320, 0.63], [350, 0.63], [380, 0.70], [400, 0.85], [420, 0.89], [450, 0.90], [500, 0.94], [550, 0.94], [600, 0.90], [650, 0.86],
              [700, 0.78], [750, 0.70], [800, 0.62], [850, 0.55], [900, 0.44], [940, 0.36], [960, 0.31], [1000, 0.20], [1050, 0.08], [1100, 0.01]];   // Mira220, typical (datasheet)
  const qe = (nm) => { if (nm < QE[0][0] || nm >= QE[QE.length - 1][0]) return 0; let i = 1; while (QE[i][0] < nm) i++;
    const [a, va] = QE[i - 1], [b, vb] = QE[i]; return va + (vb - va) * (nm - a) / (b - a); };
  const MSB = [[475, 32, '#3a6fd8', 'Blue 475'], [560, 27, '#2fa14b', 'Green 560'], [668, 16, '#d8382c', 'Red 668'], [723, 12, '#a3151f', 'Red edge 723'],
               [840, 40, '#6b1036', 'NIR 840'], [890, 30, '#43103f', 'NIR+ 890']];
  const CFG = {
    ms: {zoom: [420, 950], filters: MSB, curve: 'leaf', legend: [...MSB.map((b) => [b[2], b[3]]), ['#16683a', 'Healthy leaf'], ['#c4862f', 'Stressed leaf']]},
    duos: {qe: [300, 1100], curve: 'leaf', legend: [['#2f6f4e', 'Mira220 quantum efficiency'], ['#16683a', 'Leaf reflectance']]},
    th: {qe: [400, 940], pass: [400, 940, '#7a2f6b'], lwir: [8000, 14000, '#c2410c'],
         legend: [['#7a2f6b', 'NIR module: Mira220 behind a 400–940 nm filter'], ['#2f6f4e', 'Mira220 quantum efficiency'], ['#c2410c', 'Thermal core, 8–14 µm']]},
    sw: {pass: [900, 1700, '#3a6ea5'], curve: 'water', legend: [['#3a6ea5', 'InGaAs SWIR, 900–1700 nm'], ['#2b5a8a', 'Water absorption']]},
    construction: {pass: [400, 700, '#2f6f4e'], qe: [400, 1100], legend: [['#2f6f4e', 'Colour map, 400–700 nm'], ['#7c8a82', 'Duos, Mira220 response to 1000 nm']]},
  };
  function draw(cv) {
    const key = cv.dataset.band, C = CFG[key];
    const d = Math.min(2, devicePixelRatio || 1), rr = cv.getBoundingClientRect();
    if (C.zoom) cv.style.height = innerWidth < 760 ? '360px' : '420px';
    cv.width = rr.width * d; cv.height = cv.getBoundingClientRect().height * d;
    const g = cv.getContext('2d'), Wd = cv.width, H = cv.height, mono = `${10.5 * d}px JetBrains Mono, monospace`;
    g.clearRect(0, 0, Wd, H); g.font = mono;
    const panel = (x0, x1, top, bot, a, b, unit, opt = {}) => {
      const X = (nm) => x0 + ((nm - a) / (b - a)) * (x1 - x0), Y = (v) => bot - v * (bot - top);
      // regions
      if (!opt.lwir) [[0, 400, 'UV'], [400, 700, 'Visible'], [700, 1000, 'NIR'], [1000, 2500, 'SWIR']].forEach(([ra, rb, n], i) => {
        const L = Math.max(ra, a), R = Math.min(rb, b); if (R <= L) return;
        g.fillStyle = i % 2 ? 'rgba(47,111,78,.035)' : 'rgba(47,111,78,.07)'; g.fillRect(X(L), top, X(R) - X(L), bot - top);
        g.fillStyle = '#7c8a82'; g.fillText(n, X(L) + 6 * d, top + 14 * d); });
      else { g.fillStyle = 'rgba(194,65,12,.05)'; g.fillRect(x0, top, x1 - x0, bot - top); g.fillStyle = '#7c8a82'; g.fillText('LWIR', x0 + 6 * d, top + 14 * d); }
      // visible strip
      if (!opt.lwir && a < 700) { const L = X(Math.max(400, a)), R = X(Math.min(700, b)); const rb = g.createLinearGradient(X(400), 0, X(700), 0);
        [['#6a3fd0', 0], ['#3a6fd8', .2], ['#2fa14b', .45], ['#e8d43a', .65], ['#e98a2c', .8], ['#d8382c', 1]].forEach(([c, o]) => rb.addColorStop(o, c));
        g.fillStyle = rb; g.fillRect(L, bot + 2 * d, R - L, 5 * d); }
      // passbands
      if (C.pass && !opt.lwir) { const [pa, pb, c] = C.pass; g.fillStyle = c + '30'; g.fillRect(X(pa), top, X(pb) - X(pa), bot - top); g.fillStyle = c; g.fillRect(X(pa), top, X(pb) - X(pa), 3 * d); }
      if (opt.lwir) { const [la, lb, c] = C.lwir; g.fillStyle = c + '40'; g.fillRect(X(la), top, X(lb) - X(la), bot - top); g.fillStyle = c; g.fillRect(X(la), top, X(lb) - X(la), 3 * d); }
      // MS filters: real band-pass shapes
      if (C.filters && !opt.lwir) for (const [c0, fw, col, n] of C.filters) {
        g.beginPath(); g.moveTo(X(c0 - 2 * fw), bot);
        for (let nm = c0 - 2 * fw; nm <= c0 + 2 * fw; nm += 1) g.lineTo(X(nm), Y(0.88 * g2(nm, c0, fw) ** 0.6 * (Math.abs(nm - c0) < fw * 1.4 ? 1 : 0.2)));
        g.lineTo(X(c0 + 2 * fw), bot); g.closePath(); g.fillStyle = col + (opt.zoom ? '55' : '88'); g.fill();
        if (opt.zoom) { g.strokeStyle = col; g.lineWidth = 1.6 * d; g.stroke(); g.fillStyle = col; g.fillText(String(c0), X(c0) - 11 * d, Y(0.9) - 6 * d); }
      }
      // Mira220 quantum efficiency
      if (C.qe && !opt.lwir) {
        const [qa, qb] = C.qe;
        g.beginPath(); g.moveTo(X(qa), bot); for (let nm = qa; nm <= qb; nm += 4) g.lineTo(X(nm), Y(qe(nm))); g.lineTo(X(qb), bot); g.closePath();
        g.fillStyle = key === 'construction' ? 'rgba(124,138,130,.18)' : 'rgba(47,111,78,.16)'; g.fill();
        g.strokeStyle = key === 'construction' ? '#7c8a82' : '#2f6f4e'; g.lineWidth = 2 * d; g.beginPath();
        for (let nm = 300; nm <= 1100; nm += 4) { const x = X(nm), y = Y(qe(nm)); nm === 300 ? g.moveTo(x, y) : g.lineTo(x, y); } g.stroke();
        if (key !== 'construction') for (const [nm, v] of [[550, 0.94], [850, 0.55], [940, 0.36]]) { const x = X(nm), y = Y(v); g.fillStyle = '#0f3d27'; g.beginPath(); g.arc(x, y, 3.5 * d, 0, 7); g.fill();
          g.font = `600 ${10.5 * d}px JetBrains Mono, monospace`; g.fillText(`QE ${Math.round(v * 100)} % at ${nm} nm`, x + 8 * d, nm === 550 ? y + 16 * d : y - 6 * d); g.font = mono; }
      }
      // reference curves
      if (C.curve && !opt.lwir) {
        const draws = C.curve === 'leaf' ? (opt.zoom ? [[0, '#16683a'], [1, '#c4862f']] : [[0, '#16683a']]) : [[0, '#2b5a8a']];
        for (const [st, col] of draws) { const f = C.curve === 'leaf' ? (nm) => leaf(nm, st) : water;
          g.strokeStyle = col; g.lineWidth = 2.2 * d; g.beginPath(); let first = true;
          for (let nm = Math.max(350, a); nm <= b; nm += 3) { const x = X(nm), y = Y(f(nm)); first ? g.moveTo(x, y) : g.lineTo(x, y); first = false; } g.stroke(); }
        if (C.curve === 'water') for (const nm of [1450, 1940]) { g.fillStyle = '#2b5a8a'; g.fillText(`water ${nm}`, X(nm) - 30 * d, Y(water(nm)) - 8 * d); }
      }
      // axes
      g.strokeStyle = '#c9d2cc'; g.lineWidth = d; g.beginPath(); g.moveTo(x0, bot); g.lineTo(x1, bot); g.stroke();
      g.fillStyle = '#7c8a82';
      const step = opt.lwir ? 2000 : (b - a > 1500 ? 500 : 100);
      for (let nm = Math.ceil(a / step) * step; nm <= b; nm += step) { const x = X(nm); g.fillRect(x, bot, d, 5 * d);
        const t = opt.lwir ? String(nm / 1000) : String(nm); g.fillText(t, x - g.measureText(t).width / 2, bot + 20 * d); }
      g.fillText(unit, x1 - 16 * d, bot + 32 * d);
      if (opt.yaxis) for (const v of [0, 0.5, 1]) { g.fillText(`${v * 100}%`, 2 * d, Y(v) + 4 * d); g.fillStyle = 'rgba(124,138,130,.25)'; g.fillRect(x0, Y(v), x1 - x0, d * (v ? 0.6 : 0)); g.fillStyle = '#7c8a82'; }
      return X;
    };
    const P = 40 * d, R = 14 * d;
    if (C.zoom) {                                       // overview on top, the six filters zoomed below
      const mid = H * 0.38;
      const X = panel(P, Wd - R, 16 * d, mid - 34 * d, 0, 2500, 'nm', {yaxis: false});
      const [za, zb] = C.zoom;
      g.strokeStyle = '#2f6f4e'; g.setLineDash([4 * d, 4 * d]); g.lineWidth = d; g.strokeRect(X(za), 16 * d, X(zb) - X(za), mid - 50 * d); g.setLineDash([]);
      g.beginPath(); g.moveTo(X(za), mid - 34 * d); g.lineTo(P, mid + 2 * d); g.moveTo(X(zb), mid - 34 * d); g.lineTo(Wd - R, mid + 2 * d); g.strokeStyle = 'rgba(47,111,78,.35)'; g.stroke();
      panel(P, Wd - R, mid + 8 * d, H - 38 * d, za, zb, 'nm', {zoom: true, yaxis: true});
    } else if (C.lwir) {
      const lw = Math.min(220 * d, Wd * 0.26), gap = 26 * d, x1 = Wd - R - lw - gap;
      panel(P, x1, 16 * d, H - 40 * d, 0, 2500, 'nm', {yaxis: true});
      g.strokeStyle = '#7c8a82'; g.lineWidth = 1.5 * d;
      for (const dx of [-4, 4]) { g.beginPath(); g.moveTo(x1 + gap / 2 + dx * d - 4 * d, H - 34 * d); g.lineTo(x1 + gap / 2 + dx * d + 4 * d, H - 46 * d); g.stroke(); }
      panel(x1 + gap, Wd - R, 16 * d, H - 40 * d, 7000, 15000, 'µm', {lwir: true});
    } else panel(P, Wd - R, 16 * d, H - 40 * d, 0, 2500, 'nm', {yaxis: true});
    const lg = document.querySelector(`[data-legend="${key}"]`);
    if (lg && !lg.childElementCount) lg.innerHTML = C.legend.map(([c, n]) => `<span><i style="background:${c}"></i>${n}</span>`).join('');
  }
  const all = $$('canvas[data-band]');
  all.forEach(draw);
  let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => all.forEach(draw), 150); });
})();
