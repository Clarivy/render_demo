"""t_fruit_sss -- honeycomb mini-scene (T2 "light & material"): backlit kiwi and lime halves glowing from within.

What the tile proves (storyboard_v2 section 5)
----------------------------------------------
Subsurface scattering.  A kiwi half and a lime half stand on a candy plate with their cut faces to the camera; a big
warm light sits BEHIND them.  Light enters through the peel at the back, random-walks through the flesh and leaves
through the cut face, so the faces glow from inside (brightest where the fruit is thin, at the rims), the seeds and
membranes stay dark/opaque against the glow, and the peel edges light up.  The plate turns slowly back and forth, so
the thickness the light crosses changes and the glow breathes across the faces.

Build
-----
* The Poly Haven scans (food_kiwi_01, food_lime_01) are whole fruit split into UV islands: the pieces are welded,
  bisected crosswise through the middle and the cut is closed with a fan cap whose UV rim lands exactly on the cut
  boundary.  The cross-sections (kiwi: cream core, radial streaks, two staggered rings of black seeds; lime: ten
  segments with white membranes, pith ring, rind) are painted procedurally with numpy into in-memory images
  (deterministic, fixed RNG seed) -- no texture files.
* Flesh: Principled random-walk SSS (weight 1, radius in scene metres ~ the fruit's thickness, green-weighted), wet
  roughness, a little coat.  Peel: the scan's own textures, a touch of SSS so the rims glow too.
* Background "blush-coral" (#FFA08E, deeper than a blush so the green glow pops against its complement): the
  backlight is light-linked to the fruit + plate only (the cove keeps its coral instead of bleaching to a white
  band); a soft blend-1 spot paints a warm radial halo on the wall behind the fruit, a dim wash keeps the corners
  coral.  Backlight 600 W with a low front fill (14 W): the cut faces are lit mostly from inside (A/B in the T2
  report: 340/30 read front-lit, 800/18 starts to bleach the lime centre).

Tile contract: 1152 x 998 final, flat-top hexagon safe area, seamless LOOP-frame loop (frame LOOP+1 == frame 1), static
seed, PBR Neutral, exposure -0.2, baked closed-form motion (D.bake over f-2..LOOP+3).  Meta: renders/meta/<id>.json.

Run:  CUDA_VISIBLE_DEVICES=7 tools/blender/blender -b --factory-startup -P shots/t_fruit_sss.py -- --mode preview
Look-dev hooks (env, default off; finals run without them): TFS_BACK, TFS_FILL, TFS_RIM, TFS_SSS_K, TFS_SSS_L, TFS_EXPO,
TFS_DIST, TFS_ELEV, TFS_SWAY, TFS_FSPP.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

V = Vector
SHOT = "t_fruit_sss"
LOOP = 180
RES = (1152, 998)
ENV = os.environ.get


def envf(name, default):
    return float(ENV(name, str(default)))


args = D.parse_args()
D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=256, threshold=0.02, min_samples=32, diffuse=4, glossy=6, transmission=8, volume=2,
               caustics=False, filter_glossy=0.3, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("TFS_EXPO", -0.2))
D.setup_output(res=RES)
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.frame_start, sc.frame_end = 1, LOOP
BAKE0, BAKE1 = -2, LOOP + 3

BG_NAME, BG_HEX = "blush-coral pastel", ENV("TFS_BG", "#FFA08E")

# ----------------------------------------------------------------------------------------------------------------
# procedural cross-section textures (numpy, deterministic)
# ----------------------------------------------------------------------------------------------------------------
TEX_N = 1024
TEX_R = 1.04                      # texture half-extent in units of the cut radius (r = 1 is the peel boundary)


def _hex(c):
    h = c.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def _sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _grid():
    s = (np.arange(TEX_N) + 0.5) / TEX_N * 2 * TEX_R - TEX_R
    x, y = np.meshgrid(s, s)          # row index = y (image bottom row first, as Blender pixel order)
    return x, y, np.hypot(x, y), np.arctan2(y, x)


def _value_noise(x, y, scale, rng):
    """Smooth 2D value noise on a lattice (bilinear of random corners, smoothstep weights)."""
    g = rng.random((int(scale * 2 * TEX_R) + 3, int(scale * 2 * TEX_R) + 3))
    u = (x + TEX_R) * scale
    v = (y + TEX_R) * scale
    i, j = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - i, v - j
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = g[j, i], g[j, i + 1], g[j + 1, i], g[j + 1, i + 1]
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv


def kiwi_section():
    rng = np.random.default_rng(7)
    x, y, r, a = _grid()
    n1 = _value_noise(x, y, 9.0, rng)
    n2 = _value_noise(x, y, 31.0, rng)
    # flesh: luminous green, lighter toward the seed ring, deeper toward the skin
    col = (_hex("#A6DA45")[None, None] * (1 - _sstep(0.42, 0.95, r))[..., None]
           + _hex("#6DBA25")[None, None] * _sstep(0.42, 0.95, r)[..., None])
    # radial streaks (the kiwi's pale rays), strongest just outside the core
    rays = 0.5 + 0.5 * np.sin(a * 46 + 6.0 * n1)
    ray_k = 0.10 * (rays ** 6) * _sstep(0.18, 0.3, r) * (1 - _sstep(0.55, 0.9, r))
    col = col * (1 - ray_k[..., None]) + _hex("#E9F7B0")[None, None] * ray_k[..., None]
    col *= (0.94 + 0.08 * n2)[..., None]
    # pale halo + cream core (slightly elliptical, wobbly edge)
    core_r = 0.19 * (1 + 0.10 * np.cos(2 * a) + 0.05 * (n1 - 0.5))
    halo = _sstep(core_r + 0.11, core_r + 0.02, r)
    col = col * (1 - 0.55 * halo[..., None]) + _hex("#D6EE86")[None, None] * 0.55 * halo[..., None]
    core = _sstep(core_r + 0.025, core_r - 0.01, r)
    core_col = _hex("#F4F0C9")[None, None] * (0.95 + 0.06 * rays[..., None])
    col = col * (1 - core[..., None]) + core_col * core[..., None]
    # seeds: two staggered rings of radial teardrops
    seed = np.zeros_like(r)
    for ring_r, count, off in ((0.292, 30, 0.0), (0.352, 36, 0.5), (0.410, 42, 0.25)):
        for k in range(count):
            ak = 2 * math.pi * (k + off + 0.35 * (rng.random() - 0.5)) / count
            rk = ring_r + 0.020 * (rng.random() - 0.5)
            L, W = 0.088 * (0.85 + 0.3 * rng.random()), 0.036 * (0.85 + 0.3 * rng.random())
            cx, cy = rk * math.cos(ak), rk * math.sin(ak)
            u = (x - cx) * math.cos(ak) + (y - cy) * math.sin(ak)          # radial
            v = -(x - cx) * math.sin(ak) + (y - cy) * math.cos(ak)         # tangential
            w = W * (0.62 + 0.38 * np.clip(u / (L / 2), -1, 1))           # teardrop: wider outward
            d = (u / (L / 2)) ** 2 + (v / (w / 2 + 1e-6)) ** 2
            seed = np.maximum(seed, _sstep(1.15, 0.75, d))
    col = col * (1 - seed[..., None]) + _hex("#20160C")[None, None] * seed[..., None]
    # skin rim
    rim = _sstep(0.955, 0.99, r)
    col = col * (1 - rim[..., None]) + _hex("#6E6A2A")[None, None] * rim[..., None]
    rough = 0.16 + 0.12 * core + 0.10 * rim
    return np.clip(col, 0, 1), rough, seed


def lime_section():
    rng = np.random.default_rng(11)
    x, y, r, a = _grid()
    n1 = _value_noise(x, y, 7.0, rng)
    n3 = _value_noise(x, y, 60.0, rng)
    K = 10
    edges = np.sort((np.arange(K) + 0.30 * (rng.random(K) - 0.5)) * 2 * math.pi / K)
    # angular distance to the nearest membrane (wrap-around)
    da = np.full_like(r, 9.0)
    seg_id = np.zeros_like(r, dtype=int)
    aa = np.mod(a, 2 * math.pi)
    for k, e in enumerate(edges):
        d = np.abs((aa - e + math.pi) % (2 * math.pi) - math.pi)
        da = np.minimum(da, d)
    for k in range(K):
        e0, e1 = edges[k], edges[(k + 1) % K] + (2 * math.pi if k == K - 1 else 0.0)
        inside = ((aa - e0) % (2 * math.pi)) < ((e1 - e0) % (2 * math.pi) or 2 * math.pi)
        seg_id = np.where(inside, k, seg_id)
    seg_tint = (rng.random(K) - 0.5) * 0.08
    flesh = _hex("#BCE436")[None, None] * (1.0 + seg_tint[seg_id][..., None])
    # juice vesicles: radial elongated cells
    ves = 0.5 + 0.5 * np.sin(a * 140 + 9.0 * n1) * np.sin(r * 55 + 4.0 * n1)
    flesh = flesh * (0.90 + 0.14 * ves[..., None]) * (0.96 + 0.06 * n3[..., None])
    flesh = flesh * (1 - 0.10 * _sstep(0.5, 0.85, r))[..., None]
    col = flesh
    # membranes (white, thicker toward the centre), core, pith ring, rind
    width = 0.010 + 0.012 * (1 - r)                                     # arc length
    mem = _sstep(1.0, 0.45, (da * np.maximum(r, 0.05)) / width) * _sstep(0.05, 0.12, r) * _sstep(0.88, 0.80, r)
    white = _hex("#F3F6DC")[None, None]
    col = col * (1 - mem[..., None]) + white * mem[..., None]
    core = _sstep(0.11, 0.06, r)
    col = col * (1 - core[..., None]) + white * core[..., None]
    pith = _sstep(0.80, 0.86, r)
    col = col * (1 - pith[..., None]) + _hex("#EEF4CF")[None, None] * pith[..., None]
    rind = _sstep(0.925, 0.955, r)
    rind_col = (_hex("#79B832")[None, None] * (1 - _sstep(0.955, 1.0, r))[..., None]
                + _hex("#3F8A1C")[None, None] * _sstep(0.955, 1.0, r)[..., None])
    col = col * (1 - rind[..., None]) + rind_col * rind[..., None]
    rough = 0.14 + 0.16 * pith + 0.1 * rind
    return np.clip(col, 0, 1), rough, mem


def np_image(name, rgb, alpha=None):
    """In-memory, packed sRGB image from a float array (rows bottom-up)."""
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    px = np.ones((h, w, 4), np.float32)
    px[..., :3] = rgb
    if alpha is not None:
        px[..., 3] = alpha
    img.pixels.foreach_set(px.ravel())
    img.update()                    # mark the buffer dirty, THEN pack: a generated image's edited buffer is otherwise
    img.pack()                      # freed and regenerated black during depsgraph evaluation
    img.colorspace_settings.name = "sRGB"
    return img


def np_data_image(name, val):
    h, w = val.shape
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True)
    px = np.ones((h, w, 4), np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = val
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.pack()
    img.colorspace_settings.name = "Non-Color"
    return img


# ----------------------------------------------------------------------------------------------------------------
# fruit halves from the scans
# ----------------------------------------------------------------------------------------------------------------
def load_half(rel, name, diameter, keep="below"):
    """Import a fruit scan, weld its UV islands, scale so its width = diameter, bisect it at mid-height and close the
    cut with a UV fan cap (material slot 1).  Returns the object; local frame: cut face in z=0, centre at the origin,
    the dome toward -z.  Also returns the cut radius."""
    root, meshes = D.import_gltf(os.path.join(D.ASSETS, "models", rel))
    ob = meshes[0]
    ob.parent = None
    ob.name = name
    bpy.data.objects.remove(root)
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
    co = np.array([v.co[:] for v in bm.verts])
    mn, mx = co.min(0), co.max(0)
    width = max(mx[0] - mn[0], mx[1] - mn[1])
    s = diameter / width
    zc = 0.5 * (mn[2] + mx[2])
    cen = V((0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1]), zc))
    bmesh.ops.transform(bm, matrix=Matrix.Scale(s, 4) @ Matrix.Translation(-cen), verts=bm.verts)
    nb0 = sum(1 for e in bm.edges if e.is_boundary)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                                 plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                                 clear_outer=(keep == "below"), clear_inner=(keep != "below"))
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    # order the cut loop
    bm.verts.ensure_lookup_table()
    loop_verts = []
    adj = {}
    for e in cut_edges:
        a_, b_ = e.verts
        adj.setdefault(a_, []).append(b_)
        adj.setdefault(b_, []).append(a_)
    start = next(iter(adj))
    prev, cur = None, start
    while True:
        loop_verts.append(cur)
        nxt = [w for w in adj[cur] if w is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]
    rad = [math.hypot(v.co.x, v.co.y) for v in loop_verts]
    r_cut = sum(rad) / len(rad)
    # fan cap; UV rim = polar angle of each boundary vertex at r = 1 (texture units), so the painted peel ring lands
    # exactly on the scanned outline
    centre = bm.verts.new((0.0, 0.0, 0.0))
    uv = bm.loops.layers.uv.verify()
    cap_faces = []
    n = len(loop_verts)
    # orient: for the kept lower half the cap must face +z
    area = sum(loop_verts[i].co.x * loop_verts[(i + 1) % n].co.y - loop_verts[(i + 1) % n].co.x * loop_verts[i].co.y
               for i in range(n))
    order = loop_verts if (area > 0) == (keep == "below") else loop_verts[::-1]
    for i in range(n):
        v0, v1 = order[i], order[(i + 1) % n]
        f = bm.faces.new((centre, v0, v1))
        f.material_index = 1
        f.smooth = False
        cap_faces.append(f)
        for lp in f.loops:
            if lp.vert is centre:
                lp[uv].uv = (0.5, 0.5)
            else:
                ang = math.atan2(lp.vert.co.y, lp.vert.co.x)
                lp[uv].uv = (0.5 + 0.5 / TEX_R * math.cos(ang), 0.5 + 0.5 / TEX_R * math.sin(ang))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    nb = sum(1 for e in bm.edges if e.is_boundary)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    if keep != "below":                                       # flip so the cut faces +z and the dome hangs below
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 3, "X"))
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob, r_cut, {"boundary_before": nb0, "boundary_after": nb, "non_manifold": nm, "cut_verts": n,
                       "scale": round(s, 3)}


def flesh_mat(name, img, rough_img, sss_radius, sss_scale, ior=1.36):
    m = D.principled(name, base="white", rough=0.2, sss=1.0, sss_radius=sss_radius, sss_scale=sss_scale,
                     ior=ior, coat=envf("TFS_COAT", 0.0), coat_rough=0.08, spec=envf("TFS_SPEC", 0.35))
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    p = n["Principled BSDF"]
    p.subsurface_method = "RANDOM_WALK"
    tc = n.new("ShaderNodeTexCoord")
    t = n.new("ShaderNodeTexImage")
    t.image = img
    t.interpolation = "Cubic"
    t.extension = "EXTEND"
    l.new(tc.outputs["UV"], t.inputs["Vector"])
    l.new(t.outputs["Color"], p.inputs["Base Color"])
    tr = n.new("ShaderNodeTexImage")
    tr.image = rough_img
    tr.extension = "EXTEND"
    l.new(tc.outputs["UV"], tr.inputs["Vector"])
    l.new(tr.outputs["Color"], p.inputs["Roughness"])
    # pulpy relief from the painted cells/seeds (luminance as height)
    bw = n.new("ShaderNodeRGBToBW")
    l.new(t.outputs["Color"], bw.inputs["Color"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = envf("TFS_BUMP", 0.25)
    bump.inputs["Distance"].default_value = 0.002
    l.new(bw.outputs["Val"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def peel_tweak(ob, sss, radius, scale, sheen=0.0, coat=0.0):
    """Keep the scan's own peel material (textures from the glTF) and add a touch of SSS / sheen / coat."""
    m = ob.data.materials[0]
    p = m.node_tree.nodes.get("Principled BSDF")
    D._set(p, sss=sss, sss_radius=radius, sss_scale=scale, sheen=sheen, sheen_rough=0.4, coat=coat, coat_rough=0.2)
    p.subsurface_method = "RANDOM_WALK"
    return m


kiwi_rgb, kiwi_rough, _ = kiwi_section()
lime_rgb, lime_rough, _ = lime_section()
kiwi, KR, KINFO = load_half("food_kiwi_01/food_kiwi_01_2k.gltf", "KiwiHalf", 0.27, keep="below")
lime, LR, LINFO = load_half("food_lime_01/food_lime_01_2k.gltf", "LimeHalf", 0.25, keep="above")
SSS_K = envf("TFS_SSS_K", 0.045)
SSS_L = envf("TFS_SSS_L", 0.05)
kiwi.data.materials.append(flesh_mat("kiwi_flesh", np_image("kiwi_section", kiwi_rgb),
                                     np_data_image("kiwi_rough", kiwi_rough), (0.55, 1.0, 0.28), SSS_K))
lime.data.materials.append(flesh_mat("lime_flesh", np_image("lime_section", lime_rgb),
                                     np_data_image("lime_rough", lime_rough), (0.9, 1.0, 0.35), SSS_L))
peel_tweak(kiwi, 0.08, (0.6, 0.8, 0.3), 0.008, sheen=0.5)
peel_tweak(lime, 0.5, (0.6, 1.0, 0.3), 0.02, coat=0.3)
for o in (kiwi, lime):
    D.set_smooth(o)
    for poly in o.data.polygons:                               # flat cap (no smoothing across the cut edge)
        if poly.material_index == 1:
            poly.use_smooth = False

# ----------------------------------------------------------------------------------------------------------------
# set: blush-coral cove, candy plate, the two halves (cut faces to camera)
# ----------------------------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=10.0, height=6.0, radius=1.4, wall_y=2.2,
                   mat=D.mat_clay(BG_HEX, name="cove_blush_coral", rough=0.7, sss=0.0, sheen=0.1))
turn = D.empty("Turn", (0, 0, 0), size=0.3)
R_PLATE = envf("TFS_PLATE_R", 0.20)
plate = D.cylinder("Plate", R_PLATE, 0.03, (0, 0, 0), mat=D.mat_candy("white", name="candy_white_plate", rough=0.25),
                   bevel=0.012, base_at_zero=True)
plate.parent = turn
rim = D.torus("PlateRim", R_PLATE, 0.0135, (0, 0, 0.029), mat=D.mat_candy("mint", name="candy_mint_rim"),
              major_seg=128, minor_seg=24)
rim.parent = turn
PLATE_TOP = 0.03

# each half: cut face toward -Y (camera), tilted back so the face looks slightly up at the camera
TILT = math.radians(envf("TFS_TILT", 18.0))


def stand(ob, xy, yaw_deg, r_dome):
    """Rotate the half so its cut face (local +z) faces -Y tilted back by TILT, then rest its lowest point on the
    plate.  Parent to the turntable."""
    rot = Matrix.Rotation(math.radians(yaw_deg), 4, "Z") @ Matrix.Rotation(math.pi / 2 - TILT, 4, "X")
    ob.matrix_world = rot
    bpy.context.view_layer.update()
    zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
    ob.matrix_world = Matrix.Translation((xy[0], xy[1], PLATE_TOP - min(zs) - 0.004)) @ rot
    ob.parent = turn
    return ob


stand(kiwi, (-0.072, -0.045), envf("TFS_YAW_K", 12.0), KR)
stand(lime, (0.098, 0.07), envf("TFS_YAW_L", -10.0), LR)

# ----------------------------------------------------------------------------------------------------------------
# light: the backlight (the effect), soft front fill, rim, gentle world
# ----------------------------------------------------------------------------------------------------------------
TGT = V((0.0, 0.0, 0.16))
BACK = D.light("AREA", "BackLight", (0.15, 0.95, 0.42), (0.0, 0.0, 0.14), envf("TFS_BACK", 600.0), "#FFF2D6",
               size=0.55)
BACK.data.spread = math.radians(envf("TFS_BACK_SPREAD", 70.0))     # aim the glow at the fruit, not the floor
if ENV("TFS_BACK_LINK", "1") == "1":
    # light linking (as S03's gummy glow): the backlight lights only the fruit and the plate, so the cove floor
    # behind them keeps its coral instead of bleaching to a white band; the SSS path itself is unchanged
    _rc = bpy.data.collections.new("BackLightReceivers")
    for _o in (kiwi, lime, plate, rim):
        _rc.objects.link(_o)
    BACK.light_linking.receiver_collection = _rc
D.light("AREA", "Fill", (-1.4, -2.0, 1.4), tuple(TGT), envf("TFS_FILL", 14.0), "#FFE8EE", size=2.2)
D.light("AREA", "Rim", (1.3, 0.8, 1.2), tuple(TGT), envf("TFS_RIM", 60.0), "#FFFFFF", size=0.8)
if ENV("TFS_HALO", "1") == "1":
    # backlit halo on the cove behind the fruit: a soft spot (blend 1) makes a radial warm glow the glowing faces read
    # against; a dim flat wash keeps the corners coral (no grey)
    D.light("SPOT", "Halo", (0.0, 0.25, 1.7), (0.05, 2.0, 0.42), envf("TFS_HALO_W", 420.0), "#FFE6D6", radius=0.35,
            spot_deg=envf("TFS_HALO_DEG", 46.0), blend=1.0)
    D.light("AREA", "WallWash", (0.0, 0.6, 2.4), (0.0, 2.2, 0.8), envf("TFS_WALL", 45.0), "#FFF6EE", size=2.5)
else:
    D.light("AREA", "WallWash", (0.0, 0.6, 2.4), (0.0, 2.2, 0.8), envf("TFS_WALL", 80.0), "#FFF6EE", size=2.5)
D.world_hdri(os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr"), envf("TFS_WORLD", 0.25), rot_z=-40.0,
             camera_bg=BG_HEX)

# ----------------------------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------------------------
ELEV = math.radians(envf("TFS_ELEV", 14.0))
DIST = envf("TFS_DIST", 1.0)
CAM = TGT + V((0.0, -math.cos(ELEV), math.sin(ELEV))) * DIST
cam, cam_tgt = D.camera("Cam", tuple(CAM), tuple(TGT + V((0, 0, envf("TFS_AIMDZ", -0.05)))), lens=50.0, fstop=4.0)
cam.data.dof.focus_object = None
cam.data.dof.focus_distance = (CAM - TGT).length - 0.05


# ----------------------------------------------------------------------------------------------------------------
# motion: slow sway of the plate, sinusoidal (seamless by construction)
# ----------------------------------------------------------------------------------------------------------------
SWAY = math.radians(envf("TFS_SWAY", 24.0))


def sway(f):
    """Wrapped phase: the keys at f and f+LOOP are exactly equal (seamless loop, bit-identical inputs)."""
    return SWAY * math.sin(2 * math.pi * ((f - 1) % LOOP) / LOOP)


D.bake(turn, "rotation_euler", BAKE0, BAKE1, lambda f: (0.0, 0.0, sway(f)))


# ----------------------------------------------------------------------------------------------------------------
# hex framing metrics + meta
# ----------------------------------------------------------------------------------------------------------------
def hex_scale_of(px, py):
    cx, cy, R = RES[0] / 2, RES[1] / 2, RES[0] / 2
    dx, dy = abs(px - cx), abs(py - cy)
    return max(dy / (R * math.sqrt(3) / 2), (dx + dy / math.sqrt(3)) / R)


def frame_metrics(objs, f, stride=3):
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


HERO = [kiwi, lime, plate, rim]
METRICS = {f: frame_metrics(HERO, f) for f in (1, 1 + LOOP // 4, 1 + LOOP // 2, 1 + 3 * LOOP // 4)}
METRICS_FRUIT = {f: frame_metrics([kiwi, lime], f) for f in (1, 1 + LOOP // 4)}
sc.frame_set(1)
FINAL_SPP, FINAL_THR = int(envf("TFS_FSPP", 96)), 0.02
MEASURED_S_PER_F = 1.77      # final mode 96 spp, steady state (frames 2..n of one process)
FINAL_COST = {                  # T2 finishing pass, 2026-11-20, one process, GPU 7 (NVIDIA H200) not shared
    "gpu": "H200 (GPU 7), exclusive during the run (nvidia-smi compute-apps: only this process)",
    "measured_frames": [1, 46, 91, 136], "frame_times_s": [2.9, 1.7, 1.8, 1.8], "process_wall_s": 14.83,
    "overhead_per_process_s": 7.76, "chunk_frames": 90, "processes": 2,
    "est_gpu_h": 0.0928, "cap_gpu_h": 0.12}
meta = {
    "id": SHOT, "frames": LOOP, "loop": LOOP, "res": list(RES), "fps": 30,
    "bg": {"name": BG_NAME, "albedo_hex": BG_HEX},
    "hero": "kiwi half + lime half (scans, bisected; procedural cross-sections) on a white candy plate",
    "phenomenon": "subsurface scattering: backlit fruit flesh glows through the cut faces",
    "palette": ["blush-coral pastel", "kiwi green", "lime yellow-green", "white", "mint"],
    "motion": f"plate sways +-{math.degrees(SWAY):.0f} deg, sinusoidal, one period per loop",
    "final_samples": FINAL_SPP, "final_threshold": FINAL_THR,
    "measured_final_s_per_f": MEASURED_S_PER_F,
    "final_cost": FINAL_COST,
    "mesh_build": {"kiwi": KINFO, "lime": LINFO, "kiwi_cut_r_m": round(KR, 4), "lime_cut_r_m": round(LR, 4)},
    "hero_metrics": {str(k): v for k, v in METRICS.items()},
    "fruit_metrics": {str(k): v for k, v in METRICS_FRUIT.items()},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"[{SHOT}] mesh", json.dumps(meta["mesh_build"]))
print(f"[{SHOT}] metrics", json.dumps(METRICS))
print(f"[{SHOT}] fruit", json.dumps(METRICS_FRUIT))

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=LOOP, shot_name=SHOT)
