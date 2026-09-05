# Changelog

All notable changes to slimsico. Newest first. Dates are commit dates.

## 2026-09-05 - Skybox visible in the viewport, physical world sky

### Fixed
- The skybox cube sits 1500 studs out but every 3D viewport only drew to 1000, so the sky never showed on screen. Viewport clip distance is now 10000 in the saved file.

### Changed
- Skybox gradient deepened: less white haze at the horizon, richer blue toward the zenith.
- World background is now a physical multiple-scattering sky matched to the sun direction (for lighting and reflections; the camera sees the skybox cube). Sun lamp lowered from 9 to 5 to suit.
- Material Preview keeps studio lighting so the character's yellow stays true; the skybox is geometry and shows regardless.

## 2026-09-05 - More natural face (`2a4f3a8`)

### Changed
- Eyes are tall ovals sunk slightly into the head, angled a touch outward, in a dark slightly glossy material with a white catchlight each.
- The smile is a tapered bezier stroke projected onto the head surface in a warm brown, replacing the thin black torus arc.

## 2026-09-05 - Single-mesh rigged character (`667c884`)

### Changed
- The character body is now one connected mesh: a joint skeleton (spine, head, arms, legs) is wrapped by the Skin modifier, subdivided, and corrective-smoothed, so head, neck, torso and limbs flow together with no seams.
- Torso and limbs bulked up to the chunky Human Fall Flat proportions; arms shortened slightly.

### Added
- `CharacterRig`, an armature generated from the same skeleton with 24 bones already weighted to the body, so the character can be posed in Pose Mode.
- Eyes, mouth and crown are parented to the body like a production rig.

### Fixed
- A modifier-reordering loop that could hang Blender; it now uses the direct modifier move API.

## 2026-09-05 - Smooth, tall Human Fall Flat styled character (`de68f37`)

### Changed
- Replaced the faceted low-poly build with smooth capsules and ellipsoids: egg-shaped head, chunky soft torso and hips, sausage limbs with mitten hands and rounded feet, about 9.5 studs tall.
- Kept the matte yellow, the smile and the gold crown.

## 2026-09-05 - Low-poly matte yellow character (`e28e3d4`)

### Changed
- Replaced the metaball figure with a taller flat-shaded character built from primitives: separate limbs with joint spheres, dot eyes, a smile, and a six-point gold crown with red and blue gems.
- Materials made matte (no coat, no subsurface).

## 2026-09-05 - Crowned gummy character and numbered grid (`9b10898`)

### Added
- `build_character.py`: first character, a Human Fall Flat styled metaball gummy in pale mint with navy shorts and a gold crown.
- `make_tile_texture.py`: Pillow script that draws `textures/tiles.png`, a numbered grid where each tile shows its column number (top) and row number (below), with heavier lines every 8 tiles.
- `renders/character_viewport.png`: viewport screenshot of the character on the grid.

### Changed
- Baseplate material switched from the procedural checker/brick tiles to the numbered grid texture, mapped from object coordinates so the plate centre lands on the image centre.
- Tiles are 8 studs (64x64 grid) with small corner labels, after an earlier 4-stud / 128x128 pass whose numbers were too large.

## 2026-09-05 - White tile baseplate (`37bca35`)

### Changed
- Baseplate restyled as white ceramic 4-stud tiles with light grey grout and a semi-gloss finish.
- Brighter sun so the tiles read white rather than sky-tinted.

## 2026-09-05 - Initial scene (`0419c55`)

### Added
- `build_scene.py`: builds the whole scene headless from an empty file.
- Six-faced skybox with a procedural sky: height gradient, noise clouds and a sun disc with glow.
- 512x512 stud baseplate, sun lamp, world lighting and a camera.
- `slimsico.blend` and a 1920x1080 EEVEE render in `renders/scene.png`.

## Unreleased ideas

- Pose the character (idle stance, wave) using `CharacterRig`.
- Render the character from the scene camera instead of a viewport screenshot.
- Shape keys for blinking and mouth shapes.
- Props and set dressing on the baseplate.
