# Zero-wait manipulation (Nov 2)

The runner never stops for the page. It only uses the coin during time the run spends anyway. At the RNG-critical
press it beeps the frame that is best over whatever candidates are left, or says "no edge, press normally".

## Units used below

**Time the run spends anyway (no standing):**
- **"Walk"** means overworld walking from the end of the Jr. Troopa fight to the Hallway Bowser cutscene, re-pressing
  C-up to keep the coin up. "60 s walk" is 60 s of that walking, with the coin up most of the time.
- **"T1 menu"** is the time on the Hallway Bowser turn-1 menu: the battle intro and choosing a move. 5 s by default.
- **"T2 menu"** is the time on the turn-2 menu before reaching Time Out's target screen. 3 s by default.

**Real time added to the run:**
- **"Lead":** the wait on Time Out's target screen before the beep window opens. The simulations use 0.5 s. The page
  default is 4 s; set it to about 1.5-2 s, which a 4-beep countdown at 500 ms needs.
- **"Window":** the most the page may add on top to pick a better frame. 1 s = up to 30 game frames (30 fps).
- **"Delay":** what was actually added, lead + chosen offset, in game frames (30 = 1 s).

"Blind" is the same runs confirming Time Out the moment the target screen is reached (expected 30.7%).

## What the emulator showed (JP)

### Hallway scene (kkj_13)
- **Setup:** `zw_scene.py` from `states/kkj13_e0.st` (STORY 95, GF_KKJ13_BowserTaunts off, the route's hallway entry).
  Each run writes a DIAGNOSTIC random seed.
- **Length:** the scene to the battle start takes 449-614 frames, depending on how fast the text is advanced.
- **Extra draws:** the scene draws RNG beyond the per-frame step and the coin. The count depends on the A pace and varies
  by a step or two by seed:

  | A pace | extra steps |
  |---|---|
  | every 13 frames | 107-109 |
  | every 20 frames | 80-82 |
  | every 31 frames | 55-59 |
  | human-like, random 10-35 frames | 57-80 (8 seeds) |

- **Consequence:** a lock carried into the hallway comes out of the scene about 45-125 steps off. It must be re-found from
  shines after the scene.
- **Not identified:** what draws them. The debug-core caller probe (`zw_callers.py`) did not finish in this session. If
  the count follows the message timing the page can see, the scene could be modelled exactly. That is the most valuable
  next measurement.
- **Battle intro:** fixed (86 frames, 106 steps; `lifeshroom/ls_hwintro.py`).
- **Rooms after Jr. Troopa:** all clean (earlier: kpa_83, kpa_121, osr_02, kkj_10-19 and kkj_22, and the library pickups).

### Hallway T1 (`zw_groups.js`)
- The Spiny Flip (33 impact frames x guard or not) leaves **7 distinct RNG futures** (median; range 4-10).
- The biggest one holds 52% of the candidates (median).
- With the guard known: 4 futures (3-6).

## Update: B held makes the hallway scene exact

The user reports that the scene, and all text in the game, is consistent when B is held.

**Scene (kkj_13).** `zw_scene.py kkj13_e0.st 8 -1`, 8 seeds, B held:
- 346 frames from the scene to the battle, every time.
- 124 extra draws beyond the per-frame step and the coin.
- The 124/125 my per-frame counter printed was the coin landing on a burst frame, not a variable count.

**The draws.** All are `rand_int(15)` from the same caller 0x8012978c (debug core, `zw_callers.py ... -1`). The battle
intro's 16 extra draws come from that caller too. They come in bursts of 10-12 a frame while a text box fills, so they
are most likely one per printed character; the caller is not identified in the source.

`zw_sched.py` gives the exact schedule, in frames from the scene start:

| frame | 138 | 139 | 140 | 141 | 147 | 152 | 153 | 158 | 159 | 199 | 286 | 287 | 288 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| draws | 7 | 11 | 12 | 2 | 10 | 12 | 11 | 12 | 10 | 5 | 12 | 12 | 8 |

**The model is exact.** `zw_schedcheck.py` checks that seed, plus the per-frame step, plus the coin on its normal 24/48
schedule, plus these draws before the coin in the frame, reproduces the emulator's seed on every frame of the scene:
8 of 8 seeds.

**Battle intro with B held** (`boss_2302_route_start.st`): the T1 menu opens 42 frames in, with 60-61 RNG steps (the
coin). That is fixed for 8 seeds, with or without an A every 20 frames.

**Not measured:**
- **Jr. Troopa's kpa_83 scene:** my redirect into kpa_83 with the scene flag cleared did not trigger. The walk never
  reached an exit, so no savestate of that scene.
- **Jr. Troopa's post-battle text with B held:** not measured. It isn't needed for this plan: the lock is found during
  the walk after it.

**Simulation with the scene modelled exactly.** `zw_sim.js ... EXACT=1`, `zw_gridX.sh` -> `zw_gridX.txt`, 200 runs each.
- **What is carried:** the walk's candidates (lock or up to 64 seeds) go through the scene with only the console lag at
  the battle start unknown (0-8 frames enumerated).
- **Then:** T1 menu draws, T1 x 66 Spiny Flip candidates, T2 menu draws, best guess.
- **Base:** 60 s of walking from the Jr. Troopa fight to the Hallway Bowser cutscene, 5 s on the turn-1 menu, 3 s on the
  turn-2 menu (all time spent anyway); 0.5 s lead + up to a 1 s beep window (= up to 45 game frames of real added
  wait); press 25/50/25.

| case | P(Time Out) | blind, same runs | beeped | when beeped: shown / in game | delay when beeped |
|---|---|---|---|---|---|
| base (60 s walk) | 70.8% | 32.4% | 89% | 75% / 74% | 29 frames (1 s) |
| 45 s walk | 32.4% | 29.4% | 7% | 66% / 67% | |
| 80 s walk | 73.9% | 31.0% | 99% | 76% / 75% | |
| short menus (2 s each) | 60.0% | 32.9% | 82% | 63% / 67% | |
| window 0 (0.5 s lead only) | 39.5% | 32.4% | 28% | 56% / 55% | 15 frames |
| window 0.33 s | 58.5% | 32.4% | 82% | 64% / 63% | 20 frames |
| press +-2 frames | 61.3% | 31.8% | 87% | 65% / 65% | |
| missed / false walk shine | 32.3% | 32.4% | 23% | 69% / 31% | |
| 1-5 unmodelled draws in the scene | 69.1% | 27.4% | 87% | 73% / 75% | |
| 1-5 unmodelled draws in T1 | 38.1% | 28.5% | 76% | 75% / 42% | |

Percentiles of the realised chance per run (10/25/50/75/90): base 0.25 / 0.5 / 0.75 / 1 / 1; 45 s walk 0 / 0 / 0.25 /
0.5 / 0.75.

What the table says:
- - **With B held but the old generic re-sync** (`zw_gridB.txt`: the window narrowed to 118-131 steps), the base is only
  41.0% against 29.9% blind. Most of the gain needs the exact carry.
- **The gain against the A-pace scene** (35% base) comes from carrying the lock through the scene. Afterwards the
  menus only have to pick among 0-8 lag frames x the Spiny Flip outcomes, instead of 45-125 unknown steps.
- **Unmodelled draws in the scene** are absorbed by the lag hypotheses: an extra step looks like a lag frame.
- **Unmodelled draws in T1** are not absorbed. The shown chance is then far too high (75% shown, 42% real), though the
  run still beats blind.
- **A missed or false walk shine** gives blind with a wrong shown chance, as before.

**The page needs three things for these numbers. All are now built; see the next section:**
1. **The scene as a carried event.** A `TURNS` entry with this schedule, placed where the page sees the cutscene take
   the status bar away, with a few lag shifts as candidates. The existing `shifts` mechanism does this for one input at
   a time.
2. **Candidate sets carried through events.** Today only a single lock is carried. Without it the walk must reach a full
   38-bit lock, which takes about 80 s of C-up walk at about 0.5 bits/s.
3. **Several open candidate kinds at once.** Lag shifts and the Spiny Flip are both open in T2; today `fixHyps()`
   settles the older one when the next opens.

## Built in the page (Nov 2): the zero-wait tracker

The tracker is `zw*` in page_template.html.

**When it starts:**
- The coin comes back after 10 s or more hidden, while the route is at or before the Hallway Bowser T1 step. That is the
  battle's status bar after the scene.
- It needs one of:
  - a lock from the walk;
  - the last lock (prevLock);
  - the current look's candidate seeds (up to 64, each checked against the look's shines).
- It moves the route to the Hallway T1 step.

**What a particle is:** one walk candidate x one read of the bar-up frame (+-4 frames) x one console lag (0-8 game
frames lost in the room load before the scene).
- Each is simulated frame by frame in clock frames: the B-held scene schedule, then Charge.
- At the Spiny Flip confirm, each splits into 33 impact frames x guard or not.
- So the lag and Spiny Flip candidates stay open together.

**Pruning:**
- **Shines:** each shine the page sees must be a shine of the particle (+-1.5 frames).
- **Plain spins:** while the coin was steady (from 1 s after it came back to 4 frames before it hid or the confirm), a
  shine the particle predicts must have been seen.
- **Merging:** particles in the same RNG state merge.

**On Time Out's target screen:**
- It scores the next "best-guess window" seconds after the lead, with the press 25/50/25 over -1/0/+1 frames.
- It beeps the best frame and shows the chance, or says "No edge".
- **The two no-edge cases:** nothing fits what it saw, or the best frame works for under 40% of the particles.

**Walk counter (sidebar, and "walk" in the session log).**
- **When it runs:** from the coin's return after a long gap (10 s or more hidden: the end of Jr. Troopa's text) to the next
  long gap (the hallway cutscene taking the bar away).
- **What it shows:** real-time seconds with the coin on screen ("coin visible"), real-time seconds since the walk started
  ("walked"), and the bits of evidence so far against the ~38 a lock needs, or "locked".
  - Live: `coin visible 27.5 s of 30.0 s walked (real time) | 21 of ~38 bits`.
  - Logged when the walk ends, and shown as "Last walk": `Walk: coin visible 36.7 s of 40.0 s walked (real time) | 30
    of ~38 bits`, with the number of candidate seeds when there are several.
- **Test:** `test_walk_counter.js`, 40 s of 220-frame looks with 25-frame dropouts. Both numbers are within 0.3 s of the
  truth, and the log entry and "Last walk" appear at the long gap.
- **Caveat:** it starts at any long gap, so before Jr. Troopa it also counts other stretches. It is meant to be read
  between the Jr. Troopa fight and the hallway.

**Page-driven test** (`test_zw_hallway.js`):
- The game is simulated independently in the test, with the lag as clock frames with no game step.
- The walk lock is from one look, the battle as above, and the press lands 25/50/25.
- Real added wait: lead 0.5 s + window up to 1 s.

| case | runs | P(Time Out) | blind, same runs | beeped | when beeped: shown / in game |
|---|---|---|---|---|---|
| 60 s of coin on the walk, no errors | 60 | **60.4%** | 27.5% | 53 | 63% / 66% |
| 30 s of coin on the walk (one look) | 40 | blind in 38 runs: no seed, the tracker did not start | | 2 | |
| one turn-1-menu shine missed | 40 | 35.6% | 26.3% | 15 | 63% / 65% (23 runs: no edge, inconsistent) |
| a false shine in the turn-1 menu | 40 | 26.3% | 26.3% | 0 | all 40: no edge, inconsistent |
| lag 12 frames (model allows 0-8) | 40 | 28.1% | 28.1% | 1 | 37 runs: no edge, inconsistent |
| 20 extra draws in the scene (text not held with B) | 40 | 26.9% | 22.5% | 11 | 62% / 32% (29 runs: no edge) |
| 3 unmodelled draws in turn 1 | 40 | 48.1% | 30.6% | 34 | 62% / 50% |

The delay actually added when it beeped (no-error case): a median of 29 game frames (1 s), at most 44, at a 0.5 s lead.
With the page's default 4 s lead it would be 4 s more.

What the table says:
- **Against the simulation's 70.8%:** the page is lower (60%). It keeps more hypotheses (+-4 frames of bar-up reading
  x 0-8 frames of lag, 81 per walk seed, against the simulation's 9) and uses the turn-1 menu's plain spins only up to the
  Charge confirm.
- **Errors mostly show up as "no edge":** the consistency check catches nearly every false shine and every lag outside
  the model, and stays at blind for them.
- **Unmodelled draws are the weak spot.** A scene without B held, or unmodelled draws in turn 1, can still beep with a
  shown chance far above the real one (62% shown, 32% or 50% real). The mean still stays at or above blind, but the
  shown chance is not trustworthy then.

**Not verified:**
- The anchor (the bar-up 450 frames after the scene starts) is from one emulator run (`zw_barvis.py`).
- The coin detector's "back" time on a GV-USB2 capture, and real console load lags.
- The candidate-set start only runs when the walk left up to 64 candidates. A single 30 s look left none.
- No emulator end-to-end run of the whole route through the page.

## The page change (built): best guess at Time Out
- **When it applies:** the page is locked through T1, but the Spiny Flip outcomes still disagree in T2's menu.
- **What it does:** instead of waiting for shines, it scores every confirm frame in the next "best-guess window" (Timing
  settings, default 1 s, after the lead time). The score is the sum over futures, each weighted by how many
  impact/guard candidates ended there, of P(Time Out) under a press 25% one frame early, 50% on time and 25% one late.
- **Beep or no edge:** it beeps the best frame and shows the chance. If the best is under "beep only if it works at least"
  (default 0.40), it says "No edge ... press Time Out normally" and does not beep.
- **Shines still count:** a shine in the menu still prunes the futures and replans.

| test | result |
|---|---|
| `test_zw_mix.js` (24 random seeds, lock, no shines in T2) | shown 62% on average, 74% in the game (exact + +-1 frame) |
| forced no-edge case (threshold 0.99) | did not beep |
| `test_hw_carry.js` (best guess off, `s-zwwin` 0) | still narrows by shines and plans Time Out |

**Not built:**
- **Carrying candidate sets through the hallway scene.** The re-sync after a long hidden gap still needs a unique fit
  with log2(window) + 7 bits, about 17 bits. The natural menu time gives about 3-5 bits.
- **So in a real zero-wait run the page usually has no lock in T2,** and the built best guess rarely fires. It fires when
  something re-locks after the scene: shines in a longer T1 menu, or a lock carried without a scene.
- **What the gap needs:** the post-scene re-sync below, implemented with candidate sets, i.e. `st.hyp` over (seed
  candidate, impact, guard) instead of (impact, guard) on one lock.

## Simulation (`zw_sim.js`, `zw_grid.sh` -> `zw_grid.txt`)

The simulation uses the real LCG, the verified Time Out profile, and the page's T1 turn model. It covers:
- **Walk:** looks of 220 frames, dropouts, room loads with 0-6 lag frames, item messages; evidence counted the page's way.
- **Scene:** hidden for 650 +-60 frames, with 55-110 extra steps.
- **T1 menu, Charge, Spiny Flip, T2 menu:** natural visible time only, then the target screen.

The page model it simulates:
- **Walk candidates:** the truth plus Poisson(2^(32 - bits)) random decoys. The page carries nothing if that number is
  over 64.
- **Re-sync after the scene:** at the first shine in a battle menu, over the measured window.
- **Spiny Flip:** x 66 candidates, then the T2 menu filters them.
- **Best guess:** over the rest; "no edge" under 0.40.

The realised chance is the true trajectory's Time Out at the chosen frame, averaged over the press error.

200 runs each. The base case: 60 s of walking from the Jr. Troopa fight to the Hallway Bowser cutscene with the coin up
(spent anyway), 5 s on the turn-1 menu including the battle intro and 3 s on the turn-2 menu (spent anyway), then a
0.5 s lead and up to a 1 s beep window (real added wait: up to 45 game frames). "Blind" is the same runs pressed on reaching the target screen (expected 30.7%).

| case | P(Time Out) | blind, same runs | gain | beeped | when beeped: shown / in game | delay when beeped |
|---|---|---|---|---|---|---|
| base (60 s walk) | 35.2% | 25.1% | +10 | 43% | 49% / 51% | 29 frames (1.0 s) |
| 45 s walk | 33.4% | 33.4% | 0 | 0% | - | - |
| 80 s walk | 48.7% | 30.2% | +19 | 78% | 54% / 56% | 30 frames |
| 80 s walk, page keeps up to 4096 walk candidates | 49.7% | 31.1% | +19 | 78% | 54% / 57% | 30 frames |
| short menus (2 s each) | 29.2% | 26.3% | +3 | 8% | 44% / 50% | 31 frames |
| window 0 (only the 0.5 s lead) | 26.9% | 25.1% | +2 | 6% | 45% / 50% | 15 frames |
| window 0.33 s | 31.8% | 25.1% | +7 | 31% | 48% / 49% | 20 frames |
| window 2 s | 37.9% | 25.1% | +13 | 50% | 50% / 53% | 45 frames |
| guard known | 35.0% | 25.1% | +10 | 44% | 51% / 51% | 28 frames |
| press +-2 frames (10/20/40/20/10) | 33.7% | 25.7% | +8 | 32% | 48% / 51% | 29 frames |

Per run the realised chance is 0, 0.25, 0.5, 0.75 or 1, from the press error. In the base case the 10/25/50/75/90th
percentiles are 0 / 0 / 0.25 / 0.5 / 0.75; for 80 s they are 0 / 0.25 / 0.5 / 0.75 / 1.

**Where the base runs ended:**

| outcome | runs |
|---|---|
| beep | 85 |
| no edge | 61 |
| too few walk bits (diffuse) | 23 |
| no shine in either battle menu | 18 |
| diffuse after the scene | 12 |
| diffuse in T2 | 1 |

The walk gives about 0.5 bits per second of walking: the median is 30 bits for 60 s and 39 for 80 s. That is less than
the ~1 bit/s of standing, because of the 1 s steadiness rule after every re-press and the gap costs. **The walk length
decides almost everything**; it should be timed on a real run.

**Model errors.** 200 runs each, same base:

| injected error | P(Time Out) | blind, same runs | when beeped: shown / in game |
|---|---|---|---|
| missed or false shine in the walk | 25.0% | 25.1% | 49% / 28% |
| scene drew 10-40 more steps than the window | 33.5% | 29.1% | 48% / 39% |
| 1-5 unmodelled draws in the T1 turn | 31.9% | 27.5% | 50% / 41% |
| impact frame outside 138-170 | no change | | |

- The impact-frame case does not bite: same draw count, so the futures mostly merge. It is a weak test.
- **Never worse than blind, in these tests:** with a wrong model the choice of frame is independent of the true outcome,
  so the press is a blind one. The mean stayed within noise of blind: 25.0% against 25.1% for the walk error, and above
  blind for the others.
- **The shown chance is not trustworthy under errors:** it said 49% where the game gave 28%.
- **The consistency checks catch only part of it:**
  - "no seed fits", which stops the beeps: 48 of the 200 walk-error runs.
  - "nothing fits the T1/T2 menu shines".
  - Otherwise the decoys still fit and the page beeps with false confidence.
- **The time cost is real either way:** about 1 s of waiting when it beeps.

**Execution cost.**
- **How the page beeps:** after the target screen appears, it waits the lead time (Timing settings, default 4 s; for
  zero-wait set about 2 s, the least that fits a 4-beep countdown at 500 ms), then picks a frame inside the best-guess
  window.
- **What that costs:** it delays the confirm by lead + chosen offset compared with an immediate press, about 2-3 s with
  the page's beeps. The simulation's 0.5 s lead is optimistic.
- **Avoiding it:** press P when T2's menu opens, so the countdown runs while navigating the Star Spirit menu.

## Final Bowser phase 2 (plan with numbers; not built)

From `powerbounce/README.md` (commit 587428b).

**Carrying evidence from Hallway Bowser is not possible:**
- After Hallway Bowser, Final Bowser phase 1 is a whole battle with unmodelled attacks.
- The phase 1 -> 2 transition and the Peach/Twink cutscenes are not measured.
- The lightning (two periodic sources, periods 130 and 220) adds draws whose phases are unknown.
- So the seed must be found in phase 2 itself.

**A lock there costs about 43 bits:** 38, plus about 5 for the 130-period phase, if p130 = p220 mod 5 holds.

**What zero-wait observation can give in phase 2:**
- The menus on each turn, about 2-3 s.
- A Life Shroom revive if Mario is KO'd: 399/403 frames with the coin up, 953-976 steps in three clusters by attack,
  about 13 s of coin, about 10 bits less 2-3 for the spread.
- Bolts of the 220 source: these fix that phase, not the seed.

Even two revives and a few menus come to about 15-25 bits. That is far from 43, so the candidate set stays in the
millions.

**What that means for the bounce:**
- With that many candidates every confirm frame scores the prior: 6+ 6.8%, 7+ 1.2% with no information (from
  `fb2model.js`).
- A useful best guess needs a few hundred candidates or fewer, i.e. about 35+ bits.
- **Zero-wait gives no edge in FB2.** The page should say so and let the runner press normally.
- **What would change that:**
  - modelling phase 1 and the transition, so a lock found earlier carries in
  - a much faster on-screen readout than the coin

**If the runner ever accepts a stand:** section 3 of the powerbounce README gives what a lock reaches. With a 2 s
window and +-1 frame presses: 6+ 59%, 7+ 27%.

## Files

| file | what it is |
|---|---|
| `zw_scene.py` | scene RNG probe (A pace: fixed, human-like, or B held) |
| `zw_sched.py`, `zw_schedcheck.py` | the B-held scene schedule and its frame-by-frame check |
| `zw_kpa83.py` | attempt at the kpa_83 Jr. Troopa scene (redirect did not trigger) |
| `zw_gridB.sh`, `zw_gridX.sh` | grids: B held with the generic re-sync, and with the exact scene |
| `zw_callers.py` | rand_int callers, debug core (finished with B held, through frame 159) |
| `zw_groups.js` | Spiny Flip futures |
| `zw_sim.js` | zero-wait simulation |
| `zw_grid.sh`, `zw_grid.txt` | the grid above |
| `../test_zw_mix.js` | page test of the best guess |
| `../test_zw_hallway.js` | page-driven test of the zero-wait tracker, with error cases |
| `../test_walk_counter.js` | the walk counter |
| `zw_barvis.py` | when the status bar is on screen around the scene (bar back 450 frames after the scene starts) |

## Not measured
- The real post-Jr.-Troopa walk time with C-up up (60 s assumed; 45 s gives nothing, 80 s gives +19).
- Whether the status bar shows during the battle intro.
- The kpa_83 after-battle cutscene, the battle exit and any level-up in the emulator. The decomp shows messages, NPC moves
  and camera pans only.
- Console load frames.
- An emulator end-to-end run of the zero-wait route: no savestate chain from Jr. Troopa through the walk to the hallway.

## Update: the Charge lock (charge_live/README.md)

The tracker can now also start from the Charge rays on Hallway Bowser turn 1 (no walk lock needed): seed x q x lag 0-2
particles at the Charge's frame 0. For that path the Spiny Flip window is +40..+175 (thrown with A) and its confirm,
read from the bar hiding (`HUD_HIDE.hw_spiny`), is carried at -1/0/+1. Two changes affect every tracker run:
- Spiny Flip particles merge once Bowser's AI has run (evMax = impact + 45; his attack's own draws are tracked in
  `S.extra`), instead of 260 frames later. Same RNG states, fewer particles at the plan.
- The plan starts by itself on Time Out's target screen when the tracker is on, even without a page lock (it needed
  `st.lock` before, so a tracker started from candidate seeds never planned by itself).
- The beep lead defaults to 1.5 s (a saved 4 s is moved to 1.5 s once).
