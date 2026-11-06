/* A plan far ahead (lead 10 s) must move to a sooner window of at least the same width (3+) that leaves 2.5 s for the
 * countdown; every frame of the new window must work. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  // v73: this plan is on the old Jr. Troopa route (a shine lock); the Charge lock is the default
  await p.addInitScript(() => { try { const s = JSON.parse(localStorage.getItem('tot-settings') || '{}'); s.jrroute = 'shine'; localStorage.setItem('tot-settings', JSON.stringify(s)); } catch (e) {} });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, F = R.FRAME_MS; const res = [];
    for (const seed of [0x13572468, 0x2468ace1, 0x0badf00d]) {
      document.getElementById('reset').click(); let s = seed, f = 0; const t0 = performance.now() - 60000;
      for (let n = 0; n < 24;) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) { T.addShine(t0 + (f + 6) * F, true); n++; } for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
      for (let i = 0; i < 600 && !T.st.lock; i++) await new Promise(r => setTimeout(r, 50));
      T.setStep(T.RT().findIndex(x => x.prof === 'jrcc_bomb'));
      document.getElementById('s-lead').value = 10; T.makePlan(); const P0 = { w: T.st.plan.w.length, inS: ((T.st.plan.tPress - performance.now()) / 1000).toFixed(1) };
      await new Promise(r => setTimeout(r, 600));
      const P = T.st.plan, works = [...Array(P.w.length).keys()].every(k => R.works(P.seedBL, 0, P.w.start + k, 0, R.PROFILES.jrcc_bomb));
      res.push({ first: P0, now: { w: P.w.length, inS: ((P.tPress - performance.now()) / 1000).toFixed(1), switched: P.switched || 0, allFramesWork: works } });
      document.getElementById('s-lead').value = 4;
    }
    return res;
  });
  out.forEach(o => console.log(JSON.stringify(o))); console.log('errors', errs); await b.close();
})();
