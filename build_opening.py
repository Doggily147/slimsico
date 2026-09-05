"""Opening shot: Yellow drops out of the sky, belly-flops onto the grid, lies
there a moment, pushes himself up onto hands and knees, tucks his feet under
into a crouch, stands with a relieved hop and turns to the camera. The camera
falls alongside him, settles at ground level for the landing, then dollies
round to a three-quarter view as he gets up.

Run inside Blender with slimsico.blend open after build_character.py, then
render with:

  blender -b slimsico.blend -a          -> renders/opening.mp4

Re-running replaces the animation.
"""
import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.context.scene
rig = bpy.data.objects["CharacterRig"]
cam = bpy.data.objects["Camera"]

FPS = 24
F_START, F_LAND, F_SETTLE, F_RISE = 1, 46, 60, 84
F_PUSH, F_CROUCH, F_UP, F_FACE, F_END = 100, 114, 128, 158, 192
DROP_Z = 72.0            # where he appears in the sky
LIE_Z = 0.95             # root height when flat on his belly (half the belly depth)
R90 = math.radians(90)

# ------------------------------------------------------------ bone names
# skin_armature_create names bones Bone, Bone.00, ... ; give them real names.
NAMES = {
    "Bone": "root", "Bone.00": "spine.001", "Bone.01": "spine.002", "Bone.02": "spine.003",
    "Bone.03": "neck", "Bone.04": "head.001", "Bone.05": "head", "Bone.06": "head.top",
    "Bone.07": "shoulder.L", "Bone.08": "upper_arm.L", "Bone.09": "forearm.L", "Bone.10": "hand.L",
    "Bone.15": "shoulder.R", "Bone.16": "upper_arm.R", "Bone.17": "forearm.R", "Bone.18": "hand.R",
    "Bone.11": "hip.L", "Bone.12": "thigh.L", "Bone.13": "shin.L", "Bone.14": "foot.L",
    "Bone.19": "hip.R", "Bone.20": "thigh.R", "Bone.21": "shin.R", "Bone.22": "foot.R",
}
for old, new in NAMES.items():
    b = rig.data.bones.get(old)
    if b is not None:
        b.name = new

# ------------------------------------------------------------ reset
scene.render.fps = FPS
scene.frame_start, scene.frame_end = F_START, F_END
for o in (rig, cam):
    o.animation_data_clear()
    o.rotation_mode = "XYZ"
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)
for c in list(cam.constraints):
    cam.constraints.remove(c)

# The crown, eyes and mouth must ride on the head bone, not the body object,
# or they stay behind when the head is posed. Done here at rest pose so the
# parent-inverse keeps them exactly where build_character.py placed them.
bpy.context.view_layer.update()
head_pb = rig.pose.bones["head"]
head_parent_matrix = rig.matrix_world @ head_pb.matrix @ Matrix.Translation((0, head_pb.length, 0))
for name in ("Crown", "EyeL", "EyeR", "CatchlightL", "CatchlightR", "Mouth"):
    o = bpy.data.objects.get(name)
    if o is None or o.parent is rig:
        continue
    if o.parent is not None and o.parent.name != "Character":
        continue                      # catchlights are parented to the eyes; leave them
    world = o.matrix_world.copy()
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = "head"
    o.matrix_parent_inverse = head_parent_matrix.inverted()
    o.matrix_basis = world

PREFS = bpy.context.preferences.edit


def key(obj, frame, loc=None, rot=None, scale=None, interp="BEZIER"):
    """Key the given channels at `frame`; new keys take `interp` interpolation."""
    scene.frame_set(frame)
    previous = PREFS.keyframe_new_interpolation_type
    PREFS.keyframe_new_interpolation_type = interp
    try:
        if loc is not None:
            obj.location = loc
            obj.keyframe_insert("location", frame=frame)
        if rot is not None:
            obj.rotation_euler = rot
            obj.keyframe_insert("rotation_euler", frame=frame)
        if scale is not None:
            obj.scale = scale
            obj.keyframe_insert("scale", frame=frame)
    finally:
        PREFS.keyframe_new_interpolation_type = previous


# ------------------------------------------------------------ root motion
# Gravity from DROP_Z to LIE_Z over the fall, keyed every frame so it reads
# as a real accelerating drop. He drifts in from behind and to the side.
fall_time = (F_LAND - F_START) / FPS
g = 2 * (DROP_Z - LIE_Z) / fall_time ** 2
for f in range(F_START, F_LAND + 1):
    t = (f - F_START) / FPS
    u = t / fall_time
    z = DROP_Z - 0.5 * g * t * t
    key(rig, f, loc=(4.0 * (1 - u), 9.0 * (1 - u), max(z, LIE_Z)), interp="LINEAR")
# tumble: starts leaning back, rolls forward onto his belly by the landing
key(rig, F_START, rot=(math.radians(-25), 0, math.radians(35)))
key(rig, 24, rot=(math.radians(40), math.radians(6), math.radians(15)))
key(rig, F_LAND, rot=(R90, 0, 0), scale=(1, 1, 1))

# the belly-flop: splat, a small bounce, slide to a stop
key(rig, F_LAND + 2, loc=(0, 0, LIE_Z - 0.15), scale=(1.18, 0.72, 1.10))
key(rig, F_LAND + 6, loc=(0, -0.3, LIE_Z + 0.9), scale=(0.94, 1.12, 0.96))
key(rig, F_LAND + 10, loc=(0, -0.55, LIE_Z), scale=(1.08, 0.86, 1.03))
key(rig, F_SETTLE, loc=(0, -0.6, LIE_Z), rot=(R90, 0, 0), scale=(1, 1, 1))
key(rig, F_RISE, loc=(0, -0.6, LIE_Z), rot=(R90, 0, 0), scale=(1, 1, 1))

# getting up. The root sits at the feet, so while he is on his front the body
# lies along -Y from the root. Pushing up raises the hips (root z); tucking the
# feet under then rotating upright brings him to his feet about two studs
# forward of where his hips were.
key(rig, F_PUSH, loc=(0, -0.6, 2.05), rot=(R90, 0, 0))                       # hands and knees
key(rig, F_CROUCH, loc=(0, -1.6, -0.55), rot=(math.radians(38), 0, 0))        # crouched on his feet
key(rig, F_UP - 4, loc=(0, -2.0, 0.0), rot=(math.radians(-6), 0, 0))          # overshoots upright
key(rig, F_UP, loc=(0, -2.0, 0.0), rot=(0, 0, 0))
# a relieved little hop, then turn to face the camera
key(rig, F_UP + 6, scale=(1.05, 1.05, 0.92))
key(rig, F_UP + 12, loc=(0, -2.0, 0.8), scale=(0.96, 0.96, 1.06))
key(rig, F_UP + 18, loc=(0, -2.0, 0.0), scale=(1.04, 1.04, 0.95))
key(rig, F_UP + 24, rot=(0, 0, 0), scale=(1, 1, 1))
key(rig, F_FACE, loc=(0, -2.0, 0.0), rot=(0, 0, math.radians(-22)))
key(rig, F_END, loc=(0, -2.0, 0.0), rot=(0, 0, math.radians(-22)), scale=(1, 1, 1))

# ------------------------------------------------------------ bone poses
# Directions are in the rig's own space (the character's rest frame):
# +Z up the body, -Y is his front, X to his right. Bones are keyed parent
# first so each aim accounts for the posed parent above it.
ORDER = ["spine.001", "spine.002", "spine.003", "neck", "head",
         "upper_arm.L", "forearm.L", "upper_arm.R", "forearm.R",
         "thigh.L", "shin.L", "thigh.R", "shin.R"]
REST = {n: (rig.data.bones[n].tail_local - rig.data.bones[n].head_local).normalized() for n in ORDER}


def mirror(d):
    return (-d[0], d[1], d[2])


def pose_frame(frame, dirs):
    """Key every bone in ORDER at `frame`: aimed along dirs[name], or at rest."""
    scene.frame_set(frame)
    for name in ORDER:
        pb = rig.pose.bones[name]
        pb.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        current = pb.matrix.to_quaternion()
        target = Vector(dirs.get(name, REST[name])).normalized()
        swing = pb.y_axis.normalized().rotation_difference(target)
        pb.rotation_quaternion = current.inverted() @ swing @ current
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        bpy.context.view_layer.update()


def sym(arm=None, fore=None, thigh=None, shin=None, **rest):
    """Build a pose dict from left-side limb directions, mirrored to the right."""
    d = dict(rest)
    for name, val in (("upper_arm", arm), ("forearm", fore), ("thigh", thigh), ("shin", shin)):
        if val is not None:
            d[name + ".L"] = val
            d[name + ".R"] = mirror(val)
    return d


# while he is face down: local -Y is straight down, +Y straight up, +Z runs
# along the ground toward his head, -Z toward his feet.
FLAT_ARM = (-0.9, -0.2, -0.3)             # out to the side, resting on the ground
FLAT_FORE = (-0.95, -0.1, -0.25)
POSES = {
    F_START:  sym(arm=(-0.7, 0.1, 0.7), fore=(-0.5, 0.2, 0.85), thigh=(-0.3, 0.1, -0.95)),
    20:       sym(arm=(-0.9, -0.3, 0.3), fore=(-0.95, -0.2, 0.1), thigh=(-0.35, -0.2, -0.9)),
    F_LAND:   sym(arm=FLAT_ARM, fore=FLAT_FORE),
    F_SETTLE: sym(arm=FLAT_ARM, fore=FLAT_FORE),
    F_RISE:   sym(arm=FLAT_ARM, fore=FLAT_FORE),
    # hands come in under the shoulders and straighten, back arches up, knees
    # fold under so the shins lie along the ground
    F_RISE + 6: sym(arm=(-0.5, -0.8, 0.3), fore=(-0.2, -0.95, 0.2),
                    **{"spine.002": (0, 0.2, 0.98), "spine.003": (0, 0.35, 0.94)}),
    F_PUSH:   sym(arm=(-0.25, -0.95, 0.15), fore=(-0.1, -0.98, 0.15),
                  thigh=(-0.05, -0.85, -0.5), shin=(0, 0.1, -1.0),
                  **{"spine.001": (0, 0.3, 0.95), "spine.002": (0, 0.55, 0.83),
                     "spine.003": (0, 0.7, 0.7), "neck": (0, 0.8, 0.6), "head": (0, 0.75, 0.65)}),
    # feet plant, hands leave the ground, spine straightens
    F_CROUCH: sym(arm=(-0.55, -0.7, -0.45), fore=(-0.4, -0.7, -0.6),
                  thigh=(-0.08, -0.75, -0.65), shin=(0, 0.55, -0.83),
                  **{"head": (0, -0.3, 0.95)}),
    F_UP:     sym(arm=(-0.5, -0.2, -0.85), fore=(-0.45, -0.25, -0.85)),
    F_UP + 12: sym(arm=(-0.6, -0.1, -0.6), fore=(-0.6, -0.15, -0.65)),      # lift on the hop
    F_FACE:   {"head": (0, -0.14, 0.99)},                                    # everything at rest, chin up
    F_END:    {"head": (0, -0.14, 0.99)},
}
for frame in sorted(POSES):
    pose_frame(frame, POSES[frame])

# ------------------------------------------------------------ camera
cam.data.lens = 30
cam.data.clip_end = 5000
track = cam.constraints.new("TRACK_TO")
track.target = rig
track.subtarget = "head"
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
# falls beside him, lands as he lands, then dollies round while he gets up
key(cam, F_START, loc=(-11, -15, DROP_Z + 4))
key(cam, F_LAND, loc=(-11, -15, 3.2))
key(cam, F_RISE, loc=(-11, -15, 3.2))
key(cam, F_FACE, loc=(-8.5, -23, 6.0))
key(cam, F_END, loc=(-8.0, -24, 6.0))
scene.camera = cam

# ------------------------------------------------------------ output
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 32
image_settings = scene.render.image_settings
if hasattr(image_settings, "media_type"):          # Blender 5.0+: video is its own media type
    image_settings.media_type = "VIDEO"
else:
    image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.gopsize = 12
scene.render.filepath = "//renders/opening.mp4"
scene.frame_set(F_START)
print("opening animation keyed:", F_START, "->", F_END)
