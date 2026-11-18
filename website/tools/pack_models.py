#!/usr/bin/env python3
"""Pack the CAD models for the website viewer.

Reads cameras/<cam>/mechanical/out/model.js (+ finishes.json) and writes website/src/models/<cam>/:
  model.txt   base64 of Int16 vertex positions, 0.01 mm units, three.js axes (x right, y up, z toward the viewer)
  parts.json  per part: name, label, group, material, colour, finish role, explode (mm, three axes), offset, count
Parts in hidden groups (the DLS puck that lives on the drone) are left out.
"""
import base64, json, os, struct, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HIDE = {"DLS puck"}


def pack(cam):
    src = os.path.join(REPO, "cameras", cam, "mechanical", "out")
    meta = json.loads(open(os.path.join(src, "model.js")).read()[len("window.AVIAC_MODEL="):-1])
    fin = json.load(open(os.path.join(src, "finishes.json")))
    out = os.path.join(REPO, "website", "src", "models", cam)
    os.makedirs(out, exist_ok=True)
    buf, parts, off = bytearray(), [], 0
    for m in meta:
        if m["group"] in HIDE:
            continue
        raw = base64.b64decode(m["pos"])
        f = struct.unpack(f"<{len(raw) // 4}f", raw)
        n = len(f) // 3
        for i in range(n):
            x, y, z = f[3 * i], f[3 * i + 1], f[3 * i + 2]
            buf += struct.pack("<3h", round(x * 100), round(z * 100), round(-y * 100))   # CAD (x, y-in, z-up) -> three (x, y-up, z-out)
        e = m["explode"]
        parts.append(dict(n=m["name"], l=m["label"], g=m["group"], m=m["mat"], c=[round(v, 4) for v in m["color"]], f=m.get("finish"),
                          e=[e[0], e[2], -e[1]], o=off, k=n))
        off += n
    open(os.path.join(out, "model.txt"), "w").write(base64.b64encode(bytes(buf)).decode())
    json.dump(dict(parts=parts, finishes=fin), open(os.path.join(out, "parts.json"), "w"), separators=(",", ":"))
    print(cam, len(parts), "parts", off, "verts", round(len(buf) * 4 / 3 / 1e6, 2), "MB")


for cam in (sys.argv[1:] or ["ms", "duos"]):
    pack(cam)
