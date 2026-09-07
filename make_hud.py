"""The jetski's hover-screen: a working, scriptable device UI rendered as an
image sequence for the holographic panel (540x800 portrait, 24 fps,
transparent background so it reads as a projection, drawn at 2x and
downsampled).

It behaves like a phone. There is a home screen with a status bar, a clock, a
live speed widget, an app grid and a dock, and every button works: a timeline
of events (tap this button, type this text, go back) drives a small device
model whose screens open, animate and respond. Each app has its own animated
screen: Drive (full gauge, altitude, radar, power), Map (route to a tile,
navigation), Messages (a chat with a keyboard that types), Calls (contacts and
a live call), Music (now playing with an equaliser), Camera (viewfinder and
shutter), Photos, Weather, Notes, Shop, Settings (toggles), Games, and a lock
screen.

  python make_hud.py             idle home screen, 72-frame loop -> textures/hud/
  python make_hud.py demo        a demo of someone using every app -> textures/hud_demo/

Story scripts import this module and call render(events, out_dir, frames)
with their own event list, e.g.
    [(30, "tap", "Messages"), (60, "type", "on my way"), (96, "tap", "Send"),
     (180, "tap", "Back"), (200, "tap", "Map"), (230, "tap", "GO")]
Button names are the labels drawn on screen ("Back", "Home", "Send", "GO",
"BOOST", "Play", "Shutter", "Buy", the app names, contact names, and
"Toggle:<setting>"). Change NAME to rename the craft.
"""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

NAME = "NIMBUS"
FPS = 24
W, H = 540, 800
S = 2                                   # supersample
ROOT = os.path.dirname(os.path.abspath(__file__))

BG = (30, 10, 60, 110)
CARD = (70, 30, 125, 120)
CARD_SOLID = (60, 22, 110, 200)
TILE = (120, 60, 200, 175)
PURPLE = (210, 120, 255, 255)
LILAC = (235, 200, 255, 255)
DIM = (150, 90, 210, 170)
CYAN = (140, 230, 255, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 90, 120, 255)
GREEN = (120, 240, 170, 255)

FONT_B = "C:/Windows/Fonts/arialbd.ttf"
FONT_R = "C:/Windows/Fonts/arial.ttf"
_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_B if bold else FONT_R, size * S)
    return _fonts[key]


# ---- drawing helpers in logical 540x800 units -------------------------------
class Canvas:
    def __init__(self):
        self.img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def rr(self, box, radius, **kw):
        self.d.rounded_rectangle([v * S for v in box], radius=radius * S, **kw)

    def ell(self, cx, cy, r, **kw):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], **kw)

    def line(self, pts, fill, width):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=width * S)

    def poly(self, pts, **kw):
        self.d.polygon([(x * S, y * S) for x, y in pts], **kw)

    def arc(self, cx, cy, r, start, end, fill, width):
        self.d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], start=start, end=end, fill=fill, width=width * S)

    def txt(self, x, y, s, size, fill=WHITE, bold=False):
        self.d.text((x * S, y * S), s, font=font(size, bold), fill=fill)

    def txtc(self, cx, y, s, size, fill=WHITE, bold=False):
        f = font(size, bold)
        tw = self.d.textlength(s, font=f) / S
        self.d.text(((cx - tw / 2) * S, y * S), s, font=f, fill=fill)

    def width(self, s, size, bold=False):
        return self.d.textlength(s, font=font(size, bold)) / S


# ---- app icon glyphs, centred on (cx, cy) inside a 64 tile --------------------
def glyph_drive(c, cx, cy, t):
    r = 20
    c.arc(cx, cy + 4, r, 150, 390, WHITE, 4)
    a = math.radians(150 + 240 * (0.5 + 0.5 * math.sin(2 * math.pi * t)))
    c.line([(cx, cy + 4), (cx + (r - 6) * math.cos(a), cy + 4 + (r - 6) * math.sin(a))], WHITE, 4)


def glyph_map(c, cx, cy, t):
    c.poly([(cx - 14, cy - 4), (cx + 14, cy - 4), (cx, cy + 22)], fill=WHITE)
    c.ell(cx, cy - 5, 15, fill=WHITE)
    c.ell(cx, cy - 5, 6, fill=TILE)


def glyph_calls(c, cx, cy, t):
    c.arc(cx, cy, 18, 110, 250, WHITE, 7)
    c.ell(cx - 6, cy - 16, 8, fill=WHITE)
    c.ell(cx - 6, cy + 16, 8, fill=WHITE)


def glyph_messages(c, cx, cy, t):
    c.rr((cx - 22, cy - 18, cx + 22, cy + 12), 10, fill=WHITE)
    c.poly([(cx - 12, cy + 10), (cx - 2, cy + 10), (cx - 14, cy + 22)], fill=WHITE)
    for k in range(3):
        c.ell(cx - 10 + k * 11, cy - 3, 3, fill=TILE)


def glyph_music(c, cx, cy, t):
    c.ell(cx - 12, cy + 13, 8, fill=WHITE)
    c.ell(cx + 12, cy + 9, 8, fill=WHITE)
    c.line([(cx - 5, cy + 13), (cx - 5, cy - 18)], WHITE, 4)
    c.line([(cx + 19, cy + 9), (cx + 19, cy - 22)], WHITE, 4)
    c.line([(cx - 5, cy - 18), (cx + 19, cy - 22)], WHITE, 5)


def glyph_camera(c, cx, cy, t):
    c.rr((cx - 22, cy - 12, cx + 22, cy + 18), 6, fill=WHITE)
    c.rr((cx - 8, cy - 18, cx + 8, cy - 10), 3, fill=WHITE)
    c.ell(cx, cy + 3, 10, fill=TILE)
    c.ell(cx, cy + 3, 5, fill=WHITE)


def glyph_photos(c, cx, cy, t):
    for k in range(6):
        a = math.radians(60 * k)
        c.ell(cx + 11 * math.cos(a), cy + 11 * math.sin(a), 10, fill=(255, 255, 255, 190))


def glyph_weather(c, cx, cy, t):
    for k in range(8):
        a = math.radians(45 * k + 60 * t)
        c.line([(cx + 14 * math.cos(a), cy + 14 * math.sin(a)), (cx + 22 * math.cos(a), cy + 22 * math.sin(a))], WHITE, 3)
    c.ell(cx, cy, 10, fill=WHITE)


def glyph_notes(c, cx, cy, t):
    c.rr((cx - 18, cy - 22, cx + 18, cy + 22), 5, fill=WHITE)
    for k in range(4):
        c.line([(cx - 11, cy - 12 + k * 9), (cx + (11 if k < 3 else 0), cy - 12 + k * 9)], TILE, 3)


def glyph_shop(c, cx, cy, t):
    c.rr((cx - 18, cy - 8, cx + 18, cy + 20), 5, fill=WHITE)
    c.arc(cx, cy - 10, 11, 180, 360, WHITE, 4)


def glyph_settings(c, cx, cy, t):
    for k in range(8):
        a = math.radians(45 * k)
        c.line([(cx, cy), (cx + 21 * math.cos(a), cy + 21 * math.sin(a))], WHITE, 8)
    c.ell(cx, cy, 15, fill=WHITE)
    c.ell(cx, cy, 6, fill=TILE)


def glyph_games(c, cx, cy, t):
    c.rr((cx - 24, cy - 10, cx + 24, cy + 12), 11, fill=WHITE)
    c.line([(cx - 14, cy - 4), (cx - 14, cy + 6)], TILE, 3)
    c.line([(cx - 19, cy + 1), (cx - 9, cy + 1)], TILE, 3)
    c.ell(cx + 11, cy - 2, 3, fill=TILE)
    c.ell(cx + 17, cy + 4, 3, fill=TILE)


def glyph_home(c, cx, cy, t):
    c.poly([(cx, cy - 20), (cx + 22, cy - 1), (cx - 22, cy - 1)], fill=WHITE)
    c.rr((cx - 15, cy - 3, cx + 15, cy + 18), 3, fill=WHITE)
    c.rr((cx - 5, cy + 5, cx + 5, cy + 18), 2, fill=TILE)


def glyph_lock(c, cx, cy, t):
    c.arc(cx, cy - 10, 12, 180, 360, WHITE, 5)
    c.rr((cx - 18, cy - 6, cx + 18, cy + 20), 5, fill=WHITE)
    c.ell(cx, cy + 6, 4, fill=TILE)


APPS = [("Drive", glyph_drive), ("Map", glyph_map), ("Calls", glyph_calls), ("Messages", glyph_messages),
        ("Music", glyph_music), ("Camera", glyph_camera), ("Photos", glyph_photos), ("Weather", glyph_weather),
        ("Notes", glyph_notes), ("Shop", glyph_shop), ("Settings", glyph_settings), ("Games", glyph_games)]
DOCK = [("Home", glyph_home), ("Drive", glyph_drive), ("Messages", glyph_messages), ("Lock", glyph_lock)]
CONTACTS = ["Blue", "Red", "Green", "Pink"]
KEY_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---- the device ---------------------------------------------------------------
class Device:
    """Holds the screen state and answers taps. Screens register the buttons
    they draw each frame so a tap by name lands on the right rectangle."""

    def __init__(self):
        self.screen = "Home"
        self.frame = 0
        self.opened_at = 0
        self.prev = None                    # the last frame image, for transitions
        self.tap = None                     # (x, y, frame) of the last tap
        self.buttons = {}                   # name -> (x0, y0, x1, y1), rebuilt each frame
        self.pressed = None                 # (name, frame)
        # per-app state
        self.chat = [("in", "where are you?"), ("out", "just landed"), ("in", "meet at 33 : 32?")]
        self.read = 0                       # incoming messages seen so far
        self.typing = ""                    # text in the message box
        self.typing_key = None              # (key, frame) the key just pressed
        self.reply_at = None                # frame when a reply arrives
        self.nav = None                     # frame navigation started
        self.boost = False
        self.autopilot = False
        self.playing = False
        self.play_at = 0
        self.progress = 0.0
        self.track = 0
        self.calling = None                 # (name, frame)
        self.shutter_at = None
        self.photos = 5
        self.settings = {"Lights": True, "Hover assist": True, "Quiet mode": False, "Night HUD": False}
        self.toggled = {}                   # name -> frame
        self.bought = None                  # (item, frame)
        self.game_on = None
        self.note_text = ""

    # -- input -----------------------------------------------------------------
    def go(self, screen):
        if screen != self.screen:
            self.screen = screen
            self.opened_at = self.frame
        if screen == "Messages":
            self.read = sum(1 for who, _ in self.chat if who == "in")

    def act(self, action, arg=None):
        f = self.frame
        if action == "tap":
            name = arg
            box = self.buttons.get(name)
            if box is None:
                raise KeyError("no button %r on screen %s at frame %d (have %s)" % (name, self.screen, f, sorted(self.buttons)))
            self.tap = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, f)
            self.pressed = (name, f)
            self.press(name)
        elif action == "type":
            self.type_text = (arg, f)
        elif action in ("back", "home"):
            self.go("Home")

    def press(self, name):
        s = self.screen
        if name in ("Back", "Home"):
            self.go("Home")
        elif name == "Lock":
            self.go("Lock")
        elif name == "Unlock":
            self.go("Home")
        elif s == "Home" and name in dict(APPS):
            self.go(name)
        elif s == "Home" and name == "Speed":
            self.go("Drive")
        elif s == "Map" and name == "GO":
            self.nav = None if self.nav is not None else self.frame
        elif s == "Drive" and name == "BOOST":
            self.boost = not self.boost
        elif s == "Drive" and name == "AUTO":
            self.autopilot = not self.autopilot
        elif s == "Messages" and name == "Send" and self.typing:
            self.chat.append(("out", self.typing))
            self.typing = ""
            self.reply_at = self.frame + 40
        elif s == "Calls" and name in CONTACTS:
            self.calling = (name, self.frame)
        elif s == "Calls" and name == "End":
            self.calling = None
        elif s == "Music" and name == "Play":
            if self.playing:
                self.progress += (self.frame - self.play_at) / (FPS * 60.0)
            self.playing = not self.playing
            self.play_at = self.frame
        elif s == "Music" and name == "Next":
            self.track = (self.track + 1) % 3
            self.progress = 0.0
            self.play_at = self.frame
        elif s == "Camera" and name == "Shutter":
            self.shutter_at = self.frame
            self.photos += 1
        elif s == "Settings" and name.startswith("Toggle:"):
            key = name[7:]
            self.settings[key] = not self.settings[key]
            self.toggled[key] = self.frame
        elif s == "Shop" and name.startswith("Buy:"):
            self.bought = (name[4:], self.frame)
        elif s == "Games" and name == "Play":
            self.game_on = self.frame

    # -- typing runs across frames: one key every three frames --------------------
    type_text = None

    def tick_typing(self):
        if self.type_text is None:
            return
        text, start = self.type_text
        n = (self.frame - start) // 3
        if n >= len(text):
            self.type_text = None
            self.typing_key = None
            return
        if (self.frame - start) % 3 == 0:
            ch = text[n]
            if self.screen == "Notes":
                self.note_text += ch
            else:
                self.typing += ch
            self.typing_key = (ch, self.frame)

    # -- frame rendering ---------------------------------------------------------
    def button(self, name, box):
        self.buttons[name] = box

    def render(self):
        f = self.frame
        self.tick_typing()
        if self.reply_at is not None and f >= self.reply_at:
            self.chat.append(("in", "ok, see you there"))
            self.reply_at = None
        self.buttons = {}
        c = Canvas()
        self.frame_chrome(c)
        getattr(self, "draw_" + self.screen.replace(" ", "_").lower())(c)
        self.draw_tap(c)
        img = c.img
        # opening transition: the new screen grows and fades in over the old one
        age = f - self.opened_at
        if self.prev is not None and age < 8 and f > 0:
            k = ease(age / 8.0)
            base = self.prev.copy()
            scale = 0.9 + 0.1 * k
            small = img.resize((int(W * S * scale), int(H * S * scale)), Image.LANCZOS)
            layer = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
            layer.paste(small, ((W * S - small.width) // 2, (H * S - small.height) // 2))
            a = layer.split()[3].point(lambda v: int(v * k))
            layer.putalpha(a)
            base = Image.alpha_composite(base, layer)
            img = base
        self.prev = img
        return img.resize((W, H), Image.LANCZOS)

    def frame_chrome(self, c):
        m = 18
        c.rr((m, m, W - m, H - m), 26, fill=BG, outline=PURPLE, width=3 * S)
        for cx, cy, sx, sy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            c.line([(cx, cy + sy * 46), (cx, cy), (cx + sx * 46, cy)], LILAC, 6)
        # status bar
        for k in range(4):
            h = 5 + 4 * k
            c.rr((42 + k * 9, 46 - h, 47 + k * 9, 46), 1, fill=LILAC if k < 3 else DIM)
        c.txtc(W / 2, 30, NAME, 30, LILAC, True)
        c.rr((446, 30, 492, 50), 4, outline=LILAC, width=2 * S)
        c.rr((493, 36, 497, 44), 1, fill=LILAC)
        c.rr((449, 33, 449 + 40 * 0.78, 47), 2, fill=CYAN)
        c.line([(40, 66), (500, 66)], DIM, 2)

    def draw_tap(self, c):
        if self.tap is None:
            return
        x, y, f0 = self.tap
        age = self.frame - f0
        if age > 10:
            return
        k = age / 10.0
        c.ell(x, y, 10 + 30 * k, outline=(255, 255, 255, int(200 * (1 - k))), width=3 * S)
        c.ell(x, y, 8 * (1 - k), fill=(255, 255, 255, int(220 * (1 - k))))

    def press_scale(self, name):
        if self.pressed and self.pressed[0] == name:
            age = self.frame - self.pressed[1]
            if age < 6:
                return 1.0 - 0.12 * math.sin(math.pi * age / 6.0)
        return 1.0

    def header(self, c, title, right=None):
        """App header with a Back button; returns the content top."""
        c.rr((40, 76, 120, 108), 12, fill=CARD, outline=DIM, width=2 * S)
        c.poly([(58, 92), (70, 82), (70, 102)], fill=LILAC)
        c.txt(76, 82, "Back", 18, LILAC)
        self.button("Back", (40, 76, 120, 108))
        c.txtc(W / 2, 78, title, 28, WHITE, True)
        if right:
            c.txt(400, 84, right, 18, CYAN)
        return 124

    def big_button(self, c, name, box, label, on=False, color=None):
        k = self.press_scale(name)
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hh = (x1 - x0) / 2 * k, (y1 - y0) / 2 * k
        c.rr((cx - hw, cy - hh, cx + hw, cy + hh), 14, fill=color or (PURPLE if on else CARD_SOLID), outline=LILAC, width=2 * S)
        c.txtc(cx, cy - 12, label, 20, WHITE, True)
        self.button(name, box)

    def tile(self, c, name, cx, cy, size, glow=0.0):
        k = self.press_scale(name)
        h = size / 2 * k
        c.rr((cx - h, cy - h, cx + h, cy + h), 15,
             fill=(120 + int(30 * glow), 60 + int(30 * glow), 200, 175), outline=(230, 190, 255, 130), width=2 * S)

    # -- screens -------------------------------------------------------------
    def draw_home(self, c):
        f, t = self.frame, self.frame / float(FPS)
        blink = ":" if (f // 12) % 2 == 0 else " "
        c.txtc(W / 2, 78, "10" + blink + "42", 72, WHITE, True)
        c.txtc(W / 2, 162, "Good morning  \u00b7  Baseplate 26 : 16", 20, CYAN)
        # speed widget
        c.rr((40, 200, 500, 300), 18, fill=CARD, outline=DIM, width=2 * S)
        speed = self.speed(t)
        gx, gy, gr = 100, 268, 48
        c.arc(gx, gy, gr, 180, 360, DIM, 8)
        c.arc(gx, gy, gr, 180, 180 + 180 * speed, PURPLE, 8)
        a = math.radians(180 + 180 * speed)
        c.line([(gx, gy), (gx + (gr - 12) * math.cos(a), gy + (gr - 12) * math.sin(a))], WHITE, 4)
        c.ell(gx, gy, 6, fill=LILAC)
        c.txt(170, 212, "%d" % int(8 + 74 * speed), 54, WHITE, True)
        c.txt(172, 272, "km/h", 20, CYAN)
        alt = self.alt(t)
        c.txt(300, 214, "ALT  %.1f m" % (2.2 + 1.2 * alt), 20, LILAC)
        c.rr((300, 244, 480, 258), 6, fill=BG, outline=DIM, width=2 * S)
        c.rr((302, 246, 302 + 176 * alt, 256), 5, fill=PURPLE)
        c.ell(306, 278, 6, fill=CYAN if (f // 18) % 2 == 0 else DIM)
        c.txt(320, 270, "HOVER  LOCKED", 16, LILAC)
        self.button("Speed", (40, 200, 500, 300))
        # app grid, one icon lights in turn
        lit = int(t * 4) % 12
        for k, (label, glyph) in enumerate(APPS):
            col, row = k % 3, k // 3
            cx, cy = 110 + col * 160, 340 + row * 96
            self.tile(c, label, cx, cy, 64, 1.0 if k == lit else 0.0)
            glyph(c, cx, cy, t)
            c.txtc(cx, cy + 38, label, 17, LILAC)
            self.button(label, (cx - 40, cy - 40, cx + 40, cy + 52))
            if label == "Messages":
                unread = sum(1 for who, _ in self.chat if who == "in") - self.read
                if unread > 0:
                    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t * 2)
                    c.ell(cx + 30, cy - 33, 10, fill=(255, int(70 + 40 * pulse), 120, 255))
                    c.txtc(cx + 30, cy - 42, str(unread), 16, WHITE)
        # dock
        c.rr((40, 720, 500, 780), 22, fill=CARD, outline=DIM, width=2 * S)
        for k, (label, glyph) in enumerate(DOCK):
            cx = 100 + k * 113
            self.tile(c, label, cx, 750, 48)
            glyph(c, cx, 750, t)
            self.button(label, (cx - 28, 722, cx + 28, 778))
        c.rr((230, 786, 310, 790), 2, fill=LILAC)

    def speed(self, t):
        s = 0.5 + 0.5 * math.sin(2 * math.pi * t / 3.0) * math.cos(2 * math.pi * t / 6.0)
        return min(1.0, s + 0.35) if self.boost else s

    def alt(self, t):
        return 0.55 + 0.08 * math.sin(2 * math.pi * t / 2.3)

    def draw_drive(self, c):
        t = self.frame / float(FPS)
        top = self.header(c, "Drive", "BOOST ON" if self.boost else None)
        cx, cy, r = 270, 300, 140
        c.arc(cx, cy, r, 150, 390, DIM, 10)
        speed = self.speed(t)
        c.arc(cx, cy, r, 150, 150 + 240 * speed, RED if self.boost else PURPLE, 10)
        for k in range(13):
            a = math.radians(150 + 20 * k)
            inner = r - (24 if k % 3 == 0 else 14)
            c.line([(cx + inner * math.cos(a), cy + inner * math.sin(a)), (cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))], LILAC, 3 if k % 3 == 0 else 2)
        a = math.radians(150 + 240 * speed)
        c.line([(cx, cy), (cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a))], WHITE, 5)
        c.ell(cx, cy, 12, fill=LILAC)
        c.txtc(cx, cy + 30, "%d" % int(8 + 74 * speed), 84, WHITE, True)
        c.txtc(cx, cy + 118, "km/h", 20, CYAN)
        alt = self.alt(t)
        c.txt(40, 470, "ALT", 20, CYAN)
        c.rr((40, 498, 500, 520), 8, fill=CARD, outline=DIM, width=2 * S)
        c.rr((42, 500, 42 + 456 * alt, 518), 7, fill=PURPLE)
        c.txt(430, 470, "%.1f m" % (2.2 + 1.2 * alt), 20, LILAC)
        # radar
        rx, ry, rr_ = 120, 610, 70
        c.ell(rx, ry, rr_, fill=CARD, outline=DIM, width=2 * S)
        c.ell(rx, ry, rr_ / 2, outline=DIM, width=1 * S)
        sweep = 2 * math.pi * t / 3.0
        for k in range(18):
            a = sweep - k * 0.05
            c.line([(rx, ry), (rx + rr_ * math.cos(a), ry + rr_ * math.sin(a))], (200, 120, 255, int(200 * (1 - k / 18))), 3)
        for bx, by in ((0.5, -0.3), (-0.4, 0.55), (0.2, 0.7)):
            c.ell(rx + bx * rr_, ry + by * rr_, 5, fill=CYAN)
        # power cells
        c.txt(230, 545, "POWER", 20, CYAN)
        for k in range(6):
            level = 0.7 + 0.3 * math.sin(2 * math.pi * t * (0.3 + 0.1 * k) + k)
            x0 = 230 + k * 42
            c.rr((x0, 572, x0 + 30, 680), 6, fill=CARD, outline=DIM, width=2 * S)
            c.rr((x0 + 3, 680 - 105 * level, x0 + 27, 677), 5, fill=RED if self.boost else PURPLE)
        self.big_button(c, "BOOST", (40, 700, 260, 760), "BOOST", self.boost, RED if self.boost else None)
        self.big_button(c, "AUTO", (280, 700, 500, 760), "AUTOPILOT", self.autopilot)

    def draw_map(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Map")
        # a grid of tiles with numbers, the craft in the middle, a destination pin
        x0, y0, x1, y1 = 40, top, 500, 660
        c.rr((x0, y0, x1, y1), 14, fill=CARD)
        for k in range(1, 6):
            c.line([(x0 + k * 92, y0), (x0 + k * 92, y1)], DIM, 1)
        for k in range(1, 6):
            c.line([(x0, y0 + k * 89), (x1, y0 + k * 89)], DIM, 1)
        for col in range(5):
            for row in range(6):
                c.txt(x0 + col * 92 + 6, y0 + row * 89 + 4, "%d:%d" % (24 + col, 19 - row), 13, DIM)
        mx, my = x0 + 2.5 * 92, y0 + 3.5 * 89
        px, py = x0 + 4.5 * 92, y0 + 0.6 * 89
        # dashed route, dashes crawl toward the pin
        seg = [(mx, my), (mx, my - 89 * 2), (px, my - 89 * 2), (px, py + 10)]
        off = (f * 2) % 16
        for (ax, ay), (bx, by) in zip(seg, seg[1:]):
            L = math.hypot(bx - ax, by - ay)
            n = int(L)
            k = off
            while k < L:
                e = min(k + 8, L)
                c.line([(ax + (bx - ax) * k / L, ay + (by - ay) * k / L), (ax + (bx - ax) * e / L, ay + (by - ay) * e / L)], CYAN if self.nav else DIM, 3)
                k += 16
        # craft marker with a pulsing ring
        pulse = (t * 1.2) % 1.0
        c.ell(mx, my, 10 + 22 * pulse, outline=(210, 120, 255, int(200 * (1 - pulse))), width=3 * S)
        c.poly([(mx, my - 14), (mx + 10, my + 10), (mx, my + 4), (mx - 10, my + 10)], fill=WHITE)
        # destination pin bobbing
        bob = 4 * math.sin(2 * math.pi * t / 1.4)
        c.poly([(px - 10, py - 6 + bob), (px + 10, py - 6 + bob), (px, py + 14 + bob)], fill=RED)
        c.ell(px, py - 8 + bob, 11, fill=RED)
        c.ell(px, py - 8 + bob, 4, fill=WHITE)
        if self.nav is None:
            c.txt(40, 674, "Tile 33 : 32   \u00b7   2.4 km", 20, LILAC)
            self.big_button(c, "GO", (360, 664, 500, 712), "GO", color=GREEN)
        else:
            eta = max(0, 180 - (f - self.nav) // 8)
            c.txt(40, 674, "Navigating   \u00b7   ETA %d:%02d" % (eta // 60, eta % 60), 20, CYAN)
            c.rr((40, 700, 500, 712), 5, fill=CARD, outline=DIM, width=2 * S)
            c.rr((42, 702, 44 + 454 * min(1.0, (f - self.nav) / 1440.0), 710), 4, fill=CYAN)
            self.big_button(c, "GO", (360, 720, 500, 768), "STOP", color=RED)
        c.txt(40, 724, "Heading 035\u00b0", 18, DIM)

    def draw_messages(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Blue", "online")
        c.ell(150, 92, 12, fill=(120, 170, 255, 255))
        # bubbles, newest at the bottom above the keyboard, the last one slides in
        y = 450 if self.reply_at is not None else 500
        for i, (who, text) in enumerate(reversed(self.chat)):
            w = c.width(text, 20) + 28
            h = 40
            y -= h + 10
            if y < top:
                break
            if who == "out":
                c.rr((500 - w, y, 500, y + h), 14, fill=PURPLE)
                c.txt(500 - w + 14, y + 9, text, 20, WHITE)
            else:
                c.rr((40, y, 40 + w, y + h), 14, fill=CARD_SOLID)
                c.txt(54, y + 9, text, 20, WHITE)
        if self.reply_at is not None:
            k = (f // 4) % 3
            c.rr((40, 460, 100, 500), 14, fill=CARD_SOLID)
            for j in range(3):
                c.ell(55 + j * 15, 480, 4 if j != k else 6, fill=LILAC if j == k else DIM)
        # input box with a blinking cursor
        c.rr((40, 520, 400, 562), 14, fill=CARD, outline=DIM, width=2 * S)
        cursor = "|" if (f // 8) % 2 == 0 else ""
        c.txt(54, 530, (self.typing or ("Message" if not self.typing else "")) + cursor, 20, WHITE if self.typing else DIM)
        self.big_button(c, "Send", (412, 520, 500, 562), "Send", bool(self.typing), PURPLE if self.typing else None)
        # keyboard: the key being typed lights up
        for r, row in enumerate(KEY_ROWS):
            kw, gap = 40, 6
            xs = 270 - (len(row) * (kw + gap) - gap) / 2
            for j, ch in enumerate(row):
                kx = xs + j * (kw + gap)
                ky = 584 + r * 52
                lit = self.typing_key and self.typing_key[0] == ch and f - self.typing_key[1] < 3
                c.rr((kx, ky, kx + kw, ky + 44), 6, fill=PURPLE if lit else CARD_SOLID)
                c.txtc(kx + kw / 2, ky + 10, ch, 20, WHITE)
        lit = self.typing_key and self.typing_key[0] == " " and f - self.typing_key[1] < 3
        c.rr((150, 740, 390, 776), 6, fill=PURPLE if lit else CARD_SOLID)
        c.txtc(270, 748, "space", 16, LILAC)

    def draw_calls(self, c):
        f, t = self.frame, self.frame / float(FPS)
        if self.calling:
            name, f0 = self.calling
            self.header(c, "Call")
            age = f - f0
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t * 1.5)
            for k in range(3):
                c.ell(270, 300, 70 + 40 * k + 10 * pulse, outline=(210, 120, 255, int(120 - 35 * k)), width=2 * S)
            c.ell(270, 300, 64, fill=CARD_SOLID, outline=LILAC, width=3 * S)
            c.txtc(270, 278, name[0], 48, WHITE, True)
            c.txtc(270, 400, name, 34, WHITE, True)
            if age < 48:
                c.txtc(270, 450, "Calling" + "." * ((f // 8) % 4), 22, CYAN)
            else:
                s = (age - 48) // FPS
                c.txtc(270, 450, "Connected  %d:%02d" % (s // 60, s % 60), 22, GREEN)
                for k in range(12):
                    h = 6 + 30 * abs(math.sin(2 * math.pi * t * (1 + 0.15 * k) + k))
                    c.rr((180 + k * 15, 520 - h, 190 + k * 15, 520 + h), 4, fill=LILAC)
            self.big_button(c, "End", (170, 680, 370, 740), "END", color=RED)
            return
        top = self.header(c, "Calls")
        for i, name in enumerate(CONTACTS):
            y = top + 20 + i * 96
            k = self.press_scale(name)
            c.rr((40, y, 500, y + 80), 16, fill=CARD if k == 1 else TILE, outline=DIM, width=2 * S)
            c.ell(90, y + 40, 26, fill=[(120, 170, 255, 255), (255, 110, 110, 255), (120, 230, 150, 255), (255, 150, 220, 255)][i])
            c.txtc(90, y + 24, name[0], 26, WHITE, True)
            c.txt(136, y + 16, name, 26, WHITE, True)
            c.txt(136, y + 48, "tile %d : %d" % (30 + i * 2, 28 + i), 16, DIM)
            glyph_calls(c, 450, y + 40, t)
            self.button(name, (40, y, 500, y + 80))
        c.txt(40, top + 420, "Recent", 20, CYAN)
        c.txt(40, top + 452, "Blue  \u00b7  yesterday  \u00b7  2:14", 18, LILAC)

    def draw_music(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Music")
        titles = [("Skyline Drift", "Neon Tide"), ("Baseplate Blues", "The Tiles"), ("Hover Hymn", "Grid Choir")]
        title, artist = titles[self.track]
        # album art: a gradient square with a spinning disc
        c.rr((120, top + 10, 420, top + 310), 22, fill=(90, 40, 160, 220))
        for k in range(6):
            c.ell(270, top + 160, 120 - k * 18, outline=(200 + 9 * k, 120 + 20 * k, 255, 120), width=2 * S)
        spin = t * 1.5 if self.playing else 0
        c.line([(270, top + 160), (270 + 100 * math.cos(spin), top + 160 + 100 * math.sin(spin))], LILAC, 4)
        c.ell(270, top + 160, 14, fill=WHITE)
        c.txtc(270, top + 330, title, 30, WHITE, True)
        c.txtc(270, top + 370, artist, 20, CYAN)
        prog = self.progress + ((f - self.play_at) / (FPS * 60.0) if self.playing else 0)
        prog = prog % 1.0
        c.rr((60, top + 420, 480, top + 428), 4, fill=CARD, outline=DIM, width=1 * S)
        c.rr((60, top + 419, 62 + 418 * prog, top + 429), 4, fill=PURPLE)
        c.ell(60 + 420 * prog, top + 424, 8, fill=WHITE)
        sec = int(prog * 60)
        c.txt(60, top + 436, "0:%02d" % sec, 16, DIM)
        c.txt(440, top + 436, "1:00", 16, DIM)
        # equaliser
        for k in range(16):
            h = (6 + 40 * abs(math.sin(2 * math.pi * t * (0.8 + 0.2 * k) + k))) if self.playing else 6
            c.rr((70 + k * 26, top + 520 - h, 86 + k * 26, top + 520), 4, fill=LILAC)
        # controls
        c.poly([(150, top + 560), (150, top + 600), (120, top + 580)], fill=LILAC)
        c.poly([(150, top + 560), (150, top + 600), (180, top + 580)], fill=DIM)
        k = self.press_scale("Play")
        c.ell(270, top + 580, 36 * k, fill=PURPLE)
        if self.playing:
            c.rr((258, top + 566, 266, top + 594), 2, fill=WHITE)
            c.rr((274, top + 566, 282, top + 594), 2, fill=WHITE)
        else:
            c.poly([(260, top + 564), (260, top + 596), (288, top + 580)], fill=WHITE)
        self.button("Play", (230, top + 540, 310, top + 620))
        c.poly([(390, top + 560), (390, top + 600), (420, top + 580)], fill=LILAC)
        c.rr((420, top + 560, 426, top + 600), 2, fill=LILAC)
        self.button("Next", (380, top + 550, 440, top + 610))

    def draw_camera(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Camera")
        x0, y0, x1, y1 = 40, top, 500, 640
        c.rr((x0, y0, x1, y1), 14, fill=(20, 8, 40, 150))
        # a view of the plate: horizon and grid receding
        c.line([(x0, y0 + 190), (x1, y0 + 190)], DIM, 2)
        for k in range(-4, 5):
            c.line([(270 + k * 20, y0 + 190), (270 + k * 140, y1)], DIM, 1)
        for k in range(1, 6):
            yy = y0 + 190 + (y1 - y0 - 190) * (k / 5.0) ** 1.6
            c.line([(x0, yy), (x1, yy)], DIM, 1)
        c.ell(430, y0 + 60, 26, fill=(255, 240, 200, 200))
        # corner brackets and a wandering focus square
        for cx, cy, sx, sy in ((x0 + 14, y0 + 14, 1, 1), (x1 - 14, y0 + 14, -1, 1), (x0 + 14, y1 - 14, 1, -1), (x1 - 14, y1 - 14, -1, -1)):
            c.line([(cx, cy + sy * 30), (cx, cy), (cx + sx * 30, cy)], LILAC, 3)
        fx = 270 + 60 * math.sin(2 * math.pi * t / 5.0)
        fy = y0 + 250 + 40 * math.cos(2 * math.pi * t / 7.0)
        c.rr((fx - 40, fy - 40, fx + 40, fy + 40), 6, outline=CYAN, width=2 * S)
        c.txt(x0 + 16, y1 - 40, "1x   \u00b7   AF", 18, LILAC)
        if self.shutter_at is not None and f - self.shutter_at < 6:
            k = 1 - (f - self.shutter_at) / 6.0
            c.rr((x0, y0, x1, y1), 14, fill=(255, 255, 255, int(220 * k)))
        # thumbnail of the last photo pops in
        if self.shutter_at is not None and f - self.shutter_at > 4:
            k = max(0.05, ease((f - self.shutter_at - 4) / 8.0))
            c.rr((60, 668 + 20 * (1 - k), 60 + 60 * k, 668 + 20 * (1 - k) + 60 * k), 8, fill=(140, 90, 220, 255), outline=WHITE, width=2 * S)
        c.txtc(270, 668, str(self.photos), 18, DIM)
        k = self.press_scale("Shutter")
        c.ell(270, 720, 40 * k, fill=WHITE)
        c.ell(270, 720, 34 * k, outline=DIM, width=2 * S)
        self.button("Shutter", (220, 670, 320, 770))

    def draw_photos(self, c):
        t = self.frame / float(FPS)
        top = self.header(c, "Photos", "%d photos" % self.photos)
        for i in range(min(self.photos, 12)):
            col, row = i % 3, i // 3
            x, y = 40 + col * 156, top + 10 + row * 156
            hue = (i * 47) % 255
            c.rr((x, y, x + 144, y + 144), 10, fill=(120 + hue // 3, 60 + (255 - hue) // 3, 200, 230))
            # each photo is a little scene: a sun, a horizon, a tile
            c.ell(x + 30 + (i * 13) % 80, y + 30, 14, fill=(255, 240, 200, 230))
            c.line([(x + 6, y + 90), (x + 138, y + 90)], (255, 255, 255, 120), 2)
            c.rr((x + 40 + (i * 29) % 50, y + 100, x + 80 + (i * 29) % 50, y + 130), 4, fill=(255, 255, 255, 90))
            if i == self.photos - 1 and self.shutter_at is not None:
                c.rr((x, y, x + 144, y + 144), 10, outline=WHITE, width=3 * S)
        c.txt(40, 730, "Today  \u00b7  Baseplate", 18, DIM)

    def draw_weather(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Weather")
        c.txtc(270, top + 10, "Baseplate", 24, CYAN)
        # a sun with turning rays and a drifting cloud
        sx, sy = 270, top + 150
        for k in range(12):
            a = math.radians(30 * k + 20 * t)
            c.line([(sx + 70 * math.cos(a), sy + 70 * math.sin(a)), (sx + 95 * math.cos(a), sy + 95 * math.sin(a))], (255, 230, 150, 255), 5)
        c.ell(sx, sy, 58, fill=(255, 225, 140, 255))
        cx = 330 + 25 * math.sin(2 * math.pi * t / 6.0)
        for dx, r in ((-40, 26), (-10, 36), (30, 30), (55, 22)):
            c.ell(cx + dx, sy + 40, r, fill=(255, 255, 255, 235))
        c.rr((cx - 66, sy + 40, cx + 77, sy + 66), 12, fill=(255, 255, 255, 235))
        c.txtc(270, top + 270, "24\u00b0", 84, WHITE, True)
        c.txtc(270, top + 370, "Sunny, light wind from the tiles", 20, LILAC)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for i, day in enumerate(days):
            x = 70 + i * 100
            c.rr((x - 40, top + 420, x + 40, top + 560), 14, fill=CARD, outline=DIM, width=2 * S)
            c.txtc(x, top + 432, day, 18, CYAN)
            if i in (1, 3):
                for dx, r in ((-12, 10), (2, 14), (14, 10)):
                    c.ell(x + dx, top + 480, r, fill=(230, 230, 255, 230))
            else:
                c.ell(x, top + 480, 16, fill=(255, 225, 140, 255))
            c.txtc(x, top + 520, "%d\u00b0" % (22 + (i * 3) % 5), 20, WHITE, True)

    def draw_notes(self, c):
        f = self.frame
        top = self.header(c, "Notes", "+ New")
        notes = ["Find the crates", "Ask Blue about the plate", "Fuel cells: 6 / 6", "Meet at 33 : 32"]
        y = top + 10
        for n in notes:
            c.rr((40, y, 500, y + 70), 14, fill=CARD, outline=DIM, width=2 * S)
            c.txt(60, y + 12, n, 22, WHITE)
            c.txt(60, y + 44, "Today", 14, DIM)
            y += 84
        cursor = "|" if (f // 8) % 2 == 0 else ""
        c.rr((40, y, 500, y + 70), 14, fill=CARD_SOLID, outline=LILAC, width=2 * S)
        c.txt(60, y + 22, (self.note_text or "New note") + cursor, 22, WHITE if self.note_text else DIM)

    def draw_shop(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Shop", "12 credits")
        items = [("Fuel cell", 3), ("Neon kit", 5), ("Crown polish", 2), ("Hover pad", 8)]
        for i, (item, price) in enumerate(items):
            y = top + 10 + i * 118
            c.rr((40, y, 500, y + 104), 16, fill=CARD, outline=DIM, width=2 * S)
            c.rr((56, y + 16, 128, y + 88), 12, fill=TILE)
            (glyph_settings, glyph_weather, glyph_photos, glyph_drive)[i](c, 92, y + 52, t)
            c.txt(144, y + 20, item, 24, WHITE, True)
            c.txt(144, y + 56, "%d credits" % price, 18, CYAN)
            name = "Buy:" + item
            if self.bought and self.bought[0] == item:
                k = ease((f - self.bought[1]) / 8.0)
                c.rr((380 - 10 * k, y + 32, 484 + 10 * k, y + 72), 12, fill=GREEN)
                c.txtc(432, y + 40, "Bought", 18, WHITE, True)
            else:
                self.big_button(c, name, (380, y + 32, 484, y + 72), "Buy")

    def draw_settings(self, c):
        f = self.frame
        top = self.header(c, "Settings")
        for i, (key, on) in enumerate(self.settings.items()):
            y = top + 10 + i * 90
            c.rr((40, y, 500, y + 76), 14, fill=CARD, outline=DIM, width=2 * S)
            c.txt(60, y + 24, key, 22, WHITE)
            k = 1.0
            if key in self.toggled:
                k = ease((f - self.toggled[key]) / 6.0)
            pos = k if on else 1 - k
            c.rr((410, y + 22, 480, y + 54), 16, fill=PURPLE if pos > 0.5 else CARD_SOLID, outline=LILAC, width=2 * S)
            c.ell(426 + 38 * pos, y + 38, 12, fill=WHITE)
            self.button("Toggle:" + key, (40, y, 500, y + 76))
        c.txt(40, top + 400, "Craft", 20, CYAN)
        c.txt(40, top + 432, "Name   " + NAME, 18, LILAC)
        c.txt(40, top + 460, "Pods    7   \u00b7   Firmware 2.1", 18, LILAC)

    def draw_games(self, c):
        f, t = self.frame, self.frame / float(FPS)
        top = self.header(c, "Games", "best 420")
        x0, y0, x1, y1 = 40, top, 500, 620
        c.rr((x0, y0, x1, y1), 14, fill=(20, 8, 40, 160))
        # a tile-dodging runner: the craft weaves, blocks scroll toward it
        if self.game_on is not None:
            age = f - self.game_on
            for k in range(6):
                yy = (y0 + (age * 6 + k * 90) % (y1 - y0 - 30))
                xx = x0 + 60 + (k * 137) % 340
                c.rr((xx, yy, xx + 50, yy + 26), 5, fill=RED)
            px = 270 + 120 * math.sin(2 * math.pi * age / 70.0)
            c.txt(x0 + 16, y0 + 12, "%d" % (age * 3), 26, WHITE, True)
        else:
            px = 270
            c.txtc(270, y0 + 200, "TILE RUNNER", 34, WHITE, True)
            c.txtc(270, y0 + 250, "dodge the red blocks", 18, LILAC)
        c.poly([(px, y1 - 70), (px + 16, y1 - 30), (px, y1 - 40), (px - 16, y1 - 30)], fill=CYAN)
        self.big_button(c, "Play", (170, 660, 370, 720), "RESTART" if self.game_on is not None else "PLAY", color=GREEN)

    def draw_lock(self, c):
        f, t = self.frame, self.frame / float(FPS)
        blink = ":" if (f // 12) % 2 == 0 else " "
        c.txtc(W / 2, 200, "10" + blink + "42", 96, WHITE, True)
        c.txtc(W / 2, 310, "Tuesday  \u00b7  Baseplate", 22, CYAN)
        glyph_lock(c, 270, 420, t)
        bob = 8 * math.sin(2 * math.pi * t / 1.5)
        c.poly([(270, 640 + bob), (290, 664 + bob), (250, 664 + bob)], fill=LILAC)
        c.txtc(270, 690, "tap to unlock", 20, LILAC)
        self.button("Unlock", (40, 76, 500, 780))


# ---- rendering a timeline -----------------------------------------------------
def render(events, out_dir, frames, verbose=True):
    """Render `frames` frames to out_dir/hud_0001.png ... applying `events`,
    a list of (frame, action, arg) with action in tap / type / back / home."""
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.startswith("hud_") and old.endswith(".png"):
            os.remove(os.path.join(out_dir, old))
    dev = Device()
    by_frame = {}
    for ev in events:
        by_frame.setdefault(ev[0], []).append(ev)
    for i in range(frames):
        dev.frame = i
        # buttons are registered while drawing, so a tap lands on the previous
        # frame's layout (the screen does not move between frames)
        for ev in by_frame.get(i, ()):
            dev.act(ev[1], ev[2] if len(ev) > 2 else None)
        img = dev.render()
        img.save(os.path.join(out_dir, "hud_%04d.png" % (i + 1)), optimize=True)
    if verbose:
        print("wrote", frames, "frames to", out_dir)
    return frames


# someone using every app: the demo the story scripts can copy from
DEMO = [
    (30, "tap", "Messages"), (60, "type", "on my way"), (100, "tap", "Send"),
    (190, "tap", "Back"),
    (210, "tap", "Map"), (240, "tap", "GO"), (300, "tap", "Back"),
    (320, "tap", "Drive"), (350, "tap", "BOOST"), (400, "tap", "AUTO"), (430, "tap", "Back"),
    (450, "tap", "Calls"), (470, "tap", "Blue"), (560, "tap", "End"), (575, "tap", "Back"),
    (595, "tap", "Music"), (615, "tap", "Play"), (680, "tap", "Next"), (720, "tap", "Back"),
    (740, "tap", "Camera"), (770, "tap", "Shutter"), (800, "tap", "Back"),
    (820, "tap", "Photos"), (860, "tap", "Back"),
    (880, "tap", "Weather"), (930, "tap", "Back"),
    (950, "tap", "Settings"), (975, "tap", "Toggle:Night HUD"), (1000, "tap", "Toggle:Lights"), (1030, "tap", "Back"),
    (1050, "tap", "Shop"), (1080, "tap", "Buy:Neon kit"), (1120, "tap", "Back"),
    (1140, "tap", "Notes"), (1160, "type", "crates at 40 : 12"), (1240, "tap", "Back"),
    (1260, "tap", "Games"), (1285, "tap", "Play"), (1370, "tap", "Back"),
    (1390, "tap", "Lock"), (1440, "tap", "Unlock"),
]
DEMO_FRAMES = 1500

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "idle"
    if mode == "demo":
        render(DEMO, os.path.join(ROOT, "textures", "hud_demo"), DEMO_FRAMES)
    else:
        render([], os.path.join(ROOT, "textures", "hud"), 72)
