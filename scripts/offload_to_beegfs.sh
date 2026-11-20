#!/bin/bash
# Move large top-level project dirs to BeeGFS and leave a symlink in place (2026-11-20, local disk quota).
# Whole dirs are moved as units so relative symlinks inside them (renders/film* -> ../final/...) stay valid;
# absolute links (/home/qzhao/render_demo/...) keep resolving through the new symlink. Idempotent.
set -euo pipefail
SRC_ROOT=/home/qzhao/render_demo
DST_ROOT=/beegfs/users/qzhao/render_demo
cd "$SRC_ROOT"
for d in "$@"; do
  if [ -L "$d" ]; then echo "[offload] $d is already a symlink -> $(readlink "$d")"; continue; fi
  [ -d "$d" ] || { echo "[offload] $d missing, skip"; continue; }
  echo "[offload] $(date +%H:%M:%S) copying $d ($(du -sh "$d" | cut -f1))"
  mkdir -p "$DST_ROOT/$d"
  rsync -aH --delete "$d/" "$DST_ROOT/$d/"
  # verify: same file/link count and byte total, and an itemized dry-run shows no differences
  a=$(find "$d" | wc -l); b=$(find "$DST_ROOT/$d" | wc -l)
  sa=$(du -sb --apparent-size "$d" | cut -f1); sb=$(du -sb --apparent-size "$DST_ROOT/$d" | cut -f1)
  # BeeGFS gives symlinks their own mode bits (meaningless on Linux): ignore "permissions only" on links
  diffs=$(rsync -aHn --delete --itemize-changes "$d/" "$DST_ROOT/$d/" | grep -v '^\.L\.\.\.p\.\.\.\.\. ' | wc -l || true)
  echo "[offload] verify $d: entries $a/$b bytes $sa/$sb dry-run diffs $diffs"
  if [ "$a" != "$b" ] || [ "$sa" != "$sb" ] || [ "$diffs" != "0" ]; then echo "[offload] VERIFY FAILED for $d, left untouched"; exit 1; fi
  mv "$d" "$d.__offload_old"
  ln -s "$DST_ROOT/$d" "$d"
  rm -rf "$d.__offload_old"
  echo "[offload] $(date +%H:%M:%S) $d -> $DST_ROOT/$d"
done
