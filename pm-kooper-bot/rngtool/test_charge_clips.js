/* The Charge lock on real route clips, through the page in headless Chromium, in real time. Each clip is played by a
 * <video> element and handed to the page as its window capture (captureStream), so the page sees the frames at the
 * clip's own pace, exactly as from OBS. The page starts on the Hallway Bowser T1 step with the coin box on this
 * capture's status-bar coin and no walk lock: the Charge rays are the only seed source.
 * Clips are never committed: convert them to VP9 WebM (Chromium here has no H.264) and serve the folder with the page:
 *   ffmpeg -i CLIP.mkv -an -c:v libvpx-vp9 -deadline realtime -cpu-used 8 -row-mt 1 -crf 8 -b:v 0 DIR/rN.webm
 *   cp .../timeout_timer_standalone.html DIR/tot.html; npx http-server DIR -p 8765 -s &
 * usage: node test_charge_clips.js URLBASE NAME[,NAME...]   e.g. http://127.0.0.1:8765 r1,r2
 * Per clip (JSON): lock or not, time to lock after the rays end, the seed and q, the Spiny Flip confirm the page read,
 * the RNG states left, the Time Out confirm (bar hiding - 3 frames, as Mario's actions), the share of states for which
 * Time Out works there (-1/0/+1), and the frame the page would beep if the runner had waited on the target screen
 * (lead 1.5 s, window 1 s). */
const { chromium } = require('playwright');
(async () => {
  const base = process.argv[2], names = process.argv[3].split(',');
  const b = await chromium.launch();
  for (const name of names) {
    const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.addInitScript(clip => {
      window.__chgDebug = /debug/.test(location.hash); window.__chgNoBg = /nobg/.test(location.hash);
      localStorage.setItem('tot-boxes', JSON.stringify({ coin: { x: 1080 / 1280, y: 40 / 720, w: 40 / 1280, h: 52 / 720 }, target: { x: 0.55, y: 0.12, w: 0.2, h: 0.08 } }));
      const v = document.createElement('video'); v.muted = true; v.src = clip; v.preload = 'auto'; window.__clipVideo = v;
      navigator.mediaDevices.getDisplayMedia = async () => { await new Promise(r => v.readyState >= 3 ? r() : v.addEventListener('canplaythrough', r, { once: true })); await v.play(); window.__clipStart = performance.now(); return v.captureStream(); };
    }, base + '/' + name + '.webm');
    await p.goto(base + '/tot.html#' + (process.env.DEBUG ? 'debug' : '') + (process.env.NOBG ? 'nobg' : ''));
    await p.evaluate(() => { const T = window.__tot; T.setStep(T.RT().findIndex(s => s.turn === 'hw_spiny')); document.getElementById('s-lead').value = '1.5'; });
    await p.click('#cam-start');
    const res = await p.evaluate(async (process_debug) => {
      const T = window.__tot, v = window.__clipVideo, live = {};
      // live, as soon as the bar hides for Time Out (the page reads it 8 frames later): the confirm frame, what the
      // tracker gives there, and what it would have beeped had the runner waited on the target screen
      const watch = setInterval(() => {
        if (live.done || !(T.zw.on && T.zw.src === 'charge')) return;
        const S = T.SLOG, sp = S.find(x => x.ev === 'chargeSpinyHeld') || S.find(x => x.ev === 'hudConfirm' && x.id === 'hw_spiny'); if (!sp || !S.find(x => x.ev === 'zwInput')) return;
        const h = S.find(x => x.ev === 'barHide' && x.at > sp.at + 3000); if (!h) return;
        live.done = true; const c = Math.round(T.zwF(h.at, 0)) - 3; live.toConfirm = c; live.toHideAfterRaysS = +((h.at - T.CHG.tEnd) / 1000).toFixed(1);
        const t0 = performance.now(); live.plan = T.chgPlanAt(c - 1, 1.5, 1); live.planMs = Math.round(performance.now() - t0);
        if (live.plan.target != null) live.beepRel = live.plan.target - c;
        live.worksAt = [-1, 0, 1].map(d => { const r = T.chgEvalAt(c + d); return r.p == null ? null : +r.p.toFixed(2); });
        live.states = T.zw.parts.length; live.dead = T.zw.dead;
      }, 30);
      await new Promise(r => { const iv = setInterval(() => { if (v.ended || v.currentTime > v.duration - 0.05) { clearInterval(iv); r(); } }, 200); });
      clearInterval(watch);
      const S = T.SLOG, ev = n => S.filter(x => x.ev === n);
      const C = T.CHG, I = C.info || {};
      const out = { state: C.state, why: C.why, info: I, qs: C.qs, qsRays: C.qsRays, menu: C.menu && { from: Math.round(T.zwF ? 0 : 0), n: C.menu.taps.length, ms: Math.round(C.menu.to - C.menu.from) }, fps: document.getElementById('r-fps').textContent, shines: +document.getElementById('r-shines').textContent };
      out.spiny = ev('zwInput').map(x => x.c); out.held = ev('chargeSpinyHeld').length; out.trigger = ev('chargeTrigger');
      Object.assign(out, live);
      out.zwDead = T.zw.dead; out.inconsistentAt = ev('zwInconsistent').map(x => x.at); if (process_debug) { out.taps = (T.zw.taps || []).map(x => +x.toFixed(1)); out.vis = (T.zw.vis || []).map(w => w.map(x => +x.toFixed(1))); out.visFrom = T.zw.visFrom; out.dbg = C.dbg; out.dbgRaw = C.dbgRaw; } out.lockAt = C.tLock && window.__clipStart ? +((C.tLock - window.__clipStart) / 1000).toFixed(1) : null;
      return out;
    }, !!process.env.DEBUG);
    res.errors = errs.slice(0, 5); console.log(name, JSON.stringify(res));
    await p.close();
  }
  await b.close();
})();
