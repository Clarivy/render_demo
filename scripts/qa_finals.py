"""Final-render QA for the LaRenderer opening (CPU only).

    tools/venv/bin/python -I scripts/qa_finals.py [--shots s01_lights_world,...] [--jobs 16]

For every final frame it checks:
  * completeness and readability (16-bit PNG, 1920x1080);
  * a sudden luminance jump vs its neighbours (black or NaN frames, missing lights);
  * final vs preview, block by block. Both come from the same deterministic script, so after downscaling the
    final to 960x540 the two differ only by noise and denoising. A vanished object (Cycles persistent-data
    bug), a missing texture or a wrong camera shows up as a large local block difference.
Then it runs the storyboard section-7 presets with scripts/qa_diff.py on the finals.
Writes logs/finals/qa_report.json and renders/qa/finals_outliers.png (worst blocks, if any).

Film v2 (docs/storyboard_v2.md section 6): --film v2 (default v1: everything above, unchanged)
    tools/venv/bin/python -I scripts/qa_finals.py --film v2 [--mode final|preview] [--require-complete]
    tools/venv/bin/python -I scripts/qa_finals.py --film v2 --selftest [--selftest-dir DIR]
  Shots from docs/shots_v2.json (S01-S03 = the v1 shots, s04_subject, s05_finale). For each: the v1 frame checks
  above (in --mode preview: completeness, size and luma spikes only). Then the presets:
    s01-loop, s02-strip, s03-static   v1 section-7 presets via scripts/qa_diff.py (heat-maps in renders/qa/v2/)
    s04-subject-hold   s04_subject f150-180 static: every consecutive pair mean |d| <= 0.5/255 (bit-identical
                       expected with the static seed; the count of identical pairs is reported)
    s04-overscan       renders/<mode>/s04_subject/overscan.png: its centred frame-size crop (final offset
                       x 312, y 562) vs f180, 1 px Gaussian blur on both, mean |d| <= 1/255, p99 reported
    seam               s04_subject f180 vs s05_finale f1, 1 px Gaussian blur on both: mean |d| <= 1/255 and
                       p99 <= 4/255
    title-unchanged    s05_finale f121-180 vs v1 s05_title f61-120 (same mode): mean |d| <= 3/255 below
                       y = 420 px (film px) on every pair, and every letter's box (left, top, right; found by its
                       hue above the floor line y 700) within +-2 px
    tiles-final        renders/hex_tiles/manifest.json: every tile and the centre still say source "final", every
                       tile folder holds h_0001..h_<frames>, the still has the manifest's size. Tiles still built
                       from previews/placeholders are "incomplete" (not rendered yet), not a FAIL
  "1 px blur" = cv2.GaussianBlur sigma 1.0 px at the image's own resolution. Mean |d| is per channel and pixel
  in /255 display levels at full bit depth. Anything not rendered yet is reported as "missing" (never a crash).
  Report: logs/finals_v2/qa_report.json (preview: qa_report_preview.json); heat-maps renders/qa/v2/.
  Exit 0 = no FAIL (missing allowed unless --require-complete), 1 = a FAIL (or missing with --require-complete).
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SHOTS = ["s01_lights_world", "s02_caustics", "s03_gummy", "s04_every_dot", "s05_title"]
BLOCK = 24                       # px at 960x540
FLAG_BLOCK = 0.12                # mean |diff| of a block, in 0..1 display units
PY = os.path.join(ROOT, "tools", "venv", "bin", "python")


def load_disp(path, size=None):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    im = im[..., :3].astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    if size is not None and (im.shape[1], im.shape[0]) != size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_AREA)
    return im


def frame_stats(args):
    sid, f = args
    fin = os.path.join(ROOT, "renders", "final", sid, f"f_{f:04d}.png")
    pre = os.path.join(ROOT, "renders", "preview", sid, f"f_{f:04d}.png")
    a = load_disp(fin)
    if a is None:
        return {"frame": f, "ok": False}
    out = {"frame": f, "ok": True, "shape": list(a.shape[:2]), "finite": bool(np.isfinite(a).all()),
           "luma": float((a @ np.array([0.0722, 0.7152, 0.2126], np.float32)).mean())}  # BGR weights
    b = load_disp(pre)
    if b is not None:
        a2 = cv2.resize(a, (b.shape[1], b.shape[0]), interpolation=cv2.INTER_AREA)
        d = np.abs(a2 - b).mean(-1)
        h, w = (d.shape[0] // BLOCK) * BLOCK, (d.shape[1] // BLOCK) * BLOCK
        blocks = d[:h, :w].reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).mean((1, 3))
        iy, ix = np.unravel_index(np.argmax(blocks), blocks.shape)
        out.update({"pv_mean": float(d.mean()), "pv_block_max": float(blocks.max()),
                    "pv_block_xy": [int(ix * BLOCK * 2), int(iy * BLOCK * 2)]})   # in 1080p px
    return out


def main_v1(a):
    table = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "docs", "shots.json")))}
    report = {}
    worst = []
    for sid in [s for s in SHOTS if s in a.shots.split(",")]:
        n = table[sid]["frames"]
        with ProcessPoolExecutor(a.jobs) as ex:
            stats = list(ex.map(frame_stats, [(sid, f) for f in range(1, n + 1)]))
        missing = [s["frame"] for s in stats if not s["ok"]]
        ok = [s for s in stats if s["ok"]]
        bad_shape = [s["frame"] for s in ok if s["shape"] != [1080, 1920]]
        nonfinite = [s["frame"] for s in ok if not s["finite"]]
        lum = np.array([s["luma"] for s in ok])
        jumps = []
        for i in range(1, len(ok) - 1):        # luminance spike vs both neighbours (single-frame glitches)
            l0, l1, l2 = lum[i - 1], lum[i], lum[i + 1]
            if abs(l1 - l0) > 0.06 and abs(l1 - l2) > 0.06 and np.sign(l1 - l0) == np.sign(l1 - l2):
                jumps.append(ok[i]["frame"])
        pv = [s for s in ok if "pv_block_max" in s]
        flagged = sorted([s for s in pv if s["pv_block_max"] > FLAG_BLOCK], key=lambda s: -s["pv_block_max"])
        worst += [(sid, s) for s in flagged[:6]]
        report[sid] = {
            "frames": n, "missing": missing, "bad_shape": bad_shape, "nonfinite": nonfinite,
            "single_frame_luma_spikes": jumps,
            "final_vs_preview": {
                "compared": len(pv),
                "mean_of_mean_diff": round(float(np.mean([s["pv_mean"] for s in pv])), 4) if pv else None,
                "median_block_max": round(float(np.median([s["pv_block_max"] for s in pv])), 4) if pv else None,
                "flagged_frames": [[s["frame"], round(s["pv_block_max"], 3), s["pv_block_xy"]] for s in flagged],
            },
        }
        print(f"[qa] {sid}: missing {len(missing)}, luma spikes {jumps}, final-vs-preview flagged "
              f"{len(flagged)} (median block max {report[sid]['final_vs_preview']['median_block_max']})", flush=True)

    # storyboard section-7 presets on the finals (only for shots that are complete)
    presets = {"s01_lights_world": ["check", "s01-loop", "--mode", "final"],
               "s02_caustics": ["check", "s02-strip", "--mode", "final"],
               "s03_gummy": ["check", "s03-static", "--mode", "final", "--crop", "40,40,460,380"],
               "s04_every_dot": ["check", "s04-hold", "--mode", "final"]}
    for sid, cmd in presets.items():
        if sid in report and not report[sid]["missing"]:
            r = subprocess.run([PY, "-I", os.path.join(ROOT, "scripts", "qa_diff.py")] + cmd, cwd=ROOT,
                               capture_output=True, text=True)
            report[sid]["section7"] = {"exit": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-4:]}
            print(f"[qa] {sid} section-7 {cmd[1]}: exit {r.returncode} | {report[sid]['section7']['tail'][-1:]}")

    os.makedirs(os.path.join(ROOT, "logs", "finals"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "finals", "qa_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    if worst:     # crops of the worst flagged blocks: final | preview
        tiles = []
        for sid, s in worst[:12]:
            fr, (x, y) = s["frame"], s["pv_block_xy"]
            fa = load_disp(os.path.join(ROOT, "renders", "final", sid, f"f_{fr:04d}.png"))
            fb = load_disp(os.path.join(ROOT, "renders", "preview", sid, f"f_{fr:04d}.png"), (1920, 1080))
            x0, y0 = max(0, min(1920 - 240, x - 96)), max(0, min(1080 - 240, y - 96))
            crop = np.concatenate([fa[y0:y0 + 240, x0:x0 + 240], fb[y0:y0 + 240, x0:x0 + 240]], 1)
            crop = (np.clip(crop, 0, 1) * 255).astype(np.uint8)
            cv2.putText(crop, f"{sid[:3]} f{fr} {s['pv_block_max']:.2f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                        (0, 0, 0), 2)
            cv2.putText(crop, f"{sid[:3]} f{fr} {s['pv_block_max']:.2f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                        (255, 255, 255), 1)
            tiles.append(crop)
        rows = [np.concatenate(tiles[i:i + 3] + [np.zeros_like(tiles[0])] * (3 - len(tiles[i:i + 3])), 1)
                for i in range(0, len(tiles), 3)]
        os.makedirs(os.path.join(ROOT, "renders", "qa"), exist_ok=True)
        cv2.imwrite(os.path.join(ROOT, "renders", "qa", "finals_outliers.png"), np.concatenate(rows, 0))
        print("[qa] worst blocks (final | preview): renders/qa/finals_outliers.png")
    print("[qa] report: logs/finals/qa_report.json")


# =================================================================================================================
# film v2 (storyboard_v2 section 6)
V2_TABLE = os.path.join(ROOT, "docs", "shots_v2.json")
V2_LOGDIR = os.path.join(ROOT, "logs", "finals_v2")
V2_QA_DIR = os.path.join(ROOT, "renders", "qa", "v2")
HEX_DIR = os.path.join(ROOT, "renders", "hex_tiles")
V1_PRESETS = {"s01_lights_world": ("s01-loop", []), "s02_caustics": ("s02-strip", []),
              "s03_gummy": ("s03-static", ["--crop", "40,40,460,380"])}
HOLD_MAX, SEAM_MEAN, SEAM_P99, OVERSCAN_MEAN = 0.5, 1.0, 4.0, 1.0
TITLE_MEAN, TITLE_Y, TITLE_FLOOR_Y, TITLE_BOX_TOL = 3.0, 420, 700, 2
# letter hues (OpenCV float HSV degrees), measured on v1 s05_title f90: L a R e n d e r e r
TITLE_HUES = [("L", 330), ("a", 358), ("R", 19), ("e", 42), ("n", 72), ("d", 164), ("e", 195), ("r", 232),
              ("e", 255), ("r", 292)]


def load_v2(path, size=None):
    """load_disp for v2 inputs that may not exist yet (no OpenCV warning for a missing file)."""
    return load_disp(path, size) if os.path.isfile(path) else None


def ranges(nums):
    out, nums = [], sorted(nums)
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}" if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(out)


def rel(p):
    return os.path.relpath(p, ROOT)


def fpath(mode, sid, f):
    return os.path.join(ROOT, "renders", mode, sid, f"f_{f:04d}.png")


def png_size(path):
    """(width, height) from the PNG header, or None."""
    try:
        with open(path, "rb") as fh:
            h = fh.read(24)
    except OSError:
        return None
    if len(h) < 24 or h[:8] != b"\x89PNG\r\n\x1a\n" or h[12:16] != b"IHDR":
        return None
    return int.from_bytes(h[16:20], "big"), int.from_bytes(h[20:24], "big")


def blur1(im):
    return cv2.GaussianBlur(im, (0, 0), 1.0)


def dstats(d):
    return {"mean": round(float(d.mean()) * 255, 4), "p99": round(float(np.percentile(d, 99.0)) * 255, 3),
            "max": round(float(d.max()) * 255, 3)}


def heatmap(dmap, out, title, base=None):
    """Same look as scripts/qa_diff.py: |diff| through inferno, captioned (qa_diff is read-only here)."""
    lv = dmap * 255.0
    s = max(4.0, float(np.percentile(lv, 99.5)))
    ramp = cv2.applyColorMap(np.clip(lv / s * 255.0, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    tiles = [ramp]
    if base is not None:
        tiles.insert(0, (np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8))
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


def frame_stats_v2(args):
    """v1 frame checks for one frame of `mode`; final frames are also compared with the preview."""
    sid, f, mode = args
    a = load_v2(fpath(mode, sid, f))
    if a is None:
        return {"frame": f, "ok": False}
    out = {"frame": f, "ok": True, "shape": list(a.shape[:2]), "finite": bool(np.isfinite(a).all()),
           "luma": float((a @ np.array([0.0722, 0.7152, 0.2126], np.float32)).mean())}
    if mode == "final":
        b = load_v2(fpath("preview", sid, f))
        if b is not None:
            a2 = cv2.resize(a, (b.shape[1], b.shape[0]), interpolation=cv2.INTER_AREA)
            d = np.abs(a2 - b).mean(-1)
            h, w = (d.shape[0] // BLOCK) * BLOCK, (d.shape[1] // BLOCK) * BLOCK
            blocks = d[:h, :w].reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).mean((1, 3))
            iy, ix = np.unravel_index(np.argmax(blocks), blocks.shape)
            out.update({"pv_mean": float(d.mean()), "pv_block_max": float(blocks.max()),
                        "pv_block_xy": [int(ix * BLOCK * 2), int(iy * BLOCK * 2)]})
    return out


# ---- v2 checks (path based, so the self-test can feed them known inputs) -------------------------------------
def check_pair_blur(a_path, b_path, heat, mean_max, p99_max, label):
    a, b = load_v2(a_path), load_v2(b_path)
    miss = [rel(p) for p, im in ((a_path, a), (b_path, b)) if im is None]
    if miss:
        return {"status": "missing", "missing": miss}
    if a.shape != b.shape:
        return {"status": "FAIL", "error": f"size mismatch {list(a.shape[:2])} vs {list(b.shape[:2])}"}
    d = np.abs(blur1(a) - blur1(b))
    s = dstats(d)
    ok = s["mean"] <= mean_max and (p99_max is None or s["p99"] <= p99_max)
    heatmap(d.max(axis=2), heat, f"{label}: mean {s['mean']:.3f}/255  p99 {s['p99']:.2f}  max {s['max']:.1f} "
                                 f"(1 px blur)", a)
    return {"status": "PASS" if ok else "FAIL", **s, "limit_mean": mean_max, "limit_p99": p99_max,
            "a": rel(a_path), "b": rel(b_path), "heatmap": rel(heat)}


def check_overscan(os_path, f_path, heat, expect_size=None):
    o, f = load_v2(os_path), load_v2(f_path)
    miss = [rel(p) for p, im in ((os_path, o), (f_path, f)) if im is None]
    if miss:
        return {"status": "missing", "missing": miss}
    (H, W), (Ho, Wo) = f.shape[:2], o.shape[:2]
    if Ho < H or Wo < W:
        return {"status": "FAIL", "error": f"overscan {Wo}x{Ho} smaller than the frame {W}x{H}"}
    x0, y0 = (Wo - W) // 2, (Ho - H) // 2
    crop = o[y0:y0 + H, x0:x0 + W]
    d = np.abs(blur1(crop) - blur1(f))
    s = dstats(d)
    size_ok = expect_size is None or [Wo, Ho] == list(expect_size)
    ok = s["mean"] <= OVERSCAN_MEAN and size_ok
    heatmap(d.max(axis=2), heat, f"overscan centre crop ({x0},{y0}) vs f180: mean {s['mean']:.3f}/255 "
                                 f"p99 {s['p99']:.2f} (1 px blur)", f)
    return {"status": "PASS" if ok else "FAIL", **s, "limit_mean": OVERSCAN_MEAN, "overscan_size": [Wo, Ho],
            "expected_size": expect_size, "crop_offset": [x0, y0], "heatmap": rel(heat)}


def _pair_absdiff(args):
    pa, pb = args
    a, b = load_v2(pa), load_v2(pb)
    if a is None or b is None or a.shape != b.shape:
        return None
    d = np.abs(a - b)
    return float(d.mean()) * 255, float(d.max()) * 255, bool(not d.any())


def check_hold(paths, frames, jobs, limit=HOLD_MAX):
    miss = [f for f, p in zip(frames, paths) if not os.path.exists(p)]
    if miss:
        return {"status": "missing", "missing_frames": ranges(miss)}
    with ProcessPoolExecutor(jobs) as ex:
        res = list(ex.map(_pair_absdiff, list(zip(paths[:-1], paths[1:]))))
    if any(r is None for r in res):
        return {"status": "FAIL", "error": "unreadable frame or size mismatch in the hold"}
    means = [r[0] for r in res]
    worst = int(np.argmax(means))
    return {"status": "PASS" if max(means) <= limit else "FAIL", "pairs": len(res),
            "max_mean": round(max(means), 4), "worst_pair": [frames[worst], frames[worst + 1]],
            "max_abs": round(max(r[1] for r in res), 3), "bit_identical_pairs": sum(r[2] for r in res),
            "limit_mean": limit}


def letter_boxes(im, y_top=TITLE_Y, y_floor=TITLE_FLOOR_Y, win=12, smin=0.4, vmin=0.3):
    """Per-letter (left, top, right) in film px: each letter is the largest blob of its hue above the floor line
    (the floor reflections and the bottom bevel are cut off there, so bottoms are not compared)."""
    H = im.shape[0]
    k = H / 1080.0
    hsv = cv2.cvtColor(np.ascontiguousarray(im), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    base = (s > smin) & (v > vmin)
    base[:int(round(y_top * k))] = False
    base[int(round(y_floor * k)):] = False
    out = []
    for _, hc in TITLE_HUES:
        m = (base & (np.abs(((h - hc + 180.0) % 360.0) - 180.0) <= win)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, _, st, _ = cv2.connectedComponentsWithStats(m, 8)
        if n <= 1:
            out.append(None)
            continue
        i = 1 + int(np.argmax(st[1:, 4]))
        x, y, w, _, _ = st[i]
        out.append((x / k, y / k, (x + w - 1) / k))
    return out


def _title_pair(args):
    p2, p1, y_top = args
    a, b = load_v2(p2), load_v2(p1)
    if a is None or b is None:
        return None
    if a.shape != b.shape:
        return "size"
    y0 = int(round(y_top * a.shape[0] / 1080.0))
    mean = float(np.abs(a[y0:] - b[y0:]).mean()) * 255
    ba, bb = letter_boxes(a), letter_boxes(b)
    devs = [max(abs(u - w) for u, w in zip(x, y)) if x and y else None for x, y in zip(ba, bb)]
    return mean, devs


def check_title(pairs, jobs, y_top=TITLE_Y, mean_max=TITLE_MEAN, tol=TITLE_BOX_TOL):
    """pairs: [(v2 frame path, v1 frame path)]."""
    miss2 = [rel(p) for p, _ in pairs if not os.path.exists(p)]
    miss1 = [rel(p) for _, p in pairs if not os.path.exists(p)]
    if miss2 or miss1:
        return {"status": "missing", "missing": (miss2[:2] + (["..."] if len(miss2) > 2 else []) +
                                                 miss1[:2] + (["..."] if len(miss1) > 2 else [])),
                "n_missing": len(miss2) + len(miss1)}
    with ProcessPoolExecutor(jobs) as ex:
        res = list(ex.map(_title_pair, [(a, b, y_top) for a, b in pairs]))
    if any(r is None or r == "size" for r in res):
        return {"status": "FAIL", "error": "unreadable frames or v1/v2 size mismatch (compare the same mode)"}
    means = [r[0] for r in res]
    lost = sum(d is None for r in res for d in r[1])
    box = [d for r in res for d in r[1] if d is not None]
    box_max = round(max(box), 2) if box else None
    worst = int(np.argmax(means))
    ok = max(means) <= mean_max and box_max is not None and box_max <= tol + 1e-6 and lost == 0
    return {"status": "PASS" if ok else "FAIL", "pairs": len(res), "max_mean_below_y": round(max(means), 4),
            "avg_mean_below_y": round(float(np.mean(means)), 4), "worst_pair": [rel(x) for x in pairs[worst]],
            "letter_box_max_dev_px": box_max, "letters_not_found": lost, "limit_mean": mean_max, "y_from": y_top,
            "limit_box_px": tol}


def check_tiles(manifest_path, hex_dir):
    if not os.path.exists(manifest_path):
        return {"status": "missing", "missing": [rel(manifest_path)],
                "note": "run scripts/make_hex_tiles.py (render_finals --film v2 does, after the tile scenes)"}
    try:
        with open(manifest_path) as fh:
            m = json.load(fh)
    except (OSError, ValueError) as e:
        return {"status": "FAIL", "error": f"unreadable manifest: {e}"}
    tiles, centre = m.get("tiles") or [], m.get("center") or {}
    n_frames = int(m.get("frames", 180))
    nonfinal = {t.get("id", "?"): t.get("source") for t in tiles if t.get("source") != "final"}
    incomplete = {}
    for t in tiles:
        d = os.path.join(hex_dir, str(t.get("id", "?")))
        have = sum(os.path.exists(os.path.join(d, f"h_{k:04d}.png")) for k in range(1, n_frames + 1))
        if have < n_frames:
            incomplete[t.get("id", "?")] = have
    cpath = centre.get("path") or os.path.join(hex_dir, str(centre.get("id", "c_painting")), "still.png")
    cpath = cpath if os.path.isabs(cpath) else os.path.join(ROOT, cpath)
    csize = png_size(cpath)
    centre_ok = centre.get("source") == "final" and csize is not None and \
        (not centre.get("res") or list(csize) == list(centre["res"]))
    kinds = {}
    for t in tiles:
        kinds[t.get("kind", "?")] = kinds.get(t.get("kind", "?"), 0) + 1
    # not final yet (preview / placeholder sources) = not rendered yet -> "incomplete"; anything inconsistent
    # (a tile folder short of frames, no or wrong-size centre still, an unknown source) -> FAIL
    known = {"final", "preview", "placeholder"}
    unknown = {k: v for k, v in nonfinal.items() if v not in known}
    structural = (not tiles) or incomplete or unknown or csize is None or \
        (centre.get("res") and csize is not None and list(csize) != list(centre["res"])) or \
        centre.get("source") not in known
    if structural:
        status = "FAIL"
    elif nonfinal or centre.get("source") != "final":
        status = "incomplete"
    else:
        status = "PASS" if centre_ok else "FAIL"
    return {"status": status, "version": m.get("version"), "tiles": len(tiles), "kinds": kinds,
            "frames": n_frames, "not_final": nonfinal, "incomplete": incomplete,
            "center": {"source": centre.get("source"), "path": rel(cpath), "size": list(csize) if csize else None,
                       "expected": centre.get("res")}}


# ---- v2 driver -----------------------------------------------------------------------------------------------
def v2_table():
    with open(V2_TABLE) as fh:
        return {s["id"]: s for s in json.load(fh)}


def shot_checks(sid, n, mode, jobs):
    with ProcessPoolExecutor(jobs) as ex:
        stats = list(ex.map(frame_stats_v2, [(sid, f, mode) for f in range(1, n + 1)]))
    missing = [s["frame"] for s in stats if not s["ok"]]
    ok = [s for s in stats if s["ok"]]
    want = [1080, 1920] if mode == "final" else [540, 960]
    bad_shape = [s["frame"] for s in ok if s["shape"] != want]
    nonfinite = [s["frame"] for s in ok if not s["finite"]]
    lum = np.array([s["luma"] for s in ok])
    jumps = []
    for i in range(1, len(ok) - 1):
        l0, l1, l2 = lum[i - 1], lum[i], lum[i + 1]
        if abs(l1 - l0) > 0.06 and abs(l1 - l2) > 0.06 and np.sign(l1 - l0) == np.sign(l1 - l2):
            jumps.append(ok[i]["frame"])
    pv = [s for s in ok if "pv_block_max" in s]
    flagged = sorted([s for s in pv if s["pv_block_max"] > FLAG_BLOCK], key=lambda s: -s["pv_block_max"])
    if not ok:
        status = "missing"
    elif bad_shape or nonfinite:
        status = "FAIL"
    elif missing:
        status = "incomplete"
    elif jumps or flagged:
        status = "REVIEW"
    else:
        status = "PASS"
    return {"status": status, "frames": n, "present": len(ok), "missing": ranges(missing),
            "bad_shape": bad_shape, "nonfinite": nonfinite, "single_frame_luma_spikes": jumps,
            "final_vs_preview": None if mode != "final" else {
                "compared": len(pv),
                "mean_of_mean_diff": round(float(np.mean([s["pv_mean"] for s in pv])), 4) if pv else None,
                "median_block_max": round(float(np.median([s["pv_block_max"] for s in pv])), 4) if pv else None,
                "flagged_frames": [[s["frame"], round(s["pv_block_max"], 3), s["pv_block_xy"]] for s in flagged]}
            }, flagged


def run_v1_preset(sid, mode):
    name, extra = V1_PRESETS[sid]
    heat = os.path.join(V2_QA_DIR, f"{name}_{mode}.png")
    r = subprocess.run([PY, "-I", os.path.join(ROOT, "scripts", "qa_diff.py"), "check", name, "--mode", mode,
                        "--heatmap", heat] + extra, cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-4:]
    status = {0: "PASS", 1: "FAIL", 2: "missing"}.get(r.returncode, "FAIL")
    if r.returncode == 0 and name == "s02-strip":
        status = "INFO"                     # no threshold: the heat-map is for review (as in v1)
    return {"status": status, "preset": name, "exit": r.returncode, "tail": tail, "heatmap": rel(heat)}


def main_v2(a):
    mode = a.mode
    T = v2_table()
    order = sorted(T.values(), key=lambda s: int(s["start_frame_in_film"]))
    want = [s["id"] for s in order] if a.shots is None else [x for x in a.shots.split(",") if x in T]
    os.makedirs(V2_QA_DIR, exist_ok=True)
    report = {"film": "v2", "mode": mode, "table": rel(V2_TABLE), "shots": {}, "presets": {}}
    worst = []
    for sid in want:
        s = T[sid]
        r, flagged = shot_checks(sid, int(s["frames"]), mode, a.jobs)
        r["source"] = s.get("source", "?")
        report["shots"][sid] = r
        worst += [(sid, x) for x in flagged[:6]]
        fvp = r["final_vs_preview"] or {}
        print(f"[qa v2] {sid:17s} {r['status']:10s} {r['present']}/{r['frames']} frames"
              f"{'  missing ' + r['missing'] if r['missing'] and r['present'] else ''}"
              f"{'  luma spikes ' + str(r['single_frame_luma_spikes']) if r['single_frame_luma_spikes'] else ''}"
              f"{'  final-vs-preview flagged ' + str(len(fvp.get('flagged_frames', []))) if fvp else ''}", flush=True)

    P = report["presets"]
    for sid in [x for x in V1_PRESETS if x in want]:
        if report["shots"][sid]["status"] in ("missing", "incomplete"):
            P[V1_PRESETS[sid][0]] = {"status": "missing", "note": f"{sid} not complete in renders/{mode}/"}
        else:
            P[V1_PRESETS[sid][0]] = run_v1_preset(sid, mode)

    s04 = T.get("s04_subject", {})
    fin = T.get("s05_finale", {})
    w04, w05 = "s04_subject" in want, "s05_finale" in want         # the v2 presets follow --shots
    if w04:
        h0, h1 = s04.get("static_hold", [150, 180])
        hold_frames = list(range(h0, h1 + 1))
        P["s04-subject-hold"] = check_hold([fpath(mode, "s04_subject", f) for f in hold_frames], hold_frames,
                                           a.jobs)
        osc = s04.get("overscan", {})
        P["s04-overscan"] = check_overscan(
            os.path.join(ROOT, "renders", mode, "s04_subject", "overscan.png"),
            fpath(mode, "s04_subject", int(osc.get("frame", 180))),
            os.path.join(V2_QA_DIR, f"s04-overscan_{mode}.png"), osc.get("res_final" if mode == "final" else
                                                                          "res_preview"))
    if w04 or w05:
        P["seam"] = check_pair_blur(fpath(mode, "s04_subject", int(s04.get("frames", 180))),
                                    fpath(mode, "s05_finale", 1), os.path.join(V2_QA_DIR, f"seam_{mode}.png"),
                                    SEAM_MEAN, SEAM_P99, "seam s04_subject f180 vs s05_finale f1")
    if w05:
        tl = fin.get("title_same_as", {"shot": "s05_title", "v1_frames": [61, 120], "v2_frames": [121, 180]})
        v1f = range(tl["v1_frames"][0], tl["v1_frames"][1] + 1)
        v2f = range(tl["v2_frames"][0], tl["v2_frames"][1] + 1)
        P["title-unchanged"] = check_title([(fpath(mode, "s05_finale", f2), fpath(mode, tl["shot"], f1))
                                            for f2, f1 in zip(v2f, v1f)], a.jobs)
        P["tiles-final"] = check_tiles(os.path.join(HEX_DIR, "manifest.json"), HEX_DIR)
    for name, r in P.items():
        nums = {k: r[k] for k in ("mean", "p99", "max_mean", "bit_identical_pairs", "max_mean_below_y",
                                  "letter_box_max_dev_px", "tiles", "not_final") if k in r}
        why = r.get("error") or r.get("note") or (", ".join(map(str, r.get("missing", [])))[:120]
                                                  if r["status"] == "missing" else "")
        print(f"[qa v2] preset {name:17s} {r['status']:8s} {json.dumps(nums) if nums else ''} {why}".rstrip(),
              flush=True)

    statuses = [r["status"] for r in report["shots"].values()] + [r["status"] for r in P.values()]
    report["summary"] = {k: statuses.count(k) for k in ("PASS", "FAIL", "REVIEW", "INFO", "incomplete", "missing")
                         if statuses.count(k)}
    os.makedirs(V2_LOGDIR, exist_ok=True)
    out = os.path.join(V2_LOGDIR, "qa_report.json" if mode == "final" else f"qa_report_{mode}.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1)
    if worst:
        tiles = []
        for sid, s in worst[:12]:
            fr, (x, y) = s["frame"], s["pv_block_xy"]
            fa = load_v2(fpath("final", sid, fr))
            fb = load_v2(fpath("preview", sid, fr), (1920, 1080))
            x0, y0 = max(0, min(1920 - 240, x - 96)), max(0, min(1080 - 240, y - 96))
            crop = (np.clip(np.concatenate([fa[y0:y0 + 240, x0:x0 + 240], fb[y0:y0 + 240, x0:x0 + 240]], 1), 0, 1)
                    * 255).astype(np.uint8)
            for col, wd in (((0, 0, 0), 2), ((255, 255, 255), 1)):
                cv2.putText(crop, f"{sid[:3]} f{fr} {s['pv_block_max']:.2f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX,
                            0.45, col, wd)
            tiles.append(crop)
        rows = [np.concatenate(tiles[i:i + 3] + [np.zeros_like(tiles[0])] * (3 - len(tiles[i:i + 3])), 1)
                for i in range(0, len(tiles), 3)]
        cv2.imwrite(os.path.join(V2_QA_DIR, "finals_outliers.png"), np.concatenate(rows, 0))
        print(f"[qa v2] worst blocks (final | preview): {rel(os.path.join(V2_QA_DIR, 'finals_outliers.png'))}")
    print(f"[qa v2] summary {report['summary']}  report: {rel(out)}")
    bad = report["summary"].get("FAIL", 0) + (report["summary"].get("missing", 0) +
                                              report["summary"].get("incomplete", 0) if a.require_complete else 0)
    return 1 if bad else 0


def selftest_v2(a):
    """Feed the v2 checks inputs with known answers (v1 frames and synthetic files). Writes only to --selftest-dir."""
    import tempfile
    d = a.selftest_dir or tempfile.mkdtemp(prefix="qa_v2_selftest_")
    os.makedirs(d, exist_ok=True)
    res, errs = {}, []

    def expect(name, r, want):
        res[name] = r
        got = r["status"]
        print(f"[qa v2 selftest] {name:38s} {got:8s} (want {want}) "
              + json.dumps({k: r[k] for k in r if k in ("mean", "p99", "max_mean", "bit_identical_pairs",
                                                         "max_mean_below_y", "letter_box_max_dev_px",
                                                         "not_final", "incomplete")}))
        if got != want:
            errs.append(name)

    def save16(path, im):
        cv2.imwrite(path, np.clip(im * 65535.0 + 0.5, 0, 65535).astype(np.uint16))
        return path

    t90 = fpath("final", "s05_title", 90)
    if not os.path.exists(t90):
        print("[qa v2 selftest] needs the v1 finals (renders/final/s05_title, s04_every_dot)")
        return 2
    expect("seam: identical frames", check_pair_blur(t90, t90, os.path.join(d, "seam_same.png"), 1, 4, "same"),
           "PASS")
    expect("seam: v1 S04 f180 vs v1 S05 f1 (no match)",
           check_pair_blur(fpath("final", "s04_every_dot", 180), fpath("final", "s05_title", 1),
                           os.path.join(d, "seam_v1.png"), 1, 4, "v1"), "FAIL")
    expect("seam: missing frame", check_pair_blur(os.path.join(d, "nope.png"), t90, os.path.join(d, "x.png"), 1, 4,
                                                  "missing"), "missing")
    f180 = load_v2(fpath("final", "s04_every_dot", 180))
    pad = cv2.copyMakeBorder(f180, 562, 562, 312, 312, cv2.BORDER_REFLECT)
    expect("overscan: exact padded frame 2544x2204",
           check_overscan(save16(os.path.join(d, "os_ok.png"), pad), fpath("final", "s04_every_dot", 180),
                          os.path.join(d, "os_ok_heat.png"), [2544, 2204]), "PASS")
    expect("overscan: content off by 4 px",
           check_overscan(save16(os.path.join(d, "os_bad.png"), np.roll(pad, 4, axis=1)),
                          fpath("final", "s04_every_dot", 180), os.path.join(d, "os_bad_heat.png"), [2544, 2204]),
           "FAIL")
    same = [save16(os.path.join(d, f"hold_{k}.png"), f180) for k in range(4)]
    expect("hold: 4 identical frames", check_hold(same, list(range(4)), a.jobs), "PASS")
    expect("hold: v1 S03 f31-40 (gummy moves)",
           check_hold([fpath("final", "s03_gummy", f) for f in range(31, 41)], list(range(31, 41)), a.jobs), "FAIL")
    pairs = [(fpath("final", "s05_title", f), fpath("final", "s05_title", f)) for f in range(61, 121)]
    expect("title: v1 f61-120 vs itself", check_title(pairs, a.jobs), "PASS")
    sh = []
    for f in (61, 90, 120):
        im = load_v2(fpath("final", "s05_title", f))
        sh.append((save16(os.path.join(d, f"title_shift3_{f}.png"), np.roll(im, 3, axis=1)),
                   fpath("final", "s05_title", f)))
    expect("title: word moved 3 px", check_title(sh, a.jobs), "FAIL")
    sh = []
    for f in (61, 90):
        im = load_v2(fpath("final", "s05_title", f)).copy()
        im[:400] = im[:400] * 0.5 + 0.5                       # a new wall above y 400 only
        sh.append((save16(os.path.join(d, f"title_wall_{f}.png"), im), fpath("final", "s05_title", f)))
    expect("title: changed only above y 400", check_title(sh, a.jobs), "PASS")
    hx = os.path.join(d, "hex")
    for tid in ("c_a", "t_b"):
        os.makedirs(os.path.join(hx, tid), exist_ok=True)
        for k in (1, 2, 3):
            open(os.path.join(hx, tid, f"h_{k:04d}.png"), "wb").close()
    os.makedirs(os.path.join(hx, "c_painting"), exist_ok=True)
    cv2.imwrite(os.path.join(hx, "c_painting", "still.png"), np.zeros((2204, 2544, 3), np.uint8))
    man = {"version": 2, "res": [1152, 998], "frames": 3,
           "tiles": [{"id": "c_a", "kind": "chapter", "source": "final"}, {"id": "t_b", "kind": "mini",
                                                                             "source": "final"}],
           "center": {"id": "c_painting", "path": os.path.join(hx, "c_painting", "still.png"), "res": [2544, 2204],
                      "source": "final"}}
    for name, mm, want in (("tiles: all final", man, "PASS"),
                           ("tiles: one preview tile", dict(man, tiles=[man["tiles"][0], dict(man["tiles"][1],
                                                                                               source="preview")]),
                            "incomplete"),
                           ("tiles: frame missing", dict(man, frames=4), "FAIL"),
                           ("tiles: centre still wrong size", dict(man, center=dict(man["center"], res=[2544, 2200])),
                            "FAIL")):
        with open(os.path.join(hx, "manifest.json"), "w") as fh:
            json.dump(mm, fh)
        expect(name, check_tiles(os.path.join(hx, "manifest.json"), hx), want)
    expect("tiles: no manifest", check_tiles(os.path.join(hx, "none.json"), hx), "missing")
    with open(os.path.join(d, "selftest.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"[qa v2 selftest] {'OK' if not errs else 'FAILED: ' + ', '.join(errs)} ({len(res)} cases; files in {d})")
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=None, help="v1 default: all five v1 shots; v2 default: every v2 shot")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--film", choices=["v1", "v2"], default="v1")
    ap.add_argument("--mode", choices=["final", "preview"], default="final", help="v2 only (v1 checks finals)")
    ap.add_argument("--require-complete", action="store_true", help="v2: missing frames/inputs count as failures")
    ap.add_argument("--selftest", action="store_true", help="v2: run the v2 checks on inputs with known answers")
    ap.add_argument("--selftest-dir", default=None)
    a = ap.parse_args()
    if a.film == "v1":
        a.shots = a.shots or ",".join(SHOTS)
        return main_v1(a)
    if a.selftest:
        return selftest_v2(a)
    return main_v2(a)


if __name__ == "__main__":
    sys.exit(main())
