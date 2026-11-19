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

// ---------- pilot request: a static site has no server, so it opens the visitor's mail app with everything filled in
$$('form[data-mailto]').forEach((f) => f.addEventListener('submit', (e) => {
  e.preventDefault();
  const v = (n) => f.elements[n]?.value?.trim() || '';
  const body = `${v('message')}\n\n${v('name')} · ${v('org')}\n${v('email')}\nArea: ${v('acres')}\nInterested in: ${v('interest')}`;
  location.href = `mailto:${f.dataset.mailto}?subject=${encodeURIComponent('Pilot request: ' + (v('org') || v('name')))}&body=${encodeURIComponent(body)}`;
  $('.sent', f).hidden = false;
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
