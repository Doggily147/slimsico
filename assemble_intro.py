"""Renders the orbit angles as separate clips and stitches the intro together:

  opening.mp4 -(0.6 s dissolve)- orbit A -(0.35 s)- orbit B -(0.35 s)- orbit C

Needs slimsico.blend with both scenes keyed (build_opening.py then
build_orbit.py) and ffmpeg/ffprobe on PATH. Pass --no-render to only stitch.

  python assemble_intro.py            -> renders/intro.mp4
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
SEGMENTS = [("orbit_a", 193, 216), ("orbit_b", 217, 240), ("orbit_c", 241, 264)]
DISSOLVE_IN, DISSOLVE_CUT = 0.6, 0.35


def render_segments():
    for name, start, end in SEGMENTS:
        prefix = os.path.join(RENDERS, name + "_")
        subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"),
                        "-s", str(start), "-e", str(end), "-o", prefix, "-a"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        # Blender appends the frame range to video names; keep a stable name.
        produced = sorted(glob.glob(prefix + "*.mp4"))
        if not produced:
            raise SystemExit("no output for " + name)
        shutil.move(produced[-1], os.path.join(RENDERS, name + ".mp4"))


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def stitch():
    clips = [os.path.join(RENDERS, "opening.mp4")] + [os.path.join(RENDERS, n + ".mp4") for n, _, _ in SEGMENTS]
    fades = [DISSOLVE_IN] + [DISSOLVE_CUT] * (len(SEGMENTS) - 1)
    filters, total = [], duration(clips[0])
    for i, (clip, fade) in enumerate(zip(clips[1:], fades), start=1):
        src = "[0:v]" if i == 1 else "[v%d]" % (i - 1)
        offset = total - fade
        filters.append("%s[%d:v]xfade=transition=fade:duration=%.3f:offset=%.3f[v%d]" % (src, i, fade, offset, i))
        total = offset + duration(clip)
    out = os.path.join(RENDERS, "intro.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for c in clips:
        cmd += ["-i", c]
    cmd += ["-filter_complex", ";".join(filters), "-map", "[v%d]" % (len(clips) - 1),
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", out]
    subprocess.run(cmd, check=True)
    print("wrote", out, "%.2fs" % total)


if __name__ == "__main__":
    if "--no-render" not in sys.argv:
        render_segments()
    stitch()
