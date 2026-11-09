/* v84: Power Bounce with Normal Boots (pmrng_core.js jrpb5n / jrpb6n / hwpb6n) against the emulator
 * (fixtures/pb_nb_logs.json, pb_nb_log.py: Jr. Troopa from jr_t6_pb_target.st with the menu's boots level written to 0
 * and the route's jump charge 12; Hallway Bowser from boss_2302_goomba_menu.st (Goombario, Normal Boots) with charge 6;
 * Jr. Troopa with boots level 2 as the Ultra Boots control). Per case, from the seed written at the confirm frame:
 *  - the profile's frames: every cap roll value the game drew (rand_int(100), caller 0x802A1168) equals the model's, on
 *    the same frame, and every frame's other non-coin draws equal the profile's effects up to the last roll it needs;
 *  - the cap rule: the game stopped bouncing at the first roll over its chance (BaseHitChance 200 x chance / 100);
 *  - R.works with the profile = the game's outcome (6+: the first four rolls pass; Jr. 5+: the first three);
 *  - Normal Boots timing: rolls 26 frames apart from +77 (Jr.) / +73 (Hallway); Ultra 27 from +78 (the control: timing and
 *    cap rule only; the hit draws follow the charge, and 12 is not the Ultra route's).
 * usage: node test_pb_nb.js */
'use strict';
const fs = require('fs'), path = require('path'), R = require('./pmrng_core.js');
const FX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'pb_nb_logs.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
const CH = { jrpb6n: [140, 98, 68, 47, 32, 22, 15, 10], hwpb6n: [130, 84, 54, 35, 22, 14, 9, 5], jrpb6: [140, 98, 68, 47, 32, 22, 15, 10] };
function simRolls(prof, seed, nc, nR) {     // the profile's per-frame model (as R.works), the roll values on their frames
  let s = seed >>> 0; const out = [], draws = {}, P = R.PROFILES[prof], last = P.rolls[P.rolls.length - 1].at;
  for (let t = 0; t <= last; t++) {
    const fx = P.effects[t]; if (fx) { for (const mx of fx) s = R.randInt(s, mx)[0]; draws[t] = fx.slice(); }
    for (const r0 of P.rolls) if (r0.at === t) { const r = R.randInt(s, 100); s = r[0]; out.push([t, r[1]]); }
    if (t === nc) { const r = R.randInt(s, 100); s = r[0]; nc = t + (r[1] >= 70 ? 48 : 24); }
    s = R.adv(s);
  }
  return { rolls: out.slice(0, nR), draws, last };
}
for (const [k, G] of Object.entries(FX)) {
  let rollsOk = 0, drawsOk = 0, capOk = 0, worksOk = 0; const n = G.cases.length;
  for (const c of G.cases) {
    const seed = parseInt(c.seed, 16), nc = c.coins.length ? c.coins[0] : 1e9, P = R.PROFILES[G.prof], nR = Math.min(c.rolls.length, P.rolls.length);
    const M = simRolls(G.prof, seed, nc, nR);
    if (JSON.stringify(M.rolls) === JSON.stringify(c.rolls.slice(0, nR))) rollsOk++; else console.log(k + ' ' + c.seed + ': model rolls ' + JSON.stringify(M.rolls) + ' game ' + JSON.stringify(c.rolls));
    // the other draws up to the profile's last roll
    const lastF = c.rolls.length > nR ? M.last : Math.min(M.last, c.rolls.length ? c.rolls[c.rolls.length - 1][0] : 0);
    let dOk = true; for (let t = 0; t <= lastF; t++) { const g = (c.draws[t] || []).join(), m = (M.draws[t] || []).join(); if (g !== m) { dOk = false; console.log(k + ' ' + c.seed + ' frame ' + t + ': model ' + m + ' game ' + g); break; } }
    if (dOk) drawsOk++;
    const ch = CH[G.prof], firstFail = c.rolls.findIndex((r, i) => r[1] > ch[i]);
    if (firstFail === c.rolls.length - 1 || (firstFail < 0 && c.hp_after <= 0)) capOk++; else console.log(k + ' ' + c.seed + ': cap rule, first fail ' + firstFail + ' of ' + c.rolls.length);
    const pass = c.rolls.slice(0, P.rolls.length).filter((r, i) => r[1] <= ch[i]).length === P.rolls.length && c.rolls.slice(0, P.rolls.length).every((r, i) => r[1] <= ch[i]);
    if (R.works(seed, nc, 0, 0, P) === pass) worksOk++;
  }
  console.log(k + ' (' + G.prof + ', boots ' + G.boots + ', charge ' + G.charge + '): rolls ' + rollsOk + '/' + n + ', draws ' + drawsOk + '/' + n + ', cap rule ' + capOk + '/' + n + ', works ' + worksOk + '/' + n);
  if (G.boots === 0) check(n >= 4 && rollsOk === n && drawsOk === n && capOk === n && worksOk === n, k + ': the profile matches every emulator run');
  else check(capOk === n, k + ' (control: Ultra Boots at charge 12, not the Ultra route\'s charge, so its draw counts are not jrpb6\'s): the cap rule holds');
  const at = G.cases[0].rolls.map(r => r[0]);
  if (G.boots === 0) check(at.every((f, i) => f === at[0] + 26 * i), k + ': Normal Boots cap rolls every 26 frames from +' + at[0] + ' (' + at.join(', ') + ')');
  else check(at.every((f, i) => f === 78 + 27 * i), k + ': Ultra Boots cap rolls every 27 frames from +78 (' + at.join(', ') + ')');
}
check(R.TOP.jrpb5n === 'jrpb6n' && R.PROFILES.jrpb5n.rolls.length === 3 && R.PROFILES.hwpb6n.rolls.length === 4, 'Jr. 5+ aims at 6+; Hallway 6+ = four rolls');
console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
