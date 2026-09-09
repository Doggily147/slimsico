"""Sets the viewport subdivision level of the heavy meshes, for wrapping a
headless beat pass: level 0 while keying (every frame the scripts touch
re-evaluates these), then back to 2 before saving.

The level comes from bpy.app.driver_namespace["subdiv"] (Blender stops reading
arguments at "--", so it cannot be passed that way):

  blender -b slimsico.blend --python-expr "import bpy; bpy.app.driver_namespace['subdiv'] = 0" --python subdiv_level.py       --python build_draft2_beat6.py       --python-expr "import bpy; bpy.app.driver_namespace['subdiv'] = 2" --python subdiv_level.py --python-expr "import bpy; bpy.ops.wm.save_mainfile()"
"""
import bpy

HEAVY = ("Character", "Monster", "Purple", "Hovercraft_Body", "Hovercraft_Dash", "Hovercraft_Seat", "Officer", "Robber")
level = int(bpy.app.driver_namespace.get("subdiv", 2))
for name in HEAVY:
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    for m in o.modifiers:
        if m.type == "SUBSURF":
            m.levels = level
print("subdiv level", level)
