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
ALLOWED = {"6", "7"}
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
    ap.add_argument("--shots", default=",".join(ORDER))
    ap.add_argument("--gpus", default="6,7")
    ap.add_argument("--mode", default="final", choices=["final", "preview"])
    ap.add_argument("--frames", default=None, help="subset like 1-30,45 (applies to every listed shot)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    gpus = [g.strip() for g in a.gpus.split(",") if g.strip()]
    if not gpus or not set(gpus) <= ALLOWED:
        sys.exit(f"render_finals: GPUs {gpus} not allowed (only 6,7)")
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
