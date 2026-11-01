/* Chain search: simulate the coin through a run where it is hidden part of the time (the coin keeps drawing, room
 * transitions add a few fast frames), keep only the shines seen in each visible stretch, and check that searchChain
 * finds the true seed. Usage: node test_chain_core.js [seedhex] [full] */
const R = require('./pmrng_core.js');
const seed = (process.argv[2] ? parseInt(process.argv[2], 16) : 0x9e3779b9) >>> 0;
let s = seed, nc = 5; const draws = [];
for (let f = 0; f < 4000; f++) { if (f === nc) { const before = s; s = R.adv(s); const sh = s >= R.SHINE_MIN; draws.push({ f, before, sh }); nc = f + (sh ? 48 : 24); } s = R.adv(s); }
// visible stretches in game frames (~15 s on / ~10 s off); measured gaps are off by up to +-6 (taps) and transitions
// add ~5 fast frames that the clock does not see
const vis = [[60, 510], [810, 1230], [1530, 2000]], skew = [0, -11, 7];
const segs = vis.map(([a, b]) => { const d = draws.filter(q => q.f >= a && q.f < b); const i0 = d.findIndex(q => q.sh), i1 = d.map(q => q.sh).lastIndexOf(true); return d.slice(i0, i1 + 1); });
const BS = -Math.log2(310 / 1010), BN = -Math.log2(700 / 1010), bitsOf = p => [...p].reduce((a, c) => a + (c === 'S' ? BS : BN), 0);
let bits = 0, cost = 0; const S = segs.map((d, i) => {
  const g = { pattern: d.map(q => q.sh ? 'S' : '.').join('') }; bits += bitsOf(g.pattern);
  if (i) { const E = d[0].f - segs[i - 1][segs[i - 1].length - 1].f + skew[i]; g.lo = E - 30; g.hi = E + 60; cost += Math.log2((g.hi - g.lo) / 24 + 1); }
  console.log('seg', i, g.pattern, bitsOf(g.pattern).toFixed(1), 'bits', i ? 'gap window ' + g.lo + '..' + g.hi : ''); return g; });
console.log('bits', bits.toFixed(1), 'gap cost', cost.toFixed(1), 'net', (bits - cost).toFixed(1));
const want = segs[segs.length - 1][0].before >>> 0; let ok = true;
for (let anchor = 0; anchor < S.length; anchor++) {
  const tT = R.adv(segs[anchor][0].before); const r = R.searchChain(S, anchor, tT - 3000, tT + 3000, 64);
  console.log('anchor', anchor, 'near truth:', r.map(v => v.toString(16)), r.length === 1 && r[0] === want ? 'OK' : 'FAIL'); ok = ok && r.length === 1 && r[0] === want;
}
// carry across a gap
const c0 = R.extendCands([segs[1][0].before], S[1].pattern, S[2].pattern, S[2].lo, S[2].hi, 1000);
console.log('extendCands:', c0 && c0.map(v => v.toString(16)), c0 && c0[0] === want ? 'OK' : 'FAIL'); ok = ok && c0 && c0[0] === want;
if (process.argv[3] === 'full') {
  const anchor = S.map((g, i) => [bitsOf(g.pattern), i]).sort((a, b) => b[0] - a[0])[0][1];
  const t0 = Date.now(); const r = R.searchChain(S, anchor, 0, 4294967296, 64);
  console.log('full scan (anchor ' + anchor + ')', ((Date.now() - t0) / 1000).toFixed(1) + ' s:', r.map(v => v.toString(16)), r.length === 1 && r[0] === want ? 'UNIQUE OK' : 'CHECK');
}
console.log(ok ? 'PASS' : 'FAIL');
