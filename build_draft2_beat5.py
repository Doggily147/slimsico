"""Draft 2, beat 5: Yellow backs away from the monster, step by step with his
arms up and his eyes on it, and trips over a plank that flew past him in the
burst. He goes over backwards, lands on his back with a bounce, props up on
his elbows and scoots away. The monster comes on, a heavy lumbering walk that
shakes the ground, looms over him, and reaches down with its claw open, so
close to grabbing him that the claw hangs right over his chest.

Frames 913-1080 at 24 fps. Run inside Blender with slimsico.blend open after
build_draft2_beat4.py. Re-running replaces everything after frame 912.
Render with render_draft2.py.
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
if bpy.context.window:
    bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
target = bpy.data.objects["CamTarget"]
crate = bpy.data.objects["Crate"]
monster = bpy.data.objects["Monster"]
mrig = bpy.data.objects["MonsterRig"]
random.seed(5)

FPS = 24
F0 = 912                                   # where beat 4 ends
F_BREAK = 784                              # the burst, from beat 4 (the plank's flight starts there)
F_BACK, F_TRIP, F_LAND = 916, 966, 980     # backs away; the foot catches; flat on his back
F_PROP, F_SCOOT, F_SCOOT_END = 992, 1000, 1026
F_ADV, F_LOOM, F_REACH, F_NEAR, F_END = 914, 1030, 1044, 1064, 1080
STRIDE_M = 22                              # the monster's stride, frames
SOUND_CUES = [("thump", F_LAND), ("growl", F_LOOM)] + [("stomp", f) for f in range(F_ADV + 6, F_LOOM, STRIDE_M // 2)]
BACK_SPEED = 0.12


def clear_after(obj, frame):
    for fc in fcurves(obj):
        for kp in reversed(list(fc.keyframe_points)):
            if kp.co.x > frame + 0.5:
                fc.keyframe_points.remove(kp)


for o in (rig, cam, cam.data, target, mrig):
    clear_after(o, F0)
scene.frame_set(F0)
RX, Y0 = rig.location.x, rig.location.y
MX, MY0 = mrig.location.x, mrig.location.y
poser = Poser(rig)
mposer = Poser(mrig, order=["spine.001", "spine.002", "spine.003", "neck", "head", "snout", "jaw",
                            "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
                            "thigh.L", "shin.L", "thigh.R", "shin.R", "tail.001", "tail.002", "tail.003"])
HEAD_FRONT = (0, -0.25, 0.97)


def key_rot(frame, x, y=0.0, z=0.0):
    scene.frame_set(frame)
    rig.rotation_quaternion = Euler((x, y, z)).to_quaternion()
    rig.keyframe_insert("rotation_quaternion", frame=frame)


def look_at(some_rig, point, frame, front=HEAD_FRONT, blend=1.0, max_up=0.85, neck=0.3):
    """Head posed so the face (-Y of the head in rest space) points at a world
    point, whichever way the rig is turned; pitch limited."""
    scene.frame_set(frame)
    head = some_rig.matrix_world @ some_rig.pose.bones["head"].head
    d = some_rig.matrix_world.to_3x3().inverted() @ (Vector(point) - head).normalized()
    d.z = max(-max_up, min(d.z, max_up))
    d.normalize()
    axis = Vector((0, -1, 0)).rotation_difference(d) @ Vector((0, 0, 1))
    return {"head": tuple(Vector(front).lerp(axis, blend)), "neck": tuple(Vector((0, 0, 1)).lerp(axis, neck * blend))}


def monster_head(frame):
    scene.frame_set(frame)
    return mrig.matrix_world @ mrig.pose.bones["head"].head


def yellow_chest(frame):
    scene.frame_set(frame)
    return rig.matrix_world @ rig.pose.bones["spine.002"].head


# ------------------------------------------------------------ the plank he trips on
# one slat from the burst flies further than the rest, right over his head,
# and lands just behind where he will back to
CH = crate["size"] / 2
FLOOR = -CH + 0.22
plank = next(o for o in crate.children if o.name.startswith("Crate_SlatY") and Vector(o["rest_loc"]).z > 1.5)
clear_after(plank, F_BREAK)
PLANK_WORLD = Vector((RX + 0.4, Y0 + 7.2, 0.0))
scene.frame_set(F_BREAK)
inv = crate.matrix_world.inverted()
start = Vector(plank["rest_loc"])
end = inv @ PLANK_WORLD
end.z = FLOOR
FLIGHT = 46
for i in range(1, FLIGHT + 1):
    u = i / FLIGHT
    pos = start.lerp(end, u)
    pos.z = start.z + (end.z - start.z) * u + 20.0 * math.sin(math.pi * u)      # a high arc, over his head
    rot = (math.radians(90) * u + 2 * math.pi * u * 1.5, 0.3 * math.sin(2 * math.pi * u), 0)
    key(plank, F_BREAK + i, loc=tuple(pos), rot=rot, interp="LINEAR")
key(plank, F_BREAK + FLIGHT + 4, loc=tuple(end + Vector((0, 0, 0.35))), rot=(math.radians(90) + 3 * math.pi, 0, 0.15))  # one small bounce
key(plank, F_BREAK + FLIGHT + 8, loc=tuple(end), rot=(math.radians(90) + 3 * math.pi, 0, 0.15))
key(plank, F_END, loc=tuple(end), rot=(math.radians(90) + 3 * math.pi, 0, 0.15))

# ------------------------------------------------------------ 1. backing away
# small backward steps (+Y is behind him), arms up, eyes on the monster; the
# gait runs backwards so the feet reach behind
GUARD = {"upper_arm.L": (-0.7, -0.55, -0.2), "forearm.L": (-0.55, -0.5, 0.65), "upper_arm.R": (0.7, -0.55, -0.2), "forearm.R": (0.55, -0.5, 0.65),
         "spine.003": (0, 0.2, 0.98), "spine.002": (0, 0.1, 0.99)}
key(rig, F0 + 1, loc=(RX, Y0, 0.0))
key_rot(F0 + 1, math.radians(-8), 0, math.radians(360))
key_rot(F_BACK + 8, math.radians(-10), 0, math.radians(360))
key_rot(F_TRIP, math.radians(-10), 0, math.radians(360))
y = Y0
for f in range(F_BACK, F_TRIP + 1):
    t = f - F_BACK
    amp = min(1.0, t / 8)
    dirs = gait_dirs(-t, 26, amp)
    for k in ("upper_arm.L", "forearm.L", "upper_arm.R", "forearm.R", "spine.003", "spine.002"):
        dirs[k] = GUARD[k]
    dirs.update(look_at(rig, monster_head(f), f))
    poser.pose(f, dirs)
    y += BACK_SPEED * amp
    key(rig, f, loc=(RX, y, 0.0), interp="LINEAR")
TRIP_Y = y

# ------------------------------------------------------------ 2. the trip and the fall
# the trailing foot catches the plank: that leg stays hooked as the body keeps
# going back, the arms windmill, and he goes over onto his back with a bounce
LIE_BACK = math.radians(-82)
key(rig, F_TRIP + 4, loc=(RX, TRIP_Y + 0.5, 0.0))
key_rot(F_TRIP + 4, math.radians(-22), 0, math.radians(360))
key(rig, F_TRIP + 9, loc=(RX, TRIP_Y + 1.3, 0.0))
key_rot(F_TRIP + 9, math.radians(-52), 0, math.radians(360))
key(rig, F_LAND, loc=(RX, TRIP_Y + 2.2, 0.0))
key_rot(F_LAND, LIE_BACK, 0, math.radians(360))
key(rig, F_LAND + 3, loc=(RX, TRIP_Y + 2.4, 0.0), scale=(1.06, 1.0, 0.94))          # the bounce
key(rig, F_LAND + 7, loc=(RX, TRIP_Y + 2.5, 0.0), scale=(1, 1, 1))
key_rot(F_LAND + 7, LIE_BACK, 0, math.radians(360))
LIE_Y = TRIP_Y + 2.5
HOOKED = {"thigh.R": (0.05, -0.3, -0.95), "shin.R": (0.05, 0.75, -0.65)}                 # the caught leg folds back
poser.pose(F_TRIP + 3, {**GUARD, **HOOKED, "thigh.L": (-0.05, 0.25, -0.97), "shin.L": (-0.05, 0.2, -0.98), **look_at(rig, monster_head(F_TRIP + 3), F_TRIP + 3)})
poser.pose(F_TRIP + 8, {"upper_arm.L": (-0.75, -0.6, 0.3), "forearm.L": (-0.6, -0.5, 0.62), "upper_arm.R": (0.75, -0.6, 0.3), "forearm.R": (0.6, -0.5, 0.62),
                        "thigh.R": (0.05, -0.6, -0.8), "shin.R": (0.05, 0.4, -0.9), "thigh.L": (-0.05, -0.2, -0.98), "shin.L": (-0.05, 0.3, -0.95),
                        "spine.003": (0, 0.15, 0.99), "head": (0, -0.1, 0.99)})
FLAT_BACK = {"upper_arm.L": (-0.85, -0.3, -0.4), "forearm.L": (-0.9, -0.25, -0.35), "upper_arm.R": (0.85, -0.3, -0.4), "forearm.R": (0.9, -0.25, -0.35),
             "thigh.L": (-0.08, -0.55, -0.83), "shin.L": (-0.05, 0.35, -0.94), "thigh.R": (0.08, -0.6, -0.8), "shin.R": (0.05, 0.4, -0.92),
             "spine.003": (0, 0.05, 1.0), "head": (0, 0.05, 1.0)}
poser.pose(F_LAND, FLAT_BACK)
poser.pose(F_LAND + 7, FLAT_BACK)

# ------------------------------------------------------------ 3. props up and scoots back
# elbows under him, head up to look at the monster, then two pushes back on
# his bottom with the heels digging in
PROP = {"upper_arm.L": (-0.5, 0.55, -0.67), "forearm.L": (-0.35, -0.3, 0.88), "upper_arm.R": (0.5, 0.55, -0.67), "forearm.R": (0.35, -0.3, 0.88),
        "thigh.L": (-0.08, -0.7, -0.7), "shin.L": (-0.05, 0.45, -0.9), "thigh.R": (0.08, -0.72, -0.68), "shin.R": (0.05, 0.5, -0.87),
        "spine.001": (0, -0.1, 1.0), "spine.002": (0, -0.3, 0.95), "spine.003": (0, -0.45, 0.9)}
PROP_ROT = math.radians(-66)
key(rig, F_PROP + 8, loc=(RX, LIE_Y, 0.0))
key_rot(F_PROP + 8, PROP_ROT, 0, math.radians(360))
poser.pose(F_PROP + 8, {**PROP, **look_at(rig, monster_head(F_PROP + 8), F_PROP + 8)})
yy = LIE_Y
for push in range(2):
    fa = F_SCOOT + push * 13
    fb = fa + 7
    fc = fa + 13
    # heels dig in and the legs straighten, shoving the body back
    poser.pose(fa, {**PROP, "thigh.L": (-0.08, -0.8, -0.6), "shin.L": (-0.05, 0.5, -0.87), "thigh.R": (0.08, -0.82, -0.57), "shin.R": (0.05, 0.55, -0.83),
                    **look_at(rig, monster_head(fa), fa)})
    poser.pose(fb, {**PROP, "thigh.L": (-0.08, -0.45, -0.9), "shin.L": (-0.05, 0.1, -1.0), "thigh.R": (0.08, -0.5, -0.87), "shin.R": (0.05, 0.15, -0.99),
                    **look_at(rig, monster_head(fb), fb)})
    key(rig, fa, loc=(RX, yy, 0.0))
    yy += 1.1
    key(rig, fb, loc=(RX, yy, 0.0))
    key(rig, fc, loc=(RX, yy, 0.0))
    poser.pose(fc, {**PROP, **look_at(rig, monster_head(fc), fc)})
SCOOT_Y = yy
key(rig, F_END, loc=(RX, SCOOT_Y, 0.0))
key_rot(F_END, PROP_ROT, 0, math.radians(360))
# cowering as the claw comes down: arms cross over the face, legs pull up
COWER = {**PROP, "upper_arm.L": (-0.55, -0.7, 0.45), "forearm.L": (0.35, -0.45, 0.82), "upper_arm.R": (0.55, -0.7, 0.45), "forearm.R": (-0.35, -0.45, 0.82),
         "thigh.L": (-0.1, -0.85, -0.5), "shin.L": (-0.05, 0.6, -0.8), "thigh.R": (0.1, -0.87, -0.48), "shin.R": (0.05, 0.62, -0.78)}
for f in range(F_SCOOT_END + 1, F_END + 1):
    u = min(1.0, max(0.0, (f - F_REACH) / 12))
    p = {k: tuple(Vector(PROP[k]).lerp(Vector(COWER[k]), u * u * (3 - 2 * u))) for k in PROP}
    p.update(look_at(rig, monster_head(f), f, blend=1.0 - 0.5 * u))
    if f >= F_NEAR:                                       # a tremble
        s = 0.02 * math.sin(2 * math.pi * f / 3.0)
        p["head"] = (p["head"][0] + s, p["head"][1], p["head"][2])
    poser.pose(f, p)
ground_clamp(rig, body, range(F_BACK, F_END + 1))

# ------------------------------------------------------------ the monster comes on
# a heavy lumbering walk: short thick legs, the body rolling side to side and
# sinking on each plant, arms hanging hunched, jaw open, eyes on Yellow
STOP_MY = SCOOT_Y - 5.4                                  # stops with its reach just short of him
MENACE = {"spine.001": (0, -0.08, 1.0), "spine.002": (0, -0.3, 0.95), "spine.003": (0, -0.4, 0.92), "neck": (0, -0.55, 0.83), "head": (0, -0.6, 0.8),
          "jaw": (0, -0.85, -0.5), "upper_arm.L": (-0.6, -0.55, -0.55), "forearm.L": (-0.35, -0.7, -0.6),
          "upper_arm.R": (0.6, -0.55, -0.55), "forearm.R": (0.35, -0.7, -0.6),
          "tail.001": (0, 0.85, -0.5), "tail.002": (0, 0.9, -0.42)}
mrig.rotation_mode = "XYZ"
key(mrig, F0 + 1, loc=(MX, MY0, 0.25), rot=(0, 0, math.radians(180)), scale=(1, 1, 1))
walk_len = F_LOOM - F_ADV
my = MY0
for f in range(F_ADV, F_LOOM + 1):
    t = f - F_ADV
    amp = min(1.0, t / 14) * min(1.0, (F_LOOM - f) / 12)
    ease = amp * amp * (3 - 2 * amp)
    dirs = gait_dirs(t, STRIDE_M, ease)
    p = dict(MENACE)
    for k in ("thigh.L", "shin.L", "thigh.R", "shin.R"):
        p[k] = dirs[k]
    # arms swing a little with the walk, still hunched
    sw = 0.15 * math.sin(2 * math.pi * t / STRIDE_M) * ease
    p["upper_arm.L"] = (-0.6, -0.55 + sw, -0.55)
    p["upper_arm.R"] = (0.6, -0.55 - sw, -0.55)
    # the tail swings opposite the roll
    roll = 0.05 * math.sin(2 * math.pi * t / STRIDE_M) * ease
    p["tail.002"] = (-roll * 6, 0.9, -0.42)
    p["tail.003"] = (-roll * 9, 0.9, -0.35)
    p.update(look_at(mrig, yellow_chest(f), f, front=(0, -0.6, 0.8), max_up=0.6, neck=0.4))
    mposer.pose(f, p)
    speed = 0.4 * ease
    my = min(STOP_MY, my + speed)
    key(mrig, f, loc=(MX, my, 0.25), rot=(0, roll, math.radians(180)), interp="LINEAR")
# the loom: leans in over him, the right arm reaches down, claw open, then
# holds there, fingers flexing, jaw wide
key(mrig, F_END, loc=(MX, my, 0.25), rot=(0, 0, math.radians(180)))
LOOM = {**MENACE, "spine.001": (0, -0.25, 0.97), "spine.002": (0, -0.5, 0.87), "spine.003": (0, -0.6, 0.8), "neck": (0, -0.7, 0.7), "head": (0, -0.75, 0.66),
        "jaw": (0, -0.6, -0.8), "upper_arm.L": (-0.65, -0.5, -0.55), "forearm.L": (-0.4, -0.65, -0.65)}
for f in range(F_LOOM + 1, F_END + 1):
    u = min(1.0, (f - F_LOOM) / (F_REACH - F_LOOM))
    ue = u * u * (3 - 2 * u)
    p = {k: tuple(Vector(MENACE[k]).lerp(Vector(LOOM[k]), ue)) for k in MENACE}
    # the reaching arm: aim the upper arm and forearm from the shoulder toward
    # a point just above Yellow's chest, in the monster's rest space
    v = min(1.0, max(0.0, (f - F_LOOM - 6) / (F_NEAR - F_LOOM - 6)))
    ve = v * v * (3 - 2 * v)
    scene.frame_set(f)
    shoulder = mrig.matrix_world @ mrig.pose.bones["upper_arm.R"].head
    goal = yellow_chest(f) + Vector((0, 0, 1.6))
    d = (mrig.matrix_world.to_3x3().inverted() @ (goal - shoulder)).normalized()
    arm_rest = Vector(MENACE["upper_arm.R"])
    p["upper_arm.R"] = tuple(arm_rest.lerp((d + Vector((0.25, 0, -0.1))).normalized(), ve))
    p["forearm.R"] = tuple(Vector(MENACE["forearm.R"]).lerp((d + Vector((-0.1, 0, -0.25))).normalized(), ve))
    p["hand.R"] = tuple(Vector((0.1, -0.5, -0.86)).lerp((d + Vector((0, 0, -0.5))).normalized(), ve))
    if f >= F_NEAR:                                       # the claw flexes, the jaw works
        s = math.sin(2 * math.pi * (f - F_NEAR) / 10.0)
        p["hand.R"] = tuple((Vector(p["hand.R"]) + Vector((0, 0, -0.12 * s))).normalized())
        p["jaw"] = (0, -0.6 - 0.1 * s, -0.8)
    p.update(look_at(mrig, yellow_chest(f), f, front=(0, -0.75, 0.66), max_up=0.9, neck=0.45))
    mposer.pose(f, p)
ground_clamp(mrig, monster, range(F_ADV, F_END + 1), floor=0.0)

# ------------------------------------------------------------ camera
SHOTS = [
    # the trip: low, behind his feet, he comes over backwards toward the lens
    (F_TRIP - 6, F_LAND + 8, (RX + 2.2, TRIP_Y + 10.5, 2.0), (RX + 2.0, TRIP_Y + 10.0, 2.1), (RX, TRIP_Y + 0.5, 3.2), (RX, TRIP_Y + 1.8, 2.2), 28),
    # the reach: from his side, both of them, the claw coming down
    (F_LOOM + 1, F_NEAR - 4, (RX - 25.0, SCOOT_Y - 6.0, 7.5), (RX - 24.0, SCOOT_Y - 5.5, 7.0), (RX + 1.0, SCOOT_Y - 4.5, 5.5), (RX + 1.0, SCOOT_Y - 3.5, 4.5), 30),
    # the claw over him: low, from the monster's side, his face and crossed arms with the claw coming down between
    (F_NEAR - 3, F_END, (RX + 4.5, SCOOT_Y - 6.5, 2.4), (RX + 4.2, SCOOT_Y - 6.0, 2.3), (RX, SCOOT_Y + 1.2, 2.6), (RX, SCOOT_Y + 1.0, 2.8), 30),
]
for start, end, ca, cb, ta, tb, lens in SHOTS:
    key(cam, start, loc=ca, interp="LINEAR")
    key(cam, end, loc=cb, interp="LINEAR")
    key(target, start, loc=ta, interp="LINEAR")
    key(target, end, loc=tb, interp="LINEAR")
    for f in (start, end):
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)
# backing away: from his side, tracking him, the monster coming in from the left
for f in range(F0 + 1, F_TRIP - 6):
    scene.frame_set(f)
    him = rig.matrix_world.translation
    key(cam, f, loc=(RX - 16.0, him.y + 1.0, 5.2), interp="LINEAR")
    key(target, f, loc=(RX, him.y - 4.0, 4.6), interp="LINEAR")        # a little toward the monster coming in
for f in (F0 + 1, F_TRIP - 7):
    cam.data.lens = 26
    cam.data.keyframe_insert("lens", frame=f)
# the landing shake
for i, (dx, dz) in enumerate(((0.3, -0.2), (-0.25, 0.25), (0.15, -0.1), (0.0, 0.0))):
    key(cam, F_LAND + 1 + i, loc=(RX + 2.1 + dx, TRIP_Y + 10.2, 2.05 + dz), interp="LINEAR")
# from the ground behind his head: the monster comes at the lens
for f in range(F_LAND + 9, F_LOOM + 1):
    scene.frame_set(f)
    him = rig.matrix_world.translation
    key(cam, f, loc=(RX + 0.6, him.y + 9.5, 3.6), interp="LINEAR")     # behind and above his head (his head lies toward +Y)
    key(target, f, loc=tuple(monster_head(f) - Vector((0, 0, 3.0))), interp="LINEAR")
    # each stomp thumps the camera
    since = (f - (F_ADV + 6)) % (STRIDE_M // 2)
    if f < F_LOOM and since < 3:
        key(cam, f, loc=(RX + 0.6, him.y + 9.5, 3.6 - 0.12 * (1 - since / 3)), interp="LINEAR")
for f in (F_LAND + 9, F_LOOM):
    cam.data.lens = 24
    cam.data.keyframe_insert("lens", frame=f)

# ------------------------------------------------------------ output and checks
scene.frame_end = F_END
scene.frame_set(1)
bad = floor_violations(body, range(F_BACK, F_END + 1))
mbad = floor_violations(monster, range(F_ADV, F_END + 1), tolerance=0.3)
spikes = motion_spikes(rig, range(F0 + 2, F_END), 0.6, bone="head")
print("beat 5 keyed", F0 + 1, "->", F_END, "| trip y %.1f, lie y %.1f, monster stops y %.1f" % (TRIP_Y, LIE_Y, my),
      "| below floor:", bad or "none", "| monster below:", mbad or "none", "| head jerks:", spikes or "none", "| cues:", SOUND_CUES)
