"""Draws the jetski's holographic HUD as a looping image sequence
(textures/hud/hud_0001.png ... hud_0072.png, 3 s at 24 fps): a portrait panel
with a speed gauge, altitude bar, a radar sweep with blips, power cells, a
status readout and a scan line. Transparent background so the panel reads as
a projection. Drawn at 2x and downsampled for clean anti-aliasing.

  python make_hud.py
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

FRAMES = 72
W, H = 540, 800
S = 2                                   # supersample
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures", "hud")
os.makedirs(OUT, exist_ok=True)

BG = (30, 10, 60, 105)
PANEL = (60, 20, 110, 70)
PURPLE = (210, 120, 255, 255)
LILAC = (235, 200, 255, 255)
DIM = (150, 90, 210, 170)
CYAN = (140, 230, 255, 255)
WHITE = (255, 255, 255, 255)

bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30 * S)
big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 84 * S)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20 * S)
tiny = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16 * S)


def frame(i):
    t = i / FRAMES
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = 18 * S
    d.rounded_rectangle([m, m, W * S - m, H * S - m], radius=26 * S, fill=BG, outline=PURPLE, width=3 * S)
    # corner brackets
    for cx, cy, sx, sy in ((m, m, 1, 1), (W * S - m, m, -1, 1), (m, H * S - m, 1, -1), (W * S - m, H * S - m, -1, -1)):
        d.line([(cx, cy + sy * 46 * S), (cx, cy), (cx + sx * 46 * S, cy)], fill=LILAC, width=6 * S)
    # header
    d.text((40 * S, 34 * S), "YELLOW-07", font=bold, fill=LILAC)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t * 2)
    d.ellipse([440 * S, 40 * S, 460 * S, 60 * S], fill=(int(120 + 135 * pulse), int(230), 255, 255))
    d.text((360 * S, 40 * S), "HOVER", font=small, fill=CYAN)
    d.line([(40 * S, 78 * S), (500 * S, 78 * S)], fill=DIM, width=2 * S)

    # speed gauge: an arc with ticks and a needle
    cx, cy, r = 270 * S, 250 * S, 150 * S
    d.arc([cx - r, cy - r, cx + r, cy + r], start=150, end=390, fill=DIM, width=10 * S)
    speed = 0.5 + 0.5 * math.sin(2 * math.pi * t) * math.cos(2 * math.pi * t * 0.5)
    d.arc([cx - r, cy - r, cx + r, cy + r], start=150, end=150 + 240 * speed, fill=PURPLE, width=10 * S)
    for k in range(13):
        a = math.radians(150 + 20 * k)
        inner = r - (24 if k % 3 == 0 else 14) * S
        d.line([(cx + inner * math.cos(a), cy + inner * math.sin(a)), (cx + (r - 6 * S) * math.cos(a), cy + (r - 6 * S) * math.sin(a))],
               fill=LILAC, width=(3 if k % 3 == 0 else 2) * S)
    a = math.radians(150 + 240 * speed)
    d.line([(cx, cy), (cx + (r - 30 * S) * math.cos(a), cy + (r - 30 * S) * math.sin(a))], fill=WHITE, width=5 * S)
    d.ellipse([cx - 12 * S, cy - 12 * S, cx + 12 * S, cy + 12 * S], fill=LILAC)
    val = "%d" % int(8 + 74 * speed)
    tw = d.textlength(val, font=big)
    d.text((cx - tw / 2, cy + 30 * S), val, font=big, fill=WHITE)
    d.text((cx - 28 * S, cy + 118 * S), "km/h", font=small, fill=CYAN)

    # altitude bar
    d.text((40 * S, 420 * S), "ALT", font=small, fill=CYAN)
    d.rounded_rectangle([40 * S, 448 * S, 500 * S, 470 * S], radius=8 * S, fill=PANEL, outline=DIM, width=2 * S)
    alt = 0.55 + 0.08 * math.sin(2 * math.pi * t * 1.3)
    d.rounded_rectangle([42 * S, 450 * S, int((42 + 456 * alt) * S), 468 * S], radius=7 * S, fill=PURPLE)
    d.text((440 * S, 420 * S), "%.1f m" % (2.2 + 1.2 * alt), font=small, fill=LILAC)

    # radar with a sweep and blips
    rx, ry, rr = 130 * S, 610 * S, 90 * S
    d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=PANEL, outline=DIM, width=2 * S)
    d.ellipse([rx - rr // 2, ry - rr // 2, rx + rr // 2, ry + rr // 2], outline=DIM, width=1 * S)
    d.line([(rx - rr, ry), (rx + rr, ry)], fill=DIM, width=1 * S)
    d.line([(rx, ry - rr), (rx, ry + rr)], fill=DIM, width=1 * S)
    sweep = 2 * math.pi * t
    for k in range(18):
        a = sweep - k * 0.05
        alpha = int(200 * (1 - k / 18))
        d.line([(rx, ry), (rx + rr * math.cos(a), ry + rr * math.sin(a))], fill=(200, 120, 255, alpha), width=3 * S)
    for bx, by in ((0.5, -0.3), (-0.4, 0.55), (0.2, 0.7)):
        px, py = rx + bx * rr, ry + by * rr
        d.ellipse([px - 5 * S, py - 5 * S, px + 5 * S, py + 5 * S], fill=CYAN)
    d.text((rx - 34 * S, ry + rr + 10 * S), "RADAR", font=tiny, fill=CYAN)

    # power cells
    d.text((270 * S, 520 * S), "POWER", font=small, fill=CYAN)
    for k in range(6):
        level = 0.7 + 0.3 * math.sin(2 * math.pi * t * (0.8 + 0.2 * k) + k)
        x0 = (270 + k * 40) * S
        d.rounded_rectangle([x0, 550 * S, x0 + 30 * S, 690 * S], radius=6 * S, fill=PANEL, outline=DIM, width=2 * S)
        d.rounded_rectangle([x0 + 3 * S, int((690 - 137 * level) * S), x0 + 27 * S, 687 * S], radius=5 * S, fill=PURPLE)
    # status lines
    ticker = ["GRAV LOCK  OK", "THRUST  NOMINAL", "NAV  33 : 32", "SHIELD  ---"]
    for k, line in enumerate(ticker):
        d.text((40 * S, (712 + k * 20) * S), line, font=tiny, fill=LILAC if k != int(t * 4) % 4 else WHITE)
    # scan line
    y = m + (H * S - 2 * m) * ((t * 2) % 1.0)
    d.line([(m + 6 * S, y), (W * S - m - 6 * S, y)], fill=(255, 255, 255, 90), width=2 * S)
    return img.resize((W, H), Image.LANCZOS)


for i in range(FRAMES):
    frame(i).save(os.path.join(OUT, "hud_%04d.png" % (i + 1)), optimize=True)
print("wrote", FRAMES, "frames to", OUT)
