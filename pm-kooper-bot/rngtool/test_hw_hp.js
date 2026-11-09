/* v79: Mario's HP in the Hallway T1 Charge tracker (charge_live/hwcc_live.js), through the built standalone page in headless
 * Chromium against the model (pmrng_core.js; its Close Call roll matches the emulator: test_hw_cc_model.js). The route has
 * Mario above 5 HP (no roll): zw.parts are v77's; the <=5 HP roll states are a fallback beside them (zw.shadow).
 *  A. The HP read: tens "1" = 10 HP, no fallback; no read = the route's HP, fallback at odds 0.1; blank = 1-9 HP, odds 0.3.
 *  B. Unknown HP, random games at 3 HP (roll; Close Call games only) or 10 HP (no roll), impact frame and guard hidden: both
 *     hypotheses are carried; after the roll the fallback holds no hit; on Time Out's target screen (the real makePlan /
 *     zwPlan) no beep is made while the roll states hold 5%+ of the weight on a frame that fails under one of them, nor while
 *     they hold 50%+; "no edge" is said when they disagree. Passes: no read / no coin, blank / no coin, no read / 1.5 s coin.
 *  C. A "1" on the bar in Bowser's turn drops the fallback; a "1" after the last roll (a Life Shroom revive) stops the
 *     tracker and Time Out says no edge.
 * usage (from rngtool/, after python3 build_page.py): node test_hw_hp.js [PAGE] [N=24] */
'use strict';
const { chromium } = require('playwright');
const SP = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad';
const PAGE = process.argv[2] || SP + '/timeout_timer/timeout_timer_standalone.html', N = +(process.argv[3] || 24);
const R = require('./pmrng_core.js');
let rs = 9191; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296;
const pick = D => { let u = rnd(); for (const [v, w] of D) { if (u < w) return v; u -= w; } return D[D.length - 1][0]; };
const PD = [[-1, 0.25], [0, 0.5], [1, 0.25]], LAGS = [[0, 0.75], [1, 0.25]], CHG_N = 48, IMPS = Array.from({ length: 33 }, (_, i) => 138 + i);
const SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];
// the true game on the tracker's clock (frame 0 = the Charge's frame 0; console lag after the rays, as chgStartTracker)
function truth(g) {
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: g.Ct, id: 'hw_spiny', imp: g.imp, guard: g.guard, danger: g.danger }]);
  const S = { s: g.seed, nc: g.q, inst: [] }; let f = 0; const shines = [];
  const step = to => { while (f < to) { if (g.lag && f === CHG_N + 2) { S.nc += g.lag; f += g.lag; continue; } if (R.frameEv(S, f, ev)) shines.push(f); f++; } };
  return { S, step, f: () => f, shines };
}
(async () => {
  const b = await chromium.launch(), p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file://' + PAGE);
  let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
  check(await p.evaluate(() => window.__tot.VERSION) === 'v84', 'page version v84');
  // A. the read -> hypotheses
  const A = await p.evaluate(() => {
    const T = window.__tot, o = {};
    T.hwHpReset(); o.ten = T.hwHpHyps('ten').odds; o.blank = T.hwHpHyps('blank').odds; o.none = T.hwHpHyps(null).odds;
    return o;
  });
  check(A.ten === 0, 'A: tens "1" = 10 HP: no roll fallback');
  check(A.none === 0.1 && A.blank === 0.3, 'A: no read = the route\'s HP with the roll fallback at odds 0.1; blank tens = odds 0.3');
  // B. unknown HP
  const MODES = { none_nocoin: { tens: 'none', coin: false }, blank_nocoin: { tens: 'blank', coin: false }, none_coin: { tens: 'none', coin: true } };
  const B = { games: 0, mixed: 0, hitsLeft: 0, rows: {} }; for (const m in MODES) B.rows[m] = { plans: 0, noEdgeHp: 0, noEdge: 0, bad: 0, real: 0, claim: 0 };
  for (let k = 0; k < N; k++) {
    const g = { seed: (rnd() * 4294967296) >>> 0, q: Math.floor(rnd() * 48), lag: pick(LAGS), Ct: 110 + Math.floor(rnd() * 120), sh: pick(SHIFTS), imp: IMPS[Math.floor(rnd() * IMPS.length)], guard: rnd() < 0.5, danger: k % 2 === 0 };
    const tg = truth(g); tg.step(g.Ct + g.imp + 44 + 90);
    if (g.danger && !(tg.S.cc && tg.S.cc.lucky)) { k--; continue; }           // Mario died: no Time Out (redraw the game)
    const menu = g.danger ? tg.S.cc.f + 135 : g.Ct + g.imp + 44 + 300, cScr = menu + 45; tg.step(cScr);
    const shines = tg.shines.filter(f => f >= menu && f <= cScr - 4), S2 = { s: tg.S.s, nc: tg.S.nc, f: tg.f() };
    B.games++;
    for (const mode in MODES) {
      const M = MODES[mode];
      const r = await p.evaluate(({ g, cScr, menu, shines, M, IMPS }) => {
        const T = window.__tot, zw = T.zw, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), ti = T.RT().findIndex(s => s.prof === 'timeout');
        document.getElementById('s-prof').value = 'endgame'; document.getElementById('s-lead').value = '1.5'; document.getElementById('s-zwwin').value = '1';
        T.setStep(hi); T.hwHpReset(); T.hwTrackerAt(g.seed, [g.q], 100000); if (M.tens === 'blank') T.HWHP.tens = Array(10).fill(0);
        const vl = +document.getElementById('s-vlag').value || 0, pf = +document.getElementById('s-pfix').value || 0, tOf = (c, van) => zw.t0 + vl + (c + van + pf) * zw.rate;
        const setNow = t => { window.__dt += t - performance.now(); };
        const cRead = g.Ct - g.sh; setNow(tOf(cRead, T.VAN.B()) + 20); T.zwInput('hw_spiny', tOf(cRead, T.VAN.B()), T.VAN.B(), IMPS);
        const o = { why: T.HWHP.why, odds: T.HWHP.odds, shadow0: zw.shadow ? zw.shadow.length : 0, main0: zw.parts.length };
        T.setStep(ti); T.zwUpdate(menu - 10);
        o.rollLeft = zw.shadow ? zw.shadow.length : 0; o.rollHit = zw.shadow ? zw.shadow.filter(q => !(q.S.cc && q.S.cc.lucky)).length : 0;
        zw.vis = []; zw.visFrom = null; zw.visTo = null; zw.visLocked = true;     // no coin: nothing watched in T2's menu
        if (M.coin) { for (const f of shines) T.zwTapF(f); zw.vis.push([menu, cScr - 4]); }
        const n0 = T.SLOG.length; setNow(tOf(cScr, 0) + 30); T.st.plan = null; T.st.msg = null; T.makePlan();
        const P = T.st.plan, logs = T.SLOG.slice(n0).map(x => x.ev);
        o.shares = T.hwHpShares(); o.msg = (T.st.msg || '').slice(0, 110); o.noEdgeHp = logs.includes('zwNoEdgeHp'); o.noEdge = logs.includes('zwNoEdge') || o.noEdgeHp;
        if (P) {
          const c = P.zwAbs, chance = L => { let v = 0, W = 0; for (const q of L) { W += q.w; for (const [d, pq] of P.PD) if (T.R.works(q.S.s >>> 0, q.S.nc, c + d, q.g, T.R.PROFILES.timeout)) v += q.w * pq; } return W ? v / W : null; };
          const done = q => !q.S.inst.length && !(q.S.extra && q.S.extra.size) && q.S.ccAt == null;
          o.plan = { target: c, p: P.mix.p, pRoll: zw.shadow ? chance(zw.shadow.filter(done)) : null, pNoRoll: chance(zw.parts.filter(done)) };
        }
        return o;
      }, { g, cScr, menu, shines, M, IMPS });
      const row = B.rows[mode];
      if (r.shadow0 > 0 && r.main0 > 0) B.mixed++; B.hitsLeft += r.rollHit;
      if (r.noEdgeHp) row.noEdgeHp++; else if (r.noEdge) row.noEdge++;
      if (r.plan) {
        row.plans++; row.claim += r.plan.p;
        if (r.shares.d >= 0.5 || (r.shares.d >= 0.05 && (r.plan.pRoll == null || r.plan.pRoll < 0.4 || r.plan.pNoRoll < 0.4))) row.bad++;      // a confident beep on a guessed HP
        let real = 0; for (const [d, w] of PD) if (R.works(S2.s, S2.nc, r.plan.target + d, S2.f, R.PROFILES.timeout)) real += w; row.real += real;
      }
      if (k < 4) console.log('case', k, g.danger ? '3 HP (roll, Close Call)' : '10 HP (no roll)', mode, JSON.stringify({ why: r.why, shadow: r.shadow0, rollLeft: r.rollLeft, rollHit: r.rollHit, shareRoll: +r.shares.d.toFixed(3), plan: r.plan, msg: r.plan ? undefined : r.msg }));
    }
  }
  for (const m in MODES) { const R_ = B.rows[m]; console.log('B ' + m + ': ' + B.games + ' games, beeps ' + R_.plans + ' (claimed ' + (100 * R_.claim / Math.max(1, R_.plans)).toFixed(1) + '%, true ' + (100 * R_.real / Math.max(1, R_.plans)).toFixed(1) + '%), no edge for the HP ' + R_.noEdgeHp + ', other no edge ' + R_.noEdge + ', beeps on a guessed HP ' + R_.bad); }
  const nModes = Object.keys(MODES).length, sum = k => Object.values(B.rows).reduce((x, r) => x + r[k], 0);
  check(B.mixed === B.games * nModes, 'B: unknown / blank HP carries both hypotheses in every game (' + B.mixed + '/' + B.games * nModes + ')');
  check(B.hitsLeft === 0, 'B: no roll state that hits is kept after the roll');
  check(sum('bad') === 0, 'B: no beep on a frame that fails under one HP hypothesis while both carry weight, nor while the coin favours the roll');
  check(sum('noEdgeHp') > 0, 'B: an HP disagreement gives "no edge" (' + sum('noEdgeHp') + ' times)');
  // C. late 10 HP read, the Life Shroom watch
  const C = await p.evaluate(() => {
    const T = window.__tot, zw = T.zw, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), ti = T.RT().findIndex(s => s.prof === 'timeout'), o = {};
    const setNow = t => { window.__dt += t - performance.now(); }, vl = () => +document.getElementById('s-vlag').value || 0, pf = () => +document.getElementById('s-pfix').value || 0;
    const IM = Array.from({ length: 33 }, (_, i) => 138 + i), frames = (v, n, from) => { const Jb = T.JRT.bar; T.withSample(() => new Uint8ClampedArray(12 * 12 * 4).fill(v), () => { for (let i = 0; i < n; i++) { setNow(zw.t0 + vl() + (from + i) * zw.rate); Jb.since = performance.now() - 500; T.hwHpFrame(performance.now(), true); } }); };
    const start = seed => { T.setStep(hi); T.hwHpReset(); T.hwTrackerAt(seed, [7], 100000); const c = 150; setNow(zw.t0 + vl() + (c + T.VAN.B() + pf()) * zw.rate + 20); T.zwInput('hw_spiny', zw.t0 + vl() + (c + T.VAN.B() + pf()) * zw.rate, T.VAN.B(), IM); T.setStep(ti); return c; };
    let c = start(0x1234567);
    o.shadow0 = zw.shadow ? zw.shadow.length : 0; const n0 = zw.parts.length; frames(255, 8, c + 200);               // Bowser's turn: the bar shows the tens "1"
    o.late = { shadow: zw.shadow ? zw.shadow.length : 0, mainSame: zw.parts.length === n0 };
    c = start(0x7654321); frames(0, 8, c + 380); o.diedBlank = T.HWHP.died;    // blank after the roll: alive
    frames(255, 8, c + 400); o.died = T.HWHP.died; o.zwOn = zw.on; T.st.plan = null; T.makePlan(); o.msg = T.st.msg; o.plan = !!T.st.plan;
    return o;
  });
  check(C.shadow0 > 0 && C.late.shadow === 0 && C.late.mainSame, 'C: a "1" on the bar in Bowser\'s turn drops the roll fallback (the v77 states untouched)');
  check(!C.diedBlank && C.died && !C.zwOn && !C.plan && /No edge/.test(C.msg || ''), 'C: a "1" after the last roll = Life Shroom: tracker off, Time Out no edge');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? 'FAIL ' + fails : 'PASS'); process.exit(fails ? 1 : 0);
})();
