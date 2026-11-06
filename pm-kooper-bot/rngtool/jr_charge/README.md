# Jr. Troopa: what a Charge-ray seed lock buys (emulator, JP)

Final Jr. Troopa (battle 0x0207, Bowser's Castle), the runner's ENDGAME route (`../page_template.html`):
T1 Charge; Bomb - T2 Bomb; Whacka - T3 Charge; Bomb (Life Shroom) - T4 Bomb; Maple Syrup - T5 Charge; Do Nothing
(Life Shroom) - T6 Bounce x6; Bomb if 5 - T7 Star Storm / Shooting Star.

Everything below is emulator (mupen64plus, JP ROM, debug core) or simulation of the emulator-exact model. Nothing was
checked on console footage: none of the 23 uploaded clips shows this fight (thumbnails of all of them were checked).
(v73 correction: two short uploads do show this arena: `8526dcdd` 2026-11-02 14:16:56, 5.7 s at 30 fps, a T1 Super
Charge with Bombette; `c5537165` 14:24:35, 10.6 s, a Super Charge with Goombario. See section 7.)
**V** = verified in the emulator here, **C** = code-read (decomp), **S** = simulation of the verified model.

## Bottom line (go / no-go)

| Turn | Roll | Blind | Locked, +-1 press, 1 s window | 2 s window | exact press, 1 s | Lock source | Verdict |
|---|---|---|---|---|---|---|---|
| T1 / T2 | none (Mario at 10 HP: Jr. Troopa's hits draw nothing) | - | - | - | - | - | nothing to buy; **GO as the lock source** for T3-T6 |
| T3 | Close Call (2 HP) | 30.6% | **84.1%** | 92.3% | 100% | T3 rays (or T1 carried) | **GO** |
| T4 | Close Call (2 HP, only if T3 survived) | 29.3% | **84.0%** | 92.6% | 100% | carried from T3 / T1 | **GO** (no Charge needed) |
| T5 | Close Call (2 HP) | 29.1% | **83.7%** | 92.2% | 100% | T5 rays (or carried) | **GO** |
| T6 | Power Bounce 5+ / 6+ | 67.5% / 32.2% | **99.98% / 85.1%** | 100% / 93.9% | 100% / 100% | carried from T5 (or earlier), not across a death | **GO** |

Whole fight (`jc_fight.py`, lock success per Charge PL = 0.88, the rate the page's reader reached on the Hallway
route clips, 68 of 77 live runs; unverified in this arena on console):

| | blind | locks from each Charge's own rays | T1 lock carried (T3/T5 rays as backup) |
|---|---|---|---|
| Life Shrooms used: 0 / 1 / 2 | 2.6% / 48.1% / 49.2% | 52.7% / 42.2% / 5.1% | 58.4% / 37.8% / 3.8% |
| E[Life Shrooms used] | **1.47** | **0.52** | **0.45** |
| T6 5+ / 6+ bounces | 67.6% / 32.2% | 94.1% / 75.6% | 94.4% / 75.9% |
| E[added wait] | 0 | 6.1 s | 3.8 s |
| same, 2 s windows: shrooms 0 / E / 6+ / wait | | 70.2% / 0.32 / 87.7% / 7.2 s | 78.0% / 0.23 / 88.2% / 4.9 s |

The wait counts each planned press (0.5 s beep lead + 0.35 s mean offset into the 1 s window) and, when the lock comes
from the same turn's rays, ~3 s more for the search (rays end at confirm +61, the live search takes ~4-6 s, the
earliest Bomb / Do Nothing confirm is ~+120): the runner waits on the target screen for the beep.

**Which single Charge gives the most:** the earliest one that locks. One lock carries, frame-exact, through every
later turn until someone dies (V: from the T1 Charge seed every frame matches to the T3/T4 Close Calls in 10 runs;
from the T3 seed to T6's bounce rolls in 17 runs). T1's lock costs no wait (the search finishes during T1/T2) and
covers T3, T4, T5 and T6. A Life Shroom revive breaks the carry (933-939 LCG steps, not modelled), so each later
Charge is the re-lock: T3's after nothing broke, T5's after a T3 or T4 death. Each Charge does **not** need its own
lock; it needs one only when the carry was broken (or as a cross-check of the carry).

## 1. Levers (V)

Draw-free inputs only set the earliest frame of the next input. The levers are the confirm frames whose timing moves
where a roll falls in the LCG sequence:

- **After T1's rays:** T1 Bomb confirm, T2 Bomb confirm, T2 Whacka's Bump confirm, T3 Charge confirm, T3 Bomb confirm
  (then as below). T1/T2: no rolls (Mario 10 HP -> 2 HP each time).
- **After T3's rays:** the **T3 Bomb target confirm** (Close Call at +179). If T3 is Lucky: T4 Bomb confirm and
  **T4 Maple Syrup confirm** (Close Call at +163), T5 Charge confirm, **T5 do-nothing confirm**, **T6 Power Bounce
  confirm**.
- **After T5's rays:** the **do-nothing confirm** (Close Call at +26), then the **Power Bounce confirm** (cap rolls
  +78/+105/+132/+159).
- **Charge popup A:** A closes the "+3" popup on any frame confirm+77..+136 and the partner menu opens 16 frames later
  (no A: +153), 13 K values measured on one seed, random K in 30 runs. It draws nothing, so unlike FB2 T6 (where
  Bowser's AI hangs off it) it is not a lever by itself here: it only decides how early Bombette's menu opens. The
  fastest Bomb target confirm after a Charge is ~+122 (popup A on +77, menu inputs 6 frames apart).
- Menu confirms (Abilities / Strategies / item list), Bombette's mash, the Power Bounce action-command presses: no draws
  (menus idle-clean, V here and in `../lifeshroom/`; mash and AC timing: `../README.md`).
- Jr. Troopa's attack choice: **none on this route** (C: `final_jr_troopa.c` EVS_TakeTurn: base form -> Leap with no
  RandInt; he transforms only below 65% of 60 HP = 39; the route leaves him at 44 through his T5 turn. V: no AI draws in
  any of his turns in the logs). Only if T6 lands < 5 bounces can he drop under 39 and turn Flying (then RandInt(100) <
  50 Swoop / Spike Dive from his T6 turn on).
- Close Call (C: `1A5830.c:192`): drawn only when Mario is under 6 HP; at 10 HP (after a revive) the hit draws nothing.

## 2. Every gRandSeed draw from the rays to the rolls (V)

Per frame, in this order: battle-script draws ("pre"), energy_in_out creation, the status-bar coin (rand(100), 24
frames, 48 after a roll >= 70), effect-overlay draws ("post"), energy_in_out updates, the per-frame rand_int(1).
Offsets from each confirm (the A frame):

| Confirm | Draws |
|---|---|
| Charge | +13 and +16: energy_in_out(6) creation, rand(360) + 10 x [rand(10) speed, rand(10) phase]; until +58 / +61 each part redraws rand(359) when its 10-frame counter wraps (67-76 respawns per Charge over 67 Charges) |
| Bomb (T1) | +73: 8 x rand(359) pre, rand(360) post (explosion); **+206: 10 x rand(359) (Jr. Troopa's hit on Mario, 10 HP, no roll)** |
| Bomb (T2, T4) | +73 explosion as above |
| Bomb (T3) | +73 explosion; **+179: Close Call rand(100)** (Lucky < 30; else death at +206) |
| Whacka's Bump (T2) | +118: 22 x [359, 10, 10] (sparkles); +190: 10 x rand(359) (the hit, 10 HP) |
| Maple Syrup (T4) | +118: 10 x [359, 10, 10]; **+163: Close Call** at 2 HP (death at +190); at 10 HP (after a revive) **15** x [359, 10, 10] at +118 and the hit's 10 x rand(359) at +190 |
| Do nothing (T5) | **+26: Close Call** at 2 HP (death at +53); at 10 HP +53: 10 x rand(359) (the hit) |
| Power Bounce (T6) | +52 11, +79 11, +106 10, +133 10 x rand(359) (hit effects); **cap rolls rand(100) at +78/+105/+132/+159 <= 140/98/68/47** |

No other draws anywhere in these stretches; **no nuisance draws during the rays** (only creation, coin, respawns, the
per-frame step on all 67 Charges). `jc_model.py` holds this as data (`TURNS`).

**Is the count fixed?** The list of draws and their frames is fixed by the confirm frames. Given the seed it is fully
determined; across seeds it varies only through the ray parts' start phases (67-76 respawns per Charge) and the coin's
24/48 rule. So the lock (seed at frame 0 and the first-coin frame q, which the rays give) plus the confirm frames give
every later draw exactly.

**Checks** (`jc_turns.py` logs, `jc_check.py`): 43 runs, 11 seeds, random delays (2-40 frames) on every confirm, all
popup policies (none, +77..+136); starts at T1 (10 runs), T3 (17), T5 (16). From each run's first Charge seed and the
confirm frames alone, **every frame's gRandSeed matched the game: 69 of 69 Charge-to-roll segments, 48,246 frames from the first Charges**,
including 30 deaths (where the check stops: 15 at T3, 5 at T4, 10 at T5). Closed loop (`plan` mode: each deciding
confirm put on the model's first working frame from gRandSeed read when the window opens, i.e. what a lock knows):
**56 of 56 planned outcomes landed** (17 runs: every Close Call Lucky, every T6 6+ with Jr. Troopa at 0 HP).
Maple Syrup at 10 HP (after a T3 death, no Charge before it) checked from the T4 Bomb's seed instead: 11 of 11 runs
exact to Syrup+230. Coin-on-the-same-frame cases are few (0-3 per offset; none for +53 / +118 / +190), so the
pre/post-coin order of those is by analogy with the measured ones.

## 3. Odds (S, `jc_odds.py`, 5000 random states per gate)

Random seed and coin phase at the window's first frame; w(d) = outcome if the confirm lands on frame d. Locked: the
frame f in the window maximising 0.5 w(f) + 0.25 w(f-1) + 0.25 w(f+1). Numbers in the table at the top; the
per-frame outcomes are close to independent, so a 1 s window almost always holds a frame (exact: 100%) and usually a
3-frame run (+-1: 84%). Mean offset of the chosen frame into the window: 10.5 frames (1 s), 20 (2 s); exact presses
2.4. 0.5 s windows: 74% per Close Call, 5+ 98.8% / 6+ 72.6%.

## 4. Carry and which Charge (V + S)
See the bottom line. What the page would need to carry T1 -> T6 (not done here, `../page_template.html` is being
changed elsewhere): the T1 Bomb with Jr. Troopa's hit (`bomb_t1`, the page's `jr_bomb` lacks the +206 draws), the 10-HP
hit variants (`syrup_hit`, `nothing_hit`), arming the Charge reader on the Jr. T1/T3/T5 steps (it arms only on
`hw_spiny` now), and each confirm's frame (the page reads the bar hiding 3 frames after a Charge or Mario's item, 4
after Bomb). A confirm read 1 frame off moves an event across a coin draw only rarely (a 9-draw event changes the state
only if it crosses a coin frame), so most +-1 misreads carry to the same seed; the coin in the next menu settles the
rest. Unverified: Mario's guard presses during the T1/T2 hits (the runs did not guard; on Close Call turns guarding
did not change the roll, `../README.md`).

## 5. Reader data (`../readouts/data/`)
- `charge_cams_mario_jr.json`: Mario's Super Charge camera for frames 0..47 and the centre (-85, 18, 0), the format of
  `charge_cams_mario_route.json`. **It is bit-identical to the Hallway table** (and the same at T1, T3 and T5, any
  seed): same battle camera, same Mario home position. Centre on screen: raster (260.4, 304.9).
- `charge_mario_ref_jr.json`: Mario at frame -1, the box of `charge_live/mario_ref.json` (x0 160, y0 236, 160 x 120),
  **an emulator render**, not a capture. T1 (10 HP) and T3 (2 HP) are byte-identical; T5 NCC 1.00. The Hallway
  capture patch matches the Jr. render at NCC 0.88, dx 0 (dy -3): the page's current patch should work here too.
- `charge_jr_reader.json`: centre, nuisance draws (none), per-frame order, the burst brightness curve (emulator: Jr.
  arena within 4.3 levels of the Hallway render; largest after frame 33, where the camera swings back) and a suggested
  `CHG_BRIGHT` for this arena (page curve + emulator difference, unverified), the HUD-hide delay, the turn draws.
- End to end in the emulator (`jc_e2e.py`: rendered Charge frames, blur 1.3 px + noise 4, through the page's own maps
  code `jc_jsmaps.js` (a copy of `charge_live/tools/jsmaps.js` pointed at these files) and the page's kernel natively):
  **5 of 5 locked the true seed** (T3, T5, T1, T3 with Mario 16 px off, and with the Hallway patch), scores 4365-6644,
  2.7-4.8 x the runner-up (lock rule 3000 and 1.8 x), stage 1 2.9-6.9 s single thread; q right except T1 (41 vs 43, a
  late coin: the page keeps every q within 0.5%).

## 6. Console clips that would validate it
Only the two short T1 Charge clips of section 7 (no turn after T1, no Close Call, no seed known). Needed (same chain as the Hallway clips: S-Video -> GV-USB2 -> OBS 1280x720 60 fps, same crop, input
display on): **the whole Jr. Troopa fight from the T1 menu to the end**, 4-6 attempts:
- each Charge's 1.6 s of rays (T1, T3, T5) -> lock offline with `charge_live/tools/gameframes.py` + `jc_jsmaps.js` +
  the harness; T1's and T3's seeds must agree through the carry (T3's seed = T1's carried with the confirm frames read
  from the input display), as Mario's and Goombario's Charges did on the Hallway clip;
- the input display gives every confirm frame; the seen outcomes check the carried predictions: Close Call Lucky or
  death on T3/T4/T5, the bounce count on T6, and the coin shines in every menu;
- at least one attempt with a T3 death (re-lock at T5 after the revive) and one where T3 and T4 survive (the T4 carry);
- the T3/T5 burst brightness on capture, to replace the suggested `CHG_BRIGHT` and to take a capture Mario patch.

## 7. On the page (v73) and the two console clips
The route runs on the page now (`../charge_live/jr_live.js`, `../charge_live/README.md` v73): the T1 lock carried through
every confirm (read from the status bar hiding; Do Nothing from its Strategies screen), the four levers beeped, the T3 /
T5 locks checked against the carry, Mario's HP read after each Close Call. What section 4 listed as missing is in the
page's core: `jr_bomb_t1`, `jr_syrup_hit`, `jr_nothing_hit` (`pmrng_core.js` TURNS), checked frame by frame by
`jc_check_core.js` on 24 new runs: 64 / 64 Charge segments, 68,343 frames; 110 / 110 Close Call / Power Bounce outcomes.
Console: `8526dcdd` and `c5537165` show Mario's Super Charge in this arena (the thumbnail check missed them; both are a
few seconds long). Through the page's jr profile clip 1 locks d260c382 in two runs (5568 / 3.39x, 6079 / 3.76x), clip 2
df7d78b1 (6196 / 3.69x); neither goes on with this route, so neither seed is confirmed by later rolls.

## Files
| File | What |
|---|---|
| `jc_model.py` | per-frame RNG model (rays, coin, turn draws, rolls) |
| `jc_probe.py` | frame logger: draws, seed, battle state, HP, camera, ray parts, screenshots |
| `jc_turns.py` | plays T1-T6 / T3-T6 / T5-T6 with random or planned confirms, logs every draw |
| `jc_check.py` | model vs logs, frame by frame from each Charge |
| `jc_counts.py` | draw counts per Charge and per Charge-to-roll stretch |
| `jc_odds.py`, `odds_w*.json` | per-gate odds (blind vs locked) |
| `jc_fight.py`, `fight_*.json` | whole-fight odds, Life Shrooms, T6, waits |
| `jc_reader_data.py` | writes the three `readouts/data/charge_*jr*` files |
| `jc_mario_ref.py` | Mario patch + NCC cross-check (port of chgMarioShift1) |
| `jc_e2e.py`, `jc_jsmaps.js` | emulator end-to-end lock through the page's maps code and kernel |
| `jc_check_core.js` | the page's own core (pmrng_core.js TURNS / profiles) against `jc_turns.py` logs, frame by frame (v73) |
| `jc_fixture.py`, `plan_cases.json` | model cases for `../test_jr_plan.js` (the page's tracker and plans vs this model) |
| `jc_render.py` | the route with given confirm frames, logged, optional Glide64 screenshots (the page end to end) |
| `jc_capsim.py` | `../fb2_route/t6_capsim.py`'s capture simulation, cached per game frame, as JPEG frames |
| `jc_e2e_page.py` | renders -> capture simulation -> the page (`../test_jr_page.js`) -> its planned presses in the emulator |

Run from anywhere (`jc_probe.py` / `jc_turns.py` chdir to the emulator dir `/tmp/claude-0/pm/bot1`, debug core
`M64P_DBG=1`; screenshots need Xvfb :97 with `M64P_GFX=.../mupen64plus-video-glide64mk2.so`). States: `jr_t3_menu.st`,
`jr_t5_menu.st`, `boss_0207_route_menu.st` (the jr profiles' states; DIAGNOSTIC battles from a Koopa Village map, see
`../lifeshroom/README.md`). DIAGNOSTIC RAM write: gRandSeed (both copies) at the state load, to stand for an unknown
run; NORAYS (render only) zero-length ray quads. Nothing else is written.
