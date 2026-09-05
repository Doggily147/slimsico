"""Adds a low-poly, matte yellow, Wobbly Life styled character with a crown to
the open slimsico scene and switches the baseplate to the numbered grid
texture from make_tile_texture.py.

Every body part is its own low-segment primitive, flat shaded, so the limbs
read as separate pieces. Run inside Blender with slimsico.blend open (Text
editor, or via the MCP bridge). Re-running replaces the character.
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


def finish(obj, name, mat, parent=root):
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_flat()                      # visible facets = low poly look
    return link(obj, parent)


def sphere(name, radius, loc, mat, segments=16, rings=10, scale=(1, 1, 1), rot=None, parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.scale = scale
    if rot is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
    return finish(o, name, mat, parent)


def limb(name, start, end, radius, mat, sides=10):
    """A low-poly cylinder from start to end, capped by a small joint sphere."""
    start, end = Vector(start), Vector(end)
    d = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=d.length,
                                        location=(start + end) / 2)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return finish(o, name, mat)


# ------------------------------------------------------------ proportions
# Taller than the reference: about 7 studs from soles to the top of the head.
HEAD_R = 1.05
HEAD_C = Vector((0, 0, 6.0))
TORSO_C = Vector((0, 0, 3.75))
SHOULDER = 4.55
HIP = 2.65

# head and torso
sphere("Head", HEAD_R, HEAD_C, YELLOW)
sphere("Torso", 1.0, TORSO_C, YELLOW, segments=14, rings=9, scale=(0.95, 0.78, 1.2))
limb("Neck", (0, 0, 4.75), (0, 0, 5.15), 0.28, YELLOW, sides=8)

# arms: out to the sides and raised a little, like the reference pose
for s, side in ((-1, "L"), (1, "R")):
    shoulder = Vector((s * 0.85, 0, SHOULDER))
    direction = Vector((s * math.cos(math.radians(18)), 0, math.sin(math.radians(18))))
    elbow = shoulder + direction * 0.22
    wrist = shoulder + direction * 2.05
    sphere("Shoulder" + side, 0.34, shoulder, YELLOW, segments=10, rings=6)
    limb("Arm" + side, elbow, wrist, 0.24, YELLOW)
    sphere("Hand" + side, 0.36, shoulder + direction * 2.25, YELLOW, segments=10, rings=6)

# legs: straight down with a small stance, chunky feet
for s, side in ((-1, "L"), (1, "R")):
    hip = Vector((s * 0.42, 0, HIP))
    ankle = Vector((s * 0.55, 0, 0.45))
    sphere("Hip" + side, 0.36, hip, YELLOW, segments=10, rings=6)
    limb("Leg" + side, hip - Vector((0, 0, 0.2)), ankle, 0.27, YELLOW)
    sphere("Foot" + side, 0.5, (s * 0.55, -0.18, 0.24), YELLOW, segments=10, rings=6, scale=(0.9, 1.25, 0.48))

# ------------------------------------------------------------ face
def on_head(point):
    """Project a point onto the head sphere; returns (surface point, outward normal)."""
    n = (Vector(point) - HEAD_C).normalized()
    return HEAD_C + n * HEAD_R, n


for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_head((s * 0.4, -1.0, 6.2))
    sphere("Eye" + side, 0.13, loc + n * 0.02, DARK, segments=10, rings=6,
           scale=(1, 1, 0.5), rot=n.to_track_quat("Z", "Y"))

# mouth: a small low-poly smile arc pressed onto the face
loc, n = on_head((0, -1.0, 5.55))
bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.05,
                                 major_segments=16, minor_segments=6, location=loc + n * 0.02)
mouth = bpy.context.object
mouth.rotation_mode = "QUATERNION"
mouth.rotation_quaternion = n.to_track_quat("Z", "Y")
mb = bmesh.new()
mb.from_mesh(mouth.data)
bmesh.ops.delete(mb, geom=[v for v in mb.verts if v.co.y > 0.03], context="VERTS")
mb.to_mesh(mouth.data)
mb.free()
finish(mouth, "Mouth", DARK)

# ------------------------------------------------------------ crown
SEGMENTS, PEAKS = 24, 6
R_CROWN = 0.72
BAND_Z, VALLEY_Z, PEAK_Z = 0.0, 0.3, 0.72
crown_mesh = bpy.data.meshes.new("Crown")
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
cb.to_mesh(crown_mesh)
cb.free()
crown = bpy.data.objects.new("Crown", crown_mesh)
scene.collection.objects.link(crown)
crown.data.materials.append(GOLD)
sol = crown.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.07
sol.offset = 0
# band sits where the head is about R_CROWN wide, tilted a touch to one side
crown.location = (0.04, 0, HEAD_C.z + math.sqrt(HEAD_R ** 2 - R_CROWN ** 2) - 0.02)
crown.rotation_euler = (math.radians(3), math.radians(8), 0)
link(crown)
for i in range(PEAKS):
    a = 2 * math.pi * (i * per_peak) / SEGMENTS
    sphere("Gem%d" % (i + 1), 0.075, (R_CROWN * math.cos(a), R_CROWN * math.sin(a), 0.2),
           GEM_RED if i % 2 == 0 else GEM_BLUE, segments=8, rings=5, parent=crown)

bpy.ops.object.select_all(action="DESELECT")
for o in col.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["Head"]
print("built", len(col.objects), "objects")
