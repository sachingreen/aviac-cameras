// The numbers. Every panel and every moving thing on the page reads from these functions, so nothing on screen
// can disagree with anything else. Real units: metres, seconds, watts. No three.js in here.

export const MIRA = {name: 'ams OSRAM Mira220', px: [1600, 1400], pitch: 2.79e-6, f: 4e-3, bits: 12, lanes: 2, laneMbps: 1500};
export const BASELINE = 0.06;          // m, side by side
export const MATCH_PX = 0.25;          // stereo matching error, px
export const OVERLAP = 0.6;            // forward overlap between frame pairs
export const SKEW = 50e-6;             // trigger skew budget, s
export const SSD_GB = 256;
export const POWER = 15;               // Jetson mode in flight, W
export const AMBIENT = 40;             // degC
export const SWATH = 6.5;              // spray swath of the drone, m
export const LID = {area: 0.065, hStill: 12, hDown: 28};   // finned lid: area m2, still-air and downwash W/m2K

export const BANDS = [
  {name: 'Blue', nm: '~450 nm', cam: 'A', color: '#2f6fe0'},
  {name: 'Green', nm: '~550 nm', cam: 'A', color: '#2fa14b'},
  {name: 'Red', nm: '~650 nm', cam: 'A', color: '#d8382c'},
  {name: 'NIR', nm: '~850 nm', cam: 'A', color: '#6b1036'},
  {name: 'Your band', nm: 'twist-lock', cam: 'B', color: '#a3151f'},
];

const fov = (i) => 2 * Math.atan((MIRA.px[i] * MIRA.pitch) / (2 * MIRA.f));
export const FOV = {h: fov(0), v: fov(1)};
export const FPX = MIRA.f / MIRA.pitch;

/** Everything that follows from flying at height h (m) above the crop at speed v (m/s). */
export function flight(h, v) {
  const gsd = (h * MIRA.pitch) / MIRA.f;
  const across = 2 * h * Math.tan(FOV.h / 2);      // the cameras' long side runs across the flight line
  const along = 2 * h * Math.tan(FOV.v / 2);
  const dt = (along * (1 - OVERLAP)) / v;
  const texp = (0.5 * gsd) / v;                    // exposure that keeps motion blur at half a pixel
  const frameMB = MIRA.px[0] * MIRA.px[1] * 2 / 1e6;
  const pairMB = 2 * frameMB;
  const mbps = pairMB / dt;
  const disp = (FPX * BASELINE) / h;
  return {
    h, v, gsd, across, along, dt, fps: 1 / dt, texp, pairMB, mbps, minutes: (SSD_GB * 1000) / mbps / 60,
    swathShare: Math.min(1, across / SWATH),
    disp, depthErr: (h * h * MATCH_PX) / (FPX * BASELINE),
    read: (MIRA.px[0] * MIRA.px[1] * MIRA.bits) / 1e6 / (MIRA.lanes * MIRA.laneMbps),
    skewGround: v * SKEW,
    cardPx: [0.026 / gsd, 0.076 / gsd],            // a 26 x 76 mm water-sensitive card, in pixels
    haPerHour: (SWATH * v * 3600) / 1e4,
  };
}
export const depthErrAt = (z) => (z * z * MATCH_PX) / (FPX * BASELINE);

/** Passive lid: heat-transfer coefficient rises with the air the rotors and the flight push over it. */
export function thermal(v, flying, power = POWER) {
  const air = flying ? 4 + v * 0.6 : 0;           // downwash plus forward flight, m/s (rough)
  const h = LID.hStill + (LID.hDown - LID.hStill) * Math.min(1, air / 5);
  const rise = power / (h * LID.area);
  return {air, h, rise, lid: AMBIENT + rise, soc: AMBIENT + rise + power * 0.9};
}

// ---------------------------------------------------------------- the spray job the page simulates
// The drone flies back and forth over a 60 m x 52 m field in 6.5 m swaths. On pass 4 the pump drops out for 9 m:
// that is the gap the coverage map has to find. Distances in metres along the whole path.
export const FIELD = {w: 60, h: 52};
export const PASSES = Math.floor(FIELD.h / SWATH);
const TURN = 3.5;                                  // turn-around distance between passes
export const PASS_LEN = FIELD.w + TURN;
export const PATH_LEN = PASSES * PASS_LEN;
export const GAP = {pass: 3, from: 31, to: 40};    // 0-based pass index, metres along that pass

/** Position on the field and whether the pump is spraying, for a distance d travelled along the path. */
export function sprayAt(d) {
  const dd = ((d % PATH_LEN) + PATH_LEN) % PATH_LEN;
  const pass = Math.floor(dd / PASS_LEN);
  const s = dd - pass * PASS_LEN;
  const onField = s <= FIELD.w;
  const x = pass % 2 === 0 ? Math.min(s, FIELD.w) : FIELD.w - Math.min(s, FIELD.w);
  const y = SWATH * (pass + 0.5);
  const inGap = pass === GAP.pass && s >= GAP.from && s <= GAP.to;
  return {pass, s, x, y, onField, spraying: onField && !inGap, inGap};
}

// crop vigour for the ground texture
const h2 = (x, y) => {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
};
const vn = (x, y) => {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
  return (h2(xi, yi) * (1 - u) + h2(xi + 1, yi) * u) * (1 - w) + (h2(xi, yi + 1) * (1 - u) + h2(xi + 1, yi + 1) * u) * w;
};
export function vigour(xm, ym) {
  return Math.min(0.95, Math.max(0.1, 0.35 + 0.55 * (vn(xm / 9, ym / 7) * 0.7 + vn(xm / 2.5 + 9, ym / 2.1 + 4) * 0.3)));
}
