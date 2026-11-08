/* Jr. Troopa, Charge-lock route (v73): the page's tracker and plans against the emulator-checked model, through the built
 * standalone page in headless Chromium.
 *  1. Route: the endgame route's Jr. Troopa steps (T1 .. T6, the jr Charge profile on each), the page moving the route by
 *     the confirm count (jrConfirm), the step after T6 = Hallway T1.
 *  2. Model (the lock's clock is put an hour ahead, so the page's own ticks never step the tracker past the confirms
 *     the test feeds; live, each confirm reaches the tracker ~10 frames after it, before any of its draws): jr_charge/plan_cases.json (jc_fixture.py, from jc_model.py: jc_check_core.js matched 64/64 emulator Charge
 *     segments frame by frame). Per case the page's tracker is started as a Charge lock starts it (seed and first coin q at
 *     the rays' frame 0, console lag 0 / 1) and fed the route's confirms on their clock frames (each -2..+1, as read from the
 *     bar); at each lever (T3 Bomb, T4 Maple Syrup, T5 Do Nothing, T6 Power Bounce) on the frame 46 before its window:
 *       - the true state must be among the page's states, and its outcome on every frame of the 190-frame window must equal
 *         the model's (Close Call; Power Bounce 6+ / 5 / fewer);
 *       - the plan (lead 1.5 s, 1 s max extra wait, best chance) is scored with the model's outcomes, the press 1 frame early
 *         25%, on time 50%, late 25%, against the page's own claim and the blind odds (Close Call 30%, 5+ 67.5%, 6+ 32.2%).
 *     Modes: carry (the T1 lock carried through every turn, no coin seen), coin (the same with the menus' coin: every shine
 *     where the bar is up), own (each Charge's own lock: T3's for T3 / T4, T5's for T5 / T6), lock (the carry, and the
 *     T3 / T5 locks landing on it: each must agree with the carry, and the page goes on from it).
 *  3. A death (jrDeath, as the HP read sees it): the tracker stops, the next turn says no roll (10 HP), the T5 lock with a
 *     T4 death plans T6 through Do Nothing at 10 HP; a dodge drops the states that would have died.
 *  4. No lock: Plan press and the strip say play it blind with the blind odds.
 *  5. Arena (chgArena) on console frames of the other fights (every 6th frame of a Hallway clip, the FB2 clip and the
 *     Duplighost clip, when here): never Jr. Troopa.
 * usage (from rngtool/, after python3 build_page.py): node test_jr_plan.js [PAGE] */
'use strict';
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'jr_charge', 'plan_cases.json'), 'utf8'));
const U = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887/';
const CLIPS = [['63e6e3da-2026-11-02_15-15-06.mkv', 0, 1500], ['70665d2d-2026-11-03_20-53-09.mkv', 0, 1500], ['6c9e1375-2026-11-02_14-47-09.mkv', 0, 1500], ['aad978a3-2026-11-02_14-44-21.mkv', 0, 1500]];
function clipFrames() {
  const out = [];
  for (const [clip, a, b] of CLIPS) {
    if (!fs.existsSync(U + clip)) { console.log('(no clip ' + clip + ')'); continue; }
    const buf = execFileSync('ffmpeg', ['-v', 'error', '-i', U + clip, '-vf', 'select=between(n\\,' + a + '\\,' + b + ')*not(mod(n\\,6)),scale=160:90', '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], { maxBuffer: 1 << 30 });
    const n = buf.length / (160 * 90 * 3);
    for (let i = 0; i < n; i++) out.push([clip.slice(0, 8), buf.subarray(i * 160 * 90 * 3, (i + 1) * 160 * 90 * 3).toString('base64')]);
  }
  return out;
}
(async () => {
  let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
  const b = await chromium.launch(), p = await b.newPage(), errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { localStorage.clear(); });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(async ({ FIX }) => {
    const T = window.__tot, out = { version: T.VERSION };
    const K = { 'T1 Charge': 0, 'T1 Bomb': 1, 'T2 Bomb': 2, 'T2 Whacka': 3, 'T3 Charge': 4, 'T3 Bomb': 5, 'T4 Bomb': 6, 'T4 Syrup': 7, 'T5 Charge': 8, 'T5 Nothing': 9, 'T6 Bounce': 10 };
    const NAMES = Object.keys(K), LEV = [['T3 Bomb', 'jrcc_bomb'], ['T4 Syrup', 'jrcc_syrup'], ['T5 Nothing', 'jrcc_nothing'], ['T6 Bounce', 'jrpb5']];
    // 1. route
    const jrSteps = T.RT().map((s, i) => [i, s]).filter(x => x[1].jr != null);
    out.route = { steps: jrSteps.map(x => x[1].t + ':' + x[1].jr + ':' + (x[1].chg || '')), after: (T.RT()[T.jrStepFor(11)] || {}).t };
    // 2. model
    const res = [];
    for (const c of FIX.cases) for (const mode of ['carry', 'coin', 'own', 'lock']) {
      let off = 0, applied = -1, taps = 0, visEnd = null; const row = { mode, lev: [] };
      const start = (lock, k) => { off = c.confirms[NAMES[k]]; applied = k; taps = 0; visEnd = null; T.setStep(T.jrStepFor(k));
        return T.jrTrackerAt(parseInt(c.locks[lock].seed, 16), [c.locks[lock].q], performance.now() + 3600000, k); };
      if (mode !== 'own') row.started = start('T1', 0);
      for (const [lev, pid] of LEV) {
        const k = K[lev];
        if (mode === 'own' && (lev === 'T3 Bomb' || lev === 'T5 Nothing')) row.started = start(lev === 'T3 Bomb' ? 'T3' : 'T5', lev === 'T3 Bomb' ? 4 : 8);
        for (const nm of NAMES) { const kk = K[nm]; if (kk > applied && kk < k) { T.jrConfirmClock(kk, c.confirms[nm] - 13 - off);
          applied = kk;
          // lock: the T3 / T5 Charge's own lock lands and is checked against the carry (the new clock: its frame 0)
          if (mode === 'lock' && (kk === 4 || kk === 8)) { const lr = T.jrLockAt(parseInt(c.locks[kk === 4 ? 'T3' : 'T5'].seed, 16), [c.locks[kk === 4 ? 'T3' : 'T5'].q], kk); off = c.confirms[nm]; (row.cross = row.cross || []).push(lr.cross && lr.cross.agree); } } }
        T.jrSettle('test');           // the last Close Call dodged (the route's lever was on a dodge frame)
        const W = c.wins[lev], a = W.from - 13 - off, cScr = a - 46;
        if (mode === 'coin') {       // the coin up where the bar is up (hidden from each action's confirm +3 to +142, Do Nothing hides nothing)
          const hides = NAMES.filter(nm => c.confirms[nm] != null && nm !== 'T5 Nothing').map(nm => c.confirms[nm] - 13 - off);
          const lo = visEnd == null ? 0 : visEnd + 1; let f0 = lo;
          for (const h of hides.filter(h => h + 142 >= lo && h + 3 <= cScr).sort((x, y) => x - y)) { if (h + 3 > f0) T.zw.vis.push([f0, h + 2]); f0 = Math.max(f0, h + 143); }
          if (cScr - 4 > f0) T.zw.vis.push([f0, cScr - 4]); visEnd = cScr - 4;
          const sh = c.shines.map(f => f - 13 - off).filter(f => f > (row.lastTap != null ? row.lastTap : -1e9) && f <= cScr - 6 && T.zw.vis.some(([x, y]) => f >= x && f <= y));
          for (const f of sh) T.zw.taps.push(f); if (sh.length) row.lastTap = sh[sh.length - 1]; taps += sh.length;
        }
        T.setStep(T.jrStepFor(k));
        const pl = T.jrPlanAt(cScr, 1.5, 1, pid), S = pl.states || [], tot = S.reduce((x, q) => x + q.w, 0) || 1;
        const tr = W.state, ti = S.findIndex(q => q.s === parseInt(tr.s, 16) && q.nc === tr.nc - 13 - off && q.g === tr.F - 13 - off);
        const cls = ti >= 0 ? T.jrClasses(S[ti].s, S[ti].nc, S[ti].g, a, a + W.cls.length - 1, pid).join('') : null;
        row.lev.push({ lev, pid, a, target: pl.target, p: pl.p, p6: pl.p6, none: pl.none, states: S.length, trueIdx: ti, trueW: ti >= 0 ? +(S[ti].w / tot).toFixed(3) : 0, cls, taps, doubt: pl.doubt });
      }
      res.push(row);
    }
    out.model = res;
    // 3. a death and a dodge
    const c0 = FIX.cases[0];
    T.jrTrackerAt(parseInt(c0.locks.T1.seed, 16), [c0.locks.T1.q], performance.now() + 3600000, 0);
    for (const nm of NAMES.slice(1, 6)) T.jrConfirmClock(K[nm], c0.confirms[nm] - 13);
    const before = T.zw.parts.length; T.jrDeath(5, 600);
    T.setStep(T.jrStepFor(6)); T.jrConfirmClock(6, c0.confirms['T4 Bomb'] - 13); T.st.plan = null; T.st.msg = null; T.makePlan();
    out.death = { trackerOff: !T.zw.on, at10: T.jrStepAt10(), step: T.RT()[T.step()].t, msg: T.st.msg, before, syrupId: T.JRT.inputs.filter(x => x.k === 7).map(x => x.id) };
    T.jrConfirmClock(7, c0.confirms['T4 Syrup'] - 13);
    out.death.syrupId = T.JRT.inputs.filter(x => x.k === 7).map(x => x.id);
    // T4 death -> the T5 lock: Do Nothing at 10 HP (no roll) and T6 planned through it
    const ok5 = T.jrTrackerAt(parseInt(c0.locks.T5.seed, 16), [c0.locks.T5.q], performance.now() + 3600000, 8, { 9: true });
    T.setStep(T.jrStepFor(9)); T.st.plan = null; T.st.msg = null; T.makePlan(); const msg9 = T.st.msg;
    T.jrConfirmClock(9, c0.confirms['T5 Nothing'] - 13 - c0.confirms['T5 Charge']);
    out.death4 = { ok5, msg9, nothingId: T.JRT.inputs.filter(x => x.k === 9).map(x => x.id), step: T.RT()[T.step()].t };
    // a T3 lock that does not fit the carry (another seed): the page starts again from it
    T.jrTrackerAt(parseInt(c0.locks.T1.seed, 16), [c0.locks.T1.q], performance.now() + 3600000, 0);
    for (const nm of NAMES.slice(1, 5)) T.jrConfirmClock(K[nm], c0.confirms[nm] - 13);
    const lw = T.jrLockAt(0x12345678, [c0.locks.T3.q], 4);
    out.wrongLock = { agree: lw.cross && lw.cross.agree, on: T.zw.on, origin: T.JRT.origin, states: T.jrStatesAt(c0.confirms['T3 Charge'] + 13 + 60 - c0.confirms['T3 Charge'] - 13 + 13).length };
    // the right seed with none of the kept first-coin frames right (a late coin): agrees, and the carry's q is taken
    T.jrTrackerAt(parseInt(c0.locks.T1.seed, 16), [c0.locks.T1.q], performance.now() + 3600000, 0);
    for (const nm of NAMES.slice(1, 5)) T.jrConfirmClock(K[nm], c0.confirms[nm] - 13);
    const lq = T.jrLockAt(parseInt(c0.locks.T3.seed, 16), [(c0.locks.T3.q + 7) % 48], 4);
    out.lateQ = { agree: lq.cross && lq.cross.agree, origin: T.JRT.origin, qs: [...new Set(T.zw.parts.map(p => p.S.nc))], want: c0.locks.T3.q };
    // 4. no lock
    T.jrReset(); T.chgReset(); T.setStep(T.jrStepFor(5)); Object.assign(T.CHG, { state: 'nolock', why: 'no clear seed (best 1500, 1.05x the next)', prof: T.CHG_PROF.jr }); T.st.plan = null; T.st.msg = null; T.makePlan();
    out.nolock = { msg: T.st.msg, panel: document.getElementById('chg-status').innerText };
    T.setStep(T.jrStepFor(10)); T.st.msg = null; T.makePlan(); out.nolock6 = T.st.msg;
    T.CHG.state = 'idle'; T.st.msg = null; T.setStep(T.jrStepFor(5)); T.makePlan(); out.noCharge = T.st.msg;
    return out;
  }, { FIX });
  console.log('version ' + r.version + ' | Jr. steps ' + r.route.steps.join(', ') + ' | after T6: ' + r.route.after);
  check(r.version === 'v78', 'version v78');
  check(r.route.steps.length === 6 && r.route.steps.every(s => /:jr$/.test(s)), 'six Jr. Troopa steps with the jr Charge profile');
  check(/^Hallway Bowser/.test(r.route.after || ''), 'the step after T6 is Hallway T1');
  // 2. per mode and lever
  const agg = {};
  r.model.forEach((row, i) => {
    const c = FIX.cases[Math.floor(i / 4)];
    if (row.mode === 'lock') { const n = (row.cross || []).length, ok = (row.cross || []).filter(Boolean).length; agg.crossN = (agg.crossN || 0) + n; agg.crossOk = (agg.crossOk || 0) + ok; }
    if (!row.started) { check(false, 'case ' + Math.floor(i / 4) + ' ' + row.mode + ': tracker not started'); return; }
    row.lev.forEach(L => {
      const A = agg[row.mode + ' ' + L.lev] = agg[row.mode + ' ' + L.lev] || { n: 0, found: 0, exact: 0, frames: 0, real: 0, real6: 0, claim: 0, claim6: 0, plans: 0, trueW: 0, states: 0, wait: 0, taps: 0, bad: [] };
      const W = c.wins[L.lev], norm = ch => (L.pid === 'jrpb5' ? (ch >= '6' ? '6' : ch === '5' ? '5' : '4') : ch);
      A.n++; A.states += L.states; A.taps += L.taps;
      if (L.trueIdx >= 0) { A.found++; A.trueW += L.trueW; let e = 0; for (let j = 0; j < W.cls.length; j++) if (norm(W.cls[j]) === L.cls[j]) e++; A.frames += W.cls.length; A.exact += e; if (e < W.cls.length && A.bad.length < 3) A.bad.push('case ' + Math.floor(i / 4) + ': ' + e + '/' + W.cls.length); }
      else if (A.bad.length < 3) A.bad.push('case ' + Math.floor(i / 4) + ': true state not among ' + L.states);
      if (L.target == null) { if (A.bad.length < 3) A.bad.push('case ' + Math.floor(i / 4) + ': no plan (' + L.none + ')'); return; }
      let p = 0, p6 = 0; for (const [d, q] of [[-1, 0.25], [0, 0.5], [1, 0.25]]) { const v = norm(W.cls[L.target + d - L.a]); if (L.pid === 'jrpb5' ? v >= '5' : v === '1') p += q; if (v === '6') p6 += q; }
      A.plans++; A.real += p; A.real6 += p6; A.claim += L.p; A.claim6 += L.p6 || 0; A.wait += L.target - (L.a);
    });
  });
  console.log('lock mode: the T3 / T5 locks agreed with the carry in ' + agg.crossOk + ' of ' + agg.crossN);
  check(agg.crossOk === agg.crossN && agg.crossN === 2 * FIX.cases.length, 'every T3 / T5 lock agrees with the carry');
  delete agg.crossN; delete agg.crossOk;
  for (const k of Object.keys(agg)) {
    const A = agg[k], six = /Bounce/.test(k);
    console.log(k.padEnd(18) + ' true state found ' + A.found + '/' + A.n + ' (mean share ' + (A.trueW / Math.max(1, A.found)).toFixed(2) + ', ' + (A.states / A.n).toFixed(1) + ' states' + (A.taps ? ', ' + (A.taps / A.n).toFixed(1) + ' shines' : '') + ') | outcomes ' + A.exact + '/' + A.frames +
      ' frames = model | plans ' + A.plans + ': ' + (six ? '5+ ' : 'Close Call ') + (100 * A.real / A.plans).toFixed(1) + '%' + (six ? ', 6+ ' + (100 * A.real6 / A.plans).toFixed(1) + '%' : '') + ' (page claimed ' + (100 * A.claim / A.plans).toFixed(1) + '%' + (six ? ' / ' + (100 * A.claim6 / A.plans).toFixed(1) + '%' : '') + '; blind ' + (six ? '67.5% / 32.2%' : '30%') + ') | wait into the window ' + (A.wait / A.plans).toFixed(1) + ' frames');
    A.bad.forEach(x => console.log('    ' + x));
    check(A.found === A.n && A.exact === A.frames, k + ': the true state is tracked and its outcomes equal the model on every frame');
    check(A.plans === A.n, k + ': a plan in every case');
    if (six) check(A.real / A.plans >= 0.95 && A.real6 / A.plans >= (/^coin/.test(k) ? 0.6 : 0.45), k + ': 5+ at least 95%, 6+ well above blind');
    else check(A.real / A.plans >= (/^coin/.test(k) ? 0.7 : 0.5), k + ': Close Call well above blind 30%');
    check(Math.abs(A.real - A.claim) / A.plans < 0.15, k + ': the claimed chance within 15 points of the model');
  }
  // 3. death
  console.log('death at T3: ' + JSON.stringify(r.death).slice(0, 300));
  check(r.death.trackerOff && r.death.at10 && /No roll this turn/.test(r.death.msg || ''), 'a T3 death: tracker off, T4 says no roll (10 HP)');
  check(r.death.syrupId.join() === 'jr_syrup_hit', 'the T4 Syrup after a T3 death is the 10-HP Syrup');
  console.log('death at T4 -> T5 lock: ' + JSON.stringify(r.death4).slice(0, 300));
  check(r.death4.ok5 && /No roll this turn/.test(r.death4.msg9 || '') && r.death4.nothingId.join() === 'jr_nothing_hit' && /T6/.test(r.death4.step), 'a T4 death: the T5 lock, Do Nothing at 10 HP (no roll), on to T6');
  console.log('a wrong T3 lock: ' + JSON.stringify(r.wrongLock));
  check(r.wrongLock.agree === false && r.wrongLock.on && r.wrongLock.origin === 4, 'a T3 lock that does not fit the carry: the page starts again from it');
  console.log('the right T3 seed, a wrong q: ' + JSON.stringify(r.lateQ));
  check(r.lateQ.agree && r.lateQ.origin === 4 && r.lateQ.qs.includes(r.lateQ.want), 'a T3 lock with the right seed and a wrong q: agrees, the carry\'s q kept');
  // 4. no lock
  console.log('no lock: ' + r.nolock.msg + ' | T6: ' + r.nolock6 + ' | no Charge: ' + r.noCharge);
  check(/^No Charge lock/.test(r.nolock.msg || '') && /play it blind/.test(r.nolock.msg) && /30%/.test(r.nolock.msg), 'no lock on T3: play it blind, Close Call 30%');
  check(/67\.5%/.test(r.nolock6 || '') && /32%/.test(r.nolock6 || ''), 'no lock on T6: blind 5+ 67.5%, 6+ 32%');
  check(/play it blind/.test(r.nolock.panel), 'the Charge panel says play it blind');
  check(/play it blind/i.test(r.noCharge || ''), 'no Charge read: play it blind');
  // 5. arena on console frames of the other fights
  const F = clipFrames();
  if (F.length) {
    const ar = await p.evaluate(async F => {
      const T = window.__tot, out = {}, cv = document.createElement('canvas'); cv.width = 160; cv.height = 90; const cx = cv.getContext('2d'), im = cx.createImageData(160, 90);
      for (const [clip, b64] of F) {
        const raw = Uint8Array.from(atob(b64), ch => ch.charCodeAt(0)); for (let i = 0, j = 0; i < raw.length; i += 3, j += 4) { im.data[j] = raw[i]; im.data[j + 1] = raw[i + 1]; im.data[j + 2] = raw[i + 2]; im.data[j + 3] = 255; }
        cx.putImageData(im, 0, 0); const bm = await createImageBitmap(cv), big = new OffscreenCanvas(1280, 720); big.getContext('2d').drawImage(bm, 0, 0, 1280, 720); bm.close();
        const vf = new VideoFrame(big, { timestamp: 0 }); T.V.src = vf; let a; try { a = T.chgArena(); } finally { T.V.src = null; vf.close(); }
        const o = out[clip] = out[clip] || { n: 0, jr: 0 }; o.n++; if (a.a === 'jr') o.jr++;
      }
      return out;
    }, F);
    for (const [clip, o] of Object.entries(ar)) { console.log('arena ' + clip + ': Jr. Troopa on ' + o.jr + ' of ' + o.n + ' frames'); check(o.jr === 0, 'arena ' + clip + ' never reads as Jr. Troopa'); }
  }
  check(!errs.length, 'page errors: ' + errs.slice(0, 3).join(' | '));
  console.log(fails ? fails + ' FAILED' : 'all passed'); await b.close(); process.exit(fails ? 1 : 0);
})();
