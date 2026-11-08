//@ Hallway Bowser T1: Mario's HP and Bowser's Close Call roll in the Charge tracker (model only). charge_live/README.md v79.
//@ Inlined into page_template.html after fb14_live.js by shared/inline.py (//@ lines are dropped). Needs the page globals
//@ (R, FRAME, zw, zwF, slog, st, isRoute, RT, routeStep, render, cancelBeeps) and jr_live.js (jrTens, JR_TENS_MIN, JRT).
/* ---------- Hallway Bowser T1: Mario's HP and Bowser's Close Call roll ----------
 * v78 found (emulator, fixtures/hw3_logs.json, test_hw_cc_model.js) that at 5 HP or less (Danger) every Bowser T1 attack
 * first rolls Close Call, rand_int(100) < 30 (caller 0x80277518, 1A5830.c: only under 6 HP), at AI + 54 / 70 / 55 (Body
 * Slam / Claw Swipe / Fire Breath). Lucky: the attack misses and nothing more is drawn to T2's menu. A hit kills Mario (Game
 * Over, or a Life Shroom revive whose draws are not modelled). At 6 HP or more there is no roll: the v77 draws.
 * v78's beeped Spiny Flip throw (a Close Call lever) was removed in v79 at the runner's request: one timed throw cannot make
 * the Close Call 100%. The runner's route has Mario above 5 HP here, so the no-roll model is the route: the tracker's states
 * (zw.parts) are exactly v77's and Time Out is planned from them exactly as v77 did. The roll model is only a fallback:
 *
 * Mario's HP: the status bar's tens place in Hallway T1 (jrTens). The units are not read, so the page never knows 5 HP or
 * less for sure.
 *  - a "1": 10 HP: no roll, no fallback.
 *  - not read, or mixed reads: the route's HP (above 5) is assumed; the roll states are carried beside, at prior odds 0.1.
 *  - blank: 1-9 HP, the route's 6-9 or a 5-or-less off the route: the roll states at prior odds 0.3.
 * The roll states (zw.shadow: the same lock, impact frames and confirm shifts; the roll's hits dropped, Mario alive on T2
 * means the miss) are weighed by the same coin as zw.parts but never enter the strip, the doubt or the merges. On Time Out's
 * target screen the v77 plan stands while the roll states hold under 5% of the weight. Above that a frame must work under
 * both (else no edge), and when the coin fits the roll states better than the route's (50%+) it is no edge whatever the
 * frame. A "1" on a steady bar in Bowser's turn (before a revive could show) drops the fallback. Life Shroom: a "1" after
 * the last possible roll or hit = Mario died and was revived at 10 HP: the tracker stops and Time Out says no edge. */
const HWHP_LATE = 300;          // clock frames after the Spiny Flip confirm: a "1" read before this is 10 HP (a revive needs the roll, at +138 or
                                // later, then the death and the revive: far later). A late blank proves nothing (10 HP hit by Bowser is blank too).
const HWHP_DIE = 360;           // after this (the latest roll or hit: impact +175 + 44 + 76 = +295) a "1" on the bar is a revive
const HWHP_MIN = 0.05;          // below this share of the weight the roll states do not touch the plan
const HWHP_ODDS = { none: 0.1, blank: 0.3 };    // prior odds of the roll states against the route's no-roll states
const HWHP = {};
function hwHpReset() { Object.assign(HWHP, { tens: [], late: [], c: null, odds: 0, why: null, died: false, dieN: 0 }); if (typeof zw !== 'undefined') zw.shadow = null; }
hwHpReset();
const hwHpOne = v => v >= JR_TENS_MIN;
// the tens reads -> 'ten' (a "1"), 'blank', or null (too few, or mixed)
function hwHpRead(T, n) { if (T.length < n) return null; const k = T.filter(hwHpOne).length / T.length; return k >= 0.8 ? 'ten' : k <= 0.2 ? 'blank' : null; }
// the fallback's prior odds for the Spiny Flip confirm
function hwHpHyps(read) {
  read = read !== undefined ? read : hwHpRead(HWHP.tens, 5);
  if (read === 'ten') return { odds: 0, why: '10 HP: no roll' };
  if (read === 'blank') return { odds: HWHP_ODDS.blank, why: 'single-digit HP: the route\'s 6-9 (no roll), or 5 or less off the route (roll)' };
  return { odds: HWHP_ODDS.none, why: (HWHP.tens.length >= 5 ? 'HP read unsure' : 'HP not read') + ': the route\'s HP above 5 assumed (no roll)' };
}
/* zwInput, at the Spiny Flip confirm on clock frame c, after zw.parts got v77's split: the roll states beside them */
function hwHpSplit(c, shs, imps, id) {
  const H = hwHpHyps(), out = [];
  Object.assign(HWHP, { c, odds: H.odds, why: H.why, late: [], died: false, dieN: 0 });
  zw.shadow = null; zw.shadowT0 = zw.t0;
  if (H.odds > 0) {
    // from the states before the split: v77's split made one per (shift, impact, guard); take each pre-split state once
    const pre = zw.preSplit || [];
    for (const p of pre) for (const [sh, ws] of shs) for (const im of imps) {
      const q = zwClone(p); q.w = p.w * ws * H.odds / imps.length;
      zwMerge(q.ev, R.buildEv([{ f: c + sh, id, imp: im, guard: false, danger: true }])); q.evMax = Math.max(q.evMax, c + sh + im + 45); out.push(q);
    }
    zw.shadow = out.length <= ZW_MAXP ? out : null;
  }
  zw.preSplit = null;
  slog('hwHp', { c, why: H.why, odds: H.odds, roll: zw.shadow ? zw.shadow.length : 0, tensN: HWHP.tens.length, share10: HWHP.tens.length ? +(HWHP.tens.filter(hwHpOne).length / HWHP.tens.length).toFixed(2) : null });
}
/* zwUpdate: the roll states stepped with the same coin; a hit is dropped (Mario alive on T2 = the miss) */
function hwHpShadowUpdate(to, L) {
  if (zw.shadowT0 !== zw.t0) { zw.shadow = null; return; }
  const keep = new Map(), out = [];
  for (const p of zw.shadow) {
    if (!zwStep(p, to, L) || p.S.ccHit) continue;
    if (to > p.evMax && p.S.ccAt == null && !p.S.inst.length && !(p.S.extra && p.S.extra.size) && p.g >= (p.pauseAt || 0) + (p.pause || 0)) {
      const k = p.S.s + ':' + p.S.nc + ':' + p.g, q = keep.get(k); if (q) { q.w += p.w; q.err = Math.min(q.err, p.err); continue; } keep.set(k, p);
    }
    out.push(p);
  }
  let mx = 0; for (const p of zw.parts) if (p.w > mx) mx = p.w; for (const p of out) if (p.w > mx) mx = p.w;
  zw.shadow = out.filter(p => p.w >= mx * ZW_CUT);
}
// the weight shares: roll (the fallback) and no roll (zw.parts, the route)
function hwHpShares() {
  let n = 0, d = 0; for (const p of zw.parts || []) n += p.w; if (zw.shadow && zw.shadowT0 === zw.t0) for (const p of zw.shadow) d += p.w;
  const t = n + d; return t ? { d: d / t, n: n / t } : { d: 0, n: 0 };
}
/* zwPlan, after v77's frame choice C: null = the plan stands; else { msg, log } = no edge */
function hwHpCheck(C, PD) {
  if (!zw.shadow || zw.shadowT0 !== zw.t0 || !zw.shadow.length || C.target == null) return null;
  const sh = hwHpShares(); if (sh.d < HWHP_MIN) return null;
  const pc = x => Math.round(100 * x) + '%', why = HWHP.why || 'HP not read';
  if (sh.d >= 0.5) return { msg: 'No edge: the coin fits Bowser\'s Close Call roll (Mario at 5 HP or less) better than the route\'s HP (' + pc(sh.d) + '; ' + why + ').', log: { shareRoll: +sh.d.toFixed(3), why: 'coin favours the roll' } };
  const m = new Map(); for (const p of zw.shadow) { if (!zwSettled(p) || p.S.ccAt != null) continue; const k = (p.S.s >>> 0) + ':' + p.S.nc + ':' + p.g, q = m.get(k); if (q) q.w += p.w; else m.set(k, { s: p.S.s >>> 0, nc: p.S.nc, g: p.g, w: p.w }); }
  const L = [...m.values()].sort((a, b) => b.w - a.w), D = Math.max(...PD.map(x => Math.abs(x[0])));
  let pd = 0; if (L.length) { const x = zwShare(L, C.target - D, C.target + D, PROF()); for (const [d, q] of PD) pd += q * (x[d + D] || 0); }
  const pn = C.pStates;
  if (!L.length || Math.min(pd, pn) < num('zwedge')) return { msg: 'No edge: Mario\'s HP is not known for sure (' + why + ') and the coin has not ruled out Bowser\'s Close Call roll (' + pc(sh.d) + '): the best frame works ' + pc(pn) + ' without the roll, ' + (L.length ? pc(pd) : 'unknown') + ' with it.', log: { shareRoll: +sh.d.toFixed(3), pRoll: +pd.toFixed(3), pNoRoll: +pn.toFixed(3), target: C.target } };
  return null;
}
const hwHpStep = () => { const s = isRoute() && RT()[routeStep]; return s && /^Hallway Bowser/.test(s.t || '') ? s : null; };
/* every video frame (onFrame): the T1 HP read, a late 10 HP read, the Life Shroom watch */
function hwHpFrame(t, present) {
  const s = hwHpStep(); if (!s) return;
  const B = typeof JRT !== 'undefined' ? JRT.bar : null, steady = present && B && B.since && t - B.since > 5 * FRAME; if (!steady) return;
  const v = jrTens();
  if (HWHP.c == null) { if (s.turn === 'hw_spiny') { HWHP.tens.push(v); if (HWHP.tens.length > 40) HWHP.tens.shift(); } return; }
  if (!zw.on || zw.src !== 'charge') return;
  const fr = zwF(t, 0) - HWHP.c;
  if (fr < HWHP_LATE && zw.shadow) {
    HWHP.late = hwHpOne(v) ? HWHP.late.concat(v) : [];
    if (HWHP.late.length >= 6) { zw.shadow = null; slog('hwHpSettled', { why: '10 HP on the bar before any revive', frames: Math.round(fr) }); }
  }
  if (fr > HWHP_DIE && !HWHP.died) {
    HWHP.dieN = hwHpOne(v) ? HWHP.dieN + 1 : 0;
    if (HWHP.dieN >= 6) {
      HWHP.died = true; zw.on = false; zw.shadow = null; cancelBeeps(); st.plan = null; slog('hwHpDied', { at: Math.round(t), frames: Math.round(fr) });
      st.msg = 'Mario was hit on Hallway T1 (10 HP on the bar: a Life Shroom). The page does not follow the revive\'s random numbers: no Time Out beep this attempt, press it normally (31%).'; render();
    }
  }
}
// a new Hallway T1 (the Spiny Flip step entered again): read the HP afresh
function hwHpStepChange() { const s = isRoute() && RT()[routeStep]; if (s && s.turn === 'hw_spiny') hwHpReset(); }
