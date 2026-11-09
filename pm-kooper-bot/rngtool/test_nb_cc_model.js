// v85: Goombario's Charge, its cancel A, Maple Syrup, Headbonk x2 and the enemy turns after them on the Normal Boots route:
// the page's core (pmrng_core.js TURNS nb_*, the jrcc_gch / jrcc_gchw / jrcc_hb / hwcc_gch / hwcc_gchw profiles) against the
// emulator (fixtures/nb_cc_logs.json from nb_cc/gch_log.py and nb_cc/jr_route_log.py): every 8th frame's gRandSeed from each
// Super Charge confirm (what a Charge lock gives) and the logged confirm / cancel frames alone, every Close Call outcome,
// the T7 Power Bounce 5+ from the carried state, and the cancel window (A on +73..+132 ends Goombario's turn 5 frames later).
'use strict';
const R = require('./pmrng_core.js'), FX = require('./fixtures/nb_cc_logs.json');
let fails = 0; const ok = (c, m) => { if (!c) { fails++; console.log('FAIL ' + m); } };
const K = R.NB_K;
// the T7 Power Bounce's draws as the jrpb5n profile has them (hit effects, the cap rolls), for the frame check to the 3rd roll
R.TURNS.__nb_pb = { pre: { 52: Array(11).fill(359), 77: [100], 78: Array(11).fill(359), 103: [100], 104: Array(11).fill(359), 129: [100] }, post: {} };
// 1. the window
for (const r of FX.kscan.rows) {
  const inWin = r.K >= K.lo && r.K <= K.hi;
  ok(r.end === (inWin ? r.K : K.none) + K.back, 'K ' + r.K + ': his turn ends on +' + r.end);
  ok(r.barBack === r.end && r.barOff === 3 && r.marioBarOff === 2, 'K ' + r.K + ': bar ' + r.barOff + '/' + r.barBack + ' (Mario ' + r.marioBarOff + ')');
}
console.log('cancel window: A on +' + K.lo + '..+' + K.hi + ' ends the turn on A + ' + K.back + ', else +' + (K.none + K.back) + ' (' + FX.kscan.rows.length + ' runs)');
// 2. frame by frame, and the outcomes
const tot = { seg: 0, frames: 0, cc: 0, wait: 0, hb: 0, pb: 0, hw: 0, acFail: 0 };
for (const run of FX.runs) {
  const failAc = run.aclate >= 3;
  const hbF = (run.inputs.find(x => x.id === 'nb_hb') || {}).f;
  for (const c of run.c0s) {
    const evs = run.inputs.filter(x => x.f >= c.c0), ev = R.buildEv(evs), S = { s: parseInt(c.s0, 16) >>> 0, nc: c.nc, inst: [] };
    let last = 0; for (const f of ev.keys()) last = Math.max(last, f); if (evs.some(x => x.id === 'nb_hwcc')) last += 72;
    const end = Math.min(run.n, last + 1, run.death != null ? run.death : 1e9); let bad = null;
    const dec = run.dec.map(d => Object.assign({}, d));
    for (let f = c.c0; f < end; f++) {
      if ((f - run.f0) % 8 === 0 && f >= run.f0) { const want = parseInt(run.s[(f - run.f0) / 8], 16) >>> 0; if ((S.s >>> 0) !== want && bad == null) { bad = f; break; } }
      for (const d of dec) {
        const roll = (run.rolls.find(x => x[0] >= d.f && x[2] !== 'pb') || [])[1];
        if (d.f === f && !d.d1 && !S.inst.length && roll != null) { d.d1 = true; const p = R.works(S.s, S.nc, f, f, R.PROFILES[d.prof]); if (!(failAc && d.prof === 'jrcc_hb')) { ok(p === roll < 30, run.name + ' ' + d.prof + ' at ' + f + ': page ' + p + ', roll ' + roll); tot[d.prof === 'jrcc_hb' ? 'hb' : 'cc']++; if (d.prof === 'hwcc_gch') tot.hw++; } }
        if (d.wait && d.G === f && !d.d2 && roll != null) { d.d2 = true; const wp = d.prof + 'w'; const p = R.works(S.s, S.nc, f, f, R.PROFILES[wp]); ok(p === roll < 30, run.name + ' ' + wp + ' at ' + f + ': page ' + p + ', roll ' + roll); tot.wait++; }
      }
      if (run.pb === f && !failAc) {
        const caps = [140, 98, 68], v = run.rolls.filter(x => x[2] === 'pb' && x[0] >= f).slice(0, 3).map(x => x[1]);
        let h = 2; for (let i = 0; i < 3; i++) { if (v[i] == null || v[i] > caps[i]) break; h++; }
        ok(R.works(S.s, S.nc, f, f, R.PROFILES.jrpb5n) === (h >= 5), run.name + ' T7 Power Bounce 5+: rolls ' + v); tot.pb++;
      }
      R.frameEv(S, f, ev); tot.frames++;
    }
    tot.seg++;
    if (failAc) { ok(bad != null && bad > hbF + 80 && bad <= hbF + 88, run.name + ': a late action command (one bonk) must break the model right after the 2nd hit (+80), got ' + bad); tot.acFail++; }
    else ok(bad == null, run.name + ' from ' + c.c0 + ': mismatch at ' + bad);
  }
}
console.log('frame by frame: ' + tot.seg + ' segments, ' + tot.frames + ' frames; Close Calls ' + tot.cc + ' cancel (' + tot.hw + ' Hallway), ' + tot.wait + ' wait mode, ' + tot.hb + ' Headbonk; Power Bounce ' + tot.pb + '; late action command breaks it: ' + tot.acFail);
ok(tot.cc >= 40 && tot.wait >= 8 && tot.hb >= 8 && tot.pb >= 8 && tot.hw >= 20, 'coverage');
console.log(fails ? fails + ' FAILED' : 'all ok'); process.exit(fails ? 1 : 0);
