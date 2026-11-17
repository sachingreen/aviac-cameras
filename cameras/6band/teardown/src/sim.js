// The numbers. Every panel and every moving thing on the page reads from these functions, so nothing on screen
// can disagree with anything else. Real units: metres, seconds, watts, kelvin. No three.js in here.

export const RGB = {name: 'Sony IMX565', px: [4128, 3008], pitch: 2.74e-6, f: 16e-3, bits: 12, lanes: 2, laneMbps: 1188, mount: 'C-mount'};
export const MIRA = {name: 'ams OSRAM Mira220', px: [1600, 1400], pitch: 2.79e-6, f: 6e-3, bits: 12, lanes: 2, laneMbps: 1500, mount: 'CS-mount'};
export const OVERLAP = 0.8;          // forward overlap between consecutive frames
export const SKEW = 50e-6;           // trigger skew budget across the four sensors, s
export const SSD_GB = 256;
export const POWER = 25;             // module at MAXN_SUPER, W (design load)
export const AMBIENT = 40;           // degC (design ambient)

export const BANDS = [
  {key: 'B', name: 'Blue', lo: 420, hi: 500, peak: 460, sensor: 'IMX565', color: '#2f6fe0'},
  {key: 'G', name: 'Green', lo: 500, hi: 590, peak: 540, sensor: 'IMX565', color: '#2fa14b'},
  {key: 'R', name: 'Red', lo: 590, hi: 680, peak: 625, sensor: 'IMX565', color: '#d8382c'},
  {key: 'RE', name: 'Red edge', lo: 717, hi: 730, peak: 723, sensor: 'Mira220', color: '#a3151f'},
  {key: 'NIR', name: 'NIR', lo: 830, hi: 850, peak: 840, sensor: 'Mira220', color: '#6b1036'},
  {key: 'XNIR', name: 'Ext. NIR', lo: 860, hi: 920, peak: 890, sensor: 'Mira220', color: '#43103f'},
];
// Mira220 mono quantum efficiency, the three points the datasheet states
export const MIRA_QE = [[550, 0.95], [850, 0.56], [940, 0.36]];

const fov = (s, i) => 2 * Math.atan((s.px[i] * s.pitch) / (2 * s.f));
export const FOV = {rgbH: fov(RGB, 0), rgbV: fov(RGB, 1), miraH: fov(MIRA, 0), miraV: fov(MIRA, 1)};
const frameMbit = (s) => (s.px[0] * s.px[1] * s.bits) / 1e6;
const fileMB = (s) => (s.px[0] * s.px[1] * 2) / 1e6;          // stored as 16-bit TIFF

/** Everything that follows from flying at height h (m) and airspeed v (m/s). */
export function flight(h, v) {
  const gsdRgb = (h * RGB.pitch) / RGB.f;
  const gsdMira = (h * MIRA.pitch) / MIRA.f;
  const swath = 2 * h * Math.tan(FOV.rgbH / 2);                 // across track, set by the RGB frame
  const along = 2 * h * Math.tan(FOV.rgbV / 2);
  const dt = (along * (1 - OVERLAP)) / v;                       // trigger interval
  const texp = (0.5 * gsdRgb) / v;                              // exposure that keeps motion blur at half an RGB pixel
  const mbTrig = fileMB(RGB) + 3 * fileMB(MIRA);
  const mbps = mbTrig / dt;
  return {
    h, v, gsdRgb, gsdMira, swath, along, dt, fps: 1 / dt, texp,
    skewGround: v * SKEW,
    readRgb: frameMbit(RGB) / (RGB.lanes * RGB.laneMbps),
    readMira: frameMbit(MIRA) / (MIRA.lanes * MIRA.laneMbps),
    mbitRgb: frameMbit(RGB), mbitMira: frameMbit(MIRA),
    mbTrig, mbps, minutes: (SSD_GB * 1000) / mbps / 60,
    haPerHour: (swath * 0.7 * v * 3600) / 1e4,                  // 30 % side overlap
  };
}

// Cooling: a finned heatsink in a duct fed by ram air. Fully developed laminar flow between parallel fins
// (Nu = 7.54), heat-exchanger effectiveness for a constant-temperature wall. Calculated, not yet measured.
// Passive finned lid, no fan, no duct. Fins run fore and aft, so the flight air runs straight along them.
// Area from the CAD model: 22 fins x 9 mm x 102 mm both sides plus the base. The heat-transfer coefficient rises
// from about 12 W/m2K in still air with the airspeed; the slope is a rough forced-convection figure, not a test.
export const LID = {area: 0.052, hStill: 12, perMs: 1.6};
export function thermal(v, flying = true, power = POWER, ambient = AMBIENT) {
  const air = flying ? v : 0;
  const h = LID.hStill + LID.perMs * air;
  const rise = power / (h * LID.area);
  const lid = ambient + rise;
  return {air, h, rise, lid, plate: lid + power * 0.9, groundPlate: ambient + power / (LID.hStill * LID.area) + power * 0.9};
}

/** Crop vigour for the ground texture, 0..1. */
export const vigour = (xm, ym) => ndvi(xm, ym);

const h2 = (x, y) => {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return s - Math.floor(s);
};
const vn = (x, y) => {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
  return (h2(xi, yi) * (1 - u) + h2(xi + 1, yi) * u) * (1 - w) + (h2(xi, yi + 1) * (1 - u) + h2(xi + 1, yi + 1) * u) * w;
};
export function ndvi(xm, ym) {
  const big = vn(xm / 46, ym / 38) * 0.65 + vn(xm / 13 + 9, ym / 11 + 4) * 0.35;
  const row = 0.5 + 0.5 * Math.cos((ym / 0.75) * Math.PI * 2);
  const stress = Math.max(0, 1 - Math.hypot(xm % 170 - 85, ym - 22) / 30);
  return Math.min(0.95, Math.max(0.05, 0.28 + 0.6 * big - 0.42 * stress * stress + 0.08 * row));
}
export function ndviColor(n) {
  // brown -> yellow -> green
  const stops = [[0.1, [150, 92, 60]], [0.35, [214, 170, 70]], [0.55, [196, 205, 90]], [0.72, [96, 170, 78]], [0.92, [22, 104, 58]]];
  for (let i = 0; i < stops.length - 1; i++) {
    const [a, ca] = stops[i], [b, cb] = stops[i + 1];
    if (n <= b) {
      const k = Math.min(1, Math.max(0, (n - a) / (b - a)));
      return ca.map((c, j) => Math.round(c + (cb[j] - c) * k));
    }
  }
  return stops[stops.length - 1][1];
}
