/* Re-locking in a torch room: lock seed A, an enemy room (coin hidden, extra draws), then the Duplighost/Heart Block
 * room with the coin showing (12 draws every 50 frames after the coin, phase unknown to the page). The page must re-lock
 * there on A's trajectory, keep accepting the room's shines, then (after a battle-like gap) re-find from that lock. */
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  for (const [seed, ph] of [[0x2b2b2b2b, 7], [0x5eedf00d, 31], [0x1234abcd, 44]]) {
    const out = await p.evaluate(async ([seed, ph]) => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS, vlag = +document.getElementById('s-vlag').value;
      document.getElementById('reset').click();
      const wait = async c => { for (let i = 0; i < 900 && !c(); i++) await new Promise(r => setTimeout(r, 50)); };
      // the game: clean 0-1500, enemies 1500-2100, torch room 2300-3800 (torches every 50 frames from phase ph), battle gap 3800-4400 (+3000 draws), clean after
      const ev = new Map(); for (let f = 2300; f < 3800; f++) if ((f - ph) % 50 === 0) ev.set(f, { pre: [], post: Array(12).fill(359), eio: [] });
      const S = { s: seed >>> 0, nc: 5, inst: [] }, sh = [], drawSeed = {};
      for (let f = 0; f < 6500; f++) {
        if (f >= 1500 && f < 2100 && f % 37 === 0) for (let k = 0; k < 3; k++) S.s = R.randInt(S.s, 30)[0];
        if (f === 4000) for (let k = 0; k < 3000; k++) S.s = R.adv(S.s);
        if (f === S.nc) drawSeed[f] = S.s >>> 0;
        if (R.frameEv(S, f, ev)) sh.push(f);
      }
      const tap = f => 1e5 + (f + 6) * F + vlag, log = {};
      for (const f of sh.filter(f => f < 1450)) T.addShine(tap(f), true);
      await wait(() => T.st.lock); T.coinBack();
      let n = 0;
      for (const f of sh.filter(f => f >= 2350 && f < 3800)) { T.addShine(tap(f), true); n++; await wait(() => !T.st.searching); if (T.st.lock && !log.torchLock) log.torchLock = { afterShines: n, onTrue: T.st.lock.seed >>> 0 === drawSeed[T.st.segs[T.st.lock.seg].taps.length && Math.round((T.st.segs[T.st.lock.seg].taps[0] - 1e5 - vlag) / F - 6)], phases: T.st.lock.torch && T.st.lock.torch.length }; }
      log.endOfRoom = { locked: !!T.st.lock, torch: !!(T.st.lock && T.st.lock.torch), segs: T.st.segs.length };
      T.coinBack();
      let m = 0;
      for (const f of sh.filter(f => f >= 4500)) { T.addShine(tap(f), true); m++; await wait(() => !T.st.searching); if (T.st.lock) break; }
      const L = T.st.lock, f1 = L && Math.round((T.st.segs[L.seg].taps[0] - 1e5 - vlag) / F - 6);
      log.afterBattle = { relocked: !!L, shines: m, onTrue: !!L && L.seed >>> 0 === drawSeed[f1] };
      return log;
    }, [seed, ph]);
    console.log(seed.toString(16), 'phase', ph, JSON.stringify(out));
  }
  console.log('errors', errs); await b.close();
})();
