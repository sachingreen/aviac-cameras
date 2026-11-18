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


def body(Wd, H, D, lenses, word, bar_z):
    FT, frame, recess, wall = 6.0, 1.6, 1.2, 1.5
    fs, panel, rh, (px0, px1, pz0, pz1), inset = sculpted_body(Wd, H, -4.0, D, 7.0, FT, frame, recess, wall, 3.0, EXF, E(55), taper=1.4, r_rear=4.5, hd=3.8, b=0.9)
    for (x, z, rr) in lenses:
        panel = panel.cut(ycyl(x, z, -1, 5, rr))
    panel = light_bar(panel, (0.0, bar_z, 10.0, 0.9), recess, EXF)
    add("panel", panel, EXT, EXF, finish="panel", density=PA12CF, label="Front panel")
    light_pipe(0.0, bar_z, 10.0, recess + 1.0, 6.5, EXT, E(-82))
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
    try:
        rh = rh.cut(mark_on_side(10.0, 18.0, H - 11.0, Wd / 2 - inset(18.0), 0.4))
        t = cq.Workplane("YZ").text(word, 3.0, 0.5, kind="bold", halign="center", valign="center")
        bb = t.val().BoundingBox()
        xf = Wd / 2 - inset(18.0)
        rh = rh.cut(t.translate((xf - 0.35 - bb.xmin, 18.0 - (bb.ymin + bb.ymax) / 2, H - 22.0 - (bb.zmin + bb.zmax) / 2)))
    except Exception as e:
        print("mark skipped", e)
    rh = rh.cut(box(-5.0, 5.0, D - 2, D + 1, H / 2 - 2.0, H / 2 + 2.0))
    add("rear_housing", rh, EXT, E(55), finish="body", density=PA12CF, label="Rear housing, PA12-CF")
    for sx in (-1, 1):
        for zz in (6.0, H - 6.0):
            screw(f"rear_screw_{sx}_{int(zz)}", sx * (Wd / 2 - 6.0), zz, D + 0.6, 10.0, 0.9, EXT, E(68), "M2 x 10, rear", toward=-1)
    for sx in (-1, 1):
        standoff(f"so{sx}", sx * (Wd / 2 - 5.0), H / 2, 10.0, D - 9.0, 1.0, SEN, E(-5), "Standoff")
    return D


def build_th():
    rc.parts.clear()
    Wd, H, D = 60.0, 42.0, 36.0
    LW, RGB = (-9.0, 21.0), (17.5, 21.0)
    body(Wd, H, D, [(LW[0], LW[1], 12.6), (RGB[0], RGB[1], 7.2)], "TH", 37.0)
    lens_ring("lwir", LW[0], LW[1], -3.8, 1.2, 27.0, 22.0, OPT, E(-70))
    oring("lwir_oring", LW[0], LW[1], 1.0, 12.4, 0.55, OPT, E(-88))
    big_lens("lwir", LW[0], LW[1], -6.5, 9.0, 10.0, (0.20, 0.17, 0.24), "Germanium LWIR lens, 13 mm f/1.0", "Germanium window, DLC-coated", glass_mat="die_dark")
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
    gimbal_yoke(0.0, 14.0, H / 2, Wd / 2, H + 12.0)
    rc.export(os.path.join(REPO, "cameras", "th", "mechanical", "out"), "aviac_th")


def build_sw():
    rc.parts.clear()
    Wd, H, D = 58.0, 46.0, 44.0
    L = (0.0, 23.0)
    body(Wd, H, D, [(L[0], L[1], 16.2)], "SW", 41.5)
    lens_ring("swir", L[0], L[1], -3.8, 1.2, 34.0, 28.5, OPT, E(-70))
    oring("swir_oring", L[0], L[1], 1.0, 15.8, 0.6, OPT, E(-88))
    big_lens("swir", L[0], L[1], -9.0, 12.0, 13.2, (0.24, 0.15, 0.06), "SWIR lens, 25 mm f/1.4, 0.9-1.7 um coating", "Front element, SWIR AR coating")
    # InGaAs sensor in a ceramic package with a thermo-electric cooler behind it
    x, z, yb = L[0], L[1], 14.0
    add("swir_pkg", rbox(x - 11, x + 11, yb - 2.2, yb, z - 9.5, z + 9.5, 0.8), SEN, E(-15), mat="ceramic_dark", color=(0.10, 0.10, 0.105), mass=2.0,
        label="InGaAs SWIR sensor, 640 x 512, 5 um pixels (placeholder)")
    add("swir_frame", box(x - 7.2, x + 7.2, yb - 2.32, yb - 2.2, z - 5.9, z + 5.9).cut(box(x - 6.9, x + 6.9, yb - 5, yb + 5, z - 5.6, z + 5.6)), SEN, E(-15),
        mat="gold", color=(0.85, 0.65, 0.25), mass=0.0, label="Bond frame")
    add("swir_die", box(x - 6.6, x + 6.6, yb - 2.3, yb - 2.24, z - 5.3, z + 5.3), SEN, E(-15), mat="die_dark", color=(0.06, 0.04, 0.05), mass=0.0, label="InGaAs pixel array")
    add("swir_window", box(x - 8.6, x + 8.6, yb - 2.7, yb - 2.3, z - 7.4, z + 7.4), SEN, E(-15), mat="window", color=(0.9, 0.95, 1.0), mass=0.0, label="Sensor window")
    pcb("sensor_board", -24.0, 24.0, 4.0, 42.0, yb, 1.4, SEN, E(-15), "Sensor board", 5.0, comps="rear", seed=95, keep=(),
        ics=[(0, 23, 6, 6, 1.0, 1, "TEC driver", "ic"), (-14, 34, 5, 5, 1.0, 1, "ADC", "ic")])
    add("tec", box(x - 9, x + 9, yb + 1.4, yb + 5.4, z - 9, z + 9), SEN, E(-5), mat="satin", color=(0.75, 0.76, 0.77), density=ALU, label="Heat spreader for the sensor's cooler")
    pcb("proc", -25.0, 25.0, 4.0, 42.0, 30.0, 1.2, PROC, E(10), "Processing board: non-uniformity correction, sync, USB-C / Ethernet", 6.0, comps="both", seed=97,
        ics=[(0, 23, 12, 12, 1.2, 1, "FPGA, SWIR pipeline", "ic"), (-16, 32, 6, 5, 1.0, 1, "DDR", "ic"), (16, 32, 6, 5, 1.0, 1, "Flash", "ic"),
             (0, 23, 8.9, 3.2, D - 31.2 - 0.5, 1, "USB-C", "steel")])
    gimbal_yoke(0.0, 18.0, H / 2, Wd / 2, H + 12.0)
    rc.export(os.path.join(REPO, "cameras", "sw", "mechanical", "out"), "aviac_sw")


if __name__ == "__main__":
    {"th": build_th, "sw": build_sw}[sys.argv[1] if len(sys.argv) > 1 else "th"]()
