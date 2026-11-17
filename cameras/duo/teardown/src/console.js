// The overlay: a fixed 1600 x 900 layout of panels around the camera. update(s) redraws every live part from the
// frame's state; nothing here computes a number of its own. Layout pattern after the teardown kit's examples.
import {BANDS, BASELINE, FIELD, GAP, LID, MIRA, OVERLAP, PASS_LEN, POWER, AMBIENT, SSD_GB, SWATH, depthErrAt, sprayAt} from './sim.js';
import {ACCENT} from './machine.js';

export const C = {ink: '#16181b', mute: '#8b8f95', faint: '#c9ccd0', line: '#e1e3e6', panel: 'rgba(249,249,247,.94)', acc: ACCENT,
  spray: '#2f8fd8', miss: '#e2531a', a: '#7a3fd0', b: '#c2261f'};
export const CAMS = ['hero', 'underside', 'inside', 'lid'];
export const OPENS = ['closed', 'lid off', 'exploded'];
export const SHOWS = ['labels', 'footprints', 'signals', 'heat'];
export const MODULES = [['CAMERA A', 'Camera A (Mira220)'], ['CAMERA B', 'Camera B (Mira220)'], ['LENS PLATE', 'Optics bench'], ['CARRIER', 'Carrier board'],
  ['JETSON', 'Jetson Orin Nano'], ['FINNED LID', 'Thermal'], ['CLAMP', 'Mount']];
export const H_RANGE = [1.5, 6];
export const V_RANGE = [2, 8];

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
  const rows = (x, y, names) => names.map((n, i) => add(`<div class="rw" style="left:${x}px;top:${y + i * 17}px"><span class="mu">${n}</span><b></b></div>`).lastElementChild);
  const btn = {};

  // ------------------------------------------------------------ title and the key readout
  add(`<div style="position:absolute;left:35px;top:33px;width:43px;height:3px;background:${C.acc}"></div>`);
  add(`<div style="position:absolute;left:35px;top:47px;font-size:24px;font-weight:700;letter-spacing:-.2px">Aviac Duo <span style="color:${C.acc}">·</span> Spray-Check Camera</div>`);
  add(`<div class="cp" style="position:absolute;left:35px;top:81px;font-weight:500;letter-spacing:1.7px;font-size:9.4px">2 × MIRA220 &nbsp;•&nbsp; ${BASELINE * 1000} MM STEREO &nbsp;•&nbsp; JETSON ORIN NANO &nbsp;•&nbsp; NO FAN</div>`);
  const gsdBig = add(`<div style="position:absolute;left:33px;top:103px;font-size:56px;font-weight:800;letter-spacing:-3.2px;color:${C.acc};line-height:1"></div>`);
  add(`<div style="position:absolute;left:150px;top:128px;font-size:11px;font-weight:500;line-height:1.35">MM / PIXEL<br><span class="mu" style="letter-spacing:1px;font-size:9.4px">GROUND DETAIL</span></div>`);
  add(`<div style="position:absolute;left:35px;top:174px;width:247px;height:9px;background:#e6e7e9"></div>`);
  const gsdFill = add(`<div style="position:absolute;left:35px;top:174px;height:9px;background:${C.acc}"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:35px;top:188px;font-size:9px;font-weight:500">0</div>`);
  add(`<div class="cp" style="position:absolute;left:226px;top:188px;font-size:9px;font-weight:500">5 MM / PX</div>`);

  // ------------------------------------------------------------ flight
  add(`<div class="pn" style="left:35px;top:214px;width:247px;height:168px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:226px;font-weight:700">OVER THE CROP</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:226px;font-weight:500">${SWATH} M SPRAY SWATH</div>`);
  const fr = rows(46, 247, ['Frame on the ground', 'Share of the swath seen', 'Frame pair every', 'Shutter for ½-pixel blur', 'Work rate', 'Sync error on the ground', 'Spray card in the frame']);

  // ------------------------------------------------------------ trigger timeline
  add(`<div class="pn" style="left:35px;top:390px;width:247px;height:136px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:402px;font-weight:700">ONE TRIGGER</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:402px;font-weight:500">FIRST 20 MS</div>`);
  const tl = add(`<svg style="position:absolute;left:46px;top:420px" width="226" height="80"></svg>`);
  add(`<div style="position:absolute;left:46px;top:504px;font-size:9.5px;color:${C.mute}">Both shutters open within <b style="color:${C.ink}">50 µs</b> of each other</div>`);

  // ------------------------------------------------------------ spray coverage map
  add(`<div class="pn" style="left:35px;top:534px;width:247px;height:232px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:546px;font-weight:700">SPRAY COVERAGE</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:546px;font-weight:500">SIMULATED FIELD</div>`);
  const MW = 452, MH = 300;
  const mapC = add(`<canvas width="${MW}" height="${MH}" style="position:absolute;left:46px;top:564px;width:226px;height:150px;background:#e9eae5"></canvas>`);
  const dotC = add(`<canvas width="${MW}" height="${MH}" style="position:absolute;left:46px;top:564px;width:226px;height:150px"></canvas>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:720px;font-weight:500;font-size:8.6px"><i style="display:inline-block;width:12px;height:6px;background:${C.spray};opacity:.75;margin-right:5px"></i>SPRAYED &nbsp; <i style="display:inline-block;width:12px;height:6px;background:${C.miss};margin:0 5px 0 6px"></i>MISSED</div>`);
  const covTxt = add(`<div style="position:absolute;left:46px;top:738px;font-size:10px;width:226px"></div>`);

  // ------------------------------------------------------------ transport
  add(`<div class="pn" style="left:35px;top:774px;width:259px;height:111px"></div>`);
  btn.pause = add(`<div class="tb" style="left:45px;top:782px;width:99px;height:26px;background:${C.acc};color:#fff;border-color:${C.acc};font-size:9.6px"></div>`);
  btn.fire = add(`<div class="tb" style="left:149px;top:782px;width:136px;height:26px;font-size:9.6px">FIRE ONE PAIR</div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:818px;font-weight:500">HEIGHT ABOVE CROP</div>`);
  const hVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:818px;font-weight:700"></div>`);
  const SL = {x: 46, w: 238};
  add(`<div style="position:absolute;left:${SL.x}px;top:836px;width:${SL.w}px;height:2px;background:#e1e3e6"></div>`);
  const hKnob = add(`<div style="position:absolute;top:831px;width:9px;height:11px;margin-left:-4.5px;background:${C.acc}"></div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:851px;font-weight:500">GROUND SPEED</div>`);
  const vVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:851px;font-weight:700"></div>`);
  add(`<div style="position:absolute;left:${SL.x}px;top:869px;width:${SL.w}px;height:2px;background:#e1e3e6"></div>`);
  const vKnob = add(`<div style="position:absolute;top:864px;width:9px;height:11px;margin-left:-4.5px;background:${C.acc}"></div>`);

  // ------------------------------------------------------------ band legend
  add(`<div class="cp" style="position:absolute;left:0;right:0;top:36px;display:flex;justify-content:center;gap:16px;font-weight:500;font-size:9.6px">
    ${BANDS.map((b) => `<span><i style="display:inline-block;width:15px;height:2.4px;background:${b.color};vertical-align:middle;margin-right:6px"></i>${b.name.toUpperCase()} <span class="mu">${b.cam}</span></span>`).join('')}</div>`);

  // ------------------------------------------------------------ capture
  add(`<div class="pn" style="left:1318px;top:36px;width:245px;height:160px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:47px;font-weight:500">CAPTURE</div>`);
  const capRate = add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:47px;font-weight:500"></div>`);
  const frameBig = add(`<div style="position:absolute;left:1328px;top:62px;font-size:36px;font-weight:800;letter-spacing:-1.6px;color:${C.acc};line-height:1"></div>`);
  add(`<div style="position:absolute;left:1440px;top:72px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">FRAME PAIRS<br><span style="color:${C.mute};letter-spacing:1.5px">${Math.round(OVERLAP * 100)} % OVERLAP</span></div>`);
  add(`<div style="position:absolute;left:1329px;top:108px;width:224px;height:1px;background:${C.line}"></div>`);
  const cr = rows(1329, 116, ['One pair on disk, 16-bit', 'Written per second', `Flying time on ${SSD_GB} GB`, 'Read-out, 2 lanes']);

  // ------------------------------------------------------------ stereo depth
  add(`<div class="pn" style="left:1318px;top:204px;width:245px;height:196px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:215px;font-weight:700">STEREO DEPTH</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:215px;font-weight:500">${BASELINE * 1000} MM APART</div>`);
  const dBig = add(`<div style="position:absolute;left:1328px;top:232px;font-size:36px;font-weight:800;letter-spacing:-1.6px;line-height:1"></div>`);
  add(`<div style="position:absolute;left:1430px;top:241px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">CM DEPTH ERROR<br><span style="color:${C.mute};letter-spacing:1.5px">AT THE CROP</span></div>`);
  const dC = add(`<svg style="position:absolute;left:1326px;top:276px" width="232" height="120"></svg>`);

  // ------------------------------------------------------------ cooling
  add(`<div class="pn" style="left:1318px;top:408px;width:245px;height:170px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:419px;font-weight:700">COOLING, NO FAN</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:419px;font-weight:500">CALCULATED</div>`);
  const tBig = add(`<div style="position:absolute;left:1328px;top:436px;font-size:36px;font-weight:800;letter-spacing:-1.6px;line-height:1"></div>`);
  add(`<div style="position:absolute;left:1418px;top:445px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">°C LID ABOVE AIR<br><span style="color:${C.mute};letter-spacing:1.5px">JETSON AT ${POWER} W</span></div>`);
  add(`<div style="position:absolute;left:1329px;top:482px;width:224px;height:5px;background:#e6e7e9"></div>`);
  const tFill = add(`<div style="position:absolute;left:1329px;top:482px;height:5px;background:${C.acc}"></div>`);
  const tr = rows(1329, 498, ['Air over the lid', `Lid at ${AMBIENT} °C air`, 'SoC (estimate)', 'Finned area']);

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

  // the field map: metres -> canvas px
  const SCL = Math.min((MW - 20) / FIELD.w, (MH - 20) / FIELD.h);
  const OX = (MW - FIELD.w * SCL) / 2, OY = (MH - FIELD.h * SCL) / 2;
  const mctx = mapC.getContext('2d'), dctx = dotC.getContext('2d');
  let painted = -1, gapSeen = false;
  const resetMap = () => {
    mctx.clearRect(0, 0, MW, MH);
    mctx.fillStyle = '#dfe3d6';
    mctx.fillRect(OX, OY, FIELD.w * SCL, FIELD.h * SCL);
    mctx.strokeStyle = '#b9bdb0';
    mctx.lineWidth = 1;
    mctx.strokeRect(OX + 0.5, OY + 0.5, FIELD.w * SCL - 1, FIELD.h * SCL - 1);
    painted = 0;
    gapSeen = false;
  };
  resetMap();

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
      gsdBig.textContent = (f.gsd * 1000).toFixed(1);
      gsdFill.style.width = `${Math.min(1, (f.gsd * 1000) / 5) * 247}px`;
      fr[0].textContent = `${f.across.toFixed(1)} × ${f.along.toFixed(1)} m`;
      fr[1].textContent = `${Math.round(f.swathShare * 100)} %`;
      fr[2].textContent = `${(f.dt * 1000).toFixed(0)} ms`;
      fr[3].textContent = `1 / ${Math.round(1 / f.texp)} s`;
      fr[4].textContent = `${f.haPerHour.toFixed(1)} ha / h`;
      fr[5].textContent = `${(f.skewGround * 1000).toFixed(2)} mm`;
      fr[6].textContent = `${f.cardPx[0].toFixed(0)} × ${f.cardPx[1].toFixed(0)} px`;
      capRate.textContent = `${f.fps.toFixed(1)} PAIRS / S`;
      frameBig.textContent = String(s.frames).padStart(4, '0');
      cr[0].textContent = `${f.pairMB.toFixed(1)} MB`;
      cr[1].textContent = `${f.mbps.toFixed(0)} MB / s`;
      cr[2].textContent = `${f.minutes.toFixed(0)} min`;
      cr[3].textContent = `${(f.read * 1000).toFixed(1)} ms`;
      dBig.textContent = `± ${(f.depthErr * 100).toFixed(1)}`;
      tBig.textContent = `+${th.rise.toFixed(0)}`;
      tBig.style.color = th.rise > 25 ? C.acc : C.ink;
      tFill.style.width = `${Math.min(1, th.rise / 35) * 224}px`;
      tr[0].textContent = s.flying ? `${th.air.toFixed(1)} m / s` : 'still';
      tr[1].textContent = `${th.lid.toFixed(0)} °C`;
      tr[2].textContent = `${th.soc.toFixed(0)} °C`;
      tr[3].textContent = `${(LID.area * 1e4).toFixed(0)} cm²`;
      hVal.textContent = `${f.h.toFixed(1)} M`;
      vVal.textContent = `${f.v.toFixed(1)} M / S`;
      hKnob.style.left = `${knobX((f.h - H_RANGE[0]) / (H_RANGE[1] - H_RANGE[0])).toFixed(1)}px`;
      vKnob.style.left = `${knobX((f.v - V_RANGE[0]) / (V_RANGE[1] - V_RANGE[0])).toFixed(1)}px`;
      btn.pause.innerHTML = s.paused ? '▶ &nbsp;FLY' : '❚❚ &nbsp;HOLD';
      for (const k of CAMS) btn[k].classList.toggle('on', s.view === k);
      for (const k of OPENS) btn[k].classList.toggle('on', s.open === k);
      for (const k of SHOWS) btn[k].classList.toggle('on', !!s.show[k]);
      for (const [, g] of MODULES) btn['m:' + g].classList.toggle('on', s.iso === g);
      modInfo.textContent = s.isoText;

      // one trigger: the edge, two exposures, two read-outs, over 20 ms
      {
        const since = s.since * 1000, X = (ms) => 52 + (Math.min(20, ms) / 20) * 168;
        const names = [['TRIGGER', C.ink], ['CAMERA A', C.a], ['CAMERA B', C.b]];
        let g = '';
        names.forEach(([n, col], i) => {
          const y = 6 + i * 22;
          g += `<text x="0" y="${y + 8}" font-size="7.6" font-weight="600" fill="${C.mute}" letter-spacing=".8">${n}</text><line x1="52" y1="${y + 11}" x2="220" y2="${y + 11}" stroke="${C.line}"/>`;
          if (i === 0) g += `<rect x="52" y="${y}" width="2.4" height="11" fill="${C.ink}"/>`;
          else {
            const exp = f.texp * 1000, read = f.read * 1000;
            g += `<rect x="${X(0)}" y="${y}" width="${Math.max(2.2, X(exp) - X(0))}" height="11" fill="${C.acc}"/>`;
            g += `<rect x="${X(exp) + 1}" y="${y + 3}" width="${X(exp + read) - X(exp)}" height="8" fill="${col}" opacity=".8"/>`;
          }
        });
        for (const ms of [0, 5, 10, 15, 20]) g += `<text x="${X(ms)}" y="78" font-size="7.2" fill="${C.mute}" text-anchor="middle">${ms}</text>`;
        if (since < 20) g += `<line x1="${X(since)}" y1="2" x2="${X(since)}" y2="70" stroke="${C.ink}" stroke-width="1"/>`;
        tl.innerHTML = g;
      }

      // depth error against range, with the current height marked
      {
        const X = (z) => 30 + ((z - 1) / 7) * 190, Y = (cm) => 92 - Math.min(1, cm / 20) * 80;
        let g = `<line x1="30" y1="92" x2="220" y2="92" stroke="${C.faint}"/><line x1="30" y1="12" x2="30" y2="92" stroke="${C.faint}"/>`;
        for (const cm of [0, 10, 20]) g += `<text x="26" y="${Y(cm) + 3}" font-size="7.2" fill="${C.mute}" text-anchor="end">${cm}</text>`;
        for (const z of [1, 2, 4, 6, 8]) g += `<text x="${X(z)}" y="103" font-size="7.2" fill="${C.mute}" text-anchor="middle">${z} m</text>`;
        let d = '';
        for (let z = 1; z <= 8.001; z += 0.1) d += `${d ? 'L' : 'M'}${X(z).toFixed(1)} ${Y(depthErrAt(z) * 100).toFixed(1)}`;
        g += `<path d="${d}" fill="none" stroke="${C.ink}" stroke-width="1.4"/>`;
        const hx = X(f.h), hy = Y(f.depthErr * 100);
        g += `<line x1="${hx}" y1="${hy}" x2="${hx}" y2="92" stroke="${C.acc}" stroke-dasharray="2 2"/><circle cx="${hx}" cy="${hy}" r="3.2" fill="${C.acc}"/>`;
        g += `<text x="${Math.min(200, hx + 6)}" y="${hy - 6}" font-size="7.6" font-weight="600" fill="${C.acc}">${f.disp.toFixed(0)} px disparity</text>`;
        g += `<text x="30" y="116" font-size="7.8" fill="${C.mute}">0.25 px matching error · ${MIRA.f * 1000} mm lens</text>`;
        dC.innerHTML = g;
      }

      // spray coverage: paint the field from the last painted distance to now
      {
        const d = s.dist % (PASS_LEN * Math.floor(FIELD.h / SWATH));
        if (d < painted) resetMap();
        const step = 0.25;
        for (let x = painted; x < d; x += step) {
          const st = sprayAt(x);
          if (!st.onField) continue;
          if (st.inGap) gapSeen = true;
          mctx.fillStyle = st.spraying ? 'rgba(47,143,216,0.75)' : C.miss;
          mctx.fillRect(OX + st.x * SCL - 1, OY + (st.y - SWATH / 2) * SCL, 2.2, SWATH * SCL - 1);
        }
        painted = d;
        dctx.clearRect(0, 0, MW, MH);
        const now = sprayAt(s.dist);
        dctx.fillStyle = C.ink;
        dctx.beginPath(); dctx.arc(OX + now.x * SCL, OY + now.y * SCL, 4.5, 0, Math.PI * 2); dctx.fill();
        dctx.strokeStyle = C.ink; dctx.lineWidth = 1;
        dctx.strokeRect(OX + now.x * SCL - (f.along / 2) * SCL, OY + (now.y - f.across / 2) * SCL, f.along * SCL, f.across * SCL);
        const done = Math.min(1, d / (PASS_LEN * Math.floor(FIELD.h / SWATH)));
        covTxt.innerHTML = gapSeen
          ? `<b style="color:${C.miss}">Gap found:</b> ${GAP.to - GAP.from} m unsprayed on pass ${GAP.pass + 1}, pump off. <span class="mu">${Math.round(done * 100)} % flown.</span>`
          : `<span class="mu">Pass ${now.pass + 1}, ${Math.round(done * 100)} % of the field flown. No gaps yet.</span>`;
      }
    },
  };
}
