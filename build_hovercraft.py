"""A futuristic hover-jetski for Yellow: a flying-car style craft with a
pointed nose, a sleek lofted hull, a saddle seat and handlebars, a low tinted
cowl, swept side sponsons with light strips, twin glowing rear thrusters with a
tail fin, and repulsor pads underneath that light the ground. It hovers above
the plate with a gentle bob.

Primary colour dark grey, metallic; accents in cyan light, a red tail strip.
Everything hangs off the empty "Hovercraft" so the craft can be animated as one
thing. Run inside Blender with slimsico.blend open. Re-running replaces it.
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
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    else:
        bsdf.inputs["Emission Strength"].default_value = 0.0
    m.diffuse_color = (*rgb, 1)
    return m


GREY = material("Body", (0.11, 0.12, 0.13), rough=0.38, metallic=0.55)
PANEL = material("Panel", (0.05, 0.055, 0.06), rough=0.5, metallic=0.4)
SEAT = material("Seat", (0.05, 0.05, 0.055), rough=0.8)
CHROME = material("Chrome", (0.75, 0.77, 0.8), rough=0.15, metallic=1.0)
GLASS = material("Glass", (0.3, 0.55, 0.7), rough=0.05, emit=((0.25, 0.5, 0.7), 0.3))
CYAN = material("Cyan", (0.2, 0.9, 1.0), rough=0.3, emit=((0.2, 0.85, 1.0), 8))
CYAN_SOFT = material("CyanSoft", (0.2, 0.8, 1.0), rough=0.3, emit=((0.2, 0.8, 1.0), 3))
REDLIGHT = material("Tail", (0.9, 0.1, 0.1), rough=0.3, emit=((1.0, 0.12, 0.08), 6))
WHITELIGHT = material("Headlight", (1, 1, 1), rough=0.3, emit=((0.9, 0.95, 1.0), 10))

root = bpy.data.objects.new("Hovercraft", None)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 3
col.objects.link(root)


def attach(o, parent=None):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.parent = parent or root
    o.matrix_parent_inverse.identity()          # positions are given in the craft's own frame
    return o


def loft(name, sections, mat, ring=32, p=2.4, subdiv=2):
    """A smooth body from cross-sections along Y. Each section is
    (y, half_width, height_up, height_down, z_centre); the section outline is a
    squircle, so the body reads as sleek panels rather than a tube."""
    mesh = bpy.data.meshes.new("Hovercraft_" + name)
    bm = bmesh.new()
    rings = []
    for y, w, hu, hd, zc in sections:
        pts = []
        for i in range(ring):
            a = 2 * math.pi * i / ring
            c, s = math.cos(a), math.sin(a)
            x = w * math.copysign(abs(c) ** (2 / p), c)
            h = hu if s >= 0 else hd
            z = zc + h * math.copysign(abs(s) ** (2 / p), s)
            pts.append(bm.verts.new((x, y, z)))
        rings.append(pts)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(ring):
            bm.faces.new((r0[i], r0[(i + 1) % ring], r1[(i + 1) % ring], r1[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    o = bpy.data.objects.new("Hovercraft_" + name, mesh)
    o.data.materials.append(mat)
    if subdiv:
        sub = o.modifiers.new("Subdivision", "SUBSURF")
        sub.levels = subdiv
        sub.render_levels = subdiv + 1
    scene.collection.objects.link(o)
    return attach(o)


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0, segments=3, parent=None):
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
    return attach(o, parent)


def cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=32, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    return attach(o, parent)


def sphere(name, radius, loc, mat, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return attach(o, parent)


def wedge(name, length, width, height, loc, mat, rot=(0, 0, 0), taper=0.15, parent=None):
    """A swept fin/wing: a box whose far end narrows, bevelled, smooth."""
    mesh = bpy.data.meshes.new("Hovercraft_" + name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        if v.co.x > 0:                                   # far end tapers
            v.co.y *= taper
            v.co.z *= taper * 2.5
        v.co.x *= length
        v.co.y *= width
        v.co.z *= height
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new("Hovercraft_" + name, mesh)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = 0.12
    b.segments = 4
    b.limit_method = "NONE"
    mesh.shade_smooth()
    scene.collection.objects.link(o)
    return attach(o, parent)


# ------------------------------------------------------------ the hull (jetski shape, pointed nose)
# The craft points along -Y. Length about 15 studs, width up to 4.6.
HULL = [
    (-7.4, 0.06, 0.04, 0.04, 1.05),   # the point
    (-6.7, 0.55, 0.28, 0.22, 1.05),
    (-5.6, 1.15, 0.52, 0.42, 1.05),
    (-4.2, 1.75, 0.75, 0.6, 1.08),
    (-2.6, 2.15, 0.92, 0.72, 1.1),
    (-0.8, 2.3, 1.0, 0.8, 1.1),
    (1.2, 2.3, 1.0, 0.8, 1.1),
    (3.2, 2.2, 0.95, 0.78, 1.12),
    (5.0, 1.95, 0.85, 0.7, 1.15),
    (6.4, 1.5, 0.65, 0.55, 1.2),
    (7.3, 1.05, 0.45, 0.4, 1.25),
    (7.6, 0.75, 0.3, 0.28, 1.25),
]
loft("Hull", HULL, GREY)
# a darker belly pan under the hull, slightly inset, that carries the repulsors
BELLY = [(y, w * 0.96, 0.05, hd * 0.9 + 0.06, zc) for (y, w, hu, hd, zc) in HULL[1:-1]]
loft("BellyPan", BELLY, PANEL)
# saddle seat rising out of the deck
SADDLE = [
    (-2.4, 0.08, 0.04, 0.04, 2.0),
    (-1.6, 0.65, 0.42, 0.25, 2.02),
    (-0.4, 0.95, 0.62, 0.3, 2.06),
    (1.4, 1.05, 0.72, 0.3, 2.1),
    (3.2, 1.05, 0.7, 0.3, 2.1),
    (4.8, 0.9, 0.55, 0.3, 2.08),
    (5.6, 0.5, 0.25, 0.2, 2.05),
    (5.8, 0.15, 0.06, 0.06, 2.05),
]
loft("Saddle", SADDLE, SEAT, p=2.8)
# forward cowl: a low hump in front of the rider that carries the screen and bars
COWL = [
    (-5.4, 0.08, 0.04, 0.04, 1.95),
    (-4.8, 0.7, 0.35, 0.2, 2.0),
    (-4.0, 1.15, 0.6, 0.25, 2.05),
    (-3.0, 1.3, 0.75, 0.25, 2.1),
    (-2.2, 1.15, 0.6, 0.25, 2.1),
    (-1.9, 0.6, 0.2, 0.2, 2.1),
]
loft("Cowl", COWL, GREY)
box("Windscreen", (2.2, 0.05, 1.1), (0, -3.05, 2.98), GLASS, rot=(math.radians(-40), 0, 0), bevel=0.03, segments=1)
box("ScreenFrame", (2.4, 0.09, 0.12), (0, -3.4, 3.4), CHROME, rot=(math.radians(-40), 0, 0))
# handlebars
cylinder("BarStem", 0.11, 1.3, (0, -2.5, 3.1), CHROME, rot=(math.radians(-30), 0, 0), verts=12)
cylinder("BarCross", 0.09, 2.6, (0, -2.85, 3.66), CHROME, rot=(0, math.radians(90), 0), verts=12)
for s in (-1, 1):
    cylinder("Grip%s" % ("L" if s < 0 else "R"), 0.14, 0.7, (s * 1.15, -2.85, 3.66), SEAT, rot=(0, math.radians(90), 0), verts=12)
# side sponsons: swept wings with a cyan light strip along the leading edge
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    wedge("Sponson" + side, 3.6, 3.2, 0.42, (s * 3.3, 2.2, 1.05), GREY,
          rot=(math.radians(-8 * s), math.radians(4), math.radians(-18 * s)))
    box("SponsonLight" + side, (1.9, 0.14, 0.12), (s * 3.6, 0.85, 1.22), CYAN, rot=(0, 0, math.radians(-18 * s)))
# nose light slit and cyan side strips along the hull
box("NoseLight", (0.55, 0.15, 0.09), (0, -6.75, 1.12), WHITELIGHT)
for s in (-1, 1):
    box("SideStrip%s" % ("L" if s < 0 else "R"), (0.1, 5.0, 0.14), (s * 2.25, 0.4, 1.35), CYAN_SOFT)
# rear: twin thrusters with glowing cores, a tail fin, a red tail strip
for s in (-1, 1):
    side = "L" if s < 0 else "R"
    cylinder("Thruster" + side, 0.62, 1.6, (s * 1.25, 7.0, 1.45), PANEL, rot=(math.radians(90), 0, 0), verts=32)
    cylinder("ThrusterRing" + side, 0.7, 0.25, (s * 1.25, 7.75, 1.45), CHROME, rot=(math.radians(90), 0, 0), verts=32)
    cylinder("ThrusterCore" + side, 0.48, 0.1, (s * 1.25, 7.86, 1.45), CYAN, rot=(math.radians(90), 0, 0), verts=32)
# swept tail fin: a thin profile in the Y-Z plane, leaning back
fin_mesh = bpy.data.meshes.new("Hovercraft_TailFin")
fb = bmesh.new()
profile = [(3.6, 2.05), (6.6, 2.05), (7.1, 3.0), (6.4, 4.1), (5.7, 4.15)]      # (y, z) base to tip
front = [fb.verts.new((-0.07, y, z)) for y, z in profile]
back = [fb.verts.new((0.07, y, z)) for y, z in profile]
fb.faces.new(front)
fb.faces.new(list(reversed(back)))
for i in range(len(profile)):
    j = (i + 1) % len(profile)
    fb.faces.new((front[i], front[j], back[j], back[i]))
fb.to_mesh(fin_mesh)
fb.free()
fin = bpy.data.objects.new("Hovercraft_TailFin", fin_mesh)
fin.data.materials.append(GREY)
fb_mod = fin.modifiers.new("Bevel", "BEVEL")
fb_mod.width = 0.05
fb_mod.segments = 2
scene.collection.objects.link(fin)
attach(fin)
box("FinLight", (0.16, 0.9, 0.08), (0, 6.1, 4.05), CYAN, rot=(math.radians(-25), 0, 0))
box("TailStrip", (2.2, 0.08, 0.16), (0, 7.55, 1.9), REDLIGHT, bevel=0.02, segments=1)
# panel lines: thin dark grooves across the deck
for y in (-1.2, 1.0, 3.4):
    box("Groove%.0f" % (y * 10), (4.3, 0.06, 0.05), (0, y, 2.09), PANEL)

# ------------------------------------------------------------ hover: repulsor pads and their light
PADS = ((0, -4.6), (-1.5, 3.4), (1.5, 3.4))
for i, (px, py) in enumerate(PADS):
    cylinder("Pad%d" % i, 0.62, 0.1, (px, py, 0.34), CYAN, rot=(0, 0, 0), verts=32)
    cylinder("PadRim%d" % i, 0.78, 0.16, (px, py, 0.38), PANEL, verts=32)
    light = bpy.data.lights.new("Hovercraft_PadLight%d" % i, "POINT")
    light.color = (0.3, 0.8, 1.0)
    light.energy = 220
    light.shadow_soft_size = 0.6
    lo = bpy.data.objects.new("Hovercraft_PadLight%d" % i, light)
    lo.location = (px, py, 0.1)
    col.objects.link(lo)
    lo.parent = root
    lo.matrix_parent_inverse.identity()
# a soft glow disc under the craft so the hover reads from the side too
glow = cylinder("GlowDisc", 2.6, 0.02, (0, 0.6, -2.22), CYAN_SOFT, verts=48)
glow.scale = (1, 2.0, 1)
glow.data.materials[0] = material("Glow", (0.2, 0.8, 1.0), rough=1.0, emit=((0.2, 0.75, 1.0), 0.7))
glow.data.materials[0].blend_method = "BLEND"
glow.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.12

# ------------------------------------------------------------ hovering
HOVER_Z = 2.3                                   # belly clears the plate by a couple of studs
root.location = (0, 0, HOVER_Z)
root.animation_data_clear()
for f in range(scene.frame_start, scene.frame_end + 1):
    t = f / FPS
    scene.frame_set(f)
    root.location.z = HOVER_Z + 0.16 * math.sin(2 * math.pi * t / 2.3) + 0.05 * math.sin(2 * math.pi * t / 0.9)
    root.rotation_euler = (0.012 * math.sin(2 * math.pi * t / 3.1), 0.015 * math.sin(2 * math.pi * t / 2.7 + 1.0), 0)
    root.keyframe_insert("location", index=2, frame=f)
    root.keyframe_insert("rotation_euler", frame=f)
scene.frame_set(scene.frame_start)

bpy.ops.object.select_all(action="DESELECT")
parts = [o for o in col.objects if o.name.startswith("Hovercraft")]
print("hover-jetski built:", len(parts), "objects; hovering at z", HOVER_Z)
