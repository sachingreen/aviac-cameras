#!/usr/bin/env python3
"""Lighter images for the website: a WebP next to every JPEG under src/assets/img (40 to 70 % smaller at the same look),
800 px versions of the big product photos for phones and gallery tiles, and 160 px thumbnails for the systems bar.
build.py serves the WebP through <picture> with the JPEG as fallback. Run after adding or changing an image:

  python3 website/tools/webp.py
"""
import glob, os
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(HERE, 'src', 'assets', 'img')
Q_WEBP, Q_JPEG = 80, 82


def fresh(out, src):
    return os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src)


def save(im, path_noext, jpeg=True):
    if jpeg:
        im.save(path_noext + '.jpg', 'JPEG', quality=Q_JPEG, optimize=True, progressive=True)
    im.save(path_noext + '.webp', 'WEBP', quality=Q_WEBP, method=6)


made = 0
for src in sorted(glob.glob(os.path.join(IMG, '**', '*.jpg'), recursive=True)):
    rel = os.path.relpath(src, IMG)
    if rel.startswith('dash' + os.sep):          # the dashboard screenshots have their own sizes (made with the iPad)
        continue
    base = src[:-4]
    im = None
    # the WebP twin
    if not fresh(base + '.webp', src):
        im = im or Image.open(src).convert('RGB')
        im.save(base + '.webp', 'WEBP', quality=Q_WEBP, method=6); made += 1
    # 800 px versions of the 1600 px product photos (heroes have them already)
    top = os.path.dirname(rel) == ''
    if top and not base.endswith('_800'):
        w, h = Image.open(src).size
        if w >= 1600 and not os.path.exists(base + '_800.jpg'):
            im = im or Image.open(src).convert('RGB')
            save(im.resize((800, round(h * 800 / w)), Image.LANCZOS), base + '_800'); made += 2
    # systems bar thumbnails, 160 px wide (shown at 54 px)
    if rel.startswith('t' + os.sep) and rel.count(os.sep) == 1 and rel.endswith('_hero_light.jpg'):
        small = os.path.join(IMG, 't', 's', os.path.basename(base))
        if not fresh(small + '.webp', src):
            os.makedirs(os.path.dirname(small), exist_ok=True)
            im = im or Image.open(src).convert('RGB')
            w, h = im.size
            save(im.resize((160, round(h * 160 / w)), Image.LANCZOS), small); made += 2
# WebP twins for anything the steps above just wrote
for src in sorted(glob.glob(os.path.join(IMG, '**', '*.jpg'), recursive=True)):
    if os.path.relpath(src, IMG).startswith('dash' + os.sep):
        continue
    if not fresh(src[:-4] + '.webp', src):
        Image.open(src).convert('RGB').save(src[:-4] + '.webp', 'WEBP', quality=Q_WEBP, method=6); made += 1
jpg = sum(os.path.getsize(p) for p in glob.glob(os.path.join(IMG, '**', '*.jpg'), recursive=True))
webp = sum(os.path.getsize(p) for p in glob.glob(os.path.join(IMG, '**', '*.webp'), recursive=True))
print(f'{made} files written · JPEG {jpg / 1e6:.2f} MB · WebP {webp / 1e6:.2f} MB')
