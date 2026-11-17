"""Studio renders of the Aviac camera (Blender 4.x, Cycles CPU, headless).

usage: blender -b -P render.py -- <model.js> <board.glb> <outdir> <samples> <shot,shot,...> [width height]
The lens the close-up focuses on is the part named by $FOCUS (default rgb_lens_glass).
The carrier board is the real KiCad 3D export (board.glb); the simplified stand-in
parts in model.js that are flagged 'proxy' are hidden.
Run denoise.py on the output folder afterwards.
"""
import bpy, bmesh, json, base64, struct, sys, math, os
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
src, glb, outdir, samples = argv[0], argv[1], argv[2], int(argv[3])
shots = argv[4].split(",")
RW, RH = (int(argv[5]), int(argv[6])) if len(argv) > 6 else (1920, 1200)
os.makedirs(outdir, exist_ok=True)
U = 0.001
frame = json.load(open(os.path.join(os.path.dirname(src), "frame.json")))
BO = frame["board_origin"]          # model mm of board (0,0) top-left corner, underside

meta = json.loads(open(src).read()[len("window.AVIAC_MODEL="):-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 10
scene.cycles.transmission_bounces = 10
scene.cycles.glossy_bounces = 6
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.cycles.sample_clamp_indirect = 5.0
scene.cycles.sample_clamp_direct = 30.0
scene.render.resolution_x, scene.render.resolution_y = RW, RH
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "16"
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium High Contrast"

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bgn = world.node_tree.nodes["Background"]


# ------------------------------------------------------------------ materials
def principled(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"], m.node_tree


ALIAS = {"color": "Base Color", "metal": "Metallic", "rough": "Roughness", "ior": "IOR", "trans": "Transmission Weight",
         "coat": "Coat Weight", "coat_rough": "Coat Roughness", "spec": "Specular IOR Level", "emit": "Emission Strength",
         "emit_color": "Emission Color", "sss": "Subsurface Weight"}


def setp(b, **k):
    for key, v in k.items():
        inp = b.inputs.get(ALIAS[key])
        if inp is None:
            continue
        inp.default_value = (v[0], v[1], v[2], 1) if isinstance(v, (tuple, list)) else v


def bump(nt, b, scale, strength, distance=0.0002, detail=4.0):
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale; tex.inputs["Detail"].default_value = detail
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = distance
    nt.links.new(tex.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])


def make_material(kind, color, name):
    m, b, nt = principled(name)
    c = tuple(color)
    if kind == "shell":
        setp(b, color=(c[0] * 0.6, c[1] * 0.6, c[2] * 0.62), rough=0.56, spec=0.42)
        bump(nt, b, 2600.0, 0.22, 0.00012)
    elif kind == "pcb":
        setp(b, color=c, rough=0.40, coat=0.4, coat_rough=0.22)
    elif kind == "mask":            # solder mask of the real board
        setp(b, color=(0.003, 0.060, 0.022), rough=0.42, coat=0.30, coat_rough=0.20)
    elif kind == "track":           # copper under the mask
        setp(b, color=(0.012, 0.150, 0.055), rough=0.36, metal=0.30, coat=0.30, coat_rough=0.20)
    elif kind == "hole":            # via barrels and drill walls
        setp(b, color=(0.55, 0.42, 0.18), metal=1.0, rough=0.45)
    elif kind == "ic":
        setp(b, color=(min(c[0], 0.03), min(c[1], 0.03), min(c[2], 0.033)), rough=0.46, spec=0.4); bump(nt, b, 9000.0, 0.08, 0.00003)
    elif kind in ("ceramic", "paper"):
        setp(b, color=c, rough=0.55)
    elif kind == "ceramic_dark":
        setp(b, color=c, rough=0.35, coat=0.3)
    elif kind == "ferrite":
        setp(b, color=(0.05, 0.05, 0.055), rough=0.72); bump(nt, b, 5000.0, 0.25, 0.00006)
    elif kind == "gold":
        setp(b, color=(0.95, 0.68, 0.25), metal=1.0, rough=0.22)
    elif kind == "accent":
        setp(b, color=(0.55, 0.13, 0.015), metal=1.0, rough=0.42)
    elif kind == "steel":
        setp(b, color=(0.78, 0.79, 0.80), metal=1.0, rough=0.26)
    elif kind == "steel_black":
        setp(b, color=(0.05, 0.05, 0.055), metal=1.0, rough=0.36)
    elif kind == "alu":
        setp(b, color=(0.80, 0.81, 0.83), metal=1.0, rough=0.33)
    elif kind == "hardcoat":        # Type III hard anodise, bead-blasted: dark metallic grey, fine satin grain
        setp(b, color=(c[0] * 0.55, c[1] * 0.55, c[2] * 0.58), metal=1.0, rough=0.44)
        bump(nt, b, 7000.0, 0.10, 0.00003, detail=2.0)
    elif kind == "etch":            # laser-etched through the anodise: matte light grey
        setp(b, color=(0.74, 0.75, 0.77), metal=0.55, rough=0.6)
    elif kind == "steel_brushed":
        setp(b, color=(0.70, 0.71, 0.72), metal=1.0, rough=0.30)
        bump(nt, b, 900.0, 0.06, 0.00002, detail=1.0)
    elif kind == "anodised":
        setp(b, color=(max(c[0], 0.012), max(c[1], 0.012), max(c[2], 0.014)), metal=0.92, rough=0.40)
    elif kind == "rubberised":
        setp(b, color=c, rough=0.72, spec=0.3)
    elif kind == "rubber":
        setp(b, color=c, rough=0.68)
    elif kind == "plastic_gloss":
        setp(b, color=c, rough=0.32)
    elif kind == "fpc":
        setp(b, color=(0.80, 0.33, 0.03), rough=0.33, coat=0.6, coat_rough=0.15)
        tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
        wv.inputs["Scale"].default_value = 2100.0; wv.inputs["Distortion"].default_value = 0.0; wv.bands_direction = "Y"
        mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0.82, 0.35, 0.03, 1); mix.inputs[2].default_value = (0.58, 0.22, 0.02, 1)
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], mix.inputs[0]); nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    elif kind == "lens":
        setp(b, color=(0.93, 0.95, 1.0), rough=0.0, trans=1.0, ior=1.62, coat=1.0, coat_rough=0.0)
        tint = b.inputs.get("Coat Tint")
        if tint is not None:
            tint.default_value = (c[0] * 2.4 + 0.25, c[1] * 2.4 + 0.2, c[2] * 2.4 + 0.3, 1)
    elif kind == "window":          # AR-coated: very little surface reflection
        setp(b, color=(0.98, 0.99, 1.0), rough=0.0, trans=1.0, ior=1.12)
    elif kind == "filter":
        setp(b, color=(0.55, 0.92, 0.95), rough=0.02, trans=1.0, ior=1.52)
    elif kind == "bandpass":
        setp(b, color=(c[0] * 0.40 + 0.008, c[1] * 0.25 + 0.003, c[2] * 0.35 + 0.006), metal=0.75, rough=0.08, coat=0.6, coat_rough=0.02)
    elif kind == "cfrp":
        setp(b, color=(0.012, 0.012, 0.014), rough=0.28, coat=1.0, coat_rough=0.06)
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (520, 520, 520); mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
        ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 1.0
        ck.inputs["Color1"].default_value = (0.03, 0.03, 0.034, 1); ck.inputs["Color2"].default_value = (0.008, 0.008, 0.01, 1)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], ck.inputs["Vector"])
        nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    elif kind == "emit":
        setp(b, color=c, emit=6.0, emit_color=c)
    elif kind == "sensor":
        setp(b, color=(0.08, 0.30, 0.26), metal=1.0, rough=0.12, coat=1.0)
    elif kind == "ptfe":
        setp(b, color=(0.95, 0.95, 0.93), rough=0.45, sss=0.4)
    elif kind == "black":
        setp(b, color=(0.004, 0.004, 0.005), rough=0.9)
    else:
        setp(b, color=c, rough=0.5)
    return m


rig = bpy.data.objects.new("rig", None); scene.collection.objects.link(rig)
objs, matcache = {}, {}
for m in meta:
    raw = base64.b64decode(m["pos"]); n = len(raw) // 4
    f = struct.unpack(f"<{n}f", raw)
    verts = [(f[i] * U, f[i + 1] * U, f[i + 2] * U) for i in range(0, n, 3)]
    faces = [(i, i + 1, i + 2) for i in range(0, len(verts), 3)]
    me = bpy.data.meshes.new(m["name"]); me.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(32)
    except Exception:
        pass
    me.update()
    ob = bpy.data.objects.new(m["name"], me); scene.collection.objects.link(ob); ob.parent = rig
    key = (m["mat"], tuple(round(c, 3) for c in m["color"]))
    if key not in matcache:
        matcache[key] = make_material(m["mat"], m["color"], m["mat"] + "_" + str(len(matcache)))
    ob.data.materials.append(matcache[key])
    # CAD meshes have long thin triangles across flat faces; weighting normals by face area keeps flat faces flat
    wn = ob.modifiers.new("wnormal", "WEIGHTED_NORMAL"); wn.mode = "FACE_AREA"; wn.keep_sharp = True
    if m["mat"] in ("shell", "hardcoat", "steel_brushed", "anodised", "pcb", "plastic_gloss", "ic", "steel", "accent", "cfrp"):
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.00022 if m["mat"] == "shell" else 0.00010
        bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
    ob["explode"] = m["explode"]; ob["group"] = m["group"]; ob["proxy"] = bool(m.get("proxy"))
    objs[m["name"]] = ob

# ---- the real carrier board from KiCad
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
imported = [o for o in bpy.data.objects if o not in before]
board_root = bpy.data.objects.new("board_root", None); scene.collection.objects.link(board_root); board_root.parent = rig
# glTF import is already converted to Blender's Z-up; KiCad page coords: x right, y down (negated on export)
OFF = Vector(((BO[0] - 100.0) * U, (BO[1] + 60.0) * U, BO[2] * U))
if frame.get("flip"):        # board mounted upside down (socket side up): rotate the export 180 deg about X
    board_root.rotation_euler = (math.pi, 0, 0)
    OFF = Vector(((BO[0] - 100.0) * U, (-BO[1] - 60.0) * U, BO[2] * U))
for o in imported:
    if o.parent is None:
        o.parent = board_root
board_root["explode"] = (0, 0, 32)


def classify(col):
    r, g, b = col[0], col[1], col[2]
    mx, mn = max(r, g, b), min(r, g, b)
    if g > r * 1.25 and g > b * 1.15:
        return "track" if g > 0.3 else "mask"
    if r > 0.5 and g > 0.42 and b < 0.3 and (mx - mn) > 0.3:
        return "gold"
    if mx < 0.14:
        return "ic"
    if (mx - mn) < 0.10 and mx > 0.5:
        return "beige" if b < r - 0.1 else "steel"
    if r > g > b and (r - b) > 0.08:
        return "beige" if mx > 0.6 else "ceramic"
    return "plastic"


remap = {}
for mat in bpy.data.materials:
    if not mat.name.startswith("mat_") or not mat.use_nodes:
        continue
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b is None:
        continue
    col = tuple(b.inputs["Base Color"].default_value[:3])
    kind = classify(col)
    if kind == "beige":
        new = make_material("plastic_gloss", (0.78, 0.74, 0.62), "g_beige")
    elif kind == "plastic":
        new = make_material("plastic_gloss", col, "g_plastic")
    elif kind == "ceramic":
        new = make_material("ceramic", (0.50, 0.38, 0.26), "g_ceramic")
    else:
        new = make_material(kind, col, "g_" + kind)
    remap[mat.name] = new
import re
hole_mat = make_material("hole", (0, 0, 0), "g_hole")
board_objs = []
for o in imported:
    if o.type != "MESH":
        continue
    board_objs.append(o)
    is_component = bool(o.parent and re.match(r"^[A-Z]+\d+", o.parent.name))
    for slot in o.material_slots:
        if slot.material and slot.material.name in remap:
            new = remap[slot.material.name]
            if not is_component and new.name.startswith("g_ic"):
                new = hole_mat          # dark non-component geometry is plated holes, not black plastic
            slot.material = new
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(35)
    except Exception:
        pass

# ------------------------------------------------------------------ studio
def backdrop():
    me = bpy.data.meshes.new("cyc"); bm = bmesh.new()
    prof = [(-6.0, 0.0)] + [(1.2 + 1.0 * math.sin(a), 1.0 - 1.0 * math.cos(a)) for a in [math.radians(d) for d in range(0, 91, 6)]] + [(2.2, 6.0)]
    rows = [[bm.verts.new((x, y, z)) for x in (-8.0, 8.0)] for (y, z) in prof]
    for a, b in zip(rows[:-1], rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cyc", me); scene.collection.objects.link(ob)
    m, b, nt = principled("cyc"); ob.data.materials.append(m)
    return ob


cyc = backdrop()


def mood(dark):
    b = cyc.data.materials[0].node_tree.nodes["Principled BSDF"]
    col = (0.030, 0.032, 0.036) if dark else (0.86, 0.855, 0.84)
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1)
    b.inputs["Roughness"].default_value = 0.38 if dark else 0.42
    bgn.inputs[1].default_value = 0.035 if dark else 0.30
    bgn.inputs[0].default_value = (0.55, 0.62, 0.75, 1) if dark else (0.90, 0.90, 0.92, 1)
    scene["dark"] = dark


def area(name, loc, target, power, size, color=(1, 1, 1), size_y=None):
    d = bpy.data.lights.new(name, "AREA"); d.energy = power; d.color = color
    d.shape = "RECTANGLE" if size_y else "SQUARE"; d.size = size
    if size_y:
        d.size_y = size_y
    o = bpy.data.objects.new(name, d); o.location = loc; scene.collection.objects.link(o)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d)
scene.collection.objects.link(cam); scene.camera = cam
cam_d.clip_start = 0.01; cam_d.clip_end = 100; cam_d.sensor_width = 36
lights = []


def studio(center, scale=1.0):
    for l in lights:
        bpy.data.objects.remove(l, do_unlink=True)
    lights.clear()
    c = Vector(center); s = scale
    k = s * s
    if scene.get("dark", False):
        lights.append(area("key", c + Vector((-0.45, -0.55, 0.75)) * s, c, 6.0 * k, 0.55 * s, (1.0, 0.96, 0.90)))
        lights.append(area("rimR", c + Vector((0.55, 0.70, 0.40)) * s, c, 11 * k, 0.9 * s, (0.80, 0.90, 1.0), 0.25 * s))
        lights.append(area("rimL", c + Vector((-0.85, 0.45, 0.30)) * s, c, 6.5 * k, 0.8 * s, (1.0, 0.80, 0.62), 0.2 * s))
        lights.append(area("top", c + Vector((0.05, 0.0, 0.95)) * s, c, 2.2 * k, 1.0 * s, (1, 1, 1), 0.35 * s))
        lights.append(area("fill", c + Vector((0.7, -0.7, 0.25)) * s, c, 0.7 * k, 1.0 * s, (0.85, 0.92, 1.0)))
        return
    lights.append(area("key", c + Vector((-0.55, -0.60, 0.80)) * s, c, 11 * k, 0.9 * s, (1.0, 0.97, 0.93)))
    lights.append(area("fill", c + Vector((0.90, -0.35, 0.35)) * s, c, 3.0 * k, 1.2 * s, (0.90, 0.95, 1.0)))
    lights.append(area("rim", c + Vector((0.25, 0.75, 0.55)) * s, c, 9 * k, 0.7 * s, (1.0, 0.98, 0.95)))
    lights.append(area("top", c + Vector((0.0, 0.05, 1.0)) * s, c, 5 * k, 1.4 * s, (1, 1, 1), 0.5 * s))
    lights.append(area("kick", c + Vector((-0.8, 0.25, 0.12)) * s, c, 2.2 * k, 0.5 * s, (1.0, 0.86, 0.72)))


def pose(k=0.0, hide=(), rot=(0, 0, 0), lift=0.0, show_only=None, board=True):
    rig.rotation_euler = Euler(rot, "XYZ"); rig.location = (0, 0, 0)
    vis = []
    for ob in objs.values():
        e = ob["explode"]
        ob.location = (e[0] * k * U, e[1] * k * U, e[2] * k * U)
        hidden = ob["group"] in hide or ob.name in hide or ob["proxy"]
        if show_only is not None:
            hidden = ob["group"] not in show_only or ob["proxy"]
        ob.hide_render = hidden
        if not hidden:
            vis.append(ob)
    show_board = board and "Carrier board" not in hide and (show_only is None or "Carrier board" in show_only)
    board_root.location = OFF + Vector((0, 0, 32 * k * U))
    for o in board_objs:
        o.hide_render = not show_board
    if show_only is not None and "Carrier board" in show_only:
        for name in ("m2_ssd", "m2_ssd_ctrl", "m2_ssd_label"):
            pass
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for ob in vis + (board_objs[::25] if show_board else []):
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z))); hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    ctr = (lo + hi) / 2
    rig.location = (-ctr.x, -ctr.y, -lo.z + lift)
    bpy.context.view_layer.update()
    size = hi - lo
    return Vector((0, 0, lift + size.z / 2)), size


def shoot(name, center, size, az, el, lens, fill=0.80, fstop=None, focus=None, dark=False, light_scale=None):
    mood(dark)
    cam_d.lens = lens
    target = Vector(center)
    r = size.length / 2
    fov = 2 * math.atan(min(36.0, 36.0 * RH / RW) / (2 * lens))
    dist = r / math.sin(fov / 2) / max(fill, 0.1) * 0.62
    a, e = math.radians(az), math.radians(el)
    loc = target + Vector((dist * math.cos(e) * math.cos(a), dist * math.cos(e) * math.sin(a), dist * math.sin(e)))
    cam.location = loc
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    if fstop:
        cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = fstop
        cam_d.dof.focus_distance = (Vector(focus) - loc).length if focus is not None else dist
    else:
        cam_d.dof.use_dof = False
    studio(center, light_scale or max(0.45, min(1.0, size.length / 0.26)))
    scene.render.filepath = os.path.join(outdir, name + ".png")
    bpy.ops.render.render(write_still=True)


def world_of(name):
    ob = objs[name]
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for corner in ob.bound_box:
        w = ob.matrix_world @ Vector(corner)
        lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z))); hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return (lo + hi) / 2


TOPU = "DLS + GNSS top unit"
FLIP = (math.pi, 0, 0)
ALLG = {o["group"] for o in objs.values()}
for s in shots:
    if s == "hero_lens":
        c, size = pose(0, hide=(TOPU, "Mount"), rot=FLIP)
        shoot("01_hero_optics", c, size, az=-128, el=22, lens=85, fill=0.74, dark=True)
    elif s == "hero_lens_light":
        c, size = pose(0, hide=(TOPU, "Mount"), rot=FLIP)
        shoot("01b_hero_optics_light", c, size, az=-128, el=24, lens=85, fill=0.74)
    elif s == "hero_top":
        c, size = pose(0, hide=(TOPU,), rot=(0, 0, 0), lift=0.045)
        shoot("02_hero_mount_side", c, size, az=-52, el=28, lens=85, fill=0.74, dark=True)
    elif s == "exploded":
        c, size = pose(1.0, hide=(TOPU,), rot=(0, 0, 0), lift=0.03)
        shoot("03_exploded", c, size, az=-58, el=14, lens=70, fill=0.62)
    elif s == "inside":
        c, size = pose(0, hide=(TOPU, "Mount", "Enclosure"), rot=FLIP)
        shoot("04_inside_optics_side", c, size, az=-122, el=26, lens=85, fill=0.76)
    elif s == "inside_top":
        c, size = pose(0, hide=(TOPU, "Mount", "Enclosure"), rot=(0, 0, 0), lift=0.02)
        shoot("05_inside_electronics_side", c, size, az=-118, el=34, lens=85, fill=0.78)
    elif s == "optics_macro":
        c, size = pose(0, hide=(TOPU, "Mount"), rot=FLIP)
        f = world_of(os.environ.get("FOCUS", "rgb_lens_glass"))
        shoot("06_optics_macro", f + Vector((0.004, 0.0, -0.012)), Vector((0.11, 0.09, 0.05)), az=-108, el=33, lens=100, fill=0.80, fstop=22.0, focus=f, dark=True)
    elif s == "board":
        c, size = pose(0, show_only=("Carrier board",), rot=(0, 0, 0), lift=0.035)
        for n in ("sodimm_socket", "sodimm_latch_0", "sodimm_latch_1", "standoff_0", "standoff_1"):
            objs[n].hide_render = False
        shoot("07_carrier_board", c, size, az=-118, el=40, lens=85, fill=0.80)
    elif s == "board_macro":
        c, size = pose(0, show_only=("Carrier board",), rot=(0, 0, 0), lift=0.035)
        b = board_root.matrix_world @ Vector((0.136, -0.090, 0.002))
        shoot("08_carrier_board_macro", b, Vector((0.07, 0.05, 0.02)), az=-125, el=32, lens=100, fill=0.8, fstop=16.0, focus=b)
    # ---- compact boxes (Duo, 6B): shot in its flying orientation, mount on top
    elif s == "box_hero":
        c, size = pose(0, hide=("Drone", TOPU), rot=(0, 0, 0), lift=0.004)
        shoot("01_box_hero", c, size, az=-38, el=16, lens=85, fill=0.72, dark=True)
    elif s == "box_hero_light":
        c, size = pose(0, hide=("Drone", TOPU), rot=(0, 0, 0), lift=0.004)
        shoot("02_box_hero_light", c, size, az=-142, el=20, lens=85, fill=0.72)
    elif s == "box_under":
        c, size = pose(0, hide=("Drone", TOPU), rot=(0, 0, 0), lift=0.16)
        shoot("03_box_underside", c, size, az=-62, el=-14, lens=85, fill=0.70)
    elif s == "box_mounted":
        c, size = pose(0, rot=(0, 0, 0), lift=0.12)
        shoot("04_box_on_drone_tube", c, size, az=-28, el=8, lens=70, fill=0.70)
    elif s == "box_exploded":
        c, size = pose(1.0, hide=("Drone", TOPU), rot=(0, 0, 0), lift=0.02)
        shoot("05_box_exploded", c, size, az=-50, el=14, lens=70, fill=0.60)
    elif s == "box_inside":
        c, size = pose(0, hide=("Drone", TOPU, "Mount", "Enclosure", "lid", "gasket") + tuple(f"lid_screw_{i}" for i in range(6)), rot=(0, 0, 0), lift=0.02)
        shoot("06_box_inside", c, size, az=-128, el=36, lens=85, fill=0.78)
    elif s == "box_filter":
        c, size = pose(0, hide=("Drone", TOPU), rot=(0, 0, 0), lift=0.16)
        f = world_of(os.environ.get("FOCUS", "mira1_bezel"))
        shoot("07_box_filter_closeup", f, Vector((0.07, 0.07, 0.03)), az=-70, el=-24, lens=100, fill=0.75, fstop=16.0, focus=f, dark=True)
    elif s == "top_unit":
        c, size = pose(0.5, show_only=(TOPU,), rot=(0, 0, 0), board=False)
        shoot("09_top_unit_exploded", c, size, az=-55, el=24, lens=100, fill=0.7)
