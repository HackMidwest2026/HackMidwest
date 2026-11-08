/* v78: the Hallway T1 throw lever's route glue in the built page (headless Chromium, no video): the T1 line, the step after
 * the Spiny Flip confirm, the plan and its beeps on the aim popup, the popup closing read as the throw, the fallbacks
 * (popup never seen: the bar back in Bowser's turn; no lock; 10 HP), the death watch after the throw (a Life Shroom's
 * 10 HP: no Time Out beep), and that the route reaches Time Out's step in every case.
 * usage (from rngtool/, after python3 build_page.py): node test_hw_cc_page.js [PAGE] */
'use strict';
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
(async () => {
  const b = await chromium.launch(), p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file://' + PAGE);
  let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
  const r = await p.evaluate(() => {
    const T = window.__tot, out = {}, zw = T.zw, H = T.HWCC;
    document.getElementById('s-prof').value = 'endgame';
    const hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), wi = T.RT().findIndex(s => s.turn === 'hw_throw'), ti = T.RT().findIndex(s => s.prof === 'timeout');
    out.idx = [hi, wi, ti];
    T.setStep(hi); T.render();
    const li = [...document.querySelectorAll('#route-list li')].map(x => x.textContent).filter(x => /T1: Charge; Spiny Flip/.test(x));
    out.t1Lines = li.length; out.t1Text = li[0];
    const vl = () => +document.getElementById('s-vlag').value || 0, pf = () => +document.getElementById('s-pfix').value || 0;
    const tOf = (c, van) => zw.t0 + vl() + (c + van + pf()) * zw.rate, setNow = t => { window.__dt += t - performance.now(); };
    const game = (seed, q) => { T.setStep(hi); T.hwTrackerAt(seed, [q], performance.now() - 2000); };
    // 1. a Danger game: the Spiny Flip confirm (its screen closing, as checkPress gets it) -> the throw step, the particles held
    game(0x2468ace0, 17); const c = Math.floor(T.zwF(performance.now(), 0)) + 5; setNow(tOf(c, T.VAN.B()) + 10);
    T.checkPress(tOf(c, T.VAN.B()));
    out.afterConfirm = { step: T.step(), held: H.held, danger: H.danger, parts: zw.parts.length, holds: zw.parts.every(q => q.hold != null) };
    // the aim popup shows 4 frames later: the plan (makePlan, as autoPlan calls it)
    setNow(tOf(c + 4, 0)); T.st.plan = null; T.makePlan();
    const P = T.st.plan; out.plan = P ? { hwcc: !!(P.mix && P.mix.hwcc), p: P.mix && P.mix.p, target: P.target, from: P.from, to: P.to, tPress: P.tPress - performance.now(), win: [c + T.HWCC_WIN[0], c + T.HWCC_WIN[1]] } : null;
    out.msg1 = T.st.msg; out.line1 = T.hwccStatusLine();
    // the popup closes on the planned frame: the throw
    if (P) { setNow(tOf(P.target, T.HWCC_VAN) + 5); T.checkPress(tOf(P.target, T.HWCC_VAN)); }
    out.afterThrow = { step: T.step(), held: H.held, T: H.T, resolved: H.resolved, parts: zw.parts.length, pend: zw.ccPend };
    // Bowser's turn: the tracker reaches the roll; the states left are the Close Call ones
    T.zwUpdate(P.target + 68 + 90); out.afterRoll = { parts: zw.parts.length, lucky: zw.parts.every(q => q.S.cc && q.S.cc.lucky), pend: zw.ccPend, doubt: T.zwDoubt() };
    // the death watch: the bar back with the tens "1" (a Life Shroom revive) for 6 frames
    setNow(tOf(P.target + 300, 0)); const Jb = T.JRT.bar; Jb.since = performance.now() - 500;
    T.withSample(() => new Uint8ClampedArray(12 * 12 * 4).fill(0), () => { for (let i = 0; i < 8; i++) { setNow(performance.now() + 33.4); Jb.since = performance.now() - 500; T.hwccFrame(performance.now(), true); } });   // 3 HP: the tens blank
    out.diedBefore = H.died;
    T.withSample(() => new Uint8ClampedArray(12 * 12 * 4).fill(255), () => { for (let i = 0; i < 8; i++) { setNow(performance.now() + 33.4); Jb.since = performance.now() - 500; T.hwccFrame(performance.now(), true); } });
    out.died = { died: H.died, zwOn: zw.on }; T.st.plan = null; T.makePlan(); out.msgDied = T.st.msg;
    // 2. the popup never seen (not saved): the bar comes back in Bowser's turn -> Time Out's step, the impact frames open
    game(0x13579bdf, 30); const c2 = Math.floor(T.zwF(performance.now(), 0)) + 5; setNow(tOf(c2, T.VAN.B()) + 10); T.checkPress(tOf(c2, T.VAN.B()));
    out.fb0 = { step: T.step(), held: H.held };
    const t1 = performance.now(); for (let k = 0; k < 120; k++) { setNow(t1 + k * 33.4); T.hwccFrame(performance.now(), k > 60); }
    out.fallback = { step: T.step(), held: H.held, resolved: H.resolved, T: H.T, parts: zw.parts.length };
    // 3. 10 HP (the tens "1" read in T1): no Close Call, no beep
    game(0x0badf00d, 5); H.tens = Array(10).fill(0.5); const c3 = Math.floor(T.zwF(performance.now(), 0)) + 5; setNow(tOf(c3, T.VAN.B()) + 10); T.checkPress(tOf(c3, T.VAN.B()));
    setNow(tOf(c3 + 4, 0)); T.st.plan = null; T.makePlan(); out.hp10 = { step: T.step(), danger: H.danger, plan: !!T.st.plan, msg: T.st.msg };
    // 4. no lock: the throw step says play it blind
    T.chgReset(); T.hwccReset(); zw.on = false; T.setStep(wi); T.st.plan = null; T.makePlan(); out.nolock = { plan: !!T.st.plan, msg: T.st.msg };
    return out;
  });
  console.log(JSON.stringify(r, null, 1).slice(0, 4000));
  const [hi, wi, ti] = r.idx;
  check(wi === hi + 1 && ti === hi + 2, 'route: the throw step between the Spiny Flip and Time Out');
  check(r.t1Lines === 1, 'one "T1:" route line for both steps (' + r.t1Text + ')');
  check(r.afterConfirm.step === wi && r.afterConfirm.held && r.afterConfirm.danger && r.afterConfirm.holds, 'the Spiny Flip confirm: on the throw step, states held for the throw, Danger assumed (no HP read)');
  check(r.plan && r.plan.hwcc && r.plan.target >= r.plan.win[0] && r.plan.target <= r.plan.win[1] && r.plan.tPress > 0, 'the throw plan beeps a frame inside the aim window (' + JSON.stringify(r.plan) + ')');
  check(/Throw \(A\) on the beep/.test(r.line1), 'the Charge panel line: ' + r.line1);
  check(r.afterThrow.step === ti && !r.afterThrow.held && r.afterThrow.resolved && r.afterThrow.T === r.plan.target && r.afterThrow.pend, 'the popup closing: the throw read on the planned frame, on to Time Out');
  check(r.afterRoll.parts > 0 && r.afterRoll.lucky && !r.afterRoll.pend && r.afterRoll.doubt < 0.5, 'after the roll: only Close Call states, background weighed once, doubt ' + r.afterRoll.doubt.toFixed(3));
  check(!r.diedBefore && r.died.died && !r.died.zwOn && /No edge|hit/.test(r.msgDied || ''), 'a Life Shroom\'s 10 HP after the throw: tracker off, Time Out no edge (' + r.msgDied + ')');
  check(r.fb0.step === wi && r.fb0.held && r.fallback.step === ti && !r.fallback.held && r.fallback.resolved && r.fallback.T == null && r.fallback.parts > 0, 'popup never seen: the bar back -> Time Out step, impact frames open (' + JSON.stringify(r.fallback) + ')');
  check(r.hp10.danger === false && !r.hp10.plan && /10 HP/.test(r.hp10.msg || ''), '10 HP: no beep (' + r.hp10.msg + ')');
  check(!r.nolock.plan && /No Charge lock/.test(r.nolock.msg || ''), 'no lock: play it blind (' + r.nolock.msg + ')');
  check(!errs.length, 'no page errors ' + errs.join(' | '));
  await b.close(); console.log(fails ? 'FAIL ' + fails : 'PASS'); process.exit(fails ? 1 : 0);
})();
