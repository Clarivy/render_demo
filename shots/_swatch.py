"""Style calibration: every dopa material on a pastel cyclorama + 3D title. Not part of the film."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=256)
D.setup_color()
D.setup_output()
sc = D.bpy.context.scene
sc.frame_end = 1

D.cyclorama(mat=D.mat_clay("lavender", rough=0.7, sss=0.0, sheen=0.1), wall_y=3.0, radius=2.5)
D.world_hdri(D.HDRI["studio_small_09"], strength=0.6, camera_bg="lavender")
D.studio_rig(target=(0, 0, 0.5), key_power=700)

row1 = [
    ("clay", D.mat_clay("pink")), ("candy", D.mat_candy("orange")), ("rubber", D.mat_rubber("lemon")),
    ("velvet", D.mat_velvet("mint")), ("chrome", D.mat_metal("chrome")), ("pinkmetal", D.mat_metal("pink", rough=0.12)),
]
row2 = [
    ("irid", D.mat_iridescent("white")), ("glass", D.mat_glass("white")),
    ("dglass", D.mat_glass_dispersive("white")), ("tglass", D.mat_glass("blue", absorb=1.5)),
    ("jelly", D.mat_jelly("coral")), ("emit", D.mat_emission("aqua", 6.0)),
]
for i, (n, m) in enumerate(row1):
    x = -3.0 + i * 1.2
    if i % 2:
        D.rounded_box(n, (0.8, 0.8, 0.8), 0.18, location=(x, 0.6, 0.4), mat=m, soft=(i == 3))
    else:
        D.sphere(n, 0.42, (x, 0.6, 0.42), m)
for i, (n, m) in enumerate(row2):
    x = -3.0 + i * 1.2
    if i == 4:
        D.capsule(n, 0.3, 0.9, (x, -0.8, 0.3), rotation=(0, 90, 20), mat=m)
    elif i == 1:
        D.stanford_bunny(n, 0.85, m, location=(x, -0.8, 0.0), rotation=(0, 0, 20))
    else:
        D.sphere(n, 0.38, (x, -0.8, 0.38), m)
D.torus("ring", 0.35, 0.12, (3.6, 0.6, 0.12), mat=D.mat_candy("violet"))
D.text3d("NEURAL RENDER", font="fredoka", size=0.55, extrude=0.08, bevel=0.035,
         location=(0, 2.2, 1.6), mat=D.mat_candy("blue"))
D.camera(location=(0, -9.5, 3.2), target=(0, 0.2, 0.7), lens=45, fstop=8.0)
D.finish(args, final_samples=256, shot_name="swatch")
