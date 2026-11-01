/* Shines from a stretch where something else draws random numbers (enemies, level-up confetti) must not cost the lock:
 * lock seed A, then the coin is shown in a "dirty" room (3 extra draws every 37 frames) for 15 shines, then hidden and
 * shown again in a clean room. The page must ignore the dirty shines, keep A, and find its place on A afterwards. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const out = await p.evaluate(async () => {
    const T = window.__tot, R = T.R, F = R.FRAME_MS, vlag = +document.getElementById('s-vlag').value;
    const wait = async c => { for (let i = 0; i < 900 && !c(); i++) await new Promise(r => setTimeout(r, 100)); };
    // the game: clean, then dirty (frames 1500..2400), then clean again
    const S = { s: 0x31415926, nc: 5, inst: [] }, sh = [];
    for (let f = 0; f < 4200; f++) {
      if (f >= 1500 && f < 2400 && f % 37 === 0) for (let k = 0; k < 3; k++) S.s = R.randInt(S.s, 30)[0];
      const r = R.frameEv(S, f, null); if (r) sh.push(f);
    }
    const t0 = 1e5, tap = f => t0 + (f + 6) * F + vlag;
    for (const f of sh.filter(f => f < 1450)) T.addShine(tap(f), true);
    await wait(() => T.st.lock); const seedA = T.st.lock && T.st.lock.seed;
    T.coinBack();                                      // coin hidden, then shown in the dirty room
    const dirty = sh.filter(f => f >= 1520 && f < 2400);
    for (const f of dirty) { T.addShine(tap(f), true); await wait(() => !T.st.searching); }
    const mid = { prevLockKept: !!T.st.prevLock, segs: T.st.segs.length, note: T.st.note };
    T.coinBack();                                      // hidden again, shown in a clean room
    for (const f of sh.filter(f => f >= 2600 && f < 4200)) { T.addShine(tap(f), true); await wait(() => !T.st.searching); if (T.st.lock) break; }
    // is the new lock on A's trajectory?
    let x = seedA, onA = false; const want = T.st.lock && T.st.lock.seed >>> 0;
    // replay the true game from the start and see if the locked seed appears as a pre-draw seed
    const S2 = { s: 0x31415926, nc: 5, inst: [] };
    for (let f = 0; f < 4200 && !onA; f++) { if (f >= 1500 && f < 2400 && f % 37 === 0) for (let k = 0; k < 3; k++) S2.s = R.randInt(S2.s, 30)[0]; if (f === S2.nc && S2.s >>> 0 === want) onA = true; R.frameEv(S2, f, null); }
    return { dirtyShines: dirty.length, mid, relocked: !!T.st.lock, onTrueTrajectory: onA, note: T.st.note };
  });
  console.log(JSON.stringify(out, null, 1)); console.log('errors', errs); await b.close();
})();
