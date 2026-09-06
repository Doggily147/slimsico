"""Renders the whole episode headless, burns the subtitle in, and adds the
sound cues (belly-flop splat, the crates' falling whistles and landing thuds),
all synthesised with ffmpeg so no sample files are needed:

  python render_episode.py            -> renders/episode.mp4

Needs ffmpeg on PATH. Pass --no-render to only redo the subtitle/sound pass.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FONT = "C:/Windows/Fonts/arialbd.ttf"
FPS = 24

# (text, first frame, last frame) - frames match build_continue.py
SUBTITLES = [
    ("Where am I?", 250, 288),
]

# (sound, frame) - frames match build_opening.py / build_continue.py
SOUND_CUES = [
    ("splat", 46),
    ("whistle", 387), ("whistle", 397),
    ("thud", 417), ("thud", 427),
]
SOUNDS = {
    # a falling-object whistle: a tone sliding down over the 1.25 s drop
    "whistle": ("0.22*sin(2*PI*(1500-800*t/1.25)*t)*min(1\\,t*6)*(1-0.45*t/1.25)", 1.25),
    # a heavy wooden thud: low sine with a short noise crack
    "thud": ("0.9*exp(-t*12)*sin(2*PI*52*t)+0.35*exp(-t*40)*(random(0)-0.5)", 0.8),
    # the belly-flop: a slap of noise with a soft body thump
    "splat": ("0.7*exp(-t*22)*(random(0)-0.5)+0.45*exp(-t*9)*sin(2*PI*75*t)", 0.6),
}

raw = os.path.join(RENDERS, "episode_raw.mp4")
out = os.path.join(RENDERS, "episode.mp4")

if "--no-render" not in sys.argv:
    if os.path.exists(raw):
        os.remove(raw)
    subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-a"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

# video: subtitles
video_filters = []
for text, first, last in SUBTITLES:
    start, end = (first - 1) / FPS, last / FPS
    safe = text.replace("'", r"\'").replace(":", r"\:")
    video_filters.append(
        "drawtext=fontfile='%s':text='%s':fontsize=58:fontcolor=white:borderw=3:bordercolor=black"
        ":x=(w-text_w)/2:y=h-140:enable='between(t,%.3f,%.3f)'" % (FONT.replace(":", r"\:"), safe, start, end))

# audio: each cue is a synthesised clip delayed to its frame, then mixed
cmd = ["ffmpeg", "-v", "error", "-y", "-i", raw]
audio_filters = []
for i, (name, frame) in enumerate(SOUND_CUES, start=1):
    expr, dur = SOUNDS[name]
    cmd += ["-f", "lavfi", "-i", "aevalsrc='%s':d=%.2f:s=48000" % (expr, dur)]
    delay_ms = int(round((frame - 1) / FPS * 1000))
    audio_filters.append("[%d:a]adelay=%d:all=1[a%d]" % (i, delay_ms, i))
mix = "".join("[a%d]" % i for i in range(1, len(SOUND_CUES) + 1))
audio_filters.append("%samix=inputs=%d:normalize=0,apad[aout]" % (mix, len(SOUND_CUES)))

filter_complex = "[0:v]" + ",".join(video_filters) + "[vout];" + ";".join(audio_filters)
cmd += ["-filter_complex", filter_complex, "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-shortest", out]
subprocess.run(cmd, check=True)
os.remove(raw)
print("wrote", out)
