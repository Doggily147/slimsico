"""The monster: a big, hulking beast built the same way as Yellow so it sits in
the same world: ONE connected body from a joint skeleton skinned with the Skin
modifier and subdivided, with an armature generated from the same skeleton.
About 13 studs tall (Yellow is 9): a broad chest, a heavy brow and muzzle with
an underbite and two tusks, small curved horns, long gorilla arms with three
claws, short thick legs, a thick tail, and a row of spikes down the back.
Deep teal skin with a paler belly, glowing amber eyes.

Run inside Blender with slimsico.blend open. Re-running replaces the monster.
It is built at the origin facing -Y, standing on the plate; animation scripts
move it.
"""
import bmesh
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene


def material(name, rgb, rough=0.9, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    m.diffuse_color = (*rgb, 1)
    return m


# ------------------------------------------------------------ cleanup
if "Monster" in bpy.data.collections:
    col = bpy.data.collections["Monster"]
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
for block in (bpy.data.meshes, bpy.data.armatures):
    for d in list(block):
        if d.users == 0:
            block.remove(d)
col = bpy.data.collections.new("Monster")
scene.collection.children.link(col)


def link(obj, parent=None):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


# ------------------------------------------------------------ materials
TEAL, BELLY = (0.06, 0.26, 0.24), (0.55, 0.62, 0.42)
SKIN = material("MonsterSkin", TEAL, rough=0.8)
nt = SKIN.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Subsurface Weight"].default_value = 0.1
bsdf.inputs["Subsurface Radius"].default_value = (0.3, 0.5, 0.4)
# the belly and the underside of the muzzle are paler: blend by the object-space
# front-to-back coordinate (the skinned mesh has no usable generated coords)
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
rng = nt.nodes.new("ShaderNodeMapRange")
rng.inputs["From Min"].default_value = -2.4
rng.inputs["From Max"].default_value = -0.4
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[0].color = (*BELLY, 1)
ramp.color_ramp.elements[1].position = 0.7
ramp.color_ramp.elements[1].color = (*TEAL, 1)
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 1.6
noise.inputs["Detail"].default_value = 6.0
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.18
nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Y"], rng.inputs["Value"])
nt.links.new(rng.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
HORN = material("MonsterHorn", (0.82, 0.74, 0.55), rough=0.55)
TOOTH = material("MonsterTooth", (0.95, 0.93, 0.85), rough=0.4)
PUPIL = material("MonsterPupil", (0.03, 0.02, 0.02), rough=0.3)
EYE = bpy.data.materials.get("MonsterEye") or bpy.data.materials.new("MonsterEye")
EYE.use_nodes = True
eb = EYE.node_tree.nodes["Principled BSDF"]
eb.inputs["Base Color"].default_value = (1.0, 0.55, 0.08, 1)
eb.inputs["Emission Color"].default_value = (1.0, 0.5, 0.05, 1)
eb.inputs["Emission Strength"].default_value = 3.5
eb.inputs["Roughness"].default_value = 0.25
EYE.diffuse_color = (1.0, 0.55, 0.08, 1)

# ------------------------------------------------------------ body skeleton
# name: position, (radius across, radius front-to-back). Facing -Y.
JOINTS = {
    "pelvis":    ((0, 0.2, 4.7), (1.9, 1.6)),
    "belly":     ((0, 0.0, 6.1), (2.55, 2.15)),
    "chest":     ((0, -0.2, 7.9), (2.9, 2.3)),
    "shoulders": ((0, -0.2, 9.3), (2.55, 1.95)),
    "neck":      ((0, -0.4, 10.0), (1.25, 1.15)),
    "head_base": ((0, -0.5, 10.7), (1.95, 1.8)),
    "head":      ((0, -0.7, 11.7), (2.25, 2.05)),
    "head_top":  ((0, -0.5, 12.7), (1.55, 1.45)),
    "snout":     ((0, -2.6, 11.2), (1.45, 1.0)),
    "jaw":       ((0, -2.7, 10.0), (1.5, 0.85)),
    "tail1":     ((0, 2.1, 4.4), (0.95, 0.85)),
    "tail2":     ((0, 3.8, 3.5), (0.7, 0.62)),
    "tail3":     ((0, 5.3, 2.5), (0.42, 0.38)),
}
CHAIN = [("pelvis", "belly"), ("belly", "chest"), ("chest", "shoulders"), ("shoulders", "neck"),
         ("neck", "head_base"), ("head_base", "head"), ("head", "head_top"), ("head", "snout"),
         ("head_base", "jaw"), ("pelvis", "tail1"), ("tail1", "tail2"), ("tail2", "tail3")]
for s, side in ((-1, "L"), (1, "R")):
    JOINTS.update({
        "shoulder" + side: ((s * 3.3, -0.2, 9.0), (1.25, 1.15)),
        "elbow" + side:    ((s * 4.4, -0.5, 6.5), (1.0, 0.95)),
        "wrist" + side:    ((s * 5.0, -1.1, 4.2), (0.9, 0.85)),
        "hand" + side:     ((s * 5.2, -1.7, 3.1), (1.25, 0.9)),
        "hip" + side:      ((s * 1.35, 0.1, 4.2), (1.25, 1.15)),
        "knee" + side:     ((s * 1.5, -0.1, 2.5), (1.05, 1.0)),
        "ankle" + side:    ((s * 1.6, 0.1, 1.15), (0.95, 0.9)),
        "foot" + side:     ((s * 1.7, -1.4, 0.7), (1.15, 0.85)),
    })
    CHAIN += [("shoulders", "shoulder" + side), ("shoulder" + side, "elbow" + side),
              ("elbow" + side, "wrist" + side), ("wrist" + side, "hand" + side),
              ("pelvis", "hip" + side), ("hip" + side, "knee" + side),
              ("knee" + side, "ankle" + side), ("ankle" + side, "foot" + side)]

mesh = bpy.data.meshes.new("MonsterBody")
bm = bmesh.new()
verts = {name: bm.verts.new(pos) for name, (pos, _) in JOINTS.items()}
for a, b in CHAIN:
    bm.edges.new((verts[a], verts[b]))
bm.verts.index_update()
order = list(JOINTS.keys())
bm.to_mesh(mesh)
bm.free()

body = bpy.data.objects.new("Monster", mesh)
scene.collection.objects.link(body)
link(body)
body.data.materials.append(SKIN)
skin = body.modifiers.new("Skin", "SKIN")
skin.use_smooth_shade = True
skin.branch_smoothing = 1.0
for i, name in enumerate(order):
    sv = body.data.skin_vertices[0].data[i]
    sv.radius = JOINTS[name][1]
    sv.use_root = (name == "pelvis")
sub = body.modifiers.new("Subdivision", "SUBSURF")
sub.levels = 2
sub.render_levels = 3
smooth = body.modifiers.new("Polish", "SMOOTH")
smooth.factor = 0.35
smooth.iterations = 3
body.data.shade_smooth()

# armature from the skeleton, bones named from the joints they run to
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.skin_armature_create(modifier="Skin")
rig = bpy.context.object
rig.name = "MonsterRig"
rig.show_in_front = False
rig.data.display_type = "STICK"
link(rig)
body.parent = rig
body.matrix_parent_inverse = rig.matrix_world.inverted()
arm_mod = next(m for m in body.modifiers if m.type == "ARMATURE")
body.modifiers.move(body.modifiers.find(arm_mod.name), len(body.modifiers) - 1)
BONE_NAMES = {"belly": "spine.001", "chest": "spine.002", "shoulders": "spine.003", "neck": "neck",
              "head_base": "head.001", "head": "head", "head_top": "head.top", "snout": "snout", "jaw": "jaw",
              "tail1": "tail.001", "tail2": "tail.002", "tail3": "tail.003"}
for side in ("L", "R"):
    BONE_NAMES.update({"shoulder" + side: "shoulder." + side, "elbow" + side: "upper_arm." + side,
                       "wrist" + side: "forearm." + side, "hand" + side: "hand." + side,
                       "hip" + side: "hip." + side, "knee" + side: "thigh." + side,
                       "ankle" + side: "shin." + side, "foot" + side: "foot." + side})
by_pos = {tuple(round(c, 2) for c in pos): name for name, (pos, _) in JOINTS.items()}
for bone in rig.data.bones:
    tail = tuple(round(c, 2) for c in bone.tail_local)
    bone.name = BONE_NAMES.get(by_pos.get(tail), bone.name)

# ------------------------------------------------------------ the details ride on bones
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_eval = body.evaluated_get(depsgraph)


def on_body(point):
    ok, loc, normal, _ = body_eval.closest_point_on_mesh(Vector(point))
    return loc, normal.normalized()


def attach(obj, bone_name):
    """Bone-parent obj to the rig keeping its world transform."""
    pb = rig.pose.bones[bone_name]
    bone_world = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = bone_world.inverted()
    loc, rot, scl = world.decompose()
    obj.location, obj.scale = loc, scl
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rot


def cone(name, radius, length, base, direction, mat, bone, tip=0.0, curve=0.0):
    """A cone rising from `base` along `direction`, parented to `bone`.
    `curve` bends the tip back (a horn) by shearing the upper vertices."""
    d = Vector(direction).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius, radius2=tip, depth=length,
                                    location=Vector(base) + d * (length / 2))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    if curve:
        bmc = bmesh.new()
        bmc.from_mesh(o.data)
        for v in bmc.verts:
            k = (v.co.z + length / 2) / length
            v.co.y += curve * k * k * length
        bmc.to_mesh(o.data)
        bmc.free()
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = radius * 0.25
    bev.segments = 3
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    link(o)
    attach(o, bone)
    return o


def sphere(name, radius, loc, mat, scale=(1, 1, 1), rot=None, bone=None, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if rot is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    link(o, parent)
    if bone:
        attach(o, bone)
    return o


HEAD = Vector(JOINTS["head"][0])
# eyes: sunk under the brow either side of the muzzle, glowing, with a slit pupil
for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_body((s * 1.15, -3.0, HEAD.z + 0.35))
    rot = n.to_track_quat("Z", "Y")
    eye = sphere("MonsterEye" + side, 0.42, loc - n * 0.12, EYE, scale=(1.0, 0.85, 0.55), rot=rot, bone="head")
    sphere("MonsterPupil" + side, 0.13, loc + n * 0.14, PUPIL, scale=(0.5, 1.0, 0.6), rot=rot, bone="head")
# horns: curved back and out from the top of the head
for s, side in ((-1, "L"), (1, "R")):
    base, n = on_body((s * 1.25, 0.2, HEAD.z + 1.55))
    cone("MonsterHorn" + side, 0.45, 1.6, base - n * 0.25, (s * 0.5, 0.55, 0.67), HORN, "head", tip=0.06, curve=0.5)
# tusks up from the lower jaw, teeth down from the muzzle
for s, side in ((-1, "L"), (1, "R")):
    base, n = on_body((s * 0.95, -4.0, 10.3))
    cone("MonsterTusk" + side, 0.3, 1.15, base - n * 0.2, (s * 0.15, -0.3, 0.94), TOOTH, "jaw", tip=0.04)
for i in range(6):
    x = -0.95 + i * 0.38
    base, n = on_body((x, -3.75, 10.9))
    cone("MonsterTooth%d" % (i + 1), 0.11, 0.38, base - n * 0.08, (0, -0.25, -0.97), TOOTH, "snout", tip=0.02)
# nostrils
for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_body((s * 0.45, -4.2, 11.4))
    sphere("MonsterNostril" + side, 0.16, loc - n * 0.1, PUPIL, scale=(1.0, 1.0, 0.7), rot=n.to_track_quat("Z", "Y"), bone="snout")
# spikes down the back and along the tail
SPINE_SPIKES = [("spine.003", (0, 1.7, 9.6), 0.5, 1.4), ("spine.002", (0, 2.1, 8.4), 0.55, 1.5), ("spine.002", (0, 2.3, 7.2), 0.5, 1.4),
                ("spine.001", (0, 2.2, 6.0), 0.45, 1.2), ("tail.001", (0, 3.0, 4.9), 0.36, 0.9), ("tail.002", (0, 4.6, 3.9), 0.28, 0.7)]
for i, (bone, probe, r, length) in enumerate(SPINE_SPIKES):
    base, n = on_body(probe)
    cone("MonsterSpike%d" % (i + 1), r, length, base - n * 0.15, (n + Vector((0, 0.3, 0.6))).normalized(), HORN, bone, tip=0.04)
# three claws on each hand and foot
for s, side in ((-1, "L"), (1, "R")):
    hand = Vector(JOINTS["hand" + side][0])
    for k, dx in enumerate((-0.55, 0.0, 0.55)):
        base, n = on_body((hand.x + dx, hand.y - 1.0, hand.z - 0.25))
        cone("MonsterClaw%s%d" % (side, k), 0.2, 0.9, base - n * 0.1, (dx * 0.25, -0.75, -0.6), HORN, "hand." + side, tip=0.02)
    foot = Vector(JOINTS["foot" + side][0])
    for k, dx in enumerate((-0.6, 0.0, 0.6)):
        base, n = on_body((foot.x + dx, foot.y - 0.9, foot.z - 0.1))
        cone("MonsterToe%s%d" % (side, k), 0.2, 0.8, base - n * 0.1, (dx * 0.2, -0.9, -0.35), HORN, "foot." + side, tip=0.02)

# the monster starts hidden; the beat script shows it when the crate breaks
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = body
top = max((body_eval.matrix_world @ v.co).z for v in body_eval.data.vertices)
print("monster built:", len(col.objects), "objects | height %.1f" % top, "| bones:", sorted(b.name for b in rig.data.bones))
