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

// ---------- sample field: the same plots in true colour and in NDVI
const h2 = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
const vn = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
  return (h2(xi, yi) * (1 - u) + h2(xi + 1, yi) * u) * (1 - w) + (h2(xi, yi + 1) * (1 - u) + h2(xi + 1, yi + 1) * u) * w; };
const STOPS = [[0.1, [150, 92, 60]], [0.35, [214, 170, 70]], [0.55, [196, 205, 90]], [0.72, [96, 170, 78]], [0.92, [22, 104, 58]]];
const ramp = (n) => { for (let i = 0; i < 4; i++) { const [a, ca] = STOPS[i], [b, cb] = STOPS[i + 1]; if (n <= b) { const k = Math.max(0, (n - a) / (b - a)); return ca.map((c, j) => c + (cb[j] - c) * k); } } return STOPS[4][1]; };
function field(cv) {
  const W = (cv.width = 480), H = (cv.height = 360), g = cv.getContext('2d');
  const plots = [[0, 0, 210, 150], [214, 0, 266, 150], [0, 154, 150, 206], [154, 154, 170, 206], [328, 154, 152, 206]];
  const n = new Float32Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let v = 0.3 + 0.6 * (vn(x / 70, y / 55) * 0.7 + vn(x / 18, y / 15) * 0.3);
    v -= 0.45 * Math.max(0, 1 - Math.hypot(x - 300, y - 250) / 55);      // a stressed patch the eye cannot see yet
    n[y * W + x] = Math.max(0.05, Math.min(0.92, v));
  }
  const draw = (mode) => {
    const img = g.createImageData(W, H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const v = n[y * W + x], o = (y * W + x) * 4;
      const inPlot = plots.some(([a, b, w, h]) => x > a + 2 && x < a + w - 2 && y > b + 2 && y < b + h - 2);
      const row = 0.9 + 0.1 * Math.sin((x + y * 0.2) * 0.9);
      let c = mode === 'ndvi' ? ramp(v) : [54 + 26 * (1 - Math.min(1, v + 0.25)), 92 + 34 * Math.min(1, v + 0.3), 44];
      if (!inPlot) c = [118, 104, 80];
      img.data[o] = c[0] * row; img.data[o + 1] = c[1] * row; img.data[o + 2] = c[2] * row; img.data[o + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    if (mode === 'ndvi') { g.strokeStyle = '#fff'; g.setLineDash([5, 4]); g.lineWidth = 2; g.beginPath(); g.arc(300, 250, 56, 0, 7); g.stroke(); g.setLineDash([]);
      g.fillStyle = 'rgba(19,32,26,.8)'; g.fillRect(320, 300, 132, 24); g.fillStyle = '#fff'; g.font = '12px JetBrains Mono, monospace'; g.fillText('Stress · 0.21 ac', 328, 316); }
  };
  draw('ndvi');
  const box = cv.closest('.sample');
  $$('.tog button', box).forEach((b) => b.addEventListener('click', () => { $$('.tog button', box).forEach((x) => x.classList.toggle('on', x === b)); draw(b.dataset.mode); }));
}
$$('canvas[data-field]').forEach(field);

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
  const mobile = () => matchMedia('(max-width:560px)').matches;
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
