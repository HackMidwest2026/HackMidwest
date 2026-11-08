/* v78 (v79: the throw is the Spiny Flip's impact - 24; hw_spiny imp): Hallway Bowser T1 with Mario at 3 HP (Danger, Close Call) against the emulator (fixtures/hw3_logs.json: 15 runs of
 * hw3 logging, DIAGNOSTIC HP 3 and chosen seeds; the Spiny Flip thrown with A on a chosen frame). From the seed at the
 * Charge confirm, the Charge / Spiny Flip confirm frames and the throw frame, every frame's seed must match the game up to
 * the Close Call roll, the roll's frame and value (Lucky < 30) must be the game's, and after a Lucky roll every frame to
 * T2's menu must match (nothing more is drawn). Runs whose Spiny missed Bowser (the reticle off him: no impact) are off the
 * route and only listed. Also: the throw frame moves the roll (different throws give different rolls), which is why the
 * page keeps the impact frames open and carries the roll as a fallback (charge_live/hwcc_live.js) rather than beeping it. */
const R = require('./pmrng_core.js'), runs = require('./fixtures/hw3_logs.json');
let pass = 0, n = 0, lucky = 0; const br = {};
for (const r of runs) {
  if (!r.spinyHit) { console.log(r.name, 'Spiny Flip off Bowser (no impact): off the route, skipped'); continue; }
  n++;
  const ev = R.buildEv([{ f: r.charge, id: 'hw_charge' }, { f: r.spiny, id: 'hw_spiny', imp: r.throw - r.spiny + 24, danger: true }]);
  const S = { s: r.seeds[0] >>> 0, nc: r.coin[0], inst: [] }; let bad = null, last = r.seeds.length - 1;
  for (let f = 0; f < last; f++) {
    if (S.s !== r.seeds[f] >>> 0) { bad = f; break; }
    R.frameEv(S, f, ev);
    if (S.ccHit) { last = f + 1; break; }      // the hit kills Mario: not modelled past the roll
  }
  const cc = S.cc, gcc = r.cc[0], ccOk = cc && gcc && cc.f === gcc[0], luckyOk = cc && (cc.lucky === (r.hpEnd > 0));
  const ok = bad === null && ccOk && luckyOk; if (ok) pass++; if (cc && cc.lucky) lucky++; br[S.branch] = (br[S.branch] || 0) + 1;
  console.log(r.name, 'throw +' + (r.throw - r.spiny), S.branch, 'roll', cc ? cc.v + ' at +' + (cc.f - r.spiny) : '-', cc && cc.lucky ? 'Lucky' : 'hit (Mario dies)', 'game HP', r.hpEnd,
    ok ? 'every frame matches (' + last + ' frames' + (cc && cc.lucky ? ', to T2\'s menu' : ', to the roll') + ')' : 'MISMATCH at ' + bad + ' cc ' + JSON.stringify(cc) + ' game ' + JSON.stringify(gcc));
}
// the lever: from one run's state at the Spiny Flip confirm, the roll for each throw frame in the aim window
{ const r = runs.find(x => x.spinyHit), vals = [];
  for (let t = r.spiny + 55; t <= r.spiny + 114; t++) {
    const ev = R.buildEv([{ f: r.charge, id: 'hw_charge' }, { f: r.spiny, id: 'hw_spiny', imp: t - r.spiny + 24, danger: true }]);
    const S = { s: r.seeds[0] >>> 0, nc: r.coin[0], inst: [] }; for (let f = 0; f < t + 200 && !S.cc; f++) R.frameEv(S, f, ev); vals.push(S.cc.lucky ? 1 : 0);
  }
  const k = vals.reduce((a, b) => a + b, 0); console.log('throws +55..+114 from', r.name + ':', vals.join(''), k + '/' + vals.length, 'Lucky');
  if (!(k > 3 && k < vals.length - 3)) { console.log('FAIL the throw frame does not move the roll'); pass = -1; } }
console.log('attacks', JSON.stringify(br), 'Lucky', lucky);
console.log(pass === n ? 'PASS' : 'FAIL', pass + '/' + n);
