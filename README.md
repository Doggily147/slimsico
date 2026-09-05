# slimsico

A Roblox-style starter scene modelled in Blender: a six-faced **skybox** with a
procedural sky (height gradient, noise clouds, sun disc) and a 512x512 stud
**baseplate** with the classic 4-stud tile grid.

![render](renders/scene.png)

## Files

- `build_scene.py` - builds the whole scene from an empty file, saves `slimsico.blend`, and renders `renders/scene.png`.
- `slimsico.blend` - the saved scene.
- `renders/scene.png` - 1920x1080 EEVEE render.

## Rebuild

```
blender --background --factory-startup --python build_scene.py -- .
```

Made with Blender 5.0.
