"""Renders the OfficeTest scene headless and assembles the test:

  play attempt 1 -> REWIND (the footage since the gun came up, reversed and
  sped up with a VHS look) -> attempt 2 -> REWIND -> attempt 3

with subtitles, synthesised sound cues, and an optional ambient music bed
(put a track at audio/ambient.mp3 and it is mixed in quietly).

  python render_office_test.py            -> renders/office_test.mp4

Needs ffmpeg on PATH. Pass --no-render to only redo the assembly.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
FONT = "C:/Windows/Fonts/arialbd.ttf"
MUSIC = next((p for p in (os.path.join(ROOT, "audio", "ambient" + ext) for ext in (".mp3", ".ogg", ".wav", ".m4a"))
              if os.path.exists(p)), os.path.join(ROOT, "audio", "ambient.mp3"))
FPS = 24

# frames match build_office.py
F_END = 430
REWINDS = [(150, 200), (150, 330)]          # (rewind back to, from) in source frames
REWIND_SECONDS = (0.7, 1.0)                 # how long each rewind plays on screen
SUBTITLES = [("Hand it over.", 152, 178), ("Freeze!", 292, 318), ("WILL YOU STOP THAT?!", 380, 424)]
SOUND_CUES = [("typing", 1), ("door", 61), ("gunshot", 180), ("crash", 194),
              ("door", 246), ("siren", 246), ("yell", 378)]
SOUNDS = {
    "typing": ("0.12*exp(-mod(t\\,0.13)*90)*(random(0)-0.5)*lt(t\\,5.6)", 6.0),
    "door": ("0.25*sin(2*PI*(180+140*t)*t)*exp(-t*3)*min(1\\,t*10)", 0.7),
    "gunshot": ("0.95*exp(-t*22)*(random(0)-0.5)+0.55*exp(-t*7)*sin(2*PI*85*t)", 0.7),
    "crash": ("0.8*exp(-t*10)*sin(2*PI*48*t)+0.45*exp(-t*18)*(random(0)-0.5)", 0.9),
    "siren": ("0.22*sin(2*PI*(650+250*gt(sin(2*PI*1.4*t)\\,0))*t)*min(1\\,t*4)*(1-0.3*t/2.4)", 2.4),
    "yell": ("0.45*sin(2*PI*115*t)*(1+0.6*sin(2*PI*6.5*t))*(1+0.3*sin(2*PI*230*t))*exp(-t*1.6)*min(1\\,t*20)", 1.4),
    "rewind": ("0.3*sin(2*PI*(200+900*t)*t)*(1-t)*min(1\\,t*15)", 1.0),
}

raw = os.path.join(RENDERS, "office_raw.mp4")
out = os.path.join(RENDERS, "office_test.mp4")


def sec(frame):
    return (frame - 1) / FPS


if "--no-render" not in sys.argv:
    if os.path.exists(raw):
        os.remove(raw)
    subprocess.run([BLENDER, "-b", os.path.join(ROOT, "slimsico.blend"), "-S", "OfficeTest", "-a"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

# ------------------------------------------------------------ video timeline
# Source segments and the rewinds in between. `offset(frame)` maps a source
# frame to its time in the assembled video so sound and subtitles line up.
segments = []          # (kind, start_sec, end_sec, playback_seconds)
cursor = 1
for (back_to, frm), length in zip(REWINDS, REWIND_SECONDS):
    segments.append(("play", sec(cursor), sec(frm + 1), sec(frm + 1) - sec(cursor)))
    segments.append(("rewind", sec(back_to), sec(frm + 1), length))
    cursor = frm + 1
segments.append(("play", sec(cursor), sec(F_END + 1), sec(F_END + 1) - sec(cursor)))


def offset(frame):
    """Assembled-video time of a source frame (first occurrence after cursor logic)."""
    t_out = 0.0
    for kind, a, b, length in segments:
        if kind == "play":
            if a <= sec(frame) < b:
                return t_out + (sec(frame) - a)
            t_out += length
        else:
            t_out += length
    return t_out


def subtitle_filter(text, start, end):
    safe = text.replace("'", r"\'").replace(":", r"\:")
    return ("drawtext=fontfile='%s':text='%s':fontsize=58:fontcolor=white:borderw=3:bordercolor=black"
            ":x=(w-text_w)/2:y=h-140:enable='between(t,%.3f,%.3f)'" % (FONT.replace(":", r"\:"), safe, start, end))


parts, labels = [], []
for i, (kind, a, b, length) in enumerate(segments):
    if kind == "play":
        parts.append("[0:v]trim=start=%.4f:end=%.4f,setpts=PTS-STARTPTS[s%d]" % (a, b, i))
    else:
        speed = (b - a) / length
        parts.append("[0:v]trim=start=%.4f:end=%.4f,setpts=PTS-STARTPTS,reverse,setpts=PTS/%.4f,"
                     "hue=s=0.35,noise=alls=28:allf=t+u,"
                     "drawtext=fontfile='%s':text='<< REWIND':fontsize=64:fontcolor=white:borderw=3:bordercolor=black:x=w-text_w-70:y=60"
                     "[s%d]" % (a, b, speed, FONT.replace(":", r"\:"), i))
    labels.append("[s%d]" % i)
concat = "%sconcat=n=%d:v=1:a=0[cat]" % ("".join(labels), len(labels))
subs = ",".join(subtitle_filter(text, offset(first), offset(last) + 1 / FPS) for text, first, last in SUBTITLES)
video = ";".join(parts + [concat, "[cat]" + subs + "[vout]"])

# ------------------------------------------------------------ audio
cmd = ["ffmpeg", "-v", "error", "-y", "-i", raw]
audio_filters, inputs = [], 1
cues = [(name, offset(frame)) for name, frame in SOUND_CUES]
t_out = 0.0
for kind, a, b, length in segments:            # a whoosh at each rewind
    if kind == "rewind":
        cues.append(("rewind", t_out))
    t_out += length
total = t_out
for name, at in cues:
    expr, dur = SOUNDS[name]
    cmd += ["-f", "lavfi", "-i", "aevalsrc='%s':d=%.2f:s=48000" % (expr, dur)]
    audio_filters.append("[%d:a]adelay=%d:all=1[a%d]" % (inputs, int(round(at * 1000)), inputs))
    inputs += 1
mix_in = "".join("[a%d]" % i for i in range(1, inputs))
n_mix = inputs - 1
if os.path.exists(MUSIC):
    cmd += ["-stream_loop", "-1", "-i", MUSIC]
    audio_filters.append("[%d:a]volume=0.18,atrim=0:%.2f,afade=t=out:st=%.2f:d=2[music]" % (inputs, total, max(0, total - 2)))
    mix_in += "[music]"
    n_mix += 1
audio_filters.append("%samix=inputs=%d:normalize=0,apad[aout]" % (mix_in, n_mix))

cmd += ["-filter_complex", video + ";" + ";".join(audio_filters), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % total, out]
subprocess.run(cmd, check=True)
os.remove(raw)
print("wrote", out, "%.2fs" % total, "| music:", "yes" if os.path.exists(MUSIC) else "none (put a track at audio/ambient.mp3)")
