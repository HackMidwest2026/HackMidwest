/* The page's own RNG core (pmrng_core.js: TURNS, buildEv, frameEv, the jrcc_* / jrpb* profiles) against emulator runs of
 * the Jr. Troopa route (jc_turns.py logs), frame by frame, the way dup_charge/dc_check.py checks dc_model.py:
 *  - from each Charge confirm's seed and the first coin frame after it (what a Charge lock gives) and the confirm frames
 *    alone, every frame's gRandSeed up to a death (Life Shroom revive: not modelled), the end of the modelled draws or the
 *    end of the log; the turns at 10 HP after a revive use the _hit variants (jr_syrup_hit, jr_nothing_hit), T1's Bomb
 *    jr_bomb_t1 (Jr. Troopa's hit at 10 HP);
 *  - every Close Call and Power Bounce outcome: R.works with the planned profile from the state at that confirm, against
 *    the game's roll values (Close Call: the roll at 0x80277518 < 30; Power Bounce: the cap rolls on +78/+105/+132/+159).
 * usage: node jc_check_core.js LOG.json [...]   -> one line per Charge segment, per outcome, and a summary */
'use strict';
const fs = require('fs'), path = require('path');
const R = require(path.join(__dirname, '..', 'pmrng_core.js'));
const COIN = 0x80146D54, CC_RA = 0x80277518;
const ID = { charge: 'jr_charge', bomb: 'jr_bomb', bomb_t1: 'jr_bomb_t1', bomb_cc: 'jr_bomb_cc', syrup_cc: 'jr_syrup_cc', syrup_hit: 'jr_syrup_hit',
  nothing_cc: 'jr_nothing_cc', nothing_hit: 'jr_nothing_hit', whacka: 'jr_whacka' };
const PROFS = { bomb_cc: 'jrcc_bomb', syrup_cc: 'jrcc_syrup', nothing_cc: 'jrcc_nothing' };
// Power Bounce: its draws as the jrpb6 profile has them (hit effects, then the cap rolls), for the frame check up to the 4th roll
const PB = { pre: { 52: Array(11).fill(359), 78: [100], 79: Array(11).fill(359), 105: [100], 106: Array(10).fill(359), 132: [100], 133: Array(10).fill(359), 159: [100] }, post: {} };
R.TURNS.__jr_pb = PB;
const tot = { seg: 0, segOk: 0, frames: 0, out: 0, outOk: 0, cc: 0, pb: 0, byTurn: {} };
for (const fn of process.argv.slice(2)) {
  const r = JSON.parse(fs.readFileSync(fn, 'utf8')), L = r.log, C = r.confirms.filter(c => c[2]);
  const name = path.basename(fn);
  const charges = C.filter(c => c[2] === 'charge').map(c => c[0]);
  const deathAt = f0 => { for (let f = f0 + 1; f < L.length; f++) if (L[f].hp <= 0) return f; return L.length; };
  // segments: from each Charge confirm (what a lock gives), and from the first confirm after each death (the turns at 10 HP
  // after a revive with no Charge before them: the T4 Maple Syrup after a T3 death), with the coin phase read off the log
  const starts = charges.map((c0, k) => ({ c0, label: 'Charge #' + (k + 1) }));
  for (let f = 1; f < L.length; f++) if (L[f].hp <= 0 && L[f - 1].hp > 0) { const nx = C.find(c => c[0] > f && c[2] !== 'charge'); if (nx && !charges.some(c => c > f && c < nx[0])) starts.push({ c0: nx[0], label: nx[1] + ' after the death at ' + f }); }
  starts.forEach(({ c0, label }) => {
    const nc = (() => { for (let f = c0; f < L.length; f++) if (L[f].c.some(x => x[0] === COIN)) return f; return 1e9; })();
    const evs = C.filter(c => c[0] >= c0).map(([f, , t]) => ({ f, id: t === 'pb' ? '__jr_pb' : ID[t] })).filter(e => e.id);
    const ev = R.buildEv(evs), S = { s: L[c0].s0 >>> 0, nc, inst: [] };
    let last = 0; for (const f of ev.keys()) last = Math.max(last, f);
    const dz = deathAt(c0), end = Math.min(L.length, last + 1, dz);
    const ids = [...new Set(evs.filter(e => e.f < end).map(e => e.id.replace('__', '')))];
    let ok = true, n = 0, msg = '';
    const outs = [];
    for (let f = c0; f < end; f++) {
      if ((S.s >>> 0) !== (L[f].s0 >>> 0)) {
        const pc = C.filter(c => c[0] <= f).pop();
        ok = false; msg = 'MISMATCH at frame ' + f + ' (+' + (f - pc[0]) + ' after ' + pc[1] + ')'; break;
      }
      // an outcome confirm on this frame: the page's profile from this state (no events pending from earlier confirms)
      const here = C.find(c => c[0] === f && (PROFS[c[2]] || c[2] === 'pb'));
      if (here && !S.inst.length) {
        const t = here[2];
        if (PROFS[t]) {
          const pred = R.works(S.s, S.nc, f, f, R.PROFILES[PROFS[t]]);
          const roll = (() => { for (let g = f; g < Math.min(L.length, f + 400); g++) { const x = L[g].c.find(y => y[0] === CC_RA); if (x) return x[2]; } return null; })();
          if (roll != null) outs.push({ t, f, pred, game: roll < 30, roll });
        } else {
          const caps = [140, 98, 68, 47], vals = [78, 105, 132, 159].map(o => { const x = (L[f + o] || { c: [] }).c.find(y => y[1] === 100 && y[0] !== COIN); return x ? x[2] : null; });
          let hits = 2; for (let i = 0; i < 4; i++) { if (vals[i] == null || vals[i] > caps[i]) break; hits++; }
          const p5 = R.works(S.s, S.nc, f, f, R.PROFILES.jrpb5), p6 = R.works(S.s, S.nc, f, f, R.PROFILES.jrpb6);
          if (vals[0] != null) outs.push({ t, f, pred: p6 ? 6 : p5 ? 5 : '<5', game: hits >= 6 ? 6 : hits === 5 ? 5 : '<5', vals });
        }
      }
      R.frameEv(S, f, ev); n++;
    }
    tot.seg++; tot.frames += n; if (ok) tot.segOk++;
    for (const id of ids) { const b = tot.byTurn[id] = tot.byTurn[id] || { seg: 0, ok: 0 }; b.seg++; if (ok) b.ok++; }
    const why = end === dz ? 'death at ' + dz : end === last + 1 ? 'end of modelled draws' : 'end of log';
    console.log(name + ' from ' + label + ': ' + (ok ? 'OK ' + n + ' frames (' + why + ')' : 'FAIL ' + msg) + ' | turns ' + ids.join(','));
    for (const o of outs) {
      tot.out++; const good = o.pred === o.game; if (good) tot.outOk++; if (o.t === 'pb') tot.pb++; else tot.cc++;
      console.log('   ' + o.t + ' at ' + o.f + ': page ' + o.pred + ', game ' + o.game + (o.roll != null ? ' (roll ' + o.roll + ')' : ' (caps ' + o.vals.join('/') + ')') + (good ? '' : '  <-- DIFFERENT'));
    }
  });
}
console.log('summary: ' + tot.segOk + '/' + tot.seg + ' Charge segments match frame by frame (' + tot.frames + ' frames); outcomes ' + tot.outOk + '/' + tot.out + ' (' + tot.cc + ' Close Calls, ' + tot.pb + ' Power Bounces); per turn kind (segments containing it, all frames matched): ' +
  Object.entries(tot.byTurn).map(([k, v]) => k + ' ' + v.ok + '/' + v.seg).join(', '));
process.exit(tot.segOk === tot.seg && tot.outOk === tot.out ? 0 : 1);
