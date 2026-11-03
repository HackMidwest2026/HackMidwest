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
| `aura_tmpl.py`, `aura_tmpl.npz` | section 8: star-sprite coverage templates per size from glide64 single-star renders, sprite offsets |
| `aura_mf.py` | section 8: game frames by content, kNN background, noise map, rotated templates, FFT matched filter |
| `aura_table.py` | section 8: camera, restart likelihood table, missing logic frames, 16-part table, readings |
| `aura_register.py` | section 8: emulator route camera registered onto a clip's background |
| `aura_lock2.c` | section 8: frame-exact seed search with unread restarts (wildcards) and unordered same-frame draws |
| `aura_confirm.py` | section 8: coin shines and lightning predicted from a lock vs the same footage |
| `aura_capsim.py`, `aura_syncheck.py` | section 8: emulator renders -> simulated console capture; truth comparison |
| `aura_run.sh` | section 8: the whole chain on one prepared stretch |

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

## 7. Real footage, Nov 2 (three console clips; not committed)
Clips: A = 14:57 (17 s, Peach Beam turn), B = 15:00 (36 s, Peach Beam turn then Bowser's turn and two more turns,
input display), C = 15:24 (39 s, about 15 s still in the menu, then the Peach Beam turn). New scripts:
`aura_detect.py` (star blobs, tracks, joint fit; long-stretch mode with a rolling median and a mask of Bowser's body),
`aura_realobs.py` / `aura_parts.py` (restarts from tracks; clustering into the 16 parts), `aura_relock.c` (seed search
that needs no frame bookkeeping, see its header), `clip_timeline.py` (status bar on/off, game frames), `clip_bolts.py`
(sky-bolt onsets).

**Result: no real lock.** What was tried and why it fails so far:
- **Detection.** Stars are found as bright blobs against a per-pixel median. Over Bowser's body that is mostly junk:
  his colour cycling and idle animation make bright edges. With his body masked out (clip C, 448 game frames) the
  tracker keeps 92 tracks (5+ frames), and 58 of them fit the motion model within 4 px. That is about 16% of the
  ~358 restarts in the stretch.
- **The tracks do follow the model.** Track starts cluster in 20-frame phase (residues 7-14 and 16-19 hold most;
  3-5 are empty), and the earlier clip still gives the -2 deg/frame fit. But per-track speed and restart frame
  trade off in the fit (v scatters about 0.4). So the (phase, speed) clusters that would identify the 16 parts get
  only 1-4 restarts each instead of about 22, and the frame-exact model cannot be set up from this footage yet.
- **Search without bookkeeping** (`aura_relock.c`): each restart (frame, angle) is placed at an LCG offset of about
  1.84 x its frame difference from the anchor, +-(6 + df/8), angle +-6 deg, and k must rise with frame
  consistently.
  - Synthetic check: 15 observations (half the restarts kept, +-3 deg, +-1 frame) gave the true seed the top
    score, 15/15, tied only with the same stream shifted 2 steps.
  - On real data (clip C's densest 70-frame window: 19 restarts; clip A's still stretch: 19) the best chain is
    17/19. That is the same as with the observed angles replaced by random ones (two null runs: 17/19 and 17/19).
  - **So the real readings carry no detectable seed information at this precision.** The likely error sources: the
    frame of each restart (+-1 or more), the angle bias from the sprite offset and the camera fit (ky came out 4.4-5.1
    against 5.35 from the registration), and the junk tracks that survive.
- **Needed next:** a detector that matches the star sprite (template, size class) instead of blobs; the restart
  frame from the alpha ramp (first visible frame); and a full 20-frame part table from a longer still stretch, so the
  frame-exact `aura_lock.c` can be used with wildcards for unseen restarts.

**Confirmed on console without a lock:**
- **Sky lightning schedule** (`clip_bolts.py`, clip C still stretch): onsets at game frames 11, 72, 133, 142, 230,
  289, 361 are the 60/60/10/90/60/(60 missed)/10 waits of the 220 loop within 1-2 frames (frame counting is by
  content, so lag frames or static frames shift it). There are two extra onsets (275, 404), probably low-loop bolts
  showing.
- **Peach Beam turn length:** bar off (target confirm) -> bar back up (partner menu) is **13.450, 13.450 and 13.467 s**
  in clips A, B and C (403-404 frames at 29.97 Hz; 389-392 frames counted by content). The emulator run with A every
  25 frames for the text takes 448 frames from the A press to the partner menu. The difference fits the remark text
  being advanced faster by the runner.
- **Aura end:** the beam column hits Bowser at about 29.0 s in clip C (bar off at 19.0 s), and the star outlines are
  gone from about 29.5 s (fade 16 frames). That is about +315 frames by time after the bar went off, against +295
  after the A press in the emulator. The two are consistent only to within the confirm-versus-bar offset and lag,
  which were not measured.
- **Post-beam gap in steps:** in the emulator, aura end -> partner menu is always 153 frames and **4,034-4,201 RNG
  steps** (8 seeds). The Peach Beam itself is 4,980-5,079 steps from the A press to the aura's end. The sparkles
  (`misc_particles`) draw about 17 times per frame, nothing of which is readable. On console only the frame length
  can be measured (above); the step count needs a lock on both sides, which was not achieved.
- **Clip B later turns** (bar timeline): bar up 14.85-24.13 s (partner turn and Bowser's turn start), off to 29.90,
  up to 31.90, off to 35.02. Bowser's attack choice could not be checked against a prediction (no lock).

## 8. Matched-filter detector and a real-footage lock (Nov 2)
**Bottom line.**
- **Clip C (15:24) locks.** The stretch is the menu at 0.5-18.4 s: 530 footage game frames, which are 535 logic
  frames. The state after the aura draw of logic frame 1 (capture 0.533 s) is **`7a1af9b7`**, so gRandSeed at the end
  of that frame is **`2422e234`**. Other values:
  - sky-bolt phase 158, low-bolt phase 68, first coin draw on frame 15 (frame numbers as below);
  - gRandSeed at the end of the stretch (logic frame 534, capture 18.37 s) is **`7ed76b7d`**.
- **Scores.** The lock matches **396 of 412** read restarts (`aura_run.sh` from scratch). One hypothesis survives out of 83.5 M anchor states x
  1.4 M phase hypotheses. With every reading replaced by a random angle, the same search scores at best **32 / 411** (80 anchor states x 1.4 M hypotheses each, scored over the whole stretch).
  - Anchoring on logic frame 14 or 26 instead gives the same RNG stream.
- **Confirmed independently by the coin.** The aura readings choose the coin's phase but never see a coin value.
  - The lock predicts 18 coin draws, 4 of them shines (93, 78, 98, 77).
  - All 4 flash in the HUD exactly 5 frames later, which is the lag calibrated in the emulator. No flash is unpredicted.
  - 0 of 300 random states, each with its best coin phase, do that.
- **The lightning fits.** The 9 predicted sky bolts all have a purple onset 2-3 frames later, and all 12 onsets are
  explained by the predicted sky and low bolts (+2..4).
  - The console lag is 2 frames shorter than glide64's +4.
  - A random sky phase with its best lag window gets 9/9 in 2.9% of draws, so this check is weaker than the coin.
- **Still footage needed.** With the whole chain, part table included, **4 s** locks (70/81 reads), 5 s also gives the
  bolt phases, and 3 s does not lock. With a part table already known, 1 s of readings after the anchor is unique
  (23/23 against at best 10/23).
- **Secondary clips:**
  - A (14:57) and B (15:00) have only about 1.3 s of aura menu before the Peach Beam turn. They do not lock: best
    7/17 and 9/20, flat like random.
  - D (14:47) has 1.2-1.5 s menus between Charges (other RNG, moving camera). Too few reads; no lock.

### Pipeline (`sh aura_run.sh PRE [RENDER_DIR]` after `aura_table.py prep CLIP T0 T1 PRE`)
1. **Game frames** (`aura_mf.prep`):
   - A capture frame is a new game frame when its mean |diff| is > 1.2. The 2-3 copies of a game frame are averaged.
   - **Encoder keyframes** (x264 GOP 250) re-encode a duplicate copy differently enough (|diff| about 1.5) to look
     like a new frame. This happened twice in clip C. A keyframe that would start a 1-copy game frame is merged.
2. **Background** (`aura_mf.background`):
   - Per game frame: the per-pixel median of the 12 most similar other frames (trimmed |diff| over Bowser's box,
     frames within ±3 excluded).
   - Bowser's idle animation and colour cycle repeat about every 36 game frames, so the neighbours share pose and
     colour phase, and the stars drop out.
   - The noise sigma is the per-pixel MAD over time (high on the blue flames), floored per frame by a local robust
     scale, which kills regions where the model failed (menu wheel turning).
   - The SNR scale is calibrated on random positions (the capture noise is spatially correlated: x2.0-2.2).
3. **Templates** (`aura_tmpl.py`):
   - Single-star glide64 renders (other parts hidden by a labelled DIAGNOSTIC counter write), averaged in the
     sprite's own frame, one per size.
   - Two corrections to section 3:
     - the glide64 screenshot after frame f shows frame f - 1;
     - the sprite centre sits **5.88 x size units** further out along the radius than the model point (plus 0.82 x
       size tangential): the display list's vertices are offset and scaled with the size.
   - The route camera is exactly a plane homography: 0.000 px rms on 200 frames of RAM positions. In 320x240 terms it
     is 1.594 / 1.580 px per unit with a small shear and pitch. Section 3's 1.70 / 1.61 came from centroids that
     include the sprite offset.
   - In the capture the templates are rotated in 4° bins (5-fold symmetric), blurred (sigma 1.4 x 1.2 px) and made
     zero-mean over a disk, so broad blobs (colour-flash edges, menu bubble) give no response.
4. **Matched filter.** Per frame, FFT correlations give for every size and rotation
   N = sum c R (W - B) / sigma^2 and D = sum c^2 (W - B)^2 / sigma^2. The star is drawn as an alpha blend of white W
   over the background B.
5. **Restart table** (`aura_table.py table` / `terms`):
   - Every hypothesis (restart frame f0, speed v in 0.6..2.6, size, draw A in 0..359) is scored over its 19 visible
     frames, using the decomp's model: radius 10 + v (t+1), angle A - 2(t+1), sprite rotation = angle, alpha sin(9t).
   - The per-frame term is a bounded GLRT: amplitude free within 0.4-1.6 x alpha x a per-size gain, capped at 2x a
     perfect star's term, floored at -6.
   - A fixed amplitude fails because the real sprite contrast is about 0.6 / 1.0-1.2 / 1.1-1.3 of the template for
     sizes 1.0 / 0.7 / 0.4.
6. **Camera** (`cam`, `scan`, `refine`, `aura_register.py`):
   - Peak tracks give a first camera.
   - The radius-vs-time fit trades the camera scale against the restart frame: a camera 5% small fits every star one
     frame early with a faster speed, and on the synthetic run that wrong basin gave no lock. A scale scan on the
     table evidence picks the basin.
   - Refinement from the part table (sprite peaks, robust least squares, 6 camera parameters, integer f0, grid v)
     settles it.
   - On clip C the emulator's menu background, passed through the capture model, registers onto the clip's
     background at **scale 1.00** (correlation 0.895), shifted (-1, -6) px. **The console camera is the emulator's
     route camera.** The refinement got within 1.5% of it, and the lock uses the registered camera.
7. **Missing logic frames** (`steps`). This was the cause of the earlier failure (section 7).
   - On the console the 20-frame star cycle spans about 19.8 footage frames. Some logic frames never show as a picture
     of their own: in clip C 5 of them in 535, before footage frames 60, 166, 273, 368 and 450 (one per 80-110 frames).
   - The triple-copy frames do not mark them. They show only in the stars: every part's best restart frame drifts by
     -1 at each one.
   - First guess: a monotone step function (DP) on the drift. Then the positions are optimized on the table evidence,
     with the per-frame terms stored once (`PRE_F.npy`), and the table is rebuilt on logic frames.
   - Without this the part table comes out with duplicated stars and wrong sizes, and nothing locks.
8. **Part table** (`parts`):
   - Greedy picks on the median over cycles of the best restart score.
   - A pick masks every hypothesis whose sprite path overlaps one of its restarts (12 px, ±6 frames).
   - Size quota from the decomp: part i has scale 1 - (i mod 3) x 0.3, so 5 x 1.0, 6 x 0.7, 5 x 0.4.
   - Clip C: 16 parts, restart pattern `01100012010210111121` (not the route state's: the phases are drawn at creation).
9. **Search** (`aura_lock2.c`):
   - Anchor: a frame with one read restart. Its ±3° interval gives 83.5 M states. Each is filtered on the next 8 reads
     (6 must match at their nominal LCG offset plus 0-2 inserted bolt/coin draws).
   - The survivors get every sky phase (220) x low phase (130) x coin frame (48), scored over the whole stretch.
   - Restarts on one frame are matched as a set, since the part index order is not known.
   - Unread restarts are wildcards: they draw but are not scored.

### Validation on the emulator (known seed)
- **Setup:**
  - `boss_2304_route_menu.st`, seed 5eed0fb2, 560 frames rendered with glide64;
  - `aura_capsim.py` (S-Video model of `readouts/shimmer_svideo.py`, the OBS layout, the console's 2/3/1-copy cadence,
    x264);
  - then the same chain with no truth input.
- **Results:**
  - camera (1027.3, 366.1, 5.194, 5.222) against the true (1027.5, 365.9, 5.203, 5.245);
  - 16 / 16 parts (phase, speed, size);
  - readings within ±1° for 90% (the rest are mostly off by > 10°: overlaps);
  - the lock state is the emulator's seed (adv(e11eab6e) = 5bfe5c67 = the seed at the end of that frame);
  - sky / low / coin phases 30 / 20 / 29 = the emulator's 29 / 19 / 28 + the one-frame screenshot lag;
  - no missing logic frames found (there are none: the capture simulation shows every frame);
  - 426 / 432 reads against at best 39 / 432 with random angles;
  - coin 4 / 4 shines at +5, bolts at +4.
- `aura_lock2.c` alone on readings taken from RAM (half the restarts, ±1°) gives the true state, 223 / 223.

### Verified / not verified
- **Verified on the console clip C:**
  - a unique lock, with a 364-read margin over random angles;
  - the same stream from three anchors;
  - the coin shines (4 / 4, exact lag, no false or missed);
  - the lightning (9 / 9 sky, 12 / 12 onsets explained, at a lag 2 frames shorter than glide64's);
  - the console camera = the emulator's route camera.
- **Not verified:**
  - Why logic frames go missing on the console. The positions are fitted from the stars, not from anything in the
    capture.
  - The lock's bolt lag (+2..3) was not fixed in advance.
  - The secondary clips do not lock: too little aura menu.
  - Nothing after the Peach Beam (section 4's carry is still not modelled).
