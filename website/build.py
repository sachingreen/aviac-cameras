#!/usr/bin/env python3
"""Assemble the static site in website/public from the repo: the landing page, the brand files, compressed
renders, and the two interactive showcases (built separately with `node build.mjs` in each showcase folder).

  python3 website/build.py
Then deploy website/public (Vercel: root directory `website`, output directory `public`, no build command).
"""
import os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "public")
sys.path.insert(0, os.path.join(REPO, "toolkit", "brand"))
from logo import svg_mark, svg_wordmark, svg_lockup, IVORY, GREEN

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, "img"))

# brand
open(os.path.join(OUT, "img", "mark.svg"), "w").write(svg_mark(IVORY))
open(os.path.join(OUT, "img", "wordmark.svg"), "w").write(svg_wordmark(IVORY))
open(os.path.join(OUT, "img", "lockup.svg"), "w").write(svg_lockup())
fav = svg_mark(IVORY).replace('<svg ', f'<svg style="background:{GREEN}" ')
open(os.path.join(OUT, "favicon.svg"), "w").write(fav)

# renders, as web-sized JPEGs
R = {"ms": os.path.join(REPO, "cameras", "6band", "mechanical", "out", "renders"),
     "duo": os.path.join(REPO, "cameras", "duo", "mechanical", "out", "renders"),
     "ms_front": os.path.join(REPO, "cameras", "6band", "mechanical", "out", "front"),
     "duo_front": os.path.join(REPO, "cameras", "duo", "mechanical", "out", "front")}
for cam, d in R.items():
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".png"):
            im = Image.open(os.path.join(d, f)).convert("RGB")
            im.thumbnail((1600, 1000))
            im.save(os.path.join(OUT, "img", f"{cam.split('_')[0]}_{f[:-4]}.jpg"), quality=84, optimize=True, progressive=True)

# the interactive showcases
BACK = ('<a href="../" style="position:fixed;left:50%;bottom:10px;transform:translateX(-50%);z-index:100;font:600 11px Inter,system-ui,sans-serif;'
        'letter-spacing:.12em;text-transform:uppercase;color:#f2f1eb;background:rgba(24,36,30,.82);border:1px solid rgba(242,241,235,.25);'
        'padding:7px 14px;border-radius:20px;text-decoration:none;backdrop-filter:blur(8px)">&larr; Aviac Technologies</a>')
for cam, d in (("ms", os.path.join(REPO, "cameras", "6band", "showcase", "dist")), ("duo", os.path.join(REPO, "cameras", "duo", "showcase", "dist"))):
    o = os.path.join(OUT, cam)
    os.makedirs(o)
    html = open(os.path.join(d, "standalone.html")).read()
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<link rel="icon" href="../favicon.svg">', 1)
    html = html.replace("</body>", BACK + "\n</body>")
    open(os.path.join(o, "index.html"), "w").write(html)
    for f in ("model.txt", "board.png"):
        shutil.copy(os.path.join(d, f), os.path.join(o, f))
    shutil.copy(os.path.join(os.path.dirname(d), "src", "parts.json"), os.path.join(o, "parts.json"))   # for the 3D viewer

# landing page and its stylesheet
for f in os.listdir(os.path.join(HERE, "src")):
    shutil.copy(os.path.join(HERE, "src", f), os.path.join(OUT, f))
shutil.copy(os.path.join(HERE, "vercel.json"), os.path.join(OUT, "vercel.json"))
total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print(f"website/public: {total / 1e6:.1f} MB")
