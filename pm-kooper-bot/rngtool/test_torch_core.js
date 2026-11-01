/* Torch-room model against the emulator: 12 logged runs (Duplighost room, Heart Block room; 6 seeds each, 1500 frames).
 * The coin pattern seen in the room must match the true seed with the room's torch phase. Other phases may also match
 * (torches landing in the same gaps between coin draws so far): they give the same seed, so they are the same lock. */
const R = require('./pmrng_core.js'), fs = require('fs'), path = require('path');
const dir = '/tmp/claude-0/pm/bot1/data'; let pass = 0, n = 0;
for (const fn of fs.readdirSync(dir).filter(f => f.startsWith('torch_'))) {
  const j = JSON.parse(fs.readFileSync(path.join(dir, fn))); const coins = []; let s0 = null;
  j.toks.forEach((tk, f) => { if (tk.includes('C')) coins.push(f); });
  const torchF = j.toks.findIndex(tk => tk.length >= 12 && !tk.includes('C'));
  // the pattern from the first coin draw: S/. per draw
  const f0 = coins[0], seed0 = j.seeds[f0] >>> 0; let s = seed0, pat = '';
  for (let i = 0; i < coins.length; i++) {          // the shine decision of each coin draw, read from the logged seeds
    const before = j.seeds[coins[i]] >>> 0; pat += R.adv(before) >= R.SHINE_MIN ? 'S' : '.';
  }
  const ph = ((torchF - f0) % 50 + 50) % 50;
  const ok = R.matchesTorch(seed0, pat, ph), others = [...Array(50).keys()].filter(p => p !== ph && R.matchesTorch(seed0, pat, p));
  n++; if (ok) pass++;
  console.log(fn, 'pattern', pat.length, 'draws, phase', ph, ok ? 'MATCH' : 'NO MATCH', 'other phases matching:', others.length);
}
console.log(pass === n ? 'PASS' : 'FAIL', pass + '/' + n);
