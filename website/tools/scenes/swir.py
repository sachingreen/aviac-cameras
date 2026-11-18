#!/usr/bin/env python3
"""Procedural industrial roof: a hazy visible view and a SWIR view (around 1450 nm, where water absorbs strongly).
Wet insulation under the membrane, a ponding area and a leaking pipe run read dark in SWIR, and the haze mostly
drops out. Illustrative only."""
import numpy as np
from common import W, H, fbm, noise, hillshade, save, soften, blend

rng = np.random.default_rng(23)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
f1, f2 = fbm(H, W, 120, rng, 5), fbm(H, W, 3, rng, 3)

# membrane: light grey sheets with seams every 90 px, parapet around the edge
mem = 0.66 + 0.05 * f1 + 0.05 * (f2 - 0.5)
seam = (np.mod(yy + 3 * np.sin(xx / 300), 90) < 2.0) * 1.0
roof = np.clip(np.minimum.reduce([xx - 40, W - 40 - xx, yy - 40, H - 40 - yy]) / 1.0, 0, 1)
parapet = ((np.minimum.reduce([xx - 40, W - 40 - xx, yy - 40, H - 40 - yy]) < 14) & (roof > 0)) * 1.0
hgt = parapet * 3.0
vis = mem - 0.05 * seam
sw = 0.70 + 0.04 * f1 - 0.04 * seam                       # SWIR: membrane bright, little texture

def rect(x0, y0, x1, y1):
    return ((xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)) * 1.0

# HVAC units with fans, skylights, walkway pads
for (x0, y0, w, h) in ((260, 190, 170, 110), (980, 240, 210, 120), (1240, 760, 150, 150), (520, 820, 190, 100)):
    m = rect(x0, y0, x0 + w, y0 + h)
    vis = blend(vis, 0.78 + 0.03 * f2, m); sw = blend(sw, 0.62, m); hgt += m * 6
    for k in range(max(1, w // 80)):
        fx, fy = x0 + 40 + k * 80, y0 + h / 2
        d = np.hypot(xx - fx, yy - fy)
        fan = (d < 28) * 1.0
        vis = blend(vis, 0.30 + 0.1 * (np.mod(np.arctan2(yy - fy, xx - fx) * 4, np.pi) < 0.6), fan * (d > 6))
        sw = blend(sw, 0.35, fan)
for (x0, y0) in ((640, 160), (760, 160), (640, 420), (760, 420)):
    m = rect(x0, y0, x0 + 80, y0 + 130)
    vis = blend(vis, 0.42 + 0.08 * (yy - y0) / 130, m); sw = blend(sw, 0.18, m); hgt += m * 2
walk = rect(200, 600, 1400, 640) * (np.mod(xx, 60) > 3)
vis = blend(vis, 0.58 + 0.04 * f2, walk); sw = blend(sw, 0.66, walk)

# pipe rack: two pipes running across with supports
for py, r in ((1010, 9), (1036, 6)):
    d = np.abs(yy - py - 6 * np.sin(xx / 500))
    m = (d < r) * (xx > 120) * (xx < 1500) * 1.0
    shade = np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1))
    vis = blend(vis, 0.45 + 0.4 * shade, m); sw = blend(sw, 0.40 + 0.35 * shade, m); hgt += m * 4

# moisture: ponding near a drain, wet insulation under the membrane, a leak from the pipe joint
blob = fbm(H, W, 40, rng, 4)
pond = np.clip(1 - (np.hypot((xx - 1120) / 120, (yy - 520) / 80) + (blob - 0.5) * 0.8), 0, 1)
wet = np.clip(1 - (np.hypot((xx - 420) / 230, (yy - 460) / 150) + (blob - 0.5) * 1.1), 0, 1) ** 0.7
wet2 = np.clip(1 - (np.hypot((xx - 330) / 120, (yy - 990) / 60) + (blob - 0.5) * 0.9), 0, 1) ** 0.7
leak = np.clip(1 - np.abs(xx - 860 - 10 * np.sin(yy / 30)) / 14, 0, 1) * (yy > 1000) * (yy < 1150) * 1.0
leak = soften(leak, 3)
vis = vis - 0.06 * np.clip(pond * 3, 0, 1) - 0.015 * wet - 0.02 * leak       # barely visible in daylight
sw = sw * (1 - 0.82 * np.clip(pond * 3, 0, 1)) * (1 - 0.55 * wet) * (1 - 0.5 * wet2) * (1 - 0.6 * leak)

# outside the roof: car park and verge
outside = 1 - roof
asph = 0.30 + 0.06 * f2 + 0.03 * f1
vis = blend(vis, asph, outside); sw = blend(sw, 0.42 + 0.05 * f2, outside)

shade = hillshade(soften(hgt, 1.5), 315, 35, 2.0)
vis = vis * (0.75 + 0.35 * shade); sw = sw * (0.8 + 0.25 * shade)

# visible: industrial haze; SWIR mostly sees through it
haze = 0.42 + 0.12 * noise(H, W, 500, rng)
vrgb = np.stack([vis * 1.0, vis * 1.0, vis * 1.03], -1)
vrgb = blend(vrgb, np.array([0.80, 0.80, 0.78]), haze)
vrgb = vrgb * (1 + 0.02 * (rng.random((H, W)) - 0.5))[..., None]
save(np.clip(vrgb, 0, 1), "swir_visible")
sw = sw * 0.92 + 0.05 * haze * 0.3 + (rng.random((H, W)) - 0.5) * 0.02
srgb = np.stack([sw * 0.97, sw * 1.0, sw * 1.02], -1)
save(np.clip(srgb, 0, 1), "swir_swir")
print({"ponding": (70.0, 43.3), "wet insulation": (26.2, 38.3), "pipe leak": (53.8, 89.0)})
