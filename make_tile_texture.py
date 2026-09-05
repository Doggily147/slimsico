"""Draws the baseplate grid texture: 64x64 tiles (8 studs each on the
512x512 baseplate), dark grid lines with heavier lines every 8 tiles, and a
small label in each tile's corner: column number (top) and row number (below).
Column 1 / row 1 is the bottom-left corner of the baseplate.

  python make_tile_texture.py            -> textures/tiles.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

TILES = 64
PX = 128                    # pixels per tile
MAJOR_EVERY = 8
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures", "tiles.png")

TILE_A = (244, 245, 247)
TILE_B = (232, 234, 238)
LINE = (150, 154, 160)
MAJOR = (90, 94, 102)
COL_TEXT = (60, 64, 72)
ROW_TEXT = (40, 96, 190)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
size = TILES * PX
img = Image.new("RGB", (size, size), TILE_A)
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)

# Checker-shaded tile backgrounds.
for r in range(TILES):
    for c in range(TILES):
        if (r + c) % 2:
            x0, y0 = c * PX, r * PX
            draw.rectangle([x0, y0, x0 + PX - 1, y0 + PX - 1], fill=TILE_B)

# Grid lines: thin every tile, thick every MAJOR_EVERY tiles.
for i in range(TILES + 1):
    p = min(i * PX, size - 1)
    major = i % MAJOR_EVERY == 0
    w = 4 if major else 2
    colour = MAJOR if major else LINE
    draw.rectangle([p - w // 2, 0, p + w // 2 - 1, size - 1], fill=colour)
    draw.rectangle([0, p - w // 2, size - 1, p + w // 2 - 1], fill=colour)

# Labels: column number on top, row number below. Row 1 is at the image
# bottom because Blender's V axis points up.
for r in range(TILES):
    y0 = (TILES - 1 - r) * PX
    for c in range(TILES):
        x0 = c * PX
        draw.text((x0 + 8, y0 + 6), str(c + 1), font=font, fill=COL_TEXT)
        draw.text((x0 + 8, y0 + 26), str(r + 1), font=font, fill=ROW_TEXT)

img.save(OUT, optimize=True)
print("wrote", OUT, img.size)
