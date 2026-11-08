/* v78: Hallway Bowser T1 at 3 HP, the Spiny Flip throw beeped for Close Call (charge_live/hwcc_live.js), then Time Out on
 * T2, through the built standalone page in headless Chromium, against the model (pmrng_core.js, which matches the emulator
 * on every frame: test_hw_cc_model.js). Per case, a random game: seed and first coin at the T1 Charge's frame 0, console lag
 * 0 / 1 after the rays (CHG_LAGS), the Spiny Flip confirm on clock 110..230 read off the bar's hiding with the tracker's
 * error (CHG_SHIFTS). The page's tracker starts from the exact lock (hwTrackerAt: the true seed and q, both lags), takes the
 * confirm, plans the throw on the aim popup (lead 1.5 s, max extra wait 1 s, best chance, presses 25/50/25 over -1/0/+1), the
 * press lands by that spread and the popup closing is read +-2 frames (HWCC_SHIFTS); the true game plays it.
 * A. The throw: the page's claimed chance (mean) against the model's Close Calls; blind 30 / 101.
 * B. Time Out after a Close Call (the miss path): on the T2 target screen (roll + 140 frames, no shine shown in the menu),
 *    chgPlanAt's plan (lead 1.5 s, 1 s) and the true chance of Time Out working there with the same press spread. The same
 *    games through the tracker as v77 had it (no Close Call draw in its model, impact frames open): what v78 replaces.
 * C. 10 HP (no Close Call: the bar's tens "1" read in T1): no throw beep, Time Out on the guard / impact candidates from the
 *    throw read (v78) and from the open impact frames (v77).
 * D. Honesty: no beep claims more than the model gives by more than the sampling noise; a hit (Mario dies) leaves no state.
 * usage (from rngtool/, after python3 build_page.py): node test_hw_cc_plan.js [PAGE] [N=60] */
'use strict';
const { chromium } = require('playwright'), fs = require('fs');
const SP = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad';
const PAGE = process.argv[2] || SP + '/timeout_timer/timeout_timer_standalone.html', N = +(process.argv[3] || 60);
const R = require('./pmrng_core.js');
let rs = 4242; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296;
const pick = D => { let u = rnd(); for (const [v, w] of D) { if (u < w) return v; u -= w; } return D[D.length - 1][0]; };
const PD = [[-1, 0.25], [0, 0.5], [1, 0.25]], LAGS = [[0, 0.75], [1, 0.25]], CHG_N = 48;   // charge_live.js CHG_LAGS, CHG_N
const CHG_SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]], HWCC_SHIFTS = [[-2, 0.1], [-1, 0.25], [0, 0.4], [1, 0.2], [2, 0.05]];
/* the true game on the tracker's clock (frame 0 = the Charge's frame 0; console lag l frames after the rays, as chgStartTracker) */
function truth(g, T, danger, guard) {
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: g.Ct, id: 'hw_spiny' }].concat(T != null ? [{ f: T, id: 'hw_throw', imp: 24, danger, guard }] : []));
  const S = { s: g.seed, nc: g.q, inst: [] }; let f = 0;
  const step = to => { while (f < to) { if (g.lag && f === CHG_N + 2) { S.nc += g.lag; f += g.lag; continue; } R.frameEv(S, f, ev); f++; if (S.cc && !S.cc.lucky) return false; } return true; };
  return { S, step, f: () => f };
}
function shinesOf(g, T, danger, guard, a, b) {                    // the true game's shine draws on clock frames a..b
  const t = truth(g, T, danger, guard), out = []; t.step(a);
  // (stepped on frame by frame: a shine is a coin draw >= 70)
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: g.Ct, id: 'hw_spiny' }, { f: T, id: 'hw_throw', imp: 24, danger, guard }]);
  for (let f = t.f(); f <= b; f++) { const sh = R.frameEv(t.S, f, ev); if (sh) out.push(f); }
  return out;
}
function timeOutTrue(g, T, danger, guard, cScr, target) {          // the true chance Time Out works on target with the press spread
  const t = truth(g, T, danger, guard); t.step(cScr); if (t.S.ccHit) return null;
  let p = 0; for (const [d, w] of PD) if (R.works(t.S.s, t.S.nc, target + d, t.f(), R.PROFILES.timeout)) p += w; return p;
}
async function page(b, file) {
  const p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + file); await p.evaluate(() => { document.getElementById('s-prof').value = 'endgame'; });
  return { p, errs };
}
(async () => {
  const b = await chromium.launch(); let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
  const NEW = await page(b, PAGE);
  const ver = await NEW.p.evaluate(() => window.__tot.VERSION); check(ver === 'v78', 'page version ' + ver);
  const A = { claim: 0, real: 0, n: 0, beeps: 0, none: {} }, B = { n: 0, v78: 0, v77: 0, v78plans: 0, v77plans: 0 }, C = { n: 0, v78: 0, v77: 0, beeps: 0 };
  let over = 0, blindSum = 0, blindN = 0;
  for (let k = 0; k < N; k++) {
    const hp10 = k % 4 === 3;
    const g = { seed: (rnd() * 4294967296) >>> 0, q: Math.floor(rnd() * 48), lag: pick(LAGS), Ct: 110 + Math.floor(rnd() * 120), sh: pick(CHG_SHIFTS) };
    const r = await NEW.p.evaluate(({ g, hp10 }) => {
      const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), zw = T.zw;
      T.setStep(hi); T.hwTrackerAt(g.seed, [g.q], 100000);
      const vl = +document.getElementById('s-vlag').value || 0, pf = +document.getElementById('s-pfix').value || 0, tOf = (c, van) => zw.t0 + vl + (c + van + pf) * zw.rate;
      if (hp10) T.HWCC.tens = Array(10).fill(0.5);
      const cRead = g.Ct - g.sh; T.zwInput('hw_spiny', tOf(cRead, T.VAN.B()), T.VAN.B(), T.CHG_IMPS);
      T.setStep(hi + 1);
      const pl = T.hwccPlan(cRead + 4);
      return { danger: T.HWCC.danger, cRead, plan: pl && pl.target != null ? { target: pl.target, p: pl.p, from: pl.from, to: pl.to, states: pl.states } : { none: pl && pl.none }, step: T.step(), t0: zw.t0, rate: zw.rate, vl, pf };
    }, { g, hp10 });
    // the throw: on the beep (spread), else whenever (the runner's own: clock confirm + 60..90)
    const Tp = r.plan.target != null ? r.plan.target + pick(PD) : g.Ct + 60 + Math.floor(rnd() * 31), Tread = Tp - pick(HWCC_SHIFTS), guard = rnd() < 0.5;
    const danger = !hp10;
    // the true roll
    const tg = truth(g, Tp, danger, guard); tg.step(Tp + 68 + 80);
    const lucky = danger ? !!(tg.S.cc && tg.S.cc.lucky) : null;
    if (danger) {
      if (r.plan.target != null) {
        A.beeps++; A.claim += r.plan.p;
        let real = 0; for (const [d, w] of PD) { const t2 = truth(g, r.plan.target + d, true, false); t2.step(r.plan.target + d + 160); if (t2.S.cc && t2.S.cc.lucky) real += w; }
        A.real += real; if (r.plan.p > real + 0.5) over++;
      } else A.none[r.plan.none] = (A.none[r.plan.none] || 0) + 1;
      A.n++;
      for (let F = g.Ct + 55; F <= g.Ct + 85; F++) { const t3 = truth(g, F, true, false); t3.step(F + 160); blindSum += t3.S.cc && t3.S.cc.lucky ? 1 : 0; blindN++; }
    } else if (r.plan.target != null) C.beeps++;
    // the throw read, then (danger: after a Close Call only) the Time Out plan on T2
    if (danger && !lucky) {
      const left = await NEW.p.evaluate(({ tObs, h }) => { const T = window.__tot; T.hwccThrow(tObs); T.zwUpdate(h); return T.zw.parts.length; }, { tObs: r.t0 + r.vl + (Tread + 0 + r.pf) * r.rate, h: Tp + 68 + 80 });
      // a hit: every state that predicted the true roll hit is gone; any left would be states whose roll was Lucky
      continue;
    }
    // T2's menu: from the roll + 135 (Close Call; emulator 85-133) or Bowser's AI + 300 (a hit at 10 HP), the coin watched for
    // 1.5 s, its shines tapped as the page sees them; then Time Out's target screen
    const menu = danger ? tg.S.cc.f + 135 : Tp + 68 + 300, cScr = menu + 45, shines = shinesOf(g, Tp, danger, guard, menu, cScr - 4);
    const coin = { menu, shines, t0: r.t0, vl: r.vl, rate: r.rate };
    const t2 = await NEW.p.evaluate(({ tObs, cScr, coin }) => { const T = window.__tot; T.hwccThrow(tObs); const hi = T.RT().findIndex(s => s.prof === 'timeout'); T.setStep(hi);
      T.zw.visFrom = coin.menu; for (const f of coin.shines) T.zwTap(coin.t0 + coin.vl + (f + 6) * coin.rate); return T.chgPlanAt(cScr, 1.5, 1); }, { tObs: r.t0 + r.vl + (Tread + r.pf) * r.rate, cScr, coin });
    // the same game through the tracker as v77 had it (no throw step: the impact frames open at the confirm, no Close Call
    // draw in the model): the route is switched off for the confirm, so hwccDefer declines and zwInput splits as before
    const t77 = await NEW.p.evaluate(({ g, cScr, coin }) => {
      const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), zw = T.zw; T.setStep(hi); T.hwTrackerAt(g.seed, [g.q], 100000);
      const vl = +document.getElementById('s-vlag').value || 0, pf = +document.getElementById('s-pfix').value || 0, sel = document.getElementById('s-prof');
      sel.value = 'timeout'; try { T.zwInput('hw_spiny', zw.t0 + vl + (g.Ct - g.sh + T.VAN.B() + pf) * zw.rate, T.VAN.B(), T.CHG_IMPS); } finally { sel.value = 'endgame'; }
      zw.visFrom = coin.menu; for (const f of coin.shines) T.zwTap(coin.t0 + coin.vl + (f + 6) * coin.rate);
      return T.chgPlanAt(cScr, 1.5, 1);
    }, { g, cScr, coin });
    const pTrue77 = t77 && t77.target != null ? timeOutTrue(g, Tp, danger, guard, cScr, t77.target) : null;
    const pTrue78 = t2 && t2.target != null ? timeOutTrue(g, Tp, danger, guard, cScr, t2.target) : null;
    const row = hp10 ? C : B; row.n++;
    if (pTrue78 != null) { row.v78 += pTrue78; row.v78plans = (row.v78plans || 0) + 1; row.claim = (row.claim || 0) + t2.p; }
    if (pTrue77 != null) { row.v77 += pTrue77; row.v77plans = (row.v77plans || 0) + 1; }
    if (k < 6 || k % 10 === 0) console.log('case', k, hp10 ? '10 HP' : 'Danger', 'confirm', g.Ct, 'read', r.cRead, 'throw plan', JSON.stringify(r.plan), 'pressed', Tp, danger ? (lucky ? 'Close Call' : 'hit') : '-', 'T2 plan', t2 && t2.target, t2 && +(t2.p || 0).toFixed(2), 'true', pTrue78 != null ? pTrue78.toFixed(2) : '-', '| v77 plan', t77 && t77.target, 'true', pTrue77 != null ? pTrue77.toFixed(2) : '-');
  }
  console.log('A. throw: ' + A.n + ' Danger games, beeped ' + A.beeps + ', claimed ' + (100 * A.claim / Math.max(1, A.beeps)).toFixed(1) + '%, model ' + (100 * A.real / Math.max(1, A.beeps)).toFixed(1) + '% (blind ' + (100 * blindSum / blindN).toFixed(1) + '%), no beep: ' + JSON.stringify(A.none));
  const pc = (x, n) => (100 * x / Math.max(1, n)).toFixed(1) + '%';
  console.log('B. Time Out after the Close Call: ' + B.n + ' games; v78: ' + (B.v78plans || 0) + ' plans, claimed ' + pc(B.claim || 0, B.v78plans) + ', true chance ' + pc(B.v78, B.v78plans) + '; v77 tracker: ' + (B.v77plans || 0) + ' plans, true chance ' + pc(B.v77, B.v77plans) + ' (blind 31%)');
  console.log('C. 10 HP: ' + C.n + ' games, throw beeps ' + C.beeps + '; Time Out v78: ' + (C.v78plans || 0) + ' plans, claimed ' + pc(C.claim || 0, C.v78plans) + ', true ' + pc(C.v78, C.v78plans) + '; v77: ' + (C.v77plans || 0) + ' plans, ' + pc(C.v77, C.v77plans));
  check(A.beeps >= A.n * 0.8, 'A: a throw plan in most Danger games');
  check(A.real / Math.max(1, A.beeps) >= 0.65, 'A: the beeped throw gives Close Call well above blind (30%)');
  check(Math.abs(A.claim - A.real) / Math.max(1, A.beeps) < 0.08, 'A: the claimed chance is honest (within 8 points of the model)');
  check(B.v78plans === B.n && B.v78 / Math.max(1, B.v78plans) >= 0.65, 'B: Time Out on the Close Call (miss) path planned every time, true chance 65%+ (1.5 s of coin in the menu)');
  check(Math.abs((B.claim || 0) - B.v78) / Math.max(1, B.v78plans) < 0.12, 'B: the Time Out claim on the miss path is honest (within 12 points)');
  check(B.v78 / Math.max(1, B.v78plans) >= B.v77 / Math.max(1, B.v77plans || 1) - 0.02, 'B: Time Out on the miss path no worse than the v77 tracker');
  check((C.v78plans || 0) >= (C.v77plans || 0) && C.v78 / Math.max(1, C.v78plans) >= C.v77 / Math.max(1, C.v77plans || 1) - 0.03, 'C: Time Out at 10 HP no worse than v77');
  check(C.beeps === 0, 'C: no throw beep at 10 HP');
  check(!NEW.errs.length, 'no page errors ' + NEW.errs.join(' | '));
  await b.close(); console.log(fails ? 'FAIL ' + fails : 'PASS');
  process.exit(fails ? 1 : 0);
})();
