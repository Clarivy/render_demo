"""S05 v2 . s05_finale: "Every scene". Film frames 781-960 (bars 14-16), 180 frames, GPU 7.

Spec: docs/storyboard_v2.md section 3 (and section 4, the hex-tile contract this shot consumes). Built from a copy of
shots/s05_title.py (v1, frozen; kept for reference in renders/work/s05_finale/s05_title_v1_reference.py).

What the shot does
* f1 is S04's last frame: the camera looks square at the centre screen of a honeycomb wall, at the distance where the
  screen's image hexagon (the S04 overscan still, 2544 x 2204) is exactly 2544 px wide, so the central 1920 x 1080 of
  the still lands 1:1 on the frame (an invisible match cut on the bar-14 downbeat).
* One continuous pull-back (log distance to the centre tile, ease-in from rest): the painting shrinks into its orange
  candy bezel, ring 1 (the six chapter tiles) arrives ~f8-20, outer rings enter and POP on 8th notes, the honeycomb
  fills the frame (the "many scenes" moment f39-54, up to 21 full tiles, ~75 % covered), the white key orb swells out
  of the girl in white (f42-46, POP f46) and glides to O (arrives f61, zero speed); the camera follows it down (tilt
  f49-68, crane f50-76: the honeycomb slides up, the stage comes up from the bottom) and settles on v1's end framing
  (distance overshoot ~0.9 %, at rest f82).
* The title is v1's, shifted +60 frames: split f68, letters land 76..110 on 16ths, converge f113-121, fuse f121,
  swap f131, breaths f136/f166, shine f144-158, 1 % push f84-180. Same letters, materials, lights, bloom, end camera.

Honeycomb (storyboard_v2 3.1)
* Flat-top lattice, image-hex circumradius HEX_R 0.355 m; each cell = lavender slab (the grout/wall, cove material,
  packed edge to edge so the bevels read as grout lines) + candy bezel ring (pillowy superellipse profile, glossy) +
  screen recessed 2.7 cm behind the bezel crest. Centre cell at (0, 2.935, 2.165). Odd columns sit half a row lower;
  the bottom row is complete (even columns one row below the centre, odd half a row), so ring 1 has all six cells.
* Assignment: centre = c_painting (S04 overscan still); ring 1 = the six chapter tiles in story order clockwise from the
  top (s01 night top, s01 day, s02 wide, s02 macro below the painting, s03 gummy, s04 gallery); rings >= 2 greedy:
  never the same source as a neighbour, least-used first (minis before chapter repeats, the dark night tile never
  repeats), neighbour hero colours differ where possible; repeats get different frame offsets, chosen so a
  non-periodic source never wraps while its cell is on screen.
* Ripple: each ring POPs its bezels (in-plane scale 1.035, +1.2 cm toward the lens, POP spring 2.5 Hz / 8) on the first
  8th note after it enters the frame (f8.5, 23.5, 31, 38.5); no pops after f46.

Screens (storyboard_v2 3.3)
* Textures are read as Non-Color (raw sRGB code values t). Emission = InvView(t) x gain, where InvView = the closed-form
  Khronos PBR Neutral inverse of srgb_decode(t) x 2^(19 delta(t)) x 2^-EXPOSURE. delta is a 97^3 correction LUT
  (sqrt shaper, trilinear, float atlas built in bpy from renders/work/s05_finale/calib/inv_view_delta_97.npy) that
  turns it into the inverse of Blender's REAL view (OCIO: lg2 allocation [-9, 10] -> pbrNeutral.cube 57^3,
  tetrahedral -> sRGB), which differs from the closed form by up to ~6/255 on saturated colours. Built by
  lib/pbrn_view/{pbrn_lut,build_inv_lut,delta_lut}.py (the numpy model of the view reproduces Blender's
  output to 1 LSB of 16 bit). Calibration render (f1, chart on the frame-filling screen, final res):
  renders/work/s05_finale/calib/calibration_compare.{png,json}: ramp mean 0.11 / p99 0.47, film palette 0.17 / 0.85,
  real frame 0.12 / 0.49 (/255). Display colours the view cannot produce (a saturated colour with a channel at 255,
  e.g. the raw palette hexes or flat placeholders) fade toward white, as with any inverse.
* Gain 1.0 to f60, eases to GAIN_END by f90. Secondary rays: only short ones (ray length < 0.10-0.22 m: the cell's own
  bezel and slab) see K_DIFF of the emission, so the screens light their bezels (tactile) but never the cove, floor or
  letters; longer secondary rays see a wall-like lavender BSDF (the cove material's values) and the screens are
  excluded from the Fill light like the cove, so the floor and its coat reflections below the honeycomb match v1
  ('title unchanged': mean |d| below y 420 went from 20/255 with ungated screens to ~1.5/255). emission_sampling NONE.
  A thin Fresnel coat ramps 0 -> COAT_MAX over f4-30 (f1 is emission only, so the seam matches).
* Bloom: v1/S01's compositor Glare (BLOOM, HIGH, threshold 0.6, smoothness 0.2, strength 1, size 0.45, saturation 1)
  driven by a Shader AOV "orb_glow" that only the light-marker halos write (= their emission colour x strength, i.e.
  exactly what v1's Emit pass held for them). Screens never bloom.
* Guard: refuses renders/final/s05_finale unless renders/hex_tiles/manifest.json says every tile and the centre are
  final (S05F_ALLOW_NONFINAL=1 overrides, tests only). Without a manifest the shot uses the development placeholders in
  renders/work/s05_finale/placeholders/ (never in a final).

Deviations / tunables (logged per lead decision 3)
 1. Bottom row is complete (no notch) so ring 1 holds all six chapter tiles and the many-scenes moment reaches ~75 %
    coverage; with the lime split orb at y ~367 px the honeycomb must end <= ~335 px near the centre, which caps the end
    tile size at ~160 px wide (screen; bezel ~174 px) with the painting tile's bezel 4.5 px under the frame top.
 2. The camera is level with the centre tile (z 2.165 vs end 2.15), so the move is pull-back + tilt (no rise). The tilt
    (f48-68) is timed so every letter is off-frame when it becomes visible (L at f57 is still 30 px outside the left
    edge and enters from there, 'a' at f61 is 74 px above the top), see meta letters[].bbox_px_at_visible.
 3. Orb glide f46-61 covers ~1.5 m (screen at y 2.935 to O) in 15 frames: peak ~15 cm/f (> the 10 cm/f light rule).
    The lamp stays off while the orb is fast (ramps up f56-61, the orb is <= 10 cm/f from f58); only the
    motion-blurred halo mesh is fast, and the camera follows it down.
 4. Letters are hidden until their fall starts (v1 kept them hanging at DROP_Z from f1); identical from f110 on.
 5. f1 (the match frame): pixel filter 0.01 (keyed to 1.5 by f5) and a closed shutter, because the centre still is
    1:1 with the render and the move that starts after f1 would otherwise blur it (~1.3 px at the frame edge).

Env vars: S05F_CAM=top|side (ortho debug cameras), S05F_MASK=1 (flat ID render: letters red, screens green, bezels
blue, rest black), S05F_NOLETTERS=1, S05F_NOGLOW=1, S05F_NOORBS=1, S05F_CENTER=<png> (centre still override, used by the
calibration), S05F_ALLOW_NONFINAL=1, S05F_KDIFF, S05F_GAIN, S05F_COAT, S05F_GIRL="u,v" (orb birth point in units of
HEX_R on the centre screen), S05F_SPP, S05F_THR, S05F_MANIFEST=<path>, camera clocks S05F_EA / EFA / EFB / EC / EFC /
ST / FOC / REST (layout probes: renders/work/s05_finale/tools/layout_probe.sh).
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
# Shot and the v1 title timeline (v1-local frames fv; the film plays them at f = fv + OFF)
# ----------------------------------------------------------------------------------------------------------
SHOT, N_FRAMES, START_IN_FILM = "s05_finale", 180, 781
EXPOSURE = -0.2
OFF = 60

F_SPLIT = 8
LAND = [16, 20, 24, 27, 31, 35, 39, 42, 46, 50]
F_CONV0, F_FUSE, F_SWAP = 53, 61, 71
F_BREATH = (76, 106)
F_SHINE = (84, 98)
assert LAND == [16 + int(math.floor(3.75 * i + 0.5)) for i in range(10)]
LAND_V2 = [f + OFF for f in LAND]

# story lights (v1 values, no overrides: the title must be unchanged)
KEY_Y, KEY_Z = 2.00, 0.92
SPLIT_DX = 0.90
O = Vector((0.0, KEY_Y, KEY_Z))
SPLIT = [("coral", (-SPLIT_DX, KEY_Y, KEY_Z - 0.04), 0.49), ("lime", (0.0, KEY_Y, KEY_Z + 0.10), 1.05),
         ("blue", (SPLIT_DX, KEY_Y, KEY_Z - 0.04), 0.94)]
KEY_AIM = Vector((0.0, -0.6, 0.0))
KEY_CONE, KEY_BLEND = 100.0, 0.4
W_POWER = 560.0
LIGHT_R = 0.04
HALO_R = 0.10
HALO_R_F1 = 0.12
S04_ORB_EMIT, S04_EXPOSURE = 3.2, -0.1
HALO_W_EMIT_F1 = S04_ORB_EMIT * 2.0 ** (S04_EXPOSURE - EXPOSURE)
HALO_W_EMIT, HALO_C_EMIT = 4.0, 2.0
FACE_POWER = 140.0
FILL_POWER = 160.0
WASH_POWER = 200.0
GLOSS_POWER = 260.0
SHINE_POWER = 900.0
COVE_COAT = 0.5
GLOW = 0.0 if os.environ.get("S05F_NOGLOW") else 1.0

# camera (v1 end framing)
LENS, SENSOR = 50.0, 36.0
FPX = LENS / SENSOR * 1920.0                    # focal length in px at 100 % (horizontal sensor fit)
CAM_END = Vector((0.0, -9.0, 2.15))
TGT_END = Vector((0.0, 0.40, 0.57))
PUSH_Y = 0.08                                   # v1 f24-120 push = v2 f84-180
FSTOP = 4.0

# title (v1)
WORD = "LaRenderer"
COLOURS = ["pink", "coral", "orange", "lemon", "lime", "mint", "aqua", "blue", "violet", "#C454C9"]
TITLE_W = 5.0
TITLE_Y = 0.40
LET_R, LET_FLAT, LET_H = 0.075, 0.035, 0.115
LET_GAP = 0.08
LET_ROUGH = 0.2
DROP_Z, DROP_G = 2.8, 14.0
SQUASH, TILT_DEG = 0.30, 6.0
FUSE_PULSE = 0.07

# honeycomb (v2)
HEX_R = env_f("S05F_HEX_R", 0.355)             # image-hexagon circumradius on the screen plane (m)
K_IN, K_SCR, K_OUT = 1.006, 1.07, 1.115        # bezel opening / screen mesh / bezel outer edge (x HEX_R)
GROUT = 0.025
PITCH = math.sqrt(3) * K_OUT * HEX_R + GROUT   # centre distance of edge neighbours
RC = PITCH / math.sqrt(3)                      # cell (slab) circumradius
ZC = env_f("S05F_ZC", 2.165)
WALL_Y = 3.0
SLAB_FRONT_Y, SLAB_BACK_Y = 2.94, 3.005
SCREEN_Y = SLAB_FRONT_Y - 0.005
BEZEL_H = 0.032
NCOL, NROW = 8, 3
POP_SCALE, POP_LIFT = 0.035, 0.012
POP_LAST = 46.0                                # no ripple pops after this frame (calm title section)
COAT_MAX = env_f("S05F_COAT", 0.06)
K_DIFF = env_f("S05F_KDIFF", 0.35)                 # short secondary rays (own bezel / slab)
NEAR_RAY = (0.10, 0.22)                         # secondary ray length (m): full -> none
GAIN_END = env_f("S05F_GAIN", 0.75)
BEZEL_SOFT = 0.35                              # bezel hero colour mixed toward white (calm candy)
CENTRE_BEZEL = "orange"                        # the painting keeps S04's frame colour
TILE_RES = (1152, 998)
CENTRE_RES = (2544, 2204)

# pull-back clocks (f1 -> f84)
def env_pair(name, default):
    v = os.environ.get(name)
    return tuple(float(x) for x in v.split(",")) if v else default


E_A, E_FA = env_f("S05F_EA", 0.81), env_f("S05F_EFA", 52)       # zoom-out phase: a * I_t(2,3) over f1-E_FA
E_FB = env_pair("S05F_EFB", (47, 76))           # crane-down phase: smootherstep over E_FB
E_C, E_FC = env_f("S05F_EC", 0.004), env_pair("S05F_EFC", (74, 82))   # settle: overshoot c (log distance), return
S_T = env_pair("S05F_ST", (48, 68))             # tilt: tile screen position centre -> final, smootherstep
F_FOC = env_pair("S05F_FOC", (46, 74))          # focus rack: centre screen -> title plane
F_REST = int(env_f("S05F_REST", 82))            # from here on: exactly v1's end framing (+ its 1 % push)

# key orb birth (v2 f46-61)
GIRL = [float(v) for v in os.environ.get("S05F_GIRL", "-0.082,-0.208").split(",")]   # x HEX_R, on the centre screen
F_SWELL0, F_BORN, F_ARRIVE = 42, 46, 61
F_LAMP = (56, 61)

ROOT = D.ROOT
DEBUG_CAM = os.environ.get("S05F_CAM", "")
MASK = os.environ.get("S05F_MASK", "") == "1"
WORK = os.path.join(ROOT, "renders", "work", SHOT)


def srgb_mix(a, b, t):
    """Mix two palette colours in linear light and return an sRGB triple (D.col() linearises it exactly once)."""
    ca, cb = D.col(a), D.col(b)

    def enc(v):
        return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return tuple(enc(ca[i] * (1 - t) + cb[i] * t) for i in range(3))


COVE_COL = srgb_mix("lavender", "lilac", 0.20)


# ----------------------------------------------------------------------------------------------------------
# v1 curves of motion (closed form). All take the v1-local frame fv = f - OFF.
# ----------------------------------------------------------------------------------------------------------
def ease_out_back_s(t, s):
    t = D.clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def shutter_v1(fv):
    return 0.5 + 0.5 * D.smoothstep(D.prog(fv, F_SPLIT, F_SPLIT + 3)) * (1 - D.smoothstep(D.prog(fv, 13, 18)))


def split_pos(k, fv):
    home = Vector(SPLIT[k][1])
    if fv < F_SPLIT:
        return O.copy()
    out = ease_out_back_s(D.smootherstep(D.prog(fv, F_SPLIT, F_SPLIT + 12)), 1.0)
    back = D.ease_in_out_cubic(D.prog(fv, F_CONV0, F_FUSE))
    hover = 0.012 * math.sin(2 * math.pi * (fv - 16) / 40.0 + 2.1 * k) * D.smoothstep(D.prog(fv, 16, 24)) * \
        (1 - D.smoothstep(D.prog(fv, 47, F_CONV0)))
    p = O.lerp(home, out) + Vector((0, 0, hover))
    return p.lerp(O, back)


def split_on(fv):
    return F_SPLIT <= fv < F_SWAP


def bump(f, f0, rise=3.0, dur=14.0):
    t = f - f0
    if t <= 0 or t >= dur:
        return 0.0
    x = t / rise
    return x * math.exp(1 - x) * (1 - D.smoothstep(D.prog(t, dur * 0.6, dur)))


def w_bob(fv):
    return 0.01 * math.sin(2 * math.pi * (fv - F_SWAP) / 60.0) * D.smoothstep(D.prog(fv, F_SWAP, F_SWAP + 10))


def w_pos(fv):
    return O + Vector((0.0, 0.0, w_bob(fv)))


def white_halo_scale_v1(fv):
    r = HALO_R_F1 + (HALO_R - HALO_R_F1) * D.ease_in_out_sine(D.prog(fv, 1, 24))
    if fv < F_FUSE - 4:
        vis = 1 - D.smoothstep(D.prog(fv, F_SPLIT, F_SPLIT + 4))
    else:
        vis = D.spring((fv - (F_FUSE - 4)) / 30.0, 2.5, 8.0)
    breath = 1 + 0.04 * sum(bump(fv, b) for b in F_BREATH)
    return r / HALO_R * vis * breath


def white_halo_emit_v1(fv):
    return HALO_W_EMIT_F1 + (HALO_W_EMIT - HALO_W_EMIT_F1) * D.smoothstep(D.prog(fv, 2, F_SPLIT))


def col_halo_scale(fv):
    if fv < F_SPLIT:
        return 0.0
    pop = min(D.spring((fv - F_SPLIT) / 30.0, 2.5, 8.0), 1.25)
    meet = 1 - 0.5 * D.smoothstep(D.prog(fv, F_FUSE - 6, F_FUSE))
    gone = 1 - D.smoothstep(D.prog(fv, F_FUSE, F_FUSE + 3))
    return pop * meet * gone


def letter_state(i, fv):
    """(z_base, tilt_rad, sz) of letter i at v1 frame fv (before the floor lift). Every letter leans right."""
    tf = math.sqrt(2 * DROP_Z / DROP_G)
    vf = DROP_G * tf
    if fv < LAND[i]:
        tau = (LAND[i] - fv) / 30.0
        z = DROP_Z if tau >= tf else vf * tau - 0.5 * DROP_G * tau * tau
        v = 0.0 if tau >= tf else vf - DROP_G * tau
        sz = 1.0 + 0.06 * (v / vf)
        th = math.radians(TILT_DEG)
    else:
        t = (fv - LAND[i]) / 30.0
        env = math.exp(-6 * t)
        osc = math.cos(2 * math.pi * 2.5 * t)
        z = 0.0
        sz = 1.0 - SQUASH * env * osc
        th = math.radians(TILT_DEG) * env * osc
    if F_FUSE <= fv <= F_FUSE + 8:
        sz *= 1.0 - FUSE_PULSE * math.sin(math.pi * D.prog(fv, F_FUSE, F_FUSE + 8))
    return z, th, sz


# ----------------------------------------------------------------------------------------------------------
# v2 pull-back camera (f1 -> f84), then v1's end framing + push
# ----------------------------------------------------------------------------------------------------------
C_TILE = Vector((0.0, SCREEN_Y, ZC))
D0 = 2.0 * HEX_R * FPX / CENTRE_RES[0]          # image hexagon exactly 2544 px wide at f1
D_END = (CAM_END - C_TILE).length
EL_END = math.atan2(CAM_END.z - C_TILE.z, -(CAM_END.y - C_TILE.y))
L_T = (TGT_END - CAM_END).length
BETA_END = math.atan2(TGT_END.z - CAM_END.z, TGT_END.y - CAM_END.y)
Y_END = 540.0 - FPX * math.tan(math.atan2(C_TILE.z - CAM_END.z, C_TILE.y - CAM_END.y) - BETA_END)


def I23(t):
    t = D.clamp01(t)
    return 1 - (1 - t) ** 4 - 4 * t * (1 - t) ** 3


def e_clock(f):
    """Log-distance progress 0 -> 1: zoom-out (Beta(2,3) speed, ease-in from rest) + crane-down + settle overshoot."""
    return (E_A * I23(D.prog(f, 1, E_FA)) + (1 - E_A + E_C) * D.smootherstep(D.prog(f, *E_FB))
            - E_C * D.smootherstep(D.prog(f, *E_FC)))


def s_clock(f):
    return D.smootherstep(D.prog(f, *S_T))


def pose(f):
    """(camera position, look-at target). f >= 84: exactly v1's end framing with its 1 % push."""
    if f >= F_REST:
        return (CAM_END + Vector((0.0, PUSH_Y * D.ease_in_out_sine(D.prog(f - OFF, 24, 120)), 0.0)),
                TGT_END.copy())
    d = D0 * (D_END / D0) ** e_clock(f)
    s = s_clock(f)
    el = EL_END * s
    P = C_TILE + d * Vector((0.0, -math.cos(el), math.sin(el)))
    y_t = 540.0 + (Y_END - 540.0) * s                       # centre tile screen y: centre -> final, monotonic
    eps = math.atan2(C_TILE.z - P.z, C_TILE.y - P.y)
    beta = eps - math.atan((540.0 - y_t) / FPX)
    return P, P + L_T * Vector((0.0, math.cos(beta), math.sin(beta)))


def focus_loc(f):
    if f >= F_REST:
        return TGT_END.copy()
    return C_TILE.lerp(TGT_END, D.ease_in_out_sine(D.prog(f, *F_FOC)))


def shutter(f):
    """f1 is the match frame (S04 f180 is static): shutter closed, so the move that starts after f1 cannot blur it
    (linear keys f1 -> f2 would put ~0.13 % of zoom, 1.3 px at the frame edge, inside a 0.5 shutter)."""
    if f <= 1:
        return 1e-4
    return shutter_v1(f - OFF) if f > OFF else 0.5


def project_np(pts, P, T, W=1920, H=1080):
    P = np.array(P[:]); T = np.array(T[:])
    fw = (T - P) / np.linalg.norm(T - P)
    r = np.cross(fw, [0.0, 0.0, 1.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, fw)
    d = np.asarray(pts, float) - P
    zf = d @ fw
    k = FPX * W / 1920.0
    return np.stack([W / 2 + k * (d @ r) / zf, H / 2 - k * (d @ u) / zf], -1)


# ----------------------------------------------------------------------------------------------------------
# Key orb birth (v2 f42-61): swells out of the girl's white dress, POP on f46, glides to O, arrives at rest on f61
# ----------------------------------------------------------------------------------------------------------
P_BIRTH = Vector((GIRL[0] * HEX_R, SCREEN_Y, ZC + GIRL[1] * HEX_R))
P_POP = P_BIRTH + Vector((0.0, -0.012, 0.0))
Q_ARC = Vector((0.5 * (P_POP.x + O.x), O.y + 0.18, P_POP.z - 0.30))   # gentle arc: out of the painting, then down


def orb_glide(f):
    u = D.smoothstep(D.prog(f, F_BORN, F_ARRIVE))
    a, b = P_POP.lerp(Q_ARC, u), Q_ARC.lerp(O, u)
    return a.lerp(b, u)


def orb_pos(f):
    if f >= F_ARRIVE:
        return w_pos(f - OFF)
    if f >= F_BORN:
        return orb_glide(f)
    # swell: from 2 cm behind the screen surface to the pop point (the cap grows out of the dress)
    s = D.smoothstep(D.prog(f, F_SWELL0, F_BORN))
    return P_BIRTH + Vector((0.0, 0.02 - 0.032 * s, 0.0))


def orb_scale(f):
    """White halo scale (x HALO_R): cap swells to 0.4 over f42-46, POPs (2.5 Hz / 8) toward v1's f1 size 1.2 and is
    blended onto it over f56-61; v1's schedule from f61."""
    if f >= F_ARRIVE:
        return white_halo_scale_v1(f - OFF)
    if f < F_SWELL0:
        return 0.0
    if f < F_BORN:
        return 0.40 * D.smoothstep(D.prog(f, F_SWELL0, F_BORN))
    sp = D.spring((f - F_BORN) / 30.0, 2.5, 8.0)
    sp += (1.0 - sp) * D.smoothstep(D.prog(f, 56, F_ARRIVE))
    return 0.40 + (HALO_R_F1 / HALO_R - 0.40) * sp


def orb_emit(f):
    if f >= F_ARRIVE:
        return white_halo_emit_v1(f - OFF)
    return 0.95 + (HALO_W_EMIT_F1 - 0.95) * D.smoothstep(D.prog(f, F_BORN, F_BORN + 7))


def w_energy(f):
    if f >= F_ARRIVE:
        return 0.0 if split_on(f - OFF) else W_POWER
    return W_POWER * D.smoothstep(D.prog(f, *F_LAMP))


# ----------------------------------------------------------------------------------------------------------
# Inflated candy letters (v1 code, unchanged)
# ----------------------------------------------------------------------------------------------------------
def glyph_loops(ch, size):
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
    loops = [_resample(l, h) for l in loops]
    A = np.vstack(loops)
    B = np.vstack([np.roll(l, -1, 0) for l in loops])

    def ins(P):
        return _winding_inside(P, A, B)
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
    for (o, n) in starts:
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
        if len(q) > 1 and k > 2:
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
    flip = np.cross(b - a, c - a)[:, 1] > 0
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
    idx = np.digitize(P[:, 1], edges) - 1
    lo = np.full(len(edges) - 1, np.nan)
    hi = np.full(len(edges) - 1, np.nan)
    for b in np.unique(idx):
        if 0 <= b < len(lo):
            m = idx == b
            lo[b], hi[b] = P[m, 0].min(), P[m, 0].max()
    return lo, hi


def build_title():
    uniq = sorted(set(WORD))
    unit = {c: glyph_loops(c, 1.0) for c in uniq}
    edges = np.arange(-0.4, 1.4, 0.01)
    ext = {}
    for c, loops in unit.items():
        P = np.vstack([_resample(l, 0.002) for l in loops])
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
        me.materials.append(None)
        meshes[c] = (me, base, bpts - np.array([base.x, base.z]))
    letters = []
    for i, c in enumerate(WORD):
        me, base, bpts = meshes[c]
        ob = D.link(bpy.data.objects.new(f"Letter_{i}_{c}", me))
        ob.location = (xs[i] + shift + base.x, TITLE_Y, -0.001)
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = D.mat_candy(COLOURS[i], rough=LET_ROUGH, name=f"candy_letter_{i}")
        letters.append((ob, bpts))
    print(f"[s05f] title glyph size {size:.3f} m/em, gaps {LET_GAP} m, max inscribed half-stroke {stroke}")
    return letters, size


# ----------------------------------------------------------------------------------------------------------
# Hex tile library (renders/hex_tiles/manifest.json; development placeholders until it exists)
# ----------------------------------------------------------------------------------------------------------
CHAPTER_RING1 = {90: "c_s01_night", 30: "c_s01_day", -30: "c_s02_wide", -90: "c_s02_macro", -150: "c_s03_gummy",
                 150: "c_s04_gallery"}
NO_REPEAT = {"c_s01_night"}
HERO_OF = {"blush": "pink", "pink": "pink", "butter": "lemon", "lemon": "lemon", "cream": "lemon", "lilac": "violet",
           "violet": "violet", "lavender": "violet", "sky": "aqua", "aqua": "aqua", "blue": "blue", "mint": "mint",
           "pistachio": "lime", "lime": "lime", "peach": "orange", "orange": "orange", "coral": "coral",
           "gold": "lemon", "ink": "blue"}


def load_library():
    man_path = os.environ.get("S05F_MANIFEST", os.path.join(ROOT, "renders", "hex_tiles", "manifest.json"))
    using = "hex_tiles"
    if not os.path.exists(man_path):
        man_path = os.path.join(WORK, "placeholders", "manifest.json")
        using = "dev_placeholders"
    with open(man_path) as fh:
        man = json.load(fh)
    base = os.path.dirname(man_path)
    tiles = {}
    for t in man.get("tiles", []):
        d = os.path.join(base, t["id"])
        first = os.path.join(d, "h_0001.png")
        if not os.path.exists(first):
            print(f"[s05f] WARNING tile {t['id']} has no frames in {d}; skipped", flush=True)
            continue
        pal = str(t.get("palette") or "lavender").lower()
        key = next((w for w in pal.replace("/", " ").replace("-", " ").replace(",", " ").split() if w in HERO_OF),
                   "lavender")
        tiles[t["id"]] = dict(t, dir=d, first=first, hero=HERO_OF[key])
    centre = dict(man.get("center") or {})
    for k in ("path", "from"):
        if centre.get(k) and not os.path.isabs(centre[k]):
            centre[k] = os.path.join(ROOT, centre[k])
    if os.environ.get("S05F_CENTER"):
        centre = {"id": "c_painting", "path": os.environ["S05F_CENTER"], "source": "calibration"}
    if not centre.get("path") or not os.path.exists(centre["path"]):
        centre = {"id": "c_painting", "path": os.path.join(WORK, "placeholders", "c_painting", "still.png"),
                  "source": "placeholder"}
    return dict(path=man_path, using=using, manifest=man, tiles=tiles, centre=centre)


# ----------------------------------------------------------------------------------------------------------
# Honeycomb geometry
# ----------------------------------------------------------------------------------------------------------
def lattice():
    cells = []
    for c in range(-NCOL, NCOL + 1):
        x = 1.5 * RC * c
        for j in range(-1, NROW + 1):
            if c % 2 and j < 0:
                continue
            z = ZC + j * PITCH - (0.5 * PITCH if c % 2 else 0.0)
            cells.append(dict(c=c, j=j, x=x, z=z))
    cen = np.array([[d["x"], d["z"]] for d in cells])
    i0 = [i for i, d in enumerate(cells) if d["c"] == 0 and d["j"] == 0][0]
    ring = {i0: 0}
    front = [i0]
    nbr = {}
    for i in range(len(cells)):
        dd = np.linalg.norm(cen - cen[i], axis=1)
        nbr[i] = [int(k) for k in np.where((dd > 1e-6) & (dd < PITCH * 1.05))[0]]
    while front:
        nxt = []
        for i in front:
            for k in nbr[i]:
                if k not in ring:
                    ring[k] = ring[i] + 1
                    nxt.append(k)
        front = nxt
    for i, d in enumerate(cells):
        d["ring"] = ring.get(i, 99)
        d["nbr"] = nbr[i]
        d["ang"] = round(math.degrees(math.atan2(d["z"] - ZC, d["x"])))
    return cells, i0


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


def bezel_mesh(name="BezelMesh", n_arc=10, n_prof=22, m=2.6):
    """Candy bezel ring: a pillowy superellipse profile swept along a filleted hexagon. Local frame: (x, z) in the wall
    plane, -y toward the lens, origin = cell centre on the slab face (so pops scale about the cell centre)."""
    a_img = HEX_R * math.cos(math.radians(30))
    a_in, a_out = K_IN * a_img, K_OUT * a_img
    half = (a_out - a_in) / 2
    a_c = (a_in + a_out) / 2
    rho = half + 0.004
    Rv = a_c / math.cos(math.radians(30))
    cc = Rv - rho / math.sin(math.radians(60))
    path, nrm = [], []
    for k in range(6):
        ak = math.radians(60 * k)
        cx, cz = cc * math.cos(ak), cc * math.sin(ak)
        for j in range(n_arc + 1):
            ang = ak - math.radians(30) + math.radians(60) * j / n_arc
            nrm.append((math.cos(ang), math.sin(ang)))
            path.append((cx + rho * math.cos(ang), cz + rho * math.sin(ang)))
    prof = []
    for i in range(n_prof + 1):
        t = math.pi * (1 - i / n_prof)
        ct, st = math.cos(t), math.sin(t)
        prof.append((half * math.copysign(abs(ct) ** (2 / m), ct), BEZEL_H * abs(st) ** (2 / m)))
    bm = bmesh.new()
    vs = [[bm.verts.new((p[0] + u * n[0], -h, p[1] + u * n[1])) for (u, h) in prof] for p, n in zip(path, nrm)]
    N = len(vs)
    for k in range(N):
        a_, b_ = vs[k], vs[(k + 1) % N]
        for i in range(n_prof):
            try:
                bm.faces.new((a_[i], b_[i], b_[i + 1], a_[i + 1]))
            except ValueError:
                pass
    bm.normal_update()
    crest = [f for f in bm.faces if all(abs(v.co.y + BEZEL_H) < 0.004 for v in f.verts)]
    if crest and crest[0].normal.y > 0:
        for f in bm.faces:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    return me


def slab_mesh(name="SlabMesh"):
    """Lavender cell slab: circumradius RC (packs edge to edge), front face at local y 0, back at SLAB_BACK - FRONT."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, z)) for x, z in rounded_hex(RC, 0.012, 6)]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.y += SLAB_BACK_Y - SLAB_FRONT_Y
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = D._mesh_object("SlabProto", bm, None, smooth=False)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.009
    bev.segments = 3
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(50)
    bev.harden_normals = True
    D.apply_modifiers(ob)
    D.set_smooth(ob)
    me = ob.data
    me.name = name
    bpy.data.objects.remove(ob)
    return me


def screen_mesh(name, aspect):
    """Flat hexagon (circumradius K_SCR * HEX_R) facing -y; UVs map the image hexagon (circumradius HEX_R) to the image:
    u = 0.5 + x / (2 HEX_R), v = 0.5 + z / (2 HEX_R aspect)."""
    bm = bmesh.new()
    Rs = K_SCR * HEX_R
    vs = [bm.verts.new((Rs * math.cos(math.radians(60 * k)), 0.0, Rs * math.sin(math.radians(60 * k))))
          for k in range(6)]
    c = bm.verts.new((0.0, 0.0, 0.0))
    for k in range(6):
        bm.faces.new((c, vs[k], vs[(k + 1) % 6]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            x, z = lp.vert.co.x, lp.vert.co.z
            lp[uv].uv = (0.5 + x / (2 * HEX_R), 0.5 + z / (2 * HEX_R * aspect))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


# ----------------------------------------------------------------------------------------------------------
# Screen shading: inverse Khronos PBR Neutral (custom setup #5, tile screen)
# ----------------------------------------------------------------------------------------------------------
PBRN_SC, PBRN_DESAT, PBRN_MAXP = 0.76, 0.15, 0.9975
INV_N = 97
INV_LUT = os.path.join(WORK, "calib", f"inv_view_delta_{INV_N}.npy")
LG_MIN, LG_MAX = -9.0, 10.0


def inv_delta_image():
    """The correction LUT delta(t) = a_exact - a_closed (lg2-allocation units) as a float atlas: INV_N slices along
    blue side by side, red along x, green along y. Built by lib/pbrn_view/delta_lut.py (inverts
    Blender's real view: lg2 [-9, 10] -> pbrNeutral.cube tetrahedral -> sRGB)."""
    if not os.path.exists(INV_LUT):
        sys.path.insert(0, os.path.join(ROOT, "lib", "pbrn_view"))   # pbrn_lut / build_inv_lut / delta_lut (in git)
        import delta_lut  # noqa
        Dl, _ = delta_lut.build_delta(INV_N, "sqrt")
        os.makedirs(os.path.dirname(INV_LUT), exist_ok=True)
        np.save(INV_LUT, Dl.astype(np.float32))
    Dl = np.load(INV_LUT)
    n = Dl.shape[0]
    atl = np.ones((n, n * n, 4), np.float32)              # rows = g (bottom-up), cols = k*n + r
    for k in range(n):
        atl[:, k * n:(k + 1) * n, :3] = Dl[:, :, k].transpose(1, 0, 2)
    img = bpy.data.images.new("InvViewDelta", n * n, n, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(atl.ravel())
    img.update()
    return img, n


def inv_pbrn_group():
    """Raw display sRGB code value t (Non-Color texture) -> scene radiance that Blender's 'Khronos PBR Neutral' view
    (exposure EXPOSURE) shows as t again. Two parts:
    1. the closed-form Khronos inverse (start 0.76, desaturation 0.15, toe 0.04 / 6.25 x^2) on srgb_decode(t);
    2. x 2^(19 delta(t)): a correction LUT (97^3, trilinear, sqrt shaper) that makes it the inverse of Blender's real
       implementation (pbrNeutral.cube 57^3 in lg2 space, tetrahedral), which differs from the closed form by up to
       ~6/255 on saturated colours. Exact in gamut (simulated mean 0.07/255, p99 0.36/255 on real frames); colours
       the view cannot produce (a channel at 255 on a saturated colour) fade toward white, as with any inverse."""
    ng = bpy.data.node_groups.new("InvPBRNeutral", "ShaderNodeTree")
    ng.interface.new_socket("Color", in_out="INPUT", socket_type="NodeSocketColor")
    ng.interface.new_socket("Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, Lk = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    sep = N.new("ShaderNodeSeparateColor")
    Lk.new(gi.outputs[0], sep.inputs[0])

    def M(op, a, b=None, c=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for k, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = float(v)
            else:
                Lk.new(v, n.inputs[k])
        return n.outputs[0]
    tcode = [M("MINIMUM", M("MAXIMUM", sep.outputs[i], 0.0), 1.0) for i in range(3)]
    lin = []
    for t in tcode:                                       # exact sRGB decode
        lo = M("DIVIDE", t, 12.92)
        hi = M("POWER", M("DIVIDE", M("ADD", t, 0.055), 1.055), 2.4)
        lin.append(M("ADD", lo, M("MULTIPLY", M("GREATER_THAN", t, 0.04045), M("SUBTRACT", hi, lo))))
    dd = 1.0 - PBRN_SC
    ch = [M("MINIMUM", M("MAXIMUM", lin[i], 0.0), PBRN_MAXP) for i in range(3)]
    newp = M("MAXIMUM", M("MAXIMUM", ch[0], ch[1]), ch[2])
    mask = M("GREATER_THAN", newp, PBRN_SC)
    peak = M("ADD", M("DIVIDE", dd * dd, M("SUBTRACT", 1.0, newp)), PBRN_SC - dd)
    g = M("SUBTRACT", 1.0, M("DIVIDE", 1.0, M("ADD", M("MULTIPLY", M("SUBTRACT", peak, newp), PBRN_DESAT), 1.0)))
    ratio = M("DIVIDE", peak, M("MAXIMUM", newp, 1e-6))
    one_m_g = M("SUBTRACT", 1.0, g)
    npg = M("MULTIPLY", newp, g)
    xo = []
    for c in ch:
        comp = M("MULTIPLY", M("DIVIDE", M("SUBTRACT", c, npg), one_m_g), ratio)
        xo.append(M("ADD", c, M("MULTIPLY", mask, M("SUBTRACT", comp, c))))
    y = M("MINIMUM", M("MINIMUM", xo[0], xo[1]), xo[2])
    low = M("MULTIPLY", M("SQRT", M("MAXIMUM", y, 0.0)), 0.4)
    high = M("ADD", y, 0.04)
    sel = M("LESS_THAN", y, 0.04)
    xin = M("ADD", high, M("MULTIPLY", sel, M("SUBTRACT", low, high)))
    off = M("SUBTRACT", xin, y)
    # correction LUT lookup (trilinear: two bilinear slice reads, blended along blue)
    img, n = inv_delta_image()
    p = [M("MULTIPLY", M("SQRT", t), float(n - 1)) for t in tcode]
    k0 = M("MINIMUM", M("FLOOR", p[2]), float(n - 2))
    fb = M("SUBTRACT", p[2], k0)
    vv = M("DIVIDE", M("ADD", p[1], 0.5), float(n))
    reads = []
    for dk in (0.0, 1.0):
        uu = M("DIVIDE", M("ADD", M("ADD", M("MULTIPLY", M("ADD", k0, dk), float(n)), p[0]), 0.5), float(n * n))
        cmb = N.new("ShaderNodeCombineXYZ")
        Lk.new(uu, cmb.inputs[0])
        Lk.new(vv, cmb.inputs[1])
        tx = N.new("ShaderNodeTexImage")
        tx.image = img
        tx.interpolation = "Linear"
        tx.extension = "EXTEND"
        Lk.new(cmb.outputs[0], tx.inputs["Vector"])
        reads.append(N.new("ShaderNodeSeparateColor"))
        Lk.new(tx.outputs["Color"], reads[-1].inputs[0])
    k = 2.0 ** (-EXPOSURE)
    comb = N.new("ShaderNodeCombineColor")
    for i in range(3):
        d0, d1 = reads[0].outputs[i], reads[1].outputs[i]
        delta = M("ADD", d0, M("MULTIPLY", fb, M("SUBTRACT", d1, d0)))
        corr = M("POWER", 2.0, M("MULTIPLY", delta, LG_MAX - LG_MIN))
        Lk.new(M("MULTIPLY", M("MULTIPLY", M("ADD", xo[i], off), corr), k), comb.inputs[i])
    Lk.new(comb.outputs[0], go.inputs[0])
    return ng


def screen_ctl_group():
    """Shared animated controls for every screen: gain (true colours 1.0 -> GAIN_END) and coat weight."""
    ng = bpy.data.node_groups.new("ScreenCtl", "ShaderNodeTree")
    ng.interface.new_socket("Gain", in_out="OUTPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Coat", in_out="OUTPUT", socket_type="NodeSocketFloat")
    go = ng.nodes.new("NodeGroupOutput")
    vg = ng.nodes.new("ShaderNodeValue")
    vg.name = "gain"
    vc = ng.nodes.new("ShaderNodeValue")
    vc.name = "coat"
    ng.links.new(vg.outputs[0], go.inputs[0])
    ng.links.new(vc.outputs[0], go.inputs[1])
    return ng


def gain(f):
    return 1.0 + (GAIN_END - 1.0) * D.ease_in_out_sine(D.prog(f, 60, 90))


def coat_w(f):
    return COAT_MAX * D.smoothstep(D.prog(f, 4, 30))


def screen_material(name, image, inv, ctl, seq_offset=None, interpolation="Linear"):
    """Tile screen (custom setup #5). Camera rays: emission = InvPBRNeutral(raw sRGB texel) x gain (+ a thin coat
    from f4). Secondary rays: only short ones (<= ~0.2 m: the cell's own bezel and slab) see K_DIFF of the emission,
    so the screens light their bezels (tactile) but never the cove, floor or letters; longer secondary rays (floor
    coat, letters, the cove's bounce light) see a wall-like lavender BSDF, so the title section below the honeycomb
    looks as in v1 (the 'title unchanged' rule)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tex = N.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = interpolation
    tex.extension = "EXTEND"
    if seq_offset is not None:
        iu = tex.image_user
        iu.frame_duration = N_FRAMES
        iu.frame_start = 1 - int(seq_offset)          # cyclic: finale frame f shows h_((f-1+offset) mod 180 + 1)
        iu.frame_offset = 0
        iu.use_cyclic = True
        iu.use_auto_refresh = True
    grp = N.new("ShaderNodeGroup")
    grp.node_tree = inv
    Lk.new(tex.outputs["Color"], grp.inputs[0])
    cg = N.new("ShaderNodeGroup")
    cg.node_tree = ctl
    lp = N.new("ShaderNodeLightPath")

    def M(op, a, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for k, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = float(v)
            else:
                Lk.new(v, n.inputs[k])
        return n.outputs[0]
    cam = lp.outputs["Is Camera Ray"]
    near = N.new("ShaderNodeMapRange")                # 1 for short secondary rays, 0 beyond NEAR_RAY[1]
    near.interpolation_type = "SMOOTHSTEP"
    Lk.new(lp.outputs["Ray Length"], near.inputs["Value"])
    near.inputs["From Min"].default_value = NEAR_RAY[0]
    near.inputs["From Max"].default_value = NEAR_RAY[1]
    near.inputs["To Min"].default_value = 1.0
    near.inputs["To Max"].default_value = 0.0
    k_ray = M("ADD", cam, M("MULTIPLY", M("SUBTRACT", 1.0, cam), K_DIFF))     # camera 1, secondary K_DIFF
    st = M("MULTIPLY", k_ray, cg.outputs["Gain"])
    em = N.new("ShaderNodeEmission")
    Lk.new(grp.outputs[0], em.inputs["Color"])
    Lk.new(st, em.inputs["Strength"])
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.12
    cw = M("MULTIPLY", lw.outputs["Fresnel"], cg.outputs["Coat"])
    gl = N.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.10
    Lk.new(cw, gl.inputs["Color"])
    add = N.new("ShaderNodeAddShader")
    Lk.new(em.outputs[0], add.inputs[0])
    Lk.new(gl.outputs[0], add.inputs[1])
    wall = N.new("ShaderNodeBsdfPrincipled")          # what far secondary rays see: the cove wall
    for key in ("Base Color", "Roughness", "Coat Weight", "Coat Roughness", "Sheen Weight", "Sheen Roughness",
                "Specular IOR Level"):
        wall.inputs[key].default_value = _cp.inputs[key].default_value
    fac = M("MAXIMUM", cam, near.outputs["Result"])
    mix = N.new("ShaderNodeMixShader")
    Lk.new(fac, mix.inputs["Fac"])
    Lk.new(wall.outputs[0], mix.inputs[1])
    Lk.new(add.outputs[0], mix.inputs[2])
    Lk.new(mix.outputs[0], out.inputs["Surface"])
    m.cycles.emission_sampling = "NONE"
    return m


# ----------------------------------------------------------------------------------------------------------
# Light-marker halo (storyboard custom setup #3) + the bloom AOV
# ----------------------------------------------------------------------------------------------------------
def halo(name, colour, strength, radius, loc):
    """Camera + glossy only, never lights, never blocks. Writes colour x strength to the 'orb_glow' AOV (the only
    input of the bloom), exactly the value v1's Emit pass held for the halos."""
    m = bpy.data.materials.new("halo_" + name)
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission")
    rgb = N.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = D.col(colour)
    val = N.new("ShaderNodeValue")
    val.name = "glow"
    val.outputs[0].default_value = strength
    Lk.new(rgb.outputs[0], em.inputs["Color"])
    Lk.new(val.outputs[0], em.inputs["Strength"])
    Lk.new(em.outputs[0], out.inputs["Surface"])
    vm = N.new("ShaderNodeVectorMath")
    vm.operation = "SCALE"
    Lk.new(rgb.outputs[0], vm.inputs[0])
    Lk.new(val.outputs[0], vm.inputs["Scale"])
    aov = N.new("ShaderNodeOutputAOV")
    aov.aov_name = "orb_glow"
    Lk.new(vm.outputs[0], aov.inputs["Color"])
    m.cycles.emission_sampling = "NONE"
    ob = D.sphere(name, radius, loc, m, segments=64, rings=32)
    ob.visible_camera = True
    ob.visible_glossy = True
    ob.visible_diffuse = False
    ob.visible_transmission = False
    ob.visible_shadow = False
    ob.visible_volume_scatter = False
    return ob, val


def key_spot(name, colour, power):
    ob = D.light("SPOT", name, tuple(O), tuple(KEY_AIM), power, colour, radius=LIGHT_R, spot_deg=KEY_CONE,
                 blend=KEY_BLEND)
    ob.visible_glossy = False
    return ob


# ----------------------------------------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------------------------------------
args = D.parse_args()
LIB = load_library()
_out_dir = os.path.abspath(args.out or os.path.join(ROOT, "renders", args.mode, SHOT))
_final_dir = os.path.abspath(os.path.join(ROOT, "renders", "final", SHOT))
_srcs = {t: v.get("source", "missing") for t, v in LIB["tiles"].items()}
_srcs["c_painting"] = LIB["centre"].get("source", "missing")
_all_final = LIB["using"] == "hex_tiles" and bool(LIB["tiles"]) and all(s == "final" for s in _srcs.values())
print(f"[s05f] tile library: {LIB['using']} ({LIB['path']}), {len(LIB['tiles'])} tiles, centre "
      f"{LIB['centre'].get('source')} {LIB['centre'].get('path')}", flush=True)
if args.mode == "final" and _out_dir == _final_dir and not args.no_render and not _all_final and \
        os.environ.get("S05F_ALLOW_NONFINAL") != "1":
    sys.stderr.write("[s05f] REFUSING the s05_finale final: renders/hex_tiles/manifest.json does not say every tile and "
                     f"the centre are final ({Counter(_srcs.values())}). Run scripts/make_hex_tiles.py "
                     "--require-final after the tile/S04 finals.\n")
    sys.stderr.flush()
    os._exit(4)
if not _all_final:
    print(f"[s05f] WARNING: non-final tile sources in this render: {dict(Counter(_srcs.values()))}", flush=True)

D.reset_scene()
D.setup_cycles(samples=384, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=4, caustics=False,
               clamp_indirect=10, motion_blur=True, shutter=0.5)
D.setup_color(exposure=EXPOSURE)
D.setup_output()
sc = bpy.context.scene
sc.frame_end = N_FRAMES
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
PCT = args.pct or D.MODES[args.mode][0]

# title first (text conversion uses the selection)
letters, glyph_size = ([], 0.0) if os.environ.get("S05F_NOLETTERS") else build_title()

cove_mat = D.mat_clay(COVE_COL, rough=0.7, sss=0.0, sheen=0.1, name="cove_lavender")
_cp = cove_mat.node_tree.nodes["Principled BSDF"]
_cp.inputs["Coat Weight"].default_value = COVE_COAT
_cp.inputs["Coat Roughness"].default_value = 0.22
cove = D.cyclorama("Cove", width=30, depth=20, height=8, radius=1.2, wall_y=WALL_Y, mat=cove_mat)

# ---------------- honeycomb ----------------
CELLS, I0 = lattice()
INV = inv_pbrn_group()
CTL = screen_ctl_group()
D.bake(CTL.nodes["gain"].outputs[0], "default_value", 1, N_FRAMES, gain)
D.bake(CTL.nodes["coat"].outputs[0], "default_value", 1, N_FRAMES, coat_w)

# per-cell visibility over the shot (bezel polygon vs frame), used for offsets and ring entry
_hexu = np.array([[math.cos(math.radians(60 * k)), math.sin(math.radians(60 * k))] for k in range(6)])
_POSES = {f: pose(f) for f in range(1, N_FRAMES + 1)}


def cell_poly(d, R, y):
    return np.stack([d["x"] + R * _hexu[:, 0], np.full(6, y), d["z"] + R * _hexu[:, 1]], 1)


_RECT = np.array([[0.0, 0.0], [1920.0, 0.0], [1920.0, 1080.0], [0.0, 1080.0]])


def poly_rect_overlap(poly):
    """Separating-axis test: convex projected polygon vs the 1920 x 1080 frame."""
    if poly[:, 0].max() < 0 or poly[:, 0].min() > 1920 or poly[:, 1].max() < 0 or poly[:, 1].min() > 1080:
        return False
    n = len(poly)
    for k in range(n):
        e = poly[(k + 1) % n] - poly[k]
        ax = np.array([-e[1], e[0]])
        p1, p2 = poly @ ax, _RECT @ ax
        if p1.max() < p2.min() or p2.max() < p1.min():
            return False
    return True


def rect_inside(poly):
    """All four frame corners inside the convex projected polygon (orientation-agnostic)."""
    n = len(poly)
    sg = []
    for k in range(n):
        a, b = poly[k], poly[(k + 1) % n]
        sg.append((b[0] - a[0]) * (_RECT[:, 1] - a[1]) - (b[1] - a[1]) * (_RECT[:, 0] - a[0]))
    sg = np.array(sg)
    return bool((sg >= 0).all() or (sg <= 0).all())


VIS = np.zeros((len(CELLS), N_FRAMES + 1), bool)
FULL = np.zeros((len(CELLS), N_FRAMES + 1), bool)
for f in range(1, N_FRAMES + 1):
    P, T = _POSES[f]
    for i, d in enumerate(CELLS):
        b = project_np(cell_poly(d, K_OUT * HEX_R, SLAB_FRONT_Y - BEZEL_H), P, T)
        if i == I0:                    # the painting cell's bezel shows once the frame leaves its opening
            inner = project_np(cell_poly(d, K_IN * HEX_R, SCREEN_Y - 0.3 * BEZEL_H), P, T)
            VIS[i, f] = not rect_inside(inner)
        else:
            VIS[i, f] = poly_rect_overlap(b)
        FULL[i, f] = (b[:, 0].min() >= 0) and (b[:, 0].max() <= 1920) and (b[:, 1].min() >= 0) and (b[:, 1].max() <= 1080)

# ring entry -> ripple POP on the first 8th note after entry (8th = 7.5 frames, grid from f1)
RING_ENTRY, RING_POP = {}, {}
for i, d in enumerate(CELLS):
    fr = np.where(VIS[i, 1:])[0]
    if len(fr):
        RING_ENTRY[d["ring"]] = min(RING_ENTRY.get(d["ring"], 999), int(fr[0]) + 1)
for r, fe in sorted(RING_ENTRY.items()):
    n = math.ceil((fe - 1) / 7.5)
    p = 1 + 7.5 * n
    if p <= POP_LAST:
        RING_POP[r] = p

# tile assignment
SRC = {}
TILE_IDS = list(LIB["tiles"].keys())
for i, d in enumerate(CELLS):
    if i == I0:
        continue
    if d["ring"] == 1:
        want = CHAPTER_RING1.get(int(round(d["ang"] / 30.0)) * 30)
        if want in LIB["tiles"]:
            SRC[i] = want
uses = Counter(SRC.values())
order = sorted([i for i in range(len(CELLS)) if i != I0 and i not in SRC],
               key=lambda i: (CELLS[i]["ring"], -CELLS[i]["z"], CELLS[i]["x"]))
for i in order:
    nb_src = {SRC.get(k) for k in CELLS[i]["nbr"]}
    nb_hero = {LIB["tiles"][s]["hero"] for s in nb_src if s in LIB["tiles"]}
    best = None
    for tid in TILE_IDS:
        if tid in nb_src or (tid in NO_REPEAT and uses[tid] > 0):
            continue
        t = LIB["tiles"][tid]
        score = (uses[tid] + (0.5 if t.get("kind") == "chapter" else 0.0), t["hero"] in nb_hero, tid)
        if best is None or score < best[0]:
            best = (score, tid)
    SRC[i] = best[1] if best else TILE_IDS[i % len(TILE_IDS)]
    uses[SRC[i]] += 1


def periodic(tid):
    """True when the tile's 180-frame sequence wraps seamlessly (h_0180 -> h_0001), so any frame offset is safe."""
    lp = LIB["tiles"][tid].get("loop")
    if isinstance(lp, dict):
        per = lp.get("period")
        return bool(lp.get("cyclic")) or (lp.get("mode") == "repeat" and bool(per) and N_FRAMES % int(per) == 0)
    try:
        lp = int(lp)
    except (TypeError, ValueError):
        return False
    return lp > 0 and N_FRAMES % lp == 0


OFFSETS = [0, 90, 45, 135, 23, 113, 68, 158, 11, 101, 56, 146, 34, 124, 79, 169]
OFS = {}
_used_ofs = {}
for i in sorted(SRC, key=lambda i: (CELLS[i]["ring"], -CELLS[i]["z"], CELLS[i]["x"])):
    tid = SRC[i]
    fr = np.where(VIS[i, 1:])[0] + 1
    taken = _used_ofs.setdefault(tid, [])
    choice = None
    for o in OFFSETS:
        if o in taken:
            continue
        if not periodic(tid) and o and len(fr):
            jump = N_FRAMES + 1 - o                    # finale frame where the cyclic read wraps 180 -> 1
            if fr.min() <= jump <= fr.max():
                continue
        choice = o
        break
    OFS[i] = choice if choice is not None else 0
    taken.append(OFS[i])

# images and materials
IMAGES = {}


def seq_image(tid):
    if tid not in IMAGES:
        img = bpy.data.images.load(LIB["tiles"][tid]["first"], check_existing=False)
        img.source = "SEQUENCE"
        img.colorspace_settings.name = "Non-Color"
        img.alpha_mode = "NONE"
        IMAGES[tid] = img
    return IMAGES[tid]


MATS = {}


def _png_size(path):
    with open(path, "rb") as fh:
        hd = fh.read(24)
    return int.from_bytes(hd[16:20], "big"), int.from_bytes(hd[20:24], "big")


CENTRE_PATH = LIB["centre"]["path"]
_cand = [CENTRE_PATH] + ([LIB["centre"]["from"]] if LIB["centre"].get("from") else [])
for _c in _cand:
    if os.path.exists(_c) and _c.lower().endswith(".png") and \
            abs(_png_size(_c)[0] - CENTRE_RES[0] * PCT / 100.0) < 0.5:
        CENTRE_PATH = _c
        break
centre_img = bpy.data.images.load(CENTRE_PATH, check_existing=False)
centre_img.colorspace_settings.name = "Non-Color"
centre_img.alpha_mode = "NONE"
CENTRE_W, CENTRE_H = centre_img.size
CENTRE_TEXEL_PER_PX = CENTRE_W / (CENTRE_RES[0] * PCT / 100.0)
CENTRE_1TO1 = abs(CENTRE_TEXEL_PER_PX - 1.0) < 1e-3
centre_mat = screen_material("screen_c_painting", centre_img, INV, CTL, None,
                             "Closest" if CENTRE_1TO1 else "Linear")
print(f"[s05f] centre still {CENTRE_PATH} {CENTRE_W}x{CENTRE_H}, {CENTRE_TEXEL_PER_PX:.3f} texel/px at f1 "
      f"({'1:1, closest + tight filter at f1' if CENTRE_1TO1 else 'linear'})", flush=True)

bezel_me = bezel_mesh()
slab_me = slab_mesh()
scr_me_tile = screen_mesh("ScreenTile", TILE_RES[1] / TILE_RES[0])
scr_me_centre = screen_mesh("ScreenCentre", CENTRE_H / CENTRE_W)
BEZEL_MATS = {}


def bezel_material(hero, soft):
    key = (hero, soft)
    if key not in BEZEL_MATS:
        BEZEL_MATS[key] = D.mat_candy(srgb_mix(hero, "white", soft), rough=0.25, coat=1.0, coat_rough=0.05,
                                      name=f"bezel_{hero}_{int(soft * 100)}")
    return BEZEL_MATS[key]


slab_rx = bpy.data.collections.new("FillExclude")
slab_rx.objects.link(cove)
TILES = []
for i, d in enumerate(CELLS):
    loc_slab = Vector((d["x"], SLAB_FRONT_Y, d["z"]))
    slab = D.link(bpy.data.objects.new(f"Slab_{i}", slab_me))
    slab.location = loc_slab
    bez = D.link(bpy.data.objects.new(f"Bezel_{i}", bezel_me))
    bez.location = loc_slab
    scr = D.link(bpy.data.objects.new(f"Screen_{i}", scr_me_centre if i == I0 else scr_me_tile))
    scr.location = Vector((d["x"], SCREEN_Y, d["z"]))
    for ob in (slab, bez, scr):
        if not ob.data.materials:
            ob.data.materials.append(None)
        ob.material_slots[0].link = "OBJECT"
    slab.material_slots[0].material = cove_mat
    slab_rx.objects.link(slab)
    slab_rx.objects.link(scr)                         # screens: no Fill (their far-ray BSDF is the wall)
    if i == I0:
        tid, hero, soft, mat = "c_painting", CENTRE_BEZEL, 0.10, centre_mat
    else:
        tid = SRC[i]
        hero, soft = LIB["tiles"][tid]["hero"], BEZEL_SOFT
        key = (tid, OFS[i])
        if key not in MATS:
            MATS[key] = screen_material(f"screen_{tid}_{OFS[i]:03d}", seq_image(tid), INV, CTL, OFS[i])
        mat = MATS[key]
    bez.material_slots[0].material = bezel_material(hero, soft)
    scr.material_slots[0].material = mat
    d.update(tid=tid, offset=OFS.get(i, 0), hero=hero)
    TILES.append((i, slab, bez, scr))
    # ripple POP (bezel only): in-plane scale + a lift toward the lens, POP spring (2.5 Hz, damping 8)
    p = RING_POP.get(d["ring"])
    if p is not None and not MASK:
        h_max = max(math.exp(-8 * t) * math.sin(2 * math.pi * 2.5 * t) for t in np.linspace(0, 0.4, 400))

        def h(f, p=p):
            t = (f - p) / 30.0
            return 0.0 if t <= 0 else math.exp(-8 * t) * math.sin(2 * math.pi * 2.5 * t) / h_max
        f0, f1 = int(math.floor(p)) - 1, min(N_FRAMES, int(math.ceil(p)) + 24)
        D.bake(bez, "scale", f0, f1, lambda f, h=h: (1 + POP_SCALE * h(f), 1 + 1.5 * POP_SCALE * h(f),
                                                     1 + POP_SCALE * h(f)))
        D.bake(bez, "location", f0, f1, lambda f, h=h, L=loc_slab: (L.x, L.y - POP_LIFT * h(f), L.z))
print(f"[s05f] honeycomb: {len(CELLS)} cells, pitch {PITCH:.4f} m, {len(MATS) + 1} screen materials, "
      f"{len(IMAGES)} sequences, ring entry {RING_ENTRY}, pops {RING_POP}", flush=True)

# ---------------- story lights + halos ----------------
NO_ORBS = os.environ.get("S05F_NOORBS") == "1"
W = key_spot("OrbW", "white", 0.0)
HW, HW_VAL = halo("HaloW", "white", HALO_W_EMIT_F1, HALO_R, tuple(P_BIRTH))
CL, CH = [], []
for k, (cname, pos, frac) in enumerate(SPLIT):
    CL.append(key_spot("Orb_" + cname, cname, 0.0))
    CH.append(halo("Halo_" + cname, cname, HALO_C_EMIT, HALO_R - 0.0004 * k, tuple(O))[0])
fill = D.light("AREA", "Fill", (0, -6.0, 4.0), (0, 0.5, 0.8), power=FILL_POWER, color="white", size=6.0)
wash = D.light("AREA", "WallWash", (0.0, 1.7, 4.7), (0.0, 3.0, 1.9), power=WASH_POWER, color="white", size=10.0,
               size_y=1.2)
fill.light_linking.receiver_collection = slab_rx           # fill: letters + bezels only (v1: letters + band)
for co in slab_rx.collection_objects:
    co.light_linking.link_state = "EXCLUDE"
rig = D.world_hdri(D.HDRI["studio_small_09"], 0.3, camera_bg="lavender")

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


def shine_x(fv):
    return -SHINE_X0 + 2 * SHINE_X0 * D.ease_in_out_sine(D.prog(fv, *F_SHINE))


def shine_power(fv):
    return SHINE_POWER * math.sin(math.pi * D.prog(fv, *F_SHINE)) ** 2


D.bake(shine, "location", 1, N_FRAMES, lambda f: (shine_x(f - OFF), -3.0, 1.3))
D.bake(shine.data, "energy", 1, N_FRAMES, lambda f: shine_power(f - OFF))

D.bake(W, "location", 1, N_FRAMES, lambda f: tuple(orb_pos(f)))
D.bake(W.data, "energy", 1, N_FRAMES, lambda f: 0.0 if NO_ORBS else w_energy(f))
D.bake(HW, "location", 1, N_FRAMES, lambda f: tuple(orb_pos(f)))
D.bake(HW, "scale", 1, N_FRAMES, lambda f: (max(0.0 if NO_ORBS else orb_scale(f), 1e-4),) * 3)
D.bake(HW_VAL.outputs[0], "default_value", 1, N_FRAMES, orb_emit)
D.hide_range(HW, visible_from=F_SWELL0)
for k, (cname, pos, frac) in enumerate(SPLIT):
    D.bake(CL[k], "location", 1, N_FRAMES, lambda f, k=k: tuple(split_pos(k, f - OFF)))
    D.bake(CH[k], "location", 1, N_FRAMES, lambda f, k=k: tuple(split_pos(k, f - OFF)))
    D.bake(CL[k].data, "energy", 1, N_FRAMES,
           lambda f, fr=frac: W_POWER * fr if (split_on(f - OFF) and not NO_ORBS) else 0.0)
    D.bake(CH[k], "scale", 1, N_FRAMES, lambda f: (max(0.0 if NO_ORBS else col_halo_scale(f - OFF), 1e-4),) * 3)
    D.hide_range(CH[k], visible_from=OFF + F_SPLIT - 1)
D.bake(sc.render, "motion_blur_shutter", 1, N_FRAMES, shutter)


# letters: v1's fall / BOING / tilt / floor lift on v1 frames, hidden until their fall starts
def letter_xform(i, f):
    ob, bpts = letters[i]
    z, th, sz = letter_state(i, f - OFF)
    sxy = 1.0 / math.sqrt(sz)
    zz = -np.sin(th) * (sxy * bpts[:, 0]) + np.cos(th) * (sz * bpts[:, 1])
    lift = max(0.0, -float(zz.min()))
    return z + lift, th, sxy, sz


LET_VISIBLE_FROM = [lf - 19 for lf in LAND_V2]
for i, (ob, bpts) in enumerate(letters):
    x0, y0, z0 = ob.location
    D.bake(ob, "location", 1, N_FRAMES, lambda f, i=i, x0=x0, y0=y0, z0=z0: (x0, y0, z0 + letter_xform(i, f)[0]))
    D.bake(ob, "rotation_euler", 1, N_FRAMES, lambda f, i=i: (0.0, letter_xform(i, f)[1], 0.0))
    D.bake(ob, "scale", 1, N_FRAMES, lambda f, i=i: (letter_xform(i, f)[2], letter_xform(i, f)[2],
                                                      letter_xform(i, f)[3]))
    D.hide_range(ob, visible_from=LET_VISIBLE_FROM[i])

# camera
focus = D.empty("Focus", tuple(C_TILE))
cam, tgt = D.camera("Cam", tuple(pose(1)[0]), tuple(pose(1)[1]), lens=LENS, fstop=FSTOP, focus=focus, sensor=SENSOR)
D.bake(cam, "location", 1, N_FRAMES, lambda f: tuple(_POSES[f][0]))
D.bake(tgt, "location", 1, N_FRAMES, lambda f: tuple(_POSES[f][1]))
D.bake(focus, "location", 1, N_FRAMES, lambda f: tuple(focus_loc(f)))
if CENTRE_1TO1:
    D.bake(sc.cycles, "filter_width", 1, 5, lambda f: [0.01, 0.4, 0.9, 1.3, 1.5][f - 1])


# ----------------------------------------------------------------------------------------------------------
# QA printouts: honeycomb stats per frame, lockup, letters, orb speeds
# ----------------------------------------------------------------------------------------------------------
GX, GY = np.meshgrid((np.arange(192) + 0.5) * 10.0, (np.arange(108) + 0.5) * 10.0)
GPTS = np.stack([GX.ravel(), GY.ravel()], 1)


def inside_convex(poly, pts):
    n = len(poly)
    s = None
    for k in range(n):
        a, b = poly[k], poly[(k + 1) % n]
        cr = (b[0] - a[0]) * (pts[:, 1] - a[1]) - (b[1] - a[1]) * (pts[:, 0] - a[0])
        s = (cr >= 0) if s is None else (s & (cr >= 0))
    return s


def honeycomb_stats(f):
    P, T = _POSES[f]
    cov_c = np.zeros(len(GPTS), bool)
    cov_s = np.zeros(len(GPTS), bool)
    full_c = full_s = 0
    lowest_s = lowest_b = -1e9
    for i, d in enumerate(CELLS):
        if not VIS[i, f] and i != I0:
            continue
        b = project_np(cell_poly(d, K_OUT * HEX_R, SLAB_FRONT_Y - BEZEL_H), P, T)
        s = project_np(cell_poly(d, K_IN * HEX_R, SCREEN_Y), P, T)
        for poly in (b, s):
            e1, e2 = poly[1] - poly[0], poly[2] - poly[1]
            if e1[0] * e2[1] - e1[1] * e2[0] < 0:
                poly[:] = poly[::-1].copy()
        cov_c |= inside_convex(b, GPTS)
        cov_s |= inside_convex(s, GPTS)
        full_c += FULL[i, f]
        full_s += bool((s[:, 0].min() >= 0) and (s[:, 0].max() <= 1920) and (s[:, 1].min() >= 0) and
                       (s[:, 1].max() <= 1080))
        lowest_s = max(lowest_s, s[:, 1].max())
        lowest_b = max(lowest_b, b[:, 1].max())
    c = project_np([tuple(C_TILE)], P, T)[0]
    cb = project_np(cell_poly(CELLS[I0], K_OUT * HEX_R, SLAB_FRONT_Y - BEZEL_H), P, T)
    return dict(full_cells=int(full_c), full_screens=int(full_s), cover_cells=round(float(cov_c.mean()), 4),
                cover_screens=round(float(cov_s.mean()), 4), centre_px=[round(float(c[0]), 1), round(float(c[1]), 1)],
                centre_bezel_top_px=round(float(cb[:, 1].min()), 1),
                centre_bezel_full=bool(FULL[I0, f]),
                tile_w_px=round(float(2 * K_IN * HEX_R / (_POSES[f][0] - C_TILE).length * FPX), 1),
                lowest_screen_px=round(float(lowest_s), 1), lowest_bezel_px=round(float(lowest_b), 1))


HSTATS = {f: honeycomb_stats(f) for f in range(1, N_FRAMES + 1)}
many = [f for f in range(30, 70) if HSTATS[f]["full_cells"] >= 15 and HSTATS[f]["cover_cells"] >= 0.70]
print(f"[s05f] many-scenes frames (>=15 full cells, cells >= 70 %): {many[:1]}..{many[-1:]} ({len(many)} frames)",
      flush=True)
for f in (1, 10, 20, 30, 40, 46, 50, 61, 70, 84, 121, 180):
    print(f"[s05f] f{f:3d} {HSTATS[f]}", flush=True)


def ztop_title(f):
    P, T = _POSES[f]
    fw = (T - P).normalized()
    beta = math.atan2(fw.z, fw.y)
    return P.z + (TITLE_Y - P.y) * math.tan(beta + math.atan(540.0 / FPX))


LETTER_QA = []
for i in range(len(LAND)):
    fs = LET_VISIBLE_FROM[i]
    enter = None
    for f in range(fs, LAND_V2[i] + 1):
        if letter_state(i, f - OFF)[0] < ztop_title(f):
            enter = f
            break
    q = dict(letter=f"{i}{WORD[i]}", visible_from=fs, z_top_at_visible=round(ztop_title(fs), 3),
             drop_z=DROP_Z, enters_frame=enter, lands=LAND_V2[i])
    if letters:                                      # bounding box at the frame it becomes visible: must be off-frame
        ob = letters[i][0]
        x0, y0, z0 = ob.location
        zb, th, sxy, sz = letter_xform(i, fs)
        bb = np.array([c[:] for c in ob.bound_box]) * np.array([sxy, sxy, sz])
        pts = bb + np.array([x0, y0, z0 + zb])
        uv = project_np(pts, *_POSES[fs])
        P_, T_ = _POSES[fs]
        q["bbox_px_at_visible"] = [round(float(uv[:, 0].min())), round(float(uv[:, 0].max())),
                                   round(float(uv[:, 1].min())), round(float(uv[:, 1].max()))]
        q["off_frame_at_visible"] = bool(uv[:, 1].max() < 0 or uv[:, 0].max() < 0 or uv[:, 0].min() > 1920)
    LETTER_QA.append(q)
print("[s05f] letters", LETTER_QA, flush=True)
ORB_SPEED = {f: round((orb_pos(f + 1) - orb_pos(f)).length * 100, 2) for f in range(F_SWELL0, 75)}
print("[s05f] orb speed cm/f", ORB_SPEED, flush=True)


def project(points, f):
    from bpy_extras.object_utils import world_to_camera_view
    sc.frame_set(f)
    return np.array([world_to_camera_view(sc, cam, Vector(p))[:2] for p in points])


def lockup_report():
    rep = {"f1_cam_dist_to_screen": round((pose(1)[0] - C_TILE).length, 5), "d0": round(D0, 5),
           "f1_image_hex_px": round(2 * HEX_R / D0 * FPX, 2)}
    for f in (121, 150, 180):
        pts = []
        for ob, _ in letters:
            sc.frame_set(f)
            mw = ob.matrix_world
            vs = ob.data.vertices
            step = max(1, len(vs) // 3000)
            pts += [mw @ vs[j].co for j in range(0, len(vs), step)]
        uv = project(pts, f) if pts else np.zeros((1, 2))
        orbs = [tuple(split_pos(k, 50)) for k in range(3)] + [tuple(O)]
        ov = project(orbs, f)
        rep[f"f{f}"] = {
            "title_w_pct": round(100 * (uv[:, 0].max() - uv[:, 0].min()), 2),
            "title_left_right_px": [round(1920 * uv[:, 0].min()), round(1920 * uv[:, 0].max())],
            "baseline_from_top_pct": round(100 * (1 - uv[:, 1].min()), 2),
            "title_top_px": round(1080 * (1 - uv[:, 1].max()), 1),
            "orbs_px": [[round(1920 * v[0]), round(1080 * (1 - v[1]))] for v in ov],
            "honeycomb": HSTATS[f],
        }
    return rep


sc.frame_set(1)
LOCKUP = lockup_report() if letters else {}
print("[s05f] LOCKUP", json.dumps(LOCKUP), flush=True)

# ----------------------------------------------------------------------------------------------------------
# Meta (written at build time, every mode, before rendering)
# ----------------------------------------------------------------------------------------------------------
events = {"match_cut": 1, "pullback_start": 1}
events.update({f"ring{r}_pop": p for r, p in RING_POP.items()})
events.update({"many_scenes": [many[0], many[-1]] if many else None, "orb_swell": F_SWELL0, "orb_born": F_BORN,
               "tilt": list(S_T), "orb_at_O": F_ARRIVE, "split": F_SPLIT + OFF, "settle": F_REST})
for i, f in enumerate(LAND_V2):
    events[f"land_{i}_{WORD[i]}"] = f
events.update({"converge_start": F_CONV0 + OFF, "fuse": F_FUSE + OFF, "swap_to_white": F_SWAP + OFF,
               "breath_1": F_BREATH[0] + OFF, "shine": (F_SHINE[0] + F_SHINE[1]) // 2 + OFF,
               "breath_2": F_BREATH[1] + OFF, "end": N_FRAMES})
per_frame = {}
for f in range(1, N_FRAMES + 1):
    P, T = _POSES[f]
    per_frame[f] = dict(e=round(e_clock(f), 5), s=round(s_clock(f), 5), cam=[round(v, 4) for v in P],
                        tgt=[round(v, 4) for v in T], dist_to_tile=round((P - C_TILE).length, 4),
                        gain=round(gain(f), 4), **HSTATS[f])
meta = {"id": SHOT, "frames": N_FRAMES, "start_frame_in_film": START_IN_FILM, "events": events,
        "honeycomb": {"hex_r": HEX_R, "k_in": K_IN, "k_scr": K_SCR, "k_out": K_OUT, "grout": GROUT, "pitch": PITCH,
                      "centre": list(C_TILE), "cells": len(CELLS), "ring_entry": RING_ENTRY, "ring_pop": RING_POP,
                      "assignment": [{k: d[k] for k in ("c", "j", "ring", "tid", "offset", "hero")} for d in CELLS]},
        "library": {"manifest": LIB["path"], "using": LIB["using"], "sources": _srcs, "all_final": _all_final},
        "centre_still": {"path": CENTRE_PATH, "manifest_path": LIB["centre"]["path"], "res": [CENTRE_W, CENTRE_H],
                         "texel_per_px_f1": CENTRE_TEXEL_PER_PX},
        "camera": {"d0": D0, "d_end": D_END, "y_end_px": Y_END, "clocks": {"E_A": E_A, "E_FA": E_FA, "E_FB": E_FB,
                                                                            "E_C": E_C, "E_FC": E_FC, "S_T": S_T}},
        "orb": {"birth": list(P_BIRTH), "speed_cm_per_f": ORB_SPEED, "lamp": list(F_LAMP)},
        "letters": LETTER_QA, "lockup": LOCKUP, "per_frame": per_frame}
os.makedirs(os.path.join(ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)

# ----------------------------------------------------------------------------------------------------------
# Orb glow (lead G1): S01's compositor bloom, identical parameters, driven only by the halos' AOV
# ----------------------------------------------------------------------------------------------------------
vl = sc.view_layers[0]
_aov = vl.aovs.add()
_aov.name = "orb_glow"
_aov.type = "COLOR"
if GLOW > 0 and not MASK:
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
    ct.links.new(rl.outputs["orb_glow"], gl.inputs["Image"])
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
    cd.ortho_scale = 14.0
    dc = D.link(bpy.data.objects.new("DebugCam", cd))
    if DEBUG_CAM == "top":
        dc.location = (0, -3.5, 16)
        dc.rotation_euler = (0, 0, 0)
    else:
        dc.location = (14, -3.5, 1.8)
        dc.rotation_euler = (math.radians(90), 0, math.radians(90))
        cd.ortho_scale = 15.0
    sc.camera = dc

if MASK:
    blk = D.mat_emission("#000000", 0.0, name="mask_black")
    red = D.mat_emission((1, 0, 0), 1.0, name="mask_red")
    grn = D.mat_emission((0, 1, 0), 1.0, name="mask_green")
    blu = D.mat_emission((0, 0, 1), 1.0, name="mask_blue")
    for ob in sc.objects:
        if ob.type != "MESH":
            continue
        m = red if ob.name.startswith("Letter_") else (grn if ob.name.startswith("Screen_") else
                                                        (blu if ob.name.startswith("Bezel_") else blk))
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

D.finish(args, final_samples=int(env_f("S05F_SPP", 384)), final_threshold=env_f("S05F_THR", 0.02), frame_end=N_FRAMES,
         shot_name=SHOT)
