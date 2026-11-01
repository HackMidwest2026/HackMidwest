/* The countdown must survive new coin shines: lock, plan, keep detecting shines (same RNG path) until the press.
 * Then a contradicting path must drop the plan. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const r = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, F = 33.43; let s = 0x2468ace0, f = 0; const sh = [];
    while (sh.length < 60) { s = R.adv(s); const x = s >= R.SHINE_MIN; if (x) sh.push(f); for (let i = 0; i < (x ? 48 : 24); i++) s = R.adv(s); f += x ? 48 : 24; }
    const t0 = performance.now() - sh[19] * F - 10 * F;
    for (let i = 0; i < 20; i++) T.addShine(t0 + sh[i] * F + 6 * F + (Math.random() - 0.5) * 20, true);
    while (!T.st.lock) await new Promise(r => setTimeout(r, 100));
    T.makePlan(); const plan = T.st.plan, tPress = plan.tPress; let next = 20, added = 0;
    while (performance.now() < tPress) {
      const now = performance.now();
      while (next < sh.length && t0 + sh[next] * F + 6 * F <= now) { T.addShine(t0 + sh[next] * F + 6 * F + (Math.random() - 0.5) * 20, true); next++; added++; }
      await new Promise(r => setTimeout(r, 30));
    }
    const kept = T.st.plan === plan && T.st.plan.tPress === tPress;
    // contradicting path: a shine that does not fit -> new segment -> lock elsewhere must drop a fresh plan
    T.makePlan(); const p2 = T.st.plan;
    let s2 = 0x13572468, g = 0; const o = []; while (o.length < 30) { s2 = R.adv(s2); const x = s2 >= R.SHINE_MIN; if (x) o.push(g); for (let i = 0; i < (x ? 48 : 24); i++) s2 = R.adv(s2); g += x ? 48 : 24; }
    const base = performance.now() + 2000;
    for (const x of o) { T.addShine(base + x * F, true); while (T.st.searching) await new Promise(r => setTimeout(r, 100)); }
    return { shinesDuringCountdown: added, planKept: kept, secondPlanDroppedOnOtherPath: T.st.plan !== p2 };
  });
  console.log(JSON.stringify(r), 'errors', errs); await b.close();
})();
