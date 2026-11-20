#!/usr/bin/env python3
"""qa_diff.py: frame-difference QA for the LaRenderer opening (storyboard section 7).

Mean |difference| is reported in 8-bit levels (x/255) whatever the bit depth of the inputs (16-bit finals are
compared at full precision). Crops are given in film pixels (1920x1080) and scaled to the frame's real size,
so the same crop works on 960x540 previews. Every run writes a heat-map PNG (|diff| through a colour ramp,
captioned with the numbers). Exit code: 0 pass or no threshold, 1 above --max, 2 missing frames.

  # two frames
  tools/venv/bin/python -I scripts/qa_diff.py pair A.png B.png [--crop X,Y,W,H] [--max 0.5] [--heatmap out.png]
  # consecutive frames of a shot (or any folder of f_####.png) -> per-pair means, CSV and a mean-|diff| heat-map
  tools/venv/bin/python -I scripts/qa_diff.py range s03_gummy --frames 31-60 [--mode final] [--crop ...] [--max 1]
  tools/venv/bin/python -I scripts/qa_diff.py range renders/film_comp --frames 440-460
  # storyboard section 7 presets (frames resolved under renders/<mode>/<shot>/)
  tools/venv/bin/python -I scripts/qa_diff.py check s01-loop             # |f195 - f135| < 0.5/255
  tools/venv/bin/python -I scripts/qa_diff.py check s03-static --crop X,Y,W,H   # f31-60 consecutive < 1/255
  tools/venv/bin/python -I scripts/qa_diff.py check s04-hold             # f106-165 centre 400x400: drift only
  tools/venv/bin/python -I scripts/qa_diff.py check s02-strip            # f61-72 caustic strip (boiling look)

Heat-maps default to renders/qa/<name>.png. The colour ramp maps 0 -> black and --scale levels (default: the
larger of 4/255 and the 99.5th percentile) -> white.
"""
import argparse
import csv
import json
import os
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
QA_DIR = os.path.join(ROOT, "renders", "qa")
FW, FH = 1920, 1080

PRESETS = {
    "s01-loop": dict(kind="pair", shot="s01_lights_world", a=195, b=135, max=0.5,
                     note="theta=360 must reproduce theta=0 frame for frame"),
    "s03-static": dict(kind="range", shot="s03_gummy", frames="31-60", max=1.0,
                       note="static stripe/block region while the gummy moves: pass --crop for that region"),
    "s04-hold": dict(kind="range", shot="s04_every_dot", frames="106-165", crop=(760, 340, 400, 400), max=None,
                     note="1:1 hold: only the 0.1 px/f drift may show (no shimmer, no swimming)"),
    "s02-strip": dict(kind="range", shot="s02_caustics", frames="61-72", max=None,
                      note="12-frame caustic strip: look for blotch boiling in the heat-map"),
}


def load(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED) if os.path.isfile(path) else None
    if im is None:
        return None
    sc = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32) / sc
    if im.ndim == 2:
        im = im[..., None]
    return im[..., :3] if im.shape[2] >= 3 else im


def crop_px(crop, shape):
    """Film-pixel crop (x, y, w, h) -> slices for an image of `shape`."""
    if crop is None:
        return slice(None), slice(None)
    h, w = shape[:2]
    sx, sy = w / FW, h / FH
    x, y, cw, ch = crop
    x0, y0 = int(round(x * sx)), int(round(y * sy))
    x1, y1 = int(round((x + cw) * sx)), int(round((y + ch) * sy))
    return slice(max(0, y0), min(h, y1)), slice(max(0, x0), min(w, x1))


def absdiff(a, b, crop):
    if a.shape != b.shape:
        raise SystemExit(f"[qa_diff] size mismatch {a.shape} vs {b.shape}")
    ys, xs = crop_px(crop, a.shape)
    return np.abs(a[ys, xs] - b[ys, xs])


def heatmap(dmap, out, title, scale=None, base=None):
    """dmap: per-pixel |diff| (0..1 units, single channel). Writes a captioned colour heat-map
    (optionally side by side with `base`, the first frame's crop)."""
    lv = dmap * 255.0
    s = scale if scale else max(4.0, float(np.percentile(lv, 99.5)))
    ramp = cv2.applyColorMap(np.clip(lv / s * 255.0, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    tiles = [ramp]
    if base is not None:
        b = (np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)              # load() keeps OpenCV's BGR order
        tiles.insert(0, b if b.shape[2] == 3 else cv2.cvtColor(b, cv2.COLOR_GRAY2BGR))
    img = np.concatenate(tiles, axis=1)
    if img.shape[1] > 2400:
        k = 2400 / img.shape[1]
        img = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    bar = np.full((64, img.shape[1], 3), 24, np.uint8)
    cv2.putText(bar, title[:150], (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bar, f"ramp: black 0 -> white {s:.2f}/255 (inferno)", (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (200, 200, 200), 1, cv2.LINE_AA)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cv2.imwrite(out, np.concatenate([bar, img], axis=0))
    return out


def parse_frames(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part.strip():
            out.append(int(part))
    return out


def resolve_dir(src, mode):
    """A shot id (-> renders/<mode>/<id>) or a folder path."""
    d = src if os.path.isdir(src) else os.path.join(ROOT, src)
    if os.path.isdir(d) and not os.path.isdir(os.path.join(ROOT, "renders", mode, src)):
        return d
    return os.path.join(ROOT, "renders", mode, src)


def frame_path(d, f, prefix):
    return os.path.join(d, f"{prefix}{f:04d}.png")


def report(name, value, limit, extra=""):
    verdict = "" if limit is None else ("PASS" if value < limit else "FAIL")
    lim = "" if limit is None else f" (limit {limit}/255)"
    print(f"[qa_diff] {name}: mean |diff| = {value:.3f}/255{lim} {verdict} {extra}".rstrip())
    return limit is None or value < limit


def do_pair(a_path, b_path, crop, limit, out, scale, label=None):
    a, b = load(a_path), load(b_path)
    miss = [p for p, im in ((a_path, a), (b_path, b)) if im is None]
    if miss:
        print("[qa_diff] missing/unreadable:", ", ".join(os.path.relpath(p, ROOT) for p in miss))
        return 2
    d = absdiff(a, b, crop)
    mean = float(d.mean()) * 255
    mx = float(d.max()) * 255
    p99 = float(np.percentile(d, 99.0)) * 255
    name = label or f"{os.path.basename(a_path)} vs {os.path.basename(b_path)}"
    ok = report(name, mean, limit, f"(max {mx:.2f}, p99 {p99:.2f}; crop {crop or 'full'})")
    ys, xs = crop_px(crop, a.shape)
    out = out or os.path.join(QA_DIR, f"pair_{os.path.splitext(os.path.basename(a_path))[0]}_"
                                      f"{os.path.splitext(os.path.basename(b_path))[0]}.png")
    heatmap(d.max(axis=2), out, f"{name}: mean {mean:.3f}/255  max {mx:.2f}  p99 {p99:.2f}", scale, a[ys, xs])
    print(f"[qa_diff] heat-map {os.path.relpath(out, ROOT)}")
    return 0 if ok else 1


def do_range(d, frames, prefix, crop, limit, out, scale, csv_path, label):
    paths = [frame_path(d, f, prefix) for f in frames]
    missing = [f for f, p in zip(frames, paths) if not os.path.exists(p)]
    if missing:
        print(f"[qa_diff] {len(missing)} missing frames in {os.path.relpath(d, ROOT)}: {missing[:20]}"
              f"{' ...' if len(missing) > 20 else ''}")
        return 2
    prev, acc, rows, first = None, None, [], None
    for f, p in zip(frames, paths):
        im = load(p)
        if im is None:
            print(f"[qa_diff] unreadable {os.path.relpath(p, ROOT)}")
            return 2
        if prev is not None:
            dd = absdiff(im, prev, crop)
            m = float(dd.mean()) * 255
            rows.append((f - 1, f, m, float(dd.max()) * 255))
            dm = dd.max(axis=2)
            acc = dm if acc is None else acc + dm
        else:
            ys, xs = crop_px(crop, im.shape)
            first = im[ys, xs]
        prev = im
    means = [r[2] for r in rows]
    worst = max(rows, key=lambda r: r[2])
    name = label or f"{os.path.basename(os.path.normpath(d))} f{frames[0]}-{frames[-1]}"
    ok = report(name, max(means), limit, f"(worst pair f{worst[0]}->f{worst[1]}; average {np.mean(means):.3f}; "
                                         f"{len(rows)} pairs; crop {crop or 'full'})")
    out = out or os.path.join(QA_DIR, f"range_{name.replace(' ', '_')}.png")
    heatmap(acc / len(rows), out, f"{name}: mean of consecutive |diff| (worst pair {worst[2]:.3f}/255 at "
                                  f"f{worst[0]}->f{worst[1]})", scale, first)
    print(f"[qa_diff] heat-map {os.path.relpath(out, ROOT)}")
    csv_path = csv_path or os.path.splitext(out)[0] + ".csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frame_a", "frame_b", "mean_abs_diff_255", "max_abs_diff_255"])
        for r in rows:
            w.writerow([r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.3f}"])
    print(f"[qa_diff] per-pair values {os.path.relpath(csv_path, ROOT)}")
    return 0 if ok else 1


def parse_crop(s):
    if not s:
        return None
    v = [int(float(x)) for x in s.split(",")]
    if len(v) != 4:
        raise SystemExit("--crop takes X,Y,W,H in film pixels (1920x1080)")
    return tuple(v)


def main():
    ap = argparse.ArgumentParser(description="Frame-difference QA (storyboard section 7).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--crop", default=None, help="X,Y,W,H in film pixels (scaled for previews)")
    common.add_argument("--max", type=float, default=None, help="pass threshold for mean |diff|, in /255 levels")
    common.add_argument("--heatmap", default=None, help="heat-map PNG path (default renders/qa/...)")
    common.add_argument("--scale", type=float, default=None, help="levels mapped to white in the heat-map")
    p1 = sub.add_parser("pair", parents=[common])
    p1.add_argument("a")
    p1.add_argument("b")
    p2 = sub.add_parser("range", parents=[common])
    p2.add_argument("src", help="shot id (renders/<mode>/<id>) or a folder of <prefix>####.png")
    p2.add_argument("--frames", required=True, help="'31-60' or '1,5,9' (consecutive pairs in this order)")
    p2.add_argument("--mode", default="final", choices=["final", "preview", "draft"])
    p2.add_argument("--prefix", default="f_")
    p2.add_argument("--csv", default=None)
    p3 = sub.add_parser("check", parents=[common])
    p3.add_argument("preset", choices=sorted(PRESETS))
    p3.add_argument("--mode", default="final", choices=["final", "preview", "draft"])
    a = ap.parse_args()
    crop = parse_crop(a.crop)

    if a.cmd == "pair":
        sys.exit(do_pair(a.a, a.b, crop, a.max, a.heatmap, a.scale))
    if a.cmd == "range":
        d = resolve_dir(a.src, a.mode)
        sys.exit(do_range(d, parse_frames(a.frames), a.prefix, crop, a.max, a.heatmap, a.scale, a.csv, None))
    P = PRESETS[a.preset]
    print(f"[qa_diff] {a.preset} ({a.mode}): {P['note']}")
    d = os.path.join(ROOT, "renders", a.mode, P["shot"])
    limit = a.max if a.max is not None else P.get("max")
    crop = crop or P.get("crop")
    out = a.heatmap or os.path.join(QA_DIR, f"{a.preset}_{a.mode}.png")
    if P["kind"] == "pair":
        sys.exit(do_pair(frame_path(d, P["a"], "f_"), frame_path(d, P["b"], "f_"), crop, limit, out, a.scale,
                         f"{a.preset} f{P['a']} vs f{P['b']}"))
    if a.preset == "s03-static" and crop is None:
        print("[qa_diff] note: no --crop given, so the whole frame (moving gummy included) is measured")
    sys.exit(do_range(d, parse_frames(P["frames"]), "f_", crop, limit, out, a.scale, None, f"{a.preset}_{a.mode}"))


if __name__ == "__main__":
    main()
