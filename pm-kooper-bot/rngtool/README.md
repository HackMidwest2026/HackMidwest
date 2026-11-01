# Time Out Timer (Hallway Bowser RNG manipulation)

`timeout_timer.html` is the tool (single file; open it in a browser). Built from `page_template.html` with
`pmrng_core.js` spliced in at `/*CORE*/`.

- `pmrng_core.js`: RNG model, coin pattern from shine taps, seed search, resync, Time Out planner.
- `timeout_model.py`: the same Time Out model in Python (validated frame by frame against the emulator).
- `tool_cli.js`: Node front end used by `e2e_timeout.py`.
- `e2e_timeout.py SEED`: emulator end-to-end test (watch in the turn-1 menu, find the seed, play turn 1 with random
  waits, resync in the turn-2 menu, plan, confirm on the planned frame). Seeds 2468ace0, 13579bdf, 0f0f1e1e: all WORKED.

Model (JP): seed*0x5D588B65+1, one step per frame. Status-bar coin draws rand_int(100) every 24 frames (48 after a
shine, which happens on 70+). Time Out confirm on frame C: effect draws on C+24, C+73, C+112, roll first on C+386,
works if <= 30. In-frame order: battle script (roll, effect spawns), coin, per-frame step.

## Automatic mode (OBS Virtual Camera)

`timeout_timer_standalone.html` opened from disk in Chrome/Edge reads the OBS Virtual Camera: a box on the
status-bar coin detects every shine (white flash 4-6% of the box on draw+6/+7 vs <=1% for normal spins), segments
break automatically when the coin is hidden or a shine stops fitting the locked seed, the seed search and resyncs run
by themselves, and a saved reference of Time Out's target screen triggers the plan + beeps. Locks need evidence
margins (32+6 bits for the seed, log2(window)+7 bits for a resync).

Tests (headless Chrome with emulator footage as a fake camera, `test_cam.js`, `test_cam2.js`): seed locked from
video alone after 13 shines; full turn-1 -> turn-2 -> target-screen footage: both locks on the true seed trajectory,
plan anchored on the true seed, and the planned confirm (frame 2784+170) made Time Out work in the emulator
(`verify_planned_confirm.py`).

## Power Bounce: does action-command timing change the cap? (No.)
`pb_timing_test.py` (debug core) maps each bounce's action-command window vs Hallway Bowser and replays the chain
pressing on every frame of every window. All 34 variants gave identical cap rolls, end frame and RNG seed. The
cap roll for loop bounce k is the `rand_int(100)` on confirm + 73 + 26(k-1) frames (chance 200 x 0.65^k vs the
roll), so like Time Out the whole Power Bounce outcome is fixed by the frame of the target-confirm A, as long as
every action command is hit. Pressing early (before the window) still drops the bounce.

## OBS notes (after a user report of OBS freezing)
The seed search now runs on 2 threads by default (max half the cores) so OBS keeps its CPU; the camera source only
keeps the OBS Virtual Camera open (never a capture card OBS is using); the default source is an OBS windowed
projector captured with getDisplayMedia; frames are read from the track (MediaStreamTrackProcessor) when Chrome stops
video callbacks for a hidden window; the preview keeps the video's aspect ratio. `test_cam3.js` (MODE=vfc and
MODE=bg, emulator footage): both locked the true seed after 16-17 shines with the 2-thread search.

## Press readout and frame-rate fit
- After each confirm the page measures the frame the press landed on: the クッパ name box (top-left of the target
  screen) disappears from the video 2 game frames after the confirm frame (emulator). The same video path carries the
  shines, so capture lag cancels. It shows early/late per press and suggests a Fine offset after 3 presses.
- The console's frame length is fitted from the shine times (least squares over the longest locked segment) instead
  of assuming 59.94 Hz: a real N64 in 240p runs near 59.83 Hz, worth 1-2 frames by the press.
- `test_press_sim.js` feeds the recorded frames (`rec_video_confirm.py`) to the page with exact timestamps:
  at 33.430 and 33.367 ms per frame the fitted rate matches to 4 decimals and the measured confirm frame is exact (54).
- The strip view no longer jitters: "now" stays fixed while scrolling, and ticks are relative to now (or the press).

## Fight profiles (Fight selector on the page)
`pmrng_core.js` `PROFILES`: each profile lists the rolls one confirm decides (frames after the confirm), extra effect
draws, and how many frames after the confirm the saved target-screen box changes (press check).
- `timeout`: Hallway Bowser, Time Out (as above).
- `dup4`: 4 Duplighosts (battle 0x2402), Bombette out, T1 do nothing / do nothing. The confirm is Bombette's
  "do nothing" (Strategies: up 1, A, down 1, A). Each Duplighost rolls RandInt(1000) < 600 to copy on the enemy turn
  at confirm + 13, 110, 207, 304 (all-copy path; no other draws besides the coin). Model matched the emulator on 13
  seeds (`dup_rolls_log.py`). About 13% of frames work, mostly single frames; runs of 2 are common, so the planner
  takes 2-frame windows. Target screen: Bombette's Strategies panel (it disappears 3 frames after the confirm).
- `e2e_dup.py SEED` (debug core): seed from coin shines in Mario's menu, menu path, resync, planned confirm:
  seeds 2468ace0, 13579bdf, 0f0f1e1e: all 4 copied.
- `../boss_battle_start_setup.py`: battle setup with PARTNER / BRANK / BADGES (DIAGNOSTIC).
- Jr. Troopa (battle 0x0207; Bombette Super, Ultra Boots, 10 HP/10 FP; badges Super Jump Charge, Power Bounce,
  Close Call, Speedy Spin). Close Call = rand_int(100) < 30 when his attack hits Mario under 6 HP (he only targets
  Mario; base form is Leap only, no attack-choice roll; he stays in base form through T5 on this route).
  - `jrcc_bomb` (T3, Bombette's Bomb confirm): bomb-explosion draws at +73 (8x359, 360), roll at +179. The mash meter
    speed does not matter (same roll with mash every 2/3/5 frames, even when damage changed).
  - `jrcc_syrup` (T4, Maple Syrup confirm): sparkles at +118 ([359,10,10] x10), roll at +163.
  - `jrcc_nothing` (T5, Bombette's do nothing): roll at +26.
  - `jrpb6` (T6, Power Bounce confirm): cap rolls at +78/105/132/159 must be <= 140/98/68/47 (6+ hits); hit-effect
    draws at +52/79/106/133. With three charges, 6 hits kill him (5 leave 4 HP for Bombette's Bomb). AC windows
    46-51, 73-78, 101-105, 129-132, 157-159; any frame in a window gives the same rolls (34 variants).
  Each model matched the emulator on every roll of 7-9 seeds. `e2e_jr.py PROFILE SEED`: 2 seeds x 4 profiles, all worked.
  The page's "Jr. Troopa route" follows every target screen of the route and advances after each confirm.
  Scripts: `jr_*.py` (route building in the emulator, roll logs).
- Route update (two Maple Syrups, no Whacka's Bump): Mario stays at 2 HP from T1, so T2 is also a Close Call turn
  (Bombette Bomb, then Maple Syrup = `jrcc_syrup`, same model: matched 9 seeds; e2e 3/3 worked).
- Guarding does not matter: the Close Call roll was identical with no guard, mashing A, and single presses at 7
  different frames before the hit (T2 and T5 states; `jr_cclog.py` with GUARD=...).
- `dup3` (3+ of 4 Duplighosts copy): branching model (a failed copy = tackle, 8 x rand(359) at +34, next roll +78
  instead of +97). It reproduced every roll of 11 logged seeds (frames and values, including 1- and 2-fail paths);
  `PROFILE=dup3 e2e_dup.py`: 4/4 worked (two with exactly 3 copies, one after a failed second ghost).
  About half of all frames give 3+ copies (vs ~14% for all 4).
