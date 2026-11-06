/* The strip's geometry (feedback items 1 and 5):
 *  1. fastTable (the strip's and the planner's working-frame table) equals R.timeOutTable / R.works frame for frame.
 *  2. The aim marker is drawn in the middle of the aimed cell, never on a boundary: in game frames it is target + 0.5, and
 *     on the canvas the gold column's centre is the centre of the aimed cell (+-1 px), for whole and fractional offsets.
 *  3. The now-line meets the aim marker at the visual cue, tLast + (target - 0.5 + voff) * rate (+-0.05 frame), and
 *     is inside the aimed cell exactly while a press (with the visual offset) lands on the aimed frame.
 *  4. The now-line stays at 25% of the width before, during and after a plan (v69 moved it from 10% to 25% when a plan
 *     was made), and the displayed "now" advances at the clock's pace through makePlan (no jump).
 * usage: node test_strip_geometry.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
(async () => {
  const b = await chromium.launch(); const errs = [];
  // 1. fastTable vs timeOutTable
  { const p = await b.newPage(); p.on('pageerror', e => errs.push(String(e))); await p.goto('file://' + PAGE);
    const r = await p.evaluate(() => { const T = window.__tot, R = T.R; let bad = 0, n = 0; let s = 0x13579bdf;
      for (let k = 0; k < 12; k++) { s = R.adv(R.adv(s ^ (k * 0x9e3779b9))); const a = (k * 37) % 200, bb = a + 260;
        const A = R.timeOutTable(s >>> 0, a, bb, R.PROFILES.timeout), B = T.fastTable(s >>> 0, 0, 0, a, bb, R.PROFILES.timeout);
        for (let i = 0; i < A.length; i++) { n++; if (A[i] !== B[i]) bad++; }
        // a state in the middle of the coin cycle (next draw at g + 11)
        const g = 40, nc = g + 11; for (let c = g; c < g + 120; c++) { n++; if (R.works(s >>> 0, nc, c, g, R.PROFILES.timeout) !== T.fastTable(s >>> 0, nc, g, c, c, R.PROFILES.timeout)[0]) bad++; } }
      return { bad, n }; });
    console.log('1. fastTable vs R.timeOutTable / R.works:', JSON.stringify(r)); check(r.bad === 0 && r.n > 3000, 'fastTable differs from R.timeOutTable');
    await p.close(); }
  // 2-4 per visual offset
  for (const voff of [0, -6, -4.5, 2.3]) {
    const p = await b.newPage({ viewport: { width: 1000, height: 1300 } }); p.on('pageerror', e => errs.push(String(e)));
    await p.goto('file://' + PAGE); await p.evaluate(v => localStorage.setItem('tot-settings', JSON.stringify({ off: '-5', voff: String(v), zoom: '1.5', wtype: 'green', zwwin: '6', beeps: '3' })), voff); await p.goto('file://' + PAGE);
    const r = await p.evaluate(async () => {
      const T = window.__tot, R = T.R, G = () => T.V.stripGeom; let s = 0x2468ace0, f = 0; const taps = [], now = performance.now();
      while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
      const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
      while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
      T.setStep(T.RT().findIndex(x => x.prof === 'timeout'));
      const raf = () => new Promise(r => requestAnimationFrame(r)), nowX = () => { const g = G(); return (g.nowD - g.v0) * g.cw; };
      const samples = []; for (let i = 0; i < 20; i++) { await raf(); samples.push([performance.now(), T.V.dispAbs, nowX(), G().W]); }
      T.makePlan(); const P = T.st.plan;
      for (let i = 0; i < 40; i++) { await raf(); samples.push([performance.now(), T.V.dispAbs, nowX(), G().W]); }
      // the visual cue: the now-line at the aim marker
      const voff = parseFloat(document.getElementById('s-voff').value), tCue = P.tLast + (P.target - 0.5 + voff) * P.rate;
      while (performance.now() < tCue - 30) await new Promise(r => setTimeout(r, 10));
      let cue = null; while (!cue) { await raf(); const g = G(), t = performance.now(); if (t >= tCue - 17) cue = { dt: t - tCue, nowD: g.nowD, target: g.target, rate: P.rate }; }
      // the canvas: gold column centre vs the aimed cell's edges, at a row through the cells where only the marker is gold
      const g = G(), cv = document.getElementById('strip'), dpr = window.devicePixelRatio || 1, c = cv.getContext('2d');
      const cellL = (P.target - g.v0) * g.cw, cellR = (P.target + 1 - g.v0) * g.cw, mark = (P.target + 0.5 - g.v0) * g.cw;
      const row = c.getImageData(0, Math.round(10 * dpr), cv.width, 1).data, cols = [];   // y = 10: above the cells, only the marker's triangle and stem
      for (let x = 0; x < cv.width; x++) { const R_ = row[4 * x], G_ = row[4 * x + 1], B_ = row[4 * x + 2]; if (R_ > 150 && G_ > 100 && B_ < 110 && R_ > B_ + 60) cols.push(x / dpr); }
      const gold = cols.length ? cols.reduce((a, x) => a + x, 0) / cols.length : null;
      return { samples, cue, cellL, cellR, mark, gold, target: P.target, w: P.w, type: P.type };
    });
    // 2. marker in the middle of the aimed cell
    const mid = (r.cellL + r.cellR) / 2;
    check(Math.abs(r.mark - mid) < 1e-6, `voff ${voff}: aim marker ${r.mark} is not the cell centre ${mid}`);
    check(r.gold != null && Math.abs(r.gold - mid) <= 1.0, `voff ${voff}: gold column centre ${r.gold} is not the cell centre ${mid.toFixed(2)} (cell ${r.cellL.toFixed(1)}-${r.cellR.toFixed(1)})`);
    const mids = r.w.length % 2 ? [r.w.start + (r.w.length - 1) / 2] : [r.w.start + r.w.length / 2 - 1, r.w.start + r.w.length / 2];
    check(mids.includes(r.target), `voff ${voff}: target ${r.target} is not a middle frame of ${JSON.stringify(r.w)}`);
    // 3. now-line at the marker at the cue (corrected for the sample's time offset)
    const at = r.cue.nowD - r.cue.dt / r.cue.rate - (r.cue.target + 0.5);
    check(Math.abs(at) < 0.05, `voff ${voff}: at the visual cue the now-line is ${at.toFixed(3)} frames from the aim marker`);
    // 4. now-line fixed at 25% and the displayed now steady through makePlan
    const xs = r.samples.map(x => x[2] / x[3]); const spread = Math.max(...xs) - Math.min(...xs);
    check(spread < 0.002 && Math.abs(xs[0] - 0.25) < 0.002, `voff ${voff}: the now-line moved on the strip (${Math.min(...xs).toFixed(4)}-${Math.max(...xs).toFixed(4)} of the width)`);
    let worst = 0; for (let i = 1; i < r.samples.length; i++) { const exp = (r.samples[i][0] - r.samples[i - 1][0]) / 33.367, got = r.samples[i][1] - r.samples[i - 1][1]; worst = Math.max(worst, Math.abs(got - exp)); }
    check(worst < 0.1, `voff ${voff}: the displayed now jumped by ${worst.toFixed(3)} frames between animation frames`);
    console.log(`voff ${voff}: window ${r.type} ${JSON.stringify(r.w)} target ${r.target}; marker ${r.mark.toFixed(2)} px, gold column ${r.gold && r.gold.toFixed(2)} px, cell ${r.cellL.toFixed(2)}-${r.cellR.toFixed(2)}; now-line at the cue ${at.toFixed(3)} frames from the marker; now-line at ${(xs[0] * 100).toFixed(2)}% (spread ${spread.toFixed(4)}); worst step ${worst.toFixed(3)} frames`);
    await p.close();
  }
  console.log('errors', JSON.stringify(errs)); console.log(fails || errs.length ? 'FAILED ' + fails : 'PASS'); await b.close(); process.exit(fails || errs.length ? 1 : 0);
})();
