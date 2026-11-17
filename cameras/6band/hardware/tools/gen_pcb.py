#!/usr/bin/python3
"""Generate the carrier PCB from design.py (run with the system python that ships pcbnew).

Stage 1 (this file): board outline, stack-up, rules, footprints with nets, placement.
Routing is done by route_pairs.py (differential pairs) and the autorouter afterwards.
"""
import math, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
from design import D, PROJECT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "carrier")
FPDIR = "/usr/share/kicad/footprints"
NS = uuid.UUID("6f1d2c1e-7c0a-4b62-9d3e-aa5a0c0ffee0")
OX, OY = 100.0, 60.0            # board origin on the page
BL, BW = 100.0, 82.0            # board size (module socket with latches is 78.2 mm wide)


def P(x, y):
    return VECTOR2I(FromMM(OX + x), FromMM(OY + y))


board = pcbnew.BOARD()
board.SetCopperLayerCount(6)
ds = board.GetDesignSettings()
ds.SetBoardThickness(FromMM(1.0))
ds.m_MinClearance = FromMM(0.09)
ds.m_TrackMinWidth = FromMM(0.09)
ds.m_ViasMinSize = FromMM(0.40)
ds.m_MinThroughDrill = FromMM(0.20)
ds.m_ViasMinAnnularWidth = FromMM(0.09)
ds.m_CopperEdgeClearance = FromMM(0.25)
ds.m_HoleToHoleMin = FromMM(0.20)
ds.m_HoleClearance = FromMM(0.15)
for lid, name in ((pcbnew.In1_Cu, "In1.GND"), (pcbnew.In2_Cu, "In2.SIG"), (pcbnew.In3_Cu, "In3.PWR"), (pcbnew.In4_Cu, "In4.GND")):
    pass   # default layer names kept so every tool understands the files

# ---------------------------------------------------------------- outline
def edge_line(x0, y0, x1, y1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x0, y0)); s.SetEnd(P(x1, y1)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1)); board.Add(s)


def edge_arc(cx, cy, sx, sy, ang):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1)); board.Add(s)


R = 2.0
edge_line(R, 0, BL - R, 0); edge_line(BL, R, BL, BW - R); edge_line(BL - R, BW, R, BW); edge_line(0, BW - R, 0, R)
edge_arc(R, R, 0, R, 90); edge_arc(BL - R, R, BL - R, 0, 90); edge_arc(BL - R, BW - R, BL, BW - R, 90); edge_arc(R, BW - R, R, BW, 90)

# ---------------------------------------------------------------- nets
nets = {}
for name in D.nets():
    ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni

# ---------------------------------------------------------------- footprints
def load(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(HERE, "..", "lib", "aviac.pretty") if lib == "aviac" else os.path.join(FPDIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


fps = {}
for ref, part in D.parts.items():
    fp = load(part.fp)
    fp.SetReference(ref); fp.SetValue(part.value)
    fp.SetPath(pcbnew.KIID_PATH("/" + str(uuid.uuid5(NS, f"sym/{ref}/1"))))
    for k, v in (("MPN", part.mpn), ("Manufacturer", part.mfr)):
        try:
            fp.SetField(k, v)
            fld = fp.GetFieldByName(k)
            if fld is not None:
                fld.SetVisible(False)
        except Exception:
            pass
    if part.dnp:
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    for pad in fp.Pads():
        net = part.pins.get(pad.GetNumber())
        if net and net != "NC":
            pad.SetNet(nets[net])
    board.Add(fp)
    fps[ref] = fp


def place(ref, x, y, rot=0, bottom=False):
    fp = fps[ref]
    fp.SetPosition(P(x, y))
    if bottom and not fp.IsFlipped():
        fp.Flip(P(x, y), False)
    fp.SetOrientationDegrees(rot)
    fp.SetLocked(False)


def pad_xy(ref, num):
    for pad in fps[ref].Pads():
        if pad.GetNumber() == str(num):
            p = pad.GetPosition()
            return ToMM(p.x) - OX, ToMM(p.y) - OY
    raise KeyError((ref, num))


# ---- Jetson socket on the underside: odd-pin row toward the rear (+x), pin 1 at low y
SX, SY = 66.0, 41.0
best = None
for rot in (90, -90, 270):
    place("J2", SX, SY, rot, bottom=True)
    x1, y1 = pad_xy("J2", 1); x2, y2 = pad_xy("J2", 2)
    if x1 > x2 and y1 < SY:
        best = rot; break
if best is None:
    raise SystemExit("could not orient J2")
JROT = best
x1, y1 = pad_xy("J2", 1); x2, y2 = pad_xy("J2", 2)
print(f"J2 rot {JROT}: pin1 ({x1:.2f},{y1:.2f}) pin2 ({x2:.2f},{y2:.2f}) pin259 {pad_xy('J2',259)} pin260 {pad_xy('J2',260)}")
ODD_X, EVEN_X = x1, x2
# module standoffs: 34.09 mm from the socket datum toward the nose, +/-31.8 mm
place("H1", SX - 34.09, SY - 31.8, 0)
place("H2", SX - 34.09, SY + 31.8, 0)

# ---- camera connectors at the rear edge. Each is placed so its signal pins line up with the socket pairs.
def pair_mid_y(a, b):
    return (pad_xy("J2", a)[1] + pad_xy("J2", b)[1]) / 2


CAMX = 93.4


def net_pad_xy(ref, net):
    for pad in fps[ref].Pads():
        if pad.GetNetname() == net:
            p = pad.GetPosition()
            return ToMM(p.x) - OX, ToMM(p.y) - OY
    raise KeyError((ref, net))


def place_cam(ref, bottom, cam, y_target):
    """Rotate so the cable opening faces +x and the D0 pair is at the low-y end, then slide D0 onto y_target."""
    ok = None
    for rot in (0, 90, 180, 270):
        place(ref, CAMX, 30, rot, bottom)
        d0 = net_pad_xy(ref, f"CAM{cam}_D0_N"); ck = net_pad_xy(ref, f"CAM{cam}_CLK_N"); sda = net_pad_xy(ref, f"CAM{cam}_SDA")
        bb = fps[ref].GetBoundingBox(False, False)
        cx = ToMM(bb.GetCenter().x) - OX
        if abs(d0[0] - ck[0]) < 0.01 and d0[1] < ck[1] < sda[1] and cx > d0[0]:
            ok = rot; break
    if ok is None:
        raise SystemExit("could not orient " + ref)
    y = (net_pad_xy(ref, f"CAM{cam}_D0_N")[1] + net_pad_xy(ref, f"CAM{cam}_D0_P")[1]) / 2
    pos = fps[ref].GetPosition()
    fps[ref].SetPosition(VECTOR2I(pos.x, pos.y + FromMM(y_target - y)))
    return ok


yA_odd = pair_mid_y(3, 5)        # CSI1_D0
yA_even = pair_mid_y(4, 6)       # CSI0_D0
PORT_PITCH = 17.5
r = {}
r["J4"] = place_cam("J4", True, 1, yA_odd)                    # CAM1 <- CSI1 (odd row, underside)
r["J6"] = place_cam("J6", True, 3, yA_odd + PORT_PITCH)       # CAM3 <- CSI3
r["J3"] = place_cam("J3", False, 0, yA_even)                  # CAM0 <- CSI0 (even row, top side)
r["J5"] = place_cam("J5", False, 2, yA_even + PORT_PITCH)     # CAM2 <- CSI2
print("camera connector rotations", r, "pads x", round(pad_xy("J3", 1)[0], 2))

# ---- fixed placements (x, y, rot, bottom)
FIX = {
    "H4": (3.5, 3.5, 0, False), "H5": (3.5, 72.5, 0, False), "H6": (96.5, 72.5, 0, False), "H7": (96.5, 40.5, 0, False),
    # power entry, left flank (+y edge in board coordinates)
    "J1": (14.0, 62.5, 180, False), "D1": (24.5, 71.5, 0, False), "Q1": (25.0, 62.5, 0, False), "U1": (32.5, 62.0, 0, False),
    "U2": (20.0, 52.0, 0, False), "L1": (9.0, 53.0, 0, False),
    "U3": (20.0, 40.0, 0, False), "L2": (9.5, 40.5, 0, False), "U4": (9.0, 30.5, 0, False),
    "J8": (43.0, 72.2, 0, False), "J9": (56.0, 72.2, 0, False), "U7": (44.0, 65.0, 0, False), "U8": (52.0, 65.5, 0, False),
    "Q2": (58.5, 66.0, 0, False), "D4": (49.5, 68.8, 0, False),
    "U6": (36.0, 28.0, 0, False), "Y1": (27.5, 24.0, 0, False), "J7": (27.0, 33.0, 0, False),
    "U9": (46.0, 12.0, 0, False), "J10": (55.5, 5.0, 0, False), "L3": (53.5, 10.5, 0, False),
    "U10": (46.0, 30.0, 0, False), "U12": (22.0, 12.0, 0, False),
    "J12": (66.0, 3.6, 180, False), "U11": (66.0, 11.5, 0, False),
    "J13": (76.5, 3.8, 180, False),
    "U5": (80.0, 42.5, 90, False),
    "J11": (89.0, 58.0, 270, False), "H3": (59.15, 58.0, 0, False),
    "SW1": (9.0, 4.5, 0, False), "SW2": (15.0, 4.5, 0, False), "D2": (21.0, 4.0, 0, False), "D3": (24.0, 4.0, 0, False),
    "J14": (40.0, 4.0, 90, False),
    "TP1": (4.0, 46.0, 0, False), "TP2": (4.0, 35.0, 0, False), "TP3": (4.0, 27.0, 0, False), "TP4": (4.0, 20.0, 0, False),
}
def yy(y):
    """The table above was drawn for a 76 mm board; the board is 82 mm: keep top-edge parts, shift the rest."""
    return y if y < 16 else (y + 6 if y > 60 else y + 3)


for ref, (x, y, rot, bot) in FIX.items():
    place(ref, x, yy(y), rot, bot)

# ---- automatic placement of the small parts next to the part they serve
def bbox(fp, margin=0.0):
    b = fp.GetBoundingBox(False, False)
    return (ToMM(b.GetLeft()) - OX - margin, ToMM(b.GetTop()) - OY - margin, ToMM(b.GetRight()) - OX + margin, ToMM(b.GetBottom()) - OY + margin)


occupied = []     # (x0,y0,x1,y1) on the top side
placed = set(FIX) | {"J2", "H1", "H2", "J3", "J4", "J5", "J6"}
for ref in placed:
    if not fps[ref].IsFlipped():
        occupied.append(bbox(fps[ref], 0.35))
    elif ref in ("H1", "H2"):
        occupied.append(bbox(fps[ref], 0.35))
# keep-outs on the top side: SSD body, board edge strip behind the camera connectors, socket peg holes
occupied += [(57.0, 49.5, 88.0, 72.5)]
for pad in fps["J2"].Pads():
    if pad.GetNumber() == "" or pad.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH):
        p = pad.GetPosition(); x, y = ToMM(p.x) - OX, ToMM(p.y) - OY
        occupied.append((x - 1.6, y - 1.6, x + 1.6, y + 1.6))
# reserve the corridor used by the top-side camera pairs (between socket and connectors)
occupied.append((EVEN_X - 6.0, 2.0, CAMX - 1.5, 2 * PORT_PITCH + 8.0))


def free(b):
    if b[0] < 1.2 or b[1] < 1.2 or b[2] > BL - 1.2 or b[3] > BW - 1.2:
        return False
    return not any(b[0] < o[2] and b[2] > o[0] and b[1] < o[3] and b[3] > o[1] for o in occupied)


POWER = {"GND", "+3V3", "+1V8", "VSYS", "VBAT", "VBAT_IN"}
BIG = [r_ for r_ in D.parts if r_ in placed]


def anchor_point(part):
    """Find the pad of an already-placed part that shares a (preferably signal) net with this part."""
    cands = []
    for pin, net in part.pins.items():
        if net in ("NC",):
            continue
        for oref in placed:
            if oref == part.ref:
                continue
            op = D.parts[oref]
            for opin, onet in op.pins.items():
                if onet == net:
                    score = (0 if net not in POWER else 2) + (0 if op.block == part.block else 1)
                    cands.append((score, oref, opin))
    if not cands:
        return None
    cands.sort()
    best = cands[0][0]
    # among equally good candidates prefer the same block's largest part
    c = [x for x in cands if x[0] == best][0]
    try:
        return pad_xy(c[1], c[2]), c[1]
    except KeyError:
        return None


order = [p for p in D.parts.values() if p.ref not in placed]
order.sort(key=lambda p: (0 if any(n not in POWER and n != "NC" for n in p.pins.values()) else 1, p.ref))
unplaced = []
for rounds in range(3):
    rest = []
    for part in order:
        a = anchor_point(part)
        if a is None:
            rest.append(part); continue
        (ax, ay), aref = a
        if fps[aref].IsFlipped() or aref == "J2":
            # anchor is underneath: stay near it but on the top side
            pass
        fp = fps[part.ref]
        done = False
        for radius in [i * 0.6 for i in range(2, 60)]:
            for k in range(max(8, int(radius * 6))):
                ang = 2 * math.pi * k / max(8, int(radius * 6))
                x, y = round((ax + radius * math.cos(ang)) / 0.1) * 0.1, round((ay + radius * math.sin(ang)) / 0.1) * 0.1
                for rot in (0, 90):
                    place(part.ref, x, y, rot)
                    b = bbox(fp, 0.22)
                    if free(b):
                        occupied.append(b); placed.add(part.ref); done = True; break
                if done:
                    break
            if done:
                break
        if not done:
            rest.append(part)
    order = rest
    if not order:
        break
print("unplaced:", [p.ref for p in order])

# reference designators: small, on the fab layer for the dense parts
for ref, fp in fps.items():
    t = fp.Reference()
    t.SetTextSize(VECTOR2I(FromMM(0.6), FromMM(0.6))); t.SetTextThickness(FromMM(0.1))
    if ref[0] in "RCLDFQYT":
        t.SetVisible(False)
    fp.Value().SetVisible(False)

# silkscreen title
txt = pcbnew.PCB_TEXT(board); txt.SetText("AVIAC 6-BAND CARRIER  REV A0"); txt.SetPosition(P(40, 48)); txt.SetLayer(pcbnew.F_SilkS)
txt.SetTextSize(VECTOR2I(FromMM(1.3), FromMM(1.3))); txt.SetTextThickness(FromMM(0.2)); board.Add(txt)

board.SetFileName(os.path.join(OUT, PROJECT + ".kicad_pcb"))
pcbnew.SaveBoard(os.path.join(OUT, PROJECT + ".kicad_pcb"), board)
import json
pl = {}
for ref, fp in fps.items():
    pos = fp.GetPosition()
    pl[ref] = dict(x=round(ToMM(pos.x) - OX, 3), y=round(ToMM(pos.y) - OY, 3), rot=fp.GetOrientationDegrees(),
                   bottom=bool(fp.IsFlipped()), bbox=[round(v, 3) for v in bbox(fp)])
json.dump(dict(board=[BL, BW], parts=pl), open(os.path.join(OUT, "placement.json"), "w"), indent=0)
print("footprints", len(fps), "nets", len(nets))
