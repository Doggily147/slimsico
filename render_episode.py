"""Renders the whole episode (frames 1-450) headless and burns the subtitle in:

  python render_episode.py            -> renders/episode.mp4

Needs ffmpeg on PATH. Pass --no-render to only redo the subtitle pass.
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

raw = os.path.join(RENDERS, "episode_raw.mp4")
out = os.path.join(RENDERS, "episode.mp4")

if "--no-render" not in sys.argv:
    if os.path.exists(raw):
        os.remove(raw)
    subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-a"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

filters = []
for text, first, last in SUBTITLES:
    start, end = (first - 1) / FPS, last / FPS
    safe = text.replace("'", r"\'").replace(":", r"\:")
    filters.append(
        "drawtext=fontfile='%s':text='%s':fontsize=58:fontcolor=white:borderw=3:bordercolor=black"
        ":x=(w-text_w)/2:y=h-140:enable='between(t,%.3f,%.3f)'" % (FONT.replace(":", r"\:"), safe, start, end))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", ",".join(filters),
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
os.remove(raw)
print("wrote", out)
