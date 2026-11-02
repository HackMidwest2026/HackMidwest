// Payoff of a lock for the Final Bowser phase-2 Power Bounce (fb2model.js, emulator-matched 113/113; no aura at the
// bounce turn because the Peach Beam removed it). Frame 0 = the frame the runner reaches the target screen; the page
// picks the confirm frame d in [LEAD, LEAD + WIN) that maximises the expected count over its candidate set, under the
// press error 50% on the frame, 25% one early, 25% one late (or exact presses with EXACT=1). The true seed is one of N
// equally likely candidates (N = 1: a full lock carried to the target screen). Blind = one fixed d, no information.
// usage: node aura_payoff.js [LEAD=0] [WIN=30] [EXACT=0]
'use strict';
const { fb2Bounces } = require('../powerbounce/fb2model.js');
const LEAD = +(process.argv[2] || 0), WIN = +(process.argv[3] || 30), EXACT = +(process.argv[4] || 0);
let rs = 12345; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296;
const press = EXACT ? [[0, 1]] : [[-1, 0.25], [0, 0.5], [1, 0.25]];
function trial(N) {
  const o = { p220: Math.floor(rnd() * 220), coinNext: Math.floor(rnd() * 48), dmg0: 13 };
  o.p130 = Math.floor(rnd() * 26) * 5 + (o.p220 % 5);                 // the mod-5 relation seen in every state
  const seeds = []; for (let i = 0; i < N; i++) seeds.push(Math.floor(rnd() * 4294967296) >>> 0);
  const truth = seeds[0];
  const cache = new Map();
  const b = (s, d) => { const k = s + ':' + d; let v = cache.get(k); if (v === undefined) { v = fb2Bounces(s, d, o); cache.set(k, v); } return v; };
  let best = -1, bd = LEAD;
  for (let d = LEAD; d < LEAD + WIN; d++) {
    let e = 0; for (const s of seeds) for (const [x, w] of press) e += w * b(s, d + x);
    if (e > best) { best = e; bd = d; }
  }
  const out = press.map(([x, w]) => [b(truth, bd + x), w]);
  return { plan: best / N, out };
}
function run(N, T) {
  let E = 0; const P = {};
  for (let t = 0; t < T; t++) {
    const r = trial(N);
    for (const [c, w] of r.out) { E += w * c / T; for (let K = 4; K <= 10; K++) if (c >= K) P[K] = (P[K] || 0) + w / T; }
  }
  return { E, P };
}
function blind(T) {
  let E = 0; const P = {};
  for (let t = 0; t < T; t++) {
    const o = { p220: Math.floor(rnd() * 220), coinNext: Math.floor(rnd() * 48), dmg0: 13 }; o.p130 = Math.floor(rnd() * 26) * 5 + (o.p220 % 5);
    const c = fb2Bounces(Math.floor(rnd() * 4294967296) >>> 0, LEAD, o);
    E += c / T; for (let K = 4; K <= 10; K++) if (c >= K) P[K] = (P[K] || 0) + 1 / T;
  }
  return { E, P };
}
const fmt = (n, r) => console.log(`${n.padEnd(26)} E[bounces] ${r.E.toFixed(2)}   ` +
  [5, 6, 7, 8, 9].map(K => `${K}+ ${(100 * (r.P[K] || 0)).toFixed(1)}%`).join('  '));
console.log(`window d in [${LEAD}, ${LEAD + WIN}) frames, press ${EXACT ? 'exact' : '50/25/25 (on time / 1 early / 1 late)'}`);
fmt('blind (one fixed frame)', blind(20000));
for (const [N, T] of [[1, 3000], [10, 600], [100, 150], [1000, 40]]) fmt(`${N} candidate${N > 1 ? 's' : ''}`, run(N, T));
