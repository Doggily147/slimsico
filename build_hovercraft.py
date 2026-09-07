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
        (0.7 * w, zk + 0.3),                        # 1 chine
        (0.96 * w, zk + 0.9),                       # 2 strake
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


# ------------------------------------------------------------ seat: two tiers, flat-topped, black trim
SEAT = [
    (-1.7, 0.25, 0.1, 0.4, 3.5),
    (-1.2, 0.82, 0.72, 0.6, 3.6),
    (0.0, 0.95, 0.9, 0.7, 3.66),
    (1.8, 0.98, 0.92, 0.7, 3.7),
    (3.0, 0.98, 0.9, 0.7, 3.7),
    (3.3, 0.98, 1.15, 0.7, 3.75),                 # step up to the rear tier
    (4.6, 0.95, 1.1, 0.7, 3.75),
    (5.4, 0.7, 0.6, 0.6, 3.6),
    (5.65, 0.3, 0.15, 0.4, 3.5),
]
loft("Seat", SEAT, PURPLE, p=3.8, crease_amount=0.6)
for s in (-1, 1):
    box("SeatTrim%s" % ("L" if s < 0 else "R"), (0.12, 6.4, 0.34), (s * 0.98, 1.95, 3.4), BLACK, bevel=0.03, segments=2)
# footwell mats: ribbed rubber strips either side of the seat
for s in (-1, 1):
    for k in range(6):
        box("Mat%s%d" % ("L" if s < 0 else "R", k), (0.9, 0.55, 0.05), (s * 1.75, -1.0 + k * 1.05, 2.42), MAT, bevel=0.015, segments=1)

# ------------------------------------------------------------ console: pod, display, windshield, bars
loft("Pod", [(-3.8, 0.3, 0.1, 0.1, 4.0), (-3.3, 0.85, 0.4, 0.35, 4.1), (-2.7, 1.0, 0.5, 0.4, 4.15),
             (-2.1, 0.85, 0.38, 0.35, 4.1), (-1.85, 0.35, 0.12, 0.12, 4.02)], BLACK, p=3.4, crease_amount=0.5)
# console, front to back: windshield, then the display angled up at the
# rider, then the handlebars, all above the pod
box("Windshield", (2.1, 0.05, 0.95), (0, -3.95, 4.72), GLASS, rot=(math.radians(-42), 0, 0), bevel=0.02, segments=1)
box("ShieldFrame", (2.2, 0.08, 0.1), (0, -4.27, 5.08), CHROME, rot=(math.radians(-42), 0, 0))
box("MonitorBezel", (1.7, 0.16, 1.0), (0, -3.2, 4.85), BLACK, rot=(math.radians(-35), 0, 0), bevel=0.04, segments=2)
box("Monitor", (1.5, 0.06, 0.82), (0, -3.12, 4.86), SCREEN, rot=(math.radians(-35), 0, 0))
for i in range(3):                                                    # readout bars on the screen
    box("Readout%d" % i, (0.35 + 0.25 * i, 0.02, 0.06), (-0.45 + 0.06 * i, -3.085 + 0.1 * i, 5.12 - i * 0.2), VIOLET_STRIP,
        rot=(math.radians(-35), 0, 0))
cylinder("BarStem", 0.13, 0.9, (0, -2.55, 4.45), DARK, rot=(math.radians(-25), 0, 0), verts=14)
cylinder("BarCross", 0.1, 3.4, (0, -2.35, 4.85), DARK, rot=(0, math.radians(90), 0), verts=14)
cylinder("BarClamp", 0.18, 0.5, (0, -2.35, 4.85), CHROME, rot=(0, math.radians(90), 0), verts=14)
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    cylinder("Grip" + side, 0.15, 0.9, (s * 1.35, -2.35, 4.85), GRIP, rot=(0, math.radians(90), 0), verts=14)
    cylinder("Lever" + side, 0.05, 0.9, (s * 1.3, -2.7, 4.75), DARK, rot=(0, math.radians(90), 0), verts=8)
    box("Mirror" + side, (0.5, 0.3, 0.34), (s * 1.85, -3.5, 3.85), BLACK, bevel=0.06, segments=2)
    box("MirrorGlass" + side, (0.36, 0.03, 0.22), (s * 1.85, -3.34, 3.87), CHROME)
    # angular intake vents on the hood sides
    for k in range(3):
        box("Vent%s%d" % (side, k), (0.55, 0.12, 0.06), (s * 2.1, -4.6 + k * 0.32, 3.05 + k * 0.06), RUBBER,
            rot=(0, math.radians(-12 * s), 0))


def hull_strip(name, y_from, y_to, dz, height, mat):
    """A thin emissive band that follows the deck-side line of the hull."""
    m = bpy.data.meshes.new("Hovercraft_" + name)
    b = bmesh.new()
    prev = None
    for y, w, zk, zg, zd, zt, fw in SECTIONS:
        if y < y_from or y > y_to:
            continue
        pts = [b.verts.new((sgn * w * 0.905, y, zd + dz + h)) for sgn in (1, -1) for h in (0.0, height)]
        if prev:
            b.faces.new((prev[0], prev[1], pts[1], pts[0]))
            b.faces.new((pts[2], pts[3], prev[3], prev[2]))
        prev = pts
    b.to_mesh(m)
    b.free()
    o = bpy.data.objects.new("Hovercraft_" + name, m)
    o.data.materials.append(mat)
    sm = o.modifiers.new("Solidify", "SOLIDIFY")
    sm.thickness = 0.06
    sm.offset = 1
    scene.collection.objects.link(o)
    return attach(o)


hull_strip("HoodStrip", -6.0, -1.5, -0.32, 0.08, VIOLET_STRIP)          # purple line along the bow sides
hull_strip("RearStrip", 4.5, 7.3, -0.3, 0.06, VIOLET_STRIP)             # and along the rear quarters
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

# ------------------------------------------------------------ stern: thruster bay, step, handle
# a recessed housing in the transom with a ring nozzle and a glowing core
box("ThrusterBay", (2.6, 0.9, 1.3), (0, 7.05, 1.9), DARK, bevel=0.06, segments=2)
tube("Nozzle", 0.55, 0.7, 0.12, (0, 7.55, 1.9), CHROME, rot=(math.radians(90), 0, 0))
cylinder("NozzleCore", 0.42, 0.08, (0, 7.72, 1.9), VIOLET, rot=(math.radians(90), 0, 0))
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
cylinder("HoverPad", 1.6, 0.14, (0, 0.6, -0.02), VIOLET, verts=48)
bpy.data.objects["Hovercraft_HoverPad"].scale = (1, 2.4, 1)
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
