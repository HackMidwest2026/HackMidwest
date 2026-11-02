# Power Bounce cap searches and videos

Emulator scripts (run from the emulator's bot1/ dir) and C seed searches. Every video seed is set by a DIAGNOSTIC RAM write.

- Final Bowser phase 2 (value 60): `pb12.c` (= the pb13 search, printing 12-bounce seeds). Seed 192a7c5a, confirm delay 3,
  A one frame before each landing (d+44+27k): 12 bounces in the emulator (`_fbverify.py`, video `_fbvid.py`, Bowser HP set
  to 127 so every bounce fits).
- Blooper (value 90, 30 HP): `make_state_blooper.py` builds the battle (DIAGNOSTIC: tik_01 warp, Power Bounce equipped,
  action commands on), `_blnav.py` picks Power Bounce, `_blpress.py` found the timing (hits at d+51+26k, the action
  command works pressing 2-5 frames before the HP drop; 2 used), `_blmodel.py` / `blsearch.c` model the RNG (coin from
  frame 23, 6 star draws per hit, roll k at d+76+26k, matches the emulator log). Delay 3, all 2^32 seeds: best 26 bounces
  (35 seeds), 25 (334), 24 (2042). fc75ed54 and f535f83f verified at 26 in the emulator (Blooper 30 -> 4 HP).
- Blooper, more confirm delays (all 2^32 seeds each): d0 best 27 (3 seeds), d1 27 (1), d2 **29** (1: 1c08132d,
  verified in the emulator, Blooper 30 -> 1 HP, video), d3 26 (35), d4 28 (2). 30 (a one-cycle kill) not found yet.
- Final Bowser phase 2: the delay 64-127 run found **13 bounces**, seed 038c7d04 at delay 119 (verified in the emulator,
  video). Blooper delays 5-8: best 27, 27, 26, 27.

## Final Bowser phase 2: corrected model, lock, and what the page needs (emulator, JP)

Scripts: `fb2model.py` (the model), `fb2dist.c` (what a menu lock can reach), `fb2_bolts.py` (bolt detector check),
emulator scripts `_fbtrace.py` / `_fborder.py` (draw logs and same-frame order), `_fbmenu.py` (idle draws + screenshots),
`_fbnav.py` / `_fbdie.py` / `_fbrevive.py` (DIAGNOSTIC: Life Shroom added, Mario 1 HP, seed written; Bowser KOs Mario),
`_fblturn.py` (lightning through a whole turn), `fb2_revive_30seeds.txt` (revive data). Debug core (`M64P_DBG=1`), run from `bot1/`.

### 1. The bounce model (fixed)
Frame 0 = any frame; `d` = frame of the target-screen A (the confirm). Draws on a frame happen in this order (measured on
40 seeds, every same-frame combination seen):
1. **lightning** `rand_int(359)` (0xE00BC194), one per bolt, on fixed frames (below);
2. the **Power Bounce roll** `rand_int(100)` (0x802A1168), roll k (k = 1, 2, ...) at `d+71+27(k-1)`, continue if
   value <= 120, 72, 43, 25, 15, 9, 5, 3, 1, 0, 0 ... (bounces = rolls passed + 2), **or** the hit's firework stars
   `rand_int(359)` x n (0xE00861EC) at `d+45+27(k-1)`, n = 11 for damage >= 9, 10 for 5-8, 8 for 3-4, 6 for 1-2;
3. the **status-bar coin** `rand_int(100)` (0x80146D54), every 24 frames, 48 after a value >= 70;
4. the per-frame step.

The old search (`pb12.c`) put the roll before the lightning on a shared frame. That is the delay-2 mismatch: seed
29531ef7, d 2, roll 6 at frame 208 shares the frame with a bolt; emulator 7 bounces, old model 12. Fixed in `pb12.c`.
`fb2model.py` matches the emulator's roll values exactly on 113 of 113 (seed, delay) pairs, d 0-127, including the
verified caps 192a7c5a / d 3 (12) and 038c7d04 / d 119 (13).

**Press timing doesn't move the rolls.** Pressing 1 or 2 frames before a landing gives identical rolls and frames. The
action-command window shrinks: the press for bounce n (landing at `d+45+27(n-1)`) may come at most L frames before the
landing frame minus 1, L = 5 (bounces 2-3), 4 (4), 3 (5), 2 (6), 1 (7 and later); pressing on the landing frame fails.
From bounce 7 on that is a 2-frame window (landing-2 or landing-1).

### 2. Locking in FB2
- **The status bar and coin are on screen** in the battle menu, on the target screen and through the whole Life
  Shroom revive (screenshots), and the coin keeps its normal schedule.
- **Menus are not draw-free.** Besides the coin and the step there is the lightning: two free-running periodic sources,
  period 130 frames (bolts at phase 78, 83, 113, 118) and period 220 (18, 78, 88, 178), about 1.5 draws a second. 4000
  idle frames decompose exactly into these two; they keep running unchanged through Mario's turn, the partner's turn,
  Bowser's attack, the KO and the revive (`_fblturn.py`: 135 of 135 bolts predicted). Their phases in a real run are
  unknown. In both states measured the two phases were equal mod 5 (all bolts on one 5-frame grid); assumed, not proven.
- **Only the 220-period bolts are visible**: purple bolts in the sky, first visible 2 frames after the draw (13 of 13
  detected by `fb2_bolts.py`: pixels with r>150, b>170, g at least 40 below both, rows 60-250 of the 592x390 crop).
  The 130-period draws show nothing clear on screen. So the page can fix the 220 phase from 3 seen bolts (gaps 60, 10,
  90, 60), and must search the 130 phase: 26 values if the mod-5 assumption holds (else 130).
- **Lock cost, estimated (not simulated through the page):** the usual 38 bits plus about 5 for the 130 phase, at about
  1 bit/s of coin, so roughly 40-45 s standing in a menu; the search is the torch-style seed x phase search (26 phases).
- **The FB2 Life Shroom revive** (DIAGNOSTIC setup, 30 seeds, 21 KOs; 9 seeds Bowser didn't KO Mario): KO to the next
  Mario menu is 399 or 403 frames depending on Bowser's attack, with the coin up throughout. RNG steps over it 953-976,
  in three clusters by attack (KO at +78: 956-960, +85: 953-957, +90: 972-976) with this lightning phase (19 bolts in the
  window). Usable like the Jr. Troopa revive (about 13 s of coin, minus about 3-4 bits for the spread), not modelled in
  the page yet.

### 3. What a lock can reach (`fb2dist.c`, 20000 random seeds, random lightning phases and coin phase, first damage 13)
Without manipulation, one fixed confirm frame: 6+ bounces 8.2%, 7+ 1.35%, 8+ 0.15%. With a lock, the page picks the
confirm frame inside a window after the lock. Best count reachable on the exact frame, and the chance of at least K
when the runner's press is on the planned frame 50%, one early 25%, one late 25% (page picks the best frame for K):

| window | best exact: 7+ / 8+ / 9+ | with +-1 frame press: 6+ / 7+ / 8+ |
|---|---|---|
| 1 s (30 frames) | 32% / 3.8% / 0.3% | 51% / 17% / 1.9% |
| 2 s (60) | 53% / 7.2% / 0.5% | 59% / 27% / 3.6% |
| 5 s (150) | 84% / 16% / 1.2% | 68% / 43% / 8.3% |
| 10 s (300) | 97% / 31% / 2.3% | 76% / 51% / 16% |

Every frame of delay reshuffles all the rolls, so a 1-frame-late confirm is an unrelated outcome: a "safe on d-1, d,
d+1" plan only reaches 5-6. 10+ is out of reach in practice; the verified 12 and 13 came from searching all 2^32 seeds.
Cumulative damage with first hit 13 (13, 12, 11, ...): 6 bounces 63, 7 70, 8 76, 9 81, 10 85.

### 4. Implementation note for the page (not done; page_template.html was being edited by another change)
1. **FB2 mode** with settings: first-bounce damage (13 here; sets the star counts) and bounces needed.
2. **Bolt detector** on the capture: purple-pixel count in the sky band (thresholds above, a fraction of the crop for the
   GV-USB2 scale), onset = the first frame over the threshold; draw frame = onset - 2. Fit the 220 phase from the onsets
   (need 3; check every later onset against it; refuse to plan on a miss).
3. **Lock**: the coin chain search with extra +1 steps at the predicted bolt frames, over 26 hypotheses of the 130 phase
   (`p130 = p220 mod 5`); like the torch-phase search. Then keep tracking: coin shines must keep matching, bolts too.
4. **Plan**: for every frame d in [now + menu time (about 1.5 s to reach the target screen), now + window], run
   `fb2model` with the locked seed, both phases and the coin phase; pick d maximizing P(>= needed) under a +-1 frame
   press (or the max bounces when none reach it). Show the expected count.
5. **Beeps**: countdown to the confirm A at d (the runner sits on the target screen); then a beep 1 frame before each
   landing, at `d+44+27(n-1)` for bounce n = 2, 3, ... (landing `d+45+27(n-1)`; window above). Stop at the planned count.
6. **Checks**: the first hit lands at `d+45`; if the HP-drop flash comes a frame off, the confirm missed and the plan
   is void (re-plan from the tracked seed for the next turn).

Not verified: the page itself (nothing built), the lock time (estimate), the 130-phase mod-5 assumption beyond two
states, the bolt detector on real GV-USB2 footage, damage other than 13, and other Bowser attacks during the revive.

### 5. Zero-wait use: scoring press timings, and passive windows (coordinator update)
The goal is now no standing in menus: the page scores candidate confirm frames over whatever partial candidate set the
passive observation leaves, and picks the best.

**Scoring.** `fb2model.js` (JS port of `fb2model.py`, 300 of 300 cases identical, the verified 12 and 13 reproduced) has:
- `fb2Bounces(seed, d, {p130, p220, coinNext, dmg0, fx})`: the exact bounce count for one candidate when the
  target-screen A lands on frame d (frame 0 = the frame the candidate's seed is the start seed of).
- `fb2PAtLeast(cands, d, K, press)`: P(bounces >= K) over weighted candidates and a press-error distribution (default
  50% on frame, 25% one early, 25% one late). Expected count = sum over K of P(>= K). Cost: one candidate x one frame is
  at most ~1100 model frames; 1000 candidates x 300 frames x 3 press offsets is ~1e9 frame steps, so prune candidates or
  frames (a web worker; or score the top-weighted candidates only).
- With **no** information (prior), one confirm frame gives: 3: 28%, 4: 41%, 5: 23%, 6: 6.8%, 7: 1.2%, 8: 0.14%, 9: 0.01%.
  Every frame of d reshuffles all rolls, so with a large candidate set every d scores close to this prior; the gain comes
  only once the set is small (a lock, or a few hundred candidates). With a full lock see section 3's table.
- Inputs the page must know besides the seed: the two lightning phases (section 2; p130 = p220 mod 5 held in all 4
  states checked), the coin's next-draw frame (from the tracked coin), the first-hit damage (13 in these states), and the
  `fx` cycle when present (below).

**Passive windows in Final Bowser** (emulator; DIAGNOSTIC states as listed):

| window | coin visible | RNG besides the step + coin | fixed? |
|---|---|---|---|
| Phase 1 battle menu / target screen (`boss_2303_menu`) | yes (screenshot) | lightning, same two sources (phases 43/193 here) | yes, given the phases |
| Phase 2 menu at the start (`boss_2304_route_menu`) | yes | lightning (59/209) + effect 0xE00D6838: a 20-frame cycle `21010201310011101010` (16 draws/20 frames) | yes: identical for 3 seeds; phase unknown (20 values), not visible as far as checked |
| Phase 2 menu later (`fb2_t7like_menu`) | yes | lightning only (no 0xE00D6838) | yes, given the phases |
| Phase 2 Life Shroom revive (KO -> next menu) | yes, throughout | effect bursts + lightning; 399 or 403 frames by Bowser's attack | steps 953-976 in 3 clusters (+78 KO: 956-960, +85: 953-957, +90: 972-976), i.e. ~5 values once the attack is known |
| Mario / partner actions, Bowser's turns | yes (bar stays up) | attack choices, damage, effects | no: not modelled |
| Phase 1 revive, phase 1 -> 2 transition, Peach / Twink cutscenes | not measured | not measured | not measured |

Lightning keeps the same phases through whole turns (KO and revive included), so once known it never needs
re-finding. Which effect 0xE00D6838 is, when it stops in phase 2, and where its draws fall in the frame order relative to
the roll (assumed before the coin, after the roll/stars) are not verified; the Power Bounce model was only checked in the
state without it.

## High Power Bounce Manipulator (non-speedrun): models, step-up table, page spec

Goal: lock while standing still in the battle (allowed here), then the page counts down to the nearest confirm frame that
gives at least K bounces; the user tries, then steps K up by one until the wait for the next K is unrealistic. Each try
doubles as a calibration test of the lock, the capture timing and the user's press, for the speedrun page.

### Blooper model (verified)
`blmodel.py` / `blmodel.js` (identical on 300 random cases incl. Dodge Master and other damages). Emulator checks
(`_blorder.py`, debug core, DIAGNOSTIC: seed written, action commands on, Blooper HP 127 so long chains fit, Dodge Master
equipped in the 2nd badge slot for the DM run):
- 150 of 150 random (seed, d 0-127) pairs: every roll value and frame identical; plus the verified 29 (1c08132d, d 2).
- 60 of 60 with Dodge Master (value 97), chains up to 37 rolls (39 bounces).
- Frame order on a shared frame: stars or roll, then the coin, then the step (seen: roll+coin, stars+coin).
- `_blidle.py`: the Blooper battle menu and the Power Bounce target screen draw nothing but the coin and the step (2000
  frames each). So a plain coin lock works here (no lightning, unlike FB2).
- Timing: stars for hit k at d+51+26(k-1) (n by that hit's damage; 1 damage -> 6), roll k at d+76+26(k-1), continue if
  value <= c_k, c = 200, c = c*v/100 per roll, v = 90 (+7 Dodge Master, `power_bounce.c`).
- Action command: from about bounce 6 on, A must land 1 or 2 frames before the HP drop (d+51+26(k-1)); 3 early ends the
  chain at bounce 7 (measured on the 29 seed: leads 1-2 give all 28 rolls, lead 3 gives 5). Pressing on the drop fails.
  Within the window the press frame does not change the rolls; only the confirm frame d does.
- **HP cap.** Real Blooper has 30 HP. The verified state does 1 damage per hit, so 30 bounces kill it and the chain ends
  there whatever the rolls. Not checked: the user's Blooper damage (boots, other badges). More damage means fewer hits
  to the kill and different star counts on the early hits (`dmg0` parameter).

### Step-up table (`ladder.c`, 2000 random locked states each, 2 h of confirm frames scanned per state, first try at
least 3 s after the lock; game frames, 30 per second; full output in `ladder_tables.txt`)
"wait" = time from the lock (+3 s) until the first confirm frame with >= K, median / 90th percentile. "press" = chance
of still getting >= K when the press lands on the planned frame 50%, one early 25%, one late 25% (a 1-frame miss is a
fresh, unrelated outcome, so it is about 50% + 50% x the per-frame chance). Waits beyond the 2 h scan are from the
measured per-frame rate (geometric).

Blooper, no Dodge Master (v 90). 8 is guaranteed (the first 6 chances are >= 100):

| K | per frame | wait median | wait 90% | press ±1 |
|---|---|---|---|---|
| 13 | 24% | 0.1 s | 0.3 s | 59% |
| 15 | 6.4% | 0.4 s | 1.3 s | 52% |
| 17 | 1.1% | 2.3 s | 8.9 s | 51% |
| 18 | 0.37% | 7 s | 24 s | 50% |
| 19 | 0.11% | 23 s | 77 s (**> 1 min**) | 50% |
| 20 | 3.2e-4 | 73 s | 4.2 min | 50% |
| 21 | 7.9e-5 | 4.8 min | 16.5 min (**> 5 / 15 min**) | 50% |
| 22 | 1.7e-5 | 22 min | 72 min (**> 60 min**) | 50% |
| 23 | 3.3e-6 | 2 h | 6.5 h | 50% |
| 24 | 5.5e-7 | 12 h | — | — |

So the realistic Blooper top is 20-21; 22 is a long session; the searched 29 needs a seed 2^32-search away, out of
reach by waiting. **With Dodge Master (v 97)** every chance stays >= 100 for the first 20 rolls: 22 bounces is guaranteed and 30
(= the kill at 1 damage) comes 31% of frames, so the HP cap is reached at once (table to 41 in `ladder_tables.txt`
with HP 127).

Final Bowser phase 2 (v 60, first hit 13 damage, lightning phases random with the mod-5 assumption):

| K | no Dodge Master: per frame / median / 90% | Dodge Master (v 67): per frame / median / 90% |
|---|---|---|
| 6 | 8.1% / 0.3 s / 0.9 s | 21% / 0.1 s / 0.3 s |
| 7 | 1.3% / 1.9 s / 6.5 s | 5.6% / 0.4 s / 1.4 s |
| 8 | 0.13% / 18 s / 64 s (**> 1 min**) | 1.0% / 2.5 s / 8.5 s |
| 9 | 7.6e-5 / 5.5 min / 17.5 min (**> 5 / 15 min**) | 0.12% / 21 s / 68 s (**> 1 min**) |
| 10 | 3.2e-6 / 2 h / 6.7 h (**> 60 min**) | 9.3e-5 / 4.2 min / 14 min (**> 5 min**) |
| 11 | 7.2e-8 / 3.7 days | 4.8e-6 / 80 min / 4.5 h (**> 60 min**) |
| 12 | 2.3e-9 / ~4 months | 1.2e-7 / 2.3 days |

The press column is 50-52% for all FB2 K >= 7 (the one-frame-off outcome is almost always lower). Realistic FB2 top:
8 (9 with patience); with Dodge Master 9-10. Bowser's remaining HP caps it too (cumulative damage from 13: 8 bounces 76,
10 85).

What the ±1 column means for the user: until the press offset is calibrated, every rung is a coin flip even with a
perfect lock; with the offset known and the user's spread under a frame, it approaches the per-frame-planned 100%.

### Page spec: the High Power Bounce Manipulator (separate page and artifact; built Nov 2, see the next section)
A page of its own, `powerbounce/hpbm_template.html` with its own build step (`powerbounce/build_hpbm.py`), titled
**High Power Bounce Manipulator**, published as its own artifact. The speedrun page (`page_template.html`) is not
changed by it.

**Shared code, not copies.** Both pages must be built from the same sources: `pmrng_core.js` (LCG, coin model, seed
search), and the capture, coin detector, frame-timing and beep-scheduler code. Today the latter live inline in
`page_template.html`, so the first step is to move them into shared files (`capture.js`, `coin_detect.js`,
`beeps.js`) that `build_page.py` and `build_hpbm.py` both inline, with `page_template.html` keeping identical behaviour
(its tests and both log replays must still pass). This refactor touches `page_template.html`, so it waits until the
speedrun work there is committed (check `git status`). Then the boss models are inlined too: `blmodel.js`,
`fb2model.js`.

**Flow.**
1. Pick the fight: Blooper or Final Bowser phase 2; settings: Dodge Master on/off, first-hit damage, enemy HP left.
2. Lock: stand on the Power Bounce target screen with the status bar up until the coin lock (Blooper: plain coin
   search; FB2: coin + bolt-detector 220 phase + 26-way 130-phase search, see section 4 above).
3. **Step-up mode.** Target K selector (starts at the lowest K not guaranteed, e.g. Blooper 9, FB2 5; buttons
   K-1 / K+1). The page scans confirm frames from now + lead (3 s default) with the model and shows: the next frame with
   >= K, the countdown, the expected count on that frame, and the expected wait for K+1 (from the table above / the
   live scan), so the user sees when the next rung becomes unrealistic.
4. Beeps: countdown beeps to the confirm A on the planned frame d, then one beep per bounce at the press frame (1 frame
   before each landing: Blooper d+50+26(n-1), FB2 d+44+27(n-1)), stopping at the planned count.
5. After the try, the user enters the count they got (or the page reads it if feasible: Blooper/Bowser HP drops from the
   enemy HP bar, or counting hit flashes). Then the page re-tracks the seed from the coin (the battle keeps the bar up)
   for the next try.

**Calibration output (the log, per try):** lock time and bits; the planned frame d and its predicted count; the actual
count; the **implied confirm offset**: the offsets e in -6..+6 for which the model with the lock gives the actual count
at d + e (unique for counts that are rare; ambiguous ones logged as a set); shine-detection latency (detected flash time
minus the model's shine frame, per shine, after the lock) and the capture's frame-timing jitter (spread of frame
timestamps / presentation times). Summary: **press offset mean ± sd in frames** (from tries with a unique implied
offset), **capture latency mean ± sd in ms**, and the hit rate per K.

**Export.** A "Copy calibration" button (JSON: `{pressOffsetFrames, pressSd, captureLatencyMs, captureJitterMs,
tries, date}`) and the same object in `localStorage` under a shared key `pm-calibration`; the speedrun page reads it
(when both pages are opened from the same origin, i.e. the standalone files, or by pasting the JSON) and applies it to
its beep offset (`s-off`) and video lag (`s-vlag`).

**Tests before publishing:** the speedrun harness on emulator video (`speedrun/sr_feed.js`) at a Blooper lock and an
FB2 lock, plus a couple of step-up rungs each, checking the predicted count against the emulator's.

Not verified here: the page (not built), the user's Blooper damage and HP, the FB2 bolt detector on GV-USB2 footage,
the FB2 lock time, and whether a human press can hold a 1-frame offset (that is what the calibration measures).

### Built (Nov 2): `hpbm_template.html`, `build_hpbm.py`; artifact "High Power Bounce Manipulator"
Built as specified above, from the same shared sources as the Time Out Timer (`../shared/`: capture, coin detector,
beeps; `../pmrng_core.js`) plus `blmodel.js` and `fb2model.js`. Differences from the spec:
- **Lock:** stand on the Power Bounce target screen; with "Plan as soon as the seed is found" on (default) the
  countdown starts at the lock. No target-screen detection (nothing to save): the page assumes you are on the screen.
- **After a try** the coin hides (the bounces, the enemy's turn); when it is back the page re-finds the seed from the
  plan's frame-0 state over `Re-find range` RNG steps (default 6000; needs about log2(range) + 10 bits, ~23) before
  falling back to a full search. Reloading a save gives an unrelated seed: the re-find fails and the full search runs.
- **HP cap:** the count is capped at the hit that kills (Enemy HP left, first-hit damage, -1 per hit, at least 1);
  after each logged try the page lowers Enemy HP left by that try's damage. Blooper (30 HP, 1 per hit): 30 kills.
- **Final Bowser:** the lightning box (purple bolts, 64x48 sample, onset over 0.3%; the 32x32 sample the coin uses
  missed every bolt in the emulator video) fixes the 220-cycle phase to within +-1 frame; the search then covers those
  220 phases x the 26 130-cycle phases on the same 5-frame grid (a trie of RNG-step sequences, one per hypothesis). The
  extra early-phase-2 effect (0xE00D6838) is not modelled.
- **Calibration:** per try, the implied confirm offsets are the e in -6..+6 whose count from the lock equals the count
  typed in; only tries with one such e enter the average. Exported as `{recommendedOffFrames, vlagMs,
  pressOffsetFrames, pressSd, captureJitterMs, tries, unique, hits, date}` (Copy calibration and localStorage
  `pm-calibration`); the Time Out Timer's Timing settings -> Use calibration applies the first two. Capture latency is
  not measurable from the coin alone (a constant lag moves the lock's clock and the beeps together), so the export
  carries the video lag the tries used, and the press offset absorbs any error in it.

Tests:
- `../test_hpbm.js` (synthetic: a known seed's shines fed at their display times, the plan's count against the model
  from the true seed on the absolute confirm frame, and a try logged 1 frame late must imply +1): Blooper 5/5 seeds,
  FB2 2/2 (lock after 1547 and 3302 frames).
- **Emulator, closed loop** (`hpbm_run.py` + `hpbm_live.js`; emulator video frame by frame into the page on a simulated
  clock, confirm on the final beep, A one frame before each landing, count from the enemy's HP in RAM; DIAGNOSTIC: a
  random seed per rung, action commands on). Blooper (`blooper_pb.st`, 30 HP), seed 1234abcd, run twice with the same
  result:

  | target | offset | lock (video) | planned | got | implied offset |
  |---|---|---|---|---|---|
  | 12 | 0 | 50.7 s | 12 | 12 | 0 or +6 |
  | 15 | 0 | 45.0 s | 16 | 16 | 0 |
  | 18 | 0 | 43.4 s | 20 | 20 | 0 |
  | 15 | +1 (late) | 44.2 s | 16 | 11 | +1 or +3 (unclear, not averaged) |

  Calibration from these: press offset 0.00 +- 0.00 frames from 2 clear tries, recommended beep offset 0 (the harness
  presses exactly on the beep frame, so this checks the arithmetic, not a human). Final Bowser phase 2
  (`fb2_t7like_pb.st`, seed 5eed0fb2, target 7): locked after 100 s of video (the first search's 79 candidates all died
  on later shines; the second, with one 220 phase, locked), planned 7, got 7, implied offset 0. **Each Final Bowser
  search took about 12 minutes on 2 threads** (the harness pauses the game during searches, so the video times above
  exclude search time; a Blooper search took 10-17 s).
- `hpbm_video.py` makes the overlay video of a rung.

Not verified: a human's press (the harness presses on the beep frame), the bolt detector on GV-USB2 footage, Final
Bowser states with the early-phase-2 effect, first-hit damage other than 13 on Bowser, the re-find after a real enemy
turn (each emulator rung reloaded a state), and Dodge Master in the page (model only).
