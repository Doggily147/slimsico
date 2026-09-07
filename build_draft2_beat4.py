"""Draft 2, beat 4: the crate and the monster. Straight after the reveal
(frame 496) Yellow turns to face front and says "I will walk around to find
clues", walks off across the plate, hears a whistle from above and stops and
looks up; the camera drops behind his shoulder and tilts up to a crate
falling out of the sky. He turns and runs. The crate slams down where he was
while he is still running. He slows, stops, turns around and sees it. The
crate shudders, then bursts apart, planks and brackets flying, and a big
monster rises out of it, unfolds to its full height and roars. Yellow flinches.

Frames 497-912 at 24 fps. Run inside Blender with slimsico.blend open after
build_draft2.py, build_crate.py and build_monster.py. Re-running replaces
everything after frame 496. Render with render_draft2.py.
"""
import bpy
import math
import os
import random
import sys
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, fcurves, floor_violations, gait_dirs, ground_clamp, key, motion_spikes, set_interpolation, sym  # noqa: E402

scene = bpy.data.scenes["Scene"]
if bpy.context.window:                     # headless runs have no window
    bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
target = bpy.data.objects["CamTarget"]
mouth = bpy.data.objects["Mouth"]
mouth_open = bpy.data.objects["MouthOpen"]
crate = bpy.data.objects["Crate"]
monster = bpy.data.objects["Monster"]
mrig = bpy.data.objects["MonsterRig"]
random.seed(4)

FPS = 24
F0 = 496                                   # where beat 3 ends
F_LINE, F_LINE_END = 504, 558              # "I will walk around to find clues"
F_WALK, F_LOOKUP = 562, 618                # the walk; he stops and looks up
F_DROP = 612                               # the whistle: the crate starts to fall
F_TURN, F_RUN = 640, 654                   # turns and bolts
F_CLAND = 700                              # the crate slams down; he is mid-run
F_SLOW, F_STOP, F_TURNBACK, F_SEE = 712, 734, 738, 756
F_CRACK, F_BREAK, F_RISE_END = 768, 784, 830
F_ROAR, F_ROAR_END, F_END = 840, 876, 912
SUBTITLES = [("I will walk around to find clues", F_LINE, F_LINE_END)]     # render_draft2.py mirrors these
SOUND_CUES = [("crate_whistle", F_DROP), ("thud", F_CLAND), ("creak", F_CRACK), ("crash", F_BREAK), ("roar", F_ROAR)]
WALK_SPEED, STRIDE = 0.16, 24
RUN_SPEED, RUN_STRIDE = 0.42, 14
HEAD_FRONT = {"head": (0, -0.25, 0.97)}


# ------------------------------------------------------------ reset everything after beat 3
def clear_after(obj, frame):
    for fc in fcurves(obj):
        for kp in reversed(list(fc.keyframe_points)):
            if kp.co.x > frame + 0.5:
                fc.keyframe_points.remove(kp)


for o in (rig, cam, cam.data, target, mouth, mouth_open):
    clear_after(o, F0)
scene.frame_set(F0)
RX, SY = rig.location.x, rig.location.y
poser = Poser(rig)


def key_rot(frame, x, y=0.0, z=0.0, interp="BEZIER"):
    scene.frame_set(frame)
    rig.rotation_quaternion = Euler((x, y, z)).to_quaternion()
    rig.keyframe_insert("rotation_quaternion", frame=frame)
    if interp != "BEZIER":
        set_interpolation(rig, frame, interp, ("rotation_quaternion",))


def look_at(point, frame, blend=1.0, max_up=0.85):
    """Head posed so his FACE (the -Y side of the head) points at a world
    point, whichever way the rig is turned. Pitch is limited."""
    scene.frame_set(frame)
    head = rig.matrix_world @ rig.pose.bones["head"].head
    d = rig.matrix_world.to_3x3().inverted() @ (Vector(point) - head).normalized()
    d.z = max(-max_up, min(d.z, max_up))
    d.normalize()
    axis = Vector((0, -1, 0)).rotation_difference(d) @ Vector((0, 0, 1))
    front = Vector(HEAD_FRONT["head"])
    return {"head": tuple(front.lerp(axis, blend)), "neck": tuple(Vector((0, 0, 1)).lerp(axis, 0.3 * blend))}


def show(obj, frame, on):
    scene.frame_set(frame)
    obj.hide_render = not on
    obj.hide_viewport = not on
    obj.keyframe_insert("hide_render", frame=frame)
    obj.keyframe_insert("hide_viewport", frame=frame)


# ------------------------------------------------------------ 1. the line
# He turns from the reveal to face front, and says it with a small "off I go"
# gesture: the right hand comes up palm out, then sweeps out to point across
# the plate, then both arms settle. The head stays level.
ARMS_REST = {"upper_arm.L": (-0.5, -0.25, -0.83), "forearm.L": (-0.45, -0.3, -0.84),
             "upper_arm.R": (0.5, -0.25, -0.83), "forearm.R": (0.45, -0.3, -0.84)}
HEAD_UP = {"head": (0, -0.18, 0.98), "neck": (0, -0.05, 1.0)}
HAND_UP = {"upper_arm.R": (0.62, -0.5, -0.55), "forearm.R": (0.55, -0.45, 0.7)}
POINT = {"upper_arm.R": (0.85, -0.45, -0.2), "forearm.R": (0.92, -0.35, -0.1)}
key(rig, F0 + 1, loc=(RX, SY, 0.0))
key_rot(F0 + 1, 0, 0, math.radians(55))
key(rig, F_LINE + 12, loc=(RX, SY, 0.0))
key_rot(F_LINE + 12, 0, 0, 0)
poser.pose(F_LINE - 2, {**ARMS_REST, **HEAD_UP})
poser.pose(F_LINE + 8, {**ARMS_REST, **HAND_UP, **HEAD_UP})
poser.pose(F_LINE + 22, {**ARMS_REST, **HAND_UP, **HEAD_UP})
poser.pose(F_LINE + 34, {**ARMS_REST, **POINT, **HEAD_UP})
poser.pose(F_LINE + 46, {**ARMS_REST, **POINT, **HEAD_UP})
poser.pose(F_LINE_END, {**ARMS_REST, **HEAD_UP})
# the mouth opens per syllable: I / will / walk / a / round / to / find / clues
CLOSED, WIDE, MID, ROUND = (0.9, 0.4, 0.05), (1.0, 0.4, 0.7), (0.85, 0.4, 0.38), (0.8, 0.4, 0.8)
for o, on in ((mouth, True), (mouth_open, False)):
    show(o, F_LINE, not on)
    show(o, F_LINE_END, on)
key(mouth_open, F_LINE, scale=CLOSED)
for i, shape in enumerate((ROUND, MID, WIDE, MID, WIDE, MID, WIDE, ROUND)):
    f = F_LINE + 3 + i * 6
    key(mouth_open, f + 2, scale=shape)
    key(mouth_open, f + 5, scale=CLOSED)
key(mouth_open, F_LINE_END, scale=CLOSED)

# ------------------------------------------------------------ 2. the walk
# forward (his front, -Y) at a steady pace, easing in and out; head steady
walk_frames = range(F_WALK, F_LOOKUP + 1)
for f in walk_frames:
    t = f - F_WALK
    amp = min(1.0, t / 12) * min(1.0, (F_LOOKUP - f) / 8)
    dirs = gait_dirs(t, STRIDE, amp)
    dirs["head"] = HEAD_FRONT["head"]
    poser.pose(f, dirs)
    key(rig, f, loc=(RX, SY - WALK_SPEED * t, 0.0), interp="LINEAR")
key_rot(F_WALK, 0, 0, 0)
key_rot(F_WALK + 6, math.radians(3), 0, 0)
key_rot(F_LOOKUP, math.radians(3), 0, 0)
WALK_END_Y = SY - WALK_SPEED * (F_LOOKUP - F_WALK)
ground_clamp(rig, body, walk_frames)

# ------------------------------------------------------------ the crate falls
# from far up, ahead of him and a little to his right, landing just past where
# he stops; it drifts round slowly as it comes down and bounces once
CSIZE = crate["size"]
CH = CSIZE / 2
CX, CY = RX + 1.5, WALK_END_Y - 8.5
DROP_FROM = 150.0
fall = (F_CLAND - F_DROP) / FPS
GC = 2 * (DROP_FROM - CH) / fall ** 2
crate.animation_data_clear()
crate.rotation_mode = "XYZ"
key(crate, 1, loc=(CX, CY, -200), rot=(0, 0, 0), interp="CONSTANT")            # parked under the plate
for f in range(F_DROP, F_CLAND + 1):
    t = (f - F_DROP) / FPS
    z = max(CH, DROP_FROM - 0.5 * GC * t * t)
    key(crate, f, loc=(CX, CY, z), rot=(math.radians(6) * t / fall, math.radians(-4) * t / fall, math.radians(35) * t / fall), interp="LINEAR")
key(crate, F_CLAND + 3, loc=(CX, CY, CH + 0.7), rot=(math.radians(9), math.radians(-6), math.radians(35)))
key(crate, F_CLAND + 8, loc=(CX, CY, CH), rot=(math.radians(-3), math.radians(2), math.radians(35)))
key(crate, F_CLAND + 13, loc=(CX, CY, CH), rot=(0, 0, math.radians(35)))
key(crate, F_CRACK - 1, loc=(CX, CY, CH), rot=(0, 0, math.radians(35)))


def crate_pos(frame):
    scene.frame_set(frame)
    return crate.matrix_world.translation.copy()


# ------------------------------------------------------------ 3. the look up
# he stops dead, leans back a touch with the arms drifting out, and his face
# follows the crate down the sky until he turns to run
BRACE = {"upper_arm.L": (-0.7, -0.2, -0.65), "forearm.L": (-0.75, -0.3, -0.6),
         "upper_arm.R": (0.7, -0.2, -0.65), "forearm.R": (0.75, -0.3, -0.6), "spine.003": (0, 0.12, 0.99)}
key_rot(F_LOOKUP + 6, math.radians(-4), 0, 0)
for f in range(F_LOOKUP + 1, F_TURN + 1):
    blend = min(1.0, (f - F_LOOKUP) / 7)
    p = crate_pos(f) + Vector((0, 0, 2.5))
    dirs = {**ARMS_REST}
    for k in BRACE:
        dirs[k] = tuple(Vector(ARMS_REST.get(k, (0, 0, 1))).lerp(Vector(BRACE[k]), blend))
    dirs.update(look_at(p, f, blend))
    poser.pose(f, dirs)
    key(rig, f, loc=(RX, WALK_END_Y, 0.0), interp="LINEAR")

# ------------------------------------------------------------ 4. turns and runs
# a 14-frame spin (through 90 so the quaternion takes the short way), leaning
# in, then a hard run back the way he came (+Y) with a proper arm swing
key_rot(F_TURN, math.radians(-4), 0, 0)
key_rot(F_TURN + 7, math.radians(4), 0, math.radians(95))
key_rot(F_RUN, math.radians(12), 0, math.radians(180))
key_rot(F_SLOW, math.radians(12), 0, math.radians(180))
key_rot(F_STOP, math.radians(2), 0, math.radians(180))
y = WALK_END_Y
for f in range(F_TURN + 1, F_STOP + 1):
    t = f - F_RUN
    if f < F_RUN:
        amp = 0.0
    elif f < F_SLOW:
        amp = min(1.0, t / 10)
    else:
        amp = max(0.0, 1.0 - (f - F_SLOW) / (F_STOP - F_SLOW))
    ease = amp * amp * (3 - 2 * amp)
    dirs = gait_dirs(max(0, t), RUN_STRIDE, ease, run=True)
    if f < F_RUN:                                        # the spin: arms come in, the face swings round with the body
        u = (f - F_TURN) / (F_RUN - F_TURN)
        dirs = {k: tuple(Vector(BRACE[k]).lerp(Vector(dirs.get(k, (0, -0.25, -0.83))), u)) for k in BRACE if k != "spine.003"}
    dirs["head"] = HEAD_FRONT["head"]
    dirs["spine.003"] = (0, -0.06 * ease, 0.99)
    poser.pose(f, dirs)
    if f >= F_RUN:
        y += RUN_SPEED * ease
    key(rig, f, loc=(RX, y, 0.0), interp="LINEAR")
STOP_Y = y
ground_clamp(rig, body, range(F_RUN, F_STOP + 1))

# ------------------------------------------------------------ 5. turns back and sees it
key_rot(F_TURNBACK + 8, 0, 0, math.radians(270))
key_rot(F_SEE, 0, 0, math.radians(360))
key(rig, F_TURNBACK, loc=(RX, STOP_Y, 0.0))
key(rig, F_END, loc=(RX, STOP_Y, 0.0))
poser.pose(F_TURNBACK, sym(arm=(-0.45, -0.15, -0.87), fore=(-0.4, -0.25, -0.86), **HEAD_FRONT))
poser.pose(F_SEE, sym(arm=(-0.42, -0.1, -0.9), fore=(-0.38, -0.15, -0.9), **look_at((CX, CY, CH + 1.0), F_SEE)))
poser.pose(F_BREAK - 1, sym(arm=(-0.42, -0.1, -0.9), fore=(-0.38, -0.15, -0.9), **look_at((CX, CY, CH + 1.0), F_BREAK - 1)))

# ------------------------------------------------------------ the crate shudders, then bursts
# the whole crate jitters and hops, then every part above the base flies out
# from the centre, tumbles, and drops onto the plate. The base boards stay:
# the monster is standing on them.
for f in range(F_CRACK, F_BREAK):
    k = (f - F_CRACK) / (F_BREAK - F_CRACK)
    j = 0.6 + 1.6 * k
    key(crate, f, loc=(CX + random.uniform(-0.05, 0.05) * j, CY + random.uniform(-0.05, 0.05) * j, CH + random.uniform(0.0, 0.08) * j),
        rot=(math.radians(random.uniform(-1, 1) * j), math.radians(random.uniform(-1, 1) * j), math.radians(35 + random.uniform(-0.8, 0.8) * j)), interp="LINEAR")
key(crate, F_BREAK, loc=(CX, CY, CH), rot=(0, 0, math.radians(35)))
key(crate, F_END, loc=(CX, CY, CH), rot=(0, 0, math.radians(35)))
GRAV = 0.045                                            # studs per frame squared, in the crate's space
FLOOR = -CH + 0.22
parts = [o for o in crate.children]
for part in parts:
    part.animation_data_clear()
    part.rotation_mode = "XYZ"
    rest_loc, rest_rot = Vector(part["rest_loc"]), Euler(part["rest_rot"])
    key(part, 1, loc=tuple(rest_loc), rot=tuple(rest_rot), interp="CONSTANT")
    key(part, F_BREAK, loc=tuple(rest_loc), rot=tuple(rest_rot), interp="LINEAR")
    if rest_loc.z < -CH + 0.6:
        continue                                        # the base stays
    out = Vector((rest_loc.x, rest_loc.y, 0.0))
    if out.length < 0.5:
        out = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0))
    out.normalize()
    speed = random.uniform(0.22, 0.45)
    vel = out * speed + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), random.uniform(0.35, 0.8) + 0.25 * (rest_loc.z / CH)))
    spin = Vector((random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(-0.15, 0.15)))
    pos, rot = rest_loc.copy(), Vector(rest_rot)
    landed = None
    for i in range(1, 44):
        f = F_BREAK + i
        if landed is None:
            vel.z -= GRAV
            pos += vel
            rot += spin
            if pos.z <= FLOOR:
                pos.z = FLOOR
                landed = f
                # a small skid and a rock as it settles
                vel = Vector((vel.x * 0.3, vel.y * 0.3, 0))
        else:
            pos += vel
            vel *= 0.7
            rot += spin * max(0.0, 1 - (f - landed) / 5)
        key(part, f, loc=tuple(pos), rot=tuple(rot), interp="LINEAR")
    key(part, F_END, loc=tuple(pos), rot=tuple(rot), interp="LINEAR")

# ------------------------------------------------------------ the monster
# hidden in the crate until the burst; then it is there, crouched and folded
# small, and unfolds to its full height over two seconds, facing Yellow
mposer = Poser(mrig, order=["spine.001", "spine.002", "spine.003", "neck", "head", "snout", "jaw",
                            "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
                            "thigh.L", "shin.L", "thigh.R", "shin.R", "tail.001", "tail.002", "tail.003"])
mparts = [o for o in bpy.data.collections["Monster"].objects]
for o in mparts:
    if o is not mrig:
        o.animation_data_clear()
    if o.animation_data and o is mrig:
        mrig.animation_data_clear()
    show(o, 1, False)
    show(o, F_BREAK, True)
mrig.rotation_mode = "XYZ"
for pb in mrig.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0)
JAW_REST = tuple(mposer.rest["jaw"])
CROUCH = {"thigh.L": (-0.12, -0.85, -0.5), "shin.L": (-0.02, 0.35, -0.94), "thigh.R": (0.12, -0.85, -0.5), "shin.R": (0.02, 0.35, -0.94),
          "spine.001": (0, -0.4, 0.92), "spine.002": (0, -0.55, 0.83), "spine.003": (0, -0.65, 0.76), "neck": (0, -0.6, 0.8),
          "head": (0, -0.5, 0.87), "upper_arm.L": (-0.45, -0.65, -0.6), "forearm.L": (-0.2, -0.65, -0.72),
          "upper_arm.R": (0.45, -0.65, -0.6), "forearm.R": (0.2, -0.65, -0.72),
          "tail.001": (0, 0.55, -0.83), "tail.002": (0, 0.7, -0.7), "jaw": JAW_REST}
STAND = {"thigh.L": (-0.08, -0.05, -1.0), "shin.L": (-0.02, 0.05, -1.0), "thigh.R": (0.08, -0.05, -1.0), "shin.R": (0.02, 0.05, -1.0),
         "spine.001": (0, -0.08, 1.0), "spine.002": (0, -0.12, 0.99), "spine.003": (0, -0.1, 0.99), "neck": (0, -0.25, 0.97),
         "head": (0, -0.3, 0.95), "upper_arm.L": (-0.5, -0.2, -0.85), "forearm.L": (-0.3, -0.35, -0.9),
         "upper_arm.R": (0.5, -0.2, -0.85), "forearm.R": (0.3, -0.35, -0.9),
         "tail.001": (0, 0.85, -0.5), "tail.002": (0, 0.9, -0.42), "jaw": JAW_REST}
JAW_OPEN = (0, -0.55, -0.83)
ROAR_BACK = {**STAND, "head": (0, 0.2, 0.98), "neck": (0, 0.05, 1.0), "spine.003": (0, 0.1, 0.99), "jaw": (0, -0.75, -0.66),
             "upper_arm.L": (-0.8, -0.3, 0.5), "forearm.L": (-0.55, -0.35, 0.76), "upper_arm.R": (0.8, -0.3, 0.5), "forearm.R": (0.55, -0.35, 0.76)}
ROAR = {**STAND, "head": (0, -0.55, 0.83), "neck": (0, -0.35, 0.94), "spine.003": (0, -0.25, 0.97), "spine.002": (0, -0.2, 0.98), "jaw": JAW_OPEN,
        "upper_arm.L": (-0.85, -0.4, 0.35), "forearm.L": (-0.6, -0.5, 0.62), "upper_arm.R": (0.85, -0.4, 0.35), "forearm.R": (0.6, -0.5, 0.62),
        "tail.001": (0, 0.7, -0.7), "tail.002": (0, 0.85, -0.5)}
MENACE = {**STAND, "spine.002": (0, -0.3, 0.95), "spine.003": (0, -0.4, 0.92), "neck": (0, -0.55, 0.83), "head": (0, -0.6, 0.8),
          "jaw": (0, -0.85, -0.5), "upper_arm.L": (-0.6, -0.55, -0.55), "forearm.L": (-0.35, -0.7, -0.6),
          "upper_arm.R": (0.6, -0.55, -0.55), "forearm.R": (0.35, -0.7, -0.6)}


def blend(a, b, u):
    u = max(0.0, min(1.0, u))
    u = u * u * (3 - 2 * u)
    return {k: tuple(Vector(a[k]).lerp(Vector(b[k]), u)) for k in a}


def monster_pose(f):
    t = f / FPS
    if f < F_RISE_END:
        p = blend(CROUCH, STAND, (f - F_BREAK) / (F_RISE_END - F_BREAK))
    elif f < F_ROAR:
        p = dict(STAND)
    elif f < F_ROAR + 8:
        p = blend(STAND, ROAR_BACK, (f - F_ROAR) / 8)
    elif f < F_ROAR + 16:
        p = blend(ROAR_BACK, ROAR, (f - F_ROAR - 8) / 8)
    elif f < F_ROAR_END:
        p = dict(ROAR)
        # the roar shakes him: a small tremor in the head and arms
        s = 0.03 * math.sin(2 * math.pi * t * 9)
        p["head"] = (s, p["head"][1], p["head"][2])
        p["jaw"] = (0, JAW_OPEN[1] - 0.06 * abs(math.sin(2 * math.pi * t * 6)), JAW_OPEN[2])
    else:
        p = blend(ROAR, MENACE, (f - F_ROAR_END) / 14)
    # breathing: the chest swells and the tail sways
    br = 0.035 * math.sin(2 * math.pi * t / 1.6)
    p["spine.002"] = (p["spine.002"][0], p["spine.002"][1] - br, p["spine.002"][2])
    sway = 0.15 * math.sin(2 * math.pi * t / 2.4)
    p["tail.002"] = (sway, p["tail.002"][1], p["tail.002"][2])
    p["tail.003"] = (sway * 1.6, 0.9, -0.35)
    return p


for f in range(F_BREAK, F_END + 1):
    mposer.pose(f, monster_pose(f))
    u = max(0.0, min(1.0, (f - F_BREAK) / (F_RISE_END - F_BREAK)))
    s = 0.7 + 0.3 * (u * u * (3 - 2 * u))
    key(mrig, f, loc=(CX, CY, 0.25), rot=(0, 0, math.radians(180)), scale=(s, s, s), interp="LINEAR")
ground_clamp(mrig, monster, range(F_BREAK, F_END + 1), floor=0.25)

# Yellow flinches at the roar: leans back, arms up, then holds, eyes on it
FLINCH = {"upper_arm.L": (-0.7, -0.55, -0.2), "forearm.L": (-0.55, -0.5, 0.65), "upper_arm.R": (0.7, -0.55, -0.2), "forearm.R": (0.55, -0.5, 0.65),
          "spine.003": (0, 0.2, 0.98), "spine.002": (0, 0.1, 0.99)}
scene.frame_set(F_ROAR)


def monster_head(frame):
    scene.frame_set(frame)
    return mrig.matrix_world @ mrig.pose.bones["head"].head


for f in range(F_BREAK, F_END + 1):
    dirs = sym(arm=(-0.42, -0.1, -0.9), fore=(-0.38, -0.15, -0.9))
    if f >= F_ROAR + 4:
        u = min(1.0, (f - F_ROAR - 4) / 10)
        for k in FLINCH:
            dirs[k] = tuple(Vector(dirs.get(k, (0, 0, 1))).lerp(Vector(FLINCH[k]), u))
    dirs.update(look_at(monster_head(f), f))
    poser.pose(f, dirs)
key_rot(F_ROAR + 4, 0, 0, math.radians(360))
key_rot(F_ROAR + 14, math.radians(-8), 0, math.radians(360))
key_rot(F_END, math.radians(-8), 0, math.radians(360))
ground_clamp(rig, body, range(F_STOP, F_END + 1))

# ------------------------------------------------------------ camera
# Cuts, each a start key and an end key (linear), the tracked target keyed
# the same way; a few shots move the target every frame.
SHOTS = [
    (F0 + 1, F_WALK - 1, (RX - 4.0, SY - 14.0, 6.0), (RX - 3.6, SY - 13.4, 6.0), (RX, SY, 5.0), (RX, SY, 5.0), 38),        # the line, medium front
    (F_STOP + 1, F_SEE + 8, (RX + 3.5, STOP_Y - 13.5, 5.6), (RX + 3.2, STOP_Y - 13.0, 5.6), (RX, STOP_Y, 5.2), (RX, STOP_Y, 5.2), 30),   # stops and turns back
    (F_SEE + 9, F_ROAR + 2, (RX - 3.2, STOP_Y + 6.5, 6.5), (RX - 3.0, STOP_Y + 6.0, 6.8), (CX, CY, CH + 1.0), (CX, CY, 10.5), 32),   # over his shoulder: the burst and the rise
    (F_ROAR + 3, F_ROAR_END, (CX + 4.5, CY + 9.0, 4.0), (CX + 4.0, CY + 8.5, 4.2), (CX, CY, 11.0), (CX, CY, 11.0), 28),           # low angle up at the roar
    (F_ROAR_END + 1, F_END, (RX - 40.0, (CY + STOP_Y) / 2, 11.0), (RX - 42.0, (CY + STOP_Y) / 2, 11.5),
     ((CX + RX) / 2, (CY + STOP_Y) / 2, 5.5), ((CX + RX) / 2, (CY + STOP_Y) / 2, 5.5), 26),                                        # wide two-shot
]
for start, end, ca, cb, ta, tb, lens in SHOTS:
    key(cam, start, loc=ca, interp="LINEAR")
    key(cam, end, loc=cb, interp="LINEAR")
    key(target, start, loc=ta, interp="LINEAR")
    key(target, end, loc=tb, interp="LINEAR")
    for f in (start, end):
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
# the walk: a side tracking shot at eye height, full body
for f in range(F_WALK, F_LOOKUP + 3):
    yy = SY - WALK_SPEED * min(f - F_WALK, F_LOOKUP - F_WALK)
    key(cam, f, loc=(RX - 17.0, yy - 0.5, 4.8), interp="LINEAR")
    key(target, f, loc=(RX, yy, 4.3), interp="LINEAR")
for f in (F_WALK, F_LOOKUP + 2):
    cam.data.lens = 35
    cam.data.keyframe_insert("lens", frame=f)
# the look up: low behind his shoulder, and the camera follows the crate down
# the sky, so it faces straight up and tilts down with it
# the sky, so it faces up steeply with his head and shoulder at the bottom of
# the frame, and tilts down with it (a wide lens keeps both in)
UP_CAM = Vector((RX + 2.6, WALK_END_Y + 5.5, 2.2))
for f in range(F_LOOKUP + 3, F_TURN + 3):
    scene.frame_set(f)
    head = rig.matrix_world @ rig.pose.bones["head"].head
    to_crate = (crate_pos(f) - UP_CAM).normalized()
    to_head = (head - UP_CAM).normalized()
    aim = (to_crate * 0.62 + to_head * 0.38).normalized()
    key(cam, f, loc=tuple(UP_CAM), interp="LINEAR")
    key(target, f, loc=tuple(UP_CAM + aim * 30.0), interp="LINEAR")
for f in (F_LOOKUP + 3, F_TURN + 2):
    cam.data.lens = 18
    cam.data.keyframe_insert("lens", frame=f)
# the run: a wide side shot that holds him and the landing crate in one frame
mid_y = (WALK_END_Y + STOP_Y) / 2
for f in range(F_TURN + 3, F_STOP + 1):
    scene.frame_set(f)
    him = rig.matrix_world.translation
    cp = crate_pos(f)
    look = Vector(((him.x + CX) / 2, (him.y + CY) / 2, min(9.0, (him.z + 4.0 + cp.z) / 2)))
    shake = Vector((0, 0, 0))
    if F_CLAND <= f < F_CLAND + 6:
        k = 1 - (f - F_CLAND) / 6
        shake = Vector((random.uniform(-0.5, 0.5) * k, 0, random.uniform(-0.4, 0.4) * k))
    key(cam, f, loc=tuple(Vector((RX - 38.0, mid_y - 4.0, 10.0)) + shake), interp="LINEAR")
    key(target, f, loc=tuple(look), interp="LINEAR")
for f in (F_TURN + 3, F_STOP):
    cam.data.lens = 30
    cam.data.keyframe_insert("lens", frame=f)

# the jetski parked on the plate is not in this beat
for o in bpy.data.objects:
    if o.name.startswith("Hovercraft"):
        o.hide_render = True

# ------------------------------------------------------------ output and checks
scene.frame_end = F_END
scene.frame_set(1)
bad = floor_violations(body, range(F_WALK, F_END + 1))
mbad = floor_violations(monster, range(F_RISE_END, F_END + 1), tolerance=0.3)
spikes = motion_spikes(rig, range(F0 + 2, F_END), 0.5, bone="head")
print("beat 4 keyed", F0 + 1, "->", F_END, "| walk end y %.1f, stop y %.1f, crate (%.1f, %.1f)" % (WALK_END_Y, STOP_Y, CX, CY),
      "| below floor:", bad or "none", "| monster below:", mbad or "none", "| head jerks:", spikes or "none", "| cues:", SOUND_CUES)
