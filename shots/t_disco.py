"""T1 tile · t_disco — "Mirror ball" (finale honeycomb mini scene, storyboard_v2 section 5, group T1).

A mirror-tile disco ball turns under one narrow spot in a lilac cove.  Every flat tile is a small mirror, so the one
spot is broken into hundreds of light flecks that sweep across the cove wall and floor as the ball turns, while the
ball itself sparkles.  A few candy-coloured mirror tiles throw coloured flecks.

Tile contract (storyboard_v2 sections 4-5)
* 1152 x 998 final (preview 50 %), flat-top hexagon inscribed in the image: everything that matters sits inside
  the hexagon.  Hero (ball + its gold hanger) centred, ~60 % of the hex height, readable as a silhouette at 200 px.
* Seamless loop of LOOP frames: frame LOOP+1 == frame 1.  The tile grid repeats every 360/N_LON deg, so the ball turns
  exactly LOOP_COLS columns per loop and the colour pattern repeats every LOOP_COLS columns.
* Static seed, baked animation, PBR Neutral, exposure -0.2, no AgX / Filmic.  Meta: renders/meta/t_disco.json.
* Final: 256 spp, adaptive 0.02, OIDN: 3.51 s/f steady on one H200, uncontended (first frame of a process ~4.4 s,
  incl. baking 448 lights x 93 frames) -> 90 x 3.51 s = 0.088 GPU-h (cap 0.12).

How the flecks are rendered (deviation from plain path tracing, on purpose)
* A wall point inside a fleck is lit through exactly ONE tile, so a backward path from the wall has to hit that one
  3 cm tile by chance (~7e-5 per sample): path-traced disco flecks stay a firefly speckle at any affordable sample
  count (tested: 1024-2048 spp, tile roughness 0.02-0.15, Filter Glossy 0.3-0.6 -> speckle or a featureless glow;
  MNEE is refraction-only, path guiding is CPU-only).
* Light reflected by a flat mirror is exactly the light of the source's mirror image, restricted to the mirror's
  aperture (image-source method, geometric optics).  So every tile gets a baked virtual SPOT: at the source mirrored
  across the tile plane, aimed through the tile centre, cone = the tile's aperture seen from the image
  (round instead of square), colour = source x tile metal colour, power = source x reflectance x cos(incidence)
  (fades smoothly as a tile turns away).  The virtual spots light only the cove (light linking) and are invisible
  to glossy rays (the ball mirrors the lit cove, not the virtual sources).
* The virtual spots must NOT cast shadow rays (Light.use_shadow = False; Blender 4.x dropped cycles.cast_shadow):
  the image source sits behind its tile, inside / behind the ball, so with shadows on, the ball itself occludes
  the beam -- fully for most tiles and exactly half for the grazing rim tiles whose beams reach the back wall,
  which is what rendered the flecks as half-discs with a straight edge (the ball's silhouette seen from the image).
  Without shadow rays nothing spurious appears: a beam can only reach the cove from inside the (convex) room on
  the far side of its tile; where the cone crosses the cove from outside it meets the back face (no light).
* The ball, its glints (the real spot, light-linked to the ball), the cove, every reflection and all ambient light
  are ordinary Cycles path tracing.

Build decisions (v2 build; A/B'd on preview + final test frames)
* Fleck look: FLECK_GAIN 5 (artistic, flecks 5x the physical value), cone x1.5 (CONE_K, ~ a 1.5x larger source
  disc) and blend 0.12 -> clean round spots ~60-70 px at final that still read as dots at 200 px; f/16 keeps the
  wall sharp.  Cove ambient 110 W: a mid lilac (not the dark club violet of the first pass) on which the flecks
  stay bright.  At 256 spp + OIDN the spot edges are clean; preview (128 spp, half res) shows slightly lumpy edges.
* Candy tiles pink / aqua / mint / blue (lemon and orange mirrored the violet room as brown -> dropped).
* Motion: the ball turns LOOP_COLS 8 tile columns (90 deg) per 90-frame loop = 1 deg/f; flecks sweep the cove at
  ~2 deg/f.  The white fleck pattern repeats every column, the coloured flecks every 8 columns, so f91 == f1.
  Note for reviewers: stills one column apart (11.25 f) look alike apart from the coloured flecks; the sweep is
  continuous in motion.

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_disco.py -- --mode preview
QA:   env T_MASK=1 renders a white-on-black silhouette of the hero (framing / hex-fit measurement).
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

SHOT = "t_disco"
RES = (1152, 998)
BG = "lilac"


def envf(name, dflt):
    return float(os.environ.get(name, str(dflt)))


def envv(name, dflt):
    return Vector(tuple(float(x) for x in os.environ.get(name, dflt).split(",")))


LOOP = int(envf("T_LOOP", 90))
N = LOOP
FINAL_SPP = int(envf("T_SPP", 256))
FINAL_THR = envf("T_THR", 0.02)
MEASURED_FINAL_SPF = 3.51      # GPU 6 (H200), final 1152x998, steady, uncontended

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=int(envf("T_MINSPP", 32)), diffuse=3,
               glossy=int(envf("T_GB", 4)), transmission=2, volume=0, caustics=False, filter_glossy=0.0,
               clamp_indirect=envf("T_CLAMP", 10.0), motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("T_EXPO", -0.2))
D.setup_output(res=RES)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
BAKE = list(range(0, LOOP + 3))            # keys one frame past both ends (f1 / f(LOOP+1) shutters match)


def phase(f):
    """Loop phase in turns, NOT wrapped: f = LOOP+1 gives exactly 1.0."""
    return (f - 1) / float(LOOP)


def bake(target, path, fn, index=-1):
    D.bake(target, path, BAKE[0], BAKE[-1], fn, index=index)


def fast_bake(target, data_path, index, values):
    """Per-frame LINEAR keys on BAKE frames, written in one go (hundreds of lights x 93 frames)."""
    cur = target.path_resolve(data_path)
    if index >= 0:
        cur[index] = values[0]
    else:
        D.setattr_path(target, data_path, values[0])
    target.keyframe_insert(data_path, index=index, frame=BAKE[0])
    owner = D._anim_id(target)
    full = target.path_from_id(data_path) if hasattr(target, "path_from_id") else data_path
    fc = [c for c in D._fcurves(owner.animation_data.action)
          if c.data_path == full and c.array_index == max(index, 0)][0]
    kp = fc.keyframe_points
    kp.clear()
    kp.add(len(BAKE))
    co = []
    for f, v in zip(BAKE, values):
        co += [float(f), float(v)]
    kp.foreach_set("co", co)
    kp.foreach_set("interpolation", [1] * len(BAKE))          # LINEAR
    fc.update()


def linked_light(kind, name, loc, target, power, color, receivers, **kw):
    """Light that lights ONLY `receivers` (light linking)."""
    lt = D.light(kind, name, loc, target, power=power, color=color, **kw)
    coll = bpy.data.collections.new(name + "_link")
    for ob in receivers:
        coll.objects.link(ob)
    lt.light_linking.receiver_collection = coll
    return lt


# ----------------------------------------------------------------------------------------------
# the mirror ball: N_LON x N_LAT flat tiles on a violet grout core
# ----------------------------------------------------------------------------------------------
BALL_R = envf("T_BALL_R", 0.30)
BALL_C = envv("T_BALL_C", "0,0,1.0")
N_LON = int(envf("T_NLON", 32))
N_LAT = int(envf("T_NLAT", 14))            # rings between the polar caps
LAT_STEP = 180.0 / (N_LAT + 2)             # deg per ring; one ring-height cap at each pole
GAP = envf("T_GAP", 0.10)                  # grout gap as a fraction of the tile pitch
LOOP_COLS = int(envf("T_LOOP_COLS", 8))    # columns turned per loop (8 -> 1 deg/f) (the colour pattern repeats with this period)
CANDY = ["pink", "aqua", "mint", "blue"]    # lemon / orange tiles mirrored the violet room as brown -> dropped


def tile_color(i, j):
    """Sparse candy tiles in a pattern that repeats every LOOP_COLS columns (seamless loop)."""
    h = (((i % LOOP_COLS) * 7 + j * 13) * 2654435761) % 1000
    if h < int(envf("T_CANDY_FRAC", 0.10) * 1000):
        return CANDY[(i % LOOP_COLS + 3 * j) % len(CANDY)]
    return None


TILE_R = envf("T_TILE_R", 0.06)
mats = {None: D.mat_metal("chrome", name="metal_tile", rough=TILE_R)}
for c in CANDY:
    mats[c] = D.mat_metal(c, name=f"metal_tile_{c}", rough=TILE_R)
mat_order = [None] + CANDY

bm = bmesh.new()
TILES = []                                  # (centre, normal, half_size, colour) in ball-local coordinates
for j in range(N_LAT):
    lat0 = math.radians(-90 + LAT_STEP * (j + 1))
    lat1 = math.radians(-90 + LAT_STEP * (j + 2))
    for i in range(N_LON):
        lon0 = 2 * math.pi * i / N_LON
        lon1 = 2 * math.pi * (i + 1) / N_LON
        dl = (lon1 - lon0) * GAP / 2
        dt = (lat1 - lat0) * GAP / 2
        corners = [(lon0 + dl, lat0 + dt), (lon1 - dl, lat0 + dt), (lon1 - dl, lat1 - dt), (lon0 + dl, lat1 - dt)]
        lc, tc = (lon0 + lon1) / 2, (lat0 + lat1) / 2
        nrm = Vector((math.cos(tc) * math.cos(lc), math.cos(tc) * math.sin(lc), math.sin(tc)))
        ctr = nrm * BALL_R * math.cos(math.radians(LAT_STEP) / 2)
        pts = []
        for lo, la in corners:
            p = Vector((math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))) * BALL_R
            pts.append(p - nrm * (p - ctr).dot(nrm))      # project onto the tile plane -> a flat mirror
        f = bm.faces.new([bm.verts.new(tuple(p)) for p in pts])
        f.material_index = mat_order.index(tile_color(i, j))
        area = 0.5 * ((pts[2] - pts[0]).cross(pts[3] - pts[1])).length
        TILES.append((ctr, nrm, 0.5 * math.sqrt(area), tile_color(i, j)))
ball = D._mesh_object("DiscoBall", bm, None, smooth=False)
for c in mat_order:
    ball.data.materials.append(mats[c])
sol = ball.modifiers.new("Thick", "SOLIDIFY")
sol.thickness = 0.004
sol.offset = -1.0
core = D.sphere("Grout", BALL_R * 0.975, (0, 0, 0), D.mat_candy("violet", name="candy_grout", rough=0.35),
                segments=64, rings=32)
CAP_R = BALL_R * math.sin(math.radians(LAT_STEP)) * 1.02
cap_top = D.cylinder("CapTop", CAP_R, 0.03, (0, 0, BALL_R * math.cos(math.radians(LAT_STEP)) - 0.004),
                     base_at_zero=True, bevel=0.012, mat=D.mat_candy("pink", name="candy_pink", rough=0.2))
cap_bot = D.sphere("CapBot", CAP_R * 0.96, (0, 0, -BALL_R * math.cos(math.radians(LAT_STEP))),
                   D.mat_candy("pink", name="candy_pink2"), segments=48, rings=24)
spin = D.empty("Spin", tuple(BALL_C))
for ob in (ball, core, cap_top, cap_bot):
    ob.parent = spin
GOLD = D.mat_metal("gold", name="metal_gold", rough=0.2)
ROD_LEN = envf("T_ROD", 1.6)
rod_z0 = BALL_C.z + BALL_R * math.cos(math.radians(LAT_STEP)) + 0.02
rod = D.cylinder("Rod", 0.011, ROD_LEN, (BALL_C.x, BALL_C.y, rod_z0), base_at_zero=True, bevel=0.0, mat=GOLD)
collar = D.cylinder("Collar", 0.03, 0.05, (BALL_C.x, BALL_C.y, rod_z0), base_at_zero=True, bevel=0.012, mat=GOLD)
HERO = [ball, core, cap_top, cap_bot, rod, collar]

# ----------------------------------------------------------------------------------------------
# lilac cove
# ----------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=12.0, height=7.0, radius=1.2, wall_y=envf("T_WALLY", 1.6),
                   mat=D.mat_clay(BG, name="clay_cove", rough=0.7, sss=0.0, sheen=0.05))

# ----------------------------------------------------------------------------------------------
# light: the ONE spot (glints on the ball; light-linked to the ball), its fleck images, soft ambient, candy sky
# ----------------------------------------------------------------------------------------------
SPOT_POS = envv("T_SPOT_POS", "-0.35,-2.9,1.55")
SPOT_P = envf("T_SPOT", 3500)
SPOT_COL = "#FFF8F0"
spot = linked_light("SPOT", "DiscoSpot", tuple(SPOT_POS), tuple(BALL_C), SPOT_P, SPOT_COL,
                    [ball, core, cap_top, cap_bot, collar], radius=envf("T_SPOT_R", 0.06),
                    spot_deg=envf("T_SPOT_DEG", 20), blend=0.1)
amb = linked_light("AREA", "CoveAmb", tuple(envv("T_AMB_POS", "0.4,-2.6,2.8")), (0, 1.2, 0.6),
                   envf("T_AMB", 110), "white", [cove], size=4.0)
amb.visible_glossy = False
ballfill = linked_light("AREA", "BallFill", tuple(envv("T_BF_POS", "1.6,-1.8,1.8")), tuple(BALL_C),
                        envf("T_BF", 40), "#E8DEFF", [core, cap_top, cap_bot, rod, collar], size=1.5)
sky_path = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
WORLD_K = envf("T_WORLD", 0.05)
WORLD_GLOSSY = envf("T_WGLOSSY", 0.8)
rig = D.world_hdri(sky_path, WORLD_K, camera_bg=BG)
_wn, _wl = rig.world.node_tree.nodes, rig.world.node_tree.links
_lp = _wn.new("ShaderNodeLightPath")
_ma = _wn.new("ShaderNodeMath")
_ma.operation = "MULTIPLY_ADD"
_ma.inputs[1].default_value = WORLD_GLOSSY - WORLD_K
_ma.inputs[2].default_value = WORLD_K
_wl.new(_lp.outputs["Is Glossy Ray"], _ma.inputs[0])
_wl.new(_ma.outputs[0], rig.light_bg.inputs["Strength"])
rig.world.cycles.sampling_method = "MANUAL"
rig.world.cycles.sample_map_resolution = 1024

# ----------------------------------------------------------------------------------------------
# animation: the ball turns LOOP_COLS tile columns per loop (constant speed)
# ----------------------------------------------------------------------------------------------
TURN_PER_LOOP = 2 * math.pi * LOOP_COLS / N_LON


def spin_angle(f):
    return TURN_PER_LOOP * phase(f)


bake(spin, "rotation_euler", lambda f: (0.0, 0.0, spin_angle(f)))

# ----------------------------------------------------------------------------------------------
# fleck images: one virtual spot per tile (image-source method, see the header)
# ----------------------------------------------------------------------------------------------
FLECK_K = envf("T_FLECK_K", 0.9)           # chrome reflectance
FLECK_GAIN = envf("T_FLECK_GAIN", 5.0)     # artistic: flecks 5x the physical value so they read on a mid-lilac wall
FLECK_BLEND = envf("T_FLECK_BLEND", 0.12)
FLECK_AREA_K = 2.0 / math.sqrt(math.pi)    # round cone with the same area as the square tile aperture
fleck_coll = bpy.data.collections.new("Fleck_receivers")
fleck_coll.objects.link(cove)
src_lin = D.col(SPOT_COL)
n_lit_max = 0
if not os.environ.get("T_NOFLECKS"):
    per_frame = []
    for f in BAKE:
        R = Matrix.Rotation(spin_angle(f), 3, "Z")
        rows = []
        for (c, n, h, colname) in TILES:
            C = BALL_C + R @ c
            Nw = R @ n
            to_s = SPOT_POS - C
            dist = to_s.length
            cos_i = Nw.dot(to_s) / dist
            S_img = SPOT_POS - 2.0 * to_s.dot(Nw) * Nw          # source mirrored across the tile plane
            d_out = (C - S_img).normalized()
            rows.append((S_img, d_out, max(0.0, cos_i), dist))
        per_frame.append(rows)
    for k, (c, n, h, colname) in enumerate(TILES):
        tcol = D.col(colname) if colname else D.col("chrome")
        lt = D.light("SPOT", f"Fleck{k:03d}", (0, 0, 0), None, power=0.0,
                     color=(1, 1, 1), radius=0.0, spot_deg=1.0, blend=FLECK_BLEND)
        lt.data.color = (src_lin[0] * tcol[0], src_lin[1] * tcol[1], src_lin[2] * tcol[2])
        # cone = the tile aperture seen from the image, per frame (|image - tile| = |spot - tile| changes as the tile
        # turns; a per-light constant made f(LOOP+1) differ from f1, where a different light holds each position)
        cone_k = envf("T_FLECK_CONE_K", 1.5)
        cones = [2.0 * math.atan(FLECK_AREA_K * h / per_frame[i][k][3]) * cone_k for i in range(len(BAKE))]
        lt.data.spot_size = cones[0]
        lt.data.use_shadow = False             # Blender 4.x: Cycles reads Light.use_shadow (cycles.cast_shadow is gone)
        lt.visible_glossy = False
        lt.visible_transmission = False
        lt.visible_volume_scatter = False
        if not os.environ.get("T_FLECK_NOLINK"):
            lt.light_linking.receiver_collection = fleck_coll
        if os.environ.get("T_FLECK_NOSOFT"):
            lt.data.use_soft_falloff = False
        lt.data.shadow_soft_size = envf("T_FLECK_RAD", 0.0)
        locs = [per_frame[i][k][0] for i in range(len(BAKE))]
        eul, rots = None, []
        for i in range(len(BAKE)):
            q = per_frame[i][k][1].to_track_quat("-Z", "Y")
            eul = q.to_euler("XYZ", eul) if eul is not None else q.to_euler("XYZ")
            rots.append(tuple(eul))
        for a in range(3):
            fast_bake(lt, "location", a, [p[a] for p in locs])
            fast_bake(lt, "rotation_euler", a, [r[a] for r in rots])
        fast_bake(lt.data, "spot_size", -1, cones)
        fast_bake(lt.data, "energy", -1, [SPOT_P * FLECK_K * FLECK_GAIN * per_frame[i][k][2] for i in range(len(BAKE))])
    n_lit_max = max(sum(1 for r in rows if r[2] > 0) for rows in per_frame)

# ----------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------
LENS = envf("T_LENS", 75)
EL = math.radians(envf("T_EL", 8))
DIST = envf("T_DIST", 3.0)
CAM_TGT = envv("T_CAM_TGT", "0,0,0.95")
cam_loc = CAM_TGT + DIST * Vector((0, -math.cos(EL), math.sin(EL)))
cam, cam_t = D.camera("Cam", tuple(cam_loc), tuple(CAM_TGT), lens=LENS, fstop=envf("T_FSTOP", 16.0))

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
    "hero": f"mirror-tile disco ball ({N_LON} x {N_LAT} flat tiles, ~10 % candy-coloured) on a gold hanger",
    "phenomenon": "mirror reflections: one spot broken by the tiles into light flecks sweeping the cove "
                  "(flecks via baked image-source lights; see the script header)",
    "palette": list(dict.fromkeys([BG, "chrome", "violet", "pink", "gold"] + CANDY)),
    "motion": f"ball turns {math.degrees(TURN_PER_LOOP):.2f} deg per loop ({LOOP_COLS} tile columns)",
    "fleck_lights": len(TILES),
    "fleck_lights_lit_max": n_lit_max,
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
print(f"[t_disco] tiles {len(TILES)}  lit fleck lights (max per frame) {n_lit_max}", flush=True)
if os.environ.get("T_NODENOISE"):
    sc.cycles.use_denoising = False
D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
