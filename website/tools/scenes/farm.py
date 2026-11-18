#!/usr/bin/env python3
"""Procedural aerial farm: an RGB view and an NDVI view generated from the SAME crop model (cover, vigour, soil),
so the two always line up. Early stress lowers vigour strongly (NDVI) but changes the visible colour only slightly,
which is what the website's compare slider demonstrates. Also writes the spray-coverage view of the same farm.
Illustrative imagery, not a capture."""
import math
import os
import numpy as np
from common import OUT, W, H, fbm, noise, hillshade, ramp, NDVI_RAMP, save, soften, blend

rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
th = math.radians(8.0)
u = xx * math.cos(th) + yy * math.sin(th)            # field-grid coordinates, rotated 8 degrees to the image
v = -xx * math.sin(th) + yy * math.cos(th)

# ---- parcels: columns along u, each split into plots along v
ub = [-400.0]
while ub[-1] < W + 400:
    ub.append(ub[-1] + rng.uniform(260, 470))
ub = np.array(ub)
col = np.clip(np.searchsorted(ub, u) - 1, 0, len(ub) - 2)
pid = np.zeros((H, W), int); du = np.zeros((H, W)); dv = np.zeros((H, W))
vbs = []
for c in range(len(ub) - 1):
    vb = [-400.0]
    while vb[-1] < H + 400:
        vb.append(vb[-1] + rng.uniform(200, 430))
    vb = np.array(vb); vbs.append(vb)
    m = col == c
    r = np.clip(np.searchsorted(vb, v[m]) - 1, 0, len(vb) - 2)
    pid[m] = c * 100 + r
    du[m] = np.minimum(u[m] - ub[c], ub[c + 1] - u[m])
    dv[m] = np.minimum(v[m] - vb[r], vb[r + 1] - v[m])
edge = np.minimum(du, dv)

TYPES = ["wheat", "young", "mustard", "mature", "tilled", "stubble", "wheat", "mature", "young"]
ids = np.unique(pid)
kind = {i: TYPES[rng.integers(len(TYPES))] for i in ids}

# ---- per-pixel crop model
cover = np.zeros((H, W)); vig = np.zeros((H, W)); plant = np.zeros((H, W, 3)); soilc = np.zeros((H, W, 3))
flower = np.zeros((H, W)); straw = np.zeros((H, W)); hgt = np.zeros((H, W))
grain = fbm(H, W, 3, rng, 3)
wob = fbm(H, W, 60, rng, 3) * 6.0
soil_n = fbm(H, W, 40, rng, 5)
for i in ids:
    m = pid == i
    k = kind[i]
    along_u = rng.random() < 0.5
    coord = (u if along_u else v)[m] + wob[m]
    per = rng.uniform(6.5, 9.0)
    rows = 0.5 + 0.5 * np.sin(2 * math.pi * coord / per + rng.uniform(0, 6))
    base = rng.uniform(0.74, 0.9)
    vg = base + (fbm(H, W, 150, rng, 3)[m] - 0.5) * 0.28
    soilc[m] = np.array([0.47, 0.38, 0.29]) * (0.8 + 0.4 * soil_n[m])[:, None]
    if k == "wheat":
        cv = 0.88 + 0.12 * rows; pc = (0.36, 0.47, 0.21)
    elif k == "young":
        cv = np.clip(rows * 1.4 - 0.45, 0, 1) * 0.85; pc = (0.30, 0.47, 0.17)
    elif k == "mustard":
        cv = 0.9 + 0.1 * rows; pc = (0.34, 0.46, 0.18); flower[m] = np.clip(0.55 + 0.35 * (grain[m] - 0.5) * 3 + 0.15 * rows, 0, 1)
    elif k == "mature":
        cv = 0.97 + 0.03 * rows; pc = (0.20, 0.31, 0.12)
    elif k == "tilled":
        cv = np.zeros(m.sum()); pc = (0.3, 0.45, 0.2); vg = vg * 0
        soilc[m] *= (0.82 + 0.3 * rows)[:, None]
    else:  # stubble
        cv = np.zeros(m.sum()) + 0.05; pc = (0.3, 0.45, 0.2); straw[m] = 0.7 + 0.3 * rows
    cover[m] = cv; vig[m] = np.clip(vg, 0, 1); plant[m] = pc

# ---- tramlines: paired wheel tracks every ~110 px, the lanes a sprayer drives
tram = np.zeros((H, W))
for i in ids:
    if kind[i] in ("tilled", "stubble"):
        continue
    m = pid == i
    per, off = rng.uniform(100, 125), rng.uniform(0, 100)
    q = np.mod(u[m] + off, per)
    tram[m] = np.clip(1 - np.abs(q - 8) / 1.6, 0, 1) + np.clip(1 - np.abs(q - 26) / 1.6, 0, 1)
cover = cover * (1 - 0.8 * tram)

# ---- stress patches: two blobs in green crops, the reason this demo exists
stress = np.zeros((H, W))
green_ids = [i for i in ids if kind[i] in ("wheat", "mature")]
centres = []
for i in green_ids:
    m = pid == i
    ys, xs = np.nonzero(m & (edge > 70))
    if len(ys) > 4000:
        j = rng.integers(len(ys)); centres.append((xs[j], ys[j]))
targets = sorted(centres, key=lambda p: (p[0] - W * 0.68) ** 2 + (p[1] - H * 0.32) ** 2)[:1] + \
          sorted(centres, key=lambda p: (p[0] - W * 0.3) ** 2 + (p[1] - H * 0.72) ** 2)[:1]
blobn = fbm(H, W, 30, rng, 4)
for (cx, cy), rad in zip(targets, (95, 60)):
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) / 0.8) ** 2) / rad + (blobn - 0.5) * 0.7
    stress = np.maximum(stress, np.clip(1 - d, 0, 1) ** 0.8)
stress *= (cover > 0.3)
vig = vig * (1 - 0.75 * stress)

# ---- tracks between plots, hedgerow trees along some of them
track = np.clip(1 - (edge - 4) / 4, 0, 1)
tree = np.zeros((H, W)); th_ = np.zeros((H, W))
for c in range(1, len(ub) - 1):
    if rng.random() < 0.55:
        continue
    for t in np.arange(-300, H + 400, rng.uniform(16, 26)):
        if rng.random() < 0.25:
            continue
        uu, vv = ub[c] + rng.normal(0, 4), t
        x = uu * math.cos(th) - vv * math.sin(th); y = uu * math.sin(th) + vv * math.cos(th)
        if -40 < x < W + 40 and -40 < y < H + 40:
            r = rng.uniform(9, 20)
            x0, x1, y0, y1 = int(max(0, x - r)), int(min(W, x + r + 1)), int(max(0, y - r)), int(min(H, y + r + 1))
            if x1 <= x0 or y1 <= y0:
                continue
            d = np.sqrt((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / r
            d = d + (noise(y1 - y0, x1 - x0, 4, rng) - 0.5) * 0.5
            dome = np.clip(1 - d ** 2, 0, 1)
            tree[y0:y1, x0:x1] = np.maximum(tree[y0:y1, x0:x1], (dome > 0) * 1.0)
            th_[y0:y1, x0:x1] = np.maximum(th_[y0:y1, x0:x1], np.sqrt(dome) * r * 0.9)
tree = soften(tree, 0.8)

# ---- RGB
leaf = plant * (0.86 + 0.28 * (grain - 0.5) * 2)[..., None] * (0.92 + 0.16 * (vig - 0.8))[..., None]
leaf = leaf * (1 + np.array([0.035, -0.03, 0.0]) * stress[..., None])          # stress: barely visible in colour
rgb = blend(soilc, leaf, cover)
rgb = blend(rgb, np.array([0.86, 0.74, 0.16]) * (0.9 + 0.2 * grain)[..., None], flower * 0.85)
rgb = blend(rgb, np.array([0.70, 0.62, 0.45]) * (0.85 + 0.3 * grain)[..., None], straw * 0.9)
dirt = np.array([0.64, 0.58, 0.48]) * (0.85 + 0.3 * fbm(H, W, 8, rng, 3))[..., None]
rgb = blend(rgb, dirt, track)
treec = np.array([0.13, 0.22, 0.09]) * (0.75 + 0.5 * fbm(H, W, 5, rng, 3))[..., None]
rgb = blend(rgb, treec, tree)
height = cover * vig * 1.2 + flower * 0.4 + th_ * 1.0 + soilc[..., 0] * 0.6
shade = hillshade(soften(height, 1.0), 315, 38, 1.4)
shadow = np.clip(soften(np.roll(np.roll(th_, 9, 0), 9, 1), 3) / 10, 0, 1) * (1 - tree)
rgb = rgb * (0.55 + 0.6 * shade)[..., None] * (1 - 0.45 * shadow)[..., None]
rgb = rgb * (1 + 0.03 * (rng.random((H, W)) - 0.5))[..., None]
r2 = ((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2
rgb = np.clip(rgb * (1.06 - 0.25 * r2)[..., None], 0, 1) ** 0.95
save(rgb, "field_rgb")

# ---- NDVI, from the same model
canopy = 0.22 + 0.7 * vig
ndvi = cover * canopy + (1 - cover) * (0.12 + 0.05 * soil_n)
ndvi = ndvi * (1 - 0.28 * flower) + straw * 0.05
ndvi = ndvi * (1 - track) + 0.08 * track
ndvi = ndvi * (1 - tree) + 0.86 * tree
ndvi = soften(ndvi, 0.7) + (grain - 0.5) * 0.03
nd = ramp((ndvi + 0.12) / 1.05, NDVI_RAMP)
nd = nd * (0.9 + 0.12 * shade)[..., None]
save(nd, "field_ndvi")
np.savez_compressed(os.path.join(OUT, "..", "..", "..", "..", "tools", "scenes", "farm_state.npz"), rgb=rgb.astype(np.float32), tram=tram.astype(np.float32), pid=pid, cover=cover.astype(np.float32), u=u.astype(np.float32), track=track.astype(np.float32), tree=tree.astype(np.float32))
print("stress centres", targets)
