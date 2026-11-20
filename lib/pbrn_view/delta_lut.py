"""Correction LUT for the s05_finale screens: delta(t) = a_exact(t) - a_closed(t) in lg2-allocation units, where
a_exact inverts Blender's real PBR Neutral view (pbrNeutral.cube, tetrahedral) and a_closed is the closed-form Khronos
inverse that the shader evaluates analytically. Out-of-gamut nodes (display colours the view cannot produce) get a
harmonic (Laplace) extension of the in-gamut field, so trilinear lookups near the gamut boundary stay smooth.
The shader then emits x = x_closed(t) * 2^(19 * delta(t)) * 2^-EXPOSURE."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbrn_lut as M  # noqa
import build_inv_lut as B  # noqa


def grid(N, shaper="sqrt"):
    u = np.linspace(0, 1, N)
    return u ** 2 if shaper == "sqrt" else u


def build_delta(N, shaper="sqrt", fill_iters=600):
    tt = grid(N, shaper)
    R, G, Bb = np.meshgrid(tt, tt, tt, indexing="ij")
    T = np.stack([R, G, Bb], -1)
    L = M.srgb_dec(T)
    A = np.empty_like(L)
    for k in range(N):
        A[:, :, k] = B.solve(L[:, :, k])
    F = M.srgb_enc(M.tetra(A))
    ok = np.abs(F - T).max(-1) * 255 < 0.02
    D = A - B.g_closed(L)
    D[~ok] = 0.0
    # harmonic fill of the out-of-gamut nodes
    bad = ~ok
    for it in range(fill_iters):
        P = np.pad(D, ((1, 1), (1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (P[2:, 1:-1, 1:-1] + P[:-2, 1:-1, 1:-1] + P[1:-1, 2:, 1:-1] + P[1:-1, :-2, 1:-1] +
               P[1:-1, 1:-1, 2:] + P[1:-1, 1:-1, :-2]) / 6.0
        D[bad] = avg[bad]
    return D, ok


def lookup(D, t, shaper="sqrt"):
    N = D.shape[0]
    t = np.clip(t, 0, 1)
    p = (np.sqrt(t) if shaper == "sqrt" else t) * (N - 1)
    i0 = np.minimum(np.floor(p).astype(int), N - 2)
    f = p - i0
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = (f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) * \
                    (f[..., 2] if db else 1 - f[..., 2])
                out = out + w[..., None] * D[i0[..., 0] + dr, i0[..., 1] + dg, i0[..., 2] + db]
    return out


def invert(D, t, shaper="sqrt"):
    """Display code t -> lg2 allocation coordinate a the view must see (simulates the shader)."""
    return B.g_closed(M.srgb_dec(t)) + lookup(D, t, shaper)
