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
def rugged_body(Wd, H, D, R, FT, frame, recess, wall, panel_r, ex_front, ex_rear, rails=True, bumpers=True, bump=1.0, cap=None):
    """Front shell (y 0..FT) with a recessed panel opening, separate panel plate, rear housing (FT..D or ..cap).
    Returns the panel rectangle and the panel back face y, so the caller can cut lens holes."""
    x0, x1, z0, z1 = -Wd / 2, Wd / 2, 0.0, H
    px0, px1, pz0, pz1 = x0 + frame, x1 - frame, z0 + frame, z1 - frame
    outer = rbox(x0, x1, 0, FT, z0, z1, R)
    fs = outer.cut(rbox(x0 + wall, x1 - wall, recess + wall, FT + 1, z0 + wall, z1 - wall, max(0.5, R - wall)))
    fs = fs.cut(rbox(px0, px1, -1, recess + wall + 0.01, pz0, pz1, panel_r))                      # panel opening
    g = 0.7
    fs = fs.cut(rbox(px0 - 1.4 - g, px1 + 1.4 + g, -1, 0.5, pz0 - 1.4 - g, pz1 + 1.4 + g, panel_r + 1.4 + g)
                .cut(rbox(px0 - 1.4, px1 + 1.4, -2, 1, pz0 - 1.4, pz1 + 1.4, panel_r + 1.4)))      # gasket line
    add("front_shell", fs, EXT, ex_front, finish="body", density=PA12CF, label="Front shell, PA12-CF, 1.5 mm walls")
    panel = rbox(px0, px1, recess, recess + wall, pz0, pz1, panel_r)
    rear_end = D if cap is None else cap
    rh = rbox(x0, x1, FT, rear_end, z0, z1, R).cut(rbox(x0 + wall, x1 - wall, FT - 1, rear_end - (wall if cap is None else -1), z0 + wall, z1 - wall, max(0.5, R - wall)))
    if bumpers:
        bl, br_ = [], []
        cz = min(14.0, H * 0.3)
        for sx in (-1, 1):
            for (za, zb) in ((z0 - bump, z0 + cz), (z1 - cz, z1 + bump)):
                xa, xb = (x0 - bump, x0 + cz) if sx < 0 else (x1 - cz, x1 + bump)
                for front, (ya, yb) in ((True, (-bump, min(cz, FT + 2))), (False, (rear_end - cz, rear_end + (bump if cap is None else 0)))):
                    (bl if front else br_).append(chamfered(xa, xb, ya, yb, za, zb, min(2.4, cz * 0.18)).cut(rbox(x0 + 0.2, x1 - 0.2, -5, rear_end + 5, z0 + 0.2, z1 - 0.2, R)
                                                                                          .intersect(box(x0 + 2.5, x1 - 2.5, -5, rear_end + 5, z0 + 2.5, z1 - 2.5))))
        for nm, lst, ex in (("bumpers_front", bl, ex_front), ("bumpers_rear", br_, ex_rear)):
            bs = lst[0]
            for b in lst[1:]:
                bs = bs.union(b)
            add(nm, bs, EXT, ex, finish="bumper", density=1.2, label="Corner bumpers, overmoulded TPU")
    if rails:
        rw = min(8.0, Wd * 0.12)
        rl = rbox(x0 + 3, x0 + 3 + rw, FT + 2, rear_end - 4, z1 - 0.01, z1 + 1.2 * bump, 0.8, "|Y").union(
             rbox(x1 - 3 - rw, x1 - 3, FT + 2, rear_end - 4, z1 - 0.01, z1 + 1.2 * bump, 0.8, "|Y"))
        rh = rh.union(rl)
    return fs, panel, rh, (px0, px1, pz0, pz1), rear_end


def lens_ring(name, x, z, y_front, y_panel, od, idia, group, ex):
    """The family lens ring: dark ring with a thin bright lip, sitting proud of the panel."""
    r = yring(x, z, y_front, y_panel, od / 2, idia / 2)
    try:
        r = r.faces("<Y").edges().chamfer(0.4)
    except Exception:
        pass
    add(name + "_ring", r, group, ex, mat="satin", color=(0.05, 0.05, 0.055), mass=0.0, label="Lens ring")
    add(name + "_lip", yring(x, z, y_front - 0.15, y_front + 0.25, od / 2 - 0.6, od / 2 - 1.3), group, ex, mat="steel", color=(0.8, 0.8, 0.82), mass=0.0, label="Ring lip")


def m12_lens(name, x, z, y_front, length, group, ex, tint, label):
    barrel = ycyl(x, z, y_front + 1.2, y_front + length, 7.0).union(ycyl(x, z, y_front, y_front + 6.0, 7.6))
    for k in range(18):
        a = 2 * math.pi * k / 18
        barrel = barrel.cut(ycyl(x + 7.75 * math.cos(a), z + 7.75 * math.sin(a), y_front + 1.0, y_front + 5.0, 0.45))
    barrel = barrel.cut(ycyl(x, z, y_front - 1, y_front + 1.2, 4.6))
    add(name + "_barrel", barrel, group, ex, mat="anodised", color=(0.02, 0.02, 0.025), mass=3.5, label=label)
    add(name + "_glass", ycyl(x, z, y_front + 0.6, y_front + 1.3, 4.6), group, ex, mat="lens", color=tint, mass=0.0, label="Front element, AR coated")


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
    "gunmetal": {"body": {"mat": "powder", "color": [0.042, 0.045, 0.044]}, "bumper": {"mat": "powder", "color": [0.028, 0.03, 0.03]},
                 "panel": {"mat": "powder", "color": [0.034, 0.036, 0.035]}},
    "sand": {"body": {"mat": "powder", "color": [0.56, 0.49, 0.38]}, "bumper": {"mat": "powder", "color": [0.47, 0.41, 0.31]},
             "panel": {"mat": "powder", "color": [0.52, 0.455, 0.35]}},
    "stealth": {"body": {"mat": "powder", "color": [0.022, 0.022, 0.024]}, "bumper": {"mat": "rubberised", "color": [0.012, 0.012, 0.013]},
                "panel": {"mat": "satin", "color": [0.11, 0.11, 0.115]}},
    "bronze": {"body": {"mat": "powder", "color": [0.115, 0.07, 0.05]}, "bumper": {"mat": "rubberised", "color": [0.015, 0.014, 0.014]},
               "panel": {"mat": "satin", "color": [0.62, 0.53, 0.36]}},
}


# ================================================================== Aviac MS: 96 x 90 x 90, 1 x IMX565 (C-mount) + 3 x Mira220 (M12)
def build_ms():
    Wd, H, D = 96.0, 90.0, 90.0
    FT, frame, recess, wall = 14.0, 6.0, 3.0, 1.5
    EXF, EXO, EXS, EXP, EXR = (0, -170, 0), (0, -112, 0), (0, -58, 0), (0, 0, 0), (0, 60, 0)
    fs, panel, rh, (px0, px1, pz0, pz1), _ = rugged_body(Wd, H, D, 9.0, FT, frame, recess, wall, 5.0, EXF, EXR, bump=1.2)
    MIRA = [(-29.0, 21.0, "NIR+ 890", (0.16, 0.02, 0.10)), (-29.0, 45.0, "NIR 840", (0.33, 0.03, 0.12)), (-29.0, 69.0, "RE 723", (0.62, 0.05, 0.08))]
    IMX = (11.0, 45.0)
    BAR = (32.0, 77.5, 16.0, 1.4)                                # light bar: centre x, z, length, height
    for (x, z, *_r) in MIRA:
        panel = panel.cut(ycyl(x, z, -1, 10, 7.7))
    panel = panel.cut(ycyl(IMX[0], IMX[1], -1, 10, 17.2))
    panel, = light_bar(panel, BAR, recess, EXF),
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    screws = None
    for sx in (-1, 1):
        for zz in (7.0, H - 7.0):
            s = ycyl(sx * (Wd / 2 - 6.6), zz, -1.6, 0.2, 1.9).cut(cq.Workplane("XZ").polygon(6, 1.9).extrude(-1.0).translate((sx * (Wd / 2 - 6.6), -1.6, zz)))
            screws = s if screws is None else screws.union(s)
    add("front_screws", screws, EXT, EXF, mat="steel", color=(0.55, 0.56, 0.58), mass=1.2, label="4 x M3 stainless")

    # ---- optics: aluminium lens/filter plate, 3 x M12 lenses with band-pass filters, 1 x C-mount lens
    LP0, LP1 = recess + wall, recess + wall + 2.0
    lp = rbox(px0 + 1, px1 - 1, LP0, LP1, pz0 + 1, pz1 - 1, 4.0)
    for (x, z, *_r) in MIRA:
        lp = lp.cut(ycyl(x, z, LP0 - 1, LP1 + 1, 6.2))
    lp = lp.cut(ycyl(IMX[0], IMX[1], LP0 - 1, LP1 + 1, 16.2)).union(yring(IMX[0], IMX[1], LP1 - 0.01, LP1 + 4.0, 18.5, 16.2))   # 2 mm plate, C-mount boss
    add("lens_plate", lp, OPT, EXO, mat="satin", color=(0.55, 0.56, 0.58), density=ALU, label="Lens and filter plate, machined aluminium")
    for i, (x, z, band, tint) in enumerate(MIRA):
        lens_ring(f"mira{i}", x, z, -10.0, recess, 20.0, 15.6, OPT, EXO)
        m12_lens(f"mira{i}", x, z, -9.0, 25.0, OPT, EXO, tint, "M12 lens, 6 mm, 25 mm long")
        add(f"mira{i}_filter", ycyl(x, z, -9.6, -9.1, 6.6), OPT, EXO, mat="bandpass", color=tint, mass=0.4, label=f"Band-pass filter, {band}")
    # C-mount: compact 16 mm, 30 mm long, 12 mm proud; collar ring, focus and iris knurls
    cx, cz = IMX
    lens_ring("imx", cx, cz, -12.0, recess, 44.0, 34.0, OPT, EXO)
    cb = ycyl(cx, cz, -12.0, 18.0, 15.5).cut(ycyl(cx, cz, -13, -9.5, 11.5))
    for (ya, yb) in ((-8.0, -3.0), (0.0, 4.5)):
        for k in range(36):
            a = 2 * math.pi * k / 36
            cb = cb.cut(ycyl(cx + 15.6 * math.cos(a), cz + 15.6 * math.sin(a), ya, yb, 0.55))
    add("imx_barrel", cb, OPT, EXO, mat="anodised", color=(0.02, 0.02, 0.025), mass=45.0, label="C-mount lens, 16 mm, 1.1-inch, compact (lightweight build)")
    add("imx_glass", ycyl(cx, cz, -10.4, -9.6, 11.4), OPT, EXO, mat="lens", color=(0.20, 0.10, 0.32), mass=0.0, label="Front element, AR coated")
    add("imx_retainer", yring(cx, cz, -11.0, -10.3, 12.4, 11.4), OPT, EXO, mat="gold", color=(0.8, 0.6, 0.2), mass=0.0, label="Retaining ring")

    # ---- baseboard + image sensors
    MZ0 = 18.0
    for i, (x, z, *_r) in enumerate(MIRA):
        b = box(x - 11, x + 11, MZ0, MZ0 + 1.6, z - 11, z + 11)
        add(f"mira{i}_pcb", b, SEN, EXS, mat="pcb", color=(0.02, 0.20, 0.10), mass=2.0, label="Mira220 sensor board")
        add(f"mira{i}_sensor", box(x - 3.3, x + 3.3, MZ0 - 0.9, MZ0, z - 3.1, z + 3.1), SEN, EXS, mat="ceramic_dark", color=(0.06, 0.06, 0.07), mass=0.0, label="ams OSRAM Mira220, 1600 x 1400 global shutter")
        add(f"mira{i}_fpc", box(x + 4, x + 10, MZ0 + 1.6, 40.0, z - 4, z + 4), SEN, EXS, mat="fpc", color=(0.8, 0.42, 0.05), mass=0.3, label="FPC to the baseboard")
    IB0 = 34.0
    add("imx_pcb", box(cx - 29.5, cx + 29.5, IB0, IB0 + 1.6, cz - 31.5, cz + 31.5), SEN, EXS, mat="pcb", color=(0.02, 0.03, 0.025), mass=9.0, label="IMX565 sensor board, 59 x 63 mm")
    add("imx_sensor", box(cx - 10, cx + 10, IB0 - 1.7, IB0, cz - 8.4, cz + 8.4), SEN, EXS, mat="ceramic_dark", color=(0.07, 0.07, 0.08), mass=0.0, label="Sony IMX565, 12.4 MP global shutter")
    add("imx_b2b", box(cx - 12, cx + 12, IB0 + 1.6, 40.0, cz + 20, cz + 26), SEN, EXS, mat="plastic_gloss", color=(0.80, 0.77, 0.68), mass=0.5, label="Board-to-board connector")
    add("baseboard", box(-44, 44, 40.0, 41.6, 4.0, 86.0), SEN, EXS, mat="pcb", color=(0.02, 0.20, 0.10), mass=11.0, label="Sensor baseboard: sync, power, 4 x 2-lane MIPI")

    # ---- processing: Jetson carrier 87 x 52 and module, thermal block to the rear cap
    add("carrier", box(-43.5, 43.5, 46.0, 47.6, 19.0, 71.0), PROC, EXP, mat="pcb", color=(0.02, 0.20, 0.10), mass=16.0, label="Jetson carrier, 87 x 52 mm")
    add("sodimm", box(-36, 36, 47.6, 51.0, 22.0, 30.0), PROC, EXP, mat="plastic_gloss", color=(0.08, 0.08, 0.09), mass=3.0, label="260-pin SO-DIMM socket")
    add("jetson", box(-34.8, 34.8, 51.0, 52.2, 24.0, 69.0), PROC, EXP, mat="pcb", color=(0.02, 0.10, 0.06), mass=28.0, label="Jetson Orin NX / Nano module (bare; the case is the heatsink)")
    add("jetson_soc", box(-12, 12, 52.2, 54.6, 40.0, 64.0), PROC, EXP, mat="alu", color=(0.6, 0.6, 0.62), mass=0.0, label="Orin SoC")
    add("spreader", box(-12, 12, 54.6, 56.6, 35.0, 64.0), PROC, EXP, mat="alu", color=(0.6, 0.6, 0.62), density=ALU, label="Heat spreader on the SoC")
    add("heat_pipe", ycyl(-4, 38.5, 54.6, D - 7.5, 3.0).union(ycyl(4, 38.5, 54.6, D - 7.5, 3.0)), PROC, EXP, mat="gold", color=(0.75, 0.42, 0.25),
        mass=9.0, label="2 x 6 mm heat pipes to the rear heatsink")

    # ---- externals: rear housing, fan, finned aluminium cap with ports, DLS, mount
    rh = rh.cut(box(Wd / 2 - 2, Wd / 2 + 2, 30, 60, 10, 22))                                   # vent slots under the mark
    for k in range(3):
        rh = rh.cut(rbox(Wd / 2 - 2.5, Wd / 2 + 2, 32.0, 58.0, 12.0 + k * 3.8, 14.0 + k * 3.8, 0.9, "|X"))
    try:
        rh = rh.cut(mark_on_side(22.0, 45.0, 56.0, Wd / 2, 0.6))
    except Exception as e:
        print("mark skipped", e)
    rh = rh.cut(zcyl(0, 50.0, H - 3, H + 2, 13.0))                                                # DLS opening
    # rear: a 1.5 mm finned aluminium insert sits in a window of the PA12 rear wall; ports go through the wall below
    HX0, HX1, HZ0, HZ1 = -30.0, 30.0, 30.0, 84.0
    rh = rh.cut(rbox(HX0, HX1, D - 3, D + 1, HZ0, HZ1, 4.0))
    hs = rbox(HX0 - 2, HX1 + 2, D - 8.0, D - 6.5, HZ0 - 2, HZ1 + 2, 5.0)
    for k in range(14):
        x = HX0 + 2.0 + k * 4.0
        hs = hs.union(box(x - 0.5, x + 0.5, D - 6.51, D - 0.3, HZ0 + 1.5, HZ1 - 1.5))
    add("heatsink", hs, EXT, (0, 95, 0), mat="satin", color=(0.48, 0.49, 0.5), density=ALU, label="Finned aluminium heatsink insert, 1.5 mm base")
    for (x, w, h, zc, kind) in ((-30, 16.0, 8.0, 15.0, "xt30"), (-8, 12.0, 9.5, 15.0, "eth"), (9, 9.0, 3.4, 15.0, "usb"), (28, 0, 0, 15.0, "gps")):
        rh = rh.cut(ycyl(x, zc, D - 3, D + 1, 4.2) if kind == "gps" else box(x - w / 2, x + w / 2, D - 3, D + 1, zc - h / 2, zc + h / 2))
    for k in range(5):                                            # fan exhaust slots beside the heatsink
        for sx in (-1, 1):
            rh = rh.cut(rbox(sx * 38 - 3, sx * 38 + 3, D - 3, D + 1, 40 + k * 7, 43 + k * 7, 1.2))
    add("rear_housing", rh, EXT, EXR, finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    add("fan", box(-15, 15, 72.0, 79.0, 42.0, 72.0).cut(ycyl(0, 57.0, 71, 80, 13.0)).union(ycyl(0, 57.0, 72.5, 78.5, 5.0)), EXT, EXR,
        mat="plastic_gloss", color=(0.05, 0.05, 0.055), mass=6.0, label="30 mm fan")
    add("xt30", box(-37, -23, D - 4.5, D - 0.6, 11.5, 18.5), EXT, EXR, mat="plastic_gloss", color=(0.93, 0.74, 0.08), mass=2.0, label="Power in, XT30, 3S-6S")
    add("eth", box(-13.5, -2.5, D - 4.5, D - 0.8, 10.8, 19.2), EXT, EXR, mat="steel", color=(0.7, 0.7, 0.72), mass=1.0, label="Ethernet")
    add("usb", box(5, 13, D - 4.2, D - 0.8, 13.5, 16.5), EXT, EXR, mat="steel", color=(0.7, 0.7, 0.72), mass=0.5, label="USB-C")
    add("gps", yring(28, 15.0, D - 4.6, D + 0.6, 4.1, 2.6), EXT, EXR, mat="gold", color=(0.8, 0.6, 0.2), mass=1.0, label="GPS / PPS connector")
    add("dls_ring", zcyl(0, 50.0, H - 0.6, H + 1.4, 14.0).cut(zcyl(0, 50.0, H - 1, H + 2, 11.0)), EXT, (0, 60, 40), mat="satin", color=(0.05, 0.05, 0.055), mass=1.0, label="DLS ring")
    dome = zcyl(0, 50.0, H - 1.0, H + 1.6, 11.0)
    try:
        dome = dome.faces(">Z").edges().fillet(2.0)
    except Exception:
        pass
    add("dls_dome", dome, EXT, (0, 60, 40), mat="dome", color=(0.95, 0.95, 0.93), mass=3.0, label="Downwelling light sensor, opal diffuser")
    br = rbox(-30, 30, 22.0, 70.0, -3.2, -0.2, 3.0, "|Z")
    for sx in (-1, 1):
        for sy in (28.0, 64.0):
            br = br.cut(zcyl(sx * 22, sy, -5, 1, 1.7)).cut(zcyl(sx * 22, sy, -5, -1.8, 3.0))
        br = br.cut(rbox(sx * 12 - 7, sx * 12 + 7, 34, 58, -5, 1, 3.0, "|Z"))         # lightening pockets
    add("mount", br, "Mount", (0, 60, -40), mat="satin", color=(0.05, 0.05, 0.055), density=PA12CF, label="Drone bracket, PA12-CF, 4 x M3")
    export(os.path.join(REPO, "cameras", "ms", "mechanical", "out"), "aviac_ms")


# ================================================================== Aviac Duos: 50 x 30 x 28, 2 x Mira220 stereo, 26 mm baseline
def build_duos():
    Wd, H, D = 50.0, 30.0, 28.0
    FT, frame, recess, wall = 6.0, 1.6, 1.2, 1.5
    B = 26.0
    EXF, EXO, EXS, EXP, EXR = (0, -62, 0), (0, -38, 0), (0, -16, 0), (0, 0, 0), (0, 22, 0)
    fs, panel, rh, (px0, px1, pz0, pz1), _ = rugged_body(Wd, H, D, 3.0, FT, frame, recess, wall, 2.2, EXF, EXR, bump=0.7)
    L = [(-B / 2, 15.0), (B / 2, 15.0)]
    for (x, z) in L:
        panel = panel.cut(ycyl(x, z, -1, 5, 7.2))
    panel = light_bar(panel, (0.0, 26.0, 10.0, 0.9), recess, EXF)
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    add("front_plate", rbox(px0 + 0.5, px1 - 0.5, recess + wall, recess + wall + 1.0, pz0 + 0.5, pz1 - 0.5, 2.0).cut(ycyl(L[0][0], 15, 0, 5, 6.1)).cut(ycyl(L[1][0], 15, 0, 5, 6.1)),
        OPT, EXO, mat="satin", color=(0.55, 0.56, 0.58), density=ALU, label="Aluminium front plate: holds the 26 mm baseline")
    for i, (x, z) in enumerate(L):
        lens_ring(f"cam{i}", x, z, -3.5, recess, 20.0, 15.6, OPT, EXO)
        m12_lens(f"cam{i}", x, z, -6.0, 12.0, OPT, EXO, (0.12, 0.30, 0.28), "Low-profile M12 lens, 12 mm long")
    add("board", box(-23.2, 23.2, 7.0, 8.6, 2.0, 28.0), SEN, EXS, mat="pcb", color=(0.02, 0.20, 0.10), mass=4.0, label="Shared sensor board, both Mira220 on one clock")
    for i, (x, z) in enumerate(L):
        add(f"cam{i}_sensor", box(x - 3.3, x + 3.3, 6.1, 7.0, z - 3.1, z + 3.1), SEN, EXS, mat="ceramic_dark", color=(0.06, 0.06, 0.07), mass=0.0, label="ams OSRAM Mira220, 1600 x 1400 global shutter")
    add("iface", box(-20, 20, 14.0, 15.6, 4.0, 26.0), PROC, EXP, mat="pcb", color=(0.02, 0.10, 0.06), mass=3.0, label="Interface board: MIPI to USB-C / GMSL")
    add("iface_chip", box(-6, 6, 15.6, 16.8, 9.0, 21.0), PROC, EXP, mat="ic", color=(0.03, 0.03, 0.03), mass=0.0, label="Bridge IC")
    add("usbc", box(-4.5, 4.5, 16.8, D - 0.5, 13.4, 16.6), PROC, EXP, mat="steel", color=(0.7, 0.7, 0.72), mass=0.6, label="USB-C")
    rh = rh.cut(box(-4.6, 4.6, D - 2, D + 1, 13.3, 16.7))
    for sx in (-1, 1):
        for zz in (6.0, 24.0):
            rh = rh.cut(ycyl(sx * 19.0, zz, D - 4, D + 1, 1.1))
    for k in range(3):
        rh = rh.cut(rbox(Wd / 2 - 2.0, Wd / 2 + 1, 10.0, 22.0, 5.0 + k * 2.4, 6.3 + k * 2.4, 0.5, "|X"))
    try:
        rh = rh.cut(mark_on_side(9.0, 16.0, 19.5, Wd / 2, 0.4))
    except Exception as e:
        print("mark skipped", e)
    rh = rh.cut(zcyl(0, 18.0, -1, 4, 3.2))
    add("rear_housing", rh, EXT, EXR, finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    add("insert_14_20", zcyl(0, 18.0, 0.3, 6.0, 3.2).cut(zcyl(0, 18.0, 0, 7, 2.6)), EXT, EXR, mat="gold", color=(0.8, 0.6, 0.2), mass=1.5, label='1/4"-20 insert')
    export(os.path.join(REPO, "cameras", "duos", "mechanical", "out"), "aviac_duos")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "ms"
    (build_ms if which == "ms" else build_duos)()
