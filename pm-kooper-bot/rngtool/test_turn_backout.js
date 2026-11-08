/* Hallway turn identification and target-screen back-outs (feedback items 2 and 11).
 *  A. Backing out of Time Out's target screen (the status bar stays up) is not a press: the route stays on T2, Time Out
 *     is not marked done, nothing is measured; a real confirm (the bar hides 2-3 frames after the screen closes) is one.
 *  B. A hand-on-Bowser screen is told apart by time from the Charge burst: after Bowser's attack (a 3 s+ bar hide) and
 *     9 s+ after the burst it is Time Out (T1 -> T2); 1-8 s after the burst with no attack it is the Spiny Flip (T2 -> T1).
 * usage: node test_turn_backout.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(() => {
    const T = window.__tot, V = T.V, st = T.st, hi = T.RT().findIndex(x => x.turn === 'hw_spiny'), ti = T.RT().findIndex(x => x.prof === 'timeout'), out = {};   // v78: the throw step sits between
    const ev = n => T.SLOG.filter(e => e.ev === n).length;
    // A. back-out
    T.setStep(ti); let now = performance.now(); V.present = true; V.hudGone = 0;
    T.screenClosed(now); T.closeTick(now + 200, false); out.pendingAt200 = !!V.closePend;
    T.closeTick(now + 500, false);
    out.backout = { logged: ev('targetBackout'), step: T.step(), hwDone: !!st.hwDone, closed: ev('screenClosed') };
    // A. a confirm: the bar hides 70 ms after the screen closes
    now = performance.now(); T.screenClosed(now); V.hudGone = now + 70; T.closeTick(now + 80, false);
    out.confirm = { closed: ev('screenClosed'), hwDone: !!st.hwDone, step: T.step() };
    // B. T1 -> T2 on a Bowser screen after the attack
    T.setStep(hi); now = performance.now(); st.hwBurstT = now - 12000; st.longHides = [{ at: now - 9000, ms: 6000 }];
    T.hwStepByTarget(now); out.toT2 = T.step() === ti;
    // ... and no change 4 s after the burst with no attack yet (the Spiny Flip on T1)
    T.setStep(hi); st.hwBurstT = now - 4000; st.longHides = []; T.hwStepByTarget(now); out.staysT1 = T.step() === hi;
    // B. T2 -> T1 on a Bowser screen 3 s after the burst
    T.setStep(ti); st.hwBurstT = now - 3000; st.longHides = []; T.hwStepByTarget(now); out.toT1 = T.step() === hi;
    out.logged = T.SLOG.filter(e => e.ev === 'stepByTarget').map(e => e.why);
    return out;
  });
  console.log(JSON.stringify(r));
  check(r.pendingAt200, 'the close should wait for the bar');
  check(r.backout.logged === 1 && r.backout.closed === 0 && !r.backout.hwDone, 'a back-out must not count: ' + JSON.stringify(r.backout));
  check(r.confirm.closed === 1 && r.confirm.hwDone, 'a confirm must count: ' + JSON.stringify(r.confirm));
  check(r.toT2 && r.staysT1 && r.toT1, 'turn by time from the burst: ' + JSON.stringify(r));
  console.log('errors', JSON.stringify(errs)); console.log(fails || errs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || errs.length ? 1 : 0);
})();
