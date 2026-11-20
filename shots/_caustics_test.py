"""Tech test: caustic quality vs samples, MNEE on/off, fake-dispersion glass. Not part of the film.
env: MNEE=1 to enable Cycles shadow caustics; DISP=1 for dispersive glass."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import dopa as D  # noqa: E402

args = D.parse_args()
D.reset_scene()
D.setup_cycles(samples=1024, clamp_indirect=0.0, filter_glossy=0.0)
D.setup_color()
D.setup_output()
sc = D.bpy.context.scene
sc.frame_end = 1
mnee = os.environ.get("MNEE") == "1"
disp = os.environ.get("DISP") == "1"

floor_mat = D.mat_clay(os.environ.get("FLOOR","cream"), rough=0.6, sss=0.0, sheen=0.05)
cyc = D.cyclorama(mat=floor_mat, wall_y=4.0, radius=2.0)
D.world_color("pistachio", float(os.environ.get("AMB","0.25")))
glass = (lambda c: D.mat_glass_dispersive(c, spread=0.03)) if disp else (lambda c: D.mat_glass(c))
objs = [
    D.stanford_bunny("bunny", 1.0, glass("white"), location=(0, 0.3, 0), rotation=(0, 0, 25)),
    D.sphere("s_pink", 0.35, (-1.3, -0.2, 0.35), D.mat_glass("pink", absorb=2.0)),
    D.sphere("s_lemon", 0.3, (1.25, -0.4, 0.3), D.mat_glass("lemon", absorb=2.0)),
    D.torus("t_aqua", 0.32, 0.11, (1.0, 0.9, 0.11), mat=D.mat_glass("aqua", absorb=2.0)),
]
spot = D.light("SPOT", "Key", location=tuple(float(v) for v in os.environ.get("LPOS","-2.2,-1.2,4.2").split(",")), target=(0, 0.2, 0), power=float(os.environ.get("POW","4000")), color="white",
               radius=0.04, spot_deg=55, blend=0.4, caustics=mnee)
D.light("AREA", "Fill", location=(3, -3, 3), target=(0, 0, 0.4), power=120, color="sky", size=4)
if mnee:
    for o in objs:
        o.cycles.is_caustics_caster = True
    cyc.cycles.is_caustics_receiver = True
D.camera(location=(0.4, -6.5, 2.6), target=(0, 0.2, 0.35), lens=50, fstop=5.6)
D.finish(args, final_samples=1024, shot_name="caustics_test")
