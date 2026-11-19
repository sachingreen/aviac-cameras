#!/usr/bin/env python3
"""Build the Aviac website into website/public.

  python3 website/tools/pack_models.py      # after a CAD change: repacks src/models/
  (cd website/viewer && node build.mjs)     # after a viewer change: rebuilds src/viewer.js
  python3 website/build.py

Pages are templates in src/ with {{HEAD title}}, {{NAV key}}, {{FOOT}} and {{R}} (the path back to the site root).
Deploy website/public (Vercel: root directory website/public, no build command).
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC, OUT = os.path.join(HERE, "src"), os.path.join(HERE, "public")
sys.path.insert(0, os.path.join(REPO, "toolkit", "brand"))
from logo import svg_mark, svg_wordmark, GREEN, IVORY

NAV = [("solutions", "Solutions", "#solutions", [("crop", "Crop monitoring", "solutions/crop-monitoring/", "Multispectral · stress before it shows"),
                                                  ("spraying", "Spraying", "solutions/spraying/", "Stereo · coverage on every pass"),
                                                  ("solar", "Solar inspection", "solutions/solar/", "Thermal · hotspots to repairs"),
                                                  ("industrial", "Industrial inspection", "solutions/industrial/", "SWIR · moisture, leaks, haze"),
                                                  ("construction", "Construction monitoring", "solutions/construction/", "Weekly maps · progress and volumes")]),
       ("systems", "Systems", "#systems", [("ms", "MS", "product/multispectral/", "Agri Spectral · six bands"), ("duos", "Duos", "product/duos/", "Stereo · spray drones"),
                                           ("th", "TH", "product/thermal/", "Thermal + NIR · demo"), ("sw", "SW", "product/swir/", "SWIR · demo")]),
       ("field", "In the field", "#field", None), ("research", "Partners", "#research", None), ("company", "Company", "#company", None)]


def _ver():
    import hashlib
    h = hashlib.sha1()
    for f in ("assets/site.css", "assets/site.js"):
        h.update(open(os.path.join(SRC, f), "rb").read())
    h.update(svg_mark(GREEN).encode()); h.update(svg_wordmark(GREEN).encode())
    return h.hexdigest()[:8]


V = _ver()       # cache-buster: browsers keep img/ for a week, so a changed logo or stylesheet gets a new URL


SYSTEMS_ORDER = [("ms", "MS", "Agri Spectral", "product/multispectral/", "ms_titanium_hero_light.jpg"),
                 ("duos", "Duos", "Stereo", "product/duos/", "duos_arctic_hero_light.jpg"),
                 ("th", "TH", "Thermal + NIR", "product/thermal/", "th_field_hero_light.jpg"),
                 ("sw", "SW", "SWIR", "product/swir/", "sw_graphite_hero_light.jpg")]


def switcher(on, R):
    """Product pages: a row of all four systems under the header, and arrows at the screen edges to the neighbours."""
    keys = [k for k, *_ in SYSTEMS_ORDER]
    if on not in keys:
        return ""
    i = keys.index(on)
    prv, nxt = SYSTEMS_ORDER[(i - 1) % 4], SYSTEMS_ORDER[(i + 1) % 4]
    row = "".join(f'<a href="{R}{h}"{" class=on aria-current=page" if k == on else ""}><img src="{R}assets/img/t/{img}" alt="" width="54" height="38"><span><b>{n}</b>{sub}</span></a>'
                  for k, n, sub, h, img in SYSTEMS_ORDER)
    return (f'<div class="sysbar"><div class="wrap"><a class="sb-arrow" href="{R}{prv[3]}" aria-label="Previous system: {prv[1]}">&larr;</a>'
            f'<nav class="sb-row" aria-label="Systems">{row}</nav><a class="sb-arrow" href="{R}{nxt[3]}" aria-label="Next system: {nxt[1]}">&rarr;</a></div></div>'
            f'<a class="sb-edge l" href="{R}{prv[3]}" aria-label="Previous system: {prv[1]}"><span>&larr;</span><b>{prv[1]}</b></a>'
            f'<a class="sb-edge r" href="{R}{nxt[3]}" aria-label="Next system: {nxt[1]}"><b>{nxt[1]}</b><span>&rarr;</span></a>'
            f'<script>addEventListener("keydown",e=>{{if(e.target.closest("input,textarea,select"))return;if(e.key==="ArrowLeft")location.href="{R}{prv[3]}";if(e.key==="ArrowRight")location.href="{R}{nxt[3]}"}});'
            f'(()=>{{let x=null;addEventListener("touchstart",e=>{{if(!e.target.closest(".viewer,.cmpimg,.fly"))x=e.touches[0].clientX}},{{passive:true}});'
            f'addEventListener("touchend",e=>{{if(x===null)return;const d=e.changedTouches[0].clientX-x;x=null;if(d>90)location.href="{R}{prv[3]}";if(d<-90)location.href="{R}{nxt[3]}"}})}})();</script>')


def render(text, R):
    def head(m):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{m.group(1)}</title>
<meta name="description" content="Aviac Technologies builds drone cameras with edge AI: multispectral crop monitoring, spray coverage, thermal solar inspection, SWIR industrial inspection and construction monitoring.">
<meta name="theme-color" content="#f6f8f6">
<link rel="icon" href="{R}favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{R}assets/site.css">
</head>"""

    def nav(m):
        on = m.group(1)
        home = "" if on == "home" else R
        items = ""
        for k, t, h, sub in NAV:
            on_ = k == on or (sub and any(sk == on for sk, *_ in sub))
            if sub:
                links = "".join(f'<a href="{R}{sh}"{" class=on" if sk == on else ""}><b>{st}</b><span>{sd}</span></a>' for sk, st, sh, sd in sub)
                items += (f'<li class="dd"><a href="{home}{h}"{" class=on" if on_ else ""} aria-haspopup="true">{t} <span class="car">&#9662;</span></a>'
                          f'<div class="menu">{links}</div></li>')
            else:
                items += f'<li><a href="{home}{h}">{t}</a></li>'
        return (f'<nav class="nav"><div class="wrap"><a class="brand" href="{R or './'}" aria-label="Aviac, home"><img class="m" src="{R}img/mark.svg" alt="">'
                f'<span class="wm">Aviac</span></a><ul>{items}</ul>'
                f'<a class="btn p cta" href="{home}#contact">Request a pilot</a><button class="burger" aria-label="Menu">&#9776;</button></div></nav>' + switcher(on, R))

    foot = (f'<footer><div class="wrap"><a class="brand" href="{R or './'}" aria-label="Aviac, home"><img class="m" src="{R}img/mark.svg" alt="" style="height:22px">'
            f'<span class="wm" style="font-size:19px">Aviac</span></a>'
            f'<span>aviactech@gmail.com</span><span>&copy; Aviac Technologies 2024&ndash;26. Specifications are design figures.</span></div></footer>')
    text = re.sub(r"\{\{HEAD ([^}]*)\}\}", head, text)
    text = re.sub(r"\{\{NAV (\w+)\}\}", nav, text)
    text = text.replace("{{FOOT}}", foot).replace("{{R}}", R)
    def mv(m):
        import hashlib
        d = os.path.join(SRC, "models", m.group(1))
        h = hashlib.sha1()
        for f in ("model.txt", "parts.json"):
            fp = os.path.join(d, f)
            if os.path.exists(fp):
                h.update(open(fp, "rb").read())
        return m.group(0) + f' data-v="{h.hexdigest()[:8]}"'
    text = re.sub(r'data-src="[^"]*models/(\w+)/"', mv, text)
    for a in ("assets/site.css", "assets/site.js", "img/mark.svg", "img/wordmark.svg", "viewer.js", "flight.js"):
        text = text.replace(a + '"', f'{a}?v={V}"')
    return text


if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, "img"))
open(os.path.join(OUT, "img", "mark.svg"), "w").write(svg_mark(GREEN))
open(os.path.join(OUT, "img", "wordmark.svg"), "w").write(svg_wordmark(GREEN))
open(os.path.join(OUT, "favicon.svg"), "w").write(svg_mark(IVORY).replace("<svg ", f'<svg style="background:{GREEN}" '))
for dp, _, fs in os.walk(SRC):
    rel = os.path.relpath(dp, SRC)
    for f in fs:
        src = os.path.join(dp, f)
        dst = os.path.join(OUT, f) if rel == "." else os.path.join(OUT, rel, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if f.endswith(".html"):
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            open(dst, "w").write(render(open(src).read(), "../" * depth))
        else:
            shutil.copy(src, dst)
shutil.copy(os.path.join(HERE, "vercel.json"), os.path.join(OUT, "vercel.json"))
total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print(f"website/public: {total / 1e6:.1f} MB")
