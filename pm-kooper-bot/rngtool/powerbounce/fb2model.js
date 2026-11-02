// Final Bowser phase 2 Power Bounce model for the page (port of fb2model.py, emulator-matched; see README "FB2").
// Frame 0 = the frame whose start seed is `seed` (before that frame's draws). Per frame: lightning draws (two periodic
// sources, phases p130 / p220 = the frame offsets that put frame 0 at that point of each cycle), then roll k at
// d+71+27(k-1) or the stars at d+45+27(k-1), then extra periodic effect draws (fx, e.g. the 20-frame 0xE00D6838 cycle of
// the route FB2 state: pass {period, counts[], phase}), then the coin (next draw at frame coinNext; +24, +48 after >= 70),
// then the per-frame step. d = frame of the target-screen A.
'use strict';
const MUL = 0x5D588B65;
const adv = s => (Math.imul(s, MUL) + 1) >>> 0;
function randInt(st, mx) {            // st = {s}; rand_int(mx) for mx 100 or 359
  const m = mx === 100 ? 1009 : mx, dv = Math.floor(0xFFFFFFFF / (m + 1));
  let v; do { st.s = adv(st.s); v = Math.floor(st.s / dv); } while (v > m);
  return mx === 100 ? Math.floor(v / 10) : v;
}
const A130 = [78, 83, 113, 118], A220 = [18, 78, 88, 178];
const TH = []; { let c = 200; for (let i = 0; i < 40; i++) { c = Math.floor(c * 60 / 100); TH.push(c); } }
const nstars = dmg => dmg >= 9 ? 11 : dmg >= 5 ? 10 : dmg >= 3 ? 8 : 6;
function lightAt(f, p130, p220) {
  const a = (f + p130) % 130, b = (f + p220) % 220;
  return A130.filter(x => x === a).length + A220.filter(x => x === b).length;
}
// bounces (2 + rolls passed) for confirm frame d; o = {p130, p220, coinNext, dmg0 (13), fx}
function fb2Bounces(seed, d, o) {
  const st = { s: seed >>> 0 }, dmg0 = o.dmg0 || 13, fx = o.fx;
  let nc = o.coinNext, k = 0, hit = 0;
  for (let f = 0; f < d + 71 + 27 * 30; f++) {
    for (let i = lightAt(f, o.p130, o.p220); i > 0; i--) randInt(st, 359);
    if (f === d + 71 + 27 * k && k === hit - 1) { if (randInt(st, 100) > TH[k]) return k + 2; k++; }
    if (f === d + 45 + 27 * hit) { for (let i = nstars(Math.max(1, dmg0 - hit)); i > 0; i--) randInt(st, 359); hit++; }
    if (fx) for (let i = fx.counts[(f + fx.phase) % fx.period]; i > 0; i--) randInt(st, 359);
    if (f === nc) nc += randInt(st, 100) >= 70 ? 48 : 24;
    st.s = adv(st.s);
  }
  return k + 2;
}
// P(bounces >= K) for a planned confirm frame d over weighted candidates [{seed, w, p130, p220, coinNext, fx}],
// with the runner's press landing at d + e with probability press[e] (default 50% on time, 25% one early/late).
function fb2PAtLeast(cands, d, K, press = { '-1': 0.25, '0': 0.5, '1': 0.25 }, dmg0 = 13) {
  let tot = 0, ok = 0;
  for (const c of cands) for (const e in press) {
    const w = (c.w || 1) * press[e]; tot += w;
    if (fb2Bounces(c.seed, d + (+e), { ...c, dmg0 }) >= K) ok += w;
  }
  return tot ? ok / tot : 0;
}
if (typeof module !== 'undefined') module.exports = { fb2Bounces, fb2PAtLeast, lightAt, TH };
