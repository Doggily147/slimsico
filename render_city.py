"""Renders check views of the city to renders/city_*.png (EEVEE, 1080p,
frame 1200 so the traffic is mid-flow). Run after build_city.py:

  blender -b slimsico.blend --python render_city.py
"""
import bpy
import math
import os
import sys
from mathutils import Vector

scene = bpy.data.scenes["Scene"]
root = bpy.data.objects["City"]
cam = bpy.data.objects["CityCam"]
out_dir = os.path.join(os.path.dirname(bpy.data.filepath), "renders")
VIEWS = {                                   # name: (position, aim, lens), in the city's own space
    "gate": ((134.0, 134.0, 5.0), (70.0, 70.0, 9.0), 32),
    "aerial": ((205.0, 110.0, 120.0), (0.0, 0.0, 22.0), 28),
    "street": ((-58.0, -3.6, 2.6), (30.0, 0.0, 14.0), 26),
    "plaza_up": ((8.0, -14.0, 2.0), (-2.0, 24.0, 52.0), 24),
    "from_plate": ((330.0, 290.0, 9.0), (0.0, 0.0, 30.0), 35),
    "traffic": ((-14.6, 79.5, 2.2), (14.0, 83.5, 2.4), 32),
    "sidewalk": ((-46.0, 2.0, 2.2), (-14.0, 7.5, 3.2), 30),
    "skyline": ((-20.0, -70.0, 40.0), (10.0, 20.0, 30.0), 30),
}
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(VIEWS)
# close-ups that lock onto a vehicle where it is on the render frame (positions in the city's own space)
scene.frame_set(1200)
inv = root.matrix_world.inverted()
# a facade close-up on a real tower with balconies: from across its street
towers_with_balconies = [o for o in bpy.data.objects if o.name.startswith("City_Tower") and o.type == "MESH" and len(o.data.polygons) > 600]
# the one nearest the x avenue, seen from the open road
near = [t for t in towers_with_balconies if 9 < abs(((inv @ t.matrix_world) @ Vector(t.bound_box[0]).lerp(Vector(t.bound_box[6]), 0.5)).y) < 16]
if near:
    t = near[len(near) // 2]
    c = (inv @ t.matrix_world) @ Vector(t.bound_box[0]).lerp(Vector(t.bound_box[6]), 0.5)
    side = 1 if c.y > 0 else -1
    VIEWS["facade"] = ((c.x + 6.0, -side * 2.0, 4.0), (c.x, c.y, 12.0), 30)
# a white citizen up close
whites = [o for o in bpy.data.objects if o.name.startswith("City_Walker") and o.type == "MESH" and "white" in o.data.name.lower()]
if whites:
    o = whites[len(whites) // 2]
    M = inv @ o.matrix_world
    loc = M.translation
    heading = M.to_euler().z
    from mathutils import Matrix as _M
    pos = loc + _M.Rotation(heading, 3, "Z") @ Vector((2.6, -3.2, 2.0))
    VIEWS["citizen"] = (tuple(pos), tuple(loc + Vector((0, 0, 1.9))), 50)
for key, prefix, off, aim_up in (("car_close", "City_Car", (5.0, -5.5, 2.0), 0.9), ("flyer_close", "City_Flyer", (5.5, -5.0, 1.6), 0.6),
                                 ("walker_close", "City_Walker", (3.0, -3.5, 1.6), 1.2)):
    picks = [o for o in bpy.data.objects if o.name.startswith(prefix) and o.type == "MESH" and not o.hide_render]
    if not picks:
        continue
    o = picks[len(picks) // 3]
    M = inv @ o.matrix_world
    loc = M.translation
    heading = M.to_euler().z
    from mathutils import Matrix as _M
    pos = loc + _M.Rotation(heading, 3, "Z") @ Vector(off)
    VIEWS[key] = (tuple(pos), tuple(loc + Vector((0, 0, aim_up))), 40)
    if key not in only:
        only.append(key)
scene.camera = cam
scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
scene.frame_set(1200)
for name in only:
    pos, aim, lens = VIEWS[name]
    cam.location = pos
    d = Vector(aim) - Vector(pos)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = d.to_track_quat("-Z", "Y")
    cam.data.lens = lens
    scene.render.filepath = os.path.join(out_dir, "city_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
