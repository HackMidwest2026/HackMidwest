/* Seed carried through Jr. Troopa turns on the page: lock from shines, then T3 Charge -> Bomb (planned) -> T4 Bomb ->
 * Maple Syrup (planned) -> T5 Charge -> Do Nothing (planned), with no shines after the lock (or, with SHINES=1, shines
 * in the menus that the page must accept). The game is simulated with the emulator-verified turn model; every planned
 * press is checked against the game's own Close Call roll. Fake clock: performance.now is shifted by window.__dt. */
const { chromium } = require('playwright');
const PAGE = 'file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto(PAGE);
  for (const seed0 of [0x2468ace1, 0x13579bdf, 0x0f1e2d3c]) {
    const out = await p.evaluate(async ([seed0, SHINES, RB, DBG]) => {
      const T = window.__tot, R = T.R, FR = R.FRAME_MS, num = id => +document.getElementById('s-' + id).value;
      document.getElementById('reset').click(); T.setStep(0); window.__dbg = DBG;
      const vlag = num('vlag'), pfix = num('pfix'), wait = async c => { for (let i = 0; i < 600 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      // the game
      const G = { S: { s: seed0 >>> 0, nc: 5, inst: [] }, g: 0, ev: [], shines: [] };
      const T0 = performance.now() + 1000;
      const run = to => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const r = R.frameEv(G.S, G.g, ev); if (r) G.shines.push(G.g); } };
      const rollAt = (to) => { run(to); const ev = R.buildEv(G.ev), e = ev.get(to); return R.randInt(G.S.s, 100)[1]; };   // the roll is the frame's first draw
      const setNow = g => { window.__dt += T0 + g * FR - performance.now(); };
      const tShine = g => T0 + (g + 6) * FR + vlag;
      const log = [];
      // 1) lock from ~50 s of shines
      run(1500); setNow(1500); for (const g of G.shines) T.addShine(tShine(g), true);
      await wait(() => T.st.lock); if (!T.st.lock) return { error: 'no lock' };
      const lockedShines = G.shines.length;
      const stepOf = id => T.RT().findIndex(s => s.turn === id);
      async function planned(turnId, prof, preId, preCat, gPre, gPlan, rollOff, vanishPre, vanish) {
        T.setStep(stepOf(turnId));
        // the turn's other input first (its target screen closes `vanishPre` frames after the confirm)
        G.ev.push({ f: gPre, id: preId }); run(gPre + 2); setNow(gPre + 3);
        T.preConfirm({ cat: preCat, id: preId }, T0 + (gPre + vanishPre + pfix + RB) * FR + vlag);
        run(gPlan);
        if (SHINES) { const from = G.shines.length; for (const g of G.shines.slice(from)) T.addShine(tShine(g), true); }
        setNow(gPlan); T.makePlan(); const P = T.st.plan; if (!P) return { step: turnId, error: 'no plan: ' + T.st.msg };
        const gT = T.st.clock && Math.round((P.tLast - T0) / FR) + P.target;      // the planned frame in game frames
        G.ev.push({ f: gT, id: turnId }); const roll = rollAt(gT + rollOff);
        setNow(gT + vanish + 3); T.checkPress(T0 + (gT + vanish + pfix + RB) * FR + vlag);
        return { step: turnId, carried: P.carried, window: P.w.length, roll, landed: roll < 30, carriedNow: T.st.turnEv.length };
      }
      // T2 (simulated, nothing planned): Bomb on Jr. Troopa's screen, then Whacka's Bump on Mario's
      T.setStep(T.RT().findIndex(s => s.turn === 'jr_whacka'));
      G.ev.push({ f: 1560, id: 'jr_bomb' }); run(1562); setNow(1563); T.preConfirm({ cat: 'K', id: 'jr_bomb' }, T0 + (1560 + 2 + pfix + RB) * FR + vlag);
      G.ev.push({ f: 1840, id: 'jr_whacka' }); run(1842); setNow(1843); T.checkPress(T0 + (1840 + 2 + pfix + RB) * FR + vlag);
      log.push({ afterT2: T.st.turnEv.map(e => e.id).join(',') });
      run(2100);
      if (SHINES) { const n0 = T.st.segs.length; for (const g of G.shines.filter(g => g > 1900)) T.addShine(tShine(g), true); log.push({ shinesAfterT2: 'segments ' + n0 + ' -> ' + T.st.segs.length + ', lock ' + !!T.st.lock }); }
      log.push(await planned('jr_bomb_cc', 'jrcc_bomb', 'jr_charge', 'M', 2250, 2500, 179, 2, 2));
      run(G.g + 300);
      if (SHINES) { const n0 = T.st.segs.length; for (const g of G.shines.filter(g => g > G.g - 250)) T.addShine(tShine(g), true); log.push({ shinesAfterT3: 'segments ' + n0 + ' -> ' + T.st.segs.length + ', lock ' + !!T.st.lock }); }
      log.push(await planned('jr_syrup_cc', 'jrcc_syrup', 'jr_bomb', 'K', G.g + 100, G.g + 350, 163, 2, 2));
      run(G.g + 300);
      log.push(await planned('jr_nothing_cc', 'jrcc_nothing', 'jr_charge', 'M', G.g + 100, G.g + 400, 26, 2, 3));
      return { lockedShines, log, segments: T.st.segs.length, note: document.getElementById('carry-note').textContent.slice(0, 90), dbg: window.__dbg ? T.SLOG.filter(x => /turn|read|hyp|replan|press/.test(x.ev)) : undefined };
    }, [seed0, +process.env.SHINES || 0, +process.env.READBIAS || 0, !!process.env.DBG]);   // READBIAS: the video reads every confirm this many frames off (a capture card)
    console.log(seed0.toString(16), JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
