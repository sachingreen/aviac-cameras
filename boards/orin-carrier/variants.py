#!/usr/bin/env python3
"""Build variants of the Orin Nano carrier and their bills of materials.

  6band : all four camera ports fitted
  duo   : camera ports CAM2 and CAM3 not fitted (connector, filter, decoupling, pull-ups, trigger resistor)

usage:  python3 variants.py              writes kicad/bom_<variant>.csv and prints the not-fitted list
        /usr/bin/python3 variants.py pcb also writes kicad/variants/<variant>.kicad_pcb with those parts
                                         marked do-not-populate (for 3D export and assembly files)
"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "toolkit", "kicad"))
from design import D, PROJECT

SHARED = {"GND", "+3V3", "+1V8", "VSYS", "VBAT", "NC"}


def unfitted(ports):
    """Parts whose every signal net belongs to one of the given camera ports."""
    tags = tuple(f"CAM{p}_" for p in ports) + tuple(f"TRIG{p}" for p in ports)
    out = []
    for ref, p in D.parts.items():
        sig = [n for n in p.pins.values() if n not in SHARED]
        if sig and all(n.startswith(tags) for n in sig):
            out.append(ref)
    return out


VARIANTS = {"6band": [], "duo": unfitted([2, 3])}


def bom(variant):
    skip = set(VARIANTS[variant])
    groups = {}
    for ref, p in D.parts.items():
        if p.dnp or ref in skip or ref.startswith(("H", "TP")) or not p.mpn or p.mpn.startswith("("):
            continue
        key = (p.mpn, p.value, p.fp)
        g = groups.setdefault(key, dict(refs=[], p=p))
        g["refs"].append(ref)
    rows = sorted(groups.values(), key=lambda g: (g["refs"][0][0], len(g["refs"][0]), g["refs"][0]))
    path = os.path.join(HERE, "kicad", f"bom_{variant}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["References", "Qty", "Value", "Manufacturer part", "Manufacturer", "Description", "Footprint"])
        for g in rows:
            p = g["p"]
            w.writerow([" ".join(g["refs"]), len(g["refs"]), p.value, p.mpn, p.mfr, p.desc, p.fp.split(":")[-1]])
    return path, sum(len(g["refs"]) for g in rows), len(rows)


if __name__ == "__main__":
    for v in VARIANTS:
        path, n, lines = bom(v)
        print(f"{v}: {n} parts on {lines} lines -> {os.path.relpath(path, HERE)}")
    print("duo leaves off:", " ".join(VARIANTS["duo"]))

    if len(sys.argv) > 1 and sys.argv[1] == "pcb":
        import pcbnew
        src = os.path.join(HERE, "kicad", PROJECT + ".kicad_pcb")
        os.makedirs(os.path.join(HERE, "kicad", "variants"), exist_ok=True)
        for v, refs in VARIANTS.items():
            b = pcbnew.LoadBoard(src)
            for fp in b.GetFootprints():
                if fp.GetReference() in refs:
                    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
            out = os.path.join(HERE, "kicad", "variants", f"{v}.kicad_pcb")
            pcbnew.SaveBoard(out, b)
            print("wrote", os.path.relpath(out, HERE))
