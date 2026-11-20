"""S05 . s05_title: "LaRenderer" (title + recap). Film frames 781-900, bars 14-15, 120 frames, GPU 6.

What the shot proves / recaps (storyboard section 4, S05)
* The opening's point-light test resolves: the white orb from S04's painted dot splits into three palette lights
  (coral / lime / blue at 0.49 / 1.05 / 0.94 of W: neutral sum). They hang just BEHIND the word, so every letter throws
  three coloured shadows toward the camera across the glossy cove floor (aqua / violet / yellow where one light is
  blocked, a dark core where all three are). At f61 the three lights fuse back into one white key (co-located, same
  total power, electrical swap at f71) and the fans collapse into one crisp shadow per letter: superposition.
* Ten hue-ordered candy letters land on 16th notes (f16..50) with a volume-preserving BOING squash (C3 recap).
* The honeycomb replays S01-S04 on its four middle tiles via D.mat_video (renders/proxies, see
  scripts/make_tile_proxies.py): the teaser mosaic come alive.
* f1 matches S04 f180: a glowing orb ORB_PX wide, centred, same Emit-pass bloom; then a pull-back reveals the cove.

Fixed (kept exactly): 120 f; hits f1 orb, f8 split, letters land at 16+round(3.75 i) = 16,20,24,27,31,35,39,42,46,50,
f61 fuse, f71 light swap, f71-120 hold; ORB_PX circle match; PBR Neutral, exposure -0.2; 1920x1080 / 30 fps; static
seed; every animation baked per frame with D.bake from closed-form functions of the frame.

ROUND 2 CHANGELOG (lead notes r2 + critic r1; what changed and why)
 R1. Back key restage (critic critical #2, lead S05.2 "make the superposition read"). The four story lights are SPOT
     r 0.04 (cone 100 deg, blend 0.4) in a row 1.6 m BEHIND the word at O = (0, 2.0, 0.92), coral/blue at x -+0.9
     (z -0.04), lime z +0.10, aimed down-forward at (0,-0.6,0). Each letter now throws its three coloured shadows toward
     the camera as long streaks across the foreground floor (r1: the key sat 1 m in front of the word, every letter hid
     its own shadow and only 14-20 px slivers showed). Tried y 1.4 / z 1.05 (critic's family): fans only ~40 px tall;
     y 2.0 / z 0.92 doubles their length and the key's falloff along the floor is gentler. The cone misses the band.
     Neutral split 0.49/1.05/0.94 x W (W 260 -> 560 W: the key now lights only the floor pool), co-located swap at
     f71: unchanged. Key lights are glossy-invisible (no specular hot pool in the glossy floor); the halos still
     reflect in it.
 R2. Letter light, separated from the floor light (critic majors: focal point, overexposed pastel letters):
     * FaceKey: white 5.0 x 1.2 m AREA (140 W) in front, light-linked to the letters only (GlossReceivers) and
       diffuse-only, so the faces keep their palette colours in both phases, evenly across the 5 m word.
     * Fill lavender 110 W -> white 160 W, and light-linked to EXCLUDE the cove: it lights letters and band only.
     * WallWash (new): white 10 x 1.2 m AREA (200 W) above the frame aimed at the wall, so the backdrop reads pastel
       lavender (G2) while the floor gets only key pool + spill and falls off toward the bottom edge (lead S05.1).
     * Cove one value step darker (lavender + 20% lilac, mixed in linear light) with a soft clear coat (0.5, rough
       0.22, lead S05.1): the letters and orbs reflect softly in the floor.
     Tested 12 balances (renders/work/s05_title/v_*): a stronger wash killed the fans, no wash read dusky/grey;
     key 360 -> 560 W with wash 260 -> 200 W took the floor-strip share of S>0.3 pixels at f52 from 11% to 18%.
 R3. Lockup (lead S05.1): word 4.4 -> 5.0 m, deeper pillow (front relief LET_H 0.115 over the same LET_R 0.075
     footprint: an elliptical profile, zero slope at the crest, so no ridge). Camera end (0,-9,1.9) -> (0,-9,2.15)
     looking at (0,0.4,0.57): more floor for the fans. Result f120: title 73.8% wide, baseline 64.9%, band 57 px from
     the top, orb row 33.8-37.2% (W 36.2%).
 R4. Honeycomb calmer and inside the frame (lead S05.1, critic minor): 10 tiles (was 12; 3 solid per side, the outer
     pair cropped by the frame edges), circumradius 0.46, pitch 0.88, flatter zig-zag +-0.115 so neighbouring hex
     edges stay parallel with an 8 cm grout, BAND_Z 1.77. Solid tiles softened 40% toward the wall colour, semi-matte,
     with tinted rims instead of cream (softer contrast); with no key on the band its shadows are soft.
 R5. Screens (critic major): TILE_EMIT 0.45 -> 0.30, screen specular 0.5 -> 0.15, roughness 0.35 -> 0.2,
     coat 0.6 -> 0.1, so the cove no longer veils the picture (r1 screens/letters 0.67-0.71 display luma vs the
     0.60 gate; now 0.45-0.50).
 R6. G1 glow: S01's compositor bloom copied with identical parameters (Glare BLOOM HIGH, threshold 0.6, smoothness
     0.2, strength 1.0, size 0.45, saturation 1.0, driven by the Emit pass only, added to the image); the 0.30 screens
     stay under the threshold. The f1 core emission = S04's r2 f180 orb (4.0 x (0.7 + 0.3 (1 - Facing)), disc mean
     3.2) x 2^(-0.1 - -0.2) for the exposure difference = 3.43, so core AND glow match across the cut; it eases to
     S01's white-orb emission 4.0 by f8. Halo r 0.085 -> 0.10 (the orbs are now ~11 m from the camera). The critic's
     extra glow-shell sphere is not used: G1 asks for the same glow everywhere.
 R7. Split (critic major): S-curve that leaves O at zero speed (ease_out_back(smootherstep), f8-20, peak ~0.24 m/f
     instead of a 0.72 m jump), motion-blur shutter 0.5 -> 1.0 over f8-11 and back by f18 (as the whip does), W's halo
     shrinks over f8-12 so the colours visibly peel out of it.
 R8. Fuse on the downbeat (critic major): convergence f53 -> 61 (same ease_in_out_cubic), so lights, halos and the
     shadow fans close exactly on f61; coloured halos shrink to 0.5 as they meet (f55-61) and are gone by f64; W's halo
     POPs from inside (POP spring from f57: 0.34 f58, 0.71 f59, 1.0 f60, +23% peak f62) so the meeting reads as the
     colours merging into white (the tri-colour stack shows for ~1 frame at f58-59, small); letters' unison pulse
     3% -> 7% starting f61.
 R9. Pull-back eases in (critic minor): a 4-frame speed ramp (f1-5) on the log-distance clock instead of the
     critic's p^1.35 (that kept the camera so close that the L landed off-frame on f16 with the 5 m word).
R10. Hold accents (critic minor): a glossy-only vertical Shine strip (letters only) sweeps the word f84-98, crossing the
     centre on the f91 beat; W's halo breathes +4% on f76 and f106 with a +-1 cm bob (light and halo together).
R11. Real tiles (lead S05.4, critic critical #1): the S01 tile now plays S01 f121-240 (stable daylight with the env-map
     clicks; f1-120 opened pitch black and flashed 6x brighter in the film's last 12 frames). Set in
     scripts/make_tile_proxies.py, which now also writes renders/proxies/<id>/SOURCE.json. This script reads the
     manifest, prints the tile sources, warns on placeholders and REFUSES to write renders/final/s05_title unless all
     four tiles come from finals (S05_ALLOW_NONFINAL_PROXIES=1 overrides).
R12. Cost (lead G4, cap 0.4 GPU-h): final adaptive threshold 0.01 -> 0.02 at 384 spp. A/B at f50/f120: mean |d|
     0.2-0.4/255, floor high-pass noise 0.131 -> 0.138 and 0.183 -> 0.191 (/255), static seed so static regions
     stay identical; about 20% fewer samples (11-12.7 vs 12-15 s/f on a shared GPU 6). Unshared: ~9.1 s/f, so
     ~0.31 GPU-h for the 120 frames.

Deviations from the storyboard kept from round 1 (tunables; numbers are what the script uses):
 1. Letters are inflated Fredoka Bold outlines (oriented Bezier contours, nonzero winding), not text3d+bevel (bevel 0.07
    made neighbours interpenetrate and collapsed the 'a' counter). One object per letter, origin at its base centre.
 2. Shape-aware letter spacing: constant 8 cm clearance between outlines, then the word is scaled to TITLE_W.
 3. Rounded-corner hex bodies and a rounded hex tube rim (curve bevel) instead of 6-gon cylinder + 6-segment torus.
    Screen UVs as specified, scaled with the tile (central 65% of the clip width). Band 12 cm off the wall.
 4. Every letter leans RIGHT on landing (storyboard: alternating); 6% fall stretch before contact.
 5. Glossy-only strip softbox (GlossStrip) light-linked to the letters: the candy highlights.
 6. DOF f/1.4 at f1 -> f/4.0 by f24. Log-distance pull-back with ease_out_back(0.5) over f1-34 (arrival ~f25,
    ~1.5% overshoot, settled ~f34), 1% push f24-120.
 7. Lights: storyboard O = (0,-1.2,1.40) in front of the word, fill lavender 160 W; here the key is behind the word
    (R1), letters / backdrop have their own linked lights (R2), halos r 0.10 (R6).

Debug env vars: S05_CAM=top|side (ortho layout cameras), S05_MASK=1 (flat ID render: letters red, tile screens green,
everything else black, for the luminance QA), S05_NOLETTERS=1, S05_KEY="y,z", S05_DX, S05_W, S05_FACE, S05_FILL,
S05_COAT, S05_WASH, S05_LILAC, S05_CAMZ, S05_TGTZ, S05_BANDZ, S05_FILL_NOCOVE=0, S05_NOGLOW=1,
S05_ALLOW_NONFINAL_PROXIES=1.
"""
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.geometry import delaunay_2d_cdt  # noqa: E402


def env_f(name, default):
    return float(os.environ.get(name, default))


# ----------------------------------------------------------------------------------------------------------
# Tunables
# ----------------------------------------------------------------------------------------------------------
ORB_PX = 468                       # f1 orb diameter in px at 1920 wide (S04 f180 dot-orb)
SHOT, N_FRAMES, START_IN_FILM = "s05_title", 120, 781
EXPOSURE = -0.2

# timeline (local frames)
F_SPLIT = 8
LAND = [16, 20, 24, 27, 31, 35, 39, 42, 46, 50]
F_CONV0, F_FUSE, F_SWAP = 53, 61, 71            # converge f53-61 so the fuse lands ON the bar-15 downbeat
F_BREATH = (76, 106)
F_SHINE = (84, 98)                              # shine sweep crosses the word centre on f91
assert LAND == [16 + int(math.floor(3.75 * i + 0.5)) for i in range(10)]

# lights: back key row 1.6 m behind the word (y 2.0, z 0.92); shadows fan toward the camera across the floor
KEY_Y, KEY_Z = [float(v) for v in os.environ.get("S05_KEY", "2.00,0.92").split(",")]
SPLIT_DX = env_f("S05_DX", 0.90)
O = Vector((0.0, KEY_Y, KEY_Z))
SPLIT = [("coral", (-SPLIT_DX, KEY_Y, KEY_Z - 0.04), 0.49), ("lime", (0.0, KEY_Y, KEY_Z + 0.10), 1.05),
         ("blue", (SPLIT_DX, KEY_Y, KEY_Z - 0.04), 0.94)]
KEY_AIM = Vector((0.0, -0.6, 0.0))
KEY_CONE, KEY_BLEND = 100.0, 0.4
W_POWER = env_f("S05_W", 560.0)
LIGHT_R = 0.04
HALO_R = 0.10
HALO_R_F1 = 0.12
S04_ORB_EMIT, S04_EXPOSURE = 3.2, -0.1          # S04 f180 dot-orb (r2): 4.0 x (0.7 + 0.3 (1 - Facing)), disc mean 3.2
HALO_W_EMIT_F1 = S04_ORB_EMIT * 2.0 ** (S04_EXPOSURE - EXPOSURE)   # same display glow across the cut
HALO_W_EMIT, HALO_C_EMIT = 4.0, 2.0             # S01's white / coloured halo emission
FACE_POWER = env_f("S05_FACE", 140.0)           # white letter-only face key (diffuse only)
FILL_POWER = env_f("S05_FILL", 160.0)              # letters + band only (cove excluded)
WASH_POWER = env_f("S05_WASH", 200.0)             # cyc wash: backdrop reads pastel
GLOSS_POWER = 260.0                             # glossy-only softbox, light-linked to the letters (highlights only)
SHINE_POWER = 900.0                             # glossy-only sweep strip (hold accent)
COVE_COAT = env_f("S05_COAT", 0.5)
GLOW = 0.0 if os.environ.get("S05_NOGLOW") else 1.0

# camera
LENS, SENSOR = 50.0, 36.0
CAM_END = Vector((0.0, -9.0, env_f("S05_CAMZ", 2.15)))
TGT_END = Vector((0.0, 0.40, env_f("S05_TGTZ", 0.57)))
PUSH_Y = 0.08                                  # f24-120 push (1%)

# title
WORD = "LaRenderer"
COLOURS = ["pink", "coral", "orange", "lemon", "lime", "mint", "aqua", "blue", "violet", "#C454C9"]
TITLE_W = 5.0
TITLE_Y = 0.40
LET_R, LET_FLAT, LET_H = 0.075, 0.035, 0.115   # pillow footprint / side half-band / pillow relief (metres)
LET_GAP = 0.08                                 # horizontal clearance between neighbours (metres, final)
LET_ROUGH = 0.2
DROP_Z, DROP_G = 2.8, 14.0
SQUASH, TILT_DEG = 0.30, 6.0
FUSE_PULSE = 0.07

# honeycomb: 10 flat-top hexes, pitch 0.88, zig-zag +-0.115 (parallel neighbouring edges, 8 cm grout)
N_TILES = 10
TILE_DX = 0.88
TILE_X = [(i - (N_TILES - 1) / 2.0) * TILE_DX for i in range(N_TILES)]
BAND_Z, BAND_DZ = env_f("S05_BANDZ", 1.77), 0.115
TILE_R, TILE_DEPTH, TILE_FILLET = 0.46, 0.075, 0.053
RIM_R, RIM_T = 0.426, 0.030
SCREEN_R = 0.407
SCREEN_H = 0.814 * TILE_R / 0.55                 # flat-to-flat height mapped to the full image height
TILE_FRONT_Y = 2.80                             # wall at y=3.0 -> 12 cm standoff
TILE_EMIT = env_f("S05_TILE_EMIT", 0.30)
PLAYING = {3: ("s01_lights_world", "blue"), 4: ("s02_caustics", "mint"), 5: ("s03_gummy", "coral"),
           6: ("s04_every_dot", "lemon")}
PROXY_WINDOW = {"s01_lights_world": [121, 240], "s02_caustics": [1, 120], "s03_gummy": [1, 120],
                "s04_every_dot": [31, 150]}
SOLID = {0: "sky", 1: "blush", 2: "butter", 7: "pistachio", 8: "peach", 9: "sky"}
SOLID_SOFTEN = 0.40                             # mix toward the wall colour (calmer band)
WALL_COL = "lavender"

ROOT = D.ROOT
DEBUG_CAM = os.environ.get("S05_CAM", "")
MASK = os.environ.get("S05_MASK", "") == "1"


def srgb_mix(a, b, t):
    """Mix two palette colours in linear light and return an sRGB triple (D.col() linearises it exactly once)."""
    ca, cb = D.col(a), D.col(b)

    def enc(v):
        return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return tuple(enc(ca[i] * (1 - t) + cb[i] * t) for i in range(3))


COVE_COL = srgb_mix("lavender", "lilac", env_f("S05_LILAC", 0.20))


# ----------------------------------------------------------------------------------------------------------
# Curves of motion (closed form, frame -> value)
# ----------------------------------------------------------------------------------------------------------
def ease_out_back_s(t, s):
    t = D.clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


D_F1 = None  # filled after ORB_PX is converted to a distance


def orb_distance_for_px(px, r):
    """Camera distance at which a sphere of radius r, centred on the optical axis, is px wide (1920 frame)."""
    tan_a = (px / 2.0) / 960.0 * (SENSOR / 2.0) / LENS
    return r / math.sin(math.atan(tan_a))


def pull_p(f):
    """Pull-back clock with a 4-frame speed ramp (f1-5): the circle match holds ~2 frames (orb 468 -> ~454 -> ~416 px)
    and the camera is still far enough back by the f16 landing for the L to land in frame. Normalised to 1 at f34."""
    def tau(x):
        x = min(max(x, 1.0), 34.0) - 1.0
        return x * x / 8.0 if x <= 4.0 else x - 2.0
    return tau(f) / tau(34)


def pull_e(f):
    """Log-distance progress of the pull-back: ramped start, arrives ~f24, ~1.5% overshoot, settles f34."""
    return ease_out_back_s(pull_p(f), 0.5)


def cam_loc(f):
    d0, d1 = D_F1, (CAM_END - O).length
    e = pull_e(f)
    d = d0 * (d1 / d0) ** e
    el1 = math.atan2(CAM_END.z - O.z, -(CAM_END.y - O.y))
    el = el1 * e
    p = O + d * Vector((0.0, -math.cos(el), math.sin(el)))
    p.y += PUSH_Y * D.ease_in_out_sine(D.prog(f, 24, 120))
    return p


def tgt_loc(f):
    return O.lerp(TGT_END, D.ease_in_out_sine(D.prog(f, 1, 24)))


def focus_loc(f):
    return O.lerp(tgt_loc(f), D.smoothstep(D.prog(f, 1, 14)))


FSTOP_F1, FSTOP_END = 1.4, 4.0


def fstop(f):
    return FSTOP_F1 * (FSTOP_END / FSTOP_F1) ** D.ease_in_out_sine(D.prog(f, 1, 24))


def shutter(f):
    """0.5 -> 1.0 over the split (f8-11) so the halo streaks stay attached to their paths, back to 0.5 by f18."""
    return 0.5 + 0.5 * D.smoothstep(D.prog(f, F_SPLIT, F_SPLIT + 3)) * (1 - D.smoothstep(D.prog(f, 13, 18)))


def split_pos(k, f):
    """Coloured light k: born at O on F_SPLIT with zero speed, S-curve out with a small overshoot (settled ~f18),
    hovers, converges f53-61 (ease_in_out_cubic) and sits at O from the f61 downbeat."""
    home = Vector(SPLIT[k][1])
    if f < F_SPLIT:
        return O.copy()
    out = ease_out_back_s(D.smootherstep(D.prog(f, F_SPLIT, F_SPLIT + 12)), 1.0)
    back = D.ease_in_out_cubic(D.prog(f, F_CONV0, F_FUSE))
    hover = 0.012 * math.sin(2 * math.pi * (f - 16) / 40.0 + 2.1 * k) * D.smoothstep(D.prog(f, 16, 24)) * \
        (1 - D.smoothstep(D.prog(f, 47, F_CONV0)))
    p = O.lerp(home, out) + Vector((0, 0, hover))
    return p.lerp(O, back)


def split_on(f):
    return F_SPLIT <= f < F_SWAP


def bump(f, f0, rise=3.0, dur=14.0):
    """0 -> 1 -> 0 accent starting on f0: quick rise (peak at f0+rise), smooth decay, exactly 0 after f0+dur."""
    t = f - f0
    if t <= 0 or t >= dur:
        return 0.0
    x = t / rise
    return x * math.exp(1 - x) * (1 - D.smoothstep(D.prog(t, dur * 0.6, dur)))


def w_bob(f):
    return 0.01 * math.sin(2 * math.pi * (f - F_SWAP) / 60.0) * D.smoothstep(D.prog(f, F_SWAP, F_SWAP + 10))


def w_pos(f):
    return O + Vector((0.0, 0.0, w_bob(f)))


def white_halo_scale(f):
    """f1: r 0.12 (circle match) shrinking to HALO_R along the pull-back; f8-12 shrinks away as the colours peel out;
    POP back from inside from f59 (0.71 on the f61 downbeat, +23% peak f65); breathes +4% on f76 and f106."""
    r = HALO_R_F1 + (HALO_R - HALO_R_F1) * D.ease_in_out_sine(D.prog(f, 1, 24))
    if f < F_FUSE - 4:
        vis = 1 - D.smoothstep(D.prog(f, F_SPLIT, F_SPLIT + 4))
    else:
        vis = D.spring((f - (F_FUSE - 4)) / 30.0, 2.5, 8.0)
    breath = 1 + 0.04 * sum(bump(f, b) for b in F_BREATH)
    return r / HALO_R * vis * breath


def white_halo_emit(f):
    return HALO_W_EMIT_F1 + (HALO_W_EMIT - HALO_W_EMIT_F1) * D.smoothstep(D.prog(f, 2, F_SPLIT))


def col_halo_scale(f):
    if f < F_SPLIT:
        return 0.0
    pop = min(D.spring((f - F_SPLIT) / 30.0, 2.5, 8.0), 1.25)
    meet = 1 - 0.5 * D.smoothstep(D.prog(f, F_FUSE - 6, F_FUSE))
    gone = 1 - D.smoothstep(D.prog(f, F_FUSE, F_FUSE + 3))
    return pop * meet * gone


def letter_state(i, f):
    """(z_base, tilt_rad, sz) of letter i at frame f (before the floor lift). Every letter leans right."""
    tf = math.sqrt(2 * DROP_Z / DROP_G)
    vf = DROP_G * tf
    if f < LAND[i]:
        tau = (LAND[i] - f) / 30.0
        z = DROP_Z if tau >= tf else vf * tau - 0.5 * DROP_G * tau * tau
        v = 0.0 if tau >= tf else vf - DROP_G * tau
        sz = 1.0 + 0.06 * (v / vf)            # slight stretch along the fall, max at contact
        th = math.radians(TILT_DEG)
    else:
        t = (f - LAND[i]) / 30.0
        env = math.exp(-6 * t)
        osc = math.cos(2 * math.pi * 2.5 * t)
        z = 0.0
        sz = 1.0 - SQUASH * env * osc
        th = math.radians(TILT_DEG) * env * osc
    if F_FUSE <= f <= F_FUSE + 8:
        sz *= 1.0 - FUSE_PULSE * math.sin(math.pi * D.prog(f, F_FUSE, F_FUSE + 8))
    return z, th, sz


# ----------------------------------------------------------------------------------------------------------
# Inflated candy letters
# ----------------------------------------------------------------------------------------------------------
def glyph_loops(ch, size):
    """Original oriented outline contours ((N,2) arrays of x,z in metres, baseline z=0, left-aligned) of one
    Fredoka Bold glyph, read from the font curve (Blender's own fill of this TTF is even-odd and drops the overlap
    regions of 'a' and 'n'; the nonzero rule on these oriented contours gives the true glyph)."""
    from mathutils.geometry import interpolate_bezier
    bpy.ops.object.select_all(action="DESELECT")
    ob = D.text3d(ch, name="glyph_" + ch, font="fredoka", size=size, extrude=0.0, bevel=0.0, bevel_res=0,
                  location=(0, 0, 0), rotation=(0, 0, 0), align_x="LEFT", align_y="BOTTOM_BASELINE")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="CURVE")
    ob = bpy.context.object
    loops = []
    for sp in ob.data.splines:
        if sp.type == "BEZIER":
            bp = sp.bezier_points
            n = len(bp)
            pts = []
            for i in range(n):
                p0, p1 = bp[i], bp[(i + 1) % n]
                seg = interpolate_bezier(p0.co, p0.handle_right, p1.handle_left, p1.co, 32)
                pts += [(q.x, q.y) for q in seg[:-1]]
        else:
            pts = [(q.co.x, q.co.y) for q in sp.points]
        if len(pts) > 2:
            loops.append(np.array(pts, np.float64))
    cu = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return loops


def _resample(loop, h):
    p = np.vstack([loop, loop[:1]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    n = max(8, int(round(s[-1] / h)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)


def _winding_inside(P, A, B, chunk=3000):
    """Nonzero-winding inside test of points P against directed segments A->B (font rule; handles overlaps)."""
    out = np.empty(len(P), bool)
    for i in range(0, len(P), chunk):
        px, py = P[i:i + chunk, 0][:, None], P[i:i + chunk, 1][:, None]
        ax, ay, bx, by = A[None, :, 0], A[None, :, 1], B[None, :, 0], B[None, :, 1]
        cross = (bx - ax) * (py - ay) - (px - ax) * (by - ay)
        up = (ay <= py) & (by > py) & (cross > 0)
        dn = (by <= py) & (ay > py) & (cross < 0)
        out[i:i + chunk] = (up.sum(1) - dn.sum(1)) != 0
    return out


def _dist(P, A, B, chunk=3000):
    out = np.empty(len(P))
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    for i in range(0, len(P), chunk):
        p = P[i:i + chunk, None, :]
        t = np.clip(((p - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
        q = A[None] + t[..., None] * AB[None]
        out[i:i + chunk] = np.sqrt(((p - q) ** 2).sum(2).min(1))
    return out


def inflated_letter(name, loops, R, flat, H, h=0.0028, rings=12, grid=0.008):
    """Closed inflated solid from oriented glyph contours (x,z). Front/back half-thickness rises with an elliptical
    profile from `flat` at the outline to `flat + H` at an inward distance R (zero slope there: no ridge).
    Returns (mesh, boundary points (M,2), max inscribed distance)."""
    loops = [_resample(l, h) for l in loops]
    A = np.vstack(loops)
    B = np.vstack([np.roll(l, -1, 0) for l in loops])

    def ins(P):
        return _winding_inside(P, A, B)
    # keep only segments on the boundary of the union (overlapping contours are common in Fredoka)
    mid = (A + B) / 2
    tan = B - A
    nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-18
    eps = h * 0.25
    in_l = ins(mid + nrm * eps)
    in_r = ins(mid - nrm * eps)
    on_b = in_l != in_r
    inward = np.where(in_l[:, None], nrm, -nrm)
    Ab, Bb = A[on_b], B[on_b]
    starts = []
    off = 0
    for l in loops:
        starts.append((off, len(l)))
        off += len(l)
    keep_pt = on_b.copy()
    for (o, n) in starts:  # a point is kept if its outgoing or incoming segment is on the boundary
        keep_pt[o:o + n] |= np.roll(on_b[o:o + n], 1)
    pid = -np.ones(len(A), int)
    pid[keep_pt] = np.arange(keep_pt.sum())
    pts = [A[keep_pt]]
    edges = []
    for (o, n) in starts:
        for j in range(n):
            a, b = o + j, o + (j + 1) % n
            if on_b[a] and pid[a] >= 0 and pid[b] >= 0:
                edges.append((int(pid[a]), int(pid[b])))
    pn = np.zeros_like(A)
    for (o, n) in starts:
        seg_in = inward[o:o + n] * on_b[o:o + n, None]
        pn[o:o + n] = seg_in + np.roll(seg_in, 1, 0)
    pn /= np.linalg.norm(pn, axis=1, keepdims=True) + 1e-18
    bp, bn = A[keep_pt], pn[keep_pt]
    for k in range(1, rings + 1):
        dk = R * (1 - math.cos((k / rings) * math.pi / 2))
        q = bp + bn * dk
        q = q[ins(q)]
        if len(q):
            q = q[_dist(q, Ab, Bb) > dk * 0.8]
        if len(q) > 1 and k > 2:  # thin out points that crowd (inner side of tight curves)
            sel = [0]
            for j in range(1, len(q)):
                if np.linalg.norm(q[j] - q[sel[-1]]) > h * 0.6:
                    sel.append(j)
            q = q[sel]
        pts.append(q)
    mn, mx = A.min(0), A.max(0)
    gx, gz = np.meshgrid(np.arange(mn[0], mx[0], grid), np.arange(mn[1], mx[1], grid))
    G = np.stack([gx.ravel(), gz.ravel()], 1)
    G = G[ins(G)]
    d_in = float(_dist(G, Ab, Bb).max()) if len(G) else 0.0
    if len(G):
        G = G[_dist(G, Ab, Bb) > R + grid * 0.6]
        pts.append(G)
    P = np.vstack(pts)
    vo, eo, fo, ov, oe, of = delaunay_2d_cdt([Vector(p) for p in P], edges, [], 0, 1e-6)
    V = np.array([v[:] for v in vo])
    F = np.array([f for f in fo if len(f) == 3])
    F = F[ins(V[F].mean(1))]
    used = np.unique(F)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    V, F = V[used], remap[F]
    d = np.minimum(_dist(V, Ab, Bb), R)
    t = flat + (H / R) * np.sqrt(np.maximum(R * R - (R - d) ** 2, 0.0))
    nv = len(V)
    front = np.stack([V[:, 0], -t, V[:, 1]], 1)
    back = np.stack([V[:, 0], t, V[:, 1]], 1)
    a, b, c = front[F[:, 0]], front[F[:, 1]], front[F[:, 2]]
    flip = np.cross(b - a, c - a)[:, 1] > 0           # front faces must face -y (the camera)
    F[flip] = F[flip][:, ::-1]
    faces = [tuple(int(x) for x in f) for f in F] + [tuple(int(x) + nv for x in f[::-1]) for f in F]
    ec = Counter()
    for f in F:
        for j in range(3):
            ec[tuple(sorted((f[j], f[(j + 1) % 3])))] += 1
    for f in F:
        for j in range(3):
            u, w = int(f[j]), int(f[(j + 1) % 3])
            if ec[tuple(sorted((u, w)))] == 1:
                faces.append((w, u, u + nv, w + nv))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in np.vstack([front, back])], [], faces)
    me.validate()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    return me, np.vstack([Ab, Bb]), d_in


def zbin_extents(P, edges):
    """Per z-bin (min x, max x) of points P (x,z); NaN where empty."""
    idx = np.digitize(P[:, 1], edges) - 1
    lo = np.full(len(edges) - 1, np.nan)
    hi = np.full(len(edges) - 1, np.nan)
    for b in np.unique(idx):
        if 0 <= b < len(lo):
            m = idx == b
            lo[b], hi[b] = P[m, 0].min(), P[m, 0].max()
    return lo, hi


def build_title():
    """Ten letter objects (sorted left -> right), origins at base centre, and their outline points (local)."""
    uniq = sorted(set(WORD))
    unit = {c: glyph_loops(c, 1.0) for c in uniq}
    edges = np.arange(-0.4, 1.4, 0.01)
    ext = {}
    for c, loops in unit.items():
        P = np.vstack([_resample(l, 0.002) for l in loops])  # font outlines have 2 points per straight stem
        ext[c] = (zbin_extents(P, edges), P[:, 0].min(), P[:, 0].max())
    touch = []
    for a, b in zip(WORD[:-1], WORD[1:]):
        (la, ha), _, _ = ext[a]
        (lb, hb), _, _ = ext[b]
        m = ~np.isnan(ha) & ~np.isnan(lb)
        touch.append(float(np.max(ha[m] - lb[m])))
    span = ext[WORD[-1]][2] - ext[WORD[0]][1] + sum(touch)
    size = (TITLE_W - 9 * LET_GAP) / span
    xs = [0.0]
    for tch in touch:
        xs.append(xs[-1] + size * tch + LET_GAP)
    x_left = xs[0] + size * ext[WORD[0]][1]
    x_right = xs[-1] + size * ext[WORD[-1]][2]
    shift = -(x_left + x_right) / 2
    meshes = {}
    stroke = {}
    for c in uniq:
        loops = [l * size for l in unit[c]]
        me, bpts, d_in = inflated_letter("L_" + c, loops, LET_R, LET_FLAT, LET_H)
        stroke[c] = round(d_in, 3)
        co = np.array([v.co[:] for v in me.vertices])
        lo, hi = co.min(0), co.max(0)
        base = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
        me.transform(Matrix.Translation(-base))
        me.materials.append(None)                   # one slot; each object links its own colour
        meshes[c] = (me, base, bpts - np.array([base.x, base.z]))
    letters = []
    for i, c in enumerate(WORD):
        me, base, bpts = meshes[c]
        ob = D.link(bpy.data.objects.new(f"Letter_{i}_{c}", me))
        ob.location = (xs[i] + shift + base.x, TITLE_Y, -0.001)
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = D.mat_candy(COLOURS[i], rough=LET_ROUGH, name=f"candy_letter_{i}")
        letters.append((ob, bpts))
    print(f"[s05] title glyph size {size:.3f} m/em, gaps {LET_GAP} m, max inscribed half-stroke {stroke} "
          f"(pillow footprint LET_R {LET_R})")
    return letters, size


# ----------------------------------------------------------------------------------------------------------
# Honeycomb
# ----------------------------------------------------------------------------------------------------------
def rounded_hex(R, fillet, n_arc=8):
    """Flat-top hexagon (vertex at +x) with filleted corners, as (x, z) points, CCW."""
    pts = []
    c = R - fillet / math.sin(math.radians(60))
    for k in range(6):
        a = math.radians(60 * k)
        cx, cz = c * math.cos(a), c * math.sin(a)
        for j in range(n_arc + 1):
            ang = a - math.radians(30) + math.radians(60) * j / n_arc
            pts.append((cx + fillet * math.cos(ang), cz + fillet * math.sin(ang)))
    return pts


def hex_body(name, loc, mat):
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, z)) for x, z in rounded_hex(TILE_R, TILE_FILLET)]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.y += TILE_DEPTH
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = D._mesh_object(name, bm, mat, smooth=False)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.022
    bev.segments = 5
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(50)
    bev.harden_normals = True
    D.set_smooth(ob)
    ob.location = loc
    return ob


def hex_rim(name, loc, mat):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    pts = rounded_hex(RIM_R, 0.05, 10)
    sp.points.add(len(pts) - 1)
    for p, (x, z) in zip(sp.points, pts):
        p.co = (x, 0.0, z, 1.0)
    sp.use_cyclic_u = True
    cu.bevel_depth = RIM_T
    cu.bevel_resolution = 6
    cu.fill_mode = "FULL"
    ob = D.link(bpy.data.objects.new(name, cu))
    D.assign(ob, mat)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object
    D.set_smooth(ob)
    ob.location = loc
    return ob


def hex_screen(name, loc, mat):
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, z)) for x, z in rounded_hex(SCREEN_R, TILE_FILLET * 0.9)]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    uv = bm.loops.layers.uv.new("UVMap")
    for lp in f.loops:
        x, z = lp.vert.co.x, lp.vert.co.z
        lp[uv].uv = (0.5 + x / (SCREEN_H * 16 / 9), 0.5 + z / SCREEN_H)
    ob = D._mesh_object(name, bm, mat, smooth=False)
    ob.location = loc
    return ob


def build_band():
    tiles = []
    cream = D.mat_candy("cream", rough=0.25)
    for i, x in enumerate(TILE_X):
        z = BAND_Z + (BAND_DZ if i % 2 == 0 else -BAND_DZ)
        if i in PLAYING:
            tid, ccol = PLAYING[i]
            body = hex_body(f"Tile_{i}", (x, TILE_FRONT_Y, z), cream)
            rim = hex_rim(f"Rim_{i}", (x, TILE_FRONT_Y, z), D.mat_candy(ccol, rough=0.2))
            first = os.path.join(ROOT, "renders", "proxies", tid, "p_0001.png")
            vm = D.mat_video(first, N_FRAMES, name=f"video_{tid}", start=1, offset=0, emission=TILE_EMIT,
                             rough=0.2, cyclic=False)
            # tile screen (custom setup #5): dark glass that emits its picture. Low specular / thin coat so the
            # bright cove does not veil the picture (r1: spec 0.5 + coat 0.6 lifted the blacks into lavender).
            nt = vm.node_tree
            pb = nt.nodes["Principled BSDF"]
            for lk in list(pb.inputs["Base Color"].links):
                nt.links.remove(lk)
            pb.inputs["Base Color"].default_value = D.col("ink")
            pb.inputs["Specular IOR Level"].default_value = 0.15
            pb.inputs["Coat Weight"].default_value = 0.1
            scr = hex_screen(f"Screen_{i}", (x, TILE_FRONT_Y - 0.002, z), vm)
            tiles.append((i, body, rim, scr))
        else:
            soft = srgb_mix(SOLID[i], WALL_COL, SOLID_SOFTEN)
            body = hex_body(f"Tile_{i}", (x, TILE_FRONT_Y, z),
                            D.mat_candy(soft, rough=0.4, coat=0.5, coat_rough=0.12, name=f"tile_{SOLID[i]}_{i}"))
            rim = hex_rim(f"Rim_{i}", (x, TILE_FRONT_Y, z),
                          D.mat_candy(srgb_mix(soft, "white", 0.55), rough=0.3, name=f"rim_{SOLID[i]}_{i}"))
            tiles.append((i, body, rim, None))
    return tiles


def proxy_report():
    """Tile sources from renders/proxies/manifest.json (written by scripts/make_tile_proxies.py)."""
    try:
        with open(os.path.join(ROOT, "renders", "proxies", "manifest.json")) as fh:
            man = json.load(fh)
    except (OSError, ValueError):
        man = {}
    rep = {}
    for tid, _ in PLAYING.values():
        info = man.get(tid) or {}
        rep[tid] = {"source": info.get("source", "missing"), "source_frames": info.get("source_frames"),
                    "written": info.get("written")}
        if info.get("source_frames") and list(info["source_frames"]) != PROXY_WINDOW[tid]:
            print(f"[s05] WARNING proxy {tid} plays source f{info['source_frames']}, S05 expects "
                  f"f{PROXY_WINDOW[tid]}: re-run scripts/make_tile_proxies.py", flush=True)
    return rep


# ----------------------------------------------------------------------------------------------------------
# Lights
# ----------------------------------------------------------------------------------------------------------
def halo(name, colour, strength, radius, loc):
    """Light-marker halo (storyboard custom setup #3): camera + glossy only, never lights, never blocks."""
    m = D.mat_emission(colour, strength, name="halo_" + name)
    m.cycles.emission_sampling = "NONE"
    ob = D.sphere(name, radius, loc, m, segments=64, rings=32)
    ob.visible_camera = True
    ob.visible_glossy = True
    ob.visible_diffuse = False
    ob.visible_transmission = False
    ob.visible_shadow = False
    ob.visible_volume_scatter = False
    return ob


def key_spot(name, colour, power):
    """One of the four story lights: SPOT r 0.04 at O aimed down-forward (all four share position, aim and cone, so
    the f71 swap is invisible). Glossy-invisible so it leaves no hot specular pool in the glossy cove floor."""
    ob = D.light("SPOT", name, tuple(O), tuple(KEY_AIM), power, colour, radius=LIGHT_R, spot_deg=KEY_CONE,
                 blend=KEY_BLEND)
    ob.visible_glossy = False
    return ob


# ----------------------------------------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------------------------------------
args = D.parse_args()
PROXIES = proxy_report()
_out_dir = os.path.abspath(args.out or os.path.join(ROOT, "renders", args.mode, SHOT))
_final_dir = os.path.abspath(os.path.join(ROOT, "renders", "final", SHOT))
print("[s05] PROXIES", json.dumps(PROXIES), flush=True)
_srcs = [v["source"] for v in PROXIES.values()]
if args.mode == "final" and _out_dir == _final_dir and not args.no_render and \
        any(s != "final" for s in _srcs) and os.environ.get("S05_ALLOW_NONFINAL_PROXIES") != "1":
    sys.stderr.write("[s05] REFUSING the S05 final: the tile proxies are not all from finals "
                     f"({_srcs}). Re-run scripts/make_tile_proxies.py after the S01-S04 finals (storyboard 6).\n")
    sys.stderr.flush()
    os._exit(4)
if any(s in ("placeholder", "missing") for s in _srcs):
    print(f"[s05] WARNING: placeholder tiles in this render: {_srcs}", flush=True)

D.reset_scene()
D.setup_cycles(samples=384, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=4, caustics=False,
               clamp_indirect=10, motion_blur=True, shutter=0.5)
D.setup_color(exposure=EXPOSURE)
D.setup_output()
sc = bpy.context.scene
sc.frame_end = N_FRAMES
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False

D_F1 = orb_distance_for_px(ORB_PX, HALO_R_F1)

# title first (text conversion uses the selection)
letters, glyph_size = ([], 0.0) if os.environ.get("S05_NOLETTERS") else build_title()

cove_mat = D.mat_clay(COVE_COL, rough=0.7, sss=0.0, sheen=0.1, name="cove_lavender")
_cp = cove_mat.node_tree.nodes["Principled BSDF"]
_cp.inputs["Coat Weight"].default_value = COVE_COAT       # soft clear coat: the letters reflect in the floor
_cp.inputs["Coat Roughness"].default_value = 0.22
cove = D.cyclorama("Cove", width=30, depth=20, height=8, radius=1.2, wall_y=3.0, mat=cove_mat)
tiles = build_band()

# story lights (spots behind the word) + halos
W = key_spot("OrbW", "white", W_POWER)
HW = halo("HaloW", "white", HALO_W_EMIT_F1, HALO_R, tuple(O))
CL, CH = [], []
for k, (cname, pos, frac) in enumerate(SPLIT):
    CL.append(key_spot("Orb_" + cname, cname, 0.0))
    CH.append(halo("Halo_" + cname, cname, HALO_C_EMIT, HALO_R - 0.0004 * k, tuple(O)))
fill = D.light("AREA", "Fill", (0, -6.0, 4.0), (0, 0.5, 0.8), power=FILL_POWER, color="white", size=6.0)
# cyc wash: a wide soft source above the frame aimed at the wall, so the backdrop reads pastel while the
# foreground floor keeps a gentle falloff toward the bottom edge (light-based, no vignette)
wash = D.light("AREA", "WallWash", (0.0, 1.7, 4.7), (0.0, 3.0, 1.9), power=WASH_POWER, color="white", size=10.0,
               size_y=1.2) if WASH_POWER > 0 else None
if os.environ.get("S05_FILL_NOCOVE", "1") == "1":   # floor: key pool + wash spill -> falls off toward the bottom
    fill_rx = bpy.data.collections.new("FillExclude")
    fill_rx.objects.link(cove)
    fill.light_linking.receiver_collection = fill_rx
    for co in fill_rx.collection_objects:
        co.light_linking.link_state = "EXCLUDE"
rig = D.world_hdri(D.HDRI["studio_small_09"], 0.3, camera_bg="lavender")

# letter-only lights (light linking): even white face key (diffuse only), the candy highlight strip (glossy only)
# and the hold's shine sweep (glossy only). None of them touches the floor, so the shadow story is lamp-only.
gl_set = bpy.data.collections.new("GlossReceivers")
for ob, _ in letters:
    gl_set.objects.link(ob)
face = D.light("AREA", "FaceKey", (0.0, -3.2, 1.6), (0.0, 0.4, 0.35), power=FACE_POWER, color="white", size=5.0,
               size_y=1.2)
face.visible_glossy = False
gloss = D.light("AREA", "GlossStrip", (0.0, -3.2, 3.4), (0.0, 0.4, 0.45), power=GLOSS_POWER, color="white", size=3.2,
                size_y=0.7)
SHINE_X0 = 3.6
shine = D.light("AREA", "ShineStrip", (-SHINE_X0, -3.0, 1.3), (-SHINE_X0, 0.4, 0.35), power=0.0, color="white",
                size=0.22, size_y=2.4)
for lo in (gloss, shine):
    lo.visible_diffuse = False
    lo.visible_transmission = False
    lo.visible_volume_scatter = False
    lo.visible_glossy = True
for lo in (face, gloss, shine):
    lo.light_linking.receiver_collection = gl_set


def shine_x(f):
    return -SHINE_X0 + 2 * SHINE_X0 * D.ease_in_out_sine(D.prog(f, *F_SHINE))


def shine_power(f):
    return SHINE_POWER * math.sin(math.pi * D.prog(f, *F_SHINE)) ** 2


D.bake(shine, "location", 1, N_FRAMES, lambda f: (shine_x(f), -3.0, 1.3))
D.bake(shine.data, "energy", 1, N_FRAMES, shine_power)

D.bake(W, "location", 1, N_FRAMES, lambda f: tuple(w_pos(f)))
D.bake(W.data, "energy", 1, N_FRAMES, lambda f: 0.0 if split_on(f) else W_POWER)
D.bake(HW, "location", 1, N_FRAMES, lambda f: tuple(w_pos(f)))
D.bake(HW, "scale", 1, N_FRAMES, lambda f: (max(white_halo_scale(f), 1e-4),) * 3)
D.bake(HW.active_material.node_tree.nodes["Emission"].inputs["Strength"], "default_value", 1, N_FRAMES,
       white_halo_emit)
for k, (cname, pos, frac) in enumerate(SPLIT):
    D.bake(CL[k], "location", 1, N_FRAMES, lambda f, k=k: tuple(split_pos(k, f)))
    D.bake(CH[k], "location", 1, N_FRAMES, lambda f, k=k: tuple(split_pos(k, f)))
    D.bake(CL[k].data, "energy", 1, N_FRAMES, lambda f, fr=frac: W_POWER * fr if split_on(f) else 0.0)
    D.bake(CH[k], "scale", 1, N_FRAMES, lambda f: (max(col_halo_scale(f), 1e-4),) * 3)
D.bake(sc.render, "motion_blur_shutter", 1, N_FRAMES, shutter)

# letters: fall, BOING, tilt, floor lift (lowest outline point stays on the floor)


def letter_xform(i, f):
    ob, bpts = letters[i]
    z, th, sz = letter_state(i, f)
    sxy = 1.0 / math.sqrt(sz)
    zz = -np.sin(th) * (sxy * bpts[:, 0]) + np.cos(th) * (sz * bpts[:, 1])
    lift = max(0.0, -float(zz.min()))
    return z + lift, th, sxy, sz


for i, (ob, bpts) in enumerate(letters):
    x0, y0, z0 = ob.location
    D.bake(ob, "location", 1, N_FRAMES, lambda f, i=i, x0=x0, y0=y0, z0=z0: (x0, y0, z0 + letter_xform(i, f)[0]))
    D.bake(ob, "rotation_euler", 1, N_FRAMES, lambda f, i=i: (0.0, letter_xform(i, f)[1], 0.0))
    D.bake(ob, "scale", 1, N_FRAMES, lambda f, i=i: (letter_xform(i, f)[2], letter_xform(i, f)[2],
                                                      letter_xform(i, f)[3]))

# camera
focus = D.empty("Focus", tuple(O))
cam, tgt = D.camera("Cam", tuple(cam_loc(1)), tuple(O), lens=LENS, fstop=FSTOP_F1, focus=focus, sensor=SENSOR)
D.bake(cam, "location", 1, N_FRAMES, lambda f: tuple(cam_loc(f)))
D.bake(tgt, "location", 1, N_FRAMES, lambda f: tuple(tgt_loc(f)))
D.bake(focus, "location", 1, N_FRAMES, lambda f: tuple(focus_loc(f)))
D.bake(cam.data, "dof.aperture_fstop", 1, N_FRAMES, fstop)


# ----------------------------------------------------------------------------------------------------------
# QA printouts: lockup, orb size, letter clearance
# ----------------------------------------------------------------------------------------------------------
def project(points, f):
    from bpy_extras.object_utils import world_to_camera_view
    sc.frame_set(f)
    return np.array([world_to_camera_view(sc, cam, Vector(p))[:2] for p in points])


def lockup_report():
    rep = {}
    d = (cam_loc(1) - O).length
    r = HALO_R_F1
    rep["f1_orb_px"] = round(2 * 960 * math.tan(math.asin(r / d)) / ((SENSOR / 2) / LENS), 1)
    rep["f1_cam_dist"] = round(d, 4)
    for f in (34, 120):
        pts = []
        for ob, _ in letters:
            sc.frame_set(f)
            mw = ob.matrix_world
            vs = ob.data.vertices
            step = max(1, len(vs) // 3000)
            pts += [mw @ vs[j].co for j in range(0, len(vs), step)]
        uv = project(pts, f) if pts else np.zeros((1, 2))
        band = []
        for (i, body, rim, scr) in tiles:
            for o in (body, rim):
                mw = o.matrix_world
                band += [mw @ v.co for v in o.data.vertices]
        bv = project(band, f)
        orbs = [tuple(split_pos(k, 50)) for k in range(3)] + [tuple(O)]
        ov = project(orbs, f)
        rep[f"f{f}"] = {
            "title_w_pct": round(100 * (uv[:, 0].max() - uv[:, 0].min()), 2),
            "title_left_right_px": [round(1920 * uv[:, 0].min()), round(1920 * uv[:, 0].max())],
            "baseline_from_top_pct": round(100 * (1 - uv[:, 1].min()), 2),
            "title_top_from_top_pct": round(100 * (1 - uv[:, 1].max()), 2),
            "band_top_px": round(1080 * (1 - bv[:, 1].max()), 1),
            "band_top_from_top_pct": round(100 * (1 - bv[:, 1].max()), 2),
            "band_bottom_from_top_pct": round(100 * (1 - bv[:, 1].min()), 2),
            "band_x_px": [round(1920 * bv[:, 0].min()), round(1920 * bv[:, 0].max())],
            "orbs_from_top_pct": [round(100 * (1 - v[1]), 1) for v in ov],
            "orbs_x_px": [round(1920 * v[0]) for v in ov],
        }
    return rep


def clearance_report():
    worst = []
    edges = np.arange(-0.2, 1.6, 0.01)
    for i in range(len(letters) - 1):
        g_min, f_min = 9.0, None
        for f in range(1, N_FRAMES + 1):
            P = []
            for j in (i, i + 1):
                ob, bpts = letters[j]
                zb, th, sxy, sz = letter_xform(j, f)
                x = sxy * bpts[:, 0]
                z = sz * bpts[:, 1]
                X = np.cos(th) * x + np.sin(th) * z + base_x[j]
                Z = -np.sin(th) * x + np.cos(th) * z + zb
                P.append(np.stack([X, Z], 1))
            (la, ha) = zbin_extents(P[0], edges)
            (lb, hb) = zbin_extents(P[1], edges)
            m = ~np.isnan(ha) & ~np.isnan(lb)
            if m.any():
                g = float(np.min(lb[m] - ha[m]))
                if g < g_min:
                    g_min, f_min = g, f
        worst.append((f"{i}{WORD[i]}{WORD[i + 1]}", round(g_min, 4), f_min))
    return worst


base_x = [ob.location.x for ob, _ in letters]
sc.frame_set(1)
LOCKUP = lockup_report() if letters else {}
CLEAR = clearance_report() if letters else []
print("[s05] LOCKUP", json.dumps(LOCKUP))
print("[s05] CLEARANCE (pair, min gap m, frame)", CLEAR)
if LOCKUP and LOCKUP["f120"]["band_top_px"] < 40:
    print(f"[s05] WARNING band top {LOCKUP['f120']['band_top_px']} px from the frame top (< 40 px)", flush=True)

# ----------------------------------------------------------------------------------------------------------
# Meta (written at build time, every mode, before rendering)
# ----------------------------------------------------------------------------------------------------------
events = {"orb": 1, "split": F_SPLIT, "split_landed": F_SPLIT + 10}
for i, f in enumerate(LAND):
    events[f"land_{i}_{WORD[i]}"] = f
events.update({"letters_done": LAND[-1], "settle": 51, "converge_start": F_CONV0, "fuse": F_FUSE,
               "lights_at_O": F_FUSE, "swap_to_white": F_SWAP, "hold": F_SWAP, "breath_1": F_BREATH[0],
               "shine": (F_SHINE[0] + F_SHINE[1]) // 2, "breath_2": F_BREATH[1], "end": N_FRAMES})
meta = {"id": SHOT, "frames": N_FRAMES, "start_frame_in_film": START_IN_FILM, "events": events, "per_frame": {},
        "orb_px_f1": LOCKUP.get("f1_orb_px"), "lockup": LOCKUP, "tile_proxies": PROXIES,
        "letter_clearance_min_m": {p: g for p, g, _ in CLEAR}}
os.makedirs(os.path.join(ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=2)

# ----------------------------------------------------------------------------------------------------------
# Orb glow (lead note G1): S01's compositor bloom, identical parameters, driven by the Emit pass only, so only the
# halo markers glow (lit surfaces and the 0.30-emission screens stay under the 0.6 threshold and never bloom).
# ----------------------------------------------------------------------------------------------------------
if GLOW > 0 and not MASK:
    sc.view_layers[0].use_pass_emit = True
    sc.use_nodes = True
    ct = sc.node_tree
    for nd in list(ct.nodes):
        ct.nodes.remove(nd)
    rl = ct.nodes.new("CompositorNodeRLayers")
    gl = ct.nodes.new("CompositorNodeGlare")
    gl.glare_type = "BLOOM"
    gl.quality = "HIGH"
    gl.inputs["Threshold"].default_value = 0.6
    gl.inputs["Smoothness"].default_value = 0.2
    gl.inputs["Strength"].default_value = GLOW
    gl.inputs["Size"].default_value = 0.45
    gl.inputs["Saturation"].default_value = 1.0
    ct.links.new(rl.outputs["Emit"], gl.inputs["Image"])
    add_glow = ct.nodes.new("CompositorNodeMixRGB")
    add_glow.blend_type = "ADD"
    add_glow.inputs["Fac"].default_value = 1.0
    ct.links.new(rl.outputs["Image"], add_glow.inputs[1])
    ct.links.new(gl.outputs["Glare"], add_glow.inputs[2])
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(add_glow.outputs[0], comp.inputs["Image"])

# ----------------------------------------------------------------------------------------------------------
# Debug cameras / mask mode
# ----------------------------------------------------------------------------------------------------------
if DEBUG_CAM in ("top", "side"):
    cd = bpy.data.cameras.new("DebugCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 11.0
    dc = D.link(bpy.data.objects.new("DebugCam", cd))
    if DEBUG_CAM == "top":
        dc.location = (0, -0.5, 14)
        dc.rotation_euler = (0, 0, 0)
    else:
        dc.location = (12, -0.5, 1.5)
        dc.rotation_euler = (math.radians(90), 0, math.radians(90))
        cd.ortho_scale = 12.0
    sc.camera = dc

if MASK:
    blk = D.mat_emission("#000000", 0.0, name="mask_black")
    red = D.mat_emission((1, 0, 0), 1.0, name="mask_red")
    grn = D.mat_emission((0, 1, 0), 1.0, name="mask_green")
    for ob in sc.objects:
        if ob.type != "MESH":
            continue
        m = red if ob.name.startswith("Letter_") else (grn if ob.name.startswith("Screen_") else blk)
        for s in ob.material_slots:
            s.material = m
        if not ob.material_slots:
            ob.data.materials.append(m)
    for ob in sc.objects:
        if ob.type == "LIGHT":
            ob.data.energy = 0.0
            if ob.data.animation_data:
                ob.data.animation_data_clear()
    D.world_color("#000000", 0.0)
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.0
    sc.render.use_motion_blur = False
    sc.cycles.use_denoising = False
    sc.cycles.samples = 16

D.finish(args, final_samples=int(env_f("S05_SPP", 384)), final_threshold=env_f("S05_THR", 0.02), frame_end=N_FRAMES,
         shot_name=SHOT)
