// (log analysis) usage: node backcheck.js tolFrames fromSec seed t0ms: walk the coin draws back from a lock and match earlier shines
const R = require('/home/user/HackMidwest/pm-kooper-bot/rngtool/pmrng_core.js');
const L = require('./run3.json').events, FR = 1000 / 30, TOL = +(process.argv[2] || 10), FROM = +(process.argv[3] || 560) * 1000;
const t0 = +(process.argv[5] || 612371), lockSeed = (+(process.argv[4] || 1380350928)) >>> 0;
const obs = L.filter(e => e.ev === 'shine' && e.at < t0 - 100 && e.at > FROM).map(e => e.at).reverse();
const backN = (x, n) => { for (let i = 0; i < n; i++) x = R.back(x); return x; };
const SH = R.SHINE_MIN; const res = []; let nodes = 0;
function dfs(x, f, k, errs) {
  if (++nodes > 5e6) return;
  if (k >= obs.length) { res.push(errs); return; }
  const want = (obs[k] - t0) / FR;
  if (f < want - TOL) return;
  for (const [n, isS] of [[48, true], [24, false]]) {
    const y = backN(x, n); if ((y >= SH) !== isS) continue;
    const fp = f - n, xp = R.back(y);
    if (isS && Math.abs(fp - want) <= TOL) dfs(xp, fp, k + 1, errs.concat([+(fp - want).toFixed(1)]));
    else dfs(xp, fp, k, errs);
  }
}
dfs(lockSeed, 0, 0, []);
console.log('observed (s):', obs.map(x => (x / 1000).toFixed(1)).join(' '), '| paths', res.length, 'nodes', nodes);
const seen = new Set(); for (const r of res) { const k = r.join(','); if (!seen.has(k)) { seen.add(k); if (seen.size < 15) console.log(' frame errors (game frame - wallclock frame):', k); } }
