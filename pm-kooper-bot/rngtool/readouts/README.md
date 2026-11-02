# Faster RNG readouts? (pause screen, battle menus, field)

Question: is there anything on screen that reveals gRandSeed faster than the status-bar coin (about 1 bit/s)?
**Answer: no on the route.** The pause screen shows one more coin with the same 1 bit/s, and nothing else.

## Method
- `seed_diff.py`: same savestate and inputs, two different seeds (DIAGNOSTIC seed write after load), screenshot every
  frame, diff the frames. Also logs every `rand_int` caller per frame and the RNG steps per frame.
- `pause_coins.py`: logs every `rand_int` call with its roll (replayed from the frame's start seed; 0 mismatches),
  and screenshots the pause-screen coin every frame to see which rolls show as shines.
- Decomp: grepped `rand_int`/`rand_float` in `src/pause/`, the HUD script engine and the battle UI.

## Results (JP, emulator)
| Screen | RNG callers seen | Visible seed-dependent pixels |
|---|---|---|
| Pause, all 5 tabs (kpa_121, 560 frames) | per-frame step + 2 coin streams | only the stats-tab coin |
| Hallway Bowser T1 battle menu, idle and wheel moves (360 frames) | per-frame step + 1 coin | only the status-bar coin |
| Final Bowser P2 menu | see powerbounce/README.md: + lightning cycles (fixed, no seed info) | coin; bolts show cycle phase only |

**Pause screen in detail**
- `src/pause/` has no `rand_int` at all. The only random visual is `HES_StatusCoin`, the same HUD script as the
  status-bar coin (`hs_RandomRestart(100, 70)`: roll < 70 restarts the plain loop; roll >= 70 plays the shine).
- Two coin streams draw while paused, every 24 frames (48 after a shine): the stats-tab coin (visible) and the
  status-bar coin, which keeps animating hidden. Visible shines matched the visible stream's rolls >= 70 4 of 4 times.
- The visible pause coin is a new HUD element each time the menu opens. Its first draw is 30-31 frames after the
  Start press (3 Start timings), so its phase is known. The hidden coin's phase just continues.
- The per-frame step continues while paused (1 step per frame; the opening frame does 3 then 0).
- Other tabs (items, party, spirits, map) have no random visuals.

**Other random HUD things in the decomp, none useful**
- `status_star_shimmer.c`: 56 particles x 3 `rand_int` colour draws when star power is gained. Tiny pastel diamonds
  for 40 frames over the SP bar; not readable through a GV-USB2 capture.
- `HES_TEMPLATE_COIN` / `HES_Item_Coin` (shop prices), the popup-menu coin and the coin-count icon: same coin
  mechanism, and not on screen together with the status-bar coin on the route.
- ~~Effects mostly use `effect_rand_int`~~ **Correction (shimmer study below):** 55 effect files call `rand_int`
  through `shim_rand_int`, which is the game's `rand_int` on gRandSeed; only 12 use the separate `effect_rand_int`.
  Battle menus just happen to have no effects running.
- `btl_states_menus.c`'s `rand_int` is the Berserker badge only.

## Bits per second
A coin roll carries at most H(0.3) = 0.88 bits. Rolls come every 24 frames, or 48 after a shine: on average one per
31 frames (about 1 s). So about 0.85 bits/s from any one visible coin, which matches the 25-40 s locks seen.
No route screen shows two coins at once, so no screen beats that.

## What the pause screen is still good for
- **No auto-hide**: the stats-tab coin stays up for as long as the menu is open, without the C-up bar's 7.3 s hide
  and re-press gaps. That only matters when you stand still anyway (e.g. the High Power Bounce Manipulator in a field
  room); in battle the coin is always up.
- **Cost in a run**: opening and closing the menu takes real time and gives the same 1 bit/s, so it saves nothing
  for the zero-wait speedrun approach.

## Not verified
- A real-console capture of the pause coin (same 16x16 art as the status bar, so the detector should work).
- Field rooms beyond kpa_121 with this diff tool (earlier work already found the kpa_53 torches and the kpa_102
  wanderers; the rooms after Jr. Troopa were measured clean).
- Pause in battle (not possible) and the pause screen during a cutscene (not possible).


# Follow-up: star-power shimmer, Lakilester's Spiny Flip, Mario's Charge (S-Video)

**Bottom line: the strongest readout on the route is not the shimmer or the spinies but Mario's Charge on Hallway
Bowser T1.** It spawns two `energy_in_out` effects whose screen-wide light rays each take a fresh `rand_int(359)`
angle from gRandSeed every ~10 frames: about 110 draws in ~1.5 s, each ray hundreds of pixels long. That is far more
than the 38 bits a lock needs, inside an action the route already does. Not yet built or tested end to end.

## 1. Star-power shimmer (`status_star_shimmer.c`)
- **Trigger:** only `add_star_power()`, which only Focus calls (Mario's Focus, or the partner variant). The per-turn
  SP regen (`btl_states_actions.c`, `starPower += SP_PER_SEG`) does **not** shimmer. So it shows on the route only if
  the runner uses Focus; Hallway T1 (Charge, Spiny Flip) and the planned FB turns do not.
- **Draws:** all 56 particles colour on the first status-bar update after the trigger, in one frame:
  `r = rand_int(127)`, `g = rand_int(127 - r)`, `b = rand_int(127 - r - g)` (+128 each), on gRandSeed. 165-166 draws
  (rand_int(0) makes no draw). Verified in the emulator: RAM colours = prediction from the frame's seed, 1 draw into
  the frame, 2 of 2 seeds (`shimmer_probe.py`). Positions, velocities and scales are fixed tables; only colour is
  random. Particles live 30 frames, no respawn. JP addresses: gStatusBar 0x8010F118, ShimmerEmitters 0x8010D1C0.
- **What the colour looks like:** the display list (decoded from JP RAM, 2-cycle) is
  `COMB = PRIM + (TEX_I - 127)/2`, `C = SHADE_A*COMB + (1 - SHADE_A)*white`, shade alpha 1 at the centre and 0 at the
  diamond tips. So each star is a near-white pastel: the centre is `192 + raw` per channel, clipped at 255 (half of
  red values saturate). glide64 draws them pure white; an accurate RDP plugin could not be built here, so the colour
  model is from the decoded combiner, not a pixel-exact render.
- **Geometry:** with the bar fully shown, 46-54 of 56 particles are individually visible (centre on screen, not
  covered by a later particle) on some frame 1-7 (`shimmer_geom.py`). The rest fly off the top.
- **S-Video estimate (`shimmer_svideo.py`, STEP=8 NP=8, 1.3 MHz chroma, noise Y 2 / C 3 levels):** every one of the
  8 particles tested hit the grid cap, 9.67 bits each (77 bits for 8), because luma (4.2 MHz) alone separates the
  pastel tints. So one shimmer would carry hundreds of bits through S-Video *if* the page had an exact render model;
  the real limit is model error (the combiner model here is unverified on hardware), not the capture. Moot for the
  route anyway unless Focus is used.

## 2. Lakilester's Spiny Flip (Hallway T1)
- The Spiny Flip script itself has no `rand_int`: the spiny's arc is `JumpPartTo` to the aimed target, fully
  deterministic. `ThrowSpinyFX` (`rand_int(140)`, `rand_int(80)` arcs) is **Spiny Surge** only.
- gRandSeed visuals during it (emulator log, `spinyflip_diff.py`, 2 seeds, plus `data/hw1_*` logs):
  - `energy_in_out` charge glow around the lifted spiny while aiming: 21 init draws (`rand_int(360)` base angle,
    10 x `rand_int(10)` speed, 10 x `rand_int(20)` phase) then a `rand_int(359)` new angle per ray every 20 frames:
    38-66 draws. On screen: thin yellow streaks, 4-8 px long (320x240 space), ~1 px wide, faint.
  - Impact: 8 + 10 + 6 `rand_int(359)` draws (frames ~150, ~260, ~420 after the confirm) for the hit sparkles
    around Bowser; visible white rays for ~12 frames.
  - Bowser's reaction: an evt `RandInt(80)`, `RandInt(60)` (frame ~194) changes the following animation; after that
    the two seeds' frames differ wholesale.
- **effect_rand_int:** `effect_utils.c`, seed constant 0x1E6D3457 at boot, advanced only by the 12 effects that call
  it (smoke puffs, snow, leaves, confetti...). Never touches gRandSeed and is not touched by it. Its state depends on
  how many such calls happened since boot, so it is unknown; and it advances per call, not per frame, so it cannot
  pin frame timing either. Not useful. (The big white smoke cloud on the spiny's impact is identical for both seeds.)

## 3. Mario's Charge (Hallway T1) - the useful one
- Two `energy_in_out` effects at the Charge: 2 x (1 `rand_int(360)` + 20 `rand_int(10)`) init draws 13-16 frames
  after the confirm, then ~1.5 `rand_int(359)` draws per frame for ~45 frames (71-74 draws in 4 logged runs),
  all on gRandSeed.
- On screen (glide64, `charge/` frames): bright yellow-white rays radiating from Mario across most of the screen;
  5,000-13,000 pixels per frame differ between the two seeds (640x480). Each ray's angle is its `rand_int(359)`.
- **S-Video:** a ray is a long, bright, high-contrast luma line; S-Video carries luma at ~4.2 MHz, so its direction
  survives to well under a degree. `streak_svideo.py` (even for the short, faint Spiny Flip streaks) recovers the
  integer angle exactly in simulation (8.49 of 8.49 bits) when the page's model of the scene is exact. In practice
  the limit will be model error (camera, ray origin, which ray is which), not the capture. Even at 2-3 bits per ray
  that is 150-200 bits per Charge.
- **How the page would read it:** fixed camera at T1 (battle cam, deterministic given the inputs), ray origin at
  Mario. On each frame, find bright radial lines in an annulus around Mario (Hough over angle), note each new ray's
  angle and first frame. Search: enumerate the state at the first respawn draw from its angle (+-2 deg: about
  2^32/360*5 = 6e7 seeds), and filter each with the next few predicted draws, interleaved with the per-frame step,
  the coin and both effects' respawn order (all deterministic given the seed). ~1e8 LCG steps: about a second in a
  worker. The confirm frame of the Charge is seen by the page already.
- **Lock time:** a full lock during the Charge animation itself (~1.5 s), zero waiting, versus 25-40 s standing or
  the zero-wait coin walk. If the reading is reliable it would also make the Time Out plan a near-certain lock.

## Not verified
- The ray-angle readout on real S-Video footage; the screen angle = `unk_3C` mapping (rotation about the effect's
  local Z, then camera); occlusion by Mario/Lakilester; how the Hough step copes with 20 overlapping rays.
- The shimmer's actual colours on hardware (no accurate RDP renderer here; glide64 shows white). Since checked on a
  real capture: see "Focus shimmer on hardware" below.
- Whether Final Bowser's early phase-2 effect at 0xE00D6838 (16 draws per 20 frames, see powerbounce/README.md) is the
  same `energy_in_out` ray effect - the same caller address suggests it; if so it is a continuous readout there too.
- Jr. Troopa and the FB phases were not re-checked for Charge-like effects.

# Focus shimmer on hardware: gRandSeed recovered from a real capture (`focus_seed.py`, `focus_search.c`)

**Result: one real console clip, one seed, large margin.** Clip: Hallway Bowser, Mario uses Focus (star power not
full), real N64 -> S-Video -> GV-USB2 -> OBS, 1280x720 **60 fps** h264 (game image at x 310..1280, scale ~3.25 x 3.30
capture px per N64 px). The status-bar shimmer is the 5-point star of 56 pastel diamonds that bursts out of the bar
when it comes back after the Focus animation (capture frames 280-330, ffmpeg 1-based numbering). Two earlier clips
(14-16-56, 14-17-34) were Super Jump Charge (スーパーチャージ, 4 FP) with a full bar: no shimmer in them.

| | |
|---|---|
| state before particle 0's draws | **0x3017E5F3** (15 draws before particle 5 = 0x4D63A67A, the state the search enumerates) |
| frame-start seed, if the shimmer starts 1 draw into the frame as in the emulator | 0xEA03640A (not verified for this battle frame) |
| full search, 51 particles (5..55) | cost **60.2**; runner-up 298.2 (best of the 511 seeds whose running cost stayed < 10 + 6.5/particle) |
| tight search (< 6 + 4.5/particle) | exactly 1 survivor in 2^32: the same seed |
| half search, particles 5..29 only | same seed, cost 27.2; runner-up 106.8 |
| held-out check: particles 30..55 scored with that seed | cost 33.4; random seeds mean 243.9, best of 400 random 187.5 |

Cost = sum over particles of min(12, chi-square over Y,U,V) with tolerances 8 / 3.5 / 3.5 levels. The held-out half
is the sanity check: its 26 colours were not used to find the seed and match it about as well as the fitted half.

**How (`python3 focus_seed.py CLIP --onset 279`, ~3 min on 1-2 free cores):**
1. Decode ~60 frames as YUV 4:4:4 (no RGB round trip). Keep only distinct frames: the 60 fps capture shows every
   game frame exactly twice here (frame diffs 0.03-0.15 vs 1.6-5); no blends, no extra repeats in the shimmer.
2. Geometry: correlate luma with the exact float32 particle tracks (InitialVelocities, `*0.92` per frame) over scale,
   emitter position and animTime offset. The first frame with the star (280) is animTime 0.
3. Colour: per particle, the 5x5 mean YUV at its (refined) centre, median over the frames where the centre is clear
   of neighbours (51 of 56 particles; 0-4 fly off the top before they separate). Frame-to-frame scatter 1-3 levels.
4. Seed-free calibration: model centre colour `min(255, 192 + raw)` per channel -> BT.709 limited YCbCr, then a gain
   and offset per channel so that the measured mean and variance over all particles equal the model prior's (no seed
   used). Gains Y 0.71, U 0.65, V 0.58; the means matched to < 1 level before any fitting.
5. Brute force in C (OpenMP) over the state before particle 5, prefix early rejection; walk back to particle 0.

**What the hardware colours look like vs the model:** clearly pastel pink / green / blue / lilac / cream diamonds,
readable by eye. With the seed known, a least-squares affine fit on `min(255, base + raw)` leaves residuals
Y 3.2, U 2.8, V 1.8 levels; base 184-192 fits best (160: Y 3.9 / V 2.2, 128 unclipped: 4.1 / 2.9 / 2.5, 224:
4.4 / 4.0 / 3.9), so the decoded combiner model (centre = 192 + raw, clipped) holds on hardware. Chroma comes out at
~0.6x the nominal amplitude at the centre (S-Video chroma blur, 4:2:0, and the white shade-alpha falloff around the
centre all dilute it); the fitted U/V rows are closer to BT.601 weights than to BT.709. The fitted matrix is printed
by the script and could be reused as a fixed calibration for the same capture chain.

**Focus's other sparkles (decomp, not tested on video):** both draw on gRandSeed through `rand_int`.
- `SpawnStarSparkleFX` = `fx_sparkles(FX_SPARKLES_0, .., 40)`: 36 particles x `rand_int(40000)` twice = 72 draws,
  but type 0 never uses them (fixed star outline), so they only advance the seed - nothing to read.
- `SpawnWishSparkleFX` = `fx_stars_shimmer(5, .., 50, 50, 40, 30)`: 40 particles, all drawn at spawn: angle
  `9*i + rand_int(359)`, then `rand_int(10)` start speed and `rand_int(10)` rise acceleration = 120 draws in one
  frame. These are the white sparkles rising around Mario: x = sin(angle) * radius (fixed per i), constant, y rising
  with the two random terms; particle i appears on frame i. A real second readout (~10 bits per sparkle) but it needs
  the 3D battle camera (BTL_CAM_PLAYER_WISH) projected into the capture; the draws between it and the bar shimmer
  (frames of per-frame consumers) are not counted here.

**Not verified / limits:**
- One clip, one seed. No emulator replay of that seed: the battle state at that frame is not reproducible here, so
  the check is internal (held-out particles), not an independent later event. No later gRandSeed visual in the clip
  was predicted (nothing random is visible after the shimmer before the clip ends).
- 0xEA03640A as the frame seed assumes the emulator's "1 draw into the frame"; other consumers in the battle frame
  may come first.
- `--onset` must be given (+-2 frames); the script does not find the shimmer by itself.
- Tolerances were set from the measured scatter (1-3 levels) and confirmed by the residuals, not fitted inside the
  search; particles that are partly covered (the early frames) are excluded rather than modelled.
- Live readout (speedrun page): needs the page's capture to keep YUV or a known RGB conversion, a WASM/worker port of
  the search (2^32 states with early rejection: ~2.5 min of CPU natively here, so it wants either
  several workers or a narrower candidate set from the page's tracker), shimmer onset detection (the bar reappearing
  plus the star), and the geometry fit cached per capture layout. Only useful if the route uses Focus at all.

## Independent check: coin shines after the shimmer (`focus_coin_check.py`)

Clip 15-22-35 ("focus + stall", 60 fps, same capture chain): two Focuses at non-full star power, then the bar stays
up on a menu for ~12 s. `focus_seed.py CLIP` (onset now found automatically: `find_onsets()` -> capture frames 259
and 922; `--which 0` for the first) recovers both shimmers:

| shimmer (capture frame) | state before particle 0 | full search | half search (5..29) | held-out 30..55 vs random |
|---|---|---|---|---|
| 259 | 0x236E46CE | 1 survivor in 2^32, cost 143.7 | unique, 60.3 | 83.5 vs mean 257.6 / best-of-400 206.7 |
| 922 | 0x97E5AAD6 | 1 survivor in 2^32, cost 150.5 | unique, 71.9 | 78.6 vs mean 252.9 / best-of-400 192.6 |

(Costs are higher than the first clip's 60 - the seed-free gains came out different, residuals Y/U/V 4.4/3.4/2.4 and
6.0/5.0/3.7 - but each search still leaves exactly one seed.)

1. **The two seeds are 696 LCG draws apart** (0x236E46CE stepped forward 696 times = 0x97E5AAD6). Two unrelated
   seeds would be ~2^31 apart; landing within 696 by chance is ~2e-7. The count fits the model exactly: 163
   (shimmer 1) + 72 (`fx_sparkles` type 0) + 120 (`fx_stars_shimmer` type 5) + 330 frame steps + 11 coin draws, with
   the coin's 24/48 schedule from shimmer 1 arriving at shimmer 2 on the same phase the coin check below finds
   (next draw 10 frames after shimmer 2). The video says 331.1 game frames between the shimmers (frame timing +-1).
   The two effects' exact frames are not pinned by this (many placements give the same count).
2. **Coin shines after shimmer 2:** stepping 0x97E5AAD6 through the shimmer's 164 draws, then 1 step per frame and the
   coin's rand_int(100) every 24/48 frames, predicts 12 coin draws while the coin is visible (432 game frames):

   | draw (game frame after shimmer) | 10 | 34 | 58 | 106 | 130 | 154 | 178 | 226 | 274 | 322 | 370 | 418 |
   |---|---|---|---|---|---|---|---|---|---|---|---|---|
   | rand_int(100) | 26 | 6 | **91** | 31 | 63 | 3 | **77** | **74** | **71** | **87** | **82** | 55 |
   | predicted flash (capture frame) | | | 1050-52 | | | | 1290-92 | 1386-88 | 1482-84 | 1578-80 | 1674-76 | |
   | seen (coin-box white flash onset) | - | - | 1050 | - | - | - | 1291 | 1387 | 1484 | 1580 | 1675 | - |

   **6 of 6 shines on the predicted frames, 0 false, 0 missed** (6 non-shine draws correctly quiet). Draw-to-flash lag
   5.9, 6.3, 6.3, 6.7, 6.7, 6.1 game frames (README's draw + 6/7): consistent, no drift beyond +-1 frame.
   Of the 192 hypotheses (coin phase 0..47, step/coin order around the shimmer), 4 match, and they are the same
   draw sequence with the frame boundary labelled differently. The same search on random seeds: 1 of 2000 matches.
3. Shimmer 1 (coin visible 229 frames): 2 of 2 shines predicted (capture 423-425 seen 423, 663-665 seen 664),
   6 quiet draws quiet; weak on its own (73 of 1000 random seeds also match), but it is chained to shimmer 2 by (1).

**Frame-start seed / "1 draw into the frame":** the coin data fix the *sequence* of draws after the shimmer (exactly
one step per frame, plus the coin; no other per-frame draws on the menu) but not where the frame boundary sits
relative to the shimmer: "[step, coin?, shimmer]" and "[coin?, shimmer, step]" give identical draw sequences. With
the emulator's "1 draw into the frame" (`shimmer_probe.py`) the frame-start seeds are 0xB71482B1 (shimmer 2) and
0x8E917B49 (shimmer 1); without it they are the states above. Not resolved on hardware.

Coin detector: the `shared/coin_detect` colour tests on a fixed box (1080,48,44x48 in this 1280x720 layout); flash
onset = white share above max(2%, 4x its 97th percentile); visibility = gold share > 30%.
