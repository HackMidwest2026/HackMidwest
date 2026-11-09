/* v84: Bowser's phase-2 attack choice (pmrng_core.js fbnbAi, from the decomp) against emulator ground truth
 * (fixtures/p2ai_logs.json, fb2_route/p2ai_log.py: random actor vars, Star Rod flag, charges and HP written at
 * Lakilester's menu, then Bowser's turn). Per case:
 *  - every logged frame replays: the seed before it, each rand_int (caller, max) in order, gives the seed after it;
 *  - Bowser's AI: the first frame after the Do Nothing confirm with script RandInt calls; from the seed just before them,
 *    fbnbAi with the case's vars must make the same RandInt calls (max and value) and choose the attack the game did:
 *    read back after the turn (TurnsSinceBodySlam / ClawSwipe / Shockwave reset, the Star Rod flag set, Recover's HP),
 *    else Fire Breath or Lightning Blast by the Close Call roll's frame (Fire Breath: AI + 55; with Mario at full HP, the
 *    Recover cases, there is no roll and the two are not told apart);
 *  - the vars after the turn equal the model's (the counters the script adds and resets).
 * Also the route's blind per-turn chance (fbnbTurnBlind) against a Monte Carlo of fbnbAi.
 * usage: node test_fbnb_ai.js */
'use strict';
const fs = require('fs'), path = require('path'), R = require('./pmrng_core.js');
const FX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'p2ai_logs.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
const EVT = 'evt';
let replayOk = 0, frames = 0, aiOk = 0, atkOk = 0, varsOk = 0, unknown = 0; const byAtk = {}, lagOf = {};
for (const c of FX.cases) {
  // 1. replay every frame
  let bad = 0;
  for (const r of c.rows) { let s = r.s0 >>> 0; for (const [nm, mx] of r.d) s = R.randInt(s, mx)[0]; frames++; if (s === (r.s1 >>> 0)) replayOk++; else bad++; }
  // 2. the AI frame: the first frame with script RandInt calls after the confirm
  const ai = c.rows.find(r => r.f > 0 && r.d.some(([nm]) => nm === EVT));
  if (!ai) { check(false, 'case ' + c.k + ': no AI frame'); continue; }
  let s = ai.s0 >>> 0; const got = []; let seedAt = null;
  for (const [nm, mx] of ai.d) { if (nm === EVT && seedAt == null) seedAt = s; const r = R.randInt(s, mx); if (nm === EVT) got.push([mx, r[1]]); s = r[0]; }
  const v = Object.assign({}, c.v, { enchanted: !!c.v.enchanted, charged: !!c.v.charged }), M = R.fbnbAi(seedAt, v);
  const same = M.draws.length <= got.length && M.draws.every((d, i) => d[0] === got[i][0] && d[1] === got[i][1]);
  if (same) aiOk++; else console.log('case ' + c.k + ' draws: model ' + JSON.stringify(M.draws) + ' game ' + JSON.stringify(got) + ' vars ' + JSON.stringify(c.v));
  // 3. the attack the game used
  const A = c.after; let game;
  if (A.sinceSlam === 0) game = 'slam'; else if (A.sinceClaw === 0) game = 'claw'; else if (A.sinceShock === 0) game = 'wave';
  else if (A.sinceRecover === 0) game = 'recover'; else if (A.enchanted && !c.v.enchanted) game = 'starrod';
  else { const t = (c.tests || []).find(f => f > ai.f); game = t != null && t - ai.f === 55 ? 'fire' : t != null ? 'lightning' : 'unknown'; if (t != null) (lagOf[game] = lagOf[game] || new Set()).add(t - ai.f); }
  byAtk[game] = (byAtk[game] || 0) + 1;
  if (game === 'unknown' && (M.atk === 'fire' || M.atk === 'lightning')) unknown++; else if (game === M.atk) atkOk++; else console.log('case ' + c.k + ' attack: model ' + M.atk + ' game ' + game + ' (tests ' + JSON.stringify((c.tests || []).slice(0, 2)) + ', AI ' + ai.f + ')');
  // 4. the vars after the turn
  const mv = M.v, vOk = ['turn', 'sinceShock', 'sinceStar', 'sinceClaw', 'sinceSlam'].every(k => mv[k] === A[k]) || (game === 'starrod' && mv.turn === A.turn);
  if (vOk) varsOk++; else console.log('case ' + c.k + ' vars: model ' + JSON.stringify(mv) + ' game ' + JSON.stringify(A));
  check(!bad, 'case ' + c.k + ': ' + bad + ' frames do not replay');
}
const n = FX.cases.length;
console.log('cases ' + n + ' (attacks ' + JSON.stringify(byAtk) + '): frames replayed ' + replayOk + ' / ' + frames + ', AI draws ' + aiOk + ' / ' + n + ', attack ' + atkOk + ' / ' + (n - unknown) + ' (' + unknown + ' Fire Breath / Lightning Blast with no Close Call roll to tell them apart: Mario at full HP), Close Call at AI + ' + JSON.stringify(Object.fromEntries(Object.entries(lagOf).map(([k, v]) => [k, [...v]]))) + ', vars after ' + varsOk + ' / ' + n);
check(n >= 40, 'at least 40 emulator cases');
check(aiOk === n, 'the model makes the game\'s RandInt calls (max and value) in every case');
check(atkOk === n - unknown && unknown <= n / 5, 'the model chooses the game\'s attack in every case it can be read');
check(varsOk === n, 'the vars after the turn match');
check(['wave', 'starrod'].every(a => byAtk[a] >= 2) && ['slam', 'claw', 'fire'].filter(a => byAtk[a]).length >= 2, 'the cases cover the Star Rod, the wave and the normal attacks');
// 5. the blind per-turn chance against a Monte Carlo of the model
let x = 0x1234567;
for (const t of [2, 3, 4, 6, 8]) {
  let ok = 0; const N = 100000;
  for (let i = 0; i < N; i++) { x = (Math.imul(x, 1103515245) + 12345) >>> 0; const r = R.fbnbAi(x, R.fbnbVars(t)); if (r.atk !== 'starrod' && r.atk !== 'wave' && R.randInt(r.s, 100)[1] < 30) ok++; }
  const p = R.fbnbTurnBlind(t); console.log('T' + t + ': blind ' + p.toFixed(4) + ', Monte Carlo ' + (ok / N).toFixed(4));
  check(Math.abs(ok / N - p) < 0.006, 'T' + t + ' blind chance = Monte Carlo');
}
console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
