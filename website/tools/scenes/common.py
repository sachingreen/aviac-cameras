"""Shared helpers for the procedural demo scenes: fractal noise, hill-shading, colour ramps, output."""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(REPO, "website", "src", "assets", "img", "demo")
os.makedirs(OUT, exist_ok=True)
W, H = 1600, 1200


def noise(h, w, scale, rng, order=3):
    """Smooth value noise, features about `scale` px across, 0..1."""
    gh, gw = max(1, int(h / scale)) + 3, max(1, int(w / scale)) + 3
    g = rng.random((gh, gw))
    z = ndimage.zoom(g, (h / (gh - 3) * 1.0 + 1e-6, w / (gw - 3) * 1.0 + 1e-6), order=order, mode="reflect")
    if z.shape[0] < h or z.shape[1] < w:
        z = np.pad(z, ((0, max(0, h - z.shape[0])), (0, max(0, w - z.shape[1]))), mode="edge")
    return np.clip(z[:h, :w], 0, 1)


def fbm(h, w, scale, rng, octaves=5, gain=0.5):
    out, amp, tot, s = np.zeros((h, w)), 1.0, 0.0, scale
    for _ in range(octaves):
        if s < 1.5:
            out += amp * rng.random((h, w)); tot += amp
            break
        out += amp * noise(h, w, s, rng); tot += amp
        amp *= gain; s /= 2.0
    return out / tot


def hillshade(height, az=315.0, alt=40.0, z=1.0):
    gy, gx = np.gradient(height * z)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, al = np.radians(az), np.radians(alt)
    hs = np.sin(al) * np.sin(slope) + np.cos(al) * np.cos(slope) * np.cos(a - aspect)
    return np.clip(hs, 0, 1)


def ramp(v, stops):
    """Piecewise-linear colour ramp. stops: [(pos, (r, g, b) 0..255), ...]."""
    v = np.clip(v, 0, 1)
    pos = np.array([p for p, _ in stops]); col = np.array([c for _, c in stops], dtype=np.float64)
    out = np.zeros(v.shape + (3,))
    for k in range(3):
        out[..., k] = np.interp(v, pos, col[:, k])
    return out / 255.0


NDVI_RAMP = [(0.0, (165, 0, 38)), (0.18, (215, 48, 39)), (0.32, (244, 109, 67)), (0.45, (253, 174, 97)), (0.55, (254, 224, 139)),
             (0.64, (217, 239, 139)), (0.74, (166, 217, 106)), (0.84, (102, 189, 99)), (0.93, (26, 152, 80)), (1.0, (0, 104, 55))]
IRON = [(0.0, (0, 0, 10)), (0.15, (32, 0, 90)), (0.32, (120, 6, 140)), (0.5, (200, 40, 90)), (0.66, (240, 100, 20)),
        (0.82, (252, 180, 20)), (0.94, (255, 236, 130)), (1.0, (255, 255, 240))]


def blend(a, b, t):
    if np.ndim(t) == 2 and np.ndim(a) == 3 or np.ndim(t) == 2 and np.ndim(b) == 3:
        t = t[..., None]
    return a * (1 - t) + b * t


def save(arr, name, q=86):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    p = os.path.join(OUT, name + ".jpg")
    im.save(p, quality=q, optimize=True, progressive=True)
    print(name, im.size, os.path.getsize(p) // 1024, "KB")


def soften(a, s):
    if a.ndim == 3:
        return np.stack([ndimage.gaussian_filter(a[..., k], s) for k in range(a.shape[2])], -1)
    return ndimage.gaussian_filter(a, s)
