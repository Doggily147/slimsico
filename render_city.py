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
}
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(VIEWS)
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
