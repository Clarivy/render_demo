"""S04 · s04_every_dot · "Every dot" · capability C4 (high-resolution textures).
Film frames 601-780 = local 1-180 (bars 11-13, 20.0-26.0 s). GPU: run with CUDA_VISIBLE_DEVICES=6 or 7.

Round 2 changelog (lead notes docs/lead_notes_r2.md + critic review; round-1 script kept as
renders/work/s04_every_dot/s04_every_dot_r1.py)
-------------------------------------------------------------------------------------------------------------
 1. G1 glow. S01's compositor bloom copied with identical parameters (Emit pass only -> Glare BLOOM, quality HIGH,
    threshold 0.6, smoothness 0.2, strength 1.0, size 0.45, saturation 1.0, added over the image). Its add is keyed
    0 -> 1 at f166 so nothing in the wide can bloom; only the dot-orb emits from f168.
 2. Orb emission re-timed so it keeps building into the cut: emission mix = ease_in_cubic(f168-180) of a constant
    strength 4.0 (the film-wide white orb value: S01 white halo 4.0, S05 white halo 4.0), x (0.7 + 0.3 (1 - Facing))
    so the limb keeps a little roundness while the core clips. The bloom therefore grows over ~f175-180 (emit > 0.6).
    The orb lights the painting (rays other than camera rays see LIGHT_GAIN x the emission: the camera still sees 4.0,
    so the core / bloom match S05) and the wash trims 100 -> 80 % over f170-180 so the orb's pool reads.
 3. Pop launches on the 766 beat with matched velocity (critic): the orb rises behind the canvas over f164-166 with an
    ease-in (c = C_START (1 - p^1.6), exit 10.7 mm/f; hidden until f166), then POP spring (2.5, 8) from f166
    (entry 10.5 mm/f); C_END is solved so f180 stays exactly ORB_C180 (468 px). Overshoot peak ~f171, no stall.
    The dot itself swells: for f166-172 the orb's base colour is the Seurat scan projected along the canvas normal
    (Texture Coordinate Object of the canvas -> canvas UV) on a matte surface (rough 0.55, no coat), easing to candy
    white with its clear coat by f172 - the painted dabs inflate into the pearl instead of being covered.
 4. Push framing in screen space (critic): f31-70 the camera is oriented (no roll) so the dot projects to
    p(f) = p_wide + (centre - p_wide) smootherstep(f31-70); no counter-drift, no pan stop at f38, peak dot sweep
    23 px/f. Shutter 0.5 -> 0.35 over f46-52 and back over f72-80 (same mechanism as the whip) so dabs stay legible.
 5. Room-wide re-lit as a gallery (lead note 1): warm window-softbox KEY from the upper left (AREA 2.0 x 1.4 m, spread
    120 deg, soft contact shadows under chair / bench / duck), cool lavender FILL from the right (~25 %), the gallery
    WASH is now a soft SPOT centred on the canvas normal 6 m out (even to +-10 % across the canvas, a pool that fades
    on the wall around the frame). Key, fill and the lamp never light the canvas (light-linked EXCLUDE), so the canvas
    stays even, glare-free and tone-matched at 1:1. WallFill and the studio rig are gone; falloff toward the frame
    edges comes from the lights' cones (no compositor vignette). World 0.15 -> 0.12.
 6. Floor reads peach pastel wood (lead note 2): no multiply tint; 0.75 screen toward #FFCDB6 keeps the grain.
 7. G2 no grey: teddy plaid tinted teal (multiply #7EDFD6 0.55, saturation 1.5, value 1.15); shadows are filled cool.
 8. Foyer (whip-in only, f1-8): white candy dado rail at z 1.2 (lands at ~52 % height on f1, continuing S03's
    skirting streak), watermelon-pink clay above / rose clay below, candy panels 1.5x, rose skirting, and the wall
    extends to azimuth ~123.5 deg so the cream gap before the room shrinks from ~9 deg to ~4 deg.
 9. Whip landing: overshoot 1.5 -> 1.2 deg with a longer tail u^3 (1-u)^4 over f1-25 (peak f11.3, return <= 6 px/f).
10. Tactile soft goods: rug = Poly Haven velour_velvet re-hued candy pink (sheen 1.0) 3.5 cm thick with a soft bevel;
    plush bunny sheen roughness 0.35 -> 0.2 with a whiter sheen; lamp shade translucent (clay + translucent mix) with
    LampGlow 18 -> 35 W so the back corner has a warm practical.
11. Duck moved to the rug's front-right (0.50, -0.62), scale 1.6 -> 1.35, beak turned toward the Seurat (yaw 240:
    beak azimuth ~150 deg) so its gaze leads to the push target.
12. Final samples 256 -> 192 (threshold 0.01): measured 6.6 s (hold) / 8.5 s (push) per frame on one H200, ~0.41
    GPU-h for the shot (cap 0.5); 256 spp measured 8.3-11.8 s/f (~0.52 GPU-h). Mean |256 - 192| 0.5-0.9/255.

What the shot proves
--------------------
One unbroken camera move on ONE texture asset: a whip-in (continuing S03's whip right) lands on a candy gallery
(lemon/butter dollhouse corner, orange-framed Seurat, aqua-framed van Gogh, teal teddy armchair with a lilac plush
bunny, mint side table with a pink bowl of citrus, floor lamp, pink velvet rug, rubber duck, violet gallery bench).
A single 46x log-space dolly then runs from the room-wide (~1/44 px per texel on the Seurat) to 1.097 px per
texel on the 20000 x 13313 px scan of Seurat's "A Sunday on La Grande Jatte" (final mode; drafts use the 2048 px
and previews the 8192 px file), ending square to the canvas at f/11 with Linear texture filtering, then holds
while drifting 0.5 mm along u (~6 px over 60 f) so any texture swimming or shimmer would show. The painted white
disc of the "rosette" figure then swells out of the canvas, turns into a candy pearl and springs toward the lens as
a glowing orb: 468 px wide, centred, at f180 (the circle match into S05).

Timeline (local frames; global = local + 600)
  f1-10    whip-in: yaw +55 deg (left) -> 0 with ease_out_cubic from f1 (16.5 deg/f at f1, keyed from f0 so f1's
           motion blur continues the whip), shutter 1.0 -> 0.5; overshoot 1.2 deg past the wide at ~f11, at rest f25
  f11-30   the room-wide, one breath (pill pops in post at f16)
  f31-105  log push d = d0 (d1/d0)^ease_in_out_sine(f31-105); view direction slerps to the canvas normal
           (smootherstep f31-100); the dot's screen position glides p_wide -> centre (smootherstep f31-70);
           f-stop 2 -> 11 (log, ease_in_out_sine f60-100); shutter dips to 0.35 over f46-80
  f106-165 1:1 hold: camera + target drift -0.25 -> +0.25 mm along u (linear, 0.1 px/f)
  f164-166 the dot rises behind the canvas (hidden), a painted hemisphere already moving on the f166 beat
  f166-180 POP spring (2.5, 8) toward the lens (peak ~f171); paint -> candy pearl f166-172; emission f168-180
           (ease-in), bloom builds ~f175-180; focus pulls canvas -> orb over f167-172 then tracks it;
           f-stop 11 -> 4 (log) over f166-176

Deviations from the storyboard (tunable visual parameters only; hits, transitions, proof and colour pipeline kept)
  * Push target re-measured on the 20000 px source: the painted white disc's centroid is uv (0.27375, 0.56537);
    the storyboard's (0.2755, 0.565) sits ~35 texels right of it, and the disc is ~317 texels (2.9 cm) across,
    not 380. D moves 3.5 mm along -u so the disc and the f180 orb are centred.
  * DotOrb radius 0.0148 m (matches the painted disc, instead of 0.017) and it springs further out (centre
    38.8 mm in front of the canvas at f180, instead of 20 mm) so it still spans 468 px at f180. Focus pulls to
    the orb (0.175 -> 0.136 m) instead of 0.155 m.
  * Framing glide in screen space over f31-70 (storyboard: look-at ease_in_out_sine f31-60), see round-2 note 4.
  * Hold drift runs -0.25 -> +0.25 mm about D (instead of 0 -> +0.5 mm) so the orb is centred at f180.
  * DOF uses a baked focus distance (depth of the dot on the view axis, then the orb) instead of a focus object.
  * Lights: see round-2 note 5 (storyboard: wash AREA 650 W + studio_rig 500 W, world 0.4, which over-exposed by ~2
    stops under PBR Neutral and lit the room flat).
  * Added set: the off-frame foyer (whip-in only) and a violet velvet gallery bench with gold legs under the van Gogh.
  * van Gogh: the Met photo has a black surround; UVs are cropped to the painted area (u 0.0275-0.9665,
    v 0.0317-0.9607) and the plane/frame take that aspect, 0.8 m wide (0.6) to hold the butter wall.
  * Rubber duck re-hued from the scan's orange to lemon yellow (beak turns orange). Plush bunny 0.40 m (0.32).
  * Fruit: the lime scan, re-hued into a lemon and an orange plus brightened limes and a kiwi (the brown kiwis
    read as potatoes). Bowl is a lathed candy bowl (a solid cylinder read as a puck).
  * Magnifier: the glTF lens is four open shells (renders black as refractive glass); replaced by a closed
    ellipsoid glass lens with shadow visibility off. Lamp shade is an open truncated cone.
  * Armchair: arms 0.18 x 0.70 x 0.58 outside the seat, back 1.04 x 0.22 x 0.95 to the floor (chunkier toy look).

Env vars (debug / look-dev only; defaults are the shipped look): S04_CAM=top|chair|table|mag|side -> static debug
camera; S04_TEX=<file>; S04_KEY / S04_FILL / S04_WASH / S04_WASH_COL / S04_WORLD / S04_FLOOR_LIFT / S04_LAMP /
S04_GAIN / S04_GLOW.
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

SHOT = "s04_every_dot"
N_FRAMES = 180
FILM_START = 601

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=192, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=8,
               caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)
D.setup_color(exposure=-0.1)
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


DOT_UV = (0.27375, 0.56537)                    # measured centroid of the painted white disc (20000 px scan)
DOT = canvas_pt(*DOT_UV)
DOT_R = 0.0148                                 # painted disc radius ~ 165 texels

# ----------------------------------------------------------------------------------------------------------
# Camera path (closed-form functions of the frame; also used for meta)
# ----------------------------------------------------------------------------------------------------------
LENS, SENSOR = 40.0, 36.0
FOCAL_PX = 1920.0 * LENS / SENSOR             # 2133.3 px at 1920 width
CAM0 = Vector((0.90, -6.60, 3.00))
TGT0 = Vector((-0.20, 0.90, 1.00))
D_END = 0.175                                  # camera-canvas distance at the end of the push
DRIFT = 0.0005                                 # 0.5 mm along u over the hold
F_PUSH0, F_PUSH1, F_SLERP1, F_TGT1 = 31, 105, 100, 70
F_HOLD0, F_HOLD1 = 106, 165
F_POP = 166
WHIP_DEG, WHIP_F = 55.0, 10.0
OVERSHOOT_DEG = 1.2                            # round 2: 1.5 -> 1.2 with a longer tail (return <= ~6 px/f)
BUMP_F = 24.0                                  # overshoot bump spans f1-25
BUMP_MAX = (3 / 7) ** 3 * (4 / 7) ** 4         # max of u^3 (1-u)^4 (at u = 3/7, f11.3)


def drift(f):
    return -0.5 * DRIFT + DRIFT * D.prog(f, F_HOLD0, F_HOLD1)


def aim(f):
    """Push target incl. the sub-pixel drift."""
    return DOT + drift(f) * U_HAT


AIM0 = aim(F_PUSH0)
D0 = (CAM0 - AIM0).length                     # 8.07 m
DIR0 = (CAM0 - AIM0).normalized()


def slerp(a, b, t):
    a, b = a.normalized(), b.normalized()
    om = math.acos(max(-1.0, min(1.0, a.dot(b))))
    if om < 1e-9:
        return a.copy()
    so = math.sin(om)
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / so


def push_e(f):
    return D.ease_in_out_sine(D.prog(f, F_PUSH0, F_PUSH1))


def dist(f):
    return D0 * (D_END / D0) ** push_e(f)


def cam_pos(f):
    if f <= F_PUSH0:
        return CAM0.copy()
    s = D.smootherstep(D.prog(f, F_PUSH0, F_SLERP1))
    return aim(f) + dist(f) * slerp(DIR0, N_HAT, s)


def psi(f):
    """Whip yaw offset in degrees (+ = rotated left/CCW). ease_out_cubic over 10 f from f1 (16.5 deg/f at f1)
    plus a smooth overshoot bump u^3 (1-u)^4 over f1-25 (peak f11.3, gone by f25)."""
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


S_WIDE = project_dir((TGT0 - CAM0).normalized(), CAM0, AIM0)    # the dot's screen offset in the wide


def view_fwd(f):
    c = cam_pos(f)
    if f <= F_PUSH0:
        fwd = (TGT0 - c).normalized()
    else:   # the dot glides p_wide -> frame centre on a straight screen path (C2, no counter-drift)
        k = 1.0 - D.smootherstep(D.prog(f, F_PUSH0, F_TGT1))
        fwd = fwd_for_screen(c, aim(f), S_WIDE[0] * k, S_WIDE[1] * k)
    a = math.radians(psi(f)) if f < 1 + BUMP_F + 1 else 0.0
    if a:
        ca, sa = math.cos(a), math.sin(a)
        fwd = Vector((fwd.x * ca - fwd.y * sa, fwd.x * sa + fwd.y * ca, fwd.z))
    return fwd


def tgt_pos(f):
    c = cam_pos(f)
    return c + view_fwd(f) * (aim(f) - c).length


def fstop(f):
    if f < F_POP:
        return 2.0 * (11.0 / 2.0) ** D.ease_in_out_sine(D.prog(f, 60, 100))
    return 11.0 * (4.0 / 11.0) ** D.ease_in_out_sine(D.prog(f, F_POP, 176))


def shutter(f):
    s = 1.0 - 0.5 * D.ease_in_out_sine(D.prog(f, 1, 10))
    return s - 0.15 * (D.ease_in_out_sine(D.prog(f, 46, 52)) - D.ease_in_out_sine(D.prog(f, 72, 80)))


# ----------------------------------------------------------------------------------------------------------
# Dot-orb pop (closed form). c = signed offset of the orb centre along N_HAT from the canvas plane.
# ----------------------------------------------------------------------------------------------------------
ORB_TARGET_PX = 468.0
ORB_PX_FUDGE = 1.5                     # measured AA/DOF edge widens the silhouette by ~1.5 px vs geometry
_k = (ORB_TARGET_PX - ORB_PX_FUDGE) / 2 / FOCAL_PX                  # tan of the silhouette half-angle
ORB_Z = DOT_R * math.sqrt(1 + 1 / _k ** 2)                          # camera->orb-centre distance at f180
ORB_C180 = D_END - ORB_Z                                            # ~0.039 m in front of the canvas
POP_SPRING = (2.5, 8.0)                                             # POP (motion language 2.4)
F_RISE0 = F_POP - 2                                                 # rise f164-166 behind the canvas (hidden)
C_END = ORB_C180 / D.spring((N_FRAMES - F_POP) / 30.0, *POP_SPRING)  # orb_c(180) == ORB_C180 exactly
C_START = -DOT_R * 0.9                                              # just behind the canvas


def orb_c(f):
    if f <= F_RISE0:
        return C_START
    if f <= F_POP:                                                  # ease-in rise: exit 10.7 mm/f at f166
        return C_START * (1 - D.prog(f, F_RISE0, F_POP) ** 1.6)
    return C_END * D.spring((f - F_POP) / 30.0, *POP_SPRING)        # entry 10.5 mm/f: launch on the beat


ORB_XY = aim(F_HOLD1)                                               # the drifted centre = frame centre


def orb_pos(f):
    return ORB_XY + orb_c(f) * N_HAT


ORB_EMIT = 4.0                         # film-wide white orb emission (S01 white halo 4.0, S05 white halo 4.0)
LIGHT_GAIN = envf("S04_GAIN", 3.0)     # emission seen by non-camera rays (the orb lights the painting)


def paint_w(f):
    """0 = the orb shows the painted dot (matte), 1 = candy pearl (white, clear coat)."""
    return D.ease_in_out_sine(D.prog(f, F_POP, F_POP + 6))


def emit_mix(f):
    return D.ease_in_cubic(D.prog(f, 168, 180))


def focus(f):
    c = cam_pos(f)
    base = (aim(f) - c).dot(view_fwd(f))               # depth of the dot on the view axis
    if f < F_POP:
        return base
    orb_d = (c - orb_pos(f)).length                    # pull to the orb, then track it exactly from f172
    w = D.smootherstep(D.prog(f, F_POP + 1, F_POP + 6))
    return (1 - w) * base + w * orb_d


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
# Dot-orb (custom node setup #6). Base colour = the Seurat scan projected along the canvas normal (the painted dot)
# easing to candy white f166-172 (with roughness 0.55 -> 0.18 and coat 0 -> 1); then Mix(candy, Emission) with
# emission 4.0 x (0.7 + 0.3 (1 - Facing)), x LIGHT_GAIN for non-camera rays.
# ----------------------------------------------------------------------------------------------------------
m_orb = D.mat_candy("white", name="dot_orb", rough=0.18)
nt = m_orb.node_tree
P_orb = principled(m_orb)
tco = nt.nodes.new("ShaderNodeTexCoord")
tco.object = canvas
mpp = nt.nodes.new("ShaderNodeMapping")
mpp.vector_type = "POINT"
mpp.inputs["Location"].default_value = (0.5, 0.5, 0.0)
mpp.inputs["Scale"].default_value = (1.0 / CANVAS_W, 1.0 / CANVAS_H, 1.0)
nt.links.new(tco.outputs["Object"], mpp.inputs["Vector"])
itx = nt.nodes.new("ShaderNodeTexImage")
itx.image = SEURAT_IMG
itx.interpolation = "Linear"
itx.extension = "EXTEND"
nt.links.new(mpp.outputs["Vector"], itx.inputs["Vector"])
pmix = nt.nodes.new("ShaderNodeMix")
pmix.data_type = "RGBA"
nt.links.new(itx.outputs["Color"], sock(pmix.inputs, "A_Color"))
sock(pmix.inputs, "B_Color").default_value = D.col("white")
nt.links.new(sock(pmix.outputs, "Result_Color"), P_orb.inputs["Base Color"])
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = D.col("white")
lw = nt.nodes.new("ShaderNodeLayerWeight")
lw.inputs["Blend"].default_value = 0.5
m_rim = nt.nodes.new("ShaderNodeMath")                 # 0.7 + 0.3 (1 - facing) = 1.0 - 0.3 facing
m_rim.operation = "MULTIPLY_ADD"
nt.links.new(lw.outputs["Facing"], m_rim.inputs[0])
m_rim.inputs[1].default_value = -0.3
m_rim.inputs[2].default_value = 1.0
lpath = nt.nodes.new("ShaderNodeLightPath")
m_gain = nt.nodes.new("ShaderNodeMath")                # camera rays 1, all other rays LIGHT_GAIN
m_gain.operation = "MULTIPLY_ADD"
nt.links.new(lpath.outputs["Is Camera Ray"], m_gain.inputs[0])
m_gain.inputs[1].default_value = 1.0 - LIGHT_GAIN
m_gain.inputs[2].default_value = LIGHT_GAIN
m_s1 = nt.nodes.new("ShaderNodeMath")
m_s1.operation = "MULTIPLY"
nt.links.new(m_rim.outputs[0], m_s1.inputs[0])
m_s1.inputs[1].default_value = ORB_EMIT
m_s2 = nt.nodes.new("ShaderNodeMath")
m_s2.operation = "MULTIPLY"
nt.links.new(m_s1.outputs[0], m_s2.inputs[0])
nt.links.new(m_gain.outputs[0], m_s2.inputs[1])
nt.links.new(m_s2.outputs[0], emit.inputs["Strength"])
mix = nt.nodes.new("ShaderNodeMixShader")
out = nt.nodes["Material Output"]
nt.links.new(P_orb.outputs[0], mix.inputs[1])
nt.links.new(emit.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
orb = D.sphere("DotOrb", DOT_R, location=tuple(orb_pos(1)), mat=m_orb, segments=96, rings=48)
D.hide_range(orb, visible_from=F_POP)
D.bake(orb, "location", F_POP - 6, N_FRAMES, orb_pos)
D.bake(pmix.inputs["Factor"], "default_value", F_POP - 2, N_FRAMES, paint_w)
D.bake(P_orb.inputs["Roughness"], "default_value", F_POP - 2, N_FRAMES, lambda f: 0.55 + (0.18 - 0.55) * paint_w(f))
D.bake(P_orb.inputs["Coat Weight"], "default_value", F_POP - 2, N_FRAMES, paint_w)
D.bake(mix.inputs["Fac"], "default_value", F_POP - 2, N_FRAMES, emit_mix)

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
D.bake(wash.data, "energy", 160, N_FRAMES, lambda f: WASH_W * (1 - 0.2 * D.smoothstep(D.prog(f, 170, 180))))
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
# G1 orb glow: S01's bloom with identical parameters, driven by the Emit pass only (nothing else blooms).
# The add is keyed 0 -> 1 at f166 (the wide never blooms; the orb emits from f168).
# ----------------------------------------------------------------------------------------------------------
GLOW = envf("S04_GLOW", 1.0)
if GLOW > 0:
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
    ct.links.new(rl.outputs["Image"], add_glow.inputs[1])
    ct.links.new(gl.outputs["Glare"], add_glow.inputs[2])
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(add_glow.outputs[0], comp.inputs["Image"])
    D.bake(add_glow.inputs["Fac"], "default_value", 1, N_FRAMES, lambda f: 1.0 if f >= F_POP else 0.0)

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
                     mat=D.mat_emission("pink" if f < F_PUSH0 else ("aqua" if f < F_HOLD0 else "lime"), 3))
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
# Meta (written at build time, every mode)
# ----------------------------------------------------------------------------------------------------------


def px_per_texel(f):
    """Projected size of one 20000-px texel at the push target, seen along the dolly axis (camera -> target;
    ignores the whip yaw and the framing glide so the instrument is monotonic): sqrt of its projected area."""
    c = cam_pos(f)
    fwd = (aim(f) - c).normalized()
    p0 = project_dir(fwd, c, aim(f))
    pu = project_dir(fwd, c, aim(f) + TEXEL * U_HAT)
    pv = project_dir(fwd, c, aim(f) + TEXEL * Z_HAT)
    a = (pu[0] - p0[0], pu[1] - p0[1])
    b = (pv[0] - p0[0], pv[1] - p0[1])
    return math.sqrt(abs(a[0] * b[1] - a[1] * b[0]))


frames = list(range(1, N_FRAMES + 1))
dist_m = [round((cam_pos(f) - aim(f)).length, 5) for f in frames]
zoom = [round(D0 / d, 4) for d in dist_m]
ppt = [round(px_per_texel(f), 5) for f in frames]
speed = [round((cam_pos(f + 0.5) - cam_pos(f - 0.5)).length, 5) for f in frames]
logspeed = [round(math.log(dist(f - 0.5) / dist(f + 0.5)), 5) for f in frames]
angspeed = [round(math.degrees(view_fwd(f - 0.5).angle(view_fwd(f + 0.5), 0.0)), 4) for f in frames]
dot_screen = []
for f in frames:
    x, y = project_dir(view_fwd(f), cam_pos(f), aim(f))
    dot_screen.append([round(960 + x, 2), round(540 - y, 2)])
orb_px = 2 * FOCAL_PX * DOT_R / math.sqrt(max(1e-9, (cam_pos(180) - orb_pos(180)).length ** 2 - DOT_R ** 2))
meta = {
    "id": SHOT,
    "frames": N_FRAMES,
    "start_frame_in_film": FILM_START,
    "texture": TEX,
    "events": {"whip_in": 1, "whip_end": 11, "settled": 25, "pill_pop": 16, "push_start": F_PUSH0,
               "target_on_dot": F_TGT1, "square_to_canvas": F_SLERP1, "push_end": F_PUSH1,
               "hold_start": F_HOLD0, "hold_end": F_HOLD1, "dot_pop": F_POP, "pearl": 172, "emit_start": 168,
               "glow_full": 180},
    "per_frame": {"dist_m": dist_m, "zoom": zoom, "px_per_texel": ppt},
    "diagnostics": {"cam_speed_m_per_f": speed, "log_dist_rate_per_f": logspeed,
                    "view_ang_speed_deg_per_f": angspeed,
                    "dot_screen_px": dot_screen,
                    "whip_yaw_deg": [round(psi(f), 4) for f in frames],
                    "shutter": [round(shutter(f), 4) for f in frames],
                    "fstop": [round(fstop(f), 4) for f in frames],
                    "focus_m": [round(focus(f), 5) for f in frames],
                    "orb_c_m": [round(orb_c(f), 5) for f in frames],
                    "orb_emit_core": [round(ORB_EMIT * emit_mix(f), 4) for f in frames],
                    "orb_px_f180_predicted": round(orb_px, 1),
                    "glow": {"pass": "Emit", "type": "BLOOM", "quality": "HIGH", "threshold": 0.6,
                             "smoothness": 0.2, "strength": GLOW, "size": 0.45, "saturation": 1.0,
                             "on_from": F_POP, "orb_emission_f180": ORB_EMIT},
                    "dot_world": [round(v, 5) for v in DOT], "dot_uv": DOT_UV},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"[s04] meta: d0={D0:.4f} zoom_end={D0 / D_END:.2f} ppt_end={ppt[-1]:.3f} orb_c_end={C_END:.4f} "
      f"orb_px180={orb_px:.1f} s_wide=({960 + S_WIDE[0]:.1f},{540 - S_WIDE[1]:.1f})", flush=True)

D.finish(args, final_samples=192, final_threshold=0.01, frame_end=N_FRAMES, shot_name=SHOT)
