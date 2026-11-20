"""Seurat top-extension band for the s04_subject overscan still (storyboard_v2 section 2). CPU only, deterministic.

The finale's centre hex tile (shots/s04_subject.py --overscan) sees ~14 % of the canvas height ABOVE the painting.
This replaces the earlier mirror extension, which folded the tree trunks into V/diamond shapes. Above the inner edge
of Seurat's painted top border the band is new pointillist foliage with no recognisable structure. It blends into
the canopy below.

Everything works on FOLIAGE pixels only. The canopy (v 0.89-0.978) is masked: trunks and branches (R > G), sky
(light) and dark figures are left out, and low-passes are normalised convolutions with that mask, so no trunk colour
or shape enters the band.

  * base colour (all scales >= ~32 texels of the 20000 px scan):
      - near the seam: the painting's own foliage low-pass (sigma 32), reflected about v 0.962 (soft masses only,
        trunks already masked out). It fades out over v 0.955-0.99, so the canopy's light/dark masses continue
        across the seam;
      - above: random masses. The column-wise foliage colour (sigma 2 % of the width, drifting half-way to the
        canopy mean at the top) plus two noise octaves (sigma 32->128 and 128->512 texels), each with the canopy's
        own 3x3 colour covariance for that octave (Cholesky), so the masses have the painting's amplitude and colour
        correlation (light = yellow-green, shadow = blue-green), x1.2 (the foliage-only statistics leave out the
        trunks' contrast). Where the seam field has no foliage nearby (the sky at the far left) it uses these.
  * brushwork (scales < ~32 texels): "dead-leaves" patch synthesis by numbers. About five layers of small elliptical
    patches (radius 12-34 texels, ~2-6 px in the final overscan) are pasted opaque in random order. Each patch is cut
    from a canopy spot whose foliage low-pass colour is nearest to the target's base colour (64 k-means colour
    clusters), so dab types follow the masses as in the painting. The patch keeps its detail (scan minus its
    low-pass: the real dabs, colours and canvas weave) on top of the target base. Source centres keep 80 texels
    from any non-foliage pixel.
  * feather: the patches cover the painting with a coverage that ramps (smoothstep) from 0 at v 0.945-0.960 to
    full at v 0.971-0.9795. Both ends vary smoothly along u (sigma 500 texels), so the trunks dissolve into
    foliage at different heights over ~1.5-3.5 % of the canvas height instead of ending on one line. Full coverage
    is reached below the lowest point of the painted red/blue border (v 0.9811), so the border is fully hidden.

Only the band is written, not a full painting copy. Its rows below v 0.941 are the painting's own top rows of that
resolution (checked equal), so shots/s04_subject.py --overscan cross-fades from the original JPEG to this band over
v 0.9365-0.9395 (identical content there). The painting below, including the whole f180 frame, keeps Blender's own
JPEG decode. The band is generated once at 20000 px and area-resampled (premultiplied) for 8192 / 2048; each
resolution's painting rows come from its own JPEG.

Outputs (assets/paintings/derived/):
  seurat_grande_jatte_<N>_topband.png   N = 20000, 8192, 2048: 8-bit sRGB, width N, rows for v_b0 .. v_b1 (top row
                                        = v_b1); band row r covers v in [v_b1 - (r + 1) / H_N, v_b1 - r / H_N]
  seurat_grande_jatte_ext.json          geometry per resolution (v_b0, v_b1, rows), crossfade / feather windows,
                                        seed, parameters, the source file's size and mtime
usage: tools/venv/bin/python -I scripts/make_seurat_ext.py [--res 20000,8192,2048] [--seed 7]   (~2 min, ~20 GB RAM)
"""
import argparse
import json
import math
import os
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAINT = os.path.join(ROOT, "assets", "paintings")
OUT = os.path.join(PAINT, "derived")
SRC_N = 20000
SRC = os.path.join(PAINT, f"seurat_grande_jatte_{SRC_N}.jpg")

K0_SRC = 872            # painting rows carried in the band at 20000 (v 1 -> 0.93450)
V_TOP = 1.17            # band top (the overscan top is v 1.1434; margin for filtering)
V_X = (0.9365, 0.9395)  # shader cross-fade JPEG -> band (painting rows only on both sides)
V_D0 = (0.945, 0.960)   # patch coverage ramp start, varies smoothly along u (trunks end at different heights)
V_D1 = (0.971, 0.9795)  # ... full coverage, varies along u; the painted border's lowest point is v 0.9811
V_D = (V_D0[0], V_D1[1])
SIG_RAMP_U = 500        # texels: smoothness of the ramp's variation along u
V_SEAM = (0.955, 0.99)  # base: painting's reflected foliage low-pass -> random masses
V_REFLECT = 0.962       # reflection axis of the foliage low-pass (sources stay below the border)
V_SRC = (0.89, 0.978)   # canopy rows used as the source (below the border, above the figures' hats)
U_SRC = (0.06, 0.94)
SIG_D = 32              # texels: detail / base split
OCT = (32, 128, 512)    # noise octaves (sigma edges, texels)
SIG_BASE_U = 400        # texels: column-profile smoothing along u (2 % of the width)
R_RANGE = (12.0, 34.0)  # patch radius range (log-uniform), texels at 20000
ASPECT = (1.0, 1.6)
COVERAGE = 5.0
ERODE = 80              # texels: patch centres keep this far from non-foliage pixels
N_CLUSTERS = 64
DRIFT_TOP = 0.5         # at the band top the column profile has drifted half-way to the canopy mean
OCT_GAIN = 1.2          # mass octaves x this (the foliage-only covariance omits the trunks' contrast)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def gblur(img, sig):
    """Gaussian blur; large sigmas via a downsampled grid (cheap and smooth enough for low frequencies)."""
    f = 1 if sig <= 48 else (4 if sig <= 160 else 16)
    if f == 1:
        return cv2.GaussianBlur(img, (0, 0), sig, borderType=cv2.BORDER_REFLECT)
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sig / f, borderType=cv2.BORDER_REFLECT)
    out = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    return out


def masked_lp(img, m, sig):
    """Normalised convolution: low-pass of img over the pixels where m = 1."""
    num = gblur(img * m[..., None], sig)
    den = gblur(m, sig)
    return num / np.maximum(den, 1e-3)[..., None], den


def build(seed, log):
    t0 = time.time()
    cv2.setNumThreads(32)
    rng = np.random.default_rng(seed)
    full = cv2.imread(SRC, cv2.IMREAD_COLOR)                      # BGR uint8, 13313 x 20000
    H0, W0 = full.shape[:2]
    assert (W0, H0) == (20000, 13313), (W0, H0)
    k1 = int(round((V_TOP - 1.0) * H0))
    v_b0, v_b1 = 1.0 - K0_SRC / H0, 1.0 + k1 / H0
    hb = k1 + K0_SRC
    log(f"source {W0}x{H0}; band rows {hb} (k1 {k1} above v=1, k0 {K0_SRC}), v {v_b0:.5f}..{v_b1:.5f}")

    # ---- source canopy: foliage mask, masked low-passes, detail ------------------------------------------------
    ys0, ys1 = int((1 - V_SRC[1]) * H0), int((1 - V_SRC[0]) * H0)
    pad = 3 * SIG_D
    a0 = ys0 - pad
    srcp = full[a0:ys1 + pad].astype(np.float32)
    b24 = cv2.GaussianBlur(srcp, (0, 0), 24)
    B, G, R = b24[..., 0], b24[..., 1], b24[..., 2]
    luma = 0.114 * B + 0.587 * G + 0.299 * R
    fol = (R < G + 6) & (luma < 175) & (luma > 35)
    rows = np.arange(a0, ys1 + pad)
    fol &= ((rows >= ys0) & (rows < ys1))[:, None]
    xs = np.arange(W0)
    fol &= ((xs >= U_SRC[0] * W0) & (xs < U_SRC[1] * W0))[None, :]
    m = fol.astype(np.float32)
    lp32, den32 = masked_lp(srcp, m, SIG_D)
    det = srcp - lp32
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ERODE + 1, 2 * ERODE + 1))
    fol_er = cv2.erode(fol.astype(np.uint8), k)
    sy, sx = np.nonzero(fol_er)
    log(f"canopy rows {ys0}-{ys1}: foliage {fol.mean() * 100:.1f} %, eroded {fol_er.mean() * 100:.1f} % "
        f"({len(sy)} source centres)  [{time.time() - t0:.0f} s]")

    # octave covariances of the foliage low-pass (the masses' colour statistics)
    lp128, _ = masked_lp(srcp, m, OCT[1])
    lp512, _ = masked_lp(srcp, m, OCT[2])
    core = fol_er > 0
    chol = []
    for lo, hi in ((lp32, lp128), (lp128, lp512)):
        d = (lo - hi)[core]
        cov = np.cov(d.T)
        chol.append(np.linalg.cholesky(cov + 1e-6 * np.eye(3)).astype(np.float32))
        log(f"octave std BGR {np.sqrt(np.diag(cov)).round(2)}")

    # ---- base field over the band -----------------------------------------------------------------------------
    vrow = (v_b1 - (np.arange(hb) + 0.5) / H0).astype(np.float32)   # v at each band row centre
    num = (lp32 * m[..., None]).sum(axis=0)                           # column profile (foliage only)
    den = m.sum(axis=0)
    num = cv2.GaussianBlur(num[None], (0, 0), SIG_BASE_U, borderType=cv2.BORDER_REFLECT)[0]
    den = cv2.GaussianBlur(den[None].astype(np.float32), (0, 0), SIG_BASE_U, borderType=cv2.BORDER_REFLECT)[0]
    mean_col = lp32[core].mean(axis=0)
    col = np.where(den[:, None] > 1e-3, num / np.maximum(den, 1e-3)[:, None], mean_col).astype(np.float32)
    drift = DRIFT_TOP * smoothstep((vrow - V_D[0]) / (v_b1 - V_D[0]))
    rnd = col[None] * (1 - drift[:, None, None]) + mean_col[None, None] * drift[:, None, None]
    for (s_lo, s_hi), L in zip(((OCT[0], OCT[1]), (OCT[1], OCT[2])), chol):
        w = rng.standard_normal((hb, W0, 3)).astype(np.float32)
        nz = gblur(w, s_lo) - gblur(w, s_hi)
        nz /= nz.reshape(-1, 3).std(axis=0)[None, None]
        rnd += OCT_GAIN * (nz @ L.T)
        del w, nz
    # near the seam: the painting's foliage low-pass, reflected about V_REFLECT (rows below it: as is)
    src_v = np.where(vrow <= V_REFLECT, vrow, np.maximum(2 * V_REFLECT - vrow, 2 * V_REFLECT - V_SEAM[1]))
    src_row = np.rint((1 - src_v) * H0 - 0.5).astype(int) - a0              # rows of lp32 (offset a0)
    assert src_row.min() >= 0 and src_row.max() < lp32.shape[0]
    wd = smoothstep(den32[src_row] / 0.3)[..., None]                   # far from any foliage (sky): random
    seam = lp32[src_row] * wd
    wc = (1 - smoothstep((vrow - V_SEAM[0]) / (V_SEAM[1] - V_SEAM[0])))[:, None, None]
    base = ((seam + rnd * (1 - wd)) * wc + rnd * (1 - wc)).astype(np.float32)
    del rnd, seam
    log(f"base field built  [{time.time() - t0:.0f} s]")

    # ---- colour clusters of the source centres (texture by numbers) ---------------------------------------------
    sub = rng.choice(len(sy), 200000, replace=False)
    cols = lp32[sy[sub], sx[sub]].astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
    cv2.setRNGSeed(seed)
    _, _, cent = cv2.kmeans(cols, N_CLUSTERS, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lab = np.empty(len(sy), np.int32)
    for i in range(0, len(sy), 2_000_000):
        c = lp32[sy[i:i + 2_000_000], sx[i:i + 2_000_000]]
        lab[i:i + 2_000_000] = np.argmin(((c[:, None, :] - cent[None]) ** 2).sum(-1), axis=1)
    members = [np.nonzero(lab == j)[0] for j in range(N_CLUSTERS)]
    log(f"{N_CLUSTERS} colour clusters, sizes {min(map(len, members))}-{max(map(len, members))}  "
        f"[{time.time() - t0:.0f} s]")

    # ---- dead-leaves patches -------------------------------------------------------------------------------------
    a_b = smoothstep((vrow - (V_D[1] - 0.004)) / 0.004).astype(np.float32)
    layer = base * a_b[:, None, None]                             # premultiplied
    alpha = np.repeat(a_b[:, None], W0, axis=1).astype(np.float32)
    row_lo = int((v_b1 - V_D[0]) * H0) + 1                        # lowest band row a patch centre may use
    e_r2 = (R_RANGE[1] ** 2 - R_RANGE[0] ** 2) / (2 * math.log(R_RANGE[1] / R_RANGE[0]))
    n = int(COVERAGE * W0 * row_lo / (math.pi * e_r2))
    lr = np.log(R_RANGE)
    cy = rng.uniform(0, row_lo, n)
    cx = rng.uniform(0, W0, n)
    rad = np.exp(rng.uniform(lr[0], lr[1], n))
    asp = rng.uniform(ASPECT[0], ASPECT[1], n)
    ang = rng.uniform(0, math.pi, n)
    vc = v_b1 - cy / H0
    ramp = []
    for lo, hi in (V_D0, V_D1):                                   # smooth per-column ramp ends
        z = cv2.GaussianBlur(rng.standard_normal((1, W0)).astype(np.float32), (0, 0), SIG_RAMP_U,
                             borderType=cv2.BORDER_REFLECT)[0]
        z /= z.std()
        t = 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))
        ramp.append(lo + (hi - lo) * t)
    ixc = np.clip(cx.astype(int), 0, W0 - 1)
    keep = rng.uniform(0, 1, n) < smoothstep((vc - ramp[0][ixc]) / (ramp[1][ixc] - ramp[0][ixc]))
    tcol = base[np.clip(cy.astype(int), 0, hb - 1), np.clip(cx.astype(int), 0, W0 - 1)]
    tcl = np.empty(n, np.int32)
    for i in range(0, n, 500_000):
        tcl[i:i + 500_000] = np.argmin(((tcol[i:i + 500_000, None, :] - cent[None]) ** 2).sum(-1), axis=1)
    u = rng.uniform(0, 1, n)
    pick = np.array([members[c][int(uu * len(members[c]))] for c, uu in zip(tcl, u)])
    placed = 0
    for i in np.nonzero(keep)[0]:
        ra, rb = rad[i] * math.sqrt(asp[i]), rad[i] / math.sqrt(asp[i])
        hw = int(math.ceil(ra)) + 2
        icx, icy = int(cx[i]), int(cy[i])
        tx0, ty0 = max(icx - hw, 0), max(icy - hw, 0)
        tx1, ty1 = min(icx + hw + 1, W0), min(icy + hw + 1, hb)
        if tx0 >= tx1 or ty0 >= ty1:
            continue
        gy, gx = np.mgrid[ty0:ty1, tx0:tx1].astype(np.float32)
        dx, dy = gx + 0.5 - cx[i], gy + 0.5 - cy[i]
        c, s = math.cos(ang[i]), math.sin(ang[i])
        q = np.sqrt(((dx * c + dy * s) / ra) ** 2 + ((-dx * s + dy * c) / rb) ** 2)
        mk = np.clip((1.0 - q) * rb / 1.2 + 0.5, 0.0, 1.0)[..., None]          # ~1.2 texel AA edge
        sy0, sx0 = sy[pick[i]] + (ty0 - icy), sx[pick[i]] + (tx0 - icx)
        pasted = base[ty0:ty1, tx0:tx1] + det[sy0:sy0 + (ty1 - ty0), sx0:sx0 + (tx1 - tx0)]
        lay = layer[ty0:ty1, tx0:tx1]
        lay *= 1.0 - mk
        lay += pasted * mk
        al = alpha[ty0:ty1, tx0:tx1]
        al *= 1.0 - mk[..., 0]
        al += mk[..., 0]
        placed += 1
    log(f"patches: {placed} placed of {n} drawn (coverage {COVERAGE} above v {V_D[1]})  [{time.time() - t0:.0f} s]")
    return dict(layer=layer, alpha=alpha, H0=H0, W0=W0, k1=k1, hb=hb, v_b0=v_b0, v_b1=v_b1)


def write_res(g, nres, log):
    """Composite the generated layer over this resolution's own painting rows and write the band PNG."""
    path = os.path.join(PAINT, f"seurat_grande_jatte_{nres}.jpg")
    pimg = cv2.imread(path, cv2.IMREAD_COLOR)
    hn, wn = pimg.shape[:2]
    k0 = int(round(K0_SRC * hn / g["H0"]))
    k1 = int(round(g["k1"] * hn / g["H0"]))
    hb = k0 + k1
    if nres == SRC_N:
        lay, al = g["layer"], g["alpha"]
    else:
        lay = cv2.resize(g["layer"], (wn, hb), interpolation=cv2.INTER_AREA)
        al = cv2.resize(g["alpha"], (wn, hb), interpolation=cv2.INTER_AREA)
    under = np.zeros((hb, wn, 3), np.float32)
    under[k1:] = pimg[:k0].astype(np.float32)
    out = under * (1.0 - al[..., None]) + lay
    out = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, f"seurat_grande_jatte_{nres}_topband.png")
    cv2.imwrite(fn, out, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    # the painting rows below the patch ramp must equal this resolution's JPEG exactly
    vrow = 1.0 + k1 / hn - (np.arange(hb) + 0.5) / hn
    clean = (vrow < V_D[0] - 0.004) & (np.arange(hb) >= k1)
    same = bool(np.array_equal(out[clean], pimg[:k0][clean[k1:]]))
    log(f"{nres}: {fn} {wn}x{hb} (k0 {k0}, k1 {k1}); painting rows below v {V_D[0] - 0.004:.4f} identical: {same}")
    assert same, "painting rows changed under the band"
    return {"file": os.path.relpath(fn, ROOT), "width": wn, "rows": hb, "painting_rows": k0, "rows_above_v1": k1,
            "image_height": hn, "v_b0": 1.0 - k0 / hn, "v_b1": 1.0 + k1 / hn}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--res", default="20000,8192,2048")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    log = lambda s: print(f"[seurat_ext] {s}", flush=True)
    g = build(a.seed, log)
    out = {}
    for r in [int(x) for x in a.res.split(",")]:
        out[str(r)] = write_res(g, r, log)
    st = os.stat(SRC)
    meta = {"generator": "scripts/make_seurat_ext.py", "seed": a.seed, "source": os.path.relpath(SRC, ROOT),
            "source_size": st.st_size, "source_mtime": int(st.st_mtime),
            "uv_convention": "Blender UV of the canvas plane, v from the BOTTOM (painting v 0..1)",
            "band_mapping": "band v' = (v - v_b0) / (v_b1 - v_b0), extension EXTEND, interpolation Linear",
            "shader_crossfade_v": list(V_X), "patch_ramp_start_v": list(V_D0), "patch_ramp_full_v": list(V_D1),
            "border_lowest_v": 0.9811, "sigma_ramp_u_texels": SIG_RAMP_U,
            "seam_base_v": list(V_SEAM), "reflect_lowpass_about_v": V_REFLECT,
            "params": {"source_v": list(V_SRC), "source_u": list(U_SRC), "sigma_detail": SIG_D, "octaves": list(OCT),
                       "sigma_base_u": SIG_BASE_U, "radius_texels_20000": list(R_RANGE), "aspect": list(ASPECT),
                       "coverage": COVERAGE, "erode_texels": ERODE, "clusters": N_CLUSTERS, "drift_top": DRIFT_TOP,
                       "octave_gain": OCT_GAIN},
            "res": out}
    jp = os.path.join(OUT, "seurat_grande_jatte_ext.json")
    with open(jp, "w") as f:
        json.dump(meta, f, indent=1)
    log(f"geometry -> {jp}")


if __name__ == "__main__":
    main()
