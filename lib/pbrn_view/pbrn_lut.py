"""Blender 4.5's 'Khronos PBR Neutral' sRGB view, modelled exactly as its OCIO config builds it:
scene-linear Rec.709 x 2^exposure -> AllocationTransform lg2 [-9, 10] -> pbrNeutral.cube (57^3, tetrahedral)
-> sRGB piecewise encode. Used to build and verify the inverse LUT the s05_finale screens use."""
import os
import numpy as np

# Blender 4.5's own LUT file, inside the project's Blender install (tools/blender -> blender-4.5.15-linux-x64);
# PBRN_CUBE overrides it.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CUBE = os.environ.get("PBRN_CUBE", os.path.join(_ROOT, "tools", "blender", "4.5", "datafiles", "colormanagement",
                                                "luts", "pbrNeutral.cube"))
LG_MIN, LG_MAX = -9.0, 10.0


def load_cube(path=CUBE):
    rows, n = [], None
    with open(path) as fh:
        for ln in fh:
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("TITLE") or s.startswith("DOMAIN"):
                continue
            if s.startswith("LUT_3D_SIZE"):
                n = int(s.split()[1])
                continue
            rows.append([float(v) for v in s.split()])
    a = np.array(rows, np.float64)
    assert len(a) == n ** 3
    return a.reshape(n, n, n, 3).transpose(2, 1, 0, 3), n      # lut[r, g, b] (red fastest in the file)


LUT, N = load_cube()


def alloc(x):
    x = np.maximum(np.asarray(x, np.float64), 2.0 ** LG_MIN)
    return np.clip((np.log2(x) - LG_MIN) / (LG_MAX - LG_MIN), 0.0, 1.0)


def unalloc(a):
    return 2.0 ** (np.asarray(a, np.float64) * (LG_MAX - LG_MIN) + LG_MIN)


def tetra(a, lut=LUT, n=N):
    """OCIO-style tetrahedral interpolation of the 3D LUT at a in [0,1]^3 (..., 3)."""
    a = np.clip(np.asarray(a, np.float64), 0, 1) * (n - 1)
    i0 = np.minimum(np.floor(a).astype(int), n - 2)
    f = a - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]

    def V(dr, dg, db):
        return lut[r0 + dr, g0 + dg, b0 + db]
    c000, c111 = V(0, 0, 0), V(1, 1, 1)
    out = np.empty(a.shape, np.float64)
    m1 = (fr > fg) & (fg > fb)
    m2 = (fr > fb) & (fb >= fg) & ~m1
    m3 = (fb >= fr) & (fr > fg) & ~m1 & ~m2
    m4 = (fg >= fr) & (fr > fb) & ~m1 & ~m2 & ~m3
    m5 = (fg > fb) & (fb >= fr) & ~m1 & ~m2 & ~m3 & ~m4
    m6 = ~(m1 | m2 | m3 | m4 | m5)
    c100, c110, c101, c010, c011, c001 = V(1, 0, 0), V(1, 1, 0), V(1, 0, 1), V(0, 1, 0), V(0, 1, 1), V(0, 0, 1)
    cand = [
        (m1, (1 - fr) * c000 + (fr - fg) * c100 + (fg - fb) * c110 + fb * c111),
        (m2, (1 - fr) * c000 + (fr - fb) * c100 + (fb - fg) * c101 + fg * c111),
        (m3, (1 - fb) * c000 + (fb - fr) * c001 + (fr - fg) * c101 + fg * c111),
        (m4, (1 - fg) * c000 + (fg - fr) * c010 + (fr - fb) * c110 + fb * c111),
        (m5, (1 - fg) * c000 + (fg - fb) * c010 + (fb - fr) * c011 + fr * c111),
        (m6, (1 - fb) * c000 + (fb - fg) * c001 + (fg - fr) * c011 + fr * c111),
    ]
    for m, v in cand:
        mm = np.broadcast_to(m, out.shape)
        out[mm] = np.broadcast_to(v, out.shape)[mm]
    return out


def srgb_enc(L):
    L = np.clip(np.asarray(L, np.float64), 0, None)
    return np.where(L <= 0.0031308, 12.92 * L, 1.055 * np.power(L, 1 / 2.4) - 0.055)


def srgb_dec(t):
    t = np.asarray(t, np.float64)
    return np.where(t <= 0.04045, t / 12.92, ((t + 0.055) / 1.055) ** 2.4)


def view(scene_lin, exposure=-0.2):
    """scene-linear radiance -> display sRGB code value 0..1 (before quantisation)."""
    return srgb_enc(tetra(alloc(np.asarray(scene_lin, np.float64) * 2.0 ** exposure)))
