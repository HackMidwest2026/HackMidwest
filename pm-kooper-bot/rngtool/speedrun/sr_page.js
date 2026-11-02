/* Play the emulator "run" video into the Time Out Timer page as its OBS camera (user's settings from their log) and
 * record what the page does. usage: node sr_page.js DIR seconds */
const { chromium } = require('playwright'); const fs = require('fs');
const DIR = process.argv[2], SECS = +process.argv[3];
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--use-file-for-fake-video-capture=' + DIR + '/run.y4m', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ permissions: ['camera'] }); const p = await ctx.newPage({ viewport: { width: 1100, height: 1600 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(async () => {
    const S = { react: '200', lag: '0', off: '-5', min: '3', lead: '4', beeps: '4', gapms: '500', range: '1000', vlag: '50', wthr: '0', tmatch: '0.92', cpu: '2', zoom: '1.5', voff: '-6', pfix: '0' };
    for (const [k, v] of Object.entries(S)) { const el = document.getElementById('s-' + k); if (el) { el.value = v; el.dispatchEvent(new Event('change')); el.dispatchEvent(new Event('input')); } }
    const pr = document.getElementById('s-prof'); pr.value = 'endgame'; pr.dispatchEvent(new Event('change'));
    window.__tot.V.boxes.coin = { x: 0.78, y: 0.02, w: 0.065, h: 0.09 };          // the coin only (not the x after it)
    const s = await navigator.mediaDevices.getUserMedia({ video: true }); Object.defineProperty(s.getVideoTracks()[0], 'label', { value: 'OBS Virtual Camera (test)' });
    navigator.mediaDevices.getUserMedia = async () => s; const sel = document.getElementById('cam-sel'); const o = document.createElement('option'); o.value = 'x'; sel.appendChild(o); sel.value = 'x';
  });
  const t0 = await p.evaluate(() => performance.now()); await p.click('#cam-start');
  const tl = [];
  for (let s = 0; s < SECS; s++) {
    await p.waitForTimeout(1000);
    const r = await p.evaluate(() => { const T = window.__tot; return { t: performance.now(), shines: T.V.shines, fps: Math.round(T.V.fps), present: T.V.present, lock: T.st.lock ? (T.st.lock.seed >>> 0) : null, cands: T.st.cands ? T.st.cands.length : null, head: document.getElementById('headline').textContent.slice(0, 80) }; });
    tl.push(r); if (s % 15 === 0) console.log(s, JSON.stringify(r));
  }
  const out = await p.evaluate(() => { const T = window.__tot; return { hist: T.V.hist || [], slog: T.SLOG, lock: T.st.lock && (T.st.lock.seed >>> 0) }; });
  fs.writeFileSync(DIR + '/page.json', JSON.stringify({ t0, tl, ...out, errs }));
  await p.screenshot({ path: DIR + '/page_end.png' });
  console.log('errors', errs); await b.close();
})();
