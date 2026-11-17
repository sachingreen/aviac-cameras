// The overlay: a fixed 1600 x 900 layout of panels around the camera. update(s) redraws every live part from the
// frame's state; nothing here computes a number of its own. Layout pattern after the teardown kit's examples.
import {BANDS, LID, MIRA_QE, OVERLAP, SSD_GB, POWER, AMBIENT, ndvi, ndviColor} from './sim.js';
import {ACCENT} from './machine.js';

export const C = {ink: '#16181b', mute: '#8b8f95', faint: '#c9ccd0', line: '#e1e3e6', panel: 'rgba(249,249,247,.94)', acc: ACCENT, blue: '#3d8fe0'};
export const CAMS = ['hero', 'underside', 'inside', 'lid'];
export const OPENS = ['closed', 'lid off', 'exploded'];
export const SHOWS = ['labels', 'footprints', 'signals', 'heat'];
export const MODULES = [['RGB', 'RGB camera (IMX565)'], ['RED EDGE', 'Red edge camera (Mira220)'], ['NIR', 'NIR camera (Mira220)'], ['EXT NIR', 'Extended NIR camera (Mira220)'],
  ['LENS PLATE', 'Optics bench'], ['CARRIER', 'Carrier board'], ['JETSON', 'Jetson Orin Nano'], ['FINNED LID', 'Thermal'], ['MOUNT', 'Mount'], ['SUN SENSOR', 'DLS + GNSS top unit']];
export const H_RANGE = [30, 150];
export const V_RANGE = [12, 28];

const CSS = `
#app{font-family:Inter,system-ui,sans-serif;color:${C.ink};-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.ui{position:absolute;inset:0;pointer-events:none}
.pn{position:absolute;background:${C.panel};border:1px solid ${C.line};box-shadow:0 1px 2px rgba(20,22,26,.04)}
.cp{font-size:9.6px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;white-space:nowrap}
.mu{color:${C.mute}}
.tb{position:absolute;box-sizing:border-box;height:19px;padding:0 4px;display:flex;align-items:center;justify-content:center;font-size:8.8px;font-weight:600;letter-spacing:.9px;text-transform:uppercase;border:1px solid ${C.line};background:#fff;color:${C.ink};white-space:nowrap}
.tb.on{background:${C.ink};color:#fff;border-color:${C.ink}}
.rw{position:absolute;display:flex;justify-content:space-between;font-size:10.5px;width:225px}
.rw b{font-weight:600;font-family:'JetBrains Mono',monospace;font-size:10.2px}
.call{position:absolute;white-space:nowrap}
.call b{display:block;font-size:11.5px;font-weight:600;letter-spacing:.1px}
.call span{display:block;font-size:8.6px;font-weight:500;letter-spacing:1.4px;color:${C.mute};text-transform:uppercase;margin-top:2px}
.cur{position:absolute;left:0;top:0;z-index:50;filter:drop-shadow(0 1px 2px rgba(0,0,0,.3))}
.ring{position:absolute;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;border:1.5px solid ${C.acc};opacity:0;z-index:49}
`;
const el = (h) => {
  const d = document.createElement('div');
  d.innerHTML = h.trim();
  return d.firstElementChild;
};

export function createConsole(app) {
  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);
  const ui = el(`<div class="ui"></div>`);
  app.appendChild(ui);
  const add = (h) => {
    const n = el(h);
    ui.appendChild(n);
    return n;
  };
  const rows = (x, y, names) => names.map((n, i) => {
    const r = add(`<div class="rw" style="left:${x}px;top:${y + i * 17}px"><span class="mu">${n}</span><b></b></div>`);
    return r.lastElementChild;
  });

  // ------------------------------------------------------------ title and the key readout
  add(`<div style="position:absolute;left:35px;top:33px;width:43px;height:3px;background:${C.acc}"></div>`);
  add(`<div style="position:absolute;left:35px;top:47px;font-size:24px;font-weight:700;letter-spacing:-.2px">Aviac 6B <span style="color:${C.acc}">·</span> Six-Band Crop Camera</div>`);
  add(`<div class="cp" style="position:absolute;left:35px;top:81px;font-weight:500;letter-spacing:1.7px;font-size:9.4px">IMX565 + 3 × MIRA220 &nbsp;•&nbsp; 2 × 2 GRID &nbsp;•&nbsp; HARD-ANODISED ALUMINIUM &nbsp;•&nbsp; NO FAN</div>`);
  const gsdBig = add(`<div style="position:absolute;left:33px;top:103px;font-size:56px;font-weight:800;letter-spacing:-3.2px;color:${C.acc};line-height:1"></div>`);
  add(`<div style="position:absolute;left:178px;top:128px;font-size:11px;font-weight:500;line-height:1.35">CM / PIXEL<br><span class="mu" style="letter-spacing:1px;font-size:9.4px">GROUND DETAIL, RGB</span></div>`);
  add(`<div style="position:absolute;left:35px;top:174px;width:247px;height:9px;background:#e6e7e9"></div>`);
  const gsdFill = add(`<div style="position:absolute;left:35px;top:174px;height:9px;background:${C.acc}"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:35px;top:188px;font-size:9px;font-weight:500">0</div>`);
  add(`<div class="cp" style="position:absolute;left:226px;top:188px;font-size:9px;font-weight:500">3 CM / PX</div>`);

  // ------------------------------------------------------------ flight
  add(`<div class="pn" style="left:35px;top:214px;width:247px;height:168px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:226px;font-weight:700">FLIGHT</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:226px;font-weight:500">${Math.round(OVERLAP * 100)} % FORWARD OVERLAP</div>`);
  const fr = rows(46, 247, ['Detail, NIR bands', 'Swath width', 'Frame length on ground', 'Trigger every', 'Shutter for ½-pixel blur', 'Coverage', 'Sync error on ground']);

  // ------------------------------------------------------------ trigger timeline
  add(`<div class="pn" style="left:35px;top:390px;width:247px;height:178px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:402px;font-weight:700">ONE TRIGGER</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:402px;font-weight:500">FIRST 80 MS</div>`);
  const tl = add(`<svg style="position:absolute;left:46px;top:420px" width="226" height="118"></svg>`);
  add(`<div style="position:absolute;left:46px;top:546px;font-size:9.5px;color:${C.mute}">All four shutters open within <b style="color:${C.ink}">50 µs</b> of each other</div>`);

  // ------------------------------------------------------------ live map
  add(`<div class="pn" style="left:35px;top:576px;width:247px;height:190px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:588px;font-weight:700">VIGOUR MAP, LIVE</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:588px;font-weight:500">SIMULATED FIELD</div>`);
  const mapC = add(`<canvas width="452" height="250" style="position:absolute;left:46px;top:606px;width:226px;height:125px;background:#e6e7e9"></canvas>`);
  add(`<div style="position:absolute;left:46px;top:738px;width:226px;height:6px;background:linear-gradient(90deg,rgb(150,92,60),rgb(214,170,70),rgb(196,205,90),rgb(96,170,78),rgb(22,104,58))"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:46px;top:748px;font-size:8.4px;font-weight:500">STRESSED</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:748px;font-size:8.4px;font-weight:500">NDVI &nbsp;·&nbsp; VIGOROUS</div>`);

  // ------------------------------------------------------------ transport
  add(`<div class="pn" style="left:35px;top:774px;width:259px;height:111px"></div>`);
  const btn = {};
  btn.pause = add(`<div class="tb" style="left:45px;top:782px;width:99px;height:26px;background:${C.acc};color:#fff;border-color:${C.acc};font-size:9.6px"></div>`);
  btn.fire = add(`<div class="tb" style="left:149px;top:782px;width:136px;height:26px;font-size:9.6px">FIRE ONE FRAME</div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:818px;font-weight:500">HEIGHT ABOVE CROP</div>`);
  const hVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:818px;font-weight:700"></div>`);
  const SL = {x: 46, w: 238};
  add(`<div style="position:absolute;left:${SL.x}px;top:836px;width:${SL.w}px;height:2px;background:#e1e3e6"></div>`);
  const hKnob = add(`<div style="position:absolute;top:831px;width:9px;height:11px;margin-left:-4.5px;background:${C.acc}"></div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:851px;font-weight:500">AIRSPEED</div>`);
  const vVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:851px;font-weight:700"></div>`);
  add(`<div style="position:absolute;left:${SL.x}px;top:869px;width:${SL.w}px;height:2px;background:#e1e3e6"></div>`);
  const vKnob = add(`<div style="position:absolute;top:864px;width:9px;height:11px;margin-left:-4.5px;background:${C.acc}"></div>`);

  // ------------------------------------------------------------ band legend
  add(`<div class="cp" style="position:absolute;left:0;right:0;top:36px;display:flex;justify-content:center;gap:16px;font-weight:500;font-size:9.6px">
    ${BANDS.map((b) => `<span><i style="display:inline-block;width:15px;height:2.4px;background:${b.color};vertical-align:middle;margin-right:6px"></i>${b.name.toUpperCase()}</span>`).join('')}</div>`);

  // ------------------------------------------------------------ capture
  add(`<div class="pn" style="left:1318px;top:36px;width:245px;height:176px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:47px;font-weight:500">CAPTURE</div>`);
  const capRate = add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:47px;font-weight:500"></div>`);
  const frameBig = add(`<div style="position:absolute;left:1328px;top:62px;font-size:36px;font-weight:800;letter-spacing:-1.6px;color:${C.acc};line-height:1"></div>`);
  add(`<div style="position:absolute;left:1440px;top:72px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">FRAME SETS<br><span style="color:${C.mute};letter-spacing:1.5px">4 SENSORS EACH</span></div>`);
  add(`<div style="position:absolute;left:1329px;top:108px;width:224px;height:1px;background:${C.line}"></div>`);
  const cr = rows(1329, 116, ['One frame set on disk', 'Written per second', `Flight time on ${SSD_GB} GB`, 'RGB read-out, 2 lanes', 'NIR read-out, 2 lanes']);

  // ------------------------------------------------------------ spectral bands
  add(`<div class="pn" style="left:1318px;top:220px;width:245px;height:172px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:231px;font-weight:700">SIX BANDS</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:231px;font-weight:500">400 – 1000 NM</div>`);
  const sp = add(`<svg style="position:absolute;left:1326px;top:248px" width="232" height="138"></svg>`);
  {
    const X = (nm) => 10 + ((nm - 400) / 600) * 204;
    const Y = (q) => 104 - q * 86;
    let s = `<line x1="10" y1="104" x2="214" y2="104" stroke="${C.faint}"/>`;
    for (const nm of [400, 500, 600, 700, 800, 900, 1000]) s += `<line x1="${X(nm)}" y1="104" x2="${X(nm)}" y2="107" stroke="${C.faint}"/><text x="${X(nm)}" y="117" font-size="7.6" fill="${C.mute}" text-anchor="middle">${nm}</text>`;
    BANDS.forEach((b) => {
      if (b.sensor === 'IMX565') {
        let d = '';
        for (let nm = b.lo - 40; nm <= b.hi + 40; nm += 4) d += `${d ? 'L' : 'M'}${X(nm).toFixed(1)} ${Y(0.82 * Math.exp(-(((nm - b.peak) / ((b.hi - b.lo) * 0.52)) ** 2))).toFixed(1)}`;
        s += `<path d="${d}" fill="none" stroke="${b.color}" stroke-width="1.6"/>`;
      } else {
        s += `<rect x="${X(b.lo)}" y="${Y(0.9)}" width="${Math.max(2.5, X(b.hi) - X(b.lo))}" height="${104 - Y(0.9)}" fill="${b.color}" opacity=".85"/>`;
      }
      s += `<text x="${X(b.peak)}" y="${b.sensor === 'IMX565' ? 28 : 16}" font-size="7.4" font-weight="600" fill="${b.color}" text-anchor="middle">${b.key}</text>`;
    });
    s += `<path d="${MIRA_QE.map(([nm, q], i) => `${i ? 'L' : 'M'}${X(nm)} ${Y(q)}`).join('')}" fill="none" stroke="${C.ink}" stroke-width="1" stroke-dasharray="3 2"/>`;
    MIRA_QE.forEach(([nm, q]) => (s += `<circle cx="${X(nm)}" cy="${Y(q)}" r="2" fill="${C.ink}"/><text x="${X(nm) + 4}" y="${Y(q) - 4}" font-size="7.2" fill="${C.ink}">${Math.round(q * 100)}%</text>`));
    s += `<text x="8" y="133" font-size="8" fill="${C.mute}">Dashed: Mira220 sensitivity from its datasheet</text>`;
    sp.innerHTML = s;
  }

  // ------------------------------------------------------------ cooling
  add(`<div class="pn" style="left:1318px;top:400px;width:245px;height:186px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:411px;font-weight:700">COOLING, NO FAN</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:411px;font-weight:500">CALCULATED</div>`);
  const tBig = add(`<div style="position:absolute;left:1328px;top:428px;font-size:36px;font-weight:800;letter-spacing:-1.6px;line-height:1"></div>`);
  add(`<div style="position:absolute;left:1418px;top:438px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">°C FINNED LID<br><span style="color:${C.mute};letter-spacing:1.5px">${POWER} W AT ${AMBIENT} °C AIR</span></div>`);
  add(`<div style="position:absolute;left:1329px;top:476px;width:224px;height:5px;background:#e6e7e9"></div>`);
  const tFill = add(`<div style="position:absolute;left:1329px;top:476px;height:5px;background:${C.acc}"></div>`);
  add(`<div style="position:absolute;left:${1329 + 224 * ((99 - 40) / 70)}px;top:472px;width:1px;height:13px;background:${C.ink}"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:1329px;top:488px;font-size:8.4px;font-weight:500">40</div>`);
  add(`<div class="cp" style="position:absolute;left:${1329 + 224 * ((99 - 40) / 70) - 46}px;top:488px;font-size:8.4px;font-weight:500">THROTTLES AT 99</div>`);
  const tr = rows(1329, 510, ['Air along the fins', 'Heat transfer', 'Finned area', 'Module plate (estimate)']);

  // ------------------------------------------------------------ camera, open, show
  add(`<div class="pn" style="left:1296px;top:720px;width:268px;height:165px"></div>`);
  const group = (title, keys, y) => {
    add(`<div class="cp mu" style="position:absolute;left:1305px;top:${y}px;font-weight:500">${title}</div>`);
    let x = 1305;
    keys.forEach((k) => {
      const w = Math.round(k.length * 6.6 + 16);
      btn[k] = add(`<div class="tb" style="left:${x}px;top:${y + 15}px;width:${w}px">${k.toUpperCase()}</div>`);
      x += w + 4;
    });
  };
  group('CAMERA', CAMS, 729);
  group('OPEN IT UP', OPENS, 781);
  group('SHOW', SHOWS, 833);

  // ------------------------------------------------------------ module picker
  add(`<div class="cp mu" style="position:absolute;left:0;right:0;top:795px;text-align:center;font-weight:500"><span style="color:${C.ink}">MODULES</span> &nbsp;— &nbsp;CLICK ONE TO ISOLATE IT</div>`);
  {
    const ws = MODULES.map(([n]) => Math.round(n.length * 6.6 + 18));
    let x = 800 - (ws.reduce((a, b) => a + b, 0) + 4 * (ws.length - 1)) / 2;
    MODULES.forEach(([n, g], i) => {
      btn['m:' + g] = add(`<div class="tb" style="left:${x}px;top:815px;width:${ws[i]}px;height:22px">${n}</div>`);
      x += ws[i] + 4;
    });
  }
  const modInfo = add(`<div class="cp mu" style="position:absolute;left:0;right:0;top:848px;text-align:center;font-weight:500"></div>`);
  add(`<div class="cp" style="position:absolute;left:0;right:0;top:874px;text-align:center;font-weight:500;color:${C.faint}">DRAG TO ORBIT &nbsp;·&nbsp; SCROLL TO ZOOM &nbsp;·&nbsp; H HIDES THE PANELS</div>`);

  // ------------------------------------------------------------ callouts, the pointer
  const callSvg = add(`<svg style="position:absolute;inset:0;overflow:visible" width="1600" height="900"></svg>`);
  const callG = add(`<div style="position:absolute;inset:0"></div>`);
  const ring = add(`<div class="ring"></div>`);
  const cur = add(`<div class="cur"><svg width="22" height="22" viewBox="0 0 34 34"><path d="M4 3 L30 13.5 L17.5 17.5 L13.5 30 Z" fill="#111" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/></svg></div>`);
  const centre = (n) => [n.offsetLeft + n.offsetWidth / 2, n.offsetTop + n.offsetHeight / 2];
  const spots = Object.fromEntries(Object.entries(btn).map(([k, n]) => [k, centre(n)]));
  const knobX = (k) => SL.x + k * SL.w;
  const mctx = mapC.getContext('2d');
  let mapX = -1;

  return {
    spots, btn, root: ui, SL,
    hKnobAt: (k) => [knobX(k), 836],
    vKnobAt: (k) => [knobX(k), 869],
    pointer(c) {
      cur.style.display = c.x < 0 ? 'none' : 'block';
      cur.style.transform = `translate(${(c.x - 3).toFixed(1)}px, ${(c.y - 2).toFixed(1)}px) scale(${c.press ? 0.88 : 1})`;
      ring.style.left = `${c.rx}px`; ring.style.top = `${c.ry}px`;
      ring.style.opacity = String(c.ring * 0.85);
      ring.style.transform = `scale(${(0.35 + 0.9 * (1 - c.ring)).toFixed(3)})`;
    },
    /** calls: [{at:[x,y] screen px of the part, to:[x,y] label corner, title, sub, a: 0..1}] */
    callouts(calls) {
      let s = '', h = '';
      for (const c of calls) {
        if (!c.at || c.a < 0.02) continue;
        const right = c.to[0] > c.at[0];
        const ex = c.to[0] + (right ? -6 : 6);
        s += `<g opacity="${c.a.toFixed(2)}"><line x1="${c.at[0].toFixed(1)}" y1="${c.at[1].toFixed(1)}" x2="${ex}" y2="${c.to[1] + 7}" stroke="${C.ink}" stroke-width=".8"/><circle cx="${c.at[0].toFixed(1)}" cy="${c.at[1].toFixed(1)}" r="2.6" fill="${c.hot ? C.acc : C.ink}"/></g>`;
        h += `<div class="call" style="opacity:${c.a.toFixed(2)};top:${c.to[1]}px;${right ? `left:${c.to[0]}px` : `right:${1600 - c.to[0]}px;text-align:right`}"><b>${c.title}</b><span>${c.sub}</span></div>`;
      }
      callSvg.innerHTML = s;
      callG.innerHTML = h;
    },
    update(s) {
      const f = s.fl, th = s.th;
      gsdBig.textContent = (f.gsdRgb * 100).toFixed(2);
      gsdFill.style.width = `${Math.min(1, (f.gsdRgb * 100) / 3) * 247}px`;
      fr[0].textContent = `${(f.gsdMira * 100).toFixed(1)} cm / px`;
      fr[1].textContent = `${f.swath.toFixed(0)} m`;
      fr[2].textContent = `${f.along.toFixed(0)} m`;
      fr[3].textContent = `${(f.dt * 1000).toFixed(0)} ms`;
      fr[4].textContent = `1 / ${Math.round(1 / f.texp)} s`;
      fr[5].textContent = `${f.haPerHour.toFixed(0)} ha / h`;
      fr[6].textContent = `${(f.skewGround * 1000).toFixed(1)} mm`;
      capRate.textContent = `${f.fps.toFixed(2)} SETS / S`;
      frameBig.textContent = String(s.frames).padStart(4, '0');
      cr[0].textContent = `${f.mbTrig.toFixed(1)} MB`;
      cr[1].textContent = `${f.mbps.toFixed(0)} MB / s`;
      cr[2].textContent = `${f.minutes.toFixed(0)} min`;
      cr[3].textContent = `${(f.readRgb * 1000).toFixed(0)} ms`;
      cr[4].textContent = `${(f.readMira * 1000).toFixed(0)} ms`;
      const hot = th.plate > 89;
      tBig.textContent = th.lid.toFixed(0);
      tBig.style.color = hot ? C.acc : C.ink;
      tFill.style.width = `${Math.min(1, Math.max(0, (th.plate - 40) / 70)) * 224}px`;
      tr[0].textContent = th.air > 0 ? `${th.air.toFixed(0)} m / s` : 'still';
      tr[1].textContent = `${th.h.toFixed(0)} W / m²K`;
      tr[2].textContent = `${(LID.area * 1e4).toFixed(0)} cm²`;
      tr[3].textContent = `${th.plate.toFixed(0)} °C`;
      hVal.textContent = `${Math.round(f.h)} M`;
      vVal.textContent = `${f.v.toFixed(0)} M / S`;
      hKnob.style.left = `${knobX((f.h - H_RANGE[0]) / (H_RANGE[1] - H_RANGE[0])).toFixed(1)}px`;
      vKnob.style.left = `${knobX((f.v - V_RANGE[0]) / (V_RANGE[1] - V_RANGE[0])).toFixed(1)}px`;
      btn.pause.innerHTML = s.paused ? '▶ &nbsp;FLY' : '❚❚ &nbsp;HOLD';
      for (const k of CAMS) btn[k].classList.toggle('on', s.view === k);
      for (const k of OPENS) btn[k].classList.toggle('on', s.open === k);
      for (const k of SHOWS) btn[k].classList.toggle('on', !!s.show[k]);
      for (const [n, g] of MODULES) btn['m:' + g].classList.toggle('on', s.iso === g);
      modInfo.textContent = s.isoText;

      // one trigger: the trigger edge, four exposures, four read-outs. 0..80 ms across the panel.
      {
        const since = s.since * 1000, X = (ms) => 44 + (Math.min(80, ms) / 80) * 176;
        const names = ['TRIGGER', 'RGB', 'RED EDGE', 'NIR', 'EXT NIR'];
        let g = '';
        names.forEach((n, i) => {
          const y = 8 + i * 20;
          g += `<text x="0" y="${y + 8}" font-size="7.6" font-weight="600" fill="${C.mute}" letter-spacing=".8">${n}</text><line x1="44" y1="${y + 11}" x2="220" y2="${y + 11}" stroke="${C.line}"/>`;
          if (i === 0) g += `<rect x="44" y="${y}" width="2.4" height="11" fill="${C.ink}"/>`;
          else {
            const read = (i === 1 ? f.readRgb : f.readMira) * 1000, exp = f.texp * 1000;
            g += `<rect x="${X(0)}" y="${y}" width="${Math.max(2.2, X(exp) - X(0))}" height="11" fill="${C.acc}"/>`;
            g += `<rect x="${X(exp) + 1}" y="${y + 3}" width="${X(exp + read) - X(exp)}" height="8" fill="${BANDS[i === 1 ? 2 : i + 1].color}" opacity=".8"/>`;
          }
        });
        for (const ms of [0, 20, 40, 60, 80]) g += `<text x="${X(ms)}" y="116" font-size="7.2" fill="${C.mute}" text-anchor="middle">${ms}</text>`;
        if (since < 80) g += `<line x1="${X(since)}" y1="2" x2="${X(since)}" y2="106" stroke="${C.ink}" stroke-width="1"/>`;
        tl.innerHTML = g;
      }

      // the map: one column per stretch of ground flown, painted as the frames come in
      {
        const W = 452, Hh = 250, mPerPx = 0.75;
        const col = Math.floor(s.mapped / mPerPx);
        if (col < mapX) { mctx.clearRect(0, 0, W, Hh); mapX = -1; }
        const half = (f.swath / 2 / mPerPx) | 0;
        for (let c = mapX + 1; c <= col; c++) {
          const x = c % W;
          if (x === 0) mctx.clearRect(0, 0, W, Hh);
          for (let y = Math.max(0, 125 - half); y < Math.min(Hh, 125 + half); y += 2) {
            const [r, g, b] = ndviColor(ndvi(c * mPerPx, (y - 125) * mPerPx + 22));
            mctx.fillStyle = `rgb(${r},${g},${b})`;
            mctx.fillRect(x, y, 1, 2);
          }
        }
        mapX = col;
      }
    },
  };
}
