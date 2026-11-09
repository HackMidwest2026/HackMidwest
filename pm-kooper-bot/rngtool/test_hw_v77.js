/* v83: the plan's frame is the perfect press's (the tracker and its states must still be v77's; see the check below).
 * v79: at 10 HP (and with the HP not read: the route's HP above 5 assumed) the Hallway T2 Time Out plan must be v77's. The
 * v77 page is built from git (commit 0e9e28f, page v77) with only test hooks added (the same exports v79 has for the Hallway
 * tracker), and the same games go through both pages: the T1 Charge lock (hwTrackerAt), the Spiny Flip confirm (impact frame
 * and guard hidden), Bowser's attack at 10 HP (no Close Call roll), 1.5 s of T2's coin, then the real makePlan on Time Out's
 * target screen. Every plan (target frame, chance, no edge) must be the same. With the HP not read v79 also carries the
 * <=5 HP roll states (charge_live/hwcc_live.js); its plan may differ only by saying no edge for the HP (counted).
 * usage (from rngtool/, after python3 build_page.py): node test_hw_v77.js [N=30] */
'use strict';
const { chromium } = require('playwright'), { execSync } = require('child_process'), fs = require('fs'), path = require('path');
const SP = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad', N = +(process.argv[2] || 30);
const V79 = SP + '/timeout_timer/timeout_timer_standalone.html', V77 = SP + '/v77ref/timeout_timer_standalone.html';
const R = require('./pmrng_core.js');
function buildV77() {
  const src = SP + '/v77ref_src', H = src + '/pm-kooper-bot/rngtool', top = execSync('git rev-parse --show-toplevel', { cwd: __dirname }).toString().trim();
  fs.rmSync(src, { recursive: true, force: true }); fs.mkdirSync(src, { recursive: true });
  execSync('git archive 0e9e28f pm-kooper-bot/rngtool/page_template.html pm-kooper-bot/rngtool/pmrng_core.js pm-kooper-bot/rngtool/build_page.py pm-kooper-bot/rngtool/shared pm-kooper-bot/rngtool/charge_live pm-kooper-bot/rngtool/readouts/data | tar -x -C ' + src, { cwd: top });
  const pt = path.join(H, 'page_template.html'); let s = fs.readFileSync(pt, 'utf8');
  if (!s.includes("const VERSION = 'v77'")) throw new Error('not the v77 page');
  s = s.replace('window.__tot = { VERSION, ', `window.__tot = { VERSION, zwInput: (id, t, v, imps) => zwInput(id, t, v, imps), zwUpdate: h => zwUpdate(h), zwTapF: f => zw.taps.push(f), VAN,
  hwTrackerAt: (seed, qs, trigT) => { chgReset(); Object.assign(CHG, { prof: CHG_PROF.hw, trig: { t: trigT }, taps: [], pres: [], state: 'locked', qs }); chgStartTracker(seed >>> 0, qs); return zw.on && zw.fight === 'hw'; }, `);
  fs.writeFileSync(pt, s);
  execSync('python3 build_page.py', { cwd: H, env: Object.assign({}, process.env, { TOT_OUT: SP + '/v77ref' }) });
}
let rs = 7707; const rnd = () => (rs = (Math.imul(rs, 1103515245) + 12345) >>> 0) / 4294967296;
const pick = D => { let u = rnd(); for (const [v, w] of D) { if (u < w) return v; u -= w; } return D[D.length - 1][0]; };
const LAGS = [[0, 0.75], [1, 0.25]], CHG_N = 48, IMPS = Array.from({ length: 33 }, (_, i) => 138 + i), SHIFTS = [[-2, 0.15], [-1, 0.25], [0, 0.4], [1, 0.2]];
function truth(g) {
  const ev = R.buildEv([{ f: -13, id: 'hw_charge' }, { f: g.Ct, id: 'hw_spiny', imp: g.imp, guard: g.guard }]);
  const S = { s: g.seed, nc: g.q, inst: [] }; let f = 0; const shines = [];
  const step = to => { while (f < to) { if (g.lag && f === CHG_N + 2) { S.nc += g.lag; f += g.lag; continue; } if (R.frameEv(S, f, ev)) shines.push(f); f++; } };
  return { S, step, shines };
}
async function open(b, file) { const p = await b.newPage(), errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { const real = performance.now.bind(performance); window.__dt = 0; performance.now = () => real() + window.__dt; });
  await p.goto('file://' + file); return { p, errs }; }
const game = async (P, g, menu, cScr, shines, tens) => P.p.evaluate(({ g, menu, cScr, shines, tens, IMPS }) => {
  const T = window.__tot, zw = T.zw, hi = T.RT().findIndex(s => s.turn === 'hw_spiny'), ti = T.RT().findIndex(s => s.prof === 'timeout');
  document.getElementById('s-prof').value = 'endgame'; document.getElementById('s-lead').value = '1.5'; document.getElementById('s-zwwin').value = '1';
  T.setStep(hi); if (T.hwHpReset) T.hwHpReset(); T.hwTrackerAt(g.seed, [g.q], 100000); if (T.HWHP && tens) T.HWHP.tens = Array(10).fill(tens === 'ten' ? 0.5 : 0);
  const vl = +document.getElementById('s-vlag').value || 0, pf = +document.getElementById('s-pfix').value || 0, tOf = (c, van) => zw.t0 + vl + (c + van + pf) * zw.rate;
  const setNow = t => { window.__dt += t - performance.now(); };
  const cRead = g.Ct - g.sh; setNow(tOf(cRead, T.VAN.B()) + 20); T.zwInput('hw_spiny', tOf(cRead, T.VAN.B()), T.VAN.B(), IMPS);
  T.setStep(ti); T.zwUpdate(menu - 10);
  zw.vis = [[menu, cScr - 4]]; zw.visFrom = null; zw.visTo = null; zw.visLocked = true; for (const f of shines) T.zwTapF(f);
  const n0 = T.SLOG.length; setNow(tOf(cScr, 0) + 30); T.st.plan = null; T.st.msg = null; T.makePlan(); const P = T.st.plan;
  return { plan: P ? { target: P.zwAbs, p: +P.mix.p.toFixed(9), pStates: +P.mix.pStates.toFixed(9), doubt: P.mix.doubt, groups: P.mix.groups, w: P.w } : null, pp: P && P.mix.ppStates != null ? P.mix.ppStates : null, win: P && P.mix.win, msg: P ? null : (T.st.msg || '').slice(0, 60),
    hp: T.SLOG.slice(n0).some(x => x.ev === 'zwNoEdgeHp'), parts: zw.parts.length, shadow: zw.shadow ? zw.shadow.length : 0 };
}, { g, menu, cScr, shines, tens, IMPS });
(async () => {
  buildV77();
  const b = await chromium.launch(), A = await open(b, V77), B = await open(b, V79);
  let fails = 0; const check = (ok, msg) => { console.log((ok ? 'ok   ' : 'FAIL ') + msg); if (!ok) fails++; };
  check(await A.p.evaluate(() => window.__tot.VERSION) === 'v77' && await B.p.evaluate(() => window.__tot.VERSION) === 'v84', 'pages v77 and v84');
  const row = { ten: { same: 0, n: 0, plans: 0 }, none: { same: 0, n: 0, plans: 0, hp: 0 } };
  for (let k = 0; k < N; k++) {
    const g = { seed: (rnd() * 4294967296) >>> 0, q: Math.floor(rnd() * 48), lag: pick(LAGS), Ct: 110 + Math.floor(rnd() * 120), sh: pick(SHIFTS), imp: IMPS[Math.floor(rnd() * IMPS.length)], guard: rnd() < 0.5 };
    const menu = g.Ct + g.imp + 44 + 300, cScr = menu + 45, tg = truth(g); tg.step(cScr);
    const shines = tg.shines.filter(f => f >= menu && f <= cScr - 4);
    const a = await game(A, g, menu, cScr, shines, null);
    for (const tens of ['ten', 'none']) {
      const v = await game(B, g, menu, cScr, shines, tens === 'ten' ? 'ten' : null), r = row[tens]; r.n++; if (a.plan) r.plans++;
      // v83 (the perfect press): the tracker is v77's (same states, same doubt); the plan's frame may move (a working frame,
      // the centre of the widest run), so the plan must be one wherever v77 planned, on a frame most states agree works
      const same = a.parts === v.parts && (!a.plan || (v.plan && v.plan.doubt === a.plan.doubt && v.plan.groups === a.plan.groups && v.pp >= 0.5 && v.win >= 1));
      if (a.plan && v.plan && v.plan.target !== a.plan.target) r.moved = (r.moved || 0) + 1;
      if (same) r.same++; else if (tens === 'none' && v.hp && !v.plan) r.hp++;
      else console.log('DIFF', k, tens, JSON.stringify(a), JSON.stringify(v));
      if (tens === 'ten' && v.shadow) { console.log('FAIL 10 HP carried roll states', k); fails++; }
    }
    if (k < 3) console.log('game', k, JSON.stringify(a.plan || a.msg));
  }
  console.log('10 HP read: ' + row.ten.same + '/' + row.ten.n + ' the same as v77 (' + row.ten.plans + ' v77 plans; ' + (row.ten.moved || 0) + ' moved to the perfect-press frame); HP not read: ' + row.none.same + '/' + row.none.n + ' the same, ' + row.none.hp + ' no edge for the HP (the roll fallback)');
  check(row.ten.same === row.ten.n, 'at 10 HP the tracker is v77\'s and every v77 plan is a plan, on a working frame (v83: the centre of the widest run)');
  check(row.none.same + row.none.hp === row.none.n && row.none.hp <= Math.ceil(0.1 * row.none.n), 'HP not read: v77\'s plan, or (rarely) no edge for the HP; never another beep');
  check(row.ten.plans >= N * 0.5, 'the games plan (' + row.ten.plans + '/' + N + ')');
  check(!A.errs.length && !B.errs.length, 'no page errors ' + A.errs.concat(B.errs).slice(0, 3).join(' | '));
  await b.close(); console.log(fails ? 'FAIL ' + fails : 'PASS'); process.exit(fails ? 1 : 0);
})();
