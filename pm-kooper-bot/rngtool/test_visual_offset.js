// At the moment the beep plays (tPress), where is the now-line relative to the gold middle line? For voff = off it must coincide.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1000, height: 1300 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  const url = 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
  for (const [off, voff] of [[-6, -6], [-6, 0], [-6, -12]]) {
    await p.goto(url); await p.evaluate(([o, v]) => { localStorage.setItem('tot-settings', JSON.stringify({ off: String(o), voff: String(v), zoom: '1.5' })); }, [off, voff]); await p.goto(url);
    const r = await p.evaluate(async () => {
      const T = window.__tot, R = T.R; let s = 0x2468ace0, f = 0; const taps = []; const now = performance.now();
      while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
      const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
      while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
      T.makePlan(); const P = T.st.plan;
      while (performance.now() < P.tPress - 20) await new Promise(r => requestAnimationFrame(r));
      while (performance.now() < P.tPress) await new Promise(r => setTimeout(r, 1));
      await new Promise(r => requestAnimationFrame(r));
      // read the canvas: columns of the white now-line and the gold middle line at the top rows
      const cv = document.getElementById('strip'), c = cv.getContext('2d'), w = cv.width, row = c.getImageData(0, Math.round(6 * (window.devicePixelRatio || 1)), w, 1).data;
      const cols = { now: [], gold: [] }; const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
      for (let x = 0; x < w; x++) { const r_ = row[4 * x], g = row[4 * x + 1], b_ = row[4 * x + 2], a_ = row[4 * x + 3]; if (a_ < 200) continue; if (r_ + g + b_ < 120) cols.now.push(x); else if (r_ > 150 && g > 100 && b_ < 90) cols.gold.push(x); }
      const avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
      return { nowX: avg(cols.now), goldX: avg(cols.gold), pxPerFrame: w / 45, corr: T.V.corr, nowCols: cols.now.length, goldCols: cols.gold.length, w, dpr: window.devicePixelRatio, cw: cv.clientWidth };
    });
    console.log('beep offset', off, 'visual offset', voff, '-> at the beep, now-line minus gold line =', ((r.nowX - r.goldX) / r.pxPerFrame).toFixed(2), 'frames', JSON.stringify(r));
  }
  console.log('errors', errs); await b.close();
})();
