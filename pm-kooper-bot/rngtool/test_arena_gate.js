/* v87: the arena moves are gated (charge_live.js arenaMoveOk, chgArenaClass).
 *  1. console log bf4fbf04 (2026-11-09, page v86.1): on the Duplighosts' step a bar hide read "final bowser" (L 245.1, br -1.1,
 *     lbr -4.2: a near-white picture) and moved the route to Final Bowser. Now that picture is no arena, and the move from
 *     the Duplighosts to Final Bowser would be refused anyway (it skips two fights), so the route stays on the Duplighosts;
 *  2. the real arenas still read as before (the console values of that session: Duplighosts, Jr. Troopa, Hallway, FB);
 *  3. synthetic: a forward move one fight on after its minimum time goes, too soon or skipping a fight does not (logged
 *     arenaRejected), Final Bowser needs 5 minutes after the Duplighosts, a move back (a retry) always goes, and a manual
 *     step change always goes and restarts that fight's clock.
 * usage: node test_arena_gate.js [PAGE] */
const { chromium } = require('playwright');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const b = await chromium.launch(), errs = [], p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('tot-settings', JSON.stringify({ duproute: 'charge', jrroute: 'charge', off: '-5', vlag: '50' })); } catch (e) {} });
  await p.goto('file://' + PAGE);
  const r = await p.evaluate(() => {
    const T = window.__tot, RT = T.RT(), out = {}, idx = f => RT.findIndex((s, i) => {
      if (f === 'dup') return s.chg === 'dup'; if (f === 'jr') return s.chg === 'jr'; if (f === 'hw') return /^Hallway Bowser/.test(s.t || ''); return s.chg === 'fb1' || !!s.fb14; });
    const I = { dup: idx('dup'), jr: idx('jr'), hw: idx('hw'), fb: idx('fb') }; out.I = I;
    out.cls = { white: T.chgArenaClass(245.1, -1.1, -4.2), hwSeen: T.chgArenaClass(37.3, 35, 23.4), dupSeen: T.chgArenaClass(62.3, 10.8, 7.9), fbConsole: T.chgArenaClass(114.3, 12.5, -31.2), jr: T.chgArenaClass(68.6, 14.9, -2.3) };
    // 1. the log: reset at 11856 on the Duplighosts' step, the bad picture at 104234
    T.setStep(I.dup); T.arenaReset(11856); const n0 = T.SLOG.length;
    out.bf4 = { ok: T.arenaMoveOk(I.fb, { L: 245.1, br: -1.1, lbr: -4.2 }, 104234), rej: T.SLOG.slice(n0).filter(e => e.ev === 'arenaRejected').map(e => e.why) };
    // 3. synthetic
    const at = (from, to, tFrom, t, dupT) => { T.setStep(I[from]); T.ARENA.seen = {}; if (dupT != null) T.ARENA.seen.dup = dupT; T.arenaNote(I[from], tFrom); return T.arenaMoveOk(I[to], null, t); };
    out.syn = {
      dupJrEarly: at('dup', 'jr', 0, 60000), dupJrOk: at('dup', 'jr', 0, 200000),
      jrHwEarly: at('jr', 'hw', 0, 30000), jrHwOk: at('jr', 'hw', 0, 150000),
      hwFbOk: at('hw', 'fb', 1000000, 1200000, 0), hwFbSoonAfterDup: at('hw', 'fb', 0, 200000, 0),
      dupFb: at('dup', 'fb', 0, 3600000), jrFb: at('jr', 'fb', 0, 3600000),
      backJrDup: at('jr', 'dup', 0, 1000), backFbHw: at('fb', 'hw', 0, 1000), sameFight: at('jr', 'jr', 0, 10) };
    // manual: a click on Final Bowser's step from the Duplighosts' goes, and its clock starts there
    T.setStep(I.dup); T.ARENA.seen = {}; const tm = performance.now(); T.setStep(I.fb); out.manual = { step: T.step(), fbSeen: T.ARENA.seen.fb != null && T.ARENA.seen.fb >= tm };
    out.rejLog = T.SLOG.filter(e => e.ev === 'arenaRejected').length;
    return out;
  });
  console.log(JSON.stringify(r));
  check(r.cls.white === null, '1. the near-white picture of bf4fbf04 (L 245) is no arena');
  check(!r.bf4.ok && r.bf4.rej.length === 1 && /skips/.test(r.bf4.rej[0]), '1. and Duplighosts -> Final Bowser is refused (' + r.bf4.rej[0] + '): the route stays on the Duplighosts');
  check(r.cls.hwSeen === 'hw' && r.cls.dupSeen === 'dup' && r.cls.fbConsole === 'fb' && r.cls.jr === 'jr', '2. the session\'s real arenas read as before ' + JSON.stringify(r.cls));
  const S = r.syn;
  check(!S.dupJrEarly && S.dupJrOk && !S.jrHwEarly && S.jrHwOk && S.hwFbOk, '3. one fight on: refused too soon, allowed after the minimum');
  check(!S.hwFbSoonAfterDup, '3. Final Bowser not within 5 minutes of the Duplighosts');
  check(!S.dupFb && !S.jrFb, '3. a skipped fight is never automatic');
  check(S.backJrDup && S.backFbHw && S.sameFight, '3. back (a retry, an earlier save) and the same fight always go');
  check(r.manual.step === r.I.fb && r.manual.fbSeen, '3. a manual step change always goes and starts that fight\'s clock');
  check(r.rejLog >= 6, '3. every refused move is logged (arenaRejected: ' + r.rejLog + ')');
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
