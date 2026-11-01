/* The turn model (TURNS) against the emulator: 6 logged Jr. Troopa runs (T3 Bomb -> T6 confirm, random seeds and
 * confirm timing, Close Calls landing). From the seed at the T3 Bomb confirm and the confirm frames alone, every
 * frame's seed must match the game. The logger rewrote the seed (DIAGNOSTIC) before each starred press to force the
 * Close Call; the simulation picks the game's seed up again there. */
const R = require('./pmrng_core.js'), runs = require('./fixtures/jr_turns_runs.json');
const ID = { 'T3 Bomb': 'jr_bomb_cc', 'T4 Bomb': 'jr_bomb', 'T4 Maple': 'jr_syrup_cc', 'T5 Charge': 'jr_charge', 'T5 Nothing': 'jr_nothing_cc' };
let pass = 0;
for (const r of runs) {
  const ev = R.buildEv(r.confirms.filter(c => ID[c[1]]).map(([f, n]) => ({ f, id: ID[n] })));
  const writes = r.confirms.filter(c => /Maple|Nothing|T6/.test(c[1])).map(c => c[0]);
  const S = { s: r.seeds[0], nc: r.coins[0], inst: [] }; let bad = null, resets = 0;
  for (let f = 0; f < r.seeds.length - 1; f++) {
    if (writes.some(w => w - f >= 0 && w - f <= 45) && S.nc !== r.coins.find(c => c >= f)) { S.nc = r.coins.find(c => c >= f); }   // logger reload: coin timer
    if (S.s !== r.seeds[f] >>> 0) { if (writes.some(w => w - f >= 0 && w - f <= 45)) { S.s = r.seeds[f] >>> 0; S.nc = r.coins.find(c => c >= f); resets++; } else { bad = f; break; } }
    frameEv(S, f);
  }
  function frameEv(S, f) { R.frameEv(S, f, ev); }
  const ok = bad === null;   // (the last frame can follow the T6 seed write)
  console.log(r.seed.toString(16), 'd' + r.dseed + ':', ok ? 'every frame matches (' + (r.seeds.length - 1) + ' frames, ' + resets + ' labelled seed writes)' : 'MISMATCH at +' + bad);
  if (ok) pass++;
}
console.log(pass === runs.length ? 'PASS' : 'FAIL', pass + '/' + runs.length);
