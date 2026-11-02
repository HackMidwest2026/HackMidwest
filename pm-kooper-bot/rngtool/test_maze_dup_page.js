/* Maze rooms -> kpa_102 (C-up closed ~9 s, enemies draw extra numbers) -> Duplighost room. Short looks (status bar up
 * 220 frames, re-opened 25 frames later, shines count after 1 s steady), console load lag 0-6 frames on room loads.
 * Measures seconds of looking in the Duplighost room until the page locks: carried from the maze (near-lock candidates
 * through the enemy room), versus starting fresh at the Duplighost room. TORCH=1: the Duplighost room's torches draw
 * (12 every 50 frames, random phase). In the Duplighost room the coin stays up (Mario stands still; DUPLOOKS=1: 7 s
 * looks instead). Any lock must be on the true trajectory. */
const { chromium } = require('playwright');
const TORCH = !!+process.env.TORCH, DUPLOOKS = !!+process.env.DUPLOOKS, ALL = !!+process.env.ALL;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file:///tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html');
  const seeds = (process.argv[2] || '13572468,9e3779b9,0badf00d,7f00ff01,2468ace0,5eedf00d').split(',').map(x => parseInt(x, 16) >>> 0);
  let bad = 0; const res = { carry: [], fresh: [] };
  for (const seed of seeds) for (const mode of ['carry', 'fresh']) {
    const out = await p.evaluate(async ({ seed, mode, TORCH, DUPLOOKS, ALL }) => {
      const T = window.__tot, R = T.R, F = R.FRAME_MS; document.getElementById('reset').click();
      const MAZE_END = 30 + 6 * 245, DUP0 = MAZE_END + 270, ph = seed % 50;
      const ev = new Map(); if (TORCH) for (let f = DUP0; f < DUP0 + 4000; f++) if ((f - ph) % 50 === 0) ev.set(f, { pre: [], post: Array(12).fill(359), eio: [] });
      const S = { s: seed >>> 0, nc: 5, inst: [] }, sh = [], drawSeed = {};
      for (let f = 0; f < DUP0 + 4000; f++) {
        if (f >= MAZE_END && f < DUP0 && f % 37 === 0) for (let k = 0; k < 3; k++) S.s = R.randInt(S.s, 30)[0];   // enemies
        if (f === S.nc) drawSeed[f] = S.s >>> 0;
        if (R.frameEv(S, f, ev)) sh.push(f);
      }
      const setNow = t => { window.__dt += t - performance.now(); };
      const wait = async () => { for (let i = 0; i < 1200 && T.st.searching; i++) await new Promise(r => setTimeout(r, 50)); };
      let lag = 0, rnd = seed; const rand = n => { rnd = (rnd * 1103515245 + 12345) >>> 0; return rnd % n; };
      const tOf = f => 1e5 + (f + lag) * F + 6 * F;
      const look = async (a, z) => { for (const f of sh) if (f >= a + 30 && f < z - 4) { setNow(tOf(f) + 100); T.addShine(tOf(f), true); await wait(); if (T.st.lock) return f; } return null; };
      const back = async (hideF, backF, loadLag) => { const hideT = tOf(hideF); lag += loadLag; const backT = tOf(backF); setNow(backT + 1000); T.coinBack(backT - hideT); await wait(); };
      let a = 30;
      if (mode === 'carry') for (let k = 0; k < 6; k++) { const z = a + 220; await look(a, z); if (k < 5) { await back(z, z + 25, k % 2 ? rand(7) : 0); a = z + 25; } }
      if (mode === 'carry') await back(a + 220, DUP0, rand(7) + rand(7));     // kpa_102 with C-up closed, two room loads
      a = DUP0; let lockF = null;
      if (DUPLOOKS) { for (let k = 0; k < 12 && lockF == null; k++) { const z = a + 220; lockF = await look(a, z); if (lockF == null) { await back(z, z + 25, 0); a = z + 25; } } }
      else lockF = await look(a, a + 3000);   // standing still the status bar stays up (run 3: 54 s of coin in one look)
      let ok = null;
      if (T.st.lock) { const t1 = T.st.segs[T.st.lock.seg].taps[0]; const f1 = sh.find(f => Math.abs(tOf(f) - t1) < 2); ok = f1 != null && (drawSeed[f1] >>> 0) === (T.st.lock.seed >>> 0); }
      const ex = T.SLOG.filter(x => ALL || /wideExtend|chainSearch/.test(x.ev)).map(x => x.ev + ':' + (x.to != null ? x.to : x.found != null ? x.found : x.cands != null ? x.cands : x.taps != null ? 't' + x.taps : '')).filter(x => !x.startsWith('shine')).join(' '); T.SLOG.length = 0;
      return { dupS: lockF != null ? +((lockF - DUP0) / 30).toFixed(1) : null, ok, ex };
    }, { seed, mode, TORCH, DUPLOOKS, ALL });
    if (out.ok === false) bad++;
    res[mode].push(out.dupS);
    console.log(seed.toString(16), mode, JSON.stringify(out));
  }
  console.log('seconds in the Duplighost room to lock: carried', res.carry.join(' '), '| fresh', res.fresh.join(' '));
  console.log(bad ? 'FAIL (false lock)' : 'PASS (no false locks)'); console.log('errors', errs); await b.close();
})();
