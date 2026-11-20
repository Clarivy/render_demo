# LaRenderer: Opening Animation Storyboard (FINAL)

Status: **locked for build**. This document replaces concepts A–D. Machine-readable shot list: `docs/shots.json`.
Read `docs/brief.md` first. Every number here is a starting value that an engineer may tune only within the
stated target ("tune until X reads Y"). Everything else is a spec.

> **Lead decisions (2026-11-20). These override the text below where they conflict.**
> 1. `scripts/make_candy_sky.py` is **done and calibrated** by the lead. Its outputs are `assets/hdri/candy_sky_4k.hdr`,
>    `candy_sky_nosun_4k.hdr` and `candy_sky_preview.png`. A top-view render confirmed the convention: mapping rotation
>    z = −θ turns the env +θ CCW; at θ=0 the gnomon shadow points to azimuth 315°, at θ=90° to 45°. **Do not
>    regenerate it.** The preview PNG now uses a hue-preserving shoulder instead of x/(1+x), which greyed the pastels.
> 2. **Fixed:** shot lengths, hit frames on the beat grid (§2.7), transition specs (§2.6), capability proofs, the
>    colour pipeline and determinism.
> 3. **Tunable by builders:** any visual parameter, wherever it makes the frame more refined ("精致") or the claim
>    more readable. Log each deviation in the script header.
> 4. **The slug is off by default** (`--slug` turns it on). Deliverables are a captioned film and a clean film
>    (no overlays), each as an H.264 review MP4 and a ProRes 10-bit master.
> 5. **GPU guard.** `D.enable_gpu()` aborts unless `CUDA_VISIBLE_DEVICES` lists only 6 and/or 7, and
>    `render_split.sh` refuses any other GPU.
> 6. **Round 2 sign-offs.**
>    - **S01 glide reversed.** θ now goes 360 → 315 over f196–225 (it was 360 → 405) and the tilt is about
>      world X (it was Y), so the last beats land on the violet tick, in clear view instead of behind the
>      bunny. Section 7's QA expectation at f225 becomes 270°.
>    - **S05 S01 tile.** It now plays S01 f121–240 (the env clicks) instead of f1–120.
>    - **Lead notes and reports.** Round-2 lead notes are in `docs/lead_notes_r2.md`; per-shot reports are in
>      `docs/reports/`.

**Base concept: C, "Candy-Coated Proofs".** It ranked first with the clarity judge (48/60) and the feasibility
judge (35/50), and it has the best combined score (C 123, B 121, A 109, D 100.5). It is also the only concept whose
shots are fully independent scripts with cuts matched in 2D. Its weak spots were a lab-like look, an MNEE-only
caustic plan, strobing env background and a plain finale. These are fixed with grafts from B, A and D (§1).

---

## 0. At a glance

**Logline.** One white light runs four candy-coloured tests that graphics people already trust, then becomes the
light that reveals the name.
1. The light pops on in the dark and splits into three palette lights whose shadows paint lemon, aqua and violet.
2. It flies up to become the sun of a candy sky that clicks a full turn under a locked camera.
3. It drops into a mint jewel-box, where glass candies land on the beat and bloom tinted and rainbow caustics.
4. A dive into a mirror ball hands off to a lime gummy bunny that squashes in 0.2× slow motion over stripes and
   mirrors.
5. A whip-pan lands in a lemon gallery for one unbroken 46× push into a 20 000-px Seurat. There, a painted white
   dot pops out and glows.
6. The dot becomes the orb. It splits, lands ten candy letters and fuses into one white key over **LaRenderer**,
   under a honeycomb of all four chapters still playing.

**Length:** 30.0 s = **900 frames** at 30 fps = **15 bars** at 120 BPM. Output is 1920×1080, 16-bit PNG.

| # | id / script | Global frames | Bars | Time (s) | Capability | Final spp | est s/f | GPU-h |
|---|---|---|---|---|---|---|---|---|
| S01 | `s01_lights_world` / `shots/s01_lights_world.py` | 1–240 | 1–4 | 0.0–8.0 | C1 point lights (moving, added) + env map, any rotation | 384 | 9 | 0.60 |
| S02 | `s02_caustics` / `shots/s02_caustics.py` | 241–420 | 5–7 | 8.0–14.0 | C2 caustics (tinted + rainbow), glass, chrome inter-reflection | 2048 | 30 | 1.50 |
| S03 | `s03_gummy` / `shots/s03_gummy.py` | 421–600 | 8–10 | 14.0–20.0 | C3 animated, deforming geometry, frame-to-frame continuity | 512 | 20 | 1.00 |
| S04 | `s04_every_dot` / `shots/s04_every_dot.py` | 601–780 | 11–13 | 20.0–26.0 | C4 high-res textures (room-wide to ≈1 texel/px) | 256 | 8 | 0.42 |
| S05 | `s05_title` / `shots/s05_title.py` | 781–900 | 14–15 | 26.0–30.0 | Title + recap (teaser honeycomb, light split resolves) | 384 | 11 | 0.37 |
| | | | | | | | **Total** | **≈3.9** |

The budget is ≤6 GPU-h. Finals take ≈3.9 GPU-h; adding the S02 gate and one full preview pass brings the plan to
≈4.45 GPU-h, leaving a **≈1.55 GPU-h reserve** for one partial re-render (§6). Use only GPU 6 and GPU 7
(`CUDA_VISIBLE_DEVICES=6` or `=7`, or `scripts/render_split.sh … "6,7"`).

---

## 1. Decisions: what was kept, grafted and rejected

**Kept from C:**
- the closed-form test patterns;
- the locked cameras for C1 env and C3;
- the sundial hue-wheel island and the chrome probe;
- the Stanford bunny as the test subject in four materials (clay → crystal → gummy → plush);
- the 0.2× slow-mo gummy with lattice squash and a live frame counter;
- the log-space push into the Seurat, with Linear interpolation, a square-on f/11 end and a sub-pixel drift hold;
- the painted dot that becomes the light;
- overlays drawn in Pillow (no GPU cost) and composited in post;
- fixed seed with frame-difference QA;
- captions that name capabilities only.

**Grafted:**
| From | Idea | Where |
|---|---|---|
| B | Palette light split: coral/lime/blue at 0.49/1.05/0.94 of the white power. Verified sum = (1.001, 1.000, 1.005); single-light shadows land on lemon-yellow, aqua and violet. | S01, S05 |
| B | Env rotation as beat-quantised 90° "clicks" with a detent overshoot. A 4th click returns to θ=360°, which must reproduce θ=0 exactly. | S01 |
| B | Glass casters drop in on the beat and bloom their caustics on landing. The key light sits behind and above them so caustics spill toward the lens. One bar is a floor-skimming 85 mm caustic macro. | S02 |
| B | Colour-blocking per chapter (one saturated block + one pastel partner). The chapter colour is used on the pill dot and the finale tile rim. | all |
| B | Finale light resolution: three coloured lights fuse into one white key and every coloured fringe collapses into one crisp shadow. | S05 |
| B | Cue-sheet discipline: a visible event on every beat, and every hit carried by a spring or squash. | all |
| A + D | Sky globe on a gold stand with a pink crank. It is textured with the same env map and turns with it. | S01 |
| A | Light-sizing rule for path-traced caustics: a small light (r 0.05) within 1.5 m of every caster. | S02 |
| A | "One sky": the same generated candy sky shows in every chrome reflection of the film. | S01–S04 |
| A | Gold cone (teaser nod) and spring-overshoot settles on camera arrivals. | S02, all |
| D + B | Honeycomb of hex tiles, each playing its chapter via `D.mat_video` (the teaser grid come alive) at almost no render cost. | S05 |
| Brief §6 | Plain path tracing for caustics: no MNEE, dispersive crystal bunny, absorbing tinted glass, the caus_pop jewel-box rules. | S02 |

**Rejected:**
| Rejected idea | Reason |
|---|---|
| MNEE (B, C) | 5× slower for no gain (brief §6). |
| Env map visible as the camera background (C) | Cycles does not motion-blur world rotation, so it would strobe. |
| Pure RGB primaries (C) | Off-palette; they wash out under PBR Neutral. |
| Lens bench (C) | Reads as a laser dot. |
| CMY "registration echo" as the end frame (C) | Reads as an RGB-split glitch. |
| A's one-take Playhouse, shared set module and whole-world finale | Couples the builders; +1.4 GPU-h. |
| Bullet-time / onion-skin ghosts (A, D) | Reads as compositing. |
| Spark hopping along the letters (A) | Echoes the Pixar-lamp logo. |
| B's Cycles HUD, confetti, chrome sweep and syllable split | Clutter; splitting the word mis-parses the name. |
| Magnifier push (B, D) | Optical zoom muddies the texture claim. |
| Procedural canvas-weave bump (B) | Adds detail that is not in the 20K scan. |
| Sphere→torus morph (D) | Changes topology, so no deformation blur and the surface shimmers. |
| Caustics on the title (D) | Puts noise on the title. |

---

## 2. Global style rules

### 2.1 Palette per shot
Grounds are pastel or dark; heroes are saturated. Every shot has one saturated block plus one pastel partner.
All names are `D.PALETTE` keys.

| Shot | Ground (walls / floor / bg) | Saturated block | Heroes | Chapter colour (pill dot, finale tile rim) |
|---|---|---|---|---|
| S01 A (night) | `ink` bg, `offwhite` plate | `blue` cake | lights `coral` / `lime` / `blue`; shadows land lemon-yellow / aqua / violet | `blue` |
| S01 B (day) | `sky` bg, `offwhite` plate | `blue` cake | 8 hue ticks `pink orange lemon lime mint aqua blue violet`; `lemon` nodus; `pink` crank; `chrome`; `gold` | `blue` |
| S02 | `pistachio` right wall, `cream` floor, dim | `mint` left wall | glass `lemon` / `pink` / `aqua`, crystal (rainbow), `chrome`, `gold`, `coral` pedestal | `mint` |
| S03 | `blush`/`white` stripe wall, `cream` gloss floor | `coral` right wall | `lime` gummy; `chrome` ball with `pink` band; `lemon` / `aqua` / `violet` blocks; `mint` mirror rim | `coral` |
| S04 | `butter` right wall, `peach`-tinted wood | `lemon` left wall | `orange` and `aqua` frames, teal teddy plaid, `mint` table, `pink` rug and bowl, `lilac` plush bunny, Seurat's own dots | `lemon` |
| S05 | `lavender` cove | rainbow word | letters `pink coral orange lemon lime mint aqua blue violet #C454C9` | n/a |

The film walks the hue wheel: ink → sky → mint → coral/blush → lemon/butter → lavender. No two shots share a
ground. `lilac` is never used for type on lavender; the 10th letter is magenta `#C454C9`.

### 2.2 Materials
- Use dopa materials only:
  - `mat_clay` for walls, floors and matte props;
  - `mat_candy` for toys, frames, pedestals and letters;
  - `mat_metal` for chrome and gold;
  - `mat_glass` / `mat_glass_dispersive` for casters;
  - `mat_velvet` / Poly Haven plush for soft goods;
  - `mat_image` for paintings;
  - `mat_video` for the finale tiles.
- Exactly six small custom node setups are allowed. Each is specified in its shot section:
  1. stripes (S01 gnomon, S03 wall);
  2. globe env material (S01);
  3. light-marker halo (S01, S02, S05);
  4. fourth-wall card (S02, S03);
  5. tile screen UVs (S05);
  6. the S04 dot-orb emission mix.
- **Light-marker halo** (one definition, used everywhere): `D.sphere` + `D.mat_emission(colour, k)`.
  - Ray visibility: `visible_camera=True`, `visible_glossy=True`. `visible_diffuse`, `visible_transmission`,
    `visible_shadow` and `visible_volume_scatter` are all `False`.
  - Material emission sampling: `mat.cycles.emission_sampling = 'NONE'`.
  - The halo never lights, never blocks, and never stands in for the light behind glass.
  - The real light is a `POINT` or `SPOT` of smaller radius at the halo centre, with `camera_visible=False`.
- No AgX, no Filmic, no extra looks.

### 2.3 Light language
| Shot | Key | Fill | World | Character |
|---|---|---|---|---|
| S01 A | visible orbs: 1 → 3 → 1 POINT, r 0.03 | **none** | 0 | Night. Hard shadows; colour comes only from light mixing. |
| S01 B | the sun **inside** the env map (no lamps at all) | none | `candy_sky` 0.45 | Day. Crisp sun, coloured skylight. |
| S02 | one visible SPOT-orb, r 0.05 | sky AREA ≤10% of key | `candy_sky_nosun` 0.08 | Jewel-box: low ambient, mid-tone receiver. |
| S03 | `D.studio_rig` 850 W | rig | `candy_sky_nosun` 0.3 | Toy-commercial softbox; gentle contact shadows. |
| S04 | gallery wash AREA 650 W + `studio_rig` 500 W | rig | `candy_sky_nosun` 0.4 | Soft, even, glare-free on the canvas. |
| S05 | palette orbs → one white orb, r 0.04 | lavender AREA ≈20% | `studio_small_09` 0.3 | Stage key over the name. |

`candy_sky*` is generated once (§3.1). If the file is missing, S02–S04 fall back to `D.HDRI['colorful_studio']` at
the same strength and print a warning.

### 2.4 Motion language
- **Springs** (`D.spring(t, freq, damping)`, t in seconds):
  - `POP = (2.5, 8)`: ≈20% overshoot. Used for props, pills and halos.
  - `SETTLE = (1.6, 9)`: ≈6% overshoot. Used for every camera arrival, so no camera move ever stops dead.
  - `BOING = (2.5, 5)`: ≈35% overshoot, squash only. Used for letters and gummy.
- **Squash is volume-preserving:** `sx = sy = 1/sqrt(sz)`. Pivots sit at the contact point (object origin at its base).
- **Dollies and zooms** are interpolated in log-distance: `d = d0·(d1/d0)^e(t)`.
- **Easing:** glides use `ease_in_out_sine`; arrivals use `ease_out_cubic`; exits and launches use `ease_in_cubic`.
- **Whips** are 55° of yaw over exactly 10 frames, with cubic easing that meets at the cut at **16.5°/f** (3·55/10).
  `scene.render.motion_blur_shutter` is keyed 0.5 → 1.0 for the whip only.
- **Light speed.** Cycles motion-blurs halo meshes but not lights, so keep visible light orbs ≤10 cm/frame.
  Launches and exits are the only exception, and in those the light fades out.
- **One visible event on every beat** (15 f). Nothing appears without a spring; nothing leaves without an ease.
- **All animation is baked** with `D.bake` (per-frame, LINEAR) from closed-form functions of frame or τ, so it is
  deterministic.

### 2.5 Typography and overlays
- **Title:** 3D Fredoka Bold (`font="fredoka"`), inflated candy, built in S05. No 2D title.
- **Captions** are "sticker pills" drawn by `scripts/make_overlays.py` (Pillow) from Cycles-rendered candy sprites
  (`shots/s00_ui_sprites.py`). They are composited in post and never rendered in shots.
  - **Pill:** 60 px high, full-round ends, candy-white sprite with a baked soft shadow.
  - **Label:** Fredoka SemiBold 32 px, ink `#1C1A33`, sentence case.
  - **Chapter dot:** a 22 px candy-sphere sprite inside the pill, 14 px from its left end.
  - **Position:** lower-left, 80 px from the left and bottom edges.
- **Chips** (live instruments) are smaller pills (48 px) placed 10 px right of the pill. They use Nunito Black
  28 px, with every digit drawn centred in a **fixed-width cell** (cell = widest of 0–9) so counters never jitter.
- **Timing:** pop-in is a POP spring on scale, 0 → 1.08 → 1 over 8 f, anchored at the pill's left end. Pop-out
  takes 5 f (scale → 0, `ease_in_cubic`) and finishes **≥2 frames before** the shot cut.
- **Text rules:** captions name capabilities only. No numbers about speed or quality, no comparisons, no
  architecture words. One pill plus at most one instrument per chapter.

### 2.6 Transitions
- **Every cut is a hard cut on a bar line,** made in post (ffmpeg concat). There are no dissolves.
- Each hand-off is carried **in camera inside the outgoing and incoming shots** by a shared shape.
  Shapes are matched by on-screen size and position only; no geometry is shared between scripts.

| Cut | Global | Outgoing (last frames) | Incoming (first frames) | Match spec |
|---|---|---|---|---|
| S01→S02 | 240 → 241 (bar 5) | locked daylight island at rest | the orb falls in from frame-top into the mint room | Rhymes with S01's launch (f106–120); colour block flips sky → mint |
| S02→S03 | 420 → 421 (bar 8) | push into the mirror ball | pull-out from the rolling chrome ball | **Circle match:** ball silhouette 1536 px wide (80% of frame width), centred at (960, 540); both ball centres reflect a pastel blush "fourth wall" |
| S03→S04 | 600 → 601 (bar 11) | whip-pan **right**, 55° in 10 f (`ease_in_cubic`), shutter 1.0 | whip-in continuing **rightward**, 55° in 10 f (`ease_out_cubic`), shutter 1.0 → 0.5 | Blur match: same direction, same angular speed at the cut (16.5°/f on both sides) |
| S04→S05 | 780 → 781 (bar 14) | painted white disc pops out and glows | the glowing orb, then pull-back | **Circle match:** glowing sphere ≈468 px wide (24.4%), centred. Measure S04 f180 and match S05 f1 to ±10 px |

### 2.7 120 BPM grid (1 beat = 15 f, 1 bar = 60 f)
Bar n starts at global frame 60(n−1)+1. Beats fall at +0/+15/+30/+45. The editor's track must have its downbeat on
film frame 1.

| Bar | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Start f | 1 | 61 | 121 | 181 | 241 | 301 | 361 | 421 | 481 | 541 | 601 | 661 | 721 | 781 | 841 |
| Shot | S01 | S01 | S01 | S01 | S02 | S02 | S02 | S03 | S03 | S03 | S04 | S04 | S04 | S05 | S05 |

**Hit list (global frames):**
- **S01**
  - 16: orb pops on.
  - 61: split lands (3 lights).
  - 91: carousel complete; colours permuted.
  - 106: launch.
  - 121: day.
  - 136, 151, 166, 181: env clicks.
  - 195: θ=360 loop check.
  - 196–225: glide.
  - 226: tilt wobble.
- **S02**
  - 241: cut; orb falls.
  - 256: orb settles.
  - 271: lemon ball lands.
  - 286: heart lands.
  - 301: ring lands, cut to macro.
  - 361: back to wide.
  - 391: push into the mirror ball.
- **S03**
  - 421: cut, ball pull-out.
  - 451: gummy impact; slow-mo 451–510.
  - 516: second landing.
  - 526: bonk.
  - 591: whip.
- **S04**
  - 601: whip-in.
  - 631: push starts.
  - 706: 1:1 hold.
  - 766: dot pops.
- **S05**
  - 781: orb.
  - 788: split.
  - 796–830: letter roll.
  - 841: fuse.
  - 900: end.

### 2.8 Recurring motifs
1. **The light orb is the protagonist.**
   - S01: it pops on, splits, re-merges and launches into the sun.
   - S02: it falls in as the only caustic light.
   - S04: a painted dot pops out and becomes it.
   - S05: it splits again and fuses into the title key.
2. **The bunny is the test subject, one material per chapter:** white clay (S01), crystal dispersive glass (S02),
   lime gummy (S03), lilac velvet plush (S04).
3. **Hue wheel → hue word.** S01's dial ticks run pink → violet in hue order; S05's ten letters run the same order.
4. **Teaser rooms, candied:**
   - mint glass room with the crystal bunny on a white pedestal, chrome spiral, mirror ball and gold cone (S02,
     teaser room 3);
   - coral room (S03, room 2);
   - lemon painting room with framed paintings, chair and floor lamp (S04, rooms 1 and 4);
   - the hex mosaic itself (S05).
5. **One sky:** `candy_sky` reflects in every chrome surface of S01–S04.

### 2.9 Render and colour invariants (every shot)
- **Colour:** `D.setup_color()` with Khronos PBR Neutral, look None. Exposure: S01 −0.2, S02 −0.3, S03 −0.2,
  S04 −0.1, S05 −0.2.
- **Output:** `D.setup_output()`: 1920×1080, 16-bit PNG RGB. Previews and drafts are 8-bit (`D.finish` handles it).
- **Determinism:** Cycles seed 0, animated seed **off**. OIDN with albedo + normal, ACCURATE prefilter. Persistent data
  on (kit default).
- **Run:** `tools/blender/blender -b --factory-startup -P shots/<id>.py -- --mode draft|preview|final [--frames …]`.
  Each script ends with `D.finish(args, final_samples=…, final_threshold=…, frame_end=N, shot_name="<id>")`, so
  frames land in `renders/<mode>/<id>/f_####.png`.
- **Metadata:** each script also writes `renders/meta/<id>.json` at build time (before rendering, in every mode).
  It holds the per-frame instrument values the overlays need (S01 θ/tilt, S03 τ and speed, S04 distance, zoom and
  px/texel), so captions always match the render.
- **Independence:** no shot loads another shot's `.blend`. S05 reads other shots' rendered frames (via proxies);
  S02–S04 read the generated sky (an asset). Everything else is built from scratch with `lib/dopa.py`.
  Shot-specific helpers live inside the shot script. **Do not edit `lib/dopa.py`.**

---

## 3. Shared assets and support scripts (all Python-only)

| Script | Runs with | Produces | Owner | Needed by |
|---|---|---|---|---|
| `scripts/make_candy_sky.py` | `tools/venv/bin/python -I` | `assets/hdri/candy_sky_4k.hdr`, `assets/hdri/candy_sky_nosun_4k.hdr`, `assets/hdri/candy_sky_preview.png` | S01 engineer, **hour 1** | S01 (required); S02–S04 (optional, fallback `colorful_studio`); overlays |
| `shots/s00_ui_sprites.py` | Blender, still frames | `assets/ui/pill.png`, `assets/ui/chip.png`, `assets/ui/dot_<colour>.png` | S05 engineer | overlays |
| `scripts/make_overlays.py` | venv Python (Pillow) | `renders/overlays/o_0001..0900.png` (RGBA) | S05 engineer | assembly |
| `scripts/make_tile_proxies.py` | venv Python (Pillow) | `renders/proxies/<id>/p_0001..0120.png` (640×360) | S05 engineer | S05 |
| `scripts/assemble.py` | venv Python (+ `tools/ffmpeg`) | `renders/film/`, `out/LaRenderer_opening_master.mov`, `out/LaRenderer_opening_review.mp4` | S05 engineer | final |
| `scripts/qa_diff.py` | venv Python (numpy, cv2) | frame-difference PNGs + mean \|Δ\| | any | QA (§7) |

### 3.1 `make_candy_sky.py`: the film's environment map (deterministic, no randomness)

**Image and convention.**
- 4096×2048 equirect, float32, written with `cv2.imwrite('….hdr', bgr)`. Radiance HDR is readable by `D.world_hdri`.
- Pixel (row r, col c): `u=(c+.5)/W`, `v=1-(r+.5)/H`.
- World azimuth (Blender, counter-clockwise from +X): `a = π − 2πu`. Elevation: `e = (v − .5)·π`.
- This is Cycles' convention: image centre = +X.

**Content.**
- **Sky (e ≥ 0):** linear(`sky`) at the horizon, blending to linear(`lavender`) at the zenith with weight
  `smoothstep(e/90°)^0.8`. A haze band mixes 50% toward linear(`cream`) over e ∈ [0°, 6°]. Radiance ×1.0.
- **Ground (e < 0):** linear(`blush`) × 0.55. The horizon is a crisp 0.4° smoothstep, so the probe and globe read
  "sky above, ground below".
- **8 candy cards** standing on the horizon:
  - centre azimuths `22.5° + 45°·k` for k = 0..7;
  - colours, in order: pink, orange, lemon, lime, mint, aqua, blue, violet;
  - half-width 14° in azimuth, e from −12° to +24°, 4° corner radius, 0.15° anti-aliased edge;
  - radiance = linear(colour) × 2.0.
- **Sun** (`candy_sky_4k.hdr` only):
  - disc of angular radius 1.2° at **a = 135°, e = 40°**, so it sits between the lemon and lime cards;
  - colour linear(`#FFF2D8`);
  - radiance solved numerically so that the disc's horizontal irradiance = **3.5×** the irradiance of everything
    else in the upper hemisphere;
  - plus an aureole: + linear(`#FFF2D8`) × 3.0 × exp(−(δ/4°)²) outside the disc, where δ = angular distance to
    the sun centre.
- `candy_sky_nosun_4k.hdr`: identical but without the sun and aureole.
- **Preview** `candy_sky_preview.png`: 2048×1024, per channel `x/(1+x)` after ×0.8, sRGB-encoded, 8-bit. It is used
  as the S01 globe texture and the S01 lat-long overlay strip.
- **Print:** sun pixel radiance, the measured E_sun/E_rest (must be 3.5 ± 0.05), and the mean sky colour.

**Calibration (S01, required once).** Render a draft of S01 f121 and f150.
- The gnomon shadow must point to azimuth **315°** at f121 (front-right) and **45°** at f150 (back-right).
- If it is mirrored, change the generator to `a = 2πu − π`, regenerate, and record the change in the script header.

---

## 4. Shots

Coordinates are in metres, Z up; the camera looks roughly along +Y. "Local" frames start at 1 in each shot.
Global = local + (start − 1).

### S01 · `s01_lights_world`: "Lights on, world turns" · C1
**Frames:** local 1–240 = global 1–240 · bars 1–4 · 0.0–8.0 s. One continuous take in one script.
Phase A (point lights) runs f1–105, the launch f106–120, phase B (env map) f121–240.

**Set dressing: a floating candy sundial island** (no room; background is camera_bg only).
| Object | dopa call | Material | Placement / scale |
|---|---|---|---|
| Plate | `D.cylinder("Plate", 1.45, 0.20, (0,0,-0.10), bevel=0.06)` | `D.mat_clay("offwhite", rough=0.6, sss=0.05, sheen=0.15)` | top at z=0 |
| Cake | `D.cylinder("Cake", 1.36, 0.26, (0,0,-0.33), bevel=0.08)` | `D.mat_candy("blue")` | under the plate |
| Hue ticks ×8 | `D.capsule(r=0.045, length=0.22)`, lying radially, centre r=1.28, z=0.045 | `D.mat_candy(c)` | azimuth (CCW from +X) → colour: 315 pink, 0 orange, 45 lemon, 90 lime, 135 mint, 180 aqua, 225 blue, 270 violet |
| Pips ×8 | `D.sphere(0.03)` at r=1.28, z=0.03, azimuths 337.5° + 45k | `D.mat_clay("white")` | between the ticks |
| Gnomon | `D.capsule("Gnomon", 0.032, 1.03, (0,0,0.515))` | candy-cane stripes: pink/white helical, `fract(14·z/1.03 + atan2(y,x)/2π) < .5`, candy params (rough 0.22, coat 1) | centre |
| Nodus | `D.sphere("Nodus", 0.10, (0,0,1.03))` | `D.mat_candy("lemon")` | top of the gnomon |
| Probe | `D.sphere("Probe", 0.32, (-0.92,-0.10,0.32))` | `D.mat_metal("chrome", rough=0.02)` | left, on the plate |
| Clay bunny | `D.stanford_bunny("BunnyClay", 0.50, location=(0.86,-0.34,0), rotation=(0,0,-21))` | `D.mat_clay("white", rough=0.5)` | right-front. The scan's long (nose–tail) axis is Blender X (footprint 1.01 × 0.78 × height), so yaw −21° makes it radial: profile to camera, narrow side to the shadow rays |
| Ring | `D.torus("Ring", 0.20, 0.07, (0.30,0.90,0.27), rotation=(90,0,15))` | `D.mat_candy("white", rough=0.18)` | back-right, upright |
| Sky globe | `D.sphere("Globe", 0.20)` centred (−0.32, 0.86, 0.56); parent empty `GlobeTilt` at the same point | **globe env material:** Texture Coordinate *Object* → Environment Texture(`candy_sky_preview.png`) → Base Color, and the same × 0.3 → Emission; coat 1.0, rough 0.25 | back-left |
| Globe stand | base `D.cylinder(0.13, 0.04, base_at_zero)`, stem `D.cylinder(0.022, 0.30)` from z 0.04, meridian `D.torus(0.235, 0.012, rotation=(90,0,30))` around the globe | `D.mat_metal("gold", rough=0.2)` | under the globe |
| Crank | arm `D.capsule(0.015, 0.12)` horizontal on the globe's top pole + knob `D.sphere(0.03)` | `D.mat_candy("pink")` | parented to the globe, so it turns with it |

**Layout rule.** At its four click positions and the glide end, the gnomon shadow points along azimuths 315°, 45°,
135°, 225° and 0°.
- No object may lie within 0.35 m of those five shadow rays.
- Nothing may stand between the camera and the gnomon base.
- The layout above satisfies both. Verify in one top-view draft and nudge by ≤10 cm if needed.

**Lighting.**
- **Phase A** (no world light: strength 0; camera_bg `ink`).
  - **White orb W:** `D.light("POINT","OrbW", radius=0.03, power 0→150 W over f16–19, color="white")` plus a halo
    r 0.065, `mat_emission("white", 4)`.
  - **Split lights**, each a POINT r 0.03 with a halo r 0.065, `mat_emission(colour, 2.0)`:
    - **C** coral 73.5 W;
    - **L** lime 157.5 W;
    - **B** blue 141 W.
  - These are 150 W × 0.49 / 1.05 / 0.94; they sum to neutral white.
  - **No fill.**
- **Phase B** (no lamps):
  - `rig = D.world_hdri("assets/hdri/candy_sky_4k.hdr", strength=0.0, camera_bg="ink", glossy_sees_bg=False)`.
  - `world.cycles.sampling_method='MANUAL'`, `world.cycles.sample_map_resolution=4096`.
  - World strength keyed 0 → **0.45** over f106–121 (`ease_out_cubic`). Tune until the sunlit plate reads ≈0.88 on
    display.
  - `rig.cam_bg` colour keyed `ink` → `sky` over f106–121 (`smoothstep`).
  - Mapping rotation = **(0, −φ(f), −θ(f))** in radians.
  - Globe: `GlobeTilt.rotation_euler.y = +φ(f)` and `Globe.rotation_euler.z = +θ(f)`.

**θ(f) and φ(f), in degrees.** The same functions go into `renders/meta/s01_lights_world.json`.
- θ = 0 for f ≤ 135.
- **Clicks.** For k = 0..3, f_k = 136 + 15k, t = f − f_k ∈ [0, 14]:
  - c(t) = 1.028·smootherstep(t/10) for t ≤ 10;
  - c(t) = 1.028 − 0.028·smoothstep((t−10)/4) for t ≤ 14;
  - θ = 90k + 90·c.
  - This is a 2.5° detent overshoot. θ(195) = 360 exactly.
- **Glide:** θ = 360 + 45·ease_in_out_sine((f−196)/29) for f196–225; then θ = 405.
- **Tilt:** φ = 6·e^(−3t)·sin(2π·2t) with t = (f−226)/30 for f226–240; 0 before.
- Shadow azimuth = 315° + θ, so it lands on pink (θ=0), lemon (90), mint (180), blue (270), pink (360), then orange
  (405).
- At θ=405 the sun is camera-left (azimuth 180°), so tilting about world Y changes its elevation by ±4°.

**Camera.**
- 45 mm, sensor 36, f/4, focus empty at (0, 0, 0.3).
- f1 (0, −6.60, 2.85) → f105 (0, −6.30, 2.75), `ease_in_out_sine`; target (0, 0.10, 0.55).
- **f106–240 locked** (mandatory: all change must read as the env rotating).
- The plate fills the lower ≈45% of the frame. Orbs at z ≤ 1.95 stay in frame.

**Beats (local = global).**
- **f1–15:** ink void. The island is a black silhouette on indigo.
- **f16 (beat 2):** W pops on at (−0.40, −0.45, 1.75): halo scale POP 0 → 1.15 → 1 over 8 f, power ramps in 3 f.
  Crisp black shadows appear; the probe shows one highlight.
- **f16–40:** W glides to (0.40, −0.45, 1.75) on a shallow arc (+0.08 m at mid), `ease_in_out_sine`. The gnomon
  shadow swings like a pendulum across the back of the dial; the ring's shadow slides.
- **f41–50:** W eases to S = (0, −0.25, 1.80). The halo anticipates over f46–50 (z 0.8, xy 1.12).
- **f51–61:** split. W off; C, L and B appear at S and spring (`ease_out_back`, 10 f) to:
  - coral (0, −0.75, 1.75), azimuth 270°;
  - lime (0.693, 0.45, 1.90), azimuth 30°;
  - blue (−0.693, 0.45, 1.80), azimuth 150°.
  - All are on a circle of r 0.80 around (0, 0.05).
- **f61 (bar 2):** split lands. Shadows are three-colour:
  - lime + blue → aqua where coral is blocked;
  - coral + blue → violet where lime is blocked;
  - coral + lime → lemon-yellow where blue is blocked;
  - black only where all three are blocked.
  - The ring throws Venn rings; the probe shows three coloured orbs.
- **f61–90:** carousel. The triangle rotates +120° about the vertical axis through (0, 0.05)
  (`ease_in_out_sine`). Each light keeps its height.
- **f91:** the geometry equals f61 with the colours permuted. This is a closed-form check.
- **f91–101:** C, L and B converge to S (`ease_in_out_cubic`) and shadows re-merge to black.
- **f99–103:** halos cross-fade by scale: coloured → 0, white → 1.
- **f101:** C/L/B off and W on at 150 W, co-located, so the swap is invisible.
- **f106–120:** launch. W accelerates along (−0.5417, 0.5417, 0.6428), toward the sun direction: distance
  `ease_in_cubic` 0 → 4 m, power 150 → 0 over f110–120. The world blooms and the background turns ink → sky. The
  sun's shadow appears pointing where the orb's last shadow pointed (315°).
- **f121 (bar 3):** day. Pills pop.
- **f136 / 151 / 166 / 181:** clicks of +90°. Shadows, probe reflection, the globe with its crank, and the coloured
  irradiance on the white bunny all jump a quarter turn together and settle with the detent.
- The tick under the shadow pops at f_k+10 with a 4-frame bump: scale = 1 + 0.15·sin(π·(f−f_k−10)/4). It ends
  exactly at 1.
- **f195:** θ=360. This frame must equal f135 (QA §7).
- **f196–225:** glide +45°; the shadow sweeps continuously to the orange tick, which pops at f225–229.
- **f226–240:** tilt wobble. Shadow length breathes (sun elevation 40 ± 4°) and settles.

**On-screen text** (overlay, global frames):
- **Pill "Point lights"** (blue dot), f20–104.
  - Chip: one white candy dot; at f61 it becomes three dots (coral, lime, blue), popping 2 f apart.
- **Pill "Environment maps · any rotation"** (blue dot), f121–238.
  - Chip `θ 0°`, live `round(θ)` each frame. During f226–238 it shows `θ 405° · tilt ±4°`.
- **Lat-long strip**, top-right, f121–238:
  - 384×192 px, 80 px margins, 18 px corner radius, 6 px candy-white border;
  - shows `candy_sky_preview.png` re-projected every frame with the same rotation (yaw and tilt) as the world;
  - centred on the camera's view azimuth (90°), with azimuth increasing to the left;
  - a fixed mint ▼ playhead at the centre.

**Transition.** In: film start (hard). Out: hard cut at 240|241 (bar 5) from the locked daylight frame (§2.6).

**Capability proof.**
- **Point lights:** every light is visible as an orb, and the probe shows each at its true position, so every
  shadow traces to its source. The neutral-sum split is closed-form:
  - wherever all three lights reach must stay white;
  - wherever exactly one light is blocked must show its complement, which lands on palette hues;
  - only the triple-occluded core may go black.
  - The 120° carousel must reproduce the same shadow geometry with permuted colours.
  - Wrong visibility, a dropped light or an energy error shows instantly as a wrong colour.
- **Env map:** the camera is locked and there are no lamps. The input is visible three ways: the probe, the globe
  (a physical model of the map turning with it), and the lat-long strip.
  - The sundial shadow must turn by exactly θ: one tick per 90° click.
  - The probe counter-rotates.
  - The coloured skylight sweeps around the white bunny.
  - θ=360 reproduces θ=0 frame-for-frame.
  - The glide shows arbitrary angles; the tilt shows the rotation is not yaw-only.

**Samples and cost.**
- `D.setup_cycles(samples=384, threshold=0.008, min_samples=32, diffuse=4, glossy=6, transmission=4, caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)`.
- `final_samples=384, final_threshold=0.008`.
- ≈6 s/f in phase A and ≈11 s/f in phase B (the importance map is rebuilt every frame): average ≈9 s/f →
  **0.60 GPU-h**.

**Risks and mitigations.**
1. **Clicks read as strobing** (peak ≈17°/f, and Cycles does not blur world rotation). The flat camera_bg removes
   background strobing; shadows simply snap.
   - If the preview video still reads as jitter, stretch each click to 13 f, starting 2 f earlier.
   - Fallback: one continuous 360° over f121–222 at ≤3.6°/f (trapezoid profile, 12 f ramps).
2. **Coloured halos wash out to white** under PBR Neutral. Keep coloured halo emission at 2.0 (white at 4.0).
   Check in preview that the orbs read coral, lime and blue.
3. **Split shadows muddy.** Check the three single-occlusion colours in a preview crop. If they are weak, lower the
   light heights by 0.1 m or widen the circle to r 0.9.
4. **Mapping sign or zero wrong.** Run the §3.1 calibration once, before any preview.
5. **Noise in dark penumbrae** (phase A). min 32, clamp 10, adaptive 0.008.
6. **Light vs halo motion blur.** Keep speeds within §2.4; the launch is allowed because the light fades out.

---

### S02 · `s02_caustics`: "Jewel-box" · C2
**Frames:** local 1–180 = global 241–420 · bars 5–7 · 8.0–14.0 s.
Cameras: wide W at f1–60 and f121–180, macro M at f61–120.

**Set dressing.** A teaser room-3 remix. The room is
`D.diorama_corner("Room", size=3.4, height=2.4, floor_mat=D.mat_clay("cream", rough=0.6, sss=0.0, sheen=0.05), left_mat=D.mat_clay("mint"), right_mat=D.mat_clay("pistachio"), rot_z=45)`.
Its back corner is at (0, 2.40) and its open front corner at (0, −2.40).

| Object | dopa call | Material | Placement |
|---|---|---|---|
| Crystal bunny | `D.stanford_bunny("CrystalBunny", 0.48, location=(-0.70,0.45,0.14), rotation=(0,0,20))` | `D.mat_glass_dispersive("white", spread=0.03)` | on the plinth |
| Plinth | `D.cylinder("Plinth", 0.30, 0.14, (-0.70,0.45,0), base_at_zero=True, bevel=0.03)` | `D.mat_candy("white", rough=0.3)` | low wide plinth (teaser "white pedestal") |
| Lemon ball (drop-in) | `D.sphere("LemonBall", 0.13)` | `D.mat_glass("lemon", absorb=2.0)` | lands at (−0.25, −0.10, 0.13) |
| Pink heart (drop-in) | helper `heart_mesh(height=0.26)`: parametric heart x=16sin³t, y=13cos t−5cos2t−2cos3t−cos4t, 64-pt closed poly curve, scaled to 0.26 m tall, `fill_mode='BOTH'`, extrude 0.035, bevel_depth 0.035, bevel_res 6, converted to mesh + Subsurf 1 applied, smooth | `D.mat_glass("pink", absorb=2.0)` | stands upright facing the camera (tilted back 10°), tip in a stand at (0.05, 0.05) |
| Heart stand | `D.cylinder("HeartStand", 0.06, 0.05, (0.05,0.05,0), base_at_zero=True)` | `D.mat_candy("white")` | heart tip at z 0.05 |
| Aqua ring (drop-in) | `D.torus("AquaRing", 0.15, 0.05)` | `D.mat_glass("aqua", absorb=2.0)` | lands flat at (0.33, −0.28, 0.05) |
| Chrome swirl | helper: Archimedean spiral r 0.03 → 0.30, 6.5 turns, dome 0.04·(1−(r/0.30)²) toward the camera, curve `bevel_depth=0.014`, bevel_res 6, caps on → mesh | `D.mat_metal("chrome", rough=0.03)` | plane vertical facing −Y, centre (0.72, 1.05, 0.76); turns 0 → 90° about its normal over f1–180 (linear) |
| Swirl stick + pedestal | stick `D.cylinder(0.012, 0.06)`; pedestal `D.cylinder("SwirlPed", 0.12, 0.42, (0.72,1.05,0), base_at_zero=True)` | gold rough 0.2; `D.mat_candy("white", rough=0.3)` | back-right |
| Mirror ball | `D.sphere("MirrorBall", 0.20, (1.00,-0.40,0.50))` | `D.mat_metal("chrome", rough=0.0)` | front-right |
| Mirror-ball pedestal | `D.cylinder("MBPed", 0.13, 0.30, (1.00,-0.40,0), base_at_zero=True)` | `D.mat_candy("coral")` (S03's chapter colour) | |
| Gold cone | `D.cone("GoldCone", 0.11, 0.28, (-1.05,1.00,0.14))` | `D.mat_metal("gold", rough=0.12)` | back-left (teaser nod) |
| Fourth-wall card | `D.rounded_box("FourthWall", (7.0,0.1,3.5), 0.05, location=(0,-7.5,1.5))` | `D.mat_emission("blush", 0.35)` | visible only to glossy and transmission rays (camera, diffuse and shadow off) |

All casters (orb home O = (0, 0.85, 0.95)) are within **1.0–1.5 m** of the light. That is ≈17× the calibration
light's solid angle, so path-traced caustics converge and stay sharp.

**Lighting.**
- **Key = the orb:**
  - `D.light("SPOT","Orb", location=O, target=None, power=250, color="#FFF6E8", radius=0.05, spot_deg=120, blend=0.25)`.
  - A TRACK_TO constraint aims it at empty `OrbAim` at (−0.15, −0.05, 0).
  - Halo r 0.07, `mat_emission("#FFF6E8", 4)`, parented to the light (flags as in §2.2).
  - Tune the power until the directly lit floor pool reads **0.55–0.70** on display and the walls read 0.25–0.35
    (dim mint).
  - The spot cone keeps the back walls in shadow: the jewel-box look of caus_pop.
- **Fill:** `D.light("AREA","Fill", (0.5,-2.6,3.2), (0,0.2,0.3), power=60, color="sky", size=3.0)`. A fill-only test
  render must read ≤0.07 on the floor pool (≤10% of the key).
- **World:** `D.world_hdri("assets/hdri/candy_sky_nosun_4k.hdr", 0.08, camera_bg="pistachio", camera_bg_strength=0.25)`.
- Scene caustics: refractive **and** reflective **on**. `is_caustics_light` stays **off** (no MNEE).

**Cameras** (two objects). Switch `scene.camera` in a `frame_change_pre` handler: W for f ≤ 60 or f ≥ 121, M
otherwise. Do not key-jump one camera: its motion blur would smear across the cut.
- **Cam W:** 40 mm, f/3.5, focus empty at (0, 0, 0.2), target (0.05, 0.30, 0.50).
  - f1 (0.25, −5.30, 2.30) → f60 (0.22, −5.05, 2.22), `ease_in_out_sine`.
  - f121 (0.22, −5.05, 2.22) → f150 (0.20, −4.85, 2.15).
  - **f151–180, push into the mirror ball:** position = ball_c + d·û, with û = normalize(cam(f150) − ball_c) and
    d = 4.81·(0.556/4.81)^ease_in_cubic(prog(f,151,180)).
  - The target moves to ball_c over f151–162. Focus moves to an empty at ball_c − 0.08·û. The f-stop goes
    3.5 → 8 over f151–180.
  - **End frame:** the ball silhouette is 1536 px wide, centred. Its middle reflects the blush card; its rim shows the
    mint room, the orb and the caustics.
- **Cam M** (floor-skimming macro): 85 mm, f/5.6, focus empty at (0.05, −0.42, 0.0).
  - Camera (0.05, −3.00, 0.24) → (0.20, −3.00, 0.24) over f61–120 (`ease_in_out_sine`); target
    (0.05, −0.42, 0.02) → (0.12, −0.42, 0.02).
  - The caustic band (y −0.25 … −0.60) lies inside the ±16 cm depth of field. **The caustics are sharp, never in
    the soft foreground.** The orb is above frame (no glare).

**Beats.** Drop-ins fall 2.6 m with toy gravity g = 12 m/s² (≈20 f) and land exactly on the beat.
- **f1–14:** the orb falls in from z 3.2 to 0.95 with its light on (`ease_in_cubic`). The pool brightens and
  shadows and caustics sweep.
- **f14–24:** the orb settles: z = 0.95 − 0.05·e^(−8u)·sin(2π·2.5u).
- **f16 (beat 2, global 256):** the orb is at rest. The crystal bunny's rainbow sparkle caustics sit sharp on the
  plinth and floor; the swirl coils reflect each other. Pill pops.
- **f11→31 (beat 3, global 271):** the lemon ball lands; restitution 0.15 gives a 6 cm hop, then it rolls 3 cm and
  stops by f45. A hot lemon focal spot blooms inside its own shadow.
- **f26→46 (beat 4, global 286):** the pink heart lands tip-first in its stand and rocks
  8°·e^(−5t)·sin(2π·2t) to rest by f62. A pink heart-shaped caustic with bright rims blooms.
- **f41→61 (bar 6, global 301; the cut lands on the impact):** the aqua ring lands flat in the macro foreground.
  Its wobble is 5°·e^(−6t)·sin(2π·3t), and a bright aqua ring caustic blooms.
- **f61–120 (macro):** the orb arcs: O(φ) = (0.85 sin φ, 0.85 cos φ, 0.95), φ 0 → 35° (`ease_in_out_sine`).
  Caustics crawl, stretch into comets and refocus; the rainbow fringes slide.
- **f121–150 (bar 7, back to wide):** φ 35° → 0 and the caustics swing back.
- **f151–180:** push into the mirror ball (beat 3, global 391), which shows the glass, orb and caustic-lit floor a
  second time.

**On-screen text:** pill **"Caustics · glass · mirrors"** (mint dot), global 256–410. No instrument.

**Transition.** In: hard cut on bar 5; the orb's fall rhymes with S01's launch. Out: circle match into S03's chrome
ball (§2.6).

**Capability proof.**
- One visible, small light is the only key, so every caustic traces back to it.
- Each caster's caustic appears the moment it lands, and is tinted by its glass:
  - a lemon focal point inside the ball's shadow;
  - a pink heart-shaped caustic;
  - an aqua ring;
  - rainbow sparkles from the dispersive crystal bunny.
- When the light moves, the caustics crawl, refocus and change shape, so they cannot be decals. Screen-space and
  G-buffer methods cannot see these specular-to-diffuse paths.
- The mirror ball and chrome swirl show chained specular transport: light → glass → floor → mirror → eye.

**Samples and cost.**
- `D.setup_cycles(samples=2048, threshold=0.01, min_samples=64, diffuse=4, glossy=8, transmission=16, caustics=True, filter_glossy=0.0, clamp_indirect=20, motion_blur=True, shutter=0.5)`.
- `final_samples=2048`; exposure −0.3.
- ≈30 s/f → **1.50 GPU-h**. This is the film's largest line item. Render it first.

**Gate (before any final frame).** Render final-mode f16, f75 and f140, plus the 12-frame strip f61–72. Play the
strip as video.
- **Pass:** crisp caustics, no fireflies, no blotch "boiling" across frames, ≤40 s/f.
- **Fallbacks, in order:**
  1. cap 3072 spp (+≈0.6 GPU-h from the reserve);
  2. light radius 0.05 → 0.08 (softer but cleaner);
  3. bunny → `D.mat_glass("white")` if rainbow fireflies flicker.

**Risks and mitigations.**
1. **Caustic noise and OIDN flicker.** The gate above, the static seed and min 64 samples.
2. **Fireflies from glossy paths through glass** (filter_glossy 0 is required for sharp caustics). clamp_indirect 20;
   if the swirl sparkles, raise its roughness to 0.05.
3. **Scan bunny glass artefacts.** `D.stanford_bunny` already fills holes. If specks appear, rotate the bunny ±30°
   to hide them; never voxel-remesh it.
4. **Dark walls around a bright orb look odd.** The spot cone is intentional (caus_pop look). If reviewers object,
   add a 12 W POINT at O, with caustics unaffected.
5. **The mirror-ball centre is dark.** The fourth-wall card fixes it. Keep the card's emission at 0.35 so it does
   not act as a fill.
6. **Falling glass streaks caustics mid-air.** Acceptable; motion blur hides it.

---

### S03 · `s03_gummy`: "0.2×" · C3
**Frames:** local 1–180 = global 421–600 · bars 8–10 · 14.0–20.0 s.

**Set dressing.** A teaser room-2 remix:
`D.diorama_corner("Room", size=3.4, height=2.4, floor_mat=D.mat_candy("cream", rough=0.12, coat=1.0, coat_rough=0.02), left_mat=<stripes>, right_mat=D.mat_clay("coral"), rot_z=45)`.

- **Stripes** (left wall, on the kit's metre box-UVs): `fract(UV.x/0.18) < 0.5` → `blush`, else `white`. These are
  9 cm vertical stripes on clay (rough 0.55, sss 0.15, sheen 0.25).

| Object | dopa call | Material | Placement |
|---|---|---|---|
| Gummy bunny | `D.stanford_bunny("Gummy", 0.75, location=(-0.15,0.40,z(f)), rotation=(0,0,-30))` + Lattice modifier | `D.mat_glass("lime", ior=1.38, rough=0.08, absorb=2.5)` (absorption-only gummy: no scatter noise; deep colour in thick parts, light ears) | action zone |
| Lattice | `bpy.data.lattices.new`: 3×3×4 points, `KEY_BSPLINE`, sized to the bunny bbox ×1.15, origin at the base | shape keys: `squash` (height ×0.55, mid ring xy ×1.25), `stretch` (height ×1.25, xy ×0.90), `lean_x` and `lean_y` (top layer +0.15 m, layer 3 +0.10, layer 2 +0.04), `ear_flop` (top layer −0.06 z, +0.05 toward the back) | parented to the gummy's location |
| Chrome ball | `D.sphere("RollBall", 0.17)` + band `D.torus(0.168, 0.022)` parented, band plane ⟂ the rolling axis | `D.mat_metal("chrome", rough=0.02)`; band `D.mat_candy("pink")` | path below |
| Wall mirror | `D.cylinder("WallMirror", 0.26, 0.03, (1.30,1.09,1.00), rotation=(90,0,45))` + rim `D.torus(0.27, 0.025)` | `D.mat_metal("chrome", rough=0.0)`; rim `D.mat_candy("mint")` | on the coral wall; yaw ±15° so the gummy sits centred in it from the locked camera (verify in draft) |
| Block stack | `D.rounded_box` 0.32³ (r 0.06), 0.26³ (rot z 20°), 0.20³ (rot z −15°), stacked | `D.mat_candy("lemon"/"aqua"/"violet")` | base at (0.85, 1.05) |
| Fourth-wall card | as in S02, at y = −7.0 | `D.mat_emission("blush", 0.35)`, glossy and transmission only | behind the camera |

**Lighting.**
- `D.studio_rig(target=(-0.1,0.4,0.4), scale=1.0, key_power=850)`.
- `D.world_hdri("assets/hdri/candy_sky_nosun_4k.hdr", 0.3, camera_bg="blush")`.
- Brute-force caustics stay **on**: the soft lime caustic under the gummy converges with the big softbox.

**Time remap τ(f), in seconds.** It drives all object animation, **never the camera**:
- τ = (f−1)/30 for f ≤ 25;
- the rate ramps linearly 1 → 0.2 over f25–31, so τ(31) = 0.92;
- the rate holds 0.2× over f31–85, so τ(85) = 1.28;
- the rate ramps 0.2 → 1 over f85–91, so τ(91) = 1.40;
- then τ = 1.40 + (f−91)/30.
- Write τ per frame to meta.

**Gummy, in τ.**
- **Fall:** the base drops from z 2.6 starting at τ0 = 0.192 with g = 9.81, and makes contact at **τc = 0.92
  (f31)**. It enters the frame top at ≈f22, and slow motion engages as it nears the floor.
- **Impact springs** (u = τ − τc):
  - d1 = 0.61·e^(−5.5u)·sin(2π·4.5u);
  - `squash` = clamp(d1/0.45, 0, 1), giving a peak height of 0.55 at u ≈ 0.056;
  - `stretch` = clamp(−d1/0.25, 0, 1), giving a peak of 1.24 at u ≈ 0.17;
  - `ear_flop` = 0.9·e^(−4u)·sin(2π·3(u−0.03)) for u ≥ 0.03 (the ears lag).
- **Lift-off** at τL = 1.03 with v = 2.634 m/s: z = v(τ−τL) − ½g(τ−τL)², peak 0.354 m. **Second landing** at
  τ2 = 1.567 (f96).
  - d2 = 0.30·e^(−6u)·sin(2π·4.5u); ears ×0.5.
  - Airborne wobble: `lean_y` = 0.25·e^(−2(τ−τL))·sin(2π·3(τ−τL)).
- **Bonk** at τb = 1.90 (f106, beat 4 of bar 9):
  - `lean_x` = −0.8·e^(−3.5u)·sin(2π·2.2u), leaning away from the ball;
  - `lean_y` = 0.3·e^(−3.5u)·sin(2π·2.2u + 0.6);
  - at rest by f165.

**Ball, in τ.**
- Constant speed (≈0.51 m/s) from A = (−1.50, −0.10, 0.17) to the contact B ≈ (−0.55, 0.10, 0.17) at τb. Adjust B
  so the ball's surface touches the gummy's left-front flank exactly at τb. The gummy footprint at h 0.75 is
  ≈0.76 × 0.59 m, long axis at −30°.
- During the slow-mo window the ball is at x ≈ −1.04 … −0.86: left foreground, mirroring the impact.
- Then it deflects toward C = (0.85, −1.05, 0.17), decelerating along s(u) ∝ 1 − e^(−2.2u), and stops by f150.
- Its path must clear the gummy's front feet by ≥3 cm (check in a top-view draft).
- **Rolling without slip:** accumulate a quaternion rotation per frame, axis = ẑ × dir, angle = Δs/0.17. During the
  slow-mo it rolls in the left foreground, mirroring the impact.

**Camera.** One camera, 50 mm, f/2.2, with the focus object as its target empty.
- **f1:** 0.59 m in front of the ball's f1 position, looking at the ball centre. The ball silhouette is 1536 px
  wide, centred (the match from S02).
- **f1–15, pull-out:** log-distance, `ease_out_cubic`, then SETTLE, to the locked pose (0.20, −4.60, 1.15). The
  target moves to (−0.05, 0.40, 0.38) and focus follows it to the gummy.
- **f16–170 LOCKED:** this is the proof window. The gummy occupies 32–68% of the frame height, in front of the
  stripes.
- **f171–180, whip right:** the target rotates −55° about the camera's vertical axis (`ease_in_cubic`). Shutter is
  keyed 0.5 → 1.0 over f171–174.

**Beats** (global in brackets).
- **f1–15 (421):** pull-out; the ball is already rolling.
- **f22–30:** the gummy drops into frame and time slows.
- **f31 (451, beat 3): IMPACT; 0.2× begins.** The body squashes and bulges and the ears whip. In lockstep with it:
  - its glossy-floor reflection, the wall-mirror image and the chrome ball's reflection;
  - its contact shadow and transmitted lime glow;
  - the refracted stripes bending through its body.
- **f50–80:** rebound stretch, lift-off and an airborne wobble with lagging ears.
- **f85–91:** back to real time.
- **f96 (516):** second, smaller landing.
- **f106 (526, beat 4): bonk.** The ball strikes the left flank; the gummy jiggles sideways; the ball deflects
  front-right and rolls to a stop by f150.
- **f106–165:** the wobble decays to rest.
- **f166–170:** hold.
- **f171–180:** whip.

**On-screen text.**
- Pill **"Animated geometry · frame to frame"** (coral dot), global 436–585.
- Chip, global 445–520: `1×`, then **`0.2× · frame 451`** at 451. The counter increments with every film frame up
  to `frame 510` (fixed-width cells). It shows `1×` from 511 and pops out at 516–520.

**Transition.** In: circle match from S02 (§2.6). Out: whip right into S04's whip-in (blur match).

**Capability proof.**
- The camera is locked, so the only legitimate change between frames is the animated geometry and its light
  transport. The stripes, blocks and wall mirror must stay pixel-stable; flicker would be glaring against flat
  pastels.
- The gummy deforms non-rigidly (squash, bulge, stretch, lagging ears).
- Four independent transport paths must agree on every frame: refraction of the high-frequency stripes,
  reflections (glossy floor, wall mirror, rolling chrome ball), the contact shadow, and the transmitted glow.
- At 0.2×, consecutive frames are ≈6.7 ms of animation apart, and the counter proves they are consecutive frames.
- The banded ball proves it rotates, and the collision shows interacting animated geometry.

**Samples and cost.**
- `D.setup_cycles(samples=512, threshold=0.008, min_samples=64, diffuse=4, glossy=8, transmission=12, volume=2, caustics=True, clamp_indirect=10, motion_blur=True, shutter=0.5)`.
- Deformation motion blur on (the object default).
- `final_samples=512`. ≈20 s/f → **1.00 GPU-h**.

**Risks and mitigations.**
1. **Absorption streaks or specks** from the scan's residual non-manifold edges. Draft a squash pose first.
   - Fallback A: cap squash at height 0.62.
   - Fallback B: `D.spot_cow("Gummy", 0.60)` (watertight) with the same lattice.
2. **Ear self-intersection** at full squash. The cap at height 0.55 is designed for this; if it still happens,
   lower `ear_flop` to 0.6.
3. **OIDN flicker in the gummy** would be ironic for C3. min 64 samples; check a 10-frame preview as video; run the
   §7 frame-difference QA.
4. **Lattice motion-blur artefacts.** Set `scene.render.motion_blur_steps = 3` if the deformation blur looks wrong.
5. **Whip-blur mismatch with S04.** Both use 55° in 10 f, shutter 1.0, the same direction, and 16.5°/f at the cut.

---

### S04 · `s04_every_dot`: "Every dot" · C4
**Frames:** local 1–180 = global 601–780 · bars 11–13 · 20.0–26.0 s.

**Set dressing.** A remix of teaser rooms 1 and 4:
`D.diorama_corner("Room", size=4.0, height=2.8, floor_mat=D.polyhaven_texture("wood_floor","4k", tint="peach", tint_mix=0.25, uv_scale=0.5), left_mat=D.mat_clay("lemon"), right_mat=D.mat_clay("butter"), rot_z=45)`.

| Object | dopa call | Material | Placement |
|---|---|---|---|
| **Seurat canvas** | `D.plane("Seurat", (1.8, 1.1982), location=(-1.612,1.117,1.45), rotation=(90,0,45))` | `D.mat_image("assets/paintings/seurat_grande_jatte_20000.jpg", rough=0.55, interpolation="Linear")`, then set Principled `Specular IOR Level` = 0.2 | on the lemon wall, 7 cm proud; normal n = (0.7071, −0.7071, 0); u runs along (0.7071, 0.7071, 0) and is not mirrored |
| Frame | `D.rounded_box("Frame", (1.98,0.07,1.38), 0.03, rotation=(0,0,45))` centred at canvas − 0.036·n | `D.mat_candy("orange")` | the canvas sits 1 mm in front of its face |
| Gold lip | 4 × `D.capsule(r=0.008)` along the canvas edges | `D.mat_metal("gold", rough=0.25)` | |
| van Gogh | `D.plane("VanGogh", (0.6,0.4776), location=(1.803,0.954,1.50), rotation=(90,0,-45))` | `D.mat_image("…/vangogh_wheat_field_cypresses_met.jpg", rough=0.6, interpolation="Linear")` | butter wall |
| van Gogh frame | `D.rounded_box((0.70,0.05,0.58), 0.02, rotation=(0,0,-45))` behind it | `D.mat_candy("aqua")` | |
| Armchair | seat `rounded_box((0.80,0.70,0.40), 0.10, soft=True, base_at_zero=True)`, back `(0.80,0.20,0.55)`, arms `(0.16,0.70,0.55)`, group yaw 45° (front faces n) | `D.polyhaven_texture("curly_teddy_checkered","8k", uv_scale=1.5)` | centre (−1.223, 0.728), under the Seurat |
| Plush bunny | `D.stanford_bunny("PlushBunny", 0.32)` on the seat (z 0.40) | `D.mat_velvet("lilac")` | facing the camera |
| Side table | top `D.cylinder(0.28, 0.04)` at z 0.58, leg `D.capsule(0.03, 0.58)`, base `D.cylinder(0.16, 0.03)` | `D.mat_candy("mint")` | (−0.55, 0.25) |
| Bowl + fruit | bowl `D.cylinder(0.13, 0.05, bevel=0.02)`; `D.import_gltf` food_lime_01, food_kiwi_01 | `D.mat_candy("pink")`; glTF as-is | on the table |
| Magnifier (set dressing only) | `D.import_gltf` magnifying_glass_01 lying flat | handle → `mat_candy("pink")`, rim → `mat_metal("gold")`, lens → `mat_glass("white")` | on the table; never used optically |
| Floor lamp | pole `D.cylinder(0.02,1.5)` gold; shade `D.cone(0.25,0.30)` at z 1.6; bulb `D.sphere(0.05)` | shade `mat_clay("cream")`; bulb `mat_emission("#FFE9C7", 6)` | back corner (0, 2.05) |
| Rug | `D.cylinder("Rug", 1.0, 0.02, (-0.2,-0.2,0), base_at_zero=True, bevel=0.01)` | `D.mat_velvet("pink")` | |
| Rubber duck | `D.import_gltf` rubber_duck_toy, scale 2.5, yaw 200° | as-is | on the rug at (0.35, −0.55) |
| Dot-orb | `D.sphere("DotOrb", 0.017)` | Mix(candy white, Emission white k): k 0 → 6 | hidden until f166 (`D.hide_range`) |

**Push target.** The painted white disc of the "rosette" figure, measured on a 1:1 crop of the 20000 px scan:
- centre **uv (0.2755, 0.565)**, diameter ≈380 texels (3.4 cm);
- world position **D = (−1.898, 0.831, 1.528)**;
- it is a natural "orb" in the painting, and at the end framing it spans 21.7% of the frame width.

**Lighting.**
- Gallery wash: `D.light("AREA","Wash", (0.6,-1.8,3.0), (-1.612,1.117,1.45), power=650, color="#FFF4E6", size=2.5)`.
  Even and glare-free; the canvas specular is 0.2.
- `D.studio_rig(target=(-0.3,0.8,0.8), scale=1.0, key_power=500)`.
- `D.world_hdri("assets/hdri/candy_sky_nosun_4k.hdr", 0.4, camera_bg="cream")`.

**Camera.** One camera: 40 mm, sensor 36, focus object = the target empty. This is one unbroken dolly: no zoom, no
cut, no texture swap. Write d(f), zoom and px/texel to meta.
- **f1–10, whip-in:**
  - the view starts rotated +55° (counter-clockwise, to the left) about the camera's vertical axis and swings
    right to the wide (`ease_out_cubic`), starting at 16.5°/f to match S03's exit;
  - shutter 1.0 → 0.5 over f1–10;
  - SETTLE overshoot 1.5° by f20.
- **f1–30, wide:** camera (0.90, −6.60, 3.00), target (−0.20, 0.90, 1.00), f/2.0. The Seurat fills ≈24% of the frame
  width.
- **f31–105, log push:**
  - d(f) = 8.076·(0.175/8.076)^e, with e = `ease_in_out_sine(prog(f,31,105))`;
  - direction from D to the camera = slerp(dir0, n, s), with dir0 = normalize(cam0 − D) and
    s = `smootherstep(prog(f,31,100))`; the camera ends square to the canvas;
  - camera = D + d·dir;
  - the target moves room-centre → D over f31–60 (`ease_in_out_sine`, keep it C¹-smooth), then stays on D;
  - f-stop 2.0 → 11 over f60–100, interpolated in log space.
- **End pose** (f105): camera (−1.774, 0.708, 1.528).
  - The visible canvas is 0.1575 m = 1750 texels across 1920 px, i.e. **1.10 px/texel**.
  - Zoom ×46.1, magnifying to slightly over 1:1 (never beyond 1.3 px/texel).
- **f106–165, hold:** the camera and target drift 0.5 mm together along u (≈6 px over 60 f, ≈0.1 px/f), so any
  texture swimming or shimmer would show.
- **f166–180:** focus distance 0.175 → 0.155 m and f-stop 11 → 4 over f166–176. The canvas softens behind the
  orb.

**Beats** (global in brackets).
- **f1–10 (601):** whip-in.
- **f11–30:** the whole room for one breath: plush bunny, fruit, duck, both paintings. Pill pops on beat 2 (f16).
- **f31 (631, beat 3):** the push starts.
- **f31–105:** the room falls away, the orange frame whips past, the strollers and sunlit grass resolve into dabs,
  and the white disc with its red ring centres.
- **f106 (706, beat 4): ≈1 texel/px.** Individual dabs, complementary orange/blue dots and the canvas thread weave
  of the scan are all crisp.
- **f166 (766, beat 4): the disc pops.**
  - DotOrb centre goes from D − 0.02·n (hidden behind the canvas) to **D + 0.02·n** by f174 (`ease_out_back`).
  - Its emission ramps 0 → 6 over f170–180.
  - The painted dot becomes a light.
  - At f180 the glowing sphere is ≈468 px wide (24.4%), centred. Measure it and give the number to S05.

**On-screen text.**
- Pill **"High-res textures"** (lemon dot), global 616–765.
- Chip, global 631–765: live `×1.0 → ×46` from meta, then **`≈1 texel / px`** from 706.

**Transition.** In: whip-in from S03. Out: the dot-orb circle match into S05 (§2.6).

**Capability proof.**
- One unbroken camera move goes from ≈1/46 px per texel (the whole room) to ≈1.1 px per texel on the same 20000 px
  asset, with no swap, blur or shimmer.
- The end frame holds detail that only the full scan contains: individual dabs and canvas weave, matching the
  source crop.
- The camera ends square to the canvas at f/11, so defocus cannot hide softness, and the sub-pixel drift would
  expose any texture swimming.
- In the wide, the 8K teddy plaid, the 4K wood and the scanned fruit and duck show texture fidelity on lit, curved
  surfaces.

**Samples and cost.**
- `D.setup_cycles(samples=256, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=8, caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)`.
- `final_samples=256`.
- ≈8 s/f, plus ≈40 s one-time 20K decode and upload per process (2 processes) → **0.42 GPU-h**.
- Drafts use `seurat_grande_jatte_2048.jpg` and previews `_8192.jpg`, selected with `--mode`. Finals **must** use
  the 20000 px file.

**Risks and mitigations.**
1. **Softness at 1:1.** Use Linear interpolation: Cycles' Smart and Cubic both take a blurring B-spline path on GPU.
   Simplify texture limit off. The perpendicular end is guaranteed by the slerp.
   - QA: render f106 and f165 in final mode. Compare a 400×400 centre crop with the source crop scaled 1.097×; the
     dots must match.
2. **A kink in the camera path** where the target hand-off ends. Use smooth curves only (no LINEAR target keys at
   f60); check camera speed in meta.
3. **Glare on the canvas.** Specular 0.2 and the wash at ≈22° off the normal. If a sheen appears in the hold, lower
   the specular to 0.1.
4. **20K memory and load:** ≈1.07 GB VRAM, fine on an H200. Persistent data covers later frames.
5. **The dot-orb is visible early.** `hide_range(visible_from=166)` and the start position behind the canvas.

---

### S05 · `s05_title`: "LaRenderer" · title + recap
**Frames:** local 1–120 = global 781–900 · bars 14–15 · 26.0–30.0 s.

**Set dressing.**
- **Cove:** `D.cyclorama("Cove", width=30, depth=20, height=8, radius=1.2, wall_y=3.0, mat=D.mat_clay("lavender", rough=0.7, sss=0.0, sheen=0.1))`.
  This is the swatch-proven stage.
- **Title:**
  - `D.text3d("LaRenderer", font="fredoka", size=0.85, extrude=0.20, bevel=0.07, bevel_res=10, location=(0,0.4,0), rotation=(90,0,0), align_x="CENTER", align_y="BOTTOM", to_mesh=True)`.
  - Scale uniformly so the word is **4.4 m** wide.
  - Edit mode → `bpy.ops.mesh.separate(type='LOOSE')`. This gives exactly 10 letter objects (no i or j dots).
  - Sort them by bounding-box x, and set each origin at its base centre (the squash pivot).
  - Materials: `D.mat_candy(c, rough=0.2)` with, in order: `pink, coral, orange, lemon, lime, mint, aqua, blue, violet, "#C454C9"`.
- **Honeycomb band** (the teaser grid, flat-top hexes on the cove wall):
  - 10 tiles with circumradius 0.55, at x = −3.96, −3.08, −2.20, −1.32, −0.44, 0.44, 1.32, 2.20, 3.08, 3.96;
  - zig-zag z = 2.05 ± 0.22, alternating (+ for even index);
  - tile body front face at y ≈ 2.89.
  - **Body:** `D.cylinder(radius=0.55, depth=0.08, segments=6, bevel=0.025, rotation=(90,0,0))`.
  - **Rim:** `D.torus(major=0.51, minor=0.035, major_seg=6, rotation=(90,0,0))`. Verify the corners align with the
    body in a draft.
  - **Playing tiles** are the middle four, in story order: x −1.32 = S01, −0.44 = S02, +0.44 = S03, +1.32 = S04.
    - Rim = chapter colour (`blue`, `mint`, `coral`, `lemon`); body `mat_candy("cream")`.
    - **Screen:** a 6-gon bmesh disc of radius 0.47, 2 mm in front of the body.
      - UVs map the hex's flat-to-flat height (0.814 m) to the full image height, centred, aspect kept:
        u = 0.5 + x/(0.814·16/9), v = 0.5 + z/0.814. This shows the central 65% of the clip width.
      - Material: `D.mat_video("renders/proxies/<id>/p_0001.png", 120, start=1, offset=0, emission=0.6, rough=0.35, cyclic=False)`.
  - **Solid tiles** (three each side; the outermost are cut by the frame edge, so the band reads as a mosaic, not a
    row): bodies `mat_candy` in `sky`, `blush`, `butter` (left, outer → inner) and `pistachio`, `peach`, `lilac`
    (right, inner → outer); rims `mat_candy("cream")`.

**Lighting.**
- **White orb W:** POINT r 0.04, 260 W (tune until the letters' lit faces read their true palette colour at ≈0.85
  display), at **O = (0, −1.2, 1.40)**. Halo r 0.12 (f1) shrinking to 0.07 by f24; `mat_emission("white", 4)`.
- **Split lights**, POINT r 0.04, coloured halos r 0.07 at emission 2.0:
  - coral 127 W at (−1.0, −1.2, 1.30);
  - lime 273 W at (0, −1.2, 1.45);
  - blue 244 W at (1.0, −1.2, 1.30).
  - These are 260 W × 0.49 / 1.05 / 0.94; neutral sum.
- **Fill:** `D.light("AREA","Fill", (0,-6.0,4.0), (0,0.5,0.8), power=160, color="lavender", size=6.0)` (≈20%).
- **World:** `D.world_hdri(D.HDRI["studio_small_09"], 0.3, camera_bg="lavender")`.

**Camera.** One camera, 50 mm.
- **f1:** at (0, −2.56, 1.40), looking at O. The camera is 1.36 m from the orb, so the halo (0.24 m) spans
  **24.5% ≈ 470 px**, centred. Match S04's measured value to ±10 px by nudging this distance.
- Focus on the orb; f/2.8. Behind it are defocused lavender and coloured hex blobs.
- **f1–24, pull-back:** camera to (0, −9.0, 1.90) in log-distance from O (`ease_out_cubic`), then SETTLE (1.5%
  overshoot) by f34.
  - The target moves O → (0, 0.4, 0.75) (`ease_in_out_sine`, f1–24).
  - Focus racks from the orb to the target empty over f1–14; f-stop 2.8 → 4.0.
- **f24–120:** 1% push (camera y −9.0 → −8.92, `ease_in_out_sine`).
- **Final lockup** (rules; tune to these):
  - the title spans 62–66% of the frame width, baseline at 68–72% from the top;
  - the tile band sits within the top 32%;
  - the orb row (≈36% from the top) sits between the band and the title;
  - nothing else is in frame.

**Beats** (global in brackets).
- **f1–7 (781):** the glowing orb, matched to S04's dot.
- **f8–16 (788):** split. W's halo shrinks to 0 over f8–10, W off at f8. Coral, lime and blue appear at O and
  spring (`ease_out_back`, 8 f) to their positions while the pull-back reveals the cove and the playing honeycomb.
- **f16–50 (796–830), letter roll** in 16th notes. Letter i lands at f = 16 + round(3.75·i):
  16, 20, 24, 27, 31, 35, 39, 42, 46, 50.
  - Each falls from base z 2.8 with g = 14 m/s² (19 f, motion-blurred).
  - On landing: scale_z(t) = 1 − 0.30·e^(−6t)·cos(2π·2.5t), xy = 1/sqrt(scale_z) (BOING).
  - Tilt ±6°, alternating sign by index, decaying with the same envelope.
  - Contact shadows pop under each letter with three-colour fringes (aqua, violet and lemon-yellow edges).
- **f51–60:** everything settles. Three coloured orbs hover above the word.
- **f61 (841, bar 15 downbeat): FUSE.**
  - Coral, lime and blue spring back to O (`ease_in_out_cubic`, 8 f, settled by f71).
  - Halos cross-fade f67–71: coloured → 0, white r 0.07 → 1.
  - At f71, the coloured lights go off and W goes on at 260 W. They are co-located with the same total, so the
    swap is invisible.
  - Every coloured fringe collapses into **one crisp shadow**.
  - The letters do a unison 3% squash pulse over f61–69.
- **f71–120:** hold on **LaRenderer** under one white light. The honeycomb keeps playing at low emission.

**On-screen text:** none in the overlay; the title is the in-world 3D word. An optional tagline is left to the
editor (§8).

**Transition.** In: circle match from S04. Out: end of film. Hold the last frame, or cut to the paper video.

**Capability proof and recap.**
- The opening's point-light test resolves. Three palette lights, whose shadows fringe in complementary colours,
  fuse into one white key, and the shadow becomes one crisp silhouette: superposition, shown one last time.
- The letters land with continuous squash and stretch (C3).
- The honeycomb replays all four chapters at once as the teaser mosaic come alive.
- The hue-wheel dial of S01 returns as the hue-ordered word.

**Samples and cost.**
- `D.setup_cycles(samples=384, threshold=0.01, min_samples=32, diffuse=4, glossy=6, transmission=4, caustics=False, clamp_indirect=10, motion_blur=True, shutter=0.5)`.
- `final_samples=384`. ≈11 s/f → **0.37 GPU-h**.
- **Depends on rendered frames of S01–S04** via proxies (§5.4). Render it **last**; during development use preview
  stand-ins.

**Risks and mitigations.**
1. **Tiles compete with the title.** Tile emission 0.6, and 1/r² falloff darkens the wall. QA: the tiles' mean
   luminance must be ≤60% of the letters'; lower the emission to 0.4 if not.
2. **Lemon letter on lavender** (similar luminance). Check in preview. The extruded sides and contact shadow should
   separate it; if not, exposure −0.1 or fill +20%. Never swap in lilac.
3. **Neighbouring letters intersect during squash.** If they do, reduce squash to z 0.78 (xy 1.13) or set the text
   `spacing=1.05`.
4. **Coloured halos wash out.** Emission 2.0; check in preview.
5. **Proxies are re-tonemapped** (they look slightly flatter). Acceptable for tiles; do not raise their emission to
   compensate.
6. **Missing proxies.** `make_tile_proxies.py` writes labelled placeholder frames in the chapter colour, so S05
   always builds.

---

## 5. Assembly

### 5.1 What is done where
| Task | Where |
|---|---|
| All camera hand-offs: orb fall, mirror push and pull, whip-out and whip-in, dot pop and pull-back | **In Blender**, inside each shot |
| The finale's replay of S01–S04 | **In Blender** (S05, `D.mat_video` on the tile screens) |
| All cuts: hard cuts on bar lines; no dissolves, no speed ramps, no reframing | **In post** |
| Captions, chips and the lat-long strip | **In post** (RGBA overlay layer) |
| Grading | **None in post.** Colour is final out of Blender (fixed PBR Neutral pipeline) |

### 5.2 Cut list (film frame = shot start + local − 1)
| Film frames | Source | Local frames |
|---|---|---|
| 1–240 | `renders/final/s01_lights_world/f_0001..0240.png` | 1–240 |
| 241–420 | `renders/final/s02_caustics/f_0001..0180.png` | 1–180 |
| 421–600 | `renders/final/s03_gummy/f_0001..0180.png` | 1–180 |
| 601–780 | `renders/final/s04_every_dot/f_0001..0180.png` | 1–180 |
| 781–900 | `renders/final/s05_title/f_0001..0120.png` | 1–120 |

### 5.3 Overlay plan (`scripts/make_overlays.py`)
- Writes `renders/overlays/o_0001..0900.png` (1920×1080 RGBA, straight alpha, sRGB, display-referred).
- Draws at 2× and downsamples for crisp scaled sprites.
- Reads `renders/meta/*.json` for live values: S01 θ/tilt, S03 frame counter, S04 zoom.
- Uses the sprites from `shots/s00_ui_sprites.py`. That script renders, with an ortho camera and transparent film:
  - a horizontal `D.capsule` in `mat_candy("white", rough=0.25)` over a shadow-catcher plane, 2× resolution,
    3-sliced by the overlay script into left cap / stretchable middle / right cap;
  - 96 px candy spheres in `blue`, `mint`, `coral`, `lemon`, `white`, `lime`.
  - If sprites are missing, the overlay script falls back to Pillow-drawn pills.

| Global frames | Element | Content |
|---|---|---|
| 20–104 | pill + dot chip | "Point lights"; 1 white dot → 3 dots (coral, lime, blue) at 61 |
| 121–238 | pill + θ chip | "Environment maps · any rotation"; `θ 0°` … `θ 405° · tilt ±4°` |
| 121–238 | lat-long strip, top-right | live re-projection of `candy_sky_preview.png` |
| 256–410 | pill | "Caustics · glass · mirrors" |
| 436–585 | pill | "Animated geometry · frame to frame" |
| 445–520 | chip | `1×` → `0.2× · frame 451…510` → `1×` |
| 616–765 | pill + zoom chip | "High-res textures"; `×1.0 … ×46` from 631, then `≈1 texel / px` from 706 |
| 781–900 | — | nothing (3D title only) |

Optional `--slug`: a lower-right 20 px Fredoka SemiBold line, ink at 60% opacity, reading "Illustrative · rendered
with Cycles". It is **off** by default (lead decision); the authors decide (§8).

### 5.4 Finale proxies (`scripts/make_tile_proxies.py`)
- For each tile it writes 120 frames, 640×360, 8-bit sRGB (Lanczos):

  | Tile | Source frames | Content |
  |---|---|---|
  | S01 | f1–120 | dark start, then the coloured-shadow split |
  | S02 | f1–120 | drop-ins and caustic macro |
  | S03 | f1–120 | impact and slow-mo |
  | S04 | f31–150 | push and 1:1 hold |

- Source order: `renders/final/<id>` if complete, else `renders/preview/<id>`, else labelled placeholder frames in
  the chapter colour.
- Re-run it after each upstream final, then render S05.

### 5.5 Composite and encode (`scripts/assemble.py`)
1. Read `docs/shots.json` and symlink every shot frame into `renders/film/f_0001..0900.png`. Fail loudly if any of
   the 900 frames is missing.
2. Composite the overlay in Python: cv2 reads the 16-bit frame; alpha-blend the 8-bit overlay promoted to 16 bit;
   write `renders/film_comp/f_####.png`, 16-bit. This is deterministic and avoids ffmpeg overlay colour quirks.
3. **Master:**
   `tools/ffmpeg/ffmpeg -framerate 30 -i renders/film_comp/f_%04d.png -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le -color_primaries bt709 -color_trc bt709 -colorspace bt709 out/LaRenderer_opening_master.mov`
4. **Review:** `scripts/make_mp4.sh renders/film_comp out/LaRenderer_opening_review.mp4`
   (H.264 CRF 16, yuv420p, error-diffusion dither).
5. **Cut-pair sheet:** `scripts/contact_sheet.py out/cuts.png` with film frames 240, 241, 420, 421, 600, 601, 780
   and 781. This is the transition review.
6. **Audio:** none. The editor lays a 120 BPM track with its downbeat on film frame 1.

---

## 6. Budget and schedule
| Item | GPU-h |
|---|---|
| S02 gate: 3 frames + 12-frame strip, final mode | ≈0.15 |
| Full-film preview pass (50%, 128 spp) | ≈0.40 |
| Finals: S01 0.60 · S02 1.50 · S03 1.00 · S04 0.42 · S05 0.37 | 3.89 |
| UI sprites (stills) | <0.01 |
| **Planned** | **≈4.45 of 6.0** |
| Reserve | ≈1.55 (covers the S02 3072-spp fallback, or any one other shot again) |

**Order:**
1. **Hour 0–2, in parallel:**
   - S01: candy_sky and its calibration;
   - S02: build and gate;
   - S03 and S04: build and drafts;
   - S05: sprites, overlay, proxy and assembly scripts, with a placeholder-proxy build.
2. Previews of all five shots, then a preview film with overlays. Review it.
3. Finals on GPUs 6 and 7 (`scripts/render_split.sh shots/<id>.py final 1-N "6,7"`), in this order:
   S02 (≈45 min wall) → S01 + S03 (≈50 min) → S04 (≈13 min) → proxies → S05 (≈11 min) → assemble.
   Total ≈2 h wall-clock.

---

## 7. QA checklist (`scripts/qa_diff.py`, venv Python)
- **S01**
  - mean |f195 − f135| < 0.5/255 (loop check);
  - shadow at 315° (f121), 45° (f150), 135° (f165), 225° (f180), 0° (f225);
  - single-occlusion colours read lemon-yellow, aqua and violet.
- **S02**
  - the gate passes;
  - the 12-frame strip shows no blotch boiling;
  - the caustic band is in focus in Cam M;
  - f180 ball = 1536 ± 15 px wide.
- **S03**
  - mean |Δ| between consecutive frames over the static stripe/block region, local f31–60, < 1/255;
  - f1 ball = 1536 ± 15 px;
  - no specks in the gummy at f38 (max squash).
- **S04**
  - 1:1 crop matches the source at f106 and f165;
  - no shimmer during f106–165 (consecutive-frame diff over the centre crop shows only the drift);
  - record the f180 orb diameter.
- **S05**
  - f1 orb diameter = the recorded S04 value ±10 px;
  - title legible at 25% scale;
  - tiles ≤60% of the letters' luminance.
- **Film**
  - 900 frames;
  - every cut on a bar line;
  - the cut-pair sheet reviewed;
  - pills gone ≥2 f before each cut;
  - no caption contains a number about speed or quality, or a comparison.

---

## 8. Open questions for the authors
1. **Honesty.** The opener is path-traced in Cycles, not LaRenderer output. Should the master carry the
   "Illustrative · rendered with Cycles" slug? Or will the main video follow it with LaRenderer renders of these same
   scenes (each vignette is a valid input: point lights, env map, dielectrics, animated meshes, a 20K texture)?
2. **"20K" in captions.** The C4 pill says "High-res textures". Do we want to state the scan resolution ("20K"),
   i.e. does LaRenderer actually handle that size?
3. **Length.** Is 30.0 s acceptable? Trimming S04 to 2 bars gives 28.0 s but cuts the 1:1 hold to ≈1 s.
4. **Tagline.** Should there be one under the title (editor-added, Fredoka SemiBold, ink), or the title alone?
5. **Music.** The track must be 120 BPM with its downbeat on film frame 1. Confirm before the edit.
