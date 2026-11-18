#!/usr/bin/env python3
"""Procedural construction site from above at two dates (week 3 and week 11), drawn from one site plan so the
compare slider lines up: excavation and stockpiles, then a raft slab, columns, formwork and a tower crane.
Illustrative only."""
import numpy as np
from common import W, H, fbm, noise, hillshade, save, soften, blend

yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)


def rect(x0, y0, x1, y1):
    return ((xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)) * 1.0


def scene(week):
    rng = np.random.default_rng(5)                         # same base for both dates
    f1, f2, f3 = fbm(H, W, 100, rng, 5), fbm(H, W, 3, rng, 3), fbm(H, W, 18, rng, 4)
    # surroundings: street, pavement, neighbouring roofs, verge trees
    rgb = np.stack([0.33 + 0.05 * f2, 0.33 + 0.05 * f2, 0.34 + 0.05 * f2], -1)          # asphalt
    hgt = np.zeros((H, W))
    rgb = blend(rgb, np.array([0.72, 0.70, 0.66]) * (0.9 + 0.2 * f2)[..., None], rect(0, 980, W, 1020))   # pavement
    lane = rect(0, 1095, W, 1099) * (np.mod(xx, 70) < 40)
    rgb = blend(rgb, np.array([0.92, 0.92, 0.88]), lane)
    for (x0, y0, x1, y1, c) in ((0, 0, 230, 420, (0.55, 0.30, 0.25)), (0, 470, 230, 940, (0.62, 0.62, 0.60)),
                                (1380, 0, W, 380, (0.48, 0.50, 0.52)), (1380, 430, W, 940, (0.66, 0.42, 0.33))):
        m = rect(x0, y0, x1, y1)
        ridge = np.abs((yy - (y0 + y1) / 2)) / ((y1 - y0) / 2)
        rgb = blend(rgb, np.array(c) * (0.92 + 0.12 * f2)[..., None], m); hgt += m * (12 - 6 * ridge)
    # the site: hoarding around a dirt plot
    site = rect(270, 40, 1340, 950)
    dirt = np.stack([0.58 + 0.08 * f1, 0.48 + 0.07 * f1, 0.37 + 0.05 * f1], -1) * (0.85 + 0.3 * f2)[..., None]
    rgb = blend(rgb, dirt, site)
    hoard = site - rect(278, 48, 1332, 942)
    rgb = blend(rgb, np.array([0.18, 0.36, 0.30]), hoard); hgt += hoard * 4
    # tyre tracks from the gate
    for k in range(3):
        tr = np.clip(1 - np.abs(xx - 760 - 40 * np.sin(yy / 160 + k) - k * 14) / 3, 0, 1) * (yy > 700) * (yy < 942)
        rgb = rgb * (1 - 0.12 * tr)[..., None]
    pit = rect(420, 150, 1180, 720)
    if week == 3:
        # excavation: darker, damp soil, a ramp, stockpiles, an excavator and a tipper
        depth = pit * np.clip(np.minimum.reduce([xx - 420, 1180 - xx, yy - 150, 720 - yy]) / 40, 0, 1)
        ramp_ = rect(1000, 720, 1080, 840) * (1 - (yy - 720) / 120)
        rgb = blend(rgb, np.stack([0.45 + 0.06 * f1, 0.36 + 0.05 * f1, 0.27 + 0.04 * f1], -1) * (0.85 + 0.3 * f2)[..., None], depth)
        hgt += -depth * 30 - ramp_ * 0
        for (cx, cy, r) in ((340, 820, 70), (520, 860, 55), (1250, 300, 60)):
            d = np.hypot(xx - cx, yy - cy) / r + (f3 - 0.5) * 0.4
            pile = np.clip(1 - d, 0, 1)
            rgb = blend(rgb, np.array([0.62, 0.52, 0.40]) * (0.9 + 0.2 * f2)[..., None], np.clip(pile * 4, 0, 1)); hgt += pile * 40
        for (x0, y0, w, h, c) in ((640, 360, 70, 34, (0.95, 0.72, 0.10)), (880, 560, 90, 34, (0.85, 0.20, 0.15))):
            m = rect(x0, y0, x0 + w, y0 + h); rgb = blend(rgb, np.array(c), m); hgt += m * 10
        arm = np.clip(1 - np.abs((yy - 377) - (xx - 710) * 0.5) / 5, 0, 1) * (xx > 705) * (xx < 790)
        rgb = blend(rgb, np.array([0.95, 0.72, 0.10]) * 0.9, arm); hgt += arm * 8
    else:
        # raft slab poured over most of the pit, rebar on the rest, columns, formwork, a tower crane
        slab = rect(420, 150, 1000, 720)
        conc = np.stack([0.74 + 0.04 * f1] * 3, -1) * np.array([1.0, 0.99, 0.96]) * (0.94 + 0.12 * f2)[..., None]
        rgb = blend(rgb, conc, slab); hgt += slab * 2
        reb = rect(1000, 150, 1180, 720)
        mesh = ((np.mod(xx, 9) < 1.5) | (np.mod(yy, 9) < 1.5)) * reb
        rgb = blend(rgb, np.array([0.38, 0.33, 0.30]), reb); rgb = blend(rgb, np.array([0.50, 0.26, 0.15]), mesh)
        joints = ((np.abs(np.mod(xx - 420, 145)) < 1.2) | (np.abs(np.mod(yy - 150, 142)) < 1.2)) * slab
        rgb = rgb * (1 - 0.15 * joints)[..., None]
        for cx in np.arange(470, 1000, 96):
            for cy in np.arange(200, 700, 95):
                m = rect(cx - 9, cy - 9, cx + 9, cy + 9)
                rgb = blend(rgb, np.array([0.80, 0.80, 0.78]), m); hgt += m * 30
        for (x0, y0, w, h) in ((440, 170, 230, 90), (700, 600, 260, 100)):
            m = rect(x0, y0, x0 + w, y0 + h)
            ply = np.array([0.80, 0.55, 0.30]) * (0.9 + 0.2 * ((np.mod(xx, 60) < 58) & (np.mod(yy, 30) < 29)))[..., None]
            rgb = blend(rgb, ply, m); hgt += m * 8
        # tower crane: mast, jib and counter-jib, with their shadow
        mast = rect(1220, 520, 1244, 544); rgb = blend(rgb, np.array([0.95, 0.75, 0.12]), mast); hgt += mast * 60
        jib = np.clip(1 - np.abs(yy - 532) / 7, 0, 1) * (xx > 640) * (xx < 1320)
        lat = jib * ((np.mod(xx, 16) < 2) | (np.abs(yy - 532) > 5))
        rgb = blend(rgb, np.array([0.95, 0.75, 0.12]), jib * 0.8); rgb = rgb * (1 - 0.3 * lat)[..., None]
        sh = np.clip(1 - np.abs(yy - 532 - 70) / 3, 0, 1) * (xx > 700) * (xx < 1380)
        rgb = rgb * (1 - 0.35 * sh)[..., None]
        cw = rect(1290, 520, 1316, 544); rgb = blend(rgb, np.array([0.55, 0.55, 0.55]), cw)
        # site cabins and a smaller remaining stockpile
        for k in range(3):
            m = rect(300 + k * 70, 800, 360 + k * 70, 900); rgb = blend(rgb, np.array([0.92, 0.92, 0.90]) if k != 1 else np.array([0.30, 0.45, 0.62]), m); hgt += m * 12
        d = np.hypot(xx - 1250, yy - 300) / 40 + (f3 - 0.5) * 0.4
        pile = np.clip(1 - d, 0, 1); rgb = blend(rgb, np.array([0.62, 0.52, 0.40]), np.clip(pile * 4, 0, 1)); hgt += pile * 25
    shade = hillshade(soften(hgt, 1.5), 315, 40, 0.8)
    rgb = rgb * (0.62 + 0.5 * shade)[..., None]
    rgb = rgb * (1 + 0.025 * (rng.random((H, W)) - 0.5))[..., None]
    save(np.clip(rgb, 0, 1), f"site_w{week}")


scene(3)
scene(11)
