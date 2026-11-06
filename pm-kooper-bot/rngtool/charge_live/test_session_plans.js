/* The Time Out plans of the runner's first live session (timeout-timer-log-1793757328924, Time Out Timer v68), replayed
 * through the page's own zero-wait tracker (page_template.html zw*, charge_live.js chgStartTracker) in node:
 * every Charge lock of the log (seed, q), its Spiny Flip confirm, the shines and the bar's up/down times, then zwPlan at
 * the time the page made its plan. The clock origin (the trigger picture's time) is not logged: the first one within
 * 80 ms before the logged trigger that gives the logged Spiny Flip frame and the logged plan target is used, so each
 * attempt is checked against the log (zwInput c and the plan's target must both match).
 * Then, per attempt: the target zwPlan picks with the old press model (25/50/25 over -1/0/+1) and with the runner's own
 * spread (pressDist: the rms of the session's 5 presses on the beeps, 2.3 frames), the chance Time Out works under the
 * runner's spread for each, and whether the frame the runner actually pressed (target + err, logged) works.
 * usage (from rngtool/): node charge_live/test_session_plans.js [LOG] */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const RT = path.resolve(__dirname, '..'), R = require(path.join(RT, 'pmrng_core.js'));
const LOGF = process.argv[2] || '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887/9e47f827-timeout-timer-log-1793757328924.json';
function grabFn(src, name) {
  const i = src.indexOf('function ' + name + '('); if (i < 0) throw new Error('no function ' + name);
  for (let k = src.indexOf('{', src.indexOf(')', i)), d = 0; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}' && --d === 0) return src.slice(i, k + 1); }
  throw new Error('unbalanced ' + name);
}
const grabLine = (src, re) => { const m = src.match(re); if (!m) throw new Error('no ' + re); return m[0]; };
const PAGE = fs.readFileSync(path.join(RT, 'page_template.html'), 'utf8'), CHG = fs.readFileSync(path.join(RT, 'charge_live/charge_live.js'), 'utf8');
function tracker(presses) {
  const a = PAGE.indexOf('const ZW_SCENE'), b = PAGE.indexOf('function zwPlan(');
  const code = [grabLine(PAGE, /const PRESS_ERR = .*\n/), grabFn(PAGE, 'pressDist'), PAGE.slice(a, b), grabLine(CHG, /const CHG_N = .*\n/), grabLine(CHG, /const CHG_K = .*\n/),
    grabLine(CHG, /const CHG_LAGS = .*\n/), grabLine(CHG, /const CHG_SHIFTS = .*\n/), (CHG.includes('function chgRate(') ? grabFn(CHG, 'chgRate') : ''), grabFn(CHG, 'chgStartTracker'),
    'this.api = { zw, zwF, zwUpdate, zwInput, zwTap, zwCoinBack, chgStartTracker, CHG_IMPS, pressDist, PRESS_ERR };'].join('\n');
  const settings = { vlag: 50, pfix: 0 }, ctx = { R, FRAME: R.FRAME_MS, Math, Array, Map, Set, Object, Number, JSON, String, now: 0, log: [], presses,
    VAN: { B: () => R.PROFILES.timeout.vanish }, CHG: {}, V: {}, num: k => +(settings[k] || 0) };
  ctx.slog = (ev, o) => ctx.log.push(Object.assign({ ev }, o)); ctx.performance = { now: () => ctx.now };
  vm.createContext(ctx); vm.runInContext(code, ctx); return Object.assign(ctx.api, { ctx });
}
/* zwPlan's choice (page_template.html), with a given press model; returns the target and the parts it saw */
function plan(L, now, PD, lead, win) {
  const { zw, ctx } = L; ctx.now = now; const to = Math.floor(L.zwF(now, 0)); zw.visTo = to - 4; L.zwUpdate(to);
  const parts = zw.parts.filter(p => !p.S.inst.length && !(p.S.extra && p.S.extra.size)); if (!parts.length) return null;
  const from = Math.ceil(to + lead * 1000 / zw.rate + 1), W = Math.round(win * 1000 / zw.rate), D = Math.max(...PD.map(x => Math.abs(x[0]))), sc = new Array(W + 1).fill(0);
  const tabs = parts.map(p => { const t = new Map(); for (let c = from - 6; c <= from + W + 6; c++) t.set(c, R.works(p.S.s, p.S.nc, c, p.g, R.PROFILES.timeout) ? 1 : 0); return t; });
  parts.forEach((p, i) => { for (let k = 0; k <= W; k++) for (const [d, q] of PD) sc[k] += p.w * q * tabs[i].get(from + k + d); });
  let k = 0; for (let i = 1; i <= W; i++) if (sc[i] > sc[k] + 1e-12) k = i;
  const tot = parts.reduce((a, p) => a + p.w, 0), pAt = (c, pd) => parts.reduce((a, p, i) => a + p.w * pd.reduce((b, [d, q]) => b + q * tabs[i].get(c + d), 0), 0) / tot;
  const run = c => { let lo = c, hi = c; const all = c2 => parts.every((p, i) => tabs[i].get(c2)); if (!all(c)) return 0; while (all(lo - 1)) lo--; while (all(hi + 1)) hi++; return hi - lo + 1; };
  return { target: from + k, p: sc[k] / tot, pAt, parts: parts.length, states: new Set(parts.map(p => p.S.s + ':' + p.S.nc + ':' + p.g)).size, run, tabs, prt: parts };
}
const log = JSON.parse(fs.readFileSync(LOGF, 'utf8')), E = log.events;
const ups = E.filter(e => e.ev === 'barHide').map(e => [e.at - e.upMs, e.at]);
const presOf = t => ups.some(([a, b]) => t >= a && t < b);
const pressErrs = E.filter(e => e.ev === 'press').map(e => e.err);
const runnerPD = tracker(pressErrs).pressDist(), oldPD = tracker([]).PRESS_ERR;
const sdOf = pd => Math.sqrt(pd.reduce((a, [d, q]) => a + q * d * d, 0));
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };
console.log('runner presses on the beeps: ' + pressErrs.join(', ') + ' -> press model sd ' + sdOf(runnerPD).toFixed(2) + ' frames (old model ' + sdOf(oldPD).toFixed(2) + ')');
const rows = [];
for (const lk of E.filter(e => e.ev === 'chargeLock')) {
  const trig = E.filter(e => e.ev === 'chargeTrigger' && e.t < lk.t).pop(), sp = E.find(e => e.ev === 'zwInput' && e.t >= lk.t - 5000 && e.t > trig.t);
  const sc = E.find(e => e.ev === 'screenClosed' && e.step === 7 && e.t > trig.t), pl = E.find(e => e.ev === 'plan' && e.t > lk.t && e.t < lk.t + 30000);
  const pr = pl && E.find(e => e.ev === 'press' && e.t > pl.t && e.t < pl.t + 10000), sp2 = sc && E.find(e => e.ev === 'screenClosed' && e.t > sc.t);
  const row = { lock: Math.round(trig.t / 100) / 10, seed: lk.best.seed, qs: lk.qs.join('/'), spinyC: sp && sp.c };
  if (!pl) { row.note = 'no plan logged'; rows.push(row); continue; }
  const tMade = sp2 && sp2.plan ? sp2.plan.tMade : pl.t;
  const T0 = trig.t; let hit = null;
  for (let T = T0 - 80; T <= T0 && !hit; T++) {
    const L = tracker(pressErrs), C = L.ctx.CHG, tMaps = T + 48 * L.ctx.FRAME + 1;
    C.trig = { t: T }; C.taps = E.filter(e => e.ev === 'shine' && e.at >= tMaps && e.at < lk.t).map(e => e.at); C.pres = []; C.spiny = sc.at < lk.t ? sc.at : null;
    for (let i = Math.ceil(tMaps * 0.06); i / 0.06 < lk.t; i++) { const t = i / 0.06; C.pres.push([t, presOf(t)]); }
    L.ctx.now = lk.t; L.chgStartTracker(parseInt(lk.best.seed, 16) >>> 0, lk.qs);
    const evs = [];
    if (sc.at >= lk.t) evs.push([sc.at, 'spiny']);
    for (const e of E) if (e.ev === 'shine' && e.at >= lk.t && e.at < tMade) evs.push([e.at, 'shine']);
    for (const [a] of ups) if (a > sc.at && a < tMade - 1000) evs.push([a + 1000, 'back', a - sc.at]);
    evs.sort((x, y) => x[0] - y[0]);
    for (const [t, k, h] of evs) { L.ctx.now = t; if (k === 'spiny') L.zwInput('hw_spiny', t, L.ctx.VAN.B(), L.CHG_IMPS); else if (k === 'shine') L.zwTap(t); else L.zwCoinBack(h); }
    const c = (L.ctx.log.find(x => x.ev === 'zwInput') || {}).c;
    if (c !== sp.c) continue;
    const P = plan(L, tMade, oldPD, 1.5, 1);
    if (P && P.target === pl.target) hit = { T, P };
  }
  if (!hit) { row.note = 'log not reproduced'; check(false, 'attempt ' + row.lock + ': no clock origin reproduces the logged Spiny Flip frame and plan target'); rows.push(row); continue; }
  const P = hit.P;
  // the runner's model: rescore the same parts (the tabs cover the window +-6)
  const from = Math.min(...[...P.tabs[0].keys()]) + 6, W = 30; let best = from, bv = -1;
  for (let k = 0; k <= W; k++) { const v = P.pAt(from + k, runnerPD); if (v > bv + 1e-12) { bv = v; best = from + k; } }
  const actual = pr ? pl.target + Math.round(pr.err) : null;
  Object.assign(row, { origin: hit.T - Math.round(trig.t), states: P.states, oldTarget: P.target, oldPick: +P.pAt(P.target, oldPD).toFixed(2), oldUnderRunner: +P.pAt(P.target, runnerPD).toFixed(2),
    newTarget: best, newUnderRunner: +bv.toFixed(2), err: pr ? pr.err : null, pressedWorks: actual != null ? +P.pAt(actual, [[0, 1]]).toFixed(2) : null, logWorks: pr ? pr.works : null,
    run: P.run(P.target) });
  check(row.newUnderRunner >= row.oldUnderRunner - 1e-9, 'attempt ' + row.lock + ': the runner-spread pick must not be worse under that spread');
  if (pr) check((row.pressedWorks >= 0.5) === pr.works, 'attempt ' + row.lock + ': the replay disagrees with the log about the pressed frame (' + row.pressedWorks + ' vs ' + pr.works + ')');
  rows.push(row);
}
for (const r of rows) console.log(JSON.stringify(r));
const done = rows.filter(r => r.newUnderRunner != null);
if (done.length) console.log('mean chance under the runner\'s spread: old pick ' + (done.reduce((a, r) => a + r.oldUnderRunner, 0) / done.length).toFixed(2) + ', runner-spread pick ' + (done.reduce((a, r) => a + r.newUnderRunner, 0) / done.length).toFixed(2));
check(done.length >= 4, 'at least 4 attempts reproduced (' + done.length + ')');
console.log(fails ? fails + ' FAILED' : 'all passed');
process.exit(fails ? 1 : 0);
