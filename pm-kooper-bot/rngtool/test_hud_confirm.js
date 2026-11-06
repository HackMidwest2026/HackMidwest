/* A fast Whacka's Bump never shows the hand on Mario (emulator: A on the item, then A within ~8 frames: the name box
 * never matches). The page counts the confirm from the status bar hiding 3 frames later. Here: lock from shines, T2's
 * Bomb seen on its screen, then the coin box goes from gold to empty 3 frames after the Whacka confirm with no target
 * screen at all. Pass: the route moves on to T3, the Whacka turn sits on the true confirm frame (among its candidates),
 * and the seed is still carried. Also: a hide right after a seen target screen is not counted twice. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  // v73: these turns are the old Jr. Troopa route (a shine lock carried by the target screens); the Charge lock is the default
  await p.addInitScript(() => { try { const s = JSON.parse(localStorage.getItem('tot-settings') || '{}'); s.jrroute = 'shine'; localStorage.setItem('tot-settings', JSON.stringify(s)); } catch (e) {} });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const res = [];
  for (const seed0 of [0x2468ace1, 0x13579bdf]) {
    const out = await p.evaluate(async (seed0) => {
      const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
      document.getElementById('reset').click(); T.setStep(0);
      const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      const G = { S: { s: seed0 >>> 0, nc: 5, inst: [] }, g: 0, ev: [], shines: [] }, T0 = performance.now() + 1000;
      const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
      const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
      run(1500); setNow(1500); for (const g of G.shines) T.addShine(T0 + (g + 6) * FR + vlag, true);
      await wait(() => T.st.lock); if (!T.st.lock) return { error: 'no lock' };
      // video: a canvas whose coin box is gold (bar up) or black (bar hidden); no target screen saved for M
      const c = document.createElement('canvas'); c.width = 640; c.height = 480; const x = c.getContext('2d');
      const frame = (g, up) => { x.fillStyle = '#000'; x.fillRect(0, 0, 640, 480); if (up) { x.fillStyle = 'rgb(230,170,40)'; x.fillRect(0.795 * 640, 0.005 * 480, 0.055 * 640, 0.09 * 480); }
        window.__dt += T0 + g * FR + vlag - performance.now(); T.V.src = new VideoFrame(c, { timestamp: g * 33367 }); T.onFrame(performance.now()); T.V.src.close(); T.V.src = null; };
      T.V.boxes.coin = { x: 0.795, y: 0.005, w: 0.055, h: 0.09 }; Object.assign(T.V, { wasGone: false, present: false, presentSince: 0, hudUp: 0, hudGone: 0, lastClose: 0 });
      const wi = T.RT().findIndex(s => s.turn === 'jr_whacka'); T.setStep(wi);
      // T2 Bomb, seen on its target screen (the screen closed 2 frames after the confirm)
      G.ev.push({ f: 1560, id: 'jr_bomb' }); run(1600);
      for (let g = 1500; g < 1563; g++) frame(g, true);
      T.V.preDone = { [wi + ':0']: true }; T.V.lastClose = T0 + 1562 * FR + vlag; T.preConfirm({ cat: 'K', id: 'jr_bomb' }, T0 + (1560 + 2 + pfix) * FR + vlag);
      for (let g = 1563; g < 1700; g++) frame(g, false);       // the bar hides 3 frames after the Bomb (already counted)
      const afterBomb = { step: T.step(), turns: T.st.turnEv.map(e => e.id).join() };
      // Mario's menu: bar up, then Whacka confirmed fast at 1840: the bar is gone from 1843
      const conf = 1840; G.ev.push({ f: conf, id: 'jr_whacka' }); run(1900);
      for (let g = 1700; g < conf + 3; g++) frame(g, true);
      for (let g = conf + 3; g < conf + 40; g++) frame(g, false);
      const ev = T.st.turnEv.find(e => e.id === 'jr_whacka'), lf = T.st.clock.frames, L0 = Math.round((T.st.clock.t0 - T0) / FR);
      const cands = ev ? (ev.shifts || [0]).map(d => ev.f + d + L0) : [];
      return { afterBomb, stepAfter: T.step(), whackaStep: wi, turns: T.st.turnEv.map(e => e.id).join(), whackaFrameCands: cands, trueFrame: conf, locked: !!T.st.lock,
        hud: T.SLOG.filter(e => e.ev === 'hudConfirm' && e.t > T0).map(e => e.id) };
    }, seed0);
    const ok = out.stepAfter === out.whackaStep + 1 && out.whackaFrameCands.includes(out.trueFrame) && out.locked && out.hud.length === 1 && out.afterBomb.step === out.whackaStep;
    res.push(ok); console.log(seed0.toString(16), ok ? 'PASS' : 'FAIL', JSON.stringify(out));
  }
  console.log(res.every(x => x) ? 'PASS' : 'FAIL', 'errors', errs); await b.close();
})();
