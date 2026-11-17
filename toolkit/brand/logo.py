#!/usr/bin/env python3
"""The Aviac Technologies mark and wordmark, traced from the supplied artwork.

src/aviac_technologies_reference.png is the logo as supplied. The mark and the wordmark were cropped from it,
upscaled 4x and traced with potrace (src/*.traced.svg for the outlines, src/*.geojson for flattened
polygons). Everything else reads from those traces, so the logo is never redrawn by hand:

  polygons()        the mark as closed polygons, centred, y up, 1.0 tall: for CAD etching
  svg_mark(fill)    the mark alone, for headers and loading screens
  svg_wordmark(fill)
  svg_lockup()      mark over "Aviac Technologies" on the brand green, as supplied
Run this file to write mark.svg, wordmark.svg and lockup.svg next to it.

Brand colours sampled from the artwork: green #18241e, ivory #f2f1eb.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, IVORY = "#18241e", "#f2f1eb"


def polygons():
    feats = json.load(open(os.path.join(HERE, "src", "mark.geojson")))["features"]
    rings = [f["geometry"]["coordinates"][0] for f in feats]
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    cx, y0, h = (min(xs) + max(xs)) / 2, min(ys), max(ys) - min(ys)
    out = []
    for r in rings:
        pts = [((x - cx) / h, (y - y0) / h - 0.5) for (x, y) in r]
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        out.append(pts)
    return out


def _inner(name, fill):
    s = open(os.path.join(HERE, "src", f"{name}.traced.svg")).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    g = s[s.index("<g "):s.rindex("</g>") + 4].replace('fill="#000000"', f'fill="{fill}"')
    return vb, g


def svg_mark(fill=IVORY):
    vb, g = _inner("mark", fill)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{g}</svg>'


def svg_wordmark(fill=IVORY):
    vb, g = _inner("wordmark", fill)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{g}</svg>'


def svg_lockup(bg=GREEN, fill=IVORY):
    # positions in the supplied artwork (1210 x 558): mark crop at (50,150) 320 x 235, wordmark crop at (60,415) 1035 x 130
    _, gm = _inner("mark", fill)
    _, gw = _inner("wordmark", fill)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1210 558"><rect width="1210" height="558" fill="{bg}"/>'
            f'<g transform="translate(50 150) scale(0.25)">{gm}</g><g transform="translate(60 415) scale(0.25)">{gw}</g></svg>')


if __name__ == "__main__":
    open(os.path.join(HERE, "mark.svg"), "w").write(svg_mark(GREEN))
    open(os.path.join(HERE, "wordmark.svg"), "w").write(svg_wordmark(GREEN))
    open(os.path.join(HERE, "lockup.svg"), "w").write(svg_lockup())
    for old in ("logo.svg",):
        if os.path.exists(os.path.join(HERE, old)):
            os.remove(os.path.join(HERE, old))
    print("wrote mark.svg, wordmark.svg, lockup.svg;", len(polygons()), "polygons")
