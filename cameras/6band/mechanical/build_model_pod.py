#!/usr/bin/env python3
"""Aviac 6-band camera - parametric mechanical model (CadQuery).

Frame: X forward (flight direction), Y right, Z up. Z=0 is the mounting face
against the aircraft belly; everything hangs below (negative Z). Units: mm.

The carrier board geometry (size, connector positions, part outlines) is read from
boards/orin-carrier/kicad/placement.json, which the PCB generator writes, so the enclosure
cut-outs always follow the real board.

Optics: IMX565 on a C-mount lens, three Mira220 modules on CS-mount lenses, all
four screwed into one machined aluminium lens plate.

Outputs (in ./out): aviac_camera.step, enclosure_*.stl/.step, lens_plate.step,
model.js (tessellated parts + metadata), frame.json, parts.json
"""
import base64, json, math, os, random, struct
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
random.seed(7)
PL = json.load(open(os.path.join(HERE, "..", "..", "..", "boards", "orin-carrier", "kicad", "placement.json")))
BL, BW = PL["board"]
BX0 = 2.0                      # board x=0 sits at model X=2


def b2m(bx, by):
    """Board coordinates (KiCad, y down) -> model XY."""
    return BX0 + bx, BW / 2 - by


# ----------------------------------------------------------------- parameters
W = BW + 10.0
XC0, XC1 = 0.0, BL + 6.0
XO1 = XC1 + 110.0
ZC = -33.0
ZO = -72.0
T = 1.4
ZSPLIT = -20.0
PCB_T = 1.0
PCB_ZTOP = -8.0
MOD_L, MOD_W = 69.6, 45.0
HS_BASE, HS_FIN, HS_PITCH, HS_FT = 2.0, 8.0, 3.2, 0.7

sock = PL["parts"]["J2"]
SOCK_X, SOCK_Y = b2m(sock["x"], sock["y"])
MOD_X1 = SOCK_X + 7.98          # contact edge of the module
MOD_X0 = MOD_X1 - MOD_W
MOD_ZTOP = PCB_ZTOP - PCB_T - 6.5

RGB = (XC1 + 54.0, 0.0)
MIRAS = [((XC1 + 18.0, 0.0), "Red edge", (0.62, 0.05, 0.08)),
         ((XC1 + 85.0, -19.0), "NIR", (0.33, 0.03, 0.12)),
         ((XC1 + 85.0, 19.0), "Extended NIR", (0.16, 0.02, 0.10))]
LENS_FRONT_Z = -67.0
C_FLANGE, CS_FLANGE = 17.526, 12.526
RGB_LENS_LEN, CS_LENS_LEN = 38.0, 30.0

parts = []


def add(name, solid, color, group, explode=(0, 0, 0), density=None, mass=None, label=None, mat="plastic", proxy=False):
    parts.append(dict(name=name, solid=solid, color=color, group=group, explode=explode, density=density, mass=mass,
                      label=label or name, mat=mat, proxy=proxy))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cbox(x, y, z0, z1, lx, ly):
    return box(x - lx / 2, x + lx / 2, y - ly / 2, y + ly / 2, z0, z1)


def cyl(x, y, z0, z1, r):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def ring(x, y, z0, z1, ro, ri):
    return cq.Workplane("XY").circle(ro).circle(ri).extrude(z1 - z0).translate((x, y, z0))


def dome(x, y, z, r, h, down=True):
    R = (r * r + h * h) / (2 * h)
    s = cq.Workplane("XY").sphere(R).translate((0, 0, R - h))
    cap = s.intersect(cq.Workplane("XY").circle(r).extrude(h).translate((0, 0, -h)))
    if not down:
        cap = cap.mirror("XY")
    return cap.translate((x, y, z))


def pbox(ref, pad=0.0):
    """Model-space XY box (x0, x1, y0, y1) of a board part's footprint."""
    b = PL["parts"][ref]["bbox"]
    xa, ya = b2m(b[0], b[1]); xb, yb = b2m(b[2], b[3])
    return min(xa, xb) - pad, max(xa, xb) + pad, min(ya, yb) - pad, max(ya, yb) + pad


BLK, SIL, GLD = (0.03, 0.03, 0.035), (0.72, 0.73, 0.75), (0.83, 0.62, 0.20)
ENC = (0.055, 0.058, 0.065)
PCBG = (0.02, 0.20, 0.10)
PCBK = (0.02, 0.025, 0.03)
BEIGE = (0.80, 0.77, 0.68)

# ------------------------------------------------------------------ enclosure
def outer_solid(d=0.0):
    """Outer skin; with d > 0 the same shape shrunk by d on every face (used as the cavity)."""
    w = W / 2 - d
    a = box(XC0 + d, XC1, -w, w, ZC + d, -d)
    b = box(XC1 - 0.01, XO1 - d, -w, w, ZO + d, -d)
    s = a.union(b)
    k = d * 0.414
    step = (cq.Workplane("XZ").polyline([(XC1 - 26 + k + d, ZC + d), (XC1 + d, ZC + d), (XC1 + d, ZC - 26 + k + d)]).close()
            .extrude(2 * w).translate((0, w, 0)))
    s = s.union(step)
    s = s.cut(box(XC0 - 5, XC1 + d, -w - 1, w + 1, ZO - 5, ZC + d).cut(step))
    nose = (cq.Workplane("XZ").polyline([(XC0 - 1, ZC - 1), (XC0 + 12 + d * 2.4, ZC - 1), (XC0 - 1, ZC + 12 + d * 2.4)]).close()
            .extrude(W + 2).translate((0, W / 2 + 1, 0)))
    tail = (cq.Workplane("XZ").polyline([(XO1 + 1, ZO - 1), (XO1 - 20 - d * 2.2, ZO - 1), (XO1 + 1, ZO + 34 + d * 3.4)]).close()
            .extrude(W + 2).translate((0, W / 2 + 1, 0)))
    s = s.cut(nose).cut(tail)
    for sel, r in (("|Z", 7.0 - d), ("|X", 4.0 - d)):
        try:
            s = s.edges(sel).fillet(r)
        except Exception as e:
            print("fillet skipped", sel, e)
    return s


outer = outer_solid()
shell = outer.cut(outer_solid(T))

DUCT_ZT = MOD_ZTOP - 1.2 - 2.8 - HS_BASE
duct_ceiling = box(XC0 + T, XC1 - 2, -W / 2 + T, W / 2 - T, DUCT_ZT, DUCT_ZT + 1.4)
duct_ceiling = duct_ceiling.cut(box(MOD_X0 - 1.5, MOD_X1 + 1.5, -MOD_L / 2 - 0.5, MOD_L / 2 + 0.5, DUCT_ZT - 1, DUCT_ZT + 3))
bulk = box(XC1 - 4, XC1 - 2.6, -W / 2 + T, W / 2 - T, ZC - 26, DUCT_ZT + 1.4)
shell = shell.union(duct_ceiling.intersect(outer)).union(bulk.intersect(outer))
VW = W / 2 - 8
shell = shell.cut(box(XC0 - 2, XC0 + 16, -VW, VW, ZC + 1.6, DUCT_ZT - 0.8))
nv = int(2 * VW // 7)
for i in range(1, nv):
    y = -VW + i * 2 * VW / nv
    shell = shell.union(box(XC0 + 1.0, XC0 + 13, y - 0.5, y + 0.5, ZC + 0.6, DUCT_ZT + 0.2).intersect(outer))
for i in range(7):
    x = MOD_X1 - 6 + i * 5.2
    for sgn in (-1, 1):
        y0, y1 = (W / 2 - T - 1, W / 2 + 1) if sgn > 0 else (-W / 2 - 1, -W / 2 + T + 1)
        shell = shell.cut(box(x, x + 2.6, y0, y1, ZC + 3.2, DUCT_ZT - 1.8))


def bezel(x, y, r_clear, r_seat, r_out):
    global shell
    shell = shell.cut(cyl(x, y, ZO - 2, ZO + T + 1, r_clear))
    b = ring(x, y, ZO - 1.2, ZO + 3.2, r_out, r_clear).cut(cyl(x, y, ZO + 0.9, ZO + 4, r_seat))
    shell = shell.union(b)


bezel(RGB[0], RGB[1], 15.2, 17.7, 20.0)
for (mx, my), _, _ in MIRAS:
    bezel(mx, my, 10.6, 12.8, 15.0)

# connector openings follow the real board
zt, zb = PCB_ZTOP, PCB_ZTOP - PCB_T
for ref, h in (("J1", 5.6), ("J8", 4.6), ("J9", 4.6), ("J12", 3.6), ("J13", 4.6)):
    x0, x1, y0, y1 = pbox(ref, 0.6)
    if y0 < -BW / 2 + 12:          # left flank
        shell = shell.cut(box(x0, x1, -W / 2 - 1, -W / 2 + T + 1, zt - 0.4, zt + h))
    else:                           # right flank
        shell = shell.cut(box(x0, x1, W / 2 - T - 1, W / 2 + 1, zt - 0.4, zt + h))
ux, uy = b2m(PL["parts"]["J10"]["x"], PL["parts"]["J10"]["y"])
shell = shell.cut(cyl(ux + 6, uy - 4, -3, 1, 3.3))                           # GNSS coax gland in the roof
for ref in ("D2", "D3"):
    lx, ly = b2m(PL["parts"][ref]["x"], PL["parts"][ref]["y"])
    shell = shell.cut(cyl(lx, ly, -3, 1, 0.9))                               # light pipes over the status LEDs

MOUNT = [(12, -W / 2 + 9), (12, W / 2 - 9), (XO1 - 12, -W / 2 + 9), (XO1 - 12, W / 2 - 9)]
for (x, y) in MOUNT:
    shell = shell.union(cyl(x, y, -8, 0, 4.4).intersect(outer)).cut(cyl(x, y, -9, 1, 1.6))
SCREWS = [(6, -W / 2 + 6), (6, W / 2 - 6), (XC1, -W / 2 + 4.5), (XC1, W / 2 - 4.5), (XO1 - 6, -W / 2 + 6), (XO1 - 6, W / 2 - 6)]
for (x, y) in SCREWS:
    shell = shell.union(cyl(x, y, ZSPLIT - 8, ZSPLIT + 6, 3.0).intersect(outer)).cut(cyl(x, y, ZSPLIT - 9, ZSPLIT + 7, 1.25))
try:
    logo = cq.Workplane("XZ").text("AVIAC  6B", 7.5, 0.5, kind="bold").translate((RGB[0] + 1, -W / 2 + 0.5, -44))
    shell = shell.cut(logo)
except Exception as e:
    print("logo skipped", e)
shell = shell.cut(box(-5, XO1 + 10, -80, 80, ZSPLIT - 0.35, ZSPLIT + 0.35).cut(outer_solid(0.45)))
for zz in (-52.0, -57.0, -62.0):
    shell = shell.cut(box(XC1 + 24, XO1 - 18, -80, 80, zz - 0.6, zz + 0.6).cut(outer_solid(0.5)))

split_upper = box(-10, XO1 + 30, -80, 80, ZSPLIT, 10)
upper = shell.intersect(split_upper)
lower = shell.cut(split_upper)
POSTS = [b2m(PL["parts"][r]["x"], PL["parts"][r]["y"]) for r in ("H4", "H5", "H6", "H7")]
for (x, y) in POSTS:
    upper = upper.union(cyl(x, y, zt, -T, 2.6).cut(cyl(x, y, zt - 1, -4.0, 1.25)))
add("enclosure_upper", upper, (0.075, 0.078, 0.086), "Enclosure", (0, 0, 62), density=1.01, label="Upper shell (PA12, 1.4 mm wall)", mat="shell")
add("enclosure_lower", lower, ENC, "Enclosure", (0, 0, -78), density=1.01, label="Lower shell with air duct and lens bezels (PA12)", mat="shell")
for i, (x, y) in enumerate(SCREWS):
    head = cyl(x, y, ZSPLIT - 10.5, ZSPLIT - 8, 2.2).cut(cq.Workplane("XY").polygon(6, 2.0).extrude(1.4).translate((x, y, ZSPLIT - 10.6)))
    add(f"screw_{i}", head.union(cyl(x, y, ZSPLIT - 8, ZSPLIT + 5, 1.2)), (0.10, 0.10, 0.11), "Enclosure", (0, 0, -104), mass=0.55,
        label="M2.5 x 12 socket screw", mat="steel_black")

plate = box(2, XO1 - 2, -W / 2 + 2, W / 2 - 2, 6.0, 7.5).cut(box(22, XO1 - 22, -W / 2 + 13, W / 2 - 13, 5, 9))
for (x, y) in MOUNT:
    plate = plate.cut(cyl(x, y, 5, 9, 1.6))
for x in (24, XO1 / 2, XO1 - 24):
    for y in (-W / 2 + 7, W / 2 - 7):
        plate = plate.cut(box(x - 5, x + 5, y - 1.7, y + 1.7, 5, 9))
try:
    plate = plate.edges("|Z").fillet(1.5)
except Exception:
    pass
add("mount_plate", plate, (0.03, 0.03, 0.035), "Mount", (0, 0, 100), density=1.55, label="Belly mount plate (CFRP 1.5 mm)", mat="cfrp")
for i, (x, y) in enumerate(MOUNT):
    d = cyl(x, y, 0, 1.2, 4.2).union(cyl(x, y, 1.2, 4.8, 2.6)).union(cyl(x, y, 4.8, 6.0, 4.2))
    add(f"damper_{i+1}", d, (0.85, 0.30, 0.08), "Mount", (0, 0, 82), mass=0.9, label="M3 vibration damper (silicone)", mat="rubber")

# -------------------------------------------------------------- carrier board
CB = "Carrier board"
EX_CB = (0, 0, 32)
pcb = box(BX0, BX0 + BL, -BW / 2, BW / 2, zb, zt)
for (x, y) in POSTS:
    pcb = pcb.cut(cyl(x, y, zb - 1, zt + 1, 1.35))
try:
    pcb = pcb.edges("|Z").fillet(2.0)
except Exception:
    pass
# 'proxy' parts are simplified stand-ins used by the web viewer; the studio renders replace them with the KiCad 3D export
add("carrier_pcb", pcb, PCBG, CB, EX_CB, mass=16.5, label="Carrier PCB, 100 x 82 mm, 6-layer, 1.0 mm", mat="pcb", proxy=True)
HEIGHT = {"J1": 5.0, "J8": 4.25, "J9": 4.25, "J13": 4.25, "J12": 3.2, "J3": 2.0, "J4": 2.0, "J5": 2.0, "J6": 2.0, "J11": 4.1, "U9": 2.5,
          "L1": 5.8, "L2": 3.1, "J10": 1.3, "Y1": 0.7, "SW1": 1.6, "SW2": 1.6, "Q1": 1.0, "U6": 1.4}
NAMES = {"J1": "XT30 power input, 3S-6S", "J8": "TELEM connector (MAVLink)", "J9": "Trigger connector", "J13": "Light-sensor port",
         "J12": "USB-C (flashing, data)", "J11": "M.2 Key-M socket", "U9": "GNSS receiver u-blox MAX-M10S", "L1": "Inductor 6.8 uH (7.5 V rail)",
         "L2": "Inductor 6.8 uH (3.3 V rail)", "U6": "Sync MCU STM32G0B1", "U2": "Buck 7.5 V 4 A", "U3": "Buck 3.3 V 3 A", "U5": "I2C switch",
         "U10": "IMU ICM-42688-P", "J10": "U.FL antenna connector", "Q1": "Reverse-polarity MOSFET", "U1": "Ideal-diode controller",
         "J3": "CAM0 FPC connector (RGB)", "J4": "CAM1 FPC connector (red edge)", "J5": "CAM2 FPC connector (NIR)", "J6": "CAM3 FPC connector (ext. NIR)"}
NO3D = {"J1", "J11", "U9"}      # parts with no model in the KiCad library: keep the stand-in in the renders too
caps = res = None
for ref, p in PL["parts"].items():
    if ref[0] in "HT" or ref in ("J2", "J7", "J14"):
        continue
    x0, x1, y0, y1 = pbox(ref, -0.25)
    if x1 - x0 < 0.3 or y1 - y0 < 0.3:
        continue
    small = max(x1 - x0, y1 - y0) < 2.4
    h = HEIGHT.get(ref, {"U": 1.2, "C": 0.55 if small else 1.7, "R": 0.35, "F": 0.6, "D": 0.5 if small else 2.2, "Q": 0.9, "L": 0.6}.get(ref[0], 1.0))
    z0, z1 = (zb - h, zb) if p["bottom"] else (zt, zt + h)
    s = box(x0, x1, y0, y1, z0, z1)
    if ref == "J1":      # XT30: moulded yellow shell with two recessed gold contacts, mouth toward the left flank
        ym = y0 - 2.5
        s = box(x0 + 1.2, x1 - 1.2, ym, y1 - 3.0, zt, zt + 5.0)
        s = s.cut(box(x0 + 2.4, x1 - 2.4, ym - 1, ym + 6.5, zt + 0.9, zt + 4.1))
        s = s.edges("|Y").fillet(0.6)
        add("brd_J1", s, (0.93, 0.74, 0.08), CB, EX_CB, mass=0.0, label=NAMES["J1"], mat="plastic_gloss")
        cxm = (x0 + x1) / 2
        for k, dx in enumerate((-2.5, 2.5)):
            pin = cq.Workplane("XZ").circle(1.0).extrude(-6.0).translate((cxm + dx, ym + 0.8, zt + 2.5))
            add(f"brd_J1_pin{k}", pin, GLD, CB, EX_CB, mass=0.0, label="XT30 contact", mat="gold")
        continue
    if ref[0] == "C":
        caps = s if caps is None else caps.union(s)
    elif ref[0] in "RF":
        res = s if res is None else res.union(s)
    else:
        col, mat = BLK, "ic"
        if ref[0] == "J":
            col = (0.93, 0.74, 0.08) if ref == "J1" else SIL if ref == "J12" else GLD if ref == "J10" else BEIGE
            mat = "steel" if ref == "J12" else "plastic_gloss"
        if ref[0] == "L":
            col, mat = (0.20, 0.20, 0.21), "ferrite"
        if ref in ("U9", "Y1"):
            col, mat = SIL, "steel"
        add("brd_" + ref, s, col, CB, EX_CB, mass=0.0, label=NAMES.get(ref, ref), mat=mat, proxy=ref not in NO3D)
add("brd_caps", caps, (0.62, 0.50, 0.36), CB, EX_CB, mass=0.0, label="Ceramic capacitors", mat="ceramic", proxy=True)
add("brd_res", res, (0.05, 0.05, 0.06), CB, EX_CB, mass=0.0, label="Resistors and ferrite beads", mat="ic", proxy=True)
add("brd_bom_mass", cyl(POSTS[0][0], POSTS[0][1], zt, zt + 0.04, 2.7), GLD, CB, EX_CB, mass=12.0, label="Board components (sum of BOM masses)", mat="gold")
sx0, sx1, sy0, sy1 = pbox("J11")
hx, hy = b2m(PL["parts"]["H3"]["x"], PL["parts"]["H3"]["y"])
scy = (sy0 + sy1) / 2
add("m2_ssd", box(hx - 1.5, sx0 + 2.0, scy - 11, scy + 11, zt + 1.6, zt + 2.4), PCBG, CB, (0, 0, 46), mass=2.6, label="M.2 2230 NVMe SSD, 256 GB or more", mat="pcb")
add("m2_ssd_ctrl", box(hx + 12, hx + 23, scy - 7.5, scy + 7.5, zt + 2.4, zt + 3.4), BLK, CB, (0, 0, 46), mass=0.3, label="NVMe controller + flash", mat="ic")
add("m2_ssd_label", box(hx + 1.5, hx + 10.5, scy - 9.5, scy + 9.5, zt + 2.4, zt + 2.46), (0.92, 0.92, 0.90), CB, (0, 0, 46), mass=0.0, label="SSD label", mat="paper")
add("m2_standoff", cyl(hx, hy, zt, zt + 1.6, 2.4).union(cyl(hx, hy, zt + 2.4, zt + 3.4, 2.2)), SIL, CB, EX_CB, mass=0.3, label="M2 SSD standoff + screw", mat="steel")
sk = box(SOCK_X - 0.5, SOCK_X + 14.0, -37.0, 37.0, zb - 6.5, zb).cut(box(SOCK_X - 1, SOCK_X + 8.4, -34.9, 34.9, zb - 4.6, zb - 3.0))
add("sodimm_socket", sk, (0.08, 0.08, 0.09), CB, (0, 0, 22), mass=3.4, label="260-pin SO-DIMM socket (TE 2309413-1)", mat="plastic_gloss")
for i, y in enumerate((-37.6, 37.6)):
    add(f"sodimm_latch_{i}", cbox(SOCK_X - 2, y, zb - 6.0, zb - 1.0, 14, 1.2), SIL, CB, (0, 0, 22), mass=0.0, label="Socket latch", mat="steel")
STAND = [b2m(PL["parts"][r]["x"], PL["parts"][r]["y"]) for r in ("H1", "H2")]
for i, (x, y) in enumerate(STAND):
    add(f"standoff_{i}", cyl(x, y, zb - 6.5, zb, 2.5), SIL, CB, (0, 0, 22), mass=0.5, label="Module standoff M2.5 x 6.5", mat="steel")
    add(f"standoff_screw_{i}", cyl(x, y, MOD_ZTOP - 2.6, MOD_ZTOP - 1.2, 2.2), (0.10, 0.10, 0.11), "Jetson Orin Nano", (0, 0, 2), mass=0.2,
        label="M2.5 screw", mat="steel_black")

# -------------------------------------------------------------- Jetson module
JG = "Jetson Orin Nano"
mz = MOD_ZTOP
mod = box(MOD_X0, MOD_X1, -MOD_L / 2, MOD_L / 2, mz - 1.2, mz)
for (x, y) in STAND:
    mod = mod.cut(cyl(x, y, mz - 2, mz + 1, 1.4))
mod = mod.cut(box(MOD_X1 - 3, MOD_X1 + 1, 26.5, 28.0, mz - 2, mz + 1))
add("jetson_pcb", mod, (0.02, 0.10, 0.06), JG, (0, 0, 8), mass=60.0, label="Jetson Orin Nano 8GB module (69.6 x 45 mm)", mat="pcb")
fingers = None
yy = -33.0
while yy < 33.0:
    if not (26.0 < yy < 28.5):
        f = box(MOD_X1 - 2.6, MOD_X1 - 0.2, yy, yy + 0.32, mz - 1.24, mz - 1.2)
        fingers = f if fingers is None else fingers.union(f)
    yy += 0.5
add("jetson_fingers", fingers, GLD, JG, (0, 0, 8), mass=0.0, label="Edge contacts (260)", mat="gold")
uz = mz - 1.2
add("jetson_soc", cbox(MOD_X0 + 22, -6, uz - 2.8, uz, 25, 25), (0.60, 0.61, 0.63), JG, (0, 0, 3), mass=0.0, label="Orin SoC with thermal transfer plate", mat="alu")
add("jetson_ram", cbox(MOD_X0 + 22, 22, uz - 1.1, uz, 14, 11.5), BLK, JG, (0, 0, 3), mass=0.0, label="LPDDR5 memory 8 GB", mat="ic")
add("jetson_pmic", cbox(MOD_X0 + 8, -24, uz - 1.0, uz, 6, 6), BLK, JG, (0, 0, 3), mass=0.0, label="Power management IC", mat="ic")
jl = None
for (x, y) in [(8, -10), (8, 2), (8, 14), (38, -26), (38, 20)]:
    b = cbox(MOD_X0 + x, y, uz - 2.0, uz, 4.2, 4.2)
    jl = b if jl is None else jl.union(b)
add("jetson_inductors", jl, (0.22, 0.22, 0.23), JG, (0, 0, 3), mass=0.0, label="Module power inductors", mat="ferrite")
jc = None
for k in range(90):
    x, y = MOD_X0 + random.uniform(3, 42), random.uniform(-32, 32)
    if abs(x - (MOD_X0 + 22)) < 14 and abs(y + 6) < 14:
        continue
    b = cbox(round(x, 1), round(y, 1), uz - 0.5, uz, 1.0, 0.5) if k % 2 else cbox(round(x, 1), round(y, 1), uz - 0.5, uz, 0.5, 1.0)
    jc = b if jc is None else jc.union(b)
add("jetson_passives", jc, (0.62, 0.50, 0.36), JG, (0, 0, 3), mass=0.0, label="Module decoupling", mat="ceramic")

# ------------------------------------------------------------------ heatsink
TH = "Thermal"
hz = mz - 1.2 - 2.8
hs = box(MOD_X0 - 1, MOD_X1 + 1, -MOD_L / 2, MOD_L / 2, hz - HS_BASE, hz)
y = -MOD_L / 2 + 0.6
while y < MOD_L / 2 - 0.5:
    hs = hs.union(box(MOD_X0 - 1, MOD_X1 + 1, y, y + HS_FT, hz - HS_BASE - HS_FIN, hz - HS_BASE + 0.01))
    y += HS_PITCH
add("heatsink", hs, (0.10, 0.10, 0.11), TH, (0, 0, -34), density=2.70, label="Heatsink, black-anodised Al 6063, fins along airflow", mat="anodised")
add("tim_pad", cbox(MOD_X0 + 22, -6, hz - 0.02, hz + 0.3, 25, 25), (0.55, 0.60, 0.68), TH, (0, 0, -16), mass=0.8,
    label="Thermal pad on the SoC plate", mat="rubber")

# -------------------------------------------------------------------- optics
def lens(prefix, x, y, r_body, length, z_front, group, ex, label, mass, r_glass, tint):
    z_rear = z_front + length
    barrel = cyl(x, y, z_front + 1.0, z_rear, r_body - 1.0)
    barrel = barrel.union(cyl(x, y, z_front, z_front + 7.0, r_body))
    barrel = barrel.union(cyl(x, y, z_rear - 3.0, z_rear, r_body - 0.2))
    barrel = barrel.cut(cyl(x, y, z_front - 1, z_front + 3.6, r_glass + 0.9))
    barrel = barrel.cut(cq.Workplane("XY").circle(r_glass + 0.9).workplane(offset=3.0).circle(r_glass * 0.55).loft(combine=True)
                        .translate((x, y, z_front + 3.59)))
    add(prefix + "_barrel", barrel, (0.025, 0.025, 0.03), group, ex, mass=mass, label=label, mat="anodised")
    rings = None
    for (za, zb_, nteeth) in ((z_front + 9.5, z_front + 15.5, 44), (z_front + 18.5, z_front + 23.5, 44)):
        r = cyl(x, y, za, zb_, r_body + 0.6)
        for k in range(nteeth):
            a = 2 * math.pi * k / nteeth
            px, py = x + (r_body + 0.75) * math.cos(a), y + (r_body + 0.75) * math.sin(a)
            r = r.cut(cbox(px, py, za + 0.5, zb_ - 0.5, 0.9, 0.9).rotate((px, py, 0), (px, py, 1), math.degrees(a)))
        rings = r if rings is None else rings.union(r)
    add(prefix + "_rings", rings, (0.045, 0.045, 0.05), group, ex, mass=0.0, label="Focus and iris rings", mat="rubberised")
    for k, za in enumerate((z_front + 12.5, z_front + 21.0)):
        ts = cq.Workplane("YZ").circle(0.9).extrude(3.2).translate((x + r_body + 0.4, y + (4 if k else -4), za))
        add(prefix + f"_lock{k}", ts, SIL, group, ex, mass=0.0, label="Locking thumbscrew", mat="steel")
    add(prefix + "_retainer", ring(x, y, z_front + 0.2, z_front + 1.2, r_glass + 2.4, r_glass + 0.2), (0.75, 0.55, 0.20), group, ex, mass=0.0,
        label="Front retaining ring", mat="gold")
    add(prefix + "_glass", dome(x, y, z_front + 3.6, r_glass + 0.85, r_glass * 0.33), tint, group, ex, mass=0.0, label="Front element (multi-coated)", mat="lens")
    add(prefix + "_iris", cyl(x, y, z_front + 6.6, z_front + 6.8, r_glass * 0.9), (0.01, 0.01, 0.012), group, ex, mass=0.0, label="Aperture", mat="black")


OPT = "RGB camera (IMX565)"
rx, ry = RGB
C_FLANGE_Z = LENS_FRONT_Z + RGB_LENS_LEN            # C-mount flange plane
CS_FLANGE_Z = LENS_FRONT_Z + CS_LENS_LEN            # CS-mount flange plane
RGB_SENSOR_Z = C_FLANGE_Z + C_FLANGE
RB_Z = RGB_SENSOR_Z + 1.7 + 1.6                      # top face of the RGB sensor board
rgb_pcb = cbox(rx, ry, RB_Z - 1.6, RB_Z, 62.7, 58.7)
RGB_POSTS = [(rx + dx, ry + dy) for (dx, dy) in ((-28, -26), (-28, 26), (28, -26), (28, 26))]
for (px, py) in RGB_POSTS:
    rgb_pcb = rgb_pcb.cut(cyl(px, py, RB_Z - 3, RB_Z + 1, 1.3))
add("rgb_sensor_pcb", rgb_pcb, PCBK, OPT, (0, 0, 30), mass=9.0, label="CHC5 IMX565 sensor board (59 x 63 mm)", mat="pcb")
add("rgb_sensor_pkg", cbox(rx, ry, RB_Z - 1.6 - 1.7, RB_Z - 1.6, 20.0, 16.8), (0.07, 0.07, 0.08), OPT, (0, 0, 22), mass=0.0,
    label="Sony IMX565 package", mat="ceramic_dark")
add("rgb_sensor_die", cbox(rx, ry, RB_Z - 1.6 - 1.76, RB_Z - 1.6 - 1.7, 11.3, 8.3), (0.10, 0.22, 0.20), OPT, (0, 0, 22), mass=0.0,
    label="Active area 11.3 x 8.2 mm, 12.4 MP global shutter", mat="sensor")
add("rgb_b2b", cbox(rx - 22, ry, RB_Z, RB_Z + 3.0, 2.6, 22.0), BEIGE, OPT, (0, 0, 30), mass=0.0, label="100-pin board-to-board connector", mat="plastic_gloss")
add("rgb_adapter", cbox(rx - 24, ry, RB_Z + 3.0, RB_Z + 4.0, 16, 26), PCBG, OPT, (0, 0, 44), mass=1.6,
    label="Aviac adapter: 100-pin board connector to 22-pin FPC + trigger", mat="pcb")
add("rgb_adapter_fpc", box(rx - 31.6, rx - 26.4, ry - 7.6, ry + 7.6, RB_Z + 4.0, RB_Z + 6.0), BEIGE, OPT, (0, 0, 44), mass=0.25,
    label="22-pin FPC connector", mat="plastic_gloss")
rsc = None
for k in range(60):
    a, rr = random.uniform(0, 6.283), random.uniform(13, 27)
    px, py = rx + rr * math.cos(a) * 1.05, ry + rr * math.sin(a) * 0.95
    if abs(px - rx) > 29 or abs(py - ry) > 27 or (abs(px - (rx - 23)) < 10 and abs(py - ry) < 14) or any(abs(px - qx) < 3 and abs(py - qy) < 3 for qx, qy in RGB_POSTS):
        continue
    b = cbox(px, py, RB_Z, RB_Z + 0.5, 1.0, 0.5)
    rsc = b if rsc is None else rsc.union(b)
add("rgb_passives", rsc, (0.62, 0.50, 0.36), OPT, (0, 0, 30), mass=0.0, label="Decoupling capacitors", mat="ceramic")
add("rgb_ircut", cbox(rx, ry, RGB_SENSOR_Z - 5.6, RGB_SENSOR_Z - 5.0, 22, 19), (0.45, 0.85, 0.90), OPT, (0, 0, 14), mass=0.9,
    label="UV/IR-cut filter 400-700 nm", mat="filter")
lens("rgb_lens", rx, ry, 16.5, RGB_LENS_LEN, LENS_FRONT_Z, OPT, (0, 0, -44), "16 mm C-mount lens, 1.1-inch format, 12 MP", 62.0, 10.5, (0.20, 0.10, 0.32))
add("rgb_window", cyl(rx, ry, ZO + 0.9, ZO + 2.1, 17.5), (0.80, 0.90, 0.95), OPT, (0, 0, -100), mass=2.6,
    label="Protective window, AR-coated, 35 mm", mat="window")
add("rgb_bezel", ring(rx, ry, ZO - 1.9, ZO - 1.2, 20.0, 15.2), (0.85, 0.42, 0.08), OPT, (0, 0, -108), mass=1.2, label="Bezel ring, anodised", mat="accent")

MIRA_SENSOR_Z = CS_FLANGE_Z + CS_FLANGE
MIRA_POSTS = []
for i, ((mx, my), bn, bc) in enumerate(MIRAS):
    g = f"{bn} camera (Mira220)"
    pz0 = MIRA_SENSOR_Z + 1.0
    mp = cbox(mx, my, pz0, pz0 + 1.0, 30, 24)
    posts = [(mx + dx, my + dy) for (dx, dy) in ((-12.5, -9.5), (-12.5, 9.5), (12.5, -9.5), (12.5, 9.5))]
    MIRA_POSTS += posts
    for (px, py) in posts:
        mp = mp.cut(cyl(px, py, pz0 - 1, pz0 + 2, 1.05))
    add(f"mira{i}_pcb", mp, PCBG, g, (0, 0, 18), mass=2.4, label="SincereFirst SF3RA220IRY32 module (30 x 24 mm)", mat="pcb")
    add(f"mira{i}_sensor", cbox(mx, my, MIRA_SENSOR_Z, pz0, 6.6, 6.2), (0.06, 0.06, 0.07), g, (0, 0, 12), mass=0.0, label="ams OSRAM Mira220, 2.2 MP global shutter", mat="ceramic_dark")
    add(f"mira{i}_die", cbox(mx, my, MIRA_SENSOR_Z - 0.05, MIRA_SENSOR_Z, 4.5, 3.9), (0.10, 0.22, 0.20), g, (0, 0, 12), mass=0.0, label="Active area 4.46 x 3.91 mm", mat="sensor")
    add(f"mira{i}_fpc_conn", box(mx - 14.8, mx - 9.6, my - 7.6, my + 7.6, pz0 + 1.0, pz0 + 3.0), BEIGE, g, (0, 0, 18), mass=0.0,
        label="22-pin FPC connector", mat="plastic_gloss")
    mpas = None
    for k in range(14):
        px, py = mx + random.uniform(-6, 10), my + random.uniform(-9, 9)
        b = cbox(round(px, 1), round(py, 1), pz0 + 1.0, pz0 + 1.5, 1.0, 0.5)
        mpas = b if mpas is None else mpas.union(b)
    add(f"mira{i}_passives", mpas, (0.62, 0.50, 0.36), g, (0, 0, 18), mass=0.0, label="Module regulators and decoupling", mat="ceramic")
    lens(f"mira{i}_lens", mx, my, 14.0, CS_LENS_LEN, LENS_FRONT_Z, g, (0, 0, -34), "6 mm CS-mount lens, 1/2.7-inch, low distortion", 22.0, 7.8,
         (0.30, 0.08, 0.20))
    add(f"mira{i}_filter", cyl(mx, my, ZO + 0.9, ZO + 1.9, 12.6), bc, g, (0, 0, -92), mass=1.1, label=f"{bn} band-pass filter, 25 mm", mat="bandpass")
    add(f"mira{i}_bezel", ring(mx, my, ZO - 1.9, ZO - 1.2, 15.0, 10.6), (0.85, 0.42, 0.08), g, (0, 0, -100), mass=0.6, label="Bezel ring, anodised", mat="accent")

# one machined lens plate carries all four lens threads and all four sensor boards
PLT_T = 5.0
pz_bot = CS_FLANGE_Z                     # CS lenses seat against the underside of the plate
lp = box(XC1 + 2.2, XO1 - 4.5, -W / 2 + 3.2, W / 2 - 3.2, pz_bot, pz_bot + PLT_T)
lp = lp.cut(cyl(rx, ry, pz_bot - 1, pz_bot + PLT_T + 1, 18.0))
lp = lp.union(ring(rx, ry, pz_bot, C_FLANGE_Z - 3.0 + 0.01, 19.8, 18.0))            # sleeve around the C-mount lens
lp = lp.union(ring(rx, ry, C_FLANGE_Z - 3.0, C_FLANGE_Z + 6.0, 19.8, 12.7))        # C-mount thread turret
for (mx, my), _, _ in MIRAS:
    lp = lp.cut(cyl(mx, my, pz_bot - 1, pz_bot + PLT_T + 1, 12.7))
    lp = lp.union(ring(mx, my, pz_bot + PLT_T - 0.01, MIRA_SENSOR_Z - 1.2, 15.5, 12.7))
for (px, py) in MIRA_POSTS:
    lp = lp.union(ring(px, py, pz_bot + PLT_T - 0.01, MIRA_SENSOR_Z + 1.0, 2.0, 0.8))
for (px, py) in RGB_POSTS:
    lp = lp.union(ring(px, py, pz_bot + PLT_T - 0.01, RB_Z - 1.6, 2.4, 1.0))
for (x, y) in ((XC1 + 36, -36), (XC1 + 36, 36), (XC1 + 62, -40), (XC1 + 62, 40), (XC1 + 100, 0)):
    lp = lp.cut(cyl(x, y, pz_bot - 1, pz_bot + PLT_T + 1, 3.2))
add("lens_plate", lp, (0.05, 0.05, 0.055), "Optics bench", (0, 0, -10), density=2.70,
    label="Monolithic lens plate, machined 6061 aluminium: 1 x C-mount + 3 x CS-mount threads", mat="anodised")
for i, (px, py) in enumerate(RGB_POSTS + MIRA_POSTS):
    ztop = RB_Z if i < 4 else MIRA_SENSOR_Z + 2.0
    add(f"post_screw_{i}", cyl(px, py, ztop, ztop + 1.3, 1.9 if i < 4 else 1.6), (0.10, 0.10, 0.11), "Optics bench", (0, 0, 36 if i < 4 else 24), mass=0.15,
        label="Sensor-board screw", mat="steel_black")

# flexible cables from the carrier's rear edge to each camera
FP = "FPC cables"


def ribbon(name, pts, width, label):
    sol = None
    for (a, b) in zip(pts[:-1], pts[1:]):
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        if L < 0.05:
            continue
        seg = cq.Workplane("XY").box(L + 0.3, width, 0.16)
        seg = seg.rotate((0, 0, 0), (0, 1, 0), -math.degrees(math.atan2(dz, math.hypot(dx, dy)))).rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(dy, dx)))
        seg = seg.translate(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
        sol = seg if sol is None else sol.union(seg)
    add(name, sol, (0.80, 0.42, 0.05), FP, (0, 0, 0), mass=0.9, label=label, mat="fpc")


def scurve(p0, p1, n=9):
    out = []
    for k in range(n + 1):
        t = k / n
        s = (1 - math.cos(math.pi * t)) / 2
        out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * s, p0[2] + (p1[2] - p0[2]) * s))
    return out


def cam_conn(ref):
    x0, x1, y0, y1 = pbox(ref)
    return x1 - 0.5, (y0 + y1) / 2, (zb - 1.0 if PL["parts"][ref]["bottom"] else zt + 1.0)


mpz = MIRA_SENSOR_Z + 4.0
targets = {"J3": (rx - 31.8, ry, RB_Z + 5.0, "CAM0 cable: 22-way FPC, 100 ohm pairs, to the RGB adapter"),
           "J4": (MIRAS[0][0][0] - 14.9, MIRAS[0][0][1], mpz, "CAM1 cable: 22-way FPC to the red-edge module"),
           "J5": (MIRAS[1][0][0] - 14.9, MIRAS[1][0][1], mpz, "CAM2 cable: 22-way FPC to the NIR module"),
           "J6": (MIRAS[2][0][0] - 14.9, MIRAS[2][0][1], mpz, "CAM3 cable: 22-way FPC to the extended-NIR module")}
for ref, (tx_, ty_, tz_, lab) in targets.items():
    cx, cy, cz = cam_conn(ref)
    if ref in ("J5", "J6"):
        side = -W / 2 + 9.5 if ty_ < 0 else W / 2 - 9.5
        pts = [(cx, cy, cz), (cx + 3, cy, cz)] + scurve((cx + 3, cy, cz), (XC1 + 30, side, tz_), 10) + [(tx_ - 8, side, tz_), (tx_ - 0.5, ty_, tz_), (tx_ + 4, ty_, tz_)]
    else:
        pts = [(cx, cy, cz), (cx + 3, cy, cz)] + scurve((cx + 3, cy, cz), (tx_ - 2, ty_, tz_), 10) + [(tx_ + 4, ty_, tz_)]
    ribbon("fpc_" + ref, pts, 11.5, lab)

# ------------------------------------------------- top unit: DLS + GNSS antenna
TU = "DLS + GNSS top unit"
tx, ty, tz = 60.0, 0.0, 78.0
tb = cq.Workplane("XY").box(48, 48, 10).translate((tx, ty, tz + 5))
try:
    tb = tb.edges("|Z").fillet(8).faces(">Z").edges().fillet(2.5)
except Exception:
    pass
tu = tb.cut(cq.Workplane("XY").box(45, 45, 9).translate((tx, ty, tz + 5.8)))
tu_base = tu.intersect(box(0, 200, -60, 60, tz - 1, tz + 7.0))
tu_lid = tb.cut(cq.Workplane("XY").box(45.4, 45.4, 8.6).translate((tx, ty, tz + 4.0))).intersect(box(0, 200, -60, 60, tz + 7.0, tz + 12)) \
    .cut(cyl(tx + 10, ty, tz + 6, tz + 12, 6.2))
add("dls_housing", tu_base, ENC, TU, (0, 0, 30), density=1.01, label="Top-unit base (PA12)", mat="shell")
add("dls_pcb", cq.Workplane("XY").box(42, 42, 1.0).translate((tx, ty, tz + 2.6)), PCBK, TU, (0, 0, 44), mass=2.2, label="DLS board", mat="pcb")
add("dls_sensor", cbox(tx + 10, ty, tz + 3.1, tz + 4.0, 3.1, 2.0), (0.9, 0.9, 0.92), TU, (0, 0, 44), mass=0.0, label="Multi-band spectral sensor (AS7343)", mat="ceramic")
add("gnss_patch", cbox(tx - 10, ty, tz + 3.1, tz + 7.1, 18, 18), (0.86, 0.82, 0.70), TU, (0, 0, 58), mass=7.5, label="GNSS ceramic patch antenna 18 mm", mat="ceramic")
add("gnss_patch_top", cbox(tx - 10, ty, tz + 7.1, tz + 7.15, 14.5, 14.5), SIL, TU, (0, 0, 58), mass=0.0, label="Antenna electrode", mat="steel")
add("dls_diffuser", cyl(tx + 10, ty, tz + 5.0, tz + 10.0, 6.0).union(dome(tx + 10, ty, tz + 10.0, 6.0, 2.2, down=False)), (0.97, 0.97, 0.95), TU,
    (0, 0, 76), mass=0.6, label="PTFE cosine diffuser", mat="ptfe")
add("dls_lid", tu_lid, ENC, TU, (0, 0, 66), density=1.01, label="Top-unit lid", mat="shell")
add("harness", box(88, 96, 27, 33, -4.0, -3.0), (0.2, 0.2, 0.2), TU, (0, 0, 30), mass=9.0, label="GNSS coax + DLS cable to the top unit (0.4 m)", mat="rubber", proxy=True)
add("fasteners", cyl(POSTS[1][0], POSTS[1][1], zt, zt + 0.04, 2.7), GLD, "Enclosure", (0, 0, 32), mass=4.0,
    label="Remaining fasteners and threaded inserts (set)", mat="gold")

# ------------------------------------------------------------------- export
def tess(solid, tol, ang):
    shp = solid.val() if isinstance(solid, cq.Workplane) else solid
    v, t = shp.tessellate(tol, ang)
    pos = []
    for tri in t:
        for idx in tri:
            p = v[idx]
            pos += [p.x, p.y, p.z]
    return pos


meta, total = [], 0.0
asm = cq.Assembly(name="aviac_camera")
for p in parts:
    shp = p["solid"].val()
    vol = shp.Volume() / 1000.0
    mass = p["mass"] if p["mass"] is not None else vol * p["density"]
    total += mass
    coarse = p["mat"] == "shell" or p["name"].startswith(("brd_", "jetson_fingers")) or "_passives" in p["name"]
    pos = tess(p["solid"], 0.10 if coarse else 0.05, 0.35 if coarse else 0.22)
    b64 = base64.b64encode(struct.pack(f"<{len(pos)}f", *pos)).decode()
    bb = shp.BoundingBox()
    meta.append(dict(name=p["name"], label=p["label"], group=p["group"], color=p["color"], explode=p["explode"], mat=p["mat"], proxy=p["proxy"],
                     mass=round(mass, 2), estimated=p["mass"] is not None,
                     center=[round((bb.xmin + bb.xmax) / 2, 2), round((bb.ymin + bb.ymax) / 2, 2), round((bb.zmin + bb.zmax) / 2, 2)],
                     tris=len(pos) // 9, pos=b64))
    asm.add(p["solid"], name=p["name"], color=cq.Color(*p["color"]))

with open(os.path.join(OUT, "model.js"), "w") as f:
    f.write("window.AVIAC_MODEL=" + json.dumps(meta, separators=(",", ":")) + ";")
json.dump(dict(board_origin=[BX0, BW / 2, PCB_ZTOP - PCB_T], size=[XO1, W, -ZO]), open(os.path.join(OUT, "frame.json"), "w"))
with open(os.path.join(OUT, "parts.json"), "w") as f:
    json.dump([{k: m[k] for k in ("name", "label", "group", "mass", "estimated")} for m in meta if m["mass"] > 0], f, indent=1)
asm.save(os.path.join(OUT, "aviac_camera.step"))
for n in ("enclosure_upper", "enclosure_lower", "lens_plate"):
    s = next(p["solid"] for p in parts if p["name"] == n)
    cq.exporters.export(s, os.path.join(OUT, n + ".stl"), tolerance=0.05)
    cq.exporters.export(s, os.path.join(OUT, n + ".step"))
print("size", XO1, W, -ZO, "parts", len(meta), "tris", sum(m["tris"] for m in meta), "mass_g", round(total, 1))
by = {}
for m in meta:
    by[m["group"]] = by.get(m["group"], 0) + m["mass"]
for g, v in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"  {v:6.1f} g  {g}")
print("model.js MB", round(os.path.getsize(os.path.join(OUT, "model.js")) / 1e6, 2))
