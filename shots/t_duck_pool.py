"""t_duck_pool -- hex-tile mini scene (group T3 "motion & world", docs/storyboard_v2.md section 5).

Hero / effect
-------------
The Poly Haven rubber duck (re-hued to a classic lemon duck with an orange beak) bobs and rocks in a round candy
paddling pool.  The water surface is a real refracting mesh rippled by a Geometry Nodes deformer (a few travelling
waves + rings spreading from the bobbing duck), and the sun light focused by those ripples paints a dancing caustic
network on the white / aqua tiles of the pool floor.  The caustics are path-traced through the moving surface
(shadow caustics, Cycles manifold next-event estimation: light = caustic light, water = caster, tiles = receiver),
so they change shape with every ripple and refract again on their way to the camera.

Contract (storyboard_v2 section 5): 1152 x 998 final (preview 576 x 499), flat-top hexagon inscribed in the frame;
seamless loop of LOOP frames (frame LOOP + 1 == frame 1): every wave and every duck motion has a whole number of
cycles per loop, and the clock that drives them is baked per frame with D.bake; static seed; PBR Neutral, exposure
-0.2.  Meta: renders/meta/t_duck_pool.json.

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_duck_pool.py -- --mode preview
Test hooks (env, all default off): TD_CAUSTICS=mnee|brute|off, TD_CAM, TD_TGT, TD_LENS, TD_SUN, TD_SUN_POS,
TD_WORLD, TD_AMP (wave amplitude scale), TD_EXPO.  Finals must run with none of them set.
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
SHOT = "t_duck_pool"
LOOP = int(os.environ.get("TD_LOOP", "90"))   # seamless loop (frames)
N = LOOP
RES = (1152, 998)
BG = "cream"
FINAL_SPP, FINAL_THR = 80, 0.02
MEASURED_FINAL_SPF = 3.5       # steady-state final s/frame, H200 GPU 6 idle (nvidia-smi 0 % before the run)
COST = {"first_frame_s": 4.8, "gpu_h_est": 0.089,
        "measured": "2026-11-20, --mode final f1,30,31,61,89 in one process: 4.8 / 3.6 / 3.5 / 3.5 / 3.5 s, process wall 21 s; gpu_h = (first + 89 x s/f + 3 s scene build) / 3600"}
ENV = os.environ.get
args = D.parse_args()


def envf(name, default):
    return float(ENV(name, default))


def envv(name, default):
    return V(tuple(float(v) for v in ENV(name, default).split(",")))


EXPOSURE = envf("TD_EXPO", -0.2)
CAUSTICS = ENV("TD_CAUSTICS", "mnee")

D.reset_scene()
sc = bpy.context.scene
# refractive caustics stay ON in every mode: MNEE (shadow caustics) needs them -- with caustics filtered, Cycles
# strips the water's refraction closure after the diffuse bounce and the manifold walk finds nothing (verified on
# a glass-ball test: black shadow without, smooth caustic with).  They also let the big sky / fill light reach the
# tiles through the water by plain path tracing.
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=32, diffuse=int(envf("TD_DIFF", 4)),
               glossy=int(envf("TD_GLOSSY", 6)), transmission=int(envf("TD_TRANS", 12)), volume=2,
               caustics=(CAUSTICS != "off"), clamp_indirect=30.0, motion_blur=ENV("TD_MBLUR", "0") == "1",
               shutter=0.5)
# motion blur OFF (deviation from the house default): every motion here is < 4 mm per frame (duck bob 1.3 mm/f,
# ripple phase speed <= 3.3 mm/f), so blur is invisible, and deformation blur of the 100k-vertex water costs ~10%.
D.setup_color(exposure=EXPOSURE)
D.setup_output(res=RES)
sc.frame_start, sc.frame_end = 1, N
BAKE0, BAKE1 = -2, N + 3
FPS = 30.0
T_LOOP = LOOP / FPS                    # seconds


def clock(f):
    """Seconds, wrapped to the loop so every baked value at f and f + LOOP is identical."""
    return ((f - 1) % LOOP) / FPS


# ----------------------------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------------------------
POOL_R = 0.80            # ring (torus) centre-line radius
TUBE_R = 0.11            # ring tube radius
RINGS = [(0.11, ENV("TD_RING_LO", "lilac")), (0.31, ENV("TD_RING_HI", "pink"))]   # stacked inflatable rings
FLOOR_Z = 0.03           # top of the tiled pool floor
WATER_Z = 0.36           # still-water level: 0.33 m deep, so gentle ripples (slope ~0.1) focus on the tiles
AMP = envf("TD_AMP", 1.0)

# waves: (wavelength m, direction deg, amplitude m, cycles per loop).  Every temporal frequency is a whole number
# of cycles per loop -> seamless.  The short ripples are sized to FOCUS on the tiles: a sine of amplitude A and
# wavenumber k is a lens of focal length 1 / ((n - 1) A k^2); with A = 1 / ((n - 1) f k^2) and f ~ 0.30-0.36 m (the
# water is 0.33 m deep) their crests draw bright caustic lines just at the floor, and their sum a moving network.
# Deep water is what keeps the surface calm: the slope at focus is 1 / ((n - 1) f k), ~0.10-0.15 here, so the
# tiles stay readable through the surface (a 12 cm deep pool needed slopes of 0.2-0.3 and hid the net).
# One long, gentle swell moves the whole pattern.  Phase speeds 0.06-0.10 m/s: slow, readable, no strobing.
def _focus_amp(lam, f):
    k = 2 * math.pi / lam
    return 1.0 / (0.333 * f * k * k)


FOCUS = envf("TD_FOCUS", 0.32)
WAVES = [(0.070, 15.0, _focus_amp(0.070, FOCUS), 3), (0.082, 82.0, _focus_amp(0.082, FOCUS), 3),
         (0.094, 147.0, _focus_amp(0.094, FOCUS * 1.05), 2), (0.108, 213.0, _focus_amp(0.108, FOCUS * 1.1), 2),
         (0.076, 280.0, _focus_amp(0.076, FOCUS), 3), (0.30, 330.0, 0.0030, 1)]
RING = (0.064, 0.0016, 4)          # duck rings: wavelength, amplitude at the duck, cycles per loop


def wave_height(x, y, t):
    h = 0.0
    for lam, ang, a, n in WAVES:
        k = 2 * math.pi / lam
        w = 2 * math.pi * n / T_LOOP
        d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        h += a * AMP * math.sin(k * (d[0] * x + d[1] * y) - w * t)
    return h


def water_mesh(radius, z_top, z_bot, step):
    """Closed water body: a fine disc grid on top (rippled by the GN deformer), a side wall and a bottom, so the
    surface has an inside for the refraction.  The wall and the bottom hide inside the rim tube / below the tiles."""
    bm = bmesh.new()
    n = int(2 * radius / step) + 1
    grid = {}
    for i in range(n):
        for j in range(n):
            x, y = -radius + i * step, -radius + j * step
            if x * x + y * y <= radius * radius:
                grid[i, j] = bm.verts.new((x, y, z_top))
    for (i, j), v in list(grid.items()):
        q = [grid.get(c) for c in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
        if all(q):
            bm.faces.new(q)
    # boundary loop of the top grid -> wall down to z_bot -> bottom cap
    bm.edges.ensure_lookup_table()
    edges = [e for e in bm.edges if e.is_boundary]
    res = bmesh.ops.extrude_edge_only(bm, edges=edges)
    new_verts = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    for v in new_verts:
        v.co.z = z_bot
    bm.edges.ensure_lookup_table()
    bottom = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=bottom, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Water")
    bm.to_mesh(me)
    bm.free()
    ob = D.link(bpy.data.objects.new("Water", me))
    D.set_smooth(ob)
    return ob


def ripple_deformer():
    """GN: z += sum of travelling waves + duck rings, only on the top sheet (z > WATER_Z - 1 cm); the waves fade
    to zero toward the rim so the surface meets the wall cleanly."""
    ng = bpy.data.node_groups.new("Ripples", "GeometryNodeTree")
    it = ng.interface
    it.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    it.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    socks = {}
    for nm, dv in (("Time", 0.0), ("DuckX", 0.0), ("DuckY", 0.0), ("RingAmp", RING[1])):
        s = it.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = dv
        socks[nm] = s
    n, l = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    pos = n.new("GeometryNodeInputPosition")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(pos.outputs[0], sep.inputs[0])

    def m(op, a, b=None, c=None):
        nd = n.new("ShaderNodeMath")
        nd.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                l.new(v, nd.inputs[i])
        return nd.outputs[0]

    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    T = gi.outputs["Time"]
    total = None
    for lam, ang, a, cyc in WAVES:
        k = 2 * math.pi / lam
        w = 2 * math.pi * cyc / T_LOOP
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ph = m("SUBTRACT", m("MULTIPLY_ADD", X, k * dx, m("MULTIPLY", Y, k * dy)), m("MULTIPLY", T, w))
        term = m("MULTIPLY", m("SINE", ph), a * AMP)
        total = term if total is None else m("ADD", total, term)
    # rings around the duck: A(r) sin(k r - w t), amplitude falls off ~1/sqrt(r) and fades in near the hull
    rx = m("SUBTRACT", X, gi.outputs["DuckX"])
    ry = m("SUBTRACT", Y, gi.outputs["DuckY"])
    r = m("SQRT", m("MULTIPLY_ADD", rx, rx, m("MULTIPLY", ry, ry)))
    k_r, w_r = 2 * math.pi / RING[0], 2 * math.pi * RING[2] / T_LOOP
    ring = m("SINE", m("SUBTRACT", m("MULTIPLY", r, k_r), m("MULTIPLY", T, w_r)))
    env = m("DIVIDE", 0.14, m("MAXIMUM", r, 0.14))                       # 1 inside 14 cm, then ~0.14/r (spreading)
    fin = m("MINIMUM", m("MAXIMUM", m("DIVIDE", m("SUBTRACT", r, 0.10), 0.08), 0.0), 1.0)
    fin = m("MULTIPLY", m("MULTIPLY", fin, fin), m("SUBTRACT", 3.0, m("MULTIPLY", fin, 2.0)))   # smoothstep at the hull
    total = m("ADD", total, m("MULTIPLY", m("MULTIPLY", ring, m("MULTIPLY", env, fin)), gi.outputs["RingAmp"]))
    # fade toward the rim (r_world > POOL_R - 0.10) and only the top sheet moves
    rw = m("SQRT", m("MULTIPLY_ADD", X, X, m("MULTIPLY", Y, Y)))
    fade = m("SUBTRACT", 1.0, m("MINIMUM", m("MAXIMUM", m("DIVIDE", m("SUBTRACT", rw, POOL_R - 0.20), 0.12), 0.0),
                                    1.0))
    top = m("GREATER_THAN", Z, WATER_Z - 0.01)
    dz = m("MULTIPLY", m("MULTIPLY", total, fade), top)
    off = n.new("ShaderNodeCombineXYZ")
    l.new(dz, off.inputs[2])
    sp = n.new("GeometryNodeSetPosition")
    l.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    l.new(off.outputs[0], sp.inputs["Offset"])
    l.new(sp.outputs[0], go.inputs["Geometry"])
    return ng, {k: v.identifier for k, v in socks.items()}


# ----------------------------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------------------------
def tile_mat():
    """Procedural pool mosaic: square tiles (white / pale aqua, randomly mixed by the brick node) with deeper aqua
    grout, a soft glaze, and a grout bump so the floor reads tactile.  Light, so the caustics read."""
    m = D.mat_candy("white", name="pool_tiles", rough=0.30, coat=0.35, coat_rough=0.10, sss=0.0)
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    p = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    br = n.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = float(ENV("TD_TILE", "0.12"))
    br.inputs["Row Height"].default_value = float(ENV("TD_TILE", "0.12"))
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Mortar Smooth"].default_value = 0.35
    br.inputs["Bias"].default_value = 0.2
    br.inputs["Color1"].default_value = D.col(ENV("TD_TILE1", "#F0FFFD"))
    br.inputs["Color2"].default_value = D.col(ENV("TD_TILE2", "#B2F0EE"))
    br.inputs["Mortar"].default_value = D.col(ENV("TD_GROUT", "#5CCFD2"))
    l.new(tc.outputs["Object"], br.inputs["Vector"])
    l.new(br.outputs["Color"], p.inputs["Base Color"])
    # ambient lift: the floor between the caustic lines would otherwise drop to navy (MNEE is approximate and the
    # sky reaches the tiles only through the water); a faint self-glow of the tile albedo stands in for pool
    # skylight.  emission_sampling NONE: it lights nothing else and adds no noise.
    l.new(br.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = float(ENV("TD_TILE_EMIT", "0.22"))
    m.cycles.emission_sampling = "NONE"
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    l.new(br.outputs["Fac"], inv.inputs[1])
    l.new(inv.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def water_mat():
    """Clear pool water: IOR 1.333, perfectly smooth (MNEE needs it), a faint aqua surface tint (applied at both
    crossings -> colour^0.5) and a light aqua Beer-Lambert volume so deeper water reads aqua."""
    m = D.mat_glass("aqua", name="pool_water", rough=0.0, ior=1.333, absorb=envf("TD_WATER_ABS", 0.7),
                    absorb_color=ENV("TD_WATER_COL", "#62EEDF"))
    p = m.node_tree.nodes["Principled BSDF"]
    c = D.col("#C9F6FB")
    p.inputs["Base Color"].default_value = (c[0] ** 0.5, c[1] ** 0.5, c[2] ** 0.5, 1.0)
    return m


def huesat(mat, hue=0.5, sat=1.0, val=1.0):
    nt = mat.node_tree
    p = nt.nodes["Principled BSDF"]
    lk = [k for k in nt.links if k.to_socket == p.inputs["Base Color"]][0]
    src = lk.from_socket
    nt.links.remove(lk)
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Hue"].default_value = hue
    hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = val
    nt.links.new(src, hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], p.inputs["Base Color"])
    return hs


# ----------------------------------------------------------------------------------------------
# set: cream ground, inflatable candy rim, tiled floor, water, duck
# ----------------------------------------------------------------------------------------------
ground = D.cylinder("Ground", 6.0, 0.1, (0, 0, -0.05), mat=D.mat_clay("cream", name="ground_cream", rough=0.6,
                                                                       sss=0.0, sheen=0.05), bevel=0.0)
pool_floor = D.cylinder("PoolFloor", POOL_R + 0.02, FLOOR_Z, (0, 0, 0), mat=tile_mat(), bevel=0.0,
                        base_at_zero=True)
rings = []
for i, (zc, colr) in enumerate(RINGS):
    rm = D.mat_candy(colr, name=f"ring_{colr}", rough=0.25, coat=1.0, coat_rough=0.06)
    rings.append(D.torus(f"Ring{i}", POOL_R, TUBE_R, (0, 0, zc), mat=rm, major_seg=160, minor_seg=48))
water = water_mesh(POOL_R, WATER_Z, FLOOR_Z - 0.01, envf("TD_GRID", 0.004))
D.assign(water, water_mat())
RIP, RSOCK = ripple_deformer()
rmod = water.modifiers.new("Ripples", "NODES")
rmod.node_group = RIP

duck_root, duck_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "rubber_duck_toy",
                                                    "rubber_duck_toy_4k.gltf"))
duck = duck_meshes[0]
dm = duck.data.materials[0].copy()
dm.name = "duck_lemon"
huesat(dm, hue=float(ENV("TD_DUCK_HUE", "0.545")), sat=1.0, val=1.12)
_dp = dm.node_tree.nodes["Principled BSDF"]
_dp.inputs["Coat Weight"].default_value = 0.5          # glossy vinyl
_dp.inputs["Coat Roughness"].default_value = 0.12
duck.data.materials[0] = dm
DUCK_S = envf("TD_DUCK_S", 1.6)
DUCK_SINK = 0.035 * DUCK_S          # waterline above the duck's base
DUCK_YAW = envf("TD_DUCK_YAW", -50.0)


def duck_pose(f):
    t = clock(f)
    w1 = 2 * math.pi / T_LOOP          # one cycle per loop
    bob = 0.006 * math.sin(3 * w1 * t) + 0.002 * math.sin(2 * w1 * t + 1.1)
    pitch = 3.5 * math.sin(2 * w1 * t + 0.6) + 1.2 * math.sin(3 * w1 * t + 2.0)
    roll = 3.0 * math.sin(3 * w1 * t + 1.9)
    yaw = DUCK_YAW + 9.0 * math.sin(w1 * t)
    drift = (0.025 * math.sin(w1 * t + 0.4), 0.018 * math.sin(2 * w1 * t))
    return (drift[0], drift[1], WATER_Z - DUCK_SINK + bob), (math.radians(roll), math.radians(pitch), math.radians(yaw))


duck_root.scale = (DUCK_S, DUCK_S, DUCK_S)
D.bake(duck_root, "location", BAKE0, BAKE1, lambda f: duck_pose(f)[0])
D.bake(duck_root, "rotation_euler", BAKE0, BAKE1, lambda f: duck_pose(f)[1])
D.bake(rmod, f'["{RSOCK["DuckX"]}"]', BAKE0, BAKE1, lambda f: duck_pose(f)[0][0])
D.bake(rmod, f'["{RSOCK["DuckY"]}"]', BAKE0, BAKE1, lambda f: duck_pose(f)[0][1])
# the wave clock is baked unwrapped (continuous through the seam, so motion blur at f LOOP / LOOP+1 is right):
# every wave and the rings have whole cycles per loop, so t and t + T_LOOP give the same surface.
D.bake(rmod, f'["{RSOCK["Time"]}"]', BAKE0, BAKE1, lambda f: (f - 1) / FPS)

# ----------------------------------------------------------------------------------------------
# light: one small high sun (the caustic light), a soft sky fill, candy sky reflections
# ----------------------------------------------------------------------------------------------
SUN_W = envf("TD_SUN", 1100.0)
SUN_POS = envv("TD_SUN_POS", "-1.2,1.3,3.8")
sun = D.light("POINT", "Sun", tuple(SUN_POS), None, power=SUN_W, color="#FFF4E0", radius=0.03)
if CAUSTICS == "mnee":
    sun.data.cycles.is_caustics_light = True
    water.cycles.is_caustics_caster = True
    pool_floor.cycles.is_caustics_receiver = True
# the fill lights the ground, the rings and the duck but NOT the pool (light linking): under water the tiles get
# the key's caustics plus only a soft sky base, so the caustic net keeps its contrast (with the fill on the tiles
# it washed out to a faint mottle); the fill's cool tint keeps the ground shadows lavender, not grey (G2)
fill = D.light("AREA", "Fill", (1.8, -2.6, 2.6), (0, 0, 0.1), power=envf("TD_FILL", 170.0), color="#E6EEFF", size=3.0)
fill.visible_glossy = False
fill_rx = bpy.data.collections.new("FillExclude")
for o in (pool_floor, water):
    fill_rx.objects.link(o)
fill.light_linking.receiver_collection = fill_rx
for co in fill_rx.collection_objects:
    co.light_linking.link_state = "EXCLUDE"
sky = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
rig = D.world_hdri(sky, envf("TD_WORLD", 0.2), camera_bg=BG)

# camera: looking down into the pool, 3/4 on the duck
CAM = envv("TD_CAM", "0.0,-2.45,3.05")
TGT = envv("TD_TGT", "0.0,-0.06,0.18")
cam, cam_t = D.camera("Cam", tuple(CAM), tuple(TGT), lens=envf("TD_LENS", 50.0), fstop=8.0)
focus = D.empty("Focus", (0.0, 0.0, WATER_Z))
cam.data.dof.focus_object = focus

# ----------------------------------------------------------------------------------------------
# meta
# ----------------------------------------------------------------------------------------------
META_PATH = os.path.join(D.ROOT, "renders", "meta", SHOT + ".json")
meta = {
    "id": SHOT, "group": "T3", "frames": N, "loop": LOOP, "seamless": True, "fps": 30, "res": list(RES),
    "bg": BG, "bg_hex": D.PALETTE[BG],
    "hero": "lemon rubber duck (Poly Haven rubber_duck_toy) bobbing in a round pink inflatable paddling pool",
    "phenomenon": "refractive caustics through an animated water surface onto a tiled pool floor "
                  "(shadow caustics / MNEE), plus refraction of the floor through the ripples",
    "palette": ["cream", "aqua", "pink", "lemon"],
    "waves": [{"wavelength_m": w[0], "dir_deg": w[1], "amp_m": w[2] * AMP, "cycles_per_loop": w[3]} for w in WAVES],
    "rings": {"wavelength_m": RING[0], "amp_m": RING[1], "cycles_per_loop": RING[2]},
    "caustics": CAUSTICS,
    "final": dict({"samples": FINAL_SPP, "threshold": FINAL_THR, "s_per_frame_measured": MEASURED_FINAL_SPF},
                  **COST),
    "hex": {"shape": "flat-top", "inscribed": True, "circumradius_px": RES[0] / 2},
}
os.makedirs(os.path.dirname(META_PATH), exist_ok=True)
with open(META_PATH, "w") as fh:
    json.dump(meta, fh, indent=1)

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
