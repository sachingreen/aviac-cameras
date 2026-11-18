#!/usr/bin/env python3
"""A spray drone's rear quarter, for the Duos film: white tank, carbon centre frame, folded arms, landing skids and
the spray boom. The Duos hangs on its gimbal at the rear, looking aft at the strip just sprayed. Illustrative, not a
specific aircraft. Frame: X right, Y aft... here the drone's tail points to -Y so the Duos, turned to face -Y, looks
aft. Units: mm.

  python3 toolkit/cad/sprayer.py   -> cameras/drone/sprayer/out/
"""
import math, os, sys
import cadquery as cq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rugged_cameras as rc
from rugged_cameras import add, box, rbox, zcyl, W, V

G = "Drone"
WHITE, CF, GREY = (0.82, 0.82, 0.80), (0.02, 0.02, 0.022), (0.30, 0.32, 0.34)
# centre body: a rounded white shell over a carbon frame, the tank below it
body = rbox(-210, 210, -260, 260, 60, 190, 60, "|Z")
try:
    body = body.faces(">Z").edges().fillet(30)
except Exception:
    pass
add("body", body, G, mat="gloss_white", color=WHITE, mass=0.0, label="Body shell")
add("frame", rbox(-230, 230, -280, 280, 40, 60, 20, "|Z"), G, mat="cfrp", color=CF, mass=0.0, label="Carbon centre plate")
tank = rbox(-150, 150, -170, 170, -120, 40, 50, "|Z")
try:
    tank = tank.faces("<Z").edges().fillet(40)
except Exception:
    pass
add("tank", tank, G, mat="gloss_white", color=(0.9, 0.9, 0.88), mass=0.0, label="Spray tank, 20 L")
for s in (-1, 1):
    for y in (-180, 180):
        arm = W(cq.Solid.makeCylinder(16, 700, V(s * 220, y, 120), V(s * 0.8, math.copysign(0.6, y), 0)))
        add(f"arm_{s}_{y}", arm, G, mat="cfrp", color=CF, mass=0.0, label="Arm")
    skid = W(cq.Solid.makeCylinder(10, 760, V(s * 200, -380, -250), V(0, 1, 0)))
    add(f"skid_{s}", skid, G, mat="cfrp", color=CF, mass=0.0, label="Landing skid")
    for y in (-200, 200):
        add(f"strut_{s}_{y}", W(cq.Solid.makeCylinder(9, 300, V(s * 200, y, -250), V(s * -0.25, 0, 1))), G, mat="cfrp", color=CF, mass=0.0, label="Strut")
add("boom", W(cq.Solid.makeCylinder(9, 1400, V(-700, 120, -150), V(1, 0, 0))), G, mat="cfrp", color=CF, mass=0.0, label="Spray boom")
for k in range(8):
    add(f"nozzle_{k}", zcyl(-630 + k * 180, 120, -178, -158, 7), G, mat="accent", color=(0.85, 0.42, 0.08), mass=0.0, label="Nozzle")
CAMERA_MOUNT = (0.0, -270.0, 40.0)      # under the rear edge of the centre plate, facing aft (-Y)
rc.FINISHES = {"default": {}}
rc.export(os.path.join(rc.REPO, "cameras", "drone", "sprayer", "out"), "aviac_sprayer", extra_frame={"camera_mount": CAMERA_MOUNT})
