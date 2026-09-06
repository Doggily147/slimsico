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
- `rig_utils.py` - shared helpers for the animation scripts: keying with explicit interpolation, a parent-aware bone aimer, and a ground clamp that keeps the body's lowest point on the floor.
- `build_opening.py` - run inside Blender after the character exists: names the rig's bones and keys the opening shot (fall from the sky, belly-flop, get up) with a tracking camera, frames 1-150.
- `build_props.py` - two detailed wooden crates (slats, posts, braces, iron brackets, bolts), one open-topped with a bundle of logs.
- `build_continue.py` - frames 151-561: he looks at his hands, says "Where am I?" (subtitle), walks, hears a whistle, looks up at the falling crates (with a low shot tilted up at them), bolts while they land, slows, turns back and sees them; six camera set-ups plus a crane.
- `render_episode.py` - renders the episode headless, burns the subtitle in and adds the synthesised sound cues (splat, whistles, thuds) with ffmpeg.
- `slimsico.blend` - the saved scene, including the props and all 561 frames of animation.
- `renders/scene.png` - 1920x1080 EEVEE render of the empty set.
- `renders/character_viewport.png` - viewport screenshot of the character on the grid.
- `renders/episode.mp4` - the rendered episode so far, 23.4 s at 1080p with subtitles and sound.
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

Character and animation: open `slimsico.blend` in Blender and run, from the
Text editor, `build_character.py`, then `build_opening.py`, `build_props.py`
and `build_continue.py`. Each can be re-run; it replaces its own part.

Episode video with subtitles and sound (needs ffmpeg on PATH):

```
python render_episode.py
```

Made with Blender 5.0.
