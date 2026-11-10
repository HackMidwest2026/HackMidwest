/* v87: the Final Bowser T1 -> T2 carry fixes on the page (charge_live/fb14_live.js), on the game's own state from a
 * continuous emulator log (fixtures/fb14_chain_logs.json, the first chain: T1 Charge + Cloud Nine, Bowser missed, T2):
 *  1. a T2 lock that lands after the carried states ran past the Charge's rays (v86 skipped them all: "matched 0 of 8000")
 *     still finds the game's state, with its coin history kept;
 *  2. the end check is the seed on the frame after the rays only (a fit with the coin 11 frames off still matches);
 *  3. the cap keeps the likeliest by w x lw (v86: by w alone, the coin's weight ignored);
 *  4. the narrowed T2 search: the candidates from the carried states at the Charge frame -2 .. +2, the Charge held while
 *     it runs, the direct lock on the carried states at the shift that drew the rays;
 *  6. T4's wave in either particle order (the split).
 * usage: node test_fb14_v87.js [PAGE] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const PAGE = process.argv[2] || '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/timeout_timer/timeout_timer_standalone.html';
const L = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', 'fb14_chain_logs.json'), 'utf8'))[0];
const buf = Buffer.from(L.s0, 'base64'), seeds = Array.from({ length: L.n }, (_, i) => buf.readUInt32LE(4 * i));
let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
(async () => {
  const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); fs.createReadStream(PAGE).pipe(r); });
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const url = 'http://127.0.0.1:' + srv.address().port + '/';
  const b = await chromium.launch(), errs = [], p = await b.newPage(); p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto(url);
  const r = await p.evaluate(({ L, seeds }) => {
    const T = window.__tot, X = window.__fb14, FB = X.FB14, rate = 33.367, T1 = L.turns[0], T2 = L.turns[1], M = T2.M, out = {};
    const sAt = f => seeds[f - L.f0] >>> 0;
    // the game's state before T2's Charge (from the log's first frame with T1's true inputs), and 40 decoys
    const truth = () => { const S = X.fbNew({ s: seeds[0], nc: L.nc, f: L.f0, c: Uint8Array.from(L.aura), ph: [L.ph[0], L.ph[1]], l: 0, w: 1, from: L.f0 });
      S.ev.push({ k: 'chg', f: T1.M + 13 }, { k: 'chg', f: T1.M + 16 }); for (let i = 200; i < 210; i++) S.ev.push({ k: 'puff', f: T1.P + i }); S.ev.push({ k: 'ai', f: T1.P + 332, turn: 1 });
      S.ev.sort((a, b) => a.f - b.f); X.fbRun(S, M - 30); return S; };
    const setup = () => { X.reset(); const S = truth(), L2 = [S]; for (let i = 0; i < 40; i++) { const D = X.fbClone(S); D.s = (Math.imul(i + 1, 0x9E3779B1) ^ S.s) >>> 0; D.w = 0.5; L2.push(D); }
      const t0 = performance.now() - (M + 300) * rate; Object.assign(FB, { on: true, t0, rate, states: L2, turn: 1, M: { 1: T1.M }, lockN: 1 }); FB.trigTurn = 2; T.CHG.narrow14 = null; return S; };
    // the rays' A (the seed after its base-angle draw) and the seed after the rays, from the true state
    const S0 = setup(), A = X.fbClone(S0); X.fbRun(A, M + 13); let x = A.s; const bl = (f, ph) => { const m1 = (f + ph[0]) % 130, m2 = (f + ph[1]) % 220; return (m1 === 78 || m1 === 83 || m1 === 113 || m1 === 118 ? 1 : 0) + (m2 === 18 || m2 === 78 || m2 === 88 || m2 === 178 ? 1 : 0); };
    for (let i = bl(M + 13, A.ph); i; i--) x = X.fbRi(x, 359); const a = X.fbAdv(x) >>> 0, s61 = sAt(M + 61);
    const res = nc48 => ({ fb1: { hyps: { hy: [{ s48: s61, nc48, sc: 100, esc: 100, p: 0, q: 0, aura: Array.from(S0.c) }], a, best: 100, n: 1 } }, trigT: FB.t0 + (M + 16) * rate });
    const isTrue = S => (S.s >>> 0) === sAt(S.f);
    // 1. the late lock
    { setup(); const sh0 = FB.states[0].sh.slice(); X.input('chg', M, 2, X.FB14_CHGD); X.advance(M + 200); const ran = Math.min(...FB.states.map(S => S.f));
      const how = X.lock(res(0)); out.late = { ran, how, n: FB.states.length, nTrue: FB.states.filter(isTrue).length, shKept: FB.states.filter(isTrue).some(S => S.sh.length >= sh0.length) }; }
    // 2. the coin's phase 11 frames off in the fit
    { setup(); X.input('chg', M, 2, X.FB14_CHGD); X.advance(M + 5); const how = X.lock(res(11)); out.coin = { how, nTrue: FB.states.filter(isTrue).length }; }
    // 4. the narrowed search
    { setup(); FB.pendChg = { M, turn: 2 }; T.CHG.state = 'search'; const pr0 = T.CHG.prof; T.CHG.prof = { id: 'fb1' }; const c = X.chgCands(), N = T.CHG.narrow14, h1 = X.held();
      N.done = true; N.ok = true; const h2 = X.held(); X.advance(M + 400); const f = Math.max(...FB.states.map(S => S.f));
      const how = X.lock(res(0)), h3 = X.held();
      out.narrow = { cands: c ? c.length : 0, hasTrue: !!c && c.includes(x >>> 0), dTrue: N.dmap.get(x >>> 0) ? [...N.dmap.get(x >>> 0)] : null, h1, h2, h3, f, how, used: N.used, pend: FB.pendChg, mk: [...new Set(FB.states.map(S => S.mk))], nTrue: FB.states.filter(S => { const C = X.fbClone(S); X.fbRun(C, M + 61); return (C.s >>> 0) === s61; }).length };
      T.CHG.state = 'idle'; T.CHG.prof = pr0; }
    // 3. the cap
    { const Lc = []; for (let i = 0; i < X.FB14_MAXH + 1; i++) Lc.push(X.fbNew({ s: i + 1, nc: 0, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1, lw: 0.001 }));
      Lc.push(X.fbNew({ s: 999999, nc: 0, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 0.01, lw: 1 })); const kept = X.cap(Lc); out.cap = { maxh: X.FB14_MAXH, n: kept.length, kept: kept.some(S => S.s === 999999) }; }
    // 6. the wave split
    { const S = X.fbNew({ s: 5, nc: 0, f: 0, c: new Uint8Array(20), ph: [0, 0], l: 0, w: 1 }), L1 = X.waveSplit([S]), L2 = X.waveSplit(L1);
      out.split = { n1: L1.length, n2: L2.length, w: L1.map(S => +S.w.toFixed(3)), wb: L1.map(S => S.wb) }; }
    out.log = T.SLOG.filter(e => /^fb14(Check|Held|ChgCands|ClockFix|ClockKept)$/.test(e.ev)).slice(-8);
    return out;
  }, { L, seeds });
  console.log(JSON.stringify(r));
  check(r.late.ran > L.turns[1].M + 61 && r.late.how === 'carried' && r.late.nTrue >= 1 && r.late.shKept, '1. a lock after the states ran past the rays (to ' + r.late.ran + '): carried, the game\'s state kept with its coin history ' + JSON.stringify(r.late));
  check(r.coin.how === 'carried' && r.coin.nTrue >= 1, '2. the fit\'s coin 11 frames off: the seed after the rays still matches ' + JSON.stringify(r.coin));
  check(r.narrow.hasTrue && r.narrow.cands <= 5 * 41 && r.narrow.h1 && r.narrow.h2 && !r.narrow.h3, '4. narrowed T2: the game\'s seed among ' + r.narrow.cands + ' candidates; the Charge held while the search runs and until the lock');
  check(r.narrow.f <= L.turns[1].M + 10, '4. no state ran past the held Charge (' + r.narrow.f + ')');
  check(r.narrow.how === 'carried' && r.narrow.used && r.narrow.pend === null && r.narrow.nTrue >= 1 && r.narrow.mk.length === 1 && r.narrow.mk[0] === L.turns[1].M, '4. the direct lock: carried, the held Charge applied at the shift that drew the rays (' + r.narrow.mk + ')');
  check(r.cap.n === r.cap.maxh && r.cap.kept, '3. the cap (' + r.cap.maxh + ') keeps the state the coin favours (w 0.01 x lw 1 over w 1 x lw 0.001)');
  check(r.split.n1 === 2 && r.split.n2 === 2 && r.split.w[0] === 0.92 && r.split.w[1] === 0.08 && r.split.wb[0] === 0 && r.split.wb[1] === 1, '6. the wave split: 0.92 / 0.08, once ' + JSON.stringify(r.split));
  check(!errs.length, 'no page errors ' + errs.slice(0, 3).join(' | '));
  await b.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'all passed'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
