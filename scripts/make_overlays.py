#!/usr/bin/env python3
"""make_overlays.py: caption and instrument overlay layer of the LaRenderer opening (storyboard 2.5 and 5.3).

Writes renders/overlays/o_0001..o_0900.png: 1920x1080 RGBA, straight alpha, sRGB display-referred, 8-bit.
Everything is drawn at 2x (3840x2160) in premultiplied float and box-downsampled once, so the candy sprites,
the type and the lat-long strip land with clean, consistent edges.

  tools/venv/bin/python -I scripts/make_overlays.py                        # all 900 frames
  tools/venv/bin/python -I scripts/make_overlays.py --frames 121-238,451   # subset (same pixels as a full run)
  tools/venv/bin/python -I scripts/make_overlays.py --slug                 # + "Illustrative · rendered with Cycles"
  tools/venv/bin/python -I scripts/make_overlays.py --sheet renders/review/overlays_sheet.png   # + review sheet

Elements (global film frames, storyboard 5.3)
  20-104   pill "Point lights" (blue dot) + dot chip: one white candy dot; coral, lime, blue pop 2 f apart at 61
  121-238  pill "Environment maps · any rotation" (blue) + chip "θ N°" (live) -> "θ 405° · tilt ±4°" from 226
  121-238  lat-long strip, top-right: candy_sky_preview.png re-projected every frame with R = Rz(-θ)·Ry(-φ)
  256-410  pill "Caustics · glass · mirrors" (mint)
  436-585  pill "Animated geometry · frame to frame" (coral); chip 445-520: "1×", "0.2× · frame 451..510", "1×"
  616-765  pill "High-res textures" (lemon); chip 631-765: "×1.0 .. ×46" (live), then "≈1 texel / px" from 706
  A window [start, end]: the POP-in starts at `start` (already visible on that frame); the 5-frame ease-in
  pop-out reaches scale 0 on `end`. Every window ends >= 2 frames before its shot's cut (asserted at start-up).

Live values: renders/meta/<id>.json, per-frame keys theta_deg, tilt_deg (s01), tau_s, rate (s03), dist_m, zoom,
px_per_texel (s04). Missing files, keys or frames fall back to the storyboard section 4 formulas (reported).

Sprites: assets/ui/pill.png, chip.png, dot_<colour>.png + sprites.json from shots/s00_ui_sprites.py. Pills and
chips are 3-sliced (left cap | repeated 1-px middle | right cap). Missing sprites fall back to numpy-drawn ones.

Deviations (Lead decision 3, visual tuning only):
  * Chip pop-ins that share the pill's start are staggered by +2 f and the strip by +4 f (a cascade, not a block).
  * Chip widths spring to fit new content instead of snapping: growing uses the POP curve (8% overshoot, 8 f),
    shrinking eases out (8 f) so the chip never squeezes below its text. Digits sit in fixed cells (cell =
    widest of 0-9), so values never jitter; text is revealed through a soft edge while the chip grows.
  * Caption separators "·" are ink at 45%; chip words ("frame", "tilt", "texel / px") are ink at 62%.
  * No project font has θ, so it is built from Nunito Black "0" plus a crossbar of the font's stroke weight.
  * The slug (off by default) is white at 60% over the S01 night phase and cross-fades to ink by f121.

Film v2 (docs/storyboard_v2.md section 6): --film v2 (default v1: everything above, unchanged)
  tools/venv/bin/python -I scripts/make_overlays.py --film v2              # renders/overlays_v2/o_0001..o_0960.png
  table docs/shots_v2.json (960 frames). S01-S03 elements are exactly v1's (same frames, same meta).
  616-775  pill "High-res textures" (lemon), window end 776: popped out on f776, so 776-780 are clean (the
           cut-safety check needs 779-780)
  631-775  chip "×1.0 .. ×7.0" live from renders/meta/s04_subject.json per-frame `zoom` (d0/d of the new push);
           no "≈1 texel / px" chip in v2
  781-960  nothing (the finale has no overlays; asserted by the self-test)
  If renders/meta/s04_subject.json (or its `zoom` column) is missing, the chip uses the documented fallback
  zoom(f) = 7.0 ** ease_in_out_sine((f - 31) / (145 - 31)) on local frames (×1.0 until f31, ×7.0 from f145:
  storyboard_v2 section 2 timing, push from f31, arrival ≈ f135-150, static f150-180, end ≈ ×7) and says so.
"""
import argparse
import json
import math
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SHOTS_JSON = os.path.join(ROOT, "docs", "shots.json")
UI_DIR = os.path.join(ROOT, "assets", "ui")
FONT_LABEL = os.path.join(ROOT, "assets", "fonts", "Fredoka-SemiBold.ttf")
FONT_CHIP = os.path.join(ROOT, "assets", "fonts", "Nunito-Black.ttf")
SKY_PREVIEW = os.path.join(ROOT, "assets", "hdri", "candy_sky_preview.png")
META_DIR = os.path.join(ROOT, "renders", "meta")
OUT_DIR = os.path.join(ROOT, "renders", "overlays")

FW, FH, S = 1920, 1080, 2          # film size, supersampling factor
N_FILM = 900
PALETTE = {  # lib/dopa.py D.PALETTE (sRGB); dopa itself needs bpy, so it is mirrored here
    "pink": "#FF4D9D", "coral": "#FF6A5C", "orange": "#FF8A1F", "lemon": "#FFD23F", "lime": "#B5E61D",
    "mint": "#2ED8A3", "aqua": "#1FC2EE", "blue": "#2E5BFF", "violet": "#8A5CF6", "lilac": "#C3A6FF",
    "blush": "#FFD3E4", "peach": "#FFDCC7", "butter": "#FFF0A8", "pistachio": "#CFF5DD", "sky": "#CDE9FF",
    "lavender": "#E5DAFF", "cream": "#FFF6EC", "ink": "#1C1A33", "white": "#FFFFFF", "offwhite": "#F7F5F2",
}

# ---- layout, 1x pixels (storyboard 2.5); multiplied by S where drawn ----------------------------------------
MARGIN = 80            # pills: left and bottom; strip: top and right
PILL_H, LABEL_PX = 60, 32
DOT_PX, DOT_INSET = 22, 14
LABEL_GAP, PILL_PAD_R = 12, 26       # dot -> label, label -> right end (tuned)
CHIP_H, CHIP_PX, CHIP_GAP = 48, 28, 10
CHIP_PAD = 18                        # text chips, each side (tuned)
CHIP_DOT_PX, CHIP_DOT_GAP, CHIP_DOT_PAD = 26, 7, 11
STRIP_W, STRIP_H, STRIP_R, STRIP_BORDER = 384, 192, 18, 6
SLUG_PX = 20
SEP_ALPHA, WORD_ALPHA = 0.45, 0.62
INK = "#1C1A33"

# ---- timeline (global film frames) -----------------------------------------------------------------------------
PILLS = [
    dict(id="s01a", text="Point lights", dot="blue", start=20, end=104),
    dict(id="s01b", text="Environment maps · any rotation", dot="blue", start=121, end=238),
    dict(id="s02", text="Caustics · glass · mirrors", dot="mint", start=256, end=410),
    dict(id="s03", text="Animated geometry · frame to frame", dot="coral", start=436, end=585),
    dict(id="s04", text="High-res textures", dot="lemon", start=616, end=765),
]
CHIPS = {
    "s01a": dict(kind="dots", start=22, end=104),
    "s01b": dict(kind="theta", start=123, end=238),
    "s03": dict(kind="rate", start=445, end=520),
    "s04": dict(kind="zoom", start=631, end=765),
}
STRIP = dict(start=125, end=238)
S01_DOT_SPLIT = 61                    # white dot -> coral (61), lime (63), blue (65)
S01_TILT_FROM = 226
S03_SLOW = (451, 510)                 # "0.2× · frame N" on these film frames, "1×" around them
S04_TEXEL_FROM = 706
S04_ID = "s04_every_dot"              # the shot whose meta drives the zoom chip
POP_N, OUT_N, WIDTH_N = 8, 5, 8
SHEET_FRAMES = [25, 61, 100, 125, 140, 196, 230, 260, 300, 440, 451, 480, 515, 620, 650, 710, 760]
FILM = "v1"

# ---- film v2 (storyboard_v2 section 6): S01-S03 exactly as v1, the new S04 window, nothing in the finale --------
PILLS_V2 = PILLS[:4] + [dict(id="s04", text="High-res textures", dot="lemon", start=616, end=776)]
CHIPS_V2 = dict(CHIPS, s04=dict(kind="zoom", start=631, end=776))
SHEET_FRAMES_V2 = [25, 61, 125, 196, 230, 300, 451, 515, 620, 640, 680, 720, 750, 772, 776, 779, 781, 900]
FILMS = {
    "v1": dict(table=SHOTS_JSON, frames=900, out=OUT_DIR, pills=PILLS, chips=CHIPS, s04=S04_ID,
               texel_from=S04_TEXEL_FROM, sheet=SHEET_FRAMES),
    "v2": dict(table=os.path.join(ROOT, "docs", "shots_v2.json"), frames=960,
               out=os.path.join(ROOT, "renders", "overlays_v2"), pills=PILLS_V2, chips=CHIPS_V2, s04="s04_subject",
               texel_from=None, sheet=SHEET_FRAMES_V2),
}
S04V2_ZOOM_END, S04V2_PUSH = 7.0, (31, 145)       # fallback curve only (meta missing)


def configure(film):
    """Select the film: rebinds the module-level timeline/paths (before the Overlay is built or workers fork)."""
    global FILM, SHOTS_JSON, N_FILM, OUT_DIR, PILLS, CHIPS, S04_ID, S04_TEXEL_FROM, SHEET_FRAMES
    c = FILMS[film]
    FILM, SHOTS_JSON, N_FILM, OUT_DIR = film, c["table"], c["frames"], c["out"]
    PILLS, CHIPS, S04_ID, S04_TEXEL_FROM, SHEET_FRAMES = c["pills"], c["chips"], c["s04"], c["texel_from"], c["sheet"]


# =================================================================================================================
# easing (lib/dopa.py conventions)
def clamp01(t):
    return 0.0 if t < 0 else (1.0 if t > 1 else t)


def smoothstep(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def smootherstep(t):
    t = clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def ease_in_cubic(t):
    return clamp01(t) ** 3


def ease_out_cubic(t):
    return 1 - (1 - clamp01(t)) ** 3


def ease_in_out_sine(t):
    return -(math.cos(math.pi * clamp01(t)) - 1) / 2


def ease_out_back(t, s=1.5):
    """s=1.5 peaks at exactly 1.08 (t=0.6) and lands on 1 with zero velocity: the 0 -> 1.08 -> 1 POP."""
    t = clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def prog(f, f0, f1):
    return clamp01((f - f0) / float(f1 - f0)) if f1 != f0 else float(f >= f1)


def pop_in(k, n=POP_N):
    """k = 1 on the first frame of the window."""
    return 0.0 if k <= 0 else (1.0 if k >= n else ease_out_back(k / n))


def pop_out(f, end, n=OUT_N):
    return 1.0 if f <= end - n else 1.0 - ease_in_cubic((f - (end - n)) / n)


def presence(f, start, end):
    if f < start or f >= end:
        return 0.0
    return pop_in(f - start + 1) * pop_out(f, end)


def rnd(x):
    return int(math.floor(x + 0.5))


# =================================================================================================================
# storyboard formulas (fallbacks when renders/meta is missing). S01 local == global.
def s01_theta(f):
    if f <= 135:
        return 0.0
    if f <= 195:
        k = min(3, (f - 136) // 15)
        t = f - (136 + 15 * k)
        c = 1.028 * smootherstep(t / 10) if t <= 10 else 1.028 - 0.028 * smoothstep((t - 10) / 4)
        return 90.0 * k + 90.0 * c
    if f <= 225:
        return 360.0 + 45.0 * ease_in_out_sine((f - 196) / 29)
    return 405.0


def s01_phi(f):
    if f < 226:
        return 0.0
    t = (f - 226) / 30.0
    return 6.0 * math.exp(-3 * t) * math.sin(2 * math.pi * 2 * t)


def s03_rate(fl):
    if fl <= 25:
        return 1.0
    if fl <= 31:
        return 1.0 - 0.8 * (fl - 25) / 6
    if fl <= 85:
        return 0.2
    if fl <= 91:
        return 0.2 + 0.8 * (fl - 85) / 6
    return 1.0


def s03_tau(fl):
    if fl <= 25:
        return (fl - 1) / 30.0
    if fl <= 31:
        u = fl - 25
        return 0.8 + (u - 0.8 * u * u / 12) / 30.0
    if fl <= 85:
        return 0.92 + 0.2 * (fl - 31) / 30.0
    if fl <= 91:
        u = fl - 85
        return 1.28 + (0.2 * u + 0.8 * u * u / 12) / 30.0
    return 1.40 + (fl - 91) / 30.0


S04_D0, S04_D1 = 8.076, 0.175


def s04_dist(fl):
    return S04_D0 * (S04_D1 / S04_D0) ** ease_in_out_sine(prog(fl, 31, 105))


def s04_zoom(fl):
    return S04_D0 / s04_dist(fl)


def s04v2_zoom(fl):
    """v2 fallback (no s04_subject meta yet): ×1.0 -> ×7.0, log-space ease over the storyboard_v2 push window."""
    return S04V2_ZOOM_END ** ease_in_out_sine(prog(fl, *S04V2_PUSH))


FORMULAS = {
    "s01_lights_world": {"theta_deg": s01_theta, "tilt_deg": s01_phi},
    "s03_gummy": {"tau_s": s03_tau, "rate": s03_rate},
    "s04_every_dot": {"dist_m": s04_dist, "zoom": s04_zoom},
    "s04_subject": {"zoom": s04v2_zoom},
}
ALIASES = {
    "theta_deg": ["theta_deg", "theta", "theta_degrees", "env_rot_deg"],
    "tilt_deg": ["tilt_deg", "phi_deg", "tilt", "phi"],
    "tau_s": ["tau_s", "tau"],
    "rate": ["rate", "speed", "time_rate", "playback_rate"],
    "dist_m": ["dist_m", "distance_m", "d_m", "dist", "distance"],
    "zoom": ["zoom", "zoom_x", "magnification"],
    "px_per_texel": ["px_per_texel", "pixels_per_texel"],
}


# =================================================================================================================
# shot table and meta
def load_shots():
    with open(SHOTS_JSON) as fh:
        return json.load(fh)


def _is_int(k):
    try:
        int(str(k))
        return True
    except ValueError:
        return False


def _frames_table(obj):
    """{frame -> {key: value}} from the plausible per-frame layouts (rows keyed by frame, a list of rows,
    or columns of values)."""
    pf = obj
    if isinstance(obj, dict):
        for k in ("per_frame", "frames", "perFrame", "per_frame_values", "values"):
            if k in obj:
                pf = obj[k]
                break
    table = {}
    if isinstance(pf, list):
        for i, e in enumerate(pf):
            if isinstance(e, dict):
                fr = next((e[k] for k in ("frame", "local_frame", "f", "local") if k in e), i + 1)
                table[int(fr)] = e
    elif isinstance(pf, dict):
        keys = list(pf.keys())
        if keys and all(_is_int(k) for k in keys):
            for k, v in pf.items():
                table[int(k)] = v if isinstance(v, dict) else {"value": v}
        else:
            frames_col = next((pf[k] for k in ("frame", "frames", "local_frame") if isinstance(pf.get(k), list)), None)
            for name, colv in pf.items():
                if isinstance(colv, list):
                    for i, v in enumerate(colv):
                        fr = int(frames_col[i]) if frames_col is not None else i + 1
                        table.setdefault(fr, {})[name] = v
                elif isinstance(colv, dict):
                    for k, v in colv.items():
                        if _is_int(k):
                            table.setdefault(int(k), {})[name] = v
    return table


class ShotValues:
    """Per-frame instrument values for one shot: meta first, storyboard formula second."""

    def __init__(self, shot, log):
        self.id, self.start, self.n = shot["id"], int(shot["start_frame_in_film"]), int(shot["frames"])
        self.path = os.path.join(META_DIR, f"{self.id}.json")
        self.table, self.global_keys = {}, False
        self.used = {}
        if os.path.exists(self.path):
            try:
                with open(self.path) as fh:
                    obj = json.load(fh)
                self.table = _frames_table(obj)
                ks = list(self.table)
                if ks and self.start > 1 and min(ks) >= self.start:
                    self.global_keys = True
                rows = list(self.table.values())
                if rows and all(("global_frame" in r or "film_frame" in r) for r in rows[:3]):
                    gk = "global_frame" if "global_frame" in rows[0] else "film_frame"
                    self.table = {int(r[gk]) - self.start + 1: r for r in rows}
                    self.global_keys = False
                log.append(f"meta {self.id}: {len(self.table)} frames from {os.path.relpath(self.path, ROOT)}"
                           f"{' (global frame keys)' if self.global_keys else ''}")
            except (OSError, ValueError) as e:
                log.append(f"meta {self.id}: unreadable ({e}); using storyboard formulas")
                self.table = {}
        else:
            log.append(f"meta {self.id}: missing; using storyboard formulas")

    def get(self, key, f_global):
        fl = f_global - self.start + 1
        row = self.table.get(f_global if self.global_keys else fl)
        if row:
            for k in ALIASES.get(key, [key]):
                v = row.get(k)
                if isinstance(v, (int, float)) and math.isfinite(v):
                    self._mark(key, "meta")
                    return float(v)
        fn = FORMULAS.get(self.id, {}).get(key)
        if fn is None:
            return None
        self._mark(key, "formula")
        return float(fn(fl))

    def _mark(self, key, src):
        old = self.used.get(key)
        self.used[key] = src if old in (None, src) else "meta+formula"


# =================================================================================================================
# 2x drawing on premultiplied float32 RGBA arrays (sRGB-encoded values)
def hex_rgb(c):
    h = PALETTE.get(c, c).lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def solid(mask, colour, alpha=1.0):
    """Premultiplied RGBA layer of `colour` with coverage `mask`."""
    a = (mask * alpha).astype(np.float32)
    rgb = hex_rgb(colour) if isinstance(colour, str) else np.asarray(colour, np.float32)
    return np.concatenate([a[..., None] * rgb[None, None, :], a[..., None]], axis=-1)


def over_into(dst, src, x, y):
    """Premultiplied `src` over `dst` with src's top-left at integer (x, y). Returns the touched box or None."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return None
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    d *= 1.0 - s[..., 3:4]
    d += s
    return x0, y0, x1, y1


def place_into(dst, src, anchor, pos, scale):
    """Scale `src` by `scale` about its point `anchor` (continuous px, pixel i spans [i, i+1)) and composite it
    so the anchor lands on `pos`. Integer-aligned scale-1 placements are exact copies (no resampling)."""
    if scale <= 1e-3:
        return None
    ax, ay = anchor
    tx, ty = pos
    ox, oy = tx - ax, ty - ay
    if abs(scale - 1.0) < 1e-9 and abs(ox - round(ox)) < 1e-6 and abs(oy - round(oy)) < 1e-6:
        return over_into(dst, src, int(round(ox)), int(round(oy)))
    img, sx, sy = src, scale, scale
    h, w = src.shape[:2]
    if scale < 0.8:                       # area prefilter, then a near-unity warp for the sub-pixel part
        nw, nh = max(1, rnd(w * scale)), max(1, rnd(h * scale))
        img = cv2.resize(src, (nw, nh), interpolation=cv2.INTER_AREA)
        fx, fy = nw / w, nh / h
        ax, ay = ax * fx, ay * fy
        sx, sy = scale / fx, scale / fy
    hh, ww = img.shape[:2]
    X0, Y0 = math.floor(tx - sx * ax) - 1, math.floor(ty - sy * ay) - 1
    X1, Y1 = math.ceil(tx + sx * (ww - ax)) + 1, math.ceil(ty + sy * (hh - ay)) + 1
    M = np.float32([[sx, 0, sx * (0.5 - ax) + tx - 0.5 - X0], [0, sy, sy * (0.5 - ay) + ty - 0.5 - Y0]])
    patch = cv2.warpAffine(img, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                           borderValue=(0, 0, 0, 0))
    np.clip(patch, 0.0, 1.0, out=patch)
    return over_into(dst, patch, X0, Y0)


def rrect_mask(h, w, x0, y0, bw, bh, r):
    """Anti-aliased rounded-rectangle coverage (signed distance at pixel centres, 1-px ramp)."""
    ys = np.arange(h, dtype=np.float32)[:, None] + 0.5
    xs = np.arange(w, dtype=np.float32)[None, :] + 0.5
    qx = np.abs(xs - (x0 + bw / 2)) - (bw / 2 - r)
    qy = np.abs(ys - (y0 + bh / 2)) - (bh / 2 - r)
    sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return np.clip(0.5 - sd, 0.0, 1.0).astype(np.float32)


def blur(a, sigma):
    k = int(math.ceil(sigma * 3)) * 2 + 1
    return cv2.GaussianBlur(a, (k, k), sigma, borderType=cv2.BORDER_CONSTANT)


def fade_border(img, n=6):
    h, w = img.shape[:2]
    wy = np.clip(np.minimum(np.arange(h), np.arange(h)[::-1]) / float(n), 0, 1)
    wx = np.clip(np.minimum(np.arange(w), np.arange(w)[::-1]) / float(n), 0, 1)
    return img * (wy[:, None] * wx[None, :])[..., None].astype(np.float32)


class Canvas:
    """Full 2x canvas (lazy zeros) with a dirty box so only touched pixels are downsampled."""

    def __init__(self):
        self.a = np.zeros((FH * S, FW * S, 4), np.float32)
        self.box = None

    def _grow(self, b):
        if b is None:
            return
        if self.box is None:
            self.box = list(b)
        else:
            self.box = [min(self.box[0], b[0]), min(self.box[1], b[1]), max(self.box[2], b[2]),
                        max(self.box[3], b[3])]

    def over(self, src, x, y):
        self._grow(over_into(self.a, src, x, y))

    def place(self, src, anchor, pos, scale):
        self._grow(place_into(self.a, src, anchor, pos, scale))

    def to_rgba8(self):
        out = np.zeros((FH, FW, 4), np.uint8)
        if self.box is None:
            return out
        x0, y0, x1, y1 = self.box
        x0, y0 = x0 - x0 % S, y0 - y0 % S
        x1, y1 = x1 + (-x1) % S, y1 + (-y1) % S
        r = self.a[y0:y1, x0:x1]
        small = r.reshape((y1 - y0) // S, S, (x1 - x0) // S, S, 4).mean(axis=(1, 3))
        a = small[..., 3:4]
        rgb = np.where(a > 1e-6, small[..., :3] / np.maximum(a, 1e-6), 0.0)
        q = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)], axis=-1)
        out[y0 // S:y1 // S, x0 // S:x1 // S] = np.floor(q * 255 + 0.5).astype(np.uint8)
        out[..., :3][out[..., 3] == 0] = 0
        return out


# =================================================================================================================
# type
class Font:
    def __init__(self, path, px):
        self.f = ImageFont.truetype(path, px)
        self.px = px
        self.asc, self.desc = self.f.getmetrics()
        self.cap = -self.f.getbbox("H", anchor="ls")[1]
        self.cell = max(self.f.getlength(d) for d in "0123456789")
        self.theta = self._theta_bar() if path == FONT_CHIP else None

    def _theta_bar(self):
        """Crossbar for a θ built on this font's "0": inner counter edges at mid-height and the horizontal
        stroke weight, as integer offsets from the glyph's drawing origin (left, baseline)."""
        pad = self.px
        im = Image.new("L", (self.px * 3, self.px * 3), 0)
        ImageDraw.Draw(im).text((pad, 2 * pad), "0", font=self.f, fill=255, anchor="ls")
        m = np.asarray(im, np.float32) / 255.0
        rows = np.where(m.max(1) > 0.5)[0]
        cols = np.where(m.max(0) > 0.5)[0]
        yc = (rows.min() + rows.max() + 1) / 2.0
        line = np.where(m[int(yc)] > 0.5)[0]
        gaps = np.where(np.diff(line) > 1)[0]
        xl, xr = line[gaps[0]] + 1, line[gaps[0] + 1]           # counter [xl, xr)
        cx = (cols.min() + cols.max()) // 2
        col = np.where(m[:, cx] > 0.5)[0]
        g2 = np.where(np.diff(col) > 1)[0]
        stroke = col[g2[0]] - col.min() + 1
        t = max(2, rnd(stroke * 0.92))
        y0 = rnd(yc - t / 2.0)
        return (xl - 1 - pad, y0 - 2 * pad, xr + 1 - pad, y0 + t - 2 * pad)   # x0, y0, x1, y1 rel. (origin)

    def adv(self, ch):
        return self.f.getlength("0" if ch == "θ" else ch)


def layout(segments, font, tabular):
    """segments [(text, alpha)] -> items [(x, text, alpha)], width. tabular: every digit centred in a fixed cell
    (font.cell) and every other character on its own advance, so values never shift; else whole segments."""
    items, x = [], 0.0
    for text, alpha in segments:
        if not tabular:
            items.append((x, text, alpha))
            x += font.f.getlength(text)
            continue
        for ch in text:
            if ch.isdigit():
                items.append((x + (font.cell - font.adv(ch)) / 2.0, ch, alpha))
                x += font.cell
            else:
                items.append((x, ch, alpha))
                x += font.adv(ch)
    return items, x


def text_mask(items, width, font, pad=8):
    """Coverage mask with the baseline at row `base` and x=0 at column `pad`."""
    w = int(math.ceil(width)) + 2 * pad
    h = font.asc + font.desc + 2 * pad
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    base = pad + font.asc
    for x, s, alpha in items:
        v = rnd(255 * alpha)
        gx = rnd(x + pad)
        if s == "θ" and font.theta:
            d.text((gx, base), "0", font=font.f, fill=v, anchor="ls")
            x0, y0, x1, y1 = font.theta
            d.rectangle([gx + x0, base + y0, gx + x1 - 1, base + y1 - 1], fill=v)
        else:
            d.text((gx, base), s, font=font.f, fill=v, anchor="ls")
    return np.asarray(im, np.float32) / 255.0, pad, base


def split_label(text):
    parts = text.split(" · ")
    segs = []
    for i, p in enumerate(parts):
        if i:
            segs.append((" · ", SEP_ALPHA))
        segs.append((p, 1.0))
    return segs


# =================================================================================================================
# sprites
def load_rgba16(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim != 3 or im.shape[2] != 4:
        return None
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32)[..., [2, 1, 0, 3]] / scale
    im[..., :3] *= im[..., 3:4]                      # premultiply
    return im


def synth_capsule(body_h, length_ratio=4.0):
    """Numpy-drawn candy capsule (fallback when the Cycles sprite is missing). Same geometry contract as
    shots/s00_ui_sprites.py: body_h px high, margins (10, 8, 10, 15)/24 of body_h."""
    ml, mt, mr, mb = (rnd(body_h * m / 24) for m in (10, 8, 10, 15))
    bw = rnd(body_h * length_ratio)
    W, H = ml + bw + mr, mt + body_h + mb
    body = rrect_mask(H, W, ml, mt, bw, body_h, body_h / 2)
    ys = (np.arange(H, dtype=np.float32)[:, None] + 0.5 - (mt + body_h / 2)) / (body_h / 2)   # -1 top, +1 bottom
    shade = 0.975 - 0.085 * smoothstep_np((ys + 0.15) / 1.15)
    streak = 0.05 * np.exp(-((ys + 0.55) / 0.12) ** 2)
    xs = np.arange(W, dtype=np.float32)[None, :] + 0.5
    inner = np.clip(np.minimum(xs - ml - body_h * 0.45, ml + bw - body_h * 0.45 - xs) / (body_h * 0.3), 0, 1)
    lum = np.clip(shade + streak * inner, 0, 1)
    rgb = np.stack([lum * 0.995, lum * 0.993, lum], -1)
    sh = blur(np.roll(body, rnd(body_h * 0.07), axis=0), body_h * 0.09) * 0.32
    a = body + sh * (1 - body)
    img = np.concatenate([rgb * body[..., None], a[..., None]], -1).astype(np.float32)
    meta = {"size": [W, H], "body": [ml, mt, ml + bw, mt + body_h], "body_h": body_h, "cap": body_h / 2}
    return img, meta


def smoothstep_np(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def synth_dot(colour, diam=96, size=128):
    c = (size / 2.0, size / 2.0 - 0.06 * diam)
    ys = np.arange(size, dtype=np.float32)[:, None] + 0.5
    xs = np.arange(size, dtype=np.float32)[None, :] + 0.5
    r = diam / 2.0
    dx, dy = (xs - c[0]) / r, (ys - c[1]) / r
    rr = np.hypot(dx, dy)
    cov = np.clip((1 - rr) * r + 0.5, 0, 1)
    nz = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
    lam = np.clip(-0.45 * dy + 0.85 * nz, 0, 1)
    base = hex_rgb(colour)
    rgb = base[None, None, :] * (0.55 + 0.5 * lam[..., None])
    spec = np.exp(-(((dx - 0.0) / 0.18) ** 2 + ((dy + 0.55) / 0.12) ** 2)) * 0.85
    rgb = np.clip(rgb + spec[..., None], 0, 1)
    sh = blur(np.roll(cov, rnd(diam * 0.08), axis=0), diam * 0.08) * 0.3
    a = cov + sh * (1 - cov)
    img = np.concatenate([rgb * cov[..., None], a[..., None]], -1).astype(np.float32)
    return img, {"center": list(c), "diameter": diam, "size": [size, size]}


def tint_shadow(img, body_cov, colour=INK):
    """Cycles' shadow catcher leaves black shadows; recolour the part of alpha outside the body to ink (indigo),
    which sits better on candy grounds. img is premultiplied and modified in place."""
    sh = np.clip(img[..., 3] - body_cov, 0.0, 1.0)
    img[..., :3] += sh[..., None] * hex_rgb(colour)[None, None, :]
    return img


def radial_fade(img, centre, radius, r0=1.3, r1=1.85, drop=0.12):
    """Fade a sphere sprite's shadow/halo to zero between r0 and r1 radii (centre dropped a little toward the
    cast shadow), so no square plate can show around a dot."""
    h, w = img.shape[:2]
    ys = np.arange(h, dtype=np.float32)[:, None] + 0.5 - (centre[1] + drop * radius)
    xs = np.arange(w, dtype=np.float32)[None, :] + 0.5 - centre[0]
    t = np.clip((np.hypot(xs, ys) / radius - r0) / (r1 - r0), 0, 1)
    return img * (1.0 - t * t * (3 - 2 * t))[..., None].astype(np.float32)


class Sprites:
    def __init__(self, log, force_fallback=False):
        meta = {}
        mp = os.path.join(UI_DIR, "sprites.json")
        if os.path.exists(mp) and not force_fallback:
            with open(mp) as fh:
                meta = json.load(fh)
        self.caps, self.dots = {}, {}
        for name, body_h in (("pill", PILL_H * S), ("chip", CHIP_H * S)):
            m = meta.get(name)
            img = load_rgba16(os.path.join(UI_DIR, m["file"])) if m else None
            if img is None and name == "chip" and "pill" in self.caps and self.caps["pill"][2] == "sprite":
                pimg, pm, _ = self.caps["pill"]
                k = body_h / pm["body_h"]
                img = cv2.resize(pimg, (rnd(pimg.shape[1] * k), rnd(pimg.shape[0] * k)), interpolation=cv2.INTER_AREA)
                m = {"body": [v * k for v in pm["body"]], "body_h": body_h, "cap": body_h / 2}
                log.append("sprite chip.png missing: using pill.png scaled to 48 px")
                self.caps[name] = (img, m, "sprite")
                continue
            if img is None:
                img, m = synth_capsule(body_h)
                self.caps[name] = (img, m, "fallback")
                log.append(f"sprite {name}.png missing: Pillow/numpy fallback capsule")
                continue
            if abs(m["body_h"] - body_h) > 0.5:                      # re-rendered at another size: rescale
                k = body_h / m["body_h"]
                img = cv2.resize(img, (rnd(img.shape[1] * k), rnd(img.shape[0] * k)), interpolation=cv2.INTER_AREA)
                m = dict(m, body=[v * k for v in m["body"]], body_h=body_h, cap=body_h / 2)
            x0, y0, x1, y1 = m["body"]
            cov = rrect_mask(img.shape[0], img.shape[1], x0, y0, x1 - x0, y1 - y0, (y1 - y0) / 2.0)
            self.caps[name] = (tint_shadow(fade_border(img), cov), m, "sprite")
        for c in ("blue", "mint", "coral", "lemon", "white", "lime"):
            m = meta.get("dots", {}).get(c)
            img = load_rgba16(os.path.join(UI_DIR, m["file"])) if m else None
            if img is None:
                img, m = synth_dot(c)
                log.append(f"sprite dot_{c}.png missing: numpy fallback sphere")
                self.dots[c] = (img, m, "fallback")
            else:
                cx, cy = m["center"]
                r = m["diameter"] / 2.0
                img = radial_fade(fade_border(img, 4), (cx, cy), r)
                ys = np.arange(img.shape[0], dtype=np.float32)[:, None] + 0.5 - cy
                xs = np.arange(img.shape[1], dtype=np.float32)[None, :] + 0.5 - cx
                cov = np.clip(r - np.hypot(xs, ys) + 0.5, 0, 1)
                self.dots[c] = (tint_shadow(img, cov), m, "sprite")

    def capsule(self, name, body_w):
        """3-slice to an integer body width (>= body height). Returns (img, anchor = left end, mid-height)."""
        img, m, _ = self.caps[name]
        x0, y0, x1, y1 = (rnd(v) for v in m["body"])
        bh = y1 - y0
        bw = max(int(body_w), bh)
        sw = x1 - x0
        if bw >= sw:
            c = (x0 + x1) // 2
            out = np.concatenate([img[:, :c], np.repeat(img[:, c:c + 1], bw - sw, axis=1), img[:, c:]], axis=1)
        else:
            a = bw // 2
            out = np.concatenate([img[:, :x0 + a], img[:, x1 - (bw - a):]], axis=1)
        return np.ascontiguousarray(out), (float(x0), (y0 + y1) / 2.0), (x0, y0, x0 + bw, y1)

    def dot(self, colour):
        img, m, _ = self.dots[colour]
        return img, tuple(m["center"]), float(m["diameter"])


# =================================================================================================================
# elements
class Overlay:
    def __init__(self, slug=False, fallback_sprites=False):
        self.log = []
        self.slug = slug
        self.shots = {s["id"]: s for s in load_shots()}
        self.sprites = Sprites(self.log, force_fallback=fallback_sprites)
        self.label_font = Font(FONT_LABEL, LABEL_PX * S)
        self.chip_font = Font(FONT_CHIP, CHIP_PX * S)
        self.slug_font = Font(FONT_LABEL, SLUG_PX * S)
        self.vals = {k: ShotValues(self.shots[k], self.log)
                     for k in ("s01_lights_world", "s03_gummy", S04_ID) if k in self.shots}
        if FILM != "v1":
            self._report_s04()
        self.pill_cache = {}
        self.strip = Strip()
        tilt = [abs(self.v("s01_lights_world", "tilt_deg", f) or 0.0) for f in range(S01_TILT_FROM, 241)]
        self.tilt_amp = rnd(max(tilt)) if tilt else 4
        self.chip_tl = {pid: self._chip_timeline(pid) for pid in CHIPS}

    def v(self, shot, key, f):
        sv = self.vals.get(shot)
        return sv.get(key, f) if sv else None

    def _report_s04(self):
        """v2: say where the zoom chip comes from and what it will read (start -> end of its window)."""
        sv = self.vals.get(S04_ID)
        c = CHIPS["s04"]
        if sv is None:
            self.log.append(f"meta {S04_ID}: shot not in the table; chip uses the fallback curve")
            return
        have = any(isinstance(r.get(k), (int, float)) for r in sv.table.values() for k in ALIASES["zoom"])
        if not have:
            self.log.append(f"meta {S04_ID}: no per-frame zoom yet -> FALLBACK curve zoom = "
                            f"{S04V2_ZOOM_END:g} ** ease_in_out_sine(local f{S04V2_PUSH[0]}-{S04V2_PUSH[1]}) "
                            "(replace by rendering/building shots/s04_subject.py, then rerun)")
        z0 = sv.get("zoom", c["start"]) or 1.0
        z1 = max((sv.get("zoom", f) or 1.0) for f in range(c["start"], c["end"]))
        ze = sv.get("zoom", c["end"] - 1) or 1.0
        sv.used.clear()
        self.log.append(f"chip {S04_ID}: f{c['start']} ×{z0:.1f} -> f{c['end'] - 1} ×{ze:.1f} (peak ×{z1:.2f})"
                        + ("" if 5.0 <= ze <= 9.5 else "  WARNING: storyboard_v2 expects an end zoom of about ×7"))

    # ---- chip content ------------------------------------------------------------------------------------------
    def chip_content(self, pid, f):
        kind = CHIPS[pid]["kind"]
        if kind == "dots":
            if f < S01_DOT_SPLIT:
                return ("dots", (("white", 0, None),)), 1
            return ("dots", (("coral", 0, 0), ("lime", 1, 2), ("blue", 2, 4))), 3
        if kind == "theta":
            th = self.v("s01_lights_world", "theta_deg", f) or 0.0
            segs = [("θ ", 1.0), (f"{rnd(th)}°", 1.0)]
            if f >= S01_TILT_FROM:
                segs += [(" · ", SEP_ALPHA), ("tilt ", WORD_ALPHA), (f"±{self.tilt_amp}°", 1.0)]
            return ("text", tuple(segs)), None
        if kind == "rate":
            if S03_SLOW[0] <= f <= S03_SLOW[1]:
                r = self.v("s03_gummy", "rate", S03_SLOW[0]) or 0.2
                return ("text", ((f"{r:g}×", 1.0), (" · ", SEP_ALPHA), ("frame ", WORD_ALPHA), (f"{f}", 1.0))), None
            return ("text", (("1×", 1.0),)), None
        if kind == "zoom":
            if S04_TEXEL_FROM is not None and f >= S04_TEXEL_FROM:
                return ("text", (("≈1", 1.0), (" texel / px", WORD_ALPHA))), None
            z = self.v(S04_ID, "zoom", f) or 1.0
            zs = f"{z:.1f}" if z < 9.95 else f"{rnd(z)}"
            return ("text", ((f"×{zs}", 1.0),)), None
        raise ValueError(kind)

    def content_width(self, content, nslots):
        kind, data = content
        if kind == "dots":
            return S * (2 * CHIP_DOT_PAD + nslots * CHIP_DOT_PX + (nslots - 1) * CHIP_DOT_GAP)
        _, w = layout(data, self.chip_font, tabular=True)
        return rnd(2 * CHIP_PAD * S + w)

    def _chip_timeline(self, pid):
        """frame -> (content, animated body width). Widths spring from wherever they are to each new target."""
        c = CHIPS[pid]
        tl, cur_target, sp = {}, None, None
        for f in range(c["start"], c["end"] + 1):
            content, nslots = self.chip_content(pid, f)
            target = max(self.content_width(content, nslots), CHIP_H * S)
            if cur_target is None:
                cur_target, w = target, float(target)
            elif target != cur_target:
                w_prev = tl[f - 1][1]
                sp = (f, w_prev, target)
                cur_target = target
            if sp is not None:                    # grow: POP overshoot; shrink: ease out, never below the content
                k = f - sp[0] + 1
                ease = ease_out_back if sp[2] > sp[1] else ease_out_cubic
                w = sp[2] if k >= WIDTH_N else sp[1] + (sp[2] - sp[1]) * ease(k / WIDTH_N)
            tl[f] = (content, w)
        return tl

    # ---- builders ------------------------------------------------------------------------------------------------
    def pill(self, P):
        if P["id"] in self.pill_cache:
            return self.pill_cache[P["id"]]
        fnt = self.label_font
        items, tw = layout(split_label(P["text"]), fnt, tabular=False)
        bw = rnd(S * (DOT_INSET + DOT_PX + LABEL_GAP + PILL_PAD_R) + tw)
        img, anchor, box = self.sprites.capsule("pill", bw)
        img = img.copy()
        x0, yc = anchor
        dimg, dc, dd = self.sprites.dot(P["dot"])
        place_into(img, dimg, dc, (x0 + S * (DOT_INSET + DOT_PX / 2), yc), S * DOT_PX / dd)
        m, pad, base = text_mask(items, tw, fnt)
        tx = rnd(x0 + S * (DOT_INSET + DOT_PX + LABEL_GAP)) - pad
        ty = rnd(yc + fnt.cap / 2.0) - base
        over_into(img, solid(m, INK), tx, ty)
        self.pill_cache[P["id"]] = (img, anchor, bw)
        return self.pill_cache[P["id"]]

    def chip(self, pid, f):
        content, width = self.chip_tl[pid][f]
        img, anchor, box = self.sprites.capsule("chip", rnd(width))
        img = img.copy()
        x0, yc = anchor
        bx0, by0, bx1, by1 = box
        inset = 3 * S
        clip = rrect_mask(img.shape[0], img.shape[1], bx0 + inset, by0 + inset, bx1 - bx0 - 2 * inset,
                          by1 - by0 - 2 * inset, (by1 - by0 - 2 * inset) / 2.0)
        xs = np.arange(img.shape[1], dtype=np.float32) + 0.5
        clip *= np.clip((bx1 - inset - xs) / (12.0 * S), 0, 1)[None, :]       # soft reveal while growing
        kind, data = content
        layer = np.zeros_like(img)
        if kind == "text":
            items, tw = layout(data, self.chip_font, tabular=True)
            m, pad, base = text_mask(items, tw, self.chip_font)
            tx = rnd(x0 + S * CHIP_PAD) - pad
            ty = rnd(yc + self.chip_font.cap / 2.0) - base
            over_into(layer, solid(m, INK), tx, ty)
        else:
            dot_px = S * CHIP_DOT_PX
            slot_x = lambda i: x0 + S * (CHIP_DOT_PAD + CHIP_DOT_PX / 2 + i * (CHIP_DOT_PX + CHIP_DOT_GAP))
            if S01_DOT_SPLIT <= f < S01_DOT_SPLIT + 3:            # the white dot shrinks under the coral pop
                wsc = 1.0 - ease_in_cubic((f - S01_DOT_SPLIT + 1) / 3.0)
                dimg, dc, dd = self.sprites.dot("white")
                place_into(layer, dimg, dc, (slot_x(0), yc), wsc * dot_px / dd)
            for colour, slot, delay in data:
                sc = 1.0 if delay is None else pop_in(f - (S01_DOT_SPLIT + delay) + 1)
                if sc > 0:
                    dimg, dc, dd = self.sprites.dot(colour)
                    place_into(layer, dimg, dc, (slot_x(slot), yc), sc * dot_px / dd)
        layer *= clip[..., None]
        over_into(img, layer, 0, 0)
        return img, anchor

    # ---- frame ---------------------------------------------------------------------------------------------------
    def frame(self, f):
        cv = Canvas()
        py = (FH - MARGIN - PILL_H / 2.0) * S
        for P in PILLS:
            g = presence(f, P["start"], P["end"])
            if g <= 0:
                continue
            img, anchor, bw = self.pill(P)
            cv.place(img, anchor, (MARGIN * S, py), g)
            c = CHIPS.get(P["id"])
            if c and c["start"] <= f < c["end"]:
                own = pop_in(f - c["start"] + 1)
                if c["end"] < P["end"]:
                    own *= pop_out(f, c["end"])
                if own > 0:
                    cimg, canchor = self.chip(P["id"], f)
                    cv.place(cimg, canchor, (MARGIN * S + g * (bw + CHIP_GAP * S), py), g * own)
        sg = presence(f, STRIP["start"], STRIP["end"])
        if sg > 0:
            th = self.v("s01_lights_world", "theta_deg", f) or 0.0
            ph = self.v("s01_lights_world", "tilt_deg", f) or 0.0
            simg, sanchor = self.strip.element(th, ph)
            cv.place(simg, sanchor, ((FW - MARGIN) * S, MARGIN * S), sg)
        if self.slug:
            self.draw_slug(cv, f)
        return cv

    def draw_slug(self, cv, f):
        fnt = self.slug_font
        segs = [("Illustrative", 1.0), (" · ", 1.0), ("rendered with Cycles", 1.0)]
        items, tw = layout(segs, fnt, tabular=False)
        m, pad, base = text_mask(items, tw, fnt)
        k = smoothstep(prog(f, 106, 121))                     # S01 night phase: white, then ink
        colour = (1 - k) * hex_rgb("white") + k * hex_rgb(INK)
        x = rnd((FW - MARGIN) * S - tw) - pad
        y = rnd((FH - MARGIN) * S - fnt.desc) - base
        cv.over(solid(m, colour, 0.6), x, y)


class Strip:
    """Top-right lat-long strip: candy_sky_preview.png seen from the camera (centre = azimuth 90 deg, azimuth
    increasing to the left, zenith on top), re-projected each frame with the world mapping R = Rz(-θ)·Ry(-φ)."""

    def __init__(self):
        # S01 round 2: the tilt axis comes from renders/meta/s01_lights_world.json ("tilt_axis": "x" since the glide
        # ends at theta=315 with the sun behind the island); default "y" (storyboard) if the key or file is missing.
        self.tilt_axis = "y"
        try:
            with open(os.path.join(META_DIR, "s01_lights_world.json")) as fh:
                self.tilt_axis = str(json.load(fh).get("tilt_axis", "y")).lower()
        except (OSError, ValueError):
            pass
        src = cv2.imread(SKY_PREVIEW, cv2.IMREAD_COLOR)
        if src is None:
            src = np.full((1024, 2048, 3), (255, 233, 205), np.uint8)
        src = cv2.cvtColor(src, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        self.src = cv2.resize(src, (1536, 768), interpolation=cv2.INTER_AREA)
        self.w, self.h = STRIP_W * S, STRIP_H * S
        j = (np.arange(self.w) + 0.5) / self.w
        i = (np.arange(self.h) + 0.5) / self.h
        az = math.radians(90.0) + (0.5 - j) * 2 * math.pi
        el = (0.5 - i) * math.pi
        AZ, EL = np.meshgrid(az, el)
        self.dirs = np.stack([np.cos(EL) * np.cos(AZ), np.cos(EL) * np.sin(AZ), np.sin(EL)], -1).reshape(-1, 3)
        b, r = STRIP_BORDER * S, STRIP_R * S
        self.pad = 40 * S
        self.ow, self.oh = self.w + 2 * b, self.h + 2 * b
        E_w, E_h = self.ow + 2 * self.pad, self.oh + 2 * self.pad
        p = self.pad
        outer = rrect_mask(E_h, E_w, p, p, self.ow, self.oh, r + b)
        self.inner = rrect_mask(E_h, E_w, p + b, p + b, self.w, self.h, r)
        shadow = blur(np.roll(outer, 5 * S, axis=0), 7 * S) * 0.30
        ys = (np.arange(E_h, dtype=np.float32) - p) / self.oh
        grad = np.clip(1.0 - 0.07 * smoothstep_np(ys), 0, 1)[:, None, None] * np.array([1.0, 0.995, 1.0], np.float32)
        frame_rgb = np.broadcast_to(grad, (E_h, E_w, 3))
        ring = np.clip(outer - self.inner, 0, 1)
        base = np.zeros((E_h, E_w, 4), np.float32)
        base[..., 3] = shadow * (1 - outer)
        base[..., :3] = (base[..., 3:4] * hex_rgb(INK))
        frame_layer = np.concatenate([frame_rgb * ring[..., None], ring[..., None]], -1).astype(np.float32)
        self.base = base
        self.frame_layer = frame_layer
        # inset shade along the image's top edge + hairline, so the white frame separates from the pale sky
        inset = np.clip(1.0 - (ys[:, None] * self.oh - b) / (5 * S), 0, 1) ** 2 * 0.22
        hair = np.clip(self.inner - rrect_mask(E_h, E_w, p + b + S, p + b + S, self.w - 2 * S, self.h - 2 * S,
                                                 r - S), 0, 1) * 0.10
        self.inset = solid(np.clip(np.broadcast_to(inset, (E_h, E_w)) * self.inner + hair, 0, 1), INK)
        # mint playhead: rounded triangle pointing down, white keyline + soft shadow, fixed at the centre
        cx = p + self.ow / 2.0
        tri = tri_mask(E_h, E_w, cx, p - 3 * S, 11 * S, 15 * S, 2.5 * S)
        tri_out = tri_mask(E_h, E_w, cx, p - 3 * S, 11 * S, 15 * S, 2.5 * S, grow=2.5 * S)
        line = np.zeros((E_h, E_w), np.float32)
        lx0, lx1 = int(cx - 1 * S), int(cx + 1 * S)
        line[p + b:p + b + self.h, lx0:lx1] = 0.30
        line *= self.inner
        ph = solid(blur(np.roll(tri_out, S, axis=0), 2 * S) * 0.25, INK)
        over_into(ph, solid(tri_out, "white"), 0, 0)
        over_into(ph, solid(tri, "mint"), 0, 0)
        self.line = solid(line, "mint")
        self.playhead = ph
        self.anchor = (p + self.ow, float(p))                 # top-right corner of the white frame

    def sky(self, theta_deg, phi_deg):
        t, ph = math.radians(theta_deg), math.radians(phi_deg)
        Rz = np.array([[math.cos(-t), -math.sin(-t), 0], [math.sin(-t), math.cos(-t), 0], [0, 0, 1]])
        if self.tilt_axis == "x":            # R = Rz(-θ)·Rx(-φ)
            Ry = np.array([[1, 0, 0], [0, math.cos(-ph), -math.sin(-ph)], [0, math.sin(-ph), math.cos(-ph)]])
        else:                                 # R = Rz(-θ)·Ry(-φ)
            Ry = np.array([[math.cos(-ph), 0, math.sin(-ph)], [0, 1, 0], [-math.sin(-ph), 0, math.cos(-ph)]])
        d = self.dirs @ (Rz @ Ry).T
        az = np.arctan2(d[:, 1], d[:, 0])
        el = np.arcsin(np.clip(d[:, 2], -1, 1))
        Hs, Ws = self.src.shape[:2]
        mx = (((math.pi - az) / (2 * math.pi)) % 1.0) * Ws - 0.5
        my = np.clip((0.5 - el / math.pi) * Hs - 0.5, 0, Hs - 1)
        return cv2.remap(self.src, mx.reshape(self.h, self.w).astype(np.float32),
                         my.reshape(self.h, self.w).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

    def element(self, theta_deg, phi_deg):
        img = self.base.copy()
        sky = np.zeros_like(img)
        p, b = self.pad, STRIP_BORDER * S
        sky[p + b:p + b + self.h, p + b:p + b + self.w, :3] = self.sky(theta_deg, phi_deg)
        sky[..., 3] = 1.0
        sky *= self.inner[..., None]
        over_into(img, sky, 0, 0)
        over_into(img, self.inset, 0, 0)
        over_into(img, self.line, 0, 0)
        over_into(img, self.frame_layer, 0, 0)
        over_into(img, self.playhead, 0, 0)
        return img, self.anchor


def tri_mask(h, w, cx, top, half_w, height, radius, grow=0.0):
    """Down-pointing isosceles triangle (base on y=`top`, apex `height` below) with corners rounded by `radius`:
    the exact SDF of the triangle shrunk about its incentre by `radius`, minus `radius` (+ `grow`)."""
    A, B, C = np.array([cx - half_w, top]), np.array([cx + half_w, top]), np.array([cx, top + height])
    la, lb, lc = np.linalg.norm(B - C), np.linalg.norm(C - A), np.linalg.norm(A - B)
    inc = (la * A + lb * B + lc * C) / (la + lb + lc)
    area = abs((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1])) / 2.0
    rho = area / ((la + lb + lc) / 2.0)
    k = max(rho - radius, 1e-3) / rho
    pts = [inc + (P - inc) * k for P in (A, B, C)]
    ys = np.arange(h, dtype=np.float32)[:, None] + 0.5
    xs = np.arange(w, dtype=np.float32)[None, :] + 0.5
    dist = np.full((h, w), np.inf, np.float32)
    signs = []
    for i in range(3):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 3]
        ex, ey = x1 - x0, y1 - y0
        wx, wy = xs - x0, ys - y0
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        dist = np.minimum(dist, np.hypot(wx - ex * t, wy - ey * t))
        signs.append(ex * wy - ey * wx >= 0)
    inside = (signs[0] & signs[1] & signs[2]) | (~signs[0] & ~signs[1] & ~signs[2])
    sd = np.where(inside, -dist, dist) - radius - grow
    return np.clip(0.5 - sd, 0.0, 1.0).astype(np.float32)


# =================================================================================================================
# checks
def selftest(ov):
    errs = []
    # 1) cut safety: nothing on the two frames before each cut
    cuts = sorted(int(s["end_frame_in_film"]) for s in ov.shots.values())[:-1]
    for cut in cuts:
        for f in (cut - 1, cut):
            for P in PILLS:
                if presence(f, P["start"], P["end"]) > 0:
                    errs.append(f"pill {P['id']} visible on f{f} (cut {cut}|{cut + 1})")
            if presence(f, STRIP["start"], STRIP["end"]) > 0:
                errs.append(f"strip visible on f{f}")
    # 2) storyboard checkpoints of the fallback formulas
    for name, got, want in (("θ(150)", s01_theta(150), 90.0), ("θ(195)", s01_theta(195), 360.0),
                            ("θ(225)", s01_theta(225), 405.0), ("τ(31)", s03_tau(31), 0.92),
                            ("τ(85)", s03_tau(85), 1.28), ("τ(91)", s03_tau(91), 1.40),
                            ("zoom(105)", s04_zoom(105), 46.15)):
        if abs(got - want) > 0.01:
            errs.append(f"formula {name} = {got:.4f}, want {want}")
    # 3) no jitter: digit glyphs keep their x for every value of the same digit count
    fnt = ov.chip_font
    for n in (1, 2, 3):
        ref = None
        for v in (["0", "5", "9"] if n == 1 else ["10", "47", "99"] if n == 2 else ["100", "405", "888"]):
            items, w = layout([("θ ", 1.0), (v + "°", 1.0)], fnt, tabular=True)
            xs = [round(x, 4) for x, ch, _ in items if not ch.isdigit()] + [round(w, 4)]
            cells = [round(x + fnt.adv(ch) / 2, 4) for x, ch, _ in items if ch.isdigit()]
            sig = (tuple(xs), tuple(cells))
            if ref is None:
                ref = sig
            elif sig != ref:
                errs.append(f"digit layout moves with the value ({n} digits)")
    # 4) captions name capabilities only
    for P in PILLS:
        if any(ch.isdigit() for ch in P["text"]):
            errs.append(f"caption with a number: {P['text']}")
    if FILM != "v1":
        errs += selftest_v2(ov)
    return errs


def selftest_v2(ov):
    """storyboard_v2 section 6: S01-S03 windows identical to v1, the S04 window, a clean finale, the fallback."""
    errs = []
    v1p = {P["id"]: P for P in FILMS["v1"]["pills"]}
    for P in PILLS:
        if P["id"] != "s04" and P != v1p.get(P["id"]):
            errs.append(f"pill {P['id']} differs from v1")
    for k, c in CHIPS.items():
        if k != "s04" and c != FILMS["v1"]["chips"].get(k):
            errs.append(f"chip {k} differs from v1")
    s04 = next(P for P in PILLS if P["id"] == "s04")
    if (s04["start"], s04["end"]) != (616, 776) or S04_TEXEL_FROM is not None:
        errs.append("S04 v2 window must be 616 -> out by 776, without the texel chip")
    ends = sorted(int(s["end_frame_in_film"]) for s in ov.shots.values())
    fin0, fin1 = ends[-2] + 1, ends[-1]
    if (fin0, fin1, N_FILM) != (781, 960, 960):
        errs.append(f"v2 table: finale {fin0}-{fin1}, film {N_FILM} (want 781-960, 960)")
    for f in list(range(fin0 - 4, fin0)) + list(range(fin0, fin1 + 1)):      # 777-780 clean, finale empty
        if any(presence(f, P["start"], P["end"]) > 0 for P in PILLS) or presence(f, STRIP["start"], STRIP["end"]) > 0:
            errs.append(f"overlay element visible on f{f} (S04 out by 776, nothing in the finale)")
            break
    for name, got, want in (("zoom_v2(31)", s04v2_zoom(31), 1.0), ("zoom_v2(145)", s04v2_zoom(145), 7.0),
                            ("zoom_v2(180)", s04v2_zoom(180), 7.0)):
        if abs(got - want) > 0.01:
            errs.append(f"fallback {name} = {got:.4f}, want {want}")
    return errs


# =================================================================================================================
# driver
OV = None


def _init(slug, fallback, film=None):
    global OV
    if film is not None and film != FILM:
        configure(film)
        OV = None
    if OV is None:
        OV = Overlay(slug=slug, fallback_sprites=fallback)


def _render(args):
    f, out_dir, slug, fallback = args[:4]
    _init(slug, fallback, args[4] if len(args) > 4 else None)
    rgba = OV.frame(f).to_rgba8()
    path = os.path.join(out_dir, f"o_{f:04d}.png")
    tmp = path + ".tmp.png"
    cv2.imwrite(tmp, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_PNG_COMPRESSION, 3])
    os.replace(tmp, path)
    return f, int(rgba[..., 3].max())


def parse_frames(spec, lo=1, hi=None):
    hi = N_FILM if hi is None else hi           # the selected film's length (900 v1, 960 v2)
    if not spec:
        return list(range(lo, hi + 1))
    step = 1
    if ":" in spec:
        spec, s = spec.split(":")
        step = int(s)
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1, step))
        elif part:
            out.append(int(part))
    return sorted(set(f for f in out if lo <= f <= hi))


def film_source(shots, f, prefer=("final", "preview")):
    """(path, mode, shot id, local frame) of the rendered film frame, or (None, None, id, local)."""
    for s in shots:
        a, n = int(s["start_frame_in_film"]), int(s["frames"])
        if a <= f < a + n:
            fl = f - a + 1
            for mode in prefer:
                p = os.path.join(ROOT, "renders", mode, s["id"], f"f_{fl:04d}.png")
                if os.path.exists(p):
                    return p, mode, s["id"], fl
            return None, None, s["id"], fl
    return None, None, None, None


def read_frame_rgb(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    sc = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32) / sc
    if im.ndim == 2:
        im = np.repeat(im[..., None], 3, -1)
    im = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB)
    if im.shape[:2] != (FH, FW):
        im = cv2.resize(im, (FW, FH), interpolation=cv2.INTER_LANCZOS4)
    return np.clip(im, 0, 1)


def make_sheet(path, frames, out_dir, bg_mode):
    shots = load_shots()
    font = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Poppins-Bold.ttf"), 22)
    small = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Poppins-SemiBold.ttf"), 18)
    comps, labels = [], []
    for f in frames:
        ov = cv2.imread(os.path.join(out_dir, f"o_{f:04d}.png"), cv2.IMREAD_UNCHANGED)
        ov = cv2.cvtColor(ov, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255.0
        bg, src = None, "grey"
        if bg_mode != "grey":
            p, mode, sid, fl = film_source(shots, f, ("final", "preview") if bg_mode == "auto" else (bg_mode,))
            if p:
                bg = read_frame_rgb(p)
                src = f"{mode} {sid} f{fl}" if bg is not None else "grey"
        if bg is None:
            bg = np.full((FH, FW, 3), 128 / 255.0, np.float32)
        a = ov[..., 3:4]
        comps.append(bg * (1 - a) + ov[..., :3] * a)
        labels.append(f"f{f}  ({src})")
    cols, tw = 4, 480
    th = tw * FH // FW
    rows = (len(frames) + cols - 1) // cols
    crop_w, crop_h, crop_y = 960, 150, 885
    crops_per_row = 2
    crop_rows = (len(frames) + crops_per_row - 1) // crops_per_row
    strip_frames = [i for i, f in enumerate(frames) if STRIP["start"] <= f < STRIP["end"]]
    sc_w, sc_h = 480, 300
    head = 40
    Hs = head + rows * th + head + crop_rows * crop_h + (head + sc_h if strip_frames else 0)
    sheet = Image.new("RGB", (cols * tw, Hs), (36, 34, 52))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "overlays over film frames (grey where no render exists): thumbnails at 1/4", font=font,
           fill=(255, 255, 255))
    for i, (img, lab) in enumerate(zip(comps, labels)):
        x, y = (i % cols) * tw, head + (i // cols) * th
        t = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        sheet.paste(Image.fromarray((t * 255 + 0.5).astype(np.uint8)), (x, y))
        d.rectangle([x, y, x + 9 * len(lab) + 10, y + 24], fill=(0, 0, 0))
        d.text((x + 5, y + 1), lab, font=small, fill=(255, 255, 255))
    y_c = head + rows * th
    d.text((10, y_c + 8), "1:1 crops, lower-left (x 40-1000, y 885-1035)", font=font, fill=(255, 255, 255))
    y_c += head
    for i, (img, f) in enumerate(zip(comps, frames)):
        x, y = (i % crops_per_row) * crop_w, y_c + (i // crops_per_row) * crop_h
        c = img[crop_y:crop_y + crop_h, 40:40 + crop_w]
        sheet.paste(Image.fromarray((c * 255 + 0.5).astype(np.uint8)), (x, y))
        d.text((x + 6, y + 4), f"f{f}", font=small, fill=(255, 255, 255))
    if strip_frames:
        y_s = y_c + crop_rows * crop_h
        d.text((10, y_s + 8), "1:1 crops, lat-long strip (top-right)", font=font, fill=(255, 255, 255))
        y_s += head
        for k, i in enumerate(strip_frames[:4]):
            c = comps[i][20:20 + sc_h, FW - 40 - sc_w:FW - 40]
            sheet.paste(Image.fromarray((c * 255 + 0.5).astype(np.uint8)), (k * sc_w, y_s))
            d.text((k * sc_w + 6, y_s + 4), f"f{frames[i]}", font=small, fill=(255, 255, 255))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sheet.save(path)
    return sheet.size


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--film", choices=sorted(FILMS), default="v1",
                    help="v1 (default; docs/shots.json, renders/overlays, 900 f) or v2 (docs/shots_v2.json, "
                         "renders/overlays_v2, 960 f)")
    ap.add_argument("--frames", default=None, help="'1-900', '121-238,451', '1-900:10'. Default: the whole film")
    ap.add_argument("--out", default=None, help="default renders/overlays (v1) or renders/overlays_v2 (v2)")
    ap.add_argument("--slug", action="store_true", help='add "Illustrative · rendered with Cycles" (lower right)')
    ap.add_argument("--jobs", type=int, default=min(24, os.cpu_count() or 4))
    ap.add_argument("--fallback-sprites", action="store_true", help="ignore assets/ui (test the Pillow fallback)")
    ap.add_argument("--sheet", default=None, help="also write a review sheet (e.g. renders/review/overlays_sheet.png)")
    ap.add_argument("--sheet-frames", default=None, help="default: the film's review frames")
    ap.add_argument("--sheet-bg", default="auto", choices=["auto", "grey", "final", "preview"])
    a = ap.parse_args()
    configure(a.film)
    a.out = a.out or OUT_DIR
    a.sheet_frames = a.sheet_frames or ",".join(map(str, SHEET_FRAMES))
    if a.film != "v1" and os.path.realpath(a.out) == os.path.realpath(FILMS["v1"]["out"]):
        sys.exit("[overlays] refusing to write v2 overlays into the v1 folder renders/overlays")

    t0 = time.time()
    _init(a.slug, a.fallback_sprites)
    for line in OV.log:
        print("[overlays]", line)
    errs = selftest(OV)
    if errs:
        for e in errs:
            print("[overlays] SELFTEST FAIL:", e, file=sys.stderr)
        sys.exit(2)
    print(f"[overlays] selftest ok (cut safety, formulas, fixed digit cells"
          f"{'; v2 windows, clean finale' if FILM != 'v1' else ''}); tilt chip = ±{OV.tilt_amp}°")
    frames = parse_frames(a.frames)
    sheet_frames = parse_frames(a.sheet_frames) if a.sheet else []
    todo = sorted(set(frames) | set(sheet_frames))
    os.makedirs(a.out, exist_ok=True)
    jobs = [(f, a.out, a.slug, a.fallback_sprites) + ((FILM,) if FILM != "v1" else ()) for f in todo]
    vis = 0
    if a.jobs > 1 and len(jobs) > 8:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(a.jobs) as pool:
            for f, amax in pool.imap_unordered(_render, jobs, chunksize=4):
                vis += amax > 0
    else:
        for j in jobs:
            vis += _render(j)[1] > 0
    for key, sv in OV.vals.items():
        if sv.used:
            print(f"[overlays] values {key}: " + ", ".join(f"{k} from {v}" for k, v in sorted(sv.used.items())))
    print(f"[overlays] wrote {len(jobs)} frames ({vis} with content) to {os.path.relpath(a.out, ROOT)} "
          f"in {time.time() - t0:.1f}s")
    if a.sheet:
        size = make_sheet(a.sheet, sheet_frames, a.out, a.sheet_bg)
        print(f"[overlays] sheet {a.sheet} {size}")


if __name__ == "__main__":
    main()
