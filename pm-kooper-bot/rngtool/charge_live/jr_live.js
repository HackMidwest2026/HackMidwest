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
 * (or the bar hiding when Jr. Troopa's turn starts, JR_SEQ). The page counts the hides after a menu (bar up 0.3 s+) in
 * route order (JR_SEQ), each one an input to the tracker with its frame -2..+1 (JR_SHIFTS: the coin settles them). The
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
  { id: 'jr_whacka', t: 'T2', hide: 3 },
  { id: 'jr_charge', t: 'T3', charge: true, hide: 3 },
  { id: 'jr_bomb_cc', t: 'T3', hide: 4, prof: 'jrcc_bomb', cc: 179, next: 246, what: 'Bomb' },
  { id: 'jr_bomb', t: 'T4', hide: 4 },
  { id: 'jr_syrup_cc', t: 'T4', hide: 3, prof: 'jrcc_syrup', cc: 163, hit: 'jr_syrup_hit', next: 230, what: 'Maple Syrup' },
  { id: 'jr_charge', t: 'T5', charge: true, hide: 3 },
  { id: 'jr_nothing_cc', t: 'T5', hide: 3, prof: 'jrcc_nothing', cc: 26, hit: 'jr_nothing_hit', next: 93, what: 'Do Nothing', strat: true },
  { id: 'jr_pb', t: 'T6', hide: 3, prof: 'jrpb5', what: 'Power Bounce' } ];
const JR_DEATH = 359;          // frames a death and the Life Shroom revive add before the next menu (emulator: every run)
// a confirm read from the bar hiding: -2..+1 frames, as the Spiny Flip's (CHG_SHIFTS): a dropped picture only ever reads it
// late (the frame-fed end to end under load read the T3 Bomb 2 frames late and the T3 Charge 1-2 late)
const JR_SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];
const JR_UPMIN = 300;          // ms of bar up before a hide counts as a confirm (Whacka can follow the Bomb quickly)
/* blind odds (jr_charge/README.md, jc_odds.py): Close Call 30%; Power Bounce 5+ 67.5%, 6+ 32.2% */
const JR_BLIND = { cc: 0.30, p5: 0.675, p6: 0.322 };
const JRT = { bar: {} };
function jrReset(why) {
  Object.assign(JRT, { on: false, k: 0, inputs: [], dead: null, hp10: {}, out: {}, ccPend: null, snap: null, lockK: null, cross: null, t0: null, trigSeen: null, hides: [], hist: [], why: why || null });
  if (zw.on && zw.fight === 'jr') zw.on = false;
}
jrReset();
var JR_READY = true;     // (var: charge_live.js's chgShow runs at load, before this file's consts exist)
const jrStepNow = () => isRoute() && !!RT()[routeStep] && RT()[routeStep].jr != null;
const jrZw = () => zw.on && zw.fight === 'jr' && jrStepNow() && PROF().group === 'jr' && !jrStepAt10();
/* the route step for the next confirm k: the first Jr. Troopa step whose confirm is k or later (past the last: the step
 * after the fight) */
function jrStepFor(k) {
  const L = RT(); let last = -1;
  for (let i = 0; i < L.length; i++) if (L[i].jr != null) { if (L[i].jr >= k) return i; last = i; }
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
    if (B.gone && t - B.since >= 3 * FRAME) { if (!B.done) B.upFrom = B.prevUp; B.gone = 0; }
    if (!B.gone && !B.upFrom) B.upFrom = B.since;
  } else {
    if (B.since && !B.gone) { B.gone = t; B.prevUp = B.upFrom; B.wasUp = B.upFrom ? t - B.upFrom : 0; B.upFrom = 0; B.done = false; }
    B.since = 0;
    if (B.gone && !B.done && t - B.gone >= 8 * FRAME) { B.done = true; if (B.wasUp >= JR_UPMIN) jrHide(B.gone, B.wasUp); }
  }
  jrOutcomeWatch(t, present);
  jrTick(t);
}
/* Mario's HP tens place in the status bar (320-space x 61..67, y 27..36: blank at 2 HP, the "1" of 10 after a revive;
 * emulator renders, jr_charge/README.md): the share of white glyph pixels there */
const JR_TENS = [61, 27, 67, 36];
function jrTens() {
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
  if (fr > JR_SEQ[P.k].next + JR_DEATH + 60) jrSettle('time');
}
function jrSettle(by) {
  const P = JRT.ccPend; if (!P) return; JRT.ccPend = null;
  slog('jrOutcome', { k: P.k, dodge: true, by, tensMax: +(P.max || 0).toFixed(2) }); jrDodge(P.k);
}
/* a confirm read from the bar hiding (or, for Do Nothing, from the Strategies screen closing: jrScreenClosed) */
function jrHide(tH, upMs) {
  JRT.hides.push(tH); if (JRT.hides.length > 8) JRT.hides.shift();
  if (!jrStepNow() || !JRT.on) return;                 // before the fight: the T1 Charge's burst starts it (jrBurst)
  if (JRT.k >= JR_SEQ.length) return;
  const s = JR_SEQ[JRT.k];
  if (s.strat && JRT.stratAt != null && Math.abs(tH - JRT.stratAt) < 2000) { slog('jrHideAfterNothing', { at: Math.round(tH) }); return; }   // Do Nothing was read from its screen
  slog('jrHide', { k: JRT.k, id: s.id, at: Math.round(tH), upMs: Math.round(upMs) });
  jrConfirm(JRT.k, tH, s.hide, 'bar');
}
/* Bombette's Do Nothing on its Strategies screen (cat S): the screen closing is the confirm (3 frames, VAN.S) */
function jrScreenClosed(tObs) {
  if (!jrStepNow() || !JRT.on || JRT.k >= JR_SEQ.length) return false;
  const s = JR_SEQ[JRT.k]; if (!s.strat) return false;
  JRT.stratAt = tObs; slog('jrStrategiesClosed', { k: JRT.k, at: Math.round(tObs) });
  jrConfirm(JRT.k, tObs, R.PROFILES.jrcc_nothing.vanish, 'screen'); return true;
}
function jrConfirm(k, t, h, src) {
  if (JRT.ccPend && JRT.ccPend.k < k) jrSettle('next confirm');
  const s = JR_SEQ[k]; let id = s.id; if (s.hit && JRT.hp10[k]) id = s.hit;
  const inp = { k, id, t, h, src }; JRT.inputs.push(inp);
  if (s.charge) JRT.chargeK = k;
  if (zw.on && zw.fight === 'jr') jrApply(inp);
  if (s.cc && id === s.id) JRT.ccPend = { k, t: t - h * jrRate() };
  // the Charge watcher arms again for the next Charge (its lock is in the tracker already)
  if ((k === 3 || k === 7) && ['locked', 'nolock', 'failed', 'notseen'].includes(CHG.state)) chgReset();
  jrGo(k + 1);
  if (k === JR_SEQ.length - 1) jrEnd('the fight is over (Power Bounce confirmed)');
}
const jrRate = () => (zw.on && zw.fight === 'jr' ? zw.rate : chgRate());
/* a dodge seen: the states whose roll hits are ruled out (likelihood 0), and the background ("none of the tracked states is
 * the game's", zwDoubt) is weighed by the chance a blind press dodges (likelihood 0.30), as v72 weighs the coin */
function jrDodge(k) {
  JRT.out[k] = 'dodge';
  if (!(zw.on && zw.fight === 'jr')) return;
  let gone = 0; const keep = [];
  for (const p of zw.parts) { if (p.cc && p.cc[k] === false) gone += p.w; else keep.push(p); }
  if (keep.length) { zw.parts = keep; zw.bg = (zw.bg || 0) * JR_BLIND.cc; }
  else { zw.parts = []; zw.dead = true; zw.deadAt = null; }
  slog('jrDodge', { k, dropped: +gone.toFixed(4), left: zw.parts.length });
}
function jrDeath(k, fr) {
  JRT.out[k] = 'death';
  // the next turn's Close Call turn is at 10 HP (the revive): no roll there, its 10-HP draws instead
  if (k === 5) JRT.hp10[7] = true; else if (k === 7) JRT.hp10[9] = true;
  JRT.dead = JR_SEQ[k].t + ': Mario was hit (10 HP after the Life Shroom, read ' + fr + ' frames after the confirm): the revive breaks the carry';
  if (zw.on && zw.fight === 'jr') { zw.on = false; slog('jrCarryEnds', { k, why: 'death' }); }
  if (typeof chgShow === 'function') chgShow(); render();
}
/* an input in the tracker: like zwInput, with the confirm frame -2..+1 (JR_SHIFTS) and, on a Close Call confirm, whether
 * each state's roll dodges (p.cc[k]), so the outcome seen later can drop the ones that would have died */
function jrApply(inp) {
  const s = JR_SEQ[inp.k], c = Math.round(zwF(inp.t, inp.h + num('pfix')));
  inp.c = c;
  zwSeen(performance.now());
  if (zw.visFrom != null && (zw.visTo == null || zw.visTo < c - 4)) zw.visTo = c - 4;
  zw.visLocked = true;
  zwUpdate(Math.min(c - 3, zwHorizon(performance.now())));
  if (s.charge) JRT.snap = { k: inp.k, c, list: zw.parts.slice(0, 400).map(zwClone) };      // the carried states before this Charge (jrLock checks its lock on them)
  const out = [], cc = s.cc && inp.id === s.id;
  for (const p of zw.parts) for (const [sh, ws] of JR_SHIFTS) {
    const q = zwClone(p); q.w = p.w * ws; q.cc = p.cc ? Object.assign({}, p.cc) : null;
    const ev = R.buildEv([{ f: c + sh, id: inp.id }]);
    zwMerge(q.ev, ev); q.evMax = Math.max(q.evMax, ...ev.keys(), ...[...ev.values()].flatMap(e => e.eio.map(x => x[0])));
    if (cc) (q.cc = q.cc || {})[inp.k] = jrRollOk(q, c + sh + s.cc);
    out.push(q);
  }
  zw.parts = out;
  if (zw.parts.length > ZW_MAXP) { slog('zwTooMany', { n: zw.parts.length }); zw.parts = []; zw.dead = true; }
  else zwBgAdd(ZW_BGIN);
  slog('jrInput', { k: inp.k, id: inp.id, c, src: inp.src, particles: zw.parts.length });
}
// does this state's Close Call roll (the first draw on frame f) dodge? (simulated on a copy, the particle's clock)
function jrRollOk(q, f) {
  const S = { s: q.S.s, nc: q.S.nc, inst: q.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: q.S.extra ? new Map(q.S.extra) : undefined };
  let g = q.g;
  while (g < f) { if (q.pause && g === q.pauseAt) { S.nc += q.pause; g += q.pause; continue; } R.frameEv(S, g, q.ev); g++; }
  return R.randInt(S.s, 100)[1] < 30;
}
/* ---------- the Charges ---------- */
// a Charge with the jr profile, once its capture showed Mario in the Charge (the search started; a false trigger or a
// burst with no Mario never gets there): the fight starts on the first one; later ones anchor the count
function jrTick(t) {
  const T = CHG.trig;
  if (T && CHG.prof && CHG.prof.id === 'jr' && ['search', 'locked', 'nolock', 'failed'].includes(CHG.state) && JRT.trigSeen !== T) { JRT.trigSeen = T; jrBurst(T); }
}
function jrBurst(T) {
  const tH = CHG.hideT;
  if (!JRT.on || JRT.k >= JR_SEQ.length || (JRT.t0 && T.t - JRT.t0 > 6 * 60000)) {
    // the first Charge on a Jr. Troopa step: T1 (a new attempt after a finished or stale fight, too)
    jrReset(); Object.assign(JRT, { on: true, t0: T.t });
    jrGo(0); jrConfirm(0, tH != null && tH > 0 ? tH : T.t - 13 * FRAME, 3, 'burst'); slog('jrFight', { at: Math.round(T.t) }); return;
  }
  const last = JRT.inputs[JRT.inputs.length - 1];
  if (last && JR_SEQ[last.k].charge && Math.abs(last.t - tH) < 200) { slog('jrChargeBurst', { k: last.k }); return; }    // the hide counted as this Charge
  // the count is off (a missed or an extra hide): this burst is the Charge nearest to where the count is
  const k = [4, 8].reduce((a, b) => (Math.abs(b - JRT.k) < Math.abs(a - JRT.k) ? b : a));
  slog('jrResync', { from: JRT.k, to: k, last: last ? last.k : null });
  if (last && last.t === tH) JRT.inputs.pop();
  if (zw.on && zw.fight === 'jr') { zw.on = false; slog('jrCarryEnds', { k, why: 'count off' }); }
  JRT.k = k; jrConfirm(k, tH != null && tH > 0 ? tH : T.t - 13 * FRAME, 3, 'burst');
}
/* the lock from a Jr. Troopa Charge (chgStartTracker hands it here): start the tracker from it, or, with a carry from an
 * earlier Charge, check the carry against it (the carried states stepped coin-only to this Charge's frame 0, -2..+2) */
function jrLock(seed, qs, qw) {
  if (JRT.trigSeen !== CHG.trig && CHG.trig) { JRT.trigSeen = CHG.trig; jrBurst(CHG.trig); }
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
  // the confirms since this Charge (the runner may have gone on before the lock landed): in order, in the new clock
  const since = JRT.inputs.filter(x => x.k > k);
  for (const inp of since) jrApply(inp);
  JRT.dead = null; JRT.origin = k; JRT.hist.push({ k, t0: zw.t0, at: performance.now() });   // (the tests map plans by the tracker that made them)
  slog('jrStart', { k, since: since.map(x => x.k), particles: zw.parts.length });
}
/* the fight is over or left: the tracker off (the Hallway's walk tracker can start) */
function jrEnd(why) { if (zw.on && zw.fight === 'jr') zw.on = false; JRT.on = false; slog('jrEnd', { why }); }
/* the route moved: leaving the Jr. Troopa steps ends the fight; a step back by hand (not the page's own) starts it over */
function jrStepChange(was) {
  const W = RT()[was], N = RT()[routeStep];
  if (JRT.stepping) return;
  if (W && W.jr != null && !(N && N.jr != null)) { if (JRT.on || (zw.on && zw.fight === 'jr')) jrEnd('left the Jr. Troopa steps'); return; }
  if (N && N.jr != null && JRT.on && N.jr < JRT.k - 1) { jrReset('route moved back by hand'); slog('jrRestart', { to: routeStep }); }
  if (N && N.jr != null && zw.on && zw.fight !== 'jr') { zw.on = false; slog('trackerOffForJr', { from: was }); }
}
/* ---------- what the page says ---------- */
function jrBlindText(prof) {
  return prof === 'jrpb5' ? 'Power Bounce whenever you like: 5+ bounces about 67.5%, 6+ about ' + Math.round(100 * JR_BLIND.p6) + '%'
    : 'press whenever you like: Close Call about ' + Math.round(100 * JR_BLIND.cc) + '%';
}
function jrFight() {
  const p = PROF().id, what = (JR_SEQ.find(s => s.prof === p) || {}).what || 'the press';
  const bl = jrBlindText(p);
  return { blind: p === 'jrpb5' ? 'blind 5+ about 67.5%, 6+ about 32%' : 'a blind ' + what + ' dodges 30%', normal: 'Play it blind: ' + bl,
    busy: 'the turn is still being simulated. It plans in a moment; or play it blind (' + bl + ').' };
}
function jrNoLockMsg() {
  const p = PROF().id, s = RT()[routeStep], bl = jrBlindText(p), cs = CHG.state;
  if (jrStepAt10()) return 'No roll this turn: Mario is at 10 HP after the Life Shroom, so Jr. Troopa\'s hit has no Close Call. ' + ((JR_SEQ[s.jr] || {}).what || 'Press') + ' whenever you like; the T5 Charge locks the seed again.';
  if (JRT.dead) return 'No beeps: ' + JRT.dead + '. Play it blind: ' + bl + '. The next Charge locks again.';
  if (cs === 'capture' || cs === 'maps' || cs === 'search') return 'No beeps yet: the Charge rays are still being read. Stay on the target screen; the beeps start when the seed locks (or play it blind: ' + bl + ').';
  if (cs === 'nolock' || cs === 'failed' || cs === 'notseen') return 'No Charge lock (' + (CHG.why || 'no clear seed') + '): play it blind. ' + bl[0].toUpperCase() + bl.slice(1) + '.';
  if (zw.on && zw.fight === 'jr' && zw.dead) return 'No edge: the seed was lost. Play it blind: ' + bl + '.';
  return 'No Charge lock: the page did not read a Super Charge in this fight (Mario first on T1, T3 and T5: Super Charge on himself). Play it blind: ' + bl + '.';
}
// the Charge panel's line
function jrStatusLine(s, lost) {
  const P = st.plan, pc = x => Math.round(100 * x) + '%', stp = jrStepNow() && RT()[routeStep];
  const outs = Object.keys(JRT.out).map(k => JR_SEQ[k].t + ' ' + (JRT.out[k] === 'dodge' ? 'dodged' : 'hit (Life Shroom)')).join(', ');
  const head = '<br><b>Jr. Troopa' + (JRT.on ? ' ' + (JR_SEQ[Math.min(JRT.k, JR_SEQ.length - 1)] || {}).t : '') + ':</b> ';
  let body = '';
  if (JRT.dead) body = JRT.dead + '. ';
  if (JRT.cross) body += 'the ' + JR_SEQ[JRT.cross.k].t + ' Charge ' + (JRT.cross.agree ? 'confirmed the carried seed. ' : 'did not fit the carry: tracking from its lock. ');
  if (P && P.mix && stp && PROF().group === 'jr') body += (PROF().id === 'jrpb5' ? 'Power Bounce on the beep: 5+ ' + pc(P.mix.p) + ', 6+ ' + pc(P.mix.p4 || 0) + ' (blind 67.5% / ' + pc(JR_BLIND.p6) + ')' : (JR_SEQ[stp.jr] || {}).what + ' on the beep: Close Call ' + pc(P.mix.p) + ' (blind ' + pc(JR_BLIND.cc) + ')');
  else if ((s === 'nolock' || s === 'failed' || s === 'notseen' || lost) && !(zw.on && zw.fight === 'jr' && !zw.dead)) body += 'play it blind (Close Call ' + pc(JR_BLIND.cc) + '; Power Bounce 5+ 67.5%, 6+ ' + pc(JR_BLIND.p6) + ').';
  else if (zw.on && zw.fight === 'jr') body += 'carried from the ' + JR_SEQ[JRT.origin || 0].t + ' Charge; the beeps start on each Close Call / Power Bounce target screen.';
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
  return { target: C.target, p: C.p, p6: C.p4, pStates: C.pStates, doubt: S.doubt, w: C.w, none: C.none, from, W, states: S.list.map(q => ({ s: q.s >>> 0, nc: q.nc, g: q.g, w: q.w })) };
}
const jrBlind = id => (id === 'jrpb5' ? JR_BLIND.p5 : id === 'jrpb6' ? JR_BLIND.p6 : JR_BLIND.cc);
