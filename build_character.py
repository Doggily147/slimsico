"""Adds a Human Fall Flat styled character to the open slimsico scene and
switches the baseplate to the numbered grid texture from make_tile_texture.py.

The body is modelled with metaballs (soft, gummy, joined limbs), converted to
a mesh, and topped with a gold crown. Run inside Blender with slimsico.blend
open (Text editor, or via the MCP bridge). Re-running replaces the character.
"""
import bmesh
import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
TILE_TEX = os.path.join(ROOT, "textures", "tiles.png")

scene = bpy.context.scene


def material(name, rgb, rough=0.5, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    m.diffuse_color = (*rgb, 1)
    m.metallic = metallic
    m.roughness = rough
    return m


# ------------------------------------------------------------ baseplate grid
bp = bpy.data.objects["Baseplate"]
grid = bpy.data.materials.get("GridMat") or bpy.data.materials.new("GridMat")
grid.use_nodes = True
nt = grid.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord")
mapping = nt.nodes.new("ShaderNodeMapping")
mapping.inputs["Location"].default_value = (0.5, 0.5, 0)      # centre the plate on the image
mapping.inputs["Scale"].default_value = (1 / 512, 1 / 512, 1)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.get("tiles.png") or bpy.data.images.load(TILE_TEX)
tex.image.reload()
tex.extension = "EXTEND"
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.45
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
bp.data.materials.clear()
bp.data.materials.append(grid)

# ------------------------------------------------------------ cleanup
if "Character" in bpy.data.collections:
    col = bpy.data.collections["Character"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
for block in (bpy.data.meshes, bpy.data.metaballs):
    for d in list(block):
        if d.users == 0:
            block.remove(d)

col = bpy.data.collections.new("Character")
scene.collection.children.link(col)


def link(obj, parent=None):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


# Pale mint gummy body instead of Bob's white; navy shorts; gold crown.
SKIN = material("GummyMint", (0.72, 0.90, 0.80), rough=0.35)
sb = SKIN.node_tree.nodes["Principled BSDF"]
sb.inputs["Subsurface Weight"].default_value = 0.5
sb.inputs["Subsurface Radius"].default_value = (0.8, 1.0, 0.9)
sb.inputs["Coat Weight"].default_value = 0.6
sb.inputs["Coat Roughness"].default_value = 0.15
SHORTS = material("ShortsNavy", (0.08, 0.12, 0.32), rough=0.55)
GOLD = material("CrownGold", (1.0, 0.72, 0.18), rough=0.25, metallic=1.0)
GEM = material("CrownGem", (0.85, 0.08, 0.12), rough=0.1)
EYE = material("EyeDark", (0.05, 0.05, 0.06), rough=0.3)

# ------------------------------------------------------------ metaball body
# Metaball objects sharing a base name blend together, so the body and the
# shorts use different names to stay separate.


def metaball_object(name, resolution):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution / 2
    mb.threshold = 0.6
    o = bpy.data.objects.new(name, mb)
    scene.collection.objects.link(o)
    return link(o)


def ball(mb, loc, radius, kind="BALL", size=(1, 1, 1), rot=None):
    e = mb.elements.new()
    e.type = kind
    e.co = loc
    e.radius = radius
    e.size_x, e.size_y, e.size_z = size
    e.stiffness = 2.0
    if rot is not None:
        e.rotation = rot
    return e


body = metaball_object("GummyBody", 0.12)
mb = body.data
# head, neck, torso
ball(mb, (0, 0, 5.05), 1.3)
ball(mb, (0, 0, 4.15), 0.75)
ball(mb, (0, 0, 3.35), 1.25, "ELLIPSOID", (1.05, 0.72, 1.15))
ball(mb, (0, 0, 2.45), 1.05, "ELLIPSOID", (1.0, 0.72, 0.8))       # hips
# arms: capsules hang from the shoulders, slightly out, mitten hands
for s in (-1, 1):
    shoulder = Vector((s * 1.05, 0, 3.95))
    hand = Vector((s * 1.45, -0.15, 2.05))
    mid = (shoulder + hand) / 2
    d = hand - shoulder
    # a capsule runs along its local X axis; point that down the arm
    ball(mb, mid, 0.62, "CAPSULE", (d.length / 2 - 0.35, 1, 1), rot=d.to_track_quat("X", "Z"))
    ball(mb, hand, 0.66)
# legs: short capsules and chunky feet
for s in (-1, 1):
    hip = Vector((s * 0.5, 0, 2.1))
    ankle = Vector((s * 0.62, 0, 0.55))
    d = ankle - hip
    ball(mb, (hip + ankle) / 2, 0.66, "CAPSULE", (d.length / 2 - 0.3, 1, 1))
    mb.elements[-1].rotation = d.to_track_quat("X", "Z")
    ball(mb, (s * 0.65, -0.3, 0.42), 0.72, "ELLIPSOID", (0.62, 0.95, 0.5))

shorts = metaball_object("GummyShorts", 0.12)
sm = shorts.data
ball(sm, (0, 0, 2.45), 1.3, "ELLIPSOID", (1.1, 0.82, 0.75))
for s in (-1, 1):
    ball(sm, (s * 0.55, 0, 1.7), 0.95, "ELLIPSOID", (0.62, 0.62, 0.8))

# Freeze the metaballs into meshes so the file is stable and materials stick.
depsgraph = bpy.context.evaluated_depsgraph_get()
converted = {}
for o, mat in ((body, SKIN), (shorts, SHORTS)):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    converted[mat.name] = o
body = converted["GummyMint"]
body.name = "Character"
shorts = converted["ShortsNavy"]
shorts.name = "Shorts"
link(shorts, body)
for d in list(bpy.data.metaballs):
    if d.users == 0:
        bpy.data.metaballs.remove(d)

# Drop the figure so the soles touch the baseplate (z = 0).
floor = min((body.matrix_world @ Vector(c)).z for c in body.bound_box)
for o in (body, shorts):
    for v in o.data.vertices:
        v.co.z -= floor
HEAD_TOP = max((body.matrix_world @ Vector(c)).z for c in body.bound_box)

# ------------------------------------------------------------ face: two eyes
depsgraph = bpy.context.evaluated_depsgraph_get()
body_eval = body.evaluated_get(depsgraph)
for x in (-0.32, 0.32):
    ok, loc, n, _ = body_eval.closest_point_on_mesh(Vector((x, -2.0, HEAD_TOP - 0.55)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, segments=24, ring_count=12, location=loc + n * 0.01)
    eye = bpy.context.object
    eye.name = "Eye" + ("L" if x < 0 else "R")
    eye.rotation_mode = "QUATERNION"
    eye.rotation_quaternion = n.to_track_quat("Z", "Y")
    eye.scale = (0.8, 1.3, 0.45)
    eye.data.materials.append(EYE)
    bpy.ops.object.shade_smooth()
    link(eye, body)

# ------------------------------------------------------------ crown
SEGMENTS, PEAKS = 32, 8
R_CROWN = 0.74
BAND_Z, VALLEY_Z, PEAK_Z = 0.0, 0.32, 0.78
crown_mesh = bpy.data.meshes.new("Crown")
cb = bmesh.new()
bottom, top = [], []
per_peak = SEGMENTS // PEAKS
for i in range(SEGMENTS):
    a = 2 * math.pi * i / SEGMENTS
    x, y = R_CROWN * math.cos(a), R_CROWN * math.sin(a)
    k = i % per_peak
    t = 1 - abs(k - per_peak / 2) / (per_peak / 2)          # 0 at peak, 1 at valley
    z = PEAK_Z + (VALLEY_Z - PEAK_Z) * t
    bottom.append(cb.verts.new((x, y, BAND_Z)))
    top.append(cb.verts.new((x, y, z)))
for i in range(SEGMENTS):
    j = (i + 1) % SEGMENTS
    cb.faces.new((bottom[i], bottom[j], top[j], top[i]))
cb.to_mesh(crown_mesh)
cb.free()
crown = bpy.data.objects.new("Crown", crown_mesh)
scene.collection.objects.link(crown)
link(crown, body)
crown.data.materials.append(GOLD)
sol = crown.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.07
sol.offset = 0
bev = crown.modifiers.new("Bevel", "BEVEL")
bev.width = 0.015
bev.segments = 2
# sit the crown on the head, tilted a touch to one side
crown.location = (0.05, 0, HEAD_TOP - 0.36)
crown.rotation_euler = (math.radians(4), math.radians(9), 0)
for i in range(PEAKS):
    a = 2 * math.pi * (i * per_peak) / SEGMENTS
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, segments=16, ring_count=8,
                                         location=(R_CROWN * math.cos(a), R_CROWN * math.sin(a), 0.22))
    gem = bpy.context.object
    gem.name = "Gem%d" % (i + 1)
    gem.data.materials.append(GEM if i % 2 == 0 else material("CrownGemBlue", (0.1, 0.3, 0.9), rough=0.1))
    bpy.ops.object.shade_smooth()
    link(gem, crown)
    gem.matrix_parent_inverse.identity()
    gem.parent = crown

bpy.ops.object.select_all(action="DESELECT")
for o in col.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
print("built", sorted(o.name for o in col.objects))
