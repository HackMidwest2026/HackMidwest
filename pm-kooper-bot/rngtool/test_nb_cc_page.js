/* v85: the Normal Boots Close Calls on the page (charge_live/README.md v85), through the built standalone page in headless
 * Chromium, against the emulator-checked model (pmrng_core.js TURNS nb_*: test_nb_cc_model.js matched the emulator frame by
 * frame). Per random game (seed and first coin q at a Super Charge's rays, console lag 0) the page's tracker is started as
 * a Charge lock starts it (lag 0 / 1) and fed the route's confirms on their clock frames (as read from the bar), the coin's
 * shines where the bar is up, and the box A from the bar's return:
 *  1. Jr. Troopa: T2 Super Charge lock -> Goombario's Charge confirm: the page plans the box A at once (beeps, in the box
 *     window +73..+132, "Perfect press: works · window N frames · seed confidence NN%"), the game's Close Call with the
 *     A on that frame; T3 Maple Syrup -> Charge from the carry; T4 its own lock; T5 its lock -> the Headbonk; T6 Whacka /
 *     Do Nothing; T7 Power Bounce 5+ from the carry. Every planned press must land (perfect press).
 *  2. Hallway T1: Super Charge lock -> the box A (Bowser's attack choice in the model) -> T2 Time Out from the carry.
 *  3. Wait mode (Settings): the Charge confirm planned instead (the box left to run out): T2-T4.
 *  4. Texts: before the Charge confirm ("Locked: confirm Goombario's Charge ..."), no lock, a death (10 HP: no roll).
 * usage (from rngtool/, after python3 build_page.py): node test_nb_cc_page.js [PAGE]   (env N: games per part, default 25) */
'use strict';
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const N = +process.env.N || 25;
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), p = await b.newPage(), errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { if (!sessionStorage.getItem('nbinit')) { sessionStorage.setItem('nbinit', '1'); localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ boots: 'normal' })); } });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(({ N }) => {
    const T = window.__tot, R = T.R, K = R.NB_K, out = { version: T.VERSION, jr: [], hw: [], wait: [] };
    let rs = 0x9e3779b9; const rnd = n => { rs = (Math.imul(rs, 1103515245) + 12345) >>> 0; return rs % n; };
    out.defaultMode = document.getElementById('s-nbcc').value;
    document.getElementById('s-nbcc').value = 'cancel'; document.getElementById('s-nbcc').dispatchEvent(new Event('change'));
    const stepIdx = (seq, k) => T.RT().findIndex(s => s.seq === seq && s.jr === k);
    // the game (model) and the coin it shows where the bar is up
    function Game(seed, q) { return { S: { s: seed >>> 0, nc: q, inst: [] }, g: 0, ev: [{ f: -13, id: 'jr_charge' }], shines: [] }; }
    const run = (G, to) => { const ev = R.buildEv(G.ev); for (; G.g < to; G.g++) { const x = R.frameEv(G.S, G.g, ev); if (x) G.shines.push(G.g); } };
    const rollAt = (G, f) => { run(G, f); return R.randInt(G.S.s, 100)[1]; };
    const ccAfter = (G) => { const ev = R.buildEv(G.ev); for (let i = 0; i < 400 && !G.S.cc; i++, G.g++) { const x = R.frameEv(G.S, G.g, ev); if (x) G.shines.push(G.g); } return G.S.cc; };
    const coin = (G, off, a, b) => { b -= 6; if (b <= a) return; T.zw.vis.push([a - off, b - off]); for (const f of G.shines) if (f >= a && f <= b) T.zw.taps.push(f - off); };     // a shine drawn in the last 6 frames before the bar hides never flashes
    const plan = () => T.st.plan && T.st.plan.nbK != null ? T.st.plan : null;
    // the game's outcome if the deciding press came d frames off (25/50/25 over -1/0/+1): copies of the game from now
    const cloneG = G => ({ S: { s: G.S.s, nc: G.S.nc, inst: G.S.inst.map(I => ({ rm: I.rm, per: I.per, p: I.p.slice() })), extra: G.S.extra ? new Map(G.S.extra) : undefined }, g: G.g, ev: G.ev.slice(), shines: [] });
    const spread = (G, evAt) => { let v = 0; for (const [d, w] of [[-1, 0.25], [0, 0.5], [1, 0.25]]) { const H = cloneG(G); const r = evAt(H, d); if (r) v += w; } return v; };
    const headline = () => document.body.textContent.match(/Perfect press: works[^.]*?seed confidence \d+%/);
    function cancelTurn(G, off, k, Gf, row, what) {
      G.ev.push({ f: Gf, id: 'nb_gch' }); T.st.plan = null; try { T.jrConfirmClock(k, Gf - off); } catch (e) { throw new Error(what + " k" + k + " seq " + T.JRT.seq + " on " + T.JRT.on + " step " + T.RT()[T.step()].t + ": " + e.message); }
      const P0 = plan(), t = { what, G: Gf };
      if (P0) { t.P = P0.zwAbs + off; t.K = t.P - Gf; t.win = P0.mix.win; t.pp = P0.mix.pp; t.p = P0.mix.p; t.doubt = P0.mix.doubt; t.beeps = P0.beeps; t.head = !!headline(); }
      else t.msg = T.st.msg;
      const P = t.P != null ? t.P : Gf + K.none; t.Pg = P;
      if (t.P != null) t.sp = spread(G, (H, d) => { const Q = Math.min(Gf + K.none, P + d); H.ev.push({ f: Q, id: 'nb_jrcc' }); return rollAt(H, Q + K.jrcc) < 30; });
      G.ev.push({ f: P, id: 'nb_jrcc' }); t.roll = rollAt(G, P + K.jrcc); t.lucky = t.roll < 30;
      T.nbCancelSeenClock(P - off); row.turns.push(t); return t;
    }
    // 1. Jr. Troopa
    for (let n = 0; n < N; n++) {
      const seed = (Math.imul(n + 1, 0x2545F491) ^ 0x6c8e9cf5) >>> 0, q = rnd(48), G = Game(seed, q), row = { seed, turns: [] }; let off = 0;
      T.setStep(stepIdx('nbjr', 1)); T.jrReset(); T.st.plan = null;
      row.started = T.nbTrackerAt(seed, [q], performance.now() + 3600000, 2, 'nbjr');
      T.st.msg = null; T.makePlan(); row.before = T.st.msg;
      const G2 = 200 + rnd(40); run(G, G2); coin(G, off, 160, G2 + 2);
      let t = cancelTurn(G, off, 3, G2, row, 'T2');
      if (t.lucky) {
        T.jrSettle('test');
        const M = t.Pg + K.jrnext + 20 + rnd(40); G.ev.push({ f: M, id: 'nb_syrup' }); run(G, M); coin(G, off, t.Pg + 7, M + 2); T.jrConfirmClock(4, M - off);
        const G3 = M + 165 + rnd(30); run(G, G3); coin(G, off, M + 160, G3 + 2);
        t = cancelTurn(G, off, 5, G3, row, 'T3');
      }
      if (t.lucky) {
        T.jrSettle('test');
        const C4 = t.Pg + K.jrnext + 20 + rnd(40); G.ev.push({ f: C4, id: 'jr_charge' }); run(G, C4); coin(G, off, t.Pg + 7, C4 + 2); T.jrConfirmClock(6, C4 - off);
        run(G, C4 + 13); const lk = T.nbLockAt(G.S.s, [G.S.nc - (C4 + 13)], 6); row.cross4 = lk.cross && lk.cross.agree; off = C4 + 13;
        const G4 = C4 + 175 + rnd(30); run(G, G4); coin(G, off, C4 + 160, G4 + 2);
        t = cancelTurn(G, off, 7, G4, row, 'T4');
      }
      if (t.lucky) {
        T.jrSettle('test');
        const C5 = t.Pg + K.jrnext + 20 + rnd(40); G.ev.push({ f: C5, id: 'jr_charge' }); run(G, C5); coin(G, off, t.Pg + 7, C5 + 2); T.jrConfirmClock(8, C5 - off);
        run(G, C5 + 13); T.nbLockAt(G.S.s, [G.S.nc - (C5 + 13)], 8); off = C5 + 13;
        const cS = C5 + 175 + rnd(30); run(G, cS - 4); coin(G, off, C5 + 160, cS - 4);
        const pl = T.jrPlanAt(cS - off, 1.5, 1, 'jrcc_hb'), h = { what: 'T5 Headbonk', none: pl.none, pp: pl.pp, p: pl.p, win: pl.w && pl.w.length };
        const H = pl.target != null && !pl.none ? pl.target + off : cS + 50;
        if (pl.target != null && !pl.none) h.sp = spread(G, (X, d) => { X.ev.push({ f: H + d, id: 'nb_hb' }); return rollAt(X, H + d + 143) < 30; });
        G.ev.push({ f: H, id: 'nb_hb' }); h.roll = rollAt(G, H + 143); h.lucky = h.roll < 30; h.planned = pl.target != null && !pl.none;
        T.jrConfirmClock(9, H - off); row.turns.push(h); t = h;
        if (h.lucky) {
          T.jrSettle('test');
          const W = H + 210 + 20 + rnd(30); G.ev.push({ f: W, id: 'nb_whacka' }); run(G, W); coin(G, off, H + 115, W + 2); T.jrConfirmClock(10, W - off);
          const D = W + 170 + rnd(30); G.ev.push({ f: D, id: 'jr_nothing_hit' }); run(G, D); coin(G, off, W + 160, D - 4); T.jrConfirmClock(11, D - off);
          const cB = D + 160 + rnd(30); run(G, cB - 4); coin(G, off, D + 100, cB - 4);
          const pb = T.jrPlanAt(cB - off, 1.5, 1, 'jrpb5n'), B = pb.target + off; run(G, B);
          row.pb = { none: pb.none, pp: pb.pp, pp6: pb.pp6, five: R.works(G.S.s, G.S.nc, B, B, R.PROFILES.jrpb5n), six: R.works(G.S.s, G.S.nc, B, B, R.PROFILES.jrpb6n), step: T.RT()[T.step()].t };
        }
      }
      out.jr.push(row);
    }
    // 2. Hallway T1 -> T2 Time Out
    for (let n = 0; n < N; n++) {
      const seed = (Math.imul(n + 7, 0x27d4eb2d) ^ 0x165667b1) >>> 0, q = rnd(48), G = Game(seed, q), row = { seed, turns: [] };
      G.ev[0].id = 'hw_charge'; T.setStep(stepIdx('nbhw', 1)); T.jrReset(); T.st.plan = null;
      row.started = T.nbTrackerAt(seed, [q], performance.now() + 3600000, 0, 'nbhw');
      const G1 = 200 + rnd(40); run(G, G1); coin(G, 0, 160, G1 + 2); G.ev.push({ f: G1, id: 'nb_gch' }); T.st.plan = null; T.jrConfirmClock(1, G1);
      const P0 = plan(), t = { what: 'HW T1' }; if (P0) { t.P = P0.zwAbs; t.K = t.P - G1; t.win = P0.mix.win; t.pp = P0.mix.pp; t.p = P0.mix.p; t.head = !!headline(); } else t.msg = T.st.msg;
      const P = t.P != null ? t.P : G1 + K.none;
      if (t.P != null) t.sp = spread(G, (H, d) => { H.ev.push({ f: Math.min(G1 + K.none, P + d), id: 'nb_hwcc' }); const c = ccAfter(H); return !!(c && c.lucky); });
      G.ev.push({ f: P, id: 'nb_hwcc' }); const cc = ccAfter(G); t.lucky = !!(cc && cc.lucky); t.roll = cc && cc.v;
      T.nbCancelSeenClock(P); row.turns.push(t);
      if (t.lucky) {
        T.jrSettle('test'); row.step2 = T.RT()[T.step()].t;
        const cS = G.g + 140 + rnd(40); run(G, cS - 4); coin(G, 0, P + 100, cS - 4);
        const pl = T.jrPlanAt(cS, 1.5, 1, 'timeout'); run(G, pl.target);
        row.to = { none: pl.none, pp: pl.pp, works: pl.target != null && R.works(G.S.s, G.S.nc, pl.target, pl.target, R.PROFILES.timeout) };
      }
      out.hw.push(row);
    }
    // 3. wait mode: the Charge confirm planned (the box left to run out)
    document.getElementById('s-nbcc').value = 'wait'; document.getElementById('s-nbcc').dispatchEvent(new Event('change'));
    out.waitProf = (T.setStep(stepIdx('nbjr', 3)), T.PROF().id);
    for (let n = 0; n < N; n++) {
      const seed = (Math.imul(n + 3, 0x61C88647) ^ 0x2a2a2a2a) >>> 0, q = rnd(48), G = Game(seed, q), row = { seed, turns: [] }; let off = 0;
      T.setStep(stepIdx('nbjr', 1)); T.jrReset(); T.st.plan = null;
      row.started = T.nbTrackerAt(seed, [q], performance.now() + 3600000, 2, 'nbjr');
      let last = 0;
      for (const [k, pre] of [[3, null], [5, 'nb_syrup'], [7, 'jr_charge']]) {
        let cS;
        if (pre) { const M = last + K.jrnext + 20 + rnd(40); G.ev.push({ f: M, id: pre }); run(G, M); coin(G, off, last + 7, M + 2); T.jrConfirmClock(k - 1, M - off);
          if (pre === 'jr_charge') { run(G, M + 13); T.nbLockAt(G.S.s, [G.S.nc - (M + 13)], k - 1); off = M + 13; }
          cS = M + 175 + rnd(20); }
        else cS = 175 + rnd(20);
        run(G, cS - 4); coin(G, off, cS - 15, cS - 4);
        const pl = T.jrPlanAt(cS - off, 1.5, 1, 'jrcc_gchw'), t = { what: 'T' + (k + 1) / 2 + ' wait', none: pl.none, pp: pl.pp, p: pl.p, win: pl.w && pl.w.length };
        const Gf = pl.target != null && !pl.none ? pl.target + off : cS + 40; t.planned = pl.target != null && !pl.none;
        if (t.planned) t.sp = spread(G, (H, d) => { H.ev.push({ f: Gf + d, id: 'nb_gch' }, { f: Gf + d + K.none, id: 'nb_jrcc' }); return rollAt(H, Gf + d + K.none + K.jrcc) < 30; });
        G.ev.push({ f: Gf, id: 'nb_gch' }, { f: Gf + K.none, id: 'nb_jrcc' }); t.roll = rollAt(G, Gf + K.none + K.jrcc); t.lucky = t.roll < 30;
        T.jrConfirmClock(k, Gf - off); row.turns.push(t); last = Gf + K.none;
        if (!t.lucky) break; T.jrSettle('test');
      }
      out.wait.push(row);
    }
    // wait mode, Hallway T1 (Bowser's attack choice after the box runs out), and the early plan's floor (no target screen needed)
    for (let n = 0; n < Math.ceil(N / 2); n++) {
      const seed = (Math.imul(n + 11, 0x45d9f3b) ^ 0x7feb352d) >>> 0, q = rnd(48), G = Game(seed, q), row = { seed, turns: [] };
      G.ev[0].id = 'hw_charge'; T.setStep(stepIdx('nbhw', 1)); T.jrReset(); T.st.plan = null;
      row.started = T.nbTrackerAt(seed, [q], performance.now() + 3600000, 0, 'nbhw'); row.floor = T.jrPlanFloor();
      const cS = 175 + rnd(20); run(G, cS - 4); coin(G, 0, 160, cS - 4);
      const pl = T.jrPlanAt(cS, 1.5, 1, 'hwcc_gchw'), t = { what: 'HW wait', none: pl.none, pp: pl.pp, p: pl.p, win: pl.w && pl.w.length, planned: pl.target != null && !pl.none };
      const Gf = t.planned ? pl.target : cS + 40;
      if (t.planned) t.sp = spread(G, (H, d) => { H.ev.push({ f: Gf + d, id: 'nb_gch' }, { f: Gf + d + K.none, id: 'nb_hwcc' }); const c = ccAfter(H); return !!(c && c.lucky); });
      G.ev.push({ f: Gf, id: 'nb_gch' }, { f: Gf + K.none, id: 'nb_hwcc' }); const c = ccAfter(G); t.lucky = !!(c && c.lucky);
      row.turns.push(t); out.wait.push(row);
    }
    // 5. the live reads (press A mode): the status bar per picture (jrFrame) hides 4 frames after the Charge confirm and comes
    // back 6 frames after the box A: the page reads G and P from it, plans the box A in between and moves the route on
    document.getElementById('s-nbcc').value = 'cancel'; document.getElementById('s-nbcc').dispatchEvent(new Event('change'));
    out.live = [];
    for (let n = 0; n < 3; n++) {
      const seed = (Math.imul(n + 5, 0x3c6ef372) ^ 0x1b873593) >>> 0, q = rnd(48), row = {};
      T.setStep(stepIdx('nbjr', 1)); T.jrReset(); T.st.plan = null; T.nbTrackerAt(seed, [q], performance.now() + 3600000, 2, 'nbjr');
      T.JRT.bar = {};      // (each game's pictures start afresh)
      const vl = +document.getElementById('s-vlag').value, tOf = f => T.zw.t0 + vl + f * T.zw.rate, Gf = 220 + rnd(30);
      let P = null;
      for (let f = 150; f < 520; f++) {
        if (P == null && T.st.plan && T.st.plan.nbK === 3) { P = T.st.plan.zwAbs; row.planAt = f; }
        if (P == null && f === Gf + 60) { P = Gf + 100; row.blind = T.st.msg; }      // no plan (no edge): the runner closes the box blind
        const present = !(f >= Gf + 4 && (P == null || f < P + 6));
        T.jrFrame(tOf(f), present);
        if (P != null && f > P + 12) break;
      }
      const ins = T.JRT.inputs.filter(x => x.k === 3);
      row.G = Gf; row.P = P; row.cG = (ins.find(x => !x.cancel) || {}).c; row.cP = (ins.find(x => x.cancel) || {}).c; row.src = (ins.find(x => x.cancel) || {}).src; row.step = T.RT()[T.step()].t;
      out.live.push(row);
    }
    document.getElementById('s-nbcc').value = 'wait'; document.getElementById('s-nbcc').dispatchEvent(new Event('change'));
    // 4. texts: no lock; a death (the next turn at 10 HP: no roll)
    T.jrReset(); T.chgReset(); T.setStep(stepIdx('nbjr', 3)); Object.assign(T.CHG, { state: 'nolock', why: 'no clear seed', prof: T.CHG_PROF.jr }); T.st.plan = null; T.st.msg = null; T.makePlan(); out.nolock = T.st.msg;
    T.CHG.state = 'idle'; T.st.msg = null; T.makePlan(); out.noCharge = T.st.msg;
    { const G = Game(0x1234567, 5); T.setStep(stepIdx('nbjr', 1)); T.nbTrackerAt(0x1234567, [5], performance.now() + 3600000, 2, 'nbjr'); T.jrConfirmClock(3, 210); const P = plan() ? plan().zwAbs : 210 + K.none; T.nbCancelSeenClock(P); T.jrDeath(3, 400);
      T.st.plan = null; T.st.msg = null; T.makePlan(); out.death = { msg: T.st.msg, at10: T.jrStepAt10(), step: T.RT()[T.step()].t }; }
    out.panel = (document.getElementById('chg-status') || {}).textContent;
    return out;
  }, { N });
  console.log('version ' + r.version);
  check(r.version === 'v86', 'version v86');
  const agg = {}; const add = (k, t, planned) => { const A = agg[k] = agg[k] || { n: 0, planned: 0, landed: 0, win: 0, pp: 0, p: 0, sp: 0, inWin: 0, head: 0, conf: 0 }; A.n++; if (!planned) return;
    A.planned++; if (t.lucky) A.landed++; else if ((t.pp || 0) >= 0.95) A.conf++; A.win += t.win || 0; A.pp += t.pp || 0; A.p += t.p || 0; A.sp += t.sp || 0; if (t.K == null || (t.K >= 73 && t.K <= 132)) A.inWin++; if (t.head || t.head === undefined) A.head++; };
  for (const row of r.jr) { check(row.started, 'jr ' + row.seed.toString(16) + ': tracker started'); for (const t of row.turns) add(t.what.split(' ')[0] === 'T5' ? 'Jr T5 Headbonk' : 'Jr ' + t.what + ' box A', t, t.P != null || t.planned); }
  for (const row of r.hw) { check(row.started, 'hw ' + row.seed.toString(16) + ': tracker started'); for (const t of row.turns) add('Hallway T1 box A', t, t.P != null); }
  for (const row of r.wait) for (const t of row.turns) add('wait ' + t.what.split(' ')[0], t, t.planned);
  console.log(JSON.stringify(r.jr[0]).slice(0, 500));
  const pc = x => (100 * x).toFixed(1) + '%';
  for (const [k, A] of Object.entries(agg)) {
    const m = A.planned || 1;
    console.log(k + ': ' + A.n + ' games, planned ' + A.planned + '; perfect press on the beeped frame landed ' + A.landed + ' (' + pc(A.landed / m) + '), claimed ' + pc(A.pp / m) + '; with the 25/50/25 press spread: actual ' + pc(A.sp / m) + ', claimed ' + pc(A.p / m) + '; mean window ' + (A.win / m).toFixed(1) + ' frames');
    check(A.planned >= 0.9 * A.n, k + ': planned in at least 90% of the games');
    check(A.landed / m >= A.pp / m - 0.08, k + ': the perfect press lands about as often as claimed');
    check(A.conf === 0, k + ': no confident wrong beep (every miss was claimed under 95%)');
    check(A.inWin === A.planned, k + ': the box A always inside +73..+132');
    if (/box A/.test(k)) check(A.head === A.planned, k + ': the strip says "Perfect press: works · window N frames · seed confidence NN%"');
  }
  const jr2 = r.jr.filter(x => x.turns[0] && x.turns[0].P != null); check(jr2.every(x => x.turns[0].beeps >= 1), 'beeps scheduled for the box A');
  check(r.jr.every(x => /Locked: confirm Goombario/.test(x.before || '')), 'before the Charge confirm: "Locked: confirm Goombario\'s Charge ..."');
  const c4 = r.jr.filter(x => x.cross4 != null); check(c4.length && c4.every(x => x.cross4), 'T4 locks agree with the carry (' + c4.length + ')');
  const pb = r.jr.filter(x => x.pb); console.log('T7 Power Bounce from the carry: ' + pb.length + ' games, 5+ ' + pb.filter(x => x.pb.five).length + ', 6+ ' + pb.filter(x => x.pb.six).length + ' (step ' + (pb[0] || { pb: {} }).pb.step + ')');
  check(pb.length >= 0.8 * r.jr.length && pb.every(x => x.pb.five), 'T7 Power Bounce 5+ from the carry on every planned game');
  const to = r.hw.filter(x => x.to); console.log('Hallway T2 Time Out from the carry: ' + to.length + ' games, works ' + to.filter(x => x.to.works).length + ' (step ' + (r.hw.find(x => x.step2) || {}).step2 + ')');
  check(to.length && to.every(x => x.to.works), 'Hallway T2 Time Out from the T1 carry: every planned press works');
  console.log('live reads: ' + JSON.stringify(r.live));
  check(r.live.every(x => x.P != null && x.cG === x.G && x.cP === x.P && x.src === 'bar' && /T3$/.test(x.step) && (x.blind || x.planAt <= x.G + 14)), 'live: the Charge confirm read from the bar hiding (hide 4), the plan made at once, the box A read from the bar\'s return (P + 6), the route on to T3');
  check(r.defaultMode === 'wait', 'default: wait it out (the higher perfect-press chance)');
  check(r.wait.filter(x => x.floor !== undefined).every(x => x.floor != null), 'wait mode: the early plan has its floor right after the Super Charge (no target screen needed)');
  check(r.waitProf === 'jrcc_gchw', 'wait mode: the step plans the Charge confirm (jrcc_gchw)');
  console.log('no lock: ' + r.nolock + '\nno Charge: ' + r.noCharge + '\ndeath: ' + JSON.stringify(r.death));
  check(/No Charge lock/.test(r.nolock) && /(confirm Goombario's Charge whenever you like and leave his box|close Goombario's box whenever you like): Close Call about 30%/i.test(r.nolock), 'no lock: play it blind (30%)');
  check(/did not read a Super Charge/.test(r.noCharge), 'no Charge read: says so');
  check(r.death.at10 && /No roll this turn/.test(r.death.msg || ''), 'after a death (10 HP): no roll, no beep');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  console.log(fails ? fails + ' FAILED' : 'all ok'); await b.close(); process.exit(fails ? 1 : 0);
})();
