"""Inverse of Blender's Khronos PBR Neutral sRGB view (exposure folded out), as a 3D LUT for the s05_finale screens.

Input grid: display sRGB code values t in [0,1]^3, sampled uniformly in u = sqrt(t) (a shaper: the inverse is steep
near black). Stored value: the lg2 allocation coordinate a = (log2(x) + 9) / 19 of the scene value x the view needs
BEFORE exposure (the shader multiplies by 2^-EXPOSURE). Solved per node by damped Newton on the exact forward model
(pbrn_lut.view: lg2 alloc -> pbrNeutral.cube tetrahedral -> sRGB), so the lookup inverts Blender's real view, not the
closed-form Khronos curve (which differs from the LUT by up to ~6/255 on saturated colours).

Atlas layout (float32 EXR, Non-Color): N slices along blue, slice k at x in [k*N, (k+1)*N), red along x, green along
y (row 0 = g 0 at the bottom in Blender's convention). Usage: python build_inv_lut.py [N] [out.exr]"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbrn_lut as M  # noqa: E402


def g_closed(L):
    """Closed-form Khronos PBR Neutral inverse (display-linear -> lg2 allocation coordinate), the preconditioner."""
    sc, dd, desat = 0.76, 0.24, 0.15
    o = np.clip(L, 0, 0.9975)
    newp = o.max(-1, keepdims=True)
    peak = dd * dd / (1 - newp) - dd + sc
    g = 1 - 1 / (desat * (peak - newp) + 1)
    cc = (o - newp * g) / (1 - g)
    c = np.where(newp < sc, o, cc * peak / np.maximum(newp, 1e-12))
    y = c.min(-1, keepdims=True)
    x = np.where(y < 0.04, 0.4 * np.sqrt(np.maximum(y, 0)), y + 0.04)
    return (np.log2(np.maximum(c + (x - y), 2.0 ** M.LG_MIN)) - M.LG_MIN) / (M.LG_MAX - M.LG_MIN)


def solve(L, iters=80):
    """a in [0,1]^3 with tetra(a) = L (display-linear). Fixed-point iteration a += g(L) - g(tetra(a)) with g the
    closed-form inverse (a good approximate inverse of the LUT, so the error contracts every step; no derivatives,
    which are discontinuous on the tetrahedral seams where every grey lies). Out-of-gamut targets end at the
    nearest reachable value of the closed form (clamped to [0, 1])."""
    gL = g_closed(L)
    a = np.clip(gL, 0, 1)
    for it in range(iters):
        a = np.clip(a + (gL - g_closed(M.tetra(a))), 0, 1)
    return a


def build(N=65):
    u = np.linspace(0, 1, N)
    t = u ** 2
    R, G, B = np.meshgrid(t, t, t, indexing="ij")
    T = np.stack([R, G, B], -1)
    L = M.srgb_dec(T)
    A = np.empty_like(L)
    for k in range(N):                   # slice by slice (memory)
        A[:, :, k] = solve(L[:, :, k])
    return A                              # A[r, g, b] -> a


def lookup(A, t):
    """Trilinear lookup exactly as the shader does it (shaper u = sqrt(t))."""
    N = A.shape[0]
    p = np.sqrt(np.clip(t, 0, 1)) * (N - 1)
    i0 = np.minimum(np.floor(p).astype(int), N - 2)
    f = p - i0
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = (f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) * \
                    (f[..., 2] if db else 1 - f[..., 2])
                out = out + w[..., None] * A[i0[..., 0] + dr, i0[..., 1] + dg, i0[..., 2] + db]
    return out


def atlas(A):
    N = A.shape[0]
    img = np.zeros((N, N * N, 3), np.float32)       # rows = g, cols = k*N + r
    for k in range(N):
        img[:, k * N:(k + 1) * N] = A[:, :, k].transpose(1, 0, 2)   # [g, r]
    return img


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 65
    out = sys.argv[2] if len(sys.argv) > 2 else None
    A = build(N)
    np.save(os.path.join(os.path.dirname(out) if out else ".", f"inv_lut_{N}.npy"), A)
    if out:
        import cv2
        img = atlas(A)
        cv2.imwrite(out, img[::-1, :, ::-1].copy())  # top-down rows for the file, BGR
        print("wrote", out, img.shape)
