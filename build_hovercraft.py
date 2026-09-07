"""A stylised hovercraft, sized for Yellow (he is about 9 studs tall).

Parts: a bevelled hull on a fat rubber skirt, an open cockpit with a tinted
windscreen, a seat, dashboard and steering yoke, a big ducted rear fan with a
grille and twin rudders, twin intake pods, a roll bar, headlights and tail
lights, racing stripes and a number. Everything is parented to the empty
"Hovercraft" (the fan blades to "HovercraftFan" so they can spin), so the
whole craft can be animated as one thing.

Run inside Blender with slimsico.blend open. Re-running replaces it.
"""
import bmesh
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene

# ------------------------------------------------------------ cleanup
for o in list(bpy.data.objects):
    if o.name.startswith("Hovercraft"):
        bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.curves):
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
    m.diffuse_color = (*rgb, 1)
    return m


TEAL = material("Hull", (0.08, 0.55, 0.62), rough=0.35)
WHITE = material("Stripe", (0.95, 0.95, 0.93), rough=0.4)
ORANGE = material("Accent", (1.0, 0.42, 0.08), rough=0.45)
RUBBER = material("Skirt", (0.12, 0.12, 0.13), rough=0.9)
STEEL = material("Steel", (0.45, 0.47, 0.5), rough=0.35, metallic=0.9)
DARK = material("DarkMetal", (0.1, 0.1, 0.11), rough=0.5, metallic=0.6)
GLASS = material("Glass", (0.55, 0.8, 0.95), rough=0.05, emit=((0.4, 0.6, 0.8), 0.15))
SEAT = material("Seat", (0.16, 0.14, 0.14), rough=0.8)
HEADLIGHT = material("Headlight", (1, 1, 0.9), emit=((1.0, 0.97, 0.85), 6))
TAILLIGHT = material("Taillight", (0.9, 0.1, 0.1), emit=((1.0, 0.15, 0.1), 5))

root = bpy.data.objects.new("Hovercraft", None)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 3
root.location = (0, 0, 0)
col.objects.link(root)
fan_root = bpy.data.objects.new("HovercraftFan", None)
fan_root.empty_display_type = "SPHERE"
fan_root.empty_display_size = 1
col.objects.link(fan_root)
fan_root.parent = root                      # rides with the craft; spins on its own local Y


def attach(o, parent):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.parent = parent
    o.matrix_parent_inverse.identity()          # positions are given in the craft's own frame
    return o


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
    return attach(o, parent or root)


def cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=32, parent=None, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.data.materials.append(mat)
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    return attach(o, parent or root)


def sphere(name, radius, loc, mat, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = "Hovercraft_" + name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return attach(o, parent or root)


def tube(name, radius, depth, thickness, loc, mat, rot=(0, 0, 0), verts=48, parent=None):
    """An open ring (a duct): a capless cylinder given wall thickness."""
    mesh = bpy.data.meshes.new("Hovercraft_" + name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=verts, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    o = bpy.data.objects.new("Hovercraft_" + name, mesh)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(mat)
    s = o.modifiers.new("Solidify", "SOLIDIFY")
    s.thickness = thickness
    s.offset = 0
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width = 0.08
    b.segments = 2
    scene.collection.objects.link(o)
    return attach(o, parent or root)


# ------------------------------------------------------------ hull and skirt
# The craft points along -Y (Yellow's forward). Length 16, width 9.
L, W = 16.0, 9.0
SKIRT_TOP = 1.7                                  # the hull deck sits on the skirt
box("Skirt", (W + 1.2, L + 1.4, 1.7), (0, 0, 0.85), RUBBER, bevel=0.8, segments=6)
hull = box("Hull", (W, L, 2.1), (0, 0, SKIRT_TOP + 1.05), TEAL, bevel=0.7, segments=6)
# a rounded nose: a squashed sphere blended into the front
sphere("Nose", 3.2, (0, -L / 2 + 0.6, SKIRT_TOP + 1.05), TEAL, scale=(1.35, 0.7, 0.33))
# raised rear deck that carries the fan and the pods
box("RearDeck", (W - 1.2, 4.6, 1.0), (0, L / 2 - 3.0, SKIRT_TOP + 2.6), TEAL, bevel=0.35, segments=4)
# stripes: white centre stripe with orange edges, sitting just proud of the deck
DECK_Z = SKIRT_TOP + 2.1
box("StripeWhite", (1.6, L - 2.5, 0.05), (0, -0.5, DECK_Z + 0.03), WHITE)
box("StripeOrangeL", (0.35, L - 2.5, 0.05), (-1.15, -0.5, DECK_Z + 0.03), ORANGE)
box("StripeOrangeR", (0.35, L - 2.5, 0.05), (1.15, -0.5, DECK_Z + 0.03), ORANGE)
# side accent flashes
for s in (-1, 1):
    box("Flash%s" % ("L" if s < 0 else "R"), (0.08, 7.0, 0.7), (s * (W / 2 + 0.02), -1.0, SKIRT_TOP + 1.05), ORANGE,
        rot=(0, 0, 0), bevel=0.03, segments=1)
# rubbing strake round the hull
tube("Strake", W / 2 + 0.15, 0.3, 0.25, (0, 0, SKIRT_TOP + 0.5), DARK, verts=64)
strake = bpy.data.objects["Hovercraft_Strake"]
strake.scale = (1, L / W, 1)

# ------------------------------------------------------------ cockpit
COCK_Y = -1.5
box("Seat", (2.4, 2.2, 0.7), (0, COCK_Y + 1.2, DECK_Z + 0.35), SEAT, bevel=0.2, segments=4)
box("SeatBack", (2.4, 0.5, 2.4), (0, COCK_Y + 2.4, DECK_Z + 1.5), SEAT, bevel=0.2, segments=4)
box("Dash", (3.6, 1.2, 1.1), (0, COCK_Y - 1.9, DECK_Z + 0.55), DARK, bevel=0.15, segments=3)
box("DashScreen", (1.6, 0.06, 0.6), (0, COCK_Y - 1.3, DECK_Z + 0.75), material("Screen", (0.05, 0.2, 0.3), emit=((0.2, 0.7, 0.9), 1.5)))
cylinder("YokeStem", 0.12, 1.4, (0, COCK_Y - 0.9, DECK_Z + 1.2), STEEL, rot=(math.radians(-35), 0, 0), verts=12)
bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.1, major_segments=32, minor_segments=10,
                                 location=(0, COCK_Y - 0.5, DECK_Z + 1.75), rotation=(math.radians(55), 0, 0))
yoke = bpy.context.object
yoke.name = "Hovercraft_Yoke"
yoke.data.materials.append(DARK)
bpy.ops.object.shade_smooth()
attach(yoke, root)
# windscreen: a tinted pane raked back, with a steel frame
box("ScreenFrame", (4.6, 0.12, 2.4), (0, COCK_Y - 2.9, DECK_Z + 1.5), STEEL, rot=(math.radians(-28), 0, 0), bevel=0.05, segments=2)
box("Windscreen", (4.2, 0.06, 2.1), (0, COCK_Y - 2.88, DECK_Z + 1.5), GLASS, rot=(math.radians(-28), 0, 0))
# roll bar behind the seat
for s in (-1, 1):
    cylinder("RollBar%s" % ("L" if s < 0 else "R"), 0.16, 3.0, (s * 1.6, COCK_Y + 3.0, DECK_Z + 1.5), STEEL, verts=12)
cylinder("RollBarTop", 0.16, 3.5, (0, COCK_Y + 3.0, DECK_Z + 3.0), STEEL, rot=(0, math.radians(90), 0), verts=12)

# ------------------------------------------------------------ the fan
FAN_Y = L / 2 - 2.2
FAN_Z = SKIRT_TOP + 3.1 + 2.6
FAN_R = 2.7
tube("Duct", FAN_R + 0.2, 1.4, 0.3, (0, FAN_Y, FAN_Z), STEEL, rot=(math.radians(90), 0, 0), verts=64)
tube("DuctLip", FAN_R + 0.45, 0.35, 0.28, (0, FAN_Y - 0.75, FAN_Z), ORANGE, rot=(math.radians(90), 0, 0), verts=64)
fan_root.location = (0, FAN_Y, FAN_Z)
fan_root.rotation_euler = (0, 0, 0)
cylinder("FanHub", 0.6, 0.9, (0, 0, 0), DARK, rot=(math.radians(90), 0, 0), verts=24, parent=fan_root)
sphere("FanCap", 0.45, (0, -0.5, 0), DARK, scale=(1, 0.7, 1), parent=fan_root)
for i in range(6):
    a = 2 * math.pi * i / 6
    # a flat blade, pitched, sweeping out from the hub
    blade = box("Blade%d" % i, (0.9, 0.12, FAN_R - 0.75), (0, 0, 0), STEEL, bevel=0.03, segments=1, parent=fan_root)
    blade.data.transform(Matrix.Translation((0, 0, (FAN_R - 0.75) / 2 + 0.55)))
    blade.data.transform(Matrix.Rotation(math.radians(28), 4, "Z"))      # pitch
    blade.rotation_euler = (0, a, 0)                                     # around the hub (the fan spins on local Y)
# grille: bars across the front of the duct
for i in range(-4, 5):
    y_off = -0.85
    cylinder("Grille%d" % (i + 4), 0.05, 2 * math.sqrt(max(0.05, FAN_R ** 2 - (i * 0.6) ** 2)), (0, FAN_Y + y_off, FAN_Z + i * 0.6),
             DARK, rot=(0, math.radians(90), 0), verts=8, smooth=False)
tube("GrilleRing", FAN_R + 0.05, 0.12, 0.16, (0, FAN_Y + y_off, FAN_Z), DARK, rot=(math.radians(90), 0, 0), verts=48)
# supports from the deck to the duct
for s in (-1, 1):
    box("DuctStrut%s" % ("L" if s < 0 else "R"), (0.35, 0.9, 2.8), (s * 2.0, FAN_Y, SKIRT_TOP + 3.1 + 1.3), DARK, bevel=0.05, segments=1)
# twin rudders behind the fan
for s in (-1, 1):
    box("Rudder%s" % ("L" if s < 0 else "R"), (0.12, 1.6, 3.6), (s * 1.5, FAN_Y + 1.9, FAN_Z), ORANGE, bevel=0.05, segments=1)
cylinder("RudderBar", 0.1, 3.4, (0, FAN_Y + 1.9, FAN_Z + 1.9), STEEL, rot=(0, math.radians(90), 0), verts=10)

# ------------------------------------------------------------ pods, lights, number
for s in (-1, 1):
    pod = cylinder("Pod%s" % ("L" if s < 0 else "R"), 0.75, 3.6, (s * 2.9, L / 2 - 4.2, SKIRT_TOP + 3.1 + 0.75), TEAL, rot=(math.radians(90), 0, 0), verts=24)
    cylinder("PodIntake%s" % ("L" if s < 0 else "R"), 0.6, 0.3, (s * 2.9, L / 2 - 6.05, SKIRT_TOP + 3.1 + 0.75), DARK, rot=(math.radians(90), 0, 0), verts=24)
    sphere("Headlight%s" % ("L" if s < 0 else "R"), 0.42, (s * 2.4, -L / 2 - 0.15, SKIRT_TOP + 1.2), HEADLIGHT, scale=(1, 0.5, 1))
    box("Taillight%s" % ("L" if s < 0 else "R"), (1.0, 0.12, 0.35), (s * 3.0, L / 2 + 0.02, SKIRT_TOP + 1.3), TAILLIGHT)
for s in (-1, 1):
    curve = bpy.data.curves.new("Hovercraft_Number%s" % ("L" if s < 0 else "R"), "FONT")
    curve.body = "07"
    curve.size = 1.6
    curve.extrude = 0.03
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    num = bpy.data.objects.new("Hovercraft_Number%s" % ("L" if s < 0 else "R"), curve)
    num.data.materials.append(WHITE)
    num.location = (s * (W / 2 + 0.06), 2.2, SKIRT_TOP + 1.05)
    num.rotation_euler = (math.radians(90), 0, math.radians(90 * s))
    scene.collection.objects.link(num)
    attach(num, root)

bpy.ops.object.select_all(action="DESELECT")
parts = [o for o in col.objects if o.name.startswith("Hovercraft")]
print("hovercraft built:", len(parts), "objects; root at", tuple(root.location))
