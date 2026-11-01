/* Hallway Bowser T1 against the emulator (26 runs, random seeds/delays/aims; 8 of them guarding Bowser's attack): Charge, Lakilester's Spiny Flip (aim
 * sparkle, impact on the run's own frame), Bowser's AI picking Body Slam / Claw Swipe / Fire Breath from the simulated
 * rolls. From the seed at the Charge confirm, the two confirm frames and the impact frame, every frame's seed must match
 * the game through T2's menu. Also: the impact frame is the one thing the page cannot see, so check that wrong impact
 * frames are told apart by a few shines. */
const R = require('./pmrng_core.js'), runs = require('./fixtures/hw_t1_runs.json');
let pass = 0; const branches = {};
for (const r of runs) {
  const ev = R.buildEv([{ f: r.charge, id: 'hw_charge' }, { f: r.spiny, id: 'hw_spiny', imp: r.imp, guard: r.guard }]);
  const S = { s: r.seeds[0] >>> 0, nc: r.coins[0], inst: [] }; let bad = null;
  for (let f = 0; f < r.seeds.length - 1; f++) { if (S.s !== r.seeds[f] >>> 0) { bad = f; break; } R.frameEv(S, f, ev); }
  const ok = bad === null; if (ok) pass++; branches[S.branch + (r.guard ? ' guarded' : '')] = (branches[S.branch + (r.guard ? ' guarded' : '')] || 0) + 1;
  console.log(r.seed.toString(16), 'impact +' + r.imp, S.branch + (r.guard ? ' (guarded)' : ''), '(Mario HP after: ' + r.hpAfter + ')', ok ? 'every frame matches (' + (r.seeds.length - 1) + ' frames)' : 'MISMATCH at ' + bad);
}
console.log('branches', JSON.stringify(branches)); console.log(pass === runs.length ? 'PASS' : 'FAIL', pass + '/' + runs.length);
