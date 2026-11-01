/* First lock across gaps on the page: the coin is visible ~15 s, hidden ~10 s (a room load that runs 5 extra fast
 * frames), repeatedly. Shines only arrive while visible; coinBack() is what the camera code calls when the coin returns.
 * The page must keep the stretches and lock the true seed without a 45 s unbroken stretch. */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto(PAGE);
  const seeds = [0x13572468, 0x9e3779b9, 0x0badf00d, 0x7f00ff01];
  for (const seed of seeds) {
    const out = await p.evaluate(async seed => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS;
      document.getElementById('reset').click();
      let s = seed >>> 0, nc = 5; const draws = [];
      for (let f = 0; f < 6000; f++) { if (f === nc) { const before = s; s = R.adv(s); const sh = s >= R.SHINE_MIN; draws.push({ f, before, sh }); nc = f + (sh ? 48 : 24); } s = R.adv(s); }
      const on = 450, off = 300, extra = 5; const t0 = 1e5;
      const realT = f => t0 + (f - 2.5 * Math.floor(f / (on + off)) * extra / 5 * 1) * F + 6 * F;   // 5 fast frames per load = 2.5 frames of time
      const wait = async c => { for (let i = 0; i < 900 && !c(); i++) await new Promise(r => setTimeout(r, 100)); };
      const log = []; let lockAt = null;
      for (let k = 0; k < 6 && !T.st.lock; k++) {
        const a = k * (on + off), z = a + on;
        for (const d of draws) if (d.sh && d.f >= a && d.f < z) { T.addShine(realT(d.f), true); await wait(() => !T.st.searching); if (T.st.lock && lockAt === null) lockAt = { stretch: k + 1, f: d.f }; if (T.st.lock) break; }
        log.push('stretch ' + (k + 1) + ': ' + document.getElementById('spins-count').textContent + ' cands ' + (T.st.cands ? T.st.cands.length : '-') + ' chain ' + T.st.chain.length);
        if (!T.st.lock) T.coinBack();
      }
      // the locked seed is the seed before the first draw of the current stretch
      const L = T.st.lock; let truth = null;
      if (L) { const t1 = T.st.segs[L.seg].taps[0]; const d = draws.find(q => q.sh && Math.abs(realT(q.f) - t1) < 1); truth = d && d.before >>> 0; }
      return { log, lock: L && (L.seed >>> 0).toString(16), truth: truth && truth.toString(16), lockAt, ok: !!L && L.seed >>> 0 === truth };
    }, seed);
    console.log(seed.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
