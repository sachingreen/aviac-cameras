#!/usr/bin/env python3
"""Aviac TH (thermal) and Aviac SW (SWIR): demo inspection heads in the same family as Duos (CadQuery).

TH  - a 640 x 512 uncooled LWIR core behind a germanium lens, with a Mira220 colour camera beside it, on the gimbal
      yoke. For solar and electrical inspection.
SW  - an InGaAs SWIR sensor (about 0.9-1.7 um) behind a SWIR-coated lens, on the gimbal yoke. For moisture, leaks
      and seeing through haze in industrial inspection.
Concept hardware: parts and figures are design placeholders until a core and sensor are chosen.

  python3 toolkit/cad/inspection_cameras.py th   -> cameras/th/mechanical/out/
  python3 toolkit/cad/inspection_cameras.py sw   -> cameras/sw/mechanical/out/
"""
import os, sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rugged_cameras as rc
from rugged_cameras import (add, box, rbox, ycyl, yring, zcyl, W, V, OPT, SEN, PROC, EXT, PA12CF, ALU, REPO, sculpted_body, lens_ring, dome,
                            m12_lens, m12_holder, light_bar, light_pipe, oring, pcb, standoff, screw, image_sensor, gimbal_yoke, mark_on_side, rr_wire)

E = lambda y, z=0: (0, y, z)
EXF = E(-95)


def big_lens(name, x, z, y_front, y_back, r, tint, label, glass_label, glass_mat="lens"):
    """A large barrel lens: anodised barrel with grip flutes, a stepped bezel, a broad front element."""
    barrel = ycyl(x, z, y_front + 1.5, y_back, r).union(ycyl(x, z, y_front, y_front + 6.0, r + 0.8))
    import math
    for k in range(36):
        a = 2 * math.pi * k / 36
        barrel = barrel.cut(ycyl(x + (r + 0.95) * math.cos(a), z + (r + 0.95) * math.sin(a), y_front + 1.6, y_front + 5.4, 0.5))
    barrel = barrel.cut(ycyl(x, z, y_front - 1, y_front + 2.6, r - 1.6)).cut(ycyl(x, z, y_front - 1, y_back - 1.0, r - 1.75))
    add(name + "_barrel", barrel, OPT, E(-60), mat="anodised", color=(0.015, 0.015, 0.018), density=ALU * 0.55, label=label)
    rc.lens_stack(name, x, z, y_front + 2.2, r - 1.7, OPT, E(-60), tint, depth=(r - 1.7) * 1.2)
    if glass_mat != "lens":                                # germanium: opaque to the eye, dark grey with a DLC sheen
        for p_ in rc.parts:
            if p_["name"] == name + "_glass":
                p_["mat"], p_["label"] = glass_mat, glass_label


def body(Wd, H, D, lenses, word, bar_z, glass_holes=(), vents=False):
    FT, frame, recess, wall = 6.0, 1.6, 1.2, 1.5
    fs, panel, rh, (px0, px1, pz0, pz1), inset = sculpted_body(Wd, H, -4.0, D, 9.5, FT, frame, recess, wall, 3.0, EXF, E(55), taper=0.0, r_rear=8.0, hd=4.6, b=1.9)
    for (x, z, rr) in lenses:
        panel = panel.cut(ycyl(x, z, -1, 5, rr))
    panel = light_bar(panel, (0.0, bar_z, 10.0, 0.9), recess, EXF)
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    light_pipe(0.0, bar_z, 10.0, recess + 1.0, 6.5, EXT, E(-82))
    rc.front_glass(px0 + 0.3, px1 - 0.3, pz0 + 0.3, pz1 - 0.3, -7.3, 3.0, glass_holes, (0.0, bar_z, 10.0, 0.9))
    add("glass_name", rc.etch_text(word, 1.8, 0.0, 4.6, -7.3), EXT, (0, -240, 0), mat="etch", color=(0.7, 0.71, 0.73), mass=0.0, label="Name, etched on the glass")
    add("gasket", W(cq.Solid.makeLoft([rr_wire(Wd - 1.0, H - 1.0, 6.5, FT - 0.2, H / 2), rr_wire(Wd - 1.0, H - 1.0, 6.5, FT + 0.2, H / 2)], True))
        .cut(W(cq.Solid.makeLoft([rr_wire(Wd - 2.2, H - 2.2, 5.9, FT - 1, H / 2), rr_wire(Wd - 2.2, H - 2.2, 5.9, FT + 1, H / 2)], True))),
        EXT, E(-75), mat="rubber", color=(0.85, 0.30, 0.08), mass=0.4, label="Silicone gasket")
    fp = rbox(px0 + 0.5, px1 - 0.5, recess + wall, recess + wall + 1.2, pz0 + 0.5, pz1 - 0.5, 2.5)
    for (x, z, rr) in lenses:
        fp = fp.cut(ycyl(x, z, 0, 5, rr - 1.0))
    add("front_plate", fp, OPT, E(-45), mat="satin", color=(0.55, 0.56, 0.58), density=ALU, label="Aluminium front plate")
    # rear housing: screw holes, side vents, the wing mark and the model name on the right side
    for sx in (-1, 1):
        for zz in (6.0, H - 6.0):
            rh = rh.cut(ycyl(sx * (Wd / 2 - 6.0), zz, D - 4, D + 1, 1.1))
    for k in range(4):
        for sx in (-1, 1):
            rh = rh.cut(rbox(sx * Wd / 2 - 3.0, sx * Wd / 2 + 3.0, 12.0, 26.0, 7.0 + k * 3.0, 8.6 + k * 3.0, 0.6, "|X"))
    rh = rh.cut(box(-5.0, 5.0, D - 2, D + 1, H / 2 - 2.0, H / 2 + 2.0))
    if vents:                                       # slotted vents across the top, two groups
        for gx in (-Wd / 4, Wd / 4):
            for k in range(8):
                y = 12.0 + k * 2.0
                rh = rh.cut(rbox(gx - 7.0, gx + 7.0, y, y + 0.9, H - 3.0, H + 1.0, 0.44, "|Z"))
    add("rear_housing", rh, EXT, E(55), finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    sol = None
    for poly in rc.logo_polygons():                 # Aviac mark and name printed on the right side
        pts = [(19.0 + px * 10.0, H - 13.0 + (py - 0.5) * 10.0) for (px, py) in poly]
        w = cq.Workplane("YZ").polyline(pts).close().extrude(0.25)
        sol = w if sol is None else sol.union(w)
    t = cq.Workplane("YZ").text(word, 3.0, 0.25, kind="bold", halign="center", valign="center")
    bb = t.val().BoundingBox()
    sol = sol.union(t.translate((0, 19.0 - (bb.ymin + bb.ymax) / 2, H - 23.0 - (bb.zmin + bb.zmax) / 2)))
    add("side_mark", sol.translate((Wd / 2 - 0.1, 0, 0)), EXT, E(55), mat="etch", color=(0.75, 0.76, 0.78), mass=0.0, label="Aviac mark, printed")
    for sx in (-1, 1):
        for zz in (6.0, H - 6.0):
            screw(f"rear_screw_{sx}_{int(zz)}", sx * (Wd / 2 - 6.0), zz, D + 0.6, 10.0, 0.9, EXT, E(68), "M2 x 10, rear", toward=-1)
    for sx in (-1, 1):
        standoff(f"so{sx}", sx * (Wd / 2 - 5.0), H / 2, 10.0, D - 9.0, 1.0, SEN, E(-5), "Standoff")
    return D


def thermal_lens(name, x, z, y_glass, r):
    """A thermal lens the way they look: short and stout, a deep knurled grip ring, a black front lip with the
    germanium element set in it (dark, with the magenta-green glint of its AR coating), engraved Aviac."""
    import math
    G, ex = OPT, E(-70)
    add(name + "_mount", ycyl(x, z, y_glass - 1.5, y_glass + 9.0, r - 0.3), G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Lens mount")
    add(name + "_band", yring(x, z, y_glass - 2.6, y_glass - 1.5, r + 0.2, r - 0.6), G, ex, mat="satin", color=(0.06, 0.07, 0.09), mass=0.0, label="Mount ring")
    k_ = ycyl(x, z, y_glass - 11.0, y_glass - 2.6, r + 1.0)
    for k in range(72):
        a = 2 * math.pi * k / 72
        k_ = k_.cut(ycyl(x + (r + 1.1) * math.cos(a), z + (r + 1.1) * math.sin(a), y_glass - 10.4, y_glass - 3.2, 0.32))
    add(name + "_grip", k_, G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Knurled grip ring")
    lip = ycyl(x, z, y_glass - 13.2, y_glass - 11.0, r + 0.6).cut(ycyl(x, z, y_glass - 14, y_glass - 10, r - 2.2))
    add(name + "_lip", lip, G, ex, mat="anodised", color=(0.01, 0.01, 0.012), density=ALU, label="Front lip")
    add(name + "_engrave", ring_text(["AVIAC", "13mm f/1.0", "8-14um"], x, z, r + 0.6, y_glass - 12.1, 0.9, 110, 250), G, ex, mat="etch",
        color=(0.8, 0.8, 0.82), mass=0.0, label="Engraving")
    add(name + "_glass", dome(x, z, y_glass - 13.4, r - 2.2, 4.2), G, ex, mat="germanium", color=(0.2, 0.17, 0.24), mass=0.0, label="Germanium element, AR-coated")
    add(name + "_inner", yring(x, z, y_glass - 11.5, y_glass - 9.0, r - 2.2, r - 4.0), G, ex, mat="black", color=(0, 0, 0), mass=0.0, label="Lens interior")


def fitted_mark(cy, cz, h_max, w_max):
    """The Aviac mark as YZ polygons scaled to fit h_max x w_max, centred on (cy, cz). Returns point lists."""
    polys = rc.logo_polygons()
    xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
    w0, h0 = max(xs) - min(xs), max(ys) - min(ys)
    k = min(h_max / h0, w_max / w0)
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return [[(cy + (px - mx) * k, cz + (py - my) * k) for (px, py) in poly] for poly in polys]


def build_th():
    """TH: a dual-module thermal head. Left, the thermal module: a 1 MP (1280 x 1024, 12 um) uncooled core behind a
    short germanium lens. Right, the NIR module: a Mira220 global-shutter sensor behind one M12 lens and one
    400-940 nm filter, so a single channel covers visible through near infrared. Field-sage front housing, black
    finned aluminium rear block that sheds the core's heat."""
    import math
    rc.parts.clear()
    Wd, H, F0, F1, R1 = 66.0, 44.0, 0.0, 30.0, 52.0    # front housing y 0..30, finned rear y 30..52
    zc = H / 2
    TX, NX = -13.0, 18.0                                 # thermal and NIR lens centres
    # ---- externals
    fh = rbox(-Wd / 2, Wd / 2, F0, F1, 0, H, 6.0, "|Y")
    try:
        fh = fh.faces("<Y").edges().chamfer(1.6)
    except Exception:
        pass
    fh = fh.cut(rbox(-Wd / 2 + 2, Wd / 2 - 2, F0 + 2, F1 + 1, 2, H - 2, 4.5, "|Y")).cut(ycyl(TX, zc, -1, 3, 12.0)).cut(ycyl(NX, zc, -1, 3, 8.6))
    add("front_housing", fh, EXT, E(-60), finish="body", density=1.15, label="Front housing, PA12-CF, field sage")
    face = rbox(-Wd / 2 + 3.4, Wd / 2 - 3.4, -0.6, 0.4, 3.4, H - 3.4, 4.0, "|Y").cut(ycyl(TX, zc, -2, 2, 12.0)).cut(ycyl(NX, zc, -2, 2, 8.6))
    add("face", face, EXT, E(-60), mat="powder", color=(0.035, 0.038, 0.036), density=ALU, label="Front face plate")
    add("accent_ring", yring(TX, zc, -1.2, -0.4, 12.8, 11.2), EXT, E(-60), mat="satin", color=(0.04, 0.42, 0.20), mass=0.0, label="Accent ring, thermal")
    add("accent_ring_nir", yring(NX, zc, -1.2, -0.4, 9.4, 8.4), EXT, E(-60), mat="satin", color=(0.04, 0.42, 0.20), mass=0.0, label="Accent ring, NIR")
    add("face_text", rc.etch_text("LWIR", 1.6, TX, H - 6.2, -0.6).union(rc.etch_text("400-940 nm", 1.6, NX, H - 6.2, -0.6)), EXT, E(-60), mat="etch",
        color=(0.85, 0.85, 0.86), mass=0.0, label="Band labels, printed")
    add("light_dot", ycyl(NX, 6.5, -0.9, -0.3, 0.9), EXT, E(-60), mat="led", color=(1.0, 0.55, 0.12), mass=0.0, label="Status light")
    rb = rbox(-Wd / 2 + 1.0, Wd / 2 - 1.0, F1, R1, 1.0, H - 1.0, 5.0, "|Y")
    for k in range(10):                                 # fins: grooves round the rear block
        y = F1 + 2.0 + k * 2.0
        rb = rb.cut(box(-Wd, Wd, y, y + 0.9, H - 4.0, H + 1)).cut(box(-Wd, Wd, y, y + 0.9, -1, 4.0))
        rb = rb.cut(box(Wd / 2 - 4.0, Wd, y, y + 0.9, -1, H + 1)).cut(box(-Wd, -Wd / 2 + 4.0, y, y + 0.9, -1, H + 1))
    rb = rb.cut(ycyl(0, 12.0, R1 - 2, R1 + 1, 4.5)).cut(rbox(-Wd / 2 + 5.5, Wd / 2 - 5.5, F1 - 1, R1 - 2.5, 5.5, H - 5.5, 2.0, "|Y"))
    add("rear_block", rb, EXT, E(55), mat="powder", color=(0.012, 0.012, 0.014), density=ALU, label="Finned rear block, aluminium, black anodised")
    add("rear_conn", ycyl(0, 12.0, R1 - 0.5, R1 + 3.0, 4.4).cut(ycyl(0, 12.0, R1, R1 + 4, 3.2)), EXT, E(70), mat="steel", color=(0.6, 0.6, 0.62), mass=2.0, label="M12 connector: power and Ethernet")
    for sx in (-1, 1):
        for sz in (-1, 1):
            add(f"rear_screw_{sx}_{sz}", ycyl(sx * (Wd / 2 - 6), zc + sz * 15.0, R1 - 0.2, R1 + 0.6, 1.1), EXT, E(70), mat="steel", color=(0.12, 0.12, 0.13), mass=0.1, label="M2 screw")
    for sx in (1, -1):                                  # Aviac mark on both sides, model name on the right
        sol = None
        for pts in fitted_mark(15.0, zc + 2.0, 14.0, 16.0):
            if sx < 0:
                pts = [(30.0 - y, z) for (y, z) in pts]
            w = cq.Workplane("YZ").polyline(pts).close().extrude(0.25 * sx)
            sol = w if sol is None else sol.union(w)
        if sx > 0:
            t = cq.Workplane("YZ").text("TH", 2.6, 0.25, kind="bold", halign="center", valign="center")
            bb = t.val().BoundingBox()
            sol = sol.union(t.translate((0, 15.0 - (bb.ymin + bb.ymax) / 2, zc - 9.5 - (bb.zmin + bb.zmax) / 2)))
        add("side_mark" if sx > 0 else "side_mark_l", sol.translate((sx * (Wd / 2 - 0.1), 0, 0)), EXT, E(-60), mat="etch", color=(0.86, 0.87, 0.88), mass=0.0, label="Aviac mark, printed")
    add("tripod", zcyl(0, 24.0, -0.4, 4.0, 3.2).cut(zcyl(0, 24.0, -1, 5, 2.6)), EXT, E(55, -20), mat="gold", color=(0.8, 0.6, 0.2), mass=1.0, label='1/4"-20 insert')
    # ---- optics: thermal lens (germanium) and the NIR lens with its 400-940 nm filter
    lb = ycyl(TX, zc, -21.0, 4.0, 10.0)
    for k in range(56):
        a = 2 * math.pi * k / 56
        lb = lb.cut(ycyl(TX + 10.1 * math.cos(a), zc + 10.1 * math.sin(a), -13.0, -5.0, 0.32))
    lb = lb.cut(ycyl(TX, zc, -22, -18.5, 7.9))
    add("lens_barrel", lb, OPT, E(-110), mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Thermal lens barrel, 19 mm f/1.0, focus locked")
    add("lens_lip", yring(TX, zc, -21.6, -20.4, 10.1, 8.0), OPT, E(-110), mat="anodised", color=(0.008, 0.008, 0.01), mass=0.0, label="Front lip")
    add("lwir_glass", dome(TX, zc, -21.8, 7.95, 3.0), OPT, E(-110), mat="germanium", color=(0.2, 0.17, 0.24), mass=0.0, label="Germanium element, AR-coated")
    add("lwir_inner", yring(TX, zc, -19.0, -15.5, 8.0, 6.2), OPT, E(-110), mat="black", color=(0, 0, 0), mass=0.0, label="Lens interior")
    add("lens_engrave", ring_text(["AVIAC"], TX, zc, 10.0, -16.0, 1.3, 90, 90), OPT, E(-110), mat="etch", color=(0.85, 0.85, 0.86), mass=0.0, label="Engraved: Aviac")
    m12_lens("nir", NX, zc, -10.0, 16.0, OPT, E(-110), (0.10, 0.22, 0.20), "M12 lens, 6 mm f/2.0, NIR-corrected", filt=("400-940 nm", (0.28, 0.10, 0.16)))
    m12_holder("nir_holder", NX, zc, 6.0, 14.0, OPT, E(-90))
    for p_ in rc.parts:                                   # the 400-940 nm filter is an interference coating on clear glass
        if p_["name"] == "nir_filter":
            p_["mat"], p_["label"] = "dichroic", "Band-pass filter, 400-940 nm, interference-coated"
    add("nir_retainer", yring(NX, zc, -10.85, -10.45, 7.25, 6.6), OPT, E(-110), mat="steel", color=(0.82, 0.83, 0.85), mass=0.0, label="Filter retaining ring, polished")
    # ---- the two sensing modules
    cm = rbox(TX - 14.5, TX + 14.5, 4.0, 27.0, zc - 14.5, zc + 14.5, 1.2, "|Y").union(ycyl(TX, zc, 1.0, 4.0, 11.4))
    for sx in (-1, 1):
        for sz in (-1, 1):
            cm = cm.cut(ycyl(TX + sx * 11.8, zc + sz * 11.8, 3.0, 5.0, 0.9))
    add("core", cm, SEN, E(-35), mat="powder", color=(0.02, 0.02, 0.022), density=ALU * 0.9, label="Thermal core module: 1280 x 1024 (1 MP) uncooled VOx, 12 um (placeholder)")
    add("core_window", ycyl(TX, zc, 0.6, 1.1, 7.6), SEN, E(-35), mat="germanium", color=(0.2, 0.17, 0.24), mass=0.0, label="Detector window")
    add("core_label", rc.etch_text("1MP", 1.6, TX + 9.0, zc + 11.0, 3.95), SEN, E(-35), mat="etch", color=(0.8, 0.8, 0.82), mass=0.0, label="Core label")
    pcb("core_board", TX - 14.5, TX + 14.5, zc - 14.5, zc + 14.5, 27.2, 1.2, SEN, E(-15), "Core readout board", 2.0, comps="rear", seed=81,
        ics=[(TX, zc, 8, 8, 1.0, 1, "Readout FPGA", "ic"), (TX - 9, zc + 9, 4, 3, 0.8, 1, "Flash", "ic")])
    pcb("nir_board", NX - 9.0, NX + 9.0, zc - 10.0, zc + 10.0, 15.0, 1.2, SEN, E(-35), "NIR module: Mira220 board", 1.5, comps="rear", seed=82,
        ics=[(NX, zc, 6.6, 6.2, 0.9, -1, "Mira220, NIR-enhanced", "sensor"), (NX, zc - 7.5, 9, 2.2, 1.4, 1, "MIPI connector", "conn")])
    image_sensor("nir_sensor", NX, zc, 13.0, 15.0, "mira", SEN, E(-35), "Mira220, 1600 x 1400, global shutter, NIR-enhanced")
    pcb("proc", -Wd / 2 + 5, Wd / 2 - 5, 4.0, H - 4.0, 38.0, 1.2, PROC, E(15), "Processing board: thermal and NIR in sync, radiometry, Ethernet", 5.0, comps="both", seed=90,
        ics=[(0, zc, 12, 12, 1.2, 1, "Processor", "ic"), (-16, zc + 10, 5, 5, 1.0, 1, "DDR", "ic"), (16, zc + 10, 5, 4, 1.0, 1, "PHY", "ic"),
             (0, 12.0, 8, 8, 2.0, 1, "Connector header", "conn")])
    for sx in (-1, 1):
        standoff(f"so{sx}", sx * (Wd / 2 - 6.0), zc, 28.5, 38.0, 1.0, PROC, E(10), "Standoff")
    rc.export(os.path.join(REPO, "cameras", "th", "mechanical", "out"), "aviac_th")


def ring_text(items, x, z, r, y, size, a0, a1):
    """Numbers engraved round a lens ring, each upright on the barrel and spread from angle a0 to a1 (degrees,
    0 = +x, 90 = +z), facing out of the surface."""
    import math
    sol = None
    n = len(items)
    for i, t in enumerate(items):
        a = a0 + (a1 - a0) * (i / max(1, n - 1))
        w = cq.Workplane("YZ").text(t, size, 0.12, kind="bold", halign="center", valign="center")
        bb = w.val().BoundingBox()
        w = w.translate((-bb.xmin + r - 0.06, -(bb.ymin + bb.ymax) / 2, -(bb.zmin + bb.zmax) / 2))
        w = w.rotate((0, 0, 0), (1, 0, 0), 90)                      # read round the ring, not along the axis
        w = w.rotate((0, 0, 0), (0, 1, 0), -a)                     # to its angle round the lens axis
        w = w.translate((x, y, z))
        sol = w if sol is None else sol.union(w)
    return sol


def c_mount_lens(x, z, y0):
    """A machine-vision C-mount lens, front toward -y from the mount face at y0: bright mount ring, ribbed collar,
    iris ring with its f-numbers, focus ring with distances, a knurled locking screw, a flared front with a filter
    thread, and the glass stack you can look into. A cobalt band marks the SWIR coating."""
    import math
    G, ex = OPT, E(-70)
    add("mount_ring", yring(x, z, y0 - 1.6, y0 + 0.4, 13.6, 11.8), G, ex, mat="steel", color=(0.75, 0.76, 0.78), mass=4.0, label="C-mount, 1-32 UN thread")
    col = ycyl(x, z, y0 - 8.5, y0 - 1.6, 14.6)
    for k in range(40):
        a = 2 * math.pi * k / 40
        col = col.cut(ycyl(x + 14.75 * math.cos(a), z + 14.75 * math.sin(a), y0 - 7.8, y0 - 2.4, 0.42))
    add("collar", col, G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Lens collar")
    iris = ycyl(x, z, y0 - 15.5, y0 - 8.8, 15.6)
    for k in range(48):
        a = 2 * math.pi * k / 48
        iris = iris.cut(ycyl(x + 15.75 * math.cos(a), z + 15.75 * math.sin(a), y0 - 15.0, y0 - 13.4, 0.38))
    add("iris_ring", iris, G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Iris ring, f/1.4 to f/16")
    pass
    foc = ycyl(x, z, y0 - 28.0, y0 - 15.8, 16.6)
    for k in range(60):
        a = 2 * math.pi * k / 60
        foc = foc.cut(ycyl(x + 16.75 * math.cos(a), z + 16.75 * math.sin(a), y0 - 24.5, y0 - 18.0, 0.45))
    add("focus_ring", foc, G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Focus ring")
    pass
    pass
    add("engraving", ring_text(["AVIAC"], x, z, 16.6, y0 - 22.0, 2.2, 90, 90), G, ex, mat="etch", color=(0.88, 0.88, 0.9), mass=0.0,
        label="Engraved: Aviac")
    flare = W(cq.Solid.makeLoft([rc.rr_wire(33.2, 33.2, 16.59, y0 - 28.0, z), rc.rr_wire(38.0, 38.0, 18.99, y0 - 36.0, z)], True)).translate((x, 0, 0)) if False else \
        W(cq.Solid.makeCone(16.6, 19.0, 8.0, V(x, y0 - 28.0, z), V(0, -1, 0)))
    front = flare.union(ycyl(x, z, y0 - 39.0, y0 - 36.0, 19.6))
    for k in range(20):                                                 # fine filter-thread rings on the front lip
        front = front.cut(yring(x, z, y0 - 38.6 + k * 0.14, y0 - 38.55 + k * 0.14, 19.7, 19.45))
    front = front.cut(ycyl(x, z, y0 - 40, y0 - 22, 15.9))
    add("front_barrel", front, G, ex, mat="anodised", color=(0.012, 0.012, 0.014), density=ALU, label="Front barrel, 40.5 mm filter thread")
    add("swir_band", yring(x, z, y0 - 31.5, y0 - 30.3, 17.9, 17.0), G, ex, mat="satin", color=(0.04, 0.16, 0.55), mass=0.0, label="Cobalt band: SWIR coating, 0.9-1.7 um")
    for k in (-1, 1):
        add(f"front_screw_{k}", W(cq.Solid.makeCylinder(0.7, 0.6, V(x + k * 17.6, y0 - 39.1, z), V(0, 1, 0))), G, ex, mat="steel", color=(0.3, 0.3, 0.32), mass=0.0, label="Retainer screw")
    rc.lens_stack("swir", x, z, y0 - 38.3, 14.8, G, ex, (0.24, 0.15, 0.06), depth=16.0)



def build_sw():
    """SW after a machine-vision box camera: a white body with rounded edges, a black front plate, a black finned
    band along each side, and a proper C-mount lens."""
    rc.parts.clear()
    Wd, H, D = 54.0, 54.0, 60.0
    Lz = H / 2
    shell = rbox(-Wd / 2, Wd / 2, 3.0, D, 0, H, 7.0, "|Y").cut(rbox(-Wd / 2 + 2, Wd / 2 - 2, 1.0, D - 2, 2, H - 2, 5.0, "|Y"))
    add("rear_housing", shell, EXT, E(55), finish="body", density=1.15, label="Body, PA12-CF, painted")
    # black rear rim, like a machine-vision box camera
    add("rear_rim", rbox(-Wd / 2 - 0.3, Wd / 2 + 0.3, D - 5.0, D + 0.4, -0.3, H + 0.3, 7.2, "|Y").cut(rbox(-Wd / 2 + 2, Wd / 2 - 2, D - 6, D + 1, 2, H - 2, 5.0, "|Y")),
        EXT, E(70), mat="powder", color=(0.015, 0.015, 0.017), density=ALU, label="Rear rim, black anodised")
    # the Aviac wing mark, large, printed on both sides
    for sx in (-1, 1):
        sol = None
        for pts in fitted_mark(D / 2 + 1.0, H / 2, H * 0.62, D * 0.5):
            if sx < 0:
                pts = [(D + 2.0 - y, z) for (y, z) in pts]
            w = cq.Workplane("YZ").polyline(pts).close().extrude(0.12 * sx)
            sol = w if sol is None else sol.union(w)
        add(f"side_mark_{sx}", sol.translate((sx * (Wd / 2 - 0.02), 0, 0)), EXT, E(55), mat="powder", color=(0.004, 0.004, 0.005), mass=0.0, label="Aviac mark, printed")
    plate = rbox(-Wd / 2 + 2.5, Wd / 2 - 2.5, 0.0, 4.0, 2.5, H - 2.5, 4.5, "|Y")
    plate = plate.cut(ycyl(0, Lz, -1, 5, 12.0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            plate = plate.cut(ycyl(sx * 17.5, Lz + sz * 17.5, -1, 1.2, 1.1))
    add("panel", plate, EXT, E(-95), finish="panel", density=ALU, label="Front plate, black anodised")
    for sx in (-1, 1):
        for sz in (-1, 1):
            add(f"plate_screw_{sx}_{sz}", ycyl(sx * 17.5, Lz + sz * 17.5, -0.2, 0.9, 0.95), EXT, E(-95), mat="steel", color=(0.08, 0.08, 0.09), mass=0.1, label="M2 screw")
    add("plate_name", rc.etch_text("SW", 2.2, 0.0, 5.0, 0.0), EXT, E(-95), mat="etch", color=(0.85, 0.85, 0.86), mass=0.0, label="Name, engraved")
    add("light_dot", ycyl(17.5, 5.5, -0.3, 0.4, 0.9), EXT, E(-95), mat="led", color=(1.0, 0.55, 0.12), mass=0.0, label="Status light")
    c_mount_lens(0.0, Lz, 0.0)
    # InGaAs sensor in a ceramic package behind the mount, cooler, boards
    x, z, yb = 0.0, Lz, 17.5
    add("swir_pkg", rbox(x - 11, x + 11, yb - 2.2, yb, z - 9.5, z + 9.5, 0.8), SEN, E(-15), mat="ceramic_dark", color=(0.10, 0.10, 0.105), mass=2.0,
        label="InGaAs SWIR sensor, 640 x 512, 5 um pixels (placeholder)")
    add("swir_frame", box(x - 7.2, x + 7.2, yb - 2.32, yb - 2.2, z - 5.9, z + 5.9).cut(box(x - 6.9, x + 6.9, yb - 5, yb + 5, z - 5.6, z + 5.6)), SEN, E(-15),
        mat="gold", color=(0.85, 0.65, 0.25), mass=0.0, label="Bond frame")
    add("swir_die", box(x - 6.6, x + 6.6, yb - 2.3, yb - 2.24, z - 5.3, z + 5.3), SEN, E(-15), mat="die_dark", color=(0.06, 0.04, 0.05), mass=0.0, label="InGaAs pixel array")
    add("swir_window", box(x - 8.6, x + 8.6, yb - 2.7, yb - 2.3, z - 7.4, z + 7.4), SEN, E(-15), mat="window", color=(0.9, 0.95, 1.0), mass=0.0, label="Sensor window")
    pcb("sensor_board", -22.0, 22.0, 4.0, 48.0, yb, 1.4, SEN, E(-15), "Sensor board", 5.0, comps="rear", seed=95,
        ics=[(0, 12, 6, 6, 1.0, 1, "TEC driver", "ic"), (-14, 40, 5, 5, 1.0, 1, "ADC", "ic")])
    add("tec", box(x - 9, x + 9, yb + 1.4, yb + 5.4, z - 9, z + 9), SEN, E(-5), mat="satin", color=(0.75, 0.76, 0.77), density=ALU, label="Heat spreader for the sensor's cooler")
    pcb("proc", -22.0, 22.0, 4.0, 48.0, 40.0, 1.2, PROC, E(10), "Processing board: non-uniformity correction, sync, Ethernet", 6.0, comps="both", seed=97,
        ics=[(0, 26, 12, 12, 1.2, 1, "FPGA, SWIR pipeline", "ic"), (-14, 38, 6, 5, 1.0, 1, "DDR", "ic"), (14, 38, 6, 5, 1.0, 1, "Flash", "ic")])
    add("rear_conn", ycyl(0, 14.0, D - 0.5, D + 3.0, 5.0).cut(ycyl(0, 14.0, D, D + 4, 3.6)), EXT, E(70), mat="steel", color=(0.6, 0.6, 0.62), mass=2.0, label="M12 Ethernet / power connector")
    rc.export(os.path.join(REPO, "cameras", "sw", "mechanical", "out"), "aviac_sw")


if __name__ == "__main__":
    {"th": build_th, "sw": build_sw}[sys.argv[1] if len(sys.argv) > 1 else "th"]()
