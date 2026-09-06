"""Office test scene ("OfficeTest", a second scene in the same file).

Yellow walks into an office and pulls a gun on the worker at the desk.
Attempt 1: he shoots; the worker and chair go over backwards. Time rewinds.
Attempt 2: he slips on his way forward, lands on his back, and a police
officer bursts in and arrests him. Time rewinds.
Attempt 3: the worker has had enough, leans over the desk and yells at him;
Yellow shrinks back and lowers the gun.

The rewinds are done at render time (render_office_test.py reverses the
footage between the marked frames); here the timeline just re-keys the
"pointing the gun" pose at the start of each attempt.

Run inside Blender with slimsico.blend open after build_character.py (the
characters are cloned from Yellow). Re-running rebuilds the whole scene.
"""
import bmesh
import bpy
import math
import os
import sys
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import (Poser, clone_character, floor_violations, gait_dirs, ground_clamp, key,  # noqa: E402
                       motion_spikes, set_interpolation, sym)

SCENE_NAME = "OfficeTest"
FPS = 24
main = bpy.data.scenes["Scene"]

# ------------------------------------------------------------ fresh scene
if SCENE_NAME in bpy.data.scenes:
    old = bpy.data.scenes[SCENE_NAME]
    for o in list(old.objects):
        if o.name.startswith("Office") or o.name.split("_")[0] in ("Robber", "Worker", "Officer", "RobberRig", "WorkerRig", "OfficerRig"):
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(old)
for c in list(bpy.data.collections):
    if c.name.startswith(("Office", "OfficeCast")):
        bpy.data.collections.remove(c)
for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.curves):
    for d in list(block):
        if d.users == 0:
            block.remove(d)

scene = bpy.data.scenes.new(SCENE_NAME)
bpy.context.window.scene = scene
scene.render.fps = FPS
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 32
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = -0.2
scene.world = main.world
scene.render.image_settings.media_type = "VIDEO"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.filepath = "//renders/office_raw.mp4"

col = bpy.data.collections.new("Office")
scene.collection.children.link(col)
chars = bpy.data.collections.new("OfficeCast")
scene.collection.children.link(chars)


def material(name, rgb, rough=0.8, metallic=0.0, emit=None):
    m = bpy.data.materials.new("Office_" + name)
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


CARPET = material("Carpet", (0.24, 0.27, 0.32), rough=0.95)
WALL = material("Wall", (0.86, 0.85, 0.8), rough=0.9)
CEILING = material("Ceiling", (0.95, 0.95, 0.94), rough=0.9)
TRIM = material("Trim", (0.95, 0.94, 0.9), rough=0.6)
WALNUT = material("Walnut", (0.32, 0.2, 0.11), rough=0.55)
BLACK = material("Black", (0.03, 0.03, 0.03), rough=0.5)
GREY = material("Grey", (0.45, 0.46, 0.48), rough=0.6, metallic=0.3)
SCREEN = material("Screen", (0.05, 0.1, 0.25), rough=0.3, emit=((0.25, 0.45, 0.9), 1.2))
GLASS = material("Glass", (0.75, 0.88, 1.0), rough=0.05, emit=((0.55, 0.72, 0.95), 0.8))
PAPER = material("Paper", (0.96, 0.96, 0.94), rough=0.8)
MUG = material("Mug", (0.85, 0.2, 0.2), rough=0.4)
PLANT = material("Plant", (0.16, 0.45, 0.18), rough=0.8)
POT = material("Pot", (0.55, 0.32, 0.22), rough=0.8)
DOOR = material("Door", (0.5, 0.33, 0.18), rough=0.6)
BRASS = material("Brass", (0.9, 0.72, 0.3), rough=0.3, metallic=0.9)
TIE = material("Tie", (0.75, 0.1, 0.15), rough=0.6)
CAP = material("Cap", (0.08, 0.1, 0.25), rough=0.8)
GUN = material("Gun", (0.12, 0.12, 0.13), rough=0.45, metallic=0.8)
FLASH = material("Flash", (1, 0.9, 0.5), emit=((1.0, 0.8, 0.3), 40))


def box(name, size, loc, mat, parent=None, rot=(0, 0, 0), bevel=0.0, coll=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Office_" + name
    # scale the mesh data itself (the apply-scale operator also resets the
    # object's location in this context)
    o.data.transform(Matrix.Diagonal((*size, 1.0)))
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 2
    for c in o.users_collection:
        c.objects.unlink(o)
    (coll or col).objects.link(o)
    if parent is not None:
        scene.view_layers[0].update()          # a just-made parent may not be evaluated yet
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def cylinder(name, radius, depth, loc, mat, parent=None, rot=(0, 0, 0), verts=32, coll=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = "Office_" + name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    for c in o.users_collection:
        c.objects.unlink(o)
    (coll or col).objects.link(o)
    if parent is not None:
        scene.view_layers[0].update()
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def empty(name, loc, coll=None):
    e = bpy.data.objects.new("Office_" + name, None)
    e.location = loc
    (coll or col).objects.link(e)
    return e


# ------------------------------------------------------------ the room
W, D, H = 44.0, 34.0, 16.0            # width (x), depth (y), height
box("Floor", (W, D, 0.5), (0, 0, -0.25), CARPET)
box("Ceiling", (W, D, 0.3), (0, 0, H + 0.15), CEILING)
box("WallBack", (W, 0.5, H), (0, D / 2, H / 2), WALL)
box("WallFront", (W, 0.5, H), (0, -D / 2, H / 2), WALL)
box("WallRight", (0.5, D, H), (W / 2, 0, H / 2), WALL)
# left wall with a door opening at y = -8 (6 wide, 11 high)
DOOR_Y, DOOR_W, DOOR_H = -8.0, 6.0, 11.0
box("WallLeftA", (0.5, (D / 2 + DOOR_Y - DOOR_W / 2), H), (-W / 2, (-D / 2 + DOOR_Y - DOOR_W / 2) / 2, H / 2), WALL)
box("WallLeftB", (0.5, (D / 2 - DOOR_Y - DOOR_W / 2), H), (-W / 2, (D / 2 + DOOR_Y + DOOR_W / 2) / 2, H / 2), WALL)
box("WallLeftTop", (0.5, DOOR_W, H - DOOR_H), (-W / 2, DOOR_Y, DOOR_H + (H - DOOR_H) / 2), WALL)
for side, x in (("L", -W / 2 + 0.3), ("R", W / 2 - 0.3)):
    box("Skirting" + side, (0.15, D, 0.8), (x, 0, 0.4), TRIM)
for side, y in (("B", D / 2 - 0.3), ("F", -D / 2 + 0.3)):
    box("Skirting" + side, (W, 0.15, 0.8), (0, y, 0.4), TRIM)
# door on a hinge empty at the back edge of the opening
hinge = empty("DoorHinge", (-W / 2 + 0.25, DOOR_Y + DOOR_W / 2, 0))
box("DoorFrameTop", (0.7, DOOR_W + 0.6, 0.4), (-W / 2, DOOR_Y, DOOR_H + 0.2), TRIM)
box("DoorFrameA", (0.7, 0.3, DOOR_H), (-W / 2, DOOR_Y - DOOR_W / 2 - 0.15, DOOR_H / 2), TRIM)
box("DoorFrameB", (0.7, 0.3, DOOR_H), (-W / 2, DOOR_Y + DOOR_W / 2 + 0.15, DOOR_H / 2), TRIM)
door = box("Door", (0.3, DOOR_W - 0.2, DOOR_H - 0.2), (-W / 2 + 0.25, DOOR_Y, DOOR_H / 2), DOOR, parent=hinge, bevel=0.03)
box("DoorPanelA", (0.1, DOOR_W - 1.4, 3.6), (-W / 2 + 0.05, DOOR_Y, 7.8), DOOR, parent=hinge, bevel=0.02)
box("DoorPanelB", (0.1, DOOR_W - 1.4, 4.6), (-W / 2 + 0.05, DOOR_Y, 2.9), DOOR, parent=hinge, bevel=0.02)
cylinder("DoorKnob", 0.22, 0.5, (-W / 2, DOOR_Y - DOOR_W / 2 + 0.7, 5.2), BRASS, parent=hinge, rot=(0, math.radians(90), 0))
# window in the back wall
box("WindowFrame", (12.6, 0.7, 7.6), (2, D / 2, 9.5), TRIM)
box("WindowGlass", (11.8, 0.2, 6.8), (2, D / 2 - 0.2, 9.5), GLASS)
box("WindowBarV", (0.25, 0.3, 6.8), (2, D / 2 - 0.25, 9.5), TRIM)
box("WindowBarH", (11.8, 0.3, 0.25), (2, D / 2 - 0.25, 9.5), TRIM)
# details: clock, picture, filing cabinet, plant
cylinder("Clock", 1.4, 0.25, (-12, D / 2 - 0.3, 12), TRIM, rot=(math.radians(90), 0, 0))
cylinder("ClockFace", 1.2, 0.1, (-12, D / 2 - 0.45, 12), PAPER, rot=(math.radians(90), 0, 0))
box("ClockHandA", (0.12, 0.05, 0.9), (-12, D / 2 - 0.55, 12.4), BLACK)
box("ClockHandB", (0.7, 0.05, 0.12), (-11.7, D / 2 - 0.55, 12), BLACK)
box("Picture", (5, 0.3, 3.6), (14, D / 2 - 0.3, 10), WALNUT)
box("PictureCanvas", (4.4, 0.15, 3.0), (14, D / 2 - 0.5, 10), material("Canvas", (0.3, 0.55, 0.75)))
box("Cabinet", (4, 3, 8), (W / 2 - 2.6, D / 2 - 2, 4), GREY, bevel=0.05)
for i in range(3):
    box("Drawer%d" % i, (3.6, 0.2, 2.2), (W / 2 - 2.6, D / 2 - 3.6, 1.4 + i * 2.5), GREY, bevel=0.03)
    box("Handle%d" % i, (1.2, 0.2, 0.2), (W / 2 - 2.6, D / 2 - 3.8, 1.4 + i * 2.5), BLACK)
cylinder("Pot", 1.4, 2.4, (-W / 2 + 3, D / 2 - 3, 1.2), POT)
for i, (dx, dy, dz, r) in enumerate(((0, 0, 3.6, 1.6), (0.9, 0.4, 3.0, 1.1), (-0.8, -0.5, 3.2, 1.2), (0.3, -0.9, 4.2, 1.0), (-0.4, 0.8, 4.4, 0.9))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=20, ring_count=12, location=(-W / 2 + 3 + dx, D / 2 - 3 + dy, dz))
    leaf = bpy.context.object
    leaf.name = "Office_Leaf%d" % i
    leaf.scale = (1, 1, 0.7)
    leaf.data.materials.append(PLANT)
    bpy.ops.object.shade_smooth()
    for c in leaf.users_collection:
        c.objects.unlink(leaf)
    col.objects.link(leaf)
# lighting: a ceiling panel light plus the shared sun through the window
bpy.ops.object.light_add(type="AREA", location=(0, 2, H - 0.4))
panel = bpy.context.object
panel.name = "Office_PanelLight"
panel.data.energy = 2500
panel.data.size = 14
panel.data.color = (1.0, 0.97, 0.92)
for c in panel.users_collection:
    c.objects.unlink(panel)
col.objects.link(panel)
scene.collection.objects.link(bpy.data.objects["Sun"])

# ------------------------------------------------------------ desk, chair, kit
DESK = Vector((0, 4, 0))
DESK_H = 4.2
box("DeskTop", (14, 6, 0.4), DESK + Vector((0, 0, DESK_H - 0.2)), WALNUT, bevel=0.04)
box("DeskSideL", (0.4, 5.6, DESK_H - 0.4), DESK + Vector((-6.8, 0, (DESK_H - 0.4) / 2)), WALNUT)
box("DeskSideR", (0.4, 5.6, DESK_H - 0.4), DESK + Vector((6.8, 0, (DESK_H - 0.4) / 2)), WALNUT)
box("DeskModesty", (13.2, 0.3, 2.6), DESK + Vector((0, -2.2, 2.4)), WALNUT)
box("DeskDrawers", (3.6, 5.2, DESK_H - 0.6), DESK + Vector((4.8, 0, (DESK_H - 0.6) / 2)), WALNUT)
for i in range(3):
    box("DeskHandle%d" % i, (1.0, 0.15, 0.15), DESK + Vector((4.8, 2.7, 0.8 + i * 1.1)), BRASS)
# the monitor sits to the worker's left so his face is clear from the front
MON = Vector((4.3, 0, 0))
box("MonitorBase", (2.2, 1.4, 0.15), DESK + MON + Vector((0, -0.4, DESK_H + 0.08)), BLACK)
box("MonitorNeck", (0.4, 0.3, 1.2), DESK + MON + Vector((0, -0.4, DESK_H + 0.7)), BLACK)
box("MonitorBody", (5.0, 0.3, 3.0), DESK + MON + Vector((0, -0.4, DESK_H + 2.7)), BLACK, bevel=0.03)
box("MonitorScreen", (4.6, 0.08, 2.6), DESK + MON + Vector((0, -0.2, DESK_H + 2.7)), SCREEN)
box("Keyboard", (4.4, 1.5, 0.18), DESK + Vector((0.8, 1.4, DESK_H + 0.09)), BLACK, bevel=0.02)
box("Mouse", (0.6, 0.9, 0.3), DESK + Vector((3.9, 1.6, DESK_H + 0.15)), BLACK, bevel=0.06)
box("Papers", (2.2, 3.0, 0.25), DESK + Vector((-4.2, 0.4, DESK_H + 0.12)), PAPER)
cylinder("Mug", 0.45, 1.0, DESK + Vector((-2.6, 1.6, DESK_H + 0.5)), MUG)
cylinder("MugHandle", 0.3, 0.12, DESK + Vector((-2.1, 1.6, DESK_H + 0.5)), MUG, rot=(0, math.radians(90), 0), verts=16)
cylinder("LampBase", 0.9, 0.2, DESK + Vector((5.2, -1.6, DESK_H + 0.1)), BLACK)
box("LampArm", (0.15, 0.15, 3.2), DESK + Vector((5.2, -1.6, DESK_H + 1.7)), BLACK)
cylinder("LampShade", 0.9, 1.2, DESK + Vector((5.2, -1.2, DESK_H + 3.2)), BLACK, rot=(math.radians(-35), 0, 0))

# the chair's empty sits at the back edge of its base, so tipping it over is a
# rotation about that edge
CHAIR_C = DESK + Vector((0, 5.5, 0))                 # chair centre
chair = empty("ChairRoot", CHAIR_C + Vector((0, 2.0, 0)), coll=chars)
SEAT_H = 2.2
CO = chair.location + Vector((0, -2.0, 0))           # parts are placed in world space around the chair centre
cylinder("ChairBase", 2.2, 0.25, CO + Vector((0, 0, 0.15)), BLACK, parent=chair)
cylinder("ChairPost", 0.25, SEAT_H - 0.4, CO + Vector((0, 0, SEAT_H / 2)), GREY, parent=chair, verts=16)
box("ChairSeat", (4.0, 4.0, 0.5), CO + Vector((0, 0, SEAT_H - 0.25)), BLACK, parent=chair, bevel=0.1)
box("ChairBack", (4.0, 0.5, 4.4), CO + Vector((0, 1.9, SEAT_H + 2.2)), BLACK, parent=chair, bevel=0.1)
for i in range(5):
    a = 2 * math.pi * i / 5
    cylinder("ChairWheel%d" % i, 0.25, 0.3, CO + Vector((2.0 * math.cos(a), 2.0 * math.sin(a), 0.2)), GREY, parent=chair, rot=(0, math.radians(90), a), verts=12)

# ------------------------------------------------------------ the cast (cloned from Yellow)
src_body = bpy.data.objects["Character"]
src_rig = bpy.data.objects["CharacterRig"]
robber, robber_rig = clone_character(src_body, src_rig, "Robber", (1.0, 0.72, 0.08),
                                     extras=("EyeL", "EyeR", "CatchlightL", "CatchlightR", "Mouth", "Crown",
                                             "Gem1", "Gem2", "Gem3", "Gem4", "Gem5", "Gem6"), collection=chars)
worker, worker_rig = clone_character(src_body, src_rig, "Worker", (0.32, 0.55, 0.9), collection=chars)
officer, officer_rig = clone_character(src_body, src_rig, "Officer", (0.14, 0.18, 0.42), collection=chars)
for rig in (robber_rig, worker_rig, officer_rig):
    rig.rotation_mode = "XYZ"
    rig.show_in_front = False


def bone_attach(obj, rig, bone):
    """Parent obj to a bone, keeping obj's current world placement."""
    pb = rig.pose.bones[bone]
    scene.view_layers[0].update()
    parent_matrix = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    # build the placement from the object's own channels: a just-created object
    # may not have been evaluated yet, so its matrix_world can still be identity
    world = (Matrix.Translation(obj.location) @ obj.rotation_euler.to_matrix().to_4x4()
             @ Matrix.Diagonal((*obj.scale, 1.0)))
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = parent_matrix.inverted()
    # set the channels explicitly; assigning matrix_basis here was not sticking
    loc, rot, scale = world.decompose()
    obj.location = loc
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rot
    obj.scale = scale
    scene.view_layers[0].update()


# the worker gets a tie, the officer a cap and badge, the robber a pistol
tie = box("Tie", (0.55, 0.15, 2.4), (0, -1.05, 5.4), TIE, coll=chars, bevel=0.03)
tie_knot = box("TieKnot", (0.7, 0.25, 0.5), (0, -1.05, 6.7), TIE, coll=chars, bevel=0.05)
for o in (tie, tie_knot):
    bone_attach(o, worker_rig, "spine.003")
cap_top = cylinder("CapTop", 1.05, 0.7, (0, 0, 9.05), CAP, coll=chars)
cap_brim = box("CapBrim", (1.9, 1.3, 0.12), (0, -1.15, 8.75), BLACK, coll=chars, bevel=0.03)
badge = cylinder("Badge", 0.3, 0.1, (-0.55, -1.05, 5.9), BRASS, rot=(math.radians(90), 0, 0), coll=chars, verts=8)
bone_attach(cap_top, officer_rig, "head")
bone_attach(cap_brim, officer_rig, "head")
bone_attach(badge, officer_rig, "spine.003")
# the worker's shouting face: an open mouth and angry brows, shown only for the yell
ANGRY = material("Angry", (0.1, 0.03, 0.03), rough=0.7)
w_mouth = bpy.data.objects["Worker_Mouth"]
scene.view_layers[0].update()
# place the shout from the eyes (reliably evaluated), a little below them
eye_l, eye_r = (bpy.data.objects["Worker_Eye" + s].matrix_world.translation for s in ("L", "R"))
mouth_pos = (eye_l + eye_r) / 2 + Vector((0, -0.08, -0.72))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, segments=24, ring_count=12, location=mouth_pos + Vector((0, -0.05, -0.05)))
shout = bpy.context.object
shout.name = "Worker_Shout"
shout.scale = (1.35, 0.5, 1.1)
shout.data.materials.append(ANGRY)
bpy.ops.object.shade_smooth()
for c in shout.users_collection:
    c.objects.unlink(shout)
chars.objects.link(shout)
brows = []
for side in ("L", "R"):
    eye = bpy.data.objects["Worker_Eye" + side]
    scene.view_layers[0].update()
    p = eye.matrix_world.translation + Vector((0, -0.04, 0.34))
    s = -1 if side == "L" else 1
    brow = box("Brow" + side, (0.5, 0.08, 0.12), p, ANGRY, coll=chars, rot=(0, math.radians(-28 * s), 0), bevel=0.02)
    brow.name = "Worker_Brow" + side
    brows.append(brow)
for o in (shout, *brows):
    bone_attach(o, worker_rig, "head")
# pistol built along the hand bone (its +Y runs to the fingertips)
gun_root = empty("GunRoot", (0, 0, 0), coll=chars)
box("GunSlide", (0.32, 1.5, 0.42), (0, 0.55, 0.28), GUN, parent=gun_root, bevel=0.03)
box("GunBarrel", (0.16, 0.5, 0.16), (0, 1.5, 0.33), GUN, parent=gun_root)
box("GunGrip", (0.3, 0.42, 0.9), (0, -0.05, -0.3), GUN, parent=gun_root, rot=(math.radians(-18), 0, 0), bevel=0.03)
box("GunTrigger", (0.1, 0.12, 0.35), (0, 0.32, -0.15), GUN, parent=gun_root)
flash = bpy.data.objects.new("Office_Flash", bpy.data.meshes.new("Office_Flash"))
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.9)
bm.to_mesh(flash.data)
bm.free()
flash.data.materials.append(FLASH)
flash.location = (0, 2.1, 0.33)
flash.parent = gun_root
flash.scale = (1, 1.6, 1)
chars.objects.link(flash)
flash.hide_render = True
flash.hide_viewport = True

# ------------------------------------------------------------ placement
ROBBER_START = Vector((-W / 2 - 4.5, DOOR_Y, 0))       # outside the door, facing +X
ROBBER_MARK = Vector((0, -3.0, 0))                      # in front of the desk, facing +Y
WORKER_POS = DESK + Vector((0, 5.5, 0))                 # on the chair
OFFICER_START = Vector((-W / 2 - 4.5, DOOR_Y + 9.0, 0))   # waits behind the wall, out of sight of the door
FACE_X = math.radians(90)                               # rig rot Z to face +X
FACE_POS_Y = math.pi                                    # rig rot Z to face +Y (toward the desk)

worker_rig.parent = chair
worker_rig.matrix_parent_inverse = chair.matrix_world.inverted()
worker_rig.location = (WORKER_POS.x, WORKER_POS.y - 0.3, SEAT_H - 3.55 + 0.35)   # pelvis on the seat
worker_rig.rotation_euler = (0, 0, 0)                   # faces -Y, toward the door side
bpy.context.view_layer.update()

# gun in the robber's right hand
bpy.context.view_layer.update()
hand = robber_rig.pose.bones["hand.R"]
gun_root.parent = robber_rig
gun_root.parent_type = "BONE"
gun_root.parent_bone = "hand.R"
gun_root.matrix_parent_inverse = Matrix.Identity(4)
gun_root.location = (0, -0.2, 0)
gun_root.rotation_euler = (0, 0, 0)

# ------------------------------------------------------------ poses
P_ROB, P_WORK, P_OFF = Poser(robber_rig), Poser(worker_rig), Poser(officer_rig)
SEATED = sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
             arm=(-0.3, -0.55, -0.75), fore=(-0.1, -0.9, -0.2), **{"head": (0, -0.3, 0.95)})
HANDS_UP = sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
               arm=(-0.55, -0.1, 0.83), fore=(-0.25, -0.05, 0.97), **{"head": (0, 0.05, 1.0)})
AIM = {"upper_arm.R": (0.22, -0.9, 0.38), "forearm.R": (0.06, -0.99, 0.12),
       "upper_arm.L": (-0.45, -0.15, -0.88), "forearm.L": (-0.4, -0.3, -0.86),
       "head": (0, -0.25, 0.97), "spine.003": (0, -0.12, 0.99)}
ARMS_DOWN = sym(arm=(-0.42, -0.1, -0.9), fore=(-0.38, -0.15, -0.9))
HEAD_FRONT = (0, -0.25, 0.97)

# ------------------------------------------------------------ timeline
F_ENTER, F_ARRIVE, F_AIM = 61, 118, 150         # door opens; reaches the mark; gun up = the rewind point
F_SHOT, F_END1 = 180, 200                       # attempt 1
F_A2, F_SLIP, F_DOWN, F_COPS, F_ARREST, F_END2 = 201, 222, 240, 246, 300, 330
F_A3, F_STAND, F_YELL, F_END3 = 331, 350, 378, 430
SUBTITLES = [("Hand it over.", 152, 178), ("Freeze!", 292, 318), ("WILL YOU STOP THAT?!", F_YELL + 2, F_END3 - 6)]
REWINDS = [(F_AIM, F_END1), (F_AIM, F_END2)]     # footage reversed between attempts


def robber_at(frame, pos, rot_z, interp="BEZIER"):
    key(robber_rig, frame, loc=tuple(pos), rot=(0, 0, rot_z), interp=interp)


def visible(obj, frame, on):
    scene.frame_set(frame)
    obj.hide_render = not on
    obj.hide_viewport = not on
    obj.keyframe_insert("hide_render", frame=frame)
    obj.keyframe_insert("hide_viewport", frame=frame)


def flash_visible(frame, on):
    visible(flash, frame, on)


# the shouting face swaps in for the yell
for o in (shout, *brows):
    visible(o, 1, False)
    visible(o, F_YELL - 1, True)
visible(w_mouth, 1, True)
visible(w_mouth, F_YELL - 1, False)


# establishing: worker typing
P_WORK.pose(1, SEATED)
for f in range(1, F_AIM, 10):
    P_WORK.pose(f, sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
                       arm=(-0.3, -0.55, -0.75), fore=(-0.1, -0.9, -0.2 + 0.06 * ((f // 10) % 2)),
                       **{"head": (0, -0.3, 0.95)}))

# the door opens, Yellow walks in to the mark and turns to face the desk
key(hinge, 1, rot=(0, 0, 0), interp="CONSTANT")
key(hinge, F_ENTER, rot=(0, 0, 0))
key(hinge, F_ENTER + 14, rot=(0, 0, math.radians(-95)))
key(hinge, F_ARRIVE + 10, rot=(0, 0, math.radians(-95)))
key(hinge, F_ARRIVE + 30, rot=(0, 0, 0))
robber_at(1, ROBBER_START, FACE_X, "CONSTANT")
P_ROB.pose(1, {})
path_in = [(F_ENTER + 4, ROBBER_START, FACE_X), (F_ENTER + 30, Vector((-W / 2 + 4, DOOR_Y, 0)), FACE_X),
           (F_ARRIVE - 8, Vector((ROBBER_MARK.x - 1.5, ROBBER_MARK.y - 0.6, 0)), math.radians(120)),
           (F_ARRIVE, ROBBER_MARK, FACE_POS_Y)]
# walk: root moves along the waypoints, legs cycle
for (fa, pa, ra), (fb, pb, rb) in zip(path_in, path_in[1:]):
    for f in range(fa, fb + 1):
        u = (f - fa) / max(1, fb - fa)
        pos = pa.lerp(pb, u)
        key(robber_rig, f, loc=tuple(pos), interp="LINEAR")
    key(robber_rig, fa, rot=(0, 0, ra))
key(robber_rig, F_ARRIVE, rot=(0, 0, FACE_POS_Y))
for f in range(F_ENTER + 4, F_ARRIVE + 1):
    t = f - (F_ENTER + 4)
    ease = min(1.0, t / 10) * min(1.0, (F_ARRIVE - f) / 8)
    dirs = gait_dirs(t, 24, ease)
    dirs["head"] = HEAD_FRONT
    P_ROB.pose(f, dirs)
ground_clamp(robber_rig, robber, range(F_ENTER + 4, F_ARRIVE + 3))
key(robber_rig, F_ARRIVE + 3, loc=tuple(ROBBER_MARK))

# draws and points the gun; worker's hands go up
P_ROB.pose(F_ARRIVE + 6, ARMS_DOWN)
P_ROB.pose(F_AIM, AIM)
P_WORK.pose(F_AIM - 4, SEATED)
P_WORK.pose(F_AIM + 12, HANDS_UP)


def aim_hold(f0, f1):
    P_ROB.pose(f0, AIM)
    P_ROB.pose(f1, AIM)
    P_WORK.pose(f0, HANDS_UP)
    P_WORK.pose(f1, HANDS_UP)
    robber_at(f0, ROBBER_MARK, FACE_POS_Y)
    key(chair, f0, rot=(0, 0, 0), loc=tuple(chair.location))


# ---- attempt 1: the shot
aim_hold(F_AIM, F_SHOT - 2)
P_ROB.pose(F_SHOT, dict(AIM, **{"upper_arm.R": (0.22, -0.86, 0.46), "head": (0, -0.15, 0.99)}))   # recoil
P_ROB.pose(F_SHOT + 6, AIM)
flash_visible(1, False)
flash_visible(F_SHOT, True)
flash_visible(F_SHOT + 2, False)
P_WORK.pose(F_SHOT + 2, sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
                            arm=(-0.7, 0.2, 0.68), fore=(-0.5, 0.3, 0.8), **{"head": (0, 0.55, 0.83), "spine.003": (0, 0.4, 0.92)}))
key(chair, F_SHOT + 1, rot=(0, 0, 0))
key(chair, F_SHOT + 12, rot=(math.radians(-70), 0, 0))       # over it goes (pivot at its base)
key(chair, F_SHOT + 16, rot=(math.radians(-62), 0, 0))
key(chair, F_END1, rot=(math.radians(-66), 0, 0))
P_WORK.pose(F_END1, sym(thigh=(-0.08, -0.6, -0.8), shin=(0, 0.3, -0.95), arm=(-0.8, 0.3, 0.5), fore=(-0.6, 0.4, 0.7),
                        **{"head": (0, 0.5, 0.86)}))

# ---- attempt 2: the slip and the arrest
aim_hold(F_A2, F_SLIP - 6)
key(chair, F_A2, rot=(0, 0, 0), interp="CONSTANT")
key(chair, F_SLIP, rot=(0, 0, 0))
# a step forward, feet shoot out, lands on his back
key(robber_rig, F_SLIP, loc=tuple(ROBBER_MARK), rot=(0, 0, FACE_POS_Y))
key(robber_rig, F_SLIP + 8, loc=(0, ROBBER_MARK.y + 1.2, 0.2), rot=(math.radians(-25), 0, FACE_POS_Y))
key(robber_rig, F_DOWN, loc=(0, ROBBER_MARK.y + 2.6, 1.3), rot=(math.radians(-88), 0, FACE_POS_Y))
key(robber_rig, F_DOWN + 4, loc=(0, ROBBER_MARK.y + 2.6, 1.45), rot=(math.radians(-92), 0, FACE_POS_Y))
key(robber_rig, F_COPS + 10, loc=(0, ROBBER_MARK.y + 2.6, 1.3), rot=(math.radians(-88), 0, FACE_POS_Y))
P_ROB.pose(F_SLIP + 8, dict(AIM, **{"thigh.L": (-0.1, -0.7, -0.7), "thigh.R": (0.1, -0.9, -0.45),
                                      "upper_arm.R": (0.3, -0.5, 0.8), "upper_arm.L": (-0.7, 0.2, 0.7)}))
P_ROB.pose(F_DOWN, sym(thigh=(-0.1, -0.4, -0.9), shin=(0, -0.3, -0.95), arm=(-0.75, -0.2, 0.62), fore=(-0.55, -0.3, 0.78),
                       **{"head": (0, 0.3, 0.95)}))
P_ROB.pose(F_COPS + 10, sym(thigh=(-0.1, -0.35, -0.93), shin=(0, -0.3, -0.95), arm=(-0.8, -0.15, 0.58), fore=(-0.6, -0.25, 0.76),
                            **{"head": (0, 0.2, 0.98)}))
# the officer bursts in and stands over him; Yellow sits up with his hands up
key(hinge, F_COPS - 1, rot=(0, 0, 0), interp="CONSTANT")
key(hinge, F_COPS, rot=(0, 0, 0))
key(hinge, F_COPS + 8, rot=(0, 0, math.radians(-110)))
key(officer_rig, 1, loc=tuple(OFFICER_START), rot=(0, 0, math.radians(180)), interp="CONSTANT")
P_OFF.pose(1, {})
ARREST_SPOT = Vector((-3.2, ROBBER_MARK.y + 3.5, 0))
cop_path = [(F_COPS + 2, OFFICER_START, math.radians(180)),                         # runs along the wall to the door
            (F_COPS + 14, Vector((-W / 2 - 3.5, DOOR_Y, 0)), math.radians(120)),
            (F_COPS + 28, Vector((-W / 2 + 6, DOOR_Y, 0)), FACE_X),
            (F_COPS + 44, ARREST_SPOT, math.radians(70))]
for (fa, pa, ra), (fb, pb, rb) in zip(cop_path, cop_path[1:]):
    for f in range(fa, fb + 1):
        u = (f - fa) / max(1, fb - fa)
        key(officer_rig, f, loc=tuple(pa.lerp(pb, u)), interp="LINEAR")
    key(officer_rig, fa, rot=(0, 0, ra))
key(officer_rig, F_COPS + 44, rot=(0, 0, math.radians(70)))
for f in range(F_COPS + 2, F_COPS + 45):
    t = f - (F_COPS + 2)
    ease = min(1.0, t / 8) * min(1.0, (F_COPS + 44 - f) / 8)
    dirs = gait_dirs(t, 15, ease, run=True)
    dirs["head"] = HEAD_FRONT
    P_OFF.pose(f, dirs)
ground_clamp(officer_rig, officer, range(F_COPS + 2, F_COPS + 47))
key(officer_rig, F_COPS + 47, loc=tuple(ARREST_SPOT))
P_OFF.pose(F_COPS + 52, {"spine.003": (0, -0.35, 0.94), "head": (0, -0.55, 0.83),
                         "upper_arm.R": (0.25, -0.8, -0.55), "forearm.R": (0.1, -0.9, -0.4),
                         "upper_arm.L": (-0.4, -0.5, -0.75), "forearm.L": (-0.3, -0.7, -0.6)})     # grabs him
P_OFF.pose(F_END2, {"spine.003": (0, -0.35, 0.94), "head": (0, -0.55, 0.83),
                    "upper_arm.R": (0.25, -0.8, -0.55), "forearm.R": (0.1, -0.9, -0.4),
                    "upper_arm.L": (-0.4, -0.5, -0.75), "forearm.L": (-0.3, -0.7, -0.6)})
key(robber_rig, F_ARREST, loc=(0, ROBBER_MARK.y + 2.6, 1.3), rot=(math.radians(-88), 0, FACE_POS_Y))
key(robber_rig, F_ARREST + 12, loc=(0, ROBBER_MARK.y + 1.6, 0.3), rot=(math.radians(-40), 0, FACE_POS_Y))   # sits up
key(robber_rig, F_END2, loc=(0, ROBBER_MARK.y + 1.6, 0.3), rot=(math.radians(-38), 0, FACE_POS_Y))
P_ROB.pose(F_ARREST + 12, sym(thigh=(-0.1, -0.85, -0.5), shin=(0, -0.2, -0.98), arm=(-0.55, -0.1, 0.83), fore=(-0.3, -0.05, 0.95),
                              **{"head": (0, -0.3, 0.95)}))
P_ROB.pose(F_END2, sym(thigh=(-0.1, -0.85, -0.5), shin=(0, -0.2, -0.98), arm=(-0.55, -0.1, 0.83), fore=(-0.3, -0.05, 0.95),
                       **{"head": (0, -0.3, 0.95)}))
P_WORK.pose(F_A2, HANDS_UP)
P_WORK.pose(F_END2, HANDS_UP)
# park the officer again after the attempt (he isn't in attempt 3)
key(officer_rig, F_END2 + 1, loc=tuple(OFFICER_START), rot=(0, 0, math.radians(180)), interp="CONSTANT")
key(hinge, F_END2 + 1, rot=(0, 0, 0), interp="CONSTANT")

# ---- attempt 3: the worker has had enough
aim_hold(F_A3, F_STAND)
key(chair, F_A3, rot=(0, 0, 0), interp="CONSTANT")
key(robber_rig, F_A3, loc=tuple(ROBBER_MARK), rot=(0, 0, FACE_POS_Y), interp="CONSTANT")
key(robber_rig, F_STAND, loc=tuple(ROBBER_MARK), rot=(0, 0, FACE_POS_Y))
LEAN = sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
           arm=(-0.35, -0.85, -0.4), fore=(-0.1, -0.85, -0.5), **{"spine.003": (0, -0.6, 0.8), "spine.002": (0, -0.3, 0.95),
                                                                 "head": (0, -0.45, 0.89)})
P_WORK.pose(F_STAND + 10, sym(thigh=(-0.08, -0.95, -0.3), shin=(0, -0.05, -1.0),
                              arm=(-0.45, -0.6, -0.65), fore=(-0.2, -0.85, -0.5), **{"head": (0, -0.3, 0.95)}))    # hands come down
P_WORK.pose(F_YELL, LEAN)
P_WORK.pose(F_END3, LEAN)
key(chair, F_STAND, rot=(0, 0, 0))
key(chair, F_YELL, loc=(chair.location.x, chair.location.y - 1.2, 0), rot=(0, 0, 0))    # rolls forward to the desk
# Yellow recoils, then lowers the gun
P_ROB.pose(F_YELL - 2, AIM)
P_ROB.pose(F_YELL + 8, dict(AIM, **{"spine.003": (0, 0.28, 0.96), "head": (0, 0.3, 0.95),
                                      "upper_arm.R": (0.3, -0.6, -0.1), "forearm.R": (0.1, -0.7, 0.7)}))
P_ROB.pose(F_END3 - 10, dict(ARMS_DOWN, **{"spine.003": (0, 0.1, 0.99), "head": (0, -0.15, 0.99)}))
P_ROB.pose(F_END3, dict(ARMS_DOWN, **{"spine.003": (0, 0.1, 0.99), "head": (0, -0.2, 0.98)}))
key(robber_rig, F_YELL + 8, loc=(0, ROBBER_MARK.y - 0.9, 0), rot=(0, 0, FACE_POS_Y))
key(robber_rig, F_END3, loc=(0, ROBBER_MARK.y - 1.2, 0), rot=(0, 0, FACE_POS_Y))

# ------------------------------------------------------------ camera
cam_data = bpy.data.cameras.new("Office_Camera")
cam_data.lens = 32
cam_data.clip_end = 500
cam = bpy.data.objects.new("Office_Camera", cam_data)
col.objects.link(cam)
scene.camera = cam
target = empty("CamTarget", (0, 4, 5))
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
WORKER_HEAD = (WORKER_POS.x, WORKER_POS.y, 7.6)
ROBBER_HEAD = (ROBBER_MARK.x, ROBBER_MARK.y, 8.0)
SHOTS = [
    # (start, end, cam start, cam end, target start, target end)
    (1, F_ENTER - 1, (-17, -13, 9), (-15.5, -12.5, 8.6), (2, 5, 4.5), (2, 5, 4.5)),                 # establishing, typing
    (F_ENTER, F_ARRIVE + 2, (6, 12.5, 8.5), (5, 11.5, 8.2), (-19, -8, 6), (0, -3, 6.5)),             # from behind the desk: he comes in
    (F_ARRIVE + 3, F_SHOT + 5, (-5.5, -12.5, 10.5), (-5.0, -12.0, 10.3), WORKER_HEAD, WORKER_HEAD),  # over his shoulder: the gun comes up
    (F_SHOT + 6, F_END1, (-19, 2, 7), (-18, 2.5, 7), (0, 6, 4), (0, 7, 4)),                          # side: the chair goes over
    (F_A2, F_COPS - 1, (15, -12, 8), (14, -11, 7.6), (-1, 0, 4.5), (-1, 0, 4.2)),                      # front-right: the slip
    (F_COPS, F_END2, (14, -16, 9), (13, -15, 8.6), (-14, -8, 5), (-2, -3, 3.5)),                      # front-right: the police come in
    (F_A3, F_YELL - 1, (-5.5, -12.5, 10.5), (-5.0, -12.0, 10.3), WORKER_HEAD, WORKER_HEAD),          # over his shoulder again
    (F_YELL, F_YELL + 26, (-2.0, -0.5, 7.6), (-1.6, -0.2, 7.5), (0, 8, 7.0), (0, 7.5, 6.8)),         # close: the yell
    (F_YELL + 27, F_END3, (-7.0, 8.5, 8.5), (-6.6, 8.0, 8.3), ROBBER_HEAD, ROBBER_HEAD),             # Yellow shrinks back
]
for start, end, ca, cb, ta, tb in SHOTS:
    key(cam, start, loc=ca, interp="LINEAR")
    key(cam, end, loc=cb, interp="LINEAR")
    key(target, start, loc=ta, interp="LINEAR")
    key(target, end, loc=tb, interp="LINEAR")

# ------------------------------------------------------------ output and checks
scene.frame_start, scene.frame_end = 1, F_END3
scene.frame_set(1)
bad = {n: floor_violations(b, range(1, F_END3 + 1)) for n, b in (("robber", robber), ("officer", officer))}
spikes = motion_spikes(robber_rig, range(2, F_END3), 0.6, bone="head")
spikes = {f: v for f, v in spikes.items() if abs(f - F_A2) > 1 and abs(f - F_A3) > 1}   # attempt cuts are expected
print("office keyed 1 ->", F_END3, "| below floor:", {k: v for k, v in bad.items() if v} or "none", "| robber head jerks:", spikes or "none")
print("rewinds:", REWINDS, "| subtitles:", SUBTITLES)
bpy.context.window.scene = main
