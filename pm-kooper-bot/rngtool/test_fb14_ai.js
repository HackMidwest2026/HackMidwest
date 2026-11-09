/* v86: the Final Bowser T1-T4 tracker's Bowser AI (charge_live/fb14_live.js fbStep 'ai' with fbVars) is the decomp's
 * EVS_TakeTurn_Inner as pmrng_core.js fbnbAi has it (emulator-checked against 60 Bowser turns: test_fbnb_ai.js). v74-v85
 * had only the normal attacks and, on T4 only, RandInt(100) < 75 / RandInt(110) < 20 for the wave: RandInt(110) 20-29 (the
 * Lightning Blast) went on to RandInt(80) as a normal attack; no Recover check (Mario at 10 HP on console, Bowser at 74 HP
 * or less: RandInt(100) first). Here, for 20000 random cases (turn 1-6, a random attack history, the Recover gap on or
 * off, a random seed), the tracker's AI frame must draw exactly what fbnbAi draws and pick the same attack; the attack's
 * test (Cloud Nine's dodge) comes FB14_DELTA frames later. Also: the counters from the history (TurnsSince*, RecoversLeft).
 * usage: node test_fb14_ai.js */
'use strict';
const fs = require('fs'), path = require('path'), R = require('./pmrng_core.js');
const src = fs.readFileSync(path.join(__dirname, 'charge_live', 'fb14_live.js'), 'utf8');
const window = {}, stub = 'const FRAME = 1000 / 29.97, num = () => 0, slog = () => {}, $ = () => null, isRoute = () => false, RT = () => [], routeStep = 0, st = {}, V = {}, CHG = {};\n';
new Function('window', stub + src)(window);
const F = window.__fb14;
let fails = 0; const check = (ok, msg) => { if (!ok) fails++; console.log((ok ? 'ok   ' : 'FAIL ') + msg); };
let x = 0x9e3779b9; const rnd = n => { x = (Math.imul(x, 1103515245) + 12345) >>> 0; return (x >>> 8) % n; };
const ATK = ['fire', 'claw', 'slam', 'wave', 'lightning', 'recover'];
let same = 0, N = 20000; const byAtk = {}; let firstBad = null;
for (let i = 0; i < N; i++) {
  const turn = 1 + rnd(6), rg = rnd(2), out = {};
  for (let k = 1; k < turn; k++) { const a = ATK[rnd(rg ? 6 : 5)]; out[k] = { atk: a }; }
  const seed = (rnd(1 << 16) << 16 | rnd(1 << 16)) >>> 0;
  // the page's state: one frame with Bowser's AI on it and nothing else drawn (no bolts, no aura, the coin far away)
  const S = F.fbNew({ s: seed, nc: 1e9, f: 100, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1, rg, out: Object.assign({}, out) });
  S.ev.push({ k: 'ai', f: 100, turn });
  F.fbStep(S);
  // fbnbAi from the vars the decomp would hold before that turn
  const V = F.fbVars ? F.fbVars(S, turn) : null;
  const v0 = { turn: turn - 1, sinceShock: V.sinceShock - 1, sinceStar: V.sinceStar - 1, sinceClaw: V.sinceClaw - 1, sinceSlam: V.sinceSlam - 1, sinceRecover: V.sinceRecover - 1, recovers: V.recovers, enchanted: true, charged: true, hpGap: rg ? 26 : 0 };
  const M = R.fbnbAi(seed, v0);
  const sAfter = R.randInt(M.s, 1)[0];            // the step's own draw at the end of the frame
  const ok = S.out[turn].atk === M.atk && (S.s >>> 0) === (sAfter >>> 0);
  if (ok) same++; else if (!firstBad) firstBad = { turn, rg, out, page: S.out[turn].atk, model: M.atk, draws: M.draws };
  byAtk[M.atk] = (byAtk[M.atk] || 0) + 1;
}
console.log('attacks', JSON.stringify(byAtk));
check(same === N, 'the tracker\'s AI = fbnbAi (draws and attack) in ' + same + ' / ' + N + ' cases' + (firstBad ? ' first bad ' + JSON.stringify(firstBad) : ''));
check(byAtk.lightning > 100 && byAtk.recover > 100 && byAtk.wave > 100, 'the cases cover the Lightning Blast, Recover and the wave');
// the counters
{ const S = F.fbNew({ s: 1, nc: 1e9, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1, out: { 1: { atk: 'claw' }, 2: { atk: 'fire' }, 3: { atk: 'slam' } } });
  const V = F.fbVars(S, 4); check(V.turn === 4 && V.sinceClaw === 3 && V.sinceSlam === 1 && V.sinceShock === 4 && V.recovers === 3, 'T4 after claw / fire / slam: ' + JSON.stringify(V)); }
// T4 with the route's history (no wave yet): RandInt(110) 20-29 is the Lightning Blast, no RandInt(80) after it
{ let found = 0, okLb = 0;
  for (let s = 1; found < 50 && s < 5e7; s += 7919) {
    const S = F.fbNew({ s, nc: 1e9, f: 100, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1, out: { 1: { atk: 'fire' }, 2: { atk: 'fire' }, 3: { atk: 'fire' } } }); S.ev.push({ k: 'ai', f: 100, turn: 4 });
    let t = R.randInt(s, 100); if (t[1] < 75) continue; const u = R.randInt(t[0], 110); if (u[1] < 20 || u[1] >= 30) continue;
    found++; F.fbStep(S); if (S.out[4].atk === 'lightning' && (S.s >>> 0) === (R.randInt(u[0], 1)[0] >>> 0) && S.ev.some(e => e.k === 'test' && e.f === 100 + F.FB14_DELTA.lightning)) okLb++;
  }
  check(found === 50 && okLb === 50, 'T4: RandInt(100) >= 75 then RandInt(110) 20-29 = the Lightning Blast, nothing more drawn by the AI, its test on AI + ' + F.FB14_DELTA.lightning + ' (' + okLb + ' / ' + found + ')'); }
// the Lightning Blast frame by frame against the emulator (fixtures/fb14_lb_logs.json: fb2_route/lb_log.py T4 runs, Mario at
// 10 HP, Cloud Nine up; lb_model.py fits the aura / lightning / coin): from the Do Nothing confirm the page's state must give
// the emulator's seed on every frame to the test, and after a miss on every frame to the next menu (+30)
{ const X = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_lb_logs.json'), 'utf8')), OFF = 1000;
  let exact = 0, frames = 0, tests = 0, miss = 0;
  for (const L of X.runs) {
    const buf = Buffer.from(L.s0, 'base64'), s0 = i => buf.readUInt32LE(4 * i);
    const ph = [(((L.ph[0] - OFF) % 130) + 130) % 130, (((L.ph[1] - OFF) % 220) + 220) % 220];
    const S = F.fbNew({ s: s0(0), nc: L.nc + OFF, f: OFF, c: Uint8Array.from(L.aura), ph, l: 0, w: 1, out: { 1: { atk: 'fire' }, 2: { atk: 'fire' }, 3: { atk: 'fire' } } });
    S.ev.push({ k: 'ai', f: OFF + 13, turn: 4 });
    let bad = null; for (let i = 0; i < L.n; i++) { if ((S.s >>> 0) !== s0(i) && bad == null) bad = i; F.fbStep(S); }
    frames += L.n; if (bad == null) exact++; else console.log('lb ' + L.seed + ' W ' + L.W + ': first mismatch on frame ' + bad);
    const o = S.out[4]; if (o && o.atk === 'lightning' && o.v === L.test && o.miss === (L.test < 50) && !o.ok) tests++; if (L.miss) miss++;
  }
  check(exact === X.runs.length && tests === X.runs.length && miss >= 8, 'the Lightning Blast against the emulator: ' + exact + ' / ' + X.runs.length + ' runs exact over ' + frames + ' frames (' + miss + ' misses to the next menu), test value and attack ' + tests + ' / ' + X.runs.length + '; a blast that misses is not T4\'s goal (ok false)'); }
console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
