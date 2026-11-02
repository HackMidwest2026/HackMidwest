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
- Effects mostly use `effect_rand_int`, a separate PRNG (`effect_utils.c`) that never touches gRandSeed.
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
