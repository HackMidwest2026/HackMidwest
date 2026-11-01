const { chromium } = require('playwright');
const truth = require('/dev/shm/pmbot/vid_truth.json');
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--use-file-for-fake-video-capture=/dev/shm/pmbot/coin.y4m', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ permissions: ['camera'] }); const p = await ctx.newPage({ viewport: { width: 1100, height: 1500 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.click('#cam-start');
  const seeds = new Set(truth.filter(t => t.shine).map(t => t.seed_before >>> 0));
  for (let s = 0; s < 75; s += 5) {
    await p.waitForTimeout(5000);
    const r = await p.evaluate(() => { const T = window.__tot; return { shines: T.V.shines, fps: T.V.fps, taps: T.st.segs.map(x => x.taps.length), cands: T.st.cands && T.st.cands.length, lock: T.st.lock && T.st.lock.seed, searching: T.st.searching, msg: T.st.msg, present: T.V.present, pat: T.R.patternFromTaps(T.st.segs[T.st.segs.length - 1].taps).pattern }; });
    console.log(s + 5 + 's', JSON.stringify(r), r.lock ? ('lock is a true pre-shine seed: ' + seeds.has(r.lock >>> 0)) : '');
    if (r.lock) break;
  }
  await p.screenshot({ path: 'cam.png' });
  console.log('errors', errs);
  await b.close();
})();
