/* v86: Normal Boots, Final Bowser phase 2: Goombario's Charge turn, Bowser's turn after it and the Power Bounce against him,
 * against the emulator (fixtures/fbnb_p2_logs.json: fb2_route/nb_p2_state.py, nb_cc/gch_log.py, pb_nb_log.py,
 * nb_p2_fixture.py; charge_live/README.md v86 section 3). What a lock for the phase-2 Power Bounce would carry:
 *  - Goombario's Charge: his two energy_in_out creations on G + 14 and G + 17 (as in Jr. Troopa's arena, v85);
 *  - Bowser's AI on P + 16 (P = the box A, or G + 133 when the box runs out), its RandInt calls = pmrng_core.js fbnbAi with
 *    the T2 vars (Peach Beam on T1: TurnsSinceStarBeam 1);
 *  - the Close Call roll on AI + 52 / 55 / 62 (Body Slam / Fire Breath / Claw Swipe), < 30 = Mario (1 HP) lives; then
 *    nothing but the arena's draws to the next menu, on roll + 101 / 134 / 83;
 *  - the Power Bounce: the first hit on d + 45, cap rolls on d + 70 + 26 k, each passing roll's hit one frame after it;
 *    chance 60 (rolls of 120, 72, 43, 25 ... pass), the first two bounces free.
 * usage: node test_fbnb_turn.js */
'use strict';
const fs = require('fs'), path = require('path'), R = require('./pmrng_core.js');
const X = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fbnb_p2_logs.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
const DELTA = { slam: 52, fire: 55, claw: 62 }, MENU = { slam: 101, fire: 134, claw: 83 };
let gc = 0, ai = 0, draws = 0, atk = 0, cc = 0, life = 0, menu = 0, lucky = 0; const seen = {};
for (const r of X.charge) {
  if (r.gc.join() === '14,17') gc++;
  const P = r.P != null ? r.P : r.G + 133; if (r.ai - P === 16) ai++;
  const M = R.fbnbAi(parseInt(r.aiSeed, 16), X.vars);
  if (M.draws.length === r.aiDraws.length && M.draws.every((d, i) => d[0] === r.aiDraws[i][0] && d[1] === r.aiDraws[i][1])) draws++;
  if (r.cc - r.ai === DELTA[M.atk]) atk++; seen[M.atk] = (seen[M.atk] || 0) + 1;
  if (r.ccv < 30 === r.hpEnd > 0) life++;
  if (r.ccv < 30) { lucky++; if (r.menu - r.cc === MENU[M.atk]) menu++; }
  cc++;
}
const n = X.charge.length;
check(n >= 20 && gc === n, 'Goombario\'s Charge: his creations on G + 14 and G + 17 in ' + gc + ' / ' + n + ' runs');
check(ai === n, 'Bowser\'s AI on the box A + 16 (or G + 133 + 16) in ' + ai + ' / ' + n);
check(draws === n, 'his RandInt calls = fbnbAi with the T2 vars in ' + draws + ' / ' + n);
check(atk === n && Object.keys(seen).length === 3, 'the Close Call roll on AI + 52 / 55 / 62 by the attack fbnbAi picks in ' + atk + ' / ' + n + ' ' + JSON.stringify(seen));
check(life === n && lucky >= 6, 'roll < 30 = Mario (1 HP) lives, else he falls: ' + life + ' / ' + n + ' (' + lucky + ' Close Calls)');
check(menu === lucky, 'after a Close Call the next menu on roll + 101 / 134 / 83 in ' + menu + ' / ' + lucky);
// the Power Bounce
const TH = [120, 72, 43, 25, 15, 9, 5, 3];
let pbOk = 0;
for (const c of X.pb.cases) {
  const rollsAt = c.rolls.every(([f], k) => f === 70 + 26 * k), stop = c.rolls.findIndex(([, v], k) => v > TH[k]);
  const nHits = stop < 0 ? c.rolls.length + 1 : stop + 2;
  const hitsAt = c.hits.length === nHits && c.hits.every(([f], k) => f === (k === 0 ? 45 : 70 + 26 * (k - 1) + 1));
  if (rollsAt && hitsAt) pbOk++; else console.log('pb', c.seed, JSON.stringify(c.rolls), JSON.stringify(c.hits));
}
check(pbOk === X.pb.cases.length && X.pb.cases.length >= 8, 'Power Bounce (Normal Boots) on Final Bowser: hits on d + 45 and one frame after each passing roll, rolls on d + 70 + 26 k, chance 60: ' + pbOk + ' / ' + X.pb.cases.length);
console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
