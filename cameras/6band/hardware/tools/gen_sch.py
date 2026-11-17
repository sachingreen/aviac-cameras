#!/usr/bin/env python3
"""Generate the KiCad 8 schematic from design.py.

Style: one large sheet, one framed block per function. Every pin gets a short stub
and a net label, so connectivity is explicit and identical to the netlist that
drives the PCB. Unused pins carry no-connect flags.
"""
import math, os, sys, uuid, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import Sym, dumps, find, first
import kilib
from design import D, PROJECT, TITLE, REV
from jetson_pins import PINS as JPINS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "carrier")
os.makedirs(OUT, exist_ok=True)
NS = uuid.UUID("6f1d2c1e-7c0a-4b62-9d3e-aa5a0c0ffee0")
ROOT = str(uuid.uuid5(NS, "root"))
G = 1.27
S = Sym


def uid(*a):
    return str(uuid.uuid5(NS, "/".join(str(x) for x in a)))


def snap(v):
    return round(round(v / G) * G, 4)


# ---------------------------------------------------------------- custom symbols
def fx(size=1.27, hide=False, just=None):
    e = [S("effects"), [S("font"), [S("size"), size, size]]]
    if just:
        e.append([S("justify")] + [S(j) for j in just])
    if hide:
        e.append([S("hide"), S("yes")])
    return e


def prop(name, val, x=0, y=0, hide=False, just=None, size=1.27):
    return [S("property"), name, val, [S("at"), x, y, 0], fx(size, hide, just)]


def box_units(name, ref, units):
    """units: list of (title, left[(num,name,type)], right[...]). Returns lib symbol s-expr."""
    sym = [S("symbol"), "aviac:" + name, [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
           prop("Reference", ref, 0, 2.54), prop("Value", name, 0, 0), prop("Footprint", "", 0, 0, True), prop("Datasheet", "", 0, 0, True)]
    for ui, (title, left, right) in enumerate(units, 1):
        n = max(len(left), len(right), 1)
        wl = max([len(p[1]) for p in left] + [0]); wr = max([len(p[1]) for p in right] + [0])
        w = snap(max(10.16, (wl + wr) * 1.0 + 6)) if right else snap(max(10.16, wl * 1.0 + 5))
        w = snap(math.ceil(w / (2 * 2.54)) * 2 * 2.54)
        h = (n + 1) * 2.54
        x0, x1, ytop = -w / 2, w / 2, snap(h / 2)
        sub = [S("symbol"), f"{name}_{ui}_1",
               [S("rectangle"), [S("start"), x0, ytop], [S("end"), x1, ytop - h],
                [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]],
               [S("text"), title, [S("at"), 0, ytop + 1.6, 0], fx(1.27)]]
        for side, lst in (("L", left), ("R", right)):
            for i, (num, pname, ptype) in enumerate(lst):
                y = ytop - (i + 1) * 2.54
                x, ang = (x0 - 2.54, 0) if side == "L" else (x1 + 2.54, 180)
                sub.append([S("pin"), S(ptype), S("line"), [S("at"), x, y, ang], [S("length"), 2.54],
                            [S("name"), pname, fx(1.0)], [S("number"), str(num), fx(1.0)]])
        sym.append(sub)
    return sym


def jetson_symbol(pins):
    used = {int(n): net for n, net in pins.items()}
    g = {"CSI": [], "HS": [], "IO": [], "PWR": [], "GNDS": [], "NC": []}
    for n in sorted(JPINS):
        nm = JPINS[n]
        if nm == "GND":
            g["GNDS"].append((n, "GND", "power_in"))
        elif nm == "VDD_IN":
            g["PWR"].append((n, "VDD_IN", "power_in"))
        elif used[n] == "NC":
            g["NC"].append((n, nm, "passive"))
        elif nm.startswith("CSI"):
            g["CSI"].append((n, nm, "passive"))
        elif nm.startswith(("PCIE", "USB0")):
            g["HS"].append((n, nm, "passive"))
        else:
            g["IO"].append((n, nm, "passive"))
    half = lambda l: (l[:(len(l) + 1) // 2], l[(len(l) + 1) // 2:])
    units = [("CAMERA CSI (4 x 2-lane)",) + half(g["CSI"]), ("PCIe / USB",) + half(g["HS"]), ("CONTROL AND I/O",) + half(g["IO"]),
             ("POWER", g["PWR"], []), ("GROUND",) + half(g["GNDS"])]
    nc = g["NC"]; third = (len(nc) + 2) // 3
    for k in range(3):
        units.append((f"NOT USED {k+1}/3",) + half(nc[k * third:(k + 1) * third]))
    return box_units("Jetson_Orin_Nano_SODIMM260", "J", units)


def get_symbol(part):
    if part.custom:
        if part.custom["kind"] == "jetson":
            return jetson_symbol(part.pins)
        c = part.custom
        return box_units(part.value.replace(" ", "_"), c.get("ref", "U"), [(part.value, c["left"], c["right"])])
    return kilib.get(part.sym)


# ---------------------------------------------------------------- geometry of one unit
OUTV = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # outward direction in sheet coords (y down)
STUB = 2.54
CW = 1.02          # label character pitch, mm


def unit_cell(sym, unit, part):
    """Return dict with pins [(num, x, y(sheet-rel), ox, oy, net, etype)], bbox including labels."""
    pl = [p for p in kilib.pins(sym) if p["unit"] in (unit, 0)]
    items, xs, ys = [], [0.0], [0.0]
    for p in pl:
        net = part.pins.get(p["number"], "NC")
        ox, oy = OUTV[int(p["angle"]) % 360]
        x, y = p["x"], -p["y"]
        bx, by = x - ox * p["length"], y - oy * p["length"]      # body end of the pin
        xs += [x, bx]; ys += [y, by]
        ln = STUB + (len(net) * CW + 1.5 if net != "NC" else 1.0)
        xs.append(x + ox * ln); ys.append(y + oy * ln)
        if ox == 0:
            xs += [x - 1.5, x + 1.5]
        else:
            ys += [y - 1.5, y + 1.5]
        items.append((p["number"], x, y, ox, oy, net, p["etype"]))
    return dict(pins=items, x0=min(xs) - 2, x1=max(xs) + 2, y0=min(ys) - 5.5, y1=max(ys) + 2)


def units_of(sym):
    us = sorted({p["unit"] for p in kilib.pins(sym)} - {0})
    return us or [1]


# ---------------------------------------------------------------- layout
symbols = {}       # lib id -> s-expr
cells = []         # placed units
blocks_geo = []
BW = {"SOM": 520, "CAM": 420, "MCU": 300}
for bkey, btitle in D.blocks.items():
    bw = BW.get(bkey, 250)
    x, y, rowh, maxx = 6.0, 14.0, 0.0, 0.0
    placed = []
    parts = [p for p in D.parts.values() if p.block == bkey]
    # big parts first inside a block, passives after (stable order otherwise)
    parts.sort(key=lambda p: (0 if p.ref[0] in "JU" else 1 if p.ref[0] in "QLYD" else 2))
    for p in parts:
        sym = get_symbol(p)
        lid = sym[1]
        symbols[lid] = sym
        for u in units_of(sym):
            c = unit_cell(sym, u, p)
            w, h = c["x1"] - c["x0"], c["y1"] - c["y0"]
            if x + w > bw and x > 6.0:
                x, y, rowh = 6.0, y + rowh + 4, 0.0
            placed.append((p, sym, u, c, x - c["x0"], y - c["y0"]))
            x += w + 3; rowh = max(rowh, h); maxx = max(maxx, x)
    blocks_geo.append((bkey, btitle, placed, maxx + 4, y + rowh + 6))

# pack blocks into columns on the sheet
PAGE_W, PAGE_H, M0 = 1189.0, 841.0, 15.0
colx, coly, colw = M0, M0, 0.0
origin = {}
for bkey, btitle, placed, w, h in sorted(blocks_geo, key=lambda b: -b[4]):
    if coly + h > PAGE_H - 28 and coly > M0:
        colx, coly, colw = colx + colw + 8, M0, 0.0
    origin[bkey] = (snap(colx), snap(coly))
    coly += h + 8; colw = max(colw, w)
need_w = colx + colw + M0
if need_w > PAGE_W:
    PAGE_W = math.ceil(need_w / 10) * 10

# ---------------------------------------------------------------- emit
sch = [S("kicad_sch"), [S("version"), 20231120], [S("generator"), "aviac_gen"], [S("generator_version"), "8.0"],
       [S("uuid"), ROOT], [S("paper"), "User", PAGE_W, PAGE_H],
       [S("title_block"), [S("title"), TITLE], [S("date"), "2026-11-16"], [S("rev"), REV], [S("company"), "Aviac Technologies"],
        [S("comment"), 1, "Generated from hardware/tools/design.py - edit the source, not this file"],
        [S("comment"), 2, "Net labels carry all connectivity; every unused pin has a no-connect flag"]]]
libsyms = [S("lib_symbols")]
body = []
seen_wire, seen_label, seen_nc = set(), set(), set()
power_pins = {}      # net -> has power_out?
STROKE = [S("stroke"), [S("width"), 0], [S("type"), S("default")]]


def wire(x0, y0, x1, y1):
    k = (round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3))
    if k in seen_wire:
        return
    seen_wire.add(k)
    body.append([S("wire"), [S("pts"), [S("xy"), x0, y0], [S("xy"), x1, y1]], STROKE, [S("uuid"), uid("w", *k)]])


def label(net, x, y, ox, oy):
    k = (net, round(x, 3), round(y, 3))
    if k in seen_label:
        return
    seen_label.add(k)
    ang, just = {(1, 0): (0, ("left", "bottom")), (-1, 0): (180, ("right", "bottom")),
                 (0, -1): (90, ("left", "bottom")), (0, 1): (270, ("right", "bottom"))}[(ox, oy)]
    body.append([S("label"), net, [S("at"), x, y, ang], [S("fields_autoplaced"), S("yes")], fx(1.27, just=just), [S("uuid"), uid("l", *k)]])


def place_symbol(part, sym, unit, X, Y, ref, value, extra_props=()):
    pl = kilib.pins(sym)
    is2 = len({p["number"] for p in pl}) <= 2 and part is not None and part.ref[0] in "RCLD" and not part.ref.startswith("DN")
    xs = [p["x"] for p in pl if p["unit"] in (unit, 0)] or [0]
    ys = [-p["y"] for p in pl if p["unit"] in (unit, 0)] or [0]
    if is2:
        rx, ry, vx, vy, just = X + 2.2, Y - 1.2, X + 2.2, Y + 1.4, ("left",)
    else:
        rx, ry, vx, vy, just = X + min(xs) + 2.54, Y + min(ys) - 5.0, X + min(xs) + 2.54, Y + min(ys) - 3.0, ("left",)
    s = [S("symbol"), [S("lib_id"), sym[1]], [S("at"), X, Y, 0], [S("unit"), unit],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes" if not ref.startswith("#") and not ref.startswith("H") and not ref.startswith("TP") else "no")],
         [S("on_board"), S("yes")], [S("dnp"), S("yes" if (part is not None and part.dnp) else "no")], [S("uuid"), uid("sym", ref, unit)],
         [S("property"), "Reference", ref, [S("at"), rx, ry, 0], fx(1.27, ref.startswith("#"), just)],
         [S("property"), "Value", value + (" DNP" if part is not None and part.dnp else ""), [S("at"), vx, vy, 0], fx(1.0 if is2 else 1.27, ref.startswith("#"), just)],
         [S("property"), "Footprint", (part.fp if part is not None else "") or "", [S("at"), X, Y, 0], fx(1.27, True)],
         [S("property"), "Datasheet", "", [S("at"), X, Y, 0], fx(1.27, True)]]
    for k, v in extra_props:
        s.append([S("property"), k, v, [S("at"), X, Y, 0], fx(1.27, True)])
    for p in pl:
        if p["unit"] in (unit, 0):
            s.append([S("pin"), p["number"], [S("uuid"), uid("pin", ref, unit, p["number"])]])
    s.append([S("instances"), [S("project"), PROJECT, [S("path"), "/" + ROOT, [S("reference"), ref], [S("unit"), unit]]]])
    body.append(s)


for bkey, btitle, placed, w, h in blocks_geo:
    ox0, oy0 = origin[bkey]
    body.append([S("rectangle"), [S("start"), ox0, oy0], [S("end"), ox0 + w, oy0 + h],
                 [S("stroke"), [S("width"), 0.3], [S("type"), S("default")]], [S("fill"), [S("type"), S("none")]], [S("uuid"), uid("rect", bkey)]])
    body.append([S("text"), btitle, [S("exclude_from_sim"), S("no")], [S("at"), ox0 + 3, oy0 + 6, 0],
                 [S("effects"), [S("font"), [S("size"), 2.8, 2.8], [S("bold"), S("yes")]], [S("justify"), S("left"), S("bottom")]],
                 [S("uuid"), uid("txt", bkey)]])
    for (p, sym, u, c, cx, cy) in placed:
        X, Y = snap(ox0 + cx), snap(oy0 + cy)
        place_symbol(p, sym, u, X, Y, p.ref, p.value, (("MPN", p.mpn), ("Manufacturer", p.mfr), ("Description", p.desc)))
        stacked = {}
        for (num, px, py, dx, dy, net, etype) in c["pins"]:
            ax, ay = round(X + px, 4), round(Y + py, 4)
            key = (ax, ay)
            if key in stacked and stacked[key] != net:
                raise SystemExit(f"stacked pins with different nets on {p.ref}: {stacked[key]} / {net}")
            stacked[key] = net
            if etype == "no_connect":
                continue
            if net == "NC":
                if key not in seen_nc:
                    seen_nc.add(key)
                    body.append([S("no_connect"), [S("at"), ax, ay], [S("uuid"), uid("nc", p.ref, num)]])
                continue
            ex, ey = ax + dx * STUB, ay + dy * STUB
            wire(ax, ay, ex, ey)
            label(net, ex, ey, dx, dy)
            st = power_pins.setdefault(net, dict(pin=False, pout=False))
            if etype == "power_in":
                st["pin"] = True
            if etype == "power_out":
                st["pout"] = True

# power flags for rails that have power-input pins but no power-output pin driving them
flag = kilib.get("power:PWR_FLAG")
symbols[flag[1]] = flag
fx0, fy0 = origin["PWR_IN"]
flags = [n for n, st in power_pins.items() if st["pin"] and not st["pout"]]
for i, net in enumerate(flags):
    X, Y = snap(fx0 + 12 + i * 22), snap(fy0 + [b for b in blocks_geo if b[0] == "PWR_IN"][0][4] - 8)
    place_symbol(None, flag, 1, X, Y, f"#FLG{i+1:02d}", "PWR_FLAG")
    wire(X, Y, X, Y + 2.54)
    label(net, X, Y + 2.54, 0, 1)

for s in symbols.values():
    libsyms.append(s)
sch.append(libsyms)
sch += body
sch.append([S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]])
# project library with the custom symbols, plus project-local library tables
LIB = os.path.join(OUT, "..", "lib")
custom = [S("kicad_symbol_lib"), [S("version"), 20231120], [S("generator"), "aviac_gen"], [S("generator_version"), "8.0"]]
import copy
for lid, s in symbols.items():
    if lid.startswith("aviac:"):
        c = copy.deepcopy(s); c[1] = lid.split(":")[1]; custom.append(c)
open(os.path.join(LIB, "aviac.kicad_sym"), "w").write(dumps(custom) + "\n")
open(os.path.join(OUT, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "aviac")(type "KiCad")(uri "${KIPRJMOD}/../lib/aviac.kicad_sym")(options "")(descr "Aviac project symbols"))\n)\n')
open(os.path.join(OUT, "fp-lib-table"), "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "aviac")(type "KiCad")(uri "${KIPRJMOD}/../lib/aviac.pretty")(options "")(descr "Aviac project footprints"))\n)\n')
with open(os.path.join(OUT, PROJECT + ".kicad_sch"), "w") as f:
    f.write(dumps(sch) + "\n")
print("sheet", PAGE_W, "x", PAGE_H, "symbols", len([b for b in body if b[0] == "symbol"]), "labels", len(seen_label),
      "nc", len(seen_nc), "flags", flags)
