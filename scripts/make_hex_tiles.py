"""Hex-tile content library for the v2 finale (docs/storyboard_v2.md section 4). CPU only.

Writes, for every honeycomb cell source of shots/s05_finale.py:
  renders/hex_tiles/<tile_id>/h_0001.png .. h_0180.png   1152 x 998, 16-bit sRGB PNG, flat-top hexagon inscribed
                                                         (vertices at the midpoints of the left/right edges, flat
                                                         edges along top and bottom). Frame k is what the tile shows
                                                         on finale frame k: loops, cross-fades and holds resolved.
  renders/hex_tiles/<tile_id>/SOURCE.json                 what this tile was built from (+ the per-frame source map)
  renders/hex_tiles/c_painting/still.png                  2544 x 2204 centre still (the S04 overscan), 16-bit
  renders/hex_tiles/manifest.json                         {"version": 2, "res", "frames", "tiles": [...], "center"}
  renders/review/hex_tiles_sheet.png                      every tile at frames 1/60/120/180, hex mask drawn

Tiles
  chapter (crop a 1247.08 x 1080 flat-top-hex window out of the 1920 x 1080 shot frame, centre x chosen per tile by
  looking at the action over the whole window, Lanczos to 1152 x 998). Window / loop / crop centre (cx):
    c_s01_night    s01_lights_world  f31-105             ping-pong          cx  960   orb, split into coral/lime/blue,
                                                                                     carousel, merge to white
    c_s01_day      s01_lights_world  f121-240            ping-pong          cx  960   env-map clicks, glide, tilt
    c_s02_wide     s02_caustics      f1-60 + f121-180    xfade join + loop  cx 1000   caustic drop-ins, mirror-ball push
    c_s02_macro    s02_caustics      f61-120             ping-pong          cx  840   the 75 mm macro
    c_s03_gummy    s03_gummy         f1-170              hold f170 x10      cx  840   pull-out, 0.2x squash, bonk
    c_s04_gallery  s04_subject       f11-30              hold f30 x160      cx  890   the candy gallery wide.
                   storyboard_v2 makes s04_subject f1-30 bit-identical to v1 s04_every_dot f1-30, so renders/final/
                   s04_every_dot is the fallback after renders/final/s04_subject ("s04_every_dot (v1, identical f1-30)")
  Deviations from the storyboard_v2 table (logged in SOURCE.json "deviation" and the manifest):
    c_s01_night f31-120 -> f31-105: f106-120 is the launch (the orb leaves, the world blooms ink -> sky, the camera
      dollies in; up to 23/255 change per frame), which turned the one dark tile into a second day tile and flashed
      it bright on finale f76-105 while the letters land. f101-105 (white orb at rest) is a clean ping-pong turn.
    c_s03_gummy f1-180 -> f1-170 + hold: f171-180 is the whip-pan out of S03 (20-34/255 per frame); it would smear one
      tile across the film's last 10 frames, during the calm title hold. f170 is at rest.
  mini (renders/<mode>/t_<name>/f_####.png; final 1152 x 998 16-bit is byte-copied, anything else (preview 576 x 499)
  goes through Lanczos to 1152 x 998), looped per renders/meta/t_<name>.json "loop": an int L <= 180 = seamless loop
  of L frames (tile frame k = source frame ((k-1) mod L) + 1; L = 60 / 90 / 180 tiles are cyclic), null / absent =
  180 straight frames:
    t_chrome_cow t_glass_armadillo t_disco t_magnifier t_desk_lamp t_lightbulb t_fruit_sss t_material_balls
    t_jelly_cubes t_duck_pool t_sunset_bunny t_toy_town
  centre: renders/final/s04_subject/overscan.png (2544 x 2204, byte copy) -> renders/preview/s04_subject/overscan.png
  (1272 x 1102, Lanczos x2) -> placeholder = the painting scan cropped with the overscan geometry: the uv_rect and
  mirror line / PINGPONG band the S04 builder records in renders/meta/s04_subject.json "overscan" (else storyboard_v2
  section 2: canvas uv centre 0.486 / 0.633 (v from the bottom), frame height 0.49 of the canvas, still = 1.325 x
  2.041 frames, plain mirror at the painting edge). Raw scan colours: a stand-in, not seam-accurate.

Rules
  * Source priority per tile: final (every needed frame complete) -> preview (every needed frame complete) ->
    labelled placeholder (palette colour, label, running frame counter, hexagon outline + TOP tab + L/R vertex dots).
    A frame counts only if its PNG ends with IEND and decodes (others write frames while this runs); a decode
    failure in the middle of a build drops the whole tile to the next source. Sources never mix inside a tile.
  * Loops (chapter windows shorter than 180 frames), recorded per tile in SOURCE.json and the manifest:
      pingpong  forward, then backward without repeating the end frames (good where the motion eases at the ends)
      xfade     the last 6 frames of a pass dissolve into frames 1-6 of the next one (display-referred mix);
                period = window - 6
      hold      the last frame is held
  * Resampling: Pillow Lanczos (a = 3) on float32 sRGB-encoded values with an exact sub-pixel crop box, one resample
    per output frame (cross-fades are mixed before the resample), written 16-bit. Previews go through the same single
    resample (Lanczos x2 relative to their 50 % size).
  * Atomic: each tile is built in renders/hex_tiles/.tmp_<id>_<pid>/ and swapped in with renameat2(RENAME_EXCHANGE)
    (two renames if the kernel/filesystem refuses), so a tile directory is always one complete build. The manifest is
    written to a temp file and os.replace()d. A lock file serialises concurrent runs.
  * Idempotent and fast: a tile whose SOURCE.json signature (script version, plan, source files' size + mtime) matches
    and whose 180 frames are complete is skipped; repeated frames (holds, ping-pong, mini loops) are encoded once and
    hard-linked inside the tile directory; all frames go through one process pool (--jobs).

usage (from the repo root):
  tools/venv/bin/python -I scripts/make_hex_tiles.py [--only id,id] [--placeholder-only] [--require-final]
                                                     [--jobs 24] [--force] [--dry-run] [--no-sheet]
  --only            build only these ids (tile ids or c_painting); the manifest still lists every tile on disk
  --placeholder-only  every selected tile (and the centre) as a labelled placeholder
  --require-final   exit 2 unless every tile and the centre are from finals (after building what can be built)
  --force           rebuild even when a tile is up to date
  --dry-run         resolve and print the source table only; write nothing
  --print-plan ID   print the per-frame source map of one tile (after resolving its source) and exit
"""
import argparse
import ctypes
import datetime
import errno
import fcntl
import hashlib
import json
import math
import os
import shutil
import struct
import sys
import time
from concurrent.futures import FIRST_EXCEPTION, ProcessPoolExecutor, wait

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

SCRIPT_VERSION = "make_hex_tiles v2.1"
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT_ROOT = os.path.join(ROOT, "renders", "hex_tiles")
SHEET_PATH = os.path.join(ROOT, "renders", "review", "hex_tiles_sheet.png")
W, H = 1152, 998                       # tile image; flat-top hex with circumradius 576 inscribed
N_FRAMES = 180
SRC_W, SRC_H = 1920, 1080              # chapter shot frames (finals); previews are 960 x 540
HEX_R_SRC = SRC_H / math.sqrt(3.0)     # 623.538 px: circumradius of the flat-top hex spanning the frame height
CROP_W = 2.0 * HEX_R_SRC               # 1247.08 px ("the 1247 x 1080 window")
CENTER_ID = "c_painting"
CENTER_RES = (2544, 2204)              # bounding box of the flat-top hex that circumscribes the 16:9 frame
XFADE = 6
IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
PNG_LEVEL = 3                          # zlib level for the 16-bit PNGs (speed / size balance)

PALETTE = {  # lib/dopa.py D.PALETTE (copied: this script runs without Blender)
    "pink": "#FF4D9D", "coral": "#FF6A5C", "orange": "#FF8A1F", "lemon": "#FFD23F",
    "lime": "#B5E61D", "mint": "#2ED8A3", "aqua": "#1FC2EE", "blue": "#2E5BFF",
    "violet": "#8A5CF6", "lilac": "#C3A6FF",
    "blush": "#FFD3E4", "peach": "#FFDCC7", "butter": "#FFF0A8", "pistachio": "#CFF5DD",
    "sky": "#CDE9FF", "lavender": "#E5DAFF", "cream": "#FFF6EC",
    "ink": "#1C1A33", "white": "#FFFFFF", "offwhite": "#F7F5F2", "chrome": "#F4F4F8", "gold": "#FFC867",
}
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "Fredoka-Bold.ttf")
FONT_SEMI = os.path.join(ROOT, "assets", "fonts", "Fredoka-SemiBold.ttf")
FONT_DIGITS = os.path.join(ROOT, "assets", "fonts", "Nunito-Black.ttf")
PAINTING = os.path.join(ROOT, "assets", "paintings", "seurat_grande_jatte_8192.jpg")

# ---------------------------------------------------------------------------------------------------------------
# Tile table. palette = the tile's identity colour (D.PALETTE key; chapter colour for chapter tiles, the background
# family for minis), ground = the pastel used by the placeholder. cx = centre x of the hex crop in 1920-px frame
# coordinates (chosen by looking at the frames over the whole window; see the notes and the review sheet).
# ---------------------------------------------------------------------------------------------------------------
CHAPTERS = [
    # storyboard_v2 table: f31-120. Deviation: f31-105. f106-120 is the launch: the orb leaves the frame, the world
    # blooms ink -> lilac -> sky and the camera dollies in (frame-to-frame change up to 23/255), so the "dark tile"
    # turned into a second day tile and flashed bright on finale f76-105 (the letter landings) under either loop
    # mode. f101-105 (white orb at rest, change 0.1-0.4/255) is a clean ping-pong turn.
    dict(id="c_s01_night", srcs=[("s01_lights_world", "s01_lights_world")], windows=[(31, 105)],
         join="cut", loop="pingpong", cx=960.0, palette="blue", ground="ink",
         title="S01 night", label="Point lights", spec_frames="f31-120",
         note="orb glide, split into coral / lime / blue, carousel, merge to white; ping-pong turns on the white orb "
              "at rest (f101-105). Window ends at f105, not f120: the launch would bloom the dark tile to daylight"),
    dict(id="c_s01_day", srcs=[("s01_lights_world", "s01_lights_world")], windows=[(121, 240)],
         join="cut", loop="pingpong", cx=960.0, palette="blue", ground="sky",
         title="S01 day", label="Env-map clicks",
         note="locked camera: four 90-degree env clicks on the beat (tile f16/31/46/61), glide, tilt; the ping-pong "
              "turns on the settled tilt wobble (f240) and plays glide and click 4 back"),
    dict(id="c_s02_wide", srcs=[("s02_caustics", "s02_caustics")], windows=[(1, 60), (121, 180)],
         join="xfade", loop="xfade", cx=1000.0, palette="mint", ground="pistachio",
         title="S02 wide", label="Caustic drop-ins",
         note="same camera on both sides of the macro gap (only the orb moved), so the windows join with a 6-frame "
              "cross-fade; the loop dissolves the mirror-ball push back into the room (a ping-pong would reverse the "
              "push at full speed). cx 1000 keeps the drop-ins, orb, crystal bunny and most of the mirror ball"),
    dict(id="c_s02_macro", srcs=[("s02_caustics", "s02_caustics")], windows=[(61, 120)],
         join="cut", loop="pingpong", cx=840.0, palette="mint", ground="cream",
         title="S02 macro", label="Caustics macro",
         note="orb arc and camera slide ease out to rest at f120 (change 0.1/255), so the ping-pong turns cleanly; "
              "cx 840 frames the lemon ball with its hot focal caustic and the heart with its pink caustic (the "
              "ring sits on the frame edge and is half in; c_s02_wide shows it whole)"),
    # storyboard_v2 table: f1-180. Deviation: f1-170 + hold. f171-180 is the whip-pan out of S03 (change 20-34/255
    # per frame); it would smear one tile across the film's last 10 frames, during the calm title hold.
    dict(id="c_s03_gummy", srcs=[("s03_gummy", "s03_gummy")], windows=[(1, 170)],
         join="cut", loop="hold", cx=840.0, palette="coral", ground="blush",
         title="S03 gummy", label="Slow-mo squash", spec_frames="f1-180",
         note="pull-out, drop, 0.2x squash, bonk, settle; f170 (at rest, change 0.1-0.3/255) is held for the last 10 "
              "frames instead of the whip-pan f171-180. cx 840 keeps the gummy, its floor reflection, the ball "
              "from the bonk on and most of the block stack (the wall mirror is out of reach)"),
    dict(id="c_s04_gallery",
         srcs=[("s04_subject", "s04_subject"), ("s04_every_dot", "s04_every_dot (v1, identical f1-30)")],
         windows=[(11, 30)], join="cut", loop="hold", cx=890.0, palette="lemon", ground="butter",
         title="S04 gallery", label="Candy gallery",
         note="room-wide breath after the whip-in (the settle ends by f24), then f30 (the push has not started) is "
              "held; cx 890 keeps the Seurat, the armchair with the plush bunny, rug, duck and lamp"),
]
MINIS = [
    ("t_chrome_cow", "pink", "blush", "Chrome cow", "Mirror chrome"),
    ("t_glass_armadillo", "lemon", "butter", "Armadillo", "Glass caustics"),
    ("t_disco", "violet", "lilac", "Disco ball", "Light flecks"),
    ("t_magnifier", "blue", "sky", "Magnifier", "Lens refraction"),
    ("t_desk_lamp", "mint", "pistachio", "Desk lamp", "Spot + shadows"),
    ("t_lightbulb", "orange", "peach", "Light bulb", "Filament glow"),
    ("t_fruit_sss", "coral", "blush", "Fruit SSS", "Subsurface"),
    ("t_material_balls", "lemon", "butter", "Materials", "Five spheres"),
    ("t_jelly_cubes", "lime", "pistachio", "Jelly cubes", "Squash"),
    ("t_duck_pool", "aqua", "cream", "Duck pool", "Water caustics"),
    ("t_sunset_bunny", "coral", "peach", "Sunset bunny", "HDRI rotation"),
    ("t_toy_town", "aqua", "sky", "Toy town", "Sun sweep"),
]


def all_specs():
    specs = []
    for c in CHAPTERS:
        s = dict(c)
        s["kind"] = "chapter"
        specs.append(s)
    for tid, pal, ground, title, label in MINIS:
        specs.append(dict(id=tid, kind="mini", srcs=[(tid, tid)], palette=pal, ground=ground, title=title,
                          label=label, note=""))
    return specs


# ---------------------------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------------------------
def rel(p):
    return os.path.relpath(p, ROOT) if p else None


def hex_rgb01(name):
    h = PALETTE.get(name, name).lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


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


def png_info(path):
    """(width, height, bit_depth, colour_type) from the IHDR chunk, or None."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(29)
    except OSError:
        return None
    if len(head) < 29 or head[:8] != PNG_SIG or head[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h, head[24], head[25]


class SourceError(RuntimeError):
    pass


def load_float(path):
    """Decode an 8/16-bit PNG to float32 RGB in 0..1 (sRGB-encoded values). Raises SourceError."""
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SourceError(f"cannot decode {rel(path)}")
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    if im.ndim == 2:
        im = np.repeat(im[:, :, None], 3, axis=2)
    im = im[:, :, :3][:, :, ::-1].astype(np.float32) / scale
    return np.ascontiguousarray(im)


def lanczos(img, size, box=None):
    """Pillow Lanczos (widens its kernel when minifying) per channel on float data, optional sub-pixel box."""
    out = []
    for c in range(img.shape[2]):
        ch = Image.fromarray(np.ascontiguousarray(img[:, :, c], dtype=np.float32))
        out.append(np.asarray(ch.resize(size, Image.LANCZOS, box=box)))
    return np.stack(out, -1)


def write16(path, rgb):
    out = np.clip(np.rint(np.asarray(rgb, np.float64) * 65535.0), 0, 65535).astype(np.uint16)
    if not cv2.imwrite(path, np.ascontiguousarray(out[:, :, ::-1]), [cv2.IMWRITE_PNG_COMPRESSION, PNG_LEVEL]):
        raise RuntimeError(f"cannot write {path}")


def hex_vertices(w, h, inset=0.0):
    """Flat-top hexagon inscribed in a w x h box (vertices at the left/right edge midpoints), shrunk by `inset` px."""
    r = w / 2.0 - inset / math.cos(math.radians(30))
    cx, cy = w / 2.0, h / 2.0
    return [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))) for a in (180, 120, 60, 0, 300, 240)]


def hex_mask(w, h, inset=0.0, ss=4):
    """Anti-aliased float mask (1 inside) of the inscribed flat-top hexagon."""
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in hex_vertices(w, h, inset)], fill=255)
    return np.asarray(m.resize((w, h), Image.BOX), np.float32) / 255.0


# ---------------------------------------------------------------------------------------------------------------
# frame plans: a plan is a list of N_FRAMES entries; an entry is a tuple of (source_frame, weight) pairs (1..4).
# ---------------------------------------------------------------------------------------------------------------
def _mix(e1, e2, w):
    acc = {}
    for f, a in e1:
        acc[f] = acc.get(f, 0.0) + a * (1.0 - w)
    for f, a in e2:
        acc[f] = acc.get(f, 0.0) + a * w
    return tuple(sorted((f, round(a, 6)) for f, a in acc.items() if a > 1e-9))


def _xfade_join(a, b, x=XFADE):
    """The last x entries of `a` dissolve into the first x of `b` (weights 1/(x+1) .. x/(x+1))."""
    blend = [_mix(a[len(a) - x + j], b[j], (j + 1) / (x + 1)) for j in range(x)]
    return a[:-x] + blend + b[x:]


def base_sequence(windows, join):
    segs = [[((f, 1.0),) for f in range(a, b + 1)] for a, b in windows]
    seq = segs[0]
    for s in segs[1:]:
        seq = _xfade_join(seq, s) if join == "xfade" else seq + s
    return seq


def extend(seq, mode, n=N_FRAMES):
    """Resolve a window sequence to exactly n frames. Returns (plan, info)."""
    L = len(seq)
    if mode == "none":
        if L < n:
            raise ValueError(f"window has {L} frames < {n} and loop mode 'none'")
        return seq[:n], {"mode": "none", "period": None, "cyclic": False}
    if mode == "hold":
        return (seq + [seq[-1]] * max(0, n - L))[:n], {"mode": "hold", "held_frames": max(0, n - L),
                                                         "period": None, "cyclic": False}
    if mode == "pingpong":
        cycle = seq + seq[-2:0:-1]
        P = len(cycle)
        return [cycle[i % P] for i in range(n)], {"mode": "pingpong", "period": P, "cyclic": n % P == 0}
    if mode == "xfade":
        x = XFADE
        cyc = seq[x:L - x] + [_mix(seq[L - x + j], seq[j], (j + 1) / (x + 1)) for j in range(x)]
        out = list(seq[:x])
        while len(out) < n:
            out += cyc
        return out[:n], {"mode": "xfade", "xfade_frames": x, "period": len(cyc), "cyclic": False}
    if mode == "repeat":
        return [seq[i % L] for i in range(n)], {"mode": "repeat", "period": L, "cyclic": n % L == 0}
    raise ValueError(mode)


# ---------------------------------------------------------------------------------------------------------------
# source resolution
# ---------------------------------------------------------------------------------------------------------------
def read_mini_meta(tid):
    p = os.path.join(ROOT, "renders", "meta", f"{tid}.json")
    try:
        with open(p) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def mini_loop(meta):
    """Seamless loop length from the mini meta (frame loop+1 == frame 1): an int in 2..180, or None for 180
    straight frames (meta loop null / absent / longer than the finale)."""
    if not meta:
        return None
    v = meta.get("loop")
    try:
        v = int(v) if v not in (None, False, "", "none", "null") else None
    except (TypeError, ValueError):
        v = None
    return v if v and 1 < v <= N_FRAMES else None


def needed_frames(spec, meta=None):
    if spec["kind"] == "chapter":
        return sorted({f for a, b in spec["windows"] for f in range(a, b + 1)})
    L = mini_loop(meta)
    return list(range(1, (L or N_FRAMES) + 1))


def frame_path(d, f):
    return os.path.join(d, f"f_{f:04d}.png")


def candidates(spec, log):
    """Complete sources for a tile in priority order: [(kind, dir, from_label, frames, meta)]."""
    meta = read_mini_meta(spec["id"]) if spec["kind"] == "mini" else None
    frames = needed_frames(spec, meta)
    out = []
    for kind in ("final", "preview"):
        for src, label in spec["srcs"]:
            d = os.path.join(ROOT, "renders", kind, src)
            if not os.path.isdir(d):
                continue
            missing = [f for f in frames if not png_complete(frame_path(d, f))]
            if missing:
                log.append(f"{spec['id']}: {kind}/{src} has {len(frames) - len(missing)}/{len(frames)} needed "
                           f"frames (first missing f_{missing[0]:04d}) -> not used")
                continue
            info = png_info(frame_path(d, frames[0]))
            if info is None:
                log.append(f"{spec['id']}: {kind}/{src} f_{frames[0]:04d} has no PNG header -> not used")
                continue
            w, h = info[0], info[1]
            if spec["kind"] == "chapter":
                ok = abs(w / h - SRC_W / SRC_H) < 0.01
            else:
                ok = abs(w / h - W / H) < 0.01
            if not ok:
                log.append(f"{spec['id']}: {kind}/{src} is {w}x{h}, wrong aspect -> not used")
                continue
            out.append((kind, d, label, frames, meta))
    return out


# ---------------------------------------------------------------------------------------------------------------
# workers (run in the process pool)
# ---------------------------------------------------------------------------------------------------------------
def task_chapter(entries, box, out_path):
    acc = None
    shape = None
    for path, w in entries:
        im = load_float(path)
        if shape is None:
            shape = im.shape
        elif im.shape != shape:
            raise SourceError(f"{rel(path)}: size changed inside the window")
        acc = im * w if acc is None else acc + im * w
    sw, sh = shape[1], shape[0]
    s = sw / SRC_W
    if abs(sh / s - SRC_H) > 1.5:
        raise SourceError(f"{rel(entries[0][0])}: unexpected size {sw}x{sh}")
    b = (box[0] * s, box[1] * s, min(box[2] * s, sw), min(box[3] * s, sh))
    write16(out_path, lanczos(acc, (W, H), b))
    return out_path


def task_mini(path, out_path):
    """Exact 1152x998 16-bit RGB -> byte copy (after a decode check); anything else -> Lanczos to 1152x998, 16-bit."""
    info = png_info(path)
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None or info is None:
        raise SourceError(f"cannot decode {rel(path)}")
    if info[0] == W and info[1] == H and info[2] == 16 and info[3] == 2:
        shutil.copyfile(path, out_path)
        return out_path
    img = load_float(path)
    if img.shape[1] == W and img.shape[0] == H:
        write16(out_path, img)
    else:
        write16(out_path, lanczos(img, (W, H)))
    return out_path


_PH_CACHE = {}


def _text_mask(text, font, anchor_xy, stroke=0, ss=2):
    """Anti-aliased float mask of `text` centred at anchor_xy (1x px)."""
    m = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(m).text((anchor_xy[0] * ss, anchor_xy[1] * ss), text, font=font, fill=255, anchor="mm",
                           stroke_width=stroke * ss, stroke_fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS), np.float32).clip(0, 255) / 255.0


def _paint(img, mask, colour):
    a = mask[:, :, None]
    return img * (1.0 - a) + np.asarray(colour, np.float32)[None, None, :] * a


def _ph_static(spec):
    key = spec["id"]
    if key in _PH_CACHE:
        return _PH_CACHE[key]
    ss = 2
    pal, ground = hex_rgb01(spec["palette"]), hex_rgb01(spec["ground"])
    ink, white = hex_rgb01("ink"), hex_rgb01("white")
    dark = float(ground @ np.array([0.2126, 0.7152, 0.0722], np.float32)) < 0.4
    fg = white if dark else ink
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
    xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :, None]
    bg = ground[None, None, :] * (1.0 - 0.28 * yy) + pal[None, None, :] * (0.28 * yy)
    glow = np.exp(-(((xx - 0.32) / 0.42) ** 2 + ((yy - 0.20) / 0.36) ** 2))
    bg = bg + (1.0 - bg) * (0.10 if dark else 0.30) * glow
    if dark:
        bg = bg + pal[None, None, :] * 0.35 * glow
    inside = hex_mask(W, H)
    outside = pal * 0.55 + ink * 0.45
    img = bg * inside[:, :, None] + outside[None, None, :] * (1.0 - inside[:, :, None])
    # hexagon outline: ink hairline outside a white band, so the flat-top orientation is unmistakable
    ring = hex_mask(W, H, 6.0) - hex_mask(W, H, 22.0)
    hair = hex_mask(W, H, 22.0) - hex_mask(W, H, 26.0)
    img = _paint(img, np.clip(ring, 0, 1), white)
    img = _paint(img, np.clip(hair, 0, 1), ink)
    # TOP tab under the top edge, coral dot at the left vertex, aqua dot at the right vertex (mirror check)
    m = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([(W / 2 - 92) * ss, 30 * ss, (W / 2 + 92) * ss, 92 * ss], radius=31 * ss, fill=255)
    tab = np.asarray(m.resize((W, H), Image.LANCZOS), np.float32).clip(0, 255) / 255.0
    img = _paint(img, tab, ink if not dark else white)
    f_tab = ImageFont.truetype(FONT_BOLD, 40 * ss)
    img = _paint(img, _text_mask("TOP", f_tab, (W / 2, 62), ss=ss), white if not dark else ink)
    for (vx, vy), c in ((hex_vertices(W, H, 40.0)[0], "coral"), (hex_vertices(W, H, 40.0)[3], "aqua")):
        m = Image.new("L", (W * ss, H * ss), 0)
        ImageDraw.Draw(m).ellipse([(vx - 17) * ss, (vy - 17) * ss, (vx + 17) * ss, (vy + 17) * ss], fill=255)
        img = _paint(img, np.asarray(m.resize((W, H), Image.LANCZOS), np.float32).clip(0, 255) / 255.0,
                     hex_rgb01(c))
    # title (white with an ink outline), label, id + "placeholder"
    f_title = ImageFont.truetype(FONT_BOLD, 132 * ss)
    title = spec["title"]
    while f_title.getlength(title) > 900 * ss and f_title.size > 60 * ss:
        f_title = ImageFont.truetype(FONT_BOLD, f_title.size - 6 * ss)
    stroke = _text_mask(title, f_title, (W / 2, 0.285 * H), stroke=9, ss=ss)
    fill = _text_mask(title, f_title, (W / 2, 0.285 * H), ss=ss)
    img = _paint(img, stroke, ink if not dark else pal)
    img = _paint(img, fill, white)
    f_lab = ImageFont.truetype(FONT_SEMI, 62 * ss)
    img = _paint(img, _text_mask(spec["label"], f_lab, (W / 2, 0.425 * H), ss=ss), fg)
    f_id = ImageFont.truetype(FONT_SEMI, 38 * ss)
    img = _paint(img, _text_mask(f"{spec['id']}  ·  placeholder", f_id, (W / 2, 0.505 * H), ss=ss),
                 fg * 0.75 + (ground if not dark else pal) * 0.25)
    # progress track
    m = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle([272 * ss, 0.815 * H * ss - 17 * ss, (W - 272) * ss, 0.815 * H * ss + 17 * ss],
                                        radius=17 * ss, fill=255)
    track = np.asarray(m.resize((W, H), Image.LANCZOS), np.float32).clip(0, 255) / 255.0
    img = _paint(img, track, (white * 0.65 + ground * 0.35) if not dark else (pal * 0.45 + ink * 0.55))
    f_dig = ImageFont.truetype(FONT_DIGITS, 150 * ss)
    cell = max(f_dig.getlength(str(i)) for i in range(10)) / ss
    _PH_CACHE[key] = (img, fg, pal, f_dig, cell, dark)
    return _PH_CACHE[key]


PH_BAND = (548, 860)  # rows holding everything that changes per frame (counter, progress bar, orb)


def _band(draw, ss=2):
    """Rasterise draw(ImageDraw, y_offset, ss) at 2x inside PH_BAND only; returns the band's float alpha."""
    y0, y1 = PH_BAND
    m = Image.new("L", (W * ss, (y1 - y0) * ss), 0)
    draw(ImageDraw.Draw(m), y0, ss)
    return np.asarray(m.resize((W, y1 - y0), Image.LANCZOS), np.float32).clip(0, 255) / 255.0


def task_placeholder(spec, k, out_path):
    """Tile frame k (1..180): static card + fixed-width running counter + progress bar with an orb."""
    img, fg, pal, f_dig, cell, dark = _ph_static(spec)
    img = img.copy()
    y0, y1 = PH_BAND
    band = img[y0:y1]
    f_small = ImageFont.truetype(FONT_DIGITS, 84 * 2)
    xc = W / 2 - 1.5 * cell + 24
    yt = 0.655 * H

    def counter(d, off, ss):  # "f 001", every digit centred in a fixed cell so the counter never jitters
        d.text(((xc - 40) * ss, (yt - off) * ss), "f", font=f_small, fill=255, anchor="rm")
        for i, ch in enumerate(f"{k:03d}"):
            d.text(((xc + (i + 0.5) * cell) * ss, (yt - off) * ss), ch, font=f_dig, fill=255, anchor="mm")

    t = (k - 1) / (N_FRAMES - 1)
    xa, xb, yc = 272 + 17, W - 272 - 17, 0.815 * H
    xo = xa + (xb - xa) * t

    def fill(d, off, ss):
        d.rounded_rectangle([272 * ss, (yc - 17 - off) * ss, (xo + 17) * ss, (yc + 17 - off) * ss],
                            radius=17 * ss, fill=255)

    def orb(d, off, ss):
        d.ellipse([(xo - 30) * ss, (yc - 30 - off) * ss, (xo + 30) * ss, (yc + 30 - off) * ss], fill=255)

    band = _paint(band, _band(counter), fg)
    band = _paint(band, _band(fill), pal)
    band = _paint(band, _band(orb), hex_rgb01("white"))
    img[y0:y1] = band
    write16(out_path, img)
    return out_path


# ---------------------------------------------------------------------------------------------------------------
# building one tile
# ---------------------------------------------------------------------------------------------------------------
def crop_box(cx):
    cx = min(max(cx, CROP_W / 2), SRC_W - CROP_W / 2)
    return (cx - CROP_W / 2, 0.0, cx + CROP_W / 2, float(SRC_H))


def make_plan(spec, cand):
    """(plan, loop_info, frames_src) for a resolved candidate (None = placeholder)."""
    if spec["kind"] == "chapter":
        seq = base_sequence(spec["windows"], spec["join"])
        plan, info = extend(seq, spec["loop"])
        if spec["join"] == "xfade" and len(spec["windows"]) > 1:
            info["join"] = f"xfade{XFADE}"
        return plan, info, [list(w) for w in spec["windows"]]
    meta = cand[4] if cand else read_mini_meta(spec["id"])
    L = mini_loop(meta)
    seq = [((f, 1.0),) for f in range(1, (L or N_FRAMES) + 1)]
    plan, info = extend(seq, "repeat" if L else "none")
    info["meta_loop"] = meta.get("loop") if meta else None
    return plan, info, [[1, L or N_FRAMES]]


def file_sig(paths):
    h = hashlib.sha1()
    for p in paths:
        st = os.stat(p)
        h.update(f"{os.path.basename(p)}:{st.st_size}:{st.st_mtime_ns};".encode())
    return h.hexdigest()


def tile_signature(spec, cand, plan):
    h = hashlib.sha1()
    h.update(SCRIPT_VERSION.encode())
    keys = ("id", "kind", "windows", "join", "loop", "cx") if cand else ("id", "title", "label", "palette", "ground")
    h.update(json.dumps({k: spec.get(k) for k in keys}, sort_keys=True).encode())
    if cand:
        h.update(json.dumps(plan).encode())
        kind, d, label, frames, meta = cand
        h.update(f"{kind}|{rel(d)}|{label}|".encode())
        h.update(file_sig([frame_path(d, f) for f in frames]).encode())
    else:
        h.update(b"placeholder")
    return h.hexdigest()


def tile_complete(d):
    return all(png_complete(os.path.join(d, f"h_{k:04d}.png")) for k in range(1, N_FRAMES + 1))


def read_source_json(d):
    try:
        with open(os.path.join(d, "SOURCE.json")) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


_LIBC = None


def swap_in(tmp, final_dir):
    """Atomically replace final_dir by tmp (renameat2 RENAME_EXCHANGE), then delete the old content."""
    global _LIBC
    if not os.path.exists(final_dir):
        os.rename(tmp, final_dir)
        return "rename"
    try:
        if _LIBC is None:
            _LIBC = ctypes.CDLL(None, use_errno=True)
        r = _LIBC.renameat2(-100, os.fsencode(tmp), -100, os.fsencode(final_dir), 2)  # AT_FDCWD, RENAME_EXCHANGE
        if r != 0:
            e = ctypes.get_errno()
            raise OSError(e, os.strerror(e))
        shutil.rmtree(tmp, ignore_errors=True)  # tmp now holds the old tile
        return "exchange"
    except (AttributeError, OSError) as e:
        if isinstance(e, OSError) and e.errno not in (errno.EINVAL, errno.ENOSYS, errno.EPERM, errno.EXDEV):
            raise
        old = os.path.join(os.path.dirname(final_dir), f".old_{os.path.basename(final_dir)}_{os.getpid()}")
        os.rename(final_dir, old)
        os.rename(tmp, final_dir)
        shutil.rmtree(old, ignore_errors=True)
        return "rename2"


def run_tasks(pool, jobs):
    """jobs: list of (fn, args). Raises the first exception after every submitted job has finished."""
    futs = [pool.submit(fn, *a) for fn, a in jobs]
    done, pending = wait(futs, return_when=FIRST_EXCEPTION)
    err = next((f.exception() for f in done if f.exception() is not None), None)
    if err is not None:
        for f in pending:
            f.cancel()
        wait(futs)
        raise err


def tile_info(spec, cand, plan, loop_info, frames_src):
    """Metadata of a tile build (everything in SOURCE.json except signature / timing)."""
    kind = cand[0] if cand else "placeholder"
    if cand is None:  # describes the intended source mapping; the placeholder pixels count 1..180 and do not loop
        loop_info = dict(loop_info, cyclic=False, placeholder_counter="tile frame 1..180")
    crop = None
    if spec["kind"] == "chapter":
        b = crop_box(spec["cx"])
        crop = {"cx": round((b[0] + b[2]) / 2, 2), "cy": 540.0, "w": round(CROP_W, 3), "h": float(SRC_H),
                "box_1920": [round(v, 3) for v in b], "out": [W, H], "space": "1920x1080 frame px"}
    info = {
        "id": spec["id"], "kind": spec["kind"], "source": kind,
        "from": cand[2] if cand else spec["srcs"][0][0],
        "source_dir": rel(cand[1]) if cand else None,
        "frames_src": frames_src, "loop": loop_info, "crop": crop,
        "palette": spec["palette"], "palette_hex": PALETTE[spec["palette"]], "ground": spec["ground"],
        "label": spec["label"], "title": spec["title"], "note": spec.get("note", ""),
        "deviation": (f"window {spec['spec_frames']} in storyboard_v2 -> "
                      f"{'+'.join(f'f{a}-{b}' for a, b in spec['windows'])}") if spec.get("spec_frames") else None,
        "resample": ("copy" if (cand and spec["kind"] == "mini" and kind == "final") else
                     "Lanczos x2 (preview 50%)" if kind == "preview" else
                     "Lanczos crop 1247x1080 -> 1152x998" if cand else "drawn"),
        "map": [[list(p) for p in e] for e in plan] if cand else None,
    }
    if spec["kind"] == "mini":
        meta = cand[4] if cand else read_mini_meta(spec["id"])
        info["meta_bg"] = meta.get("bg") if meta else None
        info["meta_loop"] = meta.get("loop") if meta else None
    return info


def write_json_atomic(path, obj):
    with open(path + ".tmp", "w") as fh:
        json.dump(obj, fh, indent=1)
    os.replace(path + ".tmp", path)


def build_tile(spec, pool, args, log):
    tid = spec["id"]
    final_dir = os.path.join(OUT_ROOT, tid)
    cands = [] if args.placeholder_only else candidates(spec, log)
    for cand in cands + [None]:
        kind = cand[0] if cand else "placeholder"
        plan, loop_info, frames_src = make_plan(spec, cand)
        sig = tile_signature(spec, cand, plan)
        info = tile_info(spec, cand, plan, loop_info, frames_src)
        old = read_source_json(final_dir)
        if not args.force and old and old.get("signature") == sig and tile_complete(final_dir):
            stale = {k: v for k, v in info.items() if old.get(k) != v}
            if stale and not args.dry_run:  # same pixels, newer description (e.g. a mini meta changed)
                write_json_atomic(os.path.join(final_dir, "SOURCE.json"), dict(old, **info, refreshed=now()))
                return dict(old, **info, _action="up to date (meta refreshed)")
            return dict(old, **info, _action="up to date")
        if args.dry_run:
            return dict(info, _action="would build")
        tmp = os.path.join(OUT_ROOT, f".tmp_{tid}_{os.getpid()}")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        uniq = {}
        for k, entry in enumerate(plan, 1):
            uniq.setdefault(entry if cand else k, []).append(k)
        jobs = []
        for key, ks in uniq.items():
            out = os.path.join(tmp, f"h_{ks[0]:04d}.png")
            if cand is None:
                jobs.append((task_placeholder, (spec, ks[0], out)))
            elif spec["kind"] == "chapter":
                jobs.append((task_chapter, ([(frame_path(cand[1], f), w) for f, w in key], crop_box(spec["cx"]),
                                            out)))
            else:
                jobs.append((task_mini, (frame_path(cand[1], key[0][0]), out)))
        t0 = time.time()
        try:
            run_tasks(pool, jobs)
        except SourceError as e:
            log.append(f"{tid}: {kind} source failed while building ({e}) -> next source")
            shutil.rmtree(tmp, ignore_errors=True)
            continue
        for key, ks in uniq.items():  # repeated frames: hard links inside the tile (copies if the FS refuses)
            for k in ks[1:]:
                a, b = os.path.join(tmp, f"h_{ks[0]:04d}.png"), os.path.join(tmp, f"h_{k:04d}.png")
                try:
                    os.link(a, b)
                except OSError:
                    shutil.copyfile(a, b)
        if not tile_complete(tmp):
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError(f"{tid}: incomplete output in {tmp}")
        if cand:  # the sources must not have changed while we read them (a re-render in progress)
            if tile_signature(spec, cand, plan) != sig:
                log.append(f"{tid}: {kind} source files changed during the build -> rebuilding")
                shutil.rmtree(tmp, ignore_errors=True)
                return build_tile(spec, pool, args, log)
        info.update({"unique_frames": len(uniq), "signature": sig, "script": SCRIPT_VERSION, "written": now(),
                     "build_s": round(time.time() - t0, 2)})
        write_json_atomic(os.path.join(tmp, "SOURCE.json"), info)
        info["_action"] = f"built ({swap_in(tmp, final_dir)})"
        return info
    raise RuntimeError("unreachable")


# ---------------------------------------------------------------------------------------------------------------
# centre still
# ---------------------------------------------------------------------------------------------------------------
def overscan_geometry():
    """Canvas-uv rectangle of the centre still (v from the bottom) and the mirror axis above the painting.
    Prefers what the S04 builder measured (renders/meta/s04_subject.json "overscan": uv_rect, mirror_above_v);
    otherwise storyboard_v2 section 2: centre uv (0.486, 0.633), frame height 0.49 of the canvas, still =
    1.325 x 2.041 frames, mirror at the painting's own top edge."""
    try:
        with open(os.path.join(ROOT, "renders", "meta", "s04_subject.json")) as fh:
            ov = json.load(fh)["overscan"]
        u0, v0, u1, v1 = (float(x) for x in ov["uv_rect"])
        te = ov.get("texture_extension") or {}
        mv = float(te.get("mirror_above_v") or 1.0)
        band = te.get("pingpong_band_v")
        band = (mv - float(band[0])) if band else None
        return {"uv_rect": [u0, v0, u1, v1], "mirror_above_v": mv, "pingpong_band": band,
                "from": "renders/meta/s04_subject.json overscan"}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    aspect = 1.8 / 1.1982                      # canvas plane (texels are square: the scan has the same aspect)
    fh_ = 0.49
    fw = fh_ * (SRC_W / SRC_H) / aspect
    sw, sh = fw * CENTER_RES[0] / SRC_W, fh_ * CENTER_RES[1] / SRC_H
    u, v = 0.486, 0.633
    return {"uv_rect": [u - sw / 2, v - sh / 2, u + sw / 2, v + sh / 2], "mirror_above_v": 1.0,
            "pingpong_band": None, "from": "storyboard_v2 section 2"}


def painting_placeholder(out_path):
    """The S04 f180 + overscan picture straight from the painting scan, same geometry as the S04 overscan,
    mirrored above the painting like Blender's MIRROR extension (about the S04 builder's mirror line if known)."""
    img = cv2.imread(PAINTING, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"cannot read {PAINTING}")
    img = img[:, :, ::-1]
    ph, pw = img.shape[:2]
    g = overscan_geometry()
    u0, v0, u1, v1 = g["uv_rect"]
    # above the mirror line the scan is reflected (S04: a PINGPONG band, i.e. a triangle wave of the rows below it)
    top = int(round((1.0 - g["mirror_above_v"]) * ph))
    need = int(math.ceil(max(0.0, top - (1.0 - v1) * ph))) + 16
    j = np.arange(need)
    if g.get("pingpong_band"):
        B = max(1, int(round(g["pingpong_band"] * ph)))
        j = j % (2 * B)
        j = np.where(j < B, j, 2 * B - 1 - j)
    j = np.minimum(j, ph - top - 1)
    img = np.concatenate([img[top + j][::-1], img[top:]], axis=0)
    off = need - top                                       # scan row r -> extended row r + off
    box = [u0 * pw, (1.0 - v1) * ph + off, u1 * pw, (1.0 - v0) * ph + off]
    ih = img.shape[0]
    pad = int(math.ceil(max(0, -box[0], -box[1], box[2] - pw, box[3] - ih))) + 8
    x0, y0 = max(0, int(box[0]) - 8), max(0, int(box[1]) - 8)
    x1, y1 = min(pw, int(math.ceil(box[2])) + 8), min(ih, int(math.ceil(box[3])) + 8)
    sub = cv2.copyMakeBorder(img[y0:y1, x0:x1], pad, pad, pad, pad, cv2.BORDER_REFLECT)  # MIRROR extension
    ox, oy = x0 - pad, y0 - pad
    b = (box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy)
    write16(out_path, lanczos(sub.astype(np.float32) / 255.0, CENTER_RES, b))
    return {"painting": rel(PAINTING), "geometry_from": g["from"], "uv_rect": [round(x, 5) for x in g["uv_rect"]],
            "mirror_above_v": g["mirror_above_v"], "pingpong_band": g.get("pingpong_band"), "painting_px": [pw, ph],
            "extension": "mirror",
            "look": "raw scan sRGB (no gallery light / PBR Neutral): a stand-in, not seam-accurate"}


def build_center(args, log):
    final_dir = os.path.join(OUT_ROOT, CENTER_ID)
    cands = []
    if not args.placeholder_only:
        for kind, res in (("final", CENTER_RES), ("preview", (CENTER_RES[0] // 2, CENTER_RES[1] // 2))):
            p = os.path.join(ROOT, "renders", kind, "s04_subject", "overscan.png")
            if not os.path.exists(p):
                continue
            if not png_complete(p):
                log.append(f"{CENTER_ID}: {rel(p)} incomplete (no IEND) -> not used")
                continue
            info = png_info(p)
            if not info or abs(info[0] / info[1] - CENTER_RES[0] / CENTER_RES[1]) > 0.005:
                log.append(f"{CENTER_ID}: {rel(p)} is {info and info[:2]}, expected {res} -> not used")
                continue
            cands.append((kind, p, info))
    for cand in cands + [None]:
        kind = cand[0] if cand else "placeholder"
        h = hashlib.sha1((SCRIPT_VERSION + kind).encode())
        if cand:
            h.update(file_sig([cand[1]]).encode())
        else:
            h.update(file_sig([PAINTING]).encode())
            h.update(json.dumps(overscan_geometry(), sort_keys=True).encode())
        sig = h.hexdigest()
        old = read_source_json(final_dir)
        if not args.force and old and old.get("signature") == sig and png_complete(
                os.path.join(final_dir, "still.png")):
            return dict(old, _action="up to date")
        if args.dry_run:
            return {"id": CENTER_ID, "source": kind, "from": rel(cand[1]) if cand else rel(PAINTING),
                    "_action": "would build"}
        tmp = os.path.join(OUT_ROOT, f".tmp_{CENTER_ID}_{os.getpid()}")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        out = os.path.join(tmp, "still.png")
        extra = {}
        file_sig_before = file_sig([cand[1]]) if cand else None
        try:
            if cand is None:
                extra = painting_placeholder(out)
            else:
                kind_, p, info = cand
                im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
                if im is None:
                    raise SourceError(f"cannot decode {rel(p)}")
                if (info[0], info[1]) == CENTER_RES and info[2] == 16 and info[3] == 2:
                    shutil.copyfile(p, out)
                    extra = {"resample": "copy"}
                else:
                    img = load_float(p)
                    write16(out, img if (img.shape[1], img.shape[0]) == CENTER_RES else lanczos(img, CENTER_RES))
                    extra = {"resample": "Lanczos x2 (preview 50%)" if kind_ == "preview" else "converted to 16-bit"}
        except SourceError as e:
            log.append(f"{CENTER_ID}: {kind} failed ({e}) -> next source")
            shutil.rmtree(tmp, ignore_errors=True)
            continue
        if cand and file_sig([cand[1]]) != file_sig_before:  # rewritten while we read it -> start over
            log.append(f"{CENTER_ID}: {rel(cand[1])} changed during the copy -> retrying")
            shutil.rmtree(tmp, ignore_errors=True)
            return build_center(args, log)
        if not png_complete(out) or cv2.imread(out, cv2.IMREAD_UNCHANGED) is None:
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError(f"{CENTER_ID}: wrote an unreadable still")
        info = {"id": CENTER_ID, "path": rel(os.path.join(final_dir, "still.png")), "res": list(CENTER_RES),
                "source": kind, "from": rel(cand[1]) if cand else rel(PAINTING), "signature": sig,
                "script": SCRIPT_VERSION, "written": now(),
                "geometry": "flat-top hex bounding box around the S04 f180 frame; central 1920x1080 at offset "
                            "(312, 562) = S04 f180", **extra}
        with open(os.path.join(tmp, "SOURCE.json"), "w") as fh:
            json.dump(info, fh, indent=1)
        info["_action"] = f"built ({swap_in(tmp, final_dir)})"
        return info
    raise RuntimeError("unreachable")


# ---------------------------------------------------------------------------------------------------------------
# manifest, table, sheet
# ---------------------------------------------------------------------------------------------------------------
TILE_KEYS = ("id", "kind", "source", "from", "frames_src", "loop", "crop", "palette", "label")
EXTRA_KEYS = ("source_dir", "palette_hex", "ground", "title", "resample", "note", "deviation", "meta_bg", "written")


def gather_manifest(specs):
    tiles = []
    for spec in specs:
        d = os.path.join(OUT_ROOT, spec["id"])
        sj = read_source_json(d)
        if not sj or not tile_complete(d):
            continue
        t = {k: sj.get(k) for k in TILE_KEYS}
        t.update({k: sj[k] for k in EXTRA_KEYS if k in sj})
        t["dir"] = rel(d)
        t["first"] = rel(os.path.join(d, "h_0001.png"))
        t["cyclic"] = bool((sj.get("loop") or {}).get("cyclic"))
        tiles.append(t)
    center = None
    cj = read_source_json(os.path.join(OUT_ROOT, CENTER_ID))
    if cj and png_complete(os.path.join(OUT_ROOT, CENTER_ID, "still.png")):
        center = {k: cj.get(k) for k in ("id", "path", "res", "source", "from", "written")}
    ids = [s["id"] for s in specs]
    missing = [i for i in ids if i not in {t["id"] for t in tiles}]
    all_final = not missing and all(t["source"] == "final" for t in tiles) and bool(center) and \
        center["source"] == "final"
    return {"version": 2, "res": [W, H], "frames": N_FRAMES, "tiles": tiles, "center": center,
            "all_final": all_final, "missing": missing,
            "hex": "flat-top, inscribed: vertices at (0, 499) and (1152, 499), flat edges along y = 0 and y = 998",
            "screen_uv": "flat-top screen hexagon of circumradius R centred at the origin (x right, y up): "
                         "u = 0.5 + x / (2 R), v = 0.5 + y / (2 R * 998 / 1152); the centre still uses the same "
                         "mapping with 2544 x 2204 (v = 0.5 + y / (2 R * 2204 / 2544))",
            "frame_rule": "h_000k.png is what the tile shows on finale frame k (loops, cross-fades, holds resolved)",
            "script": SCRIPT_VERSION, "written": now()}


def write_manifest(man):
    p = os.path.join(OUT_ROOT, "manifest.json")
    with open(p + ".tmp", "w") as fh:
        json.dump(man, fh, indent=1)
    os.replace(p + ".tmp", p)
    return p


def describe_loop(info):
    lp = info.get("loop") or {}
    m = lp.get("mode")
    s = {"pingpong": f"ping-pong (period {lp.get('period')})", "xfade": f"xfade{lp.get('xfade_frames', XFADE)} loop "
         f"(period {lp.get('period')})", "hold": f"hold last x{lp.get('held_frames')}",
         "repeat": f"loop {lp.get('period')}", "none": "straight"}.get(m, str(m))
    if lp.get("join"):
        s = f"{lp['join']} join, " + s
    return s


def print_table(infos):
    print(f"\n{'tile':18s} {'source':11s} {'from':56s} {'frames':16s} {'loop':38s} {'cx':>6s}  action")
    print("-" * 160)
    for i in infos:
        fr = "+".join(f"f{a}-{b}" for a, b in (i.get("frames_src") or [])) if i.get("frames_src") else "still"
        cx = f"{i['crop']['cx']:.0f}" if i.get("crop") else ""
        src_from = i.get("from") or ""
        if i.get("source_dir"):
            src_from = i["source_dir"] + ("" if i.get("from") in (None, os.path.basename(i["source_dir"])) else
                                          f"  ({i['from'].split('(', 1)[-1].rstrip(')')})")
        print(f"{i['id']:18s} {i['source']:11s} {src_from[:56]:56s} {fr:16s} "
              f"{describe_loop(i) if i.get('loop') else '':38s} {cx:>6s}  {i.get('_action', '')}")
    print()


def make_sheet(man, path=SHEET_PATH):
    """Every tile at frames 1, 60, 120, 180 (hex mask drawn, outside dimmed) + the centre still, labelled."""
    tw, th = 288, 250
    gap, lab = 14, 34
    cols = 2
    frames = (1, 60, 120, 180)
    group_w = len(frames) * tw + (len(frames) - 1) * 6
    tiles = man["tiles"]
    rows = math.ceil(len(tiles) / cols)
    head = 86
    centre_h = 470
    sw = cols * group_w + (cols + 1) * 40
    sh = head + rows * (th + lab + gap) + centre_h + 60
    sheet = Image.new("RGB", (sw, sh), tuple(int(PALETTE["lavender"][i:i + 2], 16) for i in (1, 3, 5)))
    d = ImageDraw.Draw(sheet)
    f_h = ImageFont.truetype(FONT_BOLD, 40)
    f_l = ImageFont.truetype(FONT_SEMI, 21)
    ink = tuple(int(PALETTE["ink"][i:i + 2], 16) for i in (1, 3, 5))
    nfin = sum(t["source"] == "final" for t in tiles)
    d.text((40, 24), f"renders/hex_tiles  ·  {len(tiles)} tiles ({nfin} final)  ·  frames 1 / 60 / 120 / 180"
                     f"  ·  {man['written']}", font=f_h, fill=ink)
    mask = Image.fromarray((hex_mask(tw, th) * 255).astype(np.uint8), "L")
    outline = [(x, y) for x, y in hex_vertices(tw, th, 0.5)]
    src_col = {"final": (46, 216, 163), "preview": (255, 138, 31), "placeholder": (255, 77, 157)}
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        x0 = 40 + c * (group_w + 40)
        y0 = head + r * (th + lab + gap)
        lp = describe_loop(t)
        fr = "+".join(f"f{a}-{b}" for a, b in t["frames_src"]) if t.get("frames_src") else ""
        cx = f" · cx {t['crop']['cx']:.0f}" if t.get("crop") else ""
        frm = t.get("from") or ""
        d.ellipse([x0, y0 + 6, x0 + 18, y0 + 24], fill=src_col.get(t["source"], ink))
        dev = "  ·  window deviates from spec" if t.get("deviation") else ""
        d.text((x0 + 26, y0 + 3), f"{t['id']}  ·  {t['source']}  ·  {frm} {fr}  ·  {lp}{cx}{dev}",
               font=f_l, fill=ink)
        for j, k in enumerate(frames):
            p = os.path.join(ROOT, t["dir"], f"h_{k:04d}.png")
            im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if im is None:
                continue
            im = (im[:, :, ::-1].astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0))
            th_im = Image.fromarray(np.clip(np.rint(lanczos(im, (tw, th)) * 255), 0, 255).astype(np.uint8), "RGB")
            dim = Image.blend(th_im, Image.new("RGB", (tw, th), (40, 36, 70)), 0.72)
            th_im = Image.composite(th_im, dim, mask)
            dd = ImageDraw.Draw(th_im)
            dd.line(outline + [outline[0]], fill=(255, 255, 255), width=2)
            dd.text((tw / 2, th - 14), f"{k}", font=f_l, fill=(255, 255, 255), anchor="mm", stroke_width=2,
                    stroke_fill=ink)
            sheet.paste(th_im, (x0 + j * (tw + 6), y0 + lab))
    # centre still
    cy0 = head + rows * (th + lab + gap) + 10
    cen = man.get("center")
    if cen:
        im = cv2.imread(os.path.join(ROOT, cen["path"]), cv2.IMREAD_UNCHANGED)
        if im is not None:
            im = (im[:, :, ::-1].astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0))
            cw, chh = 508, 440
            th_im = Image.fromarray(np.clip(np.rint(lanczos(im, (cw, chh)) * 255), 0, 255).astype(np.uint8), "RGB")
            cm = Image.fromarray((hex_mask(cw, chh) * 255).astype(np.uint8), "L")
            dim = Image.blend(th_im, Image.new("RGB", (cw, chh), (40, 36, 70)), 0.72)
            th_im = Image.composite(th_im, dim, cm)
            dd = ImageDraw.Draw(th_im)
            o = hex_vertices(cw, chh, 0.5)
            dd.line(o + [o[0]], fill=(255, 255, 255), width=2)
            s = cw / CENTER_RES[0]
            dd.rectangle([312 * s, 562 * s, (312 + 1920) * s, (562 + 1080) * s], outline=(255, 210, 63), width=2)
            sheet.paste(th_im, (40, cy0 + lab))
            d.ellipse([40, cy0 + 6, 58, cy0 + 24], fill=src_col.get(cen["source"], ink))
            d.text((66, cy0 + 3), f"{cen['id']}  ·  {cen['source']}  ·  {cen['from']}  ·  "
                                  f"{cen['res'][0]}x{cen['res'][1]} (yellow = the S04 f180 frame)", font=f_l, fill=ink)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path + ".tmp.png", compress_level=6)
    os.replace(path + ".tmp.png", path)
    return path


# ---------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", default=None, help="comma-separated tile ids (and/or c_painting)")
    ap.add_argument("--placeholder-only", action="store_true")
    ap.add_argument("--require-final", action="store_true")
    ap.add_argument("--jobs", type=int, default=24)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--print-plan", default=None)
    a = ap.parse_args()

    specs = all_specs()
    ids = [s["id"] for s in specs] + [CENTER_ID]
    only = None
    if a.only:
        only = [x.strip() for x in a.only.split(",") if x.strip()]
        bad = [x for x in only if x not in ids]
        if bad:
            print(f"unknown tile id(s): {bad}; known: {ids}", file=sys.stderr)
            return 1
    if a.print_plan:
        spec = next(s for s in specs if s["id"] == a.print_plan)
        log = []
        cands = candidates(spec, log)
        plan, info, fs = make_plan(spec, cands[0] if cands else None)
        print(json.dumps({"source": cands[0][0] if cands else "placeholder", "loop": info, "frames_src": fs}))
        for k, e in enumerate(plan, 1):
            print(k, " + ".join(f"{w:.3f}*f{f}" for f, w in e))
        return 0

    os.makedirs(OUT_ROOT, exist_ok=True)
    lock = open(os.path.join(OUT_ROOT, ".lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another make_hex_tiles run holds renders/hex_tiles/.lock; waiting ...", flush=True)
        fcntl.flock(lock, fcntl.LOCK_EX)
    t0 = time.time()
    log, infos = [], []
    try:
        if not a.dry_run:
            for n in os.listdir(OUT_ROOT):
                if n.startswith((".tmp_", ".old_")):
                    shutil.rmtree(os.path.join(OUT_ROOT, n), ignore_errors=True)
        with ProcessPoolExecutor(max_workers=max(1, a.jobs)) as pool:
            for spec in specs:
                if only and spec["id"] not in only:
                    continue
                ts = time.time()
                info = build_tile(spec, pool, a, log)
                infos.append(info)
                print(f"  {spec['id']:18s} {info['source']:11s} {info.get('_action', ''):22s} "
                      f"{time.time() - ts:6.1f} s", flush=True)
        if not only or CENTER_ID in only:
            ts = time.time()
            info = build_center(a, log)
            infos.append(info)
            print(f"  {CENTER_ID:18s} {info['source']:11s} {info.get('_action', ''):22s} "
                  f"{time.time() - ts:6.1f} s", flush=True)
        if a.dry_run:
            print_table(infos)
            for line in log:
                print("  note:", line)
            return 0
        man = gather_manifest(specs)
        mp = write_manifest(man)
        if not a.no_sheet:
            make_sheet(man)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    for line in log:
        print("  note:", line)
    print_table(man["tiles"] + ([man["center"]] if man["center"] else []))
    nfin = sum(t["source"] == "final" for t in man["tiles"])
    print(f"{len(man['tiles'])}/{len(specs)} tiles on disk, {nfin} from finals; centre: "
          f"{man['center']['source'] if man['center'] else 'missing'}; manifest {rel(mp)}; "
          f"{time.time() - t0:.1f} s", flush=True)
    if a.require_final and not man["all_final"]:
        bad = [t["id"] for t in man["tiles"] if t["source"] != "final"] + man["missing"]
        if not man["center"] or man["center"]["source"] != "final":
            bad.append(CENTER_ID)
        print(f"REQUIRE-FINAL FAILED: not from finals: {', '.join(bad)}", file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
