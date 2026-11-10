/* v87: the page's Final Bowser model (charge_live/fb14_live.js fbStep) carried across T1 -> T4 against continuous emulator
 * logs (fb2_route/chain_log.py: T1 menu to 60 frames after T4's next menu, every lever on the first frame that makes
 * Bowser miss, some with a guard A in Bowser's turn; fixtures/fb14_chain_logs.json from fb2_route/chain_fixture.py). From
 * the log's first frame, with the true inputs (Charges, the Jelly, Cloud Nine, Do Nothing) and the nuisance the fixture
 * found (aura pattern, lightning phases, first coin), the model must give the emulator's seed on every frame of the log
 * and the emulator's dodge test values. T4's wave: either particle order (FB14_WAVE_POST / _B) may be the log's.
 * usage: node test_fb14_chain.js */
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'charge_live', 'fb14_live.js'), 'utf8');
const window = {}, stub = 'const FRAME = 1000 / 29.97, num = () => 0, slog = () => {}, $ = () => null, isRoute = () => false, RT = () => [], routeStep = 0, st = {}, V = {}, CHG = {};\n';
new Function('window', stub + src)(window);
const F = window.__fb14, X = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_chain_logs.json'), 'utf8'));
let bad = 0, frames = 0, tests = 0, testsOk = 0;
for (const L of X) {
  const buf = Buffer.from(L.s0, 'base64'), s0 = i => buf.readUInt32LE(4 * i);
  const run = wb => {
    const S = F.fbNew({ s: s0(0), nc: L.nc, f: L.f0, c: Uint8Array.from(L.aura), ph: [L.ph[0], L.ph[1]], l: 0, w: 1, from: L.f0, wb });
    for (const T of L.turns) {
      if (T.mkind === 'charge') { S.ev.push({ k: 'chg', f: T.M + 13 }, { k: 'chg', f: T.M + 16 }); }
      else S.ev.push({ k: 'jelly', f: T.M + F.FB14_JELLY });
      if (T.pkind === 'cloud_nine') { for (let i = 200; i < 210; i++) S.ev.push({ k: 'puff', f: T.P + i }); S.ev.push({ k: 'ai', f: T.P + 332, turn: T.turn }); }
      else S.ev.push({ k: 'ai', f: T.P + 13, turn: T.turn });
    }
    S.ev.sort((a, b) => a.f - b.f);
    // every frame; inside T4's wave after its test (AI + 73 .. + 150) the particles may run in another order (seen here
    // in 1 of 7 waves: the per-frame split differs, the totals do not), so the stream must only be back by AI + 150; a
    // guarded T4 (A on P + 87: Lakilester blocks the wave, not modelled) only to its test
    const t4 = L.turns[3], ai4 = t4.P + 13, test4 = L.tests.length >= 4 ? L.tests[3][0] : 1e9, blocked = L.guard && !(t4.ko && t4.ko[0]);
    let first = null, inWave = 0;
    for (let i = 0; i < L.n - 1; i++) { const f = L.f0 + i;
      if ((S.s >>> 0) !== s0(i)) { if (blocked && f > test4) break; if (f > test4 && f < ai4 + 150) { inWave++; S.s = s0(i); } else { first = f; break; } }
      F.fbStep(S); }
    return { first, out: S.out, inWave, blocked };
  };
  const a = run(0), b = run(1), r = a.first == null ? a : b.first == null ? b : (a.first >= b.first ? a : b), which = r === a ? 'A' : 'B';
  frames += r.first != null ? r.first - L.f0 : r.blocked ? L.tests[3][0] - L.f0 : L.n; if (r.first != null) bad++;
  const tv = Object.keys(r.out).sort().map(k => r.out[k].v), ok = L.tests.filter((t, i) => tv[i] === t[1]).length; tests += L.tests.length; testsOk += ok;
  console.log((r.first == null ? 'ok   ' : 'FAIL ') + L.name.padEnd(22) + ' seed ' + L.seed + (L.guard ? ' guarded' : '') + ' frames ' + L.n + (r.first == null ? ' exact' : ' first mismatch ' + r.first) + (r.blocked ? ' (guarded T4: Lakilester blocked the wave, checked to its test)' : '') + (r.inWave ? ' (' + r.inWave + ' wave frames in another particle order, the stream back after it)' : '') + ' | wave order ' + which + ' | tests ' + ok + ' / ' + L.tests.length + ' ' + JSON.stringify(L.tests.map(t => t[1])) + ' model ' + JSON.stringify(tv) + ' ' + Object.keys(r.out).map(k => r.out[k].atk).join(','));
  if (ok !== L.tests.length) bad++;
}
console.log((bad ? 'FAIL' : 'PASS') + ' : ' + (X.length - bad) + ' / ' + X.length + ' T1-T4 chains exact over ' + frames + ' frames; dodge tests ' + testsOk + ' / ' + tests);
process.exit(bad ? 1 : 0);
