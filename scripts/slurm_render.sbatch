#!/bin/bash
# Final renders on any Slurm cluster (one node; render_finals.py runs one Blender worker per allocated GPU).
#
#   sbatch -p <partition> [--gres=gpu:N] [-A <account>] scripts/slurm_render.sbatch --film v2 [render_finals args]
#
# Submit from the project root (logs go to logs/slurm/, which scripts/bootstrap.sh creates). The project root must
# be on storage the compute node can see. Inside the job dopa allows exactly the GPUs Slurm allocated
# (lib/dopa.py _gpu_guard). Resumable: re-submitting renders only missing or truncated frames.
# On clusters that cannot constrain sub-node GPU jobs (e.g. Crusoe), request a whole node: --gres=gpu:8 --exclusive.
#SBATCH --job-name=larenderer_render
#SBATCH --nodes=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=64
#SBATCH --mem=384G
#SBATCH --time=08:00:00
#SBATCH --output=logs/slurm/%x_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
echo "[slurm] job ${SLURM_JOB_ID:-?} on $(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader || true
python3 scripts/render_finals.py --gpus slurm "$@"
echo "[slurm] done $(date)"
