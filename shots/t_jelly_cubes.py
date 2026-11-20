"""t_jelly_cubes -- hex-tile mini scene (group T3 "motion & world", docs/storyboard_v2.md section 5).

Hero / effect
-------------
Three rounded candy-jelly cubes on a pistachio cove hop in turn on the beat (orange f1, pink f16, blue f31; the
orange one takes off again on beat 4, f46) and land with a juicy, EXACTLY volume-preserving squash: height factor s,
a barrel bulge a = BULGE * (1 - s) and the radial scale c = 1 / sqrt(s * I(a)), I(a) = 1 + 4a/3 + 8a^2/15, applied
per vertex by a Geometry Nodes deformer (x' = x*c*(1 + a*4z(1-z)), z' = s*z, plus a top-weighted wobble shear,
which has unit Jacobian).  Every landing also shakes the cubes that are on the floor (small sympathetic jiggle).
The jelly is absorption glass (surface tint colour^0.5, G5) lit from behind, so each cube throws a soft coloured
caustic glow onto the floor in front of it.  Phenomenon: deforming geometry (volume-preserving squash and stretch)
with refraction / coloured transmitted light.

Contract (storyboard_v2 section 5): 1152 x 998 final (preview 576 x 499), flat-top hexagon inscribed in the frame
(vertices at the left/right edge midpoints) -- everything important is inside it; seamless 60-frame loop
(f61 == f1; every motion is a closed-form function of the cyclic phase (f - 1 - 15k) mod 60, baked per frame with
D.bake over f-2..f63, so motion-blur intervals at the seam are identical too); static seed; PBR Neutral, exposure
-0.2.  Meta: renders/meta/t_jelly_cubes.json.

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_jelly_cubes.py -- --mode preview
Test hooks (env, all default off): TJ_CAM="x,y,z", TJ_TGT="x,y,z", TJ_LENS, TJ_KEY, TJ_RIM, TJ_FILL, TJ_WORLD,
TJ_REPORT=1 (geometry / clearance / volume report, no render).  Finals must run with none of them set.
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
SHOT = "t_jelly_cubes"
LOOP = 60                      # seamless loop: frame LOOP + 1 == frame 1
N = LOOP
RES = (1152, 998)
BG = "pistachio"
EXPOSURE = float(os.environ.get("TJ_EXPO", "-0.2"))
FINAL_SPP, FINAL_THR = 256, 0.02
MEASURED_FINAL_SPF = 3.4       # steady-state final s/frame, H200 GPU 6 idle (nvidia-smi 0 % before the run)
COST = {"first_frame_s": 4.6, "gpu_h_est": 0.058,
        "measured": "2026-11-20, --mode final f1,4,19,40 in one process: 4.6 / 3.5 / 3.4 / 3.2 s; gpu_h = (first + 59 x s/f + 3 s scene build) / 3600"}
ENV = os.environ.get
args = D.parse_args()


def envf(name, default):
    return float(ENV(name, default))


def envv(name, default):
    return V(tuple(float(v) for v in ENV(name, default).split(",")))


D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=32, diffuse=4, glossy=6, transmission=12,
               volume=2, caustics=True, clamp_indirect=float(ENV("TJ_CLAMP", "30")), motion_blur=True, shutter=0.5)
D.setup_color(exposure=EXPOSURE)
D.setup_output(res=RES)
sc.frame_start, sc.frame_end = 1, N
BAKE0, BAKE1 = -2, N + 3

# ----------------------------------------------------------------------------------------------
# motion: closed form in the cyclic phase u = (f - 1 - 15 k) mod 60 (frames).  Landing at u = 0 (on the beat),
# ground u in [0, 45), take-off at u = 45, ballistic flight u in [45, 60) = 0.5 s.
# ----------------------------------------------------------------------------------------------
FPS = 30.0
STAGGER = 15                   # one beat at 120 BPM
T_AIR = 15                     # frames in the air
HOP = envf("TJ_HOP", 0.40)     # apex height of the base (m)
G_TOY = 8.0 * HOP / (T_AIR / FPS) ** 2          # toy gravity so the flight lasts exactly T_AIR frames
V0 = G_TOY * (T_AIR / FPS) / 2.0
BULGE = 0.45                   # barrel bulge per unit squash (a = BULGE * (1 - s))
SQ_AMP, SQ_DECAY, SQ_FREQ = 0.47, 4.2, 2.6      # landing spring: min height ~0.69 at ~2.6 f, rebound ~1.09
TD_STRETCH = 0.10              # stretch along the fall at touch-down / take-off
CROUCH = 0.16                  # anticipation squash before take-off
WOB_AMP, WOB_DECAY, WOB_FREQ = 0.050, 3.6, 2.4  # top-weighted wobble shear after landing (m)
SYMP_AMP = 0.045               # sympathetic squash when a neighbour lands

# cubes: (name, colour, edge, position, yaw, wobble direction)
CUBES = [
    ("JellyOrange", "orange", 0.32, (-0.44, 0.26), -14.0, (-1.0, 0.25)),
    ("JellyPink", "pink", 0.40, (0.00, -0.06), 9.0, (0.85, 0.3)),
    ("JellyBlue", "blue", 0.32, (0.44, 0.26), 17.0, (1.0, 0.25)),
]


def phase(f, k):
    return (f - 1 - STAGGER * k) % LOOP


def air_tau(u):
    """Seconds since take-off, or None while on the ground."""
    return (u - (LOOP - T_AIR)) / FPS if u >= LOOP - T_AIR else None


def base_z(u):
    t = air_tau(u)
    if t is None:
        return 0.0
    return V0 * t - 0.5 * G_TOY * t * t


def landing_spring(u):
    """Height offset after touch-down: starts at the fall stretch, dives into the squash, rebounds, decays, and is
    tapered to exactly zero before the crouch begins."""
    t = u / FPS
    w = 2 * math.pi * SQ_FREQ
    e = math.exp(-SQ_DECAY * t)
    taper = 1.0 - D.smootherstep((u - 18.0) / 12.0)
    return e * (TD_STRETCH * math.cos(w * t) - SQ_AMP * math.sin(w * t)) * taper


def height_factor(u, f, k):
    t = air_tau(u)
    if t is not None:                           # flight: stretched along the speed, relaxed at the apex
        x = 1.0 - 2.0 * t / (T_AIR / FPS)      # +1 at take-off, -1 at touch-down
        return 1.0 + TD_STRETCH * x * x
    s = 1.0 + landing_spring(u)
    # anticipation crouch (u 33..42) then the push-off extension (u 42..45) into the take-off stretch
    s -= CROUCH * D.smoothstep((u - 33.0) / 9.0)
    s += (CROUCH + TD_STRETCH) * D.smoothstep((u - 42.0) / 3.0)
    # sympathetic jiggle when a neighbour lands (gated to the ground phase so take-off stays clean)
    gate = D.smoothstep(u / 3.0) * (1.0 - D.smoothstep((u - 36.0) / 6.0))
    for j in range(len(CUBES)):
        if j == k:
            continue
        tj = phase(f, j) / FPS
        s -= gate * SYMP_AMP * math.exp(-6.0 * tj) * math.sin(2 * math.pi * 4.0 * tj)
    return s


def wobble(u, k):
    """Top-weighted shear (m at the top) after landing, along the cube's wobble direction; zero in the air."""
    if air_tau(u) is not None:
        return 0.0
    t = u / FPS
    taper = 1.0 - D.smootherstep((u - 22.0) / 14.0)
    return WOB_AMP * math.exp(-WOB_DECAY * t) * math.sin(2 * math.pi * WOB_FREQ * t) * taper


def twist(u):
    """Yaw twist in the air (deg): a smooth bump that is back to zero at touch-down."""
    t = air_tau(u)
    if t is None:
        return 0.0
    p = t / (T_AIR / FPS)
    return 22.0 * math.sin(math.pi * p) ** 2


# volume moments of the bulge profile b(z) = 4z(1-z) over the cube, <b> and <b^2> (volume-weighted).  A sharp box
# has 2/3 and 8/15; the rounded jelly cube is measured on its own mesh at build time (calibrate_moments below).
MOMENTS = [2.0 / 3.0, 8.0 / 15.0]


def bulge_params(s):
    """a = bulge amount, c = radial scale.  The map (x, y, z) -> (c (1 + a b) x, c (1 + a b) y, s z) has Jacobian
    s c^2 (1 + a b)^2, so the volume ratio is s c^2 (1 + 2 a <b> + a^2 <b^2>) == 1 exactly for this c."""
    a = BULGE * (1.0 - s)
    i = 1.0 + 2.0 * a * MOMENTS[0] + a * a * MOMENTS[1]
    return a, 1.0 / math.sqrt(s * i)


# ----------------------------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------------------------
def jelly_mat(color, name, depth, tint_exp=0.15):
    """Absorption jelly solved from its target colour: Beer-Lambert sigma = -ln(T) / depth, with T = the linear
    palette colour, so light that crosses `depth` metres of jelly comes out exactly on the palette hue (a plain
    palette-coloured absorber would drift: pink -> salmon-red, because it eats blue as fast as green).  The surface
    tint is a faint colour^0.15 (G5: Cycles applies it at both interfaces).  Thin rounded edges stay lighter and
    glow; a touch of roughness gives a gelatin sheen."""
    c = D.col(color)
    sig = [-math.log(max(x, 0.004)) / depth for x in c[:3]]
    dens = max(sig)
    absorb = tuple(1.0 - v / dens for v in sig) + (1.0,)
    m = D.mat_glass(color, name=name, rough=0.04, ior=1.40, absorb=dens)
    m.node_tree.nodes["Volume Absorption"].inputs["Color"].default_value = absorb
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (c[0] ** tint_exp, c[1] ** tint_exp, c[2] ** tint_exp, 1.0)
    return m, dens, absorb


def cove_mat():
    """Matte pistachio cove.  No sheen, no coat, low specular: at the camera's grazing view those all add white
    and the floor read as pale mint (G2).  The albedo is pre-deepened so the lit floor lands on pistachio."""
    m = D.mat_clay(ENV("TJ_COVE", "#C8F2D6"), name="cove_pistachio", rough=0.65, sss=0.0, sheen=0.0)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Specular IOR Level"].default_value = float(ENV("TJ_COVE_SPEC", "0.25"))
    p.inputs["Coat Weight"].default_value = float(ENV("TJ_COVE_COAT", "0.0"))
    p.inputs["Coat Roughness"].default_value = 0.25
    return m


# ----------------------------------------------------------------------------------------------
# geometry-nodes jelly deformer (object space, origin at the base centre, z up)
# ----------------------------------------------------------------------------------------------
def jelly_deformer():
    ng = bpy.data.node_groups.new("JellyDeform", "GeometryNodeTree")
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    socks = {}
    for nm, dv in (("Height", 0.4), ("S", 1.0), ("A", 0.0), ("C", 1.0), ("Wx", 0.0), ("Wy", 0.0)):
        s = it.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = dv
        socks[nm] = s
    n, l = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    pos = n.new("GeometryNodeInputPosition")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(pos.outputs[0], sep.inputs[0])

    def math_node(op, a, b=None, c=None):
        m = n.new("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    zeta = math_node("DIVIDE", sep.outputs["Z"], gi.outputs["Height"])
    zeta = math_node("MAXIMUM", math_node("MINIMUM", zeta, 1.0), 0.0)
    bul = math_node("MULTIPLY", math_node("MULTIPLY", zeta, math_node("SUBTRACT", 1.0, zeta)), 4.0)
    g = math_node("MULTIPLY", gi.outputs["C"], math_node("MULTIPLY_ADD", gi.outputs["A"], bul, 1.0))
    z2 = math_node("MULTIPLY", zeta, zeta)
    x2 = math_node("MULTIPLY_ADD", sep.outputs["X"], g, math_node("MULTIPLY", gi.outputs["Wx"], z2))
    y2 = math_node("MULTIPLY_ADD", sep.outputs["Y"], g, math_node("MULTIPLY", gi.outputs["Wy"], z2))
    zz = math_node("MULTIPLY", sep.outputs["Z"], gi.outputs["S"])
    comb = n.new("ShaderNodeCombineXYZ")
    l.new(x2, comb.inputs[0])
    l.new(y2, comb.inputs[1])
    l.new(zz, comb.inputs[2])
    sp = n.new("GeometryNodeSetPosition")
    l.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    l.new(comb.outputs[0], sp.inputs["Position"])
    l.new(sp.outputs[0], go.inputs["Geometry"])
    return ng, {k: v.identifier for k, v in socks.items()}


# ----------------------------------------------------------------------------------------------
# set
# ----------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14, depth=10, height=6, radius=1.4, wall_y=2.6, mat=cove_mat())

DEFORM, SOCK = jelly_deformer()


def eval_volume(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    v = bm.calc_volume(signed=False)
    bm.free()
    ev.to_mesh_clear()
    return v


def calibrate_moments(ob, mod):
    """<b>, <b^2> of this mesh from three evaluated volumes (S = C = 1; A = 0, +0.3, -0.3)."""
    vols = []
    for a in (0.0, 0.3, -0.3):
        mod[SOCK["A"]] = a
        ob.data.update()
        vols.append(eval_volume(ob))
    mod[SOCK["A"]] = 0.0
    v0, vp, vm = vols
    return [(vp - vm) / (1.2 * v0), ((vp + vm) / (2.0 * v0) - 1.0) / 0.09]
DEPTH_K = envf("TJ_DEPTH", 0.55)     # light crossing 0.55 x edge of jelly lands on the palette colour
JELLY = {}
cubes = []
for k, (nm, colr, edge, xy, yaw0, wdir) in enumerate(CUBES):
    jm, dens, absorb = jelly_mat(colr, "jelly_" + colr, DEPTH_K * edge)
    JELLY[colr] = {"density": round(dens, 3), "absorb_linear": [round(v, 4) for v in absorb[:3]],
                   "depth_m": round(DEPTH_K * edge, 4)}
    ob = D.rounded_box(nm, (edge, edge, edge), 0.26 * edge, soft=True, base_at_zero=True, mat=jm)
    mod = ob.modifiers.new("Jelly", "NODES")
    mod.node_group = DEFORM
    mod[SOCK["Height"]] = edge
    if k == 0:                       # all three cubes share the same (scaled) shape
        MOMENTS[:] = calibrate_moments(ob, mod)
        print(f"[t_jelly] bulge moments <b>={MOMENTS[0]:.4f} <b^2>={MOMENTS[1]:.4f} (sharp box 0.6667 / 0.5333)",
              flush=True)
    wd = V((wdir[0], wdir[1], 0.0)).normalized()

    def loc_fn(f, k=k, xy=xy):
        return (xy[0], xy[1], base_z(phase(f, k)))

    def rot_fn(f, k=k, yaw0=yaw0):
        return (0.0, 0.0, math.radians(yaw0 + twist(phase(f, k))))

    def s_fn(f, k=k):
        return height_factor(phase(f, k), f, k)

    D.bake(ob, "location", BAKE0, BAKE1, loc_fn)
    D.bake(ob, "rotation_euler", BAKE0, BAKE1, rot_fn)
    D.bake(mod, f'["{SOCK["S"]}"]', BAKE0, BAKE1, s_fn)
    D.bake(mod, f'["{SOCK["A"]}"]', BAKE0, BAKE1, lambda f, s_fn=s_fn: bulge_params(s_fn(f))[0])
    D.bake(mod, f'["{SOCK["C"]}"]', BAKE0, BAKE1, lambda f, s_fn=s_fn: bulge_params(s_fn(f))[1])

    # wobble direction is given in world xy -> object local (undo the yaw incl. the air twist)
    def w_local(f, k=k, yaw0=yaw0, wd=wd, comp=0):
        u = phase(f, k)
        w = wobble(u, k)
        a = -math.radians(yaw0 + twist(u))
        lx = wd.x * math.cos(a) - wd.y * math.sin(a)
        ly = wd.x * math.sin(a) + wd.y * math.cos(a)
        return w * (lx if comp == 0 else ly)

    D.bake(mod, f'["{SOCK["Wx"]}"]', BAKE0, BAKE1, lambda f, w_local=w_local: w_local(f, comp=0))
    D.bake(mod, f'["{SOCK["Wy"]}"]', BAKE0, BAKE1, lambda f, w_local=w_local: w_local(f, comp=1))
    cubes.append(ob)

# ----------------------------------------------------------------------------------------------
# light: big warm softbox key (front-left, high), a back light behind the cubes (the jelly glows and throws its
# coloured caustics forward onto the floor), a cool fill, studio HDRI for the window reflections
# ----------------------------------------------------------------------------------------------
KEY_W, RIM_W, FILL_W = envf("TJ_KEY", 55), envf("TJ_RIM", 200), envf("TJ_FILL", 18)
key = D.light("AREA", "Key", (-2.2, -2.4, 3.0), (0.0, 0.0, 0.25), power=KEY_W, color="#FFF3E6", size=2.4)
rim = D.light("AREA", "Rim", tuple(envv("TJ_RIM_POS", "0.3,1.9,2.3")), (0.0, -0.10, 0.15), power=RIM_W,
              color="#FFFFFF", size=1.0)
rim.data.shape = "DISK"
rim.visible_glossy = ENV("TJ_RIM_GLOSSY") == "1"   # no hazy floor sheen from the back light
fill = D.light("AREA", "Fill", (2.8, -2.0, 1.4), (0.0, 0.0, 0.3), power=FILL_W, color="#E3E8FF", size=3.0)
rig = D.world_hdri(D.HDRI["studio_small_09"], envf("TJ_WORLD", 0.07), camera_bg=BG)

# camera: 85 mm product lens, slightly above the cubes; DOF keeps the cove soft
CAM = envv("TJ_CAM", "0.0,-3.72,1.20")
TGT = envv("TJ_TGT", "0.0,0.05,0.30")
cam, cam_t = D.camera("Cam", tuple(CAM), tuple(TGT), lens=envf("TJ_LENS", 85.0), fstop=5.6)
focus = D.empty("Focus", (0.0, 0.0, 0.25))
cam.data.dof.focus_object = focus

# ----------------------------------------------------------------------------------------------
# report (TJ_REPORT=1): volume at max squash, clearances
# ----------------------------------------------------------------------------------------------
META_PATH = os.path.join(D.ROOT, "renders", "meta", SHOT + ".json")
report = {}
if ENV("TJ_REPORT") == "1" or args.mode == "preview":
    sc.frame_set(1)
    rest = {}
    for k, ob in enumerate(cubes):
        # rest volume: a phase where the cube is fully settled
        f_rest = 1 + STAGGER * k + 30
        sc.frame_set(f_rest)
        rest[ob.name] = eval_volume(ob)
    vols = {}
    for k, ob in enumerate(cubes):
        f_sq = 1 + STAGGER * k + 3            # max squash ~3 frames after landing
        sc.frame_set(f_sq)
        s = bpy.context.evaluated_depsgraph_get()
        vols[ob.name] = {"rest_m3": round(rest[ob.name], 6), "squash_frame": f_sq,
                         "s": round(height_factor(phase(f_sq, k), f_sq, k), 4),
                         "ratio": round(eval_volume(ob) / rest[ob.name], 5)}
    report["volume"] = vols
    # intersection check between every pair of cubes over the whole loop (evaluated geometry, BVH overlap)
    from mathutils.bvhtree import BVHTree
    hits = []
    vdev = 0.0
    for f in range(1, LOOP + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        trees = []
        for ob in cubes:
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ob.matrix_world
            trees.append(BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]))
            bm = bmesh.new()
            bm.from_mesh(me)
            vdev = max(vdev, abs(bm.calc_volume(signed=False) / rest[ob.name] - 1.0))
            bm.free()
            ev.to_mesh_clear()
        for i in range(3):
            for j in range(i + 1, 3):
                if trees[i].overlap(trees[j]):
                    hits.append((f, cubes[i].name, cubes[j].name))
    report["intersections"] = hits
    report["volume_max_rel_dev_all_frames"] = round(vdev, 6)
    report["bulge_moments"] = [round(v, 5) for v in MOMENTS]
    print("[t_jelly] report", json.dumps(report), flush=True)
    sc.frame_set(1)
elif os.path.exists(META_PATH):          # keep the last report (final / draft runs do not recompute it)
    try:
        with open(META_PATH) as fh:
            report = json.load(fh).get("report", {})
    except (OSError, ValueError):
        report = {}

# ----------------------------------------------------------------------------------------------
# meta
# ----------------------------------------------------------------------------------------------
events = {"land_orange": [1], "land_pink": [16], "land_blue": [31], "takeoff_orange": [46],
          "takeoff_pink": [1], "takeoff_blue": [16]}
meta = {
    "id": SHOT, "group": "T3", "frames": N, "loop": LOOP, "seamless": True, "fps": 30, "res": list(RES),
    "bg": BG, "bg_hex": D.PALETTE[BG],
    "hero": "three rounded candy-jelly cubes (orange 0.32 m, pink 0.40 m, blue 0.32 m) on a pistachio cove",
    "phenomenon": "deforming geometry: exactly volume-preserving squash / stretch with barrel bulge and wobble "
                  "(Geometry Nodes, closed form); absorption-glass jelly with coloured transmitted caustic glow",
    "palette": ["pistachio", "orange", "pink", "blue"],
    "events": events,
    "motion": {"loop_frames": LOOP, "stagger_frames": STAGGER, "air_frames": T_AIR, "hop_m": HOP,
               "toy_gravity": round(G_TOY, 3), "bulge": BULGE, "landing_spring": [SQ_AMP, SQ_DECAY, SQ_FREQ]},
    "per_frame": {c[0]: {"height_factor": [round(height_factor(phase(f, k), f, k), 4) for f in range(1, N + 1)],
                         "base_z": [round(base_z(phase(f, k)), 4) for f in range(1, N + 1)]}
                  for k, c in enumerate(CUBES)},
    "report": report,
    "jelly": JELLY,
    "final": dict({"samples": FINAL_SPP, "threshold": FINAL_THR, "s_per_frame_measured": MEASURED_FINAL_SPF},
                  **COST),
    "hex": {"shape": "flat-top", "inscribed": True, "circumradius_px": RES[0] / 2},
}
os.makedirs(os.path.dirname(META_PATH), exist_ok=True)
with open(META_PATH, "w") as fh:
    json.dump(meta, fh, indent=1)

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
