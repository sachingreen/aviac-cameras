#!/usr/bin/env python3
"""Aviac VTOL survey drone, modelled from photos of the real aircraft (CadQuery). Approximate: proportions read from
the photos, not from drawings.

Slate-grey gloss fuselage pod with a nose tractor propeller and spinner, a straight high wing about 2 m across,
two carbon booms under the wing carrying four lift motors on white mounts, white lattice landing legs, black
pods at the boom ends. Frame: X right, Y aft (the nose points to -Y, like the cameras' lenses), Z up. Units: mm.
The camera bay is on the belly under the wing: CAMERA_MOUNT gives its centre.

  python3 toolkit/cad/vtol.py   -> cameras/drone/out/ (model.js, frame.json, finishes.json, drone.step)
"""
import math, os, sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rugged_cameras as rc
from rugged_cameras import add, box, rbox, zcyl, W, V

G = "Drone"
GREY, WING, WHITE, CF, BLACK = (0.19, 0.22, 0.25), (0.33, 0.35, 0.37), (0.85, 0.85, 0.83), (0.02, 0.02, 0.022), (0.012, 0.012, 0.013)
L, R0, Z0 = 1100.0, 95.0, 0.0        # fuselage length, max half-width, axis height (belly at about Z0 - 80)


def ellipse_wire(y, a, b, zc):
    pts = [V(a * math.cos(t), y, zc + b * math.sin(t)) for t in [2 * math.pi * i / 40 for i in range(40)]]
    return cq.Wire.makePolygon(pts, close=True)


def fuselage():
    # stations along y (nose at -L/2): half-width, half-height, centre height
    st = [(-550, 4, 4, 0), (-530, 34, 30, 0), (-480, 62, 55, 2), (-400, 82, 72, 6), (-280, 94, 82, 8), (-120, 95, 84, 8),
          (60, 90, 80, 6), (220, 76, 66, 4), (360, 52, 44, 4), (470, 26, 22, 6), (545, 6, 6, 8)]
    wires = [ellipse_wire(y, a, b, zc) for (y, a, b, zc) in st]
    body = W(cq.Solid.makeLoft(wires, True))
    add("fuselage", body, G, mat="gloss_grey", color=GREY, mass=0.0, label="Fuselage, glass fibre, slate-grey gloss")
    # two dark access openings on top, like the photos
    for (yc, ry) in ((-300, 70), (40, 60)):
        hatch = cq.Workplane("XY").ellipse(42, ry).extrude(2).translate((0, yc, 86))
        add(f"hatch_{yc}", hatch, G, mat="black", color=BLACK, mass=0.0, label="Access opening")
    # spinner and two-blade tractor prop at the nose
    sp = cq.Workplane("XZ").circle(26).workplane(offset=40).circle(3).loft().translate((0, -548, 0))
    add("spinner", sp, G, mat="steel", color=(0.7, 0.7, 0.72), mass=0.0, label="Spinner")
    for s in (-1, 1):
        blade = cq.Workplane("XZ").ellipse(160, 14).extrude(5).translate((s * 150, -560, 0)).rotate((0, -560, 0), (0, -559, 0), s * 12)
        add(f"prop_{s}", blade, G, mat="cfrp", color=CF, mass=0.0, label="Tractor propeller")


def wing():
    span, root, tip, t = 2100.0, 230.0, 200.0, 26.0
    for s in (-1, 1):
        prof = cq.Workplane("YZ").ellipse(root / 2, t / 2).workplane(offset=s * span / 2).ellipse(tip / 2, t * 0.4)
        w = prof.loft().translate((0, -60, 92))
        add(f"wing_{s}", w, G, mat="gloss_grey", color=WING, mass=0.0, label="Wing")
    # roundel stripes near the root, white, like the photos
    for s in (-1, 1):
        for k in range(4):
            add(f"stripe_{s}_{k}", box(s * (150 + k * 22) - 4, s * (150 + k * 22) + 4, -40, 20, 104, 106), G, mat="gloss_white", color=WHITE, mass=0.0, label="Marking")


def booms():
    for s in (-1, 1):
        x = s * 330.0
        b = W(cq.Solid.makeCylinder(11, 980, V(x, -560, 70), V(0, 1, 0)))
        add(f"boom_{s}", b, G, mat="cfrp", color=CF, mass=0.0, label="Carbon boom")
        add(f"boom_clamp_{s}", rbox(x - 22, x + 22, -100, -20, 58, 92, 6), G, mat="gloss_white", color=WHITE, mass=0.0, label="Boom mount")
        for (y, end) in ((-560, "front"), (420, "rear")):
            add(f"motor_mount_{s}_{end}", zcyl(x, y, 74, 104, 15).union(rbox(x - 9, x + 9, y - 30, y + 30, 64, 80, 4)), G, mat="gloss_white", color=WHITE, mass=0.0, label="Motor mount")
            add(f"motor_{s}_{end}", zcyl(x, y, 104, 134, 20), G, mat="anodised", color=BLACK, mass=0.0, label="Lift motor")
            add(f"motor_cap_{s}_{end}", zcyl(x, y, 134, 138, 14), G, mat="steel", color=(0.8, 0.8, 0.82), mass=0.0, label="Motor bell")
            for k in (0, 1):
                a = math.radians(30 + 180 * k)
                bl = cq.Workplane("XY").ellipse(180, 13).extrude(3).rotate((0, 0, 0), (0, 0, 1), math.degrees(a)).translate((x + 90 * math.cos(a), y + 90 * math.sin(a), 140))
                add(f"lift_prop_{s}_{end}_{k}", bl, G, mat="cfrp", color=CF, mass=0.0, label="Lift propeller")
        pod = cq.Workplane("XZ").ellipse(20, 26).workplane(offset=-150).ellipse(14, 18).loft().translate((x, 560, 60))
        add(f"pod_{s}", pod, G, mat="anodised", color=BLACK, mass=0.0, label="Boom end pod")
        # white lattice landing leg under the boom, angled out
        # tall enough to clear a camera under the belly: boom at z 60, floor at z -260
        out = s * 70.0
        prof = [(x - 9, 60), (x + 9, 60), (x + out + 9, -258), (x + out - 9, -258)]
        leg = cq.Workplane("XZ").polyline(prof).close().extrude(-60).translate((0, -290, 0))
        for k in range(6):
            zc = 20 - k * 48
            leg = leg.cut(cq.Workplane("XZ").ellipse(5, 16).extrude(-70).translate((x + out * (60 - zc) / 318, -285, zc)))
        leg = leg.union(rbox(x + out - 26, x + out + 26, -300, -220, -262, -256, 4))
        add(f"leg_{s}", leg, G, mat="gloss_white", color=WHITE, mass=0.0, label="Landing leg, printed lattice")


fuselage(); wing(); booms()
CAMERA_MOUNT = (0.0, -150.0, -76.0)        # belly, ahead of the wing

rc.FINISHES = {"default": {}}
rc.export(os.path.join(rc.REPO, "cameras", "drone", "mechanical", "out"), "aviac_vtol", extra_frame={"camera_mount": CAMERA_MOUNT})
