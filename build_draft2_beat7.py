"""Draft 2, beat 7: Lime. Purple flies Yellow on at speed in a wide bank over
the plate. Up ahead a green figure is falling out of the sky: Lime. The
jetski flies under him perfectly and he lands on the gunwale beside the
passenger seat, grabs the rail and hangs there off the side, legs dangling.
Yellow, twisting round on the seat: "What, how did you get on here?" Lime
hauls himself up over the side and sits on it, legs over the edge, one hand
on the rail. "What the hell..." pause "...is going on!" Yellow: "I don't
know any more than you." Lime: "What about you, Purple, do you know?"
Yellow: "He's not really much of a talker." Lime: "Ughhh." A second later:
"Anyways, what are your guys' names?" Yellow: "Uhhhhhhhh" (a second) "I
guess Yellow. And just call this other guy Purple." Two seconds later:
"How about you, what is your name?" Lime: "Umm" (he looks at his arm)
"Lime." Purple never speaks.

Frames 1657-2680 at 24 fps. Run inside Blender with slimsico.blend open after
build_draft2_beat6.py and build_lime.py. Re-running replaces everything after
frame 1656. Render with render_draft2.py.
"""
import bpy
import math
import os
import sys
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, fcurves, key  # noqa: E402

scene = bpy.data.scenes["Scene"]
if bpy.context.window:
    bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
target = bpy.data.objects["CamTarget"]
mouth = bpy.data.objects["Mouth"]
mouth_open = bpy.data.objects["MouthOpen"]
hc = bpy.data.objects["Hovercraft"]
prig = bpy.data.objects["PurpleRig"]
lrig = bpy.data.objects["LimeRig"]
lbody = bpy.data.objects["Lime"]
lmouth = bpy.data.objects["Lime_Mouth"]
lmouth_open = bpy.data.objects["Lime_MouthOpen"]
lime_col = bpy.data.collections["Lime"]

FPS = 24
F0 = 1656                                  # where beat 6 ends
F_FALL = 1700                              # Lime is first seen falling, far ahead and high
F_CATCH = 1770                             # the jetski passes under him: he lands on the rail
F_HANG_END, F_SIT = 1850, 1900             # hangs, then hauls himself up and sits on the side
F_WHAT, F_WHAT_END = 1800, 1850            # Yellow: What, how did you get on here?
F_HELL, F_HELL_END = 1905, 1935            # Lime: What the hell...
F_GOING, F_GOING_END = 1947, 1985          # ...is going on!
F_KNOW, F_KNOW_END = 2000, 2050            # Yellow: I don't know any more than you.
F_ABOUT, F_ABOUT_END = 2065, 2120          # Lime: What about you, Purple, do you know?
F_TALKER, F_TALKER_END = 2135, 2185        # Yellow: He's not really much of a talker.
F_UGH, F_UGH_END = 2200, 2225              # Lime: Ughhh
F_NAMES, F_NAMES_END = 2250, 2310          # Lime: Anyways, what are your guys' names?
F_UHH, F_UHH_END = 2325, 2350              # Yellow: Uhhhhhhhh
F_GUESS, F_GUESS_END = 2375, 2455          # Yellow: I guess Yellow. And just call this other guy Purple.
F_HOW, F_HOW_END = 2505, 2560              # Yellow: How about you, what is your name?
F_UMM, F_UMM_END = 2575, 2595              # Lime: Umm
F_LOOK_ARM = 2590                          # he looks at his arm
F_LIME, F_LIME_END = 2625, 2650            # Lime: Lime.
F_END = 2680
SUBTITLES = [("What, how did you get on here?", F_WHAT, F_WHAT_END), ("What the hell...", F_HELL, F_HELL_END), ("...is going on!", F_GOING, F_GOING_END),
             ("I don't know any more than you.", F_KNOW, F_KNOW_END), ("What about you, Purple, do you know?", F_ABOUT, F_ABOUT_END),
             ("He's not really much of a talker.", F_TALKER, F_TALKER_END), ("Ughhh.", F_UGH, F_UGH_END),
             ("Anyways, what are your guys' names?", F_NAMES, F_NAMES_END), ("Uhhhhhhhh...", F_UHH, F_UHH_END),
             ("I guess Yellow. And just call this other guy Purple.", F_GUESS, F_GUESS_END), ("How about you, what is your name?", F_HOW, F_HOW_END),
             ("Umm...", F_UMM, F_UMM_END), ("Lime.", F_LIME, F_LIME_END)]
SOUND_CUES = [("hover", F0 + 1), ("crate_whistle", F_FALL), ("catch", F_CATCH), ("thump", F_SIT - 6)]


def clear_after(obj, frame):
    for fc in fcurves(obj):
        for kp in reversed(list(fc.keyframe_points)):
            if kp.co.x > frame + 0.5:
                fc.keyframe_points.remove(kp)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def at(frame):
    if scene.frame_current != frame:
        scene.frame_set(frame)


for o in (rig, cam, cam.data, target, mouth, mouth_open, hc, prig):
    clear_after(o, F0)
for o in lime_col.objects:
    o.animation_data_clear()
lrig.rotation_mode = "XYZ"
poser = Poser(rig, order=Poser.ORDER + ["hand.L", "hand.R"])
pposer = Poser(prig, order=Poser.ORDER + ["hand.R", "hand.L"])
lposer = Poser(lrig, order=Poser.ORDER + ["hand.L", "hand.R"])
HEAD_FRONT = (0, -0.25, 0.97)


def look_at(some_rig, point, frame, front=HEAD_FRONT, blend=1.0, max_up=0.85, neck=0.3):
    at(frame)
    head = some_rig.matrix_world @ some_rig.pose.bones["head"].head
    d = some_rig.matrix_world.to_3x3().inverted() @ (Vector(point) - head).normalized()
    d.z = max(-max_up, min(d.z, max_up))
    d.normalize()
    axis = Vector((0, -1, 0)).rotation_difference(d) @ Vector((0, 0, 1))
    return {"head": tuple(Vector(front).lerp(axis, blend)), "neck": tuple(Vector((0, 0, 1)).lerp(axis, neck * blend))}


def show(obj, frame, on):
    scene.frame_set(frame)
    obj.hide_render = not on
    obj.hide_viewport = not on
    obj.keyframe_insert("hide_render", frame=frame)
    obj.keyframe_insert("hide_viewport", frame=frame)


CLOSED, WIDE, MID, ROUND = (0.9, 0.4, 0.05), (1.0, 0.4, 0.7), (0.85, 0.4, 0.38), (0.8, 0.4, 0.8)


def say(smile, open_mouth, first, last, shapes, gap=6):
    for o, on in ((smile, True), (open_mouth, False)):
        show(o, first, not on)
        show(o, last, on)
    key(open_mouth, first, scale=CLOSED)
    span = last - first - 6
    gap = max(4, min(gap, span // max(1, len(shapes))))
    for i, shape in enumerate(shapes):
        f = first + 3 + i * gap
        key(open_mouth, f + 2, scale=shape)
        key(open_mouth, f + gap - 1, scale=CLOSED)
    key(open_mouth, last, scale=CLOSED)


# ------------------------------------------------------------ the jetski: a wide bank over the plate
# picks up where beat 6 leaves it (flying -X) and turns right in a wide circle
# that stays over the plate, banked into the turn, at cruising speed
scene.frame_set(F0)
P0 = hc.location.copy()
H0 = hc.rotation_euler.z                                    # heading (0 = flying -Y, +90 = +X)
SPEED, R_TURN = 0.42, 80.0
ALT = P0.z
centre = P0 - Vector((math.cos(H0), math.sin(H0), 0.0)) * R_TURN   # n(h) = (cos h, sin h) points from the centre to the craft
path = {}
for f in range(F0, F_END + 1):
    t = f - F0
    h = H0 - (SPEED / R_TURN) * t
    n = Vector((math.cos(h), math.sin(h), 0.0))
    p = centre + n * R_TURN
    p.z = ALT + 0.6 * math.sin(2 * math.pi * t / 90.0)
    path[f] = [p, h]
hc.rotation_mode = "XYZ"
for f in range(F0 + 1, F_END + 1):
    p, h = path[f]
    t = f - F0
    bank = math.radians(13) * smooth(t / 30.0) + math.radians(1.2) * math.sin(2 * math.pi * t / 70.0)
    pitch = math.radians(1.0) * math.cos(2 * math.pi * t / 90.0)
    key(hc, f, loc=tuple(p), rot=(pitch, bank, h), interp="LINEAR")


def M(frame):
    at(frame)
    return hc.matrix_world.copy()


# ------------------------------------------------------------ Purple rides, eyes front
RIDE = {"spine.001": (0, -0.30, 0.95), "spine.002": (0, -0.48, 0.88), "spine.003": (0, -0.52, 0.85), "neck": (0, -0.35, 0.94), "head": (0, -0.3, 0.95),
        "thigh.L": (-0.22, -0.92, -0.32), "shin.L": (-0.12, -0.42, -0.9), "thigh.R": (0.22, -0.92, -0.32), "shin.R": (0.12, -0.42, -0.9),
        "upper_arm.L": (-0.5, -0.72, -0.48), "forearm.L": (-0.45, -0.88, 0.12), "upper_arm.R": (0.5, -0.72, -0.48), "forearm.R": (0.45, -0.88, 0.12)}
pposer.pose(F0 + 1, RIDE)
pposer.pose(F_END, RIDE)
# one glance at the new arrival as Lime lands, then front again
pposer.pose(F_CATCH + 6, RIDE)
pposer.pose(F_CATCH + 18, {**RIDE, "head": (0.55, 0.25, 0.8), "neck": (0.25, 0.1, 0.96)})
pposer.pose(F_CATCH + 40, {**RIDE, "head": (0.55, 0.25, 0.8), "neck": (0.25, 0.1, 0.96)})
pposer.pose(F_CATCH + 54, RIDE)

# ------------------------------------------------------------ Yellow on the passenger seat
SEAT_LOCAL = Vector((0.0, 5.9, 0.95))
SEATED = {"spine.001": (0, 0.1, 0.99), "spine.002": (0, 0.05, 1.0), "spine.003": (0, -0.05, 1.0), "neck": (0, -0.15, 0.99), "head": (0, -0.22, 0.97),
          "thigh.L": (-0.5, -0.78, -0.37), "shin.L": (-0.35, -0.2, -0.92), "thigh.R": (0.5, -0.78, -0.37), "shin.R": (0.35, -0.2, -0.92),
          "upper_arm.L": (-0.42, -0.5, -0.76), "forearm.L": (-0.28, -0.72, -0.63), "hand.L": (-0.2, -0.8, -0.56),
          "upper_arm.R": (0.42, -0.5, -0.76), "forearm.R": (0.28, -0.72, -0.63), "hand.R": (0.2, -0.8, -0.56)}
TWIST_R = {**SEATED, "spine.002": (0.25, 0.0, 0.97), "spine.003": (0.4, -0.1, 0.91),                    # twists right to look at Lime
           "upper_arm.R": (0.75, -0.1, -0.65), "forearm.R": (0.8, -0.3, -0.5), "hand.R": (0.8, -0.4, -0.45)}
SHRUG_Y = {**TWIST_R, "upper_arm.L": (-0.62, -0.42, -0.55), "forearm.L": (-0.72, -0.28, 0.62), "hand.L": (-0.7, -0.2, 0.68),
           "upper_arm.R": (0.62, -0.42, -0.55), "forearm.R": (0.72, -0.28, 0.62), "hand.R": (0.7, -0.2, 0.68)}


def lime_head(frame):
    at(frame)
    return lrig.matrix_world @ lrig.pose.bones["head"].head


def yellow_head(frame):
    at(frame)
    return rig.matrix_world @ rig.pose.bones["head"].head


def purple_head(frame):
    at(frame)
    return prig.matrix_world @ prig.pose.bones["head"].head


for f in range(F0 + 1, F_END + 1):
    Mf = M(f)
    key(rig, f, loc=tuple(Mf @ SEAT_LOCAL), interp="LINEAR")
    scene.frame_set(f)
    rig.rotation_mode = "QUATERNION"
    rig.rotation_quaternion = Euler((hc.rotation_euler.x * 0.6, hc.rotation_euler.y * 0.6, math.radians(360) + path[f][1])).to_quaternion()
    rig.keyframe_insert("rotation_quaternion", frame=f)

# ------------------------------------------------------------ Lime: the fall, the landing, the hang, the climb, the sit
RAIL_LOCAL = Vector((3.05, 2.6, 1.95))                      # the gunwale beside the passenger seat, right side
HANG_LOCAL = Vector((5.0, 2.6, -2.6))                       # his root while hanging off the side, clear of the hull skin
SIT_LOCAL = Vector((3.3, 3.3, 2.0))                         # sitting on the gunwale, legs over the edge
for o in lime_col.objects:
    show(o, 1, False)
    show(o, F_FALL, True)
FALL_G = 30.0
catch_world = M(F_CATCH) @ RAIL_LOCAL
FALL = {"upper_arm.L": (-0.85, -0.3, 0.4), "forearm.L": (-0.8, -0.4, 0.45), "upper_arm.R": (0.85, -0.3, 0.4), "forearm.R": (0.8, -0.4, 0.45),
        "thigh.L": (-0.2, -0.3, -0.93), "shin.L": (-0.1, 0.3, -0.95), "thigh.R": (0.2, -0.3, -0.93), "shin.R": (0.1, 0.3, -0.95),
        "spine.003": (0, -0.15, 0.99), "head": (0, -0.4, 0.92)}
HANG = {"upper_arm.L": (-0.35, -0.35, 0.87), "forearm.L": (-0.2, -0.4, 0.9), "hand.L": (-0.1, -0.5, 0.86),
        "upper_arm.R": (0.35, -0.35, 0.87), "forearm.R": (0.2, -0.4, 0.9), "hand.R": (0.1, -0.5, 0.86),
        "thigh.L": (-0.12, -0.1, -0.99), "shin.L": (-0.05, 0.2, -0.98), "thigh.R": (0.12, -0.1, -0.99), "shin.R": (0.05, 0.2, -0.98),
        "spine.002": (0, -0.08, 1.0), "spine.003": (0, -0.12, 0.99), "head": (0, -0.5, 0.87)}
PULL = {**HANG, "upper_arm.L": (-0.5, -0.6, 0.62), "forearm.L": (-0.35, -0.75, 0.55), "upper_arm.R": (0.5, -0.6, 0.62), "forearm.R": (0.35, -0.75, 0.55),
        "thigh.L": (-0.15, -0.75, -0.65), "shin.L": (-0.1, 0.35, -0.93), "thigh.R": (0.2, -0.45, -0.87), "shin.R": (0.1, 0.4, -0.9),
        "spine.002": (0, -0.3, 0.95), "spine.003": (0, -0.4, 0.92)}
OVER = {**PULL, "thigh.L": (-0.5, -0.6, -0.62), "shin.L": (-0.3, -0.1, -0.95), "thigh.R": (0.5, -0.6, -0.62), "shin.R": (0.3, -0.1, -0.95),
        "upper_arm.L": (-0.6, -0.5, -0.6), "forearm.L": (-0.5, -0.6, -0.6), "upper_arm.R": (0.6, -0.5, -0.6), "forearm.R": (0.5, -0.6, -0.6)}
SIDE_SIT = {"spine.001": (0, 0.05, 1.0), "spine.002": (0, -0.05, 1.0), "spine.003": (-0.05, -0.1, 0.99), "neck": (0, -0.15, 0.99), "head": (0, -0.25, 0.97),
            "thigh.L": (-0.3, -0.85, -0.45), "shin.L": (-0.2, -0.3, -0.93), "thigh.R": (0.3, -0.85, -0.45), "shin.R": (0.2, -0.3, -0.93),
            "upper_arm.L": (-0.7, 0.2, -0.68), "forearm.L": (-0.6, 0.3, -0.74), "hand.L": (-0.5, 0.4, -0.77),                 # holds the rail behind
            "upper_arm.R": (0.55, -0.35, -0.76), "forearm.R": (0.45, -0.5, -0.74), "hand.R": (0.4, -0.55, -0.73)}
ARM_LOOK = {**SIDE_SIT, "upper_arm.L": (-0.55, -0.6, -0.58), "forearm.L": (0.1, -0.55, 0.83), "hand.L": (0.3, -0.4, 0.87)}   # the forearm comes up, name toward his face


def key_lime(frame, local, yaw, pitch=0.0, roll=0.0):
    """Lime's root keyed in the jetski's frame."""
    Mf = M(frame)
    world = Mf @ Matrix.Translation(local) @ Euler((pitch, roll, yaw)).to_matrix().to_4x4()
    loc, rot, _ = world.decompose()
    lrig.location = loc
    lrig.rotation_euler = rot.to_euler("XYZ")
    lrig.keyframe_insert("location", frame=frame)
    lrig.keyframe_insert("rotation_euler", frame=frame)


def linear(obj):
    for fc in fcurves(obj):
        if fc.data_path in ("location", "rotation_euler"):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


# the fall: straight down onto the spot where the rail will be, slowly turning, limbs out
for f in range(F_FALL, F_CATCH + 1):
    tt = (F_CATCH - f) / FPS
    dz = 0.5 * FALL_G * tt * tt
    p = catch_world + Vector((0, 0, dz + 4.3))              # root well above the rail: he lands hands-first
    u = smooth((f - F_FALL) / 30.0)
    spin = 0.9 * (F_CATCH - f) / (F_CATCH - F_FALL)
    lrig.location = p
    lrig.rotation_euler = (math.radians(-25) * (1 - u * 0.4), spin * 0.4, path[f][1] - math.pi / 2 + spin)
    lrig.keyframe_insert("location", frame=f)
    lrig.keyframe_insert("rotation_euler", frame=f)
    pose = dict(FALL)
    flail = 0.35 * math.sin(2 * math.pi * f / 14.0)
    pose["upper_arm.L"] = (-0.85, -0.3 + flail, 0.4)
    pose["upper_arm.R"] = (0.85, -0.3 - flail, 0.4)
    lposer.pose(f, pose)
# the catch: hands hit the rail, the body swings down and hangs off the side (yaw -90: facing the hull)
YAW_HANG = -math.pi / 2
for f in range(F_CATCH + 1, F_HANG_END + 1):
    u = smooth((f - F_CATCH) / 10.0)
    swing = math.radians(35) * math.sin(math.pi * min(1.0, (f - F_CATCH) / 26.0)) * (1 - smooth((f - F_CATCH - 20) / 30.0))
    local = Vector((4.8, 2.6, 1.6)).lerp(HANG_LOCAL, u)
    key_lime(f, local, YAW_HANG, pitch=math.radians(-40) * (1 - u) + swing)
    pose = dict(HANG)
    kick = 0.3 * math.sin(2 * math.pi * (f - F_CATCH) / 18.0) * (1 - smooth((f - F_CATCH - 30) / 40.0))
    pose["thigh.L"] = (-0.12, -0.1 + kick, -0.99)
    pose["thigh.R"] = (0.12, -0.1 - kick, -0.99)
    pose.update(look_at(lrig, yellow_head(f), f, max_up=0.95, blend=smooth((f - F_CATCH - 14) / 12.0)))
    lposer.pose(f, pose)
# the climb: pulls up, gets a knee on the gunwale, swings over and sits on the side facing out (yaw +90), looking back at Yellow
for f in range(F_HANG_END + 1, F_SIT + 1):
    u = (f - F_HANG_END) / (F_SIT - F_HANG_END)
    if u < 0.4:
        w = smooth(u / 0.4)
        local = HANG_LOCAL.lerp(Vector((4.6, 2.6, 0.4)), w)
        pose = {k: tuple(Vector(HANG[k]).lerp(Vector(PULL.get(k, HANG[k])), w)) for k in HANG}
        yaw, pitch = YAW_HANG, math.radians(-15) * w
    elif u < 0.75:
        w = smooth((u - 0.4) / 0.35)
        local = Vector((4.6, 2.6, 0.4)).lerp(Vector((3.7, 3.1, 2.5)), w)
        pose = {k: tuple(Vector(PULL[k]).lerp(Vector(OVER.get(k, PULL[k])), w)) for k in PULL}
        yaw, pitch = YAW_HANG + math.pi * w, math.radians(-15) * (1 - w) + math.radians(-30) * math.sin(math.pi * w)
    else:
        w = smooth((u - 0.75) / 0.25)
        local = Vector((3.7, 3.1, 2.5)).lerp(SIT_LOCAL, w)
        pose = {k: tuple(Vector(OVER.get(k, SIDE_SIT[k])).lerp(Vector(SIDE_SIT[k]), w)) for k in SIDE_SIT}
        yaw, pitch = YAW_HANG + math.pi, 0.0
    pose.update(look_at(lrig, yellow_head(f), f, max_up=0.95, blend=0.6))
    key_lime(f, local, yaw, pitch=pitch)
    lposer.pose(f, pose)
# seated on the side for the talk: the body breathes, the head follows whoever he talks to
for f in range(F_SIT + 1, F_END + 1):
    pose = dict(SIDE_SIT)
    arm = smooth((f - F_LOOK_ARM) / 10.0) * (1 - smooth((f - (F_LIME_END + 10)) / 14.0))
    for k in ARM_LOOK:
        pose[k] = tuple(Vector(SIDE_SIT[k]).lerp(Vector(ARM_LOOK[k]), arm))
    br = 0.025 * math.sin(2 * math.pi * f / 40.0)
    pose["spine.002"] = (0, -0.05 + br, 1.0)
    if F_ABOUT - 6 <= f <= F_ABOUT_END + 6:
        aim = purple_head(f)                                # "what about you, Purple"
    elif arm > 0.5:
        at(f)
        aim = lrig.matrix_world @ lrig.pose.bones["forearm.L"].center
    else:
        aim = yellow_head(f)
    pose.update(look_at(lrig, aim, f, max_up=0.95 if arm < 0.5 else 0.6, blend=1.0))
    key_lime(f, SIT_LOCAL, YAW_HANG + math.pi, pitch=0.0)
    lposer.pose(f, pose)
linear(lrig)

# Lime's lines
say(lmouth, lmouth_open, F_HELL, F_HELL_END, (WIDE, MID, WIDE), gap=8)                                # What the hell
say(lmouth, lmouth_open, F_GOING, F_GOING_END, (MID, WIDE, ROUND), gap=9)                             # is go-ing on
say(lmouth, lmouth_open, F_ABOUT, F_ABOUT_END, (WIDE, MID, ROUND, MID, ROUND, MID, ROUND), gap=7)     # What a-bout you Pur-ple do you know
say(lmouth, lmouth_open, F_UGH, F_UGH_END, (ROUND, ROUND), gap=8)                                     # Ughhh
say(lmouth, lmouth_open, F_NAMES, F_NAMES_END, (MID, WIDE, MID, WIDE, MID, ROUND, WIDE), gap=7)       # An-y-ways what are your guys names
say(lmouth, lmouth_open, F_UMM, F_UMM_END, (ROUND, ROUND), gap=8)                                     # Umm
say(lmouth, lmouth_open, F_LIME, F_LIME_END, (WIDE, MID), gap=9)                                      # Lime

# ------------------------------------------------------------ Yellow: rides, twists round to Lime, talks
for f in range(F0 + 1, F_END + 1):
    twist = smooth((f - (F_CATCH + 4)) / 12.0)              # hears the thump, twists round to the right
    pose = {k: tuple(Vector(SEATED[k]).lerp(Vector(TWIST_R[k]), twist)) for k in SEATED}
    if F_KNOW - 8 <= f <= F_KNOW_END + 6 or F_UHH - 6 <= f <= F_GUESS_END + 8:
        shrug = smooth((f - (F_KNOW - 8)) / 10.0) * (1 - smooth((f - F_KNOW_END) / 8.0)) if f <= F_KNOW_END + 6 else \
            smooth((f - (F_UHH - 6)) / 10.0) * (1 - smooth((f - F_GUESS_END) / 10.0))
        for k in ("upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R"):
            pose[k] = tuple(Vector(pose[k]).lerp(Vector(SHRUG_Y[k]), shrug))
    br = 0.03 * math.sin(2 * math.pi * f / 40.0)
    pose["spine.002"] = (pose["spine.002"][0], pose["spine.002"][1] + br, pose["spine.002"][2])
    if f < F_CATCH + 4:
        aim = None
    elif F_TALKER - 6 <= f <= F_TALKER_END:
        aim = purple_head(f) if (f - F_TALKER) % 40 < 18 else lime_head(f)   # glances at Purple's back while talking about him
    elif F_GUESS + 40 <= f <= F_GUESS_END:
        aim = purple_head(f)                                # "this other guy"
    else:
        aim = lime_head(f)
    if aim is not None:
        pose.update(look_at(rig, aim, f, max_up=0.9, blend=twist))
    poser.pose(f, pose)
say(mouth, mouth_open, F_WHAT, F_WHAT_END, (WIDE, MID, WIDE, MID, ROUND, MID, WIDE), gap=6)           # What how did you get on here
say(mouth, mouth_open, F_KNOW, F_KNOW_END, (MID, ROUND, WIDE, MID, ROUND, MID, WIDE), gap=6)          # I don't know an-y more than you
say(mouth, mouth_open, F_TALKER, F_TALKER_END, (MID, WIDE, MID, ROUND, MID, WIDE, MID), gap=6)        # He's not real-ly much of a tal-ker
say(mouth, mouth_open, F_UHH, F_UHH_END, (ROUND, ROUND, ROUND), gap=7)                                # Uhhhhhhhh
say(mouth, mouth_open, F_GUESS, F_GUESS_END, (MID, WIDE, MID, ROUND, MID, WIDE, MID, ROUND, WIDE, MID, ROUND), gap=6)   # I guess Yel-low and just call this oth-er guy Pur-ple
say(mouth, mouth_open, F_HOW, F_HOW_END, (WIDE, MID, ROUND, WIDE, MID, WIDE, MID), gap=6)             # How a-bout you what is your name

# ------------------------------------------------------------ camera: shots in the jetski's frame
def cam_key(f, pos, tgt, lens):
    key(cam, f, loc=tuple(pos), interp="LINEAR")
    key(target, f, loc=tuple(tgt), interp="LINEAR")
    scene.frame_set(f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)


def jet(f, local):
    return M(f) @ Vector(local)


SHOTS = [
    (F0 + 1, F_FALL - 1, (-16.0, -14.0, 5.0), (0.5, 2.5, 4.5), 30),                       # flying on: wide from ahead-left, the bank
    (F_FALL, F_CATCH - 26, (0.0, 12.0, 4.5), None, 24),                                   # from behind, looking up ahead: a speck falling
    (F_CATCH - 25, F_CATCH + 10, (15.0, -5.0, 6.5), (3.2, 2.6, 6.5), 28),                 # from the right, ahead: he comes down onto the rail
    (F_CATCH + 11, F_HANG_END, (15.0, 7.0, 1.2), (4.2, 2.8, 0.3), 26),                   # low off the right side: Lime hanging, Yellow twisting round above
    (F_HANG_END + 1, F_SIT + 4, (8.0, 15.0, 8.0), (2.6, 3.2, 2.5), 30),                   # over the stern: the climb onto the side
    (F_SIT + 5, F_KNOW - 1, (13.0, -3.0, 5.5), (1.8, 4.2, 4.5), 30),                      # two-shot from the front-right: Lime on the side, Yellow behind him
    (F_KNOW, F_ABOUT - 1, (9.0, 13.0, 6.5), (0.5, 5.0, 5.0), 35),                         # Yellow's face, turned to Lime, from the right-rear
    (F_ABOUT, F_TALKER - 1, (10.0, 11.0, 6.5), (0.5, 1.8, 5.0), 30),                      # from behind them: Purple's back ahead as Lime asks him
    (F_TALKER, F_NAMES - 1, (13.0, -3.0, 5.5), (1.8, 4.2, 4.5), 30),                      # the two-shot again
    (F_NAMES, F_HOW - 1, (9.5, 12.5, 6.5), (0.5, 5.0, 5.0), 35),                          # Yellow answering
    (F_HOW, F_LOOK_ARM - 1, (13.0, -1.5, 8.6), (3.6, 3.2, 7.6), 36),                      # Lime's face from his front-right
    (F_LOOK_ARM, F_END, (13.0, -2.5, 8.4), (3.7, 3.0, 7.4), 38),                          # he looks at his arm: LIME on the forearm, then "Lime."
]
for start, end, cpos, tgt, lens in SHOTS:
    for f in range(start, end + 1):
        pos = jet(f, cpos)
        if tgt is None:                                       # the falling shot: aim between the bow and Lime
            aim = jet(f, (0, -6, 3)).lerp(lime_head(f), 0.55)
        else:
            aim = jet(f, tgt)
        cam_key(f, pos, aim, lens)

# ------------------------------------------------------------ output and checks
scene.frame_end = F_END
scene.frame_set(1)
print("beat 7 keyed", F0 + 1, "->", F_END, "| catch at", F_CATCH, "| circle centre", tuple(round(v, 1) for v in centre),
      "| cues:", SOUND_CUES, "| subtitles:", len(SUBTITLES))
