const { chromium } = require('playwright'); const fs = require('fs');
const T2 = require('/dev/shm/pmbot/vid2_truth.json');
const tgt = 'data:image/png;base64,' + fs.readFileSync('/dev/shm/pmbot/tgt.b64', 'utf8');
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--use-file-for-fake-video-capture=/dev/shm/pmbot/coin2.y4m', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ permissions: ['camera'] }); const p = await ctx.newPage({ viewport: { width: 1100, height: 1600 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  // one-time setup: target box + reference taken from a target-screen frame (what Save target screen does)
  await p.evaluate(async (src) => {
    const V = window.__tot.V; V.boxes.target = { x: 0.135, y: 0.22, w: 0.135, h: 0.09 };
    const img = new Image(); img.src = src; await img.decode();
    const big = document.createElement('canvas'); big.width = 296; big.height = 200; big.getContext('2d').drawImage(img, 0, 0, 296, 200);
    const sm = document.createElement('canvas'); sm.width = 24; sm.height = 16; const c = sm.getContext('2d');
    const b = V.boxes.target; c.drawImage(big, b.x * 296, b.y * 200, b.w * 296, b.h * 200, 0, 0, 24, 16);
    const g = c.getImageData(0, 0, 24, 16).data, ref = []; for (let i = 0; i < g.length; i += 4) ref.push((g[i] + g[i + 1] + g[i + 2]) / 3); V.ref = ref;
  }, tgt);
  await p.click('#cam-start');
  const pre = new Map(T2.truth.filter(t => t.shine).map(t => [t.seed_before >>> 0, t.frame]));
  let planned = null;
  const locks = new Set();
  for (let s = 0; s < 128; s += 2) {
    await p.waitForTimeout(2000);
    const r = await p.evaluate(() => { const T = window.__tot; return { t: Math.round(performance.now() / 1000), shines: T.V.shines, segs: T.st.segs.map(x => x.taps.length), cands: T.st.cands && T.st.cands.length, lock: T.st.lock && { seg: T.st.lock.seg, seed: T.st.lock.seed >>> 0 }, msg: T.st.msg, present: T.V.present, score: +T.V.score.toFixed(3), plan: T.st.plan && { w: T.st.plan.w, seedBL: T.st.plan.seedBL >>> 0, inS: +((T.st.plan.tPress - performance.now()) / 1000).toFixed(2) } }; });
    if (r.lock) locks.add(r.lock.seed);
    const lk = r.lock ? ' lock seed is a true pre-shine seed (video frame ' + pre.get(r.lock.seed) + ')' : '';
    if (s % 10 === 0 || r.plan) console.log(s + 2 + 's', JSON.stringify(r).slice(0, 230));
    if (r.plan) { planned = r; break; }
  }
  if (planned) {
    const f = pre.get(planned.plan.seedBL);
    console.log('plan anchored on the true shine at video frame', f, '(target screen from frame', T2.marks.target_screen + ')');
  }
  fs.writeFileSync('/dev/shm/pmbot/cam2_locks.json', JSON.stringify({ locks: [...locks], plan: planned && planned.plan }));
  const dump = await p.evaluate(() => { const T = window.__tot; return { segs: T.st.segs.map(x => x.taps), hist: T.V.hist || [], lock0: T.st.segs[0] && T.st.lock }; });
  fs.writeFileSync('/dev/shm/pmbot/cam2_dump.json', JSON.stringify(dump));
  await p.screenshot({ path: 'cam2.png' });
  console.log('errors', errs);
  await b.close();
})();
