#!/usr/bin/env python3
"""assemble.py: cut, caption and encode the LaRenderer opening (storyboard 5.2 and 5.5).

  tools/venv/bin/python -I scripts/assemble.py --mode final --master            # the deliverable
  tools/venv/bin/python -I scripts/assemble.py --mode preview --allow-missing   # review build from previews

Steps
 1. docs/shots.json -> film frame f = shot start + local - 1. Sources: renders/<mode>/<id>/f_####.png.
    Every film frame must exist; otherwise the run fails and lists the missing frames, unless --allow-missing,
    which fills each gap with a labelled placeholder in the shot's ground colour (and says so).
    renders/film/f_0001..0900.png: relative symlinks to the sources (placeholders are written as files).
 2. Overlays: runs scripts/make_overlays.py (about 10 s; --slug passes through; --skip-overlays reuses
    renders/overlays/). Composite in Python at 16 bit: frame (8- or 16-bit; preview 960x540 frames are
    Lanczos-upscaled to 1920x1080 first) blended with the 8-bit straight-alpha overlay promoted to 16 bit.
    Writes renders/film_comp/ (captioned) and renders/film_comp_clean/ (no overlays), 16-bit RGB PNG.
    Final-mode frames that are already 1920x1080 16-bit RGB are symlinked rather than rewritten.
 3. Encodes with tools/ffmpeg/ffmpeg (BT.709 matrix, tagged bt709/tv range):
      review  H.264 yuv420p CRF 16, preset slow, error-diffusion dither (as scripts/make_mp4.sh)
              out/LaRenderer_opening.mp4, out/LaRenderer_opening_clean.mp4
      master  (--master) ProRes 422 HQ, yuv422p10le
              out/LaRenderer_opening_master.mov, out/LaRenderer_opening_clean_master.mov
    Preview mode writes the same names under out/preview/.
 4. Cut-pair sheet: out/cuts.png (or out/preview/cuts.png) from film frames 240|241, 420|421, 600|601, 780|781.
 5. QA (storyboard 7, film): 900 frames, cuts on bar lines, no overlay pixel on the 2 frames before a cut;
    a manifest goes to out/[preview/]assembly.json.

Note: scripts/make_mp4.sh converts RGB->YUV with swscale's default BT.601 matrix and does not tag the stream,
so players that assume BT.709 for HD shift hues slightly. The encodes here set out_color_matrix=bt709 and
tag the stream. The intermediates in renders/film*/ are rewritten on every run; out/ keeps final and preview
apart.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FFMPEG = os.path.join(ROOT, "tools", "ffmpeg", "ffmpeg")
FFPROBE = os.path.join(ROOT, "tools", "ffmpeg", "ffprobe")
PY = os.path.join(ROOT, "tools", "venv", "bin", "python")
FW, FH, FPS = 1920, 1080, 30
CUT_PAIRS = [(240, 241), (420, 421), (600, 601), (780, 781)]
PALETTE = {"ink": "#1C1A33", "mint": "#2ED8A3", "blush": "#FFD3E4", "lemon": "#FFD23F", "lavender": "#E5DAFF",
           "sky": "#CDE9FF", "offwhite": "#F7F5F2", "pistachio": "#CFF5DD", "cream": "#FFF6EC", "white": "#FFFFFF",
           "coral": "#FF6A5C", "butter": "#FFF0A8", "peach": "#FFDCC7", "blue": "#2E5BFF"}


def log(*a):
    print("[assemble]", *a, flush=True)


def rel(p):
    return os.path.relpath(p, ROOT)


def ranges(nums):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'"""
    out, nums = [], sorted(nums)
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}" if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(out)


def hex_rgb(c):
    h = PALETTE.get(c, c).lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_rgb("lavender")


# ------------------------------------------------------------------------------------------------------------
def film_table(mode):
    with open(os.path.join(ROOT, "docs", "shots.json")) as fh:
        shots = json.load(fh)
    table, f_expected = [], 1
    for s in sorted(shots, key=lambda s: int(s["start_frame_in_film"])):
        a, n = int(s["start_frame_in_film"]), int(s["frames"])
        if a != f_expected:
            raise SystemExit(f"[assemble] docs/shots.json: {s['id']} starts at {a}, expected {f_expected}")
        for fl in range(1, n + 1):
            table.append(dict(f=a + fl - 1, shot=s["id"], local=fl, n=n,
                              ground=(s.get("palette_ground") or ["lavender"])[0],
                              src=os.path.join(ROOT, "renders", mode, s["id"], f"f_{fl:04d}.png")))
        f_expected = a + n
    return shots, table


def read_rgb(path, tries=2):
    """float32 RGB [0,1] at the file's own size, or None (missing, truncated or being written)."""
    for k in range(tries):
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED) if os.path.exists(path) else None
        if im is not None and im.ndim in (2, 3):
            sc = 65535.0 if im.dtype == np.uint16 else 255.0
            im = im.astype(np.float32) / sc
            if im.ndim == 2:
                im = np.repeat(im[..., None], 3, -1)
            return cv2.cvtColor(np.ascontiguousarray(im[..., :3]), cv2.COLOR_BGR2RGB), sc
        if k + 1 < tries:
            time.sleep(1.5)
    return None, None


def png_ihdr(path):
    """(width, height, bit depth, colour type) from the PNG header, or None."""
    try:
        with open(path, "rb") as fh:
            h = fh.read(33)
    except OSError:
        return None
    if len(h) < 26 or h[:8] != b"\x89PNG\r\n\x1a\n" or h[12:16] != b"IHDR":
        return None
    return int.from_bytes(h[16:20], "big"), int.from_bytes(h[20:24], "big"), h[24], h[25]


def is_exact_final(path):
    """Already a 1920x1080 16-bit RGB PNG, so it can be linked instead of rewritten."""
    i = png_ihdr(path)
    return i is not None and i[:2] == (FW, FH) and i[2] == 16 and i[3] == 2


_FONT = None


def placeholder(row, mode, reason):
    global _FONT
    if _FONT is None:
        _FONT = (ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Fredoka-Bold.ttf"), 64),
                 ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Fredoka-SemiBold.ttf"), 34))
    big, small = _FONT
    bg = hex_rgb(row["ground"])
    lum = 0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2]
    ink = (255, 255, 255) if lum < 110 else hex_rgb("ink")
    im = Image.new("RGB", (FW, FH), bg)
    d = ImageDraw.Draw(im)
    for x in range(-FH, FW, 90):                                   # faint diagonal hatching = "not a render"
        d.line([(x, FH), (x + FH, 0)], fill=tuple(int(c * 0.93 + i * 0.07) for c, i in zip(bg, ink)), width=18)
    d.rounded_rectangle([40, 40, FW - 40, FH - 40], radius=36, outline=ink, width=4)
    d.text((FW // 2, FH // 2 - 40), f"{row['shot']}  ·  f {row['local']:04d} / {row['n']}", font=big, fill=ink,
           anchor="mm")
    d.text((FW // 2, FH // 2 + 40), f"film frame {row['f']}  ·  {reason} ({mode})", font=small, fill=ink,
           anchor="mm")
    return np.asarray(im, np.float32) / 255.0


def write16(path, rgb):
    tmp = path + ".tmp.png"
    q = np.clip(np.floor(rgb * 65535.0 + 0.5), 0, 65535).astype(np.uint16)
    cv2.imwrite(tmp, cv2.cvtColor(q, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    os.replace(tmp, path)


def relink(link, target):
    if os.path.lexists(link):
        os.remove(link)
    os.symlink(os.path.relpath(target, os.path.dirname(link)), link)


# ------------------------------------------------------------------------------------------------------------
def composite_one(job):
    row, mode, dirs, missing_ok = job
    f = row["f"]
    name = f"f_{f:04d}.png"
    film, comp, clean = (os.path.join(d, name) for d in dirs)
    status = "ok"
    bg, scale = read_rgb(row["src"]) if row["have"] else (None, None)
    if bg is None:
        if not missing_ok:
            return f, "unreadable", 0
        bg = placeholder(row, mode, "unreadable" if row["have"] else "not rendered")
        status = "placeholder"
        write16(film, bg)
    else:
        relink(film, row["src"])
        if bg.shape[:2] != (FH, FW):
            bg = cv2.resize(bg, (FW, FH), interpolation=cv2.INTER_LANCZOS4)
            np.clip(bg, 0.0, 1.0, out=bg)
            status = "upscaled"
    ov = cv2.imread(row["overlay"], cv2.IMREAD_UNCHANGED)
    if ov is None or ov.shape[:2] != (FH, FW) or ov.ndim != 3 or ov.shape[2] != 4:
        return f, "bad overlay", 0
    exact = status == "ok" and scale == 65535.0 and is_exact_final(row["src"])
    if exact:
        relink(clean, row["src"])
    else:
        write16(clean, bg)
    amax = int(ov[..., 3].max())
    if amax == 0:
        relink(comp, os.path.realpath(clean))
    else:
        ov = ov.astype(np.float32)
        a = ov[..., 3:4] / 255.0
        fg = cv2.cvtColor(ov[..., :3], cv2.COLOR_BGR2RGB) * (257.0 / 65535.0)   # 8-bit promoted to 16-bit
        write16(comp, bg * (1.0 - a) + fg * a)
    return f, status, amax


def run(cmd, label):
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout[-3000:] + p.stderr[-3000:])
        raise SystemExit(f"[assemble] {label} failed (exit {p.returncode})")
    log(f"{label}: {time.time() - t:.1f}s")
    return p


def h264_cmd(src_dir, out):
    return [FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", "1",
            "-i", os.path.join(src_dir, "f_%04d.png"),
            "-vf", "scale=1920:1080:flags=lanczos:sws_dither=ed:out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-movflags", "+faststart", out]


def prores_cmd(src_dir, out):
    return [FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", "1",
            "-i", os.path.join(src_dir, "f_%04d.png"),
            "-vf", "scale=1920:1080:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv422p10le",
            "-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", "-pix_fmt", "yuv422p10le",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", out]


def probe(path):
    p = subprocess.run([FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames,color_space,"
                        "color_primaries,color_transfer,color_range", "-of", "json", path],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout)["streams"][0]
    except (ValueError, KeyError, IndexError):
        return {}


def main():
    ap = argparse.ArgumentParser(description="Cut, caption and encode the LaRenderer opening.")
    ap.add_argument("--mode", choices=["final", "preview"], default="final")
    ap.add_argument("--allow-missing", action="store_true", help="fill missing frames with labelled placeholders")
    ap.add_argument("--master", action="store_true", help="also write ProRes 422 HQ 10-bit masters")
    ap.add_argument("--slug", action="store_true", help='overlays carry "Illustrative · rendered with Cycles"')
    ap.add_argument("--skip-overlays", action="store_true", help="reuse renders/overlays as they are")
    ap.add_argument("--no-encode", action="store_true", help="stop after the 16-bit composites")
    ap.add_argument("--jobs", type=int, default=min(24, os.cpu_count() or 4))
    a = ap.parse_args()
    t0 = time.time()

    shots, table = film_table(a.mode)
    n_film = len(table)
    out_dir = os.path.join(ROOT, "out") if a.mode == "final" else os.path.join(ROOT, "out", "preview")
    dirs = [os.path.join(ROOT, "renders", d) for d in ("film", "film_comp", "film_comp_clean")]
    ov_dir = os.path.join(ROOT, "renders", "overlays")

    # 1) sources
    missing = {}
    for r in table:
        r["have"] = os.path.exists(r["src"])
        r["overlay"] = os.path.join(ov_dir, f"o_{r['f']:04d}.png")
        if not r["have"]:
            missing.setdefault(r["shot"], []).append(r)
    n_missing = sum(len(v) for v in missing.values())
    if missing:
        lines = [f"  {sid}: local {ranges([r['local'] for r in rows])}  (film {ranges([r['f'] for r in rows])})"
                 for sid, rows in missing.items()]
        msg = f"{n_missing} of {n_film} film frames missing in renders/{a.mode}/:\n" + "\n".join(lines)
        if not a.allow_missing:
            sys.stderr.write("[assemble] FAIL: " + msg + "\n[assemble] render them, or pass --allow-missing for a "
                             "placeholder build\n")
            sys.exit(1)
        log("WARNING " + msg + "\n[assemble] -> labelled placeholders (--allow-missing)")
    else:
        log(f"all {n_film} source frames present in renders/{a.mode}/")

    # 2) overlays
    if not a.skip_overlays:
        cmd = [PY, "-I", os.path.join(ROOT, "scripts", "make_overlays.py"), "--jobs", str(a.jobs)]
        if a.slug:
            cmd.append("--slug")
        p = run(cmd, "overlays (scripts/make_overlays.py)")
        for line in p.stdout.splitlines():
            if "values" in line or "meta" in line or "selftest" in line:
                log("  " + line.replace("[overlays] ", ""))
    bad_ov = [r["f"] for r in table if not os.path.exists(r["overlay"])]
    if bad_ov:
        raise SystemExit(f"[assemble] overlay frames missing: {ranges(bad_ov)}")

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            if fn.startswith("f_") and fn.endswith(".png"):
                os.remove(os.path.join(d, fn))

    jobs = [(r, a.mode, dirs, a.allow_missing) for r in table]
    stats, alpha = {}, {}
    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.jobs) as pool:
        for f, status, amax in pool.imap_unordered(composite_one, jobs, chunksize=4):
            stats.setdefault(status, []).append(f)
            alpha[f] = amax
    if "unreadable" in stats or "bad overlay" in stats:
        bad = stats.get("unreadable", []) + stats.get("bad overlay", [])
        raise SystemExit(f"[assemble] FAIL: unreadable source or overlay frames: {ranges(bad)} (a render may still "
                         "be writing; rerun, or pass --allow-missing)")
    log("composites: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(stats.items())) +
        f"  -> {rel(dirs[1])}/, {rel(dirs[2])}/  ({time.time() - t0:.0f}s)")
    placeholders = sorted(stats.get("placeholder", []))

    # 5) QA
    qa = {"frames": n_film == 900 and len(alpha) == 900,
          "cuts_on_bar_lines": all((int(s["start_frame_in_film"]) - 1) % 60 == 0 for s in shots),
          "overlay_clear_before_cuts": all(alpha.get(f, 0) == 0 for c, _ in CUT_PAIRS for f in (c - 1, c))}
    log("QA film: " + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in qa.items()))

    # 3) encodes + 4) cut sheet
    os.makedirs(out_dir, exist_ok=True)
    outputs = {}
    sheet = os.path.join(out_dir, "cuts.png")
    cut_frames = [os.path.join(dirs[1], f"f_{f:04d}.png") for pair in CUT_PAIRS for f in pair]
    run([PY, "-I", os.path.join(ROOT, "scripts", "contact_sheet.py"), sheet, "--cols", "2", "--width", "800"]
        + cut_frames, "cut-pair sheet")
    outputs["cuts"] = sheet
    if not a.no_encode:
        encs = [("captioned H.264", h264_cmd(dirs[1], os.path.join(out_dir, "LaRenderer_opening.mp4"))),
                ("clean H.264", h264_cmd(dirs[2], os.path.join(out_dir, "LaRenderer_opening_clean.mp4")))]
        if a.master:
            encs += [("captioned ProRes", prores_cmd(dirs[1], os.path.join(out_dir, "LaRenderer_opening_master.mov"))),
                     ("clean ProRes", prores_cmd(dirs[2], os.path.join(out_dir, "LaRenderer_opening_clean_master.mov")))]
        t = time.time()
        procs = [(label, cmd, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
                 for label, cmd in encs]
        for label, cmd, p in procs:
            so, se = p.communicate()
            if p.returncode != 0:
                sys.stderr.write(se[-3000:])
                raise SystemExit(f"[assemble] {label} encode failed")
            info = probe(cmd[-1])
            outputs[label] = {"path": cmd[-1], "probe": info}
            ok = int(info.get("nb_read_frames", 0)) == n_film
            log(f"{label}: {rel(cmd[-1])}  {info.get('codec_name')} {info.get('pix_fmt')} "
                f"{info.get('width')}x{info.get('height')} {info.get('r_frame_rate')} "
                f"{info.get('nb_read_frames')} frames {'OK' if ok else 'FRAME COUNT MISMATCH'} "
                f"[{info.get('color_space')}/{info.get('color_primaries')}/{info.get('color_transfer')}/"
                f"{info.get('color_range')}]")
            qa[f"{label} frame count"] = ok
        log(f"encodes: {time.time() - t:.0f}s")
    manifest = {"mode": a.mode, "created": time.strftime("%Y-%m-%d %H:%M:%S"), "frames": n_film,
                "placeholders": ranges(placeholders) if placeholders else "", "n_placeholders": len(placeholders),
                "upscaled_from_preview": len(stats.get("upscaled", [])), "slug": a.slug, "qa": qa,
                "outputs": outputs, "sources": {r["shot"]: f"renders/{a.mode}/{r['shot']}/" for r in table}}
    with open(os.path.join(out_dir, "assembly.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    log(f"done in {time.time() - t0:.0f}s; manifest {rel(os.path.join(out_dir, 'assembly.json'))}"
        + (f"; {len(placeholders)} placeholder frames" if placeholders else ""))
    if not all(qa.values()):
        sys.exit(3)


if __name__ == "__main__":
    main()
