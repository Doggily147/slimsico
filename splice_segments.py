"""Replace frame ranges of the finished renders/draft2.mp4 with freshly rendered
segments, burning in the subtitles that fall inside them, and keep the sound.

  python splice_segments.py renders/seg/seg_1236_1261.mp4 renders/seg/seg_2135_2504.mp4 ...

Each segment file is named seg_A_B.mp4 and covers frames A..B (inclusive) of
the timeline, rendered raw (no subtitles). The subtitle list and style come
from render_draft2.py. Run render_draft2.py --remix afterwards if the sound
needs rebuilding too.
"""
import ast
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
FPS = 24
FONT = "C:/Windows/Fonts/arialbd.ttf"
FINAL = os.path.join(RENDERS, "draft2.mp4")

src = open(os.path.join(ROOT, "render_draft2.py"), encoding="utf-8").read()
tree = ast.parse(src)
SUBTITLES = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "SUBTITLES" for t in node.targets):
        SUBTITLES = ast.literal_eval(node.value)
        break
assert SUBTITLES, "no SUBTITLES in render_draft2.py"

segs = []
for path in sys.argv[1:]:
    m = re.search(r"seg_(\d+)_(\d+)\.mp4$", path)
    assert m, path
    segs.append((int(m.group(1)), int(m.group(2)), os.path.abspath(path)))
segs.sort()
total_frames = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                                            "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", FINAL]).decode().strip())


def drawtext(text, t0, t1):
    safe = text.replace("'", "\u2019").replace(":", r"\:")
    return ("drawtext=fontfile='%s':text='%s':fontsize=58:fontcolor=white:borderw=3:bordercolor=black"
            ":x=(w-text_w)/2:y=h-140:enable='between(t,%.3f,%.3f)'" % (FONT.replace(":", r"\:"), safe, t0, t1))


inputs = ["-i", FINAL]
filters, labels = [], []
cursor = 1                                             # next timeline frame not yet placed
n = 0
for idx, (a, b, path) in enumerate(segs):
    if a > cursor:                                     # kept stretch from the finished video
        filters.append("[0:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS[k%d]" % (cursor - 1, a - 1, n))
        labels.append("[k%d]" % n); n += 1
    inputs += ["-i", path]
    subs = [drawtext(t, (max(s0, a) - a) / FPS, (min(s1, b) - a + 1) / FPS) for t, s0, s1 in SUBTITLES if s1 >= a and s0 <= b]
    chain = ",".join(subs) if subs else "null"
    filters.append("[%d:v]%s,setpts=PTS-STARTPTS[s%d]" % (idx + 1, chain, n))
    labels.append("[s%d]" % n); n += 1
    cursor = b + 1
if cursor <= total_frames:
    filters.append("[0:v]trim=start_frame=%d,setpts=PTS-STARTPTS[k%d]" % (cursor - 1, n))
    labels.append("[k%d]" % n); n += 1
filters.append("%sconcat=n=%d:v=1:a=0[v]" % ("".join(labels), len(labels)))

out = os.path.join(RENDERS, "draft2_spliced.mp4")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "0:a",
       "-c:v", "h264_nvenc", "-preset", "p6", "-rc", "vbr", "-cq", "20", "-b:v", "0", "-pix_fmt", "yuv420p", "-c:a", "copy", out]
subprocess.run(cmd, check=True)
os.replace(out, FINAL)
print("spliced", len(segs), "segments into", FINAL, "| frames", total_frames)
