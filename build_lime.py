"""Lime: a green blob like Yellow, with round glasses and "LIME" written down
his upper forearm. Yellow's one-mesh body and rig are cloned
(`rig_utils.clone_character`) and tinted lime green, with his eyes, smile and
open mouth, so every animation script drives him unchanged. The glasses (two
rings, a bridge and arms) ride on the head bone; the name is extruded text
laid on the outside of the left forearm just below the elbow, riding on the
forearm bone. He is built at the origin facing -Y in his own "Lime"
collection, hidden from render until the story needs him.

  blender -b slimsico.blend --python build_lime.py --python-expr "import bpy; bpy.ops.wm.save_mainfile()"

Re-running replaces him.
"""
import bpy
import math
import os
import sys
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import clone_character  # noqa: E402

scene = bpy.data.scenes["Scene"]
if bpy.context.window:
    bpy.context.window.scene = scene
LIME = (0.45, 0.85, 0.18)

# ------------------------------------------------------------ cleanup
if "Lime" in bpy.data.collections:
    col = bpy.data.collections["Lime"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures):
    for d in list(block):
        if d.users == 0 and d.name.startswith("Lime"):
            block.remove(d)
col = bpy.data.collections.new("Lime")
scene.collection.children.link(col)

src_body = bpy.data.objects["Character"]
src_rig = bpy.data.objects["CharacterRig"]
body, rig = clone_character(src_body, src_rig, "Lime", LIME,
                            extras=("EyeL", "EyeR", "CatchlightL", "CatchlightR", "Mouth", "MouthOpen"), collection=col)
rig.data.pose_position = "REST"
bpy.context.view_layer.update()


def material(name, rgb, rough=0.6, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    m.diffuse_color = (*rgb, 1)
    return m


FRAME = material("LimeGlasses", (0.08, 0.08, 0.09), rough=0.35, metallic=0.6)
INK = material("LimeInk", (0.05, 0.05, 0.06), rough=0.8)


def attach(obj, bone):
    """Bone-parent obj keeping its world transform (the rig is at rest, at the origin)."""
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    pb = rig.pose.bones[bone]
    bone_world = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = bone_world.inverted()
    loc, rot, scl = world.decompose()
    obj.location, obj.scale = loc, scl
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rot


# ------------------------------------------------------------ the glasses
eyes = {s: bpy.data.objects["Lime_Eye" + s] for s in ("L", "R")}
centres = {s: eyes[s].matrix_world.translation.copy() for s in ("L", "R")}
front = Vector((0, -1, 0))
for s in ("L", "R"):
    c = centres[s] + front * 0.16
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.045, major_segments=40, minor_segments=10, location=c, rotation=(math.radians(90), 0, 0))
    ring = bpy.context.object
    ring.name = "Lime_Glass" + s
    ring.data.materials.append(FRAME)
    bpy.ops.object.shade_smooth()
    attach(ring, "head")
    # the arm: from the outer edge of the ring back along the side of the head
    outer_x = c.x + (-1 if s == "L" else 1) * 0.36
    bpy.ops.mesh.primitive_cube_add(size=1, location=(outer_x + (-1 if s == "L" else 1) * 0.05, c.y + 0.85, c.z + 0.02))
    arm = bpy.context.object
    arm.name = "Lime_GlassArm" + s
    arm.data.transform(Matrix.Diagonal((0.06, 1.8, 0.06, 1.0)))
    arm.rotation_euler = (0, 0, math.radians(-10 if s == "L" else 10))
    arm.data.materials.append(FRAME)
    attach(arm, "head")
# the bridge between the rings
mid = (centres["L"] + centres["R"]) / 2 + front * 0.16
bpy.ops.mesh.primitive_cube_add(size=1, location=(mid.x, mid.y, mid.z + 0.06))
bridge = bpy.context.object
bridge.name = "Lime_GlassBridge"
bridge.data.transform(Matrix.Diagonal((abs(centres["R"].x - centres["L"].x) - 0.6, 0.06, 0.07, 1.0)))
bridge.data.materials.append(FRAME)
attach(bridge, "head")

# ------------------------------------------------------------ "LIME" down the left forearm
fb = rig.data.bones["forearm.L"]
head_w = rig.matrix_world @ fb.head_local
tail_w = rig.matrix_world @ fb.tail_local
along = (tail_w - head_w).normalized()
spot = head_w + (tail_w - head_w) * 0.3                         # the upper forearm, just below the elbow
outward = Vector((-1, 0, 0))                                    # the outside of the left arm
curve = bpy.data.curves.new("LimeName", type="FONT")
curve.body = "LIME"
curve.extrude = 0.012
curve.align_x = "CENTER"
curve.align_y = "CENTER"
text = bpy.data.objects.new("Lime_Name", curve)
scene.collection.objects.link(text)
text.data.materials.append(INK)
bpy.ops.object.select_all(action="DESELECT")
text.select_set(True)
bpy.context.view_layer.objects.active = text
bpy.ops.object.convert(target="MESH")
text = bpy.context.object
# letters read down the arm: baseline along the bone, face outward
up = outward.cross(along).normalized()                          # the text's up, across the arm
rot = Matrix((along, up, outward)).transposed()                 # columns: text x -> along, y -> up, z -> outward
text.data.transform(Matrix.Scale(0.34, 4))
text.matrix_world = Matrix.Translation(spot + outward * 0.5) @ rot.to_4x4()
bpy.context.view_layer.update()
attach(text, "forearm.L")
bpy.context.view_layer.update()
# press the letters onto the arm: shrinkwrap onto the body surface with a small offset
sw = text.modifiers.new("OnArm", "SHRINKWRAP")
sw.target = body
sw.wrap_method = "NEAREST_SURFACEPOINT"
sw.offset = 0.02

rig.data.pose_position = "POSE"
for o in col.objects:
    o.hide_render = True
bpy.ops.object.select_all(action="DESELECT")
print("Lime built:", len(col.objects), "objects | rig", rig.name, "| glasses on head, name on forearm.L")
