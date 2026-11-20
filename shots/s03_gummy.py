"""S03 · s03_gummy — "0.2x" (capability C3: animated, deforming geometry with frame-to-frame continuity).

What the shot proves
--------------------
The camera is locked f16-170 (bit-identical keys), so the only legitimate change between frames is animated geometry
and the light transport it drives.  A lime absorption-glass Stanford bunny (bunny-aligned 3x3x4 B-spline lattice,
shape keys squash / stretch / lean_x / lean_y / ear_flop, all closed-form in the time remap tau(f)) drops in,
squashes in 0.2x slow motion (f31-85) with lagging ears, hops, lands again (f96) and is bonked (f106) by a rolling
chrome ball with a pink belt (quaternion accumulation, no slip) that rebounds, rocks back and settles (f151).  Four
transport paths agree on every frame: the stripe wall refracted through the body, reflections (crisp glossy cream
floor, mint-rimmed wall mirror aimed at the gummy, the rolling chrome ball), the contact shadows and the transmitted
lime light (glow + lime caustic on the floor).  In: circle match from S02 (ball 1536 px wide, centred; blush fourth
wall in its centre; f/8 like S02's end).  Out: 55-degree whip right in 10 f (ease_in_cubic, 16.5 deg/f at the cut,
shutter 0.5 -> 1.0 over f171-174).

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/s03_gummy.py -- --mode draft
Final: final_samples / threshold below (see cost note).  Meta: renders/meta/s03_gummy.json (tau_s, rate).
Debug/test hooks (env, all default off): S03_CAM=top|side|front, S03_PATH=1 (ball-path markers), S03_REPORT=1
(geometry report, no render), S03_CHECK=1 (per-frame ball/gummy clearance + screen-gap sweep), S03_MATTE=1
(+S03_MATTE_NOMB=1) (ball-only white matte for the 1536 px measurement), S03_SEED (noise-variance QA only), plus
look-dev overrides (S03_KEY*, S03_FLAG*, S03_GLOW*, S03_FILLK, S03_DENS, ...).  Finals must run with none of them set.

Round 2 changelog (lead notes r2 + critic review; hit frames, tau(f), transitions, colour pipeline unchanged)
-------------------------------------------------------------------------------------------------------------
Lead notes
* L1 glow: gummy material = candy_glass (G5, copied from S02): surface tint colour^0.5 so the double interface lands
  on the colour, not its square; colour pre-compensated to #A0E61D (the blush stripes behind it push plain lime to
  H~60 yellow); absorption = same colour (mint mix removed: it read dark emerald), density 3.5 -> 1.6; roughness
  0.08 -> 0.10.  Plus a light-linked glow: AREA disk 1.2 m, 150 W, #F0FFF2, top-back of the gummy, receiver
  collection = the gummy only, so it lights the jelly from behind (body glow + lime caustic on the floor at its
  feet) without touching the floor/wall/mirror reflections.  Final f38/f106: gummy median H73/H67, V0.74/0.73
  (r1 V0.55/0.62), dark-brown (H<55, V<0.6) 0.7/1.2% (r1 8.5%), V<0.45 0% (r1 11.6%); mirror image V0.76-0.78.
* L2 squash: max-squash height 0.63 (fallback A; r1 0.55) by re-keying the lattice, not clamping (no plateau);
  rings = 1 + 0.727*(r1 excess) -> volume 0.9996-1.0 of rest (REPORT).
* L3 shimmer: final strip f31-42 at 320 spp: gummy-interior seed0/seed1 noise 1.71/255 mean, but consecutive frames
  at the squash turning point (f38->39, near-zero motion) differ by only 1.27/255 incl. real motion -> the noise
  stays coherent frame to frame; static stripes 0.2-0.4/255.  Not visible; samples left at 320 (cost cap).
* L4 floor: lower third falls off (overhead key + cutter flag, cream albedo x0.85); reflections kept crisp.
Critic (major)
* Light: key moved over the set (-2.5, 0, 4.5), 2.0 m (r1 3.2 m front-left): the front floor is now farther and more
  oblique than the action, shadows are shorter and grounded; a black horizontal cutter (5 x 2.1 m at z 2.4, shadow +
  diffuse rays only) shades just the front floor strip.  Fill x0.7, tinted #DCD6FF (lavender shadows, G2).  Key
  spread stays 180: Cycles keeps the power constant when spread narrows, so 45 deg concentrated it ~4x and washed
  the coral wall out (tested 120-420 W).  Contact shadow under the block stack 21%, beside the gummy's foot 7.5%.
* Gummy colour: see L1.  Gummy moved (-0.15,0.40) -> (-0.32,0.42): fully in front of the stripes (no coral seen
  through it, no tangent with the stripe/coral corner); mirror aim and contact solve re-derive.
* Surface: 12 vertex-averaging passes -> Taubin smoothing (numpy umbrella operator, lambda 0.6 / mu -0.62, 100 pairs)
  + exact volume restore: the scan crinkle is gone (bmesh smooth_laplacian_vert is a no-op on this scan).
* Dead tail: bonk decay 3.5 -> 1.4 /s, 2.2 -> 2.0 Hz (one swing per beat), tapered to exact rest by f165 (hold
  f166-170 kept); accents on the beats: f121 ear-flop pulse 0.4, f136 POP after-squash 0.12, f151 the ball peaks
  and rocks back 2 cm by f161 (SETTLE) instead of the exponential creep.  Mean consecutive |d| per beat window
  f121-135 / f136-150 / f151-165 = 1.27 / 1.07 / 0.48 (r1 0.66 / 0.30 / 0.16).
* Bonk visibility: lane shifted +0.32 m in depth (surveyed in REPORT) so the contact sits on the gummy's screen-left
  silhouette (normal vs view cos 0.15); screen gap f103-106 = 26 / 12 / 6 / 3 px (r1 overlapped from f100).  Start
  re-derived for 0.5 m/s.  Local dent: Hook on a smooth-falloff vertex group (r 0.12 m), 3 cm along the contact
  normal on a POP impulse f106-112.  Ball rebounds back-left and parks ~130 px clear of the paws.
Critic (minor) applied
* Pull-out e(p) = 1-(1-p)^1.7 + 3.21 p^2(1-p)^2: f2 = 1181 px (r1 980; S02 enters at 0.18 ln/f), 4% SETTLE at f12,
  locked with zero velocity at f15; f1 still 1535.6 px, centred.
* Floor slab x1.4 in X/Y: no slab edge in the bottom corners, no env-ground band in the mirror or the f1 ball.
* Off-screen drop shadow f16-25: the overhead key throws it on the floor at the landing spot (coral wall f16-30
  max 0.24/255; r1 dipped 10%).  Gummy unhidden at f17 (r1 f13: lime speck in the ball's reflection).
* Airborne: rock 0.25 -> 0.6, ears trail the rock (0.8, 0.04 s late), yaw twist +-5.8 deg during the 0.2x float.
* Lemon block #FFE04A (pre-compensates the coral bounce), mint rim coat 0.4 / 0.15.
* Wall mirror: invisible to diffuse rays and casts no shadow -- its wall shadow, seen through the glossy-invisible
  disc, printed a dark ellipse on the front-right floor (also in r1).
Cost: final 320 spp (r1 384), threshold 0.008: 18-37 s/f measured on an idle/shared H200 (~25-29 s mean) ->
  ~1.25-1.45 GPU-h for 180 f (cap 1.4).

Round 1 deviations from docs/storyboard.md that still hold (all visual / tunable)
--------------------------------------------------------------------------------
* Wall mirror: storyboard rotation=(90,0,45) puts the disc PERPENDICULAR to the coral wall.  The disc is aimed by the
  camera/gummy bisector (re-derived from GUMMY_XY), r 0.30, so the gummy sits centred in it.  Mirror + rim are
  invisible to glossy rays (their image in the glossy floor was a bright ring at the frame edge).
* Ball band: a thin candy-pink belt (2.5 mm proud, rounded edges) tilted 45 deg to the view axis so the rotation
  reads (a band in the rolling plane is a tyre); the ball rides on the belt radius (0.1725), never in the floor.
* Ball deflection: physical reflection about the measured contact normal (restitution 0.8), so it rebounds back to
  the left instead of the storyboard's front-right.
* Bonk response: lagged sideways drag instead of the storyboard's lean_y phase +0.6 (which pops at u=0); lean along
  the measured contact normal (the storyboard lean_x sign leaned toward the ball); stretch-first vertical pulse.
* Squash rings (bottom->top) solved for constant volume (a single mid ring x1.25 loses 17% volume).
* Gummy mesh: D.stanford_bunny leaves one 22-edge hole under the chin -> fan-filled (0 boundary / 0 non-manifold).
* Fourth-wall card emission 1.1 (glossy/transmission only) + matching side card where the floor->mirror path exits.
* Off-frame blush "hall" wall with candy panels right of the diorama, seen only by the whip (f176-180).
* Pull-out: camera = T(f) + d(f) u_lock (no rotation), target glides ball -> gummy, focus from the ball's mirror image
  to the gummy, f-stop 8 -> 2.2; camera f1 = 0.614 m from the ball (exact 1536 px solve); f < 1 tracks the ball.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

V = Vector
SHOT = "s03_gummy"
N = 180
FILM_START = 421
args = D.parse_args()
ENV = os.environ.get
DEBUG_CAM = ENV("S03_CAM", "")
REPORT_ONLY = ENV("S03_REPORT", "") == "1"


def envv(name, default):
    return V(tuple(float(v) for v in ENV(name, default).split(",")))


D.reset_scene()
sc = bpy.context.scene
# clamp_indirect: G5 (r2) -- a low clamp cuts the transmitted/caustic paths of the gummy's glow light
D.setup_cycles(samples=512, threshold=0.008, min_samples=64, diffuse=4, glossy=8, transmission=12, volume=2,
               caustics=True, clamp_indirect=float(ENV("S03_CLAMP", "10")), motion_blur=True, shutter=0.5)
EXPOSURE = float(ENV("S03_EXPO", "-0.2"))
D.setup_color(exposure=EXPOSURE)
D.setup_output()
sc.frame_start, sc.frame_end = 1, N

BAKE0, BAKE1 = -2, N + 3          # bake past both ends so shutter intervals at f1 / f180 are well defined


# ----------------------------------------------------------------------------------------------
# time remap tau(f) [s]: 1x -> ramp f25-31 -> 0.2x f31-85 -> ramp f85-91 -> 1x.  Drives objects only.
# ----------------------------------------------------------------------------------------------
def rate(f):
    if f <= 25:
        return 1.0
    if f <= 31:
        return 1.0 - 0.8 * (f - 25) / 6.0
    if f <= 85:
        return 0.2
    if f <= 91:
        return 0.2 + 0.8 * (f - 85) / 6.0
    return 1.0


def tau(f):
    if f <= 25:
        return (f - 1) / 30.0
    if f <= 31:
        x = f - 25
        return 0.8 + (x - 0.8 * x * x / 12.0) / 30.0
    if f <= 85:
        return 0.92 + 0.2 * (f - 31) / 30.0
    if f <= 91:
        x = f - 85
        return 1.28 + (0.2 * x + 0.8 * x * x / 12.0) / 30.0
    return 1.40 + (f - 91) / 30.0


assert abs(tau(31) - 0.92) < 1e-9 and abs(tau(85) - 1.28) < 1e-9 and abs(tau(91) - 1.40) < 1e-9

# ----------------------------------------------------------------------------------------------
# gummy motion, closed form in tau
# ----------------------------------------------------------------------------------------------
G = 9.81
Z_DROP, TAU0, TAU_C = 2.6, 0.192, 0.92          # fall from 2.6 m, contact at tau_c (f31)
TAU_L, V_L, TAU_2 = 1.03, 2.634, 1.567           # lift-off, launch speed, second landing (f96)
TAU_B = 1.90                                      # bonk (f106)
TAU_EAR, TAU_PLOP, TAU_SETTLE = tau(121), tau(136), tau(151)   # beat accents after the bonk (global 541/556/571)
H_GUMMY = 0.75
GUMMY_XY = envv("S03_GXY", "-0.32,0.42")          # r1 (-0.15,0.40): now fully in front of the stripes
GUMMY_YAW = -30.0
C_COM = 0.263                                     # measured centre-of-mass height of the 0.75 m bunny
EAR_AMP = float(ENV("S03_EAR", "1.0"))
SQ_H = float(ENV("S03_SQH", "0.63"))              # lead note 2 / storyboard fallback A: max-squash height (r1 0.55)
SQ_RINGS_055 = (1.15, 1.40, 1.35, 1.10)           # r1 volume-preserving rings for height 0.55 (bottom -> top)
SQ_ALPHA = float(ENV("S03_SQALPHA", "0.727"))    # ring excess scale for SQ_H (solved: volume within 1%, see REPORT)
SQUASH_RINGS = tuple(1.0 + SQ_ALPHA * (r - 1.0) for r in SQ_RINGS_055)
AIR_LEAN = float(ENV("S03_AIRLEAN", "0.6"))       # airborne rock (r1 0.25: invisible)
AIR_EAR = float(ENV("S03_AIREAR", "0.8"))         # ears lag the airborne rock
TWIST_DEG = float(ENV("S03_TWIST", "7.5"))        # airborne yaw twist amplitude (peaks at +-5.8 deg)
BONK_DECAY, BONK_FREQ = float(ENV("S03_BDECAY", "1.4")), float(ENV("S03_BFREQ", "2.0"))   # r1 3.5 /s, 2.2 Hz


def _osc(u, amp, decay, freq, lag=0.0):
    if u < lag:
        return 0.0
    return amp * math.exp(-decay * u) * math.sin(2 * math.pi * freq * (u - lag))


BONK_LEAN = float(ENV("S03_BONK_LEAN", "1.15"))


def d_spring(t):
    """Vertical jelly spring (positive = squash): first impact + second landing + bonk (stretch-first, so the
    flank contracts away from the ball before the small rebound bulge) + the f136 after-squash 'plop' (POP)."""
    return (_osc(t - TAU_C, 0.61, 5.5, 4.5) + _osc(t - TAU_2, 0.30, 6.0, 4.5)
            + _osc(t - TAU_B, -0.08, 6.0, 4.5) + _osc(t - TAU_PLOP, 0.12, 8.0, 2.5))


def k_squash(t):
    return D.clamp01(d_spring(t) / 0.45)


def k_stretch(t):
    return D.clamp01(-d_spring(t) / 0.25)


def height_factor(t):
    return 1.0 - (1.0 - SQ_H) * k_squash(t) + 0.25 * k_stretch(t)


def k_ear(t):
    e = (_osc(t - TAU_C, 0.9, 4.0, 3.0, 0.03) + _osc(t - TAU_2, 0.45, 4.0, 3.0, 0.03)
         + _osc(t - TAU_B, 0.5, 4.0, 3.0, 0.03) + _osc(t - TAU_EAR, 0.4, 4.0, 3.0))
    s = t - TAU_L
    if s >= 0:      # in the air the ears trail the nose-tail rock (opposite sign, 0.04 s late)
        e += _osc(s, -AIR_EAR, 2.0, 3.0, 0.04) * air_damp(t)
    return EAR_AMP * e


def air_damp(t):
    """The second landing soaks up what is left of the airborne rock."""
    return 1.0 if t < TAU_2 else math.exp(-6.0 * (t - TAU_2))


def yaw_twist(t):
    """Slow airborne twist (deg), one full swing during the 0.2x float (f48-85), zero value and speed at both ends."""
    s, T = t - TAU_L, tau(85) - TAU_L
    if s <= 0.0 or s >= T:
        return 0.0
    x = s / T
    return TWIST_DEG * math.sin(2 * math.pi * x) * math.sin(math.pi * x)


def gummy_base_z(t):
    if t < TAU0:
        return Z_DROP
    if t < TAU_C:
        return Z_DROP - 0.5 * G * (t - TAU0) ** 2
    if TAU_L <= t < TAU_2:
        s = t - TAU_L
        ballistic = V_L * s - 0.5 * G * s * s
        # airborne: the jelly oscillates about its centre of mass, not its feet
        return max(0.0, ballistic - (height_factor(t) - 1.0) * C_COM)
    return 0.0


# lean in WORLD metres of top-layer displacement; converted to lattice-local lean_x / lean_y keys
LEAN_TOP = 0.15                                   # top-layer displacement of a lean key at value 1
BONK = {"n": V((0.5, 0.866)), "side": V((0.866, -0.5))}   # replaced by the measured contact frame below
U_REST1, U_REST2 = tau(146) - TAU_B, tau(165) - TAU_B      # bonk wobble tapers to exact rest by f165


def bonk_taper(u):
    return 1.0 - D.smootherstep(D.clamp01((u - U_REST1) / (U_REST2 - U_REST1)))


def lean_world(t):
    yaw = math.radians(GUMMY_YAW + yaw_twist(t))
    nose_tail = V((math.cos(yaw), math.sin(yaw)))          # bunny local +x (tail) in world
    w = V((0.0, 0.0))
    s = t - TAU_L
    if s >= 0:                                             # airborne rock along the nose-tail axis
        w += nose_tail * (LEAN_TOP * AIR_LEAN * math.exp(-2.0 * s) * math.sin(2 * math.pi * 3.0 * s) * air_damp(t))
    u = t - TAU_B
    if u >= 0:                                             # bonk: push along n, lagged sideways drag
        tp = bonk_taper(u)
        w += BONK["n"] * (LEAN_TOP * BONK_LEAN * math.exp(-BONK_DECAY * u) * math.sin(2 * math.pi * BONK_FREQ * u)
                          * tp)
        w += BONK["side"] * (LEAN_TOP * _osc(u, 0.4, BONK_DECAY, BONK_FREQ, 0.04) * tp)
    return w


def lean_keys(t):
    w = lean_world(t)
    yaw = -math.radians(GUMMY_YAW + yaw_twist(t))           # world -> bunny local
    lx = w.x * math.cos(yaw) - w.y * math.sin(yaw)
    ly = w.x * math.sin(yaw) + w.y * math.cos(yaw)
    return lx / LEAN_TOP, ly / LEAN_TOP


# ----------------------------------------------------------------------------------------------
# set dressing
# ----------------------------------------------------------------------------------------------
def stripes_mat():
    """Custom node setup #1 (stripes): fract(UV.x / 0.18) < 0.5 -> blush, else white, on clay."""
    m = D.mat_clay("blush", name="stripes", rough=0.55, sss=0.15, sheen=0.25)
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    p = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    dv = n.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 0.18
    fr = n.new("ShaderNodeMath"); fr.operation = "FRACT"
    lt = n.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.5
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs["A"].default_value = D.col("white")
    mx.inputs["B"].default_value = D.col("blush")
    l.new(tc.outputs["UV"], sep.inputs[0])
    l.new(sep.outputs["X"], dv.inputs[0])
    l.new(dv.outputs[0], fr.inputs[0])
    l.new(fr.outputs[0], lt.inputs[0])
    l.new(lt.outputs[0], mx.inputs["Factor"])
    l.new(mx.outputs["Result"], p.inputs["Base Color"])
    return m


def ray_only(ob, camera=False, diffuse=False, glossy=True, transmission=True, shadow=False, scatter=False):
    ob.visible_camera = camera
    ob.visible_diffuse = diffuse
    ob.visible_glossy = glossy
    ob.visible_transmission = transmission
    ob.visible_shadow = shadow
    ob.visible_volume_scatter = scatter


floor_mat = D.mat_candy("cream", name="floor_cream", rough=float(ENV("S03_FLOOR_ROUGH", "0.12")), coat=1.0,
                        coat_rough=0.02)
_fp = floor_mat.node_tree.nodes["Principled BSDF"]
D._set(_fp, spec=float(ENV("S03_FLOOR_SPEC", "0.5")))
FLOOR_K = float(ENV("S03_FLOORK", "0.85"))           # albedo scale (critic: x0.7 if the floor stays the brightest area)
if FLOOR_K != 1.0:
    _fc = D.col("cream")
    _fp.inputs["Base Color"].default_value = (_fc[0] * FLOOR_K, _fc[1] * FLOOR_K, _fc[2] * FLOOR_K, 1.0)
room = D.diorama_corner("Room", size=3.4, height=2.4, floor_mat=floor_mat,
                        left_mat=stripes_mat(), right_mat=D.mat_clay("coral"), rot_z=45)
# r2: floor slab x1.4 in its own X/Y (plain candy material, nothing stretches): the front bevel / slab face no longer
# sits in the bottom corners, and the env-map ground beyond the old slab edge (grey-mauve bands in the wall mirror
# and in the f1 ball) is replaced by floor.  The extra floor at the back hides behind the walls.
ROOM_FLOOR = bpy.data.objects["Room_floor"]
FLOOR_SCALE = float(ENV("S03_FLOOR_SCALE", "1.4"))
ROOM_FLOOR.scale = (FLOOR_SCALE, FLOOR_SCALE, 1.0)

# block stack (lemon / aqua / violet); storyboard base (0.85, 1.05) moved to (0.66, 1.22) to clear the mirror rim
BLOCK_XY = envv("S03_BLOCKS", "0.66,1.22")
blocks = []
z = 0.0
for size, r, yaw, c in ((0.32, 0.06, 0.0, "lemon"), (0.26, 0.05, 20.0, "aqua"), (0.20, 0.04, -15.0, "violet")):
    # r2: lemon pre-compensated (#FFE04A) -- the coral bounce rendered #FFD23F as marigold #F5C153
    mat_b = D.mat_candy("#FFE04A", name="candy_lemon_block") if c == "lemon" else D.mat_candy(c)
    b = D.rounded_box(f"Block_{c}", (size, size, size), r, location=(BLOCK_XY.x, BLOCK_XY.y, z - 0.001),
                      rotation=(0, 0, yaw), mat=mat_b, base_at_zero=True)
    blocks.append(b)
    z += size - 0.001

# wall mirror on the coral wall, aimed so the gummy sits centred in it from the locked camera
LOCK = V((0.20, -4.60, 1.15))
T_LOCK = V((-0.05, 0.40, 0.38))
MIRROR_C = envv("S03_MIRROR", "1.36,1.03,0.84")
MIRROR_R = float(ENV("S03_MIRROR_R", "0.30"))
WALL_N = V((-1.0, -1.0, 0.0)).normalized()                  # coral wall inward normal
# aim: bisector of mirror->camera and mirror->gummy, so the gummy sits centred in the mirror from the lock
_aim_g = V((GUMMY_XY.x, GUMMY_XY.y, 0.33))
_bis = ((LOCK - MIRROR_C).normalized() + (_aim_g - MIRROR_C).normalized()).normalized()
MIRROR_N = _bis
mirror_q = MIRROR_N.to_track_quat("Z", "Y")
mirror = D.cylinder("WallMirror", MIRROR_R, 0.03, (0, 0, 0), mat=D.mat_metal("chrome", name="mirror_chrome",
                                                                            rough=0.0), bevel=0.008)
# r2: mint rim with a softer coat -- grazing coat reflections washed its left/right arcs to S 0.3
rim = D.torus("MirrorRim", MIRROR_R + 0.012, 0.026, (0, 0, 0),
              mat=D.mat_candy("mint", name="candy_mint_rim", coat=0.4, coat_rough=0.15))
for o in (mirror, rim):
    o.visible_glossy = False          # keep its image out of the glossy floor (a bright ring at the frame edge)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = mirror_q
    o.location = MIRROR_C
# r2: the disc is also invisible to diffuse rays: seen from the floor it hid a patch of the bright coral wall and
# printed a dark ellipse on the front-right floor (r1 had it too)
mirror.visible_diffuse = False
if ENV("S03_MIRROR_GLOSSY") == "1":          # look-dev: let the floor reflect the mirror + rim
    mirror.visible_glossy = rim.visible_glossy = True
if ENV("S03_MIRROR_NOSHADOW", "1") == "1":   # r2: their wall shadow, seen through the glossy-invisible disc, printed a dark ellipse on the floor
    mirror.visible_shadow = rim.visible_shadow = False
# wall clearance of the disc's farthest-back rim point
_back = max((MIRROR_C + mirror_q @ V((math.cos(a) * (MIRROR_R + 0.04), math.sin(a) * (MIRROR_R + 0.04), -0.03))).dot(
    -WALL_N) for a in [i * math.pi / 36 for i in range(72)])
WALL_PLANE = 1.7                                           # inner face: dot(p, -WALL_N) = 1.7
if _back > WALL_PLANE - 0.005:                             # push the mirror forward off the wall if needed
    shift = _back - (WALL_PLANE - 0.005)
    for o in (mirror, rim):
        o.location = MIRROR_C + WALL_N * shift

# fourth-wall card (blush), glossy + transmission only, behind the locked camera
card = D.rounded_box("FourthWall", (7.0, 0.1, 3.5), 0.05, location=(0, -7.0, 1.5),
                     mat=D.mat_emission("blush", float(ENV("S03_CARD", "1.1")), name="fourth_wall"))
card.data.materials[0].cycles.emission_sampling = "NONE"
ray_only(card)
# side reflection card: the camera -> glossy floor -> wall mirror path leaves the open front-left of the diorama
# near the horizon; without this card it lands on the bright sky haze and paints a cream blob on the floor.
_fimg = V((MIRROR_C.x, MIRROR_C.y, -MIRROR_C.z))
_d = (_fimg - LOCK).normalized()
_d = V((_d.x, _d.y, -_d.z))                                  # after the floor bounce, heading to the mirror
_r = _d - 2.0 * _d.dot(MIRROR_N) * MIRROR_N                 # after the mirror bounce
_rh = V((_r.x, _r.y, 0.0)).normalized()
SIDE_C = MIRROR_C + _rh * 7.0
side = D.rounded_box("SideCard", (6.0, 0.1, 4.0), 0.05, location=(SIDE_C.x, SIDE_C.y, 1.2),
                     mat=card.data.materials[0])
side.rotation_euler = (0.0, 0.0, math.atan2(_rh.y, _rh.x) - math.pi / 2)
ray_only(side)

# off-frame hall wall right of the diorama: only the whip (f176-180) sees it, where it streaks into candy bands
# (the locked frustum starts at azimuth 73 deg; this wall spans ~8-66 deg as seen from the camera)
HALL_AZ, HALL_DIST = math.radians(37.0), 6.6
_hc = V((LOCK.x + HALL_DIST * math.cos(HALL_AZ), LOCK.y + HALL_DIST * math.sin(HALL_AZ), 0.0))
hall = D.empty("Hall", tuple(_hc))
hall.rotation_euler = (0, 0, HALL_AZ - math.pi / 2)        # local +y points away from the camera
_hw = D.rounded_box("HallWall", (7.6, 0.2, 5.0), 0.05, location=(0, 0.1, -1.6), mat=D.mat_clay("blush"),
                    base_at_zero=True)
_hw.parent = hall
for i, (hx, hz, w, h, c, art) in enumerate(((-2.9, 0.75, 1.0, 0.7, "lemon", "cream"),
                                            (-1.3, 0.95, 0.8, 1.0, "aqua", "white"),
                                            (0.35, 0.7, 1.2, 0.65, "violet", "butter"),
                                            (2.0, 0.9, 0.9, 0.85, "pink", "sky"),
                                            (3.3, 0.7, 0.6, 0.55, "mint", "white"))):
    fr = D.rounded_box(f"HallFrame{i}", (w, 0.06, h), 0.03, location=(hx, -0.03, hz), mat=D.mat_candy(c))
    fr.parent = hall
    cv = D.rounded_box(f"HallArt{i}", (w * 0.76, 0.07, h * 0.72), 0.01, location=(hx, -0.035, hz),
                       mat=D.mat_clay(art))
    cv.parent = hall
_hb = D.rounded_box("HallBase", (7.6, 0.08, 0.14), 0.02, location=(0, -0.03, 0.0), mat=D.mat_candy("white"),
                    base_at_zero=True)
_hb.parent = hall
_hr = D.rounded_box("HallRail", (7.6, 0.06, 0.06), 0.02, location=(0, -0.03, 0.22), mat=D.mat_candy("coral"))
_hr.parent = hall


# ----------------------------------------------------------------------------------------------
# gummy bunny + lattice
# ----------------------------------------------------------------------------------------------
def fan_fill_holes(ob):
    """Close any boundary loops left by D.stanford_bunny (fan from the loop centroid)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    adj = {}
    for e in bm.edges:
        if e.is_boundary:
            a, b = e.verts[0].index, e.verts[1].index
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    seen, loops = set(), []
    for s0 in sorted(adj):
        if s0 in seen:
            continue
        loop, prev, cur = [s0], -1, s0
        seen.add(s0)
        while True:
            nxt = [v for v in adj[cur] if v != prev]
            if not nxt or nxt[0] == s0 or nxt[0] in seen:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) >= 3:
            loops.append([bm.verts[i] for i in loop])
    for vs in loops:
        cv = bm.verts.new(sum((v.co for v in vs), V()) / len(vs))
        for i in range(len(vs)):
            bm.faces.new((vs[i], vs[(i + 1) % len(vs)], cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    nb = sum(1 for e in bm.edges if e.is_boundary)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    D.set_smooth(ob)
    return len(loops), nb, nm


def mesh_np(me):
    """(vertex coords float64 (n,3), triangle vertex indices (t,3)) of a mesh."""
    me.calc_loop_triangles()
    n, nt = len(me.vertices), len(me.loop_triangles)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    tri = np.empty(nt * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    return co.reshape(n, 3).astype(np.float64), tri.reshape(nt, 3)


def mesh_volume(co, tri):
    a, b, c = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def taubin_smooth(ob, iters, lam=0.5, mu=-0.53):
    """Taubin lambda|mu smoothing (umbrella operator, numpy): removes the scan crinkle without the shrinkage of plain
    vertex averaging (bmesh.ops.smooth_laplacian_vert is a no-op on this scan).  Positions only, topology kept."""
    me = ob.data
    co, tri = mesh_np(me)
    v0 = mesh_volume(co, tri)
    ne = len(me.edges)
    ev = np.empty(ne * 2, np.int32)
    me.edges.foreach_get("vertices", ev)
    i0, i1 = ev[0::2], ev[1::2]
    n = len(co)
    deg = np.maximum(np.bincount(i0, minlength=n) + np.bincount(i1, minlength=n), 1).astype(np.float64)

    def lap(p):
        out = np.empty_like(p)
        for k in range(3):
            s = np.bincount(i0, weights=p[i1, k], minlength=n) + np.bincount(i1, weights=p[i0, k], minlength=n)
            out[:, k] = s / deg - p[:, k]
        return out
    for _ in range(iters):
        co += lam * lap(co)
        co += mu * lap(co)
    # restore the exact volume (scale about the centroid; Taubin drifts by well under 1%)
    v1 = mesh_volume(co, tri)
    cen = co.mean(axis=0)
    co = cen + (co - cen) * (v0 / v1) ** (1.0 / 3.0)
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.update()
    return v0, v1


def candy_glass(color, absorb=2.0, absorb_lin=None, name=None, tint_exp=0.5, rough=0.0, ior=1.5):
    """(G5, after shots/s02_caustics.py) D.mat_glass with the surface tint set to colour^tint_exp: Cycles applies the
    transmission tint at both interfaces of a closed solid, so 0.5 makes the double crossing land on the palette
    colour instead of its square (lime^2 reads olive).  Beer-Lambert absorption then deepens thick parts.
    absorb_lin: linear RGB(A) set directly on the node (D.col() would re-linearise a tuple)."""
    m = D.mat_glass(color, name=name, rough=rough, ior=ior, absorb=absorb)
    c = D.col(color)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        c[0] ** tint_exp, c[1] ** tint_exp, c[2] ** tint_exp, 1.0)
    if absorb_lin is not None and absorb > 0:
        m.node_tree.nodes["Volume Absorption"].inputs["Color"].default_value = tuple(absorb_lin[:3]) + (1.0,)
    return m


def gummy_mat():
    """Lead note 1: colour in the volume, not on the surface.  Surface = lime^0.5 (G5), absorption colour pulled
    toward lime-yellow (no mint: it read dark emerald), density 3.5 -> ~1.6."""
    gcol = ENV("S03_GCOL", "#A0E61D")
    ab = D.mix_col(gcol, ENV("S03_ABS2", "lemon"), float(ENV("S03_ABSK", "0.0")))
    return candy_glass(gcol, absorb=float(ENV("S03_DENS", "1.6")), absorb_lin=ab, name="gummy_lime",
                       tint_exp=float(ENV("S03_TEXP", "0.5")), rough=float(ENV("S03_GROUGH", "0.10")), ior=1.38)


gummy = D.stanford_bunny("Gummy", H_GUMMY, gummy_mat(), location=(GUMMY_XY.x, GUMMY_XY.y, Z_DROP),
                         rotation=(0, 0, GUMMY_YAW))
FILL = fan_fill_holes(gummy)
SMOOTH_IT = int(ENV("S03_TAUBIN", "100"))
VOL0, VOL1 = taubin_smooth(gummy, SMOOTH_IT, float(ENV("S03_TLAM", "0.6")), float(ENV("S03_TMU", "-0.62")))
_zmin = min(v.co.z for v in gummy.data.vertices)          # re-ground after smoothing (base exactly at z=0)
gummy.data.transform(Matrix.Translation((0.0, 0.0, -_zmin)))
gummy.data.update()
_vs = gummy.data.vertices
BB_MIN = V((min(v.co.x for v in _vs), min(v.co.y for v in _vs), 0.0))
BB_MAX = V((max(v.co.x for v in _vs), max(v.co.y for v in _vs), max(v.co.z for v in _vs)))

lat = bpy.data.lattices.new("GummyLattice")
lat.points_u, lat.points_v, lat.points_w = 3, 3, 4
lat.interpolation_type_u = lat.interpolation_type_v = lat.interpolation_type_w = "KEY_BSPLINE"
lat_ob = D.link(bpy.data.objects.new("GummyLattice", lat))
LAT_SIZE = (BB_MAX - BB_MIN) * 1.15
lat_ob.parent = gummy                       # follows the gummy's location (and yaw): bunny-aligned box
lat_ob.location = ((BB_MIN + BB_MAX) * 0.5).to_tuple()
lat_ob.scale = LAT_SIZE.to_tuple()
lat_ob.hide_render = True
mod = gummy.modifiers.new("Lattice", "LATTICE")
mod.object = lat_ob
ZB = (0.0 - lat_ob.location[2]) / LAT_SIZE.z          # the bunny's base in lattice-local units

lat_ob.shape_key_add(name="Basis")
LEAN_LAYERS = (0.0, 0.04, 0.10, 0.15)                  # metres, 1-based layers 1..4
EAR_DZ, EAR_BACK = -0.07, 0.06                         # top layer (ears) at value 1
EAR_COLS = (1.0, 0.75, 0.35)                           # head -> tail column weights (ears sit over the head)


def add_key(name, fn):
    k = lat_ob.shape_key_add(name=name, from_mix=False)
    k.slider_min, k.slider_max = -2.0, 2.0
    for i, p in enumerate(lat.points):
        u, v, w = i % 3, (i // 3) % 3, i // 9
        k.data[i].co = fn(V(p.co), u, v, w)
    return k


def _sq(c, u, v, w):
    s = SQUASH_RINGS[w]
    return V((c.x * s, c.y * s, ZB + (c.z - ZB) * SQ_H))


def _st(c, u, v, w):
    return V((c.x * 0.90, c.y * 0.90, ZB + (c.z - ZB) * 1.25))


def _lean(axis):
    def fn(c, u, v, w):
        d = V(c)
        d[axis] += LEAN_LAYERS[w] / LAT_SIZE[axis]
        return d
    return fn


def _ear(c, u, v, w):
    if w != 3:
        return V(c)
    k = EAR_COLS[u]
    return V((c.x + k * EAR_BACK / LAT_SIZE.x, c.y, c.z + k * EAR_DZ / LAT_SIZE.z))


K = {
    "squash": add_key("squash", _sq),
    "stretch": add_key("stretch", _st),
    "lean_x": add_key("lean_x", _lean(0)),
    "lean_y": add_key("lean_y", _lean(1)),
    "ear_flop": add_key("ear_flop", _ear),
}


def gummy_state(f):
    t = tau(f)
    lx, ly = lean_keys(t)
    return {"z": gummy_base_z(t), "yaw": GUMMY_YAW + yaw_twist(t), "squash": k_squash(t), "stretch": k_stretch(t),
            "lean_x": lx, "lean_y": ly, "ear_flop": k_ear(t)}


def apply_gummy(f):
    s = gummy_state(f)
    gummy.location.z = s["z"]
    gummy.rotation_euler.z = math.radians(s["yaw"])
    for k in K:
        K[k].value = s[k]


def eval_gummy_np():
    """Evaluated (lattice-deformed) gummy: world coords (n,3), local coords, triangles."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = gummy.evaluated_get(dg)
    me = ev.to_mesh()
    co, tri = mesh_np(me)
    ev.to_mesh_clear()
    mw = np.array(gummy.matrix_world)
    wco = co @ mw[:3, :3].T + mw[:3, 3]
    return wco, co, tri


# ----------------------------------------------------------------------------------------------
# chrome ball with a pink belt
# ----------------------------------------------------------------------------------------------
R_CHROME, R_ROLL = 0.170, 0.1725              # belt stands 2.5 mm proud; the ball rides on it
BELT_W, BELT_T = 0.022, 0.0045


def belt_mesh(name, mat, R=R_ROLL, w=BELT_W, t=BELT_T, seg=256, prof_n=40, n=6.0):
    bm = bmesh.new()
    prof = []
    for i in range(prof_n):
        th = 2 * math.pi * i / prof_n
        c, s = math.cos(th), math.sin(th)
        dr = t * math.copysign(abs(c) ** (2.0 / n), c)
        dz = w * math.copysign(abs(s) ** (2.0 / n), s)
        prof.append((math.sqrt(R * R - dz * dz) - t + dr, dz))
    rings = []
    for j in range(seg):
        ph = 2 * math.pi * j / seg
        rings.append([bm.verts.new((r * math.cos(ph), r * math.sin(ph), zz)) for (r, zz) in prof])
    for j in range(seg):
        a, b = rings[j], rings[(j + 1) % seg]
        for i in range(prof_n):
            i2 = (i + 1) % prof_n
            bm.faces.new((a[i], b[i], b[i2], a[i2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return D._mesh_object(name, bm, mat)


ball = D.sphere("RollBall", R_CHROME, (0, 0, R_ROLL), D.mat_metal("chrome", name="ball_chrome", rough=0.02),
                segments=192, rings=96)
ball.rotation_mode = "QUATERNION"
belt = belt_mesh("RollBand", D.mat_candy("pink", name="band_pink"))
belt.parent = ball
U_LOCK = (LOCK - T_LOCK).normalized()
_perp = (V((1.0, 0.0, 1.0)) - U_LOCK * V((1.0, 0.0, 1.0)).dot(U_LOCK)).normalized()
BELT_AXIS = (U_LOCK * math.cos(math.radians(45)) + _perp * math.sin(math.radians(45))).normalized()
belt.rotation_mode = "QUATERNION"
belt.rotation_quaternion = BELT_AXIS.to_track_quat("Z", "Y")

# ball lane (r2): same heading as r1 ((-1.5,-0.1) -> (-0.55,0.10)), shifted in depth so the contact lands on the
# gummy's screen-left silhouette (contact normal ~perpendicular to the view axis): the gap visibly closes on screen
# instead of the ball rolling in front of the chest.  The start A is re-derived so the ball still travels SB_IN m
# (~0.5 m/s) before the f106 contact.
D_IN = V((0.95, 0.20)).normalized()
LANE_Y = float(ENV("S03_LANE_DY", "0.32"))          # lane offset in y from the r1 lane (solved in REPORT, see below)
LANE_Q = V((-1.90, -0.10 + LANE_Y + (-1.90 + 1.50) * D_IN.y / D_IN.x))   # a far-left point on the shifted lane
SB_IN = float(ENV("S03_SB", "0.95"))
BALL_E = float(ENV("S03_BALL_E", "0.8"))
ROCK = float(ENV("S03_ROCK", "0.02"))               # f151 settle: overshoot 2 cm past rest, roll back by f161
F_PEAK, F_REST = 151, 161
BALL = {"sB": SB_IN, "dout": V((-1.0, 0.0)), "L": 0.3, "k": float(ENV("S03_BALL_K", "0.4"))}
A = LANE_Q.copy()                                   # replaced after the contact solve


def _decel(u):
    """Normalised 0->1 travel after the bonk: exponential-like, exact stop (zero speed) at U (= f151 peak)."""
    k, U = BALL["k"], tau(F_PEAK) - TAU_B
    if u <= 0:
        return 0.0
    u = min(u, U)
    g = lambda x: 1 - math.exp(-k * x) - k * x * math.exp(-k * U)   # noqa: E731
    return g(u) / g(U)


def _rock(u):
    """f151 -> f161: roll back ROCK metres (half-cosine, zero speed at both ends) = the SETTLE after the stop."""
    u0, u1 = tau(F_PEAK) - TAU_B, tau(F_REST) - TAU_B
    x = D.clamp01((u - u0) / (u1 - u0))
    return ROCK * 0.5 * (1.0 - math.cos(math.pi * x))


def ball_xy(t):
    v_in = BALL["sB"] / TAU_B
    if t <= TAU_B:
        return A + D_IN * (v_in * t)
    u = t - TAU_B
    return A + D_IN * BALL["sB"] + BALL["dout"] * (BALL["L"] * _decel(u) - _rock(u))


def gummy_bvh(f):
    apply_gummy(f)
    gummy.location.x, gummy.location.y = GUMMY_XY
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    return BVHTree.FromObject(gummy, dg), gummy.matrix_world.copy()


def nearest(bvh, mw, p):
    loc, nrm, idx, dist = bvh.find_nearest(mw.inverted() @ p)
    return mw @ loc, dist


def solve_contact(Q, bvh, mw, s_max=2.5, step=0.004):
    """First touch of a ball rolling from Q along D_IN: (s, centre, contact point, unit normal ball->gummy)."""
    s = 0.0
    while s < s_max:
        c = V((Q.x + D_IN.x * s, Q.y + D_IN.y * s, R_ROLL))
        if nearest(bvh, mw, c)[1] <= R_ROLL:
            break
        s += step
    if s >= s_max:
        return None
    a_, b_ = s - step, s
    for _ in range(40):
        m_ = 0.5 * (a_ + b_)
        c = V((Q.x + D_IN.x * m_, Q.y + D_IN.y * m_, R_ROLL))
        if nearest(bvh, mw, c)[1] <= R_ROLL:
            b_ = m_
        else:
            a_ = m_
    cB = V((Q.x + D_IN.x * a_, Q.y + D_IN.y * a_, R_ROLL))
    hitp, _d = nearest(bvh, mw, cB)
    return a_, cB, hitp, (hitp - cB).normalized()


def view_dot(hitp, n3):
    """|cos| between the horizontal contact normal and the horizontal view ray (0 = contact on the silhouette)."""
    vh = V((hitp.x - LOCK.x, hitp.y - LOCK.y)).normalized()
    return abs(V((n3.x, n3.y)).normalized().dot(vh))


# --- solve the contact on the pre-bonk gummy (shape at tau_b is independent of the bonk response)
f_b = 106
assert abs(tau(f_b) - TAU_B) < 1e-9
bvh, mw = gummy_bvh(f_b)
LANE_TABLE = []
if REPORT_ONLY:                                     # lane survey: contact normal vs view axis per depth offset
    for i in range(-6, 31, 2):
        dy = i * 0.01
        Qi = V((-1.90, -0.10 + dy + (-1.90 + 1.50) * D_IN.y / D_IN.x))
        r_ = solve_contact(Qi, bvh, mw)
        if r_:
            LANE_TABLE.append((round(dy, 2), round(view_dot(r_[2], r_[3]), 3), round(r_[2].z, 3),
                               tuple(round(x, 3) for x in r_[2])))
sol = solve_contact(LANE_Q, bvh, mw)
assert sol is not None, "ball lane misses the gummy"
_sC, cB, hitp, n3 = sol
B = V((cB.x, cB.y))
A = B - D_IN * SB_IN
BALL["sB"] = SB_IN
n_h = V((n3.x, n3.y)).normalized()
BONK["n"] = n_h
t_h = V((n_h.y, -n_h.x))
if t_h.dot(D_IN) < 0:
    t_h = -t_h
BONK["side"] = t_h
v_speed = BALL["sB"] / TAU_B
vin = D_IN * v_speed
vn, vt = vin.dot(n_h), vin.dot(t_h)
vout = t_h * vt - n_h * (BALL_E * vn)
BALL["dout"] = vout.normalized()
U_STOP = tau(F_PEAK) - TAU_B
_k = BALL["k"]
_gU = 1 - math.exp(-_k * U_STOP) - _k * U_STOP * math.exp(-_k * U_STOP)
BALL["L"] = vout.length * _gU / (_k * (1 - math.exp(-_k * U_STOP)))
REPORT = {
    "fill": FILL, "taubin_iters": SMOOTH_IT, "taubin_volume_ratio_before_restore": round(VOL1 / VOL0, 4),
    "A": tuple(round(x, 4) for x in A), "B": tuple(round(x, 4) for x in B),
    "contact_point": tuple(round(x, 4) for x in hitp), "contact_height": round(hitp.z, 4),
    "n_h": tuple(round(x, 3) for x in n_h), "contact_view_cos": round(view_dot(hitp, n3), 3),
    "v_in": round(v_speed, 3), "v_out": round(vout.length, 3), "dir_out": tuple(round(x, 3) for x in BALL["dout"]),
    "L_out": round(BALL["L"], 3), "ball_peak": tuple(round(x, 3) for x in ball_xy(tau(F_PEAK))),
    "ball_rest": tuple(round(x, 3) for x in ball_xy(tau(F_REST))), "lane_table": LANE_TABLE,
}

# --- local dent at the contact (r2): a Hook on a smooth-falloff vertex group, pushed 3 cm into the jelly along the
# contact normal on a POP impulse f106 -> ~f112 (zero at f106, so the contact solve above is unaffected)
DENT_R, DENT_D = float(ENV("S03_DENT_R", "0.12")), float(ENV("S03_DENT", "0.03"))
_wco, _lco, _tri = eval_gummy_np()
_mwi = gummy.matrix_world.inverted()
_cl = np.array(_mwi @ hitp)
_dist = np.linalg.norm(_lco - _cl, axis=1)
_x = np.clip(_dist / DENT_R, 0.0, 1.0)
_wt = (1.0 - _x * _x) ** 2
vg = gummy.vertex_groups.new(name="dent")
for _i in np.nonzero(_wt > 1e-4)[0]:
    vg.add([int(_i)], float(_wt[_i]), "REPLACE")
dent_e = D.empty("DentHook", (0, 0, 0), size=0.05)
dent_e.parent = gummy
hook = gummy.modifiers.new("Dent", "HOOK")
hook.object = dent_e
hook.vertex_group = "dent"
hook.falloff_type = "NONE"
hook.strength = 1.0
hook.matrix_inverse = Matrix.Identity(4)
N_LOCAL = (_mwi.to_3x3() @ n3).normalized()
_POP_NORM = max(math.exp(-8.0 * x / 1000.0) * math.sin(2 * math.pi * 2.5 * x / 1000.0) for x in range(400))


def dent_amount(t):
    u = t - TAU_B
    if u <= 0:
        return 0.0
    return DENT_D * math.exp(-8.0 * u) * math.sin(2 * math.pi * 2.5 * u) / _POP_NORM


# --- clearance checks along the whole path (every frame), feet clearance (verts below 6 cm)
CHECK = REPORT_ONLY or ENV("S03_CHECK") == "1"
min_clear, min_clear_f, feet_clear = 9.0, None, 9.0
for f in (range(1, N + 1) if CHECK else ()):
    if f in (f_b,):
        continue
    bvh_f, mw_f = gummy_bvh(f)
    c = ball_xy(tau(f))
    cc = V((c.x, c.y, R_ROLL))
    d = nearest(bvh_f, mw_f, cc)[1] - R_ROLL
    if d < min_clear:
        min_clear, min_clear_f = d, f
apply_gummy(f_b)
_wco106, _, _ = eval_gummy_np()
feet = [V(p) for p in _wco106[_wco106[:, 2] < 0.06]]
for f in (range(1, f_b) if CHECK else ()):
    c = ball_xy(tau(f))
    cc = V((c.x, c.y, R_ROLL))
    for p in feet[::7]:
        feet_clear = min(feet_clear, (p - cc).length - R_ROLL)
REPORT.update({"min_clearance_m": round(min_clear, 4), "min_clearance_frame": min_clear_f,
               "feet_clearance_before_bonk_m": round(feet_clear, 4)})
if REPORT_ONLY:                      # squash / stretch volume check (lattice evaluated at rest and at full keys)
    for k in K.values():
        k.value = 0.0
    gummy.location = (GUMMY_XY.x, GUMMY_XY.y, 0.0)
    gummy.rotation_euler.z = math.radians(GUMMY_YAW)
    _w0, _, _t0 = eval_gummy_np()
    K["squash"].value = 1.0
    _w1, _, _ = eval_gummy_np()
    K["squash"].value = 0.0
    K["stretch"].value = 1.0
    _w2, _, _ = eval_gummy_np()
    K["stretch"].value = 0.0
    REPORT["squash_volume_ratio"] = round(mesh_volume(_w1, _t0) / mesh_volume(_w0, _t0), 4)
    REPORT["stretch_volume_ratio"] = round(mesh_volume(_w2, _t0) / mesh_volume(_w0, _t0), 4)
    REPORT["squash_height"] = round(float(_w1[:, 2].max() - _w1[:, 2].min())
                                    / float(_w0[:, 2].max() - _w0[:, 2].min()), 4)
    _ears = _w0[:, 2] > 0.55                         # thin ears: mean distance to the ear centroid plane (thickness)
    REPORT["ear_verts"] = int(_ears.sum())

# ----------------------------------------------------------------------------------------------
# bake gummy + ball
# ----------------------------------------------------------------------------------------------
gummy.location = (GUMMY_XY.x, GUMMY_XY.y, Z_DROP)
D.bake(gummy, "location", BAKE0, BAKE1, lambda f: (GUMMY_XY.x, GUMMY_XY.y, gummy_state(f)["z"]))
D.bake(gummy, "rotation_euler", BAKE0, BAKE1, lambda f: (0.0, 0.0, math.radians(gummy_state(f)["yaw"])))
for name, kb in K.items():
    D.bake(kb, "value", BAKE0, BAKE1, (lambda nm: (lambda f: gummy_state(f)[nm]))(name))
D.bake(dent_e, "location", BAKE0, BAKE1, lambda f: tuple(N_LOCAL * dent_amount(tau(f))))

ball_pos = {f: ball_xy(tau(f)) for f in range(BAKE0 - 1, BAKE1 + 1)}
q = Quaternion()
ball_q = {}
for f in range(BAKE0, BAKE1 + 1):
    dlt = ball_pos[f] - ball_pos[f - 1]
    ds = dlt.length
    if ds > 1e-9:
        axis = V((0.0, 0.0, 1.0)).cross(V((dlt.x, dlt.y, 0.0)).normalized())
        q = Quaternion(axis, ds / R_ROLL) @ q
    ball_q[f] = q.copy()
D.bake(ball, "location", BAKE0, BAKE1, lambda f: (ball_pos[f].x, ball_pos[f].y, R_ROLL))
D.bake(ball, "rotation_quaternion", BAKE0, BAKE1, lambda f: tuple(ball_q[f]))

# before its drop the gummy hangs at z 2.6 (above frame) and would show as a lime blob in the f1 ball close-up and
# as a speck in the ball's sky reflection at f13-15: keep it out of render until the camera is locked and the ball's
# reflection no longer shows it (r1 unhid at f13)
G_VIS = int(ENV("S03_GVIS", "17"))
D.hide_range(gummy, visible_from=G_VIS)
if ENV("S03_NOGUMMY") == "1":
    gummy.hide_render = True

# ----------------------------------------------------------------------------------------------
# lights + world (r2: shaped key + flag, half fill tinted lavender, light-linked glow on the gummy)
# ----------------------------------------------------------------------------------------------
KEY, FILL_L, RIM = D.studio_rig(target=(-0.1, 0.4, 0.4), scale=1.0, key_power=float(ENV("S03_KEY", "420")))
KEY.location = envv("S03_KEY_POS", "-2.5,0.0,4.5")      # r2: over the set (r1 rig (-3.2,-3.0,4.2), front-left)
KEY_AIM = envv("S03_KEY_AIM", ",".join(str(x) for x in T_LOCK))
D.look_at(KEY, tuple(KEY_AIM))
KEY.data.size = float(ENV("S03_KEY_SIZE", "2.0"))
KEY.data.spread = math.radians(float(ENV("S03_KEY_SPREAD", "180")))
FILL_L.data.energy *= float(ENV("S03_FILLK", "0.7"))
FILL_L.data.color = D.col(ENV("S03_FILL_COL", "#DCD6FF"))[:3]
# flag: a black card between the key and the front floor (camera/glossy/transmission-invisible; blocks diffuse and
# shadow rays so MIS cannot leak around it) -> the floor falls off toward the bottom edge
FLAG = None
if ENV("S03_FLAG", "1") == "1":
    # horizontal cutter over the front floor strip: from the overhead key the rays to the front floor cross z 2.4
    # at y < -0.6 while the rays to the gummy / ball / walls cross at y > 0.1, so only the lower frame is shaded
    _fc = envv("S03_FLAG_C", "-0.6,-1.25,2.4")
    _fs = envv("S03_FLAG_SIZE", "5.0,2.1")
    flag_mat = D.principled("flag_black", base=(0.0, 0.0, 0.0, 1.0), rough=1.0, spec=0.0)
    FLAG = D.plane("Flag", (_fs.x, _fs.y), tuple(_fc), mat=flag_mat)
    ray_only(FLAG, camera=False, diffuse=True, glossy=False, transmission=False, shadow=True)
# glow: light-linked to the gummy only (lead note 1) -- it lights the jelly from behind / above and its lime light
# leaves through the body (glow + lime caustic on the floor) without washing out the floor reflections
GLOW_POS = envv("S03_GLOW_POS", f"{GUMMY_XY.x - 0.10},{GUMMY_XY.y + 1.00},{1.55}")
GLOW_AIM = envv("S03_GLOW_AIM", f"{GUMMY_XY.x},{GUMMY_XY.y},0.30")
GLOW = D.light("AREA", "GummyGlow", tuple(GLOW_POS), tuple(GLOW_AIM), power=float(ENV("S03_GLOW_W", "150")),
               color=ENV("S03_GLOW_COL", "#F0FFF2"), size=float(ENV("S03_GLOW_SIZE", "1.2")))
GLOW.data.shape = "DISK"
glow_rx = bpy.data.collections.new("GlowReceivers")
glow_rx.objects.link(gummy)
GLOW.light_linking.receiver_collection = glow_rx
if ENV("S03_GLOW_W", "150") == "0":
    GLOW.hide_render = True

sky = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
if not os.path.exists(sky):
    print("[s03] WARNING candy_sky_nosun missing -> colorful_studio")
    sky = D.HDRI["colorful_studio"]
WORLD_K = float(ENV("S03_WORLD", "0.25"))
GLOSSY_BOOST = float(ENV("S03_GBOOST", "3.6"))
rig = D.world_hdri(sky, WORLD_K, camera_bg="blush")
# chrome / coat reflections see the candy sky at a pastel-bright level (x GLOSSY_BOOST) while its diffuse
# lighting contribution stays at WORLD_K (the softbox rig remains the key)
_wn, _wl = rig.world.node_tree.nodes, rig.world.node_tree.links
_lp = _wn.new("ShaderNodeLightPath")
_ma = _wn.new("ShaderNodeMath"); _ma.operation = "MULTIPLY_ADD"
_ma.inputs[1].default_value = GLOSSY_BOOST - 1.0; _ma.inputs[2].default_value = 1.0
_mu = _wn.new("ShaderNodeMath"); _mu.operation = "MULTIPLY"; _mu.inputs[1].default_value = WORLD_K
_wl.new(_lp.outputs["Is Glossy Ray"], _ma.inputs[0])
_wl.new(_ma.outputs[0], _mu.inputs[0])
_wl.new(_mu.outputs[0], rig.light_bg.inputs["Strength"])

# ----------------------------------------------------------------------------------------------
# camera: pull-out f1-15, locked f16-170, whip right f171-180
# ----------------------------------------------------------------------------------------------
LENS = 50.0
_tan = 0.5 * (1536.0 / 1920.0) * 36.0 / LENS
D0 = float(ENV("S03_D0", str(R_CHROME / math.sin(math.atan(_tan)))))   # exact 1536 px silhouette
D1 = (LOCK - T_LOCK).length
F_LOCK = 15
WHIP_DEG, WHIP_F0 = 55.0, 170
PULL_EXP, PULL_BUMP = 1.7, 3.2136                    # r2: 0.25 ln/f off the cut (r1 0.43), 4% SETTLE at f12


def cam_target(f):
    p = D.prog(f, 1, F_LOCK)
    ball_c = V((ball_pos[min(max(f, BAKE0), BAKE1)].x, ball_pos[min(max(f, BAKE0), BAKE1)].y, R_ROLL))
    e_t = D.ease_in_out_sine(p)
    return ball_c.lerp(T_LOCK, e_t), e_t


def cam_dist(f):
    p = D.prog(f, 1, F_LOCK)
    # r2: e(p) = 1-(1-p)^1.7 (gentler off the cut: S02 pushes in at 0.18 ln/f, r1 left at 0.45) + a zero-slope bump
    # for a ~4% SETTLE overshoot in distance around f12, exactly locked with zero velocity at f15
    e = 1.0 - (1.0 - p) ** PULL_EXP + PULL_BUMP * p * p * (1.0 - p) ** 2
    return D0 * (D1 / D0) ** e


def whip_deg(f):
    if f <= WHIP_F0:
        return 0.0
    x = (f - WHIP_F0) / 10.0
    if x <= 1.0:
        return WHIP_DEG * D.ease_in_cubic(x)
    return WHIP_DEG + 3.0 * WHIP_DEG / 10.0 * (f - WHIP_F0 - 10)        # continue at 16.5 deg/f


def cam_pos(f):
    if f >= F_LOCK:
        return LOCK.copy()
    T, _ = cam_target(f)
    return T + U_LOCK * cam_dist(f)


def tgt_pos(f):
    if f < F_LOCK:
        return cam_target(f)[0]
    ang = -math.radians(whip_deg(f))
    return LOCK + Matrix.Rotation(ang, 3, "Z") @ (T_LOCK - LOCK)


def focus_pos(f):
    if f < F_LOCK:
        T, e_t = cam_target(f)
        return T + U_LOCK * (0.08 * (1.0 - e_t))
    return tgt_pos(f)


def fstop(f):
    return 8.0 * (2.2 / 8.0) ** D.ease_in_out_sine(D.prog(f, 1, F_LOCK))


def shutter(f):
    return 0.5 + 0.5 * D.prog(f, 171, 174)


focus_e = D.empty("Cam_focus", tuple(focus_pos(1)))
cam, cam_t = D.camera("Cam", tuple(cam_pos(1)), tuple(tgt_pos(1)), lens=LENS, fstop=2.2, focus=focus_e)
D.bake(cam, "location", BAKE0, BAKE1, lambda f: tuple(cam_pos(f)))
D.bake(cam_t, "location", BAKE0, BAKE1, lambda f: tuple(tgt_pos(f)))
D.bake(focus_e, "location", BAKE0, BAKE1, lambda f: tuple(focus_pos(f)))
D.bake(cam.data.dof, "aperture_fstop", BAKE0, BAKE1, fstop)
D.bake(sc.render, "motion_blur_shutter", BAKE0, BAKE1, shutter)


# ----------------------------------------------------------------------------------------------
# screen-space gap between the ball and the gummy (S03_CHECK): the bonk gap must close on screen, the parked ball
# must stay clear of the paws
# ----------------------------------------------------------------------------------------------
def screen_gap(f):
    sc.frame_set(f)
    wco, _, _ = eval_gummy_np()
    cm = cam.matrix_world.inverted()
    M = np.array(cm)
    pc = wco[::3] @ M[:3, :3].T + M[:3, 3]
    W, H = 1920.0, 1080.0
    fpx = cam.data.lens / cam.data.sensor_width * W
    gx = W / 2 + pc[:, 0] / -pc[:, 2] * fpx
    gy = H / 2 - pc[:, 1] / -pc[:, 2] * fpx
    bc = cm @ V((ball_pos[f].x, ball_pos[f].y, R_ROLL))
    bx, by = W / 2 + bc.x / -bc.z * fpx, H / 2 - bc.y / -bc.z * fpx
    br = fpx * math.tan(math.asin(min(1.0, R_CHROME / bc.length)))
    return float(np.min(np.hypot(gx - bx, gy - by)) - br), (round(bx, 1), round(by, 1)), round(br, 1)


if CHECK:
    gaps = {f: round(screen_gap(f)[0], 1) for f in list(range(96, 107)) + list(range(110, 171, 5))}
    REPORT["screen_gap_px"] = gaps
    REPORT["ball_screen_f16"] = screen_gap(16)[1:]
    sc.frame_set(1)

# ----------------------------------------------------------------------------------------------
# debug cameras / markers
# ----------------------------------------------------------------------------------------------
if ENV("S03_PATH") == "1":
    mk = D.mat_emission("pink", 3.0, name="dbg_path")
    for f in range(1, N + 1, 3):
        c = ball_pos[f]
        D.sphere(f"dbg_{f}", 0.012, (c.x, c.y, 0.01), mk, segments=12, rings=6)
if DEBUG_CAM:
    cd = bpy.data.cameras.new("DbgCam")
    dbg = D.link(bpy.data.objects.new("DbgCam", cd))
    if DEBUG_CAM == "top":
        cd.type = "ORTHO"
        cd.ortho_scale = float(ENV("S03_ORTHO", "4.2"))
        dbg.location = (float(ENV("S03_TX", "-0.3")), float(ENV("S03_TY", "0.2")), 8.0)
        dbg.rotation_euler = (0, 0, 0)
    elif DEBUG_CAM == "side":
        dbg.location = (-4.5, 0.2, 0.45)
        cd.lens = 50
        D.look_at(dbg, (-0.3, 0.2, 0.35))
    else:   # front: close to the gummy, same axis as the lock
        _tg = V((GUMMY_XY.x, GUMMY_XY.y, 0.33))
        dbg.location = tuple(_tg + U_LOCK * float(ENV("S03_FRONT_D", "2.2")))
        cd.lens = 50
        D.look_at(dbg, tuple(_tg))
    sc.camera = dbg

# ----------------------------------------------------------------------------------------------
# meta + report
# ----------------------------------------------------------------------------------------------
sq = [k_squash(tau(f)) for f in range(1, N + 1)]
f_maxsq = 1 + max(range(N), key=lambda i: sq[i])
zs = [gummy_base_z(tau(f)) for f in range(1, N + 1)]
f_lift = next(f for f in range(32, 96) if zs[f - 1] > 1e-4)
meta = {
    "id": SHOT, "frames": N, "start_frame_in_film": FILM_START,
    "events": {"cut_in_pullout": 1, "lock": 16, "gummy_enters": 22, "slowmo_ramp_in": 25, "impact": 31,
               "slowmo_start": 31, "max_squash": f_maxsq, "liftoff": f_lift, "slowmo_end": 85, "realtime": 91,
               "second_landing": 96, "bonk": 106, "ear_accent": 121, "after_squash": 136, "ball_settle": F_PEAK,
               "ball_rest": F_REST, "rest": 165, "whip_start": 171, "end": N},
    "per_frame": {"tau_s": [round(tau(f), 6) for f in range(1, N + 1)],
                  "rate": [round(rate(f), 6) for f in range(1, N + 1)]},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
REPORT.update({"max_squash_frame": f_maxsq, "liftoff_frame": f_lift, "D0": round(D0, 4), "D1": round(D1, 4),
               "mirror_n": tuple(round(x, 3) for x in MIRROR_N),
               "mirror_yaw_from_wall_deg": round(math.degrees(math.acos(max(-1, min(1, V((MIRROR_N.x, MIRROR_N.y)).normalized().dot(V((WALL_N.x, WALL_N.y))))))), 2),
               "mirror_tilt_deg": round(math.degrees(math.asin(-MIRROR_N.z)), 2)})
print("[s03] REPORT", json.dumps(REPORT))
if ENV("S03_MATTE") == "1":       # circle-match measurement pass: ball+belt white emission, nothing else
    white = D.mat_emission("white", 1.0, name="matte_white")
    for o in sc.objects:
        if o.type == "MESH":
            if o in (ball, belt):
                D.assign(o, white)
            else:
                o.hide_render = True
    D.world_color("ink", 0.0)
    if ENV("S03_MATTE_NOMB") == "1":
        sc.render.use_motion_blur = False
for _nm in (n for n in ENV("S03_HIDE", "").split(",") if n):      # look-dev hook: hide objects by name prefix
    for o in sc.objects:
        if o.name.startswith(_nm):
            o.hide_render = True
sc.frame_set(1)
if REPORT_ONLY:
    sys.exit(0)
sc.cycles.transmission_bounces = int(ENV("S03_TRANS", str(sc.cycles.transmission_bounces)))
sc.cycles.blur_glossy = float(ENV("S03_FGLOSSY", str(sc.cycles.blur_glossy)))
sc.cycles.seed = int(ENV("S03_SEED", "0"))           # test hook only (noise-variance QA); finals use seed 0
sc.cycles.volume_bounces = int(ENV("S03_VOLB", str(sc.cycles.volume_bounces)))
D.finish(args, final_samples=int(ENV("S03_FSPP", "320")), final_threshold=float(ENV("S03_FTHR", "0.008")),
         frame_end=N, shot_name=SHOT)
