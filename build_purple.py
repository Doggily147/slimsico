"""Purple: a hooded, masked figure built from Yellow's rig so the two share
proportions and the same animation scripts drive him.

From the drawing: purple all over with dark hands and feet, a hood with only
two big round eyes showing above a mask, a brown strap running from the right
shoulder across the chest to the left hip plus a brown belt, a glowing green
nanobot core on the chest where the strap crosses, green nanobot clusters on
both shoulders, and two green blades stamped with binary crossed on his back.

The body is a clone of Yellow's one-mesh Skin body and armature
(rig_utils.clone_character) tinted purple; the dark hands and feet are snug
glove and boot shells on the hand and foot bones. Everything else is
bone-parented to the clone's rig too.

Run inside Blender with slimsico.blend open and the main "Scene" active.
Headless:

  blender -b slimsico.blend -S Scene --python build_purple.py -- --still --save

--still renders renders/purple.png (front three-quarter) and
renders/purple_back.png (the blades) with everything else hidden.
--save writes slimsico.blend. Re-running replaces Purple. He is built at the
origin facing -Y and, like the jetski, hidden from render until the story
needs him (set the "Purple" collection's hide_render to False).
"""
import bpy
import math
import os
import sys
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import clone_character  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = os.path.dirname(bpy.data.filepath)
scene = bpy.data.scenes["Scene"]
if bpy.context.window is not None:
    bpy.context.window.scene = scene
assert bpy.context.scene is scene, "run with the main Scene active (headless: -S Scene)"


def material(name, rgb, rough=0.9, metallic=0.0, emit=None, strength=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*rgb, 1)
    return m


# ------------------------------------------------------------ textures follow the repo
# The blend has been saved from other checkouts; images with an absolute path
# that no longer exists render magenta. Point them at this repo's textures/
# folder, relative to the blend, so the file works from any clone.
for im in bpy.data.images:
    if not im.filepath or im.packed_file:
        continue
    if not os.path.exists(bpy.path.abspath(im.filepath)):
        name = os.path.basename(im.filepath)
        for sub in ("textures", os.path.join("textures", "hud")):
            cand = os.path.join(ROOT, sub, name)
            if os.path.exists(cand):
                im.filepath = bpy.path.relpath(cand)
                im.reload()
                print("repointed", im.name, "->", im.filepath)
                break

# ------------------------------------------------------------ cleanup
if "Purple" in bpy.data.collections:
    old = bpy.data.collections["Purple"]
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures):
    for d in list(block):
        if d.users == 0:
            block.remove(d)

col = bpy.data.collections.new("Purple")
scene.collection.children.link(col)

PURPLE = (0.40, 0.20, 0.82)
DARK_PURPLE = (0.16, 0.07, 0.36)
SOOT = (0.08, 0.05, 0.12)
BROWN = (0.42, 0.24, 0.10)
GREEN = (0.20, 0.95, 0.35)

MASK = material("PurpleMask", DARK_PURPLE, rough=0.85)
STRAP = material("PurpleStrap", BROWN, rough=0.7)
BUCKLE = material("PurpleBuckle", (0.75, 0.62, 0.30), rough=0.35, metallic=0.8)
CORE = material("NanobotCore", GREEN, rough=0.3, emit=GREEN, strength=3.0)
NANO = material("Nanobot", (0.12, 0.60, 0.25), rough=0.4, metallic=0.3, emit=GREEN, strength=0.8)
BLADE = material("BinaryBlade", (0.10, 0.55, 0.25), rough=0.25, metallic=0.7)
BINARY = material("BinaryGlow", GREEN, rough=0.5, emit=(0.5, 1.0, 0.6), strength=4.0)
GRIP = material("BladeGrip", (0.06, 0.06, 0.07), rough=0.9)
EYE = material("PurpleEye", (0.02, 0.02, 0.03), rough=0.2)
CATCH = bpy.data.materials.get("EyeCatchlight") or material("EyeCatchlight", (1, 1, 1), rough=0.3)

# ------------------------------------------------------------ the body: Yellow's rig, purple
src_body = bpy.data.objects["Character"]
src_rig = bpy.data.objects["CharacterRig"]
body, rig = clone_character(src_body, src_rig, "Purple", PURPLE, extras=(), collection=col)
rig.rotation_quaternion = (1, 0, 0, 0)
rig.rotation_mode = "XYZ"
rig.rotation_euler = (0, 0, 0)
rig.show_in_front = False
scene.frame_set(1)

skin = body.data.materials[0]
skin.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.06

# ------------------------------------------------------------ helpers
depsgraph = bpy.context.evaluated_depsgraph_get()
body_eval = body.evaluated_get(depsgraph)
HEAD_C = Vector((0, 0, 7.55))            # Yellow's head joint


def on_body(point):
    ok, loc, normal, _ = body_eval.closest_point_on_mesh(Vector(point))
    return loc, normal.normalized()


def link(obj, parent=None):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def bone_attach(obj, bone):
    """Parent obj to a bone of Purple's rig, keeping its current placement."""
    pb = rig.pose.bones[bone]
    scene.view_layers[0].update()
    parent_matrix = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    world = (Matrix.Translation(obj.location) @ obj.rotation_euler.to_matrix().to_4x4()
             @ Matrix.Diagonal((*obj.scale, 1.0)))
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = parent_matrix.inverted()
    loc, rot, scale = world.decompose()
    obj.location = loc
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rot
    obj.scale = scale
    scene.view_layers[0].update()


def sphere(name, radius, loc, mat, scale=(1, 1, 1), rot=None, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments, ring_count=segments // 2, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if rot is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return link(o)


def stroke(name, points, mat, depth, closed=False, taper=None):
    """A bevelled curve through world points (a strap, a band, a rim)."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = depth
    curve.bevel_resolution = 6
    curve.fill_mode = "FULL"
    curve.use_fill_caps = not closed
    spl = curve.splines.new("BEZIER")
    spl.bezier_points.add(len(points) - 1)
    spl.use_cyclic_u = closed
    for i, (bpt, p) in enumerate(zip(spl.bezier_points, points)):
        bpt.co = p
        bpt.handle_left_type = bpt.handle_right_type = "AUTO"
        bpt.radius = taper(i / max(1, len(points) - 1)) if taper else 1.0
    o = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return link(o)


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.rotation_euler = rot
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    link(o, parent)
    return o


def cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=24, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, vertices=verts)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    link(o, parent)
    return o


def ring_on_body(z, n=36, radius_probe=3.0):
    """Points around the body at height z, snapped to the skinned surface."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        loc, nrm = on_body((radius_probe * math.cos(a), radius_probe * math.sin(a), z))
        pts.append(loc + nrm * 0.01)
    return pts


# ------------------------------------------------------------ face: two big eyes over a mask
for s, side in ((-1, "L"), (1, "R")):
    loc, n = on_body((s * 0.50, -2.0, HEAD_C.z + 0.34))
    rot = n.to_track_quat("Z", "Y")
    eye = sphere("Purple_Eye" + side, 0.30, loc - n * 0.05, EYE, scale=(1.0, 1.0, 0.45), rot=rot)
    up = Vector((0, 0, 1))
    right = n.cross(up).normalized()
    cl = sphere("Purple_Catchlight" + side, 0.055, loc + n * 0.09 + right * (-0.08) + up * 0.09, CATCH, segments=16)
    cl.parent = eye
    cl.matrix_parent_inverse = eye.matrix_world.inverted()

# the mask: a dark band around the head just under the eyes
mask_pts = []
for i in range(40):
    a = 2 * math.pi * i / 40
    loc, nrm = on_body((2.5 * math.cos(a), 2.5 * math.sin(a), HEAD_C.z - 0.32))
    mask_pts.append(loc - nrm * 0.05)                    # half sunk into the head
mask = stroke("Purple_Mask", mask_pts, MASK, 0.15, closed=True)
# the hood: a soft peak on top of the head
peak_loc, peak_n = on_body((0, 0.3, HEAD_C.z + 1.5))
peak = sphere("Purple_HoodPeak", 0.42, peak_loc + Vector((0, 0.05, 0.02)), MASK, scale=(1.0, 1.1, 0.55))

# ------------------------------------------------------------ dark gloves and boots
# EEVEE does not read the rig's vertex groups through this modifier stack, so
# the dark hands and feet are snug shells parented to the hand and foot bones.
GLOVE = material("PurpleGlove", SOOT, rough=0.8)
for s, side in ((-1, "L"), (1, "R")):
    glove = sphere("Purple_Glove" + side, 1.0, (s * 2.11, -0.37, 3.02), GLOVE, scale=(0.54, 0.42, 0.64))
    glove.rotation_mode = "XYZ"
    glove.rotation_euler = (0, math.radians(-12 * s), 0)
    bone_attach(glove, "hand." + side)
    boot = sphere("Purple_Boot" + side, 1.0, (s * 0.74, -0.55, 0.52), GLOVE, scale=(0.58, 0.90, 0.48))
    boot.rotation_mode = "XYZ"
    bone_attach(boot, "foot." + side)

# ------------------------------------------------------------ strap, belt, core
front = []
for i in range(9):
    t = i / 8
    p = (1.05 - 2.0 * t, -2.0, 5.95 - 2.7 * t)
    loc, nrm = on_body(p)
    front.append(loc + nrm * 0.03)
back = []
for i in range(1, 8):
    t = i / 8
    p = (-0.95 + 2.0 * t, 2.0, 3.25 + 2.7 * t)
    loc, nrm = on_body(p)
    back.append(loc + nrm * 0.03)
strap = stroke("Purple_Strap", front + back, STRAP, 0.11, closed=True)
belt = stroke("Purple_Belt", ring_on_body(3.35, n=40), STRAP, 0.10, closed=True)
loc, nrm = on_body((0, -2.0, 3.35))
buckle = box("Purple_Buckle", (0.42, 0.12, 0.30), loc + nrm * 0.10, BUCKLE, bevel=0.02)

core_loc, core_n = on_body((0.12, -2.0, 4.95))
core = sphere("Purple_Core", 0.27, core_loc + core_n * 0.12, CORE, scale=(1, 1, 0.7), rot=core_n.to_track_quat("Z", "Y"))
core_ring = cylinder("Purple_CoreRing", 0.36, 0.10, core_loc + core_n * 0.08, NANO, verts=8)
core_ring.rotation_mode = "QUATERNION"
core_ring.rotation_quaternion = core_n.to_track_quat("Z", "Y")

# nanobot clusters on the shoulders: little green shards standing up
for s, side in ((-1, "L"), (1, "R")):
    base_loc, base_n = Vector((s * 1.30, 0.0, 5.55 + 0.18)), Vector((s * 0.35, 0, 1)).normalized()
    for k in range(6):
        a = 2 * math.pi * k / 6 + (0.5 if s > 0 else 0)
        off = Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 0))
        h = 0.36 + 0.12 * ((k * 7) % 3)
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.13, radius2=0.02, depth=h,
                                        location=base_loc + off + base_n * 0.10 + Vector((0, 0, h / 2 - 0.05)))
        shard = bpy.context.object
        shard.name = "Purple_Nano%s%d" % (side, k)
        shard.rotation_euler = (math.radians(12 * math.sin(a)), math.radians(-14 * s + 10 * math.cos(a)), 0)
        shard.data.materials.append(NANO)
        link(shard)
        bone_attach(shard, "shoulder." + side)

# ------------------------------------------------------------ the crossed binary blades on the back
blades_root = bpy.data.objects.new("Purple_Blades", None)
blades_root.empty_display_size = 0.5
scene.collection.objects.link(blades_root)
link(blades_root)
blades_root.location = (0, 1.35, 4.55)

BLADE_LEN, GRIP_LEN = 3.3, 1.0
for s, side in ((-1, "L"), (1, "R")):
    holder = bpy.data.objects.new("Purple_Blade" + side, None)
    holder.empty_display_size = 0.3
    scene.collection.objects.link(holder)
    link(holder, blades_root)
    holder.location = (0, 0, 0)
    holder.rotation_euler = (0, math.radians(33 * s), 0)          # lean each blade out to make the X
    # blade along local +Z, grip below the origin
    blade = box("Purple_BladeEdge" + side, (0.30, 0.055, BLADE_LEN), (0, 0, BLADE_LEN / 2 + 0.15), BLADE, bevel=0.02, parent=holder)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.16, radius2=0.0, depth=0.5, location=(0, 0, BLADE_LEN + 0.4))
    tip = bpy.context.object
    tip.name = "Purple_BladeTip" + side
    tip.scale = (1.0, 0.35, 1.0)
    tip.data.materials.append(BLADE)
    link(tip, holder)
    guard = box("Purple_BladeGuard" + side, (0.70, 0.16, 0.14), (0, 0, 0.08), GRIP, bevel=0.03, parent=holder)
    grip = cylinder("Purple_BladeGrip" + side, 0.11, GRIP_LEN, (0, 0, -GRIP_LEN / 2), GRIP, verts=12, parent=holder)
    pommel = sphere("Purple_BladePommel" + side, 0.15, (0, 0, -GRIP_LEN - 0.05), NANO, segments=16)
    pommel.parent = holder
    pommel.matrix_parent_inverse = holder.matrix_world.inverted()
    # the binary, stamped down both faces of the blade
    for face, y in (("F", 0.035), ("B", -0.035)):
        tc = bpy.data.curves.new("Purple_Binary%s%s" % (side, face), "FONT")
        tc.body = "1 0 0 1 1 0 1 0 0 1"
        tc.size = 0.24
        tc.extrude = 0.006
        tc.align_x = "CENTER"
        tc.align_y = "CENTER"
        t = bpy.data.objects.new(tc.name, tc)
        scene.collection.objects.link(t)
        t.data.materials.append(BINARY)
        link(t, holder)
        t.location = (0, y, BLADE_LEN / 2 + 0.25)
        # text lies in its local XY reading along +X; turn it to read up the
        # blade (+Z) and face out of this side of the blade (+Y or -Y)
        t.rotation_euler = (0, math.radians(-90), math.radians(-90 if y > 0 else 90))
# the parts were placed in the holder's local frame: drop the parent
# inverse that link() set from the holder's world matrix
for o in col.objects:
    if o.parent is not None and o.parent.name.startswith("Purple_Blade"):
        o.matrix_parent_inverse.identity()
bone_attach(blades_root, "spine.003")

# the strap, belt, mask, hood, eyes and core ride on the bones they sit over
for o, bone in ((strap, "spine.002"), (belt, "spine.001"), (buckle, "spine.001"), (core, "spine.002"), (core_ring, "spine.002"),
                (mask, "head"), (peak, "head"),
                (bpy.data.objects["Purple_EyeL"], "head"), (bpy.data.objects["Purple_EyeR"], "head")):
    if o.rotation_mode == "QUATERNION":
        o.rotation_mode = "XYZ"
    bone_attach(o, bone)

# ------------------------------------------------------------ stills
if "--still" in ARGS:
    keep = {"Baseplate", "Skybox", "Sun"}
    hidden = []
    for o in scene.objects:
        if o.name in keep or o.name.startswith("Purple"):
            continue
        if not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    cam_data = bpy.data.cameras.new("PurpleStillCam")
    cam_data.lens = 40
    cam = bpy.data.objects.new("PurpleStillCam", cam_data)
    scene.collection.objects.link(cam)
    old_cam, old_path, old_res = scene.camera, scene.render.filepath, (scene.render.resolution_x, scene.render.resolution_y)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    # the scene's output is the video format (Blender 5 gates the format list
    # behind media_type); switch to image/PNG for the stills and put it back
    ims = scene.render.image_settings
    old_media, old_format = ims.media_type, ims.file_format
    ims.media_type = "IMAGE"
    ims.file_format = "PNG"
    for name, pos in (("purple.png", Vector((-9.5, -13.5, 6.8))), ("purple_back.png", Vector((8.5, 14.0, 6.8)))):
        cam.location = pos
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (Vector((0, 0, 4.6)) - pos).to_track_quat("-Z", "Y")
        scene.render.filepath = os.path.join(ROOT, "renders", name)
        bpy.ops.render.render(write_still=True)
        print("still ->", scene.render.filepath)
    ims.media_type = old_media
    ims.file_format = old_format
    scene.camera, scene.render.filepath = old_cam, old_path
    scene.render.resolution_x, scene.render.resolution_y = old_res
    for o in hidden:
        o.hide_render = False
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)

# not in the story yet: hidden from render, like the jetski
col.hide_render = True

if "--save" in ARGS:
    bpy.ops.wm.save_mainfile()
    print("saved", bpy.data.filepath)

print("built Purple:", len(col.objects), "objects; rig", rig.name)
