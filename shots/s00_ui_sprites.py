"""s00_ui_sprites: Cycles-rendered candy UI sprites for the caption overlay (stills, not part of the film).

Run (GPU 7 only; dopa refuses to render without the prefix):
    CUDA_VISIBLE_DEVICES=7 tools/blender/blender -b --factory-startup -P shots/s00_ui_sprites.py
    ... -P shots/s00_ui_sprites.py -- --only pill,chip --samples 1024      (subset / quality override)

Writes 16-bit RGBA PNGs (straight alpha, sRGB display-referred through the film's Khronos PBR Neutral view):
    assets/ui/pill.png         horizontal candy capsule, body 120 px high = 2x of the 60 px caption pill
    assets/ui/chip.png         same capsule, body 96 px high = 2x of the 48 px instrument chip
    assets/ui/dot_<c>.png      candy spheres, 96 px diameter on a 192 px canvas, c in blue mint coral lemon white lime
    assets/ui/sprites.json     exact geometry (body boxes, cap widths, sphere centres) for make_overlays.py

Scene: ortho camera straight down, transparent film, a shadow-catcher plane under the toy, a light-path studio
world (uniform for diffuse rays, a smooth dome for glossy rays) plus two sun lamps. Every light is at infinity,
so shading depends on the surface normal only and the capsule's straight middle is identical along X:
make_overlays.py can 3-slice it (left cap | 1-px middle | right cap) without a seam.

Deviations from storyboard 2.5 / 5.3 (visual tuning allowed by Lead decision 3):
  * The capsule is flattened to 62% depth (an inflated lozenge). A fully round capsule read as a tube/rod
    from the top; the flattened one reads as a squishy candy sticker with a broad lit face.
  * Lifted 0.03 m off the catcher so the baked shadow separates a little (sticker-on-paper float).
  * A second, shadowless, glossy-only sun draws the crisp candy-coat streak; the key sun (large angle) gives
    the soft drop shadow toward the bottom of the frame (14 deg from the zenith for the dots, 28 for capsules).
  * Dots sit on a 192 px canvas (sphere 96 px) so their ambient halo never reaches the sprite border.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

import bpy  # noqa: E402

OUT = os.path.join(D.ROOT, "assets", "ui")
DOT_COLOURS = ["blue", "mint", "coral", "lemon", "white", "lime"]


def parse():
    import argparse
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="pill,chip,dots", help="comma list of pill, chip, dots")
    ap.add_argument("--samples", type=int, default=768)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--exposure", type=float, default=0.0)
    return ap.parse_args(argv)


A = parse()
os.makedirs(A.out, exist_ok=True)

D.reset_scene()
sc = bpy.context.scene
D.setup_cycles(samples=A.samples, threshold=0.002, min_samples=128, diffuse=6, glossy=6, transmission=4,
               caustics=False, clamp_indirect=4.0, motion_blur=False)
D.setup_color(exposure=A.exposure)
sc.render.film_transparent = True
sc.render.filter_size = 1.2
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.render.image_settings.color_depth = "16"
sc.render.image_settings.compression = 15
sc.render.resolution_percentage = 100
sc.cycles.seed = 0

# --- world + lights (all at infinity -> X-invariant shading on the capsule's straight section) -----------------
def studio_dome_world(diffuse_strength=0.62, dome_top=1.45, dome_horizon=0.22):
    """Light-path world. Diffuse/shadow rays see a uniform neutral sky (so the catcher only gets a symmetric
    soft contact halo, never a directional HDRI shadow reaching the sprite border); glossy rays see a smooth
    studio dome (bright zenith -> dim horizon), which gives one broad clean highlight instead of HDRI glints."""
    w = sc.world
    w.use_nodes = True
    n, l = w.node_tree.nodes, w.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")
    flat = n.new("ShaderNodeBackground")
    flat.inputs["Color"].default_value = D.col("#F4F4F8")
    flat.inputs["Strength"].default_value = diffuse_strength
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Generated"], sep.inputs[0])
    mr = n.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.95
    mr.inputs["To Min"].default_value = dome_horizon
    mr.inputs["To Max"].default_value = dome_top
    l.new(sep.outputs["Z"], mr.inputs["Value"])
    dome = n.new("ShaderNodeBackground")
    dome.inputs["Color"].default_value = D.col("#F7F7FB")
    l.new(mr.outputs["Result"], dome.inputs["Strength"])
    lp = n.new("ShaderNodeLightPath")
    mix = n.new("ShaderNodeMixShader")
    l.new(lp.outputs["Is Glossy Ray"], mix.inputs["Fac"])
    l.new(flat.outputs[0], mix.inputs[1])
    l.new(dome.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])


studio_dome_world()
key = D.light("SUN", "KeySun", location=(0, 0, 10), target=None, power=2.4, color="#FFFCF8", size=34.0)
key.rotation_euler = (math.radians(-28), 0, 0)          # light travels toward -Y: shadow falls to frame-bottom
spec = D.light("SUN", "SpecSun", location=(0, 0, 10), target=None, power=3.0, color="white", size=7.0)
spec.rotation_euler = (math.radians(-46), 0, 0)         # highlight streak on the upper face
spec.visible_diffuse = False                            # glossy-only: no extra shading, no shadow
spec.visible_transmission = False
spec.visible_volume_scatter = False
for owner, attr in ((spec.data, "use_shadow"), (getattr(spec.data, "cycles", None), "cast_shadow")):
    if owner is not None and hasattr(owner, attr):
        setattr(owner, attr, False)

catcher = D.plane("Catcher", (60, 60), location=(0, 0, 0), mat=D.mat_clay("white"))
catcher.is_shadow_catcher = True

cam_data = bpy.data.cameras.new("UICam")
cam_data.type = "ORTHO"
cam_data.clip_start = 0.01
cam_data.clip_end = 100
cam = D.link(bpy.data.objects.new("UICam", cam_data))
cam.location = (0, 0, 20)
cam.rotation_euler = (0, 0, 0)                          # looks down -Z, image up = +Y
sc.camera = cam

FLAT = 0.62     # capsule depth / width
LIFT = 0.03     # metres off the catcher (radius 0.5 m = half the body height)


def frame_camera(width_m, height_m, centre, px_per_m):
    """Exact pixel scale: resolution = metres * px_per_m (integers), ortho_scale = larger side in metres."""
    W, H = round(width_m * px_per_m), round(height_m * px_per_m)
    sc.render.resolution_x, sc.render.resolution_y = W, H
    cam_data.ortho_scale = max(W, H) / px_per_m
    cam_data.sensor_fit = "AUTO"
    cam.location = (centre[0], centre[1], 20)
    return W, H


def show_only(obs):
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob is not catcher:
            ob.hide_render = ob not in obs


def render_to(name):
    path = os.path.join(A.out, name)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[s00] wrote {path}", flush=True)
    return path


meta = {"scale": 2, "note": "pixel geometry of each sprite; boxes are [x0, y0, x1, y1] from the top-left"}


def capsule_sprite(name, body_px, length_m=4.0, margin=(10 / 24, 8 / 24, 10 / 24, 15 / 24)):
    """Capsule of radius 0.5 m (body height 1 m = body_px pixels), long axis X. margin = (left, top, right,
    bottom) in metres around the body for the baked shadow."""
    ob = D.capsule(name, 0.5, length_m, location=(0, 0, 0.5 * FLAT + LIFT), rotation=(0, 90, 0),
                   mat=D.mat_candy("white", name=f"candy_white_{name}", rough=0.25), segments=128, rings=64)
    ob.scale = (FLAT, 1.0, 1.0)                          # local X == world Z after the 90 deg Y rotation
    show_only([ob])
    ml, mt, mr, mb = margin
    width_m = length_m + ml + mr
    height_m = 1.0 + mt + mb
    cx = (mr - ml) / 2.0                                  # image centre relative to the body centre
    cy = (mt - mb) / 2.0
    W, H = frame_camera(width_m, height_m, (cx, cy), body_px)
    render_to(f"{name}.png")
    # body box in pixels (exact: the camera centre maps to (W/2, H/2), +Y is up)
    x0 = W / 2 + (-length_m / 2 - cx) * body_px
    x1 = W / 2 + (length_m / 2 - cx) * body_px
    y0 = H / 2 - (0.5 - cy) * body_px
    y1 = H / 2 - (-0.5 - cy) * body_px
    meta[name] = {"file": f"{name}.png", "size": [W, H], "body": [x0, y0, x1, y1], "body_h": body_px,
                  "cap": body_px / 2.0, "straight": [x0 + body_px / 2.0, x1 - body_px / 2.0]}
    ob.hide_render = True


def dot_sprites(diam_px=96, img_px=192, key_tilt=14.0):
    """Candy spheres. The key comes from nearer the zenith than for the capsules (14 deg instead of 28) so a
    22 px bead gets a tight contact shadow instead of a long cast one, and the canvas is 2x the diameter so the
    shadow and the ambient halo fade out well inside the sprite."""
    meta["dots"] = {}
    old_rot = tuple(key.rotation_euler)
    key.rotation_euler = (math.radians(-key_tilt), 0, 0)
    for c in DOT_COLOURS:
        ob = D.sphere(f"Dot_{c}", 0.5, location=(0, 0, 0.5 + 0.01),
                      mat=D.mat_candy(c, name=f"candy_dot_{c}", rough=0.2), segments=128, rings=64)
        show_only([ob])
        frame_camera(img_px / diam_px, img_px / diam_px, (0, 0), diam_px)
        render_to(f"dot_{c}.png")
        meta["dots"][c] = {"file": f"dot_{c}.png", "size": [img_px, img_px],
                           "center": [img_px / 2.0, img_px / 2.0], "diameter": diam_px}
        ob.hide_render = True
    key.rotation_euler = old_rot


only = set(A.only.split(","))
if "pill" in only:
    capsule_sprite("pill", 120, length_m=4.0)
if "chip" in only:
    capsule_sprite("chip", 96, length_m=4.0)
if "dots" in only:
    dot_sprites()

mp = os.path.join(A.out, "sprites.json")
old = {}
if os.path.exists(mp):
    try:
        with open(mp) as fh:
            old = json.load(fh)
    except (OSError, ValueError):
        old = {}
old.update(meta)
with open(mp, "w") as fh:
    json.dump(old, fh, indent=1)
print(f"[s00] wrote {mp}", flush=True)
