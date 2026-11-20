"""s01_lights_world -- "Lights on, world turns" (capability C1). Film frames 1-240 (bars 1-4, 0.0-8.0 s).

What the shot proves
--------------------
Phase A (f1-105), point lights.  A floating candy sundial island at night, lit ONLY by visible orbs (each a POINT
light, r 0.03, inside a camera/glossy-only halo).  One white orb pops on (f16), glides, then splits (f51-61) into
coral / lime / blue lights whose powers (0.49 / 1.05 / 0.94 x 150 W) sum to neutral white.  Where all three reach
the plate stays white, where exactly one is blocked the shadow shows its complement (lemon-yellow / aqua / violet),
where two are blocked the remaining primary, and only the triple-occluded core is black.  A +120 deg carousel
(f61-91) reproduces the f61 shadow geometry exactly with permuted colours at f91; the lights re-merge (f91-101) and
swap back to the white orb at f101 (co-located, equal total power: invisible swap).
Launch (f106-120): the orb crouches, springs off along the sun direction and dissolves while the world blooms
0 -> 0.32, the camera background sweeps navy -> indigo -> lilac -> sky and the camera dollies in to the day framing.
Phase B (f121-240), env map.  Locked framing, no lamps: the only light is assets/hdri/candy_sky_4k.hdr (MANUAL
sampling, 4096 map).  The map snaps +90 deg four times ON the beats 136/151/166/181 (detent), returns to theta=360
at f195 (== f135), glides back to 315 (f196-225) and tilts about X (f226-240).  The sky globe carries the env
texture and turns in lockstep; the gnomon shadow lands on the hue tick under it (315 + theta: pink, lemon, mint,
blue, pink, violet), the chrome probe shows the cards and sun turning, the coloured skylight sweeps the clay bunny.

How phase B is rendered (round 2): in the ENV's frame of reference.  The world mapping is fixed; every object, lamp
and the camera are children of one empty "EnvFrame" whose rotation is the mapping rotation M = Rz(-theta)*Rx(-phi)
(Euler (-phi, 0, -theta)).  Light from scene direction d is E(M d) in both formulations, and camera and set move
rigidly together, so every frame is the same image as "locked camera + rotating env" -- but Cycles now motion-blurs
the env rotation (it does not blur world-mapping changes): during the snaps the shadows, probe reflection and
skylight smear with the same 0.5 shutter as the globe and crank, instead of strobing between sharp positions.
Motion steps 3 (9 time samples) on every object and the camera keep the rigid co-rotation sharp (chord error < 0.3 px).

Debug hooks (env vars; defaults are the shot): S01_TOP=1 square ortho top view (shadow azimuth / layout checks);
S01_CAMB (phase-B camera "x,y,z,tx,ty,tz"), S01_LIFT, S01_SAT, S01_GLOBE_EMIT, S01_CAKE_H, S01_RC, S01_HOFF,
S01_HALO, S01_CAM, S01_PROBE, S01_BUNNY, S01_WORLD, S01_MOON, S01_GLOW, S01_GLOW_SIZE, S01_NIGHT_GLOSS,
S01_NIGHT_TOP/BOT, S01_DAY_TOP/BOT.

Round 2 changelog (lead notes docs/lead_notes_r2.md + critic review; hit frames, cut, colour pipeline unchanged)
------------------------------------------------------------------------------------------------------------
R1. Lead S01.1 -- tighter day framing: during the launch the camera dollies in (f108-120, log-distance, slerped view
    direction, ease_in_out_sine: zero velocity at both ends, the camera is static f105-108, so C1 throughout) to a
    phase-B pose (-0.06,-5.546,2.118) -> (-0.06,0.12,0.00), 46 mm: the plate spans 63.9 % of the frame width, nodus
    top 80 px, cake bottom 1025 px; nothing in the lat-long strip box, only the blue cake band under the caption
    zone.  The pose is locked exactly f121-240.  Phase A keeps the round-1 wide framing (orb headroom).
R2. Lead S01.2 -- sky globe r 0.20 -> 0.26 on a gold stand (stem 0.20, meridian 0.295), moved (-0.32,0.86) ->
    (-0.45,0.95) so the thicker nodus never overlaps it (centre 0.35 m from the 135 deg ray, 5 cm from the pip);
    day emission 0.3 -> 0.6, texture saturation x1.8, coat 1.0 -> 0.5 (cards not washed by sky reflections); bigger
    pink crank (arm 0.23, knob r 0.045) so the turning reads.  Ray-cast: 111/116 visible-hemisphere samples
    unobstructed from the phase-B camera (the rest hit its own meridian).
R3. Lead S01.3 + G2 -- tinted shadows and coloured skylight: day light = SUN part + SKY part of the same map.
    sun = max(candy_sky - candy_sky_nosun, 0) keeps its calibrated colour and power (sunlit plate, shadow geometry
    unchanged); the sky part (candy_sky_nosun, same mapping) is saturated x1.8 and weighted x1.25, so shadows read
    lavender-blue (gnomon shadow L*47 a*+10 b*-18, C* ~20; round 1 measured C* 6) and the white clay picks up the sky
    and card colours.  The same sky part x1.5 is added for GLOSSY rays only (critic "grey probe"): the probe and the
    candy coats reflect a bright candy sky (one-sky motif) with no hotter glints.
R4. Critic "strobing clicks" -- env rotation is motion-blurred for real (EnvFrame, see above) instead of the
    suggested 5-pass sub-frame supersampling (which at 26 deg/f would show 5 discrete shadow copies); zero extra cost.
R5. Critic "off-beat accents" (hit frames unchanged):
    * clicks snap ON the beat: c(t) = ease_out_back(t/12, s=0.87), t = f - f_k: 26 deg on the first frame, 2.5 deg
      detent overshoot at t~8, exactly 1 from t=12 (f135 and f193-195 are static, so the f195 = f135 loop holds);
      the landed tick pops at t=6-10 (when the shadow arrives) with a volume-preserving squash-stretch, amp 0.30.
    * split: lights travel S -> slot with ease_in_out_sine over f51-61 (peak 0.11 m/f, was 0.235) and LAND on f61
      (zero velocity); the coloured halos pop 0 -> 1.2 peaking on f61 and settle by ~f71 (f91 geometry still equals
      f61 with colours permuted: halo size does not light anything).
    * launch: crouch f101-105 (squash along the sun direction, bottoming on f105), release + stretch (1.30 / 0.88,
      volume-preserving) on f106 as the ease_in_cubic flight begins.
R6. Critic "opaque halos pop" -- halos are additive: Emission(k/2) + Transparent on both faces, so a lone halo reads
    exactly like the old opaque k halo but overlaps SUM like the lights: coral+lime = yellow, lime+blue = aqua,
    coral+blue = violet, all three = white.  Coloured halo emission = 2.0 x (0.49, 1.05, 0.94), so full overlap is
    neutral.  At the split W shrinks inside the growing coloured halos (f51-56) instead of cutting at f51; at the
    merge W grows under the converging halos (f97-101), so there is no size dip.  Bloom (G1 parameters) unchanged.
R7. Critic "parked black halo speck" -- W's halo dissolves INSIDE the frame (scale and emission -> 0, ease_in_cubic
    f107-111, last seen ~60 px below the top edge) and is render-hidden from f112; coloured halos are hidden outside
    f51-103.  No speck in the probe.
R8. Critic "hidden ending" -- the glide is REVERSED: theta 360 -> 315 (f196-225), the shadow sweeps from the pink
    tick across the open front of the dial onto the VIOLET tick (270 deg; measured 269.2), in clear view; the sun is
    then directly behind the island (azimuth 90), so the tilt is about world X (mapping Euler (-phi, 0, -theta),
    GlobeTilt.x = +phi; phi > 0 raises the sun) and the nodus shadow breathes toward / away from the camera.  The
    violet tick pops f225-229.  meta: theta_deg ends at 315, new key "tilt_axis": "x"; scripts/make_overlays.py
    Strip reads that key (default "y") so the lat-long strip tilts about the same axis.  NEEDS LEAD SIGN-OFF
    (storyboard sec. 4 glide target 405 and sec. 7 QA "0 deg (f225)" become 315 / "270 deg (f225)").
R9. Critic "pale day" -- ring white -> candy aqua; cake (saturated blue block) 0.26 -> 0.30 m tall and ~2x larger on
    screen with the tighter framing.  Day frames: 8-9 % of pixels at C* > 40 (round 1: 3.5 %), frame mean C* ~21.
R10. Critic minors adopted: gnomon r 0.032 -> 0.045 (collar 0.08) and nodus 0.10 -> 0.12 (bolder clock hand and
    landing blob); moon rim 180 -> 350 W with the gnomon collar, globe stem and meridian excluded (lavender glints,
    plate top black; f10 mean 20/255, was 10); night glossy sky 1.0 -> 2.0 (probe reads indigo chrome with three
    orb highlights; triple-occluded core still 0-2/255).  Rejected: the "Venn rings" beat is dropped (never readable
    from this camera); RC 0.5 kept (the pastel drift of the night plate is physically correct); halo radius kept 0.08.
R11. Persistent-data guard (new, see the EnvFrame block): Cycles 4.5 dropped the metal objects and the globe from a
    static frame rendered right after a moving frame in the same process; a 10-micron rig jitter at half frames
    keeps motion data on every object in every frame.  Invisible; f195 == f135 still 0.043/255 (full preview).
R12. Final sample budget (G4 cap 0.4 GPU-h; the tighter framing alone makes day frames ~1.65x costlier): night and
    launch frames f1-120 keep 384 spp, day frames f121-240 use 256 spp (vs 384: mean |diff| 0.22-0.25/255, only on
    anti-aliased edges).  Uncontended 3.8-4.0 s/frame at 1080p -> ~0.27 GPU-h for the shot.

Deviations from docs/storyboard.md kept from round 1 (visual / tunable only)
---------------------------------------------------------------------------
 1. Split-light circle r 0.80 -> 0.50 around (0, 0.05), all three on a level ring at z 1.75 (whiter plate; "each
    light keeps its height" and "f91 = f61 geometry, colours permuted" both exactly true).
 2. Halo radius 0.065 -> 0.08 and an Emit-pass-only compositor BLOOM (threshold 0.6, smoothness 0.2, strength 1.0,
    size 0.45 relative to the image, saturation 1.0).  These are the film-wide G1 parameters -- do not change them.
 3. Phase-A camera 46 mm, (0,-7.20,3.00) -> target (0,0.10,0.38) with a 4.5 % push-in along the view axis.
 4. Probe (-1.05,-0.32) r 0.30 and clay bunny (1.00,-0.50) yaw -28 h 0.44 (storyboard spots hid two landings).
 5. Hue ticks r 0.052, length 0.25, centred at r 1.27 (pips too); pivots at the contact point.
 6. Gold collar seats the candy-cane gnomon.
 7. World day strength 0.45 -> 0.32 (sunlit plate ~0.88 display, the storyboard's own target).
 8. Launch: world bloom smoothstep over f106-121; the orb power fades as 150 x (1 - bloom) (no flash).
 9. Camera background: static screen-space vertical gradient (Window.y; cannot strobe), night ink -> #2A2152, day
    lavender -> sky, dawn path through indigo and lilac with perceptually spaced sRGB stops.
10. f1-15 glossy-only light-linked lavender MoonRim AREA light; off by f19.
11. Phase-A night sky for GLOSSY rays only (navy -> indigo); diffuse rays never see it (no fill).
12. Globe emission 0 at night, keyed with the bloom by day.
13. Extra meta keys "camera_view_az_deg" (90.0) and "tilt_axis".
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

SHOT = "s01_lights_world"
N = 240
args = D.parse_args()
DEBUG_TOP = os.environ.get("S01_TOP") == "1"

D.reset_scene()
D.setup_cycles(samples=384, threshold=0.008, min_samples=32, diffuse=4, glossy=6, transmission=4,
               caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)
D.setup_color(exposure=-0.2)
D.setup_output()
sc = bpy.context.scene
sc.frame_end = N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False

rad = math.radians


def envf(name, default):
    return float(os.environ.get(name, default))


def envv(name, default):
    return [float(v) for v in os.environ.get(name, default).split(",")]


def bake(target, path, fn):
    D.bake(target, path, 1, N, fn)


# =============================================================================================================
# Closed-form timing (local frame f, 1..240).  theta / phi in degrees -> also written to renders/meta.
# =============================================================================================================
CLICKS = (136, 151, 166, 181)
CLICK_LEN, CLICK_BACK = 12, 0.87
GLIDE = 45.0                      # theta 360 -> 315 (reversed: the landing ray faces the camera)
THETA_END = 360.0 - GLIDE


def click_c(t):
    """Beat-quantised snap: ease_out_back over 12 frames from the beat frame (t = f - f_k).
    26 deg on the first frame, 2.5 deg detent overshoot at t~8, exactly 1 for t >= 12."""
    if t <= 0:
        return 0.0
    if t >= CLICK_LEN:
        return 1.0
    return D.ease_out_back(t / CLICK_LEN, CLICK_BACK)


def theta_deg(f):
    if f <= 135:
        return 0.0
    if f <= 195:
        k = min(3, (f - 136) // 15)
        return 90.0 * k + 90.0 * click_c(f - CLICKS[k])
    if f <= 225:
        return 360.0 - GLIDE * D.ease_in_out_sine((f - 196) / 29.0)
    return THETA_END


def world_k(f):
    """Day bloom 0 -> 1 over f106-121.  Smoothstep (slow start) so the sky blooms in the orb's wake; the orb's power
    fades as (1 - world_k), which keeps the plate brightness flat-to-rising through the hand-off (no flash)."""
    return D.smoothstep(D.prog(f, 106, 121))


def phi_deg(f):
    """Tilt about world X (sun at azimuth 90 after the glide): +phi raises the sun, so the first swing shortens the
    nodus shadow (its far excursion stays on the plate)."""
    if f < 226:
        return 0.0
    t = (f - 226) / 30.0
    return 6.0 * math.exp(-3.0 * t) * math.sin(2 * math.pi * 2.0 * t)


# =============================================================================================================
# Materials (dopa + the custom setups this shot owns: candy-cane stripes, globe env material, halo marker)
# =============================================================================================================
def mat_candy_cane(c1="pink", c2="white"):
    """Helical candy-cane stripes: fract(14 z/1.03 + atan2(y,x)/2pi) < .5, candy params (rough .22, coat 1)."""
    m, n, l, p = D._new_mat("candy_cane")
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    at = n.new("ShaderNodeMath")
    at.operation = "ARCTAN2"
    l.new(sep.outputs["Y"], at.inputs[0])
    l.new(sep.outputs["X"], at.inputs[1])
    a = n.new("ShaderNodeMath")
    a.operation = "MULTIPLY_ADD"          # z * 14/1.03 + atan/2pi
    l.new(sep.outputs["Z"], a.inputs[0])
    a.inputs[1].default_value = 14.0 / 1.03
    b = n.new("ShaderNodeMath")
    b.operation = "MULTIPLY"
    l.new(at.outputs[0], b.inputs[0])
    b.inputs[1].default_value = 1.0 / (2 * math.pi)
    l.new(b.outputs[0], a.inputs[2])
    fr = n.new("ShaderNodeMath")
    fr.operation = "FRACT"
    l.new(a.outputs[0], fr.inputs[0])
    lt = n.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    l.new(fr.outputs[0], lt.inputs[0])
    lt.inputs[1].default_value = 0.5
    mx = n.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    l.new(lt.outputs[0], mx.inputs["Factor"])
    mx.inputs["A"].default_value = D.col(c2)
    mx.inputs["B"].default_value = D.col(c1)
    l.new(mx.outputs["Result"], p.inputs["Base Color"])
    D._set(p, rough=0.22, coat=1.0, coat_rough=0.03, sss=0.08, sss_scale=0.03)
    return m


GLOBE_EMIT = envf("S01_GLOBE_EMIT", "0.6")
GLOBE_SAT = envf("S01_GLOBE_SAT", "1.8")
GLOBE_COAT = envf("S01_GLOBE_COAT", "0.5")


def mat_globe():
    """Globe env material: Texture Coordinate Object -> Environment Texture(candy_sky_preview.png) (x saturation)
    -> Base Color, the same x GLOBE_EMIT -> Emission (keyed with the world bloom so the night stays lamp-only)."""
    m, n, l, p = D._new_mat("globe_env")
    tc = n.new("ShaderNodeTexCoord")
    env = n.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(D.ASSETS, "hdri", "candy_sky_preview.png"), check_existing=True)
    env.interpolation = "Linear"
    l.new(tc.outputs["Object"], env.inputs["Vector"])
    src = env.outputs["Color"]
    if GLOBE_SAT != 1.0:
        hs = n.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = GLOBE_SAT
        l.new(src, hs.inputs["Color"])
        src = hs.outputs["Color"]
    l.new(src, p.inputs["Base Color"])
    l.new(src, p.inputs["Emission Color"])
    D._set(p, rough=0.25, coat=GLOBE_COAT, coat_rough=0.05, emission_strength=0.0)
    m.cycles.emission_sampling = "NONE"
    return m, p


def mat_halo(color, total):
    """Light-marker halo (storyboard material #3), ADDITIVE: Emission(total/2) + Transparent.  A camera or glossy
    ray crosses both faces of the sphere, so a lone halo is a flat disc of radiance `total` (same look as the
    opaque marker) while overlapping halos sum like the lights they mark.  Never lit, never lights."""
    m, n, l, p = D._new_mat(f"halo_{color}")
    n.remove(p)
    e = n.new("ShaderNodeEmission")
    e.name = "Emission"
    e.inputs["Color"].default_value = D.col(color)
    e.inputs["Strength"].default_value = total / 2.0
    t = n.new("ShaderNodeBsdfTransparent")
    a = n.new("ShaderNodeAddShader")
    l.new(e.outputs[0], a.inputs[0])
    l.new(t.outputs[0], a.inputs[1])
    l.new(a.outputs[0], n["Material Output"].inputs["Surface"])
    m.cycles.emission_sampling = "NONE"
    return m


def halo_flags(ob):
    ob.visible_camera = True
    ob.visible_glossy = True
    ob.visible_diffuse = False
    ob.visible_transmission = False
    ob.visible_shadow = False
    ob.visible_volume_scatter = False


# =============================================================================================================
# Set: floating candy sundial island
# =============================================================================================================
plate = D.cylinder("Plate", 1.45, 0.20, (0, 0, -0.10), bevel=0.06,
                   mat=D.mat_clay("offwhite", rough=0.6, sss=0.05, sheen=0.15))
CAKE_H = envf("S01_CAKE_H", "0.30")
cake = D.cylinder("Cake", 1.36, CAKE_H, (0, 0, -0.20 - CAKE_H / 2), bevel=0.08, mat=D.mat_candy("blue"))

TICKS = [(315, "pink"), (0, "orange"), (45, "lemon"), (90, "lime"), (135, "mint"), (180, "aqua"),
         (225, "blue"), (270, "violet")]
TICK_R, TICK_RAD, TICK_LEN = 1.27, 0.052, 0.25
TICK_POP = 0.30
ticks = {}
for az, c in TICKS:
    ob = D.capsule(f"Tick_{c}", TICK_RAD, TICK_LEN, mat=D.mat_candy(c))
    # lie the pill along local X with its contact point at the origin (squash/pop pivot at the base)
    ob.data.transform(Matrix.Translation((0, 0, TICK_RAD)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    ob.location = (TICK_R * math.cos(rad(az)), TICK_R * math.sin(rad(az)), 0.0)
    ob.rotation_euler = (0, 0, rad(az))
    ticks[az] = ob

pip_mat = D.mat_clay("white")
for k in range(8):
    a = rad(337.5 + 45 * k)
    D.sphere(f"Pip{k}", 0.03, (TICK_R * math.cos(a), TICK_R * math.sin(a), 0.03), mat=pip_mat, segments=32,
             rings=16)

GN_R, NODUS_R = 0.045, 0.12
gnomon = D.capsule("Gnomon", GN_R, 1.03, (0, 0, 0.515), mat=mat_candy_cane())
collar = D.cylinder("GnomonCollar", 0.08, 0.04, (0, 0, 0), bevel=0.015, base_at_zero=True,
                    mat=D.mat_metal("gold", name="gold_collar", rough=0.2))   # seats the cane in a gold socket
nodus = D.sphere("Nodus", NODUS_R, (0, 0, 1.03), mat=D.mat_candy("lemon"))
_pb = envv("S01_PROBE", "-1.05,-0.32,0.30")
probe = D.sphere("Probe", _pb[2], (_pb[0], _pb[1], _pb[2]), mat=D.mat_metal("chrome", rough=0.02))
_bn = envv("S01_BUNNY", "1.00,-0.50,-28,0.44")
bunny = D.stanford_bunny("BunnyClay", _bn[3], mat=D.mat_clay("white", rough=0.5), location=(_bn[0], _bn[1], 0),
                         rotation=(0, 0, _bn[2]))
ring = D.torus("Ring", 0.20, 0.07, (0.30, 0.90, 0.27), rotation=(90, 0, 15),
               mat=D.mat_candy("aqua", name="candy_aqua_ring", rough=0.18))

# sky globe on a gold stand with a pink crank
GLOBE_R = 0.26
MER_R = GLOBE_R + 0.035
_gc = envv("S01_GLOBE_XY", "-0.45,0.95")
STEM_LEN = 0.20
GC = Vector((_gc[0], _gc[1], 0.04 + STEM_LEN + MER_R))
gold = D.mat_metal("gold", rough=0.2)
pink = D.mat_candy("pink")
globe_mat, globe_bsdf = mat_globe()
tilt = D.empty("GlobeTilt", tuple(GC), size=0.3)
globe = D.sphere("Globe", GLOBE_R, (0, 0, 0), mat=globe_mat)
globe.parent = tilt
meridian = D.torus("GlobeMeridian", MER_R, 0.014, (0, 0, 0), rotation=(90, 0, 30), mat=gold)
meridian.parent = tilt
globe_base = D.cylinder("GlobeBase", 0.16, 0.04, (GC.x, GC.y, 0), bevel=0.015, base_at_zero=True, mat=gold)
globe_stem = D.cylinder("GlobeStem", 0.026, STEM_LEN + 0.01, (GC.x, GC.y, 0.035), bevel=0.006, base_at_zero=True,
                        mat=gold)
crank_post = D.capsule("CrankPost", 0.016, 0.15, (0, 0, GLOBE_R + 0.04), mat=pink)
crank_arm = D.capsule("CrankArm", 0.02, 0.23, (0.095, 0, GLOBE_R + 0.10), rotation=(0, 90, 0), mat=pink)
crank_knob = D.sphere("CrankKnob", 0.045, (0.20, 0, GLOBE_R + 0.10), mat=pink, segments=48, rings=24)
for o in (crank_post, crank_arm, crank_knob):
    o.parent = globe

# =============================================================================================================
# Phase A lights: white orb W + coral / lime / blue split (neutral sum)
# =============================================================================================================
P_W = 150.0
FRAC = {"coral": 0.49, "lime": 1.05, "blue": 0.94}
AZ0 = {"coral": 270.0, "lime": 30.0, "blue": 150.0}
S = Vector((0.0, -0.25, 1.80))
W0, W1 = Vector((-0.40, -0.45, 1.75)), Vector((0.40, -0.45, 1.75))
SUN_DIR = Vector((-0.5417, 0.5417, 0.6428))
CEN = Vector((0.0, 0.05, 0.0))
RC = envf("S01_RC", "0.50")
H_RING = 1.75 + envf("S01_HOFF", "0.0")
HALO_R = envf("S01_HALO", "0.08")
LAMP_R = 0.03
W_EMIT = 4.0                       # white halo radiance (G1: the protagonist orb)
C_EMIT_SUM = 2.0                   # coloured halos: C_EMIT_SUM x FRAC -> the three overlap to neutral white
E_SUN = Vector((0, 0, 1)).rotation_difference(SUN_DIR).to_euler()   # halo local Z -> launch direction


def slot(az):
    a = rad(az)
    return Vector((CEN.x + RC * math.cos(a), CEN.y + RC * math.sin(a), H_RING))


def w_pos(f):
    if f <= 40:
        e = D.ease_in_out_sine(D.prog(f, 16, 40))
        p = W0.lerp(W1, e)
        p.z += 0.08 * math.sin(math.pi * e)
        return p
    if f <= 50:
        return W1.lerp(S, D.ease_in_out_sine(D.prog(f, 40, 50)))
    p = S.copy()
    if f >= 101:
        if f <= 105:      # crouch: pull back 5 cm against the launch direction, bottoming on f105
            d = -0.05 * math.sin(0.5 * math.pi * D.prog(f, 101, 105))
        else:             # launch: one ease_in_cubic flight from the crouch, 4 m along the sun direction by f120
            d = -0.05 + 4.05 * D.ease_in_cubic(D.prog(f, 105, 120))
        p += SUN_DIR * d
    return p


def c_pos(name, f):
    az0 = AZ0[name]
    if f <= 51:
        return S.copy()
    if f <= 61:           # split: travel S -> slot, landing ON f61 with zero velocity
        return S.lerp(slot(az0), D.ease_in_out_sine(D.prog(f, 51, 61)))
    if f <= 91:
        return slot(az0 + 120.0 * D.ease_in_out_sine(D.prog(f, 61, 91)))
    if f <= 101:
        return slot(az0 + 120.0).lerp(S, D.ease_in_out_cubic(D.prog(f, 91, 101)))
    return S.copy()


def w_power(f):
    if f <= 15:
        return 0.0
    if f <= 19:
        return P_W * D.smoothstep((f - 15) / 4.0)
    if f <= 50:
        return P_W
    if f <= 100:
        return 0.0
    return P_W * (1.0 - world_k(f))


def c_power(name, f):
    return P_W * FRAC[name] if 51 <= f <= 100 else 0.0


def w_dissolve(f):
    """1 -> 0 over f107-111 (ease_in_cubic): the orb melts into the blooming sky while still inside the frame."""
    return 1.0 - D.ease_in_cubic(D.prog(f, 107, 111))


def w_halo(f):
    if f <= 15:
        return (0.0, 0.0, 0.0)
    if f <= 45:
        s = D.spring((f - 15) / 30.0, 2.5, 8.0)
        return (s, s, s)
    if f <= 50:           # anticipation squash before the split
        e = D.ease_in_out_sine(D.prog(f, 45, 50))
        return (1 + 0.12 * e, 1 + 0.12 * e, 1 - 0.2 * e)
    if f <= 56:           # split: W shrinks inside the growing coloured halos (additive, so no swap pop)
        k = 1.0 - D.smoothstep(D.prog(f, 51, 56))
        return (1.12 * k, 1.12 * k, 0.8 * k)
    if f <= 96:
        return (0.0, 0.0, 0.0)
    s = D.ease_out_cubic(D.prog(f, 97, 101))    # merge: W grows under the converging halos (no size dip)
    if f <= 105:          # crouch squash along the launch axis (volume-preserving), bottoming on f105
        sz = 1.0 - 0.18 * math.sin(0.5 * math.pi * D.prog(f, 101, 105))
    else:                 # release on the beat: stretch 1.30 / 0.88 on f106, relaxing as it dissolves
        sz = 1.0 + 0.30 * (1.0 - D.smoothstep(D.prog(f, 107, 111)))
    sxy = 1.0 / math.sqrt(sz)
    m = w_dissolve(f)
    return (s * sxy * m, s * sxy * m, s * sz * m)


def w_rot(f):
    return (0.0, 0.0, 0.0) if f <= 98 else tuple(E_SUN)


def w_emit(f):
    k = math.sqrt(max(w_power(f), 0.0) / P_W) if f >= 106 else 1.0
    return W_EMIT * k * w_dissolve(f) / 2.0          # per face (additive halo)


def c_halo(f):
    if f < 51:
        return (0.0, 0.0, 0.0)
    if f <= 61:           # pop out, biggest exactly on the f61 landing
        s = 1.2 * D.ease_out_cubic(D.prog(f, 51, 61))
    elif f <= 98:         # spring settle 1.2 -> 1 with zero velocity at f61
        t, w, d = (f - 61) / 30.0, 2 * math.pi * 2.5, 8.0
        s = 1.0 + 0.2 * math.exp(-d * t) * (math.cos(w * t) + d / w * math.sin(w * t))
    else:
        s = 1.0 - D.ease_in_out_sine(D.prog(f, 98, 103))
    return (s, s, s)


def make_orb(name, color, total):
    lamp = D.light("POINT", name, location=tuple(S), target=None, power=0.0, color=color, radius=LAMP_R)
    halo = D.sphere(name + "_halo", HALO_R, tuple(S), mat=mat_halo(color, total), segments=64, rings=32)
    halo_flags(halo)
    return lamp, halo


orbW, haloW = make_orb("OrbW", "white", W_EMIT)
bake(orbW, "location", lambda f: tuple(w_pos(f)))
bake(haloW, "location", lambda f: tuple(w_pos(f)))
bake(haloW, "scale", w_halo)
bake(haloW, "rotation_euler", w_rot)
bake(orbW.data, "energy", w_power)
bake(haloW.active_material.node_tree.nodes["Emission"].inputs["Strength"], "default_value", w_emit)
D.hide_range(haloW, visible_to=111)            # nothing parked in the sky: no speck in the probe by day
for cname in ("coral", "lime", "blue"):
    lamp, halo = make_orb("Orb_" + cname, cname, C_EMIT_SUM * FRAC[cname])
    bake(lamp, "location", lambda f, c=cname: tuple(c_pos(c, f)))
    bake(halo, "location", lambda f, c=cname: tuple(c_pos(c, f)))
    bake(halo, "scale", c_halo)
    bake(lamp.data, "energy", lambda f, c=cname: c_power(c, f))
    D.hide_range(halo, visible_from=51, visible_to=103)

# =============================================================================================================
# World: candy sky (sun inside the map, fixed mapping -- the set rotates instead), night -> day camera background,
# glossy-only sky lift, moon rim for f1-15
# =============================================================================================================
WORLD_DAY = envf("S01_WORLD", "0.32")
SKY_SAT = envf("S01_SAT", "1.8")
SKY_K = envf("S01_SKY_K", "1.25")
LIFT = envf("S01_LIFT", "1.5")
rig = D.world_hdri(os.path.join(D.ASSETS, "hdri", "candy_sky_4k.hdr"), strength=0.0, camera_bg="ink",
                   glossy_sees_bg=False)
rig.world.cycles.sampling_method = "MANUAL"
rig.world.cycles.sample_map_resolution = 4096
MOON_W = envf("S01_MOON", "350")
moon = D.light("AREA", "MoonRim", location=(0.0, 5.2, 1.6), target=(0, 0, 0.35), power=MOON_W, color="lavender",
               size=4.0)
moon.visible_diffuse = False          # glossy-only: specular rims on the silhouette, no fill on the plate
moon.visible_transmission = False
moon.visible_volume_scatter = False
# light linking: the moon only glints on the props' edges; plate, cake and gold parts stay dark (no orange embers)
moon_rx = bpy.data.collections.new("MoonExclude")
for o in (plate, cake, globe_base, globe_stem, collar, meridian):
    moon_rx.objects.link(o)
moon.light_linking.receiver_collection = moon_rx
for co in moon_rx.collection_objects:
    co.light_linking.link_state = "EXCLUDE"

bake(rig.light_bg.inputs["Strength"], "default_value", lambda f: WORLD_DAY * world_k(f))

wn = rig.world.node_tree
lpn = wn.nodes.new("ShaderNodeLightPath")

# Night sky for GLOSSY rays only (phase A): mirrors and coats reflect the same navy -> indigo night the camera sees,
# instead of black.  Diffuse rays never see it (no fill; shadow cores stay black), and it fades with the bloom.
tcn = wn.nodes.new("ShaderNodeTexCoord")
sepn = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(tcn.outputs["Generated"], sepn.inputs[0])
elev = wn.nodes.new("ShaderNodeMapRange")
elev.interpolation_type = "SMOOTHSTEP"
elev.inputs["From Min"].default_value = -0.1
elev.inputs["From Max"].default_value = 0.8
wn.links.new(sepn.outputs["Z"], elev.inputs["Value"])
nmix = wn.nodes.new("ShaderNodeMix")
nmix.data_type = "RGBA"
wn.links.new(elev.outputs["Result"], nmix.inputs["Factor"])
nmix.inputs["A"].default_value = D.col("#2A2152")
nmix.inputs["B"].default_value = D.col("ink")
nbg = wn.nodes.new("ShaderNodeBackground")
wn.links.new(nmix.outputs["Result"], nbg.inputs["Color"])
nmul = wn.nodes.new("ShaderNodeMath")
nmul.operation = "MULTIPLY"
wn.links.new(lpn.outputs["Is Glossy Ray"], nmul.inputs[0])
wn.links.new(nmul.outputs[0], nbg.inputs["Strength"])
NIGHT_GLOSS = envf("S01_NIGHT_GLOSS", "2.0")
bake(nmul.inputs[1], "default_value", lambda f: NIGHT_GLOSS * (1.0 - world_k(f)))

# Day light = SUN part + SKY part of the same map.  sun = max(full - nosun, 0) (disc + aureole, bit-exact: the two
# files differ only there) keeps its calibrated colour and power, so the sunlit plate and the shadow geometry are
# unchanged; the sky part (candy_sky_nosun through the same mapping) is saturated x SKY_SAT, so the sky fill tints
# every shadow lavender / sky-blue instead of grey (G2).  The same sky part, x LIFT, is added for GLOSSY rays only:
# the probe and the candy coats reflect a bright candy sky (one-sky motif) without hotter glints.
env2 = wn.nodes.new("ShaderNodeTexEnvironment")
env2.image = bpy.data.images.load(os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr"), check_existing=True)
env2.interpolation = "Cubic"
wn.links.new(rig.mapping.outputs[0], env2.inputs["Vector"])
sun_sub = wn.nodes.new("ShaderNodeVectorMath")
sun_sub.operation = "SUBTRACT"
wn.links.new(rig.env.outputs["Color"], sun_sub.inputs[0])
wn.links.new(env2.outputs["Color"], sun_sub.inputs[1])
sun_max = wn.nodes.new("ShaderNodeVectorMath")
sun_max.operation = "MAXIMUM"
wn.links.new(sun_sub.outputs[0], sun_max.inputs[0])
sun_max.inputs[1].default_value = (0.0, 0.0, 0.0)
sky = env2.outputs["Color"]
if SKY_SAT != 1.0:
    hs2 = wn.nodes.new("ShaderNodeHueSaturation")
    hs2.inputs["Saturation"].default_value = SKY_SAT
    wn.links.new(sky, hs2.inputs["Color"])
    sky = hs2.outputs["Color"]
sky_k = wn.nodes.new("ShaderNodeVectorMath")
sky_k.operation = "SCALE"
wn.links.new(sky, sky_k.inputs[0])
sky_k.inputs["Scale"].default_value = SKY_K
light_col = wn.nodes.new("ShaderNodeVectorMath")
light_col.operation = "ADD"
wn.links.new(sun_max.outputs[0], light_col.inputs[0])
wn.links.new(sky_k.outputs[0], light_col.inputs[1])
wn.links.new(light_col.outputs[0], rig.light_bg.inputs["Color"])
gbg = wn.nodes.new("ShaderNodeBackground")
wn.links.new(sky, gbg.inputs["Color"])
gmul = wn.nodes.new("ShaderNodeMath")
gmul.operation = "MULTIPLY"
wn.links.new(lpn.outputs["Is Glossy Ray"], gmul.inputs[0])
wn.links.new(gmul.outputs[0], gbg.inputs["Strength"])
bake(gmul.inputs[1], "default_value", lambda f: WORLD_DAY * LIFT * world_k(f))

nadd = wn.nodes.new("ShaderNodeAddShader")
wn.links.new(rig.light_bg.outputs[0], nadd.inputs[0])
wn.links.new(nbg.outputs[0], nadd.inputs[1])
nadd2 = wn.nodes.new("ShaderNodeAddShader")
wn.links.new(nadd.outputs[0], nadd2.inputs[0])
wn.links.new(gbg.outputs[0], nadd2.inputs[1])
wn.links.new(nadd2.outputs[0], rig.mix.inputs[1])

# Camera background: a static screen-space vertical gradient (Window.y), so nothing in it can strobe.  Each end
# follows its own dawn path, navy -> indigo -> lilac -> pastel (never through grey).
BG_TOP = [os.environ.get("S01_NIGHT_TOP", "ink"), "#3A2E9E", "lilac", os.environ.get("S01_DAY_TOP", "lavender")]
BG_BOT = [os.environ.get("S01_NIGHT_BOT", "#2A2152"), "#4433B0", "lilac", os.environ.get("S01_DAY_BOT", "sky")]


def _srgb(c):
    h = D.PALETTE.get(c, c).lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def path_col(path, f):
    """Dawn sweep: interpolated in sRGB (perceptual) space with stops re-spaced by their sRGB distance, so the
    colour moves at continuous perceptual speed (no rate kink at a stop); smoothstep in time."""
    cols = [_srgb(c) for c in path]
    seg = [math.dist(a, b) for a, b in zip(cols[:-1], cols[1:])]
    tot = sum(seg)
    t = D.smoothstep(D.prog(f, 106, 121)) * tot
    for i, L in enumerate(seg):
        if t <= L or i == len(seg) - 1:
            u = min(1.0, t / L) if L > 0 else 1.0
            a, b = cols[i], cols[i + 1]
            return D.col(tuple(x + (y - x) * u for x, y in zip(a, b)))
        t -= L
    return D.col(tuple(cols[-1]))


tcw = wn.nodes.new("ShaderNodeTexCoord")
sepw = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(tcw.outputs["Window"], sepw.inputs[0])
grad = wn.nodes.new("ShaderNodeMapRange")
grad.interpolation_type = "SMOOTHSTEP"
grad.inputs["From Min"].default_value = 0.05
grad.inputs["From Max"].default_value = 0.95
wn.links.new(sepw.outputs["Y"], grad.inputs["Value"])
bgmix = wn.nodes.new("ShaderNodeMix")
bgmix.data_type = "RGBA"
wn.links.new(grad.outputs["Result"], bgmix.inputs["Factor"])
wn.links.new(bgmix.outputs["Result"], rig.cam_bg.inputs["Color"])
bake(bgmix.inputs["A"], "default_value", lambda f: path_col(BG_BOT, f))
bake(bgmix.inputs["B"], "default_value", lambda f: path_col(BG_TOP, f))
bake(moon.data, "energy", lambda f: MOON_W * (0.75 + 0.25 * D.smoothstep(D.prog(f, 1, 15)))
     * (1.0 - D.smoothstep(D.prog(f, 15, 19))))
bake(globe_bsdf.inputs["Emission Strength"], "default_value", lambda f: GLOBE_EMIT * world_k(f))

# the globe turns in lockstep with the env (relative to the set): yaw +theta, tilt +phi about X
bake(tilt, "rotation_euler", lambda f: (rad(phi_deg(f)), 0.0, 0.0))
bake(globe, "rotation_euler", lambda f: (0.0, 0.0, rad(theta_deg(f))))


# tick pops: the tick under the shadow pops when the shadow arrives (t = 6..10 of each snap), the violet tick at
# the glide landing (f225-229).  Volume-preserving squash-stretch about the contact point, ends exactly at 1.
GLIDE_TICK = int(round(315 + THETA_END)) % 360


def tick_scale_fn(az):
    events = [fk + 6 for k, fk in enumerate(CLICKS) if (315 + 90 * (k + 1)) % 360 == az]
    if az == GLIDE_TICK:
        events.append(225)

    def fn(f):
        sz = 1.0
        for e in events:
            if e <= f <= e + 4:
                sz += TICK_POP * math.sin(math.pi * (f - e) / 4.0)
        sxy = 1.0 / math.sqrt(sz)
        return (sxy, sxy, sz)
    return fn, events


for az, ob in ticks.items():
    fn, ev = tick_scale_fn(az)
    if ev:
        bake(ob, "scale", fn)

# =============================================================================================================
# Camera: phase-A wide framing with a slow push-in, a dolly-in during the launch, phase-B pose locked f121-240.
# Poses are in the set's frame (the camera is a child of EnvFrame).
# =============================================================================================================
focus = D.empty("Focus", (0, 0, 0.3))
_cs = envv("S01_CAM", "0,-7.20,3.00,0,0.10,0.38,46")
CAM1, TGT_A, LENS = Vector(_cs[0:3]), Vector(_cs[3:6]), _cs[6]
CAM0 = CAM1 + 0.045 * (CAM1 - TGT_A)     # phase-A push-in along the view axis
_cb = envv("S01_CAMB", "-0.06,-5.546,2.118,-0.06,0.12,0.00")
CAM_B, TGT_B = Vector(_cb[0:3]), Vector(_cb[3:6])
DOLLY = tuple(int(v) for v in os.environ.get("S01_DOLLY", "108,120").split(","))


def cam_pose(f):
    if f <= 105:
        P, T = CAM0.lerp(CAM1, D.ease_in_out_sine(D.prog(f, 1, 105))), TGT_A
    else:                 # log-distance dolly with a slerped view direction (C1: zero velocity at both ends)
        e = D.ease_in_out_sine(D.prog(f, *DOLLY))
        T = TGT_A.lerp(TGT_B, e)
        dA, dB = CAM1 - TGT_A, CAM_B - TGT_B
        q = Quaternion().slerp(dA.normalized().rotation_difference(dB.normalized()), e)
        P = T + (q @ dA.normalized()) * (dA.length * (dB.length / dA.length) ** e)
    return P, (T - P).to_track_quat("-Z", "Y").to_euler()


cam, cam_tgt = D.camera("Cam", location=tuple(CAM0), target=tuple(TGT_A), lens=LENS, fstop=4.0, focus=focus,
                        sensor=36)
cam.constraints.clear()
bake(cam, "location", lambda f: tuple(cam_pose(f)[0]))
bake(cam, "rotation_euler", lambda f: tuple(cam_pose(f)[1]))

if DEBUG_TOP:
    cd = bpy.data.cameras.new("TopCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 3.3
    cd.clip_end = 50
    top = D.link(bpy.data.objects.new("TopCam", cd))
    top.location = (0, 0, 8)
    sc.camera = top
    sc.render.resolution_x = sc.render.resolution_y = 1080

# =============================================================================================================
# EnvFrame: the whole set, its lamps and the camera rotate by the mapping rotation M = Rz(-theta) Rx(-phi), the
# world map stays put -> identical images to "locked camera + rotating env", with real motion blur of the rotation.
# =============================================================================================================
spin = D.empty("EnvFrame", (0, 0, 0), size=0.5)
for ob in list(bpy.data.objects):
    if ob is not spin and ob.parent is None:
        ob.parent = spin
bake(spin, "rotation_euler", lambda f: (-rad(phi_deg(f)), 0.0, -rad(theta_deg(f))))
# Persistent-data guard: Cycles 4.5 drops some objects (metals, globe) from a STATIC frame rendered right after a
# MOVING frame in the same process (object motion data switched off between renders).  A 10-micron vertical
# jitter of the whole rig at half frames (integer frames exact) gives every object motion data in EVERY frame, so
# that switch never happens.  Camera and set move together, so it is invisible (and f135 == f195 still holds).
MICRO = envf("S01_MICRO", "1e-5")
for f in range(1, N + 1 if MICRO > 0 else 1):
    spin.location = (0.0, 0.0, 0.0)
    spin.keyframe_insert("location", frame=f)
    spin.location = (0.0, 0.0, MICRO)
    spin.keyframe_insert("location", frame=f + 0.5)
spin.location = (0.0, 0.0, 0.0)
D.linearize(spin)
MB_STEPS = int(envf("S01_MB_STEPS", "3"))
for ob in bpy.data.objects:
    if ob.type in ("MESH", "CAMERA"):
        ob.cycles.use_motion_blur = True
        ob.cycles.motion_steps = MB_STEPS
        ob.cycles.use_deform_motion = False

# =============================================================================================================
# Orb glow (G1, film-wide parameters -- keep unchanged): bloom driven by the Emit pass only, so only the halo
# markers glow (lit surfaces never bloom).  BLOOM size is relative to the image, so draft / preview / final match.
# =============================================================================================================
GLOW = envf("S01_GLOW", "1.0")
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
    gl.inputs["Size"].default_value = envf("S01_GLOW_SIZE", "0.45")
    gl.inputs["Saturation"].default_value = 1.0
    ct.links.new(rl.outputs["Emit"], gl.inputs["Image"])
    add_glow = ct.nodes.new("CompositorNodeMixRGB")
    add_glow.blend_type = "ADD"
    add_glow.inputs["Fac"].default_value = 1.0
    ct.links.new(rl.outputs["Image"], add_glow.inputs[1])
    ct.links.new(gl.outputs["Glare"], add_glow.inputs[2])
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(add_glow.outputs[0], comp.inputs["Image"])

# =============================================================================================================
# Metadata for overlays (written at build time, every mode)
# =============================================================================================================
meta = {
    "id": SHOT, "frames": N, "start_frame_in_film": 1,
    "events": {"orb_on": 16, "split": 51, "split_lands": 61, "carousel_done": 91, "merge": 101, "launch": 106,
               "day": 121, "click1": 136, "click2": 151, "click3": 166, "click4": 181, "loop_check": 195,
               "glide_start": 196, "glide_end": 225, "tilt": 226},
    "camera_view_az_deg": round(math.degrees(math.atan2(TGT_B.y - CAM_B.y, TGT_B.x - CAM_B.x)), 2),
    "tilt_axis": "x",
    "mapping_rotation": "world env lookup R = Rz(-theta_deg) * Rx(-tilt_deg) (Blender Euler XYZ (-tilt, 0, -theta))",
    "per_frame": {"theta_deg": [round(theta_deg(f), 4) for f in range(1, N + 1)],
                  "tilt_deg": [round(phi_deg(f), 4) for f in range(1, N + 1)]},
}
meta_dir = os.path.join(D.ROOT, "renders", "meta")
os.makedirs(meta_dir, exist_ok=True)
with open(os.path.join(meta_dir, f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)

# Final-mode sample budget (G4 cap 0.4 GPU-h): the night / launch frames keep 384 spp for their coloured penumbrae;
# the day frames (f121-240, smooth sunlit surfaces) use 256 spp -- measured vs 384: mean |diff| 0.22-0.25/255,
# differences only on anti-aliased edges.  Explicit --samples still overrides everything.
FINAL_SPP_NIGHT, FINAL_SPP_DAY = 384, int(envf("S01_SPP_DAY", "256"))
if args.mode == "final" and args.samples is None:
    def _final_spp(scene, depsgraph=None):
        scene.cycles.samples = FINAL_SPP_NIGHT if scene.frame_current <= 120 else FINAL_SPP_DAY
    bpy.app.handlers.frame_change_pre.append(_final_spp)

D.finish(args, final_samples=FINAL_SPP_NIGHT, final_threshold=0.008, frame_end=N, shot_name=SHOT)
