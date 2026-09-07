"""Renders draft 2 headless and mixes the sound: a soft wind bed, the falling
whistle from above, and any later cues; an ambient music track is mixed in
quietly if one is placed at audio/ambient.* .

  python render_draft2.py            -> renders/draft2.mp4

Needs ffmpeg on PATH. Pass --no-render to only redo the sound pass.
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

# frames match build_draft2.py
F_END = 460
SUBTITLES = [("Where am I?", 410, 452)]
SOUND_CUES = [("wind", 1), ("whistle", 60), ("splat", 190)]
SOUNDS = {
    # a long, faint whistle from far above that slides down and grows as he nears
    "whistle": ("0.2*sin(2*PI*(1700-600*t/5.4)*t)*min(1\\,t/2.5)*(0.3+0.7*t/5.4)", 5.4),
    # the belly-flop: a slap of noise with a soft body thump
    "splat": ("0.85*exp(-t*20)*(random(0)-0.5)+0.5*exp(-t*8)*sin(2*PI*70*t)", 0.7),
}
NOISE_BEDS = {
    # soft wind: pink noise, low-passed, gently breathing
    "wind": ("anoisesrc=c=pink:a=0.06:s=48000:d=%.2f,lowpass=f=520,volume='0.75+0.25*sin(2*PI*0.11*t)':eval=frame"),
}

raw = os.path.join(RENDERS, "draft2_raw.mp4")
out = os.path.join(RENDERS, "draft2.mp4")
total = F_END / FPS

if "--no-render" not in sys.argv:
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
os.remove(raw)
print("wrote", out, "%.2fs" % total, "| music:", "yes" if MUSIC else "none")
