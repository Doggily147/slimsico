"""Shared helpers for keying the character rig from the build scripts.

Import from a script that runs inside Blender:

    import sys, os; sys.path.insert(0, os.path.dirname(bpy.data.filepath))
    from rig_utils import key, Poser, ground_clamp
"""
import bpy
from mathutils import Vector

def fcurves(obj):
    """All f-curves animating `obj` (Blender 5 layered actions)."""
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return []
    curves = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(ad.action_slot)
            if bag is not None:
                curves.extend(bag.fcurves)
    return curves


def set_interpolation(obj, frame, interp, data_paths=None):
    """Set the interpolation of every key of `obj` sitting on `frame`."""
    for fc in fcurves(obj):
        if data_paths is not None and fc.data_path not in data_paths:
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = interp


def key(obj, frame, loc=None, rot=None, scale=None, interp="BEZIER"):
    """Key the given channels of `obj` at `frame` with `interp` interpolation."""
    bpy.context.scene.frame_set(frame)
    paths = []
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
        paths.append("location")
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)
        paths.append("rotation_euler")
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)
        paths.append("scale")
    if interp != "BEZIER":
        set_interpolation(obj, frame, interp, paths)


def mirror(d):
    return (-d[0], d[1], d[2])


def sym(arm=None, fore=None, thigh=None, shin=None, **rest):
    """Pose dict from left-side limb directions, mirrored to the right side."""
    d = dict(rest)
    for name, val in (("upper_arm", arm), ("forearm", fore), ("thigh", thigh), ("shin", shin)):
        if val is not None:
            d[name + ".L"] = val
            d[name + ".R"] = mirror(val)
    return d


class Poser:
    """Aims bones along directions given in the rig's rest space (+Z up the
    body, -Y his front, +X his right), keying parents before children so each
    aim accounts for the posed parent above it. Unlisted bones go to rest."""

    ORDER = ["spine.001", "spine.002", "spine.003", "neck", "head",
             "upper_arm.L", "forearm.L", "upper_arm.R", "forearm.R",
             "thigh.L", "shin.L", "thigh.R", "shin.R"]

    def __init__(self, rig, order=None):
        self.rig = rig
        self.order = order or self.ORDER
        self.rest = {n: (rig.data.bones[n].tail_local - rig.data.bones[n].head_local).normalized()
                     for n in self.order}

    def pose(self, frame, dirs):
        bpy.context.scene.frame_set(frame)
        for name in self.order:
            pb = self.rig.pose.bones[name]
            pb.rotation_quaternion = (1, 0, 0, 0)
            bpy.context.view_layer.update()
            current = pb.matrix.to_quaternion()
            target = Vector(dirs.get(name, self.rest[name])).normalized()
            swing = pb.y_axis.normalized().rotation_difference(target)
            pb.rotation_quaternion = current.inverted() @ swing @ current
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            bpy.context.view_layer.update()


def lowest_point(body, frame):
    """World z of the lowest vertex of the evaluated body mesh at `frame`."""
    bpy.context.scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    mw = ev.matrix_world
    return min((mw @ v.co).z for v in ev.data.vertices)


def ground_clamp(rig, body, frames, floor=0.0, smooth=1):
    """Re-key the rig's z on each frame so the body's lowest point sits on the
    floor. Used for walking and running: the stance foot always touches and
    the body bobs naturally. The corrections are averaged over neighbouring
    frames (`smooth` each side) so the bob is smooth rather than jittery."""
    frames = list(frames)
    heights = []
    for f in frames:
        bpy.context.scene.frame_set(f)
        low = lowest_point(body, f)
        heights.append(rig.location.z + (floor - low))
    if smooth:
        padded = [heights[0]] * smooth + heights + [heights[-1]] * smooth
        averaged = [sum(padded[i:i + 2 * smooth + 1]) / (2 * smooth + 1) for i in range(len(heights))]
        # smooth, but never lower than the raw contact height: no dipping
        heights = [max(a, h) for a, h in zip(averaged, heights)]
    for f, z in zip(frames, heights):
        bpy.context.scene.frame_set(f)
        key(rig, f, loc=(rig.location.x, rig.location.y, z), interp="LINEAR")


def floor_violations(body, frames, tolerance=0.03):
    """Frames where the body dips below the floor, with the depth."""
    return {f: round(z, 2) for f in frames if (z := lowest_point(body, f)) < -tolerance}


def gait_dirs(t, stride, ease, run=False):
    """Bone directions for one frame of a walk (or run) cycle in the rig's
    rest space: legs swing with a knee bend on the forward swing, arms swing
    opposite with bent elbows. `ease` in 0..1 scales the whole thing."""
    import math
    phase = 2 * math.pi * t / stride
    leg_swing, knee, arm_swing = (0.7, 0.9, 0.55) if run else (0.42, 0.55, 0.4)
    dirs = {}
    for side, ph in (("L", phase), ("R", phase + math.pi)):
        swing = leg_swing * math.sin(ph) * ease
        bend = knee * max(0.0, math.cos(ph)) * ease
        sx = -0.03 if side == "L" else 0.03
        dirs["thigh." + side] = (sx, -swing, -1.0)
        dirs["shin." + side] = (sx, -swing + bend, -1.0)
        s = -arm_swing * math.sin(ph) * ease
        ax = -0.38 if side == "L" else 0.38
        if run:
            dirs["upper_arm." + side] = (ax, s, -0.8)
            dirs["forearm." + side] = (ax * 0.7, -0.45 - 0.3 * ease, -0.9 - 1.1 * s)
        else:
            dirs["upper_arm." + side] = (ax, s, -0.88)
            dirs["forearm." + side] = (ax * 0.9, s - 0.2 * ease, -0.85)
    return dirs


def clone_character(src_body, src_rig, name, colour, extras=("EyeL", "EyeR", "CatchlightL", "CatchlightR", "Mouth"),
                    collection=None):
    """Duplicate the rigged character (mesh, armature, face parts) as a new
    independent character with its own body colour. Returns (body, rig)."""
    scene = bpy.context.scene
    col = collection or scene.collection
    rig = src_rig.copy()
    rig.data = src_rig.data.copy()
    rig.name = name + "Rig"
    rig.animation_data_clear()
    # the source rig may be mid-animation; the clone starts at the origin, at rest
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    col.objects.link(rig)

    body = src_body.copy()
    body.data = src_body.data.copy()
    body.name = name
    body.animation_data_clear()
    body.parent = rig
    body.matrix_parent_inverse.identity()
    body.matrix_basis.identity()
    for m in body.modifiers:
        if m.type == "ARMATURE":
            m.object = rig
    mat = src_body.data.materials[0].copy()
    mat.name = name + "Skin"
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*colour, 1)
    mat.diffuse_color = (*colour, 1)
    body.data.materials.clear()
    body.data.materials.append(mat)
    col.objects.link(body)

    made = {src_body.name: body}
    for extra in extras:
        src = bpy.data.objects.get(extra)
        if src is None:
            continue
        o = src.copy()
        if o.data is not None:
            o.data = o.data.copy()
        o.name = name + "_" + extra
        o.animation_data_clear()
        col.objects.link(o)
        made[extra] = o
    # re-parent the copies to the new rig / body / eyes
    for extra, o in made.items():
        if extra == src_body.name:
            continue
        src = bpy.data.objects[extra]
        parent = src.parent
        if parent is src_rig:
            o.parent = rig
            o.parent_type = src.parent_type
            o.parent_bone = src.parent_bone
        elif parent is not None and parent.name in made:
            o.parent = made[parent.name]
        o.matrix_parent_inverse = src.matrix_parent_inverse.copy()
    return body, rig


def motion_spikes(obj, frames, threshold, bone=None):
    """Frames where `obj` (or one of its pose bones) accelerates harder than
    `threshold` studs per frame squared: a quick way to find jerks."""
    positions = []
    for f in frames:
        bpy.context.scene.frame_set(f)
        if bone is not None:
            positions.append(obj.matrix_world @ obj.pose.bones[bone].head)
        else:
            positions.append(obj.matrix_world.translation.copy())
    spikes = {}
    for i in range(1, len(positions) - 1):
        accel = (positions[i + 1] - 2 * positions[i] + positions[i - 1]).length
        if accel > threshold:
            spikes[frames[i]] = round(accel, 2)
    return spikes
