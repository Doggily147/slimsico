# Changelog

All notable changes to slimsico. Newest first. Dates are commit dates.

## 2026-09-10 - Music ends with beat 6; the city moves

### Changed
- The music bed now runs under beats 1-6 only and fades out at frame 1656 (`MUSIC_END` in `render_draft2.py`); beat 7 plays with its own cues alone.
- The city moves from the far corner (-165, -165) to the front-right corner (165, -165), turned so the gate still faces the plate centre (`CITY_POS` in `build_city.py`; the built city's root empty was moved and rotated in the blend rather than rebuilt).
- `render_draft2.py --remix` rebuilds just the sound on the finished video, and `--from N --head-final` splices a new tail onto the finished video when there is no raw render on this machine (the finished frames' subtitles are already burnt in, so only the new tail gets them).

## 2026-09-10 - Draft 2 rendered through beat 7

### Changed
- `renders/draft2.mp4` is beats 1-7, 112 s with music. Known weak spots left for the next pass: the city's facades read blocky up close (the recessed window grid with narrow piers), and a few beat 7 shots are tight.

## 2026-09-09 - Beat 7: Lime

### Added
- `build_lime.py`: Lime, a lime-green blob cloned from Yellow's body and rig (`rig_utils.clone_character`) with Yellow's eyes, smile and open mouth, round glasses (two rings, a bridge and arms on the head bone) and "LIME" as extruded text pressed onto the outside of his left forearm just below the elbow, riding the forearm bone. Hidden from render until the story needs him.
- `build_draft2_beat7.py` (frames 1657-2680): Purple flies Yellow on in a wide bank over the plate at cruising speed. Up ahead Lime falls out of the sky, limbs flailing, straight down onto the spot where the gunwale will be, and the jetski passes under him perfectly: his hands hit the rail, he swings down and hangs off the right side, legs kicking, while Purple gives him one glance and Yellow twists round: "What, how did you get on here?" Lime pulls up, gets a knee on the gunwale, swings over and sits on the side with his legs over the edge and a hand on the rail: "What the hell..." "...is going on!" Then the exchange: Yellow's "I don't know any more than you" with a shrug, Lime asking Purple, Yellow's "He's not really much of a talker" with glances at Purple's back, Lime's "Ughhh", a beat, "Anyways, what are your guys' names?", Yellow's long "Uhhhhhhhh", "I guess Yellow. And just call this other guy Purple", two seconds, "How about you, what is your name?", Lime's "Umm", he lifts his forearm and looks at the name on it, "Lime." Purple never speaks. Talking mouths per syllable for both, eyelines following whoever is spoken to. Shots ride with the jetski: the bank from ahead, the speck falling seen from behind the seat, the landing from the right, low off the side for the hang, over the stern for the climb, two-shots and singles for the lines, and a close-up on the forearm for the name.
- `render_draft2.py` renders to frame 2680 with the thirteen new subtitles and cues (the hover hum, Lime's falling whistle, the catch, the thump as he lands on the seat).

## 2026-09-09 - Beat 6 bug pass

### Fixed
- A QA reviewer went over beat 6 frame by frame. Fixed: the catch now holds the wrist (Yellow's hand sits just above Purple's palm instead of a body-length below it); the hands stay together once the jetski lifts (the floor clamp only applies while he is still on his feet); Purple catches and heaves with his arm back over the side so Yellow comes up beside the passenger seat rather than through Purple's leg; Yellow sits further back with his hands on his knees, clear of the katanas; the jetski climbs higher over the monster; no pop at the join with beat 5; five shots reframed so Purple's head and the monster's jaw are in frame; and the motion-blur shutter is shorter (0.3) so fast hands and heaves stop ghosting.

## 2026-09-09 - The city, professional pass

### Changed
- An art director agent reviewed the city; the pass that followed: every tower body is now one mesh with real recessed windows (inset frames, lit or dark panes, the reveal walls lit as the room behind), residential floors with balconies (a slab, a railing, a doorway), podiums with glass lobbies (columns, reception desk, lit ceiling, seats, citizens), 232 shops you can see into (open glass fronts with a doorway, counter, shelves of goods, a hanging light, a shopkeeper and customers, a neon name over the door from a word list), six tower silhouettes plus four landmark towers nearly twice the height (a twisted stack, a ring-crowned tower, a split tower with sky bridges, a taper), a hero spire (tapered glass shaft with lit seams, an observation deck, a turning holo ring, a blinker), ten facade families (dark claddings, concrete panel, brushed metal, coloured composite) with district neon hues by sector, a plaza with a fountain and a park ring, crosswalks and traffic lights, an elevated monorail loop with pylons, two stations with waiting citizens and two four-car trains with passengers, forty big neon names on the towers, floating holo ads, haze under the dome for depth, stronger neon, fewer antennas, flyer lanes above the roofs, and citizens in a range of sizes.
- The citizens are blobs like Yellow and Purple: Yellow's body baked from his rest pose and scaled to street size, with eyes and a smile, in eight colours; about a third are white and those carry a drawn eye on the forehead. 254 of them walk the sidewalks, the avenues and the plaza, plus the ones in shops, lobbies and stations.
- Cars are profile-extruded, tapered, bevelled and smoothed, with real wheel arches, see-through glass and people inside (drivers and passengers), door seams, handles, mirrors, plates, rims with spokes; sedans, sports cars, vans and buses. Flyers likewise with pilots, engine pods, winglets and a thruster.

## 2026-09-09 - City: better towers and vehicles

### Changed
- Towers come in six silhouettes now (tiered with ledges and window bands, cylinders with ring ledges and a crown, slabs with fins and roof masts, twin towers joined by lit sky bridges, five-step tapers with a neon spike, hexagonal prisms with neon edges), most on a podium with a neon band and a lit entrance canopy, and every roof carries plant boxes, tanks, an antenna mast with neon rings or a helipad.
- Vehicles are modelled from side profiles extruded and bevelled, with dark glass cabins, tyres with chrome rims and lit hubs, bumpers, headlights, tail strips, mirrors and underglow: sedans, low sports cars with spoilers, vans and buses on the roads; sleek and cargo flyers with engine pods, intakes, glowing exhausts, winglets and a rear thruster in the air. One mesh per type, painted per instance.
- `render_city.py` adds a ring-road traffic view, a skyline view, and close-ups that lock onto a car and a flyer where they are on the render frame.

## 2026-09-09 - The cyber city

### Added
- `build_city.py`: a giant neon city under a forcefield dome in the far corner of the plate (the "City" collection, everything under the `City` empty at (-165, -165)). From the drawing: a ring wall of tough stone (procedural blocks with dark joints and bump), 14 studs high and 200 across, with a lit slit along it and a car-sized turret pod on top every 45 degrees (domed body, lit slit, chrome barrel with a glowing tip, legs), an arched forcefield gate in the front of the wall facing the plate centre with stone pillars and a ring of emitters round the arch, and a simple see-through forcefield dome sitting on the wall top (fresnel glow, faint cells, a bright ring where it meets the wall). Inside: a pavement disc, two lit avenues and a ring road with neon lane lines, a central plaza with a chrome spire and neon decks, 116 towers on an 11-stud grid stepping up toward the centre (tiered, lit windows from a brick texture in object space, neon strips down the edges, caps, antennas, helipads, holographic billboards, some showing the hover-screen HUD), low blocks and neon signs at street level, 60 ground cars (one mesh instanced, painted per object) circling the ring road both ways and running the avenues, and 48 flying cars on lanes at eight heights plus straight crossings, all keyed for the whole timeline. Six shadowless neon glow lights.
- `render_city.py`: renders five check views (the gate, aerial, street level, looking up from the plaza, and from the plate) to `renders/city_*.png`.

## 2026-09-09 - Beat 6 through a critic, twice

### Changed
- Beat 6 went through two rounds of a critic agent reviewing frames sampled every half second, with fixes after each. Round one: the jetski hovered with its nose inside the monster and its hull over Yellow's legs, so it now parks further out and further up his body; Purple's offered hand was a sideways T-pose, now it reaches down palm-first, beckons twice, and he looks down at Yellow; the monster now recoils in two steps, backing off a stride, and its lunge is bigger; the hands never actually met, so Yellow's mitten now clasps over Purple's; the jetski rises level before it turns so the grab reads; the heaves pulled Yellow's wrist above Purple's head, now to chest height; Yellow sits further back with his feet down in the footwells and leaning back; five shots were reframed (the line, the reach, the catch, the two riding lines). Round two: the jetski banked toward the side Yellow hangs on and lowered the hull onto him, so it now turns left, away from him, and the bank lifts the hull clear; the haul no longer flips him, he drags belly-first over the gunwale and settles onto the seat; a looser clasp; Yellow's hands hold the grab rail behind him; Purple's glance back is a real turn over his shoulder; the "Who are you?" camera looks up past his feet at his face; the insert and the alongside shots are pulled back so both characters are in them.
- `render_prep.py`, run by `render_draft2.py` before every render: motion blur used to straddle each camera cut and blend two shots into one ghost frame. The shutter now opens at the frame and the key before every cut is held, so cuts are clean.
- `subdiv_level.py` wraps a headless beat pass: subdivision down to 0 while keying, back to 2 before saving (a beat 6 pass is about ten minutes).

## 2026-09-09 - Full draft 2 assembled

### Changed
- `renders/draft2.mp4` is the whole of draft 2 so far, beats 1-6, 69 s with music: beat 6 rendered on this machine and spliced onto the kept raw render with `render_draft2.py --from 1081`.

### Fixed
- The hover-screen's HUD image sequence was saved with the other checkout's absolute path and rendered blank here; it is now blend-relative (`//textures/hud/`).

## 2026-09-08 - Beat 6: the haul, and the crate cleared

### Changed
- The haul is a struggle now: Purple gets his second hand on Yellow's wrist and heaves twice, leaning back into each pull; Yellow comes up in jerks, knees scrabbling at the hull, free hand grabbing for the rail, then is dragged belly-first over the side, flops across the passenger seat and pushes himself up to sitting. Every heave lifts him because he is hand-locked to Purple's hands.
- The camera is on it: a tight low shot from the front quarter with a little handheld shake (his face looking up, Purple heaving above), then over the stern for the flop and the sit-up.
- The burst crate's wood is cleared away for this beat (keyed, so beats 4-5 keep it).

## 2026-09-08 - Beat 6 fixes

### Fixed
- Purple and Yellow sat with the pelvis joint on the cushion, so the body sank through the seat; both now sit with the body's bulk on the cushion.
- Yellow scrambles to his feet beside the jetski and takes Purple's hand standing, so the hands meet before the lift instead of parting when his sitting reach fell short.
- The monster no longer just stands there: it lunges after Yellow as he reaches, swipes at him as the jetski lifts and misses, then rears up and roars after them (roar cue added).
- Music: "Volatile Reaction" (Kevin MacLeod, CC BY 4.0) at `audio/ambient.mp3`, mixed louder under the picture.

## 2026-09-08 - Draft 2, beat 6: Purple

### Added
- `build_draft2_beat6.py` (frames 1081-1656): a whine from the sky and Purple dives in on the jetski at speed, flares and banks in low beside Yellow, hovering with the pods just off the plate; the monster rears back and pulls its claw away. Purple, sitting on the rider seat, leans right out and holds his hand down to Yellow. Yellow, propped on his elbows, looks from the jetski to the hand and says "Who are you?" (talking mouth). Purple says nothing; he never does. Yellow sits up, reaches, and takes the hand. The jetski lifts and turns away from the monster and Yellow dangles under Purple's hand, swung out clear of the hull, legs kicking, while it climbs. An insert rides along with the two hands as Yellow's grip creeps down Purple's hand and trembles; a wide from the ground shows them small against the sky, going higher. Yellow's hand slips and he drops; Purple's arm snaps down and catches his other wrist one-handed as the jetski lurches and dips, then he hauls Yellow up and over the side onto the passenger seat. Flying on, Yellow holds Purple's waist and asks "Where are we going?"; three seconds of nothing; "Hello, are you going to answer me?"; "You're not much of a talker, are you?" Purple gives him one slow glance and looks straight ahead again. Shots: from the ground past Yellow up at the sky, Purple leaning out, Yellow's face for the line, a two-shot over his head for the grab, the lift-off panned from the ground, the hands insert, the climb from below, alongside for the slip, catch and haul, and three riding shots ahead of, beside and in front of the jetski for the lines.
- `render_draft2.py` renders to frame 1656 with the four new subtitles and the cues: the diving whine with wind rush, a hover hum under the rest of the beat, the lift swell, the climb rush, the slip squeak and the catch slap.

### Fixed
- The committed blend only held beats 1-3: the crate, the monster and beats 4 and 5 had never been saved into it (they were rebuilt from their scripts before beat 6). `build_crate.py` clears the whole Props collection, which deletes the jetski, so `build_hovercraft.py` now runs after it; the jetski is keyed hidden until it flies in.

## 2026-09-08 - Purple: plain katanas

### Changed
- The binary etching and the glowing pommel gems are gone, and the blades are polished steel instead of green: two normal katanas, same shape and carry.

## 2026-09-08 - Purple: debug katanas, tip-down

### Changed
- The two swords are now katanas: a curved single-edged blade with a ridge, a bright edge and an angled tip, a pierced round guard, a collar, a criss-cross wrapped grip over a pale under-wrap, an end cap with a small glowing gem, and binary etched on both flats. They hang tip-down across his back with the grips up over the shoulders.
- Checked Purple's head against Yellow's at rest with the same camera: it is the same mesh (a clone of Yellow's body), so no shape change was made.

## 2026-09-08 - Purple: plain hands and feet, Yellow's face, straight mouth

### Changed
- The glove and boot shells and the brows are removed. His eyes are now exactly Yellow's (same size, tilt, sinking and catchlights) and the mouth is Yellow's stroke drawn as a straight line: a neutral face rather than a smile.

## 2026-09-08 - Purple, second pass: modelled by hand

### Changed
- Purple is now modelled live in Blender through the Blender MCP (ahujasid/blender-mcp, addon auto-starts with the file) instead of a build script, and lives only in the blend. `build_purple.py` is removed. Gone: the mask band, the hood peak, the chest core and its ring, the shoulder shards, the tube strap and belt. New: a real face like Yellow's (the big round eyes kept, a smile stroke and two angled brows on the head bone); a flat leather shoulder strap built as a ribbon of ray-cast samples that hugs the body, running over the right shoulder ball, across the chest to the left hip and up the back; a flat belt with a brass buckle and pin; a leather gear pouch with a flap and clasp on the left hip; and two proper swords crossed on the back with the grips at the belt: hexagonal-section blades tapering to a point with the sharp edges in a bright material, glowing binary etched on both flat faces, a bevelled crossguard with ball ends and a collar, a ring-wrapped grip, a pommel with a glowing gem.
- Lesson kept for the strap: cast the sample rays from just outside the waist, not from far away, or they hit the hanging hands; and do not shrinkwrap a band that passes the hips, it snaps to the thighs.

## 2026-09-08 - Purple (first pass, replaced)

### Added
- `build_purple.py`: Purple, built from the drawing. Yellow's one-mesh body and rig are cloned (`rig_utils.clone_character`) and tinted purple so the two share proportions and every animation script drives him unchanged. On top: dark glove and boot shells on the hand and foot bones; two big round black eyes with catchlights over a dark mask band sunk into the head, and a soft hood peak; a brown strap that follows the body surface from the right shoulder across the chest to the left hip and round the back, a belt with a brass buckle; a glowing green nanobot core in an eight-sided ring on the chest where the strap crosses; six green nanobot shards standing on each shoulder; and two green blades on the back, crossed with the grips at the belt, each stamped with glowing binary down both faces. He is built at the origin facing -Y in his own "Purple" collection, hidden from render until the story needs him. `--still` renders `renders/purple.png` and `renders/purple_back.png` with everything else hidden; `--save` writes the blend.
- The blend's image textures are re-pointed to the repo's `textures/` folder, relative to the blend, whenever their absolute path no longer exists (they were saved from another checkout and rendered magenta here).

### Fixed
- `rig_utils.clone_character` now also resets the clone's quaternion rotation. Yellow's rig is keyed in quaternion mode mid-tumble, so a clone made during draft 2 came out tilted.

## 2026-09-07 - Draft 2, beat 5: the trip and the claw

### Added
- `build_draft2_beat5.py` (frames 913-1080): Yellow backs away from the monster step by step, arms up, eyes on it (the walk cycle run backwards). One slat from the burst flew further than the rest, right over his head, and landed behind him; his trailing foot catches it, the leg hooks, the arms windmill and he goes over backwards onto his back with a bounce. He props up on his elbows, looks at the monster, and shoves himself back twice with his heels. The monster comes on with a heavy lumbering walk (short thick legs, the body rolling, arms hunched, tail swinging, jaw open, eyes on him) and the ground thumps under each stomp; it stops over him, leans in, and reaches down with its claw open so the claw hangs right over him, fingers flexing, jaw working, and Yellow crosses his arms over his face and trembles. Shots: a side tracking shot with the monster coming in from the right; a low shot behind his feet so he falls toward the lens with a landing shake; from the ground behind his head with the monster coming at the lens, each stomp thumping the camera; a side shot of the reach; and a low shot from the monster's side of his face and crossed arms with the claw coming down between.
- `render_draft2.py` now renders to frame 1080 with the new cues: Yellow's landing thump, ten stomps, and a low growl. It keeps the raw render, and `--from N` renders only frames N onward and splices them onto it, so a new beat no longer means re-rendering everything.

### Fixed
- The crate builder baked the part sizes with a scale apply, which zeroed every part's location and its stored rest transform, so in the burst the base flew apart with the rest. Sizes are now baked into the mesh directly; the base stays and the monster stands on it.

## 2026-09-07 - Draft 2, beat 4: the crate and the monster

### Added
- `build_monster.py`: a big monster built the same way as Yellow (one connected Skin-modifier body from a joint skeleton, subdivided, with a generated armature) so it lives in the same world. About 12 studs tall: a broad chest, heavy muzzle with an underbite and two tusks, six teeth, nostrils, small curved horns, glowing amber eyes with slit pupils, long gorilla arms with three claws each, short thick legs with clawed feet, a thick tail and a row of spikes down the back. Deep teal skin with a paler belly and a little bump. Bones are named like Yellow's (plus `jaw`, `snout`, `tail.001-003`) so the same Poser drives it.
- `build_crate.py`: one big breakable crate (7.5 studs): corner posts, six slats a side, base and lid boards, diagonal braces, iron corner brackets and bolts, all parented to the `Crate` empty and each remembering its resting transform so the beat script can scatter them.
- `build_draft2_beat4.py` (frames 497-912): Yellow turns to face front and says "I will walk around to find clues" (talking mouth per syllable, a hand-up then point-across gesture, head level), walks off, hears a whistle and stops; the camera drops behind his shoulder with a wide lens and tilts up to a crate falling out of the sky, his crown at the bottom of frame, following it down. He turns and runs (arm swing, lean, ground clamp) and the crate slams down where he stood while he is still running, with a camera shake, in one wide side shot that holds both. He slows, stops, turns around and sees it. The crate creaks and shudders, then bursts: every part above the base flies out from the centre, tumbles under gravity and lands on the plate; the base stays. The monster is inside, crouched and folded small, and unfolds to its full height over two seconds, then rears back and roars with its jaw wide, arms up and a tremor through it, and settles into a hunched, jaw-open stance, breathing, tail swaying. Yellow flinches back with his arms up and keeps his eyes on it. Shots: the line (medium front), the walk (side tracking), the look-up (low, behind, wide lens), the run (wide side), the stop and turn (medium), over his shoulder for the burst and the rise, a low angle up at the roar, and a wide two-shot to end.
- `render_draft2.py` now renders to frame 912 with the new subtitle and cues: the crate's falling whistle, a heavy wooden slam, the creak, the splintering crash and the roar, all synthesised.

### Changed
- The parked jetski is hidden from render for this beat (it is not in the story yet).

## 2026-09-07 - Flying jetski

### Added
- The hover-screen is now a working device, so characters can use it in the story. `make_hud.py` models a phone-like UI and renders it as an image sequence from a timeline of events (tap a named button, type text, go back). The craft is now called NIMBUS (one constant to rename it). Home screen: status bar, a clock with a blinking colon, a live speed and altitude widget (tap it to open Drive), a 3x4 grid of app icons with labels and an unread badge, and a dock. Every button works: a tap ripples and the tile presses in, the app grows and fades in over the home screen, Back returns. Apps, each with its own animation: Drive (the full gauge, altitude bar, radar sweep, power cells, BOOST and AUTOPILOT toggles that change the readouts), Map (numbered tile grid, pulsing craft marker, a crawling dashed route to a bobbing pin, GO starts navigation with a counting ETA and progress), Messages (a chat with Blue: bubbles, a keyboard whose keys light as text is typed, Send posts the bubble, typing dots and a reply come back), Calls (contact list, a live call with pulsing rings, Calling dots, a connected timer and a voice waveform, End), Music (spinning album disc, progress bar, equaliser, Play/Pause, Next changes track), Camera (viewfinder with a wandering focus square, Shutter flashes and pops a thumbnail; the photo count grows), Photos (grid of little scenes), Weather (sun with turning rays, drifting cloud, five-day forecast), Notes (list plus a note that types), Shop (items with Buy that flips to Bought), Settings (toggles that slide, craft info), Games (Tile Runner: a weaving craft dodging scrolling blocks with a score), and a Lock screen (tap to unlock).
- `python make_hud.py demo` renders a 62-second demo of someone using every app to `textures/hud_demo/`; `renders/hover_screen_demo.mp4` is that demo as a video. Story scripts call `make_hud.render(events, out_dir, frames)` with their own event list and point the panel at that folder.
- `build_hovercraft.py` reads the sequence length from the HUD folder and reloads the image so a re-rendered sequence shows straight away.
- `make_hud.py`: draws the jetski's holographic HUD as a 72-frame looping image sequence (`textures/hud/`), 540x800 portrait on a transparent background, drawn at 2x and downsampled: a callsign header with a pulsing HOVER light, a speed gauge with ticks, needle and a big readout, an altitude bar, a radar with a fading sweep and blips, six power cells, a status ticker and a scan line.
- `renders/hovercraft_dash.png`: the rider's view of the dash, hologram and hover-screen.

### Changed
- The screen is no longer a tablet-like block. It is a hover-screen: a translucent panel with no bezel or housing that floats above the dash behind the hologram, projected from a lit chrome slot in the shelf through a faint light wedge. It shows the animated HUD sequence (emission with alpha, so only the drawn elements glow), drifts and tilts very slightly so it reads as a projection, faces the rider (mirrored UVs so the text reads from the seat) and sits high enough that the hologram globe and handlebars stay below it.
- The console screen is now a tall upright panel facing the rider, raised so the handlebars sit below it, and it is live: five readout bars rise and fall on their own rhythms, a scan line sweeps up and down the panel, a ring glyph turns, and the panel's glow pulses, all keyed across the scene.
- Reads as a flying vehicle now: the V bottom is replaced by a nearly flat underside carrying six anti-grav pods in three pairs (dark drums with neon rings and glowing cores) plus a smaller one under the bow, neon purple lines run the full length of both chines, swept winglets with lit edges sit at the rear quarters, the thruster core is brighter with a translucent exhaust glow, and it hovers higher, about 2.7 studs off the plate.
- Cleaned up: the seating is one low sculpted piece (rider cushion, a backrest rising out of it, a dip, a passenger cushion and a lower rear backrest, purple tops and black sides), and the bolted-on clutter is gone: mirrors, hood vents, seat trims and backrest strips removed so nothing reads as shapes dropped onto each other.
- Seating: the saddle is replaced by a rider seat with a padded, leaning backrest on a black frame with a light strip, and a raised passenger seat behind it with its own backrest at the stern; black trims along both.
- Handlebars redesigned: a chamfered stem on a chrome base, a black yoke with a lit slot and chrome cap, and winged arms swept forward and angled down to purple grips with lit tips and blade-style levers.
- The console is one integrated dash housing that rises out of the hood: a hologram projector set into its front shelf (chrome ring, purple emitter disc, a faint light cone and a slowly turning wireframe globe with a bright core), a screen block rising behind and above it with the display angled up at the rider, the handlebar stem anchored into the back of the shelf on a chrome base, mirrors on arms bolted to the housing sides, and the windshield frame seated on the housing's front lip. Nothing floats.
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
