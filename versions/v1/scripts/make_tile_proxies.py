"""Finale tile proxies for S05 (storyboard section 5.4).

For each chapter tile this writes renders/proxies/<id>/p_0001.png .. p_0120.png
(640x360, 8-bit sRGB, Lanczos) that shots/s05_title.py plays on its honeycomb screens via D.mat_video.

  Tile               source frames   chapter colour
  s01_lights_world   f121-240        blue     (round 2: S01's stable day phase with the env-map clicks;
                                              f1-120 opened pitch black and ended mid night-to-day flash)
  s02_caustics       f1-120          mint
  s03_gummy          f1-120          coral
  s04_every_dot      f31-150         lemon

Source per tile, first match wins (no mixing of sources inside one tile):
  1. renders/final/<id>    if every needed frame exists and is a complete PNG,
  2. renders/preview/<id>  if every needed frame exists and is a complete PNG,
  3. labelled placeholder frames in the chapter colour (with a running frame counter, so playback and
     sync can be checked in the S05 tiles).
A frame counts as complete only if its file ends with the PNG IEND chunk and it decodes, so frames that
another builder is writing right now never get picked up half-written.

Re-runs overwrite cleanly: every tile is built in a temporary directory next to its target and swapped in
with renames, so a tile directory is never a mix of two runs. renders/proxies/manifest.json records which
source each tile used, and each tile directory carries its own SOURCE.json ({source: final|preview|placeholder, ...});
shots/s05_title.py refuses to write its final while any tile is not from a final.

usage:
  tools/venv/bin/python -I scripts/make_tile_proxies.py [--only s01_lights_world,s04_every_dot]
                                                       [--placeholder-only] [--jobs 12]
"""
import argparse
import datetime
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT_ROOT = os.path.join(ROOT, "renders", "proxies")
W, H = 640, 360
N_FRAMES = 120
IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"

# id, first source frame, chapter colour (D.PALETTE hex), pastel partner, short label
TILES = [
    ("s01_lights_world", 121, "#2E5BFF", "#CDE9FF", "S01", "Lights + env maps"),
    ("s02_caustics", 1, "#2ED8A3", "#CFF5DD", "S02", "Caustics"),
    ("s03_gummy", 1, "#FF6A5C", "#FFD3E4", "S03", "Animated geometry"),
    ("s04_every_dot", 31, "#FFD23F", "#FFF0A8", "S04", "High-res textures"),
]
INK = (0x1C, 0x1A, 0x33)
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "Fredoka-Bold.ttf")
FONT_SEMI = os.path.join(ROOT, "assets", "fonts", "Fredoka-SemiBold.ttf")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def png_complete(path):
    """True if `path` is a finished PNG (IEND trailer present). Cheap: reads 12 bytes."""
    try:
        if os.path.getsize(path) < 100:
            return False
        with open(path, "rb") as fh:
            fh.seek(-12, os.SEEK_END)
            return fh.read(12) == IEND
    except OSError:
        return False


def needed_paths(src_dir, first):
    return [os.path.join(src_dir, f"f_{first + i:04d}.png") for i in range(N_FRAMES)]


def pick_source(tile_id, first):
    for kind in ("final", "preview"):
        d = os.path.join(ROOT, "renders", kind, tile_id)
        if not os.path.isdir(d):
            continue
        paths = needed_paths(d, first)
        missing = [p for p in paths if not png_complete(p)]
        if not missing:
            return kind, paths
        print(f"  {tile_id}: {kind} has {N_FRAMES - len(missing)}/{N_FRAMES} needed frames "
              f"(first missing {os.path.basename(missing[0])}) -> not used")
    return "placeholder", None


def resize_frame(src, dst):
    """Decode (8- or 16-bit PNG), centre-crop to 16:9, Lanczos-downscale in float, write 8-bit sRGB."""
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim != 3:
        raise RuntimeError(f"cannot decode {src}")
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im[:, :, :3][:, :, ::-1].astype(np.float32) / scale  # BGR(A) -> RGB float
    h, w = im.shape[:2]
    tw = round(h * 16 / 9)
    if tw < w:  # too wide -> crop width
        x0 = (w - tw) // 2
        im = im[:, x0:x0 + tw]
    elif tw > w:  # too tall -> crop height
        th = round(w * 9 / 16)
        y0 = (h - th) // 2
        im = im[y0:y0 + th]
    chans = []
    for c in range(3):  # Pillow's Lanczos widens its kernel when downscaling (real anti-aliasing)
        ch = Image.fromarray(np.ascontiguousarray(im[:, :, c]), mode="F").resize((W, H), Image.LANCZOS)
        chans.append(np.asarray(ch))
    out = np.clip(np.rint(np.stack(chans, -1) * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(out, "RGB").save(dst, compress_level=4)
    return dst


def placeholder_frame(dst, i, first, colour, partner, code, label):
    """Labelled chapter-colour card. Content sits in the central ~60% so the hex screen shows it."""
    ss = 2  # draw at 2x, then downsample for clean edges
    w, h = W * ss, H * ss
    c0, c1 = np.array(hex_rgb(colour), np.float32), np.array(hex_rgb(partner), np.float32)
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    grad = c0 * (1 - 0.35 * yy) + c1 * (0.35 * yy)  # chapter colour, easing toward its pastel partner
    img = Image.fromarray(np.broadcast_to(grad, (h, w, 3)).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    # a soft white orb that travels left -> right over the 120 frames (shows playback + sync)
    t = i / (N_FRAMES - 1)
    ox, oy, r = w * (0.26 + 0.48 * t), h * 0.70, 26 * ss
    glow = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glow).ellipse([ox - 2 * r, oy - 2 * r, ox + 2 * r, oy + 2 * r], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(14 * ss))
    img = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), img, glow)
    d = ImageDraw.Draw(img)
    d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=(255, 255, 255))
    # pill with the chapter code + label
    f_big = ImageFont.truetype(FONT_BOLD, 64 * ss)
    f_small = ImageFont.truetype(FONT_SEMI, 22 * ss)
    d.text((w / 2, h * 0.30), code, font=f_big, fill=(255, 255, 255), anchor="mm",
           stroke_width=3 * ss, stroke_fill=INK)
    d.text((w / 2, h * 0.47), label, font=f_small, fill=INK, anchor="mm")
    d.text((w / 2, h * 0.86), f"placeholder  f{first + i:04d}", font=f_small, fill=INK, anchor="mm")
    img.resize((W, H), Image.LANCZOS).save(dst, compress_level=4)
    return dst


def build_tile(tile, jobs, force_placeholder):
    tile_id, first, colour, partner, code, label = tile
    kind, paths = ("placeholder", None) if force_placeholder else pick_source(tile_id, first)
    os.makedirs(OUT_ROOT, exist_ok=True)
    tmp = os.path.join(OUT_ROOT, f".tmp_{tile_id}_{os.getpid()}")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    dsts = [os.path.join(tmp, f"p_{i + 1:04d}.png") for i in range(N_FRAMES)]
    try:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            if kind == "placeholder":
                futs = [ex.submit(placeholder_frame, d, i, first, colour, partner, code, label)
                        for i, d in enumerate(dsts)]
            else:
                futs = [ex.submit(resize_frame, s, d) for s, d in zip(paths, dsts)]
            for fu in futs:
                fu.result()
    except Exception as e:  # a source frame vanished or failed to decode mid-run -> placeholders
        print(f"  {tile_id}: {kind} source failed ({e}); writing placeholders instead")
        shutil.rmtree(tmp, ignore_errors=True)
        return build_tile(tile, jobs, True)
    src = os.path.relpath(os.path.dirname(paths[0]), ROOT) if paths else None
    with open(os.path.join(tmp, "SOURCE.json"), "w") as fh:
        json.dump({"tile": tile_id, "source": kind, "source_dir": src, "source_frames": [first, first + N_FRAMES - 1],
                   "written": datetime.datetime.now().isoformat(timespec="seconds")}, fh, indent=2)
    final_dir = os.path.join(OUT_ROOT, tile_id)
    old = os.path.join(OUT_ROOT, f".old_{tile_id}_{os.getpid()}")
    if os.path.isdir(final_dir):
        os.rename(final_dir, old)
    os.rename(tmp, final_dir)
    shutil.rmtree(old, ignore_errors=True)
    return {"source": kind, "source_dir": src, "source_frames": [first, first + N_FRAMES - 1],
            "proxy_frames": [1, N_FRAMES], "size": [W, H]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="comma-separated tile ids")
    ap.add_argument("--placeholder-only", action="store_true")
    ap.add_argument("--jobs", type=int, default=12)
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    man_path = os.path.join(OUT_ROOT, "manifest.json")
    manifest = {}
    if os.path.exists(man_path):
        try:
            manifest = json.load(open(man_path))
        except (OSError, ValueError):
            manifest = {}
    manifest.pop("_written", None)
    for tile in TILES:
        if only and tile[0] not in only:
            continue
        info = build_tile(tile, a.jobs, a.placeholder_only)
        info["written"] = datetime.datetime.now().isoformat(timespec="seconds")
        manifest[tile[0]] = info
        print(f"{tile[0]:18s} <- {info['source']:11s} {info['source_dir'] or ''} "
              f"f{info['source_frames'][0]}-{info['source_frames'][1]}", flush=True)
    manifest["_written"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(man_path + ".tmp", "w") as fh:
        json.dump(manifest, fh, indent=2)
    os.replace(man_path + ".tmp", man_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
