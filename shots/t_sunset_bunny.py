"""t_sunset_bunny -- hex-tile mini scene (group T3 "motion & world", docs/storyboard_v2.md section 5).

Hero / effect
-------------
A polished gold Stanford bunny (the film's test subject, now in gold) sits on a two-tier candy pedestal on a coral
sunset cove.  The only light is a real sunset environment map (Poly Haven "the_sky_is_on_fire": pink / orange /
lavender sky) plus a sun lamp locked to the map's sunset azimuth, and the map ROTATES: it swings through a
90-degree arc and back, theta(f) = 45 (1 - cos(2 pi (f - 1) / 180)), as one seamless 180-frame loop.  The camera,
the bunny and the set never move, so everything that changes is the light: the bunny's shadow sweeps a quarter
turn across the pedestal top and the cove floor, the warm glints slide over the gold, and the sky colours in the
reflections turn with the map.  Phenomenon: environment lighting under arbitrary rotation (image-based lighting,
glossy metal reflections, moving shadows).

Contract (storyboard_v2 section 5): 1152 x 998 final (preview 576 x 499), flat-top hexagon inscribed in the frame;
180 frames that are also a seamless loop (theta(181) == theta(1), zero speed there), baked with D.bake; static
seed; PBR Neutral, exposure -0.2.  Meta: renders/meta/t_sunset_bunny.json (per-frame theta, sun azimuth).

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_sunset_bunny.py -- --mode preview
Test hooks (env, all default off): TS_CAM, TS_TGT, TS_LENS, TS_SUN, TS_SUN_EL, TS_WORLD, TS_EXPO, TS_AZ0.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

V = Vector
SHOT = "t_sunset_bunny"
N = 180
LOOP = 180                       # the 180 frames are themselves a seamless loop (f181 == f1)
RES = (1152, 998)
BG = "#FFC4B2"                   # coral-sunset pastel (cove)
FINAL_SPP, FINAL_THR = 128, 0.02
MEASURED_FINAL_SPF = 1.6       # steady-state final s/frame, H200 GPU 6 idle (nvidia-smi 0 % before the run)
COST = {"first_frame_s": 4.2, "gpu_h_est": 0.082,
        "measured": "2026-11-20, --mode final f1,46,91,136 in one process: 4.2 / 2.0 / 1.3 / 1.3 s, process wall 11 s; "
                    "re-measured with the glossy tint f1,46,91,136,171: 3.7 / 1.4 / 1.6 / 1.4 / (2.7: another job started "
                    "on GPU 6 mid-run, 98 % after) s; gpu_h = (first + 179 x s/f + 3 s scene build) / 3600"}
ENV = os.environ.get
args = D.parse_args()


def envf(name, default):
    return float(ENV(name, default))


def envv(name, default):
    return V(tuple(float(v) for v in ENV(name, default).split(",")))


EXPOSURE = envf("TS_EXPO", -0.2)
D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=32, diffuse=4, glossy=6, transmission=4,
               volume=0, caustics=False, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=EXPOSURE)
D.setup_output(res=RES)
sc.frame_start, sc.frame_end = 1, N
BAKE0, BAKE1 = -2, N + 3

# ----------------------------------------------------------------------------------------------
# the rotation: theta(f) in degrees, 0 -> 90 -> 0 over the loop, zero speed at f1 and f91
# ----------------------------------------------------------------------------------------------
SWING = 90.0


def theta(f):
    return 0.5 * SWING * (1.0 - math.cos(2.0 * math.pi * (f - 1) / LOOP))


HDRI = os.path.join(D.ASSETS, "hdri", "the_sky_is_on_fire_4k.hdr")
HDRI_SUN_AZ = -58.5              # measured: the sunset glow of this map sits at azimuth -58.5 deg, elevation 4.5 deg
AZ0 = envf("TS_AZ0", 195.0)      # world azimuth of the sunset at theta = 0 (left, a little behind the bunny)
SWING_SIGN = 1.0                 # the sunset moves left -> front (195 -> 285 deg): shadows sweep right -> back.
                                 # (behind the set it would be blocked by the cove wall and the scene went dusky)
SUN_EL = envf("TS_SUN_EL", 22.0)  # the lamp rides higher than the map's 4.5-deg glow so shadows land on the set


def sun_az(f):
    return AZ0 + SWING_SIGN * theta(f)


def map_rot_z(f):
    """Mapping-node rotation (rad).  A pixel at map azimuth a0 shows up at world azimuth a0 - r, so to put the
    map's sunset at sun_az(f) the mapping rotation is r = HDRI_SUN_AZ - sun_az(f)."""
    return math.radians(HDRI_SUN_AZ - sun_az(f))


# ----------------------------------------------------------------------------------------------
# set
# ----------------------------------------------------------------------------------------------
def cove_mat():
    m = D.mat_clay(BG, name="cove_coral", rough=0.6, sss=0.0, sheen=0.0)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.3
    return m


cove = D.cyclorama("Cove", width=16, depth=12, height=7, radius=1.6, wall_y=3.2, mat=cove_mat())

PED_LO = ("violet", envf("TS_PED_R", 0.52), 0.14)          # colour, radius, height
PED_HI = ("lilac", envf("TS_PED_R", 0.52) - 0.12, 0.11)
D.cylinder("PedLo", PED_LO[1], PED_LO[2], (0, 0, 0), mat=D.mat_candy(PED_LO[0], rough=0.25), bevel=0.04,
           base_at_zero=True)
D.cylinder("PedHi", PED_HI[1], PED_HI[2], (0, 0, PED_LO[2] - 0.002), mat=D.mat_candy(PED_HI[0], rough=0.25),
           bevel=0.035, base_at_zero=True)
TOP_Z = PED_LO[2] + PED_HI[2] - 0.002
BUNNY_H = envf("TS_BUNNY_H", 0.62)
bunny = D.stanford_bunny("GoldBunny", BUNNY_H, mat=D.mat_metal(ENV("TS_GOLD", "#FFD25A"), name="gold_bunny",
                                                                 rough=envf("TS_ROUGH", 0.20)),
                         location=(0.0, 0.02, TOP_Z), rotation=(0, 0, envf("TS_YAW", -28.0)))
# cast-gold finish: the raw scan's crinkle shows as wrinkled highlights on a mirror metal, so it is smoothed with a
# volume-preserving Laplacian smooth (the silhouette is unchanged at tile size)
_sm = bunny.modifiers.new("Smooth", "LAPLACIANSMOOTH")
_sm.iterations = int(envf("TS_SMOOTH_IT", 30))
_sm.lambda_factor = envf("TS_SMOOTH_L", 0.8)
_sm.use_volume_preserve = True
_sm.use_normalized = True

# ----------------------------------------------------------------------------------------------
# light: the rotating sunset map + a sun lamp locked to its sunset azimuth (no other lamps)
# ----------------------------------------------------------------------------------------------
rig = D.world_hdri(HDRI, envf("TS_WORLD", 0.55), camera_bg=BG)
D.bake(rig.mapping.inputs["Rotation"], "default_value", BAKE0, BAKE1, map_rot_z, index=2)
# reflections only: the map's cool blue-grey sky times the yellow gold read as olive / khaki patches on the bunny
# (G2: muddy).  Glossy rays see the map through a rose tint (cool sky -> mauve, sunset -> deeper coral), so the
# gold's darks go warm amber; camera rays and diffuse light (shadows, set colours) see the untinted map.
GTINT = ENV("TS_GTINT", "#FFCFD8")
if GTINT != "off":
    _nt = rig.world.node_tree
    _vm = _nt.nodes.new("ShaderNodeVectorMath")
    _vm.operation = "MULTIPLY"
    _nt.links.new(rig.env.outputs["Color"], _vm.inputs[0])
    _vm.inputs[1].default_value = D.col(GTINT)[:3]
    _bg_g = _nt.nodes.new("ShaderNodeBackground")
    _nt.links.new(_vm.outputs[0], _bg_g.inputs["Color"])
    _bg_g.inputs["Strength"].default_value = rig.light_bg.inputs["Strength"].default_value
    _lp = _nt.nodes.new("ShaderNodeLightPath")
    _mx = _nt.nodes.new("ShaderNodeMixShader")
    _nt.links.new(_lp.outputs["Is Glossy Ray"], _mx.inputs["Fac"])
    _nt.links.new(rig.light_bg.outputs[0], _mx.inputs[1])
    _nt.links.new(_bg_g.outputs[0], _mx.inputs[2])
    _nt.links.new(_mx.outputs[0], rig.mix.inputs[1])        # replaces bg -> camera mix input 1
sun = D.light("SUN", "Sun", (0, 0, 5), None, power=envf("TS_SUN", 3.2), color=ENV("TS_SUN_COL", "#FFD9B5"), size=1.6)


def sun_rot(f):
    az, el = math.radians(sun_az(f)), math.radians(SUN_EL)
    d = V((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))   # toward the sun
    return (-d).to_track_quat("-Z", "Y").to_euler()


sun.rotation_mode = "XYZ"
D.bake(sun, "rotation_euler", BAKE0, BAKE1, lambda f: tuple(sun_rot(f)))

# camera: locked (the proof: only the light changes)
CAM = envv("TS_CAM", "0.0,-3.30,1.38")
TGT = envv("TS_TGT", "0.0,0.0,0.47")
cam, cam_t = D.camera("Cam", tuple(CAM), tuple(TGT), lens=envf("TS_LENS", 60.0), fstop=6.3)
focus = D.empty("Focus", (0.0, 0.0, 0.45))
cam.data.dof.focus_object = focus

# ----------------------------------------------------------------------------------------------
# meta
# ----------------------------------------------------------------------------------------------
META_PATH = os.path.join(D.ROOT, "renders", "meta", SHOT + ".json")
meta = {
    "id": SHOT, "group": "T3", "frames": N, "loop": LOOP, "seamless": True, "fps": 30, "res": list(RES),
    "bg": "coral sunset", "bg_hex": BG,
    "hero": "polished gold Stanford bunny on a violet / lilac candy pedestal",
    "phenomenon": "image-based lighting under rotation: a sunset HDRI (+ a sun lamp locked to its sunset) swings "
                  "through 90 deg and back; shadows sweep a quarter turn, glints slide over the gold",
    "palette": ["coral", "gold", "violet", "lilac"],
    "hdri": os.path.relpath(HDRI, D.ROOT), "hdri_sun_azimuth_deg": HDRI_SUN_AZ,
    "rotation": {"swing_deg": SWING, "law": "theta = 45 (1 - cos(2 pi (f - 1) / 180))", "sun_elevation_deg": SUN_EL,
                 "sun_azimuth_at_theta0_deg": AZ0, "direction": "left -> front (sun azimuth increasing)"},
    "per_frame": {"theta_deg": [round(theta(f), 4) for f in range(1, N + 1)],
                  "sun_azimuth_deg": [round(sun_az(f), 4) for f in range(1, N + 1)]},
    "final": dict({"samples": FINAL_SPP, "threshold": FINAL_THR, "s_per_frame_measured": MEASURED_FINAL_SPF},
                  **COST),
    "hex": {"shape": "flat-top", "inscribed": True, "circumradius_px": RES[0] / 2},
}
os.makedirs(os.path.dirname(META_PATH), exist_ok=True)
with open(META_PATH, "w") as fh:
    json.dump(meta, fh, indent=1)

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
