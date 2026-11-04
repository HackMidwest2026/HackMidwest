/* The Hallway Charge lock on real route clips, through the page in headless Chromium, fed frame by frame instead of
 * playing the clip in a <video> (live playback in headless Chromium here dropped many frames, so test_charge_clips.js
 * became unreliable). Each capture frame (JPEG) goes to the page's per-frame entry (onFrame with the frame as V.src,
 * the page's background-capture path) at its real time, start + i / 60 s, so the search and the carry run against the
 * clock as live; a frame more than 25 ms late is dropped, as a busy browser drops pictures. Same checks and output as
 * test_charge_clips.js: lock, time to lock after the rays end, seed, q, the Spiny Flip confirm, the states left, the Time
 * Out confirm (bar hiding - 3 frames), the share of states for which Time Out works there (-1/0/+1) and the frame the
 * page would beep (lead 1.5 s, window 1 s).
 * usage: [STEP=t2|fb2] [REF=i [BUSY=1]] node test_charge_feed.js URLBASE DIR NFRAMES   (URLBASE/tot.html, URLBASE/DIR/f%05d.jpg; serve on 127.0.0.1)
 *   STEP=t2: start on Hallway T2 instead of T1; STEP=fb2: start on the Final Bowser step (the arena check must take the
 *   Hallway profile and the burst must set the route to Hallway T1).
 *   REF=i: save Time Out's target screen (the クッパ name box) from capture frame i, so the page plans and beeps by itself
 *   (autoPlan) as live; BUSY=1: a shine seed search runs from the first shine after the Spiny Flip to the end (as live,
 *   where the turn-2 menu's shines started a chain search). Prints the plans made (out.plans).
 *   Diagnostics: DEBUG=1 (each game frame's picture time, out.place), GAPS=1 (the capture gaps), DUMP=1 (each picture's
 *   coin box and game-area brightness, out.dump), BAN0=[j*64+n,...] (tests only: assignments the first placement may not
 *   use, to force a wrong first placement and exercise the no-lock retry).
 *   frames: ffmpeg -i CLIP.mkv -q:v 3 -start_number 0 DIR/f%05d.jpg */
const { chromium } = require('playwright');
(async () => {
  const [base, dir, nf] = [process.argv[2], process.argv[3], +process.argv[4]];
  const b = await chromium.launch();
  const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.addInitScript(() => {
    localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
  });
  await p.goto(base + '/' + (process.env.PAGEFILE || 'tot.html'));
  if (process.env.REF) {      // Time Out's target screen saved from capture frame REF (the クッパ name box), as Save target screen does
    await p.evaluate(async ({ base, dir, i }) => {
      const im = await createImageBitmap(await (await fetch(base + '/' + dir + '/f' + String(i).padStart(5, '0') + '.jpg')).blob());
      const box = { x: 445 / 1280, y: 185 / 720, w: 120 / 1280, h: 55 / 720 }, c = document.createElement('canvas'); c.width = 24; c.height = 16;
      const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, box.x * im.width, box.y * im.height, box.w * im.width, box.h * im.height, 0, 0, 24, 16);
      const g = x.getImageData(0, 0, 24, 16).data, ref = []; for (let j = 0; j < g.length; j += 4) ref.push((g[j] + g[j + 1] + g[j + 2]) / 3);
      localStorage.setItem('tot-targets', JSON.stringify({ jr_B: { box, ref } }));
    }, { base, dir, i: +process.env.REF });
    await p.reload();
  }
  // STEP=t2: the page sits on Hallway T2 (as the runner after a retry); the burst must set it back to T1 and lock
  await p.evaluate(stp => { const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), fi = T.RT().findIndex(s => s.turn === 'fb2_pb');
    T.setStep(stp === 't2' ? hi + 1 : stp === 'fb2' ? fi : hi); document.getElementById('s-lead').value = '1.5'; }, process.env.STEP || '');
  if (process.env.BAN0) await p.evaluate(b => { window.__ban0s = b; }, process.env.BAN0);
  if (process.env.DEBUG || process.env.GAPS || process.env.DUMP || process.env.BAN0) await p.evaluate(([d, g]) => { window.__chgDebug = d; window.__gaps = g; window.__dump = !!d && d === 'dump'; if (window.__ban0s) window.__chgBan0 = JSON.parse(window.__ban0s); }, [process.env.DUMP ? 'dump' : !!process.env.DEBUG, process.env.GAPS || '']);
  const res = await p.evaluate(async ({ base, dir, nf, busy }) => {
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
    const dump = window.__dump ? { p: '', m: [], i: [], x: Object.assign(document.createElement('canvas'), { width: 32, height: 24 }).getContext('2d', { willReadFrequently: true }) } : null;
    for (let i = 0; i < nf; i++) {
      want(i); const im = await bmp.get(i); bmp.delete(i);
      const tf = t0 + i * 1000 / 60, w = tf - performance.now(); if (w > 1) await new Promise(r => setTimeout(r, w)); else if (w < -25) { late++; im.close(); continue; }
      const vf = new VideoFrame(im, { timestamp: Math.round(i * 1e6 / 60) }); im.close();
      T.V.src = vf; try { T.onFrame(tf);
        if (dump) { const g = T.chgGame(); dump.x.drawImage(vf, g.x * vf.displayWidth, g.y * vf.displayHeight, g.w * vf.displayWidth, g.h * vf.displayHeight, 0, 0, 32, 24);
          const d = dump.x.getImageData(0, 0, 32, 24).data; let m = 0; for (let j = 0; j < d.length; j += 4) m += 0.299 * d[j] + 0.587 * d[j + 1] + 0.114 * d[j + 2];
          dump.p += T.V.present ? '1' : '0'; dump.m.push(+(m / 768).toFixed(1)); dump.i.push(i); }
        } finally { T.V.src = null; vf.close(); }
      if (busy && !live.busyAt && T.SLOG.some(x => x.ev === 'zwInput') && T.SLOG.some(x => x.ev === 'shine' && x.t > T.SLOG.find(y => y.ev === 'zwInput').t)) { T.st.searching = true; T.st.searchKind = 'chain'; live.busyAt = Math.round(tf); }
      watch();
    }
    const S = T.SLOG, ev = n => S.filter(x => x.ev === n), C = T.CHG, I = C.info || {}, out0 = {};
    if (window.__chgDebug && C.dbg) out0.place = C.dbg.map((x, n) => (x ? n + ':' + x[0] : null)).filter(Boolean).join(' ');
    const out = { state: C.state, why: C.why, info: Object.assign({}, I, { gaps: window.__gaps ? I.gaps : undefined }), qs: C.qs, late, shines: +document.getElementById('r-shines').textContent };
    out.spiny = ev('zwInput').map(x => x.c); out.plans = ev('plan').map(x => ({ t: x.t, target: x.target, p: +(x.mix && x.mix.p || 0).toFixed(2), press: x.press })); out.busyAt = live.busyAt;
    Object.assign(out, out0); out.skips = C.skips; out.retries = ev('chargeRetry'); out.noLocks = ev('chargeNoLock').map(x => x.best); out.locks = ev('chargeLock').map(x => x.best); out.t0 = t0; out.trigT = C.trig ? C.trig.t : null; if (dump) out.dump = { p: dump.p, m: dump.m, i: dump.i }; out.arena = ev('chargeArena'); out.stepEnd = T.step(); out.hwDone = ev('hallwayDone').length; out.trigger = ev('chargeTrigger'); out.stepSet = ev('chargeStepSet'); out.notSeen = ev('chargeNotSeen');
    Object.assign(out, live); out.zwDead = T.zw.dead; return out;
  }, { base, dir, nf, busy: !!process.env.BUSY });
  res.errors = errs.slice(0, 5); console.log(dir, JSON.stringify(res));
  await b.close();
})();
