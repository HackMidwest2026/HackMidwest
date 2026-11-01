const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.selectOption('#s-prof', 'endgame'); await p.dispatchEvent('#s-prof', 'change');
  const r = await p.evaluate(async () => {
    const T = window.__tot, V = T.V;
    const mk = color => { const c = document.createElement('canvas'); c.width = 320; c.height = 240; const g = c.getContext('2d'); g.fillStyle = '#222'; g.fillRect(0, 0, 320, 240); g.fillStyle = color; g.fillRect(20, 20, 120, 40); return c; };
    const screenM = mk('#f0f0f0'), screenK = mk('#505050'), menu = mk('#222');
    const box = { x: 0.05, y: 0.06, w: 0.4, h: 0.2 }, ref = c => { const s = document.createElement('canvas'); s.width = 24; s.height = 16; const g = s.getContext('2d'); g.drawImage(c, box.x * 320, box.y * 240, box.w * 320, box.h * 240, 0, 0, 24, 16); const d = g.getImageData(0, 0, 24, 16).data, o = []; for (let i = 0; i < d.length; i += 4) o.push((d[i] + d[i + 1] + d[i + 2]) / 3); return o; };
    localStorage.setItem('tot-targets', JSON.stringify({ jr_M: { box, ref: ref(screenM) }, jr_K: { box, ref: ref(screenK) }, jr_S: { box, ref: ref(mk('#40c040')) }, jr_B: { box, ref: ref(mk('#c040c0')) } }));
    return 1;
  });
  await p.reload(); await p.selectOption('#s-prof', 'endgame'); await p.dispatchEvent('#s-prof', 'change');
  const out = await p.evaluate(async () => {
    const T = window.__tot, V = T.V, log = [];
    const mk = color => { const c = document.createElement('canvas'); c.width = 320; c.height = 240; const g = c.getContext('2d'); g.fillStyle = '#222'; g.fillRect(0, 0, 320, 240); g.fillStyle = color; g.fillRect(20, 20, 120, 40); return c; };
    const screens = { M: mk('#f0f0f0'), K: mk('#505050'), menu: mk('#222') };
    const cur = () => document.querySelector('#route-list li[style]').textContent;
    // jump to Jr T6 Power Bounce (step index 12 in the endgame route)
    for (let i = 0; i < 12; i++) document.getElementById('route-next').click();
    log.push('start: ' + cur());
    let t = 1e5;
    const show = async (which, frames) => { for (let i = 0; i < frames; i++) { t += 33.4; const vf = new VideoFrame(screens[which], { timestamp: Math.round(t * 1000) }); V.src = vf; T.onFrame(t); vf.close(); V.src = null; } };
    await show('menu', 10);
    await show('M', 30); log.push('the next fight\'s Mario screen appears instead of the optional Bomb: ' + cur());
    await show('menu', 30); log.push('after that screen closes: ' + cur());
    return log;
  });
  console.log(out.join('\n')); console.log('errors', errs); await b.close();
})();
