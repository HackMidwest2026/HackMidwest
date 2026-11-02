// (log analysis) usage: node chainscan.js log.json fromSec toSec part parts   [W=lo,hi to force gap windows]
const R = require('/home/user/HackMidwest/pm-kooper-bot/rngtool/pmrng_core.js');
const L = require(process.argv[2]).events, T0 = +process.argv[3] * 1000, T1 = +process.argv[4] * 1000, part = +process.argv[5], parts = +process.argv[6];
const FRAME = 1000 / 30, FLICKER = 3500;
const W = process.env.W; const gapWin = (a, b, hid) => { const E = Math.round((b - a) / FRAME); if (W) { const [l, h] = W.split(",").map(Number); return [Math.max(24, E - l), E + h]; } return hid <= 1200 ? [Math.max(24, E - 2), E + 2] : hid <= FLICKER ? [Math.max(24, E - 2), E + 8] : [Math.max(48, E - 30), E + 60]; };
const st = []; let cur = [], hid = null;
for (const e of L) { if (e.t < T0) continue; if (e.t > T1) break;
  if (e.ev === 'shine') cur.push(e.at);
  if (e.ev === 'coinBack') { if (cur.length) st.push({ taps: cur, hid }); cur = []; hid = e.hiddenMs; } }
if (cur.length) st.push({ taps: cur, hid });
const segs = st.map((x, i) => { const g = { pattern: R.patternFromTaps(x.taps).pattern }; if (i) [g.lo, g.hi] = gapWin(st[i - 1].taps[st[i - 1].taps.length - 1], x.taps[0], x.hid); return g; });
let anchor = 0; segs.forEach((g, i) => { if (g.pattern.length > segs[anchor].pattern.length) anchor = i; });
if (part === 0) console.log(segs.map(g => g.pattern + (g.lo ? ` (${g.lo}-${g.hi})` : '')).join(' | '));
const N0 = R.SHINE_MIN, N = 4294967296 - N0, lo = N0 + Math.floor(N * part / parts), hi = N0 + Math.floor(N * (part + 1) / parts), t0 = Date.now();
const r = R.searchChain(segs, anchor, lo, hi, 100000);
console.log('part', part, 'found', r.length, r.slice(0, 5).map(v => (v >>> 0).toString(16)).join(','), ((Date.now() - t0) / 1000).toFixed(0) + 's');
