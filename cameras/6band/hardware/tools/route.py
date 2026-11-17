#!/usr/bin/python3
"""Stage 2: planes, net classes, export to the autorouter, import the result, fill zones."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM
from design import D, PROJECT
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "carrier")
PCB = os.path.join(OUT, PROJECT + ".kicad_pcb")
OX, OY, BL, BW = 100.0, 60.0, 100.0, 82.0
FR = os.environ.get("FREEROUTING_JAR", "/tmp/claude-0/-home-user/98c65444-5e63-542e-8aef-e4be22683d99/scratchpad/ref/freerouting.jar")

PAIRS = [n[:-2] for n in D.nets() if n.endswith("_P") and (n[:-2] + "_N") in D.nets()]
HS = [n for n in D.nets() if n[:-2] in PAIRS]
POWER_W = {"VBAT_IN": 1.2, "VBAT": 1.2, "VSYS": 1.2, "VSYS_SW": 1.2, "P3V3_SW": 0.8, "+3V3": 0.5, "+1V8": 0.3, "GND": 0.3}

# ---- project file with net classes
pro_path = os.path.join(OUT, PROJECT + ".kicad_pro")
pro = json.load(open(pro_path)) if os.path.exists(pro_path) else {}
base = dict(bus_width=12, clearance=0.1, diff_pair_gap=0.15, diff_pair_via_gap=0.25, diff_pair_width=0.11, line_style=0,
            microvia_diameter=0.3, microvia_drill=0.1, pcb_color="rgba(0, 0, 0, 0.000)", schematic_color="rgba(0, 0, 0, 0.000)",
            track_width=0.13, via_diameter=0.45, via_drill=0.2, wire_width=6)
classes = [dict(base, name="Default")]
classes.append(dict(base, name="HS_100R", track_width=0.11, clearance=0.1))
for w in sorted(set(POWER_W.values())):
    classes.append(dict(base, name=f"PWR_{int(w*100):03d}", track_width=w, clearance=0.15, via_diameter=0.6, via_drill=0.3))
patterns = [dict(netclass="HS_100R", pattern=n) for n in HS] + [dict(netclass=f"PWR_{int(w*100):03d}", pattern=n) for n, w in POWER_W.items()]
pro["net_settings"] = dict(classes=classes, meta=dict(version=3), net_colors=None, netclass_assignments=None, netclass_patterns=patterns)
pro.setdefault("meta", dict(filename=PROJECT + ".kicad_pro", version=1))
json.dump(pro, open(pro_path, "w"), indent=2)

board = pcbnew.LoadBoard(PCB)
netcode = lambda n: board.FindNet(n)


def zone(net, layer, pts, prio=0, clearance=0.2, minw=0.15):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(netcode(net)); z.SetAssignedPriority(prio)
    z.SetLocalClearance(FromMM(clearance)); z.SetMinThickness(FromMM(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for (x, y) in pts:
        o.Append(FromMM(OX + x), FromMM(OY + y))
    board.Add(z); return z


full = [(0.3, 0.3), (BL - 0.3, 0.3), (BL - 0.3, BW - 0.3), (0.3, BW - 0.3)]
if not list(board.Zones()):
    zone("GND", pcbnew.In1_Cu, full)
    zone("GND", pcbnew.In4_Cu, full)
    zone("+3V3", pcbnew.In3_Cu, full)
pcbnew.SaveBoard(PCB, board)

if "--export" in sys.argv:
    dsn = os.path.join(OUT, "route.dsn")
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    print("DSN export", ok, os.path.getsize(dsn))
if "--import" in sys.argv:
    ses = os.path.join(OUT, "route.ses")
    ok = pcbnew.ImportSpecctraSES(board, ses)
    print("SES import", ok)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("tracks", len(board.GetTracks()))
