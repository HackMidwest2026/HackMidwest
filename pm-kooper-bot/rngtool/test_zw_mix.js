/* Zero-wait best guess at Hallway T2 (zerowait/README.md): same setup as test_hw_carry.js (lock, Charge, Spiny Flip with a
 * hidden impact frame and guard, Bowser's attack), but no shines in T2's menu: the page must plan at once on the best
 * mix of the Spiny Flip outcomes (or say there is no edge), show the chance, and the game decides. Over many seeds the
 * shown chance should match how often Time Out works in the game (exact frame and +-1), and a forced 'no edge'
 * (threshold 0.99) must not beep. usage: node test_zw_mix.js [N] */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const N = +process.argv[2] || 24; let rs = 777; const rnd = () => ((rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296);
  const cases = []; for (let i = 0; i < N; i++) cases.push([(rnd() * 4294967296) >>> 0, 138 + Math.floor(rnd() * 33), rnd() < 0.6 ? 1 : 0, i === 0 ? 0.99 : 0.0]);
  const sum = { shown: 0, real: 0, n: 0, noEdge: 0, bad: 0 };
  for (const [seed0, imp, guard, edge] of cases) {
    const out = await p.evaluate(async ([seed0, imp, guard, edge]) => {
      const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
      document.getElementById('s-zwwin').value = '1'; document.getElementById('s-zwedge').value = String(edge); document.getElementById('s-lead').value = '4';   // the lead this test was written for (the page default is now 1.5 s)
      document.getElementById('reset').click();
      const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      const G = { S: { s: seed0 >>> 0, nc: 5, inst: [] }, g: 0, ev: [], shines: [] }, T0 = performance.now() + 1000;
      const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
      const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
      run(1500); setNow(1500); for (const g of G.shines) T.addShine(T0 + (g + 6) * FR + vlag, true);
      await wait(() => T.st.lock); if (!T.st.lock) return { error: 'no lock' };
      const si = T.RT().findIndex(s => s.turn === 'hw_spiny'); T.setStep(si);
      G.ev.push({ f: 1560, id: 'hw_charge' }); run(1562); setNow(1563); T.preConfirm({ cat: 'M', id: 'hw_charge' }, T0 + (1560 + 2 + pfix) * FR + vlag);
      G.ev.push({ f: 1800, id: 'hw_spiny', imp, guard: !!guard }); run(1802); setNow(1803); T.checkPress(T0 + (1800 + 2 + pfix) * FR + vlag); if (T.RT()[T.step()].turn === 'hw_throw') T.setStep(T.step() + 1);   // v78: the page leaves the throw step when the bar comes back in Bowser's turn (no aim popup here)
      const after = { step: T.RT()[T.step()].label, candidates: T.st.hyp && T.st.hyp.length };
      run(1800 + imp + 44 + 300);
      const branch = G.S.branch;
      // T2 menu: no shines shown; plan right away
      const used = 0; run(G.g + 30); setNow(G.g); T.st.msg = null; T.makePlan(); const plan = T.st.plan;
      if (!plan && edge > 0.5) return { noEdge: true, msg: T.st.msg && T.st.msg.slice(0, 60) };
      if (!plan) {
        const C = T.st.clock, lastF = C.frames[C.frames.length - 1];
        const det = T.st.hyp.map(h => { const ev = R.buildEv(T.st.turnEv.map(e => e.imps ? Object.assign({ imp: h >> 1, guard: !!(h & 1) }, e) : e)); const b = R.baseAfter(C.seed, ev, lastF);
          const S = { s: b.seed, nc: b.F, inst: [] }; const sh = []; for (let f = b.F; f < b.F + 3000; f++) { if (R.frameEv(S, f, null)) sh.push(f); } return { h, imp: h >> 1, guard: h & 1, branch: b.branch, F: b.F, seed: (b.seed >>> 0).toString(16), firstShines: sh.slice(0, 6).join(','), sh: sh.join() }; });
        const groups = {}; det.forEach(d => { (groups[d.sh] = groups[d.sh] || []).push(d.imp + (d.guard ? 'g' : '') + ':' + d.branch + '@' + d.F); });
        const gs = G.shines.filter(g => g >= start).slice(0, 14).join(','); const firsts = {}; det.forEach(d => firsts[d.sh.split(',').slice(0, 14).join(',')] = (firsts[d.sh.split(',').slice(0, 14).join(',')] || 0) + 1);
        return { used, game: gs, predicted: firsts };
      }
      const gT = Math.round((plan.tLast - T0) / FR) + plan.target;
      run(gT - 1); const S1 = { s: G.S.s, nc: G.S.nc }; const w = d => R.works(S1.s, S1.nc - (gT - 1), 1 + d, 0, R.PROFILES.timeout);
      const real = 0.25 * w(-1) + 0.5 * w(0) + 0.25 * w(1);
      return { after, branch: branch + (guard ? ' (guarded)' : ''), impact: imp, mix: plan.mix, real, exact: w(0) };
    }, [seed0, imp, guard, edge]);
    console.log(seed0.toString(16), JSON.stringify(out));
    if (edge > 0.5) { if (!out.noEdge) sum.bad++; else sum.noEdge++; continue; }
    if (out.mix) { sum.shown += out.mix.p; sum.real += out.real; sum.n++; } else if (!out.timeOutWorksInGame && out.window) { /* locked to one outcome: normal plan */ }
  }
  console.log('best-guess plans', sum.n, '| mean shown', (sum.shown / sum.n).toFixed(3), '| mean in game (press 25/50/25)', (sum.real / sum.n).toFixed(3), '| forced no-edge ok', sum.noEdge, 'bad', sum.bad);
  console.log(sum.bad ? 'FAIL' : 'PASS', 'errors', errs); await b.close();
})();
