/* The route after a Hallway Bowser retry (charge_live/README.md, "Arming"): a long gap (10 s+, a reload walked back into
 * the hallway) on Hallway T2, or on the next fight's step right after the route left the Hallway by itself, sets the
 * route back to Hallway T1; the same gap on a step reached by hand from elsewhere does not. Built page, headless Chromium.
 * usage: node test_hw_steps.js [PAGE]   (default: the scratchpad build of timeout_timer_standalone.html) */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
(async () => {
  const b = await chromium.launch(), p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(() => {
    // v78: Time Out's step (ti) comes after the T1 throw step
    const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), ti = T.RT().findIndex(s => s.prof === 'timeout'), out = {};
    T.setStep(ti); T.coinBack(12000); out.t2 = T.step();
    T.setStep(ti); T.setStep(ti + 1); T.coinBack(12000); out.left = T.step();     // left the Hallway, no fight since
    T.setStep(hi - 1); T.setStep(ti + 1); T.coinBack(12000); out.other = T.step();    // reached from Jr. Troopa
    T.setStep(ti); T.coinBack(3000); out.short = T.step();
    out.hi = hi; out.ti = ti; out.logged = T.SLOG.filter(x => x.ev === 'stepBackToHallway').length; return out;
  });
  const ok = r.t2 === r.hi && r.left === r.hi && r.other === r.ti + 1 && r.short === r.ti && r.logged === 2 && !errs.length;
  console.log(JSON.stringify(r), errs.slice(0, 3), ok ? 'PASS' : 'FAIL'); await b.close(); process.exit(ok ? 0 : 1);
})();
