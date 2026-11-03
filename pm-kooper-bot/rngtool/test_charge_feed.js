/* The Hallway Charge lock on real route clips, through the page in headless Chromium, fed frame by frame instead of
 * playing the clip in a <video> (live playback in headless Chromium here dropped many frames, so test_charge_clips.js
 * became unreliable). Each capture frame (JPEG) goes to the page's per-frame entry (onFrame with the frame as V.src,
 * the page's background-capture path) at its real time, start + i / 60 s, so the search and the carry run against the
 * clock as live; a frame more than 25 ms late is dropped, as a busy browser drops pictures. Same checks and output as
 * test_charge_clips.js: lock, time to lock after the rays end, seed, q, the Spiny Flip confirm, the states left, the Time
 * Out confirm (bar hiding - 3 frames), the share of states for which Time Out works there (-1/0/+1) and the frame the
 * page would beep (lead 1.5 s, window 1 s).
 * usage: [STEP=t2] node test_charge_feed.js URLBASE DIR NFRAMES   (STEP=t2: start on Hallway T2 instead of T1)   (URLBASE/tot.html, URLBASE/DIR/f%05d.jpg; serve on 127.0.0.1)
 *   frames: ffmpeg -i CLIP.mkv -q:v 3 -start_number 0 DIR/f%05d.jpg */
const { chromium } = require('playwright');
(async () => {
  const [base, dir, nf] = [process.argv[2], process.argv[3], +process.argv[4]];
  const b = await chromium.launch();
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
  });
  await p.goto(base + '/tot.html');
  // STEP=t2: the page sits on Hallway T2 (as the runner after a retry); the burst must set it back to T1 and lock
  await p.evaluate(st2 => { const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'); T.setStep(st2 ? hi + 1 : hi); document.getElementById('s-lead').value = '1.5'; }, process.env.STEP === 't2');
  const res = await p.evaluate(async ({ base, dir, nf }) => {
    const T = window.__tot, live = {};
    const watch = () => {     // test_charge_clips.js: as soon as the bar hides for Time Out
      if (live.done || !(T.zw.on && T.zw.src === 'charge')) return;
      const S = T.SLOG, sp = S.find(x => x.ev === 'chargeSpinyHeld') || S.find(x => x.ev === 'hudConfirm' && x.id === 'hw_spiny'); if (!sp || !S.find(x => x.ev === 'zwInput')) return;
      const h = S.find(x => x.ev === 'barHide' && x.at > sp.at + 3000); if (!h) return;
      live.done = true; const c = Math.round(T.zwF(h.at, 0)) - 3; live.toConfirm = c; live.toHideAfterRaysS = +((h.at - T.CHG.tEnd) / 1000).toFixed(1);
      live.plan = T.chgPlanAt(c - 1, 1.5, 1); if (live.plan.target != null) live.beepRel = live.plan.target - c;
      live.worksAt = [-1, 0, 1].map(d => { const r = T.chgEvalAt(c + d); return r.p == null ? null : +r.p.toFixed(2); });
      live.states = T.zw.parts.length; live.dead = T.zw.dead;
    };
    const url = i => base + '/' + dir + '/f' + String(i).padStart(5, '0') + '.jpg';
    const bmp = new Map(); let next = 0;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(url(k)).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    want(0); for (let i = 0; i < 60; i++) await bmp.get(i);
    const t0 = performance.now() + 300; let late = 0;
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25) { late++; im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      T.V.src = vf; try { T.onFrame(tf); } finally { T.V.src = null; vf.close(); }
      watch();
    }
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), C = T.CHG, I = C.info || {};
    const out = { state: C.state, why: C.why, info: Object.assign({}, I, { gaps: undefined }), qs: C.qs, late, shines: +document.getElementById('r-shines').textContent };
    out.spiny = ev('zwInput').map(x => x.c); out.trigger = ev('chargeTrigger'); out.stepSet = ev('chargeStepSet'); out.notSeen = ev('chargeNotSeen');
    Object.assign(out, live); out.zwDead = T.zw.dead; return out;
  }, { base, dir, nf });
  res.errors = errs.slice(0, 5); console.log(dir, JSON.stringify(res));
  await b.close();
})();
