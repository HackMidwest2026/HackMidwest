# Jr. Troopa T3 death and the Life Shroom revive (emulator, JP)

Scripts (debug core, `M64P_DBG=1`; run from anywhere, they chdir to the harness dir):
- `ls_jr.py OUT N`: whole Jr. Troopa fight T1-T3 from `states/boss_0207_route_menu.st` with human delays (no page),
  every frame's battle state, RNG steps, rand_int calls (max, value, caller) and HP.
- `ls_sweep.py OUT.json N`: a state right after the T3 Bomb confirm (Mario 2 HP, Close Call), N random seeds:
  the Close Call roll, the outcome, and on a death the revive's length in frames and RNG steps. `sweep_t3_40seeds.json`.
- `ls_frames.py OUT SEED`: renders the death + revive (Glide64mk2 on Xvfb) with the coin draws.
- `ls_idle.py SEED`: after the revive, idle in T4's menu and on the Power Bounce target screen; lists draws other than
  the per-frame step and the coin.
DIAGNOSTIC: every run writes a random seed (`SEED`, `SEED2`) at its start point, to stand for an unknown run.

## Results

**The T3 death is RNG.** Jr. Troopa's T3 attack makes one `rand_int(100)` (caller 0x80277518, 177 frames after the start
point): the Close Call. 40 seeds: survived on 1..29 (13), died on 34..99 (27). So Mario survives when the roll is < 30
(30%; 101 values -> 30/101), i.e. dies 70% of the time, matching the user's number.

**The revive is a fixed length.** Death (HP 0) to T4's menu: 399 frames in all 27 deaths (Close Call roll to menu: 426;
a survived turn: 67). RNG steps from the death to the menu: 933-939 (7 values; 935 most common), the per-frame step
(1/frame) + the coin (24/48 frames) + effect bursts: 10 x rand(359) at the knockout, a 21-call burst and 7-10 x
rand(359) (Life Shroom item), two 97-step sparkle bursts, then ~35 frames of 6 or 12 sparkle draws a frame. The counts
of the last two vary by seed, which gives the 7-value spread.

**The coin is on screen and draws normally.** The battle status bar (HP/FP/star/coins) stays up through Jr. Troopa's
attack, the knockout and the whole revive (`ls_frames.py` frames), and the coin draw (0x80146d54) keeps its 24 / 48-after-shine
schedule in battle. Death to menu is 13.3 s, about 13 coin draws, about 10 bits by the usual ~1 bit/s; minus about
3 bits for the 7-way step spread.

**Battle menus and target screens are clean.** 900 frames idle in T4's menu and 600 on the Power Bounce target screen:
no draws besides the per-frame step and the coin. A battle menu is an unlimited clean window, like standing still in a
clean room.

Not measured: the battle end, Peach/cutscenes, rooms and loads between Jr. Troopa and Hallway Bowser; deaths on other
turns; whether the target screens keep the status bar up (the page's HUD-hide model says confirms hide it).
