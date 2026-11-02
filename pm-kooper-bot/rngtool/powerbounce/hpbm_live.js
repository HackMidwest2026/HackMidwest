/* Closed-loop page host for the High Power Bounce Manipulator emulator test (hpbm_run.py): the page runs on a simulated
 * clock, one call per game frame. stdin, one JSON line each: {f: video frame index, jpg: base64 JPEG 640x480}, or a
 * command {cmd: 'eval', js}, {cmd: 'log'}. stdout: one JSON line per input line.
 * Settings: the emulator video has no capture delay (vlag 0) and the runner presses on the final beep (off 0), so the
 * page's frame numbers are the game's. While the seed search runs, the game is paused (the clock does not move).
 * usage: node hpbm_live.js  (env PAGE: another build, HPBM_SET: JSON of page settings) */
const { chromium } = require('playwright'); const readline = require('readline');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1600 } }); const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.addInitScript(() => Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto(process.env.PAGE || 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/hpbm/high_power_bounce_manipulator_standalone.html');
  const t0 = await p.evaluate((S) => {
    const fe = document.getElementById('s-fight'); fe.value = S.fight || 'blooper'; fe.dispatchEvent(new Event('change'));
    for (const [k, v] of Object.entries(S)) { const el = document.getElementById('s-' + k); if (el && k !== 'fight') { el.value = v; el.dispatchEvent(new Event('change')); } }
    const H = window.__hpbm; H.V.boxes.coin = { x: 0.78, y: 0.02, w: 0.065, h: 0.09 }; H.V.stream = { getTracks: () => [], getVideoTracks: () => [] };
    window.__c = document.createElement('canvas'); window.__c.width = 640; window.__c.height = 480; window.__x = window.__c.getContext('2d');
    window.__t0 = performance.now(); return window.__t0;
  }, Object.assign({ off: '0', vlag: '0', lead: '3', beeps: '4', gapms: '500', cpu: '2', wthr: '0', horizon: '20' }, JSON.parse(process.env.HPBM_SET || '{}')));
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    const m = JSON.parse(line);
    if (m.cmd === 'eval') { const r = await p.evaluate(m.js); process.stdout.write(JSON.stringify({ r }) + '\n'); continue; }
    if (m.cmd === 'log') {
      const r = await p.evaluate(() => ({ slog: window.__hpbm.SLOG, tries: window.__hpbm.st.tries, cal: window.__hpbm.calibration(), summary: document.getElementById('cal-summary').textContent, head: document.getElementById('headline').textContent }));
      process.stdout.write(JSON.stringify(Object.assign(r, { errs, t0 })) + '\n'); continue;
    }
    const r = await p.evaluate(async ({ f, jpg }) => {
      const H = window.__hpbm, V = H.V;
      try { const bmp = await createImageBitmap(new Blob([Uint8Array.from(atob(jpg), c => c.charCodeAt(0))], { type: 'image/jpeg' }));
        window.__x.drawImage(bmp, 0, 0, 640, 480); bmp.close(); } catch (e) { window.__bad = (window.__bad || 0) + 1; }   // a torn screenshot: keep the previous picture
      const want = window.__t0 + f * 1001 / 30; window.__dt += want - performance.now();
      V.src = new VideoFrame(window.__c, { timestamp: f * 33367 }); H.onFrame(performance.now()); V.src.close(); V.src = null;
      let waited = 0;
      while (H.st.searching) { const a = performance.now(); await new Promise(r => setTimeout(r, 50)); waited += performance.now() - a; window.__dt -= performance.now() - a; }
      const P = H.st.plan;
      return { t: performance.now(), lock: H.st.lock ? H.st.lock.seed >>> 0 : null, present: V.present, shines: V.shines, taps: H.st.taps.length, waited: Math.round(waited), awaiting: !!H.st.awaiting,
        head: document.getElementById('headline').textContent,
        plan: P ? { tPress: P.tPress, d: P.d, count: P.count, K: P.K, near: P.near, baseT: P.base.t, rate: P.rate, tMade: P.tMade } : null };
    }, m);
    process.stdout.write(JSON.stringify(r) + '\n');
  }
  await b.close();
})();
