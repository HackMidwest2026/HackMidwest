/* v76 regression tests from the real console session of 2026-11-07 (fixtures/console_1107.json: frames read off the
 * clips; the video stays out of the repository).
 *  1. Duplighosts: from each console lock the page's own core predicts the copies the clip shows at the Do Nothing frame
 *     the page measured (within the +-1 frame the Charge clock is placed to), and the press reading uses the 3-frame box
 *     offset the clips confirm (highlight frame, then gone).
 *  2. A Duplighost Charge seen on a Jr. Troopa step moves the route back to the Duplighosts (retries); Jr. Troopa's own
 *     arena (console colours) does not.
 *  3. A coin (walk) lock never makes a Duplighost plan on the Charge-lock route.
 *  4. No new plan while the bar is hidden after the planned press (Jr. Troopa T3: a replan went out after the confirm).
 *  5. Final Bowser: a Charge burst moves the route off T1's Charge step and on to the next Charge's turn; the reader arms
 *     again after a lock; the shift retry the trigger level points at goes first.
 *  6. The strip's top stays put while the status text, the countdown and the route step change (desktop and phone).
 *  7. The route list: one line per turn, the current one highlighted; the version string.
 *  8. Final Bowser re-score (log 1794071163309: 37 plans in 9 s): with the runner's press spread the 4-a-second re-score
 *     reads the plan's own chance, no replan, the beeps play through; a carry with every state ruled out is dropped.
 * usage: node test_console_1107.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1107.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
const cls = seen => { const n = [...seen].filter(c => c === 'C').length; return n >= 4 ? 4 : n === 3 ? 3 : 2; };
(async () => {
  const b = await chromium.launch(); const errs = [];
  const open = async (vp) => { const p = await b.newPage({ viewport: vp || { width: 1300, height: 1400 } }); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
    await p.goto('file://' + PAGE); return p; };
  const p = await open();
  const r = await p.evaluate(async (FIX) => {
    const T = window.__tot, out = { version: T.VERSION, ver: document.getElementById('ver').textContent, title: document.title, h1: document.querySelector('h1').textContent };
    const sel = document.getElementById('s-duproute'); sel.value = 'charge'; sel.dispatchEvent(new Event('change'));
    // 1. copies from each console lock
    out.dup = FIX.dup.map(a => {
      T.setStep(0); T.dupTrackerAt(parseInt(a.seed, 16), a.qs, performance.now() - 2000);
      const S = T.dupStatesAt(100), f = Math.round(a.target + a.err);
      const byQ = S.map(q => ({ w: q.w, cls: T.dupClasses(q.s, q.nc, q.g, f - 2, f + 2) }));
      return { f, byQ, van: T.R.PROFILES.dup3.vanish };
    });
    // 2. arena: stub the picture's colours at the bar hide (sample() is what chgArena reads)
    const colours = (low, top) => (box, w, h) => { const isTop = box.y < 0.25, c = isTop ? top : low, a = new Uint8ClampedArray(w * h * 4); for (let i = 0; i < a.length; i += 4) { a[i] = c[0]; a[i + 1] = c[1]; a[i + 2] = c[2]; a[i + 3] = 255; } return a; };
    const jrI = T.RT().findIndex(x => x.chg === 'jr'), sj = colours(FIX.arena.jr.low, FIX.arena.jr.top), sd = colours(FIX.arena.dup.low, FIX.arena.dup.top);
    T.setStep(jrI); const aj = T.withSample(sj, () => T.chgArena()), pj = T.withSample(sj, () => T.chgArenaProf(T.CHG_PROF.jr, true));
    out.arenaJr = { a: aj.a, prof: pj.id, step: T.step(), jrI };
    T.setStep(jrI); const ad = T.withSample(sd, () => T.chgArena()), pd = T.withSample(sd, () => T.chgArenaProf(T.CHG_PROF.jr, true));
    out.arenaDup = { a: ad.a, prof: pd.id, step: T.step() };
    T.setStep(jrI + 2); const pd2 = T.withSample(sd, () => T.chgArenaProf(T.CHG_PROF.jr, false));      // not a real hide: no move
    out.arenaNotReal = { prof: pd2.id, step: T.step(), want: jrI + 2 };
    // 3. a coin lock on the Duplighost step: no plan
    { const R = T.R; let s = 0x2468ace0, f = 0; const taps = [], now = performance.now();
      while (taps.length < 20) { s = R.adv(s); const sh = s >= R.SHINE_MIN; if (sh) taps.push(f); for (let i = 0; i < (sh ? 48 : 24); i++) s = R.adv(s); f += sh ? 48 : 24; }
      const end = taps[taps.length - 1]; T.st.segs[0].taps = taps.map(x => now - (end - x) * R.FRAME_MS + 6 * R.FRAME_MS + 200); T.find();
      for (let i = 0; i < 900 && !T.st.lock; i++) await new Promise(r => setTimeout(r, 100));
      T.setStep(0); T.zw.on = false; T.chgReset(); T.st.plan = null; T.makePlan();
      out.walkLock = { locked: !!T.st.lock, plan: !!T.st.plan, msg: T.st.msg || '' };
      // 4. the replan hold, on Hallway T2 with that lock
      const hi = T.RT().findIndex(x => x.prof === 'timeout'); T.setStep(hi); T.st.plan = null; T.makePlan(); const P = T.st.plan;
      out.hold = { plan: !!P };
      if (P) { const n = performance.now(); P.tPress = n - 1000; P.tMade = n - 4000; T.V.hudGone = n - 500; T.st.planTry = 0; T.autoPlan();
        out.hold.kept = T.st.plan === P; T.V.hudGone = 0; T.st.planTry = 0; T.autoPlan(); out.hold.after = T.st.plan !== P;
        out.hold.logged = T.SLOG.some(e => e.ev === 'replanHeld'); }
    }
    // 5. Final Bowser steps by burst
    { const L = T.RT(), c1 = L.findIndex(x => x.fb14 === 1 && x.fb14role === 'charge'), l1 = L.findIndex(x => x.fb14 === 1 && x.fb14role === 'lever'), s2 = L.findIndex(x => x.fb14 === 2), s4 = L.findIndex(x => x.fb14 === 4), s3 = L.findIndex(x => x.fb14 === 3);
      const F = window.__fb14.FB14, trig = t => { T.CHG.trig = { t }; T.fb14Trigger(); return T.step(); };
      T.setStep(c1); const n0 = performance.now();
      const a1 = trig(n0);                         // T1's Charge on its Charge step -> the Cloud Nine step
      const a2 = trig(n0 + 3000);                  // a burst 3 s later on the lever step: not the next turn
      const a3 = trig(n0 + 20000);                 // T2's Charge with no Cloud Nine confirm seen -> T2's step
      const a4 = trig(n0 + 20500);                 // T2's own burst again: stays
      T.setStep(s3); const a5 = trig(n0 + 60000);  // a burst on T3 (no Charge there): T4's
      // the reader arms again after a lock
      T.setStep(l1); T.CHG.state = 'locked'; T.fb14AfterLock(); const rearm = T.CHG.state;
      out.fb = { c1, l1, s2, s3, s4, a1, a2, a3, a4, a5, rearm,
        order: [T.chgShiftOrder([1, -1], { d0: 15.8, cut: [10.9, 16.5] }), T.chgShiftOrder([1, -1], { d0: 13.5, cut: [10.9, 16.5] }), T.chgShiftOrder([1, -1], { d0: 11.2, cut: [10.9, 16.5] })] };
      T.CHG.trig = null; T.chgReset(); }
    // 7. the route list
    T.setStep(1);
    const lis = [...document.querySelectorAll('#route-list li')].map(li => li.textContent), cur = document.querySelector('#route-list [data-i][style*="700"]');
    out.list = { html: document.getElementById('route-list').innerHTML, lis, cur: cur && cur.textContent, n: document.querySelectorAll('#route-list [data-i]').length };
    return out;
  }, FIX);
  // 1
  r.dup.forEach((d, i) => {
    const a = FIX.dup[i], want = cls(a.seen);
    const at0 = d.byQ.some(q => q.cls[2] === want), near = d.byQ.some(q => q.cls[1] === want || q.cls[2] === want || q.cls[3] === want);
    console.log('  ' + a.clip + ': lock ' + a.seed + ', measured frame ' + d.f + ', seen ' + a.seen + ' (' + want + '), page classes f-2..f+2 per state: ' + d.byQ.map(q => q.cls.join('')).join(' '));
    check(near, 'Duplighost ' + a.seed + ': the copies seen (' + a.seen + ') are predicted within 1 frame of the measured Do Nothing frame' + (at0 ? ' (on it)' : ''));
    const err = (a.tObs - a.tPress - FIX.vlag) / FIX.consoleRate - 0.5 + FIX.off - d.van;
    check(Math.abs(err - a.err) < 0.05, 'press reading ' + err.toFixed(2) + ' = the log\'s ' + a.err + ' with the 3-frame box offset');
    check(a.boxGoneCap - a.boxHighlightCap === 2, 'one highlighted game frame before the box goes (confirm + 2 / + 3, as the emulator)');
  });
  check(r.dup[0].byQ.some(q => q.cls[2] === 2), '55ee0a3f: the failed attempt (FFCC) is the model on the measured frame, 2 before the target');
  check(r.dup.every(d => d.van === 3), 'dup3 keeps the 3-frame Strategies box offset');
  // 2
  console.log('  arena jr ' + JSON.stringify(r.arenaJr) + ' dup ' + JSON.stringify(r.arenaDup));
  check(r.arenaJr.a !== 'dup' && r.arenaJr.prof === 'jr' && r.arenaJr.step === r.arenaJr.jrI, 'Jr. Troopa\'s arena (console colours) stays on Jr. Troopa');
  check(r.arenaDup.a === 'dup' && r.arenaDup.prof === 'dup' && r.arenaDup.step === 0, 'the Duplighost room at a bar hide on a Jr. Troopa step goes back to the Duplighosts');
  check(r.arenaNotReal.prof === 'jr' && r.arenaNotReal.step === r.arenaNotReal.want, 'not at a real bar hide: no move');
  // 3
  console.log('  walk lock: ' + JSON.stringify(r.walkLock).slice(0, 200));
  check(r.walkLock.locked && !r.walkLock.plan && /No Charge lock/.test(r.walkLock.msg), 'a coin lock makes no Duplighost plan on the Charge-lock route');
  // 4
  console.log('  hold: ' + JSON.stringify(r.hold));
  check(r.hold.plan && r.hold.kept && r.hold.logged, 'no new plan while the bar is hidden after the planned press');
  check(r.hold.after, 'with the bar back the page plans again');
  // 5
  console.log('  fb: ' + JSON.stringify(r.fb));
  check(r.fb.a1 === r.fb.l1, 'Final Bowser: T1\'s burst moves the route to the Cloud Nine step');
  check(r.fb.a2 === r.fb.l1, 'a burst soon after does not skip a turn');
  check(r.fb.a3 === r.fb.s2 && r.fb.a4 === r.fb.s2, 'T2\'s Charge with no Cloud Nine confirm seen moves the route to T2 (once)');
  check(r.fb.a5 === r.fb.s4, 'a burst on T3 is T4\'s Charge');
  check(r.fb.rearm === 'idle', 'the reader arms again after a lock');
  check(JSON.stringify(r.fb.order) === '[[-1,1],[1,-1],[1,-1]]', 'the shift retry next to the trigger level goes first');
  // 7
  console.log('  route list: ' + r.list.lis.slice(0, 10).join(' | '));
  check(!/<br>/.test(r.list.html), 'no second line under a turn');
  check(r.list.lis.some(x => /^1\. T1: Charge; Bombette Do Nothing/.test(x)) && r.list.lis.some(x => /^2\. T1: Charge; Bomb$/.test(x)), 'each turn reads "N. Tn: actions"');
  check(/^2\. T1: Charge; Bomb/.test(r.list.cur || ''), 'the current step\'s turn line is highlighted');
  check(r.version === 'v78' && r.ver === 'v78', 'version v78 in the log and the header');
  check(r.title === 'Paper Mario (Any% No ACE) (RNG Manipulation)' && /RNG Manipulation/.test(r.h1), 'the page\'s new name in the title and header');
  await p.close();
  // 8. the Final Bowser plan / re-score
  { const fx = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_logs.json'), 'utf8'));
    const q = await open();
    const g = await q.evaluate(async ({ L, presses }) => {
      const T = window.__tot, F = window.__fb14, X = F.FB14, rate = 33.4253;
      T.presses.length = 0; presses.forEach(x => T.presses.push(x));
      const OFF = 1000, ph = [(((L.ph[0] - OFF) % 130) + 130) % 130, (((L.ph[1] - OFF) % 220) + 220) % 220], c = Uint8Array.from(L.aura);
      const lever = T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever'), out = { runs: [] };
      for (let k = 0; k < 4; k++) {
        const truth = F.fbNew({ s: (0x9e3779b9 * (k + 3)) >>> 0, nc: OFF + 61 + 7 * k, f: OFF + 61, c, ph, l: 0, w: 1, from: OFF + 61 });
        const S0 = F.fbClone(truth); S0.ev.push({ k: 'chg', f: OFF + 13 }, { k: 'chg', f: OFF + 16 }); S0.ev.sort((a, b) => a.f - b.f);
        const S1 = F.fbClone(S0); S1.l = 1; S0.w = 0.75; S1.w = 0.25; S0.lw = S1.lw = 1; S0.from = S1.from = S0.f;
        T.setStep(lever); X.on = true; X.states = [S0, S1]; X.taps = []; X.vis = []; X.visFrom = null; X.bg = 0; X.bgFrom = 0; X.rate = rate; X.gone = false; X.allOutLogged = false;
        X.t0 = performance.now() - (OFF + 220) * rate; X.lastT = null; T.st.plan = null;
        const n0 = T.SLOG.length; F.plan(); const P = T.st.plan; if (!P) { out.runs.push({ none: true, msg: T.st.msg }); continue; }
        const pNow = [];
        while (performance.now() < P.tPress - 50) { await new Promise(r => setTimeout(r, 250)); F.tick(performance.now()); if (P.mix.pNow != null) pNow.push(P.mix.pNow); }
        const ev = T.SLOG.slice(n0).map(e => e.ev);
        out.runs.push({ p: +P.mix.p.toFixed(3), pNow: pNow.slice(0, 4), replans: ev.filter(e => e === 'fb14Replan').length, cancels: ev.filter(e => e === 'beepsCancelled').length, kept: T.st.plan === P, PDn: P.PD.length });
        cancelBeepsSafe();
      }
      function cancelBeepsSafe() { try { T.st.plan = null; } catch (e) {} }
      // a carry with every state ruled out: dropped, plain message, the next Charge locks afresh
      T.setStep(lever); X.on = true; X.t0 = performance.now() - 2000 * rate; X.states = []; X.gone = true; T.st.plan = null; F.plan();
      out.gone = { msg: T.st.msg || '', on: X.on, t0: X.t0 };
      return out;
    }, { L: fx[0], presses: [-2.34, -2.98, -1.77, -1.31, -0.81, 1.94, 0.40, -1.07] });
    console.log('  fb re-score: ' + JSON.stringify(g.runs));
    const runs = g.runs.filter(x => !x.none);
    check(runs.length >= 3, 'Final Bowser: plans made (' + runs.length + ' of ' + g.runs.length + ')');
    check(runs.every(x => x.replans === 0 && x.kept), 'no replan of a plan the re-score agrees with: the beeps play through');
    check(runs.every(x => x.pNow.every(v => Math.abs(v - x.p) < 0.03)), 'the re-score reads the plan\'s own chance (the runner\'s spread, -4..+4)');
    console.log('  carry gone: ' + g.gone.msg.slice(0, 160));
    check(/carried seed is gone/.test(g.gone.msg) && !g.gone.on && g.gone.t0 == null, 'every state ruled out: the carry is dropped and the next Charge locks afresh');
    await q.close(); }
  // 6. the strip's position
  for (const vp of [{ width: 1300, height: 1400 }, { width: 390, height: 844 }]) {
    const q = await open(vp);
    const g = await q.evaluate(async () => {
      const T = window.__tot, top = () => { const e = document.getElementById('strip'); return e.getBoundingClientRect().top + window.scrollY; }, tops = [top()];
      const long = 'Collecting shines across rooms: 12 so far. '.repeat(6);
      for (const [h, d] of [['x', ''], [long, long + long], ['Locked', 'short']]) { document.getElementById('headline').textContent = h; document.getElementById('detail').textContent = d; await new Promise(r => requestAnimationFrame(r)); tops.push(top()); }
      const c = document.getElementById('count'); c.hidden = false; c.innerHTML = '12.3<small> s to press</small>'; await new Promise(r => requestAnimationFrame(r)); tops.push(top());
      c.innerHTML = '0.0<small> s to press</small>'; await new Promise(r => requestAnimationFrame(r)); tops.push(top()); c.hidden = true;
      for (const i of [0, 1, 3, 8, 10]) { T.setStep(i); T.st.msg = 'Step ' + i + ' ' + 'with a long message '.repeat(i); T.render && T.render(); await new Promise(r => requestAnimationFrame(r)); tops.push(top()); }
      return tops;
    });
    console.log('  ' + vp.width + 'px strip tops: ' + g.map(x => x.toFixed(1)).join(' '));
    check(g.every(x => Math.abs(x - g[0]) < 0.5), vp.width + ' px: the strip stays put while the status text, the countdown and the step change');
    await q.close();
  }
  check(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' / ') : ''));
  await b.close();
  console.log(fails ? fails + ' FAILED' : 'all passed');
  process.exit(fails ? 1 : 0);
})();
