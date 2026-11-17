#!/usr/bin/env python3
"""Aviac MS - six-band multispectral crop camera, compact rugged box (CadQuery).

Replaces the long belly pod (build_model_pod.py, kept for reference) with one machined block you can hold in
one hand: four cameras in a centred 2 x 2 grid, all lens fronts on one plane, the Jetson flipped against a
finned lid, no fan and no duct.

Body: 6061-T6 aluminium, machined from solid, Type III hard anodised (gunmetal), bead-blasted. Rubber corner
guards, a skid rim that keeps the windows off the ground when the box is set down face first, grip grooves,
rubber port covers, captive stainless screws.

Optics: Sony IMX565 on a 16 mm C-mount lens (RGB) plus three Mira220 modules on 6 mm CS-mount lenses (red edge,
NIR, extended NIR), all screwed into one machined lens plate, windows flush on one face.

Frame: X forward, Y left-right, Z up; Z=0 is the window face. Units: mm. Board geometry from
boards/orin-carrier/kicad/placement.json (6band variant: all four camera ports).

Outputs (./out): aviac_6b.step, body/lid/lens_plate/yoke/qr_plate .stl+.step, model.js, frame.json, parts.json
"""
import base64, json, math, os, random, struct, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
random.seed(13)
REPO = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(REPO, "boards", "orin-carrier"))
sys.path.insert(0, os.path.join(REPO, "toolkit", "kicad"))
from variants import VARIANTS
UNFITTED = set(VARIANTS["6band"])
PL = json.load(open(os.path.join(REPO, "boards", "orin-carrier", "kicad", "placement.json")))
BL, BW = PL["board"]

# ----------------------------------------------------------------- parameters
T = 3.0                        # wall, machined aluminium
X0, X1 = -6.0, 106.0           # outer box, X
YW = 54.0                      # outer half width
CX = (X0 + X1) / 2             # the camera grid is centred on the box
LID_T, FIN_H, FIN_T, FIN_P = 3.0, 9.0, 1.4, 4.4
BX0 = 0.0                      # board x=0 at model X
BOARD_LOW = 75.0               # carrier's downward face, clear of the RGB sensor board and its adapter
BOARD_UP = BOARD_LOW + 1.0
P = 20.0                       # half pitch of the camera grid: lens centres 40 mm apart
LENS_FRONT = 4.0
RGB = (CX - P, P)
MIRAS = [((CX + P, P), "Red edge", "RE", (0.62, 0.05, 0.08), "717-730 nm bandpass", "J4"),
         ((CX - P, -P), "NIR", "NIR", (0.33, 0.03, 0.12), "830-850 nm bandpass", "J5"),
         ((CX + P, -P), "Extended NIR", "XNIR", (0.16, 0.02, 0.10), "860-920 nm bandpass", "J6")]
C_LEN, C_FLANGE = 38.0, 17.526         # 16 mm C-mount lens for the 1.1-inch IMX565
CS_LEN, CS_FLANGE = 30.0, 12.526       # 6 mm CS-mount lens for the Mira220
CS_FLANGE_Z = LENS_FRONT + CS_LEN
SENSOR_Z = CS_FLANGE_Z + CS_FLANGE
MOD_Z = SENSOR_Z + 1.0
C_FLANGE_Z = LENS_FRONT + C_LEN
RGB_SENSOR_Z = C_FLANGE_Z + C_FLANGE
RB_Z = RGB_SENSOR_Z + 1.7 + 1.6        # top face of the RGB sensor board
GUN = (0.20, 0.205, 0.215)             # hard-anodised gunmetal

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
add("carrier_pcb", flip(pcb), PCBG, CB, EXB, mass=16.5, label="Carrier PCB, 100 x 82 mm, 6-layer (all four camera ports)", mat="pcb", proxy=True)
HEIGHT = {"J1": 5.0, "J8": 4.25, "J9": 4.25, "J13": 4.25, "J12": 3.2, "J3": 2.0, "J4": 2.0, "J5": 2.0, "J6": 2.0, "J11": 4.1, "U9": 2.5,
          "L1": 5.8, "L2": 3.1, "J10": 1.3, "Y1": 0.7, "SW1": 1.6, "SW2": 1.6, "Q1": 1.0, "U6": 1.4}
NAMES = {"J1": "XT30 power input", "J8": "TELEM connector (MAVLink)", "J9": "Trigger / spray-on input", "J13": "Light-sensor port",
         "J12": "USB-C (flashing, data)", "J11": "M.2 Key-M socket", "U9": "GNSS receiver", "U6": "Sync MCU",
         "J3": "CAM0 FPC connector (RGB)", "J4": "CAM1 FPC connector (red edge)", "J5": "CAM2 FPC connector (NIR)", "J6": "CAM3 FPC connector (ext. NIR)"}
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

# ---------------------------------------------------------------- body: machined from one block
RC = 8.0
outer = rbox(X0, X1, -YW, YW, 0, H, RC)
try:
    outer = outer.faces("<Z").edges().fillet(2.5)
except Exception:
    pass
body = outer.cut(rbox(X0 + T, X1 - T, -YW + T, YW - T, T, H + 1, RC - T))
# machined parting groove under the lid
body = body.cut(box(X0 - 1, X1 + 1, -YW - 1, YW + 1, H - 6.8, H - 6.0).cut(rbox(X0 + 0.6, X1 - 0.6, -YW + 0.6, YW - 0.6, H - 8, H - 4, RC - 0.6)))
# grip grooves on both long sides, clear of the pivot bosses
for s in (-1, 1):
    for z in (14.0, 20.0, 26.0):
        for (xa, xb) in ((X0 + 14, CX - 14), (CX + 14, X1 - 14)):
            g = box(xa, xb, s * YW - 0.7 if s > 0 else -YW - 1, s * YW + 1 if s > 0 else -YW + 0.7, z, z + 1.6)
            body = body.cut(g)
# window face: one raised plate carries all four windows, recessed behind the skid rim
WR = {"rgb": 17.5, "mira": 13.0}
WINS = [(RGB, WR["rgb"])] + [(m[0], WR["mira"]) for m in MIRAS]
body = body.union(rbox(CX - 43, CX + 43, -43, 43, -1.4, 0.4, 14.0))
for (cx, cy), r in WINS:
    body = body.cut(cyl(cx, cy, -3, T + 1, r))
    body = body.cut(ring(cx, cy, -1.6, -0.9, r + 3.4, r))
# connector openings from the real board
OPEN = []
for ref, h in (("J1", 5.6), ("J8", 4.6), ("J9", 4.6), ("J12", 3.6), ("J13", 4.6)):
    x0, x1, y0, y1 = pbox(ref, 0.6)
    y0, y1 = fy(y1), fy(y0)
    zlo, zhi = BOARD_LOW - h, BOARD_LOW + 0.4
    side = 1 if y1 > 0 else -1
    body = body.cut(box(x0, x1, YW - T - 1, YW + 1, zlo, zhi) if side > 0 else box(x0, x1, -YW - 1, -YW + T + 1, zlo, zhi))
    OPEN.append((x0, x1, zlo, zhi, side, ref))
# lid screw bosses hang from the wall top (they must clear the RGB sensor board below)
LIDSCREWS = [(X0 + 7.0, -YW + 7.0), (X0 + 7.0, YW - 7.0), (X1 - 7.0, -YW + 7.0), (X1 - 7.0, YW - 7.0)]
for (x, y) in LIDSCREWS:
    body = body.union(cyl(x, y, H - 14, H, 3.6).intersect(outer)).cut(cyl(x, y, H - 12, H + 1, 1.25))
# carrier posts also hang from the end walls, on webs, above the sensor boards
for (x, y) in POSTS:
    yy = fy(y)
    wx0, wx1 = (X0 + 1, x) if x < CX else (x, X1 - 1)
    body = body.union(box(wx0, wx1, yy - 2.0, yy + 2.0, BOARD_LOW - 9, BOARD_LOW).intersect(outer))
    body = body.union(cyl(x, yy, BOARD_LOW - 9, BOARD_LOW, 2.8)).cut(cyl(x, yy, BOARD_LOW - 8, BOARD_LOW + 1, 1.25))
PIV_Z = H * 0.55
for s in (-1, 1):
    body = body.union(cq.Workplane("XZ").circle(9.0).extrude(1.6).translate((CX, s * YW + (1.6 if s > 0 else 0), PIV_Z)))
body = body.cut(cq.Workplane("YZ").center(0, H - 16).rect(12, 1.6).extrude(-3).translate((X1 + 0.5, 0, 0)))
add("body", body, GUN, "Enclosure", (0, 0, -100), density=2.70,
    label="Body, 6061-T6 machined from solid, Type III hard anodised, bead-blasted", mat="hardcoat")
add("status_bar", cbox(X1 - 1.2, 0, H - 16.8, H - 15.2, 0.6, 11.6), (1.0, 0.55, 0.12), "Enclosure", (0, 0, -100), mass=0.0,
    label="Status light", mat="emit")
# skid rim: stainless, keeps the windows 2.5 mm off a table or the ground
rim = rbox(X0 + 1.0, X1 - 1.0, -YW + 1.0, YW - 1.0, -3.4, 0.01, RC - 1.0).cut(rbox(X0 + 6.0, X1 - 6.0, -YW + 6.0, YW - 6.0, -4, 1, RC - 5.0))
add("skid_rim", rim, (0.6, 0.6, 0.62), "Enclosure", (0, 0, -150), density=7.9, label="Skid rim, 316 stainless: the windows never touch the ground", mat="steel_brushed")
# rubber corner guards on the four vertical edges
shell = rbox(X0 - 1.8, X1 + 1.8, -YW - 1.8, YW + 1.8, 2.0, H - 9.0, RC + 1.8).cut(outer)
for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
    cxn, cyn = (X0 if sx < 0 else X1), (-YW if sy < 0 else YW)
    corner = shell.intersect(box(cxn - 20, cxn + 20, cyn - 20, cyn + 20, 0, H))
    add(f"bumper_{i}", corner, (0.035, 0.035, 0.038), "Enclosure", (sx * 18, sy * 18, -100), density=1.2,
        label="Corner guard, overmoulded TPU", mat="rubberised")
# rubber port covers over the connector openings
for i, (x0, x1, zlo, zhi, side, ref) in enumerate(OPEN):
    y0 = YW if side > 0 else -YW - 1.4
    add(f"port_cover_{i}", rbox(x0 - 2, x1 + 2, y0, y0 + 1.4, zlo - 2, zhi + 2, 0.6).edges("|Y").fillet(0.6) if False else box(x0 - 2, x1 + 2, y0, y0 + 1.4, zlo - 2, zhi + 2),
        (0.035, 0.035, 0.038), "Enclosure", (0, side * 14, -100), mass=1.0, label="Port cover, silicone, tethered", mat="rubberised")


# ---------------------------------------------------------------- markings: laser-etched through the anodise (reads light grey)
sys.path.insert(0, os.path.join(REPO, "toolkit", "brand"))
from logo import polygons as logo_polygons
ETCH = 0.06


def face_place(sol, face, at):
    """Text and art are drawn in XY (x right, y up, extruded +z); turn them onto a face so they read from outside."""
    if face == "+X":
        sol = sol.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    elif face == "-X":
        sol = sol.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), -90)
    elif face == "+Y":
        sol = sol.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 180)
    elif face == "-Y":
        sol = sol.rotate((0, 0, 0), (1, 0, 0), 90)
    elif face == "-Z":                          # the window face, read from below with the nose (+X) up
        sol = sol.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 0, 1), 90)
    return sol.translate(at)


def etched_text(txt, size, face, at, kind="bold", halign="center"):
    t = cq.Workplane("XY").text(txt, size, ETCH + 0.02, kind=kind, halign=halign, valign="center").translate((0, 0, -0.02))
    return face_place(t, face, at)


def etched_logo(height, face, at):
    k = height / 420.0                          # the mark spans y 120..540 in artwork space
    sol = None
    for poly in logo_polygons():
        pts = [((x - 300) * k, (330 - y) * k) for (x, y) in poly]
        w = cq.Workplane("XY").polyline(pts).close().extrude(ETCH + 0.02).translate((0, 0, -0.02))
        sol = w if sol is None else sol.union(w)
    return face_place(sol, face, at)


marks = []
# nose face: the mark, the name, the line
marks.append(etched_logo(24.0, "+X", (X1, 0, H * 0.58)))
marks.append(etched_text("AVIAC  MS", 7.2, "+X", (X1, 0, H * 0.33)))
marks.append(etched_text("MULTISPECTRAL  ·  6 BAND", 2.6, "+X", (X1, 0, H * 0.25), kind="regular"))
# rear face: identification plate
marks.append(etched_text("AVIAC MS-6   REV B", 3.0, "-X", (X0, 0, H * 0.42)))
marks.append(etched_text("S/N  MS6-0001   ·   3S - 6S  25 W MAX", 2.2, "-X", (X0, 0, H * 0.35), kind="regular"))
marks.append(etched_text("MADE IN INDIA", 2.2, "-X", (X0, 0, H * 0.29), kind="regular"))
# both flanks: product name and a flight-direction arrow
for face, sy in (("+Y", YW), ("-Y", -YW)):
    marks.append(etched_text("AVIAC MS", 4.2, face, (CX + (24 if sy > 0 else -24), sy, 34.0)))
    marks.append(etched_text("FWD  →" if sy < 0 else "←  FWD", 3.0, face, (CX + (24 if sy > 0 else -24), sy, 40.0), kind="regular"))
# port labels above the openings
PORTN = {"J1": "PWR 3-6S", "J8": "TELEM", "J9": "TRIG", "J12": "USB-C", "J13": "DLS"}
for (x0, x1, zlo, zhi, side, ref) in OPEN:
    face = "+Y" if side > 0 else "-Y"
    marks.append(etched_text(PORTN[ref], 2.2, face, ((x0 + x1) / 2, side * YW, zhi + 4.2)))
# window face: a band label beside each window, on the raised window plate
for ((mx, my), r, lab) in [(RGB, WR["rgb"], "RGB")] + [(m[0], WR["mira"], {"RE": "RE 723", "NIR": "NIR 840", "XNIR": "NIR+ 890"}[m[2]]) for m in MIRAS]:
    sx, sy = (1 if mx > CX else -1), (1 if my > 0 else -1)
    off = r * 0.78 + 3.2
    marks.append(etched_text(lab, 2.3, "-Z", (mx + sx * off, my + sy * off, -1.4)))
etch = marks[0]
for m in marks[1:]:
    etch = etch.union(m)
add("markings", etch, (0.72, 0.73, 0.75), "Enclosure", (0, 0, -100), mass=0.0, label="Laser-etched markings: Aviac mark, name, ports, bands", mat="etch")

# ---------------------------------------------------------------- finned lid: the heatsink
lid = rbox(X0, X1, -YW, YW, H, H + LID_T, RC)
fins = None
y = -YW + 5.0
while y + FIN_T < YW - 5.0:
    f = box(X0 + 5, X1 - 5, y, y + FIN_T, H + LID_T - 0.01, H + LID_T + FIN_H)
    fins = f if fins is None else fins.union(f)
    y += FIN_P
fins = fins.intersect(rbox(X0 + 5.5, X1 - 5.5, -YW + 5.5, YW - 5.5, H, H + LID_T + FIN_H + 1, RC - 5.5))
try:
    fins = fins.faces(">Z").edges("|X").chamfer(0.4)
except Exception:
    pass
lid = lid.union(fins)
for (x, y) in LIDSCREWS:
    lid = lid.cut(cyl(x, y, H - 1, H + LID_T + FIN_H + 1, 1.4)).cut(cyl(x, y, H + LID_T - 1.0, H + LID_T + FIN_H + 1, 3.8))
add("lid", lid, (0.62, 0.63, 0.65), TH, (0, 0, 80), density=2.70, label="Finned lid, 6063 aluminium, machined, bead-blasted: the heatsink", mat="alu")
for i, (x, y) in enumerate(LIDSCREWS):
    hd = cyl(x, y, H + LID_T - 1.0, H + LID_T + 1.4, 2.7).cut(cq.Workplane("XY").polygon(6, 2.0).extrude(1.6).translate((x, y, H + LID_T + 0.2)))
    add(f"lid_screw_{i}", hd, (0.7, 0.7, 0.72), TH, (0, 0, 100), mass=0.5, label="Captive M2.5 screw, stainless", mat="steel")
add("gasket", rbox(X0 + 0.8, X1 - 0.8, -YW + 0.8, YW - 0.8, H - 0.2, H, RC - 0.8).cut(rbox(X0 + 2.0, X1 - 2.0, -YW + 2.0, YW - 2.0, H - 1, H + 1, RC - 2.0)),
    (0.85, 0.30, 0.08), "Enclosure", (0, 0, 34), mass=1.2, label="Silicone gasket (IP65 target)", mat="rubber")

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


# ---------------------------------------------------------------- optics
OPT = "RGB camera (IMX565)"
rx, ry = RGB
rgb_pcb = cbox(rx, ry, RB_Z - 1.6, RB_Z, 62.7, 58.7)
RGB_POSTS = [(rx + dx, ry + dy) for (dx, dy) in ((-28, -25), (-28, 25), (28, -25), (28, 25))]
for (px, py) in RGB_POSTS:
    rgb_pcb = rgb_pcb.cut(cyl(px, py, RB_Z - 3, RB_Z + 1, 1.3))
add("rgb_sensor_pcb", rgb_pcb, (0.02, 0.03, 0.025), OPT, (0, 0, 26), mass=9.0, label="CHC5 IMX565 sensor board (59 x 63 mm)", mat="pcb")
add("rgb_sensor_pkg", cbox(rx, ry, RB_Z - 1.6 - 1.7, RB_Z - 1.6, 20.0, 16.8), (0.07, 0.07, 0.08), OPT, (0, 0, 20), mass=0.0, label="Sony IMX565 package", mat="ceramic_dark")
add("rgb_b2b", cbox(rx + 22, ry, RB_Z, RB_Z + 3.0, 2.6, 22.0), BEIGE, OPT, (0, 0, 26), mass=0.0, label="100-pin board-to-board connector", mat="plastic_gloss")
add("rgb_adapter", cbox(rx + 24, ry, RB_Z + 3.0, RB_Z + 4.0, 16, 26), PCBG, OPT, (0, 0, 36), mass=1.6, label="IMX565 adapter: 2-lane MIPI to 22-pin FPC", mat="pcb")
add("rgb_adapter_fpc", box(rx + 26.4, rx + 31.6, ry - 7.6, ry + 7.6, RB_Z + 4.0, RB_Z + 6.0), BEIGE, OPT, (0, 0, 36), mass=0.25, label="22-pin FPC connector", mat="plastic_gloss")
rsc = None
for k in range(40):
    px, py = rx + random.uniform(-28, 28), ry + random.uniform(-26, 26)
    if abs(px - rx) < 11 and abs(py - ry) < 9 or abs(px - (rx + 23)) < 10 and abs(py - ry) < 14 or any(abs(px - qx) < 3 and abs(py - qy) < 3 for qx, qy in RGB_POSTS):
        continue
    b = cbox(round(px, 1), round(py, 1), RB_Z, RB_Z + 0.6, 1.0, 0.5)
    rsc = b if rsc is None else rsc.union(b)
add("rgb_passives", rsc, (0.62, 0.50, 0.36), OPT, (0, 0, 26), mass=0.0, label="Decoupling capacitors", mat="ceramic")
add("rgb_ircut", cbox(rx, ry, RGB_SENSOR_Z - 5.6, RGB_SENSOR_Z - 5.0, 22, 19), (0.45, 0.85, 0.90), OPT, (0, 0, 14), mass=0.9, label="IR-cut filter, 400-680 nm", mat="filter")
lens("rgb_lens", rx, ry, 16.5, C_LEN, LENS_FRONT, OPT, (0, 0, -40), "16 mm C-mount lens, 1.1-inch format, 12 MP", 62.0, 10.5, (0.20, 0.10, 0.32))
add("rgb_window", cyl(rx, ry, 0.4, 1.4, WR["rgb"] + 0.4), (0.80, 0.90, 0.95), OPT, (0, 0, -120), mass=2.6, label="Window, sapphire, AR coated", mat="window")
add("rgb_bezel", ring(rx, ry, -1.55, -0.95, WR["rgb"] + 3.2, WR["rgb"] - 0.6), (0.85, 0.42, 0.08), OPT, (0, 0, -136), mass=1.2, label="Window retaining ring", mat="accent")

MPOSTS = []
for i, ((mx, my), band, key, bc, flabel, port) in enumerate(MIRAS):
    g = f"{band} camera (Mira220)"
    mp = cbox(mx, my, MOD_Z, MOD_Z + 1.0, 30, 24)
    posts = [(mx + dx, my + dy) for (dx, dy) in ((-12.5, -9.5), (-12.5, 9.5), (12.5, -9.5), (12.5, 9.5))]
    MPOSTS += posts
    for (px, py) in posts:
        mp = mp.cut(cyl(px, py, MOD_Z - 1, MOD_Z + 2, 1.05))
    add(f"mira{i}_pcb", mp, PCBG, g, (0, 0, -4), mass=2.4, label="Mira220 module (30 x 24 mm, trigger on pin 18)", mat="pcb")
    add(f"mira{i}_sensor", cbox(mx, my, SENSOR_Z, MOD_Z, 6.6, 6.2), (0.06, 0.06, 0.07), g, (0, 0, -8), mass=0.0, label="ams OSRAM Mira220 (mono)", mat="ceramic_dark")
    add(f"mira{i}_fpc_conn", box(mx + 9.6, mx + 14.8, my - 7.6, my + 7.6, MOD_Z + 1.0, MOD_Z + 3.0), BEIGE, g, (0, 0, -4), mass=0.0, label="22-pin FPC connector", mat="plastic_gloss")
    mpas = None
    for k in range(14):
        px, py = mx + random.uniform(-10, 6), my + random.uniform(-9, 9)
        b = cbox(round(px, 1), round(py, 1), MOD_Z + 1.0, MOD_Z + 1.5, 1.0, 0.5)
        mpas = b if mpas is None else mpas.union(b)
    add(f"mira{i}_passives", mpas, (0.62, 0.50, 0.36), g, (0, 0, -4), mass=0.0, label="Module regulators", mat="ceramic")
    lens(f"mira{i}_lens", mx, my, 13.5, CS_LEN, LENS_FRONT, g, (0, 0, -40), "6 mm CS-mount lens, 1/2.7-inch", 22.0, 7.0, (0.30, 0.08, 0.20))
    add(f"mira{i}_window", cyl(mx, my, 0.4, 1.4, WR["mira"] + 0.4), (0.80, 0.90, 0.95), g, (0, 0, -120), mass=1.2, label="Window, sapphire, AR coated", mat="window")
    add(f"mira{i}_filter", cyl(mx, my, -1.4, -0.5, WR["mira"] - 0.2), bc, g, (0, 0, -128), mass=0.9, label=flabel, mat="bandpass")
    add(f"mira{i}_bezel", ring(mx, my, -1.55, -0.95, WR["mira"] + 3.2, WR["mira"] - 0.6), (0.85, 0.42, 0.08), g, (0, 0, -136), mass=0.8, label="Filter retaining ring", mat="accent")

# lens plate: four lens threads and four sensor boards on one machined part; every band is registered here
lp = rbox(CX - 44, CX + 44, -YW + T + 0.6, YW - T - 0.6, CS_FLANGE_Z, CS_FLANGE_Z + 3.5, 6.0)
for (mx, my), *_ in MIRAS:
    lp = lp.cut(cyl(mx, my, CS_FLANGE_Z - 1, CS_FLANGE_Z + 5, 12.0))
    lp = lp.union(ring(mx, my, CS_FLANGE_Z + 3.49, SENSOR_Z - 1.2, 14.5, 12.0))
lp = lp.cut(cyl(rx, ry, CS_FLANGE_Z - 1, CS_FLANGE_Z + 5, 16.8))
lp = lp.union(ring(rx, ry, CS_FLANGE_Z + 3.49, C_FLANGE_Z + 6.0, 19.8, 16.8))      # C-mount turret
for (px, py) in MPOSTS:
    lp = lp.union(ring(px, py, CS_FLANGE_Z + 3.49, MOD_Z, 2.0, 0.8))
for (px, py) in RGB_POSTS:
    lp = lp.union(ring(px, py, CS_FLANGE_Z + 3.49, RB_Z - 1.6, 2.2, 0.9))
for (x, y) in ((CX - 41, -46), (CX - 41, 46), (CX + 41, -46), (CX + 41, 46)):
    lp = lp.cut(cyl(x, y, CS_FLANGE_Z - 1, CS_FLANGE_Z + 5, 1.4))
add("lens_plate", lp, (0.05, 0.05, 0.055), "Optics bench", (0, 0, -18), density=2.70,
    label="Lens plate, machined aluminium: 1 x C-mount + 3 x CS-mount, 40 mm grid", mat="anodised")
for i, (px, py) in enumerate(MPOSTS + RGB_POSTS):
    zt_ = MOD_Z + 1.0 if i < len(MPOSTS) else RB_Z
    add(f"post_screw_{i}", cyl(px, py, zt_, zt_ + 1.2, 1.6), (0.10, 0.10, 0.11), "Optics bench", (0, 0, -4), mass=0.15, label="Sensor-board screw", mat="steel_black")

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


XE = X1 - T - 1.2
TARGETS = [("J3", rx + 29.0, ry, RB_Z + 6.0, RB_Z + 7.5, "CAM0 cable to the RGB adapter")]
for i, ((mx, my), band, key, bc, flabel, port) in enumerate(MIRAS):
    TARGETS.append((port, mx + 12.2, my, MOD_Z + 3.0, MOD_Z + 4.5 + (3.5 if mx < CX else 0.0), f"{port.replace('J', 'CAM')} cable to the {band.lower()} module"))
for k, (ref, tx, ty, tz, zc, lab) in enumerate(TARGETS):
    cx, cy, cz = conn(ref)
    xe = XE - 0.5 * k
    pts = [(cx, cy, cz), (xe - 1.0, cy, cz)] + scurve((xe - 1.0, cy, cz), (xe, cy, cz - 3.0), 4)[1:] + \
          [(xe, cy, zc + 2.0)] + scurve((xe, cy, zc + 2.0), (max(tx + 6.0, xe - 14.0), ty, zc), 8)[1:] + [(tx + 0.5, ty, zc), (tx, ty, tz)]
    ribbon("fpc_" + ref, pts, 11.5, lab)

# ---------------------------------------------------------------- tilt yoke and quick-release plate
MG = "Mount"
TOPZ = H + LID_T + FIN_H + 12.0
ARM_T = 4.0
yoke = None
for s in (-1, 1):
    y0 = YW + 1.6 if s > 0 else -(YW + 1.6 + ARM_T)
    arm = (cq.Workplane("XZ").moveTo(CX - 11, PIV_Z).lineTo(CX + 11, PIV_Z).lineTo(CX + 18, TOPZ).lineTo(CX - 18, TOPZ).close()
           .extrude(-ARM_T).translate((0, y0, 0)))
    arm = arm.union(cq.Workplane("XZ").circle(11.0).extrude(-ARM_T).translate((CX, y0, PIV_Z)))
    try:
        arm = arm.edges("|Y").fillet(1.5)
    except Exception:
        pass
    arm = arm.cut(cq.Workplane("XZ").circle(2.6).extrude(-ARM_T - 2).translate((CX, y0 + 1, PIV_Z)))
    arm = arm.cut(cq.Workplane("XZ").center(CX, PIV_Z).circle(16.5).circle(14.5).extrude(-ARM_T - 2).translate((0, y0 + 1, 0))
                  .intersect(box(CX - 30, CX - 2, -80, 80, PIV_Z + 4, PIV_Z + 30)))
    yoke = arm if yoke is None else yoke.union(arm)
yoke = yoke.union(rbox(CX - 18, CX + 18, -(YW + 1.6 + ARM_T), YW + 1.6 + ARM_T, TOPZ, TOPZ + 5.0, 3.0))
add("yoke", yoke, GUN, MG, (0, 0, 110), density=2.70, label="Tilt yoke, 7075 aluminium, hard anodised", mat="hardcoat")
for s in (-1, 1):
    yk = YW + 1.6 + ARM_T + 0.01 if s > 0 else -(YW + 1.6 + ARM_T + 0.01)
    knob = cq.Workplane("XZ").circle(9.0).extrude(-5.5 if s > 0 else 5.5).translate((CX, yk, PIV_Z))
    for k in range(16):
        a = 2 * math.pi * k / 16
        knob = knob.cut(cq.Workplane("XZ").circle(1.1).extrude(-5.7 if s > 0 else 5.7).translate((CX + 9.4 * math.cos(a), yk, PIV_Z + 9.4 * math.sin(a))))
    add(f"tilt_knob_{s}", knob, (0.85, 0.42, 0.08), MG, (0, s * 18, 110), mass=3.5, label="Tilt lock knob, anodised orange", mat="accent")
# quick-release: a dovetail plate on the yoke slides into a receiver bolted to the airframe
qz0 = TOPZ + 5.0
qr = rbox(CX - 30, CX + 30, -26, 26, qz0, qz0 + 4.0, 3.0)
qr = qr.union(cq.Workplane("YZ").polyline([(-20, qz0 + 4.0), (20, qz0 + 4.0), (16, qz0 + 9.0), (-16, qz0 + 9.0)]).close().extrude(60).translate((CX - 30, 0, 0)))
QR_TOP = qz0 + 9.0
add("qr_plate", qr, GUN, MG, (0, 0, 132), density=2.70, label="Quick-release dovetail plate", mat="hardcoat")
rcv = rbox(CX - 34, CX + 34, -30, 30, QR_TOP - 5.5, QR_TOP + 3.0, 3.0).cut(
    cq.Workplane("YZ").polyline([(-20.4, qz0 + 3.9), (20.4, qz0 + 3.9), (16.4, QR_TOP + 0.01), (-16.4, QR_TOP + 0.01)]).close().extrude(80).translate((CX - 40, 0, 0))).cut(
    box(CX - 40, CX + 40, -21, 21, qz0, qz0 + 4.0))
add("qr_receiver", rcv, (0.06, 0.06, 0.065), MG, (0, 0, 150), density=2.70, label="Quick-release receiver (stays on the aircraft)", mat="anodised")
lever = box(CX + 34, CX + 37, 6, 34, QR_TOP - 3, QR_TOP + 1.5)
add("qr_lever", lever, (0.85, 0.42, 0.08), MG, (0, 0, 150), mass=4.0, label="Release lever", mat="accent")
PZ = QR_TOP + 3.0
add("airframe", rbox(CX - 120, CX + 120, -85, 85, PZ, PZ + 2.0, 10.0), (0.02, 0.02, 0.025), "Drone", (0, 0, 175), mass=0.0,
    label="Airframe belly plate (not part of the camera)", mat="cfrp")
# DLS + GNSS puck on top of the aircraft: sunlight in the same bands, and the antenna
TU = "DLS + GNSS top unit"
tz = PZ + 2.0
add("dls_base", cyl(CX - 60, 0, tz, tz + 9.0, 24.0).edges(">Z").fillet(3.0), GUN, TU, (0, 0, 200), density=2.70, label="Top unit body, hard anodised", mat="hardcoat")
add("dls_diffuser", cyl(CX - 60, 0, tz + 9.0, tz + 11.0, 14.0).union(dome(CX - 60, 0, tz + 11.0, 14.0, 4.0, down=False)), (0.97, 0.97, 0.95), TU, (0, 0, 212),
    mass=3.0, label="Cosine diffuser over the spectral sensor", mat="paper")
add("dls_ring", ring(CX - 60, 0, tz + 8.9, tz + 9.6, 18.0, 14.0), (0.85, 0.42, 0.08), TU, (0, 0, 206), mass=0.5, label="Retaining ring", mat="accent")

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
asm = cq.Assembly(name="aviac_6b")
for p in parts:
    shp = p["solid"].val()
    vol = shp.Volume() / 1000.0
    mass = p["mass"] if p["mass"] is not None else vol * p["density"]
    if p["group"] != "Drone":
        total += mass
    coarse = p["name"].startswith(("brd_", "jetson_passives", "markings")) or "_passives" in p["name"]
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
for old in ("aviac_camera.step", "enclosure_upper.stl", "enclosure_upper.step", "enclosure_lower.stl", "enclosure_lower.step", "heatsink.stl"):
    if os.path.exists(os.path.join(OUT, old)):
        os.remove(os.path.join(OUT, old))
asm.save(os.path.join(OUT, "aviac_6b.step"))
for n in ("body", "lid", "lens_plate", "yoke", "qr_plate", "bumper_0", "skid_rim"):
    s = next(p["solid"] for p in parts if p["name"] == n)
    cq.exporters.export(s, os.path.join(OUT, n + ".stl"), tolerance=0.05)
    cq.exporters.export(s, os.path.join(OUT, n + ".step"))
print(f"box {X1 - X0:.0f} x {2 * YW:.0f} x {H + LID_T + FIN_H:.1f} mm, with mount {QR_TOP:.0f} mm tall; parts {len(meta)}; mass {total:.0f} g")
by = {}
for m in meta:
    if m["group"] != "Drone":
        by[m["group"]] = by.get(m["group"], 0) + m["mass"]
for g, v in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"  {v:6.1f} g  {g}")
