"""t_lightbulb -- honeycomb mini-scene (T2 "light & material"): a glowing light bulb swinging on its cord.

What the tile proves (storyboard_v2 section 5)
----------------------------------------------
A moving point light seen through glass.  A clear bulb (Poly Haven lightbulb_01) hangs from a mint candy socket and
cord and swings like a pendulum; its coiled filament glows warm and is the only key light in the room.  The light
leaves through the thin glass envelope, washes the peach cove in a warm pool that slides with the swing, and the
three candy props on the floor throw hard shadows that swing the opposite way.  The glass shows its reflections and
the filament glows (the film's G1 orb bloom, driven only by the Emit pass, so nothing else blooms).

Build
-----
* lightbulb_01 is one mesh: the coil whose faces map into the model's emissive texture becomes the filament
  (emission, emission sampling off -- a POINT light of radius 6 mm at its centre does the lighting); the other base
  parts (screw, contacts, lead wires) keep the scan's metal; the envelope + stem (open single-surface shells) get a
  thin-glass shader (Fresnel mix of a warm transparent + sharp glossy), which is how a thin envelope behaves and lets
  the point light through without caustic noise; camera rays see the filament straight through it (so the filament
  lands in the Emit pass and blooms with the film's G1 parameters).
* An inner glow halo (the film's light-marker convention: camera/glossy-visible only, no lighting, no shadow) gives
  the hot bulb its soft core.
* Glass read (finishing pass): (1) Cycles' Fresnel node inverts the IOR on back faces, so the far side of the single
  shell went into total internal reflection beyond ~42 deg -> a broad olive ring and light blocked at oblique angles;
  the IOR input is now 1/1.5 on back faces (entering Fresnel on both sides).  (2) The truly clear envelope then
  vanished against the pale peach wall, so the transparent colour shifts to a thin coral edge tint at grazing angles
  (the longer path through the glass; candy glass) and an open white band around the glass, seen only by glossy rays,
  gives the white Fresnel rim of a product shot (the band has no caps, so the screw base keeps its chrome).
* Light balance (finishing pass): the bulb is the key (80 W point, r 6 mm) and lands a warm pool under itself; the
  soft fill is lavender (#C9B6FF, 32 W) so the hard shadows that swing with the bulb read tinted (G2), the top key,
  world and cove wash are low (4 W, 0.1, 32 W).
* Framing (finishing pass): camera 1.42 m (was 1.5) -> bulb + socket 0.557 of the frame height; cone and ball moved
  in (x -0.185 / +0.175, were -0.25 / +0.245) so they sit inside the 0.9 safe hexagon (scene max hex scale 0.92).
* Pendulum: L = 2.24 m, period 3.0 s = one 90-frame loop (T = 2 pi sqrt(L/g)), amplitude 4 deg, plus a slow 4 deg
  twist about the cord (same period) so the glass highlights roll.

Tile contract: 1152 x 998 final, flat-top hexagon safe area, seamless LOOP-frame loop (frame LOOP+1 == frame 1), static
seed, PBR Neutral, exposure -0.2, baked closed-form motion (D.bake over f-2..LOOP+3).  Meta: renders/meta/<id>.json.

Run:  CUDA_VISIBLE_DEVICES=7 tools/blender/blender -b --factory-startup -P shots/t_lightbulb.py -- --mode preview
Look-dev hooks (env, default off; finals run without them): TLB_BULB_W, TLB_FILL, TLB_KEY, TLB_WORLD, TLB_GLOW,
TLB_SWING, TLB_DIST, TLB_ELEV, TLB_FSPP, TLB_EXPO, TLB_FILL_HEX, TLB_SHELL, TLB_EDGE_HEX, TLB_FRES_FIX, TLB_GLOSSBG,
TLB_CONE_X, TLB_BALL_X.
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
SHOT = "t_lightbulb"
LOOP = 90
RES = (1152, 998)
ENV = os.environ.get


def envf(name, default):
    return float(ENV(name, str(default)))


args = D.parse_args()
D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=192, threshold=0.02, min_samples=32, diffuse=4, glossy=6, transmission=8, transparent=16,
               volume=2, caustics=False, filter_glossy=0.3, clamp_indirect=10.0, motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("TLB_EXPO", -0.2))
if ENV("TLB_NODN") == "1":                       # look-dev only
    sc.cycles.use_denoising = False
D.setup_output(res=RES)
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.frame_start, sc.frame_end = 1, LOOP
BAKE0, BAKE1 = -2, LOOP + 3

BG_NAME, BG_HEX = "peach pastel", ENV("TLB_BG", "#FFE2D2")
SCALE = 3.6                         # the scan is 0.1 m tall -> 0.36 m


# ----------------------------------------------------------------------------------------------------------------
# the bulb: split the scan into glass / filament / metal
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


def thin_glass(name="bulb_glass", tint="#FFFFFF"):
    """Thin envelope: Fresnel(IOR 1.5) mix of a warm-white Transparent BSDF and a sharp Glossy BSDF.  No refraction
    offset (the envelope is a single surface), transparent shadows let the filament's light out."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    tr = n.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = D.col(tint)            # (white: a warm tint read amber/olive)
    edge = ENV("TLB_EDGE_HEX", "#FF8F80")
    if edge != "none":
        # longer path through the glass at grazing angles: a thin coral edge tint (candy glass) outlines the clear
        # envelope against the pale peach wall; the face-on centre stays perfectly clear
        lw = n.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        pw = n.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = envf("TLB_EDGE_POW", 2.5)
        mxc = n.new("ShaderNodeMix")
        mxc.data_type = "RGBA"
        mxc.inputs["A"].default_value = D.col(tint)
        mxc.inputs["B"].default_value = D.col(edge)
        l.new(lw.outputs["Facing"], pw.inputs[0])
        l.new(pw.outputs[0], mxc.inputs["Factor"])
        l.new(mxc.outputs["Result"], tr.inputs["Color"])
    gl = n.new("ShaderNodeBsdfGlossy")
    gl.distribution = "GGX"
    gl.inputs["Roughness"].default_value = 0.03
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = n.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    # Cycles' Fresnel node inverts the IOR on back faces (glass -> air), which on a single-surface shell means total
    # internal reflection beyond ~42 deg on the far side of the envelope: a broad dark olive ring around the bulb and
    # light blocked at oblique angles.  Feed 1/1.5 on back faces so both sides use the entering (air -> glass) Fresnel.
    geo = n.new("ShaderNodeNewGeometry")
    eta = n.new("ShaderNodeMath")
    eta.operation = "MULTIPLY_ADD"
    eta.inputs[1].default_value = 1.0 / 1.5 - 1.5
    eta.inputs[2].default_value = 1.5
    l.new(geo.outputs["Backfacing"], eta.inputs[0])
    if ENV("TLB_FRES_FIX", "1") == "1":
        l.new(eta.outputs[0], fr.inputs["IOR"])
    mx = n.new("ShaderNodeMixShader")
    if ENV("TLB_GLASS") == "clear":                # look-dev only: no reflection at all
        fr.inputs["IOR"].default_value = 1.0
    l.new(fr.outputs[0], mx.inputs[0])
    l.new(tr.outputs[0], mx.inputs[1])
    l.new(gl.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], out.inputs["Surface"])
    return m


def split_bulb():
    root, meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "lightbulb_01", "lightbulb_01_2k.gltf"))
    src = meshes[0]
    src.parent = None
    bpy.data.objects.remove(root)
    me = src.data
    metal = me.materials[1]
    # emissive faces: their UVs land in the bright part of the model's emissive texture
    img = bpy.data.images.get("lightbulb_01_emissive")
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    uvl = me.uv_layers.active.data
    hot = set()
    for poly in me.polygons:
        u = sum(uvl[li].uv[0] for li in poly.loop_indices) / poly.loop_total
        v = sum(uvl[li].uv[1] for li in poly.loop_indices) / poly.loop_total
        x = min(w - 1, max(0, int(u % 1 * w)))
        y = min(h - 1, max(0, int(v % 1 * h)))
        if px[y, x, :3].mean() > 0.3:
            hot.add(poly.index)
    bm = bmesh.new()
    bm.from_mesh(me)
    kinds = {}
    for comp in loose_parts(bm):
        idx = [g.index for g in comp]
        if len(comp) <= 4:
            k = "drop"                                      # stray 2-face fragments of the scan
        elif all(g.material_index == 0 for g in comp):
            k = "glass"
        elif sum(1 for i in idx if i in hot) > 0.3 * len(idx):
            k = "filament"
        else:
            k = "metal"
        for i in idx:
            kinds[i] = k
    bm.free()
    out = {}
    for k in ("glass", "filament", "metal"):
        m2 = me.copy()
        m2.name = f"bulb_{k}"
        b2 = bmesh.new()
        b2.from_mesh(m2)
        b2.faces.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if kinds[f.index] != k], context="FACES")
        b2.to_mesh(m2)
        b2.free()
        m2.transform(Matrix.Rotation(math.pi, 4, "X") @ Matrix.Scale(SCALE, 4))   # hang it: base up, glass down
        out[k] = D.link(bpy.data.objects.new(f"Bulb_{k}", m2))
        D.set_smooth(out[k])
    bpy.data.objects.remove(src)
    D.assign(out["glass"], thin_glass())
    fil = D.mat_emission("#FFB65C", envf("TLB_FIL", 60.0), name="filament_glow")
    fil.cycles.emission_sampling = "NONE"                    # the POINT light does the lighting
    D.assign(out["filament"], fil)
    out["filament"].visible_shadow = False                   # the light sits inside the coil
    D.assign(out["metal"], metal)
    p = metal.node_tree.nodes.get("Principled BSDF")
    D._set(p, coat=0.3, coat_rough=0.1)
    return out


BULB = split_bulb()
_fv = [v.co for v in BULB["filament"].data.vertices]
FIL_C = sum(_fv, V()) / len(_fv)                           # bulb-local (top of the screw base ~ z +0.06)
_mz = max(v.co.z for v in BULB["metal"].data.vertices)      # top of the screw base (bulb-local, after the flip)
_gz = min(v.co.z for v in BULB["glass"].data.vertices)      # bottom of the glass

# ----------------------------------------------------------------------------------------------------------------
# rig: Pivot (above frame) -> Swing (pendulum angle about Y) -> Twist (about the cord) -> socket, cord, bulb
# ----------------------------------------------------------------------------------------------------------------
L_CORD = 2.24                                               # pendulum length to the bulb centre: T = 3.0 s
BULB_Y = envf("TLB_Y", 0.15)
BULB_Z = envf("TLB_Z", 0.38)                                # bulb (filament) height at rest
PIVOT = V((0.0, BULB_Y, BULB_Z + L_CORD))
pivot = D.empty("Pivot", tuple(PIVOT), size=0.2)
twist = D.empty("Twist", (0, 0, -L_CORD), size=0.1)
twist.parent = pivot
holder = D.empty("BulbHolder", (0, 0, 0), size=0.05)
holder.parent = twist
for k in ("glass", "filament", "metal"):
    BULB[k].parent = holder
    BULB[k].location = -FIL_C                               # filament centre on the pendulum axis end
SOCK_R, SOCK_H = 0.060, 0.115
sock_z0 = _mz - FIL_C.z - 0.012
socket = D.cylinder("Socket", SOCK_R, SOCK_H, (0, 0, sock_z0), mat=D.mat_candy("mint", name="candy_socket_mint"),
                    bevel=0.016, base_at_zero=True)
socket.parent = holder
collar = D.torus("SocketCollar", SOCK_R - 0.004, 0.009, (0, 0, sock_z0 + 0.012),
                 mat=D.mat_candy("white", name="candy_collar_white"), major_seg=96, minor_seg=16)
collar.parent = holder
cap = D.sphere("SocketCap", 0.032, (0, 0, sock_z0 + SOCK_H), D.mat_candy("mint", name="candy_cap_mint"), segments=48,
               rings=24)
cap.parent = holder
cord = D.cylinder("Cord", 0.0075, L_CORD, (0, 0, sock_z0 + SOCK_H), mat=D.mat_candy("mint", name="candy_cord_mint",
                  rough=0.35), bevel=0.0, segments=32, base_at_zero=True)
cord.parent = holder

# the light: POINT at the filament + an inner glow halo (light-marker convention)
lamp_ld = bpy.data.lights.new("Filament", "POINT")
lamp_ld.energy = envf("TLB_BULB_W", 80.0)
lamp_ld.color = D.col("#FFC98E")[:3]
lamp_ld.shadow_soft_size = envf("TLB_BULB_R", 0.006)
lamp = D.link(bpy.data.objects.new("FilamentLight", lamp_ld))
lamp.parent = holder
halo_m = bpy.data.materials.new("bulb_halo")
halo_m.use_nodes = True
_n, _l = halo_m.node_tree.nodes, halo_m.node_tree.links
_n.clear()
_o = _n.new("ShaderNodeOutputMaterial")
_e = _n.new("ShaderNodeEmission")
_e.inputs["Color"].default_value = D.col("#FFCF8A")
_lw = _n.new("ShaderNodeLayerWeight")
_lw.inputs["Blend"].default_value = 0.5
_inv = _n.new("ShaderNodeMath"); _inv.operation = "SUBTRACT"; _inv.inputs[0].default_value = 1.0
_pw = _n.new("ShaderNodeMath"); _pw.operation = "POWER"; _pw.inputs[1].default_value = 3.0
_k = _n.new("ShaderNodeMath"); _k.operation = "MULTIPLY"; _k.inputs[1].default_value = envf("TLB_GLOW", 4.0)
_tr = _n.new("ShaderNodeBsdfTransparent")
_ad = _n.new("ShaderNodeAddShader")
_l.new(_lw.outputs["Facing"], _inv.inputs[1])
_l.new(_inv.outputs[0], _pw.inputs[0])
_l.new(_pw.outputs[0], _k.inputs[0])
_l.new(_k.outputs[0], _e.inputs["Strength"])
_l.new(_e.outputs[0], _ad.inputs[0])
_l.new(_tr.outputs[0], _ad.inputs[1])
_l.new(_ad.outputs[0], _o.inputs["Surface"])
halo_m.cycles.emission_sampling = "NONE"
halo = D.sphere("BulbHalo", envf("TLB_HALO_R", 0.075), (0, 0, -0.015), halo_m, segments=48, rings=24)
halo.parent = holder
halo.visible_diffuse = halo.visible_shadow = halo.visible_transmission = halo.visible_volume_scatter = False

# ----------------------------------------------------------------------------------------------------------------
# set: peach cove + three candy props whose shadows swing
# ----------------------------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=14.0, depth=10.0, height=6.0, radius=0.9, wall_y=1.25,
                   mat=D.mat_clay(BG_HEX, name="cove_peach", rough=0.7, sss=0.0, sheen=0.1))
PROPS = [
    D.cone("PropCone", 0.062, 0.16, (envf("TLB_CONE_X", -0.185), 0.08, 0.08), mat=D.mat_candy("pink", name="candy_cone_pink"), bevel=0.01),
    D.rounded_box("PropCube", (0.11, 0.11, 0.11), 0.025, location=(0.0, 0.30, 0.0), rotation=(0, 0, 22),
                  mat=D.mat_candy("violet", name="candy_cube_violet"), base_at_zero=True),
    D.sphere("PropBall", 0.055, (envf("TLB_BALL_X", 0.175), 0.06, 0.055), D.mat_candy("aqua", name="candy_ball_aqua"), segments=64,
             rings=32),
]

# ----------------------------------------------------------------------------------------------------------------
# light: the bulb is the key; soft peach fill keeps shadows tinted (G2), weak top key, candy-sky reflections
# ----------------------------------------------------------------------------------------------------------------
TGT = V((0.0, 0.12, envf("TLB_TZ", 0.36)))
D.light("AREA", "Fill", (0.0, -2.6, 1.3), (0.0, 0.2, 0.4), envf("TLB_FILL", 32.0), ENV("TLB_FILL_HEX", "#C9B6FF"),
        size=3.0)
D.light("AREA", "Key", (-1.8, -1.2, 2.4), (0.0, 0.2, 0.3), envf("TLB_KEY", 4.0), "#F6F4FF", size=1.6)
D.world_hdri(os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr"), envf("TLB_WORLD", 0.1), rot_z=90.0,
             camera_bg=BG_HEX, glossy_sees_bg=ENV("TLB_GLOSSBG", "0") == "1")
# glass read: two tall soft cards seen only by glossy rays (S02's fourth-wall convention) give the thin envelope the
# white rim highlights of a product shot (with only the dim world in its reflections the rim read olive/amber)
_card_m = D.mat_emission("#FFF8F2", envf("TLB_CARD", 2.2), name="refl_card")
_card_m.cycles.emission_sampling = "NONE"
for _nm, _x in (("CardL", -1.3), ("CardR", 1.3)):
    _c = D.rounded_box(_nm, (0.08, 0.9, 1.6), 0.02, location=(_x, -0.35, BULB_Z + 0.2), mat=_card_m)
    _c.rotation_euler = (0, 0, math.radians(-25 if _x < 0 else 25))
    _c.visible_camera = _c.visible_diffuse = _c.visible_shadow = _c.visible_transmission = False
    _c.visible_volume_scatter = False
# glass rims: a white shell around the bulb (parented, moves with it) seen ONLY by glossy rays.  With the Fresnel fix the
# thin envelope is truly clear, so against the pale peach wall its outline vanished; reflecting this shell the
# envelope gets the white Fresnel rim of a product shot (and the candy props catch a soft reflection of the lit bulb)
if envf("TLB_SHELL", 2.0) > 0:
    _sh_m = D.mat_emission("#FFFAF4", envf("TLB_SHELL", 2.0), name="rim_shell")
    _sh_m.cycles.emission_sampling = "NONE"
    # an open band (no caps) around the glass only, so the screw base above keeps its contrasty chrome
    shell = D.cylinder("RimShell", envf("TLB_SHELL_R", 0.22), 0.34, (0, 0, -0.27), mat=_sh_m, bevel=0.0,
                       segments=64, base_at_zero=True)
    _bm = bmesh.new()
    _bm.from_mesh(shell.data)
    bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if abs(f.normal.z) > 0.5], context="FACES")
    _bm.to_mesh(shell.data)
    _bm.free()
    shell.parent = holder
    shell.visible_camera = shell.visible_diffuse = shell.visible_shadow = shell.visible_transmission = False
    shell.visible_volume_scatter = False
# lift the cove corners to peach (light-linked: the cove only, so the bulb stays the key on the props)
wash = D.light("AREA", "CoveWash", (0.0, -1.0, 2.2), (0.0, 1.2, 0.6), envf("TLB_WALL", 32.0), "#FFF4EC", size=3.0)
_wc = bpy.data.collections.new("CoveWashReceivers")
_wc.objects.link(cove)
wash.light_linking.receiver_collection = _wc

# ----------------------------------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------------------------------
ELEV = math.radians(envf("TLB_ELEV", 10.0))
DIST = envf("TLB_DIST", 1.42)
CAM = TGT + V((0.0, -math.cos(ELEV), math.sin(ELEV))) * DIST
cam, cam_tgt = D.camera("Cam", tuple(CAM), tuple(TGT), lens=50.0, fstop=8.0)
cam.data.dof.focus_object = None
cam.data.dof.focus_distance = (CAM - V((0.0, BULB_Y, BULB_Z))).length

# ----------------------------------------------------------------------------------------------------------------
# G1 glow: the film's orb bloom (S01 parameters), driven by the Emit pass only -> filament + halo glow, nothing else
# ----------------------------------------------------------------------------------------------------------------
GLOW = envf("TLB_BLOOM", 1.0)
if GLOW > 0:
    sc.view_layers[0].use_pass_emit = True
    sc.use_nodes = True
    ct = sc.node_tree
    for nd in list(ct.nodes):
        ct.nodes.remove(nd)
    rl = ct.nodes.new("CompositorNodeRLayers")
    gl = ct.nodes.new("CompositorNodeGlare")
    gl.glare_type = "BLOOM"
    gl.quality = "HIGH"
    gl.inputs["Threshold"].default_value = 0.6
    gl.inputs["Smoothness"].default_value = 0.2
    gl.inputs["Strength"].default_value = GLOW
    gl.inputs["Size"].default_value = 0.45
    gl.inputs["Saturation"].default_value = 1.0
    ct.links.new(rl.outputs["Emit"], gl.inputs["Image"])
    add_glow = ct.nodes.new("CompositorNodeMixRGB")
    add_glow.blend_type = "ADD"
    add_glow.inputs["Fac"].default_value = 1.0
    ct.links.new(rl.outputs["Image"], add_glow.inputs[1])
    ct.links.new(gl.outputs["Glare"], add_glow.inputs[2])
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(add_glow.outputs[0], comp.inputs["Image"])

# ----------------------------------------------------------------------------------------------------------------
# motion: pendulum (period = LOOP) + slow twist; wrapped phase -> keys at f and f+LOOP identical
# ----------------------------------------------------------------------------------------------------------------
SWING = math.radians(envf("TLB_SWING", 4.0))
TWIST = math.radians(envf("TLB_TWIST", 4.0))


def phase(f):
    return 2 * math.pi * ((f - 1) % LOOP) / LOOP


def swing(f):
    return SWING * math.sin(phase(f))


D.bake(pivot, "rotation_euler", BAKE0, BAKE1, lambda f: (0.0, swing(f), 0.0))
D.bake(twist, "rotation_euler", BAKE0, BAKE1, lambda f: (0.0, 0.0, TWIST * math.sin(phase(f) + 0.8)))


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


BULB_OBJS = [BULB["glass"], BULB["metal"], socket, cap]
QUARTERS = (1, 1 + LOOP // 4, 1 + LOOP // 2, 1 + 3 * LOOP // 4)
METRICS = {f: frame_metrics(BULB_OBJS, f) for f in QUARTERS}
SCENE_METRICS = {f: frame_metrics(BULB_OBJS + PROPS, f) for f in QUARTERS}
sc.frame_set(1)
FINAL_SPP, FINAL_THR = int(envf("TLB_FSPP", 128)), 0.02
MEASURED_S_PER_F = 2.47      # final mode 128 spp, steady state (frames 2..n of one process)
FINAL_COST = {                  # T2 finishing pass, 2026-11-20, one process, GPU 7 (NVIDIA H200) not shared
    "gpu": "H200 (GPU 7), exclusive during the run (nvidia-smi compute-apps: only this process)",
    "measured_frames": [1, 23, 46, 68], "frame_times_s": [3.5, 2.5, 2.5, 2.4], "process_wall_s": 12.39,
    "overhead_per_process_s": 2.52, "chunk_frames": 90, "processes": 1,
    "est_gpu_h": 0.0625, "cap_gpu_h": 0.12}
meta = {
    "id": SHOT, "frames": LOOP, "loop": LOOP, "res": list(RES), "fps": 30,
    "bg": {"name": BG_NAME, "albedo_hex": BG_HEX},
    "hero": "clear light bulb (lightbulb_01) with a glowing filament on a mint candy socket + cord",
    "phenomenon": "moving point light through glass: warm light pool + swinging hard shadows; G1 filament glow",
    "palette": ["peach pastel", "warm filament", "mint", "white", "pink", "violet", "aqua"],
    "motion": f"pendulum L {L_CORD} m, period 3.0 s = 1 loop, +-{math.degrees(SWING):.0f} deg, twist +-"
              f"{math.degrees(TWIST):.0f} deg",
    "final_samples": FINAL_SPP, "final_threshold": FINAL_THR,
    "measured_final_s_per_f": MEASURED_S_PER_F,
    "final_cost": FINAL_COST,
    "bloom": "G1 (S01 params: threshold 0.6, smoothness 0.2, strength 1.0, size 0.45, saturation 1.0), Emit pass",
    "bulb_metrics": {str(k): v for k, v in METRICS.items()},
    "scene_metrics": {str(k): v for k, v in SCENE_METRICS.items()},
}
os.makedirs(os.path.join(D.ROOT, "renders", "meta"), exist_ok=True)
with open(os.path.join(D.ROOT, "renders", "meta", f"{SHOT}.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"[{SHOT}] bulb", json.dumps(METRICS))
print(f"[{SHOT}] scene", json.dumps(SCENE_METRICS))
print(f"[{SHOT}] filament_c", tuple(round(x, 4) for x in FIL_C), "metal_top", round(_mz, 4), "glass_bottom",
      round(_gz, 4))

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=LOOP, shot_name=SHOT)
