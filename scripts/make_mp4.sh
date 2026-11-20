#!/usr/bin/env bash
# Encode a PNG frame folder to H.264 MP4 (yuv420p, error-diffusion dither from 16-bit).
#   scripts/make_mp4.sh renders/preview/s01_lights out/s01_preview.mp4 [fps=30] [prefix=f_]
# Uses the BT.709 matrix + bt709/tv tags (same chain as scripts/assemble.py); swscale's default BT.601
# matrix shifted palette pink/mint by up to 21/255 in BT.709 players.
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=$1; OUT=$2; FPS=${3:-30}; PRE=${4:-f_}
mkdir -p "$(dirname "$OUT")"
FILES=("$DIR"/${PRE}*.png)   # glob is sorted; avoids ls|head SIGPIPE under pipefail
FIRST=$(basename "${FILES[0]}" .png); FIRST=${FIRST#"$PRE"}; FIRST=$((10#$FIRST))
./tools/ffmpeg/ffmpeg -y -loglevel error -framerate "$FPS" -start_number "$FIRST" -i "$DIR/${PRE}%04d.png" \
  -vf "scale=1920:1080:flags=lanczos:sws_dither=ed:out_color_matrix=bt709:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 16 \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -movflags +faststart "$OUT"
echo "$OUT"
