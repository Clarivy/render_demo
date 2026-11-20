"""Download CC0 / OFL / public-domain assets for the opening animation.

Run:  python3 -I scripts/fetch_assets.py <assets_dir>
Everything lands under <assets_dir>/{hdri,textures,models,fonts,paintings}.
"""
import hashlib
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "render-demo-asset-fetch/1.0"}
ROOT = os.path.abspath(sys.argv[1])

HDRIS = {  # id -> resolution
    "colorful_studio": "4k",
    "studio_small_09": "4k",
    "cyclorama_hard_light": "4k",
    "neon_photostudio": "4k",
    "brown_photostudio_02": "4k",
    "venice_sunset": "4k",
    "the_sky_is_on_fire": "4k",
    "noon_grass": "4k",
    "spruit_sunrise": "4k",
    "kloppenheim_06_puresky": "4k",
}
TEXTURES = {  # id -> resolution
    "marble_01": "4k",
    "floor_tiles_06": "4k",
    "wood_floor": "4k",
    "painted_plaster_wall": "4k",
    "curly_teddy_checkered": "8k",
    "quatrefoil_jacquard_fabric": "8k",
    "velour_velvet": "4k",
    "ribbed_corduroy": "4k",
    "fabric_pattern_07": "4k",
    "rubber_tiles": "4k",
}
TEX_MAPS = ["Diffuse", "Rough", "nor_gl", "Displacement"]
MODELS = {  # id -> texture resolution for gltf
    "magnifying_glass_01": "4k",
    "rubber_duck_toy": "4k",
    "lightbulb_01": "2k",
    "desk_lamp_arm_01": "4k",
    "food_lime_01": "2k",
    "food_kiwi_01": "2k",
}
RAW = [  # (relative destination, url)
    ("fonts/Fredoka-Variable.ttf", "https://github.com/google/fonts/raw/main/ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf"),
    ("fonts/DynaPuff-Variable.ttf", "https://github.com/google/fonts/raw/main/ofl/dynapuff/DynaPuff%5Bwdth,wght%5D.ttf"),
    ("fonts/TitanOne-Regular.ttf", "https://github.com/google/fonts/raw/main/ofl/titanone/TitanOne-Regular.ttf"),
    ("fonts/LilitaOne-Regular.ttf", "https://github.com/google/fonts/raw/main/ofl/lilitaone/LilitaOne-Regular.ttf"),
    ("fonts/RammettoOne-Regular.ttf", "https://github.com/google/fonts/raw/main/ofl/rammettoone/RammettoOne-Regular.ttf"),
    ("fonts/Poppins-SemiBold.ttf", "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf"),
    ("fonts/Poppins-Bold.ttf", "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"),
    ("fonts/Poppins-ExtraBold.ttf", "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf"),
    ("fonts/Nunito-Variable.ttf", "https://github.com/google/fonts/raw/main/ofl/nunito/Nunito%5Bwght%5D.ttf"),
    ("models/stanford-bunny.obj", "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/stanford-bunny.obj"),
    ("models/spot.obj", "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/spot.obj"),
    ("models/armadillo.obj", "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/armadillo.obj"),
    ("paintings/seurat_grande_jatte_20000.jpg",
     "https://upload.wikimedia.org/wikipedia/commons/7/7d/A_Sunday_on_La_Grande_Jatte%2C_Georges_Seurat%2C_1884.jpg"),
]


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def download(url, dest, md5=None):
    dest = os.path.join(ROOT, dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return f"skip {dest}"
    tmp = dest + ".part"
    h = hashlib.md5()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
    if md5 and h.hexdigest() != md5:
        os.remove(tmp)
        raise RuntimeError(f"md5 mismatch for {url}")
    os.replace(tmp, dest)
    return f"ok   {dest} ({os.path.getsize(dest) / 1e6:.1f} MB)"


def jobs():
    out = []
    for hid, res in HDRIS.items():
        f = get_json(f"https://api.polyhaven.com/files/{hid}")["hdri"][res]["hdr"]
        out.append((f["url"], f"hdri/{hid}_{res}.hdr", f.get("md5")))
    for tid, res in TEXTURES.items():
        files = get_json(f"https://api.polyhaven.com/files/{tid}")
        for m in TEX_MAPS:
            if m not in files or res not in files[m]:
                continue
            fmt = "jpg" if "jpg" in files[m][res] else ("png" if "png" in files[m][res] else None)
            if fmt is None:
                continue
            f = files[m][res][fmt]
            out.append((f["url"], f"textures/{tid}/{tid}_{m.lower()}_{res}.{fmt}", f.get("md5")))
    for mid, res in MODELS.items():
        g = get_json(f"https://api.polyhaven.com/files/{mid}")["gltf"][res]["gltf"]
        out.append((g["url"], f"models/{mid}/{os.path.basename(g['url'])}", g.get("md5")))
        for rel, inc in g.get("include", {}).items():
            out.append((inc["url"], f"models/{mid}/{rel}", inc.get("md5")))
    for rel, url in RAW:
        out.append((url, rel, None))
    return out


def _safe(url, dest, md5):
    try:
        return download(url, dest, md5)
    except Exception as e:  # keep going, report at the end
        return f"FAIL {dest}: {e}"


if __name__ == "__main__":
    todo = jobs()
    print(f"{len(todo)} files")
    with ThreadPoolExecutor(12) as ex:
        for msg in ex.map(lambda j: _safe(*j), todo):
            print(msg, flush=True)
