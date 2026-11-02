/* Hallway Bowser T1 on the page: lock in T1's menu, Charge (seen on Mario's target screen), Spiny Flip (planned
 * nothing; its impact frame and the guard are hidden from the page), Bowser's attack, then T2's menu: the page must
 * narrow the candidates from a few shines and plan Time Out; the press is checked against the simulated game. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const cases = [[0x11111111, 150, 1], [0x22222222, 141, 1], [0x33333333, 163, 0], [0x44444444, 147, 1], [0x5a5a5a5b, 156, 0], [0x66666666, 152, 1]];
  for (const [seed0, imp, guard] of cases) {
    const out = await p.evaluate(async ([seed0, imp, guard]) => {
      const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
      document.getElementById('s-zwwin').value = '0';   // this test checks the shine-by-shine narrowing (best-guess mode off)
      document.getElementById('reset').click();
      const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      const G = { S: { s: seed0 >>> 0, nc: 5, inst: [] }, g: 0, ev: [], shines: [] }, T0 = performance.now() + 1000;
      const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
      const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
      run(1500); setNow(1500); for (const g of G.shines) T.addShine(T0 + (g + 6) * FR + vlag, true);
      await wait(() => T.st.lock); if (!T.st.lock) return { error: 'no lock' };
      const si = T.RT().findIndex(s => s.turn === 'hw_spiny'); T.setStep(si);
      G.ev.push({ f: 1560, id: 'hw_charge' }); run(1562); setNow(1563); T.preConfirm({ cat: 'M', id: 'hw_charge' }, T0 + (1560 + 2 + pfix) * FR + vlag);
      G.ev.push({ f: 1800, id: 'hw_spiny', imp, guard: !!guard }); run(1802); setNow(1803); T.checkPress(T0 + (1800 + 2 + pfix) * FR + vlag);
      const after = { step: T.RT()[T.step()].label, candidates: T.st.hyp && T.st.hyp.length };
      run(1800 + imp + 44 + 300);
      const branch = G.S.branch;
      // T2 menu: show shines one at a time until a plan is possible
      let used = 0, plan = null; const start = G.g;
      while (!plan && used < 12) {
        run(G.g + 30); const fresh = G.shines.filter(g => g >= start && g < G.g && g > (window.__lastFed || 0));
        for (const g of fresh) { window.__lastFed = g; T.addShine(T0 + (g + 6) * FR + vlag, true); used++; }
        setNow(G.g); T.st.msg = null; T.makePlan(); plan = T.st.plan;
      }
      window.__lastFed = 0;
      if (!plan) {
        const C = T.st.clock, lastF = C.frames[C.frames.length - 1];
        const det = T.st.hyp.map(h => { const ev = R.buildEv(T.st.turnEv.map(e => e.imps ? Object.assign({ imp: h >> 1, guard: !!(h & 1) }, e) : e)); const b = R.baseAfter(C.seed, ev, lastF);
          const S = { s: b.seed, nc: b.F, inst: [] }; const sh = []; for (let f = b.F; f < b.F + 3000; f++) { if (R.frameEv(S, f, null)) sh.push(f); } return { h, imp: h >> 1, guard: h & 1, branch: b.branch, F: b.F, seed: (b.seed >>> 0).toString(16), firstShines: sh.slice(0, 6).join(','), sh: sh.join() }; });
        const groups = {}; det.forEach(d => { (groups[d.sh] = groups[d.sh] || []).push(d.imp + (d.guard ? 'g' : '') + ':' + d.branch + '@' + d.F); });
        const gs = G.shines.filter(g => g >= start).slice(0, 14).join(','); const firsts = {}; det.forEach(d => firsts[d.sh.split(',').slice(0, 14).join(',')] = (firsts[d.sh.split(',').slice(0, 14).join(',')] || 0) + 1);
        return { used, game: gs, predicted: firsts };
      }
      const gT = Math.round((plan.tLast - T0) / FR) + plan.target;
      run(gT); const works = R.works(G.S.s, G.S.nc - gT, 0, 0, R.PROFILES.timeout);
      return { after, branch: branch + (guard ? ' (guarded)' : ''), impact: imp, shinesUsed: used, window: plan.w.length, carried: plan.carried, timeOutWorksInGame: works };
    }, [seed0, imp, guard]);
    console.log(seed0.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
