// Blooper Power Bounce model for the High Power Bounce Manipulator (port of blmodel.py, emulator-matched; see README).
// Frame 0 = the frame whose start seed is `seed`. Per frame: the hit's stars (d+51+26(k-1), hit k) or roll k
// (d+76+26(k-1)), then the coin (next draw at frame coinNext; +24, +48 after a value >= 70), then the per-frame step.
// The Blooper menu and target screen draw nothing else. d = frame of the target-screen A.
'use strict';
const MUL = 0x5D588B65;
const adv = s => (Math.imul(s, MUL) + 1) >>> 0;
function randInt(st, mx) {
  const m = mx === 100 ? 1009 : mx, dv = Math.floor(0xFFFFFFFF / (m + 1));
  let v; do { st.s = adv(st.s); v = Math.floor(st.s / dv); } while (v > m);
  return mx === 100 ? Math.floor(v / 10) : v;
}
function chances(value, n = 60) { const t = []; let c = 200; for (let i = 0; i < n; i++) { c = Math.floor(c * value / 100); t.push(c); } return t; }
const TH90 = chances(90), TH97 = chances(97);
const nstars = dmg => dmg >= 9 ? 11 : dmg >= 5 ? 10 : dmg >= 3 ? 8 : 6;
// bounces (2 + rolls passed) for confirm frame d; o = {coinNext, dm (Dodge Master), dmg0 (1), kmax (60)}
function blBounces(seed, d, o) {
  const st = { s: seed >>> 0 }, TH = o.dm ? TH97 : TH90, dmg0 = o.dmg0 || 1, kmax = o.kmax || 60;
  let nc = o.coinNext, k = 0, hit = 0;
  for (let f = 0; f < d + 76 + 26 * kmax; f++) {
    if (f === d + 51 + 26 * hit && hit === k) { for (let i = nstars(Math.max(1, dmg0 - hit)); i > 0; i--) randInt(st, 359); hit++; }
    if (f === d + 76 + 26 * k) { if (randInt(st, 100) > TH[k]) return k + 2; k++; if (k >= kmax) return k + 2; }
    if (f === nc) nc += randInt(st, 100) >= 70 ? 48 : 24;
    st.s = adv(st.s);
  }
  return k + 2;
}
function blPAtLeast(cands, d, K, press = { '-1': 0.25, '0': 0.5, '1': 0.25 }) {
  let tot = 0, ok = 0;
  for (const c of cands) for (const e in press) {
    const w = (c.w || 1) * press[e]; tot += w;
    if (blBounces(c.seed, d + (+e), c) >= K) ok += w;
  }
  return tot ? ok / tot : 0;
}
if (typeof module !== 'undefined') module.exports = { blBounces, blPAtLeast, chances };
