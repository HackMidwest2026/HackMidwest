/* v86: Final Bowser T1-T4 on the page, the console logs of 2026-11-08 (1794169517521 = log C, its fight 1; Time Out Timer
 * v81) replayed through this build:
 *  1. the hit watch follows the lever just confirmed: the route moves to the next turn's step at the confirm, so v82-v85
 *     watched the next turn and never saw the hit (HP 10 then blank 2-25 s after the confirm) on the turn just played;
 *  2. the miss: 10 HP steady on the bar through Bowser's turn and no hit by the next turn's own action = Bowser missed; the
 *     states that had him hit are weighed down (FB14_MISSW) from then on;
 *  3. log C fight 1 (T1: Bowser's fire breath missed, clip 15-24-14): the T2 states with that miss read agree on most
 *     frames (the shares near 0 or 1), where without it they did not;
 *  4. the Settings choice of Bowser's HP (the Recover check): 'hi' one state per fit, 'any' both.
 * usage: node test_fb14_v86.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const LOGC = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887/26031105-pm-rng-log-1794169517521.json';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1108b.json'), 'utf8')).fb;
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); fs.createReadStream(PAGE).pipe(r); });
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const url = 'http://127.0.0.1:' + srv.address().port + '/';
  const b = await chromium.launch(), errs = [];
  const open = async fbhp => { const p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
    await p.addInitScript(h => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50', fbhp: h })); } catch (e) {} }, fbhp || 'hi');
    await p.goto(url); return p; };
  const p = await open();
  // ---- 1 and 2: the HP watch
  const watch = async (blankAfter) => p.evaluate(blank => {
    const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset();
    const l1 = T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'), l2 = T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever');
    T.setStep(l1);
    Object.assign(FB, { on: true, t0: performance.now() - 10000, rate: 33.367, states: [X.fbNew({ s: 1, nc: 1e9, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1 })] });
    let t = performance.now(), ten = 0.5; window.__jrTensTest = () => ten; T.JRT.bar.since = t - 1000;
    for (let i = 0; i < 20; i++) { t += 33.4; X.hpWatch(t, true); }         // T1's menus: 10 HP on the bar
    FB.pT[1] = t; T.setStep(l2);                                              // the Cloud Nine confirm; the route moves on (as live)
    for (let i = 0; i < 300; i++) { t += 33.4; if (blank && i > 100) ten = 0; X.hpWatch(t, true); }   // Bowser's turn (a hit at ~3.4 s)
    X.turnOver(2);
    window.__jrTensTest = null;
    return { hit: FB.hit, missed: FB.missed, log: T.SLOG.filter(e => /^fb14(Hit|Missed|MissUnread)$/.test(e.ev)).slice(-2).map(e => e.ev) };
  }, blankAfter);
  const h = await watch(true), m = await watch(false);
  check(h.hit === 1, '1. a hit on T1 is read after the route moved to T2\'s step (v82-v85 watched T2 instead: none read) ' + JSON.stringify(h));
  check(!m.hit && m.missed && m.missed[1] === true, '2. 10 HP through Bowser\'s T1 turn, T2 begins: T1 read as a miss ' + JSON.stringify(m));
  // ---- 3. log C fight 1
  if (!fs.existsSync(LOGC)) console.log('skip 3: log C not present');
  else {
    const C = JSON.parse(fs.readFileSync(LOGC, 'utf8')), cap = C.chargeCaptures.find(c => c.prof === 'fb1');
    const c9 = Math.round(16 + (FIX.cloudNineBarHide - FIX.trigger) / 33.367 - 2);
    const run = async miss => p.evaluate(async ({ cap, c9, F, miss }) => {
      const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
      const rr = await T.chgReplay(cap, { fb14: true }); if (rr.state !== 'locked') return { lock: rr.state };
      const tt = f => FB.t0 + f * FB.rate, adv = h => FB.states.forEach(S => X.fbRun(S, h - S.l));
      FB.taps = F.taps.map(f => tt(f + 4.8)); FB.vis = F.vis.map(([a, b]) => [tt(a - 30), tt(b + 4)]); FB.visFrom = null;
      adv(c9 - 3); X.input('cn', c9, 1, [[-2, 0.1], [-1, 0.2], [0, 0.35], [1, 0.25], [2, 0.1]]);
      adv(611); X.input('chg', 613, 2, [[-1, 0.25], [0, 0.5], [1, 0.25]]);
      if (miss) FB.missed = { 1: true };
      T.setStep(T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever'));
      const sh = X.share(830, 860, 930, 2), w = X.weigh(830); let tot = 0, fm = 0; for (const S of w.list) { tot += S.w * S.lw; if (S.out[1] && S.out[1].miss) fm += S.w * S.lw; }
      const sure = sh.share.filter(x => x >= 0.9 || x <= 0.1).length / sh.share.length;
      return { seed: rr.best.seed, doubt: +w.doubt.toFixed(3), fireMiss: +(fm / tot).toFixed(3), sure: +sure.toFixed(3), top: +Math.max(...sh.share).toFixed(3), at897: +sh.share[37].toFixed(3) };
    }, { cap, c9, F: FIX, miss });
    const a = await run(false), bb = await run(true);
    console.log('3 without the miss read', JSON.stringify(a)); console.log('3 with it', JSON.stringify(bb));
    check(a.seed === FIX.seed && a.fireMiss < 0.5, '3. T1 lock ' + a.seed + '; without the miss read ' + Math.round(100 * a.fireMiss) + '% of the weight has Bowser missing T1 (what happened: his fire breath missed)');
    check(bb.fireMiss > 0.97 && bb.sure > 2 * a.sure && bb.sure >= 0.55, '3. with it ' + Math.round(100 * bb.fireMiss) + '%, and T2 frames 860-930 where the states agree (90%+ either way): ' + Math.round(100 * bb.sure) + '% (without: ' + Math.round(100 * a.sure) + '%)');
    check(bb.doubt < 0.4, '3. the seed confidence stays above the no-beep line (doubt ' + bb.doubt + ', without ' + a.doubt + ': the lock had the miss at 37% against 50% blind, slightly against it)');
  }
  // ---- 6. the T1 Super Charge's own bar hide on the Cloud Nine step (the route moved there when its target screen closed,
  // before the burst) is not Cloud Nine's confirm (end-to-end run 1234abcd: v85 took it, every state dropped)
  const c9 = await p.evaluate(() => {
    const T = window.__tot, X = window.__fb14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever'));
    const s0 = T.SLOG.length; let t = performance.now();
    for (let i = 0; i < 60; i++) { t += 16.7; T.fb14Frame(t, true); } for (let i = 0; i < 24; i++) { t += 16.7; T.fb14Frame(t, false); }
    const before = T.SLOG.slice(s0).filter(e => e.ev === 'fb14CloudNineByBar').length;
    X.FB14.lastBurst = { turn: 1, t: t - 3000 };                 // the burst came; the partner menu, then Cloud Nine
    for (let i = 0; i < 60; i++) { t += 16.7; T.fb14Frame(t, true); } for (let i = 0; i < 24; i++) { t += 16.7; T.fb14Frame(t, false); }
    return { before, after: T.SLOG.slice(s0).filter(e => e.ev === 'fb14CloudNineByBar').length };
  });
  check(c9.before === 0 && c9.after === 1, '6. a bar hide on the Cloud Nine step before the T1 Charge\'s burst is not Cloud Nine; one 3 s after it is ' + JSON.stringify(c9));
  // ---- 7. the first Charge burst of an attempt is T1's, whatever step early screen matches moved the route to (clip 15-24-14
  // fed to the page: the route was on T2's Do Nothing step at T1's Charge; the lock went to T2 and T2's Charge to T4)
  const t1 = await p.evaluate(() => {
    const T = window.__tot, X = window.__fb14; X.reset(); const l2 = T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever'), l1 = T.RT().findIndex(s => s.fb14 === 1 && s.fb14role === 'lever');
    T.setStep(l2); X.FB14.pend = [{ tObs: performance.now() - 3000, turn: 1, cat: 'M' }]; X.FB14.pT = { 1: performance.now() - 3000 };
    const saved = T.CHG.trig; T.CHG.trig = { t: performance.now() }; X.trigger(); const a = { step: T.step(), l1, pend: X.FB14.pend.length, trigTurn: X.FB14.trigTurn };
    T.setStep(l2); X.FB14.lastBurst = { turn: 1, t: performance.now() - 20000 }; X.FB14.t0 = performance.now() - 20000; X.FB14.on = true; X.trigger(); a.second = T.step(); a.l2 = l2; T.CHG.trig = saved; return a;
  });
  check(t1.step === t1.l1 && t1.pend === 0 && t1.trigTurn === 1, '7. the first burst with no lock goes to T1 (Cloud Nine\'s step), the confirms read before it dropped ' + JSON.stringify(t1));
  check(t1.second === t1.l2, '7. a later burst on T2\'s step stays T2\'s');
  // ---- 8. a Charge whose rays are still being captured: no state runs past it and no plan is made (end-to-end run
  // 1234abcd T2: the plan ran the states to 1141, the Charge on 1000 then found none, "No edge" for T2)
  const pc = await p.evaluate(() => {
    const T = window.__tot, X = window.__fb14, FB = X.FB14; X.reset(); T.setStep(T.RT().findIndex(s => s.fb14 === 2 && s.fb14role === 'lever'));
    Object.assign(FB, { on: true, t0: performance.now() - 1150 * 33.367, rate: 33.367, states: [X.fbNew({ s: 7, nc: 1e9, f: 900, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1 })], pendChg: { M: 1000, turn: 2 }, M: { 2: 1000 } });
    X.advance(1141); const f = FB.states[0].f; T.st.plan = null; X.plan(); const pl = X.FB14.plan;
    FB.pendChg = null; X.input('chg', 1000, 2, [[0, 1]]); return { f, plan: pl && pl.none, n: FB.states.length };
  });
  check(pc.f === 1010 && pc.plan === 'reading' && pc.n === 1, '8. a pending Charge on 1000: the states stop at 1010 (v87: its frame -2 .. +2), no plan ("reading"), and the Charge then goes into them ' + JSON.stringify(pc));
  // ---- 5. the lever press bias: both console lever presses 2.2-2.5 frames early; the beeps come that much later
  const pb = await p.evaluate(() => { const X = window.__fb14, FB = X.FB14; X.reset(); FB.t0 = 1000; FB.rate = 33.367;
    const b0 = X.bias(), t0 = X.pressT(900); X.pressAdd(-2.4); X.pressAdd(-2.4); const b1 = X.bias(); for (let i = 0; i < 8; i++) X.pressAdd(0.1); const b2 = X.bias(); localStorage.removeItem('tot-fb14press');
    return { b0, t0, b1, b2, v85: 1000 + (900 - 1.7 + (+document.getElementById('s-off').value)) * 33.367 - (+document.getElementById('s-vlag').value) }; });
  check(Math.abs(pb.b0 - 2.37) < 0.01 && Math.abs((pb.t0 - pb.v85) / 33.367 - 2.37) < 0.01, '5. the lever beep for a frame comes 2.37 frames later than v85\'s (the two logged presses: -2.54, -2.2) ' + JSON.stringify(pb));
  check(Math.abs(pb.b1 - 2.385) < 0.01 && Math.abs(pb.b2 + 0.1) < 0.01, '5. it follows the last 8 lever presses (' + pb.b1 + ', then ' + pb.b2 + ')');
  await p.close();
  // ---- 4. the Recover setting
  for (const [hp, want] of [['hi', [0]], ['lo', [1]], ['any', [0, 1]]]) {
    const q = await open(hp);
    const r = await q.evaluate(() => { const X = window.__fb14; return document.getElementById('s-fbhp').value; });
    check(r === hp, '4. Settings: Bowser\'s HP ' + hp + ' kept'); await q.close();
  }
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
