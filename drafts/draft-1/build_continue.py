"""Straight after the opening: Yellow looks down at his hands, says "Where am
I?" (burned in by render_episode.py), walks off a little way, hears a whistle
and looks up to see crates dropping out of the sky, turns and bolts while they
land behind him, slows, turns back and sees they have landed. Five camera
set-ups cut together, then a crane up to a high shot for the run.

Run inside Blender with slimsico.blend open, after build_opening.py and
build_props.py. Re-running replaces everything after frame 150.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(bpy.data.filepath))
from rig_utils import Poser, floor_violations, ground_clamp, key, motion_spikes, set_interpolation, sym  # noqa: E402

scene = bpy.context.scene
rig = bpy.data.objects["CharacterRig"]
body = bpy.data.objects["Character"]
cam = bpy.data.objects["Camera"]
crate1 = bpy.data.objects["Crate1"]
crate2 = bpy.data.objects["Crate2"]

FPS = 24
F_HANDS, F_LOOK, F_WIDE, F_WALK, F_CRATES = 151, 201, 241, 291, 381
RUN_SPEED = 0.42                               # studs per frame
RUN_STRIDE = 14                                # frames per run cycle
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
# Head moves are kept few and slow: one look down at the hands, one look
# left, one look right, one return to centre.
HEAD_DOWN = {"head": (0, -0.82, 0.57), "neck": (0, -0.3, 0.95)}
HEAD_LEFT = {"head": (-0.55, -0.3, 0.78), "neck": (-0.15, -0.05, 0.99)}
HEAD_RIGHT = {"head": (0.55, -0.3, 0.78), "neck": (0.15, -0.05, 0.99)}
poser.pose(F_HANDS + 14, sym(arm=(-0.35, -0.72, -0.6), fore=(-0.1, -0.35, 0.93), **HEAD_DOWN))
poser.pose(F_HANDS + 30, sym(arm=(-0.38, -0.7, -0.62), fore=(-0.05, -0.4, 0.92), **HEAD_DOWN))   # turns them over
poser.pose(F_LOOK - 1, sym(arm=(-0.42, -0.55, -0.72), fore=(-0.2, -0.45, 0.87), **HEAD_DOWN))

# ------------------------------------------------------------ 2. looks around (close-up)
# he lifts his head from his hands and holds it straight ahead; no looking about
poser.pose(F_LOOK + 10, sym(arm=(-0.45, -0.3, -0.85), fore=(-0.4, -0.35, -0.85), **{"head": (0, -0.2, 0.98)}))
poser.pose(F_WIDE - 1, {"head": (0, -0.2, 0.98)})

# ------------------------------------------------------------ 3. wide: "Where am I?"
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
    dirs["head"] = (0, -0.2, 0.98)                       # steady; no bobbing head
    poser.pose(f, dirs)
    # keep the root moving forward at a steady pace
    key(rig, f, loc=(0, STAND[1] - WALK_SPEED * t, 0), interp="LINEAR")
ground_clamp(rig, body, range(F_WALK, F_CRATES + 4))

# ------------------------------------------------------------ 5. hears something, looks up, runs
# Frames (relative to F_CRATES): the whistle starts at +6 as crate 1 begins to
# fall; he startles, finds it in the sky and tracks it with his head, then
# turns and bolts. The crates land behind him while he runs.
F_WHISTLE = F_CRATES + 6
F_LOOKUP = F_CRATES + 12
F_TURN = F_CRATES + 26
F_RUN = F_TURN + 14                    # a 14-frame spin so it doesn't snap
F_SLOW = F_RUN + 58
F_STOP = F_SLOW + 22
F_TURN_BACK = F_STOP + 4
F_SEE = F_TURN_BACK + 16
F_END = F_SEE + 40
HEAD_FRONT = {"head": (0, -0.25, 0.97)}

poser.pose(F_CRATES, {"head": (0, -0.2, 0.98)})
poser.pose(F_WHISTLE + 3, {"head": (0.12, -0.25, 0.96), "neck": (0.05, -0.05, 0.99)})   # ear cocked
DROP_FROM, FALL = 30.0, 30      # crates: start height and frames of fall
CRATE1_START, CRATE2_START = F_WHISTLE, F_WHISTLE + 10


def crate_height(start, frame, rest_z):
    t = max(0, frame - start) / FPS
    g = 2 * (DROP_FROM - rest_z) / (FALL / FPS) ** 2
    return max(rest_z, DROP_FROM - 0.5 * g * t * t)


def look_at(target, frame, blend=1.0, max_up=0.75):
    """Head posed so his FACE points at a world point. The face is on the
    head's -Y side and the head bone runs up +Z, so the rotation that carries
    the face normal onto the target direction is applied to the bone axis.
    Works while the rig is unrotated (facing -Y); pitch is limited."""
    scene.frame_set(frame)
    head = rig.matrix_world @ rig.pose.bones["head"].head
    d = (Vector(target) - head).normalized()
    d.z = max(-max_up, min(d.z, max_up))
    d.normalize()
    swing = Vector((0, -1, 0)).rotation_difference(d)
    axis = swing @ Vector((0, 0, 1))
    front = Vector(HEAD_FRONT["head"])
    return {"head": tuple(front.lerp(axis, blend)),
            "neck": tuple(Vector((0, 0, 1)).lerp(axis, 0.3 * blend))}


# looks up and follows crate 1 down the sky until he turns to run
c1x, c1y, c1z = crate1["rest"]
for f in range(F_LOOKUP, F_TURN + 1):
    blend = min(1.0, (f - F_LOOKUP) / 6)
    target = (c1x, c1y, crate_height(CRATE1_START, f, c1z) + 2.0)
    poser.pose(f, look_at(target, f, blend))

# ------------------------------------------------------------ 6. the run, slow down, turn, see the crates
key(rig, F_TURN, loc=(0, WALK_END_Y, 0), rot=(0, 0, 0))
key(rig, F_RUN, rot=(math.radians(12), 0, math.pi))                       # spun round, leaning in
key(rig, F_SLOW, rot=(math.radians(12), 0, math.pi))
key(rig, F_STOP, rot=(math.radians(2), 0, math.pi))
key(rig, F_TURN_BACK + 12, rot=(0, 0, math.radians(6)))                   # turns back, slight overshoot
key(rig, F_SEE + 6, rot=(0, 0, 0))
key(rig, F_END, rot=(0, 0, 0))

y = WALK_END_Y
for f in range(F_RUN, F_STOP + 1):
    t = f - F_RUN
    if f < F_SLOW:
        amp = min(1.0, t / 10)
    else:
        amp = max(0.0, 1.0 - (f - F_SLOW) / (F_STOP - F_SLOW))
    ease = amp * amp * (3 - 2 * amp)                     # smooth ramps in and out
    phase = 2 * math.pi * t / RUN_STRIDE
    dirs = {}
    for side, ph in (("L", phase), ("R", phase + math.pi)):
        swing = 0.7 * math.sin(ph) * ease
        bend = 0.9 * max(0.0, math.cos(ph)) * ease
        sx = -0.03 if side == "L" else 0.03
        dirs["thigh." + side] = (sx, -swing, -1.0)
        dirs["shin." + side] = (sx, -swing + bend, -1.0)
        # arms swing opposite to the legs, elbows bent: forearm rises as the
        # arm comes forward and drops as it goes back
        s = -0.55 * math.sin(ph) * ease
        ax = -0.38 if side == "L" else 0.38
        dirs["upper_arm." + side] = (ax, s, -0.8)
        dirs["forearm." + side] = (ax * 0.7, -0.45 - 0.3 * ease, -0.9 - 1.1 * s)
    dirs["head"] = HEAD_FRONT["head"]
    dirs["spine.003"] = (0, -0.06 * ease, 0.99)
    poser.pose(f, dirs)
    y += RUN_SPEED * ease
    key(rig, f, loc=(0, y, 0), interp="LINEAR")
STOP_Y = y
ground_clamp(rig, body, range(F_RUN, F_STOP + 4))

# he turns back with his arms settling, then looks straight at the crates
poser.pose(F_TURN_BACK, sym(arm=(-0.45, -0.15, -0.87), fore=(-0.4, -0.25, -0.86), **HEAD_FRONT))
mid = ((crate1["rest"][0] + crate2["rest"][0]) / 2, (crate1["rest"][1] + crate2["rest"][1]) / 2, 4.0)
for f in (F_SEE, F_SEE + 12, F_END):
    poser.pose(f, dict(look_at(mid, f), **sym(arm=(-0.42, -0.1, -0.9), fore=(-0.38, -0.15, -0.9))))

# ------------------------------------------------------------ the crates fall


def drop(crate, start, tilt):
    """Gravity drop from the sky onto the crate's stored rest spot, with a
    small bounce and a rocking settle."""
    x, y0, rest_z = crate["rest"]                    # set by build_props.py
    key(crate, 1, loc=(x, y0, -100), rot=(0, 0, 0), interp="CONSTANT")      # parked under the floor
    for i in range(FALL + 1):
        key(crate, start + i, loc=(x, y0, crate_height(start, start + i, rest_z)), interp="LINEAR")
    land = start + FALL
    key(crate, land, rot=(0, 0, 0))
    key(crate, land + 3, loc=(x, y0, rest_z + 0.55), rot=(math.radians(tilt), math.radians(-tilt * 0.6), 0))
    key(crate, land + 7, loc=(x, y0, rest_z), rot=(math.radians(-tilt * 0.3), 0, 0))
    key(crate, land + 11, loc=(x, y0, rest_z), rot=(0, 0, 0))


drop(crate1, CRATE1_START, 7)
drop(crate2, CRATE2_START, -6)
CRATE1_LAND, CRATE2_LAND = CRATE1_START + FALL, CRATE2_START + FALL

# ------------------------------------------------------------ camera cuts
# Each shot: a start key and an end key, linear, so the jump to the next
# shot's start is a clean cut. The Track To constraints keep him framed.
SHOTS = [
    (F_HANDS, F_LOOK - 1, (-6.0, -12.0, 8.8), (-5.4, -11.0, 8.6)),          # front 3/4 from above his eyeline, slow push in
    (F_LOOK, F_WIDE - 1, (-2.5, -8.5, 6.6), (-2.1, -8.0, 6.8)),             # close-up, low
    (F_WIDE, F_WALK - 1, (10.0, 8.0, 9.0), (9.0, 7.0, 8.5)),                # wide, from behind-right
    (F_CRATES, F_TURN, (-3.0, -44.0, 10.0), (-2.5, -43.0, 9.6)),            # wide front, sky above him
]
for start, end, a, b in SHOTS:
    key(cam, start, loc=a, interp="LINEAR")
    key(cam, end, loc=b, interp="LINEAR")
# the look-up: cut to a low camera just behind his shoulder, tilted up and
# tracking the first crate as it falls, then cut back to the wide shot
F_UPSHOT, F_UPSHOT_END = F_LOOKUP + 3, F_TURN - 1
wide_a, wide_b = SHOTS[-1][2], SHOTS[-1][3]
u = (F_UPSHOT - 1 - F_CRATES) / (F_TURN - F_CRATES)
key(cam, F_UPSHOT - 1, loc=tuple(a + (b - a) * u for a, b in zip(wide_a, wide_b)), interp="LINEAR")
key(cam, F_UPSHOT, loc=(2.0, WALK_END_Y + 5.2, 5.6), interp="LINEAR")
key(cam, F_UPSHOT_END, loc=(1.8, WALK_END_Y + 4.9, 5.8), interp="LINEAR")
for f in range(F_WALK, F_CRATES):                                           # side tracking shot, full body
    key(cam, f, loc=(-19.0, STAND[1] - WALK_SPEED * (f - F_WALK) - 1.0, 4.5), interp="LINEAR")
# the crane: as he turns to run the camera rises to a high shot, holds while
# he runs, then sinks forward over the crates toward him as he turns back
key(cam, F_RUN + 4, loc=(-2.5, -43.0, 9.6))
key(cam, F_RUN + 34, loc=(-3.0, -50.0, 30.0))
key(cam, F_STOP, loc=(-3.0, -50.0, 30.0))
key(cam, F_END, loc=(-2.0, -14.0, 14.0))

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
# A third constraint tracks the falling crate for the look-up shot.
track_crate = cam.constraints.get("TrackCrate")
if track_crate is None:
    track_crate = cam.constraints.new("TRACK_TO")
    track_crate.name = "TrackCrate"
    track_crate.target = crate1
    track_crate.track_axis = "TRACK_NEGATIVE_Z"
    track_crate.up_axis = "UP_Y"
PATHS = tuple('constraints["%s"].influence' % n for n in ("TrackHead", "TrackChest", "TrackCrate"))
for frame, (head_on, chest_on, crate_on) in ((1, (1, 0, 0)), (F_WALK, (0, 1, 0)), (F_CRATES, (1, 0, 0)),
                                             (F_UPSHOT, (0, 0, 1)), (F_UPSHOT_END + 1, (1, 0, 0))):
    scene.frame_set(frame)
    track_head.influence = head_on
    track_chest.influence = chest_on
    track_crate.influence = crate_on
    for path in PATHS:
        cam.keyframe_insert(path, frame=frame)
    set_interpolation(cam, frame, "CONSTANT", PATHS)


# ------------------------------------------------------------ output
scene.frame_end = F_END
scene.render.filepath = "//renders/episode_raw.mp4"
scene.frame_set(1)
bad = floor_violations(body, range(F_HANDS, F_END + 1))
spikes = motion_spikes(rig, range(F_HANDS + 1, F_END), 0.45, bone="head")
print("continuation keyed:", F_HANDS, "->", F_END, "| below floor:", bad or "none", "| head jerks:", spikes or "none")
print("sound cues (frames): splat 46, whistle", CRATE1_START, CRATE2_START, "thud", CRATE1_LAND, CRATE2_LAND)
