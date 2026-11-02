/* Feed the emulator run to the page frame by frame on a simulated clock (29.97 fps; while the page searches, the
 * clock waits): each frame is a 640x480 VideoFrame with the coin-box region from the run (rest black).
 * usage: node sr_feed.js DIR */
const { chromium } = require('playwright'); const fs = require('fs');
const DIR = process.argv[2], CW = 80, CH = 64, FB = CW * CH * 3, buf = fs.readFileSync(DIR + '/crops.rgb'), N = buf.length / FB;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1600 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.addInitScript(() => Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }));
  await p.goto(process.env.PAGE || 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');   // PAGE: another build to compare
  const t0 = await p.evaluate(() => {
    const S = { react: '200', lag: '0', off: '-5', min: '3', lead: '4', beeps: '4', gapms: '500', range: '1000', vlag: '50', wthr: '0', tmatch: '0.92', cpu: '2', zoom: '1.5', voff: '-6', pfix: '0' };
    for (const [k, v] of Object.entries(S)) { const el = document.getElementById('s-' + k); if (el) { el.value = v; el.dispatchEvent(new Event('change')); el.dispatchEvent(new Event('input')); } }
    const pr = document.getElementById('s-prof'); pr.value = 'endgame'; pr.dispatchEvent(new Event('change'));
    window.__tot.V.boxes.coin = { x: 0.78, y: 0.02, w: 0.065, h: 0.09 };
    window.__c = document.createElement('canvas'); window.__c.width = 640; window.__c.height = 480; window.__x = window.__c.getContext('2d');
    window.__x.fillStyle = '#000'; window.__x.fillRect(0, 0, 640, 480); window.__t0 = performance.now(); return window.__t0;
  });
  const BATCH = 150; const tl = [];
  for (let i0 = 0; i0 < N; i0 += BATCH) {
    const n = Math.min(BATCH, N - i0), chunk = buf.subarray(i0 * FB, (i0 + n) * FB).toString('base64');
    const r = await p.evaluate(async ({ chunk, i0, n, CW, CH }) => {
      const T = window.__tot, V = T.V, raw = Uint8Array.from(atob(chunk), c => c.charCodeAt(0)), img = window.__x.createImageData(CW, CH);
      for (let k = 0; k < n; k++) {
        for (let j = 0, s = k * CW * CH * 3; j < CW * CH; j++) { img.data[4 * j] = raw[s + 3 * j]; img.data[4 * j + 1] = raw[s + 3 * j + 1]; img.data[4 * j + 2] = raw[s + 3 * j + 2]; img.data[4 * j + 3] = 255; }
        window.__x.putImageData(img, 480, 0);
        const want = window.__t0 + (i0 + k) * 1001 / 30; window.__dt += want - performance.now();
        V.src = new VideoFrame(window.__c, { timestamp: (i0 + k) * 33367 }); T.onFrame(performance.now()); V.src.close(); V.src = null;
        while (T.st.searching) { const a = performance.now(); await new Promise(r => setTimeout(r, 50)); window.__dt -= performance.now() - a; }
      }
      return { lock: T.st.lock ? T.st.lock.seed >>> 0 : null, shines: V.shines, head: document.getElementById('headline').textContent.slice(0, 70) };
    }, { chunk, i0, n, CW, CH });
    if ((i0 / BATCH) % 10 === 0) console.log(i0, JSON.stringify(r));
  }
  const out = await p.evaluate(() => { const T = window.__tot; return { hist: T.V.hist || [], slog: T.SLOG, lock: T.st.lock && (T.st.lock.seed >>> 0) }; });
  fs.writeFileSync(DIR + '/page.json', JSON.stringify({ t0, ...out, errs }));
  console.log('errors', errs); await b.close();
})();
