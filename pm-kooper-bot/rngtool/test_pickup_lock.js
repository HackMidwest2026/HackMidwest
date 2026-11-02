/* A lock must survive short coin dropouts without a re-sync: (a) a 2 s item-pickup message (the coin keeps spinning,
 * frames unchanged), (b) a 2.5 s quick room load that runs 5 extra fast frames (the game gets 5 frames ahead of the
 * clock). After each, shines must be accepted where the locked seed puts them, with no new segment. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  for (const seed of [0x13572468, 0x2468ace1, 0x0badf00d]) {
    const out = await p.evaluate(async seed => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS, vlag = +document.getElementById('s-vlag').value;
      document.getElementById('reset').click();
      const S = { s: seed >>> 0, nc: 5, inst: [] }, sh = [];
      for (let f = 0; f < 5000; f++) if (R.frameEv(S, f, null)) sh.push(f);
      const setNow = t => { window.__dt += t - performance.now(); };
      const wait = async () => { for (let i = 0; i < 1200 && T.st.searching; i++) await new Promise(r => setTimeout(r, 50)); };
      let ahead = 0; const tap = f => 1e5 + (f - ahead + 6) * F + vlag;
      for (const f of sh.filter(f => f < 1500)) { setNow(tap(f) + 200); T.addShine(tap(f), true); await wait(); }
      const r = { lockedFirst: !!T.st.lock, segs0: T.st.segs.length };
      // (a) pickup: coin hidden 1500..1560 frames (2 s), nothing else changes
      setNow(tap(1560) + 1000); T.coinBack(2000);
      for (const f of sh.filter(f => f >= 1560 && f < 2600)) { setNow(tap(f) + 200); T.addShine(tap(f), true); await wait(); }
      r.afterPickup = { locked: !!T.st.lock, segs: T.st.segs.length, checked: T.st.carryOk || 0 };
      // (b) quick room load at 2600: hidden 2.5 s, the game runs 5 extra frames
      ahead = 5; setNow(tap(2680) + 1000); T.coinBack(2500);
      for (const f of sh.filter(f => f >= 2680 && f < 3800)) { setNow(tap(f) + 200); T.addShine(tap(f), true); await wait(); }
      r.afterLoad = { locked: !!T.st.lock, segs: T.st.segs.length, checked: T.st.carryOk || 0, shift: T.SLOG.filter(e => e.ev === 'clockShift').map(e => e.frames) };
      return r;
    }, seed);
    console.log(seed.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
