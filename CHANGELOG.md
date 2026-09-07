# Changelog

All notable changes to slimsico. Newest first. Dates are commit dates.

## 2026-09-07 - Flying jetski

### Changed
- Sharpened and detailed: each section now carries eleven hard lines (keel, chine, strake, gunwale, rail, deck side, footwell rim, footwell floor, seat-base wall, seat-base top, centre) and every one is creased, plus the hood-peak and step rings, so the subdivided surface reads as crisp panels rather than a curvy blob. Footwells either side of the seat with ribbed mats, a two-tier flat-topped saddle, a faceted pod with a proper console display on a bezel behind a low angular windshield, handlebars with a chrome clamp, levers and mirror glass, angular intake vents, purple light strips following the hull line at bow and stern, and a thruster bay in the transom: a recessed housing with a chrome ring nozzle and two side nozzles, all with glowing purple cores.
- The craft is remodelled after a real sit-down jetski rather than an aircraft. The body is one smooth mesh built from fourteen hull cross-sections (keel, hard chine, near-vertical topsides, gunwale, rub rail, tall deck side, deck shoulder, deck centre) with the chine, gunwale and deck edges creased so subdivision keeps them crisp. The hood rises to a handlebar pod and drops to a long, flat-topped saddle. Painted by region: purple hood and fairing, black hull and rear deck, white bow sides. Details: chrome-black handlebars with purple grips and levers, a lit pod screen, mirror pods, a rubber rub rail that follows the hull, a boarding step and grab handle at the stern, a bow eye. Instead of a jet pump, a purple hover pad underneath with three point lights that light the plate, and a faint glow disc; it hovers with a gentle bob. Shape was checked against the reference from the photo's angle and adjusted over three passes.

## 2026-09-07 - Hover-jetski

### Changed
- The hovercraft is redesigned as a flying-car style hover-jetski: a lofted dark-grey metallic hull with a pointed nose (built from squircle cross-sections and subdivided), a saddle seat and chrome handlebars, a low cowl with a raked tinted screen, swept side sponsons with cyan light strips, twin rear thrusters with glowing cores and chrome rings, a swept tail fin with a light, a red tail strip, cyan side strips, a nose light and panel grooves. Three repulsor pads underneath glow and carry point lights that light the plate, with a faint glow disc at ground level. It hovers two studs up with a gentle bob and sway keyed across the scene.

## 2026-09-07 - Hovercraft (first pass, replaced)

### Added
- `build_hovercraft.py`: a stylised hovercraft prop, 16 by 9 studs. A bevelled teal hull with a rounded nose on a fat rubber skirt with a rubbing strake, an open cockpit (seat, dashboard with a lit screen, steering yoke, raked tinted windscreen in a steel frame, roll bar), a raised rear deck carrying a big ducted six-blade fan with an orange lip, a front grille and twin orange rudders, twin intake pods, headlights and tail lights, white and orange racing stripes, side flashes and the number 07. Everything hangs off the "Hovercraft" empty; the blades hang off "HovercraftFan" so they can spin.

## 2026-09-07 - Draft 2: he says the line

### Changed
- The smile read as a moustache: it is now a thinner, darker, slightly narrower stroke sitting a little lower on the face.

### Added
- A talking mouth: an open-mouth shape on the head bone swaps in for the smile while he speaks and opens and closes per syllable ("Where", "am", "I"), then the smile returns.
- A hand gesture for the line: both hands come up and turn out in a shrug, with a second small lift on "I", then settle.

### Changed
- The line is now delivered in a medium shot of his face and hands (frames 406-452) before the wide pull-back, so the mouth and gesture read; the slow body turn starts with the pull-back. The beat runs to frame 496.

## 2026-09-06 - Draft 2, beat 3: up, the arm rub, somewhere else

### Added
- The subtitle "Where am I?" over the end of the reveal (frames 410-452), with the beat extended to frame 460 so it has room.
- Frames 241-440. He gets up with his arms (elbows lift, hands push under the chest, back arches onto hands and knees, feet tuck under, stands with a small overshoot), the ground clamp keeping contact throughout. He holds his left forearm across his belly, looks down at it once, and rubs it with his right hand three times. Then the arms lower, the head lifts once and holds, and he turns slowly to take in the plate while the camera pulls far back to show it deserted around him. Four camera set-ups: a front-left medium for the get-up, a shot from above his eyeline for the rub, a close-up for the head lift, and the wide pull-back.

## 2026-09-06 - Draft 2, beat 2: the fall and the landing

### Changed
- The tumble is a proper tumble: the body rotates about its centre of mass (not the rig origin at the feet), driven by an angular velocity that is mostly end-over-end but whose axis drifts and whose speed surges, so he flips, twists and slows instead of spinning like a propeller. The body animates through it: the spine arches and curls, arms windmill against the flip, legs kick, and every couple of seconds he tucks into a ball.
- The fall now reads as a fall: he starts with some downward speed and accelerates under gravity, the roll speeds up as he drops, and the camera follows him all the way down so the plate rushes back into frame behind him. The lens widens back out as he nears. Motion blur is on for the render.

### Added
- The landing: the tumble resolves into a belly-first hit at frame 190 with a squash, a small bounce and a slide, a camera shake on impact, and a splat in the sound mix. The whistle now runs right up to the impact. The beat ends at frame 240 with him lying still.

## 2026-09-06 - Draft 2, beat 1: a sound from above

### Added
- `build_draft2.py`: frames 1-150. A peaceful, slowly drifting wide shot of the empty baseplate under the sky. A faint whistle from above. The camera tilts up and rises, the lens tightens from 30 mm to 66 mm as it searches, and finds Yellow far up in the sky, rolling end over end with a lazy twist, limbs flailing on their own rhythms, drifting closer as he falls.
- `render_draft2.py`: headless render plus a soft pink-noise wind bed, the long descending whistle that grows as he nears, and the optional music bed.

## 2026-09-06 - Yellow redesigned for draft 2

### Changed
- Proportions: a bigger head (about a third of his height), a shorter and softer body, thicker limbs with the hands at hip height, and big rounded feet. About 9 studs tall.
- Face: larger eyes with bigger catchlights and a slightly wider smile. Crown scaled up to match the head.
- Deformation: the corrective smooth (which warned about rest shapes) is replaced by a light smooth pass; a touch of subsurface softens the shading without adding shine.
- Rig: bones are now named from the joints they run to inside `build_character.py` (`spine.002`, `upper_arm.L`, ...), and the crown, eyes and mouth are bone-parented to the head at build time, so any animation script can use the rig straight away.

## 2026-09-06 - Draft 1 archived

### Changed
- The crates episode is archived as draft 1: tagged `draft-1`, its scripts and video moved to `drafts/draft-1/`, and logged in `DRAFTS.md` with what was learned. The working scene is cleared back to Yellow standing on the grid with no animation, ready for draft 2.

## 2026-09-06 - Office test scene

### Added
- `build_office.py`: a second Blender scene, "OfficeTest", with an office set (carpet, walls, ceiling, a door on a hinge, window, clock, picture, filing cabinet, plant, ceiling panel light) and a desk with monitor, keyboard, mouse, papers, mug and lamp, plus an office chair that tips about its back edge.
- Three characters cloned from Yellow's rig via `rig_utils.clone_character`: Yellow (with crown and a pistol in his right hand), a blue office worker with a tie, and a navy police officer with a cap and badge.
- The scene: Yellow walks in and points the gun ("Hand it over."). Attempt 1: he shoots, muzzle flash, the worker and chair go over backwards. Rewind. Attempt 2: he slips, lands on his back, the officer bursts in and stands over him ("Freeze!"). Rewind. Attempt 3: the worker leans over the desk with a shouting mouth and angry brows and yells "WILL YOU STOP THAT?!"; Yellow shrinks back and lowers the gun. Nine camera set-ups.
- `render_office_test.py`: renders the scene headless, builds the rewinds at assembly time (the footage since the gun came up, reversed and sped up with a desaturated, noisy VHS look and a "<< REWIND" stamp), burns in the subtitles, and mixes synthesised sound: typing, door, gunshot, chair crash, siren, the yell, and a rewind whoosh. Mixes in an ambient music bed quietly if a track is placed at `audio/ambient.*`.
- `rig_utils.gait_dirs`: the walk and run cycle pose generator, shared by the scenes.

## 2026-09-06 - Polish pass: sound, the crate reaction, a real run

### Changed
- The crate sequence is now cause and effect: a falling whistle starts, he cocks his head, looks up and tracks the first crate down the sky with his face (not just the head bone), spins and bolts while both crates land behind him, slows to a stop, turns back and sees they have landed. The camera cranes up for the run and sinks forward over the crates toward him at the end.
- The run cycle: arms swing opposite the legs with bent elbows, the forearm rising as the arm comes forward and dropping as it goes back, instead of both forearms held out in front. Longer, smooth ramps in and out of the walk and run.
- Turn to run lengthened to 14 frames so it no longer snaps.
- Ground clamp smoothed over neighbouring frames, but never below the raw contact height, so the walk and run bob without jitter or dipping.
- Head movement in the "Where am I?" section removed: he lifts his head from his hands and holds it straight ahead. After the crates land his head settles once and holds.

### Added
- A look-up shot: as he looks up, the camera cuts to a low position just behind his shoulder, tilted up and tracking the first crate as it falls, then cuts back to the wide shot as he turns to run.
- Sound, synthesised with ffmpeg in `render_episode.py`: a belly-flop splat, a descending whistle for each falling crate, and a heavy thud for each landing, placed on the exact frames.
- `rig_utils.motion_spikes`: flags frames where the head accelerates unnaturally, used as a jerk check after keying, alongside the floor check.

## 2026-09-06 - Second beat: hands, "Where am I?", the walk, the crates

### Added
- `build_continue.py`: frames 151 onward. He lifts his hands and looks at them, a close-up as he lifts his head, a wide shot while the subtitle "Where am I?" plays, a side-tracking walk of about 14 studs, then the crate sequence above. Five camera set-ups plus the crane.
- `build_props.py`: two detailed wooden crates (corner posts, slatted sides with gaps, base boards, diagonal braces, iron corner brackets with bolt heads, procedural wood grain). Crate 2 is open-topped with a bundle of upright logs (bark texture, growth-ring ends) standing out of it.
- `rig_utils.py`: shared keying helpers, the parent-aware bone aimer, and a ground clamp that keys the rig's height so the lowest point of the body always touches the floor.
- `render_episode.py`: renders the episode headless and burns the subtitle in with ffmpeg, producing `renders/episode.mp4`.

### Changed
- The episode video replaces `renders/opening.mp4`; the opening is its first 150 frames.

## 2026-09-06 - Opening ends on his feet

### Removed
- The hop after he stands. He now just settles on his feet and the shot ends at frame 150.
- The turn-to-camera beat after he stands, and the whole orbit scene (`build_orbit.py`, `assemble_intro.py`, the orbit clips and `intro.mp4`). The opening ends once he has settled on his feet, with the camera easing back slightly.

## 2026-09-05 - Opening shot

### Added
- `build_opening.py`: a 6.25-second opening (150 frames at 24 fps). Yellow drops out of the sky with a gravity-accurate fall and a tumble, belly-flops with a squash and a small bounce, lies still, then gets up properly: hands come in under the shoulders and push the chest up, the back arches, the knees fold under onto hands and knees, the feet tuck in to a crouch, and he stands.
- Full-body poses keyed through the rig with a parent-aware bone aiming helper: spine, neck, head, upper arms, forearms, thighs and shins. Arms flail in the air, spread flat along the ground for the splat, and lower as he stands.
- Crown, eyes and mouth are bone-parented to the head so they follow it when it is posed.

### Fixed
- Hands no longer pass through the floor during the push-up: the elbows lift first, the hips rise earlier, and the hands-and-knees height was trimmed so the hands rest on the grid rather than floating.
- Feet no longer sink into the floor in the crouch (frames 106-118): the crouch root height was raised. The lowest point of the body is now checked on every frame of the shot and never goes below the grid.
- The camera falls beside him, settles at ground level for the landing, then eases back a little as he gets up, tracking his head throughout.
- `renders/opening.mp4`: the shot rendered in EEVEE at 1080p.

### Changed
- Rig bones renamed from `Bone.NN` to proper names (`spine.001`, `head`, `upper_arm.L`, `foot.R`, ...).
- Scene frame range is now 1-150 with H.264 video output settings saved in the file.
- Render lighting balanced for the yellow: sun lowered to 3 and warmed, world sky blended 70% toward a neutral warm grey (it was tinting the character green), exposure -0.35 so the white grid no longer blows out.

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
