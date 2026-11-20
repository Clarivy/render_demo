"""Kit smoke test: exercises every dopa helper builders will rely on. Not part of the film."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=256)
D.setup_color()
D.setup_output()
sc = D.bpy.context.scene
sc.frame_end = 30

t0 = time.time()
room = D.diorama_corner("Room", size=4.0, height=3.0,
                        floor_mat=D.polyhaven_texture("floor_tiles_06", uv_scale=2.0),
                        left_mat=D.mat_clay("blush"), right_mat=D.mat_clay("butter"))
print("TIMING room", round(time.time() - t0, 2))

t0 = time.time()
paint = D.mat_image(os.path.join(D.ASSETS, "paintings", "seurat_grande_jatte_20000.jpg"), name="seurat", rough=0.6)
frame = D.rounded_box("frame", (1.62, 0.08, 1.12), 0.03, location=(0, 1.35, 1.6), rotation=(0, 0, 0),
                      mat=D.mat_metal("gold", rough=0.25))
canvas = D.plane("canvas", (1.5, 1.0), location=(0, 1.30, 1.6), rotation=(90, 0, 0), mat=paint)
print("TIMING painting", round(time.time() - t0, 2))

t0 = time.time()
duck_root, duck_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "rubber_duck_toy", "rubber_duck_toy_4k.gltf"))
duck_root.location = (-0.6, -0.3, 0.0)
duck_root.scale = (2.5, 2.5, 2.5)
mag_root, mag_meshes = D.import_gltf(os.path.join(D.ASSETS, "models", "magnifying_glass_01", "magnifying_glass_01_4k.gltf"))
mag_root.location = (0.8, -0.6, 0.3)
mag_root.scale = (2.0, 2.0, 2.0)
print("TIMING gltf", round(time.time() - t0, 2), "duck meshes", len(duck_meshes), "mag meshes", len(mag_meshes))

ball = D.sphere("ball", 0.3, (0.3, 0.2, 0.3), D.mat_metal("chrome"))
D.bake(ball, "location", 1, 30, lambda f: (0.3, 0.2, 0.3 + 1.2 * D.bounce_height(f / 30 * 2.2, 1.0, 0.5, 1.0)))
D.bake(ball, "scale", 1, 30, lambda f: (1.0, 1.0, 1.0))
cube = D.rounded_box("cube", (0.4, 0.4, 0.4), 0.1, location=(-0.2, 0.6, 0.2), mat=D.mat_jelly("pink"))
D.key(cube, "rotation_euler", 1, (0, 0, 0))
D.key(cube, "rotation_euler", 30, (0, 0, math.radians(180)), interp="BEZIER", easing="EASE_IN_OUT")
D.hide_range(cube, visible_from=10)

rig = D.world_hdri(D.HDRI["colorful_studio"], strength=1.0, camera_bg="lavender")
D.bake(rig.mapping.inputs["Rotation"], "default_value", 1, 30, lambda f: f * 12.0 * math.pi / 180, index=2)
D.light("POINT", "orb", location=(-0.8, -0.5, 1.2), power=80, color="lemon", radius=0.05)
D.text3d("LaRenderer", font="fredoka", size=0.45, location=(0, -0.9, 0.25), mat=D.mat_candy("pink"))
D.camera(location=(0, -6.5, 2.6), target=(0, 0.4, 0.9), lens=40, fstop=4.0)

# verify keyed values
for f in (1, 15, 30):
    sc.frame_set(f)
    print("CHECK frame", f, "ball z", round(ball.location.z, 3), "world rotZ deg",
          round(math.degrees(rig.mapping.inputs["Rotation"].default_value[2]), 1),
          "cube rotZ", round(math.degrees(cube.rotation_euler.z), 1), "cube hidden", cube.hide_render)
D.finish(args, shot_name="kit_test")
