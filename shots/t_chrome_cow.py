"""T1 tile · t_chrome_cow — "Mirror chrome" (finale honeycomb mini scene, storyboard_v2 section 5, group T1).

A mirror-chrome Spot cow turns on a pink candy turntable in a blush cove.  Its body is a perfect mirror, so the
candy sky (the film's "one sky": sky-blue dome, eight candy cards on the horizon) and the studio softboxes slide
and swirl over it as it turns, while the turntable's pearl ring makes the rotation read at a glance.

Tile contract (storyboard_v2 sections 4-5)
* 1152 x 998 final (preview 50 %), flat-top hexagon inscribed in the image: everything that matters sits inside
  the hexagon (the screen bezel also hides ~3 % at its rim).  Hero (cow + turntable) centred, ~60 % of the hex
  height, readable as a silhouette at 200 px.
* Seamless loop of LOOP frames: frame LOOP+1 == frame 1 (every animated value is a closed-form periodic function
  of the frame; keys are baked one frame past both ends so the f1 and f(LOOP+1) shutters see the same motion).
* Static seed, D.bake, PBR Neutral, exposure -0.2, no AgX / Filmic.  Meta: renders/meta/t_chrome_cow.json.

Build decisions (v2 build, tuned on preview + final test frames)
* 180-frame seamless cycle (LOOP 180 = the finale's length; frame 181 == frame 1): one turntable turn at 2 deg/f
  (a 90-frame loop needed 4 deg/f, which smeared the head and felt hurried), while the candy sky counter-turns once,
  so the reflections swirl at 4 deg/f relative to the body.  Cycles does not motion-blur world rotation; at 2 deg/f
  the sky's own motion stays below visible strobing.
* Edge definition: a mirror at grazing angles shows exactly what is behind it, so a chrome cow in a blush cove melted
  into its backdrop.  The cove is invisible to glossy rays and glossy rays see a violet ground (T_GROUND, 1.0 x
  violet) below the horizon instead of the sky's blush ground band: chrome = pale candy sky above, candy cards on the
  horizon line, violet below -> a cool, crisp silhouette on the warm blush tile (aqua / blue / lilac tried; violet
  gives the clearest chrome horizon and keeps aqua for t_glass_armadillo).
* Spot cow 0.70 m (Subsurf 2 at render for smooth reflections) on a 0.40 m pink platter: hero 58-60 % of the hex
  height, 46 % of the width, bbox centre (0.50, 0.52), nothing outside the 0.94 hex.  70 mm, 12 deg elevation, f/5.6.
* Final: 160 spp, adaptive 0.02, OIDN; measured 1.93 s/f steady on one H200, uncontended (first frame of a process
  ~4.7 s) -> 180 x 1.93 s = 0.097 GPU-h (cap 0.12).

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_chrome_cow.py -- --mode preview
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

SHOT = "t_chrome_cow"
RES = (1152, 998)
BG = "blush"


def envf(name, dflt):
    return float(os.environ.get(name, str(dflt)))


def envv(name, dflt):
    return Vector(tuple(float(x) for x in os.environ.get(name, dflt).split(",")))


LOOP = int(envf("T_LOOP", 180))           # seamless loop length (frames)
N = LOOP                                 # frames to render: 1..LOOP (LOOP+1 == 1)
FINAL_SPP = int(envf("T_SPP", 160))
FINAL_THR = envf("T_THR", 0.02)
# measured on GPU 6 (H200), --mode final, 1152x998, steady state (first frame of a process ~4.6 s)
MEASURED_FINAL_SPF = 1.93      # GPU 6 (H200), final 1152x998, steady, uncontended (re-measured)

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=16, diffuse=3, glossy=6, transmission=4,
               volume=0, caustics=False, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("T_EXPO", -0.2))
D.setup_output(res=RES)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False


def phase(f):
    """Loop phase in turns, NOT wrapped: f = LOOP+1 gives exactly 1.0 (one full period after f1)."""
    return (f - 1) / float(LOOP)


def bake(target, path, fn, index=-1):
    D.bake(target, path, 0, LOOP + 2, fn, index=index)


# ----------------------------------------------------------------------------------------------
# set: blush cove, pink candy turntable on a white candy puck, chrome Spot cow
# ----------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=12.0, height=7.0, radius=1.4, wall_y=envf("T_WALLY", 2.4),
                   mat=D.mat_clay(BG, name="clay_cove", rough=0.65, sss=0.0, sheen=0.1))
# Edge definition (product-shot trick): a mirror at grazing angles shows exactly what is behind it, so a chrome cow in
# a blush cove dissolves into its own backdrop.  The cove is invisible to glossy rays: the chrome mirrors the candy
# sky instead (blue dome, candy cards, the darker blush ground band at its silhouette), which outlines it.
cove.visible_glossy = bool(os.environ.get("T_COVE_GLOSSY"))

BASE_R, BASE_H = envf("T_BASE_R", 0.44), 0.06
PLAT_R, PLAT_H = envf("T_PLAT_R", 0.40), 0.075
TOP_Z = BASE_H + PLAT_H
base = D.cylinder("TTBase", BASE_R, BASE_H, (0, 0, 0), base_at_zero=True, bevel=0.022,
                  mat=D.mat_candy("white", name="candy_white", rough=0.25))
pivot = D.empty("TTPivot", (0, 0, BASE_H))
platter = D.cylinder("TTPlatter", PLAT_R, PLAT_H, (0, 0, 0), base_at_zero=True, bevel=0.03,
                     mat=D.mat_candy("pink", name="candy_pink", rough=0.2))
platter.parent = pivot
# pearl ring on the platter top: the rotation reads even where the chrome shows only reflections
N_PEARL = 18
PEARL_R = 0.022
PEARL_MATS = [D.mat_candy(c, name=f"candy_{c}_pearl", rough=0.15) for c in ("white", "lemon")]
for i in range(N_PEARL):
    a = 2 * math.pi * i / N_PEARL
    rr = PLAT_R - 0.045
    p = D.sphere(f"Pearl{i:02d}", PEARL_R, (rr * math.cos(a), rr * math.sin(a), PLAT_H + PEARL_R * 0.35),
                 PEARL_MATS[i % 2], segments=32, rings=16)
    p.parent = pivot

COW_H = envf("T_COW_H", 0.70)
chrome = D.mat_metal("chrome", name="metal_chrome", rough=envf("T_CHROME_R", 0.03))
cow = D.spot_cow("ChromeCow", COW_H, chrome)
sub = cow.modifiers.new("Smooth", "SUBSURF")
sub.levels = 1
sub.render_levels = 2
cow.parent = pivot
cow.location = (0, 0, PLAT_H)
COW_YAW0 = envf("T_COW_YAW0", -30.0)

HERO = [base, platter, cow] + [o for o in bpy.data.objects if o.name.startswith("Pearl")]

# ----------------------------------------------------------------------------------------------
# light: soft studio rig (warm key, cool fill, top rim) + the candy sky for reflections
# ----------------------------------------------------------------------------------------------
TGT = Vector((0, 0, 0.40))
key = D.light("AREA", "Key", tuple(envv("T_KEY_POS", "-2.0,-2.2,2.6")), tuple(TGT), power=envf("T_KEY", 260),
              color="#FFF1E0", size=1.6)
fill = D.light("AREA", "Fill", tuple(envv("T_FILL_POS", "2.6,-1.8,1.4")), tuple(TGT), power=envf("T_FILL", 90),
               color="#E6F0FF", size=2.4)
rim = D.light("AREA", "Rim", tuple(envv("T_RIM_POS", "0.6,1.5,2.6")), tuple(TGT), power=envf("T_RIM", 120),
              color="white", size=1.2)
sky_path = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
WORLD_K = envf("T_WORLD", 0.35)
WORLD_GLOSSY = envf("T_WGLOSSY", 0.9)
rig = D.world_hdri(sky_path, WORLD_K, rot_z=envf("T_SKY_ROT", 0.0), camera_bg=BG)
# reflections see the candy sky brighter than diffuse lighting does (S02 trick): the chrome mirrors a bright candy
# world while the cove keeps its soft studio light
_wn, _wl = rig.world.node_tree.nodes, rig.world.node_tree.links
_lp = _wn.new("ShaderNodeLightPath")
_ma = _wn.new("ShaderNodeMath")
_ma.operation = "MULTIPLY_ADD"
_ma.inputs[1].default_value = WORLD_GLOSSY - WORLD_K
_ma.inputs[2].default_value = WORLD_K
_wl.new(_lp.outputs["Is Glossy Ray"], _ma.inputs[0])
_wl.new(_ma.outputs[0], rig.light_bg.inputs["Strength"])
# glossy rays see a saturated ground below the horizon instead of the sky's blush ground band (which made the cow's
# lower half melt into the blush cove): chrome = cool candy sky above + GROUND colour below, warm cove behind.
GROUND = os.environ.get("T_GROUND", "violet")
if GROUND != "none":
    _env = rig.env
    _tc = [n for n in _wn if n.bl_idname == "ShaderNodeTexCoord"][0]
    _sep = _wn.new("ShaderNodeSeparateXYZ")
    _wl.new(_tc.outputs["Generated"], _sep.inputs[0])
    _mr = _wn.new("ShaderNodeMapRange")            # 1 below the horizon, 0 above (soft 1.5 deg edge)
    _mr.inputs["From Min"].default_value = -0.026
    _mr.inputs["From Max"].default_value = 0.0
    _mr.inputs["To Min"].default_value = 1.0
    _mr.inputs["To Max"].default_value = 0.0
    _wl.new(_sep.outputs["Z"], _mr.inputs["Value"])
    _gl = _wn.new("ShaderNodeMath")                # only glossy rays get the new ground
    _gl.operation = "MULTIPLY"
    _wl.new(_mr.outputs["Result"], _gl.inputs[0])
    _wl.new(_lp.outputs["Is Glossy Ray"], _gl.inputs[1])
    _mx = _wn.new("ShaderNodeMix")
    _mx.data_type = "RGBA"
    _wl.new(_gl.outputs[0], _mx.inputs["Factor"])
    _wl.new(_env.outputs["Color"], _mx.inputs["A"])
    _gk = envf("T_GROUND_K", 1.0) / max(1e-6, WORLD_GLOSSY)    # displayed ground radiance ~ T_GROUND_K x colour
    _gc = D.col(GROUND)
    _mx.inputs["B"].default_value = (_gc[0] * _gk, _gc[1] * _gk, _gc[2] * _gk, 1.0)
    _wl.new(_mx.outputs["Result"], rig.light_bg.inputs["Color"])
rig.world.cycles.sampling_method = "MANUAL"
rig.world.cycles.sample_map_resolution = 1024

# ----------------------------------------------------------------------------------------------
# animation: one full turn of the turntable per loop (constant speed); the sky counter-turns SKY_TURNS per loop
# ----------------------------------------------------------------------------------------------
TURNS = 1.0
SKY_TURNS = envf("T_SKY_TURNS", 1.0)
bake(pivot, "rotation_euler", lambda f: (0.0, 0.0, math.radians(COW_YAW0) + 2 * math.pi * TURNS * phase(f)))
if SKY_TURNS:
    bake(rig.mapping.inputs["Rotation"], "default_value",
         lambda f: -2 * math.pi * SKY_TURNS * phase(f) + math.radians(envf("T_SKY_ROT", 0.0)), index=2)

# ----------------------------------------------------------------------------------------------
# camera: 70 mm product view, slightly high, locked
# ----------------------------------------------------------------------------------------------
LENS = envf("T_LENS", 70)
EL = math.radians(envf("T_EL", 12))
DIST = envf("T_DIST", 3.7)
CAM_TGT = envv("T_CAM_TGT", "0,0,0.40")
cam_loc = CAM_TGT + DIST * Vector((0, -math.cos(EL), math.sin(EL)))
cam, cam_t = D.camera("Cam", tuple(cam_loc), tuple(CAM_TGT), lens=LENS, fstop=envf("T_FSTOP", 5.6))

# ----------------------------------------------------------------------------------------------
# QA silhouette mode
# ----------------------------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------------------------
# metadata (build time, every mode)
# ----------------------------------------------------------------------------------------------
meta = {
    "id": SHOT,
    "group": "T1",
    "frames": N,
    "loop": LOOP,
    "loop_note": f"seamless: frame {LOOP + 1} == frame 1; play f_0001..f_{N:04d} cyclically",
    "res": list(RES),
    "fps": 30,
    "bg": BG,
    "hero": "mirror-chrome Spot cow on a pink candy turntable (white puck, white/lemon pearl ring)",
    "phenomenon": "perfect-mirror reflections: the candy sky and softboxes swirl over the chrome as it turns",
    "palette": ["blush", "pink", "white", "lemon", "chrome"],
    "motion": f"turntable {TURNS * 360:.0f} deg per loop ({TURNS * 360 / LOOP:.2f} deg/f), constant speed",
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

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
