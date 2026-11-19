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
                            m12_lens, light_bar, light_pipe, oring, pcb, standoff, screw, image_sensor, gimbal_yoke, mark_on_side, rr_wire)

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


def build_th():
    rc.parts.clear()
    Wd, H, D = 60.0, 42.0, 36.0
    LW, RGB = (-9.0, 21.0), (17.5, 21.0)
    body(Wd, H, D, [(LW[0], LW[1], 12.6), (RGB[0], RGB[1], 7.2)], "TH", 37.0, [(LW[0], LW[1], 13.9, "open"), (RGB[0], RGB[1], 9.3)], vents=True)
    thermal_lens("lwir", LW[0], LW[1], -6.0, 13.0)
    lens_ring("rgb", RGB[0], RGB[1], -3.8, 1.2, 18.0, 15.0, OPT, E(-70))
    m12_lens("rgb", RGB[0], RGB[1], -6.0, 12.0, OPT, E(-60), (0.10, 0.22, 0.20), "M12 lens, colour camera")
    # thermal core: a machined block with the bolometer window, on its own board
    core = rbox(LW[0] - 12.5, LW[0] + 12.5, 9.0, 21.0, LW[1] - 12.5, LW[1] + 12.5, 1.5)
    add("core", core, SEN, E(-25), mat="satin", color=(0.62, 0.60, 0.56), density=ALU * 0.8, label="LWIR core, 640 x 512 uncooled VOx, 12 um (placeholder)")
    add("core_window", box(LW[0] - 6.5, LW[0] + 6.5, 8.6, 9.05, LW[1] - 5.2, LW[1] + 5.2), SEN, E(-25), mat="die_dark", color=(0.05, 0.05, 0.08), mass=0.0,
        label="Microbolometer array behind its window")
    pcb("rgb_board", RGB[0] - 8.5, RGB[0] + 8.5, RGB[1] - 9.0, RGB[1] + 9.0, 8.0, 1.2, SEN, E(-15), "Colour sensor board", 1.5, comps="rear", seed=81,
        ics=[(RGB[0], RGB[1], 6.6, 6.2, 0.9, -1, "Mira220, colour", "sensor")])
    image_sensor("rgb_sensor", RGB[0], RGB[1], 6.0, 8.0, "mira", SEN, E(-15), "Mira220 colour sensor")
    pcb("proc", -27.0, 27.0, 4.0, 38.0, 24.0, 1.2, PROC, E(10), "Processing board: radiometric pipeline, sync, USB-C / Ethernet", 6.0, comps="both", seed=90,
        ics=[(0, 21, 12, 12, 1.2, 1, "FPGA, thermal pipeline", "ic"), (-16, 28, 6, 5, 1.0, 1, "DDR", "ic"), (16, 28, 6, 5, 1.0, 1, "Flash", "ic"),
             (0, 8, 14, 3, 1.6, -1, "Board-to-board", "conn"), (0, 21, 8.9, 3.2, D - 25.2 - 0.5, 1, "USB-C", "steel")])
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
    mh = 30.0
    for sx in (-1, 1):
        sol = None
        for poly in rc.logo_polygons():
            pts = [(D / 2 - 1.0 + px * mh * (1 if sx > 0 else -1), H / 2 + (py - 0.5) * mh) for (px, py) in poly]
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
