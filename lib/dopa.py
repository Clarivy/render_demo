"""dopa — Dopamine x Tactile-3D style kit for Blender 4.5 LTS (Cycles).

Every shot script does:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
    import dopa as D
    args = D.parse_args()              # flags after "--" on the blender command line
    D.reset_scene()
    ... build with D.* helpers ...
    D.finish(args)                     # render settings per mode, optional .blend save, render frames

Conventions
-----------
* Units: metres. Z up. Camera looks roughly along +Y toward a backdrop at +Y.
* Colours: pass palette names ("pink") or hex ("#FF4D9D"); helpers convert sRGB -> linear.
* Every shot is its own scene, 30 fps, frame 1 = first frame of the shot.
* Motion: prefer D.bake(...) with the easing functions below (per-frame keys, LINEAR).
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASSETS = os.path.join(ROOT, "assets")
FPS = 30

FONTS = {
    "fredoka": os.path.join(ASSETS, "fonts", "Fredoka-Bold.ttf"),
    "fredoka_semi": os.path.join(ASSETS, "fonts", "Fredoka-SemiBold.ttf"),
    "dynapuff": os.path.join(ASSETS, "fonts", "DynaPuff-Bold.ttf"),
    "titan": os.path.join(ASSETS, "fonts", "TitanOne-Regular.ttf"),
    "lilita": os.path.join(ASSETS, "fonts", "LilitaOne-Regular.ttf"),
    "poppins": os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf"),
    "nunito": os.path.join(ASSETS, "fonts", "Nunito-Black.ttf"),
}

HDRI = {n: os.path.join(ASSETS, "hdri", f"{n}_4k.hdr") for n in (
    "colorful_studio", "studio_small_09", "cyclorama_hard_light", "neon_photostudio",
    "brown_photostudio_02", "venice_sunset", "the_sky_is_on_fire", "noon_grass",
    "spruit_sunrise", "kloppenheim_06_puresky")}

# ----------------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------------
PALETTE = {
    # saturated hero colours
    "pink": "#FF4D9D", "coral": "#FF6A5C", "orange": "#FF8A1F", "lemon": "#FFD23F",
    "lime": "#B5E61D", "mint": "#2ED8A3", "aqua": "#1FC2EE", "blue": "#2E5BFF",
    "violet": "#8A5CF6", "lilac": "#C3A6FF",
    # pastel grounds
    "blush": "#FFD3E4", "peach": "#FFDCC7", "butter": "#FFF0A8", "pistachio": "#CFF5DD",
    "sky": "#CDE9FF", "lavender": "#E5DAFF", "cream": "#FFF6EC",
    # neutrals
    "ink": "#1C1A33", "white": "#FFFFFF", "offwhite": "#F7F5F2", "chrome": "#F4F4F8",
    "gold": "#FFC867",
}


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def col(c, alpha: float = 1.0):
    """Palette name / '#RRGGBB' / (r,g,b[,a]) in sRGB 0..1 -> linear RGBA tuple."""
    if isinstance(c, str):
        h = PALETTE.get(c, c).lstrip("#")
        rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        return tuple(srgb_to_linear(v) for v in rgb) + (alpha,)
    c = tuple(c)
    if len(c) == 3:
        return tuple(srgb_to_linear(v) for v in c) + (alpha,)
    return tuple(srgb_to_linear(v) for v in c[:3]) + (c[3],)


def mix_col(a, b, t: float):
    ca, cb = col(a), col(b)
    return tuple(ca[i] * (1 - t) + cb[i] * t for i in range(4))


# ----------------------------------------------------------------------------
# Scene / render setup
# ----------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 1
    if not sc.world:
        sc.world = bpy.data.worlds.new("World")
    return sc


# Outside Slurm: the GPUs this project may use on a shared box. Default 6,7 (the original br-dfw-h200-tlv1-10
# rule: at most 2 GPUs there). Override per machine with DOPA_ALLOWED_GPUS, e.g. "0" or "0,1" on a workstation.
ALLOWED_GPUS = {g.strip() for g in os.environ.get("DOPA_ALLOWED_GPUS", "6,7").split(",") if g.strip()}


def _in_slurm_gpu_job():
    """True inside a Slurm allocation that holds GPUs. This cluster sets ConstrainDevices=yes (cgroup v2), so a
    process in the job can only see the GPUs Slurm allocated to it: any CUDA_VISIBLE_DEVICES there is safe.
    (2026-11-20: the user allowed Slurm jobs with up to 4 GPUs; outside Slurm the GPU 6/7 rule still holds.)"""
    return bool(os.environ.get("SLURM_JOB_ID")) and bool(
        os.environ.get("SLURM_JOB_GPUS") or os.environ.get("SLURM_STEP_GPUS") or os.environ.get("SLURM_GPUS_ON_NODE"))


def _gpu_guard():
    """Abort unless CUDA_VISIBLE_DEVICES is set and names only allowed GPUs (never all 8 by accident).
    Inside a Slurm GPU job the allocation itself (cgroup-constrained) is the allowed set."""
    vis = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    ids = [v.strip() for v in vis.split(",") if v.strip()]
    if ids and _in_slurm_gpu_job():
        return
    if not ids or not set(ids) <= ALLOWED_GPUS:
        sys.stderr.write(f"[dopa] REFUSING TO RENDER: CUDA_VISIBLE_DEVICES={vis!r}; this project may only use "
                         f"GPU(s) {','.join(sorted(ALLOWED_GPUS))} outside Slurm (set DOPA_ALLOWED_GPUS to change). "
                         f"Run inside a Slurm GPU job, or e.g.  CUDA_VISIBLE_DEVICES=6 tools/blender/blender ...\n")
        sys.stderr.flush()
        os._exit(3)


def enable_gpu(backend: str = "CUDA"):
    """Use every GPU of `backend` that is visible. Guarded: a Slurm GPU allocation, or CUDA_VISIBLE_DEVICES within
    DOPA_ALLOWED_GPUS (default 6,7) outside Slurm."""
    _gpu_guard()
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = backend
    prefs.get_devices()
    n = 0
    for d in prefs.devices:
        d.use = d.type == backend
        n += d.use
    bpy.context.scene.cycles.device = "GPU" if n else "CPU"
    return n


def setup_cycles(samples=512, threshold=0.01, min_samples=0, max_bounces=16, diffuse=4, glossy=8,
                 transmission=16, transparent=16, volume=2, caustics=True, filter_glossy=0.0,
                 clamp_direct=0.0, clamp_indirect=12.0, denoise=True, motion_blur=True,
                 shutter=0.5, light_tree=True, backend="CUDA"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    enable_gpu(backend)
    c = sc.cycles
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = threshold
    c.adaptive_min_samples = min_samples
    c.max_bounces = max_bounces
    c.diffuse_bounces = diffuse
    c.glossy_bounces = glossy
    c.transmission_bounces = transmission
    c.transparent_max_bounces = transparent
    c.volume_bounces = volume
    c.caustics_reflective = caustics
    c.caustics_refractive = caustics
    c.blur_glossy = filter_glossy
    c.sample_clamp_direct = clamp_direct
    c.sample_clamp_indirect = clamp_indirect
    c.use_light_tree = light_tree
    c.use_denoising = denoise
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "ACCURATE"
    c.denoising_quality = "HIGH"
    c.denoising_use_gpu = True
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = shutter
    sc.render.use_persistent_data = True
    return c


def setup_color(look="None", exposure=-0.2, gamma=1.0, view="Khronos PBR Neutral"):
    """Film-wide colour pipeline. Khronos PBR Neutral keeps palette colours faithful (AgX greys them,
    Standard clips). Keep view/look fixed for every shot; per-shot exposure within +-0.5 is fine."""
    vs = bpy.context.scene.view_settings
    vs.view_transform = view
    vs.look = look
    vs.exposure = exposure
    vs.gamma = gamma
    bpy.context.scene.render.dither_intensity = 1.0


def setup_output(res=(1920, 1080), pct=100, fmt="PNG", depth="16", transparent=False):
    r = bpy.context.scene.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = pct
    r.image_settings.file_format = fmt
    r.image_settings.color_mode = "RGBA" if transparent else "RGB"
    r.image_settings.color_depth = depth
    if fmt == "PNG":
        r.image_settings.compression = 15
    r.film_transparent = transparent


# ----------------------------------------------------------------------------
# Object utilities
# ----------------------------------------------------------------------------
def link(ob, collection=None):
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def empty(name="Empty", location=(0, 0, 0), size=0.2, kind="PLAIN_AXES", parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    ob.location = location
    if parent:
        ob.parent = parent
    return link(ob)


def set_smooth(ob, smooth=True):
    me = ob.data
    if hasattr(me, "polygons"):
        me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
        me.update()
    return ob


def assign(ob, mat, slot_only=False):
    if mat is None:
        return ob
    if slot_only and ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    return ob


def look_at(ob, target, track="-Z", up="Y"):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat(track, up).to_euler()
    return ob


def place(ob, location=(0, 0, 0), rotation=(0, 0, 0), scale=None):
    ob.location = location
    ob.rotation_euler = Euler([math.radians(a) for a in rotation])
    if scale is not None:
        ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    return ob


def box_uv(ob, scale=1.0):
    """Box-projected UVs in metres (object space): a texture with uv_scale=k repeats k times per metre,
    consistently across every generated object. Bevel/subsurf modifiers interpolate these UVs."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = ((co.y, co.z), (co.x, co.z), (co.x, co.y))[ax]
            loop[uv].uv = (u * scale, v * scale)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def _mesh_object(name, bm, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    if smooth:
        set_smooth(ob)
    assign(ob, mat)
    return ob


def apply_modifiers(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.clear()
    old = ob.data
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def normalize(ob, size=1.0, ground=True, center_xy=True, axis="max"):
    """Scale an imported mesh so its bounding box `axis` extent == size; sit it on z=0."""
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ext = mx - mn
    ref = {"max": max(ext), "x": ext.x, "y": ext.y, "z": ext.z}[axis]
    s = size / ref
    # bake into mesh data so the object transform stays clean
    me = ob.data
    center = (mn + mx) / 2
    off = Vector((center.x if center_xy else 0, center.y if center_xy else 0, mn.z if ground else center.z))
    M = Matrix.Scale(s, 4) @ Matrix.Translation(-off) @ ob.matrix_world
    me.transform(M)
    ob.matrix_world = Matrix.Identity(4)
    me.update()
    bpy.context.view_layer.update()
    return ob


# ----------------------------------------------------------------------------
# Tactile geometry
# ----------------------------------------------------------------------------
def rounded_box(name="RBox", size=(1, 1, 1), radius=0.12, segments=6, location=(0, 0, 0),
                rotation=(0, 0, 0), mat=None, soft=False, base_at_zero=False):
    """Box with circular bevelled edges. soft=True adds subdivision for a pillowy, inflated look."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + (sz / 2 if base_at_zero else 0)))
    ob = _mesh_object(name, bm, mat)
    box_uv(ob)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = min(radius, min(size) / 2 - 1e-4)
    bev.segments = 2 if soft else segments
    bev.limit_method = "NONE"
    bev.profile = 0.5
    if soft:
        sub = ob.modifiers.new("Soft", "SUBSURF")
        sub.levels = 2
        sub.render_levels = 3
    else:
        bev.harden_normals = True
    return place(ob, location, rotation)


def sphere(name="Sphere", radius=0.5, location=(0, 0, 0), mat=None, segments=96, rings=48):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    ob = _mesh_object(name, bm, mat)
    return place(ob, location)


def capsule(name="Capsule", radius=0.25, length=1.0, location=(0, 0, 0), rotation=(0, 0, 0), mat=None,
            segments=64, rings=32):
    """Pill shape along local Z; `length` is the total length including caps."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    half = max(0.0, length / 2 - radius)
    for v in bm.verts:
        v.co.z += half if v.co.z > 1e-6 else (-half if v.co.z < -1e-6 else 0)
    ob = _mesh_object(name, bm, mat)
    return place(ob, location, rotation)


def cylinder(name="Cyl", radius=0.5, depth=1.0, location=(0, 0, 0), rotation=(0, 0, 0), mat=None,
             bevel=0.05, segments=96, base_at_zero=False):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    if base_at_zero:
        for v in bm.verts:
            v.co.z += depth / 2
    ob = _mesh_object(name, bm, mat)
    box_uv(ob)
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 6
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.harden_normals = True
    return place(ob, location, rotation)


def torus(name="Torus", major=0.5, minor=0.18, location=(0, 0, 0), rotation=(0, 0, 0), mat=None,
          major_seg=128, minor_seg=48):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=major_seg, minor_segments=minor_seg)
    ob = bpy.context.object
    ob.name = name
    set_smooth(ob)
    assign(ob, mat)
    return place(ob, location, rotation)


def cone(name="Cone", radius=0.4, depth=0.8, location=(0, 0, 0), rotation=(0, 0, 0), mat=None, bevel=0.03):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=96, radius1=radius, radius2=0.0,
                          depth=depth)
    ob = _mesh_object(name, bm, mat)
    if bevel:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 5
        b.limit_method = "ANGLE"
        b.harden_normals = True
    return place(ob, location, rotation)


def cyclorama(name="Cyc", width=30.0, depth=20.0, height=12.0, radius=4.0, wall_y=6.0, mat=None,
              steps=48):
    """Seamless floor that curves up into a back wall at y=wall_y (infinity cove)."""
    prof = [(wall_y - depth, 0.0)]
    for i in range(steps + 1):
        t = (math.pi / 2) * i / steps
        prof.append((wall_y - radius + radius * math.sin(t), radius - radius * math.cos(t)))
    prof.append((wall_y, height))
    bm = bmesh.new()
    xs = [-width / 2, width / 2]
    rows = [[bm.verts.new((x, y, z)) for x in xs] for (y, z) in prof]
    for a, b in zip(rows[:-1], rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    # UVs: u = x, v = arc length along the profile (metres) -> seamless texture over the curve
    uv = bm.loops.layers.uv.verify()
    arc = [0.0]
    for (y0, z0), (y1, z1) in zip(prof[:-1], prof[1:]):
        arc.append(arc[-1] + math.hypot(y1 - y0, z1 - z0))
    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        for loop in f.loops:
            co = loop.vert.co
            j = min(range(len(prof)), key=lambda k: abs(prof[k][0] - co.y) + abs(prof[k][1] - co.z))
            loop[uv].uv = (co.x, arc[j])
    return _mesh_object(name, bm, mat)


def plane(name="Plane", size=(2, 2), location=(0, 0, 0), rotation=(0, 0, 0), mat=None):
    bm = bmesh.new()
    sx, sy = size
    vs = [bm.verts.new(v) for v in [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0),
                                     (-sx / 2, sy / 2, 0)]]
    bm.faces.new(vs)
    bm.loops.layers.uv.new("UVMap")
    uv = bm.loops.layers.uv.active
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = ((loop.vert.co.x / sx) + 0.5, (loop.vert.co.y / sy) + 0.5)
    ob = _mesh_object(name, bm, mat, smooth=False)
    return place(ob, location, rotation)


def diorama_corner(name="Room", size=4.0, height=3.0, thickness=0.18, radius=0.05, floor_mat=None,
                   left_mat=None, right_mat=None, location=(0, 0, 0), rot_z=45.0):
    """Dollhouse corner like the paper-teaser rooms: a floor slab plus two back walls, all rounded slabs.
    Local frame: floor spans [-s/2, s/2]^2 (top at z=0); walls stand on the +X and +Y edges. With the
    default rot_z=45 the back corner points to +Y and the open side faces a camera at -Y.
    Returns the root empty (parent of floor/wallL/wallR)."""
    root = empty(name, location)
    s, t, h = size, thickness, height
    fl = rounded_box(name + "_floor", (s + t, s + t, t), radius, location=(t / 2, t / 2, -t / 2), mat=floor_mat)
    wl = rounded_box(name + "_wallL", (s + t, t, h), radius, location=(t / 2, s / 2 + t / 2, h / 2 - t),
                     mat=left_mat)
    wr = rounded_box(name + "_wallR", (t, s, h), radius, location=(s / 2 + t / 2, 0.0, h / 2 - t), mat=right_mat)
    for o in (fl, wl, wr):
        o.parent = root
    root.rotation_euler = Euler((0, 0, math.radians(rot_z)))
    return root


def text3d(body, name="Text", font="fredoka", size=1.0, extrude=0.12, bevel=0.05, bevel_res=8,
           location=(0, 0, 0), rotation=(90, 0, 0), mat=None, align_x="CENTER", align_y="CENTER",
           spacing=1.0, offset=0.0, to_mesh=False):
    """Chunky rounded 3D text. Default rotation stands it up facing -Y (toward a camera at -Y)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONTS.get(font, font), check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    cu.offset = offset
    cu.align_x = align_x
    cu.align_y = align_y
    cu.space_character = spacing
    cu.resolution_u = 24
    ob = link(bpy.data.objects.new(name, cu))
    if mat:
        cu.materials.append(mat)
    place(ob, location, rotation)
    if to_mesh:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.convert(target="MESH")
        ob = bpy.context.object
        set_smooth(ob)
    return ob


def import_gltf(path, name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    root = empty(name or os.path.splitext(os.path.basename(path))[0])
    for o in new:
        if o.parent is None:
            o.parent = root
    return root, meshes


def import_obj(path, name=None, mat=None, smooth=True):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    ob = new[0]
    if len(new) > 1:
        with bpy.context.temp_override(active_object=ob, selected_editable_objects=new):
            bpy.ops.object.join()
    if name:
        ob.name = name
    if smooth:
        set_smooth(ob)
    assign(ob, mat)
    return ob


def fill_holes(ob):
    """Close open boundaries (scan holes) so voxel remeshing / glass rendering sees a solid."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def remesh_watertight(ob, voxel=0.01, smooth_iters=0):
    fill_holes(ob)
    m = ob.modifiers.new("Remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.adaptivity = 0.0
    m.use_smooth_shade = True
    if smooth_iters:
        s = ob.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
        s.iterations = smooth_iters
        s.use_only_smooth = True
    apply_modifiers(ob)
    set_smooth(ob)
    return ob


def stanford_bunny(name="Bunny", height=1.0, mat=None, location=(0, 0, 0), rotation=(0, 0, 0)):
    """Stanford bunny (69k tris) with its scan holes filled - closed enough for glass.
    (Voxel remesh does NOT work on this scan: a few non-manifold boundary edges remain.)"""
    ob = import_obj(os.path.join(ASSETS, "models", "stanford-bunny.obj"), name=name)
    normalize(ob, size=height, axis="z")
    fill_holes(ob)
    set_smooth(ob)
    assign(ob, mat)
    return place(ob, location, rotation)


def spot_cow(name="Spot", height=1.0, mat=None, location=(0, 0, 0), rotation=(0, 0, 0)):
    ob = import_obj(os.path.join(ASSETS, "models", "spot.obj"), name=name)
    normalize(ob, size=height, axis="z")
    assign(ob, mat)
    return place(ob, location, rotation)


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def _set(p, **kw):
    names = {
        "base": "Base Color", "metallic": "Metallic", "rough": "Roughness", "ior": "IOR", "alpha": "Alpha",
        "sss": "Subsurface Weight", "sss_radius": "Subsurface Radius", "sss_scale": "Subsurface Scale",
        "spec": "Specular IOR Level", "spec_tint": "Specular Tint", "aniso": "Anisotropic",
        "transmission": "Transmission Weight", "coat": "Coat Weight", "coat_rough": "Coat Roughness",
        "coat_ior": "Coat IOR", "coat_tint": "Coat Tint", "sheen": "Sheen Weight", "sheen_rough": "Sheen Roughness",
        "sheen_tint": "Sheen Tint", "emission": "Emission Color", "emission_strength": "Emission Strength",
        "film": "Thin Film Thickness", "film_ior": "Thin Film IOR", "diffuse_rough": "Diffuse Roughness",
    }
    for k, v in kw.items():
        inp = p.inputs[names[k]]
        if k in ("base", "emission", "spec_tint", "coat_tint", "sheen_tint"):
            v = col(v) if not (isinstance(v, tuple) and len(v) == 4) else v
        inp.default_value = v


def principled(name, **kw):
    m, n, l, p = _new_mat(name)
    _set(p, **kw)
    return m


def mat_clay(color, name=None, rough=0.55, sss=0.15, sheen=0.25):
    """Soft matte modelling clay / soft-touch plastic. The default 'tactile' surface."""
    c = col(color)
    return principled(name or f"clay_{color}", base=c, rough=rough, sss=sss,
                      sss_radius=(c[0] + 0.2, c[1] + 0.1, c[2] + 0.1), sss_scale=0.04,
                      sheen=sheen, sheen_rough=0.45, sheen_tint="white", spec=0.45)


def mat_candy(color, name=None, rough=0.22, coat=1.0, coat_rough=0.03, sss=0.08):
    """Glossy hard-candy / lacquered toy plastic with a clear coat."""
    c = col(color)
    return principled(name or f"candy_{color}", base=c, rough=rough, coat=coat, coat_rough=coat_rough,
                      sss=sss, sss_radius=(c[0] + 0.2, c[1] + 0.1, c[2] + 0.1), sss_scale=0.03)


def mat_rubber(color, name=None, rough=0.42):
    return principled(name or f"rubber_{color}", base=col(color), rough=rough, coat=0.25, coat_rough=0.25,
                      spec=0.4)


def mat_velvet(color, name=None):
    c = col(color)
    return principled(name or f"velvet_{color}", base=c, rough=0.85, sheen=1.0, sheen_rough=0.35,
                      sheen_tint=mix_col("white", color, 0.35), spec=0.25)


def mat_metal(color="chrome", name=None, rough=0.05, aniso=0.0):
    """Chrome (default) or saturated anodised metal (pass a hero colour)."""
    return principled(name or f"metal_{color}", base=col(color), metallic=1.0, rough=rough, aniso=aniso)


def mat_iridescent(color="white", name=None, rough=0.08, film=(250.0, 750.0), film_ior=1.45, metallic=1.0,
                   noise_scale=2.5):
    """Holographic / soap-bubble thin film. film=(min_nm, max_nm) drives the thickness with a noise
    texture so the interference colours swirl across the surface; a single float gives a uniform film."""
    m, n, l, p = _new_mat(name or f"irid_{color}")
    _set(p, base=col(color), metallic=metallic, rough=rough, film_ior=film_ior)
    if isinstance(film, (int, float)):
        _set(p, film=float(film))
        return m
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = noise_scale
    nz.inputs["Detail"].default_value = 3.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = film[0]
    mr.inputs["To Max"].default_value = film[1]
    l.new(nz.outputs["Fac"], mr.inputs["Value"])
    l.new(mr.outputs["Result"], p.inputs["Thin Film Thickness"])
    return m


def mat_emission(color, strength=10.0, name=None):
    m, n, l, p = _new_mat(name or f"emit_{color}")
    n.remove(p)
    e = n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = col(color)
    e.inputs["Strength"].default_value = strength
    l.new(e.outputs[0], n["Material Output"].inputs["Surface"])
    return m


def mat_glass(color="white", name=None, rough=0.0, ior=1.5, absorb=0.0, absorb_color=None):
    """Clear or tinted glass. absorb>0 adds Beer-Lambert volume absorption (rich colour in thick parts)."""
    m, n, l, p = _new_mat(name or f"glass_{color}")
    _set(p, base=col(color), transmission=1.0, rough=rough, ior=ior, spec=0.5)
    if absorb > 0:
        va = n.new("ShaderNodeVolumeAbsorption")
        ac = col(absorb_color or color)
        va.inputs["Color"].default_value = ac
        va.inputs["Density"].default_value = absorb
        l.new(va.outputs[0], n["Material Output"].inputs["Volume"])
    return m


def mat_glass_dispersive(color="white", name=None, ior=1.5, spread=0.04, rough=0.0, absorb=0.0):
    """Fake spectral dispersion: three glass lobes (R,G,B) with slightly different IOR.
    Gives rainbow fringes and rainbow caustics in Cycles."""
    m, n, l, p = _new_mat(name or f"dglass_{color}")
    n.remove(p)
    tint = col(color)
    out = n["Material Output"]
    shaders = []
    for i, (rgb, d) in enumerate((((1, 0, 0), -spread), ((0, 1, 0), 0.0), ((0, 0, 1), spread))):
        g = n.new("ShaderNodeBsdfGlass")
        g.distribution = "MULTI_GGX"
        g.inputs["Color"].default_value = (rgb[0] * tint[0], rgb[1] * tint[1], rgb[2] * tint[2], 1)
        g.inputs["IOR"].default_value = ior + d
        g.inputs["Roughness"].default_value = rough
        g.location = (-300, 200 - 200 * i)
        shaders.append(g)
    a1 = n.new("ShaderNodeAddShader")
    a2 = n.new("ShaderNodeAddShader")
    l.new(shaders[0].outputs[0], a1.inputs[0])
    l.new(shaders[1].outputs[0], a1.inputs[1])
    l.new(a1.outputs[0], a2.inputs[0])
    l.new(shaders[2].outputs[0], a2.inputs[1])
    l.new(a2.outputs[0], out.inputs["Surface"])
    if absorb > 0:
        va = n.new("ShaderNodeVolumeAbsorption")
        va.inputs["Color"].default_value = tint
        va.inputs["Density"].default_value = absorb
        l.new(va.outputs[0], out.inputs["Volume"])
    return m


def mat_jelly(color, name=None, density=2.5, rough=0.06, sss=0.0):
    """Gummy / jelly: clear transmissive shell + coloured absorbing volume + faint scatter."""
    m, n, l, p = _new_mat(name or f"jelly_{color}")
    c = col(color)
    _set(p, base=mix_col("white", color, 0.25), transmission=1.0, rough=rough, ior=1.38, sss=sss)
    vp = n.new("ShaderNodeVolumePrincipled")
    vp.inputs["Color"].default_value = c
    vp.inputs["Density"].default_value = density * 0.15
    vp.inputs["Absorption Color"].default_value = c
    l.new(vp.outputs[0], n["Material Output"].inputs["Volume"])
    return m


def mat_image(path, name=None, rough=0.5, normal_path=None, rough_path=None, normal_strength=1.0,
              tint=None, tint_mix=0.0, uv_scale=1.0, interpolation="Smart", projection="FLAT",
              coat=0.0, sheen=0.0, closest=False):
    """Image-textured surface (paintings, Poly Haven fabrics...).
    tint (+tint_mix 0..1) multiplies the albedo toward a palette colour while keeping all detail."""
    m, n, l, p = _new_mat(name or f"img_{os.path.basename(path)}")
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    l.new(tc.outputs["UV"], mp.inputs["Vector"])

    def tex(pth, non_color=False):
        t = n.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(pth, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        t.interpolation = "Closest" if closest else interpolation
        t.projection = projection
        l.new(mp.outputs[0], t.inputs["Vector"])
        return t

    t = tex(path)
    color_out = t.outputs["Color"]
    if tint is not None and tint_mix > 0:
        mx = n.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = tint_mix
        l.new(color_out, mx.inputs["A"])
        mx.inputs["B"].default_value = col(tint)
        color_out = mx.outputs["Result"]
    l.new(color_out, p.inputs["Base Color"])
    _set(p, rough=rough, coat=coat, sheen=sheen)
    if rough_path:
        tr = tex(rough_path, True)
        l.new(tr.outputs["Color"], p.inputs["Roughness"])
    if normal_path:
        tn = tex(normal_path, True)
        nm = n.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal_strength
        l.new(tn.outputs["Color"], nm.inputs["Color"])
        l.new(nm.outputs["Normal"], p.inputs["Normal"])
    return m


def mat_video(first_frame_path, n_frames, name=None, start=1, offset=0, emission=0.0, rough=0.35,
              cyclic=False):
    """Material that plays a rendered PNG sequence (e.g. renders/final/s01/f_0001.png ...) as a texture.
    Scene frame `start` shows sequence frame 1+offset. emission>0 makes it glow like a screen."""
    m, n, l, p = _new_mat(name or f"video_{os.path.basename(os.path.dirname(first_frame_path))}")
    t = n.new("ShaderNodeTexImage")
    img = bpy.data.images.load(first_frame_path, check_existing=False)
    img.source = "SEQUENCE"
    img.colorspace_settings.name = "sRGB"
    t.image = img
    iu = t.image_user
    iu.frame_duration = n_frames
    iu.frame_start = start
    iu.frame_offset = offset
    iu.use_auto_refresh = True
    iu.use_cyclic = cyclic
    t.interpolation = "Smart"
    l.new(t.outputs["Color"], p.inputs["Base Color"])
    _set(p, rough=rough, coat=0.6, coat_rough=0.05)
    if emission > 0:
        l.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emission
    return m


def polyhaven_texture(tex_id, res="4k", name=None, **kw):
    d = os.path.join(ASSETS, "textures", tex_id)

    def f(kind):
        for ext in ("jpg", "png"):
            pth = os.path.join(d, f"{tex_id}_{kind}_{res}.{ext}")
            if os.path.exists(pth):
                return pth
        return None
    return mat_image(f("diffuse"), name=name or tex_id, normal_path=f("nor_gl"), rough_path=f("rough"), **kw)


# ----------------------------------------------------------------------------
# World & lights
# ----------------------------------------------------------------------------
class WorldRig:
    """Handles for animating the world: .mapping (rotation input), .light_bg (strength), .cam_bg."""

    def __init__(self, world, mapping=None, light_bg=None, cam_bg=None, env=None, mix=None):
        self.world, self.mapping, self.light_bg, self.cam_bg, self.env, self.mix = (
            world, mapping, light_bg, cam_bg, env, mix)

    def key_rotation(self, frame, deg_z):
        inp = self.mapping.inputs["Rotation"]
        inp.default_value[2] = math.radians(deg_z)
        inp.keyframe_insert("default_value", index=2, frame=frame)

    def key_strength(self, frame, value):
        inp = self.light_bg.inputs["Strength"]
        inp.default_value = value
        inp.keyframe_insert("default_value", frame=frame)


def world_hdri(path, strength=1.0, rot_z=0.0, camera_bg="cream", camera_bg_strength=1.0, saturation=1.0,
               glossy_sees_bg=False):
    """HDRI lighting. camera_bg: palette colour shown to camera rays (clean pastel backdrop), or None to
    show the HDRI itself. glossy_sees_bg=True makes reflections show camera_bg instead of the HDRI."""
    w = bpy.context.scene.world
    w.use_nodes = True
    nt = w.node_tree
    n, l = nt.nodes, nt.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_z)
    env = n.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    env.interpolation = "Cubic"
    l.new(tc.outputs["Generated"], mp.inputs["Vector"])
    l.new(mp.outputs[0], env.inputs["Vector"])
    src = env.outputs["Color"]
    if saturation != 1.0:
        hsv = n.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = saturation
        l.new(src, hsv.inputs["Color"])
        src = hsv.outputs["Color"]
    bg = n.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    l.new(src, bg.inputs["Color"])
    cam_bg = mix = None
    if camera_bg is not None:
        cam_bg = n.new("ShaderNodeBackground")
        cam_bg.inputs["Color"].default_value = col(camera_bg)
        cam_bg.inputs["Strength"].default_value = camera_bg_strength
        lp = n.new("ShaderNodeLightPath")
        mix = n.new("ShaderNodeMixShader")
        fac = lp.outputs["Is Camera Ray"]
        if glossy_sees_bg:
            mx = n.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            l.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
            l.new(lp.outputs["Is Glossy Ray"], mx.inputs[1])
            fac = mx.outputs[0]
        l.new(fac, mix.inputs["Fac"])
        l.new(bg.outputs[0], mix.inputs[1])
        l.new(cam_bg.outputs[0], mix.inputs[2])
        l.new(mix.outputs[0], out.inputs["Surface"])
    else:
        l.new(bg.outputs[0], out.inputs["Surface"])
    return WorldRig(w, mp, bg, cam_bg, env, mix)


def world_color(color="cream", strength=1.0):
    w = bpy.context.scene.world
    w.use_nodes = True
    n, l = w.node_tree.nodes, w.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")
    bg = n.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = col(color)
    bg.inputs["Strength"].default_value = strength
    l.new(bg.outputs[0], out.inputs["Surface"])
    return WorldRig(w, None, bg, None)


def light(kind="AREA", name=None, location=(0, 0, 3), target=(0, 0, 0), power=500.0, color="white",
          size=2.0, size_y=None, shape="RECTANGLE", radius=0.05, spot_deg=45.0, blend=0.3,
          caustics=False, camera_visible=False, temperature=None):
    """kind: AREA | POINT | SPOT | SUN. power in W (sun: strength). Points at `target`."""
    ld = bpy.data.lights.new(name or kind.lower(), kind)
    ld.color = col(color)[:3]
    ld.energy = power
    if kind == "AREA":
        ld.shape = shape
        ld.size = size
        if size_y is not None:
            ld.size_y = size_y
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = radius
        if kind == "SPOT":
            ld.spot_size = math.radians(spot_deg)
            ld.spot_blend = blend
    elif kind == "SUN":
        ld.angle = math.radians(size)
    ld.cycles.is_caustics_light = caustics
    ob = link(bpy.data.objects.new(name or kind.lower(), ld))
    ob.location = location
    ob.visible_camera = camera_visible
    if target is not None:
        look_at(ob, target)
    return ob


def studio_rig(target=(0, 0, 0.5), scale=1.0, key="white", fill="white", rim="white", key_power=900.0,
               warm_cool=True):
    """Soft three-point softbox rig tuned for tactile objects (large sources, gentle shadows)."""
    s = scale
    k = light("AREA", "Key", (-3.2 * s, -3.0 * s, 4.2 * s), target, key_power * s * s,
              "#FFF1E0" if warm_cool and key == "white" else key, size=3.2 * s)
    f = light("AREA", "Fill", (3.8 * s, -2.4 * s, 2.0 * s), target, key_power * 0.35 * s * s,
              "#E6F0FF" if warm_cool and fill == "white" else fill, size=4.0 * s)
    r = light("AREA", "Rim", (1.0 * s, 4.0 * s, 4.5 * s), target, key_power * 0.6 * s * s, rim, size=2.5 * s)
    return k, f, r


# ----------------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------------
def camera(name="Cam", location=(0, -8, 3), target=(0, 0, 0.6), lens=50.0, fstop=None, focus=None,
           sensor=36.0, clip_end=500.0):
    """Camera with a TRACK_TO target empty (animate either). fstop enables DOF focused on `focus`
    (object/empty) or the target empty."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.01
    cd.clip_end = clip_end
    ob = link(bpy.data.objects.new(name, cd))
    ob.location = location
    tgt = empty(name + "_target", target, kind="SPHERE", size=0.1)
    c = ob.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_object = focus or tgt
    bpy.context.scene.camera = ob
    return ob, tgt


# ----------------------------------------------------------------------------
# Animation
# ----------------------------------------------------------------------------
def clamp01(t):
    return 0.0 if t < 0 else (1.0 if t > 1 else t)


def prog(f, f0, f1):
    """Normalised progress of frame f through [f0, f1], clamped."""
    return clamp01((f - f0) / float(f1 - f0)) if f1 != f0 else float(f >= f1)


def lerp(a, b, t):
    if isinstance(a, (tuple, list, Vector)):
        return type(a)(x + (y - x) * t for x, y in zip(a, b)) if not isinstance(a, Vector) else a.lerp(b, t)
    return a + (b - a) * t


def smoothstep(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def smootherstep(t):
    t = clamp01(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def ease_in_out_cubic(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_cubic(t):
    return 1 - (1 - clamp01(t)) ** 3


def ease_in_cubic(t):
    return clamp01(t) ** 3


def ease_in_out_sine(t):
    return -(math.cos(math.pi * clamp01(t)) - 1) / 2


def ease_out_back(t, s=1.70158):
    t = clamp01(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def ease_out_elastic(t, period=0.3):
    t = clamp01(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t - period / 4) * (2 * math.pi) / period) + 1


def spring(t, freq=2.5, damping=5.0):
    """Damped spring from 0 -> 1 with overshoot. t in seconds-ish units (0..~1.5)."""
    if t <= 0:
        return 0.0
    return 1 - math.exp(-damping * t) * math.cos(2 * math.pi * freq * t)


def bounce_height(t, h0=1.0, restitution=0.55, g=1.0):
    """Height of a ball dropped from h0 bouncing on z=0, at normalised time t (>=0)."""
    v = math.sqrt(2 * g * h0)
    tt = t
    # first fall
    t_fall = v / g
    if tt < t_fall:
        return h0 - 0.5 * g * tt * tt
    tt -= t_fall
    v *= restitution
    while v > 1e-3:
        t_hop = 2 * v / g
        if tt < t_hop:
            return v * tt - 0.5 * g * tt * tt
        tt -= t_hop
        v *= restitution
    return 0.0


def _anim_id(target):
    """Owner ID that carries the animation data (sockets/sub-structs -> their ID)."""
    ad = getattr(target, "animation_data", None)
    if ad is not None or not hasattr(target, "id_data"):
        return target
    return target.id_data


def key(target, data_path, frame, value=None, index=-1, interp="BEZIER", easing="AUTO"):
    """Insert a keyframe (optionally setting the value first) and set its interpolation.
    Works for objects, data blocks and node sockets (e.g. key(socket, "default_value", 10, 2.0))."""
    if value is not None:
        cur = target.path_resolve(data_path)
        if index >= 0:
            cur[index] = value
        elif hasattr(cur, "__len__") and not isinstance(value, (int, float)):
            for i, v in enumerate(value):
                cur[i] = v
        else:
            setattr_path(target, data_path, value)
    target.keyframe_insert(data_path, index=index, frame=frame)
    full = target.path_from_id(data_path) if hasattr(target, "path_from_id") else data_path
    owner = _anim_id(target)
    ad = getattr(owner, "animation_data", None)
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            if fc.data_path == full and (index < 0 or fc.array_index == index):
                for kp in fc.keyframe_points:
                    if abs(kp.co.x - frame) < 1e-4:
                        kp.interpolation = interp
                        kp.easing = easing


def setattr_path(target, data_path, value):
    if "." in data_path:
        head, attr = data_path.rsplit(".", 1)
        setattr(target.path_resolve(head), attr, value)
    elif data_path.startswith("["):
        target[data_path[2:-2]] = value
    else:
        setattr(target, data_path, value)


def _fcurves(action):
    """Blender 4.4+ layered actions: gather fcurves from all channelbags; fall back to action.fcurves."""
    out = []
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
    except AttributeError:
        pass
    if not out and hasattr(action, "fcurves"):
        out = list(action.fcurves)
    return out


def bake(target, data_path, f0, f1, fn, index=-1, step=1):
    """Per-frame keys: value = fn(frame). Everything LINEAR so the curve is exactly fn.
    For vector paths with index=-1, fn must return a sequence."""
    for f in range(int(f0), int(f1) + 1, step):
        v = fn(f)
        cur = target.path_resolve(data_path)
        if index >= 0:
            cur[index] = v
        elif hasattr(cur, "__len__"):
            for i, x in enumerate(v):
                cur[i] = x
        else:
            setattr_path(target, data_path, v)
        target.keyframe_insert(data_path, index=index, frame=f)
    linearize(target)


def linearize(target):
    ad = getattr(_anim_id(target), "animation_data", None)
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def hide_range(ob, visible_from=None, visible_to=None):
    """Render-visibility keys: visible only in [visible_from, visible_to] (either may be None)."""
    def k(f, hidden):
        ob.hide_render = hidden
        ob.hide_viewport = hidden
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
    if visible_from is not None:
        k(1, True)
        k(visible_from, False)
    if visible_to is not None:
        k(visible_to + 1, True)
        if visible_from is None:
            k(1, False)


# ----------------------------------------------------------------------------
# CLI / render driver
# ----------------------------------------------------------------------------
def parse_args(argv=None):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="preview", choices=["preview", "final", "draft"],
                    help="draft: 25%% res 32spp; preview: 50%% res 128spp; final: full res, shot samples")
    ap.add_argument("--frames", default=None,
                    help="'1-300', '1,40,80', '1-300:10' (every 10th). Default: whole shot")
    ap.add_argument("--out", default=None, help="output directory for frames")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--pct", type=int, default=None, help="resolution percentage override")
    ap.add_argument("--save-blend", default=None)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--backend", default=os.environ.get("CYCLES_BACKEND", "CUDA"))
    ap.add_argument("--prefix", default="f_")
    return ap.parse_args(argv)


def parse_frames(spec, f0, f1):
    if not spec:
        return list(range(f0, f1 + 1))
    step = 1
    if ":" in spec:
        spec, s = spec.split(":")
        step = int(s)
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1, step))
        else:
            out.append(int(part))
    return out


MODES = {  # mode -> (resolution pct, samples multiplier/override, adaptive threshold)
    "draft": (25, 32, 0.05),
    "preview": (50, 128, 0.03),
    "final": (100, None, None),
}


def finish(args, final_samples=512, final_threshold=0.01, frame_end=None, out_default=None,
           shot_name="shot"):
    sc = bpy.context.scene
    if frame_end is not None:
        sc.frame_end = frame_end
    pct, spp, thr = MODES[args.mode]
    c = sc.cycles
    c.samples = args.samples or (spp if spp else final_samples)
    c.adaptive_threshold = thr if thr else final_threshold
    sc.render.resolution_percentage = args.pct or pct
    if args.mode != "final":  # 8-bit dithered previews (16-bit PNGs can look banded in image viewers)
        sc.render.image_settings.color_depth = "8"
    enable_gpu(args.backend)
    if args.save_blend:
        os.makedirs(os.path.dirname(os.path.abspath(args.save_blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_blend))
    if args.no_render:
        return
    out = args.out or out_default or os.path.join(ROOT, "renders", args.mode, shot_name)
    os.makedirs(out, exist_ok=True)
    frames = parse_frames(args.frames, sc.frame_start, sc.frame_end)
    import time
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f"{args.prefix}{f:04d}")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"[dopa] {shot_name} frame {f} -> {sc.render.filepath}.png  {time.time() - t:.1f}s", flush=True)
