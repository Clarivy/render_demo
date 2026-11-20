#!/bin/bash
# CPU post-production on any Slurm cluster: final QA, captions, 16-bit composite, H.264 + ProRes encodes.
#
#   sbatch -p <partition> scripts/slurm_post.sbatch --film v2        # -> out/v2/
#   sbatch -p <partition> scripts/slurm_post.sbatch --film v1        # -> out/
#
# Submit from the project root after scripts/slurm_render.sbatch finished.
#SBATCH --job-name=larenderer_post
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH --output=logs/slurm/%x_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
FILM=${2:-v2}
[ "${1:-}" = "--film" ] || FILM=v2
tools/venv/bin/python -I scripts/qa_finals.py --film "$FILM"
tools/venv/bin/python -I scripts/assemble.py --film "$FILM" --mode final --master
echo "[slurm] post done $(date)"
