/* Walk counter (zero-wait): after a long gap the coin comes back and the runner walks with C-up looks of 220 game frames
 * and 25-frame dropouts for 40 s (real time), with the coin's shines fed to the page. The sidebar counter must show the
 * real-time seconds with the coin visible and walked (within 0.3 s of the truth) and the bits so far; when the hallway
 * cutscene takes the bar away (a 12 s gap) the walk is logged ("walk" in the session log) and shown as "Last walk". */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, FR = R.FRAME_MS; document.getElementById('reset').click();
    const vlag = +document.getElementById('s-vlag').value, T0 = performance.now() + 1000, setNow = t => { window.__dt += t - performance.now(); };
    let s = 0x1234abcd, nc = 7; const shines = [];
    for (let f = 0; f < 1400; f++) { if (f === nc) { const q = R.randInt(s, 100); s = q[0]; nc = f + (q[1] >= 70 ? 48 : 24); if (q[1] >= 70) shines.push(f); } s = R.adv(s); }
    let vis = 0, mid = null; const F = 1200;                       // 40 s of walk = 1200 game frames
    for (let f = 0; f < F; f++) {
      const present = (f % 245) < 220, t = T0 + f * FR; setNow(t);
      if (present) vis += FR;
      T.walkWatch(t, present);
      if (present && shines.includes(f - 6) && (f % 245) >= 36) T.addShine(T0 + f * FR + vlag, true);
      if (f === 900) { await new Promise(r => setTimeout(r, 30)); mid = { text: document.getElementById('walk-counter').textContent, vis: +(vis / 1000).toFixed(1), walked: +(f * FR / 1000).toFixed(1) }; }
    }
    const tEnd = T0 + F * FR; setNow(tEnd + 12000 + 1000); T.coinBack(12000);
    const log = T.SLOG.filter(x => x.ev === 'walk').pop();
    return { mid, final: log, last: document.getElementById('walk-last').textContent, truth: { vis: +(vis / 1000).toFixed(2), walked: +(F * FR / 1000).toFixed(2) } };
  });
  console.log(JSON.stringify(out, null, 1));
  const num = (txt, re) => { const m = txt.match(re); return m ? +m[1] : NaN; };
  const mv = num(out.mid.text, /coin visible ([\d.]+) s/), mw = num(out.mid.text, /of ([\d.]+) s walked/);
  const ok = Math.abs(mv - out.mid.vis) <= 0.3 && Math.abs(mw - out.mid.walked) <= 0.3 && /of ~38 bits|locked/.test(out.mid.text) &&
    out.final && Math.abs(out.final.coinVisibleS - out.truth.vis) <= 0.3 && Math.abs(out.final.walkedS - out.truth.walked) <= 0.3 && /Last walk: coin visible/.test(out.last);
  console.log(ok ? 'PASS' : 'FAIL', 'errors', errs); await b.close();
})();
