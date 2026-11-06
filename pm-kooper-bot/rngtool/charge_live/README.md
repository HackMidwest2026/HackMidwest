# Time Out Timer v72: reliability (Nov 6)

What changed, why, and the before/after numbers. Tests: `charge_live/test_zw_tolerant.js` (node, in `run_suite.sh`),
`test_beeps_stop.js` (in `run_suite.sh`), `test_zw_wait.js`, `test_dup_plan.js`, the frame-fed `test_charge_feed.js` on
the 14 Hallway clips and `test_dup_page.js` on three Duplighost renders (not in the suite: video / renders in /dev/shm).

## 1. The tracker weighs its states instead of dropping them on one missed or false shine
**Before (v71):** a state was dropped on any predicted shine the coin did not show while steady, and on any seen shine it
did not have. One missed shine (a busy browser, the v70 T2 run of 20-54-59) lost the true seed.

**Now** (`zwStep`, `zwUpdate`, `zwDoubt` in page_template.html): every state carries a weight = prior x the likelihood
ratio of what the coin did, against a background "the coin is unrelated to every tracked state" (a random coin):
a seen shine it has x(1 - pMiss) / (W (rho + lambda)) (~20; W = the match window, -1.5 .. +tapLate frames), a missed shine
x pMiss, a seen shine it does not have x lambda / (rho + lambda) (~0.02); the background is weighed by exp(-rho) per frame
of steady coin (rho = 0.3 / 31.2, a random coin's shine draws per frame). A state is dropped only when it is 10^4 times
less likely than the best one, or has more than 3 errors. The background keeps the prior mass that the lock or the model
is wrong (5% at the lock, 3% more at the Spiny Flip confirm); its posterior share is the **doubt**:
- the chance shown and used for the edge is (1 - doubt) x the states' chance + doubt x blind (Time Out 31%, Duplighosts 3+ 47% / 4 13%);
- doubt 50%+: no beeps; the sidebar says "Charge lock: DOUBTFUL", the strip "Lock doubtful";
- the sidebar shows the fit ("fit 98%", and how many shines the best state did not fit).

**The detector's rates**, measured (rule-of-three upper bounds used):
- the runner's logs: every shine-locked stretch with a clean coin model (seeds c4d16d21, 489 s; 9e314ac1, 66 s): 161
  predicted shines, **0 missed**; 556 s of steady coin, **0 false** (`tools/detector_rates.py`: the detections incl. rejected ones vs the
  seed's coin; two other locked stretches, 7f1e2578 and 52467bd0, leave the plain coin model after their lock (a carried turn / the walk) and are left out: the script's totals include them);
- the 14 clips, frame-fed (v72 T1 runs): the best state at Time Out matches all 31 shines seen after the lock (0 missed,
  0 false; 15-30-15 excluded, see 2); the v70 T2 run of 20-54-59: 1 missed of 5 (frames dropped);
- pMiss = 0.02 (3 / ~190 shines), lambda = 1.8e-4 per frame of steady coin (3 / 16,700 frames).

**Before / after** (`test_zw_tolerant.js`, the 14 clips' coin timelines as the page read them, `charge_live/clip_events.json`;
the lock 0.3 s after the rays and 1 s after the Spiny Flip confirm):

| | v71 | v72 |
|---|---|---|
| no error: states / Time Out share at the real confirm | e.g. 20-53-09 4 / 0.916, 15-20-15 2 / 0.737 | 4 / 0.916, 3 / 0.737 (every clip within 0.015 of v71) |
| one shine after the lock removed (33 shines x 2 lock times) | **seed lost in 34 of 66** | **0 of 66** (all the clean run's states kept, at least 28% of the weight; 15-30-15: doubtful, see 2) |
| one false shine in a quiet visible stretch (4 x 2) | lost in 2 of 8 | kept in 8 of 8; doubt 50%+ (no beep) in 2 (15-18-30) |
| 20-54-59 (the v70 miss): each of its 5 shines removed | lost in 5 of 5 | 0 of 5, share 0.98-1.0 |

**Honesty** (same test, simulated: 120 random games through the same tracker, the Spiny Flip impact / guard / confirm read
error / console lag drawn, the detector missing 2%, false shines at lambda, flashes read -1 .. +3 late; 1 game in 12 with a
wrong lock; 39 skipped where Bowser's attack was still drawing at the screen): v72 beeped 78 of 81, shown 69.4% against
72.1% in the game; mean outcome with a blind press when no beep: v71 69.4%, v72 70.6%. On the 7 wrong locks both versions
beep on states that fit the T2 coin by chance (v71 4, shown 69% / game 38%; v72 5, 75% / 55%): with ~10^4 hypotheses and
2-3 shines, chance fits are common; the background's 5% prior is what the shown chance assumes.
`test_zw_wait.js` (v69's seed loss while waiting) passes: the state survives 25 s of replans, 3 beeps each.

## 2. Clip 15-30-15: the seed dies 6 s after the turn-2 shines
Reproduced (v71, node and frame-fed): the states left after the two T2 shines (clock 304, 376) are **Claw Swipe** states
(Bowser's AI on clock 234); they predict a shine at 472/473, which the clip does not show, and die at 477-481.
**The clip shows a Body Slam** (Bowser jumps on Mario; HP 10 -> 5, "Nice"), with the Spiny Flip's hit picture at
5.76 s after the trigger, i.e. Bowser's AI on clock ~219-221. So the states that fit the two T2 shines were a chance
fit, and the true state had already been dropped. Under the model **no** state with a Body Slam with its AI on clock
205-235 fits the coin with fewer than 2 errors, for any q (0..47), the Spiny Flip confirm read anywhere from 8 frames
early to 3 late, guard or not, or extra draws (1-12) in the Body Slam. Ruled out in the emulator: the Spiny Flip's aim
sparkle ending at an early A throw (`_spk_throw.py`, throw at +56: the sparkle still redraws until +118, impact +80,
AI +124, as modelled). **Not found**: the true state leaves the model between the rays and Bowser's AI (an unmodelled
draw or a wrong q/seed); it needs an emulator replay of this clip's inputs, which the clip does not give exactly.
v72 on it: the states' chance at the real confirm is 5% (No edge) with doubt 12%; with one T2 shine missed doubt rises to 76% (no beeps).

## 3. Duplighosts 1234abcd: the true q not among the candidates
Reproduced with a new render (seed 1234abcd, Charge confirm 25 frames after the target screen opens: bfdda85d at the rays,
true q 42): v71 kept q 35-41 (0.5% / 6 at most; 42 not offered), the menu check fit none ("kept all").
**Now:** q within 2% of the best, up to 10 (v71: 0.5%, 6), and the menu check (`chgQBack`) is a likelihood with the
tracker's constants, not a filter, on the console frame time, with a -1.5 .. +4 frame window. v72 on the same render:
q 38-47 from the rays, the menu weights 39/42/45/46 0.25 each (true 42 kept), 6 states at Strategies, plan +264: 3+ 99.98%,
4 31%; emulator at +263/+264/+265: 4 / 3 / 3 copies (the page's top state: 4 3 3). The other two renders (D = 25):
9e3779b9 (fc590fa8, q 18): q 18, plan +252 3+ 75%, emulator 3/3/2 (page 3 3 2); 5eed0071 (2dfcc393, q 18): the rays
put q 17 best (15-18 within 2%), the menu gives 18 0.997: plan +279 3+ 100%, emulator 3/3/3.
**The 2.5-3 frame late flash**: measured on the raw Glide64 renders, the coin's main flash (white pixels in the coin
box) is on render frames draw +6 and +7, and the burst on render frame 3 reads +7.4 / 13.1 / 19.1 above the menu, the
console curve's 7.2 / 12.5 / 19.4: the burst sits where the console puts it, the coin flash ~2 frames later. On console
(20-54-59, its 5 shines) the flash is a single 2-frame burst with no early part, read at draw + 4.8 on the burst clock
(v70: offsets -0.3 .. +0.4). So the late flash is the emulator's rendering of the HUD coin (the same display list on the
console shows it earlier), a **simulation artifact**, not a model error; the page tolerates both: the menu check and the
Duplighost tracker take flashes up to 4 frames late (tapLate 4; the Hallway's stays 3.5).
`test_dup_page.js` now sets Settings > Console frame time to 33.367 (the renders' rate; `CRATE`), as does `test_fb2_page.js`.

## 4. Final Bowser on the console's frame time
`fb2_live.js` used 33.367 ms frames for the popup frame, the press times and the T7 plan: on a real N64 (33.427) the
picture 500 frames on read as frame 516.9 (true 516) and the press for +516 came 0.9 frame early. It now uses the measured
console frame time (`consoleRate`, default 33.427), fixed per fight at the trigger (`FB2.rate`): 516.00 and 0.00
(`test_zw_tolerant.js` section 4; with the setting at 33.367 the old numbers come back). The FB2 coin check is weighed as
in 1 (`fb2Prune`), and its T7 chance counts the background's share as no 7.

## 5. Silent wrong beeps
- **Beeps after the seed was lost.** v71 kept a running plan's beeps going after "Seed lost" (the strip said "showing old
  prediction" while it beeped) and after a late "Seed changed". Now, whenever the coin changes the states' weights, the
  planned frame is scored again (`zwPlanChance`): still good, keep; not good and the beeps can move, replan; else stop
  the beeps and say so ("Beeps stopped" / "Seed lost – beeps stopped"). `test_beeps_stop.js`: shines the tracked state
  does not have, read before the press: v71 kept beeping in 3 of 3, v72 stopped them 0.5-0.9 s before the press in 3 of
  3; a control with the state's own shines keeps its plan.
- The q filter (3) and the hard drop (1) could leave only wrong states that looked certain; both are weights now, and the
  doubt sends the shown chance back to blind when the coin fits badly.
- The plan log carries the states' chance, the doubt and the shown chance (`mix.pStates`, `mix.doubt`, `mix.p`).

## Frame-fed (v72, `test_charge_feed.js`, real time)
| Clip | Lock (seed, score, ratio) | q kept | States at Time Out | At confirm -1/0/+1 | v71 same day: q / states / at confirm |
|---|---|---|---|---|---|
| 15-14-09 | b400fca5 (6171, 3.54) | 3/4/5/6/7/8/9 | 22 | 0.22 / 0.32 / 0.16 | 3/4/5/6/7 / 31 / 0.22 / 0.31 / 0.15 |
| 15-15-06 | cf5894f0 (5374, 3.47) | 19 | 23 | 0 / 0 / 0 | 19 / 20 / 0 / 0 / 0 |
| 15-16-08 | 6d3b7b2b (5992, 4.48) | 30/31/32/33/34/41/42/43/44/45 | 238 | 0.34 / 0.33 / 0.1 | 40/41/42/44/45/46 / 39 / 0.3 / 0.12 / 0.51 |
| 15-17-02 | b3fb9c3b (5810, 2.4) | 18 | 39 | 0.89 / 0 / 0.86 | 18 / 14 / 0.23 / 0.63 / 0.85 |
| 15-18-30 | 2d5dd210 (6688, 4.02) | 34/36/37/41/42/43/44/45/46/47 | 282 | 0.23 / 0.06 / 0.05 | 40/41/42/45/46/47 / 36 / 0.1 / 0.02 / 0.04 |
| 15-19-21 | ea113ee3 (6338, 4.17) | 18/19 | 330 | 0.44 / 0.3 / 0.39 | 19 / 155 / 0.46 / 0.1 / 0.33 |
| 15-20-15 | 306686e9 (5893, 4.32) | 16 | 3 | 0.74 / 0.26 / 0 | 16 / 2 / 0.74 / 0.26 / 0 |
| 15-18-39 | dedb3e53 (7989, 3.89) | 5/6/7/8/9 | 1613 | 0.47 / 0.35 / 0.16 | 6/7/8 / 509 / 0.62 / 0.26 / 0.05 |
| 15-19-56 | 517b7c30 (5956, 2.77) | 4 | 3 | 0.7 / 1 / 0.3 | 4 / 2 / 0.8 / 1 / 0.2 |
| 15-22-53 | d066fdbd (5842, 3.07) | 4/6/8/9/10/11/12/13/14/15 | 7 | 0.02 / 0 / 0.02 | 4/6/11/12/14/15 / 3 / 0 / 0 / 0 |
| 15-25-30 | 180f546b (5715, 4) | 11 | 4 | 0 / 0 / 0 | 11 / 2 / 0 / 0 / 0 |
| 15-30-15 | ce0959dc (5917, 3.59) | 16 | 10 | 0.19 / 0.03 / 0 | 16 / 0 / dead at [480] |
| 20-53-09 | 7dc894b3 (5985, 3.65) | 12/13/14 | 6 | 0.89 / 0.65 / 0.59 | 13 / 4 / 1 / 0.85 / 0.83 |
| 20-54-59 | b59bef18 (6592, 4.07) | 15/16/17 | - | (no Time Out in the clip) | 15 / None / (no Time Out in the clip) |

All 14 lock their known seeds from T1 (one no-lock first on 15-18-39 and 15-19-21 in some runs, then the retry). From T2 the
runner's 7 clips lock the same seeds and set T1 (one T2 run of 15-25-30 said "Charge not seen: no Mario" (NCC 0.15) with 74
pictures dropped; two reruns locked it; the capture side is unchanged in v72). From the FB2 step both new clips take the
Hallway profile and lock; the FB2 clip itself stays no-lock (the aura). 20-54-59 with its target screen saved and a shine
search running (BUSY): 4 plans in the 8 s wait (96/88/69/100%), the seed kept. BAN0 (a forced wrong placement): the retry
locks b59bef18. The share at the real confirm moves between runs with the dropped pictures (as in v70/v71); the known
outcomes: 20-53-09 and 15-19-56 work (v72 T2: 0.92 and 1.0 at the confirm), 15-17-02 fails (0). More q kept means more
states (15-18-39: 1613 at Time Out, v71 509); the plan reads at most 64 of them.
Duplighost renders (`test_dup_page.js`, Settings console frame time 33.367 = the renders): 1234abcd q 35-45 from the rays,
menu weights 39/42/45 1/3 each, plan +264 (3+ 99.98%, 4 31%); 9e3779b9 +252 (75%); 5eed0071 q 17/18 (0.003/0.997), +279 (100%):
the same plans the emulator checked above.

## Route note
The route panel's note no longer asks for 60 s of coin on the walk after Jr. Troopa or for B held through the text: the
Hallway T1 Charge locks the seed by itself, and the T1/T2 menus' coin only confirms it. On the Charge-lock Duplighost
route: Charge first, then keep the C-up bar up in Bombette's menu (its shines decide between the possible first coin frames).

## Suite
`run_suite.sh` (with `charge_live/test_zw_tolerant.js` and `test_beeps_stop.js` added): every test rc 0 and both log replays
lock as before (1379.7 s on 83ebd9e1, 655.7 s on 52467bd0), except `test_strip_geometry.js` once in the second full run
(the now-line 0.075 frames off at the cue under load); it passed in the first full run (stopped at a 30 min limit after test_strip_geometry) and in 3 of 3 runs alone.
`charge_live/test_session_plans.js` reproduces the v68 log's plans, so it now uses the tracker as it was until v71
(git 2d69af1; `TRACKER=disk` for v72's).

**Still open:** 15-30-15's cause (2); the wrong-lock case (a chance fit of the T2 coin still beeps; only more shines
or a read of Bowser's attack from the picture would tell); pMiss and lambda are upper bounds from few events; the
Duplighost coin-flash timing on console (no console Duplighost Charge clip); test_fb2_page.js not rerun (its renders are gone).

# Time Out Timer v71: the Duplighost Charge-lock route (Nov 6)

The Duplighosts can now be played with the **Charge lock** as an alternative to the RTA turn (route panel: *Duplighosts
route*, RTA by default). The study is `../dup_charge/README.md` (14b2938).

**The route (Charge lock).** T1: Mario's Super Charge first (no Z), Bombette Do Nothing on the beep; aim 3+ copies, 4 ideal.
T2: Power Bomb, then Jump x2 on the one that did not transform (3 and 4 copies both end the fight with Ultra Boots).

**What the page does.**
- Profile **dup** (`CHG_PROF.dup`, step key `chg: 'dup'`): the Hallway's camera table (bit-identical in this room), the
  Hallway capture Mario patch (NCC 0.90 on this room's render), the study's suggested burst curve `CHG_BRIGHT_DUP`
  (unverified on console), the Hallway's trigger (a real bar hide, 250-1000 ms), placement, retries (up to 6 s after the
  rays) and q check. The lock starts the zero-wait tracker (seed x q x console lag 0/1), with no Spiny Flip events.
- **Arena**: the floor band's B - R (purple floor +5..+20 here, the Hallway's bushes -25..-50, Final Bowser's lit floor
  luma > 95), tested first. Over every 6th frame of 4 Hallway clips and the FB2 clip it never says Duplighosts (0 / 1610);
  on the console clip of the Duplighost fight (aad978a3, Surge route) it does on 167 / 252. A Hallway picture on the
  Duplighost step is a Hallway retry; the Duplighost room on a Hallway / Final Bowser step moves the route to the
  Duplighost step (Charge-lock route only).
- **Plan** on Bombette's Strategies screen (saved screen S): `zwChoose` with profile dup3 (3+ copies): on best chance the
  frame with the best 3+ chance and, within 2 points of it, the best all-4 chance; the window types (green / yellow / red),
  the beeps (default 3), beep and visual offsets are the Hallway's. The headline, the strip line and the Charge panel show
  **3+ and all-4 chances** for the planned frame; the strip's top band marks the all-4 frames.
- **No lock** (no clear seed, Charge not seen, seed lost, or no Charge on T1): "play it blind: Do Nothing whenever you
  like, 3+ about 47%, all 4 about 13%" (study blind 47.2% / 12.9%; the Surge route without a lock is the same draw).
- **Confirm / turns**: the Strategies screen closing is the Do Nothing confirm (press check against the plan); the route
  moves on and the tracker is turned off, so the Hallway's walk tracker can start later.

**Odds with the page's defaults** (1.5 s lead, 1 s max extra wait = 30 frames, presses 25/50/25 over -1/0/+1, the
console-lag-1 state at 25%): 3+ about 96%, all 4 about 35% (400 model cases; 2 s: 99% / 42%). The study's table header
says "1 s" for its 60-frame column; a 30-frame window there is 97.3% / 44.6% (no lag state).

**Tests.** `test_dup_plan.js` (in `run_suite.sh`): the route option; the page's predicted copies equal `dc_model.py` on
every frame (15200 / 15200: 40 cases x 2 lags x 190 frames; `dup_charge/plan_cases.json` from `dc_fixture.py`); 40 plans
scored by the model with +-1 presses: 3+ 96.3%, 4 30.6% (claimed 95.2% / 29.7%); no-lock texts; the tracker off after the
step; the arena on 12 console frames (Duplighost, 2 Hallway clips, FB2). `test_dup_page.js` (not in the suite: it needs
emulator renders in /dev/shm): renders of T1 (`jr_charge/jc_probe.py`, Glide64) through `fb2_route/t6_capsim.py`, fed to the
page at 60 fps, then `dup_charge/dc_e2e_press.py` plays the planned frame in the emulator:

| seed | lock (score, ratio, after the rays) | q (truth) | plan (Strategies on clock 203) | page: lag-0 copies -1/0/+1 | emulator -1/0/+1 |
|---|---|---|---|---|---|
| 1234abcd | bfdda85d right (5744, 4.06x, 2.8-3.7 s) | 45/46 kept (42): wrong | seed lost at clock 172, play blind | - | - |
| 9e3779b9 | 77f79aca right (5689, 3.56x, 2.5 s) | 12 (12) | +252: 3+ 75%, 4 0% | 3 3 2 | 3 3 2 |
| 5eed0071 | f7118e6f right (8270, 3.81x, 2.2 s) | 23 (23) | +259: 3+ 100%, 4 0% | 3 3 3 | 3 3 3 |

In the simulated capture the coin's flash reads about 2.5-3 frames later against the burst than the console calibration
(4.8 frames) assumes (menu shines read at -99.7 / -129.7 / -56.7 for true -102 / -132 / -60). With the true first coin
late in the rays (42), the rays left 41/43-47 and the menu check kept 45/46; the tracker then lost the seed. Whether that
offset is the simulation (Glide64 screenshot timing) or real is not known: no console Duplighost Charge clip exists yet.

**Not verified on console:** the burst curve in this room, the trigger and placement on a real capture, the arena rule at
a real Charge hide (only the Surge clip's hides), the coin-flash delay in this fight, the timing of the Do Nothing press
(the Strategies box vanishing 3 frames after the confirm, the dup3 profile's value), and the 2-hit Jump kill on the
runner's boots. Recordings that would: 4-6 attempts with the capture chain of the Hallway clips and the input display on,
from the T1 menu (bar up for 2 s+) through the Charge, Bombette's menu (bar up, the coin visible for a few seconds), the
Do Nothing confirm and all 4 copy rolls, at least one with the T2 Power Bomb + Jump; ideally with the page's session log
of the same attempt.

# Time Out Timer v70: the runner's feedback on v69 (Nov 6)

What the runner reported, what it was, and what changed. Tests: `test_strip_geometry.js`, `test_beeps_window.js`,
`test_calibrate.js`, `test_zw_wait.js`, `test_turn_backout.js` (all in `run_suite.sh`), and `test_charge_feed.js` on the 14
Hallway clips.

1. **"The white bar sits between frames."** In dark mode the white bar is the now-line (`--cursor`); the gold line is the
   aimed frame. Geometry is now explicit and tested: frame f is the cell [f, f+1); the now-line is at nowF + 1 - voff,
   i.e. inside cell f exactly while a press now (with the visual offset) lands on f; the aim marker is at target + 0.5 and
   meets the now-line at tLast + (target - 0.5 + voff) * rate (measured: within 0.012 frames, voff 0 / -6 / -4.5 / +2.3;
   the gold column on the canvas is within 0.5 px of the cell centre). What could put a marker between frames in v69:
   - the zero-wait plan drew the top state's frames but chose the frame by the mixture of all states, so the aimed frame
     could be a failing cell between two runs (two yellow 2-runs); the strip now shows the frames most states agree on, and
     "best chance" only aims at such a frame;
   - the run-length label "2" was drawn on the boundary between the two yellow cells; it is now in the middle of a cell;
   - the cells were drawn left-aligned (the gap after each cell), now centred on the boundaries;
   - v69 applied the shine-clock's display correction (up to 100 ms) to the tracker's plans too.
   With different beep and visual offsets, at the last beep the now-line is at target + 0.5 + (beep offset - visual offset):
   a half-frame difference puts it on a boundary at the beep, by design (the beeps and the strip are separate cues).
2. **"It stopped beeping after ~20 s of waiting."** Found and fixed:
   - **The cause:** `zwPlan` stepped every tracker state to "now" at each plan. A shine drawn in the last ~10 frames is read
     only ~6 + tapLate frames later, so the state was passed over that frame before the flash was seen, and the next
     update (the next plan, ~2 s later while waiting) dropped every state that had the shine: the true one with it, about
     a 25% chance per replan. `test_zw_wait.js` reproduces it: v69 loses the seed after 9-10 s of replans, v70 keeps it
     for 25 s. The tracker is now stepped only to the frames whose shines have had time to be read (`zwHorizon`), and the
     coin's watched stretch only to what was watched on a steady coin (`zwSeen`; v69 set it to now - 4 even with the coin
     hidden).
   - **The clock:** the Charge tracker ran on 33.367 ms frames; a real N64 runs 240p at 33.43 ms (the runner's logs:
     33.414-33.445 ms over 60+ shine runs). The clock fell a frame behind every ~18 s, shifting the beeps (~0.9 frame at
     the usual Time Out frame) and pushing the menu shines out of tolerance on long waits. The page now measures the
     console's frame time from every run of shines (`consoleRate`, kept in the browser; default 33.427; Settings >
     Advanced can fix it). The tracker's shine offsets on 20-53-09 went from a drift of +0.4..+1.2 frames to -0.3..+0.4,
     and the share of states for which Time Out works at the real confirm on the two clips that worked rose from
     0.67 to 0.85 (20-53-09) and 0.8 to 1.0 (15-19-56).
   - **Backing out:** B on Time Out's target screen counted as the Time Out confirm, so the attempt was marked done and
     nothing more was planned. A hand-on-Bowser screen closing with the status bar still up is now a back-out (a confirm
     hides the bar 2-3 frames later): not a press, the route stays, the beeps restart on return.
   - When the tracker is really contradicted, the sidebar says "Charge lock: LOST" with why, and the strip says "Seed lost".
3. **"It failed to capture the Charge once (31%)."** A no-lock leaves a blind press (31%). Hardened:
   - a dropped frame-3 picture made the trigger picture frame 4 (+12.5) or 5 (+19.4); v69 took it as frame 3 (every frame
     after it off by one, no lock) or, at +19.4, did not trigger at all. The trigger now accepts up to +25 and the
     placement chooses the trigger picture's frame (3, 4 or 5), and the clock anchor follows it;
   - the retry with other placements: up to 4 alternatives while there is time (9 s after the rays), and also when the
     first placement had no skip (a skip forced at frames 13, 9, 17, 21);
   - frame-fed (below): all 14 clips lock their known seeds from T1, the 7 runner clips from T2, both new clips from the
     FB2 step; the forced wrong placement (BAN0) is recovered by the first retry.
4. **Low-opacity frames** are now explained on the strip in words: "Seed lost – showing old prediction", "Waiting for
   lock", "Reading the Charge…", "Tracking N possible states", "Window passed – planning the next one", "Seed changed".
5. **The strip jumped.** The now-line stays at 25% of the width in every state (v69: 10% without a plan, 25% with one);
   clock changes are eased (50 ms/s, 200 ms/s during a plan so the aim still meets the line at the cue); between plans on
   the tracker the strip shows the tracker's own frames (v69 showed the example seed until the plan); a plan's window
   stays fixed in game frames, and when a shine rules its state out the page replans and says "Seed changed".
6. **Window type** (Settings): best chance (automatic), green 3+, yellow 2, red 1 (calibration). The first run of that
   kind that starts no earlier than the earliest frame and is aimed within the max extra wait; otherwise the page says
   there is none. The aim is the run's middle frame (for even runs, the middle frame more states agree on).
7. **3 or 4 beeps.** v69 planned from now + lead + 1 frame and ignored the beep offset: with -5 and 4 beeps 500 ms apart
   over a 1.5 s lead the first beep was ~150 ms in the past (and dropped) unless the chosen frame came 5+ frames later.
   Beeps is a dropdown (default 3, once moved from a saved 4); every plan takes the earliest frame for which the press
   and every beep are still ahead, so it always plays exactly that many (tested: beeps 1-5 x offsets -5/-3.5/0/+2).
8. **Manual controls** (Shine, Find seed, New segment, Plan press, Undo tap, the spin list, reaction / TV lag / shine
   beeps) are in a collapsed "Manual mode (tapping)" section; keyboard shortcuts still work. Download session log is
   next to Reset in the status panel.
9. **Calibrate from last press** is in a "Calibrate…" menu next to Press check: last press or the average of the last
   3 / 5, beep and/or visual offset, shows the change, applies on "Yes, change them", then clears the measured presses.
   The one-click Move beeps / Move visual buttons are gone.
10. **Settings:** Basic (window type, beeps, lead, beep and visual offsets, Charge area) always shown; Advanced (with a
   line each) collapsed.
11. **Turn identification:** Spiny Flip (T1) and Time Out (T2) share the hand-on-Bowser screen. A Bowser screen 9+ s
   after the Charge burst and after Bowser's attack (a 3 s+ bar hide) is Time Out (T1 -> T2); one 1-8 s after the burst
   with no attack is the Spiny Flip (T2 -> T1). With the back-out fix, B on either screen no longer moves the route.

Frame-fed on v70 (`test_charge_feed.js`, real time; "at confirm" = share of states for which Time Out works at the
real confirm, -1/0/+1). With the console's frame time the prediction at the real confirm agrees with every known outcome
(15-17-02 now 0.24, it failed; 15-20-15, 15-19-56 and 20-53-09 worked):

| Clip | Seed (score, ratio) | Spiny c | States | At confirm | Earlier builds (README; the clip's actual outcome) |
|---|---|---|---|---|---|
| 15-14-09 | b400fca5 (7075, 3.94) | 105 | 30 | 0.27 / 0.39 / 0.09 | 0.39 / 0.09 / 0.08 (fails) |
| 15-15-06 | cf5894f0 (5702, 3.74) | 105 | 20 | 0 / 0 / 0 | 0 / 0 / 0.02 |
| 15-16-08 | 6d3b7b2b (6572, 5.11) | 106 | 27 | 0.59 / 0.04 / 0.31 | 0.62 / 0.01 / 0.31 |
| 15-17-02 | b3fb9c3b (6197, 2.27) | 103 | 8 | 0.67 / 0.24 / 0.65 | 0.24 / 0.65 / 0.87 (actual: fails) |
| 15-18-30 | 2d5dd210 (7420, 4.37) | 102 | 36 | 0.11 / 0.02 / 0.01 | 0.18 / 0.04 / 0.17 |
| 15-19-21 | ea113ee3 (7772, 4.73) | 102 | 24 | 0.3 / 0 / 0.16 | 0 / 0 / 0.78 (fails) |
| 15-20-15 | 306686e9 (6894, 4.45) | 106 | 2 | 0 / 0.76 / 0.24 | 1.00 (works) |
| 15-18-39 | dedb3e53 (8366, 3.95) | 105 | 501 | 0.26 / 0.05 / 0.18 | 0.44 / 0.10 / 0.13 (fails) |
| 15-19-56 | 517b7c30 (7004, 3.59) | 104 | 2 | 0.8 / **1** / 0.2 | 0.2 / 0.8 / 0.2 (works) |
| 15-22-53 | d066fdbd (5967, 3.06) | 102 | 3 | 0 / 0 / 0 | 0 / 0 / 0 |
| 15-25-30 | 180f546b (5913, 4.10) | 103 | 2 | 0 / 0 / 0 | 0 / 0 / 0 |
| 15-30-15 | ce0959dc (6189, 3.75) | 103 | 0 | No edge (dies at 481, as before) | No edge |
| 20-53-09 | 7dc894b3 (7476, 4.54) | 107 | 4 | 1 / **0.85** / 0.83 | 0.75 / 0.67 / 0.27 (works) |
| 20-54-59 | b59bef18 (6671, 3.94) | 101 | alive | (not pressed) | |

From T2 the runner's 7 clips lock the same seeds and set T1; from the FB2 step both new clips take the Hallway profile
and lock; the FB2 clip from T2 moves the route to FB2. 20-54-59 with its target screen saved (REF=1300, a shine search
running): 4 plans in the 8 s wait, the seed kept through 5 shines (v69 also kept it in this clip: no shine fell in the
last 10 frames before a plan). BAN0 (a forced wrong placement): no lock (1714, 1.04x), the first retry locks b59bef18.
One T2 run of 20-54-59 lost the seed at frame 405 after the coin detector missed a shine (a busy frame feed); the tracker
still drops a state on a missed shine.

Not changed: the Final Bowser tracker still runs on 33.367 ms frames (its tests are emulator renders); the shine-lock
clock keeps its own fit.

# Final Bowser phase 2, T6: the Charge lock -> the popup A (Close Call) -> T7 Power Bounce (Nov 3)

**Bottom line.**
- The page now has per-fight Charge profiles (`CHG_PROF` in `charge_live.js`): **hw** (Hallway T1, unchanged in what it
  computes) and **fb2** (the Final Bowser route's T7 step, whose pre is the T6 Super Charge). The FB2 profile reads the
  T6 Charge rays with the stage lightning as nuisance, keeps every RNG state the rays cannot tell apart, beeps the A
  that closes the "+3" popup (the Close Call lever, `fb2_live.js`), reads the frame that A happened on from the popup
  closing, follows the coin through Bowser's turn and beeps the T7 Power Bounce target A.
- **Emulator renders through the capture simulation, fed to the page in headless Chromium:** 8 of 8 T6 Charges locked
  the true seed (none wrong); pressing the beeped popup frame in the emulator gave **Close Call in 5 of 8** (the page
  said 41-63% each; a press without a plan is about 30%).
- **Time budget: not met on this machine.** The lock lands **1.6-2.6 s after the rays end** here (4 cores, 3 search
  workers, the page and the frame feeder on the same cores), against ~1.0-1.3 s for the lock, the plan and a 0.6 s
  countdown to fit before the window closes (+136). The plans above are therefore made "as if in time" (from frame
  +100 on). What it costs and what fixes it: below.
- **T7:** the page read the popup frame right in one of two phase-2 runs (off by 2 in the other); the coin during
  Bowser's turn left 337 and 853 states, so the T7 plan is near blind (7+ bounces planned at 6-7%; the emulator gave 3
  and 4 bounces). T7 needs the lightning phases pinned (see "Not done").
- **Real FB2 footage (14-47-09, Mario's Super Charge with the aura up):** trigger, frames, Mario (17 px right, NCC 0.85)
  and maps work; **no lock** (best 1871 at 1.05x the next), as expected: the aura's 16 draws per 20 frames sit between
  the ray draws and the aura profile (T1/T2/T4) is not built.

## The FB2 profile
| | Hallway (hw) | Final Bowser T6 (fb2) |
|---|---|---|
| route step | `hw_spiny` (pre: the T1 Charge) | `fb2_pb` (pre: the T6 Super Charge) |
| camera table | `readouts/data/charge_cams_mario_route.json` | `readouts/data/charge_cams_mario_fb2.json` (`fb2_route/t6_cams.py`, same method from an emulator T6 run; it equals the Hallway table to 0.000: same battle camera presets, Mario at (-85, 18, 0)) |
| Mario patch | `mario_ref.json` (route clip 15-15-06) | `mario_ref_fb2.json` (`fb2_route/t6_marioref.py`: emulator frame -1 through the capture simulation) |
| burst curve, trigger | `CHG_BRIGHT`, 5 above the menu | `CHG_BRIGHT_FB2` (capture simulation; frames 0-2 read 1.6/3.5/6.0, so the trigger is 7.5 above the menu, wider DP tolerance); the real FB2 clip's curve has the same shape (5.2, 9.4, 15.8 on frames 2-4) |
| nuisance | none | the lightning: one rand_int(359) per bolt, **before everything else on its frame** (then the effect creation, the coin, the ray redraws, the step); `fb2_route/t6_raycheck.py`: 3 emulator runs, 48/48 frames exact each, including bolts on frames 0 and 3 |
| stage 1 | effects A and B, K = 16384 | effect A only, K = 65536, started on frames 0..22 while the rays go on |
| stage 2 | `qscores` over q | `fb2full`: every lightning window pattern (1281 patterns from the phase pairs with p130 = p220 mod 5) x q |
| after the lock | the zero-wait tracker | the FB2 tracker / planner (`fb2_live.js`) |

Kernel changes (`kernel.c`, both profiles):
- **`stage1g`**: stage 1 by strides. For the part with the largest bound, both of its draws move by small constants
  along s = lo + r + g t (g up to 2^18 chosen per part), so its (speed, phase) cell is constant over runs of ~40 seeds;
  each run is scored once for that part and skipped whole when it cannot beat the threshold. **Same heaps as `stage1`**
  (checked: identical top-16384 sets, both effects, on 15-15-06 and 15-20-15), 1.5-2x faster.
- **Static dealing**: each worker gets its share of the bases (round-robin in bound order) in one message and runs
  them with no round trips (a worker's heap is the exact top K of its bases, so the union's top K is exact). Before,
  each chunk waited for the main thread, which stalls when the page is busy.
- The joint stage does its LCG jumps in the workers (same numbers).
- **FB2 stage 2** (`fb2variant`, `fb2full`, `fb2ub`, `fb2end`): all draws are single LCG steps, so a lightning pattern
  only shifts the stream; the score is a sum over frames of g[n][k] (frame n's redrawn rays with k extra draws before
  them), so each (pattern, q) costs one prefix-sum lookup per insertion. Effect B's creation moves with the bolts on
  frames 1-3 and a coin on 0-2 (4 variants). With no bolts it equals `full()` to 0.001 (all q, Hallway clip).
  Candidates are scored in decreasing upper bound until the next bound is below 1/1.8 of the best.

Hallway after these changes (deterministic feed, `test_charge_feed.js`): 15-15-06 locks cf5894f0 q19 in 3.8 s (was
5.5 s), at the Time Out confirm 0/0/0.02, beep +66 (61%), as before; 15-20-15 locks 306686e9 q16 in 3.6 s (was 5.2 s),
beep +46 (75%). `run_suite.sh` (full, after these changes): all 24 tests and the torch maze rc 0, both log replays lock as before (1379.7 s, 655.7 s on 52467bd0).

## After the lock (fb2_live.js)
1. **States.** The rays pin the stream only where the bolt draws shifted it: insertions in the first ~9 frames (no
   redraws yet) and the last ~7 (faded rays) barely change the score, so several end states fit (in the emulator run
   r1 the true pattern scored 8216 against a best of 8218). The page keeps every (pattern, q) within 0.2% of the best,
   each with every phase pair behind that pattern (and console lag 0 / 1 frame after the rays, 0.75 / 0.25): 85-4000
   states in the runs below (an even sample of 4000 when more).
2. **Popup plan.** For every state and every K in the rest of the window, Bowser's AI on K + 40 and the Close Call
   roll (t6model.py, ported; Bowser's T5 attack from the new setting rules out Body Slam / Claw on T6). The beeped
   frame maximises P(Close Call) over the states with presses 25/50/25 over -1/0/+1; among frames within 3 points of
   the best, the one with the best P(Close Call and 7 bounces with the best T7 window) wins (sampled states). Three
   beeps 0.3 s apart, the last on the press, timed as Time Out's.
3. **K seen.** The popup (a bright box across the top middle) is up on frames 76..K+1; the first picture without it
   shows frame K + 2 (emulator: K = 100 -> 102, 120 -> 122; no press: K = 137). Dropped pictures around the closing
   widen it to a range of K, all carried. Fallback: the status bar comes back on K + 5.
4. **Coin.** The status bar is up through Bowser's turn and the T7 menu: every shine seen must be a predicted one
   (+-2, up to 3.5 late) and every predicted shine while the coin was steady must have been seen.
5. **T7.** On the Power Bounce target screen (the step's B screen): the target-A frame in the beep window with the best
   P(7 bounces) (the kill at 80 HP: 15 + 14 + ... + 9), 0.1 x P(6+) as tie-break; the page's usual lead, window, beeps.

## Results (emulator T6 renders -> `fb2_route/t6_capsim.py` -> the page, `test_fb2_page.js`)
Build b1 (`route_build.py 1234abcd`, T5 Fire Breath, so Body Slam and Claw allowed on T6), the page told "Fire Breath".
Plans made as if the lock had landed by +100 (`KAT=100`); the emulator then pressed the beeped frame and its
neighbours (`fb2_route/t6_press.py`).

| seed (PRE) | bolts in the rays | lock | after the rays | states | beep K, P(CC) shown | CC at K-1 / K / K+1 |
|---|---|---|---|---|---|---|
| 0badc0de (60) | - | true | 1.6 s | 2382 | 136, 53% | no / **yes** / no |
| a5a5f00d (60) | - | true | 2.3 s | 4000 | 104, 61% | yes / **yes** / no |
| 13579bdf (60) | - | true | 2.0 s | 1137 | 133, 58% | yes / **yes** / no |
| deadbeef (60) | - | true | 2.0 s | 1092 | 101, 56% | no / **yes** / no |
| 5eed0fb2 (60) | - | true | 2.5-2.9 s | 4000 | 135, 56-59% | no / no / no |
| 00000001 (60) | - | true (K = 65536; at 16384 its A score ranked below the cut: no lock) | 2.0 s | 1530 | 121, 63% | no / no / yes |
| c0ffee11 (90) | 18 | true | 2.3-2.6 s | 85-169 | 127, 41% | no / no / no (true state kept, outvoted) |
| feedf00d (100) | 8, 38, 43 | true | 2.0 s | 383 | 100, 58% | yes / **yes** / no |

Close Call at the beeped frame: 5/8; with the 25/50/25 press error 0.44 on average (the page said 0.56). Lock scores
5900-7800 at 3.4-5.1x the next (wrong ones ~1700); 8/8 right, 0 wrong.

T7 (phase-2 renders with the popup pressed on a Close Call frame, through Bowser's turn to the target screen):
| seed | K true / seen | states after the coin | beep d, P(7) / P(6+) shown | emulator d-1 / d / d+1 |
|---|---|---|---|---|
| a5a5f00d | 104 / 104 | 337 | 468, 7% / 25% | 4 / 3 / 3 bounces |
| 13579bdf | 133 / 135 | 853 | 441, 7% / 27% | 4 / 4 / 3 bounces |

**Time** (page in headless Chromium, 3 search workers, 4 cores shared with the page's own frame work and the feeder):
stage 1 (A only, K = 65536) 1.5-2.2 s of wall time, of which only 0.1-0.3 s ran before the rays ended (the main thread,
busy with the pictures, starts it late), the joint stage 0.1-0.4 s, stage 2 0.1-0.2 s, the plan 0.04-0.4 s. The search
alone is ~1.4 CPU-s of WebAssembly (`node`, one thread), so with 7+ free cores and the early start on time it would
end at about the rays' end and the lock would land ~0.4-0.6 s after them; on this machine it does not. The popup
window closes 2.5 s after the rays and the plan needs ~0.8 s of it for the beeps.

## Not done / not verified (FB2)
- **The time budget** (above). Ways to fix it, in order of payoff: more cores (the search parallelises); the lightning
  phases pinned before the Charge (the purple bolt onsets in the T6 menu: `fb_aura/clip_bolts.py` saw them on console)
  so stage 2 and the plan have 1-4 states instead of hundreds; the ray maps in a worker (the main thread computes them,
  ~0.2 s twice). Narrowing stage 1 with the T6 menu's coin does not work without the phases: the draws between the
  menu's coin and the Charge depend on them.
- **Lightning phases from the picture**: not read. That is also what limits the popup plan (5/8, the states outvote
  the true one) and T7 (hundreds of states left).
- The menu coin before the Charge (q, as chgQBack for Hallway): not used for FB2.
- `CHG_BRIGHT_FB2` and the popup box are from glide64 renders through the simulation, not console T6 footage.
- The beep timing for the popup and the T7 A is Time Out's relation (zwPlan), not measured on FB2.
- The aura profile (T1/T2/T4: aura + lightning) is not built.

# Charge lock: the seed from the Charge rays, live on the page (Nov 2)

On Hallway Bowser turn 1 the page reads gRandSeed from Mario's (Super) Charge rays while the run goes on, carries it
through Lakilester's Spiny Flip and Bowser's attack with the zero-wait tracker, and on turn 2 beeps the best Time Out
confirm frame (or says No edge). Nothing here makes the runner wait: the only added time is the beep window.

## The first live session on v68 (2026-11-03 evening) and what changed
Log timeout-timer-log-1793757328924 (the same session as -1793757228704, extended to 986 s), clips 2026-11-03_20-53-09
(the Charge at 856 s, Time Out worked) and 20-54-59 (the Charge at 966 s, "the thing doesn't load"). Clip times map to
the log by the bar's hides: 20-53-09 = log - 849.35 s, 20-54-59 = log - 959.63 s. Real N64, OBS 1280x720 60 fps.

| Charge (bar hide, s) | Lock | Seed, score, ratio | Time Out press err (frames) | Page: works | Actual |
|---|---|---|---|---|---|
| 218.9 | yes | f70bd8ab, 6948, 4.12x | +1.69 | no | ? |
| 282.6 | no | best 1766, 1.04x | (no plan) | - | ? |
| 348.1 | yes | de795e8e, 6776, 4.16x (Mario +16.5 px) | -3.27 | no | ? |
| 447.2 | no | best 1812, 1.07x | (no plan) | - | ? |
| 540.4 | yes | d815b1fa, 7518, 3.87x | -3.28 | no | ? |
| 612.1 | no | best 1499, 1.02x | (no plan) | - | ? |
| 659.3 | no | best 1988, 1.03x | (no plan) | - | ? |
| 749.5 | yes | 7424190f, 7355, 4.70x | -1.27 | yes | ? |
| 808.3 | no | best 1868, 1.13x | (no plan) | - | ? |
| 856.5 | yes | 7dc894b3, 7698, 4.44x | +0.71 | yes | **works** (clip 20-53-09) |
| 966.3 | yes | b59bef18, 7403, 4.13x | no beeps: target screen up 8 s | - | not pressed (clip 20-54-59) |

The runner reset after every Time Out, so only the clipped outcome is known. Frame-fed, both clips lock the live seeds
(7dc894b3 q 13, b59bef18 q 15); 20-53-09 gives 0.75 / 0.67 / 0.27 at the confirm (-1/0/+1).

- **No beeps on the last attempt (20-54-59): a shine search blocked the plan.** The page plans when the target screen has
  been seen for 300 ms (`autoPlan`), but `autoPlan` returned while any shine seed search ran. The turn-2 menu's coin
  (one stretch already in the chain since 966.1 s) started a chain search on its 2nd shine (980.2 s, reproduced by
  replaying the log's shines and coin returns through the page); the earlier one in this session took 11.5 s. The target
  screen came up at ~980.6 s and stayed until the log was saved at ~988.7 s: no plan, and no zwInconsistent (the tracker
  was never asked). Fed frame by frame with the target screen saved and a search running from the first turn-2 shine,
  v68 makes no plan; this build makes them (0.94 at 22.5 s). The zero-wait plan needs no search: `autoPlan` now only waits
  for a search when there is no tracker.
- **The route went into Final Bowser after every Time Out.** On Time Out's screen closing the route moved to the next
  step, which is now the Final Bowser step (FB2). A retry without a 10 s gap stayed there, and the next Charge was read
  with the FB2 profile: at 478-489 s and 704-708 s (Mario NCC 0.11 against the FB2 patch; the FB2 profile arms on any hide
  and triggered on the Time Out animation and later turns). The runner fixed the step by hand 7 times; replayed without
  those, v68 would have read 13 of the session's triggers with the FB2 profile (charge_live/test_route_replay.js). Now:
  - a target screen closing never moves the route from the Hallway into Final Bowser: after Time Out the route stays on
    Hallway T2 and plans nothing more there (`st.hwDone`, "Time Out is done for this attempt");
  - the arena is read at every arming of the Charge capture (`chgArena`): the band under the battle floor (320-space y
    165-190) and the top of the picture (y 40-100). Hallway: luma 45-67, blue excess B - R +27..+64 at all 43 bar hides
    of the 14 Hallway clips; Final Bowser: 114-116 and +4..+11 (clip 14-47-09). A black or faded picture is neither.
    Mario's patch cannot tell them apart at the hide (NCC 0.08 with either). On the FB2 step a Hallway picture arms the
    Hallway profile, and the burst sets the route to Hallway T1 (`chargeStepSet`). On a Hallway step a Final Bowser
    picture sets the route to the FB2 step and arms the FB2 profile, so FB2 is entered when its battle shows.
- **No lock on 5 of the 11 real Charges.** Mario 0.99 and 45-48 frames in all of them, and 612/659/808 had a clean
  capture (one 33 ms gap). The best seed was 1.5-2.0k at 1.0-1.1x: nothing fit at all, so it was not q (stage 2 covers
  q 0-47), Mario's position (dx 0) or the trigger (+7.4..+7.8 = frame 3 in all of them), and the move was the same (the
  Charge's rays are the same two energy_in_out effects for every Jump Charge level in the decomp; the FP used is 4 in
  both clips). What the clips show: the N64 sometimes runs a game frame with no picture of its own inside the rays (the
  capture shows 2 pictures per game frame throughout, but the burst and the rays are one frame ahead after it). On
  20-54-59 the brightness placement puts that skip at frame 17-18 and scores 7.2k; one picture per game frame scores 6.0k.
  Where the burst is flat (frames 9-17) the placement can put the skip a few frames early, and then everything after it
  is one frame off: a frame-fed run of 20-54-59 put it at frame 10 and gave "best 1684, 1.01x", the live no-lock's
  signature (an earlier session's T1 run on 15-18-39 did the same, 2094 at 1.01x). Not proven to be the live cause: the
  live pictures are not in the log. Two changes:
  - **retry**: a real Charge with no clear seed is searched again with the next-best placement (the assignments around
    each skip of the last one banned), at most twice (`chgRetry`, `CHG_ALTS`; 1.2-3.5 s per search live, Time Out's target
    screen comes ~12 s after the rays). With the first placement forced to the early skip, 20-54-59 gives the live
    signature (1713, 1.04x), and the retry locks b59bef18 (6987, 4.27x);
  - **the evidence**: a no-lock with Mario seen keeps its game frames (the last 2, greyscale JPEG, about 2 MB each) and
    Save log writes them (`chargeCaptures`); `tools/capture_u8.py` turns one into the rasters `tools/harness.c` reads. The
    no-lock log line also carries each effect's stage-1 best and K-th score (`s1`): one effect clear and the other at
    noise means its rays were read right and the draws between were not; both at noise means the pictures were placed
    wrong. Tried and dropped: weighting the placement by the capture's clock (2 pictures per game frame) put the skip
    late or nowhere and lowered every score (6.0-6.2k on 20-54-59).
- **"Charge not seen" (264, 390, 396, 595, 788, 794, 836, 841, 932, 940 s) are harmless.** None was followed by a Spiny
  Flip hide 3.8-4.0 s later, and each attempt's real Charge came 15-30 s after. Four (264, 595, 836, 932) are the battle
  intro after a long bar-up (14-44 s while walking): a trigger 980-1010 ms after the hide at +6..7, then +29 within
  0.3 s, which is the intro's brightening on both new clips (59 -> 88 in 0.3 s). Every real Charge of the session
  triggered 439-514 ms after its hide. The others had no burst at all. test_fix_proposal.js section 4 runs both clips'
  pictures after that prefix: the intro is rejected and the Charge still triggers 483 / 500 ms after its hide.
- **Press timing.** Every plan was one frame (`w: 1`); Time Out's working frames come in runs of 0-2 for all states
  left, so no window takes +-2-3 frames. The runner's presses on the beeps: +1.69, -3.27, -3.28, -1.27, +0.71 (mean -1.1,
  rms 2.3); the page's own calibration dropped the two -3.3 ones (it only took |err| <= 3; now 5). zwPlan scored frames
  with +-1 (25/50/25); it now uses the runner's own spread (a normal with the rms of the Press check presses, 0.7-3
  frames, once 3 are in: `pressDist`). Replaying the 5 planned attempts through the tracker (test_session_plans.js; every
  logged Spiny Flip frame and plan target reproduced), the chance Time Out works under the runner's spread goes from 0.50
  to 0.54 on average (0.34 -> 0.45 on the 348 s attempt). The pressed frames that worked by the page (749, 856) are
  the ones that worked in the replay; the three -3.3/+1.7 presses fell on failing frames.

Settings for the runner: **Beep offset -5 -> -4** (the presses averaged 1.1 frames early; 5 presses, so recheck after
10), Press check correction stays 0 (the one verified outcome, +0.71 at 856 s, read as working and worked).

Frame-fed on this build (`test_charge_feed.js`, real time; the full suite passes): all 14 Hallway clips lock their
known seeds from T1 (7 route clips b400fca5 ... 306686e9, the 5 earlier runner clips dedb3e53, 517b7c30, d066fdbd,
180f546b, ce0959dc, and 7dc894b3 / b59bef18 for the two new ones), with the same Time Out shares at the confirm as
before (e.g. 15-19-56 0.2 / 0.8 / 0.2, 20-53-09 0.75 / 0.67 / 0.27); the runner's 7 clips from T2 lock the same seeds
and set T1; 20-53-09 and 20-54-59 from the FB2 step take the Hallway profile, lock and set T1 (v68: FB2 profile, Mario
0.11-0.14, no lock); the FB2 clip from Hallway T2 moves the route to FB2 at its first bar hide and reads as from the
FB2 step.

Tests: `charge_live/test_route_replay.js` (log replay of the route: every trigger on a Hallway step, never the FB2 step;
v68 reproduces the FB2 reads), `charge_live/test_session_plans.js`, `charge_live/test_fix_proposal.js` section 4,
`test_charge_feed.js` with `STEP=fb2` (both new clips lock from the FB2 step and set Hallway T1; the FB2 clip from
Hallway T2 moves the route to FB2 and reads as from the FB2 step), `REF=1300 BUSY=1` (the plan with a search running)
and `BAN0` (a forced wrong first placement, for the retry).

## The runner's first live attempts (2026-11-03) and what changed
Logs timeout-timer-log-1793735643131 / -1793736599276 / -1793737154078 / -1793737237152 / -1793737413564 /
-1793737579773 and clips 2026-11-03_15-18-39, 15-19-56, 15-22-53, 15-25-30. Test: `node charge_live/test_fix_proposal.js`
(node only, against git afeaa5f as "before"); `test_charge_feed.js` on the clips; `test_hw_steps.js`.

- **Attempt 1: a correct lock and a dead carry.** The lock was ed937d1f q 21 (score 6835, 3.41x). It landed after the
  Spiny Flip confirm, so `chgStartTracker` rebuilt the menu's visible stretch from `CHG.pres` and ended it 4 frames
  before the bar hid. A shine drawn on frame f flashes at about f + 6 on this clock, and the true seed shines on frame
  117 (lag 0) / 118 (lag 1) with the bar hiding at ~122. So both particles died at 120 (reproduced exactly). The stretch
  now ends 6 frames before, as `zwInput` does (c - 4, c = hide - 2). With that, the seed survives all five turn-2 shines
  (about 6% of random seeds do too). `zwCoinBack` had the same 4-frame end, and it also ignored a `visTo` that a confirm
  had already set, so a coin box flickering after a confirm made hidden frames look visible. It now ends at
  min(visTo, hide - 6).
- **Attempts 2-6: the trigger fired on the wrong thing.** The cases were:
  - a hallway / battle-entry bar hide taken as the Charge confirm (bar up 2-67 s while walking);
  - a fade from black (base 2.4);
  - the battle intro's brightening while the bar was still hidden;
  - a coin-box flicker re-arming the capture 10 s later.

  In each case the page captured something that was not the Charge (Mario NCC 0.06-0.09) and searched it, while the
  real Charge went by. The real Charge's bar hide was then read as the Spiny Flip confirm, which shifted the route by
  one ("skips the Spiny Flip turn"). Now (hw profile; FB2 keeps its old rules):
  - arming needs a bar hide that ended a real bar-up of 600+ ms;
  - the trigger only counts 250-1000 ms after that hide (the burst's frame 3 comes 433-484 ms after it on all 11
    clips), and needs base >= 30;
  - every picture of game frames 5-27 must sit on `CHG_BRIGHT` (within +-1.5 frames and 10 levels, at most 3 misses);
  - a capture whose frame 0 has no Mario (NCC < 0.5) is not searched: "Charge not seen", and the page waits for the
    next real hide;
  - no burst in the window gives the same "Charge not seen".
- **The confirm is anchored on the burst.** The bar hide that would count as the hw_charge pre is held (`chgPend`) until
  the capture shows a real Charge. Otherwise it is dropped and the pre stays open, so a battle-entry hide never shifts
  the route.
- **Any Hallway step arms the Hallway Charge.** A Charge seen on T2 sets the route to T1 (`chargeStepSet`). A long gap
  (10 s+, a reload) on Hallway T2, or on the next step right after the route left the Hallway by itself (fewer than 3
  real bar hides since), sets the route back to T1 (`stepBackToHallway`).

Frame-fed (`test_charge_feed.js`; the patched build; real time, 60-170 pictures dropped per clip). "At confirm" is the
share of states for which Time Out works at the confirm (bar hide - 3 frames; -1 / 0 / +1):

| Clip | Lock (seed, score/ratio) | Spiny c | States | At confirm | Runner's result |
|---|---|---|---|---|---|
| 15-14-09 .. 15-20-15 (7 route clips) | all 7 lock their known seeds | 103-107 | 6-72 | as before (e.g. 15-17-02 0.24/0.65/0.87) | - |
| 15-18-39 (attempt 3) | dedb3e53 (7998, 3.98x); one T1 run said "no clear seed" (2094, 1.01x) | 105 | 595 | 0.44 / **0.10** / 0.13 | fails |
| 15-19-56 (worked) | 517b7c30 | 104 | 2-3 | 0.74 / **0.58** / 0.42; from T2: 0.2 / **0.8** / 0.2 | **works** |
| 15-22-53 (savestate fade) | d066fdbd | 102-103 | 3 | 0 / 0 / 0 (T2 was Focus) | - |
| 15-25-30 (battle intro) | 180f546b (5042, 3.86x) | 104 | 2 | 0 / 0 / 0 | - |
| 15-30-15 | ce0959dc (6169, 3.72x) | 103 | 0: No edge | - | - |

Started on Hallway T2 (STEP=t2), the 5 runner clips lock the same seeds and set the route to T1. In 15-30-15 the
tracker keeps 5 states through both turn-2 shines and loses them in the 6 s after, which show no flash. That is not
explained (a missed draw in T1 or Bowser's turn, or a coin that did not show).

## What the page does

1. **Arming.** On the route's Hallway T1 step, when the status bar hides (the Charge confirm hides it 3 frames after
   the confirm), the page starts keeping capture frames, each drawn into the 640x480 game raster (2 px per 320-space
   unit, the capture map fitted for this OBS setup: 1280x720, `CHG_MAP`) as luma.
2. **Trigger.** The burst (`radial_shimmer`) brightens the game area. The first frame 5 levels above the median of the
   frames before it is game frame 3 (frame 0 = Charge confirm + 13). Calibrated on all 7 route clips (the true frame 0
   from the seed's score). A trigger that does not keep rising (+15 by 0.35 s) is dropped.
3. **Game frames.** The browser drops pictures and its frame times jitter by +-17 ms, so each new picture is placed by
   dynamic programming on the burst's brightness curve (`CHG_BRIGHT`, the same in every Charge: sd < 0.7 levels over 7
   clips) and the time between pictures. Frames 0-2 and -2/-1 are taken by time.
4. **Mario's position.** In 2 of the 7 clips (15-14-09, 15-19-21) Mario stood 16.5 raster px (6.1 world units) to the
   right of the reference. That, not the burst, is why those two failed offline: the rays are centred on him. The page
   finds him by normalised cross-correlation of a high-passed patch (`mario_ref.json`, frame -1 of 15-15-06) on frames
   -2..1 and moves the ray centre by 0.37 units per px.
5. **Ray maps.** For each of the 48 frames, every integer angle and every 4-unit step from the centre: luma on the
   projected ray minus beside it (+-2 px in 320 space), through the per-frame camera table
   (`readouts/data/charge_cams_mario_route.json`). **The burst is removed per angle:** each angle's median over
   distance is subtracted (the burst's streaks run the whole radius, a ray is a 128-unit segment). No emulator render
   is needed. Tested against the old emulator-render subtraction on the 5 clips it handled: the same lock margins.
6. **Search** (`kernel.c`, WebAssembly in workers, all cores but one by default):
   - Stage 1, per effect (A: scale 1.2, frame 0; B: scale 0.8, frame 3, whose base draw is the 25th or 26th LCG step
     after the seed): an effect's 10 initial rays depend only on the state s1 after its base-angle draw, and s1 lies in
     that base's interval of 2^32/361 states. Each base has an upper bound (the best ray score at each part's angle).
     Bases are searched in decreasing bound with branch and bound against the running K-th best (K = 16384, parts in
     decreasing bound order, each part's two draws by LCG jump constants). A base whose bound is at or below the K-th
     best is skipped, so the top K of all 2^32 per effect is exact. 20-50 bases of 361 are searched.
   - Joint: each candidate's other effect's initial rays are scored exactly; the top 300 go to stage 2.
   - Stage 2: the full simulation of both effects over 48 frames for every first-coin frame q (0..47, then 24/48).
   - **Lock** if the best score is at least 3000 and 1.8 times the next (true seeds 3300-8300 at 2.3-5.4 times the
     runner-up on the route clips; wrong ones 750-1500 at 1.0-1.2).
7. **Tracker.** The lock starts the zero-wait tracker (`zw*` in page_template.html) at frame 0 with particles
   seed x q (every q within 0.5% of the best; late first coins barely move the rays) x console lag 0/1/2 frames after
   the rays (weights 0.7/0.2/0.1). The coin's shines and visible stretches seen while the search ran are added. The
   Spiny Flip confirm (read from the status bar hiding, `HUD_HIDE.hw_spiny = 2` frames, carried at -2..+1: a dropped
   picture only reads it late) splits each particle over impact +40..+175 (thrown with A) x guard. At most 6 q are
   kept (best first) and lag 0/1, so a split stays under the tracker's 40000. Shines may read up to 3.5 frames late. Particles merge once Bowser's AI has run and his attack's
   draws are done. The turn-2 menu's coin prunes them; Time Out's target screen beeps the best frame in the window
   (or No edge, as before).
8. **q from the turn-1 menu** (`chgQBack`): for each q the coins before frame 0 follow from the seed stepped back; the
   menu's seen shines must match. Not exercised by the route clips (they start ~1 s before the menu, so no menu stretch
   was long enough), so **unverified**.

Sidebar: "Charge lock: yes/no", time to lock after the rays end, the hypotheses left, the seed and q.

## Files
- `kernel.c`: the search (stage 1, joint, stage 2); `build_kernel.sh` compiles it to `kernel.wasm.b64` (clang wasm32),
  which `build_page.py` inlines.
- `charge_live.js`: the page side (capture, trigger, frames, Mario, maps, workers, lock, tracker start, sidebar).
- `mario_ref.json`: Mario's reference patch.
- `tools/gameframes.py` (clip -> game-frame rasters with the page's rule), `tools/jsmaps.js` (the page's own maps code
  in node), `tools/harness.c` (the kernel natively, single thread).
- `../test_charge_clips.js`: the 7 route clips through the page in headless Chromium in real time.
- `../test_charge_feed.js`: the same with the frames fed one by one at their real times (no video decoding).
- `fb2_live.js`, `mario_ref_fb2.json`, `tools/harness_fb2.c`, `../test_fb2_page.js`: the Final Bowser profile (top section).

## Results

### Offline, the page's maps code + kernel (tools/, native, 1 thread)
| Clip | Seed | q | Score | x runner-up | Stage 1 |
|---|---|---|---|---|---|
| 15-14-09 | b400fca5 | 7 | 7088 | 3.92 | 3.8 s |
| 15-15-06 | cf5894f0 | 19 | 5878 | 3.79 | 5.8 s |
| 15-16-08 | 6d3b7b2b | 41 | 7045 | 5.18 | 4.7 s |
| 15-17-02 | b3fb9c3b | 18 | 6397 | 2.30 | 7.7 s |
| 15-18-30 | 2d5dd210 | 42 | 7467 | 4.38 | 5.3 s |
| 15-19-21 | ea113ee3 | 19 | 8235 | 4.94 | 5.4 s |
| 15-20-15 | 306686e9 | 16 | 7400 | 4.65 | 5.7 s |

All 7 lock, including the two that failed before (Mario's position). The 5 earlier seeds are reproduced.

### Live, in headless Chromium (test_charge_clips.js)
Each clip played in real time by a `<video>` and handed to the page as its capture (VP9 re-encode, crf 8). The page
starts on the Hallway T1 step with no walk lock: the rays are the only seed source. "Lock" is after the rays end;
Time Out's bar hides 11.8-12.6 s after the rays end in every clip, so that is the deadline. "At confirm" is the share
of the tracker's states for which Time Out works at the real confirm (bar hiding - 3 frames; -1 / 0 / +1). "Beep" is
the frame the page would have beeped had the runner waited on the target screen (lead 1.5 s, window 1 s), relative to
the real confirm, with the chance it showed.

**This machine was shared with another session running 4 CPU-bound threads for most of the testing (load 5-9 on 4
cores)**, so the browser dropped pictures and the search ran on what was left. Final build, run with the lowest load
(load 1.8 rising to 6):

| Clip | Lock | Seed, q | Time to lock (search, 3 workers) | States at plan | At confirm (-1/0/+1) | Predicted | Actual | Beep (shown) |
|---|---|---|---|---|---|---|---|---|
| 15-14-09 | yes | b400fca5, 3-9 | 4.0 s (3.7) | 11 | 0.39 / **0.09** / 0.08 | fails | fails | +50 (61%) |
| 15-15-06 | yes | cf5894f0, 19 | 5.5 s (5.3) | 8 | 0 / **0** / 0.02 | fails | fails | +66 (61%) |
| 15-16-08 | yes | 6d3b7b2b, 41-47 | 4.2 s (4.0) | 8 | 0.62 / **0.01** / 0.31 | fails | fails | +71 (91%) |
| 15-17-02 | yes | b3fb9c3b, 18 | 6.0 s (5.7) | 9 | 0.23 / **0.63** / 0.85 | works (wrong) | fails | +49 (90%) |
| 15-18-30 | yes | 2d5dd210, 35-42 | 5.1 s (4.9) | 20 | 0.18 / **0.04** / 0.17 | fails | fails | No edge (34% < 40%) |
| 15-19-21 | yes | ea113ee3, 19 | 10.0 s (9.7), load 6-8 | 3 | 0 / **0** / 0.78 | fails | fails | +47 (73%) |
| 15-20-15 | yes | 306686e9, 16 | 13.5 s (13.2), load 6-8 | 0 | - | No edge | works | No edge |

An earlier build (before the q cap and the -2..+1 Spiny shifts, at load ~3) gave all 7 with the tracker alive:
15-20-15 locked 5.2 s after the rays, **1.00 at the confirm (works, actual works)**, beep +46 (75%); 15-17-02 0.00
(fails, actual fails); the other five as above. Over 11 full runs of the 7 clips during development (several builds) the rays
locked the right seed in 68 of 77 clip runs and never locked a wrong one. The misses: 15-16-08 eight times (its true
seed is the weakest offline, ranked ~40th after the joint stage; every miss was at load 5-9) and 15-18-30 once (an
early build's frame placement).

Under heavy load the carry after the lock is what breaks: the bar-hiding read of the Spiny Flip confirm came 5-10
frames late twice, and a lock that lands after the turn-2 menu has nothing to prune with; both end as "No edge" (the
page never beeps on states that do not fit). 15-17-02's 0.63 at the confirm is the one wrong prediction; that clip had an
unexplained coin before the Charge in the offline fit too.

Lock time on this machine: 3.7-5.7 s of search with 3 workers at moderate load (single thread, native: 3.8-7.7 s).
Maps: 0.15-0.3 s. Capture: 3-4 ms per picture while armed (about 2 s).

## Not verified
- Only this capture: 1280x720 OBS of a GV-USB2, with this crop (`CHG_MAP`). Another crop or capture card needs the map
  refitted; the Mario check (NCC) and the trigger levels would show it (the sidebar says why there is no lock).
- Only Mario's Super Charge with Lakilester, at the route's camera. Goombario's Charge and other fights are not built.
- `HUD_HIDE.hw_spiny = 2` is from the A icon on the clips (bar hides 0-2 capture frames after the A); the tracker
  carries -2..+1 around it. The Time Out confirm in the table is the bar hiding - 3 frames (as Mario's actions), so the
  "predicted at the real confirm" column is read at that frame (+-1 shown).
- Bowser's attack is not read from the video (the coin on the turn-2 menu does the pruning).
- The q check against the turn-1 menu (unexercised, see above).
- The input display is not read: the press correction is not auto-calibrated.
- WebGPU is not used: the browser here has none; the WebAssembly search alone fits in the time available.

## Missing pictures (the aura finding, fb_aura/README.md section 8)
Some logic frames never get their own picture in the capture, and x264 sometimes re-encodes a duplicate so it looks
new. What that means here:
- **The rays window.** Frames are not counted: each new picture is placed on the burst's brightness curve (dynamic
  programming over n, steps of 0-3 frames), so a missing picture shows as a jump on the curve and a re-encoded
  duplicate as a step of 0. On the 7 source clips the curve, indexed by distinct pictures from the trigger, has sd < 0.7
  levels at every one of frames 3-45, so none of the 7 has a missing logic frame inside the rays (a skipped one would
  shift every later index by a whole step, 2-9 levels). That includes 15-17-02 and 15-18-30.
- **After the rays** the tracker's clock is time (the capture's frame times), not a picture count, so a logic frame with
  no picture costs nothing. What it cannot see is a lag frame (time passes, the game does not step); those are carried
  as 0/1 frame hypotheses after the rays and as the Spiny Flip confirm shifts.
- So a hidden missing picture does not explain the coin mismatches of 15-17-02 (a flash 24 frames before the Charge)
  and 15-18-30 (q before vs after the Charge): the offline check (readouts/charge_qback.py) also clocked by time. Not
  resolved; both are before the Charge, which the live page does not need.
