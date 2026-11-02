/* Closed-loop page host for the fight "speedrun" (sr_fight.py): the page runs on a simulated clock, one call per game
 * frame. stdin, one JSON line each: {f: video frame index, jpg: base64 JPEG 640x480}, or a command {cmd: 'save', box}
 * (= the runner drawing the target box and pressing Save target screen while that screen is up), {cmd: 'log'}.
 * stdout: one JSON line per input line: page time of the frame, route step, lock, the running plan (final beep time).
 * Settings: the runner's from their log, except the lags: the emulator video has no capture delay (vlag 0) and the
 * runner presses on the final beep (off 0), so the page's frame numbers are the game's.
 * usage: node sr_live.js  (env PAGE: another build) */
const { chromium } = require('playwright'); const readline = require('readline');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1600 } }); const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.addInitScript(() => Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 }));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto(process.env.PAGE || 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const t0 = await p.evaluate((S) => {
    for (const [k, v] of Object.entries(S)) { const el = document.getElementById('s-' + k); if (el) { el.value = v; el.dispatchEvent(new Event('change')); el.dispatchEvent(new Event('input')); } }
    const pr = document.getElementById('s-prof'); pr.value = 'endgame'; pr.dispatchEvent(new Event('change'));
    const T = window.__tot; T.V.boxes.coin = { x: 0.78, y: 0.02, w: 0.065, h: 0.09 }; T.V.stream = { getTracks: () => [], getVideoTracks: () => [] };
    window.__c = document.createElement('canvas'); window.__c.width = 640; window.__c.height = 480; window.__x = window.__c.getContext('2d');
    window.__t0 = performance.now(); T.setStep(0); return window.__t0;
  }, Object.assign({ react: '200', lag: '0', off: '0', min: '3', lead: '4', beeps: '4', gapms: '500', range: '1000', vlag: '0', wthr: '0', tmatch: '0.92', cpu: '2', zoom: '1.5', voff: '-6', pfix: '0' }, JSON.parse(process.env.SR_SET || '{}')));
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    const m = JSON.parse(line);
    if (m.cmd === 'save') {
      // the page stores a saved screen under the current step's kind: step to the first step of that kind and back
      const r = await p.evaluate(({ box, cat }) => {
        const T = window.__tot, cur = T.step(), i = cat ? T.RT().findIndex(s => s.cat === cat) : cur, swap = i >= 0 && i !== cur;
        const pd = Object.assign({}, T.V.preDone || {}), pv = Object.assign({}, T.V.pre || {});   // (stepping back and forth would forget this turn's seen inputs)
        if (swap) T.setStep(i);
        T.V.boxes.target = box; const bt = document.getElementById('cap-target'); bt.disabled = false; T.V.src = new VideoFrame(window.__c, { timestamp: 0 }); bt.click(); T.V.src.close(); T.V.src = null;
        const ok = !!T.V.ref; if (swap) { T.setStep(cur); T.V.preDone = pd; T.V.pre = pv; } return { ref: ok, step: T.step(), as: i }; }, { box: m.box, cat: m.cat });
      process.stdout.write(JSON.stringify(r) + '\n'); continue;
    }
    if (m.cmd === 'eval') { const r = await p.evaluate(m.js); process.stdout.write(JSON.stringify({ r }) + '\n'); continue; }
    if (m.cmd === 'log') {
      const r = await p.evaluate(() => ({ slog: window.__tot.SLOG, presses: document.getElementById('press-msg').textContent, carry: document.getElementById('carry-note').textContent, head: document.getElementById('headline').textContent }));
      process.stdout.write(JSON.stringify(Object.assign(r, { errs, t0 })) + '\n'); continue;
    }
    const r = await p.evaluate(async ({ f, jpg }) => {
      const T = window.__tot, V = T.V;
      const bmp = await createImageBitmap(new Blob([Uint8Array.from(atob(jpg), c => c.charCodeAt(0))], { type: 'image/jpeg' }));
      window.__x.drawImage(bmp, 0, 0, 640, 480); bmp.close();
      const want = window.__t0 + f * 1001 / 30; window.__dt += want - performance.now();
      V.src = new VideoFrame(window.__c, { timestamp: f * 33367 }); T.onFrame(performance.now()); V.src.close(); V.src = null;
      let waited = 0;
      while (T.st.searching) { const a = performance.now(); await new Promise(r => setTimeout(r, 50)); waited += performance.now() - a; window.__dt -= performance.now() - a; }
      const P = T.st.plan;
      return { t: performance.now(), step: T.step(), lock: T.st.lock ? T.st.lock.seed >>> 0 : null, score: +V.score.toFixed(3), present: V.present, shines: V.shines, waited: Math.round(waited),
        plan: P ? { tPress: P.tPress, target: P.target, w: P.w, tMade: P.tMade, seedBL: P.seedBL >>> 0, baseF: P.baseF, tLast: P.tLast, rate: P.rate, prof: P.prof, measured: P.measured || null } : null,
        turns: T.st.turnEv.length, resync: T.st.needResync, nslog: T.SLOG.length };
    }, m);
    process.stdout.write(JSON.stringify(r) + '\n');
  }
  await b.close();
})();
