"""Scene 2: the camera orbits Yellow for three seconds from three different
angles (low hero shot, eye level, high looking down) while he stands and looks
around. Keyed as frames 193-264, straight after the opening shot, so the file
holds both scenes.

Run inside Blender with slimsico.blend open after build_opening.py. The
opening's own keys are left alone; this only adds keys after frame 192.
Render the three angles as separate clips (assemble_intro.py does this and
stitches them to the opening with dissolves):

  blender -b slimsico.blend -s 193 -e 216 -o //renders/orbit_a_ -a
  blender -b slimsico.blend -s 217 -e 240 -o //renders/orbit_b_ -a
  blender -b slimsico.blend -s 241 -e 264 -o //renders/orbit_c_ -a
"""
import bpy
import math
from mathutils import Vector

scene = bpy.context.scene
rig = bpy.data.objects["CharacterRig"]
cam = bpy.data.objects["Camera"]

F_A, F_B, F_C, F_END = 193, 217, 241, 264
SEGMENT = 24                                   # frames per angle (1 s at 24 fps)
CENTRE = Vector((0, -2.0, 5.0))                # where he stands after the opening
FACING = math.radians(248)                     # azimuth his face points toward

# Three orbit arcs: (start frame, radius, height, start azimuth, end azimuth).
# Azimuths are degrees around him; a decreasing pair sweeps the other way.
ARCS = [
    (F_A, 9.0, 1.6, 215, 275),      # low, sweeping across his front
    (F_B, 12.0, 6.5, 330, 268),     # eye level, from his right side round to the front
    (F_C, 10.0, 13.0, 170, 240),    # high, looking down from front-left
]

PREFS = bpy.context.preferences.edit


def key(obj, frame, loc=None, rot=None, scale=None, interp="BEZIER"):
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


# ------------------------------------------------------------ camera orbits
# Keyed every frame with linear interpolation so each arc is a steady move and
# the jump between arcs is a clean cut.
for start, radius, height, a0, a1 in ARCS:
    for i in range(SEGMENT):
        t = i / (SEGMENT - 1)
        a = math.radians(a0 + (a1 - a0) * t)
        key(cam, start + i, loc=(CENTRE.x + radius * math.cos(a), CENTRE.y + radius * math.sin(a), height),
            interp="LINEAR")

# ------------------------------------------------------------ Yellow idles
# Gentle sway, breathing, and a look left then right.
base_rot = math.radians(-22)
key(rig, F_A, rot=(0, 0, base_rot), scale=(1, 1, 1))
key(rig, F_A + 36, rot=(0, 0, base_rot + math.radians(5)))
key(rig, F_END, rot=(0, 0, base_rot), scale=(1, 1, 1))
for f in range(F_A, F_END + 1, 18):
    key(rig, f, scale=(1, 1, 1.0 if (f - F_A) // 18 % 2 == 0 else 1.015))

ORDER = ["head", "upper_arm.L", "upper_arm.R"]
REST = {n: (rig.data.bones[n].tail_local - rig.data.bones[n].head_local).normalized() for n in ORDER}


def pose_frame(frame, dirs):
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


LOOK = {
    F_A:        {"head": (0, -0.14, 0.99)},
    F_A + 12:   {"head": (-0.3, -0.2, 0.93)},         # glances left
    F_B + 6:    {"head": (0.3, -0.2, 0.93)},          # then right
    F_C:        {"head": (0, -0.25, 0.97)},           # looks up toward the high camera
    F_END:      {"head": (0, -0.14, 0.99)},
}
for frame in sorted(LOOK):
    pose_frame(frame, LOOK[frame])

scene.frame_set(1)
print("orbit keyed:", F_A, "->", F_END)
