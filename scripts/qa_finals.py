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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=",".join(SHOTS))
    ap.add_argument("--jobs", type=int, default=16)
    a = ap.parse_args()
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


if __name__ == "__main__":
    sys.exit(main())
