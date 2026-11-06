/* Pressing early on purpose: a confirm on a working frame well before the beeps must be checked (green, carried as the
 * real press) and must not count toward the beep calibration. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  // v73: these turns are the old Jr. Troopa route (a shine lock carried by the target screens); the Charge lock is the default
  await p.addInitScript(() => { try { const s = JSON.parse(localStorage.getItem('tot-settings') || '{}'); s.jrroute = 'shine'; localStorage.setItem('tot-settings', JSON.stringify(s)); } catch (e) {} });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    localStorage.setItem('tot-presses', '[]');
    const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
    const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
    const G = { S: { s: 0x77777777, nc: 5, inst: [] }, g: 0, ev: [], shines: [] }, T0 = performance.now() + 1000;
    const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
    const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
    run(1500); setNow(1500); for (const g of G.shines) T.addShine(T0 + (g + 6) * FR + vlag, true);
    await wait(() => T.st.lock);
    T.setStep(T.RT().findIndex(s => s.turn === 'jr_bomb_cc')); setNow(1520); T.makePlan(); const P = T.st.plan;
    // earliest working frame at least 30 frames before the planned one
    let k = Math.ceil((performance.now() - P.tLast) / FR) + 5; while (!(R.works(P.seedBL, 0, k, 0, R.PROFILES.jrcc_bomb) && k < P.target - 30)) k++;
    const g = Math.round((P.tLast - T0) / FR) + k; G.ev.push({ f: g, id: 'jr_bomb_cc' }); run(g + 179); const roll = R.randInt(G.S.s, 100)[1];
    setNow(g + 4); T.checkPress(T0 + (g + 2 + pfix) * FR + vlag);
    const m = T.st.lastPress;
    return { framesBeforeBeeps: P.target - k, measuredWorks: m && m.works, onBeeps: m && m.onBeeps, calibrationPresses: JSON.parse(localStorage.getItem('tot-presses')).length,
      carried: T.st.turnEv.map(e => e.id), gameRoll: roll, closeCallInGame: roll < 30, msg: document.getElementById('press-msg').textContent.slice(0, 70) };
  });
  console.log(JSON.stringify(out, null, 1)); console.log('errors', errs); await b.close();
})();
