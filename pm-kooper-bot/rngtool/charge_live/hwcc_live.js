//@ Hallway Bowser T1 at 3 HP: the Spiny Flip's throw beeped so that Bowser's attack misses (Close Call). charge_live/README.md
//@ v78. Inlined into page_template.html after fb14_live.js by shared/inline.py (//@ lines are dropped). Needs the page globals
//@ (R, FRAME, $, num, slog, st, zw, V, isRoute, RT, routeStep, setStep, render, PROF, zwF, zwClone, zwMerge, zwChoose, zwDoubt,
//@ earliestFrame, pressTime, pressDist, PRESS_ERR, playBeeps, cancelBeeps, nBeeps, ZW_BLIND, ZW_MAXP) and jr_live.js (jrTens,
//@ JR_TENS_MIN, JRT.bar).
/* ---------- Hallway Bowser T1 at 3 HP: the Spiny Flip throw → Close Call ----------
 * The runner comes into the Hallway at 3 HP (Danger), so every attack of Bowser's first turn rolls Close Call first
 * (rand_int(100) < 30, caller 0x80277518; 1A5830.c: only under 6 HP). A hit kills Mario (5+ damage), so the route needs the
 * Lucky roll. Emulator (fixtures/hw3_logs.json, test_hw_cc_model.js; 17 runs at 3 HP, 7 with the Spiny on Bowser): from the
 * Charge to the roll nothing else changes at 3 HP (no Danger idle draws); Lakilester's Spiny Flip is thrown with A
 * (lakilester.c SpinyFlipActionCommand: A ends the aim, else the 80-frame timer), the impact's 8 x rand(359) come on throw
 * + 24 (JumpPartTo 20 + Wait 3), Bowser's AI on throw + 68 and the roll on AI + 54 / 70 / 55 (Body Slam / Claw Swipe / Fire
 * Breath). After a Lucky roll nothing more is drawn to T2's menu. So the roll is decided by the throw's frame, which the
 * runner presses: the lever. The guard comes after the roll and changes nothing. The impact frame the page could not see
 * before (33 frames held, 136 thrown with A) is now the throw read off the video: the aim popup ("stick で … をねらおう!")
 * vanishes on the throw's own frame (Glide64: 2 frames before the target menus' name box does after its confirm).
 *
 * The page: at the Spiny Flip confirm the tracker's particles take the aim sparkle and wait before the earliest impact
 * (zwStep hold); on the aim popup (target screen 'A') hwccPlan simulates, for every throw frame in the window, each state's
 * roll, and beeps the best frame with the Hallway's machinery (zwChoose, press spread, doubt, blind 30 / 101); the popup
 * closing is the throw (+-2 frames, HWCC_SHIFTS): the impact and Bowser's turn go in on that frame, and the states whose
 * roll hits are dropped (the background is weighed by a blind Close Call once they have all rolled: zwUpdate). Time Out
 * on T2 then plans from the Lucky states alone. No throw read (popup not saved, missed): the impact frames stay open as
 * before (HWCC_FALL). Mario's HP: read from the status bar's tens place in T1 (jrTens): a "1" = 10 HP, no Close Call,
 * the 10-HP model and no beep; blank = Danger (the route's 3 HP; also assumed when the bar was not read). After the throw,
 * a "1" on the bar = Mario died and a Life Shroom revived him at 10 HP: the revive's RNG is not modelled, so the tracker
 * stops and Time Out says no edge. */
const HWCC_WIN = [55, 114];      // throw frames beeped, after the Spiny Flip confirm: the reticle needs ~12-15 frames to reach
                                 // Bowser from the aim's start (confirm + 39 at the earliest); the 80-frame timer ends at + 119 at the earliest
const HWCC_HOLD = 58;            // the particles wait here until the throw is read (the earliest A-throw impact: confirm + 64)
const HWCC_IMPMIN = 60;          // no throw read: the impact frames left open (CHG_IMPS from here)
const HWCC_VAN = 0;              // the aim popup vanishes on the throw's frame (emulator); console: not measured
const HWCC_SHIFTS = [[-2, 0.1], [-1, 0.25], [0, 0.4], [1, 0.2], [2, 0.05]];   // the throw read off the video (as FB14_SHIFTS)
const HWCC_FALL = 200;           // frames after the confirm with no throw read: the impact frames go in open
const HWCC_NS = 64;              // states the plan simulates (the heaviest)
const HWCC = {};
function hwccReset() { Object.assign(HWCC, { held: false, resolved: false, pendT: null, c: null, imps: null, danger: null, T: null, died: false, dieN: 0, tens: [], stepAt: null, barSince: null, plan: null }); }
hwccReset();
var HWCC_READY = true;     // (var: charge_live.js's chgShow runs at load, before this file's consts exist)
const hwccStep = () => (isRoute() && RT()[routeStep] && RT()[routeStep].turn === 'hw_throw' ? RT()[routeStep] : null);
const hwccRoute = () => isRoute() && RT().some(x => x.turn === 'hw_throw');
const HWCC_BLIND_TXT = 'throw whenever you like (Close Call about 30%)';
// Mario's HP from the T1 bar: 10 HP shows the tens "1" (JR_TENS_MIN), 3 HP leaves it blank; not read: the route's 3 HP
function hwccDanger() {
  const T = HWCC.tens; if (T.length < 5) return { danger: true, read: false };
  const k = T.filter(v => v >= JR_TENS_MIN).length; return { danger: k * 2 < T.length, read: true, share10: +(k / T.length).toFixed(2) };
}
/* zwInput, at the Spiny Flip confirm on clock frame c: hold the impact for the throw (true), or split it as before (false) */
function hwccDefer(c, imps) {
  if (!hwccRoute()) return false;
  const d = hwccDanger();
  Object.assign(HWCC, { held: true, c, imps, danger: d.danger, T: null, resolved: false, died: false, dieN: 0, plan: null });
  slog('hwccHold', { c, danger: d.danger, hpRead: d.read, share10: d.share10, tensN: HWCC.tens.length });
  return true;
}
/* the impact and Bowser's turn into every held particle: from the throw read on clock frame T (+-2), or (T null) every
 * impact frame left open (no throw seen) */
function hwccResolve(T, why) {
  if (!HWCC.held) return;
  HWCC.held = false; HWCC.T = T; HWCC.resolved = true;
  if (!zw.on) return;
  const dg = !!HWCC.danger, out = [], imps = (HWCC.imps || []).filter(i => i >= HWCC_IMPMIN);
  for (const p of zw.parts) {
    if (p.hold == null) { out.push(p); continue; }
    const c0 = HWCC.c + (p.sh || 0), opts = T != null ? HWCC_SHIFTS.map(([d, w]) => [T + d, w]) : imps.map(i => [c0 + i - 24, 1 / imps.length]);
    for (const [Tq, wq] of opts) {
      if (Tq + 24 < p.g) continue;                       // an impact before where the particle already is: not possible
      for (const gd of dg ? [false] : [true, false]) {
        const q = zwClone(p); q.hold = null; q.w = p.w * wq / (dg ? 1 : 2);
        zwMerge(q.ev, R.buildEv([{ f: Tq, id: 'hw_throw', imp: 24, guard: gd, danger: dg }])); q.evMax = Math.max(q.evMax, Tq + 24 + 45); out.push(q);
      }
    }
  }
  zw.parts = out; if (dg) { zw.ccPend = true; zw.ccHitW = 0; }
  if (zw.parts.length > ZW_MAXP) { slog('zwTooMany', { n: zw.parts.length }); zw.parts = []; zw.dead = true; }
  slog('hwccThrow', { T, why, danger: dg, particles: zw.parts.length, planned: st.plan && st.plan.mix && st.plan.mix.hwcc ? st.plan.zwAbs : null });
}
/* the aim popup closed (checkPress on the throw step): the throw's frame */
function hwccThrow(tObs) {
  if (!HWCC.held || !zw.on) { if (!HWCC.resolved) HWCC.pendT = tObs; slog('hwccThrowSeen', { at: Math.round(tObs), held: HWCC.held, zw: zw.on }); return; }   // before the lock: applied when it lands (hwccAfterLock)
  const c = zwF(tObs, HWCC_VAN + num('pfix')), T = Math.round(c), P = st.plan && st.plan.mix && st.plan.mix.hwcc ? st.plan : null;
  if (P) slog('hwccPress', { T, c: +c.toFixed(2), planned: P.zwAbs, err: +(c - P.zwAbs).toFixed(2) });
  hwccResolve(T, 'popup');
}
/* a lock that landed after the throw was seen (chgStartTracker, after the held Spiny Flip confirm): the throw goes in now */
function hwccAfterLock() { if (HWCC.held && HWCC.pendT != null) { const t = HWCC.pendT; HWCC.pendT = null; hwccThrow(t); } }
/* every video frame (onFrame): Mario's HP in T1, the fallback when no throw is read, the death watch after it */
function hwccFrame(t, present) {
  if (!isRoute()) return;
  const s = RT()[routeStep] || {}, B = typeof JRT !== 'undefined' ? JRT.bar : null, steady = present && B && B.since && t - B.since > 5 * FRAME;
  if (s.turn === 'hw_spiny' && steady) { HWCC.tens.push(jrTens()); if (HWCC.tens.length > 40) HWCC.tens.shift(); }
  if (s.turn === 'hw_throw') {
    if (HWCC.stepAt == null) HWCC.stepAt = t;
    HWCC.barSince = present ? HWCC.barSince || t : null;
    // the bar is hidden through Lakilester's whole action: back for half a second (Bowser's turn) = the throw is long past
    // (its popup not saved, or not seen): the route goes on to Time Out
    if (HWCC.barSince && t - HWCC.stepAt > 1500 && t - HWCC.barSince > 500) { slog('hwccStepByBar', { step: routeStep }); setStep(routeStep + 1); }
  }
  if (HWCC.held && zw.on && (!/^Hallway Bowser/.test(s.t || '') || (s.turn !== 'hw_throw' && s.turn !== 'hw_spiny') || zwF(t, 0) > HWCC.c + HWCC_FALL)) hwccResolve(null, 'no throw seen');
  if (HWCC.resolved && HWCC.danger && !HWCC.died && steady && zw.on && /^Hallway Bowser/.test(s.t || '') && zwF(t, 0) > HWCC.c + 100) {
    HWCC.dieN = jrTens() >= JR_TENS_MIN ? HWCC.dieN + 1 : 0;
    if (HWCC.dieN >= 6) {
      HWCC.died = true; zw.on = false; cancelBeeps(); st.plan = null;
      slog('hwccDied', { at: Math.round(t) });
      st.msg = 'Mario was hit (10 HP on the bar: a Life Shroom). The page does not follow the revive\'s random numbers: no Time Out beep this attempt, press it normally (31%).'; render();
    }
  }
}
function hwccStepChange() {
  HWCC.stepAt = null; HWCC.barSince = null; const s = isRoute() && RT()[routeStep];
  if (HWCC.held && !(s && (s.turn === 'hw_throw' || s.turn === 'hw_spiny'))) hwccResolve(null, 'step left before a throw was read'); if (s && s.turn === 'hw_spiny' && !HWCC.held) { HWCC.tens = []; HWCC.pendT = null; HWCC.resolved = false; HWCC.died = false; } }
/* share[F - a] = the weighted share of the held states whose Close Call rolls Lucky with the throw on clock frame F */
function hwccShare(L, a, b) {
  const sh = new Float64Array(Math.max(0, b - a + 1)), tot = L.reduce((x, p) => x + p.w, 0) || 1, dg = !!HWCC.danger;
  for (const p of L) {
    const S0 = { s: p.S.s, nc: p.S.nc, inst: p.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: p.S.extra ? new Map(p.S.extra) : undefined };
    // the throw only shows from its impact (F + 24) on, so the state where the particle is (p.g, at most the hold) serves
    // every throw frame F >= p.g - 24
    let cur = p.g; const wt = p.w / tot;
    for (let F = a; F <= b; F++) {
      while (cur < F) { R.frameEv(S0, cur, p.ev); cur++; }
      const imp = { pre: Array(8).fill(359), post: [], eio: [] }, ai = { pre: [], post: [], eio: [], ai: 'hw_throw', guard: false, danger: dg };
      const ev = { get: f => (f === F + 24 ? imp : f === F + 68 ? ai : p.ev.get(f)) };
      const S = { s: S0.s, nc: S0.nc, inst: S0.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: S0.extra ? new Map(S0.extra) : undefined };
      for (let f = cur; f < F + 68 + 80 && !S.cc; f++) R.frameEv(S, f, ev);
      if (S.cc && S.cc.lucky) sh[F - a] += wt;
    }
  }
  return sh;
}
/* the throw plan, on the aim popup (cAt: tests, as if the popup showed on clock frame cAt; no beeps) */
function hwccPlan(cAt) {
  if (!hwccStep()) return false;
  const done = (msg, pl) => { HWCC.plan = pl; if (cAt != null) return pl; st.msg = msg; if (pl.none) { slog('hwccNoEdge', pl); cancelBeeps(); } if (typeof chgShow === 'function') chgShow(); render(); return true; };
  if (HWCC.danger === false) return done('Mario has 10 HP: Bowser\'s attack rolls no Close Call this turn. Throw whenever you like.', { none: '10 HP' });
  if (!zw.on && typeof CHG !== 'undefined' && ['capture', 'maps', 'search'].includes(CHG.state)) return done('No beeps yet: the Charge rays are still being read. Keep the reticle on Bowser: the beeps come if the lock lands in time; else ' + HWCC_BLIND_TXT + '.', { none: 'searching' });
  if (!zw.on || zw.dead) return done('No Charge lock for the Close Call: ' + HWCC_BLIND_TXT + '.', { none: 'no lock' });
  if (!HWCC.held) return done('No edge: the page did not see the Spiny Flip confirm (or already read the throw): ' + HWCC_BLIND_TXT + '.', { none: 'no confirm' });
  const doubt = zwDoubt();
  if (doubt >= 0.5) return done('No edge: the coin no longer fits the Charge lock (' + Math.round(doubt * 100) + '% that none of the tracked states is the game\'s): ' + HWCC_BLIND_TXT + '.', { none: 'doubt', doubt });
  const rate = zw.rate, now = performance.now(), W0 = Math.max(0, Math.round(num('zwwin') * 1000 / rate));
  const from = Math.max(HWCC.c + HWCC_WIN[0], cAt != null ? Math.ceil(cAt + num('lead') * 1000 / rate + 1) : earliestFrame(zw.t0, rate, now)), to = Math.min(HWCC.c + HWCC_WIN[1], from + W0);
  if (to < from) return done('No edge: too late for the beeps before the aim runs out (the lock came late): ' + HWCC_BLIND_TXT + '.', { none: 'late' });
  const L = zw.parts.filter(p => p.hold != null).sort((x, y) => y.w - x.w).slice(0, HWCC_NS);
  if (!L.length) return done('No edge: no state to plan with: ' + HWCC_BLIND_TXT + '.', { none: 'no states' });
  const PD = cAt != null ? PRESS_ERR : pressDist(), D = Math.max(...PD.map(x => Math.abs(x[0]))), X = 10, a0 = from - D, b0 = to + X + D;
  const t1 = performance.now(), share = hwccShare(L, a0, b0), ms = Math.round(performance.now() - t1);
  const prof = { id: 'hwcc', share: (a, b) => share.slice(a - a0, b - a0 + 1) };
  const C = zwChoose(L, from, to - from, PD, prof, { d: doubt, b3: ZW_BLIND.hwcc, b4: 0 });
  if (C.none) return done('No edge: no throw frame before the aim runs out works for enough of the ' + L.length + ' states (best ' + Math.round(100 * (C.p || 0)) + '%): ' + HWCC_BLIND_TXT + '.', { none: C.none, best: C.p });
  const pl = { target: C.target, p: C.p, pStates: C.pStates, doubt: +doubt.toFixed(3), states: L.length, ms, from, to, w: C.w, tPress: pressTime(zw.t0, rate, C.target) };
  HWCC.plan = pl; if (cAt != null) return pl;
  cancelBeeps(); playBeeps(pl.tPress);
  const first = from - 30, tab = []; for (let F = first; F <= to + 30; F++) tab.push(F >= a0 && F <= b0 ? share[F - a0] >= 0.5 : false);
  st.plan = { tMade: now, w: C.w, target: C.target, tPress: pl.tPress, tLast: zw.t0, rate, carried: true, from, to, first, prof: 'hwcc', tab, tab4: null, type: C.type, beeps: nBeeps(),
    mix: { p: C.p, pStates: C.pStates, doubt: pl.doubt, groups: L.length, zw: true, hwcc: true }, PD, zwAbs: C.target };
  st.msg = null; slog('hwccPlan', pl); if (typeof chgShow === 'function') chgShow(); render(); return true;
}
/* the Charge panel's line for this lever */
function hwccStatusLine() {
  const s = hwccStep(), P = st.plan && st.plan.mix && st.plan.mix.hwcc ? st.plan : null, pc = x => Math.round(100 * x) + '%';
  if (HWCC.died) return '<br><b>Hallway T1:</b> Mario was hit (Life Shroom): no Time Out beep this attempt.';
  if (!s) return HWCC.T != null && HWCC.danger ? '<br>Hallway T1: throw read; Time Out plans from the Close Call states.' : '';
  if (P) return '<br><b>Throw (A) on the beep:</b> Close Call ' + pc(P.mix.p) + ' (blind 30%)';
  if (HWCC.plan && HWCC.plan.none) return '<br>Hallway T1: no edge for the throw: ' + HWCC_BLIND_TXT + '.';
  return '<br>Hallway T1: aim at once and keep the reticle on Bowser; the beeps start on the aim popup.';
}
