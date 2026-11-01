/* Press-timing readout: footage with the confirm on a known frame (rec_video_confirm.py). The page must measure the
 * confirm frame (relative to its plan's last shine) from the moment the name box disappears. */
const { chromium } = require('playwright'); const fs = require('fs');
const T3 = require('/dev/shm/pmbot/vid3_truth.json');
const tgt = 'data:image/png;base64,' + fs.readFileSync('/dev/shm/pmbot/tgt3.png').toString('base64');
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--use-file-for-fake-video-capture=/dev/shm/pmbot/coin3.y4m', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ permissions: ['camera'] }); const p = await ctx.newPage({ viewport: { width: 1100, height: 1600 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  // the 4-core test box: let the search use all cores so the seed locks before the 64 s footage loops
  await p.addInitScript(() => Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }));
  await p.addInitScript(() => { window.__beeps = []; const AC = window.AudioContext; const o = AC.prototype.createOscillator; AC.prototype.createOscillator = function () { const ctx = this; const osc = o.call(this); const st = osc.start.bind(osc); osc.start = w => { window.__beeps.push(+(w - ctx.currentTime).toFixed(2)); st(w); }; return osc; }; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(async (src) => {
    const V = window.__tot.V; V.boxes.target = { x: 0.135, y: 0.22, w: 0.135, h: 0.09 }; V.measureWin = 1e9;
    const img = new Image(); img.src = src; await img.decode();
    const big = document.createElement('canvas'); big.width = 296; big.height = 200; big.getContext('2d').drawImage(img, 0, 0, 296, 200);
    const sm = document.createElement('canvas'); sm.width = 24; sm.height = 16; const c = sm.getContext('2d');
    const b = V.boxes.target; c.drawImage(big, b.x * 296, b.y * 200, b.w * 296, b.h * 200, 0, 0, 24, 16);
    const g = c.getImageData(0, 0, 24, 16).data, ref = []; for (let i = 0; i < g.length; i += 4) ref.push((g[i] + g[i + 1] + g[i + 2]) / 3); V.ref = ref;
    for (const [k, v] of [['lead', '1'], ['min', '1'], ['cpu', '4']]) document.getElementById('s-' + k).value = v;
    // accept the fake camera as the OBS camera
    const s = await navigator.mediaDevices.getUserMedia({ video: true }); Object.defineProperty(s.getVideoTracks()[0], 'label', { value: 'OBS Virtual Camera (test)' });
    navigator.mediaDevices.getUserMedia = async () => s; const sel = document.getElementById('cam-sel'); const o = document.createElement('option'); o.value = 'x'; sel.appendChild(o); sel.value = 'x';
  }, tgt);
  await p.click('#cam-start');
  const pre = new Map(T3.truth.filter(t => t.shine).map(t => [t.seed_before >>> 0, t.frame]));
  let res = null;
  for (let s = 0; s < 100; s += 2) {
    await p.waitForTimeout(2000);
    const r = await p.evaluate(() => { const T = window.__tot, L = T.st.lastPress; return { shines: T.V.shines, lock: !!T.st.lock, rate: T.st.rate, plan: L && { target: L.target, seedBL: L.seedBL >>> 0, measured: L }, msg: document.getElementById('press-msg').textContent }; });
    if (s % 10 === 0) console.log(s + 2 + 's', JSON.stringify(r).slice(0, 200));
    if (r.plan && r.plan.measured) { res = r; break; }
  }
  const dbg = await p.evaluate(() => { const T = window.__tot; return { segs: T.st.segs.map(s => s.taps), lock: T.st.lock, clock: T.st.clock, rate: T.st.rate, L: T.st.lastPress, hist: T.V.hist }; });
  fs.writeFileSync('/dev/shm/pmbot/cam4_dbg.json', JSON.stringify(dbg));
  if (res) {
    const f0 = pre.get(res.plan.seedBL), want = T3.marks.confirm - f0;
    console.log('true confirm frame (rel. to the plan\'s last shine draw):', want, '| measured:', res.plan.measured.c.toFixed(2), '-> frame', res.plan.measured.frame, '| readout:', res.msg);
  } else console.log('no measurement');
  console.log('beeps scheduled (seconds ahead when scheduled):', JSON.stringify(await p.evaluate(() => window.__beeps)));
  console.log('errors', errs); await b.close();
})();
