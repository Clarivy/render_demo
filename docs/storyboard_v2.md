# LaRenderer opening — v2 storyboard addendum (locked 2026-11-20)

v2 = v1 plus two client changes. Everything not mentioned here is exactly as in `docs/storyboard.md` (v1) and
`docs/lead_notes_r2.md`. Read those for the film-wide rules (palette, PBR Neutral, motion language, springs,
light-marker halos, G1 glow, G2 no grey, determinism, `D.bake`).

## 0. The client's notes (verbatim, Chinese) and how we read them
> 保留当前这版；
> * 能不能加一个从一个场景 zoom out 到多个 scene hexagon 作为 ending，LaRenderer 那几个字不变
> * 画不需要放大到那么大，框到主体即可

1. **Keep v1.** v1 is frozen (`versions/v1/`, the v1 files in `out/`, `renders/final/<v1 ids>`). v2 never writes
   any of them. v2 uses new shot ids and writes its film to `out/v2/`.
2. **New ending: zoom out from one scene to many scene hexagons.** The ending starts INSIDE one scene, full frame,
   and pulls back to reveal that the scene is one hexagonal cell in a honeycomb wall of many live scenes.
   The scene we zoom out of is the painting where S04 now stops (a seamless match cut), so the film reads
   "zoom in to the subject (S04) → zoom out to every scene (finale)".
3. **"LaRenderer 那几个字不变":** the title is unchanged. The same ten inflated candy letters, the same materials,
   the same landing choreography, the same three-colour-lights-fuse-to-white beat, the same final camera, so the
   word lands at exactly the same size and place as in v1 (73.8 % of frame width, baseline ≈ 65 %). No tagline.
4. **The painting does not need to be magnified that far; just frame the subject.** S04 no longer pushes to
   ≈ 1 texel/px. It stops on the painting's main subject: the woman with the orange parasol and the little girl in
   white (centre of *La Grande Jatte*), full figures, with the pointillist dots still visible. No dot-pop, no orb in S04.

Open items stay open (slug off by default, no music yet, no "20K" wording).

## 1. Film v2 (16 bars, 960 frames, 32.0 s, 120 BPM, 15 f/beat, 60 f/bar)
| # | id | script | local | film | bars | seconds | source |
|---|---|---|---|---|---|---|---|
| S01 | `s01_lights_world` | v1, unchanged | 1–240 | 1–240 | 1–4 | 0–8 | v1 finals, reused |
| S02 | `s02_caustics` | v1, unchanged | 1–180 | 241–420 | 5–7 | 8–14 | v1 finals, reused |
| S03 | `s03_gummy` | v1, unchanged | 1–180 | 421–600 | 8–10 | 14–20 | v1 finals, reused |
| S04 | **`s04_subject`** | `shots/s04_subject.py` (new, from `s04_every_dot.py`) | 1–180 | 601–780 | 11–13 | 20–26 | new |
| S05 | **`s05_finale`** | `shots/s05_finale.py` (new, from `s05_title.py`) | 1–180 | 781–960 | 14–16 | 26–32 | new |

Cuts (all on bar lines): 240|241, 420|421, 600|601 (whip, unchanged), **780|781 = invisible match cut**
(S05 f1 is the same picture as S04 f180; the pull-back starts on the bar-14 downbeat).

Global hit list for the new part (film frames; local = film − 600 for S04, film − 780 for S05):
- 601 whip-in (unchanged) · 631 push starts · ≈735–750 arrival (SETTLE) · 750–780 still hold on the subject.
- 781 pull-back starts (ease-in from rest) · ≈820–840 honeycomb fills the frame (the "many scenes" moment) ·
  826 (S05 f46) white key orb is born (preferred: it swells out of the painting tile) · 841 (f61) orb at O (bar 15
  downbeat) · 848 (f68) split into coral / lime / blue · ≈855 (f75) camera settles on the v1 end framing ·
  856–890 (f76–110) letters land on 16ths · **901 (f121) fuse to white on the bar-16 downbeat** · 911 (f131)
  light swap · 901–960 hold, shine sweep f144–158, breaths f136 / f166.

## 2. S04 `s04_subject` — "Frame the subject" (C4, 180 f)
Start from a copy of `shots/s04_every_dot.py`. Keep: the gallery set, lighting, materials, the 20000 px scan in
final mode, the whip-in f1–10 and the room-wide f11–30 **bit-for-bit** (so the S03→S04 whip cut is unchanged).
Change:
- **Push target and end framing.** Subject centre on the canvas `u = 0.486, v = 0.633` (Blender UV, v from the
  bottom; the woman with the orange parasol is the visual centre, the girl in white just left of her).
  End framing: camera square to the canvas (as v1), frame height = **0.49 ± 0.02 of the canvas height**
  (≈ 5.9 texels of the 20000 px scan per pixel; the dots read as a fine stipple). The parasol tip and the girl's
  feet are both inside the frame with ≥ 3 % margin. Verify on a test render that the composition is right
  (subject centred, nothing important cut) and adjust the centre by ≤ 0.02 if needed. Measured end zoom (d0/d)
  goes into the meta; it is about ×7 (round it to a clean number such as ×7.0 if the framing tolerance allows).
- **Timing.** f31 push starts (log-distance, `ease_in_out_sine` + screen-space target path as v1 round 2),
  arrival ≈ f135–150 with the SETTLE spring (≈ 6 % overshoot, no dead stop), **static f150–180** (camera, DOF, every
  object identical; rendered frames f150–180 must be identical up to sampling noise — static seed makes them
  bit-identical in practice).
- **Remove** the dot-pop, the pearl/orb, its light and the bloom keying (no emission anywhere in S04 v2; bloom off).
- Motion blur / shutter logic as v1 for the push; f/11 (or whatever keeps the canvas sharp) at the end.
- **Overscan still for the finale's centre tile** (`--overscan` mode, frame 180 camera): same camera position
  and orientation, horizontal sensor fit, sensor width × (2544/1920), resolution **2544 × 2204** (final; preview
  1272 × 1102), so the central 1920 × 1080 is exactly the f180 frame (crop offset x 312, y 562) and the whole
  image is the bounding box of the flat-top hexagon that circumscribes the 16:9 frame. For this still only:
  hide the orange frame and gold lip, and extend the canvas beyond its edges with MIRROR texture extension
  (the top of the hex reaches ≈ 13 % of the canvas height above the painting), so the whole hex shows painting
  only. Output `renders/<mode>/s04_subject/overscan.png` (16-bit in final). QA: its central crop vs f180,
  mean |Δ| ≤ 1/255 (after a 1 px blur), report p99.
- Meta `renders/meta/s04_subject.json`: per-frame `dist_m`, `zoom` (for the caption chip), `px_per_texel`, the
  events, the end framing (canvas uv rectangle), overscan geometry.
- Final 192 spp threshold 0.01 (as v1). Cost cap **0.45 GPU-h** (+ the overscan still).

## 3. S05 `s05_finale` — "Every scene" (180 f)
Start from a copy of `shots/s05_title.py`. Keep the title part identical: letters (geometry, materials, colours,
`TITLE_W`, `TITLE_Y`), cove floor/wall, FaceKey / Fill / WallWash / GlossStrip / Shine, the four story lights,
halos, the bloom parameters (G1), exposure −0.2, the end camera `CAM_END (0,−9,2.15)` → `TGT_END (0,0.40,0.57)`,
50 mm, and v1's title timeline shifted by **+60 frames** (v1 f1–120 → v2 f61–180):
split f68 · letters land 76, 80, 84, 87, 91, 95, 99, 102, 106, 110 · converge f113–121 · **fuse f121** · swap f131 ·
breaths f136/f166 · shine f144–158 · hold to f180, 1 % push during the hold.
v1's f1–34 orb pull-back is replaced by the honeycomb pull-back below.

### 3.1 The honeycomb wall (replaces v1's 10-tile band)
- Flat-top hexagons (as v1), candy bezels (glossy, rounded, palette colours; dopamine but calm enough behind a
  title), lavender grout/wall, screens recessed slightly behind the bezel lip so the wall reads tactile with
  parallax. Mounted on (or just in front of) the cove wall at y ≈ 2.8–3.0.
- Size and layout are yours to tune, under these constraints:
  - **Final frames (f121–180):** honeycomb in the upper part only; its lowest screen edge ≤ 400 px from the top
    (≥ 100 px of plain lavender above the letter tops), ≥ 2 rows visible, extends past the top and both sides
    of the frame (an endless wall). The centre (painting) tile is fully visible, horizontally near the centre.
  - **The "many scenes" moment (≈ f40–60):** ≥ 15 tiles fully visible and tiles cover ≥ 70 % of the frame.
  - Tile size on screen at the end ≈ 160–260 px wide (v1's were ≈ 200 px).
- **Every cell plays a scene.** No blank tiles. Content library from `renders/hex_tiles/` (§4). Rules: the six
  chapter tiles sit in ring 1 around the centre (seen big early); no source appears twice in adjacent cells;
  repeats use different frame offsets; spread the twelve minis so colours alternate.
- **Ripple accent:** as each ring enters the frame, its bezels POP (scale ≤ 1.06, POP spring) on 8th notes;
  ripples stop by f61 so the title section is calm.

### 3.2 The pull-back camera (f1–≈75)
- **f1 = S04 f180.** The camera is perpendicular to the centre tile's screen, centred, at the distance where the
  screen hexagon exactly circumscribes the frame (screen hex width on screen = 2544 px; for 50 mm / 36 mm
  sensor d0 = 2.096 · R_screen). Scale it ≈ 1.01 so no bezel pixel touches the frame corners at f1.
  The centre screen shows `renders/hex_tiles/c_painting/still.png` (the S04 overscan, 2544 × 2204), so f1 is the
  S04 f180 picture. **Seam QA:** |S05 f1 − S04 f180| mean ≤ 1/255 (1 px blur), p99 ≤ 4/255.
- f1 → ≈ f75: one continuous move (log-distance on the distance to the centre tile; ease-in from rest at f1; no
  stop in the middle; the camera arrives on the v1 end framing with SETTLE ≈ f70–80). Rise and tilt down so the
  centre tile's screen position moves smoothly and monotonically from the frame centre to its final place.
  The honeycomb fills the frame around f40–60, then the stage and cove come up from the bottom.
- DOF: focus on the centre screen until ≈ f40, then racks to the title plane by ≈ f75; f/4 (v1 end value).
  Motion blur on (0.5 shutter); keep the pull-back speed such that tile content stays legible (no smeared mess).
- Nothing may enter the frame early: letters drop only from f76 (DROP_Z 2.8 m above the floor, out of view).

### 3.3 Screens show the true scene colours
- A tile screen must display its source pixels as they look in their own shot. The view transform is
  PBR Neutral with exposure −0.2, so the screen emission must be the **inverse** of that transform applied to the
  sRGB source (sRGB → linear → inverse Khronos PBR Neutral → × 2^0.2). Implement it (shader node group or
  pre-computed half-float EXR) and **prove it**: render a calibration chart (grey ramp + palette swatches + a real
  frame) on a frame-filling screen and compare with the source: mean |Δ| ≤ 1/255, p99 ≤ 4/255.
- Screens are emission-only for camera rays at f1 (no coat reflection, so the seam matches); a subtle coat may
  ramp in later. Screens light their bezels a little (that is fine and tactile).
- **Gain:** 1.0 through f60, eases to 0.75 ± 0.1 by f90 so the title is the hero (critic tunes).
- **Bloom is driven only by the light orbs** (use a Shader AOV written by the halo materials, not the Emit pass).
  No tile pixel may bloom.
- Guard: refuse to write `renders/final/s05_finale` unless `renders/hex_tiles/manifest.json` says every tile
  (and the centre still) is from a final (`S05F_ALLOW_NONFINAL=1` overrides, for tests only).

### 3.4 The key light (white orb) and the title
- Preferred: the white orb is born from the painting tile at f46 (it swells out of the girl's white dress, a nod
  to v1's painted dot), glides to O = (0, 2.0, 0.92) and arrives on f61 with zero speed (visible orbs ≤ 10 cm/f;
  ease); then everything follows v1 shifted by +60. Fallback: it drops in from above to O by f61.
- **"Title unchanged" QA:** v2 f121–180 vs v1 `s05_title` f61–120 (same mode/resolution): letter bounding boxes
  within ±2 px; mean |Δ| ≤ 3/255 below the honeycomb (y > 420 px). Differences come only from the new wall.
- Final 384 spp, threshold 0.02 (as v1). Cost cap **0.7 GPU-h**.

## 4. Hex-tile content library (`scripts/make_hex_tiles.py`)
Contract shared by the finale, the tile scenes and the post tools:
- Output `renders/hex_tiles/<tile_id>/h_0001.png … h_0180.png`: **1152 × 998**, 16-bit sRGB PNG, flat-top hexagon
  inscribed in the image (vertices at the midpoints of the left and right edges, flat edges along top and bottom).
  Frame k is what the tile shows on finale frame k (loops and holds already resolved).
- Centre: `renders/hex_tiles/c_painting/still.png` (2544 × 2204, copied from `renders/<mode>/s04_subject/overscan.png`).
- `renders/hex_tiles/manifest.json`:
  `{"version": 2, "res": [1152, 998], "frames": 180, "tiles": [{"id", "kind": "chapter|mini", "source":
  "final|preview|placeholder", "from", "frames_src", "loop", "crop", "palette", "label"}], "center": {"id":
  "c_painting", "path", "res": [2544, 2204], "source"}}`.
- Source priority per tile: `renders/final/<src>` (every needed frame complete) → `renders/preview/<src>`
  (Lanczos ×2) → labelled placeholder in the tile's palette colour with a running frame counter.
  Never mix sources inside one tile. Atomic directory swaps. `--require-final` exits non-zero unless every tile
  and the centre are final. `--only id,id`.
- Chapter tiles (from finals; crop a 1247 × 1080 flat-top-hex window from the 1920 × 1080 frame, centre chosen per
  tile by looking at the content, then Lanczos to 1152 × 998):

  | id | source | frames | note |
  |---|---|---|---|
  | `c_s01_night` | `s01_lights_world` | f31–120 | the orb and the three coloured lights (dark tile — one is enough) |
  | `c_s01_day` | `s01_lights_world` | f121–240 | env-map clicks |
  | `c_s02_wide` | `s02_caustics` | f1–60 + f121–180 | caustic drop-ins |
  | `c_s02_macro` | `s02_caustics` | f61–120 | the 75 mm macro |
  | `c_s03_gummy` | `s03_gummy` | f1–180 | slow-mo squash |
  | `c_s04_gallery` | `s04_subject` | f11–30 (+ hold) | the candy gallery wide |

  Windows shorter than 180 frames loop with a 6-frame cross-fade or ping-pong — your choice per tile, recorded.
- Mini tiles: `t_<name>` from `renders/<mode>/t_<name>/f_####.png` (already 1152 × 998 in final), looped per their
  meta `loop` value.

## 5. Mini scenes (twelve new tile scenes, `shots/t_<name>.py`)
Each is a tiny "candy diorama" that proves one rendering phenomenon at a glance, readable at 200 px:
one bold hero, centred, large (≈ 55–65 % of the hex height), clear silhouette against a pastel background of its
own colour, contact shadows, tactile candy materials, soft studio light plus the featured effect.
- Resolution **1152 × 998 final** (`D.setup_output(res=(1152, 998))`; preview 50 % = 576 × 499), flat-top hex
  safe area: keep everything important inside the hexagon (corners are cropped by the screen).
- 180 frames at 30 fps, or a seamless loop of 60 or 90 frames (declare `loop` in the meta; frame loop+1 must equal
  frame 1). Static seed, baked animation, PBR Neutral, exposure −0.2 ± 0.3.
- Script CLI as every shot (`--mode draft|preview|final --frames`), outputs `renders/<mode>/t_<name>/f_####.png`,
  meta `renders/meta/t_<name>.json` (`frames`, `loop`, `res`, `bg`, `hero`, `phenomenon`, measured s/f),
  sheet `renders/review/t_<name>_sheet.png`.
- Cost cap per scene: **≤ 0.12 GPU-h final** (measured; choose loops and samples accordingly).
- No new downloads: local assets (`assets/models`, `assets/textures`, `assets/hdri`) and procedural geometry only.

| group | id | hero and effect | background |
|---|---|---|---|
| T1 reflect & refract | `t_chrome_cow` | mirror-chrome Spot cow on a pink turntable; env map swirls in the reflections | blush / pink |
| | `t_glass_armadillo` | aqua tinted-glass armadillo, one small spot → crisp refractive caustics on the floor, slow turn | butter |
| | `t_disco` | mirror-tile disco ball turning under one spot; light flecks sweep the cove | lilac |
| | `t_magnifier` | `magnifying_glass_01` gliding over jacquard fabric; the lens magnifies the weave | sky |
| T2 light & material | `t_desk_lamp` | `desk_lamp_arm_01` nodding; its spot pool and hard shadows sweep a marble desk with candy props | mint |
| | `t_lightbulb` | `lightbulb_01` with a glowing filament swinging on its cord; warm light through glass, moving shadows | peach |
| | `t_fruit_sss` | kiwi and lime halves, backlit → translucent subsurface glow; slow turn | blush-coral |
| | `t_material_balls` | five spheres on a turntable: velvet, gold, marble, glass, iridescent | lemon |
| T3 motion & world | `t_jelly_cubes` | three jelly cubes drop and squash (volume-preserving) in turn | pistachio |
| | `t_duck_pool` | `rubber_duck_toy` bobbing on rippling water; caustics dance on the pool tiles | aqua / cream |
| | `t_sunset_bunny` | gold Stanford bunny on a candy pedestal, sunset HDRI rotating 90° → glints and shadows move | coral sunset |
| | `t_toy_town` | candy toy town (rounded houses, cone trees); the sun sweeps morning → evening, long shadows rotate | sky / lavender |

## 6. Post tools (v1 behaviour stays the default)
- `docs/shots_v2.json` (S01–S03 entries as v1; `s04_subject`, `s05_finale` new).
- `--film v2` for `scripts/assemble.py`, `make_overlays.py`, `qa_finals.py`, `render_finals.py`.
  v2 intermediates: `renders/film_v2`, `renders/film_comp_v2`, `renders/film_comp_clean_v2`,
  `renders/overlays_v2`. v2 outputs in `out/v2/`: `LaRenderer_opening_v2.mp4`, `LaRenderer_opening_v2_clean.mp4`,
  `LaRenderer_opening_v2_master.mov`, `LaRenderer_opening_v2_clean_master.mov`, `cuts.png`, `overview_1fps.png`,
  `assembly.json`; previews in `out/v2/preview/`. Cut pairs come from the shots table.
- Overlays v2: S01–S03 as v1. S04 pill "High-res textures" from f616, zoom chip from `s04_subject` meta
  (×1.0 → about ×7, no "texel / px" chip), out by f776 (frames 779–780 clean). No overlays in the finale.
- `render_finals.py --film v2` order: the twelve `t_*` scenes and `s04_subject` (+ the overscan still job) →
  `make_hex_tiles.py --require-final` → `s05_finale`. S01–S03 reuse v1 finals (nothing to render).
- `qa_finals.py --film v2`: v1 checks plus `s04-subject-hold` (f150–180 static), `seam` (S04 f180 vs S05 f1),
  `title-unchanged` (§3.4), tile completeness (manifest all final).
- README: a v2 section in Chinese.

## 7. Rules for every agent
- GPU: only `CUDA_VISIBLE_DEVICES=6` or `7` (dopa refuses anything else). One Blender render process per agent at
  a time; keep tests short (draft/preview, sparse frames). Other people's jobs run on the other GPUs.
- Never modify: v1 shot scripts, `lib/dopa.py`, `docs/storyboard.md`, `versions/`, `renders/final/<v1 ids>`,
  any v1 file in `out/`. Read them freely.
- No downloads and no attempts to get around any server's access limits.
- Each agent owns only the files listed for it; write a report JSON to `docs/reports/<id>_build_v2.json`.
