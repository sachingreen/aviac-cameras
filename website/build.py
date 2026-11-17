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

# the pages: templates in src/ with shared head, nav, footer, cards and 3D viewers filled in
import re
ICONS = {
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    "pulse": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    "drone": '<circle cx="5" cy="5" r="2.5"/><circle cx="19" cy="5" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M7 7l3 3m7-3-3 3m-7 7 3-3m7 3-3-3"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>',
    "ruler": '<path d="m3 17 14-14 4 4L7 21z"/><path d="m7 13 2 2m1-5 2 2m1-5 2 2"/>',
    "chart": '<path d="M4 20V10m6 10V4m6 16v-7m4 7H2"/>',
    "leaf": '<path d="M5 19c0-9 6-14 15-14 0 9-5 15-14 15"/><path d="M5 19 14 10"/>',
    "scan": '<path d="M4 8V5a1 1 0 0 1 1-1h3m8 0h3a1 1 0 0 1 1 1v3m0 8v3a1 1 0 0 1-1 1h-3m-8 0H5a1 1 0 0 1-1-1v-3"/><path d="M4 12h16"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
}
NAV_ITEMS = [("home", "Home", ""), ("analytics", "Analytics", "analytics/"), ("sensors", "Sensors", "sensors/"), ("contact", "Contact", "contact/")]


def render(text, R):
    def head(m):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{m.group(1)}</title>
<meta name="description" content="Aviac builds multispectral and stereo drone cameras and the Terrain platform that turns every flight into maps, measurements and decisions.">
<meta name="theme-color" content="#0a0f0c">
<link rel="icon" href="{R}favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cal+Sans&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{R}assets/site.css">
</head>"""

    def nav(m):
        on = m.group(1)
        items = "".join(f'<li><a href="{R}{href}"{" class=on" if k == on else ""}>{t}</a></li>' for k, t, href in NAV_ITEMS)
        return (f'<nav class="nav"><div class="wrap"><a class="brand" href="{R}"><img src="{R}img/mark.svg" alt=""><b>AVIAC</b><span>TERRAIN</span></a>'
                f'<ul>{items}</ul><div class="right"><a class="btn sm" href="{R}ms/">Live 3D demo</a><a class="btn primary sm" href="{R}contact/">Book a demo</a></div>'
                f'<button class="burger" aria-label="Menu">&#9776;</button></div></nav>')

    def card(m):
        icon, title, body = m.group(1).split("|")
        return f'<div class="card reveal"><div class="ico"><svg viewBox="0 0 24 24">{ICONS[icon]}</svg></div><h4>{title}</h4><p>{body}</p></div>'

    def viewer(m):
        key, label = m.group(1).split("|")
        return (f'<div class="v3d"><div class="viewer" data-src="{R}{key}/"></div><div class="hint">{label} · drag to turn</div>'
                f'<div class="ctl"><span>Explode</span><input type="range" min="0" max="1" step="0.01" value="0"><button data-reset>Reset</button></div></div>')

    foot = (f'<footer><div class="wrap"><div class="cols">'
            f'<div><a class="brand" href="{R}"><img src="{R}img/mark.svg" alt=""><b>AVIAC</b><span>TERRAIN</span></a>'
            f'<p style="color:var(--ink-2);max-width:340px;font-size:14px;margin:18px 0 10px">Drone cameras and aerial analytics for farms and infrastructure.</p>'
            f'<a href="mailto:aviactech@gmail.com" style="font-size:14px;color:var(--ink-2)">aviactech@gmail.com</a></div>'
            f'<div><h6>Links</h6><ul><li><a href="{R}">Home</a></li><li><a href="{R}analytics/">Analytics</a></li><li><a href="{R}sensors/">Sensors</a></li><li><a href="{R}contact/">Contact</a></li></ul></div>'
            f'<div><h6>Sensors</h6><ul><li><a href="{R}sensors/#ms">Aviac MS</a></li><li><a href="{R}sensors/#duo">Aviac Duo</a></li><li><a href="{R}sensors/#swir">SWIR</a></li><li><a href="{R}ms/">3D demos</a></li></ul></div>'
            f'<div><h6>Join us</h6><ul><li><a href="{R}contact/">Book a demo</a></li><li><a href="mailto:aviactech@gmail.com?subject=Careers">Careers</a></li></ul></div>'
            f'</div><div class="legal"><span>&copy; AVIAC 2024&ndash;26. All rights reserved.</span><span>Specifications are design figures and may change.</span></div></div></footer>')
    text = re.sub(r"\{\{HEAD ([^}]*)\}\}", head, text)
    text = re.sub(r"\{\{NAV (\w+)\}\}", nav, text)
    text = re.sub(r"\{\{CARD ([^}]*)\}\}", card, text)
    text = re.sub(r"\{\{VIEWER ([^}]*)\}\}", viewer, text)
    return text.replace("{{FOOT}}", foot).replace("{{R}}", R)


SRC = os.path.join(HERE, "src")
for dp, _, fs in os.walk(SRC):
    rel = os.path.relpath(dp, SRC)
    for f in fs:
        if f.startswith("_"):
            continue
        src = os.path.join(dp, f)
        dst = os.path.join(OUT, rel, f) if rel != "." else os.path.join(OUT, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if f.endswith(".html"):
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            open(dst, "w").write(render(open(src).read(), "../" * depth))
        else:
            shutil.copy(src, dst)
shutil.copy(os.path.join(HERE, "vercel.json"), os.path.join(OUT, "vercel.json"))
total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print(f"website/public: {total / 1e6:.1f} MB")
