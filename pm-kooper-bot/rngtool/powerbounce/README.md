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
