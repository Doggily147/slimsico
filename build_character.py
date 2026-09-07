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
from mathutils import Matrix, Vector

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
# a touch of subsurface softens the shading without adding any shine
_yb = YELLOW.node_tree.nodes["Principled BSDF"]
_yb.inputs["Subsurface Weight"].default_value = 0.12
_yb.inputs["Subsurface Radius"].default_value = (0.5, 0.35, 0.1)
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
# Friendlier proportions: a bigger head, a shorter and softer body, thicker
# limbs with the hands at hip height, and big rounded feet. About 9 studs tall.
JOINTS = {
    "pelvis":    ((0, 0, 3.35), (1.18, 0.92)),
    "belly":     ((0, 0, 4.15), (1.28, 1.02)),
    "chest":     ((0, 0, 5.05), (1.22, 0.94)),
    "shoulders": ((0, 0, 5.75), (1.08, 0.80)),
    "neck":      ((0, 0, 6.25), (0.56, 0.52)),
    "head_base": ((0, 0, 6.75), (1.02, 0.96)),
    "head":      ((0, 0, 7.55), (1.30, 1.18)),
    "head_top":  ((0, 0, 8.35), (0.96, 0.90)),
}
CHAIN = [("pelvis", "belly"), ("belly", "chest"), ("chest", "shoulders"),
         ("shoulders", "neck"), ("neck", "head_base"), ("head_base", "head"), ("head", "head_top")]
for s, side in ((-1, "L"), (1, "R")):
    JOINTS.update({
        "shoulder" + side: ((s * 1.32, 0.0, 5.55), (0.60, 0.58)),
        "elbow" + side:    ((s * 1.72, -0.12, 4.45), (0.50, 0.50)),
        "wrist" + side:    ((s * 1.98, -0.28, 3.50), (0.46, 0.46)),
        "hand" + side:     ((s * 2.12, -0.38, 3.02), (0.58, 0.40)),
        "hip" + side:      ((s * 0.60, 0.0, 2.95), (0.62, 0.60)),
        "knee" + side:     ((s * 0.65, 0.0, 1.75), (0.56, 0.56)),
        "ankle" + side:    ((s * 0.70, 0.0, 0.78), (0.50, 0.50)),
        "foot" + side:     ((s * 0.75, -0.85, 0.46), (0.56, 0.42)),
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
smooth = body.modifiers.new("Polish", "SMOOTH")       # a light relax; no rest-shape warnings
smooth.factor = 0.35
smooth.iterations = 3
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
    # name the bones from the joints they run to, so animation scripts can
    # address them ("spine.002", "upper_arm.L", ...) whatever the build order
    BONE_NAMES = {"belly": "spine.001", "chest": "spine.002", "shoulders": "spine.003", "neck": "neck",
                  "head_base": "head.001", "head": "head", "head_top": "head.top"}
    for side in ("L", "R"):
        BONE_NAMES.update({"shoulder" + side: "shoulder." + side, "elbow" + side: "upper_arm." + side,
                           "wrist" + side: "forearm." + side, "hand" + side: "hand." + side,
                           "hip" + side: "hip." + side, "knee" + side: "thigh." + side,
                           "ankle" + side: "shin." + side, "foot" + side: "foot." + side})
    by_pos = {tuple(round(c, 2) for c in pos): name for name, (pos, _) in JOINTS.items()}
    for bone in armature.data.bones:
        tail = tuple(round(c, 2) for c in bone.tail_local)
        joint = by_pos.get(tail)
        bone.name = BONE_NAMES.get(joint, "root" if joint == "pelvis" else bone.name)
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


EYE = material("EyeDark", (0.05, 0.035, 0.03), rough=0.22)     # a little wet, catches light
CATCHLIGHT = material("EyeCatchlight", (1.0, 1.0, 1.0), rough=0.3)
MOUTH = material("MouthDark", (0.09, 0.045, 0.035), rough=0.55)

# eyes: soft ovals sunk slightly into the head, tilted a touch outward, with a catchlight
for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_body((s * 0.52, -2.0, HEAD_C.z + 0.25))
    rot = n.to_track_quat("Z", "Y")
    eye = sphere("Eye" + side, 0.21, loc - n * 0.04, EYE, scale=(0.84, 1.0, 0.5), rot=rot)
    eye.rotation_mode = "XYZ"
    eye.rotation_euler.rotate_axis("Y", math.radians(-8 * s))
    up = Vector((0, 0, 1))
    right = n.cross(up).normalized()
    sphere("Catchlight" + side, 0.045, loc + n * 0.07 + right * (-0.055) + up * 0.07, CATCHLIGHT, parent=eye)

# mouth: a gentle smile drawn as a tapered stroke lying on the face
curve = bpy.data.curves.new("Mouth", "CURVE")
curve.dimensions = "3D"
curve.bevel_depth = 0.034
curve.bevel_resolution = 6
curve.fill_mode = "FULL"
curve.use_fill_caps = True
spline = curve.splines.new("BEZIER")
ARC_R, ARC_SPAN, POINTS = 0.95, math.radians(100), 9
spline.bezier_points.add(POINTS - 1)
for i, bpt in enumerate(spline.bezier_points):
    t = i / (POINTS - 1)
    a = -ARC_SPAN / 2 + t * ARC_SPAN
    # wide arc centred well above the mouth so the corners curl up
    probe = (ARC_R * math.sin(a), -2.0, HEAD_C.z + 0.24 - ARC_R * math.cos(a))
    loc, n = on_body(probe)
    bpt.co = loc + n * 0.012
    bpt.handle_left_type = bpt.handle_right_type = "AUTO"
    bpt.radius = 0.55 + 0.45 * math.sin(math.pi * t)        # slightly thinner at the corners
mouth = bpy.data.objects.new("Mouth", curve)
scene.collection.objects.link(mouth)
mouth.data.materials.append(MOUTH)
link(mouth, body)

# ------------------------------------------------------------ crown
SEGMENTS, PEAKS = 48, 6
R_CROWN = 0.92
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

# ------------------------------------------------------------ face and crown ride on the head bone
# Parented to the body object they would stay behind when the head is posed.
if armature is not None:
    bpy.context.view_layer.update()
    head_pb = armature.pose.bones["head"]
    head_parent = armature.matrix_world @ head_pb.matrix @ Matrix.Translation((0, head_pb.length, 0))
    for name in ("Crown", "EyeL", "EyeR", "Mouth"):
        o = bpy.data.objects[name]
        world = o.matrix_world.copy()
        o.parent = armature
        o.parent_type = "BONE"
        o.parent_bone = "head"
        o.matrix_parent_inverse = head_parent.inverted()
        loc, rot, scl = world.decompose()
        o.location, o.scale = loc, scl
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot

bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = body
print("built", len(col.objects), "objects; armature:", armature.name if armature else None,
      "| bones:", sorted(b.name for b in armature.data.bones) if armature else None)
