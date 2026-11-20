"""S02 · s02_caustics — "Jewel-box" (capability C2: caustics, glass, mirrors).

Film frames 241-420 = local 1-180 = bars 5-7 (8.0-14.0 s).  Cameras: wide W (f1-60, f121-180) and
floor macro M (f61-120), switched with timeline markers bound to cameras (no key-jumped camera).

What the shot proves
--------------------
One small visible light (the orb, a SPOT r 0.05 inside a camera/glossy-only halo) is the only key, so every
caustic traces back to it.  Plain path tracing (no MNEE).  Each glass candy throws its tinted caustic the
moment it lands on the beat: lemon focal spot (f31), pink heart caustic (f46), aqua ring caustic (f61, cut to
macro on the impact); the dispersive crystal bunny throws rainbow sparkle onto its plinth.  In the macro the orb
clicks left on the beats (f76/f91/f106) and every caustic jumps, stretches and refocuses (they cannot be decals);
the chrome swirl and the mirror ball show chained specular transport; the shot ends pushing into the mirror ball
(circle match to S03).

ROUND 2 CHANGELOG (lead notes r2 + critic review; hit frames, transitions, proofs, pipeline unchanged)
-----------------------------------------------------------------------------------------------------
Look ("no grey", lead S02-1/5/8, G2; critic grey-mud, hero colours, cut-out brightness)
 R1. Wall washes: two AREA lights light-linked (receiver = that wall only), glossy + transmission invisible, so
     the walls read saturated mint (V ~0.8) / pistachio (V ~0.85) without lighting the pool or the casters.  The
     walls are invisible to diffuse rays, so their brighter bounce cannot green the floor or the shadows.
     (No shadow linking: blocker collections cost a dedicated light sample per bounce, +34-41 % render time.)
 R2. Fill cream 8 W -> lilac-violet #A890FF 14 W (~12 % of the key on the pool): shadows read lavender, not grey.
     Floor clay cream #FFF6EC -> warm cream-butter #FFF0CC (reads pastel; caustic hues stay true, unlike butter).
 R3. Coral kicker 20 W: AREA light-linked to MBPed only (front-right): candy coral instead of oxblood.
 R4. Key 21 -> 19 W, spot 120 deg / blend 0.35 -> 150 deg / 0.6 (broad soft pool, no dark museum vignette),
     OrbGlow 10 -> 14 W, exposure -0.3 -> -0.1 (the +0.2 lift lead S02-1 allows; caustic peaks stay < 0.97).
 R5. Out-cut (f160-180, ease_in_cubic, reflection-side only): glossy world 0.45 -> 1.0, fourth-wall card
     0.9 -> 2.0, Fill 14 -> 40 W, so the ball that cuts to S03's bright pink ball is bright and pastel.
 R6. G1 glow: S01's compositor block copied verbatim (Emit pass -> Glare BLOOM thr 0.6 / smooth 0.2 / strength 1
     / size 0.45 / HIGH, ADD over Image).  Only the camera-visible halo emits into the Emit pass.
 R7. Glass: lemon absorb 1.0 -> 0.5, tint_exp 0.35 -> 0.25 (lemon, not olive/amber); pink absorb 2.0 -> 1.0.
R18. FloorLift: a soft pale-lavender AREA from the camera side, light-linked to the floor slabs and the white
     props only (no glass receivers -> no extra caustics, no extra shadows): the periphery of the orb's pool reads
     pastel cream instead of taupe.  90 W in the wides, 30 W in the macro (only a slight shadow lift there, lead
     S02-5); it switches on the hard cuts.
Caustics (lead S02-2; critic bunny rainbow / heart)
 R8. Bunny + plinth (-0.88,0.62) r 0.30 -> (-0.72,0.55) r 0.42, dispersion spread 0.03 -> 0.07: the rainbow
     caustic lands on the white plinth top in front-left of the bunny under direct light (~53 deg incidence),
     visible in the wides.  Orb-to-bunny 0.95 m.
Motion (lead S02-7; critic cut-in, heart-crosses-orb, springy hits, macro static, push)
 R9. Orb fall: starts just above frame (z 1.72), ease_in_quad to z 0.95 at f14 (11.5 cm/f), then a
     velocity-matched damped dip 0.95 - A e^-10u sin(5 pi u) (A = v/(5 pi)): ~10 cm dip peaking on f16, settled
     by f28.  No f12-14 slam; the orb peeks in at f4, so the cut lands on action.
R10. Macro: the orb clicks LEFT 12 deg and 4 cm down on each beat f76 / f91 / f106 (S01's detent click profile),
     power x (z/0.95)^2 so the pool stays level; caustics travel INTO frame (lemon spot +130 px).  Back in the wide
     the orb swings home f122-136 (detent landing on the f136 beat).
R11. Heart drops in 0.42 m right of its stand (never crosses the orb on screen), smoothstep glide f37-46; rock
     8 -> 14 deg (still ends f61).  The stand pops up (POP spring 2.5 Hz / 8) at f38, static from f60.
R12. Ring: 3 cm restitution hop on the f61 impact (down by f65), wobble 5 -> 10 deg (ends f86).
R13. Push: the target pre-aims at the ball over f136-166 (detent settle into f166): one continuous move (peak pan
     0.76 deg/f instead of 1.75 deg/f).
Framing / continuity (critic macro framing, floor void, orb seam, swirl shadow)
R14. Cam M locked (no truck), still 75 mm high-angle; pulled back 0.4 m and 0.12 m left, target 5 cm lower:
     lemon spot >= 19 % from the left edge and >= 159 px above the caption pill all through the macro.
R15. FloorExt: an 8x8 m slab of the floor clay 1 mm under the room floor toward the camera: no slab edge / void.
R16. Swirl casts its shadow again (only its stick did); orb home x 0 -> -0.07 (clears the corner seam, ~70 px).
Render (lead S02-6, G4; critic blotch boiling)
R17. Per-segment sample policy, keyed on scene.cycles (CONSTANT) in final mode only (--samples overrides it):
     wides 768 spp adaptive (thr 0.01, min 64); macro f61-120 1536 spp with adaptive sampling OFF, so no pixel of
     the rare lemon-halo caustic paths stops early (that is what OIDN turned into boiling blotches).  Measured on
     GPU 7: wides 22-24 s/f, macro 45 s/f -> ~1.5 GPU-h for the shot (cap 1.6).  Gate f61-72: lemon-halo
     motion-compensated residual 0.68x the clean floor (round 1: 4.7x).

Round-1 deviations from the storyboard (still in force unless superseded above)
-------------------------------------------------------------------------------
 1. clamp_indirect 20 -> 0 (render setting).  20 is far below the orb's radiance (25 W over a 5 cm sphere
    ~ 250), so it scaled every refractive caustic sample down ~14x and the caustics vanished.
 2. Key 250 W -> 21 W (now 19, R4) + an omni "OrbGlow" POINT 10 W at the same point/radius, parented to the orb,
    spot 120 deg blend 0.35 aimed at (-0.25,-0.35,0).  During the fall both powers scale with (z/0.95)^1.3.
 3. Fill 60 W "sky" -> 8 W (now lilac, R2), aimed at (0,0.6,0.6).
 4. World: candy_sky_nosun 0.08 for diffuse/transmission rays but 0.45 for glossy rays (Light Path mix).
 5. Room size 3.4 -> 4.2, height 2.4 -> 2.5 (plus FloorExt, R15).
 6. Layout: casters in a V opening to the lens: heart stand (0,0.15), lemon (-0.48,-0.12), ring (0.50,-0.15);
    gold cone (-0.42,1.30); swirl (0.98,1.12) yawed -15 deg.  (Bunny/plinth: R8.)
 7. Casters: lemon r 0.13 -> 0.17; ring 0.15/0.05 -> 0.17/0.065.  Heart: inflated ("puffy candy") lens-shaped
    heart (34 cm tall, 5 cm thick, CDT outline with a filleted notch, subsurf 2) instead of the extruded slab.
 8. Glass tint: Principled base colour = colour^0.5 (candy_glass): Cycles tints at both interfaces.
 9. Cam W 40 -> 55 mm, target (0.05,0.35,0.60); push ends at d = 0.7896 m (exact 1536 px silhouette at 55 mm);
    camera baked to f181 so the f180 shutter blurs symmetrically; focus ends at ball_c + 0.06 u.
10. Cam M: 75 mm high-angle macro instead of the 85 mm floor-skimmer (caustic band unreadable at z 0.24).
11. Fourth-wall card 13x8 m centred on the ball's view axis at 7.2 m, emission 0.9 (sampling NONE).
12. Heart rock ends at its 2nd zero crossing (f61), ring wobble at its 5th (f86), then exactly 0 (decaying keys
    made Cycles treat meshes as moving every frame).  Heart object motion blur only while it falls (f<=46).
    Swirl: no object motion blur (0.5 deg/f).
13. Heart tip seated 12 mm into its stand; swirl gets a gold axle stick + hub behind the disc.

Debug: env S02_CAM=top|W|M forces a camera for every frame (top = orthographic layout check).
QA:    env S02_BALLMASK=1 renders a linear silhouette mask of the mirror ball (circle-match measurement).
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

SHOT = "s02_caustics"
N = 180
START = 241
FPS = 30.0

DEVIATIONS = []

args = D.parse_args()
D.reset_scene()
# clamp_indirect: the storyboard's 20 is far below the orb's radiance (25 W / 5 cm sphere ~ 250), so it scaled
# every refractive caustic sample down ~14x (caustics vanished).  The calibration (_caustics_test.py) used 0.
CLAMP_IND = float(os.environ.get("S02_CLAMP", "0"))
D.setup_cycles(samples=2048, threshold=0.01, min_samples=64, diffuse=int(os.environ.get("S02_DB", "4")),
               glossy=int(os.environ.get("S02_GB", "8")), transmission=int(os.environ.get("S02_TB", "16")),
               max_bounces=int(os.environ.get("S02_MB", "16")),
               caustics=True, filter_glossy=0.0, clamp_indirect=CLAMP_IND, motion_blur=True, shutter=0.5)
EXPOSURE = float(os.environ.get("S02_EXPO", "-0.1"))   # R4: +0.2 lift (lead S02-1 allows +0.2..+0.4)
D.setup_color(exposure=EXPOSURE)
D.setup_output()
sc = bpy.context.scene
sc.frame_start = 1
sc.frame_end = N
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
if os.environ.get("S02_NOMB"):
    sc.render.use_motion_blur = False

# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
V = Vector


def sec(f, f0):
    """Seconds since local frame f0."""
    return (f - f0) / FPS


def ray_only(ob, camera=True, glossy=True, diffuse=False, transmission=False, shadow=False, volume=False):
    ob.visible_camera = camera
    ob.visible_glossy = glossy
    ob.visible_diffuse = diffuse
    ob.visible_transmission = transmission
    ob.visible_shadow = shadow
    ob.visible_volume_scatter = volume
    return ob


def mesh_from_curve(cu_ob, name, mat=None):
    """Evaluate a curve object to a new mesh object, weld, recalc normals, delete the curve."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(cu_ob.evaluated_get(dg))
    me.name = name
    bpy.data.objects.remove(cu_ob, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = D.link(bpy.data.objects.new(name, me))
    D.assign(ob, mat)
    return ob


def candy_glass(color, absorb=2.0, absorb_color=None, name=None, tint_exp=0.5):
    """D.mat_glass with the surface tint set to sqrt(colour): Cycles applies the transmission tint at both
    interfaces of a closed solid, so the double crossing lands on the palette colour instead of its square
    (lemon^2 reads amber, pink^2 reads dark red).  Beer-Lambert absorption then deepens thick parts."""
    m = D.mat_glass(color, name=name, absorb=absorb, absorb_color=absorb_color)
    c = D.col(color)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        c[0] ** tint_exp, c[1] ** tint_exp, c[2] ** tint_exp, 1.0)
    return m


def non_manifold_count(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return n


def heart_outline(n=64, notch_r=6.0):
    """Closed heart polygon (curve units) with the top cusp replaced by a circular fillet of radius
    notch_r (a cusp cannot be bevelled: the offset folds into a long spike).  Resampled by arc length."""
    def P(t):
        return V((16 * math.sin(t) ** 3,
                  13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t), 0))

    def dP(t):
        return V((48 * math.sin(t) ** 2 * math.cos(t),
                  -13 * math.sin(t) + 10 * math.sin(2 * t) + 6 * math.sin(3 * t) + 4 * math.sin(4 * t), 0))

    def nout(t):            # t increases clockwise -> outward normal = (-y', x')
        d = dP(t)
        return V((-d.y, d.x, 0)).normalized()

    lo, hi = 1e-3, 1.2      # solve P(t).x + r*nout(t).x = 0 on the right branch
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if P(mid).x + notch_r * nout(mid).x > 0:
            hi = mid
        else:
            lo = mid
    ts = 0.5 * (lo + hi)
    C = P(ts) + notch_r * nout(ts)
    C.x = 0.0
    a_r = math.atan2((P(ts) - C).y, (P(ts) - C).x)           # right tangent point angle
    dense = [P(ts + (2 * math.pi - 2 * ts) * i / 2000) for i in range(2001)]
    a0, a1 = math.pi - a_r, 2 * math.pi + a_r              # left tangent -> bottom -> right tangent
    dense += [C + notch_r * V((math.cos(a0 + (a1 - a0) * i / 200), math.sin(a0 + (a1 - a0) * i / 200), 0))
              for i in range(1, 200)]
    cum = [0.0]
    for a, b in zip(dense, dense[1:] + dense[:1]):
        cum.append(cum[-1] + (b - a).length)
    L = cum[-1]
    out, j = [], 0
    for k in range(n):
        s_ = L * k / n
        while cum[j + 1] < s_:
            j += 1
        a, b = dense[j], dense[(j + 1) % len(dense)]
        w = (s_ - cum[j]) / max(1e-9, cum[j + 1] - cum[j])
        out.append(a.lerp(b, w))
    return out


def heart_mesh(name="PinkHeart", height=0.26, extrude=0.035, bevel=0.035, mat=None, n=96, notch_r=6.0):
    """Parametric heart (x=16sin^3 t, y=13cos t-5cos2t-2cos3t-cos4t) as a closed poly curve scaled to
    `height`, top cusp filleted, filled both sides, extruded + bevelled, to mesh + Subsurf 1 applied,
    smooth.  Local frame: heart in XY (lobes +Y), thickness along Z, origin at the TIP (rocking pivot)."""
    pts = heart_outline(n, notch_r)
    ys = [p.y for p in pts]
    s = height / (max(ys) - min(ys))
    y0 = min(ys)
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 6
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x * s, (p.y - y0) * s, 0.0, 1.0)
    sp.use_cyclic_u = True
    cob = D.link(bpy.data.objects.new(name + "_c", cu))
    ob = mesh_from_curve(cob, name, mat)
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    D.apply_modifiers(ob)
    me = ob.data
    ymin = min(v.co.y for v in me.vertices)
    me.transform(Matrix.Translation((0.0, -ymin, 0.0)))
    me.update()
    D.set_smooth(ob)
    return ob


def puffy_heart_mesh(name="PinkHeart", height=0.34, thick=0.10, mat=None, n=192, notch_r=6.0, grid=0.0045,
                     soft=0.006):
    """Inflated ("puffy candy") glass heart: the filleted heart outline scaled to `height`, filled with a
    constrained-Delaunay triangulation, then each surface lifted to z = +-(thick/2)*sqrt(s(2-s)) where s is a
    smooth (soft-min) distance to the outline normalised by its maximum.  Round rim, lens-like faces (so it
    FOCUSES the orb into a bright pink caustic instead of throwing a dim tinted shadow), watertight, smooth.
    Local frame: heart in XY (lobes +Y), thickness along Z, origin at the TIP (rocking pivot)."""
    from mathutils.geometry import delaunay_2d_cdt
    import numpy as np
    pts = heart_outline(n, notch_r)
    ys = [p.y for p in pts]
    sc_ = height / (max(ys) - min(ys))
    y0 = min(ys)
    poly = np.array([(p.x * sc_, (p.y - y0) * sc_) for p in pts])
    A, B = poly, np.roll(poly, -1, axis=0)

    def seg_dist(q):                         # q: (m,2) -> (m, nseg) distances to every outline segment
        ab = B - A
        t = ((q[:, None, :] - A[None]) * ab[None]).sum(-1) / (ab * ab).sum(-1)[None]
        t = np.clip(t, 0, 1)
        c = A[None] + t[..., None] * ab[None]
        return np.sqrt(((q[:, None, :] - c) ** 2).sum(-1))

    def inside(q):                           # even-odd rule
        x, y = q[:, 0][:, None], q[:, 1][:, None]
        xa, ya, xb, yb = A[:, 0][None], A[:, 1][None], B[:, 0][None], B[:, 1][None]
        cond = (ya > y) != (yb > y)
        xi = xa + (y - ya) * (xb - xa) / np.where(yb - ya == 0, 1e-12, yb - ya)
        return (cond & (x < xi)).sum(1) % 2 == 1

    def soft_d(q):                           # smooth inner distance (soft-min over segments)
        d = seg_dist(q)
        m = d.min(1, keepdims=True)
        return (m - soft * np.log(np.exp(-(d - m) / soft).sum(1, keepdims=True)))[:, 0].clip(0)

    # interior points: hex grid kept >= 0.6*grid from the outline, plus two inner offset rings for the rim
    xs = np.arange(poly[:, 0].min(), poly[:, 0].max() + grid, grid)
    ys_ = np.arange(poly[:, 1].min(), poly[:, 1].max() + grid, grid * 0.866)
    gp = np.array([(x + (0.5 * grid if j % 2 else 0.0), y) for j, y in enumerate(ys_) for x in xs])
    gp = gp[inside(gp)]
    gp = gp[seg_dist(gp).min(1) > 0.6 * grid]
    nrm = []
    for i in range(len(poly)):               # inward normals of the outline (polygon is clockwise)
        tng = poly[(i + 1) % len(poly)] - poly[i - 1]
        v = np.array([tng[1], -tng[0]])
        nrm.append(-v / np.linalg.norm(v))
    nrm = np.array(nrm)
    if not inside((poly + nrm * 1e-3)[:1])[0]:
        nrm = -nrm
    rings = [poly + nrm * off for off in (0.0012, 0.0035)]
    allp = np.vstack([poly] + rings + [gp])
    nb = len(poly)
    out = delaunay_2d_cdt([Vector((float(x), float(y))) for x, y in allp], [], [list(range(nb))], 1, 1e-7)
    verts2, faces2, orig = out[0], out[2], out[3]
    q = np.array([(v.x, v.y) for v in verts2])
    sd = soft_d(q)
    s_ = (sd / sd.max()).clip(0, 1)
    eps = 0.0006                                  # half-height of the thin side band that closes the rim
    h = np.maximum(0.5 * thick * np.sqrt(s_ * (2 - s_)), eps)
    rim_of = {}                                   # output vertex -> outline index
    for k, o in enumerate(orig):
        for i in o:
            if i < nb:
                rim_of[k] = i
    bm = bmesh.new()
    top = [bm.verts.new((x, y, eps if k in rim_of else hh)) for k, ((x, y), hh) in enumerate(zip(q, h))]
    bot = [bm.verts.new((x, y, -eps if k in rim_of else -hh)) for k, ((x, y), hh) in enumerate(zip(q, h))]
    for f in faces2:
        a, b, c = f[0], f[1], f[2]
        pa, pb, pc = q[a], q[b], q[c]
        if (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0]) < 0:
            b, c = c, b
        bm.faces.new((top[a], top[b], top[c]))
        bm.faces.new((bot[a], bot[c], bot[b]))
    rim_k = sorted(rim_of, key=lambda k: rim_of[k])
    for i in range(len(rim_k)):
        k0, k1 = rim_k[i], rim_k[(i + 1) % len(rim_k)]
        bm.faces.new((top[k0], bot[k0], bot[k1], top[k1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = D._mesh_object(name, bm, mat)
    if os.environ.get("S02_NOSUB"):
        return ob
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = int(os.environ.get("S02_HSUB", "2"))
    sub.render_levels = sub.levels
    D.apply_modifiers(ob)
    D.set_smooth(ob)
    return ob


def swirl_mesh(name="ChromeSwirl", r0=0.03, r1=0.30, turns=6.5, dome=0.04, tube=0.014, mat=None):
    """Archimedean spiral r0->r1 over `turns` in local XY, domed +Z (toward the viewer) by
    dome*(1-(r/r1)^2), swept with a round bevel (caps on) and converted to a mesh."""
    n = int(turns * 96)
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = tube
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    cu.resolution_u = 2
    sp = cu.splines.new("POLY")
    sp.points.add(n)
    for i in range(n + 1):
        u = i / n
        th = 2 * math.pi * turns * u
        r = r0 + (r1 - r0) * u
        z = dome * (1 - (r / r1) ** 2)
        sp.points[i].co = (r * math.cos(th), r * math.sin(th), z, 1.0)
    cob = D.link(bpy.data.objects.new(name + "_c", cu))
    ob = mesh_from_curve(cob, name, mat)
    D.set_smooth(ob)
    return ob


def chamfer_heart_mesh(name="PinkHeart", height=0.34, extrude=0.005, bevel=0.03, squash=0.35, mat=None, n=160,
                       notch_r=6.0, sharp_deg=12.0):
    """Flat glass heart plate with a crisp chamfer (prism ring) all round the filleted outline: a 2D curve,
    extruded + bevelled with bevel_resolution 0 (45 deg chamfer), then the thickness axis scaled by `squash`
    (chamfer ~ atan(squash) per face).  Smooth along the outline, split (sharp) at the chamfer edges.
    Same local frame as puffy_heart_mesh: heart in XY (lobes +Y), thickness along Z, origin at the TIP."""
    pts = heart_outline(n, notch_r)
    ys = [p.y for p in pts]
    s = (height - 2 * bevel) / (max(ys) - min(ys))
    y0 = min(ys)
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 0
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x * s, (p.y - y0) * s, 0.0, 1.0)
    sp.use_cyclic_u = True
    cob = D.link(bpy.data.objects.new(name + "_c", cu))
    ob = mesh_from_curve(cob, name, mat)
    me = ob.data
    ymin = min(v.co.y for v in me.vertices)
    me.transform(Matrix.Translation((0.0, -ymin, 0.0)))
    me.transform(Matrix.Diagonal((1.0, 1.0, squash, 1.0)))
    me.update()
    D.set_smooth(ob)
    me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    return ob


def linked_light(name, loc, target, power, color, size, receivers, glossy=False):
    """AREA light that lights ONLY `receivers` (light linking; shadow linking only with env S02_SHADOWLINK),
    invisible to transmission rays (and to glossy rays unless glossy=True)."""
    lt = D.light("AREA", name, loc, target, power=power, color=color, size=size)
    lt.visible_glossy = glossy
    lt.visible_transmission = False
    coll = bpy.data.collections.new(name + "_link")
    for ob in receivers:
        coll.objects.link(ob)
    lt.light_linking.receiver_collection = coll
    if os.environ.get("S02_SHADOWLINK"):     # shadow linking costs a dedicated light sample per bounce (slow)
        lt.light_linking.blocker_collection = coll
    return lt


def envf(name, dflt):
    return float(os.environ.get(name, str(dflt)))


def _v3e(name, dflt):
    return tuple(float(x) for x in os.environ.get(name, dflt).split(","))


# ----------------------------------------------------------------------------------------------
# set: mint jewel-box (teaser room 3, candied)
# ----------------------------------------------------------------------------------------------
ROOM_S = envf("S02_ROOM", 4.2)
FLOOR_MAT = D.mat_clay(os.environ.get("S02_FLOORC", "#FFF0CC"), name="clay_floor", rough=0.6, sss=0.0, sheen=0.05)
room = D.diorama_corner("Room", size=ROOM_S, height=2.5, floor_mat=FLOOR_MAT,
                        left_mat=D.mat_clay("mint"), right_mat=D.mat_clay("pistachio"), rot_z=45)
wallL, wallR = bpy.data.objects["Room_wallL"], bpy.data.objects["Room_wallR"]
if not os.environ.get("S02_WALLBOUNCE"):
    # the washed walls must not green the floor / fill the caster shadows with their bounce (R1)
    for _w in (wallL, wallR):
        _w.visible_diffuse = False
# floor extension toward the camera (R15): top 1 mm under the room floor, room-aligned (local frame of Room)
floor_ext = D.rounded_box("FloorExt", (8.0, 8.0, 0.18), 0.05, mat=FLOOR_MAT)
floor_ext.parent = room
floor_ext.location = (-2.0, -2.0, -0.09 - 0.001)

# crystal bunny on a wide low white plinth: its rainbow caustic lands on the plinth top (R8)
BUNNY_XY = tuple(float(x) for x in os.environ.get("S02_BUNNY", "-0.72,0.55").split(","))
PLINTH_R = envf("S02_PLINTH_R", 0.42)
plinth = D.cylinder("Plinth", PLINTH_R, 0.14, (BUNNY_XY[0], BUNNY_XY[1], 0), base_at_zero=True, bevel=0.03,
                    mat=D.mat_candy("white", rough=0.3))
bunny = D.stanford_bunny("CrystalBunny", 0.48, D.mat_glass("white") if os.environ.get("S02_BUNNYPLAIN")
                         else D.mat_glass_dispersive("white", spread=envf("S02_SPREAD", 0.07)),
                         location=(BUNNY_XY[0], BUNNY_XY[1], 0.14), rotation=(0, 0, 20))

# glass drop-ins
M_LEMON = candy_glass("lemon", absorb=envf("S02_ABS_LEMON", 0.5), tint_exp=envf("S02_LEMON_TEXP", 0.25))
M_PINK = candy_glass("pink", absorb=envf("S02_ABS_PINK", 1.0))
M_AQUA = candy_glass("aqua", absorb=envf("S02_ABS_AQUA", 2.0))
LEMON_R = envf("S02_LEMON_R", 0.17)
LEMON_XY = (-0.48, -0.12)
HEART_XY = (0.0, 0.15)
RING_XY = (0.50, -0.15)
lemon = D.sphere("LemonBall", LEMON_R, (LEMON_XY[0], LEMON_XY[1], LEMON_R), M_LEMON)
HEART_KIND = os.environ.get("S02_HEART", "puffy")
if HEART_KIND == "puffy":
    heart = puffy_heart_mesh("PinkHeart", envf("S02_HEART_H", 0.34), envf("S02_HEART_T", 0.05), mat=M_PINK)
elif HEART_KIND == "chamfer":
    heart = chamfer_heart_mesh("PinkHeart", envf("S02_HEART_H", 0.34), extrude=envf("S02_CH_EXT", 0.005),
                               bevel=envf("S02_CH_BEV", 0.03), squash=envf("S02_CH_SQ", 0.35), mat=M_PINK)
else:
    heart = heart_mesh("PinkHeart", 0.26, mat=M_PINK)
heart_stand = D.cylinder("HeartStand", 0.06, 0.05, (HEART_XY[0], HEART_XY[1], 0), base_at_zero=True,
                         bevel=0.015, mat=D.mat_candy("white"))
RING_R, RING_r = envf("S02_RING_R", 0.17), envf("S02_RING_RR", 0.065)
ring = D.torus("AquaRing", RING_R, RING_r, (RING_XY[0], RING_XY[1], RING_r), mat=M_AQUA)

# chrome swirl lollipop on a gold stick + white pedestal (back-right)
SW_C = V((0.98, 1.12, 0.76))
SW_YAW = math.radians(-15.0)                                # turn the disc a little toward the room centre
swirl_pivot = D.empty("SwirlPivot", tuple(SW_C))
swirl_pivot.rotation_euler = (math.radians(90), 0, SW_YAW)  # local +Z (dome) -> world -Y (camera)
swirl = swirl_mesh("ChromeSwirl", mat=D.mat_metal("chrome", rough=0.03))
swirl.parent = swirl_pivot
swirl.visible_shadow = not os.environ.get("S02_SWIRL_NOSHADOW")   # R16: the disc casts its shadow again
swirl.cycles.use_motion_blur = False      # 0.5 deg/frame spin: blur invisible, motion BVH expensive
GOLD_STICK = D.mat_metal("gold", rough=0.2)
swirl_ped = D.cylinder("SwirlPed", 0.12, 0.42, (SW_C.x, SW_C.y, 0), base_at_zero=True,
                       mat=D.mat_candy("white", rough=0.3))
_back = V((-math.sin(SW_YAW), math.cos(SW_YAW), 0)) * 0.03     # 3 cm behind the disc
stick = D.cylinder("SwirlStick", 0.012, SW_C.z - 0.42 + 0.01, (SW_C.x + _back.x, SW_C.y + _back.y, 0.415),
                   base_at_zero=True, bevel=0.0, mat=GOLD_STICK)
hub = D.sphere("SwirlHub", 0.022, (SW_C.x + _back.x, SW_C.y + _back.y, SW_C.z), GOLD_STICK)

# mirror ball on a coral pedestal (front-right) and the gold cone (back-left)
BALL_C = V((1.00, -0.40, 0.50))
BALL_R = 0.20
mball = D.sphere("MirrorBall", BALL_R, tuple(BALL_C), D.mat_metal("chrome", rough=0.0), segments=192, rings=96)
mb_ped = D.cylinder("MBPed", 0.13, 0.30, (1.00, -0.40, 0), base_at_zero=True, mat=D.mat_candy("coral"))
GCONE_XY = (-0.42, 1.30)
gcone = D.cone("GoldCone", 0.11, 0.28, (GCONE_XY[0], GCONE_XY[1], 0.14), mat=D.mat_metal("gold", rough=0.12))

# ----------------------------------------------------------------------------------------------
# light: the orb (key), lilac fill, wall washes + coral kicker (light-linked), world
# ----------------------------------------------------------------------------------------------
O_HOME = V((envf("S02_OX", -0.07), 0.85, 0.95))
O_Z = O_HOME.z
KEY_POWER = envf("S02_KEY", 19)
SPOT_DEG = envf("S02_SPOT", 150)
SPOT_BLEND = envf("S02_BLEND", 0.6)
orb = D.light("SPOT", "Orb", location=tuple(O_HOME), target=None, power=KEY_POWER, color="#FFF6E8",
              radius=envf("S02_LRAD", 0.05), spot_deg=SPOT_DEG, blend=SPOT_BLEND)
orb_aim = D.empty("OrbAim", tuple(float(x) for x in os.environ.get("S02_AIM", "-0.25,-0.35,0").split(",")))
tc = orb.constraints.new("TRACK_TO")
tc.target = orb_aim
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
# the orb also glows softly in every direction (dim omni at the same point, same radius): its caustics coincide
# with the key's.
GLOW_POWER = envf("S02_GLOW", 14)
glow = D.light("POINT", "OrbGlow", location=(0, 0, 0), target=None, power=GLOW_POWER, color="#FFF6E8",
               radius=orb.data.shadow_soft_size)
glow.parent = orb
halo_mat = D.mat_emission("#FFF6E8", 4.0, name="orb_halo")
halo_mat.cycles.emission_sampling = "NONE"
halo = D.sphere("OrbHalo", 0.07, (0, 0, 0), halo_mat)
halo.parent = orb
ray_only(halo, camera=True, glossy=True)

FILL_POWER = envf("S02_FILL", 14)
fill = D.light("AREA", "Fill", (0.5, -2.6, 3.2), (0, 0.6, 0.6), power=FILL_POWER,
               color=os.environ.get("S02_FILLC", "#A890FF"), size=3.0)

# wall washes (R1): each lights only its own wall, from the camera side, falling off into the back corner
WASH_L = envf("S02_WASHL", 56)
WASH_R = envf("S02_WASHR", 95)
washL = linked_light("WashL", (-0.55, -0.60, 1.70), (-1.60, 1.30, 0.95), WASH_L, "white", 2.5, [wallL])
washR = linked_light("WashR", (0.55, -0.60, 1.70), (1.60, 1.30, 0.95), WASH_R, "white", 2.5, [wallR])
# coral kicker (R3): lights only the mirror-ball pedestal (its camera side was in the orb's shadow -> oxblood)
KICK = envf("S02_KICK", 20)
kick = linked_light("CoralKick", (1.70, -1.30, 0.90), (1.00, -0.40, 0.15), KICK, "white", 0.6, [mb_ped],
                    glossy=True)

# floor lift (R18): a soft lavender bounce from the camera side, light-linked to the floor and the white props only
# (no casters, no shadows, no caustics: glass is not a receiver), so the periphery of the orb's pool reads
# pastel cream / lavender instead of taupe while the pool, the caster shadows' shapes and the caustics stay put
FLIFT = envf("S02_FLIFT", 90)
if FLIFT > 0:
    flift = linked_light("FloorLift", _v3e("S02_FLIFT_POS", "0.60,-3.20,2.40"), _v3e("S02_FLIFT_AIM", "0.30,-0.40,0.0"),
                         FLIFT, os.environ.get("S02_FLIFTC", "#F0E8FF"), envf("S02_FLIFT_SIZE", 4.5),
                         [bpy.data.objects["Room_floor"], floor_ext, plinth, swirl_ped, heart_stand])
    # the macro keeps its caustic contrast: only a slight lift there (lead S02-5); switches on the hard cuts
    FLIFT_M = envf("S02_FLIFT_M", 30)
    D.bake(flift.data, "energy", 1, N, lambda f: FLIFT_M if 61 <= f <= 120 else FLIFT)

sky_path = os.path.join(D.ASSETS, "hdri", "candy_sky_nosun_4k.hdr")
if not os.path.exists(sky_path):
    print("[s02] WARNING: candy_sky_nosun_4k.hdr missing, falling back to colorful_studio", flush=True)
    sky_path = D.HDRI["colorful_studio"]
WORLD_K = envf("S02_WORLD", 0.08)
WORLD_GLOSSY = envf("S02_WGLOSSY", 0.45)
rig = D.world_hdri(sky_path, WORLD_K, camera_bg=os.environ.get("S02_BG", "mint"),
                   camera_bg_strength=envf("S02_BGK", 0.18))
# reflections see the candy sky brighter (WORLD_GLOSSY) than diffuse lighting does (WORLD_K): chrome and glass
# mirror a bright candy world while the jewel-box ambient stays low.
_wn, _wl = rig.world.node_tree.nodes, rig.world.node_tree.links
_lp = _wn.new("ShaderNodeLightPath")
_ma = _wn.new("ShaderNodeMath")
_ma.operation = "MULTIPLY_ADD"
_ma.inputs[1].default_value = WORLD_GLOSSY - WORLD_K
_ma.inputs[2].default_value = WORLD_K
_wl.new(_lp.outputs["Is Glossy Ray"], _ma.inputs[0])
_wl.new(_ma.outputs[0], rig.light_bg.inputs["Strength"])

# ----------------------------------------------------------------------------------------------
# animation (closed form, baked per frame)
# ----------------------------------------------------------------------------------------------
G = 12.0           # toy gravity
DROP_H = 2.6

# orb fall (R9): ease_in_quad from just above frame to O_Z at f14, then a velocity-matched damped dip
O_Z0 = envf("S02_OZ0", 1.72)
F_LAND = 14
V_T = 2.0 * (O_Z0 - O_Z) / (F_LAND - 1) * FPS          # m/s at f14 (slope of the quad at its end)
A_DIP = V_T / (5.0 * math.pi)                          # dip amplitude that matches that velocity
CLICKS = (76, 91, 106)                                 # macro beats (R10)
CLICK_DEG = envf("S02_CLICK_DEG", 12.0)
CLICK_DZ = envf("S02_CLICK_DZ", 0.04)
SWING_F0, SWING_LEN = 122, 14                          # swing home lands (detent peak) on the f136 beat


def click_c(t):
    """S01's detent click profile (t = frames since the click starts): smootherstep to 1.028 in 10 f, settle 4 f."""
    if t <= 0:
        return 0.0
    if t <= 10:
        return 1.028 * D.smootherstep(t / 10.0)
    return 1.028 - 0.028 * D.smoothstep((t - 10) / 4.0)


def orb_c(f):
    """Arc progress in clicks (0..3, detent overshoot included)."""
    if f < CLICKS[0]:
        return 0.0
    if f <= 121:
        k = min(2, (f - CLICKS[0]) // 15)
        return k + click_c(f - CLICKS[k])
    t = f - SWING_F0
    if t <= 0:
        return 3.0
    if t <= SWING_LEN:
        s = 1.028 * D.smootherstep(t / float(SWING_LEN))
    else:
        s = 1.028 - 0.028 * D.smoothstep((t - SWING_LEN) / 4.0)
    return 3.0 * (1.0 - s)


def orb_phi(f):
    return -CLICK_DEG * orb_c(f) if f >= 61 else 0.0


def orb_pos(f):
    if f <= F_LAND:
        p = (f - 1) / float(F_LAND - 1)
        return (O_HOME.x, O_HOME.y, O_Z0 - (O_Z0 - O_Z) * p * p)
    if f < 61:
        u = sec(f, F_LAND)
        dz = 0.0 if u > 0.6 else A_DIP * math.exp(-10.0 * u) * math.sin(5.0 * math.pi * u)
        return (O_HOME.x, O_HOME.y, O_Z - dz)
    c = orb_c(f)
    ph = math.radians(-CLICK_DEG * c)
    return (O_HOME.x + O_HOME.y * math.sin(ph), O_HOME.y * math.cos(ph), O_Z - CLICK_DZ * c)


D.bake(orb, "location", 1, N, orb_pos)


def orb_power_scale(f):
    z = orb_pos(f)[2]
    if f <= F_LAND:
        return max(1.0, (z / O_Z) ** 1.3)
    if f >= 61:
        return (z / O_Z) ** 2             # keeps the pool level as the orb steps down in the macro
    return 1.0


D.bake(orb.data, "energy", 1, N, lambda f: KEY_POWER * orb_power_scale(f))
D.bake(glow.data, "energy", 1, N, lambda f: GLOW_POWER * orb_power_scale(f))


def fall_height(f, f_land):
    """Height above the rest position of a drop-in landing on local frame f_land (t<0: falling)."""
    t = sec(f, f_land)
    return 0.5 * G * t * t if t < 0 else 0.0


def first_visible(f_land, above=2.9):
    return int(math.floor(f_land - math.sqrt(2 * above / G) * FPS))


# lemon ball: lands f31, hop with restitution 0.15, rolls 3 cm, stops by f45
LEMON_REST = V((LEMON_XY[0], LEMON_XY[1], LEMON_R))
LEMON_ROLL_DIR = V((-0.6, 0.8, 0.0)).normalized()
V_IMP = G * math.sqrt(2 * DROP_H / G)
V_HOP = 0.15 * V_IMP


def lemon_roll(f):
    return 0.03 * D.ease_out_cubic(D.prog(f, 31, 45))


def lemon_loc(f):
    t = sec(f, 31)
    if t < 0:
        z = fall_height(f, 31)
    else:
        t_hop = 2 * V_HOP / G
        z = V_HOP * t - 0.5 * G * t * t if t < t_hop else 0.0
    p = LEMON_REST - LEMON_ROLL_DIR * 0.03 + LEMON_ROLL_DIR * lemon_roll(f)
    return (p.x, p.y, LEMON_REST.z + z)


ROLL_AXIS = V((0, 0, 1)).cross(LEMON_ROLL_DIR)


def lemon_rot(f):
    ang = lemon_roll(f) / LEMON_R
    return Matrix.Rotation(ang, 4, ROLL_AXIS).to_euler()


D.bake(lemon, "location", 1, N, lemon_loc)
D.bake(lemon, "rotation_euler", 1, N, lambda f: tuple(lemon_rot(f)))
D.hide_range(lemon, visible_from=first_visible(31))

# pink heart (R11): falls 0.42 m right of its stand (clear of the orb on screen), glides in over f37-46, lands
# tip-first f46 and rocks 14deg e^-5t sin(2pi 2t) about the camera axis (first swing continues the glide, left)
HEART_TIP = V((HEART_XY[0], HEART_XY[1], 0.05 - 0.012))   # seated 12 mm into the stand
HEART_TILT_BACK = envf("S02_HTILT", 10)
HEART_GLIDE = envf("S02_HGLIDE", 0.42)
HEART_ROCK = envf("S02_HROCK", 14)


def heart_dx(f):
    return HEART_GLIDE * (1.0 - D.smoothstep(D.prog(f, 37, 46)))


def heart_rock(f):
    t = sec(f, 46)
    # ends exactly at its 2nd zero crossing (t=0.5 s = f61; "at rest by f62") so the heart is truly static for
    # the whole macro: a moving 430k-tri glass heart cost ~200 s/f at 2048 spp
    return 0.0 if (t <= 0 or t >= 0.5) else HEART_ROCK * math.exp(-5 * t) * math.sin(2 * math.pi * 2 * t)


def heart_matrix(f):
    rock = math.radians(heart_rock(f))
    # heart local: XY plane, lobes +Y, normal +Z.  Stand it up (lobes up, normal -> -Y), lean back, rock about the
    # world axis that faces the camera (positive rock = top to the left).
    R = (Matrix.Rotation(-rock, 4, "Y") @ Matrix.Rotation(math.radians(90 - HEART_TILT_BACK), 4, "X"))
    T = Matrix.Translation(HEART_TIP + V((heart_dx(f), 0, fall_height(f, 46))))
    return T @ R


D.bake(heart, "location", 1, N, lambda f: tuple(heart_matrix(f).to_translation()))
D.bake(heart, "rotation_euler", 1, N, lambda f: tuple(heart_matrix(f).to_euler()))
D.hide_range(heart, visible_from=first_visible(46))
# object motion blur only while it falls (f<=46); a moving glass heart costs ~4x render time (caustic paths
# re-enter its motion BVH many times), so the post-landing rock renders unblurred
for _f, _on in ((1, True), (46, True), (47, False)):
    heart.cycles.use_motion_blur = _on
    heart.keyframe_insert("cycles.use_motion_blur", frame=_f)

# heart stand pops up (POP spring 2.5 Hz / damping 8, ~20 % overshoot) at f38, ready for the f46 landing
STAND_POP = 38
D.hide_range(heart_stand, visible_from=STAND_POP)


def stand_scale(f):
    if f < STAND_POP:
        return 0.001
    if f >= 60:
        return 1.0
    return max(0.001, D.spring(sec(f, STAND_POP), 2.5, 8.0))


D.bake(heart_stand, "scale", 1, N, lambda f: (stand_scale(f),) * 3)

# aqua ring (R12): lands flat f61 (the cut to macro lands on the impact), 3 cm restitution hop, wobble
# 10deg e^-6t sin(2pi 3t)
RING_REST = V((RING_XY[0], RING_XY[1], RING_r))
RING_WOB = envf("S02_RWOB", 10.0)
V_RHOP = math.sqrt(2 * G * envf("S02_RHOP", 0.03))


def ring_wobble(f):
    t = sec(f, 61)
    # ends at its 5th zero crossing (t=5/6 s, f86): static afterwards (see heart_rock)
    return 0.0 if (t <= 0 or t >= 5.0 / 6.0) else RING_WOB * math.exp(-6 * t) * math.sin(2 * math.pi * 3 * t)


def ring_hop(f):
    t = sec(f, 61)
    return V_RHOP * t - 0.5 * G * t * t if 0 < t < 2 * V_RHOP / G else 0.0


def ring_loc(f):
    w = math.radians(ring_wobble(f))
    lift = RING_R * abs(math.sin(w)) + RING_r * (1 - math.cos(w))   # keep the low edge on the floor
    return (RING_REST.x, RING_REST.y, RING_REST.z + fall_height(f, 61) + ring_hop(f) + lift)


D.bake(ring, "location", 1, N, ring_loc)
D.bake(ring, "rotation_euler", 1, N, lambda f: (math.radians(ring_wobble(f)), 0.0, 0.0))
D.hide_range(ring, visible_from=first_visible(61))

# chrome swirl spins 0 -> 90 deg about its normal over f1-180 (linear)
D.bake(swirl, "rotation_euler", 1, N, lambda f: (0.0, 0.0, math.radians(90.0 * (f - 1) / (N - 1))))

# ----------------------------------------------------------------------------------------------
# cameras
# ----------------------------------------------------------------------------------------------
W0, W60 = V((0.25, -5.30, 2.30)), V((0.22, -5.05, 2.22))
W150 = V((0.20, -4.85, 2.15))
W_TGT = V((0.05, 0.35, 0.60))
W_LENS = envf("S02_WLENS", 55)
U_HAT = (W150 - BALL_C).normalized()
D_START = (W150 - BALL_C).length
# exact sphere silhouette: half-width on the sensor = lens*tan(asin(r/d)); 1536/1920 of the 36 mm sensor
_tan = 0.5 * (1536.0 / 1920.0) * 36.0 / W_LENS
D_END = envf("S02_DEND", BALL_R / math.sin(math.atan(_tan)))
BALL_FOCUS_OFF = 0.06

# fourth-wall card: blush, visible only to glossy + transmission rays, centred on the mirror ball's
# view axis (behind the camera at the end of the push) and facing the ball.
CARD_DIST = 7.2
CARD_K = envf("S02_CARD", 0.9)
card = D.rounded_box("FourthWall", (13.0, 0.1, 8.0), 0.05, location=tuple(BALL_C + U_HAT * CARD_DIST),
                     mat=D.mat_emission("blush", CARD_K, name="fourth_wall"))
card.rotation_euler = (-U_HAT).to_track_quat("Y", "Z").to_euler()   # local +Y faces the ball
ray_only(card, camera=False, glossy=True, transmission=True)
if not os.environ.get("S02_CARD_NEE"):
    card.active_material.cycles.emission_sampling = "NONE"   # reflection card only: never a sampled light

# out-cut brightness (R5): reflection-side ramps over f160-180 so the ball hands S03 a bright pastel frame
OUT_F0 = 160
WG_END, CARD_END, FILL_END = envf("S02_WG_END", 1.0), envf("S02_CARD_END", 2.0), envf("S02_FILL_END", 40.0)


def out_ramp(f):
    return D.ease_in_cubic(D.prog(f, OUT_F0, N))


D.bake(_ma.inputs[1], "default_value", 1, N,
       lambda f: (WORLD_GLOSSY + (WG_END - WORLD_GLOSSY) * out_ramp(f)) - WORLD_K)
D.bake(card.active_material.node_tree.nodes["Emission"].inputs["Strength"], "default_value", 1, N,
       lambda f: CARD_K + (CARD_END - CARD_K) * out_ramp(f))
D.bake(fill.data, "energy", 1, N, lambda f: FILL_POWER + (FILL_END - FILL_POWER) * out_ramp(f))


def w_pos(f):
    if f <= 60:
        return W0.lerp(W60, D.ease_in_out_sine(D.prog(f, 1, 60)))
    if f <= 120:
        return W60.copy()
    if f <= 150:
        return W60.lerp(W150, D.ease_out_cubic(D.prog(f, 121, 150)))
    x = (f - 150) / 30.0                      # not clamped: f181 extrapolates the push for motion blur
    e = x ** 3
    d = D_START * (D_END / D_START) ** e
    return BALL_C + U_HAT * d


AIM_F0, AIM_F1 = 136, 166                     # R13: one continuous move into the ball, detent into f166


def w_aim(f):
    t = f - AIM_F0
    L = float(AIM_F1 - AIM_F0)
    if t <= 0:
        return 0.0
    if t <= L:
        return 1.02 * D.smootherstep(t / L)
    return 1.02 - 0.02 * D.smoothstep((t - L) / 6.0)


def w_tgt(f):
    return W_TGT.lerp(BALL_C, w_aim(f))


def w_focus(f):
    return V((0.0, 0.0, 0.2)).lerp(BALL_C + U_HAT * BALL_FOCUS_OFF, D.ease_in_out_sine(D.prog(f, 140, 166)))


def w_fstop(f):
    return 3.5 * (8.0 / 3.5) ** D.ease_in_out_sine(D.prog(f, 151, 180))


camW_focus = D.empty("CamW_focus", (0, 0, 0.2))
camW, camW_t = D.camera("CamW", tuple(W0), tuple(W_TGT), lens=W_LENS, fstop=3.5, focus=camW_focus)
# bake one frame past the end so the f180 shutter interval (179.75-180.25) blurs symmetrically about the
# f180 pose (the push keeps its ease_in_cubic curve, extrapolated)
D.bake(camW, "location", 1, N + 1, lambda f: tuple(w_pos(f)))
D.bake(camW_t, "location", 1, N, lambda f: tuple(w_tgt(f)))
D.bake(camW_focus, "location", 1, N, lambda f: tuple(w_focus(f)))
D.bake(camW.data, "dof.aperture_fstop", 1, N, w_fstop)


def _v3(env, dflt):
    return V(tuple(float(x) for x in os.environ.get(env, dflt).split(",")))


# R14: locked macro (no truck), 75 mm high angle, pulled back 0.4 m and 0.12 m left, target 5 cm lower
M0 = _v3("S02_M0", "-0.015,-3.087,2.066")
MT0 = _v3("S02_MT0", "-0.06,-0.05,0.07")
M_LENS = envf("S02_MLENS", 75)
camM_focus = D.empty("CamM_focus", tuple(_v3("S02_MF", "-0.03,-0.15,0.0")))
camM, camM_t = D.camera("CamM", tuple(M0), tuple(MT0), lens=M_LENS, fstop=5.6, focus=camM_focus)

force = os.environ.get("S02_CAM", "")
if force == "top":
    cd = bpy.data.cameras.new("CamTop")
    cd.type = "ORTHO"
    cd.ortho_scale = 5.6
    top = D.link(bpy.data.objects.new("CamTop", cd))
    top.location = (0.0, 0.0, 9.0)
    sc.camera = top
elif force in ("W", "M"):
    sc.camera = camW if force == "W" else camM
else:
    for name, fr, cam in (("W", 1, camW), ("M", 61, camM), ("W2", 121, camW)):
        mk = sc.timeline_markers.new(name, frame=fr)
        mk.camera = cam
    sc.camera = camW

# ----------------------------------------------------------------------------------------------
# G1 orb glow (R6): S01's compositor block, verbatim parameters.  Bloom driven by the Emit pass only, so only
# the camera-visible halo glows (lit surfaces, caustics and reflections never bloom).  Size is relative to the
# image, so draft / preview / final match.
# ----------------------------------------------------------------------------------------------
GLOW = envf("S02_BLOOM", 1.0)
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

# ----------------------------------------------------------------------------------------------
# metadata (build time, every mode)
# ----------------------------------------------------------------------------------------------
meta = {
    "id": SHOT,
    "frames": N,
    "start_frame_in_film": START,
    "events": {"orb_fall": 1, "orb_rest": 16, "lemon_land": 31, "stand_pop": STAND_POP, "heart_land": 46,
               "ring_land": 61, "cut_macro": 61, "orb_clicks": list(CLICKS), "cut_wide": 121,
               "orb_home": SWING_F0 + SWING_LEN, "push_start": 151, "aim_settle": AIM_F1, "end": 180},
    "per_frame": {
        "orb_phi_deg": [round(orb_phi(f), 4) for f in range(1, N + 1)],
        "cam_macro": [1 if 61 <= f <= 120 else 0 for f in range(1, N + 1)],
    },
}
meta_dir = os.path.join(D.ROOT, "renders", "meta")
os.makedirs(meta_dir, exist_ok=True)
with open(os.path.join(meta_dir, SHOT + ".json"), "w") as fh:
    json.dump(meta, fh, indent=1)

print(f"[s02] heart non-manifold edges: {non_manifold_count(heart)} ({len(heart.data.polygons)} faces)  "
      f"swirl: {non_manifold_count(swirl)}", flush=True)
print(f"[s02] u_hat={tuple(round(c, 4) for c in U_HAT)} d_start={D_START:.4f} d_end={D_END:.4f}", flush=True)
if os.environ.get("S02_BALLMASK"):            # QA only: linear silhouette mask pass for the circle-match measurement
    D.assign(mball, D.mat_emission("white", 0.5, name="ballmask"))
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob is not mball:
            ob.hide_render = True
    rig.light_bg.inputs["Strength"].links and rig.world.node_tree.links.remove(rig.light_bg.inputs["Strength"].links[0])
    rig.light_bg.inputs["Strength"].default_value = 0.0
    rig.cam_bg.inputs["Strength"].default_value = 0.0
for d in DEVIATIONS:
    print("[s02] deviation:", d, flush=True)
for _nm in filter(None, os.environ.get("S02_HIDE", "").split(",")):   # debug: hide named objects
    bpy.data.objects[_nm].hide_render = True

# ----------------------------------------------------------------------------------------------
# R17: per-segment sample policy (final mode only; an explicit --samples overrides it for tests).  Keyed on
# scene.cycles with CONSTANT interpolation, so the frame_set() in D.finish applies it per frame.
# ----------------------------------------------------------------------------------------------
WIDE_SPP = int(envf("S02_WIDE_SPP", 768))
WIDE_THR = envf("S02_WIDE_THR", 0.01)
MACRO_SPP = int(envf("S02_MACRO_SPP", 1536))
MACRO_ADAPT = os.environ.get("S02_MACRO_ADAPT", "0") == "1"
MACRO_THR, MACRO_MIN = envf("S02_MACRO_THR", 0.002), int(envf("S02_MACRO_MIN", 1024))
POLICY = {1: (WIDE_SPP, True, WIDE_THR, 64), 61: (MACRO_SPP, MACRO_ADAPT, MACRO_THR, MACRO_MIN),
          121: (WIDE_SPP, True, WIDE_THR, 64)}
if args.mode == "final" and not args.samples and not os.environ.get("S02_NOPOLICY"):
    _c = sc.cycles
    for _f, (_spp, _ad, _thr, _mn) in POLICY.items():
        _c.samples, _c.use_adaptive_sampling, _c.adaptive_threshold, _c.adaptive_min_samples = _spp, _ad, _thr, _mn
        for _p in ("samples", "use_adaptive_sampling", "adaptive_threshold", "adaptive_min_samples"):
            _c.keyframe_insert(_p, frame=_f)
    for _fc in D._fcurves(sc.animation_data.action):
        if _fc.data_path.startswith("cycles."):
            for _kp in _fc.keyframe_points:
                _kp.interpolation = "CONSTANT"


def _report(scene, *_):
    c = scene.cycles
    print(f"[s02] render f{scene.frame_current}: spp {c.samples} adaptive {c.use_adaptive_sampling} "
          f"thr {c.adaptive_threshold:.4f} min {c.adaptive_min_samples}", flush=True)


bpy.app.handlers.render_pre.append(_report)

D.finish(args, final_samples=2048, final_threshold=0.01, frame_end=N, shot_name=SHOT)
