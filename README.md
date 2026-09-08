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
- `build_draft2_beat4.py` - draft 2, beat 4 (frames 497-912): the line "I will walk around to find clues", the walk, the look up at a crate falling out of the sky, the run while it lands, the turn back, the crate bursting apart and the monster rising out of it and roaring.
- `build_draft2_beat5.py` - draft 2, beat 5 (frames 913-1080): Yellow backs away, trips over a plank and falls on his back; the monster stomps over, looms and reaches down, its claw hanging over him.
- **Purple** lives in `slimsico.blend` (the "Purple" collection), modelled by hand in Blender through the Blender MCP rather than by a script: Yellow's rig cloned and tinted purple, Yellow's own face with a straight mouth instead of the smile, a flat leather shoulder strap over the right shoulder ball and across the chest, a belt with a brass buckle and a gear pouch on the left hip, and two crossed swords on the back: hexagonal-section green blades with bright edges and glowing binary etched on both faces, a crossguard with ball ends, a wrapped grip and a gem pommel. Everything is bone-parented so the animation scripts drive him unchanged. Hidden from render until the story needs him.
- `build_crate.py` - one big breakable wooden crate; every part is parented to the `Crate` empty and remembers its rest transform.
- `build_monster.py` - the monster: a big rigged beast built with the same one-mesh Skin technique as Yellow (tusks, horns, claws, spikes, glowing eyes).
- `render_draft2.py` - renders draft 2 headless and mixes the sound (wind bed, the falling whistle, the splat) plus an optional music bed from `audio/ambient.*`.
- `build_hovercraft.py` - a flying jetski for Yellow modelled after a small runabout, sharp and futuristic: one hull mesh from cross-sections with every hard line creased (keel, chine, strake, gunwale, rail, deck side, footwell rims), painted purple hood, black hull and rear, white bow sides; footwells with mats, one sculpted two-seat unit with backrests, an integrated dash with a hologram projector and a floating holographic hover-screen behind it showing the animated HUD from `make_hud.py`, windshield, winged handlebars, light strips, rub rail, a thruster bay at the stern with glowing nozzles, boarding step; anti-grav pods with neon rings underneath that light the ground, neon chine lines and winglets; hovers with a gentle bob.
- `make_hud.py` - the hover-screen as a working device UI (craft name NIMBUS): a phone-like home screen with a live speed widget, app grid and dock, and thirteen animated app screens (Drive, Map, Messages with a typing keyboard, Calls, Music, Camera, Photos, Weather, Notes, Shop, Settings, Games, Lock) whose buttons all work. Renders a timeline of taps and typing to an image sequence: the idle loop to `textures/hud/`, `python make_hud.py demo` to `textures/hud_demo/`; story scripts call `render(events, out_dir, frames)`. Needs Pillow.
- `build_office.py` - builds the "OfficeTest" scene: an office set, the worker and police officer cloned from Yellow, and the three-attempt robbery with rewinds.
- `render_office_test.py` - renders OfficeTest and assembles it with the rewinds, subtitles, sound, and an optional music bed from `audio/ambient.*`.
- `slimsico.blend` - the saved scene: the set, Yellow on the grid (cleared between drafts), and the OfficeTest scene.
- `renders/scene.png` - 1920x1080 EEVEE render of the empty set.
- `renders/character_viewport.png` - viewport screenshot of the character on the grid.
- `renders/office_test.mp4` - the office robbery test scene with rewinds.
- `renders/draft2.mp4` - draft 2 so far.
- `renders/hovercraft.png` - viewport shot of the flying jetski.
- `renders/hovercraft_dash.png` - the rider's view of the dash, hologram and hover-screen.
- `renders/hover_screen_demo.mp4` - the hover-screen demo: every app opened and used.
- `renders/monster.png`, `renders/monster_rise.png` - the monster roaring, and rising out of the burst crate.
- `renders/purple.png`, `renders/purple_back.png` - Purple from the front and from behind (the swords).
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

Jetski HUD frames (before running `build_hovercraft.py`):

```
python make_hud.py
```

Hover-screen demo video (needs ffmpeg on PATH):

```
python make_hud.py demo
ffmpeg -y -f lavfi -i color=c=0x14081f:s=540x800:r=24 -framerate 24 -i textures/hud_demo/hud_%04d.png -filter_complex "[0][1]overlay=shortest=1" -c:v libx264 -pix_fmt yuv420p -crf 20 renders/hover_screen_demo.mp4
```

Character: open `slimsico.blend` in Blender and run `build_character.py` from
the Text editor, then `build_draft2.py` for the current draft, and `build_crate.py`, `build_monster.py` then `build_draft2_beat4.py` and `build_draft2_beat5.py` for beats 4 and 5 (the beat scripts also run headless: `blender -b slimsico.blend --python build_draft2_beat5.py`). Finished drafts
are archived under `drafts/`; see `DRAFTS.md`.

Draft 2 video with sound (needs ffmpeg on PATH):

```
python render_draft2.py
```

Only a new tail (frames 913 on), spliced onto the kept raw render:

```
python render_draft2.py --from 913
```

Office test scene (run `build_office.py` in Blender first):

```
python render_office_test.py
```

Made with Blender 5.0.
