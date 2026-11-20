"""Generate the film's environment map ("candy sky"), deterministic, no randomness.

Run:  tools/venv/bin/python -I scripts/make_candy_sky.py [--width 4096]

Writes
  assets/hdri/candy_sky_4k.hdr        sky + 8 candy cards + compact sun (S01 phase B lighting)
  assets/hdri/candy_sky_nosun_4k.hdr  same without the sun/aureole (reflection/ambient env for S02-S04)
  assets/hdri/candy_sky_preview.png   2048x1024 tonemapped sRGB preview (S01 globe texture + lat-long overlay)

Convention (verified 2026-11-20 by a top-view sundial render: theta=0 -> shadow az 315, theta=90 -> 45): equirect, pixel (row r, col c):
  u = (c+.5)/W, v = 1-(r+.5)/H, Blender world azimuth (CCW from +X) a = pi - 2*pi*u, elevation e = (v-.5)*pi.
  Image centre (u=.5) is +X, top row is the zenith.
"""
import argparse
import os

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "assets", "hdri")

PAL = {
    "pink": "#FF4D9D", "orange": "#FF8A1F", "lemon": "#FFD23F", "lime": "#B5E61D", "mint": "#2ED8A3",
    "aqua": "#1FC2EE", "blue": "#2E5BFF", "violet": "#8A5CF6",
    "sky": "#CDE9FF", "lavender": "#E5DAFF", "cream": "#FFF6EC", "blush": "#FFD3E4",
}
SUN_HEX = "#FFF2D8"
CARDS = ["pink", "orange", "lemon", "lime", "mint", "aqua", "blue", "violet"]
SUN_AZ, SUN_EL, SUN_R = 135.0, 40.0, 1.2          # degrees
TARGET_RATIO = 3.5                                 # E_sun / E_rest on a horizontal plane


def lin(hexstr):
    h = hexstr.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def lum(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def build(W):
    H = W // 2
    c = (np.arange(W) + 0.5) / W
    r = (np.arange(H) + 0.5) / H
    u, v = np.meshgrid(c, 1.0 - r)
    az = np.pi - 2 * np.pi * u                      # radians, CCW from +X
    el = (v - 0.5) * np.pi
    eld = np.degrees(el)
    azd = np.degrees(az) % 360.0

    img = np.zeros((H, W, 3), np.float64)
    # sky
    w = smoothstep(np.clip(eld, 0, 90) / 90.0) ** 0.8
    sky = lin(PAL["sky"]) * (1 - w[..., None]) + lin(PAL["lavender"]) * w[..., None]
    haze = 0.5 * (1.0 - smoothstep(np.clip(eld, 0, None) / 6.0))
    sky = sky * (1 - haze[..., None]) + lin(PAL["cream"]) * haze[..., None]
    ground = lin(PAL["blush"]) * 0.55
    t = smoothstep((eld + 0.2) / 0.4)[..., None]     # crisp 0.4 deg horizon
    img = ground * (1 - t) + sky * t

    # candy cards: rounded rectangles in (azimuth, elevation) degrees
    hw, e0, e1, rad, aa = 14.0, -12.0, 24.0, 4.0, 0.15
    for k, name in enumerate(CARDS):
        ca = 22.5 + 45.0 * k
        da = (azd - ca + 180.0) % 360.0 - 180.0
        # signed distance to rounded box centred at (0, (e0+e1)/2)
        ec, he = 0.5 * (e0 + e1), 0.5 * (e1 - e0)
        qx = np.abs(da) - (hw - rad)
        qy = np.abs(eld - ec) - (he - rad)
        outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
        inside = np.minimum(np.maximum(qx, qy), 0)
        sd = outside + inside - rad
        a = smoothstep(0.5 - sd / (2 * aa))[..., None]
        img = img * (1 - a) + (lin(PAL[name]) * 2.0) * a

    nosun = img.copy()

    # sun + aureole
    sa, se = np.radians(SUN_AZ), np.radians(SUN_EL)
    sdir = np.array([np.cos(se) * np.cos(sa), np.cos(se) * np.sin(sa), np.sin(se)])
    dirs = np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], -1)
    delta = np.degrees(np.arccos(np.clip(dirs @ sdir, -1, 1)))
    disc = smoothstep(0.5 - (delta - SUN_R) / (2 * 0.06))   # ~1 px anti-aliased edge
    sun_col = lin(SUN_HEX)
    aureole = sun_col * 3.0 * np.exp(-(delta / 4.0) ** 2)[..., None] * (1 - disc[..., None])
    rest = img + aureole

    # horizontal-plane irradiance weights: L * cos(theta_zenith) * dOmega
    dA = (2 * np.pi / W) * (np.pi / H)
    wgt = np.where(el > 0, np.sin(el) * np.cos(el) * dA, 0.0)
    E_rest = np.sum(lum(rest * (1 - disc[..., None])) * wgt)
    E_disc_unit = np.sum(lum(sun_col[None, None, :] * disc[..., None]) * wgt)
    L_sun = TARGET_RATIO * E_rest / E_disc_unit
    sunimg = rest * (1 - disc[..., None]) + (sun_col * L_sun) * disc[..., None]
    E_sun = np.sum(lum(sun_col * L_sun * disc[..., None]) * wgt)
    print(f"[candy_sky] {W}x{H}  sun radiance per channel = {np.round(sun_col * L_sun, 2)}  "
          f"E_sun/E_rest = {E_sun / E_rest:.3f}  (target {TARGET_RATIO})")
    up = el > 0
    print(f"[candy_sky] mean upper-hemisphere colour (linear) = {np.round(nosun[up].mean(0), 4)}")
    return sunimg.astype(np.float32), nosun.astype(np.float32)


def write_hdr(path, rgb):
    cv2.imwrite(path, np.ascontiguousarray(rgb[..., ::-1]))
    print("[candy_sky] wrote", path)


def preview(path, rgb, W=2048):
    """Hue-preserving soft shoulder on the max channel (keeps palette hues: sky reads #CDE9FF-ish, cards stay
    candy, sun -> warm white). Plain x/(1+x) greyed the pastels, so it is not used."""
    H = W // 2
    x = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_AREA).astype(np.float64)
    m = np.max(x, axis=-1, keepdims=True)
    knee = 0.8
    mt = np.where(m < knee, m, knee + (1 - knee) * np.tanh((m - knee) / (1 - knee)))
    x = x * (mt / np.maximum(m, 1e-8))
    s = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    cv2.imwrite(path, np.clip(np.round(s[..., ::-1] * 255), 0, 255).astype(np.uint8))
    print("[candy_sky] wrote", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=4096)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sun, nosun = build(a.width)
    write_hdr(os.path.join(a.out, "candy_sky_4k.hdr"), sun)
    write_hdr(os.path.join(a.out, "candy_sky_nosun_4k.hdr"), nosun)
    preview(os.path.join(a.out, "candy_sky_preview.png"), sun)
