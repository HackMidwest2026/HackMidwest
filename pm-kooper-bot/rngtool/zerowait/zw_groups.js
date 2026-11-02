/* How many distinct RNG futures the Hallway T1 Spiny Flip leaves (33 impact frames x guard or not), and their weights.
 * usage: node zw_groups.js N */
const R = require('../pmrng_core.js');
const N = +process.argv[2] || 50; let rs = 12345; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0);
function groupsFor(seed, guardKnown) {
  const evs = [{ f: 0, id: 'hw_charge' }, { f: 260, id: 'hw_spiny' }];
  const imps = []; for (let i = 138; i <= 170; i++) for (const g of guardKnown == null ? [1, 0] : [guardKnown]) imps.push(i * 2 + g);
  const bs = imps.map(h => [h, R.baseAfter(seed, R.buildEv(evs.map(e => e.id === 'hw_spiny' ? Object.assign({ imp: h >> 1, guard: !!(h & 1) }, e) : e)), 260)]).filter(x => x[1]);
  const Fc = Math.max(...bs.map(x => x[1].F)); const groups = new Map();
  for (const [h, b] of bs) {
    const S = { s: b.seed >>> 0, nc: b.F, inst: [] }; let f = b.F;
    while (!(f >= Fc && f === S.nc)) { R.frameEv(S, f, null); f++; }
    const k = S.s + ':' + f; if (!groups.has(k)) groups.set(k, { seed: S.s, F: f, n: 0, branch: b.branch }); groups.get(k).n++;
  }
  return [...groups.values()].sort((a, b) => b.n - a.n);
}
if (require.main === module) {
  for (const gk of [null, 1, 0]) {
    const cnt = [], top = [];
    for (let i = 0; i < N; i++) { const g = groupsFor(rnd(), gk); const tot = g.reduce((a, x) => a + x.n, 0); cnt.push(g.length); top.push(g[0].n / tot); }
    cnt.sort((a, b) => a - b); top.sort((a, b) => a - b);
    console.log('guard', gk == null ? 'unknown' : gk ? 'yes' : 'no', '| groups median', cnt[N >> 1], 'range', cnt[0], '-', cnt[N - 1], '| biggest group weight median', top[N >> 1].toFixed(2), 'min', top[0].toFixed(2));
  }
}
module.exports = { groupsFor };
