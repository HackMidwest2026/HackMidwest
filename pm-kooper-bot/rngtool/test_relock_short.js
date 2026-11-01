/* Re-finding a lock from short stretches (maze rooms): lock seed A, then an enemy room (extra draws, coin hidden),
 * then stretches of only 2-3 shines with the coin hidden 6-10 s between them (room loads; the coin keeps drawing). No
 * single stretch has the ~6 shines a resync needs; together they must re-lock on A's trajectory. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  for (const seed of [0x0ddba12, 0x5eedf00d, 0x1234abcd, 0x2b2b2b2b]) {
    const out = await p.evaluate(async seed => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS, vlag = +document.getElementById('s-vlag').value;
      document.getElementById('reset').click();
      const wait = async c => { for (let i = 0; i < 900 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      const S = { s: seed >>> 0, nc: 5, inst: [] }, sh = [];
      for (let f = 0; f < 9000; f++) { if (f >= 1500 && f < 2100 && f % 37 === 0) for (let k = 0; k < 3; k++) S.s = R.randInt(S.s, 30)[0]; if (R.frameEv(S, f, null)) sh.push(f); }
      const tap = f => 1e5 + (f + 6) * F + vlag;
      for (const f of sh.filter(f => f < 1450)) T.addShine(tap(f), true);
      await wait(() => T.st.lock); if (!T.st.lock) return { skipped: 'no starting lock from 48 s of shines' }; T.coinBack();
      // short stretches: visible ~7 s (210 frames), hidden ~8 s (240 frames)
      let n = 0, stretches = 0, at = null;
      for (let a = 2200; a < 9000 && !T.st.lock; a += 450) {
        const vis = sh.filter(f => f >= a && f < a + 210).slice(0, 3); if (!vis.length) continue; stretches++;
        for (const f of vis) { T.addShine(tap(f), true); n++; await wait(() => !T.st.searching); if (T.st.lock) { at = { stretches, shines: n }; break; } }
        if (!T.st.lock) T.coinBack();
      }
      const want = T.st.lock && T.st.lock.seed >>> 0; let onA = false;
      const S2 = { s: seed >>> 0, nc: 5, inst: [] };
      for (let f = 0; f < 9000 && !onA; f++) { if (f >= 1500 && f < 2100 && f % 37 === 0) for (let k = 0; k < 3; k++) S2.s = R.randInt(S2.s, 30)[0]; if (f === S2.nc && S2.s >>> 0 === want) onA = true; R.frameEv(S2, f, null); }
      return { relocked: !!T.st.lock, onTrueTrajectory: onA, after: at };
    }, seed);
    console.log(seed.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
