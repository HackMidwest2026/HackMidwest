/* v80 regression tests from the console session of 2026-11-08, Jr. Troopa (fixtures/console_1108.json: the logs' events
 * and seeds, numbers read off the clips; no video or frames in the repository).
 *  1. T3 (log 1794153816860): the T3 Charge locked 5cde8fa6 q32, the Bomb was confirmed on clock frame 188 (bar hide) and
 *     the runner got the Close Call; v79 dropped every state ("dropped 18.19, left 0"). The model dodges on 187..189
 *     (lag 0) and 188..190 (lag 1), so most of the -2..+1 states dodged: zwUpdate merged the shifts' states, which meet
 *     in one RNG state after the roll, and kept the first shift's outcome (a hit). Now the outcome is part of the state.
 *  2. Recovery when the outcome seen fits no state: the confirm read again -4..+4 from the states before it (no beep until
 *     two shines confirm them); none: no edge, and the next Charge locks afresh.
 *  3. The seed found again from the coin (log 1794154120837): from the T3 lock and the shines after the tracker died.
 *     T4's menu (252 s): found in it, and the clip-fed T5 lock (89f7812e) agrees with the carry from there. The T5 / T6
 *     menus alone: found on the 7th shine (1848542, ~3 s before the Power Bounce confirm), with the true states among the
 *     tracker's, and T6 planned. A lock from another seed finds nothing.
 *  4. T5 Charge (clip 11-08-04: v79 "no Mario", NCC 0.40-0.48; Mario stood until 183 ms before the trigger picture): the
 *     Mario check reads the wider window when frames -2..1 miss him; a faint Mario after a Charge-shaped burst is searched
 *     anyway (no lock from it on a picture with no rays); a read with no Mario is kept with its pictures and replays.
 * usage: node test_console_1108.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1108.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [];
  const open = async () => { const p = await b.newPage({ viewport: { width: 1300, height: 1400 } }); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
    await p.goto('file://' + PAGE); return p; };
  const p = await open();
  const r = await p.evaluate(async (FIX) => {
    const T = window.__tot, out = {}, seed3 = parseInt(FIX.t3.seed, 16), q3 = FIX.t3.q, C = FIX.t3.c;
    const K = FIX.clock, F = t => (t - K.vlag - K.t0) / K.rate;
    const start3 = () => T.jrTrackerAt(seed3, [q3], performance.now() + 3600000, 4);
    // 1. the model's dodge frames, and the console's confirm through the tracker
    start3(); const S0 = T.jrStatesAt(150);
    out.dodge = S0.map(q => T.jrClasses(q.s, q.nc, q.g, 170, 210, 'jrcc_bomb').map((v, i) => (v ? 170 + i : null)).filter(x => x != null));
    start3(); T.jrConfirmClock(5, C[5]);
    T.jrStatesAt(C[5] + 250);         // the tracker stepped on as the page does between the confirms (it merged states here)
    out.split = T.zw.parts.map(q => ({ s: q.S.s >>> 0, cc: q.cc && q.cc[5] }));
    const n0 = T.SLOG.length; T.jrConfirmClock(6, C[6]);
    const L = T.SLOG.slice(n0); out.t3 = { outcome: L.find(e => e.ev === 'jrOutcome'), dodge: L.find(e => e.ev === 'jrDodge'), recover: L.some(e => e.ev === 'jrRecover'), dead: T.zw.dead,
      allDodge: T.zw.parts.every(q => q.cc && q.cc[5] === true), parts: T.zw.parts.length, reconOk: T.jrReconOk() };
    // 2a. an outcome no state allows (confirm read 2 frames late of every dodge): rebuilt -4..+4, no beep until 2 shines
    start3(); T.jrConfirmClock(5, 199); T.jrStatesAt(199 + 250); T.jrSettle('test');
    const rec = T.SLOG.filter(e => e.ev === 'jrRecover').pop();
    T.setStep(T.jrStepFor(6)); T.jrConfirmClock(6, C[6]); T.setStep(T.jrStepFor(7));
    out.recon = { rec, dead: T.zw.dead, parts: T.zw.parts.length, allDodge: T.zw.parts.every(q => q.cc && q.cc[5] === true), ok0: T.jrReconOk(), zw0: T.jrZw() };
    T.st.plan = null; T.st.msg = null; T.makePlan(); out.recon.msg = T.st.msg; out.recon.plan = !!T.st.plan;
    { // two shines where the heaviest rebuilt state has them (the coin watched from the T4 Bomb's draws on)
      let top = null; for (const q of T.zw.parts) if (!top || q.w > top.w) top = q;
      const S = { s: top.S.s, nc: top.S.nc, inst: [] }, sh = []; let g = top.g; const ev = top.ev;
      for (; g < C[6] + 2000 && sh.length < 2; g++) { const v = T.R.frameEv(S, g, ev); if (v === true && g > C[6] + 80) sh.push(g); }
      T.zw.vis.push([C[6] + 80, sh[1] + 4]); for (const f of sh) T.zwTapF(f + 1); T.jrStatesAt(sh[1] + 10);
      out.recon.ok2 = T.jrReconOk(); out.recon.zw2 = T.jrZw(); out.recon.dbg = { sh, taps: T.zw.taps, parts: T.zw.parts.map(q => ({ w: q.w, m: [...q.m], err: q.err, g: q.g, s: q.S.s >>> 0 })), recon: T.JRT.recon, step: T.step(), prof: T.PROF ? 1 : 0 }; }
    // 2b. nothing to rebuild from: no edge, and the next Charge starts afresh
    start3(); T.jrConfirmClock(5, C[5]); T.JRT.ccSnap = null; for (const q of T.zw.parts) q.cc[5] = false; T.jrSettle('test');
    T.setStep(T.jrStepFor(7)); T.st.plan = null; T.st.msg = null; T.makePlan();
    out.lost = { dead: T.zw.dead, lost: T.JRT.lost, msg: T.st.msg, plan: !!T.st.plan };
    T.jrConfirmClock(6, C[6]); T.jrConfirmClock(7, C[7]); T.jrConfirmClock(8, Math.round(F(FIX.t5.hide) - 3));
    const lk = T.jrLockAt(parseInt(FIX.t5.clip.lock, 16), FIX.t5.clip.qs, 8); out.lost.after = { dead: T.zw.dead, origin: T.JRT.origin, cross: lk.cross, parts: T.zw.parts.length };
    // 3. the seed from the coin
    const shines = FIX.events.filter(e => e.ev === 'shine' && e.at > FIX.events.find(x => x.ev === 'jrDodge').t).map(e => e.at);
    const vis = FIX.vis.map(([a, z]) => [F(a) - 1, F(z) - 6]);
    const ins = [[6, C[6]], [7, C[7]], [8, Math.round(F(FIX.t5.hide) - 3)], [9, Math.round(F(FIX.nothingAt) - 3)]];
    const scen = (deadAgainAt8, from, seedOverride) => {
      const res = { found: null, log: [] };
      T.jrTrackerAt(seed3, [q3], performance.now() + 3600000, 4); T.zw.vis.push(...vis);
      T.jrConfirmClock(5, C[5]); T.zw.parts = []; T.zw.dead = true; T.JRT.lostF = C[6]; T.JRT.ccSnap = null;     // as v79 left it
      if (seedOverride) T.JRT.lastLock.seed = seedOverride;
      let ii = 0;
      for (const t of shines.filter(x => x >= from)) {
        const f = F(t) - 6;
        while (ii < ins.length && ins[ii][1] < f) { T.jrConfirmClock(ins[ii][0], ins[ii][1]); if (ins[ii][0] === 8 && deadAgainAt8) { T.zw.parts = []; T.zw.dead = true; T.JRT.lostF = ins[ii][1]; } ii++; }
        T.zwTapF(f);
        if (!T.zw.dead) continue;
        const k0 = T.SLOG.length; T.jrShineAt(f + 12); res.log.push(...T.SLOG.slice(k0).filter(e => /jrShine/.test(e.ev)).map(e => [Math.round(t), e.ev, e.clusters || e.pos, e.expectWrong]));
        if (!T.zw.dead) { res.found = { t, f: Math.round(f), n: T.zw.parts.length, doubt: +T.zwStates(performance.now()).doubt.toFixed(3) }; break; }
      }
      res.ii = ii; return res;
    };
    out.coinA = scen(false, 0);
    if (out.coinA.found) { const ii = out.coinA.ii; for (const [k, c] of ins.slice(ii)) { if (k > 8) break; T.jrConfirmClock(k, c); }
      out.coinA.cross = T.jrLockAt(parseInt(FIX.t5.clip.lock, 16), FIX.t5.clip.qs, 8).cross; }
    out.coinB = scen(true, 1832000);
    if (out.coinB.found) { T.setStep(T.jrStepFor(10)); const cS = out.coinB.found.f + 8, pl = T.jrPlanAt(cS, 1.5, 1, 'jrpb5');
      out.coinB.plan = { target: pl.target, p5: pl.p, p6: pl.p6, none: pl.none, doubt: pl.doubt, pbC: Math.round(F(FIX.pbHide) - 3) };
      out.coinB.at9467 = T.jrStatesAt(9467).map(q => q.s.toString(16) + ':' + q.nc); }
    out.coinWrong = scen(false, 0, 0x12345678);
    out.coinWrongB = scen(true, 1832000, 0x0badf00d);
    // 4. the T5 Charge read on pictures made here (Mario's reference patch where the Charge has him, or not)
    const M = T.chgMarioRef(), ref = Uint8Array.from(atob(M.b64), c => c.charCodeAt(0));
    let rnd = 12345; const rand = () => (rnd = (rnd * 1103515245 + 12345) >>> 0) / 4294967296;
    const mk = (g, mario, noise) => { const Y = new Uint8Array(640 * 480).fill(60 + (g % 3) * 2);
      if (mario) for (let y = 0; y < M.h; y++) for (let x = 0; x < M.w; x++) { const v = 60 + mario * (ref[y * M.w + x] - 60) + (noise ? noise * (rand() - 0.5) : 0); Y[(M.y0 + y) * 640 + M.x0 + x] = Math.max(0, Math.min(255, Math.round(v))); }
      return Y; };
    const capture = marioOf => { const t0 = performance.now() - 4000, fr = [];
      for (let i = 0; i < 16 + 2 * 50; i++) { const n = 3 + Math.floor((i - 16) / 2), mm = marioOf(n); fr.push({ t: t0 + i * 16.7, m: 60 + (n >= 3 ? Math.min(60, 6 * (n - 2)) : 0), Y: mk(n, mm && mm[0], mm && mm[1]) }); }
      // a repeated picture is the same raster
      for (let i = 1; i < fr.length; i++) if (Math.floor((i - 16) / 2) === Math.floor((i - 17) / 2)) fr[i].Y = fr[i - 1].Y;
      return { fr, trig: { t: fr[16].t, tRaw: fr[16].t, n: 3, base: 60, i: 16, d0: 6, cut: [9.85, 15.95] } }; };
    const run = async (marioOf) => { const { fr, trig } = capture(marioOf), k0 = T.SLOG.length, c0 = T.CHG_CAPS.length; T.setStep(T.jrStepFor(9));
      T.chgSolveTest(fr, trig, 'jr'); const st0 = T.CHG.state;
      for (let i = 0; i < 600 && !['notseen', 'nolock', 'failed', 'locked'].includes(T.CHG.state); i++) await new Promise(r => setTimeout(r, 100));
      for (let i = 0; i < 100 && T.CHG_CAPS.length === c0; i++) await new Promise(r => setTimeout(r, 100));
      return { st0, state: T.CHG.state, info: T.CHG.info && { marioNcc: T.CHG.info.marioNcc, marioWide: T.CHG.info.marioWide, marioWeak: T.CHG.info.marioWeak }, ev: T.SLOG.slice(k0).map(e => e.ev), cap: T.CHG_CAPS.length > c0 ? T.CHG_CAPS[T.CHG_CAPS.length - 1] : null }; };
    // the faint Mario: noise until the match reads 0.3..0.5
    let nz = 0, ncc = 1; for (const a of [120, 160, 200, 240, 300, 360, 440, 520]) { rnd = 777; const v = T.chgMarioNcc(mk(0, 1, a)); if (v < 0.5 && v >= 0.3) { nz = a; ncc = v; break; } }
    out.ncc = { full: T.chgMarioNcc(mk(0, 1, 0)), none: T.chgMarioNcc(mk(0, 0, 0)), faint: ncc, noise: nz };
    const none = await run(() => null);
    out.none = { st0: none.st0, state: none.state, ev: none.ev, cap: none.cap && { outcome: none.cap.result && none.cap.result.outcome, pics: none.cap.pics.length, prof: none.cap.prof } };
    if (none.cap) { const rr = await T.chgReplay(none.cap); out.none.replay = rr.state; }
    const wide = await run(n => (n <= -3 ? [1, 0] : null));
    out.wide = { st0: wide.st0, state: wide.state, info: wide.info, notseen: wide.ev.includes('chargeNotSeen') };
    rnd = 777; const weak = await run(n => (n >= -2 && n <= 1 ? [1, nz] : null));
    out.weak = { st0: weak.st0, state: weak.state, info: weak.info, logged: weak.ev.includes('chargeMarioWeak'), locked: weak.ev.includes('chargeLock') };
    return out;
  }, FIX);
  // 1
  console.log('  model dodges (lag 0 / 1): ' + r.dodge.map(x => x.join(',')).join(' / '));
  check(JSON.stringify(r.dodge) === JSON.stringify([FIX.t3.dodgeModel.lag0, FIX.t3.dodgeModel.lag1]), 'the T3 lock\'s Close Call frames match the fixture (the re-simulation)');
  check(FIX.t3.dodgeModel.lag0.includes(188) && FIX.t3.dodgeModel.lag1.includes(188), 'the confirm read (188) dodges in both lags: the model allows what the runner got');
  const sameS = new Set(r.split.map(x => x.s)).size, mixed = r.split.some(x => x.cc) && r.split.some(x => !x.cc);
  console.log('  after the T3 confirm, stepped on: ' + r.split.length + ' states over ' + sameS + ' RNG states, outcomes ' + r.split.map(x => (x.cc ? 'D' : 'h')).join(''));
  check(mixed && sameS < r.split.length, 'shifts with different outcomes share an RNG state after the roll and stay apart');
  console.log('  T3 outcome: ' + JSON.stringify(r.t3));
  check(r.t3.outcome && r.t3.outcome.dodge && r.t3.dodge && r.t3.dodge.left > 0 && !r.t3.dead && r.t3.allDodge && !r.t3.recover, 'the Close Call keeps the states that dodge (v79: left 0)');
  // 2
  console.log('  rebuilt: ' + JSON.stringify(r.recon).slice(0, 400));
  check(r.recon.rec && !r.recon.dead && r.recon.parts > 0 && r.recon.allDodge, 'an outcome no state allows: rebuilt from the confirm -4..+4, only states that dodge');
  check(!r.recon.ok0 && !r.recon.zw0 && !r.recon.plan && /No edge yet/.test(r.recon.msg || ''), 'no beep from the rebuilt states before the coin confirms them');
  if (!(r.recon.ok2 && r.recon.zw2)) console.log('  dbg ' + JSON.stringify(r.recon.dbg));
  check(r.recon.ok2 && r.recon.zw2, 'two shines on the heaviest rebuilt state: it plans again');
  console.log('  lost: ' + JSON.stringify(r.lost).slice(0, 300));
  check(r.lost.dead && /dodged/.test(r.lost.lost || '') && !r.lost.plan && /No edge/.test(r.lost.msg || ''), 'nothing to rebuild from: no edge');
  check(!r.lost.after.dead && r.lost.after.origin === 8 && r.lost.after.parts > 0, 'the T5 Charge lock starts the tracker afresh');
  // 3
  console.log('  coin, T4 menu: ' + JSON.stringify(r.coinA.found) + ' ' + JSON.stringify(r.coinA.log.slice(-2)));
  check(r.coinA.found && r.coinA.found.t < FIX.vis[0][1], 'tracker dead from T3: the T4 menu\'s shines find the seed again in that menu');
  check(r.coinA.cross && r.coinA.cross.agree, 'and the T5 lock (89f7812e, clip-fed) agrees with the carry from there');
  console.log('  coin, T5/T6 menus: ' + JSON.stringify(r.coinB.found) + ' ' + JSON.stringify(r.coinB.log) + ' plan ' + JSON.stringify(r.coinB.plan));
  check(r.coinB.found && r.coinB.found.t <= 1848542 && r.coinB.log.some(x => x[1] === 'jrShineSearch' && Array.isArray(x[2]) && x[2].length > 1), 'T5/T6 shines alone: ambiguous at first (no edge), found by the 7th shine');
  check(r.coinB.at9467 && ['c5a92300:9512', 'd6573893:9513'].every(s => r.coinB.at9467.includes(s)), 'the found states hold the carried truth (c5a92300 / d6573893 at frame 9467)');
  check(r.coinB.plan && !r.coinB.plan.none && r.coinB.plan.target < r.coinB.plan.pbC && r.coinB.plan.p5 >= 0.6, 'T6 Power Bounce planned before the runner\'s press (frame ' + (r.coinB.plan && r.coinB.plan.target) + ' < ' + (r.coinB.plan && r.coinB.plan.pbC) + ')');
  check(!r.coinWrong.found && !r.coinWrongB.found, 'a lock from another seed finds nothing (no edge)');
  // 4
  console.log('  clip scan (T5, ms: NCC): ' + FIX.t5.clip.scan.map(x => x.join(':')).join(' '));
  check(FIX.t5.clip.scan.filter(x => x[0] >= -170 && x[0] <= -60).every(x => x[1] < 0.5) && FIX.t5.clip.scan.some(x => x[0] >= -300 && x[1] >= 0.9), 'the clip: frames -2..1 by time miss Mario, the wider window has him');
  console.log('  Mario NCC: ' + JSON.stringify(r.ncc));
  console.log('  no Mario: ' + JSON.stringify(r.none));
  check(r.none.state === 'notseen' && r.none.cap && r.none.cap.outcome === 'notseen' && r.none.cap.pics > 10 && r.none.cap.prof === 'jr', 'a read with no Mario is kept with its pictures');
  check(r.none.replay === 'notseen', 'and replays as it ran');
  console.log('  Mario before frame -2 only: ' + JSON.stringify(r.wide));
  check(!r.wide.notseen && r.wide.info && r.wide.info.marioWide && r.wide.info.marioNcc >= 0.9, 'Mario standing earlier than frame -2: the wider window finds him and the read goes on');
  console.log('  faint Mario: ' + JSON.stringify(r.weak));
  check(r.ncc.faint >= 0.3 && r.ncc.faint < 0.5 && r.weak.logged && r.weak.info && r.weak.info.marioWeak && ['nolock', 'failed'].includes(r.weak.state) && !r.weak.locked, 'a faint Mario after a Charge-shaped burst: searched anyway, and no lock from a picture with no rays');
  check(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' / ') : ''));
  await b.close();
  console.log(fails ? fails + ' FAILED' : 'all passed');
  process.exit(fails ? 1 : 0);
})();
