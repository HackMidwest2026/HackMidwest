/* The route through the runner's first live session (timeout-timer-log-1793757328924, Time Out Timer v68), replayed
 * through the built page in headless Chromium: every target screen that closed (screenClosed: the Spiny Flip read from the
 * bar, Time Out, later Bowser target screens) goes to checkPress at its logged time, every logged coin return to coinBack,
 * and every Charge the page confirmed (chargeConfirm) sets Hallway T1 as chgPendResolve does. The runner's own step
 * changes by hand are left out: the page must keep the route right by itself.
 * v68 went from Hallway T2 into the Final Bowser step on Time Out's screen closing; a quick retry has no 10 s gap, so the
 * route stayed there and the next Hallway Charges were read with the Final Bowser profile (the log: prof fb2 at
 * 478-489 s and 704-708 s; the runner stepped back by hand 7 times). Checks:
 *   - this build: at every Charge trigger of the log the route is on a Hallway step (the Hallway profile), it never
 *     reaches the Final Bowser step, and after each Time Out it stays on Hallway T2 with no new plan;
 *   - v68 (PAGE0, built from 5d19125): the same replay puts the route on the Final Bowser step at 478 s and 704 s, as logged.
 * usage (from rngtool/): node charge_live/test_route_replay.js [LOG] [PAGE] [PAGE0] */
'use strict';
const { chromium } = require('playwright'), fs = require('fs');
const LOGF = process.argv[2] || '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887/9e47f827-timeout-timer-log-1793757328924.json';
const PAGE = process.argv[3] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const PAGE0 = process.argv[4] || '/dev/shm/tt/oldbuild/timeout_timer_standalone.html';
const E = JSON.parse(fs.readFileSync(LOGF, 'utf8')).events;
async function replay(b, file) {
  const p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file://' + file);
  const r = await p.evaluate(events => {
    const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), fi = T.RT().findIndex(s => s.turn === 'fb2_pb'), ti = T.RT().findIndex(s => s.prof === 'timeout');
    const setNow = t => { window.__dt += t - performance.now(); };
    document.getElementById('reset').click(); T.setStep(hi);
    const atTrig = [], fbAt = [], afterTimeOut = []; let lastStep = T.step();
    for (const e of events) {
      // v78: the throw step after the Spiny Flip (its aim popup is not in these v68 logs): the page leaves it when the bar
      // comes back in Bowser's turn (hwccFrame), so the next screen closing is Time Out's
      if (e.ev === 'screenClosed' && T.RT()[T.step()].turn === 'hw_throw') T.setStep(T.step() + 1);
      if (e.ev === 'screenClosed') { setNow(e.t); const was = T.step(); T.checkPress(e.at);
        if (was === ti) { T.st.plan = null; T.makePlan(); afterTimeOut.push({ t: Math.round(e.t / 1000), step: T.step(), plan: !!T.st.plan, msg: (T.st.msg || '').slice(0, 30) }); } }
      else if (e.ev === 'coinBack') { setNow(e.t); T.coinBack(e.hiddenMs); }
      else if (e.ev === 'chargeConfirm') { setNow(e.t); if (T.step() !== hi) T.setStep(hi); }
      else if (e.ev === 'chargeTrigger') atTrig.push({ t: Math.round(e.t / 100) / 10, step: T.step(), prof: T.RT()[T.step()].turn === 'fb2_pb' ? 'fb2' : /^Hallway/.test(T.RT()[T.step()].t) ? 'hw' : 'other' });
      if (T.step() !== lastStep) { lastStep = T.step(); if (lastStep === fi) fbAt.push(Math.round(e.t / 1000)); }
    }
    return { hi, ti, fi, atTrig, fbAt, afterTimeOut, stepBack: T.SLOG.filter(x => x.ev === 'stepBackToHallway').length, done: T.SLOG.filter(x => x.ev === 'hallwayDone').length };
  }, E);
  await p.close(); return Object.assign(r, { errs });
}
(async () => {
  const b = await chromium.launch(); let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
  const n = await replay(b, PAGE);
  console.log('this build: ' + JSON.stringify(n));
  check(!n.errs.length, 'page errors ' + n.errs.join(' | '));
  check(n.atTrig.length >= 20 && n.atTrig.every(x => x.prof === 'hw'), 'every Charge trigger on a Hallway step');
  check(!n.fbAt.length, 'the route never reaches the Final Bowser step');
  check(n.afterTimeOut.length >= 5 && n.afterTimeOut.every(x => x.step === n.ti && !x.plan), 'after Time Out: stays on Hallway T2, no new plan');
  if (fs.existsSync(PAGE0)) {
    const o = await replay(b, PAGE0);
    console.log('v68: ' + JSON.stringify({ fbAt: o.fbAt, fb2Triggers: o.atTrig.filter(x => x.prof === 'fb2') }));
    check(o.fbAt.includes(475) && o.fbAt.includes(684), 'v68 replay should reach the Final Bowser step on the Time Outs at 475 s and 684 s, as logged');
    check(o.atTrig.some(x => x.prof === 'fb2' && x.t >= 478 && x.t <= 489) && o.atTrig.some(x => x.prof === 'fb2' && x.t >= 704 && x.t <= 708), 'v68 replay should read the triggers at 478-489 s and 704 s with the FB2 profile, as logged');
  } else console.log('(no v68 build at ' + PAGE0 + ': the before/after comparison is skipped)');
  console.log(fails ? fails + ' FAILED' : 'all passed'); await b.close(); process.exit(fails ? 1 : 0);
})();
