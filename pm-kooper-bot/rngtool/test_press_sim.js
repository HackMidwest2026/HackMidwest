/* Press-timing readout with exact timing: the recorded emulator frames (rec_video_confirm.py) are fed to the page's
 * frame handler one by one with timestamps on a chosen clock (no camera, no playback jitter). RATE_MS sets the
 * console's frame length (33.367 = 59.94 Hz, 33.430 = 59.83 Hz N64 240p). The readout must give the true confirm frame. */
const { chromium } = require('playwright'); const fs = require('fs');
const T3 = require('/dev/shm/pmbot/vid3_truth.json');
const RATE = parseFloat(process.env.RATE_MS || '33.4300'), LAG = parseFloat(process.env.LAG_MS || '70');
(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1100, height: 1400 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => { window.__sim = null; const real = performance.now.bind(performance); performance.now = () => window.__sim !== null ? window.__sim : real(); });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const r = await p.evaluate(async ({ n, tgtF, RATE, LAG }) => {
    const T = window.__tot, V = T.V;
    V.boxes.coin = V.boxes.coin; V.boxes.target = { x: 0.135, y: 0.22, w: 0.135, h: 0.09 }; V.measureWin = 1e12;
    const load = async f => { const img = new Image(); img.src = 'file:///dev/shm/pmbot/vid/f' + String(f).padStart(5, '0') + '.png'; await img.decode(); return createImageBitmap(img); };
    // reference for the target screen
    const bm = await load(tgtF); const cv = document.createElement('canvas'); cv.width = 24; cv.height = 16; const c = cv.getContext('2d');
    const bx = V.boxes.target; c.drawImage(bm, bx.x * bm.width, bx.y * bm.height, bx.w * bm.width, bx.h * bm.height, 0, 0, 24, 16);
    const g = c.getImageData(0, 0, 24, 16).data, ref = []; for (let i = 0; i < g.length; i += 4) ref.push((g[i] + g[i + 1] + g[i + 2]) / 3); V.ref = ref;
    const t00 = 1e6;
    for (let f = 0; f < n; f++) {
      const b = await load(f);
      for (const half of [0, 1]) {                       // 60 Hz video: each game frame shown for two video frames
        const t = t00 + f * RATE + half * RATE / 2 + LAG;
        window.__sim = t; V.src = new VideoFrame(b, { timestamp: Math.round(t * 1000) }); T.onFrame(t); V.src.close(); V.src = null;
      }
      b.close();
      while (T.st.searching) { const s = window.__sim; window.__sim = null; await new Promise(r => setTimeout(r, 200)); window.__sim = s; }
    }
    return { rate: T.st.rate, L: T.st.lastPress, lock: T.st.lock, shines: V.shines, msg: document.getElementById('press-msg').textContent, rowHidden: document.getElementById('press-row').hidden };
  }, { n: T3.frames, tgtF: T3.marks.target_screen + 30, RATE, LAG });
  const pre = new Map(T3.truth.filter(t => t.shine).map(t => [t.seed_before >>> 0, t.frame]));
  if (!r.L) { console.log('no measurement', JSON.stringify(r).slice(0, 300)); }
  else {
    const want = T3.marks.confirm - pre.get(r.L.seedBL >>> 0);
    console.log('RATE_MS', RATE, '| fitted frame ms', r.rate.toFixed(4), '| true confirm frame', want, '| measured', r.L.c.toFixed(2), '->', r.L.frame, want === r.L.frame ? 'MATCH' : 'MISMATCH'); console.log('readout:', r.rowHidden ? '(hidden)' : r.msg);
  }
  console.log('errors', errs); await b.close();
})();
