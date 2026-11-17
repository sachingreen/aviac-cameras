#!/usr/bin/env python3
"""Aviac Duo - compact sealed box for spray drones (CadQuery).

One box, no fan, no air duct: the Jetson module presses on a finned aluminium lid through a thermal pad,
and rotor downwash cools the lid. Two Mira220 cameras look down through hydrophobic windows, 60 mm
apart, centred under the board on one machined lens plate. Both cameras sit on the box's centre line, under the board. A tilting yoke clamps the box to a
20-25 mm carbon tube.

Frame: X forward, Y left-right, Z up; Z=0 is the underside of the box (the windows). Units: mm.
The carrier is the shared Orin Nano board (duo variant) mounted socket-side up, so the module sits
against the lid. Board geometry comes from boards/orin-carrier/kicad/placement.json.

Outputs (./out): aviac_duo.step, body/lid/lens_plate .stl+.step, model.js, frame.json, parts.json
"""
import base64, json, math, os, random, struct, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
random.seed(11)
REPO = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(REPO, "boards", "orin-carrier"))
sys.path.insert(0, os.path.join(REPO, "toolkit", "kicad"))
from variants import VARIANTS
UNFITTED = set(VARIANTS["duo"])
PL = json.load(open(os.path.join(REPO, "boards", "orin-carrier", "kicad", "placement.json")))
BL, BW = PL["board"]

# ----------------------------------------------------------------- parameters
T = 2.2                        # wall
X0, X1 = -3.0, 105.0           # outer box, X
YW = 49.0                      # outer half width
CX = (X0 + X1) / 2             # the cameras sit on the box's centre line
LID_T, FIN_H, FIN_T, FIN_P = 2.6, 8.0, 1.3, 4.2
BX0 = 1.0                      # board x=0 at model X
BOARD_LOW = 54.0               # carrier's downward face (connectors, SSD, camera ports)
BOARD_UP = BOARD_LOW + 1.0     # upward face (Jetson socket side)
BASE = 60.0                    # stereo baseline
CAMS = [((CX, -BASE / 2), "A", (0.30, 0.12, 0.42), "Dual-band filter, visible + 850 nm (RGB-IR sensor)"),
        ((CX, BASE / 2), "B", (0.62, 0.05, 0.08), "Twist-lock filter, swappable (mono sensor)")]
LENS_FRONT = 4.0
CS_LEN, CS_FLANGE = 26.0, 12.526       # compact 4 mm CS lens
FLANGE_Z = LENS_FRONT + CS_LEN
SENSOR_Z = FLANGE_Z + CS_FLANGE
MOD_Z = SENSOR_Z + 1.0                 # Mira module PCB underside

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


def rbox(x0, x1, y0, y1, z0, z1, r):
    s = box(x0, x1, y0, y1, z0, z1)
    try:
        s = s.edges("|Z").fillet(r)
    except Exception:
        pass
    return s


BLK, SIL, GLD = (0.03, 0.03, 0.035), (0.72, 0.73, 0.75), (0.83, 0.62, 0.20)
PCBG, BEIGE = (0.02, 0.20, 0.10), (0.80, 0.77, 0.68)

# ---------------------------------------------------------------- board frame: build top-side-up, then flip
# In the board frame the carrier's top face is z=0, its bottom face z=-1 (as on the 6-band camera).
# flip(): rotate 180 deg about X and lift, so the top face lands at BOARD_LOW and the socket side faces up.
def b2m(bx, by):
    return BX0 + bx, BW / 2 - by


def pbox(ref, pad=0.0):
    b = PL["parts"][ref]["bbox"]
    xa, ya = b2m(b[0], b[1]); xb, yb = b2m(b[2], b[3])
    return min(xa, xb) - pad, max(xa, xb) + pad, min(ya, yb) - pad, max(ya, yb) + pad


def flip(s):
    return s.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, BOARD_LOW))


def fy(y):            # board-frame Y -> model Y after the flip
    return -y


zt, zb = 0.0, -1.0
CB, JG, TH = "Carrier board", "Jetson Orin Nano", "Thermal"
EXB = (0, 0, 32)
POSTS = [b2m(PL["parts"][r]["x"], PL["parts"][r]["y"]) for r in ("H4", "H5", "H6", "H7")]
pcb = box(BX0, BX0 + BL, -BW / 2, BW / 2, zb, zt)
for (x, y) in POSTS:
    pcb = pcb.cut(cyl(x, y, zb - 1, zt + 1, 1.35))
pcb = pcb.edges("|Z").fillet(2.0)
add("carrier_pcb", flip(pcb), PCBG, CB, EXB, mass=16.5, label="Carrier PCB, 100 x 82 mm, 6-layer (duo variant)", mat="pcb", proxy=True)
HEIGHT = {"J1": 5.0, "J8": 4.25, "J9": 4.25, "J13": 4.25, "J12": 3.2, "J3": 2.0, "J4": 2.0, "J11": 4.1, "U9": 2.5,
          "L1": 5.8, "L2": 3.1, "J10": 1.3, "Y1": 0.7, "SW1": 1.6, "SW2": 1.6, "Q1": 1.0, "U6": 1.4}
NAMES = {"J1": "XT30 power input", "J8": "TELEM connector (MAVLink)", "J9": "Trigger / spray-on input", "J13": "Light-sensor port",
         "J12": "USB-C (flashing, data)", "J11": "M.2 Key-M socket", "U9": "GNSS receiver", "U6": "Sync MCU",
         "J3": "CAM0 FPC connector (camera A)", "J4": "CAM1 FPC connector (camera B)"}
NO3D = {"J1", "J11", "U9"}
caps = res = None
for ref, p in PL["parts"].items():
    if ref[0] in "HT" or ref in ("J2", "J7", "J14") or ref in UNFITTED:
        continue
    x0, x1, y0, y1 = pbox(ref, -0.25)
    if x1 - x0 < 0.3 or y1 - y0 < 0.3:
        continue
    small = max(x1 - x0, y1 - y0) < 2.4
    h = HEIGHT.get(ref, {"U": 1.2, "C": 0.55 if small else 1.7, "R": 0.35, "F": 0.6, "D": 0.5 if small else 2.2, "Q": 0.9, "L": 0.6}.get(ref[0], 1.0))
    z0, z1 = (zb - h, zb) if p["bottom"] else (zt, zt + h)
    s = flip(box(x0, x1, y0, y1, z0, z1))
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
        add("brd_" + ref, s, col, CB, EXB, mass=0.0, label=NAMES.get(ref, ref), mat=mat, proxy=ref not in NO3D)
add("brd_caps", caps, (0.62, 0.50, 0.36), CB, EXB, mass=0.0, label="Ceramic capacitors", mat="ceramic", proxy=True)
add("brd_res", res, (0.05, 0.05, 0.06), CB, EXB, mass=0.0, label="Resistors", mat="ic", proxy=True)
add("brd_bom_mass", flip(cyl(POSTS[0][0], POSTS[0][1], zt, zt + 0.04, 2.7)), GLD, CB, EXB, mass=11.0, label="Board components (BOM)", mat="gold")
sx0, sx1, sy0, sy1 = pbox("J11")
hx, hy = b2m(PL["parts"]["H3"]["x"], PL["parts"]["H3"]["y"])
scy = (sy0 + sy1) / 2
add("m2_ssd", flip(box(hx - 1.5, sx0 + 2.0, scy - 11, scy + 11, zt + 1.6, zt + 2.4)), PCBG, CB, EXB, mass=2.6, label="M.2 2230 NVMe SSD", mat="pcb")
add("m2_ssd_ctrl", flip(box(hx + 12, hx + 23, scy - 7.5, scy + 7.5, zt + 2.4, zt + 3.4)), BLK, CB, EXB, mass=0.3, label="NVMe controller", mat="ic")
# module socket, standoffs, module, SoC
sock = PL["parts"]["J2"]
SOCK_X, _ = b2m(sock["x"], sock["y"])
MOD_X1 = SOCK_X + 7.98
MOD_X0 = MOD_X1 - 45.0
sk = box(SOCK_X - 0.5, SOCK_X + 14.0, -37.0, 37.0, zb - 6.5, zb).cut(box(SOCK_X - 1, SOCK_X + 8.4, -34.9, 34.9, zb - 4.6, zb - 3.0))
add("sodimm_socket", flip(sk), (0.08, 0.08, 0.09), CB, EXB, mass=3.4, label="260-pin SO-DIMM socket", mat="plastic_gloss")
STAND = [b2m(PL["parts"][r]["x"], PL["parts"][r]["y"]) for r in ("H1", "H2")]
for i, (x, y) in enumerate(STAND):
    add(f"standoff_{i}", flip(cyl(x, y, zb - 6.5, zb, 2.5)), SIL, CB, EXB, mass=0.5, label="Module standoff", mat="steel")
mz = zt - 1.0 - 6.5
mod = box(MOD_X0, MOD_X1, -34.8, 34.8, mz - 1.2, mz)
for (x, y) in STAND:
    mod = mod.cut(cyl(x, y, mz - 2, mz + 1, 1.4))
EXJ = (0, 0, 52)
add("jetson_pcb", flip(mod), (0.02, 0.10, 0.06), JG, EXJ, mass=60.0, label="Jetson Orin Nano 8GB module", mat="pcb")
uz = mz - 1.2
add("jetson_soc", flip(cbox(MOD_X0 + 22, -6, uz - 2.8, uz, 25, 25)), (0.60, 0.61, 0.63), JG, EXJ, mass=0.0, label="Orin SoC thermal plate", mat="alu")
add("jetson_ram", flip(cbox(MOD_X0 + 22, 22, uz - 1.1, uz, 14, 11.5)), BLK, JG, EXJ, mass=0.0, label="LPDDR5 8 GB", mat="ic")
jc = None
for k in range(80):
    x, y = MOD_X0 + random.uniform(3, 42), random.uniform(-32, 32)
    if abs(x - (MOD_X0 + 22)) < 14 and abs(y + 6) < 14:
        continue
    b = cbox(round(x, 1), round(y, 1), uz - 0.5, uz, 1.0, 0.5) if k % 2 else cbox(round(x, 1), round(y, 1), uz - 0.5, uz, 0.5, 1.0)
    jc = b if jc is None else jc.union(b)
add("jetson_passives", flip(jc), (0.62, 0.50, 0.36), JG, EXJ, mass=0.0, label="Module decoupling", mat="ceramic")
SOC_TOP = BOARD_LOW - (uz - 2.8)            # after the flip
LID_Z = SOC_TOP + 0.5                       # thermal pad 0.5 mm
H = LID_Z                                   # body height: the lid sits on the Jetson through the pad
socx, socy = MOD_X0 + 22, fy(-6)
add("tim_pad", cbox(socx, socy, SOC_TOP, LID_Z, 25, 25), (0.55, 0.60, 0.68), TH, (0, 0, 70), mass=0.8, label="Thermal pad, 0.5 mm, 6 W/mK", mat="rubber")

# ---------------------------------------------------------------- body: one sealed box
RC = 9.0
outer = rbox(X0, X1, -YW, YW, 0, H, RC)
try:
    outer = outer.faces("<Z").edges().fillet(3.0)
except Exception:
    pass
body = outer.cut(rbox(X0 + T, X1 - T, -YW + T, YW - T, T, H + 1, RC - T))
# a shallow groove 6 mm under the lid: reads as a machined parting line
body = body.cut(box(X0 - 1, X1 + 1, -YW - 1, YW + 1, H - 6.6, H - 5.8).cut(rbox(X0 + 0.5, X1 - 0.5, -YW + 0.5, YW - 0.5, H - 8, H - 4, RC - 0.5)))
# underside: one raised bezel plate carries both windows
WIN_R = 13.0
bez = rbox(CX - 19, CX + 19, -YW + 3.5, YW - 3.5, -1.4, 0.4, 18.0)
body = body.union(bez)
for (cx, cy), *_ in CAMS:
    body = body.cut(cyl(cx, cy, -3, T + 1, WIN_R))
    body = body.cut(ring(cx, cy, -1.6, -0.9, WIN_R + 3.4, WIN_R))
# connector openings, from the real board, on whichever flank each connector faces
for ref, h in (("J1", 5.6), ("J8", 4.6), ("J9", 4.6), ("J12", 3.6), ("J13", 4.6)):
    x0, x1, y0, y1 = pbox(ref, 0.6)
    y0, y1 = fy(y1), fy(y0)
    zlo, zhi = BOARD_LOW - h, BOARD_LOW + 0.4
    if y1 > 0:
        body = body.cut(box(x0, x1, YW - T - 1, YW + 1, zlo, zhi))
    else:
        body = body.cut(box(x0, x1, -YW - 1, -YW + T + 1, zlo, zhi))
LIDSCREWS = [(X0 + 6.5, -YW + 6.5), (X0 + 6.5, YW - 6.5), (X1 - 6.5, -YW + 6.5), (X1 - 6.5, YW - 6.5)]
for (x, y) in LIDSCREWS:
    body = body.union(cyl(x, y, T, H, 3.4).intersect(outer)).cut(cyl(x, y, T + 2, H + 1, 1.25))
for (x, y) in POSTS:
    yy = fy(y)
    body = body.union(cyl(x, yy, T, BOARD_LOW, 2.6)).cut(cyl(x, yy, T + 3, BOARD_LOW + 1, 1.25))
PIV_Z = H * 0.52
for s in (-1, 1):
    body = body.union(cq.Workplane("XZ").circle(8.0).extrude(1.4).translate((CX, s * YW + (1.4 if s > 0 else 0), PIV_Z)))
try:
    body = body.cut(cq.Workplane("YZ").text("AVIAC  DUO", 6.0, -0.45, kind="bold").translate((X1, 0, H * 0.45)))
except Exception as e:
    print("logo skipped", e)
body = body.cut(cq.Workplane("YZ").center(0, H - 13).rect(10, 1.6).extrude(-3).translate((X1 + 0.5, 0, 0)))   # status light bar
add("body", body, (0.10, 0.105, 0.115), "Enclosure", (0, 0, -92), density=1.20,
    label="Body, glass-filled nylon, IP65 with the lid gasket", mat="shell")
add("status_bar", cbox(X1 - 1.2, 0, H - 13.8, H - 12.2, 0.6, 9.6), (1.0, 0.55, 0.12), "Enclosure", (0, 0, -92), mass=0.0,
    label="Status light", mat="emit")

# ---------------------------------------------------------------- finned lid: the heatsink, machined aluminium
lid = rbox(X0, X1, -YW, YW, H, H + LID_T, RC)
fins = None
y = -YW + 4.5
while y + FIN_T < YW - 4.5:
    f = box(X0 + 4, X1 - 4, y, y + FIN_T, H + LID_T - 0.01, H + LID_T + FIN_H)
    fins = f if fins is None else fins.union(f)
    y += FIN_P
fins = fins.intersect(rbox(X0 + 4.5, X1 - 4.5, -YW + 4.5, YW - 4.5, H, H + LID_T + FIN_H + 1, RC - 4.5))
lid = lid.union(fins)
for (x, y) in LIDSCREWS:
    lid = lid.cut(cyl(x, y, H - 1, H + LID_T + FIN_H + 1, 1.4)).cut(cyl(x, y, H + LID_T - 0.8, H + LID_T + FIN_H + 1, 3.6))
add("lid", lid, (0.62, 0.63, 0.65), TH, (0, 0, 74), density=2.70, label="Finned lid, 6063 aluminium, bead-blasted: the heatsink", mat="alu")
for i, (x, y) in enumerate(LIDSCREWS):
    hd = cyl(x, y, H + LID_T - 0.8, H + LID_T + 1.2, 2.5).cut(cq.Workplane("XY").polygon(6, 2.0).extrude(1.5).translate((x, y, H + LID_T - 0.1)))
    add(f"lid_screw_{i}", hd, (0.08, 0.08, 0.09), TH, (0, 0, 92), mass=0.4, label="M2.5 lid screw", mat="steel_black")
add("gasket", rbox(X0 + 0.6, X1 - 0.6, -YW + 0.6, YW - 0.6, H - 0.2, H, RC - 0.6).cut(rbox(X0 + 1.6, X1 - 1.6, -YW + 1.6, YW - 1.6, H - 1, H + 1, RC - 1.6)),
    (0.85, 0.30, 0.08), "Enclosure", (0, 0, 30), mass=1.0, label="Silicone gasket (IP65)", mat="rubber")

# ---------------------------------------------------------------- optics
def lens(prefix, x, y, r_body, length, z_front, group, ex, label, mass, r_glass, tint):
    """Machine-vision lens pointing down (-Z): barrel, two knurled rings, front retainer, glass."""
    z_rear = z_front + length
    barrel = cyl(x, y, z_front + 1.0, z_rear, r_body - 1.0)
    barrel = barrel.union(cyl(x, y, z_front, z_front + 6.0, r_body))
    barrel = barrel.union(cyl(x, y, z_rear - 3.0, z_rear, r_body - 0.2))
    barrel = barrel.cut(cyl(x, y, z_front - 1, z_front + 3.6, r_glass + 0.9))
    add(prefix + "_barrel", barrel, (0.025, 0.025, 0.03), group, ex, mass=mass, label=label, mat="anodised")
    rings = None
    for (za, zb_) in ((z_front + 8.0, z_front + 13.0), (z_front + 15.5, z_front + 20.0)):
        r = cyl(x, y, za, zb_, r_body + 0.6)
        for k in range(40):
            a = 2 * math.pi * k / 40
            px, py = x + (r_body + 0.75) * math.cos(a), y + (r_body + 0.75) * math.sin(a)
            r = r.cut(cbox(px, py, za + 0.5, zb_ - 0.5, 0.9, 0.9).rotate((px, py, 0), (px, py, 1), math.degrees(a)))
        rings = r if rings is None else rings.union(r)
    add(prefix + "_rings", rings, (0.045, 0.045, 0.05), group, ex, mass=0.0, label="Focus and iris rings", mat="rubberised")
    add(prefix + "_retainer", ring(x, y, z_front + 0.2, z_front + 1.2, r_glass + 2.4, r_glass + 0.2), (0.75, 0.55, 0.20), group, ex, mass=0.0,
        label="Front retaining ring", mat="gold")
    add(prefix + "_glass", dome(x, y, z_front + 3.6, r_glass + 0.85, r_glass * 0.33), tint, group, ex, mass=0.0, label="Front element", mat="lens")
    add(prefix + "_iris", cyl(x, y, z_front + 6.0, z_front + 6.2, r_glass * 0.9), (0.01, 0.01, 0.012), group, ex, mass=0.0, label="Aperture", mat="black")


MPOSTS = []
for i, ((mx, my), key, bc, flabel) in enumerate(CAMS):
    g = f"Camera {key} (Mira220)"
    mp = cbox(mx, my, MOD_Z, MOD_Z + 1.0, 30, 24)
    posts = [(mx + dx, my + dy) for (dx, dy) in ((-12.5, -9.5), (-12.5, 9.5), (12.5, -9.5), (12.5, 9.5))]
    MPOSTS += posts
    for (px, py) in posts:
        mp = mp.cut(cyl(px, py, MOD_Z - 1, MOD_Z + 2, 1.05))
    add(f"mira{i}_pcb", mp, PCBG, g, (0, 0, -4), mass=2.4, label="Mira220 module (30 x 24 mm, trigger on pin 18)", mat="pcb")
    add(f"mira{i}_sensor", cbox(mx, my, SENSOR_Z, MOD_Z, 6.6, 6.2), (0.06, 0.06, 0.07), g, (0, 0, -8), mass=0.0, label="ams OSRAM Mira220", mat="ceramic_dark")
    add(f"mira{i}_fpc_conn", box(mx + 9.6, mx + 14.8, my - 7.6, my + 7.6, MOD_Z + 1.0, MOD_Z + 3.0), BEIGE, g, (0, 0, -4), mass=0.0,
        label="22-pin FPC connector", mat="plastic_gloss")
    mpas = None
    for k in range(14):
        px, py = mx + random.uniform(-10, 6), my + random.uniform(-9, 9)
        b = cbox(round(px, 1), round(py, 1), MOD_Z + 1.0, MOD_Z + 1.5, 1.0, 0.5)
        mpas = b if mpas is None else mpas.union(b)
    add(f"mira{i}_passives", mpas, (0.62, 0.50, 0.36), g, (0, 0, -4), mass=0.0, label="Module regulators", mat="ceramic")
    lens(f"mira{i}_lens", mx, my, 13.5, CS_LEN, LENS_FRONT, g, (0, 0, -34), "4 mm CS-mount lens, 58 deg, 1/2.7-inch", 18.0, 7.0, (0.30, 0.08, 0.20))
    add(f"mira{i}_window", cyl(mx, my, 0.4, 1.4, WIN_R + 0.4), (0.80, 0.90, 0.95), g, (0, 0, -112), mass=1.2,
        label="Window, hydrophobic + AR coated: spray mist beads off", mat="window")
    add(f"mira{i}_filter", cyl(mx, my, -1.4, -0.5, WIN_R - 0.2), bc, g, (0, 0, -124), mass=0.9, label=flabel, mat="bandpass")
    bz = ring(mx, my, -1.55, -0.95, WIN_R + 3.2, WIN_R - 0.6)
    if key == "B":                                     # twist-lock tabs: the user changes this filter in the field
        for a in (30, 150, 270):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            bz = bz.union(cbox(mx + (WIN_R + 3.4) * ca, my + (WIN_R + 3.4) * sa, -1.9, -0.95, 3.0, 3.0))
    add(f"mira{i}_bezel", bz, (0.85, 0.42, 0.08), g, (0, 0, -132), mass=0.8, label="Filter retaining ring" + (", twist-lock" if key == "B" else ""), mat="accent")

# lens plate: both CS threads and both sensor boards in one machined part (the stereo calibration lives here)
lp = rbox(CX - 21, CX + 21, -YW + T + 0.6, YW - T - 0.6, FLANGE_Z, FLANGE_Z + 3.5, 6.0)
for (cx, cy), *_ in CAMS:
    lp = lp.cut(cyl(cx, cy, FLANGE_Z - 1, FLANGE_Z + 5, 12.0))
    lp = lp.union(ring(cx, cy, FLANGE_Z + 3.49, SENSOR_Z - 1.2, 14.5, 12.0))
for (px, py) in MPOSTS:
    lp = lp.union(ring(px, py, FLANGE_Z + 3.49, MOD_Z, 2.0, 0.8))
lp = lp.cut(rbox(CX - 14, CX + 14, -9, 9, FLANGE_Z + 1.2, FLANGE_Z + 4, 3.0))
for (x, y) in ((CX - 17, -42), (CX - 17, 42), (CX + 17, -42), (CX + 17, 42)):
    lp = lp.cut(cyl(x, y, FLANGE_Z - 1, FLANGE_Z + 5, 1.4))
add("lens_plate", lp, (0.05, 0.05, 0.055), "Optics bench", (0, 0, -18), density=2.70,
    label=f"Lens plate, machined aluminium, 2 x CS-mount, {BASE:.0f} mm baseline", mat="anodised")
for i, (px, py) in enumerate(MPOSTS):
    add(f"post_screw_{i}", cyl(px, py, MOD_Z + 1.0, MOD_Z + 2.2, 1.6), (0.10, 0.10, 0.11), "Optics bench", (0, 0, -4), mass=0.15,
        label="Sensor-board screw", mat="steel_black")

# ---------------------------------------------------------------- flat cables: down the end of the board to the cameras
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
    add(name, sol, (0.80, 0.42, 0.05), "FPC cables", (0, 0, 8), mass=0.6, label=label, mat="fpc")


def scurve(p0, p1, n=9):
    out = []
    for k in range(n + 1):
        t = k / n
        s = (1 - math.cos(math.pi * t)) / 2
        out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * s, p0[2] + (p1[2] - p0[2]) * s))
    return out


def conn(ref):
    x0, x1, y0, y1 = pbox(ref)
    face = BOARD_UP + 1.0 if PL["parts"][ref]["bottom"] else BOARD_LOW - 1.0
    return x1 - 0.5, fy((y0 + y1) / 2), face


XE = X1 - T - 1.2                       # cables drop down the end wall, past the board edge
for ref, (i, lab) in (("J3", (0, "CAM0 cable to camera A")), ("J4", (1, "CAM1 cable to camera B"))):
    cx, cy, cz = conn(ref)
    (mx, my), *_ = CAMS[i]
    zc = MOD_Z + 2.0 + 0.5 * i
    xe = XE - 0.6 * i
    pts = [(cx, cy, cz), (xe - 1.0, cy, cz)] + scurve((xe - 1.0, cy, cz), (xe, cy, cz - 3.0), 4)[1:] + \
          [(xe, cy, zc + 2.0)] + scurve((xe, cy, zc + 2.0), (mx + 18.0, my, zc), 8)[1:] + [(mx + 11.5, my, zc)]
    ribbon("fpc_" + ref, pts, 11.5, lab)

# ---------------------------------------------------------------- tilt yoke and tube clamp (fits any drone with a 20-25 mm tube)
MG = "Mount"
TOPZ = H + LID_T + FIN_H + 12.0
ARM_T = 3.2
yoke = None
for s in (-1, 1):
    y0 = s * (YW + 1.6) if s > 0 else -(YW + 1.6 + ARM_T)
    arm = (cq.Workplane("XZ").moveTo(CX - 10, PIV_Z).lineTo(CX + 10, PIV_Z).lineTo(CX + 15, TOPZ).lineTo(CX - 15, TOPZ).close()
           .extrude(-ARM_T).translate((0, y0, 0)))
    arm = arm.union(cq.Workplane("XZ").circle(10.0).extrude(-ARM_T).translate((CX, y0, PIV_Z)))
    try:
        arm = arm.edges("|Y").fillet(1.2)
    except Exception:
        pass
    arm = arm.cut(cq.Workplane("XZ").circle(2.6).extrude(-ARM_T - 2).translate((CX, y0 + 1, PIV_Z)))
    arm = arm.cut(cq.Workplane("XZ").center(CX, PIV_Z).circle(15.5).circle(13.5).extrude(-ARM_T - 2).translate((0, y0 + 1, 0))
                  .intersect(box(CX - 30, CX - 2, -80, 80, PIV_Z + 4, PIV_Z + 30)))
    yoke = arm if yoke is None else yoke.union(arm)
bridge = rbox(CX - 15, CX + 15, -(YW + 1.6 + ARM_T), YW + 1.6 + ARM_T, TOPZ, TOPZ + 4.0, 3.0)
yoke = yoke.union(bridge)
add("yoke", yoke, (0.08, 0.08, 0.09), MG, (0, 0, 104), density=2.70, label="Tilt yoke, 0-35 deg back, aluminium", mat="anodised")
for s in (-1, 1):
    yk = s * (YW + 1.6 + ARM_T + 0.01) if s > 0 else -(YW + 1.6 + ARM_T + 0.01)
    knob = cq.Workplane("XZ").circle(8.5).extrude(-5.0 if s > 0 else 5.0).translate((CX, yk, PIV_Z))
    for k in range(14):
        a = 2 * math.pi * k / 14
        knob = knob.cut(cq.Workplane("XZ").circle(1.1).extrude(-5.2 if s > 0 else 5.2)
                        .translate((CX + 8.9 * math.cos(a), yk, PIV_Z + 8.9 * math.sin(a))))
    add(f"tilt_knob_{s}", knob, (0.85, 0.42, 0.08), MG, (0, s * 16, 104), mass=3.0, label="Tilt lock knob", mat="accent")
TUBE_R = 12.5
cz = TOPZ + 4.0 + TUBE_R + 1.0
clamp = rbox(CX - 12, CX + 12, -26, 26, TOPZ + 4.0, cz, 2.0).union(
    cq.Workplane("YZ").circle(TUBE_R + 5).extrude(24).translate((CX - 12, 0, cz)).intersect(box(CX - 12, CX + 12, -40, 40, TOPZ + 4.0, cz)))
clamp = clamp.cut(cq.Workplane("YZ").circle(TUBE_R).extrude(30).translate((CX - 15, 0, cz)))
cap = cq.Workplane("YZ").circle(TUBE_R + 5).circle(TUBE_R).extrude(24).translate((CX - 12, 0, cz)).intersect(box(CX - 12, CX + 12, -40, 40, cz + 0.6, cz + 30))
cap = cap.union(box(CX - 12, CX + 12, -TUBE_R - 11, -TUBE_R - 1, cz + 0.6, cz + 4)).union(box(CX - 12, CX + 12, TUBE_R + 1, TUBE_R + 11, cz + 0.6, cz + 4))
clamp = clamp.union(box(CX - 12, CX + 12, -TUBE_R - 11, -TUBE_R - 1, cz - 4, cz)).union(box(CX - 12, CX + 12, TUBE_R + 1, TUBE_R + 11, cz - 4, cz))
add("clamp_base", clamp, (0.08, 0.08, 0.09), MG, (0, 0, 124), density=2.70, label="Tube clamp, fits 20 / 22 / 25 mm with inserts", mat="anodised")
add("clamp_cap", cap, (0.08, 0.08, 0.09), MG, (0, 0, 146), density=2.70, label="Tube clamp cap", mat="anodised")
for s in (-1, 1):
    add(f"clamp_screw_{s}", cyl(CX, s * (TUBE_R + 6), cz + 4, cz + 6.5, 2.6), (0.6, 0.6, 0.62), MG, (0, 0, 156), mass=1.0, label="M3 clamp screw", mat="steel")
tube = cq.Workplane("XZ").circle(TUBE_R - 0.05).extrude(-180).translate((CX, -90, cz))
add("drone_tube", tube, (0.02, 0.02, 0.025), "Drone", (0, 0, 146), mass=0.0, label="Drone frame tube, 25 mm carbon (not part of the camera)", mat="cfrp")

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
asm = cq.Assembly(name="aviac_duo")
for p in parts:
    shp = p["solid"].val()
    vol = shp.Volume() / 1000.0
    mass = p["mass"] if p["mass"] is not None else vol * p["density"]
    if p["group"] != "Drone":
        total += mass
    coarse = p["name"].startswith(("brd_", "jetson_passives")) or "_passives" in p["name"]
    pos = tess(p["solid"], 0.10 if coarse else 0.04, 0.35 if coarse else 0.2)
    bb = shp.BoundingBox()
    meta.append(dict(name=p["name"], label=p["label"], group=p["group"], color=p["color"], explode=p["explode"], mat=p["mat"], proxy=p["proxy"],
                     mass=round(mass, 2), estimated=p["mass"] is not None,
                     center=[round((bb.xmin + bb.xmax) / 2, 2), round((bb.ymin + bb.ymax) / 2, 2), round((bb.zmin + bb.zmax) / 2, 2)],
                     tris=len(pos) // 9, pos=base64.b64encode(struct.pack(f"<{len(pos)}f", *pos)).decode()))
    asm.add(p["solid"], name=p["name"], color=cq.Color(*p["color"]))
with open(os.path.join(OUT, "model.js"), "w") as f:
    f.write("window.AVIAC_MODEL=" + json.dumps(meta, separators=(",", ":")) + ";")
# the renderer places the KiCad board export: flipped, with its top face at BOARD_LOW
json.dump(dict(board_origin=[BX0, BW / 2, BOARD_UP], flip=True, size=[X1 - X0, 2 * YW, H + LID_T + FIN_H]), open(os.path.join(OUT, "frame.json"), "w"))
with open(os.path.join(OUT, "parts.json"), "w") as f:
    json.dump([{k: m[k] for k in ("name", "label", "group", "mass", "estimated")} for m in meta if m["mass"] > 0 and m["group"] != "Drone"], f, indent=1)
for old in ("aviac_camera.step", "enclosure_upper.stl", "enclosure_upper.step", "enclosure_lower.stl", "enclosure_lower.step"):
    if os.path.exists(os.path.join(OUT, old)):
        os.remove(os.path.join(OUT, old))
asm.save(os.path.join(OUT, "aviac_duo.step"))
for n in ("body", "lid", "lens_plate", "yoke", "clamp_base", "clamp_cap"):
    s = next(p["solid"] for p in parts if p["name"] == n)
    cq.exporters.export(s, os.path.join(OUT, n + ".stl"), tolerance=0.05)
    cq.exporters.export(s, os.path.join(OUT, n + ".step"))
print(f"box {X1 - X0:.0f} x {2 * YW:.0f} x {H + LID_T + FIN_H:.1f} mm, with mount {cz + TUBE_R + 5:.0f} mm tall; parts {len(meta)}; mass {total:.0f} g")
by = {}
for m in meta:
    if m["group"] != "Drone":
        by[m["group"]] = by.get(m["group"], 0) + m["mass"]
for g, v in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"  {v:6.1f} g  {g}")
