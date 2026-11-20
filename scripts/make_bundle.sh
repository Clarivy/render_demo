#!/bin/bash
# Build the data bundle needed to re-render this project on another cluster. Code travels by git; this bundle
# carries everything git does not: the assets, the exact tool tarballs, and optionally a render cache.
#
#   scripts/make_bundle.sh [OUT_DIR] [--with-cache]
#
# OUT_DIR (default /beegfs/users/qzhao/render_demo/bundles) receives:
#   render_demo_assets.tar.zst          assets/ (fetched + generated; checked against repro/assets.sha256)
#   tools-src/blender-4.5.15-linux-x64.tar.xz   the official Blender tarball (sha256 in repro/tools.sha256)
#   tools-src/ffmpeg-7.0.2-amd64-static.tar.xz  the static ffmpeg used for every encode
#   render_demo_cache_v1_s01_s03.tar    (--with-cache) v1 finals of S01-S03 + their meta: v2 reuses them, and
#                                       re-rendering them costs ~2.5 GPU-h (S02's caustics dominate)
#   SHA256SUMS                          checksums of all of the above
# Copy OUT_DIR to the other cluster (rsync, or S3/R2), then run scripts/bootstrap.sh --bundle <dir> there.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=/beegfs/users/qzhao/render_demo/bundles
WITH_CACHE=0
for a in "$@"; do
  case "$a" in
    --with-cache) WITH_CACHE=1 ;;
    *) OUT=$a ;;
  esac
done
mkdir -p "$OUT/tools-src"
cd "$ROOT"

echo "[bundle] asset manifest -> repro/assets.sha256"
(cd assets && find -L . -type f ! -name '*.part' | LC_ALL=C sort | xargs -d '\n' sha256sum) > repro/assets.sha256

echo "[bundle] assets -> $OUT/render_demo_assets.tar.zst"
tar -C "$ROOT" -chf - assets | zstd -T0 -3 -q -f -o "$OUT/render_demo_assets.tar.zst"

BL=blender-4.5.15-linux-x64.tar.xz
if [ ! -f "$OUT/tools-src/$BL" ]; then
  echo "[bundle] downloading the official $BL"
  curl -sL --fail -A "render-demo-bootstrap/1.0" -o "$OUT/tools-src/$BL" \
    "https://download.blender.org/release/Blender4.5/$BL"
fi
FF=ffmpeg-7.0.2-amd64-static
if [ ! -f "$OUT/tools-src/$FF.tar.xz" ]; then
  echo "[bundle] packing tools/$FF"
  (cd tools && tar -chf - "$FF" | xz -T0 -6 > "$OUT/tools-src/$FF.tar.xz")
fi
(cd "$OUT/tools-src" && sha256sum -c "$ROOT/repro/tools.sha256")

if [ "$WITH_CACHE" = 1 ]; then
  echo "[bundle] render cache (v1 finals S01-S03 + meta) -> $OUT/render_demo_cache_v1_s01_s03.tar"
  tar -C "$ROOT" -chf "$OUT/render_demo_cache_v1_s01_s03.tar" \
    renders/final/s01_lights_world renders/final/s02_caustics renders/final/s03_gummy \
    renders/meta/s01_lights_world.json renders/meta/s02_caustics.json renders/meta/s03_gummy.json
fi

(cd "$OUT" && find . -maxdepth 2 -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs -d '\n' sha256sum > SHA256SUMS)
echo "[bundle] done:"; ls -la "$OUT" "$OUT/tools-src"
