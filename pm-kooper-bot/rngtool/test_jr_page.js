/* Jr. Troopa on the Charge-lock route through the page in headless Chromium, fed frame by frame (the way of
 * test_dup_page.js): emulator renders of the fight (jr_charge/jc_render.py, Glide64) through the capture simulation
 * (fb2_route/t6_capsim.py: S-Video, the route clips' OBS layout, 60 fps capture, a logic frame now and then with no
 * picture, x264), each capture frame handed to the page's own onFrame at its real time (frame i at start + i / 60 s; a
 * frame more than 25 ms late is dropped, as a busy browser drops pictures).
 * The page starts on the Jr. Troopa T1 step with the coin box on this layout and saves the target screens the route needs
 * (hand on Jr. Troopa, on Mario, Bombette's Strategies) from the capture frames SPEC names, as the runner saves each kind
 * once. It must: read the T1 Super Charge (profile jr), lock the seed and start the tracker; count the confirms from the
 * status bar (and Do Nothing from its screen) and move the route by itself; read each later Charge and check the carry;
 * read Mario's HP after each Close Call; and on each lever's target screen plan and beep (zwPlan, its own timing).
 * Prints JSON: the lock(s), the inputs it took (route index, frame), the plans (clock frame, chances, the time of the
 * press), the outcomes it read, the route step, and the session events; jr_charge/jc_e2e_page.py turns the plans into presses
 * in the emulator.
 * usage: [CRATE=33.367] node test_jr_page.js URLBASE DIR NFRAMES SPEC.json
 *   URLBASE/tot.html = the standalone page, URLBASE/DIR/f%05d.jpg = the capture frames (serve with
 *   python3 -m http.server --bind 127.0.0.1 8771); SPEC: {"targets": [[key, captureIndex, box], ...]} */
const { chromium } = require('playwright'), fs = require('fs');
(async () => {
  const [base, dir, nf, specF] = [process.argv[2], process.argv[3], +process.argv[4], process.argv[5]], SPEC = JSON.parse(fs.readFileSync(specF, 'utf8'));
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.clear();
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
  });
  await p.goto(base + '/tot.html');
  const out = await p.evaluate(async ({ base, dir, nf, SPEC, crate }) => {
    const T = window.__tot;
    document.getElementById('s-crate').value = crate;     // emulator renders run at 33.367 ms a frame
    T.setStep(T.jrStepFor(0));
    const url = i => base + '/' + dir + '/f' + String(i).padStart(5, '0') + '.jpg';
    const bmp = new Map(); let next = 0;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(url(k)).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    const saves = new Map(SPEC.targets.map(([key, ci, box]) => [ci, [key, box]]));
    want(0); await bmp.get(0); for (let i = 1; i < 60; i++) await bmp.get(i);
    const t0 = performance.now() + 300, late = [], steps = [];
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25 && !saves.has(i)) { late.push(i); im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      T.V.src = vf;
      try { if (saves.has(i)) { const [key, box] = saves.get(i); T.saveTarget(key, box); } T.onFrame(tf); } finally { T.V.src = null; vf.close(); }
      if (!steps.length || steps[steps.length - 1][1] !== T.step()) steps.push([i, T.step()]);
    }
    for (let k = 0; k < 100 && ['maps', 'search', 'capture'].includes(T.CHG.state); k++) await new Promise(r => setTimeout(r, 100));
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), cap = t => +((t - t0) * 60 / 1000).toFixed(1);   // a page time -> capture frame index
    const plans = ev('plan').map(x => Object.assign({ capPress: cap(x.tPress) }, x));
    return { t0, late: late.length, steps, step: T.step(), stepName: T.RT()[T.step()] && T.RT()[T.step()].t, JRT: { on: T.JRT.on, k: T.JRT.k, origin: T.JRT.origin, hist: T.JRT.hist.map(h => ({ k: h.k, at: h.at, cap: cap(h.at) })), lockK: T.JRT.lockK, dead: T.JRT.dead, out: T.JRT.out, hp10: T.JRT.hp10, cross: T.JRT.cross, inputs: T.JRT.inputs.map(x => ({ k: x.k, id: x.id, c: x.c, src: x.src, cap: cap(x.t) })) },
      zw: { on: T.zw.on, fight: T.zw.fight, parts: T.zw.parts && T.zw.parts.length, dead: T.zw.dead, taps: T.zw.taps && T.zw.taps.length, rate: T.zw.rate, t0cap: T.zw.t0 != null ? cap(T.zw.t0) : null },
      chg: { state: T.CHG.state, why: T.CHG.why, info: T.CHG.info, qs: T.CHG.qs },
      plans, locks: ev('chargeLock').map(x => ({ t: cap(x.t), best: x.best, qs: x.qs, lockAfterRaysMs: x.lockAfterRaysMs })), nolock: ev('chargeNoLock').map(x => ({ t: cap(x.t), best: x.best })),
      events: S.filter(x => /^(jr|chargeTrigger|chargeNotSeen|chargeArena|chargeFalseTrigger|zwStart|zwNoEdge|zwDoubt|beepsStopped|seedChanged|zwInconsistent|screenClosed|step$)/.test(x.ev)).map(x => Object.assign({}, x, { t: cap(x.t) })),
      panel: document.getElementById('chg-status').innerText, headline: document.getElementById('headline').textContent, detail: document.getElementById('detail').textContent };
  }, { base, dir, nf, SPEC, crate: process.env.CRATE || '33.367' });
  out.pageErrors = errs.slice(0, 5); console.log(JSON.stringify(out));
  await b.close();
})();
