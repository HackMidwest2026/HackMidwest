/* Edge non-shines: short glances (C-up ~3 s, hidden ~1 s). Each gap also knows m1 draws after the last shine and m2
 * before the next first shine that were visible and did not shine. Check the true seed is still found with those
 * constraints, and count how many seeds fit in a 2^24 window with and without them. */
const R = require('./pmrng_core.js');
const seed = (process.argv[2] ? parseInt(process.argv[2], 16) : 0x1234abcd) >>> 0, MARGIN = 10;
let s = seed, nc = 5; const draws = [];
for (let f = 0; f < 3000; f++) { if (f === nc) { const before = s; s = R.adv(s); const sh = s >= R.SHINE_MIN; draws.push({ f, before, sh }); nc = f + (sh ? 48 : 24); } s = R.adv(s); }
const vis = []; for (let a = 40; a < 2900; a += 120) vis.push([a, a + 90]);
const st = vis.map(([a, b]) => { const d = draws.filter(q => q.f >= a && q.f < b); const i0 = d.findIndex(q => q.sh), i1 = d.map(q => q.sh).lastIndexOf(true); return i0 < 0 ? null : { d: d.slice(i0, i1 + 1), a, b }; }).filter(x => x && x.d.length >= 1);
const count = (lo, hi, f0) => { let k = 0; for (let i = 1; ; i++) { const f = f0 + 48 + 24 * (i - 1); if (f > hi - MARGIN) return Math.min(k, 4); k++; } };
const segs = st.map((x, i) => {
  const g = { pattern: x.d.map(q => q.sh ? 'S' : '.').join('') };
  if (i) { const p = st[i - 1], E = x.d[0].f - p.d[p.d.length - 1].f; g.lo = E - 2; g.hi = E + 2;
    let m1 = 0; for (let f = p.d[p.d.length - 1].f + 48; f <= p.b - MARGIN && m1 < 4; f += 24) m1++;
    let m2 = 0; for (let i2 = 1; x.d[0].f - (24 * i2 + 24) >= x.a + MARGIN && m2 < 4; i2++) m2++;
    g.m1 = m1; g.m2 = m2; }
  return g; });
console.log(segs.map(g => g.pattern + (g.m1 != null ? ` [${g.m1},${g.m2}]` : '')).join(' | '));
const want = st[st.length - 1].d[0].before >>> 0;
const anchor = segs.map((g, i) => [g.pattern.length, i]).sort((a, b) => b[0] - a[0])[0][1], tT = R.adv(st[anchor].d[0].before);
const lo = Math.max(0, tT - 8388608), hi = tT + 8388608;
const withM = R.searchChain(segs, anchor, lo, hi, 100000);
const noM = R.searchChain(segs.map(g => Object.assign({}, g, { m1: 0, m2: 0 })), anchor, lo, hi, 100000);
console.log('fits in 2^24 window: with edges', withM.length, 'without', noM.length);
const ok = withM.includes(want) && noM.includes(want) && withM.length <= noM.length;
console.log(ok ? 'PASS' : 'FAIL');
