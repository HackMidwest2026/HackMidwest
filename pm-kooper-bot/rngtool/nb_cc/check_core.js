/* v85: the page's RNG core (pmrng_core.js: TURNS nb_*, buildEv, frameEv, the jrcc_gch / jrcc_hb / hwcc_gch profiles and
 * their wait-mode twins) against the emulator logs of the Normal Boots route (nb_cc/gch_log.py, nb_cc/jr_route_log.py),
 * frame by frame, as jr_charge/jc_check_core.js does for Ultra Boots:
 *  - from each Super Charge confirm's seed and the first coin frame after it (what a Charge lock gives) and the logged
 *    confirm / cancel-A frames alone, every frame's gRandSeed up to a death, the end of the modelled draws or the log;
 *  - every Close Call: the page's profile from the state at the deciding press (the cancel A, or the Headbonk confirm) and
 *    the wait-mode profile from the state at the Charge confirm when the box ran out, against the game's roll (< 30).
 * module: check(logObject) -> { segs: [...], outs: [...] }; CLI: node check_core.js LOG.json ... (exit 1 on any mismatch) */
'use strict';
const fs = require('fs'), path = require('path');
const R = require(path.join(__dirname, '..', 'pmrng_core.js'));
const COIN = '80146d54', CC = '80277518', K = R.NB_K;
const PB5N = { pre: { 52: Array(11).fill(359), 77: [100], 78: Array(11).fill(359), 103: [100], 104: Array(11).fill(359), 129: [100] }, post: {} };
R.TURNS.__nb_pb = PB5N;
// a log -> frames [{ s0, c: [[ra, mx]], hp }], inputs [{ f, id }], deciding presses [{ f, prof, waitF }]
function normalize(r) {
  const out = { inputs: [], dec: [], name: r.name || r.seed };
  if (r.marks) {                       // gch_log.py: one turn from Mario's menu
    const L = r.log.map((x, i) => ({ s0: i ? parseInt(r.log[i - 1].seed, 16) : null, c: x.c, hp: x.hp }));
    out.L = L; const hw = /2302/.test(r.state), M = r.marks, G = M.G[0], P = M.P ? M.P[0] : G + K.none;
    out.inputs.push({ f: M.mario[0], id: hw ? 'hw_charge' : 'jr_charge' });
    if (r.move === 'charge') {
      out.inputs.push({ f: G, id: 'nb_gch' });
      const id = r.hp >= 6 ? (hw ? null : 'nb_jrhit') : hw ? 'nb_hwcc' : 'nb_jrcc';
      if (id) out.inputs.push({ f: P, id });
      if (r.hp < 6) out.dec.push({ f: P, prof: hw ? 'hwcc_gch' : 'jrcc_gch', G, wait: !M.P || r.K < K.lo || r.K > K.hi });
    } else { out.inputs.push({ f: G, id: 'nb_hb' }); out.dec.push({ f: G, prof: 'jrcc_hb', G }); }
    out.c0s = [M.mario[0]];
    return out;
  }
  // jr_route_log.py: the whole fight
  const L = r.log.map(x => ({ s0: parseInt(x.s0, 16), c: x.c, hp: x.hp })); out.L = L;
  const E = r.ev, at = n => E.find(x => x.name === n);
  out.c0s = [];
  for (const x of E) {
    const m = /^T(\d) (.*)$/.exec(x.name); if (!m) continue; const t = +m[1], what = m[2];
    if (what === 'Super Charge') { out.inputs.push({ f: x.f, id: 'jr_charge' }); out.c0s.push(x.f); }
    else if (what === 'Maple Syrup') out.inputs.push({ f: x.f, id: 'nb_syrup' });
    else if (what === 'Goombario Charge') {
      const c = at('T' + t + ' cancel A'), P = c ? c.f : x.f + K.none;
      out.inputs.push({ f: x.f, id: 'nb_gch' }); out.inputs.push({ f: P, id: t === 1 ? 'nb_jrhit' : 'nb_jrcc' });
      if (t > 1) out.dec.push({ f: P, prof: 'jrcc_gch', G: x.f, wait: !c });
    } else if (what === 'Headbonk') { out.inputs.push({ f: x.f, id: 'nb_hb' }); out.dec.push({ f: x.f, prof: 'jrcc_hb', G: x.f }); }
    else if (what === 'Whacka') out.inputs.push({ f: x.f, id: 'nb_whacka' });
    else if (what === 'Do Nothing') out.inputs.push({ f: x.f, id: 'jr_nothing_hit' });
    else if (what === 'Power Bounce') { out.inputs.push({ f: x.f, id: '__nb_pb' }); out.pb = x.f; }
  }
  return out;
}
function rollAfter(L, f) { for (let g = f; g < Math.min(L.length, f + 400); g++) { let s = L[g].s0; for (const [ra, mx] of L[g].c) { const q = R.randInt(s, mx); if (ra === CC) return q[1]; s = q[0]; } } return null; }
function check(r) {
  const N = normalize(r), L = N.L, segs = [], outs = [];
  const deathAt = f0 => { for (let f = f0 + 1; f < L.length; f++) if (L[f].hp <= 0) return f; return L.length; };
  for (const c0 of N.c0s) {
    if (L[c0].s0 == null) continue;
    const nc = (() => { for (let f = c0; f < L.length; f++) if (L[f].c.some(x => x[0] === COIN)) return f; return 1e9; })();
    const evs = N.inputs.filter(x => x.f >= c0), ev = R.buildEv(evs), S = { s: L[c0].s0 >>> 0, nc, inst: [] };
    let last = 0; for (const f of ev.keys()) last = Math.max(last, f);
    const dz = deathAt(c0), end = Math.min(L.length, last + 1, dz); let ok = true, n = 0, msg = '';
    for (let f = c0; f < end; f++) {
      if (L[f].s0 == null || (S.s >>> 0) !== (L[f].s0 >>> 0)) { const pc = evs.filter(x => x.f <= f).pop(); ok = false; msg = 'mismatch at ' + f + ' (+' + (f - pc.f) + ' after ' + pc.id + ')'; break; }
      for (const d of N.dec) {
        if (d.f === f && !S.inst.length && !(S.extra && S.extra.size) && S.ccAt == null && !d.done1 && f >= c0) { d.done1 = true; const game = rollAfter(L, f); if (game != null) outs.push({ kind: d.prof, f, page: R.works(S.s, S.nc, f, f, R.PROFILES[d.prof]), game: game < 30, roll: game }); }
        // the wait mode: from the state at the Charge confirm (eio not yet created), the box run out
        if (d.wait && d.G === f && !S.inst.length && !d.done2 && f >= c0) { d.done2 = true; const game = rollAfter(L, f); const wp = d.prof === 'hwcc_gch' ? 'hwcc_gchw' : 'jrcc_gchw'; if (game != null) outs.push({ kind: wp, f, page: R.works(S.s, S.nc, f, f, R.PROFILES[wp]), game: game < 30, roll: game }); }
      }
      R.frameEv(S, f, ev); n++;
    }
    segs.push({ c0, ok, n, msg, why: end === dz ? 'death' : end === last + 1 ? 'end of modelled draws' : 'end of log', ids: [...new Set(evs.filter(x => x.f < end).map(x => x.id))] });
  }
  if (N.pb != null) {          // Power Bounce 5+ from the state at its confirm (the carried model)
    const f = N.pb, caps = [140, 98, 68];
    const vals = [77, 103, 129].map(o => { const x = L[f + o]; if (!x) return null; let s = x.s0; for (const [ra, mx] of x.c) { const q = R.randInt(s, mx); if (mx === 100 && ra !== COIN) return q[1]; s = q[0]; } return null; });
    if (vals[0] != null) { let h = 2; for (let i = 0; i < 3; i++) { if (vals[i] == null || vals[i] > caps[i]) break; h++; } outs.push({ kind: 'jrpb5n', f, game: h >= 5, vals, needState: true }); }
  }
  return { name: N.name, segs, outs };
}
module.exports = { check, normalize };
if (require.main === module) {
  let bad = 0, segs = 0, frames = 0, nout = 0;
  for (const fn of process.argv.slice(2)) {
    const r = JSON.parse(fs.readFileSync(fn, 'utf8')); r.name = path.basename(fn); const c = check(r);
    for (const s of c.segs) { segs++; frames += s.n; if (!s.ok) bad++; console.log(c.name + ' from ' + s.c0 + ': ' + (s.ok ? 'OK ' + s.n + ' frames (' + s.why + ')' : 'FAIL ' + s.msg) + ' | ' + s.ids.join(',')); }
    for (const o of c.outs) if (!o.needState) { nout++; const g = o.page === o.game; if (!g) bad++; console.log('   ' + o.kind + ' at ' + o.f + ': page ' + o.page + ', game ' + o.game + ' (roll ' + o.roll + ')' + (g ? '' : '  <-- DIFFERENT')); }
  }
  console.log('summary: ' + segs + ' segments, ' + frames + ' frames, ' + nout + ' outcomes, ' + bad + ' bad');
  process.exit(bad ? 1 : 0);
}
