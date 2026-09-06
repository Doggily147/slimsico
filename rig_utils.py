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


def ground_clamp(rig, body, frames, floor=0.0):
    """Re-key the rig's z on each frame so the body's lowest point sits on the
    floor. Used for walking: the stance foot always touches, and the body
    bobs naturally as the legs swing."""
    for f in frames:
        low = lowest_point(body, f)
        z = rig.location.z + (floor - low)
        key(rig, f, loc=(rig.location.x, rig.location.y, z), interp="LINEAR")


def floor_violations(body, frames, tolerance=0.03):
    """Frames where the body dips below the floor, with the depth."""
    return {f: round(z, 2) for f in frames if (z := lowest_point(body, f)) < -tolerance}
