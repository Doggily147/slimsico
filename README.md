# slimsico

A Roblox-style starter scene modelled in Blender: a six-faced **skybox** with a
procedural sky (height gradient, noise clouds, sun disc) and a 512x512 stud
**baseplate** finished as glossy white 4-stud ceramic tiles with light grout.

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
