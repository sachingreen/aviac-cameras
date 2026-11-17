// The overlay: a fixed 1600 x 900 layout of panels around the camera. update(s) redraws every live part from the
// frame's state; nothing here computes a number of its own. Layout pattern after the teardown kit's examples.
import {BANDS, LID, RGB, MIRA_QE, OVERLAP, SSD_GB, POWER, AMBIENT, ndvi, ndviColor} from './sim.js';
import {ACCENT} from './machine.js';
import {CLASSES} from './farm.js';

export const C = {ink: '#e9f3fb', mute: '#7f95aa', faint: '#3b4d61', line: 'rgba(120,200,255,.16)', panel: 'rgba(7,13,22,.58)', acc: ACCENT, cyan: '#38e1ff', blue: '#3d8fe0'};
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
.pn{position:absolute;background:linear-gradient(160deg,rgba(14,24,40,.62),rgba(5,10,18,.52));border:1px solid rgba(120,200,255,.14);border-radius:3px;
  backdrop-filter:blur(14px) saturate(140%);-webkit-backdrop-filter:blur(14px) saturate(140%);box-shadow:0 0 0 1px rgba(0,0,0,.25),0 18px 40px -18px rgba(0,0,0,.8),inset 0 1px 0 rgba(160,220,255,.08)}
.pn::before,.pn::after{content:'';position:absolute;width:10px;height:10px;border-color:${C.cyan};border-style:solid;opacity:.85;filter:drop-shadow(0 0 4px ${C.cyan})}
.pn::before{left:-1px;top:-1px;border-width:1.5px 0 0 1.5px}
.pn::after{right:-1px;bottom:-1px;border-width:0 1.5px 1.5px 0}
.cp{font-size:9.6px;font-weight:600;letter-spacing:1.6px;text-transform:uppercase;white-space:nowrap;font-family:'Space Grotesk',Inter,sans-serif}
.mu{color:${C.mute}}
.tb{position:absolute;box-sizing:border-box;height:19px;padding:0 4px;display:flex;align-items:center;justify-content:center;font:600 8.8px 'Space Grotesk',Inter,sans-serif;letter-spacing:1.1px;text-transform:uppercase;
  border:1px solid rgba(120,200,255,.22);background:rgba(10,20,34,.55);color:#cfe6f5;white-space:nowrap;border-radius:2px;transition:all .25s;backdrop-filter:blur(8px)}
.tb.on{background:linear-gradient(90deg,rgba(56,225,255,.95),rgba(80,160,255,.95));color:#031018;border-color:${C.cyan};box-shadow:0 0 14px rgba(56,225,255,.55)}
.rw{position:absolute;display:flex;justify-content:space-between;font-size:10.5px;width:225px}
.rw b{font-weight:600;font-family:'JetBrains Mono',monospace;font-size:10.2px;color:#f2f8fc}
.big{background:linear-gradient(180deg,#ffffff 10%,${C.cyan} 95%);-webkit-background-clip:text;background-clip:text;color:transparent!important;filter:drop-shadow(0 0 14px rgba(56,225,255,.35));font-family:'Space Grotesk',Inter,sans-serif}
.big.hot{background:linear-gradient(180deg,#ffe2d2 0%,${C.acc} 90%);-webkit-background-clip:text;background-clip:text;filter:drop-shadow(0 0 14px rgba(255,107,44,.45))}
.fill{background:linear-gradient(90deg,${C.cyan},#7a8cff 60%,${C.acc});box-shadow:0 0 12px rgba(56,225,255,.6)}
.knob{background:${C.cyan}!important;box-shadow:0 0 10px ${C.cyan};border-radius:2px}
.call{position:absolute;white-space:nowrap;padding:4px 8px;background:rgba(6,12,22,.55);border-left:2px solid ${C.cyan};backdrop-filter:blur(6px)}
.call b{display:block;font:600 12px 'Space Grotesk',Inter,sans-serif;letter-spacing:.2px;color:#fff}
.call span{display:block;font-size:8.6px;font-weight:500;letter-spacing:1.4px;color:${C.mute};text-transform:uppercase;margin-top:2px}
.cur{position:absolute;left:0;top:0;z-index:50;filter:drop-shadow(0 0 6px rgba(56,225,255,.6))}
.ring{position:absolute;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;border:1.5px solid ${C.cyan};box-shadow:0 0 12px ${C.cyan};opacity:0;z-index:49}
.callsvg line{filter:drop-shadow(0 0 3px rgba(56,225,255,.9))}
.tag{position:absolute;transform:translate(-50%,-100%);margin-top:-6px;padding:4px 8px 4px 9px;background:rgba(4,10,18,.72);border:1px solid var(--c);border-radius:2px;white-space:nowrap;
  box-shadow:0 0 14px color-mix(in srgb,var(--c) 45%,transparent);backdrop-filter:blur(6px)}
.tag::after{content:'';position:absolute;left:50%;top:100%;width:1px;height:6px;background:var(--c)}
.tag b{display:block;font:700 9px 'Space Grotesk',Inter,sans-serif;letter-spacing:1.3px;color:var(--c)}
.tag span{display:block;font:500 8.4px 'JetBrains Mono',monospace;color:#cfe2ee;margin-top:1px}
.live{display:inline-block;width:6px;height:6px;border-radius:50%;background:${C.acc};box-shadow:0 0 8px ${C.acc};margin-right:6px;animation:pulse 1.4s infinite}
@keyframes pulse{50%{opacity:.25}}
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
  add(`<div style="position:absolute;left:35px;top:33px;width:64px;height:2px;background:linear-gradient(90deg,${C.cyan},${C.acc});box-shadow:0 0 10px ${C.cyan}"></div>`);
  add(`<div style="position:absolute;left:35px;top:45px;font:700 26px 'Space Grotesk',Inter,sans-serif;letter-spacing:-.3px;text-shadow:0 0 24px rgba(56,225,255,.25)">Aviac 6B <span style="color:${C.acc}">·</span> Six-Band Crop Camera</div>`);
  add(`<div class="cp" style="position:absolute;left:35px;top:81px;font-weight:500;letter-spacing:1.7px;font-size:9.4px">IMX565 + 3 × MIRA220 &nbsp;•&nbsp; 2 × 2 GRID &nbsp;•&nbsp; HARD-ANODISED ALUMINIUM &nbsp;•&nbsp; NO FAN</div>`);
  const gsdBig = add(`<div style="position:absolute;left:33px;top:103px;font-size:58px;font-weight:700;letter-spacing:-2.6px;line-height:1" class="big"></div>`);
  add(`<div style="position:absolute;left:178px;top:128px;font-size:11px;font-weight:500;line-height:1.35">CM / PIXEL<br><span class="mu" style="letter-spacing:1px;font-size:9.4px">GROUND DETAIL, RGB</span></div>`);
  add(`<div style="position:absolute;left:35px;top:174px;width:247px;height:9px;background:rgba(120,200,255,.10)"></div>`);
  const gsdFill = add(`<div class="fill" style="position:absolute;left:35px;top:174px;height:9px"></div>`);
  const gsdMath = add(`<div style="position:absolute;left:35px;top:188px;width:260px;font:500 9.2px 'JetBrains Mono',monospace;color:#9fb6c9;white-space:nowrap"></div>`);

  // ------------------------------------------------------------ flight
  add(`<div class="pn" style="left:35px;top:214px;width:247px;height:168px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:226px;font-weight:700">FLIGHT</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:226px;font-weight:500">${Math.round(OVERLAP * 100)} % FORWARD OVERLAP</div>`);
  const fr = rows(46, 247, ['Detail, NIR bands', 'Swath width', 'Frame length on ground', 'Trigger every', 'Shutter for ½-pixel blur', 'Coverage', 'Sync error on ground']);

  // ------------------------------------------------------------ detections
  add(`<div class="pn" style="left:35px;top:390px;width:247px;height:178px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:402px;font-weight:700"><i class="live"></i>FIELD DETECTIONS</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:402px;font-weight:500">ON-BOARD · LIVE</div>`);
  const detRows = CLASSES.map((c, i) => {
    const y = 424 + i * 21;
    add(`<div style="position:absolute;left:46px;top:${y + 3}px;width:8px;height:8px;border-radius:2px;background:${c.color};box-shadow:0 0 8px ${c.color}"></div>`);
    add(`<div style="position:absolute;left:62px;top:${y}px;font:600 10.6px 'Space Grotesk',Inter,sans-serif;letter-spacing:.3px;color:#e9f3fb">${c.name}</div>`);
    return add(`<div style="position:absolute;right:${1600 - 271}px;top:${y - 2}px;font:600 14px 'JetBrains Mono',monospace;color:${c.color};text-shadow:0 0 10px ${c.color}">0</div>`);
  });
  add(`<div style="position:absolute;left:46px;top:511px;width:225px;height:1px;background:rgba(120,200,255,.16)"></div>`);
  const detLast = add(`<div style="position:absolute;left:46px;top:518px;width:225px;font-size:10px;line-height:1.45"></div>`);

  // ------------------------------------------------------------ survey mission: a 640-acre block flown in passes
  const BLOCK_AC = 640, BLOCK_M = Math.sqrt(BLOCK_AC * 4046.86);       // one square mile
  add(`<div class="pn" style="left:35px;top:576px;width:247px;height:190px"></div>`);
  add(`<div class="cp" style="position:absolute;left:46px;top:588px;font-weight:700"><i class="live"></i>SURVEY MISSION</div>`);
  add(`<div class="cp mu" style="position:absolute;right:${1600 - 271}px;top:588px;font-weight:500">${BLOCK_AC}-ACRE BLOCK</div>`);
  const MP = 260;
  const mapC = add(`<canvas width="${MP}" height="${MP}" style="position:absolute;left:46px;top:606px;width:130px;height:130px;background:rgba(120,200,255,.06);outline:1px solid rgba(120,200,255,.25)"></canvas>`);
  const mapO = add(`<canvas width="${MP}" height="${MP}" style="position:absolute;left:46px;top:606px;width:130px;height:130px"></canvas>`);
  const acBig = add(`<div class="big" style="position:absolute;left:186px;top:606px;font-size:26px;font-weight:700;letter-spacing:-.8px;line-height:1"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:187px;top:634px;font-size:8.4px;font-weight:500">ACRES SURVEYED</div>`);
  const ms = [650, 676, 702].map((y) => add(`<div style="position:absolute;left:187px;top:${y}px;font:600 11px 'JetBrains Mono',monospace;color:#f2f8fc"></div>`));
  const msl = ['DONE', 'PASS', 'TIME LEFT'];
  [662, 688, 714].forEach((y, i) => add(`<div class="cp mu" style="position:absolute;left:187px;top:${y}px;font-size:7.8px;font-weight:500">${msl[i]}</div>`));
  add(`<div style="position:absolute;left:46px;top:744px;width:130px;height:5px;background:linear-gradient(90deg,rgb(150,92,60),rgb(214,170,70),rgb(196,205,90),rgb(96,170,78),rgb(22,104,58))"></div>`);
  add(`<div class="cp mu" style="position:absolute;left:46px;top:752px;font-size:7.6px;font-weight:500">NDVI · STRESSED → VIGOROUS</div>`);

  // ------------------------------------------------------------ transport
  add(`<div class="pn" style="left:35px;top:774px;width:259px;height:111px"></div>`);
  const btn = {};
  btn.pause = add(`<div class="tb" style="left:45px;top:782px;width:99px;height:26px;background:linear-gradient(90deg,#ff6b2c,#ff9a3c);color:#160800;border-color:#ff8a3a;box-shadow:0 0 16px rgba(255,107,44,.55);font-size:9.6px"></div>`);
  btn.fire = add(`<div class="tb" style="left:149px;top:782px;width:136px;height:26px;font-size:9.6px">FIRE ONE FRAME</div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:818px;font-weight:500">HEIGHT ABOVE CROP</div>`);
  const hVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:818px;font-weight:700"></div>`);
  const SL = {x: 46, w: 238};
  add(`<div style="position:absolute;left:${SL.x}px;top:836px;width:${SL.w}px;height:2px;background:rgba(120,200,255,.18)"></div>`);
  const hKnob = add(`<div style="position:absolute;top:831px;width:9px;height:11px;margin-left:-4.5px" class="knob"></div>`);
  add(`<div class="cp" style="position:absolute;left:45px;top:851px;font-weight:500">AIRSPEED</div>`);
  const vVal = add(`<div class="cp" style="position:absolute;right:${1600 - 284}px;top:851px;font-weight:700"></div>`);
  add(`<div style="position:absolute;left:${SL.x}px;top:869px;width:${SL.w}px;height:2px;background:rgba(120,200,255,.18)"></div>`);
  const vKnob = add(`<div style="position:absolute;top:864px;width:9px;height:11px;margin-left:-4.5px" class="knob"></div>`);

  // ------------------------------------------------------------ band legend
  add(`<div class="cp" style="position:absolute;left:0;right:0;top:36px;display:flex;justify-content:center;gap:16px;font-weight:500;font-size:9.6px">
    ${BANDS.map((b) => `<span><i style="display:inline-block;width:15px;height:2.4px;background:${b.color};vertical-align:middle;margin-right:6px"></i>${b.name.toUpperCase()}</span>`).join('')}</div>`);

  // ------------------------------------------------------------ capture
  add(`<div class="pn" style="left:1318px;top:36px;width:245px;height:176px"></div>`);
  add(`<div class="cp" style="position:absolute;left:1329px;top:47px;font-weight:500">CAPTURE</div>`);
  const capRate = add(`<div class="cp mu" style="position:absolute;right:${1600 - 1552}px;top:47px;font-weight:500"></div>`);
  const frameBig = add(`<div class="big" style="position:absolute;left:1328px;top:62px;font-size:36px;font-weight:700;letter-spacing:-1.2px;line-height:1"></div>`);
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
  const tBig = add(`<div class="big" style="position:absolute;left:1328px;top:428px;font-size:36px;font-weight:700;letter-spacing:-1.2px;line-height:1"></div>`);
  add(`<div style="position:absolute;left:1418px;top:438px;font-size:10.5px;font-weight:500;letter-spacing:1px;line-height:1.35">°C FINNED LID<br><span style="color:${C.mute};letter-spacing:1.5px">${POWER} W AT ${AMBIENT} °C AIR</span></div>`);
  add(`<div style="position:absolute;left:1329px;top:476px;width:224px;height:5px;background:rgba(120,200,255,.10)"></div>`);
  const tFill = add(`<div class="fill" style="position:absolute;left:1329px;top:476px;height:5px"></div>`);
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
  const tagG = add(`<div style="position:absolute;inset:0"></div>`);
  const callSvg = add(`<svg class="callsvg" style="position:absolute;inset:0;overflow:visible" width="1600" height="900"></svg>`);
  const callG = add(`<div style="position:absolute;inset:0"></div>`);
  const ring = add(`<div class="ring"></div>`);
  const cur = add(`<div class="cur"><svg width="22" height="22" viewBox="0 0 34 34"><path d="M4 3 L30 13.5 L17.5 17.5 L13.5 30 Z" fill="#e9fbff" stroke="#38e1ff" stroke-width="2.2" stroke-linejoin="round"/></svg></div>`);
  const centre = (n) => [n.offsetLeft + n.offsetWidth / 2, n.offsetTop + n.offsetHeight / 2];
  const spots = Object.fromEntries(Object.entries(btn).map(([k, n]) => [k, centre(n)]));
  const knobX = (k) => SL.x + k * SL.w;
  const mctx = mapC.getContext('2d'), octx = mapO.getContext('2d');
  let mapD = 0, seenDet = 0;
  const pinsReset = () => {};
  const pins = [];

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
    /** tags: [{at:[x,y] screen px, cls, conf, area, a}] - floating labels over the detections */
    tags(list) {
      tagG.innerHTML = list.filter((t) => t.at && t.at[1] > 110 && t.at[1] < 770 && t.at[0] > 300 && t.at[0] < 1300).map((t) =>
        `<div class="tag" style="left:${t.at[0].toFixed(0)}px;top:${t.at[1].toFixed(0)}px;opacity:${t.a.toFixed(2)};--c:${t.cls.color}"><b>${t.cls.short}</b><span>${Math.round(t.conf * 100)} % · ${(t.area * 1e4).toFixed(0)} m²</span></div>`).join('');
    },
    /** calls: [{at:[x,y] screen px of the part, to:[x,y] label corner, title, sub, a: 0..1}] */
    callouts(calls) {
      let s = '', h = '';
      for (const c of calls) {
        if (!c.at || c.a < 0.02) continue;
        const right = c.to[0] > c.at[0];
        const ex = c.to[0] + (right ? -6 : 6);
        s += `<g opacity="${c.a.toFixed(2)}"><line x1="${c.at[0].toFixed(1)}" y1="${c.at[1].toFixed(1)}" x2="${ex}" y2="${c.to[1] + 7}" stroke="${C.cyan}" stroke-width=".9" stroke-opacity=".85"/><circle cx="${c.at[0].toFixed(1)}" cy="${c.at[1].toFixed(1)}" r="6" fill="none" stroke="${C.cyan}" stroke-opacity=".5"/><circle cx="${c.at[0].toFixed(1)}" cy="${c.at[1].toFixed(1)}" r="2.6" fill="${c.hot ? C.acc : C.cyan}"/></g>`;
        h += `<div class="call" style="opacity:${c.a.toFixed(2)};top:${c.to[1]}px;${right ? `left:${c.to[0]}px` : `right:${1600 - c.to[0]}px;text-align:right`}"><b>${c.title}</b><span>${c.sub}</span></div>`;
      }
      callSvg.innerHTML = s;
      callG.innerHTML = h;
    },
    update(s) {
      const f = s.fl, th = s.th;
      gsdBig.textContent = (f.gsdRgb * 100).toFixed(2);
      gsdMath.innerHTML = `GSD = <b style="color:#fff">${f.h.toFixed(0)} m</b> × ${(RGB.pitch * 1e6).toFixed(2)} µm ÷ ${(RGB.f * 1e3).toFixed(0)} mm = <b style="color:${C.cyan}">${(f.gsdRgb * 100).toFixed(2)} cm</b>`;
      gsdFill.style.width = `${Math.min(1, (f.gsdRgb * 100) / 3) * 247}px`;
      fr[0].textContent = `${(f.gsdMira * 100).toFixed(1)} cm / px`;
      fr[1].textContent = `${f.swath.toFixed(0)} m`;
      fr[2].textContent = `${f.along.toFixed(0)} m`;
      fr[3].textContent = `${(f.dt * 1000).toFixed(0)} ms`;
      fr[4].textContent = `1 / ${Math.round(1 / f.texp)} s`;
      fr[5].textContent = `${(f.haPerHour * 2.471).toFixed(0)} acres / h`;
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
      tBig.classList.toggle('hot', hot);
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

      // detections
      if (s.det) {
        CLASSES.forEach((c, i) => (detRows[i].textContent = String(s.det.counts[c.key])));
        const e = s.det.log[0];
        detLast.innerHTML = e
          ? `<b style="font:700 10.4px 'Space Grotesk',Inter,sans-serif;letter-spacing:1px;color:${e.cls.color}">${e.cls.short}</b> <span class="mu">· ${Math.round(e.conf * 100)} % confidence</span><br>` +
            `<span class="mu">${e.cls.note} · ${(e.area * 1e4).toFixed(0)} m²</span>`
          : `<span class="mu">Scanning the crop for stress, pests and gaps…</span>`;
      }

      // the survey: lawnmower passes across the block, 30 % side overlap, painted as NDVI as the frames come in
      {
        const sw = f.swath * 0.7, passes = Math.ceil(BLOCK_M / sw), pw = MP / passes, k = MP / BLOCK_M;
        const total = passes * BLOCK_M;
        let d = s.mapped % total;
        if (d < mapD) { mctx.clearRect(0, 0, MP, MP); pins.length = 0; mapD = 0; }
        const at = (dd) => {
          const pass = Math.floor(dd / BLOCK_M), along = dd - pass * BLOCK_M;
          return [pass % 2 ? BLOCK_M - along : along, pass];
        };
        for (let x = mapD; x < d; x += 4) {
          const [u, pass] = at(x);
          const [r, g, b] = ndviColor(ndvi(u, pass * sw * 0.8));
          mctx.fillStyle = `rgb(${r},${g},${b})`;
          mctx.fillRect(u * k - 1, pass * pw, 2.6, pw + 0.4);
        }
        mapD = d;
        const [u, pass] = at(d);
        const cx = u * k, cy = (pass + 0.5) * pw;
        if (s.det) for (; seenDet < s.det.events.length; seenDet++) {
          const e = s.det.events[seenDet], [pu, pp] = at(e.d % total);
          pins.push([pu * k, (pp + 0.5) * pw, e.cls.color]);
        }
        octx.clearRect(0, 0, MP, MP);
        for (const [px, py, c] of pins) {
          octx.fillStyle = c; octx.shadowColor = c; octx.shadowBlur = 8;
          octx.beginPath(); octx.arc(px, py, 4, 0, Math.PI * 2); octx.fill();
        }
        octx.shadowBlur = 12; octx.shadowColor = '#38e1ff'; octx.strokeStyle = '#38e1ff'; octx.lineWidth = 2;
        octx.strokeRect(cx - 6, cy - pw / 2 - 2, 12, pw + 4);
        octx.shadowBlur = 0;
        const acres = (d * f.swath * 0.7) / 4046.86;
        acBig.textContent = acres.toFixed(acres < 100 ? 1 : 0);
        ms[0].textContent = `${((d / total) * 100).toFixed(1)} %`;
        ms[1].textContent = `${pass + 1} / ${passes}`;
        ms[2].textContent = `${Math.max(0, (total - d) / f.v / 60).toFixed(0)} min`;
      }
    },
  };
}
