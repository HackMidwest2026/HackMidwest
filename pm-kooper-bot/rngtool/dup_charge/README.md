# Duplighosts: Charge-ray lock -> Bombette's Do Nothing -> 3+/4 copies (JP, emulator)

Runner's route: T1 Mario Super Charge, Bombette Do Nothing; T2 Bombette Power Bomb, then Mario Jump (2 hits) on the
Duplighost that did not transform. Each Duplighost rolls `RandInt(1000) < 600` to copy Bombette.
**V** = emulator-verified here, **C** = code-read, **S** = simulation of the verified model.

Emulator: JP ROM, `/tmp/claude-0/pm/bot1`, debug core. State `states/boss_2402_dchg_menu.st` (DIAGNOSTIC SETUP:
`AC=1 PARTNER=3 BRANK=1 BADGES=10c,e4,112,11f BOOTS=2 FP=10 NOFS=1 SUF=_dchg boss_battle_start_setup.py 2402`). That is
the Jr. Troopa route state's setup: Bombette Super, Super Jump Charge, Power Bounce, Close Call, Speedy Spin, Ultra
Boots, 10 HP / 10 FP. DIAGNOSTIC RAM write in every run: gRandSeed (both copies) set at the state load. Nothing else.

## Bottom line
| | blind | locked, 1 s window, +-1 press (25/50/25) | locked, exact press, 1 s |
|---|---|---|---|
| aim at 3+ (`safe3`) | 3+ **47.2%**, 4 12.9% | 3+ **99.7%**, 4 57.8% | 3+ 100% (median wait 1 frame) |
| aim at all 4 (`all4`) | 4 **12.9%** | 4 **67.6%**, 3+ 92.4% | 4 99.97% |
| 0.5 s window (15 frames) | | safe3: 3+ 90.9%, 4 36.0%; all4: 4 50.5% | 4 87.4% |
| 2 s window (120 frames) | | safe3: 3+ 99.995%, 4 70.5%; all4: 4 75.3% | 4 100% |

(`dc_odds.py 20000 15 30 60 120`, `odds.json`.) **3 copies and 4 copies both end the fight on T2** (V, below), so the
target to beep is `safe3`: 99.7% with +-1 presses against 47% blind. **GO**, if the Charge reader locks in this arena on
console (emulator: 4 of 4).

## 1. Turn order and levers (V)
- T1: Mario acts first (no Z). Charge confirm C0; rays at C0+13 / +16 (two energy_in_out(6)), until +58 / +61.
- Charge popup A ("+3") on C0+77..+136 opens Bombette's menu 16 frames later (no A: +153); same as Jr. Troopa.
  **It draws nothing** (V: 40 runs with random popup policy, every frame matched by a model that is not told the popup frame).
- Bombette's wheel / Strategies / list: no draws.
- **The only lever is Bombette's Do Nothing confirm C** (the last input before the enemy turn). The Charge confirm is
  the lock source, not a lever. Mario first is the only order that works: with Z (Bombette first, Mario's Charge last)
  the Charge confirm would be the lever and the rays would be read too late to plan it.

## 2. Every draw from the rays to the copy rolls (V)
Per frame: script draws, energy_in_out creation (rand(360) + 10 x [rand(10), rand(10)]), the status-bar coin
(rand(100), 24 frames, 48 after >= 70), energy_in_out updates (a part redraws rand(359) when its counter wraps), the
per-frame rand_int(1). From C: copy roll at C+13; a copy -> next roll +97; a failed copy (flying tackle, 4 damage)
-> fx_firework 8 x rand(359) at +34 and next roll +78. Same as the old `dup3` profile. Nothing else: no nuisance draws
in the rays (stage kpa_01's torches draw nothing), the popup or the menus.
**The count is fixed given the seed at C0, the first coin frame q (both from the rays) and the frames C0 and C.**
Close Call (rand(100) at 0x80277518) only when a tackle hits Mario under 6 HP: from 10 HP only on a 3rd failed copy
(1 copy or fewer), so it never touches 3+. If the runner arrives under 10 HP that changes (see the Surge README).
`dc_check.py` over 60 runs (`dc_turns.py`, random seeds, random delays 2-40 frames before both confirms, random popup
policy none / +77..+136): **60/60 match every frame from the Charge confirm to the 4th roll +40** (or the 3rd failed
copy) and every roll value. That is about 31,000 frames. 40 of the runs were blind and 20 planned. **Planned**: Do
Nothing put on the model's first all-4 frame, computed only from gRandSeed and q at the Charge confirm (what the lock
knows) plus the Charge confirm frame. **20/20 gave 4 copies.**

## 3. Odds (S): table above
Per frame 12.9% all-4 and 47.5% 3+. Each frame is close to an independent draw, so blind = per-frame. All-4 frames
come in runs: 87% singles, 11% pairs, 1.4% triples. That is why +-1 presses cap all-4 at ~68% in 1 s, while 3+ runs
are long. **Added wait:** the chosen frame's mean offset into the window is ~25 frames (0.4 s) for 1 s (exact 3+:
1.2 frames). The main cost is waiting for the lock. The rays end at C0+61. The natural Do Nothing confirm is about
C0+120..+150 (popup A early, then about 30 frames of menu). The window opens at lock + 0.5 s beep lead. With a lock
1.6-2.6 s after the rays (FB2 page, 3 workers) that is +1-2 s. With 4-6 s (the Jr. estimate) it is +4-6 s. Plus 0.4 s.
The runner sits on Do Nothing with the hand ready.
**vs the Surge plan** (`../duplighost_surge`): the per-frame odds are the same (the same rolls, 13% / 47%). The
difference is the lock. Surge needs a spiny detector that does not exist yet, and its coin phase is ambiguous (a
1-frame phase error keeps an all-4 frame only 28% of the time). The Charge rays give seed + q directly. The reader is
proven on console (Hallway 14/14) and works here in the emulator (section 5). Surge planned exact frames (all-4
within 1 s 98.4%); with +-1 presses its numbers would match the ones here.

## 4. The rest of the route (V, `T2=1` in the 60 runs)
- **4 copies (23 runs): T2 Bombette Power Bomb (Z, Abilities, down 2) kills all four, fight over.** A blast kills a
  copied Bombette outright (its owner Duplighost dies with it). Even a single Bomb killed a 15-HP copy.
- **3 copies (11 runs): Power Bomb kills the 3 copies.** The untransformed one takes 6 (100% mash) and is left at 9.
  Mario's Jump with the Super Charge does 3+3 = 6 per hit, two hits = 12, so **the fight ends on T2 (11/11)**. This needs
  the Jump action command (window = jump start +16..+19; Mario runs up first, then a fixed 18-frame arc). One hit leaves
  3 HP. C: with Super Boots 2 x 5 = 10 still kills; with Normal Boots 2 x 4 = 8 does not. Any Power Bomb at 3+
  damage (mash > 35%) still leaves <= 12.
- 2 copies (16 runs): Power Bomb + Jump kills one Duplighost. The other one is at 9 HP, copies Bombette again on T2's
  enemy turn (it is ReadyToCopy again, C: `EVS_TakeTurn`) and the fight goes on. Mario has 0 FP left (Charge 4 + Power
  Bomb 6), so there is no second Power Bomb.
- Does the lock carry to anything useful? Not on the 3+ path: the fight ends on T2 and Power Bomb / Jump have no
  rolls. On the 2-copy path the carry would reach T2's copy roll and Close Call (Mario at 2 HP), but the route is lost
  anyway. Not modelled.

## 5. Reader data (`../readouts/data/`, `dc_reader_data.py`)
- `charge_cams_mario_dup.json`: **bit-identical to `charge_cams_mario_route.json` and `_jr.json`** (same battle camera,
  Mario home (-85, 18, 0)), both seeds. Centre raster (260.4, 304.9).
- `charge_mario_ref_dup.json`: Mario at frame -1, an **emulator render** (the format of `charge_mario_ref_jr.json`). The
  Hallway capture patch (`charge_live/mario_ref.json`) scores NCC 0.90 here (dx 0, dy -3), the same as on the
  Hallway render (0.92), so the page's current patch should work.
- `charge_dup_reader.json`: nuisance draws during the rays **none**; per-frame order; HUD hide 3 frames after the
  confirm; creation at +13 (both runs). **Burst curve: within 0.7 levels of the Hallway render on frames 0-33, then 1.6-2.8 darker
  (frames 34-45, after the camera swings back and this room's background shows)**. A suggested `CHG_BRIGHT` for this arena is included (page curve +
  emulator difference, unverified). It differs from the page's by <= 2.8 levels.
- End to end (`../jr_charge/jc_e2e.py` with `CAMS=charge_cams_mario_dup.json MARIO=.../charge_mario_ref_dup.json`,
  blur 1.3 + noise 4, the page's maps and kernel natively): **4/4 locked the true seed with the right q**. Scores
  4160-7045, 2.9-4.3x the runner-up. The runs were: 2 seeds; Mario shifted 16 px; the Hallway capture patch.

## 6. Recordings that would validate it on console
Same capture chain as the Hallway clips (S-Video -> GV-USB2 -> OBS 1280x720 60 fps, same crop, input display on).
4-6 attempts of the Duplighost fight from the T1 menu to the end of T2 (or the reset):
- the Charge's 1.6 s of rays -> lock offline (`charge_live/tools/gameframes.py` + `jc_jsmaps.js` with the env above);
- the input display gives the Charge confirm, the popup A and the Do Nothing confirm. The seen copies (0-4, in order,
  plus which Duplighost tackled) must equal `dc_model` from the lock and those two confirm frames. 4 rolls give ~3-6
  bits of check per attempt; also the coin shines in Bombette's menu;
- at least one attempt with the T2 Power Bomb + Jump (3 copies) to confirm the 2-hit kill on the runner's boots;
- the burst brightness in this room, to replace the suggested `CHG_BRIGHT` and take a capture Mario patch.

## Files
| file | what |
|---|---|
| `dc_model.py` | per-frame model (jc_model's rays/coin + the Duplighost branching); `table()` = copies per confirm frame |
| `dc_turns.py` | emulator driver: T1 (random or planned Do Nothing), optional T2 (Power Bomb, Jump with the AC) |
| `dc_check.py` | model vs logs, every frame from the Charge confirm |
| `dc_odds.py`, `odds.json` | blind vs locked odds, windows 0.25-2 s, run lengths, waits |
| `dc_reader_data.py` | writes the three `readouts/data/charge_*dup*` files from `jc_probe.py` screenshot runs |
| `dc_fixture.py`, `plan_cases.json` | model cases (seed and q at the rays' frame 0, copies per Do Nothing frame) for the page test `../test_dup_plan.js` |
| `dc_e2e_press.py` | plays a page plan's Do Nothing frame (and +-1) in the emulator after the rendered Charge (`../test_dup_page.js`) |

On the page (v71, `../charge_live/README.md`): the route option *Charge lock*. Note on the table above: the "1 s" column
is `dc_odds.py`'s 60-frame window (2 s at 30 game frames/s); 30 frames (the page's default 1 s max extra wait) is
safe3 3+ 97.3%, 4 44.6% (`odds.json` windows.30).

Logs and screenshots were in /dev/shm (not committed).
