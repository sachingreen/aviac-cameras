#!/usr/bin/env python3
"""Photographic finish for product renders: a soft bloom on the brightest highlights and fine luminance grain.
usage: finish.py in.png out.jpg"""
import sys
import numpy as np
from PIL import Image, ImageFilter

im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(np.float32) / 255.0
lum = a.mean(-1, keepdims=True)
hi = np.clip((lum - 0.72) / 0.28, 0, 1) * a
glow = np.asarray(Image.fromarray((hi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(a.shape[1] / 90))).astype(np.float32) / 255.0
a = 1 - (1 - a) * (1 - glow * 0.35)                       # screen blend
rng = np.random.default_rng(3)
g = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
g = np.asarray(Image.fromarray(((g * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255.0 - 0.5
a = np.clip(a + g[..., None] * 0.035 * (0.6 + 0.4 * (1 - lum)), 0, 1)
Image.fromarray((a * 255).astype(np.uint8)).save(sys.argv[2], quality=88, optimize=True, progressive=True)
