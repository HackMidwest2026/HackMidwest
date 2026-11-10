//@ Jr. Troopa on the Charge-lock route (jr_charge/README.md; charge_live/README.md v73). Inlined into page_template.html
//@ after fb2_live.js by shared/inline.py (//@ lines are dropped). Needs the page globals (R, FRAME, $, num, slog, st, zw, V,
//@ isRoute, RT, routeStep, setStep, render, PROF) and charge_live.js (CHG, CHG_PROF, chgReset, chgStartTracker, chgArena).
/* ---------- Jr. Troopa: one Charge lock carried through the fight ----------
 * The route (jr_charge/README.md): T1 Charge; Bomb - T2 Bomb; Whacka - T3 Charge; Bomb (Close Call) - T4 Bomb; Maple Syrup
 * (Close Call) - T5 Charge; Do Nothing (Close Call) - T6 Power Bounce (6+, Bomb if 5). Mario's T1 Super Charge rays lock
 * the seed (profile jr); the zero-wait tracker then carries it frame-exactly through every later confirm (emulator: every
 * frame from the T1 Charge to the T3/T4 Close Calls in 10 runs, from T3 to T6's cap rolls in 17; the page's own core
 * jr_charge/jc_check_core.js: 64/64 Charge segments, 110/110 outcomes). The levers are the confirms that decide a roll:
 * the T3 Bomb target A (Close Call at +179), the T4 Maple Syrup A (+163), the T5 Do Nothing A (+26) and the T6 Power
 * Bounce A (cap rolls at +78/+105/+132/+159); each is beeped on its target screen with the Hallway's machinery (zwPlan:
 * window types, beeps, offsets, the v72 weighting and doubt, the beeps stopped on a bad plan).
 *
 * Turn tracking: every confirm on this route but Bombette's Do Nothing hides the status bar a fixed number of frames
 * after the A (emulator: Mario's actions 3, Bombette's Bomb 4); Do Nothing is read from its Strategies screen closing
 * (or the bar hiding when Jr. Troopa's turn starts, JRS()). The page counts the hides after a menu (bar up 0.3 s+) in
 * route order (JRS()), each one an input to the tracker with its frame -2..+1 (JR_SHIFTS: the coin settles them). The
 * Charge bursts anchor the count (T1, T3, T5).
 *
 * Deaths: a Close Call that fails kills Mario and the Life Shroom revives him at 10 HP: 933-939 RNG steps nobody
 * models, so the carry ends there. The status bar is up through Jr. Troopa's turn (emulator: back ~134 frames after the
 * Bomb, up through the hit, the death and the revive), so the page reads Mario's HP from it: at 2 HP the tens place left
 * of the units is empty, after the revive it shows the "1" of 10 (jrTens; the revive comes before the next menu, which
 * opens 246 / 230 / 93 frames after the Bomb / Syrup / Do Nothing confirm with a dodge and 359 frames later with a death,
 * every emulator run). A dodge (the next confirm, or that time passing, with no 10 HP seen) drops the states that would
 * have died; a death turns the tracker off (the next turn has no roll at 10 HP: Syrup / Do Nothing whenever you like),
 * and the next Charge locks again.
 * Each later Charge (T3, T5) is also read: its lock checks the carry (the carried states stepped to its frame 0); if
 * none fits, the tracker starts again from the new lock and the confirms since its Charge. */
const JR_SEQ = [
  { id: 'jr_charge', t: 'T1', charge: true, hide: 3 },
  { id: 'jr_bomb_t1', t: 'T1', hide: 4 },
  { id: 'jr_bomb', t: 'T2', hide: 4 },
  { id: 'jr_whacka', t: 'T2', hide: 3, rearm: true },
  { id: 'jr_charge', t: 'T3', charge: true, hide: 3 },
  { id: 'jr_bomb_cc', t: 'T3', hide: 4, prof: 'jrcc_bomb', cc: 179, next: 246, what: 'Bomb', revive: 7 },
  { id: 'jr_bomb', t: 'T4', hide: 4 },
  { id: 'jr_syrup_cc', t: 'T4', hide: 3, prof: 'jrcc_syrup', cc: 163, hit: 'jr_syrup_hit', next: 230, what: 'Maple Syrup', rearm: true, revive: 9 },
  { id: 'jr_charge', t: 'T5', charge: true, hide: 3 },
  { id: 'jr_nothing_cc', t: 'T5', hide: 3, prof: 'jrcc_nothing', cc: 26, hit: 'jr_nothing_hit', next: 93, what: 'Do Nothing', strat: true },
  { id: 'jr_pb', t: 'T6', hide: 3, prof: 'jrpb5', what: 'Power Bounce' } ];
/* v85, the Normal Boots route (charge_live/README.md v85): Goombario instead of Bombette, Mario's Super Charge every turn but
 * T3 (Maple Syrup) and T6/T7. A Goombario Charge (nb_gch, hide 4: its target-screen A, gStatusBar off 3 frames later as
 * Bombette's Bomb) is followed by the A that closes its "attack power up" box (cancel: P = +73..+132, or +133 untouched):
 * the Close Call hangs off P (cancel id, ccP frames after P; Hallway: Bowser's AI at P + 16, ai). The page reads P from the
 * status bar coming back (P + 5, emulator: every run; nbCancelSeen). cancel entries: the route moves on after P, not G.
 * menu: frames from the confirm before the next lever can be planned (jrPlanFloor; after a Super Charge Goombario's menu opens
 * 154 frames later without the popup A, emulator; 150 leaves the runner time to reach his Charge's target screen).
 * The Headbonk (T5) is a plain target-screen lever (Close Call +143). T6 Whacka (10 HP after it: Jr. Troopa's hit, no roll)
 * and Goombario's Do Nothing (Strategies, as Bombette's), T7 Power Bounce 5+ (jrpb5n) from the carry. */
const JR_SEQ_NB = [
  { id: 'jr_charge', t: 'T1', charge: true, hide: 3, menu: 110 },
  { id: 'nb_gch', t: 'T1', hide: 4, cancel: 'nb_jrhit', what: 'A on Goombario\'s box', rearm: true },
  { id: 'jr_charge', t: 'T2', charge: true, hide: 3, menu: 150 },
  { id: 'nb_gch', t: 'T2', hide: 4, cancel: 'nb_jrcc', ccP: 29, hit: 'nb_jrhit', next: 97, prof: 'jrcc_gch', profW: 'jrcc_gchw', what: 'A on Goombario\'s box', revive: 5 },
  { id: 'nb_syrup', t: 'T3', hide: 3, menu: 160, rearm: true },
  { id: 'nb_gch', t: 'T3', hide: 4, cancel: 'nb_jrcc', ccP: 29, hit: 'nb_jrhit', next: 97, prof: 'jrcc_gch', profW: 'jrcc_gchw', what: 'A on Goombario\'s box', revive: 7 },
  { id: 'jr_charge', t: 'T4', charge: true, hide: 3, menu: 150 },
  { id: 'nb_gch', t: 'T4', hide: 4, cancel: 'nb_jrcc', ccP: 29, hit: 'nb_jrhit', next: 97, prof: 'jrcc_gch', profW: 'jrcc_gchw', what: 'A on Goombario\'s box', rearm: true, revive: 9 },
  { id: 'jr_charge', t: 'T5', charge: true, hide: 3, menu: 150 },
  { id: 'nb_hb', t: 'T5', hide: 4, prof: 'jrcc_hb', cc: 143, hit: 'nb_hb_hit', next: 210, what: 'Headbonk' },
  { id: 'nb_whacka', t: 'T6', hide: 3 },
  { id: 'jr_nothing_hit', t: 'T6', hide: 3, strat: true, what: 'Do Nothing' },
  { id: 'jr_pb_nb', t: 'T7', hide: 3, prof: 'jrpb5n', what: 'Power Bounce' } ];
const HW_SEQ_NB = [
  { id: 'hw_charge', t: 'T1', charge: true, hide: 3, menu: 150 },
  { id: 'nb_gch', t: 'T1', hide: 4, cancel: 'nb_hwcc', ai: true, next: 160, prof: 'hwcc_gch', profW: 'hwcc_gchw', what: 'A on Goombario\'s box' },
  { id: 'to_nb', t: 'T2', hide: 3, prof: 'timeout', what: 'Time Out' } ];
const JR_SEQS = { ultra: JR_SEQ, nbjr: JR_SEQ_NB, nbhw: HW_SEQ_NB };
const jrStepSeq = () => { const s = isRoute() && RT()[routeStep]; return (s && s.seq) || 'ultra'; };
const JRS = () => JR_SEQS[(JRT && JRT.on && JRT.seq) || jrStepSeq()] || JR_SEQ;
// v85: what the beeped press is on a Goombario Charge turn (by the Settings mode)
const jrWhat = s => (!s ? null : s.cancel ? (jrSeqProf(s) === s.profW ? 'Goombario\'s Charge confirm' : 'A on Goombario\'s box') : s.what);
const jrSeqProf = s => (s && s.profW && (typeof nbccMode !== 'function' || nbccMode() === 'wait') ? s.profW : s && s.prof);
// the P read from the bar coming back: -2..+1 as the hides (a dropped picture reads it late)
const NB_SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];
const NB_SHIFTS_BLIND = [[-3, 0.05], [-2, 0.1], [-1, 0.2], [0, 0.3], [1, 0.2], [2, 0.1], [3, 0.05]];   // the bar's return not seen: the beeped frame, the runner's press spread
const JR_DEATH = 359;          // frames a death and the Life Shroom revive add before the next menu (emulator: every run)
// a confirm read from the bar hiding: -2..+1 frames, as the Spiny Flip's (CHG_SHIFTS): a dropped picture only ever reads it
// late (the frame-fed end to end under load read the T3 Bomb 2 frames late and the T3 Charge 1-2 late)
const JR_SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];
/* when the outcome seen (a dodge) fits none of the states, the Close Call confirm is tried again -4..+4 from the states
 * before it (jrRecover): the states left are a reconstruction, never beeped on until the coin confirms them (jrReconOk) */
const JR_SHIFTS_WIDE = [[-4, 0.03], [-3, 0.07], [-2, 0.15], [-1, 0.2], [0, 0.25], [1, 0.15], [2, 0.08], [3, 0.05], [4, 0.02]];
const JR_RECON_TAPS = 2;       // shines the heaviest reconstructed state must have matched (and none missed) before a beep
/* v86.1 (console 2026-11-09, logs 1794269702752 / 1794269850246, clips 19-14-36 / 19-17-03): a hide counts as a confirm
 * after 600+ ms of bar up (as hudWatch's barHide and the Charge's arming; v86 took 300). On battle entry the bar shows
 * 380-400 ms before Jr. Troopa's speech hides it; v86 counted that as the T1 Bomb. The fastest console confirm in every
 * log: 1133 ms (the T1 Charge right after the speech). */
const JR_UPMIN = 600;
/* v86.1: the bar gone this long is no turn of the fight (a reset, the walk back, the battle loading; the longest gap inside
 * the fight is a Power Bounce or a death + revive with the bar up): the bar's return after it may be a new battle */
const JR_ENTRY_GAP = 12000;
/* v86.1: a hide after this much bar up (an idle runner, or a reset after it: 104883 ms in log 1794269850246) counts only
 * once the bar is back within JR_ENTRY_GAP; a reset never brings it back that soon (a real confirm after a long idle does:
 * the T5 Charge 84016 ms after the T4 death, same log, is anchored by its burst at once) */
const JR_UPHOLD = 30000;
/* blind odds (jr_charge/README.md, jc_odds.py): Close Call 30%; Power Bounce 5+ 67.5%, 6+ 32.2% */
const JR_BLIND = { cc: 0.30, p5: 0.675, p6: 0.322 };
const JRT = { bar: {} };
function jrReset(why) {
  // v86.1: the Charge already seen stays seen (v86 set it null, and the next frame's jrTick started a "new fight" at the
  // PREVIOUS Charge's time: the restart consumed T1 with a stale burst)
  const seen = typeof CHG !== 'undefined' && CHG ? CHG.trig || null : null;
  if (JRT.bar) JRT.bar.held = null;
  Object.assign(JRT, { on: false, k: 0, anchor: null, chargeK: null, inputs: [], dead: null, hp10: {}, out: {}, ccPend: null, snap: null, lockK: null, cross: null, t0: null, trigSeen: null, hides: [], hist: [], why: why || null, ccSnap: null, recon: null, lost: null, lastLock: null, lostF: null, shineTry: 0, shineRec: null, seq: null, cancel: null });
  JRT.trigSeen = seen;
  if (zw.on && zw.fight === 'jr') zw.on = false;
}
jrReset();
var JR_READY = true;     // (var: charge_live.js's chgShow runs at load, before this file's consts exist)
const jrStepNow = () => isRoute() && !!RT()[routeStep] && RT()[routeStep].jr != null;
const jrZw = () => zw.on && zw.fight === 'jr' && jrStepNow() && PROF().group === 'jr' && !jrStepAt10() && jrReconOk();
/* the route step for the next confirm k: the first Jr. Troopa step whose confirm is k or later (past the last: the step
 * after the fight) */
function jrStepFor(k) {
  const L = RT(), sq = (JRT.on && JRT.seq) || jrStepSeq(); let last = -1;
  for (let i = 0; i < L.length; i++) if (L[i].jr != null && (L[i].seq || 'ultra') === sq) { if (L[i].jr >= k) return i; last = i; }
  return last >= 0 ? last + 1 : -1;
}
function jrGo(k) {
  JRT.k = k; const i = jrStepFor(k);
  if (i >= 0 && i < RT().length && i !== routeStep) { JRT.stepping = true; try { setStep(i); } finally { JRT.stepping = false; } }
}
// the step's roll does not happen: Mario at 10 HP after a revive (no Close Call), or the carry ended before it
function jrStepAt10() { const s = jrStepNow() && RT()[routeStep]; return !!(s && JRT.hp10[s.jr]); }
/* ---------- the status bar, per video frame (onFrame) ---------- */
function jrFrame(t, present) {
  const B = JRT.bar;
  if (present) {
    if (!B.since) B.since = t;
    // back for 3 frames: a gap shorter than 8 frames was a flicker (a shine's white flash, a dropped picture) and the bar's
    // up time goes on from before it
    if (B.gone && t - B.since >= 3 * FRAME) { if (!B.done) B.upFrom = B.prevUp; else jrBarBack(B, B.since - B.gone); B.gone = 0; }
    if (!B.gone && !B.upFrom) B.upFrom = B.since;
  } else {
    if (B.since && !B.gone) { B.gone = t; B.prevUp = B.upFrom; B.wasUp = B.upFrom ? t - B.upFrom : 0; B.upFrom = 0; B.done = false; }
    B.since = 0;
    if (B.gone && !B.done && t - B.gone >= 8 * FRAME) {
      B.done = true;
      if (B.wasUp >= JR_UPHOLD && JRT.on) { B.held = { t: B.gone, up: B.wasUp }; slog('jrHideHeld', { at: Math.round(B.gone), upMs: Math.round(B.wasUp) }); }
      else if (B.wasUp >= JR_UPMIN) jrHide(B.gone, B.wasUp);
      else if (B.entry && B.gone - B.entry.at < JR_UPMIN + 8 * FRAME) jrEntry(B.gone, B.entry.gap, B.wasUp);   // the bar's flash before Jr. Troopa's speech
      B.entry = null;
    }
  }
  nbCancelWatch(t, present);
  jrOutcomeWatch(t, present);
  jrTick(t);
  jrShineTry();
}
/* v86.1: the bar back after a gap (ms): a held long-idle hide counts now (a turn went on) or never (gone JR_ENTRY_GAP+:
 * a reset); a long gap is remembered (jrResyncK) and its bar-up may be a battle entry's flash (jrEntry) */
function jrBarBack(B, gap) {
  if (B.held) { const h = B.held; B.held = null; if (gap < JR_ENTRY_GAP) jrHide(h.t, h.up); else slog('jrHideDropped', { at: Math.round(h.t), upMs: Math.round(h.up), goneMs: Math.round(gap) }); }
  if (gap >= JR_ENTRY_GAP) { (B.gaps = B.gaps || []).push({ from: B.gone, to: B.since }); if (B.gaps.length > 8) B.gaps.shift(); B.entry = { at: B.since, gap }; }
  else B.entry = null;
}
/* v86.1, battle entry (clips 19-14-36, 19-17-03: the runner reset and walked back in): after the bar was gone 12 s+, it
 * shows 380-400 ms, Jr. Troopa's speech hides it, then the T1 menu. The fight starts over: T1, waiting for its Charge. */
function jrEntry(tH, gap, upMs) {
  if (!jrStepNow()) return;
  slog('jrBattleEntry', { at: Math.round(tH), goneMs: Math.round(gap), upMs: Math.round(upMs), was: JRT.on ? JRT.k : null });
  if (JRT.on || JRT.k) jrReset('battle entry');
  if (typeof CHG !== 'undefined' && ['locked', 'nolock', 'failed', 'notseen'].includes(CHG.state)) chgReset();
  jrGo(0);
}
/* Mario's HP tens place in the status bar (320-space x 61..67, y 27..36: blank at 2 HP, the "1" of 10 after a revive;
 * emulator renders, jr_charge/README.md): the share of white glyph pixels there */
const JR_TENS = [61, 27, 67, 36];
function jrTens() {
  if (window.__jrTensTest) return window.__jrTensTest();     // (tests)
  const [SX, OX, SY, OY] = chgMap(), b = { x: (OX + JR_TENS[0] * SX) / 1280, y: (OY + JR_TENS[1] * SY) / 720, w: (JR_TENS[2] - JR_TENS[0]) * SX / 1280, h: (JR_TENS[3] - JR_TENS[1]) * SY / 720 };
  const g = sample(b, 12, 12); let n = 0;
  for (let i = 0; i < g.length; i += 4) if (g[i] > 150 && g[i + 1] > 150 && g[i + 2] > 150) n++;
  return n / (g.length / 4);
}
const JR_TENS_MIN = 0.12;
/* after a Close Call confirm: 10 HP on a steady bar for 6 frames = Mario died and was revived; no 10 HP by the next
 * confirm (or by the time a revive would long have shown) = a dodge */
function jrOutcomeWatch(t, present) {
  const P = JRT.ccPend; if (!P) return;
  const fr = (t - P.t) / jrRate(), B = JRT.bar;
  if (present && B.since && t - B.since > 5 * FRAME && fr > 150) {
    const v = jrTens(); P.n = v >= JR_TENS_MIN ? (P.n || 0) + 1 : 0; P.max = Math.max(P.max || 0, v);
    if (P.n >= 6) { JRT.ccPend = null; slog('jrOutcome', { k: P.k, frames: Math.round(fr), dodge: false, by: 'HP 10', tens: +v.toFixed(2) }); jrDeath(P.k, Math.round(fr)); return; }
  }
  if (fr > JRS()[P.k].next + JR_DEATH + 60) jrSettle('time');
}
function jrSettle(by) {
  const P = JRT.ccPend; if (!P) return; JRT.ccPend = null;
  slog('jrOutcome', { k: P.k, dodge: true, by, tensMax: +(P.max || 0).toFixed(2) }); jrDodge(P.k);
}
/* a confirm read from the bar hiding (or, for Do Nothing, from the Strategies screen closing: jrScreenClosed) */
function jrHide(tH, upMs) {
  JRT.hides.push(tH); if (JRT.hides.length > 8) JRT.hides.shift();
  if (!jrStepNow() || !JRT.on) return;                 // before the fight: the T1 Charge's burst starts it (jrBurst)
  if (JRT.k >= JRS().length) return;
  const s = JRS()[JRT.k];
  if (s.strat && JRT.stratAt != null && Math.abs(tH - JRT.stratAt) < 2000) { slog('jrHideAfterNothing', { at: Math.round(tH) }); return; }   // Do Nothing was read from its screen
  slog('jrHide', { k: JRT.k, id: s.id, at: Math.round(tH), upMs: Math.round(upMs) });
  jrConfirm(JRT.k, tH, s.hide, 'bar');
}
/* Bombette's Do Nothing on its Strategies screen (cat S): the screen closing is the confirm (3 frames, VAN.S) */
function jrScreenClosed(tObs) {
  if (!jrStepNow() || !JRT.on || JRT.k >= JRS().length) return false;
  const s = JRS()[JRT.k]; if (!s.strat) return false;
  JRT.stratAt = tObs; slog('jrStrategiesClosed', { k: JRT.k, at: Math.round(tObs) });
  jrConfirm(JRT.k, tObs, R.PROFILES.jrcc_nothing.vanish, 'screen'); return true;
}
function jrConfirm(k, t, h, src) {
  if (JRT.ccPend && JRT.ccPend.k < k) jrSettle('next confirm');
  if (JRT.cancel && !JRT.cancel.done && JRT.cancel.k < k) nbCancelSeen(null, 'next confirm');     // v85: the bar's return was missed
  const s = JRS()[k]; let id = s.id; if (s.hit && JRT.hp10[k] && !s.cancel) id = s.hit;
  const inp = { k, id, t, h, src };
  // v85: Goombario's Charge. Wait mode (or the T1 Charge, no roll): the box runs out (P = +133), so this confirm decides it
  // and both go in now; cancel mode: the box A comes later (nbCancelSeen), planned here (nbCancelPlan)
  const roll = !!(s.ccP || s.ai) && !JRT.hp10[k], pid = roll ? s.cancel : s.hit || s.cancel;
  const wait = !!s.cancel && roll && jrSeqProf(s) === s.profW;      // (no roll: T1, or 10 HP after a revive: the box A is read all the same)
  if (s.cancel) { inp.pid = pid; if (wait) inp.wait = true; }
  JRT.inputs.push(inp);
  jrPress(inp);
  if (s.charge) JRT.chargeK = k;
  if (zw.on && zw.fight === 'jr') jrApply(inp);
  if (s.cc && id === s.id) JRT.ccPend = { k, t: t - h * jrRate() };
  if (s.cancel && wait && roll) JRT.ccPend = { k, t: t - (h - R.NB_K.none) * jrRate() };
  if (s.cancel && !wait) {
    JRT.cancel = { k, t, tA: t - h * jrRate(), pid, roll, done: false };
    if (JRS()[k].rearm && ['locked', 'nolock', 'failed', 'notseen'].includes(CHG.state)) chgReset();
    slog('nbCharge', { k, t: JRS()[k].t, roll });
    if (roll) nbCancelPlan('charge confirmed'); else render();
    return;                                       // the route moves on at the box A (nbCancelSeen)
  }
  // the Charge watcher arms again for the next Charge (its lock is in the tracker already)
  if (JRS()[k].rearm && ['locked', 'nolock', 'failed', 'notseen'].includes(CHG.state)) chgReset();
  jrGo(k + 1);
  if (k === JRS().length - 1) jrEnd('the fight is over (Power Bounce confirmed)');
}
const jrRate = () => (zw.on && zw.fight === 'jr' ? zw.rate : chgRate());
/* a dodge seen: the states whose roll hits are ruled out (likelihood 0), and the background ("none of the tracked states is
 * the game's", zwDoubt) is weighed by the chance a blind press dodges (likelihood 0.30), as v72 weighs the coin */
function jrDodge(k) {
  JRT.out[k] = 'dodge';
  if (!(zw.on && zw.fight === 'jr')) return;
  let gone = 0; const keep = [];
  for (const p of zw.parts) { if (p.cc && p.cc[k] === false) gone += p.w; else keep.push(p); }
  slog('jrDodge', { k, dropped: +gone.toFixed(4), left: keep.length });
  if (keep.length) { zw.parts = keep; zw.bg = (zw.bg || 0) * JR_BLIND.cc; return; }
  jrRecover(k);
}
/* the dodge fits none of the states (console 2026-11-08 T3: the merge bug, zwUpdate): rebuild them from the states before
 * that Close Call confirm with the confirm -4..+4, keep the ones that dodge, and apply the confirms since. The result is a
 * reconstruction: the background takes half the weight and no beep goes out until the coin confirms a state (jrReconOk).
 * Nothing dodges: no edge for the rest of the fight, until a Charge locks again (jrLock starts afresh on a dead tracker). */
function jrRecover(k) {
  const P = JRT.ccSnap, inp = P && P.k === k ? JRT.inputs.filter(x => x.k === k).pop() : null;
  if (inp && P.list.length) {
    const s = JRS()[k], out = [];
    for (const p of P.list) for (const q of jrSplit(p, inp, P.c, JR_SHIFTS_WIDE, s)) if (q.cc[k]) { q.err = 0; out.push(q); }
    if (out.length) {
      zw.parts = out; zw.dead = false; zw.deadAt = null;
      const since = JRT.inputs.filter(x => x.k > k);
      for (const x of since) jrApply(x);
      if (zw.parts.length && !zw.dead) {
        let sw = 0; for (const p of zw.parts) sw += p.w; zw.bg = Math.max(zw.bg || 0, sw);       // doubt 50%: the coin has to confirm
        JRT.recon = { k, taps0: zw.taps.length, at: performance.now() };
        slog('jrRecover', { k, c: P.c, particles: zw.parts.length, since: since.map(x => x.k), shifts: [...new Set(out.map(q => q.sh))].sort((a, b) => a - b) });
        if (typeof chgShow === 'function') chgShow(); return;
      }
    }
  }
  zw.parts = []; zw.dead = true; zw.deadAt = null; JRT.lostF = Math.floor(zwHorizon(performance.now()));
  JRT.lost = JRS()[k].t + ': the ' + (jrWhat(JRS()[k]) || 'press') + ' dodged, which none of the carried states allows';
  slog('jrLost', { k, why: 'outcome fits no state, even with the confirm -4..+4' });
  if (typeof chgShow === 'function') chgShow();
}
/* a reconstructed state beeps only once the coin confirms it: the heaviest state has matched JR_RECON_TAPS shines seen
 * after the reconstruction, with no shine missed or extra (its errors since then) */
function jrReconOk() {
  const R0 = JRT.recon; if (!R0) return true;
  if (!(zw.on && zw.fight === 'jr') || zw.dead || !zw.parts.length) return true;     // zwPlan says the seed is lost
  let top = null; for (const p of zw.parts) if (!top || p.w > top.w) top = p;
  let n = 0; for (const i of top.m) if (i >= R0.taps0) n++;
  return n >= JR_RECON_TAPS && !top.err;
}
/* v81 (the lock badge only; the beeps keep zwPlan's doubt / edge rules): a seed found again from the coin counts as
 * confirmed once its heaviest state has matched JR_RECON_TAPS shines seen after the restart, with none missed */
function jrShineRecOk() {
  const R0 = JRT.shineRec; if (!R0 || R0.taps0 == null) return true;
  if (!(zw.on && zw.fight === 'jr') || zw.dead || !zw.parts.length) return true;
  let top = null; for (const p of zw.parts) if (!top || p.w > top.w) top = p;
  let n = 0; for (const i of top.m) if (i >= R0.taps0) n++;
  return n >= JR_RECON_TAPS && !top.err;
}
function jrDeath(k, fr) {
  JRT.out[k] = 'death';
  // the next turn's Close Call turn is at 10 HP (the revive): no roll there, its 10-HP draws instead
  const nx = JRS()[k].revive; if (nx != null) JRT.hp10[nx] = true;
  JRT.dead = JRS()[k].t + ': Mario was hit (10 HP after the Life Shroom, read ' + fr + ' frames after the confirm): the revive breaks the carry';
  if (zw.on && zw.fight === 'jr') { zw.on = false; slog('jrCarryEnds', { k, why: 'death' }); }
  if (typeof chgShow === 'function') chgShow(); render();
}
/* an input in the tracker: like zwInput, with the confirm frame -2..+1 (JR_SHIFTS) and, on a Close Call confirm, whether
 * each state's roll dodges (p.cc[k]), so the outcome seen later can drop the ones that would have died */
function jrApply(inp, re) {
  const s = JRS()[inp.k];
  if (inp.cancel) { const g = JRT.inputs.find(x => x.k === inp.k && !x.cancel && x.c != null); inp.G = g ? g.c : null; }
  const c = inp.cancel && inp.rel != null && inp.G != null ? inp.G + inp.rel : Math.round(zwF(inp.t, inp.h + num('pfix')));
  inp.c = c;
  zwSeen(performance.now());
  if (zw.visFrom != null && (zw.visTo == null || zw.visTo < c - 4)) zw.visTo = c - 4;
  zw.visLocked = true;
  zwUpdate(Math.min(c - 3, zwHorizon(performance.now())));
  if (s.charge) JRT.snap = { k: inp.k, c, list: zw.parts.slice(0, 400).map(zwClone) };      // the carried states before this Charge (jrLock checks its lock on them)
  const cc = (s.cc && inp.id === s.id) || ((inp.cancel || inp.wait) && !!(s.ccP || s.ai) && inp.pid === s.cancel);
  // a Close Call confirm: the states before it are kept, in case the outcome seen fits none of the split (jrRecover)
  if (cc) JRT.ccSnap = { k: inp.k, c, list: zw.parts.map(p => Object.assign(zwClone(p), { cc: p.cc ? Object.assign({}, p.cc) : null })) };
  const out = [];
  const shifts = inp.shifts || (inp.cancel ? NB_SHIFTS : JR_SHIFTS);
  for (const p of zw.parts) out.push(...jrSplit(p, inp, c, shifts, s));
  zw.parts = out;
  if (zw.parts.length > ZW_MAXP) { slog('zwTooMany', { n: zw.parts.length }); zw.parts = []; zw.dead = true; }
  else zwBgAdd(ZW_BGIN);
  slog('jrInput', { k: inp.k, id: inp.id, c, src: inp.src, particles: zw.parts.length, re: re || undefined });   // re: replayed onto a new lock (jrStartFrom), in its clock
}
// one state x the confirm frame c + sh for each shift: the input's events in, and on a Close Call confirm the roll's
// outcome (q.cc[k]); the outcome is part of the state (zwUpdate merges only states with the same outcomes)
function jrSplit(p, inp, c, shifts, s) {
  const K = R.NB_K, nbRoll = (inp.cancel || inp.wait) && !!(s.ccP || s.ai) && inp.pid === s.cancel, cc = (s.cc && inp.id === s.id) || nbRoll;
  for (var out = [], i = 0; i < shifts.length; i++) {
    const [sh, ws] = shifts[i]; let f = c + sh;
    // v85: the box A only counts on +73..+132 after Goombario's Charge confirm (before: nothing; after: the box ran out)
    if (inp.cancel && inp.G != null) { if (f < inp.G + K.lo) continue; if (f > inp.G + K.hi) f = inp.G + K.none; }
    const q = zwClone(p); q.w = p.w * ws; q.cc = p.cc ? Object.assign({}, p.cc) : null; q.sh = sh;
    const P = inp.wait ? f + K.none : f, list = inp.wait ? [{ f, id: inp.id }, { f: P, id: inp.pid }] : [{ f, id: inp.id }];
    const ev = R.buildEv(list);
    zwMerge(q.ev, ev); q.evMax = Math.max(q.evMax, ...ev.keys(), ...[...ev.values()].flatMap(e => e.eio.map(x => x[0])), s.ai && (inp.cancel || inp.wait) ? P + K.hwai + 72 : 0);
    if (cc) (q.cc = q.cc || {})[inp.k] = nbRoll ? (s.ai ? nbAiRollOk(q) : jrRollOk(q, P + s.ccP)) : jrRollOk(q, f + s.cc);
    out.push(q);
  }
  return out;
}
// v85, Hallway Bowser after Goombario's Charge: his AI picks the attack, the Close Call comes 54 / 70 / 55 frames later (S.cc)
function nbAiRollOk(q) {
  const S = { s: q.S.s, nc: q.S.nc, inst: q.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: q.S.extra ? new Map(q.S.extra) : undefined, ccAt: q.S.ccAt };
  let g = q.g;
  for (let n = 0; n < 800 && !S.cc; n++) { if (q.pause && g === q.pauseAt) { S.nc += q.pause; g += q.pause; continue; } R.frameEv(S, g, q.ev); g++; }
  return !!(S.cc && S.cc.lucky);
}
/* ---------- v85: Goombario's Charge, the box A (Normal Boots) ----------
 * The plan: as soon as his Charge confirm is read (the bar hiding, 4 frames after its A), the frame of the A that closes his
 * "attack power up" box: zwPlan over the tracker's states stepped to the box (his Charge's sparkles end on +62), in the box
 * window (+73..+132, never past the lead), the perfect press (ppPick: a working frame, the centre of the widest run). */
function nbCancelPlan(why) {
  const C = JRT.cancel; if (!C || C.done || !C.roll || !jrZw()) return false;
  const g = JRT.inputs.find(x => x.k === C.k && !x.cancel && x.c != null); if (!g) return false;
  const K = R.NB_K, P0 = st.plan;
  zwPlan(why || 'box', { lo: g.c + K.lo, hi: g.c + K.hi, h: g.c + 63 });
  if (st.plan && st.plan !== P0) st.plan.nbK = C.k;
  return true;
}
/* the box A, read from the status bar coming back (his turn ends 5 frames after it, the picture one frame later: NB_BACK_H;
 * -2..+1). Not seen: the planned frame with the press spread (the beeps not stopped), else the box ran out (+133). */
const NB_BACK_H = 6;
function nbCancelSeen(tBack, why) {
  const C = JRT.cancel; if (!C || C.done) return; C.done = true;
  const inp = { k: C.k, id: C.pid, pid: C.pid, h: NB_BACK_H, src: tBack != null ? 'bar' : why, cancel: true };
  if (tBack != null) inp.t = tBack;
  else {
    const g = JRT.inputs.find(x => x.k === C.k && !x.cancel), P = st.plan && st.plan.nbK === C.k && !st.plan.stopped && g && g.c != null ? st.plan.zwAbs - g.c : null;
    inp.rel = P != null ? P : R.NB_K.none; inp.shifts = P != null ? NB_SHIFTS_BLIND : [[0, 1]];
    inp.t = C.tA + (inp.rel + inp.h) * jrRate();
  }
  JRT.inputs.push(inp); jrPress(inp);
  if (zw.on && zw.fight === 'jr') jrApply(inp);
  slog('nbBoxA', { k: C.k, how: inp.src, c: inp.c, G: inp.G, K: inp.G != null && inp.c != null ? inp.c - inp.G : null });
  if (C.roll) JRT.ccPend = { k: C.k, t: inp.t - inp.h * jrRate() };
  jrGo(C.k + 1);
  if (C.k === JRS().length - 1) jrEnd('the fight is over');
}
// makePlan on a box-A step (cancel mode): no lock / no roll -> the usual texts; before the Charge confirm -> what to do
function nbCancelMake() {
  const s = RT()[routeStep], C = JRT.cancel;
  if (jrStepAt10() || !jrZw()) { st.msg = jrNoLockMsg(); render(); if (typeof chgShow === 'function') chgShow(); return; }
  if (!C || C.k !== s.jr || C.done) { st.msg = 'Locked: confirm Goombario\'s Charge whenever you like. The beeps start as soon as the status bar hides: press A on the last beep to close his "attack power up" box → Close Call.'; render(); return; }
  if (st.plan && st.plan.nbK === C.k) return;
  nbCancelPlan('screen');
}
function nbCancelWatch(t, present) {
  const C = JRT.cancel; if (!C || C.done) return; const B = JRT.bar, r = jrRate();
  if (present && B.since && t - B.since >= 3 * FRAME && B.since > C.tA + (R.NB_K.lo + 3) * r) { nbCancelSeen(B.since, 'bar'); return; }
  if (t > C.tA + (R.NB_K.none + 60) * r) nbCancelSeen(null, 'not seen');
}
// does this state's Close Call roll (the first draw on frame f) dodge? (simulated on a copy, the particle's clock)
function jrRollOk(q, f) {
  const S = { s: q.S.s, nc: q.S.nc, inst: q.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: q.S.extra ? new Map(q.S.extra) : undefined };
  let g = q.g;
  while (g < f) { if (q.pause && g === q.pauseAt) { S.nc += q.pause; g += q.pause; continue; } R.frameEv(S, g, q.ev); g++; }
  return R.randInt(S.s, 100)[1] < 30;
}
/* ---------- the seed found again from the coin (v80) ----------
 * The tracker is dead (an outcome that fits no state, or the coin ruled every state out) but this fight had a good Charge
 * lock: the game's RNG is still that seed stepped on some number of times, bounded by the frames since the lock (one step
 * a frame, a coin draw every 24-48 frames, the modelled inputs' draws, plus a margin). Every position in that range x the
 * first shine's coin frame x the confirms' shifts in the stretch is simulated over the shines seen since the tracker died
 * (R.frameEv, the inputs' events); a position must explain every shine and show none where the coin was watched. Exactly
 * one cluster of such positions (a few steps apart, at most JR_SHINE_MAXSTATES states), from JR_SHINE_MIN shines or more
 * and with few wrong clusters expected (JR_SHINE_P): the tracker starts again from its states (zwPlan's doubt and edge
 * rules decide the beeps). Otherwise: no
 * edge, and the next Charge locks again.
 * Console 2026-11-08 (log 1794154120837): the T3 tracker died; the T4 menu (252 s) showed 78 shines and the T5 / T6 menus 8. */
const JR_SHINE_MIN = 5, JR_SHINE_USE = 12, JR_SHINE_MARGIN = 300, JR_SHINE_CLUSTER = 8, JR_SHINE_MAXSTATES = 12;
/* the evidence: a wrong position explains n shines about JR_SHINE_P^n of the time (this log: 5 wrong of 28352 positions x
 * frames x shifts at 5 shines, none at 6), so tried x JR_SHINE_P^n wrong clusters are expected. The tracker starts again
 * only below JR_SHINE_EMAX, with that share as its doubt (at least 10%) */
const JR_SHINE_P = 0.18, JR_SHINE_EMAX = 0.5;
function jrShineTry() {
  if (!(zw.on && zw.fight === 'jr' && zw.dead) || !JRT.on || !JRT.lastLock || JRT.lastLock.t0 !== zw.t0) return;
  if (zw.taps.length === JRT.shineTry) return;
  JRT.shineTry = zw.taps.length;
  try { jrShineSearch(zwHorizon(performance.now())); } catch (e) { slog('jrShineError', { msg: String(e && e.message || e) }); }
}
function jrShineSearch(hor) {
  const L = JRT.lastLock, now = performance.now(), late = zw.tapLate || 3.5;
  // the stretch: shines after the tracker died and after the rays of any Charge since (their parts draw on their own)
  const ins = JRT.inputs.filter(x => x.c != null && x.k > L.k), chg = ins.filter(x => JRS()[x.k].charge).map(x => x.c + 75);
  const lo = Math.max(JRT.lostF != null ? JRT.lostF : (zw.deadAt || 0), ...chg);
  const idx = zw.taps.map((f, i) => i).filter(i => zw.taps[i] > lo && zw.taps[i] < hor - late).sort((a, b) => zw.taps[a] - zw.taps[b]).slice(0, JR_SHINE_USE);
  if (idx.length < JR_SHINE_MIN) return;
  const T = idx.map(i => zw.taps[i]), Fref = Math.floor(T[0] - late - 1), Fend = Math.ceil(T[T.length - 1] + 2);
  // the inputs whose events fall in the stretch, each with its confirm shifts (the outcome: a dodge, as the tracker assumes)
  const near = ins.filter(x => { const e = R.buildEv([{ f: x.c, id: x.id }]); return [...e.keys()].some(f => f >= Fref - 2 && f <= Fend + 2); });
  let combos = [[]]; for (const x of near) { const nx = []; for (const cmb of combos) for (const [sh] of JR_SHIFTS) nx.push(cmb.concat([{ f: x.c + sh, id: x.id }])); combos = nx; if (combos.length > 64) return; }
  const evs = combos.map(cmb => (cmb.length ? R.buildEv(cmb) : new Map()));
  if (evs.some(ev => [...ev.entries()].some(([f, e]) => f >= Fref && f < Fend && e.eio.length))) return;
  // the range of positions: frames since the lock's frame 0, the coin's draws, the modelled draws since (x1.5), a margin
  let D = 0; for (const x of ins) for (const e of R.buildEv([{ f: x.c, id: x.id }]).values()) D += e.pre.length + e.post.length + e.eio.length * 100;
  const nLo = Math.max(0, Fref + Math.floor(Fref / 48) - 20), nHi = Fref + Math.ceil(Fref / 24) + Math.ceil(1.5 * D) + JR_SHINE_MARGIN;
  const groups = new Map(); let s = L.seed >>> 0, tried = 0;
  for (let n = 0; n <= nHi; n++, s = R.adv(s)) {
    if (n < nLo) continue;
    for (let nc0 = Math.floor(T[0] - late); nc0 <= Math.ceil(T[0] + 1.5); nc0++) for (let v = 0; v < evs.length; v++) {
      tried++;
      const S = { s, nc: nc0, inst: [] }, m = []; let j = 0, ok = true;
      for (let f = Fref; f < Fend && ok; f++) {
        const r = R.frameEv(S, f, evs[v]);
        if (r === true) { if (j < T.length && T[j] - f >= -1.5 && T[j] - f <= late) { m.push(idx[j]); j++; } else if (zwVisible(f)) ok = false; }
        if (j < T.length && T[j] < f - 2) ok = false;        // a shine seen that this position does not have
      }
      if (!ok || j < T.length) continue;
      const key = (S.s >>> 0) + ':' + S.nc, G = groups.get(key);
      if (G) G.n++; else groups.set(key, { S, n: 1, pos: n, nc0, v, m });
    }
  }
  // positions a few steps apart explain the same shines (a step more is a coin frame later): one cluster of them is one
  // place in the sequence, carried as the tracker's states (zwPlan beeps only a frame that works for enough of them)
  const G = [...groups.values()].sort((a, b) => a.pos - b.pos), C = [];
  for (const g of G) { const c = C[C.length - 1]; if (c && g.pos - c[c.length - 1].pos <= JR_SHINE_CLUSTER) c.push(g); else C.push([g]); }
  slog('jrShineSearch', { taps: T.length, from: Fref, to: Fend, nLo, nHi, tried, groups: G.length, clusters: C.map(c => c[0].pos + (c.length > 1 ? '..' + c[c.length - 1].pos : '')).slice(0, 6), expectWrong: +(tried * Math.pow(JR_SHINE_P, T.length)).toFixed(3) });
  const E = tried * Math.pow(JR_SHINE_P, T.length);
  if (C.length !== 1 || C[0].length > JR_SHINE_MAXSTATES || E >= JR_SHINE_EMAX) return;
  const mAll = new Set(zw.taps.map((f, i) => i).filter(i => zw.taps[i] < Fend));
  zw.parts = C[0].map(g => { const ev = new Map(); for (const [f, e] of evs[g.v]) if (f >= Fend) ev.set(f, e);
    return { S: { s: g.S.s, nc: g.S.nc, inst: [] }, g: Fend, ev, evMax: Math.max(Fend, ...ev.keys()), pauseAt: null, pause: 0, w: g.n, m: new Set(mAll), fx: new Set(), err: 0 }; });
  let sw = 0; for (const q of zw.parts) sw += q.w;
  const d = Math.max(0.1, E / (1 + E));
  zw.dead = false; zw.deadAt = null; zw.bg = sw * d / (1 - d); zw.bgTo = Fend;      // zwPlan's rules (doubt < 0.5, zwedge) decide the beeps
  const g = C[0][0];
  JRT.recon = null; JRT.lost = null; JRT.lostF = null; JRT.shineRec = { pos: g.pos, n: C[0].length, taps: T.length, at: now, taps0: zw.taps.length };
  // the confirms after the stretch (none, usually: the search runs on the menu after them) go in as live
  for (const x of JRT.inputs.filter(x => x.c != null && x.c >= Fend)) jrApply(x);
  slog('jrShineRecover', { pos: C[0].map(x => x.pos), states: zw.parts.map(q => (q.S.s >>> 0).toString(16) + ':' + q.S.nc), g: Fend, taps: T.length, nLo, nHi, expectWrong: +E.toFixed(3), doubt: +d.toFixed(3) });
  if (typeof chgShow === 'function') chgShow();
}
/* ---------- the Charges ---------- */
// a Charge with the jr profile, once its capture showed Mario in the Charge (the search started; a false trigger or a
// burst with no Mario never gets there): the fight starts on the first one; later ones anchor the count
function jrTick(t) {
  const T = CHG.trig;
  if (T && CHG.prof && (CHG.prof.id === 'jr' || CHG.prof.id === 'nbhw') && ['search', 'locked', 'nolock', 'failed'].includes(CHG.state) && JRT.trigSeen !== T) { JRT.trigSeen = T; jrBurst(T); }
}
function jrBurst(T) {
  const tH = CHG.hideT, tC = tH != null && tH > 0 ? tH : T.t - 13 * FRAME, B = JRT.bar;
  // v86.1: this Charge's own hide, held after a long idle (JR_UPHOLD), counts now
  if (B.held && Math.abs(B.held.t - tC) < 200) { const h = B.held; B.held = null; if (JRT.on && JRT.k < JRS().length) jrHide(h.t, h.up); }
  if (!JRT.on || JRT.k >= JRS().length || (JRT.t0 && T.t - JRT.t0 > 6 * 60000)) { jrNewFight(T, tC); return; }
  const last = JRT.inputs[JRT.inputs.length - 1];
  if (last && JRS()[last.k].charge && Math.abs(last.t - tC) < 200) { JRT.anchor = { k: last.k, t: last.t }; slog('jrChargeBurst', { k: last.k }); return; }    // the hide counted as this Charge
  // the count is off (a missed or an extra hide, a restart): this burst is the Charge that fits the confirms since the last
  // Charge burst best (jrResyncK)
  if (last && Math.abs(last.t - tC) < 200) JRT.inputs.pop();
  const R0 = jrResyncK(tC);
  slog('jrResync', { from: JRT.k, to: R0.k, last: last ? last.k : null, confirms: R0.n, why: R0.why });
  if (R0.k === 0) { jrNewFight(T, tC); return; }
  if (zw.on && zw.fight === 'jr') { zw.on = false; slog('jrCarryEnds', { k: R0.k, why: 'count off' }); }
  JRT.k = R0.k; JRT.anchor = { k: R0.k, t: tC }; jrConfirm(R0.k, tC, 3, 'burst');
}
// the first Charge on a Jr. Troopa step: T1 (a new attempt after a finished, stale or restarted fight, too)
function jrNewFight(T, tC) {
  jrReset(); Object.assign(JRT, { on: true, t0: T.t, seq: jrStepSeq(), trigSeen: T, anchor: { k: 0, t: tC } });
  jrGo(0); jrConfirm(0, tC, 3, 'burst'); slog('jrFight', { at: Math.round(T.t) });
}
/* v86.1: which Charge a burst is when the count is off (v86: the Charge index nearest the count, never back to T1; log
 * 1794269850246: a stale restart and two non-confirm hides put the real T1 Charge at T3, "jrResync from 4 to 4", and the
 * T1 Bomb was planned as T3's Close Call). From the last Charge burst (the anchor: k, t), n confirms were counted before
 * this one: a later Charge c fits with |c - k - 1 - n| confirms off. T1 (a new fight) fits when the bar was gone
 * JR_ENTRY_GAP+ since the anchor (a reset, a battle entry), off by the confirms counted after that gap; ties go to the
 * later Charge. No later Charge on the route: a new fight. */
function jrResyncK(tC) {
  const S = JRS(), A = JRT.anchor || { k: 0, t: JRT.t0 != null ? JRT.t0 : -Infinity };
  const conf = JRT.inputs.filter(x => !x.cancel && x.t > A.t + 200 && x.t < tC - 200), n = conf.length;
  let best = null;
  for (let c = A.k + 1; c < S.length; c++) if (S[c].charge) { const off = Math.abs(c - A.k - 1 - n); if (!best || off < best.off) best = { k: c, off, n, why: 'count' }; }
  const gap = (JRT.bar.gaps || []).filter(g => g.to > A.t && g.to < tC).pop();
  if (gap) { const off = conf.filter(x => x.t > gap.to).length; if (!best || off < best.off) best = { k: 0, off, n, why: 'bar gone ' + Math.round((gap.to - gap.from) / 1000) + ' s: new fight' }; }
  return best || { k: 0, off: 0, n, why: 'no later Charge: new fight' };
}
/* the lock from a Jr. Troopa Charge (chgStartTracker hands it here): start the tracker from it, or, with a carry from an
 * earlier Charge, check the carry against it (the carried states stepped coin-only to this Charge's frame 0, -2..+2) */
function jrLock(seed, qs, qw) {
  if (JRT.trigSeen !== CHG.trig && CHG.trig) { JRT.trigSeen = CHG.trig; jrBurst(CHG.trig); }
  if (!JRT.on) { slog('jrLockIgnored', { why: 'the fight was restarted after this Charge' }); return; }      // v86.1
  const k = JRT.chargeK != null ? JRT.chargeK : 0;
  JRT.lockK = k;
  if (zw.on && zw.fight === 'jr' && !zw.dead && JRT.snap && JRT.snap.k === k) {
    const c = JRT.snap.c, hits = [];
    for (const q of JRT.snap.list) {
      const S = { s: q.S.s, nc: q.S.nc, inst: q.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: q.S.extra ? new Map(q.S.extra) : undefined };
      let g = q.g;
      for (let d = -2; d <= 2; d++) {
        const F0 = c + 13 + d;
        while (g < F0) { if (q.pause && g === q.pauseAt) { S.nc += q.pause; g += q.pause; continue; } R.frameEv(S, g, q.ev); g++; }
        // the seed is the evidence (32 bits); the first coin frame is the carry's: the rays barely tell late coins apart, and
        // the 10 q kept can miss the true one (e2e: T5 lock 0cbf505c with q 31-42 kept, the true q 44)
        if (g === F0 && !S.inst.length && (S.s >>> 0) === (seed >>> 0) && S.nc - F0 >= 0 && S.nc - F0 < 48) hits.push({ d, q: S.nc - F0, w: q.w });
      }
    }
    JRT.cross = { k, agree: hits.length > 0, d: hits.map(h => h.d) };
    slog('jrCrossCheck', { k, agree: hits.length > 0, hits: hits.slice(0, 4), states: JRT.snap.list.length });
    // agreed: go on from the new lock (its frame 0 is exact; the carry's Charge confirm is only known to -2..+1), with the
    // first coin frames the carry agrees on (test_jr_plan.js: T3 from its own lock 85% vs the carry 78% with no coin seen)
    if (hits.length) { jrStartFrom(k, seed, [...new Set(hits.map(h => h.q))], null); return; }
  }
  jrStartFrom(k, seed, qs, qw);
}
function jrStartFrom(k, seed, qs, qw) {
  const old = zw.on && zw.fight === 'jr' ? { t0: zw.t0, rate: zw.rate } : null;
  CHG.jrInner = true; try { chgStartTracker(seed, qs, qw); } finally { CHG.jrInner = false; }
  Object.assign(zw, { fight: 'jr', imps: null, shifts: null, tapLate: 4 });
  // a plan beeping from the old tracker: its frame in the new clock (zwTick checks it against the new states)
  const P = st.plan; if (old && P && P.mix && P.mix.zw && P.zwAbs != null) { P.zwAbs = Math.round(P.zwAbs + (old.t0 - zw.t0) / zw.rate); P.zwKey = null; }
  // v85: this Charge's own confirm is frame -13 of the new clock (the rays' frame 0 = confirm + 13): jrPlanFloor counts from it
  if (JRS() !== JR_SEQ) { const ci = JRT.inputs.filter(x => x.k === k && !x.cancel).pop(); if (ci) ci.c = -13; }     // (Normal Boots only: Ultra Boots unchanged)
  // the confirms since this Charge (the runner may have gone on before the lock landed): in order, in the new clock
  const since = JRT.inputs.filter(x => x.k > k);
  for (const inp of since) jrApply(inp, true);
  JRT.dead = null; JRT.recon = null; JRT.shineRec = null; JRT.lost = null; JRT.lostF = null; JRT.origin = k; JRT.lastLock = { k, seed: seed >>> 0, t0: zw.t0 }; JRT.hist.push({ k, t0: zw.t0, at: performance.now() });   // (the tests map plans by the tracker that made them)
  slog('jrStart', { k, since: since.map(x => x.k), particles: zw.parts.length });
  if (JRT.cancel && !JRT.cancel.done && JRT.cancel.roll) nbCancelPlan('lock');
}
/* v82 (log 1794169121337, the middle fight's T3): the plan from the tracker as soon as its states allow, before the target
 * screen shows. v81 planned only once that screen had been up 0.3 s; the runner confirmed the Bomb 0.4 s after the menu
 * opened, before any plan (it came 175 ms after the bar hid). The plan's frame is never earlier than a plan made on the
 * screen would allow: the previous confirm + the frames until the menu opens (the bar back: Charge 110-113 frames, the
 * T4 Bomb 160-162, both on every fight of that log; after a Close Call the menu after a dodge, JRS() next) + the beep
 * lead + 10. The doubt and edge rules are zwPlan's; a lock that lands later re-scores it (zwTick, "Seed changed"). */
const JR_MENU_CHG = 110, JR_MENU_BOMB = 160;
function jrPlanFloor() {
  if (!(zw.on && zw.fight === 'jr') || JRT.k < 1 || JRT.k >= JRS().length || !jrSeqProf(JRS()[JRT.k])) return null;
  const k = JRT.k, ps = JRS()[k - 1], prev = JRT.inputs.filter(x => x.k === k - 1).pop();
  if (!prev || prev.c == null || !ps) return null;
  const gap = ps.menu ? ps.menu : ps.charge ? JR_MENU_CHG : ps.next ? ps.next : ps.id === 'jr_bomb' ? JR_MENU_BOMB : null;
  return gap == null ? null : prev.c + gap + Math.ceil(earliestPress(0) / zw.rate) + 10;
}
function jrEarlyPlan(t) {
  if (V.wasOn || !jrZw() || JRT.k >= JRS().length || PROF().id !== jrSeqProf(JRS()[JRT.k]) || PROF().lever === 'cancel' || jrPlanFloor() == null) return;   // the screen up: autoPlan as before
  if (st.plan && performance.now() < st.plan.tPress + 600) return;
  if (st.planTry && performance.now() - st.planTry < 500) return;
  st.planEarly = true; try { autoPlan(); } finally { st.planEarly = false; }
}
/* v82: every beeped Jr. Troopa confirm is measured against its plan at the confirm the tracker reads (the bar hiding, or
 * Do Nothing's Strategies screen closing): v81 measured only on a target screen closing, before the route moved, so the
 * T3 Bomb (its screen not watched) and T5 Do Nothing (the step moved before the measure) had none. The tracker's frame is
 * the one the Close Call outcomes have fitted; the target screen read ran ~3 frames later on T4 / T6 in that log. A press
 * more than 5 frames off the beeps (or after the beeps were stopped) is logged but kept out of the press spread. */
function jrPress(inp) {
  const P = st.plan, s = JRS()[inp.k];
  if (!P || !P.mix || !P.mix.zw || P.zwAbs == null || P.measured || !s || !jrSeqProf(s) || PROF().id !== jrSeqProf(s) || !(zw.on && zw.fight === 'jr')) return;
  if (s.cancel && PROF().lever === 'cancel' && !inp.cancel) return;      // v85: Goombario's Charge confirm is not the beeped press (its box A is)
  const rate = zw.rate; if (inp.t - inp.h * rate < (P.tMade || 0)) return;      // the plan came after the press
  const c = zwF(inp.t, inp.h + num('pfix')), f = Math.round(c), err = c - P.zwAbs, onBeeps = Math.abs(err) <= 5 && !P.stopped;
  const d = f - P.zwAbs, inWin = P.target + d >= P.w.start && P.target + d <= P.w.end;
  if (onBeeps) { presses.push(err); while (presses.length > 8) presses.shift(); try { localStorage.setItem('tot-presses', JSON.stringify(presses)); } catch (e) {} }
  V.pressNote = null; P.measured = { frame: f, c, err, inWin, works: inWin, likely: false, tObs: inp.t, onBeeps };
  slog('press', { prof: PROF().id, step: routeStep, err: +err.toFixed(2), inWin, works: inWin, likely: false, near: [], onBeeps, src: inp.src, k: inp.k });
  st.lastPress = Object.assign({ target: P.target, seedBL: P.seedBL, rate: P.rate }, P.measured);
  if (typeof showPresses === 'function') showPresses();
}
/* the fight is over or left: the tracker off (the Hallway's walk tracker can start) */
function jrEnd(why) { if (zw.on && zw.fight === 'jr') zw.on = false; JRT.on = false; slog('jrEnd', { why }); }
/* the route moved: leaving the Jr. Troopa steps ends the fight; a step back by hand (not the page's own) starts it over */
function jrStepChange(was) {
  const W = RT()[was], N = RT()[routeStep];
  if (JRT.stepping) return;
  if (W && W.jr != null && !(N && N.jr != null && (N.seq || 'ultra') === (W.seq || 'ultra'))) { if (JRT.on || (zw.on && zw.fight === 'jr')) jrEnd('left the Jr. Troopa steps'); if (N && N.jr != null) jrReset('another fight'); return; }
  if (N && N.jr != null && JRT.on && N.jr < JRT.k - 1) {
    jrReset('route moved back by hand'); slog('jrRestart', { to: routeStep });
    // v86.1: the Charge watcher ready for the new fight's T1 Charge (the restart keeps the old burst seen: jrReset)
    if (typeof CHG !== 'undefined' && ['locked', 'nolock', 'failed', 'notseen'].includes(CHG.state)) chgReset();
  }
  if (N && N.jr != null && zw.on && zw.fight !== 'jr') { zw.on = false; slog('trackerOffForJr', { from: was }); }
}
/* ---------- what the page says ---------- */
function jrBlindText(prof) {
  if (R.PROFILES[prof] && R.PROFILES[prof].lever === 'cancel') return 'close Goombario\'s box whenever you like: Close Call about ' + Math.round(100 * JR_BLIND.cc) + '%';
  if (R.PROFILES[prof] && R.PROFILES[prof].lever === 'wait') return 'confirm Goombario\'s Charge whenever you like and leave his box: Close Call about ' + Math.round(100 * JR_BLIND.cc) + '%';
  return prof === 'jrpb5' || prof === 'jrpb5n' ? 'Power Bounce whenever you like: 5+ bounces about 67.5%, 6+ about ' + Math.round(100 * JR_BLIND.p6) + '%'
    : 'press whenever you like: Close Call about ' + Math.round(100 * JR_BLIND.cc) + '%';
}
function jrFight() {
  const p = PROF().id, what = jrWhat(JRS().find(s => jrSeqProf(s) === p)) || 'the press';
  const bl = jrBlindText(p);
  return { blind: /^jrpb5n?$/.test(p) ? 'blind 5+ about 67.5%, 6+ about 32%' : 'a blind ' + what + ' dodges 30%', normal: 'Play it blind: ' + bl,
    busy: 'the turn is still being simulated. It plans in a moment; or play it blind (' + bl + ').' };
}
function jrNoLockMsg() {
  const p = PROF().id, s = RT()[routeStep], bl = jrBlindText(p), cs = CHG.state;
  if (jrStepAt10()) return 'No roll this turn: Mario is at 10 HP after the Life Shroom, so Jr. Troopa\'s hit has no Close Call. ' + (jrWhat(JRS()[s.jr]) || 'Press') + ' whenever you like; ' + (JRS() === JR_SEQ ? 'the T5 Charge locks the seed again.' : 'the next Super Charge locks the seed again.');
  if (JRT.recon && !jrReconOk()) return 'No edge yet: the ' + JRS()[JRT.recon.k].t + ' ' + (jrWhat(JRS()[JRT.recon.k]) || 'press') + ' outcome fit none of the carried states, so the page rebuilt them (its confirm read again, -4..+4 frames). No beep until the coin confirms them (' + JR_RECON_TAPS + ' shines on the menu). Play it blind: ' + bl + '.';
  if (JRT.dead) return 'No beeps: ' + JRT.dead + '. Play it blind: ' + bl + '. The next Charge locks again.';
  if (cs === 'capture' || cs === 'maps' || cs === 'search') return 'No beeps yet: the Charge rays are still being read. Stay on the target screen; the beeps start when the seed locks (or play it blind: ' + bl + ').';
  if (cs === 'nolock' || cs === 'failed' || cs === 'notseen') return 'No Charge lock (' + (CHG.why || 'no clear seed') + '): play it blind. ' + bl[0].toUpperCase() + bl.slice(1) + '.';
  if (zw.on && zw.fight === 'jr' && zw.dead) return 'No edge: the seed was lost. Play it blind: ' + bl + '.';
  if (JRS() !== JR_SEQ) return 'No Charge lock: the page did not read a Super Charge in this fight (Mario first: Super Charge on himself, then Goombario). Play it blind: ' + bl + '.';
  return 'No Charge lock: the page did not read a Super Charge in this fight (Mario first on T1, T3 and T5: Super Charge on himself). Play it blind: ' + bl + '.';
}
// the Charge panel's line
function jrStatusLine(s, lost) {
  const P = st.plan, pc = x => Math.round(100 * x) + '%', stp = jrStepNow() && RT()[routeStep];
  const outs = Object.keys(JRT.out).map(k => JRS()[k].t + ' ' + (JRT.out[k] === 'dodge' ? 'dodged' : 'hit (Life Shroom)')).join(', ');
  const head = '<br><b>' + (JRS() === HW_SEQ_NB ? 'Hallway Bowser (Normal Boots)' : JRS() === JR_SEQ_NB ? 'Jr. Troopa (Normal Boots)' : 'Jr. Troopa') + (JRT.on ? ' ' + (JRS()[Math.min(JRT.k, JRS().length - 1)] || {}).t : '') + ':</b> ';
  let body = '';
  if (JRT.dead) body = JRT.dead + '. ';
  if (JRT.lost && zw.dead) body += 'No edge: ' + JRT.lost + ' (until the next Charge locks, or the coin finds the seed again). ';
  if (JRT.shineRec && !zw.dead) body += 'seed found again from ' + JRT.shineRec.taps + ' shines. ';
  if (JRT.cross) body += 'the ' + JRS()[JRT.cross.k].t + ' Charge ' + (JRT.cross.agree ? 'confirmed the carried seed. ' : 'did not fit the carry: tracking from its lock. ');
  if (P && P.mix && stp && PROF().group === 'jr') body += (/^jrpb5n?$/.test(PROF().id) ? 'Power Bounce on the beep: ' + ppText(P.mix, PROF().id) + ' (blind 67.5% / ' + pc(JR_BLIND.p6) + '; with your press spread 5+ ' + pc(P.mix.p) + ', 6+ ' + pc(P.mix.p4 || 0) + ')' : jrWhat(JRS()[stp.jr]) + ' on the beep: Close Call. ' + ppText(P.mix, PROF().id) + ' (blind ' + pc(JR_BLIND.cc) + '; with your press spread ' + pc(P.mix.p) + ')');
  else if ((s === 'nolock' || s === 'failed' || s === 'notseen' || lost) && !(zw.on && zw.fight === 'jr' && !zw.dead)) body += 'play it blind (Close Call ' + pc(JR_BLIND.cc) + '; Power Bounce 5+ 67.5%, 6+ ' + pc(JR_BLIND.p6) + ').';
  else if (zw.on && zw.fight === 'jr') body += 'carried from the ' + JRS()[JRT.origin || 0].t + ' Charge; the beeps start on each Close Call / Power Bounce target screen.';
  return head + body + (outs ? ' <span class="note">(' + outs + ')</span>' : '');
}
/* for tests: the plan if the step's target screen showed on clock frame cScr (zwChoose over the tracker's states, the
 * 25/50/25 press spread), the states, the outcome classes per frame, and a tracker started as a lock starts it */
function jrPlanAt(cScr, leadS, winS, profId) {
  if (zw.visFrom != null && !zw.visLocked) zw.visTo = cScr - 4;
  const S = zwStatesAt(cScr);
  if (!S.list.length) return { none: 'nothing fits', states: 0 };
  const prof = R.PROFILES[profId || PROF().id], from = Math.ceil(cScr + leadS * 1000 / zw.rate + 1), W = Math.max(0, Math.round(winS * 1000 / zw.rate));
  const top = R.TOP[prof.id], C = zwChoose(S.list, from, W, PRESS_ERR, prof, { d: S.doubt, b3: jrBlind(prof.id), b4: top ? jrBlind(top) : 0 });
  return { target: C.target, p: C.p, p6: C.p4, pp: C.pp, pp6: C.pp4, w4: C.w4, pStates: C.pStates, doubt: S.doubt, w: C.w, none: C.none, from, W, states: S.list.map(q => ({ s: q.s >>> 0, nc: q.nc, g: q.g, w: q.w })) };
}
const jrBlind = id => (/^jrpb5n?$/.test(id) ? JR_BLIND.p5 : /^jrpb6n?$/.test(id) ? JR_BLIND.p6 : JR_BLIND.cc);
