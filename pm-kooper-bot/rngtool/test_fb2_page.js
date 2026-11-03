/* Final Bowser T6 -> T7 through the page in headless Chromium, fed frame by frame (no <video> decoding: live clip
 * playback here dropped many frames). Each capture frame (JPEG, decoded ahead in the page) is handed to the page's own
 * per-frame entry (onFrame, with the frame as V.src, as its background-capture path does) at its real time: frame i at
 * start + i / 60 s, so the lock and the plan run against the clock as they would live; a frame more than 25 ms late
 * is dropped (as a busy browser drops pictures) and counted.
 * The page starts on the Final Bowser Power Bounce step (its pre is the T6 Charge) with the coin box on this layout.
 * usage: node test_fb2_page.js URLBASE DIR NFRAMES [T5ATTACK=any]   (URLBASE/tot.html = the standalone page,
 *        URLBASE/DIR/f%05d.jpg = the capture frames; serve with python3 -m http.server --bind 127.0.0.1)
 * Prints JSON: the trigger, the lock (seed, score, time after the rays end, stage times), the FB2 states, the beeped
 * popup frame K with its chances, the K the page read from the popup closing, and the page's log of these events.
 * KAT=k: also the popup plan as if the lock had landed in time for frame k on (no beeps); T7C=c: the T7 plan as if the
 * Power Bounce target screen showed on frame c (both confirm-relative). TRUTH=s61hex:nextcoin:p130:p220 (fb2_route/t6_truth.py):
 * whether that state, and with those lightning phases, is among the kept ones. */
const { chromium } = require('playwright');
(async () => {
  const [base, dir, nf] = [process.argv[2], process.argv[3], +process.argv[4]], t5 = process.argv[5] || 'any';
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
  });
  await p.goto(base + '/tot.html');
  const out = await p.evaluate(async ({ base, dir, nf, t5, kAt, t7c, wait, truth }) => {
    const T = window.__tot; document.getElementById('s-fb2t5').value = t5;
    T.setStep(T.RT().findIndex(s => s.turn === 'fb2_pb'));
    const url = i => base + '/' + dir + '/f' + String(i).padStart(5, '0') + '.jpg';
    const bmp = new Map(); let next = 0;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(url(k)).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    want(0); await bmp.get(0); for (let i = 1; i < 60; i++) await bmp.get(i);
    const t0 = performance.now() + 300, late = [], prof = { n: 0, sum: 0, max: 0, slow: 0, by: {} };
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25) { late.push(i); im.close(); continue; }   // a busy page drops the picture, as a browser does
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      const ta = performance.now(); T.V.src = vf; try { T.onFrame(tf); } finally { T.V.src = null; vf.close(); } const dt = performance.now() - ta; prof.n++; prof.sum += dt; if (dt > prof.max) prof.max = dt; if (dt > 12) { prof.slow++; const k = T.CHG.state; prof.by[k] = (prof.by[k] || 0) + 1; }
    }
    await new Promise(r => setTimeout(r, wait || 500));
    // the plans as if the lock had landed in time: the popup frame from kAt on (KAT), the T7 target A from screen frame T7C
    const F2 = window.__fb2, extra = {};
    if (F2 && F2.FB2.on) { if (kAt) extra.planKAt = F2.planKAt(kAt); if (t7c) extra.planT7At = F2.planT7At(t7c); extra.kSeen = F2.FB2.kSeen; extra.states = F2.FB2.hyps.length;
      if (truth) { const [ts, tn, p1, p2] = truth.split(':'); const hit = F2.FB2.hyps.filter(h => h.s === (parseInt(ts, 16) >>> 0) && h.nc === +tn); extra.truth = { stateKept: hit.length > 0, withPhases: hit.some(h => h.ph[0] === +p1 && h.ph[1] === +p2) }; }
      extra.t7left = F2.FB2.t7 ? F2.prune(t7c || Math.floor(F2.pic(performance.now()))) : null; extra.taps = F2.FB2.taps.map(x => +x.toFixed(1)); extra.vis = F2.FB2.vis.map(w => w.map(x => +x.toFixed(1))); }
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), C = T.CHG, F = window.__fb2 || {};
    return { state: C.state, why: C.why, info: C.info, late: late.length, onFrameMs: { mean: +(prof.sum / prof.n).toFixed(2), max: Math.round(prof.max), over12: prof.slow, by: prof.by }, fps: document.getElementById('r-fps') && document.getElementById('r-fps').textContent,
      trigger: ev('chargeTrigger'), early: ev('chargeEarly'), lock: ev('chargeLock'), nolock: ev('chargeNoLock'), errors: ev('chargeError'),
      fb2Lock: ev('fb2Lock'), planK: ev('fb2PlanK'), kSeen: ev('fb2K'), planT7: ev('fb2PlanT7'), trigT: C.trig && C.trig.t, t0,
      extra, fb2: document.getElementById('fb2-status').innerText, chg: document.getElementById('chg-status').innerText };
  }, { base, dir, nf, t5, kAt: +(process.env.KAT || 0), t7c: +(process.env.T7C || 0), wait: +(process.env.WAIT || 0), truth: process.env.TRUTH || '' });
  out.pageErrors = errs.slice(0, 5); console.log(JSON.stringify(out));
  await b.close();
})();
