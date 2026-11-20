"""T1 tile · t_glass_armadillo — "Tinted glass + caustics" (finale honeycomb mini scene, storyboard_v2 section 5).

An aqua tinted-glass armadillo turns slowly on a white candy turntable in a butter cove.  One small spot light behind
and above it is the only hard light, so the glass focuses it into crisp aqua caustics that spill forward across the
turntable toward the lens and change shape as the body turns (they cannot be decals).

Tile contract (storyboard_v2 sections 4-5)
* 1152 x 998 final (preview 50 %), flat-top hexagon inscribed in the image: everything that matters sits inside
  the hexagon.  Hero (armadillo + turntable) centred, ~60 % of the hex height, readable as a silhouette at 200 px.
* Seamless loop of LOOP frames: frame LOOP+1 == frame 1 (closed-form periodic animation, keys baked one frame past
  both ends so the f1 and f(LOOP+1) shutters see the same motion).
* Static seed, D.bake, PBR Neutral, exposure -0.2, no AgX / Filmic.  Meta: renders/meta/t_glass_armadillo.json.

Build decisions (v2 build; every number below was A/B'd on half-res / final test frames)
* Caustic convergence.  Brute-force path tracing through the scan (IOR 1.5, small spot) gives a firefly speckle
  even at 2048 spp, and Cycles MNEE (shadow caustics) only a dim, uniform aqua fill at ~3x the cost.  What works:
  Filter Glossy 0.2 (T_FG), which roughens the glass only on paths that already bounced off a diffuse surface, so the
  spot can be sampled directly through the exit interface: the caustic converges at 384 spp and stays stable.
  The camera still sees perfectly smooth glass (camera paths are not blurred).
* Focus.  The armadillo's blobby limbs focus light only centimetres behind themselves at IOR 1.5; IOR 1.3 (T_IOR)
  moves the focus toward the floor, so the caustic is a bright aqua pool, not a dim haze.  Smooth modifier (6 x 0.5)
  softens the scan's scale bumps (cleaner caustic and refraction; silhouette unchanged).
* Spot r 0.04 at (0.30, 0.95, 1.95), 450 W, aimed down-forward: crisp shadow outline, the whole shadow / caustic lands
  on the white turntable (a lower spot threw part of it onto the butter floor as a green smudge).
* No grey, true colours: the wash is light-linked to the cove only and the cove is invisible to diffuse bounce, so
  the turntable shadow keeps its contrast (lavender fill #DCD0FF, light-linked to hero + turntable); the cove is
  invisible to glossy / transmission rays and those rays see the candy sky (0.9) with a cream ground, so the glass
  reads candy aqua (through the butter wall it read olive-teal).  Glass = S02's candy_glass (tint aqua^0.5, Beer
  absorption 0.5).
* Motion: 90-frame seamless loop, slow turn yaw = 200 deg + 30 deg sin(2 pi phase) (<= 2.1 deg/f; a full turn in
  90 f needs 4 deg/f and shows the back), object motion blur off on the glass (slow, and cheaper).
* Hero 62 % of the hex height (70 mm, 20 deg elevation), nothing outside the 0.94 hex.
* Final: 384 spp, adaptive 0.02, OIDN: 2.41 s/f steady on one H200, uncontended (first frame of a process ~3.3 s)
  -> 90 x 2.41 s = 0.060 GPU-h (cap 0.12).  384 vs 1024 spp: mean |d| 0.66/255, caustic visually identical.

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_glass_armadillo.py -- --mode preview
QA:   env T_MASK=1 renders a white-on-black silhouette of the hero (framing / hex-fit measurement).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

SHOT = "t_glass_armadillo"
RES = (1152, 998)
BG = "butter"


def envf(name, dflt):
    return float(os.environ.get(name, str(dflt)))


def envv(name, dflt):
    return Vector(tuple(float(x) for x in os.environ.get(name, dflt).split(",")))


LOOP = int(envf("T_LOOP", 90))
N = LOOP
FINAL_SPP = int(envf("T_SPP", 384))
FINAL_THR = envf("T_THR", 0.02)
MEASURED_FINAL_SPF = 2.41  # GPU 6 (H200), --mode final 1152x998, steady state, uncontended (re-measured)

args = D.parse_args()
D.reset_scene()
# clamp_indirect 0: a clamp below the spot's radiance scales every caustic sample down (S02 lesson, lead notes G5)
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=int(envf("T_MINSPP", 64)), diffuse=3, glossy=4,
               transmission=int(envf("T_TB", 12)), volume=0, caustics=True, filter_glossy=envf("T_FG", 0.2),
               clamp_indirect=envf("T_CLAMP", 0.0), motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("T_EXPO", -0.2))
D.setup_output(res=RES)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False


def phase(f):
    """Loop phase in turns, NOT wrapped: f = LOOP+1 gives exactly 1.0."""
    return (f - 1) / float(LOOP)


def bake(target, path, fn, index=-1):
    D.bake(target, path, 0, LOOP + 2, fn, index=index)


def candy_glass(color, absorb=2.0, name=None, tint_exp=0.5):
    """S02's helper (lead notes G5): surface tint = colour^0.5 because Cycles tints at both interfaces of a closed
    solid; Beer-Lambert absorption then deepens the thick parts."""
    m = D.mat_glass(color, name=name, absorb=absorb, ior=envf("T_IOR", 1.3))
    c = D.col(color)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        c[0] ** tint_exp, c[1] ** tint_exp, c[2] ** tint_exp, 1.0)
    return m


def linked_light(name, loc, target, power, color, size, receivers, glossy=False):
    """AREA light that lights ONLY `receivers` (light linking), invisible to transmission (and glossy) rays."""
    lt = D.light("AREA", name, loc, target, power=power, color=color, size=size)
    lt.visible_glossy = glossy
    lt.visible_transmission = False
    coll = bpy.data.collections.new(name + "_link")
    for ob in receivers:
        coll.objects.link(ob)
    lt.light_linking.receiver_collection = coll
    return lt


# ----------------------------------------------------------------------------------------------
# set: butter cove, white candy turntable (the caustic receiver), aqua glass armadillo
# ----------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=12.0, height=7.0, radius=1.4, wall_y=envf("T_WALLY", 2.4),
                   mat=D.mat_clay(BG, name="clay_cove", rough=0.65, sss=0.0, sheen=0.1))
# the glass refracts / reflects the candy sky instead of the butter cove (butter seen through aqua glass reads
# olive-green): the cove is invisible to transmission and glossy rays, the turntable stays visible to both
cove.visible_transmission = bool(os.environ.get("T_COVE_TRANS"))
cove.visible_glossy = bool(os.environ.get("T_COVE_TRANS"))
TT_R, TT_H = envf("T_TT_R", 0.55), 0.06
tt = D.cylinder("Turntable", TT_R, TT_H, (0, 0, 0), base_at_zero=True, bevel=0.025,
                mat=D.mat_clay("white", name="clay_tt", rough=0.5, sss=0.0, sheen=0.1))
pivot = D.empty("Pivot", (0, 0, TT_H))
ARM_H = envf("T_ARM_H", 0.80)
arm = D.import_obj(os.path.join(D.ASSETS, "models", "armadillo.obj"), name="GlassArmadillo")
D.normalize(arm, size=ARM_H, axis="z")
if envf("T_SMOOTH", 6) > 0:          # soften the scan's scale bumps so the glass focuses cleaner caustics
    _sm = arm.modifiers.new("Smooth", "SMOOTH")
    _sm.factor = 0.5
    _sm.iterations = int(envf("T_SMOOTH", 6))
D.assign(arm, candy_glass("aqua", absorb=envf("T_ABSORB", 0.5), name="glass_aqua",
                          tint_exp=envf("T_TINT_EXP", 0.5)))
arm.parent = pivot
if os.environ.get("T_ARM_MB", "0") == "0":     # object motion blur off (slow turn): cheaper glass traversal
    arm.cycles.use_motion_blur = False
ARM_YAW0 = envf("T_YAW0", 200.0)
HERO = [tt, arm]

# ----------------------------------------------------------------------------------------------
# light: one small spot (the caustic light) behind / above, soft studio fill, candy sky for reflections
# ----------------------------------------------------------------------------------------------
SPOT_POS = envv("T_SPOT_POS", "0.30,0.95,1.95")
SPOT_AIM = envv("T_SPOT_AIM", "0,-0.10,0.20")
spot = D.light("SPOT", "CausticSpot", tuple(SPOT_POS), tuple(SPOT_AIM), power=envf("T_SPOT", 450), color="#FFF8EC",
               radius=envf("T_SPOT_R", 0.04), spot_deg=envf("T_SPOT_DEG", 60), blend=0.5)
spot.visible_glossy = True
# fill: a soft lavender-sky light on the hero and the turntable only, so the shadow reads tinted, never grey, while
# the caustic keeps its contrast
fill = linked_light("Fill", tuple(envv("T_FILL_POS", "-1.6,-2.4,2.2")), (0, 0, 0.3), envf("T_FILL", 18),
                    os.environ.get("T_FILL_C", "#DCD0FF"), 2.4, [tt, arm], glossy=True)
# wash: the butter backdrop only (light-linked to the cove); the cove is invisible to diffuse rays, so its bright
# bounce cannot fill the turntable shadow
wash = linked_light("Wash", tuple(envv("T_WASH_POS", "0.0,-1.0,3.0")), (0, 1.8, 1.0), envf("T_WASH", 260), "white",
                    3.0, [cove])
cove.visible_diffuse = bool(os.environ.get("T_COVE_BOUNCE"))
sky_path = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
WORLD_K = envf("T_WORLD", 0.2)
WORLD_GLOSSY = envf("T_WGLOSSY", 0.9)
rig = D.world_hdri(sky_path, WORLD_K, camera_bg=BG)
_wn, _wl = rig.world.node_tree.nodes, rig.world.node_tree.links
_lp = _wn.new("ShaderNodeLightPath")
_ma = _wn.new("ShaderNodeMath")
_ma.operation = "MULTIPLY_ADD"
_ma.inputs[1].default_value = WORLD_GLOSSY - WORLD_K
_ma.inputs[2].default_value = WORLD_K
_gt = _wn.new("ShaderNodeMath")                 # glossy OR transmission ray
_gt.operation = "MAXIMUM"
_wl.new(_lp.outputs["Is Glossy Ray"], _gt.inputs[0])
_wl.new(_lp.outputs["Is Transmission Ray"], _gt.inputs[1])
_wl.new(_gt.outputs[0], _ma.inputs[0])
_wl.new(_ma.outputs[0], rig.light_bg.inputs["Strength"])
GROUND = os.environ.get("T_GROUND", "cream")      # what the glass sees below the horizon (the sky's own is mauve)
if GROUND != "none":
    _tc = [n for n in _wn if n.bl_idname == "ShaderNodeTexCoord"][0]
    _sep = _wn.new("ShaderNodeSeparateXYZ")
    _wl.new(_tc.outputs["Generated"], _sep.inputs[0])
    _mr = _wn.new("ShaderNodeMapRange")
    _mr.inputs["From Min"].default_value = -0.026
    _mr.inputs["From Max"].default_value = 0.0
    _mr.inputs["To Min"].default_value = 1.0
    _mr.inputs["To Max"].default_value = 0.0
    _wl.new(_sep.outputs["Z"], _mr.inputs["Value"])
    _gm = _wn.new("ShaderNodeMath")
    _gm.operation = "MULTIPLY"
    _wl.new(_mr.outputs["Result"], _gm.inputs[0])
    _wl.new(_gt.outputs[0], _gm.inputs[1])
    _mx = _wn.new("ShaderNodeMix")
    _mx.data_type = "RGBA"
    _wl.new(_gm.outputs[0], _mx.inputs["Factor"])
    _wl.new(rig.env.outputs["Color"], _mx.inputs["A"])
    _gk = envf("T_GROUND_K", 0.8) / max(1e-6, WORLD_GLOSSY)
    _gc = D.col(GROUND)
    _mx.inputs["B"].default_value = (_gc[0] * _gk, _gc[1] * _gk, _gc[2] * _gk, 1.0)
    _wl.new(_mx.outputs["Result"], rig.light_bg.inputs["Color"])
rig.world.cycles.sampling_method = "MANUAL"
rig.world.cycles.sample_map_resolution = 1024

# ----------------------------------------------------------------------------------------------
# animation: slow turn
# ----------------------------------------------------------------------------------------------
SWAY = envf("T_SWAY", 30.0)        # deg amplitude of a back-and-forth turn; 0 -> full turns
TURNS = envf("T_TURNS", 1.0)


def yaw(f):
    if SWAY:
        return math.radians(ARM_YAW0 + SWAY * math.sin(2 * math.pi * phase(f)))
    return math.radians(ARM_YAW0) + 2 * math.pi * TURNS * phase(f)


bake(pivot, "rotation_euler", lambda f: (0.0, 0.0, yaw(f)))

# ----------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------
LENS = envf("T_LENS", 70)
EL = math.radians(envf("T_EL", 20))
DIST = envf("T_DIST", 3.75)
CAM_TGT = envv("T_CAM_TGT", "0,-0.05,0.36")
cam_loc = CAM_TGT + DIST * Vector((0, -math.cos(EL), math.sin(EL)))
cam, cam_t = D.camera("Cam", tuple(cam_loc), tuple(CAM_TGT), lens=LENS, fstop=envf("T_FSTOP", 5.6))

if os.environ.get("T_MASK"):
    white = D.mat_emission("white", 1.0, name="mask_white")
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            if ob in HERO:
                ob.data.materials.clear()
                ob.data.materials.append(white)
            else:
                ob.hide_render = True
        elif ob.type == "LIGHT":
            ob.hide_render = True
    D.world_color("ink", 0.0)
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = 0.0
    sc.render.use_motion_blur = False
    cam.data.dof.use_dof = False

meta = {
    "id": SHOT,
    "group": "T1",
    "frames": N,
    "loop": LOOP,
    "loop_note": f"seamless: frame {LOOP + 1} == frame 1; play f_0001..f_{N:04d} cyclically",
    "res": list(RES),
    "fps": 30,
    "bg": BG,
    "hero": "aqua tinted-glass Stanford armadillo on a white candy turntable",
    "phenomenon": "refractive caustics: one small spot focused by the glass into an aqua caustic pool inside its shadow",
    "motion": f"slow turn: yaw 200 + {SWAY:.0f} deg x sin(2 pi phase), period {LOOP} f",
    "palette": ["butter", "aqua", "white"],
    "final_spp": FINAL_SPP,
    "final_threshold": FINAL_THR,
    "measured_final_s_per_frame": MEASURED_FINAL_SPF,
    "est_final_gpu_h": round(MEASURED_FINAL_SPF * N / 3600.0, 4) if MEASURED_FINAL_SPF else None,
    "measured_final_note": "GPU 6 (H200), --mode final, steady mean of frames 2-8 of one 8-frame process; uncontended: nvidia-smi polled every 0.5 s showed no other GPU-6 process during the run; first frame of a process is +1-3 s (scene build / BVH / texture upload)",
}
meta_dir = os.path.join(D.ROOT, "renders", "meta")
os.makedirs(meta_dir, exist_ok=True)
if not os.environ.get("T_MASK"):
    with open(os.path.join(meta_dir, SHOT + ".json"), "w") as fh:
        json.dump(meta, fh, indent=1)

MNEE = os.environ.get("T_MNEE", "0") == "1"
if MNEE:     # Cycles shadow caustics (manifold next-event estimation): spot -> armadillo glass -> turntable / cove
    spot.data.cycles.is_caustics_light = True
    arm.cycles.is_caustics_caster = True
    for _r in (tt, cove):
        _r.cycles.is_caustics_receiver = True
if os.environ.get("T_NODENOISE"):
    sc.cycles.use_denoising = False
D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
