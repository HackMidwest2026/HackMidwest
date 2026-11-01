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
- Duplighosts 3+: the beeps aim at a frame where all 4 copy, inside a 3+ window (earliest such window in the next
  minute; the all-4 frame nearest its middle). e2e (PROFILE=dup3): 6/6 got all four copies.
- Test-harness fix: e2e_dup.py / e2e_jr.py pressed one frame after the planned model frame (a "+1" copied from the
  Time Out test, where it meant "one frame into the window"). Mapping is model frame t = the emulator step numbered
  L + t. Found when aiming at single all-4 frames (`e2e_dup_framecheck.py` compares emulator vs model per frame:
  identical once aligned). Re-run with the fix: dup3 6/6, dup4 3/3, Jr. Troopa T2-T6 5/5 worked.
- The all-4 target must have both neighbours giving 3+ (`aim4` in pmrng_core.js). e2e with the press on the target
  and one frame early/late (SHIFT=0/-1/+1, 4 seeds each): exact = 4 copies 4/4; one frame off = 3 or 4 copies 8/8.
- Jr. Troopa T6: the route step uses `jrpb5` (5+ hits: first three cap rolls pass) and aims at a 6+ frame whose
  neighbours both give 5+ (`aimTop`). 5 hits leave him at 4 HP for Bombette's Bomb. e2e_jr.py jrpb5 with
  SHIFT=0/-1/+1 (4 seeds each): exact = 6+ hits (Jr. Troopa at 0 HP) 4/4; one frame off = 5 or 6+ hits 8/8.

## First lock across gaps (coin hidden by room loads)

Before a lock, every stretch of visible coin (3+ shines) is kept instead of thrown away when the coin disappears.
Measured in Bowser's Castle (`kpa_100 -> kpa_03`, `kpa_133 -> kpa_49`, emulator, frame by frame): through a room
transition the RNG keeps stepping once per game frame and the coin keeps drawing on its 24/48-frame schedule; a load
only runs ~5 extra fast frames. So a hidden stretch is the same coin process continuing, and only the exact frame count
is open: the page searches E-30..E+60 frames (E from the tap times), about 2 bits per gap. `searchChain` scans the
strongest stretch over all seeds and checks the others across their gaps (backwards through the coin's branching
history, forwards by simulation); `extendCands` carries candidates into the next stretch. Lock needs 38 bits + the gap
costs. Rooms with their own RNG users (the jail `kpa_17` adds ~25%) break the chain, as they break a single stretch;
the page then drops the older stretches. Tests: `test_chain_core.js` (core, `full` = all 2^32 seeds, ~18 s single
thread), `test_chain_page.js` (page, 15 s on / 10 s off: locks the true seed in the 4th-5th stretch).

The endgame route shows one step per turn: the turn's last input, or the starred press when it comes first.

## Carrying the seed through Jr. Troopa's turns (no shines between Close Calls)

Measured with `jr_turnlog.py` (6 runs from the T3 Bomb target screen to T6, random seeds and confirm delays; DIAGNOSTIC
seed writes before each starred press force the Close Call): from each confirm, the turn's draws land on the same frames
with the same ranges every time (`turns_jr.json`, built by `jr_turnsched.py`): T3 Bomb (8 x rand(359) + rand(360) after
the coin at +73, Close Call roll +179), T4 Bomb (same explosion), T4 Maple Syrup (30 at +118, roll +163), T5 Do Nothing
(roll +26), and T2's Whacka's Bump with Jr. Troopa's T2 turn (66 draws at +118, 10 at +190; `jr_t2log.py`, 6 runs with no
seed writes at all, T2 Bomb -> T3 Bomb target screen). The Super Charge is two `energy_in_out` sparkle effects (created +13/+16, removed +58/+61): each of 10 parts
gets rand(10) speed and a rand(10) start phase, and redraws rand(359) when its 10-frame counter wraps; `jr_chargefit.py`
fits this exactly. The coin keeps its 24/48 schedule throughout (a one-frame skip seen in the logs came from the logger's
own savestate reload). `test_turns.js`: from the seed at the T3 confirm and the confirm frames alone, every frame's seed
matches the game in all 6 runs.

On the page: each planned press (and the turn's other input, seen on its own saved target screen: the Charge's "target
on Mario", the Bomb's "target on Jr. Troopa") is an event on the locked segment; plans start from the first coin draw
after the simulated turns (`R.baseAfter`). New shines are checked against the simulated shines (the coin shines unseen
during attacks). Guards: a planned press on a failing frame, or an unseen earlier input, stops the carry until shines
find the seed again; and every confirm the page sees is logged, so a plan never starts from shines older than an input it
cannot simulate (T1's Bomb and Jr. Troopa's T1 turn, any other fight's inputs). Tests: `test_carry_page.js` (3 seeds x T3/T4/T5: every planned Close Call lands with no shines
after the lock; SHINES=1: menu shines accepted), `test_carry_guard.js`.

## Bowser's Castle rooms (route to the Duplighosts)

`kpa_roomsteps.py` / `kpa_roomrng.py`: per room, any RNG user besides the frame step and the coin breaks a first lock.
Clean: kpa_82 (quiz), kpa_33 (stair hall, Save Block), kpa_52 entrance side, kpa_08, kpa_100 (key), kpa_40/41 (maze).
Not clean: kpa_61 (room script), kpa_52 near its enemies, kpa_102 (fire room), kpa_53 (torches: 12 draws every 50
frames). The Duplighost battle load itself is clean (22 frames, no extra draws).

## Keeping the lock through screens with other random numbers

After a lock, shines that fit nowhere near the expected position (level-up confetti, kpa_61's Magikoopas, the fire room,
the Duplighost torches, a stray C-up) no longer drop the lock: the page keeps only the newest shines of that stretch and
waits for ones that fit. Only after 12+ shines in a row that never fit does it search all seeds with them in the
background: one clean fit means the RNG really was replaced (savestate, reset, retried fight) and the page follows it;
none means the stretch is ignored. Tests: `test_dirty.js`, `test_lost.js`.
