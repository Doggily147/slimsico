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
  sausage limbs, mitten hands) but its own identity: a big friendly head,
  matte yellow, and a crown.
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
- `rig_utils.py` - shared helpers for the animation scripts: keying with explicit interpolation, a parent-aware bone aimer, and a ground clamp that keeps the body's lowest point on the floor.
- `build_draft2.py` - draft 2 animation on the main scene (the peaceful plate, a sound from above, the camera finds Yellow tumbling far up in the sky and follows him down to a belly-flop landing).
- `render_draft2.py` - renders draft 2 headless and mixes the sound (wind bed, the falling whistle, the splat) plus an optional music bed from `audio/ambient.*`.
- `build_hovercraft.py` - a flying jetski for Yellow modelled after a small runabout, sharp and futuristic: one hull mesh from cross-sections with every hard line creased (keel, chine, strake, gunwale, rail, deck side, footwell rims), painted purple hood, black hull and rear, white bow sides; footwells with mats, a rider seat and a passenger seat each with a backrest, an integrated dash with a hologram projector, a screen above it, windshield, winged handlebars, mirrors, vents, light strips, rub rail, a thruster bay at the stern with glowing nozzles, boarding step; a purple hover pad underneath that lights the ground; hovers with a gentle bob.
- `build_office.py` - builds the "OfficeTest" scene: an office set, the worker and police officer cloned from Yellow, and the three-attempt robbery with rewinds.
- `render_office_test.py` - renders OfficeTest and assembles it with the rewinds, subtitles, sound, and an optional music bed from `audio/ambient.*`.
- `slimsico.blend` - the saved scene: the set, Yellow on the grid (cleared between drafts), and the OfficeTest scene.
- `renders/scene.png` - 1920x1080 EEVEE render of the empty set.
- `renders/character_viewport.png` - viewport screenshot of the character on the grid.
- `renders/office_test.mp4` - the office robbery test scene with rewinds.
- `renders/draft2.mp4` - draft 2 so far.
- `renders/hovercraft.png` - viewport shot of the flying jetski.
- `CHANGELOG.md` - full history of changes.
- `DRAFTS.md` - the draft log; each finished draft is archived under `drafts/` and tagged.

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
the Text editor, then `build_draft2.py` for the current draft. Finished drafts
are archived under `drafts/`; see `DRAFTS.md`.

Draft 2 video with sound (needs ffmpeg on PATH):

```
python render_draft2.py
```

Office test scene (run `build_office.py` in Blender first):

```
python render_office_test.py
```

Made with Blender 5.0.
