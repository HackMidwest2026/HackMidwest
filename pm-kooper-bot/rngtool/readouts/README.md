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
- The shimmer's actual colours on hardware (no accurate RDP renderer here; glide64 shows white).
- Whether Final Bowser's early phase-2 effect at 0xE00D6838 (16 draws per 20 frames, see powerbounce/README.md) is the
  same `energy_in_out` ray effect - the same caller address suggests it; if so it is a continuous readout there too.
- Jr. Troopa and the FB phases were not re-checked for Charge-like effects.
