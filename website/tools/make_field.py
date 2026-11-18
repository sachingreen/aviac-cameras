#!/usr/bin/env python3
"""Sample-field images for the website's RGB / NDVI demo, from the aerial imagery in the Aviac dashboard screenshot.

RGB is the photo itself. NDVI is estimated from it (visible-band greenness, which tracks NDVI on this kind of scene),
mapped on the dashboard's NDVI ramp, with one stressed patch added that the RGB photo does not show.
The NDVI here is an illustration; real NDVI comes from the camera's red and NIR bands.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "website", "src", "assets", "img")
im = Image.open(os.path.join(REPO, "references", "dashboard", "dashboard.webp")).convert("RGB").crop((780, 250, 1145, 630))
im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
im.save(os.path.join(OUT, "field_rgb.jpg"), quality=88, optimize=True, progressive=True)
a = np.asarray(im).astype(np.float32) / 255.0
r, g, b = a[..., 0], a[..., 1], a[..., 2]
# vegetation signal for this RGB scene: green-dominant and not bright-yellow; dense canopy reads high, bare ground low
mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
sat = (mx - mn) / (mx + 1e-3)
greenish = np.clip((g - r) / (g + r + 1e-3) * 4.0 + 0.5, 0, 1)    # 0 for brown/yellow, 1 for green
v = np.clip(0.25 + 0.65 * greenish * (0.5 + 0.5 * sat) + 0.15 * (1 - mx), 0, 1)
v = np.where((r > 0.55) & (g > 0.55) & (b < 0.35), 0.48 + 0.1 * greenish, v)   # flowering mustard: moderate vigour
v = np.asarray(Image.fromarray((v * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255.0
H, W = v.shape
yy, xx = np.mgrid[0:H, 0:W]
cx, cy, rad = W * 0.72, H * 0.30, W * 0.12                       # the stressed patch, inside the dark crop at top right
d = np.sqrt(((xx - cx) / rad) ** 2 + ((yy - cy) / (rad * 0.8)) ** 2)
v = v - 0.6 * np.clip(1 - d, 0, 1) ** 1.3
v = np.clip(v, 0, 1)
stops = [(0.10, (150, 92, 60)), (0.35, (214, 170, 70)), (0.55, (196, 205, 90)), (0.72, (96, 170, 78)), (0.92, (22, 104, 58))]
out = np.zeros((H, W, 3), np.float32)
for (a0, c0), (a1, c1) in zip(stops[:-1], stops[1:]):
    m = (v >= a0) & (v <= a1)
    k = ((v - a0) / (a1 - a0))[..., None]
    out[m] = (np.array(c0) + (np.array(c1) - np.array(c0)) * k)[m]
out[v < stops[0][0]] = stops[0][1]
out[v > stops[-1][0]] = stops[-1][1]
shade = (0.82 + 0.18 * (a.mean(axis=2) / max(1e-3, a.mean())))[..., None]   # keep the photo's texture under the colour
Image.fromarray(np.clip(out * np.clip(shade, 0.7, 1.15), 0, 255).astype(np.uint8)).save(os.path.join(OUT, "field_ndvi.jpg"), quality=88, optimize=True, progressive=True)
print("field images", W, H, "patch at", round(cx / W, 2), round(cy / H, 2))
