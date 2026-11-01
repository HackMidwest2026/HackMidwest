/* The strip must not jump: lock a seed, keep detecting shines in real time with +-10 ms noise (camera mode), then a
 * coin gap with resync. Sample the displayed "now" (in game frames) every 50 ms: steps must stay ~1.5 frames. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const r = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, F = 33.43; let s = 0x2468ace0, f = 0; const sh = [];
    while (sh.length < 60) { s = R.adv(s); const x = s >= R.SHINE_MIN; if (x) sh.push(f); for (let i = 0; i < (x ? 48 : 24); i++) s = R.adv(s); f += x ? 48 : 24; }
    const t0 = performance.now() - sh[19] * F - 10 * F, noise = () => (Math.random() - 0.5) * 20;
    for (let i = 0; i < 20; i++) T.addShine(t0 + sh[i] * F + 6 * F + noise(), true);
    while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
    const samples = []; let next = 20; const end = performance.now() + 20000; let gapDone = false;
    while (performance.now() < end) {
      const now = performance.now();
      // live shines as they "happen"; a coin gap (hidden) between 8 s and 12 s
      while (next < sh.length && t0 + sh[next] * F + 6 * F <= now) {
        const tt = t0 + sh[next] * F + 6 * F;
        const hidden = now > end - 12000 && now < end - 8000;
        if (!hidden) { if (!gapDone && now >= end - 8000) { T.newSegment(); gapDone = true; } T.addShine(tt + noise(), true); }
        next++;
      }
      await new Promise(r => requestAnimationFrame(r));
      if (window.__tot.V.dispAbs !== null && (samples.length === 0 || now - samples[samples.length - 1][0] >= 50)) samples.push([window.__tot.V.dispT, window.__tot.V.dispAbs, !!T.st.lock]);
    }
    return samples;
  });
  // displayed now should advance (dt / 33.43) frames between samples; report the worst deviation
  let worst = 0, at = 0;
  for (let i = 1; i < r.length; i++) { const exp = (r[i][0] - r[i - 1][0]) / 33.43, got = r[i][1] - r[i - 1][1]; if (r[i][2] !== r[i - 1][2]) continue; const dev = Math.abs(got - exp); if (dev > worst) { worst = dev; at = i; } }
  const devs = []; for (let i = 2; i < r.length; i++) { if (r[i][2] !== r[i - 1][2]) continue; devs.push([Math.abs((r[i][1] - r[i - 1][1]) - (r[i][0] - r[i - 1][0]) / 33.43), i]); }
  devs.sort((a, b) => b[0] - a[0]);
  console.log('samples', r.length, '| first-sample deviation', worst.toFixed(2), '@', at, '| largest later step deviations (frames@sample):', devs.slice(0, 5).map(x => x[0].toFixed(3) + '@' + x[1]).join(', '), '| errors', errs);
  await b.close();
})();
