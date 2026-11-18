#!/usr/bin/env python3
"""Aviac MS and Aviac Duos, rugged-body generation (CadQuery).

One family: a rounded body with chamfered corner bumpers and rails, a recessed front panel inside a frame
with a gasket line, the same lens ring on every lens, an amber status LED, side vents under a debossed Aviac
wing mark. Both are drawn lens-forward.

Frame: X to the right, Y into the body (the front face is y = 0, lenses stick out to -y), Z up. Units: mm.
Parts carry `group` = the teardown stage (Optics / Baseboard + image sensors / Processing board / Externals),
`explode` = where the side-scroll moves them, and `finish` = the colourway role (body, bumper, panel).

  python3 toolkit/cad/rugged_cameras.py ms     -> cameras/ms/mechanical/out/
  python3 toolkit/cad/rugged_cameras.py duos   -> cameras/duos/mechanical/out/
"""
import base64, json, math, os, struct, sys
import cadquery as cq

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "toolkit", "brand"))
from logo import polygons as logo_polygons

V = cq.Vector
OPT, SEN, PROC, EXT = "Optics", "Baseboard + image sensors", "Processing board", "Externals"
PA12CF = 1.15          # g/cm3, PA12 carbon-fibre nylon
ALU = 2.70
parts = []


def add(name, solid, group, explode=(0, 0, 0), mat="powder", color=(0.2, 0.2, 0.2), finish=None, density=None, mass=None, label=None):
    parts.append(dict(name=name, solid=solid, group=group, explode=explode, mat=mat, color=color, finish=finish,
                      density=density, mass=mass, label=label or name))


def W(s):
    return cq.Workplane("XY").add(s) if isinstance(s, cq.Shape) else s


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def rbox(x0, x1, y0, y1, z0, z1, r, axis="|Y"):
    s = box(x0, x1, y0, y1, z0, z1)
    if r > 0:
        try:
            s = s.edges(axis).fillet(min(r, (x1 - x0) / 2.01, (z1 - z0) / 2.01))
        except Exception:
            pass
    return s


def ycyl(x, z, y0, y1, r):
    """Cylinder along Y from y0 to y1."""
    return W(cq.Solid.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0)))


def yring(x, z, y0, y1, ro, ri):
    return ycyl(x, z, y0, y1, ro).cut(ycyl(x, z, y0 - 1, y1 + 1, ri))


def zcyl(x, y, z0, z1, r):
    return W(cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1)))


def chamfered(x0, x1, y0, y1, z0, z1, c):
    s = box(x0, x1, y0, y1, z0, z1)
    try:
        s = s.edges().chamfer(c)
    except Exception:
        pass
    return s


def mark_on_side(height, y, z, x_face, depth):
    """The Aviac wing mark as a solid to cut into the +X side face, centred at (y, z)."""
    sol = None
    for poly in logo_polygons():
        pts = [(-px * height, py * height) for (px, py) in poly]       # mirror so it reads correctly from +X
        w = cq.Workplane("YZ").polyline(pts).close().extrude(depth + 0.5).translate((x_face - depth, y, z))
        sol = w if sol is None else sol.union(w)
    return sol


# ------------------------------------------------------------------ the shared rugged body
def soft_box(x0, x1, y0, y1, z0, z1, R, r):
    """Rounded block: radius R on the edges that run front to back, r on every other edge."""
    s = rbox(x0, x1, y0, y1, z0, z1, R)
    try:
        s = s.faces("<Y or >Y").edges().fillet(r)
    except Exception:
        try:
            s = s.edges("not |Y").fillet(r * 0.6)
        except Exception:
            pass
    return s


def rugged_body(Wd, H, D, R, FT, frame, recess, wall, panel_r, ex_front, ex_rear, rails=False, bumpers=True, bump=1.0, cap=None, soft=2.0):
    """Moulded body: soft edges all round, split at y = FT into a front shell and a rear housing, a recessed panel opening
    with a chamfered lip and a gasket line, and overmoulded corner bumpers that hug the eight corners."""
    x0, x1, z0, z1 = -Wd / 2, Wd / 2, 0.0, H
    px0, px1, pz0, pz1 = x0 + frame, x1 - frame, z0 + frame, z1 - frame
    rear_end = D if cap is None else cap
    outer = soft_box(x0, x1, 0, rear_end, z0, z1, R, soft)
    inner = rbox(x0 + wall, x1 - wall, recess + wall, rear_end - wall, z0 + wall, z1 - wall, max(0.5, R - wall))
    shell = outer.cut(inner)
    shell = shell.cut(rbox(px0, px1, -1, recess + wall + 0.01, pz0, pz1, panel_r))                              # panel opening
    try:
        pcx, pcz = (px0 + px1) / 2, (pz0 + pz1) / 2
        lip = (cq.Workplane("XZ", origin=(pcx, 0.0, pcz)).rect(px1 - px0 + 2.2, pz1 - pz0 + 2.2)
               .workplane(offset=-1.1).rect(px1 - px0, pz1 - pz0).loft(combine=True)).translate((0, -0.01, 0))
        if lip.val().Volume() > 0 and lip.val().isValid():
            shell = shell.cut(lip)                                                                               # chamfered lip
    except Exception as e:
        print("lip skipped", e)
    g = 0.6
    shell = shell.cut(rbox(px0 - 2.6 - g, px1 + 2.6 + g, -1, 0.45, pz0 - 2.6 - g, pz1 + 2.6 + g, panel_r + 2.6 + g)
                      .cut(rbox(px0 - 2.6, px1 + 2.6, -2, 1, pz0 - 2.6, pz1 + 2.6, panel_r + 2.6)))              # gasket line
    split = box(x0 - 5, x1 + 5, FT, rear_end + 5, z0 - 5, z1 + 5)
    seam = soft_box(x0 - 2, x1 + 2, FT - 0.3, FT + 0.3, z0 - 2, z1 + 2, R + 2, 0.2).cut(rbox(x0 + 0.45, x1 - 0.45, FT - 1, FT + 1, z0 + 0.45, z1 - 0.45, R - 0.45))
    fs = shell.cut(split).cut(seam)
    rh = shell.intersect(split).cut(seam)
    add("front_shell", fs, EXT, ex_front, finish="body", density=PA12CF, label="Front shell, PA12-CF, 1.5 mm walls")
    panel = rbox(px0, px1, recess, recess + wall, pz0, pz1, panel_r)
    if bumpers:
        skin = soft_box(x0 - bump, x1 + bump, -bump * 0.6, rear_end + bump * 0.6, z0 - bump, z1 + bump, R + bump, soft + bump).cut(outer)
        c = min(13.0, H * 0.28)
        for nm, (ya, yb), ex in (("bumpers_front", (-5, c), ex_front), ("bumpers_rear", (rear_end - c, rear_end + 5), ex_rear)):
            corners = None
            for sx in (-1, 1):
                for sz in (-1, 1):
                    xa, xb = (x0 - 5, x0 + c) if sx < 0 else (x1 - c, x1 + 5)
                    za, zb = (z0 - 5, z0 + c) if sz < 0 else (z1 - c, z1 + 5)
                    k = box(xa, xb, ya, yb, za, zb)
                    corners = k if corners is None else corners.union(k)
            add(nm, skin.intersect(corners), EXT, ex, finish="bumper", density=1.2, label="Corner bumpers, overmoulded TPU")
    return fs, panel, rh, (px0, px1, pz0, pz1), rear_end


def rr_wire(w, h, r, y, zc, n=10):
    """Rounded rectangle in the XZ plane at depth y, as a closed polygon (n points per corner)."""
    r = max(0.3, min(r, w / 2 - 0.01, h / 2 - 0.01))
    pts = []
    for (cx, cz, a0) in ((w / 2 - r, zc + h / 2 - r, 0), (-w / 2 + r, zc + h / 2 - r, 90), (-w / 2 + r, zc - h / 2 + r, 180), (w / 2 - r, zc - h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append(V(cx + r * math.cos(a), y, cz + r * math.sin(a)))
    return cq.Wire.makePolygon(pts, close=True)


def sculpted_body(Wd, H, y0, D, R, FT, frame, recess, wall, panel_r, ex_front, ex_rear, taper, r_rear, hd, b):
    """A moulded body that tapers toward the back and rounds off at the rear, split at y = FT into a front shell and a
    rear housing. The front is a deep tunnel around the recessed panel; a TPU hood rings it and stands proud of every
    lens, so a fall lands on the hood, not the glass. Returns the panel rectangle and inset(y), the side inset at y."""
    zc = H / 2

    def inset(y):
        t = taper * max(0.0, (y - FT) / (D - FT))
        if y > D - r_rear:
            u = y - (D - r_rear)
            t += r_rear - math.sqrt(max(0.0, r_rear * r_rear - u * u))
        return t

    ys = [y0, FT] + [FT + (D - r_rear - FT) * i / 4 for i in range(1, 5)] + [D - r_rear + r_rear * math.sin(math.pi / 2 * i / 10) for i in range(1, 11)]
    ys = sorted(set(round(v, 4) for v in ys))

    def solid(off, ya, yb):
        sec = [y for y in ys if ya < y < yb]
        wires = [rr_wire(Wd - 2 * (inset(y) + off), H - 2 * (inset(y) + off), R - inset(y) - off, y, zc) for y in [ya] + sec + [yb]]
        return W(cq.Solid.makeLoft(wires, True))

    outer = solid(0.0, y0, D)
    inner = solid(wall, recess + wall, D - wall)
    px0, px1, pz0, pz1 = -Wd / 2 + frame, Wd / 2 - frame, frame, H - frame
    shell = outer.cut(inner).cut(rbox(px0, px1, y0 - 1, recess + wall + 0.01, pz0, pz1, panel_r))
    split = box(-Wd, Wd, FT, D + 5, -5, H + 5)
    seam = solid(-2.0, FT - 0.3, FT + 0.3).cut(solid(0.5, FT - 0.4, FT + 0.4))
    fs = shell.cut(split).cut(seam)
    rh = shell.intersect(split).cut(seam)
    add("front_shell", fs, EXT, ex_front, finish="body", density=PA12CF, label="Front shell, PA12-CF: the lens tunnel")
    panel = rbox(px0, px1, recess, recess + wall, pz0, pz1, panel_r)
    # hood: chamfered front edge, wraps the front 6 mm of the body, opening chamfered into the tunnel
    hw = [rr_wire(Wd + 2 * b - 2.4, H + 2 * b - 2.4, R + b - 1.2, y0 - hd, zc), rr_wire(Wd + 2 * b, H + 2 * b, R + b, y0 - hd + 1.2, zc),
          rr_wire(Wd + 2 * b, H + 2 * b, R + b, y0 + 6.0, zc)]
    hood = W(cq.Solid.makeLoft(hw, True)).cut(outer)
    ow = (px1 - px0, pz1 - pz0)
    mouth = W(cq.Solid.makeLoft([rr_wire(ow[0] + 3.0, ow[1] + 3.0, panel_r + 1.5, y0 - hd - 0.01, zc), rr_wire(ow[0], ow[1], panel_r, y0 - hd + 1.5, zc),
                                 rr_wire(ow[0], ow[1], panel_r, y0 + 1, zc)], True))
    hood = hood.cut(mouth)
    add("hood", hood, EXT, ex_front, finish="bumper", density=1.2, label="Protective hood, overmoulded TPU: stands proud of every lens")
    return fs, panel, rh, (px0, px1, pz0, pz1), inset


def lens_ring(name, x, z, y_front, y_panel, od, idia, group, ex):
    """The family lens ring: satin black, a stepped bezel, a fine bright chamfer on the front edge."""
    r = yring(x, z, y_front, y_panel, od / 2, idia / 2).union(yring(x, z, y_front + 1.2, y_panel, od / 2 + 0.8, od / 2 - 0.5))
    try:
        r = r.faces("<Y").edges().chamfer(0.35)
    except Exception:
        pass
    add(name + "_ring", r, group, ex, mat="satin", color=(0.035, 0.035, 0.038), mass=0.0, label="Lens ring")
    add(name + "_lip", yring(x, z, y_front - 0.05, y_front + 0.12, od / 2 - 0.45, od / 2 - 0.85), group, ex, mat="satin", color=(0.32, 0.33, 0.34), mass=0.0, label="Ring chamfer")


def dome(x, z, y_apex, r_edge, sag):
    """Spherical cap facing -y: apex at y_apex, rim radius r_edge, depth sag."""
    Rs = (r_edge * r_edge + sag * sag) / (2 * sag)
    sph = W(cq.Solid.makeSphere(Rs, V(x, y_apex + Rs, z)))
    return sph.intersect(ycyl(x, z, y_apex - 0.01, y_apex + sag, r_edge + 0.01))


def m12_lens(name, x, z, y_front, length, group, ex, tint, label, filt=None):
    """M12 lens seen from the front: knurled barrel, stepped black interior, a curved front element; optional band-pass
    filter as coated glass in front of it."""
    barrel = ycyl(x, z, y_front + 1.2, y_front + length, 7.0).union(ycyl(x, z, y_front, y_front + 5.0, 7.6))
    for k in range(24):
        a = 2 * math.pi * k / 24
        barrel = barrel.cut(ycyl(x + 7.75 * math.cos(a), z + 7.75 * math.sin(a), y_front + 1.4, y_front + 4.4, 0.42))
    barrel = barrel.cut(ycyl(x, z, y_front - 1, y_front + 2.2, 5.4)).cut(ycyl(x, z, y_front - 1, y_front + 3.4, 4.4))
    add(name + "_barrel", barrel, group, ex, mat="anodised", color=(0.015, 0.015, 0.018), mass=3.0 if length > 15 else 1.8, label=label)
    add(name + "_inner", yring(x, z, y_front + 3.3, y_front + 4.2, 4.4, 2.2), group, ex, mat="black", color=(0, 0, 0), mass=0.0, label="Aperture")
    add(name + "_glass", dome(x, z, y_front + 2.4, 4.3, 0.9), group, ex, mat="lens", color=tint, mass=0.0, label="Front element, multi-coated")
    if filt:
        add(name + "_filter", ycyl(x, z, y_front - 0.6, y_front - 0.1, 6.9), group, ex, mat="filterglass", color=filt[1], mass=0.4, label=f"Band-pass filter, {filt[0]}")


def etch_text(txt, size, x, z, y, kind="bold"):
    """Text laser-etched on a front face (reads from the front, -Y)."""
    t = cq.Workplane("XZ").text(txt, size, 0.06, kind=kind, halign="center", valign="center")
    bb = t.val().BoundingBox()
    return t.translate((x - (bb.xmin + bb.xmax) / 2, y - bb.ymax + 0.01, z - (bb.zmin + bb.zmax) / 2))


def export(out, name, extra_frame=None):
    os.makedirs(out, exist_ok=True)
    meta, total, by = [], 0.0, {}
    asm = cq.Assembly(name=name)
    for p in parts:
        shp = p["solid"].val()
        vol = shp.Volume() / 1000.0
        mass = p["mass"] if p["mass"] is not None else vol * (p["density"] or 1.2)
        total += mass
        by[p["group"]] = by.get(p["group"], 0) + mass
        fine = p["name"] in ("front_shell", "rear_housing", "bumpers_front", "bumpers_rear", "panel") or "ring" in p["name"] or "glass" in p["name"] or "dome" in p["name"]
        v, t = shp.tessellate(0.03 if fine else 0.06, 0.18 if fine else 0.3)
        pos = []
        for tri in t:
            for i in tri:
                pos += [v[i].x, v[i].y, v[i].z]
        bb = shp.BoundingBox()
        meta.append(dict(name=p["name"], label=p["label"], group=p["group"], color=p["color"], explode=p["explode"], mat=p["mat"], proxy=False,
                         finish=p["finish"], mass=round(mass, 2), estimated=p["mass"] is not None,
                         center=[round((bb.xmin + bb.xmax) / 2, 2), round((bb.ymin + bb.ymax) / 2, 2), round((bb.zmin + bb.zmax) / 2, 2)],
                         tris=len(pos) // 9, pos=base64.b64encode(struct.pack(f"<{len(pos)}f", *pos)).decode()))
        asm.add(p["solid"], name=p["name"], color=cq.Color(*[min(1, c) for c in p["color"]]))
    open(os.path.join(out, "model.js"), "w").write("window.AVIAC_MODEL=" + json.dumps(meta, separators=(",", ":")) + ";")
    json.dump(dict(board_origin=[0, 0, 0], flip=False, **(extra_frame or {})), open(os.path.join(out, "frame.json"), "w"))
    json.dump(FINISHES, open(os.path.join(out, "finishes.json"), "w"), indent=1)
    json.dump([{k: m[k] for k in ("name", "label", "group", "mass", "estimated")} for m in meta], open(os.path.join(out, "parts.json"), "w"), indent=1)
    asm.save(os.path.join(out, name + ".step"))
    for n in ("front_shell", "rear_housing", "panel"):
        s = next((p["solid"] for p in parts if p["name"] == n), None)
        if s is not None:
            cq.exporters.export(s, os.path.join(out, n + ".stl"), tolerance=0.05)
    bbs = [p["solid"].val().BoundingBox() for p in parts if p["group"] != "Mount"]
    print(f"{name}: {len(parts)} parts, {total:.0f} g")
    for g, m in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"   {m:6.1f} g  {g}")


def light_bar(panel, bar, recess, ex):
    """Thin status light: a slot in the panel with a diffused bar that blinks while capturing."""
    x, z, l, h = bar
    panel = panel.cut(rbox(x - l / 2 - 0.6, x + l / 2 + 0.6, -1, recess + 3, z - h / 2 - 0.6, z + h / 2 + 0.6, min(h / 2 + 0.6, 1.2)))
    add("light_bezel", rbox(x - l / 2 - 0.6, x + l / 2 + 0.6, recess - 0.4, recess + 1.5, z - h / 2 - 0.6, z + h / 2 + 0.6, min(h / 2 + 0.6, 1.2))
        .cut(rbox(x - l / 2, x + l / 2, recess - 1, recess + 2, z - h / 2, z + h / 2, h / 2.01)), EXT, ex, mat="satin", color=(0.04, 0.04, 0.045), mass=0.1, label="Light bar bezel")
    add("light_bar", rbox(x - l / 2, x + l / 2, recess - 0.2, recess + 1.4, z - h / 2, z + h / 2, h / 2.01), EXT, ex, mat="led", color=(1.0, 0.55, 0.12),
        mass=0.1, label="Status light bar, amber: blinks while capturing")
    return panel


# colourways: role -> material and colour (linear RGB)
FINISHES = {
    "titanium": {"body": {"mat": "blast", "color": [0.30, 0.30, 0.31]}, "bumper": {"mat": "knurl", "color": [0.012, 0.012, 0.013]},
                 "panel": {"mat": "glass_black", "color": [0.004, 0.004, 0.005]}},
    "graphite": {"body": {"mat": "blast", "color": [0.06, 0.062, 0.066]}, "bumper": {"mat": "knurl", "color": [0.01, 0.01, 0.011]},
                 "panel": {"mat": "glass_black", "color": [0.004, 0.004, 0.005]}},
    "arctic": {"body": {"mat": "gloss_white", "color": [0.80, 0.80, 0.79]}, "bumper": {"mat": "knurl", "color": [0.55, 0.55, 0.55]},
               "panel": {"mat": "glass_black", "color": [0.004, 0.004, 0.005]}},
    "gunmetal": {"body": {"mat": "powder", "color": [0.042, 0.045, 0.044]}, "bumper": {"mat": "powder", "color": [0.028, 0.03, 0.03]},
                 "panel": {"mat": "powder", "color": [0.034, 0.036, 0.035]}},
    "sand": {"body": {"mat": "powder", "color": [0.56, 0.49, 0.38]}, "bumper": {"mat": "powder", "color": [0.47, 0.41, 0.31]},
             "panel": {"mat": "powder", "color": [0.52, 0.455, 0.35]}},
    "stealth": {"body": {"mat": "powder", "color": [0.022, 0.022, 0.024]}, "bumper": {"mat": "rubberised", "color": [0.012, 0.012, 0.013]},
                "panel": {"mat": "satin", "color": [0.11, 0.11, 0.115]}},
    "bronze": {"body": {"mat": "powder", "color": [0.115, 0.07, 0.05]}, "bumper": {"mat": "rubberised", "color": [0.015, 0.014, 0.014]},
               "panel": {"mat": "satin", "color": [0.62, 0.53, 0.36]}},
}


# ------------------------------------------------------------------ parts that make a teardown read as real
import random
GREEN, BLACKPCB = (0.02, 0.20, 0.10), (0.02, 0.03, 0.025)


def pcb(name, x0, x1, z0, z1, y0, t, group, ex, label, mass, comps="front", seed=1, keep=(), color=GREEN, ics=(), r=0.0):
    """A board lying in the XZ plane at y0..y0+t, with passives scattered on one or both faces and listed ICs.
    keep: rectangles (x0, x1, z0, z1) to leave clear; ics: (x, z, w, h, height, side, label, kind)."""
    b = rbox(x0, x1, y0, y0 + t, z0, z1, r) if r else box(x0, x1, y0, y0 + t, z0, z1)
    add(name, b, group, ex, mat="pcb", color=color, mass=mass, label=label)
    rnd = random.Random(seed)
    pas = None
    sides = {"front": [-1], "rear": [1], "both": [-1, 1]}[comps]
    n = int((x1 - x0) * (z1 - z0) / 26)
    for k in range(n):
        x, z = rnd.uniform(x0 + 1.5, x1 - 1.5), rnd.uniform(z0 + 1.5, z1 - 1.5)
        if any(a <= x <= b2 and c <= z <= d for (a, b2, c, d) in keep) or (r and min(x - x0, x1 - x) < r and min(z - z0, z1 - z) < r):
            continue
        side = rnd.choice(sides)
        w, h = (1.0, 0.5) if rnd.random() < 0.7 else (1.6, 0.8)
        if rnd.random() < 0.5:
            w, h = h, w
        yy0, yy1 = (y0 - 0.45, y0) if side < 0 else (y0 + t, y0 + t + 0.45)
        c = box(x - w / 2, x + w / 2, yy0, yy1, z - h / 2, z + h / 2)
        pas = c if pas is None else pas.union(c)
    if pas is not None:
        add(name + "_passives", pas, group, ex, mat="ceramic", color=(0.62, 0.50, 0.36), mass=0.0, label="Passives")
    for i, (x, z, w, h, ht, side, lab, kind) in enumerate(ics):
        yy0, yy1 = (y0 - ht, y0) if side < 0 else (y0 + t, y0 + t + ht)
        mat, col = {"ic": ("ic", (0.03, 0.03, 0.033)), "conn": ("plastic_gloss", (0.80, 0.77, 0.68)), "steel": ("steel", (0.72, 0.72, 0.74)),
                    "ind": ("ferrite", (0.2, 0.2, 0.21)), "gold": ("gold", (0.8, 0.6, 0.2)), "black": ("plastic_gloss", (0.05, 0.05, 0.055)),
                    "xtal": ("steel", (0.7, 0.7, 0.72)), "sensor": ("ceramic_dark", (0.06, 0.06, 0.07))}[kind]
        add(f"{name}_c{i}", box(x - w / 2, x + w / 2, yy0, yy1, z - h / 2, z + h / 2), group, ex, mat=mat, color=col, mass=0.0, label=lab)


def screw(name, x, z, y_head, length, r, group, ex, label="Screw", head="pan", toward=-1):
    """Screw along Y. Head at y_head, shank runs into the part (toward = +1 into +y)."""
    hh = 0.8 * r if head == "pan" else 0.6 * r
    hd = ycyl(x, z, y_head - (hh if toward > 0 else 0), y_head + (0 if toward > 0 else hh), r * 1.8)
    try:
        hd = hd.faces("<Y" if toward > 0 else ">Y").edges().fillet(r * 0.5)
    except Exception:
        pass
    hd = hd.cut(W(cq.Workplane("XZ").polygon(6, r * 1.1).extrude(1.0).val()).translate((x, y_head - (hh + 0.4 if toward > 0 else -hh - 0.4) - (0 if toward > 0 else 1.0), z)))
    sh = ycyl(x, z, y_head, y_head + toward * length, r * 0.92) if toward > 0 else ycyl(x, z, y_head + toward * length, y_head, r * 0.92)
    add(name, hd.union(sh), group, ex, mat="steel_black", color=(0.05, 0.05, 0.055), mass=0.3 * r, label=label)


def zscrew(name, x, y, z_head, length, r, group, ex, label="Screw"):
    add(name, zcyl(x, y, z_head - 0.8 * r, z_head, r * 1.8).union(zcyl(x, y, z_head, z_head + length, r * 0.92)), group, ex, mat="steel_black", color=(0.05, 0.05, 0.055), mass=0.3 * r, label=label)


def standoff(name, x, z, y0, y1, r, group, ex, label="Standoff"):
    s = W(cq.Workplane("XZ").polygon(6, r * 2.3).extrude(-(y1 - y0)).val()).translate((x, y0, z)).cut(ycyl(x, z, y0 - 1, y1 + 1, r * 0.55))
    add(name, s, group, ex, mat="steel", color=(0.75, 0.62, 0.32), mass=0.4, label=label)


def m12_holder(name, x, z, y0, y1, group, ex):
    h = rbox(x - 9.5, x + 9.5, y0, y1, z - 7.5, z + 7.5, 1.2).union(rbox(x - 7.5, x + 7.5, y0, y1, z - 9.5, z + 9.5, 1.2))
    h = h.union(box(x - 13.5, x + 13.5, y1 - 2.0, y1, z - 3, z + 3)).cut(ycyl(x, z, y0 - 1, y1 + 1, 6.05))
    for sx in (-1, 1):
        h = h.cut(ycyl(x + sx * 11.5, z, y0 - 1, y1 + 1, 1.0))
    add(name, h, group, ex, mat="plastic_gloss", color=(0.04, 0.04, 0.045), mass=1.2, label="M12 lens holder")


def oring(name, x, z, y, ro, rs, group, ex):
    t = W(cq.Solid.makeTorus(ro, rs, V(x, y, z), V(0, 1, 0)))
    add(name, t, group, ex, mat="rubber", color=(0.02, 0.02, 0.022), mass=0.1, label="O-ring seal")


def ribbon(name, pts, width, group, ex, label):
    sol = None
    for (a, b) in zip(pts[:-1], pts[1:]):
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        if L < 0.05:
            continue
        seg = cq.Workplane("XY").box(width, L + 0.2, 0.15)
        seg = seg.rotate((0, 0, 0), (1, 0, 0), math.degrees(math.atan2(dz, math.hypot(dx, dy)))).rotate((0, 0, 0), (0, 0, 1), -math.degrees(math.atan2(dx, dy)))
        seg = seg.translate(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
        sol = seg if sol is None else sol.union(seg)
    add(name, sol, group, ex, mat="fpc", color=(0.8, 0.42, 0.05), mass=0.3, label=label)


def light_pipe(x, z, l, y0, y1, group, ex):
    add("light_pipe", rbox(x - l / 2, x + l / 2, y0, y1, z - 0.6, z + 0.6, 0.55), group, ex, mat="dome", color=(0.95, 0.95, 0.93), mass=0.1, label="Light pipe")


# ================================================================== Aviac MS: 96 x 90 x 90, 1 x IMX565 (C-mount) + 3 x Mira220 (M12)
def build_ms():
    Wd, H, D = 96.0, 90.0, 90.0
    FT, frame, recess, wall = 14.0, 6.0, 3.0, 1.5
    E = lambda y, z=0: (0, y, z)                                       # explode: along the depth, front parts toward the viewer
    EXF = E(-250)
    D = 80.0                                                            # rear stack moved 10 mm forward; the front tunnel starts at y = -10
    fs, panel, rh, (px0, px1, pz0, pz1), inset = sculpted_body(Wd, H, -10.0, D, 15.0, FT, frame, recess, wall, 6.0, EXF, E(150), taper=3.0, r_rear=10.0, hd=4.0, b=1.6)
    MIRA = [(-29.0, 21.0, "NIR+ 890", (0.16, 0.02, 0.10)), (-29.0, 45.0, "NIR 840", (0.33, 0.03, 0.12)), (-29.0, 69.0, "RE 723", (0.62, 0.05, 0.08))]
    cx, cz = 11.0, 45.0
    BAR = (32.0, 77.5, 16.0, 1.4)
    for (x, z, *_r) in MIRA:
        panel = panel.cut(ycyl(x, z, -1, 10, 7.7))
    panel = panel.cut(ycyl(cx, cz, -1, 10, 17.2))
    panel = light_bar(panel, BAR, recess, EXF)
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    for sx in (-1, 1):
        for zz in (7.0, H - 7.0):
            screw(f"front_screw_{sx}_{int(zz)}", sx * (Wd / 2 - 4.2), zz, -13.7, 16.0, 1.3, EXT, EXF, "M3 x 16, stainless, hood and front shell", toward=1)
    mk = etch_text("AVIAC MS", 3.0, cx, 13.0, recess)
    for (x, z, band, _t) in MIRA:
        mk = mk.union(etch_text(band.split()[0], 1.7, -15.0, z, recess))
    add("markings", mk, EXT, EXF, mat="etch", color=(0.7, 0.71, 0.73), mass=0.0, label="Laser-etched markings")
    add("gasket", W(cq.Solid.makeLoft([rr_wire(Wd - 1.2, H - 1.2, 14.4, FT - 0.25, H / 2), rr_wire(Wd - 1.2, H - 1.2, 14.4, FT + 0.25, H / 2)], True))
        .cut(W(cq.Solid.makeLoft([rr_wire(Wd - 2.6, H - 2.6, 13.7, FT - 1, H / 2), rr_wire(Wd - 2.6, H - 2.6, 13.7, FT + 1, H / 2)], True))),
        EXT, E(-200), mat="rubber", color=(0.85, 0.30, 0.08), mass=1.2, label="Silicone gasket, IP54 seal at the seam")
    light_pipe(BAR[0], BAR[1], BAR[2], recess + 1.4, 12.0, EXT, E(-215))

    # ---- 1. optics
    for i, (x, z, band, tint) in enumerate(MIRA):
        oring(f"mira{i}_oring", x, z, recess - 0.3, 8.6, 0.6, OPT, E(-225))
        lens_ring(f"mira{i}", x, z, -10.0, recess, 20.0, 15.6, OPT, E(-190))
        add(f"mira{i}_retainer", yring(x, z, -10.3, -9.7, 7.6, 6.2), OPT, E(-196), mat="satin", color=(0.2, 0.2, 0.21), mass=0.1, label="Filter retaining ring")
        m12_lens(f"mira{i}", x, z, -9.0, 25.0, OPT, E(-165), (0.10, 0.22, 0.20), "M12 lens, 6 mm, 25 mm long", filt=(band, tint))
        m12_holder(f"mira{i}_holder", x, z, 8.5, 17.0, OPT, E(-120))
    oring("imx_oring", cx, cz, recess - 0.3, 18.6, 0.7, OPT, E(-225))
    lens_ring("imx", cx, cz, -12.0, recess, 44.0, 34.0, OPT, E(-190))
    cb = ycyl(cx, cz, -12.0, 18.0, 15.5).cut(ycyl(cx, cz, -13, -9.5, 11.5))
    for (ya, yb) in ((-8.0, -3.0), (0.0, 4.5)):
        for k in range(36):
            a = 2 * math.pi * k / 36
            cb = cb.cut(ycyl(cx + 15.6 * math.cos(a), cz + 15.6 * math.sin(a), ya, yb, 0.55))
    cb = cb.union(ycyl(cx, cz, 18.0, 22.0, 12.7))                                               # C-mount thread
    LE = E(-165)
    add("imx_barrel", cb, OPT, LE, mat="anodised", color=(0.015, 0.015, 0.018), mass=45.0, label="C-mount lens, 16 mm, 1.1-inch, compact")
    add("imx_inner", yring(cx, cz, -9.6, -4.0, 11.5, 7.5).union(yring(cx, cz, -4.0, -3.0, 11.5, 5.0)), OPT, LE, mat="black", color=(0, 0, 0), mass=0.0, label="Lens interior")
    add("imx_glass", dome(cx, cz, -11.3, 11.4, 2.2), OPT, LE, mat="lens", color=(0.10, 0.24, 0.20), mass=0.0, label="Front element, multi-coated")
    add("imx_iris", yring(cx, cz, -6.0, -5.4, 11.5, 2.6).union(ycyl(cx, cz, -3.2, -2.8, 11.5)), OPT, LE, mat="black", color=(0, 0, 0), mass=0.0, label="Aperture")
    add("imx_retainer", yring(cx, cz, -11.6, -10.9, 12.6, 11.4), OPT, LE, mat="satin", color=(0.25, 0.25, 0.26), mass=0.0, label="Retaining ring")
    LP0, LP1 = recess + wall, recess + wall + 2.0
    lp = rbox(px0 + 1, px1 - 1, LP0, LP1, pz0 + 1, pz1 - 1, 4.0)
    for (x, z, *_r) in MIRA:
        lp = lp.cut(ycyl(x, z, LP0 - 1, LP1 + 1, 6.2))
        for sx in (-1, 1):
            lp = lp.cut(ycyl(x + sx * 11.5, z, LP0 - 1, LP1 + 1, 1.0))
    lp = lp.cut(ycyl(cx, cz, LP0 - 1, LP1 + 1, 16.2)).union(yring(cx, cz, LP1 - 0.01, 22.0, 15.2, 12.8))   # C-mount boss
    for (x, z) in ((-40, 8), (-40, 82), (40, 8), (40, 82)):
        lp = lp.cut(ycyl(x, z, LP0 - 1, LP1 + 1, 1.3))
    add("lens_plate", lp, OPT, E(-100), mat="satin", color=(0.55, 0.56, 0.58), density=ALU, label="Lens and filter plate, aluminium, 2 mm: holds all four optical axes")
    for (x, z) in ((-40, 8), (-40, 82), (40, 8), (40, 82)):
        screw(f"lp_screw_{x}_{z}", x, z, LP0 - 0.01, 6.0, 1.0, OPT, E(-108), "M2 x 6, lens plate", toward=1)
    add("ircut", box(cx - 12, cx + 12, 27.0, 27.8, cz - 10, cz + 10), OPT, E(-80), mat="filterglass", color=(0.30, 0.55, 0.62), mass=0.8, label="IR-cut filter, 400-680 nm (RGB)")
    hold = rbox(cx - 20, cx + 20, 22.0, 32.3, cz - 20, cz + 20, 2.0).cut(rbox(cx - 13, cx + 13, 21, 33, cz - 11, cz + 11, 1.0))
    add("imx_holder", hold, OPT, E(-88), mat="plastic_gloss", color=(0.04, 0.04, 0.045), mass=3.0, label="C-mount to sensor spacer, sets the 17.53 mm flange distance")

    # ---- 2. baseboard + image sensors
    for i, (x, z, *_r) in enumerate(MIRA):
        pcb(f"mira{i}_pcb", x - 11, x + 11, z - 11, z + 11, 17.0, 1.6, SEN, E(-60), "Mira220 sensor board", 2.0, comps="rear", seed=10 + i,
            ics=[(x, z, 6.6, 6.2, 0.9, -1, "ams OSRAM Mira220, 1600 x 1400 global shutter", "sensor"), (x + 6, z, 4, 12, 2.0, 1, "22-pin FPC connector", "conn"),
                 (x - 6, z - 5, 3, 3, 1.0, 1, "LDO", "ic"), (x - 6, z + 5, 2, 1.2, 0.8, 1, "Oscillator", "xtal")])
        for sx in (-1, 1):
            screw(f"mira{i}_screw{sx}", x + sx * 11.5, z, 18.65, 9.0, 0.8, SEN, E(-55), "M1.6 holder screw", toward=-1)
    pcb("imx_pcb", cx - 29.5, cx + 29.5, cz - 31.5, cz + 31.5, 34.0, 1.6, SEN, E(-40), "IMX565 sensor board, 59 x 63 mm", 9.0, comps="both", seed=20, color=BLACKPCB,
        keep=((cx - 12, cx + 12, cz - 10, cz + 10),),
        ics=[(cx, cz, 20, 16.8, 1.7, -1, "Sony IMX565, 12.4 MP global shutter", "sensor"), (cx + 20, cz + 23, 22, 3, 2.8, 1, "100-pin board-to-board", "conn"),
             (cx - 18, cz - 20, 5, 5, 1.0, 1, "PMIC", "ic"), (cx + 15, cz - 22, 4, 4, 0.9, 1, "Sensor clock", "xtal")])
    for (x, z) in ((cx - 27, cz - 29), (cx + 27, cz - 29), (cx - 27, cz + 29), (cx + 27, cz + 29)):
        standoff(f"imx_so_{x}_{z}", x, z, 32.3, 34.0, 1.2, SEN, E(-45))
        screw(f"imx_screw_{x}_{z}", x, z, 35.6, 5.0, 1.0, SEN, E(-36), "M2 x 5", toward=-1)
    for i, (x, z, *_r) in enumerate(MIRA):
        ribbon(f"mira{i}_fpc", [(x + 6, 19.5, z), (x + 6, 26.0, z), (x + 3, 38.5, z - 6 + i * 2), (x + 3, 40.0, z - 6 + i * 2)], 8.0, SEN, E(-30), "22-way FPC, 2-lane MIPI")
    pcb("baseboard", -43, 43, 4.0, 86.0, 40.0, 1.6, SEN, E(-15), "Sensor baseboard: trigger sync, power, 4 x 2-lane MIPI to the carrier", 11.0, comps="both", seed=30,
        keep=((-36, -18, 10, 80),), r=11.0,
        ics=[(-26, 15, 6, 12, 1.5, -1, "FPC connector, NIR+", "conn"), (-26, 39, 6, 12, 1.5, -1, "FPC connector, NIR", "conn"), (-26, 63, 6, 12, 1.5, -1, "FPC connector, RE", "conn"),
             (cx + 20, cz + 23, 22, 3, 1.6, -1, "100-pin board-to-board", "conn"), (-36, 45, 5, 5, 1.0, 1, "Sync MCU", "ic"), (-30, 30, 3.2, 2.5, 0.8, 1, "TCXO", "xtal"),
             (20, 12, 5, 5, 3.0, 1, "Inductor", "ind"), (30, 12, 5, 5, 3.0, 1, "Inductor", "ind"), (-30, 80, 14, 4, 4.0, 1, "Board-to-carrier connector", "conn")])
    for (x, z) in ((-40, 8), (-40, 82), (40, 8), (40, 82)):
        standoff(f"bb_so_{x}_{z}", x, z, LP1, 40.0, 1.5, SEN, E(-70), "Standoff, lens plate to baseboard")

    # ---- 3. processing board
    pcb("carrier", -43.5, 43.5, 19.0, 71.0, 46.0, 1.6, PROC, E(20), "Jetson carrier, 87 x 52 mm", 16.0, comps="both", seed=40, keep=((-35, 35, 21, 70),),
        ics=[(-30, 66, 14, 4, 3.0, -1, "Board-to-board", "conn"), (25, 30, 22, 30, 2.2, -1, "M.2 2230 NVMe SSD", "black"), (25, 30, 9, 9, 2.5, -1, "SSD controller", "ic"),
             (-25, 30, 6, 6, 3.0, -1, "Power inductor", "ind"), (-15, 30, 6, 6, 3.0, -1, "Power inductor", "ind"), (-20, 50, 5, 5, 1.2, -1, "PMIC", "ic"),
             (0, 26, 72, 8, 3.4, 1, "260-pin SO-DIMM socket", "black")])
    for (x, z) in ((-40, 22), (40, 22), (-40, 68), (40, 68)):
        standoff(f"car_so_{x}_{z}", x, z, 41.6, 46.0, 1.4, PROC, E(10), "Standoff, baseboard to carrier")
    jy = 51.0
    add("jetson", box(-34.8, 34.8, jy, jy + 1.2, 24.0, 69.0), PROC, E(45), mat="pcb", color=(0.02, 0.10, 0.06), mass=28.0, label="Jetson Orin NX / Nano module")
    add("jetson_soc", box(-12, 12, jy + 1.2, jy + 3.6, 40.0, 64.0), PROC, E(45), mat="alu", color=(0.6, 0.6, 0.62), mass=0.0, label="Orin SoC, integrated heat spreader")
    for i, zz in enumerate((30.0, 36.0)):
        add(f"jetson_ram{i}", box(16, 30, jy + 1.2, jy + 2.3, zz - 2.5, zz + 2.5), PROC, E(45), mat="ic", color=(0.03, 0.03, 0.033), mass=0.0, label="LPDDR5")
    add("jetson_gold", box(-34, 34, jy - 0.01, jy + 1.21, 24.0, 26.0), PROC, E(45), mat="gold", color=(0.8, 0.6, 0.2), mass=0.0, label="Edge connector")
    for sx in (-1, 1):
        standoff(f"mod_so{sx}", sx * 31.5, 66.0, 47.6, jy, 1.3, PROC, E(35), "Module standoff")
        screw(f"mod_screw{sx}", sx * 31.5, 66.0, jy + 1.2, 4.0, 1.0, PROC, E(52), "M2 x 4, module", toward=-1)
    add("tim_pad", box(-12, 12, jy + 3.6, jy + 4.1, 40.0, 64.0), PROC, E(62), mat="rubber", color=(0.55, 0.60, 0.68), mass=0.6, label="Thermal pad, 0.5 mm")
    add("spreader", box(-13, 13, jy + 4.1, jy + 6.1, 35.0, 65.0), PROC, E(70), mat="alu", color=(0.62, 0.63, 0.65), density=ALU, label="Heat spreader")
    add("heat_pipe", ycyl(-4, 38.5, jy + 6.1, D - 8.0, 3.0).union(ycyl(4, 38.5, jy + 6.1, D - 8.0, 3.0)), PROC, E(70), mat="gold", color=(0.75, 0.42, 0.25),
        mass=9.0, label="2 x 6 mm heat pipes to the rear heatsink")

    # ---- 4. externals: rear housing, heatsink, fan, I/O, mount, DLS puck
    # ribbed rubber grips on both sides (the 6-camera design's signature) and the wing mark above them
    for sx in (-1, 1):
        xf = sx * (Wd / 2 - inset(40.0))
        pad = rbox(min(xf - sx * 0.8, xf + sx * 0.4), max(xf - sx * 0.8, xf + sx * 0.4), 24.0, 56.0, 20.0, 54.0, 3.0, "|X")
        for k in range(8):
            yy = 26.5 + k * 3.9
            pad = pad.union(rbox(min(xf, xf + sx * 1.8), max(xf, xf + sx * 1.8), yy - 1.0, yy + 1.0, 21.5, 52.5, 0.8, "|Y"))
        add(f"grip_{sx}", pad, EXT, E(150), mat="rubberised", color=(0.015, 0.015, 0.017), density=1.2, label="Ribbed TPU grip")
    try:
        rh = rh.cut(mark_on_side(18.0, 40.0, 69.0, Wd / 2 - inset(40.0), 0.6))
    except Exception as e:
        print("mark skipped", e)
    HX0, HX1, HZ0, HZ1 = -30.0, 30.0, 30.0, 84.0
    rh = rh.cut(rbox(HX0, HX1, D - 3, D + 1, HZ0, HZ1, 4.0))
    PORTS = ((-30, 16.0, 8.0, "xt30"), (-8, 12.0, 9.5, "eth"), (9, 9.0, 3.4, "usb"), (24, 0, 0, "gps"), (35, 0, 0, "dls"))
    for (x, w, h, kind) in PORTS:
        rh = rh.cut(ycyl(x, 15.0, D - 3, D + 1, 3.7 if kind == "dls" else 4.2) if kind in ("gps", "dls") else box(x - w / 2, x + w / 2, D - 3, D + 1, 15 - h / 2, 15 + h / 2))
    for k in range(5):
        for sx in (-1, 1):
            rh = rh.cut(rbox(sx * 38 - 3, sx * 38 + 3, D - 3, D + 1, 40 + k * 7, 43 + k * 7, 1.2))
    add("rear_housing", rh, EXT, E(150), finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    hs = rbox(HX0 - 2, HX1 + 2, D - 8.0, D - 6.5, HZ0 - 2, HZ1 + 2, 5.0)
    for k in range(14):
        x = HX0 + 2.0 + k * 4.0
        hs = hs.union(box(x - 0.5, x + 0.5, D - 6.51, D - 0.3, HZ0 + 1.5, HZ1 - 1.5))
    add("heatsink", hs, EXT, E(120), mat="satin", color=(0.48, 0.49, 0.5), density=ALU, label="Finned aluminium heatsink insert")
    add("hs_pad", box(-9, 9, D - 8.5, D - 8.0, 34.0, 43.0), EXT, E(105), mat="rubber", color=(0.55, 0.60, 0.68), mass=0.3, label="Thermal pad, heat pipes to heatsink")
    for (x, z) in ((HX0 - 0.5, HZ0 - 0.5), (HX1 + 0.5, HZ0 - 0.5), (HX0 - 0.5, HZ1 + 0.5), (HX1 + 0.5, HZ1 + 0.5)):
        screw(f"hs_screw_{x}_{z}", x, z, D - 6.5, 4.0, 0.8, EXT, E(128), "M1.6 heatsink screw", toward=1)
    fan = box(-15, 15, D - 18.0, D - 11.0, 42.0, 72.0).cut(ycyl(0, 57.0, D - 19, D - 10, 13.6))
    hub = ycyl(0, 57.0, D - 17.5, D - 11.5, 5.0)
    for k in range(7):
        a = 2 * math.pi * k / 7
        bl = box(-1.0, 1.0, D - 16.5, D - 12.5, 0, 8.0).rotate((0, 0, 0), (0, 1, 0), math.degrees(a)).rotate((0, D - 14.5, 0), (0, D - 14.5, 1), 18).translate((0, 0, 57.0))
        hub = hub.union(bl.intersect(ycyl(0, 57.0, D - 18, D - 11, 13.2)))
    for (x, z) in ((-12.5, 44.5), (12.5, 44.5), (-12.5, 69.5), (12.5, 69.5)):
        fan = fan.cut(ycyl(x, z, D - 19, D - 10, 1.2))
    add("fan", fan, EXT, E(85), mat="plastic_gloss", color=(0.05, 0.05, 0.055), mass=4.0, label="30 mm fan, 5 V")
    add("fan_rotor", hub, EXT, E(85), mat="plastic_gloss", color=(0.07, 0.07, 0.075), mass=2.0, label="Fan rotor")
    for (x, z) in ((-12.5, 44.5), (12.5, 44.5), (-12.5, 69.5), (12.5, 69.5)):
        screw(f"fan_screw_{x}_{z}", x, z, D - 18.2, 9.0, 0.9, EXT, E(78), "Fan screw", toward=1)
    pcb("io_board", -41, 41, 5.0, 26.0, D - 8.0, 1.6, EXT, E(100), "Rear I/O board", 4.0, comps="front", seed=50, r=9.0,
        ics=[(-30, 15, 14, 7, 6.0, 1, "XT30 power in, 3S-6S", "conn"), (-8, 15, 11, 9, 6.0, 1, "Ethernet", "steel"), (9, 15, 8.6, 3.2, 6.0, 1, "USB-C", "steel"),
             (24, 15, 7.5, 7.5, 6.0, 1, "GPS / PPS, 8-pin", "gold"), (35, 15, 6.8, 6.8, 6.0, 1, "DLS port", "gold"), (0, 22, 10, 3, 1.5, -1, "Cable to carrier", "conn")])
    ribbon("io_cable", [(0, D - 8.1, 22), (0, D - 18.0, 22), (0, 49.0, 22), (0, 47.7, 22)], 9.0, EXT, E(90), "Cable, I/O board to carrier")
    br = rbox(-30, 30, 22.0, 70.0, -3.2, -0.2, 3.0, "|Z")
    for sx in (-1, 1):
        for sy in (28.0, 64.0):
            br = br.cut(zcyl(sx * 22, sy, -5, 1, 1.7)).cut(zcyl(sx * 22, sy, -5, -1.8, 3.0))
        br = br.cut(rbox(sx * 12 - 7, sx * 12 + 7, 34, 58, -5, 1, 3.0, "|Z"))
    add("mount", br, "Mount", E(150, -45), mat="satin", color=(0.05, 0.05, 0.055), density=PA12CF, label="Drone bracket, PA12-CF, 4 x M3")
    for sx in (-1, 1):
        for sy in (28.0, 64.0):
            zscrew(f"mount_screw_{sx}_{sy}", sx * 22, sy, -1.8, 8.0, 1.5, "Mount", E(150, -65), "M3 x 8, bracket")
    pk = zcyl(0, 0, 0, 9.0, 21.0)
    try:
        pk = pk.faces(">Z").edges().fillet(3.0)
    except Exception:
        pass
    add("dls_puck", pk.translate((0.0, 45.0, H + 70.0)), "DLS puck", (0, 0, 0), finish="body", density=PA12CF, label="Light sensor + GNSS puck, on top of the drone")
    add("dls_dome", zcyl(0, 45.0, H + 78.8, H + 81.2, 13.0), "DLS puck", (0, 0, 0), mat="dome", color=(0.95, 0.95, 0.93), mass=3.0, label="Opal diffuser")
    export(os.path.join(REPO, "cameras", "ms", "mechanical", "out"), "aviac_ms")


# ================================================================== Aviac Duos: 50 x 30 x 28, 2 x Mira220 stereo, 26 mm baseline
def build_duos():
    Wd, H, D = 50.0, 30.0, 28.0
    FT, frame, recess, wall = 6.0, 1.6, 1.2, 1.5
    B = 26.0
    E = lambda y, z=0: (0, y, z)
    EXF = E(-95)
    D = 24.0                                                            # body -4 .. 24 = 28 mm; the hood adds 3.5
    fs, panel, rh, (px0, px1, pz0, pz1), inset = sculpted_body(Wd, H, -4.0, D, 6.0, FT, frame, recess, wall, 2.6, EXF, E(55), taper=1.0, r_rear=3.5, hd=3.5, b=0.8)
    L = [(-B / 2, 15.0), (B / 2, 15.0)]
    for (x, z) in L:
        panel = panel.cut(ycyl(x, z, -1, 5, 7.2))
    panel = light_bar(panel, (0.0, 26.0, 10.0, 0.9), recess, EXF)
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    light_pipe(0.0, 26.0, 10.0, recess + 1.0, 6.5, EXT, E(-82))
    add("gasket", W(cq.Solid.makeLoft([rr_wire(Wd - 1.0, H - 1.0, 5.5, FT - 0.2, H / 2), rr_wire(Wd - 1.0, H - 1.0, 5.5, FT + 0.2, H / 2)], True))
        .cut(W(cq.Solid.makeLoft([rr_wire(Wd - 2.2, H - 2.2, 4.9, FT - 1, H / 2), rr_wire(Wd - 2.2, H - 2.2, 4.9, FT + 1, H / 2)], True))),
        EXT, E(-75), mat="rubber", color=(0.85, 0.30, 0.08), mass=0.3, label="Silicone gasket")
    for i, (x, z) in enumerate(L):
        oring(f"cam{i}_oring", x, z, recess - 0.2, 8.6, 0.5, OPT, E(-88))
        lens_ring(f"cam{i}", x, z, -3.5, recess, 20.0, 15.6, OPT, E(-70))
        m12_lens(f"cam{i}", x, z, -6.0, 12.0, OPT, E(-60), (0.10, 0.22, 0.20), "Low-profile M12 lens, 12 mm long")
    fp = rbox(px0 + 0.5, px1 - 0.5, recess + wall, recess + wall + 1.0, pz0 + 0.5, pz1 - 0.5, 2.0).cut(ycyl(L[0][0], 15, 0, 5, 6.1)).cut(ycyl(L[1][0], 15, 0, 5, 6.1))
    add("front_plate", fp, OPT, E(-45), mat="satin", color=(0.55, 0.56, 0.58), density=ALU, label="Aluminium front plate: holds the 26 mm baseline")
    for i, (x, z) in enumerate(L):
        h = ycyl(x, z, 3.7, 6.0, 7.4).cut(ycyl(x, z, 3, 7, 6.05))
        add(f"cam{i}_holder", h, OPT, E(-35), mat="plastic_gloss", color=(0.04, 0.04, 0.045), mass=0.4, label="M12 lens mount")
    pcb("board", -23.2, 23.2, 2.0, 28.0, 7.0, 1.2, SEN, E(-15), "Shared sensor board: both Mira220 on one clock and one trigger", 3.0, comps="rear", seed=60,
        ics=[(L[0][0], 15, 6.6, 6.2, 0.9, -1, "Mira220, left", "sensor"), (L[1][0], 15, 6.6, 6.2, 0.9, -1, "Mira220, right", "sensor"),
             (0, 15, 2.5, 2, 0.8, 1, "Shared oscillator", "xtal"), (0, 6, 12, 2.5, 1.6, 1, "Board-to-board", "conn")])
    pcb("iface", -20, 20, 4.0, 26.0, 14.0, 1.2, PROC, E(10), "Interface board: MIPI to USB-C / GMSL", 2.5, comps="both", seed=70,
        ics=[(0, 15, 9, 9, 1.0, 1, "Bridge IC", "ic"), (0, 6, 12, 2.5, 1.6, -1, "Board-to-board", "conn"), (-12, 20, 3, 3, 0.8, 1, "Flash", "ic"),
             (12, 20, 3.2, 2.5, 0.8, 1, "Oscillator", "xtal"), (0, 15, 8.9, 3.2, D - 15.2 - 0.5, 1, "USB-C", "steel")])
    for sx in (-1, 1):
        standoff(f"so{sx}", sx * 20.5, 15.0, 8.2, 14.0, 0.9, SEN, E(-5), "Standoff")
    rh = rh.cut(box(-4.6, 4.6, D - 2, D + 1, 13.3, 16.7))
    for sx in (-1, 1):
        for zz in (6.0, 24.0):
            rh = rh.cut(ycyl(sx * 19.0, zz, D - 4, D + 1, 1.1))
    for k in range(3):
        for sx in (-1, 1):
            rh = rh.cut(rbox(sx * Wd / 2 - 3.0, sx * Wd / 2 + 3.0, 9.0, 19.0, 5.0 + k * 2.4, 6.3 + k * 2.4, 0.5, "|X"))
    try:
        rh = rh.cut(mark_on_side(9.0, 14.0, 19.5, Wd / 2 - inset(14.0), 0.4))
    except Exception as e:
        print("mark skipped", e)
    rh = rh.cut(zcyl(0, 18.0, -1, 4, 3.2))
    add("rear_housing", rh, EXT, E(55), finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    for sx in (-1, 1):
        for zz in (6.0, 24.0):
            screw(f"rear_screw_{sx}_{int(zz)}", sx * 19.0, zz, D + 0.6, 10.0, 0.8, EXT, E(68), "M1.6 x 10, rear", toward=-1)
    add("insert_14_20", zcyl(0, 18.0, 0.3, 6.0, 3.2).cut(zcyl(0, 18.0, 0, 7, 2.6)), EXT, E(55, -18), mat="gold", color=(0.8, 0.6, 0.2), mass=1.5, label='1/4"-20 insert')
    export(os.path.join(REPO, "cameras", "duos", "mechanical", "out"), "aviac_duos")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "ms"
    (build_ms if which == "ms" else build_duos)()
