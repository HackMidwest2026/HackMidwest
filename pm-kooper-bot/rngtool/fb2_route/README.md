# Final Bowser phase 2 route: can it be RNG-manipulated end to end? (JP, emulator)

Route (runner): T1 Super Charge + Lakilester Cloud Nine; T2 Charge; T3 Jammin' Jelly; T4 Charge; T5 Peach Beam;
T6 Charge, then Close Call; T7 Power Bounce x7. Lakilester does nothing on T2-T7 (Strategies -> なにもしない).
Save in the route states: Ultra Boots, badges S.Jump Charge (スーパーチャージ, 4 FP, +3), Power Bounce (れんぞくジャンプ, 3 FP),
Power Rush, Close Call; Lakilester Super rank; items Jammin' Jelly, Life Shroom; Mario 10 max HP / 15 FP.

## Bottom line
- **T6 -> T7: GO (emulator-verified model).** The lever after the T6 Charge-ray lock is **not** a partner input:
  Lakilester is KO'd from the T4 wave until T7. It is **the A that closes the "+3" popup after the Charge**, on any frame
  K = confirm+77 .. +136 (no press: it closes by itself, same as K = 137). Bowser's AI runs on K+40, the Close Call roll
  on K+40+55 (Fire Breath) / +62 (Claw Swipe). Between the end of the rays (+60) and the roll there are only lightning,
  coin, step and Bowser's 2-3 AI draws, so the whole stretch to the T7 Power Bounce rolls is a closed model
  (`t6model.py`): **229/229 runs exact** on Bowser's attack and the Close Call value (8 seeds, 3 route builds, K over
  the whole window, all three attacks) and **48/48 Power Bounce roll sequences exact** after a Lucky.
- **Joint odds** (Close Call AND bounces; `t6pay.c`, 4000 random locked states; K window 1 s from +100, d window 1 s
  from the earliest target-screen A; press 50% on frame / 25% one early / 25% one late; the page re-plans d after
  seeing the actual K):

  | | P(Close Call) | P(CC and 6+) | P(CC and 7+) | P(CC and 8+) |
  |---|---|---|---|---|
  | blind (no popup press, earliest target A) | 29.8% | 2.4% | 0.35% | 0% |
  | locked, +-1 frame presses | 83% | 47% | 22% | 3.6% |
  | locked, exact presses | 100% | 99.8% | 67% | 11% |
  | locked, +-1, K window 2 s (77..136) | 91% | 53% | 29% | 5.1% |
  | locked, +-1, d window 2 s | 83% | 51% | 29% | 5.1% |

  Added wait against the fastest play (popup A on +77, earliest target A): about 45-50 frames (1.5-1.7 s) for a plan;
  not pressing the popup at all already costs 60 frames.
- **T1-T4: GO in the emulator, page model missing.** Each turn has two levers after a lock: Mario's confirm (and the
  popup A on Charge turns) and Lakilester's confirm (Cloud Nine on T1, Do Nothing on T2-T4). The outcome per lever
  frame is a fresh ~50% Cloud Nine dodge (T4: ~39%, the wave must be chosen and dodged). With a lock, a 1 s window
  gives ~98% per turn with +-1 presses (exact: ~100%), 87% over T1-T4; blind it is ~5%. The aura is up through all
  four turns, so each menu can re-lock. What is missing is a page model of each turn's draws (Charge popup timing,
  Cloud Nine's puffs, the message blips, Bowser's attack timings), the same work as `t6model.py` but with the aura.
- **T5 (Peach Beam turn): NO-GO for now.** Lakilester is KO'd, Cloud Nine has ended, so Bowser's T5 attack is a Close
  Call roll (30% per lever frame in the emulator, 27% measured). The levers (Peach Beam confirm, the remark text A
  presses) come before or inside the beam's ~5000 unmodelled steps (misc_particles, shimmer_burst; `../fb_aura`
  section 4). Blind 30%.

Verified vs code-read is marked per section. Every number above is emulator or simulation; nothing here was checked
on console footage.

## Files
| file | what |
|---|---|
| `route.py` | route player: menu sequences with the confirm delay as a parameter, draw logging by caller, Bowser/partner state |
| `route_build.py` | plays T1-T7, choosing each turn's lever frame so Bowser misses; saves `tN_menu.st`; per-frame miss strings |
| `fb2_state.py` | dumps a state's HP/FP/badges/items/charges/Cloud Nine |
| `nav.py` | input list + glide64 screenshots (menu exploration) |
| `t14_study.py` | T1-T5 draws per phase, by caller, per seed |
| `t6_study.py` | T6 -> T7 runs (Close Call, rolls) against `fb2model`; popup-press policies |
| `t6_collect.py` | per-frame draw logs for T6/T7 runs (seeds x K x d) |
| `t6model.py` | the T6 -> T7 model (from a seed after the rays to the Power Bounce rolls) |
| `t6_check.py` | model vs the collected logs |
| `t6pay.c` | joint payoff of K and d after a lock |
| `item_names.json` | item ids (decomp `src/item_table.yaml`) |
| `t1menu_state.py` | v87: the phase-2 T1 menu state route_build.py starts from (`../make_states.sh` runs it) |
| `chain_log.py` | v87: one continuous T1 -> T4 debug-core log (every lever on the first frame that makes Bowser miss; GUARD=1 an A in Bowser's turn) |
| `chain_fixture.py` | v87: `../fixtures/fb14_chain_logs.json` from chain logs (`../test_fb14_chain.js`) |

Emulator scripts run from `/tmp/claude-0/pm/bot1` (debug core `M64P_DBG=1` when draws are logged). DIAGNOSTIC RAM
writes (setup only, labelled in the code): Mario HP 5 at phase-2 start (the route enters at Danger), Bowser HP 80
(the real value is whatever phase 1 left; 80 makes 7 bounces from a 15-damage first hit the kill), gRandSeed at a menu.
Built from `boss_2304_peach_start.st` (phase 2 with the Peach Beam unlocked) -> `/dev/shm/fb2r/t1menu.st`.

## 1. Turn structure (emulator, 3 full route builds)
- Mario acts first, then Lakilester, every turn. "Do nothing" is a confirmed menu choice: partner wheel up to
  さくせん (Strategies), A, down to なにもしない, A. That last A is the confirm and a lever.
- Menus remember the wheel slot (after the Jelly the wheel is on Items) but the Jump submenu opens at the top.
- **Cloud Nine** (three-chances command): quality = turns, up to **4** with the presses at confirm+132/152/172
  (the decomp's `ApplyCloudNine` sets turnsLeft = quality). Cast on T1 with 4: up for Bowser's T1-T4 attacks, ends at the
  start of T5. So "Bowser misses the first 4 turns through Cloud Nine" holds; T5 has no Cloud Nine.
- **T4 wave** = Draining Shockwave (TurnCount 4 > 3, a jump charge is up: `RandInt(100) < 75` -> wave, else
  `RandInt(110) < 20` -> wave; ~79.5%). It tests Mario (Cloud Nine 50%) and then **Lakilester, who has no dodge**: he is
  KO'd for 3 turns (koDuration 3 at the T5 menu, 2 at T6, 1 at T7). If the wave hits Mario it drains the charges.
  If Bowser picks a normal attack on T4 instead, TurnsSinceShockwave keeps growing and the wave comes on T5/T6 with no
  Cloud Nine, so the T4 wave is the outcome to aim for. After it, T5 and T6 are `EVS_UseAttack` (Body Slam / Claw /
  Fire Breath), and Bowser does not recover or speak (Mario 50% HP vs Bowser 80%: `GetPlayerHpPercent - HP% > 25`
  is false; the <50% speech never fires).
- **So on T5, T6 and T7 there is no partner turn**: the only inputs are Mario's.
- FP: T1 Charge 4 + Cloud Nine 4 (15 -> 7), T2 Charge (3), T3 Jelly (15), T4 Charge (11), T6 Charge (7), T7 Power
  Bounce (4).
- First Power Bounce hit on T7: **15** (12 charge, Power Rush at Danger), then 14, 13, ... (11 stars while >= 9).

Per-frame outcome of the lever (route_build, 31 delays per turn, 3 builds): T1 45-58% miss, T2 35-65%, T3 48-58%,
T4 45-65% (any miss), T5 23-29% (Close Call only), T6 19-42%. The miss strings look like independent coin flips per
frame (e.g. T1 `0011110100010010101101101110111`).

## 2. T6 -> T7 (verified in the emulator)
Inputs between the T6 Charge-ray lock and the Close Call roll: **only the popup A (K)**. Inputs between the roll and
the bounce rolls: the T7 menu navigation (draw-free) and the target-screen A (d). Lakilester is KO'd. A presses during
Bowser's turn do nothing (no text there in the Lucky branch).

Every gRandSeed draw, frame 0 = the T6 Charge confirm (`t6_collect.py`, `t6_check.py`):
| frames | draws |
|---|---|
| 13-60 | the Charge rays (`readouts/charge_model.py`), coin, lightning, step |
| 61 .. K+39 | lightning (130/220 loops), coin (24/48 rule), step |
| K+40 | Bowser's AI: RandInt(100) (Star Rod re-cast: 2 turns after the beam, chance 0, still drawn), RandInt(80) (< 20 and Body Slam allowed -> Body Slam), else RandInt(60) (< 20 and Claw allowed -> Claw), else Fire Breath |
| K+40+55 (Fire) / +62 (Claw) | the target test: Close Call `rand_int(100) < 30` (`1A5830.c:192`; caller 0x80277518) |
| then | lightning, coin, step only; T7 menu on test+134 (Fire) / +83 (Claw) |
| d+45+27k, d+71+27k | the Power Bounce stars and rolls (`../powerbounce/fb2model.py`) |
Same-frame order: lightning, script draws, coin, step. K = 77 is the first frame the A closes the popup; without a press
it closes like K = 137. **The count is fixed given the seed, K, the Body Slam/Claw flags (from the attacks the runner
saw on T4/T5) and the lightning phases.**

**Checks** (`t6_check.py` on `t6_collect.py` logs; the model starts from the logged seed at frame 61 with the logged
lightning frames and coin phase, nothing else):
- build b1 (Claw allowed, Body Slam not), seeds 1234abcd 9e3779b9 00000001 deadbeef 5eed0fb2 a5a5f00d 0badc0de 13579bdf,
  K = 74..136: attack + Close Call value + test frame + T7 menu frame **169/169**;
- build b2 (Body Slam allowed, Claw not): **30/30**; build b3 (Claw allowed): **30/30**;
- Power Bounce after a Lucky (8 seeds x 3 K x 2 target frames): **48/48** roll sequences identical (bounces seen 3-7).
- Measured timings: Body Slam test at AI+52, T7 menu +101 later; Claw +62 / +83; Fire Breath +55 / +134.
- `t6_study.py` with seed 1234abcd: A every 25 frames vs no input during the Charge changes Bowser's AI frame from +177
  to +140: that was the popup press, which led to finding the K lever.
- The bounce move is **Power Bounce** (れんぞくジャンプ, 3 FP). On T7 the first hit is 15, not the 13 of
  `fb2_t7like_pb`, so `fb2model` needs dmg0 = 15 (11 stars per hit down to 9 damage: through bounce 7).

**Lock -> levers.** The rays lock gives the seed at frame 61 (and the coin phase). The T6 Charge confirm itself is
before the lock, so it is a lever only with an earlier lock (a coin lock in the T6 menu). K and d come after it.
Joint odds: see the table at the top (`./t6pay TRIALS KLO KW DW SLAM_OK CLAW_OK [EXACT]`, flags make no real
difference: 22-23% for Close Call and 7+ with +-1 presses, 20% with Fire Breath only).

## 3. T1-T4 (emulator; levers verified; the page model: section 7)
`t14_study.py` (b1, seeds 1234abcd 9e3779b9 00000001, no input outside the confirms):
- **Mario's action to the partner menu is 154 frames for a Charge (popup left alone) and for the Jelly**, for every seed.
  Draws: Charge = 2 x (1 x 360 + 20 x 10) ray inits + ray respawns, Jelly = 10 x (359, 10, 10) of its sparkle effect
  (caller 0xE0044170); both fixed counts. The rest is aura (16 per 20 frames), coin, lightning, step. LCG steps
  differ by seed only through the coin's 24/48 rule (396-404 for the Charge, 319-321 for the Jelly).
- **Partner confirm -> Bowser's AI: the AI draws on confirm+13** (RandInt(80), maybe RandInt(60); T1 has no recover or
  Star Rod draw; Bowser at 80% vs Mario 50%), the dodge roll (Cloud Nine 50%, caller 0x802774B0) on +65 (Fire) /
  +68 (Claw) / +75. Between them only aura, coin, lightning and step. So T2-T4 have the same closed form as T6, with the
  aura added (its model is exact: `../fb_aura/aura_model.py`).
- T1 adds Cloud Nine: 20 puff draws on 10 frames and Lakilester's own effect (21 draws), at fixed frames after the
  confirm; the three-chances presses decide the turns (4 needed), not the draws.
- T4: the Draining Shockwave branch (RandInt(100) < 75 with a charge up, else RandInt(110) < 20) must come up and the
  Cloud Nine roll must pass: ~39% per lever frame. Its timings were not fitted.
- Hazard: A pressed while the Cloud Nine message prints adds speech-blip draws (`rand_int(15)` x characters, caller
  0x8012978C), seen with A every 25 frames, absent with no input.

**Odds per turn** (independent ~p per lever frame, as the miss strings in section 1 show; 20000 simulated windows):
| p per frame | blind | locked, 0.5 s window, +-1 press | 1 s | 2 s | exact press, 1 s |
|---|---|---|---|---|---|
| 0.495 (T1-T3 dodge) | 49.5% | 92% | 98% | 99.8% | 100% |
| 0.39 (T4 wave + dodge) | 39% | 84% | 93% | 98% | 100% |
| 0.30 (Close Call) | 30% | 74% | 84% | 92% | 100% |
T1-T4 together: blind ~4.7%, locked with 1 s windows and +-1 presses ~87%. Each turn has two levers (Mario's confirm /
popup A, then the partner confirm), so the effective window can be longer than one lever's.

## 4. What breaks the carry
- **T5.** The Peach Beam's particle logic (~5000 steps, seed-dependent count) and Bowser's remark text (speech blips
  `rand_int(15)` per printed character, count set by how the text is advanced) are not modelled. Until they are, T5 is a
  blind 30% Close Call, and nothing carries from T1-T5 into T6: the T6 Charge rays are the next lock.
- **Body Slam / Claw allowed flags at T6**: set by Bowser's T4/T5 attacks (a Body Slam or Claw on T5 forbids it on T6).
  The runner sees them; the page needs them as inputs.
- **Lightning phases**: the 220 loop is visible (purple sky bolts), the 130 loop is not (search it: 26 values if
  p130 = p220 mod 5 holds, else 130).
- **Text input on T1**: pressing A while the Cloud Nine message prints adds speech-blip draws (seen in the emulator
  with A every 25 frames, absent with no input). The route must not press A there, or the page must see the press.
- **Mario's HP**: Close Call and Power Rush need HP <= 5; a different HP changes Bowser's recover check.
- **Bowser's HP**: Recover rolls appear if Mario's HP% exceeds Bowser's by more than 25; the <50% speech adds text.
- **The T6 Charge readout on the FB2 camera**: glide64 renders show the rays on the dark FB arena sky with the same
  close-up Charge camera (frames ~+16..+33), then the default camera with Bowser in view; the aura is gone after the
  beam. The rays search needs the lightning draws as nuisance (1-2 bolts in the 48-frame window; 220 phase known, 130
  phase searched) and FB2 background renders + a camera table (`data/charge_cams_*.json` style) and Mario's position;
  or the page's render-free mode (`../charge_live`). Not run on FB2 footage.
- **Lock latency**: the rays end at +60 and the popup window closes at +136: the search and plan must finish within
  ~1-2.5 s (the live page's WebAssembly search takes seconds; a K window starting at +100 leaves 1.3 s).

## 6. Live on the page (Nov 3): `../charge_live/README.md`, top section
The page's Final Bowser step (T7 Power Bounce, with the T6 Super Charge as its pre) reads the T6 Charge rays with the
lightning as nuisance, beeps the popup A, reads K from the popup closing, prunes with the coin through Bowser's turn and
beeps the T7 target A. Emulator renders through the capture simulation: 8/8 true locks, Close Call at the beeped frame
5/8; the lock lands 1.6-2.6 s after the rays on this 4-core machine, which is too late for the popup window (see there).
New scripts:
| file | what |
|---|---|
| `t6_render.py` | T6 Charge (+ popup A at K, Bowser's turn, optional Power Bounce) with glide64 screenshots and every draw logged |
| `t6_raycheck.py` | the Charge-ray model with the lightning against those logs (bolts first on their frame: 48/48 x 3 runs) |
| `bolt_phase.py` | the lightning phases of a log |
| `t6_cams.py`, `t6_marioref.py` | the page's FB2 camera table and Mario patch |
| `t6_capsim.py` | renders -> simulated console capture at the Charge lock's OBS layout (time-based cadence, missing pictures, x264) |
| `t6_truth.py` | a log's true seed / phases / state at +61 |
| `t6_press.py` | presses a planned popup frame (and T7 target frame) in the emulator: Close Call, bounces |

Note for the page's model: with no press the popup closes like K = 137, the first picture without it shows K + 2, and
the status bar is back on K + 5 and stays up through Bowser's turn and the T7 menu (the coin is readable there).

## 7. T1-T4 modelled and on the page (Nov 6): `../charge_live/README.md`, v74
The page model section 3 asked for is built: every draw of T1-T4 from a menu seed to the dodge test, and through the next
menu after a miss (`t14model.py`; Bowser's star aura is 16 rand_int(359) per 20 frames in a fixed 20-frame pattern, after
the coin and before the Charge rays; the wave's draws a fixed schedule). Checked frame by frame on 64 emulator logs
(`t14_log.py`): 64 / 64 exact to the test, every miss exact to the next menu. The T1 Charge locks the seed with the aura
as nuisance; Cloud Nine (T1) and Do Nothing (T2-T4) are beeped; T2 and T4's Charges lock again and check the carry; the
carried seed at the Peach Beam confirm narrows the T6 Charge's search to ~900 seeds (`t5_steps.py`: the beam's random
numbers beyond the frames, 8654-9351 in 120 runs).
**Status (end to end, v74 section 5):** the T1 lock finds the true seed, but the aura pattern it fits can be wrong where
a capture picture is misplaced, and then the carry to T2 fails (the next Charge locks afresh); the narrowed T6 lock has
not yet run end to end.
| file | what |
|---|---|
| `t14_log.py` | one turn T1-T5 logged draw by draw (and Glide64 screenshots with SHOTS) |
| `t14model.py` | the T1-T4 model, `check` against the logs |
| `t14_fixture.py` | the page model's fixture (`../fixtures/fb14_logs.json`) |
| `t5_steps.py` | Peach Beam confirm -> T6 rays frame 0: steps vs frames |
| `fb14_e2e.py` | T1 -> T6 end to end: renders, capture simulation, the page, its beeped frames pressed in the emulator |

## 5. Recordings that would validate it
1. **T6 -> T7 (the main test)**: 5+ takes of T6 (Charge, popup A, Bowser's turn) through the T7 Power Bounce, input
   display on, still camera, with 3-5 s in the T6 menu before the Charge (the lightning's purple onsets there are what
   the page most needs next). Check: Charge-ray lock; the A icon frame = K; predicted Bowser attack and Close Call vs seen;
   then the T7 target A frame and the bounce count vs `t6model`.
2. The same but pressing the popup A at different K (early / late / none), to confirm K+40 and the 77/137 limits on
   console.
3. T1-T4 with ~2-4 s of still menu each turn (aura relock) and input display: Bowser's dodge per turn vs prediction.
4. T5 Peach Beam turn through Bowser's attack, several takes, for the beam's step count (needs locks on both sides).
5. Lightning: 20 s of a still post-beam menu for the 220 phase and the coin.
