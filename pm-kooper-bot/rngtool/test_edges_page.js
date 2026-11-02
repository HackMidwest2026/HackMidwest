/* Short looks (the C-up status bar auto-hides after ~220 frames; re-opened ~25 frames later; shines count only once the
 * coin has been steady 1 s), as in the maze rooms. Every 2nd dropout is a room load with 0-6 frames of console load time
 * (clock runs, game does not). The page gets coinBack(hiddenMs) 1 s after the coin is back, like the camera code.
 * Compares time to a lock with and without the look-edge non-shines; any lock must be on the true trajectory. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const seeds = (process.argv[2] || '13572468,9e3779b9,0badf00d,7f00ff01,2468ace0,5eedf00d').split(',').map(x => parseInt(x, 16) >>> 0);
  let bad = 0; const sum = { on: [], off: [] };
  for (const seed of seeds) for (const edges of [true, false]) {
    const out = await p.evaluate(async ({ seed, edges }) => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS; T.EDGES.on = edges; document.getElementById('reset').click();
      let s = seed >>> 0, nc = 5; const draws = [];
      for (let f = 0; f < 9000; f++) { if (f === nc) { const before = s; s = R.adv(s); const sh = s >= R.SHINE_MIN; draws.push({ f, before, sh }); nc = f + (sh ? 48 : 24); } s = R.adv(s); }
      const setNow = t => { window.__dt += t - performance.now(); };
      const wait = async () => { for (let i = 0; i < 1200 && T.st.searching; i++) await new Promise(r => setTimeout(r, 50)); };
      let lag = 0, rnd = seed; const rand = n => { rnd = (rnd * 1103515245 + 12345) >>> 0; return rnd % n; };
      const tOf = f => 1e5 + (f + lag) * F + 6 * F;
      let a = 30, lockF = null;
      for (let k = 0; k < 40 && !T.st.lock; k++) {
        const z = a + 220;
        for (const d of draws) if (d.sh && d.f >= a + 30 && d.f < z - 4) { setNow(tOf(d.f) + 100); T.addShine(tOf(d.f), true); await wait(); if (T.st.lock) { lockF = d.f; break; } }
        if (T.st.lock) break;
        const hideT = tOf(z); const loadLag = k % 2 ? rand(7) : 0; lag += loadLag;
        const a2 = z + 25; const backT = tOf(a2);            // coin back at a2 (wall clock), reported 1 s later
        setNow(backT + 1000); T.coinBack(backT - hideT); await wait();
        a = a2;
      }
      let ok = null;
      if (T.st.lock) { const t1 = T.st.segs[T.st.lock.seg].taps[0]; const d = draws.find(q => q.sh && Math.abs(tOf(q.f) - t1) < 2); ok = !!d && (d.before >>> 0) === (T.st.lock.seed >>> 0); }
      T.EDGES.on = true;
      const cs = T.SLOG.filter(x => x.ev === 'chainSearch' || x.ev === 'chainSearchStopped').map(x => x.ev === 'chainSearch' ? x.stretches + ':' + x.found : 'stop'); T.SLOG.length = 0;
      return { lockS: lockF && +(lockF / 30).toFixed(1), ok, cs: cs.join(' ') };
    }, { seed, edges });
    if (out.ok === false) bad++;
    sum[edges ? 'on' : 'off'].push(out.lockS);
    console.log(seed.toString(16), edges ? 'edges' : 'no edges', JSON.stringify(out));
  }
  console.log('lock s with edges', sum.on.join(' '), '| without', sum.off.join(' '));
  console.log(bad ? 'FAIL (false lock)' : 'PASS (no false locks)'); console.log('errors', errs); await b.close();
})();
