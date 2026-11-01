/* A near-lock carried across a long cutscene: lava ride with dropouts (stretches of 2-3 shines, coin gone < 1 s between,
 * ~31 bits: not quite a lock), then a 2-minute quiz with the coin hidden (the coin keeps drawing, plus 40 quiz draws),
 * then short stretches. The page must lock on the true seed soon after, without a fresh 13-shine stretch. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  for (const seed of [0x2b2b2b2b, 0x5eedf00d, 0x1234abcd, 0x0ddba12]) {
    const out = await p.evaluate(async seed => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS, vlag = +document.getElementById('s-vlag').value;
      document.getElementById('reset').click();
      const S = { s: seed >>> 0, nc: 5, inst: [] }, sh = [], drawSeed = {};
      const QUIZ = [2900, 2900 + 4080];                              // 136 s of coin hidden; 40 quiz draws inside
      for (let f = 0; f < 9500; f++) {
        if (f > QUIZ[0] && f < QUIZ[1] && f % 100 === 0) S.s = R.randInt(S.s, 3)[0];
        if (f === S.nc) drawSeed[f] = S.s >>> 0;
        if (R.frameEv(S, f, null)) sh.push(f);
      }
      const setNow = t => { window.__dt += t - performance.now(); };
      const wait = async () => { for (let i = 0; i < 1200 && T.st.searching; i++) await new Promise(r => setTimeout(r, 50)); };
      const tap = f => 1e5 + (f + 6) * F + vlag; const res = { lavaShines: 0 };
      // lava ride: visible 160 frames, dropout ~20 frames (0.7 s), repeated, from frame 100 to 2900
      let n = 0;
      for (let a = 100; a < 2900; a += 180) {
        const vis = sh.filter(f => f >= a && f < a + 160);
        for (const f of vis) { setNow(tap(f) + 200); T.addShine(tap(f), true); n++; await wait(); }
        if (a + 180 < 2900) { setNow(tap(a + 185)); T.coinBack(700); await wait(); }   // (the last stretch ends in the quiz)
      }
      res.lavaShines = n; res.afterLava = { locked: !!T.st.lock, cands: T.st.cands ? T.st.cands.length : null };
      // the quiz: hidden 136 s
      setNow(tap(QUIZ[1]) + 1000); T.coinBack(136000); await wait(); await wait();
      res.carried = T.st.wcarry ? T.st.wcarry.cands.length : (T.st.wcarryPending ? 'pending' : null);
      // after: short stretches with brief dropouts
      let m = 0;
      for (let a = QUIZ[1] + 60; a < 9500 && !T.st.lock; a += 180) {
        for (const f of sh.filter(f => f >= a && f < a + 160)) { setNow(tap(f) + 200); T.addShine(tap(f), true); m++; await wait(); if (T.st.lock) break; }
        if (!T.st.lock) { setNow(tap(a + 185)); T.coinBack(700); await wait(); }
      }
      const L = T.st.lock, f1 = L && Math.round((T.st.segs[L.seg].taps[0] - 1e5 - vlag) / F - 6);
      res.afterQuiz = { locked: !!L, shinesAfterQuiz: m, onTrue: !!L && (L.seed >>> 0) === drawSeed[f1] };
      return res;
    }, seed);
    console.log(seed.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
