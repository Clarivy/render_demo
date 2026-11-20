"""T1 tile · t_magnifier — "Magnifying glass" (finale honeycomb mini scene, storyboard_v2 section 5, group T1).

A big candy magnifying glass (Poly Haven magnifying_glass_01, re-skinned in candy colours) glides in a slow circle
over a pink quatrefoil-jacquard swatch stretched in a white candy embroidery hoop on a sky-blue cove.  The lens is
real refracting glass, so the weave under it is magnified ~2x and swims as the glass moves, while the rest of the
swatch keeps its true scale.  The ring + handle read as the classic magnifier icon at 200 px.

Tile contract (storyboard_v2 sections 4-5)
* 1152 x 998 final (preview 50 %), flat-top hexagon inscribed in the image: everything that matters sits inside
  the hexagon.  Hero (magnifier) big and centred, readable as a silhouette at 200 px.
* Seamless loop of LOOP frames: frame LOOP+1 == frame 1 (closed-form periodic motion, keys baked one frame past
  both ends so the f1 and f(LOOP+1) shutters see the same motion).
* Static seed, D.bake, PBR Neutral, no AgX / Filmic.  Meta: renders/meta/t_magnifier.json.
* Final: 192 spp, adaptive 0.02, OIDN: 2.61 s/f steady on one H200, uncontended (first frame of a process ~4.5 s,
  4 x 8k fabric maps) -> 90 x 2.61 s = 0.065 GPU-h (cap 0.12).

Build decisions (v2 build; A/B'd on preview + final test frames)
* Magnification is optical, not a texture trick: camera rays refract through a real glass lens onto the cloth.
  The asset's own lens is low-poly (7 rings) and weak (faces R ~ 0.38 m -> f ~ 0.38 m, x1.3): through it the weave
  showed facet ripples.  It is replaced by a procedural biconvex lens in the asset's rim groove (aperture r 65.5 mm,
  spherical faces R = LENS_RC 0.25 m, IOR 1.5 crown glass, 64 rings x 160 segments, analytic per-corner normals)
  -> f ~ 0.25 m; held LENS_H 0.105 m above the cloth and viewed ~35 deg off vertical it shows the weave at ~x2
  (quatrefoil pitch inside vs outside the lens, measured on the final test frames).  The asset rim / ferrule /
  handle geometry is used as is.
* Lens orientation: tilted LENS_TILT 22 deg toward the camera (14 deg left a strongly oblique, swirly zone in the
  lower half of the lens), handle yawed so it points to the lower right -> the ring reads as a circle, the whole
  glass as the magnifier icon.
* The lens casts no shadow rays (visible_shadow off): the cloth under it stays lit by the studio lights, so the
  magnified weave is clean and noise-free (a physical lens would throw a caustic spot + dark ring that path
  tracing resolves only with fireflies).  Rim and handle cast normal soft shadows (height cue).
* The asset's textures are a worn black finish; the model is re-skinned in house candy materials: lemon candy rim,
  violet candy handle, gold ferrule.  The jacquard (8k diffuse / displacement / roughness / normal) is tone-on-tone
  crimson: its displacement map (the raised quatrefoil floats) drives a deep-pink -> light-pink ramp so the pattern
  reads at tile size (stretching the diffuse itself turned the threads into stripes that swirled like a
  fingerprint under the lens), the diffuse adds the thread detail, roughness + normal maps the sheen and relief;
  planar UVs, 0.40 m per texture repeat (~2.4 cm quatrefoil pitch).
* Camera 85 mm, 55 deg elevation, no DOF (the magnified virtual image lies ~0.3 m behind the lens: any DOF that
  softens the floor also blurs the magnified weave).  Exposure -0.35 (inside the -0.2 +- 0.3 band): the sky cove
  read near-white at -0.2.  Glossy rays see the candy sky at 0.5 (a brighter sky veiled the lens).
* Motion: 90-frame seamless loop, the glass glides once round a 5.2 x 4.0 cm ellipse (~1.6 mm/f), +-6 mm bob at
  twice the loop rate, +-2.5 / 3 deg wobble.

Run:  CUDA_VISIBLE_DEVICES=6 tools/blender/blender -b --factory-startup -P shots/t_magnifier.py -- --mode preview
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

SHOT = "t_magnifier"
RES = (1152, 998)
BG = "sky"


def envf(name, dflt):
    return float(os.environ.get(name, str(dflt)))


def envv(name, dflt):
    return Vector(tuple(float(x) for x in os.environ.get(name, dflt).split(",")))


LOOP = int(envf("T_LOOP", 90))
N = LOOP
FINAL_SPP = int(envf("T_SPP", 192))
FINAL_THR = envf("T_THR", 0.02)
MEASURED_FINAL_SPF = 2.61      # GPU 6 (H200), final 1152x998, steady, uncontended

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=FINAL_SPP, threshold=FINAL_THR, min_samples=int(envf("T_MINSPP", 32)), diffuse=3, glossy=4,
               transmission=int(envf("T_TB", 8)), volume=0, caustics=False, filter_glossy=0.0,
               clamp_indirect=envf("T_CLAMP", 10.0), motion_blur=True, shutter=0.5)
D.setup_color(exposure=envf("T_EXPO", -0.35))
D.setup_output(res=RES)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False


def phase(f):
    """Loop phase in turns, NOT wrapped: f = LOOP+1 gives exactly 1.0."""
    return (f - 1) / float(LOOP)


def bake(target, path, fn, index=-1):
    D.bake(target, path, 0, LOOP + 2, fn, index=index)


# ----------------------------------------------------------------------------------------------
# set: sky cove, white candy embroidery hoop with a pink jacquard swatch
# ----------------------------------------------------------------------------------------------
cove = D.cyclorama("Cove", width=8.0, depth=6.0, height=4.0, radius=0.6, wall_y=envf("T_WALLY", 0.9),
                   mat=D.mat_clay(BG, name="clay_cove", rough=0.65, sss=0.0, sheen=0.1))

HOOP_R = envf("T_HOOP_R", 0.140)           # fabric radius (m)
RING_r = envf("T_RING_r", 0.0105)          # hoop ring tube radius
FAB_Z = RING_r + 0.0005                    # cloth plane = ring mid-height
TEX_M = envf("T_TEX_M", 0.40)              # metres per texture repeat (8k map, ~16 quatrefoils across)
TEX = os.path.join(D.ASSETS, "textures", "quatrefoil_jacquard_fabric")


def fabric_mat():
    m = bpy.data.materials.new("jacquard_pink")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    uv = n.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"

    def tex(kind, non_color):
        t = n.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX, f"quatrefoil_jacquard_fabric_{kind}_8k.jpg"),
                                       check_existing=True)
        t.image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        t.interpolation = "Cubic"
        l.new(uv.outputs["UV"], t.inputs["Vector"])
        return t

    # crimson tone-on-tone jacquard -> two-tone candy pink.  The quatrefoil floats are driven by the DISPLACEMENT
    # map (clean motif shapes, little thread noise; stretching the diffuse itself turned the threads into
    # high-contrast stripes that swirled like a fingerprint under the lens); the diffuse's red channel then
    # multiplies in the thread detail gently.
    tdisp = tex("displacement", True)
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = envf("T_FAB_LO", 0.30)
    mr.inputs["From Max"].default_value = envf("T_FAB_HI", 0.72)
    mr.clamp = True
    l.new(tdisp.outputs["Color"], mr.inputs["Value"])
    mx = n.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    pk = D.col(os.environ.get("T_FAB_COL", "pink"))
    kd, kl = envf("T_FAB_DARK", 0.32), envf("T_FAB_LIGHT", 0.22)
    mx.inputs["A"].default_value = (pk[0] * kd, pk[1] * kd, pk[2] * kd, 1.0)
    mx.inputs["B"].default_value = D.mix_col(os.environ.get("T_FAB_COL", "pink"), "white", kl)
    l.new(mr.outputs["Result"], mx.inputs["Factor"])
    td = tex("diffuse", False)
    sep = n.new("ShaderNodeSeparateColor")
    l.new(td.outputs["Color"], sep.inputs["Color"])
    gr = n.new("ShaderNodeMath")                       # thread detail ~1.0 +- 0.2
    gr.operation = "MULTIPLY"
    gr.inputs[1].default_value = 1.0 / 0.29
    l.new(sep.outputs["Red"], gr.inputs[0])
    mt = n.new("ShaderNodeMix")
    mt.data_type = "RGBA"
    mt.blend_type = "MULTIPLY"
    mt.inputs["Factor"].default_value = envf("T_FAB_DETAIL", 0.6)
    l.new(mx.outputs["Result"], mt.inputs["A"])
    l.new(gr.outputs[0], mt.inputs["B"])
    l.new(mt.outputs["Result"], p.inputs["Base Color"])
    tr = tex("rough", True)
    l.new(tr.outputs["Color"], p.inputs["Roughness"])
    tn = tex("nor_gl", True)
    nm = n.new("ShaderNodeNormalMap")
    nm.uv_map = "UVMap"
    nm.inputs["Strength"].default_value = envf("T_FAB_NRM", 0.6)
    l.new(tn.outputs["Color"], nm.inputs["Color"])
    l.new(nm.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Sheen Weight"].default_value = envf("T_FAB_SHEEN", 0.4)
    p.inputs["Sheen Roughness"].default_value = 0.4
    p.inputs["Specular IOR Level"].default_value = 0.4
    return m


def swatch(name, radius, z, mat, segments=192):
    """Flat cloth disc with planar UVs (TEX_M metres per texture repeat)."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=segments, radius=radius)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / TEX_M + 0.5, lp.vert.co.y / TEX_M + 0.5)
    ob = D._mesh_object(name, bm, mat, smooth=False)
    ob.location = (0, 0, z)
    return ob


cloth = swatch("Jacquard", HOOP_R + 0.002, FAB_Z, fabric_mat())
WHITE = D.mat_candy("white", name="candy_white", rough=0.25)
GOLD = D.mat_metal("gold", name="metal_gold", rough=0.18)
ring = D.torus("Hoop", major=HOOP_R + 0.002, minor=RING_r, location=(0, 0, FAB_Z), mat=WHITE, major_seg=192,
               minor_seg=32)
ring_in = D.torus("HoopInner", major=HOOP_R - RING_r * 0.9, minor=RING_r * 0.55, location=(0, 0, FAB_Z + 0.002),
                  mat=WHITE, major_seg=192, minor_seg=24)
# gold clasp at the back of the hoop: one rounded block + its thumb-screw knob
cy = HOOP_R + 0.002 + RING_r
clasp = D.rounded_box("Clasp", size=(0.024, 0.016, 0.022), radius=0.005, location=(0, cy + 0.004, FAB_Z), mat=GOLD)
knob = D.cylinder("Knob", 0.0085, 0.010, (0.017, cy + 0.004, FAB_Z + 0.002), rotation=(0, math.pi / 2, 0),
                  mat=GOLD, bevel=0.003)
STAGE = [cloth, ring, ring_in, clasp, knob]
HOOP_C = envv("T_HOOP_C", "0.012,0.052,0")    # hoop centre: under the lens's line of sight (see the camera)
stage = D.empty("Stage", tuple(HOOP_C))
for ob in STAGE:
    ob.parent = stage

# ----------------------------------------------------------------------------------------------
# the magnifier: Poly Haven magnifying_glass_01, re-skinned (candy rim / handle, gold ferrule, glass lens)
# ----------------------------------------------------------------------------------------------
LENS_C_Z = 0.2055                           # lens centre in the asset (lens axis = asset -Y after import)
LENS_A = envf("T_LENS_A", 0.0655)         # clear aperture radius (sits in the asset rim's groove)
LENS_RC = envf("T_LENS_RC", 0.25)          # radius of curvature of both faces (biconvex)
LENS_EDGE = envf("T_LENS_EDGE", 0.002)     # edge thickness
LENS_IOR = envf("T_IOR", 1.5)
root, parts = D.import_gltf(os.path.join(D.ASSETS, "models", "magnifying_glass_01", "magnifying_glass_01_4k.gltf"))
mag = parts[0]
RIM = D.mat_candy(os.environ.get("T_RIM_COL", "lemon"), name="candy_rim", rough=0.2)
HANDLE = D.mat_candy(os.environ.get("T_HANDLE_COL", "violet"), name="candy_handle", rough=0.22)
GLASS = D.mat_glass("white", name="glass_lens", rough=0.0, ior=LENS_IOR)
me = mag.data
Z_RIM = envf("T_Z_RIM", 0.134)              # asset z above which the frame is the lens rim
Z_FERRULE = envf("T_Z_FERRULE", 0.112)      # gold ferrule band between handle and rim
bmm = bmesh.new()
bmm.from_mesh(me)
for f in bmm.faces:
    if f.material_index == 1:               # asset slot 1 = its lens: replaced by the procedural lens below
        f.material_index = 3
    else:
        z = f.calc_center_median().z
        f.material_index = 0 if z >= Z_RIM else (2 if z >= Z_FERRULE else 1)
bmesh.ops.delete(bmm, geom=[f for f in bmm.faces if f.material_index == 3], context="FACES")
bmm.to_mesh(me)
bmm.free()
me.materials[0] = RIM                        # replace slots in place (materials.clear() zeroes material_index)
me.materials[1] = HANDLE
me.materials.append(GOLD)
me.update()
for p_ in me.polygons:
    p_.use_smooth = True
mag.parent = None
root.parent = None
mag.data.transform(Matrix.Translation((0, 0, -LENS_C_Z)))          # lens centre at the object origin
LENS_TILT = math.radians(envf("T_LENS_TILT", 22))     # lens normal tilted toward the camera
HANDLE_YAW = math.radians(envf("T_HANDLE_YAW", -145))   # handle toward camera-right (lower right in frame)
base_rot = Matrix.Rotation(LENS_TILT, 4, "X") @ Matrix.Rotation(HANDLE_YAW, 4, "Z") @ Matrix.Rotation(
    math.radians(90), 4, "X")
pivot = D.empty("MagPivot", (0, 0, 0))
mag.parent = pivot
mag.matrix_parent_inverse = Matrix.Identity(4)
mag.matrix_basis = base_rot


def build_lens(name, a, rc, edge, nr=64, ns=160):
    """Watertight biconvex lens (spherical faces, short cylindrical edge) in the asset frame (axis = local Y),
    with analytic per-corner normals so the refraction (= the magnified weave) is free of facet ripples."""
    hc = math.sqrt(rc * rc - a * a)
    y0 = edge / 2 - hc                      # centre of the +Y face's sphere is at (0, y0, 0); -Y face mirrored
    bm = bmesh.new()

    def cap(sign):
        rows = [[bm.verts.new((0.0, sign * (edge / 2 + rc - hc), 0.0))]]
        for i in range(1, nr + 1):
            r = a * i / nr
            yy = sign * (edge / 2 + math.sqrt(rc * rc - r * r) - hc)
            rows.append([bm.verts.new((r * math.cos(2 * math.pi * k / ns), yy, r * math.sin(2 * math.pi * k / ns)))
                         for k in range(ns)])
        for k in range(ns):
            bm.faces.new((rows[0][0], rows[1][k], rows[1][(k + 1) % ns]))
        for i in range(1, nr):
            for k in range(ns):
                bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][(k + 1) % ns], rows[i][(k + 1) % ns]))
        return rows[-1]

    top, bot = cap(+1), cap(-1)
    for k in range(ns):
        bm.faces.new((top[k], bot[k], bot[(k + 1) % ns], top[(k + 1) % ns]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob_ = D._mesh_object(name, bm, GLASS, smooth=True)
    me_ = ob_.data
    nrm = []
    for poly in me_.polygons:
        side = all(abs(abs(me_.vertices[v].co.y) - edge / 2) < 1e-7 for v in poly.vertices)
        for li in poly.loop_indices:
            co = me_.vertices[me_.loops[li].vertex_index].co
            if side:
                nv = Vector((co.x, 0.0, co.z)).normalized()
            else:
                sg = 1.0 if co.y > 0 else -1.0
                nv = (co - Vector((0.0, sg * y0, 0.0))).normalized()
            nrm.append(tuple(nv))
    me_.normals_split_custom_set(nrm)
    return ob_


lens = build_lens("Lens", LENS_A, LENS_RC, LENS_EDGE)
lens.parent = pivot
lens.matrix_parent_inverse = Matrix.Identity(4)
lens.matrix_basis = base_rot
lens.visible_shadow = False                 # the cloth under the lens stays lit (see the header)
LENS_T = LENS_EDGE + 2 * (LENS_RC - math.sqrt(LENS_RC ** 2 - LENS_A ** 2))
LENS_F = 1.0 / ((LENS_IOR - 1) * (2 / LENS_RC - (LENS_IOR - 1) * LENS_T / (LENS_IOR * LENS_RC ** 2)))
HERO = [mag, lens]

LENS_H = envf("T_LENS_H", 0.105)            # lens centre height above the cloth
GLIDE_A = envf("T_GLIDE_A", 0.026)          # glide ellipse semi-axes (m)
GLIDE_B = envf("T_GLIDE_B", 0.020)
GLIDE_C = envv("T_GLIDE_C", "-0.018,0.012,0")


def pivot_loc(f):
    a = 2 * math.pi * phase(f)
    return (GLIDE_C.x + GLIDE_A * math.cos(a), GLIDE_C.y + GLIDE_B * math.sin(a),
            FAB_Z + LENS_H + 0.006 * math.sin(2 * a))


def pivot_rot(f):
    a = 2 * math.pi * phase(f)
    return (math.radians(2.5) * math.sin(a + 0.6), math.radians(3.0) * math.cos(a), 0.0)


bake(pivot, "location", pivot_loc)
bake(pivot, "rotation_euler", pivot_rot)

# ----------------------------------------------------------------------------------------------
# light: soft studio rig (warm key upper-left behind, cool fill right, top rim) + candy sky for reflections
# ----------------------------------------------------------------------------------------------
TGT = Vector((0, 0, 0.05))
key = D.light("AREA", "Key", tuple(envv("T_KEY_POS", "-0.75,0.15,1.05")), tuple(TGT), power=envf("T_KEY", 60),
              color="#FFF1E0", size=envf("T_KEY_SIZE", 0.35))
fill = D.light("AREA", "Fill", tuple(envv("T_FILL_POS", "0.9,-0.7,0.6")), tuple(TGT), power=envf("T_FILL", 15),
               color="#E6F0FF", size=0.9)
rim = D.light("AREA", "Rim", tuple(envv("T_RIM_POS", "0.3,0.9,0.9")), tuple(TGT), power=envf("T_RIM", 22),
              color="white", size=0.5)
sky_path = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
WORLD_K = envf("T_WORLD", 0.22)
WORLD_GLOSSY = envf("T_WGLOSSY", 0.5)
rig = D.world_hdri(sky_path, WORLD_K, rot_z=envf("T_SKY_ROT", 30.0), camera_bg=BG)
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
# camera: 85 mm, 55 deg elevation, locked
# ----------------------------------------------------------------------------------------------
LENS = envf("T_LENS", 85)
EL = math.radians(envf("T_EL", 55))
DIST = envf("T_DIST", 1.09)
CAM_TGT = envv("T_CAM_TGT", "0.015,0.010,0.040")
cam_loc = CAM_TGT + DIST * Vector((0, -math.cos(EL), math.sin(EL)))
cam, cam_t = D.camera("Cam", tuple(cam_loc), tuple(CAM_TGT), lens=LENS, fstop=envf("T_FSTOP", 0.0))
cam_t.location = CAM_TGT

# ----------------------------------------------------------------------------------------------
# QA silhouette mode
# ----------------------------------------------------------------------------------------------
if os.environ.get("T_MASK"):
    white = D.mat_emission("white", 1.0, name="mask_white")
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            if ob in HERO or (os.environ.get("T_MASK") == "all" and ob in STAGE):
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
    "hero": "magnifying_glass_01 (Poly Haven) re-skinned: lemon candy rim, violet candy handle, gold ferrule, "
            "glass lens; over a pink quatrefoil jacquard swatch in a white candy embroidery hoop",
    "phenomenon": "refraction / magnification: the glass lens magnifies the jacquard weave (~x2) as it glides",
    "palette": [BG, "pink", "white", "lemon", "violet", "gold"],
    "motion": f"magnifier glides once round a {GLIDE_A * 200:.0f} x {GLIDE_B * 200:.0f} cm ellipse per loop, "
              "+-6 mm bob, +-3 deg wobble",
    "lens": {"ior": LENS_IOR, "radius_of_curvature_m": LENS_RC, "aperture_radius_m": LENS_A,
             "centre_thickness_m": round(LENS_T, 4), "focal_length_m": round(LENS_F, 4),
             "height_above_cloth_m": LENS_H, "casts_shadow": False,
             "magnification_measured": "x1.87-2.00 (quatrefoil pitch inside vs outside the lens, FFT peak, final test "
                                       "frames 1, 23, 46, 68)"},
    "final_spp": FINAL_SPP,
    "final_threshold": FINAL_THR,
    "measured_final_s_per_frame": MEASURED_FINAL_SPF,
    "est_final_gpu_h": round(MEASURED_FINAL_SPF * N / 3600.0, 4) if MEASURED_FINAL_SPF else None,
    "measured_final_note": "GPU 6 (H200), --mode final, steady mean of frames 2-8 of one 8-frame process; uncontended: nvidia-smi polled every 0.5 s showed no other GPU-6 process during the run; first frame of a process is +1-3 s (scene build / BVH / texture upload)",
}
meta_dir = os.path.join(D.ROOT, "renders", "meta")
os.makedirs(meta_dir, exist_ok=True)
if not os.environ.get("T_MASK") and not os.environ.get("T_NOMETA"):
    with open(os.path.join(meta_dir, SHOT + ".json"), "w") as fh:
        json.dump(meta, fh, indent=1)

D.finish(args, final_samples=FINAL_SPP, final_threshold=FINAL_THR, frame_end=N, shot_name=SHOT)
