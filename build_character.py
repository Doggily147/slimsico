"""Adds a tall, smooth, matte yellow Human Fall Flat styled character with a
crown to the open slimsico scene and switches the baseplate to the numbered
grid texture from make_tile_texture.py.

The body is ONE connected mesh: a joint skeleton is skinned with the Skin
modifier (clean quad topology that flows from head to toes) and smoothed with
subdivision surfaces, then an armature is generated from the same skeleton so
the character can be posed. Eyes, mouth and crown are separate objects parented
to the body, as in a normal character rig.

Run inside Blender with slimsico.blend open (Text editor, or via the MCP
bridge). Re-running replaces the character.
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
for block in (bpy.data.meshes, bpy.data.metaballs, bpy.data.armatures):
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


def link(obj, parent=None):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


# ------------------------------------------------------------ body skeleton
# Each joint: name, position, (radius across, radius front-to-back).
# The Skin modifier wraps this graph in one continuous quad mesh.
JOINTS = {
    "pelvis":    ((0, 0, 3.55), (1.18, 0.88)),
    "belly":     ((0, 0, 4.45), (1.26, 0.96)),
    "chest":     ((0, 0, 5.45), (1.22, 0.90)),
    "shoulders": ((0, 0, 6.25), (1.12, 0.76)),
    "neck":      ((0, 0, 6.85), (0.50, 0.48)),
    "head_base": ((0, 0, 7.45), (0.90, 0.86)),
    "head":      ((0, 0, 8.15), (1.12, 1.02)),
    "head_top":  ((0, 0, 8.85), (0.82, 0.78)),
}
CHAIN = [("pelvis", "belly"), ("belly", "chest"), ("chest", "shoulders"),
         ("shoulders", "neck"), ("neck", "head_base"), ("head_base", "head"), ("head", "head_top")]
for s, side in ((-1, "L"), (1, "R")):
    JOINTS.update({
        "shoulder" + side: ((s * 1.30, 0.0, 6.00), (0.56, 0.54)),
        "elbow" + side:    ((s * 1.78, -0.10, 4.95), (0.46, 0.46)),
        "wrist" + side:    ((s * 2.10, -0.28, 3.95), (0.42, 0.42)),
        "hand" + side:     ((s * 2.28, -0.40, 3.40), (0.54, 0.36)),
        "hip" + side:      ((s * 0.62, 0.0, 3.10), (0.58, 0.56)),
        "knee" + side:     ((s * 0.66, 0.0, 1.85), (0.50, 0.50)),
        "ankle" + side:    ((s * 0.70, 0.0, 0.75), (0.44, 0.44)),
        "foot" + side:     ((s * 0.74, -0.80, 0.45), (0.50, 0.40)),
    })
    CHAIN += [("shoulders", "shoulder" + side), ("shoulder" + side, "elbow" + side),
              ("elbow" + side, "wrist" + side), ("wrist" + side, "hand" + side),
              ("pelvis", "hip" + side), ("hip" + side, "knee" + side),
              ("knee" + side, "ankle" + side), ("ankle" + side, "foot" + side)]

body_mesh = bpy.data.meshes.new("CharacterBody")
bm = bmesh.new()
verts = {name: bm.verts.new(pos) for name, (pos, _) in JOINTS.items()}
for a, b in CHAIN:
    bm.edges.new((verts[a], verts[b]))
bm.verts.index_update()
order = list(JOINTS.keys())
bm.to_mesh(body_mesh)
bm.free()

body = bpy.data.objects.new("Character", body_mesh)
scene.collection.objects.link(body)
link(body)
body.data.materials.append(YELLOW)

skin = body.modifiers.new("Skin", "SKIN")
skin.use_smooth_shade = True
skin.branch_smoothing = 1.0
# radii live in the mesh's skin layer, which the modifier creates on add
for i, name in enumerate(order):
    sv = body.data.skin_vertices[0].data[i]
    sv.radius = JOINTS[name][1]
    sv.use_root = (name == "pelvis")
sub = body.modifiers.new("Subdivision", "SUBSURF")
sub.levels = 2
sub.render_levels = 3
smooth = body.modifiers.new("Polish", "CORRECTIVE_SMOOTH")
smooth.factor = 0.5
smooth.iterations = 8
smooth.smooth_type = "LENGTH_WEIGHTED"
body.data.shade_smooth()

# armature from the same skeleton so the character can be posed
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
armature = None
try:
    bpy.ops.object.skin_armature_create(modifier="Skin")
    armature = bpy.context.object
    armature.name = "CharacterRig"
    armature.show_in_front = False              # bones stay inside the body
    armature.data.display_type = "STICK"
    link(armature)
    body.parent = armature
    body.matrix_parent_inverse = armature.matrix_world.inverted()
    # keep the armature deform last so the skin/subdivision shape is what gets posed
    arm_mod = next(m for m in body.modifiers if m.type == "ARMATURE")
    body.modifiers.move(body.modifiers.find(arm_mod.name), len(body.modifiers) - 1)
except RuntimeError as ex:
    print("armature skipped:", ex)

# ------------------------------------------------------------ face
depsgraph = bpy.context.evaluated_depsgraph_get()
body_eval = body.evaluated_get(depsgraph)
HEAD_C = Vector(JOINTS["head"][0])


def on_body(point):
    ok, loc, normal, _ = body_eval.closest_point_on_mesh(Vector(point))
    return loc, normal.normalized()


def sphere(name, radius, loc, mat, scale=(1, 1, 1), rot=None, parent=body):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if rot is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return link(o, parent)


for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_body((s * 0.42, -2.0, HEAD_C.z + 0.25))
    sphere("Eye" + side, 0.14, loc + n * 0.01, DARK, scale=(1, 1, 0.45), rot=n.to_track_quat("Z", "Y"))

loc, n = on_body((0, -2.0, HEAD_C.z - 0.45))
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
link(mouth, body)

# ------------------------------------------------------------ crown
SEGMENTS, PEAKS = 48, 6
R_CROWN = 0.84
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
crown_mesh = bpy.data.meshes.new("Crown")
cb.to_mesh(crown_mesh)
cb.free()
crown = bpy.data.objects.new("Crown", crown_mesh)
scene.collection.objects.link(crown)
crown.data.materials.append(GOLD)
sol = crown.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.07
sol.offset = 0
bev = crown.modifiers.new("Bevel", "BEVEL")
bev.width = 0.015
bev.segments = 2
# find where the head is R_CROWN wide by probing the skinned surface
top_z = max((body_eval.matrix_world @ v.co).z for v in body_eval.data.vertices)
band_z = top_z - 0.3
for _ in range(40):
    loc, _n = on_body((R_CROWN, 0, band_z))
    if loc.x >= R_CROWN - 0.01:
        break
    band_z -= 0.03
crown.location = (0.04, 0, band_z - 0.04)
crown.rotation_euler = (math.radians(3), math.radians(8), 0)
link(crown, body)
for i in range(PEAKS):
    a = 2 * math.pi * (i * per_peak) / SEGMENTS
    sphere("Gem%d" % (i + 1), 0.085, (R_CROWN * math.cos(a), R_CROWN * math.sin(a), 0.2),
           GEM_RED if i % 2 == 0 else GEM_BLUE, parent=crown)
    bpy.context.object.matrix_parent_inverse.identity()

bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = body
print("built", len(col.objects), "objects; armature:", armature.name if armature else None)
