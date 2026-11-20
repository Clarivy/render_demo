# LaRenderer — Opening Animation Brief

## 1. What we are making
A ~24–30 s **opening animation** for the promo video of **LaRenderer**, a feed-forward *latent-space neural
renderer* (scene → sparse voxel latents → transformer encoder → flow-matching camera decoder). Reference:
`intro.tex` (paper intro) and `teaser.pdf` (teaser: dollhouse-corner rooms with mustard / coral / teal /
orange walls, a crystal-glass Stanford bunny, a chrome spiral sculpture, a mirror ball, glassware,
framed impressionist paintings, marble and checker-tile floors, bright caustics).

**The opening shows concepts, not architecture.** No network diagrams, no tokens, no equations.
It must make four capability claims instantly readable to a graphics / vision audience:

| # | Capability (user's words) | What the viewer must *see* |
|---|---|---|
| C1 | Accepts **point lights** and **env-map** input; **any env-map rotation stays consistent** | light sources moving/added and their shadows/highlights responding; an environment map that visibly rotates while reflections, shading and shadows rotate coherently |
| C2 | **Complex light transport & caustics; highly reflective materials** | sharp refractive caustics (ideally coloured), mirror/chrome inter-reflections, glass |
| C3 | **Animated geometry with frame-to-frame continuity** | objects moving / deforming smoothly with stable, flicker-free shading, shadows, reflections |
| C4 | **High-resolution textures** | a continuous push from a wide view to extreme close-up where texture detail stays crisp |

Ends on the title **LaRenderer**.

## 2. Style: 多巴胺 (Dopamine) × Tactile 3D
* **Dopamine**: joyful, saturated candy colours, colour-blocking, optimistic energy. Pastel grounds +
  saturated hero objects. Palette (in `lib/dopa.py`, `D.PALETTE`):
  hero `pink #FF4D9D, coral #FF6A5C, orange #FF8A1F, lemon #FFD23F, lime #B5E61D, mint #2ED8A3,
  aqua #1FC2EE, blue #2E5BFF, violet #8A5CF6, lilac #C3A6FF`;
  pastel grounds `blush, peach, butter, pistachio, sky, lavender, cream`; neutrals `ink, white, chrome, gold`.
* **Tactile 3D**: everything looks touchable — rounded/bevelled/inflated forms, soft clay, glossy candy
  plastic, squishy jelly, velvet/plush, chrome, glass; soft big-softbox lighting with gentle contact
  shadows; miniature/toy scale with shallow depth of field; bouncy, springy, satisfying motion
  (squash & stretch, overshoot, settle).
* Nod to the paper teaser (dollhouse-corner rooms, glass bunny, chrome spiral, mirror ball, paintings)
  re-imagined in this style — the opening should feel like the teaser came alive.
* Original designs only. Do not recreate existing IP/characters (e.g. no hopping desk-lamp character).

## 3. Technical frame
* **Blender 4.5.15 LTS**, Cycles, `tools/blender/blender -b --factory-startup -P shots/<shot>.py -- <flags>`.
* **GPUs: at most 2 for the whole project — use only GPU 6 and GPU 7** via `CUDA_VISIBLE_DEVICES=6` or `=7`.
  Never touch other GPUs. Backend CUDA (H200 has no RT cores; CUDA ≥ OptiX here).
* Output 1920×1080, **30 fps**, PNG 16-bit frames → assembled with `tools/ffmpeg/ffmpeg`.
* Colour pipeline is fixed film-wide: view transform **Khronos PBR Neutral**, look None, exposure ≈ −0.2
  (per-shot exposure tweak within ±0.5 allowed). It keeps palette colours faithful. (`D.setup_color()`)
* Measured speed: style swatch (11 objects incl. glass, 1280×720, 256 spp, adaptive, OIDN) ≈ 4–6 s/frame
  on one H200. Caustic-heavy glass scenes need more samples (1024–2048).
* **Final render budget**: ≤ ~6 GPU-hours total (≈ 3 h wall-clock on 2 GPUs) → average ≲ 25 s per
  1080p frame per GPU across ~800–900 frames. Spend more on the caustics shot, less elsewhere.
* Music is added later by the editor: cut on a **120 BPM grid** (1 beat = 15 frames, 1 bar = 60 frames).

## 4. Code conventions
* Every shot is a standalone, deterministic script `shots/sNN_name.py` that builds its scene from
  scratch with the shared kit **`lib/dopa.py`** (read it — palette, materials, rounded geometry, text,
  HDRI world rig with rotatable mapping, lights, camera rig, easing/spring/bounce helpers, `bake()`
  per-frame keyframing, CLI `parse_args()`/`finish()`), then renders via `D.finish(args, ...)`.
* Flags: `--mode draft|preview|final` (25 %/32 spp, 50 %/128 spp, 100 %/shot samples), `--frames
  "1-150"` or `"1,40,90"` or `"1-150:10"`, `--out DIR`, `--samples N`, `--pct N`, `--save-blend PATH`.
* Review helper: `tools/venv/bin/python -I scripts/contact_sheet.py OUT.png FRAMES...`.
  View any PNG with the Read tool. Two-GPU render: `scripts/render_split.sh shots/x.py final 1-150 "6,7"`.
* Style calibration render: `renders/calib/swatch_0001.png` (all kit materials under the film look).

## 5. Asset inventory (all CC0 / OFL / public domain, under `assets/`)
* HDRIs (4k .hdr, `D.HDRI[name]`): colorful_studio, studio_small_09, cyclorama_hard_light, neon_photostudio,
  brown_photostudio_02, venice_sunset, the_sky_is_on_fire, noon_grass, spruit_sunrise, kloppenheim_06_puresky.
* Textures (Poly Haven; diffuse/rough/nor_gl/displacement; `D.polyhaven_texture(id, res)`): marble_01,
  floor_tiles_06, wood_floor, painted_plaster_wall, rubber_tiles, velour_velvet, ribbed_corduroy,
  fabric_pattern_07 (4k); curly_teddy_checkered, quatrefoil_jacquard_fabric (8k).
* Paintings: `paintings/seurat_grande_jatte_20000.jpg` (Seurat, *A Sunday on La Grande Jatte*, 20000×13313,
  pointillist dots resolve at extreme zoom) + 16384/8192/2048 px versions; `vangogh_wheat_field_cypresses_met.jpg` (4000×3184).
* Models: Stanford bunny (`D.stanford_bunny`, glass-ready), Spot cow (`D.spot_cow`), armadillo (obj);
  Poly Haven glTF: magnifying_glass_01, rubber_duck_toy, lightbulb_01, desk_lamp_arm_01, food_lime_01, food_kiwi_01.
* Fonts: Fredoka Bold/SemiBold (rounded, default title), DynaPuff Bold (puffy), Titan One, Lilita One,
  Rammetto One, Poppins Bold/SemiBold/ExtraBold, Nunito Black.
* More CC0 assets may be fetched (e.g. Poly Haven API `https://api.polyhaven.com/files/<id>`) into `assets/`.

## 6. Measured technical learnings (read before building)
* **Caustics** (`renders/calib/caus_compare.png`, `renders/calib/caus_pop_0001.png`): plain path tracing is the way.
  1080p glass set: 1024 spp ≈ 14 s, 2048 ≈ 15–20 s, 4096 ≈ 31 s per frame on one H200. MNEE shadow caustics
  were 5× slower for no visible gain — don't use. Caustics only *read* if the receiver is not over-exposed:
  keep the directly lit floor at mid-tone (≈50–70 %), low ambient (world ≈0.05–0.1), a small-radius
  spot/point (radius 0.02–0.05) at a grazing-ish angle so caustics land inside the glass objects' shadows.
  `D.mat_glass_dispersive` (3-IOR fake dispersion) costs no extra time and gives rainbow sparkle + rainbow caustics.
  Coloured glass (`D.mat_glass(color, absorb=2)`) throws coloured caustics.
* **Big textures**: the 20000 px Seurat takes ~11 s to load and ~30 s for the first frame (upload); later frames
  of the same process are fast (persistent data). Use the 2048/8192 versions for drafts.
* **First frame of every process** pays BVH/texture setup; subsequent frames reuse it.
* **UVs**: generated meshes (`rounded_box`, `cylinder`, `cyclorama`, `plane`) carry box/metre UVs, so
  `mat_image(..., uv_scale=k)` repeats k times per metre. Imported glTFs keep their own UVs.
* **Stanford bunny**: `D.stanford_bunny()` (holes filled). Do NOT voxel-remesh it (fails on this scan).
* **Image sequences**: `D.mat_video(first_png, n_frames, start=..)` plays a rendered shot as a texture (verified).
* **Viewer banding**: 16-bit PNGs can look posterised in the image viewer; the files are smooth.
  draft/preview modes write 8-bit dithered PNGs for review.
* **Temporal stability**: keep Cycles' seed static (default; do not enable animated seed), use enough samples
  that OIDN is not hallucinating detail frame-to-frame — flicker would undermine the C3 claim.
* Kit smoke test with most helpers: `shots/_kit_test.py` → `renders/calib/kit/f_0015.png`.
* **HDRI character** (`renders/calib/hdri_sheet.png`, same set under each map): for the env-rotation proof use
  maps with a strong compact sun → `spruit_sunrise` (low warm sun, long sweeping shadows) or `noon_grass`
  (crisp high sun); `cyclorama_hard_light` (hard studio key). Mood fills: `the_sky_is_on_fire` (pink cast),
  `venice_sunset` (lilac cast); `colorful_studio`/`studio_small_09`/`brown_photostudio_02` are soft studio light.
