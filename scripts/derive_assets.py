"""Rebuild the assets that are not plain downloads (only needed when NOT using the data bundle).

    tools/venv/bin/python -I scripts/derive_assets.py          # after scripts/fetch_assets.py assets

The data bundle (scripts/make_bundle.sh -> scripts/bootstrap.sh --bundle) already contains everything and is the
supported route; this script records how the derived files were made so a from-the-internet rebuild is possible.
Steps (each skipped if its output exists):
  1. paintings/vangogh_wheat_field_cypresses_met.jpg  - The Met Open Access, object 436535 (CC0)
  2. paintings/SOURCES.txt
  3. fonts/{Fredoka-Bold,Fredoka-SemiBold,DynaPuff-Bold,Nunito-Black,Nunito-ExtraBold}.ttf
     - static instances of the variable Google Fonts (fontTools varLib.instancer)
  4. paintings/seurat_grande_jatte_{16384,8192,2048}.jpg - Lanczos downscales of the 20000 px scan, JPEG q95
  5. hdri/candy_sky_4k.hdr, candy_sky_nosun_4k.hdr, candy_sky_preview.png  - scripts/make_candy_sky.py
  6. paintings/derived/seurat_grande_jatte_*_topband.png + seurat_grande_jatte_ext.json - scripts/make_seurat_ext.py
  7. ui/*.png + sprites.json - Blender (GPU): shots/s00_ui_sprites.py. Printed as a command, not run here.
Upstream files can change, so a rebuild may not match repro/assets.sha256 byte for byte; the script reports any
mismatch at the end (sha256sum -c).
"""
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
A = os.path.join(ROOT, "assets")
PY = os.path.join(ROOT, "tools", "venv", "bin", "python")
UA = {"User-Agent": "render-demo-asset-fetch/1.0"}

SOURCES = (
    "vangogh_wheat_field_cypresses_met.jpg - Vincent van Gogh, Wheat Field with Cypresses (1889). The Met, Open "
    "Access (CC0 / public domain), object 436535.\n"
    "seurat_grande_jatte_20000.jpg - Georges Seurat, A Sunday on La Grande Jatte (1884), 20000x13313 scan. "
    "Wikimedia Commons, public domain.\n")
FONTS = [  # output, variable source, axis settings
    ("Fredoka-Bold.ttf", "Fredoka-Variable.ttf", {"wght": 700, "wdth": 100}),
    ("Fredoka-SemiBold.ttf", "Fredoka-Variable.ttf", {"wght": 600, "wdth": 100}),
    ("DynaPuff-Bold.ttf", "DynaPuff-Variable.ttf", {"wght": 700, "wdth": 100}),
    ("Nunito-Black.ttf", "Nunito-Variable.ttf", {"wght": 900}),
    ("Nunito-ExtraBold.ttf", "Nunito-Variable.ttf", {"wght": 800}),
]


def p(*parts):
    return os.path.join(A, *parts)


def step(name, out, fn):
    if os.path.exists(out):
        print(f"[derive] skip {name} ({os.path.relpath(out, ROOT)} exists)")
        return
    print(f"[derive] {name}", flush=True)
    fn()


def vangogh():
    url = "https://images.metmuseum.org/CRDImages/ep/original/DP-42549-001.jpg"
    dst = p("paintings", "vangogh_wheat_field_cypresses_met.jpg")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(dst + ".part", "wb") as f:
        f.write(r.read())
    os.replace(dst + ".part", dst)


def sources():
    with open(p("paintings", "SOURCES.txt"), "w") as f:
        f.write(SOURCES)


def fonts():
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for out, src, axes in FONTS:
        if os.path.exists(p("fonts", out)):
            continue
        inst = instancer.instantiateVariableFont(TTFont(p("fonts", src)), axes)
        inst.save(p("fonts", out))
        print(f"[derive]   fonts/{out}")


def downscales():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(p("paintings", "seurat_grande_jatte_20000.jpg"))
    im.load()
    for w in (16384, 8192, 2048):
        h = round(im.size[1] * w / im.size[0])
        im.resize((w, h), Image.LANCZOS).save(p("paintings", f"seurat_grande_jatte_{w}.jpg"), quality=95)
        print(f"[derive]   paintings/seurat_grande_jatte_{w}.jpg {w}x{h}")


def run(script, *args):
    subprocess.run([PY, "-I", os.path.join(ROOT, "scripts", script), *args], check=True, cwd=ROOT)


def main():
    os.makedirs(p("paintings", "derived"), exist_ok=True)
    step("van Gogh (The Met 436535)", p("paintings", "vangogh_wheat_field_cypresses_met.jpg"), vangogh)
    step("paintings/SOURCES.txt", p("paintings", "SOURCES.txt"), sources)
    step("static font instances", p("fonts", "Nunito-ExtraBold.ttf"), fonts)
    step("painting downscales", p("paintings", "seurat_grande_jatte_2048.jpg"), downscales)
    step("candy sky HDRIs", p("hdri", "candy_sky_preview.png"), lambda: run("make_candy_sky.py"))
    step("Seurat top band", p("paintings", "derived", "seurat_grande_jatte_ext.json"), lambda: run("make_seurat_ext.py"))
    if not os.path.exists(p("ui", "sprites.json")):
        print("[derive] UI sprites need Blender on a GPU; run inside a GPU allocation:\n"
              "    tools/blender/blender -b --factory-startup -P shots/s00_ui_sprites.py")
    print("[derive] checking against repro/assets.sha256")
    r = subprocess.run(["sha256sum", "--quiet", "-c", os.path.join(ROOT, "repro", "assets.sha256")], cwd=A)
    print("[derive] all assets match the manifest" if r.returncode == 0 else
          "[derive] some files differ from the manifest (listed above); renders may differ slightly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
