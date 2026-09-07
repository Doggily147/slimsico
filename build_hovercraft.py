"""A flying jetski for Yellow, modelled after a small sit-down runabout but
sharper and more futuristic: an angular hull with a hard chine and a side
strake, flared gunwales, footwells either side of a long two-tier saddle, a
faceted hood carrying a handlebar pod with a console display and a low
windshield, side intake vents, purple light strips, and a thruster bay at the
stern with a glowing nozzle. It flies: a purple hover pad underneath lights
the ground, and a gentle bob is keyed across the scene.

The body is ONE mesh from hull cross-sections, with every hard line creased
so subdivision keeps the panels crisp. Painted by region: purple hood and
fairing, black hull, rear deck and footwells, white bow sides.

Sized like the real thing next to Yellow (about 14 studs long, 6 wide).
Everything hangs off the empty "Hovercraft". Run inside Blender with
slimsico.blend open; re-running replaces it.
"""
import bmesh
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene
FPS = 24

# ------------------------------------------------------------ cleanup
for o in list(bpy.data.objects):
    if o.name.startswith("Hovercraft"):
        bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.lights):
    for d in list(block):
        if d.users == 0 and d.name.startswith("Hovercraft"):
            block.remove(d)
col = bpy.data.collections.get("Props")
if col is None:
    col = bpy.data.collections.new("Props")
    scene.collection.children.link(col)


def material(name, rgb, rough=0.5, metallic=0.0, emit=None, coat=0.0):
    m = bpy.data.materials.get("Hover_" + name) or bpy.data.materials.new("Hover_" + name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = coat
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*rgb, 1)
    return m


PURPLE = material("Purple", (0.40, 0.07, 0.72), rough=0.3, coat=0.6)
BLACK = material("Black", (0.02, 0.02, 0.025), rough=0.42, coat=0.4)
WHITE = material("White", (0.92, 0.92, 0.9), rough=0.33, coat=0.5)
RUBBER = material("Rubber", (0.06, 0.06, 0.065), rough=0.92)
MAT = material("Mat", (0.1, 0.1, 0.11), rough=0.95)
GRIP = material("Grip", (0.5, 0.12, 0.8), rough=0.8)
DARK = material("DarkMetal", (0.12, 0.12, 0.13), rough=0.45, metallic=0.75)
CHROME = material("Chrome", (0.72, 0.74, 0.78), rough=0.18, metallic=1.0)
GLASS = material("Glass", (0.25, 0.2, 0.35), rough=0.05, emit=((0.35, 0.25, 0.5), 0.2))
SCREEN = material("Screen", (0.03, 0.02, 0.06), rough=0.25, emit=((0.55, 0.3, 1.0), 1.6))
VIOLET = material("HoverLight", (0.7, 0.3, 1.0), rough=0.3, emit=((0.65, 0.25, 1.0), 9))
VIOLET_STRIP = material("Strip", (0.7, 0.3, 1.0), rough=0.3, emit=((0.6, 0.25, 1.0), 5))
NEON = material("Neon", (0.75, 0.3, 1.0), rough=0.3, emit=((0.62, 0.22, 1.0), 5.5))
VIOLET_SOFT = material("HoverGlow", (0.7, 0.3, 1.0), rough=1.0, emit=((0.6, 0.25, 1.0), 0.8))
VIOLET_SOFT.blend_method = "BLEND"
VIOLET_SOFT.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.14

root = bpy.data.objects.new("Hovercraft", None)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 3
col.objects.link(root)


def attach(o, parent=None):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.parent = parent or root
    o.matrix_parent_inverse.identity()
    return o


# ------------------------------------------------------------ the body, one mesh
# Half-section from the keel up and over to the centreline. Every point is a
# hard line that runs the length of the hull:
#   keel, chine, strake, gunwale, rail top, deck side, footwell rim, footwell
#   floor, seat-base wall, seat-base top, centre.
# `fw` is the footwell depth (0 through the hood, where the deck is solid).
def outline(w, zk, zg, zd, zt, fw):
    return [
        (0.0, zk),                                  # 0 keel
        (0.72 * w, zk + 0.12),                      # 1 chine: a nearly flat underside
        (0.96 * w, zk + 0.85),                      # 2 strake
        (w, zg),                                    # 3 gunwale
        (0.96 * w, zg + 0.3),                       # 4 rail top
        (0.9 * w, zd),                              # 5 deck side, tall
        (0.74 * w, zd + 0.05),                      # 6 footwell rim
        (0.62 * w, zd - fw),                        # 7 footwell floor
        (0.44 * w, zd - fw),                        # 8 floor to seat base
        (0.38 * w, zt - 0.1),                       # 9 seat-base wall top
        (0.0, zt),                                  # 10 centre
    ]


#            y     w     zk    zg    zd    zt    fw
SECTIONS = [
    (-7.2, 0.35, 1.25, 1.55, 1.8, 1.9, 0.0),      # sharp nose
    (-6.6, 1.25, 0.85, 1.7, 2.2, 2.4, 0.0),
    (-5.6, 2.05, 0.45, 1.75, 2.55, 2.85, 0.0),
    (-4.6, 2.6, 0.22, 1.8, 2.85, 3.3, 0.0),        # bow rising into the hood
    (-3.6, 2.88, 0.08, 1.82, 3.0, 3.75, 0.0),
    (-2.7, 3.0, 0.0, 1.85, 3.05, 3.98, 0.0),       # hood peak / console
    (-2.0, 3.04, 0.0, 1.85, 3.05, 3.6, 0.0),
    (-1.6, 3.05, 0.0, 1.85, 3.0, 3.25, 0.55),      # footwells begin, seat base
    (-0.4, 3.08, 0.0, 1.85, 2.98, 3.15, 0.65),
    (1.4, 3.08, 0.0, 1.85, 2.98, 3.15, 0.65),
    (3.2, 3.02, 0.02, 1.85, 2.98, 3.15, 0.65),
    (4.6, 2.9, 0.1, 1.85, 3.0, 3.2, 0.5),
    (5.6, 2.72, 0.22, 1.82, 3.02, 3.25, 0.0),      # rear deck, solid
    (6.7, 2.4, 0.42, 1.75, 2.85, 3.05, 0.0),
    (7.25, 2.0, 0.62, 1.65, 2.62, 2.8, 0.0),       # transom
]
mesh = bpy.data.meshes.new("Hovercraft_Body")
bm = bmesh.new()
rings = []
for y, w, zk, zg, zd, zt, fw in SECTIONS:
    half = outline(w, zk, zg, zd, zt, fw)
    pts = [(x, y, z) for x, z in half] + [(-x, y, z) for x, z in reversed(half[1:-1])]
    rings.append([bm.verts.new(p) for p in pts])
n = len(rings[0])
for r0, r1 in zip(rings, rings[1:]):
    for i in range(n):
        bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
bm.faces.new(list(reversed(rings[0])))
bm.faces.new(rings[-1])
bm.faces.ensure_lookup_table()
bm.normal_update()
# crease every hard line along the hull, and the ring at the hood peak, so the
# subdivided surface stays sharp-edged and panelled
crease = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
HARD = {1: 0.85, 2: 0.7, 3: 0.95, 4: 0.95, 5: 0.85, 6: 0.9, 7: 0.8, 8: 0.7, 9: 0.75}
for r0, r1 in zip(rings, rings[1:]):
    for idx, amount in HARD.items():
        for i in (idx, n - idx):
            e = bm.edges.get((r0[i], r1[i]))
            if e is not None:
                e[crease] = amount
for ring_idx in (5, 7, 12):                      # hood peak, seat-base step, rear deck step
    r = rings[ring_idx]
    for i in range(n):
        e = bm.edges.get((r[i], r[(i + 1) % n]))
        if e is not None:
            e[crease] = max(e[crease], 0.6)
# paint by region
mesh.materials.append(BLACK)
mesh.materials.append(PURPLE)
mesh.materials.append(WHITE)
GUNWALE = 1.85
for f in bm.faces:
    c = f.calc_center_median()
    nrm = f.normal
    if c.z < GUNWALE + 0.15:
        f.material_index = 0                                     # hull: black
    elif c.y < -1.5 and abs(nrm.x) > 0.5 and c.z < 3.1:
        f.material_index = 2                                     # bow side walls: white
    elif c.y < -1.5:
        f.material_index = 1                                     # hood and fairing: purple
    else:
        f.material_index = 0                                     # rear deck, footwells: black
bm.to_mesh(mesh)
bm.free()
mesh.shade_smooth()
body = bpy.data.objects.new("Hovercraft_Body", mesh)
scene.collection.objects.link(body)
attach(body)
sub = body.modifiers.new("Subdivision", "SUBSURF")
sub.levels = 2
sub.render_levels = 3


def loft(name, sections, mat, ring=28, p=2.6, subdiv=2, crease_amount=0.0):
    """A smooth closed body from (y, half_width, height_up, height_down, z_centre) sections."""
    m = bpy.data.meshes.new("Hovercraft_" + name)
    b = bmesh.new()
    rs = []
    for y, w, hu, hd, zc in sections:
        pts = []
        for i in range(ring):
            a = 2 * math.pi * i / ring
            cx, sz = math.cos(a), math.sin(a)
            x = w * math.copysign(abs(cx) ** (2 / p), cx)
            h = hu if sz >= 0 else hd
            z = zc + h * math.copysign(abs(sz) ** (2 / p), sz)
            pts.append(b.verts.new((x, y, z)))
        rs.append(pts)
    for r0, r1 in zip(rs, rs[1:]):
        for i in range(ring):
            b.faces.new((r0[i], r0[(i + 1) % ring], r1[(i + 1) % ring], r1[i]))
    b.faces.new(list(reversed(rs[0])))
    b.faces.new(rs[-1])
    if crease_amount:
        cl = b.edges.layers.float.get("crease_edge") or b.edges.layers.float.new("crease_edge")
        for r0, r1 in zip(rs, rs[1:]):
            for i in (0, ring // 2, ring // 4, 3 * ring // 4):
                e = b.edges.get((r0[i], r1[i]))
                if e is not None:
                    e[cl] = crease_amount
    b.to_mesh(m)
    b.free()
    m.shade_smooth()
    o = bpy.data.objects.new("Hovercraft_" + name, m)
    o.data.materials.append(mat)
    if subdiv:
        s = o.modifiers.new("Subdivision", "SUBSURF")
        s.levels = subdiv
        s.render_levels = subdiv + 1
    scene.collection.objects.link(o)
    return attach(o)


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0, segments=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.data.transform(Matrix.Diagonal((*size, 1.0)))
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = segments
        b.limit_method = "NONE"
    return attach(o)


def cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    return attach(o)


def tube(name, radius, depth, thickness, loc, mat, rot=(0, 0, 0), verts=40):
    m = bpy.data.meshes.new("Hovercraft_" + name)
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=False, segments=verts, radius1=radius, radius2=radius, depth=depth)
    b.to_mesh(m)
    b.free()
    m.shade_smooth()
    o = bpy.data.objects.new("Hovercraft_" + name, m)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    s = o.modifiers.new("Solidify", "SOLIDIFY")
    s.thickness = thickness
    s.offset = 0
    bv = o.modifiers.new("Bevel", "BEVEL")
    bv.width = 0.04
    bv.segments = 2
    scene.collection.objects.link(o)
    return attach(o)


# ------------------------------------------------------------ seating: one sculpted piece
# Rider cushion, a backrest rising out of it, a dip, the passenger cushion
# and a lower rear backrest, all one continuous surface. Purple on the top
# faces, black on the sides, with the cushion edges creased.
SEAT = [
    (-1.6, 0.3, 0.1, 0.5, 3.3),
    (-1.1, 0.85, 0.5, 0.6, 3.35),
    (0.2, 0.98, 0.6, 0.6, 3.38),
    (1.9, 0.98, 0.6, 0.6, 3.38),
    (2.3, 0.95, 0.9, 0.6, 3.48),
    (2.55, 0.9, 1.2, 0.6, 3.55),                 # rider backrest
    (2.8, 0.86, 1.15, 0.6, 3.55),
    (3.05, 0.9, 0.7, 0.6, 3.5),
    (3.6, 0.95, 0.75, 0.6, 3.45),                # passenger cushion, a step up
    (5.0, 0.95, 0.75, 0.6, 3.45),
    (5.35, 0.9, 1.0, 0.6, 3.5),                  # rear backrest
    (5.6, 0.8, 0.95, 0.6, 3.5),
    (5.85, 0.5, 0.45, 0.5, 3.4),
    (6.0, 0.2, 0.1, 0.4, 3.35),
]
seat = loft("Seat", SEAT, PURPLE, p=3.6, crease_amount=0.6)
seat.data.materials.append(BLACK)
sb = bmesh.new()
sb.from_mesh(seat.data)
sb.normal_update()
for f in sb.faces:
    f.material_index = 0 if abs(f.normal.z) > 0.35 else 1      # tops purple, sides black
sb.to_mesh(seat.data)
sb.free()
# footwell mats: ribbed rubber strips either side of the seat
for s in (-1, 1):
    for k in range(5):
        box("Mat%s%d" % ("L" if s < 0 else "R", k), (0.9, 0.6, 0.05), (s * 1.75, -0.8 + k * 1.15, 2.42), MAT, bevel=0.015, segments=1)

# ------------------------------------------------------------ the dash: one housing out of the hood
# A dash housing rises out of the hood with a flat shelf. Set into the front
# of the shelf is a hologram projector: a chrome ring with a purple emitter
# disc, a faint light cone, and a slowly turning holographic globe above it.
# Behind and above the hologram a screen block rises from the shelf, its face
# angled up at the rider. The handlebar stem is anchored into the back of the
# shelf, the windshield frame sits on the front lip, and the mirrors hang off
# short arms bolted to the housing sides. Nothing floats.
DASH = [
    (-4.5, 0.45, 0.12, 0.5, 3.7),
    (-4.1, 1.15, 0.42, 0.7, 3.85),
    (-3.4, 1.4, 0.5, 0.8, 3.9),
    (-2.5, 1.4, 0.5, 0.8, 3.9),
    (-1.95, 1.0, 0.35, 0.7, 3.85),
    (-1.72, 0.45, 0.12, 0.5, 3.8),
]
loft("Dash", DASH, BLACK, p=3.6, crease_amount=0.7)
SHELF = 4.38                                                  # top of the dash housing
# hologram projector
tube("HoloRing", 0.44, 0.1, 0.1, (0, -3.55, SHELF), CHROME, verts=40)
cylinder("HoloDisc", 0.36, 0.05, (0, -3.55, SHELF + 0.01), VIOLET, verts=40)
cone_mesh = bpy.data.meshes.new("Hovercraft_HoloCone")
cb = bmesh.new()
bmesh.ops.create_cone(cb, cap_ends=False, segments=32, radius1=0.34, radius2=0.42, depth=0.5)
cb.to_mesh(cone_mesh)
cb.free()
cone_mesh.shade_smooth()
cone = bpy.data.objects.new("Hovercraft_HoloCone", cone_mesh)
cone.location = (0, -3.55, SHELF + 0.28)
cone.data.materials.append(VIOLET_SOFT)
scene.collection.objects.link(cone)
attach(cone)
# the hologram itself: a wireframe globe with a bright core, slowly turning
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.3, location=(0, -3.55, SHELF + 0.6))
holo = bpy.context.object
holo.name = "Hovercraft_Hologram"
holo.data.materials.append(VIOLET_STRIP)
wf = holo.modifiers.new("Wire", "WIREFRAME")
wf.thickness = 0.018
attach(holo)
holo.animation_data_clear()
holo.rotation_euler = (0.3, 0, 0)
holo.keyframe_insert("rotation_euler", frame=scene.frame_start)
holo.rotation_euler = (0.3, 0, 2 * math.pi * (scene.frame_end - scene.frame_start) / 96.0)
holo.keyframe_insert("rotation_euler", frame=scene.frame_end)
for fc in holo.animation_data.action.layers[0].strips[0].channelbag(holo.animation_data.action_slot).fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, segments=16, ring_count=8, location=(0, -3.55, SHELF + 0.6))
core = bpy.context.object
core.name = "Hovercraft_HoloCore"
core.data.materials.append(VIOLET)
bpy.ops.object.shade_smooth()
attach(core)
# the screen: a tall upright panel rising from the shelf behind the hologram,
# facing the rider, with live readouts
SCREEN_Y = -2.6
box("ScreenBlock", (1.25, 0.32, 1.7), (0, SCREEN_Y, SHELF + 0.72), BLACK, bevel=0.05, segments=3)
box("ScreenPanel", (1.05, 0.03, 1.5), (0, SCREEN_Y + 0.165, SHELF + 0.74), SCREEN)
box("ScreenHeader", (0.9, 0.02, 0.08), (0, SCREEN_Y + 0.185, SHELF + 1.38), VIOLET_STRIP)
readouts = []
for i in range(5):                                                    # five bars that rise and fall
    readouts.append(box("Readout%d" % i, (0.5, 0.02, 0.09), (-0.2, SCREEN_Y + 0.185, SHELF + 1.18 - i * 0.16), VIOLET_STRIP))
scan = box("ScanLine", (0.95, 0.02, 0.03), (0, SCREEN_Y + 0.19, SHELF + 0.74), NEON)
ring_glyph = tube("ScreenRing", 0.16, 0.02, 0.03, (0.3, SCREEN_Y + 0.185, SHELF + 0.2), VIOLET_STRIP, rot=(math.radians(90), 0, 0), verts=24)
# reactive: bars breathe at different rates, the scan line sweeps, the panel pulses
panel_bsdf = SCREEN.node_tree.nodes["Principled BSDF"]
for f in range(scene.frame_start, scene.frame_end + 1, 2):
    t = f / FPS
    scene.frame_set(f)
    for i, bar in enumerate(readouts):
        width = 0.55 + 0.4 * math.sin(2 * math.pi * t / (1.3 + 0.37 * i) + i)
        bar.scale = (max(0.15, width), 1, 1)
        bar.location.x = -0.42 + 0.5 * bar.scale.x / 2
        bar.keyframe_insert("scale", index=0, frame=f)
        bar.keyframe_insert("location", index=0, frame=f)
    sweep = (t / 1.8) % 1.0
    scan.location.z = SHELF + 0.05 + 1.38 * (sweep if int(t / 1.8) % 2 == 0 else 1.0 - sweep)
    scan.keyframe_insert("location", index=2, frame=f)
    ring_glyph.rotation_euler.y = 2 * math.pi * t / 2.5
    ring_glyph.keyframe_insert("rotation_euler", index=1, frame=f)
    panel_bsdf.inputs["Emission Strength"].default_value = 1.4 + 0.5 * math.sin(2 * math.pi * t / 2.0)
    panel_bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
scene.frame_set(scene.frame_start)
# handlebars anchored into the back of the shelf: a chamfered stem and yoke
# with winged grips angled out and forward, lit tips and a lit slot
cylinder("StemBase", 0.26, 0.12, (0, -2.08, SHELF + 0.02), CHROME, verts=8)
box("BarStem", (0.26, 0.26, 0.8), (0, -2.0, SHELF + 0.36), DARK, rot=(math.radians(-22), 0, 0), bevel=0.05, segments=2)
BAR_Z = SHELF + 0.74
box("Yoke", (1.1, 0.55, 0.32), (0, -1.86, BAR_Z), BLACK, bevel=0.07, segments=3)
box("YokeSlot", (0.7, 0.04, 0.08), (0, -2.14, BAR_Z + 0.02), VIOLET_STRIP)
box("YokeCap", (0.5, 0.35, 0.06), (0, -1.86, BAR_Z + 0.19), CHROME, bevel=0.02, segments=1)
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    # each wing: an angled arm out of the yoke, then a grip, then a lit tip
    ang = math.radians(-24 * s)                       # swept forward
    tilt = math.radians(8 * s)                        # tips a little lower than the yoke
    box("BarArm" + side, (1.0, 0.16, 0.16), (s * 0.95, -1.98, BAR_Z - 0.04), DARK, rot=(0, tilt, ang), bevel=0.04, segments=2)
    cylinder("Grip" + side, 0.15, 0.85, (s * 1.78, -2.3, BAR_Z - 0.16), GRIP, rot=(0, math.radians(90) + tilt, ang), verts=16)
    cylinder("GripTip" + side, 0.16, 0.08, (s * 2.2, -2.47, BAR_Z - 0.22), VIOLET_STRIP, rot=(0, math.radians(90) + tilt, ang), verts=16)
    box("Lever" + side, (0.7, 0.05, 0.14), (s * 1.7, -2.6, BAR_Z - 0.3), DARK, rot=(0, tilt, ang), bevel=0.02, segments=1)
# windshield: its frame sits on the front lip of the housing
box("ShieldBase", (2.3, 0.14, 0.1), (0, -4.15, SHELF - 0.02), CHROME)
box("Windshield", (2.2, 0.05, 1.0), (0, -4.15 + 0.31, SHELF + 0.4), GLASS, rot=(math.radians(-38), 0, 0), bevel=0.02, segments=1)
box("ShieldFrame", (2.3, 0.08, 0.1), (0, -4.15 + 0.62, SHELF + 0.79), CHROME, rot=(math.radians(-38), 0, 0))


def hull_line(name, idx, y_from, y_to, dz, height, mat, inset=1.0):
    """A thin emissive band following one of the hull's hard lines (outline
    point `idx`) between y_from and y_to, on both sides."""
    m = bpy.data.meshes.new("Hovercraft_" + name)
    b = bmesh.new()
    prev = None
    for y, w, zk, zg, zd, zt, fw in SECTIONS:
        if y < y_from or y > y_to:
            continue
        px, pz = outline(w, zk, zg, zd, zt, fw)[idx]
        pts = [b.verts.new((sgn * px * inset, y, pz + dz + h)) for sgn in (1, -1) for h in (0.0, height)]
        if prev:
            b.faces.new((prev[0], prev[1], pts[1], pts[0]))
            b.faces.new((pts[2], pts[3], prev[3], prev[2]))
        prev = pts
    b.to_mesh(m)
    b.free()
    o = bpy.data.objects.new("Hovercraft_" + name, m)
    o.data.materials.append(mat)
    sm = o.modifiers.new("Solidify", "SOLIDIFY")
    sm.thickness = 0.07
    sm.offset = 1
    scene.collection.objects.link(o)
    return attach(o)


hull_line("ChineNeon", 1, -6.7, 7.3, 0.02, 0.09, NEON, inset=1.01)     # neon along both chines, full length
hull_line("DeckNeon", 5, -6.0, -1.5, -0.32, 0.08, VIOLET_STRIP)        # and along the bow sides
hull_line("RearNeon", 5, 4.5, 7.3, -0.3, 0.06, VIOLET_STRIP)
# rub rail all round the gunwale, following the hull outline
rail_mesh = bpy.data.meshes.new("Hovercraft_RubRail")
rb = bmesh.new()
prev = None
for y, w, zk, zg, zd, zt, fw in SECTIONS[1:-1]:
    pts = [rb.verts.new((s * w * 1.01, y, zg + dz)) for s in (1, -1) for dz in (0.04, 0.3)]
    if prev:
        rb.faces.new((prev[0], prev[1], pts[1], pts[0]))
        rb.faces.new((pts[2], pts[3], prev[3], prev[2]))
    prev = pts
rb.to_mesh(rail_mesh)
rb.free()
rail = bpy.data.objects.new("Hovercraft_RubRail", rail_mesh)
rail.data.materials.append(RUBBER)
solid = rail.modifiers.new("Solidify", "SOLIDIFY")
solid.thickness = 0.12
solid.offset = 1
rail.data.shade_smooth()
scene.collection.objects.link(rail)
attach(rail)

# ------------------------------------------------------------ winglets: swept fins at the rear quarters
def fin(name, pts, thickness, loc, rot, mat):
    """A flat fin from a 2D outline (x, y), extruded `thickness` in z."""
    m = bpy.data.meshes.new("Hovercraft_" + name)
    b = bmesh.new()
    lo = [b.verts.new((x, y, -thickness / 2)) for x, y in pts]
    hi = [b.verts.new((x, y, thickness / 2)) for x, y in pts]
    b.faces.new(list(reversed(lo)))
    b.faces.new(hi)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        b.faces.new((lo[i], lo[j], hi[j], hi[i]))
    b.to_mesh(m)
    b.free()
    o = bpy.data.objects.new("Hovercraft_" + name, m)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    bv = o.modifiers.new("Bevel", "BEVEL")
    bv.width = 0.05
    bv.segments = 2
    scene.collection.objects.link(o)
    return attach(o)


for sgn in (-1, 1):
    side = "L" if sgn < 0 else "R"
    # rooted inside the hull side, swept back, canted down a little
    fin("Wing" + side, [(0, -1.2), (sgn * 1.6, -0.1), (sgn * 2.0, 0.7), (sgn * 1.2, 1.1), (0, 1.2)], 0.14,
        (sgn * 2.35, 4.3, 2.3), (0, math.radians(12 * sgn), 0), BLACK)
    box("WingEdge" + side, (0.05, 0.9, 0.05), (sgn * 4.3, 4.9, 1.95), NEON, rot=(0, math.radians(12 * sgn), math.radians(-30 * sgn)))

# ------------------------------------------------------------ stern: thruster bay, step, handle
# a recessed housing in the transom with a ring nozzle and a glowing core
box("ThrusterBay", (2.6, 0.9, 1.3), (0, 7.05, 1.9), DARK, bevel=0.06, segments=2)
tube("Nozzle", 0.55, 0.7, 0.12, (0, 7.55, 1.9), CHROME, rot=(math.radians(90), 0, 0))
cylinder("NozzleCore", 0.42, 0.08, (0, 7.72, 1.9), NEON, rot=(math.radians(90), 0, 0))
glow_cone = bpy.data.meshes.new("Hovercraft_Exhaust")
gb = bmesh.new()
bmesh.ops.create_cone(gb, cap_ends=False, segments=32, radius1=0.42, radius2=0.2, depth=1.6)
gb.to_mesh(glow_cone)
gb.free()
glow_cone.shade_smooth()
exhaust = bpy.data.objects.new("Hovercraft_Exhaust", glow_cone)
exhaust.location = (0, 8.55, 1.9)
exhaust.rotation_euler = (math.radians(-90), 0, 0)
exhaust.data.materials.append(VIOLET_SOFT)
scene.collection.objects.link(exhaust)
attach(exhaust)
for s in (-1, 1):
    tube("SideNozzle%s" % ("L" if s < 0 else "R"), 0.22, 0.5, 0.06, (s * 1.0, 7.5, 1.9), DARK, rot=(math.radians(90), 0, 0), verts=20)
    cylinder("SideCore%s" % ("L" if s < 0 else "R"), 0.16, 0.06, (s * 1.0, 7.62, 1.9), VIOLET, rot=(math.radians(90), 0, 0), verts=20)
box("Step", (2.3, 0.9, 0.16), (0, 7.55, 2.7), RUBBER, bevel=0.05, segments=2)
cylinder("GrabHandle", 0.07, 1.7, (0, 6.7, 3.55), DARK, rot=(0, math.radians(90), 0), verts=10)
for s in (-1, 1):
    cylinder("GrabPost%s" % ("L" if s < 0 else "R"), 0.07, 0.45, (s * 0.85, 6.7, 3.35), DARK, verts=10)
box("TailStrip", (1.9, 0.06, 0.12), (0, 7.4, 2.5), VIOLET_STRIP)
cylinder("BowEye", 0.14, 0.4, (0, -7.0, 1.45), DARK, rot=(0, math.radians(90), 0), verts=12)

# ------------------------------------------------------------ the hover: a purple pad and its light
# two anti-grav pods under the hull, each a dark drum with a neon ring and a
# glowing core, plus a smaller one under the bow
PODS = ((-1.55, -2.4, 0.7), (1.55, -2.4, 0.7), (-1.85, 0.9, 0.85), (1.85, 0.9, 0.85),
        (-1.5, 4.1, 0.7), (1.5, 4.1, 0.7), (0, -5.3, 0.5))
for i, (px, py, r) in enumerate(PODS):
    cylinder("Pod%d" % i, r, 0.42, (px, py, -0.05), PANEL if False else BLACK, verts=40)
    tube("PodRing%d" % i, r + 0.02, 0.12, 0.1, (px, py, -0.2), NEON, verts=40)
    cylinder("PodCore%d" % i, r * 0.72, 0.06, (px, py, -0.28), VIOLET, verts=40)
for i, (px, py, r) in enumerate(PODS):
    light = bpy.data.lights.new("Hovercraft_HoverLight%d" % i, "POINT")
    light.color = (0.6, 0.25, 1.0)
    light.energy = 110
    light.shadow_soft_size = 0.8
    lo = bpy.data.objects.new("Hovercraft_HoverLight%d" % i, light)
    lo.location = (px, py, -0.4)
    col.objects.link(lo)
    lo.parent = root
    lo.matrix_parent_inverse.identity()
HOVER_Z = 2.7
glow = cylinder("HoverGlow", 2.6, 0.02, (0, 0.6, -HOVER_Z + 0.05), VIOLET_SOFT, verts=48)
glow.scale = (1, 2.2, 1)

# ------------------------------------------------------------ hovering
root.location = (0, 0, HOVER_Z)
root.animation_data_clear()
for f in range(scene.frame_start, scene.frame_end + 1):
    t = f / FPS
    scene.frame_set(f)
    root.location.z = HOVER_Z + 0.14 * math.sin(2 * math.pi * t / 2.4) + 0.04 * math.sin(2 * math.pi * t / 0.9)
    root.rotation_euler = (0.012 * math.sin(2 * math.pi * t / 3.1), 0.014 * math.sin(2 * math.pi * t / 2.7 + 1.0), root.rotation_euler.z)
    root.keyframe_insert("location", index=2, frame=f)
    root.keyframe_insert("rotation_euler", frame=f)
scene.frame_set(scene.frame_start)

bpy.ops.object.select_all(action="DESELECT")
print("flying jetski built:", len([o for o in col.objects if o.name.startswith("Hovercraft")]), "objects")
