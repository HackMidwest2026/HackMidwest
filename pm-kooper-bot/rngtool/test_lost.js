/* Recovery test: lock seed A from automatic detections, then the RNG jumps (savestate / reset) and the coin comes back
 * showing seed B's trajectory. The page must notice, search again by itself and lock B (no Reset press). */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, F = R.FRAME_MS, log = [];
    const shines = (seed, n) => { let s = seed, f = 0; const o = []; while (o.length < n) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) o.push({ f, before: o.length ? null : null }); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; } return o.map(x => x.f); };
    const wait = async cond => { for (let i = 0; i < 600 && !cond(); i++) await new Promise(r => setTimeout(r, 100)); };
    let t = 1e5;
    for (const f of shines(0x2468ace0, 20)) T.addShine(t + f * F + 7 * F, true);
    await wait(() => T.st.lock); log.push('A locked: ' + (T.st.lock && (T.st.lock.seed >>> 0).toString(16)));
    const seedA = T.st.lock && T.st.lock.seed;
    // savestate: coin hidden, then back on a different RNG trajectory
    T.newSegment(); t += 3e5;
    const B = shines(0x13572468, 30);
    for (const f of B) { T.addShine(t + f * F + 7 * F, true); if (T.st.searching) await wait(() => !T.st.searching); }
    await wait(() => T.st.lock && T.st.lock.seed !== seedA);
    const L = T.st.lock; let s = 0x13572468; const pre = new Set();
    for (let i = 0; i < 2000; i++) { const t2 = R.adv(s); if (t2 >= R.SHINE_MIN) pre.add(s >>> 0); s = R.adv(s); }
    log.push('after jump: lock ' + (L && (L.seed >>> 0).toString(16)) + ', segments ' + T.st.segs.length + ', headline: ' + document.getElementById('headline').textContent);
    // is the new lock on B's trajectory? (seed before some draw of B)
    let x = 0x13572468, onB = false; for (let i = 0; i < 4000 && L; i++) { if ((x >>> 0) === (L.seed >>> 0)) { onB = true; break; } x = R.adv(x); }
    log.push('new lock is on seed B\'s trajectory: ' + onB);
    return log;
  });
  console.log(out.join('\n')); console.log('errors', errs); await b.close();
})();
