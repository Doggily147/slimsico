"""Draft 2, beat 6: Purple. As the monster's claw hangs over Yellow, a whine
from the sky: Purple swoops in on the jetski at speed, banks in low beside
Yellow and hovers there, sitting on the rider seat, and holds out his hand.
Yellow, propped on his elbows, says "Who are you?". Purple says nothing (he
never does). Yellow grabs the hand; the jetski lifts and Yellow dangles from
it as it climbs. An insert shows the two hands, Yellow's grip slipping, while
the jetski flies on and higher. Yellow slips and drops; Purple snaps his arm
down and catches him by the wrist with one hand, hauls him up, and Yellow
climbs onto the passenger seat. Flying on: "Where are we going?" Three
seconds. "Hello, are you going to answer me?" "You're not much of a talker,
are you?" Purple looks straight ahead.

Frames 1081-1656 at 24 fps. Run inside Blender with slimsico.blend open after
build_draft2_beat5.py (and build_purple's Purple in the "Purple" collection).
Re-running replaces everything after frame 1080. Render with render_draft2.py.
"""
import bpy
import math
import os
import sys
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, fcurves, floor_violations, key  # noqa: E402

scene = bpy.data.scenes["Scene"]
if bpy.context.window:
    bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
target = bpy.data.objects["CamTarget"]
mouth = bpy.data.objects["Mouth"]
mouth_open = bpy.data.objects["MouthOpen"]
mrig = bpy.data.objects["MonsterRig"]
hc = bpy.data.objects["Hovercraft"]
prig = bpy.data.objects["PurpleRig"]
purple_col = bpy.data.collections["Purple"]

FPS = 24
F0 = 1080                                  # where beat 5 ends
F_SWOOP, F_ARRIVE = 1081, 1128             # the dive in; hovering beside him
F_HAND = 1134                              # Purple's hand comes out
F_WHO, F_WHO_END = 1166, 1196              # "Who are you?"
F_SIT, F_GRAB = 1200, 1226                 # Yellow sits up and reaches; the hands meet
F_LIFT = 1236                              # the jetski lifts
F_INSERT, F_INSERT_END = 1262, 1284        # the hands, slipping
F_SLIP, F_CATCH = 1300, 1306               # he lets go; Purple catches his wrist
F_HAUL, F_ON = 1318, 1372                  # pulled up; seated behind Purple
F_WHERE, F_WHERE_END = 1392, 1430          # "Where are we going?"
F_HELLO, F_HELLO_END = 1502, 1562          # three seconds later: "Hello, are you going to answer me?"
F_TALKER, F_TALKER_END = 1578, 1636        # "You're not much of a talker, are you?"
F_END = 1656
GRAB, CATCH_ARM = "L", "R"                 # the jetski hovers on his left: left hand grabs, right wrist gets caught
SUBTITLES = [("Who are you?", F_WHO, F_WHO_END), ("Where are we going?", F_WHERE, F_WHERE_END),
             ("Hello, are you going to answer me?", F_HELLO, F_HELLO_END), ("You're not much of a talker, are you?", F_TALKER, F_TALKER_END)]
SOUND_CUES = [("swoop", F_SWOOP), ("hover", F_ARRIVE - 10), ("lift", F_LIFT), ("roar", F_LIFT + 12), ("climb", F_INSERT_END), ("slip", F_SLIP), ("catch", F_CATCH)]


def clear_after(obj, frame):
    for fc in fcurves(obj):
        for kp in reversed(list(fc.keyframe_points)):
            if kp.co.x > frame + 0.5:
                fc.keyframe_points.remove(kp)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def at(frame):
    """Move to a frame only when not already there: frame_set re-evaluates the
    whole scene, and this beat asks for the same frame many times over."""
    if scene.frame_current != frame:
        scene.frame_set(frame)


for o in (rig, cam, cam.data, target, mrig, mouth, mouth_open, hc):
    clear_after(o, F0)
clear_after(prig, 0)
prig.animation_data_clear()
scene.frame_set(F0)
RX, SY = rig.location.x, rig.location.y     # Yellow lies here, head toward +Y, the monster on his -Y side
poser = Poser(rig)
pposer = Poser(prig)
mposer = Poser(mrig, order=["spine.001", "spine.002", "spine.003", "neck", "head", "snout", "jaw",
                            "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
                            "thigh.L", "shin.L", "thigh.R", "shin.R", "tail.001", "tail.002", "tail.003"])
HEAD_FRONT = (0, -0.25, 0.97)


def key_rot(some_rig, frame, x, y=0.0, z=0.0):
    scene.frame_set(frame)
    some_rig.rotation_mode = "QUATERNION"
    some_rig.rotation_quaternion = Euler((x, y, z)).to_quaternion()
    some_rig.keyframe_insert("rotation_quaternion", frame=frame)


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


def say(first, last, shapes, gap=6):
    """Yellow talks: the smile swaps for the open mouth, which opens per syllable."""
    for o, on in ((mouth, True), (mouth_open, False)):
        show(o, first, not on)
        show(o, last, on)
    key(mouth_open, first, scale=CLOSED)
    span = last - first - 6
    gap = max(4, min(gap, span // max(1, len(shapes))))
    for i, shape in enumerate(shapes):
        f = first + 3 + i * gap
        key(mouth_open, f + 2, scale=shape)
        key(mouth_open, f + gap - 1, scale=CLOSED)
    key(mouth_open, last, scale=CLOSED)


# ------------------------------------------------------------ the jetski's flight
# World path of the "Hovercraft" root (it faces its local -Y; heading 0 = flying
# toward -Y, +90 deg = toward +X). Purple sits on it, parented, so he rides it.
HOVER = Vector((RX - 6.2, SY + 0.6, 1.35))               # hovering beside Yellow, low, pods just off the plate
FAR = Vector((RX - 6.2, SY + 95.0, 48.0))                 # where it comes from: far behind his head and high
path = {}                                                 # frame -> (pos, heading, pitch, roll)


def seg(f0, f1, p0, p1, h0, h1, ease="smooth", arc=0.0):
    for f in range(f0, f1 + 1):
        u = (f - f0) / max(1, f1 - f0)
        w = smooth(u) if ease == "smooth" else (1 - (1 - u) ** 2.2 if ease == "out" else u * u)
        p = Vector(p0).lerp(Vector(p1), w)
        p.z += arc * math.sin(math.pi * u)
        path[f] = [p, h0 + (h1 - h0) * w, 0.0, 0.0]


seg(F_SWOOP, F_ARRIVE, FAR, HOVER, 0, 0, ease="out")
seg(F_ARRIVE, F_LIFT, HOVER, HOVER, 0, 0)
UP1 = Vector((RX - 3.0, SY - 6.0, 7.5))                   # the first lift: up and forward, turning away from the monster
UP2 = Vector((RX + 18.0, SY - 14.0, 15.0))
UP3 = Vector((RX + 48.0, SY - 16.0, 24.0))
CRUISE0 = Vector((RX + 66.0, SY - 16.0, 26.0))
seg(F_LIFT, F_INSERT, HOVER, UP1, 0, 50, ease="in")
seg(F_INSERT, F_SLIP, UP1, UP2, 50, 90, ease="smooth")
seg(F_SLIP, F_ON, UP2, UP3, 90, 90, ease="smooth")
seg(F_ON, F_END, UP3, CRUISE0 + Vector((0.42 * (F_END - F_ON) - 18.0, 0, 0)), 90, 90, ease="smooth")
# the catch: a dip and a lurch as Purple grabs him
for f in range(F_SLIP, F_CATCH + 10):
    d = math.sin(math.pi * (f - F_SLIP) / (F_CATCH + 10 - F_SLIP))
    path[f][0] = path[f][0] + Vector((0, 0, -0.9 * d))
# pitch from the vertical speed, roll from the turn rate; a hover bob when parked
for f in range(F_SWOOP, F_END + 1):
    p0 = path[max(F_SWOOP, f - 1)][0]
    p1 = path[min(F_END, f + 1)][0]
    v = (p1 - p0) / 2
    horiz = math.hypot(v.x, v.y)
    pitch = -math.atan2(v.z, max(horiz, 0.05)) * 0.55
    h0 = path[max(F_SWOOP, f - 1)][1]
    h1 = path[min(F_END, f + 1)][1]
    roll = -math.radians(h1 - h0) * 6.0
    if F_ARRIVE <= f <= F_LIFT:
        pitch = math.radians(2.0) * math.sin(2 * math.pi * f / 40.0)
        path[f][0] = path[f][0] + Vector((0, 0, 0.08 * math.sin(2 * math.pi * f / 36.0)))
    if f < F_ARRIVE:                                      # the flare as it arrives
        u = (f - F_SWOOP) / (F_ARRIVE - F_SWOOP)
        pitch += math.radians(-14) * max(0.0, 1 - abs(u - 0.82) / 0.18)
        roll += math.radians(18) * math.sin(math.pi * u) * math.sin(2 * math.pi * u * 0.5)
    path[f][2], path[f][3] = pitch, roll
hc.rotation_mode = "XYZ"
for f in range(F_SWOOP, F_END + 1):
    p, h, pitch, roll = path[f]
    key(hc, f, loc=tuple(p), rot=(pitch, roll, math.radians(h)), interp="LINEAR")
for o in hc.children:                                     # parked and hidden until now; it flies in this beat
    for fc in fcurves(o):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for kp in reversed(list(fc.keyframe_points)):
                fc.keyframe_points.remove(kp)
    show(o, 1, False)
    show(o, F_SWOOP, True)
    o.hide_render = False
    o.hide_viewport = False


def hc_matrix(frame):
    at(frame)
    return hc.matrix_world.copy()


# ------------------------------------------------------------ Purple rides it
# Parented to the jetski root: sits on the rider cushion, leaning forward to
# the handlebars. His rig faces the jetski's forward (-Y) like Yellow's would.
purple_col.hide_render = False
for o in purple_col.objects:
    o.hide_render = False
prig.parent = hc
prig.parent_type = "OBJECT"
prig.matrix_parent_inverse.identity()
prig.rotation_mode = "XYZ"
prig.location = (0.0, 0.15, 0.95)                         # pelvis joint ~0.9 above the cushion: the body's bulk sits on it, not through it
prig.rotation_euler = (0, 0, 0)
prig.scale = (1, 1, 1)
RIDE = {"spine.001": (0, -0.30, 0.95), "spine.002": (0, -0.48, 0.88), "spine.003": (0, -0.52, 0.85), "neck": (0, -0.35, 0.94), "head": (0, -0.3, 0.95),
        "thigh.L": (-0.22, -0.92, -0.32), "shin.L": (-0.12, -0.42, -0.9), "thigh.R": (0.22, -0.92, -0.32), "shin.R": (0.12, -0.42, -0.9),
        "upper_arm.L": (-0.5, -0.72, -0.48), "forearm.L": (-0.45, -0.88, 0.12), "upper_arm.R": (0.5, -0.72, -0.48), "forearm.R": (0.45, -0.88, 0.12)}
HAND_OUT = {**RIDE, "spine.001": (0.2, -0.25, 0.95), "spine.002": (0.42, -0.3, 0.86), "spine.003": (0.55, -0.3, 0.78),   # leans right out to his right
            "upper_arm.R": (0.97, -0.12, -0.2), "forearm.R": (0.98, -0.1, -0.15), "hand.R": (0.97, -0.08, -0.22),
            "upper_arm.L": (-0.3, -0.75, -0.6), "forearm.L": (-0.25, -0.9, -0.05)}
pposer_order = pposer.order + ["hand.R", "hand.L"]
pposer = Poser(prig, order=pposer_order)
pposer.pose(F0 + 1, RIDE)
pposer.pose(F_ARRIVE, RIDE)
pposer.pose(F_HAND + 8, HAND_OUT)


def purple_hand(frame):
    at(frame)
    return prig.matrix_world @ prig.pose.bones["hand.R"].tail


def yellow_point(frame, bone="head"):
    at(frame)
    return rig.matrix_world @ rig.pose.bones[bone].head


# ------------------------------------------------------------ the monster flinches back
# the claw pulls away and it rears as the jetski screams in, then it stands
# there watching them go, jaw working
scene.frame_set(F0)
MSTART = {n: tuple(mrig.pose.bones[n].matrix.to_3x3() @ Vector((0, 1, 0))) for n in mposer.order}
REAR = {"spine.001": (0, 0.1, 1.0), "spine.002": (0, 0.05, 1.0), "spine.003": (0, -0.05, 1.0), "neck": (0, -0.35, 0.94), "head": (0, -0.5, 0.87),
        "jaw": (0, -0.7, -0.7), "upper_arm.L": (-0.7, -0.3, -0.65), "forearm.L": (-0.55, -0.55, -0.62),
        "upper_arm.R": (0.7, -0.5, 0.5), "forearm.R": (0.6, -0.7, 0.4), "hand.R": (0.5, -0.8, 0.3),
        "tail.001": (0, 0.85, -0.5), "tail.002": (0, 0.9, -0.42), "tail.003": (0, 0.9, -0.35)}
MZ = mrig.location.z
M0 = mrig.location.copy()
MROT = tuple(mrig.rotation_euler)
LUNGE = {**REAR, "spine.001": (0, -0.3, 0.95), "spine.002": (0, -0.55, 0.83), "spine.003": (0, -0.65, 0.76), "neck": (0, -0.75, 0.66), "head": (0, -0.8, 0.6),
         "jaw": (0, -0.55, -0.83), "upper_arm.L": (-0.75, -0.55, -0.35), "forearm.L": (-0.55, -0.8, -0.25)}
SWIPE_UP = (0.55, -0.35, 0.75)                             # the right arm cocks back over its head ...
SWIPE_DOWN = (0.35, -0.9, -0.25)                           # ... and comes down where Yellow was
ROAR = {**REAR, "spine.003": (0, 0.1, 0.99), "neck": (0, -0.2, 0.98), "head": (0, -0.35, 0.94), "jaw": (0, -0.45, -0.89),
        "upper_arm.L": (-0.6, -0.3, 0.74), "forearm.L": (-0.5, -0.35, 0.79), "upper_arm.R": (0.6, -0.3, 0.74), "forearm.R": (0.5, -0.35, 0.79), "hand.R": (0.4, -0.3, 0.87)}
mrig.rotation_mode = "XYZ"
key(mrig, F0 + 1, loc=tuple(M0), rot=MROT)
for f in range(F0 + 1, F_END + 1):
    u = smooth((f - (F_ARRIVE - 8)) / 10.0)
    p = {}
    for n in mposer.order:
        a = Vector(MSTART.get(n, (0, 0, 1)))
        b = Vector(REAR.get(n, MSTART.get(n, (0, 0, 1))))
        p[n] = tuple(a.lerp(b, u).normalized())
    # the lunge: from the moment Yellow reaches, it comes on at him
    lunge = smooth((f - F_SIT) / 14.0) * (1.0 - smooth((f - (F_LIFT + 18)) / 22.0))
    for n in LUNGE:
        p[n] = tuple(Vector(p[n]).lerp(Vector(LUNGE[n]), lunge).normalized())
    # the swipe: cocked back as the hands meet, comes down as the jetski lifts, and misses
    cock = smooth((f - (F_GRAB - 4)) / 8.0)
    strike = smooth((f - (F_LIFT + 1)) / 7.0)
    if cock > 0:
        arm = Vector(p["upper_arm.R"]).lerp(Vector(SWIPE_UP), cock).lerp(Vector(SWIPE_DOWN), strike)
        p["upper_arm.R"] = tuple(arm.normalized())
        p["forearm.R"] = tuple((arm + Vector((0.1, -0.2, -0.15 * strike))).normalized())
        p["hand.R"] = tuple((arm + Vector((0, -0.3, -0.3 * strike))).normalized())
    # then it rears up and roars after them
    roar = smooth((f - (F_LIFT + 12)) / 10.0) * (1.0 - smooth((f - (F_LIFT + 50)) / 30.0))
    for n in ROAR:
        p[n] = tuple(Vector(p[n]).lerp(Vector(ROAR[n]), roar).normalized())
    if f >= F_ARRIVE + 2:
        s = math.sin(2 * math.pi * (f - F_ARRIVE) / 14.0)
        if roar < 0.5 and strike < 0.5:
            p["jaw"] = (0, -0.7 - 0.12 * s, -0.7)
        p.update(look_at(mrig, (path[f][0] + Vector((0, 0, 2.5))) if f > F_LIFT + 8 else yellow_point(f), f,
                         front=(0, -0.5, 0.87), max_up=0.95, neck=0.45, blend=1.0 - 0.6 * roar))
    mposer.pose(f, p)
    # it steps in toward him with the lunge (toward +Y, where he lies), sinking on the plant
    my = M0.y + 2.6 * lunge
    key(mrig, f, loc=(M0.x, my, M0.z - 0.25 * lunge + 0.15 * roar), rot=(MROT[0] - 0.12 * roar, MROT[1], MROT[2]), interp="LINEAR")

# ------------------------------------------------------------ Yellow
# 1. propped on his elbows he turns his head to the jetski, then to Purple's hand
PROP = {"upper_arm.L": (-0.5, 0.55, -0.67), "forearm.L": (-0.35, -0.3, 0.88), "upper_arm.R": (0.5, 0.55, -0.67), "forearm.R": (0.35, -0.3, 0.88),
        "thigh.L": (-0.08, -0.7, -0.7), "shin.L": (-0.05, 0.45, -0.9), "thigh.R": (0.08, -0.72, -0.68), "shin.R": (0.05, 0.5, -0.87),
        "spine.001": (0, -0.1, 1.0), "spine.002": (0, -0.3, 0.95), "spine.003": (0, -0.45, 0.9)}
COWER = {**PROP, "upper_arm.L": (-0.55, -0.7, 0.45), "forearm.L": (0.35, -0.45, 0.82), "upper_arm.R": (0.55, -0.7, 0.45), "forearm.R": (-0.35, -0.45, 0.82),
         "thigh.L": (-0.1, -0.85, -0.5), "shin.L": (-0.05, 0.6, -0.8), "thigh.R": (0.1, -0.87, -0.48), "shin.R": (0.05, 0.62, -0.78)}
PROP_ROT = math.radians(-66)
key(rig, F0 + 1, loc=(RX, SY, 0.0), scale=(1, 1, 1))
key_rot(rig, F0 + 1, PROP_ROT, 0, math.radians(360))
key(rig, F_SIT, loc=(RX, SY, 0.0))
key_rot(rig, F_SIT, PROP_ROT, 0, math.radians(360))
for f in range(F0 + 1, F_SIT + 1):
    u = smooth((f - (F_ARRIVE - 14)) / 14.0)             # the arms come down off his face as the jetski arrives
    p = {k: tuple(Vector(COWER[k]).lerp(Vector(PROP[k]), u)) for k in PROP}
    if f < F_ARRIVE - 10:
        p.update(look_at(rig, path[f][0], f, blend=0.6))
    elif f < F_HAND + 10:
        p.update(look_at(rig, path[f][0] + Vector((0, 0, 3.0)), f))
    else:
        p.update(look_at(rig, purple_hand(f) if f > F_HAND + 8 else path[f][0] + Vector((0, 0, 3.0)), f))
    poser.pose(f, p)
say(F_WHO, F_WHO_END, (ROUND, WIDE, MID), gap=9)          # Who / are / you

# 2. sits up and reaches: the right arm goes up to the hand
SIT = {**PROP, "spine.001": (-0.05, -0.15, 0.99), "spine.002": (-0.22, -0.2, 0.95), "spine.003": (-0.32, -0.2, 0.93),      # up on his feet, leaning to the jetski
       "upper_arm.R": (0.5, -0.3, -0.81), "forearm.R": (0.45, -0.35, -0.82),
       "thigh.L": (-0.08, -0.14, -0.99), "shin.L": (-0.05, 0.06, -1.0), "thigh.R": (0.08, -0.18, -0.98), "shin.R": (0.05, 0.1, -0.99)}
SIT_ROT = 0.0


def reach_dirs(frame, base, arm="R", blend=1.0):
    """Aim the right arm straight at Purple's hand from the shoulder, in the rig's rest space."""
    at(frame)
    sh = rig.matrix_world @ rig.pose.bones["upper_arm." + arm].head
    d = (rig.matrix_world.to_3x3().inverted() @ (purple_hand(frame) - sh)).normalized()
    rest = Vector(base["upper_arm." + arm])
    return {"upper_arm." + arm: tuple(rest.lerp(d, blend).normalized()), "forearm." + arm: tuple(Vector(base["forearm." + arm]).lerp(d, blend).normalized()),
            "hand." + arm: tuple(d)}


poser = Poser(rig, order=Poser.ORDER + ["hand.L", "hand.R"])
for f in range(F_SIT + 1, F_GRAB + 1):
    u = smooth((f - F_SIT) / (F_GRAB - F_SIT))
    p = {k: tuple(Vector(PROP[k]).lerp(Vector(SIT[k]), u)) for k in PROP}
    p.update(reach_dirs(f, p, arm=GRAB, blend=u))
    p.update(look_at(rig, purple_hand(f), f))
    key_rot(rig, f, PROP_ROT * (1 - u) + SIT_ROT * u, 0, math.radians(360))
    poser.pose(f, p)
    # he shuffles toward the hand as he reaches, so the hands meet at F_GRAB without a jump
    scene.view_layers[0].update()
    hand = rig.matrix_world @ rig.pose.bones["hand." + GRAB].tail
    delta = (purple_hand(f) - hand) * u
    loc = Vector((RX, SY, 0.0)) + delta
    loc.z = 0.0                                           # on his feet on the plate; the arm does the reaching
    key(rig, f, loc=tuple(loc), interp="LINEAR")
from rig_utils import ground_clamp
ground_clamp(rig, body, range(F_SIT + 1, F_GRAB + 1))        # the scramble up never dips below the plate

# 3. lifted: he hangs from Purple's hand, body straight below it, legs kicking,
# the other arm reaching for the grip too; the rig is placed each frame so his
# right hand sits in Purple's
HANG = {"spine.001": (0, 0.0, 1.0), "spine.002": (0, 0.0, 1.0), "spine.003": (0, 0.0, 1.0), "neck": (0, -0.1, 1.0),
        "upper_arm.L": (-0.15, 0.0, 0.99), "forearm.L": (-0.05, 0.0, 1.0), "hand.L": (0.0, 0.0, 1.0),
        "upper_arm.R": (0.35, -0.2, 0.92), "forearm.R": (0.15, -0.15, 0.98), "hand.R": (0, 0, 1),
        "thigh.L": (-0.12, -0.15, -0.98), "shin.L": (-0.05, 0.1, -0.99), "thigh.R": (0.12, -0.15, -0.98), "shin.R": (0.05, 0.1, -0.99)}


def swing_out(frame, x, tilt):
    """Body rotation for hanging under the jetski: pitched by `x`, turned with the
    heading, and swung outward from the hull by `tilt` about the jetski's forward axis."""
    from mathutils import Quaternion
    h = math.radians(path[frame][1])
    forward = Vector((math.sin(h), -math.cos(h), 0))
    q = Quaternion(forward, tilt) @ Euler((x, 0, math.radians(360) + h)).to_quaternion()
    at(frame)
    rig.rotation_mode = "QUATERNION"
    rig.rotation_quaternion = q
    rig.keyframe_insert("rotation_quaternion", frame=frame)


def place_hand(frame, dirs, goal, arm="R", slip=0.0, floor=False):
    """Pose, then move the rig so his hand meets `goal` (his hand slides `slip`
    below it). With `floor`, he never sinks below the plate: the hands part a
    little instead while he is still being pulled to his feet."""
    poser.pose(frame, dirs)
    scene.view_layers[0].update()
    hand = rig.matrix_world @ rig.pose.bones["hand." + arm].tail
    delta = Vector(goal) - hand - Vector((0, 0, slip))
    loc = Vector(rig.location) + delta
    if floor and loc.z < 0.0:
        loc.z = 0.0
    key(rig, frame, loc=tuple(loc), interp="LINEAR")


for f in range(F_GRAB + 1, F_SLIP + 1):
    hz = purple_hand(f).z
    u = smooth((hz - 5.6) / 6.0)                          # off his feet as the hand rises
    p = {k: tuple(Vector(SIT.get(k, HANG[k])).lerp(Vector(HANG[k]), u)) for k in HANG}
    if u < 1.0:
        p.update(reach_dirs(f, p, arm=GRAB, blend=1.0 - u))
    k2 = 2 * math.pi * f / 22.0                           # the legs kick once he is off the ground
    kick = 0.55 * smooth((hz - 10.8) / 3.0)
    p["thigh.L"] = (-0.12, -0.15 - kick * math.sin(k2), -0.98)
    p["thigh.R"] = (0.12, -0.15 + kick * math.sin(k2), -0.98)
    p["shin.L"] = (-0.05, 0.1 + 0.4 * kick * max(0.0, math.sin(k2)), -0.99)
    p["shin.R"] = (0.05, 0.1 + 0.4 * kick * max(0.0, -math.sin(k2)), -0.99)
    slip = 0.0
    if f >= F_INSERT:                                     # the grip creeps down the hand
        slip = 0.28 * smooth((f - F_INSERT) / (F_SLIP - F_INSERT))
    p.update(look_at(rig, purple_hand(f) + Vector((0, 0, 1.0)), f, max_up=0.95))
    # tilt the whole body to hang under the hand, swung outward clear of the hull once airborne
    swing_out(f, SIT_ROT * (1 - u) + math.radians(-6) * u, math.radians(30) * smooth((hz - 10.3) / 3.0))
    place_hand(f, p, purple_hand(f), arm=GRAB, slip=slip, floor=True)
# the wrist tremble in the insert
for f in range(F_INSERT, F_INSERT_END + 1):
    scene.frame_set(f)
    j = 0.03 * math.sin(2 * math.pi * f / 2.0)
    key(rig, f, loc=(rig.location.x + j, rig.location.y, rig.location.z - abs(j)), interp="LINEAR")

# 4. the slip and the catch: he drops, Purple's arm snaps down and grabs his left wrist
scene.frame_set(F_SLIP)
DROP = 1.25
for f in range(F_SLIP + 1, F_CATCH + 1):
    u = (f - F_SLIP) / (F_CATCH - F_SLIP)
    p = dict(HANG)
    p["upper_arm.L"] = (-0.6, -0.2, 0.77)                 # the freed hand flails
    p["forearm.L"] = (-0.7, -0.3, 0.6)
    p["upper_arm.R"] = (0.25, -0.1, 0.97)                 # the right arm stays up: that is the one Purple catches
    p["forearm.R"] = (0.1, -0.05, 0.99)
    p.update(look_at(rig, purple_hand(f), f, max_up=0.95))
    swing_out(f, math.radians(-6 - 10 * u), math.radians(30 - 8 * u))
    place_hand(f, p, purple_hand(f) - Vector((0, 0, DROP * u * u)), arm=CATCH_ARM)
# Purple's arm snaps down to the catch, then he hauls
CATCH = {**RIDE, "spine.002": (0.35, -0.2, 0.92), "spine.003": (0.5, -0.1, 0.86), "upper_arm.R": (0.75, -0.1, -0.65), "forearm.R": (0.7, -0.05, -0.7), "hand.R": (0.6, 0, -0.8)}
pposer.pose(F_INSERT_END, HAND_OUT)
pposer.pose(F_SLIP, HAND_OUT)
pposer.pose(F_CATCH - 1, CATCH)
pposer.pose(F_CATCH + 8, CATCH)
for f in range(F_CATCH + 1, F_HAUL + 1):
    p = dict(HANG)
    p["upper_arm.L"] = (-0.5, -0.3, 0.8)                  # the loose arm reaches back up for the grip
    p["forearm.L"] = (-0.55, -0.35, 0.75)
    p["upper_arm.R"] = (0.25, -0.1, 0.97)
    p["forearm.R"] = (0.1, -0.05, 0.99)
    sw = 0.2 * math.sin(2 * math.pi * (f - F_CATCH) / 9.0) * max(0.0, 1 - (f - F_CATCH) / 12.0)   # the swing after the catch
    p["thigh.L"] = (-0.12, -0.2 + sw, -0.97)
    p["thigh.R"] = (0.12, -0.2 + sw, -0.97)
    p.update(look_at(rig, purple_hand(f) + Vector((0, 0, 1.5)), f, max_up=0.95))
    swing_out(f, math.radians(-16 + 10 * smooth((f - F_CATCH) / 10.0)), math.radians(24) + sw * 0.5)
    place_hand(f, p, purple_hand(f) - Vector((0, 0, DROP)), arm=CATCH_ARM)

# 5. hauled up and onto the passenger seat: Purple pulls, Yellow's body comes
# up and swings over the seat, and he settles behind Purple holding his waist
HAUL = {**CATCH, "upper_arm.R": (0.55, -0.35, 0.75), "forearm.R": (0.4, -0.35, 0.85), "hand.R": (0.3, -0.3, 0.9)}
pposer.pose(F_HAUL + 14, HAUL)
pposer.pose(F_ON - 6, RIDE)
pposer.pose(F_ON, RIDE)
SEATED = {"spine.001": (0, -0.12, 0.99), "spine.002": (0, -0.2, 0.98), "spine.003": (0, -0.22, 0.97), "neck": (0, -0.15, 0.99), "head": (0, -0.22, 0.97),
          "thigh.L": (-0.25, -0.9, -0.37), "shin.L": (-0.15, -0.45, -0.88), "thigh.R": (0.25, -0.9, -0.37), "shin.R": (0.15, -0.45, -0.88),
          "upper_arm.L": (-0.35, -0.85, -0.4), "forearm.L": (-0.05, -0.98, -0.2), "hand.L": (0, -1, 0),
          "upper_arm.R": (0.35, -0.85, -0.4), "forearm.R": (0.05, -0.98, -0.2), "hand.R": (0, -1, 0)}
SEAT_LOCAL = Vector((0.0, 4.15, 0.95))                     # on the passenger cushion (pelvis joint ~0.9 above it), in the jetski's frame
for f in range(F_HAUL + 1, F_ON + 1):
    u = smooth((f - F_HAUL) / (F_ON - F_HAUL))
    p = {k: tuple(Vector(HANG[k]).lerp(Vector(SEATED[k]), u)) for k in HANG}
    p.update(look_at(rig, purple_hand(f) + Vector((0, 0, 1.0)), f, blend=1 - u, max_up=0.95))
    M = hc_matrix(f)
    hang_goal = purple_hand(f) - Vector((0, 0, DROP * (1 - u)))
    seat_goal = M @ SEAT_LOCAL
    # world placement: from hanging under the hand to sitting on the seat, rising over the side
    swing_out(f, math.radians(-8) * (1 - u), math.radians(24) * (1 - u))
    poser.pose(f, p)
    scene.view_layers[0].update()
    hand = rig.matrix_world @ rig.pose.bones["hand." + CATCH_ARM].tail
    hang_loc = Vector(rig.location) + (hang_goal - hand)
    outward = M.to_3x3() @ Vector((1.0, 0.0, 0.0))
    arc = Vector((0, 0, 2.4)) * math.sin(math.pi * u) + outward * (2.6 * math.sin(math.pi * u) * (1 - u))
    key(rig, f, loc=tuple(hang_loc.lerp(seat_goal, u) + arc), interp="LINEAR")

# 6. riding behind Purple: the seat carries him; the lines
for f in range(F_ON + 1, F_END + 1):
    M = hc_matrix(f)
    key(rig, f, loc=tuple(M @ SEAT_LOCAL), interp="LINEAR")
    key_rot(rig, f, path[f][2] * 0.6, path[f][3] * 0.6, math.radians(360 + path[f][1]))
    p = dict(SEATED)
    if F_WHERE - 6 <= f <= F_WHERE_END + 10 or F_HELLO - 8 <= f <= F_TALKER_END + 12:
        # he leans to look at the back of Purple's head while he talks
        p["spine.003"] = (0.12, -0.28, 0.95)
        p.update(look_at(rig, (M @ Vector((0, 0.15, 5.9))), f, max_up=0.7))
    poser.pose(f, p)
say(F_WHERE, F_WHERE_END, (WIDE, MID, WIDE, ROUND), gap=8)                          # Where / are / we / go-ing
say(F_HELLO, F_HELLO_END, (MID, ROUND, MID, MID, ROUND, MID, WIDE, MID), gap=6)      # Hel-lo, are you go-ing to an-swer me
say(F_TALKER, F_TALKER_END, (ROUND, MID, WIDE, MID, ROUND, MID, WIDE, ROUND), gap=6)  # You're not much of a tal-ker, are you
# Purple: eyes front the whole time; one slow glance back at "talker", then front again
pposer.pose(F_TALKER + 20, RIDE)
pposer.pose(F_TALKER + 34, {**RIDE, "head": (0.45, -0.15, 0.88), "neck": (0.2, -0.2, 0.96)})
pposer.pose(F_TALKER + 52, {**RIDE, "head": (0.45, -0.15, 0.88), "neck": (0.2, -0.2, 0.96)})
pposer.pose(F_TALKER_END + 14, RIDE)
pposer.pose(F_END, RIDE)

# ------------------------------------------------------------ camera
def cam_key(f, pos, tgt, lens):
    key(cam, f, loc=tuple(pos), interp="LINEAR")
    key(target, f, loc=tuple(tgt), interp="LINEAR")
    scene.frame_set(f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)


def jet(f, local):
    return hc_matrix(f) @ Vector(local)


# the swoop: from the ground beyond Yellow's feet, looking up past him at the sky it comes out of
for f in range(F_SWOOP, F_ARRIVE + 1):
    u = (f - F_SWOOP) / (F_ARRIVE - F_SWOOP)
    look = path[f][0].lerp(Vector((RX - 3.0, SY + 1.5, 3.5)), smooth((u - 0.55) / 0.45))
    cam_key(f, (RX + 12.0, SY - 3.0, 1.6), look, 22)
# the hand comes out: medium on Purple leaning out, Yellow's head at the bottom of frame
for f in (F_ARRIVE + 1, F_WHO - 1):
    cam_key(f, (RX + 5.5, SY + 12.5, 4.8), (RX - 4.4, SY + 0.9, 4.6), 30)
# "Who are you?": his face, from above his feet, the hand hanging in at the top
for f in (F_WHO, F_SIT - 1):                              # (the monster stands at SY - 5.4: stay this side of it)
    cam_key(f, (RX + 2.8, SY - 3.4, 3.7), (RX - 0.6, SY + 1.6, 2.9), 40)
# he sits up and grabs it: a two-shot from behind his head
for f in (F_SIT, F_LIFT - 1):
    cam_key(f, (RX + 2.4, SY + 9.0, 3.4), (RX - 2.6, SY + 0.6, 3.6), 30)
# lift-off: static on the ground, panning up with them
for f in range(F_LIFT, F_INSERT):
    cam_key(f, (RX + 11.0, SY + 7.0, 2.0), path[f][0] + Vector((0, 0, 1.0)), 28)
# the insert: the hands, tight, riding along with them
for f in range(F_INSERT, F_INSERT_END + 1):
    g = purple_hand(f)
    side = Matrix.Rotation(math.radians(path[f][1]), 3, "Z") @ Vector((1.0, -1.1, 1.1)).normalized()
    cam_key(f, g + side * 4.4, g - Vector((0, 0, 0.3)), 45)
# climbing higher: from the ground, small against the sky
for f in range(F_INSERT_END + 1, F_SLIP - 2):
    cam_key(f, (RX + 14.0, SY - 2.0, 1.5), path[f][0] - Vector((0, 0, 1.0)), 24)
# the slip and the catch, then the haul: alongside, tracking, Yellow's side
for f in range(F_SLIP - 2, F_ON + 1):
    M = hc_matrix(f)
    if f < F_HAUL:
        cam_key(f, M @ Vector((13.0, 0.5, 0.5)), M @ Vector((4.2, 0.6, -1.5)), 30)
    else:
        cam_key(f, M @ Vector((14.0, -4.0, 3.5)), M @ Vector((2.5, 2.5, 2.5)), 30)
# flying on: ahead and to Purple's left, looking back at both of them
for f in range(F_ON + 1, F_END + 1):
    M = hc_matrix(f)
    if f < F_HELLO - 8:
        cam_key(f, M @ Vector((-7.5, -7.0, 3.0)), M @ Vector((0.4, 2.4, 5.6)), 38)
    elif f < F_TALKER - 6:
        cam_key(f, M @ Vector((-8.5, 0.5, 6.0)), M @ Vector((0.0, 4.2, 5.8)), 45)           # closer on Yellow's face, past Purple's shoulder
    else:
        cam_key(f, M @ Vector((8.0, -5.0, 3.8)), M @ Vector((0.2, 2.6, 5.5)), 40)           # front three-quarter: Purple's blank face, Yellow behind

# ------------------------------------------------------------ output and checks
scene.frame_end = F_END
scene.frame_set(1)
bad = floor_violations(body, range(F0 + 1, F_SLIP))
print("beat 6 keyed", F0 + 1, "->", F_END, "| hover at", tuple(round(v, 1) for v in HOVER), "| below floor before lift:", bad or "none",
      "| cues:", SOUND_CUES, "| subtitles:", [(s, a, b) for s, a, b in SUBTITLES])
