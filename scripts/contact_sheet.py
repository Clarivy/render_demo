"""Tile rendered frames into one labelled image for review.
usage: tools/venv/bin/python -I scripts/contact_sheet.py OUT.png [--cols 4] [--width 480] FRAME.png ...
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("frames", nargs="+")
ap.add_argument("--cols", type=int, default=4)
ap.add_argument("--width", type=int, default=480)
a = ap.parse_args()
ims = [Image.open(f).convert("RGB") for f in a.frames]
w = a.width
h = round(ims[0].size[1] * w / ims[0].size[0])
rows = (len(ims) + a.cols - 1) // a.cols
sheet = Image.new("RGB", (a.cols * w, rows * h), "white")
d = ImageDraw.Draw(sheet)
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts", "Poppins-Bold.ttf")
font = ImageFont.truetype(font_path, max(12, w // 28))
for i, (f, im) in enumerate(zip(a.frames, ims)):
    x, y = (i % a.cols) * w, (i // a.cols) * h
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y))
    label = os.path.splitext(os.path.basename(f))[0]
    d.rectangle([x, y, x + len(label) * w // 50 + 12, y + w // 22], fill=(0, 0, 0))
    d.text((x + 6, y + 2), label, fill="white", font=font)
sheet.save(a.out)
print(a.out, sheet.size)
