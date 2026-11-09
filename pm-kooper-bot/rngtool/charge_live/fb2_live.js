//@ Final Bowser phase 2, T6 -> T7, live (charge_live/README.md, FB2 section; fb2_route/README.md section 2). Inlined into
//@ page_template.html after charge_live.js; //@ lines are dropped. Needs the page globals R, FRAME, $, num, slog, sample,
//@ chgMap, CHG, beepAt, cancelBeeps, PRESS_ERR, render, st and the charge lock (chgSearch's FB2 profile).
/* ---------- FB2: the T6 Super Charge lock -> the popup A (Close Call) -> the T7 Power Bounce ----------
 * The T6 Charge's rays give the seed at the end of the rays (confirm + 61) up to the lightning: the rays window only
 * shows where the bolt draws shifted the stream, so the lock keeps every (lightning pattern, first coin q) whose score
 * is within FB2_TOL of the best, each with every lightning phase pair (p130, p220) that gives that pattern
 * (p130 = p220 mod 5), and console lag 0/1 after the rays. From there the stretch to the T7 bounces is closed
 * (fb2_route/t6model.py, 229/229 runs): only the A that closes the "+3" popup (confirm + K, K = 77..136; no press = 137)
 * moves Bowser's AI (K + 40: RandInt 100, 80, maybe 60), and the Close Call roll (rand_int(100) < 30) comes 52/62/55
 * frames later (Body Slam / Claw / Fire Breath); then the T7 menu, and the Power Bounce rolls from the target-screen A
 * (d): stars d + 45 + 27k, rolls d + 71 + 27k (powerbounce/fb2model.py, first hit 15). Same-frame order: bolts, script
 * draws, coin, step.
 * 1. Lock -> plan K: the frame in the rest of the popup window that is best over the kept states (press 25/50/25 over
 *    -1/0/+1), with the T7 bounce windows as tie-breaker; 3 beeps 0.3 s apart, the last on the press.
 * 2. The popup closing (first picture without it = K + 2; the status bar comes back on K + 5) gives the K that happened.
 * 3. The status bar is up through Bowser's turn and the T7 menu: its coin shines prune the states.
 * 4. On the T7 Power Bounce target screen: the best target-A frame for 7+ bounces (the kill at Bowser 80 HP), as the
 *    page's other plans (lead, window, beeps). */
const FB2_TOL = 0.002, FB2_P130 = [78, 83, 113, 118], FB2_P220 = [18, 78, 88, 178];
const FB2_DELTA = { slam: 52, claw: 62, fire: 55 }, FB2_MENU = { slam: 101, claw: 83, fire: 134 }, FB2_KMIN = 77, FB2_KMAX = 137;
const FB2_LAGS = [[0, 0.75], [1, 0.25]], FB2_BEEPS = 3, FB2_GAP = 300, FB2_DMG0 = 15, FB2_HP = 80, FB2_MAXH = 4000;
const FB2_TH = (() => { const t = []; let c = 200; for (let i = 0; i < 30; i++) { c = Math.floor(c * 60 / 100); t.push(c); } return t; })();
var FB2 = { on: false };      // var: charge_live.js calls fb2Reset (via chgReset) before this file has run
function fb2Reset() { if (!FB2) return; Object.assign(FB2, { rate: typeof chgRate === 'function' && typeof consoleRate === 'function' ? chgRate() : null, on: false, hyps: null, plan: null, kObs: null, kSeen: null, kHow: null, t7: null, popup: null, why: null, taps: [], vis: [], visFrom: null }); fb2Show(); }
const fb2nb = (f, p1, p2) => (FB2_P130.includes((f + p1) % 130) ? 1 : 0) + (FB2_P220.includes((f + p2) % 220) ? 1 : 0);
/* the window patterns (bolt counts on rays frames 0..47 = confirm + 13..60) and the phase pairs behind each */
function fb2Patterns() {
  if (fb2Patterns.c) return fb2Patterns.c;
  const idx = new Map(), list = [];
  for (let p2 = 0; p2 < 220; p2++) for (let p1 = p2 % 5; p1 < 130; p1 += 5) {
    const r = []; for (let n = 0; n < 48; n++) r.push(fb2nb(n + 13, p1, p2));
    const k = r.join(''); let i = idx.get(k); if (i == null) { i = list.length; idx.set(k, i); list.push({ r, ph: [] }); } list[i].ph.push([p1, p2]);
  }
  const bytes = new Uint8Array(list.length * 52); list.forEach((x, i) => x.r.forEach((v, n) => { bytes[i * 52 + n] = v; }));
  return (fb2Patterns.c = { list, bytes });
}
/* ---- the model (t6pay.c / t6model.py) ---- */
function fb2Frame1(S, f, ph) {      // the idle draws of frame f: bolts, coin, step
  for (let i = fb2nb(f, ph[0], ph[1]); i; i--) S.s = R.randInt(S.s, 359)[0];
  if (f === S.nc) { const r = R.randInt(S.s, 100); S.s = r[0]; S.nc += r[1] >= 70 ? 48 : 24; if (S.coins) S.coins.push([f, r[1] >= 70]); }
  S.s = R.adv(S.s);
}
function fb2Idle(S, f0, f1, ph) { for (let f = f0; f < f1; f++) fb2Frame1(S, f, ph); }
/* Bowser's T6 turn from state S at the start of frame E = K + 40: { lucky, atk, T, menu, S (start of frame T + 1) } */
function fb2AI(S0, E, ph, slamOk, clawOk) {
  const S = { s: S0.s, nc: S0.nc, coins: S0.coins ? S0.coins.slice() : null };
  for (let i = fb2nb(E, ph[0], ph[1]); i; i--) S.s = R.randInt(S.s, 359)[0];
  S.s = R.randInt(S.s, 100)[0]; let r = R.randInt(S.s, 80); S.s = r[0]; let atk;
  if (r[1] < 20 && slamOk) atk = 'slam'; else { r = R.randInt(S.s, 60); S.s = r[0]; atk = r[1] < 20 && clawOk ? 'claw' : 'fire'; }
  if (E === S.nc) { const c = R.randInt(S.s, 100); S.s = c[0]; S.nc += c[1] >= 70 ? 48 : 24; if (S.coins) S.coins.push([E, c[1] >= 70]); }
  S.s = R.adv(S.s);
  const T = E + FB2_DELTA[atk]; fb2Idle(S, E + 1, T, ph);
  for (let i = fb2nb(T, ph[0], ph[1]); i; i--) S.s = R.randInt(S.s, 359)[0];
  const cc = R.randInt(S.s, 100); S.s = cc[0];
  if (T === S.nc) { const c = R.randInt(S.s, 100); S.s = c[0]; S.nc += c[1] >= 70 ? 48 : 24; if (S.coins) S.coins.push([T, c[1] >= 70]); }
  S.s = R.adv(S.s);
  return { lucky: cc[1] < 30, cc: cc[1], atk, T, menu: T + FB2_MENU[atk], S };
}
/* Power Bounce from state S at the start of frame f0 (<= d), target-screen A on frame d: the number of bounces (the
 * 7th ends the fight at 80 HP: 15 + 14 + ... + 9 = 84) */
function fb2PB(S0, f0, d, ph) {
  const S = { s: S0.s, nc: S0.nc }; fb2Idle(S, f0, d, ph);
  let k = 0, hit = 0, dmg = 0;
  for (let f = d; f < d + 71 + 27 * 20; f++) {
    for (let i = fb2nb(f, ph[0], ph[1]); i; i--) S.s = R.randInt(S.s, 359)[0];
    if (f === d + 71 + 27 * k && k === hit - 1) { const r = R.randInt(S.s, 100); S.s = r[0]; if (r[1] > FB2_TH[k]) return k + 2; k++; }
    if (f === d + 45 + 27 * hit) { const dm = Math.max(1, FB2_DMG0 - hit); for (let i = dm >= 9 ? 11 : dm >= 5 ? 10 : dm >= 3 ? 8 : 6; i; i--) S.s = R.randInt(S.s, 359)[0]; hit++; dmg += dm; if (dmg >= FB2_HP) return hit; }
    if (f === S.nc) { const r = R.randInt(S.s, 100); S.s = r[0]; S.nc += r[1] >= 70 ? 48 : 24; }
    S.s = R.adv(S.s);
  }
  return k + 2;
}
/* the same for every d in [D0 - 1, D0 + W + 1] (the idle frames up to D0 - 1 simulated once) */
function fb2PBWin(S0, f0, D0, W, ph) {
  const S = { s: S0.s, nc: S0.nc }; fb2Idle(S, f0, D0 - 1, ph); const out = [];
  for (let d = D0 - 1; d <= D0 + W + 1; d++) { out.push(fb2PB(S, d, d, ph)); fb2Frame1(S, d, ph); }
  return out;
}
/* Bowser's attack flags at T6: a Body Slam or a Claw on T5 forbids that attack on T6 (fb2_route README section 4) */
function fb2Flags() { const v = ($('s-fb2t5') || {}).value || 'any'; return v === 'slam' ? [[false, true, 1]] : v === 'claw' ? [[true, false, 1]] : v === 'fire' ? [[true, true, 1]] : [[true, true, 1 / 3], [false, true, 1 / 3], [true, false, 1 / 3]]; }
/* ---- clock: confirm-relative logic frames from the Charge trigger (the picture of rays frame 3 = confirm + 16) ---- */
/* v72: on the console's frame time (consoleRate, as the Hallway tracker since v70; 33.427 ms until the shines measure it),
 * fixed for the fight at the trigger (FB2.rate, fb2Reset). v71 ran this clock on 33.367 ms (59.94 Hz): ~0.25 frame late at
 * the popup and ~0.9 at the T7 target A on a real N64. Emulator renders run at 33.367: tests set Settings > Console frame
 * time to that. */
const fb2Rate = () => (FB2 && FB2.rate) || (typeof chgRate === 'function' ? chgRate() : FRAME);
const fb2Pic = t => 16 + (t - CHG.trig.t) / fb2Rate();                  // logic frame shown by a picture at time t (lag 0)
// the press for logic frame k: as Time Out's (zwPlan: 4.7 frames before the picture of that frame, minus the capture
// delay, plus the runner's offset)
const fb2PressT = k => CHG.trig.t + (k - 13 - 4.7 + num('off')) * fb2Rate() - num('vlag');
/* the lock: hypotheses from the worker's (pattern, q) pairs */
function fb2Lock(res) {
  const P = fb2Patterns(), hy = res.fb2 && res.fb2.hyps; if (!hy || !hy.pairs.length) { FB2.why = 'no hypotheses'; fb2Show(); return; }
  const seen = new Map(), H = [];
  for (const [p, q, sc, s48, nc48] of hy.pairs) for (const ph of P.list[p].ph) {
    const key = s48 + ':' + nc48 + ':' + ph[0] + ':' + ph[1]; if (seen.has(key)) continue;
    const h = { s: s48 >>> 0, nc: nc48 + 13, ph, w: 1 }; seen.set(key, h); H.push(h);
  }
  const wsum = H.length; H.forEach(h => { h.w = 1 / wsum; });
  const Hk = H.length > FB2_MAXH ? H.filter((h, i) => i % Math.ceil(H.length / FB2_MAXH) === 0) : H;   // too many: an even sample
  Hk.forEach(h => { h.w = 1 / Hk.length; });
  Object.assign(FB2, { on: true, hyps: Hk, pairs: hy.pairs.length, best: hy.best, kObs: null, plan: null, t7: null, taps: [], vis: [], visFrom: null, tLock: performance.now() });
  slog('fb2Lock', { pairs: hy.pairs.length, hyps: H.length, states: new Set(H.map(h => h.s + ':' + h.nc)).size, kSeen: FB2.kSeen });
  if (FB2.kSeen != null) { FB2.plan = { none: 'the lock came after the popup closed' }; if (FB2.kSeen >= 0) fb2SetK(FB2.kSeen, FB2.kHow, FB2.kFrom); } else fb2PlanK();
}
/* the K plan: lucky per hypothesis x flags for every logic K, then the best time frame k in the rest of the window */
function fb2PlanK(kAt) {      // kAt (tests): plan as if the earliest beepable frame were kAt, no beeps
  const t0 = performance.now(), H = FB2.hyps, F = fb2Flags(), now = performance.now();
  const kFirst = kAt != null ? kAt : Math.max(FB2_KMIN + 1, Math.ceil(fb2Pic(now + num('vlag')) + (FB2_BEEPS - 1) * FB2_GAP / fb2Rate() + 0.15 * 1000 / fb2Rate() + 2));
  const rows = [], K0 = Math.max(FB2_KMIN, Math.min(FB2_KMAX, kFirst - 3));   // per (h, flag): lucky for K = K0..137 and the AI result
  for (const h of H) for (const [so, co, wf] of F) {
    const S = { s: h.s, nc: h.nc }; fb2Idle(S, 61, K0 + 40, h.ph);
    const L = new Uint8Array(FB2_KMAX - FB2_KMIN + 1), A = [];
    for (let K = K0; K <= FB2_KMAX; K++) { const r = fb2AI(S, K + 40, h.ph, so, co); L[K - FB2_KMIN] = r.lucky ? 1 : 0; A[K - FB2_KMIN] = r; fb2Frame1(S, K + 40, h.ph); }
    rows.push({ h, w: h.w * wf, L, A });
  }
  const luck = (row, K) => row.L[(K < FB2_KMIN || K > FB2_KMAX ? FB2_KMAX : K) - FB2_KMIN];
  const pcc = k => { let v = 0; for (const r of rows) for (const [l, wl] of FB2_LAGS) for (const [d, q] of PRESS_ERR) v += r.w * wl * q * luck(r, k + d - l); return v; };
  const tot = rows.reduce((a, r) => a + r.w, 0), cand = [];
  for (let k = kFirst; k <= FB2_KMAX - 1; k++) cand.push({ k, p: pcc(k) / tot });
  const blind = pcc(FB2_KMAX + 5) / tot;                         // no press: the popup closes by itself (K = 137)
  if (!cand.length) { const pl = { none: 'the lock came too late for the popup window (closes on +136)', blind, kFirst }; if (kAt != null) return pl; FB2.plan = pl; slog('fb2PlanK', { none: true, kFirst }); fb2Show(); return pl; }
  cand.sort((a, b) => b.p - a.p);
  // tie-break on the T7 windows: P(Close Call and 7+ with the best target-A frame in 1 s from the earliest), on a
  // sample of the states, for the k within 3 points of the best
  const top = cand.filter(c => c.p >= cand[0].p - 0.03).slice(0, 3), sub = rows.length > 24 ? rows.filter((r, i) => i % Math.ceil(rows.length / 24) === 0) : rows;
  const p7Of = c => {
    let v = 0, w = 0;
    for (const r of sub) for (const [l, wl] of FB2_LAGS) for (const [d, q] of PRESS_ERR) {
      const K = Math.min(FB2_KMAX, Math.max(FB2_KMIN, c.k + d - l)), K2 = c.k + d - l < FB2_KMIN ? FB2_KMAX : K, a = r.A[K2 - FB2_KMIN]; w += r.w * wl * q;
      if (!a || !a.lucky) continue; const D0 = a.menu + 45, b = fb2PBWin(a.S, a.T + 1, D0, 30, r.h.ph).map(x => (x >= 7 ? 1 : 0));
      let best = 0; for (let i = 1; i <= 30; i++) best = Math.max(best, 0.25 * b[i - 1] + 0.5 * b[i] + 0.25 * b[i + 1]); v += r.w * wl * q * best;
    }
    c.p7 = w ? v / w : 0;
  };
  for (const c of top) p7Of(c);
  top.sort((a, b) => (b.p + b.p7) - (a.p + a.p7)); let c = top[0];
  // v83, the perfect press (zwChoose's ppPick): a frame the Close Call works on for the states (the console lag 0 / 1
  // unseen, so weighed in), the centre of the widest run of such frames; the spread-weighted p kept for the log
  { const ppk = k => { let v = 0; for (const r of rows) for (const [l, wl] of FB2_LAGS) v += r.w * wl * luck(r, k - l); return v / tot; };
    const a = kFirst - 1, b = FB2_KMAX - 1, sh = []; for (let k = a; k <= b; k++) sh.push(k >= kFirst ? ppk(k) : 0);
    const pk = ppPick(sh, null, a, b, kFirst, b - kFirst, k => pcc(k) / tot, 'safe3'), q = cand.find(x => x.k === pk.target) || c;
    if (q.p7 == null) p7Of(q); c = Object.assign({}, q, { pp: ppk(pk.target), win: pk.run.length }); }
  const tPress = fb2PressT(c.k), pl = { k: c.k, p: c.p, pp: c.pp, win: c.win, p7: c.p7, blind, tPress, kFirst, ms: Math.round(performance.now() - t0), states: rows.length,
    alt: cand.slice(0, 5).map(x => [x.k, +x.p.toFixed(3)]) };
  if (kAt != null) return pl;
  cancelBeeps(); for (let i = 0; i < FB2_BEEPS; i++) beepAt(tPress - (FB2_BEEPS - 1 - i) * FB2_GAP, i === FB2_BEEPS - 1 ? 1320 : 880, i === FB2_BEEPS - 1 ? 0.12 : 0.06);
  FB2.plan = pl; slog('fb2PlanK', FB2.plan); fb2Show(); return pl;
}
/* per picture after the lock: the popup ("+3", a bright box across the top middle: 320-space x 70..250, y 65..100) */
function fb2PopupBox() { const [SX, OX, SY, OY] = chgMap(); return { x: (OX + 80 * SX) / 1280, y: (OY + 70 * SY) / 720, w: 160 * SX / 1280, h: 25 * SY / 720 }; }
function fb2Frame(t, present) {
  if (!CHG.trig) return;
  if (FB2.kSeen == null) {
    const g = sample(fb2PopupBox(), 32, 8); let m = 0; for (let i = 0; i < g.length; i += 4) m += 0.299 * g[i] + 0.587 * g[i + 1] + 0.114 * g[i + 2]; m /= 256;
    const P = FB2.popup || (FB2.popup = { seen: false }), f = fb2Pic(t);     // the popup is up on frames 76 .. K + 1 (K <= 137)
    if (f > 145) { fb2SeenK(P.seen ? FB2_KMAX : null, P.seen ? 'popup (to the end)' : 'not seen'); return; }
    if (m > 85 && f > 70) { P.seen = true; P.lastOn = t; }
    else if (P.seen && t - P.lastOn < 400) fb2SeenK(Math.round(f - 2), 'popup', Math.min(Math.round(f - 2), Math.round(fb2Pic(P.lastOn)) - 1));   // pictures dropped in between: K from the last one with the popup on
    else if (!P.seen && present && f > 80) fb2SeenK(Math.round(f - 5), 'bar');   // the popup was missed: the bar comes back on K + 5
    return;
  }
  // the coin through Bowser's turn and the T7 menu
  if (present && FB2.visFrom == null) FB2.visFrom = fb2Pic(t) + 30;
  if (!present && FB2.visFrom != null) { FB2.vis.push([FB2.visFrom, fb2Pic(t) - 4]); FB2.visFrom = null; }
}
function fb2SeenK(k, how, k0) { FB2.kHow = how; FB2.kFrom = k0 != null ? k0 : k; slog('fb2Seen', { k, how }); if (k == null) { FB2.kSeen = -1; FB2.why = 'the popup and the bar were not seen: no K'; return; } FB2.kSeen = k; if (FB2.on) fb2SetK(k, how, FB2.kFrom); }
function fb2Tap(t) { if (CHG.trig && FB2.kSeen != null && FB2.kSeen >= 0) FB2.taps.push(fb2Pic(t) - 4.8); }      // the flash shows ~4.8 frames after the draw
function fb2SetK(k, how, k0) {      // the popup A on frame k (k0..k when pictures were dropped around the closing)
  FB2.kObs = k; FB2.kHow = how; const F = fb2Flags(), out = [], ks = []; for (let x = Math.min(k, k0 != null ? k0 : k); x <= k; x++) ks.push(x);
  for (const h of FB2.hyps) for (const [l, wl] of FB2_LAGS) for (const kk of ks) for (const [so, co, wf] of F) {
    const K = kk - l < FB2_KMIN ? FB2_KMAX : Math.min(FB2_KMAX, kk - l), S = { s: h.s, nc: h.nc, coins: [] }; fb2Idle(S, 61, K + 40, h.ph);
    const a = fb2AI(S, K + 40, h.ph, so, co); out.push({ h, l, K, a, w: h.w * wl * wf / ks.length });
  }
  const tot = out.reduce((x, o) => x + o.w, 0), luck = out.reduce((x, o) => x + (o.a.lucky ? o.w : 0), 0) / tot;
  const atk = {}; out.forEach(o => { atk[o.a.atk] = (atk[o.a.atk] || 0) + o.w / tot; });
  FB2.t7 = { states: out.filter(o => o.a.lucky), pLucky: luck, atk };
  slog('fb2K', { k, k0: ks[0], how, pLucky: +luck.toFixed(3), atk, planned: FB2.plan && FB2.plan.k }); fb2Show();
}
/* the states left after the coin seen since K, weighed as the zero-wait tracker weighs its states (v72, zwLR): a seen
 * shine a state has (+-2 frames, a dropped picture reads it up to 3.5 late), a predicted shine inside a stretch with the
 * bar up that was not seen (a missed shine), a seen shine it does not have (a false one). v71 dropped a state on any one
 * of them. Returns the states with their weights (w) and the background's share (doubt, as zwDoubt). */
function fb2Prune(upto) {
  const T7 = FB2.t7; if (!T7) return [];
  const vis = FB2.vis.concat(FB2.visFrom != null ? [[FB2.visFrom, upto - 4]] : []).map(([a, b]) => [a, Math.min(b, upto - 4)]).filter(([a, b]) => b > a), taps = FB2.taps.filter(x => x < upto);
  const Wd = 5.5 * (ZW_RHO + ZW_FALSE), Lm = (1 - ZW_PMISS) / Wd, Lmiss = ZW_PMISS, Lf = ZW_FALSE / (ZW_RHO + ZW_FALSE);
  const near = (x, f) => x - f >= -2 && x - f <= 3.5, out = []; let mx = 0, tot0 = 0;
  for (const o of T7.states) {
    tot0 += o.w;
    const S = { s: o.a.S.s, nc: o.a.S.nc, coins: o.a.S.coins.slice() }; fb2Idle(S, o.a.T + 1, Math.floor(upto), o.h.ph);
    const sh = S.coins.filter(c => c[1]).map(c => c[0] + o.l); let lw = 1, err = 0;
    for (const x of taps) if (sh.some(f => near(x, f))) lw *= Lm; else { lw *= Lf; err++; }
    for (const f of sh) if (vis.some(([a, b]) => f >= a && f <= b) && !taps.some(x => near(x, f))) { lw *= Lmiss; err++; }
    if (err > ZW_MAXERR) continue;
    const w = o.w * lw; out.push(Object.assign({}, o, { w, err })); mx = Math.max(mx, w);
  }
  const nVis = vis.reduce((a, [x, y]) => a + (y - x), 0), keep = out.filter(o => o.w >= mx * ZW_CUT), sum = keep.reduce((a, o) => a + o.w, 0), bg = tot0 * ZW_BG0 / (1 - ZW_BG0) * Math.exp(-ZW_RHO * nVis);
  keep.doubt = keep.length ? bg / (bg + sum) : 1;
  return keep;
}
/* the T7 plan on the Power Bounce target screen (or at clock frame cScr in tests): the best target-A frame for 7+ */
function fb2PlanT7(cScr) {
  if (!FB2.on || !FB2.t7) return false;
  const now = performance.now(), cNow = cScr != null ? cScr : fb2Pic(now + num('vlag')), S = fb2Prune(cNow);
  if (!S.length || S.doubt >= 0.5) { st.msg = 'No edge: the FB2 states the page kept do not fit what it saw in Bowser\'s turn (the coin, or the popup frame). Press Power Bounce normally.'; FB2.t7.plan = { none: 'no state fits' }; slog('fb2NoEdge', { doubt: S.doubt != null ? +S.doubt.toFixed(3) : null }); fb2Show(); render(); return true; }
  const tot = S.reduce((a, o) => a + o.w, 0), W = Math.max(0, Math.round(Math.max(1, num('zwwin')) * 1000 / fb2Rate()));
  let from = Math.ceil(cNow + num('lead') * 1000 / fb2Rate() + 1);
  if (cScr == null) for (let i = 0; i < 300 && fb2PressT(from) < earliestPress(now); i++) from++;   // every beep still ahead
  const s7 = new Array(W + 1).fill(0), s6 = new Array(W + 1).fill(0);
  for (const o of S) { const b = []; for (let x = from - 1; x <= from + W + 1; x++) b.push(fb2PB(o.a.S, o.a.T + 1, x - o.l, o.h.ph));
    for (let k = 0; k <= W; k++) for (const [d, q] of PRESS_ERR) { s7[k] += o.w * q * (b[k + 1 + d] >= 7 ? 1 : 0); s6[k] += o.w * q * (b[k + 1 + d] >= 6 ? 1 : 0); } }
  // v83, the perfect press: the 7-bounce share on each frame itself (no spread), the centre of the widest run of frames
  // that give 7 for the states (ppPick); with no such frame, the best 7 frame as before. Spread-weighted p7 / p6 logged.
  const e7 = new Array(W + 3).fill(0), e6 = new Array(W + 3).fill(0);
  for (const o of S) for (let x = from - 1; x <= from + W + 1; x++) { const v = fb2PB(o.a.S, o.a.T + 1, x - o.l, o.h.ph); if (v >= 7) e7[x - from + 1] += o.w / tot; if (v >= 6) e6[x - from + 1] += o.w / tot; }
  let k = 0; for (let i = 1; i <= W; i++) if (s7[i] + 0.1 * s6[i] > s7[k] + 0.1 * s6[k] + 1e-12) k = i;
  const pk = ppPick(e7, e6, from - 1, from + W + 1, from, W, x => (s7[x - from] || 0) / tot, 'safe3'); if (pk.ok) k = pk.target - from;
  const d = from + k, dz = S.doubt || 0, plan = { d, p7: (1 - dz) * s7[k] / tot, p6: (1 - dz) * s6[k] / tot, pp7: (1 - dz) * e7[k + 1], pp6: (1 - dz) * e6[k + 1], win: pk.ok ? pk.run.length : 0, doubt: +dz.toFixed(3), states: S.length, tPress: fb2PressT(d) };   // the background's share counts as no 7 (blind 7 is ~7%)
  FB2.t7.plan = plan;
  if (cScr != null) return plan;
  if (cScr == null) { cancelBeeps(); playBeeps(plan.tPress);
    st.msg = null; st.plan = { tMade: now, w: { start: d, end: d, length: 1 }, target: d, tPress: plan.tPress, tLast: CHG.trig.t, rate: fb2Rate(), carried: true, from, to: from + W, first: 0, prof: 'fb2', tab: [], tab4: null, mix: { p: plan.p7, pp: plan.pp7, win: plan.win, doubt: dz, groups: S.length, zw: true } }; }
  slog('fb2PlanT7', plan); fb2Show(); if (cScr == null) render(); return true;
}
function fb2Show() {
  const el = $('fb2-status'); if (!el) return;
  if (!FB2.on) { el.innerHTML = '<b>FB2 T6 → T7:</b> ' + (FB2.why ? FB2.why : 'waiting for the T6 Super Charge lock'); return; }
  const P = FB2.plan, T = FB2.t7, pc = x => Math.round(100 * x) + '%';
  el.innerHTML = '<b>FB2 T6 → T7</b> (' + FB2.hyps.length + ' RNG states after the rays)' +
    '<br>Popup A: ' + (!P ? '…' : P.none ? 'no plan (' + P.none + '; a blind press is ' + pc(P.blind) + ')' : 'beep on +' + P.k + ': Close Call, perfect press ' + pc(P.pp != null ? P.pp : P.p) + (P.win ? ' (window ' + P.win + ')' : '') + ' (with your press spread ' + pc(P.p) + '), Close Call and 7 bounces ' + pc(P.p7 || 0) + ' (no press: ' + pc(P.blind) + ')') +
    (FB2.kObs != null ? '<br>Seen: popup A on +' + FB2.kObs + (FB2.kHow === 'bar' ? ' (from the bar)' : '') + '; Close Call ' + pc(T.pLucky) + '; Bowser ' + Object.entries(T.atk).map(([a, w]) => a + ' ' + pc(w)).join(', ') : '') +
    (T && T.plan ? '<br>T7: ' + (T.plan.none ? 'no edge (' + T.plan.none + ')' : 'target A on +' + T.plan.d + ': perfect press 7 bounces ' + pc(T.plan.pp7 != null ? T.plan.pp7 : T.plan.p7) + (T.plan.win ? ' (window ' + T.plan.win + ')' : '') + ', 6+ ' + pc(T.plan.pp6 != null ? T.plan.pp6 : T.plan.p6) + '; with your press spread 7 ' + pc(T.plan.p7) + ', 6+ ' + pc(T.plan.p6) + ' (' + T.plan.states + ' states)') : '');
}
fb2Reset();
window.__fb2 = { FB2, planKAt: k => fb2PlanK(k), setK: (k, how, k0) => fb2SetK(k, how || 'test', k0), planT7At: c => fb2PlanT7(c), pic: t => fb2Pic(t), pressT: k => fb2PressT(k), prune: c => fb2Prune(c).length };   // for tests
