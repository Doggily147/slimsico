"""Draft 2. Beat 1: the baseplate, peaceful, under the sky. A sound from above.
The camera tilts up, rises, tightens its lens, and finds Yellow far up in the
sky, rolling through the air as he falls. Beat 2: the fall accelerates, the
camera follows him down, and he belly-flops onto the plate.

Beat 3: he gets up with his arms, rubs his forearm looking down at it,
then realises he is somewhere else and turns to take in the empty plate.

Frames 1-460 at 24 fps. Later beats extend this timeline.

Run inside Blender with slimsico.blend open after build_character.py.
Re-running replaces the animation. Render with render_draft2.py.
"""
import bpy
import math
import os
import sys
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, floor_violations, ground_clamp, key, motion_spikes, set_interpolation  # noqa: E402

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]

FPS = 24
F_START, F_SOUND, F_TILT, F_FOUND, F_LAND = 1, 60, 72, 108, 190
SOUND_CUES = [("wind", 1), ("whistle", F_SOUND), ("splat", F_LAND)]      # read by render_draft2.py
SUBTITLES = [("Where am I?", 410, 452)]                                      # read by render_draft2.py
LIE_Z = 1.12                        # root height lying on his belly (half the belly depth)

# ------------------------------------------------------------ reset
for o in (rig, cam):
    o.animation_data_clear()
for c in list(cam.constraints):
    cam.constraints.remove(c)
for pb in rig.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0)
rig.rotation_mode = "QUATERNION"
target = bpy.data.objects.get("CamTarget")
if target is None:
    target = bpy.data.objects.new("CamTarget", None)
    scene.collection.objects.link(target)
target.animation_data_clear()
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
cam.data.clip_end = 5000
if cam.data.animation_data:
    cam.data.animation_data_clear()


def key_quat(obj, frame, q, interp="LINEAR"):
    scene.frame_set(frame)
    obj.rotation_quaternion = q
    obj.keyframe_insert("rotation_quaternion", frame=frame)
    if interp != "BEZIER":
        set_interpolation(obj, frame, interp, ("rotation_quaternion",))


# ------------------------------------------------------------ the fall
# Starts far up and off to one side with a little downward speed already,
# then accelerates under gravity so the last second is fast. Lands at the
# origin, belly first.
TOP = Vector((14.0, 30.0, 165.0))
BELLY_LAND = Vector((0.0, 6.0, LIE_Z))                     # where his belly hits the plate
COM = Vector((0, 0, 4.2))                                  # centre of mass, in the rig's rest space
fall_time = (F_LAND - F_START) / FPS
V0 = 14.0                                                   # studs per second at frame 1
G = 2 * (TOP.z - BELLY_LAND.z - V0 * fall_time) / fall_time ** 2
LANDING_ROT = Euler((math.radians(90), 0, 0)).to_quaternion()   # face down, head toward -Y
ROOT_LAND = BELLY_LAND - LANDING_ROT @ COM                 # where the rig's origin ends up
poser = Poser(rig)
FLAT = {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
        "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
        "thigh.L": (-0.05, 0, -1), "shin.L": (0, 0, -1), "thigh.R": (0.05, 0, -1), "shin.R": (0, 0, -1),
        "spine.002": (0, 0, 1), "spine.003": (0, 0, 1), "head": (0, -0.15, 0.99)}


def smooth_pulse(t, period, width, phase=0.0):
    """0..1 bump that comes round every `period` seconds, `width` seconds wide."""
    x = ((t + phase) % period) / width
    return 0.0 if x >= 1.0 else math.sin(math.pi * x) ** 2


# The body tumbles about its centre of mass. The angular velocity is mostly
# end-over-end but its axis drifts and its speed surges, so he flips, twists
# and slows rather than spinning like a propeller. Integrated frame by frame.
q = Euler((0.6, 0.25, 0.7)).to_quaternion()
for f in range(F_START, F_LAND + 1):
    t = (f - F_START) / FPS
    u = t / fall_time
    z = TOP.z - V0 * t - 0.5 * G * t * t
    com_world = Vector((TOP.x + (BELLY_LAND.x - TOP.x) * u, TOP.y + (BELLY_LAND.y - TOP.y) * u, max(z, LIE_Z)))
    if f > F_START:
        surge = 0.75 + 0.5 * math.sin(0.55 * t + 0.8) ** 2          # speeds up and eases
        faster = 0.8 + 0.7 * u                                       # tumbles harder as he falls
        w = Vector((2.4 + 0.8 * math.sin(0.6 * t + 0.3),             # flips (about his width)
                    0.9 * math.sin(0.9 * t + 1.2),                   # cartwheel component
                    1.1 * math.sin(0.45 * t) + 0.4)) * surge * faster  # twist
        q = (Quaternion(w.normalized(), w.length / FPS) @ q).normalized()
    # the last 18 frames resolve the tumble into the belly-first landing
    blend = max(0.0, (f - (F_LAND - 18)) / 18)
    q_out = q.slerp(LANDING_ROT, blend * blend * (3 - 2 * blend))
    root = com_world - q_out @ COM
    key(rig, f, loc=tuple(root), interp="LINEAR")
    key_quat(rig, f, q_out)

    # body animation: arms windmill against the flip, legs kick, the spine
    # arches and curls, and now and then he tucks up into a ball
    tuck = smooth_pulse(t, 2.6, 0.7, 0.9)
    arch = 0.4 * math.sin(0.8 * t + 0.4)
    dirs = {"spine.002": (0, arch * 0.6, 0.95), "spine.003": (0, arch, 0.92),
            "head": (0.15 * math.sin(0.5 * t), -0.1 + 0.3 * math.sin(0.8 * t + 1.0), 0.95)}
    for side, s, ph in (("L", -1, 0.0), ("R", 1, 2.4)):
        a = 2.4 * t + ph
        arm = Vector((s * 0.55, 0.85 * math.sin(a), 0.85 * math.cos(a)))
        fore = Vector((s * 0.35, 0.85 * math.sin(a - 0.7), 0.85 * math.cos(a - 0.7)))
        kick = math.sin(1.9 * t + ph * 0.7)
        thigh = Vector((s * 0.15, -0.55 * kick, -0.85))
        shin = Vector((s * 0.05, -0.55 * kick + 0.6 * max(0.0, math.sin(1.9 * t + ph * 0.7 + 0.6)), -0.85))
        # the tuck pulls everything in
        arm = arm.lerp(Vector((s * 0.45, -0.75, -0.2)), tuck)
        fore = fore.lerp(Vector((s * 0.2, -0.5, 0.85)), tuck)
        thigh = thigh.lerp(Vector((s * 0.12, -0.95, -0.3)), tuck)
        shin = shin.lerp(Vector((s * 0.05, 0.25, -0.95)), tuck)
        dirs["upper_arm." + side] = tuple(arm)
        dirs["forearm." + side] = tuple(fore)
        dirs["thigh." + side] = tuple(thigh)
        dirs["shin." + side] = tuple(shin)
    if tuck > 0:
        dirs["spine.003"] = tuple(Vector(dirs["spine.003"]).lerp(Vector((0, -0.55, 0.83)), tuck))
        dirs["head"] = tuple(Vector(dirs["head"]).lerp(Vector((0, -0.6, 0.8)), tuck))
    if blend > 0:
        for k in FLAT:
            dirs[k] = tuple(Vector(dirs[k]).lerp(Vector(FLAT[k]), blend))
    poser.pose(f, dirs)

# ------------------------------------------------------------ the landing
RX, RY = ROOT_LAND.x, ROOT_LAND.y
key(rig, F_LAND, scale=(1, 1, 1))
key(rig, F_LAND + 2, loc=(RX, RY, LIE_Z - 0.15), scale=(1.2, 0.7, 1.12))          # splat
key(rig, F_LAND + 7, loc=(RX, RY - 0.5, LIE_Z + 1.0), scale=(0.94, 1.12, 0.96))    # small bounce
key(rig, F_LAND + 12, loc=(RX, RY - 1.0, LIE_Z), scale=(1.08, 0.86, 1.03))
key(rig, F_LAND + 20, loc=(RX, RY - 1.4, LIE_Z), scale=(1, 1, 1))
key(rig, 240, loc=(RX, RY - 1.4, LIE_Z), scale=(1, 1, 1))
key_quat(rig, F_LAND + 20, LANDING_ROT, "BEZIER")
key_quat(rig, 240, LANDING_ROT, "BEZIER")
poser.pose(F_LAND + 20, {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
                         "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
                         "head": (0, -0.15, 0.99)})
poser.pose(240, {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
                   "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
                   "head": (0, -0.15, 0.99)})

# ------------------------------------------------------------ beat 3: up, the arm rub, the realisation
# He pushes up with his arms (hands under the shoulders, back arching, onto
# hands and knees, feet tuck under, stands), rubs his left forearm with his
# right hand while looking down at it, then the head lifts once and holds,
# and he turns slowly to take in the empty plate. The ground clamp keeps
# whatever is lowest in contact through the whole get-up.
F_LIE, F_PUSH1, F_PUSH2, F_KNEES, F_CROUCH, F_STAND = 241, 256, 264, 276, 290, 304
F_RUB, F_REAL, F_LIFT, F_TURN, F_END = 316, 372, 384, 400, 460
LIE_Y = RY - 1.4
R90 = math.radians(90)


def key_rot(frame, x, y=0.0, z=0.0):
    key_quat(rig, frame, Euler((x, y, z)).to_quaternion(), "BEZIER")


HEAD_FRONT = {"head": (0, -0.25, 0.97)}
poser.pose(F_LIE + 8, dict(FLAT))
key(rig, F_LIE + 8, loc=(RX, LIE_Y, LIE_Z))
key_rot(F_LIE + 8, R90)
# elbows lift first, then the hands come in under the chest and push
poser.pose(F_PUSH1, {"upper_arm.L": (-0.8, 0.2, 0.2), "forearm.L": (-0.6, -0.55, 0.3),
                     "upper_arm.R": (0.8, 0.2, 0.2), "forearm.R": (0.6, -0.55, 0.3), **HEAD_FRONT})
poser.pose(F_PUSH2, {"upper_arm.L": (-0.85, -0.42, 0.25), "forearm.L": (-0.3, -0.75, 0.4),
                     "upper_arm.R": (0.85, -0.42, 0.25), "forearm.R": (0.3, -0.75, 0.4),
                     "spine.002": (0, 0.2, 0.98), "spine.003": (0, 0.35, 0.94), **HEAD_FRONT})
key(rig, F_PUSH2, loc=(RX, LIE_Y, LIE_Z + 0.9))
key_rot(F_PUSH2, R90)
# hands and knees: back arched, knees folded under, shins along the ground
poser.pose(F_KNEES, {"upper_arm.L": (-0.25, -0.95, 0.15), "forearm.L": (-0.1, -0.98, 0.15),
                     "upper_arm.R": (0.25, -0.95, 0.15), "forearm.R": (0.1, -0.98, 0.15),
                     "thigh.L": (-0.05, -0.85, -0.5), "shin.L": (0, 0.1, -1.0),
                     "thigh.R": (0.05, -0.85, -0.5), "shin.R": (0, 0.1, -1.0),
                     "spine.001": (0, 0.3, 0.95), "spine.002": (0, 0.55, 0.83), "spine.003": (0, 0.7, 0.7),
                     "neck": (0, 0.8, 0.6), "head": (0, 0.75, 0.65)})
key(rig, F_KNEES, loc=(RX, LIE_Y, LIE_Z + 1.0))
key_rot(F_KNEES, R90)
# feet plant, hands leave the ground, spine straightens into a crouch
poser.pose(F_CROUCH, {"upper_arm.L": (-0.55, -0.7, -0.45), "forearm.L": (-0.4, -0.7, -0.6),
                      "upper_arm.R": (0.55, -0.7, -0.45), "forearm.R": (0.4, -0.7, -0.6),
                      "thigh.L": (-0.08, -0.75, -0.65), "shin.L": (0, 0.55, -0.83),
                      "thigh.R": (0.08, -0.75, -0.65), "shin.R": (0, 0.55, -0.83), **HEAD_FRONT})
key(rig, F_CROUCH, loc=(RX, LIE_Y - 1.0, 0.2))
key_rot(F_CROUCH, math.radians(38))
# stands, with a small overshoot
poser.pose(F_STAND, {"upper_arm.L": (-0.5, -0.2, -0.85), "forearm.L": (-0.45, -0.25, -0.85),
                     "upper_arm.R": (0.5, -0.2, -0.85), "forearm.R": (0.45, -0.25, -0.85), **HEAD_FRONT})
key(rig, F_STAND - 6, loc=(RX, LIE_Y - 1.4, 0.0))
key_rot(F_STAND - 6, math.radians(-4))
key(rig, F_STAND, loc=(RX, LIE_Y - 1.4, 0.0))
key_rot(F_STAND, 0.0)
STAND_Y = LIE_Y - 1.4

# the rub: the right arm reaches right across the chest so the hand lands on
# the left upper arm, then slides up and down it three times while he looks
# down at it. The left arm hangs a little forward to meet the hand.
LOOK_ARM = {"head": (-0.42, -0.58, 0.7), "neck": (-0.1, -0.2, 0.97), "spine.003": (-0.1, -0.12, 0.99)}
ARM_L = {"upper_arm.L": (-0.3, -0.35, -0.88), "forearm.L": (-0.25, -0.4, -0.88)}


def rub_pose(slide):
    return {**ARM_L, "upper_arm.R": (-0.86, -0.34, -0.36 + 0.06 * slide),
            "forearm.R": (-0.88, -0.3, -0.34 - 0.32 * slide), **LOOK_ARM}


poser.pose(F_RUB, rub_pose(0.0))
for f in range(F_RUB + 6, F_REAL - 6):
    t = (f - F_RUB - 6) / FPS
    poser.pose(f, rub_pose(math.sin(2 * math.pi * t / 0.75)))
poser.pose(F_REAL, rub_pose(0.0))

# the realisation: the arms lower, the head lifts once and holds, then a slow
# turn of the whole body to take in the empty plate
poser.pose(F_LIFT, {"upper_arm.L": (-0.5, -0.25, -0.83), "forearm.L": (-0.45, -0.3, -0.84),
                    "upper_arm.R": (0.5, -0.25, -0.83), "forearm.R": (0.45, -0.3, -0.84),
                    "head": (0, -0.18, 0.98), "neck": (0, -0.05, 1.0)})
poser.pose(F_END, {"upper_arm.L": (-0.5, -0.25, -0.83), "forearm.L": (-0.45, -0.3, -0.84),
                   "upper_arm.R": (0.5, -0.25, -0.83), "forearm.R": (0.45, -0.3, -0.84),
                   "head": (0, -0.18, 0.98), "neck": (0, -0.05, 1.0)})
key(rig, F_TURN, loc=(RX, STAND_Y, 0.0))
key_rot(F_TURN, 0.0)
key(rig, F_END, loc=(RX, STAND_Y, 0.0))
key_rot(F_END, 0.0, 0.0, math.radians(55))
ground_clamp(rig, body, range(F_LIE, F_END + 1))

# ------------------------------------------------------------ camera
# Peaceful wide shot at ground level, drifting; the tilt up to the sky; then
# it follows him all the way down so the plate rushes back into frame.
HORIZON = Vector((0.0, 80.0, 7.0))
key(cam, F_START, loc=(-34.0, -40.0, 5.5))
key(cam, F_TILT, loc=(-31.0, -39.0, 5.8))
key(cam, F_FOUND, loc=(-29.0, -38.0, 9.0))                 # rises a little as it looks up
key(cam, F_LAND - 30, loc=(-28.0, -37.5, 9.5))
key(cam, F_LAND, loc=(-28.0, -37.5, 6.5))                  # settles back down for the landing
key(cam, F_LIE - 1, loc=(-27.5, -37.0, 6.0), interp="LINEAR")
key(target, F_START, loc=tuple(HORIZON))
key(target, F_TILT, loc=tuple(HORIZON))
for f in range(F_TILT, F_LIE):
    u = min(1.0, (f - F_TILT) / (F_FOUND - F_TILT))
    ease = u * u * (3 - 2 * u)
    scene.frame_set(f)
    him = rig.matrix_world.translation + Vector((0, 0, 3.0))
    key(target, f, loc=tuple(HORIZON.lerp(him, ease)), interp="LINEAR")
# impact shake: a few frames of jitter on the camera itself
for i, (dx, dz) in enumerate(((0.35, -0.25), (-0.3, 0.3), (0.2, -0.15), (-0.1, 0.1), (0.0, 0.0))):
    key(cam, F_LAND + 1 + i, loc=(-28.0 + dx, -37.5, 6.5 + dz), interp="LINEAR")
# beat 3 shots: cuts, each a start key and an end key
SHOTS = [
    (F_LIE, F_STAND + 6, (-10.0, LIE_Y - 15.0, 4.5), (-9.0, LIE_Y - 14.0, 4.8), (RX, LIE_Y - 3.0, 3.0), (RX, STAND_Y, 4.6)),   # get-up, front-left medium
    (F_STAND + 7, F_REAL + 6, (4.2, STAND_Y - 8.6, 9.4), (3.8, STAND_Y - 8.2, 9.2), (RX - 0.4, STAND_Y - 0.6, 5.7), (RX - 0.4, STAND_Y - 0.6, 5.7)),  # the rub, from above and his right
    (F_REAL + 7, F_TURN + 4, (-2.2, STAND_Y - 7.5, 7.6), (-2.0, STAND_Y - 7.2, 7.5), (RX, STAND_Y, 7.4), (RX, STAND_Y, 7.4)),   # the head lifts, close
    (F_TURN + 5, F_END, (-12.0, STAND_Y - 18.0, 8.0), (-44.0, STAND_Y - 68.0, 26.0), (RX, STAND_Y, 5.0), (RX, STAND_Y, 4.0)),   # the reveal: pulls way back
]
for start, end, ca, cb, ta, tb in SHOTS:
    key(cam, start, loc=ca, interp="LINEAR")
    key(cam, end, loc=cb, interp="LINEAR")
    key(target, start, loc=ta, interp="LINEAR")
    key(target, end, loc=tb, interp="LINEAR")
# the lens tightens as it finds him, widens back out as he comes down, and
# goes wide for the reveal
for frame, lens in ((F_TILT, 30), (F_FOUND + 10, 62), (F_LAND - 40, 55), (F_LAND - 6, 32), (F_LIE - 1, 30),
                    (F_LIE, 35), (F_TURN + 4, 40), (F_TURN + 5, 28), (F_END, 24)):
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=frame)

# ------------------------------------------------------------ output and checks
scene.frame_start, scene.frame_end = F_START, F_END
scene.render.fps = FPS
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.render.image_settings.media_type = "VIDEO"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.filepath = "//renders/draft2_raw.mp4"
scene.frame_set(1)
bad = floor_violations(body, range(F_LAND - 5, F_END + 1))
spikes = motion_spikes(rig, range(F_LIE + 1, F_END), 0.5, bone="head")
print("draft 2 keyed", F_START, "->", F_END, "| gravity %.1f studs/s^2" % G, "| below floor:", bad or "none",
      "| head jerks:", spikes or "none", "| sound cues:", SOUND_CUES)
