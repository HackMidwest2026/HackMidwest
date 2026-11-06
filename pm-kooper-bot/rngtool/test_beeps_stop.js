/* v72: a running zero-wait plan whose states the coin then rules out must stop its beeps (feedback: a wrong confident
 * beep is worse than "no edge"). One known state is tracked on the console's clock (as test_zw_wait.js); the page plans on
 * Time Out's target screen; then the coin shows shines this state does not have, read in time, before the press. v71 kept
 * the old beeps going ("Seed lost – showing old prediction" with the beeps still playing); v72 must cancel them (log
 * beepsStopped, the plan marked stopped, the strip says so) before the press. A control run with the true shines only
 * must keep its plan and beeps.
 * usage: node test_beeps_stop.js [PAGE]   (PAGE = an older build, to compare) */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const errs = [];
  for (const [seed, bad] of [[0x1badb002, true], [0x2468ace0, true], [0x0ddba11, true], [0x1badb002, false]]) {
    const p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { window.__stops = 0; const AC = window.AudioContext; if (!AC) return; const o = AC.prototype.createOscillator; AC.prototype.createOscillator = function () { const n = o.call(this), st = n.stop.bind(n); n.stop = (...a) => { if (!a.length) window.__stops++; return st(...a); }; return n; }; });
    await p.goto('file://' + PAGE); await p.evaluate(() => localStorage.setItem('tot-settings', JSON.stringify({ off: '-5', beeps: '3', lead: '1.5', zwwin: '1', zwedge: '0', vlag: '50', wtype: 'best' }))); await p.goto('file://' + PAGE);
    const r = await p.evaluate(async ([seed, bad]) => {
      const T = window.__tot, R = T.R, zw = T.zw, rate = 33.427, vlag = 50, now0 = performance.now();
      T.setStep(T.RT().findIndex(x => x.prof === 'timeout'));
      const shines = new Set(); { let x = seed >>> 0, n = 0; for (let t = 0; t < 2400; t++) { if (t === n) { const q = R.randInt(x, 100); x = q[0]; if (q[1] >= 70) shines.add(t); n = t + (q[1] >= 70 ? 48 : 24); } x = R.adv(x); } }
      const t0 = now0 - 2000 - vlag;      // clock frame 0 was 2 s ago: the coin has been watched since
      Object.assign(zw, { on: true, dead: false, t0, rate, taps: [], vis: [], visFrom: 0, visTo: null, visLocked: false, parts: [{ S: { s: seed >>> 0, nc: 0, inst: [] }, g: 0, ev: new Map(), evMax: -1, pauseAt: 0, pause: 0, w: 1, m: new Set() }], nBase: 1, f0: 0, tapLate: 1.5, imps: null, shifts: null, src: 'charge', bg: 0.05 / 0.95, bgTo: null });
      const fNow = () => (performance.now() - vlag - t0) / rate, readAt = f => t0 + (f + 6) * rate + vlag;
      for (const f of shines) if (f + 10 < fNow()) T.zwTap(readAt(f));
      const step = async ms => { const end = performance.now() + ms; while (performance.now() < end) { T.V.steadyT = performance.now(); T.V.present = true; await new Promise(q => requestAnimationFrame(q)); } };
      await step(300);
      T.st.plan = null; T.makePlan(); const P = T.st.plan; if (!P) return { noPlan: T.st.msg };
      // shines this state does not have (bad), or its own shines (control), each read when its flash would show
      const f0 = Math.ceil(fNow()), extra = [];
      if (bad) { for (let f = f0 + 2; extra.length < 5 && f < f0 + 60; f++) if (![...shines].some(x => Math.abs(x - f) < 6)) { extra.push(f); f += 5; } }
      else for (const f of shines) if (f >= f0 && f < f0 + 60) extra.push(f);
      let k = 0; const until = P.tPress + 400;
      while (performance.now() < until) { while (k < extra.length && readAt(extra[k]) <= performance.now()) T.zwTap(readAt(extra[k++])); await step(16); }
      const S = T.SLOG, st = document.getElementById('strip-state');
      return { tPressIn: Math.round(P.tPress - now0), taps: extra.length, stopped: !!P.stopped, stopEv: S.filter(x => x.ev === 'beepsStopped').map(x => ({ t: Math.round(x.t - now0), why: x.why, doubt: x.doubt })), stopsBeforePress: S.some(x => x.ev === 'beepsStopped' && x.t < P.tPress), dead: zw.dead, parts: zw.parts.length, strip: st ? st.textContent : null, oscStopped: window.__stops };
    }, [seed, bad]);
    console.log((bad ? 'contradicting shines ' : 'control ') + seed.toString(16) + ': ' + JSON.stringify(r));
    if (bad) { check(r.stopped && r.stopsBeforePress, seed.toString(16) + ': the beeps were not stopped before the press'); check(/stopped|lost/i.test(r.strip || ''), seed.toString(16) + ': the strip does not say so'); }
    else check(!r.stopped && !(r.stopEv || []).length, 'control: the plan was stopped by its own shines');
    await p.close();
  }
  console.log('errors', JSON.stringify(errs)); console.log(fails || errs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || errs.length ? 1 : 0);
})();
