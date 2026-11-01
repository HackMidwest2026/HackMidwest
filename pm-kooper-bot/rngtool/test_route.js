// Route mode: steps advance on each target-screen close; planning only on the starred steps; per-category references.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1500 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.selectOption('#s-prof', 'jr'); await p.dispatchEvent('#s-prof', 'change');
  const r = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, out = [];
    // lock a seed
    let s = 0x2468ace0, f = 0; const taps = []; const now = performance.now();
    while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
    const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
    while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
    for (let i = 0; i < 12; i++) {
      const step = document.querySelector('#route-list li[style]').textContent;
      T.V.matchSince = 0; T.makePlan(); const planned = !!T.st.plan;
      out.push(step + ' | plan: ' + (planned ? T.st.plan.w.length + '-frame window' : 'none') + ' | box label: ' + document.getElementById('target-label').textContent);
      // simulate the target screen closing after being up
      T.V.wasOn = true; T.V.onFor = 500; T.V.ref = T.V.ref || new Array(384).fill(0);
      document.getElementById('route-next').click();
    }
    return out;
  });
  console.log(r.join('\n')); console.log('errors', errs); await b.close();
})();
