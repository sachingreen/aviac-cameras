#!/usr/bin/env python3
"""Aviac mark, vectorised from the supplied logo (two pairs of wings over a trident body).

One source for every use: polygons() for CAD etching, svg() for the web pages. Coordinates are the
600 x 600 artwork space of the original image, y down. Run this file to write logo.svg next to it.
"""
import os

# cubic bezier outlines of the left half; the right half is the mirror image about x = 300
LEFT = [
    # upper wing: tip at the top left, sweeps down to the centre
    [(80, 140), (178, 150, 238, 220, 252, 292), (196, 280, 100, 238, 80, 140)],
    # lower wing: long and thin, below the upper one
    [(22, 234), (112, 236, 202, 266, 248, 302), (176, 318, 76, 292, 22, 234)],
    # inner sliver beside the stem
    [(244, 334), (254, 336, 266, 340, 272, 344), (268, 362, 264, 380, 258, 398), (254, 378, 250, 356, 244, 334)],
]
# the body: two arms that meet in a stem tapering to a point (drawn whole, symmetric)
BODY = [(226, 290), (300, 326), (374, 290), (362, 312), (314, 350), (305, 536), (295, 536), (286, 350), (238, 312)]


def _bez(p0, c, n=14):
    (x0, y0), (x1, y1, x2, y2, x3, y3) = p0, c
    out = []
    for i in range(1, n + 1):
        t = i / n
        a, b, cc, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * x0 + b * x1 + cc * x2 + d * x3, a * y0 + b * y1 + cc * y2 + d * y3))
    return out


def polygons():
    """Closed polygons in artwork space (y down)."""
    out = []
    for path in LEFT:
        pts = [path[0]]
        for seg in path[1:]:
            pts += _bez(pts[-1], seg)
        pts = pts[:-1]
        out.append(pts)
        out.append([(600 - x, y) for (x, y) in reversed(pts)])
    out.append(list(BODY))
    return out


def svg(fill="#e8ecef", ring="#1d1f22", contours=True):
    def d(path):
        s = f"M{path[0][0]} {path[0][1]}"
        for seg in path[1:]:
            s += " C" + " ".join(str(v) for v in seg)
        return s + "Z"
    paths = [d(p) for p in LEFT]
    body = "M" + " L".join(f"{x} {y}" for x, y in BODY) + "Z"
    topo = ""
    if contours:
        topo = '<g fill="none" stroke="#5b6066" stroke-width="1.2" opacity=".55">' + "".join(
            f'<path d="M{-20} {80 + 70 * i} C 150 {40 + 70 * i}, 260 {150 + 70 * i}, 420 {90 + 70 * i} S 640 {160 + 70 * i}, 640 {120 + 70 * i}"/>' for i in range(8)) + "</g>"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600"><defs><clipPath id="c"><circle cx="300" cy="300" r="298"/></clipPath></defs>'
            f'<circle cx="300" cy="300" r="298" fill="{ring}"/><g clip-path="url(#c)">{topo}</g>'
            f'<g fill="{fill}">' + "".join(f'<path d="{p}"/><path d="{p}" transform="translate(600 0) scale(-1 1)"/>' for p in paths)
            + f'<path d="{body}"/></g></svg>')


def svg_mark(fill="currentColor"):
    """The mark alone, no disc: for headings and the loading screen."""
    def d(path):
        s = f"M{path[0][0]} {path[0][1]}"
        for seg in path[1:]:
            s += " C" + " ".join(str(v) for v in seg)
        return s + "Z"
    paths = [d(p) for p in LEFT]
    body = "M" + " L".join(f"{x} {y}" for x, y in BODY) + "Z"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 120 580 430"><g fill="{fill}">'
            + "".join(f'<path d="{p}"/><path d="{p}" transform="translate(600 0) scale(-1 1)"/>' for p in paths) + f'<path d="{body}"/></g></svg>')


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(here, "logo.svg"), "w").write(svg())
    open(os.path.join(here, "mark.svg"), "w").write(svg_mark("#1d1f22"))
    print("wrote logo.svg, mark.svg")
