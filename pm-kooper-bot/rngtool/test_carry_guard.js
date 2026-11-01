/* Carrying the seed: if a turn's earlier input (here T4's Bomb) was not seen, the next plan must not be made from the
 * carried prediction. Then: a press that misses the Close Call stops the carry until shines find the seed again. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
    const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
    const G = { S: { s: 0x5eed5eed, nc: 5, inst: [] }, g: 0, ev: [], shines: [] }, T0 = performance.now() + 1000;
    const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
    const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
    run(1500); setNow(1500); for (const g of G.shines) T.addShine(T0 + (g + 6) * FR + vlag, true);
    await wait(() => T.st.lock);
    // an input the page cannot simulate (T1's Bomb + Jr. Troopa's T1 turn) after the lock blocks planning
    const s1 = T.RT().findIndex(s => s.label === 'Bomb'); T.setStep(s1); run(1560); setNow(1560); T.checkPress(T0 + (1555 + 2 + pfix) * FR + vlag);
    T.setStep(T.RT().findIndex(s => s.turn === 'jr_bomb_cc')); T.st.msg = null; T.makePlan();
    const blocked = { plan: !!T.st.plan, msg: (T.st.msg || '').slice(0, 70) };
    T.st.inputs = []; T.st.msg = null;   // (continue the rest of the test as before)
    window.__blocked = blocked;
    G.ev.push({ f: 1650, id: 'jr_charge' }); run(1652); setNow(1653); T.V.preDone = { [T.step() + ':0']: true }; T.preConfirm({ cat: 'M', id: 'jr_charge' }, T0 + (1652 + pfix) * FR + vlag);
    run(1900); setNow(1900); T.makePlan(); let P = T.st.plan; const gT = Math.round((P.tLast - T0) / FR) + P.target;
    G.ev.push({ f: gT, id: 'jr_bomb_cc' }); run(gT + 5); setNow(gT + 5); T.checkPress(T0 + (gT + 2 + pfix) * FR + vlag);
    const r = { unmodeledT1: window.__blocked };
    // T4: the Bomb happens in the game but its screen is not seen
    G.ev.push({ f: gT + 400, id: 'jr_bomb' }); run(gT + 700); setNow(gT + 700); T.st.plan = null; T.makePlan();
    r.unseenBomb = { plan: !!T.st.plan, msg: (T.st.msg || '').slice(0, 60) };
    // now it was seen, but the press lands on a failing frame after the window -> carry stops
    T.V.preDone[T.step() + ':0'] = true; T.preConfirm({ cat: 'K', id: 'jr_bomb' }, T0 + (gT + 402 + pfix) * FR + vlag); T.st.msg = null; T.makePlan(); P = T.st.plan;
    let k = P.w.end + 1; while (R.works(P.seedBL, 0, k, 0, R.PROFILES.jrcc_syrup)) k++;
    const g4 = Math.round((P.tLast - T0) / FR) + k; r.missFrame = k - P.target;
    T.checkPress(T0 + (g4 + 2 + pfix) * FR + vlag);
    r.afterMiss = { needResync: T.st.needResync, carried: T.st.turnEv.length, note: document.getElementById('carry-note').textContent.slice(0, 60) };
    T.st.plan = null; T.makePlan(); r.planAfterMiss = { plan: !!T.st.plan, msg: (T.st.msg || '').slice(0, 60) };
    return r;
  });
  console.log(JSON.stringify(out, null, 1)); console.log('errors', errs); await b.close();
})();
