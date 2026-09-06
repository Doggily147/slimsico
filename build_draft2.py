"""Draft 2. Beat 1: the baseplate, peaceful, under the sky. A sound from above.
The camera tilts up, rises, tightens its lens, and finds Yellow far up in the
sky, rolling through the air as he falls. Beat 2: the fall accelerates, the
camera follows him down, and he belly-flops onto the plate.

Frames 1-240 at 24 fps. Later beats extend this timeline.

Run inside Blender with slimsico.blend open after build_character.py.
Re-running replaces the animation. Render with render_draft2.py.
"""
import bpy
import math
import os
import sys
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, floor_violations, key, set_interpolation  # noqa: E402

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]

FPS = 24
F_START, F_SOUND, F_TILT, F_FOUND, F_LAND, F_END = 1, 60, 72, 108, 190, 240
SOUND_CUES = [("wind", 1), ("whistle", F_SOUND), ("splat", F_LAND)]      # read by render_draft2.py
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
LAND = Vector((0.0, 6.0, LIE_Z))
fall_time = (F_LAND - F_START) / FPS
V0 = 14.0                                                   # studs per second at frame 1
G = 2 * (TOP.z - LAND.z - V0 * fall_time) / fall_time ** 2
LANDING_ROT = Euler((math.radians(90), 0, 0)).to_quaternion()   # face down, head toward -Y
poser = Poser(rig)
for f in range(F_START, F_LAND + 1):
    t = (f - F_START) / FPS
    u = t / fall_time
    z = TOP.z - V0 * t - 0.5 * G * t * t
    pos = Vector((TOP.x + (LAND.x - TOP.x) * u, TOP.y + (LAND.y - TOP.y) * u, max(z, LIE_Z)))
    key(rig, f, loc=tuple(pos), interp="LINEAR")
    # tumble: end over end, speeding up with the fall, with a lazy twist
    roll = 0.10 * (f - F_START) + 0.0009 * (f - F_START) ** 2
    tumble = Euler((roll, 0.3 * math.sin(roll * 0.5), 0.6 + 0.03 * (f - F_START))).to_quaternion()
    # the last 18 frames resolve the tumble into the belly-first landing
    blend = max(0.0, (f - (F_LAND - 18)) / 18)
    q = tumble.slerp(LANDING_ROT, blend * blend * (3 - 2 * blend))
    key_quat(rig, f, q)
    # limbs flail loosely, each on its own rhythm, then spread for the splat
    dirs = {}
    for side, s, ph in (("L", -1, 0.0), ("R", 1, 1.9)):
        a = 0.5 * math.sin(2.1 * t + ph)
        dirs["upper_arm." + side] = (s * 0.75, 0.3 * math.cos(1.7 * t + ph), 0.55 + a)
        dirs["forearm." + side] = (s * 0.5, 0.25 * math.sin(2.6 * t + ph), 0.8)
        dirs["thigh." + side] = (s * 0.3, -0.35 + 0.3 * math.sin(1.5 * t + ph), -0.9)
        dirs["shin." + side] = (s * 0.1, 0.45 * max(0.0, math.sin(1.5 * t + ph + 1.0)), -0.9)
    if blend > 0:
        flat = {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
                "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
                "thigh.L": (-0.05, 0, -1), "shin.L": (0, 0, -1), "thigh.R": (0.05, 0, -1), "shin.R": (0, 0, -1)}
        for k in flat:
            dirs[k] = tuple(Vector(dirs[k]).lerp(Vector(flat[k]), blend))
    dirs["head"] = (0, -0.15, 0.99)
    poser.pose(f, dirs)

# ------------------------------------------------------------ the landing
key(rig, F_LAND, scale=(1, 1, 1))
key(rig, F_LAND + 2, loc=(LAND.x, LAND.y, LIE_Z - 0.15), scale=(1.2, 0.7, 1.12))          # splat
key(rig, F_LAND + 7, loc=(LAND.x, LAND.y - 0.5, LIE_Z + 1.0), scale=(0.94, 1.12, 0.96))    # small bounce
key(rig, F_LAND + 12, loc=(LAND.x, LAND.y - 1.0, LIE_Z), scale=(1.08, 0.86, 1.03))
key(rig, F_LAND + 20, loc=(LAND.x, LAND.y - 1.4, LIE_Z), scale=(1, 1, 1))
key(rig, F_END, loc=(LAND.x, LAND.y - 1.4, LIE_Z), scale=(1, 1, 1))
key_quat(rig, F_LAND + 20, LANDING_ROT, "BEZIER")
key_quat(rig, F_END, LANDING_ROT, "BEZIER")
poser.pose(F_LAND + 20, {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
                         "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
                         "head": (0, -0.15, 0.99)})
poser.pose(F_END, {"upper_arm.L": (-0.9, -0.2, -0.3), "forearm.L": (-0.95, -0.1, -0.25),
                   "upper_arm.R": (0.9, -0.2, -0.3), "forearm.R": (0.95, -0.1, -0.25),
                   "head": (0, -0.15, 0.99)})

# ------------------------------------------------------------ camera
# Peaceful wide shot at ground level, drifting; the tilt up to the sky; then
# it follows him all the way down so the plate rushes back into frame.
HORIZON = Vector((0.0, 80.0, 7.0))
CAM_BASE = Vector((-34.0, -40.0, 5.5))
key(cam, F_START, loc=tuple(CAM_BASE))
key(cam, F_TILT, loc=(-31.0, -39.0, 5.8))
key(cam, F_FOUND, loc=(-29.0, -38.0, 9.0))                 # rises a little as it looks up
key(cam, F_LAND - 30, loc=(-28.0, -37.5, 9.5))
key(cam, F_LAND, loc=(-28.0, -37.5, 6.5))                  # settles back down for the landing
key(cam, F_END, loc=(-27.5, -37.0, 6.0))
key(target, F_START, loc=tuple(HORIZON))
key(target, F_TILT, loc=tuple(HORIZON))
for f in range(F_TILT, F_END + 1):
    u = min(1.0, (f - F_TILT) / (F_FOUND - F_TILT))
    ease = u * u * (3 - 2 * u)
    scene.frame_set(f)
    him = rig.matrix_world.translation + Vector((0, 0, 3.0))
    key(target, f, loc=tuple(HORIZON.lerp(him, ease)), interp="LINEAR")
# impact shake: a few frames of jitter on the camera itself
for i, (dx, dz) in enumerate(((0.35, -0.25), (-0.3, 0.3), (0.2, -0.15), (-0.1, 0.1), (0.0, 0.0))):
    key(cam, F_LAND + 1 + i, loc=(-28.0 + dx, -37.5, 6.5 + dz), interp="LINEAR")
# the lens tightens as it finds him, then widens back out as he comes down
for frame, lens in ((F_TILT, 30), (F_FOUND + 10, 62), (F_LAND - 40, 55), (F_LAND - 6, 32), (F_END, 30)):
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
print("draft 2 keyed", F_START, "->", F_END, "| gravity %.1f studs/s^2" % G, "| below floor:", bad or "none",
      "| sound cues:", SOUND_CUES)
