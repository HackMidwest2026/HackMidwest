/* The page's Final Bowser T1-T4 model (charge_live/fb14_live.js fbStep) against the emulator, frame by frame: 32 logs of
 * fb2_route/t14_log.py (T1 Super Charge + Cloud Nine, T2 Charge + Do Nothing, T3 Jammin' Jelly + Do Nothing, T4 Charge +
 * Do Nothing with the Draining Shockwave; 8 seeds each, different menu waits, popup presses and confirm frames) in
 * fixtures/fb14_logs.json (fb2_route/t14_fixture.py: the seed before every frame, the nuisance t14model.py fits). From the
 * log's first frame the page's state must give the emulator's seed on every frame up to the dodge test, and on every
 * frame of the log after a miss (after a hit Mario's HP and Peach's wish draw more: not modelled, the route has failed).
 * v86: Bowser's AI is fbVars + the decomp's whole turn (test_fb14_ai.js); the logs' history is none (T1-T3: normal attacks only,
 * T4: the wave branch), as v74's t4 flag had it. + 16 logs at 10 HP (fixtures/fb14_logs_hp10.json).
 * usage: node test_fb14_model.js */
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'charge_live', 'fb14_live.js'), 'utf8');
const window = {}, stub = 'const FRAME = 1000 / 29.97, num = () => 0, slog = () => {}, $ = () => null, isRoute = () => false, RT = () => [], routeStep = 0, st = {}, V = {}, CHG = {};\n';
new Function('window', stub + src)(window);
// v86: + 16 logs with Mario at 10 HP (the runner's T1-T4 on console; fixtures/fb14_logs_hp10.json, the route_build MARIO_HP=10
// build): the tests and the misses are the same draws
const F = window.__fb14, X = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_logs.json'), 'utf8')).concat(JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_logs_hp10.json'), 'utf8')));
const OFF = 1000; let bad = 0, frames = 0, tests = 0, testsOk = 0;
for (const L of X) {
  const buf = Buffer.from(L.s0, 'base64'), s0 = i => buf.readUInt32LE(4 * i);
  const ph = [(((L.ph[0] - OFF) % 130) + 130) % 130, (((L.ph[1] - OFF) % 220) + 220) % 220];
  const st0 = { s: s0(0), nc: L.nc + OFF, f: L.f0 + OFF, c: Uint8Array.from({ length: 20 }, (_, j) => L.aura[j]), ph, l: 0, w: 1, resp: new Uint8Array(64), ev: [], wv: -1e9, lv: -1e9, rg: 0, prev: null, out: {}, sh: [], from: 0, lw: 1, err: 0 };
  // (the build's attack the turn before, when it rules Body Slam / Claw out: t14model.check's flags)
  if (L.flags && L.turn > 1) { if (!L.flags[0]) st0.out[L.turn - 1] = { atk: 'slam' }; else if (!L.flags[1]) st0.out[L.turn - 1] = { atk: 'claw' }; }
  const ev = (k, f, extra) => Object.assign({ k, f: f + OFF }, extra || {});
  if (L.turn !== 3) st0.ev.push(ev('chg', 13), ev('chg', 16)); else st0.ev.push(ev('jelly', 118));
  if (L.turn === 1) { for (let i = 200; i < 210; i++) st0.ev.push(ev('puff', L.P + i)); st0.ev.push(ev('ai', L.P + 332, { turn: 1 })); }
  else st0.ev.push(ev('ai', L.P + 13, { turn: L.turn }));
  st0.ev.sort((a, b) => a.f - b.f);
  const hit = L.test && L.test.value >= 50, last = hit ? L.test.test + 1 : L.n - 1 + L.f0;
  let firstBad = null, n = 0;
  for (let i = 0; i < L.n && L.f0 + i <= last; i++) {
    if ((st0.s >>> 0) !== s0(i) && firstBad == null) firstBad = L.f0 + i;
    n++; F.fbStep(st0);
  }
  frames += n; if (firstBad != null) bad++;
  const o = st0.out[L.turn]; tests++; const tOk = o && L.test && o.v === L.test.value && o.atk === L.test.attack; if (tOk) testsOk++;
  console.log(L.name.padEnd(32), 'turn', L.turn, 'frames', String(n).padStart(4), firstBad == null ? 'exact' : 'FIRST MISMATCH AT ' + firstBad, '| test', o ? o.atk + ' ' + o.v + (o.ok ? ' (ok)' : '') : '-', 'emulator', L.test ? L.test.attack + ' ' + L.test.value : '-', tOk ? '' : 'DIFFERENT');
}
console.log(bad === 0 && testsOk === tests ? 'PASS' : 'FAIL', ':', X.length - bad, '/', X.length, 'logs exact over', frames, 'frames; tests', testsOk, '/', tests);
process.exit(bad === 0 && testsOk === tests ? 0 : 1);
