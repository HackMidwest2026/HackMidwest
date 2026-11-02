# Duplighosts: Spiny Surge readout -> Change Member confirm -> 4 transforms (JP)

The turn as the runner plays it: Z (partner first), Lakilester Spiny Surge (100%), then Mario: Strategies > Change Member >
Bombette (that A is "the confirm", frame C), then the enemy turn. Each Duplighost rolls `RandInt(1000) < 600` to copy.
Question: if the seed is read from the Surge, can the confirm frame be planned to get all 4 (or 3+) copies?

Emulator: JP ROM, `/tmp/claude-0/pm/bot1` (harness, debug core with every `rand_int` logged with its caller).
State `states/boss_2402_laki_menu.st` (DIAGNOSTIC SETUP, same as the Bombette Duplighost state but Lakilester Super out):
`AC=1 PARTNER=8 BRANK=1 BADGES=121,112,11f NOFS=1 SUF=_laki boss_battle_start_setup.py 2402`.
DIAGNOSTIC RAM write in every test: gRandSeed (both words) set once at Mario's turn-1 menu.

## Scripts
| file | what |
|---|---|
| `dsurge.py` | emulator driver: Z, Surge (mash pattern), Mario's menu, the 6 Change Member inputs at chosen frames, enemy turn; logs every draw and replays the seed (checked against gRandSeed) |
| `surge_model.py` | the draw model from the first throw to the 4th copy roll |
| `trace_turn.py` | Q1: plays cases in the emulator and compares every draw (frame, range, value) with the model |
| `window_stats.py` | Q2: per-confirm-frame outcomes over random seeds (fast event-driven model, checked against `surge_model`) |
| `phase_ambiguity.py` | how much a wrong coin phase costs |
| `surge_search.c` | Q4: seed search from throw rest points with early rejection, self-test with timing |
| `clip_spinies.py`, `clip_fit.py`, `clip_marks.py` | real clip: red spiny blobs, fit of one spiny's flight, input-display/ring timing marks |
| `emu_marks.py` | emulator side of the timing marks (glide64 screenshots) |
| `plan_e2e.py` | planned confirms in the emulator (all-4 / exactly-3 frames from the model) |
| `data/trace_48.json`, `data/plan_e2e.log`, `data/window_stats.txt` | results |

Run the emulator scripts from `/tmp/claude-0/pm/bot1` with `M64P_DBG=1 PYTHONPATH=.` (see each docstring).

## Q1: the draws from the Surge to the copy rolls (emulator, verified)
Per game frame: script/effect-creation draws, then the status-bar coin if due, then one `rand_int(1)` (0x800269AC, the
"per-frame step" of the other models). Frame 0 = first throw, L = last throw, C = confirm:
- each throw: `rand_int(140)`, `(80)`, `(360)`, `(10)` (rest x-10, rest y-10, yaw, spin speed - 5);
- the hit: one `fx_firework` per Duplighost at L+26, L+32, L+38, L+44: 8 x `rand_int(359)` at damage 3 (100% mash), 6 at
  damage 1-2 (intensity from `show_damage_fx`);
- Mario's menu (gBattleState 13) at L+103. Menus (wheel, Strategies, Change Member list): no draws at all;
- copy rolls: first at C+56; a copy -> next roll +97; a failed copy (flying tackle) -> its firework (8 x 359) at +34 and
  the next roll at +78 (the same branching as the `dup3` profile, only the first roll moves from +13 to +56);
- the coin: `rand_int(100)` every 24 frames, 48 after a shine (70+), all the way through (also hidden during the Surge).

So **the count is fixed given: the seed before the first throw, the coin phase, the throw frames, the damage class and C.**
Navigation timing before the confirm does not matter (only C does); the spiny count only adds 4 draws per throw.
`trace_turn.py 48`: 48 cases, random seeds, 6 full-mash patterns (7 to 28 spinies, damage 2 and 3), random menu-input
gaps and confirm frames (38-115 frames after Mario's menu), plus 2 weak-mash patterns:
- full mash, 36 cases: Mario's menu at L+103 in all 36; every draw matched the model up to the 4th roll in 32; the 4
  others had 2+ failed copies and then Close Call draws (below). All 14 full-mash cases with 3+ copies matched.
- the replayed seed equalled gRandSeed in all 48 (no draw missed by the log).
- `plan_e2e.py`: model planned the first all-4 confirm 35+ frames after Mario's menu from the readout's inputs (seed before
  the first throw, coin phase, throw frames, damage): **8/8 gave 4 copies** (median 2 frames past ready); planned
  exactly-3 frames: 6/6 gave 3 (`data/plan_e2e.log`).
Not covered by the model (and why it does not matter for 3+/4):
- Close Call (`rand_int(100)` at 0x80277518) when a tackle hits Mario under 6 HP: from 10 HP only the 3rd tackle, i.e.
  only after 2 failed copies. If the runner arrives with <= 5 HP + Close Call equipped, the 1-fail (3-copy) path gets an
  extra draw: the 4-copy frames are unaffected, the 3-copy model would need it added.
- A weak/early-stopped mash: when the last throw is more than ~13 frames before the end of the 60-frame mash window the
  rest of the move is timed from the window, not the last throw (seen: menu at L+116/L+122). At 100% with mashing to the
  end (every case above) it is always L+103. The page can instead time from Mario's menu appearing (L+103 by definition).

## Q2: confirm frame -> outcome (model, 20000 seeds; `window_stats.py 20000 30 60`)
Confirm frames from "ready" (30 frames after Mario's menu; the real clip's runner confirmed ~36 game frames after it)
over the next 60 frames:
- per frame: all 4 = 12.9%, 3+ = 47.5%. All-4 frames are single frames 87% of the time, runs of 2 11%, 3 1.4%.
- wait for the first all-4 frame: mean 6.7 frames, median 4, p90 16, p99 33. **None within 15 frames (0.5 s): 12.5%;
  within 30 (1 s): 1.6%;** within 60: 0.03%.
- first 3+ frame: mean 1.2, median 1, p99 7 frames. None within 0.5 s: 0.03%.
- the page's safer target (`aim4`: an all-4 frame with both neighbours 3+): 3.0% of frames; mean wait 40 frames, median 26;
  none within 0.5 s 67%, within 1 s 46%, within 2 s 22%.
These rates match blind (13% / 47%) because each frame is a fresh draw; planning only picks the frame.
Earlier inputs: none of the menu inputs draw, so only the confirm frame and the time since the throws matter.

## Q3: hidden / unmodelled parts, what the rolls depend on
- In the battle everything is accounted for (48/48 cases: replay seed equals gRandSeed; only spiny, firework, coin,
  per-frame and roll draws before the 4th roll, plus Close Call on 2+ fails; the game-over path after that has more).
- **The coin phase is the hidden part.** The readout gives the seed; the coin's next-draw frame is a second unknown.
  The search finds it only up to the gap between two observed throws (a coin draw anywhere in that gap gives the same
  spiny values). An error of even 1 frame is not harmless: an all-4 frame stays all-4 only ~28% of the time and 3+ ~63%
  (`phase_ambiguity.py`). Resolve it with shines: the coin is visible in the T1 menus before Z and in Mario's menu after
  the Surge; with the seed known, each phase hypothesis predicts the shine frames (not yet tested on video).
- The copy decision (`EVS_TakeTurn`) depends only on: the Duplighost's state var (ReadyToCopy at the start), the battle
  flag "has copied" and the last copied partner (all copy Bombette on turn 1, so no effect), and the roll. Not on HP.
  Surge cannot kill (15 HP, damage 3). A dead or missing Duplighost would skip its turn and shift every later roll.
  The partner in the party list order does not matter (no draws).
- Lakilester's rank must be Super (damage table and firework size); at Ultra 100% gives damage 4 = same 8-draw firework.

## Q4: practicality
**Real clip** (`aad978a3-...mkv`, Duplighosts, 100%, 4 transforms; copied to /dev/shm, not committed):
- One isolated spiny (the first) tracked 17 game frames: flight fits the code (x roughly linear, y a parabola of fixed
  curvature; curvature gives ~3.3 capture px per world unit). Rest point from the first 17 frames: x +-0.7, y +-0.2
  units (1 sd) -> **~10-11 bits from (x, y)** at +-2 sd, ~8.8 bits from only 8 frames. Spin speed not measured.
- Problems: throws are 3-4 game frames apart and all start at the same point, so after the first one the launch blobs
  merge; the "100%" popup covers the launch area for ~18 game frames (a third of the window) and is itself red. Only a
  handful of throws are cleanly separable without a real tracker, so plan on ~3-5 good spinies (~30-50 bits) per Surge,
  not 10+. Enough for a lock with the interval search below, but the detector is not written.
- Timing on the console: input-display A presses at capture 575, 586, 616 (Strategies, Change Member, Bombette); first
  transform ring at 770: 77 game frames after the displayed confirm. Emulator: first roll at C+56, ring at C+74 (`emu_marks.py`, glide64). The ~3 frame
  difference is input-display/capture latency, so it is a fixed calibration (the page's press check already measures
  the confirm from the video). Runner: confirm ~36 game frames after Mario's menu appeared.
**Search speed** (`surge_search.c`, native, one thread): enumerate only the advanced seeds whose first x draw falls in
the observed interval (a contiguous range: tolerance/141 of 2^32), test y on the next draw, then follow later throws with
both coin branches. 0.23 s (x+-2, y+-1, every throw), 0.45 s (10 throws 6 apart, +-3/+-2), 0.7 s (every 2nd throw
observed), 1.7 s (x+-4, y+-3, every 3rd). The true seed was always found and unique; extra matches were the same seed with
the coin draw in a different unobserved gap (the phase ambiguity above). Browser JS is ~3-5x slower single-threaded, so a
few seconds, or ~1 s with workers. The T1-menu coin shines can narrow the start further but are not needed.
**Time budget**: the first spiny's track is readable ~17 frames after its launch; the whole Surge ends at L+~30; Mario's
menu is at L+103 and the runner needs ~35 more frames to have the hand on Bombette. That is ~3.5-4 s from the end of
the throws to the earliest confirm, enough for a 1-2 s search, and the plan only needs a target a few frames later
(median wait 4 frames for an all-4 frame).

## Verdict
Mechanically yes (emulator-verified model, fixed schedule, menus draw nothing). Practically it needs: a spiny-launch
detector that copes with merged blobs and the 100% popup (not written), the coin phase resolved from shines (not tested on
video), and a confirm on an exact frame (all-4 frames are 87% single frames; the safe `aim4` target needs a median 26-frame
wait). Go for 3+ (almost any planned frame, median 1 frame), conditional-go for 4 once the detector and the phase
resolution are tested on more real clips.
