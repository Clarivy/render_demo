"""t_material_balls -- honeycomb mini-scene (T2 "light & material"): five material spheres on a candy turntable.

What the tile proves (storyboard_v2 section 5)
----------------------------------------------
Five spheres of the same size under the same light read as five different materials at a glance: violet velvet
(sheen rim), polished gold (sharp coloured reflections of the candy sky), candy marble (procedural pastel veins under
a clear coat, a little subsurface), aqua glass (refraction + a tinted caustic on the platter) and an iridescent
thin-film chrome (interference colours that shift with the view angle).  They ride a white candy platter that turns
360 degrees per loop, so every sphere passes the key, the rim light and the camera, and the highlights slide.

Tile contract (storyboard_v2 sections 4-5)
-----------------------------------------
1152 x 998 final (preview 576 x 499), flat-top hexagon inscribed in the frame (vertices at the left/right edge
midpoints); everything important stays inside a 0.90-scaled safe hexagon.  Seamless LOOP-frame loop: frame LOOP+1 ==
frame 1 (all motion is a closed-form periodic function of the frame, baked per frame with D.bake over f-2..LOOP+3 so
the shutter intervals at the seam are defined).  Static seed, PBR Neutral, exposure -0.2.  Meta: renders/meta/<id>.json.

Run:  CUDA_VISIBLE_DEVICES=7 tools/blender/blender -b --factory-startup -P shots/t_material_balls.py -- --mode preview
      (--frames 1-90:10, --frames 91 for the seam check; --mode final for the finals queue)
Look-dev hooks (env, default off; finals must run without them): TMB_KEY, TMB_RIM, TMB_FILL, TMB_WORLD, TMB_EXPO,
TMB_DIST, TMB_ELEV, TMB_FSPP.

Design notes / deviations (all visual, tunable)
----------------------------------------------
* Background "lemon": a pastel lemon cove (#FFE58C albedo) -- deeper than T1's butter so the two tiles stay distinct.
* Marble is procedural (white with pink + lilac veins): assets/textures/marble_01 is a beige limestone tile, which
  would read tan (G2).
* Glass uses the S02/S03 candy_glass correction (G5: surface tint colour^0.5 so the double interface lands on the
  palette colour).
* Twelve candy studs on the platter rim make the turn read even when no sphere is in front.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

V = Vector
SHOT = "t_material_balls"
LOOP = 180                       # seamless loop length (frames); frame LOOP+1 == frame 1
RES = (1152, 998)
ENV = os.environ.get


def envf(name, default):
    return float(ENV(name, str(default)))


args = D.parse_args()
D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=256, threshold=0.02, min_samples=32, diffuse=4, glossy=6, transmission=10, volume=2,
               caustics=True, filter_glossy=0.3, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("TMB_EXPO", -0.2))
D.setup_output(res=RES)
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.frame_start, sc.frame_end = 1, LOOP
BAKE0, BAKE1 = -2, LOOP + 3

BG_NAME, BG_HEX = "lemon pastel", "#FFEC6E"

# ----------------------------------------------------------------------------------------------------------------
# set: lemon cove, candy turntable
# ----------------------------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=10.0, height=6.0, radius=1.2, wall_y=1.7,
                   mat=D.mat_clay(BG_HEX, name="cove_lemon", rough=0.7, sss=0.0, sheen=0.1))

R_SPH = 0.152                     # sphere radius (m)
R_RING = 0.335                    # sphere centres on this ring
R_PLAT, H_PLAT = 0.54, 0.07       # turning platter (pink candy rim)
R_INLAY, H_INLAY = 0.475, 0.016   # white inlay on top of it (the spheres rest on it)
R_BASE, H_BASE = 0.45, 0.06       # fixed plinth under it
Z_PLAT = H_BASE                   # platter bottom
Z_REST = H_PLAT + H_INLAY - 0.004  # sphere contact height above the platter bottom

base = D.cylinder("Plinth", R_BASE, H_BASE, (0, 0, 0), mat=D.mat_candy("white", name="candy_white_plinth",
                                                                     rough=0.3), bevel=0.02, base_at_zero=True)
turn = D.empty("Turn", (0, 0, Z_PLAT), size=0.3)
plat = D.cylinder("Platter", R_PLAT, H_PLAT, (0, 0, 0), mat=D.mat_candy("blue", name="candy_blue_platter"),
                  bevel=0.028, base_at_zero=True)
plat.parent = turn
inlay = D.cylinder("Inlay", R_INLAY, H_INLAY, (0, 0, H_PLAT - 0.004),
                   mat=D.mat_candy("white", name="candy_white_inlay", rough=0.28), bevel=0.007, base_at_zero=True)
inlay.parent = turn
_stud = D.mat_candy("white", name="candy_white_stud", rough=0.2)
STUDS = []
for i in range(12):
    a = 2 * math.pi * (i + 0.5) / 12
    rs = 0.5 * (R_INLAY + R_PLAT)
    st = D.sphere(f"Stud{i:02d}", 0.017, (math.cos(a) * rs, math.sin(a) * rs, H_PLAT - 0.003), _stud,
                  segments=32, rings=16)
    st.parent = turn
    STUDS.append(st)


def candy_glass(color, absorb=2.0, name=None, tint_exp=0.5, rough=0.0, ior=1.5):
    """G5 (after shots/s02_caustics.py): D.mat_glass with the surface tint at colour^tint_exp, so the two interfaces of
    a closed solid land on the palette colour instead of its square; Beer-Lambert absorption deepens thick parts."""
    m = D.mat_glass(color, name=name, rough=rough, ior=ior, absorb=absorb)
    c = D.col(color)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        c[0] ** tint_exp, c[1] ** tint_exp, c[2] ** tint_exp, 1.0)
    return m


def mat_marble(name="candy_marble", base="#FBF6F3", vein1="#EE6FAE", vein2="#A88CF0", scale=1.0):
    """Procedural candy marble: the troughs of two strongly distorted diagonal wave fields give long, thin, branching
    veins (pink, lilac) on a warm-white stone, polished with a clear coat and a touch of subsurface."""
    m = D.principled(name, base=base, rough=0.22, coat=1.0, coat_rough=0.04, sss=0.12,
                     sss_radius=(1.0, 0.85, 0.8), sss_scale=0.02)
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    p = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")

    def veins(sc_, rot, distortion, width):
        mp = n.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = rot
        l.new(tc.outputs["Object"], mp.inputs["Vector"])
        wv = n.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "DIAGONAL"
        wv.wave_profile = "SIN"
        wv.inputs["Scale"].default_value = sc_
        wv.inputs["Distortion"].default_value = distortion
        wv.inputs["Detail"].default_value = 5.0
        wv.inputs["Detail Scale"].default_value = 1.4
        wv.inputs["Detail Roughness"].default_value = 0.62
        l.new(mp.outputs[0], wv.inputs["Vector"])
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = width
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        l.new(wv.outputs["Fac"], mr.inputs["Value"])
        return mr.outputs["Result"]
    # soft halo + crisp core per vein family, so the veins vary in width like stone (not hairline cracks)
    v1 = veins(1.3 * scale, (0.4, 0.9, 0.2), 7.0, 0.085)
    v1h = veins(1.3 * scale, (0.4, 0.9, 0.2), 7.0, 0.26)
    v2 = veins(2.6 * scale, (1.2, -0.5, 0.7), 10.0, 0.035)
    halo = n.new("ShaderNodeMath"); halo.operation = "MULTIPLY"; halo.inputs[1].default_value = 0.45
    l.new(v1h, halo.inputs[0])
    vmax = n.new("ShaderNodeMath"); vmax.operation = "MAXIMUM"
    l.new(v1, vmax.inputs[0])
    l.new(halo.outputs[0], vmax.inputs[1])
    v1 = vmax.outputs[0]
    mx1 = n.new("ShaderNodeMix"); mx1.data_type = "RGBA"
    mx1.inputs["A"].default_value = D.col(base)
    mx1.inputs["B"].default_value = D.col(vein1)
    l.new(v1, mx1.inputs["Factor"])
    mx2 = n.new("ShaderNodeMix"); mx2.data_type = "RGBA"
    l.new(mx1.outputs["Result"], mx2.inputs["A"])
    mx2.inputs["B"].default_value = D.col(vein2)
    l.new(v2, mx2.inputs["Factor"])
    l.new(mx2.outputs["Result"], p.inputs["Base Color"])
    return m


def mat_irid(name="iridescent"):
    """Oil-slick pearl: a deep blue-violet dielectric under a high-index thin film (IOR 2.4, specular level 1.0).  The
    film thickness runs 200 -> 800 nm with height on the ball (plus a little noise), like the bands of a soap bubble,
    so the reflections carry pink / green / blue interference bands.  (A thin film over bright chrome -- D.mat_iridescent
    -- measured nearly colourless here: the metal's reflectance swamps the interference contrast.)"""
    m, n, l, p = D._new_mat(name)
    D._set(p, base=D.col(ENV("TMB_IRIDBASE", "#4A3A99")), metallic=0.0, rough=0.05, spec=1.0,
           film_ior=envf("TMB_FILMIOR", 2.4))
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 2.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    k = n.new("ShaderNodeMath"); k.operation = "MULTIPLY_ADD"
    k.inputs[1].default_value = 1.0 / (2.0 * R_SPH)              # z in [-r, r] -> [-0.5, 0.5]
    k.inputs[2].default_value = 0.5
    l.new(sep.outputs["Z"], k.inputs[0])
    wob = n.new("ShaderNodeMath"); wob.operation = "MULTIPLY_ADD"
    wob.inputs[1].default_value = 0.35
    l.new(nz.outputs["Fac"], wob.inputs[0])
    l.new(k.outputs[0], wob.inputs[2])
    mr = n.new("ShaderNodeMapRange")
    mr.clamp = False
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.35
    mr.inputs["To Min"].default_value = envf("TMB_FILM0", 200.0)
    mr.inputs["To Max"].default_value = envf("TMB_FILM1", 800.0)
    l.new(wob.outputs[0], mr.inputs["Value"])
    l.new(mr.outputs["Result"], p.inputs["Thin Film Thickness"])
    return m


SPHERES = [  # (name, material, label) in ring order
    ("Gold", D.mat_metal("gold", name="gold_ball", rough=0.10), "gold"),
    ("Velvet", D.mat_velvet("pink", name="velvet_pink"), "velvet"),
    ("Glass", candy_glass("aqua", absorb=envf("TMB_GLASS_ABS", 0.6), name="glass_aqua",
                          tint_exp=envf("TMB_GLASS_TEXP", 0.8)), "glass"),
    ("Irid", mat_irid(),
     "iridescent"),
    ("Marble", mat_marble(), "marble"),
]
balls = []
for i, (nm, mat, _lab) in enumerate(SPHERES):
    a = math.radians(-90.0 + 72.0 * i)          # gold starts at the front (camera side, -Y)
    b = D.sphere(nm, R_SPH, (math.cos(a) * R_RING, math.sin(a) * R_RING, Z_REST + R_SPH), mat, segments=128, rings=64)
    b.parent = turn
    balls.append(b)

# ----------------------------------------------------------------------------------------------------------------
# light: soft studio key + rim + fill, candy-sky reflections
# ----------------------------------------------------------------------------------------------------------------
TGT = V((0.0, 0.0, 0.20))
D.light("AREA", "Key", (-1.9, -1.9, 2.4), tuple(TGT), envf("TMB_KEY", 200.0), "#FFFBF5", size=1.1)
D.light("AREA", "Fill", (2.4, -1.6, 1.3), tuple(TGT), envf("TMB_FILL", 90.0), "#E8E4FF", size=2.4)
D.light("AREA", "Rim", (0.9, 2.2, 2.0), tuple(TGT), envf("TMB_RIM", 220.0), "#FFFFFF", size=1.4)
D.world_hdri(os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr"), envf("TMB_WORLD", 0.55), rot_z=30.0,
             camera_bg=BG_HEX)

# ----------------------------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------------------------
ELEV = math.radians(envf("TMB_ELEV", 30.0))
DIST = envf("TMB_DIST", 2.2)
CAM = TGT + V((0.0, -math.cos(ELEV), math.sin(ELEV))) * DIST
AIM = TGT + V((0.0, 0.0, envf("TMB_AIMDZ", -0.055)))     # aim a little low: centres the group in the hex
cam, cam_tgt = D.camera("Cam", tuple(CAM), tuple(AIM), lens=50.0, fstop=5.6)
cam.data.dof.focus_object = None
cam.data.dof.focus_distance = (CAM - TGT).length          # focus on the ring centre (f/5.6 keeps all five sharp)


# ----------------------------------------------------------------------------------------------------------------
# motion: one full platter turn per loop (linear, so the speed is constant and the seam is invisible)
# ----------------------------------------------------------------------------------------------------------------
def turn_angle(f):
    return 2 * math.pi * (f - 1) / LOOP


def turn_quat(f):
    """Platter rotation as a quaternion whose keys at f and f+LOOP are exact negations (the same rotation): the
    motion-blur interpolation around the seam then produces bit-identical matrices, so frame LOOP+1 renders exactly
    like frame 1.  (An Euler angle of 2*pi vs 0 differs in the last bits and re-rolls the noise.)"""
    k, r = divmod(f - 1, LOOP)
    h = math.pi * r / LOOP                       # half angle of the wrapped rotation
    sgn = -1.0 if k % 2 else 1.0
    return (sgn * math.cos(h), 0.0, 0.0, sgn * math.sin(h))


turn.rotation_mode = "QUATERNION"
D.bake(turn, "rotation_quaternion", BAKE0, BAKE1, turn_quat)


# ----------------------------------------------------------------------------------------------------------------
# hex framing metrics + meta
# ----------------------------------------------------------------------------------------------------------------
def hex_scale_of(px, py):
    """Smallest flat-top-hexagon scale (1 = inscribed in the frame) that contains pixel (px, py)."""
    cx, cy, R = RES[0] / 2, RES[1] / 2, RES[0] / 2
    dx, dy = abs(px - cx), abs(py - cy)
    return max(dy / (R * math.sqrt(3) / 2), (dx + dy / math.sqrt(3)) / R)


def frame_metrics(objs, f, stride=4):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys, hs = [], [], []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world.copy()
        for k in range(0, len(me.vertices), stride):
            c = world_to_camera_view(sc, cam, mw @ me.vertices[k].co)
            px, py = c.x * RES[0], (1.0 - c.y) * RES[1]
            xs.append(px)
            ys.append(py)
            hs.append(hex_scale_of(px, py))
        ev.to_mesh_clear()
    return {"bbox_px": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
            "height_frac": round((max(ys) - min(ys)) / RES[1], 3),
            "centre_px": [round((min(xs) + max(xs)) / 2), round((min(ys) + max(ys)) / 2)],
            "max_hex_scale": round(max(hs), 3)}


HERO = [plat, base, inlay] + balls
METRICS = {f: frame_metrics(HERO, f) for f in (1, 1 + LOOP // 4, 1 + LOOP // 2, 1 + 3 * LOOP // 4)}
sc.frame_set(1)
FINAL_SPP, FINAL_THR = int(envf("TMB_FSPP", 96)), 0.02
MEASURED_S_PER_F = 1.9      # final mode 96 spp, steady state (frames 2..n of one process)
FINAL_COST = {                  # T2 finishing pass, 2026-11-20, one process, GPU 7 (NVIDIA H200) not shared
    "gpu": "H200 (GPU 7), exclusive during the run (nvidia-smi compute-apps: only this process)",
    "measured_frames": [1, 46, 91, 136], "frame_times_s": [3.0, 1.9, 1.9, 1.9], "process_wall_s": 11.27,
    "overhead_per_process_s": 3.67, "chunk_frames": 90, "processes": 2,
    "est_gpu_h": 0.097, "cap_gpu_h": 0.12}
meta = {
    "id": SHOT, "frames": LOOP, "loop": LOOP, "res": list(RES), "fps": 30,
    "bg": {"name": BG_NAME, "albedo_hex": BG_HEX},
    "hero": "five spheres (gold, velvet, glass, iridescent, marble) on a white candy turntable",
    "phenomenon": "material response: velvet sheen, metal, subsurface marble, refraction + caustic, thin film",
    "palette": ["lemon pastel", "white", "pink", "violet", "aqua", "gold"],
    "motion": "platter 360 deg per loop, constant speed (2 deg/f)",
    "final_samples": FINAL_SPP, "final_threshold": FINAL_THR,
    "measured_final_s_per_f": MEASURED_S_PER_F,
    "final_cost": FINAL_COST,
    "hero_metrics": {str(k): v for k, v in METRICS.items()},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"[{SHOT}] metrics", json.dumps(METRICS))

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=LOOP, shot_name=SHOT)
