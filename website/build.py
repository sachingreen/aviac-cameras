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

NAV = [("systems", "Systems", "#systems", [("ms", "MS", "product/multispectral/", "Agri Spectral · six bands"), ("duos", "Duos", "product/duos/", "Stereo · spray drones")]),
       ("field", "In the field", "#field", None), ("research", "Research", "#research", None), ("company", "Company", "#company", None)]


def render(text, R):
    def head(m):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{m.group(1)}</title>
<meta name="description" content="Aviac Technologies builds multispectral and stereo drone cameras with edge AI for precision agriculture.">
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
        return (f'<nav class="nav"><div class="wrap"><a class="brand" href="{R}" aria-label="Aviac Technologies, home"><img class="m" src="{R}img/mark.svg" alt="">'
                f'<img class="w" src="{R}img/wordmark.svg" alt=""></a><ul>{items}</ul>'
                f'<a class="btn p cta" href="{home}#contact">Request a pilot</a><button class="burger" aria-label="Menu">&#9776;</button></div></nav>')

    foot = (f'<footer><div class="wrap"><a class="brand" href="{R}"><img class="m" src="{R}img/mark.svg" alt="" style="height:22px">'
            f'<img class="w" src="{R}img/wordmark.svg" alt="Aviac Technologies" style="height:13px"></a>'
            f'<span>aviactech@gmail.com</span><span>&copy; Aviac Technologies 2024&ndash;26. Specifications are design figures.</span></div></footer>')
    text = re.sub(r"\{\{HEAD ([^}]*)\}\}", head, text)
    text = re.sub(r"\{\{NAV (\w+)\}\}", nav, text)
    return text.replace("{{FOOT}}", foot).replace("{{R}}", R)


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
