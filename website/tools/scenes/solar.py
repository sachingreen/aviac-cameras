#!/usr/bin/env python3
"""Procedural solar farm seen from above: an RGB view and a thermal view of the same rows. The thermal view is drawn
at 640 x 480 (a typical uncooled core) and scaled up, with a few typical anomalies placed as hotspot candidates.
Illustrative only: colours here are not radiometric temperatures."""
import numpy as np
from PIL import Image
from common import W, H, fbm, noise, hillshade, ramp, IRON, save, soften, blend

rng = np.random.default_rng(11)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)

# ---- ground: dry grass with gravel service tracks
g1 = fbm(H, W, 90, rng, 5); g2 = fbm(H, W, 4, rng, 3)
grass = np.stack([0.50 + 0.10 * g1, 0.50 + 0.06 * g1, 0.33 + 0.04 * g1], -1) * (0.82 + 0.36 * g2)[..., None]
road = np.clip(1 - np.abs(yy - 1090 - 12 * np.sin(xx / 260)) / 26, 0, 1)
road = np.maximum(road, np.clip(1 - np.abs(xx - 120) / 22, 0, 1))
gravel = np.array([0.66, 0.63, 0.58]) * (0.85 + 0.3 * fbm(H, W, 3, rng, 3))[..., None]
rgb = blend(grass, gravel, np.clip(road * 1.5, 0, 1))
gtemp = 0.36 + 0.06 * g1 + 0.08 * road                     # thermal: grass cool, gravel warmer

# ---- array: rows of tables, each 2 modules high (portrait), modules 30 x 54 px with 6 x 10 cells
MW, MH, GAP = 34, 60, 2
rows_y = np.arange(60, 1010, 160)
mod_id = -np.ones((H, W), int); cell = np.zeros((H, W)); frame = np.zeros((H, W)); mloc = {}
k = 0
for ry in rows_y:
    x = 175.0
    while x + 12 * (MW + GAP) < W - 40:
        for c in range(12):                                   # 12 modules wide, 2 high per table
            for r in range(2):
                x0 = int(x + c * (MW + GAP)); y0 = int(ry + r * (MH + GAP))
                mod_id[y0:y0 + MH, x0:x0 + MW] = k
                ly, lx = np.mgrid[0:MH, 0:MW]
                cx_ = (lx - 1) % ((MW - 2) / 6); cy_ = (ly - 1) % ((MH - 2) / 10)
                cell[y0:y0 + MH, x0:x0 + MW] = ((cx_ < 0.9) | (cy_ < 0.9)) * 1.0
                fr = (lx < 1) | (lx > MW - 2) | (ly < 1) | (ly > MH - 2)
                frame[y0:y0 + MH, x0:x0 + MW] = fr * 1.0
                mloc[k] = (x0, y0)
                k += 1
        x += 12 * (MW + GAP) + 14
panel = mod_id >= 0
# shadow: tables cast a band to the north (up) at morning sun
shadow = np.zeros((H, W))
for ry in rows_y:
    sh = np.clip(1 - np.abs(yy - (ry - 9)) / 9, 0, 1)
    shadow = np.maximum(shadow, sh * (np.convolve(panel[ry + 4].astype(float), np.ones(5) / 5, "same")[None, :] > 0.5))
shadow = soften(shadow * (1 - panel), 2)

# ---- RGB
sky = 0.5 + 0.5 * (xx / W) * 0.6 + 0.15 * noise(H, W, 400, rng)          # sky reflection gradient on the glass
glass = np.stack([0.06 + 0.05 * sky, 0.09 + 0.06 * sky, 0.17 + 0.09 * sky], -1)
glass = blend(glass, np.array([0.22, 0.26, 0.36]), cell * 0.55)
glass = blend(glass, np.array([0.74, 0.75, 0.77]), frame)
mod_tone = np.zeros((H, W))
for kk in range(k):
    x0, y0 = mloc[kk]; mod_tone[y0:y0 + MH, x0:x0 + MW] = rng.normal(0, 0.03)
glass = glass * (1 + mod_tone)[..., None]
# soiling streak on one table, visible in RGB
soil = np.clip(1 - np.abs(yy - 60 - 100) / 10, 0, 1) * (np.abs(xx - 900) < 120) * (fbm(H, W, 8, rng, 3) > 0.45) * panel
glass = blend(glass, np.array([0.45, 0.40, 0.33]), soil * 0.6)
rgb = blend(rgb, glass, panel * 1.0)
rgb = rgb * (1 - 0.5 * shadow)[..., None]
# inverter skids
for (ix, iy) in ((150, 380), (150, 830)):
    m = (np.abs(xx - ix) < 26) & (np.abs(yy - iy) < 16)
    rgb[m] = np.array([0.82, 0.83, 0.84]); gtemp[m] = 0.62
rgb = rgb * (1 + 0.025 * (rng.random((H, W)) - 0.5))[..., None]
save(np.clip(rgb, 0, 1), "solar_rgb")

# ---- thermal (relative, not calibrated): modules warm in sun, anomalies hotter
t = gtemp * (1 - 0.35 * shadow)
mt = 0.56 + 0.02 * (xx / W) + mod_tone * 0.12
t = np.where(panel, mt - 0.04 * frame, t)
picks = {}
def mod_at(fx, fy):
    best = min(mloc.items(), key=lambda kv: (kv[1][0] - fx * W) ** 2 + (kv[1][1] - fy * H) ** 2)
    return best
# 1 single-cell hotspot
kk, (x0, y0) = mod_at(0.30, 0.22); cx, cy = x0 + 12, y0 + 20
t = np.where((np.abs(xx - cx) < 4) & (np.abs(yy - cy) < 4), 0.98, t); picks["cell"] = (cx, cy)
# 2 bypass-diode substring: a third of one module
kk, (x0, y0) = mod_at(0.62, 0.52)
m = (xx >= x0) & (xx < x0 + MW // 3 + 1) & (yy >= y0) & (yy < y0 + MH)
t = np.where(m, 0.76, t); picks["substring"] = (x0 + 5, y0 + MH // 2)
# 3 whole module warm (open circuit)
kk, (x0, y0) = mod_at(0.80, 0.30)
m = (xx >= x0) & (xx < x0 + MW) & (yy >= y0) & (yy < y0 + MH)
t = np.where(m, 0.72, t); picks["module"] = (x0 + MW // 2, y0 + MH // 2)
# 4 a string of modules offline: half a table warm
kk, (x0, y0) = mod_at(0.42, 0.78)
m = (xx >= x0) & (xx < x0 + 6 * (MW + GAP)) & (yy >= y0) & (yy < y0 + MH) & panel
t = np.where(m, 0.68, t); picks["string"] = (x0 + 3 * (MW + GAP), y0 + MH // 2)
# 5 soiling: shaded cells run warm
t = np.where(soil > 0.3, t + 0.13 * soil, t)
picks["soiling"] = (900, 170)
# thermal camera look: render at 640 x 480, slight blur, then up-scale
small = np.asarray(Image.fromarray((np.clip(t, 0, 1) * 65535).astype(np.uint16)).resize((640, 480), Image.BOX)).astype(np.float64) / 65535
small = soften(small, 0.6) + (rng.random(small.shape) - 0.5) * 0.012
lo, hi = 0.28, 1.0
th_ = ramp((small - lo) / (hi - lo), IRON)
big = np.asarray(Image.fromarray((th_ * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float64) / 255
save(big, "solar_thermal")
print({kk: (round(v[0] / W * 100, 1), round(v[1] / H * 100, 1)) for kk, v in picks.items()})
