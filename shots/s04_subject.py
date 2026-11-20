"""S04 · s04_subject · "Frame the subject" · capability C4 (high-resolution textures) · film v2.
Film frames 601-780 = local 1-180 (bars 11-13, 20.0-26.0 s). GPU: run with CUDA_VISIBLE_DEVICES=6 or 7.

v2 changelog (docs/storyboard_v2.md section 2). Derived from shots/s04_every_dot.py (v1 round 2, frozen; its
round-2 notes are in that file and in docs/reports/s04_every_dot_fix_r2.json). The client asked to keep v1 and to
stop the push on the painting's main subject instead of magnifying to ~1 texel/px.
-------------------------------------------------------------------------------------------------------------
 1. f1-30 are bit-for-bit v1 (the S03->S04 whip cut is unchanged): the set, lights, materials, world, whip-in,
    room-wide, shutter, f-stop and focus are v1's. The wide still keys the camera target empty and the focus
    distance from v1's dot (aim_v1), which only fixes the empty's distance along the same view ray.
 2. New push target: the subject centre SUBJ_UV = (0.486, 0.633) (Blender UV, v from the bottom; the woman with
    the orange parasol is the visual centre, the girl in white just left of her), adjustable by <= 0.02
    (S04_DU / S04_DV, recorded in the meta; shipped: dv = +0.004 after the f180 test, centre (0.486, 0.637)).
    End framing square to the canvas at ZOOM_END = d0/d = x7.000 (d0 = |CAM0 - AIM| = 8.22 m, d_end = 1.17 m):
    frame height = 0.496 of the canvas height (spec 0.49 +- 0.02), ~6.1 texels of the 20000 px scan per pixel,
    so the pointillist dots read as a fine stipple. At rest the parasol tip and the girl's feet have 5.5 % / 5.6 %
    margins (spec >= 3 %); at the one-frame push peak (f136, x7.42) they are 2.8 % / 3.0 % of the frame
    height, still inside (meta end_framing.push_peak).
 3. Timing: push from f31 on the log distance with the v1 round-2 screen-space target path (the subject glides
    from its wide position to the frame centre over f31-F_TGT1, no roll, no counter-drift) while the view
    direction slerps onto the canvas normal (square by F_SLERP1). SETTLE arrival: the forward lobe is an
    ease_in_out_sine velocity lobe of (1 + OVER) of the log distance over f31-141; a sin^2 return lobe (OVER,
    f132-149) catches it, so the push passes the end framing ~f128, peaks on the f136 beat (film 736) at
    +6 % zoom (x7.42) and springs back to rest at f149 with zero velocity and zero acceleration (no dead stop).
    Every key from f149 on is identical (camera, target, DOF, shutter), so f150-180 are a static hold.
 4. Removed: the dot-pop, the pearl / orb, its emission and canvas light gain, the wash trim and the G1 bloom
    compositor (no orb, no glow, bloom off). The only emitter left is v1's practical lamp bulb inside its shade
    (part of the f1-30 set; off-frame from ~f55).
 5. Motion blur / shutter as v1: 1.0 -> 0.5 over the whip, dip to 0.35 over the fastest part of the push
    (re-timed to the v2 speed peak), back to 0.5. f-stop f/2 -> f/11 (log, ease_in_out_sine) during the push;
    the end is square to the canvas at f/11 with the focus on the canvas plane.
 6. --overscan (or S04_OVERSCAN=1): one still of the f180 camera for the finale's centre hex tile. Same camera
    position and orientation, horizontal sensor fit, sensor width x 2544/1920, 2544 x 2204 (final; preview
    1272 x 1102), so the central 1920 x 1080 (offset 312, 562) is exactly f180 and the image is the bounding box of
    the flat-top hexagon that circumscribes the 16:9 frame. The orange frame and the gold lip are hidden, the
    canvas plane is extended upward (the hex top is ~14 % of the canvas height above the painting). Above the
    painting the texture is a GENERATED pointillist foliage band (lead follow-up 2026-11-20, replacing the earlier
    mirror, which folded the trunks into V/diamond shapes):
    assets/paintings/derived/seurat_grande_jatte_<N>_topband.png from scripts/make_seurat_ext.py (deterministic,
    seed in the JSON next to it). It has the canopy's own dabs, colours and light/dark masses, no trunks or
    figures, and full coverage below the painted red/blue border, so the border is hidden too. The shader keeps the original JPEG for v <= 0.9365 (the whole f180 frame
    and everything below it: Blender's own decode, unchanged) and cross-fades to the band over v 0.9365-0.9395,
    where the band still holds the painting's own rows. The band image is mapped v' = (v - v_b0) / (v_b1 - v_b0)
    with EXTEND. In the band, generated patches cover the painting from v 0.945-0.960 (varying along u) to full
    coverage at v 0.971-0.9795. Only --overscan uses it; f_0001-0180 never load it.
    Writes renders/<mode>/s04_subject/overscan.png (16-bit in final). Interface: see "Usage" below.
 7. Meta renders/meta/s04_subject.json (written by every non-overscan run, also with --no-render): per-frame
    dist_m, zoom (d0/d, caption chip), px_per_texel; events; zoom_end; the end framing (canvas uv rectangle,
    margins, push peak); the overscan geometry; the measured final cost (cost_final.measured_final_s_per_frame,
    read by scripts/render_finals.py --film v2 for its plan); motion diagnostics.
 8. Build QA (docs/reports/s04_subject_build_v2.json): f1-30 camera keys bit-identical to v1 (f0-30: matrix, lens,
    f-stop, focus, shutter) and pixels within the GPU's run-to-run noise of v1's previews; f150-180 static (dither
    level, < 1/255); one smooth push lobe + the SETTLE lobe, no hitch; overscan crop vs f180 after a 1 px blur:
    preview mean 0.78/255, p99 3.06 (generated band), final 0.61 / 2.56 (measured on the superseded mirror
    still; the crop region shades identically with the band). Final cost ~7.1 s/frame on one H200 (GPU 6 alone),
    ~0.39 GPU-h for 180 frames in the queue's 3 jobs, + ~0.016 GPU-h for the overscan still (cap 0.45).

Usage (GPU 6 or 7 only; one Blender process at a time)
  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/s04_subject.py -- --mode preview
      [--frames 1-180:5] [--out DIR]          frames -> renders/<mode>/s04_subject/f_####.png (+ the meta)
  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/s04_subject.py -- --mode final
      --frames 180 --overscan [--out DIR]     the overscan still (what scripts/render_finals.py --film v2 runs)
  --overscan (or env S04_OVERSCAN=1) may stand anywhere after `--`; it is taken out of argv before dopa's parser.
  It always renders frame 180 only (another --frames value is ignored, with a note), at 2544 x 2204 16-bit in final
  (1272 x 1102 8-bit in preview, 636 x 551 in draft), to DIR/overscan.png (DIR = --out, else
  renders/<mode>/s04_subject) via DIR/_overscan_tmp/ (removed afterwards). It never writes f_####.png and never
  rewrites the meta, so f_0180.png stays untouched. Crop offset of the f180 frame: (312, 562) final, (156, 281)
  preview. It needs the generated band of its texture resolution: run `tools/venv/bin/python -I
  scripts/make_seurat_ext.py` once (CPU, ~2 min; writes all three resolutions); the script stops with that hint
  if the band is missing.

What the shot proves
--------------------
One unbroken camera move on ONE texture asset: a whip-in (continuing S03's whip right) lands on the candy gallery
(lemon/butter dollhouse corner, orange-framed Seurat, aqua-framed van Gogh, teal teddy armchair with a lilac plush
bunny, mint side table with a pink bowl of citrus, floor lamp, pink velvet rug, rubber duck, violet bench), then a
single x7 log-space dolly frames the heart of Seurat's "A Sunday on La Grande Jatte" (the 20000 x 13313 px scan in
final mode; drafts use the 2048 px and previews the 8192 px file): the woman with the orange parasol and the girl
in white, full figures, square to the canvas at f/11 with Linear filtering, every dot still visible. The still
hold (f150-180) is the first frame of the finale's pull-back (invisible match cut 780|781).

Timeline (local frames; global = local + 600)
  f1-10    whip-in: yaw +55 deg (left) -> 0 with ease_out_cubic from f1 (16.5 deg/f at f1, keyed from f0 so f1's
           motion blur continues the whip), shutter 1.0 -> 0.5; overshoot 1.2 deg past the wide at ~f11, at rest f25
  f11-30   the room-wide, one breath (pill pops in post at f16)
  f31-149  log push d = d0 (d_end/d0)^e(f): e = (1 + OVER) ease_in_out_sine(f31-141) - OVER sinramp(f132-149);
           view direction slerps to the canvas normal (smootherstep f31-F_SLERP1); the subject's screen position
           glides p_wide -> centre (smootherstep f31-F_TGT1); f-stop 2 -> 11 (log); shutter dips to 0.35
  ~f128    the end framing is first reached (x7.0) while still moving
  f136     beat (film 736): the push peaks at x7.42 (+6 %), then the SETTLE return
  f149     at rest, zero velocity and acceleration (every key from here on is identical)
  f150-180 static hold on the subject (bit-identical frames); f180 = finale f1

Deviations from the storyboard (tunable visual parameters only; hits, framing rules and proofs kept)
  * SETTLE overshoot is +6 % in image scale (zoom x7.42 -> x7.00), i.e. 2.9 % of the log-distance move: 6 % of
    the log move would be +12 % in scale and would cut the parasol tip at the peak. At the peak frame the
    parasol-tip margin is 2.8 % (>= 3 % is met at the end framing; OVER = 0.0355 would give 3.0 % at +5.5 %).
  * The SETTLE arrival is shaped in closed form (velocity lobes) instead of D.spring, so the settle ends exactly
    at f149 (a spring never stops) and f150-180 can be bit-identical.
  * Overscan extension: a generated foliage band (scripts/make_seurat_ext.py) instead of the storyboard's MIRROR
    texture extension. Any mirror repeats the trunks as chevrons: a plain MIRROR at the canvas edge also doubles
    the red/blue painted border, and the build's stretched single mirror about the border still folded the trunks
    into V/diamond shapes (rejected by the lead). The painted top border is covered by the band as well.
  * v1 deviations that still apply (set, lights, materials): see shots/s04_every_dot.py.

Env vars (debug / look-dev only; defaults are the shipped look): S04_CAM=top|chair|table|mag|side -> static debug
camera; S04_TEX=<file>; S04_DU / S04_DV (subject centre adjustment, uv); S04_ZOOM (end zoom, default 7.0);
S04_OVERSCAN=1 (same as --overscan); S04_KEY / S04_FILL / S04_WASH / S04_WASH_COL / S04_WORLD / S04_FLOOR_LIFT /
S04_LAMP (v1 look-dev knobs, defaults = v1).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

SHOT = "s04_subject"
N_FRAMES = 180
FILM_START = 601

# --overscan (or S04_OVERSCAN=1): render only the f180 overscan still for the finale's centre hex tile.
# D.parse_args() does not know the flag, so it is taken out of argv first.
OVERSCAN = os.environ.get("S04_OVERSCAN", "0").strip() not in ("", "0")
if "--overscan" in sys.argv:
    sys.argv.remove("--overscan")
    OVERSCAN = True
OVS_RES = (2544, 2204)          # bounding box of the flat-top hexagon circumscribing the 1920 x 1080 frame

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=192, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=8,
               caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)
D.setup_color(exposure=-0.1)
if OVERSCAN:
    D.setup_output(res=OVS_RES)
else:
    D.setup_output()
sc = bpy.context.scene
sc.frame_end = N_FRAMES
sc.render.use_simplify = False  # never limit texture size (the whole point of the shot)


def envf(name, default):
    return float(os.environ.get(name, default))


# ----------------------------------------------------------------------------------------------------------
# Seurat texture by mode
# ----------------------------------------------------------------------------------------------------------
TEX = {"draft": "seurat_grande_jatte_2048.jpg", "preview": "seurat_grande_jatte_8192.jpg",
       "final": "seurat_grande_jatte_20000.jpg"}[args.mode]
TEX = os.environ.get("S04_TEX", TEX)
TEX_PATH = os.path.join(D.ASSETS, "paintings", TEX)
print(f"[s04] Seurat texture: {TEX}", flush=True)

# ----------------------------------------------------------------------------------------------------------
# Canvas geometry (metres). The plane's u runs along U_HAT (not mirrored), v along +Z; normal N_HAT.
# ----------------------------------------------------------------------------------------------------------
IMG_W, IMG_H = 20000, 13313
CANVAS_W = 1.8
CANVAS_H = CANVAS_W * IMG_H / IMG_W            # 1.19817 m
TEXEL = CANVAS_W / IMG_W                       # 0.09 mm per texel of the 20000 px scan
CANVAS_C = Vector((-1.612, 1.117, 1.45))
R2 = math.sqrt(0.5)
U_HAT = Vector((R2, R2, 0.0))
N_HAT = Vector((R2, -R2, 0.0))
Z_HAT = Vector((0.0, 0.0, 1.0))


def canvas_pt(u, v, off=0.0):
    return CANVAS_C + (u - 0.5) * CANVAS_W * U_HAT + (v - 0.5) * CANVAS_H * Z_HAT + off * N_HAT


V1_DOT_UV = (0.27375, 0.56537)                 # v1's push target (painted white disc): wide keys only
V1_DOT = canvas_pt(*V1_DOT_UV)
V1_DRIFT = 0.0005

SUBJ_UV0 = (0.486, 0.633)                      # storyboard_v2: subject centre (woman with the orange parasol)
SUBJ_DUV = (envf("S04_DU", 0.0), envf("S04_DV", 0.004))  # framing adjustment after the f180 test (<= 0.02)
assert abs(SUBJ_DUV[0]) <= 0.02 and abs(SUBJ_DUV[1]) <= 0.02, "subject centre may move by <= 0.02 only"
SUBJ_UV = (SUBJ_UV0[0] + SUBJ_DUV[0], SUBJ_UV0[1] + SUBJ_DUV[1])
AIM = canvas_pt(*SUBJ_UV)                      # push target on the canvas plane (no hold drift in v2)
# measured on the scan (8192 px, v from the bottom): the parasol's top and the girl's feet (framing margins)
PARASOL_TIP_UV = (0.4977, 0.8580)
GIRL_FEET_UV = (0.4566, 0.4167)
# overscan extension: the generated foliage band above the painting (scripts/make_seurat_ext.py)
EXT_JSON = os.path.join(D.ASSETS, "paintings", "derived", "seurat_grande_jatte_ext.json")
OVS_EXT_TOP = 0.20                             # the overscan canvas plane is extended upward by this (canvas h)

# ----------------------------------------------------------------------------------------------------------
# Camera path (closed-form functions of the frame; also used for meta)
# ----------------------------------------------------------------------------------------------------------
LENS, SENSOR = 40.0, 36.0
FOCAL_PX = 1920.0 * LENS / SENSOR             # 2133.3 px at 1920 width
CAM0 = Vector((0.90, -6.60, 3.00))
TGT0 = Vector((-0.20, 0.90, 1.00))
WHIP_DEG, WHIP_F = 55.0, 10.0
OVERSHOOT_DEG = 1.2                            # v1 round 2: 1.5 -> 1.2 with a longer tail (return <= ~6 px/f)
BUMP_F = 24.0                                  # overshoot bump spans f1-25
BUMP_MAX = (3 / 7) ** 3 * (4 / 7) ** 4         # max of u^3 (1-u)^4 (at u = 3/7, f11.3)

F_PUSH0 = 31                                   # push starts (beat 3, film 631)
F_TGT1 = 88                                    # the subject reaches the frame centre (screen-space glide)
F_SLERP1 = 124                                 # camera square to the canvas
F_FWD1 = 141                                   # forward ease_in_out_sine lobe ends
F_RET0 = 132                                   # SETTLE return lobe starts
F_LOCK = 149                                   # last moving key: every key from here on is identical
F_PEAK_BEAT = 136                              # the push peaks on this beat (film 736)
OVER = 0.038                                   # forward lobe = 1 + OVER of the log distance (peak +6 % zoom)
F_FS0, F_FS1 = 70, 124                         # f-stop 2 -> 11 (log, ease_in_out_sine)
F_FOCUS1 = 46                                  # focus hand-off v1 dot depth -> subject depth (f30-46)
F_SH = (58, 66, 106, 116)                      # shutter 0.5 -> 0.35 over F_SH[0..1], back over F_SH[2..3]


def aim_v1(f):
    """v1's push target incl. its hold-drift offset (-0.25 mm along u before f106). Used only for f <= 31 so the
    target empty and the focus distance of the wide are bit-for-bit v1."""
    return V1_DOT + (-0.5 * V1_DRIFT + V1_DRIFT * D.prog(f, 106, 165)) * U_HAT


D0 = (CAM0 - AIM).length                      # 8.22 m
DIR0 = (CAM0 - AIM).normalized()
ZOOM_END = envf("S04_ZOOM", 7.0)
D_END = D0 / ZOOM_END                          # camera-canvas distance at rest
FRAME_H = D_END * (SENSOR * 1080.0 / 1920.0) / LENS          # visible canvas height at rest (m)
FRAME_H_FRAC = FRAME_H / CANVAS_H
assert 0.47 <= FRAME_H_FRAC <= 0.51, f"end framing {FRAME_H_FRAC:.4f} of the canvas height is outside 0.49 +- 0.02"


def slerp(a, b, t):
    a, b = a.normalized(), b.normalized()
    om = math.acos(max(-1.0, min(1.0, a.dot(b))))
    if om < 1e-9:
        return a.copy()
    so = math.sin(om)
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / so


def push_e(f):
    """Log-distance progress with the SETTLE arrival. Velocity = an ease_in_out_sine lobe carrying 1 + OVER over
    f31-141 minus a sin^2 lobe carrying OVER over f132-149: past the end framing ~f128, peak +6 % zoom on f136,
    back to rest on f149 with zero velocity and zero acceleration. Exactly 0 up to f31 and exactly 1 from f149."""
    if f <= F_PUSH0:
        return 0.0
    if f >= F_LOCK:
        return 1.0
    p2 = D.prog(f, F_RET0, F_LOCK)
    return ((1.0 + OVER) * D.ease_in_out_sine(D.prog(f, F_PUSH0, F_FWD1))
            - OVER * (p2 - math.sin(2.0 * math.pi * p2) / (2.0 * math.pi)))


def dist(f):
    return D0 * (D_END / D0) ** push_e(f)


def cam_pos(f):
    f = min(f, F_LOCK)
    if f <= F_PUSH0:
        return CAM0.copy()
    s = D.smootherstep(D.prog(f, F_PUSH0, F_SLERP1))
    return AIM + dist(f) * slerp(DIR0, N_HAT, s)


def psi(f):
    """Whip yaw offset in degrees (+ = rotated left/CCW). ease_out_cubic over 10 f from f1 (16.5 deg/f at f1)
    plus a smooth overshoot bump u^3 (1-u)^4 over f1-25 (peak f11.3, gone by f25). (v1, unchanged)"""
    if f < 1:
        return WHIP_DEG + 3 * WHIP_DEG / WHIP_F * (1 - f)   # continue the whip for f1's motion blur
    main = WHIP_DEG * (1 - D.ease_out_cubic((f - 1) / WHIP_F))
    u = (f - 1) / BUMP_F
    bump = (u ** 3 * (1 - u) ** 4) / BUMP_MAX if 0 < u < 1 else 0.0
    return main - OVERSHOOT_DEG * bump


def basis(fwd):
    right = fwd.cross(Z_HAT).normalized()
    return right, right.cross(fwd)


def project_dir(fwd, c, p):
    """Screen offset (px from the frame centre, x right, y up) of world point p for a no-roll camera at c."""
    right, up = basis(fwd)
    v = p - c
    z = v.dot(fwd)
    return FOCAL_PX * v.dot(right) / z, FOCAL_PX * v.dot(up) / z


def _dir(yaw, pitch):
    return Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))


def fwd_for_screen(c, p, sx, sy):
    """No-roll view direction (up = +Z) that puts world point p at screen offset (sx, sy) px. Newton on yaw/pitch."""
    v = (p - c).normalized()
    yaw, pitch = math.atan2(v.y, v.x), math.asin(max(-1.0, min(1.0, v.z)))
    for _ in range(12):
        x0, y0 = project_dir(_dir(yaw, pitch), c, p)
        ex, ey = x0 - sx, y0 - sy
        if abs(ex) < 1e-6 and abs(ey) < 1e-6:
            break
        h = 1e-6
        xa, ya = project_dir(_dir(yaw + h, pitch), c, p)
        xb, yb = project_dir(_dir(yaw, pitch + h), c, p)
        j00, j01, j10, j11 = (xa - x0) / h, (xb - x0) / h, (ya - y0) / h, (yb - y0) / h
        det = j00 * j11 - j01 * j10
        yaw -= (j11 * ex - j01 * ey) / det
        pitch -= (-j10 * ex + j00 * ey) / det
    return _dir(yaw, pitch)


S_WIDE = project_dir((TGT0 - CAM0).normalized(), CAM0, AIM)     # the subject's screen offset in the wide


def view_fwd(f):
    f = min(f, F_LOCK)
    c = cam_pos(f)
    if f <= F_PUSH0:
        fwd = (TGT0 - c).normalized()
    else:   # the subject glides p_wide -> frame centre on a straight screen path (C2, no counter-drift)
        k = 1.0 - D.smootherstep(D.prog(f, F_PUSH0, F_TGT1))
        fwd = fwd_for_screen(c, AIM, S_WIDE[0] * k, S_WIDE[1] * k)
    a = math.radians(psi(f)) if f < 1 + BUMP_F + 1 else 0.0
    if a:
        ca, sa = math.cos(a), math.sin(a)
        fwd = Vector((fwd.x * ca - fwd.y * sa, fwd.x * sa + fwd.y * ca, fwd.z))
    return fwd


def tgt_pos(f):
    c = cam_pos(f)
    if f <= F_PUSH0:   # v1 verbatim: the empty sits on the same view ray at v1's dot distance
        return c + view_fwd(f) * (aim_v1(f) - c).length
    return c + view_fwd(f) * (AIM - c).length


def fstop(f):
    f = min(f, F_LOCK)
    return 2.0 * (11.0 / 2.0) ** D.ease_in_out_sine(D.prog(f, F_FS0, F_FS1))


def shutter(f):
    f = min(f, F_LOCK)
    s = 1.0 - 0.5 * D.ease_in_out_sine(D.prog(f, 1, 10))
    return s - 0.15 * (D.ease_in_out_sine(D.prog(f, F_SH[0], F_SH[1])) - D.ease_in_out_sine(D.prog(f, F_SH[2], F_SH[3])))


def focus(f):
    """Depth of the push target on the view axis (canvas plane at rest). f <= 30: v1's dot (bit-for-bit wide);
    f30-46 the focus point slides to the subject (the camera is at rest until f31, so this is a sub-pixel rack)."""
    f = min(f, F_LOCK)
    c = cam_pos(f)
    if f <= 30:
        return (aim_v1(f) - c).dot(view_fwd(f))
    w = D.smoothstep(D.prog(f, 30, F_FOCUS1))
    return (aim_v1(f).lerp(AIM, w) - c).dot(view_fwd(f))


# ----------------------------------------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------------------------------------
def principled(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def sock(sockets, ident):
    return next(s for s in sockets if s.identifier == ident)


def base_color_insert(mat, node, in_sock, out_sock):
    """Insert `node` between whatever feeds Principled 'Base Color' and the socket."""
    nt = mat.node_tree
    p = principled(mat)
    lk = [lk for lk in nt.links if lk.to_socket == p.inputs["Base Color"]][0]
    src = lk.from_socket
    nt.links.remove(lk)
    nt.links.new(src, in_sock)
    nt.links.new(out_sock, p.inputs["Base Color"])
    return node


def huesat(mat, hue=0.5, sat=1.0, val=1.0):
    hs = mat.node_tree.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Hue"].default_value = hue
    hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = val
    base_color_insert(mat, hs, hs.inputs["Color"], hs.outputs["Color"])
    return hs


def recolor(mat, name, hue=0.5, sat=1.0, val=1.0):
    """Copy of an image-textured material with a hue/saturation/value shift on its albedo."""
    m = mat.copy()
    m.name = name
    huesat(m, hue, sat, val)
    return m


# floor: pastel peach wood (screen toward a pink-peach keeps the grain; the 4K oak alone reads dark brown)
m_floor = D.polyhaven_texture("wood_floor", "4k", uv_scale=0.5)
_scr = m_floor.node_tree.nodes.new("ShaderNodeMix")
_scr.data_type = "RGBA"
_scr.blend_type = "SCREEN"
_scr.inputs["Factor"].default_value = envf("S04_FLOOR_LIFT", 0.75)
sock(_scr.inputs, "B_Color").default_value = D.col(os.environ.get("S04_FLOOR_COL", "#FFCDB6"))
base_color_insert(m_floor, _scr, sock(_scr.inputs, "A_Color"), sock(_scr.outputs, "Result_Color"))
m_lemon = D.mat_clay("lemon")
m_butter = D.mat_clay("butter")
m_seurat = D.mat_image(TEX_PATH, name="seurat", rough=0.55, interpolation="Linear")
principled(m_seurat).inputs["Specular IOR Level"].default_value = 0.2
SEURAT_IMG = next(nd for nd in m_seurat.node_tree.nodes if nd.type == "TEX_IMAGE").image
m_vangogh = D.mat_image(os.path.join(D.ASSETS, "paintings", "vangogh_wheat_field_cypresses_met.jpg"),
                        name="vangogh", rough=0.6, interpolation="Linear")
principled(m_vangogh).inputs["Specular IOR Level"].default_value = 0.2
m_orange = D.mat_candy("orange")
m_aqua = D.mat_candy("aqua")
m_gold = D.mat_metal("gold", rough=0.25)
# teal teddy plaid (storyboard): multiply toward teal, then saturate (the scan's grey bands read grey otherwise)
m_teddy = D.polyhaven_texture("curly_teddy_checkered", "8k", uv_scale=1.5, tint="#7EDFD6", tint_mix=0.55)
huesat(m_teddy, 0.5, 1.5, 1.15)
m_plush = D.mat_velvet("lilac")
principled(m_plush).inputs["Sheen Roughness"].default_value = 0.2
principled(m_plush).inputs["Sheen Tint"].default_value = D.mix_col("white", "lilac", 0.15)
m_mint = D.mat_candy("mint")
m_pink = D.mat_candy("pink")
# pink velvet rug: Poly Haven velour_velvet (raspberry) re-hued to candy pink; pile from its normal/roughness maps
m_rug = D.polyhaven_texture("velour_velvet", "4k", name="rug_velvet", uv_scale=1.5)
huesat(m_rug, 0.468, 1.0, 2.3)
_pr = principled(m_rug)
_pr.inputs["Sheen Weight"].default_value = 1.0
_pr.inputs["Sheen Roughness"].default_value = 0.3
_pr.inputs["Sheen Tint"].default_value = D.mix_col("white", "pink", 0.3)
_pr.inputs["Specular IOR Level"].default_value = 0.25
m_cream = D.mat_clay("cream")
m_bulb = D.mat_emission("#FFE9C7", 6.0)
# lamp shade: cream clay + translucent (the bulb inside makes it glow)
m_shade = D.mat_clay("cream", name="shade_cream")
_snt = m_shade.node_tree
_tr = _snt.nodes.new("ShaderNodeBsdfTranslucent")
_tr.inputs["Color"].default_value = D.col("#FFE7C4")
_sm = _snt.nodes.new("ShaderNodeMixShader")
_sm.inputs["Fac"].default_value = 0.45
_snt.links.new(principled(m_shade).outputs[0], _sm.inputs[1])
_snt.links.new(_tr.outputs[0], _sm.inputs[2])
_snt.links.new(_sm.outputs[0], _snt.nodes["Material Output"].inputs["Surface"])

# ----------------------------------------------------------------------------------------------------------
# Shot-local geometry helpers
# ----------------------------------------------------------------------------------------------------------


def lathe(name, profile, mat=None, segments=96, subsurf=2, location=(0, 0, 0)):
    """Surface of revolution about +Z from an (r, z) profile; ends at r=0 are welded."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=segments,
                   use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = D._mesh_object(name, bm, mat)
    if subsurf:
        s = ob.modifiers.new("Smooth", "SUBSURF")
        s.levels = subsurf
        s.render_levels = subsurf
    ob.location = location
    return ob


def open_cone(name, r_bot, r_top, h, mat=None, thickness=0.008, location=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=96, radius1=r_bot, radius2=r_top,
                          depth=h)
    ob = D._mesh_object(name, bm, mat)
    so = ob.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = thickness
    so.offset = 0.0
    bv = ob.modifiers.new("Bevel", "BEVEL")
    bv.width = thickness * 0.45
    bv.segments = 3
    bv.limit_method = "ANGLE"
    ob.location = location
    return ob


# ----------------------------------------------------------------------------------------------------------
# Room
# ----------------------------------------------------------------------------------------------------------
room = D.diorama_corner("Room", size=4.0, height=2.8, floor_mat=m_floor, left_mat=m_lemon, right_mat=m_butter,
                        rot_z=45)

# Seurat on the lemon wall (7 cm proud), orange candy frame, gold lip
canvas = D.plane("Seurat", (CANVAS_W, CANVAS_H), location=tuple(CANVAS_C), rotation=(90, 0, 45), mat=m_seurat)
frame = D.rounded_box("Frame", (1.98, 0.07, 1.38), 0.03, location=tuple(CANVAS_C - 0.036 * N_HAT),
                      rotation=(0, 0, 45), mat=m_orange)
LIP_R = 0.008
for nm, (u, v), horiz in (("LipTop", (0.5, 1.0), True), ("LipBot", (0.5, 0.0), True),
                          ("LipL", (0.0, 0.5), False), ("LipR", (1.0, 0.5), False)):
    length = (CANVAS_W if horiz else CANVAS_H) + 2 * LIP_R
    D.capsule(nm, LIP_R, length, location=tuple(canvas_pt(u, v)), rotation=(0, 90, 45) if horiz else (0, 0, 45),
              mat=m_gold, segments=32, rings=16)

# van Gogh on the butter wall: crop the Met photo's black surround via UVs
VG_PX = (110, 3866, 125, 3083)                 # painted area in the 4000x3184 photo (x0, x1, y0, y1)
VG_U0, VG_U1 = VG_PX[0] / 4000, VG_PX[1] / 4000
VG_V0, VG_V1 = 1 - VG_PX[3] / 3184, 1 - VG_PX[2] / 3184
VG_W = 0.8
VG_H = VG_W * (VG_PX[3] - VG_PX[2]) / (VG_PX[1] - VG_PX[0])
VG_C = Vector((1.803, 0.954, 1.50))
VG_N = Vector((-R2, -R2, 0.0))
vg = D.plane("VanGogh", (VG_W, VG_H), location=tuple(VG_C), rotation=(90, 0, -45), mat=m_vangogh)
for lp in vg.data.uv_layers.active.data:
    u, v = lp.uv
    lp.uv = (VG_U0 + u * (VG_U1 - VG_U0), VG_V0 + v * (VG_V1 - VG_V0))
D.rounded_box("VanGoghFrame", (VG_W + 0.10, 0.05, VG_H + 0.10), 0.02, location=tuple(VG_C - 0.026 * VG_N),
              rotation=(0, 0, -45), mat=m_aqua)

# Teddy armchair under the Seurat (front faces N_HAT)
CHAIR_C = Vector((-1.223, 0.728, 0.0))
chair = D.empty("Armchair", tuple(CHAIR_C))
chair.rotation_euler = (0, 0, math.radians(45))
bpy.context.view_layer.update()
for nm, size, loc, rad in (("Seat", (0.80, 0.70, 0.40), (0, -0.02, 0), 0.10),
                           ("Back", (1.04, 0.22, 0.95), (0, 0.25, 0), 0.10),
                           ("ArmL", (0.18, 0.70, 0.58), (-0.44, -0.02, 0), 0.08),
                           ("ArmR", (0.18, 0.70, 0.58), (0.44, -0.02, 0), 0.08)):
    p = D.rounded_box("Chair" + nm, size, rad, location=loc, mat=m_teddy, soft=True, base_at_zero=True)
    p.parent = chair

# Lilac plush bunny on the seat
bunny = D.stanford_bunny("PlushBunny", 0.40, mat=m_plush)
bunny.parent = chair
bunny.location = (0.0, -0.06, 0.40)
bunny.rotation_euler = (0, 0, math.radians(envf("S04_BUNNY_YAW", 90)))

# Mint side table with a pink bowl of fruit and a magnifier
TABLE = Vector((-0.55, 0.25, 0.0))
D.cylinder("TableBase", 0.16, 0.03, location=tuple(TABLE), mat=m_mint, bevel=0.012, base_at_zero=True)
D.capsule("TableLeg", 0.03, 0.58, location=tuple(TABLE + Vector((0, 0, 0.29))), mat=m_mint)
D.cylinder("TableTop", 0.28, 0.04, location=tuple(TABLE + Vector((0, 0, 0.58))), mat=m_mint, bevel=0.015)
TOP_Z = 0.60
BOWL_S = 1.15
BOWL_C = TABLE + Vector((0.03, 0.07, TOP_Z))
bowl = lathe("Bowl", [(r * BOWL_S, z * BOWL_S) for r, z in (
    (0.0, 0.0), (0.055, 0.0), (0.064, 0.006), (0.095, 0.024), (0.118, 0.048), (0.129, 0.07), (0.130, 0.078),
    (0.124, 0.081), (0.117, 0.072), (0.104, 0.046), (0.075, 0.026), (0.035, 0.016), (0.0, 0.014))],
    mat=m_pink, location=tuple(BOWL_C))


def recenter(ob):
    """Move the mesh's bbox centre to its origin (glTF fruit pivots sit at their base)."""
    cs = [v.co for v in ob.data.vertices]
    mn = Vector([min(c[i] for c in cs) for i in range(3)])
    mx = Vector([max(c[i] for c in cs) for i in range(3)])
    ob.data.transform(Matrix.Translation(-(mn + mx) / 2))
    return (mx - mn) / 2


_, lime_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "food_lime_01", "food_lime_01_2k.gltf"))
_, kiwi_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "food_kiwi_01", "food_kiwi_01_2k.gltf"))
FRUIT_S = 1.25
lime_src, kiwi_src = lime_meshes[0], kiwi_meshes[0]
recenter(lime_src)
recenter(kiwi_src)
m_lime = lime_src.data.materials[0]
fruit_mats = {"lime": recolor(m_lime, "fruit_lime", hue=0.5, sat=1.15, val=1.8), "kiwi": kiwi_src.data.materials[0],
              "lemon": recolor(m_lime, "fruit_lemon", hue=0.414, sat=1.1, val=3.8),    # citrus re-coloured
              "orange": recolor(m_lime, "fruit_orange", hue=0.344, sat=1.15, val=3.6)}  # from the lime scan
fruit_layout = [  # (kind, scale, dx, dy, centre z above the bowl base, rx, ry, rz)
    ("lemon", 1.1, 0.002, -0.054, 0.060, 90, 0, 160), ("lime", 1.0, -0.060, 0.0, 0.058, 90, 0, 115),
    ("lime", 1.0, 0.060, 0.004, 0.058, 90, 0, 70), ("kiwi", 1.0, 0.0, 0.052, 0.066, 90, 0, 15),
    ("orange", 1.25, 0.0, -0.004, 0.122, 70, 10, 30)]
first = {"lime": lime_src, "kiwi": kiwi_src}
for kind, s, dx, dy, dz, rx, ry, rz in fruit_layout:
    src = kiwi_src if kind == "kiwi" else lime_src
    if first.get(kind) is not None and kind in ("lime", "kiwi"):
        ob = first.pop(kind)
    else:
        ob = D.link(src.copy())
        ob.data = src.data.copy()
    ob.parent = None
    ob.data.materials[0] = fruit_mats[kind]
    ob.location = tuple(BOWL_C + Vector((dx, dy, dz)))
    ob.rotation_euler = tuple(math.radians(a) for a in (rx, ry, rz))
    ob.scale = (FRUIT_S * s,) * 3

# magnifier lying flat (set dressing only): pink handle, gold rim, closed ellipsoid glass lens
# (the glTF lens is four open shells, which renders dark as refractive glass)
mag_root, mag_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "magnifying_glass_01",
                                                  "magnifying_glass_01_4k.gltf"))
mag = mag_meshes[0]
_bm = bmesh.new()
_bm.from_mesh(mag.data)
bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if f.material_index == 1], context="FACES")
_bm.to_mesh(mag.data)
_bm.free()
mag.data.materials.append(m_pink)                     # slot 2: handle
for poly in mag.data.polygons:
    if poly.center.z < 0.135:
        poly.material_index = 2
mag.data.materials[0] = m_gold                         # rim
lens = D.sphere("MagLens", 0.0625, location=(0, 0, 0.2055), mat=D.mat_glass("white"), segments=64, rings=32)
lens.scale = (1.0, 0.14, 1.0)
lens.parent = mag
lens.visible_shadow = False   # caustics are off: a shadow-casting lens would leave the table under it black
mag_root.location = tuple(TABLE + Vector((-0.17, -0.17, TOP_Z + 0.0134)))
mag_root.rotation_euler = (math.radians(90), 0, math.radians(110))

# Floor lamp in the back corner: translucent shade glowing from the bulb inside
LAMP = Vector((0.0, 2.05, 0.0))
D.cylinder("LampBase", 0.16, 0.035, location=tuple(LAMP), mat=m_gold, bevel=0.012, base_at_zero=True)
D.cylinder("LampPole", 0.02, 1.5, location=tuple(LAMP + Vector((0, 0, 0.78))), mat=m_gold, bevel=0.0)
open_cone("LampShade", 0.25, 0.15, 0.30, mat=m_shade, location=tuple(LAMP + Vector((0, 0, 1.62))))
D.sphere("LampBulb", 0.05, location=tuple(LAMP + Vector((0, 0, 1.56))), mat=m_bulb)
lamp_glow = D.light("POINT", "LampGlow", tuple(LAMP + Vector((0, 0, 1.56))), None, power=envf("S04_LAMP", 35),
                    color="#FFE2B8", radius=0.05)

# Pink velvet rug (3.5 cm, soft bevel) and the rubber duck (re-hued to a classic lemon duck, orange beak)
RUG_T = 0.035
D.cylinder("Rug", 1.0, RUG_T, location=(-0.2, -0.2, 0.0), mat=m_rug, bevel=0.014, base_at_zero=True)
duck_root, duck_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "rubber_duck_toy",
                                                    "rubber_duck_toy_4k.gltf"))
duck = duck_meshes[0]
duck.data.materials[0] = recolor(duck.data.materials[0], "duck_lemon", hue=0.545, sat=1.0, val=1.12)
DUCK_S = envf("S04_DUCK_S", 1.35)
duck_root.location = (envf("S04_DUCK_X", 0.50), envf("S04_DUCK_Y", -0.62), RUG_T)
duck_root.scale = (DUCK_S, DUCK_S, DUCK_S)
duck_root.rotation_euler = (0, 0, math.radians(envf("S04_DUCK_YAW", 240)))   # beak (local -Y) toward the Seurat

# Violet velvet gallery bench under the van Gogh (complementary accent on the empty right side)
m_bench = D.mat_velvet("violet")
BENCH = Vector((1.38, 0.62, 0.0))
bench = D.empty("Bench", tuple(BENCH))
bench.rotation_euler = (0, 0, math.radians(135))
cush = D.rounded_box("BenchCushion", (1.10, 0.40, 0.20), 0.08, location=(0, 0, 0.22), mat=m_bench, soft=True,
                     base_at_zero=True)
cush.parent = bench
for i, (lx, ly) in enumerate(((-0.46, -0.13), (0.46, -0.13), (-0.46, 0.13), (0.46, 0.13))):
    leg = D.capsule(f"BenchLeg{i}", 0.028, 0.26, location=(lx, ly, 0.13), mat=m_gold, segments=32, rings=16)
    leg.parent = bench

# Off-frame "foyer" wall to the left of the room: only seen during the whip-in (f1-8). A white candy dado rail at
# z 1.2 lands at ~52 % frame height on f1 (continuing S03's skirting streak); watermelon-pink clay above, rose
# below; big candy panels so their hues survive ~600 px streaks. The wall reaches azimuth ~123.5 deg (the wide's
# left frame edge is at 122.5 deg), which shrinks the cream gap before the room's left wall.
_az = math.radians(158.0)
_fc = Vector((0.90 + 6.6 * math.cos(_az), -6.60 + 6.6 * math.sin(_az), 0.0))
_face = math.degrees(_az) - 180.0 + 90.0            # box local +y faces away from the camera, +x toward the room
foyer = D.empty("Foyer", tuple(_fc))
foyer.rotation_euler = (0, 0, math.radians(_face))
FY_X0, FY_X1, RAIL_Z = -3.75, 4.15, 1.2
_fw_w, _fw_cx = FY_X1 - FY_X0, (FY_X0 + FY_X1) / 2
for nm, z0, z1, colr in (("FoyerWallLow", -1.5, RAIL_Z, os.environ.get("S04_FY_LOW", "#E79BB8")),
                              ("FoyerWallUp", RAIL_Z, 3.5, os.environ.get("S04_FY_UP", "#FF8FA6"))):
    w = D.rounded_box(nm, (_fw_w, 0.2, z1 - z0), 0.04, location=(_fw_cx, 0.1, z0), mat=D.mat_clay(colr),
                      base_at_zero=True)
    w.parent = foyer
_rail = D.rounded_box("FoyerRail", (_fw_w, 0.10, 0.09), 0.03, location=(_fw_cx, -0.05, RAIL_Z - 0.045),
                      mat=D.mat_candy("white"), base_at_zero=True)
_rail.parent = foyer
for i, (fx, fz, w, h, c, art) in enumerate(((-2.75, 2.15, 1.65, 1.28, "aqua", "butter"),
                                            (-0.55, 2.25, 1.35, 1.65, "lemon", "sky"),
                                            (1.75, 2.10, 1.95, 1.20, "violet", "blush"),
                                            (3.75, 2.20, 1.20, 1.50, "mint", "lemon"))):
    fr = D.rounded_box(f"FoyerFrame{i}", (w, 0.06, h), 0.03, location=(fx, -0.03, fz), mat=D.mat_candy(c))
    fr.parent = foyer
    cv = D.rounded_box(f"FoyerArt{i}", (w * 0.78, 0.07, h * 0.74), 0.01, location=(fx, -0.035, fz),
                       mat=D.mat_clay(art))
    cv.parent = foyer
_bb = D.rounded_box("FoyerBase", (_fw_w, 0.06, 0.16), 0.02, location=(_fw_cx, -0.02, 0.0),
                    mat=D.mat_candy("#F07CA2"), base_at_zero=True)
_bb.parent = foyer

# ----------------------------------------------------------------------------------------------------------
# Lights and world: warm window key (upper left), cool fill (right), gallery wash spot on the Seurat.
# Key, fill and lamp are light-linked to EXCLUDE the canvas, so only the wash (+ world, bounce) lights it.
# ----------------------------------------------------------------------------------------------------------
KEY_W = envf("S04_KEY", 160)
FILL_W = envf("S04_FILL", 60)
WASH_W = envf("S04_WASH", 1510)
WORLD_K = envf("S04_WORLD", 0.08)
WASH_COL = os.environ.get("S04_WASH_COL", "#DFEFF4")
KEY_POS = Vector((envf("S04_KEY_X", -3.4), envf("S04_KEY_Y", -1.6), envf("S04_KEY_Z", 4.4)))
KEY_TGT = Vector((envf("S04_KEY_TX", -0.7), envf("S04_KEY_TY", 0.5), envf("S04_KEY_TZ", 0.5)))
key = D.light("AREA", "KeyWindow", tuple(KEY_POS), tuple(KEY_TGT), power=KEY_W,
              color=os.environ.get("S04_KEY_COL", "#FFF3E6"), size=2.0, size_y=1.4)
key.data.spread = math.radians(envf("S04_KEY_SPREAD", 95))
FILL_POS = Vector((envf("S04_FILL_X", 3.0), envf("S04_FILL_Y", -4.6), envf("S04_FILL_Z", 2.6)))
fill = D.light("AREA", "FillCool", tuple(FILL_POS), (0.6, 1.0, 1.0), power=FILL_W,
               color=os.environ.get("S04_FILL_COL", "#D9E3FF"), size=3.0)
WASH_POS = CANVAS_C + 6.0 * (math.cos(math.radians(20)) * N_HAT + math.sin(math.radians(20)) * Z_HAT)
wash = D.light("SPOT", "Wash", tuple(WASH_POS), tuple(CANVAS_C), power=WASH_W, color=WASH_COL, radius=0.25,
               spot_deg=44, blend=0.7)
D.light("SPOT", "FoyerLight", (-2.0, -6.2, 3.6), tuple(_fc + Vector((0, 0, 1.2))), power=envf("S04_FOYER", 1100),
        color="#FFF4EA", radius=0.4, spot_deg=75, blend=0.6)
not_canvas = bpy.data.collections.new("NotOnCanvas")
not_canvas.objects.link(canvas)
for lt in (key, fill, lamp_glow):
    lt.light_linking.receiver_collection = not_canvas
for co in not_canvas.collection_objects:
    co.light_linking.link_state = "EXCLUDE"
SKY = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
if not os.path.exists(SKY):
    print("[s04] WARNING: candy_sky_nosun_4k.hdr missing, falling back to colorful_studio", flush=True)
    SKY = D.HDRI["colorful_studio"]
D.world_hdri(SKY, WORLD_K, camera_bg="cream", camera_bg_strength=envf("S04_VOID", 0.9))

# ----------------------------------------------------------------------------------------------------------
# Camera (baked per frame from the closed-form path; frame 0 keyed for f1's motion blur)
# ----------------------------------------------------------------------------------------------------------
cam, tgt = D.camera("Cam", location=tuple(CAM0), target=tuple(TGT0), lens=LENS, fstop=2.0, sensor=SENSOR)
cam.data.dof.focus_object = None
D.bake(cam, "location", 0, N_FRAMES, cam_pos)
D.bake(tgt, "location", 0, N_FRAMES, tgt_pos)
D.bake(cam.data, "dof.aperture_fstop", 0, N_FRAMES, fstop)
D.bake(cam.data, "dof.focus_distance", 0, N_FRAMES, focus)
D.bake(sc, "render.motion_blur_shutter", 0, N_FRAMES, shutter)

# ----------------------------------------------------------------------------------------------------------
# Debug cameras (S04_CAM=top|chair|side)
# ----------------------------------------------------------------------------------------------------------
dbg = os.environ.get("S04_CAM")
if dbg:
    if dbg == "top":
        dc, _ = D.camera("DbgTop", location=(-0.3, -1.6, 14.0), target=(-0.3, -1.6, 0.0), lens=50)
        dc.data.type = "ORTHO"
        dc.data.ortho_scale = 11.0
        for f in range(1, N_FRAMES + 1, 4):   # camera path markers (emissive, debug only)
            D.sphere(f"PathMark{f}", 0.04, location=tuple(cam_pos(f)),
                     mat=D.mat_emission("pink" if f < F_PUSH0 else ("aqua" if f < F_LOCK else "lime"), 3))
    elif dbg == "chair":     # from the main camera's direction, close
        _d = (CAM0 - CHAIR_C).normalized()
        D.camera("DbgChair", location=tuple(CHAIR_C + Vector((0, 0, 0.55)) + 1.8 * _d),
                 target=tuple(CHAIR_C + Vector((0, 0, 0.55))), lens=50)
    elif dbg == "mag":
        D.camera("DbgMag", location=tuple(TABLE + Vector((-0.05, -0.55, 1.05))),
                 target=tuple(TABLE + Vector((-0.08, -0.15, 0.61))), lens=60)
    elif dbg == "table":
        D.camera("DbgTable", location=tuple(TABLE + Vector((0.25, -0.9, 1.15))),
                 target=tuple(TABLE + Vector((0.0, 0.03, 0.64))), lens=50)
    elif dbg == "side":
        D.camera("DbgSide", location=(5.0, -5.0, 2.5), target=(-1.0, 0.5, 1.2), lens=28)
    sc.render.use_motion_blur = False


# ----------------------------------------------------------------------------------------------------------
# Overscan still (--overscan / S04_OVERSCAN=1): the f180 camera on a wider sensor for the finale's centre hex
# tile. Same position, orientation, lens and DOF; horizontal fit with the sensor widened by 2544/1920 keeps the
# focal length in pixels, so the central 1920 x 1080 (offset 312, 562) is exactly f180.
# ----------------------------------------------------------------------------------------------------------
OVS_SENSOR = SENSOR * OVS_RES[0] / 1920.0                        # 47.7 mm
OVS_CROP = ((OVS_RES[0] - 1920) // 2, (OVS_RES[1] - 1080) // 2)  # (312, 562)
HEX_R_PX = 960.0 + 540.0 / math.sqrt(3.0)                        # flat-top hex through the frame's corners
LIP_NAMES = ("LipTop", "LipBot", "LipL", "LipR")


def extend_canvas_top(ob, ext):
    """Move the canvas plane's top edge up by `ext` canvas heights and extend its UVs to match, so every texel
    keeps its world position (only the overscan sees past the painting's edge)."""
    me = ob.data
    uvl = me.uv_layers.active
    for v in me.vertices:
        if v.co.y > 0:
            v.co.y = CANVAS_H / 2 + ext * CANVAS_H
    for lp in me.loops:
        if me.vertices[lp.vertex_index].co.y > 0:
            uvl.data[lp.index].uv = (uvl.data[lp.index].uv[0], 1.0 + ext)
    me.update()


def uv_rect(d, w_px=1920, h_px=1080):
    """Canvas uv rectangle (u0, v0, u1, v1; v from the bottom) of a w_px x h_px image (focal 2133.3 px) seen square
    to the canvas from distance d, centred on the subject."""
    hw = d * (w_px / FOCAL_PX) / 2 / CANVAS_W
    hh = d * (h_px / FOCAL_PX) / 2 / CANVAS_H
    return (SUBJ_UV[0] - hw, SUBJ_UV[1] - hh, SUBJ_UV[0] + hw, SUBJ_UV[1] + hh)


OVS_RECT = uv_rect(D_END, *OVS_RES)


def load_ext():
    """The generated foliage band (scripts/make_seurat_ext.py): its JSON and the entry for this run's texture."""
    try:
        with open(EXT_JSON) as fh:
            ext = json.load(fh)
    except (OSError, ValueError):
        return None, None
    return ext, ext.get("res", {}).get(os.path.splitext(TEX)[0].rsplit("_", 1)[-1])


EXT, EXT_RES = load_ext()


def band_extension(mat):
    """Overscan texture lookup. v <= x0: the original JPEG (mix factor 0, so exactly the f180 shading); x0..x1: a
    cross-fade to the band, which still holds the painting's own rows there; above: the generated foliage band,
    mapped v' = (v - v_b0) / (v_b1 - v_b0) with EXTEND. The original image node is left untouched."""
    if EXT_RES is None:
        raise SystemExit(f"[s04] --overscan needs the generated foliage band for {TEX} ({EXT_JSON}): run "
                         "tools/venv/bin/python -I scripts/make_seurat_ext.py")
    v_b0, v_b1 = EXT_RES["v_b0"], EXT_RES["v_b1"]
    x0, x1 = EXT["shader_crossfade_v"]
    assert v_b0 < x0 < x1 < 0.95 and v_b1 > OVS_RECT[3] + 0.01, (v_b0, x0, x1, v_b1, OVS_RECT)
    nt = mat.node_tree
    tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
    lk = next(lk for lk in nt.links if lk.to_node == tex and lk.to_socket.name == "Vector")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(lk.from_socket, sep.inputs[0])

    def madd(a, mul, add, clamp=False):
        nd = nt.nodes.new("ShaderNodeMath")
        nd.operation = "MULTIPLY_ADD"
        nd.use_clamp = clamp
        nt.links.new(a, nd.inputs[0])
        nd.inputs[1].default_value = mul
        nd.inputs[2].default_value = add
        return nd.outputs[0]

    v = sep.outputs["Y"]
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(madd(v, 1.0 / (v_b1 - v_b0), -v_b0 / (v_b1 - v_b0)), comb.inputs["Y"])
    band = nt.nodes.new("ShaderNodeTexImage")
    band.image = bpy.data.images.load(os.path.join(D.ROOT, EXT_RES["file"]), check_existing=True)
    band.image.colorspace_settings.name = "sRGB"
    band.interpolation = tex.interpolation
    band.projection = "FLAT"
    band.extension = "EXTEND"
    nt.links.new(comb.outputs[0], band.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MIX"
    nt.links.new(madd(v, 1.0 / (x1 - x0), -x0 / (x1 - x0), clamp=True), sock(mix.inputs, "Factor_Float"))
    old = [lk for lk in nt.links if lk.from_socket == tex.outputs["Color"]]
    dst = [lk.to_socket for lk in old]
    for lk in old:
        nt.links.remove(lk)
    nt.links.new(tex.outputs["Color"], sock(mix.inputs, "A_Color"))
    nt.links.new(band.outputs["Color"], sock(mix.inputs, "B_Color"))
    for so in dst:
        nt.links.new(sock(mix.outputs, "Result_Color"), so)
    print(f"[s04] overscan band: {EXT_RES['file']} v {v_b0:.5f}..{v_b1:.5f}, cross-fade v {x0}..{x1}", flush=True)


if OVERSCAN:
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = OVS_SENSOR
    for ob in [frame] + [bpy.data.objects[n] for n in LIP_NAMES]:
        ob.hide_render = True
        ob.hide_viewport = True
    extend_canvas_top(canvas, OVS_EXT_TOP)
    band_extension(m_seurat)

# ----------------------------------------------------------------------------------------------------------
# Meta (written at build time, every mode)
# ----------------------------------------------------------------------------------------------------------


def px_per_texel(f):
    """Projected size of one 20000-px texel at the push target, seen along the dolly axis (camera -> target;
    ignores the whip yaw and the framing glide so the instrument is monotonic): sqrt of its projected area."""
    c = cam_pos(f)
    fwd = (AIM - c).normalized()
    p0 = project_dir(fwd, c, AIM)
    pu = project_dir(fwd, c, AIM + TEXEL * U_HAT)
    pv = project_dir(fwd, c, AIM + TEXEL * Z_HAT)
    a = (pu[0] - p0[0], pu[1] - p0[1])
    b = (pv[0] - p0[0], pv[1] - p0[1])
    return math.sqrt(abs(a[0] * b[1] - a[1] * b[0]))


def margins(rect):
    u0, v0, u1, v1 = rect
    h = v1 - v0
    return {"parasol_tip_top": round((v1 - PARASOL_TIP_UV[1]) / h, 4),
            "girl_feet_bottom": round((GIRL_FEET_UV[1] - v0) / h, 4)}


# Measured final cost (2026-11-20, renders/work/s04_subject/cost_probe2.py: one Blender process per probe, GPU 6 polled
# with nvidia-smi; frames rendered while another process ran on GPU 6 are left out). Not a render input: recorded in
# the meta so scripts/render_finals.py --film v2 plans with it (it reads the first "*s_per_frame*" number it finds).
FINAL_COST = {
    "measured_final_s_per_frame": 7.11,          # mean over f1-180, linear interpolation of the clean samples
    "samples_s": {"1": 7.2, "5": 7.4, "10": 7.2, "25": 7.2, "31": 7.2, "45": 7.6, "60": 8.3, "70": 8.6, "95": 7.1,
                  "120": 6.4, "136": 6.4, "142": 6.4, "150": 6.4, "180": 6.4},
    "first_frame_extra_s": 25.0,                 # 20K texture load/upload + BVH on the first frame of a process
    "process_startup_s": 12.6,                   # Blender start + scene build before the first frame
    "gpu_h_180_frames": {"1_job": 0.366, "3_jobs": 0.387, "4_jobs": 0.398},
    "overscan_still": {"render_s": 43.4, "wall_s": 57, "gpu_h": 0.016},
    "cap_gpu_h": 0.45, "gpu": "1x H200 (GPU 6, not shared during the clean samples)",
    "test_frames": ["renders/test/s04_subject_cost", "renders/test/s04_subject_cost2",
                    "renders/test/s04_subject_ovs_final_mirror_superseded (overscan cost; mirror version)"],
}

frames = list(range(1, N_FRAMES + 1))
dist_m = [round((cam_pos(f) - AIM).length, 5) for f in frames]
zoom = [round(D0 / d, 4) for d in dist_m]
ppt = [round(px_per_texel(f), 5) for f in frames]
speed = [round((cam_pos(f + 0.5) - cam_pos(f - 0.5)).length, 5) for f in frames]
logspeed = [round(math.log(dist(f - 0.5) / dist(f + 0.5)), 5) for f in frames]
angspeed = [round(math.degrees(view_fwd(f - 0.5).angle(view_fwd(f + 0.5), 0.0)), 4) for f in frames]
subj_screen = []
for f in frames:
    x, y = project_dir(view_fwd(f), cam_pos(f), AIM)
    subj_screen.append([round(960 + x, 2), round(540 - y, 2)])
_fine = [F_PUSH0 + i * 0.05 for i in range(int((F_LOCK - F_PUSH0) / 0.05) + 1)]
F_CROSS = next(f for f in _fine if push_e(f) >= 1.0)                # end framing first reached (still moving)
F_PEAK = max(_fine, key=push_e)                                      # max push (+6 % zoom)
ZOOM_PEAK = D0 / dist(F_PEAK)
END_RECT = uv_rect(D_END)
PEAK_RECT = uv_rect(dist(F_PEAK))
meta = {
    "id": SHOT,
    "version": "v2",
    "frames": N_FRAMES,
    "start_frame_in_film": FILM_START,
    "built_mode": args.mode,
    "texture": TEX,
    "texture_final": "seurat_grande_jatte_20000.jpg",
    "zoom_end": round(D0 / D_END, 4),
    "static_hold": [150, N_FRAMES],
    "cost_final": FINAL_COST,
    "events": {"whip_in": 1, "whip_end": 11, "settled": 25, "pill_pop": 16, "push_start": F_PUSH0,
               "subject_centred": F_TGT1, "square_to_canvas": F_SLERP1,
               "end_framing_first_reached": round(F_CROSS, 2), "push_peak": round(F_PEAK, 2),
               "push_peak_beat": F_PEAK_BEAT, "settle_return_start": F_RET0, "settled_lock": F_LOCK,
               "hold_start": 150, "hold_end": N_FRAMES, "match_cut_to_s05_finale_f1": N_FRAMES},
    "per_frame": {"dist_m": dist_m, "zoom": zoom, "px_per_texel": ppt},
    "end_framing": {
        "subject_centre_uv": [round(SUBJ_UV[0], 5), round(SUBJ_UV[1], 5)],
        "storyboard_centre_uv": list(SUBJ_UV0), "centre_adjust_uv": [round(x, 5) for x in SUBJ_DUV],
        "uv_convention": "Blender UV of the canvas plane, u left->right, v from the BOTTOM",
        "uv_rect": [round(x, 5) for x in END_RECT],
        "frame_height_frac_of_canvas": round(FRAME_H_FRAC, 5),
        "frame_width_frac_of_canvas": round(END_RECT[2] - END_RECT[0], 5),
        "zoom": round(D0 / D_END, 4), "d0_m": round(D0, 5), "dist_m": round(D_END, 5),
        "px_per_texel": ppt[-1], "texels_per_px": round(1.0 / ppt[-1], 3),
        "fstop": round(fstop(N_FRAMES), 3), "square_to_canvas": True,
        "margins_frac_of_frame_h": margins(END_RECT),
        "parasol_tip_uv": list(PARASOL_TIP_UV), "girl_feet_uv": list(GIRL_FEET_UV),
        "push_peak": {"frame": round(F_PEAK, 2), "zoom": round(ZOOM_PEAK, 4),
                      "overshoot_scale_pct": round((ZOOM_PEAK / (D0 / D_END) - 1) * 100, 2),
                      "overshoot_log_pct": round((push_e(F_PEAK) - 1) * 100, 2),
                      "uv_rect": [round(x, 5) for x in PEAK_RECT], "margins_frac_of_frame_h": margins(PEAK_RECT)},
    },
    "overscan": {
        "switch": "--overscan (or S04_OVERSCAN=1)", "frame": N_FRAMES,
        "output": "renders/<mode>/s04_subject/overscan.png", "bit_depth": "16 in final, 8 in preview/draft",
        "res_final": list(OVS_RES), "res_preview": [OVS_RES[0] // 2, OVS_RES[1] // 2],
        "crop_offset_final": list(OVS_CROP), "crop_offset_preview": [OVS_CROP[0] // 2, OVS_CROP[1] // 2],
        "sensor_fit": "HORIZONTAL", "sensor_width_mm": round(OVS_SENSOR, 4), "lens_mm": LENS,
        "focal_px_final": round(FOCAL_PX, 3),
        "hex": {"type": "flat-top", "circumradius_px_final": round(HEX_R_PX, 3),
                "width_px_final": round(2 * HEX_R_PX, 2), "height_px_final": round(math.sqrt(3) * HEX_R_PX, 2),
                "note": "vertices at the midpoints of the image's left/right edges; the hex passes through the four "
                        "corners of the central 1920x1080 (= f180)"},
        "uv_rect": [round(x, 5) for x in OVS_RECT],
        "hex_top_above_painting_frac_of_canvas_h": round(OVS_RECT[3] - 1.0, 4),
        "hidden": ["Frame"] + list(LIP_NAMES),
        "canvas_plane_extended_top_frac_of_canvas_h": OVS_EXT_TOP,
        "texture_extension": {
            "method": "generated pointillist foliage band above the painting (no mirror)",
            "generator": "scripts/make_seurat_ext.py",
            "geometry_json": os.path.relpath(EXT_JSON, D.ROOT),
            "seed": (EXT or {}).get("seed"),
            "files": {k: r["file"] for k, r in (EXT or {}).get("res", {}).items()},
            "band_v_by_res": {k: [round(r["v_b0"], 6), round(r["v_b1"], 6)]
                              for k, r in (EXT or {}).get("res", {}).items()},
            "band_mapping": "band v' = (v - v_b0) / (v_b1 - v_b0); extension EXTEND; interpolation Linear",
            "shader_crossfade_v": (EXT or {}).get("shader_crossfade_v"),
            "patch_ramp_start_v": (EXT or {}).get("patch_ramp_start_v"),
            "patch_ramp_full_v": (EXT or {}).get("patch_ramp_full_v"),
            "painted_border_lowest_v": (EXT or {}).get("border_lowest_v"),
            "image_extension": "EXTEND",
            "note": "original JPEG (Blender's decode) for v below the cross-fade, i.e. the whole f180 frame and "
                    "everything under it; above, foliage synthesised from the canopy's own dabs (foliage-only "
                    "patches, colour-matched to soft light/dark masses that continue the canopy across the seam); "
                    "trunks dissolve into it at varying heights; the painted red/blue top border is covered",
            "obsolete": "the v2 build's mirror extension (mirror_above_v 0.9815, mirror_scale_k 0.713) and its "
                        "mirror_* keys were removed on 2026-11-20 (lead follow-up: it folded the trunks into "
                        "V/diamond shapes)"},
    },
    "diagnostics": {"push_e": [round(push_e(f), 6) for f in frames],
                    "cam_speed_m_per_f": speed, "log_dist_rate_per_f": logspeed,
                    "edge_px_per_f_from_scale": [round(abs(x) * 960, 2) for x in logspeed],
                    "view_ang_speed_deg_per_f": angspeed,
                    "subject_screen_px": subj_screen,
                    "whip_yaw_deg": [round(psi(f), 4) for f in frames],
                    "shutter": [round(shutter(f), 4) for f in frames],
                    "fstop": [round(fstop(f), 4) for f in frames],
                    "focus_m": [round(focus(f), 5) for f in frames],
                    "subject_world": [round(v, 5) for v in AIM], "subject_screen_wide_px":
                        [round(960 + S_WIDE[0], 2), round(540 - S_WIDE[1], 2)],
                    "push_params": {"over": OVER, "fwd_lobe": [F_PUSH0, F_FWD1], "return_lobe": [F_RET0, F_LOCK],
                                    "glide": [F_PUSH0, F_TGT1], "slerp": [F_PUSH0, F_SLERP1],
                                    "fstop_ramp": [F_FS0, F_FS1], "shutter_dip": list(F_SH)}},
}
if not OVERSCAN:   # the overscan run shares the camera path; it never rewrites the meta
    os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
    with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
print(f"[s04] meta: d0={D0:.4f} d_end={D_END:.4f} zoom_end={D0 / D_END:.3f} frame_h={FRAME_H_FRAC:.4f} "
      f"ppt_end={ppt[-1]:.4f} cross=f{F_CROSS:.2f} peak=f{F_PEAK:.2f} x{ZOOM_PEAK:.3f} "
      f"margins_end={margins(END_RECT)} margins_peak={margins(PEAK_RECT)} "
      f"s_wide=({960 + S_WIDE[0]:.1f},{540 - S_WIDE[1]:.1f}) ovs_uv={tuple(round(x, 4) for x in OVS_RECT)}",
      flush=True)

if OVERSCAN:
    out_dir = args.out or os.path.join(D.ROOT, "renders", args.mode, SHOT)
    if args.frames not in (None, str(N_FRAMES)):
        print(f"[s04] --overscan renders frame {N_FRAMES} only (ignoring --frames {args.frames})", flush=True)
    tmp = os.path.join(out_dir, "_overscan_tmp")
    args.frames, args.out, args.prefix = str(N_FRAMES), tmp, "overscan_"
    D.finish(args, final_samples=192, final_threshold=0.01, frame_end=N_FRAMES, shot_name=SHOT)
    if not args.no_render:
        dst = os.path.join(out_dir, "overscan.png")
        os.replace(os.path.join(tmp, f"overscan_{N_FRAMES:04d}.png"), dst)
        try:
            os.rmdir(tmp)
        except OSError:
            pass
        print(f"[s04] overscan still -> {dst}", flush=True)
else:
    D.finish(args, final_samples=192, final_threshold=0.01, frame_end=N_FRAMES, shot_name=SHOT)
