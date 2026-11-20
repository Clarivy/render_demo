#!/bin/bash
# Set up a fresh checkout so it can render, on any Linux x86_64 cluster with NVIDIA GPUs.
#
#   scripts/bootstrap.sh --bundle DIR [--data-root DIR] [--cache] [--python python3.12]   # supported route
#   scripts/bootstrap.sh --download   [--data-root DIR]           [--python python3.12]   # from the internet
#
# --bundle DIR     a directory made by scripts/make_bundle.sh (assets tarball, tool tarballs, SHA256SUMS)
# --download       Blender from download.blender.org (sha256-checked), current static ffmpeg, assets via
#                  scripts/fetch_assets.py + scripts/derive_assets.py (upstream files may have changed)
# --data-root DIR  put the big trees (renders out tools assets logs) on DIR (shared storage visible to the compute
#                  nodes) and symlink them here, as on the original box (/beegfs/users/qzhao/render_demo)
# --cache          also unpack render_demo_cache_v1_s01_s03.tar from the bundle (v1 finals that v2 reuses)
# --python EXE     Python >= 3.11 for the helper venv (default python3)
# Idempotent: re-running skips finished steps. The project root itself must be on storage the compute nodes see.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
BUNDLE="" DOWNLOAD=0 DATA="" CACHE=0 PY=python3
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) BUNDLE=$(cd "$2" && pwd); shift 2 ;;
    --download) DOWNLOAD=1; shift ;;
    --data-root) DATA=$2; shift 2 ;;
    --cache) CACHE=1; shift ;;
    --python) PY=$2; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
done
[ -n "$BUNDLE" ] || [ "$DOWNLOAD" = 1 ] || { echo "need --bundle DIR or --download"; exit 2; }
say() { echo "[bootstrap] $*"; }

# 1. big trees: real dirs, or symlinks to --data-root
for d in renders out tools assets logs; do
  if [ -e "$d" ] || [ -L "$d" ]; then continue; fi
  if [ -n "$DATA" ]; then mkdir -p "$DATA/$d"; ln -s "$(cd "$DATA/$d" && pwd)" "$d"; say "$d -> $DATA/$d"
  else mkdir -p "$d"; fi
done
mkdir -p logs/slurm renders/meta

# 2. verify the bundle
if [ -n "$BUNDLE" ]; then
  say "checking $BUNDLE/SHA256SUMS"
  (cd "$BUNDLE" && sha256sum --quiet -c SHA256SUMS)
fi

# 3. tools: Blender 4.5.15 LTS (exact) and a static ffmpeg
BL=blender-4.5.15-linux-x64
if [ ! -x "tools/$BL/blender" ]; then
  if [ -n "$BUNDLE" ]; then src="$BUNDLE/tools-src/$BL.tar.xz"
  else src="tools/$BL.tar.xz"
    curl -sL --fail -A "render-demo-bootstrap/1.0" -o "$src" "https://download.blender.org/release/Blender4.5/$BL.tar.xz"
  fi
  want=$(grep " $BL.tar.xz\$" repro/tools.sha256 | cut -d' ' -f1)
  got=$(sha256sum "$src" | cut -d' ' -f1)
  [ "$want" = "$got" ] || { echo "Blender tarball sha256 mismatch ($got)"; exit 1; }
  say "unpacking $BL"; tar -xJf "$src" -C tools
  [ -n "$BUNDLE" ] || rm -f "$src"
fi
ln -sfn "$BL" tools/blender
FF=ffmpeg-7.0.2-amd64-static
if [ ! -x tools/ffmpeg/ffmpeg ]; then
  if [ -n "$BUNDLE" ]; then
    say "unpacking $FF"; tar -xJf "$BUNDLE/tools-src/$FF.tar.xz" -C tools; ln -sfn "$FF" tools/ffmpeg
  else
    say "downloading the current static ffmpeg (7.0.2 is no longer published upstream; encodes may differ slightly)"
    curl -sL --fail -A "render-demo-bootstrap/1.0" -o tools/ffmpeg-static.tar.xz \
      https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    dir=$(tar -tJf tools/ffmpeg-static.tar.xz | head -1 | cut -d/ -f1)
    tar -xJf tools/ffmpeg-static.tar.xz -C tools && rm tools/ffmpeg-static.tar.xz && ln -sfn "$dir" tools/ffmpeg
  fi
fi

# 4. helper venv (numpy / opencv / pillow / fonttools, pinned)
if [ ! -x tools/venv/bin/python ]; then
  say "creating tools/venv with $PY"
  "$PY" -m venv tools/venv
  tools/venv/bin/python -m pip install -q --upgrade pip
  tools/venv/bin/python -m pip install -q -r repro/requirements.txt
fi

# 5. assets
if [ ! -f assets/fonts/Fredoka-Bold.ttf ]; then
  if [ -n "$BUNDLE" ]; then
    say "unpacking assets"
    zstd -dc "$BUNDLE/render_demo_assets.tar.zst" | tar -xf - -C "$ROOT" --keep-directory-symlink
  else
    tools/venv/bin/python -I scripts/fetch_assets.py assets
    tools/venv/bin/python -I scripts/derive_assets.py
  fi
fi
say "verifying assets against repro/assets.sha256"
if (cd assets && sha256sum --quiet -c "$ROOT/repro/assets.sha256"); then say "assets: all $(wc -l < repro/assets.sha256) files match"
else say "WARNING: some assets differ from the manifest (see above)"; fi

# 6. optional render cache (v1 finals S01-S03 that film v2 reuses)
if [ "$CACHE" = 1 ] && [ -n "$BUNDLE" ] && [ -f "$BUNDLE/render_demo_cache_v1_s01_s03.tar" ]; then
  say "unpacking the v1 S01-S03 render cache"
  tar -xf "$BUNDLE/render_demo_cache_v1_s01_s03.tar" -C "$ROOT" --keep-directory-symlink
fi

# 7. smoke checks
tools/blender/blender -b --factory-startup --python-expr "import bpy; print('blender', bpy.app.version_string)" \
  2>/dev/null | grep "^blender 4.5.15"
tools/ffmpeg/ffmpeg -hide_banner -encoders 2>/dev/null | grep -qE "libx264" && say "ffmpeg has libx264"
tools/venv/bin/python -I -c "import cv2, numpy, PIL, fontTools; print('[bootstrap] venv ok')"
cat <<EOF
[bootstrap] ready. Next (see README, 在其他集群复现):
  sbatch -p <partition> --gres=gpu:4 scripts/slurm_render.sbatch --film v2     # every missing final frame
  sbatch -p <partition> scripts/slurm_post.sbatch --film v2                    # QA + subtitles + encodes -> out/v2/
EOF
