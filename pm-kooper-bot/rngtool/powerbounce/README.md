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
