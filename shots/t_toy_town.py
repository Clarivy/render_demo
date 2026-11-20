"""t_toy_town -- hex-tile mini scene (group T3 "motion & world", docs/storyboard_v2.md section 5).

Hero / effect
-------------
A candy toy town on a round lavender cake-plate: five rounded clay houses with glossy candy gable roofs (the big
lemon house with the pink roof in the middle is the hero) and cone trees, on a sky-blue cove.  The only thing that
moves is the SUN: over the 180 frames it sweeps one whole day, morning -> noon -> evening (azimuth from the left
through the front to the right, elevation 13 deg -> 46 deg -> 13 deg, lingering at the ends, its colour peach -> warm white -> coral), so the
long morning shadows that point right swing round behind the houses, shrink at noon and stretch out again to the
left in the evening.  The shadows are filled by the lavender-blue sky, so they read colourful (cool lilac against the
warm sunlit faces), and at dusk the windows light up.  Phenomenon: a moving directional light with soft shadows
(sun position over a day, shadow length and direction, warm key / cool sky fill).

Contract (storyboard_v2 section 5): 1152 x 998 final (preview 576 x 499), flat-top hexagon inscribed in the frame;
180 straight frames (one day, not a loop: meta "loop": null -> the tile plays f1..f180 once in the finale); every
light value is a closed-form function of t = (f - 1) / 179, baked per frame with D.bake; static seed; PBR Neutral,
exposure -0.2.  Meta: renders/meta/t_toy_town.json (per-frame sun azimuth / elevation).

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_toy_town.py -- --mode preview
Test hooks (env, all default off): TT_CAM, TT_TGT, TT_LENS, TT_SUN, TT_WORLD, TT_FILL, TT_EXPO, TT_AZ0, TT_AZ1,
TT_EL0, TT_EL1, TT_SUN_ANGLE.  Finals must run with none of them set.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

V = Vector
SHOT = "t_toy_town"
N = 180
LOOP = None                      # one day, straight: not a loop
RES = (1152, 998)
BG = "sky"
FINAL_SPP, FINAL_THR = 128, 0.02
MEASURED_FINAL_SPF = 1.2       # steady-state final s/frame, H200 GPU 6 idle (nvidia-smi 0 % before the run)
COST = {"first_frame_s": 1.8, "gpu_h_est": 0.061,
        "measured": "2026-11-20, --mode final f1,45,90,135,180 in one process: 1.8 / 1.0 / 0.9 / 1.0 / 1.8 s, process wall 8 s; gpu_h = (first + 179 x s/f + 3 s scene build) / 3600"}
ENV = os.environ.get
args = D.parse_args()


def envf(name, default):
    return float(ENV(name, default))


def envv(name, default):
    return V(tuple(float(v) for v in ENV(name, default).split(",")))


EXPOSURE = envf("TT_EXPO", -0.2)
D.reset_scene()
sc = bpy.context.scene
# nothing moves but the light -> no motion blur; no caustics (opaque toys)
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=32, diffuse=4, glossy=4, transmission=4,
               volume=0, caustics=False, clamp_indirect=10.0, motion_blur=False)
D.setup_color(exposure=EXPOSURE)
D.setup_output(res=RES)
sc.frame_start, sc.frame_end = 1, N
BAKE0, BAKE1 = 1, N


# ----------------------------------------------------------------------------------------------
# the day: t = 0 morning .. 1 evening
# ----------------------------------------------------------------------------------------------
AZ0, AZ1 = envf("TT_AZ0", 192.0), envf("TT_AZ1", 348.0)   # left (a little in front) -> front -> right
EL0, EL1 = envf("TT_EL0", 13.0), envf("TT_EL1", 46.0)     # low morning / evening sun, high noon


WARP = 0.45                      # solar-time warp: slow at the long-shadow ends, quick through noon


def day_t(f):
    """Solar time 0..1 for frame f: s = t - WARP sin(2 pi t) / (2 pi), t = (f - 1) / 179.  Its speed 1 - WARP cos(2 pi t)
    is 0.55x at morning / evening (the long shadows linger and swing slowly) and 1.45x at noon, where the short
    shadows fall behind the houses (hidden from the elevated camera)."""
    t = (f - 1) / (N - 1)
    return t - WARP * math.sin(2.0 * math.pi * t) / (2.0 * math.pi)


def sun_az(f):
    return AZ0 + (AZ1 - AZ0) * day_t(f)


def sun_el(f):
    return EL0 + (EL1 - EL0) * math.sin(math.pi * day_t(f))


SUN_COLS = [(0.0, "#FFCFAE"), (0.5, "#FFF5E6"), (1.0, "#FFA987")]     # peach morning, warm-white noon, coral dusk


def sun_col(f):
    t = day_t(f)
    for (t0, c0), (t1, c1) in zip(SUN_COLS[:-1], SUN_COLS[1:]):
        if t <= t1:
            u = D.smoothstep((t - t0) / (t1 - t0))
            a, b = D.col(c0), D.col(c1)
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
    return tuple(D.col(SUN_COLS[-1][1])[:3])


SUN_W = envf("TT_SUN", 3.7)


def sun_power(f):
    """The ground irradiance of a sun at elevation el is power * sin(el): at 13 deg it would be a quarter of noon's
    and the long morning / evening shadows (the point of the tile) would drown in the sky fill.  power ~ 1 /
    sin(el)^0.6 keeps the ground contrast up at the ends (2.4x noon power at 13 deg) without blowing out the walls
    that face the low sun."""
    return SUN_W / math.sin(math.radians(sun_el(f))) ** 0.6


def sun_rot(f):
    az, el = math.radians(sun_az(f)), math.radians(sun_el(f))
    d = V((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))     # toward the sun
    return (-d).to_track_quat("-Z", "Y").to_euler()


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------
def gable_roof(name, w, d, h, mat):
    """Triangular prism, ridge along local x, base at z = 0, softened with a bevel (toy-block roof)."""
    bm = bmesh.new()
    prof = [(-d / 2, 0.0), (d / 2, 0.0), (0.0, h)]
    a = [bm.verts.new((-w / 2, y, z)) for y, z in prof]
    b = [bm.verts.new((w / 2, y, z)) for y, z in prof]
    bm.faces.new((a[0], a[2], a[1]))
    bm.faces.new((b[0], b[1], b[2]))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = D.link(bpy.data.objects.new(name, me))
    D.assign(ob, mat)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = min(0.022, h * 0.2)
    bev.segments = 5
    bev.limit_method = "NONE"
    bev.harden_normals = True
    D.set_smooth(ob)
    return ob


def roof_mat(colr, name):
    """Satin candy roof: a flat 45-degree slope mirrors the noon sun straight into the camera, so the coat is thin
    and soft and the specular low (a glossy coat flared the hero's pink roof white at noon)."""
    m = D.mat_candy(colr, name=name, rough=0.42, coat=0.35, coat_rough=0.28)
    m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.35
    return m


WIN_MATS = []


def window_mat(name):
    m = D.principled(name, base=D.col("#FFF6EC"), rough=0.25, coat=0.6, coat_rough=0.05)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Emission Color"].default_value = D.col("#FFD27A")
    p.inputs["Emission Strength"].default_value = 0.0
    WIN_MATS.append(m)
    return m


def house(name, xy, yaw, size, body, roof, door, pitch=0.52, chimney=False, windows=2):
    # pitch 0.52 (a ~40 deg gable on the hero): the front slope's mirror direction from the camera is a sun at ~69 deg
    # elevation, far from the 46 deg noon sun (45 / 54 deg slopes sat in it and flared the pink roof white at noon)
    w, d, h = size
    root = D.empty(name, (xy[0], xy[1], PLATE_TOP))
    root.rotation_euler = (0.0, 0.0, math.radians(yaw))
    parts = []
    parts.append(D.rounded_box(name + "_body", (w, d, h), 0.045, soft=False, base_at_zero=True,
                               mat=D.mat_clay(body, name=f"{name}_clay", rough=0.5, sss=0.08, sheen=0.15)))
    rf = gable_roof(name + "_roof", w + 0.07, d + 0.09, pitch * d, roof_mat(roof, f"{name}_roof"))
    rf.location = (0.0, 0.0, h - 0.006)
    parts.append(rf)
    dr = D.rounded_box(name + "_door", (0.075 * (w / 0.3) ** 0.3, 0.02, 0.125 * (h / 0.3) ** 0.3), 0.012,
                       base_at_zero=True, mat=D.mat_candy(door, name=f"{name}_door", rough=0.25))
    dr.location = (0.0 if windows != 2 else 0.0, -d / 2 - 0.006, 0.0)
    parts.append(dr)
    wm = window_mat(name + "_win")
    wy = -d / 2 - 0.005
    ws = (0.055, 0.016, 0.065)
    if windows == 2:
        xs = [-w * 0.30, w * 0.30]
    else:
        xs = [w * 0.27]
        dr.location.x = -w * 0.15
    for i, x in enumerate(xs):
        win = D.rounded_box(f"{name}_win{i}", ws, 0.012, mat=wm)
        win.location = (x, wy, h * 0.58)
        parts.append(win)
    # one side window per side so the glow reads from the 3/4 view
    for sgn in (-1, 1):
        win = D.rounded_box(f"{name}_swin{sgn}", (0.016, ws[0], ws[2]), 0.012, mat=wm)
        win.location = (sgn * (w / 2 + 0.005), 0.0, h * 0.58)
        parts.append(win)
    if chimney:
        ch = D.rounded_box(name + "_chimney", (0.065, 0.065, 0.16), 0.016, base_at_zero=True,
                           mat=D.mat_candy(door, name=f"{name}_chim", rough=0.25))
        ch.location = (w * 0.28, d * 0.18, h + pitch * d * 0.30)
        parts.append(ch)
    for p in parts:
        p.parent = root
    return root


def tree(name, xy, height, colr, radius=None):
    r = radius or height * 0.34
    root = D.empty(name, (xy[0], xy[1], PLATE_TOP))
    trunk = D.cylinder(name + "_trunk", 0.026, 0.07, (0, 0, 0), mat=TRUNK, bevel=0.008, segments=32,
                       base_at_zero=True)
    cn = D.cone(name + "_cone", r, height, (0, 0, 0.055 + height / 2), mat=D.mat_candy(colr, name=f"{name}_leaf",
                                                                                    rough=0.30, coat=0.6, coat_rough=0.12),
                bevel=0.025)
    for p in (trunk, cn):
        p.parent = root
    return root


# ----------------------------------------------------------------------------------------------
# set
# ----------------------------------------------------------------------------------------------
def cove_mat():
    """Matte sky-blue cove.  A low sun barely lights the back wall, which then went grey-lavender in the morning
    and dusty mauve at dusk (G2), so the cove carries a faint self-lift in its own colour (emission sampling off:
    it lights nothing else); the shadows that fall on it stay cool and coloured."""
    c = ENV("TT_COVE", "#C2E0FF")
    m = D.mat_clay(c, name="cove_sky", rough=0.65, sss=0.0, sheen=0.0)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Specular IOR Level"].default_value = 0.25
    p.inputs["Emission Color"].default_value = D.col(ENV("TT_COVE_EMIT_COL", "#BFDCFF"))
    p.inputs["Emission Strength"].default_value = envf("TT_COVE_EMIT", 0.22)
    m.cycles.emission_sampling = "NONE"
    return m


cove = D.cyclorama("Cove", width=16, depth=12, height=7, radius=2.2, wall_y=3.4, mat=cove_mat())

PLATE_R, PLATE_H = 1.0, 0.10
D.cylinder("PlateBase", PLATE_R + 0.06, 0.07, (0, 0, 0), mat=D.mat_candy("lilac", name="plate_lilac", rough=0.3),
           bevel=0.03, base_at_zero=True)
D.cylinder("Plate", PLATE_R, PLATE_H, (0, 0, 0.0), mat=D.mat_clay(ENV("TT_PLATE", "#DCCDFF"), name="plate_lavender",
                                                                  rough=0.55, sss=0.0, sheen=0.1),
           bevel=0.035, base_at_zero=True)
PLATE_TOP = PLATE_H
TRUNK = D.mat_clay("#F2A66B", name="trunk_caramel", rough=0.5, sss=0.0, sheen=0.1)

HOUSES = [
    # name, xy, yaw, (w, d, h), body, roof, door, kwargs
    ("Hero", (0.0, 0.16), 0.0, (0.46, 0.36, 0.38), "lemon", "pink", "blue", dict(chimney=True)),
    ("HouseL", (-0.58, 0.12), 24.0, (0.30, 0.28, 0.30), "mint", "coral", "violet", dict(windows=1)),
    ("HouseR", (0.57, 0.20), -22.0, (0.27, 0.27, 0.44), "pink", "violet", "lemon", dict(windows=1)),
    ("HouseFL", (-0.34, -0.42), 12.0, (0.26, 0.24, 0.24), "aqua", "orange", "pink", dict(windows=1)),
    ("HouseFR", (0.38, -0.40), -14.0, (0.27, 0.24, 0.26), "coral", "blue", "lemon", dict(windows=1)),
]
for nm, xy, yaw, size, body, roofc, doorc, kw in HOUSES:
    house(nm, xy, yaw, size, body, roofc, doorc, **kw)

TREES = [("TreeL", (-0.80, -0.16), 0.38, "lime"), ("TreeR", (0.82, -0.12), 0.42, "mint"),
         ("TreeBL", (-0.26, 0.64), 0.44, "lime"), ("TreeBR", (0.25, 0.68), 0.36, "mint"),
         ("TreeF", (0.0, -0.74), 0.26, "lime")]
for nm, xy, hgt, colr in TREES:
    tree(nm, xy, hgt, colr)

# ----------------------------------------------------------------------------------------------
# light: the sun (moves) + lavender-blue sky fill (shadow colour) + one big soft front softbox
# ----------------------------------------------------------------------------------------------
sun = D.light("SUN", "Sun", (0, 0, 5), None, power=SUN_W, color="#FFF5E6", size=envf("TT_SUN_ANGLE", 3.0))
sun.rotation_mode = "XYZ"
D.bake(sun, "rotation_euler", BAKE0, BAKE1, lambda f: tuple(sun_rot(f)))
D.bake(sun.data, "color", BAKE0, BAKE1, sun_col)
D.bake(sun.data, "energy", BAKE0, BAKE1, sun_power)

SKY0, SKY1 = D.col("#C9DAFF"), D.col("#D6C6FF")          # sky fill: blue-lavender by day, violet at dusk
rig = D.world_color("#C9DAFF", envf("TT_WORLD", 0.28))


def sky_col(f):
    u = D.smoothstep((day_t(f) - 0.55) / 0.45)
    return tuple(SKY0[i] + (SKY1[i] - SKY0[i]) * u for i in range(3)) + (1.0,)


D.bake(rig.light_bg.inputs["Color"], "default_value", BAKE0, BAKE1, sky_col)
soft = D.light("AREA", "Soft", (0.8, -3.6, 3.2), (0.0, 0.0, 0.2), power=envf("TT_FILL", 90.0), color="#F4F0FF",
               size=4.0)
soft.visible_glossy = False

# dusk: the windows light up over the last ~40 frames
GLOW = 3.0


def glow(f):
    return GLOW * D.smoothstep((f - 138.0) / 40.0)


for m in WIN_MATS:
    D.bake(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", BAKE0, BAKE1, glow)

# camera: elevated 3/4 product view of the whole plate, locked
CAM = envv("TT_CAM", "0.0,-3.40,2.60")
TGT = envv("TT_TGT", "0.0,0.06,0.04")
cam, cam_t = D.camera("Cam", tuple(CAM), tuple(TGT), lens=envf("TT_LENS", 50.0), fstop=8.0)
focus = D.empty("Focus", (0.0, 0.0, 0.25))
cam.data.dof.focus_object = focus

# ----------------------------------------------------------------------------------------------
# meta
# ----------------------------------------------------------------------------------------------
META_PATH = os.path.join(D.ROOT, "renders", "meta", SHOT + ".json")
meta = {
    "id": SHOT, "group": "T3", "frames": N, "loop": LOOP, "seamless": False, "fps": 30, "res": list(RES),
    "bg": "sky / lavender", "bg_hex": D.PALETTE[BG], "ground_hex": ENV("TT_PLATE", "#DCCDFF"),
    "hero": "candy toy town on a lavender cake-plate: lemon / pink-roof hero house, four smaller rounded clay houses "
            "with candy gable roofs, five cone trees",
    "phenomenon": "moving sun over one day (morning -> noon -> evening): long soft shadows swing round and shrink / "
                  "stretch, warm key vs cool lavender sky fill in the shadows; windows light up at dusk",
    "palette": ["sky", "lavender", "lemon", "pink", "mint", "aqua", "coral", "lime"],
    "sun": {"azimuth_deg": [AZ0, AZ1], "elevation_deg": [EL0, EL1, EL0],
            "law": "t = (f - 1) / 179; s = t - 0.45 sin(2 pi t) / (2 pi); az = az0 + (az1 - az0) s; "
                   "el = el0 + (el1 - el0) sin(pi s)",
            "angle_deg": envf("TT_SUN_ANGLE", 3.0), "colour": [c for _, c in SUN_COLS]},
    "per_frame": {"sun_azimuth_deg": [round(sun_az(f), 3) for f in range(1, N + 1)],
                  "sun_elevation_deg": [round(sun_el(f), 3) for f in range(1, N + 1)]},
    "final": dict({"samples": FINAL_SPP, "threshold": FINAL_THR, "s_per_frame_measured": MEASURED_FINAL_SPF},
                  **COST),
    "hex": {"shape": "flat-top", "inscribed": True, "circumradius_px": RES[0] / 2},
}
os.makedirs(os.path.dirname(META_PATH), exist_ok=True)
with open(META_PATH, "w") as fh:
    json.dump(meta, fh, indent=1)

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
