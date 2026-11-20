# Lead notes, polish round 2 (after the build round)

These notes take priority over critic suggestions. The fixed elements of the storyboard still hold: hit
frames, transitions, capability proofs and QA thresholds.

## Global
- **G1 · One glowing light.** Every visible light orb in the film gets the same soft glow:
  - which orbs: the S01 orbs, the S02 orb, the S04 dot-orb once it emits (f170 onward), and the S05 orbs;
  - how: copy S01's compositor bloom (Glare/Bloom driven only by the Emit pass, so nothing else blooms) with
    identical parameters, so the protagonist light looks the same everywhere;
  - the orb **core** stays crisp; the S04 f180 / S05 f1 circle match still measures the core at 468 ± 10 px,
    and the glow radius must match on both sides of that cut.
- **G2 · No grey.** Dopamine means clean, bright, saturated values. Every ground must read as its pastel (not
  grey or tan), shadows must be tinted (cool lavender, mint or sky), and hero colours must render true. Only
  light sources and speculars may clip.
- **G3 · Keep what works.** After changes, re-run the shot's QA checks (section 7 of the storyboard plus the
  checks the builder reported) and report the numbers.
- **G4 · Final-render cost caps** (GPU-hours for the whole shot at final quality): S01 ≤ 0.4, S02 ≤ 1.6,
  S03 ≤ 1.4, S04 ≤ 0.5, S05 ≤ 0.4.
- **G5 · Lessons from S02 that apply to every glass object.**
  - `D.mat_glass` and `D.mat_jelly` put the tint on Principled Base Color, and Cycles applies it at both
    interfaces of a closed solid, so the perceived colour is the palette colour squared (lemon reads amber,
    lime reads olive). S02's `candy_glass` helper corrects this with base = colour^0.5; copy it.
  - `clamp_indirect` must not be so low that it cuts transmitted or caustic paths from small bright lights.
    S02's clamp of 20 suppressed its caustics about 14×.
- **G1 parameters** live in `shots/s01_lights_world.py`. The S01 fixer must keep them unchanged so every
  other shot can copy them.

## S01 · lights_world
1. **Tighter day framing.** The island spans only about 46% of the frame width, so the locked day phase feels
   sparse.
   - During the launch (f106–120), dolly the camera in, eased and C1-smooth, to a tighter phase-B framing in
     which the island spans about 62–68% of the frame width.
   - Lock that pose exactly from f121 to f240. The f135 = f195 loop QA must still pass.
   - Phase A keeps its wider framing so the orbs have headroom.
   - Keep important things out of the overlay zones: the lat-long strip (top-right box, x 1456–1840,
     y 80–272) and the caption pill (lower-left, x 80–900, y 940–1000).
2. **The sky globe must carry the env-rotation read.** Make it larger (r ≈ 0.26–0.28), brighter and more
   saturated by day (emission about 0.5–0.6 or a brighter base), unobstructed, with the pink crank clearly
   turning.
3. *(Nice to have)* Make the coloured skylight on the white clay bunny visible: as the env turns, its flanks
   should pick up card colours.

## S02 · caustics
1. **The wide reads grey and dim** (f1–60, f121–180). Make it candy without losing caustic contrast:
   - the floor reads as a warm pastel (cream/butter) mid-tone, not grey;
   - shadows are tinted (cool lavender/mint fill, ≤ 10–15% of the key);
   - the walls read saturated mint/pistachio, not dark green;
   - the mirror-ball pedestal reads as candy coral, not maroon;
   - an exposure lift of +0.2 to +0.4 is allowed if caustic peaks stay unclipped.
2. **Caustics should sparkle in the wide too.** The crystal bunny's rainbow caustics on its plinth and the
   floor should be visible there. Options: a slightly stronger or closer orb, or a brighter plinth top.
3. **G1** applies to the orb.
4. **Lemon ball crescent.** In the macro (f66/f75) the lemon ball shows a sharp crescent "cut". If it is a
   geometry, intersection or normal problem, fix it. If it is a true refraction of the floor horizon, nudge the
   ball's position or rotation so it reads as a clean candy ball.
5. **Keep the macro** (now 75 mm and high-angle). It is the strongest proof. Only lift its shadows slightly
   away from grey.
6. **Cost.** The builder estimates 1.8–2.0 GPU-h against the 1.6 cap. Bring it under: for example, fewer
   samples in the wide frames where the caustics are small, and/or 1536 spp for the macro if the gate
   stability numbers hold.
7. **The f12–14 orb stop** causes a hard lighting snap (|Δ| up to 14/255). Ease the last frames of the fall
   so the light settles rather than slams.
8. **Match brightness across the cuts.** At 240|241 the film drops from S01's bright pastel day into a dim
   room; at 420|421 S02's grey-dark ball cuts to S03's bright pink ball. Making the room and the ball's
   reflection (the blush card and room rim) brighter and more pastel fixes both.

## S03 · gummy
1. **The gummy should glow.** Its thick body goes dark olive-brown; it should look like a translucent lime
   gummy:
   - the double tint (G5) is probably part of the cause: correct the base colour to colour^0.5;
   - lower the absorption density and/or brighten the absorption colour toward lime-yellow;
   - add a **light-linked** back/rim light whose only receiver is the gummy, so it glows from behind without
     washing out the floor reflections.
2. **Max squash (f38) is too flat**; it reads as lying down. Cap the squash height at about 0.62–0.65
   (storyboard fallback A) and keep it volume-preserving and juicy.
3. **Shimmer check.** Run a final-quality strip over f31–42 and measure gummy-interior shimmer (temporal
   noise). If it is visible, raise the samples within the cap.
4. *(Optional)* Less pale empty floor in the lower third, provided the reflection read survives.

## S04 · every_dot
1. **The room-wide (f11–30) is lit flat.** Give it a premium gallery look:
   - a warm, soft key from the upper left (a big window or softbox) with readable soft contact shadows under
     the armchair, bench and duck;
   - a cooler fill;
   - a light-based falloff toward the frame edges (no compositor vignette).
   - The canvas must stay evenly lit and glare-free.
2. **The floor** should read as clearly peach/pastel wood, not tan.
3. **G1** applies to the end orb (from f170); its core stays at 468 px at f180.
4. **Minification check.** Run a final-mode strip over f31–45, where the 20K texture is most minified, and
   check for boiling or sparkle. Report the result.

## S05 · title
1. **A more heroic lockup.**
   - Title about 72–76% of frame width, with juicier, deeper-pillow letters.
   - Baseline about 64–67% from the top.
   - The honeycomb sits fully inside the frame vertically (≥ 40 px top margin). It may bleed off the left and
     right edges. Make it calmer, with fewer or smaller solid tiles and softer contrast. The four playing tiles
     must read clearly as the four chapter clips.
   - The cove floor gets a soft glossy clear-coat so the letters cast soft reflections, filling the lower
     third elegantly. Avoid a hot spot; the floor falls off slightly toward the bottom edge.
2. **Make the superposition read.** Place the three coloured lights so each letter's three coloured shadows
   fan out visibly during f16–60 and then collapse into one at the fuse.
3. **G1** applies. The f1 orb matches S04's f180 orb: a 468 ± 10 px core and the same glow.
4. **Real tiles.** Re-run scripts/make_tile_proxies.py once the latest previews exist (S02's preview now
   exists), then re-render the preview.
