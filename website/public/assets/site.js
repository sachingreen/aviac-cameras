// Aviac website: nav, reveals, the spectral chart, the sample field (RGB / NDVI), colourway swatches, and the pinned
// teardown on product pages. No library: the teardown reads scroll position and drives the 3D viewer directly.
document.documentElement.classList.add('js');
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

// nav
const nav = $('.nav');
addEventListener('scroll', () => nav?.classList.toggle('scrolled', scrollY > 10), {passive: true});
// phone menu: the button says whether the menu is open, and Escape closes it and returns focus to the button
const burger = $('.burger'), menuList = $('.nav ul');
const setMenu = (open) => {
  nav?.classList.toggle('open', open);
  document.documentElement.classList.toggle('menu-open', open);   // the page behind the open menu holds still
  burger?.setAttribute('aria-expanded', String(open));
  burger?.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
};
if (burger && menuList) {
  menuList.id ||= 'site-menu';
  burger.setAttribute('aria-controls', menuList.id);
  // the bar's "Request a pilot" and "Sign in" are hidden on small screens, so the menu carries them as its last items
  const acts = [$('.nav .cta'), $('.nav .signin')].filter(Boolean);
  if (acts.length) {
    const li = document.createElement('li');
    li.className = 'm-acts';
    acts.forEach((a) => { const c = a.cloneNode(true); c.classList.remove('cta', 'signin'); c.classList.add('btn'); li.append(c); });
    li.firstElementChild?.classList.add('p');
    menuList.append(li);
  }
  setMenu(false);
  burger.addEventListener('click', () => {
    const open = !nav.classList.contains('open');
    setMenu(open);
    if (open) $('a', menuList)?.focus({preventScroll: true});   // keyboard users start inside the menu
  });
  nav.addEventListener('focusout', (e) => {                     // tabbing out of the nav closes the menu
    if (nav.classList.contains('open') && e.relatedTarget && !nav.contains(e.relatedTarget)) setMenu(false);
  });
}
$$('.nav ul a').forEach((l) => l.addEventListener('click', () => setMenu(false)));   // close after choosing
addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (nav?.classList.contains('open')) { setMenu(false); burger?.focus(); return; }
  const dd = document.activeElement?.closest?.('.nav li.dd');                         // desktop dropdown: Escape closes it,
  if (dd) { dd.classList.add('shut'); $('a', dd).focus(); }                            // focus stays on its top link
});
$$('.nav li.dd').forEach((dd) => {
  const reopen = () => dd.classList.remove('shut');
  dd.addEventListener('mouseleave', reopen);
  dd.addEventListener('focusout', (e) => { if (!dd.contains(e.relatedTarget)) reopen(); });
});

// reveals (content stays visible without JS)
const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), {threshold: 0.12});
$$('.reveal').forEach((el) => io.observe(el));

// ---------- RGB / NDVI compare: drag the divider, or use the toggle
// Pin labels sit on the revealed (right) side of the divider: each label tries the right of its dot, then the left,
// and keeps whichever fits inside the revealed area without covering another label or dot; if neither does, only
// the dot shows until there is room (a wider screen, or the divider moved further left).
const placePins = (box, cur) => {
  const W = box.clientWidth, H = box.clientHeight, minX = cur * W + 4, GAP = 16, placed = [];
  const pins = $$('.pin', box).filter((p) => p.classList.contains('on'));
  const dots = pins.map((p) => ({x: parseFloat(p.style.left) / 100 * W, y: parseFloat(p.style.top) / 100 * H}));
  const hits = (a, b) => a.l < b.r && a.r > b.l && a.t < b.b && a.b > b.t;
  pins.forEach((p, i) => {
    const b = $('b', p); if (!b) return;
    p.classList.remove('dot');
    const w = b.offsetWidth, h = b.offsetHeight, {x, y} = dots[i];
    const box2 = (left) => ({l: left ? x - GAP - w : x + GAP, r: left ? x - GAP : x + GAP + w, t: y - h / 2, b: y + h / 2});
    const others = dots.filter((_, j) => j !== i).map((d) => ({l: d.x - 11, r: d.x + 11, t: d.y - 11, b: d.y + 11}));
    const ok = (r) => r.l >= minX && r.r <= W - 4 && r.t >= 4 && r.b <= H - 4 && ![...placed, ...others].some((o) => hits(r, o));
    const pref = p.dataset.side || (p.classList.contains('lft') ? 'l' : 'r');
    p.dataset.side = pref;
    const order = pref === 'l' ? [true, false] : [false, true];
    const fit = order.find((left) => ok(box2(left)));
    if (fit === undefined) { p.classList.add('dot'); return; }
    p.classList.toggle('lft', fit);
    placed.push(box2(fit));
  });
};
$$('.cmpimg').forEach((box) => {
  const card = box.closest('.sample'), h = $('.handle', box), togs = $$('.tog button', card);
  let cur = 0.5;
  togs.forEach((b) => b.setAttribute('type', 'button'));
  const set = (k, anim) => {
    cur = clamp(k, 0, 1);
    box.classList.toggle('dragging', !anim);
    box.style.setProperty('--x', `${cur * 100}%`);
    h.setAttribute('aria-valuenow', Math.round(cur * 100));
    h.setAttribute('aria-valuetext', `${Math.round((1 - cur) * 100)}% ${togs.find((b) => +b.dataset.at === 1)?.textContent.trim() || 'overlay'}`);
    $$('.pin', box).forEach((p) => p.classList.toggle('on', parseFloat(p.style.left) > cur * 100 + 1));
    placePins(box, cur);
    togs.forEach((b) => {                                    // a view button is "on" only when that view fills the frame
      const on = +b.dataset.at === 1 ? cur <= 0.02 : cur >= 0.98;
      b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on));
    });
  };
  const at = (e) => { const r = box.getBoundingClientRect(); return (e.clientX - r.left) / r.width; };
  // mouse and pen drag at once; touch waits until the finger clearly moves sideways, so a vertical swipe stays a page scroll
  let down = false, touch = null;
  const release = () => { down = false; touch = null; };
  box.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') { touch = {x: e.clientX, y: e.clientY, id: e.pointerId}; return; }
    down = true; box.setPointerCapture(e.pointerId); set(at(e));
  });
  box.addEventListener('pointermove', (e) => {
    if (touch && !down) {
      const dx = e.clientX - touch.x, dy = e.clientY - touch.y;
      if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) { down = true; box.setPointerCapture(touch.id); }
      else return;
    }
    if (down) set(at(e));
  });
  box.addEventListener('pointerup', (e) => { if (touch && !down && e.pointerType === 'touch') set(at(e), true); release(); });   // a tap moves the divider there
  box.addEventListener('pointercancel', release);
  box.addEventListener('lostpointercapture', release);
  h.addEventListener('keydown', (e) => {
    const to = {ArrowLeft: cur - 0.05, ArrowDown: cur - 0.05, ArrowRight: cur + 0.05, ArrowUp: cur + 0.05, Home: 0, End: 1}[e.key];
    if (to === undefined) return;
    e.preventDefault(); set(to, true);
  });
  togs.forEach((b) => b.addEventListener('click', () => set(+b.dataset.at === 1 ? 0 : 1, true)));
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => placePins(box, cur), 120); });
  document.fonts?.ready.then(() => placePins(box, cur));
  set(0.5, true);
});

// ---------- colourway swatches on product pages
$$('.swatches').forEach((sw) => {
  const target = $(sw.dataset.for);
  let req = 0;                                                       // only the latest pick may swap the photo in
  const mark = (b) => $$('button', sw).forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', String(x === b)); });
  mark($('button.on', sw));
  $$('button', sw).forEach((b) => b.addEventListener('click', () => {
    const mine = ++req;
    mark(b);
    $('span', sw).textContent = b.title;
    if (target.tagName === 'IMG' && b.dataset.img) {               // studio photo: load the new one, then cross-fade
      const base = b.dataset.img, n = new Image(), pic = target.parentElement.tagName === 'PICTURE' ? $('source', target.parentElement) : null;
      const ext = /\.webp(\?|$)/.test(target.currentSrc || '') ? 'webp' : 'jpg';          // preload whichever format this browser shows
      n.sizes = target.sizes; n.srcset = `${base}_800.${ext} 800w, ${base}.${ext} 1600w`; n.src = `${base}.${ext}`;
      target.classList.add('swap');
      n.decode().catch(() => {}).then(() => {
        if (mine !== req) return;                                  // a newer pick is on its way; let it win
        if (pic) pic.srcset = `${base}_800.webp 800w, ${base}.webp 1600w`;
        target.srcset = `${base}_800.jpg 800w, ${base}.jpg 1600w`; target.src = base + '.jpg';
        target.alt = target.alt.replace(/ in \w+$/, ' in ' + b.dataset.finish);
        target.classList.remove('swap');
      });
    }
    $$(`.viewer[data-follow="${target.id}"]`).forEach((f) => { f.dataset.finish = b.dataset.finish; window.Aviac?.viewers?.[f.id]?.setFinish(b.dataset.finish); });
  }));
});

// ---------- teardown: a pinned stage; scrolling down steps through the parts. One card shows at a time and the cards
// move vertically (the next rises in from below, the last lifts away), with a vertical progress rail beside the model
const td = $('.td');
// phones and portrait tablets stack the model above one card; wider screens put them side by side (matches site.css)
const stackedTD = () => matchMedia('(max-width:760px), (max-width:1023px) and (orientation:portrait)').matches;
if (td) {
  const cards = $$('.card', td), bars = $$('.prog i', td), label = $('.prog span', td), stage = $('.viewer', td), vid = stage.id;
  const stages = cards.map((c) => c.dataset.group || null);
  const views = cards.map((c) => (c.dataset.view || '0.6,0.2,3.2').split(',').map(Number));
  const holdD = Math.max(...views.slice(1, -1).map((v) => v[2]));   // the widest exploded framing on this page
  let last = -1, applied = -1, appliedTo = null;
  const apply = (i) => {
    const v = window.Aviac?.viewers?.[vid];
    if (!v || (i === applied && v === appliedTo)) return;     // only real changes reach the model, so it can rest between them
    applied = i; appliedTo = v;
    v.driven = true;
    const end = i === cards.length - 1;
    v.explode(i === 0 || end ? 0 : 1);
    const [az, el, d] = views[i];
    const hold = !stackedTD() && !(i === 0 || end);   // desktop: every exploded step at one distance and a capped turn, so the model holds its size and place
    const fit = Math.max(1, 1.95 / (stage.clientWidth / Math.max(1, stage.clientHeight)));   // a narrower stage pulls the camera back so the exploded stack still fits
    v.view(hold ? Math.min(az, 0.75) : az, el, hold ? holdD * fit : d);
    v.focus(i === 0 || end ? null : stages[i]);
  };
  const span = () => Math.max(1, td.offsetHeight - innerHeight);
  const tick = () => {
    const p = clamp(-td.getBoundingClientRect().top / span(), 0, 1);
    const i = clamp(Math.round(p * (cards.length - 1)), 0, cards.length - 1);
    if (i !== last) {
      last = i;
      cards.forEach((c, j) => { c.classList.toggle('on', j === i); c.classList.toggle('past', j < i); });
      bars.forEach((b, j) => b.classList.toggle('on', j <= i));
      label.textContent = `${i + 1} / ${cards.length}`;
      layout();
    }
    apply(i);
  };
  // desktop: the model sits left of the card, placed by site.css; phones: the stage ends just above the card on show
  const layout = () => {
    if (!stackedTD()) { stage.style.bottom = ''; stage.style.height = ''; return; }
    // phones: the model ends above the card, but always keeps at least 34% of the screen; a long card on a short
    // screen overlaps the model's faded lower edge instead of squeezing it away
    const minModel = innerHeight * 0.34, top = stage.offsetTop || 118;
    const below = Math.min(cards[Math.max(0, last)].offsetHeight + 16 + 12, innerHeight - top - minModel);
    stage.style.bottom = Math.max(0, below) + 'px'; stage.style.height = 'auto';
  };
  layout();
  document.fonts.ready.then(layout);
  let queued = false;
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; tick(); }); } }, {passive: true});
  addEventListener('resize', () => { layout(); applied = -1; tick(); });   // a new size re-lays the stage and re-frames the model
  const pick = setInterval(() => { tick(); if (appliedTo) clearInterval(pick); }, 400);   // picks up the viewer once it has loaded
  // keyboard: up/down and left/right arrows step through the stages while the teardown is pinned
  addEventListener('keydown', (e) => {
    const step = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key];
    if (!step || e.target.closest?.('input,textarea,select')) return;
    const r = td.getBoundingClientRect();
    if (r.top > 0 || r.bottom < innerHeight) return;                // not pinned: arrows do what they normally do
    const next = Math.max(0, last) + step;
    const sideways = e.key === 'ArrowLeft' || e.key === 'ArrowRight';
    if (next < 0 || next >= cards.length) {                         // past either end: up/down scroll the page as usual;
      if (sideways) e.preventDefault();                             // left/right do nothing (never switch product mid-teardown)
      return;
    }
    const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    scrollTo({top: r.top + scrollY + (next / (cards.length - 1)) * span() + 1, behavior: smooth ? 'smooth' : 'auto'});
    e.preventDefault();
  });
}

// ---------- pilot request: sent to info@aviac.in through FormSubmit (a static site has no server of its own);
// if that service cannot be reached, the visitor's mail app opens with everything filled in instead
$$('form[data-mailto]').forEach((f) => f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const v = (n) => f.elements[n]?.value?.trim() || '';
  if (v('_honey')) return;                                  // bots fill the hidden field
  // "required" lets a field of only spaces through; ask for real text, beside the field, in the browser's own bubble
  for (const [n, say] of [['name', 'Please add your name.'], ['message', 'Please tell us a little about the job.']]) {
    const el = f.elements[n];
    if (el && !v(n)) { el.setCustomValidity(say); el.reportValidity(); el.addEventListener('input', () => el.setCustomValidity(''), {once: true}); return; }
  }
  const msg = $('.sent', f), btn = $('button[type=submit]', f);
  const subject = (/quote/i.test(v('interest')) ? 'Quote request: ' : 'Pilot request: ') + (v('org') || v('name'));
  btn.disabled = true;                                      // .btn[disabled] in site.css greys it out
  try {
    const r = await fetch(`https://formsubmit.co/ajax/${f.dataset.mailto}`, {method: 'POST', headers: {'Content-Type': 'application/json', Accept: 'application/json'},
      body: JSON.stringify({_subject: subject, _template: 'table', name: v('name'), email: v('email'), company: v('org'), size: v('acres'), interested_in: v('interest'), message: v('message')})});
    const j = await r.json().catch(() => ({}));
    if (!r.ok || String(j.success) !== 'true') throw new Error('send failed');
    msg.textContent = `Thank you, ${v('name').split(' ')[0] || 'we have it'}. Your request is with us at ${f.dataset.mailto}; we will reply within two working days.`;
    f.reset();
  } catch (err) {
    const who = [v('name'), v('org')].filter(Boolean).join(' · ');
    const body = `${v('message')}\n\n${who}\n${v('email')}\nSize: ${v('acres') || '-'}\nInterested in: ${v('interest')}`;
    location.href = `mailto:${f.dataset.mailto}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    msg.textContent = `Your mail app should open with the request ready. If it does not, write to ${f.dataset.mailto}.`;
  }
  msg.hidden = false; btn.disabled = false;
}));

// ---------- home: solutions explorer, auto-advancing until someone picks a market.
// It holds still while the pointer or keyboard focus is on it, and never advances for people who ask for less motion.
// Only the shown pane can be tabbed to; the hidden ones are inert. Tabs follow the ARIA tabs pattern (arrows, Home, End).
$$('.explorer').forEach((ex) => {
  const tabs = $$('.xt', ex), panes = $$('.xp', ex), bar = $('.xbar i', ex);
  const DWELL_MS = 6000;
  let i = 0, t0 = performance.now(), seen = false, held = false;
  let auto = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  const go = (k) => {
    i = k;
    tabs.forEach((t, j) => { t.classList.toggle('on', j === k); t.setAttribute('aria-selected', String(j === k)); t.tabIndex = j === k ? 0 : -1; });
    panes.forEach((p, j) => { p.classList.toggle('on', j === k); p.inert = j !== k; });
    t0 = performance.now();
    // phones/tablets: the tabs are one sideways-scrolling row; bring the chosen one into view (row only, never the page)
    const row = tabs[k].parentElement;
    if (row.scrollWidth > row.clientWidth + 1) {
      const left = tabs[k].offsetLeft - row.offsetLeft - 20;
      row.scrollTo({left: Math.max(0, left), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    }
  };
  const pick = (k) => { auto = false; go(k); if (bar) bar.style.width = '0'; };   // a visitor's choice stops the auto-advance
  tabs.forEach((t, k) => {
    t.addEventListener('click', () => pick(k));
    t.addEventListener('mouseenter', () => matchMedia('(hover:hover)').matches && pick(k));
    t.addEventListener('keydown', (e) => {
      const n = tabs.length;
      const to = {ArrowDown: k + 1, ArrowRight: k + 1, ArrowUp: k - 1, ArrowLeft: k - 1, Home: 0, End: n - 1}[e.key];
      if (to === undefined) return;
      e.preventDefault();
      const next = (to + n) % n;
      pick(next); tabs[next].focus();
    });
  });
  const hold = (v) => { held = v; t0 = performance.now(); if (bar && v) bar.style.width = '0'; };
  ex.addEventListener('pointerenter', () => hold(true));
  ex.addEventListener('pointerleave', () => hold(false));
  ex.addEventListener('focusin', () => hold(true));
  ex.addEventListener('focusout', (e) => { if (!ex.contains(e.relatedTarget)) hold(false); });
  new IntersectionObserver((es) => { seen = es[0].isIntersecting; t0 = performance.now(); }).observe(ex);
  const tick = (now) => {
    if (auto && seen && !held) {
      const k = (now - t0) / DWELL_MS;
      if (bar) bar.style.width = `${Math.min(1, k) * 100}%`;
      if (k >= 1) go((i + 1) % panes.length);
    }
    if (auto) requestAnimationFrame(tick);
  };
  go(0);
  if (auto) requestAnimationFrame(tick);
});

// ---------- home: the readings rail rows act as buttons for keyboards and screen readers, and say which one is shown
$$('.lc-tele [role=button]').forEach((row) => {
  const sync = () => row.setAttribute('aria-pressed', String(row.classList.contains('on')));
  sync();
  new MutationObserver(sync).observe(row, {attributes: true, attributeFilter: ['class']});
  row.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); row.click(); } });
});

// ---------- home: "Request a pilot" on a solution or product page arrives as ?for=<page>; pre-select that job in the form
{
  const key = new URLSearchParams(location.search).get('for');
  const select = $('#f-int');
  if (key && select && /^[a-z-]{2,40}$/.test(key)) {
    const match = [...select.options].find((o) => (o.dataset.for || '').split(' ').includes(key));
    if (match) select.value = match.value;
  }
}

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
  $$('.systems,.minis,.steps,.people,.partners,.stats,.dgrid').forEach((g) => [...g.children].forEach((c, i) => {
    c.style.setProperty('--d', `${Math.min(i, 6) * 0.08}s`);
    if (!c.classList.contains('reveal') && !g.classList.contains('reveal')) { c.classList.add('reveal'); io.observe(c); }
  }));
  const par = reduce ? [] : $$('.hero .pic img,.phero .pic img');
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
    sw: {win: [[400, 1700, 'SWIRL · IMX992 400–1700 nm']], mica: true},
    construction: {win: [[400, 700, 'Colour map'], [700, 1000, 'Duos NIR']], qe: true},
  };
  const WIN = '#2f6f4e';
  function draw(cv) {
    const key = cv.dataset.band, C = CFG[key];
    const d = Math.min(2, devicePixelRatio || 1), cssW = cv.getBoundingClientRect().width, small = cssW < 560;
    const cssH = C.zoom ? 470 : (small ? 300 : 330);
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
      // tick step from the plot's real width, so labels never run together on narrow screens
      const step = opt.lwir ? 2000 : (b - a > 1500 ? [250, 500, 1000] : [100, 250, 500]).find((s) => X(a + s) - X(a) >= 46 * d) || 1000;
      for (let nm = Math.ceil(a / step) * step; nm <= b; nm += step) { const x = X(nm); g.fillStyle = '#2b3a33'; g.fillRect(x, bot, d, 4 * d);
        const lab = opt.lwir ? String(nm / 1000) : String(nm); g.font = font();
        text(lab, Math.min(x, Wd - g.measureText(lab).width / 2 - 2 * d), bot + 15 * d, '#3b4a43', 'center'); }   // keep the last tick inside the canvas
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
      g.save(); g.beginPath(); g.rect(x0, top, x1 - x0, bot - top); g.clip();   // filter shapes stay inside the plot box
      if (C.filters && !opt.lwir) for (const [c0, fw, col, n] of C.filters) {
        if (c0 < a || c0 > b) continue;
        g.beginPath(); g.moveTo(X(c0 - 2 * fw), bot);
        for (let nm = c0 - 2 * fw; nm <= c0 + 2 * fw; nm += 1) g.lineTo(X(nm), Y(ymax * 0.86 * Math.pow(g2(nm, c0, fw), 0.55)));
        g.lineTo(X(c0 + 2 * fw), bot); g.closePath(); g.fillStyle = col + (opt.zoom ? '3a' : '60'); g.fill();
        if (opt.zoom) { g.strokeStyle = col; g.lineWidth = 1.4 * d; g.stroke(); }
      }
      g.restore();
      if (opt.zoom && C.filters) {                       // peak labels, staggered so neighbours never collide
        C.filters.forEach(([c0, , col, n], i) => { const yy = top + (i % 2 ? 28 : 14) * d; text(`${c0}`, X(c0), yy, col, 'center', 600); });
      }
      // feature markers
      let lastLab = -1e9;
      if (!opt.lwir && !opt.zoom) for (const [nm, n] of [[700, 'red edge'], [1450, 'water'], [1940, 'water'], [2200, 'Al-OH']]) {
        if (nm < a || nm > b) continue; const x = X(nm); g.strokeStyle = '#b9c3bd'; g.setLineDash([2 * d, 3 * d]); g.beginPath(); g.moveTo(x, top + 36 * d); g.lineTo(x, bot); g.stroke(); g.setLineDash([]);
        g.font = font(); const tw = g.measureText(n).width; if (x + 3 * d > lastLab + 6 * d && x + 3 * d + tw < x1 - (C.qe ? 34 * d : 0)) { text(n, x + 3 * d, top + (46 + (C.win.length > 1 ? 10 : 0)) * d, '#8a979e', 'left', 500); lastLab = x + 3 * d + tw; }
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
      const cap = 'Zoom: the six MS filters over a healthy and a stressed leaf'; g.font = font();
      text(g.measureText(cap).width < Wd - L - Rr ? cap : 'Zoom: the six MS filters', (L + Wd - Rr) / 2, H - 6 * d, '#3b4a43', 'center');
    } else if (C.lwir) {
      const lw = Math.min(small ? 80 * d : 200 * d, Wd * 0.24), gap = (C.qe ? (small ? 40 : 52) : (small ? 16 : 26)) * d, x1 = Wd - (small ? 8 : 14) * d - lw - gap;
      plot(L, x1, top, H - 34 * d, 0, 2500, 0.7, {yaxis: true});
      plot(x1 + gap, Wd - (small ? 8 : 14) * d, top, H - 34 * d, 7000, 15000, 0.7, {lwir: true});
      g.strokeStyle = '#2b3a33'; g.lineWidth = 1.4 * d; for (const dx of [-3, 3]) { g.beginPath(); g.moveTo(x1 + gap * 0.7 + dx * d - 4 * d, H - 28 * d); g.lineTo(x1 + gap * 0.7 + dx * d + 4 * d, H - 40 * d); g.stroke(); }
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
  document.fonts.ready.then(run); run();
  let t; addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
})();

// ---------- product pages: arrow keys and a clear sideways swipe step to the neighbouring system. Registered last, so a
// section that uses the arrows itself (the teardown) handles them first and this one stands aside.
{
  const prev = $('.sb-edge.l'), next = $('.sb-edge.r');
  if (prev && next) {
    addEventListener('keydown', (e) => {
      if (e.defaultPrevented || e.altKey || e.metaKey || e.ctrlKey || e.target.closest('input,textarea,select,[contenteditable]')) return;
      if (e.key === 'ArrowLeft') location.href = prev.href;
      if (e.key === 'ArrowRight') location.href = next.href;
    });
    let x0 = null, y0 = 0;
    addEventListener('touchstart', (e) => { x0 = e.target.closest('.viewer,.cmpimg,.fly,.td,.sb-row,.gallery,.stage') ? null : e.touches[0].clientX; y0 = e.touches[0].clientY; }, {passive: true});
    addEventListener('touchend', (e) => {
      if (x0 === null) return;
      const t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0; x0 = null;
      if (Math.abs(dx) < 90 || Math.abs(dx) < 2 * Math.abs(dy)) return;                 // a scroll that drifts sideways is not a swipe
      location.href = dx > 0 ? prev.href : next.href;
    });
  }
}
