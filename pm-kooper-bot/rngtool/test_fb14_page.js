/* Final Bowser phase 2 T1-T4 (and the carry into T6) through the page in headless Chromium, fed frame by frame (the way
 * of test_fb2_page.js / test_dup_page.js): emulator renders (fb2_route/fb14_e2e.py: Glide64 screenshots of the route's
 * turns) through the capture simulation (fb2_route/t6_capsim.py: S-Video, the route clips' OBS layout, 60 fps capture, a
 * logic frame now and then with no picture, x264), each capture frame handed to the page's own onFrame at its real time
 * (frame i at start + i / 60 s; one more than 25 ms late is dropped, as a busy browser drops pictures).
 * The page starts on the Final Bowser T1 Charge step of the endgame route, with the coin box on this layout and the two
 * screens this fight needs saved from the capture itself (cat M: the マリオ name box of a target screen on Mario; cat S:
 * the Strategies panel with the hand on なにもしない), at the capture frames REFM and REFS.
 * MANIFEST.lateMs: drop a picture only when it is that late (default 25 ms, as a busy browser; the end-to-end runs on a
 * loaded machine use more, so that the turns are tested rather than the machine).
 * usage: [CRATE=33.367] [CPUS=n] node test_fb14_page.js URLBASE MANIFEST.json   (URLBASE/tot.html = the standalone page;
 *   MANIFEST = { frames: [url, ...], refM: i, refS: i, step: 'charge' } (urls relative to URLBASE); serve with
 *   python3 -m http.server --bind 127.0.0.1 PORT)
 * Prints JSON: the Charge triggers / locks / no-locks with their timing, the FB14 events (locks, carry checks, plans with
 * the beeped clock frame and chance, confirms, the Peach Beam, the T6 narrowed search), the FB2 events, the panels. */
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [base, man] = [process.argv[2], process.argv[3]], M = JSON.parse(fs.readFileSync(man, 'utf8'));
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.36, y: 0.265, w: 0.08, h: 0.06 } }));
  });
  await p.goto(base + '/tot.html');
  const out = await p.evaluate(async ({ dbg, base, M, crate, cpus, t5 }) => {
    const T = window.__tot, F = window.__fb14; if (dbg) { window.__fb14dbg = []; window.__chgDebug = true; if (M.truth) window.__fb14truth = M.truth; if (M.truthAura) window.__fb14truthAura = M.truthAura; if (M.truthT6) window.__fb14truthT6 = parseInt(M.truthT6, 16); } document.getElementById('s-crate').value = crate; if (cpus) document.getElementById('s-chgcpu').value = cpus;
    if (t5) document.getElementById('s-fb2t5').value = t5;
    const BOX = { M: { x: 0.36, y: 0.265, w: 0.08, h: 0.06 }, B: { x: 0.36, y: 0.265, w: 0.08, h: 0.06 }, S: { x: 0.33, y: 0.317, w: 0.176, h: 0.1 } };
    const bmp = new Map(); let next = 0; const nf = M.frames.length;
    const want = i => { while (next < Math.min(nf, i + 90)) { const k = next++; bmp.set(k, fetch(base + '/' + M.frames[k]).then(r => r.blob()).then(x => createImageBitmap(x))); } };
    // the two screens, saved from the capture (as the runner's Save target screen does)
    const refs = {};
    for (const [cat, i] of [['M', M.refM], ['S', M.refS], ['B', M.refB]]) { if (i == null) continue;
      const im = await fetch(base + '/' + M.frames[i]).then(r => r.blob()).then(x => createImageBitmap(x)), vf = new VideoFrame(im, { timestamp: 0 });
      T.V.src = vf; const g = F.sample(BOX[cat], 24, 16), ref = []; for (let k = 0; k < g.length; k += 4) ref.push((g[k] + g[k + 1] + g[k + 2]) / 3); T.V.src = null; vf.close(); im.close();
      refs[cat] = ref; }
    const tg = JSON.parse(localStorage.getItem('tot-targets') || '{}'); for (const c in refs) tg['jr_' + c] = { box: BOX[c], ref: refs[c] }; localStorage.setItem('tot-targets', JSON.stringify(tg));
    F.reloadTargets();
    T.setStep(T.RT().findIndex(s => s.fb14 === (M.turn || 1) && s.fb14role === (M.step || 'charge')));
    want(0); await bmp.get(0); for (let i = 1; i < Math.min(nf, 60); i++) await bmp.get(i);
    const lateMs = M.lateMs || 25, t0 = performance.now() + 300, late = [], beeps = [], trace = [], slow = [];
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -lateMs) { late.push(i); im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      const ta = performance.now(); T.V.src = vf; try { T.onFrame(tf); } finally { T.V.src = null; vf.close(); } const dt = performance.now() - ta; if (dt > 30) slow.push([i, Math.round(dt), T.CHG.state]);
      if (dbg) trace.push([i, +(T.V.score || 0).toFixed(3), T.V.present ? 1 : 0, T.step()]);
    }
    for (let k = 0; k < 100 && ['maps', 'search', 'capture'].includes(T.CHG.state); k++) await new Promise(r => setTimeout(r, 100));
    if (M.waitMs) await new Promise(r => setTimeout(r, M.waitMs));
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), C = T.CHG, cf = t => +((t - t0) * 60 / 1000).toFixed(1);   // capture frame of a page time
    const fbe = S.filter(x => /^fb14|^fb2|^charge(Lock|NoLock|Trigger|Narrow|NotSeen|Retry|Error|Arena)|^step$|^beepsStopped|^screenClosed/.test(x.ev));
    const plans = ev('fb14Plan').map(x => Object.assign({}, x, { tPressCap: x.tPress != null ? cf(x.tPress) : null }));
    return { lateIdx: late.slice(0, 80), slow: slow.slice(0, 40), t0, clockT0: F.FB14.t0, clockT0Cap: F.FB14.t0 != null ? cf(F.FB14.t0) : null, rate: F.FB14.rate, late: late.length, state: C.state, info: C.info, events: fbe, plans,
      fb14: { on: F.FB14.on, states: F.FB14.states.length, M: F.FB14.M, P: F.FB14.P, pb: F.FB14.pb, t6: F.FB14.t6 && { at: F.FB14.t6.at, bases: F.FB14.t6.bases.length }, taps: F.FB14.t0 != null ? F.FB14.taps.map(t => +(F.pic(t) - 4.8).toFixed(1)) : [], vis: F.FB14.t0 != null ? F.FB14.vis.map(v => [+(F.pic(v[0]) + 30).toFixed(1), +(F.pic(v[1]) - 4).toFixed(1)]) : [] },
      fb2: window.__fb2 && { on: window.__fb2.FB2.on, plan: window.__fb2.FB2.plan, kSeen: window.__fb2.FB2.kSeen },
      place: dbg && T.CHG.G0 ? T.CHG.G0 : undefined, pics: dbg ? T.CHG.J0 : undefined, trace: dbg ? trace : undefined, lockStates: dbg ? window.__fb14dbg : undefined, states: dbg ? F.FB14.states.slice(0, 400).map(S => ({ s: S.s >>> 0, nc: S.nc, f: S.f, l: S.l, w: +(S.w * S.lw).toExponential(2), err: S.err, c: Array.from(S.c).join(''), ph: S.ph, sh: S.sh, out: S.out })) : undefined, step: T.step(), panels: { chg: document.getElementById('chg-status').innerText, fb14: document.getElementById('fb14-status').innerText, fb2: document.getElementById('fb2-status').innerText } };
  }, { dbg: !!process.env.DBG, base, M, crate: process.env.CRATE || '33.367', cpus: process.env.CPUS || '', t5: process.env.T5 || '' });
  out.pageErrors = errs.slice(0, 5); console.log(JSON.stringify(out));
  await b.close();
})();
