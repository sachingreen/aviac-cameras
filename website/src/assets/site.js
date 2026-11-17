// Aviac / Terrain website: navigation, scroll reveals, and the field visuals drawn in code (no stock imagery).
// The maps are illustrations of the product's output, generated from noise, not customer data.

// ---------- small noise for the field maps
const h2 = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
const vn = (x, y) => {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
  return (h2(xi, yi) * (1 - u) + h2(xi + 1, yi) * u) * (1 - w) + (h2(xi, yi + 1) * (1 - u) + h2(xi + 1, yi + 1) * u) * w;
};
const ndvi = (x, y, s = 1) => Math.min(0.95, Math.max(0.05, 0.22 + 0.62 * (vn(x / (70 * s), y / (55 * s)) * 0.65 + vn(x / (22 * s) + 9, y / (18 * s) + 4) * 0.35)));
const STOPS = [[0.1, [150, 92, 60]], [0.35, [214, 170, 70]], [0.55, [196, 205, 90]], [0.72, [96, 170, 78]], [0.92, [22, 104, 58]]];
const ramp = (n) => {
  for (let i = 0; i < STOPS.length - 1; i++) {
    const [a, ca] = STOPS[i], [b, cb] = STOPS[i + 1];
    if (n <= b) { const k = Math.max(0, (n - a) / (b - a)); return ca.map((c, j) => Math.round(c + (cb[j] - c) * k)); }
  }
  return STOPS[STOPS.length - 1][1];
};
const fit = (cv) => {
  const r = cv.getBoundingClientRect(), d = Math.min(2, devicePixelRatio || 1);
  cv.width = Math.round(r.width * d); cv.height = Math.round(r.height * d);
  return {g: cv.getContext('2d'), w: cv.width, h: cv.height, d};
};

// ---------- nav
document.querySelector('.burger')?.addEventListener('click', () => document.querySelector('.nav').classList.toggle('open'));

// ---------- reveal on scroll
const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), {threshold: 0.12});
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

// ---------- the Terrain dashboard: a field in NDVI, survey passes being flown, detections pinned
function dashboard(cv) {
  const {g, w, h} = fit(cv);
  const img = g.createImageData(w, h);
  const plots = [];
  for (let i = 0; i < 9; i++) plots.push([h2(i, 3) * w, h2(i, 7) * h]);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let n = ndvi(x, y, w / 900);
    // field boundaries: nearest-plot cells, with darker tracks between them
    let a = 1e9, b = 1e9;
    for (const [px, py] of plots) { const d = (x - px) ** 2 + (y - py) ** 2; if (d < a) { b = a; a = d; } else if (d < b) b = d; }
    const edge = Math.sqrt(b) - Math.sqrt(a) < 2.2 * (w / 900);
    const row = 0.92 + 0.08 * Math.sin((x + y * 0.3) * 0.9);
    let [r, gg, bb] = ramp(n);
    if (edge) [r, gg, bb] = [62, 54, 40];
    const o = (y * w + x) * 4;
    img.data[o] = r * row; img.data[o + 1] = gg * row; img.data[o + 2] = bb * row; img.data[o + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const base = g.getImageData(0, 0, w, h);
  // detections in the low-NDVI spots
  const pins = [];
  for (let k = 0; k < 400 && pins.length < 7; k++) {
    const x = h2(k, 11) * w * 0.9 + w * 0.05, y = h2(k, 13) * h * 0.85 + h * 0.08;
    if (ndvi(x, y, w / 900) < 0.36 && pins.every((p) => Math.hypot(p.x - x, p.y - y) > w * 0.12)) pins.push({x, y, c: ['#ffb020', '#ff4a3a', '#ff3aa8', '#b6f36a'][pins.length % 4]});
  }
  let t0 = performance.now();
  const lane = h / 7;
  const draw = (now) => {
    const t = ((now - t0) / 1000) % 18;
    g.putImageData(base, 0, 0);
    // flown passes: darken the not-yet-flown part a little
    const total = 7 * w, done = (t / 18) * total, pass = Math.floor(done / w), along = done - pass * w;
    g.fillStyle = 'rgba(6,10,8,.42)';
    for (let p = 0; p < 7; p++) {
      if (p < pass) continue;
      if (p > pass) { g.fillRect(0, p * lane, w, lane); continue; }
      if (p % 2 === 0) g.fillRect(along, p * lane, w - along, lane); else g.fillRect(0, p * lane, w - along, lane);
    }
    // path and drone
    g.strokeStyle = 'rgba(56,225,255,.55)'; g.lineWidth = 1.2 * (w / 900); g.setLineDash([6, 6]);
    g.beginPath();
    for (let p = 0; p <= pass; p++) {
      const y = (p + 0.5) * lane, x1 = p === pass ? (p % 2 ? w - along : along) : (p % 2 ? 0 : w);
      if (p === 0) g.moveTo(0, y); else g.lineTo(p % 2 ? w : 0, y);
      g.lineTo(x1, y);
    }
    g.stroke(); g.setLineDash([]);
    const dx = pass % 2 ? w - along : along, dy = (pass + 0.5) * lane;
    g.fillStyle = 'rgba(56,225,255,.16)'; g.fillRect(dx - lane * 0.5, dy - lane * 0.5, lane, lane);
    g.fillStyle = '#38e1ff'; g.beginPath(); g.arc(dx, dy, 5 * (w / 900), 0, 7); g.fill();
    // pins appear once flown over
    for (const p of pins) {
      const pp = Math.floor(p.y / lane), seen = pp < pass || (pp === pass && (pp % 2 ? p.x > w - along : p.x < along));
      if (!seen) continue;
      const pulse = (now / 900 + p.x) % 1;
      g.strokeStyle = p.c; g.globalAlpha = 1 - pulse; g.lineWidth = 2 * (w / 900);
      g.beginPath(); g.arc(p.x, p.y, (8 + pulse * 18) * (w / 900), 0, 7); g.stroke();
      g.globalAlpha = 1; g.fillStyle = p.c; g.beginPath(); g.arc(p.x, p.y, 5 * (w / 900), 0, 7); g.fill();
    }
    requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
}
document.querySelectorAll('canvas[data-dash]').forEach(dashboard);

// ---------- prescription map: management zones and the rate for each
function prescription(cv) {
  const {g, w, h} = fit(cv);
  const cell = Math.round(w / 48);
  const cols = ['#d9583b', '#e8a23c', '#c9d65a', '#5fb94e', '#1f8a48'];
  for (let y = 0; y < h; y += cell) for (let x = 0; x < w; x += cell) {
    const n = ndvi(x * 1.4, y * 1.4, w / 1100);
    const z = Math.min(4, Math.floor((n - 0.12) / 0.16));
    g.fillStyle = cols[Math.max(0, z)];
    g.globalAlpha = 0.85;
    g.fillRect(x, y, cell - 1, cell - 1);
  }
  g.globalAlpha = 1;
  // crop rows on top
  g.strokeStyle = 'rgba(0,0,0,.14)'; g.lineWidth = 1;
  for (let x = 0; x < w; x += 6) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
}
document.querySelectorAll('canvas[data-rx]').forEach(prescription);

// ---------- analytics illustrations
function boundary(cv) {
  const {g, w, h} = fit(cv);
  for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) { const [r, gg, b] = ramp(ndvi(x * 2, y * 2, 1)); g.fillStyle = `rgb(${r * 0.7},${gg * 0.7},${b * 0.7})`; g.fillRect(x, y, 2, 2); }
  const pts = [[0.16, 0.2], [0.72, 0.12], [0.86, 0.58], [0.6, 0.86], [0.2, 0.74]].map(([x, y]) => [x * w, y * h]);
  g.fillStyle = 'rgba(182,243,106,.12)'; g.strokeStyle = '#b6f36a'; g.lineWidth = 2.5;
  g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#fff'; pts.forEach(([x, y]) => { g.beginPath(); g.arc(x, y, 5, 0, 7); g.fill(); });
  g.font = `600 ${Math.round(w / 22)}px JetBrains Mono, monospace`; g.fillStyle = '#eef2ec'; g.fillText('42.6 ac', w * 0.4, h * 0.5);
}
function classify(cv) {
  const {g, w, h} = fit(cv);
  const cls = ['#2f7d43', '#9bbf4f', '#c79a5b', '#5a6a72', '#3c7fb0'];
  for (let y = 0; y < h; y += 3) for (let x = 0; x < w; x += 3) {
    const n = vn(x / 60, y / 50) * 0.7 + vn(x / 18, y / 15) * 0.3;
    g.fillStyle = cls[Math.min(4, Math.floor(n * 5))]; g.fillRect(x, y, 3, 3);
  }
}
function elevation(cv) {
  const {g, w, h} = fit(cv);
  for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
    const e = vn(x / 90, y / 70) * 0.8 + vn(x / 30, y / 25) * 0.2;
    const band = Math.abs((e * 14) % 1 - 0.5) < 0.05;
    const c = [20 + e * 40, 40 + e * 120, 60 + e * 140];
    g.fillStyle = band ? 'rgba(238,242,236,.85)' : `rgb(${c.map(Math.round).join(',')})`;
    g.fillRect(x, y, 2, 2);
  }
}
document.querySelectorAll('canvas[data-ill]').forEach((cv) => ({boundary, classify, elevation})[cv.dataset.ill]?.(cv));

// ---------- industries: accordion that also swaps the picture
document.querySelectorAll('.acc').forEach((acc) => {
  const imgs = document.querySelectorAll(acc.dataset.pics + ' img');
  acc.querySelectorAll('button').forEach((b, i) => b.addEventListener('click', () => {
    acc.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
    imgs.forEach((im) => (im.style.opacity = im.dataset.i == (b.dataset.pic ?? i) ? 1 : 0));
  }));
});

// ---------- sensor tabs
document.querySelectorAll('.tabs').forEach((tabs) => {
  const set = (k) => {
    tabs.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.tab === k));
    document.querySelectorAll('.panel').forEach((p) => p.classList.toggle('on', p.id === k));
    history.replaceState(null, '', '#' + k);
    window.dispatchEvent(new Event('resize'));
  };
  tabs.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => set(b.dataset.tab)));
  const want = location.hash.slice(1);
  if (want && document.getElementById(want)) set(want);
});

// ---------- contact: a static site has no server, so the form opens the visitor's mail app with everything filled in
document.querySelectorAll('form[data-mailto]').forEach((f) => f.addEventListener('submit', (e) => {
  e.preventDefault();
  const v = (n) => f.elements[n]?.value?.trim() || '';
  const body = `${v('message')}\n\n${v('name')}\n${v('email')}${v('acres') ? `\nArea: ${v('acres')}` : ''}${v('interest') ? `\nInterested in: ${v('interest')}` : ''}`;
  location.href = `mailto:${f.dataset.mailto}?subject=${encodeURIComponent(v('subject') || 'Enquiry from the website')}&body=${encodeURIComponent(body)}`;
  f.querySelector('.sent').hidden = false;
}));
