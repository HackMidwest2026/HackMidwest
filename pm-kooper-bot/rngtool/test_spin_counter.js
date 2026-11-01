const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1000, height: 1700 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  const log = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, out = [];
    let s = 0x2468ace0, f = 0; const taps = []; const t0 = performance.now();
    while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
    for (let i = 0; i < 16; i++) { T.addShine(t0 + taps[i] * R.FRAME_MS, true); while (T.st.searching) await new Promise(r => setTimeout(r, 100)); out.push(document.getElementById('spins-count').textContent); }
    return out;
  });
  console.log('counter after each shine:', log.join('  '));
  const panel = await (await p.$('#route')).evaluateHandle(e => e.closest('section')); await panel.asElement().screenshot({ path: 'route2.png' });
  console.log('errors', errs); await b.close();
})();
