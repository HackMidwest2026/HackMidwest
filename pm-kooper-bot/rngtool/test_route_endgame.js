const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1500 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.selectOption('#s-prof', 'endgame'); await p.dispatchEvent('#s-prof', 'change');
  const r = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, out = [];
    let s = 0x2468ace0, f = 0; const taps = []; const now = performance.now();
    while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
    const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
    while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
    const n = document.querySelectorAll('#route-list li').length;
    for (let i = 0; i < n; i++) {
      const step = document.querySelector('#route-list li[style]').textContent;
      T.st.plan = null; T.makePlan(); const P = T.st.plan;
      out.push(step + ' | ' + document.getElementById('target-label').textContent + ' | plan: ' + (P ? P.w.length + '-frame window' + (P.aim4 ? ', aiming at the better outcome' : '') : 'none'));
      document.getElementById('route-next').click();
    }
    return out;
  });
  console.log(r.join('\n')); console.log('errors', errs); await b.close();
})();
