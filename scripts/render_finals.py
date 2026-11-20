"""Final-render queue for the LaRenderer opening. Uses ONLY GPU 6 and GPU 7 (project rule).

    python3 scripts/render_finals.py                    # all shots, missing frames only
    python3 scripts/render_finals.py --shots s02_caustics --frames 61-72
    python3 scripts/render_finals.py --dry-run          # print the job plan

* One worker thread per GPU pulls (shot, frame-chunk) jobs from a shared queue, so both GPUs stay busy.
  Each job is one Blender process (`--mode final --frames a,b,c`), sized at roughly 6-10 min of work.
* Skip-existing: a frame counts as done only if its PNG exists and ends with an IEND chunk
  (a killed process can leave a truncated file). Re-running the script resumes where it stopped.
* s05_title depends on the other shots (its tiles play them): its jobs start only after every S01-S04
  frame exists, and scripts/make_tile_proxies.py is re-run first.
* Logs: logs/finals/<shot>_<job>_gpu<N>.log. Summary with per-frame times: logs/finals/summary.json.

Film v2 (docs/storyboard_v2.md section 6): --film v2 (default v1: everything above, unchanged)
    python3 scripts/render_finals.py --film v2 --dry-run          # print the staged plan; writes nothing
    python3 scripts/render_finals.py --film v2                    # every v2 job, missing frames only (resumable)
    python3 scripts/render_finals.py --film v2 --shots t_disco,s04_subject,s04_overscan
  Table docs/shots_v2.json. S01-S03 are the v1 finals, reused: no jobs (their completeness is reported).
  Stage A, one queue on both GPUs, longest jobs first:
    * the twelve tile scenes (s05_finale "tile_scenes"): shots/t_<name>.py -> renders/<mode>/t_<name>/f_####.png,
      frames 1..loop from renders/meta/t_<name>.json ("loop": 60/90/180), 180 when not looped. A scene whose meta
      does not exist yet gets a `--no-render` build first (every shot writes its meta at build time); if there is
      still no meta it is skipped and reported (make_hex_tiles then has no final for it).
    * s04_subject f1-180 (chunks of 60) and the overscan still: one job, frame 180 with `--overscan` (the switch
      read from shots/s04_subject.py) -> renders/<mode>/s04_subject/overscan.png (2544x2204 final, 1272x1102
      preview). The job fails if that file is missing or the wrong size, or if f_0180.png changed under it.
  Stage B: tools/venv/bin/python -I scripts/make_hex_tiles.py --require-final (preview mode: without the flag).
    A non-zero exit blocks stage C (log logs/finals_v2/hex_tiles.log).
  Stage C: s05_finale f1-180 (chunks of 45, at least one job per GPU).
  --shots takes tile names, "tiles", s04_subject, s04_overscan, hex_tiles, s05_finale. GPUs 6,7 only (same guard).
  Logs and summary: logs/finals_v2/.
"""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ALLOWED = {g.strip() for g in os.environ.get("DOPA_ALLOWED_GPUS", "6,7").split(",") if g.strip()}  # outside Slurm (lib/dopa.py)
ORDER = ["s02_caustics", "s01_lights_world", "s03_gummy", "s04_every_dot", "s05_title"]
CHUNK = {"s02_caustics": 16, "s01_lights_world": 40, "s03_gummy": 24, "s04_every_dot": 45, "s05_title": 60}
LOGDIR = os.path.join(ROOT, "logs", "finals")


def shots_table():
    with open(os.path.join(ROOT, "docs", "shots.json")) as f:
        return {s["id"]: s for s in json.load(f)}


def frame_ok(path):
    try:
        if os.path.getsize(path) < 1000:
            return False
        with open(path, "rb") as f:
            f.seek(-12, os.SEEK_END)
            return b"IEND" in f.read()
    except OSError:
        return False


def missing_frames(sid, n, mode, subset=None):
    d = os.path.join(ROOT, "renders", mode, sid)
    frames = subset or range(1, n + 1)
    return [f for f in frames if not frame_ok(os.path.join(d, f"f_{f:04d}.png"))]


def parse_range(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def make_jobs(sid, frames, gpus):
    """Interleave frames so every job samples the whole shot (cost evens out), then chunk."""
    size = CHUNK.get(sid, 40)
    n_jobs = max(len(gpus), -(-len(frames) // size))
    return [(sid, frames[i::n_jobs]) for i in range(n_jobs) if frames[i::n_jobs]]


# =================================================================================================================
# film v2 (docs/storyboard_v2.md section 6)
V2_TABLE = os.path.join(ROOT, "docs", "shots_v2.json")
V2_LOGDIR = os.path.join(ROOT, "logs", "finals_v2")
PY = os.path.join(ROOT, "tools", "venv", "bin", "python")
CHUNK_V2 = {"tile": 90, "s04_subject": 60, "s05_finale": 45}   # frames per Blender process (~4-10 min each)
TILE_CAP_GPU_H = 0.12          # storyboard_v2 section 5: per tile scene, final
JOB_OVERHEAD_S = 30            # Blender start + scene build per process (20K texture upload for S04: +40 s)


def frame_spec(frames):
    """dopa --frames syntax: 'a-b:step' for an arithmetic run (interleaved chunks), else a comma list."""
    if len(frames) == 1:
        return str(frames[0])
    step = frames[1] - frames[0]
    if step > 0 and all(b - a == step for a, b in zip(frames, frames[1:])):
        return f"{frames[0]}-{frames[-1]}" + (f":{step}" if step > 1 else "")
    return ",".join(map(str, frames))


def stat_sig(path):
    try:
        st = os.stat(path)
        return st.st_size, st.st_mtime_ns
    except OSError:
        return None


def png_wh(path):
    try:
        with open(path, "rb") as f:
            h = f.read(24)
    except OSError:
        return None
    if len(h) < 24 or h[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(h[16:20], "big"), int.from_bytes(h[20:24], "big")


def ranges(nums):
    out, nums = [], sorted(nums)
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}" if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(out) if out else "none"


def read_meta(name):
    try:
        with open(os.path.join(ROOT, "renders", "meta", f"{name}.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def tile_frames(meta):
    """Frames to render for a tile scene: its loop length if looped, else 180 (storyboard_v2 section 5)."""
    loop = meta.get("loop")
    if isinstance(loop, dict):
        loop = loop.get("frames") or loop.get("length") or loop.get("period")
    if loop is True:
        loop = meta.get("frames")
    if isinstance(loop, (int, float)) and not isinstance(loop, bool) and loop > 0:
        return int(loop), f"loop {int(loop)}"
    return 180, "not looped: 180"


def measured_spf(obj):
    """A measured final s/frame anywhere in a meta dict (keys differ per builder), or None."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 and \
                    re.search(r"s_per_f|spf|sec_per_frame", k, re.I):
                return float(v)
        for v in obj.values():
            r = measured_spf(v)
            if r:
                return r
    return None


def overscan_args():
    """How shots/s04_subject.py renders its overscan still: (extra args or None, note)."""
    script = os.path.join(ROOT, "shots", "s04_subject.py")
    if not os.path.exists(script):
        return ["--overscan"], ("shots/s04_subject.py not written yet; expected interface `-- --mode <mode> "
                                "--frames 180 --overscan` -> renders/<mode>/s04_subject/overscan.png, f_0180 untouched")
    with open(script, errors="replace") as f:
        src = f.read()
    if "--overscan" in src:
        return ["--overscan"], "shots/s04_subject.py takes --overscan"
    return None, "shots/s04_subject.py has no --overscan switch: overscan job not scheduled"


def v2_jobs(sid, script, frames, size, min_jobs, spf, logdir, mode, expect_dir):
    n_jobs = max(min_jobs, -(-len(frames) // size)) if frames else 0
    jobs = []
    for i in range(n_jobs):
        fr = frames[i::n_jobs]
        if fr:
            jobs.append(dict(sid=sid, script=script, frames=fr, args=[], kind="frames", logdir=logdir,
                             expect=[os.path.join(expect_dir, f"f_{f:04d}.png") for f in fr],
                             est_s=JOB_OVERHEAD_S + spf * len(fr)))
    return jobs


def main_v2(a, gpus):
    with open(V2_TABLE) as f:
        T = {s["id"]: s for s in json.load(f)}
    fin, s04 = T["s05_finale"], T["s04_subject"]
    tiles = list(fin.get("tile_scenes", []))
    sel = None if a.shots is None else set(a.shots.split(","))
    if sel and "tiles" in sel:
        sel |= set(tiles)
    on = (lambda k: True) if sel is None else (lambda k: k in sel)
    subset = parse_range(a.frames) if a.frames else None
    mode, logdir = a.mode, V2_LOGDIR
    rdir = lambda sid: os.path.join(ROOT, "renders", mode, sid)
    est_total = 0.0
    print(f"[finals v2] film v2 ({os.path.relpath(V2_TABLE, ROOT)}), mode {mode}, GPUs {','.join(gpus)}"
          f"{' (DRY RUN: nothing is rendered or written)' if a.dry_run else ''}")
    stage_a, notes, probes = [], [], []
    for sid in [s for s in sorted(T, key=lambda k: T[k]["start_frame_in_film"]) if T[s].get("source") == "v1"]:
        n = int(T[sid]["frames"])
        miss = missing_frames(sid, n, mode)
        if not miss:
            print(f"[finals v2] reused {sid}: {n}/{n} frames in renders/{mode}/{sid} (v1, no jobs)")
            continue
        # A fresh checkout on another cluster (no v1 render cache): render the missing frames with the unchanged v1
        # script, in stage A. On the original box all v1 frames exist, so this never runs there.
        if sel is not None and sid not in sel and "v1shots" not in sel:
            print(f"[finals v2] reused {sid}: {n - len(miss)}/{n} frames (v1)  WARNING missing {ranges(miss)} "
                  f"(not selected by --shots; add {sid} or v1shots)")
            continue
        script = T[sid]["script"]
        spf = float(T[sid].get("est_s_per_frame", 20))
        jobs = v2_jobs(sid, script, miss, CHUNK.get(sid, 30), len(gpus), spf, logdir, mode, rdir(sid))
        est = sum(j["est_s"] for j in jobs)
        est_total += est
        print(f"[finals v2] A  {sid:18s} {len(miss):3d}/{n} frames to render with the v1 script {script} "
              f"(no v1 finals here)  {len(jobs)} job(s) ~{est / 3600:.3f} GPU-h")
        stage_a += jobs

    # ---- stage A: tile scenes, s04_subject, the overscan still -------------------------------------------------
    for name in tiles:
        if not on(name):
            continue
        script = os.path.join("shots", f"{name}.py")
        if not os.path.exists(os.path.join(ROOT, script)):
            notes.append(f"{name}: {script} not written yet -> skipped (make_hex_tiles keeps its preview/placeholder)")
            continue
        meta = read_meta(name)
        if meta is None:
            probes.append(name)
            notes.append(f"{name}: no renders/meta/{name}.json yet -> a `--no-render` build writes it first, then "
                         "its frames are planned")
            continue
        n, why = tile_frames(meta)
        frames = [f for f in (subset or range(1, n + 1)) if 1 <= f <= n]
        miss = missing_frames(name, n, mode, frames) if frames else []      # a subset outside the loop: nothing
        spf = measured_spf(meta)
        spf_est = spf if spf else TILE_CAP_GPU_H * 3600.0 / n
        jobs = v2_jobs(name, script, miss, CHUNK_V2["tile"], 1, spf_est, logdir, mode, rdir(name))
        est = sum(j["est_s"] for j in jobs)
        est_total += est
        print(f"[finals v2] A  {name:18s} {len(miss):3d}/{n} frames to render ({why}; "
              f"{f'measured {spf:g} s/f' if spf else 'no measured s/f: cap ' + str(TILE_CAP_GPU_H) + ' GPU-h'})"
              f"  {len(jobs)} job(s) ~{est / 3600:.3f} GPU-h")
        stage_a += jobs
    if on("s04_subject"):
        sid, n = "s04_subject", int(s04["frames"])
        if not os.path.exists(os.path.join(ROOT, s04["script"])):
            notes.append(f"{sid}: {s04['script']} not written yet -> skipped")
        else:
            sub = [f for f in subset if 1 <= f <= n] if subset else None
            miss = missing_frames(sid, n, mode, sub) if sub != [] else []
            spf = measured_spf(read_meta(sid) or {}) or float(s04["est_s_per_frame"])   # measured, else the table
            jobs = v2_jobs(sid, s04["script"], miss, CHUNK_V2[sid], len(gpus), spf, logdir, mode, rdir(sid))
            est = sum(j["est_s"] for j in jobs) + 40 * len(jobs)
            est_total += est
            print(f"[finals v2] A  {sid:18s} {len(miss):3d}/{n} frames to render  {len(jobs)} job(s) "
                  f"~{est / 3600:.3f} GPU-h (cap {s04.get('cost_cap_gpu_hours')})")
            stage_a += jobs
    if on("s04_overscan") or on("s04_subject"):
        osc = s04.get("overscan", {})
        out = os.path.join(rdir("s04_subject"), "overscan.png")
        size = osc.get("res_final" if mode == "final" else "res_preview")
        args, note = overscan_args()
        fr = int(osc.get("frame", 180))
        done = frame_ok(out) and (size is None or png_wh(out) == tuple(size))
        f180 = os.path.join(rdir("s04_subject"), f"f_{fr:04d}.png")
        if done and stat_sig(f180) and stat_sig(out)[1] < stat_sig(f180)[1] - 600e9:
            notes.append(f"s04_overscan: overscan.png is older than f_{fr:04d}.png; delete it to re-render if the "
                         "shot changed (the seam needs both from the same build)")
        have_script = os.path.exists(os.path.join(ROOT, s04["script"]))
        state = "done" if done else ("to render" if have_script and args is not None else "not scheduled")
        print(f"[finals v2] A  {'s04_overscan':18s} {state}: frame {fr} {' '.join(args or [])} -> "
              f"{os.path.relpath(out, ROOT)} {size}  ({note})")
        if not done and args is not None and have_script:
            stage_a.append(dict(sid="s04_subject", script=s04["script"], frames=[fr], args=args, kind="overscan",
                                logdir=logdir, expect=[out], size=size, protect=[f180],
                                est_s=JOB_OVERHEAD_S + 40 + 2.8 * float(s04["est_s_per_frame"])))
            est_total += stage_a[-1]["est_s"]
    for n_ in notes:
        print(f"[finals v2]    note: {n_}")
    stage_a.sort(key=lambda j: -j["est_s"])                      # longest first: both GPUs finish together

    # ---- stage B / C ---------------------------------------------------------------------------------------------
    hex_cmd = [PY, "-I", os.path.join(ROOT, "scripts", "make_hex_tiles.py")] + \
        (list(fin.get("hex_tiles", {}).get("args_final", ["--require-final"])) if mode == "final" else [])
    do_hex = on("hex_tiles") or on("s05_finale")
    sid, n = "s05_finale", int(fin["frames"])
    stage_c = []
    if on(sid):
        if not os.path.exists(os.path.join(ROOT, fin["script"])):
            print(f"[finals v2] C  {sid}: {fin['script']} not written yet -> skipped")
        else:
            sub = [f for f in subset if 1 <= f <= n] if subset else None
            miss = missing_frames(sid, n, mode, sub) if sub != [] else []
            spf = measured_spf(read_meta(sid) or {}) or float(fin["est_s_per_frame"])
            stage_c = v2_jobs(sid, fin["script"], miss, CHUNK_V2[sid], len(gpus), spf, logdir, mode, rdir(sid))
            est = sum(j["est_s"] for j in stage_c)
            est_total += est
    if do_hex:
        print(f"[finals v2] B  {' '.join(os.path.relpath(c, ROOT) if c.startswith(ROOT) else c for c in hex_cmd)}"
              f"  (non-zero exit blocks stage C)")
    if on(sid) and os.path.exists(os.path.join(ROOT, fin["script"])):
        print(f"[finals v2] C  {sid:18s} {len(sum((j['frames'] for j in stage_c), []))}/{n} frames to render  "
              f"{len(stage_c)} job(s) ~{sum(j['est_s'] for j in stage_c) / 3600:.3f} GPU-h "
              f"(cap {fin.get('cost_cap_gpu_hours')})")
    print(f"[finals v2] estimate ~{est_total / 3600:.2f} GPU-h for {len(stage_a) + len(stage_c)} Blender jobs "
          f"(+ {len(probes)} meta build(s)); wall ~{est_total / 60 / max(1, len(gpus)):.0f} min on {len(gpus)} GPU(s)")

    if a.dry_run:
        for st, jobs in (("A", stage_a), ("C", stage_c)):
            for j in jobs:
                cmd = ["tools/blender/blender", "-b", "--factory-startup", "-P", j["script"], "--", "--mode", mode] + \
                      (["--frames", frame_spec(j["frames"])] if j["frames"] else []) + j["args"]
                print(f"[finals v2]   {st} CUDA_VISIBLE_DEVICES=<{'|'.join(gpus)}> {' '.join(cmd)}")
        for name in probes:
            print(f"[finals v2]   A CUDA_VISIBLE_DEVICES=<{'|'.join(gpus)}> tools/blender/blender -b --factory-startup "
                  f"-P shots/{name}.py -- --mode {mode} --no-render   (meta build, then plan its frames)")
        return 0

    os.makedirs(logdir, exist_ok=True)
    r = Runner(gpus, mode, False)
    t_start = time.time()
    summary = {"film": "v2", "mode": mode, "stages": {}}
    if probes:                       # meta builds (cheap), then plan those scenes
        r.run_stage([dict(sid=nm, script=os.path.join("shots", f"{nm}.py"), frames=[], args=["--no-render"],
                          kind="meta", logdir=logdir, expect=[os.path.join(ROOT, "renders", "meta", f"{nm}.json")],
                          est_s=JOB_OVERHEAD_S) for nm in probes])
        for nm in probes:
            meta = read_meta(nm)
            if meta is None:
                print(f"[finals v2] {nm}: still no meta after the build -> skipped")
                continue
            n_, why = tile_frames(meta)
            fr_ = [f for f in (subset or range(1, n_ + 1)) if 1 <= f <= n_]
            miss = missing_frames(nm, n_, mode, fr_) if fr_ else []
            stage_a += v2_jobs(nm, os.path.join("shots", f"{nm}.py"), miss, CHUNK_V2["tile"], 1,
                               measured_spf(meta) or TILE_CAP_GPU_H * 3600.0 / n_, logdir, mode, rdir(nm))
            print(f"[finals v2] A  {nm}: {len(miss)}/{n_} frames ({why})")
        stage_a.sort(key=lambda j: -j["est_s"])
    if stage_a:
        r.run_stage(stage_a)
    summary["stages"]["A"] = {"jobs": len(stage_a), "failed": len(r.failed)}
    blocked = None
    if do_hex:
        hl = os.path.join(logdir, "hex_tiles.log")
        with open(hl, "w") as lf:
            rc = subprocess.call(hex_cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT)
        with open(hl, errors="replace") as lf:
            tail = lf.read().strip().splitlines()[-6:]
        for line in tail:
            print(f"[finals v2] hex_tiles | {line}")
        summary["stages"]["B"] = {"exit": rc, "log": os.path.relpath(hl, ROOT), "tail": tail}
        if rc != 0:
            blocked = f"make_hex_tiles exit {rc} (see {os.path.relpath(hl, ROOT)})"
    if stage_c and blocked:
        print(f"[finals v2] s05_finale BLOCKED: {blocked}; render the missing finals and rerun")
        r.failed.append({"shot": "s05_finale", "blocked": blocked})
    elif stage_c:
        r.run_stage(stage_c)
    summary["stages"]["C"] = {"jobs": 0 if blocked else len(stage_c), "blocked": blocked}
    gpu_s = sum(sum(v.values()) for v in r.times.values())
    summary.update({"wall_min": round((time.time() - t_start) / 60, 1), "gpu_hours_render": round(gpu_s / 3600, 2),
                    "per_shot_mean_s": {k: round(sum(v.values()) / len(v), 1) for k, v in r.times.items() if v},
                    "failed": r.failed})
    with open(os.path.join(logdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("[finals v2] summary", json.dumps(summary))
    return 1 if r.failed else 0


class Runner:
    def __init__(self, gpus, mode, dry):
        self.gpus, self.mode, self.dry = gpus, mode, dry
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.times = {}      # sid -> {frame: seconds}
        self.failed = []
        self.job_no = 0

    def worker(self, gpu):
        while True:
            job = self.q.get()
            if job is None:
                self.q.task_done()
                return
            if isinstance(job, dict):          # film v2 job (v1 jobs are (sid, frames) tuples, handled below)
                self.run_v2(job, gpu)
                self.q.task_done()
                continue
            sid, frames = job
            with self.lock:
                self.job_no += 1
                jn = self.job_no
            log = os.path.join(LOGDIR, f"{sid}_job{jn:03d}_gpu{gpu}.log")
            cmd = [os.path.join(ROOT, "tools", "blender", "blender"), "-b", "--factory-startup", "-P",
                   os.path.join(ROOT, "shots", f"{sid}.py"), "--", "--mode", self.mode,
                   "--frames", ",".join(map(str, frames))]
            t0 = time.time()
            print(f"[finals] {time.strftime('%H:%M:%S')} GPU{gpu} start {sid} job{jn} ({len(frames)} frames)",
                  flush=True)
            if not self.dry:
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu)
                with open(log, "w") as lf:
                    rc = subprocess.call(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
                with open(log, errors="replace") as lf:
                    for m in re.finditer(r"\[dopa\] \S+ frame (\d+) -> .*?\s([\d.]+)s", lf.read()):
                        with self.lock:
                            self.times.setdefault(sid, {})[int(m.group(1))] = float(m.group(2))
                bad = [f for f in frames if not frame_ok(os.path.join(ROOT, "renders", self.mode, sid,
                                                                      f"f_{f:04d}.png"))]
                if rc != 0 or bad:
                    with self.lock:
                        self.failed.append({"shot": sid, "rc": rc, "missing": bad, "log": log})
                    print(f"[finals] GPU{gpu} {sid} job{jn} rc={rc} missing={bad[:10]}... see {log}", flush=True)
            print(f"[finals] {time.strftime('%H:%M:%S')} GPU{gpu} done  {sid} job{jn} "
                  f"in {(time.time() - t0) / 60:.1f} min", flush=True)
            self.q.task_done()

    def run_v2(self, job, gpu):
        """One Blender process for a v2 job dict: sid, script, frames, args, kind, expect, size, protect, logdir."""
        with self.lock:
            self.job_no += 1
            jn = self.job_no
        tag = job["sid"] + ("" if job["kind"] == "frames" else "_" + job["kind"])
        log = os.path.join(job["logdir"], f"{tag}_job{jn:03d}_gpu{gpu}.log")
        cmd = [os.path.join(ROOT, "tools", "blender", "blender"), "-b", "--factory-startup", "-P",
               os.path.join(ROOT, job["script"]), "--", "--mode", self.mode] + \
              (["--frames", frame_spec(job["frames"])] if job["frames"] else []) + job["args"]
        t0 = time.time()
        what = f"{len(job['frames'])} frames" if job["kind"] == "frames" else job["kind"]
        print(f"[finals v2] {time.strftime('%H:%M:%S')} GPU{gpu} start {tag} job{jn} ({what})", flush=True)
        if self.dry:
            print(f"[finals v2]     CUDA_VISIBLE_DEVICES={gpu} " + " ".join(os.path.relpath(c, ROOT)
                                                                        if c.startswith(ROOT) else c for c in cmd))
        else:
            before = {p: stat_sig(p) for p in job.get("protect", [])}
            env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu)
            os.makedirs(job["logdir"], exist_ok=True)
            with open(log, "w") as lf:
                rc = subprocess.call(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
            with open(log, errors="replace") as lf:
                for m in re.finditer(r"\[dopa\] \S+ frame (\d+) -> .*?\s([\d.]+)s", lf.read()):
                    with self.lock:
                        self.times.setdefault(tag, {})[int(m.group(1))] = float(m.group(2))
            bad = [os.path.relpath(p, ROOT) for p in job["expect"]
                   if not (frame_ok(p) if p.endswith(".png") else os.path.exists(p))]
            if job.get("size") and not bad:
                got = png_wh(job["expect"][0])
                if got != tuple(job["size"]):
                    bad.append(f"{os.path.relpath(job['expect'][0], ROOT)} is {got}, want {tuple(job['size'])}")
            changed = [os.path.relpath(p, ROOT) for p, sig in before.items() if sig != stat_sig(p)]
            if rc != 0 or bad or changed:
                with self.lock:
                    self.failed.append({"shot": tag, "rc": rc, "missing": bad[:20], "changed": changed, "log": log})
                print(f"[finals v2] GPU{gpu} {tag} job{jn} rc={rc} missing={bad[:6]} changed={changed} see {log}",
                      flush=True)
        print(f"[finals v2] {time.strftime('%H:%M:%S')} GPU{gpu} done  {tag} job{jn} "
              f"in {(time.time() - t0) / 60:.1f} min", flush=True)

    def run_stage(self, jobs):
        threads = [threading.Thread(target=self.worker, args=(g,), daemon=True) for g in self.gpus]
        for t in threads:
            t.start()
        for j in jobs:
            self.q.put(j)
        for _ in threads:
            self.q.put(None)
        for t in threads:
            t.join()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=None, help="v1 default: all five v1 shots; v2: see the module docstring")
    ap.add_argument("--gpus", default=",".join(sorted(ALLOWED)),
                    help="GPU ids (outside Slurm: within DOPA_ALLOWED_GPUS, default 6,7); inside a Slurm job: slurm = all allocated")
    ap.add_argument("--mode", default="final", choices=["final", "preview"])
    ap.add_argument("--frames", default=None, help="subset like 1-30,45 (applies to every listed shot)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--film", default="v1", choices=["v1", "v2"])
    a = ap.parse_args()
    gpus = [g.strip() for g in a.gpus.split(",") if g.strip()]
    allowed = ALLOWED
    if os.environ.get("SLURM_JOB_ID") and os.environ.get("CUDA_VISIBLE_DEVICES"):
        # inside a Slurm GPU job (cgroup ConstrainDevices=yes): the job's own GPUs are the allowed set, and
        # --gpus slurm means "all of them" (2026-11-20: user allowed Slurm jobs with up to 4 GPUs)
        allowed = {g.strip() for g in os.environ["CUDA_VISIBLE_DEVICES"].split(",") if g.strip()}
        if a.gpus == "slurm":
            gpus = sorted(allowed)
    if not gpus or not set(gpus) <= allowed:
        sys.exit(f"render_finals: GPUs {gpus} not allowed (allowed: {','.join(sorted(allowed))})")
    if a.film == "v2":
        sys.exit(main_v2(a, gpus))
    a.shots = a.shots or ",".join(ORDER)
    os.makedirs(LOGDIR, exist_ok=True)
    table = shots_table()
    want = [s for s in ORDER if s in a.shots.split(",")]
    subset = parse_range(a.frames) if a.frames else None
    r = Runner(gpus, a.mode, a.dry_run)
    t_start = time.time()

    pre = [s for s in want if s != "s05_title"]
    jobs = []
    for sid in pre:
        miss = missing_frames(sid, table[sid]["frames"], a.mode, subset)
        print(f"[finals] {sid}: {len(miss)} frames to render")
        jobs += make_jobs(sid, miss, gpus)
    if jobs:
        r.run_stage(jobs)

    if "s05_title" in want:
        blockers = {s: len(missing_frames(s, table[s]["frames"], a.mode)) for s in ORDER if s != "s05_title"}
        if any(blockers.values()) and a.mode == "final":
            print(f"[finals] WARNING: upstream frames missing {blockers}; proxies will fall back to preview/"
                  f"placeholder tiles for those shots")
        if not a.dry_run:
            subprocess.call([os.path.join(ROOT, "tools", "venv", "bin", "python"), "-I",
                             os.path.join(ROOT, "scripts", "make_tile_proxies.py")], cwd=ROOT)
        miss = missing_frames("s05_title", table["s05_title"]["frames"], a.mode, subset)
        print(f"[finals] s05_title: {len(miss)} frames to render")
        r.run_stage(make_jobs("s05_title", miss, gpus))

    gpu_s = sum(sum(v.values()) for v in r.times.values())
    summary = {"wall_min": round((time.time() - t_start) / 60, 1), "gpu_hours_render": round(gpu_s / 3600, 2),
               "per_shot_mean_s": {k: round(sum(v.values()) / len(v), 1) for k, v in r.times.items() if v},
               "failed": r.failed}
    with open(os.path.join(LOGDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("[finals] summary", json.dumps(summary))
    sys.exit(1 if r.failed else 0)


if __name__ == "__main__":
    main()
