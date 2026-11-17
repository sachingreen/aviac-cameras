#!/usr/bin/env python3
"""Pack the mechanical model and a texture of the routed carrier board for the teardown page.

  assets/model.bin   Float32 triangle soup, metres, three.js axes (x forward, y up, z = -model Y)
  src/parts.json     per part: name, label, group, material, colour, explode, proxy, offset, count, centre, mass
  assets/board.png   top view of the real board: solder mask, copper under mask, exposed pads, silkscreen
"""
import base64, io, json, os, struct, subprocess, sys
import numpy as np
from PIL import Image
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(HERE, "..")
meta = json.loads(open(os.path.join(ROOT, "mechanical", "out", "model.js")).read()[len("window.AVIAC_MODEL="):-1])
frame = json.load(open(os.path.join(ROOT, "mechanical", "out", "frame.json")))

parts, chunks, off = [], [], 0
for m in meta:
    if m["name"] in ("harness",):
        continue
    raw = np.frombuffer(base64.b64decode(m["pos"]), dtype="<f4").reshape(-1, 3)
    p = np.empty_like(raw)
    p[:, 0], p[:, 1], p[:, 2] = raw[:, 0] * 1e-3, raw[:, 2] * 1e-3, -raw[:, 1] * 1e-3
    chunks.append(p.astype("<f4").tobytes())
    c, e = m["center"], m["explode"]
    parts.append(dict(n=m["name"], l=m["label"], g=m["group"], m=m["mat"], c=[round(v, 3) for v in m["color"]],
                      e=[e[0] * 1e-3, e[2] * 1e-3, -e[1] * 1e-3], p=bool(m.get("proxy")), o=off, k=len(raw),
                      ctr=[round(c[0] * 1e-3, 5), round(c[2] * 1e-3, 5), round(-c[1] * 1e-3, 5)], mass=m["mass"]))
    off += len(raw)
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
open(os.path.join(OUT, "assets", "model.bin"), "wb").write(b"".join(chunks))
# the page host serves text and images, not raw binaries: the same floats again as base64 text
open(os.path.join(OUT, "assets", "model.txt"), "w").write(base64.b64encode(b"".join(chunks)).decode())
bo = frame["board_origin"]
pl = json.load(open(os.path.join(ROOT, "..", "..", "boards", "orin-carrier", "kicad", "placement.json")))
flip = bool(frame.get("flip"))       # board mounted socket-side up: the routed face looks down
json.dump(dict(parts=parts, verts=off, board=dict(x0=bo[0] * 1e-3, z0=-bo[1] * 1e-3, y=((bo[2] - 1.0) if flip else (bo[2] + 1.0)) * 1e-3,
                                                  l=pl["board"][0] * 1e-3, w=pl["board"][1] * 1e-3, flip=flip),
               size=[v * 1e-3 for v in frame["size"]]),
          open(os.path.join(OUT, "src", "parts.json"), "w"), separators=(",", ":"))
print("parts", len(parts), "verts", off, "model.bin MB", round(off * 12 / 1e6, 2))

# ---- board texture from the KiCad layers
pcb = os.path.join(ROOT, "..", "..", "boards", "orin-carrier", "kicad", "aviac_carrier.kicad_pcb")
tmp = os.path.join(OUT, "assets", "_tmp")
os.makedirs(tmp, exist_ok=True)
Wpx = 2400


def layer(name):
    svg = os.path.join(tmp, name.replace(".", "_") + ".svg")
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "--layers", name + ",Edge.Cuts", "--exclude-drawing-sheet", "--page-size-mode", "2",
                    "--black-and-white", "-o", svg, pcb], check=True, capture_output=True)
    png = cairosvg.svg2png(url=svg, output_width=Wpx, background_color="white")
    a = np.asarray(Image.open(io.BytesIO(png)).convert("L")).astype(np.float32) / 255.0
    return 1.0 - a


edge = layer("Edge.Cuts")
cu = np.clip(layer("F.Cu") - edge, 0, 1)
mask_open = np.clip(layer("F.Mask") - edge, 0, 1)
silk = np.clip(layer("F.SilkS") - edge, 0, 1)
# crop every layer to the board outline (parts that overhang the edge enlarge the exported page)
ys, xs = np.where(edge > 0.5)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
cu, mask_open, silk = cu[y0:y1, x0:x1], mask_open[y0:y1, x0:x1], silk[y0:y1, x0:x1]
h, w = cu.shape
img = np.zeros((h, w, 3), np.float32)
img[:] = (0.035, 0.235, 0.135)                                   # solder mask over laminate
img = img * (1 - cu[..., None]) + np.array((0.075, 0.36, 0.20)) * cu[..., None]          # copper under mask
pad = np.minimum(cu, mask_open)
img = img * (1 - pad[..., None]) + np.array((0.86, 0.69, 0.33)) * pad[..., None]         # exposed, gold-plated pads
img = img * (1 - silk[..., None] * 0.9) + np.array((0.93, 0.94, 0.92)) * silk[..., None] * 0.9
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "assets", "board.png"), optimize=True)
print("board.png", w, h, round(os.path.getsize(os.path.join(OUT, "assets", "board.png")) / 1e3), "kB")
import shutil
shutil.rmtree(tmp)
