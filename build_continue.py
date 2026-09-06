"""Frames 151-450, straight after the opening: Yellow looks down at his hands,
looks around ("Where am I?" is burned in by render_episode.py), walks off a
little way, and two big crates drop out of the sky beside him. Five camera
set-ups, cut between.

Run inside Blender with slimsico.blend open, after build_opening.py and
build_props.py. Re-running replaces everything after frame 150.
"""
import bpy
import math
import os
import sys

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, floor_violations, ground_clamp, key, set_interpolation, sym  # noqa: E402

scene = bpy.context.scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
crate1 = bpy.data.objects["Crate1"]
crate2 = bpy.data.objects["Crate2"]

FPS = 24
F_HANDS, F_LOOK, F_WIDE, F_WALK, F_CRATES, F_END = 151, 201, 241, 291, 381, 450
SUB_START, SUB_END = 250, 288          # "Where am I?" (render_episode.py reads these)
STAND = (0, -2.0, 0.0)                 # where the opening leaves him
WALK_SPEED = 0.16                      # studs per frame
STRIDE = 24                            # frames per full walk cycle
WALK_END_Y = STAND[1] - WALK_SPEED * (F_CRATES - 1 - F_WALK)


def clear_after(obj, frame):
    """Drop every key after `frame` on obj (and its pose bones for an armature)."""
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return
    action = ad.action
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(ad.action_slot)
            if bag is None:
                continue
            for fc in bag.fcurves:
                for kp in reversed(list(fc.keyframe_points)):
                    if kp.co.x > frame:
                        fc.keyframe_points.remove(kp)


for o in (rig, cam):
    clear_after(o, 150)
# constraint influence keys live on the camera too; start those from scratch
ad = cam.animation_data
if ad and ad.action:
    for layer in ad.action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(ad.action_slot)
            if bag:
                for fc in [fc for fc in bag.fcurves if fc.data_path.startswith("constraints")]:
                    bag.fcurves.remove(fc)
for crate in (crate1, crate2):
    crate.animation_data_clear()
    crate.rotation_mode = "XYZ"

poser = Poser(rig)
REST = poser.rest

# ------------------------------------------------------------ 1. hands (front 3/4)
key(rig, F_HANDS, loc=STAND, rot=(0, 0, 0), scale=(1, 1, 1))
poser.pose(F_HANDS, {})
poser.pose(F_HANDS + 14, sym(arm=(-0.35, -0.72, -0.6), fore=(-0.1, -0.35, 0.93),
                             **{"head": (0, -0.82, 0.57), "neck": (0, -0.3, 0.95)}))
poser.pose(F_HANDS + 30, sym(arm=(-0.38, -0.7, -0.62), fore=(-0.05, -0.4, 0.92),
                             **{"head": (0, -0.84, 0.55), "neck": (0, -0.3, 0.95)}))    # turns them over a touch
poser.pose(F_LOOK - 1, sym(arm=(-0.42, -0.55, -0.72), fore=(-0.2, -0.45, 0.87),
                           **{"head": (0, -0.35, 0.94)}))

# ------------------------------------------------------------ 2. looks around (close-up)
poser.pose(F_LOOK + 6, sym(arm=(-0.45, -0.3, -0.85), fore=(-0.4, -0.35, -0.85), **{"head": (0, -0.2, 0.98)}))
poser.pose(F_LOOK + 16, {"head": (-0.55, -0.3, 0.78), "neck": (-0.15, -0.05, 0.99)})     # left
poser.pose(F_LOOK + 30, {"head": (0.55, -0.3, 0.78), "neck": (0.15, -0.05, 0.99)})      # right

# ------------------------------------------------------------ 3. wide: "Where am I?"
poser.pose(F_WIDE + 8, {"head": (0.2, -0.3, 0.93)})
poser.pose(F_WIDE + 24, {"head": (-0.25, -0.4, 0.88)})                                    # glances down-left
poser.pose(F_WALK - 1, {"head": (0, -0.2, 0.98)})

# ------------------------------------------------------------ 4. the walk (side tracking)
key(rig, F_WALK, loc=STAND, rot=(0, 0, 0))
key(rig, F_WALK + 6, rot=(math.radians(4), 0, 0))
key(rig, F_CRATES - 1, loc=(0, WALK_END_Y, 0), rot=(math.radians(4), 0, 0), interp="LINEAR")
key(rig, F_CRATES + 5, rot=(0, 0, 0))
for f in range(F_WALK, F_CRATES):
    t = f - F_WALK
    phase = 2 * math.pi * t / STRIDE
    amp = min(1.0, t / 12) * min(1.0, (F_CRATES - 1 - f) / 8)
    dirs = {}
    for side, ph in (("L", phase), ("R", phase + math.pi)):
        swing = 0.42 * math.sin(ph) * amp
        bend = 0.55 * max(0.0, math.cos(ph)) * amp
        sx = -0.03 if side == "L" else 0.03
        dirs["thigh." + side] = (sx, -swing, -1.0)
        dirs["shin." + side] = (sx, -swing + bend, -1.0)
        arm = -0.4 * math.sin(ph) * amp
        ax = -0.4 if side == "L" else 0.4
        dirs["upper_arm." + side] = (ax, arm, -0.88)
        dirs["forearm." + side] = (ax * 0.9, arm - 0.2 * amp, -0.85)
    dirs["head"] = (0.12 * math.sin(phase / 2) * amp, -0.2, 0.97)
    poser.pose(f, dirs)
    # keep the root moving forward at a steady pace
    key(rig, f, loc=(0, STAND[1] - WALK_SPEED * t, 0), interp="LINEAR")
ground_clamp(rig, body, range(F_WALK, F_CRATES + 4))

# ------------------------------------------------------------ 5. the crates
poser.pose(F_CRATES, {})
poser.pose(F_CRATES + 20, {"head": (0, -0.55, 0.83), "neck": (0, -0.15, 0.99)})           # hears them, looks up
poser.pose(F_CRATES + 36, sym(arm=(-0.75, -0.3, 0.55), fore=(-0.6, -0.3, 0.75),
                              **{"head": (0, 0.12, 0.99), "spine.003": (0, 0.12, 0.99)}))   # flinch as crate 1 lands
poser.pose(F_CRATES + 52, sym(arm=(-0.5, -0.25, -0.82), fore=(-0.45, -0.3, -0.83),
                              **{"head": (-0.5, -0.35, 0.8), "neck": (-0.15, -0.05, 0.99)}))   # looks at crate 1
poser.pose(F_CRATES + 63, {"head": (0.5, -0.35, 0.8), "neck": (0.15, -0.05, 0.99)})     # then crate 2
poser.pose(F_END, {"head": (0.45, -0.4, 0.8), "neck": (0.15, -0.05, 0.99)})

DROP_FROM, FALL = 30.0, 30      # start height and frames of fall: in frame for the last half second


def drop(crate, start, tilt):
    """Gravity drop from the sky onto the crate's stored rest spot, with a
    small bounce and a rocking settle."""
    fall = FALL
    x, y, REST_Z = crate["rest"]                     # set by build_props.py
    key(crate, 1, loc=(x, y, -100), rot=(0, 0, 0), interp="CONSTANT")       # parked under the floor
    g = 2 * (DROP_FROM - REST_Z) / (fall / FPS) ** 2
    for i in range(fall + 1):
        t = i / FPS
        key(crate, start + i, loc=(x, y, max(REST_Z, DROP_FROM - 0.5 * g * t * t)), interp="LINEAR")
    land = start + fall
    key(crate, land, rot=(0, 0, 0))
    key(crate, land + 3, loc=(x, y, REST_Z + 0.55), rot=(math.radians(tilt), math.radians(-tilt * 0.6), 0))
    key(crate, land + 7, loc=(x, y, REST_Z), rot=(math.radians(-tilt * 0.3), 0, 0))
    key(crate, land + 11, loc=(x, y, REST_Z), rot=(0, 0, 0))


drop(crate1, F_CRATES + 6, 7)          # lands at F_CRATES + 36
drop(crate2, F_CRATES + 16, -6)        # lands at F_CRATES + 46

# ------------------------------------------------------------ camera cuts
# Each shot: a start key and an end key, linear, so the jump to the next
# shot's start is a clean cut. The Track To constraint keeps his head framed.
SHOTS = [
    (F_HANDS, F_LOOK - 1, (-6.0, -12.0, 8.8), (-5.4, -11.0, 8.6)),          # front 3/4 from above his eyeline, slow push in
    (F_LOOK, F_WIDE - 1, (-2.5, -8.5, 6.6), (-2.1, -8.0, 6.8)),             # close-up, low
    (F_WIDE, F_WALK - 1, (10.0, 8.0, 9.0), (9.0, 7.0, 8.5)),                # wide, from behind-right
    (F_CRATES, F_END, (-3.0, -44.0, 10.0), (-2.5, -43.0, 9.6)),             # wide front, sky above him
]
for start, end, a, b in SHOTS:
    key(cam, start, loc=a, interp="LINEAR")
    key(cam, end, loc=b, interp="LINEAR")
for f in range(F_WALK, F_CRATES):                                           # side tracking shot, full body
    key(cam, f, loc=(-19.0, STAND[1] - WALK_SPEED * (f - F_WALK) - 1.0, 4.5), interp="LINEAR")

# The opening's Track To follows his head, which crops his legs in the side
# shot. A second constraint follows his chest and takes over for the walk.
track_head = next(c for c in cam.constraints if c.type == "TRACK_TO")
track_head.name = "TrackHead"
track_chest = cam.constraints.get("TrackChest")
if track_chest is None:
    track_chest = cam.constraints.new("TRACK_TO")
    track_chest.name = "TrackChest"
    track_chest.target = rig
    track_chest.subtarget = "spine.002"
    track_chest.track_axis = "TRACK_NEGATIVE_Z"
    track_chest.up_axis = "UP_Y"
for frame, head_on in ((1, 1.0), (F_WALK, 0.0), (F_CRATES, 1.0)):
    scene.frame_set(frame)
    track_head.influence = head_on
    track_chest.influence = 1.0 - head_on
    cam.keyframe_insert('constraints["TrackHead"].influence', frame=frame)
    cam.keyframe_insert('constraints["TrackChest"].influence', frame=frame)
    set_interpolation(cam, frame, "CONSTANT",
                      ('constraints["TrackHead"].influence', 'constraints["TrackChest"].influence'))

# ------------------------------------------------------------ output
scene.frame_end = F_END
scene.render.filepath = "//renders/episode_raw.mp4"
scene.frame_set(1)
bad = floor_violations(body, range(F_HANDS, F_END + 1))
print("continuation keyed:", F_HANDS, "->", F_END, "| below floor:", bad or "none")
