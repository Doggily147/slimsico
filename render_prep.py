"""Run by render_draft2.py inside Blender just before rendering (not saved):
stops motion blur smearing across camera cuts. The shutter opens at the frame
instead of straddling it, and wherever the camera or its target jumps to a
new shot between two frames, the key before the jump is held constant so the
blur never blends the old shot into the new one.
"""
import bpy

scene = bpy.data.scenes["Scene"]
scene.render.motion_blur_position = "START"
scene.render.motion_blur_shutter = 0.3                       # a shorter shutter: fast hands and heaves stop ghosting
JUMP = 2.0                                       # studs in one frame: a cut, not a move


def fcurves(obj):
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(ad.action_slot)
            if bag is not None:
                out.extend(bag.fcurves)
    return out


# find every frame where the camera or its target jumps on any axis, then hold
# all location channels of both at those frames (holding one axis is not enough)
cuts = set()
objs = [bpy.data.objects.get(n) for n in ("Camera", "CamTarget")]
objs = [o for o in objs if o is not None]
for obj in objs:
    for fc in fcurves(obj):
        if fc.data_path != "location":
            continue
        pts = fc.keyframe_points
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if b.co.x - a.co.x <= 1.5 and abs(b.co.y - a.co.y) > JUMP:
                cuts.add(round(a.co.x))
held = 0
for obj in objs:
    for fc in fcurves(obj):
        if fc.data_path != "location":
            continue
        for kp in fc.keyframe_points:
            if round(kp.co.x) in cuts:
                kp.interpolation = "CONSTANT"
                held += 1
print("render prep: shutter at frame start,", len(cuts), "cuts,", held, "keys held")
