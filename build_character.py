"""Adds a tall, smooth, matte yellow Human Fall Flat styled character with a
crown to the open slimsico scene and switches the baseplate to the numbered
grid texture from make_tile_texture.py.

The body is built from smooth capsules and ellipsoids (egg-shaped head,
chunky soft torso, sausage limbs with mitten hands) so every limb is its own
piece but nothing is faceted. Run inside Blender with slimsico.blend open
(Text editor, or via the MCP bridge). Re-running replaces the character.
"""
import bmesh
import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
TILE_TEX = os.path.join(ROOT, "textures", "tiles.png")

scene = bpy.context.scene


def material(name, rgb, rough=0.9, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
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

YELLOW = material("WobblyYellow", (1.0, 0.72, 0.08), rough=0.95)
DARK = material("FaceDark", (0.06, 0.05, 0.04), rough=0.8)
GOLD = material("CrownGold", (1.0, 0.80, 0.25), rough=0.5, metallic=0.7)
GEM_RED = material("CrownGemRed", (0.85, 0.10, 0.12), rough=0.4)
GEM_BLUE = material("CrownGemBlue", (0.12, 0.35, 0.90), rough=0.4)

root = bpy.data.objects.new("Character", None)
root.empty_display_type = "PLAIN_AXES"
root.empty_display_size = 1.0
col.objects.link(root)


def link(obj, parent=root):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def add_mesh(name, bm, mat, loc=(0, 0, 0), rot=None, scale=(1, 1, 1), parent=root):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth()
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.scale = scale
    if rot is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
    o.data.materials.append(mat)
    scene.collection.objects.link(o)
    return link(o, parent)


def ellipsoid(name, radius, loc, mat, scale=(1, 1, 1), rot=None, parent=root, pear=0.0):
    """Smooth sphere; `pear` > 0 widens the lower half for a soft belly."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=radius)
    if pear:
        for v in bm.verts:
            t = (1 - v.co.z / radius) / 2            # 0 at the top, 1 at the bottom
            f = 1 + pear * math.sin(math.pi * min(1.0, t * 1.15))
            v.co.x *= f
            v.co.y *= f
    return add_mesh(name, bm, mat, loc, rot, scale, parent)


def capsule(name, start, end, radius, mat, tip=1.0):
    """Smooth sausage from start to end. `tip` < 1 makes the far end slimmer."""
    start, end = Vector(start), Vector(end)
    d = end - start
    half = max(0.0, d.length / 2 - radius)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=radius)
    for v in bm.verts:
        if v.co.z >= 0:
            v.co.x *= tip
            v.co.y *= tip
            v.co.z = v.co.z * tip + half
        else:
            v.co.z -= half
    return add_mesh(name, bm, mat, (start + end) / 2, d.to_track_quat("Z", "Y"))


# ------------------------------------------------------------ proportions
# Tall: about 9.5 studs from the soles to the top of the head.
HEAD_R = 1.15
HEAD_SCALE = Vector((1.0, 0.94, 1.14))            # egg shaped, a little taller than wide
HEAD_C = Vector((0, 0, 8.25))
SHOULDER_Z = 6.35
HIP_Z = 3.55

ellipsoid("Head", HEAD_R, HEAD_C, YELLOW, scale=HEAD_SCALE)
ellipsoid("Neck", 0.5, (0, 0, 7.0), YELLOW, scale=(1, 1, 0.7))
ellipsoid("Torso", 1.0, (0, 0, 5.25), YELLOW, scale=(1.08, 0.82, 1.55), pear=0.16)
ellipsoid("Hips", 1.0, (0, 0, 3.75), YELLOW, scale=(1.12, 0.84, 0.72))

# arms: relaxed, hanging a little out from the body, mitten hands
for s, side in ((-1, "L"), (1, "R")):
    shoulder = Vector((s * 1.05, 0, SHOULDER_Z))
    direction = Vector((s * math.sin(math.radians(24)), -0.08, -math.cos(math.radians(24)))).normalized()
    capsule("Arm" + side, shoulder, shoulder + direction * 3.1, 0.38, YELLOW, tip=0.9)
    hand = shoulder + direction * 3.35
    ellipsoid("Hand" + side, 0.46, hand, YELLOW, scale=(0.95, 0.72, 1.15),
              rot=direction.to_track_quat("-Z", "Y"))

# legs: slightly apart, rounded feet pointing forward
for s, side in ((-1, "L"), (1, "R")):
    hip = Vector((s * 0.55, 0, HIP_Z))
    ankle = Vector((s * 0.68, 0, 0.85))
    capsule("Leg" + side, hip, ankle, 0.42, YELLOW, tip=0.92)
    ellipsoid("Foot" + side, 0.55, (s * 0.7, -0.32, 0.45), YELLOW, scale=(1.0, 1.55, 0.8))

# ------------------------------------------------------------ face
def on_head(point):
    """Project a point onto the egg-shaped head; returns (surface point, outward normal)."""
    local = Vector([(a - c) / sc for a, c, sc in zip(point, HEAD_C, HEAD_SCALE)]).normalized()
    surface = HEAD_C + Vector([l * sc * HEAD_R for l, sc in zip(local, HEAD_SCALE)])
    normal = Vector([l / sc for l, sc in zip(local, HEAD_SCALE)]).normalized()
    return surface, normal


for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_head((s * 0.42, -1.2, 8.45))
    ellipsoid("Eye" + side, 0.14, loc + n * 0.02, DARK, scale=(1, 1, 0.45),
              rot=n.to_track_quat("Z", "Y"))

loc, n = on_head((0, -1.2, 7.75))
bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.055,
                                 major_segments=40, minor_segments=12, location=loc + n * 0.02)
mouth = bpy.context.object
mouth.rotation_mode = "QUATERNION"
mouth.rotation_quaternion = n.to_track_quat("Z", "Y")
mb = bmesh.new()
mb.from_mesh(mouth.data)
bmesh.ops.delete(mb, geom=[v for v in mb.verts if v.co.y > 0.03], context="VERTS")
mb.to_mesh(mouth.data)
mb.free()
mouth.name = "Mouth"
mouth.data.shade_smooth()
mouth.data.materials.append(DARK)
link(mouth)

# ------------------------------------------------------------ crown
SEGMENTS, PEAKS = 48, 6
R_CROWN = 0.82
BAND_Z, VALLEY_Z, PEAK_Z = 0.0, 0.32, 0.8
cb = bmesh.new()
bottom, top = [], []
per_peak = SEGMENTS // PEAKS
for i in range(SEGMENTS):
    a = 2 * math.pi * i / SEGMENTS
    x, y = R_CROWN * math.cos(a), R_CROWN * math.sin(a)
    k = i % per_peak
    t = 1 - abs(k - per_peak / 2) / (per_peak / 2)          # 0 at a peak, 1 in a valley
    z = PEAK_Z + (VALLEY_Z - PEAK_Z) * t
    bottom.append(cb.verts.new((x, y, BAND_Z)))
    top.append(cb.verts.new((x, y, z)))
for i in range(SEGMENTS):
    j = (i + 1) % SEGMENTS
    cb.faces.new((bottom[i], bottom[j], top[j], top[i]))
# the band is where the head is R_CROWN wide; tilt it a touch to one side
h = HEAD_R * HEAD_SCALE.z * math.sqrt(max(0.0, 1 - (R_CROWN / (HEAD_R * HEAD_SCALE.x)) ** 2))
crown = add_mesh("Crown", cb, GOLD, (0.04, 0, HEAD_C.z + h - 0.03))
crown.data.shade_flat()
crown.rotation_mode = "XYZ"
crown.rotation_euler = (math.radians(3), math.radians(8), 0)
sol = crown.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.07
sol.offset = 0
bev = crown.modifiers.new("Bevel", "BEVEL")
bev.width = 0.015
bev.segments = 2
for i in range(PEAKS):
    a = 2 * math.pi * (i * per_peak) / SEGMENTS
    ellipsoid("Gem%d" % (i + 1), 0.085, (R_CROWN * math.cos(a), R_CROWN * math.sin(a), 0.2),
              GEM_RED if i % 2 == 0 else GEM_BLUE, parent=crown)

bpy.ops.object.select_all(action="DESELECT")
for o in col.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["Head"]
print("built", len(col.objects), "objects")
