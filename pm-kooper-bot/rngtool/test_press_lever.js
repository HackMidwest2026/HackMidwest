/* v87: the Strategies-screen press reading and the per-lever correction, from the console sessions of 2026-11-07 and
 * 2026-11-09 (fixtures/console_1107.json, console_1109_press.json; numbers read off the clips, no pictures):
 *  1. the S screen's offset, from the clips with the input display (11-09 19-50-01 Duplighosts, 19-59-56 Jr. Troopa T5):
 *     the A on the display, then the Strategies box greys 10-11 capture frames later and goes 12-13 later, while a Mario
 *     action's bar hides 11-14 after its A (HUD_HIDE 3): grey = confirm + 2, gone = confirm + 3. The page closes the screen
 *     on the grey frame (every 11-09 clip), so dup3 / dup4 / jrcc_nothing read the press with vanish 2 (v86: 3, a frame early);
 *  2. the copies each Duplighost clip shows against the page's core at the frame read (v86 offset) + s: s = +1 (the v87
 *     reading) fits best, a 2-frame misread is ruled out, so the remaining early presses (about -1) are the runner's and
 *     the Charge clock's own placement: no Duplighost correction;
 *  3. only Final Bowser keeps a learned lever correction, and each press is kept against the beep, so a press on time after
 *     it keeps the correction (v86 let it decay); a Duplighost plan beeps on the global offset alone.
 * usage: node test_press_lever.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const F7 = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1107.json'), 'utf8')), F9 = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'console_1109_press.json'), 'utf8'));
const ncop = seen => { const n = [...seen].filter(c => c === 'C').length; return n < 3 ? 2 : n; };
const A = F9.dup.map(a => ({ seed: a.seed, qs: a.qs, target: a.target, err: a.err, copies: a.copies }))
  .concat(F7.dup.map(a => ({ seed: a.seed, qs: a.qs, target: a.target, err: a.err, copies: ncop(a.seen) })));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [], p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(A => {
    const T = window.__tot, out = {}; const sel = document.getElementById('s-duproute'); sel.value = 'charge'; sel.dispatchEvent(new Event('change'));
    out.van = { dup3: T.R.PROFILES.dup3.vanish, dup4: T.R.PROFILES.dup4.vanish, jrcc_nothing: T.R.PROFILES.jrcc_nothing.vanish, jrcc_bomb: T.R.PROFILES.jrcc_bomb.vanish, jrcc_syrup: T.R.PROFILES.jrcc_syrup.vanish, timeout: T.R.PROFILES.timeout.vanish };
    out.cls = A.map(a => { T.setStep(0); T.dupTrackerAt(parseInt(a.seed, 16), a.qs, performance.now() - 2000); const S = T.dupStatesAt(100), f = Math.round(a.target + a.err);
      return S.map(q => ({ w: q.w, c: T.dupClasses(q.s, q.nc, q.g, f - 4, f + 4) })); });
    out.keys = ['dup3', 'dup4', 'fb14', 'jrcc_bomb', 'jrcc_syrup', 'jrcc_nothing', 'jrpb5', 'timeout'].map(k => T.leverKey(k));
    out.fb0 = T.leverBias('fb14'); T.leverAdd('fb14', 0 - out.fb0); T.leverAdd('fb14', 0 - out.fb0); out.fb1 = T.leverBias('fb14'); localStorage.removeItem('tot-fb14press');
    T.setStep(0); T.dupTrackerAt(parseInt(A[0].seed, 16), A[0].qs, performance.now() - 2000); T.st.plan = null; T.makePlan(); const P = T.st.plan;
    out.plan = P ? { bias: P.bias, dt: (P.tPress - T.pressTime(P.tLast, P.rate, P.target)) / P.rate, prof: P.prof } : null;
    return out;
  }, A);
  check(r.van.dup3 === 2 && r.van.dup4 === 2 && r.van.jrcc_nothing === 2, '1. the Strategies screen (dup3, dup4, jrcc_nothing) reads the press from its grey frame, confirm + 2 ' + JSON.stringify(r.van));
  const like = {}; for (let s = -2; s <= 3; s++) { let L = 1; for (let i = 0; i < A.length; i++) { const S = r.cls[i], tot = S.reduce((x, q) => x + q.w, 0); L *= S.filter(q => q.c[4 + s] === A[i].copies).reduce((x, q) => x + q.w, 0) / tot; } like[s] = L; }
  console.log('  likelihood of the copies seen (' + A.length + ' attempts) if the true press was the v86 reading + s: ' + Object.entries(like).map(([s, L]) => (s > 0 ? '+' : '') + s + ': ' + L.toExponential(2)).join(', '));
  check(like[1] > like[0] && like[2] === 0 && like[3] === 0, '2. the copies fit the v87 reading (+1) best, and rule out a 2-frame misread');
  const v87 = A.map(a => a.err + 1), mean = v87.reduce((x, y) => x + y, 0) / v87.length;
  console.log('  Duplighost presses as v87 reads them: ' + v87.map(x => x.toFixed(2)).join(', ') + ' (mean ' + mean.toFixed(2) + ')');
  check(JSON.stringify(r.keys) === JSON.stringify([null, null, 'fb14', null, null, null, null, null]), '3. only Final Bowser\'s levers keep a learned correction ' + JSON.stringify(r.keys));
  check(Math.abs(r.fb0 - 2.37) < 0.01 && Math.abs(r.fb1 - r.fb0) < 0.2, '3. Final Bowser +' + r.fb0.toFixed(2) + ', still +' + r.fb1.toFixed(2) + ' after two presses on time with it');
  check(r.plan && r.plan.prof === 'dup3' && Math.abs(r.plan.dt) < 0.01, '3. a Duplighost plan beeps on the global offset alone (' + JSON.stringify(r.plan) + ')');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
