"""t_desk_lamp -- honeycomb mini-scene (T2 "light & material"): an architect lamp sweeps its light over a marble desk.

What the tile proves (storyboard_v2 section 5)
----------------------------------------------
A moving spot light with hard shadows.  The coral architect lamp (Poly Haven desk_lamp_arm_01) stands on a candy-white
marble desk in a mint room; its head nods and the lamp swivels a little on its base, so the warm spot pool glides in
a slow ellipse over three candy props (a book stack, an aqua mug, a lemon gumball).  Their crisp shadows swing,
stretch and shrink around them every frame, and the pool's soft edge and the lamp's own shadow move with it.
Mechanical, even motion only (no anticipation, no hop, no character acting -- brief: no desk-lamp character).

Build
-----
* The scan is one mesh: its C-clamp (every loose part below z = 7 mm) is dropped and the lamp stands on a round
  candy base; the head (shade, bulb, bracket and pin: loose parts with centroid y > 0.085, z > 0.55 in model space)
  becomes its own object pivoting on the head pin (model axis X through y 0.101, z 0.695); the bulb part is a separate
  glowing object that casts no shadow, with the SPOT light (r 12 mm) at its centre aimed down the shade axis
  (65 deg below the arm plane's horizontal, measured on a side view).  The paint gets a clear coat (candy).
* Light (pool contrast pass): the spot is the brightest light on the desk -- 140 W, blend 0.12 (a crisp pool rim), radius
  6 mm (hard shadows).  The soft key is light-linked to the lamp and the props only and the fill/world are low, so
  off the pool the desk sits a saturated teal-mint (~#5B9D89) and the pool is a warm cream (~#E6FBD9): the props'
  shadows inside the pool are holes of that teal (measured A/B in the T2 report; the earlier all-key look left the
  pool cream-on-pale-mint, V 0.97 vs 0.82, and filled the shadows in).
* Desk: a thick marble slab with procedural pastel veins (mint + pink on warm white; marble_01 is a beige limestone
  tile and would read tan), on a mint cove.

Tile contract: 1152 x 998 final, flat-top hexagon safe area, seamless LOOP-frame loop (frame LOOP+1 == frame 1), static
seed, PBR Neutral, exposure -0.2, baked closed-form motion (D.bake over f-2..LOOP+3).  Meta: renders/meta/<id>.json.

Run:  CUDA_VISIBLE_DEVICES=7 tools/blender/blender -b --factory-startup -P shots/t_desk_lamp.py -- --mode preview
Look-dev hooks (env, default off; finals run without them): TDL_SPOT, TDL_KEY, TDL_FILL, TDL_WORLD, TDL_NOD,
TDL_SWIVEL, TDL_DIST, TDL_ELEV, TDL_FSPP, TDL_EXPO, TDL_KEYLINK, TDL_SPOT_R, TDL_SPOT_BLEND.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

V = Vector
SHOT = "t_desk_lamp"
LOOP = 180
RES = (1152, 998)
ENV = os.environ.get


def envf(name, default):
    return float(ENV(name, str(default)))


args = D.parse_args()
D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=192, threshold=0.02, min_samples=32, diffuse=4, glossy=6, transmission=6, volume=2,
               caustics=False, filter_glossy=0.3, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("TDL_EXPO", -0.2))
D.setup_output(res=RES)
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.frame_start, sc.frame_end = 1, LOOP
BAKE0, BAKE1 = -2, LOOP + 3

BG_NAME, BG_HEX = "mint pastel", ENV("TDL_BG", "#A9EDD6")


# ----------------------------------------------------------------------------------------------------------------
# the lamp: split the scan into body / head / bulb, drop the clamp
# ----------------------------------------------------------------------------------------------------------------
def loose_parts(bm):
    bm.faces.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        parts.append(comp)
    return parts


HINGE = V((0.0, 0.101, 0.695))            # head pin (model space), axis = model X
SHADE_AXIS = V((0.0, math.cos(math.radians(65.0)), -math.sin(math.radians(65.0))))   # model space, at rest
CLAMP_ZMAX, HEAD_YC, HEAD_ZC = 0.007, 0.085, 0.55
SWIVEL_XY = V((0.0, -0.02))               # swivel column (model space)
LAMP_Z0 = 0.0036                          # lowest point of the lamp once the clamp is gone


def split_lamp():
    root, meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "desk_lamp_arm_01", "desk_lamp_arm_01_4k.gltf"))
    src = meshes[0]
    src.parent = None
    bpy.data.objects.remove(root)
    me = src.data
    paint = me.materials[0]
    bm = bmesh.new()
    bm.from_mesh(me)
    kinds = {}
    for comp in loose_parts(bm):
        vs = {v for g in comp for v in g.verts}
        zmax = max(v.co.z for v in vs)
        cy = sum(v.co.y for v in vs) / len(vs)
        cz = sum(v.co.z for v in vs) / len(vs)
        bulb = all(g.material_index == 1 for g in comp)
        k = "clamp" if zmax < CLAMP_ZMAX else ("bulb" if bulb else ("head" if (cy > HEAD_YC and cz > HEAD_ZC)
                                                                         else "body"))
        for g in comp:
            kinds[g.index] = k
    bm.free()
    out = {}
    for k in ("body", "head", "bulb"):
        m2 = me.copy()
        m2.name = f"lamp_{k}"
        b2 = bmesh.new()
        b2.from_mesh(m2)
        b2.faces.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if kinds[f.index] != k], context="FACES")
        b2.to_mesh(m2)
        b2.free()
        ob = D.link(bpy.data.objects.new(f"Lamp_{k}", m2))
        out[k] = ob
    bpy.data.objects.remove(src)
    # candy paint: keep the scan's textures, add a clear coat
    p = paint.node_tree.nodes.get("Principled BSDF")
    D._set(p, coat=0.6, coat_rough=0.06)
    glow = D.mat_emission("#FFF0CC", envf("TDL_BULB", 6.0), name="lamp_bulb_glow")
    glow.cycles.emission_sampling = "NONE"        # the SPOT does the lighting; the bulb is only seen
    D.assign(out["bulb"], glow)
    out["bulb"].visible_shadow = False
    return out, paint


LAMP, PAINT = split_lamp()

# rig (model space -> world): Swivel (base, vertical axis) -> Lamp body -> HeadPivot (hinge, model X) -> head, bulb
LAMP_BASE_XY = V((envf("TDL_LX", -0.36), envf("TDL_LY", 0.12)))
YAW0 = math.radians(envf("TDL_YAW", -125.0))      # model +Y (the reach) -> world direction at YAW0 + 90 deg
BASE_R, BASE_H = 0.078, 0.022
swivel = D.empty("Swivel", (LAMP_BASE_XY.x, LAMP_BASE_XY.y, BASE_H), size=0.15)
body_root = D.empty("LampModel", (0, 0, 0), size=0.1)
body_root.parent = swivel
body_root.location = (-SWIVEL_XY.x, -SWIVEL_XY.y, -LAMP_Z0)
LAMP["body"].parent = body_root
head_pivot = D.empty("HeadPivot", tuple(HINGE), size=0.05)
head_pivot.parent = body_root
for k in ("head", "bulb"):
    ob = LAMP[k]
    ob.data.transform(Matrix.Translation(-HINGE))
    ob.parent = head_pivot
    ob.location = (0, 0, 0)

# bulb centre (model space) -> spot light at the bulb, aimed down the shade axis, parented to the head
_bv = [v.co for v in LAMP["bulb"].data.vertices]
BULB_C = sum(_bv, V()) / len(_bv)                     # head-local (hinge at origin)
spot_ld = bpy.data.lights.new("LampSpot", "SPOT")
spot_ld.energy = envf("TDL_SPOT", 140.0)
spot_ld.color = D.col("#FFE9C8")[:3]
spot_ld.shadow_soft_size = envf("TDL_SPOT_R", 0.006)
spot_ld.spot_size = math.radians(envf("TDL_SPOT_DEG", 52.0))
spot_ld.spot_blend = envf("TDL_SPOT_BLEND", 0.12)
spot = D.link(bpy.data.objects.new("LampSpot", spot_ld))
spot.parent = head_pivot
spot.location = BULB_C + SHADE_AXIS * 0.012
spot.rotation_euler = SHADE_AXIS.to_track_quat("-Z", "Y").to_euler()

# round candy base (the clamp is gone) in the lamp's own coral-orange
base = D.cylinder("LampBase", BASE_R, BASE_H, (LAMP_BASE_XY.x, LAMP_BASE_XY.y, 0.0),
                  mat=D.mat_candy("#F2622A", name="candy_lamp_base", rough=0.25), bevel=0.009, base_at_zero=True)
foot = D.torus("LampFoot", BASE_R - 0.006, 0.006, (LAMP_BASE_XY.x, LAMP_BASE_XY.y, 0.004),
               mat=D.mat_rubber("white", name="rubber_foot"), major_seg=96, minor_seg=16)
swivel.rotation_euler = (0, 0, YAW0)

# ----------------------------------------------------------------------------------------------------------------
# set: mint cove, marble desk, candy props
# ----------------------------------------------------------------------------------------------------------------
DESK_H = 0.06
cove = D.cyclorama("Cove", width=14.0, depth=10.0, height=6.0, radius=0.15, wall_y=1.15,
                   mat=D.mat_clay(BG_HEX, name="cove_mint", rough=0.7, sss=0.0, sheen=0.1))
cove.location.z = -DESK_H


def mat_marble(name="desk_marble", base=ENV("TDL_MARBLE", "#C9F0E2"), vein1="#FFFFFF", vein2="#F4BCD3"):
    """Procedural candy marble (same recipe as t_material_balls): distorted diagonal wave troughs as veins, soft halo
    + crisp core -- here a pastel mint marble with white + rose veins, polished (coat).  White and rose marbles read
    teal-grey outside the pool under the mint wall's bounce (against G2); mint marble reads mint, and the warm pool
    turns it cream, so the pool edge is a hue change as well as a value change."""
    m = D.principled(name, base=base, rough=0.3, coat=0.6, coat_rough=0.06, sss=0.05,
                     sss_radius=(1.0, 0.9, 0.85), sss_scale=0.01)
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
    v1 = veins(0.38, (0.3, 0.2, 0.5), 5.0, 0.020)
    v1h = veins(0.38, (0.3, 0.2, 0.5), 5.0, 0.11)
    v2 = veins(0.8, (1.1, -0.4, 0.9), 8.0, 0.0075)
    halo = n.new("ShaderNodeMath"); halo.operation = "MULTIPLY"; halo.inputs[1].default_value = 0.15
    l.new(v1h, halo.inputs[0])
    vmax = n.new("ShaderNodeMath"); vmax.operation = "MAXIMUM"
    l.new(v1, vmax.inputs[0])
    l.new(halo.outputs[0], vmax.inputs[1])
    mx1 = n.new("ShaderNodeMix"); mx1.data_type = "RGBA"
    mx1.inputs["A"].default_value = D.col(base)
    mx1.inputs["B"].default_value = D.col(vein1)
    l.new(vmax.outputs[0], mx1.inputs["Factor"])
    mx2 = n.new("ShaderNodeMix"); mx2.data_type = "RGBA"
    l.new(mx1.outputs["Result"], mx2.inputs["A"])
    mx2.inputs["B"].default_value = D.col(vein2)
    l.new(v2, mx2.inputs["Factor"])
    l.new(mx2.outputs["Result"], p.inputs["Base Color"])
    return m


desk = D.rounded_box("Desk", (2.4, 1.62, DESK_H), 0.02, location=(0.0, 0.26, -DESK_H), mat=mat_marble(),
                     base_at_zero=True)                      # back edge at y 1.07: the wall rises right behind it

# props in the pool's path (world xy); each sits on the desk (z = 0)
books = []
for i, (sz, yaw, c, dz) in enumerate((((0.21, 0.15, 0.036), 14.0, "pink", 0.0),
                                       ((0.175, 0.125, 0.032), -7.0, "violet", 0.036))):
    b = D.rounded_box(f"Book{i}", sz, 0.008, location=(0.20, -0.06, dz), rotation=(0, 0, yaw),
                      mat=D.mat_candy(c, name=f"candy_book_{c}"), base_at_zero=True)
    books.append(b)
MUG_XY = (-0.01, -0.17)
mug = D.cylinder("Mug", 0.046, 0.10, (MUG_XY[0], MUG_XY[1], 0.0), mat=D.mat_candy("aqua", name="candy_mug_aqua"),
                 bevel=0.008, base_at_zero=True)
mug_in = D.cylinder("MugIn", 0.038, 0.09, (MUG_XY[0], MUG_XY[1], 0.012), mat=D.mat_candy("white",
                    name="candy_mug_in"), bevel=0.004, base_at_zero=True)
handle = D.torus("MugHandle", 0.028, 0.0085, (MUG_XY[0] - 0.048, MUG_XY[1], 0.05), rotation=(90, 0, 0),
                 mat=D.mat_candy("aqua", name="candy_mug_aqua_h"), major_seg=64, minor_seg=16)
gum = D.sphere("Gumball", 0.048, (0.15, -0.31, 0.048), D.mat_candy("lemon", name="candy_gum_lemon"), segments=64,
               rings=32)
PROPS = books + [mug, mug_in, handle, gum]

# ----------------------------------------------------------------------------------------------------------------
# light: soft ambient key + mint-tinted fill (low, so the warm spot pool reads), candy-sky reflections
# ----------------------------------------------------------------------------------------------------------------
TGT = V((envf("TDL_TX", -0.10), 0.02, 0.33))
key = D.light("AREA", "Key", (-1.6, -2.2, 2.6), (0.0, 0.1, 0.2), envf("TDL_KEY", 48.0), "#FFF6F0", size=2.4)
if ENV("TDL_KEYLINK", "1") == "1":
    # light-linked: the soft key models the lamp and the props but not the desk, so on the desk only the spot (plus
    # a dim fill, the world and the wall's bounce) lands: the pool is the brightest thing on the desk and the props'
    # spot shadows cut real holes in it instead of being filled in by the key
    _kc = bpy.data.collections.new("KeyReceivers")
    for _o in [LAMP["body"], LAMP["head"], base, foot] + PROPS:
        _kc.objects.link(_o)
    key.light_linking.receiver_collection = _kc
lamp_key = D.light("AREA", "LampKey", (-1.0, -1.3, 1.5), (-0.3, 0.1, 0.5), envf("TDL_LAMPKEY", 55.0), "#FFF8F2",
                   size=1.2)
_lc = bpy.data.collections.new("LampKeyReceivers")     # light-linked: keeps the coral paint vivid while the desk
for _o in (LAMP["body"], LAMP["head"], base, foot):     # ambient stays low enough for the spot pool to read
    _lc.objects.link(_o)
lamp_key.light_linking.receiver_collection = _lc
D.light("AREA", "Fill", (2.2, -1.8, 1.2), (0.0, 0.1, 0.3), envf("TDL_FILL", 9.0), "#DDF7EE", size=2.6)
wash = D.light("AREA", "WallWash", (0.0, -0.5, 2.6), (0.0, 1.2, 0.8), envf("TDL_WALL", 110.0), "#FFFFFF", size=2.5)
_wc = bpy.data.collections.new("WallWashReceivers")       # light-linked: keeps the mint wall bright without
_wc.objects.link(cove)                                    # flattening the desk, so the spot pool has headroom
wash.light_linking.receiver_collection = _wc
D.world_hdri(os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr"), envf("TDL_WORLD", 0.1), rot_z=60.0,
             camera_bg=BG_HEX)

# ----------------------------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------------------------
ELEV = math.radians(envf("TDL_ELEV", 17.0))
AZ = math.radians(envf("TDL_AZ", 20.0))      # orbit right: lamp near centre, props forward
DIST = envf("TDL_DIST", 2.1)
CAM = TGT + V((math.sin(AZ) * math.cos(ELEV), -math.cos(AZ) * math.cos(ELEV), math.sin(ELEV))) * DIST
cam, cam_tgt = D.camera("Cam", tuple(CAM), tuple(TGT), lens=50.0, fstop=8.0)
cam.data.dof.focus_object = None
cam.data.dof.focus_distance = (CAM - V((0.0, 0.05, 0.2))).length

# ----------------------------------------------------------------------------------------------------------------
# motion: head nod (about the pin) + gentle swivel, quarter-period apart -> the pool travels a slow ellipse.
# Wrapped phase: keys at f and f+LOOP are identical (seamless).
# ----------------------------------------------------------------------------------------------------------------
NOD = math.radians(envf("TDL_NOD", 11.0))
NOD0 = math.radians(envf("TDL_NOD0", 0.0))
SWIV = math.radians(envf("TDL_SWIVEL", 13.0))


def phase(f):
    return 2 * math.pi * ((f - 1) % LOOP) / LOOP


def nod(f):
    return NOD0 + NOD * math.sin(phase(f))


def swiv(f):
    return YAW0 + SWIV * math.cos(phase(f))


D.bake(head_pivot, "rotation_euler", BAKE0, BAKE1, lambda f: (nod(f), 0.0, 0.0))
D.bake(swivel, "rotation_euler", BAKE0, BAKE1, lambda f: (0.0, 0.0, swiv(f)))


# ----------------------------------------------------------------------------------------------------------------
# hex framing metrics, pool track + meta
# ----------------------------------------------------------------------------------------------------------------
def hex_scale_of(px, py):
    cx, cy, R = RES[0] / 2, RES[1] / 2, RES[0] / 2
    dx, dy = abs(px - cx), abs(py - cy)
    return max(dy / (R * math.sqrt(3) / 2), (dx + dy / math.sqrt(3)) / R)


def project(p):
    c = world_to_camera_view(sc, cam, p)
    return c.x * RES[0], (1.0 - c.y) * RES[1]


def frame_metrics(objs, f, stride=5):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys, hs = [], [], []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world.copy()
        for k in range(0, len(me.vertices), stride):
            px, py = project(mw @ me.vertices[k].co)
            xs.append(px)
            ys.append(py)
            hs.append(hex_scale_of(px, py))
        ev.to_mesh_clear()
    return {"bbox_px": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
            "height_frac": round((max(ys) - min(ys)) / RES[1], 3),
            "centre_px": [round((min(xs) + max(xs)) / 2), round((min(ys) + max(ys)) / 2)],
            "max_hex_scale": round(max(hs), 3)}


def pool_centre(f):
    """Where the spot axis meets the desk (z = 0), world + pixel."""
    sc.frame_set(f)
    mw = spot.matrix_world
    o = mw.translation
    d = (mw.to_3x3() @ V((0, 0, -1))).normalized()
    t = -o.z / d.z
    p = o + d * t
    px, py = project(p)
    return [round(p.x, 3), round(p.y, 3)], [round(px), round(py)], round(math.degrees(math.asin(-d.z)), 1)


HERO = [LAMP["body"], LAMP["head"], base]
METRICS = {f: frame_metrics(HERO, f) for f in (1, 1 + LOOP // 4, 1 + LOOP // 2, 1 + 3 * LOOP // 4)}
SCENE_METRICS = {f: frame_metrics(HERO + PROPS, f) for f in (1, 1 + LOOP // 2)}
POOL = {f: pool_centre(f) for f in range(1, LOOP + 1, LOOP // 12)}
sc.frame_set(1)
FINAL_SPP, FINAL_THR = int(envf("TDL_FSPP", 128)), 0.02
MEASURED_S_PER_F = 1.9      # final mode 128 spp, steady state (frames 2..n of one process)
FINAL_COST = {                  # T2 finishing pass, 2026-11-20, one process, GPU 7 (NVIDIA H200) not shared
    "gpu": "H200 (GPU 7), exclusive during the run (nvidia-smi compute-apps: only this process)",
    "measured_frames": [1, 46, 91, 136], "frame_times_s": [3.4, 1.9, 1.9, 1.9], "process_wall_s": 10.52,
    "overhead_per_process_s": 2.92, "chunk_frames": 90, "processes": 2,
    "est_gpu_h": 0.0966, "cap_gpu_h": 0.12}
meta = {
    "id": SHOT, "frames": LOOP, "loop": LOOP, "res": list(RES), "fps": 30,
    "bg": {"name": BG_NAME, "albedo_hex": BG_HEX},
    "hero": "coral architect desk lamp (desk_lamp_arm_01) on a round candy base",
    "phenomenon": "moving spot light: warm pool + hard shadows sweeping over candy props on a marble desk",
    "palette": ["mint pastel", "coral-orange", "white marble (mint/pink veins)", "pink", "violet", "aqua", "lemon"],
    "motion": f"head nod +-{math.degrees(NOD):.0f} deg (sin) + swivel +-{math.degrees(SWIV):.0f} deg (cos), one period "
              "per loop: the pool travels an ellipse",
    "final_samples": FINAL_SPP, "final_threshold": FINAL_THR,
    "measured_final_s_per_f": MEASURED_S_PER_F,
    "final_cost": FINAL_COST,
    "hero_metrics": {str(k): v for k, v in METRICS.items()},
    "scene_metrics": {str(k): v for k, v in SCENE_METRICS.items()},
    "pool_track": {str(k): {"world_xy": v[0], "px": v[1], "axis_elev_deg": v[2]} for k, v in POOL.items()},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"[{SHOT}] metrics", json.dumps(METRICS))
print(f"[{SHOT}] scene", json.dumps(SCENE_METRICS))
print(f"[{SHOT}] pool", json.dumps(POOL))

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=LOOP, shot_name=SHOT)
