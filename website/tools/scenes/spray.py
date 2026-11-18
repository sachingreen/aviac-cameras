#!/usr/bin/env python3
"""Spray-coverage view of the procedural farm (run farm.py first): the Duos looks back at the boom and the
coverage map marks what was sprayed, a missed strip and an overlap. Illustrative only."""
import os
import numpy as np
from common import OUT, W, H, save, soften, blend

st = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "farm_state.npz"))
rgb, tram, pid, u = st["rgb"].astype(np.float64), st["tram"], st["pid"], st["u"]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
sprayed_ids = [i for i in np.unique(pid) if tram[pid == i].max() > 0.5]
crop = np.isin(pid, sprayed_ids) & (st["track"] < 0.5)
grey = rgb.mean(-1, keepdims=True) * np.array([1, 1, 1]) * 0.9 + rgb * 0.1
cov = crop * 1.0
# a missed strip: one pass skipped in a parcel right of centre; an overlap in a parcel lower left
def pick(fx, fy):
    best, bd = None, 1e18
    for i in sprayed_ids:
        ys, xs = np.nonzero(pid[::8, ::8] == i)
        if len(ys) < 600:
            continue
        d = (xs.mean() * 8 - fx * W) ** 2 + (ys.mean() * 8 - fy * H) ** 2
        if d < bd:
            best, bd = i, d
    m = pid == best
    return m, np.median(u[m])
m_miss, u_miss = pick(0.62, 0.40)
m_over, u_over = pick(0.22, 0.72)
miss = m_miss & (np.abs(u - u_miss) < 24)                    # one boom width skipped
over = m_over & (np.abs(u - u_over) < 16)                    # two passes overlapping
teal, deep, warn = np.array([0.10, 0.62, 0.58]), np.array([0.10, 0.30, 0.62]), np.array([0.96, 0.46, 0.10])
out = blend(grey, teal, cov * 0.5)
out = blend(out, deep, soften(over * 1.0, 1) * 0.7)
out = blend(out, warn, soften(miss * 1.0, 1) * 0.85)
save(np.clip(out, 0, 1), "spray_coverage")
ys, xs = np.nonzero(miss); ys2, xs2 = np.nonzero(over)
print({"miss": (round(xs.mean() / W * 100, 1), round(ys.mean() / H * 100, 1)), "overlap": (round(xs2.mean() / W * 100, 1), round(ys2.mean() / H * 100, 1))})
