/* v82 regression tests from the console logs of 2026-11-08 evening (Time Out Timer v81; fixtures/console_1108b.json holds
 * the events and numbers; the Charge reads are pictures, so they are read from the uploaded logs at run time and those
 * checks are skipped when the logs are absent).
 *  1. Jr. Troopa Charge reads: 4 of 9 first reads of log A (and T5 of log D) no-locked at 1.0x and locked on a re-read
 *     1.3-1.9 s later. The emulator brightness curve was 2-4 levels darker than the console's on frames 7-26, so the
 *     placement put a skip into the rise and took it out at ~21. With the console curve every one locks on its first
 *     placement, on the seed the live re-read found.
 *  2. Jr. Troopa T3 (log A, middle fight): the plan from the tracker before the target screen shows (v81 planned only on
 *     that screen; the runner confirmed 0.4 s after the menu opened, before any plan), never earlier than a plan made on
 *     the screen; the press measured at the confirm the tracker reads, an off-beep press logged but kept out of the spread.
 *  3. Hallway (logs C and E): after Time Out the rest of the battle hides the coin ~13.6 s; v81 stepped back to T1 there.
 *  4. Final Bowser (log C): T1's Cloud Nine confirm was never read (no target screen), so the carry had no Cloud Nine:
 *     T2's doubt 63%. The same lock and coin with Cloud Nine from the bar hiding: 1.5%, and T2 "no edge" (the states agree
 *     the frame the runner pressed is a hit: Bowser's fire hit Mario there). The T2 Charge peaked at +58, over the
 *     emulator curve's shape bound: the console curve takes it. The bar hide gives the Cloud Nine confirm.
 *     Log F: Bowser hit Mario on T1 (Life Shroom); the T2 read matched none of the carried states and v81 planned T2 from a
 *     fresh lock at doubt 0.7% (wrong): a contradicted or weak read starts doubtful, the badge is not green, a hit (HP 10
 *     then blank) ends the attempt's beeps.
 * usage: node test_console_1108b.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const U = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887';
const LOGA = U + '/e7954ce1-pm-rng-log-1794169121337.json', LOGC = U + '/26031105-pm-rng-log-1794169517521.json', LOGD = U + '/ccc6d6a3-pm-rng-log-1794170011547.json', LOGF = U + '/77f91cbb-pm-rng-log-1794170840652.json';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1108b.json'), 'utf8'));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
const readLog = f => (fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null);
(async () => {
  const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); fs.createReadStream(PAGE).pipe(r); });
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const url = 'http://127.0.0.1:' + srv.address().port + '/';
  const b = await chromium.launch(), errs = [];
  const open = async () => { const p = await b.newPage({ viewport: { width: 1300, height: 1400 } }); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
    await p.goto(url); return p; };
  // ---- 1. the Jr. Troopa Charge reads
  const A = readLog(LOGA), D = readLog(LOGD);
  if (!A || !D) console.log('skip 1: logs A / D not present');
  else {
    const p = await open();
    const caps = FIX.jrCaptures.A.map(i => ['A' + i, A.chargeCaptures[i], FIX.jrCaptures.seedsA[i]]).concat(FIX.jrCaptures.D.map(i => ['D' + i, D.chargeCaptures[i], FIX.jrCaptures.seedsD[i]]));
    for (const [name, c, seed] of caps) {
      const r = await p.evaluate(async c => { const r = await window.__tot.chgReplay(c, { maxAlts: 0 }); return { state: r.state, best: r.best, att: r.attempts.length }; }, c);
      check(r.state === 'locked' && r.best && r.best.seed === seed && r.att === 1, '1. ' + name + ' (' + c.stepT + ', live: ' + (c.result.alt ? 're-read ' + c.result.alt : 'first read') + ', ' + c.result.lockAfterRaysMs + ' ms): locks ' + seed + ' on the first placement (' + (r.best && r.best.seed + ' ' + r.best.score + ' ' + r.best.ratio + 'x') + ')');
    }
    await p.close();
  }
  // ---- 2. Jr. Troopa T3: the early plan, the press
  {
    const p = await open();
    const r = await p.evaluate(J => {
      const T = window.__tot, out = {}, rate = T.consoleRate ? 1000 / 29.97 : 33.37;
      // the T1 lock 31 s ago: now is clock frame ~940, after the T3 Charge's confirm (866) and its rays (eio to +61)
      const trigT = performance.now() - 940 * 33.367;
      out.on = T.jrTrackerAt(parseInt(J.seed, 16), J.qs, trigT, 0);
      for (const k of [1, 2, 3, 4]) T.jrConfirmClock(k, J.c[k]);
      const stp = T.RT()[T.step()]; out.step = stp && stp.t; out.prof = T.PROF ? T.PROF().id : null;
      out.floor = T.jrPlanFloor(); out.now = T.zwF(performance.now(), 0);
      T.st.plan = null; T.st.planTry = 0; T.jrEarlyPlan(performance.now());
      const P = T.st.plan, pl = T.SLOG.filter(e => e.ev === 'plan').pop();
      out.plan = P && { early: P.early, target: P.zwAbs, tPress: P.tPress, p: P.mix.p, doubt: P.mix.doubt, firstBeepIn: pl && pl.firstBeepIn, logEarly: pl && pl.early };
      // the press on the beeps: measured at the confirm (the bar hide), into the spread
      const n0 = T.presses.length, s0 = T.SLOG.length;
      if (P) T.jrConfirmClock(5, P.zwAbs);
      const pr = T.SLOG.slice(s0).find(e => e.ev === 'press');
      out.press = pr && { err: pr.err, onBeeps: pr.onBeeps, src: pr.src, k: pr.k }; out.pushed = T.presses.length - n0;
      return out;
    }, FIX.jrMiddle);
    console.log('2', JSON.stringify(r));
    check(r.on && /T3/.test(r.step || ''), '2. the tracker from the T1 lock carried to T3 (' + r.step + ')');
    check(r.floor === 866 + 110 + 45 + 10, '2. the earliest planned frame: the Charge confirm 866 + 110 (the menu) + 45 (the lead) + 10 = ' + r.floor);
    check(r.plan && r.plan.early && r.plan.logEarly && r.plan.target >= r.floor, '2. planned before the target screen showed (v81: no plan until the screen, which came after the runner\'s confirm): frame ' + (r.plan && r.plan.target) + ', ' + (r.plan && Math.round(r.plan.p * 100)) + '%, doubt ' + (r.plan && r.plan.doubt) + ', first beep in ' + (r.plan && r.plan.firstBeepIn) + ' ms');
    check(r.press && Math.abs(r.press.err) < 0.6 && r.press.onBeeps && r.press.k === 5 && r.pushed === 1, '2. the T3 Bomb press is measured at its bar-hide confirm and goes into the spread (' + JSON.stringify(r.press) + ')');
    const r2 = await p.evaluate(J => {
      const T = window.__tot, trigT = performance.now() - 940 * 33.367;
      T.jrTrackerAt(parseInt(J.seed, 16), J.qs, trigT, 0); for (const k of [1, 2, 3, 4]) T.jrConfirmClock(k, J.c[k]);
      T.st.plan = null; T.st.planTry = 0; T.jrEarlyPlan(performance.now()); const P = T.st.plan; if (!P) return null;
      const n0 = T.presses.length, s0 = T.SLOG.length; T.st.plan.tMade = performance.now() - 30000;   // (the plan stands; the press 44 frames early, as log A t=872115)
      T.jrConfirmClock(5, P.zwAbs - 44);
      const pr = T.SLOG.slice(s0).find(e => e.ev === 'press'); return { err: pr && pr.err, onBeeps: pr && pr.onBeeps, pushed: T.presses.length - n0 };
    }, FIX.jrMiddle);
    check(r2 && r2.err < -40 && r2.onBeeps === false && r2.pushed === 0, '2. a press 44 frames off the beeps is logged and kept out of the press spread (' + JSON.stringify(r2) + ')');
    await p.close();
  }
  // ---- 3. the Hallway after Time Out: no step back
  {
    const p = await open();
    await p.addInitScript(() => {});
    const r = await p.evaluate(async H => {
      const real = performance.now.bind(performance); let dt = 0; performance.now = () => real() + dt; const setNow = t => { dt += t - performance.now(); };
      const T = window.__tot, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'); document.getElementById('reset').click(); T.setStep(hi);
      const steps = [];
      for (const e of H.events) {
        if (e.ev === 'screenClosed') { setNow(e.t); T.checkPress(e.at); }
        else if (e.ev === 'coinBack') { setNow(e.t); T.coinBack(e.hiddenMs); }
        else if (e.ev === 'chargeConfirm') { setNow(e.t); if (T.step() !== hi) T.setStep(hi); }
        steps.push([e.t, T.step()]);
      }
      const L = T.SLOG;
      return { hi, done: L.filter(x => x.ev === 'hallwayDone').length, back: L.filter(x => x.ev === 'stepBackToHallway').length, held: L.filter(x => x.ev === 'stepBackHeld').map(x => x.hiddenMs),
        after: H.stepBackAt.map(t => (steps.filter(s => s[0] <= t + 1).pop() || [0, -1])[1]) };
    }, FIX.hallway);
    console.log('3', JSON.stringify(r));
    check(r.done === 2 && r.back === 0, '3. Time Out twice (hallwayDone ' + r.done + '), no step back to Hallway T1 (' + r.back + '; v81 stepped back at ' + FIX.hallway.stepBackAt.join(', ') + ')');
    check(r.held.length >= 2 && r.held.every(ms => ms > 13000 && ms < 14000) && r.after.every(s => s === r.hi + 1), '3. the ~13.6 s coin hides after Time Out are held (' + r.held.join(', ') + ' ms) and the route stays on Hallway T2');
    await p.close();
  }
  // ---- 4. Final Bowser
  {
    const p = await open();
    const r0 = await p.evaluate(() => { const T = window.__tot, P = T.CHG_PROF.fb1, B = P.bright(); return { b17: B[17 - 3], b14: B[14 - 3], up: P.shapeUp, cut: P.trigCut, hi: P.trigHi }; });
    // the T2 Charge's picture at +465 ms (frame ~17): +58.1 over the menu; the shape check's bound over frames 15.5..18.5
    const n = 3 + 465 / 33.367, lo = Math.max(3, Math.floor(n - 1.5)), hiK = Math.ceil(n + 1.5);
    const hiB = await p.evaluate(([lo, hiK]) => { const B = window.__tot.CHG_PROF.fb1.bright(); let h = -1e9; for (let k = lo; k <= hiK; k++) h = Math.max(h, B[k - 3]); return h; }, [lo, hiK]);
    const d = FIX.fb.t2.m - FIX.fb.t2.base, bound = hiB + 10 + (r0.up || 0) * Math.abs(hiB);
    check(d <= bound && d > 46.6 + 10, '4. the T2 burst (+' + d.toFixed(1) + ') is inside the shape bound (' + bound.toFixed(1) + ') that the emulator curve put at 56.6');
    // the Cloud Nine confirm from the bar hiding, before the lock: kept for the lock with its shifts
    const rb = await p.evaluate(() => {
      const T = window.__tot, X = window.__fb14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
      X.FB14.lastBurst = { turn: 1, t: performance.now() - 4000 };     // (v86: after the T1 Charge's burst, as live)
      const s0 = T.SLOG.length; let t = performance.now();
      for (let i = 0; i < 60; i++) { t += 16.7; T.fb14Frame ? T.fb14Frame(t, true) : null; }
      for (let i = 0; i < 24; i++) { t += 16.7; T.fb14Frame ? T.fb14Frame(t, false) : null; }
      const L = T.SLOG.slice(s0); return { has: !!T.fb14Frame, byBar: L.filter(e => e.ev === 'fb14CloudNineByBar').length, before: L.filter(e => e.ev === 'fb14ConfirmBeforeLock').length, pend: X.FB14.pend.map(x => ({ turn: x.turn, n: x.shifts && x.shifts.length })) };
    });
    check(rb.byBar === 1 && rb.before === 1 && rb.pend.length === 1 && rb.pend[0].turn === 1 && rb.pend[0].n === 5, '4. T1\'s bar hide on the Cloud Nine step is its confirm, kept for the lock (' + JSON.stringify(rb) + ')');
    const C = readLog(LOGC);
    if (!C) console.log('skip 4b: log C not present');
    else {
      const cap = C.chargeCaptures.find(c => c.prof === 'fb1');
      const run = async c9 => p.evaluate(async ({ cap, c9, F }) => {
        const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
        const rr = await T.chgReplay(cap, { fb14: true }); if (rr.state !== 'locked') return { lock: rr.state };
        const tt = f => FB.t0 + f * FB.rate, adv = h => FB.states.forEach(S => X.fbRun(S, h - S.l));
        FB.taps = F.taps.map(f => tt(f + 4.8)); FB.vis = F.vis.map(([a, b]) => [tt(a - 30), tt(b + 4)]); FB.visFrom = null;
        const SH = { chg: [[-1, 0.25], [0, 0.5], [1, 0.25]], nothing: [[-2, 0.1], [-1, 0.25], [0, 0.4], [1, 0.2], [2, 0.05]], jelly: [[-1, 0.25], [0, 0.5], [1, 0.25]], cn: [[-2, 0.1], [-1, 0.2], [0, 0.35], [1, 0.25], [2, 0.1]] };
        const inputs = (c9 != null ? [['cn', c9, 1]] : []).concat(F.inputs), out = { lock: rr.state, seed: rr.best && rr.best.seed };
        for (const [k, f, turn] of inputs) {
          if (k === 'nothing') { adv(f - 3); const w = X.weigh(f - 3); out.t2 = { doubt: +w.doubt.toFixed(3), n: w.list.length };
            adv(830); T.setStep(T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever')); const pl = X.plan(834); out.plan = pl && { none: pl.none, best: pl.best != null ? +pl.best.toFixed(3) : null, target: pl.target, p: pl.p }; }
          X.input(k, f, turn, SH[k]);
        }
        adv(1573); const w = X.weigh(1573); out.t3 = { doubt: +w.doubt.toFixed(3), n: w.list.length };
        return out;
      }, { cap, c9, F: FIX.fb });
      // the Cloud Nine confirm from the bar: 2 frames before it on T1's clock (frame 0 = the trigger - 16 frames)
      const c9 = Math.round(16 + (FIX.fb.cloudNineBarHide - FIX.fb.trigger) / 33.367 - 2);
      const no = await run(null), yes = await run(c9);
      // the badge and the plan right after the T1 lock (log C): not green on a weak, broad read; a plan or "No edge" at once
      const bd = await p.evaluate(async cap => { const T = window.__tot, X = window.__fb14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
        await T.chgReplay(cap, { fb14: true }); T.st.plan = null; T.st.msg = null; T.makePlan();
        return { badge: T.lockBadgeState(), prior: X.FB14.prior, plan: !!(T.st.plan && T.st.plan.fb14), msg: (T.st.msg || '').slice(0, 60) }; }, cap);
      console.log('4b T1 badge', JSON.stringify(bd));
      check(bd.badge.state !== 'ok' && bd.prior && bd.prior.d > 0.3, '4. after log C\'s T1 lock (2.5x, placements within 10%) the badge is not green (' + bd.badge.state + ', ' + bd.badge.why + '; prior doubt ' + (bd.prior && bd.prior.d) + ')');
      check(bd.plan || /No edge/.test(bd.msg), '4. T1 plans at once or says no edge (' + (bd.plan ? 'plan' : bd.msg) + ')');
      console.log('4b without Cloud Nine', JSON.stringify(no)); console.log('4b with Cloud Nine at ' + c9, JSON.stringify(yes));
      check(no.lock === 'locked' && no.seed === FIX.fb.seed && no.t2.doubt > 0.5, '4. v81 (no Cloud Nine on T1): T2\'s doubt ' + no.t2.doubt + ' as logged (0.66-0.69)');
      check(yes.t2 && yes.t2.doubt < 0.3, '4. with T1\'s Cloud Nine from the bar hide (frame ' + c9 + '): T2\'s doubt ' + (yes.t2 && yes.t2.doubt) + ' (the weak T1 read starts at 44%; the coin brings it down)');
      check(yes.plan && yes.plan.none === 'edge' && yes.plan.best < 0.2, '4. ... and T2 says no edge (best ' + (yes.plan && yes.plan.best) + '): the states agree Bowser hits around the frame pressed (897), as he did');
      check(yes.t3.n === 0 && no.t3.n === 0, '4. after that hit (and the Life Shroom) no state fits T3\'s coin: the carry is gone, as logged');
    }
    const F = readLog(LOGF);
    if (!F) console.log('skip 4c: log F not present');
    else {
      // log F: T1 lock, (Cloud Nine; Bowser hit Mario: Life Shroom), T2 Charge; the T2 read matches none of the carried states.
      // v81 replaced them with a fresh T2 lock and planned at doubt 0.7% (70%, a 10-frame window): Bowser hit again
      const fbs = F.chargeCaptures.filter(c => c.prof === 'fb1'), c1 = fbs[fbs.length - 2], c2 = fbs[fbs.length - 1];   // (log F holds log C's reads too)
      const rf = await p.evaluate(async ({ c1, c2, gap, hide }) => {
        const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
        const t1 = performance.now() - 60000; await T.chgReplay(c1, { fb14: true, t0: t1 });
        const out = { b1: T.lockBadgeState(), n1: FB.states.length };
        const adv = h => FB.states.forEach(S => X.fbRun(S, h - S.l)), fr = t => (t - FB.t0) / FB.rate, c9 = Math.round(fr(t1 + hide) - 2);
        adv(c9 - 3); X.input('cn', c9, 1, [[-2, 0.1], [-1, 0.2], [0, 0.35], [1, 0.25], [2, 0.1]]);
        const M2 = Math.round(fr(t1 + gap) - 16); adv(M2 + 11); X.input('chg', M2, 2, [[-1, 0.25], [0, 0.5], [1, 0.25]]);
        T.setStep(T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever'));
        const s0 = T.SLOG.length; await T.chgReplay(c2, { fb14: true, t0: t1 + gap });
        const L = T.SLOG.slice(s0); out.check = L.find(e => e.ev === 'fb14Check'); out.prior = FB.prior;
        const pl = X.plan(M2 + 240); out.plan = pl && (pl === true ? FB.plan : pl); out.b2 = T.lockBadgeState();
        return out;
      }, { c1, c2, gap: 2617716 - 2588174, hide: 2591818 - 2588174 });
      console.log('4c', JSON.stringify(rf));
      check(rf.b1.state !== 'ok', '4. log F T1 lock (' + rf.n1 + ' states): badge ' + rf.b1.state + ' (' + rf.b1.why + '), not green');
      check(rf.check && rf.check.matched === 0 && rf.prior && rf.prior.contra && rf.prior.d >= 0.5, '4. the T2 read contradicts the carry (matched ' + (rf.check && rf.check.matched) + ' of ' + (rf.check && rf.check.carried) + '): the fresh lock starts at doubt ' + (rf.prior && rf.prior.d));
      check(rf.plan && (rf.plan.none || rf.plan.doubt >= 0.5), '4. no T2 beep plan from it (' + JSON.stringify(rf.plan).slice(0, 120) + '); v81: doubt 0.007, 70%, and Bowser hit');
      check(rf.b2.state !== 'ok', '4. the badge after the T2 lock: ' + rf.b2.state + ' (' + rf.b2.why + ')');
    }
    // the hit: the "1" of 10 HP before the lever, blank after it = Mario was hit (the route is over for this attempt)
    const rh = await p.evaluate(() => {
      const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
      Object.assign(FB, { on: true, t0: performance.now() - 10000, rate: 33.367, states: [{ s: 1, nc: 100, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1, resp: new Uint8Array(64), ev: [], wv: -1e9, prev: null, out: {}, sh: [], lw: 1, err: 0 }] });
      const J = T.JRT; let t = performance.now(), ten = 0.5; window.__jrTensTest = () => ten;
      J.bar.since = t - 1000;
      for (let i = 0; i < 20; i++) { t += 16.7; T.fb14Frame(t, true); }
      FB.pT[1] = t - 3000; ten = 0;
      for (let i = 0; i < 30; i++) { t += 16.7; T.fb14Frame(t, true); }
      window.__jrTensTest = null; T.st.plan = null; T.makePlan();
      return { hit: FB.hit, badge: T.lockBadgeState(), log: T.SLOG.filter(e => e.ev === 'fb14Hit').length, msg: (T.st.msg || '').slice(0, 40) };
    });
    check(rh.hit === 1 && rh.log === 1 && rh.badge.state === 'no' && /No edge/.test(rh.msg), '4. HP 10 then blank after the lever = a hit: no edge for the attempt (' + JSON.stringify(rh) + ')');
    await p.close();
  }
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
