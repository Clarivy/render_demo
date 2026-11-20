#!/bin/bash
# LaRenderer v2 finals on Slurm (user allowed up to 4 GPUs, 2026-11-20).
# The project lives on this node's local disk, so the job is pinned to br-dfw-h200-tlv1-10.
#SBATCH --job-name=larenderer_v2_finals
#SBATCH --partition=batch
#SBATCH --nodelist=br-dfw-h200-tlv1-10
#SBATCH --nodes=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=64
#SBATCH --mem=384G
#SBATCH --time=04:00:00
#SBATCH --output=/home/qzhao/render_demo/logs/slurm/%x_%j.out
set -euo pipefail
cd /home/qzhao/render_demo
echo "[slurm] job $SLURM_JOB_ID on $(hostname) CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-}"
nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader
python3 scripts/render_finals.py --film v2 --gpus slurm "$@"
echo "[slurm] done $(date)"
