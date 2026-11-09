# v87 recovery notes

The v87 work (Final Bowser T1-T4 carry fix, guarding checks, the Do Nothing Jr. Troopa route) was lost uncommitted when the cloud container restarted on 2026-11-09. This is the agent's report of it, reconstructed from its transcript, kept so the work can be re-applied. Nothing below is in the code yet; base is v86 (f9a0d51).

Report from the transcript only. The container restarted and nothing was committed. I ran nothing after the restart. Repo state is v86 (f9a0d51).

## (1) Task A: why the T1→T2/T3 carry was lost, and the fixes

**The model was not the problem.**
- I traced the v86 e2e run 1234abcd on the debug core: from T1 frame 61, with the true events, `fbStep` (charge_live/fb14_live.js) gives the game's seed on every frame through T3's dodge test.
- I then made 4 continuous T1→T4 chain logs (each lever on the first frame that makes Bowser miss). The model was exact on every frame to T4's next menu: 9130 frames, 16/16 dodge tests. Later 7 logs (incl. 2 guarded): 15609 frames, 28/28 tests.
- Callers seen between the T1 lock and T2: step, aura `e00d6838`, bolt `e00bc194`, coin `80146d54`, evt `802d46e0` (Cloud Nine puffs RandInt(40)/(30) on P+200..209, Bowser AI on P+332 after Cloud Nine / P+13 after Do Nothing), testtgt `802774b0`, Charge rays `e00d6160/62c8/6624`, Jelly `e0044170/4368/4398`. Every one was already modelled.
- **Also found (not a page bug):** at MARIO_HP=10 a hit kills Mario and the Life Shroom revives him to 10. So fb14_e2e's `hp == MHP` check read hits as misses; v86's 1234abcd T2/T3 "misses" were hits (Life Shroom used).

**The page lost the game's state.** All fixes below are in charge_live/fb14_live.js unless noted.

1. **A late T2 lock skipped every carried state.** The T2 full search took 4–9 s and landed after the Do Nothing confirm. `fb14Lock`'s check did `if (T.f > m + 13) continue`, so "matched 0 of 8000". The true carry was then replaced by a fresh lock flagged as contradicting it, which died on T3's coin.
   - Fix in `fbStep`, 'chg' event: `if (!S.ca || S.ca.mk !== S.mk) S.ca = { mk: S.mk, a: fbAdv(s) >>> 0, f61: f + 48, s61: null, nc61: null };` placed before the `fbRi(s, 360)`.
   - Fix at the start of `fbStep`: `if (S.ca && S.ca.s61 == null && f === S.ca.f61) { S.ca.s61 = s >>> 0; S.ca.nc61 = S.nc; }`
   - `fbClone`: copy `ca: S.ca && Object.assign({}, S.ca)` and `wb: S.wb`.
   - `fb14Lock` loop: compute `m = (S.mk ?? M) - S.l`. If `S.f > m + 13`, accept when `ca.mk === S.mk && ca.s61 != null && ca.a === a && ends.has(String(ca.s61))`, push S itself, and continue.

2. **Ends check used the coin phase.**
   - Change `ends = new Set(H.hy.map(h => String(h.s48 >>> 0)))` (seed only, no `:nc`). Use `ends.has(String(T.s >>> 0))` in both paths.
   - Reason: the game's s61 was among the fits but with the coin 11 frames off. The first v87 build dropped the true state and planned T2 at 99.85% on a frame where Bowser hit — the only confident wrong plan I saw.

3. **Cap cut the true state.**
   - `fb14Cap` now sorts by `w*(lw||1)` instead of `w`.
   - `FB14_MAXH` 8000 → 12000.
   - Reason: the true state ranked 3000–7000 by prior and was cut after the ×5 Do Nothing shifts.

4. **T2/T4 narrowed lock on the carried stream.**
   - New `fb14ChgCands()`. For each state and each `d` in `FB14_CHGD = [[-2,.08],[-1,.22],[0,.4],[1,.22],[2,.08]]`: clone, `fbRun` to `m+13` (`m = P.M + d - S.l`), apply that frame's bolts as `fbRi(x,359)` per bolt, then add `x` to a `Map x → Set(d)`.
   - It sets `CHG.narrow14 = {M, turn, done: false, n, dmap}` and returns the keys. This gave 14–22 distinct seeds.
   - charge_live.js line ~501: `cands = … : !E && chgP().id==='fb1' && typeof fb14ChgCands==='function' ? fb14ChgCands() : null`.
   - After `slog('chargeNarrow')`: `if (CHG.narrow14) { CHG.narrow14.done = true; CHG.narrow14.ok = !!ok; if (ok) res.narrow14 = true; }`.
   - `fb1Stage2(W, call, top, times, t3, narrow)`: when narrow, `tol: FB14_NTOL (0.03), max: 20000`. The caller passes `!!opts.cands`.
   - Hold: new `fb14Held()`:
     - return false if there is no `pendChg`, `!FB14.on`, or the profile is not fb1;
     - if there is no `narrow14` for this M: return `CHG.state === 'maps'`;
     - if not done: return true while in maps/search;
     - else: return `ok && !used && (CHG.state === 'search' || FB14.refining)`.
   - In `fb14Frame`, the `pendChg` apply condition adds `&& !fb14Held()`; it advances to M+10 and uses `FB14_CHGD` shifts. `fb14Advance` caps at `pendChg.M + 10` (was +11).
   - In `fb14Lock`, before the carried check: if `FB14.pendChg` and `narrow14.M` matches:
     - set `used = true` and clear `pendChg`;
     - build `held` = clones of every state at the `d` values whose candidate `x` gives `fbAdv(x) === H.a` (all `FB14_CHGD` if none), with `T.w *= wd`, `T.mk = pc.M + d`, `fbInputEv(T, 'chg', F, turn)`;
     - check `carried = held || FB14.states`;
     - if held and nothing matched: `FB14.states = fb14Cap(held)`.
   - charge_live.js `chgDecide` fb1 branch: if `CHG.res.narrow14`, set `res.trigT = CHG.trig.t` and call `fb14Lock(res)` directly (it now returns `how`). Only if the result is not 'carried', fall back to `fb14Refine(...).then(fb14Lock)` (placement plus joint took 5–7 s).
   - Also reordered `fb14Lock`: the carried check runs first, and fresh fits are built (wrapped in `buildFresh()`) only when nothing matched. Building them took about 1 s.

5. **T2 Charge read 2 frames off (e2e).** Shifts widened to ±2 (above).
   - Matched states keep their coin history: the line `T.sh = []; T.from = T.f;` was removed.
   - ClockFix: temporarily set `FB14.states = match`, run `fb14Weigh(M+61)`, vote `mk` by `w*lw`, and apply only if the top share is ≥ 0.6. Otherwise log `fb14ClockKept`.

6. **Wave particles in a second order.** 1 of 13 T4 waves (seed 13579bdf with the T4 popup left alone) split the `e00742fc` particles over odd and even frames, which changes T4's test.
   - Added `FB14_WAVE_POST_B = {67:1,68:1,69:1,70:2,71:1,72:2,73:2,74:3,75:2,76:4,77:2,78:5,79:2,80:6,81:2,82:7,83:2,84:8,85:1,86:8,87:1,88:7,89:2,90:8,91:1,92:8,93:1,94:7,95:2,96:7,97:2,98:7,99:2,100:7,101:2,102:7,103:2,104:7,105:2,106:8,107:1,108:8,109:1,110:7,111:2,112:8,113:1,114:8,115:1,116:7,117:2,118:7,119:2,120:7,121:2,122:7,123:2,124:7,125:2,126:6,127:2,128:6,129:1,130:5,131:1,132:4,133:1,134:4,136:3,138:2,140:1}` and `FB14_WAVEB_P = 0.08`.
   - `fbStep`: `if (dw > 0 && dw <= 160) { const k = (S.wb ? FB14_WAVE_POST_B : FB14_WAVE_POST)[dw] || 0; …`.
   - New `fb14WaveSplit(L)`: each state with `wb == null` becomes wb 0 at weight ×0.92 plus a clone with wb 1 at ×0.08. It is applied in `fb14Input` when kind is 'chg' and turn 4, and at the end of `fb14Lock` when turn === 4.
   - `fb14Cap` key includes `(S.wb ? 1 : 0)`.

7. **Harness fixes.**
   - fb14_e2e.py: `ncap(n)` = the capture index where game step n first shows. The capture is 60 fps against 29.97 game fps (2.002 pictures a frame), so the old `2*n` splice drifted about 1 frame per 500. Replaced `2*(R0+1+d)`, `2*ref[2]`, `2*(nZ+1)`, `2*(R7+10)`.
   - Miss now requires `shroom >= 1` (Life Shroom count of item 149); T4 requires `wave_now(r)` (Bowser's actor+0x88+8, TurnsSinceShockwave == 0).
   - `GUARD = 1`: one A on confirm+400 (T1) or +87 (T2–T4).
   - test_fb14_page.js, `VCLOCK=1`: `performance.now` is overridden to the fed picture time; the feed paces to real time but never drops (`run1.sh`: `VCLOCK=1 LATEMS=600000`). Without it, long manifests dropped 1300–2900 pictures in v86 and in v87 too.
   - The e2e queue now deletes each finished run's png/jpg dirs and .mkv files. /dev/shm filling up caused one OOM.
   - Test-only tracer in fb14_live.js: `fb14Truth`/`fb14IsTrue`, guarded by `window.__fb14seeds`; test_fb14_page.js passes `M.truthSeeds {off, s, c, ph, ev}`. `window.__fb14` also exposes `FB14_MAXH`, `cap`, `held`, `chgCands`.
   - test_fb14_v86.js thresholds: 'sure' ≥ 0.55 (v87 measured 0.592), and the pending Charge now stops at 1010.

## (2) Guarding (fb2_route/guard_scan.py, b10 build)
- A single A on every frame of Bowser's turn (T2 k 0–150, T1 330–560, T4 0–220, D 0–5 each), and mashing every 2–5 frames from his AI on: **no draw changes on misses** for T1–T3.
- Blocked hits still killed Mario (Life Shroom used), so the hit read is unchanged.
- A presses during Cloud Nine's message (before +332) add speech-blip draws.
- On T4, a single A at P+86..88 makes Lakilester block the wave. He is not KO'd (ko [0,0] instead of [13,3]) and the draws change from P+89. That is after T4's dodge test at P+85, so the T4 beep is unaffected, but the model past T4 does not cover a blocked wave.
- Mashing on T4 (every 2–5 frames) only shortened the turn, with no draw change, and did not block.

## (3) e2e results (VCLOCK, GUARD=1, idle machine, the final code)
| seed | turn | planned frame, perfect-press claim | lands at planned / −1 / +1 |
|---|---|---|---|
| 1234abcd | T1 | 453, ~1.0 | yes / yes / yes |
| 1234abcd | T2 | 1477, 1.0 | yes / yes / yes |
| 1234abcd | T3 | 2036, 1.0 | yes / yes / yes |
| 1234abcd | T4 | 2583, 1.0 | yes / yes / no — the wave came and missed Mario |
| 9e3779b9 | T1 | 480, 1.0 | yes / yes / yes |
| 9e3779b9 | T2 | 1415, 1.0 | yes / yes / yes |
| 9e3779b9 | T3 | 1996, 1.0 | yes / yes / yes |
| 9e3779b9 | T4 | 2593, 1.0 | yes / yes / yes — wave, missed Mario |

2b7e1516, 5eed0fb2, 0badc0de and 13579bdf were queued or running when the container restarted. **Only 2 of the 6 seeds you asked for were completed.**

Earlier spoiled runs, for the record: 2000 ms drop feed (T3 blind, the page dropped 2910 pictures); first v87 build (T2 planned at 99.85% and Bowser hit — that was the coin-phase bug); no-drop feed with the real clock (T2 planned at frame 4517, blind).

## (4) Task B: new Ultra Jr. Troopa route (Bombette Do Nothing every turn)
**Draws** (nb_cc/ub2_route_log.py; 10 plan-mode and 6 random fights; DIAGNOSTIC writes: seed, items [Whacka 0x93, Maple Syrup 0xA3, Life Shroom 0x95 ×2], Mario HP 10 / FP 10). Every turn is a TURNS entry the core already has:
- Super Charge: `jr_charge` (eio on +13/+16).
- Do Nothing at 10 HP: `jr_nothing_hit` (10×359 on +53, no roll).
- Do Nothing at 2 HP: `jr_nothing_cc` (Close Call rand_int(100) on +26, caller 80277518; next menu +93 after a dodge, +109 after a hit at 10 HP).
- Whacka's Bump: `nb_whacka` (22×(359,10,10) on +118; HP and FP set to 10).
- Maple Syrup: `nb_syrup` (10×(359,10,10) on +118).
- T7 Power Bounce with four Charges: 11×359 on +52/79/106/133/160, cap rolls on +78/105/132/159 (caller 802a1168, caps 140/98/68/47). 6 hits kill him from 60 HP; 5 leave him at 5.

**HP and FP along the route:** T1 10→2; T2–T6 at 2 (Close Call); T3 Whacka → 10, then hit to 2; Super Charge costs 4 FP (max FP 10).

**Menus:** Charge, Whacka and Syrup confirm → Bombette's menu +153.

**Model check:** 55 segments (each Super Charge as the lock), 87,860 frames, every 8th seed equal; 49 Close Calls (152 checks); 10 Power Bounce outcomes (40 checks).

**Page odds** (test_ub2_page.js, 40 model games per row, Charge relocks on T2/T4/T5, no coin fed):
- Per turn, ±1-frame presses actual (claimed): T2 80.6% (76.6%), T4 85.6% (81.1%), T5 86.9% (81.4%), T6 85.6% (80.5%), T7 6+ 88.8% (84.7%).
- Perfect-press claims 93–96%; every planned frame landed.
- Whole fight: perfect press 40/40; ±1 presses 21/40 (52%); blind 0.26%.
- T1 lock alone, no relock: whole fight 32/40.
- All 120 relocks agreed with the carry.

**Speed** (nb_cc/speed_jr.py, normal core; first battle menu → post-battle fade; 20 frames on each menu, popup A on +77, deciding confirms on the first frame that works):

| route | T1 | T2 | T3 | T4 | T5 | T6 | T7 | total frames | seconds |
|---|---|---|---|---|---|---|---|---|---|
| New (Do Nothing) | 342 | 346–355 | 415 | 358–361 | 346–348 | 399–406 | 548–549 (Power Bounce + fade) | 2758–2766 | 92.0–92.3 |
| Old (Bombs, ENDGAME_JR) | 503 | 611 | 522–523 | 595–598 | 359–364 | 538–567 (Power Bounce + fade) | — | 3134–3159 | 104.6–105.4 |

- **The new route is about 390 frames (13 s) faster**, mostly because each Do Nothing turn is 150–250 frames shorter than a Bomb turn.
- In the old route Jr. Troopa is at 44 HP before the Power Bounce; in the new one at 60. 6 bounces kill him on both.
- An earlier, rougher timing (random 2–40 frame waits) gave PB confirm at a median 2723 frames (new) against 2918 (old).

## (5) Every code change, as precisely as I can give it
- **fb14_live.js:** everything in (1) items 1–6, plus the test hooks in item 7.
- **charge_live.js:** the `cands` line for fb1; `CHG.narrow14` done/ok after `chargeNarrow`; `fb1Stage2` gets the 6th argument `!!opts.cands`; the `chgDecide` narrow14 direct-lock path.
- **jr_live.js:**
  - `JR_SEQ_UB2`, in order:
    - jr_charge T1 (charge, hide 3)
    - jr_nothing_hit T1 (hide 3, strat, rearm)
    - jr_charge T2
    - jr_nothing_cc T2 (prof jrcc_nothing, cc 26, hit jr_nothing_hit, next 93, strat)
    - nb_whacka T3 (hide 3, menu 150)
    - jr_nothing_hit T3 (strat, rearm)
    - jr_charge T4
    - jr_nothing_cc T4 (rearm, revive 9)
    - jr_charge T5
    - jr_nothing_cc T5 (revive 11)
    - nb_syrup T6 (menu 150)
    - jr_nothing_cc T6
    - jr_pb T7 (prof jrpb6u, what 'Power Bounce')
  - `JR_SEQS.ub2`; `jrIsNB()` replaces `JRS() !== JR_SEQ` in the `ci.c = -13` line and in the no-lock text.
  - New no-lock text for ub2: "Mario first on T1, T2, T4 and T5: Super Charge on himself, then Bombette: Do Nothing".
  - Blind text for jrpb6u: "6+ bounces about 32%". Status line for jrpb6u. Header "Jr. Troopa (Do Nothing route)". `jrBlind` regex `/^jrpb6[nu]?$/`.
- **pmrng_core.js:** `PROFILES.jrpb6u` = effects {52, 79, 106, 133: 11×359}, rolls `[[78,140],[105,98],[132,68],[159,47]]` with ok `v <= c`; vanish 2, minRun 2.
- **page_template.html:**
  - Option `charge2` "Charge lock, Do Nothing route: Bombette Do Nothing every turn, beeps on T2, T4-T7".
  - `ENDGAME_JR2`, 6 steps, all `seq: 'ub2'`, `chg: 'jr'`:
    - T1: jr 1, cat S
    - T2: jr 3, prof jrcc_nothing
    - T3: no step
    - T4: jr 7
    - T5: jr 9
    - T6: jr 11
    - T7: jr 12, prof jrpb6u, cat K
  - `jrRoute()` returns 'shine', 'charge2' or 'charge'; `endgameNow()` maps charge2 → ENDGAME_JR2.
  - `ZW_BLIND.jrpb6u = 0.322`; `JR_SEQ_UB2` exported in `__tot`; `routeOddsShow` on route change; the Jr. odds line made route-dependent.
  - `VERSION` set to 'v87', and the version checks in 8 tests moved to v87.
- **New files:**
  - fb2_route/chain_log.py, chain_fixture.py, e2e_relog.py, guard_scan.py
  - nb_cc/ub2_route_log.py, speed_jr.py
  - check_core.js ub2 branch (TURNS `__ub2_pb`) and a NOTE env in make_fixture.js
  - test_fb14_chain.js, test_fb14_v87.js, test_ub2_model.js, test_ub2_page.js (all added to run_suite.sh)
  - fixtures fb14_chain_logs.json and ub2_logs.json — both lost; they need regenerating from new emulator runs.
- **fb2_route/README.md:** file-table rows for the new scripts.
- **README v87 draft:** was in the scratchpad and is lost; its content is the material above.

## Not done
- e2e on 4 more seeds.
- The full run_suite.sh.
- The build to timeout_timer_v87.
- The commit and push.
- Task C.

Everything above was emulator-only and has to be re-created and re-tested before committing.
