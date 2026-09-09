# Drafts

Each draft of the episode is archived under `drafts/` and tagged in git, so
it can be checked out whole. The working scene in `slimsico.blend` is
cleared between drafts: Yellow on the grid, no animation.

## Draft 1 - the crates (2026-09-05 to 2026-09-06)

Tag `draft-1`. Files in `drafts/draft-1/`:

- `episode.mp4` - the final draft-1 render, 23.4 s, 1080p, subtitles and sound.
- `build_opening.py` - frames 1-150: fall from the sky, belly-flop, get up.
- `build_props.py` - two detailed crates, one with logs.
- `build_continue.py` - frames 151-561: hands, "Where am I?", walk, whistle, look up, run, slow, turn back.
- `render_episode.py` - headless render with subtitle and synthesised sound.

The scripts import `rig_utils.py` from the repo root and expect the character
from `build_character.py`; to rebuild the draft, copy them back to the root or
check out the tag.

What it was:

1. Yellow drops out of a clear sky, tumbling, and belly-flops onto the grid.
2. He pushes up onto hands and knees, crouches, and stands.
3. He looks at his hands, lifts his head, and says "Where am I?".
4. He walks off. A falling whistle: he looks up, tracks a crate down the sky,
   bolts. Two crates thud down behind him. He slows, turns back, and sees them.

What was learned (carry into draft 2):

- Head animation must be sparse and deliberate: one held look at a time, no
  nods, no left-right scanning, no head bob in walks or runs.
- To make him look at something, aim his face, not the head bone.
- Get-ups use hands and feet; nothing rotates into place.
- Nothing may dip below the floor; check every frame. Smooth the ground clamp
  but never below contact.
- Run cycle: bent elbows swinging with the legs, forearms not held forward.
- Cause and effect for props: sound, look, react, then the event lands.
- Balance render lighting for the yellow (neutral world, soft warm sun).

## Draft 2 - in progress (from 2026-09-06)

Working scripts at the repo root: `build_draft2.py`, `render_draft2.py`. Uses the redesigned Yellow.

Beats so far:

1. The baseplate, peaceful. A sound from above. The camera tilts up and finds Yellow far up in the sky, rolling as he falls.
2. The fall accelerates, the camera follows him down to the plate, and he belly-flops with a squash, a bounce and a slide, then lies still.
3. He gets up with his arms, rubs his left arm looking down at it, then the head lifts, he says "Where am I?" with a shrug and a moving mouth in a medium shot, and turns slowly as the camera pulls back to reveal the deserted plate.
4. "I will walk around to find clues." He walks off, a crate falls out of the sky, he runs, it slams down, bursts, and the monster rises and roars.
5. He backs away, trips over a plank, lands on his back and scoots; the monster stomps over and reaches down, its claw over him.
6. Purple swoops in on the jetski, holds out a hand; "Who are you?"; Yellow grabs it, dangles as they climb, slips, is caught one-handed and hauled onto the seat. "Where are we going?" ... "Hello, are you going to answer me?" "You're not much of a talker, are you?" Purple never speaks.
7. Lime falls out of the sky ahead of the jetski, which flies under him perfectly; he lands on the rail, hangs off the side, climbs on and sits on it. "What, how did you get on here?" "What the hell... is going on!" "I don't know any more than you." "What about you, Purple, do you know?" "He's not really much of a talker." "Ughhh. Anyways, what are your guys' names?" "Uhhhhhhhh... I guess Yellow. And just call this other guy Purple. How about you, what is your name?" He looks at his arm: "Lime."
