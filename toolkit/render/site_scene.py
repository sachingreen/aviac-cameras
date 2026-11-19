"""High-rise under construction, for the construction-monitoring demo (Blender 4, Cycles).

One procedural city block built the same way for every date, so images from the same camera line up:
  week 3   five floors of frame, the lower two glazed, the tower crane short
  week 11  fourteen floors of frame, eight glazed, formwork and rebar on the top deck, the crane climbed
Views: 'oblique' (a drone looking down at 40 degrees) and 'top' (straight down, orthographic, 220 x 165 m, for the
flight demo's ground). Also writes the pixel positions of a few features for the website's pins.

  blender -b -P site_scene.py -- <week> <oblique|top> <out.png> <samples> <w> <h>
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
WEEK, VIEW, OUT, SAMPLES, RW, RH = int(argv[0]), argv[1], argv[2], int(argv[3]), int(argv[4]), int(argv[5])
FLOORS = {3: 5, 11: 14}[WEEK]
CLAD = {3: 2, 11: 8}[WEEK]
FH = 3.6                                     # floor height, m
BX, BY = 32.0, 22.0                          # tower footprint
rnd = random.Random(4)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = RW, RH
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.cycles.max_bounces = 6

MATS = {}


def mat(name, color, rough=0.6, metal=0.0, noise=None, alpha=1.0, emit=None, trans=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    if noise:                                 # large-scale variation so surfaces do not read as flat CG
        tc = nt.nodes.new("ShaderNodeTexCoord"); ns = nt.nodes.new("ShaderNodeTexNoise")
        ns.inputs["Scale"].default_value = noise[0]; ns.inputs["Detail"].default_value = 6.0
        mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = "MULTIPLY"; mx.inputs["Fac"].default_value = noise[1]
        mx.inputs[1].default_value = (*color, 1)
        nt.links.new(tc.outputs["Object"], ns.inputs["Vector"]); nt.links.new(ns.outputs["Color"], mx.inputs[2])
        nt.links.new(mx.outputs[0], b.inputs["Base Color"])
    MATS[name] = m
    return m


def cube(name, x0, x1, y0, y1, z0, z1, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object; o.name = name
    o.scale = (max(0.02, x1 - x0), max(0.02, y1 - y0), max(0.02, z1 - z0))
    o.data.materials.append(m)
    return o


def cylz(name, x, y, z0, z1, r, m, seg=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m)
    return o


def beam(name, a, b, r, m):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


CONC = mat("concrete", (0.55, 0.54, 0.51), 0.85, noise=(0.4, 0.35))
CONC_D = mat("concrete_fresh", (0.42, 0.41, 0.39), 0.8, noise=(0.6, 0.3))
GLASS = mat("glass", (0.10, 0.16, 0.20), 0.05, metal=0.6)
MULL = mat("mullion", (0.20, 0.21, 0.22), 0.4, metal=0.8)
PLY = mat("formwork", (0.75, 0.42, 0.16), 0.7, noise=(1.5, 0.25))
REBAR = mat("rebar", (0.30, 0.14, 0.07), 0.7, metal=0.4)
NET = mat("netting", (0.12, 0.42, 0.25), 0.8)
YEL = mat("crane", (0.95, 0.66, 0.05), 0.45, metal=0.2)
DIRT = mat("dirt", (0.40, 0.31, 0.22), 0.95, noise=(0.08, 0.5))
ASPH = mat("asphalt", (0.10, 0.10, 0.11), 0.85, noise=(0.2, 0.3))
PAVE = mat("pavement", (0.55, 0.54, 0.50), 0.85, noise=(0.5, 0.2))
GRASS = mat("grass", (0.09, 0.15, 0.05), 0.9, noise=(0.05, 0.4))
HOARD = mat("hoarding", (0.10, 0.30, 0.22), 0.6)
WHITE = mat("paint_white", (0.80, 0.80, 0.78), 0.5)
LINE = mat("road_line", (0.85, 0.85, 0.80), 0.6)
TREE = mat("tree", (0.10, 0.22, 0.06), 0.9, noise=(2.0, 0.5))

# ---------------- ground: the site, the street, neighbours
cube("ground", -1500, 1500, -1500, 1500, -0.2, 0, GRASS)
cube("site", -32, 32, -26, 26, 0, 0.03, DIRT)
cube("road", -1500, 1500, -48, -34, 0, 0.04, ASPH)
cube("road2", 44, 58, -1500, 1500, 0, 0.04, ASPH)
for k in range(-200, 200, 9):
    cube(f"dash{k}", k, k + 4.5, -41.2, -40.8, 0.04, 0.05, LINE)
    cube(f"dash2{k}", 50.8, 51.2, k, k + 4.5, 0.04, 0.05, LINE)
cube("pave", -200, 200, -34, -30, 0, 0.12, PAVE)
cube("pave2", 40, 44, -200, 200, 0, 0.12, PAVE)
for (n, x0, x1, y0, y1) in (("hS", -32, 32, -26.3, -26), ("hN", -32, 32, 26, 26.3), ("hW", -32.3, -32, -26, 26), ("hE", 32, 32.3, -26, 26)):
    cube(n, x0, x1, y0, y1, 0, 2.4, HOARD)
neigh = [(-110, -60, -20, 40, 18), (-60, -36, 30, 70, 9), (60, 100, -20, 30, 24), (60, 110, 40, 90, 12), (-30, 30, 34, 80, 6), (-120, -70, -120, -55, 14), (62, 120, -130, -55, 30)]
for i, (x0, x1, y0, y1, h) in enumerate(neigh):
    shade = 0.28 + 0.2 * rnd.random()
    m = mat(f"bldg{i}", (shade, shade * 0.96, shade * 0.9), 0.75, noise=(0.3, 0.25))
    cube(f"n{i}", x0, x1, y0, y1, 0, h, m)
    for f in range(1, int(h / 3)):                                      # window bands
        cube(f"n{i}w{f}", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, f * 3 - 1.6, f * 3 - 0.6, GLASS)
    cube(f"n{i}roof", x0 + 2, x0 + 6, y0 + 2, y0 + 5, h, h + 2, WHITE)
for t in range(40):
    x, y = rnd.uniform(-150, 150), rnd.choice([rnd.uniform(-30, -29), rnd.uniform(28, 32)]) if t < 24 else rnd.uniform(-150, 150)
    if -36 < x < 36 and -28 < y < 28:
        continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rnd.uniform(2.2, 3.6), location=(x, y, 4))
    o = bpy.context.active_object; o.data.materials.append(TREE); o.scale = (1, 1, 0.85)
    cylz(f"trunk{t}", x, y, 0, 3, 0.25, mat("bark", (0.2, 0.14, 0.08), 0.9))

# ---------------- the tower
ox, oy = -BX / 2, -BY / 2 + 2
cube("raft", ox - 2, ox + BX + 2, oy - 2, oy + BY + 2, 0, 0.6, CONC)
cols = [(ox + i * BX / 4, oy + j * BY / 3) for i in range(5) for j in range(4)]
for f in range(FLOORS):
    z = 0.6 + f * FH
    top = f == FLOORS - 1
    cube(f"slab{f}", ox, ox + BX, oy, oy + BY, z + FH - 0.3, z + FH, CONC_D if f >= FLOORS - 2 else CONC)
    for (cx, cy) in cols:
        cube(f"col{f}_{cx}_{cy}", cx - 0.35, cx + 0.35, cy - 0.35, cy + 0.35, z, z + FH - 0.3, CONC)
    if f < CLAD:                                                       # curtain wall: glass with mullions
        for (n, x0, x1, y0, y1) in (("S", ox, ox + BX, oy - 0.1, oy), ("N", ox, ox + BX, oy + BY, oy + BY + 0.1),
                                    ("W", ox - 0.1, ox, oy, oy + BY), ("E", ox + BX, ox + BX + 0.1, oy, oy + BY)):
            cube(f"glass{f}{n}", x0, x1, y0, y1, z, z + FH - 0.3, GLASS)
        for i in range(0, 17):
            x = ox + i * BX / 16
            cube(f"mS{f}{i}", x - 0.06, x + 0.06, oy - 0.2, oy - 0.05, z, z + FH, MULL)
        for i in range(0, 12):
            y = oy + i * BY / 11
            cube(f"mW{f}{i}", ox - 0.2, ox - 0.05, y - 0.06, y + 0.06, z, z + FH, MULL)
    elif not top:                                                      # edge protection and netting on open floors
        for (n, x0, x1, y0, y1) in (("S", ox, ox + BX, oy - 0.3, oy - 0.25), ("W", ox - 0.3, ox - 0.25, oy, oy + BY),
                                    ("N", ox, ox + BX, oy + BY + 0.25, oy + BY + 0.3), ("E", ox + BX + 0.25, ox + BX + 0.3, oy, oy + BY)):
            cube(f"net{f}{n}", x0, x1, y0, y1, z + FH - 0.3, z + FH + 1.1, NET)
# the core rises a floor above the deck; formwork and rebar on the top deck
zt = 0.6 + FLOORS * FH
cube("core", ox + 12, ox + 20, oy + 7, oy + 15, 0.6, zt + 3.2, CONC)
cube("core_form", ox + 11.7, ox + 20.3, oy + 6.7, oy + 15.3, zt + 2.0, zt + 3.4, PLY)
cube("deck_form", ox + 1, ox + BX * 0.55, oy + 1, oy + BY - 1, zt, zt + 0.12, PLY)
for i in range(30):
    x = ox + BX * 0.56 + i * (BX * 0.42 / 30)
    cube(f"rebarx{i}", x - 0.03, x + 0.03, oy + 1, oy + BY - 1, zt + 0.05, zt + 0.12, REBAR)
for j in range(22):
    y = oy + 1 + j * (BY - 2) / 22
    cube(f"rebary{j}", ox + BX * 0.56, ox + BX - 1, y - 0.03, y + 0.03, zt + 0.12, zt + 0.18, REBAR)
for i, (x, y) in enumerate(((ox + 6, oy + 4), (ox + 9, oy + 17), (ox + 25, oy + 6))):
    cube(f"pallet{i}", x, x + 2.2, y, y + 1.6, zt, zt + 0.9, mat("pallet", (0.58, 0.44, 0.26), 0.8))
# hoist on the east face
cube("hoist_mast", ox + BX + 0.6, ox + BX + 1.6, oy + 9, oy + 10, 0, zt + 2, YEL)
cube("hoist_car", ox + BX + 1.6, ox + BX + 4.4, oy + 8, oy + 11, 4 + (FLOORS % 5) * FH, 7 + (FLOORS % 5) * FH, WHITE)

# ---------------- tower crane: lattice mast, jib, counter-jib, cab
cxm, cym = ox - 7, oy + BY / 2
mh = zt + 14
for (dx, dy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    beam(f"mleg{dx}{dy}", (cxm + dx, cym + dy, 0), (cxm + dx, cym + dy, mh), 0.09, YEL)
k = 0
for z in range(0, int(mh), 2):
    for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        beam(f"mb{k}", (cxm + a[0], cym + a[1], z), (cxm + b[0], cym + b[1], z + 2), 0.04, YEL); k += 1
cube("slew", cxm - 1.6, cxm + 1.6, cym - 1.6, cym + 1.6, mh, mh + 1.2, YEL)
cube("cab", cxm + 1.0, cxm + 3.2, cym - 2.6, cym - 0.6, mh - 1.0, mh + 1.2, WHITE)
ang = math.radians(28)
dirv = Vector((math.cos(ang), math.sin(ang), 0))
jl, cl = 55.0, 16.0
for s in (-0.8, 0.8):
    off = Vector((-dirv.y, dirv.x, 0)) * s
    beam(f"jib{s}", Vector((cxm, cym, mh + 1.2)) + off, Vector((cxm, cym, mh + 1.2)) + dirv * jl + off * 0.4, 0.07, YEL)
    beam(f"cjib{s}", Vector((cxm, cym, mh + 1.2)) + off, Vector((cxm, cym, mh + 1.2)) - dirv * cl + off, 0.07, YEL)
beam("jibtop", (cxm, cym, mh + 3.4), Vector((cxm, cym, mh + 1.4)) + dirv * jl, 0.06, YEL)
for i in range(1, 27):
    p = Vector((cxm, cym, mh + 1.2)) + dirv * (i * jl / 27)
    beam(f"jd{i}", p, p + Vector((0, 0, 2.0 * (1 - i / 27))) + dirv * 1.0, 0.035, YEL)
beam("apex", (cxm, cym, mh + 1.2), (cxm, cym, mh + 6), 0.12, YEL)
beam("tie", (cxm, cym, mh + 6), Vector((cxm, cym, mh + 1.4)) + dirv * jl * 0.7, 0.04, YEL)
beam("tie2", (cxm, cym, mh + 6), Vector((cxm, cym, mh + 1.4)) - dirv * cl, 0.04, YEL)
cw = Vector((cxm, cym, 0)) - dirv * (cl - 2.5)
cube("counterweight", cw.x - 1.6, cw.x + 1.6, cw.y - 1.6, cw.y + 1.6, mh - 1.2, mh + 1.0, CONC)
hook = Vector((cxm, cym, 0)) + dirv * 34
beam("rope", (hook.x, hook.y, mh + 1.2), (hook.x, hook.y, zt + 6), 0.03, mat("steel", (0.6, 0.6, 0.62), 0.3, metal=1.0))
cube("load", hook.x - 1.4, hook.x + 1.4, hook.y - 0.5, hook.y + 0.5, zt + 4.6, zt + 6, REBAR)

# site clutter: cabins, a stockpile, trucks
for i in range(3):
    cube(f"cabin{i}", 20 + i * 3.4, 23 + i * 3.4, 14, 22, 0, 2.7, WHITE if i != 1 else mat("cabin_blue", (0.12, 0.25, 0.45), 0.6))
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=7 if WEEK == 3 else 3.5, depth=3.2 if WEEK == 3 else 1.6, location=(-24, 18, 1.6 if WEEK == 3 else 0.8))
bpy.context.active_object.data.materials.append(mat("stock", (0.55, 0.47, 0.35), 0.95, noise=(0.5, 0.4)))
for i, (x, y, r) in enumerate(((-10, -38, 0), (14, -44, 0), (50, 10, 90))):
    o = cube(f"truck{i}", x - 4, x + 4, y - 1.2, y + 1.2, 0.5, 3.2, mat(f"truck{i}", ((0.75, 0.15, 0.1), (0.9, 0.9, 0.88), (0.15, 0.3, 0.6))[i], 0.4))
    o.rotation_euler.z = math.radians(r)

# ---------------- light: a clear morning sky
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
sky = w.node_tree.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(38); sky.sun_rotation = math.radians(140); sky.altitude = 200; sky.air_density = 1.4; sky.dust_density = 1.6
w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.30
sd = bpy.data.lights.new("sun", "SUN"); sd.energy = 4.2; sd.angle = math.radians(1.0); sd.color = (1.0, 0.95, 0.88)
so = bpy.data.objects.new("sun", sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(140 + 90))
sc.view_settings.exposure = -1.1

# ---------------- camera
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_end = 2000
if VIEW == "top":
    cd.type = "ORTHO"; cd.ortho_scale = 220.0
    cam.location = (0, 0, 400); cam.rotation_euler = (0, 0, 0)
else:
    cd.lens = 32
    tgt = Vector((-4, 2, 18))
    cam.location = Vector((-80, -96, 118))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)

# pins for the website (percent of the frame)
from bpy_extras.object_utils import world_to_camera_view
feat = {"top_deck": Vector((ox + BX * 0.3, oy + BY / 2, zt + 0.2)), "facade": Vector((ox + BX / 2, oy, 0.6 + (CLAD - 0.5) * FH)),
        "crane": Vector((cxm + 2, cym - 1.6, mh)), "stockpile": Vector((-24, 18, 1.5)), "rebar": Vector((ox + BX * 0.8, oy + BY / 2, zt + 0.2))}
pins = {}
for k, v in feat.items():
    p = world_to_camera_view(sc, cam, v)
    pins[k] = (round(p.x * 100, 1), round((1 - p.y) * 100, 1))
json.dump(pins, open(os.path.splitext(OUT)[0] + "_pins.json", "w"))
print("PINS", pins)
