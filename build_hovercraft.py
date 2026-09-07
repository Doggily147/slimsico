"""A flying jetski for Yellow, modelled after a small sit-down runabout: a
chunky V hull with chines and flared gunwales, a stepped deck, a rising hood
with a handlebar pod, a long saddle seat and a boarding step at the stern. The
body is ONE smooth mesh built from hull cross-sections, painted by region:
purple hood and fairing, black hull and rear deck, white bow sides. It flies:
no jet pump, instead a purple hover pad underneath that lights the ground, and
a gentle bob keyed across the scene.

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


def material(name, rgb, rough=0.5, metallic=0.0, emit=None):
    m = bpy.data.materials.get("Hover_" + name) or bpy.data.materials.new("Hover_" + name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = 0.0
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*rgb, 1)
    return m


PURPLE = material("Purple", (0.42, 0.08, 0.72), rough=0.32)
PURPLE.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.6   # glossy gelcoat
BLACK = material("Black", (0.02, 0.02, 0.025), rough=0.45)
BLACK.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.4
WHITE = material("White", (0.92, 0.92, 0.9), rough=0.35)
WHITE.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.5
RUBBER = material("Rubber", (0.06, 0.06, 0.065), rough=0.9)
GRIP = material("Grip", (0.5, 0.12, 0.8), rough=0.8)
DARK = material("DarkMetal", (0.12, 0.12, 0.13), rough=0.5, metallic=0.7)
SCREEN = material("Screen", (0.04, 0.02, 0.08), rough=0.3, emit=((0.6, 0.3, 1.0), 1.2))
VIOLET = material("HoverLight", (0.7, 0.3, 1.0), rough=0.3, emit=((0.65, 0.25, 1.0), 9))
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
# A cross-section is described by a few hull measurements; `outline` turns it
# into the half-section from the keel up over the deck, which is mirrored.
#   w   half width at the gunwale (the widest point)
#   zk  keel height, zg gunwale height, zd deck height at the edge, zt deck
#   height at the centre, hood: how much the centre bulges (hood / seat base)
def outline(w, zk, zg, zd, zt):
    return [
        (0.0, zk),                       # keel
        (0.72 * w, zk + 0.32),           # hard chine
        (0.98 * w, zk + 1.15),           # topsides, nearly vertical
        (w, zg),                         # gunwale, widest
        (0.97 * w, zg + 0.28),           # rub rail top
        (0.9 * w, zd),                   # deck side wall, tall
        (0.55 * w, zt - 0.08),           # deck shoulder
        (0.0, zt),                       # deck centre
    ]


#            y     w     zk    zg    zd    zt
SECTIONS = [
    (-7.15, 0.4, 1.3, 1.6, 1.8, 1.9),         # nose
    (-6.6, 1.3, 0.9, 1.7, 2.15, 2.35),
    (-5.6, 2.1, 0.5, 1.75, 2.5, 2.75),
    (-4.5, 2.65, 0.25, 1.8, 2.8, 3.2),         # bow rising into the hood
    (-3.4, 2.9, 0.1, 1.82, 2.95, 3.65),
    (-2.5, 3.0, 0.0, 1.85, 3.0, 3.9),          # hood peak / console
    (-1.7, 3.05, 0.0, 1.85, 3.0, 3.25),        # drops to the seat base
    (-0.5, 3.08, 0.0, 1.85, 2.95, 3.05),
    (1.2, 3.08, 0.0, 1.85, 2.95, 3.05),
    (2.9, 3.02, 0.02, 1.85, 2.95, 3.05),
    (4.4, 2.9, 0.1, 1.85, 2.95, 3.1),
    (5.7, 2.7, 0.22, 1.8, 2.95, 3.1),          # rear deck
    (6.8, 2.35, 0.42, 1.75, 2.8, 2.95),
    (7.25, 1.9, 0.62, 1.65, 2.6, 2.75),        # transom
]
mesh = bpy.data.meshes.new("Hovercraft_Body")
bm = bmesh.new()
rings = []
for y, w, zk, zg, zd, zt in SECTIONS:
    half = outline(w, zk, zg, zd, zt)
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
# crease the hard lines so subdivision keeps them crisp: chine, gunwale, rub
# rail and the deck edge run the length of the hull
crease = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
HARD = {1: 0.75, 3: 0.9, 4: 0.9, 5: 0.6}          # outline point index -> crease
for r0, r1 in zip(rings, rings[1:]):
    for idx, amount in HARD.items():
        for i in (idx, n - idx):                    # both sides of the mirror
            e = bm.edges.get((r0[i], r1[i]))
            if e is not None:
                e[crease] = amount
# paint by region: black hull and rear, purple hood and fairing, white bow sides
mesh.materials.append(BLACK)
mesh.materials.append(PURPLE)
mesh.materials.append(WHITE)
GUNWALE = 1.85
for f in bm.faces:
    c = f.calc_center_median()
    nrm = f.normal
    if c.z < GUNWALE + 0.15:
        f.material_index = 0                                     # hull: black
    elif c.y < -1.4 and abs(nrm.x) > 0.55:
        f.material_index = 2                                     # bow side walls: white
    elif c.y < -1.4:
        f.material_index = 1                                     # hood and fairing: purple
    else:
        f.material_index = 0                                     # rear deck and sides: black
bm.to_mesh(mesh)
bm.free()
mesh.shade_smooth()
body = bpy.data.objects.new("Hovercraft_Body", mesh)
scene.collection.objects.link(body)
attach(body)
sub = body.modifiers.new("Subdivision", "SUBSURF")
sub.levels = 2
sub.render_levels = 3


def loft(name, sections, mat, ring=28, p=2.6, subdiv=2):
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


# ------------------------------------------------------------ seat, pod, bars, details
# the saddle: long, rounded, purple, sitting down into the deck
SEAT = [
    (-1.8, 0.25, 0.1, 0.4, 3.45),
    (-1.2, 0.8, 0.7, 0.6, 3.55),
    (0.0, 0.95, 0.88, 0.7, 3.62),
    (1.6, 0.98, 0.92, 0.7, 3.66),
    (3.2, 0.98, 0.88, 0.7, 3.66),
    (4.6, 0.92, 0.75, 0.7, 3.62),
    (5.4, 0.68, 0.45, 0.6, 3.5),
    (5.65, 0.28, 0.12, 0.4, 3.4),
]
loft("Seat", SEAT, PURPLE, p=3.4)
# a black seat bolster strip down each side of the saddle
for s in (-1, 1):
    box("SeatTrim%s" % ("L" if s < 0 else "R"), (0.14, 6.2, 0.3), (s * 0.95, 1.9, 3.35), BLACK, bevel=0.04, segments=2)
# handlebar pod on the hood: a rounded black housing with a small screen
loft("Pod", [(-3.6, 0.25, 0.1, 0.1, 3.95), (-3.2, 0.7, 0.35, 0.3, 4.05), (-2.6, 0.85, 0.42, 0.35, 4.1),
             (-2.0, 0.7, 0.32, 0.3, 4.05), (-1.75, 0.3, 0.1, 0.1, 4.0)], BLACK, p=2.6)
box("PodScreen", (0.9, 0.06, 0.4), (0, -3.05, 4.35), SCREEN, rot=(math.radians(-35), 0, 0))
# handlebars: a bar across on a short stem, angled back, purple grips, black levers
cylinder("BarStem", 0.13, 0.9, (0, -2.7, 4.5), DARK, rot=(math.radians(-25), 0, 0), verts=14)
cylinder("BarCross", 0.1, 3.4, (0, -2.5, 4.92), DARK, rot=(0, math.radians(90), 0), verts=14)
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    cylinder("Grip" + side, 0.15, 0.9, (s * 1.35, -2.5, 4.92), GRIP, rot=(0, math.radians(90), 0), verts=14)
    cylinder("Lever" + side, 0.05, 0.9, (s * 1.3, -2.85, 4.82), DARK, rot=(0, math.radians(90), 0), verts=8)
    # mirror pods either side of the hood
    box("Mirror" + side, (0.45, 0.28, 0.32), (s * 1.8, -3.3, 3.8), BLACK, bevel=0.1, segments=3)
# rub rail all round the gunwale: a rubber strip that follows the hull outline
rail_mesh = bpy.data.meshes.new("Hovercraft_RubRail")
rb = bmesh.new()
prev = None
for y, w, zk, zg, zd, zt in SECTIONS[1:-1]:
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
# stern: boarding step and a grab handle
box("Step", (2.2, 0.9, 0.16), (0, 7.5, 2.5), RUBBER, bevel=0.05, segments=2)
cylinder("GrabHandle", 0.07, 1.6, (0, 6.9, 3.45), DARK, rot=(0, math.radians(90), 0), verts=10)
for s in (-1, 1):
    cylinder("GrabPost%s" % ("L" if s < 0 else "R"), 0.07, 0.4, (s * 0.8, 6.9, 3.25), DARK, verts=10)
# bow: a small eye and a white nose cap line
cylinder("BowEye", 0.14, 0.4, (0, -6.95, 1.5), DARK, rot=(0, math.radians(90), 0), verts=12)

# ------------------------------------------------------------ the hover: a purple pad and its light
cylinder("HoverPad", 1.6, 0.14, (0, 0.6, -0.02), VIOLET, verts=48)
pad = bpy.data.objects["Hovercraft_HoverPad"]
pad.scale = (1, 2.4, 1)
cylinder("HoverPadRim", 1.75, 0.22, (0, 0.6, 0.06), BLACK, verts=48)
bpy.data.objects["Hovercraft_HoverPadRim"].scale = (1, 2.4, 1)
for i, (px, py) in enumerate(((0, -3.2), (0, 0.6), (0, 4.2))):
    light = bpy.data.lights.new("Hovercraft_HoverLight%d" % i, "POINT")
    light.color = (0.6, 0.25, 1.0)
    light.energy = 260
    light.shadow_soft_size = 0.8
    lo = bpy.data.objects.new("Hovercraft_HoverLight%d" % i, light)
    lo.location = (px, py, -0.4)
    col.objects.link(lo)
    lo.parent = root
    lo.matrix_parent_inverse.identity()
HOVER_Z = 2.2
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
