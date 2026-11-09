/* v85: the emulator logs (gch_log.py / jr_route_log.py) -> fixtures/nb_cc_logs.json (compact: the seed every 8th frame from
 * the first Super Charge on, the inputs, the first coin frames, the Close Call rolls, the Power Bounce cap rolls).
 * usage: node make_fixture.js OUT.json LOG.json ... */
'use strict';
const fs = require('fs'), path = require('path'), C = require('./check_core.js');
const out = { note: 'v85 emulator logs (JP, debug core), Normal Boots route: nb_cc/gch_log.py (one turn: Super Charge, Goombario Charge / Headbonk, the enemy turn) and nb_cc/jr_route_log.py (the Jr. Troopa fight T1-T7). s: gRandSeed before frame f for every 8th frame from the first Super Charge confirm (f0) on.', runs: [] };
for (const fn of process.argv.slice(3)) {
  const r = JSON.parse(fs.readFileSync(fn, 'utf8')), N = C.normalize(r), L = N.L, f0 = Math.min(...N.c0s);
  const firstCoin = c0 => { for (let f = c0; f < L.length; f++) if (L[f].c.some(x => x[0] === '80146d54')) return f; return null; };
  const death = (() => { for (let f = f0 + 1; f < L.length; f++) if (L[f].hp <= 0) return f; return null; })();
  const s = []; for (let f = f0; f < L.length; f += 8) s.push((L[f].s0 >>> 0).toString(16));
  const rolls = []; for (let f = f0; f < L.length; f++) { let x = L[f].s0; for (const [ra, mx] of L[f].c) { const q = require('../pmrng_core.js').randInt(x, mx); if (ra === '80277518') rolls.push([f, q[1]]); if (mx === 100 && ra !== '80146d54' && N.pb != null && f >= N.pb) rolls.push([f, q[1], 'pb']); x = q[0]; } }
  out.runs.push({ name: path.basename(fn), aclate: r.aclate || 0, f0, n: L.length, death, inputs: N.inputs, c0s: N.c0s.map(c => ({ c0: c, s0: (L[c].s0 >>> 0).toString(16), nc: firstCoin(c) })), dec: N.dec.map(d => ({ f: d.f, prof: d.prof, G: d.G, wait: !!d.wait })), pb: N.pb != null ? N.pb : null, rolls, s });
}
fs.writeFileSync(process.argv[2], JSON.stringify(out));
console.log(out.runs.length, 'runs', fs.statSync(process.argv[2]).size, 'bytes');
