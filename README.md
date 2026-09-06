# slimsico

A stylised Blender scene and character: a six-faced **skybox** with a
procedural sky (height gradient, noise clouds, sun disc), a 512x512 stud
**baseplate** finished as a numbered grid of 8-stud tiles, and a smooth,
matte yellow, Human Fall Flat styled **character** wearing a gold crown.

![character](renders/character_viewport.png)

## Goal

Build a polished, animation-ready character and set in Blender that would be
comfortable to use in a professional animated series:

- **One connected body.** No visibly separate parts and no faceting. The body
  is a single smooth mesh that flows from head to toes.
- **Rigged.** An armature is generated with the body so the character can be
  posed and animated straight away.
- **Distinct look.** Human Fall Flat proportions (egg head, chunky soft torso,
  sausage limbs, mitten hands) but its own identity: tall, matte yellow, a
  friendly face, and a crown.
- **Reproducible.** Everything is built by scripts checked into this repo, so
  the scene and character can be regenerated and tweaked by editing numbers,
  not by hand-modelling.
- **A usable set.** The baseplate grid is numbered so positions can be
  described by tile, for laying out props and blocking shots.

Progress against this goal is tracked in [CHANGELOG.md](CHANGELOG.md).

## Files

- `build_scene.py` - builds the whole scene from an empty file, saves `slimsico.blend`, and renders `renders/scene.png`.
- `make_tile_texture.py` - draws `textures/tiles.png`, the 64x64 numbered grid of 8-stud tiles (column number on top, row number below, row 1 at the bottom-left). Needs Pillow.
- `build_character.py` - run inside Blender with the scene open: builds the crowned character as one connected Skin-modifier mesh with subdivision and an auto-generated armature (`CharacterRig`), and switches the baseplate to the numbered grid texture.
- `build_opening.py` - run inside Blender after the character exists: names the rig's bones and keys the opening shot (fall from the sky, belly-flop, get up) with a tracking camera, 150 frames at 24 fps.
- `slimsico.blend` - the saved scene, including the opening animation.
- `renders/scene.png` - 1920x1080 EEVEE render of the empty set.
- `renders/character_viewport.png` - viewport screenshot of the character on the grid.
- `renders/opening.mp4` - the rendered opening shot (1080p, H.264).
- `CHANGELOG.md` - full history of changes.

## Rebuild

Empty set, headless:

```
blender --background --factory-startup --python build_scene.py -- .
```

Grid texture:

```
python make_tile_texture.py
```

Character: open `slimsico.blend` in Blender and run `build_character.py` from
the Text editor. Re-running it replaces the character. Then run
`build_opening.py` the same way to key the opening shot.

Opening shot video (the .blend carries the output settings):

```
blender -b slimsico.blend -a
```

Made with Blender 5.0.
