"""Renders low-res check frames through the scene camera to a folder given in
CHECK_DIR (env), for beats 6 and 7. Run headless after keying:

  CHECK_DIR=... blender -b slimsico.blend --python checks_beat7.py
"""
import bpy
import os

out = os.environ.get("CHECK_DIR", os.path.join(os.path.dirname(bpy.data.filepath), "renders", "checks"))
os.makedirs(out, exist_ok=True)
s = bpy.data.scenes["Scene"]
s.render.image_settings.media_type = "IMAGE"
s.render.image_settings.file_format = "PNG"
s.render.resolution_percentage = 40
for f in (1100, 1240, 1310, 1340, 1420, 1680, 1730, 1765, 1790, 1830, 1880, 1910, 2010, 2080, 2400, 2600):
    s.frame_set(f)
    s.render.filepath = os.path.join(out, "b7_%d.png" % f)
    bpy.ops.render.render(write_still=True)
print("checks done")
