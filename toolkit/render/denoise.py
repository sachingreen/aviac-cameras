#!/usr/bin/env python3
"""Denoise rendered PNGs with Intel Open Image Denoise (standalone oidnDenoise binary).
usage: denoise.py <folder> [path-to-oidnDenoise]"""
import glob, os, subprocess, sys
import numpy as np
from PIL import Image

folder = sys.argv[1]
OIDN = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OIDN", "oidnDenoise")


def write_pfm(path, a):
    with open(path, "wb") as f:
        f.write(b"PF\n%d %d\n-1.0\n" % (a.shape[1], a.shape[0]))
        f.write(np.flipud(a).astype("<f4").tobytes())


def read_pfm(path):
    with open(path, "rb") as f:
        assert f.readline().strip() == b"PF"
        w, h = map(int, f.readline().split()); f.readline()
        return np.flipud(np.frombuffer(f.read(), "<f4").reshape(h, w, 3))


for p in sorted(glob.glob(os.path.join(folder, "*.png"))):
    if p.endswith("_raw.png"):
        continue
    im = Image.open(p)
    a = np.asarray(im)
    scale = 65535.0 if a.dtype == np.uint16 else 255.0
    rgb = (a[..., :3] / scale).astype(np.float32)
    write_pfm(p + ".in.pfm", rgb)
    r = subprocess.run([OIDN, "--ldr", p + ".in.pfm", "-o", p + ".out.pfm"], capture_output=True, text=True)
    if r.returncode != 0:
        print("denoise failed", p, r.stderr[-200:]); continue
    out = np.clip(read_pfm(p + ".out.pfm"), 0, 1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(p, optimize=True)
    os.remove(p + ".in.pfm"); os.remove(p + ".out.pfm")
    print("denoised", os.path.basename(p))
