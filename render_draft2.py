"""Renders draft 2 headless and mixes the sound: a soft wind bed, the falling
whistle from above, and any later cues; an ambient music track is mixed in
quietly if one is placed at audio/ambient.* .

  python render_draft2.py            -> renders/draft2.mp4

Needs ffmpeg on PATH. Pass --no-render to only redo the sound pass, or
--from N to render only frames N..end and splice them onto the kept raw render.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FONT = "C:/Windows/Fonts/arialbd.ttf"
MUSIC = next((p for p in (os.path.join(ROOT, "audio", "ambient" + ext) for ext in (".mp3", ".ogg", ".wav", ".m4a"))
              if os.path.exists(p)), None)
FPS = 24

# frames match build_draft2.py and build_draft2_beat4.py / beat5 / beat6
F_END = 1656
F_ADV, F_LOOM = 914, 1030
SUBTITLES = [("Where am I?", 412, 452), ("I will walk around to find clues", 504, 558),
             ("Who are you?", 1166, 1196), ("Where are we going?", 1392, 1430),
             ("Hello, are you going to answer me?", 1502, 1562), ("You’re not much of a talker, are you?", 1578, 1636)]   # a typographic apostrophe: a plain one breaks drawtext quoting
SOUND_CUES = [("wind", 1), ("whistle", 60), ("splat", 190),
              ("crate_whistle", 612), ("thud", 700), ("creak", 768), ("crash", 784), ("roar", 840),
              ("thump", 980), ("growl", 1030),
              ("swoop", 1081), ("hover", 1118), ("lift", 1236), ("climb", 1284), ("slip", 1300), ("catch", 1306)] + [("stomp", f) for f in range(F_ADV + 6, F_LOOM, 11)]
SOUNDS = {
    # a long, faint whistle from far above that slides down and grows as he nears
    "whistle": ("0.2*sin(2*PI*(1700-600*t/5.4)*t)*min(1\\,t/2.5)*(0.3+0.7*t/5.4)", 5.4),
    # the belly-flop: a slap of noise with a soft body thump
    "splat": ("0.85*exp(-t*20)*(random(0)-0.5)+0.5*exp(-t*8)*sin(2*PI*70*t)", 0.7),
    # the crate: a falling-object whistle over the 3.7 s drop, growing as it nears
    "crate_whistle": ("0.24*sin(2*PI*(1600-900*t/3.7)*t)*min(1\\,t*2)*(0.3+0.7*t/3.7)", 3.7),
    # a heavy wooden slam: deep thump with a sharp crack, and a little rumble after
    "thud": ("1.0*exp(-t*9)*sin(2*PI*45*t)+0.45*exp(-t*35)*(random(0)-0.5)+0.2*exp(-t*3)*sin(2*PI*30*t)", 1.2),
    # the crate creaking and straining before it goes
    "creak": ("0.3*sin(2*PI*(160+50*sin(2*PI*2.5*t))*t)*(0.55+0.45*sin(2*PI*3*t))*min(1\\,t*4)*exp(-t*1.2)", 1.5),
    # the burst: splintering wood, a crack of noise with a thump underneath
    "crash": ("0.95*exp(-t*5)*(random(0)-0.5)+0.5*exp(-t*9)*sin(2*PI*58*t)", 1.4),
    # the roar: a low growl with a rasp that swells, wavers and trails off
    "roar": ("0.75*sin(2*PI*(68+14*sin(2*PI*4.5*t))*t)*(1+0.5*sin(2*PI*31*t))*min(1\\,t*4)*exp(-t*0.8)+0.3*exp(-t*1.1)*min(1\\,t*4)*(random(0)-0.5)", 2.0),
    # Yellow landing on his back: a soft body thump
    "thump": ("0.6*exp(-t*16)*sin(2*PI*80*t)+0.3*exp(-t*30)*(random(0)-0.5)", 0.5),
    # the monster's footfalls: a deep stomp with a little grit
    "stomp": ("0.7*exp(-t*14)*sin(2*PI*38*t)+0.2*exp(-t*40)*(random(0)-0.5)", 0.6),
    # a low rolling growl as it looms
    "growl": ("0.55*sin(2*PI*(55+8*sin(2*PI*3*t))*t)*(1+0.4*sin(2*PI*27*t))*min(1\\,t*3)*exp(-t*0.7)", 2.5),
    # the jetski diving in: a rising whine that doppler-drops as it passes, with wind rush
    "swoop": ("0.45*sin(2*PI*(900+700*t/2.0-500*max(0\\,t-1.5))*t)*min(1\\,t/0.6)*(1-t/2.2)+0.35*(random(0)-0.5)*min(1\\,t)*exp(-(t-1.6)*(t-1.6)*3)", 2.2),
    # the hover hum under the rest of the beat: a soft two-tone thrum
    "hover": ("0.11*(sin(2*PI*92*t)+0.6*sin(2*PI*138*t))*(0.85+0.15*sin(2*PI*1.3*t))*min(1\\,t/2)", 23.0),
    # the lift: the hum swells and a whoosh
    "lift": ("0.5*sin(2*PI*(110+60*t)*t)*min(1\\,t/0.8)*exp(-t*0.6)+0.25*(random(0)-0.5)*exp(-(t-0.7)*(t-0.7)*4)", 2.4),
    # climbing away: wind rush
    "climb": ("0.3*(random(0)-0.5)*min(1\\,t/0.5)*exp(-t*1.2)", 2.0),
    # the slip: a short squeak and a rush of air
    "slip": ("0.35*sin(2*PI*(1400-900*t)*t)*exp(-t*12)+0.3*(random(0)-0.5)*exp(-t*6)", 0.5),
    # the catch: a slap and a body thump
    "catch": ("0.7*exp(-t*22)*(random(0)-0.5)+0.5*exp(-t*9)*sin(2*PI*95*t)", 0.6),
}
NOISE_BEDS = {
    # soft wind: pink noise, low-passed, gently breathing
    "wind": ("anoisesrc=c=pink:a=0.06:s=48000:d=%.2f,lowpass=f=520,volume='0.75+0.25*sin(2*PI*0.11*t)':eval=frame"),
}

raw = os.path.join(RENDERS, "draft2_raw.mp4")
out = os.path.join(RENDERS, "draft2.mp4")
total = F_END / FPS
CLIP = None
if "--clip" in sys.argv:
    # render and mix only frames A..B (e.g. one beat) to renders/draft2_clip_A_B.mp4,
    # with the subtitles and cues shifted so they land at the right moment
    i = sys.argv.index("--clip")
    CLIP = (int(sys.argv[i + 1]), int(sys.argv[i + 2]))
    A, B = CLIP
    raw = os.path.join(RENDERS, "draft2_clip_raw.mp4")
    out = os.path.join(RENDERS, "draft2_clip_%d_%d.mp4" % (A, B))
    total = (B - A + 1) / FPS
    SUBTITLES = [(t, a - A + 1, b - A + 1) for t, a, b in SUBTITLES if b >= A and a <= B]
    SOUND_CUES = [(n, max(1, f - A + 1)) for n, f in SOUND_CUES if (f - A + 1) + (SOUNDS.get(n, ("", 0))[1] * FPS if n in SOUNDS else 10 ** 6) > 0 and f <= B]
    if "--no-render" not in sys.argv:
        if os.path.exists(raw):
            os.remove(raw)
        subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-S", "Scene", "-s", str(A), "-e", str(B),
                        "--python-expr", "import bpy; bpy.context.scene.render.filepath = %r" % raw.replace("\\", "/"), "-a"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

if CLIP is not None:
    pass
elif "--from" in sys.argv:
    first = int(sys.argv[sys.argv.index("--from") + 1])
    part = os.path.join(RENDERS, "draft2_raw_part.mp4")
    head = os.path.join(RENDERS, "draft2_raw_head.mp4")
    subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-S", "Scene", "-s", str(first), "-e", str(F_END),
                    "--python-expr", "import bpy; bpy.context.scene.render.filepath = %r" % part.replace("\\", "/"), "-a"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # the kept raw render up to the splice point, re-encoded so the join is clean
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-frames:v", str(first - 1), "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-an", head], check=True)
    joined = os.path.join(RENDERS, "draft2_raw_joined.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", head, "-i", part, "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]", "-map", "[v]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p", joined], check=True)
    os.replace(joined, raw)
    os.remove(head)
    os.remove(part)
elif "--no-render" not in sys.argv:
    if os.path.exists(raw):
        os.remove(raw)
    subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-S", "Scene", "-a"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

video_filters = []
for text, first, last in SUBTITLES:
    safe = text.replace("'", r"\'").replace(":", r"\:")
    video_filters.append(
        "drawtext=fontfile='%s':text='%s':fontsize=58:fontcolor=white:borderw=3:bordercolor=black"
        ":x=(w-text_w)/2:y=h-140:enable='between(t,%.3f,%.3f)'" % (FONT.replace(":", r"\:"), safe, (first - 1) / FPS, last / FPS))
video = "[0:v]" + (",".join(video_filters) if video_filters else "null") + "[vout]"

cmd = ["ffmpeg", "-v", "error", "-y", "-i", raw]
audio_filters, inputs, mix_in = [], 1, ""
for name, frame in SOUND_CUES:
    at_ms = int(round((frame - 1) / FPS * 1000))
    if name in NOISE_BEDS:
        cmd += ["-f", "lavfi", "-i", NOISE_BEDS[name] % (total + 1)]
    else:
        expr, dur = SOUNDS[name]
        cmd += ["-f", "lavfi", "-i", "aevalsrc='%s':d=%.2f:s=48000" % (expr, dur)]
    audio_filters.append("[%d:a]adelay=%d:all=1[a%d]" % (inputs, at_ms, inputs))
    mix_in += "[a%d]" % inputs
    inputs += 1
n_mix = inputs - 1
if MUSIC:
    cmd += ["-stream_loop", "-1", "-i", MUSIC]
    audio_filters.append("[%d:a]volume=0.16,atrim=0:%.2f,afade=t=in:d=1.5,afade=t=out:st=%.2f:d=2[music]" % (inputs, total, max(0, total - 2)))
    mix_in += "[music]"
    n_mix += 1
audio_filters.append("%samix=inputs=%d:normalize=0,apad[aout]" % (mix_in, n_mix))

cmd += ["-filter_complex", video + ";" + ";".join(audio_filters), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % total, out]
subprocess.run(cmd, check=True)
print("wrote", out, "%.2fs" % total, "| music:", "yes" if MUSIC else "none")
