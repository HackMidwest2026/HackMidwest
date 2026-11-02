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

## Hallway Bowser T1 carried to Time Out

`hw1_turnlog.py` / `hw1_guardlog.py` (26 runs from the route start state `boss_2302_route_menu.st`: DIAGNOSTIC setup
Lakilester Super rank, Jump Charge + Power Bounce + Close Call, 10 HP / 15 FP; random seeds, delays and aims; 8 runs
guarding): Charge = the Jr. model. Spiny Flip: an aim sparkle (`energy_in_out`, 10 parts, 20-frame cycle, +39..+119),
impact 8 x rand(359) on a frame that depends on where the reticle ended up (+147..+154 here), then Bowser's AI 44 frames
later (`EVS_UseAttack`): RandInt(80) < 20 Body Slam, else RandInt(60) < 20 Claw Swipe, else Fire Breath. Each attack's
draws were measured, guarded (A 1-3 frames before the hit, `hw1_guardtiming.py`) and not; `test_hw_t1.js`: every frame
of all 26 runs matches. On the page the impact frame and the guard are unknown, so 66 candidates (+138..+170, guard or
not) are simulated; candidates in the same RNG state at the current frame are merged, and each shine in T2's menu drops
the ones that did not predict it. `test_hw_carry.js`: 6 cases (all attacks, guarded or not, impact +141..+163): 1-3
shines, then Time Out planned and STOP in the game every time.

## Re-finding a lock from short stretches

While a lock is being re-found (after a gap with other random numbers), each stretch's candidate positions are carried
across the next clean gap (the coin keeps drawing; `R.extendCands`, E-30..+60 frames) instead of being thrown away when
the coin hides, so short stretches (maze rooms, 2-3 shines each) add up. 2-shine stretches now count for a first lock
too. Rooms measured clean before the quiz room: kpa_133 (flood), kpa_134, kpa_130 (cannon), kpa_112; kpa_113 is not.
`test_relock_short.js`: after an enemy room, only 2-3-shine stretches with 8 s gaps: re-locked on the true seed in all
4 cases (14-18 shines over 6-10 stretches).

Early castle (`kpa_roomride.py`, Lakilester ridden over the lava): kpa_12 and kpa_14 (the two lava rides) and kpa_13
between them are clean, about a minute of coin in one block: the place for the first lock. kpa_111 (Dry Bones) is not.
kpa_11 (the lava room next to the jail, Save Block + island Life Shroom; the route rides it on Lakilester) is clean
once its Koopatrol is defeated (GF_KPA11_Defeated_Guard, as in the route); while it is there its wander AI draws random
numbers every few seconds. The ride is the first-lock spot; the flood rooms + cannon room are the backup.
More rooms (`kpa_roomsteps.py`): kpa_63 (Save Block room after door 1), kpa_118 (room before the key) and kpa_119 (key
room) are clean; kpa_114 (Heart Block room: 12 draws every 50 frames, like the Duplighost room's torches) and kpa_115
are not. "Download session log" saves every shine, gap, lock, plan and press with times (JSON) for analysing a run.

## Torch rooms (Duplighost room kpa_53, Heart Block room kpa_114)

`torch_log.py` (12 runs, 1500 frames): exactly 12 draws every 50 frames, after the coin on shared frames, on a phase set
by the room load. `R.matchesTorch` / `R.resyncTorch` search every start position and all 50 phases; phases that put the
torches in the same gaps between coin draws give the same seed and are kept until later shines split them
(`test_torch_core.js`: the true phase matches in all 12 logs). On the page the torch model is tried when the plain one
finds nothing, before old shines are dropped; a lock there keeps every phase that still fits. Carrying candidates across
a gap is trusted only when the coin was hidden for at most 4 s (a room load with C-up held); after a longer gap (C-up
closed through enemies, a battle) the new stretch must rule out a wrong carried candidate on its own (7 bits).
`test_torch_page.js`: re-locks in the torch room on the true seed (8-11 shines) and after a battle (3/3, no wrong lock).

Long C-up-closed gaps (the ~2-minute quiz cutscene): a lock carries across them with the usual wide re-sync; a near-lock
(a chain that found a few candidates but not yet enough evidence) is carried across too (`R.extendWide`, E-300..+range
steps) instead of being dropped. Dropouts under 1.2 s cost little (+-2 frames) and, while locked, no longer start a
re-sync: the next shines just have to land where the locked seed puts its shines. `test_wide.js` (lava ride with
dropouts, 2-minute quiz, short stretches after): locks during the ride in 4/4 and re-finds the true seed after the quiz.

Item pickups: the status-bar coin icon is never disabled (`inventory.c`), and HUD scripts ignore the item-get time
freeze, so the coin keeps drawing while the bar is hidden for a "You got ..." message; an item block gives its item a
fixed direction, so the pickup itself draws nothing. Dropouts up to 3.5 s therefore keep a lock: under 1.2 s the frame
count is exact (+-2), up to 3.5 s it may include a quick room load (-2..+8; the first shine after it shifts the clock
exactly onto the predicted shine). `test_pickup_lock.js`: a 2 s pickup and a 2.5 s load with 5 fast frames keep the lock
(no re-sync, shift measured as 5).
After Jr. Troopa (STORY 95 states, `kpa_roomsteps.py`): kpa_83, kpa_121, osr_02 (outside Peach's castle) and Peach's
castle kkj_10/11/12/14/15/16/17/18/19/22 are all clean.
Library = kkj_16: the Life Shroom and Power Rush pickups (`kkj16_pickup.py`, DIAGNOSTIC teleport onto the item) add no RNG
draws; the coin keeps drawing through the item-get message. After Hallway Bowser (GFLAGS 1FA,1FB; also 1FA only for the
kkj_23 Bowser-flees scene): kkj_13, kkj_22, kkj_23, kkj_24 and kkj_25 (entry 0, the route's door) are all clean.

Run 3 log (Nov 2): the dungeon glances were mostly 1-2 shines each and never connected (`chainscan.js`: no seed fits
even with wide gap windows, so some shines were missed or doubled); one 1.9 s room load measured 7 frames longer than
the game ran (console load time without game frames). Changes: room-load gap windows reach 12-14 frames below the clock
(still under 24 frames wide, so they cost almost nothing), and once the current stretch alone has 30 bits it is searched
by itself (stopping a running chain search). Replaying the Duplighost-room stretch now locks at 655.7 s instead of 665.3 s.
`test_edges_core.js` covers optional m1/m2 gap constraints in the core (draws seen without a shine at a gap's edges); the
page does not feed them yet.
First lock: C-up closed up to 15 s (CHAIN_GAP) keeps the coin chain with the wide gap window instead of restarting it.
A hand-on-Mario step (cat M, e.g. the Whacka) counts from one frame of its target screen (a quick confirm).

## Emulator "speedrun" of the dungeon C-up rooms (`speedrun/`)

`sr_run.py` plays the Bowser's Castle route rooms in one continuous emulator session (real room loads; DIAGNOSTIC:
each exit is redirected to the next route room and Mario is put back at the entry point before walking out; kpa_11
ridden on Lakilester), presses C-up like a runner and records 640x480 video plus the RNG truth. `sr_crops.py` +
`sr_feed.js` feed it to the page frame by frame on a simulated 29.97 fps clock (Chrome's fake camera ran ~3% slow,
which would skew the page's frame counts); `sr_analyze.py` checks every detection and lock against the truth.
Findings (Nov 2): C-up keeps the status bar up only ~220 frames (7.3 s) and a second press while it is up closes it, so
every look is <= 7 s; detection: 35 of 38 steady shines, no false ones; no lock in the dungeon with the planned room
times (about 1 bit of evidence per second of coin, and closed-C-up rooms restart the chain).
Coin-present fix: the quiz door's speech bubble sat over the coin box and its white counted as "coin on screen" for the
whole quiz (run 3: a 2-minute quiz looked like a 20 s gap with 117 s of coin and no shines). Present now needs the
status bar's tan/gold (with g > 0.6 r, so lava glow does not count); `test_present.js` (emulator frames incl. the quiz).

## Maze rooms -> Duplighost room (Nov 2)

Measured (emulator): kpa_102 between the maze and the Duplighost room has 3 wandering enemies (~3.5 extra RNG steps per
second; 29 in a 9 s crossing; running straight in starts a battle). kpa_53 has no entry cutscene (the Duplighost scene
starts when you talk to "Peach"), but standing near the entrance its torches draw (452 extra steps in 62 s, the torch
model). Run 3's Duplighost-room lock matched the plain coin for 53 s, so where the runner waits the torches did not draw.
Standing still keeps the status bar up (1774 of 1853 frames); walking it hides after ~7.3 s.
Page changes:
- Look edges (option 2): draws right after a look's last shine and right before the next look's first shine that were
  on screen without a shine are known non-shines (m1/m2 per gap, 10-frame margin, not past a rejected detection, at
  most 4 each side; `test_edges_page.js`: lock after 56-90 s of short looks instead of 63-120 s). A look with no shine
  now extends the gap (its time and hidden time) instead of being dropped.
- Carry through kpa_102 (option 1): a chain search starts from 20 net bits so the maze leaves candidates; when the
  next stretch does not continue them (enemy steps), they are carried with the wide window (E-300..E+1000 steps) and,
  if those die, with the torch model (all 50 phases, <= 64 candidates). `test_maze_dup_page.js`: Duplighost-room lock
  after 23-28 s when the maze left candidates (4 of 6 seeds; else ~46-50 s, same as fresh). TORCH=1: 28-32 s carried.
- First lock inside a torch room: if no seed fits the plain coin (or the chance fits die) after 30 bits, search every
  seed and torch phase (`searchShineStartTorch`, ~2 min with 2 workers); lock needs 38 + log2(50) bits.
- One single-stretch search per stretch even over carried candidates (a chance carry no longer blocks the lock).
Emulator end to end (`speedrun/`, SR_START=kpa40_e1.st, 7 maze rooms 8 s each, kpa_102 closed 9 s, kpa_53 standing
60 s; Xvfb 800x600): 28 of 29 showable shines detected, no false ones; the maze looks gave only 1-2 shines each (no
candidates), so the lock came from the Duplighost room alone via the torch search: true lock 47 s after the first shine
there (plus ~2 min of search time). The page before these changes did not lock at all there.

## Fight "speedrun": Duplighosts -> Jr. Troopa, closed loop (Nov 2)

`speedrun/sr_fight.py` plays the fights in the emulator with the page in the loop: every game frame's video goes into
the page (`speedrun/sr_live.js`, simulated 29.97 fps clock, settings from the runner's log but vlag 0 / off 0 since the
emulator video has no capture delay), the runner saves each target screen the first time it shows (box on the name box,
or the Strategies panel), waits on the target screen for the beeps and presses A on the frame of the final beep. Truth:
every frame's RNG and rand_int call (debug core), and the game's outcome (Duplighost copy rolls, Mario's HP after Jr.
Troopa's attack, Jr. Troopa's HP after the bounces). DIAGNOSTIC: each fight's starting seed is written (an unknown run);
the overworld between the fights is not played (black frames; with JRX the Jr. Troopa seed continues the Duplighost
fight's RNG by GAP + JRX steps). `speedrun/sr_fight_video.py` overlays the page's view on the run.

Findings and page changes:
- Duplighosts (seed 2468ace0): lock 52 s into the fight (19 shines, waiting on Bombette's Strategies screen); the final
  beep fell on the ideal frame (ideal = the frame the model needs, from the RNG truth), the press read back as -0.01
  frames, all 4 copied. So the page's press readout is exact in the emulator; run 3's -1.68 (all 4 copied, but read as a
  failing frame: the 4-copy frames were 154-156, read 153.3) is the capture chain reading the panel's disappearance
  ~1-2.5 frames early relative to the shines.
- Press readout tolerance: a press read within 2 frames of a working frame counts as worked ("a failing frame by the
  video, but a working one is within 2 frames"), and the readout suggests the Press check correction (run 3: about
  -1.5). For a carried turn every working frame within 2 frames is a candidate (`shifts`), the aimed frame first.
- Confirm frames read off the video (Bomb, Charge, Whacka) carry +-2-frame candidates too; most end in the same seed,
  the read frame's group plans and the shines in the next menu drop the others.
- Fast Whacka (emulator, `explore_whacka`): after A on the item the target state starts 3 frames later and a confirm
  is taken from the next frame; the name box only matches from ~10 frames (score <= 0.83 before), so a fast runner
  never shows the target screen (the user's run 3). The status bar starts hiding a fixed number of frames after every
  action confirm (Mario's actions 3, Bombette's Bomb 4, measured on every confirm of a Jr. Troopa run; Bombette doing
  nothing does not hide it). Steps whose turn inputs are all listed (`hud: true`: Jr. T2-T5, Hallway T1) count a hide
  that no target screen explains as the next input (`hudWatch`). `test_hud_confirm.js`.
- Carry through the bar hiding: v60 started a new segment whenever the bar was gone > 3.5 s while locked, which in a
  fight is every action (5-10 s). The carried turns were thrown away each turn and every Close Call waited 20-40 s for
  a relock (emulator baseline). A lock carrying inputs now stays through the hide; each new shine is checked against the
  simulation (a miss still starts a new segment).
- Results (emulator, closed loop; the runner presses on the final beep):
  - Duplighosts: 2 runs, every press on the ideal frame, 4 of 4 copied both times.
  - Jr. Troopa on v60 (seed 13579bdf): T2 lock after 40 s in T2's menu; the fast Whacka was not seen, so T3's Charge
    was taken as the Whacka; the lock dropped every turn and each Close Call waited 21-37 s for a relock; T3/T4/T5
    Close Calls and the 6-bounce landed only because the runner waited on each target screen.
  - Jr. Troopa with these changes (same seed): the lock carried from T2 through T3 and T4 with no relock (Whacka counted
    from the bar), T3 press 16 s and T4 press 27 s sooner than v60, both Close Calls landed.
  - Full run (Duplighosts, 40 s of black, Jr. Troopa with the RNG continued by 12000 extra steps): T2 relock from the
    Duplighost lock after 25.6 s (768 frames) instead of 40 s fresh; T3 and T4 Close Calls landed on beeps (presses on
    the ideal frame). Not solved: T5 got no plan (the route had already moved to T6; the T5 Close Call landed by chance
    on an unplanned press) and T6 got no plan before the run hit its time limit. The fights are now played without the
    page, so this was not chased further.
- Scripts: `speedrun/sr_fight.py`, `sr_live.js`, `sr_fight_video.py`, `sr_whacka.py` (fast Whacka), `sr_hudcheck.py`
  (bar hide delay per confirm).

## Zero-wait (Nov 2): `zerowait/`
The runner never stands for the page. The hallway scene (kkj_13) draws 55-110 extra RNG steps depending on the text pace
(`zerowait/zw_scene.py`), so a lock carried into it has to be re-found after it. New on the page: when the lock survives
T1 but the Spiny Flip's outcomes (7 on median) still disagree in T2's menu, it beeps the frame that is best over all of
them (best-guess window, default 1 s; "no edge" under 40%) and shows the chance (`test_zw_mix.js`: shown 62%, in the
game 74%, no shines needed). Simulated zero-wait runs (`zerowait/zw_sim.js`): +10 points of Time Out with a 60 s C-up
walk after Jr. Troopa, +19 with 80 s, none with 45 s. Those numbers need a candidate-set re-sync after the hallway
scene that the page does not have yet. Final Bowser phase 2: no edge without standing (about 15-25 bits against 43
needed). Details and the model-error runs: `zerowait/README.md`.

## Shared code with the High Power Bounce Manipulator (Nov 2): `shared/`
The capture (`shared/capture.js`: camera / window capture, background frame reading, frame timestamps, box sampling,
automatic flash threshold), the coin detector (`shared/coin_detect.frag.js`, inlined into each page's `onFrame`) and the
beeps (`shared/beeps.js`) now live in `shared/` and are inlined by `shared/inline.py` into both this page
(`build_page.py`) and `powerbounce/hpbm_template.html` (`powerbounce/build_hpbm.py`). The move alone builds this page
byte for byte identical to before (checked with `cmp` on both built files).

One addition here: Timing settings → **Use calibration**. It reads the calibration the High Power Bounce Manipulator
measures (localStorage key `pm-calibration` when both are opened as files in the same browser, or its Copy calibration
text pasted in the box) and sets Beep offset (`recommendedOffFrames`) and Video lag (`vlagMs`). Nothing changes until
it is clicked.

`run_suite.sh` runs the page tests one at a time plus both user log replays (see the script for the list; `ONLY=...`
runs a subset).

## Zero-wait tracker (Nov 2, B held)

**Where the shines come from:**
- Walking from the end of the Jr. Troopa fight to the Hallway Bowser cutscene, with C-up re-pressed (about 60 s of coin,
  time spent anyway).
- The turn-1 and turn-2 menus.

**What the page does:**
- It carries the walk's seed, or up to 64 candidates, through the B-held hallway scene, which is exact: 346 frames,
  124 x rand_int(15) on fixed frames.
- The lag (0-8 frames) and the Spiny Flip (33 impact frames x guard) stay open together as particles.
- On Time Out's target screen it beeps the best frame or says "no edge".

**Results:**
- `test_zw_hallway.js`: P(Time Out) 60.4% against 27.5% blind (60 runs).
- The real added wait is the lead plus up to the 1 s beep window: a median of 29 game frames at a 0.5 s lead.
- Error cases and units: `zerowait/README.md`.
