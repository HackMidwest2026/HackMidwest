/* Duplighosts T1 on the Charge-lock route through the page in headless Chromium, fed frame by frame (the way of
 * test_fb2_page.js): emulator renders of the T1 menu, Mario's Super Charge and the rays (jr_charge/jc_probe.py with
 * Glide64 screenshots, battle 0x2402) through the capture simulation (fb2_route/t6_capsim.py: S-Video, the route clips'
 * OBS layout, 60 fps capture, a logic frame now and then with no picture, x264), each capture frame handed to the page's
 * own onFrame at its real time (frame i at start + i / 60 s; a frame more than 25 ms late is dropped, as a busy browser
 * drops pictures).
 * The page starts on the Duplighost step of the Charge-lock route with the coin box on this layout. It must arm on the
 * menu's bar hide (the arena check must say Duplighosts, not the Hallway), trigger on the burst with the dup profile,
 * lock the seed, and start the tracker; then the Do Nothing plan as if Bombette's Strategies screen showed on clock frame
 * CSCR (lead 1.5 s, 1 s max extra wait, best chance). Prints JSON: trigger, lock, arena events, the plan (target clock
 * frame, 3+ and 4 chances) and the predicted copies on target -1 / 0 / +1 for the lag-0 state; dup_charge/dc_e2e_press.py
 * then plays that frame in the emulator.
 * usage: node test_dup_page.js URLBASE DIR NFRAMES [CSCR=203]   (URLBASE/tot.html = the standalone page,
 *        URLBASE/DIR/f%05d.jpg = the capture frames; serve with python3 -m http.server --bind 127.0.0.1) */
const { chromium } = require('playwright');
(async () => {
  const [base, dir, nf] = [process.argv[2], process.argv[3], +process.argv[4]], cScr = +(process.argv[5] || 203);
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
  });
  await p.goto(base + '/tot.html');
  const out = await p.evaluate(async ({ base, dir, nf, cScr }) => {
    const T = window.__tot, sel = document.getElementById('s-duproute'); sel.value = 'charge'; sel.dispatchEvent(new Event('change'));
    T.setStep(T.RT().findIndex(s => s.chg === 'dup'));
    const url = i => base + '/' + dir + '/f' + String(i).padStart(5, '0') + '.jpg';
    const bmp = new Map(); let next = 0;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(url(k)).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    want(0); await bmp.get(0); for (let i = 1; i < 60; i++) await bmp.get(i);
    const t0 = performance.now() + 300, late = [];
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25) { late.push(i); im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      T.V.src = vf; try { T.onFrame(tf); } finally { T.V.src = null; vf.close(); }
    }
    for (let k = 0; k < 150 && ['maps', 'search', 'capture', 'armed'].includes(T.CHG.state); k++) await new Promise(r => setTimeout(r, 100));
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), C = T.CHG, res = { state: C.state, why: C.why, info: C.info, qs: C.qs, qsRays: C.qsRays, menu: C.menu && { from: Math.round(C.menu.from - C.trig.t), to: Math.round(C.menu.to - C.trig.t), taps: C.menu.taps.map(x => Math.round(x - C.trig.t)) }, taps: T.zw.taps && T.zw.taps.map(x => +x.toFixed(1)), dead: T.zw.deadAt, prof: C.prof && C.prof.id, late: late.length, zwOn: T.zw.on, fight: T.zw.fight,
      trigger: ev('chargeTrigger'), arena: ev('chargeArena'), lock: ev('chargeLock'), nolock: ev('chargeNoLock'), notseen: ev('chargeNotSeen'), retry: ev('chargeRetry'), zwStart: ev('zwStart'), errors: ev('chargeError'),
      panel: document.getElementById('chg-status').innerText };
    if (T.zw.on && T.zw.fight === 'dup') {
      const st0 = T.dupStatesAt(Math.min(cScr - 10, 150)).sort((x, y) => y.w - x.w), pl = T.dupPlanAt(cScr, 1.5, 1);
      res.plan = { target: pl.target, p3: pl.p3, p4: pl.p4, w: pl.w, none: pl.none, from: pl.from, states: pl.states.length };
      if (pl.target != null) res.predicted = st0.map(q => ({ w: +q.w.toFixed(3), cls: T.dupClasses(q.s, q.nc, q.g, pl.target - 1, pl.target + 1).join('') }));
    }
    return res;
  }, { base, dir, nf, cScr });
  out.pageErrors = errs.slice(0, 5); console.log(JSON.stringify(out));
  await b.close();
})();
