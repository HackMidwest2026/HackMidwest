# Final Bowser phase 2: Bowser's star aura as an RNG readout (JP, emulator + one real-console clip)

**Bottom line.**
- The early-phase-2 effect at 0xE00D6838 is Bowser's star aura: the white star outlines that fly out of him. The blue
  flames are a different effect and use no RNG.
- The star aura is readable enough for an instant lock: about 0.6-0.9 s of watching locks the seed in simulation.
- It does not set up the bounce by itself. The aura is removed by the Peach Beam, which is the only thing that makes
  Bowser damageable. So the bounce always comes at least one Bowser turn later.
- Between the last aura frame and the next Mario menu there are 4,658-5,685 RNG steps from effects and AI that are not
  modelled (8 seeds).
- With an exact lock carried to the target screen, a 1 s beep window gives 5.34 expected bounces (1-frame press error)
  or 6.28 (exact press), against 4.13 blind. If the carry leaves 100+ candidates, it is back to blind.

## Files
| file | what |
|---|---|
| `aura_probe.py` | finds the aura in RAM, logs every rand_int per frame, checks the per-part draw rule against RAM |
| `aura_model.py` | frame model (bolts > coin > aura > step) + `check` mode against the emulator over several seeds |
| `aura_render.py`, `aura_geom.py` | glide64 renders; projects each star from RAM; single-star renders to fit the screen geometry |
| `aura_svideo.py`, `bg_menu_320.png` | S-Video simulation of one star's angle (reuses `readouts/shimmer_svideo.py`) |
| `aura_lock.c`, `aura_lockdemo.py` | seed search from noisy star angles; trials against the model |
| `aura_carry.py` | Peach Beam -> Lakilester -> Bowser's turn -> T2 menu, every draw by caller, several seeds |
| `aura_payoff.js` | bounce payoff of a lock / N candidates with `powerbounce/fb2model.js` |
| `aura_clip.py` | real-console recording: star tracks fitted with the aura's motion |

Emulator scripts are run from `/tmp/claude-0/pm/bot1` (debug core `M64P_DBG=1`; glide64 on `DISPLAY` for renders).
Every DIAGNOSTIC RAM write is labelled in the code:
- the seed is written after a load;
- `aura_geom.py` hides the other stars to measure one.

## 1. What it is
- **Effect:** `energy_in_out` with **arg0 = 4** (`fx_energy_in_out(4, ..., 1.2, 0)`), created by
  `add_part_decor_radiating_stars`. That is `ACTOR_DECORATION_RADIAL_STAR_EMITTER`, decoration slot 1 of Bowser's main
  part.
- **Parts:** 17. Part 0 is the header (position = Bowser + 41 x 1.5 up, scale 1.2 x 1.5); parts 1-16 are stars.
- **Each star:**
  - period 20: `unk_14` counts 0..19, then restarts with `unk_3C = rand_int(359)`;
  - speed `rand_int(10)*0.2+0.6` (0.6-2.6 units/frame outward), fixed;
  - spin `unk_40 = -2` deg/frame;
  - size 1.0 / 0.7 / 0.4 by index mod 3;
  - alpha `sin(9 t deg)`;
  - drawn with `RENDER_MODE_CLOUD_NO_ZCMP`, so it is drawn over Bowser and not hidden by him.
- **Not the blue flames.** The flames are `ACTOR_DECORATION_BOWSER_AURA` (effect `aura`), which has no rand call.
- **Trigger** (`final_bowser_2.c`): `EVS_Init` adds it at phase-2 creation. In `boss_2304_route_start` its counter is
  already 597 frames when the first turn begins, so it starts during the phase 1 -> 2 transition.
- **Duration:**
  - It runs continuously, on every turn, through menus, actions and Bowser's attacks.
  - It ends only on `EVENT_PEACH_BEAM`: `RemoveActorDecoration` dismisses it and it updates for 16 more frames.
  - Measured: the last aura update is **+295 frames after the Peach Beam's target confirm** (8/8 seeds).
  - `EVS_StarRodCast` re-adds it later: Bowser re-enchants with chance 0 / 0 / 15% / 75% at 1 / 2 / 3 / 4+ turns
    after the beam.
- **Enchanted means defense 99**, so a Power Bounce while the aura is up does nothing. The bounce turn never has the
  aura: Peach Beam turn -> Bowser's turn -> the bounce turn at the earliest.

## 2. Draws (verified)
- Per frame:
  1. lightning `rand_int(359)` per bolt (sky loop 60/10/90/60 = 220, low loop 5/30/5/90 = 130; `kkj_02` stage script);
  2. the coin `rand_int(100)`;
  3. the aura: every star whose counter wraps, in index order 1..16, one `rand_int(359)` each;
  4. the step.
- So the aura comes after the lightning and the coin.
- The 16 stars' restart phases are fixed at creation. In the route state they give the 20-frame count pattern
  `21010201310011101010`: 16 draws per 20 frames, with one 3-draw frame per cycle.
- `aura_probe.py`: 300/300 frames, every aura draw equals the new `unk_3C` in RAM.
- `aura_model.py check boss_2304_route_menu.st 2000` with 5 seeds (1234abcd, 9e3779b9, 00000001, deadbeef, 5eed0fb2):
  - 2000/2000 frames' end seed predicted exactly from the seed alone, for every seed;
  - 1600/1600 angles exact;
  - frames with a bolt and a coin together were included.
- The lightning phases (sky 29, low 19) were equal mod 5 again.

## 3. Readability
- **Geometry** (`aura_geom.py`, single stars, glide64; route menu camera):
  - the screen angle of a star about the aura centre (232, 117) in 320x240 equals `unk_3C` (0 = right,
    counter-clockwise) within +-2 deg, with a constant small bias by sprite size;
  - the radius is 1.70 px/unit horizontally and 1.61 vertically;
  - big stars' centroids sit about 4-6 units further out than the model point, from the sprite's own offset; that is
    a calibration constant;
  - a star shows for about 12-14 of its 20 frames, from about 20 px to about 100 px from the centre (320 scale);
  - the sprite also rotates with the angle.
- **S-Video** (`aura_svideo.py`; same capture model as `readouts/`: 4.2 MHz luma, 1.3 MHz chroma, noise Y 2 / C 3;
  star over the real menu background):
  - 8.49 of 8.49 bits (the exact integer) for every size (1.0 / 0.7 / 0.4), speed (0.6 / 2.6), and angle over the sky
    or over Bowser (3 trials each);
  - this assumes an exact page model, as in the earlier readout studies. The real limits are overlaps (about 13 stars
    on screen), the camera (it moves in cutscenes and actions; static in menus), the sprite offset and capture
    cadence slips, not the capture bandwidth.
- **Bits per second:** 16 draws / 20 frames = 24 draws/s. Even at +-6 deg reading error (about 4.7 bits/draw) that
  is about 110 bits/s, against about 1 bit/s from the coin.
- **Lock** (`aura_lock.c` via `aura_lockdemo.py`):
  - What the search is told: the star phases (one 20-frame cycle shows each star's restart frame) and the sky-bolt
    phase.
  - What it searches: the seed, the low-bolt phase (130) and the coin's next frame (48).
  - The anchor is the cycle's 3-draw frame: about 11,500 seeds match at +-2 deg, enumerated from the angle interval
    without a 2^32 loop.
  - Results, watched from a random frame (35 trials, about 1-15 s of CPU each):

    | reading error | trials locked on the true seed | median frames to unique | max frames to unique |
    |---|---|---|---|
    | +-2 deg | 20/20 | 18 | 24 |
    | +-4 deg | 10/10 | 20 | 27 |
    | +-6 deg | 5/5 | 18 | 27 (0.9 s) |

## 4. Payoff
- **Carry** (`aura_carry.py`; 8 seeds; T1 Peach Beam, Lakilester's first move, Bowser's turn with A every 25 frames):
  - aura end -> T2 menu takes 658 / 756 / 975 frames by Bowser's attack (3 branches) and **4,658-5,685 RNG steps**;
  - the draw count also varies within a branch.
- **Draws there that nothing models yet:**
  - `misc_particles` (0xE00E4xxx, the Peach Beam's sparkles): a seed-dependent number of 5-draw particle spawns,
    about 607-625 during the beam and 374-401 after the aura ends;
  - `shimmer_burst` (0xE007xxxx): 411 x 4 draws;
  - Lakilester's aim glow (`energy_in_out` type 0-2);
  - Bowser's AI (evt RandInt 100 / 80 / 60 at 0x802D46E0);
  - a `rand_int(100)` at 0x80266DE4;
  - the hit fireworks (16 x 359);
  - 0x8012978C `rand_int(15)` x 40.
- **So the lock carries exactly to the aura's last frame and no further.** Carrying it needs these measured the way
  Hallway Bowser T1 was (schedules per branch plus the stochastic `misc_particles` logic), then a few coin shines in
  the T2 menu to pick among the remaining candidates. The aura does keep re-locking live during the beam itself
  (it is up until +295), so the reading is fresh right up to the beam's end.
- **Bounce payoff** (`node aura_payoff.js`):
  - setup: frame 0 = arrival on the target screen; the page picks d in [0, 30) (1 s) with the best expected count;
    first hit 13 damage, no aura;
  - the 1,000-candidate row has 40 trials only (noisy);
  - every row has 40-3,000 trials (blind 20,000).

  | information | E[bounces], press 50/25/25 | 6+ | 7+ | 8+ | E, exact press | 6+ | 7+ |
  |---|---|---|---|---|---|---|---|
  | blind | 4.13 | 8.3% | 1.2% | 0.1% | 4.13 | 8.3% | 1.2% |
  | exact lock | **5.34** | 45% | 13.6% | 1.7% | **6.28** | 92% | 32% |
  | 10 candidates | 4.50 | 16% | 3.5% | 0.3% | 4.75 | 22% | 6.0% |
  | 100 | 4.26 | 7.8% | 2.0% | 0.2% | 4.32 | 10% | 2.0% |
  | 1000 | 4.19 | 7.5% | 1.9% | (1.3%) | 4.23 | 10% | 0% |

  So the aura's value depends entirely on the carry: it needs to reach the target screen as an exact seed (or about 10
  candidates) to be worth about +1.2 to +2.2 bounces.

## 5. Real console (one recording, 1280x720 60 fps, S-Video -> GV-USB2; not committed)
- The recording is phase 2 from Bowser's opening line: Mario Super Charge, Goombario Charge, Bowser's Fire Breath,
  Mario KO, Life Shroom.
- The star outlines are clearly visible the whole time (also over Bowser) at about 25-30 capture px per big star.
- **Motion matches the model.** `aura_clip.py` takes 9 distinct game frames with a still camera at 1.15-1.4 s and
  links 4 star tracks. One common centre with every star turning **-2 deg/frame** and moving out linearly fits with
  **2.1 px rms** (about 0.7 N64 px). The same fit with 0 deg/frame gives 4.9 px and +2 deg/frame gives 15.1 px.
  The fitted centre is on Bowser's chest.
- The blue flames flicker but carry no RNG (effect `aura`, no rand). The pink/white flashes are Bowser's Star Rod
  colour cycling (`UpdateEnchantedBowserColors`), not RNG as far as the decomp shows.
- **Timing:** the game advances every 2nd capture frame, with cadence slips. In 120 frames the pairing flipped twice
  (one duplicated or dropped field each time), so the page must find game frames by content, not by counting.
- The opening speech and actions move the camera (zoom-in for the speech, Charge close-ups). Only menu and
  target-screen stretches have the still camera the geometry fit assumes.
- **Not checked on this clip:** the angle = draw mapping (no RAM for a console run), and a lock. The camera in this
  run is not the emulator route state's, so the centre and scale must be fitted per camera preset.

## 6. Recordings that would confirm it
1. **Required:** about 10 s standing still in a phase-2 battle menu (no inputs, star bar up), then Peach Beam with the
   rest of the turn and Bowser's turn, and the next menu. A console run cannot be compared to a known emulator state,
   so the check is self-contained:
   - lock on the stars in the menu, predict the coin shines of the next 10 s and Bowser's AI branch;
   - the shines confirm the lock;
   - the predicted bolt frames confirm the phases.
2. One take of the same menu with the camera untouched for 20+ s, for the geometry fit (centre, scale, sprite offset)
   and the cadence slips.
3. For the carry: 3-5 Peach Beam turns recorded through to the next menu, with the inputs visible (input display on),
   to measure the post-beam schedules on console against the emulator.

## Verified / not verified
- **Verified in the emulator:**
  - effect identity, arg0, per-frame draws and order (5 seeds x 2000 frames exact);
  - the aura's end at Peach Beam +295 (8 seeds);
  - the screen geometry (glide64, single-star renders);
  - the carry's step counts (8 seeds).
- **Verified on the real clip:** the -2 deg/frame radial motion about one centre (4 tracks, 2.1 px rms).
- **Simulation only:** S-Video bits, the lock search (against the verified model), the payoff table.
- **Not verified:**
  - a lock from real footage (no detector built; star overlaps, camera presets, sprite offset);
  - any carry past the Peach Beam (not modelled);
  - `fb2model` in a state after the Peach Beam (it was matched in `fb2_t7like_pb`);
  - glide64 versus real RDP star rendering (the clip looks the same to the eye).
