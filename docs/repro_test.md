# Reproduction test (2026-11-20)

Goal: show that a fresh `git clone` plus the data bundle renders the same pictures, on another node, without anything
from the original box's working directories.

| Step | Result |
|---|---|
| `git clone` → `/beegfs/users/qzhao/render_demo_reprotest` | commit `f92998a` |
| `scripts/bootstrap.sh --bundle /beegfs/users/qzhao/render_demo/bundles` | 58 s; bundle SHA256SUMS OK; Blender 4.5.15 LTS; venv from `repro/requirements.txt`; **119/119 assets match `repro/assets.sha256`** |
| Slurm, 1 GPU, node **br-dfw-h200-tlv1-15** (the original box is tlv1-10; `--exclude`d) | jobs 211356, 211357 and the tile-input rerun |

Preview-mode frames from the clone vs. the original box (mean / p99 / max absolute difference, 8-bit levels):

| Shot | Frame | Mean | p99 | Max | Note |
|---|---|---|---|---|---|
| `s01_lights_world` (v1 script) | 121 | 0.040 | 0.33 | 1 | GPU noise level |
| `s03_gummy` (v1 script) | 91 | 0.027 | 0.33 | 1 | GPU noise level |
| `s04_subject` | 180 | 0.042 | 0.33 | 5 | GPU noise level |
| `t_disco` | 1 | 0.029 | 0.33 | 1 | GPU noise level |
| `s05_finale`, same hex-tile inputs | 150 | 0.058 below the honeycomb (0.92 in it) | 0.67 | — | the original preview was rendered at 17:20, when the tiles were still preview-quality; the library now holds finals |

Found and fixed during the test: `shots/s05_finale.py` imported its colour-inverse LUT code from `renders/work/`
(not in git) and that code had an absolute Blender path. Moved to `lib/pbrn_view/` (commit `f92998a`); the 97³ LUT
rebuilt from it, inside Blender on the clone, is **bit-identical** to the one the v2 finals used.

Not exercised end to end on the clone: the full final queue (≈ 5.5 GPU-h from scratch without the v1 render cache,
≈ 2.2 GPU-h with it) and the CPU post job; their code paths are the ones that produced `out/v2/` on the original box.
