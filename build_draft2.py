"""Draft 2. Beat 1: the baseplate, peaceful, under the sky. A sound from above.
The camera tilts up, rises, tightens its lens, and finds Yellow far up in the
sky, rolling through the air as he falls.

Frames 1-150 at 24 fps. Later beats extend this timeline.

Run inside Blender with slimsico.blend open after build_character.py.
Re-running replaces the animation. Render with render_draft2.py.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, key, motion_spikes, set_interpolation  # noqa: E402

scene = bpy.data.scenes["Scene"]
bpy.context.window.scene = scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]

FPS = 24
F_START, F_SOUND, F_TILT, F_FOUND, F_END = 1, 60, 72, 108, 150
SOUND_CUES = [("wind", 1), ("whistle", F_SOUND)]          # read by render_draft2.py

# ------------------------------------------------------------ reset
for o in (rig, cam):
    o.animation_data_clear()
    o.rotation_mode = "XYZ"
for c in list(cam.constraints):
    cam.constraints.remove(c)
for pb in rig.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0)
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

# ------------------------------------------------------------ Yellow, far up, tumbling
# He starts high and off to one side and drifts closer as he drops. Later
# beats continue the fall; this one only ever shows him far away.
FALL_TOP = Vector((10.0, 24.0, 165.0))
FALL_END = Vector((6.0, 16.0, 95.0))
poser = Poser(rig)
for f in range(F_START, F_END + 1):
    u = (f - F_START) / (F_END - F_START)
    pos = FALL_TOP.lerp(FALL_END, u * u * 0.4 + u * 0.6)          # gently accelerating
    key(rig, f, loc=tuple(pos), interp="LINEAR")
    # a slow end-over-end roll with a lazy twist
    roll = 0.11 * (f - F_START)
    key(rig, f, rot=(roll, 0.35 * math.sin(roll * 0.5), 0.6 + 0.04 * (f - F_START)), interp="LINEAR")
    # limbs flail loosely, each on its own rhythm
    t = (f - F_START) / FPS
    dirs = {}
    for side, s, ph in (("L", -1, 0.0), ("R", 1, 1.9)):
        a = 0.5 * math.sin(2.1 * t + ph)
        dirs["upper_arm." + side] = (s * 0.75, 0.3 * math.cos(1.7 * t + ph), 0.55 + a)
        dirs["forearm." + side] = (s * 0.5, 0.25 * math.sin(2.6 * t + ph), 0.8)
        dirs["thigh." + side] = (s * 0.3, -0.35 + 0.3 * math.sin(1.5 * t + ph), -0.9)
        dirs["shin." + side] = (s * 0.1, 0.45 * max(0.0, math.sin(1.5 * t + ph + 1.0)), -0.9)
    dirs["head"] = (0, -0.15, 0.99)
    poser.pose(f, dirs)

# ------------------------------------------------------------ camera
# Peaceful wide shot at ground level, drifting; then the tilt up to the sky.
HORIZON = Vector((0.0, 80.0, 7.0))
key(cam, F_START, loc=(-34.0, -40.0, 5.5))
key(cam, F_TILT, loc=(-31.0, -39.0, 5.8))
key(cam, F_FOUND, loc=(-29.0, -38.0, 9.0))                 # rises a little as it looks up
key(cam, F_END, loc=(-28.0, -37.5, 10.0))
key(target, F_START, loc=tuple(HORIZON))
key(target, F_TILT, loc=tuple(HORIZON))
for f in range(F_TILT, F_END + 1):
    u = min(1.0, (f - F_TILT) / (F_FOUND - F_TILT))
    ease = u * u * (3 - 2 * u)
    scene.frame_set(f)
    him = rig.matrix_world.translation + Vector((0, 0, 4.5))
    key(target, f, loc=tuple(HORIZON.lerp(him, ease)), interp="LINEAR")
# the lens tightens as it finds him
cam.data.lens = 30
cam.data.keyframe_insert("lens", frame=F_TILT)
cam.data.lens = 62
cam.data.keyframe_insert("lens", frame=F_FOUND + 10)
cam.data.lens = 66
cam.data.keyframe_insert("lens", frame=F_END)

# ------------------------------------------------------------ output and checks
scene.frame_start, scene.frame_end = F_START, F_END
scene.render.fps = FPS
scene.render.image_settings.media_type = "VIDEO"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.filepath = "//renders/draft2_raw.mp4"
scene.frame_set(1)
print("draft 2 keyed", F_START, "->", F_END, "| sound cues:", SOUND_CUES)
