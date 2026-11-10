/* v87: Jr. Troopa (Ultra Boots) after the T3 Charge's own lock, from console log 2f22d4dc-1794272306426 (2026-11-09, page
 * v86.1; its events only): T1 lock d16199be q13, the confirms on the T1 clock (T1 Bomb 109, T2 Bomb 402, Whacka 596, T3
 * Charge 872), the T3 lock 588947ce q15-17 (the cross-check agreed). v86.1 left the T3 Charge's confirm in the T1 clock, so
 * the replan after that lock counted the Bomb's earliest frame from 872 + the menu in the new clock: target 1057, the beep 30 s
 * later. Now the Charge is frame -13 of its own clock and the earlier confirms move with it; and no zero-wait plan asks for a
 * press more than ZW_MAX_AHEAD (10 s) away.
 * usage: node test_jr_v87.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [], p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(async () => {
    const T = window.__tot, out = {};
    const s3 = T.RT().findIndex(s => s.jr === 5); T.setStep(s3);
    T.jrTrackerAt(0xd16199be, [13], performance.now() - 30000, 0);
    for (const [k, c] of [[1, 109], [2, 402], [3, 596], [4, 872]]) T.jrConfirmClock(k, c);
    const L = T.jrLockAt(0x588947ce, [15, 16, 17], 4);
    out.cross = L.cross; out.floor = T.jrPlanFloor();
    T.st.plan = null; for (let i = 0; i < 40 && !T.st.plan; i++) { T.st.planTry = 0; T.jrEarlyPlan(performance.now()); if (!T.st.plan) await new Promise(r => setTimeout(r, 150)); } const P = T.st.plan;
    out.plan = P ? { target: P.target, inMs: Math.round(P.tPress - performance.now()) } : { msg: T.st.msg };
    out.tooFar = T.SLOG.filter(e => e.ev === 'zwTooFar').length;
    return out;
  });
  console.log(JSON.stringify(r));
  check(r.floor != null && r.floor < 400, 'the T3 Bomb\'s earliest frame is counted from the T3 Charge in its own clock (' + r.floor + '; v86.1 ~1050)');
  check(r.plan && r.plan.inMs != null && r.plan.inMs < 10000, 'the replan beeps within seconds, not 30 s later (' + JSON.stringify(r.plan) + ')');
  // the cap on its own: the v86.1 frame base put back (the T3 Charge at 872 in the new clock): no edge, no far beep
  const q = await p.evaluate(async () => { const T = window.__tot; T.JRT.inputs.filter(x => x.k === 4).pop().c = 872; T.st.plan = null; const n0 = T.SLOG.length;
    for (let i = 0; i < 20; i++) { T.st.planTry = 0; T.jrEarlyPlan(performance.now()); if (T.SLOG.slice(n0).some(e => e.ev === 'zwTooFar')) break; await new Promise(r => setTimeout(r, 150)); }
    return { cap: T.zwMaxAhead, far: T.SLOG.slice(n0).filter(e => e.ev === 'zwTooFar').length, plan: !!T.st.plan, msg: T.st.msg }; });
  check(q.cap === 10000 && q.far >= 1 && !q.plan && /No edge/.test(q.msg || ''), 'a plan more than 10 s past the frames the page is at is no edge (' + JSON.stringify(q) + ')');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
