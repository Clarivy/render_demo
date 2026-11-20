#!/usr/bin/env bash
# Render a shot across two GPUs (interleaved frames), e.g.
#   scripts/render_split.sh shots/s02_caustics.py final 1-150 "6,7" [extra args...]
# Each GPU gets its own Blender process (better scaling than multi-device in one process).
set -euo pipefail
cd "$(dirname "$0")/.."
SHOT=$1; MODE=$2; RANGE=$3; GPUS=$4; shift 4
IFS=',' read -ra G <<< "$GPUS"
for g in "${G[@]}"; do
  if [[ "$g" != "6" && "$g" != "7" ]]; then echo "render_split: GPU '$g' not allowed (only 6,7)" >&2; exit 3; fi
done
N=${#G[@]}
A=${RANGE%-*}; B=${RANGE#*-}
NAME=$(basename "$SHOT" .py)
mkdir -p logs
for i in "${!G[@]}"; do
  START=$((A + i))
  CUDA_VISIBLE_DEVICES=${G[$i]} ./tools/blender/blender -b --factory-startup -P "$SHOT" -- \
    --mode "$MODE" --frames "${START}-${B}:${N}" "$@" > "logs/${NAME}_${MODE}_gpu${G[$i]}.log" 2>&1 &
done
wait
grep -h "\[dopa\]" logs/${NAME}_${MODE}_gpu*.log | wc -l
