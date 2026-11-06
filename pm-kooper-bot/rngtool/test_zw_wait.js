/* The zero-wait tracker must survive waiting on Time Out's target screen (feedback item 2). One known state is tracked
 * on the console's clock; the coin's shines are read at their real times; the page replans every ~2 s as it does while
 * the runner waits on the target screen, timed so that a shine has been drawn but its flash not yet read at each plan.
 * v69 stepped the tracker to "now" at every plan, passing over such a shine before it was read, and the next plan
 * dropped the true state ("No edge" after ~20 s). Here the state must survive 25 s of plans, every plan must have
 * exactly the set number of beeps, and the strip must keep showing frames.
 * usage: node test_zw_wait.js [PAGE]   (PAGE=v69 build: prints when it dies, for comparison) */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const errs = []; const out = [];
  for (const seed of [0x1badb002, 0x2468ace0, 0x0ddba11]) {
    const p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { window.__osc = 0; const AC = window.AudioContext; if (!AC) return; const o = AC.prototype.createOscillator; AC.prototype.createOscillator = function () { window.__osc++; return o.call(this); }; });
    await p.goto('file://' + PAGE); await p.evaluate(() => localStorage.setItem('tot-settings', JSON.stringify({ off: '-5', beeps: '3', lead: '1.5', zwwin: '1', zwedge: '0', vlag: '50', wtype: 'best' }))); await p.goto('file://' + PAGE);
    const r = await p.evaluate(async seed => {
      const T = window.__tot, R = T.R, zw = T.zw, rate = 33.427, vlag = 50, now0 = performance.now();
      T.setStep(T.RT().findIndex(x => x.prof === 'timeout'));
      // the true state's shines (coin draws: 24 frames after a plain spin, 48 after a shine; works()' per-frame step)
      const shines = []; { let x = seed >>> 0, n = 0; for (let t = 0; t < 2400; t++) { if (t === n) { const q = R.randInt(x, 100); x = q[0]; if (q[1] >= 70) shines.push(t); n = t + (q[1] >= 70 ? 48 : 24); } x = R.adv(x); } }
      const t0 = now0 + 300 - vlag;      // clock frame 0 is 0.3 s from now
      Object.assign(zw, { on: true, dead: false, t0, rate, taps: [], vis: [], visFrom: 0, visTo: null, visLocked: false, parts: [{ S: { s: seed >>> 0, nc: 0, inst: [] }, g: 0, ev: new Map(), evMax: -1, pauseAt: 0, pause: 0, w: 1, m: new Set() }], nBase: 1, f0: 0, tapLate: 1.5, imps: null, shifts: null, src: 'charge' });
      const readAt = f => t0 + (f + 6) * rate + vlag, planAt = shines.filter(f => f > 60).map(f => t0 + (f + 3) * rate + vlag);   // 3 frames after a shine's draw, 3 before its flash is read
      let si = 0, pi = 0, plans = 0, beepsBad = [], noFrames = 0, deadAt = null; const end = now0 + 25000;
      while (performance.now() < end) {
        const now = performance.now(); T.V.steadyT = now; T.V.present = true;
        while (si < shines.length && readAt(shines[si]) <= now) { (T.zwTap || T.addShine)(readAt(shines[si]) + (Math.random() - 0.5) * 10, true); si++; }
        if (pi < planAt.length && planAt[pi] <= now) {
          pi++; if (!T.st.plan || now > T.st.plan.tPress + 600) { const o0 = window.__osc; T.st.plan = null; T.makePlan(); plans++; if (T.st.plan && window.__osc - o0 !== 3) beepsBad.push(window.__osc - o0); }
        }
        if (zw.dead && deadAt == null) deadAt = Math.round((now - now0) / 100) / 10;
        if (T.stripData && !T.stripData().tab.length) noFrames++;
        await new Promise(r => requestAnimationFrame(r));
      }
      return { plans, shinesRead: si, deadAt, parts: zw.parts.length, beepsBad, noFrames, lastMsg: T.st.msg, state: document.getElementById('strip-state') ? document.getElementById('strip-state').textContent : null };
    }, seed);
    out.push(Object.assign({ seed: seed.toString(16) }, r));
    console.log('seed ' + seed.toString(16) + ': ' + JSON.stringify(r));
    check(r.deadAt == null && r.parts > 0, `seed ${seed.toString(16)}: the tracker died at ${r.deadAt} s`);
    check(r.plans >= 5, `seed ${seed.toString(16)}: only ${r.plans} plans in 25 s`);
    check(!r.beepsBad.length, `seed ${seed.toString(16)}: plans with other than 3 beeps: ${r.beepsBad}`);
    check(r.noFrames < 5, `seed ${seed.toString(16)}: the strip had no frames in ${r.noFrames} animation frames`);
    await p.close();
  }
  console.log('errors', JSON.stringify(errs)); console.log(fails || errs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || errs.length ? 1 : 0);
})();
