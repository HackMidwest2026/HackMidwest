/* fix_proposal.patch, tested: the page's own zero-wait tracker (page_template.html zw*) and chgStartTracker
 * (charge_live.js) run in node on event timings, without and with the patch (applied to a temp copy when the files
 * on disk do not have it yet, reversed out of one when they do).
 *
 * 1. The live log timeout-timer-log-1793735643131 (real N64, the runner's first live attempt): Charge lock ed937d1f
 *    q 21 at 427144 ms, after the Spiny Flip confirm (bar hid 426190, back from 424681). The clock's frame 0 (trigger
 *    picture time) is not logged; every value that gives the logged Spiny Flip frame c = 120 is tried.
 *    Unpatched: must reproduce the log exactly (zwStart 2 particles, zwInconsistent at 120, zwInput c 120 with 0).
 *    Patched: the seed survives the confirm and all five later shines (431040 ... 440673, including the one the
 *    page rejected at 435023) for every coin-return time on the turn-2 menu tried.
 * 2. The 7 route clips (2026-11-02_15-*.mkv; never committed): the page's coin detector and Charge trigger rule were
 *    run on the decoded frames (ffmpeg -> 32x32 coin box, 32x24 game area) and the timings are below, ms from the
 *    trigger picture. Each clip's offline seed and q (charge_live/README.md; 15-16-08 with the q the live page kept)
 *    are locked 1 s after the Spiny Flip confirm (as in every live clip run) and 0.3 s after the rays (before it).
 *    Patched: the tracker must be alive at Time Out's confirm (bar hiding - 3 frames) with the same states and the
 *    same share for which Time Out works as unpatched.
 * usage (from rngtool/): node charge_live/test_fix_proposal.js */
'use strict';
const fs = require('fs'), path = require('path'), os = require('os'), vm = require('vm'), cp = require('child_process');
const RT = path.resolve(__dirname, '..'), PATCH = path.join(__dirname, 'fix_proposal.patch'), MARK = 'b = zwF(t, 0) - 6;';

function grabFn(src, name) {
  const i = src.indexOf('function ' + name + '('); if (i < 0) throw new Error('no function ' + name);
  for (let k = src.indexOf('{', src.indexOf(')', i)), d = 0; k < src.length; k++) {
    if (src[k] === '{') d++; else if (src[k] === '}' && --d === 0) return src.slice(i, k + 1);
  }
  throw new Error('unbalanced ' + name);
}
function grabLine(src, re) { const m = src.match(re); if (!m) throw new Error('no ' + re); return m[0]; }
/* the two charge_live.js texts: [unpatched, patched] */
function variants() {
  const disk = fs.readFileSync(path.join(RT, 'charge_live/charge_live.js'), 'utf8');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'chgfix-')), f = path.join(dir, 'charge_live/charge_live.js');
  fs.mkdirSync(path.dirname(f)); fs.writeFileSync(f, disk);
  const had = disk.includes(MARK);
  cp.execFileSync('patch', ['-s', '-p3', '-d', dir].concat(had ? ['-R'] : []), { input: fs.readFileSync(PATCH) });
  const other = fs.readFileSync(f, 'utf8'); fs.rmSync(dir, { recursive: true, force: true });
  const v = had ? [other, disk] : [disk, other];
  if (v[0].includes(MARK) || !v[1].includes(MARK)) throw new Error('patch did not change the line it is about');
  return v;
}
const PAGE = fs.readFileSync(path.join(RT, 'page_template.html'), 'utf8'), R = require(path.join(RT, 'pmrng_core.js'));
function tracker(chg) {
  const a = PAGE.indexOf('const ZW_SCENE'), b = PAGE.indexOf('function zwPlan()');
  const code = [PAGE.slice(a, b), grabLine(chg, /const CHG_N = .*\n/), grabLine(chg, /const CHG_K = .*\n/), grabLine(chg, /const CHG_LAGS = .*\n/),
    grabLine(chg, /const CHG_SHIFTS = .*\n/), grabFn(chg, 'chgStartTracker'),
    'this.api = { zw, zwF, zwUpdate, zwInput, zwTap, zwCoinBack, chgStartTracker, CHG_IMPS };'].join('\n');
  const settings = { vlag: 50, pfix: 0 }, ctx = { R, FRAME: R.FRAME_MS, Math, Array, Map, Set, Object, Number, JSON, String, now: 0, log: [],
    VAN: { B: () => R.PROFILES.timeout.vanish }, CHG: {}, num: k => +(settings[k] || 0) };
  ctx.slog = (ev, o) => ctx.log.push(Object.assign({ ev }, o)); ctx.performance = { now: () => ctx.now };
  vm.createContext(ctx); vm.runInContext(code, ctx); return Object.assign(ctx.api, { ctx });
}
/* the page between the end of the rays and the lock: a picture every 1/60 s into CHG.pres (present from `pres`
 * transitions), shines seen into CHG.taps */
function lockAt(L, T, tLock, presOf, taps, spiny, seed, qs) {
  const { ctx, zw } = L, C = ctx.CHG, tMaps = T + 48 * ctx.FRAME + 1;
  C.trig = { t: T }; C.taps = taps.filter(s => s >= tMaps && s < tLock); C.pres = []; C.spiny = tLock > spiny ? spiny : null;
  for (let i = Math.ceil(tMaps * 0.06); i / 0.06 < tLock; i++) { const t = i / 0.06; C.pres.push([t, presOf(t)]); }
  ctx.now = tLock; L.chgStartTracker(seed >>> 0, qs); return zw;
}
let fails = 0; const check = (ok, msg) => { if (!ok) { fails++; console.log('FAIL ' + msg); } };

/* ---- 1. the live log ---- */
const LOG = { up: 424681, spiny: 426190, lock: 427144, shines: [431040, 432723, 435023, 438274, 440673] };
function runLog(chg, T, TB) {
  const L = tracker(chg), presOf = t => t >= LOG.up && t < LOG.spiny;
  const zw = lockAt(L, T, LOG.lock, presOf, [], LOG.spiny, 0xed937d1f, [21]), log = L.ctx.log.map(e => [e.ev, e.c, e.at, e.particles]);
  const atConfirm = zw.parts.length;
  if (zw.dead || TB == null) return { log, atConfirm, end: zw.parts.length };
  L.ctx.now = TB + 1000; L.zwCoinBack(TB - LOG.spiny);       // the turn-2 menu's coin back (not logged: the segment had no shines)
  for (const s of LOG.shines) { L.ctx.now = s + 30; L.zwTap(s); }
  L.ctx.now = LOG.shines[4] + 1000; L.zwUpdate(Math.floor(L.zwF(L.ctx.now, 0)) - 6);
  return { log, atConfirm, end: zw.parts.length, states: [...new Set(zw.parts.map(p => p.S.s.toString(16) + ' ' + p.S.branch))] };
}
const [OLD, NEW] = variants(), want = JSON.stringify([['zwStart', null, null, 2], ['zwInconsistent', null, 120, null], ['zwInput', 120, null, 0]]);
const Ts = []; for (let T = 422200; T <= 422300; T++) { const r = runLog(OLD, T); if (r.log[r.log.length - 1][1] === 120) Ts.push([T, JSON.stringify(r.log.map(x => x.map(y => y === undefined ? null : y))) === want]); }
const repro = Ts.filter(x => x[1]).map(x => x[0]);
check(repro.length >= 5, 'unpatched: the logged death (zwInconsistent at 120) is reproduced for ' + repro.length + ' clock origins');
console.log('log: clock origins giving c = 120: ' + Ts[0][0] + '..' + Ts[Ts.length - 1][0] + ' ms; unpatched reproduces the logged death on ' + repro[0] + '..' + repro[repro.length - 1]);
let minEnd = 1e9, states = new Set();
for (const T of repro.filter((x, i) => i % 3 === 0)) for (const TB of [428500, 429500, 430000]) {
  const r = runLog(NEW, T, TB); check(r.atConfirm > 0, 'patched: alive after the Spiny Flip confirm (T ' + T + ')');
  check(r.end > 0, 'patched: alive after the five turn-2 shines (T ' + T + ', coin back ' + TB + ')');
  minEnd = Math.min(minEnd, r.end); (r.states || []).forEach(s => states.add(s));
}
console.log('log, patched: ed937d1f alive after the confirm and all 5 later shines; ' + minEnd + '+ states left, e.g. ' + [...states].slice(0, 3).join(', '));

/* ---- 2. the route clips (ms from the trigger picture; pres = coin box present from that time on, 1/0) ---- */
const CLIPS = {
  '15-14-09': {"seed":"b400fca5","qs":[7],"trig":0,"pres":[[133.3,1],[583.3,0],[2233.3,1],[3450.0,0],[6633.3,1],[13800.0,0]],"shines":[8316.7,10716.7,13133.3],"coinBack":[[3250.0,1650.0],[7650.0,3183.3]],"spiny":3450.0,"timeOut":13800.0},
  '15-15-06': {"seed":"cf5894f0","qs":[19],"trig":0,"pres":[[166.7,1],[533.3,0],[2233.3,1],[3450.0,0],[6583.3,1],[13500.0,0]],"shines":[8716.7,10300.0,12750.0],"coinBack":[[3250.0,1700.0],[7600.0,3133.3]],"spiny":3450.0,"timeOut":13500.0},
  '15-16-08': {"seed":"6d3b7b2b","qs":[41,42,43,44,45,46,47],"trig":0,"pres":[[166.7,1],[533.3,0],[2216.7,1],[3483.3,0],[6583.3,1],[13483.3,0]],"shines":[12016.7],"coinBack":[[3233.3,1683.3],[7600.0,3100.0]],"spiny":3483.3,"timeOut":13483.3},
  '15-17-02': {"seed":"b3fb9c3b","qs":[18],"trig":0,"pres":[[133.3,1],[550.0,0],[2200.0,1],[3383.3,0],[6500.0,1],[14183.3,0]],"shines":[9550.0,11083.3],"coinBack":[[3200.0,1650.0],[7516.7,3116.7]],"spiny":3383.3,"timeOut":14183.3},
  '15-18-30': {"seed":"2d5dd210","qs":[42],"trig":0,"pres":[[166.7,1],[533.3,0],[2250.0,1],[3350.0,0],[6466.7,1],[13433.3,0]],"shines":[],"coinBack":[[3266.7,1716.7],[7483.3,3116.7]],"spiny":3350.0,"timeOut":13433.3},
  '15-19-21': {"seed":"ea113ee3","qs":[19],"trig":0,"pres":[[133.3,1],[566.7,0],[2216.7,1],[3350.0,0],[6416.7,1],[13566.7,0]],"shines":[13533.3],"coinBack":[[3233.3,1650.0],[7433.3,3066.7]],"spiny":3350.0,"timeOut":13566.7},
  '15-20-15': {"seed":"306686e9","qs":[16],"trig":0,"pres":[[183.3,1],[550.0,0],[2200.0,1],[3433.3,0],[6550.0,1],[14150.0,0]],"shines":[8616.7,11050.0],"coinBack":[[3216.7,1650.0],[7566.7,3116.7]],"spiny":3433.3,"timeOut":14150.0},
};
function runClip(chg, c, late) {
  const L = tracker(chg), presOf = t => { let p = 0; for (const [a, v] of c.pres) { if (a > t) break; p = v; } return !!p; };
  const T = 0, tLock = late ? c.spiny + 1000 : 48 * L.ctx.FRAME + 300, zw = lockAt(L, T, tLock, presOf, c.shines, c.spiny, parseInt(c.seed, 16), c.qs);
  const evs = [];
  if (tLock <= c.spiny) evs.push([c.spiny, 'spiny']);
  for (const s of c.shines) if (s >= tLock) evs.push([s, 'shine']);
  for (const [t, h] of c.coinBack) if (t >= tLock) evs.push([t, 'back', h]);
  evs.sort((a, b) => a[0] - b[0]);
  for (const [t, k, h] of evs) { if (t >= c.timeOut) break; L.ctx.now = t;
    if (k === 'spiny') L.zwInput('hw_spiny', t, L.ctx.VAN.B(), L.CHG_IMPS); else if (k === 'shine') L.zwTap(t); else L.zwCoinBack(h); }
  const cf = Math.round(L.zwF(c.timeOut, 0)) - 3; L.ctx.now = c.timeOut; zw.visTo = cf - 4; L.zwUpdate(cf);
  let w = 0, ok = 0; for (const p of zw.parts) { if (p.S.inst.length || (p.S.extra && p.S.extra.size) || p.g > cf) continue; w += p.w; if (R.works(p.S.s, p.S.nc, cf, p.g, R.PROFILES.timeout)) ok += p.w; }
  return { parts: zw.parts.length, works: w ? +(ok / w).toFixed(3) : null };
}
for (const [n, c] of Object.entries(CLIPS)) {
  const row = [n];
  for (const late of [true, false]) {
    const a = runClip(OLD, c, late), b = runClip(NEW, c, late);
    check(b.parts > 0, n + (late ? ' late' : ' early') + ' lock: patched tracker alive at Time Out');
    check(a.parts === b.parts && a.works === b.works, n + (late ? ' late' : ' early') + ' lock: patched differs from unpatched (' + JSON.stringify([a, b]) + ')');
    row.push((late ? 'late ' : 'early ') + b.parts + ' states, Time Out works ' + b.works);
  }
  console.log('clip ' + row.join(' | '));
}
console.log(fails ? fails + ' FAILED' : 'all passed');
process.exit(fails ? 1 : 0);
