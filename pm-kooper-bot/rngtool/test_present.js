/* Coin-present test on emulator frames (fixtures/present): the status bar up (lava room, a shine) must read "present";
 * frames without the bar (lava glow, the torch room, the quiz door's speech bubble over the coin box) must not.
 * Each image is fed to the page's frame handler as a VideoFrame for 1.5 s of page time. */
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const DIR = path.join(__dirname, 'fixtures', 'present');
const want = { lava_bar: true, shine_bar: true, maze_bar: true, lava_nohud: false, torch_nohud: false, quiz_00230: false, quiz_01450: false };
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  let ok = true; const res = {};
  for (const [name, exp] of Object.entries(want)) {
    const f = path.join(DIR, name + '.jpg'); if (!fs.existsSync(f)) { res[name] = 'missing'; ok = false; continue; }
    const src = 'data:image/jpeg;base64,' + fs.readFileSync(f).toString('base64');
    const got = await p.evaluate(async (src) => {
      const T = window.__tot, V = T.V; V.boxes.coin = { x: 0.78, y: 0.02, w: 0.065, h: 0.09 };
      const img = new Image(); img.src = src; await img.decode();
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; c.getContext('2d').drawImage(img, 0, 0);
      V.src = new VideoFrame(c, { timestamp: 0 }); V.present = false; V.wasGone = false; V.presentSince = 0;
      let t = performance.now(); for (let i = 0; i < 45; i++) { window.__dt += 33.4; T.onFrame(performance.now()); }
      const r = V.present; V.src.close(); V.src = null; return r;
    }, src);
    res[name] = got; if (got !== exp) ok = false;
  }
  console.log(JSON.stringify(res)); console.log(ok ? 'PASS' : 'FAIL'); console.log('errors', errs); await b.close();
})();
