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
// TH adds a broken-axis panel for long-wave infrared (8 to 14 um).
(() => {
  const BANDS = {
    ms: {bands: [[463, 487, '#3a6fd8', 'Blue 475'], [548, 572, '#2fa14b', 'Green 560'], [658, 678, '#d8382c', 'Red 668'], [718, 728, '#a3151f', 'Red edge 723'],
                 [830, 850, '#6b1036', 'NIR 840'], [880, 900, '#43103f', 'NIR+ 890']], curve: 'leaf'},
    duos: {bands: [[400, 1000, '#2f6f4e', 'Mira220, 400–1000 nm']], resp: true, curve: 'leaf'},
    th: {bands: [[400, 940, '#7a2f6b', 'NIR module, 400–940 nm']], lwir: [8000, 14000, '#c2410c', 'Thermal, 8–14 µm']},
    sw: {bands: [[900, 1700, '#3a6ea5', 'InGaAs SWIR, 900–1700 nm']], curve: 'water'},
    construction: {bands: [[400, 700, '#2f6f4e', 'Colour map, 400–700 nm'], [700, 1000, '#7c8a82', 'Duos NIR, to 1000 nm']]},
  };
  const leaf = (nm) => {                                   // a healthy leaf: green bump, red trough, red edge, NIR plateau, water dips in SWIR
    const vis = 0.05 + 0.08 * Math.exp(-(((nm - 550) / 40) ** 2));
    const edge = 1 / (1 + Math.exp(-(nm - 715) / 14));
    let r = vis + edge * 0.47;
    if (nm > 1000) r -= (nm - 1000) * 0.00011 + 0.05 * Math.exp(-(((nm - 1200) / 45) ** 2)) + 0.17 * Math.exp(-(((nm - 1450) / 70) ** 2)) + 0.26 * Math.exp(-(((nm - 1940) / 90) ** 2));
    return Math.max(0.02, r);
  };
  const water = (nm) => 0.04 + 0.42 * Math.exp(-(((nm - 1450) / 60) ** 2)) + 0.6 * Math.exp(-(((nm - 1940) / 70) ** 2)) + 0.08 * Math.exp(-(((nm - 1200) / 40) ** 2)) + (nm > 2200 ? (nm - 2200) * 0.0012 : 0);
  function draw(cv) {
    const key = cv.dataset.band, cfg = BANDS[key];
    const d = Math.min(2, devicePixelRatio || 1), r = cv.getBoundingClientRect();
    cv.width = r.width * d; cv.height = r.height * d;
    const g = cv.getContext('2d'), Wd = cv.width, H = cv.height, P = 34 * d, top = 18 * d, bot = H - 40 * d;
    const lw = cfg.lwir ? Math.min(220 * d, Wd * 0.26) : 0, gap = cfg.lwir ? 26 * d : 0;
    const x0 = P, x1 = Wd - P - lw - gap;
    const X = (nm) => x0 + (nm / 2500) * (x1 - x0), Y = (v) => bot - v * (bot - top);
    const mono = `${10.5 * d}px JetBrains Mono, monospace`;
    g.clearRect(0, 0, Wd, H);
    // regions
    const regions = [[0, 400, 'UV'], [400, 700, 'Visible'], [700, 1000, 'NIR'], [1000, 2500, 'SWIR']];
    regions.forEach(([a, b, n], i) => { g.fillStyle = i % 2 ? 'rgba(47,111,78,.035)' : 'rgba(47,111,78,.07)'; g.fillRect(X(a), top, X(b) - X(a), bot - top);
      g.fillStyle = '#7c8a82'; g.font = mono; g.fillText(n, X(a) + 6 * d, top + 14 * d); });
    // visible rainbow strip on the axis
    const rb = g.createLinearGradient(X(400), 0, X(700), 0);
    [['#6a3fd0', 0], ['#3a6fd8', .2], ['#2fa14b', .45], ['#e8d43a', .65], ['#e98a2c', .8], ['#d8382c', 1]].forEach(([c, o]) => rb.addColorStop(o, c));
    g.fillStyle = rb; g.fillRect(X(400), bot + 2 * d, X(700) - X(400), 5 * d);
    // the camera's bands
    for (const [a, b, c] of cfg.bands) {
      if (cfg.resp) {                                      // a broad sensor response: a soft hump
        g.beginPath(); g.moveTo(X(a), bot);
        for (let nm = a; nm <= b; nm += 5) g.lineTo(X(nm), Y(0.82 * Math.exp(-(((nm - 560) / 240) ** 2)) + 0.04));
        g.lineTo(X(b), bot); g.closePath(); g.fillStyle = c + '40'; g.fill(); g.strokeStyle = c; g.lineWidth = 2 * d; g.stroke();
      } else { g.fillStyle = c + (b - a > 60 ? '33' : '55'); g.fillRect(X(a), top, Math.max(2 * d, X(b) - X(a)), bot - top);
        g.fillStyle = c; g.fillRect(X(a), top, Math.max(2 * d, X(b) - X(a)), 3 * d); }
    }
    // reference curve
    if (cfg.curve) {
      const f = cfg.curve === 'leaf' ? leaf : water;
      g.strokeStyle = cfg.curve === 'leaf' ? '#16683a' : '#2b5a8a'; g.lineWidth = 2.2 * d; g.beginPath();
      for (let nm = 350; nm <= 2500; nm += 5) { const x = X(nm), y = Y(f(nm)); nm === 350 ? g.moveTo(x, y) : g.lineTo(x, y); }
      g.stroke();
      if (cfg.curve === 'water') for (const nm of [1450, 1940]) { g.fillStyle = '#2b5a8a'; g.font = mono; g.fillText(`water ${nm}`, X(nm) - 30 * d, Y(water(nm)) - 8 * d); }
    }
    // axis
    g.strokeStyle = '#c9d2cc'; g.lineWidth = d; g.beginPath(); g.moveTo(x0, bot); g.lineTo(x1, bot); g.stroke();
    g.fillStyle = '#7c8a82'; g.font = mono;
    for (let nm = 0; nm <= 2500; nm += 500) { const x = X(nm); g.fillRect(x, bot, d, 5 * d); g.fillText(nm, x - g.measureText(String(nm)).width / 2, bot + 22 * d); }
    g.fillText('nm', x1 - 16 * d, bot + 34 * d);
    // LWIR extension panel, after a broken axis
    if (cfg.lwir) {
      const [a, b, c] = cfg.lwir, L0 = x1 + gap, L1 = Wd - P;
      const XL = (nm) => L0 + ((nm - 7000) / 8000) * (L1 - L0);
      g.strokeStyle = '#7c8a82'; g.lineWidth = 1.5 * d;
      for (const dx of [-4, 4]) { g.beginPath(); g.moveTo(x1 + gap / 2 + dx * d - 4 * d, bot + 6 * d); g.lineTo(x1 + gap / 2 + dx * d + 4 * d, bot - 6 * d); g.stroke(); }
      g.fillStyle = 'rgba(194,65,12,.05)'; g.fillRect(L0, top, L1 - L0, bot - top);
      g.fillStyle = c + '40'; g.fillRect(XL(a), top, XL(b) - XL(a), bot - top); g.fillStyle = c; g.fillRect(XL(a), top, XL(b) - XL(a), 3 * d);
      g.fillStyle = '#7c8a82'; g.fillText('LWIR', L0 + 6 * d, top + 14 * d);
      g.strokeStyle = '#c9d2cc'; g.lineWidth = d; g.beginPath(); g.moveTo(L0, bot); g.lineTo(L1, bot); g.stroke();
      for (const um of [8, 10, 12, 14]) { const x = XL(um * 1000); g.fillStyle = '#7c8a82'; g.fillRect(x, bot, d, 5 * d); g.fillText(`${um}`, x - 5 * d, bot + 22 * d); }
      g.fillText('µm', L1 - 16 * d, bot + 34 * d);
    }
    // legend
    const lg = document.querySelector(`[data-legend="${key}"]`);
    if (lg && !lg.childElementCount) {
      const items = cfg.bands.map(([, , c, n]) => [c, n]);
      if (cfg.lwir) items.push([cfg.lwir[2], cfg.lwir[3]]);
      if (cfg.curve === 'leaf') items.push(['#16683a', 'Healthy leaf reflectance']);
      if (cfg.curve === 'water') items.push(['#2b5a8a', 'Water absorption']);
      lg.innerHTML = items.map(([c, n]) => `<span><i style="background:${c}"></i>${n}</span>`).join('');
    }
  }
  const all = $$('canvas[data-band]');
  all.forEach(draw);
  let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => all.forEach(draw), 150); });
})();
